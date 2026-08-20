# Roadmap

The roadmap follows product risk: useful catalogue, explicit actions, repeat
visits, cross-device sync, then recommendation sophistication.

## Phase 0 — working vertical slice

Status: **implemented locally**.

- Tool model separate from GitHub Repository;
- apps, CLI tools, self-hosted services, and browser extensions;
- GitHub trust enrichment;
- responsive static PWA;
- platform and category filters;
- Save / Try next / I use this / Not for me;
- separate personal lists;
- local persistence and export;
- offline application shell;
- one `run-everything.sh` command.

Exit work:

- test the whole interaction on an actual phone;
- monitor false-positive rate of strict automatic publications;
- keep cards artwork-free unless authoritative product assets are available;
- decide whether Try next needs a soft limit of ten;
- conduct five observed sessions with technical macOS users.

## Phase 1 — public catalogue

Goal: learn whether people find and adopt tools before building accounts.

- connect `kgnx.nx.kg`;
- deploy static site on GitHub Pages;
- daily automatic Search → strict gate → one publication → 30-day Archive;
- committed candidate, publication, evidence, and lifecycle history;
- false-positive monitoring and automatic rollback criteria;
- individual indexable tool and collection pages;
- RSS feeds;
- privacy-safe aggregate measurement with consent.

Exit criteria:

- 30% of visitors take an explicit action;
- 20% place a tool in Try next;
- users report installing something they discovered;
- 25% return within 14 days;
- fewer than 5% of automatic publications require removal.

## Phase 2 — cross-device private beta

Goal: complete the phone-to-computer workflow.

- GitHub App OAuth through a Cloudflare Worker BFF;
- encrypted server tokens and HttpOnly sessions;
- D1 user, preference, session, and app-state tables;
- merge anonymous local state on first sign-in;
- offline outbox and timestamp-based sync;
- optional import of relevant personal GitHub stars;
- explicit GitHub Star button separate from Save;
- weekly email and optional web push;
- delete account and full state export.

Exit criteria:

- users successfully save on phone and install from desktop;
- no state-loss or merge incidents;
- authentication increases cross-device completion rather than blocking use;
- at least 10% of active users use a second device.

## Phase 3 — personal discovery

Goal: make “I use this” improve the next visit.

- transparent local ranking from platforms, categories, traits, and actions;
- similar apps and useful alternatives;
- diversity constraints;
- update notifications for Try next and Using;
- optional shareable “My open-source stack”;
- experiments comparing explicit rules against content embeddings.

Do not add embeddings unless they measurably improve Try or install outcomes.

## Phase 4 — expand carefully

- dedicated Windows and Linux editions;
- self-hosted collection;
- community nominations entering the same automatic evidence gates;
- team-curated stacks;
- package-manager integration and verified install commands;
- PostgreSQL only if D1 and static snapshots become limiting;
- native shell only if measured PWA limitations block retention.

## Intentionally deferred

- infinite feed;
- unattended publication without the strict evidence and policy gates;
- public downvotes;
- mandatory login;
- automatic GitHub starring;
- sponsored organic ranking;
- native iOS and Android codebases;
- graph database, vector database, ClickHouse, or RAG without measured need.
