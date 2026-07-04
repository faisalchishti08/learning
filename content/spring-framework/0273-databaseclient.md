---
card: spring-framework
gi: 273
slug: databaseclient
title: DatabaseClient
---

## 1. What it is

`DatabaseClient` is Spring's **reactive JDBC template** — a fluent, non-blocking SQL client built on R2DBC. It wraps raw R2DBC `Connection` and `Statement` lifecycle the same way `JdbcTemplate` wraps JDBC, returning `Mono<T>` and `Flux<T>` instead of blocking results.

```java
// SELECT → Flux of domain objects
Flux<Order> orders = client.sql("SELECT * FROM orders WHERE status = :s")
    .bind("s", "OPEN")
    .map(row -> new Order(row.get("id", Long.class), row.get("total", Double.class)))
    .all();

// INSERT → Mono<Long> of rows updated
Mono<Long> inserted = client.sql("INSERT INTO orders(total,status) VALUES(:total,:status)")
    .bind("total", 99.0).bind("status","OPEN")
    .fetch().rowsUpdated();
```

`DatabaseClient` was introduced in Spring Framework 5.3 and lives in `org.springframework.r2dbc.core`.

## 2. Why & when

`DatabaseClient` is the entry point for R2DBC-based database access in Spring applications. It:
- Manages `Connection` acquisition and release from a `ConnectionFactory`.
- Translates R2DBC exceptions to Spring's `DataAccessException` hierarchy.
- Supports named parameters (`:name`) transparently — internally rewrites to positional syntax.
- Integrates with `@Transactional` via `ReactiveTransactionManager` and `R2dbcTransactionManager`.

Use `DatabaseClient` directly when:
- You need full SQL control (joins, aggregations, window functions).
- You're writing a reactive Spring WebFlux application.
- You want lightweight mapping without an ORM.

Use `R2dbcEntityTemplate` (built on `DatabaseClient`) for convention-based CRUD when entities map directly to tables.

## 3. Core concept

`DatabaseClient` spec chain:

```
DatabaseClient.create(connectionFactory)

  .sql(String)                          ← set SQL

Binding (choose one style):
  .bind("paramName", value)             ← named, one at a time
  .bind(index, value)                   ← positional (0-based index)
  .bindValues(Map<String,?>)            ← bulk named

Result fetch:
  .fetch()                              ← returns FetchSpec
    .all()   → Flux<Map<String,Object>> ← all rows
    .one()   → Mono<Map<String,Object>> ← exactly one (or empty Mono)
    .first() → Mono<Map<String,Object>> ← first row (ignores extras)
    .rowsUpdated() → Mono<Long>         ← for updates/inserts/deletes

  .map(rowMapper)                       ← transform Row → T BEFORE fetch
    .all() / .one() / .first()          ← same terminals on Flux<T>/Mono<T>
```

Key difference from `JdbcTemplate`:
- `DatabaseClient.map(fn).all()` — the mapping function receives a `Row` object (R2DBC) not a `ResultSet`.
- `Row.get("column", Class<T>)` reads a single column value by name and type.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- User code -->
  <rect x="10" y="75" width="120" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="98" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Your Code</text>
  <text x="70" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.sql().bind().map()</text>
  <text x="70" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Flux&lt;T&gt; / Mono&lt;T&gt;</text>

  <line x1="132" y1="105" x2="185" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DatabaseClient -->
  <rect x="187" y="45" width="210" height="120" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="292" y="68" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">DatabaseClient</text>
  <line x1="197" y1="74" x2="387" y2="74" stroke="#8b949e" stroke-width="0.5"/>
  <text x="292" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1. :name → $1 rewrite</text>
  <text x="292" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2. ConnectionFactory.create()</text>
  <text x="292" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">3. Statement.bind + execute</text>
  <text x="292" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">4. Result → Row → T</text>
  <text x="292" y="156" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">5. translate exceptions</text>

  <line x1="399" y1="105" x2="452" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- ConnectionFactory -->
  <rect x="454" y="75" width="200" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="554" y="98" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ConnectionFactory</text>
  <text x="554" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">r2dbc-h2 / r2dbc-pool</text>
  <text x="554" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Mono&lt;Connection&gt;</text>

  <!-- Return arrow -->
  <line x1="452" y1="130" x2="399" y2="130" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>
  <text x="425" y="148" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="monospace">Flux&lt;T&gt;</text>
</svg>

`DatabaseClient` reuses one `ConnectionFactory`, rewrites named params, and returns cold publishers.

## 5. Runnable example

Scenario: an **order management** system — insert orders, query with filters, update status, and demonstrate the `FetchSpec` terminal methods.

### Level 1 — Basic

Named params in INSERT + SELECT with `.fetch().all()` and `.map()`.

```java
// DatabaseClientDemo.java
import io.r2dbc.h2.*;
import org.springframework.r2dbc.core.DatabaseClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import java.util.Map;

public class DatabaseClientDemo {

    static DatabaseClient buildClient() {
        return DatabaseClient.create(new H2ConnectionFactory(
            H2ConnectionConfiguration.builder()
                .inMemory("orders").option("DB_CLOSE_DELAY=-1").build()));
    }

    public static void main(String[] args) {
        DatabaseClient client = buildClient();

        // Create schema
        client.sql("CREATE TABLE orders (id BIGINT AUTO_INCREMENT PRIMARY KEY, " +
                   "product VARCHAR(100), total DOUBLE, status VARCHAR(30))")
            .fetch().rowsUpdated().block();

        // INSERT — named params
        Flux.just(
            Map.of("product","Widget","total",49.99,"status","OPEN"),
            Map.of("product","Gadget","total",99.00,"status","OPEN"),
            Map.of("product","Sensor","total",199.99,"status","CLOSED")
        ).concatMap(row ->
            client.sql("INSERT INTO orders(product,total,status) VALUES(:product,:total,:status)")
                .bindValues(row).fetch().rowsUpdated()
        ).blockLast();

        // SELECT all — .fetch().all() → Flux<Map<String,Object>>
        System.out.println("All orders:");
        client.sql("SELECT id,product,total,status FROM orders ORDER BY id")
            .fetch().all()
            .doOnNext(r -> System.out.printf("  [%s] %-10s $%.2f  %s%n",
                r.get("ID"), r.get("PRODUCT"), r.get("TOTAL"), r.get("STATUS")))
            .blockLast();

        // SELECT with filter — named param
        Long openCount = client.sql("SELECT COUNT(*) cnt FROM orders WHERE status=:s")
            .bind("s","OPEN")
            .map(row -> row.get("cnt", Long.class))
            .one().block();
        System.out.println("Open orders: " + openCount);
    }
}
```

How to run: `java -cp spring-r2dbc.jar:r2dbc-spi.jar:r2dbc-h2.jar:reactor-core.jar:. DatabaseClientDemo.java`

`.bindValues(Map<String,?>)` binds all named params in one call. `.fetch().all()` returns `Flux<Map<String,Object>>` — column names are the `Map` keys (lowercase for H2 R2DBC). `.map(row -> ...)` before `.all()` transforms each `Row` to a typed object.

---

### Level 2 — Intermediate

`.map()` for domain objects + `.one()`, `.first()`, and update with `rowsUpdated()`.

```java
// DatabaseClientDemo.java
import io.r2dbc.h2.*;
import org.springframework.r2dbc.core.DatabaseClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import java.util.Map;

record Order(long id, String product, double total, String status) {}

public class DatabaseClientDemo {

    static DatabaseClient buildClient() {
        return DatabaseClient.create(new H2ConnectionFactory(
            H2ConnectionConfiguration.builder()
                .inMemory("orders").option("DB_CLOSE_DELAY=-1").build()));
    }

    static Order fromRow(io.r2dbc.spi.Row row) {
        return new Order(
            row.get("id", Long.class),
            row.get("product", String.class),
            row.get("total", Double.class),
            row.get("status", String.class));
    }

    public static void main(String[] args) {
        DatabaseClient client = buildClient();

        // Setup
        client.sql("CREATE TABLE orders (id BIGINT AUTO_INCREMENT PRIMARY KEY, " +
                   "product VARCHAR(100), total DOUBLE, status VARCHAR(30))")
            .fetch().rowsUpdated()
            .then(Flux.just(
                new Object[]{"Widget",49.99,"OPEN"},
                new Object[]{"Gadget",99.00,"OPEN"},
                new Object[]{"Sensor",199.99,"CLOSED"},
                new Object[]{"Relay",29.99,"OPEN"}
            ).concatMap(a -> client.sql(
                "INSERT INTO orders(product,total,status) VALUES(:p,:t,:s)")
                .bind("p",a[0]).bind("t",a[1]).bind("s",a[2]).fetch().rowsUpdated()
            ).then())
            .block();

        // .map() → Flux<Order>
        Flux<Order> openOrders = client.sql(
            "SELECT * FROM orders WHERE status=:s ORDER BY total DESC")
            .bind("s","OPEN")
            .map(row -> fromRow(row))
            .all();
        System.out.println("Open orders (high→low):");
        openOrders.doOnNext(o -> System.out.printf("  [%d] %-10s $%.2f%n",
            o.id(), o.product(), o.total())).blockLast();

        // .one() — expects exactly one row or empty
        Mono<Order> sensor = client.sql("SELECT * FROM orders WHERE product=:p")
            .bind("p","Sensor")
            .map(row -> fromRow(row))
            .one();
        System.out.println("Sensor: " + sensor.block());

        // UPDATE — returns Mono<Long>
        Mono<Long> rowsUpdated = client.sql(
            "UPDATE orders SET status=:newStatus WHERE status=:oldStatus")
            .bind("newStatus","SHIPPED").bind("oldStatus","OPEN")
            .fetch().rowsUpdated();
        System.out.println("Shipped: " + rowsUpdated.block() + " orders");

        // .first() — returns first row without throwing on extras
        Mono<Order> first = client.sql("SELECT * FROM orders ORDER BY id")
            .map(row -> fromRow(row))
            .first();
        System.out.println("First order: " + first.block());
    }
}
```

How to run: same classpath

`.map(rowMapper)` is called before the terminal (`.all()`/`.one()`/`.first()`). The `Row` parameter is scoped — only valid inside the mapping lambda. `.one()` returns an empty `Mono` if no row matches (does NOT throw `EmptyResultDataAccessException` — that's a difference from JDBC `queryForObject`). `.first()` takes the first row and ignores any additional rows.

---

### Level 3 — Advanced

Pipeline composition — chained reactive operations, `flatMap`, and error handling.

```java
// DatabaseClientDemo.java
import io.r2dbc.h2.*;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.r2dbc.core.DatabaseClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

record Order(long id, String product, double total, String status) {}

public class DatabaseClientDemo {

    static DatabaseClient buildClient() {
        return DatabaseClient.create(new H2ConnectionFactory(
            H2ConnectionConfiguration.builder()
                .inMemory("orders").option("DB_CLOSE_DELAY=-1").build()));
    }

    static Order fromRow(io.r2dbc.spi.Row r) {
        return new Order(r.get("id",Long.class), r.get("product",String.class),
            r.get("total",Double.class), r.get("status",String.class));
    }

    // Reactive service method — chains insert + select
    static Mono<Order> createAndFetch(DatabaseClient client, String product, double total) {
        return client.sql("INSERT INTO orders(product,total,status) VALUES(:p,:t,'OPEN')")
            .bind("p",product).bind("t",total)
            .fetch().rowsUpdated()
            .flatMap(rows ->
                client.sql("SELECT * FROM orders WHERE product=:p ORDER BY id DESC LIMIT 1")
                    .bind("p",product)
                    .map(row -> fromRow(row))
                    .one()
            );
    }

    public static void main(String[] args) {
        DatabaseClient client = buildClient();

        // Schema
        client.sql("CREATE TABLE orders (id BIGINT AUTO_INCREMENT PRIMARY KEY, " +
                   "product VARCHAR(100) NOT NULL, total DOUBLE NOT NULL, status VARCHAR(30))")
            .fetch().rowsUpdated().block();

        // Chain inserts + fetch via reactive pipeline
        Flux.just(
            new String[]{"Widget","49.99"},
            new String[]{"Gadget","99.00"},
            new String[]{"Sensor","199.99"}
        ).concatMap(a -> createAndFetch(client, a[0], Double.parseDouble(a[1])))
         .doOnNext(o -> System.out.printf("Created: %s (id=%d)%n", o.product(), o.id()))
         .blockLast();

        // Reactive aggregation — total revenue
        Mono<Double> revenue = client.sql("SELECT SUM(total) rev FROM orders WHERE status=:s")
            .bind("s","OPEN")
            .map(row -> row.get("rev", Double.class))
            .one();
        System.out.printf("Open revenue: $%.2f%n", revenue.block());

        // Error handling — duplicate constraint
        client.sql("INSERT INTO orders(product,total,status) VALUES(:p,:t,:s)")
            .bind("p",null).bind("t",10.0).bind("s","OPEN")
            .fetch().rowsUpdated()
            .onErrorResume(DataIntegrityViolationException.class, ex -> {
                System.out.println("Caught violation: " + ex.getClass().getSimpleName());
                return Mono.just(0L);
            })
            .block();
    }
}
```

How to run: same classpath

`flatMap` inside a reactive chain is the reactive equivalent of "then do this": insert completes → immediately query for the inserted row. `onErrorResume(ExceptionType.class, fn)` catches specific exceptions in the reactive stream — `DatabaseClient` translates R2DBC exceptions to Spring `DataAccessException` subclasses the same way `JdbcTemplate` does for JDBC.

## 6. Walkthrough

**Level 2 — `UPDATE` with `rowsUpdated()` (execution order):**

1. **`client.sql("UPDATE orders SET status=:newStatus WHERE status=:oldStatus").bind(...).bind(...).fetch().rowsUpdated()`**: builds a cold `Mono<Long>`. No DB call yet.
2. **`.block()`**: subscribes and blocks the calling thread. The reactive runtime starts.
3. **`ConnectionFactory.create()`**: H2 R2DBC driver creates a `Mono<Connection>`. H2 opens an in-process connection.
4. **Named-param rewrite**: `:newStatus` → `$1`, `:oldStatus` → `$2`. SQL becomes `UPDATE orders SET status=$1 WHERE status=$2`.
5. **`connection.createStatement(sql).bind("$1","SHIPPED").bind("$2","OPEN")`**.
6. **`statement.execute()`**: emits `Flux<Result>`.
7. **`result.getRowsUpdated()`**: emits `Mono<Long>` with the affected-row count (3 OPEN orders → 3).
8. **`fetch().rowsUpdated()`**: unwraps to `Mono<Long>` = 3.
9. **`.block()`** returns `3L`.
10. **Connection released** back.

```
SQL sent:  UPDATE orders SET status=$1 WHERE status=$2
Params:    ["SHIPPED", "OPEN"]
DB result: 3 rows updated
Mono<Long>: 3
```

## 7. Gotchas & takeaways

> **`.one()` returns empty `Mono` (not an exception) when no row matches.** This is different from `JdbcTemplate.queryForObject()` which throws. Chain `.switchIfEmpty(Mono.error(new NotFoundException(...)))` if you need an error on no result.

> **`Row` is only valid inside the `.map()` callback.** Do not store a `Row` reference in a variable outside the lambda — R2DBC drivers recycle the `Row` object for the next row immediately after the callback returns.

> **`DatabaseClient` integrates with reactive transactions** via `R2dbcTransactionManager`. Wrap calls in `@Transactional` (on a reactive method returning `Mono`/`Flux`) and the same connection is reused for all operations in the transaction.

- `DatabaseClient` is the reactive `JdbcTemplate` — fluent, SQL-level, non-blocking.
- `.fetch().all()` → `Flux<Map>`, `.map(fn).all()` → `Flux<T>`, `.fetch().one()` → `Mono<Map>`.
- `.one()` returns empty `Mono` (no exception) on zero rows; `.first()` silently ignores extra rows.
- `Row` is only valid inside the mapping callback — never capture it outside.
- Integrates with `@Transactional` on reactive methods via `R2dbcTransactionManager`.
