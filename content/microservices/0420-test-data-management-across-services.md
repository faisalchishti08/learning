---
card: microservices
gi: 420
slug: test-data-management-across-services
title: "Test data management across services"
---

## 1. What it is

**Test data management** is the discipline of creating, isolating, and cleaning up the data a test needs — rows in a database, messages on a topic, cached entries — so that tests are repeatable, independent of each other, and independent of whatever data happens to already exist. In a single-service, single-database world this is mostly a matter of resetting one table between tests. In microservices, it becomes genuinely harder: a realistic test scenario (a customer with an order, a payment record, and a shipment) often spans data owned by *several different services*, each with its own database that no other service is allowed to touch directly — so "set up test data" has to happen through each service's own API, not through a shared SQL script.

## 2. Why & when

You need a deliberate test data strategy the moment more than one test can run against the same environment, or more than one service owns a piece of the data a scenario needs — which is essentially always, past the smallest toy system.

- **Shared state is the single largest cause of flaky tests.** If test A creates a customer with a specific email and test B assumes that email doesn't exist yet, whichever test runs second fails — not because of a bug, but because of test *order*. This compounds badly in CI, where tests often run in parallel.
- **Cross-service scenarios need cross-service setup.** A [component test](0414-component-testing-single-service-in-isolation.md) or [end-to-end test](0417-end-to-end-testing-its-fragility.md) that needs "a customer who already has 3 past orders" has to create that state through `OrderService`'s own API (or a dedicated test-data API), because `OrderService`'s database is private — reaching directly into another service's schema breaks the same encapsulation that made splitting into services worthwhile in the first place.
- **Data ownership boundaries mean no single "reset everything" script works globally.** Each service is responsible for its own data's lifecycle in tests, which means test data strategy has to be designed *per service* and then composed for cross-service scenarios, not centralized.
- **Production-like data shapes catch bugs synthetic data misses**, but production data itself usually can't be copied into test environments wholesale because of privacy and compliance — which is why synthetic data generation and careful data anonymization matter as much as data creation mechanics.

You reach for a deliberate strategy any time your test suite grows past a handful of tests sharing one environment, and especially the moment you write your first test that needs data spanning more than one service.

## 3. Core concept

Picture a big shared kitchen where several independent food trucks each keep their own locked pantry, but sometimes need to prepare a dish together (a food truck festival's combo platter). Each truck is responsible for its own ingredients — nobody else is allowed to open another truck's pantry directly — but when a combo platter needs ingredients from three trucks, someone has to coordinate: each truck contributes its part through its own counter window, not by letting an outsider rummage through its fridge.

Four practical strategies address the different facets of the problem:

1. **Isolation per test** — the safest and most reliable approach: each test creates exactly the data it needs, with unique identifiers (a random or test-run-scoped suffix), and doesn't depend on any data another test created. This is slower to write per test but eliminates almost all order-dependent flakiness.
2. **Cleanup after each test** — for tests that must share infrastructure (like a Testcontainers database reused across a test class for speed), explicit teardown — deleting or rolling back what the test created — keeps state from leaking into the next test.
3. **Test-data builder APIs / fixtures** — reusable helper code (`aCustomerWith(...).havingOrders(3).build()`) that hides the mechanics of creating cross-service state behind a readable, composable interface, often calling each owning service's real API under the hood.
4. **Synthetic data generation** — for realistic-scale or realistic-shape data (thousands of orders, varied edge cases), generate data programmatically rather than hand-writing every row, and never copy real production data into test environments without proper anonymization, for both privacy and compliance reasons.

The unifying principle across all four is **respecting ownership**: a test for `ShippingService` that needs an existing order should call `OrderService`'s API to create it (or use a fixture that does), not insert directly into `OrderService`'s database — doing the latter couples the test to internal schema details that are supposed to be private, and the coupling breaks the moment `OrderService`'s schema changes even though its API contract didn't.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A cross-service test scenario is set up by calling each owning service's own API to create its piece of the data, rather than reaching directly into another service's private database" font-family="sans-serif">
  <text x="320" y="20" fill="#e6edf3" font-size="12" text-anchor="middle">Setting up "a customer with a shipped order"</text>

  <rect x="30" y="50" width="150" height="60" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="105" y="75" fill="#e6edf3" font-size="10" text-anchor="middle">CustomerService</text>
  <text x="105" y="92" fill="#8b949e" font-size="9" text-anchor="middle">own DB</text>

  <rect x="245" y="50" width="150" height="60" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="75" fill="#e6edf3" font-size="10" text-anchor="middle">OrderService</text>
  <text x="320" y="92" fill="#8b949e" font-size="9" text-anchor="middle">own DB</text>

  <rect x="460" y="50" width="150" height="60" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="535" y="75" fill="#e6edf3" font-size="10" text-anchor="middle">ShippingService</text>
  <text x="535" y="92" fill="#8b949e" font-size="9" text-anchor="middle">own DB</text>

  <rect x="200" y="150" width="240" height="45" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="177" fill="#79c0ff" font-size="10" text-anchor="middle">test fixture: calls each service's own API</text>

  <line x1="320" y1="150" x2="105" y2="110" stroke="#79c0ff" stroke-dasharray="3,2"/>
  <line x1="320" y1="150" x2="320" y2="110" stroke="#79c0ff" stroke-dasharray="3,2"/>
  <line x1="320" y1="150" x2="535" y2="110" stroke="#79c0ff" stroke-dasharray="3,2"/>

  <line x1="150" y1="205" x2="490" y2="205" stroke="#f85149" stroke-dasharray="2,4"/>
  <text x="320" y="222" fill="#f85149" font-size="9" text-anchor="middle">never: reaching directly into another service's database</text>
</svg>

A test fixture composes cross-service state by calling each owning service's own API, never by reaching directly into another service's private database.

## 5. Runnable example

Scenario: a component test needs "a customer with an existing order" — data owned by two different services. We build a fixture that respects ownership, then add per-test isolation with unique identifiers, then add explicit cleanup and a harder case: a fixture failing partway through, needing to unwind what it already created.

### Level 1 — Basic

```java
// File: TestDataFixtureBasic.java -- a test-data fixture that sets up
// CROSS-SERVICE state by calling each owning service's OWN API, never by
// reaching directly into another service's data.
import java.util.*;

public class TestDataFixtureBasic {
    record Customer(String id, String email) {}
    record Order(String id, String customerId, double total) {}

    // Each service owns and exposes its own data through its own API --
    // exactly like a real service would, just simplified to in-memory maps here.
    static class CustomerService {
        private final Map<String, Customer> customers = new HashMap<>();
        Customer createCustomer(String email) {
            String id = "cust-" + (customers.size() + 1);
            Customer c = new Customer(id, email);
            customers.put(id, c);
            System.out.println("[CustomerService] created " + c);
            return c;
        }
    }

    static class OrderService {
        private final Map<String, Order> orders = new HashMap<>();
        Order createOrder(String customerId, double total) {
            String id = "order-" + (orders.size() + 1);
            Order o = new Order(id, customerId, total);
            orders.put(id, o);
            System.out.println("[OrderService] created " + o);
            return o;
        }
    }

    // A FIXTURE that composes both services' APIs to build a realistic scenario.
    static Order aCustomerWithAnOrder(CustomerService customerService, OrderService orderService, String email, double orderTotal) {
        Customer customer = customerService.createCustomer(email);
        return orderService.createOrder(customer.id(), orderTotal);
    }

    public static void main(String[] args) {
        CustomerService customerService = new CustomerService();
        OrderService orderService = new OrderService();

        Order order = aCustomerWithAnOrder(customerService, orderService, "alice@example.com", 79.99);
        System.out.println("Fixture ready: order " + order.id() + " for customer " + order.customerId());
    }
}
```

How to run: `java TestDataFixtureBasic.java`

`aCustomerWithAnOrder` composes two separate services' own APIs — `CustomerService.createCustomer` and `OrderService.createOrder` — to build a realistic cross-service scenario, exactly like a real fixture would call two real services' real HTTP APIs. Neither service ever reaches into the other's internal storage; `OrderService` only knows the customer's `id`, which is exactly the level of coupling a real order-to-customer relationship should have.

### Level 2 — Intermediate

```java
// File: TestDataFixtureIsolated.java -- the SAME fixture, now with PER-TEST
// ISOLATION: every call generates unique identifiers so that running the
// SAME fixture twice (simulating two different tests, or a test rerun)
// never collides, unlike hardcoded ids/emails would.
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class TestDataFixtureIsolated {
    record Customer(String id, String email) {}
    record Order(String id, String customerId, double total) {}

    static final AtomicInteger testRunCounter = new AtomicInteger(0);

    static class CustomerService {
        private final Map<String, Customer> customers = new HashMap<>();
        Customer createCustomer(String email) {
            if (customers.values().stream().anyMatch(c -> c.email().equals(email))) {
                throw new IllegalStateException("email already in use: " + email); // simulates a real unique-email constraint
            }
            String id = "cust-" + (customers.size() + 1);
            Customer c = new Customer(id, email);
            customers.put(id, c);
            return c;
        }
    }

    static class OrderService {
        private final Map<String, Order> orders = new HashMap<>();
        Order createOrder(String customerId, double total) {
            String id = "order-" + (orders.size() + 1);
            Order o = new Order(id, customerId, total);
            orders.put(id, o);
            return o;
        }
    }

    // ISOLATED fixture: generates a unique email per invocation, so no two
    // "tests" collide even if they run back to back against the same services.
    static Order aCustomerWithAnOrder(CustomerService customerService, OrderService orderService, double orderTotal) {
        int testId = testRunCounter.incrementAndGet();
        String uniqueEmail = "test-user-" + testId + "-" + System.nanoTime() + "@example.com";
        Customer customer = customerService.createCustomer(uniqueEmail);
        return orderService.createOrder(customer.id(), orderTotal);
    }

    public static void main(String[] args) {
        CustomerService customerService = new CustomerService();
        OrderService orderService = new OrderService();

        // Simulate TWO separate test runs against the SAME shared service instances --
        // without unique identifiers, the second createCustomer call would collide.
        Order firstTestOrder = aCustomerWithAnOrder(customerService, orderService, 40.00);
        Order secondTestOrder = aCustomerWithAnOrder(customerService, orderService, 60.00);

        System.out.println("First test's order: " + firstTestOrder.id() + " (customer " + firstTestOrder.customerId() + ")");
        System.out.println("Second test's order: " + secondTestOrder.id() + " (customer " + secondTestOrder.customerId() + ")");
        System.out.println("No collision because each fixture call used a unique email.");
    }
}
```

How to run: `java TestDataFixtureIsolated.java`

`CustomerService.createCustomer` now enforces a unique-email constraint, mirroring a real database's unique index — and the fixture generates a fresh email (`"test-user-" + testId + "-" + System.nanoTime()`) on every call specifically so that constraint never trips between independent test runs sharing the same service instances. Running the fixture twice back-to-back, simulating two different tests (or a flaky rerun of the same test), succeeds cleanly for both, which would not be true if the fixture had used a hardcoded email like `"test@example.com"` for every call.

### Level 3 — Advanced

```java
// File: TestDataFixtureCleanupOnFailure.java -- the SAME isolated fixture,
// now handling the PRODUCTION-FLAVORED hard case: the fixture creates a
// customer successfully, but the order-creation step fails partway through
// -- the fixture must UNWIND (delete) the customer it already created,
// rather than leaking orphaned test data into the shared environment.
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class TestDataFixtureCleanupOnFailure {
    record Customer(String id, String email) {}
    record Order(String id, String customerId, double total) {}

    static final AtomicInteger testRunCounter = new AtomicInteger(0);

    static class CustomerService {
        private final Map<String, Customer> customers = new HashMap<>();
        Customer createCustomer(String email) {
            String id = "cust-" + (customers.size() + 1);
            Customer c = new Customer(id, email);
            customers.put(id, c);
            System.out.println("[CustomerService] created " + c);
            return c;
        }
        void deleteCustomer(String id) {
            customers.remove(id);
            System.out.println("[CustomerService] ROLLED BACK: deleted " + id);
        }
        int customerCount() { return customers.size(); }
    }

    static class OrderService {
        private final Map<String, Order> orders = new HashMap<>();
        Order createOrder(String customerId, double total) {
            if (total <= 0) throw new IllegalArgumentException("order total must be positive, got " + total);
            String id = "order-" + (orders.size() + 1);
            Order o = new Order(id, customerId, total);
            orders.put(id, o);
            return o;
        }
        int orderCount() { return orders.size(); }
    }

    // A fixture that CLEANS UP after itself if a later step fails, so a
    // failed test setup never leaves orphaned data behind for other tests to trip over.
    static Order aCustomerWithAnOrder(CustomerService customerService, OrderService orderService, double orderTotal) {
        int testId = testRunCounter.incrementAndGet();
        String uniqueEmail = "test-user-" + testId + "@example.com";
        Customer customer = customerService.createCustomer(uniqueEmail);
        try {
            return orderService.createOrder(customer.id(), orderTotal);
        } catch (RuntimeException e) {
            System.out.println("[fixture] order creation failed, unwinding customer creation to avoid orphaned test data");
            customerService.deleteCustomer(customer.id());
            throw e;
        }
    }

    public static void main(String[] args) {
        CustomerService customerService = new CustomerService();
        OrderService orderService = new OrderService();

        // Successful fixture call.
        aCustomerWithAnOrder(customerService, orderService, 25.00);
        System.out.println("After success: customers=" + customerService.customerCount() + " orders=" + orderService.orderCount());

        // A fixture call whose SECOND step (order creation) fails.
        boolean threw = false;
        try {
            aCustomerWithAnOrder(customerService, orderService, -5.00); // invalid total, deliberately
        } catch (IllegalArgumentException e) {
            threw = true;
            System.out.println("Caught expected failure: " + e.getMessage());
        }
        System.out.println("After failed attempt: threw=" + threw
                + ", customers=" + customerService.customerCount() + " (unchanged, no orphan!) orders=" + orderService.orderCount());
    }
}
```

How to run: `java TestDataFixtureCleanupOnFailure.java`

This is the scenario a real cross-service fixture eventually has to handle: creating state in *one* service succeeds, but a later step in *another* service fails, and without explicit cleanup, the first service is left holding an orphaned customer record that no order ever references — exactly the kind of leaked test data that silently pollutes shared test environments and makes later, unrelated tests behave unpredictably (a customer-listing test that asserts an exact count would fail for a reason having nothing to do with its own logic). The `try`/`catch` inside the fixture calls `customerService.deleteCustomer(customer.id())` before re-throwing, so a failed fixture call leaves the system in exactly the state it started in — no orphan.

## 6. Walkthrough

Trace the second `aCustomerWithAnOrder` call in `TestDataFixtureCleanupOnFailure.main` — the one passing `-5.00`. **First**, `testRunCounter.incrementAndGet()` produces the next test id, and a unique email is built from it. `customerService.createCustomer(uniqueEmail)` runs successfully, printing `[CustomerService] created Customer[id=cust-2, email=test-user-2@example.com]` (the second customer created overall, after the successful call earlier in `main`) and returning that `Customer`.

**Next**, execution enters the `try` block and calls `orderService.createOrder(customer.id(), -5.00)`. Inside `createOrder`, the guard `if (total <= 0)` is true for `-5.00`, so it throws `IllegalArgumentException("order total must be positive, got -5.0")` before any order is added to `orders`.

**Then**, control jumps to the fixture's `catch (RuntimeException e)` block. It prints the unwinding message, then calls `customerService.deleteCustomer(customer.id())`, which removes `cust-2` from `CustomerService`'s internal map and prints the rollback confirmation. After the cleanup, the `catch` block re-throws the original exception (`throw e;`), so the caller still sees the real failure — the fixture doesn't swallow the error, it just ensures cleanup happens before the error propagates.

**Finally**, back in `main`, the surrounding `try`/`catch` catches the re-thrown `IllegalArgumentException`, sets `threw = true`, and prints the caught message. The last line checks both services' counts: `customerService.customerCount()` is still `1` (only the customer from the successful first call remains — `cust-2` was created and then deleted, netting to zero change), and `orderService.orderCount()` is still `1` (the failed order was never actually added). No orphaned data survives the failed fixture call.

```
[CustomerService] created Customer[id=cust-1, email=test-user-1@example.com]
After success: customers=1 orders=1
[CustomerService] created Customer[id=cust-2, email=test-user-2@example.com]
[fixture] order creation failed, unwinding customer creation to avoid orphaned test data
[CustomerService] ROLLED BACK: deleted cust-2
Caught expected failure: order total must be positive, got -5.0
After failed attempt: threw=true, customers=1 (unchanged, no orphan!) orders=1
```

## 7. Gotchas & takeaways

> Copying a snapshot of production data into a test or staging environment "just to have realistic data" is a common shortcut with real consequences: it routinely leaks personally identifiable information into less-secured environments and can violate data-protection regulations outright. Generate synthetic data that matches production's *shape* (distribution of order sizes, realistic name formats, realistic edge cases) instead of using real customer data, and if production data must be used at all, run it through a genuine anonymization process first.

- Respect service ownership when building test data: create data for another service's domain through that service's own API, never by writing directly into its database.
- Give every test its own uniquely identified data — unique emails, unique ids — so tests never collide with each other regardless of execution order or parallelism.
- Clean up what a fixture creates, especially on partial failure, so a failed test setup doesn't leave orphaned data that silently breaks unrelated tests later.
- This problem gets harder, not easier, as you move up the [test pyramid](0411-test-pyramid-for-microservices.md) — a [component test](0414-component-testing-single-service-in-isolation.md) usually needs data from just its own service plus stubs, while an [end-to-end test](0417-end-to-end-testing-its-fragility.md) may genuinely need coordinated state across several real services.
- Never use real, unanonymized production data in test environments — synthetic data generation, designed to match production's realistic shape and edge cases, is the safer and usually just-as-effective alternative.
