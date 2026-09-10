---
card: system-design
gi: 255
slug: web-crawler-high-level-architecture
title: Web Crawler — high-level architecture
---

## 1. What it is

This page covers the **high-level architecture** facet of the **Web Crawler** case study — the components (URL frontier, fetcher workers, content storage, link extractor) that implement the self-feeding crawl loop from [functional requirements](0251-web-crawler-functional-requirements.md), sized to the [capacity estimation](0253-web-crawler-capacity-estimation.md)'s ~2,000+ concurrent fetch operations and ~778 TB storage figures.

## 2. Why & when

Every earlier facet built toward this one: the throughput and politeness-driven parallelism numbers from capacity estimation are what this architecture must actually deliver, and the [API design](0254-web-crawler-api-design.md)'s control endpoints are what start, pause, and observe the components described here.

## 3. Core concept

- **URL Frontier.** The crawl queue — but not a plain FIFO queue. It must support prioritization (FR-7), politeness (only surface a URL from a domain whose per-domain delay has elapsed, per NFR-2), and deduplication (FR-3) — substantial enough to warrant its own [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md).
- **Fetcher workers (a large, horizontally scaled pool).** Each worker pulls a URL from the frontier, checks `robots.txt` for that domain (FR-4, likely via a cached, periodically-refreshed robots.txt cache to avoid re-fetching it on every single page), fetches the page, and hands the result to the link extractor — sized directly from capacity estimation's ~2,000+ concurrent operations figure.
- **Link extractor.** Parses fetched HTML, extracts hyperlinks, normalizes them (resolving relative URLs, stripping fragments), and feeds newly discovered URLs back into the URL Frontier — this is the step that closes FR-1/FR-2's self-feeding loop.
- **Content storage.** Stores fetched page content, analogous to [Pastebin](0246-pastebin-high-level-architecture.md)'s blob storage, but at a much larger scale — satisfying FR-6 (content available to downstream consumers like a search indexer).
- **Dedup store.** A separate, fast-lookup store (a large-scale set/filter structure) tracking every URL already crawled or already queued, checked by the link extractor before a newly discovered URL is added to the frontier — implementing FR-3, and covered in detail in the [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md).

## 4. Diagram

```
                          +------------------+
                          |   URL Frontier     |
                          |  (priority +         |
                          |   politeness-aware)   |
                          +--------+---------+
                                   | pull next eligible URL
                                   v
                     +---------------------------+
                     |   Fetcher Worker Pool         |
                     |  (~2,000+ concurrent, per       |
                     |   capacity estimation)            |
                     +-------------+---------------+
                                   |
                    +--------------+---------------+
                    v                                v
           +----------------+                +-----------------+
           | robots.txt Cache|                |  Content Storage  |
           | (per domain)    |                |  (fetched pages)   |
           +----------------+                +-----------------+
                    ^                                   |
                    | checked before fetch                |
                    |                                       v
           +---------------------------+          +-----------------+
           |      Link Extractor           |<---------|  (parses fetched  |
           |  - normalize URLs               |          |   HTML)            |
           |  - check Dedup Store             |          +-----------------+
           |  - feed new URLs back to           |
           |    URL Frontier                      |
           +---------------------------+
                    ^
                    | check/record seen URLs
                    v
           +---------------------------+
           |        Dedup Store            |
           +---------------------------+
```
*Caption: the loop closes at the Link Extractor, which feeds newly discovered, deduplicated URLs back into the same Frontier the Fetcher Workers pull from — this is the architectural expression of FR-1/FR-2's self-feeding crawl loop.*

## 5. Runnable example

### Component list and key configuration

```text
URL FRONTIER
  - Not a plain FIFO queue - internally organizes URLs by domain, with a
    per-domain "next eligible time" respecting NFR-2's politeness delay.
  - Supports priority tiers (FR-7): higher-priority URLs surface first
    among all currently-eligible (politeness-window-open) URLs.
  - See the deep-dive facet for the concrete data structure.

FETCHER WORKER POOL (horizontally scaled, ~2,000+ concurrent per capacity estimation)
  - Pulls one eligible URL from the Frontier at a time.
  - Checks robots.txt Cache for that domain BEFORE fetching (FR-4);
    fetches and caches robots.txt itself if not already cached.
  - Fetches the page with a strict timeout (per NFR-3's fault-isolation
    target) - a slow/hanging server affects only this one fetch, never
    blocks other workers.
  - On success: hands content to the Link Extractor and writes to
    Content Storage. On failure: logs the failure, does NOT block or
    retry indefinitely (a bounded retry policy, then give up on this URL).

ROBOTS.TXT CACHE
  - Key: domain. Value: parsed disallow rules + any crawl-delay directive.
  - TTL: hours to a day - robots.txt changes rarely, so aggressive caching
    avoids fetching it on every single page from the same domain.

LINK EXTRACTOR
  - Parses HTML, extracts <a href> links, normalizes (resolve relative
    paths, strip URL fragments/tracking parameters where sensible).
  - Checks Dedup Store per extracted URL; only NEW URLs are added to the
    Frontier.

CONTENT STORAGE
  - Analogous to Pastebin's blob storage, at much larger scale (~778 TB
    per capacity estimation for a 90-day crawl).

DEDUP STORE
  - A large-scale set-membership structure (see deep-dive facet for why
    a plain hash set does not scale to billions of URLs cheaply).
```

## 6. Walkthrough

1. **A Fetcher Worker pulls the next eligible URL from the URL Frontier** — "eligible" meaning both its domain's politeness timer has elapsed (NFR-2) and it is the highest-priority URL currently available (FR-7) — this single pull operation is where the Frontier's internal complexity (detailed in the [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md)) is fully hidden from the worker, which just asks for "the next thing I should fetch" and trusts the Frontier to answer correctly.
2. **The worker checks the robots.txt Cache for that URL's domain before fetching anything.** If this domain's rules are not yet cached, the worker fetches and parses `robots.txt` itself first, caching the result for every other worker that later pulls a URL from the same domain — this single-fetch-then-cache pattern is what keeps FR-4 compliance cheap even under heavy traffic to a popular domain, avoiding a redundant `robots.txt` fetch on every single page.
3. **If the URL is disallowed by robots.txt, the worker discards it without fetching the actual page** — FR-4 enforced directly at this decision point, before any content is ever requested from the target server, which also means a disallowed URL never even touches NFR-2's per-domain rate budget for real content fetches.
4. **On a successful fetch, the worker hands the raw HTML to the Link Extractor and writes the content itself to Content Storage** — these two actions happening from the same successful fetch mirrors the URL Shortener and Pastebin architectures' pattern of a single write path feeding multiple downstream concerns from one successful operation.
5. **The Link Extractor parses the HTML, normalizes every discovered link, and checks each one against the Dedup Store.** Only links that are genuinely new (never before seen by this crawl) are added back to the URL Frontier — this final step is what closes FR-1/FR-2's loop: a URL discovered on this page becomes a URL some future Fetcher Worker will pull and process, continuing the crawl outward from the original seed URLs, while the Dedup Store's check (detailed further in the deep-dive facet) is what stops the same URL from being queued and crawled over and over.

## 7. Gotchas & takeaways

> **Gotcha:** it is tempting to design the Fetcher Worker pool as simply "N threads pulling from one shared queue," treating the URL Frontier as an implementation detail rather than a first-class component — but given NFR-2's per-domain politeness constraint, a naive shared queue without domain-aware eligibility tracking would let many workers simultaneously pull and fetch URLs from the same popular domain, violating politeness the moment real traffic (not a toy example) hits the system. The Frontier's domain-awareness is not optional polish; it is the mechanism that makes the whole architecture NFR-2-compliant at all.

- The self-feeding loop from functional requirements maps directly onto this architecture's component boundary between the Link Extractor (which discovers new work) and the URL Frontier (which the Fetcher Workers consume from) — understanding this one connection is the key to understanding the whole system's dynamics.
- Robots.txt caching per domain is what keeps FR-4 compliance cheap at scale — without it, every single page fetch would need its own separate robots.txt fetch, doubling the effective request rate against every target domain and directly working against NFR-2's politeness goal.
- Content storage here follows the same metadata/blob-style separation principle as [Pastebin's architecture](0246-pastebin-high-level-architecture.md), just operating at a scale roughly 100x larger, per the capacity estimation comparison.
- See [Web Crawler — data model & schema](0256-web-crawler-data-model-schema.md) next for the concrete schema behind the Frontier, Dedup Store, and crawled-page metadata this architecture's components actually read and write.
