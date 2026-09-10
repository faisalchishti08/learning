---
card: system-design
gi: 239
slug: rate-limiter-deep-dive-distributed-counter-accuracy-algorith
title: "Rate Limiter — deep-dive: distributed counter accuracy & algorithm choice"
---

## 1. What it is

This page covers the **deep-dive** facet of the **Rate Limiter** case study, focused on the one genuinely hard sub-problem: which counting algorithm actually implements `allow(...)` (from [API design](0236-rate-limiter-api-design.md)), writing into the `tokens`/`lastRefillAt` value shape (from [data model & schema](0238-rate-limiter-data-model-schema.md)), and what accuracy tradeoff each algorithm makes under the [non-functional requirements](0234-rate-limiter-non-functional-requirements.md)'s NFR-4 (bounded accuracy is acceptable).

## 2. Why & when

"Count requests and reject over the limit" sounds simple until you consider what happens at a window boundary — a naive fixed window lets a client burst up to 2x its limit right at the boundary between two windows, since each window's count resets independently with no memory of the previous one. This is the one part of the whole case study that is a genuine algorithm problem with real, well-known tradeoffs between the options — worth its own facet, the same way the [URL Shortener](0230-url-shortener-deep-dive-unique-key-generation-collisions.md) case study had a dedicated deep-dive for key generation.

## 3. Core concept

- **Fixed window counter.** Divide time into fixed windows (e.g. every 00:00-00:59, 01:00-01:59). Count requests within the current window; reset to zero at each boundary. Simple and cheap (one counter per window), but allows a burst of up to 2x the limit spanning a boundary — a client could send N requests at 00:59 and another N at 01:00, getting 2N requests in under 2 seconds of real time.
- **Sliding window log.** Store the timestamp of every individual request; count how many fall within the last window-length of time, computed fresh on every check. Perfectly accurate (no boundary burst problem), but memory cost grows with the number of requests per client per window, which can be significant at high limits.
- **Sliding window counter (a practical compromise).** Combine two adjacent fixed windows with a weighted estimate: `estimated count = current window's count + previous window's count * (overlap fraction)`. Much cheaper than a full log, and eliminates most of the fixed window's boundary-burst problem, at the cost of being an *approximation*, not an exact count — an acceptable tradeoff explicitly allowed by NFR-4.
- **Token bucket.** A bucket holds up to `capacity` tokens, refilling at a steady `rate` (tokens/second) up to that capacity. Each request consumes one token if available; if the bucket is empty, the request is rejected. This naturally supports FR-7's "allow short bursts" — a client that has not made requests recently has a full bucket and can burst up to `capacity` requests immediately, then is limited to the steady refill rate.
- **This case study chooses token bucket**, because it is the only algorithm among these that directly satisfies FR-7 (bounded bursting) while still being cheap (small, fixed state per client — just `tokens` and `lastRefillAt`, matching the schema from [data model & schema](0238-rate-limiter-data-model-schema.md)) and avoiding the fixed window's boundary problem entirely, since refill is continuous rather than reset-at-a-boundary.

## 4. Diagram

```
  FIXED WINDOW (boundary burst problem)         TOKEN BUCKET (this case study's choice)

  window: 00:00-00:59         01:00-01:59        capacity=10, refill rate=1 token/sec
  count:  0 -> 100 (limit)    0 -> 100 (limit)
                                                   t=0s:   bucket has 10 tokens (full, client idle)
  |------- 100 reqs --------|-- 100 reqs --|      t=0s:   burst of 10 requests -> bucket now EMPTY
  00:00                    00:59  01:00           t=0s:   11th request -> REJECTED (0 tokens)
              ^                                    t=5s:   bucket has refilled to 5 tokens
              |                                            (5 sec x 1 token/sec)
    200 requests fit in under 2 seconds           t=5s:   5 more requests allowed, bucket now 0
    of real time - the "boundary burst"           t=5s:   6th request -> REJECTED

                                                   (burst is bounded by CAPACITY, sustained rate
                                                    is bounded by REFILL RATE - both explicit,
                                                    tunable numbers, exactly matching FR-7)
```
*Caption: a fixed window's reset-to-zero at each boundary is what allows the 2x burst; token bucket's continuous refill and explicit capacity give the same "allow some burst" behavior deliberately and boundedly, rather than as an accidental flaw.*

## 5. Runnable example

**Level 1 — Basic.** Fixed window counter, showing the boundary-burst problem directly.

**Level 2 — Intermediate.** Token bucket algorithm: capacity, refill rate, consume-on-request.

**Level 3 — Advanced.** Token bucket under concurrent access, using the same atomic-check-then-consume discipline the [high-level architecture](0237-rate-limiter-high-level-architecture.md) requires, and a comparison showing token bucket does not have the fixed window's boundary problem.

```java
// RateLimiterAlgorithmDemo.java
import java.util.*;
import java.util.concurrent.atomic.*;

public class RateLimiterAlgorithmDemo {

    // ---------- Level 1: fixed window counter - has the boundary-burst problem ----------
    static class FixedWindowLimiter {
        int limit;
        long windowSeconds;
        Map<Long, Integer> countsByWindow = new HashMap<>(); // windowStart -> count

        FixedWindowLimiter(int limit, long windowSeconds) { this.limit = limit; this.windowSeconds = windowSeconds; }

        boolean allow(long nowSeconds) {
            long windowStart = (nowSeconds / windowSeconds) * windowSeconds;
            int count = countsByWindow.getOrDefault(windowStart, 0);
            if (count >= limit) return false;
            countsByWindow.put(windowStart, count + 1);
            return true;
        }
    }

    // ---------- Level 2 & 3: token bucket - this case study's chosen algorithm ----------
    static class TokenBucket {
        double capacity, tokens, refillRatePerSecond;
        long lastRefillAtMs;
        final Object lock = new Object(); // Level 3: guards the check-then-consume as one atomic step

        TokenBucket(double capacity, double refillRatePerSecond, long nowMs) {
            this.capacity = capacity; this.tokens = capacity; // start full
            this.refillRatePerSecond = refillRatePerSecond; this.lastRefillAtMs = nowMs;
        }

        void refill(long nowMs) {
            double elapsedSeconds = (nowMs - lastRefillAtMs) / 1000.0;
            double refillAmount = elapsedSeconds * refillRatePerSecond;
            tokens = Math.min(capacity, tokens + refillAmount);
            lastRefillAtMs = nowMs;
        }

        boolean allow(long nowMs) {
            synchronized (lock) { // atomic check-then-consume, as the high-level architecture requires
                refill(nowMs);
                if (tokens >= 1.0) {
                    tokens -= 1.0;
                    return true;
                }
                return false;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Level 1 - fixed window: 100/min limit, boundary-burst demonstrated at small scale:");
        FixedWindowLimiter fixedWindow = new FixedWindowLimiter(3, 60); // limit=3 for a readable demo
        long windowABoundary = 60; // window A: [0,60), window B: [60,120)
        int allowedInWindowA = 0, allowedInWindowB = 0;
        for (int i = 0; i < 3; i++) if (fixedWindow.allow(windowABoundary - 1)) allowedInWindowA++; // t=59s, still in window A
        for (int i = 0; i < 3; i++) if (fixedWindow.allow(windowABoundary)) allowedInWindowB++;     // t=60s, now window B
        System.out.println("  3 requests at t=59s (window A): " + allowedInWindowA + " allowed");
        System.out.println("  3 requests at t=60s (window B, 1 second later): " + allowedInWindowB + " allowed");
        System.out.println("  total: " + (allowedInWindowA + allowedInWindowB) +
            " requests allowed within 1 second of real time, for a limit of 3/window <- the boundary burst");

        System.out.println("\nLevel 2 - token bucket: capacity=5, refill=1 token/sec:");
        long t0 = 0;
        TokenBucket bucket = new TokenBucket(5, 1.0, t0);
        for (int i = 1; i <= 6; i++) {
            System.out.println("  request " + i + " at t=0s: " + (bucket.allow(t0) ? "ALLOWED" : "REJECTED") +
                " (tokens now: " + String.format("%.1f", bucket.tokens) + ")");
        }
        long t5 = 5000; // 5 seconds later
        System.out.println("  ...5 seconds pass, bucket refills...");
        boolean allowedAfterRefill = bucket.allow(t5);
        System.out.println("  request at t=5s: " + (allowedAfterRefill ? "ALLOWED" : "REJECTED") +
            " (tokens now: " + String.format("%.1f", bucket.tokens) + ")");

        System.out.println("\nLevel 3 - token bucket under concurrent access, atomic check-then-consume:");
        TokenBucket concurrentBucket = new TokenBucket(10, 1.0, 0);
        AtomicInteger allowedCount = new AtomicInteger(0);
        Thread[] threads = new Thread[20]; // 20 concurrent requests, capacity is only 10
        for (int i = 0; i < threads.length; i++) {
            threads[i] = new Thread(() -> { if (concurrentBucket.allow(0)) allowedCount.incrementAndGet(); });
        }
        for (Thread t : threads) t.start();
        for (Thread t : threads) t.join();
        System.out.println("  20 concurrent requests against a bucket with capacity=10: " +
            allowedCount.get() + " allowed (exactly the capacity, thanks to atomic synchronized access)");
    }
}
```

**How to run:** `java RateLimiterAlgorithmDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `FixedWindowLimiter` with `limit=3` is checked three times at `t=59` (still inside window `[0,60)`) — all three succeed, since the window's count starts at 0. Then it is checked three more times at `t=60` (now inside window `[60,120)`, a fresh window with its own zeroed count) — all three succeed again, because the window boundary reset the count entirely.
2. **The total, 6 requests allowed within roughly 1 second of real time, for a nominal limit of "3 per window," is exactly the boundary-burst problem** described in Part 3 — a client that times its requests around a window boundary can get up to 2x its intended limit, a real flaw in this otherwise simple algorithm.
3. **Level 2:** `TokenBucket` starts full (`tokens = capacity = 5`). The loop calls `bucket.allow(t0)` six times, all at the same timestamp `t0` (no time has passed, so no refill happens between calls). The first five succeed, each consuming one token and printing the decreasing token count; the sixth call finds `tokens < 1.0` and is rejected — this is the capacity bound (FR-7's "short burst") working exactly as designed: up to 5 requests immediately, then rejection.
4. **After `t5 = 5000` (5 seconds later), `bucket.allow(t5)` is called again.** Inside `allow`, `refill(t5)` computes `elapsedSeconds = 5.0` and `refillAmount = 5.0 * 1.0 = 5.0` tokens — but `Math.min(capacity, tokens + refillAmount)` caps this at `capacity = 5`, since the bucket was already at 0 and can refill at most back to full. The call succeeds, consuming one token, leaving `4.0` — proving the bucket genuinely refills over real elapsed time, at exactly the configured rate.
5. **Level 3** runs 20 threads concurrently against one `TokenBucket` with `capacity=10`, all calling `allow(0)` at essentially the same instant. Because `allow` wraps its check-and-consume in a `synchronized (lock)` block, each thread's check-then-decrement happens atomically with respect to every other thread — the final `allowedCount.get()` prints exactly `10`, matching the bucket's capacity precisely, with no race condition letting more than 10 through despite 20 threads racing simultaneously. This is the same atomicity guarantee the [high-level architecture](0237-rate-limiter-high-level-architecture.md) requires from the shared store in production — here demonstrated directly with a `synchronized` block as the in-process stand-in for Redis's atomic `INCR`/Lua-script behavior.

## 7. Gotchas & takeaways

> **Gotcha:** a token bucket implemented with a naive, non-atomic "check tokens, then separately decrement" sequence (instead of the single `synchronized` block shown in Level 3) reintroduces the exact race condition atomicity was meant to prevent — two concurrent requests can both read `tokens >= 1.0` as true before either decrements, letting both through when only one token was actually available. The check and the consume must be one indivisible operation, whether implemented as a language-level lock (as here) or a single atomic store operation (a Redis Lua script, in production).

- Fixed window is the simplest algorithm but has a real, well-known boundary-burst flaw — understand this tradeoff explicitly rather than defaulting to fixed window purely for its simplicity.
- Token bucket directly satisfies FR-7 (bounded bursting) as a first-class, tunable feature (via `capacity`) rather than as an accidental flaw (as the fixed window's boundary burst is) — this distinction, "designed-in burst tolerance" vs. "accidental burst bug," is the core reason this case study selects it.
- Atomicity of the check-and-consume step is non-negotiable for correctness under concurrency, exactly as Level 3 demonstrates — this requirement is what the [high-level architecture](0237-rate-limiter-high-level-architecture.md)'s shared, atomic-operation store exists to satisfy in a real, multi-instance deployment.
- See [Rate Limiter — scaling & tradeoffs](0240-rate-limiter-scaling-tradeoffs.md) next for how this token-bucket approach holds up (and what changes) as the system scales well past the original capacity estimation's numbers.
