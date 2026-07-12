---
card: microservices
gi: 43
slug: service-per-team
title: Service per team
---

## 1. What it is

**Service per team** is the organizational pairing rule that says each service (or small, cohesive group of services) should be owned by exactly one team — never split across multiple teams' shared ownership, and never one team owning so many services it can't reasonably operate them all well. This is [Conway's Law](0022-conway-s-law-and-its-inverse-maneuver.md) and [two-pizza team sizing](0030-team-size-organizational-readiness-two-pizza-teams.md) combined into a concrete decomposition rule: don't just draw service boundaries around business capabilities or data ownership in the abstract — draw them so that exactly one team can own each resulting service end to end.

## 2. Why & when

A service owned jointly by two teams recreates cross-team coordination for every change to that service — exactly the coordination cost splitting into services was meant to eliminate. This can happen subtly: two teams might both need to modify a shared `OrderService` for their own, unrelated features, requiring the same kind of scheduling and communication overhead a monolith would have needed for the same two features, just now wrapped in extra network calls.

Apply the service-per-team rule when finalizing a decomposition: for each candidate service boundary, ask "which single team will own this, completely, going forward?" If the honest answer involves two teams, or "whichever team gets to it first," the boundary needs to be redrawn — either split the service further along the line that separates the two teams' actual concerns, or merge it fully under one team with the other team accessing it only through its API.

## 3. Core concept

The test, applied per service: count how many teams need direct write access to a service's code to ship their own features.

- **Service per team, correctly applied:** exactly 1 team owns and modifies the code. Other teams that need something from it call its published API.
- **Violated:** 2+ teams directly modify the same service's code for their own independent features — a shared-ownership service that recreates cross-team release coordination.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A correctly-owned service has exactly one team modifying its code, with other teams calling its API; a jointly-owned service has two teams both modifying the same code, recreating coordination overhead">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Service per team</text>
  <rect x="60" y="60" width="180" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrdersService</text>
  <text x="150" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">owned by OrdersTeam only</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Jointly owned (violated)</text>
  <rect x="420" y="60" width="180" height="55" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="510" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrdersService</text>
  <text x="510" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">TeamA AND TeamB both push code</text>
</svg>

One service, exactly one owning team versus two teams sharing modification rights on the same codebase.

## 5. Runnable example

Scenario: modeling ownership as write access to a service's code, first with a joint-ownership scenario showing coordination cost, then split so each team owns its own service cleanly.

### Level 1 — Basic

```java
// File: JointOwnershipCost.java -- TWO teams both need to modify the
// SAME OrderService for their OWN, unrelated features -- coordination required.
public class JointOwnershipCost {
    static class OrderService {
        String checkout(String item) { return "checked out: " + item; } // TeamA's concern
        String applyLoyaltyPoints(String customerId, int points) { return "applied " + points + " points to " + customerId; } // TeamB's concern, SAME service
    }

    public static void main(String[] args) {
        OrderService orders = new OrderService();
        System.out.println("TeamA's feature: " + orders.checkout("widget"));
        System.out.println("TeamB's feature: " + orders.applyLoyaltyPoints("cust-1", 50));
        System.out.println("Both teams must coordinate ANY deploy of OrderService, even for unrelated changes");
    }
}
```

**How to run:** `javac JointOwnershipCost.java && java JointOwnershipCost` (JDK 17+).

Expected output:
```
TeamA's feature: checked out: widget
TeamB's feature: applied 50 points to cust-1
Both teams must coordinate ANY deploy of OrderService, even for unrelated changes
```

`checkout` (TeamA's concern) and `applyLoyaltyPoints` (TeamB's concern) both live in the same class — deploying a fix to either one requires coordinating with whichever team owns the other, since they share the same deployable unit.

### Level 2 — Intermediate

```java
// File: OneServicePerTeam.java -- split into TWO services, each owned
// by EXACTLY one team, calling each other's API instead of sharing code.
public class OneServicePerTeam {
    // owned SOLELY by OrdersTeam
    static class OrdersService {
        String checkout(String item) { return "checked out: " + item; }
    }

    // owned SOLELY by LoyaltyTeam
    static class LoyaltyService {
        String applyLoyaltyPoints(String customerId, int points) { return "applied " + points + " points to " + customerId; }
    }

    public static void main(String[] args) {
        OrdersService orders = new OrdersService();   // OrdersTeam deploys this ALONE
        LoyaltyService loyalty = new LoyaltyService(); // LoyaltyTeam deploys this ALONE

        System.out.println("OrdersTeam's feature: " + orders.checkout("widget"));
        System.out.println("LoyaltyTeam's feature: " + loyalty.applyLoyaltyPoints("cust-1", 50));
    }
}
```

**How to run:** `javac OneServicePerTeam.java && java OneServicePerTeam` (JDK 17+).

Expected output:
```
OrdersTeam's feature: checked out: widget
LoyaltyTeam's feature: applied 50 points to cust-1
```

Each service is now owned by exactly one team. `OrdersTeam` can deploy `OrdersService` any time without coordinating with `LoyaltyTeam`, and vice versa — the coordination cost from Level 1 is gone.

### Level 3 — Advanced

```java
// File: LoyaltyDependsOnOrdersApi.java -- LoyaltyTeam needs order data,
// but gets it via OrdersService's PUBLISHED API -- never by modifying
// OrdersService's code directly.
public class LoyaltyDependsOnOrdersApi {
    record OrderSummary(String orderId, double total) { } // OrdersService's PUBLISHED contract

    static class OrdersService { // owned SOLELY by OrdersTeam
        String checkout(String item, double total) { return "checked out: " + item; }
        OrderSummary getOrderSummary(String orderId) { return new OrderSummary(orderId, 9.99); } // the ONE way in
    }

    static class LoyaltyService { // owned SOLELY by LoyaltyTeam
        OrdersService orders; // depends on OrdersService's API, NEVER touches its internal code
        LoyaltyService(OrdersService orders) { this.orders = orders; }

        int calculatePointsEarned(String orderId) {
            OrderSummary summary = orders.getOrderSummary(orderId); // API call, not a code merge
            return (int) (summary.total() * 10); // LoyaltyTeam's OWN business rule, in LoyaltyTeam's OWN code
        }
    }

    public static void main(String[] args) {
        OrdersService orders = new OrdersService();
        LoyaltyService loyalty = new LoyaltyService(orders);

        orders.checkout("widget", 9.99);
        int points = loyalty.calculatePointsEarned("ord-1");
        System.out.println("Points earned: " + points + " (computed in LoyaltyService, using OrdersService's PUBLISHED API only)");
    }
}
```

**How to run:** `javac LoyaltyDependsOnOrdersApi.java && java LoyaltyDependsOnOrdersApi` (JDK 17+).

Expected output:
```
Points earned: 99 (computed in LoyaltyService, using OrdersService's PUBLISHED API only)
```

The production-flavored payoff: `LoyaltyService.calculatePointsEarned` needs order data, but it gets it through `orders.getOrderSummary(orderId)` — `OrdersService`'s published, stable API — never by adding a `points` field or a loyalty-specific method directly into `OrdersService`'s own code. `LoyaltyTeam` can change `calculatePointsEarned`'s formula freely, deploying `LoyaltyService` alone, and `OrdersTeam` never needs to be involved in that change at all.

## 6. Walkthrough

1. `orders.checkout("widget", 9.99)` runs entirely within `OrdersService`, owned solely by `OrdersTeam` — this line represents a feature `OrdersTeam` built and can deploy independently.
2. `loyalty.calculatePointsEarned("ord-1")` runs next, inside `LoyaltyService`, owned solely by `LoyaltyTeam`. It calls `orders.getOrderSummary("ord-1")` — a method call on the `OrdersService` object, but specifically one of `OrdersService`'s *published* methods, not a private field or internal implementation detail.
3. `getOrderSummary` returns an `OrderSummary(orderId, 9.99)` record — `OrdersTeam`'s stable, published contract for what order data looks like from the outside.
4. Back in `calculatePointsEarned`, `LoyaltyService`'s own code computes `summary.total() * 10 = 9.99 * 10 = 99.9`, cast to `int`, yielding `99` — this formula is entirely `LoyaltyTeam`'s own business logic, living in `LoyaltyTeam`'s own service, never touching `OrdersService`'s source code.
5. If `LoyaltyTeam` later changes the points formula to `total * 20`, that change happens entirely inside `LoyaltyService` — `OrdersService`'s code, and `OrdersTeam`'s deploy schedule, are completely unaffected, exactly matching the service-per-team rule's goal.

```
OrdersTeam owns:   OrdersService (checkout, getOrderSummary)       <- OrdersTeam's code, OrdersTeam's deploys
LoyaltyTeam owns:  LoyaltyService (calculatePointsEarned)          <- LoyaltyTeam's code, LoyaltyTeam's deploys
        |
LoyaltyService depends on OrdersService's PUBLISHED API (getOrderSummary), never its internal code
```

## 7. Gotchas & takeaways

> **Gotcha:** service-per-team doesn't mean "exactly one service per team" — a team can, and often should, own several small, related services (see [service granularity](0019-service-granularity-nano-micro-macro-mini-services.md)), as long as that team has the capacity to genuinely operate all of them well (see [two-pizza team sizing](0030-team-size-organizational-readiness-two-pizza-teams.md)). The rule is specifically about avoiding *shared* ownership of any single service across multiple teams, not about capping each team at one service.

- Service per team means every service has exactly one team with direct write access to its code — other teams that need something from it call its published API instead.
- Joint ownership of a service by two teams recreates the cross-team coordination cost splitting into services was meant to eliminate, just now with added network overhead on top.
- The test for a correctly-drawn boundary: does this service have exactly one team that could deploy a change to it, right now, without needing another team's involvement?
- When one team genuinely needs data or behavior another team's service owns, the dependency should flow through that service's published API — never through direct, shared modification of its underlying code.
