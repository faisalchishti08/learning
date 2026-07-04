---
card: spring-framework
gi: 249
slug: transactionaloperator-reactive
title: TransactionalOperator (reactive)
---

## 1. What it is

`TransactionalOperator` is the reactive equivalent of `TransactionTemplate`. It wraps a `ReactiveTransactionManager` and applies transaction semantics to a reactive publisher (`Mono` or `Flux`) using Project Reactor's operator composition. Instead of a thread-bound transaction (which doesn't work in reactive pipelines), it uses Reactor's `Context` to propagate the transaction.

```java
transactionalOperator.execute(status ->
    r2dbcTemplate.update("INSERT INTO orders ...")
        .then(auditTemplate.insert("order created"))
).subscribe();
```

`@Transactional` also works in reactive Spring (WebFlux + R2DBC) since Spring 5.2, using `ReactiveTransactionManager` under the hood.

## 2. Why & when

Reactive applications (WebFlux, R2DBC) cannot use thread-local storage for transaction context because the reactive pipeline may switch threads between operators. The `TransactionalOperator` solves this by:

1. Beginning the transaction and storing the connection in Reactor's `Context` (not a `ThreadLocal`).
2. Propagating the context through every `flatMap`, `map`, and operator in the chain.
3. Committing on completion or rolling back on error.

Use `TransactionalOperator` when:
- Writing a **reactive application** with R2DBC, MongoDB reactive, or another reactive data source.
- You need **programmatic** transaction control in a reactive pipeline.
- You're writing **library code** and don't want to force `@Transactional` on callers.

For typical WebFlux + Spring Data R2DBC service methods, `@Transactional` is simpler and preferred.

## 3. Core concept

`TransactionalOperator` is created from a `ReactiveTransactionManager`:

```java
TransactionalOperator operator = TransactionalOperator.create(reactiveTransactionManager);
```

Two usage patterns:

**Wrapping**: `operator.execute(status -> mono)` — runs the reactive pipeline within a managed transaction.

**Composing**: `mono.as(operator::transactional)` — applies the operator inline in the pipeline chain.

The transaction context is stored in Reactor's `ContextView` (immutable) and mutated through `Context.put(key, value)`. Each R2DBC operation reads the connection from the context rather than a `ThreadLocal`.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Reactive pipeline -->
  <rect x="10" y="60" width="630" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="325" y="82" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Reactive Pipeline (Project Reactor)</text>

  <!-- TX begin -->
  <rect x="25" y="92" width="130" height="38" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="108" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">TransactionalOperator</text>
  <text x="90" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">begin tx → Reactor Context</text>

  <line x1="157" y1="111" x2="185" y2="111" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- R2DBC op 1 -->
  <rect x="185" y="92" width="110" height="38" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="240" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">R2DBC insert()</text>
  <text x="240" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reads conn from ctx</text>

  <line x1="297" y1="111" x2="325" y2="111" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- flatMap -->
  <rect x="325" y="92" width="110" height="38" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="380" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">flatMap(audit)</text>
  <text x="380" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ctx propagated</text>

  <line x1="437" y1="111" x2="465" y2="111" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- commit/rollback -->
  <rect x="465" y="92" width="155" height="38" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="543" y="108" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">onComplete → commit</text>
  <text x="543" y="122" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">onError → rollback</text>

  <!-- Context label -->
  <text x="325" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Reactor Context carries the R2DBC connection through every operator — no ThreadLocal</text>
</svg>

Transaction context flows through the Reactor `Context`, not a `ThreadLocal` — safe across thread switches.

## 5. Runnable example

Scenario: a **`ProductService`** using R2DBC — first with `TransactionalOperator.execute()`, then with `.as(operator::transactional)` composition, then with `@Transactional` on a reactive method.

### Level 1 — Basic

`TransactionalOperator.execute()` wrapping a reactive insert pipeline.

```java
// ReactiveTransactionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.r2dbc.core.*;
import org.springframework.r2dbc.connection.*;
import org.springframework.transaction.reactive.*;
import io.r2dbc.spi.*;
import io.r2dbc.h2.*;
import reactor.core.publisher.*;

@Configuration
@ComponentScan
public class ReactiveTransactionDemo {
    @Bean
    public ConnectionFactory connectionFactory() {
        return H2ConnectionFactory.inMemory("testdb");
    }

    @Bean
    public DatabaseClient databaseClient(ConnectionFactory cf) {
        return DatabaseClient.create(cf);
    }

    @Bean
    public ReactiveTransactionManager reactiveTransactionManager(ConnectionFactory cf) {
        return new R2dbcTransactionManager(cf);
    }

    public static void main(String[] args) throws InterruptedException {
        var ctx = new AnnotationConfigApplicationContext(ReactiveTransactionDemo.class);
        var db = ctx.getBean(DatabaseClient.class);
        var tm = ctx.getBean(ReactiveTransactionManager.class);

        // Create schema
        db.sql("CREATE TABLE products (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), stock INT)")
          .fetch().rowsUpdated().block();

        TransactionalOperator txOp = TransactionalOperator.create(tm);

        // Execute a reactive pipeline inside a managed transaction
        txOp.execute(status ->
            db.sql("INSERT INTO products(name,stock) VALUES('Widget',100)")
              .fetch().rowsUpdated()
              .doOnNext(n -> System.out.println("Inserted " + n + " row(s)"))
        ).blockLast();

        // Verify
        db.sql("SELECT name, stock FROM products")
          .fetch().all()
          .doOnNext(row -> System.out.println("Product: " + row))
          .blockLast();

        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-r2dbc.jar:r2dbc-spi.jar:r2dbc-h2.jar:reactor-core.jar:. ReactiveTransactionDemo.java`

`txOp.execute(status -> publisher)` subscribes to the inner publisher inside a transaction bound to the Reactor `Context`. On `onComplete()`, the `R2dbcTransactionManager` commits. The `blockLast()` is used here only to run the reactive pipeline synchronously in a `main()` method — in a real WebFlux app you'd return the `Mono`/`Flux` directly.

---

### Level 2 — Intermediate

**`.as(operator::transactional)`** — composing the operator inline in a pipeline.

```java
// ReactiveTransactionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.r2dbc.core.*;
import org.springframework.r2dbc.connection.*;
import org.springframework.transaction.reactive.*;
import io.r2dbc.h2.*;
import reactor.core.publisher.*;

@Configuration
@ComponentScan
public class ReactiveTransactionDemo {
    @Bean public io.r2dbc.spi.ConnectionFactory connectionFactory() {
        return H2ConnectionFactory.inMemory("testdb2");
    }
    @Bean public DatabaseClient databaseClient(io.r2dbc.spi.ConnectionFactory cf) {
        return DatabaseClient.create(cf);
    }
    @Bean public ReactiveTransactionManager reactiveTransactionManager(io.r2dbc.spi.ConnectionFactory cf) {
        return new R2dbcTransactionManager(cf);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ReactiveTransactionDemo.class);
        var db = ctx.getBean(DatabaseClient.class);
        var tm = ctx.getBean(ReactiveTransactionManager.class);

        db.sql("CREATE TABLE products (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), stock INT)")
          .fetch().rowsUpdated().block();

        TransactionalOperator txOp = TransactionalOperator.create(tm);

        // Pipeline composed with .as(txOp::transactional)
        Mono<Long> insertAndAudit =
            db.sql("INSERT INTO products(name,stock) VALUES('Gadget',50)")
              .fetch().rowsUpdated()
              .flatMap(n ->
                db.sql("INSERT INTO products(name,stock) VALUES('Audit',0)")
                  .fetch().rowsUpdated()
                  .thenReturn(n))
              .as(txOp::transactional);   // wraps the WHOLE chain in a transaction

        insertAndAudit
          .doOnSuccess(n -> System.out.println("Both inserts committed: " + n + " product row(s)"))
          .doOnError(e -> System.out.println("Rolled back: " + e.getMessage()))
          .block();

        db.sql("SELECT name FROM products").fetch().all()
          .doOnNext(r -> System.out.println("Row: " + r)).blockLast();

        ctx.close();
    }
}
```

How to run: same classpath

`.as(txOp::transactional)` applies `transactional()` as a Reactor operator at the point where it is declared. The transaction wraps the entire upstream pipeline — both INSERTs run within the same R2DBC connection held in the Reactor Context.

---

### Level 3 — Advanced

**`@Transactional` on a reactive service method** — the declarative approach using `ReactiveTransactionManager`.

```java
// ReactiveTransactionDemo.java
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
public class ReactiveTransactionDemo {
    @Bean public io.r2dbc.spi.ConnectionFactory connectionFactory() {
        return H2ConnectionFactory.inMemory("testdb3");
    }
    @Bean public DatabaseClient databaseClient(io.r2dbc.spi.ConnectionFactory cf) {
        return DatabaseClient.create(cf);
    }
    @Bean public ReactiveTransactionManager transactionManager(io.r2dbc.spi.ConnectionFactory cf) {
        return new R2dbcTransactionManager(cf);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ReactiveTransactionDemo.class);
        var db = ctx.getBean(DatabaseClient.class);
        db.sql("CREATE TABLE products (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), stock INT)")
          .fetch().rowsUpdated().block();

        ctx.getBean(ProductService.class)
           .createProduct("Reactive Widget", 200)
           .doOnSuccess(n -> System.out.println("Committed: " + n + " row"))
           .block();

        db.sql("SELECT name, stock FROM products").fetch().all()
          .doOnNext(r -> System.out.println("Saved: " + r)).blockLast();

        ctx.close();
    }
}

@Service
class ProductService {
    private final DatabaseClient db;
    ProductService(DatabaseClient db) { this.db = db; }

    @Transactional    // reactive @Transactional — works with ReactiveTransactionManager
    public Mono<Long> createProduct(String name, int stock) {
        return db.sql("INSERT INTO products(name,stock) VALUES(:name,:stock)")
            .bind("name", name)
            .bind("stock", stock)
            .fetch().rowsUpdated()
            .doOnNext(n -> System.out.println("Inserted reactively: " + name));
    }
}
```

How to run: same classpath + `spring-tx.jar`

Spring detects that `transactionManager` is a `ReactiveTransactionManager` and wraps `createProduct()` using `ReactiveTransactionInterceptor` instead of the standard `TransactionInterceptor`. The returned `Mono<Long>` is subscribed to inside the reactive transaction — the transaction commits when the `Mono` completes or rolls back on error.

## 6. Walkthrough

**Level 1 — `execute()` subscription flow:**

```
TransactionalOperator.execute(status -> insertMono)
  → R2dbcTransactionManager.getReactiveTransaction()
     → cf.create()   [open R2DBC connection]
     → con.beginTransaction()
     → store con in Reactor Context under TX_KEY

  subscribe to insertMono:
    → DatabaseClient reads con from Reactor Context
    → executes "INSERT products ('Widget',100)" on con
    → onNext(1)   → System.out "Inserted 1 row(s)"
    → onComplete()

  TransactionalOperator.onComplete handler:
    → R2dbcTransactionManager.commit()
       → con.commitTransaction()
       → con.close()
       → Context cleared

blockLast() unblocks: returns
```

**Level 3 — `@Transactional` on reactive method:**

```
svc.createProduct("Reactive Widget", 200)
  → ReactiveTransactionInterceptor.invoke()
    → transactionManager.getReactiveTransaction(def)
       → connection acquired; stored in Reactor Context

  → Mono returned from createProduct()
    [decorated to add tx lifecycle hooks]

.block():
  subscribe starts
  → DatabaseClient.sql(INSERT) uses con from Context
  → onNext(1L) → doOnNext prints "Inserted reactively…"
  → onComplete()
  → interceptor hook fires: commit()
     → con.commitTransaction(); con.close()
  block() returns 1L
```

## 7. Gotchas & takeaways

> **`ThreadLocal`-based transaction context does not work in reactive pipelines.** If you accidentally use `DataSourceTransactionManager` with a reactive R2DBC setup, each R2DBC call gets a different connection (new connection per thread-switch) and they are not in the same transaction. Always use `R2dbcTransactionManager` (or another `ReactiveTransactionManager` implementation) with reactive code.

> **`@Transactional` on reactive methods returns a `Mono`/`Flux` — the transaction is not started until subscription.** If you call a `@Transactional` reactive method but never subscribe, no transaction starts and no code runs. This is reactive laziness — the annotation wraps the publisher, not the method call itself.

> **Error propagation rules are the same as imperative transactions.** An `onError` signal from the inner publisher triggers rollback; `onComplete` triggers commit. Spring also respects `rollbackFor` / `noRollbackFor` in reactive `@Transactional`.

- `TransactionalOperator.execute(status -> publisher)` — programmatic; owns the whole pipeline.
- `.as(txOp::transactional)` — inline composition; cleaner when the tx scope is one chain segment.
- `@Transactional` on reactive methods — declarative; requires `ReactiveTransactionManager` as the TM bean.
- Reactive transactions propagate via Reactor `Context`, not `ThreadLocal` — never mix `DataSourceTransactionManager` with R2DBC.
