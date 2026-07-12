---
card: microservices
gi: 62
slug: strategic-vs-tactical-ddd
title: "Strategic vs tactical DDD"
---

## 1. What it is

Domain-Driven Design splits into two distinct levels of work. **Strategic DDD** operates at the scale of the whole system: it identifies [bounded contexts](0049-bounded-context.md), draws the [context map](0050-context-map-context-mapping.md) between them, and decides which context is core, supporting, or generic — the decisions that determine where your microservice boundaries actually go. **Tactical DDD** operates inside a single bounded context, once its boundary is already settled: it is the toolbox of building blocks — [entities and value objects](0053-entities-and-value-objects.md), [aggregates](0052-aggregates-and-aggregate-roots.md), [domain events](0054-domain-events.md), [domain services](0055-domain-services.md), and [repositories](0056-repositories-ddd-sense.md) — used to model that one context's internals well.

## 2. Why & when

Teams new to DDD often reach straight for the tactical patterns — aggregates, value objects, repositories — because they read like concrete code recipes. But applying tactical patterns without first doing the strategic work is like carefully bricklaying a wall before deciding where the building's rooms go: the individual bricks may be well laid, yet the wall might sit in entirely the wrong place. In a microservices architecture, strategic DDD is what decides service boundaries; tactical DDD is what makes the code inside each resulting service coherent. Skipping strategic analysis is exactly how teams end up with a service boundary that cuts across a single business concept, forcing chatty cross-service calls for what should have been one atomic operation.

Use strategic DDD first, whenever you are deciding how many services to have and where their boundaries sit — new system design, breaking apart a monolith, or reorganizing existing services. Use tactical DDD second, once a boundary is fixed, to design the internal model of that one service well.

## 3. Core concept

Strategic DDD answers "how many contexts, and where are their edges?" Tactical DDD answers "given this one context, how do I model it?" The two are sequential and complementary, not competing.

```
STRATEGIC DDD (system-wide)                  TACTICAL DDD (inside one context)
------------------------------               ------------------------------------
Identify bounded contexts                     Entities & value objects
Classify subdomains (core/support/generic)    Aggregates & aggregate roots
Draw the context map                          Domain events
Choose integration patterns (ACL, OHS, etc.)  Domain services
        |                                     Repositories
        v
   "Where do boundaries go?"                    "How do I model inside one boundary?"
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Strategic DDD determines the outer boundaries between bounded contexts; tactical DDD then models the internals inside each resulting context">
  <rect x="10" y="10" width="300" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="30" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Strategic DDD</text>
  <text x="160" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">bounded contexts, context map,</text>
  <text x="160" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">subdomain classification</text>
  <text x="160" y="82" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">decides WHERE service boundaries go</text>

  <rect x="330" y="10" width="300" height="90" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="30" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Tactical DDD</text>
  <text x="480" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">entities, value objects, aggregates,</text>
  <text x="480" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">domain events, repositories</text>
  <text x="480" y="82" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">decides HOW to model inside a boundary</text>

  <line x1="310" y1="55" x2="330" y2="55" stroke="#6db33f" stroke-width="2" marker-end="url(#arrow62)"/>
  <defs>
    <marker id="arrow62" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/>
    </marker>
  </defs>

  <rect x="30" y="140" width="580" height="60" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="165" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order Context (strategic boundary)</text>
  <text x="320" y="183" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Order aggregate, OrderLine value object, OrderPlaced event -- tactical patterns applied INSIDE this one boundary</text>
</svg>

Strategic DDD draws the boundary first; tactical DDD models what lives inside it.

## 5. Runnable example

Scenario: a single `Order` concept, first modeled with no strategic thinking (one tangled class doing everything), then split by identifying its bounded context boundary (strategic), then modeled properly inside that boundary using tactical patterns.

### Level 1 — Basic

```java
// File: NoStrategy.java -- one class mixes ordering, shipping, and billing
// concerns because no strategic boundary was ever drawn.
import java.util.*;

public class NoStrategy {
    static class Order {
        String id;
        List<String> items = new ArrayList<>();
        String shippingCarrier;   // shipping concern leaking in
        String invoiceNumber;     // billing concern leaking in
        double taxRate;           // billing concern leaking in

        Order(String id) { this.id = id; }
    }

    public static void main(String[] args) {
        Order o = new Order("ORD-1");
        o.items.add("widget");
        o.shippingCarrier = "UPS";
        o.invoiceNumber = "INV-1";
        o.taxRate = 0.08;
        System.out.println("Order " + o.id + " tangles ordering, shipping, and billing in one place.");
    }
}
```

**How to run:** `javac NoStrategy.java && java NoStrategy` (JDK 17+).

Expected output:
```
Order ORD-1 tangles ordering, shipping, and billing in one place.
```

This is the state before any DDD is applied: one class accreting every concern that ever touches an order, because nobody ever asked "where does the Ordering context end and the Shipping or Billing context begin?"

### Level 2 — Intermediate

```java
// File: StrategicBoundary.java -- strategic DDD step: identify that
// Ordering, Shipping, and Billing are SEPARATE bounded contexts.
// Each context now owns only the data and behavior that is truly its own.
import java.util.*;

public class StrategicBoundary {
    // Ordering context -- owns items and order lifecycle only
    static class Order {
        String id;
        List<String> items = new ArrayList<>();
        Order(String id) { this.id = id; }
    }

    // Shipping context -- owns carrier assignment, referencing the order only by id
    static class Shipment {
        String orderId;
        String carrier;
        Shipment(String orderId, String carrier) { this.orderId = orderId; this.carrier = carrier; }
    }

    // Billing context -- owns invoicing, referencing the order only by id
    static class Invoice {
        String orderId;
        String invoiceNumber;
        double taxRate;
        Invoice(String orderId, String invoiceNumber, double taxRate) {
            this.orderId = orderId; this.invoiceNumber = invoiceNumber; this.taxRate = taxRate;
        }
    }

    public static void main(String[] args) {
        Order order = new Order("ORD-1");
        order.items.add("widget");
        Shipment shipment = new Shipment(order.id, "UPS");
        Invoice invoice = new Invoice(order.id, "INV-1", 0.08);
        System.out.println("Ordering owns: " + order.items);
        System.out.println("Shipping owns: " + shipment.carrier + " for order " + shipment.orderId);
        System.out.println("Billing owns: " + invoice.invoiceNumber + " at rate " + invoice.taxRate);
    }
}
```

**How to run:** `javac StrategicBoundary.java && java StrategicBoundary` (JDK 17+).

Expected output:
```
Ordering owns: [widget]
Shipping owns: UPS for order ORD-1
Billing owns: INV-1 at rate 0.08
```

This is strategic DDD in action: three bounded contexts, each referencing the order only by its id, never by sharing its object. No tactical modeling has happened yet inside any one context — this step only decided *where the walls go*.

### Level 3 — Advanced

```java
// File: TacticalInsideStrategic.java -- tactical DDD step: NOW that the
// Ordering context's boundary is fixed, model its internals properly --
// aggregate root, value object, and a domain event raised on state change.
import java.util.*;

public class TacticalInsideStrategic {
    // value object: immutable, compared by value, not identity
    record OrderLine(String sku, int quantity) {}

    // domain event: an immutable record of something that happened
    record OrderPlaced(String orderId, int lineCount) {}

    // aggregate root: the ONLY entry point into the Order aggregate;
    // guards its own invariants and is the sole holder of OrderLine objects
    static class Order {
        private final String id;
        private final List<OrderLine> lines = new ArrayList<>();
        private boolean placed = false;
        private final List<Object> raisedEvents = new ArrayList<>();

        Order(String id) { this.id = id; }

        void addLine(String sku, int quantity) {
            if (placed) throw new IllegalStateException("cannot modify a placed order");
            if (quantity <= 0) throw new IllegalArgumentException("quantity must be positive");
            lines.add(new OrderLine(sku, quantity));
        }

        void place() {
            if (lines.isEmpty()) throw new IllegalStateException("cannot place an empty order");
            placed = true;
            raisedEvents.add(new OrderPlaced(id, lines.size()));
        }

        List<Object> pullEvents() {
            List<Object> events = new ArrayList<>(raisedEvents);
            raisedEvents.clear();
            return events;
        }
    }

    public static void main(String[] args) {
        Order order = new Order("ORD-1");
        order.addLine("widget", 2);
        order.addLine("gadget", 1);
        order.place();

        for (Object event : order.pullEvents()) {
            System.out.println("Event raised: " + event);
        }

        try {
            order.addLine("late-item", 1);
        } catch (IllegalStateException e) {
            System.out.println("Guarded: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac TacticalInsideStrategic.java && java TacticalInsideStrategic` (JDK 17+).

Expected output:
```
Event raised: OrderPlaced[orderId=ORD-1, lineCount=2]
Guarded: cannot modify a placed order
```

This is tactical DDD applied *inside* the already-fixed Ordering boundary: `Order` is the aggregate root guarding its own invariants (no empty orders, no modifying a placed order), `OrderLine` is a value object, and `OrderPlaced` is a domain event raised by the aggregate itself — nothing about Shipping or Billing leaks in, because strategic DDD already drew that line in Level 2.

## 6. Walkthrough

Trace the full arc from Level 1 to Level 3 to see the two levels of DDD working in sequence.

1. **Level 1 starting point** — `NoStrategy.Order` is created and immediately accumulates shipping and billing fields directly on itself. There is no bounded context boundary at all; every concern that ever touches an order gets bolted onto the same class. `main` prints a single sentence confirming the tangle.
2. **Level 2 — strategic decision** — the same responsibilities are pulled apart into `Order`, `Shipment`, and `Invoice`, three separate classes standing in for three separate bounded contexts (Ordering, Shipping, Billing). Critically, `Shipment` and `Invoice` reference the order only by `orderId` — a plain string — never by holding a reference to the `Order` object itself. That single choice is the strategic decision: it draws a hard wall between contexts so that, for example, the Shipping context could later become its own microservice without dragging Ordering's internals along with it. `main` constructs all three objects and prints what each context owns, showing the separation is real and enforced by the code shape, not just an intention in a diagram.
3. **Level 3 — tactical modeling inside the fixed boundary** — with the Ordering context's edge already settled, `TacticalInsideStrategic.Order` is now modeled properly as an **aggregate root**: it is the only way to add an `OrderLine` (a **value object** — immutable, defined by its `sku` and `quantity`, not by identity), and it is the only object allowed to raise the `OrderPlaced` **domain event**. `main` calls `addLine` twice, then `place()`, which appends an `OrderPlaced` event to the internal `raisedEvents` list. `pullEvents()` drains and returns that list — this is the standard "aggregate collects events, something later publishes them" pattern used before those events would be handed to an event bus in a real service.
4. **Guard demonstration** — `main` then tries `addLine("late-item", 1)` on the now-placed order. The aggregate root's `placed` flag causes it to throw `IllegalStateException`, proving the aggregate is genuinely protecting its own invariant ("no changes after placement") rather than trusting external callers to behave.
5. **Output** — the program prints the event's string form (Java records auto-generate a readable `toString`) followed by the caught guard message, so the whole call sequence — build order, place it, event fires, later mutation attempt rejected — is visible end to end.

The lesson embedded in the progression: Level 2's strategic split (contexts referencing each other only by id) is what made Level 3's tactical richness *safe* to add. If Shipping still held a direct reference into `Order`'s internals, an aggregate root's invariant guarantees would mean nothing — an external class could reach in and mutate `lines` directly, bypassing every check `place()` and `addLine()` enforce.

## 7. Gotchas & takeaways

> **Gotcha:** teams frequently apply tactical patterns — aggregates, repositories, value objects — to a domain model whose boundaries were never strategically analyzed. The result is beautifully engineered code sitting inside the wrong boundary, which is far more expensive to fix later than a plain class in the right boundary.

- Do strategic DDD first: identify contexts, classify subdomains, draw the context map. That is what determines your microservice boundaries.
- Do tactical DDD second, and only inside a single, already-decided bounded context.
- A tactical aggregate root's invariant guarantees are only meaningful if the strategic boundary genuinely isolates that context — cross-context object references undermine the whole exercise.
- Not every context needs deep tactical modeling: a generic subdomain (see [subdomain classification](0051-subdomains-core-supporting-generic.md)) may just need a simple CRUD model, while your core subdomain deserves the full tactical toolbox.
- Revisit strategic boundaries occasionally — tactical modeling inside a context often surfaces evidence that a boundary was drawn in the wrong place, which is a strategic-level fix, not a tactical one.
