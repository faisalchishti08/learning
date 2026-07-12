---
card: microservices
gi: 42
slug: self-contained-service-pattern
title: Self-contained service pattern
---

## 1. What it is

The **self-contained service (SCS) pattern** requires that a service handle any request it receives using only its own local data — no synchronous, blocking calls out to other services during request handling. Any data the service needs from elsewhere is obtained *ahead of time*, asynchronously (typically by consuming events and keeping a local, denormalized copy), rather than fetched *during* the request by calling another service and waiting for its response. This directly extends [design for failure](0011-design-for-failure.md) and [decentralized data management](0009-decentralized-data-management.md): if a service never makes a synchronous call to another service while serving a request, another service being slow or down can never directly cause *this* service's request to be slow or fail.

## 2. Why & when

A request that fans out to several synchronous downstream calls inherits the combined latency and combined failure probability of every one of those calls — even with retries and circuit breakers in place (see [design for failure](0011-design-for-failure.md)), a chain of synchronous dependencies is fundamentally more fragile than a service that can answer entirely from its own local, already-available data. The self-contained pattern eliminates that fragility at the root: if `OrderService` never calls `CustomerService` synchronously to render an order confirmation, `CustomerService` being down simply cannot break `OrderService`'s response to that request.

Apply this pattern for latency- and reliability-sensitive read paths especially — anywhere a slow or failing dependency during request handling would be unacceptable. The tradeoff, made explicit rather than hidden, is staleness: a locally-cached copy of another service's data is only as fresh as the last event it processed, so this pattern trades perfect real-time consistency for reliability and speed, an explicit and often very worthwhile tradeoff.

## 3. Core concept

The shift is in *when* cross-service data is fetched, not whether it's ever needed:

- **Synchronous dependency (not self-contained):** `OrderService` receives a request, calls `CustomerService` over the network, waits for the response, then finishes handling the request. `CustomerService` being slow makes this request slow.
- **Self-contained:** `OrderService` already has a local, denormalized copy of the customer data it needs, kept up to date by consuming `CustomerService`'s events *before* any request arrives. Handling the request touches only local data — no network call, no dependency on `CustomerService`'s current availability.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A non-self-contained service calls another service synchronously during request handling; a self-contained service keeps a locally updated copy of that data, ahead of time, via events">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">NOT self-contained</text>
  <rect x="30" y="50" width="110" height="45" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="85" y="77" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">request arrives</text>
  <rect x="180" y="50" width="130" height="45" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="245" y="70" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">synchronous call</text>
  <text x="245" y="85" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">to CustomerService</text>
  <line x1="140" y1="72" x2="180" y2="72" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a42)"/>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Self-contained</text>
  <rect x="420" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">events consumed AHEAD OF TIME</text>
  <rect x="420" y="90" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="110" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">request served from</text>
  <text x="510" y="125" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">LOCAL data only</text>
  <defs><marker id="a42" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker></defs>
</svg>

Fetch cross-service data synchronously during the request, or asynchronously ahead of time and serve entirely from local state.

## 5. Runnable example

Scenario: rendering an order confirmation needing customer data, first via a synchronous, fragile call, then refactored to a self-contained design using a locally maintained copy kept up to date via events.

### Level 1 — Basic

```java
// File: SynchronousDependency.java -- NOT self-contained: OrderService
// calls CustomerService SYNCHRONOUSLY during request handling.
public class SynchronousDependency {
    static class CustomerService {
        boolean isDown = false;
        String getEmail(String customerId) {
            if (isDown) throw new RuntimeException("CustomerService is down");
            return "alice@example.com";
        }
    }

    static class OrderService {
        CustomerService customerService;
        OrderService(CustomerService customerService) { this.customerService = customerService; }

        String renderConfirmation(String customerId, String item) {
            String email = customerService.getEmail(customerId); // SYNCHRONOUS call, DURING request handling
            return "Order confirmed for " + item + ", sent to " + email;
        }
    }

    public static void main(String[] args) {
        CustomerService customerService = new CustomerService();
        OrderService orders = new OrderService(customerService);

        System.out.println(orders.renderConfirmation("cust-1", "widget")); // works fine

        customerService.isDown = true; // CustomerService goes down
        try {
            System.out.println(orders.renderConfirmation("cust-1", "widget"));
        } catch (RuntimeException e) {
            System.out.println("Order confirmation FAILED entirely: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac SynchronousDependency.java && java SynchronousDependency` (JDK 17+).

Expected output:
```
Order confirmed for widget, sent to alice@example.com
Order confirmation FAILED entirely: CustomerService is down
```

`renderConfirmation` fails completely the moment `CustomerService` is unreachable, even though `OrderService`'s own order data is perfectly fine — a dependency having nothing to do with the order itself broke the whole request.

### Level 2 — Intermediate

```java
// File: SelfContainedWithLocalCopy.java -- OrderService keeps its OWN
// local copy of customer email, updated via events, BEFORE any request arrives.
import java.util.*;

public class SelfContainedWithLocalCopy {
    interface CustomerEventListener { void onCustomerEmailChanged(String customerId, String email); }

    static class CustomerService {
        List<CustomerEventListener> listeners = new ArrayList<>();
        void subscribe(CustomerEventListener listener) { listeners.add(listener); }
        void updateEmail(String customerId, String email) {
            for (var listener : listeners) listener.onCustomerEmailChanged(customerId, email); // publish AHEAD of any request
        }
    }

    static class OrderService {
        Map<String, String> localCustomerEmails = new HashMap<>(); // OrderService's OWN local, denormalized copy

        void onCustomerEmailChanged(String customerId, String email) { localCustomerEmails.put(customerId, email); }

        String renderConfirmation(String customerId, String item) {
            String email = localCustomerEmails.getOrDefault(customerId, "unknown@example.com"); // LOCAL read, no network call
            return "Order confirmed for " + item + ", sent to " + email;
        }
    }

    public static void main(String[] args) {
        CustomerService customerService = new CustomerService();
        OrderService orders = new OrderService();
        customerService.subscribe(orders::onCustomerEmailChanged);

        customerService.updateEmail("cust-1", "alice@example.com"); // happens BEFORE any order request

        System.out.println(orders.renderConfirmation("cust-1", "widget")); // served ENTIRELY from local data
    }
}
```

**How to run:** `javac SelfContainedWithLocalCopy.java && java SelfContainedWithLocalCopy` (JDK 17+).

Expected output:
```
Order confirmed for widget, sent to alice@example.com
```

`renderConfirmation` never calls `CustomerService` at all during request handling — it reads only from `localCustomerEmails`, a copy already populated ahead of time via the event subscription. There is no synchronous dependency for a request to fail on.

### Level 3 — Advanced

```java
// File: ProveResilienceUnderOutage.java -- prove the self-contained
// design SURVIVES a CustomerService outage that would have broken Level 1.
import java.util.*;

public class ProveResilienceUnderOutage {
    interface CustomerEventListener { void onCustomerEmailChanged(String customerId, String email); }

    static class CustomerService {
        List<CustomerEventListener> listeners = new ArrayList<>();
        boolean isDown = false;
        void subscribe(CustomerEventListener listener) { listeners.add(listener); }
        void updateEmail(String customerId, String email) {
            if (isDown) { System.out.println("  [CustomerService] DOWN -- cannot publish event right now"); return; }
            for (var listener : listeners) listener.onCustomerEmailChanged(customerId, email);
        }
    }

    static class OrderService {
        Map<String, String> localCustomerEmails = new HashMap<>();
        void onCustomerEmailChanged(String customerId, String email) { localCustomerEmails.put(customerId, email); }
        String renderConfirmation(String customerId, String item) {
            String email = localCustomerEmails.getOrDefault(customerId, "unknown@example.com");
            return "Order confirmed for " + item + ", sent to " + email;
        }
    }

    public static void main(String[] args) {
        CustomerService customerService = new CustomerService();
        OrderService orders = new OrderService();
        customerService.subscribe(orders::onCustomerEmailChanged);

        customerService.updateEmail("cust-1", "alice@example.com"); // event delivered while CustomerService is UP
        System.out.println(orders.renderConfirmation("cust-1", "widget")); // works, uses local copy

        customerService.isDown = true; // CustomerService now goes DOWN entirely
        System.out.println(orders.renderConfirmation("cust-1", "widget")); // STILL works -- OrderService never calls it during requests
        System.out.println(orders.renderConfirmation("cust-2", "gadget")); // works for a customer never seen before too, just falls back
    }
}
```

**How to run:** `javac ProveResilienceUnderOutage.java && java ProveResilienceUnderOutage` (JDK 17+).

Expected output:
```
Order confirmed for widget, sent to alice@example.com
Order confirmed for widget, sent to alice@example.com
Order confirmed for gadget, sent to unknown@example.com
```

The production-flavored proof: after `customerService.isDown = true`, `OrderService.renderConfirmation` is called twice more and succeeds both times — including for `cust-2`, a customer `OrderService` never received an event for, which correctly falls back to `"unknown@example.com"` rather than throwing. Unlike Level 1's `SynchronousDependency`, `CustomerService`'s outage has zero effect on `OrderService`'s ability to serve requests, because `renderConfirmation` never calls `CustomerService` at all — it only ever reads from its own already-populated local copy.

## 6. Walkthrough

1. `customerService.updateEmail("cust-1", "alice@example.com")` runs while `CustomerService.isDown` is still `false`, so the event is published normally, and `orders.onCustomerEmailChanged("cust-1", "alice@example.com")` runs, storing the email in `orders.localCustomerEmails`.
2. The first `orders.renderConfirmation("cust-1", "widget")` call reads `localCustomerEmails.getOrDefault("cust-1", ...)`, finds the stored email, and returns the confirmation message — no call to `CustomerService` occurred during this request at all.
3. `customerService.isDown = true` simulates `CustomerService` becoming completely unreachable — a real outage.
4. The second `orders.renderConfirmation("cust-1", "widget")` call runs the *exact same code path* as step 2: it reads from `localCustomerEmails`, which still holds the email stored back in step 1. `CustomerService`'s current `isDown` state is never consulted, because `renderConfirmation` never calls `CustomerService` in the first place — the request succeeds identically to before the outage.
5. The third call, `orders.renderConfirmation("cust-2", "gadget")`, looks up `"cust-2"` in `localCustomerEmails`, finds nothing (no event was ever received for this customer), and falls back to `"unknown@example.com"` via `getOrDefault`'s default value — a graceful degradation, not a crash, even for data `OrderService` never had a chance to receive.

```
BEFORE outage: CustomerService.updateEmail -> event -> OrderService.localCustomerEmails["cust-1"] = "alice@example.com"
                                                                        |
        renderConfirmation("cust-1", ...) reads LOCAL data -> succeeds

AFTER outage:  CustomerService.isDown = true (irrelevant to OrderService's request path)
        renderConfirmation("cust-1", ...) reads LOCAL data (unchanged) -> succeeds
        renderConfirmation("cust-2", ...) reads LOCAL data (never received) -> graceful fallback, still succeeds
```

## 7. Gotchas & takeaways

> **Gotcha:** the self-contained pattern trades real-time accuracy for reliability — `orders.localCustomerEmails` can be stale if `CustomerService` published an update while `OrderService` was itself down or disconnected and missed the event. This staleness window is an explicit, accepted tradeoff, not a bug, but it means the self-contained pattern is a poor fit for data where staleness of even a few seconds is genuinely unacceptable (real-time account balance for a financial transaction, for instance).

- The self-contained service pattern requires handling a request using only local data — no synchronous calls to other services during request handling — by keeping cross-service data locally, updated ahead of time via events.
- The concrete resilience payoff: another service being down or slow cannot directly break a self-contained service's ability to handle its own requests, since no synchronous call to that dependency ever happens mid-request.
- The explicit tradeoff is staleness — a locally-cached copy is only as fresh as the last event successfully processed, trading perfect real-time consistency for independence from another service's availability.
- Apply this pattern specifically to latency- and reliability-sensitive read paths where a synchronous dependency's occasional slowness or downtime would be unacceptable, not universally for every piece of cross-service data a service might need.
