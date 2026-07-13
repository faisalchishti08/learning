---
card: microservices
gi: 164
slug: rate-limiting-at-the-edge
title: "Rate limiting at the edge"
---

## 1. What it is

Rate limiting at the edge caps how many requests a given client (identified by API key, IP address, or authenticated identity) can make within a time window, rejecting excess requests before they ever reach a backend service — a specific [cross-cutting concern](0163-cross-cutting-concerns-at-the-gateway-auth-logging-metrics.md) implemented once at the gateway rather than duplicated inside every backend.

## 2. Why & when

Without rate limiting, a single misbehaving client — a buggy retry loop, a scraper, or a malicious actor — can consume a disproportionate share of backend capacity, degrading service for every other legitimate client, and backend services have no inherent way to distinguish "unusually high but legitimate traffic" from "a client that needs to be throttled" without doing that accounting work themselves, repeatedly, in every service. Enforcing limits at the gateway means the check happens exactly once per request, before any backend resources are spent processing it, and the limiting logic and its configuration live in exactly one place rather than being duplicated (and inevitably drifting) across services.

Apply rate limiting at the edge for any externally-facing API where fair usage or backend capacity protection matters — which is nearly all production APIs serving external or third-party clients. Different limits for different client tiers (free vs. paid, internal vs. external) are a natural extension of the same mechanism, since the limit itself is just a configuration value keyed by client identity.

## 3. Core concept

A counter (or a more sophisticated bucket-based structure) tracks how many requests a given client identity has made within the current time window; each incoming request increments that counter and checks it against the client's configured limit, rejecting the request immediately if the limit is already exceeded, without any backend call happening at all.

```java
Map<String, Integer> requestCountsInWindow = new HashMap<>();

boolean allowRequest(String clientId, int limit) {
    int count = requestCountsInWindow.merge(clientId, 1, Integer::sum);
    return count <= limit; // false means: REJECT, never even call the backend
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client's requests are counted against its configured limit within the current time window at the gateway; requests within the limit are forwarded to the backend, while requests exceeding the limit are rejected before the backend is ever called" >
  <rect x="20" y="60" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="87" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Client requests</text>

  <rect x="230" y="45" width="180" height="75" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="68" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Rate limiter</text>
  <text x="320" y="84" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">count vs. limit,</text>
  <text x="320" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">per client, per window</text>

  <rect x="480" y="20" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Backend</text>

  <rect x="480" y="100" width="130" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="545" y="122" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">429 rejected</text>

  <line x1="150" y1="82" x2="228" y2="82" stroke="#8b949e" marker-end="url(#arr45)"/>
  <line x1="410" y1="70" x2="478" y2="40" stroke="#8b949e" marker-end="url(#arr45)"/>
  <line x1="410" y1="95" x2="478" y2="115" stroke="#8b949e" marker-end="url(#arr45)"/>

  <defs>
    <marker id="arr45" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Excess requests are turned away entirely at the edge, never spending any backend resources at all.

## 5. Runnable example

Scenario: a shared API endpoint that starts with no rate limiting at all (showing one client able to monopolize capacity), adds a fixed-window counter to cap each client's request rate, and finally upgrades to a token-bucket algorithm that allows brief bursts while still enforcing a sustained average rate, a common refinement over a simple fixed window.

### Level 1 — Basic

```java
// File: NoRateLimiting.java -- ANY client can send unlimited requests; one
// misbehaving client can monopolize backend capacity entirely.
public class NoRateLimiting {
    static int backendCallsHandled = 0;
    static String callBackend(String clientId) { backendCallsHandled++; return "response for " + clientId; }

    public static void main(String[] args) {
        // client-A sends 10 rapid requests; NOTHING stops it
        for (int i = 0; i < 10; i++) callBackend("client-A");
        // client-B, a NORMAL, well-behaved client, still gets served, but shares the SAME unlimited resource pool
        callBackend("client-B");

        System.out.println("Total backend calls handled: " + backendCallsHandled);
        System.out.println("client-A alone consumed 10x the capacity client-B used -- nothing prevented that imbalance.");
    }
}
```

**How to run:** `javac NoRateLimiting.java && java NoRateLimiting` (JDK 17+).

### Level 2 — Intermediate

```java
// File: FixedWindowRateLimit.java -- caps each client to a fixed number of
// requests per counting window, rejecting excess requests BEFORE the backend is called.
import java.util.*;

public class FixedWindowRateLimit {
    static Map<String, Integer> requestCounts = new HashMap<>();
    static int backendCallsHandled = 0;
    static int limitPerClient = 3;

    static String handleRequest(String clientId) {
        int count = requestCounts.merge(clientId, 1, Integer::sum);
        if (count > limitPerClient) {
            System.out.println("[rate limiter] REJECTED request " + count + " from " + clientId + " (limit=" + limitPerClient + ")");
            return "429 Too Many Requests";
        }
        System.out.println("[rate limiter] ALLOWED request " + count + "/" + limitPerClient + " from " + clientId);
        backendCallsHandled++;
        return "response for " + clientId;
    }

    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) handleRequest("client-A"); // 5 attempts, only 3 allowed
        handleRequest("client-B"); // client-B has its OWN independent count

        System.out.println("Total backend calls handled: " + backendCallsHandled + " (client-A capped at 3, client-B's 1 unaffected)");
    }
}
```

**How to run:** `javac FixedWindowRateLimit.java && java FixedWindowRateLimit` (JDK 17+).

Expected output:
```
[rate limiter] ALLOWED request 1/3 from client-A
[rate limiter] ALLOWED request 2/3 from client-A
[rate limiter] ALLOWED request 3/3 from client-A
[rate limiter] REJECTED request 4 from client-A (limit=3)
[rate limiter] REJECTED request 5 from client-A (limit=3)
[rate limiter] ALLOWED request 1/3 from client-B
Total backend calls handled: 4 (client-A capped at 3, client-B's 1 unaffected)
```

### Level 3 — Advanced

```java
// File: TokenBucketRateLimit.java -- allows a BURST up to the bucket's capacity,
// while still enforcing a sustained average rate via gradual token refill --
// a common refinement over a fixed window's harsh all-or-nothing cutoff.
import java.util.*;

public class TokenBucketRateLimit {
    static class TokenBucket {
        double tokens;
        double maxTokens;
        double refillRatePerSecond;
        long lastRefillTimeNanos;

        TokenBucket(double maxTokens, double refillRatePerSecond) {
            this.tokens = maxTokens; // starts FULL -- allows an immediate burst
            this.maxTokens = maxTokens;
            this.refillRatePerSecond = refillRatePerSecond;
            this.lastRefillTimeNanos = System.nanoTime();
        }

        boolean tryConsume() {
            refill();
            if (tokens >= 1.0) { tokens -= 1.0; return true; }
            return false;
        }

        void refill() {
            long now = System.nanoTime();
            double elapsedSeconds = (now - lastRefillTimeNanos) / 1_000_000_000.0;
            tokens = Math.min(maxTokens, tokens + elapsedSeconds * refillRatePerSecond); // GRADUAL refill over time
            lastRefillTimeNanos = now;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        TokenBucket bucket = new TokenBucket(3, 1.0); // capacity 3, refills 1 token/second

        // BURST: 3 rapid requests immediately allowed (bucket starts full)
        for (int i = 1; i <= 3; i++) System.out.println("Request " + i + " (immediate burst): allowed=" + bucket.tryConsume());
        // a 4th IMMEDIATE request is rejected -- bucket is now empty
        System.out.println("Request 4 (immediate, no wait): allowed=" + bucket.tryConsume());

        System.out.println("Waiting 1.5 seconds for tokens to refill...");
        Thread.sleep(1500); // ~1.5 tokens should refill at 1/second

        // a 5th request AFTER waiting is allowed again -- the SUSTAINED rate is still enforced, just not a hard cutoff
        System.out.println("Request 5 (after 1.5s wait): allowed=" + bucket.tryConsume());
        System.out.println("Request 6 (immediately after request 5): allowed=" + bucket.tryConsume());
    }
}
```

**How to run:** `javac TokenBucketRateLimit.java && java TokenBucketRateLimit` (JDK 17+).

Expected output:
```
Request 1 (immediate burst): allowed=true
Request 2 (immediate burst): allowed=true
Request 3 (immediate burst): allowed=true
Request 4 (immediate, no wait): allowed=false
Waiting 1.5 seconds for tokens to refill...
Request 5 (after 1.5s wait): allowed=true
Request 6 (immediately after request 5): allowed=false
```

## 6. Walkthrough

1. **Level 1** — `callBackend` is called ten times for `"client-A"` and once for `"client-B"` with no check anywhere limiting either client's request count; `backendCallsHandled` simply reflects every call made, with no mechanism protecting shared capacity from one client's disproportionate usage.
2. **Level 2, per-client counting** — `requestCounts.merge(clientId, 1, Integer::sum)` increments a counter keyed by `clientId`, meaning `"client-A"` and `"client-B"` each accumulate their own independent count, unaffected by each other's request volume.
3. **Level 2, the cutoff check** — `handleRequest` compares the freshly incremented `count` against `limitPerClient` (3); the first three calls for `"client-A"` pass this check and increment `backendCallsHandled`, while the fourth and fifth are rejected before `backendCallsHandled` is touched at all — the backend is never invoked for rejected requests.
4. **Level 2, the fixed window's limitation illustrated** — every one of `"client-A"`'s first three requests is allowed regardless of how close together in time they arrived, and every request after the third is rejected regardless of how much time has passed since the first — this is the "fixed window" characteristic: a hard, uniform cutoff with no notion of gradual recovery.
5. **Level 3, starting full and burst capacity** — `TokenBucket`'s constructor sets `tokens = maxTokens` immediately, so the first `maxTokens` (3) calls to `tryConsume` all succeed in rapid succession — a token bucket explicitly allows a burst up to its capacity, unlike a fixed window's per-window uniform cap applied identically regardless of arrival timing.
6. **Level 3, the refill mechanism** — `refill` computes `elapsedSeconds` since the last refill call and adds `elapsedSeconds * refillRatePerSecond` tokens back into the bucket, capped at `maxTokens`; this happens at the start of every `tryConsume` call, so the bucket's available capacity is always recalculated based on genuinely elapsed real time.
7. **Level 3, tracing the six requests** — requests 1 through 3 consume the bucket's initial 3 tokens, leaving it empty; request 4, called immediately after with essentially zero elapsed time, finds `tokens < 1.0` and is rejected; after `Thread.sleep(1500)`, roughly 1.5 tokens have refilled at the configured rate of 1/second, so request 5's call to `refill` brings `tokens` up to about 1.5, allowing it to succeed and leaving roughly 0.5 remaining; request 6, called immediately afterward with negligible additional elapsed time, finds `tokens < 1.0` again and is rejected — demonstrating that unlike Level 2's rigid window boundary, the token bucket smoothly and continuously enforces a sustained average rate while still permitting legitimate short bursts.

## 7. Gotchas & takeaways

> **Gotcha:** a fixed-window rate limiter has a well-known edge case at window boundaries — a client can send its full limit right at the end of one window and its full limit again right at the start of the next, achieving up to double the intended rate within a short span straddling the boundary; token bucket (and its close relative, the sliding-window log) avoid this specific problem by tracking capacity continuously rather than resetting abruptly at fixed boundaries.

- Rate limiting at the edge caps per-client request rates before backend resources are ever spent, protecting shared capacity from any single client's disproportionate usage.
- A fixed-window counter is simple to implement but applies a hard, uniform cutoff with a known boundary-straddling edge case that can allow brief rate spikes near window transitions.
- A token bucket allows legitimate short bursts up to its capacity while still enforcing a genuinely sustained average rate through continuous, gradual refill, avoiding the fixed window's rigid cutoff.
- Because the check happens entirely at the gateway, rejected requests never consume any backend processing capacity at all — the protection is real, not just accounted for after the fact.
- Rate limiting configuration (limits per client tier, burst capacity, refill rate) is naturally expressed as data keyed by client identity, making differentiated limits for different client tiers a direct extension of the same mechanism.
