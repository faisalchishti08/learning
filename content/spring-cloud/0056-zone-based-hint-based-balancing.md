---
card: spring-cloud
gi: 56
slug: zone-based-hint-based-balancing
title: "Zone-based & hint-based balancing"
---

## 1. What it is

Beyond plain round-robin and random, Spring Cloud LoadBalancer supports zone-based balancing (preferring same-zone instances, the client-side counterpart to the Eureka zone-awareness card from the Service Discovery section, now expressed as a `ServiceInstanceListSupplier` decorator) and hint-based balancing (attaching an arbitrary "hint" — a string tag — to a request, and filtering candidate instances to only those advertising a matching hint in their own metadata).

```properties
spring.cloud.loadbalancer.zone=us-east-1a
spring.cloud.loadbalancer.configurations=zone-preference,hint

spring.cloud.loadbalancer.hint.billing-service=canary
```

```java
// a per-request hint, overriding the default configured hint for this one call
ServiceInstance instance = loadBalancerClient.choose("billing-service",
        new DefaultRequest<>(new RequestDataContext(null, new LinkedHashSet<>() {{ add("canary"); }})));
```

## 2. Why & when

Zone preference (covered client-side generically in an earlier Eureka card) reduces cross-zone latency and cost by keeping normal traffic local. Hint-based balancing solves a different, complementary problem: routing specific traffic to a specific *subset* of instances identified by an arbitrary tag, independent of which zone they happen to be in — most commonly used for canary deployments (a new version tagged `canary`, receiving only deliberately-selected traffic) or A/B-testing splits.

Reach for these when:

- Zone-based: the same motivation as the earlier Eureka zone-awareness card — reduce cross-zone latency/cost for the common case, while still falling back gracefully if the local zone has no eligible instances.
- Hint-based: rolling out a new version to a small subset of instances and directing only specific, deliberately-tagged traffic to it (internal testers, a percentage of production users) before a full rollout.
- Combining both: a canary deployment that should also respect zone locality — hint-based filtering picks the eligible subset, then zone preference (or round-robin) selects among that subset.

## 3. Core concept

```
 zone-based:   candidates = instances where instance.zone == caller's configured zone
               (fallback to all instances if the local zone has none)

 hint-based:   candidates = instances where instance.metadata["hint"] == request's hint
               (a request with no hint, or an instance with no matching hint tag, doesn't filter that dimension)
```

Both are supplier-chain filters (from the `ServiceInstanceListSupplier` card) — they narrow the candidate list *before* the selection algorithm ever runs, exactly like the health/zone-filter chain built earlier.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request tagged with a canary hint is filtered down to only instances advertising that same hint in their metadata, bypassing every other instance regardless of zone">
  <rect x="30" y="20" width="200" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="130" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">.1 (zone a, hint=stable)</text>
  <rect x="230" y="20" width="200" height="30" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.3"/>
  <text x="330" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">.2 (zone a, hint=canary)</text>
  <rect x="430" y="20" width="180" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="520" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">.3 (zone b, hint=stable)</text>

  <rect x="150" y="90" width="200" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="250" y="112" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">request with hint=canary</text>

  <line x1="250" y1="90" x2="330" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a56)"/>
  <line x1="220" y1="90" x2="130" y2="55" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="380" y1="90" x2="500" y2="55" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <text x="250" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">only .2 (matching hint) is eligible -- .1 and .3 skipped regardless of zone</text>

  <defs><marker id="a56" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A hint filters purely on the metadata tag, cutting across zone boundaries entirely.

## 5. Runnable example

The scenario: route canary traffic to `billing-service`. Start with plain zone preference, then add hint-based filtering for canary routing, then combine both filters together for a zone-aware canary rollout.

### Level 1 — Basic

Plain zone preference, as a refresher baseline (same mechanism as the earlier Eureka zone-awareness card).

```java
import java.util.*;
import java.util.stream.Collectors;

public class ZoneHintBalancingLevel1 {
    record Instance(String address, String zone, String hint) {}

    static List<Instance> instances = List.of(
            new Instance("10.0.2.1:8080", "us-east-1a", "stable"),
            new Instance("10.0.2.2:8080", "us-east-1a", "canary"),
            new Instance("10.0.2.3:8080", "us-east-1b", "stable")
    );

    static List<Instance> zoneFiltered(List<Instance> candidates, String zone) {
        List<Instance> sameZone = candidates.stream().filter(i -> i.zone().equals(zone)).collect(Collectors.toList());
        return sameZone.isEmpty() ? candidates : sameZone;
    }

    public static void main(String[] args) {
        System.out.println("zone-filtered (us-east-1a): " + zoneFiltered(instances, "us-east-1a"));
    }
}
```

How to run: `java ZoneHintBalancingLevel1.java`

Filtering to `us-east-1a` keeps `.1` and `.2`, dropping `.3` — this is exactly the zone-preference filter from earlier, now with a `hint` field on each instance that isn't used yet.

### Level 2 — Intermediate

Add hint-based filtering: only keep instances whose `hint` matches the request's requested hint.

```java
import java.util.*;
import java.util.stream.Collectors;

public class ZoneHintBalancingLevel2 {
    record Instance(String address, String zone, String hint) {}

    static List<Instance> instances = List.of(
            new Instance("10.0.2.1:8080", "us-east-1a", "stable"),
            new Instance("10.0.2.2:8080", "us-east-1a", "canary"),
            new Instance("10.0.2.3:8080", "us-east-1b", "stable")
    );

    static List<Instance> hintFiltered(List<Instance> candidates, String requestedHint) {
        if (requestedHint == null) return candidates; // no hint requested -- don't filter on this dimension at all
        List<Instance> matching = candidates.stream().filter(i -> i.hint().equals(requestedHint)).collect(Collectors.toList());
        return matching.isEmpty() ? candidates : matching; // fall back if nothing actually has this hint
    }

    public static void main(String[] args) {
        System.out.println("hint=canary -> " + hintFiltered(instances, "canary"));
        System.out.println("hint=null (default traffic) -> " + hintFiltered(instances, null));
    }
}
```

How to run: `java ZoneHintBalancingLevel2.java`

`hintFiltered(instances, "canary")` keeps only `.2`, the single instance tagged `canary` — normal, unhinted requests (`hintFiltered(instances, null)`) pass through completely untouched, which is exactly the intended behavior: hint-based routing is opt-in per request, and the vast majority of ordinary traffic should never be filtered by it at all.

### Level 3 — Advanced

Combine both filters in a chain — hint filtering first (narrowing to the canary subset), then zone preference within that subset — modeling a zone-aware canary rollout, and confirm the final selection only ever draws from instances satisfying both conditions.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

public class ZoneHintBalancingLevel3 {
    record Instance(String address, String zone, String hint) {}

    static List<Instance> instances = List.of(
            new Instance("10.0.2.1:8080", "us-east-1a", "stable"),
            new Instance("10.0.2.2:8080", "us-east-1a", "canary"),
            new Instance("10.0.2.3:8080", "us-east-1b", "stable"),
            new Instance("10.0.2.4:8080", "us-east-1b", "canary")
    );

    static List<Instance> hintFiltered(List<Instance> candidates, String requestedHint) {
        if (requestedHint == null) return candidates;
        List<Instance> matching = candidates.stream().filter(i -> i.hint().equals(requestedHint)).collect(Collectors.toList());
        return matching.isEmpty() ? candidates : matching;
    }

    static List<Instance> zoneFiltered(List<Instance> candidates, String zone) {
        List<Instance> sameZone = candidates.stream().filter(i -> i.zone().equals(zone)).collect(Collectors.toList());
        return sameZone.isEmpty() ? candidates : sameZone;
    }

    static AtomicInteger counter = new AtomicInteger(0);
    static Instance pick(List<Instance> candidates) {
        return candidates.get(counter.getAndIncrement() % candidates.size());
    }

    public static void main(String[] args) {
        String callerZone = "us-east-1a";
        String requestedHint = "canary";

        List<Instance> afterHint = hintFiltered(instances, requestedHint);
        List<Instance> afterZone = zoneFiltered(afterHint, callerZone);

        System.out.println("after hint filter: " + afterHint);
        System.out.println("after zone filter (on top of hint filter): " + afterZone);

        for (int i = 0; i < 3; i++) System.out.println("pick " + i + " -> " + pick(afterZone).address());
    }
}
```

How to run: `java ZoneHintBalancingLevel3.java`

`afterHint` keeps `.2` and `.4` (both `canary`), dropping the two `stable` instances entirely regardless of zone. `afterZone`, applied on top of `afterHint`, further narrows to just `.2` (the only `canary` instance also in `us-east-1a`) — since that same-zone subset isn't empty, no fallback is needed. All three `pick` calls correctly land on `.2`, the single instance that satisfies both the hint and the zone preference simultaneously.

## 6. Walkthrough

Trace the filter chain construction in Level 3.

1. `hintFiltered(instances, "canary")` runs first — it filters the full four-instance list down to those with `hint.equals("canary")`: `.2` (`us-east-1a`) and `.4` (`us-east-1b`). Since this filtered list isn't empty, it's returned as-is; `.1` and `.3` (both `stable`) are excluded from all further consideration.
2. `zoneFiltered(afterHint, "us-east-1a")` runs next, operating only on the two-instance `afterHint` result, not the original four — it filters for `zone.equals("us-east-1a")`, which matches only `.2`. Since this further-filtered list (`[.2]`) isn't empty, it's returned as the final candidate set.
3. The two `println` calls confirm each stage's output explicitly: `afterHint` shows both canary instances across both zones, and `afterZone` shows the chain has narrowed all the way down to the single instance satisfying both conditions.
4. The three `pick` calls each compute `afterZone.get(counter % afterZone.size())` — since `afterZone.size() == 1`, every single pick, regardless of the counter's value, resolves to index `0`, which is `.2`. Every canary-hinted, zone-`us-east-1a` request in this scenario deterministically lands on the one instance actually eligible for it.

```
instances: [.1(a,stable), .2(a,canary), .3(b,stable), .4(b,canary)]
        |  hintFiltered("canary")
        v
       [.2(a,canary), .4(b,canary)]
        |  zoneFiltered("us-east-1a")
        v
       [.2(a,canary)]              <- only instance satisfying BOTH conditions
        |
        v  pick (any algorithm) -- only one candidate, always resolves here
       .2
```

## 7. Gotchas & takeaways

> **Gotcha:** both zone and hint filters fall back to the unfiltered list when their preferred subset is empty (as modeled by `isEmpty() ? candidates : matching` in both filters) — this is a deliberate availability-over-strictness tradeoff, but it means a canary hint with zero matching instances silently sends traffic to *any* instance, including non-canary ones, rather than failing loudly. If a canary rollout genuinely requires isolation (traffic must never leak to non-canary instances even if the canary pool is temporarily empty), this fallback behavior needs to be explicitly disabled or handled differently.

- Zone and hint filtering are both supplier-chain decorators, composable with each other and with health filtering, in whatever order the deployment's priorities dictate — filter for correctness first, then preference, as established in the earlier supplier-chain card.
- Hint-based routing is the standard mechanism for canary deployments and A/B testing within Spring Cloud LoadBalancer — tag the new version's instances, configure or pass the hint, and only tagged traffic reaches them.
- Because hint filtering happens before the selection algorithm runs, the algorithm itself (round-robin, random) needs no awareness of canary/hint logic at all — it just balances across whatever the filtered candidate list happens to contain.
- Configuring a default hint per service (`spring.cloud.loadbalancer.hint.billing-service=canary`) versus passing a per-request hint gives two different granularities of control — a static default for "this whole client always wants canary traffic" versus a dynamic per-call override for finer-grained testing.
