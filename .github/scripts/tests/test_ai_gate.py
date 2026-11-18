import json

from ai_gate import MAX_DESCRIPTION, critical_findings, decide, main


def files(tmp_path, reviewed, results=None):
    r = tmp_path / "reviewed.txt"
    r.write_text("".join(f"{p}\n" for p in reviewed), encoding="utf-8")
    out = tmp_path / "results.json"
    if results is not None:
        out.write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
    return str(r), str(out)


def entry(path, *severities, error=None):
    return {"file": path, "error": error,
            "findings": [{"severity": s, "field": "body", "message": f"{s} m"} for s in severities]}


class TestDecide:
    def test_a_critical_finding_holds_the_post(self, tmp_path):
        reviewed, results = files(tmp_path, ["src/content/news/gr/a.md"],
                                  [entry("src/content/news/gr/a.md", "minor", "critical")])
        state, description, found = decide(reviewed, results)
        assert state == "failure"
        assert description.startswith("Held: 1 critical AI remark.")
        assert [p for p, _ in found] == ["src/content/news/gr/a.md"]

    def test_counts_every_critical_finding(self, tmp_path):
        reviewed, results = files(tmp_path, ["a.md", "b.md"],
                                  [entry("a.md", "critical", "critical"), entry("b.md", "critical")])
        assert decide(reviewed, results)[1].startswith("Held: 3 critical AI remarks.")

    def test_major_and_minor_findings_never_hold(self, tmp_path):
        reviewed, results = files(tmp_path, ["a.md"], [entry("a.md", "major", "minor")])
        assert decide(reviewed, results)[0] == "success"

    def test_no_findings_passes(self, tmp_path):
        reviewed, results = files(tmp_path, ["a.md"], [])
        assert decide(reviewed, results)[:2] == ("success", "No critical AI remark")

    def test_nothing_to_review_passes(self, tmp_path):
        # Code pull requests: the check must still report, or they'd wait forever.
        reviewed, results = files(tmp_path, [])
        assert decide(reviewed, results)[:2] == ("success", "No content to review")
        assert decide(None, None)[0] == "success"
        assert decide(str(tmp_path / "missing.txt"), None)[0] == "success"

    def test_a_review_that_could_not_run_does_not_hold(self, tmp_path):
        # An outage must not stop every post: no results file at all ...
        reviewed, results = files(tmp_path, ["a.md"])
        assert decide(reviewed, results)[0] == "success"
        # ... a broken one ...
        (tmp_path / "results.json").write_text("{not json", encoding="utf-8")
        assert decide(reviewed, results)[0] == "success"
        # ... or an error for a file.
        reviewed, results = files(tmp_path, ["a.md"], [entry("a.md", error="Gemini API 503")])
        state, description, _ = decide(reviewed, results)
        assert state == "success" and "couldn't be reviewed" in description

    def test_a_critical_finding_holds_even_when_another_file_errored(self, tmp_path):
        reviewed, results = files(tmp_path, ["a.md", "b.md"],
                                  [entry("a.md", "critical"), entry("b.md", error="503")])
        assert decide(reviewed, results)[0] == "failure"


class TestCriticalFindings:
    def test_ignores_malformed_output(self):
        assert critical_findings({"findings": []}) == []
        assert critical_findings(["x", {"findings": None}, {"findings": ["x", {"severity": "critical"}]}]) == [
            ("", {"severity": "critical"})]


class TestMain:
    def test_prints_state_and_description_on_one_line(self, tmp_path, capsys):
        reviewed, results = files(tmp_path, ["a.md"], [entry("a.md", "critical")])
        assert main(["--reviewed", reviewed, "--results", results]) == 0
        out, err = capsys.readouterr()
        state, description = out.rstrip("\n").split("\t")
        assert state == "failure" and len(description) <= MAX_DESCRIPTION
        assert "critical in a.md" in err

    def test_always_exits_zero(self, tmp_path, capsys):
        # The workflow posts the state; the step itself must not fail on a hold.
        assert main([]) == 0
        assert capsys.readouterr().out == "success\tNo content to review\n"
