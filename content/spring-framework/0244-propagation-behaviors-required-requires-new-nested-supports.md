---
card: spring-framework
gi: 244
slug: propagation-behaviors-required-requires-new-nested-supports
title: Propagation behaviors (REQUIRED, REQUIRES_NEW, NESTED, SUPPORTS, etc.)
---

## 1. What it is

**Transaction propagation** defines what happens when a method annotated with `@Transactional` is called while a transaction may already be active. Spring offers seven propagation behaviours, controlled by the `propagation` attribute:

```java
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void auditLog(String msg) { ... }
```

The choice determines whether the called method runs inside the caller's transaction, starts its own, or requires (or forbids) an existing one.

## 2. Why & when

| Behaviour | Use when |
|-----------|---------|
| `REQUIRED` | Default — the called method joins the outer tx; both succeed or both fail together |
| `REQUIRES_NEW` | The inner operation (audit, notification) must commit/rollback independently |
| `SUPPORTS` | Works with or without a tx — use for queries that can tolerate either context |
| `NOT_SUPPORTED` | Must run outside any tx — legacy code that breaks inside transactions |
| `MANDATORY` | Must be called from within an active tx — programming guard for internal APIs |
| `NEVER` | Must NOT be called within a tx — administrative or unsafe operations |
| `NESTED` | Sub-operation that can partially roll back via savepoint, but stays in the outer tx |

## 3. Core concept

```
REQUIRED          REQUIRES_NEW           NESTED            SUPPORTS
Outer Tx ┐        Outer Tx  Inner Tx    Outer Tx           (with tx)  (without)
  Inner ─┘        SUSPEND ─► NEW       [SAVEPOINT]          Inner Tx   no tx
  (joins)         RESUME ◄             rollback to SP       (joins)    runs anyway
```

**`REQUIRED`** (default): if an outer transaction exists, the called method participates in it. The `TransactionStatus.isNewTransaction()` returns `false`. If the inner method marks the tx rollback-only, the outer commit will throw `UnexpectedRollbackException`.

**`REQUIRES_NEW`**: Spring suspends the outer transaction (stores its connection/session in the thread context), opens a new independent transaction. After the inner method completes (commit or rollback), the outer transaction resumes. This means the inner tx's result is visible to the outer tx only after the outer commits (in SERIALIZABLE mode) or via re-read.

**`NESTED`**: uses JDBC savepoints. The inner method executes within the same physical transaction as the outer, but a savepoint is set before it. If the inner rolls back, only the work after the savepoint is undone — the outer transaction continues. `NESTED` is only supported by `DataSourceTransactionManager` (JDBC).

**`SUPPORTS`**: joins a transaction if one exists; runs without if none. Suitable for read-only helpers that can tolerate either context.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="rarr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#f85149"/>
    </marker>
  </defs>

  <!-- REQUIRED -->
  <rect x="10" y="20" width="150" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">REQUIRED</text>
  <rect x="25" y="50" width="120" height="40" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="85" y="67" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Outer Tx</text>
  <rect x="35" y="58" width="100" height="24" rx="3" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="85" y="73" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Inner (joins)</text>

  <!-- REQUIRES_NEW -->
  <rect x="175" y="20" width="150" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="250" y="40" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">REQUIRES_NEW</text>
  <rect x="185" y="50" width="60" height="40" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="215" y="64" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Outer</text>
  <text x="215" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">suspended</text>
  <rect x="255" y="50" width="60" height="40" rx="3" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="285" y="64" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Inner</text>
  <text x="285" y="78" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">new tx</text>

  <!-- NESTED -->
  <rect x="340" y="20" width="150" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="415" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">NESTED</text>
  <rect x="350" y="50" width="130" height="40" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="370" y="64" fill="#8b949e" font-size="8" font-family="sans-serif">Outer Tx</text>
  <rect x="390" y="54" width="82" height="30" rx="3" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="431" y="67" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">[SAVEPOINT]</text>
  <text x="431" y="79" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Inner (same conn)</text>

  <!-- SUPPORTS / MANDATORY / NEVER -->
  <rect x="505" y="20" width="185" height="200" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="593" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Others</text>
  <line x1="515" y1="48" x2="680" y2="48" stroke="#8b949e" stroke-width="0.5"/>
  <text x="593" y="66" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">SUPPORTS</text>
  <text x="593" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">joins if exists; no tx if not</text>
  <line x1="515" y1="90" x2="680" y2="90" stroke="#8b949e" stroke-width="0.3"/>
  <text x="593" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">NOT_SUPPORTED</text>
  <text x="593" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">suspends outer; runs without tx</text>
  <line x1="515" y1="132" x2="680" y2="132" stroke="#8b949e" stroke-width="0.3"/>
  <text x="593" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">MANDATORY</text>
  <text x="593" y="164" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">throws if no active tx</text>
  <line x1="515" y1="174" x2="680" y2="174" stroke="#8b949e" stroke-width="0.3"/>
  <text x="593" y="192" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">NEVER</text>
  <text x="593" y="206" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">throws if active tx exists</text>
</svg>

Seven propagation modes. `REQUIRED` (default) joins; `REQUIRES_NEW` suspends + creates new; `NESTED` uses a savepoint.

## 5. Runnable example

Scenario: an **`OrderService`** calling an `AuditService` and an `InventoryService` — demonstrating `REQUIRED`, `REQUIRES_NEW`, and `NESTED` on the same order-placement flow.

### Level 1 — Basic

`REQUIRED` (default) — inner and outer share one transaction.

```java
// PropagationDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class PropagationDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PropagationDemo.class);
        try {
            ctx.getBean(OrderService.class).placeOrder("ORD-1", "ITEM-X");
        } catch (Exception e) {
            System.out.println("Both order + inventory rolled back: " + e.getMessage());
        }
        ctx.close();
    }
}

@Service
class OrderService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    private final InventoryService inv;
    OrderService(javax.sql.DataSource ds, InventoryService inv) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); this.inv = inv;
    }

    @Transactional
    public void placeOrder(String orderId, String item) {
        jdbc.update("INSERT INTO orders(id,item) VALUES(?,?)", orderId, item);
        System.out.println("[ORDER] inserted " + orderId);
        inv.deductStock(item);   // REQUIRED — joins this tx; failure rolls back both
    }
}

@Service
class InventoryService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    InventoryService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional(propagation = Propagation.REQUIRED)   // joins outer
    public void deductStock(String item) {
        jdbc.update("INSERT INTO inventory(item,qty) VALUES(?,?)", item, -1);
        System.out.println("[INVENTORY] deducted " + item);
        throw new RuntimeException("Stock system offline");   // rolls back BOTH
    }
}
```

`orders-schema.sql`:
```sql
CREATE TABLE orders    (id VARCHAR(20) PRIMARY KEY, item VARCHAR(50));
CREATE TABLE inventory (id BIGINT AUTO_INCREMENT PRIMARY KEY, item VARCHAR(50), qty INT);
CREATE TABLE audit_log (id BIGINT AUTO_INCREMENT PRIMARY KEY, msg VARCHAR(255));
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. PropagationDemo.java`

`InventoryService.deductStock` joins the outer transaction (REQUIRED). Its `RuntimeException` rolls back both the inventory INSERT and the order INSERT — they share one connection.

---

### Level 2 — Intermediate

**`REQUIRES_NEW`** for audit — audit commits even when the order rolls back.

```java
// PropagationDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class PropagationDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PropagationDemo.class);
        try {
            ctx.getBean(OrderService.class).placeOrder("ORD-2", "ITEM-Y");
        } catch (Exception e) {
            System.out.println("Order rolled back: " + e.getMessage());
            System.out.println("(audit log committed independently)");
        }
        ctx.close();
    }
}

@Service
class OrderService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    private final AuditService audit;
    OrderService(javax.sql.DataSource ds, AuditService audit) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); this.audit = audit;
    }

    @Transactional
    public void placeOrder(String orderId, String item) {
        audit.log("Placing order " + orderId);   // REQUIRES_NEW → commits independently
        jdbc.update("INSERT INTO orders(id,item) VALUES(?,?)", orderId, item);
        System.out.println("[ORDER] inserted " + orderId);
        throw new RuntimeException("Payment gateway timeout");   // rolls back only the order
    }
}

@Service
class AuditService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    AuditService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional(propagation = Propagation.REQUIRES_NEW)   // independent tx
    public void log(String msg) {
        jdbc.update("INSERT INTO audit_log(msg) VALUES(?)", msg);
        System.out.println("[AUDIT tx committed] " + msg);
    }
}
```

How to run: same classpath

`AuditService.log` suspends the outer order transaction, creates its own, inserts the audit row, and commits. The outer transaction resumes. When `placeOrder` throws, only the order INSERT is rolled back — the audit record is already durable.

---

### Level 3 — Advanced

**`NESTED`** — promo application can fail without aborting the order.

```java
// PropagationDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class PropagationDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PropagationDemo.class);
        // promoCode invalid — promo fails but order succeeds
        ctx.getBean(OrderService.class).placeOrderWithPromo("ORD-3","ITEM-Z","INVALID");
        ctx.close();
    }
}

@Service
class OrderService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    private final PromoService promo;
    private final AuditService audit;
    OrderService(javax.sql.DataSource ds, PromoService promo, AuditService audit) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
        this.promo = promo; this.audit = audit;
    }

    @Transactional
    public void placeOrderWithPromo(String orderId, String item, String code) {
        jdbc.update("INSERT INTO orders(id,item) VALUES(?,?)", orderId, item);
        System.out.println("[ORDER] inserted " + orderId);

        try {
            promo.apply(code);    // NESTED — savepoint; rolls back only promo on failure
        } catch (Exception e) {
            System.out.println("[ORDER] promo skipped: " + e.getMessage());
        }
        // Order INSERT still present — promo was rolled back to savepoint only
        audit.log("Order completed (promo " + (code.startsWith("V") ? "applied" : "skipped") + "): " + orderId);
        System.out.println("[ORDER] committed");
    }
}

@Service
class PromoService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    PromoService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional(propagation = Propagation.NESTED)   // savepoint within outer tx
    public void apply(String code) {
        if (!code.startsWith("V")) throw new IllegalArgumentException("Invalid code: " + code);
        jdbc.update("INSERT INTO audit_log(msg) VALUES(?)", "Promo applied: " + code);
        System.out.println("[PROMO] applied " + code);
    }
}

@Service
class AuditService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    AuditService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void log(String msg) {
        jdbc.update("INSERT INTO audit_log(msg) VALUES(?)", msg);
        System.out.println("[AUDIT] " + msg);
    }
}
```

How to run: same classpath

`PromoService.apply` with `NESTED` creates a savepoint. On failure, only the work after the savepoint (nothing, in this case) is undone. The outer order INSERT is not affected. The outer `@Transactional` commits with the order record intact.

## 6. Walkthrough

**Level 2 — `REQUIRES_NEW` suspend/resume (connection perspective):**

```
OrderService.placeOrder("ORD-2","ITEM-Y") begins
  outer tx T1: conn1 acquired, autoCommit=false

  audit.log("Placing order ORD-2")
    → REQUIRES_NEW:
       conn1 stored in ThreadLocal["suspended"]
       conn2 acquired, autoCommit=false       ← inner tx T2
    → INSERT audit_log   [conn2]
    → T2.commit() → conn2.commit(); conn2 released
    → conn1 restored from ThreadLocal["suspended"]   ← outer T1 resumes

  INSERT orders [conn1]
  throw RuntimeException("Payment gateway timeout")
  T1.rollback() → conn1.rollback(); conn1 released

Result:
  audit_log: 1 row (committed independently)
  orders:    0 rows (rolled back)
```

**Level 3 — `NESTED` savepoint lifecycle:**

```
OrderService.placeOrderWithPromo("ORD-3","ITEM-Z","INVALID")
  outer tx T1: conn acquired

  INSERT orders ('ORD-3','ITEM-Z')   [conn, before any savepoint]

  promo.apply("INVALID")
    → NESTED: SAVEPOINT sp1 set on conn
    → throw IllegalArgumentException  (code does not start with 'V')
    → ROLLBACK TO SAVEPOINT sp1   [no new work to undo — savepoint was set right before the throw path]
    → conn still open (T1 still active)

  catch: "[ORDER] promo skipped"
  audit.log("Order completed...")
    → REQUIRES_NEW: new conn2, INSERT audit_log, commit

  T1.commit(): conn.commit()
    → orders row persisted ✓
    → promo row NOT present (rolled back to sp1) ✓
```

## 7. Gotchas & takeaways

> **`REQUIRES_NEW` means two open connections simultaneously.** If your connection pool has `maxPoolSize=5` and 5 threads each hit `REQUIRES_NEW`, you need 10 connections (5 suspended + 5 new) — you'll deadlock. Size your pool accordingly: `maxPoolSize >= 2 × max-concurrent-REQUIRES_NEW-callers`.

> **`NESTED` is JDBC-only.** `JpaTransactionManager` does not support savepoints through Spring's `NESTED` propagation. If you use JPA, catch the exception from the inner method manually and implement partial rollback at the application level.

> **`REQUIRED` propagation and `setRollbackOnly()` interact dangerously.** If the inner method marks the transaction rollback-only (via an exception that's caught and re-swallowed by the outer), the outer `commit()` will throw `UnexpectedRollbackException`. Always let the exception propagate or check `TransactionStatus.isRollbackOnly()` before committing.

- `REQUIRED` (default) — the safe default: both callers share fate.
- `REQUIRES_NEW` — the audit/notification pattern: inner commits even if outer fails. Watch connection pool sizing.
- `NESTED` — the partial-rollback pattern: inner can fail without killing the outer. JDBC only.
- `SUPPORTS` — for helper methods that should work in or out of a transaction (e.g., a formatter that does read-only lookups).
- `MANDATORY` — a programming contract: call this method from within a transaction, or die.
