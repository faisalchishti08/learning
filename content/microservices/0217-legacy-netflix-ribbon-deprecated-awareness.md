---
card: microservices
gi: 217
slug: legacy-netflix-ribbon-deprecated-awareness
title: "Legacy Netflix Ribbon (deprecated) awareness"
---

## 1. What it is

Netflix Ribbon was the original client-side load-balancing library in the Spring Cloud ecosystem, integrated via `spring-cloud-starter-netflix-ribbon` — the load balancer applications used before [Spring Cloud LoadBalancer](0212-spring-cloud-loadbalancer-default-client-side-lb.md) existed. Ribbon is now deprecated and in maintenance mode; awareness of it matters for recognizing and migrating legacy systems that still depend on it, not for building anything new.

## 2. Why & when

Ribbon predates Spring Cloud LoadBalancer by years and was built with its own configuration model (`ribbon.*` properties, `IRule` implementations for selection strategy, `ServerList` for candidate resolution) that entirely predates Spring Cloud LoadBalancer's `ServiceInstanceListSupplier`-based composition model covered in [custom LoadBalancer configuration](0214-custom-loadbalancer-configuration-serviceinstancelistsupplie.md). As with [Zuul](0181-legacy-spring-cloud-netflix-zuul-deprecated-awareness.md), Netflix moved away from actively maintaining Ribbon, and Spring Cloud LoadBalancer became the standard, actively maintained replacement — meaning Ribbon-based systems keep functioning but sit on an architecture receiving no further active development.

Recognize Ribbon-based configuration in an older codebase (`spring-cloud-starter-netflix-ribbon` as a dependency, `<service-name>.ribbon.*` configuration properties, or custom `IRule` classes) and plan a migration to Spring Cloud LoadBalancer as part of routine modernization — not urgently, since Ribbon continues to function for existing deployments, but as accumulating technical debt. Do not choose Ribbon for any new client-side load-balancing implementation; Spring Cloud LoadBalancer is the only actively recommended choice today.

## 3. Core concept

Ribbon's selection-strategy and candidate-list concepts map onto Spring Cloud LoadBalancer's equivalent concepts, but with different terminology and a different underlying architecture — recognizing the mapping is what turns a Ribbon-to-LoadBalancer migration into a translation exercise rather than a redesign.

```java
// RIBBON (legacy) -- selection strategy via a custom IRule
public class MyCustomRule extends AbstractLoadBalancerRule {
    public Server choose(Object key) { /* pick a Server from the candidate ServerList */ return null; }
}
// RIBBON (legacy) -- candidate list configuration via properties
order-service.ribbon.listOfServers: 10.0.1.5:8080,10.0.1.6:8080

// SPRING CLOUD LOADBALANCER (current) -- the CONCEPTUAL equivalent, different API
class MyReactorLoadBalancer implements ReactorServiceInstanceLoadBalancer { // maps from IRule
    public Mono<Response<ServiceInstance>> choose(Request request) { /* pick a ServiceInstance */ return null; }
}
class MyServiceInstanceListSupplier implements ServiceInstanceListSupplier { // maps from ServerList
    public Flux<List<ServiceInstance>> get() { /* supply the candidate list */ return null; }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ribbon's IRule and ServerList concepts map onto Spring Cloud LoadBalancer's equivalent concepts: IRule corresponds to ReactorServiceInstanceLoadBalancer for selection, and ServerList corresponds to ServiceInstanceListSupplier for candidate resolution" >
  <rect x="20" y="20" width="240" height="130" rx="8" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="140" y="40" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Ribbon (deprecated)</text>
  <text x="40" y="65" fill="#e6edf3" font-size="7.5" font-family="sans-serif">IRule (selection strategy)</text>
  <text x="40" y="90" fill="#e6edf3" font-size="7.5" font-family="sans-serif">ServerList (candidates)</text>
  <text x="40" y="115" fill="#e6edf3" font-size="7.5" font-family="sans-serif">ribbon.* properties</text>

  <rect x="360" y="20" width="260" height="130" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="40" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring Cloud LoadBalancer (current)</text>
  <text x="380" y="65" fill="#e6edf3" font-size="7.5" font-family="sans-serif">ReactorServiceInstanceLoadBalancer</text>
  <text x="380" y="90" fill="#e6edf3" font-size="7.5" font-family="sans-serif">ServiceInstanceListSupplier</text>
  <text x="380" y="115" fill="#e6edf3" font-size="7.5" font-family="sans-serif">DiscoveryClient-backed by default</text>

  <line x1="260" y1="85" x2="358" y2="85" stroke="#8b949e" marker-end="url(#arr217)"/>

  <defs>
    <marker id="arr217" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Ribbon's selection and candidate-resolution concepts have direct equivalents in Spring Cloud LoadBalancer, making migration a mapping exercise rather than a redesign.

## 5. Runnable example

Scenario: a legacy order-service client that starts modeled in Ribbon's `IRule`-plus-`ServerList` style (showing the older architecture's shape), migrates to the equivalent Spring Cloud LoadBalancer style with identical selection behavior preserved, and finally demonstrates the mapping applied to a weighted (not just round-robin) selection strategy, confirming the translation generalizes beyond the simplest case.

### Level 1 — Basic

```java
// File: RibbonStyleSelection.java -- models the SHAPE of Ribbon's legacy
// IRule-based selection PLUS ServerList-based candidates, for comparison.
import java.util.*;

public class RibbonStyleSelection {
    record Server(String host, int port) {}
    interface IRule { Server choose(List<Server> candidates); } // Ribbon's OWN selection abstraction

    static IRule roundRobinRule = new IRule() {
        int index = 0;
        public Server choose(List<Server> candidates) { return candidates.get(index++ % candidates.size()); }
    };

    public static void main(String[] args) {
        List<Server> serverList = List.of(new Server("10.0.1.5", 8080), new Server("10.0.1.6", 8080)); // "ribbon.listOfServers" equivalent

        for (int i = 0; i < 3; i++) {
            Server chosen = roundRobinRule.choose(serverList);
            System.out.println("[Ribbon IRule] chose " + chosen.host() + ":" + chosen.port());
        }
        System.out.println("This is LEGACY Ribbon's shape: a ServerList of candidates PLUS an IRule choosing among them.");
    }
}
```

**How to run:** `javac RibbonStyleSelection.java && java RibbonStyleSelection` (JDK 17+).

### Level 2 — Intermediate

```java
// File: MigratedToLoadBalancerStyle.java -- the SAME selection behavior,
// expressed in Spring Cloud LoadBalancer's supplier/load-balancer model instead.
import java.util.*;
import java.util.function.*;

public class MigratedToLoadBalancerStyle {
    record ServiceInstance(String host, int port) {}
    interface ServiceInstanceListSupplier { List<ServiceInstance> get(); } // maps from Ribbon's ServerList
    interface ReactorServiceInstanceLoadBalancer { ServiceInstance choose(List<ServiceInstance> candidates); } // maps from Ribbon's IRule

    static ServiceInstanceListSupplier supplier = () -> List.of(new ServiceInstance("10.0.1.5", 8080), new ServiceInstance("10.0.1.6", 8080));

    static ReactorServiceInstanceLoadBalancer roundRobinLoadBalancer = new ReactorServiceInstanceLoadBalancer() {
        int index = 0;
        public ServiceInstance choose(List<ServiceInstance> candidates) { return candidates.get(index++ % candidates.size()); }
    };

    public static void main(String[] args) {
        for (int i = 0; i < 3; i++) {
            ServiceInstance chosen = roundRobinLoadBalancer.choose(supplier.get());
            System.out.println("[Spring Cloud LoadBalancer] chose " + chosen.host() + ":" + chosen.port());
        }
        System.out.println("SAME round-robin outcome, SAME two-part structure -- expressed in Spring Cloud LoadBalancer's CURRENT vocabulary instead of Ribbon's.");
    }
}
```

**How to run:** `javac MigratedToLoadBalancerStyle.java && java MigratedToLoadBalancerStyle` (JDK 17+).

Expected output:
```
[Spring Cloud LoadBalancer] chose 10.0.1.5:8080
[Spring Cloud LoadBalancer] chose 10.0.1.6:8080
[Spring Cloud LoadBalancer] chose 10.0.1.5:8080
SAME round-robin outcome, SAME two-part structure -- expressed in Spring Cloud LoadBalancer's CURRENT vocabulary instead of Ribbon's.
```

### Level 3 — Advanced

```java
// File: WeightedRuleConfirmsGeneralization.java -- migrates a SECOND, more
// elaborate Ribbon rule (weighted, not just round-robin) to confirm the
// Ribbon -> LoadBalancer mapping generalizes beyond the simplest strategy.
import java.util.*;

public class WeightedRuleConfirmsGeneralization {
    // === the RIBBON-STYLE original: a weighted IRule ===
    record Server(String host, int weight) {}
    interface IRule { Server choose(List<Server> candidates); }

    static IRule weightedRibbonRule = candidates -> {
        int totalWeight = candidates.stream().mapToInt(Server::weight).sum();
        int r = 15; // fixed "random" pick for reproducible output
        int cumulative = 0;
        for (Server s : candidates) { cumulative += s.weight(); if (r < cumulative) return s; }
        return candidates.get(candidates.size() - 1);
    };

    static void selectViaRibbonStyle(List<Server> servers) {
        Server chosen = weightedRibbonRule.choose(servers);
        System.out.println("[Ribbon weighted IRule] chose " + chosen.host() + " (weight " + chosen.weight() + ")");
    }

    // === the MIGRATED Spring Cloud LoadBalancer equivalent -- SAME weighted logic ===
    record ServiceInstance(String host, int weight) {}
    interface ReactorServiceInstanceLoadBalancer { ServiceInstance choose(List<ServiceInstance> candidates); }

    static ReactorServiceInstanceLoadBalancer weightedLoadBalancer = candidates -> {
        int totalWeight = candidates.stream().mapToInt(ServiceInstance::weight).sum();
        int r = 15; // SAME fixed pick, for direct comparison
        int cumulative = 0;
        for (ServiceInstance s : candidates) { cumulative += s.weight(); if (r < cumulative) return s; }
        return candidates.get(candidates.size() - 1);
    };

    static void selectViaLoadBalancerStyle(List<ServiceInstance> instances) {
        ServiceInstance chosen = weightedLoadBalancer.choose(instances);
        System.out.println("[Spring Cloud LoadBalancer weighted] chose " + chosen.host() + " (weight " + chosen.weight() + ")");
    }

    public static void main(String[] args) {
        System.out.println("=== legacy Ribbon-style weighted selection ===");
        selectViaRibbonStyle(List.of(new Server("10.0.1.5", 10), new Server("10.0.1.6", 30)));

        System.out.println("\n=== migrated Spring Cloud LoadBalancer weighted selection ===");
        selectViaLoadBalancerStyle(List.of(new ServiceInstance("10.0.1.5", 10), new ServiceInstance("10.0.1.6", 30)));

        System.out.println("\nBoth Ribbon's weighted IRule and Spring Cloud LoadBalancer's weighted ReactorServiceInstanceLoadBalancer chose the IDENTICAL instance for the same weights and pick -- the migration preserved behavior for a non-trivial strategy too, not just plain round-robin.");
    }
}
```

**How to run:** `javac WeightedRuleConfirmsGeneralization.java && java WeightedRuleConfirmsGeneralization` (JDK 17+).

Expected output:
```
=== legacy Ribbon-style weighted selection ===
[Ribbon weighted IRule] chose 10.0.1.6 (weight 30)

=== migrated Spring Cloud LoadBalancer weighted selection ===
[Spring Cloud LoadBalancer weighted] chose 10.0.1.6 (weight 30)

Both Ribbon's weighted IRule and Spring Cloud LoadBalancer's weighted ReactorServiceInstanceLoadBalancer chose the IDENTICAL instance for the same weights and pick -- the migration preserved behavior for a non-trivial strategy too, not just plain round-robin.
```

## 6. Walkthrough

1. **Level 1** — `serverList` models Ribbon's `<service>.ribbon.listOfServers` property-based candidate configuration as a plain list, and `roundRobinRule`'s `choose` method mirrors how a real Ribbon `IRule` implementation selects a `Server` from the candidates it's given.
2. **Level 2, the candidate-resolution concept translated** — `ServiceInstanceListSupplier.get()` replaces Ribbon's `ServerList`, and `supplier`'s lambda returns the identical two-instance candidate set Level 1 used, just wrapped behind Spring Cloud LoadBalancer's supplier interface rather than Ribbon's `ServerList` abstraction.
3. **Level 2, the selection concept translated** — `ReactorServiceInstanceLoadBalancer.choose` replaces Ribbon's `IRule.choose`, and `roundRobinLoadBalancer`'s implementation uses the identical round-robin indexing logic as Level 1's `roundRobinRule`, only renamed to match current terminology.
4. **Level 2, the observable equivalence** — running three selections in each level produces the identical `10.0.1.5, 10.0.1.6, 10.0.1.5` rotation, confirming the migration changed only vocabulary and structure, not runtime selection behavior.
5. **Level 3, a Ribbon rule beyond plain round-robin** — `weightedRibbonRule` implements weighted selection (heavier-weighted servers get proportionally larger "slices" of a cumulative range), computing `totalWeight` and walking candidates until the fixed pick value `r` falls within a server's cumulative slice — a materially more complex strategy than Level 1's simple rotation.
6. **Level 3, the Gateway-equivalent weighted strategy** — `weightedLoadBalancer` implements the byte-for-byte identical cumulative-weight algorithm, just expressed through `ReactorServiceInstanceLoadBalancer.choose` instead of `IRule.choose`, using the same fixed pick value `r = 15` for a direct, reproducible comparison.
7. **Level 3, confirming the mapping generalizes** — both `selectViaRibbonStyle` and `selectViaLoadBalancerStyle`, given the same two weighted candidates (weights 10 and 30) and the same pick value, select the identical instance (`10.0.1.6`, since its cumulative range `10..40` contains `r = 15`... note the cumulative check `r < cumulative` after adding weight 10 gives `15 < 10` false, then adding weight 30 gives `15 < 40` true, selecting `10.0.1.6`) — this match, on a non-trivial weighted strategy rather than just round-robin, is what confirms the Ribbon-to-LoadBalancer conceptual mapping generalizes across selection strategies, not just the simplest one.

## 7. Gotchas & takeaways

> **Gotcha:** a Ribbon-to-LoadBalancer migration also changes the *timing model* underneath selection — Ribbon's `ServerList` implementations were commonly polling-based with their own refresh interval, whereas Spring Cloud LoadBalancer's default `ServiceInstanceListSupplier` is built directly on [`DiscoveryClient`](0200-spring-cloud-discoveryclient-abstraction.md), meaning migrating isn't purely a class-renaming exercise — any custom Ribbon `ServerList` refresh logic needs to be re-thought in terms of `DiscoveryClient`'s own refresh semantics, or the [caching layer](0216-loadbalancer-caching-health-checks.md) covered separately.

- Netflix Ribbon is Spring's deprecated, legacy client-side load-balancing library, superseded by [Spring Cloud LoadBalancer](0212-spring-cloud-loadbalancer-default-client-side-lb.md) as the actively recommended choice.
- Ribbon's `IRule` (selection strategy) and `ServerList` (candidate resolution) concepts have direct equivalents in Spring Cloud LoadBalancer's `ReactorServiceInstanceLoadBalancer` and `ServiceInstanceListSupplier`.
- This conceptual mapping holds even for non-trivial strategies like weighted selection, not only the simplest round-robin case, making a Ribbon migration a genuine translation exercise rather than a from-scratch redesign.
- No new client-side load-balancing implementation should be built on Ribbon today; awareness of it is primarily useful for recognizing and planning migration of existing legacy systems.
- A Ribbon migration also involves rethinking the underlying refresh/timing model (Ribbon's own polling versus `DiscoveryClient`-backed resolution), not just renaming classes to their Spring Cloud LoadBalancer equivalents.
