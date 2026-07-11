---
card: spring-data
gi: 93
slug: databaseclient-reactive
title: "DatabaseClient (reactive)"
---

## 1. What it is

`DatabaseClient` is the reactive, lower-level SQL execution API that `R2dbcEntityTemplate` itself is built on top of — the reactive counterpart to plain `JdbcTemplate`. Where `R2dbcEntityTemplate` works in terms of mapped entities, `DatabaseClient` works in terms of raw SQL strings and manual row mapping, giving full control when neither a repository method nor the entity template's fluent API fits.

```java
@Autowired DatabaseClient client;

Flux<Order> orders = client.sql("SELECT id, status FROM orders WHERE total > :minTotal")
    .bind("minTotal", 100.0)
    .map(row -> new Order(row.get("id", Long.class), row.get("status", String.class)))
    .all();
```

## 2. Row of abstraction

```
 orderRepository.findByStatus(status)      <- highest level: generated, entity-mapped
        |
 R2dbcEntityTemplate.select(Order.class)   <- mid level: entity-mapped, fluent Criteria
        |
 DatabaseClient.sql("SELECT ...")           <- lowest level: raw SQL, manual row mapping
```

Each layer is built on the one below it — `DatabaseClient` is where raw SQL strings and manual `Row`-to-object mapping live, exactly mirroring `JdbcTemplate`'s role beneath `JdbcAggregateTemplate` on the blocking side.

## 2. Why & when

The previous card established that `R2dbcEntityTemplate` is what generated repository methods delegate to; `DatabaseClient` is one further level down — the same relationship `JdbcTemplate` has beneath `JdbcAggregateTemplate`. Reaching this low is for genuinely raw SQL needs: complex joins across differently-shaped result sets, or SQL that doesn't map cleanly onto any single mapped entity at all.

Reach for `DatabaseClient` directly specifically when:

- A query's result shape doesn't correspond to any single mapped entity — a report combining columns from several tables into an ad hoc row shape, better modeled as manual mapping than as a synthetic entity class.
- You need complete control over the SQL text itself, including database-specific syntax that neither derived queries nor the Criteria API (covered next) can express.
- You're building the lowest layer of a custom repository fragment, and even `R2dbcEntityTemplate`'s entity-oriented operations don't fit — `DatabaseClient` is the most general reactive SQL execution tool available.

## 3. Core concept

```
 client.sql("SELECT id, status, total FROM orders WHERE total > :minTotal")
       .bind("minTotal", 100.0)          -- named parameter binding, avoids SQL injection
       .map(row -> new OrderSummary(     -- MANUAL row-to-object mapping, no entity metadata involved
           row.get("id", Long.class),
           row.get("status", String.class),
           row.get("total", Double.class)))
       .all()                             -- returns Flux<OrderSummary>
```

`DatabaseClient` gives full control over both the SQL text and the row-mapping logic, at the cost of writing both by hand.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Three layers of abstraction from generated repository down to raw SQL via DatabaseClient">
  <rect x="20" y="15" width="600" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="40" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">orderRepository.findByStatus(...) -- generated, entity-mapped</text>

  <rect x="20" y="70" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="95" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">R2dbcEntityTemplate.select(...).matching(...) -- entity-mapped, fluent</text>

  <rect x="20" y="125" width="600" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="150" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">DatabaseClient.sql("...").map(row -&gt; ...) -- raw SQL, manual mapping</text>

  <line x1="320" y1="55" x2="320" y2="65" stroke="#8b949e" stroke-width="1.3" marker-end="url(#dc)"/>
  <line x1="320" y1="110" x2="320" y2="120" stroke="#8b949e" stroke-width="1.3" marker-end="url(#dc)"/>
  <defs><marker id="dc" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each layer is built on the one beneath it — `DatabaseClient` is the lowest, most general layer, working directly with SQL text and rows.

## 5. Runnable example

The scenario: an ad hoc reporting query combining orders and a computed aggregate, evolving from a plain entity-mapped baseline, to a raw-SQL-and-manual-mapping approach for a shape no entity represents, to parameterized binding guarding against SQL injection.

### Level 1 — Basic

Show the entity-mapped baseline for contrast: a query result that maps cleanly onto `Order` itself.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

public class DatabaseClientLevel1 {
    // Entity-mapped: the result IS an Order, nothing extra.
    static CompletableFuture<List<Order>> findByStatus(List<Order> data, String status) {
        return CompletableFuture.supplyAsync(() ->
            data.stream().filter(o -> o.status.equals(status)).collect(Collectors.toList()));
    }

    public static void main(String[] args) throws Exception {
        List<Order> orders = List.of(new Order(1, "SHIPPED", 50), new Order(2, "SHIPPED", 150));
        List<Order> found = findByStatus(orders, "SHIPPED").get();
        System.out.println("Entity-mapped result: " + found.size() + " Order objects");
    }
}
```

How to run: `java DatabaseClientLevel1.java`

The result is directly a `List<Order>` — a shape the repository or entity template layer handles perfectly well, with no need to drop down to raw SQL at all.

### Level 2 — Intermediate

Introduce a report shape that no single entity represents — a combination of a status, a count, and an average total — matching the kind of query `DatabaseClient` is for, with manual row-to-object mapping.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

// No entity represents this shape -- it's an ad hoc aggregate report row.
record StatusSummary(String status, long count, double averageTotal) {}

// Stands in for a raw database Row -- DatabaseClient's .map(row -> ...) receives something like this.
class Row {
    private final Map<String, Object> values;
    Row(Map<String, Object> values) { this.values = values; }
    <T> T get(String column, Class<T> type) { return type.cast(values.get(column)); }
}

public class DatabaseClientLevel2 {
    // Simulates: client.sql("SELECT status, COUNT(*) c, AVG(total) avg_total FROM orders GROUP BY status")
    //                  .map(row -> new StatusSummary(row.get("status", String.class), ...)).all()
    static CompletableFuture<List<StatusSummary>> statusSummaryReport(List<Order> data) {
        return CompletableFuture.supplyAsync(() -> {
            Map<String, List<Order>> byStatus = data.stream().collect(Collectors.groupingBy(o -> o.status));
            List<Row> simulatedRows = byStatus.entrySet().stream()
                .map(e -> new Row(Map.of(
                    "status", e.getKey(),
                    "c", (long) e.getValue().size(),
                    "avg_total", e.getValue().stream().mapToDouble(o -> o.total).average().orElse(0))))
                .collect(Collectors.toList());

            // Manual row mapping -- exactly what a real .map(row -> ...) lambda does with a real Row.
            return simulatedRows.stream()
                .map(row -> new StatusSummary(row.get("status", String.class), row.get("c", Long.class), row.get("avg_total", Double.class)))
                .collect(Collectors.toList());
        });
    }

    public static void main(String[] args) throws Exception {
        List<Order> orders = List.of(
            new Order(1, "SHIPPED", 50), new Order(2, "SHIPPED", 150), new Order(3, "PENDING", 200)
        );
        List<StatusSummary> report = statusSummaryReport(orders).get();
        for (StatusSummary s : report) System.out.println(s.status() + ": count=" + s.count() + ", avg=" + s.averageTotal());
    }
}
```

How to run: `java DatabaseClientLevel2.java`

`StatusSummary` has no corresponding mapped entity — it's an ad hoc aggregate shape, exactly the case where `DatabaseClient`'s raw-SQL-plus-manual-mapping approach fits better than any entity-oriented repository method or `R2dbcEntityTemplate` query, since there's no single entity type to select into.

### Level 3 — Advanced

Add named-parameter binding, matching `DatabaseClient`'s `.bind(name, value)` mechanism, which safely parameterizes a raw SQL string instead of concatenating user input directly into it.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }
record StatusSummary(String status, long count, double averageTotal) {}

class Row {
    private final Map<String, Object> values;
    Row(Map<String, Object> values) { this.values = values; }
    <T> T get(String column, Class<T> type) { return type.cast(values.get(column)); }
}

// Stands in for DatabaseClient's fluent sql(...).bind(...).map(...).all() chain.
class SqlSpec {
    private final List<Order> data;
    private final Map<String, Object> boundParams = new HashMap<>();
    SqlSpec(List<Order> data) { this.data = data; }

    SqlSpec bind(String name, Object value) { boundParams.put(name, value); return this; } // NAMED, not string-concatenated

    CompletableFuture<List<StatusSummary>> statusSummaryAbove() {
        return CompletableFuture.supplyAsync(() -> {
            double minTotal = (double) boundParams.get("minTotal"); // bound value used SAFELY, no string concatenation
            System.out.println("  SQL: SELECT status, COUNT(*), AVG(total) FROM orders WHERE total > :minTotal GROUP BY status"
                + "  [minTotal=" + minTotal + "]");

            Map<String, List<Order>> byStatus = data.stream()
                .filter(o -> o.total > minTotal)
                .collect(Collectors.groupingBy(o -> o.status));

            return byStatus.entrySet().stream()
                .map(e -> new StatusSummary(e.getKey(), e.getValue().size(),
                    e.getValue().stream().mapToDouble(o -> o.total).average().orElse(0)))
                .collect(Collectors.toList());
        });
    }
}

public class DatabaseClientLevel3 {
    public static void main(String[] args) throws Exception {
        List<Order> orders = List.of(
            new Order(1, "SHIPPED", 50), new Order(2, "SHIPPED", 150),
            new Order(3, "PENDING", 200), new Order(4, "PENDING", 30)
        );

        SqlSpec spec = new SqlSpec(orders).bind("minTotal", 100.0); // named binding, injection-safe
        List<StatusSummary> report = spec.statusSummaryAbove().get();

        for (StatusSummary s : report) System.out.println(s.status() + ": count=" + s.count() + ", avg=" + s.averageTotal());
    }
}
```

How to run: `java DatabaseClientLevel3.java`

`.bind("minTotal", 100.0)` supplies the parameter by name, never concatenated directly into the SQL string — the printed SQL shows `:minTotal` as a named marker with the bound value reported separately, exactly matching how `DatabaseClient.sql(...).bind(...)` protects against SQL injection while still allowing fully raw, hand-written SQL text.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `orders` is built with four entries across two statuses, and `spec = new SqlSpec(orders).bind("minTotal", 100.0)` constructs the query specification, storing `100.0` in `boundParams` under the key `"minTotal"` — no SQL has executed yet at this point, mirroring how a real `DatabaseClient.sql(...).bind(...)` chain builds up a request object before anything runs against the database.

`spec.statusSummaryAbove()` is then called. Inside, `minTotal` is read back out of `boundParams` (`100.0`), and the simulated SQL string is printed showing the parameter marker `:minTotal` alongside its bound value — demonstrating that the actual value was carried alongside the query text as data, not spliced into the string itself.

The filtering step then keeps only orders where `total > 100.0`: order 2 (`SHIPPED`, `150`) and order 3 (`PENDING`, `200`) pass; order 1 (`50`) and order 4 (`30`) are excluded. `Collectors.groupingBy(o -> o.status)` partitions the two survivors into `SHIPPED -> [order2]` and `PENDING -> [order3]`. The final `.map(...)` step computes, for each group, its size and average total, producing two `StatusSummary` records: `("SHIPPED", 1, 150.0)` and `("PENDING", 1, 200.0)`.

Back in `main`, the loop prints both summaries, confirming only orders above the `100.0` threshold contributed to the report.

```
bind("minTotal", 100.0)  -- stored as a NAMED parameter, not concatenated into SQL text

statusSummaryAbove():
  filter total > 100.0  -> [order2(SHIPPED,150), order3(PENDING,200)]
  groupBy status         -> SHIPPED=[order2], PENDING=[order3]
  map to StatusSummary    -> [("SHIPPED",1,150.0), ("PENDING",1,200.0)]
```

In a real Spring Data R2DBC application, `databaseClient.sql("SELECT status, COUNT(*) c, AVG(total) avg_total FROM orders WHERE total > :minTotal GROUP BY status").bind("minTotal", 100.0).map(row -> new StatusSummary(row.get("status", String.class), row.get("c", Long.class), row.get("avg_total", Double.class))).all()` sends that parameterized SQL to the database over a non-blocking R2DBC connection, and the `.map(row -> ...)` lambda runs once per returned row, manually constructing a `StatusSummary` from named columns — there is no entity metadata, no automatic mapping convention involved at all; the developer is fully responsible for both the SQL text and the row-to-object translation, in exchange for complete control over both.

## 7. Gotchas & takeaways

> Gotcha: `DatabaseClient`'s raw SQL is not portable the same way JPQL nominally is — it's exactly as vendor-specific as the SQL text you write, so a query relying on a particular database's syntax needs review (or rewriting) before running against a different database engine, same caveat as native `@Query` SQL on the JDBC module.

- `DatabaseClient` is the lowest-level reactive SQL execution API — `R2dbcEntityTemplate` (and everything generated repositories delegate to) is itself built on top of it.
- Reach for it when a query's result shape doesn't map onto any single entity, or when you need full control over both the SQL text and row-to-object mapping.
- Always use named parameter binding (`.bind(name, value)`) rather than string-concatenating values into the SQL text — this is the reactive module's equivalent safeguard against SQL injection.
- This is a genuinely lower-level, more manual tool than either a repository method or `R2dbcEntityTemplate`'s fluent Criteria API — reach for it only when those higher layers don't fit.
