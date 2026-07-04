---
card: spring-framework
gi: 274
slug: connectionfactory-configuration
title: ConnectionFactory configuration
---

## 1. What it is

`ConnectionFactory` is the R2DBC equivalent of JDBC's `DataSource` — a factory that creates reactive, non-blocking `Connection` instances. Just as every Spring JDBC component starts with a `DataSource`, every Spring R2DBC component starts with a `ConnectionFactory`.

Spring supports two primary `ConnectionFactory` implementations:

| Implementation | Use |
|---|---|
| Vendor-specific (e.g., `H2ConnectionFactory`, `PostgresqlConnectionFactory`) | Direct driver; no pooling |
| `ConnectionPool` from `r2dbc-pool` | Reactive connection pool — production use |

```java
// Vendor factory (no pooling — for tests)
ConnectionFactory factory = new H2ConnectionFactory(
    H2ConnectionConfiguration.builder().inMemory("mydb").build());

// Pooled factory (production)
ConnectionPool pool = new ConnectionPool(ConnectionPoolConfiguration.builder(factory)
    .maxSize(20).build());
```

## 2. Why & when

Every R2DBC operation needs a `ConnectionFactory`. You must configure it explicitly — unlike `DataSource` in JDBC (where Spring Boot auto-configures HikariCP), R2DBC requires a specific vendor driver and optionally `r2dbc-pool` for connection pooling.

**Use a pooled `ConnectionFactory` in production** — opening a new TCP connection to the database per query is expensive even with R2DBC. `r2dbc-pool` maintains a pool of open R2DBC connections that are lent and returned reactively.

**Vendor-specific factories** (without pool) are fine for:
- Tests with H2 in-memory.
- Tools and scripts that run once.
- Environments where connection pooling is handled externally.

## 3. Core concept

`ConnectionFactory` API:

```java
// R2DBC SPI
ConnectionFactory {
    Publisher<? extends Connection> create();    // get a connection
    ConnectionFactoryMetadata getMetadata();     // driver info
}

Connection {
    Publisher<? extends Statement> createStatement(String sql);
    Publisher<Void> close();
    Publisher<Void> beginTransaction();
    Publisher<Void> commitTransaction();
    Publisher<Void> rollbackTransaction();
}
```

`r2dbc-pool` (`ConnectionPool`) wraps any `ConnectionFactory` and adds:
- `maxSize` — max concurrent connections.
- `initialSize` — connections created eagerly at startup.
- `maxIdleTime` / `maxLifeTime` — idle and max connection lifetime.
- `validationQuery` — SQL run to verify a connection before lending (e.g., `SELECT 1`).

Spring Framework wires `DatabaseClient` with a `ConnectionFactory` and `R2dbcTransactionManager` also takes a `ConnectionFactory` — both share the same factory so transaction binding works correctly.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- DatabaseClient -->
  <rect x="10" y="75" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="98" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">DatabaseClient</text>
  <text x="75" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">sql().fetch()</text>
  <line x1="142" y1="100" x2="195" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- ConnectionPool -->
  <rect x="197" y="50" width="200" height="100" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="297" y="72" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ConnectionPool</text>
  <line x1="207" y1="78" x2="387" y2="78" stroke="#8b949e" stroke-width="0.5"/>
  <text x="297" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">pool.create() → Mono&lt;Con&gt;</text>
  <text x="297" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">wraps: PooledConnection</text>
  <text x="297" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">release → return to pool</text>

  <line x1="399" y1="100" x2="452" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Driver ConnectionFactory -->
  <rect x="454" y="60" width="220" height="80" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="564" y="82" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Vendor ConnectionFactory</text>
  <text x="564" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">H2ConnectionFactory</text>
  <text x="564" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">PostgresqlConnectionFactory</text>
  <text x="564" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">MysqlConnectionFactory</text>

  <!-- Return arrow -->
  <line x1="452" y1="120" x2="399" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>
</svg>

`ConnectionPool` wraps the vendor factory; `DatabaseClient` and `R2dbcTransactionManager` share the pool.

## 5. Runnable example

Scenario: a **task tracker** — configure H2 R2DBC `ConnectionFactory` for tests, demonstrate pooled `ConnectionFactory`, and wire both `DatabaseClient` and `R2dbcTransactionManager` to the same factory.

### Level 1 — Basic

`H2ConnectionFactory` directly — no pooling, for tests.

```java
// ConnectionFactoryDemo.java
import io.r2dbc.h2.*;
import io.r2dbc.spi.ConnectionFactory;
import org.springframework.r2dbc.core.DatabaseClient;
import reactor.core.publisher.Flux;

public class ConnectionFactoryDemo {

    public static void main(String[] args) {
        // H2 in-memory R2DBC — no pooling
        H2ConnectionConfiguration config = H2ConnectionConfiguration.builder()
            .inMemory("tasks")
            .option("DB_CLOSE_DELAY=-1")
            .build();
        ConnectionFactory factory = new H2ConnectionFactory(config);

        // Verify: print factory metadata
        System.out.println("Driver: " + factory.getMetadata().getName());

        DatabaseClient client = DatabaseClient.create(factory);

        // Schema + seed
        client.sql("CREATE TABLE tasks (id BIGINT AUTO_INCREMENT PRIMARY KEY, " +
                   "title VARCHAR(200), done BOOLEAN DEFAULT FALSE)")
            .fetch().rowsUpdated()
            .thenMany(Flux.just("Buy groceries","Write tests","Review PR").map(t ->
                client.sql("INSERT INTO tasks(title) VALUES(:t)").bind("t",t).fetch().rowsUpdated()
            ).concatMap(m -> m))
            .blockLast();

        Long count = client.sql("SELECT COUNT(*) cnt FROM tasks")
            .map(r -> r.get("cnt", Long.class)).one().block();
        System.out.println("Tasks created: " + count);
    }
}
```

How to run: `java -cp spring-r2dbc.jar:r2dbc-spi.jar:r2dbc-h2.jar:reactor-core.jar:. ConnectionFactoryDemo.java`

`H2ConnectionFactory` opens a new R2DBC connection for every `create()` call — no pooling. `factory.getMetadata().getName()` returns the driver name (e.g., `H2`). For tests this is fine; for production under load, every query opening a new connection is expensive.

---

### Level 2 — Intermediate

`ConnectionPool` from `r2dbc-pool` — reactive connection pooling.

```java
// ConnectionFactoryDemo.java
import io.r2dbc.h2.*;
import io.r2dbc.pool.*;
import io.r2dbc.spi.ConnectionFactory;
import org.springframework.r2dbc.core.DatabaseClient;
import reactor.core.publisher.Flux;
import java.time.Duration;

public class ConnectionFactoryDemo {

    static ConnectionPool buildPool() {
        // 1. Build the vendor ConnectionFactory
        ConnectionFactory h2 = new H2ConnectionFactory(
            H2ConnectionConfiguration.builder()
                .inMemory("tasks").option("DB_CLOSE_DELAY=-1").build());

        // 2. Wrap with a reactive pool
        ConnectionPoolConfiguration poolConfig = ConnectionPoolConfiguration.builder(h2)
            .name("task-pool")
            .initialSize(2)          // open 2 connections eagerly
            .maxSize(10)             // max 10 concurrent connections
            .maxIdleTime(Duration.ofMinutes(10))
            .maxLifeTime(Duration.ofMinutes(30))
            .validationQuery("SELECT 1")
            .build();

        return new ConnectionPool(poolConfig);
    }

    public static void main(String[] args) throws InterruptedException {
        ConnectionPool pool = buildPool();

        // Print pool state (before use)
        System.out.println("Allocated: " + pool.getMetrics()
            .map(m -> m.allocatedSize()).orElse(-1));

        DatabaseClient client = DatabaseClient.create(pool);
        client.sql("CREATE TABLE tasks (id BIGINT AUTO_INCREMENT PRIMARY KEY, " +
                   "title VARCHAR(200), done BOOLEAN DEFAULT FALSE)")
            .fetch().rowsUpdated().block();

        // 5 concurrent inserts — pool lends connections
        Flux.range(1, 5)
            .flatMap(i -> client.sql("INSERT INTO tasks(title) VALUES(:t)")
                .bind("t","Task-" + i).fetch().rowsUpdated())
            .blockLast();

        // Pool metrics after load
        pool.getMetrics().ifPresent(m ->
            System.out.printf("Pool: allocated=%d  acquired=%d  pending=%d%n",
                m.allocatedSize(), m.acquiredSize(), m.pendingAcquireSize()));

        Long count = client.sql("SELECT COUNT(*) cnt FROM tasks")
            .map(r -> r.get("cnt", Long.class)).one().block();
        System.out.println("Tasks: " + count);

        // Graceful shutdown
        pool.disposeLater().block();
        System.out.println("Pool disposed");
    }
}
```

How to run: `java -cp spring-r2dbc.jar:r2dbc-spi.jar:r2dbc-h2.jar:r2dbc-pool.jar:reactor-core.jar:. ConnectionFactoryDemo.java`

`ConnectionPool` maintains a pool of `PooledConnection` instances — each `create()` call returns an existing idle connection or creates a new one (up to `maxSize`). `pool.getMetrics()` exposes `allocatedSize()` (total connections), `acquiredSize()` (in-use connections), `pendingAcquireSize()` (waiting requests). `disposeLater()` shuts down the pool gracefully.

---

### Level 3 — Advanced

`ConnectionFactory` wired into `@Configuration` with `R2dbcTransactionManager` for shared TX integration.

```java
// ConnectionFactoryDemo.java
import io.r2dbc.h2.*;
import io.r2dbc.pool.*;
import io.r2dbc.spi.ConnectionFactory;
import org.springframework.context.annotation.*;
import org.springframework.r2dbc.connection.R2dbcTransactionManager;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.transaction.ReactiveTransactionManager;
import org.springframework.transaction.reactive.TransactionalOperator;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import java.time.Duration;

@Configuration
class R2dbcConfig {
    @Bean
    public ConnectionFactory connectionFactory() {
        ConnectionFactory h2 = new H2ConnectionFactory(
            H2ConnectionConfiguration.builder()
                .inMemory("tasks").option("DB_CLOSE_DELAY=-1").build());
        return new ConnectionPool(ConnectionPoolConfiguration.builder(h2)
            .maxSize(10).maxIdleTime(Duration.ofMinutes(5)).build());
    }

    @Bean
    public DatabaseClient databaseClient(ConnectionFactory cf) {
        return DatabaseClient.create(cf);
    }

    @Bean
    public ReactiveTransactionManager transactionManager(ConnectionFactory cf) {
        return new R2dbcTransactionManager(cf);  // shares same factory as DatabaseClient
    }

    @Bean
    public TransactionalOperator transactionalOperator(ReactiveTransactionManager tm) {
        return TransactionalOperator.create(tm);
    }
}

public class ConnectionFactoryDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(R2dbcConfig.class);
        DatabaseClient client = ctx.getBean(DatabaseClient.class);
        TransactionalOperator tx = ctx.getBean(TransactionalOperator.class);

        // Create schema
        client.sql("CREATE TABLE tasks (id BIGINT AUTO_INCREMENT PRIMARY KEY, " +
                   "title VARCHAR(200), done BOOLEAN DEFAULT FALSE)")
            .fetch().rowsUpdated().block();

        // Transactional insert — both succeed or both rolled back
        Flux<Long> inserts = Flux.concat(
            client.sql("INSERT INTO tasks(title) VALUES(:t)").bind("t","Deploy app")
                .fetch().rowsUpdated(),
            client.sql("INSERT INTO tasks(title) VALUES(:t)").bind("t","Write docs")
                .fetch().rowsUpdated()
        ).as(tx::transactional);   // wraps the Flux in a reactive transaction
        inserts.blockLast();

        Long total = client.sql("SELECT COUNT(*) cnt FROM tasks")
            .map(r -> r.get("cnt", Long.class)).one().block();
        System.out.println("Tasks committed: " + total);

        ctx.close();
    }
}
```

How to run: same classpath + spring-context.jar + spring-tx.jar

`R2dbcTransactionManager(connectionFactory)` must receive the **same** `ConnectionFactory` as `DatabaseClient` — this ensures both use the same connection binding for transactions. `TransactionalOperator.transactional(publisher)` wraps any `Mono`/`Flux` in a transaction: it begins the TX, subscribes to the publisher, and commits on completion or rolls back on error.

## 6. Walkthrough

**Level 2 — `ConnectionPool` connection lifecycle:**

1. **`ConnectionPool` created**: initialises `initialSize=2` connections eagerly. H2 opens 2 R2DBC connections. `allocatedSize=2`.
2. **`flatMap` with 5 concurrent inserts**: 5 subscriptions arrive concurrently to `client.sql(...).fetch().rowsUpdated()`.
3. **First 2 subscriptions**: pool has 2 idle connections → `pool.create()` returns `PooledConnection` immediately. `acquiredSize=2`.
4. **Next 2 subscriptions**: pool is at `initialSize=2` but below `maxSize=10` → creates 2 more connections. `allocatedSize=4`, `acquiredSize=4`.
5. **5th subscription**: same — creates one more. `allocatedSize=5`, `acquiredSize=5`.
6. **Each INSERT executes** on its pooled connection.
7. **On completion** each `PooledConnection.close()` returns it to the pool (not closes the TCP connection). `acquiredSize` drops back to 0.
8. **Pool metrics**: `allocatedSize=5`, `acquiredSize=0`, `pendingAcquireSize=0`.

```
Pool after 5 concurrent inserts:
  allocatedSize=5   (5 open connections in pool)
  acquiredSize=0    (all returned after inserts)
  pendingAcquireSize=0  (no waiting threads)
```

## 7. Gotchas & takeaways

> **`DatabaseClient` and `R2dbcTransactionManager` must share the same `ConnectionFactory` instance.** If they use different factories, transaction binding fails silently — each gets a different connection and they won't participate in the same transaction.

> **`ConnectionPool.disposeLater()` is a cold `Mono<Void>`.** You must subscribe (e.g., `.block()`) to actually dispose the pool and close all connections. Calling `disposeLater()` without subscribing is a no-op.

> **`validationQuery` adds latency per borrow.** For H2 and well-managed databases, skip it (omit the option) — it runs a query every time a connection is borrowed from the pool. Use `acquireRetry` instead for transient failures.

- `ConnectionFactory` = R2DBC equivalent of JDBC `DataSource`.
- `ConnectionPool` from `r2dbc-pool` = reactive HikariCP; wrap any vendor factory.
- Both `DatabaseClient` and `R2dbcTransactionManager` must use the same `ConnectionFactory`.
- `pool.getMetrics()` → live pool health (allocated, acquired, pending).
- `pool.disposeLater().block()` cleanly shuts down — call on application stop.
