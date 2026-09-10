---
card: system-design
gi: 198
slug: hexagonal-ports-and-adapters
title: Hexagonal / ports-and-adapters
---

## 1. What it is

**Hexagonal architecture**, also called **ports-and-adapters**, is a way to structure a single service's *internal* code so that its business logic has no dependency on any specific technology — no direct dependency on a database driver, an HTTP framework, or a message queue library. The business logic defines **ports** (interfaces it needs, like `OrderRepository`), and technology-specific **adapters** implement those ports.

## 2. Why & when

Business logic that calls a specific database driver or framework class directly becomes hard to test (you need a real database to run a unit test) and hard to change (swapping databases means rewriting the business logic itself). Hexagonal architecture solves this by inverting the dependency: business logic depends only on an interface (`port`) it defines itself, and the database-specific code (`adapter`) depends on that interface, not the other way around.

Use this pattern inside any single service — regardless of whether that service is part of a [monolith](0195-monolith-modular-monolith.md) or a [microservice](0196-microservices.md) — whenever you want to unit-test business rules without spinning up a real database or HTTP server, or whenever you expect the underlying technology (which database, which message broker) to change later. It is unnecessary for a tiny script with no meaningful business logic to protect.

## 3. Core concept

- **The hexagon (core).** The center of the diagram holds pure business logic: domain objects and use cases, with zero imports from any framework or driver.
- **Ports.** Interfaces defined *by the core*, describing what it needs (`OrderRepository.save(Order)`) or what it offers (`PlaceOrderUseCase.execute(...)`). A port is owned by the core, not by the technology on the other side.
- **Driven adapters (outbound).** Implementations of a port that the core calls out to — a `JpaOrderRepository` implementing `OrderRepository`, or a `KafkaEventPublisher` implementing `EventPublisher`. These depend on the core's interface; the core never imports them.
- **Driving adapters (inbound).** Code that calls *into* the core through a port — a REST controller calling `PlaceOrderUseCase.execute(...)`, or a message listener doing the same. Multiple driving adapters (REST, a CLI, a scheduled job) can all call the same use case.
- **Dependency inversion is the whole mechanism.** The arrow of dependency always points inward, toward the core. Frameworks depend on business logic; business logic never depends on frameworks.

## 4. Diagram

```
                 DRIVING ADAPTERS (inbound)
        +----------------+      +----------------+
        | REST Controller|      | CLI Command     |
        +--------+-------+      +--------+--------+
                 |                        |
                 v                        v
        +------------------------------------------+
        |     PORT: PlaceOrderUseCase (interface)   |
        +------------------------------------------+
                 |
                 v
        +------------------------------------------+
        |          CORE (business logic)             |
        |   Order, pricing rules, validation rules    |
        |   depends on NOTHING technology-specific    |
        +------------------------------------------+
                 |
                 v
        +------------------------------------------+
        |     PORT: OrderRepository (interface)     |
        +------------------------------------------+
                 ^                        ^
                 |                        |
        +--------+-------+      +--------+--------+
        | JpaOrderRepo    |      | InMemoryOrderRepo|
        | (real DB)       |      | (for tests)       |
        +-----------------+      +-------------------+
                 DRIVEN ADAPTERS (outbound)
```
*Caption: arrows always point toward the core. The core defines `PlaceOrderUseCase` and `OrderRepository` as interfaces; every technology-specific class implements one of them, never the reverse.*

## 5. Runnable example

**Level 1 — Basic.** The core use case depends only on a `OrderRepository` port; an in-memory adapter implements it.

**Level 2 — Intermediate.** Add a second, "real" adapter (simulating a JDBC-backed repository) and a driving adapter (a fake REST controller) that both work against the exact same core, unchanged.

**Level 3 — Advanced.** Show the core unit-tested with a test double for the port — no database, no framework — proving the whole point of the pattern.

```java
// HexagonalDemo.java
import java.util.*;

public class HexagonalDemo {

    // ---------- CORE: domain + port, zero technology dependencies ----------
    record Order(String id, String customerId, double amount) {}

    interface OrderRepository { // PORT, owned by the core
        void save(Order order);
        Optional<Order> findById(String id);
    }

    static class PlaceOrderUseCase { // CORE use case, only depends on the port interface
        private final OrderRepository repository;
        PlaceOrderUseCase(OrderRepository repository) { this.repository = repository; }

        Order execute(String customerId, double amount) {
            if (amount <= 0) throw new IllegalArgumentException("amount must be positive");
            Order order = new Order(UUID.randomUUID().toString().substring(0, 8), customerId, amount);
            repository.save(order);
            return order;
        }
    }

    // ---------- Level 1: driven adapter #1 - in-memory ----------
    static class InMemoryOrderRepository implements OrderRepository {
        Map<String, Order> store = new HashMap<>();
        public void save(Order order) { store.put(order.id(), order); }
        public Optional<Order> findById(String id) { return Optional.ofNullable(store.get(id)); }
    }

    // ---------- Level 2: driven adapter #2 - simulated JDBC-backed repository ----------
    static class SimulatedJdbcOrderRepository implements OrderRepository {
        List<String> executedSql = new ArrayList<>();
        Map<String, Order> table = new HashMap<>();
        public void save(Order order) {
            executedSql.add("INSERT INTO orders VALUES ('" + order.id() + "', '" +
                order.customerId() + "', " + order.amount() + ")");
            table.put(order.id(), order);
        }
        public Optional<Order> findById(String id) { return Optional.ofNullable(table.get(id)); }
    }

    // Level 2: driving adapter - a fake REST controller calling the same use case.
    static class OrderRestController {
        private final PlaceOrderUseCase useCase;
        OrderRestController(PlaceOrderUseCase useCase) { this.useCase = useCase; }
        String postOrder(String customerId, double amount) {
            Order order = useCase.execute(customerId, amount);
            return "201 Created -> {id: " + order.id() + ", customerId: " + order.customerId() + "}";
        }
    }

    // ---------- Level 3: unit test the core with a minimal test double ----------
    static class RecordingFakeRepository implements OrderRepository {
        List<Order> saved = new ArrayList<>();
        public void save(Order order) { saved.add(order); }
        public Optional<Order> findById(String id) {
            return saved.stream().filter(o -> o.id().equals(id)).findFirst();
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - core + in-memory adapter:");
        PlaceOrderUseCase useCase1 = new PlaceOrderUseCase(new InMemoryOrderRepository());
        Order o1 = useCase1.execute("cust-1", 49.99);
        System.out.println("  placed: " + o1);

        System.out.println("\nLevel 2 - same core, different driven adapter + a driving adapter:");
        SimulatedJdbcOrderRepository jdbcRepo = new SimulatedJdbcOrderRepository();
        PlaceOrderUseCase useCase2 = new PlaceOrderUseCase(jdbcRepo);
        OrderRestController controller = new OrderRestController(useCase2);
        System.out.println("  " + controller.postOrder("cust-2", 120.00));
        System.out.println("  SQL executed by adapter: " + jdbcRepo.executedSql);

        System.out.println("\nLevel 3 - unit test the core with no database at all:");
        RecordingFakeRepository fake = new RecordingFakeRepository();
        PlaceOrderUseCase testUseCase = new PlaceOrderUseCase(fake);
        try {
            testUseCase.execute("cust-3", -5.00); // should be rejected by core validation
            System.out.println("  FAIL: expected rejection");
        } catch (IllegalArgumentException e) {
            System.out.println("  PASS: core rejected invalid amount without touching any real DB: " + e.getMessage());
        }
        System.out.println("  orders saved by fake during this test: " + fake.saved.size());
    }
}
```

**How to run:** `java HexagonalDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `PlaceOrderUseCase` is constructed with an `InMemoryOrderRepository`. Calling `execute("cust-1", 49.99)` builds an `Order`, calls `repository.save(order)` through the `OrderRepository` interface, and returns the order. The use case's code never mentions `InMemoryOrderRepository` by name — it only knows `OrderRepository`.
2. **Level 2:** the exact same `PlaceOrderUseCase` class is reused, this time constructed with `SimulatedJdbcOrderRepository` instead. `OrderRestController.postOrder(...)` (a driving adapter) calls `useCase.execute(...)` — the same call Level 1 made directly — and formats the result as an HTTP-style response string. Note `jdbcRepo.executedSql` shows the "SQL" that ran, proving the swap from in-memory to JDBC changed nothing in the core.
3. **Level 3:** `RecordingFakeRepository` is a minimal test double with no real persistence at all. `testUseCase.execute("cust-3", -5.00)` triggers the core's own validation rule (`amount <= 0`) and throws `IllegalArgumentException` — this exception comes from business logic in `PlaceOrderUseCase`, not from any adapter.
4. Because that validation lives in the core and depends on nothing external, the `catch` block proves the rule was tested with zero database setup and zero HTTP server — exactly the payoff the pattern promises.
5. `fake.saved.size()` prints `0`, because the invalid order was rejected before `repository.save(...)` was ever called — the core enforced its rule before any adapter saw the data.

## 7. Gotchas & takeaways

> **Gotcha:** it is easy to define a port that just mirrors your database's schema (`OrderRepository.findByCustomerIdAndStatusAndDateRange(...)`) — this leaks database concerns into the "core" and defeats the pattern. Ports should reflect what the *business logic* needs, not what a particular query engine makes convenient.

- The core never imports a framework annotation, driver class, or protocol library — if it does, the boundary has already broken.
- This pattern is about a single service's internal structure. It answers "how do I organize this service's code," not "how do services talk to each other" (that is [microservices](0196-microservices.md) or [SOA](0197-service-oriented-architecture-soa.md)).
- The real payoff is testability: the core's business rules run in fast, dependency-free unit tests, while integration tests (with a real database) cover the adapters separately.
- Do not over-apply this to trivial CRUD services with no real business rules — the extra interfaces add ceremony with no corresponding benefit when there is nothing to protect.
