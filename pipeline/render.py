"""Render the discovery PWA from the enriched tool catalogue.

    python3 -m pipeline.render

Cards ship in the HTML so pages stay indexable and readable without JavaScript.
A card answers "what is this and is it for me?"; everything else, including
install commands and maintenance evidence, lives in the detail view.
"""

from __future__ import annotations

import html
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "data" / "tools" / "feed.json"
CANDIDATES = ROOT / "data" / "candidates" / "candidates.json"
WEB = ROOT / "web"
SITE = ROOT / "site"

SITE_NAME = "kgnx"
TITLE = "Open-source tools worth using"
DESCRIPTION = (
    "Apps, command-line tools, self-hosted services, and extensions that are "
    "free, open source, and actually maintained."
)

FILTER_CATEGORIES = [
    "Productivity",
    "Terminal",
    "Developer tools",
    "Privacy",
    "Self-hosted",
    "Media",
    "System",
    "Automation",
]


def e(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def platform_summary(platforms: list[str]) -> str:
    desktop = [p for p in platforms if p in ("macOS", "Windows", "Linux")]
    if len(desktop) == 3 and len(platforms) == 3:
        return "macOS · Windows · Linux"
    if len(platforms) > 3:
        return " · ".join(platforms[:3]) + f" +{len(platforms) - 3}"
    return " · ".join(platforms)


def card(tool: dict) -> str:
    traits = "".join(f"<span>{e(trait)}</span>" for trait in tool["traits"])
    categories = " ".join(tool["categories"])
    platforms = " ".join(tool["platforms"])
    haystack = " ".join(
        [tool["name"], tool["pitch"], categories, platforms, tool["repo"], tool["kind"]]
    ).lower()
    automatic = (
        '<span class="automatic" title="Published by the strict automated pipeline">'
        "Auto-selected</span>"
        if tool.get("automated")
        else ""
    )

    return f"""<article class="tool" data-tool="{e(tool['slug'])}"
  data-tool-kind="{e(tool['kind'])}" data-platforms="{e(platforms.lower())}"
  data-categories="{e(categories.lower())}" data-haystack="{e(haystack)}"
  data-lifecycle="{e(tool['lifecycle']['status'])}" data-status="">
  <div class="tool-head">
    <span class="kind {e(tool['kind'])}">{e(tool['kind_label'])}</span>
    {automatic}
    <span class="runs-on">{e(platform_summary(tool['platforms']))}</span>
    <button class="dismiss" data-action="dismiss"
      aria-label="Hide {e(tool['name'])}" title="Not for me">×</button>
  </div>

  <h3 class="tool-name"><button data-open>{e(tool['name'])}</button></h3>
  <p class="pitch">{e(tool['pitch'])}</p>
  <div class="traits">{traits}</div>

  <div class="actions" role="group" aria-label="Actions for {e(tool['name'])}">
    <button class="action save" data-action="saved">Save</button>
    <button class="action try" data-action="try">Try next</button>
    <button class="action using" data-action="using">I use this</button>
  </div>

  <div class="tool-foot">
    <button class="details" data-open>Details</button>
    <a class="get" href="{e(tool['get_url'])}" target="_blank" rel="noopener">Project page ↗</a>
  </div>
</article>"""


def kind_chips(feed: dict) -> str:
    chips = [
        '<button class="chip active" data-kind="all" aria-pressed="true">'
        f'Everything <i>{feed["count"]}</i></button>'
    ]
    for kind in feed["kinds"]:
        chips.append(
            f'<button class="chip" data-kind="{e(kind["id"])}" aria-pressed="false">'
            f'{e(kind["label"])} <i>{kind["count"]}</i></button>'
        )
    return "".join(chips)


def category_chips(feed: dict) -> str:
    return "".join(
        f'<button class="chip" data-category="{e(category.lower())}" aria-pressed="false">'
        f"{e(category)}</button>"
        for category in FILTER_CATEGORIES
        if category in feed["categories"]
    )


def selection_section(feed: dict) -> str:
    """Explain where the catalogue comes from, since curation is the product."""
    screened = 0
    if CANDIDATES.exists():
        try:
            screened = json.loads(CANDIDATES.read_text()).get("screened", 0)
        except json.JSONDecodeError:
            screened = 0
    screened_line = (
        f"<li><b>{screened}</b> repositories screened automatically in the last run</li>"
        if screened
        else ""
    )

    return f"""<section class="method shell" id="how">
  <p class="eyebrow">How tools are chosen</p>
  <h2>Search finds candidates.<br>Strict evidence decides.</h2>
  <div class="method-grid">
    <article>
      <h3>1 · Search</h3>
      <p>A scheduled job queries the public GitHub API for maintained projects by
      topic, platform, and kind, then discards anything archived, inactive,
      undocumented, or not actually installable.</p>
    </article>
    <article>
      <h3>2 · Evidence</h3>
      <p>Each survivor is measured: last activity, releases, contributors, author
      concentration, tests, CI, and licence. Popularity is capped on purpose so
      that well-known projects cannot crowd out small useful ones.</p>
    </article>
    <article>
      <h3>3 · Publication</h3>
      <p>At most one unseen tool is published per day, rotating tool kinds. Its
      repository name and description stay authoritative; missing facts are
      shown as unknown. After 30 days it moves to Archive.</p>
    </article>
  </div>
  <ul class="method-facts">
    <li><b>{feed['count']}</b> tools currently published</li>
    <li><b>{feed.get('automatic_count', 0)}</b> published unattended</li>
    {screened_line}
    <li>Tests + CI + licence + 100 commits + 3 contributors + 2 releases required</li>
  </ul>
</section>"""


def page(feed: dict) -> str:
    cards = "\n".join(card(tool) for tool in feed["tools"])
    generated = feed["generated_at"].replace("T", " ").replace("+00:00", " UTC")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(SITE_NAME)} — {e(TITLE)}</title>
  <meta name="description" content="{e(DESCRIPTION)}">
  <meta property="og:title" content="{e(TITLE)}">
  <meta property="og:description" content="{e(DESCRIPTION)}">
  <meta property="og:type" content="website">
  <link rel="icon" href="icon.svg" type="image/svg+xml">
  <link rel="manifest" href="manifest.webmanifest">
  <meta name="theme-color" content="#f6f4ef">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header">
    <div class="shell header-inner">
      <a class="brand" href="./" aria-label="{e(SITE_NAME)} home">
        <span class="brand-mark">k</span><span>{e(SITE_NAME)}</span>
      </a>
      <nav class="desktop-nav" aria-label="Your lists">
        <button data-view="discover" class="nav-item active">Discover</button>
        <button data-view="saved" class="nav-item">Saved <span data-count="saved"></span></button>
        <button data-view="try" class="nav-item">Try next <span data-count="try"></span></button>
        <button data-view="using" class="nav-item">Using <span data-count="using"></span></button>
        <button data-view="archive" class="nav-item">Archive <span>{feed['archive_count'] or ''}</span></button>
      </nav>
      <button class="profile-button" data-profile>
        <span class="profile-dot"></span>
        <span class="profile-copy"><b>Local profile</b><small>on this device</small></span>
      </button>
    </div>
  </header>

  <main>
    <section class="hero shell">
      <p class="eyebrow">Known good. Try next.</p>
      <h1>Open-source tools<br><em>worth using.</em></h1>
      <p class="lede">{e(DESCRIPTION)}</p>
      <p class="hero-links"><a href="#how">How tools are chosen ↓</a></p>
    </section>

    <section class="controls shell" aria-label="Filter the catalogue">
      <div class="row kinds">{kind_chips(feed)}</div>
      <div class="row secondary">
        <div class="platforms">
          <button class="chip active" data-platform="all" aria-pressed="true">Any platform</button>
          <button class="chip" data-platform="macos" aria-pressed="false">macOS</button>
          <button class="chip" data-platform="windows" aria-pressed="false">Windows</button>
          <button class="chip" data-platform="linux" aria-pressed="false">Linux</button>
          <button class="chip" data-platform="ios android" aria-pressed="false">Mobile</button>
          <button class="chip" data-platform="self-hosted docker" aria-pressed="false">Server</button>
        </div>
        <label class="search">
          <span aria-hidden="true">⌕</span>
          <input data-search type="search" placeholder="Search by name, purpose, platform">
        </label>
      </div>
      <div class="row categories">{category_chips(feed)}</div>
    </section>

    <section class="feed shell">
      <div class="feed-head">
        <div>
          <p class="eyebrow" data-view-eyebrow>Discover</p>
          <h2 data-view-title>Worth a look</h2>
        </div>
        <p class="summary" data-summary></p>
      </div>
      <div class="grid" data-grid>{cards}</div>
      <div class="empty" data-empty hidden>
        <h3>Nothing here yet</h3>
        <p data-empty-copy>Try another filter.</p>
        <button data-clear>Clear filters</button>
      </div>
    </section>

    {selection_section(feed)}
  </main>

  <nav class="mobile-nav" aria-label="Your lists">
    <button data-view="discover" class="active"><span>⌕</span>Discover</button>
    <button data-view="saved"><span>♡</span>Saved<i data-count="saved"></i></button>
    <button data-view="try"><span>＋</span>Try<i data-count="try"></i></button>
    <button data-view="using"><span>✓</span>Using<i data-count="using"></i></button>
    <button data-view="archive"><span>↶</span>Archive</button>
  </nav>

  <dialog class="detail" data-detail>
    <button class="dialog-close" data-dialog-close aria-label="Close">×</button>
    <div data-detail-body></div>
  </dialog>

  <dialog class="profile-dialog" data-profile-dialog>
    <button class="dialog-close" data-dialog-close aria-label="Close">×</button>
    <p class="eyebrow">Your profile</p>
    <h2>Private by default.</h2>
    <p>Save, Try next, and Using are stored only in this browser. No account, no
    activity sent to a server.</p>
    <div class="profile-stats">
      <span><b data-count="saved">0</b> saved</span>
      <span><b data-count="try">0</b> to try</span>
      <span><b data-count="using">0</b> using</span>
    </div>
    <div class="future-sync">
      <span>Next</span>
      <div><b>GitHub sync</b><p>Continue on another device, and star a repository as a separate deliberate action.</p></div>
    </div>
    <button class="export-button" data-export>Export my list</button>
    <small>Your data leaves the browser only when you export it.</small>
  </dialog>

  <div class="toast" data-toast role="status" aria-live="polite"></div>
  <footer><div class="shell">Updated {e(generated)} · {feed['count']} tools ·
    evidence from the public GitHub API</div></footer>
  <script src="app.js" defer></script>
</body>
</html>
"""


def main() -> None:
    if not FEED.exists():
        raise SystemExit("No catalogue. Run `python3 -m pipeline.catalog` first.")
    feed = json.loads(FEED.read_text())

    SITE.mkdir(exist_ok=True)
    for stale in SITE.glob("*.html"):
        stale.unlink()
    for asset in (
        "styles.css",
        "app.js",
        "sw.js",
        "manifest.webmanifest",
        "icon.svg",
        "CNAME",
    ):
        shutil.copy2(WEB / asset, SITE / asset)
    # The detail view fetches this lazily instead of inlining every field.
    shutil.copy2(FEED, SITE / "tools.json")
    (SITE / "index.html").write_text(page(feed))

    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{stamp}] rendered {feed['count']} tools -> {SITE / 'index.html'}")


if __name__ == "__main__":
    main()
