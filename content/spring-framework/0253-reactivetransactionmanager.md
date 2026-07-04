---
card: spring-framework
gi: 253
slug: reactivetransactionmanager
title: ReactiveTransactionManager
---

## 1. What it is

`ReactiveTransactionManager` is the reactive counterpart of `PlatformTransactionManager`. It defines the same three operations — `getReactiveTransaction`, `commit`, `rollback` — but returns Project Reactor types (`Mono<ReactiveTransaction>` etc.) instead of blocking results. It was introduced in Spring 5.2 alongside `TransactionalOperator` and reactive `@Transactional` support.

```java
public interface ReactiveTransactionManager extends TransactionManager {
    Mono<ReactiveTransaction> getReactiveTransaction(TransactionDefinition definition);
    Mono<Void> commit(ReactiveTransaction transaction);
    Mono<Void> rollback(ReactiveTransaction transaction);
}
```

The key implementation is `R2dbcTransactionManager` (for relational databases via R2DBC) and `ReactiveMongoTransactionManager` (MongoDB).

## 2. Why & when

Thread-blocking transaction management (`PlatformTransactionManager`) cannot be used in a fully reactive pipeline because:

1. Reactive code runs on a small, fixed scheduler thread pool.
2. Blocking a scheduler thread (e.g., waiting for `getTransaction()`) reduces throughput and can deadlock.
3. `ThreadLocal` storage (used by Spring's imperative TM for binding connections) doesn't work reliably when the reactive pipeline switches threads between operators.

Use `ReactiveTransactionManager` when building a reactive application with:
- **Spring WebFlux** + R2DBC (reactive relational databases).
- **Spring Data MongoDB** reactive.
- Any other reactive data source that ships a `ReactiveTransactionManager` implementation.

Do NOT use `PlatformTransactionManager` in reactive code — it blocks the scheduler thread.

## 3. Core concept

`ReactiveTransactionManager` stores the active connection/session in Project Reactor's **`Context`** (an immutable per-subscription key-value map). The context is propagated through every `flatMap`, `map`, and other operators automatically. Each reactive data access operation reads the connection from the context rather than a `ThreadLocal`.

Key differences from `PlatformTransactionManager`:

| | PlatformTransactionManager | ReactiveTransactionManager |
|-|---------------------------|---------------------------|
| Return type | blocking `TransactionStatus` | `Mono<ReactiveTransaction>` |
| Connection storage | `ThreadLocal` | Reactor `Context` |
| Programming model | Imperative | Reactive (`Mono`/`Flux`) |
| Spring API | `TransactionTemplate` / `@Transactional` | `TransactionalOperator` / `@Transactional` |

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Interface box -->
  <rect x="10" y="40" width="270" height="135" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="145" y="62" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">ReactiveTransactionManager</text>
  <line x1="20" y1="72" x2="270" y2="72" stroke="#8b949e" stroke-width="0.5"/>
  <text x="145" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Mono&lt;ReactiveTransaction&gt; getReactiveTransaction()</text>
  <text x="145" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Mono&lt;Void&gt; commit(ReactiveTransaction)</text>
  <text x="145" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Mono&lt;Void&gt; rollback(ReactiveTransaction)</text>
  <text x="145" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">context: stored in Reactor Context</text>
  <text x="145" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(not ThreadLocal)</text>

  <line x1="282" y1="107" x2="340" y2="107" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="311" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implemented by</text>

  <!-- Implementations -->
  <rect x="340" y="40" width="350" height="135" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="515" y="62" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Implementations</text>
  <line x1="350" y1="72" x2="680" y2="72" stroke="#8b949e" stroke-width="0.5"/>
  <text x="515" y="92" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">R2dbcTransactionManager</text>
  <text x="515" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(PostgreSQL, MySQL, H2 via R2DBC)</text>
  <text x="515" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">ReactiveMongoTransactionManager</text>
  <text x="515" y="144" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(MongoDB multi-document)</text>
  <text x="515" y="164" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ custom implementations</text>
</svg>

`ReactiveTransactionManager` stores transaction state in Reactor `Context`, not `ThreadLocal`, enabling safe cross-thread propagation.

## 5. Runnable example

Scenario: a **`CatalogService`** using R2DBC — first with a basic reactive transaction, then with error-triggered rollback, then with `@Transactional` on a reactive service method.

### Level 1 — Basic

`R2dbcTransactionManager` + `TransactionalOperator.execute()`.

```java
// ReactiveTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.r2dbc.core.*;
import org.springframework.r2dbc.connection.*;
import org.springframework.transaction.*;
import org.springframework.transaction.reactive.*;
import io.r2dbc.h2.*;

@Configuration
public class ReactiveTMDemo {
    @Bean public io.r2dbc.spi.ConnectionFactory cf() {
        return H2ConnectionFactory.inMemory("catalog");
    }
    @Bean public DatabaseClient db(io.r2dbc.spi.ConnectionFactory cf) {
        return DatabaseClient.create(cf);
    }
    @Bean public ReactiveTransactionManager tm(io.r2dbc.spi.ConnectionFactory cf) {
        return new R2dbcTransactionManager(cf);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ReactiveTMDemo.class);
        var db = ctx.getBean(DatabaseClient.class);
        var tm = ctx.getBean(ReactiveTransactionManager.class);

        // Schema
        db.sql("CREATE TABLE catalog (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), price DOUBLE)")
          .fetch().rowsUpdated().block();

        TransactionalOperator txOp = TransactionalOperator.create(tm);

        txOp.execute(status ->
            db.sql("INSERT INTO catalog(name,price) VALUES('Widget',9.99)")
              .fetch().rowsUpdated()
              .doOnNext(n -> System.out.println("[REACTIVE TX] inserted " + n + " row(s)"))
        ).blockLast();

        db.sql("SELECT name, price FROM catalog").fetch().all()
          .doOnNext(r -> System.out.println("Catalog: " + r)).blockLast();

        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-r2dbc.jar:r2dbc-spi.jar:r2dbc-h2.jar:reactor-core.jar:. ReactiveTMDemo.java`

`R2dbcTransactionManager.getReactiveTransaction()` returns a `Mono` that, when subscribed, acquires an R2DBC connection and begins a transaction. The connection is stored in the Reactor `Context`. All R2DBC operations downstream read the connection from the context and execute on the same transaction.

---

### Level 2 — Intermediate

**Error-triggered rollback** in a reactive pipeline — `onError` signal causes automatic rollback.

```java
// ReactiveTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.r2dbc.core.*;
import org.springframework.r2dbc.connection.*;
import org.springframework.transaction.*;
import org.springframework.transaction.reactive.*;
import io.r2dbc.h2.*;
import reactor.core.publisher.*;

@Configuration
public class ReactiveTMDemo {
    @Bean public io.r2dbc.spi.ConnectionFactory cf() { return H2ConnectionFactory.inMemory("catalog2"); }
    @Bean public DatabaseClient db(io.r2dbc.spi.ConnectionFactory cf) { return DatabaseClient.create(cf); }
    @Bean public ReactiveTransactionManager tm(io.r2dbc.spi.ConnectionFactory cf) {
        return new R2dbcTransactionManager(cf);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ReactiveTMDemo.class);
        var db = ctx.getBean(DatabaseClient.class);
        var tm = ctx.getBean(ReactiveTransactionManager.class);

        db.sql("CREATE TABLE catalog (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), price DOUBLE)")
          .fetch().rowsUpdated().block();

        TransactionalOperator txOp = TransactionalOperator.create(tm);

        // Pipeline that fails mid-way — both inserts should roll back
        txOp.execute(status ->
            db.sql("INSERT INTO catalog(name,price) VALUES('Gadget',19.99)")
              .fetch().rowsUpdated()
              .flatMap(n -> {
                  System.out.println("[REACTIVE TX] first insert OK");
                  // Simulate error after first insert
                  return Mono.<Long>error(new RuntimeException("Stock system down"));
              })
        )
        .onErrorResume(e -> {
            System.out.println("[REACTIVE TX] rolled back: " + e.getMessage());
            return Mono.empty();
        })
        .blockLast();

        // Verify rollback
        db.sql("SELECT COUNT(*) FROM catalog").fetch().one()
          .doOnNext(r -> System.out.println("Rows after rollback: " + r.get("COUNT(*)"))).block();

        ctx.close();
    }
}
```

How to run: same classpath

The `Mono.error(...)` propagates an `onError` signal through the pipeline. `TransactionalOperator` catches it, calls `tm.rollback(reactiveTransaction)` (returning a `Mono<Void>`), and then re-emits the error (or `onErrorResume` swallows it). The row count is 0 — the first insert was rolled back.

---

### Level 3 — Advanced

**`@Transactional` on a reactive service** — the declarative approach for reactive code.

```java
// ReactiveTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.r2dbc.core.*;
import org.springframework.r2dbc.connection.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.reactive.*;
import org.springframework.stereotype.*;
import io.r2dbc.h2.*;
import reactor.core.publisher.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class ReactiveTMDemo {
    @Bean public io.r2dbc.spi.ConnectionFactory cf() { return H2ConnectionFactory.inMemory("catalog3"); }
    @Bean public DatabaseClient db(io.r2dbc.spi.ConnectionFactory cf) { return DatabaseClient.create(cf); }
    // Named "transactionManager" — auto-detected by @EnableTransactionManagement
    @Bean public ReactiveTransactionManager transactionManager(io.r2dbc.spi.ConnectionFactory cf) {
        return new R2dbcTransactionManager(cf);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ReactiveTMDemo.class);
        var db = ctx.getBean(DatabaseClient.class);
        db.sql("CREATE TABLE catalog (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), price DOUBLE)")
          .fetch().rowsUpdated().block();

        CatalogService svc = ctx.getBean(CatalogService.class);

        svc.addProduct("Reactive Gadget", 29.99)
           .doOnSuccess(n -> System.out.println("Committed: " + n + " row"))
           .block();

        svc.addProduct("FAIL-PRODUCT", -1.0)
           .onErrorResume(e -> { System.out.println("Rolled back: " + e.getMessage()); return Mono.empty(); })
           .block();

        db.sql("SELECT name, price FROM catalog").fetch().all()
          .doOnNext(r -> System.out.println("In DB: " + r)).blockLast();

        ctx.close();
    }
}

@Service
class CatalogService {
    private final DatabaseClient db;
    CatalogService(DatabaseClient db) { this.db = db; }

    @Transactional   // reactive @Transactional — uses ReactiveTransactionManager
    public Mono<Long> addProduct(String name, double price) {
        if (price < 0) return Mono.error(new IllegalArgumentException("Negative price: " + price));
        return db.sql("INSERT INTO catalog(name,price) VALUES(:name,:price)")
            .bind("name", name).bind("price", price)
            .fetch().rowsUpdated()
            .doOnNext(n -> System.out.println("[SERVICE TX] inserted: " + name + " $" + price));
    }
}
```

How to run: same classpath + `spring-tx.jar`

Spring detects `transactionManager` is a `ReactiveTransactionManager` and uses `ReactiveTransactionInterceptor` instead of `TransactionInterceptor`. The returned `Mono<Long>` is decorated with transaction lifecycle hooks. On subscription, the transaction opens; on `onComplete`, it commits; on `onError`, it rolls back. Only "Reactive Gadget" appears in the final DB query.

## 6. Walkthrough

**Level 3 — `@Transactional` reactive subscription flow:**

```
svc.addProduct("Reactive Gadget", 29.99)
  → ReactiveTransactionInterceptor.invoke()
     decorates the returned Mono with tx lifecycle hooks
  ← returns decorated Mono (NOT yet subscribed)

.doOnSuccess(...).block()  ← subscribes

subscription propagates:
  → ReactiveTransactionInterceptor hook fires on subscription:
      tm.getReactiveTransaction(def)
        → R2dbcTransactionManager.doGetTransaction()
           → cf.create() [async — returns Mono<Connection>]
           → con.beginTransaction() [async]
           → store con in Reactor Context under TX_KEY
        ← Mono<ReactiveTransaction> completes

  → addProduct() body runs:
      price ≥ 0 ✓
      db.sql(INSERT...).fetch().rowsUpdated()
        → R2DBC reads con from Reactor Context
        → executes INSERT reactively
        → onNext(1L) → doOnNext prints "[SERVICE TX] inserted Reactive Gadget $29.99"
        → onComplete

  → ReactiveTransactionInterceptor onComplete hook:
      tm.commit(reactiveTransaction)
        → con.commitTransaction() [async]
        → con.close()
      ← Mono<Void> completes
  ← Mono<Long> emits 1L

doOnSuccess(n -> ...) → prints "Committed: 1 row"
block() returns 1L
```

## 7. Gotchas & takeaways

> **Never use `PlatformTransactionManager` in a reactive pipeline.** Calling blocking methods on a reactive scheduler thread causes `BlockHoundUnauthorizedCallException` (with BlockHound enabled) or deadlock. Always use `ReactiveTransactionManager` with reactive data sources.

> **`@Transactional` on a method that returns `Mono` or `Flux` must return that publisher.** The annotation wraps the returned publisher — it does NOT run the body synchronously. If the method throws synchronously before returning the publisher, the transaction still opens but immediately rolls back.

> **Propagation in reactive context works the same as imperative** — `REQUIRED` participates in the existing Reactor Context transaction; `REQUIRES_NEW` creates a new one. However, the context must be propagated correctly through `flatMap` chains for participants to see the parent transaction.

- `R2dbcTransactionManager` — the standard reactive TM for relational databases via R2DBC.
- `ReactiveMongoTransactionManager` — for MongoDB multi-document reactive transactions.
- `TransactionalOperator` — programmatic reactive transactions.
- `@Transactional` — declarative reactive transactions (Spring 5.2+), same annotation, different interceptor.
- Context propagation is automatic in Project Reactor through `flatMap` chains.
