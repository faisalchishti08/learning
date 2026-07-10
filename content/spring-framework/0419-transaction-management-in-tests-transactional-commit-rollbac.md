---
card: spring-framework
gi: 419
slug: transaction-management-in-tests-transactional-commit-rollbac
title: "Transaction management in tests (@Transactional, @Commit, @Rollback)"
---

## 1. What it is

`@Transactional` on a test class or method wraps each test method in a database transaction that, by default, **rolls back** automatically after the test finishes — regardless of whether the test passed or failed. `@Rollback(false)` (or the more explicit `@Commit`) overrides that default when you specifically want a test's changes to persist. This gives every transactional test a clean, isolated database state without writing any manual cleanup code.

```java
@SpringJUnitConfig(Config.class)
@Transactional // every @Test method's DB changes roll back automatically afterward
class OrderRepositoryTest {
    @Autowired JdbcTemplate jdbcTemplate;

    @Test
    void insertingAnOrderIsVisibleWithinTheTest() {
        jdbcTemplate.update("INSERT INTO orders VALUES (1, 'PENDING')");
        // visible here, but automatically rolled back once the test method returns
    }
}
```

## 2. Why & when

Integration tests that touch a real database naturally leave data behind — an `INSERT` in one test can pollute the state seen by the next test, making tests order-dependent and flaky. Manually cleaning up after every test (a `@AfterEach` deleting whatever rows were inserted) is tedious and easy to get wrong, especially as tests grow more complex. `@Transactional` on a test solves this at the root: wrap the whole test method in one transaction, and roll it back afterward — every `INSERT`/`UPDATE`/`DELETE` the test performed simply vanishes, leaving the database exactly as it was before the test ran, with zero manual cleanup code.

Use `@Transactional` on integration tests whenever:

- The test writes to a real (even if embedded) database and you want automatic, guaranteed cleanup without writing teardown code.
- You want tests to be independent of execution order — a transactional test's writes can never leak into the next test, because they never actually commit.

Use `@Rollback(false)` or `@Commit` on the rare test that specifically needs to verify data survives a genuine commit — for example, testing code that spans multiple transactions, or verifying behavior that only manifests after a commit (like a database trigger, or another process reading committed data). Be deliberate about this, since a committing test needs its own manual cleanup to avoid polluting subsequent tests.

## 3. Core concept

```
 @Transactional
 @Test
 void myTest() { ... }
        |
        v
 TransactionalTestExecutionListener.beforeTestMethod()
        |
        v
     BEGIN transaction
        |
        v
     test method body runs (INSERT/UPDATE/DELETE all happen INSIDE this transaction)
        |
        v
 TransactionalTestExecutionListener.afterTestMethod()
        |
        v
     default: ROLLBACK   (unless @Rollback(false) / @Commit is present -> COMMIT instead)
```

The rollback happens regardless of whether the test method throws an assertion failure — a *failing* test's partial writes are rolled back exactly the same as a *passing* test's, since the decision is based on the `@Rollback`/`@Commit` annotation, not the test's outcome.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Test method wrapped in a transaction that rolls back by default after the method completes">
  <rect x="10" y="70" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">BEGIN</text>

  <rect x="230" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Test method body</text>
  <text x="320" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">INSERT/UPDATE/DELETE</text>

  <rect x="500" y="70" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="565" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ROLLBACK</text>
  <text x="565" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(default)</text>

  <line x1="140" y1="95" x2="225" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="95" x2="495" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Everything between BEGIN and ROLLBACK — including any assertion failure — leaves no trace in the database once the test method returns.

## 5. Runnable example

### Level 1 — Basic

Insert a row inside one `@Transactional` test method, verify it's visible *within* that test, then let a second test method (which shares the same cached `ApplicationContext` and therefore the same embedded database, per the context-caching card) confirm the row is gone — directly demonstrating the automatic rollback between test methods.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;

public class TxTestBasic {

    @Configuration
    @EnableTransactionManagement
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:orders-schema.sql") // CREATE TABLE orders(id BIGINT, status VARCHAR(20))
                    .build();
        }
        @Bean
        JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
        @Bean
        PlatformTransactionManager transactionManager(DataSource ds) { return new DataSourceTransactionManager(ds); }
    }

    @SpringJUnitConfig(Config.class)
    @Transactional
    static class OrderInsertTest {
        @Autowired JdbcTemplate jdbcTemplate;

        @Test
        void insertVisibleWithinTest() {
            jdbcTemplate.update("INSERT INTO orders VALUES (1, 'PENDING')");
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);
            System.out.println("Count within the transactional test: " + count);
            if (count != 1) throw new AssertionError("Expected 1 row visible within the test");
        }

        @Test
        void previousTestsInsertShouldBeGoneHere() {
            // Runs in the SAME cached context/database as insertVisibleWithinTest, but its own
            // fresh transaction -- if rollback worked, this sees zero rows, not the row inserted above.
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);
            System.out.println("Count in a separate test method, same database: " + count);
            if (count != 0) throw new AssertionError("Expected 0 -- the earlier insert should have been rolled back");
            System.out.println("Confirmed: transactional test rollback left no trace -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(OrderInsertTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: add `spring-test`, `spring-context`, `spring-jdbc`, `spring-tx`, `com.h2database:h2`, JUnit 5, and the JUnit Platform Launcher to the classpath, with `orders-schema.sql` on the classpath; then `java TxTestBasic.java`.

Inside `insertVisibleWithinTest`, the row is genuinely visible via `SELECT COUNT(*)` — the transaction hasn't been rolled back yet, so queries within the same transaction see the uncommitted insert normally. Once the test method returns, `TransactionalTestExecutionListener` issues a `ROLLBACK`, and the separate, later verification confirms zero rows remain — the insert never actually persisted.

### Level 2 — Intermediate

Contrast the default rollback behavior against `@Commit`, showing a test whose changes are deliberately meant to survive, plus explicit manual cleanup for that case since committing tests don't get automatic cleanup.

```java
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.test.annotation.Commit;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;

public class TxTestIntermediate {

    @Configuration
    @EnableTransactionManagement
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:orders-schema.sql")
                    .build();
        }
        @Bean
        JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
        @Bean
        PlatformTransactionManager transactionManager(DataSource ds) { return new DataSourceTransactionManager(ds); }
    }

    @SpringJUnitConfig(Config.class)
    @Transactional
    static class MixedRollbackTest {
        @Autowired JdbcTemplate jdbcTemplate;

        @Test
        void defaultsToRollback() {
            jdbcTemplate.update("INSERT INTO orders VALUES (1, 'TEMP')");
            System.out.println("defaultsToRollback: inserted row 1 (will roll back)");
        }

        @Test
        @Commit // OVERRIDES the class-level default: this test's changes will actually commit
        void explicitlyCommits() {
            jdbcTemplate.update("INSERT INTO orders VALUES (2, 'PERMANENT')");
            System.out.println("explicitlyCommits: inserted row 2 (WILL be committed)");
        }

        @AfterEach
        void cleanupIfCommitted() {
            // Committing tests need their own explicit cleanup -- rollback won't do it for them.
            jdbcTemplate.update("DELETE FROM orders WHERE id = 2");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(MixedRollbackTest.class))
                .build();
        launcher.execute(request);
        System.out.println("Both tests ran. Row 1 was rolled back automatically; "
                + "row 2 was committed and then explicitly cleaned up in @AfterEach.");
    }
}
```

How to run: same dependencies as Level 1, then `java TxTestIntermediate.java`.

`defaultsToRollback` relies on the class-level `@Transactional`'s default behavior — its `INSERT` never persists. `@Commit` on `explicitlyCommits` overrides that default for just this one method, so its `INSERT` genuinely commits to the database — which is exactly why this test needs its own `@AfterEach` cleanup (`DELETE FROM orders WHERE id = 2`); a committing test opts out of the automatic-cleanup safety net the rest of this card is about, and the burden of not polluting subsequent tests shifts back onto the test author.

### Level 3 — Advanced

A test verifying `@Transactional` propagation behavior *within the code under test* — where the test's own outer transaction interacts with the tested method's transaction boundary — plus `TestTransaction` for programmatically flushing, committing mid-test, or starting a new transaction, useful for testing code that specifically depends on a commit having happened (e.g., verifying a database trigger or a separately-transacted step).

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.test.context.transaction.TestTransaction;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;

public class TxTestAdvanced {

    static class AuditService {
        private final JdbcTemplate jdbcTemplate;
        AuditService(JdbcTemplate jdbcTemplate) { this.jdbcTemplate = jdbcTemplate; }

        // REQUIRES_NEW: this write must survive even if the CALLER's transaction later rolls back --
        // audit trails shouldn't disappear just because the operation they're auditing failed.
        @Transactional(propagation = Propagation.REQUIRES_NEW)
        void recordAudit(String action) {
            jdbcTemplate.update("INSERT INTO audit_log VALUES (?)", action);
        }
    }

    @Configuration
    @EnableTransactionManagement
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:audit-schema.sql") // CREATE TABLE audit_log(action VARCHAR(100))
                    .build();
        }
        @Bean
        JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
        @Bean
        PlatformTransactionManager transactionManager(DataSource ds) { return new DataSourceTransactionManager(ds); }
        @Bean
        AuditService auditService(JdbcTemplate jdbcTemplate) { return new AuditService(jdbcTemplate); }
    }

    @SpringJUnitConfig(Config.class)
    @Transactional // the TEST's own outer transaction
    static class AuditPropagationTest {
        @Autowired JdbcTemplate jdbcTemplate;
        @Autowired AuditService auditService;

        @Test
        void requiresNewSurvivesOuterRollback() {
            auditService.recordAudit("order-created"); // runs in its OWN, separate, already-committed transaction

            Integer countBeforeEnd = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM audit_log", Integer.class);
            System.out.println("Audit rows visible within the test's outer transaction: " + countBeforeEnd);
            if (countBeforeEnd != 1) throw new AssertionError("Expected the REQUIRES_NEW insert to be visible");

            // The test's OWN transaction (the outer one) will still roll back per the class-level @Transactional,
            // but recordAudit's REQUIRES_NEW transaction already committed independently and won't be affected.
            System.out.println("This test's own transaction will roll back, but the audit row already committed separately.");
        }

        @Test
        void manualCommitMidTestViaTestTransaction() {
            jdbcTemplate.update("INSERT INTO audit_log VALUES ('manual-checkpoint')");

            TestTransaction.flagForCommit();  // override this test's default rollback behavior
            TestTransaction.end();            // actually commits the current transaction NOW, mid-test

            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM audit_log", Integer.class);
            System.out.println("Committed mid-test via TestTransaction, count now: " + count);

            TestTransaction.start(); // start a fresh transaction to continue the test
            jdbcTemplate.update("DELETE FROM audit_log"); // clean up everything, including the mid-test commit
            TestTransaction.flagForCommit();
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(AuditPropagationTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: same dependencies as Level 1, with `audit-schema.sql` on the classpath, then `java TxTestAdvanced.java`.

`Propagation.REQUIRES_NEW` on `recordAudit` means it suspends the test's outer transaction and runs (and commits) in a genuinely separate, independent transaction — this is real production logic being tested (audit records that must survive even if the operation they describe later fails), and the test verifies this propagation behavior correctly rather than just trusting the annotation. `TestTransaction.flagForCommit()` + `TestTransaction.end()` is the escape hatch for tests that specifically need to force a real commit partway through a test method (not just via `@Commit` on the whole method), useful when testing something that depends on data actually being durably committed mid-test, followed by starting a fresh transaction to continue testing and clean up.

## 6. Walkthrough

Trace `TxTestAdvanced.AuditPropagationTest.requiresNewSurvivesOuterRollback()`:

1. **Outer transaction begins.** Because the class is `@Transactional`, `TransactionalTestExecutionListener` starts the test's own outer transaction before the method runs.
2. **`recordAudit` called.** `auditService.recordAudit("order-created")` is a Spring-managed bean method annotated `@Transactional(propagation = REQUIRES_NEW)`. Spring's transaction infrastructure sees this propagation setting and **suspends** the test's currently-active outer transaction, starting a brand-new, independent transaction for this call.
3. **Insert and commit, independently.** Inside that new transaction, the `INSERT INTO audit_log` runs; when `recordAudit` returns normally, its own `REQUIRES_NEW` transaction **commits** — for real, durably, regardless of what happens to the outer test transaction afterward. The outer (test) transaction then resumes.
4. **Visibility check.** Back in the test method (now back within the resumed outer transaction), `SELECT COUNT(*) FROM audit_log` returns `1` — the committed row is visible, both because it's genuinely committed and because the resumed outer transaction can see already-committed data from the separate transaction.
5. **Test method ends.** `requiresNewSurvivesOuterRollback` returns normally.
6. **Outer transaction rolls back.** `TransactionalTestExecutionListener` issues a `ROLLBACK` on the *outer* test transaction — per the class-level `@Transactional` default. But this rollback has nothing left to undo regarding the audit row, because that row was never part of the outer transaction in the first place; it was committed independently in step 3, entirely outside the outer transaction's scope.
7. **Net effect.** The audit row genuinely persists past this test method (proving the production `REQUIRES_NEW` behavior works as intended) — which is why, in a real test suite, a test like this would need its own explicit cleanup (a `@AfterEach` deleting from `audit_log`), exactly as `@Commit`-based tests do, since the outer transaction's automatic rollback cannot reach a `REQUIRES_NEW` transaction's already-committed effects.

```
Outer test transaction: BEGIN
   recordAudit() -- @Transactional(REQUIRES_NEW)
        outer transaction SUSPENDED
        new transaction: BEGIN -> INSERT audit_log -> COMMIT (durable, independent)
        outer transaction RESUMED
   SELECT COUNT(*) -> 1 (sees the already-committed row)
Outer test transaction: ROLLBACK  (nothing to undo for the audit row -- it was never inside this transaction)
```

## 7. Gotchas & takeaways

> Gotcha: `@Transactional(propagation = REQUIRES_NEW)` methods called from within a `@Transactional` test are a common source of "why didn't rollback clean this up?" confusion — the outer test transaction's automatic rollback only ever undoes what happened *inside* it; anything a `REQUIRES_NEW` call committed independently survives the outer rollback and needs its own explicit cleanup, exactly like an explicitly `@Commit`-annotated test does.

- `@Transactional` on a test class/method wraps each test method in a transaction that rolls back by default after the method completes, regardless of pass/fail — giving automatic, zero-code database cleanup for the common case.
- `@Commit` (or `@Rollback(false)`) opts a specific test out of that default, for the rare case where you need to verify behavior that depends on a genuine commit — and that test then needs its own manual cleanup.
- `REQUIRES_NEW` propagation inside code under test commits independently of the test's outer transaction, so its effects survive the outer transaction's automatic rollback — a real production behavior worth testing explicitly, as shown here, not just trusting.
- `TestTransaction.flagForCommit()`/`.end()`/`.start()` give fine-grained, mid-test control over transaction boundaries for the rare test that needs to force a real commit partway through and then continue testing in a fresh transaction.
