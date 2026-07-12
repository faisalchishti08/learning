---
card: microservices
gi: 40
slug: decompose-by-use-case-verb
title: Decompose by use case / verb
---

## 1. What it is

**Decomposing by use case (or "verb")** draws service boundaries around specific actions the system performs — `PlaceOrderService`, `CancelOrderService`, `ShipOrderService` — rather than around the data entity those actions operate on. This is the direct alternative to [decomposing by resource/noun](0041-decompose-by-resource-noun.md), where you'd instead have one `OrderService` owning all order-related operations. Verb-based decomposition asks "what does the system *do*?" first; noun-based decomposition asks "what does the system *have*?" first.

## 2. Why & when

Verb-based decomposition shines when different actions on the same conceptual entity have genuinely different behavior, different rates of change, different scaling needs, or different teams responsible for them. Placing an order and cancelling an order might involve wildly different business rules, different downstream side effects (payment authorization versus refund processing), and might be owned by entirely different teams in a large organization — bundling both into one `OrderService` can recreate the "god service" problem even though it's nominally organized around a single entity.

Reach for verb-based decomposition when a resource's different operations have diverged enough in complexity, ownership, or change frequency that keeping them together in one noun-based service creates unnecessary coupling between unrelated concerns. Avoid it as a default for every resource — many simple entities genuinely are best served by one cohesive CRUD-style service, where splitting create/read/update/delete into separate services would be needless over-fragmentation (see [avoiding chatty services](0046-avoiding-chatty-services-too-fine-grained.md)).

## 3. Core concept

The structural difference, made concrete:

- **Noun-based:** `OrderService` has methods `place()`, `cancel()`, `ship()`, `refund()` — one service, one team, one deploy for all order operations.
- **Verb-based:** `PlaceOrderService`, `CancelOrderService`, `ShipOrderService`, `RefundOrderService` — four separate services, each independently deployable, potentially owned by four different teams with genuinely different concerns.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Noun-based decomposition bundles all order operations into one OrderService; verb-based decomposition splits each operation into its own independently deployable service">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Noun-based</text>
  <rect x="40" y="35" width="220" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="58" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="150" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">place(), cancel(),</text>
  <text x="150" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ship(), refund()</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Verb-based</text>
  <g fill="#1c2430" stroke="#6db33f" stroke-width="1.2" font-family="sans-serif">
    <rect x="330" y="35" width="90" height="35" rx="5"/><text x="375" y="57" fill="#e6edf3" font-size="7.5" text-anchor="middle">PlaceOrderService</text>
    <rect x="430" y="35" width="90" height="35" rx="5"/><text x="475" y="57" fill="#e6edf3" font-size="7.5" text-anchor="middle">CancelOrderService</text>
    <rect x="330" y="80" width="90" height="35" rx="5"/><text x="375" y="102" fill="#e6edf3" font-size="7.5" text-anchor="middle">ShipOrderService</text>
    <rect x="430" y="80" width="90" height="35" rx="5"/><text x="475" y="102" fill="#e6edf3" font-size="7.5" text-anchor="middle">RefundOrderService</text>
  </g>
</svg>

The same four operations, bundled into one service or split into four independently deployable ones.

## 5. Runnable example

Scenario: order operations first bundled as one noun-based service, then split by verb to show independent deployability of just one operation, then demonstrating a genuine scaling difference between operations that justifies the split.

### Level 1 — Basic

```java
// File: NounBasedOrderService.java -- ONE service bundling ALL order operations
public class NounBasedOrderService {
    static class OrderService {
        String place(String item) { return "order placed: " + item; }
        String cancel(String orderId) { return "order cancelled: " + orderId; }
        String ship(String orderId) { return "order shipped: " + orderId; }
    }

    public static void main(String[] args) {
        OrderService orders = new OrderService();
        System.out.println(orders.place("widget"));
        System.out.println(orders.cancel("ord-1"));
        System.out.println(orders.ship("ord-1"));
    }
}
```

**How to run:** `javac NounBasedOrderService.java && java NounBasedOrderService` (JDK 17+).

Expected output:
```
order placed: widget
order cancelled: ord-1
order shipped: ord-1
```

All three operations live in one class. Deploying a fix to `ship`'s logic requires redeploying the whole `OrderService`, even if `place` and `cancel` are completely unaffected.

### Level 2 — Intermediate

```java
// File: VerbBasedServices.java -- SPLIT by verb: each operation is its
// own independently deployable service.
public class VerbBasedServices {
    static class PlaceOrderService { String place(String item) { return "order placed: " + item; } }
    static class CancelOrderService { String cancel(String orderId) { return "order cancelled: " + orderId; } }
    static class ShipOrderService { String ship(String orderId) { return "order shipped: " + orderId; } }

    public static void main(String[] args) {
        System.out.println(new PlaceOrderService().place("widget"));
        System.out.println(new CancelOrderService().cancel("ord-1"));
        System.out.println(new ShipOrderService().ship("ord-1"));
    }
}
```

**How to run:** `javac VerbBasedServices.java && java VerbBasedServices` (JDK 17+).

Expected output:
```
order placed: widget
order cancelled: ord-1
order shipped: ord-1
```

Same observable behavior, but now `ShipOrderService` can be redeployed, scaled, or even rewritten entirely without touching `PlaceOrderService` or `CancelOrderService` at all — each verb is now a fully independent unit.

### Level 3 — Advanced

```java
// File: JustifyingTheSplit.java -- show a CONCRETE reason verb-based
// splitting pays off: wildly different traffic volumes per operation.
import java.util.concurrent.atomic.AtomicInteger;

public class JustifyingTheSplit {
    static class PlaceOrderService {
        AtomicInteger instancesNeeded = new AtomicInteger(1);
        String place(String item, int requestsPerSecond) {
            instancesNeeded.set(Math.max(1, requestsPerSecond / 100)); // scales with HIGH checkout traffic
            return "order placed: " + item;
        }
    }

    static class CancelOrderService {
        AtomicInteger instancesNeeded = new AtomicInteger(1);
        String cancel(String orderId, int requestsPerSecond) {
            instancesNeeded.set(Math.max(1, requestsPerSecond / 100)); // cancellations are RARE by comparison
            return "order cancelled: " + orderId;
        }
    }

    public static void main(String[] args) {
        PlaceOrderService placeOrders = new PlaceOrderService();
        CancelOrderService cancelOrders = new CancelOrderService();

        placeOrders.place("widget", 5000);  // checkout traffic: HIGH
        cancelOrders.cancel("ord-1", 20);   // cancellation traffic: LOW

        System.out.println("PlaceOrderService needs " + placeOrders.instancesNeeded.get() + " instances (high checkout traffic)");
        System.out.println("CancelOrderService needs " + cancelOrders.instancesNeeded.get() + " instance(s) (low cancellation traffic)");
        System.out.println("If bundled into ONE OrderService, it would need " + placeOrders.instancesNeeded.get() + " instances for BOTH operations -- wasting capacity on the rare one");
    }
}
```

**How to run:** `javac JustifyingTheSplit.java && java JustifyingTheSplit` (JDK 17+).

Expected output:
```
PlaceOrderService needs 50 instances (high checkout traffic)
CancelOrderService needs 1 instance(s) (low cancellation traffic)
If bundled into ONE OrderService, it would need 50 instances for BOTH operations -- wasting capacity on the rare one
```

The production-flavored justification: `place` sees `5000` requests/second (checkout is the busiest path in most e-commerce systems) while `cancel` sees only `20`. Split by verb, each operation scales independently — `50` instances for placing orders, `1` for cancelling. Bundled into one `OrderService`, the whole service would need `50` instances just to handle `place`'s load, even though `cancel`'s actual traffic would be comfortably served by a single instance — a direct, measurable waste of capacity that verb-based splitting avoids.

## 6. Walkthrough

1. `placeOrders.place("widget", 5000)` runs `instancesNeeded.set(Math.max(1, 5000 / 100))`, computing `Math.max(1, 50) = 50` — `PlaceOrderService`'s scaling need is set based purely on its own traffic figure.
2. `cancelOrders.cancel("ord-1", 20)` runs the analogous computation on a completely separate object: `Math.max(1, 20 / 100) = Math.max(1, 0) = 1`.
3. Because `PlaceOrderService` and `CancelOrderService` are separate classes with separate `instancesNeeded` fields, these two computations never interact — each operation's scaling decision is made entirely independently, based on its own actual traffic.
4. The final print explicitly states the counterfactual: if both operations were methods on one bundled `OrderService`, that single service's instance count would have to satisfy the *busiest* operation's needs (`50` instances), even though `cancel`'s actual load would be comfortably handled by just `1` — the other `49` instances would sit there purely to serve `cancel` requests that never come close to needing that capacity.
5. This is [independent scalability](0014-independent-scalability.md) applied specifically at the verb level: splitting by use case lets each operation's infrastructure be sized to its own actual demand, rather than every operation inheriting the busiest one's requirements.

```
Bundled OrderService:        needs 50 instances total (sized for place(), wastes capacity on cancel())
Split PlaceOrderService:     needs 50 instances (sized correctly for its own high traffic)
Split CancelOrderService:    needs  1 instance  (sized correctly for its own low traffic)
```

## 7. Gotchas & takeaways

> **Gotcha:** splitting every verb into its own service by default reintroduces the [chatty services](0046-avoiding-chatty-services-too-fine-grained.md) and [over-granularity](0019-service-granularity-nano-micro-macro-mini-services.md) problems covered elsewhere in this section — verb-based decomposition earns its cost specifically when different operations on the same entity genuinely diverge in traffic, ownership, or complexity, not as a blanket rule applied to every CRUD operation on every resource.

- Verb-based decomposition draws service boundaries around actions (`PlaceOrderService`, `CancelOrderService`) rather than around the data entity those actions operate on.
- It's the direct alternative to [resource/noun-based decomposition](0041-decompose-by-resource-noun.md), and the right choice specifically when different operations on the same entity have genuinely diverged in traffic pattern, ownership, or business complexity.
- The concrete payoff is independent scalability and independent deployability per operation — a high-traffic operation can scale separately from a low-traffic one on the same conceptual entity, instead of both being forced to share the same instance count.
- Don't apply verb-based splitting to every resource by default — many entities' operations genuinely belong together in one cohesive service, and over-splitting adds real coordination and network-hop cost for no matching benefit.
