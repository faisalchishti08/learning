---
card: spring-framework
gi: 252
slug: application-managed-vs-container-managed-transactions
title: Application-managed vs container-managed transactions
---

## 1. What it is

**Container-managed transactions (CMT)** — the container (a Java EE application server or Spring) manages transaction lifecycle automatically. `@Transactional` is Spring's CMT mechanism: the proxy begins and commits/rolls back without any explicit transaction code in the business class.

**Application-managed transactions (AMT)** — the application explicitly controls transaction lifecycle by calling `PlatformTransactionManager.getTransaction()` / `commit()` / `rollback()`, or by directly using `EntityManager.getTransaction()` (JPA), or `Connection.commit()` (JDBC).

```java
// CMT — Spring handles everything
@Transactional
public void save(Order o) { repo.save(o); }

// AMT — application handles everything
public void save(Order o) {
    TransactionStatus tx = tm.getTransaction(new DefaultTransactionDefinition());
    try { repo.save(o); tm.commit(tx); }
    catch (Exception e) { tm.rollback(tx); throw e; }
}
```

## 2. Why & when

| | CMT (@Transactional) | AMT (programmatic) |
|--|---------------------|-------------------|
| Code volume | Minimal — annotation only | More boilerplate |
| Transaction boundaries | Fixed at method boundary | Flexible — anywhere in code |
| Mid-method control | Not possible without self-inject | Direct — `setRollbackOnly()`, conditional commit |
| Testability | Needs Spring context or mock | Pure unit test possible |
| Multiple TX per method | Not directly | Yes — explicit loop |
| Library code | Requires Spring on caller's classpath | Works standalone |

Use CMT (default): normal Spring service classes.
Use AMT: batch processing (tx-per-item loop), library code, tests, or complex conditional commit logic.

## 3. Core concept

Both approaches ultimately call the same `PlatformTransactionManager` API. CMT is a **compile-time-invisible** wrapper: Spring generates a proxy that calls `getTransaction()`/`commit()`/`rollback()` around your method. AMT calls the same methods explicitly.

In a Jakarta EE application server:
- **CMT** uses `@jakarta.transaction.Transactional` or `@Stateless`/`@Stateful` EJB container — the container intercepts calls and manages `UserTransaction`.
- **AMT** uses `@Resource UserTransaction ut; ut.begin(); ... ut.commit();`

Spring's `JtaTransactionManager` integrates with a Jakarta EE container's `UserTransaction`, so Spring's `@Transactional` acts as CMT even in a full Java EE environment.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- CMT -->
  <rect x="10" y="20" width="320" height="175" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="170" y="43" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">CMT — Container-Managed</text>
  <line x1="20" y1="52" x2="320" y2="52" stroke="#8b949e" stroke-width="0.5"/>
  <text x="170" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Transactional</text>
  <text x="170" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">public void save(Order o) {</text>
  <text x="170" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">    repo.save(o);</text>
  <text x="170" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">}</text>
  <text x="170" y="152" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">proxy handles: begin / commit / rollback</text>
  <text x="170" y="168" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">method boundary = transaction boundary</text>
  <text x="170" y="183" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">minimal code, fixed scope</text>

  <!-- AMT -->
  <rect x="365" y="20" width="325" height="175" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="527" y="43" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">AMT — Application-Managed</text>
  <line x1="375" y1="52" x2="680" y2="52" stroke="#8b949e" stroke-width="0.5"/>
  <text x="527" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">TransactionStatus tx = tm.getTransaction();</text>
  <text x="527" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">try {</text>
  <text x="527" y="107" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">    repo.save(o); tm.commit(tx);</text>
  <text x="527" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">} catch (Exception e) {</text>
  <text x="527" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">    tm.rollback(tx); throw e;</text>
  <text x="527" y="156" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">}</text>
  <text x="527" y="180" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">flexible scope, explicit control</text>
</svg>

CMT delegates tx management to the proxy; AMT keeps control in the application code.

## 5. Runnable example

Scenario: a **`BatchProcessor`** importing records — first CMT (one transaction for the whole batch), then AMT (one transaction per record), then hybrid (CMT method delegates AMT sub-transactions).

### Level 1 — Basic

**CMT**: one `@Transactional` wrapping the entire batch — all records or none.

```java
// CmtAmtDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class CmtAmtDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("records-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CmtAmtDemo.class);
        // CMT: one tx — if one fails, ALL roll back
        try {
            ctx.getBean(BatchProcessor.class).importAllCmt(List.of("A","B","FAIL","C"));
        } catch (Exception e) {
            System.out.println("CMT: entire batch rolled back: " + e.getMessage());
        }
        var jdbc = new org.springframework.jdbc.core.JdbcTemplate(
            ctx.getBean(javax.sql.DataSource.class));
        System.out.println("Saved (CMT): " + jdbc.queryForList("SELECT name FROM records", String.class));
        ctx.close();
    }
}

@Service
class BatchProcessor {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    BatchProcessor(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional    // CMT: one tx for the whole batch
    public void importAllCmt(List<String> items) {
        for (String item : items) {
            if ("FAIL".equals(item)) throw new RuntimeException("Bad record: " + item);
            jdbc.update("INSERT INTO records(name) VALUES(?)", item);
            System.out.println("[CMT] inserted: " + item);
        }
    }
}
```

`records-schema.sql`: `CREATE TABLE records (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50));`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. CmtAmtDemo.java`

All four inserts (A, B, FAIL, C) are in one transaction. "FAIL" triggers rollback — zero records committed. Appropriate for small batches where partial failure is unacceptable.

---

### Level 2 — Intermediate

**AMT**: one transaction per record — successful records commit even when one fails.

```java
// CmtAmtDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.support.*;
import org.springframework.stereotype.*;
import java.util.*;

@Configuration
@ComponentScan
public class CmtAmtDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("records-schema.sql").build();
    }
    @Bean public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CmtAmtDemo.class);
        ctx.getBean(BatchProcessor.class).importEachAmt(List.of("D","E","FAIL","F"));
        var jdbc = new org.springframework.jdbc.core.JdbcTemplate(
            ctx.getBean(javax.sql.DataSource.class));
        System.out.println("Saved (AMT per-record): " + jdbc.queryForList("SELECT name FROM records", String.class));
        ctx.close();
    }
}

@org.springframework.stereotype.Service
class BatchProcessor {
    private final PlatformTransactionManager tm;
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    BatchProcessor(PlatformTransactionManager tm, javax.sql.DataSource ds) {
        this.tm = tm; this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
    }

    // AMT: no @Transactional — we control each tx explicitly
    public void importEachAmt(List<String> items) {
        TransactionTemplate tmpl = new TransactionTemplate(tm);
        tmpl.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRES_NEW);

        for (String item : items) {
            tmpl.execute(status -> {
                try {
                    if ("FAIL".equals(item)) throw new RuntimeException("Bad: " + item);
                    jdbc.update("INSERT INTO records(name) VALUES(?)", item);
                    System.out.println("[AMT] committed: " + item);
                } catch (RuntimeException e) {
                    System.out.println("[AMT] rolled back: " + item + " (" + e.getMessage() + ")");
                    status.setRollbackOnly();
                }
                return null;
            });
        }
    }
}
```

How to run: same classpath

Each item gets its own transaction. D, E, F commit. "FAIL" rolls back but does not affect the others. Final query shows D, E, F. AMT is the right pattern for large batch jobs where you need per-item fault tolerance.

---

### Level 3 — Advanced

**Hybrid**: a CMT service method delegates to an AMT helper for per-item sub-transactions, then validates the whole batch result in the outer CMT transaction.

```java
// CmtAmtDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.support.*;
import org.springframework.stereotype.*;
import java.util.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class CmtAmtDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("records-schema.sql").build();
    }
    @Bean public PlatformTransactionManager transactionManager(javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CmtAmtDemo.class);
        ctx.getBean(BatchService.class).processBatch(List.of("G","H","FAIL","I"));
        var jdbc = new org.springframework.jdbc.core.JdbcTemplate(
            ctx.getBean(javax.sql.DataSource.class));
        System.out.println("Final records: " + jdbc.queryForList("SELECT name FROM records", String.class));
        ctx.close();
    }
}

@Service
class BatchService {
    private final PlatformTransactionManager tm;
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;

    BatchService(PlatformTransactionManager tm, javax.sql.DataSource ds) {
        this.tm = tm; this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
    }

    @Transactional   // CMT: outer tx for audit/summary
    public void processBatch(List<String> items) {
        int success = 0;
        TransactionTemplate sub = new TransactionTemplate(tm);
        sub.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRES_NEW);

        for (String item : items) {
            Boolean ok = sub.execute(status -> {    // AMT inner tx: REQUIRES_NEW suspends outer
                try {
                    if ("FAIL".equals(item)) throw new RuntimeException("Bad: " + item);
                    jdbc.update("INSERT INTO records(name) VALUES(?)", item);
                    System.out.println("[INNER TX] committed: " + item);
                    return true;
                } catch (RuntimeException e) {
                    System.out.println("[INNER TX] rolled back: " + item);
                    status.setRollbackOnly();
                    return false;
                }
            });
            if (Boolean.TRUE.equals(ok)) success++;
        }

        // Outer CMT tx: write summary (committed with outer)
        jdbc.update("INSERT INTO records(name) VALUES(?)", "SUMMARY: " + success + "/" + items.size() + " ok");
        System.out.println("[CMT OUTER] summary written: " + success + " succeeded");
    }
}
```

How to run: same classpath

Per-item REQUIRES_NEW sub-transactions commit/rollback independently. The outer CMT transaction is suspended for each sub-transaction. After all items, the outer transaction writes a summary row and commits. Final state: G, H, I, and the SUMMARY row.

## 6. Walkthrough

**Level 2 — AMT per-record loop (state trace):**

```
importEachAmt(["D","E","FAIL","F"])
  item="D":
    tmpl.execute()
      → REQUIRES_NEW: conn1 acquired, autoCommit=false
      → INSERT records 'D'
      → commit: conn1.commit(); conn1 released
    System.out "[AMT] committed: D"

  item="E": same as D → committed

  item="FAIL":
    tmpl.execute()
      → REQUIRES_NEW: conn3 acquired, autoCommit=false
      → throw RuntimeException("Bad: FAIL")
      → catch: setRollbackOnly()
      → callback returns null
      → isRollbackOnly=true → rollback: conn3.rollback(); conn3 released
    System.out "[AMT] rolled back: FAIL"

  item="F": same as D → committed
```

**Level 3 — hybrid (outer CMT + inner AMT):**

```
BatchService.processBatch() → CMT T1 (ordersTM conn_outer, autoCommit=false)

  item="G":
    sub.execute() → REQUIRES_NEW: conn_outer SUSPENDED; conn_g acquired
    INSERT records 'G' [conn_g] → commit [conn_g] → conn_outer RESUMED

  item="FAIL":
    sub.execute() → REQUIRES_NEW: conn_outer SUSPENDED; conn_f acquired
    throw RuntimeException → setRollbackOnly → rollback [conn_f] → conn_outer RESUMED

  item="I": committed in its own conn

  INSERT records 'SUMMARY: 3/4 ok' [conn_outer]   ← part of outer CMT tx

T1 commits: conn_outer.commit()
  → summary row persisted

Final: G, H, I, SUMMARY
```

## 7. Gotchas & takeaways

> **AMT inner `REQUIRES_NEW` needs two connections simultaneously.** The outer CMT transaction holds `conn_outer`; the inner AMT suspends it and borrows `conn_inner`. With a pool of size N, up to N/2 concurrent threads can do this pattern before deadlocking. Size pools at 2× the expected concurrent AMT-within-CMT callers.

> **CMT and AMT can coexist in the same method** (as shown in Level 3). Spring's `REQUIRES_NEW` propagation in the inner `TransactionTemplate` correctly suspends and resumes the outer CMT transaction.

> **Direct `EntityManager.getTransaction()` in a Spring-managed context will break things.** Spring's JPA integration uses its own `JpaTransactionManager`; calling `em.getTransaction()` bypasses Spring and creates an application-managed JPA transaction that is not coordinated with Spring's.

- CMT (`@Transactional`): clean, declarative, method-boundary scoped — the default.
- AMT (`TransactionTemplate` / `PlatformTransactionManager` directly): flexible, explicit — for batch loops, library code, conditional commits.
- Hybrid: CMT outer (summary/audit) + AMT inner per-item (fault-tolerant batch).
- Never mix Spring-managed JPA with `em.getTransaction()` — always go through `JpaTransactionManager`.
