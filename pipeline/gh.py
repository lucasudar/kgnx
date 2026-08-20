"""Minimal GitHub REST client with an on-disk cache.

The cache exists because evidence collection costs four to five requests per
repository and rubric builds overlap heavily between runs.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.github.com"
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
CACHE_TTL = 6 * 3600


def token() -> str:
    env = os.environ.get("GITHUB_TOKEN")
    if env:
        return env
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit("No GitHub token: set GITHUB_TOKEN or run `gh auth login`.")


class Github:
    def __init__(self, auth: str | None = None, use_cache: bool = True) -> None:
        self.token = auth or token()
        self.use_cache = use_cache
        self.requests = 0
        self.cache_hits = 0
        CACHE_DIR.mkdir(exist_ok=True)

    def _cache_path(self, path: str) -> Path:
        key = re.sub(r"[^A-Za-z0-9]+", "_", path).strip("_")[:180]
        return CACHE_DIR / f"{key}.json"

    def _request(self, path: str, per_page: int | None = None):
        url = path if path.startswith("http") else f"{API}{path}"
        if per_page:
            url += ("&" if "?" in url else "?") + f"per_page={per_page}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
                "User-Agent": "stargaze-pipeline",
            },
        )
        for attempt in range(3):
            try:
                self.requests += 1
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.load(resp), resp.headers
            except urllib.error.HTTPError as err:
                if err.code == 404:
                    return None, {}
                # Secondary rate limits ask for a wait rather than a retry storm.
                if err.code in (403, 429) and attempt < 2:
                    time.sleep(int(err.headers.get("Retry-After", 5)))
                    continue
                return None, {}
            except (urllib.error.URLError, TimeoutError):
                if attempt < 2:
                    time.sleep(2)
                    continue
                return None, {}
        return None, {}

    def get(self, path: str, cache: bool = True):
        cache_file = self._cache_path(path)
        if self.use_cache and cache and cache_file.exists():
            if time.time() - cache_file.stat().st_mtime < CACHE_TTL:
                self.cache_hits += 1
                return json.loads(cache_file.read_text())
        data, _ = self._request(path)
        if self.use_cache and cache and data is not None:
            cache_file.write_text(json.dumps(data))
        return data

    def count(self, path: str, cache: bool = True) -> int | None:
        """Total items in a paginated collection, read from the last-page link."""
        cache_file = self._cache_path(f"count::{path}")
        if self.use_cache and cache and cache_file.exists():
            if time.time() - cache_file.stat().st_mtime < CACHE_TTL:
                self.cache_hits += 1
                return json.loads(cache_file.read_text())
        items, headers = self._request(path, per_page=1)
        if items is None:
            return None
        match = re.search(r'[?&]page=(\d+)>;\s*rel="last"', headers.get("Link", ""))
        total = int(match.group(1)) if match else (len(items) if isinstance(items, list) else None)
        if self.use_cache and cache and total is not None:
            cache_file.write_text(json.dumps(total))
        return total

    def search_repos(self, query: str, per_page: int = 50, sort: str = "stars") -> list[dict]:
        path = (
            "/search/repositories?q="
            + urllib.parse.quote(query)
            + f"&sort={sort}&order=desc&per_page={min(per_page, 100)}"
        )
        result = self.get(path)
        return result.get("items", []) if result else []
