---
card: spring-framework
gi: 248
slug: programmatic-transaction-management-transactiontemplate
title: Programmatic transaction management (TransactionTemplate)
---

## 1. What it is

`TransactionTemplate` is Spring's helper for **programmatic transaction management** — writing transaction control directly in code rather than via `@Transactional`. It wraps a `PlatformTransactionManager` and runs a callback inside a transaction, automatically committing on success or rolling back on unchecked exception.

```java
transactionTemplate.execute(status -> {
    jdbcTemplate.update("INSERT INTO orders ...", ...);
    return orderId;   // return value from the callback
});
```

It uses the **template method pattern**: `TransactionTemplate.execute()` handles begin/commit/rollback; you supply only the business logic as a `TransactionCallback<T>`.

## 2. Why & when

Use `TransactionTemplate` over `@Transactional` when:

- You need **mid-method transaction control** — start a transaction at one point, commit at another, depending on runtime conditions.
- You are writing **library code** without a Spring context, yet want transaction support.
- You need to **return a value** from the transaction callback (unlike `TransactionCallbackWithoutResult` which is void).
- You need to **mark the transaction rollback-only** without throwing an exception: `status.setRollbackOnly()`.

For the vast majority of service methods, `@Transactional` is cleaner. `TransactionTemplate` is for the edge cases.

## 3. Core concept

`TransactionTemplate` holds a reference to a `PlatformTransactionManager` and a `DefaultTransactionDefinition` for configuration (propagation, isolation, timeout, read-only). Calling `execute(callback)`:

1. Calls `transactionManager.getTransaction(this)` — opens or joins a transaction.
2. Invokes `callback.doInTransaction(status)` — your business logic.
3. If callback returns normally → `transactionManager.commit(status)`.
4. If callback throws `RuntimeException` or `Error` → `transactionManager.rollback(status)`.
5. If callback sets `status.setRollbackOnly()` then returns normally → commit is attempted but results in rollback.

`TransactionTemplate` is thread-safe once configured. Configure it once as a `@Bean` and inject it wherever needed.

## 4. Diagram

<svg viewBox="0 0 680 190" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="rarr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#f85149"/>
    </marker>
  </defs>

  <!-- Caller -->
  <rect x="10" y="75" width="90" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="55" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Application</text>

  <line x1="102" y1="95" x2="155" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- TransactionTemplate -->
  <rect x="155" y="30" width="210" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="260" y="53" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">TransactionTemplate</text>
  <line x1="165" y1="62" x2="355" y2="62" stroke="#8b949e" stroke-width="0.5"/>
  <text x="260" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">1. getTransaction()</text>
  <text x="260" y="96" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">2. callback.doInTransaction()</text>
  <text x="260" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">3a. commit()    ← normal</text>
  <text x="260" y="128" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">3b. rollback()  ← exception</text>
  <text x="260" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">configures: propagation/isolation/timeout</text>

  <line x1="367" y1="95" x2="420" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- PTM -->
  <rect x="420" y="60" width="240" height="70" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="83" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">PlatformTransactionManager</text>
  <text x="540" y="101" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">DataSourceTM / JpaTM / JtaTM</text>
  <text x="540" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">actual begin / commit / rollback</text>
</svg>

`TransactionTemplate` owns the begin/commit/rollback lifecycle; the callback owns the business logic.

## 5. Runnable example

Scenario: a **`ShipmentService`** — first using `TransactionTemplate` with a return value, then with conditional rollback, then with explicit configuration.

### Level 1 — Basic

`TransactionTemplate.execute()` with a return value — the simplest programmatic pattern.

```java
// TransactionTemplateDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.support.*;
import org.springframework.transaction.*;

@Configuration
@ComponentScan
public class TransactionTemplateDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("shipments-schema.sql").build();
    }

    @Bean public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    @Bean public TransactionTemplate transactionTemplate(PlatformTransactionManager tm) {
        return new TransactionTemplate(tm);   // thread-safe; configure once
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TransactionTemplateDemo.class);
        var tt = ctx.getBean(TransactionTemplate.class);
        var jdbc = new org.springframework.jdbc.core.JdbcTemplate(ctx.getBean(javax.sql.DataSource.class));

        Long shipmentId = tt.execute(status -> {
            jdbc.update("INSERT INTO shipments(tracking,status) VALUES(?,'CREATED')", "TRK-001");
            Long id = jdbc.queryForObject("SELECT id FROM shipments WHERE tracking=?", Long.class, "TRK-001");
            System.out.println("Shipment created with id=" + id);
            return id;   // return value from the transaction
        });
        System.out.println("Returned from template: id=" + shipmentId);
        ctx.close();
    }
}
```

`shipments-schema.sql`:
```sql
CREATE TABLE shipments (
  id       BIGINT AUTO_INCREMENT PRIMARY KEY,
  tracking VARCHAR(50) UNIQUE,
  status   VARCHAR(20)
);
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. TransactionTemplateDemo.java`

The callback returns a `Long` — `execute()` propagates it as the return value after committing the transaction. If the callback threw a `RuntimeException`, the transaction would rollback and the exception would propagate to the caller. No `@Transactional` annotation needed.

---

### Level 2 — Intermediate

**Conditional rollback** via `status.setRollbackOnly()` — mark rollback without throwing.

```java
// TransactionTemplateDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.support.*;
import org.springframework.transaction.*;
import java.util.*;

@Configuration
@ComponentScan
public class TransactionTemplateDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("shipments-schema.sql").build();
    }
    @Bean public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }
    @Bean public TransactionTemplate transactionTemplate(PlatformTransactionManager tm) {
        return new TransactionTemplate(tm);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TransactionTemplateDemo.class);
        var tt = ctx.getBean(TransactionTemplate.class);
        var jdbc = new org.springframework.jdbc.core.JdbcTemplate(ctx.getBean(javax.sql.DataSource.class));

        List<String> batch = List.of("TRK-002", "TRK-DUPE", "TRK-003");

        for (String tracking : batch) {
            tt.execute(status -> {
                try {
                    jdbc.update("INSERT INTO shipments(tracking,status) VALUES(?,'CREATED')", tracking);
                    System.out.println("Inserted: " + tracking);
                } catch (Exception e) {
                    System.out.println("Failed " + tracking + " — marking rollback-only (no throw)");
                    status.setRollbackOnly();   // mark without propagating exception
                }
                return null;    // TransactionCallbackWithoutResult alternative
            });
        }

        // Check what committed
        List<String> saved = jdbc.queryForList("SELECT tracking FROM shipments", String.class);
        System.out.println("Committed shipments: " + saved);
        ctx.close();
    }
}
```

How to run: same classpath

Each shipment is in its own template call (one transaction per iteration). If an INSERT fails (e.g., duplicate key), `setRollbackOnly()` marks that transaction for rollback — it rolls back silently without a thrown exception reaching the for-loop. Only successfully inserted shipments appear in the final query.

---

### Level 3 — Advanced

**Custom `TransactionTemplate` configuration** — per-operation template with different isolation and timeout; plus void callback via `TransactionCallbackWithoutResult`.

```java
// TransactionTemplateDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.support.*;

@Configuration
@ComponentScan
public class TransactionTemplateDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("shipments-schema.sql").build();
    }
    @Bean public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TransactionTemplateDemo.class);
        var tm = ctx.getBean(PlatformTransactionManager.class);
        var jdbc = new org.springframework.jdbc.core.JdbcTemplate(ctx.getBean(javax.sql.DataSource.class));

        // Write template: REQUIRED, READ_COMMITTED, 10s timeout
        TransactionTemplate writeTmpl = new TransactionTemplate(tm);
        writeTmpl.setTimeout(10);
        writeTmpl.setIsolationLevel(TransactionDefinition.ISOLATION_READ_COMMITTED);

        // Read-only template: REQUIRED, READ_COMMITTED, readOnly, 5s timeout
        TransactionTemplate readTmpl = new TransactionTemplate(tm);
        readTmpl.setReadOnly(true);
        readTmpl.setTimeout(5);

        // Write via TransactionCallbackWithoutResult (void callback)
        writeTmpl.execute(new TransactionCallbackWithoutResult() {
            @Override
            protected void doInTransactionWithoutResult(TransactionStatus status) {
                jdbc.update("INSERT INTO shipments(tracking,status) VALUES(?,'CREATED')", "TRK-010");
                jdbc.update("INSERT INTO shipments(tracking,status) VALUES(?,'CREATED')", "TRK-011");
                System.out.println("Write template: 2 shipments inserted");
            }
        });

        // Read via lambda — no return
        readTmpl.execute(status -> {
            var rows = jdbc.queryForList("SELECT tracking, status FROM shipments", String.class);
            System.out.println("Read template (readOnly): " + rows);
            return null;
        });

        ctx.close();
    }
}
```

How to run: same classpath

Two `TransactionTemplate` instances with different settings — no need for `@Configuration`-level beans. The write template uses `TransactionCallbackWithoutResult` (a convenience subclass for void callbacks). The read template is `readOnly=true`, which lets the JDBC driver and JPA skip lock acquisition and dirty-check flush.

## 6. Walkthrough

**Level 1 — `execute()` flow:**

```
tt.execute(callback)
  → AbstractPlatformTransactionManager.getTransaction(tt)
    → DataSourceTransactionManager.doBegin():
        con = pool.getConnection()
        con.setAutoCommit(false)
        bind con to ThreadLocal

  → callback.doInTransaction(status):
      jdbc.update("INSERT shipments…")   [on bound con]
      jdbc.queryForObject("SELECT id…")  [on bound con]
      return shipmentId

  → no exception → AbstractPlatformTransactionManager.commit(status):
      doCommit(): con.commit()
      con returned to pool; ThreadLocal cleared

  ← returns shipmentId to caller
```

**Level 2 — `setRollbackOnly()` path:**

```
tt.execute(status -> {
  try {
    jdbc.update("INSERT shipments 'TRK-DUPE'…")   → DataIntegrityViolationException (duplicate key)
  } catch (Exception e) {
    status.setRollbackOnly()   → TransactionStatus.rollbackOnly = true
  }
  return null;
})

after callback returns normally:
  commit(status) called
  → AbstractPlatformTransactionManager detects rollbackOnly=true
  → calls doRollback() instead
  → con.rollback(); con released
  ← execute() returns null (no exception thrown)
```

**Level 3 — two templates, different settings:**

```
writeTmpl.execute(callback):
  getTransaction(): con acquired; isolation=READ_COMMITTED; autoCommit=false; timeout=10s
  doInTransactionWithoutResult(): 2 INSERTs
  commit(): con.commit()

readTmpl.execute(callback):
  getTransaction(): new con acquired; isolation=READ_COMMITTED; readOnly=true; autoCommit=false; timeout=5s
  callback(): SELECT all shipments
  commit(): con.commit() (read-only — nothing dirty to flush)
```

## 7. Gotchas & takeaways

> **`execute()` re-throws `RuntimeException` and wraps checked exceptions in `UndeclaredThrowableException`.** If your callback throws a checked exception, the template wraps it. Use `executeWithoutResult()` (Spring 5.2+) or cast at the call site.

> **`TransactionTemplate` is `REQUIRED` propagation by default.** If called within an existing `@Transactional` method, it joins that transaction. Use `setPropagationBehavior(REQUIRES_NEW)` on the template to always open a fresh transaction.

> **`setRollbackOnly()` without throwing will still rollback.** The template checks `status.isRollbackOnly()` before calling `commit()` and redirects to `rollback()`. The exception is NOT thrown — `execute()` returns normally. Callers must check the return value or use a flag.

- `TransactionTemplate` is thread-safe once configured — declare as a singleton `@Bean`.
- Use `execute(status -> { ... return value; })` when you need a return value.
- Use `TransactionCallbackWithoutResult` for void operations (avoids the `return null` boilerplate).
- `Spring 5.2+` added `executeWithoutResult(Consumer<TransactionStatus>)` — cleaner alternative to `TransactionCallbackWithoutResult`.
