---
card: spring-data
gi: 58
slug: projections-dto-interface
title: "Projections (DTO & interface)"
---

## 1. What it is

A projection lets a repository method return only a subset of an entity's fields instead of the whole entity — either as an **interface projection** (a plain interface with getter methods matching the property names you want) or a **DTO (class) projection** (a plain constructor whose parameters Spring Data binds by name/position). Spring Data JPA generates the implementation at runtime for interfaces, and uses constructor-matching for DTOs; either way, only the requested columns are fetched.

```java
interface OrderSummary {
    Long getId();
    double getTotal();
}

List<OrderSummary> findByStatus(String status);
```

## 2. Why & when

Earlier cards covered open/closed and dynamic projections at a conceptual level as part of Spring Data Commons. This card is the JPA-specific mechanics: how an interface projection actually causes JPA to generate a narrower `SELECT` (only the getters you declare), and how a DTO projection's constructor becomes the shape of a JPQL `SELECT new com.example.OrderSummary(o.id, o.total) FROM Order o` under the hood.

Reach for a projection instead of returning the full entity when:

- A list or summary view only needs a few fields, and fetching entire entities (including large columns or lazy relationships that might trigger extra queries) would waste bandwidth and database work.
- You want the query itself to select fewer columns — a closed interface projection (every getter matches a real property, no derived methods) lets the JPA provider generate a `SELECT id, total FROM orders` instead of `SELECT * FROM orders`.
- You need a genuinely independent, decoupled shape (a DTO) to hand across a service boundary or serialize as an API response, rather than exposing the entity's own structure.

## 3. Core concept

```
 Entity:  Order { id, total, status, customer, lineItems, createdAt, ... }

 Interface projection:
   interface OrderSummary { Long getId(); double getTotal(); }
   -> generates: SELECT o.id, o.total FROM Order o WHERE o.status = ?

 DTO projection:
   record OrderSummaryDto(Long id, double total) {}
   -> generates: SELECT new com.example.OrderSummaryDto(o.id, o.total) FROM Order o WHERE o.status = ?

 Both: only 2 columns fetched, NOT the full Order row.
```

Both projection styles narrow the `SELECT` to the fields actually requested — the difference is only in how you declare the shape (interface getters vs. constructor parameters).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Interface and DTO projections both narrow the generated SELECT to fewer columns">
  <rect x="10" y="15" width="180" height="130" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="35" fill="#e6edf3" font-size="10.5" text-anchor="middle" font-family="sans-serif">Order entity</text>
  <text x="100" y="55" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">id, total, status,</text>
  <text x="100" y="68" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">customer, lineItems,</text>
  <text x="100" y="81" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">createdAt, ...</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">interface OrderSummary</text>
  <text x="330" y="56" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">getId(), getTotal()</text>

  <rect x="240" y="95" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="117" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">record OrderSummaryDto</text>
  <text x="330" y="131" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">(Long id, double total)</text>

  <rect x="460" y="55" width="170" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="545" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SELECT id, total</text>
  <text x="545" y="91" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">FROM orders WHERE ...</text>

  <line x1="190" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="1.3" marker-end="url(#pr)"/>
  <line x1="190" y1="100" x2="235" y2="120" stroke="#8b949e" stroke-width="1.3" marker-end="url(#pr)"/>
  <line x1="420" y1="45" x2="455" y2="70" stroke="#8b949e" stroke-width="1.3" marker-end="url(#pr)"/>
  <line x1="420" y1="120" x2="455" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#pr)"/>
  <defs><marker id="pr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both projection shapes cause the same narrower query — the fields you declare, and no more.

## 5. Runnable example

The scenario: an order repository serving a summary view, evolving from an interface projection, to a DTO projection, to a nested/closed projection that also reaches into a related entity's field.

### Level 1 — Basic

Model an interface projection with a simulated repository that only copies the requested fields — standing in for the narrower `SELECT` a real closed interface projection generates.

```java
import java.util.*;
import java.util.stream.*;

class Order {
    Long id; double total; String status;
    Order(Long id, double total, String status) { this.id = id; this.total = total; this.status = status; }
}

// interface OrderSummary { Long getId(); double getTotal(); }
interface OrderSummary {
    Long getId();
    double getTotal();
}

class OrderSummaryView implements OrderSummary {
    private final Long id; private final double total;
    OrderSummaryView(Long id, double total) { this.id = id; this.total = total; }
    public Long getId() { return id; }
    public double getTotal() { return total; }
    public String toString() { return "OrderSummary{id=" + id + ", total=" + total + "}"; }
}

public class ProjectionLevel1 {
    static List<OrderSummary> findByStatus(List<Order> data, String status) {
        return data.stream()
            .filter(o -> o.status.equals(status))
            .map(o -> (OrderSummary) new OrderSummaryView(o.id, o.total)) // only id+total copied
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1L, 50, "SHIPPED"),
            new Order(2L, 150, "PENDING")
        );
        List<OrderSummary> results = findByStatus(orders, "SHIPPED");
        System.out.println(results);
    }
}
```

How to run: `java ProjectionLevel1.java`

`OrderSummary` declares only two getters, matching two of `Order`'s many fields. A real Spring Data repository method `List<OrderSummary> findByStatus(String status)` would cause the JPA provider to generate `SELECT o.id, o.total FROM orders o WHERE status = ?` — never fetching `status` itself or any other column. Here, `OrderSummaryView` plays the role of the runtime proxy Spring Data generates automatically.

### Level 2 — Intermediate

Add a DTO (class/record) projection alongside the interface one, and compare the two declaration styles for the same narrowed shape.

```java
import java.util.*;
import java.util.stream.*;

class Order {
    Long id; double total; String status;
    Order(Long id, double total, String status) { this.id = id; this.total = total; this.status = status; }
}

interface OrderSummary {
    Long getId();
    double getTotal();
}

class OrderSummaryView implements OrderSummary {
    private final Long id; private final double total;
    OrderSummaryView(Long id, double total) { this.id = id; this.total = total; }
    public Long getId() { return id; }
    public double getTotal() { return total; }
    public String toString() { return "OrderSummary{id=" + id + ", total=" + total + "}"; }
}

// record OrderSummaryDto(Long id, double total) {}
record OrderSummaryDto(Long id, double total) {}

public class ProjectionLevel2 {
    static List<OrderSummary> findByStatusInterface(List<Order> data, String status) {
        return data.stream().filter(o -> o.status.equals(status))
            .map(o -> (OrderSummary) new OrderSummaryView(o.id, o.total))
            .collect(Collectors.toList());
    }

    // DTO projection: Spring Data matches this constructor by parameter name/type in a real @Query.
    static List<OrderSummaryDto> findByStatusDto(List<Order> data, String status) {
        return data.stream().filter(o -> o.status.equals(status))
            .map(o -> new OrderSummaryDto(o.id, o.total))
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1L, 50, "SHIPPED"),
            new Order(2L, 150, "PENDING")
        );
        System.out.println("Interface: " + findByStatusInterface(orders, "SHIPPED"));
        System.out.println("DTO:       " + findByStatusDto(orders, "SHIPPED"));
    }
}
```

How to run: `java ProjectionLevel2.java`

The DTO version (`OrderSummaryDto`) is a plain immutable record — no interface, no runtime proxy needed, because the JPA provider constructs it directly via `SELECT new ...OrderSummaryDto(o.id, o.total) FROM Order o` (JPQL constructor expression). Both approaches fetch the identical two columns; the choice is about whether you want a generated proxy (interface, slightly more flexible, supports open projections with `@Value` SpEL) or a concrete, easily-serializable class (DTO, simpler to reason about, works well as an API response type).

### Level 3 — Advanced

Add a **nested closed projection** that reaches into a related entity (`Customer`), simulating how a real interface projection can expose a nested interface for an association without fetching the whole related entity.

```java
import java.util.*;
import java.util.stream.*;

class Customer {
    Long id; String name;
    Customer(Long id, String name) { this.id = id; this.name = name; }
}

class Order {
    Long id; double total; String status; Customer customer;
    Order(Long id, double total, String status, Customer customer) {
        this.id = id; this.total = total; this.status = status; this.customer = customer;
    }
}

interface CustomerName { String getName(); }

// Nested closed projection: reaches into the related Customer, but ONLY its name.
interface OrderWithCustomer {
    Long getId();
    double getTotal();
    CustomerName getCustomer();
}

class CustomerNameView implements CustomerName {
    private final String name;
    CustomerNameView(String name) { this.name = name; }
    public String getName() { return name; }
    public String toString() { return name; }
}

class OrderWithCustomerView implements OrderWithCustomer {
    private final Long id; private final double total; private final CustomerName customer;
    OrderWithCustomerView(Long id, double total, CustomerName customer) {
        this.id = id; this.total = total; this.customer = customer;
    }
    public Long getId() { return id; }
    public double getTotal() { return total; }
    public CustomerName getCustomer() { return customer; }
    public String toString() {
        return "Order{id=" + id + ", total=" + total + ", customer=" + customer + "}";
    }
}

public class ProjectionLevel3 {
    static List<OrderWithCustomer> findByStatusWithCustomer(List<Order> data, String status) {
        return data.stream().filter(o -> o.status.equals(status))
            .map(o -> (OrderWithCustomer) new OrderWithCustomerView(
                o.id, o.total, new CustomerNameView(o.customer.name)))
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1L, 50, "SHIPPED", new Customer(10L, "Ada Lovelace")),
            new Order(2L, 150, "PENDING", new Customer(11L, "Alan Turing"))
        );
        System.out.println(findByStatusWithCustomer(orders, "SHIPPED"));
    }
}
```

How to run: `java ProjectionLevel3.java`

`OrderWithCustomer.getCustomer()` returns another projection interface (`CustomerName`), not the full `Customer` entity — this stays a *closed* projection (every leaf getter maps to a real column) because Spring Data can still generate a single `SELECT o.id, o.total, c.name FROM Order o JOIN o.customer c`, joining just far enough to grab `name` without loading the rest of `Customer`.

## 6. Walkthrough

Execution starts in `main` with two `Order` objects, each carrying a nested `Customer`. `findByStatusWithCustomer(orders, "SHIPPED")` filters the list down to order 1 first (matching `status == "SHIPPED"`).

For that matching order, the mapping step constructs a `CustomerNameView` from `o.customer.name` ("Ada Lovelace") — standing in for the join Spring Data would generate to reach the customer's name — then wraps `id`, `total`, and that nested view into an `OrderWithCustomerView`.

The resulting list, `[Order{id=1, total=50, customer=Ada Lovelace}]`, is printed. Order 2 never reaches the mapping step because it fails the `status.equals("SHIPPED")` filter first — mirroring how a real `WHERE status = ?` clause excludes non-matching rows before any column is even selected.

```
Order{id=1, status=SHIPPED, customer=Ada}  --passes filter-->  OrderWithCustomerView{id=1, total=50, customer=Ada}
Order{id=2, status=PENDING, customer=Alan} --filtered out-->  (excluded)
```

In a real Spring Data JPA repository, `List<OrderWithCustomer> findByStatus(String status)` would translate roughly to `SELECT o.id, o.total, c.name FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = ?` — the database does the join and column-narrowing, and Spring Data wraps each result row in a generated proxy implementing `OrderWithCustomer` (and a nested proxy for `getCustomer()`), so the calling code sees plain Java objects, never a `ResultSet`.

## 7. Gotchas & takeaways

> Gotcha: an interface projection stops being "closed" (and loses its narrower-`SELECT` benefit) the moment one of its methods uses a SpEL expression like `@Value("#{target.firstName + ' ' + target.lastName}")` — that becomes an *open* projection, which requires the full entity to be fetched first so the expression has something to evaluate against.

- Interface projections are declared as getters; Spring Data implements them at runtime with a generated proxy.
- DTO (class/record) projections are declared as a constructor; Spring Data matches query result columns to constructor parameters.
- A closed projection (every getter maps directly to a property, no SpEL) lets the underlying query select only those columns — the real performance win.
- Nested projections can reach into associations without loading the full related entity, as long as they stay closed all the way down.
