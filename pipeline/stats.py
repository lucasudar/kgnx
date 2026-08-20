"""Refresh the live numbers in README between the stats markers.

    python3 -m pipeline.stats

The catalogue rotates daily, so counts must never be hand-written into prose.
Everything here is derived from generated data and rewritten in place.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "data" / "tools" / "feed.json"
CANDIDATES = ROOT / "data" / "candidates" / "candidates.json"
README = ROOT / "README.md"

START = "<!-- stats:start -->"
END = "<!-- stats:end -->"


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def humanise(stamp: str) -> str:
    try:
        moment = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return "unknown"
    return moment.strftime("%d %b %Y, %H:%M UTC")


def block(feed: dict, candidates: dict) -> str:
    kinds = feed.get("kinds", [])
    kind_row = " · ".join(f"{kind['count']} {kind['label'].lower()}" for kind in kinds)
    rows = [
        ("Published", feed.get("count", 0)),
        ("Current", feed.get("active_count", 0)),
        ("Archived", feed.get("archive_count", 0)),
        ("Chosen unattended", feed.get("automatic_count", 0)),
        ("Screened last run", candidates.get("screened", 0)),
        ("Waiting candidates", len(candidates.get("proposals", []))),
    ]
    header = " | ".join(label for label, _ in rows)
    divider = " | ".join("---" for _ in rows)
    values = " | ".join(f"**{value}**" for _, value in rows)

    return "\n".join(
        [
            START,
            "",
            f"| {header} |",
            f"| {divider} |",
            f"| {values} |",
            "",
            f"{kind_row}. Evidence refreshed {humanise(feed.get('generated_at', ''))}.",
            "",
            END,
        ]
    )


def main() -> None:
    feed = load(FEED)
    if not feed:
        raise SystemExit("No catalogue. Run `python3 -m pipeline.catalog` first.")

    text = README.read_text()
    if START not in text or END not in text:
        raise SystemExit(f"README is missing the {START} / {END} markers.")

    head, _, rest = text.partition(START)
    _, _, tail = rest.partition(END)
    README.write_text(head + block(feed, load(CANDIDATES)) + tail)
    print(f"stats: refreshed README for {feed.get('count', 0)} tools")


if __name__ == "__main__":
    main()
