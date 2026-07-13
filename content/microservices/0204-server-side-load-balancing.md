---
card: microservices
gi: 204
slug: server-side-load-balancing
title: "Server-side load balancing"
---

## 1. What it is

Server-side load balancing has the calling service send its request to a single, stable address — a dedicated load balancer — which itself decides which backend instance actually handles the request; unlike [client-side load balancing](0203-client-side-load-balancing.md), the balancing decision, its algorithm, and any state it needs live entirely in that separate, shared intermediary, not in the calling service's own process.

## 2. Why & when

Requiring every calling service to embed its own load-balancing algorithm and instance-tracking state, as client-side balancing does, is unnecessary infrastructure duplication when a shared intermediary can make that decision once, on behalf of every caller. Server-side balancing centralizes this logic in one place — a network appliance, a software load balancer, or a [gateway](0157-api-gateway-pattern.md) — meaning callers can be as simple as making an ordinary call to a fixed address, at the cost of that extra network hop through the balancer and the balancer itself becoming a piece of shared, critical infrastructure.

Use server-side balancing when calling services should remain simple, when a polyglot environment makes maintaining consistent client-side balancing logic across languages impractical, or when a platform (Kubernetes' `Service`, a cloud provider's managed load balancer) already provides this centrally as a matter of course. This mirrors the broader trade-off between [client-side](0185-client-side-service-discovery.md) and [server-side](0186-server-side-service-discovery.md) discovery, applied specifically to the load-distribution decision itself.

## 3. Core concept

The load balancer, as a distinct running component, holds both the current instance list and the balancing algorithm's state; every caller sends requests to the balancer's own fixed address, and the balancer, entirely on its own, decides which backend instance handles each individual request and forwards it there.

```java
// the CALLER: an ORDINARY call to a FIXED address -- no algorithm, no instance list, nothing
httpClient.call("order-service-lb.internal", 80, "/orders/42");

// the LOAD BALANCER, a SEPARATE running component: holds the algorithm AND the state
class LoadBalancerService {
    int roundRobinIndex = 0;
    void handleIncomingRequest(Request request) {
        ServiceInstance chosen = instances.get(roundRobinIndex++ % instances.size()); // the DECISION lives HERE, not in the caller
        forwardTo(chosen, request);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The calling service makes an ordinary call to a fixed load balancer address; the load balancer, a separate running component, holds the instance list and balancing algorithm and forwards the request to whichever backend instance it selects" >
  <rect x="20" y="60" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Calling service</text>

  <rect x="230" y="55" width="180" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="78" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Load Balancer</text>
  <text x="320" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">holds instances + algorithm</text>

  <rect x="480" y="60" width="140" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Chosen instance</text>

  <line x1="150" y1="82" x2="228" y2="82" stroke="#8b949e" marker-end="url(#arr85)"/>
  <line x1="410" y1="82" x2="478" y2="82" stroke="#8b949e" marker-end="url(#arr85)"/>

  <defs>
    <marker id="arr85" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The balancing decision lives entirely in the intermediary component, not in the caller.

## 5. Runnable example

Scenario: shipping-service calling order-service that starts with client-side balancing logic embedded in the caller (contrast baseline), extracts all of that logic into a separate, shared load balancer so the caller becomes trivially simple, and finally demonstrates a second, independently-written caller immediately benefiting from the same load balancer with no duplicated balancing logic of its own — the concrete payoff of centralizing the decision.

### Level 1 — Basic

```java
// File: ClientSideBaseline.java -- the CALLER holds the algorithm and state
// itself (contrast baseline, mirroring client-side balancing).
import java.util.*;

public class ClientSideBaseline {
    record ServiceInstance(String id) {}
    static List<ServiceInstance> instances = List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b"));

    static class ShippingServiceCaller {
        int index = 0;
        String callOrderService() { return "calling " + instances.get(index++ % instances.size()).id(); } // ALGORITHM lives HERE
    }

    public static void main(String[] args) {
        System.out.println(new ShippingServiceCaller().callOrderService());
        System.out.println("shipping-service's OWN code contains the balancing algorithm -- server-side balancing REMOVES this.");
    }
}
```

**How to run:** `javac ClientSideBaseline.java && java ClientSideBaseline` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ServerSideCentralized.java -- ALL balancing logic moves into a SEPARATE
// LoadBalancerService; the CALLER becomes a trivial, fixed-address call.
import java.util.*;

public class ServerSideCentralized {
    record ServiceInstance(String id) {}

    // the SEPARATE intermediary -- holds instances AND the algorithm
    static class LoadBalancerService {
        List<ServiceInstance> instances = List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b"));
        int roundRobinIndex = 0;
        String handleRequest(String path) {
            ServiceInstance chosen = instances.get(roundRobinIndex++ % instances.size());
            return "[load balancer] routed to " + chosen.id() + path;
        }
    }

    // the CALLER: TRIVIALLY simple -- an ordinary call, NO algorithm, NO instance list
    static class ShippingServiceCaller {
        LoadBalancerService fixedAddress; // stands in for a fixed DNS name / VIP
        ShippingServiceCaller(LoadBalancerService fixedAddress) { this.fixedAddress = fixedAddress; }
        String callOrderService(String path) { return fixedAddress.handleRequest(path); }
    }

    public static void main(String[] args) {
        LoadBalancerService lb = new LoadBalancerService();
        ShippingServiceCaller caller = new ShippingServiceCaller(lb);

        System.out.println(caller.callOrderService("/orders/42"));
        System.out.println(caller.callOrderService("/orders/43"));
        System.out.println("shipping-service's code is TRIVIAL now -- ALL balancing logic lives in ONE shared LoadBalancerService.");
    }
}
```

**How to run:** `javac ServerSideCentralized.java && java ServerSideCentralized` (JDK 17+).

Expected output:
```
[load balancer] routed to order-a/orders/42
[load balancer] routed to order-b/orders/43
shipping-service's code is TRIVIAL now -- ALL balancing logic lives in ONE shared LoadBalancerService.
```

### Level 3 — Advanced

```java
// File: MultipleCallersShareTheBalancer.java -- a SECOND, INDEPENDENTLY
// written caller shares the SAME LoadBalancerService, with ZERO balancing
// code of its own -- the concrete payoff of centralizing the decision.
import java.util.*;

public class MultipleCallersShareTheBalancer {
    record ServiceInstance(String id) {}

    static class LoadBalancerService { // UNCHANGED from Level 2
        List<ServiceInstance> instances = List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b"), new ServiceInstance("order-c"));
        int roundRobinIndex = 0;
        String handleRequest(String path) {
            ServiceInstance chosen = instances.get(roundRobinIndex++ % instances.size());
            return "routed to " + chosen.id();
        }
    }

    static class ShippingServiceCaller {
        LoadBalancerService lb;
        ShippingServiceCaller(LoadBalancerService lb) { this.lb = lb; }
        void placeOrderRelatedCall() { System.out.println("[shipping-service] " + lb.handleRequest("/orders/42")); }
    }
    static class AnalyticsServiceCaller { // written by a DIFFERENT team, NO shared code with ShippingServiceCaller
        LoadBalancerService lb;
        AnalyticsServiceCaller(LoadBalancerService lb) { this.lb = lb; }
        void recordOrderMetrics() { System.out.println("[analytics-service] " + lb.handleRequest("/orders/42/metrics")); }
    }

    public static void main(String[] args) {
        LoadBalancerService sharedLb = new LoadBalancerService(); // ONE shared intermediary

        ShippingServiceCaller shipping = new ShippingServiceCaller(sharedLb);
        AnalyticsServiceCaller analytics = new AnalyticsServiceCaller(sharedLb);

        shipping.placeOrderRelatedCall();
        analytics.recordOrderMetrics();
        shipping.placeOrderRelatedCall();

        System.out.println("Neither caller class contains ANY balancing algorithm -- BOTH share the SAME centralized decision-making, correctly rotating together.");
    }
}
```

**How to run:** `javac MultipleCallersShareTheBalancer.java && java MultipleCallersShareTheBalancer` (JDK 17+).

Expected output:
```
[shipping-service] routed to order-a
[analytics-service] routed to order-b
[shipping-service] routed to order-c
Neither caller class contains ANY balancing algorithm -- BOTH share the SAME centralized decision-making, correctly rotating together.
```

## 6. Walkthrough

1. **Level 1** — `ShippingServiceCaller` maintains its own `index` field and computes `instances.get(index++ % instances.size())` directly, meaning the balancing algorithm is inseparable from this specific caller's own implementation.
2. **Level 2, extracting the logic into an intermediary** — `LoadBalancerService.handleRequest` now holds both `instances` and `roundRobinIndex`, performing the identical round-robin computation, but as a method on a *separate* class representing a distinct, shared component.
3. **Level 2, the caller's genuine simplicity** — `ShippingServiceCaller.callOrderService` does nothing but delegate to `fixedAddress.handleRequest(path)`; comparing this class's definition to Level 1's version shows the entire algorithm and state have been removed.
4. **Level 3, a second, independently-written caller** — `AnalyticsServiceCaller` is a separate class with no dependency on `ShippingServiceCaller`, modeling code written by a different team; it too holds only a reference to the shared `LoadBalancerService` and delegates identically.
5. **Level 3, shared state producing correct, coordinated rotation** — because both `shipping` and `analytics` are constructed with references to the *same* `sharedLb` object, `roundRobinIndex` advances as one consistent, shared counter across calls from either caller — the three interleaved calls (`shipping`, `analytics`, `shipping`) correctly rotate through `order-a`, `order-b`, `order-c` as a single sequence, not two independent ones.
6. **Level 3, the observable outcome confirming centralization** — the printed log traces each call's origin (`[shipping-service]` or `[analytics-service]`) alongside which instance the shared balancer selected, and the rotation pattern is continuous across both callers, directly demonstrating that the decision genuinely lives in one shared place rather than being duplicated (and potentially inconsistent) per caller.
7. **Level 3, the structural contrast with client-side balancing** — in [client-side load balancing](0203-client-side-load-balancing.md)'s equivalent scenario, two independent callers would each maintain their *own* separate round-robin counter, with no coordination between them; here, because the algorithm and its state live in one shared `LoadBalancerService`, the rotation is naturally coordinated across every caller using it, which is the concrete payoff of moving the decision server-side.

## 7. Gotchas & takeaways

> **Gotcha:** server-side balancing's shared state, while enabling coordinated rotation across multiple callers, also makes the load balancer itself a genuinely stateful, critical piece of shared infrastructure — unlike client-side balancing, where each caller's independent state means a bug or crash in one caller's balancing logic only affects that caller, a bug or outage in the shared load balancer can simultaneously affect every service relying on it, making its own [reliability and high availability](0170-single-point-of-failure-concerns-ha-gateways.md) a critical, non-optional concern.

- Server-side load balancing has the calling service make an ordinary call to a fixed intermediary address, with the balancing algorithm and its state living entirely in that separate, shared component rather than in the caller.
- This lets calling services remain simple and free of balancing-specific logic, at the cost of an extra network hop and the intermediary becoming shared, critical infrastructure.
- Multiple independently-written callers sharing the same server-side load balancer get naturally coordinated distribution, since the balancing state (like a round-robin counter) is centralized rather than duplicated per caller.
- This mirrors the broader trade-off between client-side and server-side service discovery, applied specifically to the traffic-distribution decision.
- The load balancer's shared, stateful nature makes its own reliability a critical concern — an outage or bug there can affect every service relying on it simultaneously, unlike the more isolated blast radius of a bug in one caller's own client-side balancing logic.
