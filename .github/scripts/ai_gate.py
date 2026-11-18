#!/usr/bin/env python3
"""
Decide the `ai-gate` check: hold a post while the AI review finds a critical problem.

Reads the JSON that content_review.py writes (REVIEW_OUTPUT) and prints one
line, `<state><TAB><description>`. The review workflow posts it as the commit
status `ai-gate`, which the `main-protected` ruleset requires, so a failure
keeps the post from going live, even when it is set to Ready.

- failure: a file this run reviewed has a critical finding.
- success: no critical finding, nothing to review, or the review couldn't run.
  An outage must not stop every post; the status comment tells the admins.

Major and minor findings never hold a post. Each run reviews the files its
push changed plus every human-written file in the pull request (see
content-review.yml), so the Greek text is checked again on every save: a
corrected post passes on its next save.

The workflow runs main's copy of this script (and of the reviewer), not the
branch's, so a draft made before a rule changed is held by the current rule.

Usage:
    ai_gate.py --reviewed FILE --results FILE
"""

import argparse
import json
import sys
from pathlib import Path

# GitHub cuts a commit status description at 140 characters.
MAX_DESCRIPTION = 140


def critical_findings(results: object) -> list[tuple[str, dict]]:
    """(file, finding) for every critical finding in content_review.py's output."""
    found: list[tuple[str, dict]] = []
    if not isinstance(results, list):
        return found
    for entry in results:
        if not isinstance(entry, dict):
            continue
        for finding in entry.get("findings") or []:
            if isinstance(finding, dict) and finding.get("severity") == "critical":
                found.append((str(entry.get("file", "")), finding))
    return found


def has_lines(path: str | None) -> bool:
    return bool(path) and Path(path).is_file() and any(
        line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()
    )


def decide(reviewed: str | None, results: str | None) -> tuple[str, str, list[tuple[str, dict]]]:
    """(state, description, critical findings) for the ai-gate status."""
    if not has_lines(reviewed):
        return "success", "No content to review", []
    path = Path(results) if results else None
    if not path or not path.is_file():
        return "success", "The AI review couldn't run, so the post isn't held", []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError):
        return "success", "The AI review couldn't run, so the post isn't held", []
    found = critical_findings(data)
    if found:
        n = len(found)
        noun = "remark" if n == 1 else "remarks"
        return "failure", f"Held: {n} critical AI {noun}. Correct the post and save.", found
    if isinstance(data, list) and any(isinstance(e, dict) and e.get("error") for e in data):
        return "success", "Some files couldn't be reviewed, so the post isn't held", []
    return "success", "No critical AI remark", []


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--reviewed", help="the files the review was asked to check, one per line")
    p.add_argument("--results", help="REVIEW_OUTPUT json from content_review.py")
    args = p.parse_args(sys.argv[1:] if argv is None else argv)

    state, description, found = decide(args.reviewed, args.results)
    for path, finding in found:
        # The log only: the remarks themselves are in the status comment.
        print(f"critical in {path}: {str(finding.get('message', ''))[:300]}", file=sys.stderr)
    print(f"{state}\t{description[:MAX_DESCRIPTION]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
