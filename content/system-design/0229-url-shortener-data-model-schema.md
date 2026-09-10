---
card: system-design
gi: 229
slug: url-shortener-data-model-schema
title: URL Shortener — data model & schema
---

## 1. What it is

This page covers the **data model & schema** facet of the **URL Shortener** case study — the entities, fields, keys, and indexes the [database from the high-level architecture](0228-url-shortener-high-level-architecture.md) actually stores, and whether a SQL or NoSQL store fits better. It defines the concrete shape of the "source of truth" component named in that facet.

## 2. Why & when

The [high-level architecture](0228-url-shortener-high-level-architecture.md) names "a database" as a component, but does not say what is stored, in what shape, or with what keys — that is exactly this facet's job. Define the schema right after the architecture is settled, since the schema must support every access pattern the architecture assumes: a fast lookup by `shortCode` on every redirect, and an insert per creation.

## 3. Core concept

- **Primary entity: `Url`.** One row (or document) per short-code-to-long-URL mapping. Fields: `short_code` (the primary key — this is exactly what every redirect looks up by), `long_url`, `created_at`, `expires_at` (nullable, satisfying FR-5), `creator_id` (nullable, for FR-7's "manage my URLs"), `click_count` (satisfying FR-6, though see the walkthrough for why this needs care under concurrent writes).
- **`short_code` as the primary key, not a separate auto-increment ID.** Every redirect looks up by `short_code` directly — making it the primary key means that lookup is a direct primary-key read, the fastest possible access pattern a database offers, with no secondary index needed for the system's single most frequent operation.
- **SQL vs. NoSQL.** This data model has no relationships to join (each `Url` row stands alone) and its access pattern is a simple key lookup — exactly the profile a NoSQL key-value store (like DynamoDB or Cassandra) is built for, and such a store scales horizontally more simply than a relational database for this specific shape. A relational database works fine too, especially if `creator_id` needs to join against a `Users` table for FR-7 — the choice is a real tradeoff, not a forced one.
- **Index on `creator_id`** (only needed if FR-7, "list my URLs," is in scope) — this is a secondary index, since it is not the primary lookup path, and it is only needed to support one specific, lower-frequency query.
- **`click_count` as a separate, append-oriented record**, not a field updated in place on every redirect — explained in the walkthrough, this avoids turning the hottest read path into a write-contention bottleneck.

## 4. Diagram

```
   +-----------------------------------+
   |                Url                  |
   +-----------------------------------+
   | PK  short_code      VARCHAR(10)     |  <- every redirect looks up by this
   |     long_url        TEXT             |
   |     created_at       TIMESTAMP        |
   |     expires_at        TIMESTAMP NULL   |
   |     creator_id         VARCHAR NULL     |  <- FK to Users, optional
   +-----------------------------------+
                    ^
                    | (optional FK, only if FR-7 in scope)
                    |
   +-----------------------------------+
   |               Users                  |
   +-----------------------------------+
   | PK  user_id          VARCHAR         |
   |     ...                                |
   +-----------------------------------+

   +-----------------------------------+
   |           ClickEvent (separate)      |   <- append-only, NOT updated in place
   +-----------------------------------+
   | PK  event_id         UUID             |
   |     short_code         VARCHAR (index) |
   |     clicked_at          TIMESTAMP        |
   +-----------------------------------+
```
*Caption: `Url` is the single source of truth for redirects, keyed by exactly what a redirect looks up by. `ClickEvent` is deliberately separate and append-only, so recording a click never contends with the redirect's read.*

## 5. Runnable example

### Schema (SQL DDL)

```sql
-- Primary entity: one row per short URL. short_code is the PK because
-- that is exactly what every redirect looks up by.
CREATE TABLE url (
    short_code   VARCHAR(10)  PRIMARY KEY,
    long_url     TEXT         NOT NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT now(),
    expires_at   TIMESTAMP    NULL,
    creator_id   VARCHAR(36)  NULL REFERENCES users(user_id)
);

-- Secondary index, only needed to support FR-7 ("list my URLs").
-- Not needed at all if that requirement is out of scope for a given deployment.
CREATE INDEX idx_url_creator_id ON url(creator_id);

-- Click events are append-only and separate from the url table itself -
-- this keeps redirect reads and click-count writes from contending with
-- each other on the same row.
CREATE TABLE click_event (
    event_id     UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    short_code   VARCHAR(10)  NOT NULL REFERENCES url(short_code),
    clicked_at   TIMESTAMP    NOT NULL DEFAULT now()
);

CREATE INDEX idx_click_event_short_code ON click_event(short_code);

-- A click COUNT for a given short_code is then a query over click_event,
-- computed periodically (or on demand), rather than a field updated on
-- every single redirect:
--   SELECT COUNT(*) FROM click_event WHERE short_code = 'aZ9kLp';
```

## 6. Walkthrough

1. **`short_code` is declared `PRIMARY KEY` directly**, not a separate surrogate ID with a secondary unique index on `short_code`. Since the redirect path (the system's highest-QPS operation, per [capacity estimation](0226-url-shortener-capacity-estimation.md)) always looks up by `short_code`, making it the primary key means this lookup is the database's fastest possible access path — no extra index hop required.
2. **`long_url` is `TEXT`, not a fixed-length `VARCHAR`**, because URLs have no fixed maximum length in practice — a fixed-length field here risks silently truncating a legitimate long URL, which would corrupt the redirect for that link.
3. **`expires_at` is nullable and directly supports FR-5.** The redirect path's database (or cache) lookup, on a cache miss, must check `expires_at` against the current time before returning a redirect — a `NULL` value means "never expires," the default for most short URLs.
4. **`creator_id` is nullable and only referenced (with its supporting index) if FR-7 is actually in scope.** A deployment that never implements "list my URLs" can omit both the column and the index entirely — this is a direct illustration of only building schema to support requirements actually in scope, per [functional requirements](0224-url-shortener-functional-requirements.md)'s explicit prioritization.
5. **`click_event` is a separate, append-only table rather than a `click_count` integer column updated on the `url` row itself.** If every redirect had to `UPDATE url SET click_count = click_count + 1 WHERE short_code = ...`, a popular link being clicked thousands of times per second would create heavy write contention on that single row — exactly the kind of hot-row problem that would undermine the [high-level architecture](0228-url-shortener-high-level-architecture.md)'s cache-based design for that same row's *read* path. Appending a new, independent row per click avoids any contention entirely, since inserts to a table do not lock existing rows, and the total count can be computed asynchronously whenever it is actually needed.

## 7. Gotchas & takeaways

> **Gotcha:** the naive `click_count` column looks simpler and is a common first instinct, but it silently reintroduces write contention on the exact row the whole architecture was built to serve from cache with zero contention. Always check whether a "simple counter" field sits on the same row as your hottest read path before adding it.

- Make the primary key match the system's actual dominant lookup pattern — `short_code` as the PK is not a stylistic choice, it is a direct consequence of the redirect being the system's highest-frequency operation.
- Only add a schema element (a column, an index) when a specific in-scope functional requirement needs it — `creator_id` and its index exist solely because of FR-7, and should be omitted if that requirement is dropped.
- Separate high-frequency, append-only writes (click events) from the row a high-frequency read path depends on — this is a general pattern for avoiding read/write contention on hot data, not specific to URL shorteners.
- See [URL Shortener — deep-dive: unique key generation & collisions](0230-url-shortener-deep-dive-unique-key-generation-collisions.md) next for how `short_code` values are actually generated to guarantee the uniqueness this primary key requires.
