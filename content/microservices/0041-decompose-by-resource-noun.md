---
card: microservices
gi: 41
slug: decompose-by-resource-noun
title: Decompose by resource / noun
---

## 1. What it is

**Decomposing by resource (or "noun")** draws service boundaries around a data entity — `OrderService` owns everything about orders (create, read, update, cancel, ship), `CustomerService` owns everything about customers — rather than splitting each individual action into its own service. This is the more common default in REST-oriented systems, where a service naturally maps to a RESTful resource with standard operations (`GET /orders/{id}`, `POST /orders`, `DELETE /orders/{id}`) exposed together under one coherent API and one team's ownership.

## 2. Why & when

Resource-based decomposition fits naturally when an entity's various operations share the same underlying data, the same business invariants, and are reasonably close in complexity and change frequency — placing, updating, and cancelling an order usually all need to enforce consistent rules about what a valid order looks like, and keeping that validation logic in one place (one service) avoids duplicating or, worse, subtly diverging business rules across several separate verb-based services.

Use resource-based decomposition as your default starting point for most entities — it's simpler to reason about, requires fewer network hops for related operations, and keeps an entity's invariants enforced in exactly one place. Move away from it toward [verb-based decomposition](0040-decompose-by-use-case-verb.md) only once you have a concrete reason: operations on the entity have genuinely diverged in traffic, ownership, or complexity enough that bundling them creates real coupling cost.

## 3. Core concept

A resource-based service owns the full lifecycle of one entity type, typically mapping directly onto REST's standard verbs against one URL path:

```
OrderService  owns  /orders
  GET    /orders/{id}   -> read
  POST   /orders        -> create
  PUT    /orders/{id}   -> update
  DELETE /orders/{id}   -> cancel
```

All of these share one team, one deploy pipeline, one database — and, critically, one place where "what makes an order valid" is enforced consistently across every operation that touches it.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OrderService owns the full lifecycle of the Order resource -- create, read, update, cancel -- all sharing one consistent set of business invariants">
  <rect x="200" y="30" width="240" height="120" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="320" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">POST /orders (create)</text>
  <text x="320" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">GET /orders/{id} (read)</text>
  <text x="320" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">PUT /orders/{id} (update)</text>
  <text x="320" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">DELETE /orders/{id} (cancel)</text>
  <text x="320" y="140" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">ONE consistent validation layer</text>
</svg>

One resource, one service, one consistently-enforced set of business rules across every operation.

## 5. Runnable example

Scenario: order operations organized around the `Order` resource, first showing how shared validation logic lives in one place, then extended to show what would break if that validation were duplicated across separate verb-based services instead.

### Level 1 — Basic

```java
// File: ResourceBasedOrderService.java -- ONE service owns the Order
// resource's FULL lifecycle, including its validation rules.
public class ResourceBasedOrderService {
    static class Order { String id; double total; String status; Order(String id, double total, String status) { this.id = id; this.total = total; this.status = status; } }

    static class OrderService {
        java.util.Map<String, Order> orders = new java.util.HashMap<>();

        // the ONE place order validity is defined -- used by EVERY operation below
        boolean isValid(double total) { return total > 0; }

        String create(String id, double total) {
            if (!isValid(total)) return "rejected: invalid total";
            orders.put(id, new Order(id, total, "PLACED"));
            return "created: " + id;
        }

        String update(String id, double newTotal) {
            if (!isValid(newTotal)) return "rejected: invalid total"; // SAME validation rule reused
            orders.get(id).total = newTotal;
            return "updated: " + id;
        }
    }

    public static void main(String[] args) {
        OrderService orders = new OrderService();
        System.out.println(orders.create("ord-1", 9.99));
        System.out.println(orders.update("ord-1", -5.0)); // invalid -- caught by the SAME rule create() used
    }
}
```

**How to run:** `javac ResourceBasedOrderService.java && java ResourceBasedOrderService` (JDK 17+).

Expected output:
```
created: ord-1
rejected: invalid total
```

`isValid` is defined once and reused by both `create` and `update` — the business rule "a total must be positive" is enforced consistently, with zero risk of the two operations quietly disagreeing about what counts as valid.

### Level 2 — Intermediate

```java
// File: DuplicatedValidationRisk.java -- shows what happens if validation
// logic is DUPLICATED across separate verb-based services instead, and
// one copy DRIFTS from the other during maintenance.
public class DuplicatedValidationRisk {
    static class CreateOrderService {
        boolean isValid(double total) { return total > 0; } // copy #1
        String create(String id, double total) { return isValid(total) ? "created: " + id : "rejected: invalid total"; }
    }

    static class UpdateOrderService {
        // copy #2 -- maintained SEPARATELY, and a later "fix" here forgot to also update copy #1
        boolean isValid(double total) { return total >= 0; } // BUG: now allows total == 0, copy #1 does not
        String update(String id, double newTotal) { return isValid(newTotal) ? "updated: " + id : "rejected: invalid total"; }
    }

    public static void main(String[] args) {
        CreateOrderService create = new CreateOrderService();
        UpdateOrderService update = new UpdateOrderService();

        System.out.println("create($0.00): " + create.create("ord-1", 0.0));  // rejected by copy #1's rule
        System.out.println("update($0.00): " + update.update("ord-1", 0.0));  // ACCEPTED by copy #2's drifted rule
    }
}
```

**How to run:** `javac DuplicatedValidationRisk.java && java DuplicatedValidationRisk` (JDK 17+).

Expected output:
```
create($0.00): rejected: invalid total
update($0.00): updated: ord-1
```

The two services silently disagree on whether `$0.00` is a valid order total — `create` rejects it, `update` accepts it — because each service maintains its own separate copy of the same conceptual business rule, and one copy drifted during unrelated maintenance. This is the concrete risk resource-based decomposition avoids by keeping such rules in exactly one place.

### Level 3 — Advanced

```java
// File: ConsistentAcrossOperations.java -- back to resource-based, now
// proving CONSISTENCY holds across every operation touching the resource,
// even as the entity's lifecycle grows to include a THIRD operation.
public class ConsistentAcrossOperations {
    static class Order { String id; double total; String status; Order(String id, double total, String status) { this.id = id; this.total = total; this.status = status; } }

    static class OrderService {
        java.util.Map<String, Order> orders = new java.util.HashMap<>();

        boolean isValid(double total) { return total > 0; } // the ONE rule, used by ALL THREE operations below

        String create(String id, double total) {
            if (!isValid(total)) return "rejected: invalid total";
            orders.put(id, new Order(id, total, "PLACED"));
            return "created: " + id;
        }

        String update(String id, double newTotal) {
            if (!isValid(newTotal)) return "rejected: invalid total";
            orders.get(id).total = newTotal;
            return "updated: " + id;
        }

        // a NEW operation added later -- automatically inherits the SAME validation, no risk of drift
        String applyDiscount(String id, double discountAmount) {
            Order order = orders.get(id);
            double newTotal = order.total - discountAmount;
            if (!isValid(newTotal)) return "rejected: discount would make total invalid"; // SAME rule, reused AGAIN
            order.total = newTotal;
            return "discount applied to " + id + ", new total: " + newTotal;
        }
    }

    public static void main(String[] args) {
        OrderService orders = new OrderService();
        orders.create("ord-1", 9.99);
        System.out.println(orders.applyDiscount("ord-1", 5.00));   // valid: 9.99 - 5.00 = 4.99
        System.out.println(orders.applyDiscount("ord-1", 100.00)); // invalid: would go negative, rejected by the SAME rule
    }
}
```

**How to run:** `javac ConsistentAcrossOperations.java && java ConsistentAcrossOperations` (JDK 17+).

Expected output:
```
discount applied to ord-1, new total: 4.99
rejected: discount would make total invalid
```

The production-flavored payoff: `applyDiscount`, a brand-new operation added later, automatically reuses `isValid` — the exact same rule `create` and `update` already depend on. There was no separate copy to remember to write, and no risk of this new operation silently disagreeing with the other two about what a valid order total is, precisely because all three operations live inside the one service that owns the `Order` resource.

## 6. Walkthrough

1. `orders.create("ord-1", 9.99)` runs first, calling `isValid(9.99)`, which returns `true` (`9.99 > 0`), so the order is created and stored in `orders.orders`.
2. `orders.applyDiscount("ord-1", 5.00)` runs next: it reads the existing `Order`, computes `newTotal = 9.99 - 5.00 = 4.99`, then calls the *same* `isValid` method, which returns `true` (`4.99 > 0`). The order's `total` field is updated, and the method returns the success message.
3. `orders.applyDiscount("ord-1", 100.00)` runs last: it computes `newTotal = 4.99 - 100.00 = -95.01`, then calls `isValid(-95.01)`, which correctly returns `false` (not greater than `0`), so the method returns the rejection message without mutating `order.total` at all.
4. Every one of these three method calls — `create`, `update` (in Level 1/3's earlier example), and `applyDiscount` — resolves `isValid` to the exact same method body, defined exactly once on `OrderService`. There is no separate "discount validation" logic that could have drifted from the original rule the way `DuplicatedValidationRisk`'s two services drifted from each other.

```
OrderService.isValid(total)  <- ONE rule
        |
   +----+----+------------------+
create()  update()  applyDiscount()   <- ALL THREE call the SAME isValid, guaranteed consistent
```

## 7. Gotchas & takeaways

> **Gotcha:** resource-based decomposition's consistency benefit only holds as long as the resource genuinely stays as one service — the moment a team, under scaling or ownership pressure, splits `OrderService`'s operations across multiple services without deliberately extracting the shared validation logic into a common, explicitly reused place (a shared library, or one operation calling another's API), `DuplicatedValidationRisk`'s drift scenario becomes a live risk again.

- Resource-based (noun) decomposition organizes a service around a data entity's full lifecycle — create, read, update, delete — typically mapping directly onto a RESTful API for that resource.
- The concrete benefit: business invariants and validation rules for that entity live in exactly one place, guaranteed to be applied consistently across every operation that touches the entity.
- The concrete risk it avoids: [verb-based decomposition](0040-decompose-by-use-case-verb.md) done carelessly can duplicate shared validation logic across several separate services, which can then silently drift out of sync during independent maintenance.
- Use resource-based decomposition as the default for most entities, moving to verb-based splitting only when specific operations have diverged enough in traffic, ownership, or complexity to justify the coordination cost of keeping shared rules consistent across separate services.
