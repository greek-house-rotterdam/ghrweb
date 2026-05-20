from unittest.mock import patch

import content_review as content_review_mod
from content_review import (
    ERROR_MESSAGE_MAX_LEN,
    format_comment,
    format_unavailable_comment,
    parse_frontmatter,
    review_content,
    severity_emoji,
)


# ---------------------------------------------------------------------------
# parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_splits_frontmatter_and_body(self):
        content = "---\ntitle: Hello\nlang: gr\n---\nBody text"
        fm, body = parse_frontmatter(content)
        assert fm["title"] == "Hello"
        assert fm["lang"] == "gr"
        assert body == "Body text"

    def test_returns_empty_dict_when_no_frontmatter(self):
        content = "Just plain text"
        fm, body = parse_frontmatter(content)
        assert fm == {}
        assert body == "Just plain text"

    def test_strips_quotes_from_values(self):
        content = '---\ntitle: "Quoted Title"\n---\nBody'
        fm, _ = parse_frontmatter(content)
        assert fm["title"] == "Quoted Title"

    def test_strips_single_quotes(self):
        content = "---\ntitle: 'Single Quoted'\n---\nBody"
        fm, _ = parse_frontmatter(content)
        assert fm["title"] == "Single Quoted"

    def test_handles_colons_in_values(self):
        content = "---\ntitle: Time: 19:00\n---\nBody"
        fm, _ = parse_frontmatter(content)
        assert fm["title"] == "Time: 19:00"

    def test_strips_body_whitespace(self):
        content = "---\ntitle: T\n---\n\n  Body  \n\n"
        _, body = parse_frontmatter(content)
        assert body == "Body"


# ---------------------------------------------------------------------------
# severity_emoji
# ---------------------------------------------------------------------------


class TestSeverityEmoji:
    def test_critical(self):
        assert severity_emoji("critical") == "\U0001f534"  # red circle

    def test_major(self):
        assert severity_emoji("major") == "\U0001f7e0"  # orange circle

    def test_minor(self):
        assert severity_emoji("minor") == "\U0001f7e1"  # yellow circle

    def test_unknown_returns_white(self):
        assert severity_emoji("info") == "\u26aa"  # white circle
        assert severity_emoji("") == "\u26aa"


# ---------------------------------------------------------------------------
# format_comment
# ---------------------------------------------------------------------------


class TestFormatComment:
    def test_includes_file_path_in_header(self):
        result = format_comment("src/content/news/gr/post.md", [])
        assert "src/content/news/gr/post.md" in result

    def test_formats_single_finding(self):
        findings = [{"severity": "minor", "field": "title", "message": "Too short"}]
        result = format_comment("test.md", findings)
        assert "MINOR" in result
        assert "title" in result
        assert "Too short" in result

    def test_sorts_by_severity(self):
        findings = [
            {"severity": "minor", "field": "body", "message": "Minor issue"},
            {"severity": "critical", "field": "title", "message": "Critical issue"},
            {"severity": "major", "field": "description", "message": "Major issue"},
        ]
        result = format_comment("test.md", findings)
        lines = [l for l in result.split("\n") if l.startswith("- ")]
        # critical should come before major, major before minor
        assert "CRITICAL" in lines[0]
        assert "MAJOR" in lines[1]
        assert "MINOR" in lines[2]

    def test_handles_missing_fields_gracefully(self):
        findings = [{"severity": "minor"}]  # missing field and message
        result = format_comment("test.md", findings)
        assert "MINOR" in result
        assert "unknown" in result


# ---------------------------------------------------------------------------
# format_unavailable_comment
# ---------------------------------------------------------------------------


class TestFormatUnavailableComment:
    """The "review unavailable" comment is what editors see when the AI
    reviewer could not run for a file. It must clearly communicate that
    the failure is infrastructure-related (not a content issue) and that
    the merge is not blocked."""

    def test_includes_file_path_in_header(self):
        result = format_unavailable_comment(
            "src/content/news/gr/post.md", "Gemini API 503"
        )
        assert "src/content/news/gr/post.md" in result

    def test_states_that_review_is_unavailable(self):
        # Editors must be able to tell this is NOT a content problem.
        result = format_unavailable_comment("test.md", "boom")
        assert "Content review unavailable" in result

    def test_states_that_merge_is_not_blocked(self):
        # Critical for editor UX: they should not think their PR is broken.
        result = format_unavailable_comment("test.md", "boom")
        assert "Merge is not blocked" in result

    def test_surfaces_the_underlying_error(self):
        # Admin needs the error text to diagnose without leaving the PR.
        result = format_unavailable_comment("test.md", "Gemini API 404: model gone")
        assert "Gemini API 404: model gone" in result


# ---------------------------------------------------------------------------
# review_content — covers the new (findings, error) tuple contract
# ---------------------------------------------------------------------------


class _FakeResponse:
    """Minimal stand-in for requests.Response used by review_content."""

    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"{self.status_code} error", response=self)

    def json(self):
        return self._payload


_GEMINI_OK = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {"text": '[{"severity": "minor", "field": "title", "message": "x"}]'}
                ]
            }
        }
    ]
}


class TestReviewContent:
    """review_content() returns (findings, error). Exactly one is meaningful
    per call: a successful run returns ([...], None); a failed run returns
    ([], "<error>"). The error string drives the "review unavailable" PR
    comment in the workflow, so it must be present whenever the API call
    could not be completed."""

    def test_returns_empty_tuple_when_api_key_missing(self):
        # No API key configured = skip review entirely. Treated as a
        # successful no-op (not an error) so no PR comment is posted.
        with patch.object(content_review_mod, "GEMINI_API_KEY", ""):
            findings, error = review_content("test.md", "---\ntitle: T\n---\nBody")
        assert findings == []
        assert error is None

    def test_returns_findings_on_success(self):
        # Happy path: API responds 200 with a JSON array of findings.
        with patch.object(content_review_mod, "GEMINI_API_KEY", "fake-key"), patch.object(
            content_review_mod.requests,
            "post",
            return_value=_FakeResponse(200, _GEMINI_OK),
        ):
            findings, error = review_content("test.md", "---\ntitle: T\n---\nBody")

        assert error is None
        assert len(findings) == 1
        assert findings[0]["severity"] == "minor"

    def test_http_error_returns_error_message(self):
        # On HTTP failure (e.g. model deprecation, 5xx, quota), the function
        # must surface the error so the workflow can post a comment.
        with patch.object(content_review_mod, "GEMINI_API_KEY", "fake-key"), patch.object(
            content_review_mod.requests,
            "post",
            return_value=_FakeResponse(503, text="Service Unavailable"),
        ):
            findings, error = review_content("test.md", "---\ntitle: T\n---\nBody")

        assert findings == []
        assert error is not None
        # The wrapped RuntimeError message includes the status code and body.
        assert "503" in error

    def test_malformed_json_returns_error_message(self):
        # If Gemini returns 200 but the body is not valid JSON, that's still
        # a "review unavailable" situation — surface it as an error.
        bad_payload = {
            "candidates": [{"content": {"parts": [{"text": "not json"}]}}]
        }
        with patch.object(content_review_mod, "GEMINI_API_KEY", "fake-key"), patch.object(
            content_review_mod.requests,
            "post",
            return_value=_FakeResponse(200, bad_payload),
        ):
            findings, error = review_content("test.md", "---\ntitle: T\n---\nBody")

        assert findings == []
        assert error is not None

    def test_long_error_message_is_truncated(self):
        # The error ends up inline in a PR comment, so it must not be a
        # multi-kilobyte API response dump.
        long_body = "X" * (ERROR_MESSAGE_MAX_LEN * 3)
        with patch.object(content_review_mod, "GEMINI_API_KEY", "fake-key"), patch.object(
            content_review_mod.requests,
            "post",
            return_value=_FakeResponse(500, text=long_body),
        ):
            _, error = review_content("test.md", "---\ntitle: T\n---\nBody")

        assert error is not None
        # Truncated form ends with "..." and stays within the cap (+3 for ellipsis).
        assert len(error) <= ERROR_MESSAGE_MAX_LEN + 3
        assert error.endswith("...")
