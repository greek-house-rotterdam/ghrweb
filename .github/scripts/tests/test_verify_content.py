from pathlib import Path
from unittest.mock import patch

from verify_content import get_collections, verify_collection


class TestGetCollections:
    def test_returns_directories(self, tmp_path):
        (tmp_path / "news").mkdir()
        (tmp_path / "events").mkdir()
        (tmp_path / "readme.md").touch()  # file, not dir — should be excluded

        with patch("verify_content.CONTENT_DIR", tmp_path):
            result = get_collections()

        names = {d.name for d in result}
        assert "news" in names
        assert "events" in names
        assert "readme.md" not in names

    def test_returns_empty_when_dir_missing(self, tmp_path):
        with patch("verify_content.CONTENT_DIR", tmp_path / "nonexistent"):
            result = get_collections()
        assert result == []


class TestVerifyCollection:
    def _make_collection(self, tmp_path, name, files_by_lang):
        """Helper to create a collection with files per language.

        files_by_lang: dict mapping lang -> list of filenames
        Example: {"gr": ["a.md", "b.md"], "nl": ["a.md"], "en": ["a.md", "b.md"]}
        """
        col_dir = tmp_path / name
        for lang, filenames in files_by_lang.items():
            lang_dir = col_dir / lang
            lang_dir.mkdir(parents=True, exist_ok=True)
            for fn in filenames:
                (lang_dir / fn).touch()
        return col_dir

    def test_no_errors_when_all_files_present(self, tmp_path):
        col = self._make_collection(tmp_path, "news", {
            "gr": ["a.md", "b.md"],
            "nl": ["a.md", "b.md"],
            "en": ["a.md", "b.md"],
        })
        errors = verify_collection(col)
        assert errors == []

    def test_detects_missing_file_in_one_language(self, tmp_path):
        col = self._make_collection(tmp_path, "news", {
            "gr": ["a.md", "b.md"],
            "nl": ["a.md"],          # missing b.md
            "en": ["a.md", "b.md"],
        })
        errors = verify_collection(col)
        assert len(errors) == 1
        assert "nl" in errors[0]
        assert "b.md" in errors[0]

    def test_detects_multiple_missing_files(self, tmp_path):
        col = self._make_collection(tmp_path, "events", {
            "gr": ["a.md", "b.md", "c.md"],
            "nl": ["a.md"],                    # missing b.md, c.md
            "en": ["a.md", "b.md"],            # missing c.md
        })
        errors = verify_collection(col)
        assert len(errors) == 3

    def test_handles_empty_language_dir(self, tmp_path):
        col = self._make_collection(tmp_path, "faq", {
            "gr": ["a.md"],
            "nl": [],       # empty
            "en": ["a.md"],
        })
        errors = verify_collection(col)
        assert len(errors) == 1
        assert "nl" in errors[0]

    def test_handles_missing_language_dir(self, tmp_path):
        """If a language directory doesn't exist at all, files are reported missing."""
        col = tmp_path / "news"
        (col / "gr").mkdir(parents=True)
        (col / "gr" / "post.md").touch()
        (col / "en").mkdir(parents=True)
        (col / "en" / "post.md").touch()
        # nl dir doesn't exist at all

        errors = verify_collection(col)
        assert len(errors) == 1
        assert "nl" in errors[0]

    def test_no_errors_for_empty_collection(self, tmp_path):
        col = self._make_collection(tmp_path, "empty", {
            "gr": [],
            "nl": [],
            "en": [],
        })
        errors = verify_collection(col)
        assert errors == []
