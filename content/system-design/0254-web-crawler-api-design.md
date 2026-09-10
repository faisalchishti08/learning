---
card: system-design
gi: 254
slug: web-crawler-api-design
title: Web Crawler — API design
---

## 1. What it is

This page covers the **API design** facet of the **Web Crawler** case study — since, as [functional requirements](0251-web-crawler-functional-requirements.md) noted, this system has no traditional end-user-facing API, this facet instead covers the **operator/control API**: how a human or another system starts a crawl job, checks its progress, and retrieves crawled results, at the scale established in [capacity estimation](0253-web-crawler-capacity-estimation.md).

## 2. Why & when

Every earlier case study's API design faced outward, toward end users or client applications. This one faces "inward" — toward the engineers and systems operating the crawler itself. Design it once the crawl loop's shape (FR-1/FR-2) and its scale (capacity estimation) are settled, since the operator API's job is to control and observe that loop, not to define it.

## 3. Core concept

- **`POST /api/crawl-jobs` starts a new crawl job**, given a set of seed URLs and configuration (scope restriction per FR-10, priority rules per FR-7, recrawl policy per FR-9) — this is the operator-facing equivalent of the crawl loop's starting point.
- **`GET /api/crawl-jobs/{jobId}` reports job status and progress** — pages crawled so far, queue depth, error rate — since a crawl job can run for hours to days (per NFR-4's fault-tolerance discussion), an operator needs ongoing visibility, not just a fire-and-forget start call.
- **`POST /api/crawl-jobs/{jobId}/pause` and `.../resume`** — a crawl job is long-running infrastructure, not a single request/response transaction, so it needs lifecycle controls a typical CRUD API does not.
- **`GET /api/crawl-jobs/{jobId}/pages`** — paginated access to the crawled page results for this job (reusing [pagination, filtering & sorting](0209-pagination-filtering-sorting.md)'s cursor-based approach directly, since this collection can be enormous, per the ~7.8 billion pages estimated for a large crawl).
- **Idempotency on job creation.** Starting the same crawl job twice by accident (a retried `POST /api/crawl-jobs` after a client-side timeout) should not spin up two independent, duplicate crawls consuming the same fetch budget — an `Idempotency-Key` header, reused from [idempotency & safe methods](0210-idempotency-safe-methods.md), applies here exactly as it did for the URL Shortener's creation endpoint.

## 4. Diagram

```
  Operator                    Crawler Control API              Crawl Loop (internal)

    |-- POST /api/crawl-jobs ------------->|
    |   { seedUrls: [...], scope: ... }     |
    |<-- 201 Created, jobId: "job-42" ------|
    |                                        |-- starts the internal
    |                                        |   fetch/extract/enqueue loop
    |                                        |   from functional requirements
    |
    |-- GET /api/crawl-jobs/job-42 -------->|
    |<-- 200 OK, { pagesCrawled: 1200000,    |
    |     queueDepth: 45000, errorRate:       |
    |     0.02, status: "RUNNING" } -----------|

    | ... hours later ...

    |-- POST /api/crawl-jobs/job-42/pause ->|
    |<-- 200 OK, status: "PAUSED" -----------|-- internal loop stops
    |                                         |   pulling new work,
    |                                         |   in-flight fetches finish
    |
    |-- GET /api/crawl-jobs/job-42/pages -->|
    |<-- 200 OK, { pages: [...], nextCursor:  |
    |     "..." } ------------------------------|
```
*Caption: unlike the earlier case studies' single request/response endpoints, this API's job resource is a long-running, stateful entity — creation starts a process, and most other calls observe or control that ongoing process rather than completing a single transaction.*

## 5. Runnable example

### API specification

```http
### Start a crawl job
POST /api/crawl-jobs HTTP/1.1
Content-Type: application/json
Idempotency-Key: 9f2a1c...

{
  "seedUrls": ["https://example.com", "https://another-example.org"],
  "scope": { "allowedDomains": ["example.com", "another-example.org"] },
  "recrawlPolicy": { "enabled": true, "intervalDays": 7 },
  "priority": "normal"
}

HTTP/1.1 201 Created
Location: /api/crawl-jobs/job-42

{
  "jobId": "job-42",
  "status": "RUNNING",
  "createdAt": "2026-09-10T14:22:00Z",
  "seedUrlCount": 2
}

### Check job status/progress
GET /api/crawl-jobs/job-42 HTTP/1.1

HTTP/1.1 200 OK

{
  "jobId": "job-42",
  "status": "RUNNING",
  "pagesCrawled": 1200000,
  "queueDepth": 45000,
  "errorRate": 0.02,
  "startedAt": "2026-09-10T14:22:00Z"
}

### Pause a running job
POST /api/crawl-jobs/job-42/pause HTTP/1.1

HTTP/1.1 200 OK

{ "jobId": "job-42", "status": "PAUSED" }

### List crawled pages for this job (cursor-paginated, per capacity's scale)
GET /api/crawl-jobs/job-42/pages?limit=100 HTTP/1.1

HTTP/1.1 200 OK

{
  "pages": [
    { "url": "https://example.com/about", "fetchedAt": "...", "contentRef": "blob://..." },
    { "url": "https://example.com/products", "fetchedAt": "...", "contentRef": "blob://..." }
  ],
  "nextCursor": "eyJpZCI6MTAwfQ=="
}

### Duplicate job creation attempt (same Idempotency-Key)
POST /api/crawl-jobs HTTP/1.1
Idempotency-Key: 9f2a1c...

HTTP/1.1 201 Created

{
  "jobId": "job-42",
  "status": "RUNNING",
  "createdAt": "2026-09-10T14:22:00Z",
  "seedUrlCount": 2
}
(returned from the idempotency store - no second crawl job was started)
```

## 6. Walkthrough

1. **`POST /api/crawl-jobs` with `seedUrls`, `scope`, `recrawlPolicy`, and `priority` implements FR-1/FR-2's starting conditions plus FR-7, FR-9, and FR-10's configurable behaviors, all set at job-creation time** — this single call is the operator-facing trigger for the entire self-feeding fetch-and-extract loop from [functional requirements](0251-web-crawler-functional-requirements.md), which then runs autonomously afterward with no further per-page API calls needed.
2. **`GET /api/crawl-jobs/job-42` returns `pagesCrawled`, `queueDepth`, and `errorRate`** — this observability is essential precisely because, per [non-functional requirements](0252-web-crawler-non-functional-requirements.md)'s NFR-4, a crawl job is long-running and must survive individual worker failures; an operator needs to see aggregate progress and health without needing to inspect individual workers directly.
3. **`POST /api/crawl-jobs/job-42/pause` stops the internal loop from pulling new work from the queue, while letting in-flight fetches complete naturally** — this lifecycle control exists because a crawl job, unlike a single API request, is something an operator might need to intentionally halt (for cost control, to investigate an issue, or to respect a target site's complaint) without losing all progress made so far, which a hard "cancel and discard" would not allow.
4. **`GET /api/crawl-jobs/job-42/pages` uses cursor-based pagination directly reusing the pattern from [pagination, filtering & sorting](0209-pagination-filtering-sorting.md)**, and this choice is deliberate, not incidental — given the ~7.8 billion pages a large crawl can accumulate (per [capacity estimation](0253-web-crawler-capacity-estimation.md)), offset pagination's "skip N rows" approach would become prohibitively slow at depth, exactly the problem that facet's Level 2 walkthrough demonstrated directly.
5. **The duplicate `POST /api/crawl-jobs` call, reusing the same `Idempotency-Key`, returns the *same* `job-42` rather than starting a second crawl** — this directly reuses [idempotency & safe methods](0210-idempotency-safe-methods.md)'s pattern, and it matters more here than in a typical CRUD API: accidentally starting a second, duplicate multi-day crawl job over the same seed URLs would waste a substantial amount of the fetch-throughput budget calculated in capacity estimation, competing with the original job for the same politeness-constrained per-domain slots.

## 7. Gotchas & takeaways

> **Gotcha:** a `pause` endpoint that stops the loop but does not clearly communicate "in-flight fetches are still completing, this is not instantaneous" can confuse an operator checking `pagesCrawled` immediately after pausing and seeing it still increasing briefly — the API's status transitions (`RUNNING` → `PAUSING` → `PAUSED`, rather than a single instantaneous `RUNNING` → `PAUSED`) should reflect this reality explicitly, rather than presenting pause as an atomic, instant operation it is not.

- This API is fundamentally about controlling and observing a long-running process, not completing individual request/response transactions — design every endpoint with that job-lifecycle nature in mind, not as if this were a typical stateless CRUD resource.
- Reuse [idempotency & safe methods](0210-idempotency-safe-methods.md) for job creation specifically because a duplicate multi-day crawl is an expensive, resource-competing mistake, not a minor inconvenience.
- Reuse cursor-based [pagination](0209-pagination-filtering-sorting.md) for the crawled-pages listing endpoint specifically because of this system's enormous potential result-set size, established concretely in [capacity estimation](0253-web-crawler-capacity-estimation.md).
- See [Web Crawler — high-level architecture](0255-web-crawler-high-level-architecture.md) next for what actually runs behind this control API — the distributed fetcher workers, queue, and storage that carry out the crawl this API starts and observes.
