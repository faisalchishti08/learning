---
card: system-design
gi: 228
slug: url-shortener-high-level-architecture
title: URL Shortener — high-level architecture
---

## 1. What it is

This page covers the **high-level architecture** facet of the **URL Shortener** case study — the components (client, load balancer, service, cache, database) and how a request flows through them. This facet is the centerpiece that ties together the [non-functional requirements](0225-url-shortener-non-functional-requirements.md)'s read-heavy skew, the [capacity estimation](0226-url-shortener-capacity-estimation.md)'s peak QPS numbers, and the [API design](0227-url-shortener-api-design.md)'s two endpoints into one coherent system.

## 2. Why & when

Every earlier facet page built toward this one: the read:write ratio (100:1) and peak read QPS (~11,600/sec) from capacity estimation are numbers no single database instance serves comfortably on its own, so the architecture must be built around absorbing that read load without every request hitting the database. This facet is where those numbers become concrete component choices.

## 3. Core concept

- **Load balancer.** Distributes incoming requests (both creation and redirect) across many stateless application server instances, and is the first line of defense for [multi-AZ](0221-multi-az-multi-region-deployment.md)-style availability.
- **Stateless application servers.** Handle both `POST /api/urls` (creation) and `GET /{shortCode}` (redirect). Being stateless means any instance can handle any request, which is what makes horizontal [autoscaling](0223-autoscaling-horizontal-pod-autoscaling.md) straightforward.
- **Cache (in front of the database, on the read path).** Given the 100:1 read:write ratio, a cache holding the mapping for frequently-accessed short codes absorbs the overwhelming majority of redirect traffic — most popular links get clicked repeatedly, so a relatively small cache captures a large fraction of total reads (a classic Zipfian/long-tail access pattern).
- **Database.** The durable source of truth for every short-code-to-long-URL mapping (satisfying the durability NFR), and the fallback for a cache miss.
- **Key-generation service.** A dedicated component (or logic within the application server) responsible for producing a new, unique short code on each creation request — separated out conceptually here because its algorithm is substantial enough to warrant its own facet page.

## 4. Diagram

```
                              +----------------+
      Client (browser) ----->|  Load Balancer   |
                              +--------+--------+
                                       |
                    +------------------+------------------+
                    v                                       v
             +-------------+                         +-------------+
             | App Server   |          ...            | App Server   |
             | (stateless)  |                          | (stateless)  |
             +------+------+                          +------+------+
                    |                                        |
        +-----------+-----------+                            |
        v                       v                             |
  POST /api/urls          GET /{shortCode}                    |
  (creation path)         (redirect path)                     |
        |                       |                             |
        v                       v                             |
  +-----------+           +-----------+                       |
  | Key-gen    |           |   Cache    | <---- cache miss ----+
  | service    |           | (hot codes)|
  +-----------+           +-----+-----+
        |                       | cache hit: return
        v                       | mapping directly (fast path)
  +---------------------------------------------------+
  |                     Database                         |
  |     (durable source of truth for every mapping)       |
  +---------------------------------------------------+
```
*Caption: the redirect path checks the cache first and only falls through to the database on a miss — this single design decision is what lets the architecture absorb the ~11,600 peak read QPS estimated earlier without every request touching the database.*

## 5. Runnable example

### Component list and key configuration

```text
LOAD BALANCER
  - Health-checks app server instances; routes both POST and GET traffic.
  - No routing logic specific to URL Shortener - a standard L7 load balancer.

APP SERVER (stateless, horizontally scaled)
  - Handles POST /api/urls: calls key-gen service, writes to DB, primes cache.
  - Handles GET /{shortCode}: reads cache first, falls back to DB on a miss,
    writes the DB result back into the cache (cache-aside pattern), issues
    the redirect response.
  - Scaled via horizontal autoscaling on request rate / CPU.

CACHE (e.g. Redis)
  - Key: shortCode. Value: longUrl (+ expiresAt, for expiration checks).
  - TTL: a rolling expiration (e.g. 24h since last access) so cold entries
    naturally age out, keeping the cache focused on genuinely hot codes.
  - Sized to comfortably hold the "hot set" - the small fraction of all
    short codes that account for the large majority of redirect traffic.

DATABASE (e.g. a key-value store or a relational DB with shortCode as PK)
  - Source of truth. Every write goes here first (durability requirement).
  - Read replicas can absorb cache-miss read traffic if the cache alone is
    insufficient at peak.

KEY-GENERATION SERVICE
  - Produces a unique shortCode per creation request (see the deep-dive
    facet page for the actual algorithm and collision handling).
```

## 6. Walkthrough

1. **A creation request (`POST /api/urls`) arrives at the load balancer**, which routes it to any healthy app server instance — statelessness means the choice of instance does not matter. The app server calls the key-generation service to get a unique `shortCode`, then writes the full mapping (`shortCode` → `longUrl`, plus metadata) to the database.
2. **The app server also primes the cache with this new mapping immediately after the database write succeeds.** This is a deliberate choice: a freshly created link is often shared and clicked soon after creation, so writing it into the cache proactively avoids an unnecessary first cache-miss on what may be its very first redirect.
3. **A redirect request (`GET /{shortCode}`) arrives at the same load balancer** and is routed to any app server. The app server's first action is to check the cache for `shortCode` — this is the **fast path**, and given the 100:1 read:write ratio and the long-tail access pattern of real link popularity, this path handles the large majority of all redirect traffic.
4. **On a cache hit, the app server returns the redirect response immediately**, using the cached `longUrl` — the database is never touched for this request. This single branch is what allows the architecture to absorb ~11,600 peak QPS: the cache, not the database, is what actually needs to sustain that rate.
5. **On a cache miss** (an infrequently accessed or brand-new-but-not-yet-cached code), the app server falls through to the database, reads the mapping, returns the redirect, and — following the cache-aside pattern — writes the result into the cache so the *next* request for this same code hits the fast path instead. This self-reinforcing behavior is what keeps the cache automatically focused on genuinely popular codes without any manual curation.

## 7. Gotchas & takeaways

> **Gotcha:** priming the cache on every creation (step 2) is a reasonable default, but for a system creating 100M+ URLs a month, most of which are clicked rarely or never, this can fill the cache with cold entries that crowd out genuinely hot ones. A rolling TTL (as noted in the component list) mitigates this by letting rarely-accessed entries age out naturally, keeping the cache focused on actual demand rather than raw creation volume.

- The cache-aside pattern (check cache, fall back to database on miss, then populate cache) is the specific mechanism that turns the 100:1 read:write ratio from a scaling problem into a scaling advantage — most traffic never reaches the database at all.
- Every component here is a direct answer to a number established earlier: the cache exists because of the read:write ratio and peak QPS ([capacity estimation](0226-url-shortener-capacity-estimation.md)); the database exists because of the durability NFR ([non-functional requirements](0225-url-shortener-non-functional-requirements.md)); the two request paths exist because of the two API endpoints ([API design](0227-url-shortener-api-design.md)).
- See [URL Shortener — deep-dive: unique key generation & collisions](0230-url-shortener-deep-dive-unique-key-generation-collisions.md) next for exactly how the key-generation service produces a unique code without colliding with an existing one.
- See [URL Shortener — scaling & tradeoffs](0231-url-shortener-scaling-tradeoffs.md) for what happens when this architecture's individual components (the cache, the database) themselves become bottlenecks at larger scale.
