#!/usr/bin/env python3
"""
Switch GitHub auto-merge on or off for a content pull request (plan item C1).

Decap CMS puts the label `decap-cms/pending_publish` on a pull request when the
editor sets the post to Ready. With that label, the pull request is set to merge
by itself (squash) as soon as the required checks pass. Without it, auto-merge
is switched off again.

The label is read live from GitHub, not taken from the event that started the
workflow: Decap changes two labels per status change, and the runs may overlap.

`gh pr merge --auto` merges at once when the pull request is already mergeable
(gh 2.102 checks GitHub's merge state first). If GitHub still answers "clean
status" because the state changed in between, we merge directly.

Fails soft: when the repository does not allow auto-merge yet, this prints a
warning and ends green. The status comment then tells the editor to press Publish.

Environment:
    GH_TOKEN, REPO, PR_NUMBER, RUN_URL, GITHUB_RUN_ID, ADMIN_MENTIONS
    (the last four are used by pr_status.py)
"""

import json
import os
import subprocess
import sys
from collections.abc import Callable

import pr_status

LABEL = "decap-cms/pending_publish"

Runner = Callable[..., tuple[int, str]]


def gh(*args: str) -> tuple[int, str]:
    """Run the gh CLI. Returns (exit code, stdout and stderr together)."""
    done = subprocess.run(["gh", *args], capture_output=True, text=True)
    return done.returncode, (done.stdout + done.stderr).strip()


class Failed(Exception):
    pass


def read_pr(run: Runner, repo: str, pr: str) -> dict:
    code, out = run("pr", "view", pr, "-R", repo, "--json", "state,labels,autoMergeRequest")
    if code != 0:
        raise Failed(f"could not read the pull request: {out}")
    return json.loads(out)


def mentions(out: str, *phrases: str) -> bool:
    low = out.lower().replace("-", " ")
    return any(p in low for p in phrases)


def enable(run: Runner, repo: str, pr: str) -> str:
    """Returns "on", or "unavailable" when the repository doesn't allow auto-merge."""
    code, out = run("pr", "merge", pr, "-R", repo, "--auto", "--squash")
    if code == 0:
        return "on"
    if mentions(out, "auto merge is not allowed"):
        return "unavailable"
    if mentions(out, "clean status"):
        code, out = run("pr", "merge", pr, "-R", repo, "--squash")
        if code == 0:
            return "on"
    raise Failed(f"could not turn on auto-merge: {out}")


def disable(run: Runner, repo: str, pr: str) -> str:
    code, out = run("pr", "merge", pr, "-R", repo, "--disable-auto")
    # Not enabled, or not allowed in this repository at all: either way it is off.
    if code == 0 or mentions(out, "not enabled", "not allowed"):
        return "off"
    raise Failed(f"could not turn off auto-merge: {out}")


def apply(run: Runner, repo: str, pr: str) -> str | None:
    """Make auto-merge match the labels. Returns "on", "off", "unavailable",
    or None when the pull request is no longer open."""
    info = read_pr(run, repo, pr)
    if info.get("state") != "OPEN":
        return None
    if LABEL in [label["name"] for label in info.get("labels", [])]:
        if info.get("autoMergeRequest"):
            return "on"
        return enable(run, repo, pr)
    if not info.get("autoMergeRequest"):
        return "off"
    return disable(run, repo, pr)


def main(run: Runner = gh) -> int:
    repo, pr = os.environ["REPO"], os.environ["PR_NUMBER"]
    try:
        state = apply(run, repo, pr)
    except Failed as e:
        print(f"::error title=Auto-publish::{e}")
        return 1
    if state is None:
        print(f"PR #{pr} is not open: nothing to do.")
        return 0
    print(f"Auto-publish is {state} for PR #{pr}.")
    if state == "unavailable":
        print(
            "::warning title=Auto-publish is not available::Auto-merge is not allowed in this "
            'repository. Turn on "Allow auto-merge" in Settings > General > Pull Requests. '
            "Until then, editors must press Publish themselves."
        )
    try:
        print(pr_status.update(
            pr_status.Api(repo, pr),
            "autopublish",
            {"state": state, "run": pr_status.run_stamp()},
            mentions=os.environ.get("ADMIN_MENTIONS", ""),
            run_url=os.environ.get("RUN_URL", ""),
        ))
    except (pr_status.NotVerified, subprocess.CalledProcessError) as e:
        # The comment is a courtesy: never fail because of it.
        print(f"::warning title=PR status comment::{e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
