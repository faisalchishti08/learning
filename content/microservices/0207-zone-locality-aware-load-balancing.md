---
card: microservices
gi: 207
slug: zone-locality-aware-load-balancing
title: "Zone / locality-aware load balancing"
---

## 1. What it is

Zone (or locality) aware load balancing prefers routing a request to an instance in the same availability zone, region, or rack as the caller, falling back to other zones only when no local instance is available — a specific, higher-priority application of [instance metadata](0190-instance-metadata-tagging.md)-based routing, aimed specifically at minimizing cross-zone latency and cross-zone data transfer cost.

## 2. Why & when

Calls that cross availability zones (or regions) typically incur measurably higher latency than calls staying within the same zone, and many cloud providers charge explicitly for cross-zone data transfer, making zone-blind load balancing both slower and more expensive than necessary whenever same-zone instances are available. Zone-aware balancing directly targets this by preferring local instances first, trading away perfectly even load distribution across the entire fleet for meaningfully lower latency and cost on the common case, while still falling back to cross-zone routing when local capacity is exhausted or unavailable, preserving overall availability.

Use zone-aware balancing in any multi-zone or multi-region deployment where cross-zone latency or cost is a genuine concern — which describes most cloud deployments spanning more than one availability zone. Skip it for single-zone deployments, where there's no zone distinction to prefer in the first place.

## 3. Core concept

Each instance carries zone metadata; the balancer first filters (or strongly prefers) instances matching the caller's own zone, applying its normal selection algorithm (round-robin, random, least-connections) within that same-zone subset, and only considers instances in other zones if the local subset is empty or exhausted.

```java
String callerZone = "us-east-1a";
List<ServiceInstance> sameZoneInstances = allInstances.stream()
    .filter(i -> callerZone.equals(i.metadata().get("zone")))
    .toList();

List<ServiceInstance> candidates = sameZoneInstances.isEmpty() ? allInstances : sameZoneInstances; // FALLBACK if no local instances
ServiceInstance chosen = normalLoadBalancer.choose(candidates);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A caller in zone us-east-1a prefers routing to instances also in us-east-1a; only if no instances exist there does it fall back to instances in us-east-1b, avoiding cross-zone latency and cost on the common case" >
  <rect x="20" y="20" width="280" height="100" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="40" fill="#8b949e" font-size="8" font-family="sans-serif">Zone us-east-1a</text>
  <rect x="40" y="55" width="100" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="90" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Caller</text>
  <rect x="180" y="55" width="100" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="230" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Instance (local)</text>
  <line x1="140" y1="70" x2="178" y2="70" stroke="#8b949e" marker-end="url(#arr87)"/>
  <text x="160" y="100" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">preferred: low latency, no cross-zone cost</text>

  <rect x="360" y="20" width="260" height="100" rx="8" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="490" y="40" fill="#8b949e" font-size="8" font-family="sans-serif">Zone us-east-1b</text>
  <rect x="440" y="55" width="140" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/><text x="510" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Instance (fallback only)</text>

  <defs>
    <marker id="arr87" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Local-zone instances are preferred first; cross-zone instances only enter the picture as a fallback.

## 5. Runnable example

Scenario: a shipping-service calling order-service across zones that starts with zone-blind balancing sending roughly half its traffic cross-zone unnecessarily, adds zone-aware filtering so traffic stays local whenever possible, and finally demonstrates the required fallback behavior when the local zone genuinely has no available instances, preserving availability over strict zone preference.

### Level 1 — Basic

```java
// File: ZoneBlindBalancing.java -- NO zone awareness; roughly HALF of traffic
// crosses zones UNNECESSARILY, even though local instances exist.
import java.util.*;

public class ZoneBlindBalancing {
    record ServiceInstance(String id, String zone) {}

    public static void main(String[] args) {
        List<ServiceInstance> instances = List.of(
            new ServiceInstance("order-a", "us-east-1a"), new ServiceInstance("order-b", "us-east-1a"),
            new ServiceInstance("order-c", "us-east-1b"), new ServiceInstance("order-d", "us-east-1b"));
        String callerZone = "us-east-1a";
        int index = 0;

        Map<String, Integer> crossZoneCount = new TreeMap<>(Map.of("same-zone", 0, "cross-zone", 0));
        for (int i = 0; i < 8; i++) {
            ServiceInstance chosen = instances.get(index++ % instances.size()); // ZONE-BLIND round-robin
            String key = chosen.zone().equals(callerZone) ? "same-zone" : "cross-zone";
            crossZoneCount.merge(key, 1, Integer::sum);
        }
        System.out.println("Traffic distribution: " + crossZoneCount);
        System.out.println("HALF of all calls crossed zones UNNECESSARILY -- us-east-1a had capacity the whole time.");
    }
}
```

**How to run:** `javac ZoneBlindBalancing.java && java ZoneBlindBalancing` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ZoneAwarePreference.java -- FILTERS to the caller's OWN zone first;
// traffic stays LOCAL whenever local instances exist.
import java.util.*;

public class ZoneAwarePreference {
    record ServiceInstance(String id, String zone) {}

    static ServiceInstance chooseZoneAware(List<ServiceInstance> allInstances, String callerZone, int[] indexHolder) {
        List<ServiceInstance> sameZone = allInstances.stream().filter(i -> i.zone().equals(callerZone)).toList();
        List<ServiceInstance> candidates = sameZone.isEmpty() ? allInstances : sameZone; // PREFER local, fall back if empty
        return candidates.get(indexHolder[0]++ % candidates.size());
    }

    public static void main(String[] args) {
        List<ServiceInstance> instances = List.of(
            new ServiceInstance("order-a", "us-east-1a"), new ServiceInstance("order-b", "us-east-1a"),
            new ServiceInstance("order-c", "us-east-1b"), new ServiceInstance("order-d", "us-east-1b"));
        String callerZone = "us-east-1a";
        int[] index = {0};

        Map<String, Integer> crossZoneCount = new TreeMap<>(Map.of("same-zone", 0, "cross-zone", 0));
        for (int i = 0; i < 8; i++) {
            ServiceInstance chosen = chooseZoneAware(instances, callerZone, index);
            String key = chosen.zone().equals(callerZone) ? "same-zone" : "cross-zone";
            crossZoneCount.merge(key, 1, Integer::sum);
        }
        System.out.println("Traffic distribution: " + crossZoneCount);
        System.out.println("ALL traffic stayed LOCAL -- us-east-1a had 2 healthy instances, so cross-zone routing was NEVER needed.");
    }
}
```

**How to run:** `javac ZoneAwarePreference.java && java ZoneAwarePreference` (JDK 17+).

Expected output:
```
Traffic distribution: {cross-zone=0, same-zone=8}
ALL traffic stayed LOCAL -- us-east-1a had 2 healthy instances, so cross-zone routing was NEVER needed.
```

### Level 3 — Advanced

```java
// File: FallbackWhenLocalZoneExhausted.java -- when the LOCAL zone genuinely
// has NO healthy instances, the balancer correctly FALLS BACK to cross-zone --
// availability wins over strict zone preference.
import java.util.*;

public class FallbackWhenLocalZoneExhausted {
    record ServiceInstance(String id, String zone, boolean healthy) {}

    static ServiceInstance chooseZoneAware(List<ServiceInstance> allInstances, String callerZone, int[] indexHolder) {
        List<ServiceInstance> healthyInSameZone = allInstances.stream()
            .filter(i -> i.zone().equals(callerZone) && i.healthy())
            .toList();
        List<ServiceInstance> healthyAnywhere = allInstances.stream().filter(ServiceInstance::healthy).toList();

        List<ServiceInstance> candidates = healthyInSameZone.isEmpty() ? healthyAnywhere : healthyInSameZone;
        if (candidates.isEmpty()) throw new RuntimeException("no healthy instances anywhere");
        return candidates.get(indexHolder[0]++ % candidates.size());
    }

    public static void main(String[] args) {
        List<ServiceInstance> instances = List.of(
            new ServiceInstance("order-a", "us-east-1a", false), // LOCAL zone, but UNHEALTHY
            new ServiceInstance("order-b", "us-east-1a", false), // LOCAL zone, but UNHEALTHY
            new ServiceInstance("order-c", "us-east-1b", true),  // cross-zone, healthy
            new ServiceInstance("order-d", "us-east-1b", true)); // cross-zone, healthy
        String callerZone = "us-east-1a";
        int[] index = {0};

        System.out.println("Local zone (us-east-1a) instances are BOTH unhealthy -- what happens?");
        for (int i = 0; i < 4; i++) {
            ServiceInstance chosen = chooseZoneAware(instances, callerZone, index);
            System.out.println("  chose: " + chosen.id() + " (zone=" + chosen.zone() + ")");
        }
        System.out.println("The balancer CORRECTLY fell back to cross-zone instances (order-c, order-d) -- AVAILABILITY was preserved, at the cost of losing zone locality this time.");
    }
}
```

**How to run:** `javac FallbackWhenLocalZoneExhausted.java && java FallbackWhenLocalZoneExhausted` (JDK 17+).

Expected output:
```
Local zone (us-east-1a) instances are BOTH unhealthy -- what happens?
  chose: order-c (zone=us-east-1b)
  chose: order-d (zone=us-east-1b)
  chose: order-c (zone=us-east-1b)
  chose: order-d (zone=us-east-1b)
The balancer CORRECTLY fell back to cross-zone instances (order-c, order-d) -- AVAILABILITY was preserved, at the cost of losing zone locality this time.
```

## 6. Walkthrough

1. **Level 1** — `instances.get(index++ % instances.size())` cycles through all four instances regardless of zone, meaning exactly half of the eight selections (`order-c`, `order-d`) fall in `us-east-1b`, crossing zones every time despite `us-east-1a` having ample capacity.
2. **Level 2, filtering to the caller's own zone first** — `chooseZoneAware` computes `sameZone` by filtering `allInstances` against `callerZone`, and only falls back to the full `allInstances` list if that filtered list is empty; with two healthy `us-east-1a` instances present, `candidates` is always `sameZone`.
3. **Level 2, the resulting all-local distribution** — all eight selections land on `order-a` or `order-b`, both in `us-east-1a`, directly resolving Level 1's unnecessary cross-zone traffic.
4. **Level 3, incorporating health alongside zone** — `chooseZoneAware` now filters `allInstances` by both `zone().equals(callerZone)` *and* `healthy()`, computing `healthyInSameZone` separately from `healthyAnywhere` (all healthy instances regardless of zone).
5. **Level 3, the fallback condition** — `candidates = healthyInSameZone.isEmpty() ? healthyAnywhere : healthyInSameZone` means the balancer only reaches for cross-zone instances when the local zone has *no* healthy candidates at all — with both `order-a` and `order-b` marked unhealthy, `healthyInSameZone` is empty, triggering the fallback.
6. **Level 3, the observed fallback behavior** — all four selections in the trace go to `order-c` and `order-d`, both in `us-east-1b`, confirming the balancer correctly and automatically routed cross-zone once the local zone became unavailable, rather than failing the requests outright or blindly continuing to prefer an unhealthy local instance.
7. **Level 3, the priority ordering this demonstrates** — the final printed comment names the deliberate trade-off directly: this design prioritizes availability (serving the request from *somewhere* healthy) over strict zone locality (serving it from a specific, possibly-unavailable local zone) — a fallback that degrades gracefully to slightly higher latency and cost rather than failing the request entirely is almost always the correct choice, since a failed request is a strictly worse outcome than a slower, cross-zone-served one.

## 7. Gotchas & takeaways

> **Gotcha:** zone-aware balancing that never falls back — treating zone preference as a hard requirement rather than a preference — turns a partial local-zone outage into a full request failure for every caller in that zone, even when perfectly healthy capacity exists just one zone away; the fallback behavior demonstrated in Level 3 isn't an optional nicety, it's what prevents zone locality from becoming a single point of failure in its own right.

- Zone-aware load balancing prefers routing to instances in the caller's own zone, minimizing cross-zone latency and data transfer cost, while falling back to other zones when local capacity is unavailable.
- This is a specific, latency-and-cost-focused application of metadata-based routing, layered as a preference on top of a normal selection algorithm applied within the preferred candidate set.
- Zone-blind balancing routes a meaningful fraction of traffic cross-zone unnecessarily whenever local capacity exists, incurring avoidable latency and cost.
- The fallback to cross-zone instances when the local zone has no healthy candidates is essential — without it, zone preference becomes a new availability risk rather than a pure optimization.
- This pattern applies broadly to any multi-zone or multi-region deployment where cross-zone communication carries a measurable latency or cost penalty worth avoiding on the common case.
