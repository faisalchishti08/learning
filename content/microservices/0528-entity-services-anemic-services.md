---
card: microservices
gi: 528
slug: entity-services-anemic-services
title: "Entity services / anemic services"
---

## 1. What it is

An **entity service** (or **anemic service**) is a microservice built directly around a database entity — a "Customer service," an "Order service" — that exposes little more than CRUD operations (create, read, update, delete) mirroring the entity's columns, with no real business logic or behavior of its own. It's the microservices-era version of the "anemic domain model" anti-pattern: data and behavior have been split apart, with the service holding data and callers left to implement whatever business logic actually operates on that data themselves, scattered across every caller instead of owned in one place.

## 2. Why & when

You watch for entity/anemic services because they push complexity to the wrong place and erode the entire value of having a service boundary:

- **A service boundary should encapsulate a business capability, not just a data table.** "Customer service" that only offers `createCustomer`, `getCustomer`, `updateCustomer`, `deleteCustomer` is really just a remote database table with extra steps — none of the actual business rules around *what it means* to update a customer (validation, side effects, invariants) live inside the service; they live wherever a caller happens to implement them.
- **This forces business logic to duplicate across every caller.** If "cancelling an order" involves several steps — checking it hasn't shipped, refunding payment, releasing reserved inventory — and the Order service only exposes `updateOrder(status)`, every single caller that needs to cancel an order has to reimplement that entire sequence correctly, independently, with no guarantee they all get it right or stay in sync as the rules evolve.
- **It defeats encapsulation and invariant enforcement.** A well-designed service protects its own invariants — "an order's total can never go negative," "a cancelled order can't be shipped" — by only exposing operations that preserve them. A pure CRUD interface lets any caller set any field to any value, including combinations that violate the entity's own business rules, because the service never expressed those rules as part of its interface.
- **The fix is to expose behavior-shaped operations, not field-shaped ones** — `cancelOrder(orderId)`, `shipOrder(orderId)`, `applyDiscount(orderId, code)` — each one encapsulating the business rules and side effects that operation requires, so callers describe *intent* ("cancel this order") rather than manually recreating the mechanics of what cancellation actually involves.

## 3. Core concept

Think of a bank that, instead of offering "withdraw money" as a teller operation (which enforces "you can't withdraw more than your balance," "large withdrawals need ID," "certain account types have a hold period"), simply hands every customer direct edit access to their own balance field in a spreadsheet. Technically, "withdrawing $50" is just "reduce the balance field by 50" — but every single customer now has to remember, and correctly apply, all the bank's actual rules themselves, with nothing stopping one customer from setting their own balance to any number they like. A real "withdraw" operation encodes the rules once, in one place, and every customer interacts with the intent ("I want to withdraw $50") rather than the raw mechanics of the underlying data.

Concretely:

1. **CRUD operations expose the shape of the data**, not the shape of the business — `updateCustomer(customer)` lets a caller set any field to anything, with no way for the service to know or enforce *why* the update is happening or whether it's a legitimate transition.
2. **Behavior-shaped operations expose the shape of the business** — `changeShippingAddress(customerId, newAddress)`, `deactivateAccount(customerId, reason)` — each one named after an actual intent, and each one free to enforce whatever validation, side effects, or invariants that specific intent requires.
3. **Business logic that operates on an entity belongs inside the service that owns that entity**, not scattered across every caller — this is what makes the service an actual encapsulation boundary, rather than a thin, rule-free wrapper around a table.
4. **Recognizing an anemic service is often as simple as asking "does this service's interface read like a list of business actions, or a list of database columns?"** — a service whose every method is `getX`/`setX`/`updateX` mirroring field names is very likely anemic, regardless of how many separate methods it has.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Anemic service exposes raw CRUD, pushing business rules to every caller; behavior-shaped service exposes named business operations that enforce the rules once, in one place">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Anemic (CRUD-shaped)</text>
  <rect x="20" y="35" width="260" height="80" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService.updateOrder(order)</text>
  <text x="150" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">caller must know: check not shipped,</text>
  <text x="150" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">refund payment, release inventory --</text>
  <text x="150" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reimplemented by EVERY caller</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Behavior-shaped</text>
  <rect x="380" y="35" width="260" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService.cancelOrder(orderId)</text>
  <text x="510" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">checks, refund, and release logic</text>
  <text x="510" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">live ONCE inside the service --</text>
  <text x="510" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">every caller just states intent</text>
</svg>

CRUD-shaped operations push business rules out to every caller; behavior-shaped operations enforce them once, inside the owning service.

## 5. Runnable example

Scenario: cancelling an order that involves several business rules. We start with the anemic CRUD version where callers reimplement cancellation logic themselves, extend it to show two callers implementing it slightly differently (drift), then handle the fix: a behavior-shaped `cancelOrder` operation that owns the entire rule set in one place.

### Level 1 — Basic

```java
// File: AnemicOrderService.java -- pure CRUD: callers must know and
// apply the business rules around "cancelling" an order THEMSELVES.
import java.util.*;

public class AnemicOrderService {
    enum Status { PLACED, SHIPPED, CANCELLED }
    static class Order {
        String id; Status status; boolean paymentRefunded; boolean inventoryReleased;
        Order(String id, Status status) { this.id = id; this.status = status; }
    }

    static Map<String, Order> orders = new HashMap<>(Map.of("order-1", new Order("order-1", Status.PLACED)));

    // pure CRUD: just sets whatever field the caller passes, no business rules enforced
    static void updateOrder(String id, Status newStatus) {
        orders.get(id).status = newStatus;
    }

    public static void main(String[] args) {
        // caller has to remember EVERYTHING cancellation requires, by hand:
        Order order = orders.get("order-1");
        if (order.status != Status.SHIPPED) { // caller-side check #1
            updateOrder("order-1", Status.CANCELLED);
            order.paymentRefunded = true;      // caller-side step #2
            order.inventoryReleased = true;    // caller-side step #3
            System.out.println("Cancelled order-1 (caller manually did all 3 steps correctly, this time)");
        }
    }
}
```

How to run: `java AnemicOrderService.java`

`updateOrder` blindly sets whatever status the caller passes — it has no idea "cancelling" also requires refunding payment and releasing inventory. The caller in `main` happens to remember all three steps this time, but nothing in `AnemicOrderService`'s interface enforces, checks, or even documents that these three things must happen together.

### Level 2 — Intermediate

```java
// File: DriftedCallers.java -- TWO DIFFERENT callers reimplement
// cancellation slightly differently -- one of them forgets a step.
import java.util.*;

public class DriftedCallers {
    enum Status { PLACED, SHIPPED, CANCELLED }
    static class Order {
        String id; Status status; boolean paymentRefunded; boolean inventoryReleased;
        Order(String id, Status status) { this.id = id; this.status = status; }
    }
    static Map<String, Order> orders = new HashMap<>(Map.of(
        "order-1", new Order("order-1", Status.PLACED),
        "order-2", new Order("order-2", Status.PLACED)
    ));
    static void updateOrder(String id, Status newStatus) { orders.get(id).status = newStatus; }

    // Caller A (web checkout team): remembers all 3 steps
    static void cancelFromWebCheckout(String orderId) {
        Order order = orders.get(orderId);
        updateOrder(orderId, Status.CANCELLED);
        order.paymentRefunded = true;
        order.inventoryReleased = true;
    }

    // Caller B (admin tool team, built independently, months later): FORGOT inventory release
    static void cancelFromAdminTool(String orderId) {
        Order order = orders.get(orderId);
        updateOrder(orderId, Status.CANCELLED);
        order.paymentRefunded = true;
        // BUG: inventoryReleased is never set -- inventory stays reserved forever for a cancelled order
    }

    public static void main(String[] args) {
        cancelFromWebCheckout("order-1");
        cancelFromAdminTool("order-2");
        for (Order o : orders.values()) {
            System.out.println(o.id + ": status=" + o.status + ", refunded=" + o.paymentRefunded + ", inventoryReleased=" + o.inventoryReleased);
        }
        System.out.println("order-2's inventory is now stuck reserved forever -- the admin tool's caller didn't know it had to release it.");
    }
}
```

How to run: `java DriftedCallers.java`

Two independently-built callers each reimplement "cancel an order" against the same anemic `updateOrder` primitive. `cancelFromWebCheckout` gets all three steps right; `cancelFromAdminTool`, built later by a different team with no shared cancellation logic to rely on, forgets to release inventory. The output shows `order-2` left with `inventoryReleased=false` — a real, silent bug caused entirely by the business rule living nowhere except in each caller's memory.

### Level 3 — Advanced

```java
// File: BehaviorShapedFix.java -- the FIX: a NAMED operation,
// cancelOrder(orderId), that owns ALL the business rules and side
// effects internally -- every caller just expresses intent.
import java.util.*;

public class BehaviorShapedFix {
    enum Status { PLACED, SHIPPED, CANCELLED }
    static class Order {
        String id; Status status; boolean paymentRefunded; boolean inventoryReleased;
        Order(String id, Status status) { this.id = id; this.status = status; }
    }

    static class OrderService {
        private Map<String, Order> orders = new HashMap<>(Map.of(
            "order-1", new Order("order-1", Status.PLACED),
            "order-2", new Order("order-2", Status.SHIPPED)
        ));

        // the ONE place all of cancellation's rules and side effects live
        String cancelOrder(String orderId) {
            Order order = orders.get(orderId);
            if (order == null) return "REJECTED: no such order";
            if (order.status == Status.SHIPPED) return "REJECTED: cannot cancel a shipped order";
            order.status = Status.CANCELLED;
            order.paymentRefunded = true;
            order.inventoryReleased = true;
            return "CANCELLED: " + orderId + " (payment refunded, inventory released)";
        }

        Order get(String orderId) { return orders.get(orderId); }
    }

    public static void main(String[] args) {
        OrderService orderService = new OrderService();

        // "web checkout" caller: just expresses intent
        System.out.println(orderService.cancelOrder("order-1"));
        // "admin tool" caller: same one-line call, gets the SAME correct behavior automatically
        System.out.println(orderService.cancelOrder("order-2")); // already shipped -- correctly rejected

        Order order1 = orderService.get("order-1");
        System.out.println("order-1: status=" + order1.status + ", refunded=" + order1.paymentRefunded + ", inventoryReleased=" + order1.inventoryReleased);
    }
}
```

How to run: `java BehaviorShapedFix.java`

`cancelOrder` is the single owner of every rule cancellation requires: checking the order isn't already shipped, updating status, refunding payment, and releasing inventory — all inside one method, inside the service that owns the `Order` entity. Both callers ("web checkout" and "admin tool," represented here by the two `cancelOrder` calls) get identical, correct behavior automatically, including the correct rejection for `order-2` (already shipped) — no caller has to know or remember any of these rules themselves.

## 6. Walkthrough

Trace `BehaviorShapedFix.main` end to end:

1. **`OrderService` is constructed**, initializing two orders: `order-1` (status `PLACED`) and `order-2` (status `SHIPPED`) — both stored in a private map, not directly accessible to callers.
2. **`orderService.cancelOrder("order-1")` is called.** Inside, it looks up `order-1`, checks `order.status == Status.SHIPPED` — false, since it's `PLACED` — so it proceeds: sets `status = CANCELLED`, `paymentRefunded = true`, `inventoryReleased = true`, all in one place, and returns the success message.
3. **`orderService.cancelOrder("order-2")` is called next.** It looks up `order-2`, checks the same condition — this time `true`, since `order-2` is `SHIPPED` — and immediately returns the rejection message `"REJECTED: cannot cancel a shipped order"` without touching any of `order-2`'s fields at all.
4. **`main` retrieves `order-1` via `orderService.get("order-1")`** and prints its final state: `status=CANCELLED, refunded=true, inventoryReleased=true` — all three effects correctly applied together, every time, because they live inside one method rather than being manually reconstructed by each caller.

Contrast with Level 2: there, the exact same two logical actions (cancel a placed order, attempt to cancel a shipped order) were left to each caller to implement independently, and one caller's implementation drifted from correctness — a bug that `BehaviorShapedFix` makes structurally impossible, since there's no code path a caller could take that bypasses the rules; calling `cancelOrder` is the *only* way to cancel an order, and that one method is where the rules live.

## 7. Gotchas & takeaways

> **Gotcha:** adding more CRUD-style getter/setter methods to an anemic service ("we'll add `updatePaymentRefunded` and `updateInventoryReleased` as separate endpoints too") doesn't fix anemia — it just gives callers more fine-grained ways to violate the entity's invariants; the fix is fewer, more meaningful, behavior-named operations, not more field-level ones.

- A quick diagnostic: if a service's method names read like column names (`getX`, `setX`, `updateX`) rather than business actions (`cancelOrder`, `applyDiscount`, `promoteToPremium`), it's very likely anemic.
- Business logic that operates on an entity belongs inside the service that owns that entity — pushing it out to callers means it will be reimplemented multiple times, inconsistently, by people who don't necessarily know all the rules.
- Behavior-shaped operations aren't just about organization — they're what let a service actually enforce its own invariants, since callers can no longer set any field to any value directly.
- When reviewing a service's API, ask what business capability each endpoint represents; an endpoint that's really just "set this column" is a sign the real business operation it's meant to support hasn't been identified and named yet.
