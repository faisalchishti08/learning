---
card: system-design
gi: 227
slug: url-shortener-api-design
title: URL Shortener — API design
---

## 1. What it is

This page covers the **API design** facet of the **URL Shortener** case study — the concrete endpoints, HTTP verbs, request/response shapes, and status codes the system exposes, satisfying the [functional requirements](0224-url-shortener-functional-requirements.md) already established. Other facets (like [high-level architecture](0228-url-shortener-high-level-architecture.md)) cover what happens behind these endpoints; this page covers the contract clients see.

## 2. Why & when

Once functional requirements are settled, the API is the first concrete artifact clients and other engineers will actually interact with — get it wrong and every consumer is affected. Design it directly from the functional requirements list, applying [resource modeling](0206-resource-modeling-naming.md) and [idempotency](0210-idempotency-safe-methods.md) principles, before writing any implementation code, since the API contract should drive the implementation, not the other way around.

## 3. Core concept

- **Two core endpoints, matching FR-1 and FR-2.** `POST /api/urls` creates a short URL (FR-1); `GET /{shortCode}` is the actual redirect (FR-2) — note this second one is not prefixed with `/api/`, since it is the public-facing short link itself, not an API call a client parses as JSON.
- **Idempotency on creation.** Calling `POST /api/urls` with the same long URL twice, with no other distinguishing input, could reasonably create two different short codes for the same destination — this is acceptable default behavior, but supplying a client-generated `Idempotency-Key` header (see [idempotency & safe methods](0210-idempotency-safe-methods.md)) lets a client safely retry a creation request after a network timeout without risking a duplicate.
- **Custom alias handling (FR-4).** An optional `customAlias` field in the creation request; if provided and already taken, the endpoint must return a specific, distinguishable error rather than silently falling back to a generated code.
- **Correct status codes.** `201 Created` for a successful creation, `301 Moved Permanently` or `302 Found` for the redirect (a real design decision, covered in the walkthrough below), `404 Not Found` for an unknown or expired short code, `409 Conflict` for a taken custom alias.
- **Error shape.** Every error response follows the [`application/problem+json`](0211-error-contracts-problem-json.md) contract established for the whole API, so clients parse errors from any endpoint the same way.

## 4. Diagram

```
  CREATE                                        REDIRECT

  Client                    Server               Client (browser)          Server
    |                          |                     |                        |
    |-- POST /api/urls ------->|                     |-- GET /aZ9kLp -------->|
    |   { longUrl: "...",      |                     |                        | look up "aZ9kLp"
    |     customAlias: null,   |                     |                        | in cache, then DB
    |     Idempotency-Key: k1} |                     |                        |
    |                          | generate short code  |                        |
    |                          | store mapping        |<-- 301 Moved -----------|
    |<-- 201 Created ----------|                     |    Location: <longUrl>  |
    |   { shortUrl: "...",     |                     |                        |
    |     shortCode: "aZ9kLp"} |                     | browser follows the     |
    |                          |                     | redirect automatically  |
```
*Caption: creation is a normal request/response API call. The redirect is not JSON at all — it is a raw HTTP redirect response a browser follows automatically, which is why its endpoint has no `/api/` prefix.*

## 5. Runnable example

### API specification

```http
### Create a short URL
POST /api/urls HTTP/1.1
Content-Type: application/json
Idempotency-Key: 7b3f9c2a-...

{
  "longUrl": "https://example.com/some/very/long/path?query=params",
  "customAlias": null,
  "expiresAt": null
}

### Success response
HTTP/1.1 201 Created
Content-Type: application/json
Location: /api/urls/aZ9kLp

{
  "shortCode": "aZ9kLp",
  "shortUrl": "https://short.ly/aZ9kLp",
  "longUrl": "https://example.com/some/very/long/path?query=params",
  "createdAt": "2026-09-10T14:22:00Z",
  "expiresAt": null
}

### Custom alias already taken
POST /api/urls HTTP/1.1
Content-Type: application/json

{ "longUrl": "https://example.com/sale", "customAlias": "my-sale" }

HTTP/1.1 409 Conflict
Content-Type: application/problem+json

{
  "type": "https://api.short.ly/errors/alias-taken",
  "title": "Alias Already Taken",
  "status": 409,
  "detail": "The alias 'my-sale' is already in use.",
  "instance": "/errors/instances/e-1023"
}

### Redirect (the public-facing short link itself)
GET /aZ9kLp HTTP/1.1
Host: short.ly

HTTP/1.1 301 Moved Permanently
Location: https://example.com/some/very/long/path?query=params

### Unknown or expired short code
GET /doesNotExist HTTP/1.1
Host: short.ly

HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{
  "type": "https://api.short.ly/errors/short-code-not-found",
  "title": "Short Code Not Found",
  "status": 404,
  "detail": "No active URL exists for short code 'doesNotExist'.",
  "instance": "/errors/instances/e-1024"
}
```

## 6. Walkthrough

1. **`POST /api/urls` with a body containing `longUrl` (required), `customAlias` (optional, FR-4), and `expiresAt` (optional, FR-5) implements creation.** The `Idempotency-Key` header lets a client safely retry this call after a timeout without risking a duplicate short URL being created for the same intended request — this directly reuses the pattern from [idempotency & safe methods](0210-idempotency-safe-methods.md).
2. **A successful creation returns `201 Created`** with the generated (or accepted custom) `shortCode`, the full `shortUrl` the creator will actually share, and the original `longUrl` echoed back for confirmation — this lets the client immediately display or copy the new short link with no second request needed.
3. **When `customAlias` is supplied but already taken, the server returns `409 Conflict`**, using the shared [`problem+json`](0211-error-contracts-problem-json.md) error shape with a specific `type` (`alias-taken`) the client can match on to show a targeted error message ("that alias is taken, try another"), rather than a generic failure.
4. **`GET /aZ9kLp` is the redirect itself — the short link a person actually clicks.** It deliberately has no `/api/` prefix and returns no JSON body at all; it returns a bare HTTP redirect status with a `Location` header, which every browser follows automatically without the visitor seeing any intermediate page. Choosing `301 Moved Permanently` (cacheable by browsers and CDNs, reducing load on the server for repeat visits to the same link) versus `302 Found` (never cached, so every visit hits the server, but click analytics — FR-6 — stay accurate per-click) is a real design tradeoff: 301 is faster and cheaper at scale, 302 is more accurate for analytics. Many production URL shorteners choose 302 specifically to keep click counts accurate.
5. **`GET /doesNotExist` for an unrecognized or expired code returns `404 Not Found`**, again using the shared `problem+json` shape — this is the same contract every other error on this API follows, so a client's error-handling code does not need special cases per endpoint.

## 7. Gotchas & takeaways

> **Gotcha:** choosing `301 Moved Permanently` for the redirect without considering FR-6 (click analytics) is a subtle trap — browsers and CDNs cache a 301 aggressively, meaning a repeat visitor's browser may resolve the redirect locally without ever hitting the server again, silently undercounting clicks. If accurate click analytics matter, `302 Found` (or `307`, which also preserves the HTTP method) is usually the right choice, at the cost of higher server load per click.

- Design the API directly from the functional requirements list — each endpoint here traces to a specific FR from [functional requirements](0224-url-shortener-functional-requirements.md), and any endpoint that does not trace to a requirement is worth questioning.
- The redirect endpoint is not a typical JSON API call — treat it as a special case that returns raw HTTP semantics (a `Location` header and a redirect status), because that is what makes it work transparently in a browser with zero client-side code.
- Use the shared [`problem+json`](0211-error-contracts-problem-json.md) error contract across every endpoint on this API, including the redirect path's `404` — consistency here is what makes client error handling simple.
- See [URL Shortener — high-level architecture](0228-url-shortener-high-level-architecture.md) next for what happens behind these two endpoints — the cache, database, and key-generation service that make the redirect fast and the creation collision-free.
