"""Turn a repository into adoption evidence.

The product promise is that a card answers "can I bet on this?" instead of
"how many stars does it have?". Every field here must be defensible to a
sceptical reader and cheap enough to compute for thousands of repositories.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from .gh import Github

MANIFESTS = {
    "package.json", "pnpm-workspace.yaml", "deno.json", "pyproject.toml",
    "setup.py", "requirements.txt", "cargo.toml", "go.mod", "pom.xml",
    "build.gradle", "build.gradle.kts", "gemfile", "composer.json",
    "cmakelists.txt", "makefile", "dockerfile", "mix.exs", "pubspec.yaml",
    "build.zig", "package.swift", "gleam.toml", "gradlew",
}
TEST_DIRS = {"test", "tests", "spec", "specs", "__tests__", "e2e", "testing"}
DOC_LANGS = {"markdown", "html", "css", "text", "mdx"}

# Reading material rather than software. Useful, but it does not belong in a
# rubric that promises tools you can depend on.
GUIDE_WORDS = (
    "awesome", "cheatsheet", "cheat-sheet", "ultimate guide", "the guide",
    "tutorial", "handbook", "roadmap", "curated", "list of", "resources",
    "interview questions", "study notes", "papers", "e-book", "ebook",
    "learning path", "bootcamp", "course",
)


def _days_since(stamp: str | None) -> int | None:
    if not stamp:
        return None
    moment = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    return max((datetime.now(timezone.utc) - moment).days, 0)


@dataclass
class Badge:
    kind: str  # "good" | "warn"
    text: str


@dataclass
class Evidence:
    name: str
    url: str
    description: str = ""
    language: str | None = None
    topics: list[str] = field(default_factory=list)
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    age_days: int = 0
    pushed_days_ago: int | None = None
    stars_per_day: float = 0.0
    commits: int | None = None
    contributors: int | None = None
    top_author_share: float | None = None
    releases: int | None = None
    latest_release_days: int | None = None
    has_manifest: bool = False
    has_tests: bool = False
    has_ci: bool = False
    has_license: bool = False
    archived: bool = False
    is_fork: bool = False
    docs_only: bool = False
    content_kind: str = "project"  # "project" | "guide"
    maturity: str = "unknown"
    badges: list[Badge] = field(default_factory=list)
    momentum: float = 0.0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["badges"] = [asdict(b) for b in self.badges]
        return data


def collect(gh: Github, repo: dict) -> Evidence | None:
    """Build evidence from a search/repo payload plus a few extra calls."""
    name = repo.get("full_name")
    if not name:
        return None

    ev = Evidence(
        name=name,
        url=repo.get("html_url", f"https://github.com/{name}"),
        description=(repo.get("description") or "").strip(),
        language=repo.get("language"),
        topics=repo.get("topics") or [],
        stars=repo.get("stargazers_count", 0),
        forks=repo.get("forks_count", 0),
        open_issues=repo.get("open_issues_count", 0),
        archived=bool(repo.get("archived")),
        is_fork=bool(repo.get("fork")),
        has_license=bool(repo.get("license")),
    )
    ev.age_days = _days_since(repo.get("created_at")) or 1
    ev.pushed_days_ago = _days_since(repo.get("pushed_at"))
    ev.stars_per_day = round(ev.stars / max(ev.age_days, 1), 2)

    root = gh.get(f"/repos/{name}/contents")
    entries = {e["name"].lower(): e["type"] for e in root} if isinstance(root, list) else {}
    ev.has_manifest = any(f in MANIFESTS for f in entries)
    ev.has_tests = any(
        n in TEST_DIRS or n.split(".")[0] in TEST_DIRS or n.startswith("test_")
        for n in entries
    )
    ev.has_ci = ".github" in entries
    ev.docs_only = (
        (ev.language or "").lower() in DOC_LANGS or ev.language is None
    ) and not ev.has_manifest

    haystack = " ".join(
        [name.split("/")[-1], ev.description, " ".join(ev.topics)]
    ).lower().replace("_", " ").replace("-", " ")
    ev.content_kind = (
        "guide" if any(w.replace("-", " ") in haystack for w in GUIDE_WORDS) else "project"
    )

    ev.commits = gh.count(f"/repos/{name}/commits")
    ev.contributors = gh.count(f"/repos/{name}/contributors")
    ev.releases = gh.count(f"/repos/{name}/releases")

    top = gh.get(f"/repos/{name}/contributors?per_page=10")
    if isinstance(top, list) and top:
        lead = top[0].get("contributions", 0)
        # Prefer the true commit total; the top-10 sum inflates the share on
        # repositories with a long contributor tail.
        total = max(ev.commits or 0, sum(c.get("contributions", 0) for c in top), 1)
        ev.top_author_share = round(lead / total, 2)

    latest = gh.get(f"/repos/{name}/releases/latest")
    if isinstance(latest, dict):
        ev.latest_release_days = _days_since(latest.get("published_at"))

    _judge(ev)
    return ev


def _judge(ev: Evidence) -> None:
    """Assign badges, a maturity verdict, and a momentum figure."""
    good, warn = [], []

    if ev.pushed_days_ago is not None:
        if ev.pushed_days_ago <= 7:
            good.append(Badge("good", "active this week"))
        elif ev.pushed_days_ago > 180:
            warn.append(Badge("warn", f"no commits for {ev.pushed_days_ago} days"))
    if ev.archived:
        warn.append(Badge("warn", "archived by its owner"))

    if ev.contributors is not None:
        if ev.contributors <= 1:
            warn.append(Badge("warn", "single contributor"))
        elif ev.contributors >= 20:
            good.append(Badge("good", f"{ev.contributors} contributors"))
    if ev.top_author_share is not None and ev.top_author_share >= 0.95 and (ev.contributors or 0) > 1:
        share = round(ev.top_author_share * 100)
        warn.append(Badge("warn", f"top author wrote {share}% of commits"))

    if ev.has_tests:
        good.append(Badge("good", "has tests"))
    else:
        warn.append(Badge("warn", "no tests"))
    if ev.has_ci:
        good.append(Badge("good", "CI configured"))
    if ev.releases:
        good.append(Badge("good", f"{ev.releases} releases"))
    else:
        warn.append(Badge("warn", "no releases"))
    if not ev.has_license:
        warn.append(Badge("warn", "no licence"))
    if ev.docs_only:
        warn.append(Badge("warn", "documentation only, no code"))
    if ev.content_kind == "guide":
        warn.append(Badge("warn", "reading material, not a tool"))
    if ev.commits is not None and ev.commits <= 10:
        warn.append(Badge("warn", f"only {ev.commits} commits"))

    if ev.age_days <= 30:
        good.append(Badge("good", f"{ev.age_days} days old"))
    if ev.stars_per_day >= 5:
        good.append(Badge("good", f"{ev.stars_per_day} stars/day"))

    ev.badges = good + warn

    # Maturity is deliberately coarse: three buckets a reader can act on.
    depth = sum(
        [
            ev.has_tests,
            ev.has_ci,
            bool(ev.releases),
            ev.has_license,
            (ev.contributors or 0) >= 5,
            (ev.commits or 0) >= 100,
        ]
    )
    alive = not ev.archived and (ev.pushed_days_ago or 999) <= 90
    if not alive or ev.docs_only:
        ev.maturity = "risky"
    elif depth >= 5:
        ev.maturity = "proven"
    elif depth >= 3:
        ev.maturity = "promising"
    else:
        ev.maturity = "risky"

    # Momentum favours recent traction and recent work, not absolute size.
    recency = 1.0 / (1 + (ev.pushed_days_ago or 30) / 14)
    ev.momentum = round(math.log10(1 + ev.stars_per_day * 10) * recency, 3)
