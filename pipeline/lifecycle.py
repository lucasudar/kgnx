"""Maintain the transparent publication lifecycle.

    python3 -m pipeline.lifecycle
    python3 -m pipeline.lifecycle --republish jiggler

New editorial catalogue entries receive a 30-day publication window. They move
to Archive automatically afterward but remain searchable, saved, and linked.
Republishing is an explicit Git change, not a hidden database mutation.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog" / "tools.json"
AUTOMATIC = ROOT / "data" / "catalog" / "automatic.json"
STATE = ROOT / "data" / "editorial" / "lifecycle.json"
DEFAULT_DAYS = 30


def iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def new_window(now: datetime, days: int, generation: int = 1) -> dict:
    return {
        "status": "active",
        "published_at": iso(now),
        "active_until": iso(now + timedelta(days=days)),
        "archived_at": None,
        "generation": generation,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--republish", help="slug to return to the current feed")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    args = parser.parse_args()

    tools = json.loads(CATALOG.read_text())
    if AUTOMATIC.exists():
        tools.extend(json.loads(AUTOMATIC.read_text()))
    known = {tool["slug"] for tool in tools}
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    now = datetime.now(timezone.utc)

    added = archived = 0
    for slug in sorted(known):
        if slug not in state:
            state[slug] = new_window(now, args.days)
            added += 1
            continue

        item = state[slug]
        if item["status"] == "active" and now >= parse(item["active_until"]):
            item["status"] = "archived"
            item["archived_at"] = iso(now)
            archived += 1

    if args.republish:
        if args.republish not in known:
            raise SystemExit(f"Unknown catalogue slug: {args.republish}")
        generation = state.get(args.republish, {}).get("generation", 0) + 1
        state[args.republish] = new_window(now, args.days, generation)
        print(f"republished {args.republish} for {args.days} days")

    # Keep removed catalogue entries in history; their Git trail remains useful.
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(dict(sorted(state.items())), indent=2))

    active = sum(1 for slug in known if state[slug]["status"] == "active")
    archive = len(known) - active
    print(
        f"lifecycle: {active} active, {archive} archived "
        f"({added} new, {archived} expired)"
    )


if __name__ == "__main__":
    main()
