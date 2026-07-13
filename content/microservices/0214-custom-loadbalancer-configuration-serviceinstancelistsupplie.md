---
card: microservices
gi: 214
slug: custom-loadbalancer-configuration-serviceinstancelistsupplie
title: "Custom LoadBalancer configuration & ServiceInstanceListSupplier"
---

## 1. What it is

`ServiceInstanceListSupplier` is the Spring Cloud LoadBalancer extension point that supplies the *candidate list* of instances a load-balancing algorithm chooses from — by composing or replacing this supplier, an application can layer custom filtering (health-check awareness, [zone preference](0207-zone-locality-aware-load-balancing.md), custom metadata-based rules) *before* the selection algorithm ever runs, without needing to reimplement the selection algorithm itself.

## 2. Why & when

The default `ServiceInstanceListSupplier` simply returns whatever `DiscoveryClient` reports, and the default `RoundRobinLoadBalancer` selects from that list unconditionally — sufficient for the common case, but insufficient the moment an application needs custom candidate filtering that the default discovery-plus-selection pipeline doesn't provide on its own. Rather than reimplementing the entire load-balancing algorithm to add this filtering, `ServiceInstanceListSupplier`'s composable, delegating design lets custom filtering logic be layered on top of (or in front of) the existing instance-resolution pipeline, with the actual selection algorithm downstream remaining completely unaware of, and unmodified by, whatever filtering happened upstream.

Customize `ServiceInstanceListSupplier` when the default candidate list needs additional, application-specific filtering — zone preference, metadata-based rules (only route to canary instances for beta users), or any candidate-narrowing logic not covered by the framework's built-in options. Leave it at its default when the unfiltered, discovery-provided instance list is already exactly the right candidate set for the selection algorithm to choose from.

## 3. Core concept

A `ServiceInstanceListSupplier` implementation wraps (delegates to) an upstream supplier, applying its own filtering logic to whatever candidate list the upstream supplier provides, and Spring Cloud LoadBalancer's configuration lets these suppliers be composed in a chain — each one narrowing the candidate set further before the final list reaches the selection algorithm.

```java
// a CUSTOM supplier, DELEGATING to (wrapping) the standard discovery-based supplier
class ZonePreferenceServiceInstanceListSupplier implements ServiceInstanceListSupplier {
    ServiceInstanceListSupplier delegate; // the UPSTREAM supplier being wrapped
    String callerZone;

    public Flux<List<ServiceInstance>> get() {
        return delegate.get().map(instances -> { // FILTER whatever the delegate provides
            List<ServiceInstance> sameZone = instances.stream().filter(i -> callerZone.equals(i.getMetadata().get("zone"))).toList();
            return sameZone.isEmpty() ? instances : sameZone; // fall back if empty
        });
    }
}
// the SELECTION algorithm downstream (round-robin, etc.) is COMPLETELY unaware this filtering happened
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A discovery-based supplier provides the raw instance list; a custom zone-preference supplier wraps and filters it; the resulting narrowed list is what the round-robin selection algorithm actually chooses from, unaware that filtering happened upstream" >
  <rect x="20" y="55" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Discovery supplier</text>

  <rect x="230" y="45" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="68" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Custom filter supplier</text>
  <text x="320" y="84" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">wraps + narrows the list</text>

  <rect x="470" y="55" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Selection algorithm</text>

  <line x1="170" y1="75" x2="228" y2="75" stroke="#8b949e" marker-end="url(#arr92)"/>
  <line x1="410" y1="75" x2="468" y2="75" stroke="#8b949e" marker-end="url(#arr92)"/>

  <defs>
    <marker id="arr92" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Filtering layers compose upstream of selection; the algorithm downstream never needs to know filtering happened.

## 5. Runnable example

Scenario: an order-service instance pool that starts with the default, unfiltered discovery-to-selection pipeline (showing round-robin selecting among all instances, including a canary), wraps the default supplier with a custom filter excluding canary instances for regular traffic, and finally composes two filters together (zone preference and canary exclusion) to demonstrate that multiple independent custom suppliers layer cleanly without interfering with each other.

### Level 1 — Basic

```java
// File: DefaultUnfilteredPipeline.java -- the DEFAULT supplier passes ALL
// discovered instances straight through -- a canary instance receives
// REGULAR traffic it was never meant to get.
import java.util.*;

public class DefaultUnfilteredPipeline {
    record ServiceInstance(String id, Map<String, String> metadata) {}

    interface ServiceInstanceListSupplier { List<ServiceInstance> get(); }

    static class DefaultDiscoverySupplier implements ServiceInstanceListSupplier {
        public List<ServiceInstance> get() {
            return List.of(
                new ServiceInstance("order-a", Map.of("canary", "false")),
                new ServiceInstance("order-b", Map.of("canary", "false")),
                new ServiceInstance("order-canary", Map.of("canary", "true"))); // meant for BETA users ONLY
        }
    }

    public static void main(String[] args) {
        ServiceInstanceListSupplier supplier = new DefaultDiscoverySupplier();
        int index = 0;

        for (int i = 0; i < 3; i++) {
            List<ServiceInstance> candidates = supplier.get(); // ALL instances, unfiltered
            System.out.println("regular traffic candidate: " + candidates.get(index++ % candidates.size()).id());
        }
        System.out.println("order-canary received REGULAR traffic -- it was NEVER supposed to, without explicit opt-in.");
    }
}
```

**How to run:** `javac DefaultUnfilteredPipeline.java && java DefaultUnfilteredPipeline` (JDK 17+).

### Level 2 — Intermediate

```java
// File: CustomFilteringSupplier.java -- a CUSTOM supplier WRAPS the default,
// EXCLUDING canary instances from regular traffic -- selection downstream is
// UNCHANGED and UNAWARE of the filtering.
import java.util.*;

public class CustomFilteringSupplier {
    record ServiceInstance(String id, Map<String, String> metadata) {}
    interface ServiceInstanceListSupplier { List<ServiceInstance> get(); }

    static class DefaultDiscoverySupplier implements ServiceInstanceListSupplier {
        public List<ServiceInstance> get() {
            return List.of(
                new ServiceInstance("order-a", Map.of("canary", "false")),
                new ServiceInstance("order-b", Map.of("canary", "false")),
                new ServiceInstance("order-canary", Map.of("canary", "true")));
        }
    }

    // WRAPS a delegate supplier, FILTERING out canary instances
    static class ExcludeCanarySupplier implements ServiceInstanceListSupplier {
        ServiceInstanceListSupplier delegate;
        ExcludeCanarySupplier(ServiceInstanceListSupplier delegate) { this.delegate = delegate; }
        public List<ServiceInstance> get() {
            return delegate.get().stream().filter(i -> !"true".equals(i.metadata().get("canary"))).toList();
        }
    }

    public static void main(String[] args) {
        // COMPOSE: wrap the default supplier with the custom filter
        ServiceInstanceListSupplier supplier = new ExcludeCanarySupplier(new DefaultDiscoverySupplier());
        int index = 0;

        for (int i = 0; i < 4; i++) {
            List<ServiceInstance> candidates = supplier.get(); // the SELECTION algorithm sees only the FILTERED list
            System.out.println("regular traffic candidate: " + candidates.get(index++ % candidates.size()).id());
        }
        System.out.println("order-canary was NEVER selected -- filtered out BEFORE round-robin even ran, no changes to the selection logic itself.");
    }
}
```

**How to run:** `javac CustomFilteringSupplier.java && java CustomFilteringSupplier` (JDK 17+).

Expected output:
```
regular traffic candidate: order-a
regular traffic candidate: order-b
regular traffic candidate: order-a
regular traffic candidate: order-b
order-canary was NEVER selected -- filtered out BEFORE round-robin even ran, no changes to the selection logic itself.
```

### Level 3 — Advanced

```java
// File: ComposedMultipleFilters.java -- TWO independent custom suppliers
// (zone preference AND canary exclusion) COMPOSE cleanly, layered together,
// each unaware of the other's existence.
import java.util.*;

public class ComposedMultipleFilters {
    record ServiceInstance(String id, Map<String, String> metadata) {}
    interface ServiceInstanceListSupplier { List<ServiceInstance> get(); }

    static class DefaultDiscoverySupplier implements ServiceInstanceListSupplier {
        public List<ServiceInstance> get() {
            return List.of(
                new ServiceInstance("order-a", Map.of("zone", "us-east", "canary", "false")),
                new ServiceInstance("order-b", Map.of("zone", "us-east", "canary", "true")),  // local zone, BUT canary
                new ServiceInstance("order-c", Map.of("zone", "us-west", "canary", "false")),  // stable, but WRONG zone
                new ServiceInstance("order-d", Map.of("zone", "us-east", "canary", "false"))); // local zone, stable -- IDEAL
        }
    }

    static class ExcludeCanarySupplier implements ServiceInstanceListSupplier {
        ServiceInstanceListSupplier delegate;
        ExcludeCanarySupplier(ServiceInstanceListSupplier delegate) { this.delegate = delegate; }
        public List<ServiceInstance> get() { return delegate.get().stream().filter(i -> !"true".equals(i.metadata().get("canary"))).toList(); }
    }

    static class ZonePreferenceSupplier implements ServiceInstanceListSupplier {
        ServiceInstanceListSupplier delegate;
        String callerZone;
        ZonePreferenceSupplier(ServiceInstanceListSupplier delegate, String callerZone) { this.delegate = delegate; this.callerZone = callerZone; }
        public List<ServiceInstance> get() {
            List<ServiceInstance> all = delegate.get();
            List<ServiceInstance> sameZone = all.stream().filter(i -> callerZone.equals(i.metadata().get("zone"))).toList();
            return sameZone.isEmpty() ? all : sameZone;
        }
    }

    public static void main(String[] args) {
        // COMPOSE THREE layers: discovery -> exclude canary -> prefer zone
        ServiceInstanceListSupplier supplier = new ZonePreferenceSupplier(
            new ExcludeCanarySupplier(new DefaultDiscoverySupplier()), "us-east");

        List<ServiceInstance> finalCandidates = supplier.get();
        System.out.println("Final candidate list after BOTH filters composed: " + finalCandidates.stream().map(ServiceInstance::id).toList());
        System.out.println("order-b excluded (canary), order-c excluded (wrong zone) -- ONLY order-a and order-d, the TRULY ideal candidates, remain.");
        System.out.println("Neither ExcludeCanarySupplier NOR ZonePreferenceSupplier knows the OTHER exists -- they compose PURELY through delegation.");
    }
}
```

**How to run:** `javac ComposedMultipleFilters.java && java ComposedMultipleFilters` (JDK 17+).

Expected output:
```
Final candidate list after BOTH filters composed: [order-a, order-d]
order-b excluded (canary), order-c excluded (wrong zone) -- ONLY order-a and order-d, the TRULY ideal candidates, remain.
Neither ExcludeCanarySupplier NOR ZonePreferenceSupplier knows the OTHER exists -- they compose PURELY through delegation.
```

## 6. Walkthrough

1. **Level 1** — `DefaultDiscoverySupplier.get()` returns all three instances unconditionally, including `order-canary`; the round-robin loop treats it identically to the two stable instances, and it receives regular traffic on its scheduled turn — a direct demonstration of the unfiltered default pipeline's limitation.
2. **Level 2, wrapping via delegation** — `ExcludeCanarySupplier` holds a `delegate` field (an instance of `ServiceInstanceListSupplier`, here `DefaultDiscoverySupplier`) and its own `get()` method calls `delegate.get()` first, then applies `.filter(i -> !"true".equals(...))` to the result before returning.
3. **Level 2, the composition point** — `new ExcludeCanarySupplier(new DefaultDiscoverySupplier())` explicitly wires the custom filter in front of the default discovery supplier; the resulting `supplier` variable, from the caller's perspective, is just another `ServiceInstanceListSupplier` — the wrapping is invisible to whatever code ultimately consumes `supplier.get()`.
4. **Level 2, the selection loop unmodified** — the round-robin loop in `main` is structurally identical to Level 1's, operating on whatever `supplier.get()` returns; it required zero changes to accommodate the new filtering behavior, since filtering happened entirely upstream, before this loop ever runs.
5. **Level 3, two independent filter implementations** — `ExcludeCanarySupplier` and `ZonePreferenceSupplier` are each written without any reference to or awareness of the other; both share the identical pattern (hold a `delegate`, call it, transform its result).
6. **Level 3, chaining the composition** — `new ZonePreferenceSupplier(new ExcludeCanarySupplier(new DefaultDiscoverySupplier()), "us-east")` nests three layers: the innermost `DefaultDiscoverySupplier` provides all four instances, `ExcludeCanarySupplier` wraps it and removes `order-b` (canary), and the outermost `ZonePreferenceSupplier` wraps *that* result and further narrows it to only `us-east` instances.
7. **Level 3, tracing the narrowing at each layer** — `DefaultDiscoverySupplier` provides all four instances; `ExcludeCanarySupplier.get()` calls its delegate and removes `order-b`, leaving `[order-a, order-c, order-d]`; `ZonePreferenceSupplier.get()` calls *its* delegate (which is the `ExcludeCanarySupplier`, already having removed the canary), receives that three-instance list, and further filters to only `us-east` instances, removing `order-c` (which is in `us-west`) and leaving exactly `[order-a, order-d]` — the two instances that are simultaneously stable *and* in the caller's local zone, arrived at purely through composed, independent filtering layers, with neither filter needing any knowledge of the other's existence or logic.

## 7. Gotchas & takeaways

> **Gotcha:** the order in which custom `ServiceInstanceListSupplier` layers are composed can matter for correctness or efficiency, even when each individual filter's logic is independent — a filter that's expensive to compute (an async metrics fetch) should generally run *after* cheaper filters have already narrowed the candidate set, to avoid doing expensive work on candidates a cheaper, earlier filter would have excluded anyway; composition order is a real design decision, not an arbitrary implementation detail.

- `ServiceInstanceListSupplier` supplies the candidate instance list a selection algorithm chooses from, and custom implementations can wrap (delegate to) an existing supplier to layer additional filtering logic in front of selection.
- This lets application-specific candidate-narrowing rules (zone preference, canary exclusion, custom metadata-based logic) be added without reimplementing the selection algorithm itself, which remains entirely unaware that any filtering happened upstream.
- Multiple independent custom suppliers compose cleanly through simple delegation, each filter narrowing whatever candidate list its delegate provides, with no coordination or awareness required between them.
- This composable design is what makes Spring Cloud LoadBalancer extensible for application-specific routing needs beyond the built-in default behavior, without requiring a custom selection algorithm for every new filtering requirement.
- The order in which composed filters run can affect both correctness and efficiency; placing cheaper filters before more expensive ones avoids unnecessary work on candidates that would have been excluded anyway.
