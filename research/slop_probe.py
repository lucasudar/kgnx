"""Measure how much of GitHub Trending is substance versus filler.

Trending is fetched through a local FlareSolverr instance because GitHub has no
official trending API. Repository evidence comes from the authenticated REST API
using the token from `gh auth token`.

Usage:
    python3 research/slop_probe.py --since daily
    python3 research/slop_probe.py --since weekly --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone

FLARESOLVERR = "http://192.168.1.202:8191/v1"
API = "https://api.github.com"

# Root-level files that indicate a real, buildable project rather than a
# collection of markdown.
MANIFESTS = {
    "package.json", "pnpm-workspace.yaml", "deno.json", "bun.lockb",
    "pyproject.toml", "setup.py", "requirements.txt", "cargo.toml",
    "go.mod", "pom.xml", "build.gradle", "build.gradle.kts", "gemfile",
    "composer.json", "cmakelists.txt", "makefile", "dockerfile",
    "mix.exs", "pubspec.yaml", "build.zig", "package.swift", "gleam.toml",
}
TEST_HINTS = ("test", "tests", "spec", "specs", "__tests__", "e2e")
SRC_HINTS = ("src", "lib", "cmd", "pkg", "app", "internal", "core")
LIST_WORDS = (
    "awesome", "skills", "skill", "prompt", "prompts", "cheatsheet",
    "cheat-sheet", "resources", "collection", "curated", "list of",
    "roadmap", "interview", "tutorials", "handbook", "guide", "notes",
    "papers", "books", "wiki", "directory", "index of", "templates",
)
DOC_LANGS = {None, "markdown", "html", "css", "text", "mdx", "jupyter notebook"}


def gh_token() -> str:
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit("Could not read a GitHub token from `gh auth token`.")


def fetch_trending(since: str) -> list[str]:
    payload = json.dumps(
        {
            "cmd": "request.get",
            "url": f"https://github.com/trending?since={since}",
            "maxTimeout": 60000,
        }
    ).encode()
    req = urllib.request.Request(
        FLARESOLVERR, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        body = json.load(resp)
    html = body["solution"]["response"]
    # The repository title on the trending page is the only <h2> anchor.
    names = re.findall(r'<h2[^>]*>\s*<a[^>]*href="/([^"?#]+)"', html)
    seen: list[str] = []
    for name in names:
        if name.count("/") == 1 and name not in seen:
            seen.append(name)
    return seen


class Api:
    def __init__(self, token: str) -> None:
        self.token = token

    def _open(self, path: str, per_page: int | None = None):
        url = path if path.startswith("http") else f"{API}{path}"
        if per_page:
            url += ("&" if "?" in url else "?") + f"per_page={per_page}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
                "User-Agent": "slop-probe",
            },
        )
        return urllib.request.urlopen(req, timeout=30)

    def get(self, path: str):
        try:
            with self._open(path) as resp:
                return json.load(resp)
        except urllib.error.HTTPError:
            return None

    def count(self, path: str) -> int | None:
        """Total items in a paginated collection, via the last-page link."""
        try:
            with self._open(path, per_page=1) as resp:
                link = resp.headers.get("Link", "")
                items = json.load(resp)
        except urllib.error.HTTPError:
            return None
        match = re.search(r'[?&]page=(\d+)>;\s*rel="last"', link)
        if match:
            return int(match.group(1))
        return len(items) if isinstance(items, list) else None


@dataclass
class Verdict:
    name: str
    stars: int = 0
    language: str | None = None
    age_days: int = 0
    stars_per_day: float = 0.0
    commits: int | None = None
    contributors: int | None = None
    releases: int | None = None
    has_manifest: bool = False
    has_tests: bool = False
    has_ci: bool = False
    has_license: bool = False
    archived: bool = False
    doc_only: bool = False
    list_like: bool = False
    score: int = 0
    reasons: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.score >= 60:
            return "filler"
        if self.score >= 30:
            return "thin"
        return "substance"


def assess(api: Api, name: str) -> Verdict | None:
    repo = api.get(f"/repos/{name}")
    if not repo:
        return None

    v = Verdict(name=name)
    v.stars = repo.get("stargazers_count", 0)
    v.language = repo.get("language")
    v.archived = bool(repo.get("archived"))
    v.has_license = bool(repo.get("license"))

    created = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
    v.age_days = max((datetime.now(timezone.utc) - created).days, 1)
    v.stars_per_day = round(v.stars / v.age_days, 1)

    root = api.get(f"/repos/{name}/contents") or []
    entries = {e["name"].lower(): e["type"] for e in root} if isinstance(root, list) else {}
    v.has_manifest = any(f in MANIFESTS for f in entries)
    v.has_tests = any(
        n.startswith(TEST_HINTS) or n.split(".")[0] in TEST_HINTS for n in entries
    )
    v.has_ci = ".github" in entries
    has_src = any(n in SRC_HINTS and t == "dir" for n, t in entries.items())

    v.commits = api.count(f"/repos/{name}/commits")
    v.contributors = api.count(f"/repos/{name}/contributors")
    v.releases = api.count(f"/repos/{name}/releases")

    text = " ".join(
        [name, repo.get("description") or "", " ".join(repo.get("topics") or [])]
    ).lower()
    v.list_like = any(w in text for w in LIST_WORDS)
    v.doc_only = (v.language or "").lower() in {l for l in DOC_LANGS if l} or v.language is None

    # Scoring: each signal is evidence about substance, and every point is
    # explainable to a human on the card.
    if v.doc_only and not v.has_manifest and not has_src:
        v.score += 40
        v.reasons.append("no code: docs/markdown only, no manifest or source dir")
    if v.list_like and not v.has_manifest:
        v.score += 20
        v.reasons.append("reads as a curated list / prompt collection")
    if not v.has_tests:
        v.score += 12
        v.reasons.append("no tests at root")
    if not v.has_ci:
        v.score += 8
        v.reasons.append("no CI configuration")
    if v.commits is not None and v.commits <= 5:
        v.score += 15
        v.reasons.append(f"only {v.commits} commit(s)")
    if v.contributors is not None and v.contributors <= 1:
        v.score += 10
        v.reasons.append("single contributor")
    if not v.releases:
        v.score += 5
        v.reasons.append("no releases")
    if not v.has_license:
        v.score += 5
        v.reasons.append("no license")
    if v.age_days <= 30 and v.stars_per_day >= 300:
        v.score += 15
        v.reasons.append(
            f"star spike: {v.stars_per_day}/day over {v.age_days} days"
        )
    if v.archived:
        v.score += 20
        v.reasons.append("archived")

    v.score = min(v.score, 100)
    return v


def search_repos(api: "Api", query: str, limit: int) -> list[str]:
    result = api.get(
        "/search/repositories?q="
        + urllib.parse.quote(query)
        + f"&sort=stars&order=desc&per_page={limit}"
    )
    if not result:
        return []
    return [item["full_name"] for item in result.get("items", [])]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default="daily", choices=["daily", "weekly", "monthly"])
    parser.add_argument("--search", help="use GitHub search instead of trending")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--json", dest="json_out")
    args = parser.parse_args()

    api = Api(gh_token())

    if args.search:
        names = search_repos(api, args.search, args.limit)
        if not names:
            sys.exit("Search returned no repositories.")
        print(f"GitHub Search ({args.search}): {len(names)} repositories\n")
    else:
        names = fetch_trending(args.since)
        if not names:
            sys.exit("Trending page returned no repositories.")
        print(f"GitHub Trending ({args.since}): {len(names)} repositories\n")
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = [v for v in pool.map(lambda n: assess(api, n), names) if v]

    results.sort(key=lambda v: v.score, reverse=True)
    for v in results:
        head = f"{v.score:3d}  {v.label:9s}  {v.name}"
        meta = f"{v.stars}★  {v.language or 'no language'}  {v.age_days}d"
        print(f"{head}\n     {meta}")
        for reason in v.reasons:
            print(f"       - {reason}")
        print()

    total = len(results)
    buckets = {"filler": 0, "thin": 0, "substance": 0}
    for v in results:
        buckets[v.label] += 1

    def pct(n: int) -> str:
        return f"{n}/{total} ({round(100 * n / total)}%)"

    print("summary")
    print(f"  filler     {pct(buckets['filler'])}")
    print(f"  thin       {pct(buckets['thin'])}")
    print(f"  substance  {pct(buckets['substance'])}")
    print(f"  no tests   {pct(sum(1 for v in results if not v.has_tests))}")
    print(f"  no code    {pct(sum(1 for v in results if v.doc_only and not v.has_manifest))}")
    print(f"  list-like  {pct(sum(1 for v in results if v.list_like))}")
    print(f"  1 author   {pct(sum(1 for v in results if (v.contributors or 0) <= 1))}")

    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump([v.__dict__ for v in results], fh, indent=2)
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
