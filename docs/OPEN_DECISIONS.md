# Open decisions

These choices materially affect implementation and should be answered before
coding the public architecture.

## 1. Public beta authentication

**Decided:** yes, a small backend-for-frontend is required for any hosted
web version. GitHub tokens must not live in the browser.

Sequence:

1. local prototype with a developer token;
2. private beta on existing homelab HTTPS if useful;
3. public beta on a free-tier BFF (see [HOSTING.md](HOSTING.md)).

## 2. Product wedge

**Decided:** lead with personalized discovery of new repositories.

Existing stars remain the taste signal and a second mode (review / try next),
not the first screen. This competes more directly with Fork it, so ranking
quality and health filters must be visible from day one.

## 3. Launch identity

`Stargaze` must remain a codename. A new launch name should:

- not contain a confusingly generic `star` + `gaze/gazer` combination;
- be easy to search on GitHub and the web;
- work as a verb or memorable ritual if possible;
- have an available domain and GitHub organization;
- receive a basic trademark screening before monetization.

Naming should happen after the product wedge is approved but before public
screenshots or OAuth registration.

## 4. Repository access

**Decided:** public starred repositories only in v0.1.

## 5. “Stale” definition

There should be no universal automatic “dead” label. Decide:

- default inactivity threshold (candidate: 24 months);
- whether thresholds vary by repository type;
- whether archived repositories get a separate deck;
- what evidence is required before suggesting an alternative.

## 6. Try-next queue

Recommended initial constraints:

- maximum 10 repositories;
- optional personal deadline;
- revisited before new discoveries are shown;
- actions: tried/useful, tried/not useful, postpone, remove.

This is deliberately opinionated. Without a cap, it becomes another star list.

## 7. Privacy and telemetry

Decide whether the beta collects any server-side product analytics.

Recommended:

- opt-in or clearly disclosed minimal events;
- never send repository names, private URLs, notes, README text, or raw star
  lists;
- collect deck completion and anonymous action counts only;
- generate Wrapped cards locally and preview exact content before sharing.

## 8. Open-source strategy

**Decided:** open-source from day one.

## 9. FlareSolverr

**Found:** FlareSolverr 3.5.0 on Proxmox CT 102 (`media-arr`) at
`http://192.168.1.202:8191`. Used only for research fetches of GitHub Trending
and Product Hunt. It is **not** a runtime dependency.

## 10. Hosting

**Recommended:** do not rent a VPS yet. Store almost nothing on the server.

See [HOSTING.md](HOSTING.md). Default path:

1. static PWA on Cloudflare Pages or GitHub Pages ($0);
2. BFF on Cloudflare Workers + D1 ($0, then $5/month if CPU/limits bite);
3. keep the user's star library in IndexedDB;
4. optional private-beta host on existing Caddy (`192.168.1.109` / public
   reverse proxy) instead of paying anyone.
