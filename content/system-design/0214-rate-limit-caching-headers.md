---
card: system-design
gi: 214
slug: rate-limit-caching-headers
title: Rate-limit & caching headers
---

## 1. What it is

**Rate-limit headers** (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`) tell a client how many requests it is allowed, how many it has left, and when the limit resets — communicated as HTTP headers on every response, not just when the limit is hit. **Caching headers** (`Cache-Control`, `ETag`, `Last-Modified`) tell a client and any intermediate cache (a browser, a CDN, a proxy) whether a response can be reused without asking the server again, and how to check if a cached copy is still valid.

## 2. Why & when

Without rate-limit headers, a client only discovers it hit a limit when a request is rejected — it has no way to pace itself proactively, so its natural behavior is to keep hammering the API until it gets blocked. Publishing the current limit and remaining count on every response, not just the rejection, lets well-behaved clients back off before they are throttled.

Without caching headers, a client re-fetches data it already has and that has not changed, wasting bandwidth and server capacity on both sides. `ETag` and `Cache-Control` let a client (or an intermediate cache) know precisely when it is safe to reuse a stored response and when it must ask the server again. Add rate-limit headers to any API with usage limits (which should be nearly all public APIs, to protect against abuse and runaway clients). Add caching headers to any endpoint whose data does not change on every single request — which includes most `GET` endpoints.

## 3. Core concept

- **`X-RateLimit-Limit` / `X-RateLimit-Remaining` / `X-RateLimit-Reset`.** Sent on *every* response, these tell the client the total allowance for the current window, how many requests remain, and when (as a Unix timestamp or seconds) the window resets — this is not a standardized header name across all APIs, but this pattern is the de facto convention.
- **`429 Too Many Requests` + `Retry-After`.** When the limit is exceeded, the server returns status `429` and a `Retry-After` header telling the client exactly how long to wait before retrying — the client should not guess or retry immediately.
- **`Cache-Control`.** Directives like `max-age=60` (cacheable for 60 seconds), `no-store` (never cache — for sensitive data), or `private` (cacheable only by the end client, not a shared proxy/CDN) control caching behavior declaratively.
- **`ETag` + conditional requests.** An `ETag` is an opaque identifier (often a hash) for the current version of a resource. A client that already has a cached copy sends `If-None-Match: <etag>` on its next request; if the resource has not changed, the server returns `304 Not Modified` with an empty body instead of re-sending the full response.
- **`Last-Modified` + `If-Modified-Since`.** A timestamp-based alternative to `ETag`, working the same way — the client sends back the last-known modification time, and the server replies `304` if nothing has changed since.

## 4. Diagram

```
  RATE LIMITING                              CONDITIONAL CACHING (ETag)

  GET /orders                                GET /orders/5
  <- 200 OK                                  <- 200 OK
     X-RateLimit-Limit: 100                     ETag: "v3-a1b2c3"
     X-RateLimit-Remaining: 63                   Cache-Control: max-age=60
     X-RateLimit-Reset: 1699999999                (client stores response + ETag)

  ... 63 more requests later ...             ... 60s later, client re-checks ...

  GET /orders                                GET /orders/5
  <- 429 Too Many Requests                    If-None-Match: "v3-a1b2c3"
     Retry-After: 42                          <- 304 Not Modified  (no body sent -
     (client MUST wait 42s                       resource unchanged, client's
      before retrying)                            cached copy is still valid)
```
*Caption: rate-limit headers make throttling predictable rather than a surprise; `ETag` plus a conditional request lets the server confirm "nothing changed" cheaply, without resending the full payload.*

## 5. Runnable example

**Level 1 — Basic.** A rate limiter that tracks remaining requests per client and exposes the standard headers, rejecting with `429` once exhausted.

**Level 2 — Intermediate.** An `ETag`-based cache: the server computes a hash of the resource, and a conditional request with a matching `If-None-Match` gets a cheap `304` instead of the full body.

**Level 3 — Advanced.** Combine both: a client makes repeated conditional requests, consuming rate-limit budget only on real fetches, and the resource changing invalidates the cached `ETag`.

```java
// RateLimitCachingDemo.java
import java.util.*;

public class RateLimitCachingDemo {

    // ---------- Level 1: rate limiting with standard headers ----------
    static class RateLimiter {
        int limit;
        Map<String, Integer> remainingByClient = new HashMap<>();
        RateLimiter(int limit) { this.limit = limit; }

        String handleRequest(String clientId) {
            int remaining = remainingByClient.getOrDefault(clientId, limit);
            if (remaining <= 0) {
                return "429 Too Many Requests, Retry-After: 42";
            }
            remaining--;
            remainingByClient.put(clientId, remaining);
            return "200 OK, X-RateLimit-Limit: " + limit + ", X-RateLimit-Remaining: " + remaining;
        }
    }

    // ---------- Level 2: ETag-based conditional caching ----------
    record Order(String id, double amount, String status) {}

    static class OrderResource {
        Order order;
        OrderResource(Order order) { this.order = order; }

        String etag() { return "\"" + Objects.hash(order) + "\""; } // hash of current content = ETag

        String handleGet(String ifNoneMatch) {
            String currentEtag = etag();
            if (currentEtag.equals(ifNoneMatch)) {
                return "304 Not Modified (ETag: " + currentEtag + ", no body sent)";
            }
            return "200 OK, ETag: " + currentEtag + ", body: " + order;
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - rate limiting, 3-request limit:");
        RateLimiter limiter = new RateLimiter(3);
        for (int i = 1; i <= 4; i++) {
            System.out.println("  request " + i + ": " + limiter.handleRequest("client-A"));
        }

        System.out.println("\nLevel 2 - ETag conditional caching:");
        OrderResource resource = new OrderResource(new Order("5", 42.00, "PENDING"));
        String firstResponse = resource.handleGet(null); // no cached ETag yet
        System.out.println("  first GET (no If-None-Match): " + firstResponse);
        String cachedEtag = resource.etag();
        System.out.println("  client stores ETag: " + cachedEtag);
        System.out.println("  second GET (If-None-Match: " + cachedEtag + "): " + resource.handleGet(cachedEtag));

        System.out.println("\nLevel 3 - resource changes, cached ETag becomes stale, THEN combine with rate limiting:");
        resource.order = new Order("5", 42.00, "SHIPPED"); // status changed - content changed
        System.out.println("  resource updated server-side (status: PENDING -> SHIPPED)");
        System.out.println("  GET with STALE If-None-Match: " + resource.handleGet(cachedEtag) +
            "  <- ETag no longer matches, full body returned");

        RateLimiter limiter2 = new RateLimiter(2);
        OrderResource resource2 = new OrderResource(new Order("6", 10.00, "PENDING"));
        String etag2 = null;
        for (int i = 1; i <= 3; i++) {
            String rateResult = limiter2.handleRequest("client-B");
            if (rateResult.startsWith("429")) {
                System.out.println("  request " + i + ": " + rateResult + " (never reached the cache check)");
                continue;
            }
            String cacheResult = resource2.handleGet(etag2);
            System.out.println("  request " + i + ": " + rateResult + " | " + cacheResult);
            etag2 = resource2.etag();
        }
    }
}
```

**How to run:** `java RateLimitCachingDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `limiter.handleRequest("client-A")` is called four times in a row. The first three calls find `remaining > 0`, decrement it, and return a `200 OK` with the current `X-RateLimit-Remaining` value counting down from 2 to 0. The **fourth** call finds `remaining <= 0` and returns `"429 Too Many Requests, Retry-After: 42"` — the client now knows exactly how long to wait, rather than guessing.
2. **Level 2:** `resource.handleGet(null)` is the client's first request, with no `If-None-Match` header (it has nothing cached yet). Since `null` never equals `currentEtag`, the method returns the full `200 OK` body along with the resource's current `ETag`.
3. The client stores that `ETag` (`cachedEtag`) and, on its next request, sends it back as `If-None-Match`. `resource.handleGet(cachedEtag)` now finds `currentEtag.equals(ifNoneMatch)` true — the resource has not changed since the client last fetched it — and returns `"304 Not Modified"` with no body at all.
4. **Level 3:** `resource.order` is reassigned to a new `Order` with `status: "SHIPPED"` instead of `"PENDING"` — the underlying data changed. Calling `resource.handleGet(cachedEtag)` again with the client's now-stale `ETag` finds `currentEtag` (recomputed from the new order) no longer equals `cachedEtag`, so it returns a full `200 OK` with the updated body — the change in content is exactly what invalidated the cache.
5. The final loop combines both mechanisms with a 2-request limit: requests 1 and 2 pass the rate check and proceed to the cache check (request 1 gets a full body since `etag2` starts `null`; request 2 sends back the `ETag` captured after request 1 and gets `304`). Request 3 is rejected by `limiter2` with `429` before the cache logic ever runs — the printed note makes explicit that a rate-limited request never reaches the cache check at all, since the server should reject cheaply, before doing any resource-specific work.

## 7. Gotchas & takeaways

> **Gotcha:** rate-limit counters must be safe under concurrent requests from the same client — a naive read-then-write (as shown here for clarity) has a race condition under real concurrency. Production rate limiters use atomic operations (e.g. Redis `INCR`) specifically to avoid two simultaneous requests both reading the same "remaining" value before either decrements it.

- Send rate-limit headers on every response, not just on the `429` — this lets well-behaved clients self-throttle before they are ever blocked.
- Always send `Retry-After` on a `429` (or a `503`) — a specific wait time is far more useful to a client than a bare rejection it must guess how to handle.
- Use `ETag` (content-based) when the resource's exact byte content matters for equality; use `Last-Modified` (time-based) when a coarser, timestamp-based check is good enough and cheaper to compute.
- These headers are what make [idempotency](0210-idempotency-safe-methods.md)-safe retries and [pagination](0209-pagination-filtering-sorting.md) efficient in practice — a client that respects `Retry-After` and caches with `ETag` puts far less load on the server than one that blindly polls.
