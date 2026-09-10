---
card: system-design
gi: 256
slug: web-crawler-data-model-schema
title: Web Crawler — data model & schema
---

## 1. What it is

This page covers the **data model & schema** facet of the **Web Crawler** case study — the concrete schema behind the URL Frontier, Dedup Store, and crawled-page metadata named as components in [high-level architecture](0255-web-crawler-high-level-architecture.md), at the ~7.8 billion page / ~778 TB scale established in [capacity estimation](0253-web-crawler-capacity-estimation.md).

## 2. Why & when

The architecture facet named these components abstractly; this facet defines exactly what each one stores, since the schema must support the specific access patterns the architecture assumes: the Frontier's "give me the next eligible URL by domain and priority," the Dedup Store's "have I seen this URL before," and crawled-page metadata's "where is this page's content stored."

## 3. Core concept

- **`FrontierEntry` — not a flat queue row, but grouped by domain.** Fields: `url`, `domain`, `priority`, `discoveredAt`. Crucially, entries are organized (indexed, or physically partitioned) by `domain`, because the Frontier's core operation — "find the next eligible URL respecting per-domain politeness" — needs to check each domain's own state, not scan the whole queue.
- **`DomainState` — one row per domain, tracking politeness.** Fields: `domain`, `lastFetchedAt`, `crawlDelaySeconds` (from that domain's own robots.txt, or the system default) — this is what a Fetcher Worker (or the Frontier itself) checks to determine whether a domain is currently "eligible" (enough time has elapsed since `lastFetchedAt`).
- **`CrawledPage` — metadata about a successfully fetched page.** Fields: `url`, `contentRef` (a pointer into Content Storage, mirroring [Pastebin's `blob_key`](0247-pastebin-data-model-schema.md) pattern directly), `fetchedAt`, `contentHash` (supporting FR-8's duplicate-content detection), `httpStatus`.
- **Dedup structure — not a normal database table at all.** Given ~7.8 billion URLs, a conventional table with a unique index would require enormous storage and lookup cost just for membership testing; this is covered in depth in the [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md), which introduces a probabilistic structure (a Bloom filter) specifically because a normal schema element is the wrong tool at this scale.
- **`contentHash` on `CrawledPage` directly supports FR-8** (duplicate content detection across different URLs) — two different URLs producing the same `contentHash` signals the same underlying content is reachable at multiple addresses, a check the schema enables without needing to re-read and re-compare full page content.

## 4. Diagram

```
   DOMAIN STATE (politeness tracking, keyed by domain)

   +---------------------------------------+
   | domain              example.com           |
   | last_fetched_at        2026-09-10T14:22:00 |
   | crawl_delay_seconds       2                  |
   +---------------------------------------+

   FRONTIER ENTRY (queued, not-yet-fetched URLs, grouped by domain)

   +---------------------------------------+
   | url                  https://example.com/x |
   | domain                 example.com            |
   | priority                  NORMAL                |
   | discovered_at                2026-09-10T14:20:00 |
   +---------------------------------------+

   CRAWLED PAGE (successfully fetched, metadata only)

   +---------------------------------------+
   | url                  https://example.com/about |
   | content_ref             blob://pages/abc123       |
   | fetched_at                 2026-09-10T14:22:03      |
   | content_hash                   sha256:9f2a...          |
   | http_status                       200                    |
   +---------------------------------------+
```
*Caption: `DomainState` is the small, hot table checked on nearly every fetch decision; `FrontierEntry` and `CrawledPage` are the much larger collections, organized around the same `domain`/`url` keys the architecture's components actually query by.*

## 5. Runnable example

### Schema (SQL DDL, plus the conceptual dedup structure)

```sql
-- Small, hot table - one row per domain the crawler has ever encountered.
-- Checked (and updated) on nearly every fetch decision.
CREATE TABLE domain_state (
    domain               VARCHAR(255) PRIMARY KEY,
    last_fetched_at        TIMESTAMP    NULL,
    crawl_delay_seconds       INTEGER      NOT NULL DEFAULT 2
);

-- The queue itself - URLs discovered but not yet fetched.
-- Indexed by domain so the Frontier can efficiently ask "what's queued
-- for domains that are currently eligible (per domain_state)?"
CREATE TABLE frontier_entry (
    url                  VARCHAR(2048) PRIMARY KEY,
    domain                 VARCHAR(255) NOT NULL,
    priority                  VARCHAR(20)  NOT NULL DEFAULT 'NORMAL',
    discovered_at               TIMESTAMP    NOT NULL DEFAULT now()
);
CREATE INDEX idx_frontier_domain_priority ON frontier_entry(domain, priority);

-- Metadata for successfully crawled pages - content itself lives in
-- Content Storage, referenced by content_ref (same pattern as Pastebin's
-- blob_key).
CREATE TABLE crawled_page (
    url                  VARCHAR(2048) PRIMARY KEY,
    content_ref             VARCHAR(255) NOT NULL,
    fetched_at                 TIMESTAMP    NOT NULL,
    content_hash                  CHAR(64)     NOT NULL,  -- supports FR-8
    http_status                      INTEGER      NOT NULL
);
CREATE INDEX idx_crawled_page_content_hash ON crawled_page(content_hash);

-- The dedup structure is NOT a conventional table at this scale (~7.8B
-- URLs) - see the deep-dive facet for the Bloom filter approach that
-- replaces a naive "SELECT 1 FROM crawled_page WHERE url = ?" existence
-- check, which would be far too slow and storage-heavy at this volume.
```

## 6. Walkthrough

1. **`domain_state` is deliberately a small, separate table from `frontier_entry` and `crawled_page`**, even though both of those reference `domain` — this mirrors the same "separate the low-write-frequency configuration data from the high-write-frequency operational data" principle seen in the [Rate Limiter](0238-rate-limiter-data-model-schema.md)'s split between config and counters: `domain_state` is updated once per fetch per domain (a moderate rate), while `frontier_entry` rows are inserted and deleted continuously as URLs are discovered and consumed.
2. **`frontier_entry`'s index on `(domain, priority)` directly supports the Frontier's core operation**: finding the highest-priority queued URL for a domain whose `domain_state.last_fetched_at` shows its politeness window has elapsed. This two-step lookup — check `domain_state` for eligibility, then query `frontier_entry` for that domain's best candidate — is exactly what the [high-level architecture](0255-web-crawler-high-level-architecture.md)'s Frontier component performs internally.
3. **`crawled_page.content_ref` points into Content Storage rather than embedding the actual page content**, directly reusing the metadata/blob separation pattern from [Pastebin's schema](0247-pastebin-data-model-schema.md) — the same reasoning applies here, amplified by scale: with an average page size around 100 KB (per [capacity estimation](0253-web-crawler-capacity-estimation.md)) and billions of pages, keeping content out of the metadata table entirely is what keeps `crawled_page` itself fast to query.
4. **`content_hash`, indexed separately, supports FR-8's duplicate-content detection** — a query like `SELECT url FROM crawled_page WHERE content_hash = ?` finds every other URL that produced identical content, without ever needing to re-fetch or byte-compare the actual page bodies, which would be prohibitively expensive at this scale.
5. **The comment explicitly ruling out a conventional table for the dedup structure is the most important note on this page.** A `SELECT 1 FROM crawled_page WHERE url = ?` existence check, run roughly once per discovered link across potentially tens of billions of link-discovery events over a large crawl's lifetime, would impose enormous read load on a conventional indexed table — this is exactly the motivation for the [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md)'s Bloom filter approach, a genuinely different kind of data structure than anything the earlier three case studies needed.

## 7. Gotchas & takeaways

> **Gotcha:** using `crawled_page`'s own primary key (`url`) as the dedup check — "if it's not already in `crawled_page`, it's new" — misses URLs that are already *queued* in `frontier_entry` but not yet fetched. A correct dedup check must consider both "already fetched" and "already queued," or the same discovered URL can be added to the Frontier multiple times before it is ever actually fetched, wasting Frontier capacity even though FR-3 nominally covers this.

- Separate low-write-frequency domain configuration (`domain_state`) from high-write-frequency operational data (`frontier_entry`), the same principle applied in the [Rate Limiter](0238-rate-limiter-data-model-schema.md) case study, here adapted to domains rather than clients.
- Keep crawled page content out of the metadata table entirely, following the same reasoning as [Pastebin's](0247-pastebin-data-model-schema.md) metadata/blob split, amplified by this system's far larger scale.
- `content_hash` is a schema-level enabler for FR-8 that avoids expensive full-content comparison — index it specifically to support that lookup pattern.
- See [Web Crawler — deep-dive: URL frontier, dedup & politeness](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md) next for the Bloom filter and domain-aware priority queue that actually implement the Frontier and Dedup Store's real, at-scale behavior.
