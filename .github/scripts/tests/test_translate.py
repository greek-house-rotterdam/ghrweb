from pathlib import Path
from unittest.mock import patch

import pytest

import translate as translate_mod
from translate import (
    build_markdown,
    compute_source_hash,
    get_source_lang,
    get_target_langs,
    parse_markdown,
    translate_file,
)


# ---------------------------------------------------------------------------
# compute_source_hash
# ---------------------------------------------------------------------------


class TestComputeSourceHash:
    def test_deterministic(self):
        h1 = compute_source_hash({"title": "Hello", "description": "World"}, "body")
        h2 = compute_source_hash({"title": "Hello", "description": "World"}, "body")
        assert h1 == h2

    def test_returns_12_hex_chars(self):
        h = compute_source_hash({"title": "Test"}, "body")
        assert len(h) == 12
        assert all(c in "0123456789abcdef" for c in h)

    def test_changes_with_title(self):
        h1 = compute_source_hash({"title": "A"}, "body")
        h2 = compute_source_hash({"title": "B"}, "body")
        assert h1 != h2

    def test_changes_with_description(self):
        h1 = compute_source_hash({"title": "T", "description": "A"}, "body")
        h2 = compute_source_hash({"title": "T", "description": "B"}, "body")
        assert h1 != h2

    def test_changes_with_body(self):
        h1 = compute_source_hash({"title": "T"}, "body1")
        h2 = compute_source_hash({"title": "T"}, "body2")
        assert h1 != h2

    def test_ignores_non_translatable_fields(self):
        """Fields like lang, order, date should not affect the hash."""
        h1 = compute_source_hash({"title": "T", "lang": "gr", "order": 1}, "body")
        h2 = compute_source_hash({"title": "T", "lang": "nl", "order": 99}, "body")
        assert h1 == h2

    def test_empty_field_is_skipped(self):
        h1 = compute_source_hash({"title": "T"}, "body")
        h2 = compute_source_hash({"title": "T", "description": ""}, "body")
        assert h1 == h2

    def test_field_order_does_not_matter(self):
        h1 = compute_source_hash({"title": "T", "description": "D"}, "body")
        h2 = compute_source_hash({"description": "D", "title": "T"}, "body")
        assert h1 == h2


# ---------------------------------------------------------------------------
# get_source_lang
# ---------------------------------------------------------------------------


class TestGetSourceLang:
    def test_extracts_gr(self):
        assert get_source_lang(Path("src/content/news/gr/post.md")) == "gr"

    def test_extracts_nl(self):
        assert get_source_lang(Path("src/content/events/nl/event.md")) == "nl"

    def test_extracts_en(self):
        assert get_source_lang(Path("src/content/faq/en/question.md")) == "en"

    def test_raises_for_unknown_language(self):
        with pytest.raises(ValueError, match="No known language"):
            get_source_lang(Path("src/content/news/fr/post.md"))

    def test_raises_for_path_without_language(self):
        with pytest.raises(ValueError):
            get_source_lang(Path("src/content/news/post.md"))


# ---------------------------------------------------------------------------
# get_target_langs
# ---------------------------------------------------------------------------


class TestGetTargetLangs:
    def test_gr_returns_nl_and_en(self):
        assert set(get_target_langs("gr")) == {"nl", "en"}

    def test_nl_returns_gr_and_en(self):
        assert set(get_target_langs("nl")) == {"gr", "en"}

    def test_en_returns_gr_and_nl(self):
        assert set(get_target_langs("en")) == {"gr", "nl"}

    def test_always_returns_two_targets(self):
        for lang in ("gr", "nl", "en"):
            assert len(get_target_langs(lang)) == 2


# ---------------------------------------------------------------------------
# parse_markdown / build_markdown
# ---------------------------------------------------------------------------


class TestParseMarkdown:
    def test_splits_frontmatter_and_body(self):
        text = "---\ntitle: Hello\nlang: gr\n---\nBody text"
        fm, body = parse_markdown(text)
        assert fm["title"] == "Hello"
        assert fm["lang"] == "gr"
        assert body == "Body text"

    def test_raises_on_missing_frontmatter(self):
        with pytest.raises(ValueError, match="No valid YAML"):
            parse_markdown("Just text, no frontmatter")

    def test_strips_body_whitespace(self):
        text = "---\ntitle: T\n---\n\n  Body  \n\n"
        _, body = parse_markdown(text)
        assert body == "Body"

    def test_multiline_body(self):
        text = "---\ntitle: T\n---\nLine 1\n\nLine 2\n\nLine 3"
        _, body = parse_markdown(text)
        assert "Line 1" in body
        assert "Line 2" in body
        assert "Line 3" in body

    def test_boolean_and_numeric_values(self):
        text = "---\ntitle: T\nregistrationRequired: true\norder: 5\n---\nBody"
        fm, _ = parse_markdown(text)
        assert fm["registrationRequired"] is True
        assert fm["order"] == 5


class TestBuildMarkdown:
    def test_wraps_in_frontmatter_delimiters(self):
        result = build_markdown({"title": "Hello"}, "Body")
        assert result.startswith("---\n")
        assert "---\n\nBody\n" in result

    def test_includes_all_fields(self):
        result = build_markdown({"title": "T", "lang": "gr"}, "Body")
        assert "title: T" in result
        assert "lang: gr" in result

    def test_roundtrip_preserves_content(self):
        fm_in = {"title": "Post Title", "description": "A description", "lang": "gr"}
        body_in = "Some markdown content"
        rebuilt = build_markdown(fm_in, body_in)
        fm_out, body_out = parse_markdown(rebuilt)
        assert fm_out["title"] == fm_in["title"]
        assert fm_out["description"] == fm_in["description"]
        assert body_out == body_in


# ---------------------------------------------------------------------------
# translate_file (mocking translate_payload to avoid real API calls)
# ---------------------------------------------------------------------------


def _fake_translation(api_key, source_lang, target_lang, payload, guidelines):
    """Return a deterministic translation for tests: prefix each value with target lang."""
    return {k: f"[{target_lang}] {v}" if v else v for k, v in payload.items()}


class TestTranslateFile:
    def _make(self, tmp_path, lang, content):
        """Create a content file in the expected directory structure."""
        path = tmp_path / "src" / "content" / "news" / lang / "post.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_skips_files_that_are_translations(self, tmp_path):
        """Files with source_hash in frontmatter are translations, not sources."""
        source = self._make(
            tmp_path,
            "gr",
            "---\ntitle: Test\nsource_hash: abc123\nlang: gr\n---\nBody",
        )
        with patch.object(translate_mod, "translate_payload") as mock:
            translate_file("fake-key", source, "")
            mock.assert_not_called()

    def test_skips_locked_target(self, tmp_path):
        """Target files with translation_locked: true must not be overwritten."""
        source = self._make(
            tmp_path, "gr", "---\ntitle: Source\nlang: gr\n---\nBody"
        )
        locked_path = tmp_path / "src" / "content" / "news" / "nl" / "post.md"
        locked_path.parent.mkdir(parents=True, exist_ok=True)
        locked_path.write_text(
            "---\ntitle: Locked\nlang: nl\nsource_hash: old\ntranslation_locked: true\n---\nLocked",
            encoding="utf-8",
        )

        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ):
            translate_file("fake-key", source, "")

        # Locked target should be untouched
        assert "Locked" in locked_path.read_text()

    def test_skips_when_source_hash_matches(self, tmp_path):
        """If source hasn't changed (hash matches), skip re-translation."""
        source = self._make(
            tmp_path,
            "gr",
            "---\ntitle: Hello\ndescription: Desc\nlang: gr\n---\nBody",
        )
        current_hash = compute_source_hash(
            {"title": "Hello", "description": "Desc"}, "Body"
        )
        for lang in ("nl", "en"):
            p = tmp_path / "src" / "content" / "news" / lang / "post.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(
                f"---\ntitle: x\nlang: {lang}\nsource_hash: {current_hash}\n---\nbody",
                encoding="utf-8",
            )

        with patch.object(translate_mod, "translate_payload") as mock:
            translate_file("fake-key", source, "")
            mock.assert_not_called()

    def test_translates_when_target_missing(self, tmp_path):
        """New file with no existing translations should be translated."""
        source = self._make(
            tmp_path,
            "gr",
            "---\ntitle: New Post\ndescription: A new post\nlang: gr\n---\nContent here",
        )

        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ) as mock:
            translate_file("fake-key", source, "")
            # Called once per target language (nl, en)
            assert mock.call_count == 2

        # Target files should now exist
        nl_target = tmp_path / "src" / "content" / "news" / "nl" / "post.md"
        en_target = tmp_path / "src" / "content" / "news" / "en" / "post.md"
        assert nl_target.exists()
        assert en_target.exists()

    def test_translated_file_has_source_hash(self, tmp_path):
        """Translated files must include source_hash in frontmatter."""
        source = self._make(
            tmp_path, "gr", "---\ntitle: Test\nlang: gr\n---\nBody"
        )

        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ):
            translate_file("fake-key", source, "")

        nl_target = tmp_path / "src" / "content" / "news" / "nl" / "post.md"
        content = nl_target.read_text()
        assert "source_hash:" in content

    def test_translated_file_has_correct_lang(self, tmp_path):
        """Translated files must have lang set to the target language."""
        source = self._make(
            tmp_path, "gr", "---\ntitle: Test\nlang: gr\n---\nBody"
        )

        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ):
            translate_file("fake-key", source, "")

        nl_target = tmp_path / "src" / "content" / "news" / "nl" / "post.md"
        fm, _ = parse_markdown(nl_target.read_text())
        assert fm["lang"] == "nl"

    def test_translated_body_uses_returned_value(self, tmp_path):
        """The body in the output file should come from the translation result."""
        source = self._make(
            tmp_path,
            "gr",
            "---\ntitle: Title\nlang: gr\n---\nOriginal body content",
        )

        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ):
            translate_file("fake-key", source, "")

        nl_target = tmp_path / "src" / "content" / "news" / "nl" / "post.md"
        _, body = parse_markdown(nl_target.read_text())
        assert body == "[nl] Original body content"


# ---------------------------------------------------------------------------
# translate_payload — input/output shape (without hitting the real API)
# ---------------------------------------------------------------------------


class TestTranslatePayload:
    def test_empty_payload_returns_unchanged(self):
        """No translatable text → no API call, return as-is."""
        result = translate_mod.translate_payload(
            "fake-key", "gr", "nl", {"title": "", "description": "", "body": "  "}, ""
        )
        assert result == {"title": "", "description": "", "body": "  "}

    def test_calls_gemini_with_expected_shape(self):
        """The HTTP request payload contains the source content + system prompt."""
        captured = {}

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "text": '{"title": "Hallo", "body": "Vertaald"}'
                                    }
                                ]
                            }
                        }
                    ]
                }

        def fake_post(url, params=None, json=None, timeout=None):
            captured["url"] = url
            captured["params"] = params
            captured["json"] = json
            return FakeResponse()

        with patch.object(translate_mod.requests, "post", side_effect=fake_post):
            result = translate_mod.translate_payload(
                "test-key",
                "gr",
                "nl",
                {"title": "Γεια", "body": "Σώμα"},
                "tone guidelines text",
            )

        assert result == {"title": "Hallo", "body": "Vertaald"}
        assert captured["params"] == {"key": "test-key"}
        # System prompt includes the guidelines
        sys_text = captured["json"]["systemInstruction"]["parts"][0]["text"]
        assert "tone guidelines text" in sys_text
        assert "Greek to Dutch" in sys_text
        # User content includes the source payload
        user_text = captured["json"]["contents"][0]["parts"][0]["text"]
        assert "Γεια" in user_text
        assert "Σώμα" in user_text
