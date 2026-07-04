---
card: spring-framework
gi: 275
slug: reactive-transactions-with-r2dbc
title: Reactive transactions with R2DBC
---

## 1. What it is

**Reactive transactions** in Spring apply the same ACID guarantees as traditional transactions, but the coordination is done through reactive types (`Mono`/`Flux`) instead of thread-local storage. The key classes are:

- **`R2dbcTransactionManager`** — implements `ReactiveTransactionManager`; manages transactions over an R2DBC `ConnectionFactory`.
- **`TransactionalOperator`** — programmatic reactive transaction wrapper (equivalent to `TransactionTemplate` in JDBC).
- **`@Transactional`** — declarative, works on methods returning `Mono` or `Flux` (Spring AOP intercepts them and wraps in a transaction).

```java
// Declarative — method returns Mono; Spring wraps the whole subscription in a TX
@Transactional
public Mono<Void> transfer(long from, long to, double amount) {
    return debit(from, amount).then(credit(to, amount));
}

// Programmatic — explicit wrapping
Flux<Long> txOps = Flux.concat(debit(from, amt), credit(to, amt))
    .as(transactionalOperator::transactional);
```

## 2. Why & when

Traditional Spring transaction management stores the current transaction's `Connection` in a **thread-local** variable. In reactive code there is no stable "current thread" — a reactive pipeline can hop between threads at every operator. R2DBC transactions solve this by storing the connection in Reactor's **`Context`** (a per-subscription key-value store that travels with the reactive pipeline).

Use reactive transactions when:
- The entire stack is reactive (WebFlux + R2DBC).
- You need atomicity across multiple database operations in a reactive pipeline.
- Rolling back reactively on error (e.g., if the second operation fails, undo the first).

**Never mix** reactive and imperative transactions — don't call a `@Transactional` R2DBC method from a blocking `JdbcTemplate` context or vice versa.

## 3. Core concept

`ReactiveTransactionManager` replaces `PlatformTransactionManager`:

```java
// Traditional (blocking)
PlatformTransactionManager → getTransaction() → commit() → rollback()

// Reactive
ReactiveTransactionManager → getReactiveTransaction() → commit() → rollback()
  all methods return Mono<> — non-blocking
```

Reactor `Context` carries the transaction:
```
subscribe():
  → ReactiveTransactionManager.getReactiveTransaction()
  → acquires Connection from pool (Mono<Connection>)
  → stores Connection in Reactor Context

inside pipeline:
  → DatabaseClient.sql(...).fetch().all()
  → reads Connection from Context (not thread-local)
  → executes on the TX-bound Connection

on completion:
  → commit() or rollback()
  → releases Connection to pool
```

`TransactionalOperator.transactional(publisher)` is the programmatic API: it wraps any `Mono` or `Flux` and applies the transaction.

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

  <!-- Subscribe -->
  <rect x="10" y="90" width="100" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="60" y="113" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">subscribe()</text>
  <line x1="112" y1="110" x2="155" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- TX start -->
  <rect x="157" y="70" width="170" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="242" y="93" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">R2dbcTransactionManager</text>
  <line x1="167" y1="99" x2="317" y2="99" stroke="#8b949e" stroke-width="0.5"/>
  <text x="242" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1. acquire Connection</text>
  <text x="242" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2. store in Reactor Context</text>
  <line x1="329" y1="110" x2="372" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Reactor Context -->
  <rect x="374" y="80" width="160" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="454" y="102" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Reactor Context</text>
  <text x="454" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">key=CF → PooledConnection</text>

  <!-- DatabaseClient reads context -->
  <rect x="157" y="175" width="380" height="30" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="347" y="194" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">DatabaseClient reads TX-bound connection from Context</text>

  <!-- Commit/rollback -->
  <rect x="540" y="90" width="150" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="615" y="108" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">commit / rollback</text>
  <text x="615" y="122" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">on complete / onError</text>
  <line x1="536" y1="110" x2="693" y2="110" stroke="#8b949e" stroke-width="1" marker-end="url(#arr2)"/>
</svg>

TX state lives in Reactor `Context`; `DatabaseClient` reads it automatically. TX commits on `onComplete`, rolls back on `onError`.

## 5. Runnable example

Scenario: a **bank transfer** — debit from one account, credit another atomically; rollback if the second step fails.

### Level 1 — Basic

`TransactionalOperator` for programmatic reactive transaction.

```java
// ReactiveTransactionDemo.java
import io.r2dbc.h2.*;
import io.r2dbc.spi.ConnectionFactory;
import org.springframework.r2dbc.connection.R2dbcTransactionManager;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.transaction.ReactiveTransactionManager;
import org.springframework.transaction.reactive.TransactionalOperator;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class ReactiveTransactionDemo {

    static ConnectionFactory buildCF() {
        return new H2ConnectionFactory(H2ConnectionConfiguration.builder()
            .inMemory("bank").option("DB_CLOSE_DELAY=-1").build());
    }

    public static void main(String[] args) {
        ConnectionFactory cf = buildCF();
        DatabaseClient client = DatabaseClient.create(cf);
        ReactiveTransactionManager txm = new R2dbcTransactionManager(cf);
        TransactionalOperator tx = TransactionalOperator.create(txm);

        // Schema + seed
        client.sql("CREATE TABLE accounts (id BIGINT PRIMARY KEY, name VARCHAR(50), balance DOUBLE)")
            .fetch().rowsUpdated()
            .then(client.sql("INSERT INTO accounts VALUES(1,'Alice',1000.0)").fetch().rowsUpdated())
            .then(client.sql("INSERT INTO accounts VALUES(2,'Bob',500.0)").fetch().rowsUpdated())
            .block();

        // Transfer $200 from Alice to Bob — wrapped in a transaction
        Mono<Void> transfer = client.sql("UPDATE accounts SET balance=balance-:amt WHERE id=:id")
            .bind("amt",200.0).bind("id",1L).fetch().rowsUpdated()
            .then(client.sql("UPDATE accounts SET balance=balance+:amt WHERE id=:id")
                .bind("amt",200.0).bind("id",2L).fetch().rowsUpdated())
            .then();

        transfer.as(tx::transactional).block();

        // Verify
        client.sql("SELECT name, balance FROM accounts ORDER BY id")
            .fetch().all()
            .doOnNext(r -> System.out.printf("  %-6s $%.2f%n", r.get("NAME"), r.get("BALANCE")))
            .blockLast();
        // Alice: $800, Bob: $700
    }
}
```

How to run: `java -cp spring-r2dbc.jar:spring-tx.jar:r2dbc-spi.jar:r2dbc-h2.jar:reactor-core.jar:. ReactiveTransactionDemo.java`

`.as(tx::transactional)` wraps any `Mono` or `Flux` in a transaction. If any step in the chain emits `onError`, the transaction rolls back automatically. `R2dbcTransactionManager` acquires a connection from `cf`, begins the transaction, and stores the connection in the Reactor `Context` so `DatabaseClient` uses it for all subsequent SQL in the chain.

---

### Level 2 — Intermediate

Rollback on error — simulated failed transfer.

```java
// ReactiveTransactionDemo.java
import io.r2dbc.h2.*;
import io.r2dbc.spi.ConnectionFactory;
import org.springframework.r2dbc.connection.R2dbcTransactionManager;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.transaction.ReactiveTransactionManager;
import org.springframework.transaction.reactive.TransactionalOperator;
import reactor.core.publisher.Mono;

public class ReactiveTransactionDemo {

    static ConnectionFactory buildCF() {
        return new H2ConnectionFactory(H2ConnectionConfiguration.builder()
            .inMemory("bank").option("DB_CLOSE_DELAY=-1").build());
    }

    static void printBalances(DatabaseClient client) {
        client.sql("SELECT name, balance FROM accounts ORDER BY id")
            .fetch().all()
            .doOnNext(r -> System.out.printf("  %-6s $%.2f%n", r.get("NAME"), r.get("BALANCE")))
            .blockLast();
    }

    public static void main(String[] args) {
        ConnectionFactory cf = buildCF();
        DatabaseClient client = DatabaseClient.create(cf);
        TransactionalOperator tx = TransactionalOperator.create(new R2dbcTransactionManager(cf));

        client.sql("CREATE TABLE accounts (id BIGINT PRIMARY KEY, name VARCHAR(50), balance DOUBLE)")
            .fetch().rowsUpdated()
            .then(client.sql("INSERT INTO accounts VALUES(1,'Alice',1000.0)").fetch().rowsUpdated())
            .then(client.sql("INSERT INTO accounts VALUES(2,'Bob',500.0)").fetch().rowsUpdated())
            .block();

        System.out.println("Before failed transfer:");
        printBalances(client);

        // Attempt a transfer that fails mid-way
        Mono<Void> failingTransfer = client.sql(
            "UPDATE accounts SET balance=balance-:amt WHERE id=:id")
            .bind("amt",300.0).bind("id",1L).fetch().rowsUpdated()
            .then(Mono.error(new RuntimeException("Payment gateway failed!")))
            .then(client.sql(
                "UPDATE accounts SET balance=balance+:amt WHERE id=:id")
                .bind("amt",300.0).bind("id",2L).fetch().rowsUpdated())
            .then();

        failingTransfer.as(tx::transactional)
            .onErrorResume(e -> {
                System.out.println("Error caught: " + e.getMessage() + " — TX rolled back");
                return Mono.empty();
            })
            .block();

        System.out.println("After failed transfer (should be unchanged):");
        printBalances(client);
        // Both balances unchanged — rollback worked
    }
}
```

How to run: same classpath

When `Mono.error(...)` is emitted in the middle of the reactive chain, the `TransactionalOperator` intercepts `onError` and calls `ReactiveTransactionManager.rollback(status)` before propagating the error upstream. Alice's debit is undone — neither account changes.

---

### Level 3 — Advanced

`@Transactional` on a reactive method in a Spring `@Service` + propagation.

```java
// ReactiveTransactionDemo.java
import io.r2dbc.h2.*;
import io.r2dbc.spi.ConnectionFactory;
import org.springframework.context.annotation.*;
import org.springframework.r2dbc.connection.R2dbcTransactionManager;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.reactive.TransactionalOperator;
import reactor.core.publisher.Mono;

@Configuration
@EnableTransactionManagement
class BankConfig {
    @Bean ConnectionFactory connectionFactory() {
        return new H2ConnectionFactory(H2ConnectionConfiguration.builder()
            .inMemory("bank").option("DB_CLOSE_DELAY=-1").build());
    }
    @Bean DatabaseClient databaseClient(ConnectionFactory cf) { return DatabaseClient.create(cf); }
    @Bean ReactiveTransactionManager transactionManager(ConnectionFactory cf) {
        return new R2dbcTransactionManager(cf);
    }
}

@Service
class AccountService {
    private final DatabaseClient client;
    AccountService(DatabaseClient client) { this.client = client; }

    @Transactional
    public Mono<Void> transfer(long from, long to, double amount) {
        return client.sql("UPDATE accounts SET balance=balance-:amt WHERE id=:id")
            .bind("amt",amount).bind("id",from).fetch().rowsUpdated()
            .then(client.sql("UPDATE accounts SET balance=balance+:amt WHERE id=:id")
                .bind("amt",amount).bind("id",to).fetch().rowsUpdated())
            .then();
    }

    @Transactional(readOnly = true)
    public Mono<Double> getBalance(long id) {
        return client.sql("SELECT balance FROM accounts WHERE id=:id")
            .bind("id",id)
            .map(row -> row.get("balance", Double.class))
            .one();
    }
}

public class ReactiveTransactionDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(BankConfig.class, AccountService.class);
        DatabaseClient client = ctx.getBean(DatabaseClient.class);
        AccountService svc = ctx.getBean(AccountService.class);

        client.sql("CREATE TABLE accounts (id BIGINT PRIMARY KEY, name VARCHAR(50), balance DOUBLE)")
            .fetch().rowsUpdated()
            .then(client.sql("INSERT INTO accounts VALUES(1,'Alice',1000.0)").fetch().rowsUpdated())
            .then(client.sql("INSERT INTO accounts VALUES(2,'Bob',500.0)").fetch().rowsUpdated())
            .block();

        // @Transactional wraps the Mono — TX begins on subscribe, commits on onComplete
        svc.transfer(1L, 2L, 150.0).block();

        System.out.printf("Alice: $%.2f%n", svc.getBalance(1L).block());
        System.out.printf("Bob:   $%.2f%n", svc.getBalance(2L).block());
        ctx.close();
    }
}
```

How to run: same classpath + spring-context.jar + spring-aspects.jar

`@Transactional` on a reactive method (returning `Mono`/`Flux`) triggers Spring AOP to wrap the subscription in a transaction via `R2dbcTransactionManager`. The transaction does NOT begin when `transfer()` is called — it begins when the caller subscribes to the returned `Mono`. `@Transactional(readOnly=true)` hints the database driver to optimise for read-only access.

## 6. Walkthrough

**Level 1 — `transfer` wrapped in `TransactionalOperator` (execution order):**

1. **`transfer.as(tx::transactional).block()`**: subscribes. `TransactionalOperator.transactional(transfer)` intercepts the subscription.
2. **`R2dbcTransactionManager.getReactiveTransaction()`**: acquires a `Connection` from the `ConnectionFactory`, calls `connection.beginTransaction()` → `Mono<Void>`.
3. **Connection stored in Reactor `Context`** under the `ConnectionFactory` key.
4. **First UPDATE**: `DatabaseClient` detects TX-bound connection in Context — reuses it. `UPDATE accounts SET balance=balance-200 WHERE id=1` — Alice's balance `1000 → 800`.
5. **Second UPDATE** (chained via `.then()`): same TX-bound connection. `UPDATE accounts SET balance=balance+200 WHERE id=2` — Bob's balance `500 → 700`.
6. **`Mono<Void>` completes** — `TransactionalOperator` calls `R2dbcTransactionManager.commit()` → `connection.commitTransaction()`. Changes made permanent.
7. **Connection released** to pool.

For the failing transfer (Level 2), step 4 runs (Alice debited), then `Mono.error(...)` triggers `onError`. `TransactionalOperator` calls `rollback()` → `connection.rollbackTransaction()`. Alice's debit is undone.

```
Normal TX:
  beginTransaction()
  UPDATE ... WHERE id=1  → Alice: 1000→800
  UPDATE ... WHERE id=2  → Bob:   500→700
  commit()              → persisted

Failed TX:
  beginTransaction()
  UPDATE ... WHERE id=1  → Alice: 1000→800 (in TX, not committed)
  Mono.error() fired
  rollback()            → Alice: 800→1000 (undone)
```

## 7. Gotchas & takeaways

> **`@Transactional` on reactive methods: the transaction begins at subscription time, NOT at method call time.** If the method is called but the returned `Mono` is never subscribed to, no transaction ever begins. This is a fundamental difference from blocking `@Transactional`.

> **Never block inside a `@Transactional` reactive method.** Calling `.block()` inside a reactive TX method will deadlock the event loop. Use `.then()`, `flatMap()`, and other reactive operators to chain operations.

> **`@Transactional` `propagation = REQUIRES_NEW` works reactively** via Reactor `Context` substitution — the inner transaction uses a new connection stored in a child Context while the outer TX connection is preserved in the parent Context.

- `R2dbcTransactionManager` — drives reactive TX via Reactor Context (not thread-local).
- `TransactionalOperator.transactional(publisher)` — programmatic TX wrapper for any `Mono`/`Flux`.
- `@Transactional` works on reactive methods — TX begins at subscribe, commits at onComplete, rolls back at onError.
- Both `DatabaseClient` and `TransactionManager` must share the same `ConnectionFactory`.
- Never `.block()` inside a reactive TX method — deadlock risk.
