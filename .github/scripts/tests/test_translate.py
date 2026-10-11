import json
import sys
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

    def test_changes_with_faq_question_and_answer(self):
        """FAQ text lives in question/answer and the body is empty."""
        h1 = compute_source_hash({"question": "Q1", "answer": "A"}, "")
        h2 = compute_source_hash({"question": "Q2", "answer": "A"}, "")
        h3 = compute_source_hash({"question": "Q1", "answer": "B"}, "")
        assert len({h1, h2, h3}) == 3

    def test_changes_with_schedule(self):
        h1 = compute_source_hash({"title": "T", "schedule": "Κάθε Πέμπτη"}, "body")
        h2 = compute_source_hash({"title": "T", "schedule": "Κάθε Παρασκευή"}, "body")
        assert h1 != h2

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

    def test_translates_faq_question_and_answer(self, tmp_path):
        """FAQ text is in frontmatter; it must be translated, not copied."""
        source = tmp_path / "src" / "content" / "faq" / "gr" / "q.md"
        source.parent.mkdir(parents=True)
        source.write_text(
            "---\nquestion: Ερώτηση\nanswer: Απάντηση\norder: 3\nlang: gr\n---\n",
            encoding="utf-8",
        )

        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ) as mock:
            translate_file("fake-key", source, "")
            payload = mock.call_args.args[3]
            assert payload["question"] == "Ερώτηση"
            assert payload["answer"] == "Απάντηση"

        nl_target = tmp_path / "src" / "content" / "faq" / "nl" / "q.md"
        fm, _ = parse_markdown(nl_target.read_text())
        assert fm["question"] == "[nl] Ερώτηση"
        assert fm["answer"] == "[nl] Απάντηση"
        assert fm["order"] == 3

    def test_translates_activity_schedule(self, tmp_path):
        source = self._make(
            tmp_path,
            "gr",
            "---\ntitle: Χορός\nschedule: Κάθε Πέμπτη 19:00\nemoji: 💃\nlang: gr\n---\nBody",
        )

        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ):
            translate_file("fake-key", source, "")

        nl_target = tmp_path / "src" / "content" / "news" / "nl" / "post.md"
        fm, _ = parse_markdown(nl_target.read_text())
        assert fm["schedule"] == "[nl] Κάθε Πέμπτη 19:00"
        assert fm["emoji"] == "💃"


class TestSharedFieldSync:
    """Shared fields (image, date, order, ...) follow the Greek on every run."""

    def _setup(self, tmp_path, source_fm, target_fm, locked=False, hash_matches=True):
        base = tmp_path / "src" / "content" / "news"
        gr, nl = base / "gr" / "post.md", base / "nl" / "post.md"
        gr.parent.mkdir(parents=True)
        nl.parent.mkdir(parents=True)
        gr.write_text(f"---\n{source_fm}---\nBody", encoding="utf-8")
        h = compute_source_hash({"title": "Hello"}, "Body")
        extra = "translation_locked: true\n" if locked else ""
        sh = h if hash_matches else "stale"
        nl.write_text(
            f"---\ntitle: Hallo\n{target_fm}lang: nl\nsource_hash: '{sh}'\n{extra}---\n\nTekst\n",
            encoding="utf-8",
        )
        # an English target that is already in sync, so only NL is under test
        shared = source_fm.replace("title: Hello\n", "").replace("lang: gr\n", "")
        en = base / "en" / "post.md"
        en.parent.mkdir(parents=True)
        en.write_text(
            f"---\ntitle: Hi\n{shared}lang: en\nsource_hash: '{h}'\n---\n\nText\n",
            encoding="utf-8",
        )
        return gr, nl

    def test_image_and_order_change_syncs_without_api_call(self, tmp_path, capsys):
        gr, nl = self._setup(
            tmp_path,
            "title: Hello\nimage: /images/new.jpg\norder: 5\nlang: gr\n",
            "image: /images/old.jpg\norder: 1\n",
        )
        with patch.object(translate_mod, "translate_payload") as mock:
            translate_file("fake-key", gr, "")
            mock.assert_not_called()
        fm, body = parse_markdown(nl.read_text())
        assert fm["image"] == "/images/new.jpg"
        assert fm["order"] == 5
        assert fm["title"] == "Hallo"  # text untouched
        assert body == "Tekst"
        assert list(fm)[:3] == ["title", "image", "order"]  # key order kept
        assert "shared fields synced" in capsys.readouterr().out

    def test_locked_target_is_synced_but_text_kept(self, tmp_path):
        gr, nl = self._setup(
            tmp_path,
            "title: Hello\norder: 7\nlang: gr\n",
            "order: 1\n",
            locked=True,
            hash_matches=False,
        )
        with patch.object(translate_mod, "translate_payload") as mock:
            translate_file("fake-key", gr, "")
            mock.assert_not_called()
        fm, body = parse_markdown(nl.read_text())
        assert fm["order"] == 7
        assert fm["title"] == "Hallo"
        assert fm["translation_locked"] is True
        assert fm["source_hash"] == "stale"
        assert body == "Tekst"

    def test_key_removed_from_source_is_removed_from_target(self, tmp_path):
        gr, nl = self._setup(
            tmp_path,
            "title: Hello\nlang: gr\n",
            "image: /images/old.jpg\n",
        )
        with patch.object(translate_mod, "translate_payload") as mock:
            translate_file("fake-key", gr, "")
            mock.assert_not_called()
        fm, _ = parse_markdown(nl.read_text())
        assert "image" not in fm
        assert fm["title"] == "Hallo"
        assert fm["lang"] == "nl"
        assert "source_hash" in fm

    def test_new_source_key_is_added(self, tmp_path):
        gr, nl = self._setup(tmp_path, "title: Hello\nemoji: 🎉\nlang: gr\n", "")
        translate_file("fake-key", gr, "")
        fm, _ = parse_markdown(nl.read_text())
        assert fm["emoji"] == "🎉"

    def test_nothing_written_when_nothing_changed(self, tmp_path):
        gr, nl = self._setup(
            tmp_path,
            "title: Hello\ndate: 2026-05-01\nlang: gr\n",
            "date: 2026-05-01\n",
        )
        # odd formatting that a rewrite would normalise
        nl.write_text(
            nl.read_text().replace("title: Hallo", "title:   Hallo"), encoding="utf-8"
        )
        before = nl.read_bytes()
        mtime = nl.stat().st_mtime_ns
        with patch.object(translate_mod, "translate_payload") as mock:
            translate_file("fake-key", gr, "")
            mock.assert_not_called()
        assert nl.read_bytes() == before
        assert nl.stat().st_mtime_ns == mtime

    def test_equal_datetime_is_not_a_change(self, tmp_path):
        gr, nl = self._setup(
            tmp_path,
            "title: Hello\ndate: 2026-05-01T10:00:00Z\nlang: gr\n",
            "date: 2026-05-01T10:00:00Z\n",
        )
        nl.write_text(
            nl.read_text().replace("title: Hallo", "title:   Hallo"), encoding="utf-8"
        )
        before = nl.read_bytes()
        translate_file("fake-key", gr, "")
        assert nl.read_bytes() == before

    def test_retranslation_keeps_shared_fields_from_source(self, tmp_path):
        gr, nl = self._setup(
            tmp_path,
            "title: Hello\nimage: /images/a.jpg\norder: 2\nlang: gr\n",
            "image: /images/old.jpg\n",
            hash_matches=False,
        )
        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ):
            translate_file("fake-key", gr, "")
        fm, _ = parse_markdown(nl.read_text())
        assert fm["image"] == "/images/a.jpg"
        assert fm["order"] == 2
        assert fm["lang"] == "nl"
        assert fm["source_hash"] == compute_source_hash({"title": "Hello"}, "Body")


class TestHandWrittenTarget:
    """A4: a target without source_hash that isn't locked is never overwritten."""

    def _setup(self, tmp_path, target_text):
        base = tmp_path / "src" / "content" / "news"
        gr, nl = base / "gr" / "post.md", base / "nl" / "post.md"
        gr.parent.mkdir(parents=True)
        nl.parent.mkdir(parents=True)
        gr.write_text(
            "---\ntitle: Hello\nimage: /images/x.jpg\nlang: gr\n---\nBody",
            encoding="utf-8",
        )
        nl.write_text(target_text, encoding="utf-8")
        return gr, nl

    def test_fails_and_leaves_file_untouched(self, tmp_path):
        text = "---\ntitle: Handgeschreven\nlang: nl\n---\n\nMijn tekst\n"
        gr, nl = self._setup(tmp_path, text)
        with patch.object(translate_mod, "translate_payload") as mock:
            with pytest.raises(translate_mod.HandWrittenTargetError) as exc:
                translate_file("fake-key", gr, "")
            mock.assert_not_called()
        assert nl.read_text() == text
        msg = str(exc.value)
        assert str(nl) in msg
        assert "translation_locked: true" in msg
        assert "source_hash" in msg and "delete" in msg

    def test_main_reports_why_it_failed_for_the_pr_status(self, tmp_path, monkeypatch):
        text = "---\ntitle: Handgeschreven\nlang: nl\n---\n\nMijn tekst\n"
        gr, nl = self._setup(tmp_path, text)
        report = tmp_path / "failure.json"
        monkeypatch.setenv("GEMINI_API_KEY", "k")
        monkeypatch.setenv("TRANSLATE_REPORT", str(report))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["translate.py", str(gr.relative_to(tmp_path))])
        with pytest.raises(SystemExit):
            translate_mod.main()
        data = json.loads(report.read_text(encoding="utf-8"))
        assert data["kind"] == "hand-written" and "written by hand" in data["message"]

    def test_other_targets_are_not_written_first(self, tmp_path):
        """The check runs before any target is translated."""
        gr, nl = self._setup(
            tmp_path, "---\ntitle: Handgeschreven\nlang: nl\n---\n\nTekst\n"
        )
        with pytest.raises(translate_mod.HandWrittenTargetError):
            translate_file("fake-key", gr, "")
        assert not (tmp_path / "src" / "content" / "news" / "en" / "post.md").exists()

    def test_locked_hand_written_file_is_fine(self, tmp_path):
        gr, nl = self._setup(
            tmp_path,
            "---\ntitle: Handgeschreven\nlang: nl\ntranslation_locked: true\n---\n\nTekst\n",
        )
        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ):
            translate_file("fake-key", gr, "")
        fm, body = parse_markdown(nl.read_text())
        assert fm["title"] == "Handgeschreven"
        assert fm["image"] == "/images/x.jpg"  # shared field synced
        assert body == "Tekst"

    def test_unparseable_target_is_still_retranslated(self, tmp_path):
        gr, nl = self._setup(tmp_path, "no frontmatter here")
        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ):
            translate_file("fake-key", gr, "")
        fm, _ = parse_markdown(nl.read_text())
        assert fm["lang"] == "nl"
        assert "source_hash" in fm


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

        def fake_post(url, params=None, headers=None, json=None, timeout=None):
            captured["url"] = url
            captured["params"] = params
            captured["headers"] = headers
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
        assert captured["headers"] == {"x-goog-api-key": "test-key"}
        # The key must never be in the URL: requests errors print the URL.
        assert captured["params"] is None
        assert "key=" not in captured["url"]
        # System prompt includes the guidelines
        sys_text = captured["json"]["systemInstruction"]["parts"][0]["text"]
        assert "tone guidelines text" in sys_text
        assert "Greek to Dutch" in sys_text
        # User content includes the source payload
        user_text = captured["json"]["contents"][0]["parts"][0]["text"]
        assert "Γεια" in user_text
        assert "Σώμα" in user_text


# ---------------------------------------------------------------------------
# A9: hand-corrected translations are kept and flagged
# ---------------------------------------------------------------------------


class TestKeepHandFixedTranslations:
    GR = "---\ntitle: Γεια\nimage: /images/a.jpg\nlang: gr\n---\nΚείμενο"

    def _setup(self, tmp_path, gr_text=None):
        base = tmp_path / "src" / "content" / "news"
        for lang in ("gr", "nl", "en"):
            (base / lang).mkdir(parents=True)
        gr = base / "gr" / "post.md"
        gr.write_text(gr_text or self.GR, encoding="utf-8")
        return gr, base / "nl" / "post.md", base / "en" / "post.md"

    def _translate_all(self, gr):
        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ):
            return translate_file("k", gr, "")

    def _change_greek(self, gr, new="Αλλαγμένο κείμενο"):
        gr.write_text(self.GR.replace("Κείμενο", new), encoding="utf-8")

    def _hand_edit(self, nl):
        nl.write_text(
            nl.read_text(encoding="utf-8").replace("[nl] Κείμενο", "Mijn correctie"),
            encoding="utf-8",
        )

    def test_bot_writes_translation_hash_matching_its_text(self, tmp_path):
        gr, nl, _ = self._setup(tmp_path)
        self._translate_all(gr)
        fm, body = parse_markdown(nl.read_text())
        assert fm["translation_hash"] == compute_source_hash(fm, body)
        assert "translation_hash: '" in nl.read_text()  # quoted, stays a string
        assert not translate_mod.is_hand_edited(fm, body)

    def test_hash_is_consistent_for_multiline_and_quoted_text(self, tmp_path):
        gr, nl, _ = self._setup(
            tmp_path,
            "---\ntitle: Χορός\nschedule: 'Κάθε: Πέμπτη'\nlang: gr\n---\nA\n\n- β: γ\n",
        )

        def fake(api_key, s, t, payload, g):
            return {
                k: f"  «{t}»: {v}\n\nline2 # not a comment " for k, v in payload.items()
            }

        with patch.object(translate_mod, "translate_payload", side_effect=fake):
            translate_file("k", gr, "")
        fm, body = parse_markdown(nl.read_text())
        assert not translate_mod.is_hand_edited(fm, body)

    def test_hand_edited_target_is_kept_when_greek_changes(self, tmp_path, capsys):
        gr, nl, en = self._setup(tmp_path)
        self._translate_all(gr)
        original = parse_markdown(nl.read_text())[0]
        self._hand_edit(nl)
        self._change_greek(gr)
        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ) as mock:
            kept = translate_file("k", gr, "")
        assert [c.args[2] for c in mock.call_args_list] == ["en"]  # no call for nl
        fm, body = parse_markdown(nl.read_text())
        assert body == "Mijn correctie"
        assert fm["source_hash"] == compute_source_hash(
            {"title": "Γεια"}, "Αλλαγμένο κείμενο"
        )
        assert fm["translation_hash"] == original["translation_hash"]
        assert kept == [(nl, "Γεια")]
        out = capsys.readouterr().out
        assert "::warning title=Kept a hand-corrected translation::" in out

    def test_kept_target_still_gets_shared_fields(self, tmp_path):
        gr, nl, _ = self._setup(tmp_path)
        self._translate_all(gr)
        self._hand_edit(nl)
        gr.write_text(
            self.GR.replace("Κείμενο", "Νέο").replace("a.jpg", "b.jpg"),
            encoding="utf-8",
        )
        self._translate_all(gr)
        fm, body = parse_markdown(nl.read_text())
        assert fm["image"] == "/images/b.jpg"
        assert body == "Mijn correctie"

    def test_flagged_once_then_flagged_again_on_next_greek_change(self, tmp_path):
        gr, nl, _ = self._setup(tmp_path)
        self._translate_all(gr)
        self._hand_edit(nl)
        self._change_greek(gr, "Δεύτερο")
        assert len(self._translate_all(gr)) == 1
        assert self._translate_all(gr) == []  # same Greek again: not flagged
        self._change_greek(gr, "Τρίτο")
        assert len(self._translate_all(gr)) == 1  # still hand-edited
        assert parse_markdown(nl.read_text())[1] == "Mijn correctie"

    def test_unedited_target_is_retranslated_with_new_hash(self, tmp_path):
        gr, nl, _ = self._setup(tmp_path)
        self._translate_all(gr)
        old = parse_markdown(nl.read_text())[0]["translation_hash"]
        self._change_greek(gr)
        assert self._translate_all(gr) == []
        fm, body = parse_markdown(nl.read_text())
        assert body == "[nl] Αλλαγμένο κείμενο"
        assert fm["translation_hash"] != old
        assert fm["translation_hash"] == compute_source_hash(fm, body)

    def test_no_translation_hash_means_retranslate(self, tmp_path):
        gr, nl, _ = self._setup(tmp_path)
        self._translate_all(gr)
        lines = nl.read_text(encoding="utf-8").splitlines()
        nl.write_text(
            "\n".join(l for l in lines if not l.startswith("translation_hash")) + "\n",
            encoding="utf-8",
        )
        self._hand_edit(nl)
        self._change_greek(gr)
        assert self._translate_all(gr) == []
        fm, body = parse_markdown(nl.read_text())
        assert body == "[nl] Αλλαγμένο κείμενο"
        assert "translation_hash" in fm

    def test_locked_target_unchanged(self, tmp_path):
        gr, nl, _ = self._setup(tmp_path)
        self._translate_all(gr)
        self._hand_edit(nl)
        nl.write_text(
            nl.read_text(encoding="utf-8").replace(
                "lang: nl\n", "lang: nl\ntranslation_locked: true\n"
            ),
            encoding="utf-8",
        )
        before = parse_markdown(nl.read_text())
        self._change_greek(gr)
        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ) as mock:
            kept = translate_file("k", gr, "")
        assert [c.args[2] for c in mock.call_args_list] == ["en"]
        assert kept == []  # locked is not "kept"
        assert parse_markdown(nl.read_text()) == before  # source_hash not touched

    def test_hand_edit_and_greek_change_in_one_run_keeps_the_edit(self, tmp_path):
        # The editor's PR contains both the NL fix and the new Greek.
        gr, nl, _ = self._setup(tmp_path)
        self._translate_all(gr)
        self._hand_edit(nl)
        self._change_greek(gr)
        kept = self._translate_all(gr)
        assert len(kept) == 1
        assert parse_markdown(nl.read_text())[1] == "Mijn correctie"

    def test_unchanged_greek_with_hand_edit_writes_nothing(self, tmp_path):
        gr, nl, _ = self._setup(tmp_path)
        self._translate_all(gr)
        self._hand_edit(nl)
        before = nl.read_bytes()
        with patch.object(translate_mod, "translate_payload") as mock:
            assert translate_file("k", gr, "") == []
            mock.assert_not_called()
        assert nl.read_bytes() == before

    def test_kept_list_is_written_for_the_pr_notice(self, tmp_path, monkeypatch):
        gr, nl, _ = self._setup(tmp_path)
        self._translate_all(gr)
        self._hand_edit(nl)
        self._change_greek(gr)
        report = tmp_path / "kept.md"
        monkeypatch.setenv("GEMINI_API_KEY", "k")
        monkeypatch.setenv("KEPT_REPORT", str(report))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            sys, "argv", ["translate.py", str(gr.relative_to(tmp_path))]
        )
        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ):
            translate_mod.main()
        assert report.read_text(encoding="utf-8") == (
            f"- «Γεια» (NL): `{nl.relative_to(tmp_path)}`\n"
        )

    def test_no_report_file_when_nothing_was_kept(self, tmp_path, monkeypatch):
        gr, _, _ = self._setup(tmp_path)
        report = tmp_path / "kept.md"
        monkeypatch.setenv("GEMINI_API_KEY", "k")
        monkeypatch.setenv("KEPT_REPORT", str(report))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            sys, "argv", ["translate.py", str(gr.relative_to(tmp_path))]
        )
        with patch.object(
            translate_mod, "translate_payload", side_effect=_fake_translation
        ):
            translate_mod.main()
        assert not report.exists()

    def test_backfilled_hash_equals_what_the_bot_writes(self, tmp_path):
        """Backfill hashes the file as it reads; the bot's hash is the same function."""
        gr, nl, _ = self._setup(tmp_path)
        self._translate_all(gr)
        fm, body = parse_markdown(nl.read_text())
        bot_hash = fm.pop("translation_hash")
        assert compute_source_hash(fm, body) == bot_hash


class TestNonGreekSource:
    def _write(self, tmp_path, lang, extra=""):
        p = tmp_path / "src" / "content" / "news" / lang / "post.md"
        p.parent.mkdir(parents=True)
        p.write_text(
            f"---\ntitle: Hallo\nlang: {lang}\n{extra}---\nTekst", encoding="utf-8"
        )
        return p

    @pytest.mark.parametrize("lang", ["nl", "en"])
    def test_unlocked_non_greek_source_fails_with_clear_message(self, tmp_path, lang):
        p = self._write(tmp_path, lang)
        with patch.object(translate_mod, "translate_payload") as mock:
            with pytest.raises(translate_mod.NonGreekSourceError) as exc:
                translate_file("k", p, "")
            mock.assert_not_called()
        msg = str(exc.value)
        assert str(p) in msg and "written in Greek" in msg
        assert "translation_locked: true" in msg
        assert not (tmp_path / "src" / "content" / "news" / "gr").exists()

    def test_locked_non_greek_file_is_skipped(self, tmp_path):
        p = self._write(tmp_path, "nl", "translation_locked: true\n")
        with patch.object(translate_mod, "translate_payload") as mock:
            assert translate_file("k", p, "") == []
            mock.assert_not_called()
        assert not (tmp_path / "src" / "content" / "news" / "gr").exists()

    @pytest.mark.parametrize("lang,kind", [("nl", "non-greek")])
    def test_main_reports_why_it_failed_for_the_pr_status(self, tmp_path, monkeypatch, lang, kind):
        p = self._write(tmp_path, lang)
        report = tmp_path / "failure.json"
        monkeypatch.setenv("GEMINI_API_KEY", "k")
        monkeypatch.setenv("TRANSLATE_REPORT", str(report))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["translate.py", str(p.relative_to(tmp_path))])
        with pytest.raises(SystemExit):
            translate_mod.main()
        data = json.loads(report.read_text(encoding="utf-8"))
        assert data["kind"] == kind and "written in Greek" in data["message"]

    def test_non_greek_file_with_source_hash_is_still_just_skipped(self, tmp_path):
        p = self._write(tmp_path, "en", "source_hash: abc\n")
        assert translate_file("k", p, "") == []
