---
card: spring-data
gi: 61
slug: stored-procedures-procedure
title: "Stored procedures (@Procedure)"
---

## 1. What it is

`@Procedure` lets a Spring Data JPA repository method call a database stored procedure directly, mapping Java method parameters to the procedure's IN parameters and its return value (or OUT parameters) back to a Java type — without hand-writing `EntityManager.createStoredProcedureQuery(...)` boilerplate.

```java
@Procedure(procedureName = "calculate_order_total")
BigDecimal calculateOrderTotal(@Param("order_id") Long orderId);
```

## 2. Why & when

Every prior JPA card (JPQL, native SQL, Criteria, Querydsl) builds queries from the Java/JPA side. Stored procedures flip that: business logic already lives in the database as a named procedure, usually because a DBA-managed system, a legacy schema, or a performance-critical batch operation was built that way before or independently of the application. `@Procedure` is the thin bridge that lets a repository invoke that existing procedure like any other repository method.

Reach for `@Procedure` specifically when:

- A stored procedure already exists in the database (written by a DBA, shared across multiple applications, or performing a bulk operation more efficiently in the database engine) and you need to call it from Java.
- The computation genuinely belongs in the database — e.g., a recalculation that must run atomically as part of a larger PL/SQL batch job already scheduled at the database level.
- You want the procedure call to look like a normal repository method to the rest of the codebase, rather than exposing raw `EntityManager` or JDBC calls throughout the service layer.

## 3. Core concept

```
 Database:
   CREATE PROCEDURE calculate_order_total(IN order_id BIGINT, OUT total DECIMAL)
   ...

 Repository:
   interface OrderRepository extends JpaRepository<Order, Long> {
       @Procedure(procedureName = "calculate_order_total")
       BigDecimal calculateOrderTotal(@Param("order_id") Long orderId);
   }

 Call:
   BigDecimal total = orderRepository.calculateOrderTotal(42L);
   -- Spring Data maps orderId -> IN param, procedure's OUT param -> BigDecimal return value
```

`@Procedure` handles the IN/OUT parameter binding so the procedure call reads like any other repository method.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A repository method call maps to IN and OUT parameters of a database stored procedure">
  <rect x="20" y="50" width="220" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="72" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">calculateOrderTotal(42L)</text>
  <text x="130" y="87" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Java method call</text>

  <rect x="400" y="50" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="72" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">calculate_order_total(...)</text>
  <text x="510" y="87" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">DB stored procedure</text>

  <line x1="240" y1="65" x2="395" y2="65" stroke="#8b949e" stroke-width="1.4" marker-end="url(#sp)"/>
  <text x="317" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">IN: order_id=42</text>
  <line x1="395" y1="85" x2="240" y2="85" stroke="#8b949e" stroke-width="1.4" marker-end="url(#sp)"/>
  <text x="317" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OUT: total -&gt; BigDecimal</text>
  <defs><marker id="sp" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The Java call sends IN parameters and receives the procedure's OUT parameter (or return value) mapped straight back to a Java type.

## 5. Runnable example

The scenario: recalculating an order's total via a "stored procedure," evolving from a single hard-coded procedure call, to a parameterized repository-shaped wrapper, to a version returning multiple OUT values via a small result record.

### Level 1 — Basic

Simulate a stored procedure as a plain Java method (since a single-file example cannot run a real database), called the way `@Procedure` would wire it.

```java
import java.math.BigDecimal;
import java.util.*;

// Stands in for: CREATE PROCEDURE calculate_order_total(IN order_id BIGINT, OUT total DECIMAL)
class OrderDatabase {
    private final Map<Long, List<BigDecimal>> lineItemPrices = Map.of(
        1L, List.of(new BigDecimal("19.99"), new BigDecimal("5.00")),
        2L, List.of(new BigDecimal("100.00"))
    );

    BigDecimal calculateOrderTotalProcedure(long orderId) {
        return lineItemPrices.getOrDefault(orderId, List.of())
            .stream().reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}

public class ProcedureLevel1 {
    // interface OrderRepository { @Procedure(procedureName = "calculate_order_total")
    //                              BigDecimal calculateOrderTotal(@Param("order_id") Long orderId); }
    public static void main(String[] args) {
        OrderDatabase db = new OrderDatabase();
        BigDecimal total = db.calculateOrderTotalProcedure(1L);
        System.out.println("Order 1 total: " + total);
    }
}
```

How to run: `java ProcedureLevel1.java`

`calculateOrderTotalProcedure` plays the role of the database-side stored procedure; a real `@Procedure`-annotated repository method would send `orderId` as the procedure's `order_id` IN parameter and receive the computed total back — the calling code never sees SQL or PL/SQL, only a Java method call returning `BigDecimal`.

### Level 2 — Intermediate

Wrap the simulated procedure behind a repository-shaped class, matching how `@Procedure` presents it to the rest of the application as an ordinary repository method.

```java
import java.math.BigDecimal;
import java.util.*;

class OrderDatabase {
    private final Map<Long, List<BigDecimal>> lineItemPrices = Map.of(
        1L, List.of(new BigDecimal("19.99"), new BigDecimal("5.00")),
        2L, List.of(new BigDecimal("100.00"))
    );
    BigDecimal calculateOrderTotalProcedure(long orderId) {
        return lineItemPrices.getOrDefault(orderId, List.of())
            .stream().reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}

// interface OrderRepository extends JpaRepository<Order, Long> {
//     @Procedure(procedureName = "calculate_order_total")
//     BigDecimal calculateOrderTotal(@Param("order_id") Long orderId);
// }
class OrderRepository {
    private final OrderDatabase db;
    OrderRepository(OrderDatabase db) { this.db = db; }
    BigDecimal calculateOrderTotal(Long orderId) {
        return db.calculateOrderTotalProcedure(orderId);
    }
}

public class ProcedureLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository(new OrderDatabase());
        System.out.println("Order 1 total: " + repo.calculateOrderTotal(1L));
        System.out.println("Order 2 total: " + repo.calculateOrderTotal(2L));
    }
}
```

How to run: `java ProcedureLevel2.java`

`OrderRepository.calculateOrderTotal` is what application code actually calls — it looks identical to any derived-query or `@Query` repository method, even though underneath it invokes a stored procedure rather than issuing a `SELECT`. This is the point of `@Procedure`: procedure calls integrate into the repository abstraction like everything else.

### Level 3 — Advanced

Model a procedure with *multiple* OUT parameters (total and item count) by returning a small result record, and add basic handling for an order that doesn't exist (no rows to reduce).

```java
import java.math.BigDecimal;
import java.util.*;

// Stands in for two OUT parameters: OUT total DECIMAL, OUT item_count INT
record OrderTotals(BigDecimal total, int itemCount) {}

class OrderDatabase {
    private final Map<Long, List<BigDecimal>> lineItemPrices = Map.of(
        1L, List.of(new BigDecimal("19.99"), new BigDecimal("5.00")),
        2L, List.of(new BigDecimal("100.00"))
    );

    // CREATE PROCEDURE calculate_order_totals(IN order_id BIGINT, OUT total DECIMAL, OUT item_count INT)
    Optional<OrderTotals> calculateOrderTotalsProcedure(long orderId) {
        List<BigDecimal> prices = lineItemPrices.get(orderId);
        if (prices == null) return Optional.empty(); // no such order -> procedure returns no rows
        BigDecimal total = prices.stream().reduce(BigDecimal.ZERO, BigDecimal::add);
        return Optional.of(new OrderTotals(total, prices.size()));
    }
}

class OrderRepository {
    private final OrderDatabase db;
    OrderRepository(OrderDatabase db) { this.db = db; }

    // @Procedure(procedureName = "calculate_order_totals")
    // OrderTotals calculateOrderTotals(@Param("order_id") Long orderId);
    Optional<OrderTotals> calculateOrderTotals(Long orderId) {
        return db.calculateOrderTotalsProcedure(orderId);
    }
}

public class ProcedureLevel3 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository(new OrderDatabase());

        repo.calculateOrderTotals(1L).ifPresentOrElse(
            t -> System.out.println("Order 1: total=" + t.total() + ", items=" + t.itemCount()),
            () -> System.out.println("Order 1 not found")
        );

        repo.calculateOrderTotals(999L).ifPresentOrElse(
            t -> System.out.println("Order 999: total=" + t.total() + ", items=" + t.itemCount()),
            () -> System.out.println("Order 999 not found")
        );
    }
}
```

How to run: `java ProcedureLevel3.java`

`OrderTotals` models a procedure with two OUT parameters bundled into one Java return type — a common pattern with `@Procedure` when the underlying procedure produces more than a single scalar value. Wrapping the result in `Optional` also handles the case where the procedure legitimately finds nothing for a given ID, rather than letting a missing order surface as a null-pointer failure downstream.

## 6. Walkthrough

Execution starts in `main`. First, `repo.calculateOrderTotals(1L)` is called. Inside, `db.calculateOrderTotalsProcedure(1L)` looks up `lineItemPrices.get(1L)`, finds two prices (`19.99`, `5.00`), reduces them to a total of `24.99`, and returns `Optional.of(new OrderTotals(24.99, 2))`.

Back in `main`, `ifPresentOrElse` takes the present branch since the `Optional` is non-empty, printing `Order 1: total=24.99, items=2`.

Next, `repo.calculateOrderTotals(999L)` runs the same path, but `lineItemPrices.get(999L)` returns `null` (no such key), so `calculateOrderTotalsProcedure` returns `Optional.empty()` immediately — standing in for the stored procedure producing no OUT values because no matching order exists in the database. `ifPresentOrElse` takes the absent branch this time, printing `Order 999 not found`.

```
calculateOrderTotals(1L)     -> found  -> OrderTotals(24.99, 2)  -> "Order 1: total=24.99, items=2"
calculateOrderTotals(999L)   -> absent -> Optional.empty()       -> "Order 999 not found"
```

In a real Spring Data JPA repository, `orderRepository.calculateOrderTotals(1L)` would trigger `EntityManager.createStoredProcedureQuery("calculate_order_totals")` internally: bind `1L` to the `order_id` IN parameter, execute the procedure against the database, and map its `total`/`item_count` OUT parameters into the returned Java object — from a controller's perspective, calling this repository method is indistinguishable from calling any other query method, even though a stored procedure executes underneath.

## 7. Gotchas & takeaways

> Gotcha: if the stored procedure's parameter names in the database don't exactly match what `@Param` declares (or positional binding is used inconsistently), the call fails at runtime with a parameter-binding error — procedure signatures are not checked at compile time the way a Java method signature would be.

- `@Procedure` binds Java method parameters to a stored procedure's IN parameters, and its OUT parameter(s)/return value back to the Java return type.
- Reach for it when the logic already lives in the database as a procedure — not as a way to introduce new business logic into the database from scratch.
- Multiple OUT parameters typically map into a small dedicated result type, not a single scalar return value.
- Wrap the result in `Optional` (or check for an empty result) when the procedure can legitimately produce nothing for a given input.
