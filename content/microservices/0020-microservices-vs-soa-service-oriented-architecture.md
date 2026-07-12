---
card: microservices
gi: 20
slug: microservices-vs-soa-service-oriented-architecture
title: "Microservices vs SOA (Service-Oriented Architecture)"
---

## 1. What it is

**Service-Oriented Architecture (SOA)** is an older architectural style, popular in the 2000s enterprise world, that also splits functionality into services — but typically routes communication through a central, "smart" **Enterprise Service Bus (ESB)** that handles routing, message transformation, and sometimes business orchestration, and often shares one large, centrally-governed canonical data model across all services. **Microservices** emerged partly as a reaction to SOA's tendency toward exactly that kind of central coupling: smart endpoints and dumb pipes instead of a smart bus, decentralized data instead of one canonical model, and decentralized governance instead of a single enterprise architecture team dictating standards for everyone.

Both styles genuinely split a system into services; the real difference is where the coordination logic and shared state live.

## 2. Why & when

SOA's centralized approach made sense for its era's problem: connecting large, often third-party or legacy enterprise systems that couldn't be redesigned, where a central integration layer translating between incompatible formats was often the only practical option. Its downside, in practice, was that the ESB itself frequently became a bottleneck — a shared piece of infrastructure every team's integration had to go through, owned by a specialized team, accumulating business logic no one fully understood, and becoming a single point of failure and a single point of slow, coordinated change.

Reach for microservices' decentralized approach when you're building services you actually control end to end, and can afford to give each team real autonomy over their own contract and data. SOA-style centralization still has a place when integrating systems you don't control and genuinely can't change — sometimes an ESB-like translation layer is the least-bad option available, not an architectural mistake.

## 3. Core concept

The structural difference, concretely:

- **SOA:** Service A and Service B don't call each other directly — they both go through a central ESB, which knows how to route, transform, and sometimes orchestrate business logic between them. Data models are frequently shared/canonical across the enterprise.
- **Microservices:** Service A calls Service B directly (or through a lightweight, "dumb" transport with no business logic of its own). Each service owns its own data and makes its own governance choices, coordinated only by agreed contracts.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SOA routes every service-to-service call through a central ESB with routing and transformation logic; microservices call each other directly over a lightweight transport">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">SOA</text>
  <rect x="30" y="70" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service A</text>
  <rect x="150" y="55" width="120" height="65" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="210" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ESB (routing +</text>
  <text x="210" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">transformation)</text>
  <rect x="300" y="70" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="345" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service B</text>

  <text x="530" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Microservices</text>
  <rect x="440" y="70" width="90" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service A</text>
  <rect x="540" y="70" width="90" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service B</text>
  <line x1="530" y1="90" x2="540" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a20)"/>
  <defs><marker id="a20" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

SOA centralizes routing and transformation in an ESB; microservices connect services directly through a lightweight, logic-free transport.

## 5. Runnable example

Scenario: Service A needing data from Service B in a slightly incompatible format, first routed and transformed through a central ESB, then connected directly with the transformation logic moved to the edges.

### Level 1 — Basic

```java
// File: SoaStyle.java -- a central ESB routes AND transforms between two services
import java.util.*;

public class SoaStyle {
    static class ServiceA { Map<String, String> getOrder() { return Map.of("orderId", "1001", "total", "9.99"); } }
    static class ServiceB {
        void receiveOrder(Map<String, String> order) {
            System.out.println("Service B received order #" + order.get("order_id") + " for $" + order.get("amount"));
        }
    }

    // the ESB knows the shape BOTH services expect, and transforms between them centrally
    static class Esb {
        void route(ServiceA a, ServiceB b) {
            Map<String, String> raw = a.getOrder();
            Map<String, String> transformed = Map.of(
                "order_id", raw.get("orderId"), // ESB renames the field
                "amount", raw.get("total")       // ESB renames this field too
            );
            b.receiveOrder(transformed);
        }
    }

    public static void main(String[] args) {
        new Esb().route(new ServiceA(), new ServiceB());
    }
}
```

**How to run:** `javac SoaStyle.java && java SoaStyle` (JDK 17+).

Expected output:
```
Service B received order #1001 for $9.99
```

`Esb.route` knows both `ServiceA`'s output shape and `ServiceB`'s expected input shape, and translates between them centrally. Neither service knows about the other directly — every interaction, and every future change to how they communicate, has to go through this one shared class.

### Level 2 — Intermediate

```java
// File: MicroservicesStyle.java -- Service A calls Service B DIRECTLY;
// the transformation logic moves to the EDGE that needs it.
import java.util.*;

public class MicroservicesStyle {
    static class ServiceA { Map<String, String> getOrder() { return Map.of("orderId", "1001", "total", "9.99"); } }

    static class ServiceB {
        // ServiceB's OWN contract, published and stable -- callers adapt to IT, not a central authority
        void receiveOrder(String orderId, String amount) {
            System.out.println("Service B received order #" + orderId + " for $" + amount);
        }
    }

    public static void main(String[] args) {
        ServiceA a = new ServiceA();
        ServiceB b = new ServiceB();

        Map<String, String> order = a.getOrder();
        b.receiveOrder(order.get("orderId"), order.get("total")); // A adapts to B's contract itself -- no central mediator
    }
}
```

**How to run:** `javac MicroservicesStyle.java && java MicroservicesStyle` (JDK 17+).

Expected output:
```
Service B received order #1001 for $9.99
```

There is no central class mediating between `ServiceA` and `ServiceB` — the caller (standing in for `ServiceA`'s consumer-side code) reads `ServiceA`'s output and adapts it directly to `ServiceB`'s published `receiveOrder(orderId, amount)` contract. Adding a third service that also needs to call `ServiceB` doesn't require touching any shared mediator at all.

### Level 3 — Advanced

```java
// File: ScalingBothStyles.java -- add a THIRD consuming service in both
// styles, showing where the coordination cost actually lands.
import java.util.*;

public class ScalingBothStyles {
    static class ServiceA { Map<String, String> getOrder() { return Map.of("orderId", "1001", "total", "9.99"); } }
    static class ServiceB {
        void receiveOrder(String orderId, String amount) { System.out.println("ServiceB: order #" + orderId + " for $" + amount); }
    }
    static class ServiceC { // NEW consumer, also wants Service A's order data
        void archiveOrder(String orderId) { System.out.println("ServiceC: archived order #" + orderId); }
    }

    // SOA-style: adding ServiceC means the ESB's routing logic grows
    static class Esb {
        void routeToB(ServiceA a, ServiceB b) {
            Map<String, String> raw = a.getOrder();
            b.receiveOrder(raw.get("orderId"), raw.get("total"));
        }
        void routeToC(ServiceA a, ServiceC c) { // the ESB had to learn a SECOND route
            Map<String, String> raw = a.getOrder();
            c.archiveOrder(raw.get("orderId"));
        }
    }

    public static void main(String[] args) {
        System.out.println("-- SOA style: central ESB grows with every new consumer --");
        Esb esb = new Esb();
        esb.routeToB(new ServiceA(), new ServiceB());
        esb.routeToC(new ServiceA(), new ServiceC()); // ESB code had to be edited to add this route

        System.out.println("-- Microservices style: each consumer adapts itself, mediator never changes --");
        ServiceA a = new ServiceA();
        Map<String, String> order = a.getOrder();
        new ServiceB().receiveOrder(order.get("orderId"), order.get("total"));
        new ServiceC().archiveOrder(order.get("orderId")); // NEW consumer, added with ZERO shared code touched
    }
}
```

**How to run:** `javac ScalingBothStyles.java && java ScalingBothStyles` (JDK 17+).

Expected output:
```
-- SOA style: central ESB grows with every new consumer --
ServiceB: order #1001 for $9.99
ServiceC: archived order #1001
-- Microservices style: each consumer adapts itself, mediator never changes --
ServiceB: order #1001 for $9.99
ServiceC: archived order #1001
```

The production-flavored contrast: both styles successfully deliver the order to `ServiceB` and `ServiceC`. But in the SOA-style block, adding `ServiceC` required a brand-new `routeToC` method on the shared `Esb` class — every new consumer grows the central mediator. In the microservices-style block, `ServiceC` was simply added as new, independent code — nothing shared had to change to accommodate it.

## 6. Walkthrough

1. In the SOA-style block, `esb.routeToB(new ServiceA(), new ServiceB())` runs first: it fetches `ServiceA`'s raw order data, transforms it into `ServiceB`'s expected argument order, and calls `receiveOrder`.
2. `esb.routeToC(new ServiceA(), new ServiceC())` runs next, calling a *second* method on the *same* `Esb` class — this method had to be written and added to `Esb` specifically to support `ServiceC`, meaning the central mediator's code grew to accommodate a new consumer.
3. In the microservices-style block, `Map<String, String> order = a.getOrder()` fetches the data once, directly, with no mediator involved.
4. `new ServiceB().receiveOrder(order.get("orderId"), order.get("total"))` adapts the raw map to `ServiceB`'s contract inline, at the point of use.
5. `new ServiceC().archiveOrder(order.get("orderId"))` does the same for `ServiceC`'s contract — and critically, nothing about `ServiceA`, `ServiceB`, or any shared class needed to change to add this new consumer; it's purely additive, independent code.

```
SOA:            Esb.routeToB(...)   Esb.routeToC(...)     <- BOTH live on the SAME shared class
                        |                   |
                 adding a consumer = editing the shared Esb

Microservices:  ServiceB.receiveOrder(...)   ServiceC.archiveOrder(...)   <- independent call sites
                        |                            |
                 adding a consumer = new, isolated code, nothing shared touched
```

## 7. Gotchas & takeaways

> **Gotcha:** "we don't have a literal ESB product installed" doesn't automatically mean a system has avoided SOA's central-coupling problem — a shared internal library that every service must import to communicate with any other service, or a shared "integration team" that every cross-service change must go through, can recreate the exact same bottleneck under a different name.

- SOA and microservices both split systems into services; the real difference is where routing, transformation, and coordination logic lives — centralized in an ESB (SOA) versus distributed to the services themselves (microservices).
- SOA's centralization suits integrating systems you don't control and can't redesign; microservices' decentralization suits systems you build and own end to end, where team autonomy is achievable and valuable.
- The concrete test: does adding a new consumer of an existing service require editing a shared, central piece of code, or can it be added as new, isolated code?
- Microservices emerged largely as a direct reaction against SOA's tendency for the ESB to become an organizational and technical bottleneck — the same failure mode can reappear in a "microservices" system that recreates a central mediator under a different name.
