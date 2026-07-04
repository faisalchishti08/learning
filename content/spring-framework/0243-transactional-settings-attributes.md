---
card: spring-framework
gi: 243
slug: transactional-settings-attributes
title: "@Transactional settings & attributes"
---

## 1. What it is

`@Transactional` has eight attributes that configure exactly how the transaction should behave. They map directly to `TransactionDefinition` fields:

```java
@Transactional(
    transactionManager = "myTm",          // which TM bean to use
    propagation        = Propagation.REQUIRED,
    isolation          = Isolation.DEFAULT,
    timeout            = -1,              // seconds; -1 = database default
    readOnly           = false,
    rollbackFor        = {},              // rollback on these checked exceptions too
    noRollbackFor      = {},              // don't rollback on these unchecked exceptions
    label              = {}              // arbitrary metadata strings (Spring 5.3+)
)
```

Most applications leave all attributes at their defaults and only override `readOnly`, `propagation`, or `rollbackFor` for specific methods.

## 2. Why & when

| Attribute | Override when |
|-----------|--------------|
| `transactionManager` | Multiple TMs in the same context (JDBC + MongoDB) |
| `propagation` | Inner service must commit independently (`REQUIRES_NEW`) or should fail if no outer tx exists (`MANDATORY`) |
| `isolation` | Concurrent access patterns require stricter (or looser) consistency guarantees |
| `timeout` | Long-running operations must not hold locks indefinitely |
| `readOnly` | Query-only methods — enables JPA flush skip, potential read-replica routing |
| `rollbackFor` | Checked exceptions that represent business failures (e.g., `InsufficientFundsException`) |
| `noRollbackFor` | Informational `RuntimeException` subclasses that should not abort the transaction |
| `label` | Custom metadata readable by `TransactionAttributeSource` extensions |

## 3. Core concept

Spring resolves `@Transactional` attributes in this lookup order (most specific wins):

1. Method-level `@Transactional` on the target class.
2. Class-level `@Transactional` on the target class.
3. Method-level `@Transactional` on the implemented interface (Spring 5.0+ respects interface annotations).
4. Class-level `@Transactional` on the interface.

**`rollbackFor` / `noRollbackFor`** override the default rollback rule (rollback on `RuntimeException` and `Error`; commit on checked exceptions). You can specify exception classes or their names.

```java
@Transactional(rollbackFor = {IOException.class, BusinessException.class})
public void process() throws IOException { ... }
```

**`timeout`** is checked at the `PlatformTransactionManager` level — it does NOT cancel a running SQL query automatically. Use JDBC statement timeout (`JdbcTemplate.setQueryTimeout()`) to actually abort SQL.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- @Transactional -->
  <rect x="10" y="15" width="310" height="190" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="165" y="38" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">@Transactional attributes</text>
  <line x1="20" y1="46" x2="310" y2="46" stroke="#8b949e" stroke-width="0.5"/>

  <text x="165" y="66" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">transactionManager = "myTm"</text>
  <text x="165" y="83" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">propagation = REQUIRED</text>
  <text x="165" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">isolation = DEFAULT</text>
  <text x="165" y="117" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">timeout = -1</text>
  <text x="165" y="134" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">readOnly = false</text>
  <text x="165" y="151" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">rollbackFor = {}</text>
  <text x="165" y="168" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">noRollbackFor = {}</text>
  <text x="165" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">label = {}</text>

  <!-- Arrow -->
  <line x1="322" y1="110" x2="380" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="351" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">compiled to</text>

  <!-- TransactionAttribute -->
  <rect x="380" y="65" width="305" height="90" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="533" y="88" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">RuleBasedTransactionAttribute</text>
  <text x="533" y="106" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">extends DefaultTransactionAttribute</text>
  <text x="533" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">extends DefaultTransactionDefinition</text>
  <text x="533" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ rollbackRules list (RollbackRuleAttribute)</text>
</svg>

Each `@Transactional` annotation is parsed into a `RuleBasedTransactionAttribute` at context startup.

## 5. Runnable example

Scenario: a **`LoanService`** — first showing default attributes, then per-method attribute overrides, then `rollbackFor` for a custom checked exception.

### Level 1 — Basic

Default `@Transactional` — rollbacks only on `RuntimeException`, read-write, `REQUIRED`.

```java
// TxSettingsDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxSettingsDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("loans-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxSettingsDemo.class);
        LoanService svc = ctx.getBean(LoanService.class);
        svc.applyForLoan("CUST-1", 50_000.0);

        // Checked exception — default: does NOT rollback
        try { svc.reviewLoan("CUST-1"); } catch (Exception e) {
            System.out.println("Caught: " + e.getMessage() + " — but was the TX committed?");
        }
        ctx.close();
    }
}

@Service
class LoanService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    LoanService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional    // all defaults
    public void applyForLoan(String customerId, double amount) {
        jdbc.update("INSERT INTO loans(customer_id,amount,status) VALUES(?,?,'PENDING')", customerId, amount);
        System.out.println("Loan application stored: " + customerId);
    }

    @Transactional    // checked exception → tx COMMITS by default
    public void reviewLoan(String customerId) throws Exception {
        jdbc.update("UPDATE loans SET status='REVIEWED' WHERE customer_id=?", customerId);
        throw new Exception("Review system offline");   // checked — tx commits anyway
    }
}
```

`loans-schema.sql`:
```sql
CREATE TABLE loans (id BIGINT AUTO_INCREMENT PRIMARY KEY,
  customer_id VARCHAR(50), amount DECIMAL(12,2), status VARCHAR(20));
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. TxSettingsDemo.java`

`reviewLoan` throws a checked `Exception`. Default `@Transactional` does NOT rollback on checked exceptions — the `UPDATE` is committed even though the exception propagates. This is a common surprise.

---

### Level 2 — Intermediate

Per-method attribute overrides: `readOnly` on a query, `timeout` on a slow operation, `REQUIRES_NEW` on audit logging.

```java
// TxSettingsDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxSettingsDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("loans-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxSettingsDemo.class);
        LoanService svc = ctx.getBean(LoanService.class);
        svc.applyForLoan("CUST-2", 75_000.0);
        List<String> loans = svc.getAllLoans();
        System.out.println("Loans: " + loans);
        ctx.close();
    }
}

@Service
class LoanService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    private final AuditLogger audit;
    LoanService(javax.sql.DataSource ds, AuditLogger audit) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); this.audit = audit;
    }

    @Transactional(timeout = 10)    // abort if loan creation takes > 10 seconds
    public void applyForLoan(String customerId, double amount) {
        jdbc.update("INSERT INTO loans(customer_id,amount,status) VALUES(?,?,'PENDING')", customerId, amount);
        audit.record("Loan applied: " + customerId);   // REQUIRES_NEW — commits independently
        System.out.println("Loan stored and audit committed: " + customerId);
    }

    @Transactional(readOnly = true, timeout = 5)   // read-only; fast query budget
    public List<String> getAllLoans() {
        return jdbc.queryForList(
            "SELECT customer_id||' $'||amount||' ('||status||')' FROM loans", String.class);
    }
}

@Service
class AuditLogger {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    AuditLogger(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional(propagation = Propagation.REQUIRES_NEW)   // always its own tx
    public void record(String msg) {
        jdbc.update("INSERT INTO loans(customer_id,amount,status) VALUES(?,0,'AUDIT')", msg);
        System.out.println("[AUDIT new tx] " + msg);
    }
}
```

How to run: same classpath

`applyForLoan` has a 10-second timeout. `getAllLoans` is read-only with a 5-second timeout. `AuditLogger.record` uses `REQUIRES_NEW` — its transaction commits even if `applyForLoan` rolls back.

---

### Level 3 — Advanced

**`rollbackFor` and `noRollbackFor`** — fine-grained rollback control with custom exception hierarchy.

```java
// TxSettingsDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxSettingsDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("loans-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxSettingsDemo.class);
        LoanService svc = ctx.getBean(LoanService.class);

        // rollbackFor: checked InsufficientFundsException triggers rollback
        try { svc.disburse("CUST-3", 100_000.0); } catch (InsufficientFundsException e) {
            System.out.println("Disbursement rolled back: " + e.getMessage());
        }

        // noRollbackFor: OptimisticLockWarning (RuntimeException) does NOT rollback
        try { svc.approveLoan("CUST-3"); } catch (OptimisticLockWarning w) {
            System.out.println("Warning (tx committed): " + w.getMessage());
        }
        ctx.close();
    }
}

class InsufficientFundsException extends Exception {
    InsufficientFundsException(String msg) { super(msg); }
}

class OptimisticLockWarning extends RuntimeException {
    OptimisticLockWarning(String msg) { super(msg); }
}

@Service
class LoanService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    LoanService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional(rollbackFor = InsufficientFundsException.class)
    public void disburse(String customerId, double amount) throws InsufficientFundsException {
        jdbc.update("INSERT INTO loans(customer_id,amount,status) VALUES(?,?,'DISBURSING')", customerId, amount);
        double availableFunds = 50_000.0;   // simulated limit
        if (amount > availableFunds)
            throw new InsufficientFundsException("Requested $" + amount + ", available $" + availableFunds);
        jdbc.update("UPDATE loans SET status='DISBURSED' WHERE customer_id=?", customerId);
    }

    @Transactional(noRollbackFor = OptimisticLockWarning.class)
    public void approveLoan(String customerId) {
        jdbc.update("INSERT INTO loans(customer_id,amount,status) VALUES(?,0,'APPROVED')", customerId);
        System.out.println("Loan approved for " + customerId);
        throw new OptimisticLockWarning("Stale data detected — retrying later");
        // tx COMMITS despite this RuntimeException (noRollbackFor)
    }
}
```

How to run: same classpath

`rollbackFor = InsufficientFundsException.class` makes the checked exception trigger rollback — the INSERT into `loans` is undone. `noRollbackFor = OptimisticLockWarning.class` prevents rollback for this `RuntimeException` — the `INSERT` is committed, then the warning propagates.

## 6. Walkthrough

**Level 3 — `disburse` rollback path:**

```
proxy.disburse("CUST-3", 100_000.0)
  → TransactionInterceptor resolves @Transactional attrs:
      rollbackFor=[InsufficientFundsException]
  → getTransaction() → conn acquired, autoCommit=false

  → disburse() body:
      INSERT loans ('CUST-3', 100000, 'DISBURSING')   on conn
      availableFunds=50_000 < 100_000 → throw InsufficientFundsException

  → TransactionInterceptor catches exception
    → checks rollback rules:
        InsufficientFundsException matches rollbackFor → ROLLBACK
    → tm.rollback(status) → conn.rollback()
    → conn released, ThreadLocal cleared

  → InsufficientFundsException re-thrown to caller
```

**Level 3 — `approveLoan` commit despite exception:**

```
proxy.approveLoan("CUST-3")
  → getTransaction() → conn acquired, autoCommit=false

  → approveLoan() body:
      INSERT loans ('CUST-3', 0, 'APPROVED')   on conn
      throw OptimisticLockWarning("Stale data…")

  → TransactionInterceptor catches RuntimeException
    → checks rollback rules:
        OptimisticLockWarning matches noRollbackFor → DO NOT rollback → COMMIT
    → tm.commit(status) → conn.commit()   [INSERT is persisted]
    → conn released

  → OptimisticLockWarning re-thrown to caller
```

**Rule evaluation priority:** `noRollbackFor` is checked first against the exact exception class and its superclasses; then `rollbackFor`. The most specific match wins. If there is a conflict, the most specific rule wins.

## 7. Gotchas & takeaways

> **Checked exceptions commit by default.** This is the single most common `@Transactional` mistake. If your method throws `IOException`, `SQLException`, `BusinessException extends Exception`, etc., the transaction commits unless you add `rollbackFor`.

> **`timeout` does not cancel SQL.** It marks the transaction rollback-only after the specified seconds, but any in-flight SQL continues until the JDBC/database timeout kicks in. Set `JdbcTemplate.queryTimeout` or a JDBC URL parameter to actually abort queries.

> **`noRollbackFor` on `RuntimeException` subclasses is rare but valid.** Use it when a `RuntimeException` is informational (e.g., a warning you want to log) and you do NOT want it to undo the work done so far.

- Default rollback behaviour: rollback on `RuntimeException` and `Error`; commit on `Exception` and its checked subclasses.
- `rollbackFor` is additive — it extends the default rule, not replaces it. You still rollback on `RuntimeException` even if you specify `rollbackFor = IOException.class`.
- `noRollbackFor` can override the default `RuntimeException` rollback for specific subclasses.
- `label` (Spring 5.3+) stores arbitrary strings readable by custom `TransactionAttributeSource` implementations — useful for multi-tenant routing or monitoring annotation metadata.
