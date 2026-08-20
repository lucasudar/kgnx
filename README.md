# kgnx

**Known good. Try next.**

Discover useful open-source tools you can start using today, save them on your
phone, and install them later from your computer.

A catalogue entry is anything usable, not only a desktop application:

| Kind | Examples |
| --- | --- |
| App | VoiceInk, Maccy, Ice, Zed |
| Command line | ripgrep, fzf, lazygit, restic |
| Self-hosted | Immich, Vaultwarden, Paperless-ngx |
| Browser extension | uBlock Origin, Dark Reader |

> Status: working local-first vertical slice. `kgnx` is the working product name
> inspired by the available `kgnx.nx.kg` domain; naming is not final.

## Product thesis

People do not want repositories. They want a clipboard manager, local meeting
transcription, better window management, or a trustworthy replacement for a
subscription.

GitHub is evidence, not the product:

- the card leads with the outcome, the kind of tool, platforms, and the real
  install command where one exists;
- no invented artwork: if a tool has no genuine icon, none is drawn;
- Save, Try next, and I use this create a useful personal workflow;
- maintenance evidence is available under **Why trust it?**;
- browsing and local personalisation require no account;
- GitHub authentication later adds cross-device sync and an optional, separate
  Star action.

The initial wedge is technical users looking for free and open-source tools they
probably missed, starting from macOS but not limited to it.

## Run everything

Requires Python 3 and an authenticated GitHub CLI (`gh auth login`).

```bash
./run-everything.sh
```

This refreshes GitHub evidence, builds the catalogue, renders the PWA, and serves
it at <http://127.0.0.1:8787>. If the server already exists, it reuses it.

Individual stages:

```bash
python3 -m pipeline.discover --limit 8   # search GitHub for new candidates
python3 -m pipeline.autopublish          # publish at most one strict candidate
python3 -m pipeline.lifecycle            # expire 30-day publication windows
python3 -m pipeline.catalog              # refresh evidence for published tools
python3 -m pipeline.render               # build the static site
python3 -m http.server 8787 --directory site
```

`./run-everything.sh --discover` includes the search step.

The scheduled GitHub Action runs the same sequence once per day, commits the
generated JSON and site directly, deploys Pages, and optionally posts the new
tool to Telegram. No pull request or approval queue is involved.

## How selection works

Search proposes, strict evidence gates decide, and one tool is published per day.

1. `pipeline/discover.py` queries the public GitHub API per kind (macOS and
   desktop app topics, CLI and TUI topics, self-hosted and homelab topics,
   browser-extension topics), bounded by star range and recent activity.
2. Candidates are rejected when archived, forked, templated, unsafe by policy,
   thinly described, or when their own description does not prove that they are
   a runnable tool of the claimed kind.
3. Unattended publication additionally requires: activity within 21 days,
   `proven` maturity, at least 100 commits, 3 contributors, 2 releases, tests,
   CI, and a detected licence.
4. `pipeline.autopublish` rotates through kinds and publishes no more than one
   unseen candidate per UTC day. Unknown facts are displayed as unknown; they
   are never invented.
5. The tool remains current for 30 days and then moves to Archive automatically.

The latest strict run screened 215 repositories and produced 34 eligible
proposals. The full candidate and publication JSON remains committed for audit.

## What exists

- 59 tools: 58 initial selections plus one strict automatic publication;
- a detail view per tool: upstream description, full maintenance evidence,
  topics, install command, and links;
- responsive discovery UI with phone bottom navigation;
- kind, platform, category, and text filters with a visible active-filter
  summary and a clear button;
- daily automatic discovery, strict publication, and 30-day archive rotation;
- local Save / Try next / I use this / Not for me state;
- separate Saved, Try next, and Using views;
- JSON export;
- progressive static HTML, PWA manifest, and offline service worker;
- GitHub evidence hidden behind a human-readable trust disclosure;
- no backend, account, token in the browser, or telemetry.

## Repository map

```text
data/catalog/tools.json  initial catalogue
data/catalog/automatic.json  unattended publications
data/tools/feed.json     generated catalogue + GitHub evidence
data/candidates/         candidates and daily publication report
pipeline/discover.py     GitHub Search candidate generation
pipeline/autopublish.py  strict daily selection
pipeline/lifecycle.py    current/archive rotation
pipeline/catalog.py      catalogue enrichment
pipeline/telegram.py     optional one-tool Telegram announcement
pipeline/gh.py           cached GitHub REST client
pipeline/evidence.py     explainable trust signals
pipeline/render.py       static PWA renderer
web/                     source assets and local state client
site/                    deployable generated output
docs/PRODUCT.md          product loop and content policy
docs/ARCHITECTURE.md     current and authenticated architecture
```

The earlier repository-rubric experiment was replaced by `pipeline/discover.py`,
which applies the same search-and-evidence approach to tool candidates instead
of raw repositories. `research/slop_probe.py` remains as the measurement that
rejected the AI-filler premise.

## Telegram

Create a channel, add a bot as an administrator, then add two repository
secrets:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

The daily workflow posts only when `autopublish` added a new tool. Missing
secrets simply disable Telegram; they never fail catalogue publication.

## Next architecture stage

Anonymous state remains local. When cross-device use is implemented:

- GitHub App OAuth with PKCE through a Cloudflare Worker BFF;
- encrypted GitHub token on the server, opaque HttpOnly session in the browser;
- D1 tables for user app state and preferences;
- timestamp-based merge of existing local state on first sign-in;
- GitHub Star as an explicit external action, never an automatic side effect of
  Save.

The public catalogue and SEO pages remain static and cacheable.

## Documents

- [Product brief](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Market and research](docs/RESEARCH.md)
- [GitHub API constraints](docs/GITHUB_API.md)
- [Roadmap](docs/ROADMAP.md)
- [Hosting](docs/HOSTING.md)
