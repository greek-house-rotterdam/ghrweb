from pathlib import Path

from sync_deletions import get_counterparts, main, plan


class TestGetCounterparts:
    def test_gr_returns_nl_and_en(self):
        result = get_counterparts(Path("src/content/news/gr/post.md"))
        langs = {p.parts[-2] for p in result}
        assert langs == {"nl", "en"}

    def test_nl_returns_gr_and_en(self):
        result = get_counterparts(Path("src/content/events/nl/event.md"))
        langs = {p.parts[-2] for p in result}
        assert langs == {"gr", "en"}

    def test_en_returns_gr_and_nl(self):
        result = get_counterparts(Path("src/content/faq/en/question.md"))
        langs = {p.parts[-2] for p in result}
        assert langs == {"gr", "nl"}

    def test_preserves_collection_and_filename(self):
        result = get_counterparts(Path("src/content/news/gr/my-post.md"))
        for p in result:
            assert p.parts[0] == "src"
            assert p.parts[1] == "content"
            assert p.parts[2] == "news"
            assert p.name == "my-post.md"

    def test_returns_exactly_two(self):
        result = get_counterparts(Path("src/content/news/gr/post.md"))
        assert len(result) == 2

    def test_returns_empty_for_unknown_language(self):
        result = get_counterparts(Path("src/content/news/fr/post.md"))
        assert result == []

    def test_returns_empty_for_path_without_language(self):
        result = get_counterparts(Path("src/content/news/post.md"))
        assert result == []

    def test_works_with_activities_collection(self):
        result = get_counterparts(Path("src/content/activities/nl/dance.md"))
        paths = {str(p) for p in result}
        assert any("activities/gr/dance.md" in p for p in paths)
        assert any("activities/en/dance.md" in p for p in paths)

    def test_works_with_resources_collection(self):
        result = get_counterparts(Path("src/content/resources/en/info.md"))
        assert len(result) == 2
        langs = {p.parts[-2] for p in result}
        assert langs == {"gr", "nl"}


GR = Path("src/content/news/gr/post.md")
NL = Path("src/content/news/nl/post.md")
EN = Path("src/content/news/en/post.md")


def on_disk(*paths: Path):
    """An `exists` stand-in: these files are still in the checkout."""
    present = set(paths)
    return lambda p: p in present


class TestPlan:
    def test_deleting_the_greek_removes_the_translations(self):
        assert plan([GR], on_disk(NL, EN)) == ([NL, EN], [])

    def test_deleting_a_translation_keeps_the_post_and_translates_it_again(self):
        # The bug this fixes: this used to delete the Greek source and Dutch too.
        assert plan([EN], on_disk(GR, NL)) == ([], [GR])

    def test_deleting_both_translations_translates_the_greek_once(self):
        assert plan([NL, EN], on_disk(GR)) == ([], [GR])

    def test_deleting_the_greek_and_a_translation_removes_the_rest(self):
        assert plan([GR, EN], on_disk(NL)) == ([NL], [])

    def test_translations_already_gone_are_not_listed(self):
        assert plan([GR], on_disk()) == ([], [])

    def test_ignores_paths_without_a_language(self):
        assert plan([Path("src/content/news/post.md")], on_disk(GR)) == ([], [])


class TestMain:
    def test_deletes_translations_of_a_deleted_greek_post(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        for p in (NL, EN):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x")
        out = tmp_path / "retranslate.txt"
        assert main(["--retranslate-to", str(out), str(GR)]) == 0
        assert not NL.exists() and not EN.exists()
        assert out.read_text() == ""

    def test_lists_the_greek_when_a_translation_was_deleted(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        for p in (GR, NL):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x")
        out = tmp_path / "retranslate.txt"
        assert main(["--retranslate-to", str(out), str(EN)]) == 0
        assert GR.exists() and NL.exists()
        assert out.read_text() == f"{GR}\n"
