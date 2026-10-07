import json

import pytest

import pr_notice
from pr_notice import build_body, clear_notice, main, marker, set_notice


class FakeGh:
    """Stands in for the gh CLI: serves a fixed comment list and records calls."""

    def __init__(self, comments=()):
        self.comments = list(comments)
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        if args[:2] == ("api", "repos/o/r/issues/7/comments") and "--paginate" in args:
            return "\n".join(json.dumps(c) for c in self.comments) + "\n"
        return ""

    def writes(self):
        """Calls other than the comment listing."""
        return [c for c in self.calls if "--paginate" not in c]


# ---------------------------------------------------------------------------
# build_body
# ---------------------------------------------------------------------------


class TestBuildBody:
    def test_starts_with_topic_marker(self):
        # The marker is how later runs find this comment again.
        body = build_body("translate", "@PanoEvJ", "https://run")
        assert body.startswith(marker("translate"))

    def test_has_greek_and_english_text(self):
        body = build_body("translate", "", "")
        assert "Η αυτόματη μετάφραση" in body
        assert "The automatic translation" in body

    def test_mentions_admins_and_links_run(self):
        body = build_body("review", "@PanoEvJ @someone", "https://run/1")
        assert "cc @PanoEvJ @someone" in body
        assert "[workflow run](https://run/1)" in body

    def test_omits_footer_when_nothing_to_show(self):
        body = build_body("review", "  ", "")
        assert "cc" not in body
        assert "workflow run" not in body

    def test_review_notice_says_publishing_is_not_blocked(self):
        # The review check is advisory; editors must not think they're stuck.
        assert "does not block publishing" in build_body("review", "", "")

    def test_adds_details_below_the_text(self):
        body = build_body("images", "@PanoEvJ", "", "- `a.heic`: Unsupported format\n")
        assert body.index("*An image can't be used") < body.index("- `a.heic`") < body.index("cc @PanoEvJ")

    def test_images_notice_tells_the_editor_what_to_do(self):
        # Unlike the other notices, the editor can fix this one themselves.
        body = build_body("images", "", "")
        assert "Ανέβασε" in body
        assert "JPEG, PNG or WebP" in body


# ---------------------------------------------------------------------------
# set_notice / clear_notice
# ---------------------------------------------------------------------------


class TestSetNotice:
    def test_creates_when_no_notice_exists(self):
        gh = FakeGh([{"id": 1, "body": "unrelated comment"}])
        assert set_notice("o/r", "7", "translate", "BODY", gh) == "created"
        assert gh.writes() == [
            ("api", "repos/o/r/issues/7/comments", "-f", "body=BODY", "--silent")
        ]

    def test_updates_existing_notice_in_place(self):
        gh = FakeGh([{"id": 5, "body": f"{marker('translate')}\nold"}])
        assert set_notice("o/r", "7", "translate", "NEW", gh) == "updated"
        assert gh.writes() == [
            ("api", "-X", "PATCH", "repos/o/r/issues/comments/5", "-f", "body=NEW", "--silent")
        ]

    def test_removes_duplicate_notices(self):
        gh = FakeGh([
            {"id": 5, "body": marker("translate")},
            {"id": 6, "body": marker("translate")},
        ])
        set_notice("o/r", "7", "translate", "NEW", gh)
        assert ("api", "-X", "DELETE", "repos/o/r/issues/comments/6", "--silent") in gh.writes()

    def test_ignores_other_topics(self):
        # A review notice must not be overwritten by a translate notice.
        gh = FakeGh([{"id": 5, "body": marker("review")}])
        assert set_notice("o/r", "7", "translate", "NEW", gh) == "created"


class TestClearNotice:
    def test_deletes_all_notices_for_topic(self):
        gh = FakeGh([
            {"id": 5, "body": marker("translate")},
            {"id": 6, "body": "other"},
            {"id": 8, "body": marker("translate")},
        ])
        assert clear_notice("o/r", "7", "translate", gh) == 2
        assert gh.writes() == [
            ("api", "-X", "DELETE", "repos/o/r/issues/comments/5", "--silent"),
            ("api", "-X", "DELETE", "repos/o/r/issues/comments/8", "--silent"),
        ]

    def test_no_op_when_nothing_to_clear(self):
        gh = FakeGh([{"id": 6, "body": "other"}])
        assert clear_notice("o/r", "7", "review", gh) == 0
        assert gh.writes() == []

    def test_handles_null_comment_body(self):
        gh = FakeGh([{"id": 6, "body": None}])
        assert clear_notice("o/r", "7", "review", gh) == 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    @pytest.fixture(autouse=True)
    def _env(self, monkeypatch):
        monkeypatch.setenv("REPO", "o/r")
        monkeypatch.setenv("PR_NUMBER", "7")
        monkeypatch.setenv("ADMIN_MENTIONS", "@PanoEvJ")
        monkeypatch.setenv("RUN_URL", "https://run/1")

    @pytest.mark.parametrize("argv", [
        [], ["set"], ["post", "translate"], ["set", "nope"],
        ["clear", "images", "details.md"], ["set", "images", "a.md", "b.md"],
    ])
    def test_rejects_bad_arguments(self, argv):
        assert main(argv, FakeGh()) == 2

    def test_set_includes_details_file(self, tmp_path):
        details = tmp_path / "problems.md"
        details.write_text("- `public/images/a.heic`: Unsupported format\n", encoding="utf-8")
        gh = FakeGh()
        assert main(["set", "images", str(details)], gh) == 0
        (call,) = gh.writes()
        assert "- `public/images/a.heic`: Unsupported format" in call[3]

    def test_set_without_details_file_still_posts(self, tmp_path):
        # A crash before the report was written must not hide the notice.
        gh = FakeGh()
        assert main(["set", "images", str(tmp_path / "missing.md")], gh) == 0
        (call,) = gh.writes()
        assert call[3].removeprefix("body=") == build_body("images", "@PanoEvJ", "https://run/1")

    def test_set_posts_full_notice(self):
        gh = FakeGh()
        assert main(["set", "translate"], gh) == 0
        (call,) = gh.writes()
        body = call[3].removeprefix("body=")
        assert body == build_body("translate", "@PanoEvJ", "https://run/1")

    def test_clear_removes_notice(self):
        gh = FakeGh([{"id": 5, "body": marker("review")}])
        assert main(["clear", "review"], gh) == 0
        assert gh.writes() == [("api", "-X", "DELETE", "repos/o/r/issues/comments/5", "--silent")]


def test_every_topic_has_heading_greek_and_english():
    for topic, parts in pr_notice.NOTICES.items():
        assert len(parts) == 3 and all(parts), topic
