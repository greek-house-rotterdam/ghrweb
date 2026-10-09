#!/usr/bin/env python3
"""
Copy Cloudflare's per-commit preview URL into a `deploy/preview` commit status.

Decap CMS shows its "View Preview" button for an unpublished entry when the
PR's head commit has a commit status whose context contains "deploy"
(check-runs are ignored). Cloudflare Workers Builds only posts a check-run and
a PR comment, so this script reads the comment and posts the status.

Why the comment and not the check-run: GitHub does not start `check_run` /
`check_suite` workflows when the commit was pushed by GitHub Actions, and our
translation bot pushes to most CMS branches that way. Cloudflare's PR comment
is written by the Cloudflare app, so `issue_comment` always fires.

Environment:
    GH_TOKEN      token for the gh CLI (needs statuses: write)
    REPO          owner/name
    PR_NUMBER     pull request number
    COMMENT_BODY  body of the Cloudflare comment (from the event payload)
"""

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable

CONTEXT = "deploy/preview"

# Only ever link to our own Workers preview hostnames.
PREVIEW_URL_RE = re.compile(
    r"^https://[a-z0-9-]+-ghrweb\.enosi-ellinon-ollandias\.workers\.dev/?$"
)
# The comment is a table row: | status | ghrweb | <short sha> | <a href='...'>Commit Preview URL</a> ...
SHA_RE = re.compile(r"\|\s*ghrweb\s*\|\s*([0-9a-f]{7,40})\s*\|")
URL_RE = re.compile(r"""href=['"]([^'"]+)['"]\s*>\s*Commit Preview URL""")


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


def sync(repo: str, pr_number: str, body: str, gh: Callable[..., str]) -> str:
    """Post the status if needed. Returns a one-line outcome for the log."""
    parsed = parse_comment(body)
    if not parsed:
        return "skip: no finished preview in this comment"
    short_sha, url = parsed

    pr = json.loads(gh("api", f"repos/{repo}/pulls/{pr_number}"))
    if pr["state"] != "open":
        return "skip: PR is not open"
    if pr["head"]["repo"] is None or pr["head"]["repo"]["full_name"] != repo:
        return "skip: fork PR"
    head = pr["head"]["sha"]
    if not head.startswith(short_sha):
        return f"skip: comment is for {short_sha}, PR head is {head[:8]}"

    existing = json.loads(gh("api", f"repos/{repo}/commits/{head}/statuses"))
    for s in existing:
        if s["context"] == CONTEXT:
            # Statuses are newest first; only the newest one counts.
            if s["state"] == "success" and s["target_url"] == url:
                return f"skip: {head[:8]} already has {CONTEXT} -> {url}"
            break

    gh(
        "api", "-X", "POST", f"repos/{repo}/statuses/{head}",
        "-f", "state=success",
        "-f", f"target_url={url}",
        "-f", "description=Cloudflare preview",
        "-f", f"context={CONTEXT}",
    )
    return f"posted {CONTEXT} on {head[:8]} -> {url}"


def run_gh(*args: str) -> str:
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout


def main() -> int:
    print(
        sync(
            os.environ["REPO"],
            os.environ["PR_NUMBER"],
            os.environ["COMMENT_BODY"],
            run_gh,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
