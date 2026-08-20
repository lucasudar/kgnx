# Hosting and free storage

The backend is not a warehouse for GitHub stars. It is a **lockbox for GitHub
login**. Almost all product data stays in the browser.

## What the server actually stores

| Data | Where | Size |
|---|---|---|
| GitHub identity (`user id`, login) | server | tiny |
| Encrypted GitHub access/refresh token | server | tiny |
| Session cookie mapping | server | tiny |
| Consent / settings needed across devices | server, later | tiny |
| Star library, review history, notes, decks | **IndexedDB on the device** | the real volume |
| README / release details | fetched on demand, cached locally | not persisted as a corpus |

A few hundred or a few thousand users fit in megabytes of server state. Do not
buy a dedicated VM for that.

## Recommended free path

### 1. Public site: Cloudflare Pages or GitHub Pages — $0

The PWA is static files. Either host is enough. Prefer Cloudflare Pages if the
API also lives on Cloudflare, so one account and one domain.

### 2. BFF: Cloudflare Workers + D1 — $0, then maybe $5/month

Current free Workers plan (2026):

- 100,000 Worker requests / day;
- D1: 5 million row reads / day, 100,000 writes / day, 5 GB storage;
- KV: 100,000 reads / day, 1,000 writes / day, 1 GB.

That is enough for a public beta of GitHub OAuth + token proxy.

Caveat: **free Workers CPU is 10 ms per request**. OAuth callback and a thin
GitHub proxy are I/O-bound and usually fit. Heavy JSON transforms, encryption of
large payloads, or AI inference will not. If the free CPU cap bites, the next
step is **Workers Paid at $5/month**, not a VPS.

Do not run FlareSolverr, Playwright, or LLMs on this Worker.

### 3. Optional private beta: existing homelab — $0

You already have:

- Caddy CT 109 for HTTPS;
- `develop-env` CT 112;
- public GitHub API from the user's own token during local work.

A private invite can hit a Hono API behind Caddy. Move to Cloudflare only when
strangers need a stable public URL and you do not want GitHub tokens on the home
server.

## Other free options

| Service | Role | Use it? |
|---|---|---|
| **Neon** free Postgres (~0.5 GB, scale-to-zero) | SQL if we outgrow D1 | Yes later; not required for tokens+sessions |
| **Vercel Hobby** | static + serverless functions | Fine alternative to Pages/Workers; still needs a DB for tokens |
| **Supabase** free | Postgres + Auth | Overkill. We already authenticate with GitHub, not email/password |
| **Turso** | hosted SQLite | Reasonable D1 alternative |
| **Render** free Postgres / web | possible, but services sleep | Avoid as the login path |
| **Railway** | tiny trial credit | Not a durable free tier |
| **Fly.io** | no free tier for new accounts (2026) | Skip until paying |
| **Hetzner / VPS** | always-on VM | Unnecessary until we snapshot a public repo corpus |

## What not to store for free “because we can”

- full copies of every user's stars;
- READMEs of the whole GitHub;
- a graph of stargazers (API no longer allows this for arbitrary repos);
- GH Archive dumps (incomplete for 2025–2026 WatchEvents, expensive to query).

Those belong in Phase 3, after people actually return, and then on Postgres
snapshots — still not a graph database.

## AI on a free backend

Do **not** put an LLM in the request path of every swipe. That kills both the
free tier and latency.

Use AI only as an optional explainer:

- candidate list comes from GitHub Search + local ranking;
- a short “why this card” sentence can be rule-based first;
- optional BYOK (user's OpenRouter/OpenAI key) or a later cheap batch job.

Your Ollama CT 107 is useful for **your** experiments, not for every public
user.

## Cost trigger

Stay on $0 until one of these is true:

- Cloudflare returns Error 1027 (daily request cap);
- Worker CPU timeouts on the proxy;
- we start storing a shared discovery corpus;
- we need background snapshot jobs every few hours.

Then pay **$5/month Workers** or add **Neon**, still without a VPS.
