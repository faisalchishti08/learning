---
card: microservices
gi: 187
slug: service-registry-as-source-of-truth
title: "Service registry as source of truth"
---

## 1. What it is

Treating the service registry as the single source of truth means every component making a routing or discovery decision — a [gateway](0157-api-gateway-pattern.md), a load balancer, another service's [client-side discovery](0185-client-side-service-discovery.md) logic — defers entirely to what the registry currently reports, rather than any component maintaining its own separately cached, potentially conflicting belief about which instances exist and are healthy.

## 2. Why & when

If different components in a system each maintain their own independent view of "what instances exist" — one cached from an old lookup, another refreshed a moment ago, a third hard-coded from deployment-time configuration — those views can and eventually will disagree, and different callers making decisions based on different, conflicting information produces inconsistent, hard-to-diagnose routing behavior: one caller successfully reaching a healthy instance while another simultaneously fails trying to reach an instance that already shut down. Designating the registry as the single, authoritative source of truth eliminates this class of problem by construction — every component's view is *derived from* the same registry, so any staleness or disagreement is at worst a temporary propagation delay, not a fundamentally conflicting, independently-maintained belief.

Apply this principle consistently across a system's discovery-related components: any cache of instance information should be explicitly understood as a *cache* of the registry's data (with a bounded staleness window), never as an independent record that could diverge and be trusted over the registry itself. When a discrepancy is found, the registry's current state is correct by definition, and any other component's view is what needs to be refreshed or corrected.

## 3. Core concept

Every discovery decision traces back to a single query (or a bounded-staleness cache of a query) against the registry; no component invents, hard-codes, or independently maintains conflicting instance information that could disagree with what the registry itself currently reports.

```java
// WRONG: a gateway maintaining its OWN separately-updated instance list, that
// could drift out of sync with what the registry ACTUALLY says
gateway.knownInstances = List.of(hardcodedInstanceA, hardcodedInstanceB); // an INDEPENDENT belief -- can conflict with the registry

// RIGHT: every component queries (or caches, WITH bounded staleness) the SAME registry
List<ServiceInstance> instances = registry.getInstances("order-service"); // the registry is the ONLY authority
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three components -- a gateway, a load balancer, and a client-side discovery caller -- all derive their view of order-service's instances from the same single registry, rather than each maintaining an independent, potentially conflicting record" >
  <rect x="240" y="20" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service Registry</text>

  <rect x="30" y="120" width="140" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="100" y="142" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Gateway</text>
  <rect x="250" y="120" width="140" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="320" y="142" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Load Balancer</text>
  <rect x="470" y="120" width="140" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="540" y="142" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Client-side caller</text>

  <line x1="100" y1="120" x2="270" y2="62" stroke="#8b949e" marker-end="url(#arr68)"/>
  <line x1="320" y1="120" x2="320" y2="62" stroke="#8b949e" marker-end="url(#arr68)"/>
  <line x1="540" y1="120" x2="370" y2="62" stroke="#8b949e" marker-end="url(#arr68)"/>

  <text x="320" y="175" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">every view traces back to the SAME single authoritative source</text>

  <defs>
    <marker id="arr68" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Every discovery-aware component's view derives from the same registry, eliminating conflicting independent beliefs.

## 5. Runnable example

Scenario: a gateway and a load balancer that start maintaining independently updated, drifting instance lists (showing the resulting inconsistency), refactor to both deriving their view from the same shared registry, and finally demonstrate a bounded-staleness cache used correctly — refreshed periodically from the registry rather than maintained as an independent, divergent record.

### Level 1 — Basic

```java
// File: IndependentDriftingLists.java -- the GATEWAY and the LOAD BALANCER each
// maintain their OWN instance list, updated at DIFFERENT times -- they DRIFT apart.
import java.util.*;

public class IndependentDriftingLists {
    record ServiceInstance(String id) {}

    static class Gateway {
        List<ServiceInstance> knownInstances = new ArrayList<>(List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b")));
    }
    static class LoadBalancer {
        List<ServiceInstance> knownInstances = new ArrayList<>(List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b")));
    }

    public static void main(String[] args) {
        Gateway gateway = new Gateway();
        LoadBalancer loadBalancer = new LoadBalancer();

        // order-a shuts down -- but ONLY the gateway's operator remembers to update ITS list
        gateway.knownInstances.removeIf(i -> i.id().equals("order-a"));
        // NOBODY updated loadBalancer's list -- it's now WRONG

        System.out.println("Gateway believes: " + gateway.knownInstances);
        System.out.println("Load balancer believes: " + loadBalancer.knownInstances);
        System.out.println("DISAGREEMENT: the load balancer will still route to a DEAD instance the gateway already knows is gone.");
    }
}
```

**How to run:** `javac IndependentDriftingLists.java && java IndependentDriftingLists` (JDK 17+).

### Level 2 — Intermediate

```java
// File: SharedRegistryAsSingleAuthority.java -- BOTH components query the SAME
// registry -- there is NO way for them to disagree, since neither maintains its OWN list.
import java.util.*;

public class SharedRegistryAsSingleAuthority {
    record ServiceInstance(String id) {}

    static class ServiceRegistry {
        List<ServiceInstance> instances = new ArrayList<>(List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b")));
        void deregister(String id) { instances.removeIf(i -> i.id().equals(id)); }
        List<ServiceInstance> getInstances() { return instances; } // the ONLY place instance data lives
    }

    static class Gateway {
        ServiceRegistry registry; // NO local list -- ONLY a reference to the shared registry
        Gateway(ServiceRegistry registry) { this.registry = registry; }
        List<ServiceInstance> currentView() { return registry.getInstances(); } // ALWAYS queries fresh
    }
    static class LoadBalancer {
        ServiceRegistry registry;
        LoadBalancer(ServiceRegistry registry) { this.registry = registry; }
        List<ServiceInstance> currentView() { return registry.getInstances(); }
    }

    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry(); // ONE registry, shared
        Gateway gateway = new Gateway(registry);
        LoadBalancer loadBalancer = new LoadBalancer(registry);

        registry.deregister("order-a"); // updated ONCE, in the ONE authoritative place

        System.out.println("Gateway's current view: " + gateway.currentView());
        System.out.println("Load balancer's current view: " + loadBalancer.currentView());
        System.out.println("BOTH agree, ALWAYS -- there is structurally NO way for them to disagree, since neither has its OWN list.");
    }
}
```

**How to run:** `javac SharedRegistryAsSingleAuthority.java && java SharedRegistryAsSingleAuthority` (JDK 17+).

Expected output:
```
Gateway's current view: [ServiceInstance[id=order-b]]
Load balancer's current view: [ServiceInstance[id=order-b]]
BOTH agree, ALWAYS -- there is structurally NO way for them to disagree, since neither has its OWN list.
```

### Level 3 — Advanced

```java
// File: BoundedStalenessCacheDoneRight.java -- a CACHE is fine for performance,
// but must be explicitly understood as a TEMPORARY snapshot of the registry, refreshed
// periodically -- NEVER treated as an independent, authoritative record of its own.
import java.util.*;

public class BoundedStalenessCacheDoneRight {
    record ServiceInstance(String id) {}

    static class ServiceRegistry {
        List<ServiceInstance> instances = new ArrayList<>(List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b")));
        void deregister(String id) { instances.removeIf(i -> i.id().equals(id)); }
        List<ServiceInstance> getInstances() { return new ArrayList<>(instances); } // a fresh COPY each query
    }

    // a CACHE, correctly implemented: refreshes FROM the registry, never independently modified
    static class CachedDiscoveryClient {
        ServiceRegistry registry;
        List<ServiceInstance> cachedInstances;
        long lastRefreshMillis;
        long cacheTtlMillis;
        CachedDiscoveryClient(ServiceRegistry registry, long cacheTtlMillis) {
            this.registry = registry; this.cacheTtlMillis = cacheTtlMillis;
            refresh(0);
        }
        void refresh(long nowMillis) {
            cachedInstances = registry.getInstances(); // ALWAYS pulled FROM the registry -- never invented locally
            lastRefreshMillis = nowMillis;
        }
        List<ServiceInstance> getInstances(long nowMillis) {
            if (nowMillis - lastRefreshMillis > cacheTtlMillis) refresh(nowMillis); // bounded staleness -- auto-refreshes
            return cachedInstances;
        }
    }

    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();
        CachedDiscoveryClient client = new CachedDiscoveryClient(registry, 1000); // 1-second cache TTL

        System.out.println("t=0, cached view: " + client.getInstances(0));

        registry.deregister("order-a"); // the REGISTRY (authoritative) is updated immediately
        System.out.println("t=500, cached view (WITHIN TTL, deliberately stale for a moment): " + client.getInstances(500));

        System.out.println("t=1500, cached view (TTL expired, auto-refreshed FROM the registry): " + client.getInstances(1500));
        System.out.println("The cache was NEVER independently wrong -- it was DELIBERATELY, boundedly stale, then self-corrected by refreshing FROM the single source of truth.");
    }
}
```

**How to run:** `javac BoundedStalenessCacheDoneRight.java && java BoundedStalenessCacheDoneRight` (JDK 17+).

Expected output:
```
t=0, cached view: [ServiceInstance[id=order-a], ServiceInstance[id=order-b]]
t=500, cached view (WITHIN TTL, deliberately stale for a moment): [ServiceInstance[id=order-a], ServiceInstance[id=order-b]]
t=1500, cached view (TTL expired, auto-refreshed FROM the registry): [ServiceInstance[id=order-b]]
```

## 6. Walkthrough

1. **Level 1** — `Gateway.knownInstances` and `LoadBalancer.knownInstances` are two entirely separate `List` fields, each independently constructed and independently mutable; removing `order-a` from `gateway.knownInstances` has no effect whatsoever on `loadBalancer.knownInstances`, since they are unrelated objects.
2. **Level 1, the resulting disagreement** — the printed output shows the gateway believing only `order-b` remains while the load balancer still believes both `order-a` and `order-b` are available, a direct, structural inconsistency stemming from each component owning its own independent data.
3. **Level 2, removing independent state entirely** — neither `Gateway` nor `LoadBalancer` has a `knownInstances` field anymore; both hold only a `registry` reference and implement `currentView()` by calling `registry.getInstances()` directly.
4. **Level 2, structural agreement, not coincidental agreement** — after `registry.deregister("order-a")` is called exactly once, both `gateway.currentView()` and `loadBalancer.currentView()` reflect the change identically — not because someone remembered to update both, but because there is only one place ("the registry") where instance data exists at all.
5. **Level 3, a cache that still defers to the registry** — `CachedDiscoveryClient.refresh` always assigns `cachedInstances = registry.getInstances()`, pulling fresh data from the registry itself; nothing in this class ever constructs or modifies instance data independently.
6. **Level 3, bounded, temporary staleness versus independent wrongness** — at `t=500`, the cache still reports `order-a` as present, even though the registry has already removed it — but this is *deliberate*, bounded staleness governed by `cacheTtlMillis`, not an independently-diverged belief; the cache is explicitly a time-bounded snapshot, not a competing authority.
7. **Level 3, the self-correcting refresh** — at `t=1500`, `getInstances` detects `nowMillis - lastRefreshMillis > cacheTtlMillis` (1500 > 1000) and calls `refresh(1500)`, which re-pulls the current state directly from `registry`, correctly reflecting `order-a`'s removal — the key structural difference from Level 1's problem is that this cache's staleness is bounded, self-correcting, and always resolves back toward the registry's authoritative state, rather than drifting arbitrarily far from it with no mechanism to reconcile.

## 7. Gotchas & takeaways

> **Gotcha:** even a correctly-implemented, registry-derived cache introduces a real propagation delay — a newly registered instance, or a just-deregistered one, won't be reflected in a cached view until that cache's next refresh, meaning "the registry is the single source of truth" doesn't mean "every component sees changes instantaneously," only that every component's *eventual* view is consistent with, and derived from, the same authoritative source, never independently conflicting with it.

- Treating the service registry as the single source of truth means every discovery-aware component derives its view of available instances from the registry, rather than maintaining its own independently-updated, potentially conflicting record.
- Components with separately maintained instance lists can and will drift out of sync over time, producing inconsistent routing behavior across different parts of the system.
- Deriving every component's view from the same registry eliminates this class of disagreement by construction, since there is structurally only one place where instance data is authoritative.
- Caching for performance is compatible with this principle, as long as the cache is explicitly understood as a bounded-staleness snapshot of the registry, always refreshed from it, never an independent record of its own.
- Even a correctly-implemented cache introduces propagation delay; the source-of-truth principle guarantees eventual consistency toward the registry's state, not instantaneous consistency across every component at every moment.
