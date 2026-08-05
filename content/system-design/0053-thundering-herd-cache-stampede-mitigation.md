---
card: system-design
gi: 53
slug: thundering-herd-cache-stampede-mitigation
title: "Thundering herd / cache stampede & mitigation"
---

## 1. What it is

A **thundering herd**, also called a **cache stampede**, happens when a popular cache entry expires (or the cache is cold-started) and a large number of concurrent requests all miss at the same instant. Every one of them independently goes to the database to reload the same data, hitting it with a sudden spike of duplicate load instead of just one reload.

## 2. Why & when

A cache normally protects the database from repeated load. A stampede is the moment that protection briefly disappears for one key — exactly when the database can least afford it, because the spike is concentrated and sudden rather than spread out. This happens naturally to any popular, TTL-based key: the more popular the key, the more concurrent requests are waiting right when it expires, so the worse the stampede. Watch for it whenever a database sees sharp, periodic load spikes that line up with a cache TTL.

## 3. Core concept

**Why it happens:** a plain cache-aside `get` has no coordination between concurrent callers. If a key is missing, every caller independently checks the cache, sees it is empty, and independently queries the database — there is nothing stopping ten simultaneous callers from doing ten simultaneous, identical database queries.

**Mitigation: request coalescing (a.k.a. single-flight).** The first caller to miss a key acquires a per-key lock and performs the reload; every other concurrent caller for that same key waits on the first caller's in-flight result instead of independently querying the database. Once the first caller finishes, all waiters receive the same freshly loaded value.

**Mitigation: early / jittered expiry.** Instead of every reader treating a key as valid until exactly the same expiry instant, add a small random jitter to when different processes consider it worth refreshing — this spreads reloads out over time instead of concentrating them at one instant.

**Mitigation: locking with a stale fallback.** If the reload is slow, let waiting callers briefly serve the just-expired (stale) value rather than blocking, trading a moment of staleness for protecting the database entirely.

## 4. Diagram

```
WITHOUT coalescing (10 concurrent requests, key just expired):
  Req1..Req10 --miss--> each independently queries Database   (10 identical queries)

WITH coalescing:
  Req1  --miss--> acquires lock for key --> queries Database --> stores result
  Req2..Req10 --miss--> lock held --> WAIT on Req1's in-flight result
  Req1 finishes --> Req2..Req10 all receive the same result, Database queried ONCE
```
*Caption: coalescing collapses N concurrent misses for the same key into a single database query.*

## 5. Runnable example

**Level 1 — Basic.** A naive cache where every concurrent miss independently queries the database, counting the duplicate load.

**Level 2 — Request coalescing.** The same scenario, but a per-key lock ensures only one thread queries the database; the rest wait for its result.

**Level 3 — Concurrent load test.** Run both versions with several threads racing on the same expired key to show the exact difference in database query count.

```java
// ThunderingHerd.java
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class ThunderingHerd {

    static final Map<String, String> database = Map.of("product:99", "Widget");
    static final AtomicInteger dbQueriesNaive = new AtomicInteger();
    static final AtomicInteger dbQueriesCoalesced = new AtomicInteger();

    static String slowDbQuery(String key, AtomicInteger counter) {
        counter.incrementAndGet();
        return database.get(key);
    }

    // Level 1: naive - every miss queries the database directly, no coordination.
    static String naiveGet(String key) throws InterruptedException {
        Thread.sleep(5); // simulate a slow query so misses overlap
        return slowDbQuery(key, dbQueriesNaive);
    }

    // Level 2: coalesced - one in-flight Future per key, shared by all waiters.
    static final Map<String, CompletableFuture<String>> inFlight = new ConcurrentHashMap<>();
    static String coalescedGet(String key) throws Exception {
        CompletableFuture<String> future = inFlight.computeIfAbsent(key, k ->
            CompletableFuture.supplyAsync(() -> {
                try { Thread.sleep(5); } catch (InterruptedException ignored) {}
                return slowDbQuery(k, dbQueriesCoalesced);
            })
        );
        String result = future.get();
        inFlight.remove(key, future); // clear once done, so a later miss can reload again
        return result;
    }

    public static void main(String[] args) throws Exception {
        int concurrentRequests = 10;

        // Level 3: naive version - 10 threads race on the same expired key.
        ExecutorService pool1 = Executors.newFixedThreadPool(concurrentRequests);
        CountDownLatch start1 = new CountDownLatch(1);
        for (int i = 0; i < concurrentRequests; i++) {
            pool1.submit(() -> {
                try { start1.await(); naiveGet("product:99"); } catch (Exception ignored) {}
            });
        }
        start1.countDown();
        pool1.shutdown();
        pool1.awaitTermination(2, TimeUnit.SECONDS);
        System.out.println("naive: database queries for 10 concurrent misses = " + dbQueriesNaive.get());

        // Same scenario, coalesced version.
        ExecutorService pool2 = Executors.newFixedThreadPool(concurrentRequests);
        CountDownLatch start2 = new CountDownLatch(1);
        for (int i = 0; i < concurrentRequests; i++) {
            pool2.submit(() -> {
                try { start2.await(); coalescedGet("product:99"); } catch (Exception ignored) {}
            });
        }
        start2.countDown();
        pool2.shutdown();
        pool2.awaitTermination(2, TimeUnit.SECONDS);
        System.out.println("coalesced: database queries for 10 concurrent misses = " + dbQueriesCoalesced.get());
    }
}
```

**How to run:** save as `ThunderingHerd.java`, then run `java ThunderingHerd.java`.

## 6. Walkthrough

1. All 10 threads in the naive pool wait on `start1`, then release together, so all 10 call `naiveGet("product:99")` at nearly the same instant.
2. Each `naiveGet` call sleeps briefly (simulating query latency) and then independently calls `slowDbQuery`, incrementing `dbQueriesNaive` every time — so the final count is `10`, one query per request.
3. In the coalesced pool, all 10 threads similarly release together and call `coalescedGet("product:99")`.
4. `inFlight.computeIfAbsent` ensures only the *first* thread to reach that line actually creates the `CompletableFuture` (and starts the simulated query); every other thread sees the future already present and simply attaches to it via `future.get()`.
5. Only the one thread that created the future calls `slowDbQuery`, so `dbQueriesCoalesced` ends at `1` — the other nine threads all receive the same result once it completes, without ever touching the database.

## 7. Gotchas & takeaways

> Gotcha: `computeIfAbsent` on a `ConcurrentHashMap` is what makes the coalescing atomic; using a plain `HashMap` with a separate "check, then create" step reintroduces a race where two threads could both create their own future, defeating the coalescing entirely.

- Coalescing turns N concurrent duplicate queries into 1, at the cost of the waiting threads' latency being bounded by the single query rather than running in parallel — which is the correct trade, since the query result is identical for all of them anyway.
- Jittered expiry and coalescing address the same problem from different angles and are often combined: jitter reduces how many keys expire at the exact same instant, coalescing handles whatever concurrent misses still happen.
- Related concepts: [Refresh-ahead cache](0049-refresh-ahead-cache.md) (avoids the stampede by never letting the entry fully expire under steady traffic), [Hot keys & key distribution](0052-hot-keys-key-distribution.md) (a related but distinct problem of sustained, not momentary, overload on one key).
