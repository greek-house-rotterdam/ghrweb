#!/usr/bin/env python3
"""
Copy Cloudflare's per-commit preview URL into a `deploy/preview` commit status.

Decap CMS shows its "View Preview" button for an unpublished entry when the
PR's head commit has a commit status whose context contains "deploy"
(check-runs are ignored). Cloudflare Workers Builds only posts a check-run and
a PR comment, so this script reads the comment and posts the status. It also
puts the link into the PR's status comment (pr_status.py), where editors read it.

Two ways in, both ending in the same status (#127):

- `preview_status.py check-run` (the `preview` job in translate.yml, after
  each save): waits for Cloudflare's "Workers Builds: ghrweb" check run on the
  PR's final head and reads "Preview URL:" from its summary. This is the main
  path: the check run always has the URL. A workflow can't simply listen for
  `check_run` events, because GitHub doesn't start those for commits pushed by
  GitHub Actions, and the translation bot pushes most CMS branches that way.
- `preview_status.py` (preview-status.yml, on Cloudflare's PR comment): the
  fallback. Cloudflare's comment is unreliable: on #125 it came 17 minutes
  after the build, and on #121 it never came.

Environment:
    GH_TOKEN      token for the gh CLI (needs statuses: write, pull-requests: write;
                  check-run mode also checks: read)
    RUN_URL       link to the workflow run, shown in the status comment
    REPO          owner/name
    PR_NUMBER     pull request number
    COMMENT_BODY  body of the Cloudflare comment (comment mode)
    HEAD_SHA      the PR's head after the translation bot (check-run mode)
    WAIT_SECONDS  how long check-run mode waits for the build (default 900)
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from collections.abc import Callable

CONTEXT = "deploy/preview"

# Only ever link to our own Workers preview hostnames.
PREVIEW_URL_RE = re.compile(
    r"^https://[a-z0-9-]+-ghrweb\.enosi-ellinon-ollandias\.workers\.dev/?$"
)
# The comment is a table row: | status | ghrweb | <short sha> | <a href='...'>Commit Preview URL</a> ...
SHA_RE = re.compile(r"\|\s*ghrweb\s*\|\s*([0-9a-f]{7,40})\s*\|")
URL_RE = re.compile(r"""href=['"]([^'"]+)['"]\s*>\s*Commit Preview URL""")

# Cloudflare's check run on each commit. Its summary has a line
# "Preview URL: https://<version>-ghrweb.enosi-ellinon-ollandias.workers.dev".
CHECK_NAME = "Workers Builds: ghrweb"
CHECK_APP = "cloudflare-workers-and-pages"
SUMMARY_URL_RE = re.compile(r"^Preview URL:\s*(\S+)\s*$", re.MULTILINE)
WAIT_SECONDS = 15 * 60
POLL_SECONDS = 20


def parse_comment(body: str) -> tuple[str, str] | None:
    """Return (commit sha prefix, preview URL) from a Cloudflare comment, or
    None when the build is not finished or the URL is not one of ours."""
    if "Deployment successful" not in body:
        return None
    sha = SHA_RE.search(body)
    url = URL_RE.search(body)
    if not sha or not url:
        return None
    if not PREVIEW_URL_RE.fullmatch(url.group(1)):
        return None
    return sha.group(1), url.group(1)


def parse_check_run(run: dict) -> str | None:
    """Return the preview URL from a finished, successful Cloudflare check run,
    or None (another app, not finished, failed, or not one of our URLs)."""
    if (run.get("app") or {}).get("slug") != CHECK_APP:
        return None
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        return None
    match = SUMMARY_URL_RE.search((run.get("output") or {}).get("summary") or "")
    if not match or not PREVIEW_URL_RE.fullmatch(match.group(1)):
        return None
    return match.group(1)


def wait_for_check_run(
    repo: str,
    sha: str,
    gh: Callable[..., str],
    wait_s: float = WAIT_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> tuple[str, str | None]:
    """Wait for Cloudflare's check run on `sha`. Returns ("ok", url),
    ("failed", None) when the build finished without a usable URL, or
    ("timeout", None)."""
    name = urllib.parse.quote(CHECK_NAME)
    deadline = clock() + wait_s
    while True:
        data = json.loads(gh("api", f"repos/{repo}/commits/{sha}/check-runs?check_name={name}"))
        runs = [r for r in data.get("check_runs", []) if (r.get("app") or {}).get("slug") == CHECK_APP]
        # A rebuild of the same commit adds a run; the newest one counts.
        runs.sort(key=lambda r: r.get("started_at") or "", reverse=True)
        if runs and runs[0].get("status") == "completed":
            url = parse_check_run(runs[0])
            return ("ok", url) if url else ("failed", None)
        if clock() >= deadline:
            return ("timeout", None)
        sleep(POLL_SECONDS)


def sync(
    repo: str,
    pr_number: str,
    body: str,
    gh: Callable[..., str],
    show_link: Callable[[str, str], str] | None = None,
) -> str:
    """Comment mode: post the status from Cloudflare's PR comment."""
    parsed = parse_comment(body)
    if not parsed:
        return "skip: no finished preview in this comment"
    short_sha, url = parsed
    return post(repo, pr_number, short_sha, url, gh, show_link)


def sync_from_check_run(
    repo: str,
    pr_number: str,
    sha: str,
    gh: Callable[..., str],
    show_link: Callable[[str, str], str] | None = None,
    wait_s: float = WAIT_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> str:
    """Check-run mode: wait for Cloudflare's build of `sha`, then post."""
    result, url = wait_for_check_run(repo, sha, gh, wait_s, sleep, clock)
    if result == "timeout":
        return f"skip: no finished Cloudflare build for {sha[:8]} after {int(wait_s)} s"
    if result == "failed" or not url:
        return f"skip: Cloudflare's build of {sha[:8]} has no usable preview URL"
    return post(repo, pr_number, sha, url, gh, show_link)


def post(
    repo: str,
    pr_number: str,
    short_sha: str,
    url: str,
    gh: Callable[..., str],
    show_link: Callable[[str, str], str] | None = None,
) -> str:
    """Post the status on the PR head if `short_sha` is still the head, then
    show the link in the PR's status comment through `show_link(head sha, url)`.
    Returns a one-line outcome for the log."""
    pr = json.loads(gh("api", f"repos/{repo}/pulls/{pr_number}"))
    if pr["state"] != "open":
        return "skip: PR is not open"
    if pr["head"]["repo"] is None or pr["head"]["repo"]["full_name"] != repo:
        return "skip: fork PR"
    head = pr["head"]["sha"]
    if not head.startswith(short_sha):
        return f"skip: preview is for {short_sha[:8]}, PR head is {head[:8]}"

    outcome = None
    existing = json.loads(gh("api", f"repos/{repo}/commits/{head}/statuses"))
    for s in existing:
        if s["context"] == CONTEXT:
            # Statuses are newest first; only the newest one counts.
            if s["state"] == "success" and s["target_url"] == url:
                outcome = f"skip: {head[:8]} already has {CONTEXT} -> {url}"
            break

    if outcome is None:
        gh(
            "api", "-X", "POST", f"repos/{repo}/statuses/{head}",
            "-f", "state=success",
            "-f", f"target_url={url}",
            "-f", "description=Cloudflare preview",
            "-f", f"context={CONTEXT}",
        )
        outcome = f"posted {CONTEXT} on {head[:8]} -> {url}"

    if show_link:
        # Also when the status already exists: the comment may lack the link.
        try:
            outcome += f"; {show_link(head, url)}"
        except Exception as e:  # the status above is what matters; this is a courtesy
            outcome += f"; status comment not updated ({e})"
    return outcome


def run_gh(*args: str) -> str:
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout


def main(argv: list[str] | None = None) -> int:
    import pr_status

    argv = sys.argv[1:] if argv is None else argv
    repo, pr = os.environ["REPO"], os.environ["PR_NUMBER"]

    def show_link(head: str, url: str) -> str:
        data = {"state": "ok", "sha": head, "url": url, "run": pr_status.run_stamp()}
        # Pass the admins too: every write re-renders the whole comment, and
        # without them it would drop the "cc" line another job put there.
        return pr_status.update(
            pr_status.Api(repo, pr, run_gh), "preview", data,
            mentions=os.environ.get("ADMIN_MENTIONS", ""),
            run_url=os.environ.get("RUN_URL", ""),
        )

    if argv and argv[0] == "check-run":
        wait_s = float(os.environ.get("WAIT_SECONDS", WAIT_SECONDS))
        print(sync_from_check_run(repo, pr, os.environ["HEAD_SHA"], run_gh, show_link, wait_s))
    else:
        print(sync(repo, pr, os.environ["COMMENT_BODY"], run_gh, show_link))
    return 0


if __name__ == "__main__":
    sys.exit(main())
