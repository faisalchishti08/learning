---
card: system-design
gi: 147
slug: centralized-counter-redis-rate-limiting
title: Centralized counter (Redis) rate limiting
---

## 1. What it is

A **centralized counter** rate limiter stores each client's request count in one shared, fast store — almost always Redis — instead of in the memory of a single application server. Every instance of your service, no matter which one receives a given request, checks and increments the same counter in Redis. This makes the rate limit correct across a whole fleet of servers, not just correct on one machine.

## 2. Why & when

An in-process counter, like the ones shown for the [token bucket](0143-token-bucket.md) or [fixed-window counter](0145-fixed-window-counter.md), only limits requests that land on that one server. If a client's requests are load-balanced across ten servers, an in-process limiter set to "100 requests per minute" actually allows up to 1,000 requests per minute, ten times over — because each server tracks its own separate count. A centralized counter fixes this by making all ten servers check and update the same number. Use it whenever your service runs more than one instance and needs a rate limit that holds true across the whole fleet, which is true for nearly every production API.

## 3. Core concept

- **Shared state, not local state:** the count lives in Redis (or a similar fast, shared store), keyed by client ID plus the current window, so every app server sees the same number.
- **Atomicity is essential:** a naive "read count, check limit, write count+1" done as three separate steps has a race condition — two servers can both read the count just under the limit at the same instant, and both allow a request that together exceeds it. The check-and-increment must happen as a single atomic operation.
- **`INCR` + `EXPIRE`:** Redis's `INCR` command atomically increments a counter and returns the new value in one step; pairing it with `EXPIRE` on the key makes old windows clean themselves up automatically.
- **Lua scripts for multi-step atomicity:** when the logic needs more than a single atomic command (e.g. checking a limit before incrementing, or implementing a token bucket in Redis), a Lua script run via Redis's scripting feature executes multiple commands as one atomic unit, closing the race condition.
- **Latency tradeoff:** every request now needs a network round trip to Redis, adding latency compared to an in-process check — this cost buys you correctness across the fleet, which local counters cannot provide.

## 4. Diagram

```
   server A  \
   server B   >---- INCR ratelimit:{client}:{window} ----> Redis
   server C  /              (atomic, shared counter)          |
                                                          EXPIRE at
                                                          window end

   Without Redis: each server has its OWN counter -> limit effectively x N servers.
   With Redis: all servers share ONE counter -> the limit is enforced correctly, fleet-wide.
```
*Caption: every server instance increments the same Redis key atomically, so the rate limit is correct no matter which server a request lands on.*

## 5. Runnable example

This models the interaction with Redis in-process (no live Redis server needed to read the mechanism); the "How to run" note below shows what a real Redis client call looks like.

**Level 1 — Basic.** Model `INCR` as a single atomic operation shared across simulated "servers".

**Level 2 — Add `EXPIRE`-style window cleanup.** Old windows are cleared so the counter does not grow forever.

**Level 3 — Atomic check-then-increment via a "Lua script".** Combine the limit check and the increment into one atomic step, closing the race condition a naive two-step check has.

```java
// CentralizedCounterDemo.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class CentralizedCounterDemo {

    // Models a single shared Redis instance that every "server" talks to.
    static class FakeRedis {
        final Map<String, AtomicInteger> counters = new ConcurrentHashMap<>();
        final Map<String, Long> expiresAtMillis = new ConcurrentHashMap<>();

        // Level 3: models an atomic Lua script - "check limit, then INCR" as one step.
        synchronized boolean incrAndCheckLimit(String key, int limit, long windowMillis, long now) {
            Long expiry = expiresAtMillis.get(key);
            if (expiry == null || now >= expiry) {
                counters.put(key, new AtomicInteger(0)); // Level 2: window expired, reset
                expiresAtMillis.put(key, now + windowMillis);
            }
            int newCount = counters.get(key).incrementAndGet();
            return newCount <= limit; // atomic: no other server can slip in between check and incr
        }
    }

    public static void main(String[] args) throws InterruptedException {
        FakeRedis redis = new FakeRedis();
        String clientKey = "ratelimit:client-42:window-0";
        int limit = 5;
        long windowMillis = 1000;
        long now = System.currentTimeMillis();

        // Level 1: three separate "server" threads all hit the SAME Redis key.
        ExecutorService pool = Executors.newFixedThreadPool(3);
        AtomicInteger allowedCount = new AtomicInteger(0);
        List<Future<?>> futures = new ArrayList<>();
        for (int server = 1; server <= 3; server++) {
            final int serverId = server;
            futures.add(pool.submit(() -> {
                for (int i = 0; i < 3; i++) { // each server tries 3 requests -> 9 total, limit is 5
                    boolean allowed = redis.incrAndCheckLimit(clientKey, limit, windowMillis, now);
                    if (allowed) allowedCount.incrementAndGet();
                    System.out.println("server-" + serverId + " request " + i + ": " + (allowed ? "ALLOWED" : "REJECTED (429)"));
                }
            }));
        }
        for (Future<?> f : futures) f.get();
        pool.shutdown();

        System.out.println("total allowed across all servers: " + allowedCount.get() + " (limit was " + limit + ")");
    }
}
```

**How to run:** save as `CentralizedCounterDemo.java`, then run `java CentralizedCounterDemo.java`. (A real service would use a Redis client, e.g. Spring Data Redis's `RedisTemplate`, and call `redisTemplate.execute(luaScript, List.of(key), limit, windowMillis)`, with the Lua script doing the same check-and-increment against the real Redis server.)

## 6. Walkthrough

1. Three server threads are started, each simulating a different application instance receiving traffic for the same client, `client-42`.
2. Each thread calls `redis.incrAndCheckLimit` with the exact same `clientKey`, so every increment lands on the one shared `AtomicInteger` inside `FakeRedis.counters`, regardless of which "server" thread called it.
3. The `synchronized` keyword on `incrAndCheckLimit` models Redis's own single-threaded, atomic command execution: only one caller's check-and-increment can run at a time, so no two servers can both read the count as "4, under the limit of 5" and both increment past it.
4. As the 9 total requests (3 servers times 3 requests) run, the shared counter climbs from 0 up to 9, but `newCount <= limit` only stays true for the first 5 calls to actually execute, regardless of which server thread happened to get there first — the other 4 are rejected.
5. The final printed total confirms exactly 5 requests were allowed across all three servers combined, matching the configured `limit` — proving the rate limit held fleet-wide, not per-server (an in-process-only limiter would have allowed up to 5 per server, 15 total).

## 7. Gotchas & takeaways

> Gotcha: implementing this as separate "read the count", "check the limit", "write count+1" calls to Redis (three round trips) reintroduces the exact race condition a centralized counter is meant to fix — two servers can interleave those three steps and both slip a request through over the limit. Always use a single atomic Redis command (`INCR`) or a Lua script for anything needing more than one step.

- A rate limit is only correct across a fleet of servers if the counter lives in one shared, atomically-updated place — an in-process counter silently multiplies the limit by the number of servers.
- Redis's `INCR` is atomic by itself; anything needing a check *before* the increment needs a Lua script (or a similarly atomic primitive) to avoid a race condition.
- The cost of correctness is a network round trip to Redis on every rate-limit check, which is a real latency tradeoff to account for.
- Related concepts: [Per-user vs global quotas](0148-per-user-vs-global-quotas.md) (deciding what key this counter is keyed by), [Bucket4j for token-bucket rate limiting](0150-bucket4j-for-token-bucket-rate-limiting.md) (a library with a Redis-backed distributed mode), [Spring Cloud Gateway RequestRateLimiter (Redis)](0151-spring-cloud-gateway-requestratelimiter-redis.md) (this exact pattern, pre-built at the gateway layer).
