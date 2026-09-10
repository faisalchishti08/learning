---
card: system-design
gi: 236
slug: rate-limiter-api-design
title: Rate Limiter — API design
---

## 1. What it is

This page covers the **API design** facet of the **Rate Limiter** case study — how a protected service actually checks a request against the limiter, and what a rejected client sees. Unlike the [URL Shortener](0227-url-shortener-api-design.md)'s public-facing API, this API is primarily an internal contract between application servers and the rate-limiting component, plus the external-facing response headers a client observes.

## 2. Why & when

A rate limiter is nearly always a library call or a sidecar check embedded inside a request's handling path, not a separately-called public endpoint — so its "API" is really two things: an internal check interface, and the external HTTP contract (status codes and headers) the client actually sees. Define both directly from the [functional requirements](0233-rate-limiter-functional-requirements.md), since FR-2's "clear rejection signal" and FR-5's "usage headers" are both API-shaped requirements.

## 3. Core concept

- **Internal check interface: `boolean allow(clientId, ruleName)` (or richer, returning remaining quota).** Called once per gated request, before the request reaches the protected business logic — this is the actual "endpoint" most of this system's callers interact with, and it is an in-process or low-latency remote call, not a public HTTP route.
- **`429 Too Many Requests` on rejection (FR-2).** The standard, distinguishable HTTP status for rate limiting — a client can programmatically distinguish "you are rate limited" from any other 4xx/5xx failure.
- **`Retry-After` header on rejection.** Tells the client exactly how long to wait before the current window resets, reusing the pattern from [rate-limit & caching headers](0214-rate-limit-caching-headers.md).
- **`X-RateLimit-*` headers on every response, not just rejections (FR-5).** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` let a well-behaved client see it is approaching its limit before it is ever rejected.
- **Per-rule reporting (FR-6).** If a client has multiple simultaneous rules (a per-minute and a per-day limit), the response should indicate which specific rule caused a rejection, so a client integrating against the API can distinguish "I burst too fast" from "I've used my whole day's quota."

## 4. Diagram

```
   App Server                    Rate Limiter (internal)         Client

   incoming request
        |
        |-- allow(clientId="c-42", rule="per-minute") ------->|
        |<---------------------- true, remaining=37 ----------|
        |
   request proceeds normally ------------------------------------> 200 OK
                                                                    X-RateLimit-Limit: 100
                                                                    X-RateLimit-Remaining: 37
                                                                    X-RateLimit-Reset: 1699999999

   [later, client exceeds its limit]

        |-- allow(clientId="c-42", rule="per-minute") ------->|
        |<---------------------- false, remaining=0 ----------|
        |
   request rejected -------------------------------------------> 429 Too Many Requests
                                                                    Retry-After: 12
                                                                    X-RateLimit-Limit: 100
                                                                    X-RateLimit-Remaining: 0
```
*Caption: the internal `allow(...)` check happens once per request, before any business logic runs. Its boolean result maps directly to whether the app server proceeds normally or returns a `429`.*

## 5. Runnable example

### API specification

```http
### Internal check interface (conceptual - typically a library call, not HTTP)
allow(clientId: "c-42", rule: "per-minute") -> { allowed: true, remaining: 37, resetAt: 1699999999 }

### A request that passes the check
GET /api/orders HTTP/1.1
Authorization: Bearer <client-c-42-token>

HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 37
X-RateLimit-Reset: 1699999999
Content-Type: application/json

{ "orders": [...] }

### A request that exceeds the per-minute limit
GET /api/orders HTTP/1.1
Authorization: Bearer <client-c-42-token>

HTTP/1.1 429 Too Many Requests
Retry-After: 12
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699999999
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Client 'c-42' exceeded the 'per-minute' limit of 100 requests.",
  "instance": "/errors/instances/e-2001"
}

### A request that exceeds the per-day limit specifically (FR-6: distinguish which rule)
HTTP/1.1 429 Too Many Requests
Retry-After: 41230
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 0
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Client 'c-42' exceeded the 'per-day' limit of 5000 requests. Resets in 11h27m.",
  "instance": "/errors/instances/e-2002"
}
```

## 6. Walkthrough

1. **The internal `allow(clientId, rule)` call is where FR-1 and FR-3 are actually enforced** — it is called once, synchronously, before the app server does any real work for the request, and it returns whether this specific client, under this specific rule, is still within its limit.
2. **When `allow(...)` returns `true`, the app server proceeds normally** and attaches the `X-RateLimit-*` headers to its normal `200 OK` response — this satisfies FR-5, letting the client observe its remaining quota on every successful request, not only when it gets rejected.
3. **When `allow(...)` returns `false`, the app server short-circuits and returns `429 Too Many Requests`** instead of running any business logic — this is the concrete implementation of FR-2's "clear, distinguishable rejection signal": `429` is a status code reserved specifically for this situation, distinguishable from a `500` (server error) or a `403` (authorization failure) by any client's error-handling code.
4. **`Retry-After` on the rejection tells the client precisely how long to wait** — reusing the exact pattern established in [rate-limit & caching headers](0214-rate-limit-caching-headers.md), so a client library already handling that header for other APIs works correctly here with no special-casing.
5. **The two `429` examples show FR-6 in the error body's `detail` field** — the first names the `per-minute` rule as the one that was exceeded, the second names `per-day` — even though both share the identical `type` and `status`. A client that only checks `status === 429` treats both the same (correctly retries later); a client that reads `detail` can distinguish a short burst-limit hit from a full daily-quota exhaustion, which call for very different retry strategies (seconds vs. hours).

## 7. Gotchas & takeaways

> **Gotcha:** forgetting to send `X-RateLimit-*` headers on **successful** responses (only sending them on `429`) is a common oversight that defeats FR-5's actual purpose — a well-behaved client cannot proactively self-throttle if it only learns its remaining quota after already being rejected once.

- The internal `allow(...)` check and the external HTTP contract (`429`, headers) are two different layers of the same API — design both, since callers of this system exist at both layers (the app server calling the check, and the end client reading the response).
- Always send usage headers on every response, success or failure — this is what actually enables proactive client-side throttling, not just reactive retry-after-rejection behavior.
- Use the `detail` field to distinguish which specific rule was violated when multiple rules apply (FR-6) — this gives integrating clients enough information to choose an appropriate retry strategy per rule.
- See [Rate Limiter — high-level architecture](0237-rate-limiter-high-level-architecture.md) next for what backs the `allow(...)` check — the storage layer and algorithm that make it fast enough to sit on every request's critical path.
