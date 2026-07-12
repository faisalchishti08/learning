---
card: microservices
gi: 29
slug: distributed-monolith-anti-pattern
title: Distributed monolith anti-pattern
---

## 1. What it is

A **distributed monolith** is a system that has been split into multiple separately deployed services, but that still must be built, tested, and released together as a coordinated unit — inheriting every downside of a monolith's tight coupling (synchronized releases, shared failure modes) while adding every downside of a distributed system (network latency, partial failures) on top. It looks like microservices on an architecture diagram — many boxes, many arrows — but behaves like a monolith the moment you try to change or deploy just one piece of it.

## 2. Why & when

This anti-pattern typically emerges gradually, not by design: a team splits a monolith into services along convenient lines (often technical layers rather than business capabilities) without also decentralizing data or truly decoupling contracts. The services end up sharing a database, or one service's internal data shape leaks into another's expectations, or a "shared library" of business logic gets imported by every service and must be versioned in lockstep. None of these individually look catastrophic, but together they recreate the monolith's coordination requirement — now paid for with the overhead of network calls, multiple deploy pipelines, and multiple processes to operate.

Recognize this anti-pattern by testing [independent deployability](0013-independent-deployability.md) directly and honestly: can any one service actually be redeployed alone, right now, without any other service also needing to change? If the honest answer across most of your services is "no," you have a distributed monolith, and the fix is either to genuinely decouple the services (decentralize their data, tighten and stabilize their contracts) or to merge them back into a real monolith and stop paying the network-overhead cost for coupling you still have.

## 3. Core concept

The concrete symptom, testable in code or in process: does deploying Service A ever require deploying Service B in the same release window, for reasons other than a deliberate, temporary migration step?

- **Genuine microservices:** Service A and Service B each have their own data, their own stable contract; each can deploy on its own schedule indefinitely.
- **Distributed monolith:** Service A and Service B share a database schema, or Service A's code directly assumes Service B's internal response shape beyond its published contract — a change to one routinely forces a synchronized change to the other.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Genuine microservices deploy independently on separate schedules; a distributed monolith looks like separate services but must still be deployed together in lockstep">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Genuine microservices</text>
  <rect x="30" y="35" width="110" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service A</text>
  <rect x="160" y="35" width="110" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="215" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service B</text>
  <text x="150" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">deploy independently, any time</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Distributed monolith</text>
  <rect x="390" y="35" width="110" height="45" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="445" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service A</text>
  <rect x="520" y="35" width="110" height="45" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="575" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service B</text>
  <line x1="500" y1="57" x2="520" y2="57" stroke="#f0883e" stroke-width="2"/>
  <text x="500" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">must release together (shared schema)</text>
</svg>

Both look like two boxes on a diagram; only one of them can actually be deployed independently.

## 5. Runnable example

Scenario: two services sharing a data structure, first coupled so tightly that changing one breaks the other's deploy, then genuinely decoupled by giving each its own contract.

### Level 1 — Basic

```java
// File: DistributedMonolithSymptom.java -- Service A directly depends on
// Service B's INTERNAL response shape, beyond any published contract.
import java.util.*;

public class DistributedMonolithSymptom {
    // Service B's internal representation -- NOT a published, stable contract
    static Map<String, Object> serviceBInternalOrder() {
        Map<String, Object> order = new LinkedHashMap<>();
        order.put("id", 1001);
        order.put("total", 9.99);
        return order;
    }

    // Service A reaches DIRECTLY into that internal shape
    static String serviceAConsumesOrder() {
        Map<String, Object> order = serviceBInternalOrder();
        return "Order #" + order.get("id") + ": $" + order.get("total");
    }

    public static void main(String[] args) {
        System.out.println(serviceAConsumesOrder());
    }
}
```

**How to run:** `javac DistributedMonolithSymptom.java && java DistributedMonolithSymptom` (JDK 17+).

Expected output:
```
Order #1001: $9.99
```

This works today, but `serviceAConsumesOrder` depends on `"id"` and `"total"` being exactly those key names in exactly that shape — an internal detail of Service B, not a published API. Any refactor of Service B's internal representation (even one that doesn't change its *intended* public behavior) risks silently breaking Service A.

### Level 2 — Intermediate

```java
// File: RefactorBreaksConsumer.java -- Service B refactors its INTERNAL
// representation; because Service A depended on internals, it now BREAKS.
import java.util.*;

public class RefactorBreaksConsumer {
    // Service B's team renames "id" to "orderId" -- seems like a safe INTERNAL cleanup to them
    static Map<String, Object> serviceBInternalOrderV2() {
        Map<String, Object> order = new LinkedHashMap<>();
        order.put("orderId", 1001); // renamed
        order.put("total", 9.99);
        return order;
    }

    // Service A's code, UNCHANGED, still expects the OLD key name
    static String serviceAConsumesOrder(Map<String, Object> order) {
        return "Order #" + order.get("id") + ": $" + order.get("total"); // "id" no longer exists!
    }

    public static void main(String[] args) {
        System.out.println(serviceAConsumesOrder(serviceBInternalOrderV2()));
    }
}
```

**How to run:** `javac RefactorBreaksConsumer.java && java RefactorBreaksConsumer` (JDK 17+).

Expected output:
```
Order #null: $9.99
```

Service B's team considered `id` -> `orderId` a harmless internal rename. Service A silently breaks — `order.get("id")` now returns `null` since the key no longer exists — with no compiler error, no obvious failure, just quietly wrong output. This is the distributed monolith symptom in action: Service B cannot deploy this "internal" change without also coordinating a change in Service A.

### Level 3 — Advanced

```java
// File: DecoupledWithPublishedContract.java -- Service B now exposes a
// STABLE, published contract; its internals can change freely underneath it.
import java.util.*;

public class DecoupledWithPublishedContract {
    // Service B's PUBLISHED, STABLE contract -- a dedicated type, not a raw internal map
    record OrderContract(int orderId, double total) { }

    // Service B's internals -- free to be renamed, restructured, whatever the team needs
    static Map<String, Object> serviceBInternalRepresentation() {
        Map<String, Object> internal = new LinkedHashMap<>();
        internal.put("orderId", 1001); // internal name, can be anything
        internal.put("total", 9.99);
        return internal;
    }

    // Service B explicitly TRANSLATES internals into the published contract at the boundary
    static OrderContract serviceBPublishOrder() {
        Map<String, Object> internal = serviceBInternalRepresentation();
        return new OrderContract((int) internal.get("orderId"), (double) internal.get("total"));
    }

    // Service A depends ONLY on the published contract -- never on Service B's internals
    static String serviceAConsumesOrder(OrderContract order) {
        return "Order #" + order.orderId() + ": $" + order.total();
    }

    public static void main(String[] args) {
        System.out.println(serviceAConsumesOrder(serviceBPublishOrder()));
        // Service B can now rename its internal "orderId" to ANYTHING, and Service A is UNAFFECTED,
        // because serviceBPublishOrder's translation is the only place that internal name is used.
    }
}
```

**How to run:** `javac DecoupledWithPublishedContract.java && java DecoupledWithPublishedContract` (JDK 17+).

Expected output:
```
Order #1001: $9.99
```

The production-flavored fix: `OrderContract` is a stable, published type Service A depends on. `serviceBPublishOrder` is the one, explicit translation point between Service B's internals (free to change) and the published contract (kept stable). Service B's internal representation could be renamed, restructured, or replaced entirely, and as long as `serviceBPublishOrder` still produces a correct `OrderContract`, Service A never needs to change or even redeploy.

## 6. Walkthrough

1. `serviceBInternalRepresentation()` builds a `Map` with whatever internal key names Service B's team currently prefers — `"orderId"` in this version, but this could be renamed freely without external consequence.
2. `serviceBPublishOrder()` reads that internal map and explicitly constructs an `OrderContract(orderId, total)` — this is the one, deliberate translation step from "whatever Service B feels like internally" to "the stable shape the outside world depends on."
3. `serviceAConsumesOrder(serviceBPublishOrder())` receives an `OrderContract` object, not a raw map — it calls `order.orderId()` and `order.total()`, strongly-typed accessor methods defined once, on the published contract type itself.
4. If Service B's team later renames the internal map key from `"orderId"` to, say, `"order_identifier"`, only `serviceBPublishOrder`'s single line (`(int) internal.get("orderId")`) needs to change to read the new key name — `OrderContract`'s shape, and every line of `serviceAConsumesOrder`, remains untouched.
5. This is the concrete fix for the distributed monolith symptom shown in Level 2: by inserting one explicit translation point between "internal representation" and "published contract," a service's internal refactors stop being able to silently break its consumers.

```
Distributed monolith (Level 2):  ServiceB internal map --------------------> ServiceA (depends DIRECTLY on internal keys)
                                        rename "id" -> BREAKS ServiceA silently

Decoupled (Level 3):              ServiceB internal map -> OrderContract -> ServiceA (depends ONLY on OrderContract)
                                        internal renamed -> ONLY serviceBPublishOrder's one line changes
```

## 7. Gotchas & takeaways

> **Gotcha:** a distributed monolith is often invisible until the exact moment someone tries to change one service without the other — a demo, a code review, even most of a system's uptime can look perfectly fine while the coupling sits latent, undetected until a routine internal refactor silently breaks a consumer in production.

- A distributed monolith looks like microservices — many separately deployed services — but still requires coordinated releases across those services, inheriting a monolith's coupling cost plus a distributed system's network cost.
- The concrete test: can any one service redeploy alone, right now, without any other service also needing a change? If not, consistently, across most services, that's a distributed monolith.
- The fix is a stable, explicitly published contract (like `OrderContract` above) at each service boundary, with a deliberate translation step separating "internal representation" (free to change) from "external contract" (kept stable).
- Recognizing this anti-pattern early is far cheaper than living with it — the network overhead cost is being paid every day, while the coupling cost (and the corresponding coordination burden) is only discovered when someone actually tries to deploy independently and can't.
