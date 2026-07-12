---
card: microservices
gi: 52
slug: aggregates-and-aggregate-roots
title: Aggregates and aggregate roots
---

## 1. What it is

An **aggregate** is a cluster of related objects — entities and value objects — that must be treated as a single, consistent unit whenever it's modified: changes across the whole cluster either all succeed together or none do, and the invariants that must always hold true (like "an order's total must equal the sum of its line items") are enforced across the entire cluster together. The **aggregate root** is the single object within that cluster that external code is allowed to reference and call methods on directly — everything else inside the aggregate is only reachable *through* the root, never referenced or modified independently from outside.

```java
class Order { // the aggregate root
    private List<OrderLineItem> lineItems = new ArrayList<>(); // internal to the aggregate, NOT exposed for direct external mutation
    void addLineItem(String item, double price) {
        lineItems.add(new OrderLineItem(item, price));
        recalculateTotal(); // the invariant "total = sum of line items" is enforced HERE, inside the aggregate
    }
}
```

## 2. Why & when

Without the aggregate boundary, external code could reach directly into an order's internal line items — adding one, removing one, changing a price — without going through any logic that keeps the order's `total` field consistent with those changes. Bugs like "the total doesn't match the line items" become common and hard to trace, since the inconsistency could have been introduced from any of dozens of call sites scattered across the codebase, each mutating internal state independently.

Design an aggregate whenever a group of objects has a genuine consistency requirement that must hold as a unit — model the smallest cluster of objects that must change together atomically as one aggregate, with exactly one root as the only entry point. Keep aggregates small: a large aggregate with many entities inside it tends to create unnecessary contention (two unrelated changes to the same aggregate can't happen concurrently without one waiting for the other) and makes the "what needs to change together" boundary harder to reason about.

## 3. Core concept

The rule, stated concretely: external code holds a reference only to the aggregate root, never to any entity inside the aggregate. Every mutation to anything inside the aggregate happens through a method call on the root, which is responsible for keeping the aggregate's invariants true after every change.

```
External code:  Order order = orderRepository.find(id);
                 order.addLineItem("widget", 9.99);   // the ONLY way in -- through the root
                 // order.lineItems.add(...)           <- NEVER allowed: bypasses the root's invariant enforcement
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="External code can only reference the Order aggregate root; OrderLineItem entities inside the aggregate are reachable only through the root's own methods">
  <rect x="220" y="30" width="200" height="120" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Order (aggregate root)</text>
  <rect x="245" y="70" width="150" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderLineItem #1</text>
  <rect x="245" y="105" width="150" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="125" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderLineItem #2</text>

  <rect x="30" y="70" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="100" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">external code</text>
  <line x1="170" y1="90" x2="220" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#a52)"/>
  <text x="195" y="78" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">only</text>
  <defs><marker id="a52" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

External code touches only the aggregate root; entities inside the boundary are reachable exclusively through it.

## 5. Runnable example

Scenario: an order with line items, first mutated unsafely from outside the aggregate boundary (breaking an invariant), then properly encapsulated behind the aggregate root, then extended to show the root enforcing a more complex invariant across a state transition.

### Level 1 — Basic

```java
// File: NoAggregateBoundary.java -- external code reaches DIRECTLY into
// internal state, bypassing any invariant enforcement.
import java.util.*;

public class NoAggregateBoundary {
    static class OrderLineItem { String item; double price; OrderLineItem(String item, double price) { this.item = item; this.price = price; } }

    static class Order {
        public List<OrderLineItem> lineItems = new ArrayList<>(); // PUBLIC -- exposed for direct external mutation
        public double total = 0; // NOT automatically kept in sync
    }

    public static void main(String[] args) {
        Order order = new Order();
        order.lineItems.add(new OrderLineItem("widget", 9.99)); // external code mutates internals DIRECTLY
        // order.total was NEVER updated -- nothing enforced the invariant "total = sum of line items"
        System.out.println("line items: " + order.lineItems.size() + ", total: " + order.total + " (WRONG -- should be 9.99)");
    }
}
```

**How to run:** `javac NoAggregateBoundary.java && java NoAggregateBoundary` (JDK 17+).

Expected output:
```
line items: 1, total: 0.0 (WRONG -- should be 9.99)
```

External code added a line item directly to the public list, but nothing recalculated `total` — the invariant "total must equal the sum of line items" silently broke, because there was no aggregate boundary forcing every mutation through logic that maintains it.

### Level 2 — Intermediate

```java
// File: AggregateRoot.java -- Order is the AGGREGATE ROOT; line items are
// only reachable and mutable THROUGH it.
import java.util.*;

public class AggregateRoot {
    static class OrderLineItem { String item; double price; OrderLineItem(String item, double price) { this.item = item; this.price = price; } }

    static class Order { // the AGGREGATE ROOT -- the ONLY external entry point
        private final List<OrderLineItem> lineItems = new ArrayList<>(); // PRIVATE now
        private double total = 0;

        void addLineItem(String item, double price) { // the ONLY way to add a line item
            lineItems.add(new OrderLineItem(item, price));
            recalculateTotal(); // the invariant is enforced HERE, every time, automatically
        }

        private void recalculateTotal() {
            total = lineItems.stream().mapToDouble(li -> li.price).sum();
        }

        double getTotal() { return total; }
        int getLineItemCount() { return lineItems.size(); }
    }

    public static void main(String[] args) {
        Order order = new Order();
        order.addLineItem("widget", 9.99); // the ONLY way in -- through the root
        System.out.println("line items: " + order.getLineItemCount() + ", total: " + order.getTotal());
    }
}
```

**How to run:** `javac AggregateRoot.java && java AggregateRoot` (JDK 17+).

Expected output:
```
line items: 1, total: 9.99
```

`lineItems` is now `private`, reachable only through `addLineItem`, which always calls `recalculateTotal` immediately afterward — the invariant "total matches the sum of line items" can no longer be broken by external code, because there's no path that bypasses the root's own logic.

### Level 3 — Advanced

```java
// File: EnforcingComplexInvariant.java -- the aggregate root enforces a
// MORE COMPLEX invariant across a state transition: a CONFIRMED order
// cannot have line items added or removed.
import java.util.*;

public class EnforcingComplexInvariant {
    static class OrderLineItem { String item; double price; OrderLineItem(String item, double price) { this.item = item; this.price = price; } }
    enum OrderStatus { OPEN, CONFIRMED }

    static class Order {
        private final List<OrderLineItem> lineItems = new ArrayList<>();
        private double total = 0;
        private OrderStatus status = OrderStatus.OPEN;

        void addLineItem(String item, double price) {
            if (status == OrderStatus.CONFIRMED) {
                throw new IllegalStateException("Cannot modify line items on a CONFIRMED order"); // invariant enforced BY THE ROOT
            }
            lineItems.add(new OrderLineItem(item, price));
            recalculateTotal();
        }

        void confirm() {
            if (lineItems.isEmpty()) throw new IllegalStateException("Cannot confirm an order with no line items"); // ANOTHER invariant
            status = OrderStatus.CONFIRMED;
        }

        private void recalculateTotal() { total = lineItems.stream().mapToDouble(li -> li.price).sum(); }
        double getTotal() { return total; }
        OrderStatus getStatus() { return status; }
    }

    public static void main(String[] args) {
        Order order = new Order();
        order.addLineItem("widget", 9.99);
        order.confirm();
        System.out.println("Order confirmed, status: " + order.getStatus() + ", total: " + order.getTotal());

        try {
            order.addLineItem("gadget", 19.99); // attempting to modify a CONFIRMED order
        } catch (IllegalStateException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac EnforcingComplexInvariant.java && java EnforcingComplexInvariant` (JDK 17+).

Expected output:
```
Order confirmed, status: CONFIRMED, total: 9.99
Rejected: Cannot modify line items on a CONFIRMED order
```

The production-flavored case: the aggregate root now enforces two invariants across the order's whole lifecycle — line items can't be added to a confirmed order, and an order can't be confirmed while empty. Both rules are checked inside the root's own methods, at the single point every mutation must pass through — there is no way for external code to add a line item to a confirmed order, because the only entry point (`addLineItem`) itself refuses to allow it.

## 6. Walkthrough

1. `order.addLineItem("widget", 9.99)` runs first: `status` is still `OPEN`, so the check passes, the line item is added, and `recalculateTotal()` sets `total` to `9.99`.
2. `order.confirm()` runs next: `lineItems` is not empty, so the check passes, and `status` is set to `CONFIRMED`.
3. The first print confirms both the status transition and the correctly-maintained total.
4. `order.addLineItem("gadget", 19.99)` is attempted inside a `try` block. Inside `addLineItem`, the very first check, `status == OrderStatus.CONFIRMED`, is now `true`, so the method throws `IllegalStateException` immediately — the line item list is never touched, and `total` is never recalculated, because the invariant check happens *before* any mutation.
5. The `catch` block prints the rejection message, confirming the aggregate root successfully protected its own consistency: a confirmed order's line items and total are guaranteed to stay exactly as they were at confirmation time, with no code path anywhere in the program able to bypass that guarantee.

```
addLineItem("widget", 9.99)  -> OPEN, allowed -> total = 9.99
confirm()                    -> lineItems non-empty, allowed -> status = CONFIRMED
addLineItem("gadget", 19.99) -> status == CONFIRMED -> REJECTED, total UNCHANGED
```

## 7. Gotchas & takeaways

> **Gotcha:** a common mistake is making an aggregate too large — bundling `Order`, `Customer`, and `Product` into one giant aggregate because they're all "related" creates unnecessary contention (two unrelated changes, like updating a customer's address and adding a line item to an unrelated order, shouldn't need to coordinate through the same aggregate) and makes the true consistency boundary harder to see. Keep an aggregate limited to exactly what genuinely must be consistent together, and reference other aggregates only by their ID, not by direct object reference.

- An aggregate is a cluster of objects that must be kept consistent as a unit; the aggregate root is the single object external code is allowed to reference and call methods on directly.
- Every mutation to anything inside the aggregate must go through the root's own methods — this is what makes it possible to guarantee the aggregate's invariants hold true after every single change, with no bypass path.
- Complex invariants spanning multiple fields or a state transition (like "a confirmed order can't have its line items changed") belong inside the aggregate root's methods, checked before any mutation is allowed to proceed.
- Keep aggregates small and focused on a genuine consistency boundary — reference other aggregates by ID rather than direct object reference, to avoid unnecessary coupling and contention between unrelated concerns.
