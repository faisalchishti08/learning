---
card: system-design
gi: 246
slug: pastebin-high-level-architecture
title: Pastebin — high-level architecture
---

## 1. What it is

This page covers the **high-level architecture** facet of the **Pastebin** case study — the components and request flow that implement the [API design](0245-pastebin-api-design.md)'s endpoints, shaped specifically around the [capacity estimation](0244-pastebin-capacity-estimation.md)'s key finding: storage volume (~7.3 TB over 2 years, driven by a 10 KB average item size), not raw QPS, is this system's dominant constraint — the opposite emphasis from the [URL Shortener's](0228-url-shortener-high-level-architecture.md) QPS-driven, cache-heavy design.

## 2. Why & when

The URL Shortener's architecture centered on a cache absorbing enormous read QPS against tiny records. Pastebin's numbers are different enough (~347 peak read QPS — modest; ~7.3 TB total content — substantial) that copying that architecture wholesale would misallocate engineering effort. This facet is where the estimation's specific conclusion becomes a specifically different architecture.

## 3. Core concept

- **Metadata database vs. blob storage — a split the URL Shortener never needed.** Given the 10 KB average (and up to 1 MB maximum) item size, storing paste content directly in the same database row as a normal OLTP database's other rows is workable but not ideal at this volume; a common, more scalable split is a small metadata database (paste ID, language, expiration, size) plus a dedicated blob/object storage service (like S3) holding the actual text content, referenced by the metadata row.
- **Cache still present, but less load-bearing than the URL Shortener's.** With a 10:1 (not 100:1) read:write ratio and modest peak QPS (~347, not ~11,600), a cache in front of frequently-viewed pastes still helps latency, but the architecture does not depend on it to survive — a meaningfully different role than the URL Shortener's cache, which was load-bearing for the whole system's viability at scale.
- **A background expiration sweeper.** Because FR-4 allows pastes to expire, and storage volume is the system's binding constraint, a background process that finds and deletes expired pastes' blobs (and metadata rows) is a first-class architectural component here — reclaiming storage matters in a way it barely did for the URL Shortener, whose total storage was comparatively trivial.
- **The reveal endpoint's delete-on-read semantics (FR-6) touch both stores.** A successful `POST /api/pastes/{id}/reveal` must delete both the metadata row and the blob content — and doing so needs care to avoid a state where one is deleted and the other is not (a partial-failure risk that did not exist when everything lived in one row).

## 4. Diagram

```
                              +----------------+
      Client -------------->|  Load Balancer   |
                              +--------+--------+
                                       |
                    +------------------+------------------+
                    v                                       v
             +-------------+                         +-------------+
             | App Server   |                         | App Server   |
             +------+------+                         +------+------+
                    |                                        |
        +-----------+-----------+                            |
        v                       v                             |
  POST /api/pastes         GET /api/pastes/{id}                |
  (creation)               (retrieval, cache-aside)             |
        |                       |                               |
        v                       v                               |
  +-----------+           +-----------+                         |
  | Metadata   |           |   Cache    |  <---- cache miss -----+
  | Database   |           | (hot pastes)|
  +-----+-----+           +-----+-----+
        |                       | cache hit: return
        v                       | content directly
  +-----------+                 |
  | Blob        | <-------------+  (metadata DB points to blob
  | Storage      |                  storage; app server fetches
  | (paste text)  |                  the actual content from there
  +-----------+                  on a cache miss)

  Background: Expiration Sweeper
    - periodically scans metadata DB for expires_at < now()
    - deletes matching blobs from Blob Storage, THEN the metadata row
```
*Caption: the metadata database and blob storage are two separate stores, coordinated by the app server — a direct architectural consequence of the capacity estimation's much larger average item size compared to the URL Shortener.*

## 5. Runnable example

### Component list and key configuration

```text
LOAD BALANCER / APP SERVERS
  - Same role as in the URL Shortener architecture: stateless, horizontally
    scaled, handling both creation and retrieval requests.

METADATA DATABASE
  - Holds: pasteId, language, createdAt, expiresAt, burnAfterReading,
    blobReference (a pointer to the content in blob storage), sizeBytes.
  - Does NOT hold the actual paste text - kept small and fast for the
    metadata lookups that gate every retrieval (existence check,
    expiration check, burn-after-reading check).

BLOB STORAGE (e.g. S3-compatible object storage)
  - Holds: the actual paste content, keyed by a reference stored in the
    metadata row (often the pasteId itself, or a derived storage key).
  - Chosen specifically because of the ~10 KB average / up to 1 MB max
    item size from capacity estimation - well beyond what a lean OLTP
    database row is best suited for at this volume (~7.3 TB over 2 years).

CACHE (e.g. Redis, or a CDN for public, non-burn pastes)
  - Caches full paste content for frequently-viewed pastes.
  - Present, but NOT load-bearing for system viability the way the URL
    Shortener's cache was - peak QPS here (~347) is comfortably within
    what a well-provisioned database + blob storage could serve directly
    if the cache were briefly unavailable.

EXPIRATION SWEEPER (background job)
  - Periodically queries: SELECT * FROM metadata WHERE expires_at < now()
  - For each match: delete the blob from Blob Storage, THEN delete the
    metadata row (in that order - see walkthrough for why).
```

## 6. Walkthrough

1. **A creation request (`POST /api/pastes`) arrives and is routed to an app server**, which writes the actual content to blob storage first, then writes a metadata row (referencing that blob) to the metadata database — this ordering matters: writing the blob first means a crash between the two writes leaves an orphaned, harmless blob with no metadata pointing to it (cleanable later), rather than a metadata row pointing at content that was never actually saved.
2. **A retrieval request (`GET /api/pastes/{id}`) for a normal paste first checks the cache.** On a cache hit, the app server returns the cached content directly, without touching either the metadata database or blob storage — the same cache-aside pattern as the URL Shortener, just serving a proportionally smaller fraction of total traffic here, given the lower read:write ratio from [non-functional requirements](0243-pastebin-non-functional-requirements.md).
3. **On a cache miss, the app server queries the metadata database first** (checking existence, expiration, and burn-after-reading status — all fast checks against small rows), and only if those checks pass does it fetch the actual content from blob storage — this two-step lookup (fast metadata check, then a separate content fetch) is exactly what the metadata/blob split enables: an expired or already-burned paste is rejected cheaply, without ever touching the (potentially much larger) blob storage read.
4. **The expiration sweeper runs periodically**, finding metadata rows whose `expires_at` has passed. It deletes the corresponding blob **first**, then the metadata row — this ordering, the reverse of creation's ordering, is deliberate: if the sweeper crashes between the two deletes, the result is a metadata row that still exists but whose blob is gone (a "dangling reference"), which the retrieval path can detect and treat as `410 Gone`, rather than the more confusing alternative of a blob existing with no metadata pointing at it, which nothing in the system would ever notice or clean up.
5. **A successful `POST /api/pastes/{id}/reveal` (FR-6) follows the same careful ordering as the sweeper**: read and return the content, delete the blob, then delete (or mark burned) the metadata row — ensuring a reader always gets the content back before any deletion happens, while still leaving the system in a safely detectable state if a failure occurs partway through.

## 7. Gotchas & takeaways

> **Gotcha:** the ordering of blob-then-metadata deletes (or metadata-then-blob writes) is not a minor implementation detail — get it backwards, and a crash partway through leaves the system either serving content that officially doesn't exist (a security-relevant issue for a burned or expired paste) or permanently leaking blob storage with no metadata ever pointing to it for cleanup. Choose and document the ordering deliberately, as this facet does, rather than leaving it to accident.

- The metadata/blob split is this architecture's central, distinguishing decision, and it traces directly back to [capacity estimation](0244-pastebin-capacity-estimation.md)'s much larger average item size compared to the URL Shortener — cite that specific number when explaining why this system's architecture differs from that one's.
- The cache here plays a real but non-load-bearing role, a genuinely different emphasis from the URL Shortener's cache-critical design — both conclusions come directly from each system's own capacity estimation, not from a generic "always cache reads" instinct.
- The expiration sweeper is a first-class architectural component specifically because storage volume, not QPS, is this system's binding constraint — reclaiming expired storage matters here in a way it barely registered for the URL Shortener.
- See [Pastebin — data model & schema](0247-pastebin-data-model-schema.md) next for the concrete metadata schema and blob storage key structure that implement this architecture's two-store split.
