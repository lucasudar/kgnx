"""Promote strict candidates without human involvement.

    python3 -m pipeline.autopublish
    python3 -m pipeline.autopublish --limit 2

The script publishes at most one new tool per daily run by default. It rotates
through kinds so one fashionable category cannot occupy the whole feed. Missing
product facts are represented honestly rather than invented.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "data" / "candidates" / "candidates.json"
CURATED = ROOT / "data" / "catalog" / "tools.json"
AUTOMATIC = ROOT / "data" / "catalog" / "automatic.json"
REPORT = ROOT / "data" / "candidates" / "published.json"
KIND_ORDER = ["app", "cli", "service", "extension"]

CATEGORY_TERMS = {
    "AI": (" ai ", "llm", "agent"),
    "Automation": ("automation", "workflow"),
    "Backup": ("backup", "sync"),
    "Browser": ("browser", "chrome", "firefox"),
    "Developer tools": ("developer", "coding", "code ", "git", "api"),
    "Documents": ("pdf", "document", "ocr"),
    "Media": ("video", "audio", "music", "photo", "screen recorder"),
    "Networking": ("network", "proxy", "dns", "firewall"),
    "Privacy": ("privacy", "encrypted", "local first", "local-first"),
    "Productivity": ("productivity", "clipboard", "window", "workspace"),
    "Self-hosted": ("self hosted", "self-hosted", "selfhosted", "homelab"),
    "System": ("system", "monitor", "process", "disk"),
    "Terminal": ("terminal", " cli", "tui", "command line"),
}


def text(candidate: dict) -> str:
    return " ".join(
        [
            candidate["repo"],
            candidate.get("upstream_description") or "",
            " ".join(candidate.get("topics") or []),
        ]
    ).lower().replace("-", " ").replace("_", " ")


def infer_platforms(candidate: dict) -> list[str]:
    value = text(candidate)
    kind = candidate["kind"]
    if kind == "service":
        return ["Self-hosted", "Docker"] if "docker" in value else ["Self-hosted"]
    if kind == "extension":
        result = []
        if "firefox" in value:
            result.append("Firefox")
        if "chrome" in value or "chromium" in value:
            result.append("Chrome")
        if "safari" in value:
            result.append("Safari")
        return result or ["Browser"]
    if kind == "cli":
        # The candidate is known to be a terminal tool, but GitHub metadata
        # usually cannot prove every supported operating system.
        return ["Terminal"]

    result = []
    if any(term in value for term in ("macos", "mac os", "swiftui", "apple silicon")):
        result.append("macOS")
    if "windows" in value:
        result.append("Windows")
    if "linux" in value:
        result.append("Linux")
    if "android" in value:
        result.append("Android")
    if " ios " in f" {value} ":
        result.append("iOS")
    return result or ["Desktop"]


def infer_categories(candidate: dict) -> list[str]:
    value = f" {text(candidate)} "
    found = [
        category
        for category, terms in CATEGORY_TERMS.items()
        if any(term in value for term in terms)
    ]
    fallback = {
        "app": "Productivity",
        "cli": "Developer tools",
        "service": "Self-hosted",
        "extension": "Browser",
    }[candidate["kind"]]
    return (found or [fallback])[:3]


def product_name(repo: str) -> str:
    # The repository slug is the only authoritative name available without a
    # human or an additional product-metadata source. Preserve it exactly.
    return repo.split("/")[-1]


def concise(description: str, limit: int = 190) -> str:
    value = re.sub(r"\s+", " ", description).strip()
    if len(value) <= limit:
        return value
    shortened = value[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return shortened + "…"


def score(candidate: dict) -> float:
    """Momentum with modest depth bonuses; absolute stars never dominate."""
    return (
        candidate.get("stars_per_day", 0)
        + min(candidate.get("contributors") or 0, 50) / 5
        + min(candidate.get("releases") or 0, 30) / 5
    )


def to_tool(candidate: dict, now: str) -> dict:
    return {
        "slug": candidate["suggested_slug"],
        "name": product_name(candidate["repo"]),
        "repo": candidate["repo"],
        "kind": candidate["kind"],
        "pitch": concise(candidate["upstream_description"]),
        "platforms": infer_platforms(candidate),
        "categories": infer_categories(candidate),
        "traits": ["Open source", "Actively maintained", "Tests + CI"],
        "get_url": candidate["url"],
        "automated": True,
        "selected_at": now,
        "selection_reason": (
            f"{candidate['maturity']} · updated {candidate['last_push_days']}d ago · "
            f"{candidate['contributors']} contributors · {candidate['releases']} releases"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--force", action="store_true", help="allow another publication today")
    args = parser.parse_args()

    report = json.loads(CANDIDATES.read_text())
    curated = json.loads(CURATED.read_text())
    automatic = json.loads(AUTOMATIC.read_text()) if AUTOMATIC.exists() else []
    known_repos = {
        tool["repo"].lower() for tool in [*curated, *automatic]
    }
    known_slugs = {tool["slug"] for tool in [*curated, *automatic]}

    today = datetime.now(timezone.utc)
    published_today = any(
        tool.get("selected_at", "")[:10] == today.date().isoformat()
        for tool in automatic
    )
    available = [
        candidate
        for candidate in report["proposals"]
        if candidate["repo"].lower() not in known_repos
        and candidate["suggested_slug"] not in known_slugs
    ]
    by_kind = {
        kind: sorted(
            (candidate for candidate in available if candidate["kind"] == kind),
            key=score,
            reverse=True,
        )
        for kind in KIND_ORDER
    }

    # Rotate the first choice by UTC day, then continue around the ring.
    start = today.toordinal() % len(KIND_ORDER)
    rotation = KIND_ORDER[start:] + KIND_ORDER[:start]
    selected = []
    if published_today and not args.force:
        print("daily publication already exists; use --force to override")
        args.limit = 0
    while len(selected) < args.limit:
        progress = False
        for kind in rotation:
            if by_kind[kind] and len(selected) < args.limit:
                selected.append(by_kind[kind].pop(0))
                progress = True
        if not progress:
            break

    selected_at = today.isoformat(timespec="seconds")
    published = [to_tool(candidate, selected_at) for candidate in selected]
    automatic.extend(published)
    AUTOMATIC.parent.mkdir(parents=True, exist_ok=True)
    AUTOMATIC.write_text(json.dumps(automatic, indent=2, ensure_ascii=False))

    publication_report = {
        "generated_at": selected_at,
        "new_count": len(published),
        "new_tools": published,
        "automatic_total": len(automatic),
    }
    REPORT.write_text(json.dumps(publication_report, indent=2, ensure_ascii=False))

    if published:
        for tool in published:
            print(f"auto-published: {tool['name']} ({tool['kind']}) — {tool['repo']}")
    else:
        print("auto-published: none (no unseen candidate passed the strict gate)")


if __name__ == "__main__":
    main()
