---
card: microservices
gi: 278
slug: distributed-rate-limiting-redis-backed
title: "Distributed rate limiting (Redis-backed)"
---

## 1. What it is

Distributed rate limiting is the practice of enforcing a rate limit across *multiple* instances of a service — for example, five replicas of the same API behind a load balancer — by storing the counter state in a shared, external store like Redis instead of in each instance's local memory. Every instance reads and updates the same shared counter, so the limit applies to the caller's total traffic across the whole fleet, not just the traffic that happened to land on one instance.

## 2. Why & when

An in-memory limiter like the ones built in [token bucket](0274-token-bucket-algorithm.md) or [fixed/sliding window counters](0276-fixed-window-sliding-window-counters.md) works correctly only when there is exactly one instance enforcing it. The moment a service scales horizontally to N instances behind a load balancer, each instance holds its *own* independent counter — a client sending requests that get spread round-robin across five instances, each with a local limit of 100/minute, can actually push up to 500/minute through the fleet as a whole, five times the intended limit.

Redis (or a similar fast, shared, atomic store) fixes this by centralizing the counter: every instance increments and checks the *same* key, so the limit is enforced against the caller's true aggregate traffic regardless of which instance handles any given request. Use distributed rate limiting whenever the service that needs the limit runs more than one instance, which is the normal case for any production microservice behind a load balancer.

## 3. Core concept

Each check-and-increment must be atomic to avoid a race where two instances both read the counter as "under limit" at the same moment and both increment, overshooting. Redis provides this atomicity via a single command (`INCR` with `EXPIRE`) or, for more complex logic like token bucket, a small Lua script executed atomically on the Redis server itself.

```java
// Conceptual Redis-backed fixed-window limiter (pseudocode over a Redis client).
class RedisRateLimiter {
    boolean allow(String clientId, int limit, long windowSeconds) {
        String key = "ratelimit:" + clientId + ":" + (System.currentTimeMillis() / (windowSeconds * 1000));
        long count = redis.incr(key);          // ATOMIC increment on the SHARED store
        if (count == 1) redis.expire(key, windowSeconds); // set TTL only on the FIRST hit
        return count <= limit;                 // decision based on the FLEET-WIDE total
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple service instances each check and increment the same shared counter key in Redis, so the rate limit applies to the caller's total traffic across the whole fleet rather than to each instance independently">
  <rect x="30" y="20" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="44" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Instance A</text>
  <rect x="30" y="80" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="104" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Instance B</text>
  <rect x="30" y="140" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="164" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Instance C</text>

  <line x1="120" y1="40" x2="280" y2="95" stroke="#8b949e" marker-end="url(#arr278)"/>
  <line x1="120" y1="100" x2="280" y2="100" stroke="#8b949e" marker-end="url(#arr278)"/>
  <line x1="120" y1="160" x2="280" y2="105" stroke="#8b949e" marker-end="url(#arr278)"/>

  <rect x="290" y="70" width="140" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Redis</text>
  <text x="360" y="112" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">shared counter (atomic INCR)</text>

  <text x="360" y="20" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">one true, fleet-wide count</text>
</svg>

All instances check and increment the same shared Redis key, so the limit reflects the caller's fleet-wide total.

## 5. Runnable example

Scenario: simulating multiple app instances with independent local counters that overshoot a fleet-wide limit, extended to route them through a shared in-memory stand-in for Redis to enforce the true limit, and finally handling the atomicity concern with a race-safe increment plus a TTL for automatic window expiry, mirroring what a real Redis `INCR`+`EXPIRE` (or Lua script) does.

### Level 1 — Basic

```java
// File: IndependentLocalLimitersOvershoot.java -- three "instances" each
// enforce the SAME limit independently, in local memory, and together
// overshoot the intended fleet-wide total.
public class IndependentLocalLimitersOvershoot {
    static class LocalLimiter {
        int count = 0;
        final int limit = 10;
        boolean allow() { if (count < limit) { count++; return true; } return false; }
    }

    public static void main(String[] args) {
        LocalLimiter instanceA = new LocalLimiter();
        LocalLimiter instanceB = new LocalLimiter();
        LocalLimiter instanceC = new LocalLimiter();
        LocalLimiter[] instances = { instanceA, instanceB, instanceC };

        int totalAllowed = 0;
        // 30 requests round-robin across 3 instances, each with its own limit of 10.
        for (int i = 0; i < 30; i++) {
            LocalLimiter chosen = instances[i % 3];
            if (chosen.allow()) totalAllowed++;
        }
        System.out.println("Intended fleet-wide limit: 10");
        System.out.println("Actual total allowed across all instances: " + totalAllowed);
    }
}
```

How to run: `java IndependentLocalLimitersOvershoot.java`

Thirty requests round-robin across three instances, each independently allowing up to 10. Since the requests are evenly distributed, all 30 get allowed (10 per instance) — three times the intended limit of 10 for the caller. This is the core problem: no shared state means no true fleet-wide enforcement.

### Level 2 — Intermediate

```java
// File: SharedCounterAcrossInstances.java -- a stand-in "Redis" object
// (a plain shared map here) is checked and incremented by every
// instance, correctly enforcing ONE fleet-wide limit of 10.
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

public class SharedCounterAcrossInstances {
    // Stands in for Redis: one shared store all instances talk to.
    static class FakeRedis {
        private final ConcurrentHashMap<String, AtomicInteger> counters = new ConcurrentHashMap<>();
        int incr(String key) {
            return counters.computeIfAbsent(key, k -> new AtomicInteger(0)).incrementAndGet();
        }
    }

    static class RedisBackedLimiter {
        final FakeRedis redis; final String clientId; final int limit;
        RedisBackedLimiter(FakeRedis redis, String clientId, int limit) {
            this.redis = redis; this.clientId = clientId; this.limit = limit;
        }
        boolean allow() {
            int count = redis.incr("ratelimit:" + clientId);
            return count <= limit;
        }
    }

    public static void main(String[] args) {
        FakeRedis redis = new FakeRedis();
        RedisBackedLimiter instanceA = new RedisBackedLimiter(redis, "client-42", 10);
        RedisBackedLimiter instanceB = new RedisBackedLimiter(redis, "client-42", 10);
        RedisBackedLimiter instanceC = new RedisBackedLimiter(redis, "client-42", 10);
        RedisBackedLimiter[] instances = { instanceA, instanceB, instanceC };

        int totalAllowed = 0;
        for (int i = 0; i < 30; i++) {
            if (instances[i % 3].allow()) totalAllowed++;
        }
        System.out.println("Intended fleet-wide limit: 10");
        System.out.println("Actual total allowed across all instances: " + totalAllowed);
    }
}
```

How to run: `java SharedCounterAcrossInstances.java`

Same 30 requests, same round-robin distribution across three logical instances, but now every instance shares one `FakeRedis` store and increments the *same* key (`"ratelimit:client-42"`). Only the first 10 of the 30 requests (across all instances combined) get `count <= limit`; the rest are correctly rejected. The total allowed now matches the intended limit of 10, regardless of how traffic is distributed across instances.

### Level 3 — Advanced

```java
// File: RaceSafeWindowedLimiter.java -- adds what a real Redis-backed
// limiter needs in production: an atomic check-and-increment under
// concurrent access from multiple threads (simulating multiple instances
// hitting Redis at once), plus a time-windowed key so old counters expire.
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.*;

public class RaceSafeWindowedLimiter {
    static class FakeRedis {
        private final ConcurrentHashMap<String, AtomicLong> counters = new ConcurrentHashMap<>();
        // Mirrors Redis's atomic INCR: safe even under concurrent callers.
        long incr(String key) {
            return counters.computeIfAbsent(key, k -> new AtomicLong(0)).incrementAndGet();
        }
    }

    static class WindowedRedisLimiter {
        final FakeRedis redis; final String clientId; final int limit; final long windowSeconds;
        WindowedRedisLimiter(FakeRedis redis, String clientId, int limit, long windowSeconds) {
            this.redis = redis; this.clientId = clientId; this.limit = limit; this.windowSeconds = windowSeconds;
        }
        boolean allow() {
            long windowBucket = System.currentTimeMillis() / (windowSeconds * 1000);
            String key = "ratelimit:" + clientId + ":" + windowBucket; // TTL-equivalent: key changes per window
            long count = redis.incr(key); // ATOMIC -- no lost updates even under a race
            return count <= limit;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        FakeRedis redis = new FakeRedis();
        WindowedRedisLimiter[] instances = new WindowedRedisLimiter[5];
        for (int i = 0; i < 5; i++) instances[i] = new WindowedRedisLimiter(redis, "client-42", 20, 1);

        ExecutorService pool = Executors.newFixedThreadPool(5);
        java.util.concurrent.atomic.AtomicInteger totalAllowed = new java.util.concurrent.atomic.AtomicInteger(0);
        CountDownLatch done = new CountDownLatch(100);

        // 100 requests fired CONCURRENTLY across 5 simulated instances --
        // the exact race condition a naive check-then-increment would lose.
        for (int i = 0; i < 100; i++) {
            WindowedRedisLimiter chosen = instances[i % 5];
            pool.submit(() -> {
                if (chosen.allow()) totalAllowed.incrementAndGet();
                done.countDown();
            });
        }
        done.await();
        pool.shutdown();
        System.out.println("Intended fleet-wide limit: 20 (per 1s window)");
        System.out.println("Actual total allowed under concurrent load: " + totalAllowed.get());
    }
}
```

How to run: `java RaceSafeWindowedLimiter.java`

One hundred requests fire concurrently (via a thread pool, simulating five real service instances each fielding traffic in parallel) against a shared limiter with a fleet-wide limit of 20 per 1-second window. Because `FakeRedis.incr` uses `AtomicLong.incrementAndGet`, which is a single atomic hardware-level operation, no two concurrent callers can both read the same "current count" and both proceed — exactly matching what Redis's real `INCR` command guarantees (Redis processes commands single-threaded internally, so `INCR` is inherently atomic even under massive concurrent client load). The result prints an allowed total of exactly 20, no more, no less, even though 100 requests arrived simultaneously across 5 concurrent "instances." The window-bucketed key (`windowBucket = now / windowSeconds`) also means old counters are naturally abandoned once the bucket changes — the real Redis equivalent uses `EXPIRE` to physically delete the key after the window passes, freeing memory.

## 6. Walkthrough

Trace `RaceSafeWindowedLimiter.main` in order. **First**, a shared `FakeRedis` store is created along with five `WindowedRedisLimiter` instances, all configured with the same `clientId`, `limit=20`, and `windowSeconds=1` — modeling five service replicas that all talk to the same Redis.

**Next**, 100 tasks are submitted to a 5-thread pool. Each task picks one of the five limiter "instances" (round-robin) and calls `allow()` concurrently with the other 99.

**Inside `allow()`**, each call first computes `windowBucket` from the current time — this groups all calls within the same second into the same Redis key, e.g. `"ratelimit:client-42:29384701"`. It then calls `redis.incr(key)`.

**Inside `FakeRedis.incr`**, `computeIfAbsent` retrieves (or lazily creates) the `AtomicLong` for that key, and `incrementAndGet()` atomically bumps it and returns the new value — this is the critical step: even with 100 threads calling this concurrently, the JVM's atomic compare-and-swap under the hood guarantees every increment is counted exactly once and no two threads ever see the same "before" value. This mirrors Redis's real behavior, where all commands against a single key execute one at a time on the Redis server.

**Back in `allow()`**, the returned count is compared against `limit` — the first 20 calls (across *all* threads and *all* five "instances" combined) that reach this point return `true`; the remaining 80 see a count already above 20 and return `false`.

**State transformation across layers**: a raw concurrent burst of 100 requests enters the thread pool (dispatch layer) → each is routed to one of five limiter objects standing in for service instances (routing layer) → each limiter delegates the actual accounting to the single shared `FakeRedis` (data layer) → the atomic increment there produces one true, fleet-wide sequence number per request → that number flows back up through the limiter (business-logic layer, compares against limit) → and finally back to the caller as a boolean allow/deny decision.

```
100 concurrent requests
   |
   v
[5 limiter "instances"] --all incr()--> [ONE shared FakeRedis counter, atomic]
   |
   v
first 20 (fleet-wide, order-independent) -> allowed
remaining 80 -> denied
```

## 7. Gotchas & takeaways

> A naive "read count, compare, then write count+1" sequence against a shared store is NOT safe under concurrency — two callers can both read the same stale count before either writes, both proceeding when only one should. The store operation itself must be atomic (Redis's `INCR`, or a Lua script for anything more complex than a plain counter).

- Local, per-instance limiters silently multiply the effective limit by the number of instances — always use a shared store once a service scales beyond one instance.
- Redis is the standard choice for this because `INCR` is atomic by construction and Redis operations are extremely low-latency, keeping the added round trip cheap.
- For algorithms more complex than a plain counter (e.g., a real token bucket with fractional refill), use a Redis Lua script (`EVAL`) so the entire read-modify-write sequence executes atomically on the Redis server in one round trip, rather than as several separate commands from the client that could race.
- Use a TTL (or a window-bucketed key, as shown) so old counters are automatically cleaned up — an ever-growing set of stale keys is a memory leak in the rate limiter's backing store.
