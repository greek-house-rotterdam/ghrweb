import json

import pytest

import auto_publish
from auto_publish import LABEL, Failed, apply, disable, enable


class FakeGh:
    """Answers `gh pr view` with a pull request (or, given a list, one per call,
    the last one repeating), `gh pr merge` from a script of (exit code, output)
    pairs, and `gh api` / `gh pr list` through `other`; records every call."""

    def __init__(self, pr=None, merge=(), other=lambda args: (0, "")):
        self.pr = pr
        self.merge = list(merge)
        self.other = other
        self.calls = []

    def __call__(self, *args):
        self.calls.append(list(args))
        if args[:2] == ("pr", "view"):
            if isinstance(self.pr, list):
                return 0, json.dumps(self.pr.pop(0) if len(self.pr) > 1 else self.pr[0])
            return 0, json.dumps(self.pr)
        if args[:2] == ("pr", "merge"):
            return self.merge.pop(0)
        return self.other(args)

    def merges(self):
        return [c[c.index("-R") + 2:] for c in self.calls if c[:2] == ["pr", "merge"]]

    def deleted(self):
        return [c[-1] for c in self.calls if c[:3] == ["api", "-X", "DELETE"]]


HEAD = "cms/news-gr/η-nvidia-σε-πτωση"
HEAD_REF = "repos/o/r/git/refs/heads/cms/news-gr/%CE%B7-nvidia-%CF%83%CE%B5-%CF%80%CF%84%CF%89%CF%83%CE%B7"


def pr(labels=(), auto=None, state="OPEN", head=HEAD):
    return {
        "state": state,
        "labels": [{"name": n} for n in labels],
        "autoMergeRequest": auto,
        "headRefName": head,
    }


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class TestApply:
    def test_ready_label_turns_auto_merge_on_with_squash(self):
        gh = FakeGh(pr([LABEL, "other"]), [(0, "")])
        assert apply(gh, "o/r", "7") == "on"
        assert gh.merges() == [["--auto", "--squash"]]

    def test_ready_label_with_auto_merge_already_on_does_nothing(self):
        gh = FakeGh(pr([LABEL], auto={"enabledAt": "x"}))
        assert apply(gh, "o/r", "7") == "on"
        assert gh.merges() == []

    def test_other_status_labels_do_not_turn_it_on(self):
        for label in ("decap-cms/draft", "decap-cms/pending_review"):
            gh = FakeGh(pr([label]))
            assert apply(gh, "o/r", "7") == "off"
            assert gh.merges() == []

    def test_moving_out_of_ready_turns_it_off(self):
        gh = FakeGh(pr(["decap-cms/pending_review"], auto={"enabledAt": "x"}), [(0, "")])
        assert apply(gh, "o/r", "7") == "off"
        assert gh.merges() == [["--disable-auto"]]

    def test_merged_pull_request_gets_its_branch_deleted(self):
        gh = FakeGh(pr([LABEL], state="MERGED"))
        assert apply(gh, "o/r", "7") is None
        assert gh.merges() == []
        assert gh.deleted() == [HEAD_REF]

    def test_closed_pull_request_is_left_alone(self):
        gh = FakeGh(pr([LABEL], state="CLOSED"))
        assert apply(gh, "o/r", "7") is None
        assert gh.merges() == [] and gh.deleted() == []

    def test_unreadable_pull_request_fails(self):
        with pytest.raises(Failed):
            apply(lambda *a: (1, "boom"), "o/r", "7")


class TestEnable:
    def test_repository_without_auto_merge_is_unavailable_not_an_error(self):
        gh = FakeGh(merge=[(1, "GraphQL: Auto merge is not allowed for this repository (enablePullRequestAutoMerge)")])
        assert enable(gh, "o/r", "7") == "unavailable"

    def test_clean_status_falls_back_to_merging_now(self):
        gh = FakeGh(merge=[(1, "GraphQL: Pull request is in clean status (enablePullRequestAutoMerge)"), (0, "")])
        assert enable(gh, "o/r", "7") == "on"
        assert gh.merges() == [["--auto", "--squash"], ["--squash"]]

    def test_clean_status_and_the_direct_merge_fails(self):
        gh = FakeGh(merge=[(1, "Pull request is in clean status"), (1, "base branch policy prohibits the merge")])
        with pytest.raises(Failed, match="policy"):
            enable(gh, "o/r", "7")

    def test_other_errors_are_real_failures(self):
        with pytest.raises(Failed):
            enable(FakeGh(merge=[(1, "HTTP 502")]), "o/r", "7")


class TestDisable:
    @pytest.mark.parametrize(
        "out", ["Pull request Auto merge is not enabled", "Auto merge is not allowed for this repository"]
    )
    def test_not_enabled_is_fine(self, out):
        assert disable(FakeGh(merge=[(1, out)]), "o/r", "7") == "off"

    def test_other_errors_fail(self):
        with pytest.raises(Failed):
            disable(FakeGh(merge=[(1, "HTTP 502")]), "o/r", "7")


class TestDeleteBranch:
    def test_deletes_a_cms_branch_with_a_greek_name(self):
        gh = FakeGh()
        assert auto_publish.delete_branch(gh, "o/r", HEAD) is True
        assert gh.deleted() == [HEAD_REF]

    def test_never_touches_other_branches(self):
        gh = FakeGh()
        assert auto_publish.delete_branch(gh, "o/r", "main") is False
        assert auto_publish.delete_branch(gh, "o/r", "feat/x") is False
        assert gh.calls == []

    def test_already_gone_is_fine(self):
        gh = FakeGh(other=lambda args: (1, "gh: Reference does not exist (HTTP 422)"))
        assert auto_publish.delete_branch(gh, "o/r", HEAD) is False

    def test_other_errors_fail(self):
        with pytest.raises(Failed, match="could not delete"):
            auto_publish.delete_branch(FakeGh(other=lambda args: (1, "HTTP 502")), "o/r", HEAD)


class TestWaitForMerge:
    def wait(self, gh, wait_s=600):
        clock = FakeClock()
        return auto_publish.wait_for_merge(gh, "o/r", "7", wait_s, clock.sleep, clock), clock

    def test_waits_for_the_merge_then_deletes_the_branch(self):
        gh = FakeGh([pr([LABEL]), pr([LABEL]), pr([LABEL], state="MERGED")])
        outcome, clock = self.wait(gh)
        assert outcome == "merged"
        assert gh.deleted() == [HEAD_REF]
        assert clock.now == 2 * auto_publish.POLL_SECONDS

    def test_stops_when_moved_out_of_ready(self):
        gh = FakeGh([pr([LABEL]), pr(["decap-cms/pending_review"])])
        assert self.wait(gh)[0] == "not ready"
        assert gh.deleted() == []

    def test_stops_when_closed_without_merging(self):
        gh = FakeGh([pr([LABEL], state="CLOSED")])
        assert self.wait(gh)[0] == "closed"
        assert gh.deleted() == []

    def test_gives_up_after_the_wait(self):
        gh = FakeGh([pr([LABEL])])
        outcome, clock = self.wait(gh, wait_s=60)
        assert outcome == "timeout"
        assert clock.now >= 60
        assert gh.deleted() == []


class TestSweep:
    REFS = "\n".join(f"refs/heads/cms/news-gr/{n}" for n in ("merged", "open", "closed", "new"))
    PRS = {
        "cms/news-gr/merged": [{"state": "MERGED"}],
        "cms/news-gr/open": [{"state": "MERGED"}, {"state": "OPEN"}],
        "cms/news-gr/closed": [{"state": "CLOSED"}],
        "cms/news-gr/new": [],
    }

    def gh(self):
        def other(args):
            if args[0] == "api" and "matching-refs" in args[2]:
                return 0, self.REFS
            if args[:2] == ("pr", "list"):
                return 0, json.dumps(self.PRS[args[args.index("--head") + 1]])
            return 0, ""  # the DELETE

        return FakeGh(other=other)

    def test_deletes_branches_whose_pull_requests_are_all_done(self):
        gh = self.gh()
        assert auto_publish.sweep(gh, "o/r") == ["cms/news-gr/merged", "cms/news-gr/closed"]

    def test_keeps_open_ones_and_branches_without_a_pull_request(self):
        gh = self.gh()
        auto_publish.sweep(gh, "o/r")
        assert not any(d.endswith(("/open", "/new")) for d in gh.deleted())

    def test_main_sweep_mode(self, monkeypatch, capsys):
        monkeypatch.setenv("REPO", "o/r")
        assert auto_publish.main(self.gh(), argv=["sweep"]) == 0
        assert "Deleted 2 leftover branch(es)" in capsys.readouterr().out


class TestMain:
    @pytest.fixture(autouse=True)
    def env(self, monkeypatch):
        monkeypatch.setenv("REPO", "o/r")
        monkeypatch.setenv("PR_NUMBER", "7")
        monkeypatch.setenv("WAIT_SECONDS", "0")
        self.updates = []
        monkeypatch.setattr(
            auto_publish.pr_status, "update",
            lambda api, name, data, **kw: self.updates.append((name, data)) or "ok",
        )

    def test_unavailable_warns_and_stays_green(self, capsys):
        gh = FakeGh(pr([LABEL]), [(1, "Auto merge is not allowed for this repository")])
        assert auto_publish.main(gh) == 0
        out = capsys.readouterr().out
        assert "::warning" in out and "Allow auto-merge" in out
        assert self.updates[0][1]["state"] == "unavailable"

    def test_on_writes_the_status_line(self):
        assert auto_publish.main(FakeGh(pr([LABEL]), [(0, "")])) == 0
        assert self.updates[0][0] == "autopublish" and self.updates[0][1]["state"] == "on"

    def test_real_failure_is_red_and_writes_no_line(self, capsys):
        assert auto_publish.main(FakeGh(pr([LABEL]), [(1, "HTTP 502")])) == 1
        assert "::error" in capsys.readouterr().out
        assert self.updates == []

    def test_status_comment_trouble_never_fails_the_job(self, monkeypatch):
        def broken(*a, **k):
            raise auto_publish.pr_status.NotVerified("x")

        monkeypatch.setattr(auto_publish.pr_status, "update", broken)
        assert auto_publish.main(FakeGh(pr([LABEL]), [(0, "")])) == 0
