import json
import subprocess

import pytest

import pr_status
from pr_status import (
    Api,
    NotVerified,
    State,
    apply_section,
    compute_alerts,
    encode,
    holds,
    merge_states,
    next_step,
    parse,
    render,
    update,
    view_states,
)

HEAD = "a" * 40
BOT = "github-actions[bot]"


class FakeGitHub:
    """A tiny in-memory PR: serves comments, head sha and files like gh does."""

    def __init__(self, comments=(), files=("src/content/news/gr/x.md",), head=HEAD):
        self.comments = [dict(c) for c in comments]
        self.files = list(files)
        self.head = head
        self.next_id = 100
        self.log = []

    def add(self, body, login=BOT):
        self.next_id += 1
        self.comments.append({"id": self.next_id, "body": body, "login": login})
        return self.next_id

    def __call__(self, *args):
        a = list(args)
        if a[-1] == "--silent":
            a = a[:-1]
        if "--paginate" in a and a[1].endswith("/comments"):
            return "\n".join(json.dumps(c) for c in self.comments) + "\n"
        if "--paginate" in a and a[1].endswith("/files"):
            return "\n".join(self.files) + "\n"
        if a[1].endswith("/pulls/7"):
            return self.head + "\n"
        if a[:2] == ["api", "-X"] and a[2] == "PATCH":
            cid = int(a[3].rsplit("/", 1)[1])
            self.log.append(("edit", cid))
            match = [c for c in self.comments if c["id"] == cid]
            if not match:
                raise subprocess.CalledProcessError(1, "gh")  # 404
            match[0]["body"] = a[5].removeprefix("body=")
            return ""
        if a[:2] == ["api", "-X"] and a[2] == "DELETE":
            cid = int(a[3].rsplit("/", 1)[1])
            self.log.append(("delete", cid))
            self.comments = [c for c in self.comments if c["id"] != cid]
            return ""
        if a[0] == "api" and a[1].endswith("/issues/7/comments"):
            self.log.append(("create", self.next_id + 1))
            self.add(a[3].removeprefix("body="))
            return ""
        raise AssertionError(f"unexpected gh call: {args}")

    def status_bodies(self):
        return [c["body"] for c in self.comments if pr_status.MARK in c["body"]]

    def state(self):
        (body,) = self.status_bodies()
        return parse(body)


def api_for(gh):
    return Api("o/r", "7", gh)


def upd(gh, name, data, **kw):
    kw.setdefault("sleep", lambda s: None)
    kw.setdefault("mentions", "@Admin")
    return update(api_for(gh), name, data, **kw)


TR_OK = {"state": "ok", "sha": HEAD, "files": ["src/content/news/nl/x.md"], "nothing": False, "run": 1}
TR_FAIL = {"state": "fail", "sha": HEAD, "kind": "hand-written", "message": "boom", "run": 1}
IMG_OK = {"state": "ok", "sha": HEAD, "count": 1, "run": 1}
IMG_FAIL = {"state": "fail", "sha": HEAD, "problems": ["`a.heic`: Unsupported format"], "run": 1}
PREV = {"state": "ok", "sha": HEAD, "url": "https://abc-ghrweb.enosi-ellinon-ollandias.workers.dev", "run": 1}


def review(path, findings=(), error=None, sha=HEAD):
    return {"files": {path: {"sha": sha, "error": error, "findings": list(findings)}}, "sha": sha}


# ---------------------------------------------------------------------------
# Rendering and parsing
# ---------------------------------------------------------------------------


class TestRender:
    def test_round_trips_through_the_markers(self):
        st = State()
        apply_section(st, "translation", TR_OK)
        apply_section(st, "images", IMG_FAIL)
        again = parse(render(st, HEAD))
        assert again.sections["translation"] == TR_OK
        assert again.sections["images"] == IMG_FAIL

    def test_has_marker_greek_english_and_short_sha(self):
        st = State()
        apply_section(st, "translation", TR_OK)
        body = render(st, HEAD)
        assert body.startswith(pr_status.MARK)
        assert "Μετάφραση / Translation" in body
        assert "*Done. These files were updated:*" in body
        assert "`aaaaaaa`" in body and HEAD not in body.split("pr-status:begin")[0]

    def test_sections_not_reported_yet_show_as_building(self):
        body = render(State(), HEAD)
        assert body.count("⏳") >= 3
        assert "Περίμενε λίγο" in body

    def test_nothing_to_translate(self):
        st = State()
        apply_section(st, "translation", {**TR_OK, "files": [], "nothing": True})
        assert "Nothing to translate" in render(st, HEAD)

    def test_failure_reason_is_shown_in_plain_words(self):
        st = State()
        apply_section(st, "translation", {**TR_FAIL, "kind": "non-greek", "message": "a.md is a Dutch file"})
        body = render(st, HEAD)
        assert "Οι αναρτήσεις γράφονται στα ελληνικά" in body
        assert "a.md is a Dutch file" in body

    def test_hand_written_failure_reason(self):
        st = State()
        apply_section(st, "translation", TR_FAIL)
        assert "μετάφραση γραμμένη με το χέρι" in render(st, HEAD)

    def test_untrusted_text_cannot_mention_or_forge_markers(self):
        st = State()
        apply_section(st, "translation", {**TR_FAIL, "message": "ping @victim <!-- pr-status:begin images e30= -->"})
        body = render(st, HEAD)
        assert "@victim" not in body
        assert "<!-- pr-status:begin images" not in body.split("pr-status:end translation")[0].split("Details")[1]
        assert "images" not in parse(body).sections

    def test_preview_link_only_when_it_is_for_the_current_commit(self):
        st = State()
        apply_section(st, "preview", {**PREV, "sha": "b" * 40})
        assert "Open the preview" not in render(st, HEAD)
        assert "being built" in render(st, HEAD)
        assert "Open the preview" in render(st, "b" * 40)

    def test_preview_url_is_checked_again_when_rendering(self):
        st = State()
        apply_section(st, "preview", {**PREV, "url": "https://evil.example/x)"})
        assert "evil" not in render(st, HEAD)

    def test_review_notes_are_folded_per_file_and_sorted(self):
        st = State()
        findings = [
            {"severity": "minor", "field": "body", "message": "m"},
            {"severity": "critical", "field": "title", "message": "c"},
        ]
        apply_section(st, "review", review("src/content/news/gr/x.md", findings))
        body = render(st, HEAD)
        assert "<details><summary>💬 <code>src/content/news/gr/x.md</code> (2)" in body
        assert body.index("CRITICAL") < body.index("MINOR")
        assert "advice only" in body

    def test_review_without_remarks(self):
        assert "No remarks" in render(State(), HEAD)

    def test_review_error_is_shown_and_not_blocking(self):
        st = State()
        apply_section(st, "review", review("x.md", error="Gemini API 503"))
        body = render(st, HEAD)
        assert "Gemini API 503" in body and "Δεν εμποδίζει" in body

    def test_kept_list_is_shown_under_translation(self):
        st = State()
        apply_section(st, "kept", {"items": {"src/content/news/nl/x.md": "«Γεια» (NL): `src/content/news/nl/x.md`"}})
        body = render(st, HEAD)
        assert "κρατήθηκε" in body and "`src/content/news/nl/x.md`" in body

    def test_mentions_only_while_something_failed(self):
        st = State()
        apply_section(st, "translation", TR_FAIL)
        assert "cc @Admin" in render(st, HEAD, "@Admin")
        apply_section(st, "translation", TR_OK)
        assert "cc" not in render(st, HEAD, "@Admin")

    def test_alerts_marker_lists_the_failures(self):
        st = State()
        apply_section(st, "translation", TR_FAIL)
        apply_section(st, "images", IMG_FAIL)
        apply_section(st, "review", review("x.md", error="e"))
        assert parse(render(st, HEAD)).alerts == {"translation", "images", "review"}

    def test_big_state_stays_under_github_limit(self):
        st = State()
        apply_section(st, "translation", {**TR_OK, "files": [f"src/content/news/nl/{i}.md" for i in range(500)]})
        assert len(render(st, HEAD)) < 65000


# ---------------------------------------------------------------------------
# Next step
# ---------------------------------------------------------------------------


def views(**over):
    v = {"translation": "ok", "images": "ok", "preview": "ok", "review": "ok"}
    v.update(over)
    return v


class TestNextStep:
    def test_all_good_says_publish(self):
        gr, en = next_step(views())
        assert gr == "Έτοιμο: στο /admin → Workflow, βάλε την ανάρτηση στο Ready και πάτα Publish."
        assert "Publish" in en

    def test_translation_failure_says_admin_was_told(self):
        gr, _ = next_step(views(translation="fail"))
        assert "ο διαχειριστής ενημερώθηκε" in gr and "Έτοιμο" not in gr

    def test_image_failure_tells_the_editor_what_to_do(self):
        gr, _ = next_step(views(images="fail"))
        assert "Αντικατάστησε την εικόνα" in gr and "ενημερώθηκε" in gr

    def test_both_failures_are_both_named(self):
        gr, _ = next_step(views(translation="fail", images="fail"))
        assert "μετάφραση" in gr and "εικόνα" in gr

    def test_pending_names_what_is_still_running(self):
        gr, en = next_step(views(preview="pending"))
        assert "προεπισκόπηση" in gr and "preview" in en and "Έτοιμο" not in gr

    def test_failure_wins_over_pending(self):
        gr, _ = next_step(views(translation="fail", preview="pending"))
        assert "δεν ολοκληρώθηκε" in gr

    def test_remarks_are_optional_reading(self):
        gr, _ = next_step(views(review="remarks"))
        assert gr.startswith("Έτοιμο") and "προαιρετικό" in gr

    def test_review_not_run_does_not_block(self):
        gr, _ = next_step(views(review="warn"))
        assert gr.startswith("Έτοιμο") and "δεν εμποδίζει" in gr


class TestViews:
    def test_default_is_pending_except_review(self):
        v = view_states(State(), HEAD)
        assert (v["translation"], v["images"], v["preview"], v["review"]) == ("pending", "pending", "pending", "ok")

    def test_review_error_beats_remarks(self):
        st = State()
        apply_section(st, "review", {"files": {
            "a.md": {"error": None, "findings": [{"severity": "minor"}]},
            "b.md": {"error": "x", "findings": []},
        }, "sha": HEAD})
        assert view_states(st, HEAD)["review"] == "warn"
        assert compute_alerts(view_states(st, HEAD)) == {"review"}


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------


class TestMerge:
    def test_kept_lists_accumulate(self):
        st = State()
        apply_section(st, "kept", {"items": {"a": "A1"}})
        apply_section(st, "kept", {"items": {"b": "B", "a": "A2"}})
        assert st.sections["kept"]["items"] == {"a": "A2", "b": "B"}

    def test_review_replaces_only_the_reviewed_files(self):
        st = State()
        apply_section(st, "review", {"files": {"a.md": {"error": None, "findings": [{"severity": "minor"}]},
                                              "b.md": {"error": None, "findings": [{"severity": "minor"}]}}, "sha": "1"})
        # a.md reviewed again and now clean, b.md not part of this run
        apply_section(st, "review", {"files": {"a.md": None}, "sha": "2"})
        assert list(st.sections["review"]["files"]) == ["b.md"]
        assert st.sections["review"]["sha"] == "2"

    def test_review_drops_files_that_left_the_pr(self):
        st = State()
        apply_section(st, "review", {"files": {"a.md": {"error": None, "findings": [{}]},
                                              "b.md": {"error": None, "findings": [{}]}}, "sha": "1"})
        apply_section(st, "review", {"files": {}, "sha": "2"}, pr_files=["b.md"])
        assert list(st.sections["review"]["files"]) == ["b.md"]

    def test_other_sections_are_left_alone(self):
        st = State()
        apply_section(st, "translation", TR_OK)
        apply_section(st, "images", IMG_FAIL)
        assert st.sections["translation"] == TR_OK

    def test_duplicates_merge_newer_wins(self):
        old, new = State(), State()
        apply_section(old, "translation", TR_OK)
        apply_section(old, "images", IMG_OK)
        apply_section(new, "translation", TR_FAIL)
        merged = merge_states([old, new])
        assert merged.sections["translation"] == TR_FAIL and merged.sections["images"] == IMG_OK

    def test_holds_accepts_a_newer_run_but_not_an_older_one(self):
        st = State()
        apply_section(st, "images", {**IMG_OK, "run": 5})
        assert holds(st, "images", {**IMG_OK, "run": 4})
        assert not holds(st, "images", {**IMG_OK, "run": 6})
        assert not holds(State(), "images", IMG_OK)


# ---------------------------------------------------------------------------
# update(): create, edit, notify, retry
# ---------------------------------------------------------------------------


class TestUpdate:
    def test_creates_one_comment_then_edits_it(self):
        gh = FakeGitHub()
        assert "created" in upd(gh, "translation", TR_OK)
        assert "updated" in upd(gh, "images", IMG_OK)
        assert len(gh.status_bodies()) == 1
        assert set(gh.state().sections) == {"translation", "images"}

    def test_code_pr_gets_no_comment(self):
        gh = FakeGitHub(files=["src/pages/index.astro", ".github/workflows/x.yml"])
        assert upd(gh, "translation", TR_OK).startswith("skip")
        assert gh.comments == []

    def test_image_only_pr_gets_a_comment(self):
        gh = FakeGitHub(files=["public/images/a.jpg"])
        upd(gh, "images", IMG_OK)
        assert len(gh.status_bodies()) == 1

    def test_existing_comment_is_kept_updating_when_content_left_the_pr(self):
        gh = FakeGitHub()
        upd(gh, "translation", TR_OK)
        gh.files = ["docs/x.md"]
        assert "updated" in upd(gh, "images", IMG_OK)

    def test_unchanged_body_is_not_written_again(self):
        gh = FakeGitHub()
        upd(gh, "translation", TR_OK)
        gh.log.clear()
        upd(gh, "translation", TR_OK)
        assert ("edit", 101) not in gh.log

    def test_ignores_status_marker_in_a_comment_by_someone_else(self):
        gh = FakeGitHub()
        gh.add(pr_status.MARK + "\nspoof", login="mallory")
        upd(gh, "translation", TR_OK)
        assert gh.comments[0]["body"].endswith("spoof")  # untouched
        assert len(gh.status_bodies()) == 2

    def test_new_failure_recreates_the_comment_with_a_mention(self):
        gh = FakeGitHub()
        upd(gh, "translation", TR_OK)
        first = gh.comments[0]["id"]
        result = upd(gh, "translation", TR_FAIL)
        assert "re-created" in result
        assert [c["id"] for c in gh.comments] != [first] and len(gh.comments) == 1
        assert "cc @Admin" in gh.comments[0]["body"]
        assert ("create", gh.comments[0]["id"]) in gh.log  # created before the old one was deleted
        assert gh.log.index(("delete", first)) > gh.log.index(("create", gh.comments[0]["id"]))
        # the other sections came along
        assert gh.state().sections["translation"] == TR_FAIL

    def test_failure_that_persists_does_not_notify_again(self):
        gh = FakeGitHub()
        upd(gh, "translation", TR_FAIL)
        cid = gh.comments[0]["id"]
        assert "updated" in upd(gh, "images", IMG_OK)
        assert "updated" in upd(gh, "translation", {**TR_FAIL, "run": 2, "sha": "c" * 40})
        assert [c["id"] for c in gh.comments] == [cid]
        assert "cc @Admin" in gh.comments[0]["body"]

    def test_second_kind_of_failure_notifies_again(self):
        gh = FakeGitHub()
        upd(gh, "translation", TR_FAIL)
        assert "re-created" in upd(gh, "images", IMG_FAIL)
        assert gh.state().alerts == {"translation", "images"}

    def test_failure_clears_then_comes_back_notifies_again(self):
        gh = FakeGitHub()
        upd(gh, "translation", TR_FAIL)
        upd(gh, "translation", {**TR_OK, "run": 2})
        assert "cc" not in gh.comments[0]["body"] and gh.state().alerts == set()
        assert "re-created" in upd(gh, "translation", {**TR_FAIL, "run": 3})

    def test_first_ever_update_in_failure_mentions(self):
        gh = FakeGitHub()
        upd(gh, "translation", TR_FAIL)
        assert "cc @Admin" in gh.comments[0]["body"]

    def test_old_notices_are_deleted_and_kept_list_carried_over(self):
        gh = FakeGitHub()
        gh.add("<!-- pr-notice:translate -->\nfailed")
        gh.add("<!-- content-review:src/content/news/gr/x.md -->\nreview")
        gh.add("<!-- pr-notice:kept -->\n### t\n\n- «Γεια» (NL): `src/content/news/nl/x.md`\n")
        keep = gh.add("a human comment")
        upd(gh, "translation", TR_OK)
        assert [c["id"] for c in gh.comments if pr_status.MARK not in c["body"]] == [keep]
        assert "src/content/news/nl/x.md" in gh.state().sections["kept"]["items"]

    def test_old_notices_by_humans_are_not_deleted(self):
        gh = FakeGitHub()
        gh.add("<!-- pr-notice:translate --> quoting the bot", login="editor")
        upd(gh, "translation", TR_OK)
        assert any(c["login"] == "editor" for c in gh.comments)

    def test_duplicate_status_comments_are_merged_into_one(self):
        gh = FakeGitHub()
        for tr in (TR_OK, IMG_OK):
            st = State()
            apply_section(st, "translation" if tr is TR_OK else "images", tr)
            gh.add(render(st, HEAD))
        upd(gh, "preview", PREV)
        assert len(gh.status_bodies()) == 1
        assert set(gh.state().sections) == {"translation", "images", "preview"}


class TestRace:
    def test_a_concurrent_overwrite_is_noticed_and_retried(self):
        gh = FakeGitHub()
        upd(gh, "translation", TR_OK)
        other = {"done": False}

        # Another job read the comment before our edit and writes back its own
        # section on top of the old content right after our edit, losing ours.
        def call(*args):
            out = gh(*args)
            if args[:3] == ("api", "-X", "PATCH") and not other["done"]:
                other["done"] = True
                gh.comments[0]["body"] = render(
                    _state_with(translation=TR_OK, review=review("x.md")), HEAD
                )
            return out

        api = Api("o/r", "7", call)
        update(api, "images", IMG_OK, sleep=lambda s: None)
        st = gh.state()
        assert st.sections["images"] == IMG_OK  # ours survived (retried)
        assert "review" in st.sections  # theirs too

    def test_gives_up_after_the_attempts(self):
        gh = FakeGitHub()
        upd(gh, "translation", TR_OK)

        def call(*args):
            out = gh(*args)
            if args[:3] == ("api", "-X", "PATCH"):
                gh.comments[0]["body"] = render(_state_with(translation=TR_OK), HEAD)
            return out

        with pytest.raises(NotVerified):
            update(Api("o/r", "7", call), "images", IMG_OK, attempts=3, sleep=lambda s: None)

    def test_edit_of_a_comment_deleted_meanwhile_is_retried(self):
        gh = FakeGitHub()
        upd(gh, "translation", TR_OK)
        calls = {"n": 0}

        def call(*args):
            if args[:3] == ("api", "-X", "PATCH") and calls["n"] == 0:
                calls["n"] += 1
                gh.comments.clear()  # another job re-created and deleted it
                gh.add(render(_state_with(translation=TR_OK), HEAD))
            return gh(*args)

        update(Api("o/r", "7", call), "images", IMG_OK, sleep=lambda s: None)
        assert gh.state().sections["images"] == IMG_OK
        assert len(gh.status_bodies()) == 1

    def test_retries_back_off(self):
        gh = FakeGitHub()
        upd(gh, "translation", TR_OK)
        sleeps = []

        def call(*args):
            out = gh(*args)
            if args[:3] == ("api", "-X", "PATCH"):
                gh.comments[0]["body"] = render(_state_with(translation=TR_OK), HEAD)
            return out

        with pytest.raises(NotVerified):
            update(Api("o/r", "7", call), "images", IMG_OK, attempts=3, sleep=sleeps.append)
        assert len([s for s in sleeps if s != 2.0]) == 2  # a pause before each retry


def _state_with(**sections):
    st = State()
    for name, data in sections.items():
        apply_section(st, name, data)
    return st


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


class TestCli:
    @pytest.fixture(autouse=True)
    def env(self, monkeypatch):
        monkeypatch.setenv("REPO", "o/r")
        monkeypatch.setenv("PR_NUMBER", "7")
        monkeypatch.setenv("ADMIN_MENTIONS", "@Admin")
        monkeypatch.setenv("GITHUB_RUN_ID", "42")
        monkeypatch.setattr(pr_status.time, "sleep", lambda s: None)

    def test_translation_ok_lists_written_files(self, tmp_path):
        written = tmp_path / "w.txt"
        written.write_text("src/content/news/nl/x.md\nsrc/content/news/en/x.md\n")
        gh = FakeGitHub()
        assert pr_status.main(["translation", "--state", "ok", "--sha", HEAD, "--written", str(written)], gh) == 0
        t = gh.state().sections["translation"]
        assert t["files"] == ["src/content/news/nl/x.md", "src/content/news/en/x.md"] and t["run"] == 42

    def test_translation_failure_reads_the_report(self, tmp_path):
        report = tmp_path / "r.json"
        report.write_text(json.dumps({"kind": "non-greek", "message": "x.md is Dutch"}))
        gh = FakeGitHub()
        pr_status.main(["translation", "--state", "fail", "--sha", HEAD, "--report", str(report)], gh)
        t = gh.state().sections["translation"]
        assert (t["kind"], t["message"]) == ("non-greek", "x.md is Dutch")

    def test_translation_failure_without_report_is_generic(self, tmp_path):
        gh = FakeGitHub()
        pr_status.main(["translation", "--state", "fail", "--sha", HEAD, "--report", str(tmp_path / "none")], gh)
        assert "technical problem" in gh.comments[0]["body"]

    def test_missing_translation_report(self, tmp_path):
        missing = tmp_path / "m.md"
        missing.write_text("- `src/content/news/nl/x.md`\n")
        gh = FakeGitHub()
        pr_status.main(["translation", "--state", "fail", "--missing", str(missing)], gh)
        assert gh.state().sections["translation"]["kind"] == "missing"

    def test_kept_without_report_does_nothing(self, tmp_path):
        gh = FakeGitHub()
        assert pr_status.main(["kept", "--file", str(tmp_path / "none")], gh) == 0
        assert gh.comments == []

    def test_kept_report_lines_are_keyed_by_path(self, tmp_path):
        f = tmp_path / "k.md"
        f.write_text("- «Γεια» (NL): `src/content/news/nl/x.md`\n")
        gh = FakeGitHub()
        pr_status.main(["kept", "--file", str(f)], gh)
        assert list(gh.state().sections["kept"]["items"]) == ["src/content/news/nl/x.md"]

    def test_images_failure_reads_problems(self, tmp_path):
        f = tmp_path / "p.md"
        f.write_text("- `public/images/a.heic`: Unsupported format\n")
        gh = FakeGitHub()
        pr_status.main(["images", "--state", "fail", "--problems", str(f)], gh)
        assert gh.state().sections["images"]["problems"] == ["`public/images/a.heic`: Unsupported format"]

    def test_review_results(self, tmp_path):
        reviewed = tmp_path / "r.txt"
        reviewed.write_text("a.md\nb.md\n")
        results = tmp_path / "res.json"
        results.write_text(json.dumps([{"file": "a.md", "findings": [{"severity": "major", "field": "body", "message": "m"}], "error": None}]))
        gh = FakeGitHub(files=["src/content/x.md", "a.md", "b.md"])
        pr_status.main(["review", "--sha", HEAD, "--reviewed", str(reviewed), "--results", str(results)], gh)
        assert list(gh.state().sections["review"]["files"]) == ["a.md"]

    def test_review_that_died_marks_every_file_unavailable(self, tmp_path):
        reviewed = tmp_path / "r.txt"
        reviewed.write_text("a.md\n")
        gh = FakeGitHub(files=["a.md", "src/content/x.md"])
        pr_status.main(["review", "--sha", HEAD, "--reviewed", str(reviewed), "--results", str(tmp_path / "none")], gh)
        assert gh.state().alerts == {"review"}

    def test_an_api_failure_warns_but_does_not_fail_the_job(self, capsys):
        def broken(*args):
            raise subprocess.CalledProcessError(1, "gh")

        assert pr_status.main(["preview", "--sha", HEAD, "--url", PREV["url"]], broken) == 0
        assert "::warning" in capsys.readouterr().out
