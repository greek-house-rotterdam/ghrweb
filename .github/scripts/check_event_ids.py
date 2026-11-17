#!/usr/bin/env python3
"""
Check that each Greek event text in a pull request belongs to one real event (#105).

The verify job (translate.yml, a required check) runs

    check_event_ids.py --report PATH FILE...

with the event-translation files the PR adds or changes. For each Greek one
(src/content/event-translations/gr/<name>.md) it checks that:

  - an event is chosen (`tt_event_id`);
  - no other Greek entry is for the same event;
  - the file name is the event's ID. Decap names the file after the event when
    the entry is created and never renames it, so another ID means the event
    was changed later (or Decap added "-1" to a second entry for one event);
  - the event is in the live site's event list, /admin/events.json, which the
    site's build writes from Ticket Tailor (src/pages/admin/events.json.ts).
    So no Ticket Tailor key is needed here.

Exits 1 on a problem, which blocks publishing. When the list can't be read,
or is empty (that build had no events), the last check is skipped with a
warning: an outage must not block posts. Entries the PR doesn't touch are not
checked, so an event leaving Ticket Tailor blocks only a later change to its
own entry, not other posts.

--report writes the result as JSON for the PR status comment
(`pr_status.py events`):

    {"state": "ok" | "warn" | "fail",
     "found": [{"file", "id", "name", "start"}],
     "problems": [{"kind": "missing" | "duplicate" | "renamed" | "unknown",
                   "file", "id", "other"}]}

Nothing is written when the PR changes no Greek event text.
"""

import argparse
import json
import sys
import time
from collections.abc import Callable, Iterable
from pathlib import Path

import requests

from _common import parse_markdown

GREEK_DIR = Path("src/content/event-translations/gr")
EVENTS_URL = "https://ghrweb.enosi-ellinon-ollandias.workers.dev/admin/events.json"
TIMEOUT_S = 15
# Waits between attempts: three tries in all.
RETRY_DELAYS_S = (2, 5)


def greek_files(paths: Iterable[str]) -> list[Path]:
    """The Greek event texts among the changed paths that still exist."""
    out = {Path(p) for p in paths if p.strip()}
    return sorted(p for p in out if p.parent == GREEK_DIR and p.suffix == ".md" and p.is_file())


def read_event_id(path: Path) -> str:
    try:
        frontmatter, _ = parse_markdown(path.read_text(encoding="utf-8"))
    except Exception:
        return ""  # unreadable frontmatter is the build's job to report
    value = frontmatter.get("tt_event_id")
    return "" if value is None else str(value).strip()


def entries_by_event(folder: Path) -> dict[str, list[str]]:
    """Every Greek event text, grouped by the event it is for."""
    out: dict[str, list[str]] = {}
    for f in sorted(folder.glob("*.md")):
        if event_id := read_event_id(f):
            out.setdefault(event_id, []).append(f.as_posix())
    return out


def load_events(
    url: str = EVENTS_URL,
    get: Callable[..., requests.Response] = requests.get,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, dict] | None:
    """The live site's events by ID, or None when the list can't be read or is empty."""
    for attempt in range(len(RETRY_DELAYS_S) + 1):
        if attempt:
            sleep(RETRY_DELAYS_S[attempt - 1])
        try:
            res = get(url, timeout=TIMEOUT_S, headers={"Accept": "application/json"})
        except requests.RequestException:
            continue
        if res.status_code == 429 or res.status_code >= 500:
            continue
        if res.status_code != 200:
            return None  # e.g. 404: trying again won't help
        try:
            events = res.json().get("events")
        except (ValueError, AttributeError):
            return None
        if not isinstance(events, list):
            return None
        by_id = {e["id"]: e for e in events if isinstance(e, dict) and isinstance(e.get("id"), str)}
        return by_id or None
    return None


def check(files: list[Path], events: dict[str, dict] | None, folder: Path = GREEK_DIR) -> dict:
    by_event = entries_by_event(folder)
    found: list[dict] = []
    problems: list[dict] = []
    for path in files:
        f = path.as_posix()
        event_id = read_event_id(path)
        if not event_id:
            problems.append({"kind": "missing", "file": f})
            continue
        others = [o for o in by_event.get(event_id, []) if o != f]
        if others:
            problems.append({"kind": "duplicate", "file": f, "id": event_id, "other": others[0]})
            continue
        if path.stem != event_id:
            problems.append({"kind": "renamed", "file": f, "id": event_id})
            continue
        if events is None:
            continue
        event = events.get(event_id)
        if event is None:
            problems.append({"kind": "unknown", "file": f, "id": event_id})
        else:
            found.append({
                "file": f,
                "id": event_id,
                "name": str(event.get("name") or ""),
                "start": str(event.get("start") or ""),
            })
    state = "fail" if problems else ("warn" if events is None else "ok")
    return {"state": state, "found": found, "problems": problems}


MESSAGES = {
    "missing": "no event is chosen",
    "duplicate": "event {id} already has Greek text in {other}",
    "renamed": "the file is named for another event than {id}: the event was changed after the entry was created",
    "unknown": "{id} is not in the site's list of Ticket Tailor events",
}


def main(
    argv: list[str] | None = None,
    get: Callable[..., requests.Response] = requests.get,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="*", help="changed files; only Greek event texts are checked")
    ap.add_argument("--report", help="write the result as JSON, for the PR status comment")
    ap.add_argument("--events-url", default=EVENTS_URL, help="the site's public event list")
    args = ap.parse_args(sys.argv[1:] if argv is None else argv)

    files = greek_files(args.files)
    if not files:
        print("No Greek event texts changed.")
        return 0
    events = load_events(args.events_url, get, sleep)
    if events is None:
        print(f"::warning title=Event check::Could not read the event list at {args.events_url}; "
              "not checking that the events exist.")
    result = check(files, events)
    for item in result["found"]:
        print(f"✅ {item['file']}: {item['id']} «{item['name']}» {item['start']}")
    for p in result["problems"]:
        print(f"❌ {p['file']}: " + MESSAGES[p["kind"]].format(**p))
    if args.report:
        Path(args.report).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return 1 if result["state"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
