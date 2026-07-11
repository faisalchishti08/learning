---
card: spring-cloud
gi: 54
slug: reactorloadbalancer-serviceinstancelistsupplier
title: "ReactorLoadBalancer & ServiceInstanceListSupplier"
---

## 1. What it is

`ReactorLoadBalancer<ServiceInstance>` is the interface actual load-balancing strategies implement (the reactive foundation LoadBalancer's algorithms — round-robin, random — are built on), and `ServiceInstanceListSupplier` is the interface that supplies the candidate instance list a `ReactorLoadBalancer` picks from. Splitting these two lets the "where do candidate instances come from" question (discovery, filtering by health, filtering by zone) evolve independently of the "which one do we pick" question.

```java
@Bean
ReactorLoadBalancer<ServiceInstance> customLoadBalancer(
        Environment environment, LoadBalancerClientFactory factory) {
    String serviceId = environment.getProperty(LoadBalancerClientFactory.PROPERTY_NAME);
    return new RoundRobinLoadBalancer(
            factory.getLazyProvider(serviceId, ServiceInstanceListSupplier.class), serviceId);
}
```

## 2. Why & when

The earlier LoadBalancer card modeled discovery-and-select as two informally separate steps; `ServiceInstanceListSupplier` and `ReactorLoadBalancer` are the actual named interfaces Spring Cloud LoadBalancer uses for exactly that split. `ServiceInstanceListSupplier` implementations can be chained/decorated — one supplier fetches from discovery, another wraps it to filter unhealthy instances, another wraps *that* to filter by zone — and the `ReactorLoadBalancer` at the end just consumes whatever final, filtered list comes out, with no awareness of how it was built.

Understanding this split matters when:

- Customizing which instances are even eligible for selection — filtering by zone, by a custom metadata tag, by a health signal beyond what discovery alone reports — which is done by supplying a custom or decorated `ServiceInstanceListSupplier`, not by touching the balancing algorithm itself.
- Customizing the selection algorithm itself — implementing a new `ReactorLoadBalancer` (weighted balancing, sticky sessions) that can then work with *any* supplier, unchanged.
- Debugging "why isn't this instance ever selected" — the answer is either it never appears in the supplier's list (a filtering problem) or it appears but the algorithm never picks it (a selection problem) — knowing the split narrows down where to look.

## 3. Core concept

```
 ServiceInstanceListSupplier chain:
   DiscoveryClientServiceInstanceListSupplier   (raw list from Eureka/Consul/Zookeeper)
       -> wrapped by HealthCheckServiceInstanceListSupplier   (filters out unhealthy)
       -> wrapped by ZonePreferenceServiceInstanceListSupplier (prefers same-zone instances)
       -> final filtered list

 ReactorLoadBalancer:
   consumes the FINAL list from the supplier chain
   applies its algorithm (round-robin, random, custom) to pick ONE instance
```

Each supplier in the chain narrows or reorders the candidate list; the balancer at the end just picks from whatever it's handed.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A chain of service instance list suppliers narrows the candidate list from raw discovery results through health filtering and zone preference before the load balancer picks one instance">
  <rect x="20" y="70" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="95" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">raw discovery list</text>

  <line x1="170" y1="90" x2="215" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a54)"/>

  <rect x="220" y="70" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="295" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">health-filtered</text>
  <text x="295" y="102" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">supplier wraps supplier</text>

  <line x1="370" y1="90" x2="415" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a54)"/>

  <rect x="420" y="70" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="495" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">zone-preferred</text>

  <line x1="495" y1="110" x2="495" y2="140" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a54)"/>

  <rect x="380" y="145" width="230" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="170" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ReactorLoadBalancer picks 1</text>

  <defs><marker id="a54" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each stage in the supplier chain is a decorator around the previous one, progressively narrowing the list the final balancer sees.

## 5. Runnable example

The scenario: build a `ServiceInstanceListSupplier` decorator chain for `billing-service`, growing from a raw discovery supplier, to a health-filtering decorator, to a zone-preference decorator — with the balancing algorithm (round-robin) plugged in unchanged at every step.

### Level 1 — Basic

A raw `ServiceInstanceListSupplier` — just wraps the discovery result directly.

```java
import java.util.*;

public class SupplierChainLevel1 {
    record Instance(String address, String zone, boolean healthy) {}

    interface InstanceListSupplier {
        List<Instance> get();
    }

    static InstanceListSupplier discoverySupplier = () -> List.of(
            new Instance("10.0.2.1:8080", "us-east-1a", true),
            new Instance("10.0.2.2:8080", "us-east-1a", false), // unhealthy
            new Instance("10.0.2.3:8080", "us-east-1b", true)
    );

    public static void main(String[] args) {
        System.out.println("raw supplier result: " + discoverySupplier.get());
    }
}
```

How to run: `java SupplierChainLevel1.java`

`discoverySupplier` mirrors `DiscoveryClientServiceInstanceListSupplier`: it returns exactly what discovery reports, including an instance that's actually unhealthy — no filtering has happened yet at this stage.

### Level 2 — Intermediate

Wrap the raw supplier with a health-filtering decorator, modeling `HealthCheckServiceInstanceListSupplier`.

```java
import java.util.*;
import java.util.stream.Collectors;

public class SupplierChainLevel2 {
    record Instance(String address, String zone, boolean healthy) {}

    interface InstanceListSupplier { List<Instance> get(); }

    static InstanceListSupplier discoverySupplier = () -> List.of(
            new Instance("10.0.2.1:8080", "us-east-1a", true),
            new Instance("10.0.2.2:8080", "us-east-1a", false),
            new Instance("10.0.2.3:8080", "us-east-1b", true)
    );

    static InstanceListSupplier healthFiltered(InstanceListSupplier delegate) {
        return () -> delegate.get().stream().filter(Instance::healthy).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        InstanceListSupplier chain = healthFiltered(discoverySupplier);
        System.out.println("health-filtered result: " + chain.get());
    }
}
```

How to run: `java SupplierChainLevel2.java`

`healthFiltered` wraps `discoverySupplier`, calling its `get()` and filtering the result — the unhealthy `.2` instance disappears from the output, exactly what `HealthCheckServiceInstanceListSupplier` does when decorating a raw discovery supplier. Note the raw supplier itself is completely unmodified; the filtering is purely additive, applied by the wrapper.

### Level 3 — Advanced

Add a zone-preference decorator on top of the health filter, and plug the final chain into a round-robin `ReactorLoadBalancer`-equivalent, confirming the balancer only ever sees the fully filtered, zone-preferred list.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

public class SupplierChainLevel3 {
    record Instance(String address, String zone, boolean healthy) {}

    interface InstanceListSupplier { List<Instance> get(); }

    static InstanceListSupplier discoverySupplier = () -> List.of(
            new Instance("10.0.2.1:8080", "us-east-1a", true),
            new Instance("10.0.2.2:8080", "us-east-1a", false),
            new Instance("10.0.2.3:8080", "us-east-1b", true),
            new Instance("10.0.2.4:8080", "us-east-1a", true)
    );

    static InstanceListSupplier healthFiltered(InstanceListSupplier delegate) {
        return () -> delegate.get().stream().filter(Instance::healthy).collect(Collectors.toList());
    }

    static InstanceListSupplier zonePreferred(InstanceListSupplier delegate, String callerZone) {
        return () -> {
            List<Instance> all = delegate.get();
            List<Instance> sameZone = all.stream().filter(i -> i.zone().equals(callerZone)).collect(Collectors.toList());
            return sameZone.isEmpty() ? all : sameZone;
        };
    }

    interface ReactorLoadBalancer { Instance choose(List<Instance> instances); }

    static class RoundRobinLoadBalancer implements ReactorLoadBalancer {
        AtomicInteger counter = new AtomicInteger(0);
        public Instance choose(List<Instance> instances) {
            return instances.get(counter.getAndIncrement() % instances.size());
        }
    }

    public static void main(String[] args) {
        InstanceListSupplier finalChain = zonePreferred(healthFiltered(discoverySupplier), "us-east-1a");
        ReactorLoadBalancer balancer = new RoundRobinLoadBalancer();

        System.out.println("final supplier chain output: " + finalChain.get());
        for (int i = 0; i < 4; i++) {
            System.out.println("pick " + i + " -> " + balancer.choose(finalChain.get()).address());
        }
    }
}
```

How to run: `java SupplierChainLevel3.java`

`finalChain` is `zonePreferred(healthFiltered(discoverySupplier), "us-east-1a")` — health filtering runs first (removing `.2`), then zone preference runs on the *already-filtered* result (keeping only the `us-east-1a` instances, `.1` and `.4`, since that zone still has healthy instances after filtering). The `RoundRobinLoadBalancer` only ever sees this final two-instance list and alternates cleanly between `.1` and `.4` — it has no idea `.2` or `.3` even exist, because they were filtered out upstream before it ever ran.

## 6. Walkthrough

Trace `finalChain.get()`'s construction and the subsequent picks in Level 3.

1. `finalChain.get()` is called (implicitly, each time `balancer.choose(finalChain.get())` runs) — this invokes the outermost decorator, `zonePreferred`, whose lambda first calls `delegate.get()`, which is `healthFiltered(discoverySupplier)`.
2. `healthFiltered`'s lambda calls `discoverySupplier.get()`, returning all four raw instances, then filters to `Instance::healthy`, dropping `.2` (unhealthy) and keeping `.1`, `.3`, `.4`.
3. Back in `zonePreferred`, that three-instance health-filtered list is now filtered again for `zone.equals("us-east-1a")` — `.1` and `.4` match, `.3` (zone `us-east-1b`) doesn't. Since the same-zone list isn't empty, it's returned as the final result: `[.1, .4]`.
4. The first `println` confirms this final chain output directly: two instances, both healthy and both in the caller's zone.
5. The four `balancer.choose(...)` calls each re-run the entire chain (`finalChain.get()` is called fresh each time in this simplified model; a real implementation would typically cache/reactively stream this rather than recomputing per call) and then round-robin across the resulting two-instance list: pick 0 gets `.1` (index `0 % 2`), pick 1 gets `.4` (index `1 % 2`), pick 2 wraps back to `.1`, pick 3 gets `.4` again.

```
discoverySupplier.get()      -> [.1(healthy), .2(unhealthy), .3(zone b), .4(healthy)]
        |  healthFiltered
        v
                              -> [.1, .3, .4]
        |  zonePreferred("us-east-1a")
        v
                              -> [.1, .4]   (.3 dropped, wrong zone; same-zone list non-empty so no fallback needed)
        |
        v  RoundRobinLoadBalancer, sees ONLY this final list
pick 0 -> .1   pick 1 -> .4   pick 2 -> .1   pick 3 -> .4
```

## 7. Gotchas & takeaways

> **Gotcha:** decorator order matters — health filtering *then* zone preference (as here) correctly falls back to other zones only among healthy instances; doing it in the opposite order (zone preference first, then health filtering) could zone-restrict down to a list that then gets entirely filtered out by health checks, when a perfectly good instance existed in another zone all along. Always filter for correctness (health) before filtering for preference (zone).

- `ServiceInstanceListSupplier` and `ReactorLoadBalancer` cleanly separate "which instances are eligible" from "which eligible instance gets picked" — most customization needs (filtering, ordering) belong in the supplier chain, not the balancing algorithm.
- Decorators compose in the order they wrap each other — always trace outward-to-inward carefully when stacking multiple suppliers, since each one only sees what the one inside it returns.
- A `ReactorLoadBalancer` implementation is reusable across any supplier chain — the round-robin algorithm here has zero knowledge of health checks or zones, and would work identically with a completely different supplier chain in front of it.
- This is the same layered-decorator idea seen elsewhere in Spring (`HandlerInterceptor` chains, servlet filter chains) — recognizing the pattern makes both reading Spring Cloud LoadBalancer's source and writing custom suppliers much more approachable.
