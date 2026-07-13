---
card: microservices
gi: 413
slug: integration-testing-service-its-db-broker
title: "Integration testing (service + its DB/broker)"
---

## 1. What it is

An **integration test** verifies that a service correctly talks to a piece of real infrastructure it owns — most commonly its own database or message broker — instead of faking that infrastructure away the way a [unit test](0412-unit-testing-services.md) would. The scope is deliberately narrow: not the whole service, and definitely not other services, just the boundary between "our code" and "the real thing our code depends on." In modern Java practice this almost always means running the real database or broker in a disposable container (Testcontainers is the standard tool) rather than against a shared, long-lived test environment.

## 2. Why & when

You write an integration test specifically to catch the class of bug a unit test structurally cannot: mistakes in the *real* interaction with real infrastructure. A unit test that mocks a repository interface proves your service calls `save()` when it should — it proves nothing about whether the SQL your JPA query actually generates is correct, whether a unique constraint fires when you expect, or whether your Kafka consumer correctly deserializes the message format a real broker delivers.

- **Query correctness.** An `@Query` with a subtly wrong `WHERE` clause, or a JPA mapping that silently produces `N+1` queries, only shows up against a real database engine — an in-memory fake won't enforce the same constraints, indexes, or query planner behavior as production.
- **Schema and migration correctness.** If a migration script (Flyway/Liquibase) and your entity mappings have drifted apart, a real database catches it at test time instead of at deploy time.
- **Serialization correctness.** A message consumer that expects a specific Avro or JSON shape needs to be tested against a real broker actually carrying bytes over the wire, not a mocked `Consumer` object that hands back whatever Java object you told it to.
- **Transactional behavior.** Whether a rollback actually rolls back, whether an outbox row and a business row commit atomically — these only mean something against a real transactional database.

You reach for an integration test whenever a change touches the boundary between your service and its own data store or broker — a new query, a new migration, a new message schema — and you accept the tradeoff that these tests are slower (typically hundreds of milliseconds to a few seconds, dominated by container startup) and more numerous than a handful, but far fewer than your full unit-test count, following the [test pyramid](0411-test-pyramid-for-microservices.md)'s shape.

## 3. Core concept

Picture a unit test as testing whether your car's ignition logic decides correctly *when* to start the engine, using a fake engine that just logs "started." An integration test is turning the key on the *real* engine, in a controlled garage, to confirm it actually starts — you're not driving it down the highway yet (that's an [end-to-end test](0417-end-to-end-testing-its-fragility.md)), but you're no longer pretending the engine exists; you're using the real one, isolated from traffic.

The key discipline is **scope**: an integration test touches exactly one piece of real infrastructure that belongs to *this* service — its own database, its own broker topic — and nothing beyond that boundary. It does not call other services over HTTP, and it does not spin up the whole application context unless testing the wiring itself is the point. The standard shape in a Spring Boot codebase looks like this:

```java
@Testcontainers
class OrderRepositoryIT {
    @Container
    static PostgreSQLContainer<?> db = new PostgreSQLContainer<>("postgres:16");

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry r) {
        r.add("spring.datasource.url", db::getJdbcUrl);
    }

    @Test
    void savesAndFindsOrder() {
        Order saved = repository.save(new Order("order-1", "sku-1", 3));
        assertThat(repository.findById("order-1")).contains(saved);
    }
}
```

`PostgreSQLContainer` starts a real, disposable PostgreSQL instance in Docker just for this test class, and `@DynamicPropertySource` points the application's datasource at it. The test runs real SQL against a real database engine, then the container is torn down — no shared test database to get into a weird state, and no fake standing in for behavior a fake can't accurately reproduce.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An integration test runs the service's real repository code against a real, disposable database container, verifying the actual query and schema, while everything outside the service's own data store remains out of scope">
  <rect x="40" y="70" width="160" height="80" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OrderRepository</text>
  <text x="120" y="123" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">real code, under test</text>

  <line x1="200" y1="110" x2="280" y2="110" stroke="#79c0ff" stroke-width="2"/>
  <text x="240" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">real SQL</text>

  <rect x="280" y="70" width="160" height="80" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="360" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">PostgreSQL</text>
  <text x="360" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">real, disposable</text>
  <text x="360" y="134" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Testcontainer</text>

  <rect x="480" y="70" width="130" height="80" rx="10" fill="#1c2430" stroke="#f85149" stroke-dasharray="4,2"/>
  <text x="545" y="105" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">other services</text>
  <text x="545" y="123" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">OUT OF SCOPE</text>

  <text x="320" y="190" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">only this service's own data store is real; other services are not involved</text>
</svg>

An integration test keeps the scope narrow — real code against the service's own real data store — while leaving every other service out of the picture entirely.

## 5. Runnable example

Scenario: an `OrderRepository` backed by a simple key-value store. Because this file must stay a plain, runnable Java program without an actual Docker daemon or database driver, we simulate "the real database" as a durable, constraint-enforcing in-process store that behaves like one (unique keys, explicit commit/rollback) — the point being to test real *persistence semantics*, not fake ones, which is what a real integration test does against an actual container.

### Level 1 — Basic

```java
// File: OrderRepositoryIntegrationBasic.java -- an integration-style test:
// real save/find logic exercised against a real, stateful store (standing
// in for a containerized database) rather than a mock repository interface.
import java.util.*;

public class OrderRepositoryIntegrationBasic {
    record Order(String id, String sku, int quantity) {}

    // Stands in for a real database: a durable, constraint-aware store.
    static class OrderStore {
        private final Map<String, Order> rows = new HashMap<>();
        void insert(Order o) {
            if (rows.containsKey(o.id())) throw new IllegalStateException("duplicate key: " + o.id());
            rows.put(o.id(), o);
        }
        Optional<Order> findById(String id) { return Optional.ofNullable(rows.get(id)); }
    }

    static class OrderRepository {
        private final OrderStore store;
        OrderRepository(OrderStore store) { this.store = store; }
        void save(Order order) { store.insert(order); }
        Optional<Order> findById(String id) { return store.findById(id); }
    }

    static void assertTrue(String label, boolean condition) {
        System.out.println((condition ? "PASS" : "FAIL") + ": " + label);
    }

    public static void main(String[] args) {
        OrderStore realStore = new OrderStore(); // a fresh, real store per test run
        OrderRepository repository = new OrderRepository(realStore);

        repository.save(new Order("order-1", "sku-1", 3));
        Optional<Order> found = repository.findById("order-1");
        assertTrue("saved order is found with correct fields",
                found.isPresent() && found.get().sku().equals("sku-1") && found.get().quantity() == 3);
    }
}
```

How to run: `java OrderRepositoryIntegrationBasic.java`

Unlike a unit test of `OrderRepository`, this does not mock `OrderStore` — it uses a real, working `OrderStore` instance (standing in for a real containerized database in this runnable file) so that `save` and `findById` are exercised against genuine persistence logic, including the possibility of real failure modes like a duplicate key, which the next level exercises directly.

### Level 2 — Intermediate

```java
// File: OrderRepositoryIntegrationConstraints.java -- the SAME repository,
// now testing REAL database-level behavior a unit test's mock could never
// catch: a unique-key constraint violation, and a query that only a real
// engine enforces correctly (finding orders above a quantity threshold).
import java.util.*;

public class OrderRepositoryIntegrationConstraints {
    record Order(String id, String sku, int quantity) {}

    static class OrderStore {
        private final Map<String, Order> rows = new HashMap<>();
        void insert(Order o) {
            if (rows.containsKey(o.id())) throw new IllegalStateException("duplicate key: " + o.id());
            rows.put(o.id(), o);
        }
        Optional<Order> findById(String id) { return Optional.ofNullable(rows.get(id)); }
        List<Order> findByQuantityGreaterThan(int threshold) {
            List<Order> result = new ArrayList<>();
            for (Order o : rows.values()) if (o.quantity() > threshold) result.add(o);
            result.sort(Comparator.comparing(Order::id));
            return result;
        }
    }

    static class OrderRepository {
        private final OrderStore store;
        OrderRepository(OrderStore store) { this.store = store; }
        void save(Order order) { store.insert(order); }
        List<Order> findBulkOrders(int threshold) { return store.findByQuantityGreaterThan(threshold); }
    }

    static void assertTrue(String label, boolean condition) {
        System.out.println((condition ? "PASS" : "FAIL") + ": " + label);
    }

    public static void main(String[] args) {
        OrderStore realStore = new OrderStore();
        OrderRepository repository = new OrderRepository(realStore);

        repository.save(new Order("order-1", "sku-1", 3));
        repository.save(new Order("order-2", "sku-2", 12));
        repository.save(new Order("order-3", "sku-3", 25));

        List<Order> bulk = repository.findBulkOrders(10);
        assertTrue("query finds exactly the 2 orders above threshold, in order",
                bulk.size() == 2 && bulk.get(0).id().equals("order-2") && bulk.get(1).id().equals("order-3"));

        boolean duplicateRejected;
        try {
            repository.save(new Order("order-1", "sku-9", 1)); // same id as an existing order
            duplicateRejected = false;
        } catch (IllegalStateException e) {
            duplicateRejected = true;
        }
        assertTrue("real store enforces the unique-key constraint on save", duplicateRejected);
    }
}
```

How to run: `java OrderRepositoryIntegrationConstraints.java`

Two things happen here that a mocked repository could never meaningfully verify. First, `findBulkOrders` runs a real filter-and-sort query against the store and the test checks the *exact* result set and order — this is testing the query logic itself, not just that "some method was called." Second, saving a second order with an already-used id triggers the store's real duplicate-key check, exactly mirroring how a real database's unique constraint would reject a duplicate primary key with a constraint-violation exception. A mock repository, told in advance what to return, would have no opinion about either of these — they only mean something against something that actually enforces the rules.

### Level 3 — Advanced

```java
// File: OrderRepositoryIntegrationTransaction.java -- the SAME repository,
// now testing a REAL transactional guarantee: saving an order AND writing
// an outbox event must succeed or fail TOGETHER (atomicity), the
// production-flavored hard case integration tests exist to catch.
import java.util.*;

public class OrderRepositoryIntegrationTransaction {
    record Order(String id, String sku, int quantity) {}
    record OutboxEvent(String orderId, String type) {}

    static class TransactionalStore {
        private final Map<String, Order> orders = new HashMap<>();
        private final List<OutboxEvent> outbox = new ArrayList<>();

        // Simulates a single DB transaction covering two writes.
        // If ANYTHING after the first write throws, BOTH writes must be undone.
        void saveOrderWithOutboxEvent(Order order, boolean simulateOutboxFailure) {
            Map<String, Order> ordersBackup = new HashMap<>(orders);
            List<OutboxEvent> outboxBackup = new ArrayList<>(outbox);
            try {
                if (orders.containsKey(order.id())) throw new IllegalStateException("duplicate key: " + order.id());
                orders.put(order.id(), order);
                if (simulateOutboxFailure) throw new RuntimeException("outbox write failed (e.g. serialization error)");
                outbox.add(new OutboxEvent(order.id(), "ORDER_CREATED"));
            } catch (RuntimeException e) {
                // ROLLBACK: restore both maps to their pre-transaction state.
                orders.clear(); orders.putAll(ordersBackup);
                outbox.clear(); outbox.addAll(outboxBackup);
                throw e;
            }
        }

        Optional<Order> findOrder(String id) { return Optional.ofNullable(orders.get(id)); }
        List<OutboxEvent> allOutboxEvents() { return outbox; }
    }

    static void assertTrue(String label, boolean condition) {
        System.out.println((condition ? "PASS" : "FAIL") + ": " + label);
    }

    public static void main(String[] args) {
        TransactionalStore store = new TransactionalStore();

        // Happy path: both writes commit together.
        store.saveOrderWithOutboxEvent(new Order("order-1", "sku-1", 2), false);
        assertTrue("happy path: order saved", store.findOrder("order-1").isPresent());
        assertTrue("happy path: outbox event saved", store.allOutboxEvents().size() == 1);

        // Failure path: the outbox write fails -- the order write must ALSO be rolled back,
        // not left half-committed (which would silently drop the event forever).
        boolean threw = false;
        try {
            store.saveOrderWithOutboxEvent(new Order("order-2", "sku-2", 5), true);
        } catch (RuntimeException e) {
            threw = true;
        }
        assertTrue("failure path: exception propagated", threw);
        assertTrue("failure path: order-2 was ROLLED BACK, not left half-saved", store.findOrder("order-2").isEmpty());
        assertTrue("failure path: outbox still has only the original 1 event", store.allOutboxEvents().size() == 1);
    }
}
```

How to run: `java OrderRepositoryIntegrationTransaction.java`

This is the kind of bug integration tests are specifically good at catching and unit tests structurally cannot: a partial-commit bug where the order row is saved but the outbox event write fails, leaving the order persisted with no corresponding event ever published — a silent data-consistency bug that could sit undetected in production for a long time. `saveOrderWithOutboxEvent` snapshots both collections before attempting either write, and on any exception restores both to their pre-transaction state before re-throwing, mirroring how a real `@Transactional` method backed by a real database would roll back every write in the same transaction on any unhandled exception. The test doesn't just check that an exception was thrown — it explicitly checks that `order-2` is *absent* afterward, proving the rollback actually happened rather than the order being left half-saved.

## 6. Walkthrough

Trace `OrderRepositoryIntegrationTransaction.main` in order. **First**, `store.saveOrderWithOutboxEvent(new Order("order-1", ...), false)` runs. Inside, backups of both `orders` and `outbox` are taken. `orders.put("order-1", ...)` succeeds. Since `simulateOutboxFailure` is `false`, the `if` guard is skipped, and `outbox.add(new OutboxEvent("order-1", "ORDER_CREATED"))` runs. No exception occurs, so the `catch` block never triggers, and both writes stand. The two `assertTrue` calls confirm `order-1` is findable and exactly one outbox event exists.

**Next**, `store.saveOrderWithOutboxEvent(new Order("order-2", ...), true)` runs inside a `try` block in `main`. Inside the method, backups are taken again — now including `order-1` and its outbox event as the "before" state. `orders.put("order-2", ...)` succeeds, so at this instant `order-2` exists in `orders` but *no* outbox event has been written for it yet. `simulateOutboxFailure` is `true`, so the method throws `RuntimeException("outbox write failed...")` before `outbox.add` for `order-2` ever runs.

**Then**, the `catch` block inside `saveOrderWithOutboxEvent` fires: `orders.clear(); orders.putAll(ordersBackup)` restores `orders` to exactly its pre-call state — which still contains `order-1` but no longer contains `order-2`, undoing the partial write. `outbox.clear(); outbox.addAll(outboxBackup)` does the same for the outbox (a no-op here since the outbox was never touched this call). The exception is then re-thrown, propagating out to `main`'s `try`/`catch`, which sets `threw = true`.

**Finally**, the last three `assertTrue` calls verify the outcome: the exception did propagate, `order-2` is absent from the store (proving rollback, not a half-commit), and the outbox still holds exactly the one event from the happy path, not a phantom entry from the failed attempt.

```
PASS: happy path: order saved
PASS: happy path: outbox event saved
PASS: failure path: exception propagated
PASS: failure path: order-2 was ROLLED BACK, not left half-saved
PASS: failure path: outbox still has only the original 1 event
```

## 7. Gotchas & takeaways

> Pointing integration tests at a shared, long-lived test database (instead of a fresh container per run) is a common shortcut that eventually causes mysterious failures: one test's leftover row breaks another test's assumption about how many rows a query should return, and the failures only reproduce when tests run in a particular order. Testcontainers exists specifically to give each test run — or at least each test class — a clean, disposable, real instance, trading a bit of startup time for complete isolation.

- Integration tests verify the boundary between your code and *your own* infrastructure — real database, real broker — not other services; calling another service belongs in a [component test](0414-component-testing-single-service-in-isolation.md) or higher.
- They catch a class of bug unit tests structurally cannot: wrong SQL, broken migrations, constraint violations, and partial-commit consistency bugs like the outbox example above.
- Keep the scope narrow and the count moderate — following the [test pyramid](0411-test-pyramid-for-microservices.md), you want far fewer integration tests than unit tests, because container startup makes each one meaningfully slower.
- Prefer a fresh, real, disposable instance (a Testcontainers container) over a shared test environment — shared state is the single biggest source of flaky integration tests.
- A green integration-test suite proves your service persists and retrieves data correctly; it says nothing about whether the service behaves correctly when *other* services are involved — that's what [component testing](0414-component-testing-single-service-in-isolation.md) and [end-to-end testing](0417-end-to-end-testing-its-fragility.md) check next.
