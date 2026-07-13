---
card: microservices
gi: 190
slug: instance-metadata-tagging
title: "Instance metadata & tagging"
---

## 1. What it is

Instance metadata is arbitrary key-value information an instance attaches to its [service registry](0182-service-registry-concept.md) entry beyond just its host and port — a version number, a deployment region, a canary/stable designation, custom capability flags — letting callers make more sophisticated routing decisions than "give me any healthy instance," such as "give me an instance in my same region" or "give me an instance running the canary version."

## 2. Why & when

A bare host-and-port instance list is sufficient for simple, uniform load balancing, but many real routing needs require distinguishing between instances beyond just "healthy or not": routing based on deployment region to minimize cross-region latency, directing a small percentage of traffic to a canary release for gradual rollout validation, or selecting instances with specific capability flags (a GPU-enabled instance for a particular workload, for instance). Metadata attached at registration time gives callers (or the load-balancing logic acting on their behalf) the information needed to make these distinctions, without requiring a separate lookup or a different discovery mechanism entirely.

Attach metadata to instance registrations whenever routing decisions need to consider more than basic health — canary deployments, multi-region topologies, and capability-based routing are the common cases. Keep metadata to genuinely routing-relevant information; business data unrelated to instance selection doesn't belong in the registry and should live in the services' own data stores instead.

## 3. Core concept

Metadata is a set of key-value pairs attached to an instance at registration time, queryable alongside the instance's basic connection information; callers or load-balancing logic can filter or prefer instances based on metadata values in addition to (or instead of) simple health-based selection.

```java
// registration includes METADATA beyond just host/port
registry.register("order-service", new ServiceInstance(
    "order-a", "10.0.1.5", 8080,
    Map.of("region", "us-east", "version", "2.3.1", "canary", "false")));

// a caller can FILTER by metadata, not just pick any healthy instance
List<ServiceInstance> sameRegionInstances = registry.getInstances("order-service").stream()
    .filter(i -> i.metadata().get("region").equals(callerRegion))
    .toList();
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three order-service instances are registered with different region and canary metadata; a caller in us-east filters the instance list by region, selecting only the two us-east instances and excluding the eu-west one, regardless of health" >
  <rect x="20" y="20" width="160" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-a</text>
  <text x="100" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">region=us-east, canary=false</text>

  <rect x="20" y="80" width="160" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="100" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-b</text>
  <text x="100" y="115" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">region=us-east, canary=true</text>

  <rect x="20" y="140" width="160" height="45" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="100" y="160" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-c</text>
  <text x="100" y="175" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">region=eu-west (filtered OUT)</text>

  <rect x="420" y="70" width="180" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Caller (us-east)</text>
  <text x="510" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">filters by region=us-east</text>

  <line x1="180" y1="42" x2="418" y2="85" stroke="#8b949e" marker-end="url(#arr71)"/>
  <line x1="180" y1="102" x2="418" y2="95" stroke="#8b949e" marker-end="url(#arr71)"/>

  <defs>
    <marker id="arr71" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Metadata lets a caller narrow the candidate instance pool by criteria beyond simple health.

## 5. Runnable example

Scenario: a multi-region order-service deployment that starts with region-blind routing (showing the cross-region latency risk), adds region metadata so callers can filter by region, and finally adds canary-percentage-based routing on top, demonstrating multiple metadata dimensions combining to express a realistic, production-flavored routing policy.

### Level 1 — Basic

```java
// File: RegionBlindRouting.java -- NO metadata; a caller in us-east can be
// routed to a eu-west instance, adding unnecessary cross-region latency.
import java.util.*;

public class RegionBlindRouting {
    record ServiceInstance(String id, String host) {}

    public static void main(String[] args) {
        List<ServiceInstance> allInstances = List.of(
            new ServiceInstance("order-a", "10.0.1.5"),  // actually in us-east
            new ServiceInstance("order-c", "10.0.9.9"));  // actually in eu-west -- but NOTHING distinguishes this

        String callerRegion = "us-east";
        ServiceInstance chosen = allInstances.get(1); // could pick EITHER -- no region awareness at all
        System.out.println("Caller in " + callerRegion + " was routed to " + chosen.id() + " -- possibly in a DIFFERENT region, adding latency, with no way to know or avoid it.");
    }
}
```

**How to run:** `javac RegionBlindRouting.java && java RegionBlindRouting` (JDK 17+).

### Level 2 — Intermediate

```java
// File: RegionAwareFiltering.java -- REGION metadata lets the caller FILTER to
// same-region instances, avoiding unnecessary cross-region latency.
import java.util.*;

public class RegionAwareFiltering {
    record ServiceInstance(String id, String host, Map<String, String> metadata) {}

    public static void main(String[] args) {
        List<ServiceInstance> allInstances = List.of(
            new ServiceInstance("order-a", "10.0.1.5", Map.of("region", "us-east")),
            new ServiceInstance("order-b", "10.0.1.6", Map.of("region", "us-east")),
            new ServiceInstance("order-c", "10.0.9.9", Map.of("region", "eu-west")));

        String callerRegion = "us-east";
        List<ServiceInstance> sameRegion = allInstances.stream()
            .filter(i -> i.metadata().get("region").equals(callerRegion)) // FILTER by metadata
            .toList();

        System.out.println("All instances: " + allInstances.stream().map(ServiceInstance::id).toList());
        System.out.println("Same-region (" + callerRegion + ") candidates: " + sameRegion.stream().map(ServiceInstance::id).toList());
        System.out.println("order-c (eu-west) was correctly EXCLUDED -- the caller will never pay cross-region latency for this call.");
    }
}
```

**How to run:** `javac RegionAwareFiltering.java && java RegionAwareFiltering` (JDK 17+).

Expected output:
```
All instances: [order-a, order-b, order-c]
Same-region (us-east) candidates: [order-a, order-b]
order-c (eu-west) was correctly EXCLUDED -- the caller will never pay cross-region latency for this call.
```

### Level 3 — Advanced

```java
// File: MultiDimensionalMetadataRouting.java -- combines REGION filtering with
// CANARY-PERCENTAGE routing -- multiple metadata dimensions expressing a
// realistic, production-flavored policy TOGETHER.
import java.util.*;

public class MultiDimensionalMetadataRouting {
    record ServiceInstance(String id, String host, Map<String, String> metadata) {}

    public static void main(String[] args) {
        List<ServiceInstance> allInstances = List.of(
            new ServiceInstance("order-a", "10.0.1.5", Map.of("region", "us-east", "canary", "false")),
            new ServiceInstance("order-b", "10.0.1.6", Map.of("region", "us-east", "canary", "false")),
            new ServiceInstance("order-canary", "10.0.1.7", Map.of("region", "us-east", "canary", "true")), // ONLY 10% of traffic should hit this
            new ServiceInstance("order-c", "10.0.9.9", Map.of("region", "eu-west", "canary", "false")));

        String callerRegion = "us-east";
        List<ServiceInstance> sameRegion = allInstances.stream()
            .filter(i -> i.metadata().get("region").equals(callerRegion))
            .toList();

        Random random = new Random(42); // fixed seed for reproducible demo output
        int canaryTrafficPercent = 10;
        Map<String, Integer> chosenCounts = new TreeMap<>();

        for (int i = 0; i < 100; i++) {
            boolean routeToCanary = random.nextInt(100) < canaryTrafficPercent; // 10% chance
            List<ServiceInstance> candidates = sameRegion.stream()
                .filter(inst -> inst.metadata().get("canary").equals(routeToCanary ? "true" : "false"))
                .toList();
            ServiceInstance chosen = candidates.get(random.nextInt(candidates.size()));
            chosenCounts.merge(chosen.id(), 1, Integer::sum);
        }

        System.out.println("Same-region candidates: " + sameRegion.stream().map(ServiceInstance::id).toList());
        System.out.println("Distribution over 100 requests: " + chosenCounts);
        System.out.println("order-canary received roughly " + canaryTrafficPercent + "% of traffic, as configured -- order-c (eu-west) received NONE, EVER.");
    }
}
```

**How to run:** `javac MultiDimensionalMetadataRouting.java && java MultiDimensionalMetadataRouting` (JDK 17+).

Expected output (exact distribution depends on the fixed random seed, but order-canary receives roughly 10% and order-c receives 0%):
```
Same-region candidates: [order-a, order-b, order-canary]
Distribution over 100 requests: {order-a=45, order-b=44, order-canary=11}
order-canary received roughly 10% of traffic, as configured -- order-c (eu-west) received NONE, EVER.
```

## 6. Walkthrough

1. **Level 1** — `allInstances` is a plain list of `id` and `host` pairs, with no attribute distinguishing which region either instance actually resides in; `chosen = allInstances.get(1)` illustrates that a routing decision here has no principled basis for preferring the same-region instance over the cross-region one.
2. **Level 2, metadata attached to each instance** — `ServiceInstance` now includes a `Map<String, String> metadata` field, with `order-a` and `order-b` tagged `"region" -> "us-east"` and `order-c` tagged `"region" -> "eu-west"`.
3. **Level 2, filtering using that metadata** — the `.filter(i -> i.metadata().get("region").equals(callerRegion))` step excludes any instance whose region metadata doesn't match `callerRegion`, producing `sameRegion` containing only `order-a` and `order-b`.
4. **Level 2, the concrete latency-avoidance payoff** — the printed comparison between `allInstances` and `sameRegion` shows `order-c` present in the former but absent from the latter, directly confirming that a caller using this filtered list will never be routed cross-region for this particular call.
5. **Level 3, a second metadata dimension** — each instance now also carries a `"canary"` key, with `order-canary` distinctly marked `"true"` while the others are marked `"false"`, representing a canary release deployed alongside the stable version.
6. **Level 3, combining region filtering with percentage-based canary routing** — for each simulated request, `routeToCanary` is determined by a weighted random draw (10% chance), and the candidate list is *then* filtered by both the caller's region *and* the desired canary status, meaning the two metadata dimensions compose together rather than requiring separate, unrelated routing mechanisms.
7. **Level 3, the measured outcome confirming the policy** — across 100 simulated requests, `order-canary` receives a count close to the configured 10% target, `order-a` and `order-b` split the remaining roughly 90% between them, and `order-c` (excluded by the region filter before canary logic is even considered) receives exactly zero requests — demonstrating that multiple independent metadata dimensions can be layered together to express a genuinely realistic production routing policy (region-scoped, percentage-based canary rollout) entirely from data attached at registration time, with no special-purpose routing infrastructure beyond metadata-aware filtering.

## 7. Gotchas & takeaways

> **Gotcha:** metadata values are typically just strings from the registry's point of view — there's no built-in schema validation ensuring every instance consistently populates the same metadata keys with the same expected value formats; a typo (`"cannary"` instead of `"canary"`, or `"True"` instead of `"true"`) silently produces an instance that's invisible to metadata-based filtering logic expecting the correct key and format, without any error being raised anywhere.

- Instance metadata attaches arbitrary key-value information to a registry entry beyond basic host and port, letting routing decisions consider criteria like region, version, or canary status.
- This enables routing patterns — region-aware selection, canary rollouts, capability-based routing — that a bare host-and-port instance list cannot express on its own.
- Multiple metadata dimensions compose naturally: filtering by region and then by canary status (or any other combination) is just successive filtering over the same underlying instance list.
- Metadata should be kept to genuinely routing-relevant information; unrelated business data belongs in each service's own data store, not the registry.
- Metadata values typically lack schema validation, making consistent key naming and value formatting across all instances a real, easy-to-get-wrong operational discipline requirement.
