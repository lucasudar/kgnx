# Architecture

## Product boundary

The core entity is a usable **Tool**, not a GitHub repository. A tool has a
`kind` of `app`, `cli`, `service`, or `extension`, which determines how it is
installed and filtered.

```text
Editorial app metadata ─┐
                       ├─ App catalogue ─ Static PWA
GitHub trust evidence ──┘                    │
                                            ├─ anonymous local state
                                            └─ authenticated sync (later)
```

GitHub may be the source repository, but one app can eventually have several
repositories, package-manager entries, store listings, and release channels.
The domain model must not use `repository_id` as the product identifier.

## Current vertical slice

The implemented prototype has no backend:

```text
data/catalog/tools.json      editorial value, kind, platforms, install command
        │
pipeline/catalog.py          GitHub evidence enrichment
        │
data/tools/feed.json         deployable public catalogue
        │
pipeline/render.py           static HTML generation
        │
site/                        indexable offline-capable PWA
        │
web/app.js                   local Save / Try / Using / preferences
```

Run the complete path:

```bash
./run-everything.sh
```

Static HTML is deliberate. App and collection pages must be indexable and
shareable. JavaScript progressively adds personalisation; the content remains
readable if it fails.

## Domain model

### Tool

```text
id / slug
name
kind: app | cli | service | extension
pitch
platforms[]
categories[]
traits[]
install_command
product_url
install_targets[]
source_repositories[]
editorial_status
first_seen_at
approved_at
featured_at
last_featured_at
```

### AppSnapshot

Time-stamped public evidence:

```text
app_id
captured_at
last_push_at
latest_release_at
stars
contributors
top_author_share
commits
has_tests
has_ci
licence
maturity_verdict
```

Snapshots make change, renewed momentum, and abandonment measurable without
depending on inaccessible stargazer lists.

### Edition

```text
id
slug
title
published_at
collection
app_slots[] {
  app_id
  position
  editorial_reason
}
```

An Edition is stable. Re-running ingestion updates evidence but does not silently
replace its contents.

### UserAppState

```text
user_id or anonymous device
app_id
status: saved | try | using
dismissed_at
first_seen_at
last_viewed_at
updated_at
```

`status` is one mutually exclusive workflow state. Dismissal is separate.
GitHub stars are not represented here; they are external mutations with their
own audit trail.

### Preference

```text
platforms[]
categories[]
privacy_traits[]
notification_settings
```

## Anonymous storage

The prototype stores one versioned object in `localStorage` because the catalogue
is small. Before thousands of apps or offline snapshots, migrate to IndexedDB.

Current key:

```text
kgnx.state.v2
```

State includes statuses, dismissed IDs, platform/category preferences, and the
active view. An export button gives the user a JSON copy.

Local state remains the instant UI source even after authentication. Sync writes
to a local outbox first, updates optimistically, and retries in the background.

## Authentication and sync

Authentication is optional and should be introduced only for cross-device value.

Recommended public architecture:

```text
Browser/PWA
   │ HttpOnly session cookie
Cloudflare Worker BFF
   ├─ GitHub App OAuth with PKCE
   ├─ sync API
   ├─ optional star mutation proxy
   └─ D1
```

The browser must never store a GitHub access token. The BFF holds encrypted
tokens and exposes only the required operations.

### First sign-in merge

1. Browser authorises with GitHub.
2. Server creates a user and returns an opaque session cookie.
3. Browser uploads its local state with original timestamps.
4. Server merges each app by `updated_at`; explicit `using` wins a timestamp tie.
5. Server returns canonical state.
6. Browser keeps the local copy for offline use.

### Minimal D1 schema

```sql
users(
  id, github_user_id, github_login, created_at
)

sessions(
  id_hash, user_id, expires_at
)

user_app_state(
  user_id, app_id, status, dismissed_at,
  first_seen_at, last_viewed_at, updated_at,
  primary key(user_id, app_id)
)

user_preferences(
  user_id primary key, payload_json, updated_at
)

github_mutations(
  id, user_id, app_id, kind, status, created_at, completed_at
)
```

Do not store every impression initially. Product analytics should be
privacy-safe aggregates with explicit consent.

## GitHub integration

### Public ingestion token

The scheduled pipeline uses a repository secret with read-only public access.
It refreshes evidence and candidate pools. It is not the user’s token.

### User token

Request the minimum permission required for:

- identifying the user;
- reading their own stars if they opt into import;
- starring an app only after an explicit click.

An internal Save never triggers a GitHub star automatically.

### Limits

The current catalogue uses roughly six REST calls per app and caches responses
for six hours. Daily refresh of hundreds of approved apps remains within normal
authenticated limits. At larger scale:

- refresh active/current-edition apps daily;
- refresh archive apps weekly;
- use ETags;
- snapshot only fields needed by cards;
- queue retries using `Retry-After`.

## Fully automated discovery pipeline

The launch pipeline has no approval queue or admin application.

```text
Search / nominations / release feeds
        ↓
candidate pool
        ↓ automatic checks
installable? active? licence? release path? clear product?
        ↓
strict unattended-publication gate
proven + ≤21d activity + tests + CI + licence
+ ≥100 commits + ≥3 contributors + ≥2 releases
        ↓
one publication per UTC day, rotating kinds
        ↓
30-day current window → archive
```

`.github/workflows/refresh-catalogue.yml` runs daily:

1. `pipeline/discover.py` searches by kind and updates the auditable candidate
   report.
2. `pipeline/autopublish.py` chooses at most one unseen candidate. It rotates
   app → CLI → service → extension by UTC day so one category cannot dominate.
3. Product name and pitch come from authoritative repository fields. Platforms
   and categories use deterministic text rules. If metadata cannot prove an
   install command, none is shown.
4. `pipeline/lifecycle.py` expires 30-day windows.
5. The catalogue, site, candidates, and lifecycle state are committed directly
   by the bot. That commit triggers Pages deployment.

The bias is deliberately toward false negatives: useful tools may be missed,
but uncertain tools are not automatically published. The blocklist excludes
reading lists, templates, bypass/cracking/credential tools, spam, and similar
high-risk categories. The project never describes an automated selection as
“guaranteed safe”; it only states which public evidence passed.

Lifecycle state lives in `data/editorial/lifecycle.json`. A new catalogue entry
is active for 30 days, then remains available in Archive. Republish explicitly:

```bash
python3 -m pipeline.lifecycle --republish <slug>
```

There is no hidden moderation database. `data/catalog/automatic.json`,
`data/candidates/`, and the bot's Git history expose every automated decision.

## Personal ranking

No LLM is required for v0.1.

Start with explicit, inspectable weights:

- selected platform match;
- category match;
- similarities to apps marked Using;
- traits shared with Saved or Try apps;
- novelty and diversity;
- penalties for dismissed, viewed repeatedly, or already used apps.

Server-side embeddings are only justified after enough real actions exist to
evaluate whether they improve installation or retention.

## Delivery

### Prototype and first public release

- static HTML/CSS/JavaScript;
- Cloudflare Pages or GitHub Pages;
- scheduled GitHub Action for public data;
- custom domain `kgnx.nx.kg`;
- PWA manifest and service worker;
- no backend until sync is implemented.

### Authenticated beta

- Cloudflare Pages + Worker + D1;
- GitHub App OAuth;
- local-first sync;
- weekly email/RSS generation;
- optional web push.

### Growth

Move public catalogue snapshots to object storage/CDN and D1 user state to
PostgreSQL only after measured volume requires it. A graph database, ClickHouse,
vector database, and RAG are not launch requirements.

## Security and privacy invariants

- Browsing never requires authentication.
- GitHub tokens never enter browser storage.
- Save is private and does not create a public GitHub endorsement.
- User actions are exportable and deletable.
- Dismissal is not a global negative signal.
- Evidence is public and explainable.
- Sponsored content, if ever allowed, cannot influence organic ranking.
