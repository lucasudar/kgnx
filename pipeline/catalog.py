"""Build the tool catalogue from editorial metadata and GitHub evidence.

    python3 -m pipeline.catalog

A catalogue entry is anything a person can start using: a desktop app, a
command-line tool, a self-hosted service, or a browser extension. The editorial
file describes what it does for a person; GitHub supplies only trust evidence.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from .evidence import collect
from .gh import Github

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog" / "tools.json"
AUTOMATIC = ROOT / "data" / "catalog" / "automatic.json"
LIFECYCLE = ROOT / "data" / "editorial" / "lifecycle.json"
OUTPUT = ROOT / "data" / "tools" / "feed.json"

KIND_ORDER = ["app", "cli", "service", "extension"]
KIND_LABELS = {
    "app": "App",
    "cli": "Command line",
    "service": "Self-hosted",
    "extension": "Browser extension",
}


def enrich(gh: Github, tool: dict, lifecycle: dict) -> dict | None:
    repo = gh.get(f"/repos/{tool['repo']}")
    if not repo:
        print(f"warning: repository not found, dropping {tool['slug']} ({tool['repo']})")
        return None

    evidence = collect(gh, repo)
    if not evidence:
        return None

    result = dict(tool)
    result["kind_label"] = KIND_LABELS.get(tool["kind"], tool["kind"].title())
    result["lifecycle"] = lifecycle[tool["slug"]]
    result["github"] = evidence.to_dict()
    result["trust"] = {
        "maturity": evidence.maturity,
        "last_push_days": evidence.pushed_days_ago,
        "contributors": evidence.contributors,
        "commits": evidence.commits,
        "releases": evidence.releases,
        "has_tests": evidence.has_tests,
        "has_ci": evidence.has_ci,
        "has_license": evidence.has_license,
        "license": (repo.get("license") or {}).get("spdx_id"),
        "stars": evidence.stars,
        "language": evidence.language,
    }
    return result


def editorial_order(tool: dict) -> tuple:
    """Featured picks first, then healthy tools; popularity is capped on purpose."""
    trust = tool["trust"]
    active = 1 if tool["lifecycle"]["status"] == "active" else 0
    featured = 1 if tool.get("featured") else 0
    maturity = {"proven": 2, "promising": 1, "risky": 0}.get(trust["maturity"], 0)
    stars = min(trust["stars"], 10_000)
    return active, featured, maturity, stars


def main() -> None:
    tools = json.loads(CATALOG.read_text())
    if AUTOMATIC.exists():
        tools.extend(json.loads(AUTOMATIC.read_text()))
    if not LIFECYCLE.exists():
        raise SystemExit("No lifecycle state. Run `python3 -m pipeline.lifecycle` first.")
    lifecycle = json.loads(LIFECYCLE.read_text())
    gh = Github()
    with ThreadPoolExecutor(max_workers=6) as pool:
        enriched = [
            item
            for item in pool.map(lambda tool: enrich(gh, tool, lifecycle), tools)
            if item
        ]

    enriched.sort(key=editorial_order, reverse=True)

    kinds = [
        {"id": kind, "label": KIND_LABELS[kind], "count": sum(1 for t in enriched if t["kind"] == kind)}
        for kind in KIND_ORDER
        if any(t["kind"] == kind for t in enriched)
    ]

    feed = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(enriched),
        "active_count": sum(
            1 for tool in enriched if tool["lifecycle"]["status"] == "active"
        ),
        "archive_count": sum(
            1 for tool in enriched if tool["lifecycle"]["status"] == "archived"
        ),
        "automatic_count": sum(1 for tool in enriched if tool.get("automated")),
        "kinds": kinds,
        "categories": sorted({c for t in enriched for c in t["categories"]}),
        "platforms": sorted({p for t in enriched for p in t["platforms"]}),
        "tools": enriched,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(feed, indent=2, ensure_ascii=False))

    summary = ", ".join(f"{k['count']} {k['label'].lower()}" for k in kinds)
    print(f"built {len(enriched)} tools ({summary}) -> {OUTPUT}")
    print(f"api requests: {gh.requests}, cache hits: {gh.cache_hits}")


if __name__ == "__main__":
    main()
