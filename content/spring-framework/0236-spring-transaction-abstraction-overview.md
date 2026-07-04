---
card: spring-framework
gi: 236
slug: spring-transaction-abstraction-overview
title: Spring transaction abstraction overview
---

## 1. What it is

Spring's **transaction abstraction** is a unified API that lets you write transactional code once, independent of the underlying technology — JDBC, JPA, Hibernate, JTA, or any other. The abstraction sits above the technology-specific transaction managers and provides a single programming model for all of them.

The three core interfaces are:

- `PlatformTransactionManager` — the central strategy: `getTransaction`, `commit`, `rollback`.
- `TransactionDefinition` — the configuration: propagation, isolation, timeout, read-only flag.
- `TransactionStatus` — the live handle to the current transaction: is it new? is it rolled back?

```java
// The same code works whether the TM is JDBC, JPA, or JTA:
TransactionStatus tx = txManager.getTransaction(new DefaultTransactionDefinition());
try {
    // ... business logic
    txManager.commit(tx);
} catch (Exception e) {
    txManager.rollback(tx);
    throw e;
}
```

## 2. Why & when

Before Spring, transaction code was technology-specific: `Connection.setAutoCommit(false)` for JDBC, `EntityManager.getTransaction()` for JPA, `UserTransaction` for JTA. Changing the persistence technology meant rewriting all transaction management.

Spring's abstraction solves this by:
1. **Decoupling** transaction control from resource management.
2. Allowing **declarative transactions** (`@Transactional`) that apply to any backend.
3. Supporting **transaction synchronization** — registering callbacks that run at commit/rollback time, regardless of the underlying resource type.

Use the abstraction directly (programmatic) only when you need fine-grained control. In most apps `@Transactional` (declarative) is sufficient.

## 3. Core concept

The relationship between the three interfaces:

```
TransactionDefinition (configuration)
  propagation / isolation / timeout / readOnly
        │
        ▼
PlatformTransactionManager.getTransaction(def)
        │
        ▼
TransactionStatus (live handle)
  isNewTransaction / hasSavepoint / isRollbackOnly
        │
   commit(status) or rollback(status)
```

Spring ships concrete implementations for every common technology:

| TransactionManager | Technology |
|-------------------|-----------|
| `DataSourceTransactionManager` | JDBC / Spring JDBC |
| `JpaTransactionManager` | JPA / Hibernate |
| `JtaTransactionManager` | JTA / distributed transactions |
| `R2dbcTransactionManager` | R2DBC (reactive) |
| `MongoTransactionManager` | MongoDB |

You declare exactly one as a `@Bean`; `@Transactional` uses it automatically.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- App -->
  <rect x="10" y="75" width="120" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="96" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Application</text>
  <text x="70" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Transactional</text>

  <line x1="132" y1="100" x2="188" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Abstraction layer -->
  <rect x="188" y="50" width="200" height="100" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="288" y="72" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Spring TX Abstraction</text>
  <line x1="198" y1="80" x2="378" y2="80" stroke="#8b949e" stroke-width="0.5"/>
  <text x="288" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">PlatformTransactionManager</text>
  <text x="288" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">TransactionDefinition</text>
  <text x="288" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">TransactionStatus</text>

  <line x1="390" y1="100" x2="445" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Implementations -->
  <rect x="445" y="30" width="240" height="140" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="565" y="52" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Concrete Implementations</text>
  <line x1="455" y1="60" x2="675" y2="60" stroke="#8b949e" stroke-width="0.5"/>
  <text x="565" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">DataSourceTransactionManager</text>
  <text x="565" y="97" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">JpaTransactionManager</text>
  <text x="565" y="114" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">JtaTransactionManager</text>
  <text x="565" y="131" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">R2dbcTransactionManager</text>
  <text x="565" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">MongoTransactionManager</text>
</svg>

App code targets the abstraction; switching from JDBC to JPA is one bean swap.

## 5. Runnable example

Scenario: a **`BankingService`** that transfers funds — first using `DataSourceTransactionManager` programmatically, then switching to `JpaTransactionManager` without touching business logic.

### Level 1 — Basic

Programmatic transaction with `DataSourceTransactionManager` and JDBC.

```java
// TxAbstractionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.transaction.*;
import org.springframework.transaction.support.*;

@Configuration
public class TxAbstractionDemo {
    @Bean
    public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("schema.sql")
            .build();
    }

    @Bean
    public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxAbstractionDemo.class);
        var txManager = ctx.getBean(PlatformTransactionManager.class);
        var ds = ctx.getBean(javax.sql.DataSource.class);

        DefaultTransactionDefinition def = new DefaultTransactionDefinition();
        def.setName("fund-transfer");
        def.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRED);

        TransactionStatus status = txManager.getTransaction(def);
        try {
            var jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
            jdbc.update("UPDATE accounts SET balance = balance - ? WHERE id = ?", 100, 1);
            jdbc.update("UPDATE accounts SET balance = balance + ? WHERE id = ?", 100, 2);
            txManager.commit(status);
            System.out.println("Transfer committed");
        } catch (Exception e) {
            txManager.rollback(status);
            System.out.println("Transfer rolled back: " + e.getMessage());
        }
        ctx.close();
    }
}
```

`schema.sql` (on classpath):
```sql
CREATE TABLE accounts (id INT PRIMARY KEY, balance DECIMAL(10,2));
INSERT INTO accounts VALUES (1, 1000.00), (2, 500.00);
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. TxAbstractionDemo.java`

`txManager.getTransaction(def)` opens a JDBC connection and sets autoCommit=false. Both UPDATEs run in the same connection. `commit(status)` calls `connection.commit()`. The abstraction hides all JDBC resource management.

---

### Level 2 — Intermediate

Same transfer logic but the `PlatformTransactionManager` is declared — showing how swapping the bean changes the technology without touching `BankingService`.

```java
// TxAbstractionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxAbstractionDemo {
    @Bean
    public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("schema.sql")
            .build();
    }

    @Bean
    public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        // Swap to JpaTransactionManager or JtaTransactionManager here — BankingService unchanged
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxAbstractionDemo.class);
        ctx.getBean(BankingService.class).transfer(1, 2, 200.0);
        ctx.close();
    }
}

@Service
class BankingService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;

    BankingService(javax.sql.DataSource ds) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
    }

    @Transactional   // uses whatever PlatformTransactionManager is registered
    public void transfer(int fromId, int toId, double amount) {
        jdbc.update("UPDATE accounts SET balance = balance - ? WHERE id = ?", amount, fromId);
        jdbc.update("UPDATE accounts SET balance = balance + ? WHERE id = ?", amount, toId);
        System.out.printf("Transferred $%.2f from %d to %d%n", amount, fromId, toId);
    }
}
```

How to run: same classpath

`@Transactional` resolves the `PlatformTransactionManager` bean automatically. Changing `DataSourceTransactionManager` to `JpaTransactionManager` in the `@Bean` method is the only change needed to switch from JDBC to JPA transactions.

---

### Level 3 — Advanced

**Transaction synchronization** — registering a callback that runs after commit, using `TransactionSynchronizationManager`. Shows direct interaction with the abstraction internals.

```java
// TxAbstractionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.support.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxAbstractionDemo {
    @Bean
    public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("schema.sql")
            .build();
    }

    @Bean
    public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxAbstractionDemo.class);
        ctx.getBean(BankingService.class).transfer(1, 2, 300.0);
        ctx.close();
    }
}

@Service
class BankingService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;

    BankingService(javax.sql.DataSource ds) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
    }

    @Transactional
    public void transfer(int fromId, int toId, double amount) {
        jdbc.update("UPDATE accounts SET balance = balance - ? WHERE id = ?", amount, fromId);
        jdbc.update("UPDATE accounts SET balance = balance + ? WHERE id = ?", amount, toId);

        // Register an after-commit callback — fires only if the transaction commits
        TransactionSynchronizationManager.registerSynchronization(
            new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    System.out.printf("[NOTIFICATION] Transfer of $%.2f committed — send email%n", amount);
                }
                @Override
                public void afterCompletion(int status) {
                    String outcome = status == TransactionSynchronization.STATUS_COMMITTED
                        ? "COMMITTED" : "ROLLED_BACK";
                    System.out.println("[AUDIT] transaction outcome: " + outcome);
                }
            }
        );

        System.out.printf("Transfer $%.2f queued within transaction%n", amount);
    }
}
```

How to run: same classpath

`TransactionSynchronizationManager.registerSynchronization()` attaches a lifecycle hook to the active transaction — part of Spring's abstraction layer. The `afterCommit()` callback fires only on successful commit; `afterCompletion()` fires regardless of outcome. This is how Spring's `@ApplicationEvent` publishing defers events until after commit.

## 6. Walkthrough

**Level 1 — programmatic path, step by step:**

1. `txManager.getTransaction(def)` is called.
2. `DataSourceTransactionManager` calls `DataSourceUtils.getConnection(dataSource)` — borrows a `Connection` from the pool and sets `autoCommit=false`.
3. The `TransactionStatus` returned holds a reference to this connection via `DataSourceTransactionObject`.
4. Both `JdbcTemplate.update()` calls use the **same connection** (bound to the current thread via `TransactionSynchronizationManager`'s `ThreadLocal`).
5. `txManager.commit(status)` calls `connection.commit()`, then returns the connection to the pool.

**State trace:**

```
txManager.getTransaction(def)
  → connection acquired from pool
  → autoCommit = false
  → connection bound to ThreadLocal

jdbc.update("UPDATE accounts ... id=1")   → executes on bound connection
jdbc.update("UPDATE accounts ... id=2")   → executes on SAME bound connection

txManager.commit(status)
  → connection.commit()
  → connection.setAutoCommit(true)
  → connection returned to pool
  → ThreadLocal cleared
```

**Level 3 — synchronization callbacks:**

```
@Transactional transfer() runs
  → tx opens
  → both UPDATEs execute
  → TransactionSynchronizationManager.registerSynchronization(hook)
     stores hook in ThreadLocal list

txManager.commit(status)
  → connection.commit()
  → for each registered synchronization:
      hook.afterCommit()    [prints "[NOTIFICATION] Transfer … committed"]
      hook.afterCompletion(STATUS_COMMITTED)  [prints "[AUDIT] … COMMITTED"]
  → ThreadLocal cleared
```

## 7. Gotchas & takeaways

> **There can be multiple `PlatformTransactionManager` beans.** If you have both JPA and MongoDB, declare two TMs and use `@Transactional("mongoTransactionManager")` to select which one. Spring does not auto-select between two TMs of different types.

> **`TransactionSynchronizationManager` is thread-bound.** Its `ThreadLocal`s are valid only inside an active transaction on the current thread. Calling `registerSynchronization()` outside a transaction throws `IllegalStateException`.

- The abstraction's value is portability — the same `@Transactional`-annotated service works with any backend.
- `DataSourceTransactionManager` for JDBC, `JpaTransactionManager` for JPA — never mix them on the same datasource (they manage connections independently and will deadlock).
- `TransactionSynchronization.afterCommit()` is the right place to send emails, publish events, or enqueue jobs — not inside the transaction body (where a rollback would undo the work but the side effect would have already happened).
- `TransactionStatus.isRollbackOnly()` returns `true` if the transaction has been marked for rollback but not yet rolled back.
