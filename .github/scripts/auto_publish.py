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

Once auto-merge is on, the job waits (up to WAIT_SECONDS) for the merge and then
deletes the post's `cms/...` branch. GitHub's "Automatically delete head
branches" skips merges made with the workflow token, and Decap can't save the
same post again while its old branch is still there. The nightly rebuild runs
`auto_publish.py sweep`, which deletes any `cms/` branch whose pull requests
are all merged or closed, for the cases this job missed (a timeout, a run that
never started).

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
import time
import urllib.parse
from collections.abc import Callable

import pr_status

LABEL = "decap-cms/pending_publish"
# How long the job waits for the merge after turning auto-merge on, and how
# often it looks. The checks usually take a few minutes.
WAIT_SECONDS = 30 * 60
POLL_SECONDS = 20

Runner = Callable[..., tuple[int, str]]


def gh(*args: str) -> tuple[int, str]:
    """Run the gh CLI. Returns (exit code, stdout and stderr together)."""
    done = subprocess.run(["gh", *args], capture_output=True, text=True)
    return done.returncode, (done.stdout + done.stderr).strip()


class Failed(Exception):
    pass


def read_pr(run: Runner, repo: str, pr: str) -> dict:
    code, out = run("pr", "view", pr, "-R", repo, "--json", "state,labels,autoMergeRequest,headRefName")
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


def has_ready_label(info: dict) -> bool:
    return LABEL in [label["name"] for label in info.get("labels", [])]


def delete_branch(run: Runner, repo: str, branch: str) -> bool:
    """Delete a post's `cms/...` branch after its merge. Returns False when there
    was nothing to delete (not a cms/ branch, or already gone: a merge by a
    person, such as Decap's Publish, lets GitHub delete it by itself)."""
    if not branch.startswith("cms/"):
        return False
    ref = urllib.parse.quote(f"heads/{branch}", safe="/")
    code, out = run("api", "-X", "DELETE", f"repos/{repo}/git/refs/{ref}")
    if code == 0:
        return True
    if mentions(out, "reference does not exist", "not found", "http 422", "http 404"):
        return False
    raise Failed(f"could not delete the branch {branch}: {out}")


def wait_for_merge(
    run: Runner,
    repo: str,
    pr: str,
    wait_s: float = WAIT_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> str:
    """With auto-merge on, wait until GitHub merges, then delete the branch.
    Returns "merged", "closed", "not ready" (moved out of Ready: the run for that
    label change turns auto-merge off) or "timeout"."""
    deadline = clock() + wait_s
    while True:
        info = read_pr(run, repo, pr)
        state = info.get("state")
        if state == "MERGED":
            delete_branch(run, repo, info.get("headRefName", ""))
            return "merged"
        if state != "OPEN":
            return "closed"
        if not has_ready_label(info):
            return "not ready"
        if clock() >= deadline:
            return "timeout"
        sleep(POLL_SECONDS)


def sweep(run: Runner, repo: str) -> list[str]:
    """Delete every `cms/` branch whose pull requests are all merged or closed.
    A branch with no pull request at all is kept: Decap may be creating it."""
    code, out = run("api", "--paginate", f"repos/{repo}/git/matching-refs/heads/cms/", "--jq", ".[].ref")
    if code != 0:
        raise Failed(f"could not list the cms/ branches: {out}")
    deleted = []
    for ref in out.splitlines():
        branch = ref.strip().removeprefix("refs/heads/")
        if not branch:
            continue
        code, prs = run("pr", "list", "-R", repo, "--head", branch, "--state", "all", "--json", "state")
        if code != 0:
            raise Failed(f"could not read the pull requests of {branch}: {prs}")
        states = [p.get("state") for p in json.loads(prs or "[]")]
        if states and "OPEN" not in states and delete_branch(run, repo, branch):
            deleted.append(branch)
    return deleted


def apply(run: Runner, repo: str, pr: str) -> str | None:
    """Make auto-merge match the labels. Returns "on", "off", "unavailable",
    or None when the pull request is no longer open (a merged one gets its
    branch deleted)."""
    info = read_pr(run, repo, pr)
    if info.get("state") == "MERGED":
        delete_branch(run, repo, info.get("headRefName", ""))
    if info.get("state") != "OPEN":
        return None
    if has_ready_label(info):
        if info.get("autoMergeRequest"):
            return "on"
        return enable(run, repo, pr)
    if not info.get("autoMergeRequest"):
        return "off"
    return disable(run, repo, pr)


def main(
    run: Runner = gh,
    argv: list[str] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    if argv and argv[0] == "sweep":
        try:
            deleted = sweep(run, os.environ["REPO"])
        except Failed as e:
            print(f"::error title=Branch cleanup::{e}")
            return 1
        print(f"Deleted {len(deleted)} leftover branch(es): {', '.join(deleted) or 'none'}.")
        return 0

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

    if state == "on":
        wait_s = float(os.environ.get("WAIT_SECONDS", WAIT_SECONDS))
        try:
            outcome = wait_for_merge(run, repo, pr, wait_s, sleep, clock)
        except Failed as e:
            print(f"::error title=Auto-publish::{e}")
            return 1
        print({
            "merged": f"PR #{pr} is merged and its branch is deleted.",
            "closed": f"PR #{pr} was closed without merging.",
            "not ready": f"PR #{pr} was moved out of Ready.",
            "timeout": f"PR #{pr} isn't merged yet; auto-merge stays on. The nightly cleanup deletes its branch after the merge.",
        }[outcome])
    return 0


if __name__ == "__main__":
    sys.exit(main(argv=sys.argv[1:]))
