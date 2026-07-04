---
card: spring-framework
gi: 240
slug: transactionstatus
title: TransactionStatus
---

## 1. What it is

`TransactionStatus` is the live handle to an active transaction. `PlatformTransactionManager.getTransaction()` returns one, and you pass it back to `commit()` or `rollback()`. It answers three questions about the transaction's current state:

```java
public interface TransactionStatus extends TransactionExecution, SavepointManager {
    boolean isNewTransaction();      // did this call actually open a new tx?
    boolean hasSavepoint();          // is this a NESTED execution point?
    boolean isRollbackOnly();        // has someone marked this tx for rollback?
    void setRollbackOnly();          // mark it for rollback without throwing
    boolean isCompleted();           // has commit or rollback already been called?
    // from SavepointManager:
    Object createSavepoint();
    void rollbackToSavepoint(Object savepoint);
    void releaseSavepoint(Object savepoint);
}
```

In declarative `@Transactional` code you rarely interact with `TransactionStatus` directly — the proxy does it for you. It is essential for programmatic transactions.

## 2. Why & when

`TransactionStatus` is needed when:

1. **Programmatic transaction control** — you call `txManager.getTransaction()` manually and need to track the live state.
2. **Conditional rollback** — you want to mark the transaction for rollback (via `setRollbackOnly()`) without throwing an exception.
3. **Savepoint management** — you create and release savepoints within a JDBC transaction for partial rollback.
4. **Introspection** — you want to know whether `REQUIRED` joined an existing transaction (`isNewTransaction() == false`) or opened a new one.

## 3. Core concept

`isNewTransaction()` is particularly important for propagation logic:

- `REQUIRED` joins an existing transaction → `isNewTransaction()` returns `false`. The called code is a participant — if it calls `rollback()`, it will actually just mark the transaction rollback-only; the outer code is responsible for the final commit or rollback.
- `REQUIRES_NEW` always opens a new transaction → `isNewTransaction()` returns `true`. This code is the owner — it commits or rolls back independently.

`setRollbackOnly()` is the programmatic equivalent of throwing an unchecked exception inside `@Transactional`: it marks the transaction so that the next `commit()` call is silently converted to a rollback.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- TM -->
  <rect x="10" y="60" width="200" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="83" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">PlatformTransactionManager</text>
  <text x="110" y="101" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">getTransaction(def)</text>
  <text x="110" y="117" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">commit(status)</text>
  <text x="110" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">rollback(status)</text>

  <line x1="212" y1="100" x2="265" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="239" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">returns</text>

  <!-- TransactionStatus -->
  <rect x="265" y="30" width="230" height="140" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="380" y="53" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">TransactionStatus</text>
  <line x1="275" y1="62" x2="485" y2="62" stroke="#8b949e" stroke-width="0.5"/>
  <text x="380" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">isNewTransaction()</text>
  <text x="380" y="96" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">hasSavepoint()</text>
  <text x="380" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">isRollbackOnly()</text>
  <text x="380" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">setRollbackOnly()</text>
  <text x="380" y="144" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">isCompleted()</text>
  <text x="380" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">createSavepoint()</text>

  <line x1="497" y1="100" x2="550" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="524" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">passed to</text>

  <!-- App -->
  <rect x="550" y="70" width="120" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="610" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Application</text>
  <text x="610" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">inspect / mark</text>
  <text x="610" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">commit / rollback</text>
</svg>

`getTransaction()` returns the live status handle; the application inspects and commits/rolls back through it.

## 5. Runnable example

Scenario: a **`BatchImporter`** processing records — first using `TransactionStatus` for conditional rollback, then for savepoints.

### Level 1 — Basic

Use `TransactionStatus.isNewTransaction()` to log whether we opened a new transaction or joined an existing one.

```java
// TxStatusDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.support.*;

@Configuration
public class TxStatusDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("items-schema.sql").build();
    }
    @Bean public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxStatusDemo.class);
        var tm = ctx.getBean(PlatformTransactionManager.class);
        var ds = ctx.getBean(javax.sql.DataSource.class);

        // Programmatic transaction
        DefaultTransactionDefinition def = new DefaultTransactionDefinition();
        def.setName("batch-import");

        TransactionStatus outer = tm.getTransaction(def);
        System.out.println("Outer tx: isNewTransaction=" + outer.isNewTransaction());
        // isNewTransaction=true — we opened a fresh transaction

        // Simulate inner call with REQUIRED
        DefaultTransactionDefinition innerDef = new DefaultTransactionDefinition();
        innerDef.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRED);
        TransactionStatus inner = tm.getTransaction(innerDef);
        System.out.println("Inner tx: isNewTransaction=" + inner.isNewTransaction());
        // isNewTransaction=false — joined the outer transaction

        // Must commit outer, not inner (inner has no independent lifecycle)
        tm.commit(outer);
        System.out.println("Outer committed. isCompleted=" + outer.isCompleted());
        ctx.close();
    }
}
```

`items-schema.sql`: `CREATE TABLE items (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100));`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. TxStatusDemo.java`

`inner.isNewTransaction()` returns `false` — `REQUIRED` reused the outer connection. Committing the inner status does nothing (it's a participant). Only `outer.commit()` does the real commit.

---

### Level 2 — Intermediate

`setRollbackOnly()` — mark a transaction for rollback without throwing an exception.

```java
// TxStatusDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.support.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxStatusDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("items-schema.sql").build();
    }
    @Bean public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxStatusDemo.class);
        ctx.getBean(BatchImporter.class).importBatch(
            java.util.List.of("valid-item", "invalid!item", "another-valid"));
        ctx.close();
    }
}

@org.springframework.stereotype.Service
class BatchImporter {
    private final PlatformTransactionManager tm;
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;

    BatchImporter(PlatformTransactionManager tm, javax.sql.DataSource ds) {
        this.tm = tm; this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
    }

    public void importBatch(java.util.List<String> items) {
        DefaultTransactionDefinition def = new DefaultTransactionDefinition();
        TransactionStatus status = tm.getTransaction(def);
        try {
            for (String item : items) {
                if (item.contains("!")) {
                    System.out.println("[SKIP] invalid item: " + item + " — marking rollback-only");
                    status.setRollbackOnly();     // mark without throwing
                    break;
                }
                jdbc.update("INSERT INTO items(name) VALUES(?)", item);
                System.out.println("[INSERT] " + item);
            }

            if (status.isRollbackOnly()) {
                tm.rollback(status);
                System.out.println("Batch rolled back due to validation failure");
            } else {
                tm.commit(status);
                System.out.println("Batch committed");
            }
        } catch (Exception e) {
            tm.rollback(status);
            throw e;
        }
    }
}
```

How to run: same classpath

`setRollbackOnly()` marks the transaction for rollback without throwing. The loop continues (or breaks) cleanly. The explicit `isRollbackOnly()` check after the loop decides whether to `commit` or `rollback`. This pattern is useful when you want to validate all items before deciding, without using exceptions for flow control.

---

### Level 3 — Advanced

**Manual savepoints** — partially roll back a sub-operation while keeping the outer transaction alive.

```java
// TxStatusDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.support.*;

@Configuration
public class TxStatusDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("items-schema.sql").build();
    }
    @Bean public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxStatusDemo.class);
        var tm = ctx.getBean(PlatformTransactionManager.class);
        var ds = ctx.getBean(javax.sql.DataSource.class);
        var jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);

        TransactionStatus status = tm.getTransaction(new DefaultTransactionDefinition());

        jdbc.update("INSERT INTO items(name) VALUES(?)", "item-before-savepoint");
        System.out.println("[TX] inserted item-before-savepoint");

        // Create savepoint
        Object sp = status.createSavepoint();
        System.out.println("[TX] savepoint created");

        jdbc.update("INSERT INTO items(name) VALUES(?)", "item-after-savepoint");
        System.out.println("[TX] inserted item-after-savepoint");

        // Simulate failure after savepoint — roll back only the post-savepoint work
        status.rollbackToSavepoint(sp);
        System.out.println("[TX] rolled back to savepoint (item-after-savepoint undone)");

        status.releaseSavepoint(sp);

        tm.commit(status);
        System.out.println("[TX] committed. Checking what survived:");
        var ctx2 = new AnnotationConfigApplicationContext(TxStatusDemo.class);
        var jdbc2 = new org.springframework.jdbc.core.JdbcTemplate(ctx2.getBean(javax.sql.DataSource.class));
        // NOTE: In-memory H2 is shared; items should reflect only the pre-savepoint insert
        System.out.println("Items after commit: (expect only pre-savepoint row)");
        ctx.close();
    }
}
```

How to run: same classpath

`createSavepoint()` sets a JDBC savepoint (`SAVEPOINT sp1`) on the current connection. `rollbackToSavepoint(sp)` executes `ROLLBACK TO SAVEPOINT sp1`. Only the work done after the savepoint is undone; `item-before-savepoint` survives and is committed. This is the manual equivalent of `PROPAGATION_NESTED`.

## 6. Walkthrough

**Level 2 — `setRollbackOnly()` path:**

```
importBatch(["valid-item", "invalid!item", "another-valid"])
  status = tm.getTransaction(def)      → conn acquired, autoCommit=false
  status.isNewTransaction() == true

  loop item="valid-item":
    jdbc.update("INSERT items ... 'valid-item'")  → SQL executed on conn

  loop item="invalid!item":
    contains "!" → status.setRollbackOnly()
                   TransactionStatus.rollbackOnly = true
    break

  status.isRollbackOnly() == true
    → tm.rollback(status)
       conn.rollback()           ← both the valid-item INSERT and everything undone
       conn released
  prints "Batch rolled back"
```

**Level 3 — savepoint lifecycle:**

```
status = tm.getTransaction(def)    → conn acquired

INSERT items "item-before-savepoint"   → SQL on conn (not yet committed)

sp = status.createSavepoint()
  → conn.setSavepoint("SAVEPOINT_1")   → JDBC savepoint created

INSERT items "item-after-savepoint"    → SQL on conn (not yet committed)

status.rollbackToSavepoint(sp)
  → conn.rollback(SAVEPOINT_1)         → undoes only "item-after-savepoint" INSERT

status.releaseSavepoint(sp)
  → conn.releaseSavepoint(SAVEPOINT_1) → frees savepoint resources

tm.commit(status)
  → conn.commit()                      → commits "item-before-savepoint" only
  → conn released
```

## 7. Gotchas & takeaways

> **Calling `commit()` on a participant `TransactionStatus` (`isNewTransaction()==false`) triggers `UnexpectedRollbackException` if the TM detects you're committing the wrong status.** Only commit or rollback the status returned by `getTransaction()` for a new transaction; for a participant, you're just a borrower.

> **`createSavepoint()` is only supported by `DataSourceTransactionManager` (JDBC).** `JtaTransactionManager` does not expose savepoints through `TransactionStatus`. Use `PROPAGATION_NESTED` with `JdbcTemplate` if you need partial rollback.

> **`isCompleted()` returns `true` after commit or rollback.** Using a completed `TransactionStatus` in any further operation throws `IllegalTransactionStateException`.

- `isNewTransaction()` — check before committing; only the tx owner should commit.
- `setRollbackOnly()` — prefer over throwing an exception when you want to control rollback semantics without disrupting the call stack.
- `isRollbackOnly()` — check after calling sub-services; if they marked the tx rollback-only, there is no point continuing.
- `createSavepoint()` / `rollbackToSavepoint()` — use for partial rollback within a single JDBC transaction; prefer `PROPAGATION_NESTED` for Spring-managed code.
