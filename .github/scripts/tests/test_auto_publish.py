import json

import pytest

import auto_publish
from auto_publish import LABEL, Failed, apply, disable, enable


class FakeGh:
    """Answers `gh pr view` with a pull request and `gh pr merge` from a script of
    (exit code, output) pairs; records every call."""

    def __init__(self, pr=None, merge=()):
        self.pr = pr
        self.merge = list(merge)
        self.calls = []

    def __call__(self, *args):
        self.calls.append(list(args))
        if args[:2] == ("pr", "view"):
            return 0, json.dumps(self.pr)
        return self.merge.pop(0)

    def merges(self):
        return [c[c.index("-R") + 2:] for c in self.calls if c[:2] == ["pr", "merge"]]


def pr(labels=(), auto=None, state="OPEN"):
    return {"state": state, "labels": [{"name": n} for n in labels], "autoMergeRequest": auto}


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

    def test_closed_pull_request_is_left_alone(self):
        gh = FakeGh(pr([LABEL], state="MERGED"))
        assert apply(gh, "o/r", "7") is None
        assert gh.merges() == []

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


class TestMain:
    @pytest.fixture(autouse=True)
    def env(self, monkeypatch):
        monkeypatch.setenv("REPO", "o/r")
        monkeypatch.setenv("PR_NUMBER", "7")
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
