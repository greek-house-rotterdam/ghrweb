"""The verify job's event check (#105): each Greek event text belongs to one real event."""

import json

import pytest
import requests

import check_event_ids
from check_event_ids import check, greek_files, load_events, main


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A working tree with an empty Greek event-translations folder."""
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "src/content/event-translations/gr"
    folder.mkdir(parents=True)
    return folder


def write_entry(folder, name, event_id):
    path = folder / name
    tt = "" if event_id is None else f"tt_event_id: {event_id}\n"
    path.write_text(f"---\n{tt}title: Τίτλος\nlang: gr\n---\nΚείμενο\n", encoding="utf-8")
    return f"src/content/event-translations/gr/{name}"


class Response:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = body

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


def site(*responses):
    """A fake requests.get that answers with the given responses in order."""
    calls = []
    queue = list(responses)

    def get(url, **kwargs):
        calls.append(url)
        r = queue.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    get.calls = calls
    return get


LIST = Response(body={"events": [
    {"id": "ev_1", "name": "Πάσχα", "start": "2027-04-25T19:00:00+02:00", "past": False},
    {"id": "ev_2", "name": "Board games", "start": "2026-11-20T19:00:00+01:00", "past": False},
]})


class TestWhichFiles:
    def test_only_greek_event_texts_that_exist(self, repo):
        gr = write_entry(repo, "ev_1.md", "ev_1")
        paths = [
            gr,
            "src/content/event-translations/nl/ev_1.md",
            "src/content/news/gr/x.md",
            "src/content/event-translations/gr/deleted.md",
            "",
        ]
        assert [p.as_posix() for p in greek_files(paths)] == [gr]


class TestCheck:
    def test_ok_names_the_event(self, repo):
        f = write_entry(repo, "ev_1.md", "ev_1")
        result = check(greek_files([f]), load_events(get=site(LIST)))
        assert result == {
            "state": "ok",
            "found": [{"file": f, "id": "ev_1", "name": "Πάσχα", "start": "2027-04-25T19:00:00+02:00"}],
            "problems": [],
        }

    def test_unknown_event_fails(self, repo):
        f = write_entry(repo, "ev_9.md", "ev_9")
        result = check(greek_files([f]), load_events(get=site(LIST)))
        assert result["state"] == "fail"
        assert result["problems"] == [{"kind": "unknown", "file": f, "id": "ev_9"}]

    def test_event_changed_after_the_entry_was_created(self, repo):
        f = write_entry(repo, "ev_1.md", "ev_2")
        result = check(greek_files([f]), load_events(get=site(LIST)))
        assert result["problems"] == [{"kind": "renamed", "file": f, "id": "ev_2"}]

    def test_second_entry_for_the_same_event(self, repo):
        first = write_entry(repo, "ev_1.md", "ev_1")
        # What Decap names a second entry for an event that already has one.
        second = write_entry(repo, "ev_1-1.md", "ev_1")
        result = check(greek_files([second]), load_events(get=site(LIST)))
        assert result["problems"] == [{"kind": "duplicate", "file": second, "id": "ev_1", "other": first}]

    def test_no_event_chosen(self, repo):
        f = write_entry(repo, "x.md", None)
        result = check(greek_files([f]), None)
        assert result["problems"] == [{"kind": "missing", "file": f}]

    def test_list_unavailable_warns_but_still_checks_names_and_duplicates(self, repo):
        ok = write_entry(repo, "ev_9.md", "ev_9")
        assert check(greek_files([ok]), None) == {"state": "warn", "found": [], "problems": []}
        bad = write_entry(repo, "ev_8.md", "ev_7")
        assert check(greek_files([bad]), None)["state"] == "fail"

    def test_entries_outside_the_pr_are_not_checked(self, repo):
        write_entry(repo, "ev_gone.md", "ev_gone")  # its event left Ticket Tailor
        f = write_entry(repo, "ev_1.md", "ev_1")
        assert check(greek_files([f]), load_events(get=site(LIST)))["state"] == "ok"


class TestLoadEvents:
    def test_reads_the_live_list(self):
        get = site(LIST)
        assert set(load_events(get=get)) == {"ev_1", "ev_2"}
        assert get.calls == [check_event_ids.EVENTS_URL]

    def test_retries_a_server_error_or_a_network_error(self):
        sleeps = []
        get = site(Response(503), requests.ConnectionError("down"), LIST)
        assert load_events(get=get, sleep=sleeps.append) is not None
        assert sleeps == [2, 5]

    def test_gives_up_after_three_tries(self):
        get = site(Response(500), Response(502), Response(503))
        assert load_events(get=get, sleep=lambda s: None) is None
        assert len(get.calls) == 3

    @pytest.mark.parametrize("answer", [
        Response(404),
        Response(body=ValueError("not json")),
        Response(body={"events": "x"}),
        Response(body=[]),
        # An empty list: that build had no events, so nothing is known.
        Response(body={"events": []}),
    ])
    def test_a_list_it_cannot_use_counts_as_unavailable(self, answer):
        assert load_events(get=site(answer), sleep=lambda s: None) is None


class TestMain:
    def test_no_greek_event_text_writes_no_report(self, repo, tmp_path):
        report = tmp_path / "r.json"
        get = site()
        assert main(["src/content/news/gr/x.md", "--report", str(report)], get=get) == 0
        assert not report.exists() and get.calls == []

    def test_problem_exits_1_and_writes_the_report(self, repo, tmp_path):
        f = write_entry(repo, "ev_9.md", "ev_9")
        report = tmp_path / "r.json"
        assert main([f, "--report", str(report)], get=site(LIST)) == 1
        assert json.loads(report.read_text(encoding="utf-8"))["problems"][0]["kind"] == "unknown"

    def test_ok_exits_0(self, repo, tmp_path):
        f = write_entry(repo, "ev_2.md", "ev_2")
        report = tmp_path / "r.json"
        assert main([f, "--report", str(report)], get=site(LIST)) == 0
        assert json.loads(report.read_text(encoding="utf-8"))["state"] == "ok"

    def test_unreachable_list_exits_0_with_a_warning(self, repo, tmp_path, capsys):
        f = write_entry(repo, "ev_2.md", "ev_2")
        report = tmp_path / "r.json"
        down = site(*[requests.ConnectionError("down")] * 3)
        assert main([f, "--report", str(report)], get=down, sleep=lambda s: None) == 0
        assert json.loads(report.read_text(encoding="utf-8"))["state"] == "warn"
        assert "::warning" in capsys.readouterr().out
