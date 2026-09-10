---
card: system-design
gi: 247
slug: pastebin-data-model-schema
title: Pastebin — data model & schema
---

## 1. What it is

This page covers the **data model & schema** facet of the **Pastebin** case study — the concrete metadata schema and blob storage key structure that implement the two-store split from [high-level architecture](0246-pastebin-high-level-architecture.md): a lean metadata database plus separate blob storage for actual paste content.

## 2. Why & when

The architecture facet named "metadata database" and "blob storage" as separate components; this facet defines exactly what each one holds, since the split only works correctly if the metadata schema captures everything a retrieval needs to check (existence, expiration, burn status) **without** needing to touch the blob, and the blob storage key structure lets the metadata row point at content unambiguously.

## 3. Core concept

- **`Paste` metadata entity — deliberately excludes the content itself.** Fields: `paste_id` (primary key — matches the API's `pasteId`), `blob_key` (the reference into blob storage), `language` (FR-5), `size_bytes`, `created_at`, `expires_at` (nullable, FR-4), `burn_after_reading` (boolean, FR-6), `burned_at` (nullable — set once a burn-after-reading paste has been revealed, distinguishing "not yet viewed" from "already viewed and content deleted").
- **`blob_key`, not the content, lives in the metadata row.** This is the direct schema-level expression of the architecture's split — a metadata query never needs to move potentially-large content across the network just to check expiration or burn status.
- **Blob storage key structure: `pastes/{paste_id}`.** A simple, direct mapping from `paste_id` to its blob location — no separate ID scheme needed for the blob itself, since `paste_id` is already globally unique (generated the same way as the [URL Shortener's short codes](0230-url-shortener-deep-dive-unique-key-generation-collisions.md), reusing that same counter-based or random-generation approach).
- **`burned_at` as a nullable timestamp, not a simple boolean flag, on top of `burn_after_reading`.** Two fields together (`burn_after_reading` says "this paste is configured to burn"; `burned_at` says "and it already has, at this specific time") let the retrieval path distinguish three states cleanly: a normal paste (`burn_after_reading = false`), an unviewed burn-after-reading paste (`burn_after_reading = true, burned_at = null`), and an already-viewed one (`burn_after_reading = true, burned_at` set) — the last of which should return `410 Gone` per [API design](0245-pastebin-api-design.md).
- **No relational joins needed for the core read path.** Like the URL Shortener, a single `paste_id`-keyed lookup answers every metadata question a retrieval needs — this data model, despite splitting content into a second store, keeps the metadata side itself simple and join-free.

## 4. Diagram

```
   METADATA DATABASE                              BLOB STORAGE

   +-----------------------------------+          +------------------------+
   |              Paste                  |          |   Key: pastes/xK9pLm2    |
   +-----------------------------------+          |   Value: <paste content>  |
   | PK  paste_id         VARCHAR(10)    |--------->+------------------------+
   |     blob_key          VARCHAR         |  points to
   |     language            VARCHAR NULL   |  the blob
   |     size_bytes            INTEGER        |
   |     created_at              TIMESTAMP      |
   |     expires_at                TIMESTAMP NULL|
   |     burn_after_reading           BOOLEAN     |
   |     burned_at                      TIMESTAMP NULL|
   +-----------------------------------+

   Three burn-related states, distinguished by TWO fields together:
     burn_after_reading=false                  -> normal paste, never burns
     burn_after_reading=true,  burned_at=NULL   -> unviewed, still revealable
     burn_after_reading=true,  burned_at=<time>  -> already viewed, 410 Gone
```
*Caption: the metadata row holds everything a retrieval needs to decide `200`, `410`, or "fetch the blob" — without ever reading the blob itself for that decision.*

## 5. Runnable example

### Schema (SQL DDL for metadata; blob storage shown as key-value shape)

```sql
-- Metadata only - the actual paste CONTENT lives in blob storage,
-- referenced by blob_key, never duplicated here.
CREATE TABLE paste (
    paste_id            VARCHAR(10)  PRIMARY KEY,
    blob_key            VARCHAR(50)  NOT NULL,
    language            VARCHAR(30)  NULL,
    size_bytes           INTEGER      NOT NULL,
    created_at            TIMESTAMP    NOT NULL DEFAULT now(),
    expires_at             TIMESTAMP    NULL,
    burn_after_reading       BOOLEAN      NOT NULL DEFAULT false,
    burned_at                 TIMESTAMP    NULL
);

-- No secondary indexes needed for the core read path - paste_id as the
-- primary key already serves the only lookup retrieval performs.

-- A periodic query the expiration sweeper runs:
--   SELECT paste_id, blob_key FROM paste
--   WHERE expires_at IS NOT NULL AND expires_at < now();
```

```text
// Blob storage entry shape (conceptual - a real object store like S3
// has no fixed "schema" beyond key -> bytes, plus optional metadata).
// Key: "pastes/{paste_id}"  (e.g. "pastes/xK9pLm2")
// Value: the raw paste content bytes
// Optional object metadata (if the store supports it):
{
  "contentType": "text/plain",
  "uploadedAt": "2026-09-10T14:22:00Z"
}
```

## 6. Walkthrough

1. **`paste_id` is the primary key of the `paste` table**, mirroring the [URL Shortener](0229-url-shortener-data-model-schema.md)'s `short_code`-as-primary-key decision for the same reason: it is exactly what every retrieval looks up by, so making it the primary key gives the metadata check the fastest possible access path.
2. **`blob_key` stores a reference (`"pastes/xK9pLm2"`) rather than the content itself** — this single field is the schema-level implementation of the architecture's core decision. A retrieval's first step (check the metadata) never touches this field's *target*, only the reference string itself, which is why the metadata check stays fast and cheap regardless of how large the actual paste content is.
3. **`expires_at` being nullable and checked before content is fetched** means an expired paste is rejected at the metadata layer — the app server never issues an unnecessary blob storage read for content it is about to refuse to serve anyway, directly following the [high-level architecture](0246-pastebin-high-level-architecture.md)'s walkthrough of the two-step lookup.
4. **`burn_after_reading` and `burned_at` together, rather than a single boolean, implement all three burn-related states cleanly.** A retrieval handler can check: if `burn_after_reading` is `false`, treat this as any normal paste. If `true` and `burned_at IS NULL`, this is an unviewed burn-after-reading paste — eligible for the preview-then-reveal flow from [API design](0245-pastebin-api-design.md). If `true` and `burned_at` is set, immediately return `410 Gone` without any further lookup — the content is already gone.
5. **The expiration sweeper's query, `SELECT paste_id, blob_key FROM paste WHERE expires_at IS NOT NULL AND expires_at < now()`, reads exactly the two fields it needs** — `paste_id` to eventually delete the metadata row, and `blob_key` to know which blob to delete first (per the deletion ordering established in the [high-level architecture](0246-pastebin-high-level-architecture.md)'s walkthrough) — this query never needs to read or transfer any actual paste content, keeping the sweeper's own database load light even as it processes potentially many expired rows.

## 7. Gotchas & takeaways

> **Gotcha:** using a single boolean (`is_burned`) instead of the nullable-timestamp `burned_at` loses the specific moment a paste was burned — useful for debugging ("was this burned recently, or did our sweeper have a bug and leave it un-cleaned for weeks?") and for any future auditing requirement. Prefer a nullable timestamp over a boolean whenever "when did this happen" could plausibly matter later, not just "did it happen."

- Keep actual content entirely out of the metadata schema — `blob_key` as a pointer, not `content` as an inline field, is what makes the metadata/blob split from [high-level architecture](0246-pastebin-high-level-architecture.md) actually effective rather than just conceptual.
- Model burn-after-reading's three real states (never burns / unviewed / already viewed) with two fields together, rather than forcing a single boolean to carry more meaning than it can hold.
- The metadata table needs no secondary indexes for its core read path, exactly like the URL Shortener's schema — `paste_id` as the primary key already serves the system's single most frequent query.
- This closes the requirements-through-schema portion of the Pastebin case study — the remaining facets (deep-dive, scaling, and Spring/Java implementation) build directly on this schema and the two-store split it implements.
