---
card: spring-cloud
gi: 46
slug: rate-limiting-requestratelimiter-redis
title: "Rate limiting (RequestRateLimiter / Redis)"
---

## 1. What it is

The `RequestRateLimiter` GatewayFilter caps how many requests a given caller (identified by a `KeyResolver` — often the client's API key, IP address, or user ID) can make in a given period, using a token-bucket algorithm backed by Redis, so the limit works correctly even across multiple Gateway instances sharing the same Redis store.

```yaml
filters:
  - name: RequestRateLimiter
    args:
      redis-rate-limiter.replenishRate: 10   # tokens added per second
      redis-rate-limiter.burstCapacity: 20    # bucket size -- max tokens that can accumulate
      key-resolver: "#{@apiKeyResolver}"
```

```java
@Bean
KeyResolver apiKeyResolver() {
    return exchange -> Mono.just(exchange.getRequest().getHeaders().getFirst("X-Api-Key"));
}
```

## 2. Why & when

Without rate limiting, a single misbehaving client (a buggy retry loop, a scraper, an abusive user) can consume disproportionate backend capacity, degrading service for every other caller. `RequestRateLimiter` enforces a per-key budget directly at the gateway, before requests ever reach a backend — and because it's Redis-backed rather than in-memory, the limit is correctly enforced across an entire fleet of gateway instances, not just per-instance (which would let a client multiply their effective limit by hitting different gateway nodes).

Reach for `RequestRateLimiter` when:

- Multiple external clients (API consumers, mobile app users, partner integrations) share backend capacity, and one client's excessive traffic shouldn't degrade service for everyone else.
- Gateway runs as multiple instances behind a load balancer — an in-memory-only rate limiter would let a client's requests spread across instances to evade the intended limit.
- You want burst tolerance (short spikes above the steady-state rate are fine) rather than a hard, unforgiving per-second cap — the token bucket model naturally supports this.

## 3. Core concept

```
 token bucket per key:
   - starts with `burstCapacity` tokens
   - refills at `replenishRate` tokens/second, capped at burstCapacity
   - each request consumes 1 token
   - request allowed if a token is available; rejected (429) if the bucket is empty
```

Steady traffic within `replenishRate` never depletes the bucket; short bursts are absorbed by whatever tokens have accumulated, up to `burstCapacity`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A token bucket refills at a steady rate and each request consumes one token, with requests rejected once the bucket is empty until it refills">
  <rect x="230" y="20" width="180" height="120" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="40" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">token bucket</text>
  <rect x="250" y="55" width="140" height="70" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <rect x="250" y="90" width="140" height="35" rx="4" fill="#6db33f60"/>
  <text x="320" y="112" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">tokens available</text>

  <line x1="320" y1="20" x2="320" y2="5" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="0" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">refills at replenishRate/s</text>

  <rect x="30" y="65" width="130" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="95" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">request arrives</text>
  <line x1="160" y1="80" x2="228" y2="80" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a46)"/>

  <rect x="480" y="40" width="130" height="30" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.2"/>
  <text x="545" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">token available -&gt; 200</text>
  <rect x="480" y="100" width="130" height="30" rx="6" fill="#e6494930" stroke="#e64949" stroke-width="1.2"/>
  <text x="545" y="120" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">bucket empty -&gt; 429</text>

  <line x1="410" y1="70" x2="478" y2="55" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a46)"/>
  <line x1="410" y1="100" x2="478" y2="115" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a46)"/>

  <defs><marker id="a46" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each request draws one token; availability of a token — not a raw request counter — decides pass or reject.

## 5. Runnable example

The scenario: rate-limit an API key calling `orders-service`. Start with a fixed per-key request counter (the naive, wrong approach), then implement a real token bucket with steady refill, then add multi-key isolation showing one caller's traffic never affects another's budget.

### Level 1 — Basic

A naive fixed counter — the problem a token bucket actually solves.

```java
import java.util.*;

public class RateLimitLevel1 {
    static Map<String, Integer> requestCounts = new HashMap<>();
    static final int LIMIT_PER_MINUTE = 5;

    static boolean allow(String apiKey) {
        int count = requestCounts.merge(apiKey, 1, Integer::sum);
        return count <= LIMIT_PER_MINUTE; // once the minute's count is exceeded, EVERYTHING is rejected until reset
    }

    public static void main(String[] args) {
        for (int i = 0; i < 7; i++) {
            System.out.println("request " + i + " -> " + (allow("key-1") ? "200" : "429"));
        }
    }
}
```

How to run: `java RateLimitLevel1.java`

A raw counter has no notion of *when* requests happened — it just counts up to a limit and then rejects everything until some external reset, which produces awkward all-or-nothing behavior at period boundaries instead of the smoother, continuously-refilling budget a token bucket provides.

### Level 2 — Intermediate

Implement a real token bucket: tokens refill continuously based on elapsed time, not in a lump-sum reset.

```java
import java.util.*;

public class RateLimitLevel2 {
    static class TokenBucket {
        double tokens;
        double replenishRate;   // tokens per second
        double burstCapacity;   // max tokens
        long lastRefillMs;

        TokenBucket(double replenishRate, double burstCapacity, long nowMs) {
            this.replenishRate = replenishRate;
            this.burstCapacity = burstCapacity;
            this.tokens = burstCapacity; // start full
            this.lastRefillMs = nowMs;
        }

        boolean tryConsume(long nowMs) {
            double elapsedSeconds = (nowMs - lastRefillMs) / 1000.0;
            tokens = Math.min(burstCapacity, tokens + elapsedSeconds * replenishRate); // refill based on elapsed time
            lastRefillMs = nowMs;
            if (tokens >= 1) {
                tokens -= 1;
                return true;
            }
            return false;
        }
    }

    public static void main(String[] args) {
        TokenBucket bucket = new TokenBucket(2.0, 5.0, 0); // 2 tokens/sec, burst up to 5

        long[] requestTimesMs = {0, 100, 200, 300, 400, 500, 3000}; // 6 rapid requests, then one much later
        for (int i = 0; i < requestTimesMs.length; i++) {
            boolean allowed = bucket.tryConsume(requestTimesMs[i]);
            System.out.println("t=" + requestTimesMs[i] + "ms -> " + (allowed ? "200" : "429"));
        }
    }
}
```

How to run: `java RateLimitLevel2.java`

`tryConsume` refills tokens proportionally to elapsed time on every call, then consumes one if available — the first 5 rapid requests (within the initial burst capacity) succeed, the 6th fails because the bucket is drained faster than it refills at this pace, and the request at `t=3000ms` succeeds again because nearly 2.5 seconds elapsed since the last check, refilling the bucket well past 1 token.

### Level 3 — Advanced

Add multiple independent keys, modeling how a Redis-backed limiter isolates each caller's budget — one client exhausting their limit never affects another's.

```java
import java.util.*;

public class RateLimitLevel3 {
    static class TokenBucket {
        double tokens, replenishRate, burstCapacity;
        long lastRefillMs;

        TokenBucket(double replenishRate, double burstCapacity, long nowMs) {
            this.replenishRate = replenishRate;
            this.burstCapacity = burstCapacity;
            this.tokens = burstCapacity;
            this.lastRefillMs = nowMs;
        }

        boolean tryConsume(long nowMs) {
            double elapsedSeconds = (nowMs - lastRefillMs) / 1000.0;
            tokens = Math.min(burstCapacity, tokens + elapsedSeconds * replenishRate);
            lastRefillMs = nowMs;
            if (tokens >= 1) { tokens -= 1; return true; }
            return false;
        }
    }

    // one bucket PER KEY -- this map is what would live in Redis in a real, multi-instance gateway deployment
    static Map<String, TokenBucket> buckets = new HashMap<>();

    static boolean allow(String apiKey, long nowMs) {
        TokenBucket bucket = buckets.computeIfAbsent(apiKey, k -> new TokenBucket(2.0, 5.0, nowMs));
        return bucket.tryConsume(nowMs);
    }

    public static void main(String[] args) {
        // key-1 makes 6 rapid requests, exhausting its bucket
        for (int i = 0; i < 6; i++) {
            System.out.println("key-1 request " + i + " -> " + (allow("key-1", i * 100) ? "200" : "429"));
        }

        // key-2, a completely different caller, makes its own first request at the same time -- unaffected by key-1
        System.out.println("key-2 request 0 -> " + (allow("key-2", 500) ? "200" : "429"));
    }
}
```

How to run: `java RateLimitLevel3.java`

`buckets` maps each `apiKey` to its own independent `TokenBucket` — `key-1` burning through its budget with six rapid requests has zero effect on `key-2`'s bucket, which starts fresh and full. This directly mirrors how a real Redis-backed `RequestRateLimiter` keys its rate-limit state: each distinct `KeyResolver` result (an API key, a user ID, an IP address) gets its own isolated bucket in Redis, correctly enforced across every gateway instance sharing that Redis store.

## 6. Walkthrough

Trace the sequence in Level 3.

1. The loop calls `allow("key-1", nowMs)` six times at `nowMs = 0, 100, 200, 300, 400, 500` — each call resolves (or creates, on the first call) `key-1`'s `TokenBucket`, initialized full at `5.0` tokens.
2. Requests `0` through `4` (at `t=0` through `t=400`) each consume roughly one token, with only a small amount of refill happening between them (100ms apart, at `2.0` tokens/sec, that's `0.2` tokens refilled per gap) — since the bucket started at `5.0`, all five succeed, draining it close to empty.
3. Request `5` (at `t=500`) finds the bucket has refilled only slightly since the last consumption and doesn't have a full token available, so `tryConsume` returns `false`, printing `429`.
4. `allow("key-2", 500)` runs — this is `key-2`'s very first request ever, so `computeIfAbsent` creates a brand-new `TokenBucket` for it, starting full at `5.0` tokens, completely independent of whatever happened to `key-1`'s bucket. The consumption succeeds immediately, printing `200`.
5. The key takeaway is visible directly in the output: `key-1` being rate-limited at `t=500` has no bearing whatsoever on `key-2`'s request at the exact same timestamp — the per-key isolation is what makes rate limiting fair across many independent callers sharing one gateway.

```
key-1's bucket: 5.0 -> 4.0 -> 3.0 -> 2.0 -> 1.0 -> (~0.2, refilled a bit) -> consume fails -> 429
key-2's bucket: (freshly created) 5.0 -> consume succeeds -> 200

key-1 and key-2 never share state -- one client's limit never borrows from another's
```

## 7. Gotchas & takeaways

> **Gotcha:** the `KeyResolver` choice determines what's actually being rate-limited — resolving by IP address means every user behind the same corporate NAT or mobile carrier shares one bucket, while resolving by API key or authenticated user ID isolates correctly per actual caller. Picking the wrong key can either rate-limit innocent co-located users together or fail to limit a single abusive caller who rotates IPs.

- Token bucket rate limiting naturally tolerates short bursts (up to `burstCapacity`) while still enforcing a steady-state average rate (`replenishRate`) — a better fit for real traffic patterns than a hard fixed-window counter.
- Redis-backing is what makes the limit correct across multiple gateway instances — an in-memory-only limiter would let a client multiply its effective limit by however many gateway instances it happens to hit.
- Each rate-limited key needs its own isolated bucket state — conflating keys (or choosing too coarse a key) either under- or over-limits the wrong set of callers.
- A `429 Too Many Requests` response should generally include a `Retry-After` header so well-behaved clients know when to try again, rather than immediately retrying and just consuming more of their own budget.
