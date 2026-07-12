---
card: microservices
gi: 56
slug: repositories-ddd-sense
title: Repositories (DDD sense)
---

## 1. What it is

A **repository**, in the DDD sense, is an abstraction that provides collection-like access to [aggregates](0052-aggregates-and-aggregate-roots.md) — `orderRepository.findById(id)`, `orderRepository.save(order)` — hiding away how those aggregates are actually persisted (a relational database, a document store, an in-memory map for testing) behind an interface that looks and feels like working with an in-memory collection of domain objects. Critically, a repository always deals in **whole aggregates**, never fragments — you never fetch "just the line items" or save "just the total field"; you always load and save a complete, consistent `Order` through its root.

```java
interface OrderRepository {
    Optional<Order> findById(String orderId);
    void save(Order order); // saves the WHOLE aggregate, root and everything inside it, atomically
}
```

## 2. Why & when

Without the repository abstraction, domain and application logic ends up scattered with direct persistence calls — SQL queries, or a specific database client's API — mixed directly into code that should be focused purely on business rules. That mixing makes the domain logic harder to test (every test needs a real or heavily-mocked database) and harder to change (switching persistence technology means hunting down and rewriting persistence code wherever it happens to be scattered). A repository draws a clean line: domain and application logic talk only to the repository's collection-like interface; the actual persistence mechanism lives entirely behind it, in one place, swappable independently.

Introduce a repository for each aggregate root in your domain — one `OrderRepository` for the `Order` aggregate, one `CustomerRepository` for the `Customer` aggregate — never one repository per entity or value object *inside* an aggregate, since those are only ever accessed through their aggregate root anyway.

## 3. Core concept

The interface stays deliberately simple and collection-like, hiding all persistence detail behind it:

```
OrderRepository (interface, lives in the DOMAIN layer)
    findById(id) -> Optional<Order>
    save(order)  -> void
        |
   implemented by:
        InMemoryOrderRepository   (for tests -- fast, no real database needed)
        JdbcOrderRepository       (for production -- a real relational database underneath)
```

Domain and application code depends only on the interface; which implementation is actually wired in is a deployment/configuration detail, not something business logic needs to know about.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Domain logic depends on the OrderRepository interface; either an in-memory or a real database implementation can be plugged in behind it without domain logic changing">
  <rect x="30" y="55" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Domain / application logic</text>

  <rect x="260" y="55" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="335" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderRepository (interface)</text>

  <rect x="460" y="20" width="150" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="535" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">InMemoryOrderRepository</text>
  <rect x="460" y="100" width="150" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="535" y="125" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">JdbcOrderRepository</text>

  <line x1="210" y1="80" x2="260" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a56)"/>
  <line x1="410" y1="75" x2="460" y2="45" stroke="#8b949e" stroke-width="1"/>
  <line x1="410" y1="85" x2="460" y2="115" stroke="#8b949e" stroke-width="1"/>
  <defs><marker id="a56" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Domain logic depends only on the interface; either implementation can be swapped in behind it invisibly.

## 5. Runnable example

Scenario: order management logic, first with persistence code mixed directly into business logic, then cleanly separated behind a repository interface, then swapping the implementation to prove the domain logic is fully insulated.

### Level 1 — Basic

```java
// File: MixedPersistence.java -- persistence details MIXED directly into
// business logic -- hard to test, hard to change.
import java.util.*;

public class MixedPersistence {
    static class Order { String orderId; double total; Order(String orderId, double total) { this.orderId = orderId; this.total = total; } }

    static Map<String, Order> database = new HashMap<>(); // persistence detail LIVING directly alongside business logic

    static void placeOrderAndSave(String orderId, double total) {
        Order order = new Order(orderId, total); // business logic
        database.put(orderId, order); // persistence detail, MIXED IN directly -- no separation at all
        System.out.println("order placed and saved: " + orderId);
    }

    public static void main(String[] args) {
        placeOrderAndSave("ord-1", 29.98);
        System.out.println("total orders in database: " + database.size());
    }
}
```

**How to run:** `javac MixedPersistence.java && java MixedPersistence` (JDK 17+).

Expected output:
```
order placed and saved: ord-1
total orders in database: 1
```

`placeOrderAndSave` mixes constructing the `Order` (business logic) with directly manipulating a `HashMap` standing in for a database (a persistence detail) — testing this logic in isolation, or later swapping to a real database, means touching this same method either way.

### Level 2 — Intermediate

```java
// File: RepositoryAbstraction.java -- persistence hidden behind a
// collection-like REPOSITORY interface.
import java.util.*;

public class RepositoryAbstraction {
    static class Order { String orderId; double total; Order(String orderId, double total) { this.orderId = orderId; this.total = total; } }

    interface OrderRepository { // the DOMAIN-facing abstraction
        Optional<Order> findById(String orderId);
        void save(Order order);
    }

    static class InMemoryOrderRepository implements OrderRepository { // ONE implementation, persistence detail lives HERE only
        Map<String, Order> storage = new HashMap<>();
        public Optional<Order> findById(String orderId) { return Optional.ofNullable(storage.get(orderId)); }
        public void save(Order order) { storage.put(order.orderId, order); }
    }

    // business logic now depends ONLY on the interface -- no persistence detail visible here at all
    static void placeOrder(OrderRepository repository, String orderId, double total) {
        Order order = new Order(orderId, total);
        repository.save(order);
        System.out.println("order placed and saved: " + orderId);
    }

    public static void main(String[] args) {
        OrderRepository repository = new InMemoryOrderRepository();
        placeOrder(repository, "ord-1", 29.98);
        System.out.println("found: " + repository.findById("ord-1").isPresent());
    }
}
```

**How to run:** `javac RepositoryAbstraction.java && java RepositoryAbstraction` (JDK 17+).

Expected output:
```
order placed and saved: ord-1
found: true
```

`placeOrder` now depends only on the `OrderRepository` interface — no `HashMap`, no persistence detail of any kind is visible in this method. `InMemoryOrderRepository` is the only place that knows how orders are actually stored.

### Level 3 — Advanced

```java
// File: SwappableImplementation.java -- prove the business logic is
// FULLY INSULATED by swapping to a DIFFERENT repository implementation.
import java.util.*;

public class SwappableImplementation {
    static class Order { String orderId; double total; Order(String orderId, double total) { this.orderId = orderId; this.total = total; } }

    interface OrderRepository {
        Optional<Order> findById(String orderId);
        void save(Order order);
    }

    static class InMemoryOrderRepository implements OrderRepository {
        Map<String, Order> storage = new HashMap<>();
        public Optional<Order> findById(String orderId) { return Optional.ofNullable(storage.get(orderId)); }
        public void save(Order order) { storage.put(order.orderId, order); System.out.println("  [InMemory] saved " + order.orderId); }
    }

    // a COMPLETELY different implementation -- simulates a "database" with logging and an audit trail,
    // a genuinely different internal mechanism from InMemoryOrderRepository.
    static class AuditedOrderRepository implements OrderRepository {
        Map<String, Order> storage = new HashMap<>();
        List<String> auditLog = new ArrayList<>();
        public Optional<Order> findById(String orderId) { return Optional.ofNullable(storage.get(orderId)); }
        public void save(Order order) {
            storage.put(order.orderId, order);
            auditLog.add("saved " + order.orderId + " at $" + order.total);
            System.out.println("  [Audited] saved " + order.orderId + " (audit log now has " + auditLog.size() + " entries)");
        }
    }

    // BUSINESS LOGIC, IDENTICAL in both runs below -- never touches persistence detail at all
    static void placeOrder(OrderRepository repository, String orderId, double total) {
        Order order = new Order(orderId, total);
        repository.save(order);
    }

    public static void main(String[] args) {
        System.out.println("Using InMemoryOrderRepository:");
        placeOrder(new InMemoryOrderRepository(), "ord-1", 29.98);

        System.out.println("Using AuditedOrderRepository (SAME business logic, different persistence):");
        placeOrder(new AuditedOrderRepository(), "ord-2", 19.99);
    }
}
```

**How to run:** `javac SwappableImplementation.java && java SwappableImplementation` (JDK 17+).

Expected output:
```
Using InMemoryOrderRepository:
  [InMemory] saved ord-1
Using AuditedOrderRepository (SAME business logic, different persistence):
  [Audited] saved ord-2 (audit log now has 1 entries)
```

The production-flavored proof: `placeOrder`'s source code is called identically in both cases, yet produces genuinely different persistence behavior — `AuditedOrderRepository` maintains an audit log `InMemoryOrderRepository` doesn't even have — purely because a different `OrderRepository` implementation was passed in. `placeOrder` itself never changed, and never needed to know which implementation it was actually working with.

## 6. Walkthrough

1. `placeOrder(new InMemoryOrderRepository(), "ord-1", 29.98)` constructs an `Order`, then calls `repository.save(order)` — resolved at run time to `InMemoryOrderRepository.save`, which stores the order in its own `storage` map and prints the `[InMemory]` log line.
2. `placeOrder(new AuditedOrderRepository(), "ord-2", 19.99)` runs the *exact same* `placeOrder` method body — same bytecode, same source — but this time `repository.save(order)` resolves to `AuditedOrderRepository.save`, which stores the order in its own separate `storage` map, *and* additionally appends an entry to its own `auditLog`, printing the `[Audited]` log line with the current audit log size.
3. `placeOrder` itself has no branching logic, no `if` statement checking which repository type it received — the different behavior comes entirely from Java's dynamic dispatch resolving `repository.save(...)` to whichever concrete implementation was actually passed in.
4. This is the repository abstraction's core payoff made concrete: business logic (`placeOrder`) is completely decoupled from persistence mechanism (`InMemoryOrderRepository` versus `AuditedOrderRepository`) — swapping one for the other, even one with a genuinely different internal capability like an audit log, required zero changes to the business logic calling it.

```
placeOrder(repository, orderId, total)  <- IDENTICAL code, both calls
        |
   repository.save(order)  <- resolved at RUN TIME
        |
   +-------------------------+---------------------------------------+
   InMemoryOrderRepository     AuditedOrderRepository
   (simple map storage)        (map storage + audit log, extra capability)
```

## 7. Gotchas & takeaways

> **Gotcha:** a repository should return and accept whole aggregates, never fragments — a method like `updateOrderTotal(orderId, newTotal)` that bypasses loading the full `Order` and calling its own invariant-enforcing methods reintroduces exactly the aggregate-boundary violation [aggregates and aggregate roots](0052-aggregates-and-aggregate-roots.md) is meant to prevent. Always load the full aggregate, mutate it through its own methods, then save the whole thing back.

- A repository provides collection-like access to aggregates (`findById`, `save`), hiding the actual persistence mechanism behind a simple interface that domain and application logic depend on.
- Repositories always deal in whole aggregates, never fragments — loading, mutating through the aggregate root's own methods, and saving the complete aggregate back, never partially updating internal state directly.
- One repository per aggregate root — entities and value objects living inside an aggregate are never given their own separate repository, since they're only ever accessed through their aggregate's root anyway.
- The concrete proof of proper separation: business logic calling a repository should be able to work identically against any correct implementation of that repository's interface, with zero changes required to swap one implementation for another.
