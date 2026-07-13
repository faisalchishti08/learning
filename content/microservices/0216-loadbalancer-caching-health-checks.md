---
card: microservices
gi: 216
slug: loadbalancer-caching-health-checks
title: "LoadBalancer caching & health checks"
---

## 1. What it is

Spring Cloud LoadBalancer optionally caches the instance list it gets from `DiscoveryClient` for a short, configurable time-to-live, and separately can layer a `HealthCheckServiceInstanceListSupplier` in front of the default supplier chain to actively probe instances and exclude unhealthy ones — two independent optimizations that both sit between raw discovery data and the final candidate list the selection algorithm chooses from.

## 2. Why & when

Querying `DiscoveryClient` on every single outbound call, as the uncached default effectively does, means a registry lookup for every call — fine for occasional calls but a real, avoidable overhead under high call volume, since the instance list rarely changes between two calls milliseconds apart. Caching the resolved instance list for a short TTL (a second or a few seconds, not minutes) removes this redundant lookup cost for the common case while still refreshing often enough that scale-up and scale-down events are reflected quickly. Separately, `DiscoveryClient`-reported instances reflect registration status, not necessarily current, real-time health — an instance can be registered and yet be temporarily failing or slow to respond, a gap a `HealthCheckServiceInstanceListSupplier` closes by actively probing each candidate's health endpoint before including it.

Enable caching in any application making a meaningfully high volume of load-balanced calls, where shaving repeated registry lookups off the hot path matters; leave it disabled for lower-volume cases where the extra millisecond of a fresh lookup is negligible. Layer in a `HealthCheckServiceInstanceListSupplier` whenever registered-but-unhealthy instances are a real risk in the target environment — the combination of caching and health-checking is a very common production configuration.

## 3. Core concept

Caching and health-checking are both implemented as `ServiceInstanceListSupplier` decorators — the same composable extension point used for [custom candidate filtering](0214-custom-loadbalancer-configuration-serviceinstancelistsupplie.md) — meaning both can be enabled together, and the order they're composed in determines whether health checks run against cached data or trigger their own fresher lookups.

```java
// CACHING supplier -- wraps a delegate, reuses its result for a short TTL instead of calling it every time
class CachingServiceInstanceListSupplier implements ServiceInstanceListSupplier {
    ServiceInstanceListSupplier delegate;
    List<ServiceInstance> cached; long cachedAt; long ttlMillis = 2000; // e.g. a 2-second TTL

    public Flux<List<ServiceInstance>> get() {
        long now = System.currentTimeMillis();
        if (cached != null && now - cachedAt < ttlMillis) return Flux.just(cached); // CACHE HIT
        return delegate.get().doOnNext(list -> { cached = list; cachedAt = now; }); // CACHE MISS -- refresh
    }
}

// HEALTH-CHECK supplier -- wraps a delegate, probes each instance, EXCLUDES failing ones
class HealthCheckServiceInstanceListSupplier implements ServiceInstanceListSupplier {
    ServiceInstanceListSupplier delegate;
    public Flux<List<ServiceInstance>> get() {
        return delegate.get().map(instances -> instances.stream().filter(this::isHealthy).toList());
    }
    boolean isHealthy(ServiceInstance i) { /* probe i's /actuator/health endpoint */ return true; }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Discovery client feeds a caching supplier, which serves cached results within its TTL or refreshes from discovery, and its output then passes through a health-check supplier that probes and filters instances before the final list reaches selection" >
  <rect x="15" y="70" width="110" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">DiscoveryClient</text>
  <text x="70" y="103" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">raw instance list</text>

  <rect x="170" y="60" width="150" height="65" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="245" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Caching supplier</text>
  <text x="245" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">hit: cached copy</text>
  <text x="245" y="111" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">miss: refresh + store</text>

  <rect x="365" y="60" width="150" height="65" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Health-check supplier</text>
  <text x="440" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">probes each instance</text>
  <text x="440" y="111" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">drops unhealthy ones</text>

  <rect x="555" y="70" width="70" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="590" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Selection</text>

  <line x1="125" y1="92" x2="168" y2="92" stroke="#8b949e" marker-end="url(#arr216)"/>
  <line x1="320" y1="92" x2="363" y2="92" stroke="#8b949e" marker-end="url(#arr216)"/>
  <line x1="515" y1="92" x2="553" y2="92" stroke="#8b949e" marker-end="url(#arr216)"/>

  <defs>
    <marker id="arr216" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Caching avoids redundant discovery lookups; health-checking layers on top to exclude instances that are registered but currently unhealthy.

## 5. Runnable example

Scenario: a call counter tracks how many times the "expensive" discovery lookup actually runs, first with no caching (every call triggers a lookup), then with TTL-based caching added (most calls reuse a cached result), and finally with a health check layered on top that excludes an instance which starts failing mid-run — the SAME underlying lookup-counting mechanism used throughout to make the optimization's effect directly observable.

### Level 1 — Basic

```java
// File: UncachedLookupEveryCall.java -- EVERY call triggers a fresh,
// "expensive" discovery lookup -- the counter proves this.
import java.util.*;

public class UncachedLookupEveryCall {
    record ServiceInstance(String host, boolean healthy) {}
    static int lookupCount = 0;

    static List<ServiceInstance> expensiveDiscoveryLookup() {
        lookupCount++; // counts EVERY call -- simulates real registry lookup cost
        return List.of(new ServiceInstance("10.0.1.5", true), new ServiceInstance("10.0.1.6", true));
    }

    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) expensiveDiscoveryLookup(); // 5 outbound calls, 5 SEPARATE lookups
        System.out.println("Calls made: 5, discovery lookups performed: " + lookupCount);
    }
}
```

**How to run:** `javac UncachedLookupEveryCall.java && java UncachedLookupEveryCall` (JDK 17+).

Expected output:
```
Calls made: 5, discovery lookups performed: 5
```

### Level 2 — Intermediate

```java
// File: CachedLookupWithTtl.java -- the SAME 5 calls, but now cached with
// a TTL -- most reuse the cached list instead of re-querying.
import java.util.*;

public class CachedLookupWithTtl {
    record ServiceInstance(String host, boolean healthy) {}
    static int lookupCount = 0;
    static List<ServiceInstance> cached; static long cachedAt = -1; static final long TTL_MILLIS = 100;

    static List<ServiceInstance> expensiveDiscoveryLookup() {
        lookupCount++;
        return List.of(new ServiceInstance("10.0.1.5", true), new ServiceInstance("10.0.1.6", true));
    }

    static List<ServiceInstance> cachedGetInstances(long simulatedNow) {
        if (cached != null && simulatedNow - cachedAt < TTL_MILLIS) return cached; // CACHE HIT -- no lookup
        cached = expensiveDiscoveryLookup(); cachedAt = simulatedNow; // CACHE MISS -- refresh
        return cached;
    }

    public static void main(String[] args) {
        long[] callTimes = {0, 10, 20, 150, 160}; // 5 calls; only the 4th falls outside the 100ms TTL
        for (long t : callTimes) cachedGetInstances(t);
        System.out.println("Calls made: 5, discovery lookups performed: " + lookupCount + " (cache absorbed the rest)");
    }
}
```

**How to run:** `javac CachedLookupWithTtl.java && java CachedLookupWithTtl` (JDK 17+).

Expected output:
```
Calls made: 5, discovery lookups performed: 2 (cache absorbed the rest)
```

### Level 3 — Advanced

```java
// File: CachedPlusHealthCheckedLookup.java -- caching AND health-checking
// layered together; an instance that starts failing mid-run gets excluded
// from the final candidate list even though it's still cached/registered.
import java.util.*;

public class CachedPlusHealthCheckedLookup {
    record ServiceInstance(String host, boolean healthyAtProbeTime) {}
    static int lookupCount = 0; static int healthProbeCount = 0;
    static List<ServiceInstance> cached; static long cachedAt = -1; static final long TTL_MILLIS = 100;
    static boolean instanceBFailing = false; // toggled mid-run to simulate a real failure

    static List<ServiceInstance> expensiveDiscoveryLookup() {
        lookupCount++;
        return List.of(new ServiceInstance("10.0.1.5", true), new ServiceInstance("10.0.1.6", !instanceBFailing));
    }

    static List<ServiceInstance> cachedGetInstances(long simulatedNow) {
        if (cached != null && simulatedNow - cachedAt < TTL_MILLIS) return cached;
        cached = expensiveDiscoveryLookup(); cachedAt = simulatedNow;
        return cached;
    }

    // health check runs on EVERY call, even against cached data -- caching and health-checking are INDEPENDENT layers
    static List<ServiceInstance> healthFilteredInstances(long simulatedNow) {
        List<ServiceInstance> candidates = cachedGetInstances(simulatedNow);
        List<ServiceInstance> healthy = new ArrayList<>();
        for (ServiceInstance i : candidates) {
            healthProbeCount++;
            boolean stillHealthy = i.host().equals("10.0.1.6") ? !instanceBFailing : true; // re-probe LIVE health
            if (stillHealthy) healthy.add(i);
        }
        return healthy;
    }

    public static void main(String[] args) {
        System.out.println("Before instance B fails: " + healthFilteredInstances(0));
        instanceBFailing = true; // instance B starts failing, but cache entry is still fresh (within TTL)
        System.out.println("After instance B fails (cache still fresh):  " + healthFilteredInstances(10));
        System.out.println("Discovery lookups: " + lookupCount + ", health probes: " + healthProbeCount);
        System.out.println("Health checks excluded the failing instance WITHOUT needing a fresh discovery lookup.");
    }
}
```

**How to run:** `javac CachedPlusHealthCheckedLookup.java && java CachedPlusHealthCheckedLookup` (JDK 17+).

Expected output:
```
Before instance B fails: [ServiceInstance[host=10.0.1.5, healthyAtProbeTime=true], ServiceInstance[host=10.0.1.6, healthyAtProbeTime=true]]
After instance B fails (cache still fresh):  [ServiceInstance[host=10.0.1.5, healthyAtProbeTime=true]]
Discovery lookups: 1, health probes: 4
Health checks excluded the failing instance WITHOUT needing a fresh discovery lookup.
```

## 6. Walkthrough

1. **Level 1, the uncached baseline** — `expensiveDiscoveryLookup` increments `lookupCount` on every invocation, and `main` calls it directly 5 times, so `lookupCount` ends at exactly 5 — one lookup per call, with no reuse whatsoever.
2. **Level 2, introducing the TTL cache** — `cachedGetInstances` checks whether `cached` exists and is still within `TTL_MILLIS` of `cachedAt`; if so it returns `cached` directly (a cache hit, no lookup performed), otherwise it calls `expensiveDiscoveryLookup` and records the new `cachedAt` timestamp (a cache miss).
3. **Level 2, why only 2 lookups happen** — of the five simulated call times (`0, 10, 20, 150, 160`), the calls at `10` and `20` fall within 100ms of the cache entry created at `0`, so they hit the cache; the call at `150` is outside the TTL, forcing a refresh (second lookup, new `cachedAt = 150`); the call at `160` then falls within 100ms of *that* refreshed entry, so it hits the cache again — two lookups total instead of five.
4. **Level 3, layering health-checking on top of caching** — `healthFilteredInstances` calls `cachedGetInstances` to get the (possibly cached) candidate list, then independently re-probes each candidate's live health via `healthProbeCount`-incrementing checks, filtering out anything currently unhealthy — this probing happens on *every* call, regardless of whether the underlying instance list itself came from cache or a fresh lookup.
5. **Level 3, the failure and its detection** — `instanceBFailing` is set to `true` between the two `healthFilteredInstances` calls in `main`, simulating instance B degrading; because the cache entry from time `0` is still within its TTL at time `10`, `cachedGetInstances` returns the *same* cached instance list (still showing B as originally healthy) — but the *health probe*, which runs independently on each call, catches B's now-failing state and excludes it from the returned list regardless.
6. **Level 3, why this separation matters** — the final printed counts (`1` discovery lookup, `4` health probes across two calls of two instances each) show that caching reduced expensive registry lookups while health-checking still caught the failure promptly, because the two concerns are decoupled: caching controls how often the *candidate list* is refreshed, while health-checking controls which candidates in that list are currently considered usable, and it re-evaluates on every call independent of the cache.

## 7. Gotchas & takeaways

> **Gotcha:** caching the instance *list* and checking instance *health* are separate concerns with separate refresh cadences — a long cache TTL does not mean health information goes stale for that same duration, since health checks (when enabled) typically re-probe independently of the caching layer, as Level 3 demonstrates; conversely, don't assume enabling health checks alone gives you caching, or that caching alone gives you health awareness — both need to be explicitly configured for the combined benefit.

- Caching the resolved instance list with a short TTL cuts down on redundant `DiscoveryClient` lookups under high call volume, at the cost of the instance list being up to one TTL period stale after a registry change.
- `HealthCheckServiceInstanceListSupplier` actively probes candidate instances and excludes currently-unhealthy ones, closing the gap between "registered" (what `DiscoveryClient` reports) and "actually able to serve a request right now."
- Both caching and health-checking are implemented as composable `ServiceInstanceListSupplier` decorators, the same extension point used for [custom candidate filtering](0214-custom-loadbalancer-configuration-serviceinstancelistsupplie.md), and can be combined freely.
- Caching and health-checking operate on different cadences by design — caching reduces lookup frequency, while health-checking can still re-evaluate instance health independently of whether the underlying list came from cache.
- Enable caching for high-call-volume applications where lookup overhead matters, and layer in health-checking wherever registered-but-unhealthy instances are a realistic risk — the two together are a common, complementary production configuration.
