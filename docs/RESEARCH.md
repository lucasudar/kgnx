# Market and competitor research

Research date: 2026-08-19.

## Executive summary

The broad idea is validated but not empty:

- Tinder-style GitHub discovery already exists on web, PWA, Android, and iOS.
- Personalized feeds, real GitHub starring, and swipe learning are already
  marketed by `Fork it`.
- Cleanup of stale and archived stars is already sold by `Stargazer`.
- Semantic search, AI categorization, release tracking, similar-repository
  recommendations, and local-first storage all have existing products.
- `Stargaze` is already used by several products in this exact category.

Therefore, “swipe repositories” is not a defensible product by itself. The
credible opening is a polished cross-platform workflow joining safe star
review, rediscovery, a capped “try next” queue, and small explainable discovery
decks.

## Direct competitors

| Product | Platform / stack | What it already does | Evidence of traction | Gap relevant to us |
|---|---|---|---|---|
| [Fork it](https://forkit.tech/) | Android-first, iPhone PWA, web; backend OAuth | Interest onboarding, swipe discovery, real stars, ranker learns from swipes, streaks | Public product and polished landing page | Focuses on acquiring new stars, not reviewing and activating an existing library |
| [_gitinder](https://github.com/Osman-Kahraman/_gitinder) | Native SwiftUI iOS | OAuth, swipe discovery, star/skip, repository metadata | 31 stars, 4 forks; last observed push 2026-05 | Narrow discovery demo; no cleanup or durable workflow |
| [GitHub-RepoSwipe](https://github.com/mytricker0/Github-RepoSwipe) | Expo / mobile / web | Trending and filtered deck, real star/unstar, no backend, Device Flow | 2 stars; last observed push 2026-04 | Weak traction; authentication approach is not recommended for public web SPAs |
| [GitMatch](https://github.com/sharf-shawon/GitMatch) | React/Vite, Firebase, Gemini | Swipe discovery, learned preferences, collections | 1 star when researched | Similar mechanics without evidence of retention |
| [Stargaze swipe deck](https://github.com/masonwyatt23/stargaze) | Next.js, Supabase | Swipe indie projects, auto-star, saves, leaderboard, creator pages | Overlaps in name and mechanics | Creator-promotion orientation rather than personal star hygiene |
| [Stargazer](https://stargazer.dev/) | Native macOS, local-first | AI organization, stale/archive cleanup, search, code browsing, repo chat, releases, snapshots, similar stars | Commercial beta; $49 launch / $79 lifetime pricing | Mac-only today and feature-heavy; opportunity for lighter web/mobile ritual |

## Adjacent competitors

| Product | Category | Relevant capability |
|---|---|---|
| [SimRepo](https://github.com/Mubelotix/SimRepo) | Browser extension | Similar repositories and personalized home recommendations using server-side Qdrant and embeddings trained from 300M+ stars |
| [GitRec](https://github.com/gorse-io/gitrec) | Recommender | Personalized and related GitHub repositories using Gorse |
| [github-star-manager](https://github.com/cosformula/github-star-manager) | CLI | AI categories, conservative unstar suggestions, backup and restore |
| [starman](https://github.com/morehao/starman) | CLI/TUI | Local SQLite sync, AI analysis, embeddings, search, categories, backup |
| [Stargaze CLI](https://crates.io/crates/stargaze) | Rust CLI/MCP | Local cache, README search, local semantic embeddings, MCP server |
| [Stargaze graph](https://github.com/ervinismu/stargaze) | Browser visualization | Client-only topic graph of a user's stars |
| [Stargaze browser](https://github.com/andreasphil/stargaze) | Web | Faster browsing and filtering of GitHub stars |
| [Astral](https://astralapp.com/) | Hosted/self-host library | Import, tags, notes, search. 3,567 GitHub stars; no swipe or recs |
| [GithubStarsManager](https://github.com/AmintaCCCP/GithubStarsManager) | Web/Electron | AI tag/search, release tracking. 3,377 stars, actively shipping |
| [GitTok](https://gittok.dev/) | Vertical-scroll discovery | Trending/curated README feed; not a personal ranker |
| [RepoPulse](https://github.com/ddfriday/repo-pulse) | Trending analytics | Periodic repository snapshots and explainable momentum ranking |
| [Trendshift](https://trendshift.io/) | Discovery | Independent live momentum rankings |

## Naming assessment

`Stargaze` should not be used as the launch name:

- multiple GitHub-star tools already use it;
- one existing project explicitly describes itself as a swipe deck;
- another caches and semantically searches GitHub stars;
- another browses starred repositories;
- the well-known Stargaze blockchain creates additional search confusion;
- `Stargazer` is an active paid star-management product.

This is not a formal trademark opinion, but it is enough to reject the name for
brand discoverability. Keep it only as a local codename until naming research.

## Demand evidence

Hacker News discussions repeatedly show that developers use stars as bookmarks,
often accumulating more than a thousand and losing the ability to retrieve or
review them:

- [Discussion: stars as bookmarks and limits of GitHub Lists](https://news.ycombinator.com/item?id=43965696)
- [Discussion: stars as bookmarks rather than endorsements](https://news.ycombinator.com/item?id=42540182)
- [Show HN: semantic search over stars](https://news.ycombinator.com/item?id=42427802)
- [Show HN: cleanup of old forks and stars](https://news.ycombinator.com/item?id=24207672)

The pain is real. Historical launches often receive little attention, which
also shows that “better star manager” alone does not guarantee distribution.
The product needs exceptional interaction design and a shareable result.

## Strategic whitespace

Potential differentiation worth validating:

1. **Review as a finite ritual:** a daily/weekly deck that ends, rather than
   another permanent dashboard.
2. **A real action queue:** “try next” is capped and revisited; it is not another
   unlimited collection.
3. **Review history:** remember why a star was kept and when it was last checked.
4. **Evidence cards:** concise health, movement, release, license, and maintenance
   signals without an LLM-generated wall of text.
5. **Safe mutation:** staged unstars, preview, undo, backup/export, and respectful
   GitHub rate handling.
6. **Closed loop:** retained and attempted repositories improve future decks.
7. **Cross-platform delivery:** phone-friendly PWA with an information-dense
   desktop detail view.
8. **Shareable outcome:** privacy-safe “Star Wrapped” showing categories and
   cleanup results without exposing private repository names.

## Risks

- A swipe interface may be entertaining only once.
- Existing competitors can copy interaction mechanics quickly.
- GitHub API policy changes can invalidate graph-based ranking.
- Health signals can mislabel mature but stable libraries as abandoned.
- Unstarring is destructive from the user's perspective and demands trust.
- A recommendation product can become a popularity amplifier or spam channel.
- GitHub stars include private repositories when permissions allow; accidental
  upload or sharing would be a severe privacy failure.
- The launch name currently collides with direct competitors.

## Research method and limitation

Sources included official GitHub documentation and changelog entries, live
product pages, GitHub repository metadata, web search, and direct page fetching.

FlareSolverr 3.5.0 was later found on Proxmox CT 102 (`media-arr`) at
`http://192.168.1.202:8191` and used to fetch GitHub Trending and Product Hunt.
Extra adjacent products seen there: StarLens (AI roast/insights of stars),
Bookmarkjar (generic AI bookmarks including GitHub stars), StarDash (AI
organization + Discover search). None replace a swipe discovery + try-next loop.
FlareSolverr is research-only and must not become a runtime dependency.

## Measured test: is GitHub full of AI-generated filler? (2026-08-19)

A proposed differentiator was filtering AI-generated, substance-free repositories.
`research/slop_probe.py` tested it against live data by scoring repositories on
code presence, manifests, tests, CI, commit depth, contributor count, releases,
licence, and star-velocity anomalies. Three samples, 73 repositories:

| Sample | filler | thin | substance | no tests | single author |
| --- | --- | --- | --- | --- | --- |
| Trending, daily (13) | 0% | 8% | 92% | 23% | 0% |
| Fresh `mcp`, >30 stars (30) | 0% | 20% | 80% | 50% | 30% |
| Fresh `mcp`, 0–5 stars (30) | 7% | 23% | 70% | 27% | 83% |

**The premise failed.** Even the unfiltered long tail is mostly real code with
real commit history. Trending repositories averaged hundreds to thousands of
commits and dozens to hundreds of contributors. Anti-filler scoring is hygiene,
not a moat, and a simple star floor already removes most of what it would catch.

Two findings did survive and are more useful:

1. **Coverage, not noise, is the gap.** Trending returned only 13 repositories,
   dominated by mature giants (`immich` at 1658 days old, `nautilus_trader` at
   2977 days). Search surfaced genuinely new projects with real momentum that no
   curated list carries at the moment they matter, e.g. 598 stars in 44 days,
   489 stars in 3 days. The mid-tail is uncovered.
2. **Maturity signals are absent everywhere, and half the fresh popular
   repositories lack them.** 50% of fresh repositories above 30 stars had no
   tests and 30% had a single contributor. Competitors show stars; nobody shows
   "one author, no tests, three days old" next to the star count, which is the
   information an adopter actually needs.

Pipeline cost is confirmed cheap: roughly four REST calls per repository, 73
repositories scored in about 14 seconds per sample, far inside the 5000/hour
authenticated limit.
