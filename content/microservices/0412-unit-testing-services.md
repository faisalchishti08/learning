---
card: microservices
gi: 412
slug: unit-testing-services
title: "Unit testing services"
---

## 1. What it is

A **unit test** exercises the smallest meaningful piece of behavior in isolation — typically one class or one method — with every collaborator it depends on replaced by a **test double** (a fake, stub, or mock) instead of the real thing. No network call, no database, no message broker, and no other service is involved. In a microservices codebase, unit tests form the base of the [test pyramid](0411-test-pyramid-for-microservices.md): they're what most of your tests should be, because they run in milliseconds and, when they fail, point at exactly the line of logic that broke.

## 2. Why & when

You write a unit test any time you add or change business logic that can be expressed as "given this input, produce this output" or "given this state, perform this action" — which is most of the code inside a service. The value comes from three properties working together:

- **Speed.** Thousands of unit tests can run in seconds because nothing touches the network, disk, or a container. That speed is what makes a "run tests before every commit" habit realistic.
- **Precision.** When a unit test fails, you already know which class and which method is wrong — there's no chain of services to dig through, unlike a failing [end-to-end test](0417-end-to-end-testing-its-fragility.md).
- **Determinism.** With every collaborator faked, there's no flaky network call, no race condition, and no shared test database to cause a test to fail for reasons unrelated to the code under test.

You reach for a unit test whenever logic is worth naming — a pricing rule, a validation rule, a state transition — and you reach for a *different* kind of test (integration, component) specifically when what you need to verify is how the service talks to something outside itself, such as its own database (see [integration testing](0413-integration-testing-service-its-db-broker.md)). Trying to verify database behavior with a unit test that mocks the repository proves nothing about whether the real query works; trying to verify a pricing rule with an integration test wastes the speed a unit test would have given you for free.

## 3. Core concept

Picture testing a single gear from a large machine. A unit test takes that one gear off the machine entirely, turns it by hand, and checks that it rotates the way it's supposed to — you don't need the whole machine running, or even assembled, to know the gear itself is correctly shaped. A test double stands in for the *next* gear the one under test would normally mesh with, so you can turn the test gear in isolation and observe exactly what it does, without needing that next gear to be real or working.

Concretely, a unit test has three parts, often called **Arrange, Act, Assert**:

1. **Arrange** — construct the object under test and its test doubles, and set up the input.
2. **Act** — call the one method being tested.
3. **Assert** — check the result matches what's expected, and optionally verify the test double was called the way you expect.

Test doubles come in a few flavors that matter to get right:

| Kind | What it does | When to use it |
|---|---|---|
| **Stub** | Returns a canned answer when called | The collaborator's output matters, not how it was called |
| **Mock** | Records how it was called so the test can assert on it | You need to verify an interaction happened (e.g. "payment was charged exactly once") |
| **Fake** | A lightweight working implementation (e.g. an in-memory map instead of a real database) | You need realistic-ish behavior without the real infrastructure |

The discipline that keeps unit tests fast and precise is **isolation**: the object under test should never reach past its own boundary — no real HTTP call, no real database connection, no real clock (`System.currentTimeMillis()` should be injected, not called directly) — because any of those turns a millisecond-fast, always-deterministic test into a slow, sometimes-flaky one.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A unit test isolates one class, replacing its collaborators such as a repository or payment client with test doubles, so the test exercises only the logic inside the class under test">
  <text x="320" y="24" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Unit test boundary</text>
  <rect x="230" y="50" width="180" height="80" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="85" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OrderValidator</text>
  <text x="320" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">class under test</text>

  <rect x="40" y="60" width="130" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-dasharray="4,2"/>
  <text x="105" y="84" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">FakeInventoryClient</text>
  <rect x="40" y="115" width="130" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-dasharray="4,2"/>
  <text x="105" y="139" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">StubPricingRules</text>

  <rect x="470" y="60" width="140" height="40" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="540" y="78" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">real database</text>
  <text x="540" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">NOT reached</text>
  <rect x="470" y="115" width="140" height="40" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="540" y="133" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">real network</text>
  <text x="540" y="147" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">NOT reached</text>

  <line x1="170" y1="80" x2="230" y2="80" stroke="#79c0ff"/>
  <line x1="170" y1="135" x2="230" y2="100" stroke="#79c0ff"/>
  <line x1="410" y1="80" x2="470" y2="80" stroke="#f85149" stroke-dasharray="2,3"/>
  <text x="440" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">test doubles stand in on the left; real infrastructure on the right is never touched</text>
</svg>

A unit test wires the class under test to lightweight test doubles instead of real collaborators, keeping the test fast, deterministic, and focused on one piece of logic.

## 5. Runnable example

Scenario: an `OrderValidator` that decides whether an order can proceed, based on inventory availability and pricing. We test it first with a hand-rolled fake collaborator, then add a mock that records how it was called, then test a harder rule that depends on multiple collaborators interacting.

### Level 1 — Basic

```java
// File: OrderValidatorBasicTest.java -- a unit test using a hand-rolled
// FAKE collaborator (an in-memory stand-in for a real inventory service),
// with no network, no database, and no other service involved.
import java.util.*;

public class OrderValidatorBasicTest {
    interface InventoryClient {
        boolean isInStock(String sku);
    }

    // The class under test: pure logic, one dependency injected via constructor.
    static class OrderValidator {
        private final InventoryClient inventory;
        OrderValidator(InventoryClient inventory) { this.inventory = inventory; }
        boolean canPlaceOrder(String sku, int quantity) {
            if (quantity <= 0) return false;
            return inventory.isInStock(sku);
        }
    }

    // A FAKE: a lightweight, fully working implementation backed by a Set,
    // instead of a real network call to an inventory service.
    static class FakeInventoryClient implements InventoryClient {
        private final Set<String> inStockSkus;
        FakeInventoryClient(Set<String> inStockSkus) { this.inStockSkus = inStockSkus; }
        public boolean isInStock(String sku) { return inStockSkus.contains(sku); }
    }

    static void assertTrue(String label, boolean condition) {
        System.out.println((condition ? "PASS" : "FAIL") + ": " + label);
    }

    public static void main(String[] args) {
        OrderValidator validator = new OrderValidator(new FakeInventoryClient(Set.of("sku-1", "sku-2")));

        assertTrue("in-stock sku with positive quantity is allowed", validator.canPlaceOrder("sku-1", 3));
        assertTrue("out-of-stock sku is rejected", !validator.canPlaceOrder("sku-99", 1));
        assertTrue("zero quantity is rejected regardless of stock", !validator.canPlaceOrder("sku-1", 0));
    }
}
```

How to run: `java OrderValidatorBasicTest.java`

`OrderValidator` depends on the `InventoryClient` interface, not a concrete implementation — the key design choice that makes unit testing possible at all. `FakeInventoryClient` implements that interface with nothing but a `Set`, so the test runs entirely in memory: no real inventory service is ever contacted. Each `assertTrue` call arranges an input, acts by calling `canPlaceOrder`, and asserts the result, all in microseconds.

### Level 2 — Intermediate

```java
// File: OrderValidatorMockTest.java -- the SAME validator, now with a
// hand-rolled MOCK that records how it was called, so the test can verify
// an interaction (e.g. "inventory was checked exactly once per call")
// in addition to checking the return value.
import java.util.*;

public class OrderValidatorMockTest {
    interface InventoryClient {
        boolean isInStock(String sku);
    }

    static class OrderValidator {
        private final InventoryClient inventory;
        OrderValidator(InventoryClient inventory) { this.inventory = inventory; }
        boolean canPlaceOrder(String sku, int quantity) {
            if (quantity <= 0) return false; // short-circuits BEFORE touching inventory
            return inventory.isInStock(sku);
        }
    }

    // A MOCK: like the fake, but also records every call it received.
    static class MockInventoryClient implements InventoryClient {
        private final Set<String> inStockSkus;
        final List<String> callsReceived = new ArrayList<>();
        MockInventoryClient(Set<String> inStockSkus) { this.inStockSkus = inStockSkus; }
        public boolean isInStock(String sku) {
            callsReceived.add(sku);
            return inStockSkus.contains(sku);
        }
    }

    static void assertTrue(String label, boolean condition) {
        System.out.println((condition ? "PASS" : "FAIL") + ": " + label);
    }

    public static void main(String[] args) {
        MockInventoryClient mockInventory = new MockInventoryClient(Set.of("sku-1"));
        OrderValidator validator = new OrderValidator(mockInventory);

        validator.canPlaceOrder("sku-1", 2);
        assertTrue("inventory WAS checked for a valid quantity", mockInventory.callsReceived.equals(List.of("sku-1")));

        validator.canPlaceOrder("sku-1", 0); // invalid quantity: should short-circuit
        assertTrue("inventory was NOT checked again for an invalid quantity (still only 1 call)",
                mockInventory.callsReceived.size() == 1);
    }
}
```

How to run: `java OrderValidatorMockTest.java`

`MockInventoryClient` adds one thing a plain fake doesn't have: a `callsReceived` log. The first assertion checks not just the return value but that `isInStock` was actually invoked with `"sku-1"` — proving the validator really consulted inventory rather than, say, always returning `true`. The second assertion is the more interesting one: after calling `canPlaceOrder` with an invalid quantity, `callsReceived` still has only one entry, proving the `quantity <= 0` short-circuit genuinely skips the inventory check rather than calling it and ignoring the result. A fake alone couldn't have caught a bug where that short-circuit was accidentally removed but the logic still happened to return the right boolean.

### Level 3 — Advanced

```java
// File: OrderValidatorDiscountRuleTest.java -- the SAME validator, now with
// a harder, production-flavored rule: a bulk-order discount that depends on
// TWO collaborators (inventory AND pricing) interacting, plus an edge case
// where pricing throws for an unknown sku -- verifying the validator
// handles a failing collaborator without crashing the whole check.
import java.util.*;

public class OrderValidatorDiscountRuleTest {
    interface InventoryClient { boolean isInStock(String sku); }
    interface PricingClient { double unitPrice(String sku); } // throws IllegalArgumentException for unknown sku

    record OrderDecision(boolean allowed, double totalPrice, String reason) {}

    static class OrderValidator {
        private final InventoryClient inventory;
        private final PricingClient pricing;
        OrderValidator(InventoryClient inventory, PricingClient pricing) {
            this.inventory = inventory; this.pricing = pricing;
        }

        OrderDecision evaluate(String sku, int quantity) {
            if (quantity <= 0) return new OrderDecision(false, 0, "invalid quantity");
            if (!inventory.isInStock(sku)) return new OrderDecision(false, 0, "out of stock");

            double unitPrice;
            try {
                unitPrice = pricing.unitPrice(sku);
            } catch (IllegalArgumentException e) {
                return new OrderDecision(false, 0, "pricing unavailable for " + sku);
            }

            double total = unitPrice * quantity;
            if (quantity >= 10) total *= 0.9; // 10% bulk discount at 10+ units
            return new OrderDecision(true, total, "ok");
        }
    }

    static class FakeInventoryClient implements InventoryClient {
        private final Set<String> inStock;
        FakeInventoryClient(Set<String> inStock) { this.inStock = inStock; }
        public boolean isInStock(String sku) { return inStock.contains(sku); }
    }

    static class StubPricingClient implements PricingClient {
        private final Map<String, Double> prices;
        StubPricingClient(Map<String, Double> prices) { this.prices = prices; }
        public double unitPrice(String sku) {
            Double p = prices.get(sku);
            if (p == null) throw new IllegalArgumentException("no price for " + sku);
            return p;
        }
    }

    static void assertTrue(String label, boolean condition) {
        System.out.println((condition ? "PASS" : "FAIL") + ": " + label);
    }

    public static void main(String[] args) {
        InventoryClient inventory = new FakeInventoryClient(Set.of("sku-1", "sku-2"));
        PricingClient pricing = new StubPricingClient(Map.of("sku-1", 20.0));
        OrderValidator validator = new OrderValidator(inventory, pricing);

        OrderDecision small = validator.evaluate("sku-1", 5);
        assertTrue("5 units at $20 = $100, no discount", small.allowed() && small.totalPrice() == 100.0);

        OrderDecision bulk = validator.evaluate("sku-1", 10);
        assertTrue("10 units at $20 with 10% bulk discount = $180", bulk.allowed() && bulk.totalPrice() == 180.0);

        // sku-2 is in stock but StubPricingClient has no price for it -- exercises the failure path.
        OrderDecision missingPrice = validator.evaluate("sku-2", 3);
        assertTrue("missing price is handled gracefully, not thrown", !missingPrice.allowed()
                && missingPrice.reason().equals("pricing unavailable for sku-2"));
    }
}
```

How to run: `java OrderValidatorDiscountRuleTest.java`

This version tests a rule that genuinely needs two collaborators to interact correctly: `evaluate` must check inventory *and* pricing, apply a bulk discount only above a threshold, and — the hard case — degrade gracefully if `pricing.unitPrice` throws for a sku that has no price configured, rather than letting the exception propagate and crash the whole order flow. `StubPricingClient` is deliberately built to throw for unmapped skus, so `missingPrice` exercises a real failure mode of a real collaborator, entirely without a network call. This is exactly the kind of edge case a unit test is best positioned to catch cheaply — reproducing "the pricing service returned an unexpected error for one specific sku" against a *real* pricing service would be slow and unreliable by comparison.

## 6. Walkthrough

Trace `OrderValidatorDiscountRuleTest.main` in order. **First**, `validator.evaluate("sku-1", 5)` runs. `quantity` (5) is positive, so the first guard passes. `inventory.isInStock("sku-1")` returns `true` from the fake's `Set`. `pricing.unitPrice("sku-1")` returns `20.0` from the stub's `Map`. `total` becomes `20.0 * 5 = 100.0`; since `quantity` (5) is below the discount threshold of 10, no discount applies, and `evaluate` returns `OrderDecision(allowed=true, totalPrice=100.0, reason="ok")`.

**Next**, `validator.evaluate("sku-1", 10)` runs the same path, but `quantity` is now 10, so `total *= 0.9` fires: `20.0 * 10 = 200.0`, then `200.0 * 0.9 = 180.0`. The decision is `OrderDecision(allowed=true, totalPrice=180.0, reason="ok")`.

**Then**, `validator.evaluate("sku-2", 3)` runs. `quantity` (3) passes the first guard. `inventory.isInStock("sku-2")` returns `true` — sku-2 *is* in stock. But `pricing.unitPrice("sku-2")` looks up `"sku-2"` in `StubPricingClient`'s map, finds nothing, and throws `IllegalArgumentException("no price for sku-2")`. The `catch` block inside `evaluate` intercepts that exception and returns `OrderDecision(allowed=false, totalPrice=0, reason="pricing unavailable for sku-2")` instead of letting the exception escape — this is the behavior under test.

**Finally**, all three `assertTrue` calls print, confirming the plain case, the discount case, and the failure-handling case all behave as designed.

```
PASS: 5 units at $20 = $100, no discount
PASS: 10 units at $20 with 10% bulk discount = $180
PASS: missing price is handled gracefully, not thrown
```

## 7. Gotchas & takeaways

> A unit test that mocks so many collaborators the test ends up asserting "the mock was called with the exact arguments I told it to expect" has stopped testing behavior and started testing the mock itself. If a test would still pass after you delete the method body and replace it with `return null`, it isn't testing anything real — favor asserting on outcomes (return values, state changes) over asserting on call sequences wherever the outcome alone is enough.

- Keep unit tests isolated: no real network, database, clock, or filesystem access — anything that crosses the process boundary belongs in an [integration test](0413-integration-testing-service-its-db-broker.md) instead.
- Depend on interfaces, not concrete classes, for anything you'll want to fake or mock — `OrderValidator` above is testable specifically because it takes `InventoryClient` and `PricingClient` as constructor parameters rather than constructing them itself.
- Use a fake when you need realistic-ish behavior (an in-memory collection standing in for a store); use a mock when you specifically need to verify an interaction happened, not just its result.
- Unit tests are the base of the [test pyramid](0411-test-pyramid-for-microservices.md) — they should vastly outnumber every other layer, because they're the cheapest tests you'll ever write.
- A passing unit-test suite proves your logic is correct in isolation; it says nothing about whether your service's real database queries, real HTTP clients, or real message consumers actually work — that's what [integration testing](0413-integration-testing-service-its-db-broker.md) and [component testing](0414-component-testing-single-service-in-isolation.md) are for.
