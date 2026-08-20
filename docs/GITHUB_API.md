# GitHub API constraints

Verified against GitHub documentation available on 2026-08-19.

## Core limits

| API category | Authenticated limit | Product consequence |
|---|---:|---|
| REST primary | 5,000 requests/hour/user in the normal case | Enough for personal star import if enrichment is lazy |
| GraphQL primary | 5,000 points/hour/user in the normal case | Useful for selected batched details, not a way to evade REST limits |
| REST repository search | 30 requests/minute authenticated | Candidate queries must be bounded, cached, and queued |
| Search results | Maximum 1,000 results per query | Segment by topic/language/date; do not treat search as a complete corpus |
| Unauthenticated REST | 60 requests/hour/IP | Not suitable for the authenticated product |

Limits can differ for Enterprise-owned/approved applications. Design for the
normal 5,000 limit and inspect headers at runtime.

## Secondary limits

GitHub also applies abuse-prevention limits:

- most REST `GET`/`HEAD`/`OPTIONS` requests cost one secondary point;
- most REST mutations cost five secondary points;
- no more than 900 REST secondary points per minute;
- no more than 2,000 GraphQL secondary points per minute;
- no more than roughly 90 seconds of API CPU time per 60 seconds;
- generally no more than 80 content-generating requests per minute and 500 per
  hour, with undisclosed lower limits possible;
- undisclosed endpoint-specific limits may apply.

On `403` or `429`:

1. honor `Retry-After`;
2. otherwise wait until `X-RateLimit-Reset` if the primary budget is empty;
3. otherwise stop for at least a minute and exponentially back off;
4. do not keep retrying, because GitHub may ban the integration.

## Importing a user's stars

Endpoint:

```text
GET /user/starred?sort=created&direction=desc&per_page=100
Accept: application/vnd.github.star+json
```

The custom media type wraps each repository with `starred_at`. At 100
repositories per page:

| User library | Minimum list requests |
|---:|---:|
| 500 stars | 5 |
| 1,000 stars | 10 |
| 5,000 stars | 50 |
| 10,000 stars | 100 |

This is inexpensive relative to the hourly budget. Fetching README, releases,
contributors, commits, and issues for every star is not; enrich lazily.

## Star and unstar

Endpoints:

```text
PUT    /user/starred/{owner}/{repo}
DELETE /user/starred/{owner}/{repo}
```

These actions are available to GitHub App **user** access tokens with
**Starring: write** and **Metadata: read**. Installation tokens cannot star
on behalf of a user. OAuth apps typically need `public_repo` to star public
repositories; that scope is write access to public repos, not a stars-only
permission. Fine-grained PATs cannot globally manage stars.

Mutations must be serialized: GitHub recommends pausing at least one second
between mutative requests. PUT/DELETE cost five secondary points. Stay under
the content-creation secondary limits and never fan out concurrent unstars.

## Breaking change: stargazer lists

Beginning in July 2026, GitHub limits:

```text
GET /repos/{owner}/{repo}/stargazers
```

to repository administrators and collaborators. Other callers may receive an
empty response, `403`, or `404`.

This invalidates the original plan:

```text
my favorite repos → their stargazers → those users' stars → co-star ranking
```

The total `stargazers_count` field remains useful as a popularity signal, but
the identities and star timestamps for arbitrary repositories are no longer a
dependable source.

## Public user star lists

GitHub still documents:

```text
GET /users/{username}/starred
```

However, this does not solve candidate-user discovery. Harvesting unrelated
users also creates privacy, policy, quality, and request-volume risks. It may be
used for explicit user-facing features such as “compare with this username,”
but should not silently power the main recommendation model.

## Trending and velocity

GitHub has no official Trending API, and repository search does not expose
“stars gained in the last seven days.” Reliable velocity requires snapshots:

1. discover a bounded candidate set;
2. store `stargazers_count` at regular intervals;
3. compute deltas over the product's observed interval;
4. label the metric as applying to tracked repositories.

Scraping GitHub Trending is brittle and must not be the only source.

## Public event datasets

[GH Archive](https://www.gharchive.org/) and the ClickHouse GitHub dataset
contain `WatchEvent` star events. They are useful for historical experiments,
but current data is incomplete:

- WatchEvent capture degraded from mid-2025;
- reported comparisons show capture below 20% in parts of 2026;
- the ClickHouse explorer explicitly warns that stars and other non-push events
  are heavily undercounted in 2025–2026.

Consequences:

- do not claim exact current velocity from GH Archive;
- do not use missing events as negative feedback;
- pre-2025 co-star embeddings may help experiments but become increasingly
  stale;
- any model trained on the data needs a visible provenance and freshness label.

## Conditional requests and caching

Authenticated conditional REST requests with a saved ETag do not consume the
primary limit when GitHub returns `304 Not Modified`.

Requirements:

- persist ETag per exact URL and representation;
- keep request headers and query stable;
- send `If-None-Match`;
- still avoid aggressive polling because secondary limits can apply;
- use response rate headers rather than calling `/rate_limit` repeatedly.

## Search candidate generation

Repository search supports up to 100 results per page and 1,000 per query.
Generate a small diversified set of queries rather than a broad crawl:

```text
language:<language> topic:<topic> archived:false pushed:>=<date> stars:<range>
```

Use multiple popularity bands so established projects do not crowd out emerging
ones. Rank and deduplicate locally, and cache the candidate pool.

## Authentication constraints

- Browser bundles cannot hold a client secret.
- GitHub supports PKCE (`S256`) and recommends it for GitHub Apps and OAuth
  apps. The dedicated GitHub App SPA client (no secret, CORS on the token
  endpoint) is still a **paused preview** as of 2026-08-13; do not depend on it.
- OAuth apps gained refresh tokens on 2026-08-14: access ~8 hours, refresh ~6
  months, opt-in via `offline_access`. New apps default to short-lived tokens.
  The token exchange endpoint still requires a backend (`client_secret`, no CORS).
- GitHub recommends authorization code + PKCE over Device Flow for normal
  browser applications. Do not enable Device Flow for a PWA.
- A backend session with an HttpOnly cookie provides a stronger token boundary
  than storing a GitHub token in localStorage or IndexedDB.

## Primary sources

- [REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [GraphQL rate limits](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api)
- [REST search](https://docs.github.com/en/rest/search/search)
- [Starring endpoints](https://docs.github.com/en/rest/activity/starring)
- [API best practices and conditional requests](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)
- [2026 stargazer restriction](https://github.blog/changelog/2026-06-30-upcoming-access-restrictions-to-public-api-endpoints-and-ui-views/)
- [OAuth authorization and Device Flow](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)
- [PKCE changelog](https://github.blog/changelog/2025-07-14-pkce-support-for-oauth-and-github-app-authentication/)
- [OAuth refresh tokens and multiple redirect URIs](https://github.blog/changelog/2026-08-14-multiple-redirect-uris-and-token-refresh-for-oauth-apps/)
- [GitHub App SPA roadmap item](https://github.com/github/roadmap/issues/1153) (paused preview)
- [GH Archive](https://www.gharchive.org/)
- [GH Archive WatchEvent completeness issue](https://github.com/igrigorik/gharchive.org/issues/320)
