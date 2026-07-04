---
card: spring-framework
gi: 239
slug: transactiondefinition-propagation-isolation-timeout-read-onl
title: TransactionDefinition (propagation, isolation, timeout, read-only)
---

## 1. What it is

`TransactionDefinition` is the configuration interface passed to `PlatformTransactionManager.getTransaction()`. It carries four key attributes that control exactly how the transaction should behave:

1. **Propagation** — what to do when a method is called inside an existing transaction.
2. **Isolation** — how much to shield this transaction from concurrent transactions.
3. **Timeout** — maximum seconds before the transaction is automatically rolled back.
4. **Read-only** — hint to the resource manager that no writes will occur.

```java
DefaultTransactionDefinition def = new DefaultTransactionDefinition();
def.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRED);
def.setIsolationLevel(TransactionDefinition.ISOLATION_READ_COMMITTED);
def.setTimeout(30);
def.setReadOnly(true);
```

When using `@Transactional`, these attributes are set via annotation attributes — the annotation is compiled into a `TransactionAttribute` (which extends `TransactionDefinition`).

## 2. Why & when

These four attributes exist because different operations have different transaction needs:

- A **reporting query** should be read-only and can use a less strict isolation level for performance.
- An **inventory deduction** may need `SERIALIZABLE` isolation to prevent phantom reads.
- An **audit-trail write** may need `REQUIRES_NEW` so it commits even if the outer transaction rolls back.
- A **batch import** needs a long timeout; a **payment** needs a short one.

## 3. Core concept

**Propagation constants** (on `TransactionDefinition`):

| Constant | Meaning |
|----------|---------|
| `PROPAGATION_REQUIRED` | Use existing tx; create new if none *(default)* |
| `PROPAGATION_REQUIRES_NEW` | Always create a new tx; suspend the outer one |
| `PROPAGATION_SUPPORTS` | Use existing tx if present; otherwise run without |
| `PROPAGATION_NOT_SUPPORTED` | Always run without a tx; suspend outer if present |
| `PROPAGATION_MANDATORY` | Must be called within a tx; throw if none |
| `PROPAGATION_NEVER` | Must NOT be in a tx; throw if one exists |
| `PROPAGATION_NESTED` | Run within a savepoint of the outer tx (JDBC only) |

**Isolation constants**:

| Constant | Prevents dirty read | Prevents non-repeatable read | Prevents phantom read |
|----------|--------------------|-----------------------------|----------------------|
| `ISOLATION_READ_UNCOMMITTED` | ✗ | ✗ | ✗ |
| `ISOLATION_READ_COMMITTED` | ✓ | ✗ | ✗ |
| `ISOLATION_REPEATABLE_READ` | ✓ | ✓ | ✗ |
| `ISOLATION_SERIALIZABLE` | ✓ | ✓ | ✓ |
| `ISOLATION_DEFAULT` | Database default (usually READ_COMMITTED) |

**Timeout**: seconds before the TM forces a rollback. `-1` (TIMEOUT_DEFAULT) means the database's default.

**Read-only**: when `true`, the TM and/or resource can skip locking and buffering for writes — can improve query performance significantly on high-read workloads.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- TransactionDefinition box -->
  <rect x="10" y="20" width="330" height="170" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="175" y="44" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">TransactionDefinition</text>
  <line x1="20" y1="52" x2="330" y2="52" stroke="#8b949e" stroke-width="0.5"/>

  <rect x="25" y="62" width="140" height="30" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="95" y="80" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Propagation</text>

  <rect x="175" y="62" width="150" height="30" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="250" y="80" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Isolation Level</text>

  <rect x="25" y="104" width="140" height="30" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="95" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Timeout (secs)</text>

  <rect x="175" y="104" width="150" height="30" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="250" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Read-Only flag</text>

  <text x="175" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Transactional(propagation=REQUIRED,</text>
  <text x="175" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">isolation=READ_COMMITTED, timeout=30, readOnly=false)</text>

  <!-- Arrow to TM -->
  <line x1="342" y1="105" x2="400" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="371" y="97" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">passed to</text>

  <!-- PlatformTM -->
  <rect x="400" y="72" width="285" height="65" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="543" y="96" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">PlatformTransactionManager</text>
  <text x="543" y="114" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">getTransaction(definition)</text>
  <text x="543" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ applies propagation / isolation / timeout</text>
</svg>

`TransactionDefinition` is the spec; the TM interprets it when opening a transaction.

## 5. Runnable example

Scenario: an **`OrderService`** managing orders and an `AuditService` — demonstrating propagation differences, isolation impact, and read-only optimization.

### Level 1 — Basic

`PROPAGATION_REQUIRED` (default) — inner call joins the outer transaction.

```java
// TxDefinitionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxDefinitionDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxDefinitionDemo.class);
        ctx.getBean(OrderService.class).placeOrder("ITEM-A", 10);
        ctx.close();
    }
}

@Service
class OrderService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    private final AuditService audit;
    OrderService(javax.sql.DataSource ds, AuditService audit) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
        this.audit = audit;
    }

    @Transactional(propagation = Propagation.REQUIRED)  // default
    public void placeOrder(String item, int qty) {
        jdbc.update("INSERT INTO orders(item,qty) VALUES(?,?)", item, qty);
        audit.log("Order placed: " + item + " x" + qty);
        System.out.println("Order complete");
    }
}

@Service
class AuditService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    AuditService(javax.sql.DataSource ds) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
    }

    @Transactional(propagation = Propagation.REQUIRED)   // joins existing tx
    public void log(String msg) {
        jdbc.update("INSERT INTO audit_log(msg) VALUES(?)", msg);
        System.out.println("[AUDIT joined outer tx] " + msg);
    }
}
```

`orders-schema.sql`:
```sql
CREATE TABLE orders    (id BIGINT AUTO_INCREMENT PRIMARY KEY, item VARCHAR(100), qty INT);
CREATE TABLE audit_log (id BIGINT AUTO_INCREMENT PRIMARY KEY, msg VARCHAR(255));
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. TxDefinitionDemo.java`

`OrderService.placeOrder` opens a transaction. `AuditService.log` is called inside it — `REQUIRED` means it **joins** the existing transaction. Both inserts are in the same DB transaction. If either fails, both roll back.

---

### Level 2 — Intermediate

`PROPAGATION_REQUIRES_NEW` for the audit — audit commits independently even if the order rolls back. Plus `readOnly=true` on a report query.

```java
// TxDefinitionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxDefinitionDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxDefinitionDemo.class);
        OrderService svc = ctx.getBean(OrderService.class);

        // Attempt that fails — audit still commits
        try { svc.placeOrderFailing("ITEM-B", -1); } catch (Exception e) {
            System.out.println("Order rolled back: " + e.getMessage());
        }

        // Read-only report
        List<String> items = svc.listOrders();
        System.out.println("Orders (read-only tx): " + items);
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
    public void placeOrderFailing(String item, int qty) {
        audit.log("Attempting order: " + item + " x" + qty);   // commits independently
        if (qty < 0) throw new IllegalArgumentException("Invalid qty: " + qty);
        jdbc.update("INSERT INTO orders(item,qty) VALUES(?,?)", item, qty);
    }

    @Transactional(readOnly = true, timeout = 5)   // read-only hint + 5s timeout
    public List<String> listOrders() {
        return jdbc.queryForList("SELECT item FROM orders", String.class);
    }
}

@Service
class AuditService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    AuditService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional(propagation = Propagation.REQUIRES_NEW)   // always its own tx
    public void log(String msg) {
        jdbc.update("INSERT INTO audit_log(msg) VALUES(?)", msg);
        System.out.println("[AUDIT new tx] " + msg);
    }
}
```

How to run: same classpath

`audit.log()` starts its own transaction (`REQUIRES_NEW`), suspending the outer one. It commits immediately. When `placeOrderFailing` throws, the outer transaction rolls back — the order INSERT never happens — but the audit record is already committed. `listOrders()` uses `readOnly=true`: the datasource can skip write-lock acquisition and Hibernate (if used) flushes no dirty state.

---

### Level 3 — Advanced

`ISOLATION_REPEATABLE_READ` to prevent non-repeatable reads in a pricing engine, and `PROPAGATION_NESTED` (savepoint) to partially roll back.

```java
// TxDefinitionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.support.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxDefinitionDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxDefinitionDemo.class);
        ctx.getBean(OrderService.class).placeOrderWithPromo("ITEM-C", 5, "INVALID-CODE");
        ctx.close();
    }
}

@Service
class OrderService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    private final PromoService promo;

    OrderService(javax.sql.DataSource ds, PromoService promo) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); this.promo = promo;
    }

    @Transactional(isolation = Isolation.REPEATABLE_READ)
    public void placeOrderWithPromo(String item, int qty, String promoCode) {
        jdbc.update("INSERT INTO orders(item,qty) VALUES(?,?)", item, qty);
        System.out.println("[ORDER] inserted " + item);

        try {
            promo.applyPromo(promoCode);   // NESTED — partial rollback on failure
        } catch (Exception e) {
            System.out.println("[ORDER] promo failed: " + e.getMessage() + " — order still proceeds");
        }
        // Order commits even though promo rolled back to savepoint
        System.out.println("[ORDER] placed successfully (promo skipped)");
    }
}

@Service
class PromoService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    PromoService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional(propagation = Propagation.NESTED)   // savepoint within outer tx
    public void applyPromo(String code) {
        if (!code.startsWith("VALID")) throw new IllegalArgumentException("Invalid promo: " + code);
        jdbc.update("INSERT INTO audit_log(msg) VALUES(?)", "Promo applied: " + code);
    }
}
```

How to run: same classpath

`PROPAGATION_NESTED` creates a savepoint before `applyPromo`. When `applyPromo` throws, Spring rolls back to the savepoint — only the promo INSERT is undone. The outer transaction (the order INSERT) is unaffected. `REPEATABLE_READ` isolation ensures that if `OrderService` re-reads the order mid-transaction, it sees the same data (a concurrent UPDATE by another tx won't be visible).

## 6. Walkthrough

**Level 2 — `REQUIRES_NEW` suspend/resume:**

```
OrderService.placeOrderFailing() begins
  outer tx T1 opens (DataSource conn1 bound to thread)

  audit.log("Attempting order…")
    → REQUIRES_NEW: conn1 SUSPENDED, new conn2 acquired
    → inner tx T2 opens
    → INSERT audit_log (conn2)
    → T2 commits  [audit_log row persisted]
    → conn2 released; conn1 RESUMED, rebound to thread

  qty < 0 → throw IllegalArgumentException
  outer tx T1 rolls back  [orders row NOT inserted]
  conn1 released
```

**Level 3 — NESTED savepoint:**

```
OrderService.placeOrderWithPromo() begins (REPEATABLE_READ)
  tx T1 opens, conn acquired

  INSERT orders (conn)
  System.out.println "[ORDER] inserted ITEM-C"

  PromoService.applyPromo("INVALID-CODE")
    → NESTED: SAVEPOINT SP1 created on conn
    → throw IllegalArgumentException
    → ROLLBACK TO SAVEPOINT SP1  [only undo anything after SP1]

  catch: "[ORDER] promo failed: Invalid promo…"
  T1 continues; orders row still present (pre-SP1 state preserved)
  T1 commits → orders row persisted
```

## 7. Gotchas & takeaways

> **`readOnly=true` is a hint, not an enforcement.** Spring tells the underlying resource (JDBC driver, JPA provider) about the read-only flag, but it does not prevent writes at the application level. Hibernate skips dirty checking and flush on read-only transactions; some JDBC drivers skip lock acquisition. The actual behaviour depends on the resource.

> **`ISOLATION_SERIALIZABLE` kills concurrency.** It locks read ranges to prevent phantom reads, but causes many transactions to fail with lock-timeout or serialization errors under concurrent load. Use it only for the narrowest possible scope.

> **`PROPAGATION_NESTED` is JDBC-only.** JTA and JPA transaction managers do not support savepoints in this way. Using `NESTED` with `JtaTransactionManager` throws `NestedTransactionNotSupportedException`.

- Default `@Transactional` is `REQUIRED` + `READ_COMMITTED` + no timeout + read-write. Only override when you have a specific reason.
- Use `REQUIRES_NEW` when an inner operation (audit, notification) must commit regardless of outer tx outcome.
- Use `readOnly=true` + a secondary datasource (read replica) to offload reporting queries.
- `timeout` on `@Transactional` does not kill a running JDBC query; it marks the tx rollback-only. You need a JDBC timeout (statement/query timeout) to actually abort running SQL.
