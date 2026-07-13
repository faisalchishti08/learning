---
card: microservices
gi: 186
slug: server-side-service-discovery
title: "Server-side service discovery"
---

## 1. What it is

Server-side service discovery has the calling service make a plain call to a stable, well-known address — a load balancer or [gateway](0157-api-gateway-pattern.md) — which itself queries the [service registry](0182-service-registry-concept.md), selects an instance, and forwards the request; the calling service contains no registry-awareness or load-balancing logic at all, unlike [client-side discovery](0185-client-side-service-discovery.md), where the caller performs those steps itself.

## 2. Why & when

Requiring every service that makes outbound calls to integrate a registry client and load-balancing library, as client-side discovery does, becomes a genuine burden in a polyglot system with services written in multiple languages, or simply an unwanted dependency to maintain across every service's codebase. Server-side discovery removes this burden entirely: the calling service issues an ordinary call to a fixed, stable address (which never itself needs to change, since it represents the intermediary, not any specific backend instance), and all discovery and load-balancing complexity is concentrated in exactly one place — the intermediary — rather than duplicated across every caller.

Use server-side discovery when calling services should remain simple and free of registry-specific dependencies, or in polyglot environments where maintaining consistent client libraries across every language would be impractical. This is the default model in Kubernetes (a `Service` object is server-side discovery baked into the platform) and is the model an API gateway implements when it resolves a route's `lb://service-name` destination on the caller's behalf.

## 3. Core concept

The calling service's code contains only an ordinary call to a fixed intermediary address; the intermediary itself performs the registry query, applies load-balancing logic, and forwards the request to whichever backend instance it selects — none of that complexity is visible to, or a dependency of, the calling service.

```java
// the CALLING service: an ORDINARY call, to a FIXED address, no registry-awareness at all
HttpResponse response = httpClient.call("order-service-lb.internal", 80, "/orders/42");

// the INTERMEDIARY (load balancer / gateway): does ALL the discovery work, on the caller's BEHALF
List<ServiceInstance> instances = discoveryClient.getInstances("order-service"); // the caller NEVER does this
ServiceInstance chosen = loadBalancer.choose(instances);
forwardTo(chosen);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The calling service makes an ordinary call to a fixed, stable load balancer address; the load balancer itself queries the registry, selects an instance, and forwards the request -- the caller contains no discovery logic at all" >
  <rect x="20" y="60" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Calling service</text>

  <rect x="230" y="55" width="160" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="78" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Load Balancer</text>
  <text x="310" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">queries registry, chooses</text>

  <rect x="480" y="60" width="140" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Chosen instance</text>

  <line x1="150" y1="82" x2="228" y2="82" stroke="#8b949e" marker-end="url(#arr67)"/>
  <line x1="390" y1="82" x2="478" y2="82" stroke="#8b949e" marker-end="url(#arr67)"/>

  <defs>
    <marker id="arr67" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The caller's only responsibility is calling a fixed address; the intermediary owns every discovery and selection decision.

## 5. Runnable example

Scenario: a shipping-service calling order-service that starts with client-side discovery embedded in the caller (as a contrast baseline), moves all of that logic into a separate load-balancer intermediary so the caller becomes trivially simple, and finally demonstrates the payoff of that simplicity — a second caller, written independently and with zero discovery code, immediately benefiting from the same intermediary with no duplicated logic anywhere.

### Level 1 — Basic

```java
// File: ClientSideBaseline.java -- the CALLER itself performs discovery and
// load balancing (contrast baseline, mirroring client-side discovery).
import java.util.*;

public class ClientSideBaseline {
    record ServiceInstance(String id, String host) {}
    static List<ServiceInstance> registryInstances = List.of(new ServiceInstance("order-a", "10.0.1.5"), new ServiceInstance("order-b", "10.0.1.6"));

    static class ShippingServiceCaller {
        int roundRobinIndex = 0;
        String callOrderService() {
            ServiceInstance chosen = registryInstances.get(roundRobinIndex++ % registryInstances.size()); // the CALLER chooses
            return "calling " + chosen.id() + " at " + chosen.host();
        }
    }

    public static void main(String[] args) {
        ShippingServiceCaller caller = new ShippingServiceCaller();
        System.out.println(caller.callOrderService());
        System.out.println("shipping-service's OWN code contains discovery/load-balancing logic -- this is what server-side discovery removes.");
    }
}
```

**How to run:** `javac ClientSideBaseline.java && java ClientSideBaseline` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ServerSideViaLoadBalancer.java -- ALL discovery/load-balancing logic
// moves into a SEPARATE intermediary; the CALLER becomes trivially simple.
import java.util.*;

public class ServerSideViaLoadBalancer {
    record ServiceInstance(String id, String host) {}

    // the INTERMEDIARY: does discovery AND load balancing, on behalf of ANY caller
    static class OrderServiceLoadBalancer {
        List<ServiceInstance> registryInstances = List.of(new ServiceInstance("order-a", "10.0.1.5"), new ServiceInstance("order-b", "10.0.1.6"));
        int roundRobinIndex = 0;
        String handleRequest(String path) {
            ServiceInstance chosen = registryInstances.get(roundRobinIndex++ % registryInstances.size());
            return "[load balancer] routed to " + chosen.id() + " at " + chosen.host() + path;
        }
    }

    // the CALLER: TRIVIALLY simple -- just calls a FIXED address, ZERO discovery awareness
    static class ShippingServiceCaller {
        OrderServiceLoadBalancer fixedAddress; // stands in for a fixed DNS name / VIP the caller always uses
        ShippingServiceCaller(OrderServiceLoadBalancer fixedAddress) { this.fixedAddress = fixedAddress; }
        String callOrderService(String path) {
            return fixedAddress.handleRequest(path); // an ORDINARY call, no discovery code AT ALL
        }
    }

    public static void main(String[] args) {
        OrderServiceLoadBalancer lb = new OrderServiceLoadBalancer();
        ShippingServiceCaller caller = new ShippingServiceCaller(lb);

        System.out.println(caller.callOrderService("/orders/42"));
        System.out.println(caller.callOrderService("/orders/43"));
        System.out.println("shipping-service's code is now TRIVIAL -- ALL discovery/load-balancing logic lives in ONE shared intermediary.");
    }
}
```

**How to run:** `javac ServerSideViaLoadBalancer.java && java ServerSideViaLoadBalancer` (JDK 17+).

Expected output:
```
[load balancer] routed to order-a at 10.0.1.5/orders/42
[load balancer] routed to order-b at 10.0.1.6/orders/43
shipping-service's code is now TRIVIAL -- ALL discovery/load-balancing logic lives in ONE shared intermediary.
```

### Level 3 — Advanced

```java
// File: MultipleCallersShareOneIntermediary.java -- a SECOND, INDEPENDENTLY
// written caller uses the SAME intermediary, with ZERO discovery code of its
// own -- the payoff of centralizing this logic in ONE place.
import java.util.*;

public class MultipleCallersShareOneIntermediary {
    record ServiceInstance(String id, String host) {}

    static class OrderServiceLoadBalancer { // the SAME intermediary from Level 2, UNCHANGED
        List<ServiceInstance> registryInstances = List.of(
            new ServiceInstance("order-a", "10.0.1.5"), new ServiceInstance("order-b", "10.0.1.6"), new ServiceInstance("order-c", "10.0.1.7"));
        int roundRobinIndex = 0;
        String handleRequest(String path) {
            ServiceInstance chosen = registryInstances.get(roundRobinIndex++ % registryInstances.size());
            return "routed to " + chosen.id();
        }
    }

    // CALLER 1: shipping-service -- written by one team
    static class ShippingServiceCaller {
        OrderServiceLoadBalancer lb;
        ShippingServiceCaller(OrderServiceLoadBalancer lb) { this.lb = lb; }
        void placeOrderRelatedCall() { System.out.println("[shipping-service] " + lb.handleRequest("/orders/42")); }
    }

    // CALLER 2: analytics-service -- written INDEPENDENTLY, by a DIFFERENT team,
    // with NO knowledge of shipping-service's code, yet uses the SAME intermediary identically simply
    static class AnalyticsServiceCaller {
        OrderServiceLoadBalancer lb;
        AnalyticsServiceCaller(OrderServiceLoadBalancer lb) { this.lb = lb; }
        void recordOrderMetrics() { System.out.println("[analytics-service] " + lb.handleRequest("/orders/42/metrics")); }
    }

    public static void main(String[] args) {
        OrderServiceLoadBalancer sharedLoadBalancer = new OrderServiceLoadBalancer(); // ONE intermediary, shared

        ShippingServiceCaller shipping = new ShippingServiceCaller(sharedLoadBalancer);
        AnalyticsServiceCaller analytics = new AnalyticsServiceCaller(sharedLoadBalancer);

        shipping.placeOrderRelatedCall();
        analytics.recordOrderMetrics();
        shipping.placeOrderRelatedCall();

        System.out.println("Neither ShippingServiceCaller NOR AnalyticsServiceCaller contains ANY discovery or load-balancing code -- BOTH share the SAME intermediary's logic.");
    }
}
```

**How to run:** `javac MultipleCallersShareOneIntermediary.java && java MultipleCallersShareOneIntermediary` (JDK 17+).

Expected output:
```
[shipping-service] routed to order-a
[analytics-service] routed to order-b
[shipping-service] routed to order-c
Neither ShippingServiceCaller NOR AnalyticsServiceCaller contains ANY discovery or load-balancing code -- BOTH share the SAME intermediary's logic.
```

## 6. Walkthrough

1. **Level 1** — `ShippingServiceCaller.callOrderService` directly indexes into `registryInstances` using its own `roundRobinIndex` field, meaning discovery-equivalent logic (choosing which instance to call) lives entirely inside this specific caller's own class.
2. **Level 2, extracting that logic into an intermediary** — `OrderServiceLoadBalancer.handleRequest` now contains the instance list and the round-robin selection logic that used to live in `ShippingServiceCaller`; `ShippingServiceCaller` itself becomes a thin wrapper whose `callOrderService` method does nothing but delegate to `fixedAddress.handleRequest(path)`.
3. **Level 2, the caller's genuine simplicity** — comparing `ShippingServiceCaller`'s class definition between Level 1 and Level 2 makes the reduction concrete: Level 2's version has no `registryInstances` field, no `roundRobinIndex`, and no selection logic of its own at all — just a single delegating method call.
4. **Level 2, the intermediary doing the real work** — the printed log lines show `"[load balancer] routed to ..."`, confirming that the actual routing decision (which instance, `order-a` or `order-b`) was made inside `OrderServiceLoadBalancer`, not inside `ShippingServiceCaller`.
5. **Level 3, a second, independent caller** — `AnalyticsServiceCaller` is a separate class, deliberately modeled as being written by a different team with no dependency on or knowledge of `ShippingServiceCaller`'s implementation, yet it too holds only a reference to the *same* `OrderServiceLoadBalancer` instance and delegates to it identically.
6. **Level 3, sharing state correctly across callers** — because both `ShippingServiceCaller` and `AnalyticsServiceCaller` are constructed with references to the *same* `sharedLoadBalancer` object, the `roundRobinIndex` field inside that one shared intermediary advances consistently across calls from *either* caller — the three interleaved calls in `main` (`shipping`, `analytics`, `shipping`) rotate through `order-a`, `order-b`, `order-c` in sequence, as a single shared counter, not three independent ones.
7. **Level 3, the demonstrated payoff** — neither `ShippingServiceCaller` nor `AnalyticsServiceCaller` contains a single line of discovery or load-balancing logic, and yet both correctly and consistently reach healthy `order-service` instances — this is the concrete benefit server-side discovery provides: any number of independently-written callers, potentially in entirely different languages in a real polyglot system, can rely on the identical, centrally-maintained intermediary without any of them needing to replicate its logic.

## 7. Gotchas & takeaways

> **Gotcha:** server-side discovery makes the intermediary (load balancer or gateway) itself a shared, critical dependency for every service-to-service call passing through it — unlike client-side discovery, where a bug or outage in one caller's load-balancing logic only affects that one caller, an intermediary outage or misbehavior in server-side discovery can simultaneously affect every service relying on it, making the intermediary's own reliability (mirroring [HA gateway design](0170-single-point-of-failure-concerns-ha-gateways.md)) a critical concern.

- Server-side service discovery has the calling service make an ordinary call to a fixed, stable intermediary address; the intermediary itself performs registry querying, instance selection, and request forwarding on the caller's behalf.
- This removes the need for every calling service to integrate its own registry-client and load-balancing library, concentrating that logic and its maintenance in one shared place instead.
- Multiple independently-written callers, potentially in different languages, can share the same intermediary without any of them duplicating discovery logic — a direct contrast with client-side discovery's per-caller integration requirement.
- Kubernetes' `Service` object and an API gateway's `lb://` route resolution are both concrete, widely-used examples of server-side discovery in practice.
- The intermediary becomes a critical, shared dependency for every call passing through it, requiring the same reliability engineering (high availability, monitoring) as any other piece of infrastructure central to the whole system's service-to-service communication.
