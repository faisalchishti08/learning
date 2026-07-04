---
card: spring-framework
gi: 272
slug: r2dbc-overview
title: R2DBC overview
---

## 1. What it is

**R2DBC** (Reactive Relational Database Connectivity) is a specification — analogous to JDBC but designed for **non-blocking, reactive** database access. Instead of blocking threads while waiting for SQL results, R2DBC returns `Publisher` types (`Mono<T>` / `Flux<T>`) that emit results asynchronously.

```java
// JDBC — blocks the thread until rows arrive
List<User> users = jdbcTemplate.query("SELECT * FROM users", USER_MAPPER);

// R2DBC — returns immediately; data arrives reactively
Flux<User> users = databaseClient.sql("SELECT * FROM users")
    .map(row -> new User(row.get("id", Long.class), row.get("name", String.class)))
    .all();
```

Spring Framework 5.3+ integrates R2DBC via `DatabaseClient` (the reactive counterpart to `JdbcTemplate`) and `R2dbcEntityTemplate`. Spring Boot auto-configures R2DBC when an R2DBC driver is on the classpath.

## 2. Why & when

JDBC blocks the calling thread during I/O — a thread-per-request model limits throughput to the thread pool size. Under high load (thousands of concurrent connections), each waiting thread consumes ~0.5 MB of memory — that's 500 MB for 1000 concurrent queries, just in thread stacks.

R2DBC solves this by returning control to the event loop immediately and delivering results through a reactive pipeline — a small number of threads can serve thousands of concurrent database operations.

**Use R2DBC when:**
- Building a reactive/non-blocking application with Spring WebFlux.
- High concurrency is needed (API gateways, streaming services, chat backends).
- The entire stack is reactive end-to-end (HTTP → service → database).

**Stick with JDBC when:**
- Using Spring MVC (blocking HTTP handling makes R2DBC pointless).
- Using JPA / Hibernate (they are inherently blocking; no R2DBC equivalent).
- Simplicity matters more than reactive backpressure.

## 3. Core concept

R2DBC key types:

| Type | Role |
|---|---|
| `ConnectionFactory` | R2DBC equivalent of `DataSource` — creates reactive `Connection`s |
| `Connection` | R2DBC non-blocking connection |
| `Statement` | Parameterised SQL; `.execute()` returns `Flux<Result>` |
| `DatabaseClient` | Spring's fluent wrapper (like `JdbcTemplate` but reactive) |
| `R2dbcEntityTemplate` | Higher-level ORM-style CRUD |

The reactive contract:
- `Mono<T>` — 0 or 1 items (like `Optional<T>` but async)
- `Flux<T>` — 0..N items (like `List<T>` but streaming async)
- Nothing happens until you **subscribe** — calling `.subscribe()`, `.block()`, or returning from a WebFlux controller.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- JDBC model -->
  <text x="165" y="18" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JDBC (blocking)</text>
  <rect x="10" y="28" width="80" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="50" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">Thread</text>
  <line x1="92" y1="43" x2="146" y2="43" stroke="#8b949e" stroke-width="2"/>
  <text x="120" y="37" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">⏳ waiting</text>
  <rect x="148" y="28" width="60" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="178" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">DB</text>
  <text x="120" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Thread blocked during I/O</text>

  <!-- R2DBC model -->
  <text x="500" y="18" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">R2DBC (non-blocking)</text>
  <rect x="350" y="28" width="80" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="390" y="47" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">Event loop</text>
  <line x1="432" y1="43" x2="490" y2="43" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="462" y="38" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Flux&lt;R&gt;</text>
  <rect x="492" y="28" width="60" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="522" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">DB</text>
  <line x1="490" y1="65" x2="432" y2="65" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>
  <text x="462" y="78" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="monospace">rows arrive async</text>

  <!-- Spring layers -->
  <rect x="30" y="110" width="640" height="95" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="132" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Spring R2DBC Stack</text>
  <line x1="40" y1="138" x2="660" y2="138" stroke="#8b949e" stroke-width="0.5"/>
  <text x="200" y="158" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">DatabaseClient</text>
  <text x="200" y="172" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fluent SQL API</text>
  <text x="350" y="158" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">R2dbcEntityTemplate</text>
  <text x="350" y="172" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">ORM-style CRUD</text>
  <text x="520" y="158" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">ConnectionFactory</text>
  <text x="520" y="172" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">R2DBC DataSource equivalent</text>
  <text x="350" y="192" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">r2dbc-h2 / r2dbc-postgresql / r2dbc-mysql</text>
</svg>

R2DBC returns control immediately; rows arrive reactively through `Flux<T>` callbacks on the event loop.

## 5. Runnable example

Scenario: a **user registry** — connect via R2DBC to H2, insert users, query reactively, demonstrating the non-blocking execution model.

### Level 1 — Basic

`ConnectionFactory` setup and low-level `Connection.createStatement()`.

```java
// R2dbcDemo.java
import io.r2dbc.h2.H2ConnectionConfiguration;
import io.r2dbc.h2.H2ConnectionFactory;
import io.r2dbc.spi.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class R2dbcDemo {

    public static void main(String[] args) {
        // Build ConnectionFactory — H2 in-memory, R2DBC protocol
        H2ConnectionConfiguration config = H2ConnectionConfiguration.builder()
            .inMemory("users")                // database name
            .option("DB_CLOSE_DELAY=-1")
            .build();
        ConnectionFactory factory = new H2ConnectionFactory(config);

        // All operations return Mono/Flux — subscribe to run them
        Mono.from(factory.create())
            .flatMapMany(con -> Flux.concat(
                // DDL
                Mono.from(con.createStatement(
                    "CREATE TABLE IF NOT EXISTS users " +
                    "(id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100))")
                    .execute()).flatMap(r -> Mono.from(r.getRowsUpdated())),
                // INSERT
                Mono.from(con.createStatement(
                    "INSERT INTO users(name) VALUES($1)")
                    .bind("$1", "Alice")
                    .execute()).flatMap(r -> Mono.from(r.getRowsUpdated())),
                Mono.from(con.createStatement(
                    "INSERT INTO users(name) VALUES($1)")
                    .bind("$1", "Bob")
                    .execute()).flatMap(r -> Mono.from(r.getRowsUpdated())),
                // SELECT
                Flux.from(con.createStatement("SELECT id, name FROM users ORDER BY id")
                    .execute())
                    .flatMap(r -> r.map((row, meta) ->
                        "User[" + row.get("id", Long.class) + "] " + row.get("name", String.class)))
                    .doOnNext(System.out::println)
            ))
            .blockLast();   // block only in main() — never in reactive pipelines
    }
}
```

How to run: `java -cp spring-r2dbc.jar:r2dbc-spi.jar:r2dbc-h2.jar:reactor-core.jar:. R2dbcDemo.java`

`Mono.from(factory.create())` acquires a connection reactively. `createStatement(sql).execute()` returns `Flux<Result>` — nothing sends to the database until subscription. `blockLast()` subscribes and blocks the calling thread, acceptable in `main()` but forbidden inside a reactive pipeline (would deadlock a Netty event loop).

---

### Level 2 — Intermediate

`DatabaseClient` — Spring's fluent R2DBC wrapper, equivalent to `JdbcTemplate`.

```java
// R2dbcDemo.java
import io.r2dbc.h2.*;
import org.springframework.r2dbc.core.DatabaseClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import java.util.Map;

record User(long id, String name, String role) {}

public class R2dbcDemo {

    public static void main(String[] args) {
        H2ConnectionFactory factory = new H2ConnectionFactory(
            H2ConnectionConfiguration.builder()
                .inMemory("users").option("DB_CLOSE_DELAY=-1").build());

        DatabaseClient client = DatabaseClient.create(factory);

        // Schema + seed
        client.sql("CREATE TABLE users (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), role VARCHAR(50))")
            .fetch().rowsUpdated()
            .then(client.sql("INSERT INTO users(name,role) VALUES(:name,:role)")
                .bind("name","Alice").bind("role","ADMIN").fetch().rowsUpdated())
            .then(client.sql("INSERT INTO users(name,role) VALUES(:name,:role)")
                .bind("name","Bob").bind("role","USER").fetch().rowsUpdated())
            .then(client.sql("INSERT INTO users(name,role) VALUES(:name,:role)")
                .bind("name","Carol").bind("role","USER").fetch().rowsUpdated())
            .block();

        // SELECT all — Flux<Map<String,Object>>
        Flux<Map<String,Object>> rows = client.sql("SELECT id,name,role FROM users ORDER BY id")
            .fetch().all();
        rows.doOnNext(r -> System.out.printf("  [%s] %-10s %s%n",
                r.get("ID"), r.get("NAME"), r.get("ROLE")))
            .blockLast();

        // SELECT by role — named param, map to domain record
        Flux<User> admins = client.sql("SELECT * FROM users WHERE role = :role")
            .bind("role","ADMIN")
            .map(row -> new User(
                row.get("id", Long.class),
                row.get("name", String.class),
                row.get("role", String.class)))
            .all();
        System.out.println("Admins:");
        admins.doOnNext(u -> System.out.println("  " + u.name())).blockLast();

        // COUNT — Mono<Integer>
        Mono<Integer> count = client.sql("SELECT COUNT(*) cnt FROM users WHERE role=:r")
            .bind("r","USER")
            .map(row -> row.get("cnt", Integer.class))
            .one();
        System.out.println("USER count: " + count.block());
    }
}
```

How to run: same classpath

`DatabaseClient.create(factory)` builds a client backed by the `ConnectionFactory`. `.sql(...)` starts a builder; `.bind("name", val)` binds named parameters; `.fetch().all()` returns `Flux<Map<String,Object>>`; `.fetch().one()` returns `Mono<Map>`. `.map(row -> ...)` transforms each `Row` (a cursor) into a domain object inside the reactive chain.

---

### Level 3 — Advanced

Full CRUD pipeline — insert, update, query with `Flux` transformation, delete.

```java
// R2dbcDemo.java
import io.r2dbc.h2.*;
import org.springframework.r2dbc.core.DatabaseClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

record User(long id, String name, String role) {}

public class R2dbcDemo {

    static DatabaseClient buildClient() {
        return DatabaseClient.create(new H2ConnectionFactory(
            H2ConnectionConfiguration.builder()
                .inMemory("users").option("DB_CLOSE_DELAY=-1").build()));
    }

    public static void main(String[] args) {
        DatabaseClient client = buildClient();

        // Schema + seed as a reactive chain
        Mono<Void> setup = client.sql(
            "CREATE TABLE users (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), role VARCHAR(50))")
            .fetch().rowsUpdated()
            .thenMany(Flux.just(
                new String[]{"Alice","ADMIN"}, new String[]{"Bob","USER"},
                new String[]{"Carol","USER"}, new String[]{"Dave","MOD"},
                new String[]{"Eve","USER"}
            ).concatMap(arr ->
                client.sql("INSERT INTO users(name,role) VALUES(:name,:role)")
                    .bind("name", arr[0]).bind("role", arr[1]).fetch().rowsUpdated()
            ))
            .then();
        setup.block();

        // UPDATE — raise Dave to ADMIN
        Long updated = client.sql("UPDATE users SET role=:role WHERE name=:name")
            .bind("role","ADMIN").bind("name","Dave")
            .fetch().rowsUpdated().block();
        System.out.println("Updated rows: " + updated);

        // Query with reactive transformation — group by role
        client.sql("SELECT id,name,role FROM users ORDER BY role,name")
            .map(row -> new User(
                row.get("id", Long.class),
                row.get("name", String.class),
                row.get("role", String.class)))
            .all()
            .groupBy(User::role)
            .flatMap(group -> group.collectList()
                .doOnNext(users -> System.out.println(group.key() + ": " +
                    users.stream().map(User::name).toList())))
            .blockLast();

        // DELETE — remove all USERs
        Long deleted = client.sql("DELETE FROM users WHERE role=:role")
            .bind("role","USER").fetch().rowsUpdated().block();
        System.out.println("Deleted USER rows: " + deleted);

        Long remaining = client.sql("SELECT COUNT(*) cnt FROM users")
            .map(row -> row.get("cnt", Long.class)).one().block();
        System.out.println("Remaining: " + remaining);
    }
}
```

How to run: same classpath

`Flux.just(...).concatMap(...)` builds a sequential reactive pipeline for bulk inserts. `groupBy(User::role)` partitions the stream into sub-`GroupedFlux` keyed by role — a reactive equivalent of `collect(groupingBy(...))`. Each group emits independently; `flatMap` subscribes to each group and collects it to a list.

## 6. Walkthrough

**Level 2 — `DatabaseClient` SELECT with named param (execution order):**

1. **`client.sql("SELECT * FROM users WHERE role = :role").bind("role","ADMIN")`**: builds a `GenericExecuteSpec`. No connection opened yet.
2. **`.map(row -> new User(...))`**: registers a row-mapping function in the spec. Still no DB call.
3. **`.all()`**: returns a cold `Flux<User>`. Nothing executes until subscription.
4. **`.doOnNext(...).blockLast()`**: subscribes. `blockLast()` drives the reactive loop from the calling thread.
5. **`ConnectionFactory.create()`**: H2 R2DBC driver opens a connection asynchronously (emits `Connection`).
6. **Named param rewrite**: `:role` → `$1` (H2 R2DBC uses positional syntax). Binds `"ADMIN"` to `$1`.
7. **`Statement.execute()`**: H2 executes `SELECT * FROM users WHERE role = $1` with `["ADMIN"]`. H2 returns a `Flux<Result>`.
8. **Row mapping**: for each `Result`, `row -> new User(row.get("id",...), row.get("name",...), row.get("role",...))` is called for each row that matches.
9. **`doOnNext` prints** each `User`.
10. **`blockLast()`** returns after the last row is emitted.
11. **Connection released** back to the pool (R2DBC pool or closed if not pooled).

```
SQL sent: SELECT * FROM users WHERE role = $1
Params:   ["ADMIN"]
DB:       1 row → {id=1, name=Alice, role=ADMIN}
Pipeline: Result → Row → User(1,"Alice","ADMIN") → doOnNext → print
```

## 7. Gotchas & takeaways

> **Never call `.block()` inside a reactive pipeline (WebFlux handler, `@Transactional` reactive method).** It blocks a Netty event-loop thread and causes a deadlock. Use `.block()` only in `main()` or tests, and only when the rest of the chain is non-reactive.

> **R2DBC is NOT a drop-in replacement for JDBC + JPA.** There is no R2DBC equivalent of Hibernate or the JPA spec — you use `DatabaseClient` or `R2dbcEntityTemplate` for CRUD, which is SQL-level, not entity-lifecycle level.

> **`row.get(column)` cursor is only valid during the `.map()` callback.** Do not capture a `Row` reference and read it outside the mapping lambda — R2DBC drivers invalidate `Row` objects after the callback returns.

- R2DBC = reactive JDBC; returns `Mono<T>` / `Flux<T>`; non-blocking throughout.
- `DatabaseClient` = reactive `JdbcTemplate`; fluent builder; `.fetch().all()` → `Flux`.
- Nothing executes until subscription — cold publishers.
- `.block()` in main()/tests only; never inside a reactive pipeline.
- No JPA/Hibernate equivalent — SQL-level operations only.
