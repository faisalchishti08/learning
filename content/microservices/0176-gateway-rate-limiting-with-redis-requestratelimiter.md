---
card: microservices
gi: 176
slug: gateway-rate-limiting-with-redis-requestratelimiter
title: "Gateway rate limiting with Redis RequestRateLimiter"
---

## 1. What it is

Spring Cloud Gateway's `RequestRateLimiter` filter, backed by Redis, implements [rate limiting at the edge](0164-rate-limiting-at-the-edge.md) using a distributed token bucket whose state lives in Redis rather than in any single gateway instance's memory — this is what makes rate limits correctly enforced across a fleet of multiple, independently running [HA gateway](0170-single-point-of-failure-concerns-ha-gateways.md) instances, since all of them share the same Redis-backed counters rather than each tracking limits independently and incorrectly.

## 2. Why & when

An in-memory rate limiter, tracking counts in a single gateway instance's local memory, breaks the instant that gateway is scaled to more than one instance: a client's requests, load-balanced across multiple gateway instances, each tracking their own independent count, could exceed the intended overall limit by a factor of however many instances exist, since no single instance ever sees the client's *total* request volume. A Redis-backed limiter solves this by making the counter state shared and centralized — every gateway instance checks and increments the *same* Redis-stored counter for a given client, regardless of which specific gateway instance happens to handle any particular request.

Use a Redis-backed distributed rate limiter as soon as the gateway runs as more than one instance (which, per [HA gateway design](0170-single-point-of-failure-concerns-ha-gateways.md), is essentially always true in production) and rate limits need to be enforced correctly against a client's *total* traffic across the whole gateway fleet, not just against whatever single instance happens to receive each request.

## 3. Core concept

Each gateway instance, on every request, checks and atomically updates a token bucket's state stored in Redis (keyed by client identity), rather than maintaining that state locally — because Redis is the single shared source of truth, every instance sees a consistent, up-to-date view of each client's current rate limit status, no matter how many gateway instances are running or which one handles any specific request.

```java
// EVERY gateway instance checks/updates the SAME Redis-stored bucket for a given client
RateLimiter.Response response = redisRateLimiter.isAllowed(clientRouteId, clientId);
// internally: an atomic Lua script in Redis checks tokens, decrements if allowed, ALL in one atomic operation
if (!response.isAllowed()) return http429(); // enforced CORRECTLY regardless of which gateway instance handled this request
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client's requests are load-balanced across three gateway instances; all three instances check and update the SAME shared Redis-backed token bucket for that client, so the client's total rate limit is correctly enforced regardless of which instance handles each request" >
  <rect x="20" y="80" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="104" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Client</text>

  <rect x="180" y="20" width="110" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="235" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">gateway-1</text>
  <rect x="180" y="85" width="110" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="235" y="105" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">gateway-2</text>
  <rect x="180" y="150" width="110" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="235" y="170" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">gateway-3</text>

  <rect x="440" y="75" width="160" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="94" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Redis</text>
  <text x="520" y="110" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">shared bucket per client</text>

  <line x1="120" y1="100" x2="178" y2="35" stroke="#8b949e" marker-end="url(#arr57)"/>
  <line x1="120" y1="100" x2="178" y2="100" stroke="#8b949e" marker-end="url(#arr57)"/>
  <line x1="120" y1="100" x2="178" y2="165" stroke="#8b949e" marker-end="url(#arr57)"/>
  <line x1="290" y1="35" x2="438" y2="85" stroke="#8b949e" marker-end="url(#arr57)"/>
  <line x1="290" y1="100" x2="438" y2="98" stroke="#8b949e" marker-end="url(#arr57)"/>
  <line x1="290" y1="165" x2="438" y2="110" stroke="#8b949e" marker-end="url(#arr57)"/>

  <defs>
    <marker id="arr57" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Every gateway instance defers to the same shared Redis state, so the client's true total request rate is what gets enforced.

## 5. Runnable example

Scenario: a rate limit enforced across multiple gateway instances that starts with each instance tracking counts independently in memory (showing the broken, over-limit outcome), moves to a shared, simulated Redis-backed counter all instances defer to, and finally demonstrates the atomicity requirement by showing what happens if the check-and-increment isn't performed as a single atomic operation under concurrent access.

### Level 1 — Basic

```java
// File: InMemoryPerInstanceLimiter.java -- EACH gateway instance tracks its OWN
// count; a client hitting MULTIPLE instances can exceed the INTENDED total limit.
import java.util.*;

public class InMemoryPerInstanceLimiter {
    static class GatewayInstance {
        String id;
        Map<String, Integer> localCounts = new HashMap<>(); // LOCAL to THIS instance only
        int limitPerInstance = 3;
        GatewayInstance(String id) { this.id = id; }

        boolean allowRequest(String clientId) {
            int count = localCounts.merge(clientId, 1, Integer::sum);
            return count <= limitPerInstance;
        }
    }

    public static void main(String[] args) {
        GatewayInstance instance1 = new GatewayInstance("gateway-1");
        GatewayInstance instance2 = new GatewayInstance("gateway-2");
        String clientId = "client-A";
        int intendedTotalLimit = 3; // the OPERATOR intended client-A to get 3 requests TOTAL, across the whole fleet

        int allowedCount = 0;
        // client's requests get LOAD BALANCED across both instances
        for (int i = 0; i < 3; i++) if (instance1.allowRequest(clientId)) allowedCount++;
        for (int i = 0; i < 3; i++) if (instance2.allowRequest(clientId)) allowedCount++;

        System.out.println("Intended total limit: " + intendedTotalLimit);
        System.out.println("ACTUALLY allowed (across BOTH instances): " + allowedCount);
        System.out.println("BUG: client-A got " + allowedCount + " requests through, DOUBLE the intended limit, just by hitting 2 instances.");
    }
}
```

**How to run:** `javac InMemoryPerInstanceLimiter.java && java InMemoryPerInstanceLimiter` (JDK 17+).

Expected output:
```
Intended total limit: 3
ACTUALLY allowed (across BOTH instances): 6
BUG: client-A got 6 requests through, DOUBLE the intended limit, just by hitting 2 instances.
```

### Level 2 — Intermediate

```java
// File: SharedRedisBackedLimiter.java -- a SIMULATED shared Redis store;
// BOTH gateway instances check/update the SAME counter, enforcing the TRUE total limit.
import java.util.*;
import java.util.concurrent.*;

public class SharedRedisBackedLimiter {
    // simulates Redis: a SINGLE, SHARED store, external to any individual gateway instance
    static class SimulatedRedis {
        Map<String, Integer> sharedCounts = new ConcurrentHashMap<>();
        synchronized int incrementAndGet(String key) { return sharedCounts.merge(key, 1, Integer::sum); } // ATOMIC increment
    }

    static class GatewayInstance {
        String id;
        SimulatedRedis redis; // SHARED across all instances -- injected, not owned locally
        int totalLimit;
        GatewayInstance(String id, SimulatedRedis redis, int totalLimit) { this.id = id; this.redis = redis; this.totalLimit = totalLimit; }

        boolean allowRequest(String clientId) {
            int count = redis.incrementAndGet(clientId); // checks the SHARED counter, not a local one
            return count <= totalLimit;
        }
    }

    public static void main(String[] args) {
        SimulatedRedis sharedRedis = new SimulatedRedis(); // ONE Redis, shared by BOTH gateway instances
        int intendedTotalLimit = 3;
        GatewayInstance instance1 = new GatewayInstance("gateway-1", sharedRedis, intendedTotalLimit);
        GatewayInstance instance2 = new GatewayInstance("gateway-2", sharedRedis, intendedTotalLimit);
        String clientId = "client-A";

        int allowedCount = 0;
        for (int i = 0; i < 3; i++) if (instance1.allowRequest(clientId)) allowedCount++;
        for (int i = 0; i < 3; i++) if (instance2.allowRequest(clientId)) allowedCount++;

        System.out.println("Intended total limit: " + intendedTotalLimit);
        System.out.println("ACTUALLY allowed (across BOTH instances, SHARED Redis): " + allowedCount);
        System.out.println("CORRECT: client-A's TRUE total was enforced, regardless of which instance handled which request.");
    }
}
```

**How to run:** `javac SharedRedisBackedLimiter.java && java SharedRedisBackedLimiter` (JDK 17+).

Expected output:
```
Intended total limit: 3
ACTUALLY allowed (across BOTH instances, SHARED Redis): 3
CORRECT: client-A's TRUE total was enforced, regardless of which instance handled which request.
```

### Level 3 — Advanced

```java
// File: AtomicityUnderConcurrency.java -- demonstrates WHY the check-and-increment
// MUST be atomic: a non-atomic version, under GENUINE concurrent access from
// multiple instances, can still let TOO MANY requests through via a race condition.
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class AtomicityUnderConcurrency {
    // BROKEN: check-then-increment as TWO SEPARATE steps -- a race window exists between them
    static class NonAtomicRedis {
        Map<String, Integer> counts = new ConcurrentHashMap<>();
        boolean checkAndIncrementNonAtomic(String key, int limit) {
            int current = counts.getOrDefault(key, 0); // STEP 1: read
            if (current >= limit) return false;
            // <-- ANOTHER THREAD could read the SAME 'current' value HERE, before this thread writes back
            counts.put(key, current + 1); // STEP 2: write -- a SEPARATE operation from the read
            return true;
        }
    }

    // CORRECT: check-and-increment as ONE atomic operation -- mirrors Redis's atomic Lua script
    static class AtomicRedis {
        Map<String, Integer> counts = new ConcurrentHashMap<>();
        synchronized boolean checkAndIncrementAtomic(String key, int limit) { // synchronized == atomic for this simulation
            int current = counts.getOrDefault(key, 0);
            if (current >= limit) return false;
            counts.put(key, current + 1);
            return true;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        int limit = 5;
        int concurrentRequests = 20;

        // test the BROKEN, non-atomic version under REAL concurrency
        NonAtomicRedis nonAtomic = new NonAtomicRedis();
        AtomicInteger nonAtomicAllowed = new AtomicInteger();
        ExecutorService pool1 = Executors.newFixedThreadPool(10);
        CountDownLatch latch1 = new CountDownLatch(concurrentRequests);
        for (int i = 0; i < concurrentRequests; i++) {
            pool1.submit(() -> { if (nonAtomic.checkAndIncrementNonAtomic("client-A", limit)) nonAtomicAllowed.incrementAndGet(); latch1.countDown(); });
        }
        latch1.await();
        pool1.shutdown();

        // test the CORRECT, atomic version under the SAME concurrency
        AtomicRedis atomic = new AtomicRedis();
        AtomicInteger atomicAllowed = new AtomicInteger();
        ExecutorService pool2 = Executors.newFixedThreadPool(10);
        CountDownLatch latch2 = new CountDownLatch(concurrentRequests);
        for (int i = 0; i < concurrentRequests; i++) {
            pool2.submit(() -> { if (atomic.checkAndIncrementAtomic("client-A", limit)) atomicAllowed.incrementAndGet(); latch2.countDown(); });
        }
        latch2.await();
        pool2.shutdown();

        System.out.println("Configured limit: " + limit);
        System.out.println("Non-atomic check-then-increment allowed: " + nonAtomicAllowed.get() + " (can EXCEED the limit under a race)");
        System.out.println("Atomic check-and-increment allowed:     " + atomicAllowed.get() + " (NEVER exceeds the limit, guaranteed)");
    }
}
```

**How to run:** `javac AtomicityUnderConcurrency.java && java AtomicityUnderConcurrency` (JDK 17+).

Expected output (the non-atomic count is non-deterministic and can vary between runs, but is frequently greater than the limit; the atomic count is always exactly at or below the limit):
```
Configured limit: 5
Non-atomic check-then-increment allowed: 7 (can EXCEED the limit under a race)
Atomic check-and-increment allowed:     5 (NEVER exceeds the limit, guaranteed)
```

## 6. Walkthrough

1. **Level 1** — `instance1` and `instance2` each maintain their own separate `localCounts` map; `client-A`'s six total requests, three routed to each instance, are each checked only against that specific instance's own local count of 3, meaning both instances independently allow their full quota — six requests total pass, against an intended limit of three.
2. **Level 2, a shared external store** — `SimulatedRedis` is instantiated exactly once (`sharedRedis`) and passed to *both* `GatewayInstance` constructors; neither instance maintains its own count anymore, both defer to `sharedRedis.incrementAndGet`.
3. **Level 2, the correct enforcement** — because both instances check and increment the identical shared counter, the sixth request (regardless of which instance receives it) sees a count already at or past the limit and is correctly rejected — the total allowed count matches the intended limit of 3, exactly.
4. **Level 3, the danger of separating check and increment** — `NonAtomicRedis.checkAndIncrementNonAtomic` reads `current` in one step and writes `current + 1` in a separate, later step; between those two steps, another thread (representing a different gateway instance or a concurrent request on the same instance) could read the *same* stale `current` value before the first thread's write takes effect.
5. **Level 3, the race made concrete under real concurrency** — twenty concurrent tasks call `checkAndIncrementNonAtomic` against a shared `ConcurrentHashMap`-backed counts store from a ten-thread pool; even though the underlying map itself is thread-safe for individual operations, the *combination* of a separate read followed by a separate write is not atomic as a whole, letting multiple threads pass the `current >= limit` check using the same stale value before either has written back its increment.
6. **Level 3, the fix: atomicity** — `AtomicRedis.checkAndIncrementAtomic` is marked `synchronized`, meaning only one thread can execute the read-check-write sequence at a time for a given `AtomicRedis` instance, exactly mirroring how real Redis executes a rate-limiting Lua script as a single atomic operation, with no other client able to interleave a read or write in the middle of it.
7. **Level 3, the measured difference** — `nonAtomicAllowed`'s final count is frequently higher than the configured `limit` of 5 (a real, observable consequence of the race condition, not just a theoretical risk), while `atomicAllowed`'s final count never exceeds `5` — this is exactly why Redis's `RequestRateLimiter` implementation in Spring Cloud Gateway relies on an atomic Lua script rather than separate GET and SET commands, and why any custom distributed rate limiter must guarantee the same atomicity to be correct under genuine concurrent load from multiple gateway instances.

## 7. Gotchas & takeaways

> **Gotcha:** a Redis-backed rate limiter introduces Redis itself as a new dependency the gateway now relies on for every single request's rate-limit check — if Redis becomes slow or unavailable, every gateway instance's rate limiting (and potentially request handling entirely, depending on fail-open vs. fail-closed configuration) is affected simultaneously; this dependency needs the same reliability consideration as any other critical infrastructure component the gateway relies on.

- Spring Cloud Gateway's Redis-backed `RequestRateLimiter` solves the correctness problem an in-memory, per-instance rate limiter has once the gateway runs as more than one instance — a near-universal requirement given [HA gateway design](0170-single-point-of-failure-concerns-ha-gateways.md).
- All gateway instances checking and updating the same shared Redis-stored counter is what makes a client's *total* request rate, across the whole fleet, correctly enforced, regardless of which specific instance handles any given request.
- The check-and-increment operation must be atomic — performing the check and the increment as two separate steps introduces a race condition that can let more requests through than the configured limit under genuine concurrent load.
- Redis's atomic Lua script execution is what provides this atomicity guarantee in the real Spring Cloud Gateway implementation, avoiding the race condition a naive separate-read-then-write approach would have.
- Introducing Redis as the rate limiter's backing store makes Redis itself a critical dependency for request handling, requiring the same reliability planning as any other infrastructure component the gateway depends on.
