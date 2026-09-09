---
card: system-design
gi: 149
slug: rate-limit-response-headers-429-handling
title: Rate-limit response headers & 429 handling
---

## 1. What it is

**Rate-limit response headers** are HTTP headers a server adds to every response, telling the caller how many requests they have left, when their quota resets, and (when rejected) how long to wait before trying again. **429 Too Many Requests** is the standard HTTP status code a server returns when a client has exceeded its rate limit. Together, these turn a rate limiter from a silent wall into a self-describing contract the caller can program against.

## 2. Why & when

Without headers, a client that gets rejected has no idea whether to retry in one second or one hour, or how close it was to the limit before it got rejected at all — it can only guess, which usually means retrying too aggressively (making the problem worse) or giving up too early. Standard headers let a well-behaved client back off exactly as long as needed, and even avoid hitting the limit in the first place by watching how many requests remain. Any public or internal API that enforces a rate limit should return these headers on every response, not only on rejections, so clients can self-regulate proactively.

## 3. Core concept

- **`X-RateLimit-Limit`:** the total number of requests allowed in the current window (or bucket capacity).
- **`X-RateLimit-Remaining`:** how many requests the client has left before hitting the limit, as of this response.
- **`X-RateLimit-Reset`:** when the limit resets, usually as a Unix timestamp or seconds-from-now.
- **`Retry-After`:** on a `429` response specifically, the standard HTTP header telling the client exactly how many seconds to wait before its next attempt — this is the header a correct client retry loop should honor.
- **Send headers on every response, not just rejections:** a client watching `X-RateLimit-Remaining` drop toward zero on *successful* responses can slow itself down proactively, before ever receiving a `429`.

## 4. Diagram

```
   client request
        |
        v
   +-----------------------------------------------+
   | server: check limiter                          |
   | allowed? -- yes --> 200 OK                     |
   |   headers: X-RateLimit-Limit: 100               |
   |            X-RateLimit-Remaining: 37             |
   |            X-RateLimit-Reset: 1717000060           |
   |                                                 |
   | allowed? -- no --> 429 Too Many Requests        |
   |   headers: X-RateLimit-Remaining: 0                |
   |            Retry-After: 23        <- seconds       |
   +-----------------------------------------------+
        |
        v
   client reads Retry-After, sleeps 23s, then retries
```
*Caption: every response carries enough information for the client to know exactly how close it is to the limit, and exactly how long to wait if it gets rejected.*

## 5. Runnable example

**Level 1 — Basic.** A rate limiter that computes the header values alongside its allow/reject decision.

**Level 2 — Build the actual header map for a response.** Model the response as a status code plus a header map, the way a servlet filter would build it.

**Level 3 — Client-side handling.** A retry loop that reads `Retry-After` from a `429` response and waits exactly that long before retrying, instead of guessing.

```java
// RateLimitHeadersDemo.java
import java.util.*;

public class RateLimitHeadersDemo {

    static class RateLimitResult {
        final boolean allowed;
        final int limit, remaining;
        final long resetEpochSeconds;
        final int retryAfterSeconds; // only meaningful when !allowed

        RateLimitResult(boolean allowed, int limit, int remaining, long resetEpochSeconds, int retryAfterSeconds) {
            this.allowed = allowed;
            this.limit = limit;
            this.remaining = remaining;
            this.resetEpochSeconds = resetEpochSeconds;
            this.retryAfterSeconds = retryAfterSeconds;
        }
    }

    // Level 1: a fixed-window limiter that also reports remaining count and reset time.
    static class HeaderAwareLimiter {
        final int limit;
        final long windowSeconds;
        int count = 0;
        long windowStartSeconds;

        HeaderAwareLimiter(int limit, long windowSeconds, long nowSeconds) {
            this.limit = limit;
            this.windowSeconds = windowSeconds;
            this.windowStartSeconds = nowSeconds;
        }

        RateLimitResult check(long nowSeconds) {
            if (nowSeconds - windowStartSeconds >= windowSeconds) {
                windowStartSeconds = nowSeconds;
                count = 0;
            }
            long resetAt = windowStartSeconds + windowSeconds;
            if (count >= limit) {
                int retryAfter = (int) (resetAt - nowSeconds);
                return new RateLimitResult(false, limit, 0, resetAt, retryAfter);
            }
            count++;
            return new RateLimitResult(true, limit, limit - count, resetAt, 0);
        }
    }

    // Level 2: build the actual HTTP status + header map, the way a server would.
    static Map<String, String> buildResponseHeaders(RateLimitResult r) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("X-RateLimit-Limit", String.valueOf(r.limit));
        headers.put("X-RateLimit-Remaining", String.valueOf(r.remaining));
        headers.put("X-RateLimit-Reset", String.valueOf(r.resetEpochSeconds));
        if (!r.allowed) {
            headers.put("Retry-After", String.valueOf(r.retryAfterSeconds));
        }
        return headers;
    }

    // Level 3: client-side retry loop that honors Retry-After instead of guessing.
    static void simulateClientCall(HeaderAwareLimiter limiter, long nowSeconds) {
        RateLimitResult result = limiter.check(nowSeconds);
        Map<String, String> headers = buildResponseHeaders(result);
        int status = result.allowed ? 200 : 429;
        System.out.println("t=" + nowSeconds + "s -> " + status + " " + (result.allowed ? "OK" : "Too Many Requests") + " " + headers);
        if (!result.allowed) {
            int waitSeconds = Integer.parseInt(headers.get("Retry-After"));
            System.out.println("  client: honoring Retry-After, will wait " + waitSeconds + "s before retrying");
        }
    }

    public static void main(String[] args) {
        long start = 1_000_000L;
        HeaderAwareLimiter limiter = new HeaderAwareLimiter(3, 10, start); // 3 requests per 10s window

        for (long t = start; t < start + 4; t++) {
            simulateClientCall(limiter, t); // 4 calls in 4 seconds - the 4th exceeds the limit of 3
        }
        // Client waited out the window; the next call after reset succeeds again.
        simulateClientCall(limiter, start + 10);
    }
}
```

**How to run:** save as `RateLimitHeadersDemo.java`, then run `java RateLimitHeadersDemo.java`.

## 6. Walkthrough

1. At `t=1000000`, `check` finds the window just started, allows the request, and returns `remaining = limit - count = 3 - 1 = 2`; `buildResponseHeaders` produces a `200`-style header map with `X-RateLimit-Remaining: 2`.
2. At `t+1` and `t+2`, the same happens, with `remaining` dropping to 1 then 0 as `count` climbs to 2 then 3.
3. At `t+3`, `check` finds `count = 3 >= limit = 3`, so it computes `retryAfter = resetAt - nowSeconds` (the window resets at `windowStartSeconds + 10`, and only 3 seconds have elapsed, so `retryAfter = 7`), and returns an unallowed result.
4. `buildResponseHeaders` sees `!r.allowed` and adds the `Retry-After` header on top of the usual three, and `simulateClientCall` prints the `429` status along with the client's decision to wait exactly `7` seconds — not an arbitrary guess.
5. The final call at `t+10` lands exactly at the window boundary; `check` finds `nowSeconds - windowStartSeconds >= windowSeconds` is true, resets `count` to 0, and allows the request again — showing the client's wait, guided by the earlier `Retry-After` value, was exactly long enough.

## 7. Gotchas & takeaways

> Gotcha: a client that ignores `Retry-After` and instead retries immediately (or on a fixed short delay) after a `429` will often get rejected again and again, adding load to an already-throttling server for no benefit — always parse and honor `Retry-After` in retry logic, ideally combined with the [exponential backoff and jitter](0135-retries-with-exponential-backoff-jitter.md) pattern for the case where the header is absent.

- Standard rate-limit headers turn a rejection into actionable information: how many requests are left, and exactly how long to wait.
- Sending these headers on *every* response, not just on `429`s, lets well-behaved clients self-throttle before ever being rejected.
- `Retry-After` is the one header a client's retry logic must actually read and obey — guessing the wait time defeats the purpose of the header existing.
- Related concepts: [Retries with exponential backoff & jitter](0135-retries-with-exponential-backoff-jitter.md) (what to do when `Retry-After` is missing), [Fixed-window counter](0145-fixed-window-counter.md) and [Token bucket](0143-token-bucket.md) (the limiters whose internal state these headers expose), [Spring Cloud Gateway RequestRateLimiter (Redis)](0151-spring-cloud-gateway-requestratelimiter-redis.md) (a gateway that sets these headers automatically).
