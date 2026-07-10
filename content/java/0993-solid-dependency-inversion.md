---
card: java
gi: 993
slug: solid-dependency-inversion
title: SOLID — Dependency Inversion
---

## 1. What it is

The **Dependency Inversion Principle (DIP)** says high-level modules (business logic) shouldn't depend on low-level modules (database drivers, HTTP clients, file systems); both should depend on **abstractions** (interfaces). And abstractions shouldn't depend on details — details should depend on abstractions. In practice: an `OrderService` shouldn't construct a `MySqlOrderRepository` directly inside itself; it should depend on an `OrderRepository` interface, and something else (a caller, a framework, a wiring class) decides which concrete implementation to hand it.

The name is about *inverting* the naive direction of dependency: instead of business logic depending downward on infrastructure details, both depend on an abstraction that sits between them, and the infrastructure now depends *up* on that abstraction by implementing it.

## 2. Why & when

When high-level logic directly instantiates low-level details (`new MySqlOrderRepository()` inside `OrderService`), the business logic becomes welded to that one database technology — swapping databases, or testing the service without a real database, means editing the high-level class itself. DIP exists to keep the expensive-to-change, important business logic decoupled from the cheap-to-swap technical details underneath it, so the direction of "what depends on what" flows toward stability, not toward whatever happens to be the current infrastructure choice.

Reach for DIP whenever a class that represents genuine business logic reaches for `new` on something that talks to the outside world (a database, an HTTP client, a file system, a clock). Pass an interface into the constructor instead, and let something else decide the concrete implementation. This is what makes unit testing without a real database possible — a test can hand in an in-memory fake implementing the same interface.

## 3. Core concept

```
// Violates DIP: OrderService (high-level) directly depends on MySqlOrderRepository (low-level detail)
class OrderService {
    private final MySqlOrderRepository repository = new MySqlOrderRepository();
    void placeOrder(String item) { repository.save(item); }
}

// Follows DIP: OrderService depends on an abstraction; the concrete detail is supplied from outside
interface OrderRepository { void save(String item); }
class MySqlOrderRepository implements OrderRepository {
    public void save(String item) { /* JDBC calls */ }
}
class OrderService {
    private final OrderRepository repository; // depends on the interface, not the detail
    OrderService(OrderRepository repository) { this.repository = repository; }
    void placeOrder(String item) { repository.save(item); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OrderService depending directly on MySqlOrderRepository versus both OrderService and MySqlOrderRepository depending on an OrderRepository interface">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Before: direct dependency</text>
  <rect x="40" y="60" width="200" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="140" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <rect x="40" y="130" width="200" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="140" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MySqlOrderRepository</text>
  <line x1="140" y1="100" x2="140" y2="130" stroke="#f0883e" marker-end="url(#a)"/>

  <text x="490" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">After: inverted via interface</text>
  <rect x="400" y="30" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="51" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OrderRepository (interface)</text>
  <rect x="380" y="100" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="425" y="124" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <rect x="490" y="100" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="124" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">MySqlOrderRepository</text>
  <line x1="425" y1="100" x2="470" y2="64" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="550" y1="100" x2="510" y2="64" stroke="#79c0ff" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both `OrderService` and `MySqlOrderRepository` now point *up* at the shared `OrderRepository` abstraction, instead of the service pointing straight down at the concrete database class.

## 5. Runnable example

Scenario: an order service that persists orders, evolving from a hard-wired database dependency into a design where the concrete storage is supplied from outside and swappable — including for tests.

### Level 1 — Basic

```java
// File: DipBasic.java
class MySqlOrderRepository {
    void save(String item) {
        System.out.println("[MySQL] INSERT INTO orders VALUES ('" + item + "')");
    }
}

class OrderService {
    private final MySqlOrderRepository repository = new MySqlOrderRepository();
    void placeOrder(String item) {
        repository.save(item);
    }
}

public class DipBasic {
    public static void main(String[] args) {
        OrderService service = new OrderService();
        service.placeOrder("widget");
    }
}
```

**How to run:** save as `DipBasic.java`, then `javac DipBasic.java && java DipBasic` (JDK 17+).

Expected output:
```
[MySQL] INSERT INTO orders VALUES ('widget')
```

`OrderService` constructs `MySqlOrderRepository` itself — it's welded to MySQL and can't be tested or reconfigured without editing `OrderService`'s own source.

### Level 2 — Intermediate

```java
// File: DipIntermediate.java
interface OrderRepository {
    void save(String item);
}

class MySqlOrderRepository implements OrderRepository {
    public void save(String item) {
        System.out.println("[MySQL] INSERT INTO orders VALUES ('" + item + "')");
    }
}

class OrderService {
    private final OrderRepository repository;
    OrderService(OrderRepository repository) { this.repository = repository; }
    void placeOrder(String item) {
        repository.save(item);
    }
}

public class DipIntermediate {
    public static void main(String[] args) {
        OrderService service = new OrderService(new MySqlOrderRepository());
        service.placeOrder("widget");
    }
}
```

**How to run:** save as `DipIntermediate.java`, then `javac DipIntermediate.java && java DipIntermediate` (JDK 17+).

Expected output:
```
[MySQL] INSERT INTO orders VALUES ('widget')
```

The real-world concern added: `OrderService` now depends on the `OrderRepository` interface, and the concrete `MySqlOrderRepository` is handed in from outside (here, from `main`). Switching databases means writing a new class implementing `OrderRepository` — `OrderService` itself never changes.

### Level 3 — Advanced

```java
// File: DipAdvanced.java
import java.util.ArrayList;
import java.util.List;

interface OrderRepository {
    void save(String item);
    List<String> findAll();
}

class MySqlOrderRepository implements OrderRepository {
    public void save(String item) {
        System.out.println("[MySQL] INSERT INTO orders VALUES ('" + item + "')");
    }
    public List<String> findAll() {
        throw new UnsupportedOperationException("would query the real database");
    }
}

// A fake used purely for testing -- OrderService has no idea it isn't talking
// to a real database, because it only ever depends on the OrderRepository interface.
class InMemoryOrderRepository implements OrderRepository {
    private final List<String> orders = new ArrayList<>();
    public void save(String item) {
        orders.add(item);
        System.out.println("[in-memory] saved '" + item + "'");
    }
    public List<String> findAll() {
        return List.copyOf(orders);
    }
}

class OrderService {
    private final OrderRepository repository;
    OrderService(OrderRepository repository) { this.repository = repository; }
    void placeOrder(String item) { repository.save(item); }
    List<String> listOrders() { return repository.findAll(); }
}

public class DipAdvanced {
    public static void main(String[] args) {
        // Production wiring would supply MySqlOrderRepository here.
        // For this demo (and in real unit tests) we supply the fake instead --
        // OrderService's own code is completely identical either way.
        OrderService service = new OrderService(new InMemoryOrderRepository());
        service.placeOrder("widget");
        service.placeOrder("gadget");
        System.out.println("all orders: " + service.listOrders());
    }
}
```

**How to run:** save as `DipAdvanced.java`, then `javac DipAdvanced.java && java DipAdvanced` (JDK 17+).

Expected output:
```
[in-memory] saved 'widget'
[in-memory] saved 'gadget'
all orders: [widget, gadget]
```

The production-flavored hard case: `InMemoryOrderRepository` is a test double that never touches a real database, yet `OrderService` works with it exactly as it would with `MySqlOrderRepository` — that's the entire payoff of DIP, testing high-level logic in complete isolation from infrastructure.

## 6. Walkthrough

Tracing `DipAdvanced.main` end to end:

1. `new InMemoryOrderRepository()` constructs a fake repository backed by a plain `ArrayList`, no database involved.
2. `new OrderService(repository)` stores that fake behind the `OrderRepository` field — `OrderService`'s constructor and every method inside it only ever refer to the interface type, never to `InMemoryOrderRepository` specifically.
3. `service.placeOrder("widget")` calls `repository.save("widget")`, which dispatches (via the interface) to `InMemoryOrderRepository.save`: the item is appended to the internal list and `"[in-memory] saved 'widget'"` is printed.
4. `service.placeOrder("gadget")` repeats the same path, appending `"gadget"` and printing its own confirmation line.
5. `service.listOrders()` calls `repository.findAll()`, dispatching to `InMemoryOrderRepository.findAll()`, which returns an immutable copy of the list: `["widget", "gadget"]`.
6. `main` prints `"all orders: [widget, gadget]"`. If `MySqlOrderRepository` were substituted in at construction instead, every line of `OrderService` and `main`'s calls to it would be byte-for-byte identical — only the object passed to the constructor would change.

## 7. Gotchas & takeaways

> **Gotcha:** DIP is not "always use interfaces everywhere." It specifically targets the boundary between important business logic and volatile infrastructure details. Wrapping a trivial, stable utility class in an interface "just in case" adds indirection without the actual benefit DIP provides — swappability and testability at a genuine seam.

- DIP: high-level modules and low-level modules should both depend on an abstraction; the abstraction shouldn't depend on either's details.
- The practical test: does a business-logic class construct (`new`) something that talks to a database, network, or file system directly inside itself? If so, that dependency should be inverted.
- Passing dependencies in through a constructor (rather than constructing them internally) is called **dependency injection** — it's the mechanical technique that makes DIP practical; frameworks like Spring automate the wiring.
- The single biggest practical payoff is testability: a fake or in-memory implementation of the interface lets you test business logic with zero real infrastructure.
- Don't invert every dependency reflexively — reserve it for genuine seams where swapping the implementation (for testing, for a new technology, for a different environment) is a real, anticipated need.
- DIP is the principle that ties the rest of SOLID together: [SOLID — Open/Closed](0990-solid-open-closed.md)'s new implementations and [SOLID — Interface Segregation](0992-solid-interface-segregation.md)'s focused interfaces are exactly what gets passed across a DIP-inverted boundary.
