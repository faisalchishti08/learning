---
card: system-design
gi: 150
slug: bucket4j-for-token-bucket-rate-limiting
title: Bucket4j for token-bucket rate limiting
---

## 1. What it is

**Bucket4j** is a Java library that implements the [token bucket](0143-token-bucket.md) algorithm as a tested, ready-to-use component, with both a purely in-memory mode and a distributed mode backed by Redis, Hazelcast, or another shared store. Instead of hand-writing the refill math and thread-safety shown in the token bucket's own example, you configure a `Bandwidth` (the bucket's capacity and refill rate) and ask Bucket4j whether to allow each request.

## 2. Why & when

Hand-rolled token bucket code is easy to get subtly wrong under concurrency — two threads both reading `availableTokens` and both deciding they can proceed, when only one token was actually left. Bucket4j solves this with proper atomic and thread-safe implementations, and adds features a hand-written version usually skips: multiple bandwidths on one bucket (e.g. a burst limit AND a sustained limit together), and a distributed mode so the bucket's state is correct across many application servers, similar in spirit to a [centralized Redis counter](0147-centralized-counter-redis-rate-limiting.md) but purpose-built for the token bucket algorithm specifically. Use it in any real Java or Spring Boot service instead of hand-writing bucket logic.

## 3. Core concept

- **`Bandwidth`:** defines one capacity-and-refill-rate rule, e.g. `Bandwidth.classic(100, Refill.intervally(100, Duration.ofMinutes(1)))` — 100 tokens, refilling fully every minute.
- **`Bucket`:** the runtime object you call per request; built from a `BucketConfiguration` holding one or more `Bandwidth` rules.
- **`tryConsume(n)`:** attempts to remove `n` tokens; returns `true`/`false` immediately, mirroring the hand-written bucket's `tryConsume` but with production-grade thread safety.
- **Multiple bandwidths on one bucket:** you can combine a tight burst limit (e.g. 20 tokens refilling instantly every second) with a looser sustained limit (e.g. 1,000 tokens refilling over an hour) on the *same* bucket — a request must satisfy every configured bandwidth to be allowed.
- **Distributed mode:** backing the bucket with a `ProxyManager` over Redis or Hazelcast makes the same bucket state visible and atomically updated across every server instance, the same correctness property a centralized Redis counter provides, but implemented specifically for this algorithm.

## 4. Diagram

```
   BucketConfiguration
     bandwidth 1: burst  = 20 tokens / 1 second   <- stops short spikes
     bandwidth 2: sustained = 1000 tokens / 1 hour <- stops sustained abuse

   request -> bucket.tryConsume(1)
                 |
        check bandwidth 1 AND bandwidth 2
                 |
        BOTH must have a token available
                 |
         yes -> allow, remove 1 token from each bandwidth
         no  -> reject (whichever bandwidth is exhausted)
```
*Caption: a single Bucket4j bucket can enforce more than one rate rule at once — a request must pass every configured bandwidth, not just one.*

## 5. Runnable example

**Level 1 — Basic.** Model a single-bandwidth bucket, mirroring Bucket4j's `tryConsume` API.

**Level 2 — Multiple bandwidths.** Combine a tight burst limit with a looser sustained limit on the same bucket.

**Level 3 — Thread-safe concurrent access.** Show the bucket giving a correct total under concurrent access from multiple threads, the property real Bucket4j provides out of the box.

```java
// Bucket4jDemo.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class Bucket4jDemo {

    // Models one Bucket4j "Bandwidth": a capacity that refills over time.
    static class Bandwidth {
        final long capacity;
        final double refillPerMillis;
        double available;
        long lastRefillMillis;

        Bandwidth(long capacity, long refillAmount, long refillPeriodMillis, long nowMillis) {
            this.capacity = capacity;
            this.refillPerMillis = refillAmount / (double) refillPeriodMillis;
            this.available = capacity;
            this.lastRefillMillis = nowMillis;
        }

        synchronized boolean tryConsume(int tokens, long nowMillis) {
            available = Math.min(capacity, available + (nowMillis - lastRefillMillis) * refillPerMillis);
            lastRefillMillis = nowMillis;
            if (available >= tokens) {
                available -= tokens;
                return true;
            }
            return false;
        }
    }

    // Models a Bucket4j "Bucket": all configured bandwidths must allow the request.
    static class Bucket {
        final List<Bandwidth> bandwidths;
        Bucket(List<Bandwidth> bandwidths) { this.bandwidths = bandwidths; }

        // Level 2: every bandwidth must have capacity, or the whole request is rejected.
        synchronized boolean tryConsume(int tokens, long nowMillis) {
            for (Bandwidth b : bandwidths) {
                if (!b.tryConsume(tokens, nowMillis)) return false;
            }
            return true;
        }
    }

    public static void main(String[] args) throws InterruptedException, ExecutionException {
        long now = System.currentTimeMillis();
        // Level 1 & 2: burst bandwidth (5 tokens / 1000ms) + sustained bandwidth (8 tokens / 5000ms)
        Bandwidth burst = new Bandwidth(5, 5, 1000, now);
        Bandwidth sustained = new Bandwidth(8, 8, 5000, now);
        Bucket bucket = new Bucket(List.of(burst, sustained));

        // Level 3: 10 concurrent requests from 4 threads, same bucket - result must still respect BOTH limits.
        ExecutorService pool = Executors.newFixedThreadPool(4);
        AtomicInteger allowed = new AtomicInteger(0);
        List<Future<?>> futures = new ArrayList<>();
        for (int i = 0; i < 10; i++) {
            futures.add(pool.submit(() -> {
                if (bucket.tryConsume(1, System.currentTimeMillis())) allowed.incrementAndGet();
            }));
        }
        for (Future<?> f : futures) f.get();
        pool.shutdown();

        System.out.println("allowed out of 10 concurrent requests: " + allowed.get() + " (burst bandwidth capped it at 5)");
    }
}
```

**How to run:** save as `Bucket4jDemo.java`, then run `java Bucket4jDemo.java`. (Real Bucket4j: add the `com.bucket4j:bucket4j-core` dependency, then `Bucket bucket = Bucket.builder().addLimit(Bandwidth.classic(5, Refill.intervally(5, Duration.ofSeconds(1)))).addLimit(Bandwidth.classic(8, Refill.intervally(8, Duration.ofSeconds(5)))).build();` and call `bucket.tryConsume(1)` per request.)

## 6. Walkthrough

1. The `Bucket` is built with two `Bandwidth` rules: a `burst` bandwidth (5 tokens, refilling over 1000ms) and a `sustained` bandwidth (8 tokens, refilling over 5000ms) — both start full.
2. 10 requests are submitted concurrently across 4 threads; each calls `bucket.tryConsume(1, ...)`, which is `synchronized`, so only one thread's check-and-decrement runs at a time against both bandwidths — the same atomicity real Bucket4j guarantees internally.
3. Inside `Bucket.tryConsume`, the loop checks `burst.tryConsume(1, ...)` first; since almost no time passes during the test, `burst`'s `available` drops from 5 straight to 0 across the first 5 successful calls.
4. The 6th call finds `burst.available < 1` (its refill is negligible in this short a time), so `burst.tryConsume` returns `false`, and `Bucket.tryConsume` returns `false` immediately — it never even checks `sustained`, because Bucket4j-style bandwidths are evaluated in order and any failing bandwidth rejects the whole request.
5. The final count confirms exactly 5 of the 10 concurrent requests were allowed — bound by the tighter `burst` bandwidth, not the looser `sustained` one — demonstrating that a request must satisfy every configured bandwidth, and that the result stays correct even under real concurrent access from multiple threads.

## 7. Gotchas & takeaways

> Gotcha: adding bandwidths that do not actually make sense together (e.g. a sustained limit numerically smaller than the burst limit's own capacity) means the sustained bandwidth becomes the *de facto* only limit, since it will always exhaust first — check that your bandwidths are ordered from tightest-and-shortest to loosest-and-longest, matching their intended purpose (burst control vs. sustained-abuse control).

- Bucket4j gives you the token bucket algorithm with production-grade thread safety, instead of a hand-rolled implementation that is easy to get subtly wrong under concurrency.
- Combining multiple bandwidths on one bucket lets you enforce a burst limit and a sustained limit simultaneously, with a single `tryConsume` call.
- Its distributed mode (Redis/Hazelcast-backed) extends the same correctness guarantee across a fleet of servers.
- Related concepts: [Token bucket](0143-token-bucket.md) (the algorithm Bucket4j implements), [Centralized counter (Redis) rate limiting](0147-centralized-counter-redis-rate-limiting.md) (the same fleet-wide correctness goal, achieved with raw Redis commands), [Spring Cloud Gateway RequestRateLimiter (Redis)](0151-spring-cloud-gateway-requestratelimiter-redis.md) (rate limiting applied at the API gateway layer instead of inside each service).
