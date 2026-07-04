---
card: spring-framework
gi: 246
slug: rollback-rules-rollbackfor-norollbackfor
title: Rollback rules (rollbackFor / noRollbackFor)
---

## 1. What it is

Spring's default rollback rule is: **rollback on `RuntimeException` and `Error`; commit on checked `Exception`**. The `rollbackFor` and `noRollbackFor` attributes on `@Transactional` let you override this for specific exception types:

```java
@Transactional(
    rollbackFor   = {IOException.class, BusinessException.class},  // also rollback these checked types
    noRollbackFor = {OptimisticLockException.class}                // DON'T rollback this RuntimeException
)
public void process() throws IOException { ... }
```

Internally, Spring compiles these into a list of `RollbackRuleAttribute` objects (positive rules) and `NoRollbackRuleAttribute` objects (negative rules). When an exception escapes the method, Spring walks the rule list and picks the most specific match.

## 2. Why & when

The default rule (rollback on unchecked only) reflects Java's convention that `RuntimeException` signals unexpected conditions that violate system integrity, while `Exception` signals recoverable application conditions. But this convention breaks in practice:

- Your `InsufficientFundsException extends Exception` is a business failure — it **should** rollback.
- Your `StaleDataWarning extends RuntimeException` is informational — it **should not** rollback.

Use `rollbackFor` whenever a checked exception represents a genuine failure that should undo all work done so far. Use `noRollbackFor` when a `RuntimeException` subclass is informational and committing partial work is acceptable.

## 3. Core concept

Spring stores rollback rules as a list of `RollbackRuleAttribute` objects in `RuleBasedTransactionAttribute`. When an exception escapes, `rollbackOn(Throwable ex)` is called:

1. Walk the rule list.
2. For each rule, compute the **depth** of the match in the exception class hierarchy: exact match = 0, superclass match = 1, superclass-of-superclass = 2, etc. No match = `Integer.MAX_VALUE`.
3. Pick the rule with the **smallest depth** (most specific).
4. If the winning rule is a `RollbackRuleAttribute` (positive) → rollback; if `NoRollbackRuleAttribute` → commit.
5. If no rule matches → apply the default (rollback on `RuntimeException`/`Error`, commit on `Exception`).

This means you can have both `rollbackFor = IOException.class` and `noRollbackFor = FileNotFoundException.class` — `FileNotFoundException extends IOException`, so the more specific `NoRollbackRuleAttribute` wins for that subclass.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="rarr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#f85149"/>
    </marker>
    <marker id="garr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Exception escapes -->
  <rect x="10" y="80" width="120" height="50" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="70" y="101" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Exception</text>
  <text x="70" y="117" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">escapes method</text>

  <line x1="132" y1="105" x2="185" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Rule evaluation -->
  <rect x="185" y="55" width="200" height="100" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="285" y="78" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Rule evaluation</text>
  <line x1="195" y1="86" x2="375" y2="86" stroke="#8b949e" stroke-width="0.5"/>
  <text x="285" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">find closest rule match</text>
  <text x="285" y="119" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">rollbackFor vs noRollbackFor</text>
  <text x="285" y="134" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">depth-first hierarchy match</text>

  <!-- ROLLBACK branch -->
  <line x1="387" y1="85" x2="440" y2="55" stroke="#f85149" stroke-width="1.5" marker-end="url(#rarr)"/>
  <rect x="440" y="25" width="140" height="50" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="510" y="48" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">ROLLBACK</text>
  <text x="510" y="64" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">rollbackFor matched</text>

  <!-- COMMIT branch -->
  <line x1="387" y1="125" x2="440" y2="155" stroke="#6db33f" stroke-width="1.5" marker-end="url(#garr)"/>
  <rect x="440" y="135" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="158" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">COMMIT</text>
  <text x="510" y="174" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">noRollbackFor matched</text>

  <!-- Default -->
  <rect x="440" y="85" width="140" height="40" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="510" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Default (no match):</text>
  <text x="510" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">RuntimeException→ROLLBACK</text>
</svg>

Exception walks the rule list; most-specific match (smallest inheritance depth) wins.

## 5. Runnable example

Scenario: a **`PaymentService`** with a custom exception hierarchy — demonstrating `rollbackFor`, `noRollbackFor`, and the hierarchy depth rule.

### Level 1 — Basic

Checked `PaymentException` causes rollback with `rollbackFor`.

```java
// RollbackRulesDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class RollbackRulesDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("payments-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(RollbackRulesDemo.class);
        PaymentService svc = ctx.getBean(PaymentService.class);

        // Without rollbackFor: checked exception commits (wrong!)
        try { svc.processDefault("TXN-1", -100.0); } catch (Exception e) {
            System.out.println("DEFAULT (no rollbackFor): " + e.getMessage());
        }

        // With rollbackFor: checked exception rolls back (correct!)
        try { svc.processWithRollback("TXN-2", -100.0); } catch (Exception e) {
            System.out.println("WITH rollbackFor: rolled back");
        }
        ctx.close();
    }
}

class PaymentException extends Exception {
    PaymentException(String msg) { super(msg); }
}

@Service
class PaymentService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    PaymentService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional          // no rollbackFor — checked exception COMMITS
    public void processDefault(String txnId, double amount) throws PaymentException {
        jdbc.update("INSERT INTO payments(id,amount,status) VALUES(?,'PENDING')", txnId, amount);
        if (amount < 0) throw new PaymentException("Negative amount: " + amount);
    }

    @Transactional(rollbackFor = PaymentException.class)   // checked exception ROLLS BACK
    public void processWithRollback(String txnId, double amount) throws PaymentException {
        jdbc.update("INSERT INTO payments(id,amount,status) VALUES(?,'PENDING')", txnId, amount);
        if (amount < 0) throw new PaymentException("Negative amount: " + amount);
    }
}
```

`payments-schema.sql`:
```sql
CREATE TABLE payments (id VARCHAR(20) PRIMARY KEY, amount DECIMAL(10,2), status VARCHAR(20));
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. RollbackRulesDemo.java`

`processDefault` commits despite the exception — the `INSERT` with `amount=-100` is committed, which is wrong. `processWithRollback` rolls it back. `rollbackFor = PaymentException.class` adds a positive rollback rule for the checked exception.

---

### Level 2 — Intermediate

**`noRollbackFor`** — an informational `RuntimeException` should not undo the transaction.

```java
// RollbackRulesDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class RollbackRulesDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("payments-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(RollbackRulesDemo.class);
        PaymentService svc = ctx.getBean(PaymentService.class);

        try {
            svc.processWithWarning("TXN-3", 500.0);
        } catch (FraudWarning w) {
            System.out.println("Warning propagated (tx committed): " + w.getMessage());
        }
        ctx.close();
    }
}

class FraudWarning extends RuntimeException {
    FraudWarning(String msg) { super(msg); }
}

@Service
class PaymentService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    PaymentService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional(noRollbackFor = FraudWarning.class)   // commit despite RuntimeException
    public void processWithWarning(String txnId, double amount) {
        jdbc.update("INSERT INTO payments(id,amount,status) VALUES(?,?,'FLAGGED')", txnId, amount);
        System.out.println("Payment inserted (flagged): " + txnId);
        // FraudWarning is a RuntimeException — default rule would rollback, but noRollbackFor overrides
        throw new FraudWarning("High-value transaction flagged for review: $" + amount);
    }
}
```

How to run: same classpath

Without `noRollbackFor`, the `RuntimeException` would trigger a rollback — the INSERT would be undone. With `noRollbackFor = FraudWarning.class`, the INSERT commits (the payment is recorded as `FLAGGED`), and the `FraudWarning` propagates to the caller for logging or retry handling.

---

### Level 3 — Advanced

**Hierarchy depth rule** — `rollbackFor = IOException.class` + `noRollbackFor = FileNotFoundException.class`. `FileNotFoundException` (subclass) beats `IOException` (superclass).

```java
// RollbackRulesDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import java.io.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class RollbackRulesDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("payments-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(RollbackRulesDemo.class);
        PaymentService svc = ctx.getBean(PaymentService.class);

        // IOException (not FileNotFoundException) → rollback
        try { svc.storeReceipt("TXN-4", "generic-io-failure"); }
        catch (Exception e) { System.out.println("IOException → rolled back: " + e.getMessage()); }

        // FileNotFoundException (subclass) → commit (noRollbackFor wins)
        try { svc.storeReceipt("TXN-5", "file-not-found"); }
        catch (Exception e) { System.out.println("FileNotFoundException → committed: " + e.getMessage()); }

        ctx.close();
    }
}

@Service
class PaymentService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    PaymentService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional(
        rollbackFor   = IOException.class,              // rollback on IOException and subclasses
        noRollbackFor = FileNotFoundException.class     // EXCEPT FileNotFoundException (more specific)
    )
    public void storeReceipt(String txnId, String mode) throws IOException {
        jdbc.update("INSERT INTO payments(id,amount,status) VALUES(?,0,'RECEIPT')", txnId);
        System.out.println("Inserted receipt for " + txnId + " (mode=" + mode + ")");
        if ("generic-io-failure".equals(mode)) throw new IOException("Storage unavailable");
        if ("file-not-found".equals(mode))     throw new FileNotFoundException("template.pdf not found");
    }
}
```

How to run: same classpath

`IOException` at depth 0 matches the `rollbackFor` rule → rollback. `FileNotFoundException` matches `noRollbackFor` at depth 0 and `rollbackFor` at depth 1 (`FileNotFoundException extends IOException`). **Most specific wins** → `noRollbackFor` wins → commit. The `TXN-5` INSERT is committed.

## 6. Walkthrough

**Level 3 — rule evaluation detail:**

```
storeReceipt("TXN-5","file-not-found")
  tx opens
  INSERT payments ('TXN-5',0,'RECEIPT')   [on conn]
  throw FileNotFoundException("template.pdf not found")

TransactionInterceptor.rollbackOn(FileNotFoundException):
  rules = [
    NoRollbackRuleAttribute(FileNotFoundException)   ← added from noRollbackFor
    RollbackRuleAttribute(IOException)               ← added from rollbackFor
    RollbackRuleAttribute(RuntimeException)          ← the built-in default
  ]
  for each rule, compute depth of FileNotFoundException in hierarchy:
    NoRollbackRuleAttribute(FileNotFoundException): depth=0  ← EXACT MATCH, smallest
    RollbackRuleAttribute(IOException):             depth=1
    RollbackRuleAttribute(RuntimeException):        no match

  winning rule: NoRollbackRuleAttribute → DO NOT rollback → COMMIT
  conn.commit()
  FileNotFoundException re-thrown to caller
```

**Level 1 — default vs rollbackFor:**

```
processDefault throws PaymentException (checked):
  rules = [RollbackRuleAttribute(RuntimeException) default]
  PaymentException not a subclass of RuntimeException → no rule matches
  default: checked exception → COMMIT  ← wrong!

processWithRollback throws PaymentException (rollbackFor):
  rules = [RollbackRuleAttribute(PaymentException), RollbackRuleAttribute(RuntimeException) default]
  PaymentException depth 0 in RollbackRuleAttribute(PaymentException) → wins → ROLLBACK  ← correct
```

## 7. Gotchas & takeaways

> **Checked exceptions commit by default.** If your custom `BusinessException extends Exception` signals an abort, you MUST add `rollbackFor = BusinessException.class`. Otherwise Spring silently commits partial work.

> **`rollbackFor` is additive, not replacing.** Adding `rollbackFor = IOException.class` still rolls back on `RuntimeException` (the built-in rule). You cannot remove the default `RuntimeException` rollback rule with `noRollbackFor`... unless you explicitly list every `RuntimeException` subclass, which is impractical.

> **`noRollbackFor` on a superclass + `rollbackFor` on a subclass works as expected.** The more specific (lower depth) rule always wins. This lets you fine-tune an entire exception family with one parent rule and one override.

- Default: rollback on `RuntimeException`/`Error`; commit on `Exception`.
- `rollbackFor`: extend rollback to named checked (or unchecked) exception types.
- `noRollbackFor`: prevent rollback for informational `RuntimeException` subclasses.
- Hierarchy depth rule: most specific type in the class hierarchy wins.
- `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()` is the programmatic equivalent — marks rollback without throwing any exception.
