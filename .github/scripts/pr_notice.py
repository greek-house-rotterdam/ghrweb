#!/usr/bin/env python3
"""
Keep one plain-language status notice per topic on a pull request.

A failing workflow calls `pr_notice.py set <topic>`. The notice tells the
editor, in Greek and English, what happened and @-mentions the site admins.
Each notice carries a hidden `<!-- pr-notice:<topic> -->` marker, so re-runs
update the same comment instead of adding new ones, and a later successful
run calls `pr_notice.py clear <topic>` to remove it.

The "kept" topic is information, not a failure: it lists translations that were
corrected by hand and so were not re-translated. It mentions nobody, is never
cleared by a later run (that run wouldn't flag the file again), and each `set`
adds its files to the list already in the comment instead of replacing it.

Mentions name users, not a team: a team @-mention posted with the workflow's
GITHUB_TOKEN does not notify anyone.

Usage:
    pr_notice.py set <topic> [details-file]
    pr_notice.py clear <topic>

A details file (markdown) is added below the text, e.g. the list of images
that can't be published.

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
from pathlib import Path

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
    "kept": (
        "ℹ️ Κρατήθηκε διορθωμένη μετάφραση / Kept a corrected translation",
        "Η ελληνική εκδοχή άλλαξε, αλλά η ολλανδική ή η αγγλική μετάφραση "
        "είχε διορθωθεί με το χέρι, οπότε κρατήθηκε όπως ήταν και δεν "
        "ξαναμεταφράστηκε. Μπορεί να μην ταιριάζει πια με το ελληνικό "
        "κείμενο: έλεγξέ την στο /admin (δες τη λίστα παρακάτω).",
        "The Greek changed, but the Dutch or English translation had been "
        "corrected by hand, so it was kept as it was and not translated "
        "again. It may no longer match the Greek: check it in /admin (see the "
        "list below).",
    ),
    "images": (
        "⚠️ Πρόβλημα με εικόνα / Image problem",
        "Κάποια εικόνα δεν μπορεί να χρησιμοποιηθεί (δες παρακάτω), οπότε η "
        "ανάρτηση δεν μπορεί να δημοσιευτεί ακόμα. Ανέβασε στη θέση της μια "
        "εικόνα JPEG, PNG ή WebP, έως 5 MB, και αποθήκευσε ξανά. Ο "
        "διαχειριστής ενημερώθηκε και θα βοηθήσει αν το μήνυμα δεν φύγει.",
        "An image can't be used (see below), so this post can't be published "
        "yet. Upload a JPEG, PNG or WebP image of up to 5 MB in its place and "
        "save again. The site admin has been notified and will help if this "
        "message doesn't go away.",
    ),
}

# Informational topics: nobody is @-mentioned.
NO_MENTION_TOPICS = {"kept"}

# Topics whose details accumulate: a new `set` merges its list into the one
# already in the comment (keyed by the `path` in backticks) instead of replacing it.
MERGE_TOPICS = {"kept"}

USAGE = (
    "usage: pr_notice.py set <topic> [details-file] | clear <topic>"
    f"   (topics: {', '.join(NOTICES)})"
)

Runner = Callable[..., str]


def gh(*args: str) -> str:
    """Run the gh CLI and return its stdout."""
    return subprocess.run(
        ["gh", *args], capture_output=True, text=True, check=True
    ).stdout


def marker(topic: str) -> str:
    return f"<!-- pr-notice:{topic} -->"


def build_body(topic: str, mentions: str, run_url: str, details: str = "") -> str:
    """Render the notice comment for a topic."""
    heading, greek, english = NOTICES[topic]
    lines = [marker(topic), f"### {heading}", "", greek, "", f"*{english}*"]
    if details.strip():
        lines += ["", details.strip()]

    footer = []
    if mentions.strip() and topic not in NO_MENTION_TOPICS:
        footer.append(f"cc {mentions.strip()}")
    if run_url:
        footer.append(f"[workflow run]({run_url})")
    if footer:
        lines += ["", " · ".join(footer)]

    return "\n".join(lines)


def find_notices(
    repo: str, pr: str, topic: str, run: Runner = gh
) -> list[tuple[int, str]]:
    """(id, body) of existing comments on the PR that carry this topic's marker."""
    out = run(
        "api", f"repos/{repo}/issues/{pr}/comments", "--paginate",
        "--jq", ".[] | {id, body}",
    )
    tag = marker(topic)
    found = []
    for line in out.splitlines():
        if not line.strip():
            continue
        comment = json.loads(line)
        if tag in (comment.get("body") or ""):
            found.append((comment["id"], comment["body"]))
    return found


def find_notice_ids(repo: str, pr: str, topic: str, run: Runner = gh) -> list[int]:
    """IDs of existing comments on the PR that carry this topic's marker."""
    return [cid for cid, _ in find_notices(repo, pr, topic, run)]


def _entry_key(line: str) -> str:
    """The `path` in backticks that identifies a list entry (or the whole line)."""
    start = line.find("`")
    end = line.find("`", start + 1)
    return line[start + 1 : end] if start != -1 and end != -1 else line


def merge_details(old_bodies: list[str], new_details: str) -> str:
    """Combine the list entries (lines starting "- ") of earlier notices with new ones.

    Earlier entries keep their place, a new entry for the same path replaces the
    old one, and other new entries are appended.
    """
    merged: dict[str, str] = {}
    for text in [*old_bodies, new_details]:
        for line in text.splitlines():
            if line.startswith("- "):
                merged[_entry_key(line)] = line
    return "\n".join(merged.values()) + "\n" if merged else ""


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
    valid = (
        len(argv) in (2, 3)
        and argv[0] in ("set", "clear")
        and argv[1] in NOTICES
        and (len(argv) == 2 or argv[0] == "set")
    )
    if not valid:
        print(USAGE, file=sys.stderr)
        return 2

    action, topic = argv[:2]
    repo = os.environ["REPO"]
    pr = os.environ["PR_NUMBER"]

    if action == "set":
        # A missing details file still posts the notice, just without the list.
        details_path = Path(argv[2]) if len(argv) == 3 else None
        details = (
            details_path.read_text(encoding="utf-8")
            if details_path and details_path.is_file()
            else ""
        )
        if topic in MERGE_TOPICS:
            old = [b for _, b in find_notices(repo, pr, topic, run)]
            details = merge_details(old, details)
        body = build_body(
            topic,
            os.environ.get("ADMIN_MENTIONS", ""),
            os.environ.get("RUN_URL", ""),
            details,
        )
        result = set_notice(repo, pr, topic, body, run)
        print(f"Notice '{topic}' {result} on PR #{pr}")
    else:
        removed = clear_notice(repo, pr, topic, run)
        print(f"Notice '{topic}': removed {removed} comment(s) on PR #{pr}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
