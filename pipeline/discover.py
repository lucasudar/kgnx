"""Propose new catalogue candidates from GitHub Search.

    python3 -m pipeline.discover                 # every kind
    python3 -m pipeline.discover --kind cli      # one kind
    python3 -m pipeline.discover --limit 12

Search generates candidates and evidence filters them; nothing is published
automatically. Approved entries are copied by hand into
`data/catalog/tools.json`, which keeps editorial judgement in the loop.
"""

from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .evidence import Evidence, collect
from .gh import Github

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog" / "tools.json"
AUTOMATIC = ROOT / "data" / "catalog" / "automatic.json"
OUTPUT = ROOT / "data" / "candidates" / "candidates.json"

# Ceilings keep household names out: they are already easy to find elsewhere.
QUERIES = {
    "app": [
        "topic:macos topic:swift stars:{stars} pushed:>{recent}",
        "topic:macos-app stars:{stars} pushed:>{recent}",
        "topic:menubar stars:{stars} pushed:>{recent}",
        "topic:desktop-app topic:electron stars:{stars} pushed:>{recent}",
        "topic:tauri stars:{stars} pushed:>{recent}",
    ],
    "cli": [
        "topic:cli topic:rust stars:{stars} pushed:>{recent}",
        "topic:cli-tool stars:{stars} pushed:>{recent}",
        "topic:terminal stars:{stars} pushed:>{recent}",
        "topic:tui stars:{stars} pushed:>{recent}",
    ],
    "service": [
        "topic:self-hosted stars:{stars} pushed:>{recent}",
        "topic:selfhosted topic:docker stars:{stars} pushed:>{recent}",
        "topic:homelab stars:{stars} pushed:>{recent}",
    ],
    "extension": [
        "topic:browser-extension stars:{stars} pushed:>{recent}",
        "topic:firefox-addon stars:{stars} pushed:>{recent}",
        "topic:chrome-extension stars:{stars} pushed:>{recent}",
    ],
}

BOUNDS = {
    "app": (150, 25_000),
    "cli": (200, 25_000),
    "service": (200, 30_000),
    "extension": (150, 20_000),
}
RECENT_DAYS = 45

# A tool must be runnable, so reading material and course repos are rejected.
REJECT_WORDS = (
    "awesome", "curated", "list of", "cheatsheet", "tutorial", "course",
    "roadmap", "interview", "boilerplate", "starter", "template", "example",
    "dotfiles", "config", "theme", "wallpaper", "icon pack", "learning",
    "book", "notes", "guide", "playground", "clone of", "demo",
    # High-risk or low-trust categories are not suitable for unattended
    # publication. They can be nominated manually later if policy changes.
    "bypass", "watermark remover", "account generator", "account register",
    "credential stealer", "spam", "botting", "captcha solver", "cheat",
    "piracy", "crack", "malware", "exploit kit",
)

KIND_TERMS = {
    "app": (
        "macos", "mac app", "desktop app", "menu bar", "menubar", "swiftui",
        "electron app", "tauri app", "windows app", "desktop application",
    ),
    "cli": (
        " cli", "cli ", "command line", "command-line", "terminal tool",
        "terminal ui", " tui", "tui ", "shell tool",
    ),
    "service": (
        "self hosted", "self-hosted", "selfhosted", "homelab", "docker compose",
        "docker-compose", "home server", "self hosting",
    ),
    "extension": (
        "browser extension", "chrome extension", "firefox extension",
        "firefox addon", "firefox add-on", "webextension",
    ),
}

DESCRIPTION_PATTERNS = {
    "app": (
        r"\bdesktop (app|application|workspace|client)\b",
        r"\b(macos|mac|windows) (app|application|client)\b",
        r"\b(app|application|client|editor|viewer|manager) for\b",
        r"\bcross-platform (app|application|client)\b",
    ),
    "cli": (
        r"\bcli\b", r"\bcommand[- ]line (tool|app|utility)\b",
        r"\bterminal (app|tool|utility|manager|weather)\b",
        r"\bfor the terminal\b", r"\bfuzzy finder\b", r"\bmultiplexer\b",
        r"\b(native )?renderer\b",
    ),
    "service": (
        r"\bself[- ]hosted\b", r"\bselfhosted\b", r"\bself hostable\b",
        r"\bhome server\b", r"\bserver you\b", r"\bdocker\b",
    ),
    "extension": (
        r"\bbrowser[- ]extension\b", r"\b(chrome|firefox|safari) extension\b",
        r"\bfirefox add[- ]?on\b", r"\bwebextension\b",
    ),
}


def fill(query: str, kind: str) -> str:
    low, high = BOUNDS[kind]
    recent = datetime.now(timezone.utc).date() - timedelta(days=RECENT_DAYS)
    return query.replace("{stars}", f"{low}..{high}").replace("{recent}", str(recent))


def looks_like_reading_material(repo: dict) -> bool:
    text = " ".join(
        [
            repo.get("full_name", "").split("/")[-1],
            repo.get("description") or "",
            " ".join(repo.get("topics") or []),
        ]
    ).lower().replace("-", " ").replace("_", " ")
    return any(word in text for word in REJECT_WORDS)


def kind_score(repo: dict, kind: str) -> int:
    """Require direct textual evidence that the candidate belongs to its kind."""
    text = " ".join(
        [
            repo.get("full_name", "").split("/")[-1],
            repo.get("description") or "",
            " ".join(repo.get("topics") or []),
        ]
    ).lower().replace("-", " ").replace("_", " ")
    return sum(1 for term in KIND_TERMS[kind] if term.replace("-", " ") in text)


def description_proves_kind(repo: dict, kind: str) -> bool:
    """Topics generate leads; the project's own description must confirm kind."""
    description = (repo.get("description") or "").lower()
    return any(re.search(pattern, description) for pattern in DESCRIPTION_PATTERNS[kind])


def looks_like_dependency(repo: dict, kind: str) -> bool:
    """Reject SDKs/libraries that topic search mistakes for runnable tools."""
    if kind not in ("app", "cli"):
        return False
    description = (repo.get("description") or "").lower()
    topics = {topic.lower() for topic in repo.get("topics") or []}
    dependency_topics = {
        "library", "framework", "sdk", "cli-framework", "swift-package",
        "npm-package", "python-library", "rust-library",
    }
    if not (
        any(word in description for word in (" library", " sdk", " framework"))
        or topics.intersection(dependency_topics)
    ):
        return False
    runnable_words = (
        "desktop app", "application", " client", " editor", " viewer",
        " manager", " workspace", "command line tool", "command-line tool",
        " cli tool", " tui app", "terminal app", "terminal tool",
    )
    return not any(word in description for word in runnable_words)


def candidates(gh: Github, kind: str, published: set[str]) -> list[dict]:
    low, high = BOUNDS[kind]
    seen: dict[str, dict] = {}
    for query in QUERIES[kind]:
        for repo in gh.search_repos(fill(query, kind), per_page=60):
            name = (repo.get("full_name") or "").lower()
            if not name or name in seen or name in published:
                continue
            if repo.get("archived") or repo.get("fork") or repo.get("is_template"):
                continue
            if not (low <= repo.get("stargazers_count", 0) <= high):
                continue
            if len((repo.get("description") or "").strip()) < 25:
                continue
            if looks_like_reading_material(repo):
                continue
            if kind_score(repo, kind) < 1:
                continue
            if not description_proves_kind(repo, kind):
                continue
            if looks_like_dependency(repo, kind):
                continue
            seen[name] = repo
    return list(seen.values())


def eligible(evidence: Evidence) -> bool:
    """Strict unattended-publication gate, intentionally favouring false negatives."""
    return (
        not evidence.archived
        and not evidence.docs_only
        and evidence.content_kind != "guide"
        and evidence.maturity == "proven"
        and (evidence.pushed_days_ago or 999) <= 21
        and (evidence.commits or 0) >= 100
        and (evidence.contributors or 0) >= 3
        and (evidence.releases or 0) >= 2
        and evidence.has_tests
        and evidence.has_ci
        and evidence.has_license
    )


def proposal(kind: str, evidence: Evidence) -> dict:
    return {
        "kind": kind,
        "repo": evidence.name,
        "suggested_slug": evidence.name.split("/")[-1].lower(),
        "upstream_description": evidence.description,
        "language": evidence.language,
        "topics": evidence.topics[:8],
        "stars": evidence.stars,
        "stars_per_day": evidence.stars_per_day,
        "age_days": evidence.age_days,
        "last_push_days": evidence.pushed_days_ago,
        "contributors": evidence.contributors,
        "releases": evidence.releases,
        "commits": evidence.commits,
        "has_tests": evidence.has_tests,
        "has_ci": evidence.has_ci,
        "has_license": evidence.has_license,
        "maturity": evidence.maturity,
        "url": evidence.url,
        # Editorial work still required before publication.
        "needs": ["pitch", "platforms", "categories", "traits", "install", "get_url"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=sorted(QUERIES))
    parser.add_argument("--limit", type=int, default=10, help="proposals per kind")
    args = parser.parse_args()

    catalog = json.loads(CATALOG.read_text())
    if AUTOMATIC.exists():
        catalog.extend(json.loads(AUTOMATIC.read_text()))
    published = {tool["repo"].lower() for tool in catalog}
    kinds = [args.kind] if args.kind else list(QUERIES)

    gh = Github()
    screened = 0
    proposals: list[dict] = []

    for kind in kinds:
        pool = candidates(gh, kind, published)
        screened += len(pool)
        with ThreadPoolExecutor(max_workers=6) as workers:
            collected = [e for e in workers.map(lambda r: collect(gh, r), pool) if e]
        passing = [e for e in collected if eligible(e)]
        passing.sort(key=lambda e: e.momentum, reverse=True)

        print(f"\n{kind}: {len(pool)} searched, {len(passing)} passed screening")
        for evidence in passing[: args.limit]:
            proposals.append(proposal(kind, evidence))
            print(
                f"  {evidence.name}  {evidence.stars} stars  "
                f"{evidence.age_days}d old  {evidence.contributors or '?'} authors  "
                f"[{evidence.maturity}]"
            )
            print(f"    {(evidence.description or '')[:100]}")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "screened": screened,
        "published_already": len(published),
        "proposals": proposals,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(
        f"\n{len(proposals)} proposals from {screened} screened repositories -> {OUTPUT}"
        f"\napi requests: {gh.requests}, cache hits: {gh.cache_hits}"
    )


if __name__ == "__main__":
    main()
