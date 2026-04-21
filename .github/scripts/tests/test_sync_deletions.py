from pathlib import Path

from sync_deletions import get_counterparts


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
