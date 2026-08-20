# Product brief

## One sentence

Discover useful open-source tools you can start using today, save them on your
phone, and install them later from your computer.

GitHub is the evidence source. The usable tool is the product.

## Scope: tools, not only applications

Restricting the catalogue to graphical applications would exclude much of what
this audience actually adopts. An entry has a `kind`:

- **app** — a program with a user interface;
- **cli** — a command-line tool;
- **service** — something self-hosted on your own hardware;
- **extension** — a browser extension.

Kind is a first-class filter because it maps to how a person will install and
use the tool. Libraries and frameworks stay out: the catalogue is for things you
run, not things you build against.

## No invented artwork

Generic generated icons look decorative but carry no information. If a tool has
no genuine icon, the card shows none. The visual hierarchy comes from the name,
the kind, the platforms, and the install command instead.

## Initial audience

Start with technical macOS users who enjoy finding small, useful tools and are
comfortable with open source. The catalogue can include cross-platform apps,
but the first promise is narrow:

> The best free and open-source Mac apps you probably missed.

This audience is a good wedge because it:

- already understands GitHub but does not want to browse repositories all day;
- moves naturally between phone discovery and desktop installation;
- shares utilities with colleagues;
- values local-first, privacy, and transparent maintenance;
- has a clear category of paid subscriptions worth replacing.

Windows, Linux, mobile, and self-hosted collections follow after retention is
demonstrated.

## Problem

Useful open-source apps are scattered across GitHub, Hacker News, Reddit,
personal dotfile posts, and recommendation lists. GitHub Trending is organised
around repositories and popularity. App stores favour commercial distribution.
Generic alternative sites mix abandoned projects, services, libraries, and
installable software.

The user does not want “a repository with 8,000 stars.” They want:

- a clipboard manager that stays local;
- a meeting recorder without a subscription;
- a better window manager;
- a trustworthy free replacement for a paid utility;
- confidence that an unfamiliar app is maintained and safe enough to try.

## Product loop

```text
Discover → Save → Try next → I use this → Better discoveries
```

### Discover

The public feed is useful without an account. It shows a finite daily drop,
filtered by the user’s platforms and interests. Collections describe outcomes,
not implementation topics:

- Productivity;
- Voice and meetings;
- Clipboard and automation;
- Menu bar utilities;
- Privacy-first and local;
- Replacements for subscriptions;
- Developer tools;
- Hidden gems.

### Save

Save means “remember this.” It is private and deliberately separate from a
GitHub star. On an anonymous device it is stored locally.

### Try next

Try next is an intentionally short installation queue. It connects the main
cross-device workflow:

```text
discover on phone → save or queue → open on computer → install
```

The UI should discourage turning Try next into another infinite bookmark list.
A soft limit of ten is enough initially.

### I use this

This is stronger than a like. It identifies the user’s real software stack and
is the best personalisation signal. Later it also powers an optional shareable
“My open-source stack” page.

### Not for me

Hides the app and adjusts future local ranking. It is not a public downvote and
must never hurt a project globally.

## Card information hierarchy

The default card answers “what will this do for me?”

1. kind and supported platforms;
2. tool name;
3. one-sentence outcome;
4. traits: free, local, encrypted, keyboard-first, and similar;
5. the real install command, copyable, when one exists;
6. Save, Try next, and I use this;
7. link to the project or install page.

Repository evidence is behind **Why trust it?**:

- last activity;
- releases;
- contributors and author concentration;
- tests and CI;
- licence;
- source link.

Stars and commit counts must not dominate the card.

## Content lifecycle

The launch catalogue is fully automated, with conservative deterministic gates:

1. Ingestion searches by kind once per day.
2. Rules reject archived, inactive, non-installable, ambiguously classified,
   poorly described, dependency-only, and policy-blocked items.
3. Publication requires activity within 21 days, proven maturity, at least 100
   commits, 3 contributors, 2 releases, tests, CI, and a detected licence.
4. At most one unseen candidate is published per UTC day. Kinds rotate to
   preserve diversity.
5. Repository name and description remain authoritative; missing product facts
   are shown as unknown rather than generated.
6. Tools remain current for 30 days and then move to Archive.
7. A later qualifying run may republish an archived tool.

Every candidate, publication, evidence snapshot, lifecycle transition, and bot
commit remains public in the repository. This is transparent automation, not a
claim that software can be guaranteed safe.

## Personalisation

### Anonymous

Stored locally:

- platform and category preferences;
- Save / Try next / Using status per app;
- dismissed apps;
- viewed apps;
- lightweight ordering derived from explicit actions.

This is enough to make the product personally useful before authentication.

### Signed in with GitHub

Authentication adds:

- cross-device state sync;
- optional import of relevant starred repositories;
- optional GitHub Star action;
- shareable stack;
- release notifications for selected apps.

GitHub Star remains a separate explicit action. Signing in never becomes a gate
for discovery.

## Return mechanisms

A browser URL alone does not create a habit. Return channels are part of the
product:

- a finite “Today’s 5” drop;
- weekly editorial edition;
- RSS per platform/category;
- optional weekly email;
- optional web push for followed collections;
- updates to apps in Try next or Using;
- shareable collection and app pages.

No streaks, fake urgency, or full daily reshuffles.

## Success metrics

Early private beta:

- at least 30% of visitors take one explicit action;
- at least 20% put one app in Try next;
- at least 15% mark an app as already used;
- at least 25% return within 14 days;
- at least 10% open the product from a second device;
- qualitative evidence that users installed or adopted something useful.

GitHub stars added and cards viewed are secondary metrics.

## Monetisation constraints

Do not monetise before repeat use exists. Plausible later options:

- paid cross-device sync and update tracking;
- team-curated stacks;
- premium alerts and private collections;
- ethical affiliate links for optional paid versions.

Sponsored placement would undermine trust. If ever introduced, it must be
labelled and excluded from organic ranking.
