#!/usr/bin/env python3
"""
Keep one plain-language status notice per topic on a pull request.

A failing workflow calls `pr_notice.py set <topic>`. The notice tells the
editor, in Greek and English, what happened and @-mentions the site admins.
Each notice carries a hidden `<!-- pr-notice:<topic> -->` marker, so re-runs
update the same comment instead of adding new ones, and a later successful
run calls `pr_notice.py clear <topic>` to remove it.

Mentions name users, not a team: a team @-mention posted with the workflow's
GITHUB_TOKEN does not notify anyone.

Usage:
    pr_notice.py set <topic>
    pr_notice.py clear <topic>

Environment:
    GH_TOKEN        token for the gh CLI (the workflow's github.token)
    REPO            owner/name
    PR_NUMBER       pull request number
    RUN_URL         link to the workflow run, shown in the notice
    ADMIN_MENTIONS  who to @-mention, e.g. "@PanoEvJ" (space-separated)
"""

import json
import os
import subprocess
import sys
from collections.abc import Callable

# topic -> (heading, Greek text for the editor, English text)
NOTICES = {
    "translate": (
        "⚠️ Η μετάφραση δεν ολοκληρώθηκε / Translation failed",
        "Η αυτόματη μετάφραση αυτής της ανάρτησης δεν ολοκληρώθηκε, οπότε "
        "δεν μπορεί να δημοσιευτεί ακόμα. Δεν χρειάζεται να κάνεις κάτι: "
        "ο διαχειριστής ενημερώθηκε και θα το φροντίσει.",
        "The automatic translation of this post did not finish, so it can't "
        "be published yet. Nothing for you to do: the site admin has been "
        "notified.",
    ),
    "review": (
        "⚠️ Ο αυτόματος έλεγχος δεν έγινε / Content review didn't run",
        "Ο αυτόματος έλεγχος περιεχομένου (AI) δεν μπόρεσε να ελέγξει αυτή "
        "την ανάρτηση. Αυτό δεν εμποδίζει τη δημοσίευση. Ο διαχειριστής "
        "ενημερώθηκε.",
        "The AI content review could not check this post. This does not "
        "block publishing. The site admin has been notified.",
    ),
}

USAGE = f"usage: pr_notice.py set|clear <topic>   (topics: {', '.join(NOTICES)})"

Runner = Callable[..., str]


def gh(*args: str) -> str:
    """Run the gh CLI and return its stdout."""
    return subprocess.run(
        ["gh", *args], capture_output=True, text=True, check=True
    ).stdout


def marker(topic: str) -> str:
    return f"<!-- pr-notice:{topic} -->"


def build_body(topic: str, mentions: str, run_url: str) -> str:
    """Render the notice comment for a topic."""
    heading, greek, english = NOTICES[topic]
    lines = [marker(topic), f"### {heading}", "", greek, "", f"*{english}*"]

    footer = []
    if mentions.strip():
        footer.append(f"cc {mentions.strip()}")
    if run_url:
        footer.append(f"[workflow run]({run_url})")
    if footer:
        lines += ["", " · ".join(footer)]

    return "\n".join(lines)


def find_notice_ids(repo: str, pr: str, topic: str, run: Runner = gh) -> list[int]:
    """IDs of existing comments on the PR that carry this topic's marker."""
    out = run(
        "api", f"repos/{repo}/issues/{pr}/comments", "--paginate",
        "--jq", ".[] | {id, body}",
    )
    tag = marker(topic)
    ids = []
    for line in out.splitlines():
        if not line.strip():
            continue
        comment = json.loads(line)
        if tag in (comment.get("body") or ""):
            ids.append(comment["id"])
    return ids


def delete_comment(repo: str, comment_id: int, run: Runner = gh) -> None:
    run("api", "-X", "DELETE", f"repos/{repo}/issues/comments/{comment_id}", "--silent")


def set_notice(repo: str, pr: str, topic: str, body: str, run: Runner = gh) -> str:
    """Create the notice, or update it in place if it already exists.

    Returns "created" or "updated".
    """
    ids = find_notice_ids(repo, pr, topic, run)
    if not ids:
        run("api", f"repos/{repo}/issues/{pr}/comments", "-f", f"body={body}", "--silent")
        return "created"

    run("api", "-X", "PATCH", f"repos/{repo}/issues/comments/{ids[0]}",
        "-f", f"body={body}", "--silent")
    for duplicate in ids[1:]:
        delete_comment(repo, duplicate, run)
    return "updated"


def clear_notice(repo: str, pr: str, topic: str, run: Runner = gh) -> int:
    """Remove every notice for this topic. Returns how many were removed."""
    ids = find_notice_ids(repo, pr, topic, run)
    for comment_id in ids:
        delete_comment(repo, comment_id, run)
    return len(ids)


def main(argv: list[str] | None = None, run: Runner = gh) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] not in ("set", "clear") or argv[1] not in NOTICES:
        print(USAGE, file=sys.stderr)
        return 2

    action, topic = argv
    repo = os.environ["REPO"]
    pr = os.environ["PR_NUMBER"]

    if action == "set":
        body = build_body(
            topic, os.environ.get("ADMIN_MENTIONS", ""), os.environ.get("RUN_URL", "")
        )
        result = set_notice(repo, pr, topic, body, run)
        print(f"Notice '{topic}' {result} on PR #{pr}")
    else:
        removed = clear_notice(repo, pr, topic, run)
        print(f"Notice '{topic}': removed {removed} comment(s) on PR #{pr}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
