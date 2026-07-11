---
card: spring-cloud
gi: 57
slug: caching-health-checks
title: "Caching & health checks"
---

## 1. What it is

Spring Cloud LoadBalancer caches the resolved instance list for a configurable TTL (`spring.cloud.loadbalancer.cache.ttl`, default 35 seconds) rather than querying the discovery client on every single call, and separately supports an active health-check supplier (`HealthCheckServiceInstanceListSupplier`) that periodically pings instances directly, on top of whatever health status discovery itself reports.

```properties
spring.cloud.loadbalancer.cache.enabled=true
spring.cloud.loadbalancer.cache.ttl=35s
spring.cloud.loadbalancer.cache.capacity=256

spring.cloud.loadbalancer.health-check.path.billing-service=/actuator/health
spring.cloud.loadbalancer.health-check.interval=25s
```

## 2. Why & when

Querying discovery (Eureka/Consul/Zookeeper) on every single outbound call would add unnecessary latency and load on the discovery infrastructure, especially for a high-throughput caller making many requests per second to the same downstream service — the instance list rarely changes second-to-second, so caching it briefly is a straightforward win. Active health checking exists as a second, complementary safety net: even if a cached instance list is briefly stale, or discovery's own health reporting has a gap, LoadBalancer can still notice a specific instance is failing and avoid it directly.

Configure caching and health checks deliberately when:

- Call volume to a downstream service is high enough that per-call discovery lookups would add meaningful latency or load — caching amortizes that lookup cost across many calls within the TTL window.
- The default 35-second cache TTL is too slow or too fast for the deployment's actual instance churn rate — a fast-scaling environment might want a shorter TTL to pick up new instances sooner; a very stable environment might tolerate a longer one to reduce discovery load further.
- Discovery-reported health alone isn't precise enough — active health checking catches an instance that's still registered and heartbeating but is actually failing to serve real requests, closing a gap similar to (but independent of) the health-check-propagation card from the Service Discovery section.

## 3. Core concept

```
 without caching:  every call -> query discovery -> pick instance -> call it
                    (discovery queried N times for N calls)

 with caching:      first call -> query discovery -> cache result for TTL
                     subsequent calls within TTL -> read from cache -> pick instance -> call it
                     (discovery queried once per TTL window, not once per call)

 active health check (independent, periodic):
    every health-check-interval -> ping each cached instance directly
    -> instances failing the ping are marked unhealthy, removed from the pick pool immediately
```

Caching reduces how often the instance *list* is refreshed; active health checking is a separate, faster-reacting signal for individual instance *health* layered on top of it.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple calls within the cache TTL window reuse the same cached instance list, while a separate periodic health check independently marks individual instances unhealthy as needed">
  <rect x="30" y="20" width="580" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">cache TTL window (35s): call, call, call, call all reuse ONE discovery query's result</text>

  <rect x="30" y="100" width="270" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.3"/>
  <text x="165" y="124" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">cached list refreshed every TTL</text>

  <rect x="340" y="100" width="270" height="40" rx="6" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="475" y="124" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">active health check every interval</text>

  <text x="320" y="170" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">two independent clocks: list refresh (TTL) vs individual instance health (interval)</text>

  <defs><marker id="a57" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Caching amortizes the cost of resolving *which* instances exist; active health checks independently and continuously verify *whether* each one is actually reachable.

## 5. Runnable example

The scenario: model LoadBalancer's caching and active health-check layers for `billing-service`. Start with an uncached, always-fresh lookup, then add TTL-based caching, then add an independent periodic health check that removes a failing instance from the pool even mid-TTL-window.

### Level 1 — Basic

Uncached: every call queries discovery fresh.

```java
import java.util.*;

public class LoadBalancerCachingLevel1 {
    static int discoveryQueryCount = 0;

    static List<String> queryDiscovery() {
        discoveryQueryCount++;
        return List.of("10.0.2.1:8080", "10.0.2.2:8080", "10.0.2.3:8080");
    }

    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) {
            queryDiscovery(); // called on every single request
        }
        System.out.println("discovery queried " + discoveryQueryCount + " times for 5 calls"); // 5 -- wasteful
    }
}
```

How to run: `java LoadBalancerCachingLevel1.java`

Five calls means five separate discovery queries, even though the instance list almost certainly didn't change between any of them — pure overhead with no benefit.

### Level 2 — Intermediate

Add TTL-based caching: the instance list is only re-queried once the cache entry expires.

```java
import java.util.*;

public class LoadBalancerCachingLevel2 {
    static int discoveryQueryCount = 0;
    static List<String> cachedInstances = null;
    static long cachedAtMs = -1;
    static long ttlMs = 35_000;

    static List<String> queryDiscovery() {
        discoveryQueryCount++;
        return List.of("10.0.2.1:8080", "10.0.2.2:8080", "10.0.2.3:8080");
    }

    static List<String> getInstances(long nowMs) {
        if (cachedInstances == null || nowMs - cachedAtMs >= ttlMs) {
            cachedInstances = queryDiscovery();
            cachedAtMs = nowMs;
        }
        return cachedInstances;
    }

    public static void main(String[] args) {
        long[] callTimesMs = {0, 5_000, 10_000, 36_000, 40_000}; // 5 calls, spread across two TTL windows
        for (long t : callTimesMs) {
            getInstances(t);
        }
        System.out.println("discovery queried " + discoveryQueryCount + " times for 5 calls across ~40s"); // 2, not 5
    }
}
```

How to run: `java LoadBalancerCachingLevel2.java`

`getInstances` only calls `queryDiscovery` when the cache is empty or the TTL has elapsed — the first three calls (at `t=0, 5000, 10000`) all fall within the first 35-second TTL window and reuse the same cached result, while the call at `t=36000` triggers a fresh query since the TTL has expired, and `t=40000` then reuses *that* new cached result. Five calls collapse into just two real discovery queries.

### Level 3 — Advanced

Add an independent active health check that runs on its own interval, marking a specific instance unhealthy immediately — even in the middle of an otherwise-valid cache TTL window, showing the two mechanisms operate on separate clocks.

```java
import java.util.*;
import java.util.stream.Collectors;

public class LoadBalancerCachingLevel3 {
    static int discoveryQueryCount = 0;
    static List<String> cachedInstances = null;
    static long cachedAtMs = -1;
    static long ttlMs = 35_000;

    static Map<String, Boolean> activeHealthStatus = new HashMap<>(); // populated by the health-check loop
    static long healthCheckIntervalMs = 25_000;
    static long lastHealthCheckMs = -1;

    static List<String> queryDiscovery() {
        discoveryQueryCount++;
        return List.of("10.0.2.1:8080", "10.0.2.2:8080", "10.0.2.3:8080");
    }

    static List<String> getRawInstances(long nowMs) {
        if (cachedInstances == null || nowMs - cachedAtMs >= ttlMs) {
            cachedInstances = queryDiscovery();
            cachedAtMs = nowMs;
        }
        return cachedInstances;
    }

    static boolean pingInstance(String address, long nowMs) {
        return !(address.equals("10.0.2.2:8080") && nowMs >= 15_000); // .2 starts failing pings from t=15s onward
    }

    static void maybeRunHealthCheck(List<String> instances, long nowMs) {
        if (lastHealthCheckMs == -1 || nowMs - lastHealthCheckMs >= healthCheckIntervalMs) {
            for (String addr : instances) activeHealthStatus.put(addr, pingInstance(addr, nowMs));
            lastHealthCheckMs = nowMs;
            System.out.println("t=" + nowMs + "ms: health check ran -> " + activeHealthStatus);
        }
    }

    static List<String> getHealthyInstances(long nowMs) {
        List<String> raw = getRawInstances(nowMs);
        maybeRunHealthCheck(raw, nowMs);
        return raw.stream().filter(a -> activeHealthStatus.getOrDefault(a, true)).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        long[] callTimesMs = {0, 10_000, 20_000, 30_000};
        for (long t : callTimesMs) {
            System.out.println("t=" + t + "ms healthy instances: " + getHealthyInstances(t));
        }
    }
}
```

How to run: `java LoadBalancerCachingLevel3.java`

The cache TTL (`35s`) and health-check interval (`25s`) are different clocks entirely: the cached instance *list* doesn't need re-fetching across this whole run (all calls are within 35s of `t=0`), but the health check runs on its own 25-second cadence and, once it runs at `t=20000` (>= `lastHealthCheckMs + 25000` from the initial run at `t=0`), it pings each instance directly and discovers `.2` has been failing since `t=15000` — immediately removing it from `getHealthyInstances`'s result from that point forward, without needing the instance list cache itself to expire or refresh at all.

## 6. Walkthrough

Trace the four calls in Level 3.

1. `getHealthyInstances(0)` runs first — `getRawInstances(0)` finds no cache yet, calls `queryDiscovery()` (query count becomes `1`), and caches the three-instance list at `t=0`. `maybeRunHealthCheck` finds `lastHealthCheckMs == -1`, so it runs immediately: `pingInstance` for each address at `nowMs=0` — `.2`'s failure condition (`nowMs >= 15_000`) isn't yet true, so all three ping successfully. `getHealthyInstances` returns all three.
2. `getHealthyInstances(10_000)` runs next — the cache is still within its 35-second TTL (only 10 seconds elapsed), so `getRawInstances` reuses the cached list without querying discovery again. `maybeRunHealthCheck` checks `10_000 - 0 = 10_000`, which is `< 25_000` (the health-check interval), so it does *not* run again yet. All three instances remain marked healthy from the first check, so all three are still returned.
3. `getHealthyInstances(20_000)` runs — cache is still valid (20s < 35s TTL). `maybeRunHealthCheck` checks `20_000 - 0 = 20_000`, still `< 25_000`, so no new health check runs yet either. Interestingly, `.2` has actually started failing pings as of `t=15_000` in reality, but since the health check hasn't re-run, `activeHealthStatus` still reflects the stale `t=0` result — this is the real, bounded staleness window active health checking has, governed by its own interval.
4. `getHealthyInstances(30_000)` runs — cache is still valid (30s < 35s TTL, still no fresh discovery query). `maybeRunHealthCheck` now checks `30_000 - 0 = 30_000`, which *is* `>= 25_000`, so the health check finally re-runs: pinging each instance at `nowMs=30_000`, and this time `.2`'s failure condition (`30_000 >= 15_000`) is true, so `.2` is marked unhealthy. `getHealthyInstances` filters it out, returning only `.1` and `.3` from this call onward.

```
t=0:     cache miss -> discovery queried (count=1) -> health check runs -> all healthy
t=10000: cache hit (10s < 35s TTL) -> health check skipped (10s < 25s interval) -> all still "healthy" (stale)
t=20000: cache hit -> health check skipped (20s < 25s interval) -> still stale, .2 is actually down but not yet detected
t=30000: cache hit -> health check RUNS (30s >= 25s interval) -> .2 detected unhealthy -> excluded going forward
```

## 7. Gotchas & takeaways

> **Gotcha:** there is a real detection-lag window between an instance actually failing and the active health check next running (governed by `health-check.interval`, independent of the cache TTL) — in the trace above, `.2` was actually broken from `t=15000` but wasn't excluded from results until `t=30000`, a 15-second window where it could still be selected and calls to it would fail. Tuning the health-check interval tighter reduces this window at the cost of more frequent health-check traffic against every instance.

- Caching the instance *list* and actively checking instance *health* are two independent mechanisms with two independent clocks — don't assume a short cache TTL alone gives fast failure detection; that's the health-check interval's job.
- A longer cache TTL reduces load on the discovery infrastructure but delays picking up genuinely new instances; a shorter health-check interval improves failure detection speed but increases health-check traffic against every candidate instance.
- Both settings should scale with the deployment's actual dynamics — a fast-autoscaling environment likely wants both tighter than the defaults; a very stable, rarely-changing fleet can comfortably use longer intervals for both.
- Active health checking complements, rather than replaces, discovery's own health reporting (covered in the Service Discovery section) — it's a second, faster, more direct signal specifically about whether *this* LoadBalancer can actually still reach a given instance.
