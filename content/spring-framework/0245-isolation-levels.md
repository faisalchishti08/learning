---
card: spring-framework
gi: 245
slug: isolation-levels
title: Isolation levels
---

## 1. What it is

**Transaction isolation** controls how much a transaction is shielded from the effects of concurrent transactions. SQL defines four isolation levels — each prevents a different class of concurrency anomaly. Spring exposes them through `@Transactional(isolation = Isolation.XXX)` and `TransactionDefinition.ISOLATION_*` constants.

```java
@Transactional(isolation = Isolation.REPEATABLE_READ)
public BigDecimal getAccountBalance(String accountId) { ... }
```

The four levels, from weakest to strongest:

| Level | Dirty Read | Non-Repeatable Read | Phantom Read |
|-------|-----------|--------------------|----|
| `READ_UNCOMMITTED` | ✓ possible | ✓ | ✓ |
| `READ_COMMITTED` | prevented | ✓ | ✓ |
| `REPEATABLE_READ` | prevented | prevented | ✓ |
| `SERIALIZABLE` | prevented | prevented | prevented |

`DEFAULT` uses the database's own default (usually `READ_COMMITTED` for PostgreSQL/Oracle; `REPEATABLE_READ` for MySQL InnoDB).

## 2. Why & when

| Anomaly | What it means | Prevented by |
|---------|--------------|--------------|
| **Dirty read** | T1 reads uncommitted data from T2; T2 rolls back; T1 used phantom data | READ_COMMITTED+ |
| **Non-repeatable read** | T1 reads a row; T2 updates+commits it; T1 re-reads and gets different data | REPEATABLE_READ+ |
| **Phantom read** | T1 queries for rows matching a condition; T2 inserts+commits a matching row; T1 re-queries and gets an extra row | SERIALIZABLE |

- `READ_COMMITTED` is the right default for most OLTP workloads.
- `REPEATABLE_READ` when you read data multiple times in one transaction and need consistency.
- `SERIALIZABLE` only for critical financial or inventory operations where phantom reads would cause correctness issues.
- Higher isolation = more locking = lower throughput. Use the minimum level that meets correctness requirements.

## 3. Core concept

Spring maps `Isolation` enum values to JDBC `Connection.setTransactionIsolation(int)` constants:

| Spring `Isolation` | JDBC constant |
|-------------------|--------------|
| `DEFAULT` | -1 (no `setTransactionIsolation` call — database default) |
| `READ_UNCOMMITTED` | `Connection.TRANSACTION_READ_UNCOMMITTED` (1) |
| `READ_COMMITTED` | `Connection.TRANSACTION_READ_COMMITTED` (2) |
| `REPEATABLE_READ` | `Connection.TRANSACTION_REPEATABLE_READ` (4) |
| `SERIALIZABLE` | `Connection.TRANSACTION_SERIALIZABLE` (8) |

`DataSourceTransactionManager` calls `con.setTransactionIsolation(level)` at the start of each transaction. `JpaTransactionManager` sets it at the JDBC connection level before handing the connection to JPA/Hibernate.

Not all databases support all levels: MySQL InnoDB supports all four; PostgreSQL does not support `READ_UNCOMMITTED` (silently upgrades to `READ_COMMITTED`).

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Spectrum bar -->
  <defs>
    <linearGradient id="spec" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#f85149"/>
      <stop offset="100%" stop-color="#6db33f"/>
    </linearGradient>
  </defs>
  <rect x="40" y="30" width="620" height="22" rx="4" fill="url(#spec)"/>
  <text x="40" y="70" fill="#f85149" font-size="10" font-family="sans-serif">READ_UNCOMMITTED</text>
  <text x="200" y="70" fill="#e6ac3a" font-size="10" font-family="sans-serif">READ_COMMITTED</text>
  <text x="380" y="70" fill="#79c0ff" font-size="10" font-family="sans-serif">REPEATABLE_READ</text>
  <text x="560" y="70" fill="#6db33f" font-size="10" font-family="sans-serif">SERIALIZABLE</text>

  <text x="350" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">← lowest isolation (more concurrency) ——————— highest isolation (more locking) →</text>

  <!-- Table: anomalies -->
  <rect x="40" y="85" width="620" height="130" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>

  <!-- Header -->
  <text x="80"  y="107" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Level</text>
  <text x="255" y="107" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Dirty Read</text>
  <text x="390" y="107" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Non-Repeatable</text>
  <text x="550" y="107" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Phantom</text>
  <line x1="50" y1="112" x2="650" y2="112" stroke="#8b949e" stroke-width="0.5"/>

  <text x="80"  y="130" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">READ_UNCOMMITTED</text>
  <text x="255" y="130" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">possible</text>
  <text x="390" y="130" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">possible</text>
  <text x="550" y="130" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">possible</text>

  <text x="80"  y="149" fill="#e6ac3a" font-size="9" text-anchor="middle" font-family="monospace">READ_COMMITTED</text>
  <text x="255" y="149" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">prevented</text>
  <text x="390" y="149" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">possible</text>
  <text x="550" y="149" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">possible</text>

  <text x="80"  y="168" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">REPEATABLE_READ</text>
  <text x="255" y="168" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">prevented</text>
  <text x="390" y="168" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">prevented</text>
  <text x="550" y="168" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">possible</text>

  <text x="80"  y="187" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">SERIALIZABLE</text>
  <text x="255" y="187" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">prevented</text>
  <text x="390" y="187" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">prevented</text>
  <text x="550" y="187" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">prevented</text>

  <text x="350" y="208" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Spring: Isolation.READ_COMMITTED → con.setTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED)</text>
</svg>

Higher isolation prevents more anomalies at the cost of concurrency.

## 5. Runnable example

Scenario: a **`ReportingService`** reading account balances — demonstrating the non-repeatable read anomaly and how `REPEATABLE_READ` prevents it.

### Level 1 — Basic

`READ_COMMITTED` (default) — two reads in one transaction can get different values.

```java
// IsolationDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import java.util.concurrent.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class IsolationDemo {
    @Bean public javax.sql.DataSource dataSource() {
        // NOTE: H2 in-memory has limited concurrent transaction demo capability;
        // this shows the Spring API — real anomalies need a real DB with concurrent sessions.
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("accounts-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(IsolationDemo.class);
        // Seed data
        var svc = ctx.getBean(ReportingService.class);
        var jdbc = new org.springframework.jdbc.core.JdbcTemplate(ctx.getBean(javax.sql.DataSource.class));
        jdbc.update("INSERT INTO accounts(id,balance) VALUES('ACC-1',1000)");

        // READ_COMMITTED: re-read may return different value
        svc.readTwice("ACC-1");
        ctx.close();
    }
}

@Service
class ReportingService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    ReportingService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional(isolation = Isolation.READ_COMMITTED)
    public void readTwice(String accountId) {
        Double b1 = jdbc.queryForObject("SELECT balance FROM accounts WHERE id=?", Double.class, accountId);
        System.out.println("First read:  $" + b1);
        // In a real concurrent scenario another tx could UPDATE here and commit
        // With READ_COMMITTED the second read would see the new value (non-repeatable read)
        Double b2 = jdbc.queryForObject("SELECT balance FROM accounts WHERE id=?", Double.class, accountId);
        System.out.println("Second read: $" + b2);
        System.out.println("Values match? " + b1.equals(b2) + "  (would differ under concurrent UPDATE)");
    }
}
```

`accounts-schema.sql`: `CREATE TABLE accounts (id VARCHAR(20) PRIMARY KEY, balance DECIMAL(10,2));`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. IsolationDemo.java`

With `READ_COMMITTED`, if a concurrent transaction updates and commits between the two reads, the second read returns the new value. This is the non-repeatable read anomaly. With H2 in-process no concurrency is shown, but the isolation level is correctly applied via `setTransactionIsolation`.

---

### Level 2 — Intermediate

`REPEATABLE_READ` — configuring isolation and verifying the JDBC connection's isolation level is set correctly.

```java
// IsolationDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import java.sql.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class IsolationDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("accounts-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(IsolationDemo.class);
        var jdbc = new org.springframework.jdbc.core.JdbcTemplate(ctx.getBean(javax.sql.DataSource.class));
        jdbc.update("INSERT INTO accounts(id,balance) VALUES('ACC-2',5000)");
        ctx.getBean(ReportingService.class).repeatedRead("ACC-2");
        ctx.close();
    }
}

@Service
class ReportingService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    private final javax.sql.DataSource ds;
    ReportingService(javax.sql.DataSource ds) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); this.ds = ds;
    }

    @Transactional(isolation = Isolation.REPEATABLE_READ)
    public void repeatedRead(String accountId) {
        // Verify isolation level on the active connection
        org.springframework.jdbc.datasource.DataSourceUtils.getConnection(ds);
        // Spring bound the connection — check it
        jdbc.execute((Connection con) -> {
            int lvl = con.getTransactionIsolation();
            System.out.println("JDBC isolation level: " + lvl
                + " (REPEATABLE_READ=" + Connection.TRANSACTION_REPEATABLE_READ + ")");
            return null;
        });

        Double b1 = jdbc.queryForObject("SELECT balance FROM accounts WHERE id=?", Double.class, accountId);
        System.out.println("First  read: $" + b1);
        // Concurrent UPDATE by another connection would be invisible until this tx ends
        Double b2 = jdbc.queryForObject("SELECT balance FROM accounts WHERE id=?", Double.class, accountId);
        System.out.println("Second read: $" + b2);
        System.out.println("Isolation guaranteed same value: " + b1.equals(b2));
    }
}
```

How to run: same classpath

The `JDBC isolation level: 4` output confirms Spring set `TRANSACTION_REPEATABLE_READ` on the underlying connection. Under `REPEATABLE_READ`, a re-read of the same row within one transaction always returns the value that was current at the transaction's start, regardless of concurrent commits.

---

### Level 3 — Advanced

**`SERIALIZABLE`** — range lock example for inventory reservation (phantom read prevention), and demonstrating `ISOLATION_DEFAULT` fall-through.

```java
// IsolationDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class IsolationDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("inventory-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(IsolationDemo.class);
        var jdbc = new org.springframework.jdbc.core.JdbcTemplate(ctx.getBean(javax.sql.DataSource.class));
        jdbc.update("INSERT INTO inventory(sku,qty) VALUES('WIDGET',10)");
        jdbc.update("INSERT INTO inventory(sku,qty) VALUES('GADGET',5)");

        InventoryService svc = ctx.getBean(InventoryService.class);
        svc.reserveSerializable("WIDGET", 3);
        svc.reportDefault();    // uses database default isolation
        ctx.close();
    }
}

@Service
class InventoryService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    InventoryService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    // SERIALIZABLE: prevents phantom reads — another tx cannot INSERT a new WIDGET row
    // while this tx is reading all WIDGET rows
    @Transactional(isolation = Isolation.SERIALIZABLE)
    public void reserveSerializable(String sku, int qty) {
        int available = jdbc.queryForObject(
            "SELECT qty FROM inventory WHERE sku=?", Integer.class, sku);
        System.out.println("[SERIAL] available " + sku + ": " + available);
        if (available >= qty) {
            jdbc.update("UPDATE inventory SET qty=qty-? WHERE sku=?", qty, sku);
            System.out.println("[SERIAL] reserved " + qty + " of " + sku);
        } else {
            System.out.println("[SERIAL] insufficient stock");
        }
    }

    // ISOLATION_DEFAULT — database decides; no Spring override
    @Transactional(isolation = Isolation.DEFAULT)
    public void reportDefault() {
        var rows = jdbc.queryForList("SELECT sku, qty FROM inventory");
        System.out.println("[DEFAULT isolation] inventory:");
        rows.forEach(r -> System.out.println("  " + r.get("sku") + ": " + r.get("qty")));
    }
}
```

`inventory-schema.sql`: `CREATE TABLE inventory (sku VARCHAR(50) PRIMARY KEY, qty INT);`

How to run: same classpath

`SERIALIZABLE` on `reserveSerializable` sets a range lock on the `inventory` table. Under concurrent load, another transaction attempting to insert a new `WIDGET` row while this reads would block (or fail with a serialization error). `Isolation.DEFAULT` makes no `setTransactionIsolation` call — the database uses its configured default (H2 default: `READ_COMMITTED`).

## 6. Walkthrough

**`@Transactional(isolation = Isolation.REPEATABLE_READ)` startup (Level 2):**

1. `@EnableTransactionManagement` registers `AnnotationTransactionAttributeSource`.
2. At context startup, the `BeanPostProcessor` sees `@Transactional(isolation=REPEATABLE_READ)` on `repeatedRead()`.
3. It creates a `RuleBasedTransactionAttribute` with `isolationLevel=4` (REPEATABLE_READ).

**Per-call flow for `repeatedRead("ACC-2")`:**

```
proxy.repeatedRead("ACC-2")
  → TransactionInterceptor
    → DataSourceTransactionManager.doBegin(txObj, definition):
        con = pool.getConnection()
        con.setTransactionIsolation(4)   ← TRANSACTION_REPEATABLE_READ
        con.setAutoCommit(false)
        bind con to ThreadLocal

  → ReportingService.repeatedRead():
      jdbc.execute(con → print isolation)   prints "JDBC isolation level: 4"
      SELECT balance WHERE id='ACC-2'       → $5000.00 on con
      SELECT balance WHERE id='ACC-2'       → $5000.00 on SAME con (same snapshot)

  → commit():
      con.commit()
      con.setAutoCommit(true)
      con.setTransactionIsolation(original_level)   ← RESTORED for pool reuse
      con released to pool
```

Spring restores the original connection isolation level after the transaction completes — essential for connection pool hygiene.

## 7. Gotchas & takeaways

> **Spring resets the isolation level when releasing the connection to the pool.** If you configure the DataSource with `defaultTransactionIsolation=REPEATABLE_READ` and a transaction uses `Isolation.READ_COMMITTED`, Spring sets 2 for that transaction and then restores the DataSource default after commit/rollback. The pool sees the right level on each borrow.

> **Not all databases respect all levels.** PostgreSQL silently upgrades `READ_UNCOMMITTED` to `READ_COMMITTED`. H2 and SQLite have limited isolation enforcement. Always test isolation assumptions against your actual production database.

> **`Isolation.DEFAULT` means "don't touch the connection's isolation level"** — not that it defaults to `READ_COMMITTED`. If your DataSource is configured with `defaultTransactionIsolation=SERIALIZABLE` and you use `Isolation.DEFAULT`, transactions run serializable.

- Use `READ_COMMITTED` for most OLTP — it's the usual database default and balances consistency with concurrency.
- Use `REPEATABLE_READ` for calculations that read the same row multiple times in one transaction (e.g., balance checks before and after debiting).
- Use `SERIALIZABLE` only for the narrowest critical sections (e.g., seat/ticket allocation) — it locks heavily and under contention produces serialization-failure exceptions that require retry logic.
- Never use `READ_UNCOMMITTED` in production — it allows dirty reads that can expose partially written data.
