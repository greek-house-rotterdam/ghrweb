#!/usr/bin/env python3
"""
Keep ONE status comment per content pull request, in Greek with English in italics.

Each workflow reports its own part and this script rewrites only that part:

    translation  translate.yml (translate and verify jobs)
    kept         translate.yml: hand-corrected translations that were kept (A9)
    images       translate.yml (verify job)
    preview      preview-status.yml: the Cloudflare preview link
    review       content-review.yml: the AI review, notes per file

The comment carries the marker `<!-- pr-status -->`. Every section sits between
`<!-- pr-status:begin <name> <data> -->` and `<!-- pr-status:end <name> -->`; the
data in the begin marker (base64 JSON) is what later runs read back, the visible
text is rendered from it. Each section shows the short commit it refers to, so
stale information is visible. The "next step" line is derived from the sections.

Concurrency. The jobs run at the same time, and GitHub can't update a comment
conditionally. So every update is: read, change own section, write, wait a
moment, read again and check that the section is there, otherwise retry with a
random back-off. A concurrent writer that overwrote ours is caught by the re-read.

Notifications. GitHub's docs don't say whether adding an @mention by editing a
comment notifies, so a mention is never added by an edit. When a failure appears
that admins were not yet told about, the comment is re-created (new one first,
then the old one deleted) with a `cc @admins` line: a new comment notifies the
mentioned admins and emails the PR author. While the failure persists, updates
edit the comment in place and don't notify again.

Old `pr-notice:*` and `content-review:*` comments by the bot are deleted on the
first update; a "kept" list in them is carried over.

PRs that change no content and no images get no comment.

Environment:
    GH_TOKEN        token for the gh CLI (the workflow's github.token)
    REPO            owner/name
    PR_NUMBER       pull request number
    RUN_URL         link to the workflow run, shown in the footer
    GITHUB_RUN_ID   orders writes of the same section (newer run wins)
    ADMIN_MENTIONS  who to @-mention on failures, e.g. "@PanoEvJ" (space-separated)
"""

import argparse
import base64
import json
import os
import random
import re
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

Runner = Callable[..., str]

BOT_LOGIN = "github-actions[bot]"
MARK = "<!-- pr-status -->"
LEGACY_MARKERS = ("<!-- pr-notice:", "<!-- content-review:")
BEGIN_RE = re.compile(r"<!-- pr-status:begin (\w+) ([A-Za-z0-9_=-]*) -->")
ALERTS_RE = re.compile(r"<!-- pr-status:alerts ([a-z,]*) -->")
URL_RE = re.compile(r"^https://[A-Za-z0-9.-]+/?$")

SECTION_NAMES = ("translation", "kept", "images", "preview", "review")
CONTENT_PREFIXES = ("src/content/", "public/images/")
MAX_ITEMS = 20
MAX_TEXT = 600


# ---------------------------------------------------------------------------
# gh access
# ---------------------------------------------------------------------------


def gh(*args: str) -> str:
    """Run the gh CLI and return its stdout."""
    return subprocess.run(
        ["gh", *args], capture_output=True, text=True, check=True
    ).stdout


class Api:
    """The few GitHub calls this script needs."""

    def __init__(self, repo: str, pr: str, run: Runner = gh):
        self.repo, self.pr, self.run = repo, pr, run
        self._head: str | None = None
        self._files: list[str] | None = None

    def comments(self) -> list[dict]:
        out = self.run(
            "api", f"repos/{self.repo}/issues/{self.pr}/comments", "--paginate",
            "--jq", ".[] | {id, body, login: .user.login}",
        )
        return [json.loads(line) for line in out.splitlines() if line.strip()]

    def create(self, body: str) -> None:
        self.run("api", f"repos/{self.repo}/issues/{self.pr}/comments",
                 "-f", f"body={body}", "--silent")

    def edit(self, comment_id: int, body: str) -> None:
        self.run("api", "-X", "PATCH", f"repos/{self.repo}/issues/comments/{comment_id}",
                 "-f", f"body={body}", "--silent")

    def delete(self, comment_id: int) -> None:
        self.run("api", "-X", "DELETE", f"repos/{self.repo}/issues/comments/{comment_id}",
                 "--silent")

    def head_sha(self) -> str:
        if self._head is None:
            self._head = self.run(
                "api", f"repos/{self.repo}/pulls/{self.pr}", "--jq", ".head.sha"
            ).strip()
        return self._head

    def files(self) -> list[str]:
        if self._files is None:
            out = self.run(
                "api", f"repos/{self.repo}/pulls/{self.pr}/files", "--paginate",
                "--jq", ".[].filename",
            )
            self._files = [line for line in out.splitlines() if line]
        return self._files


# ---------------------------------------------------------------------------
# State: parsing and merging
# ---------------------------------------------------------------------------


@dataclass
class State:
    sections: dict[str, dict] = field(default_factory=dict)
    alerts: set[str] = field(default_factory=set)  # failures admins were told about


def encode(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def decode(text: str) -> dict | None:
    try:
        data = json.loads(base64.urlsafe_b64decode(text.encode("ascii")).decode("utf-8"))
    except (ValueError, UnicodeError):
        return None
    return data if isinstance(data, dict) else None


def parse(body: str) -> State:
    """Read the state back from a status comment."""
    state = State()
    for name, text in BEGIN_RE.findall(body):
        data = decode(text)
        if data is not None and name in SECTION_NAMES:
            state.sections[name] = data
    m = ALERTS_RE.search(body)
    if m:
        state.alerts = {a for a in m.group(1).split(",") if a}
    return state


def merge_states(states: list[State]) -> State:
    """Combine duplicate comments (oldest first); newer sections win."""
    merged = State()
    for s in states:
        merged.sections.update(s.sections)
        merged.alerts = s.alerts
    return merged


def apply_section(state: State, name: str, data: dict, pr_files: list[str] | None = None) -> None:
    """Replace this section's data. `kept` and `review` merge per entry instead."""
    if name == "kept":
        items = dict(state.sections.get("kept", {}).get("items", {}))
        items.update(data["items"])
        state.sections["kept"] = {"items": items}
    elif name == "review":
        files = dict(state.sections.get("review", {}).get("files", {}))
        for path, entry in data["files"].items():
            if entry is None:
                files.pop(path, None)  # reviewed, nothing to say
            else:
                files[path] = entry
        if pr_files is not None:  # drop files that left the PR
            files = {p: e for p, e in files.items() if p in pr_files}
        state.sections["review"] = {"files": files, "sha": data["sha"]}
    else:
        state.sections[name] = data


def holds(state: State, name: str, data: dict) -> bool:
    """Is what we wrote still in the comment? A newer run's write also counts."""
    actual = state.sections.get(name)
    if actual is None:
        return name == "review" and all(e is None for e in data["files"].values())
    if name == "kept":
        return all(actual.get("items", {}).get(k) == v for k, v in data["items"].items())
    if name == "review":
        files = actual.get("files", {})
        return all(
            (path not in files) if entry is None else files.get(path) == entry
            for path, entry in data["files"].items()
        )
    if actual == data:
        return True
    return (actual.get("run") or 0) > (data.get("run") or 0)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def clean(text: str, limit: int = MAX_TEXT) -> str:
    """Make untrusted text (file names, AI output, error messages) harmless:
    no @-mentions, no HTML or fake markers, bounded length."""
    text = str(text).replace("@", "@​").replace("<", "&lt;")
    return text if len(text) <= limit else text[:limit] + "…"


def bi(greek: str, english: str) -> str:
    return f"{greek}\n\n*{english}*"


def short(sha: str | None) -> str:
    return (sha or "")[:7]


def same_commit(a: str | None, b: str | None) -> bool:
    return bool(a and b and (a.startswith(b) or b.startswith(a)))


def bullets(items: list[str]) -> str:
    shown = [f"- {i}" for i in items[:MAX_ITEMS]]
    if len(items) > MAX_ITEMS:
        shown.append(f"- … (+{len(items) - MAX_ITEMS})")
    return "\n".join(shown)


def view_states(state: State, head: str | None) -> dict[str, str]:
    """Status of each visible section: ok, fail, pending, remarks, warn."""
    s = state.sections
    out = {
        "translation": s.get("translation", {}).get("state", "pending"),
        "images": s.get("images", {}).get("state", "pending"),
    }
    prev = s.get("preview")
    out["preview"] = (
        "ok" if prev and prev.get("state") == "ok" and (head is None or same_commit(prev.get("sha"), head))
        else "pending"
    )
    files = s.get("review", {}).get("files", {})
    if any(e.get("error") for e in files.values()):
        out["review"] = "warn"
    elif any(e.get("findings") for e in files.values()):
        out["review"] = "remarks"
    else:
        out["review"] = "ok"
    return out


def compute_alerts(views: dict[str, str]) -> set[str]:
    """Problems admins are told about."""
    alerts = {n for n in ("translation", "images") if views[n] == "fail"}
    if views["review"] == "warn":
        alerts.add("review")
    return alerts


def render_translation(data: dict | None) -> str:
    title = "### 1. Μετάφραση / Translation"
    if not data or data.get("state") == "pending":
        return f"{title}\n\n" + bi("⏳ Σε εξέλιξη…", "In progress…")
    sha = f" · commit `{short(data.get('sha'))}`" if data.get("sha") else ""
    if data["state"] == "ok":
        if data.get("nothing"):
            text = bi("✅ Δεν υπάρχει τίποτα για μετάφραση.", "Nothing to translate.")
        elif data.get("files"):
            text = bi("✅ Έτοιμη. Ενημερώθηκαν αυτά τα αρχεία:", "Done. These files were updated:")
            text += "\n\n" + bullets([f"`{clean(f, 200)}`" for f in data["files"]])
        else:
            text = bi("✅ Οι μεταφράσεις είναι ήδη ενημερωμένες.", "The translations are already up to date.")
        return f"{title}{sha}\n\n{text}"
    kind = data.get("kind")
    if kind == "non-greek":
        why = bi(
            "Οι αναρτήσεις γράφονται στα ελληνικά, αλλά βρέθηκε αρχείο σε άλλη γλώσσα χωρίς σύνδεση με ελληνικό κείμενο.",
            "Posts are written in Greek, but a file in another language was found that isn't linked to a Greek text.",
        )
    elif kind == "hand-written":
        why = bi(
            "Υπάρχει μετάφραση γραμμένη με το χέρι που θα αντικαθίστατο. Ο διαχειριστής θα αποφασίσει τι θα γίνει.",
            "A hand-written translation exists that would have been overwritten. The site admin will decide what to do.",
        )
    elif kind == "missing":
        why = bi(
            "Λείπει μετάφραση για κάποιο αρχείο (δες παρακάτω).",
            "A translation is missing for some file (see below).",
        )
    else:
        why = bi("Παρουσιάστηκε τεχνικό πρόβλημα.", "A technical problem came up.")
    text = bi("❌ Η μετάφραση δεν ολοκληρώθηκε.", "Translation did not finish.") + "\n\n" + why
    if data.get("message"):
        text += "\n\n<details><summary>Λεπτομέρειες / Details</summary>\n\n"
        text += clean(data["message"], 1500) + "\n\n</details>"
    return f"{title}{sha}\n\n{text}"


def render_kept(data: dict | None) -> str:
    if not data or not data.get("items"):
        return ""
    text = bi(
        "ℹ️ Η ελληνική εκδοχή άλλαξε, αλλά η ολλανδική ή η αγγλική μετάφραση είχε διορθωθεί με το χέρι, "
        "οπότε κρατήθηκε όπως ήταν. Μπορεί να μην ταιριάζει πια με το ελληνικό κείμενο: έλεγξέ την στο /admin.",
        "The Greek changed, but the Dutch or English translation had been corrected by hand, so it was kept "
        "as it was. It may no longer match the Greek: check it in /admin.",
    )
    return text + "\n\n" + bullets([clean(v, 300) for v in data["items"].values()])


def render_images(data: dict | None) -> str:
    title = "### 2. Εικόνες / Images"
    if not data or data.get("state") == "pending":
        return f"{title}\n\n" + bi("⏳ Σε εξέλιξη…", "In progress…")
    sha = f" · commit `{short(data.get('sha'))}`" if data.get("sha") else ""
    if data["state"] == "ok":
        if data.get("count"):
            text = bi(f"✅ Οι εικόνες είναι εντάξει ({data['count']}).", f"The images are fine ({data['count']}).")
        else:
            text = bi("✅ Καμία αλλαγή σε εικόνες.", "No image changes.")
        return f"{title}{sha}\n\n{text}"
    text = bi("❌ Κάποια εικόνα δεν μπορεί να χρησιμοποιηθεί:", "An image can't be used:")
    if data.get("problems"):
        text += "\n\n" + bullets([clean(p, 300) for p in data["problems"]])
    return f"{title}{sha}\n\n{text}"


def render_preview(data: dict | None, ok: bool) -> str:
    title = "### 3. Προεπισκόπηση / Preview"
    if ok and data and URL_RE.match(data.get("url", "")):
        return (
            f"{title} · commit `{short(data.get('sha'))}`\n\n"
            + bi(f"✅ [Άνοιγμα προεπισκόπησης]({data['url']})", f"[Open the preview]({data['url']})")
        )
    return f"{title}\n\n" + bi("⏳ Η προεπισκόπηση ετοιμάζεται…", "The preview is being built…")


SEVERITY_EMOJI = {"critical": "🔴", "major": "🟠", "minor": "🟡"}
SEVERITY_ORDER = ["critical", "major", "minor"]


def render_review(data: dict | None, view: str) -> str:
    title = "### 4. Έλεγχος AI / AI review"
    files = (data or {}).get("files", {})
    if view == "ok":
        return f"{title}\n\n" + bi("✅ Καμία παρατήρηση.", "No remarks.")
    text = ""
    if view == "remarks":
        text = bi("💬 Παρατηρήσεις (συμβουλευτικές, δεν εμποδίζουν τη δημοσίευση):",
                  "Remarks (advice only, they don't block publishing):")
    else:
        text = bi("⚠️ Ο έλεγχος AI δεν μπόρεσε να ελέγξει κάποιο αρχείο. Δεν εμποδίζει τη δημοσίευση· ο διαχειριστής ενημερώθηκε.",
                  "The AI review could not check some file. It doesn't block publishing; the site admin has been notified.")
    for path in sorted(files):
        entry = files[path]
        sha = f" · `{short(entry.get('sha'))}`" if entry.get("sha") else ""
        if entry.get("error"):
            text += (f"\n\n<details><summary>⚠️ <code>{clean(path, 200)}</code>{sha}</summary>\n\n"
                     f"Error: `{clean(entry['error'], 300)}`\n\n</details>")
        elif entry.get("findings"):
            ordered = sorted(
                entry["findings"],
                key=lambda f: SEVERITY_ORDER.index(f.get("severity")) if f.get("severity") in SEVERITY_ORDER else 9,
            )
            lines = []
            for f in ordered[:MAX_ITEMS]:
                sev = f.get("severity", "minor")
                lines.append(f"- {SEVERITY_EMOJI.get(sev, '⚪')} **{clean(sev, 20).upper()}** "
                             f"({clean(f.get('field', 'unknown'), 40)}): {clean(f.get('message', ''), 400)}")
            text += (f"\n\n<details><summary>💬 <code>{clean(path, 200)}</code> "
                     f"({len(ordered)}){sha}</summary>\n\n" + "\n".join(lines) + "\n\n</details>")
    return f"{title}\n\n{text}"


def next_step(views: dict[str, str]) -> tuple[str, str]:
    """One line (Greek, English) from the sections' states."""
    problems_gr, problems_en = [], []
    if views["translation"] == "fail":
        problems_gr.append("Η μετάφραση δεν ολοκληρώθηκε: ο διαχειριστής ενημερώθηκε και θα το φροντίσει, δεν χρειάζεται να κάνεις κάτι.")
        problems_en.append("Translation did not finish: the site admin has been told and will take care of it, nothing for you to do.")
    if views["images"] == "fail":
        problems_gr.append("Αντικατάστησε την εικόνα που δεν μπορεί να χρησιμοποιηθεί (JPEG, PNG ή WebP, έως 5 MB) και αποθήκευσε ξανά· ο διαχειριστής ενημερώθηκε και θα βοηθήσει αν το μήνυμα δεν φύγει.")
        problems_en.append("Replace the image that can't be used (JPEG, PNG or WebP, up to 5 MB) and save again; the site admin has been told and will help if this message doesn't go away.")
    if problems_gr:
        return " ".join(problems_gr), " ".join(problems_en)

    waiting = [(g, e) for n, g, e in
               (("translation", "μετάφραση", "translation"), ("images", "εικόνες", "images"),
                ("preview", "προεπισκόπηση", "preview"))
               if views[n] == "pending"]
    if waiting:
        return (
            "⏳ Περίμενε λίγο, τρέχουν ακόμα: " + ", ".join(g for g, _ in waiting) + ". Αυτό το σχόλιο ενημερώνεται μόνο του.",
            "Wait a moment, still running: " + ", ".join(e for _, e in waiting) + ". This comment updates by itself.",
        )

    gr = "Έτοιμο: στο /admin → Workflow, βάλε την ανάρτηση στο Ready και πάτα Publish."
    en = "Ready: in /admin → Workflow, move the post to Ready and press Publish."
    if views["review"] == "remarks":
        gr += " Δες πρώτα τις παρατηρήσεις του ελέγχου AI (προαιρετικό)."
        en += " Read the AI review remarks first (optional)."
    elif views["review"] == "warn":
        gr += " Ο έλεγχος AI δεν έτρεξε, αλλά αυτό δεν εμποδίζει τη δημοσίευση."
        en += " The AI review did not run, but that doesn't block publishing."
    return gr, en


def render(state: State, head: str | None, mentions: str = "", run_url: str = "") -> str:
    """The whole comment. The `alerts` marker records who has been told."""
    views = view_states(state, head)
    alerts = compute_alerts(views)
    s = state.sections
    prev = s.get("preview")

    def block(name: str, text: str) -> str:
        data = s.get(name)
        return f"<!-- pr-status:begin {name} {encode(data) if data is not None else ''} -->\n{text}\n<!-- pr-status:end {name} -->"

    tr = render_translation(s.get("translation"))
    kept = render_kept(s.get("kept"))
    parts = [
        MARK,
        f"<!-- pr-status:alerts {','.join(sorted(alerts))} -->",
        "## Κατάσταση της ανάρτησης / Post status",
        block("translation", tr),
        block("kept", kept) if kept else "",
        block("images", render_images(s.get("images"))),
        block("preview", render_preview(prev, views["preview"] == "ok")),
        block("review", render_review(s.get("review"), views["review"])),
    ]
    gr, en = next_step(views)
    parts.append(f"### 5. Τι ακολουθεί / Next step\n\n{gr}\n\n*{en}*")
    footer = []
    if alerts and mentions.strip():
        footer.append(f"cc {mentions.strip()}")
    if run_url:
        footer.append(f"[τελευταία ενημέρωση / last update]({run_url})")
    if footer:
        parts.append(" · ".join(footer))
    return "\n\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Updating the comment
# ---------------------------------------------------------------------------


def is_bot(comment: dict) -> bool:
    return comment.get("login") == BOT_LOGIN


def status_comments(comments: list[dict]) -> list[dict]:
    return sorted(
        (c for c in comments if is_bot(c) and MARK in (c.get("body") or "")),
        key=lambda c: c["id"],
    )


def legacy_comments(comments: list[dict]) -> list[dict]:
    return [c for c in comments if is_bot(c) and any(m in (c.get("body") or "") for m in LEGACY_MARKERS)]


def legacy_kept_items(legacy: list[dict]) -> dict[str, str]:
    """The list in an old "kept" notice, keyed by the `path` in backticks."""
    items = {}
    for c in legacy:
        body = c["body"]
        if "<!-- pr-notice:kept -->" not in body:
            continue
        for line in body.splitlines():
            if line.startswith("- ") and "`" in line:
                start = line.find("`")
                end = line.find("`", start + 1)
                items[line[start + 1:end]] = line[2:]
    return items


class NotVerified(Exception):
    pass


def touches_content(files: list[str]) -> bool:
    return any(f.startswith(CONTENT_PREFIXES) for f in files)


def update(
    api: Api,
    name: str,
    data: dict,
    *,
    mentions: str = "",
    run_url: str = "",
    attempts: int = 5,
    settle: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Write one section into the status comment. Returns a log line.

    Read, change, write, settle, re-read and check; retry when the section was
    lost to a concurrent writer or the comment vanished (recreated by another job).
    """
    for attempt in range(attempts):
        if attempt:
            sleep(random.uniform(1, 3) * attempt)
        api._head = None  # the bot may have pushed since the last attempt
        comments = api.comments()
        existing = status_comments(comments)
        legacy = legacy_comments(comments)

        if not existing and not touches_content(api.files()):
            return "skip: this PR changes no content or images"

        state = merge_states([parse(c["body"]) for c in existing])
        if "kept" not in state.sections and (items := legacy_kept_items(legacy)):
            state.sections["kept"] = {"items": items}
        told = set(state.alerts)

        files = api.files() if name == "review" else None
        apply_section(state, name, data, files)
        body = render(state, api.head_sha(), mentions, run_url)
        new_alerts = parse(body).alerts

        try:
            if not existing:
                api.create(body)
                action = "created"
            elif new_alerts - told:
                # A failure admins weren't told about: a new comment notifies.
                api.create(body)
                for c in existing:
                    api.delete(c["id"])
                action = "re-created (new failure, notifies)"
            else:
                target, duplicates = existing[-1], existing[:-1]
                if body != target["body"]:
                    api.edit(target["id"], body)
                for c in duplicates:
                    api.delete(c["id"])
                action = "updated"
        except subprocess.CalledProcessError:
            continue  # e.g. the comment was deleted under us: look again

        sleep(settle)
        after = status_comments(api.comments())
        if len(after) == 1 and holds(parse(after[0]["body"]), name, data):
            for c in legacy:
                try:
                    api.delete(c["id"])
                except subprocess.CalledProcessError:
                    pass
            return f"Section '{name}' {action} on PR #{api.pr}"
    raise NotVerified(f"section '{name}' could not be written after {attempts} attempts")


# ---------------------------------------------------------------------------
# Section data from the command line
# ---------------------------------------------------------------------------


def read_lines(path: str | None) -> list[str]:
    if not path or not Path(path).is_file():
        return []
    return [l.rstrip("\n") for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def run_stamp() -> int:
    try:
        return int(os.environ.get("GITHUB_RUN_ID", "0"))
    except ValueError:
        return 0


def entry_key(line: str) -> str:
    start = line.find("`")
    end = line.find("`", start + 1)
    return line[start + 1:end] if start != -1 and end != -1 else line


def build_data(args: argparse.Namespace) -> dict:
    sha = getattr(args, "sha", None) or ""
    if args.section == "translation":
        data = {"state": args.state, "sha": sha, "run": run_stamp()}
        if args.state == "ok":
            data["files"] = [l.split("\t")[-1] for l in read_lines(args.written)]
            data["nothing"] = bool(args.nothing)
        else:
            report = Path(args.report) if args.report else None
            if report and report.is_file() and report.stat().st_size:
                try:
                    r = json.loads(report.read_text(encoding="utf-8"))
                    data["kind"], data["message"] = r.get("kind", ""), r.get("message", "")
                except ValueError:
                    pass
            elif args.missing:
                data["kind"] = "missing"
                data["message"] = "\n".join(read_lines(args.missing))
        return data
    if args.section == "kept":
        return {"items": {entry_key(l): l[2:] for l in read_lines(args.file) if l.startswith("- ")}}
    if args.section == "images":
        data = {"state": args.state, "sha": sha, "run": run_stamp()}
        if args.state == "ok":
            data["count"] = args.count
        else:
            data["problems"] = [l[2:] if l.startswith("- ") else l for l in read_lines(args.problems)]
        return data
    if args.section == "preview":
        return {"state": "ok", "sha": sha, "url": args.url, "run": run_stamp()}
    # review: results is the content_review.py JSON; reviewed is the file list
    reviewed = read_lines(args.reviewed)
    files: dict[str, dict | None] = {p: None for p in reviewed}
    results_path = Path(args.results) if args.results else None
    if results_path and results_path.is_file():
        for r in json.loads(results_path.read_text(encoding="utf-8")):
            files[r["file"]] = {"sha": sha, "error": r.get("error"), "findings": r.get("findings") or []}
    else:  # the review step died before writing anything
        files = {p: {"sha": sha, "error": "the review did not run", "findings": []} for p in reviewed}
    return {"files": files, "sha": sha}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="section", required=True)

    t = sub.add_parser("translation")
    t.add_argument("--state", choices=["ok", "fail"], required=True)
    t.add_argument("--sha")
    t.add_argument("--written", help="file with the changed content paths, one per line")
    t.add_argument("--nothing", action="store_true", help="no content to translate")
    t.add_argument("--report", help="TRANSLATE_REPORT json written by translate.py")
    t.add_argument("--missing", help="VERIFY_REPORT: files missing a translation")

    k = sub.add_parser("kept")
    k.add_argument("--file", required=True, help="KEPT_REPORT")

    i = sub.add_parser("images")
    i.add_argument("--state", choices=["ok", "fail"], required=True)
    i.add_argument("--sha")
    i.add_argument("--count", type=int, default=0)
    i.add_argument("--problems", help="markdown list of problems")

    v = sub.add_parser("preview")
    v.add_argument("--sha", required=True)
    v.add_argument("--url", required=True)

    r = sub.add_parser("review")
    r.add_argument("--sha")
    r.add_argument("--reviewed", required=True, help="files the review was asked to check")
    r.add_argument("--results", help="REVIEW_OUTPUT json from content_review.py")
    return p


def main(argv: list[str] | None = None, run: Runner = gh) -> int:
    args = parser().parse_args(sys.argv[1:] if argv is None else argv)
    if args.section == "kept" and not read_lines(args.file):
        print("No hand-corrected translations were kept.")
        return 0
    data = build_data(args)
    api = Api(os.environ["REPO"], os.environ["PR_NUMBER"], run)
    try:
        print(update(api, args.section, data,
                     mentions=os.environ.get("ADMIN_MENTIONS", ""),
                     run_url=os.environ.get("RUN_URL", "")))
    except (NotVerified, subprocess.CalledProcessError) as e:
        # The comment is a courtesy: never fail the check because of it.
        print(f"::warning title=PR status comment::{e}")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
