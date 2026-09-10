---
card: system-design
gi: 245
slug: pastebin-api-design
title: Pastebin — API design
---

## 1. What it is

This page covers the **API design** facet of the **Pastebin** case study — the concrete endpoints implementing the [functional requirements](0242-pastebin-functional-requirements.md), with particular attention to FR-6's "burn after reading" behavior, which — as flagged in that facet's walkthrough — makes retrieval a non-[idempotent](0210-idempotency-safe-methods.md) operation for that specific paste type, a wrinkle the [URL Shortener's API](0227-url-shortener-api-design.md) never had to handle.

## 2. Why & when

Design the API directly from the functional requirements list, exactly as with the URL Shortener, applying the same [resource modeling](0206-resource-modeling-naming.md) principles — but here, do it with special care around FR-6, since a naive design (treating every `GET` as automatically safe) would actively break that specific requirement the first time a browser prefetch or bot preview triggers it prematurely.

## 3. Core concept

- **`POST /api/pastes` creates a paste (FR-1), analogous to the URL Shortener's creation endpoint.** The request body includes the text content, an optional `language` hint (FR-5), an optional `expiresIn` setting (FR-4), and an optional `burnAfterReading` flag (FR-6).
- **`GET /api/pastes/{pasteId}` retrieves paste metadata and content (FR-2) — for a normal paste.** For a `burnAfterReading` paste, this same endpoint's semantics change: a successful call also deletes the paste, making the endpoint non-idempotent specifically for that paste type.
- **A confirmation step for burn-after-reading retrieval.** To avoid a prefetch or bot accidentally consuming a burn-after-reading paste, the recommended design separates "preview that this is a burn-after-reading paste" from "actually confirm and reveal it" — e.g. `GET` returns a warning/confirmation response, and a separate `POST /api/pastes/{pasteId}/reveal` performs the actual, one-time reveal-and-delete. This restores the property that `GET` stays safe, moving the unsafe, non-idempotent action to an explicit `POST`.
- **`413 Payload Too Large`** when submitted content exceeds FR-3's configured maximum — a specific, distinguishable status code rather than a generic `400`.
- **`410 Gone`** for a paste that has expired (FR-4) or was already burned (FR-6) — distinct from `404 Not Found`, since `410` specifically communicates "this did exist, but is now permanently unavailable," which is more precise than "never existed" for a client that might want to react differently (e.g. show "this paste has expired" rather than "not found").

## 4. Diagram

```
  NORMAL PASTE (idempotent GET)              BURN-AFTER-READING PASTE (separate reveal step)

  Client                    Server            Client                       Server
    |-- GET /api/pastes/x ->|                   |-- GET /api/pastes/y ------>|
    |<---- 200 OK, content -|                    |<-- 200 OK, {burnAfterRead: |
    |-- GET /api/pastes/x ->|  (same every time)|      true, NOT yet revealed}|
    |<---- 200 OK, content -|                    |                             |
                                                  | (client shows a confirm      |
                                                  |  prompt to the user first)    |
                                                  |                                 |
                                                  |-- POST /api/pastes/y/reveal -->|
                                                  |<-- 200 OK, content -------------|
                                                  |    (paste now PERMANENTLY        |
                                                  |     deleted server-side)          |
                                                  |-- GET /api/pastes/y ----------->|
                                                  |<-- 410 Gone ---------------------|
```
*Caption: a normal paste's `GET` is safely repeatable forever. A burn-after-reading paste's `GET` only previews; the actual, one-time reveal is a separate `POST` — keeping `GET`'s safety property intact for every paste type.*

## 5. Runnable example

### API specification

```http
### Create a paste
POST /api/pastes HTTP/1.1
Content-Type: application/json

{
  "content": "public class Main { public static void main(String[] a) {} }",
  "language": "java",
  "expiresIn": "1d",
  "burnAfterReading": false
}

### Success response
HTTP/1.1 201 Created
Content-Type: application/json
Location: /api/pastes/xK9pLm2

{
  "pasteId": "xK9pLm2",
  "url": "https://pastebin.example/xK9pLm2",
  "language": "java",
  "createdAt": "2026-09-10T14:22:00Z",
  "expiresAt": "2026-09-11T14:22:00Z",
  "burnAfterReading": false
}

### Content too large
POST /api/pastes HTTP/1.1
Content-Type: application/json

{ "content": "<11 MB of text>" }

HTTP/1.1 413 Payload Too Large
Content-Type: application/problem+json

{
  "type": "https://api.pastebin.example/errors/paste-too-large",
  "title": "Paste Too Large",
  "status": 413,
  "detail": "Paste content is 11534336 bytes; the maximum is 1048576 bytes (1 MB).",
  "instance": "/errors/instances/e-3001"
}

### Retrieve a NORMAL paste (safe, idempotent, repeatable)
GET /api/pastes/xK9pLm2 HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/json

{
  "pasteId": "xK9pLm2",
  "content": "public class Main { ... }",
  "language": "java",
  "expiresAt": "2026-09-11T14:22:00Z"
}

### Retrieve a BURN-AFTER-READING paste (preview only - does NOT consume it)
GET /api/pastes/yZ3qRw8 HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/json

{
  "pasteId": "yZ3qRw8",
  "burnAfterReading": true,
  "revealed": false,
  "message": "This paste will be permanently deleted after viewing. Confirm to reveal."
}

### Confirm and reveal (the actual one-time, non-idempotent action)
POST /api/pastes/yZ3qRw8/reveal HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/json

{
  "pasteId": "yZ3qRw8",
  "content": "the secret content, shown exactly once",
  "language": "text"
}

### A second reveal attempt, or GET, after burning
GET /api/pastes/yZ3qRw8 HTTP/1.1

HTTP/1.1 410 Gone
Content-Type: application/problem+json

{
  "type": "https://api.pastebin.example/errors/paste-burned",
  "title": "Paste Already Viewed",
  "status": 410,
  "detail": "This paste was set to burn after reading and has already been viewed.",
  "instance": "/errors/instances/e-3002"
}
```

## 6. Walkthrough

1. **`POST /api/pastes` with `content`, `language`, `expiresIn`, and `burnAfterReading` implements FR-1, FR-4, FR-5, and FR-6's creation-time setup all in one call** — a successful response returns `201 Created` with the new `pasteId` and its full metadata, letting the creator immediately share the returned `url`.
2. **A paste exceeding FR-3's maximum returns `413 Payload Too Large`**, a status code specifically meant for exactly this situation, using the shared [`problem+json`](0211-error-contracts-problem-json.md) shape with the actual and maximum sizes stated in `detail` — precise enough for a client to show a meaningful "your paste is too large by X bytes" message.
3. **`GET /api/pastes/xK9pLm2` for a normal (non-burn) paste behaves exactly like any safe, idempotent `GET`** — repeated calls return the identical content every time, with no side effects, satisfying both FR-2 and the general [idempotency & safe methods](0210-idempotency-safe-methods.md) principle that a `GET` should never change server state.
4. **`GET /api/pastes/yZ3qRw8` for a burn-after-reading paste deliberately does NOT reveal the content.** It returns a preview response with `revealed: false` and a warning message — this call is safe and repeatable, exactly like any other `GET`, because the actual content-revealing, paste-deleting action has been moved to a separate endpoint entirely. This is the direct fix for the wrinkle flagged in [functional requirements](0242-pastebin-functional-requirements.md)'s walkthrough: a link-preview bot or browser prefetch hitting this `GET` causes no harm, since it never sees the real content or triggers the burn.
5. **`POST /api/pastes/yZ3qRw8/reveal` is the one genuinely non-idempotent operation in this whole API** — its first call returns the actual content and deletes the paste server-side; using `POST` (which carries no safety or idempotency expectation, per [idempotency & safe methods](0210-idempotency-safe-methods.md)) for this specific action is the correct, honest choice, rather than overloading `GET` with hidden side effects. Any subsequent call to either `GET` or `POST .../reveal` for the same `pasteId` returns `410 Gone`, communicating precisely "this existed and was intentionally, permanently removed" — a more informative signal to the client than a plain `404`.

## 7. Gotchas & takeaways

> **Gotcha:** designing the burn-after-reading feature with a single `GET` that both returns the content and deletes it (the naive, obvious-seeming approach) silently violates one of HTTP's most fundamental contracts — that `GET` requests are safe. Any browser, proxy, CDN, security scanner, or chat app that prefetches links for a preview could consume the paste before its intended recipient ever opens it. The two-step preview-then-reveal design in this facet exists specifically to prevent that failure mode.

- Model the burn-after-reading feature as two distinct operations — a safe `GET` preview and a non-idempotent `POST` reveal — rather than one endpoint with hidden, destructive side effects on a nominally safe HTTP method.
- Use `410 Gone` (not `404 Not Found`) for content that existed and was deliberately removed (via expiration or burn) — this extra precision helps clients show an accurate, specific message to the user.
- `413 Payload Too Large` is the correct status for FR-3's size limit — a more specific and more useful signal to API consumers than a generic `400 Bad Request`.
- See [Pastebin — high-level architecture](0246-pastebin-high-level-architecture.md) next for how this API's creation and retrieval paths are actually served, given the [capacity estimation](0244-pastebin-capacity-estimation.md)'s conclusion that storage volume, not QPS, is this system's dominant constraint.
