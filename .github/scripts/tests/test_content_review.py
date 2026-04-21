from content_review import format_comment, parse_frontmatter, severity_emoji


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
