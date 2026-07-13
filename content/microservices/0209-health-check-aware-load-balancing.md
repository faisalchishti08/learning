---
card: microservices
gi: 209
slug: health-check-aware-load-balancing
title: "Health-check-aware load balancing"
---

## 1. What it is

Health-check-aware load balancing filters a load balancer's candidate instance pool to only those currently passing a health check, before applying its normal selection algorithm — combining [health-check-based registration](0188-health-check-based-registration.md)'s exclusion logic directly with the balancing decision itself, so an unhealthy instance is never selected in the first place, rather than being selected and then failing the request.

## 2. Why & when

A load balancer that selects among *all* registered instances, healthy or not, will periodically route requests to instances that are technically registered but currently unable to serve them correctly, producing avoidable request failures the balancer could have sidestepped entirely by simply checking health status before selecting. Combining health awareness directly into the selection step — rather than treating health-based exclusion as a separate registry concern happening independently of balancing — closes this gap: the balancer's candidate pool is always the *currently healthy* subset, not the full registered set.

Build health awareness directly into any load balancer implementation, whether client-side or server-side — this is close to a baseline requirement for a load balancer to be genuinely useful, since selecting an unhealthy instance defeats much of the purpose of balancing in the first place. The health status itself typically comes from the same mechanisms already covered ([heartbeats/lease renewal](0189-heartbeats-lease-renewal.md), active health-check probing), with the balancer simply consuming that status as an input to its selection.

## 3. Core concept

Before applying the balancing algorithm (round-robin, random, least-connections, weighted), the balancer first filters the full instance list down to only those currently reporting healthy, and applies its selection logic exclusively within that filtered subset — an instance never reappears as a candidate again until its health status genuinely recovers.

```java
List<ServiceInstance> allInstances = discoveryClient.getInstances("order-service");
List<ServiceInstance> healthyInstances = allInstances.stream()
    .filter(ServiceInstance::isHealthy) // FILTER before selecting, not after
    .toList();

if (healthyInstances.isEmpty()) throw new NoHealthyInstancesException();
ServiceInstance chosen = balancingAlgorithm.choose(healthyInstances); // NEVER sees an unhealthy instance
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four registered instances exist, one of which is currently unhealthy; the load balancer filters to the three healthy instances before applying round-robin selection, so the unhealthy instance is never a candidate for any request" >
  <rect x="20" y="30" width="90" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="65" y="52" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">A: healthy</text>
  <rect x="120" y="30" width="90" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="165" y="52" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">B: unhealthy</text>
  <rect x="220" y="30" width="90" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="265" y="52" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">C: healthy</text>
  <rect x="320" y="30" width="90" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="365" y="52" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">D: healthy</text>

  <rect x="150" y="95" width="260" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="280" y="117" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Candidate pool: A, C, D only</text>

  <line x1="65" y1="65" x2="200" y2="95" stroke="#8b949e" marker-end="url(#arr89)"/>
  <line x1="265" y1="65" x2="270" y2="95" stroke="#8b949e" marker-end="url(#arr89)"/>
  <line x1="365" y1="65" x2="340" y2="95" stroke="#8b949e" marker-end="url(#arr89)"/>

  <defs>
    <marker id="arr89" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Filtering happens before selection; the unhealthy instance never enters the candidate pool at all.

## 5. Runnable example

Scenario: an order-service call flow that starts with a health-blind balancer occasionally selecting and failing against an unhealthy instance, adds health filtering before the selection step so unhealthy instances are structurally excluded, and finally demonstrates the balancer correctly and automatically adapting as an instance's health status changes over time, without any change to the balancer's own code.

### Level 1 — Basic

```java
// File: HealthBlindSelection.java -- the balancer selects among ALL registered
// instances, INCLUDING unhealthy ones -- producing AVOIDABLE request failures.
import java.util.*;

public class HealthBlindSelection {
    record ServiceInstance(String id, boolean healthy) {}

    public static void main(String[] args) {
        List<ServiceInstance> allInstances = List.of(
            new ServiceInstance("order-a", true), new ServiceInstance("order-b", false), new ServiceInstance("order-c", true));
        int index = 0;

        int successes = 0, failures = 0;
        for (int i = 0; i < 6; i++) {
            ServiceInstance chosen = allInstances.get(index++ % allInstances.size()); // NO health filtering
            if (chosen.healthy()) { successes++; System.out.println("call to " + chosen.id() + ": SUCCESS"); }
            else { failures++; System.out.println("call to " + chosen.id() + ": FAILED (was unhealthy the whole time)"); }
        }
        System.out.println("Successes: " + successes + ", Failures: " + failures + " -- avoidable failures from selecting a KNOWN-unhealthy instance.");
    }
}
```

**How to run:** `javac HealthBlindSelection.java && java HealthBlindSelection` (JDK 17+).

### Level 2 — Intermediate

```java
// File: FilterBeforeSelect.java -- FILTERS to healthy instances BEFORE
// applying the selection algorithm -- the unhealthy instance is NEVER chosen.
import java.util.*;

public class FilterBeforeSelect {
    record ServiceInstance(String id, boolean healthy) {}

    static class HealthAwareBalancer {
        int index = 0;
        ServiceInstance choose(List<ServiceInstance> allInstances) {
            List<ServiceInstance> healthy = allInstances.stream().filter(ServiceInstance::healthy).toList(); // FILTER FIRST
            if (healthy.isEmpty()) throw new RuntimeException("no healthy instances");
            return healthy.get(index++ % healthy.size()); // selection ONLY sees the filtered list
        }
    }

    public static void main(String[] args) {
        List<ServiceInstance> allInstances = List.of(
            new ServiceInstance("order-a", true), new ServiceInstance("order-b", false), new ServiceInstance("order-c", true));
        HealthAwareBalancer balancer = new HealthAwareBalancer();

        int successes = 0;
        for (int i = 0; i < 6; i++) {
            ServiceInstance chosen = balancer.choose(allInstances);
            successes++;
            System.out.println("call to " + chosen.id() + ": SUCCESS (healthy=" + chosen.healthy() + ")");
        }
        System.out.println("Successes: " + successes + "/6 -- order-b was NEVER selected, since it was filtered out BEFORE selection even ran.");
    }
}
```

**How to run:** `javac FilterBeforeSelect.java && java FilterBeforeSelect` (JDK 17+).

Expected output:
```
call to order-a: SUCCESS (healthy=true)
call to order-c: SUCCESS (healthy=true)
call to order-a: SUCCESS (healthy=true)
call to order-c: SUCCESS (healthy=true)
call to order-a: SUCCESS (healthy=true)
call to order-c: SUCCESS (healthy=true)
Successes: 6/6 -- order-b was NEVER selected, since it was filtered out BEFORE selection even ran.
```

### Level 3 — Advanced

```java
// File: AdaptsAsHealthChanges.java -- the balancer AUTOMATICALLY reflects
// CHANGING health status over time -- an instance recovering rejoins the
// candidate pool, and one failing leaves it, with NO code changes needed.
import java.util.*;

public class AdaptsAsHealthChanges {
    static class ServiceInstance {
        String id; boolean healthy;
        ServiceInstance(String id, boolean healthy) { this.id = id; this.healthy = healthy; }
    }

    static class HealthAwareBalancer {
        int index = 0;
        ServiceInstance choose(List<ServiceInstance> allInstances) {
            List<ServiceInstance> healthy = allInstances.stream().filter(i -> i.healthy).toList();
            if (healthy.isEmpty()) throw new RuntimeException("no healthy instances");
            return healthy.get(index++ % healthy.size());
        }
    }

    public static void main(String[] args) {
        ServiceInstance a = new ServiceInstance("order-a", true);
        ServiceInstance b = new ServiceInstance("order-b", true);
        ServiceInstance c = new ServiceInstance("order-c", true);
        List<ServiceInstance> allInstances = List.of(a, b, c);
        HealthAwareBalancer balancer = new HealthAwareBalancer(); // constructed ONCE, never reconfigured

        System.out.println("=== all healthy ===");
        for (int i = 0; i < 3; i++) System.out.println("chose: " + balancer.choose(allInstances).id);

        b.healthy = false; // order-b DEGRADES
        System.out.println("\n=== order-b becomes unhealthy ===");
        for (int i = 0; i < 3; i++) System.out.println("chose: " + balancer.choose(allInstances).id);

        b.healthy = true; // order-b RECOVERS
        System.out.println("\n=== order-b recovers ===");
        for (int i = 0; i < 3; i++) System.out.println("chose: " + balancer.choose(allInstances).id);

        System.out.println("\nThe SAME balancer object, with NO reconfiguration, automatically EXCLUDED and later RE-INCLUDED order-b, purely by re-evaluating health on EVERY call.");
    }
}
```

**How to run:** `javac AdaptsAsHealthChanges.java && java AdaptsAsHealthChanges` (JDK 17+).

Expected output:
```
=== all healthy ===
chose: order-a
chose: order-b
chose: order-c

=== order-b becomes unhealthy ===
chose: order-a
chose: order-c
chose: order-a

=== order-b recovers ===
chose: order-c
chose: order-a
chose: order-b

The SAME balancer object, with NO reconfiguration, automatically EXCLUDED and later RE-INCLUDED order-b, purely by re-evaluating health on EVERY call.
```

## 6. Walkthrough

1. **Level 1** — `allInstances.get(index++ % allInstances.size())` cycles through all three instances regardless of `healthy`, so `order-b` (marked unhealthy) is selected on schedule and its call correctly logs as a failure — this is an avoidable failure, since the balancer had the health information available and simply didn't use it before selecting.
2. **Level 2, filtering as the first step** — `HealthAwareBalancer.choose` computes `healthy` via `.filter(ServiceInstance::healthy)` before doing anything else, and the subsequent `healthy.get(index++ % healthy.size())` operates exclusively on this filtered list — `order-b` never appears in `healthy` at all.
3. **Level 2, the resulting zero-failure outcome** — all six calls succeed, alternating between `order-a` and `order-c` only, directly demonstrating that filtering before selecting structurally eliminates the possibility of choosing a known-unhealthy instance.
4. **Level 3, mutable instance state** — `ServiceInstance` is now a plain mutable class (not an immutable record) with a directly settable `healthy` field, allowing `main` to change an instance's health status mid-run to simulate a real health transition.
5. **Level 3, the balancer never touched after construction** — `balancer` is created exactly once at the start of `main` and is never reconstructed or reconfigured for the remainder of the program, despite `b.healthy` being toggled twice.
6. **Level 3, tracing the exclusion and re-inclusion** — during the "all healthy" phase, selections rotate through all three instances; after `b.healthy = false`, subsequent calls to `balancer.choose` recompute the filtered list fresh each time, correctly omitting `order-b` and rotating only through `order-a` and `order-c`; after `b.healthy = true` restores it, the very next call to `choose` recomputes the filter again and finds `order-b` eligible once more, automatically including it back in the rotation.
7. **Level 3, why this requires no explicit "handle recovery" logic** — because `choose` recomputes the healthy subset fresh from current state on every single invocation, rather than caching a filtered list once, there is no special code path needed to detect recovery — the balancer simply, correctly reflects whatever the current health state happens to be at the moment of each call, exactly mirroring how a real load balancer combined with ongoing health checking (via heartbeats or active probing) naturally and automatically adapts its candidate pool as instance health genuinely changes over time.

## 7. Gotchas & takeaways

> **Gotcha:** filtering to only healthy instances means the candidate pool can shrink dramatically during a partial outage, and if enough instances become simultaneously unhealthy, the remaining healthy instances absorb a correspondingly larger share of traffic — a load balancer correctly avoiding unhealthy instances doesn't by itself prevent the remaining healthy instances from becoming overloaded by the redirected traffic; this interacts directly with [circuit breakers](0177-gateway-circuit-breaker-filter-resilience4j.md) and capacity planning as complementary concerns, not something health-aware balancing alone solves.

- Health-check-aware load balancing filters the candidate instance pool to only currently-healthy instances before applying the selection algorithm, rather than selecting first and potentially failing against an unhealthy instance afterward.
- This structurally eliminates avoidable request failures caused by routing to instances the balancer already had health information about.
- The filtering step should recompute fresh on every selection (or on a short, bounded refresh interval), so the balancer automatically reflects both instances becoming unhealthy and instances recovering, with no special-case handling needed for either transition.
- Health status itself typically comes from existing mechanisms (heartbeats, active health-check probing) already covered elsewhere; health-aware balancing is about correctly consuming that status at the selection step, not a separate health-detection mechanism of its own.
- A shrinking healthy candidate pool during a partial outage concentrates more traffic on the remaining healthy instances, which health-aware balancing alone doesn't prevent — this interacts with broader capacity planning and resilience patterns like circuit breakers.
