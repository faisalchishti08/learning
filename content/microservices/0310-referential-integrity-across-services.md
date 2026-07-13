---
card: microservices
gi: 310
slug: referential-integrity-across-services
title: "Referential integrity across services"
---

## 1. What it is

Referential integrity — the guarantee that a foreign key always points to a row that actually exists — is normally enforced automatically by a relational database's own constraints within a single schema. Across services, this guarantee disappears entirely: `OrderService` storing a `customerId` has no database-level mechanism forcing that ID to correspond to a real, currently-existing customer in `CustomerService`'s separate database, because there is no shared foreign key constraint that can span two different database instances.

## 2. Why & when

This loss of an automatic guarantee is a direct, unavoidable consequence of [database per service](0304-database-per-service-pattern.md) — the same isolation that provides independence also removes the database engine's ability to enforce cross-service consistency for you. In practice, references across services need to be treated differently based on how strictly they must hold: some references can tolerate occasionally pointing to a deleted or non-existent entity (a `productSku` on an old order referencing a since-discontinued product is often fine to leave as-is, since the order is historical), while others need active enforcement through application-level mechanisms — validating a reference at write time via an API call, or using events to propagate deletions/changes so dependent services can react.

Recognize where strict referential integrity genuinely matters (blocking an operation that would create a dangling reference to something that must exist, like preventing an order for a truly nonexistent customer) versus where eventual, soft consistency is acceptable (a stale display name is a minor issue; an order referencing a deleted customer ID might just need to render as "former customer" rather than blocking anything). Choosing the wrong level of enforcement for a given reference — over-enforcing where staleness would have been fine, or under-enforcing where a dangling reference could cause real harm — is the actual design decision this topic is about.

## 3. Core concept

Validate references synchronously (via an API call) at the point of creation when a dangling reference must never be allowed; otherwise, accept it can dangle and handle that gracefully at read time, or propagate deletions via events so dependent data can be cleaned up asynchronously.

```java
// Option A: SYNCHRONOUS validation at write time -- when the reference
// MUST be valid before the operation is allowed to proceed.
@Service
class OrderService {
    private final CustomerServiceClient customerClient;
    void placeOrder(String customerId, List<OrderLine> lines) {
        if (!customerClient.exists(customerId)) { // API call, validates BEFORE writing
            throw new IllegalArgumentException("customer " + customerId + " does not exist");
        }
        // ... proceed with order creation, reference now KNOWN to be valid at this moment
    }
}

// Option B: EVENTUAL propagation -- accept the dangling window,
// react to it via an event instead of blocking anything up front.
@EventListener
void onCustomerDeleted(CustomerDeletedEvent event) {
    orderRepository.markOrdersAsFormerCustomer(event.customerId()); // graceful cleanup, asynchronous
}
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Within one service's database, a foreign key constraint automatically guarantees a referenced row exists; across services, no such automatic guarantee exists, so each cross-service reference must be deliberately handled either by synchronous validation before writing or by reacting gracefully to events when the referenced entity changes or is deleted">
  <rect x="30" y="30" width="220" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="52" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">WITHIN one database</text>
  <text x="140" y="68" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">FOREIGN KEY -- enforced automatically</text>

  <rect x="390" y="30" width="220" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="500" y="48" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ACROSS services</text>
  <text x="500" y="64" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no automatic guarantee --</text>
  <text x="500" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">must be handled DELIBERATELY</text>

  <text x="500" y="115" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">validate synchronously at write time, OR</text>
  <text x="500" y="130" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">accept staleness and react to events</text>
</svg>

A database-enforced guarantee within one schema becomes a deliberate design decision once services and databases split apart.

## 5. Runnable example

Scenario: an order silently created against a nonexistent customer with no check at all, extended to synchronous validation at write time that blocks the invalid reference from ever being created, and finally handling the harder case — a customer that existed at order time but is later deleted — gracefully via an event-driven reaction instead of leaving a broken dangling reference.

### Level 1 — Basic

```java
// File: NoIntegrityCheck.java -- OrderService accepts a customerId with
// ZERO validation; an order referencing a customer that DOES NOT EXIST
// is created silently, with no error and no warning.
import java.util.*;

public class NoIntegrityCheck {
    static Set<String> existingCustomerIds = Set.of("cust-1", "cust-2");

    record Order(String id, String customerId) {}
    static List<Order> orders = new ArrayList<>();

    static void placeOrder(String orderId, String customerId) {
        orders.add(new Order(orderId, customerId)); // NO check against existingCustomerIds at all
    }

    public static void main(String[] args) {
        placeOrder("order-1", "cust-999"); // does NOT exist!
        System.out.println("Order created: " + orders.get(0)
                + " -- referencing a customer that DOES NOT EXIST, with no error or warning of any kind.");
    }
}
```

How to run: `java NoIntegrityCheck.java`

`placeOrder` accepts any `customerId` without checking it against `existingCustomerIds`, so an order referencing `"cust-999"`, which was never a real customer, is created successfully — a dangling reference from the moment of creation, invisible until something later tries to look up that customer and fails to find them.

### Level 2 — Intermediate

```java
// File: SynchronousValidation.java -- placeOrder now validates the
// customerId against CustomerService's API BEFORE allowing the order to
// be created, preventing the dangling reference from ever existing.
import java.util.*;

public class SynchronousValidation {
    static class CustomerServiceClient {
        Set<String> existingCustomerIds = Set.of("cust-1", "cust-2");
        boolean exists(String customerId) { return existingCustomerIds.contains(customerId); } // stands in for an API call
    }

    record Order(String id, String customerId) {}
    static List<Order> orders = new ArrayList<>();

    static void placeOrder(CustomerServiceClient customerClient, String orderId, String customerId) {
        if (!customerClient.exists(customerId)) {
            throw new IllegalArgumentException("cannot place order: customer '" + customerId + "' does not exist");
        }
        orders.add(new Order(orderId, customerId));
    }

    public static void main(String[] args) {
        CustomerServiceClient customerClient = new CustomerServiceClient();

        placeOrder(customerClient, "order-1", "cust-1"); // VALID
        System.out.println("order-1 created successfully: " + orders.get(0));

        try {
            placeOrder(customerClient, "order-2", "cust-999"); // INVALID
        } catch (IllegalArgumentException e) {
            System.out.println("order-2 REJECTED before creation: " + e.getMessage()
                    + " -- the dangling reference was never allowed to exist.");
        }
    }
}
```

How to run: `java SynchronousValidation.java`

`placeOrder` now calls `customerClient.exists(customerId)` before writing anything. The valid order for `"cust-1"` is created normally. The order attempting to reference `"cust-999"` is rejected with a clear exception *before* any data is written — the dangling reference is prevented structurally, at the cost of `placeOrder` now depending synchronously on `CustomerService`'s availability for every order creation.

### Level 3 — Advanced

```java
// File: EventDrivenGracefulHandling.java -- handles the HARDER case:
// cust-1 existed and was VALID when order-1 was created, but is LATER
// deleted. Rather than leaving order-1 with a silently broken reference,
// OrderService reacts to a CustomerDeletedEvent and gracefully updates
// its own data to reflect the deletion, without blocking anything.
import java.util.*;

public class EventDrivenGracefulHandling {
    static class Order {
        String id, customerId;
        String customerDisplayStatus = "ACTIVE"; // updated gracefully when the customer is later deleted
        Order(String id, String customerId) { this.id = id; this.customerId = customerId; }
        public String toString() { return id + " (customer=" + customerId + ", status=" + customerDisplayStatus + ")"; }
    }

    static List<Order> orders = new ArrayList<>();
    static Set<String> existingCustomerIds = new HashSet<>(Set.of("cust-1"));

    static void placeOrder(String orderId, String customerId) {
        if (!existingCustomerIds.contains(customerId)) throw new IllegalArgumentException("customer does not exist");
        orders.add(new Order(orderId, customerId));
    }

    // Simulates CustomerService publishing a CustomerDeletedEvent, and
    // OrderService's event listener reacting to it -- NOT a synchronous
    // check, but a graceful, asynchronous cleanup of dependent data.
    static void onCustomerDeletedEvent(String customerId) {
        existingCustomerIds.remove(customerId);
        for (Order order : orders) {
            if (order.customerId.equals(customerId)) {
                order.customerDisplayStatus = "FORMER CUSTOMER (deleted)"; // graceful, not a hard failure
            }
        }
        System.out.println("  [event] customer '" + customerId + "' deleted -- " + orders.size()
                + " existing order(s) gracefully updated, NOT deleted or broken.");
    }

    public static void main(String[] args) {
        placeOrder("order-1", "cust-1"); // valid at creation time
        System.out.println("Before deletion: " + orders.get(0));

        onCustomerDeletedEvent("cust-1"); // customer is later deleted in CustomerService

        System.out.println("After deletion:  " + orders.get(0)
                + " -- the order still exists and displays gracefully, rather than being a silently broken dangling reference.");

        try {
            placeOrder("order-2", "cust-1"); // NEW orders against the now-deleted customer are correctly rejected
        } catch (IllegalArgumentException e) {
            System.out.println("New order against deleted customer correctly REJECTED: " + e.getMessage());
        }
    }
}
```

How to run: `java EventDrivenGracefulHandling.java`

`order-1` is created while `cust-1` is valid. When `cust-1` is later deleted, `onCustomerDeletedEvent` — standing in for an event listener reacting to a `CustomerDeletedEvent` published by `CustomerService` — updates `order-1`'s local `customerDisplayStatus` field gracefully, rather than leaving the order with a silently dangling `customerId` that would fail unpredictably if something tried to look up that customer later. The order itself is preserved (historical orders shouldn't simply vanish because a customer account was later deleted), but a *new* order attempted against the now-deleted customer is still correctly rejected by the synchronous validation, since `existingCustomerIds` was updated by the same event.

## 6. Walkthrough

Trace `EventDrivenGracefulHandling.main` in order. **First**, `placeOrder("order-1", "cust-1")` is called; `existingCustomerIds` contains `"cust-1"`, so the check passes, and a new `Order` is added to `orders` with `customerDisplayStatus="ACTIVE"` (its default).

**`onCustomerDeletedEvent("cust-1")` is called**, simulating `OrderService`'s event listener reacting to a `CustomerDeletedEvent` that `CustomerService` published after actually deleting the customer in its own database. Inside, `existingCustomerIds.remove("cust-1")` updates the local validation set — this is `OrderService`'s own, locally-maintained knowledge of which customer IDs are currently valid, kept in sync via events rather than a live cross-service query on every check.

**The method then iterates `orders`**, finds `order-1` (whose `customerId` matches `"cust-1"`), and sets its `customerDisplayStatus` to `"FORMER CUSTOMER (deleted)"` — this mutates `OrderService`'s own data in response to the event, gracefully reflecting the fact that the referenced customer no longer exists, without deleting the order itself or leaving it in a broken, unexplained state.

**`orders.get(0)` is printed again**, now showing the updated status — the order record itself is unchanged in every other respect (its ID, its customer ID reference, its line items would all remain intact in a real system), only its *display* status reflects the now-known fact that this reference points to a deleted entity.

**Finally, `placeOrder("order-2", "cust-1")` is attempted.** Since `existingCustomerIds` no longer contains `"cust-1"` (removed by the event handler moments earlier), the validation check `!existingCustomerIds.contains(customerId)` is `true`, and the method throws `IllegalArgumentException` — correctly preventing a *new* dangling reference to a customer already known to be deleted, even though this rejection happens via the same locally-maintained set that the event handler keeps updated, not a fresh synchronous call to `CustomerService` for this specific check.

```
placeOrder("order-1", "cust-1")  -- cust-1 IS in existingCustomerIds -> order created, status=ACTIVE
CustomerService deletes cust-1 -> publishes CustomerDeletedEvent
OrderService.onCustomerDeletedEvent("cust-1")
        |
        +-- existingCustomerIds.remove("cust-1")     (local validation set updated)
        +-- order-1.customerDisplayStatus = "FORMER CUSTOMER (deleted)"   (graceful, not broken)
placeOrder("order-2", "cust-1")  -- cust-1 NOT in existingCustomerIds -> REJECTED
```

## 7. Gotchas & takeaways

> Treating every cross-service reference as requiring strict, synchronous, always-consistent enforcement recreates tight coupling between services (every write depends on another service's availability) — while treating every reference as freely allowed to dangle indefinitely risks confusing or broken behavior wherever that reference is later used. The right choice is per-reference, based on the actual cost of a temporarily dangling reference for that specific case.

- Referential integrity across service boundaries is never automatic — it requires a deliberate choice per reference between synchronous validation at write time and eventual, event-driven reconciliation.
- Synchronous validation is appropriate when a dangling reference must never be allowed to exist even momentarily, at the cost of coupling that write path's availability to the referenced service's availability.
- Event-driven reconciliation is appropriate when a brief window of staleness is acceptable, and lets the referencing service react gracefully (not necessarily by deleting its own data) once it learns the referenced entity changed or was removed.
- A locally-maintained, event-synced set of valid IDs (as in Level 3) lets a service validate new references quickly, without a synchronous cross-service call on every write, while still staying reasonably current — a common, practical middle ground between the two extremes.
