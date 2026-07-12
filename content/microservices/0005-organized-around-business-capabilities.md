---
card: microservices
gi: 5
slug: organized-around-business-capabilities
title: Organized around business capabilities
---

## 1. What it is

**Organized around business capabilities** is the Lewis & Fowler characteristic that says services should be split along the lines of what the business *does* — orders, payments, shipping — rather than along technical layers like "the UI team," "the business-logic team," and "the database team." Each service becomes a vertical slice: it owns its own presentation logic, business rules, and data for one capability, end to end. A cross-cutting change to one business concern (say, "how we calculate order totals") should touch exactly one service, not require coordinated changes across a UI team, a middleware team, and a DBA team.

## 2. Why & when

Technical-layer organization feels natural because it mirrors how software is technically structured — controllers, services, repositories — but it has a costly side effect: any single business feature cuts horizontally across every layer team. Adding a "returns" feature might need a new controller (UI team), new business logic (services team), and new tables (DB team), all coordinated and released together, even though the feature is conceptually one cohesive thing. Business-capability organization keeps that whole vertical slice inside one team and one service, so most feature work stays contained.

Adopt this once you can name your system's real business capabilities distinctly enough to draw service boundaries around them — orders, inventory, payments are commonly distinct capabilities in an e-commerce system. If your "capabilities" are still vague or highly interdependent, splitting prematurely along the wrong lines creates services that constantly need each other's internals, which is worse than a well-organized monolith.

## 3. Core concept

Two ways to draw the same feature's boundaries:

- **Layered organization:** one `OrderController`, one `PaymentController` — but both are methods on a single shared `Controller` layer class, alongside a single shared `Service` layer and a single shared `Repository` layer. Adding a business capability means touching all three shared layers.
- **Capability organization:** one `OrdersService` and one `PaymentsService`, each internally containing its own mini presentation/logic/data layers. Adding a business capability means adding a brand-new, self-contained unit — touching nothing that already exists.

The test: when a new business capability is added, does it require editing existing shared classes, or does it arrive as new, isolated code?

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Layered organization cuts horizontally across shared Controller, Service and Repository classes; capability organization cuts vertically into self-contained Orders and Payments services">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Layered (horizontal)</text>
  <rect x="30" y="35" width="240" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Controller (Orders + Payments methods)</text>
  <rect x="30" y="75" width="240" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service (Orders + Payments methods)</text>
  <rect x="30" y="115" width="240" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="135" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Repository (Orders + Payments methods)</text>

  <text x="480" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Capability (vertical)</text>
  <rect x="360" y="35" width="110" height="110" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="415" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrdersService</text>
  <text x="415" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">own logic + own data</text>

  <rect x="490" y="35" width="130" height="110" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">PaymentsService</text>
  <text x="555" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">own logic + own data</text>
</svg>

Layered code cuts across every feature; capability-organized code keeps each feature self-contained.

## 5. Runnable example

Scenario: adding a brand-new "Returns" capability to a system, first in a layered design (touching every shared layer), then in a capability-organized design (arriving as isolated new code).

### Level 1 — Basic

```java
// File: LayeredSystem.java -- shared Controller/Service/Repository layers,
// each handling MULTIPLE business capabilities together.
import java.util.*;

public class LayeredSystem {
    static class Controller {
        Service service;
        Controller(Service service) { this.service = service; }
        String handleOrder(String item) { return service.placeOrder(item); }
        String handlePayment(double amount) { return service.charge(amount); }
    }

    static class Service {
        Repository repo;
        Service(Repository repo) { this.repo = repo; }
        String placeOrder(String item) { repo.saveOrder(item); return "order placed: " + item; }
        String charge(double amount) { repo.saveCharge(amount); return "charged: $" + amount; }
    }

    static class Repository {
        List<String> orders = new ArrayList<>();
        List<Double> charges = new ArrayList<>();
        void saveOrder(String item) { orders.add(item); }
        void saveCharge(double amount) { charges.add(amount); }
    }

    public static void main(String[] args) {
        Controller controller = new Controller(new Service(new Repository()));
        System.out.println(controller.handleOrder("widget"));
        System.out.println(controller.handlePayment(9.99));
    }
}
```

**How to run:** `javac LayeredSystem.java && java LayeredSystem` (JDK 17+).

Expected output:
```
order placed: widget
charged: $9.99
```

`Controller`, `Service`, and `Repository` each already handle two unrelated business concepts side by side. Adding "Returns" as a third capability means adding a method to all three shared classes.

### Level 2 — Intermediate

```java
// File: CapabilitySystem.java -- Orders and Payments as SELF-CONTAINED
// capability services, each with its own internal mini-layers.
public class CapabilitySystem {
    static class OrdersService {
        java.util.List<String> orders = new java.util.ArrayList<>();
        String placeOrder(String item) { orders.add(item); return "order placed: " + item; }
    }

    static class PaymentsService {
        java.util.List<Double> charges = new java.util.ArrayList<>();
        String charge(double amount) { charges.add(amount); return "charged: $" + amount; }
    }

    public static void main(String[] args) {
        OrdersService orders = new OrdersService();
        PaymentsService payments = new PaymentsService();
        System.out.println(orders.placeOrder("widget"));
        System.out.println(payments.charge(9.99));
    }
}
```

**How to run:** `javac CapabilitySystem.java && java CapabilitySystem` (JDK 17+).

Expected output:
```
order placed: widget
charged: $9.99
```

`OrdersService` and `PaymentsService` are now fully independent units; neither references the other, and neither is a shared, multi-purpose class. Each is a complete vertical slice for its one business capability.

### Level 3 — Advanced

```java
// File: CapabilitySystemNewFeature.java -- add "Returns" as a BRAND-NEW
// capability, touching zero existing code, only adding new code.
public class CapabilitySystemNewFeature {
    static class OrdersService { // UNCHANGED from Level 2
        java.util.List<String> orders = new java.util.ArrayList<>();
        String placeOrder(String item) { orders.add(item); return "order placed: " + item; }
    }

    static class PaymentsService { // UNCHANGED from Level 2
        java.util.List<Double> charges = new java.util.ArrayList<>();
        String charge(double amount) { charges.add(amount); return "charged: $" + amount; }
    }

    // NEW capability: its own class, own data, own logic -- nothing above was touched to add it
    static class ReturnsService {
        java.util.List<String> returns = new java.util.ArrayList<>();
        String processReturn(String item) { returns.add(item); return "return processed: " + item; }
    }

    public static void main(String[] args) {
        OrdersService orders = new OrdersService();
        PaymentsService payments = new PaymentsService();
        ReturnsService returnsSvc = new ReturnsService();

        System.out.println(orders.placeOrder("widget"));
        System.out.println(payments.charge(9.99));
        System.out.println(returnsSvc.processReturn("widget")); // brand-new capability, isolated
        System.out.println("orders capability untouched: " + orders.orders);
        System.out.println("payments capability untouched: " + payments.charges);
    }
}
```

**How to run:** `javac CapabilitySystemNewFeature.java && java CapabilitySystemNewFeature` (JDK 17+).

Expected output:
```
order placed: widget
charged: $9.99
return processed: widget
orders capability untouched: [widget]
payments capability untouched: [9.99]
```

The production-flavored proof point: `ReturnsService` is entirely new code. `OrdersService` and `PaymentsService` above it are byte-for-byte identical to Level 2 — no shared "Controller" or "Repository" class needed a new method added to accommodate returns, because there was never a shared layer to touch in the first place.

## 6. Walkthrough

1. `OrdersService orders = new OrdersService();` and `PaymentsService payments = new PaymentsService();` construct two independent capability units, each carrying only its own data (`orders` list, `charges` list).
2. `ReturnsService returnsSvc = new ReturnsService();` constructs a third, completely new unit — its constructor doesn't reference `OrdersService` or `PaymentsService` at all, and neither of those classes' source code changed to make room for it.
3. `orders.placeOrder("widget")` runs first, mutating only `OrdersService`'s own internal `orders` list.
4. `payments.charge(9.99)` runs next, mutating only `PaymentsService`'s own internal `charges` list — a completely separate piece of state.
5. `returnsSvc.processReturn("widget")` runs the new capability's logic, mutating only its own new `returns` list.
6. The final two prints confirm `orders.orders` and `payments.charges` are exactly as they were before `ReturnsService` was introduced — proof that adding a business capability was purely additive, not a modification of existing shared code.

```
Layered add-a-feature:     edit Controller + edit Service + edit Repository  (3 shared files touched)
Capability add-a-feature:  add ReturnsService.java                          (0 existing files touched)
```

## 7. Gotchas & takeaways

> **Gotcha:** business-capability boundaries only pay off if they're drawn around genuinely distinct capabilities. Splitting "create order" and "update order" into two different services, when they always change together and constantly need each other's internal state, creates the coordination cost of microservices without the isolation benefit — that's a sign the boundary was drawn in the wrong place, not that capability-based organization itself failed.

- Organizing around business capabilities means each service is a full vertical slice — its own presentation, logic, and data for one thing the business does — instead of one layer among several shared, cross-cutting layers.
- The concrete test: does adding a new business capability require editing existing shared code, or does it arrive as new, isolated code?
- This characteristic is what makes a team's ownership boundary match a service's technical boundary — a prerequisite for the "you build it, you run it" ownership model.
- Don't split along technical layers (UI/logic/data) across services — that just relocates a monolith's tight coupling onto the network, adding latency without adding independence.
