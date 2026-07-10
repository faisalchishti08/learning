---
card: spring-framework
gi: 420
slug: sql-test-database-setup
title: "@Sql & test database setup"
---

## 1. What it is

`@Sql` runs SQL scripts (or inline statements) against a test's `DataSource` at a specified point in the test lifecycle — before or after a test method (or class) runs. It's the declarative way to seed known test data or reset schema state, instead of writing that setup as imperative `JdbcTemplate` calls scattered through test methods.

```java
@Test
@Sql("classpath:seed-products.sql")   // runs BEFORE this test method, by default
void findsSeededProducts() {
    List<Product> products = productRepository.findAll();
    assertEquals(2, products.size());
}
```

## 2. Why & when

A test that needs specific rows present to exercise a query meaningfully (testing "find products under $50" needs actual rows with varying prices) either builds that data imperatively with repeated `jdbcTemplate.update(...)` calls at the top of every test method, or declares it once as a reusable SQL script and lets `@Sql` run it automatically. The declarative approach keeps the *data setup* separate from the *test logic*, makes the seed data reusable across multiple tests, and keeps individual test methods focused on what they're actually verifying rather than cluttered with setup boilerplate.

Reach for `@Sql` when:

- A test needs specific, known rows to exist before it runs — seed data for a query test, a specific "current state" for a business-logic test.
- Several tests in a class (or across classes) need the same baseline data — write the script once, reference it from every test that needs it.
- You want schema setup (creating tables not already handled by a global schema script) scoped to just the tests that need it, rather than adding to a shared, all-tests schema file.

Combine `@Sql` with `@Transactional` (from the previous card) for the common case: `@Sql` seeds data inside the test's transaction, the test exercises it, and the transaction rolls back afterward — meaning you rarely need a matching `@Sql` cleanup script, since rollback handles cleanup automatically.

## 3. Core concept

```
 @Test
 @Sql("classpath:seed-products.sql")     <- default phase: BEFORE_TEST_METHOD
 void myTest() { ... }

 @Test
 @Sql(scripts = "classpath:cleanup.sql",
      executionPhase = Sql.ExecutionPhase.AFTER_TEST_METHOD)
 void anotherTest() { ... }
        |
        v
 SqlScriptsTestExecutionListener
        |
        | at the configured phase, executes each script's
        | statements against the test's DataSource, inside
        | whatever transaction is already active (if @Transactional)
        v
     database state reflects the script's INSERT/UPDATE/DDL statements
```

`@Sql` can be applied at the class level (runs for every test method) or the method level (runs for just that one), and multiple `@Sql` annotations can target different phases (before vs. after) on the same test.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sql script runs before the test method, test runs, transaction rolls back afterward">
  <rect x="10" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Sql script runs</text>
  <text x="85" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BEFORE_TEST_METHOD</text>

  <rect x="245" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Test method body</text>

  <rect x="480" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ROLLBACK (if @Transactional)</text>

  <line x1="160" y1="95" x2="240" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="395" y1="95" x2="475" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both the seed script's inserts and anything the test itself does are inside the same transaction, so both roll back together automatically.

## 5. Runnable example

### Level 1 — Basic

Seed two rows via `@Sql` before a test method, and verify the test sees exactly that seeded data — the most common `@Sql` usage.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;
import java.util.List;

public class SqlTestBasic {

    @Configuration
    @EnableTransactionManagement
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:products-schema.sql") // CREATE TABLE products(id BIGINT, name VARCHAR(100), price DECIMAL)
                    .build();
        }
        @Bean JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
        @Bean PlatformTransactionManager transactionManager(DataSource ds) { return new DataSourceTransactionManager(ds); }
    }

    @SpringJUnitConfig(Config.class)
    @Transactional
    static class ProductQueryTest {
        @Autowired JdbcTemplate jdbcTemplate;

        @Test
        @Sql("classpath:seed-two-products.sql")
        // seed-two-products.sql contains:
        //   INSERT INTO products VALUES (1, 'Keyboard', 49.99);
        //   INSERT INTO products VALUES (2, 'Monitor', 199.99);
        void findsSeededProducts() {
            List<String> names = jdbcTemplate.queryForList("SELECT name FROM products ORDER BY id", String.class);
            System.out.println("Seeded product names: " + names);
            if (!names.equals(List.of("Keyboard", "Monitor"))) throw new AssertionError("Unexpected seed data");
            System.out.println("findsSeededProducts -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(ProductQueryTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: add `spring-test`, `spring-context`, `spring-jdbc`, `spring-tx`, `com.h2database:h2`, JUnit 5, and the JUnit Platform Launcher to the classpath, with `products-schema.sql` and `seed-two-products.sql` on the classpath; then `java SqlTestBasic.java`.

`@Sql("classpath:seed-two-products.sql")` on the test method runs before `findsSeededProducts` executes, inside the same transaction the class-level `@Transactional` already started — so the seeded rows are visible to the test's query, and (because of `@Transactional`'s default rollback) automatically undone afterward with no separate cleanup script needed.

### Level 2 — Intermediate

Use class-level `@Sql` (shared baseline for every test in the class) combined with method-level `@Sql` (additional, test-specific data), and control script execution order and error handling with `@SqlConfig`.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.context.jdbc.SqlConfig;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;

public class SqlTestIntermediate {

    @Configuration
    @EnableTransactionManagement
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:orders-schema.sql") // CREATE TABLE orders(id BIGINT, customer VARCHAR(50), status VARCHAR(20))
                    .build();
        }
        @Bean JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
        @Bean PlatformTransactionManager transactionManager(DataSource ds) { return new DataSourceTransactionManager(ds); }
    }

    @SpringJUnitConfig(Config.class)
    @Transactional
    @Sql("classpath:seed-baseline-customer.sql")
    // seed-baseline-customer.sql: INSERT INTO orders VALUES (1, 'Ada', 'PENDING');
    @SqlConfig(errorMode = SqlConfig.ErrorMode.FAIL_ON_ERROR) // fail loudly if a script errors, don't silently skip
    static class OrderQueryTest {
        @Autowired JdbcTemplate jdbcTemplate;

        @Test
        void baselineCustomerAlwaysPresent() {
            // Class-level @Sql already ran -- every test method sees the baseline row.
            Integer count = jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM orders WHERE customer = 'Ada'", Integer.class);
            if (count != 1) throw new AssertionError("Expected baseline customer to be present");
            System.out.println("baselineCustomerAlwaysPresent -- PASS");
        }

        @Test
        @Sql("classpath:seed-extra-customer.sql")
        // seed-extra-customer.sql: INSERT INTO orders VALUES (2, 'Bob', 'SHIPPED');
        void classAndMethodLevelSqlBothApply() {
            // Both the class-level baseline AND this method-level extra row should be present.
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);
            System.out.println("Total orders visible (baseline + method-level seed): " + count);
            if (count != 2) throw new AssertionError("Expected both baseline and extra rows, got " + count);
            System.out.println("classAndMethodLevelSqlBothApply -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(OrderQueryTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: same dependencies as Level 1, with `orders-schema.sql`, `seed-baseline-customer.sql`, and `seed-extra-customer.sql` on the classpath; then `java SqlTestIntermediate.java`.

The class-level `@Sql("classpath:seed-baseline-customer.sql")` runs before *every* test method in `OrderQueryTest`, establishing a shared baseline; `classAndMethodLevelSqlBothApply`'s method-level `@Sql` adds to that baseline for just this one test, and both scripts' inserts are visible together — class-level and method-level `@Sql` compose rather than one replacing the other. `@SqlConfig(errorMode = FAIL_ON_ERROR)` ensures a broken script (a typo, a missing table) fails the test loudly rather than silently continuing with incomplete seed data.

### Level 3 — Advanced

Combine `AFTER_TEST_METHOD` execution phase for teardown-style scripts (useful outside a `@Transactional` context, or for cleanup that must run even without transaction rollback), and inline SQL statements via `@Sql(statements = ...)` for small, one-off setup that doesn't warrant a separate script file.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import javax.sql.DataSource;

public class SqlTestAdvanced {

    @Configuration
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:counters-schema.sql") // CREATE TABLE counters(name VARCHAR(50), value INT)
                    .build();
        }
        @Bean JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
    }

    // NOTE: deliberately NOT @Transactional here -- this class tests behavior WITHOUT
    // automatic rollback, so AFTER_TEST_METHOD cleanup scripts are genuinely needed.
    @SpringJUnitConfig(Config.class)
    static class CounterTest {
        @Autowired JdbcTemplate jdbcTemplate;

        @Test
        @Sql(statements = "INSERT INTO counters VALUES ('visits', 0)") // inline, no separate file needed
        @Sql(statements = "DELETE FROM counters WHERE name = 'visits'",
             executionPhase = Sql.ExecutionPhase.AFTER_TEST_METHOD)
        void incrementingCounterWorksAndCleansUpAfterward() {
            jdbcTemplate.update("UPDATE counters SET value = value + 1 WHERE name = 'visits'");
            jdbcTemplate.update("UPDATE counters SET value = value + 1 WHERE name = 'visits'");

            Integer value = jdbcTemplate.queryForObject(
                    "SELECT value FROM counters WHERE name = 'visits'", Integer.class);
            System.out.println("Counter value after two increments: " + value);
            if (value != 2) throw new AssertionError("Expected 2, got " + value);
            System.out.println("incrementingCounterWorksAndCleansUpAfterward -- PASS");
            // Without @Transactional, these UPDATEs are genuinely committed --
            // the AFTER_TEST_METHOD @Sql above is what removes the row afterward.
        }

        @Test
        void counterTableIsEmptyAfterPreviousTestCleanedUp() {
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM counters", Integer.class);
            System.out.println("Counters table row count in a fresh test: " + count);
            if (count != 0) throw new AssertionError("Expected the AFTER_TEST_METHOD cleanup to have run, got " + count + " rows");
            System.out.println("counterTableIsEmptyAfterPreviousTestCleanedUp -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(CounterTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: same dependencies as Level 1 (no `spring-tx` needed here, since this class intentionally has no `@Transactional`), with `counters-schema.sql` on the classpath; then `java SqlTestAdvanced.java`.

Because `CounterTest` is deliberately not `@Transactional`, every `UPDATE`/`INSERT` genuinely commits — there's no automatic rollback safety net here, which is exactly why the `AFTER_TEST_METHOD`-phased `@Sql` cleanup script is necessary: without it, the `'visits'` row would leak into `counterTableIsEmptyAfterPreviousTestCleanedUp`, and that second test's assertion would fail. `@Sql(statements = "...")` (inline SQL, no separate file) is convenient for a single short statement where creating a whole `.sql` file feels like overkill.

## 6. Walkthrough

Trace `SqlTestAdvanced.CounterTest`'s two test methods in sequence:

1. **`incrementingCounterWorksAndCleansUpAfterward` begins.** Before the method body runs, the `BEFORE_TEST_METHOD`-phased (the default) inline `@Sql(statements = "INSERT INTO counters VALUES ('visits', 0)")` executes, inserting a starting row.
2. **Test body runs.** Two `UPDATE counters SET value = value + 1` statements execute, each genuinely committing immediately (no surrounding transaction to defer them) — the counter reaches `2`.
3. **Assertion passes.** The test queries and confirms `value == 2`, printing the success line.
4. **`AFTER_TEST_METHOD` cleanup fires.** After the test method returns, the second `@Sql` annotation's `DELETE FROM counters WHERE name = 'visits'` executes — this is a real, separate SQL statement that genuinely removes the row, since (again) there's no transaction rollback to rely on instead.
5. **Second test begins.** `counterTableIsEmptyAfterPreviousTestCleanedUp` runs next (assuming JUnit's default execution order, though tests generally shouldn't rely on this) — since context caching means it shares the same embedded database as the first test, its `SELECT COUNT(*)` genuinely reflects whatever state the first test left behind.
6. **Assertion confirms cleanup worked.** The count is `0`, proving the `AFTER_TEST_METHOD` cleanup script from step 4 genuinely ran and genuinely removed the row — if that cleanup script were missing or buggy, this second test would see a leftover row and fail, exactly the kind of test-pollution bug `@Transactional` normally prevents automatically.

```
Test 1 (incrementingCounterWorksAndCleansUpAfterward):
   BEFORE_TEST_METHOD @Sql: INSERT 'visits', 0    (committed, no transaction)
   test body: UPDATE x2 -> value = 2
   assert value == 2 -- PASS
   AFTER_TEST_METHOD @Sql: DELETE 'visits'         (committed cleanup)

Test 2 (counterTableIsEmptyAfterPreviousTestCleanedUp):
   same database (context cached) -- SELECT COUNT(*) -> 0
   assert count == 0 -- PASS (proves cleanup from Test 1 actually worked)
```

## 7. Gotchas & takeaways

> Gotcha: `@Sql`'s cleanup scripts (`AFTER_TEST_METHOD`) are only strictly necessary when a test class is *not* wrapped in a rolled-back `@Transactional` boundary — combining `@Transactional` (which rolls back everything, including anything `@Sql` inserted) with an `AFTER_TEST_METHOD` cleanup script is usually redundant, though harmless. The pattern in Level 3 (no `@Transactional`, explicit `AFTER_TEST_METHOD` cleanup) is specifically for tests that need to verify genuinely committed behavior and therefore can't rely on rollback for cleanup.

- `@Sql` declaratively seeds (or cleans up) test data via real SQL scripts, keeping data setup separate from test assertion logic and reusable across multiple tests.
- Class-level and method-level `@Sql` annotations compose — both run, rather than one overriding the other — letting you establish a shared baseline plus test-specific additions.
- Pair `@Sql` with `@Transactional` for the common case: seeded data and any test-made changes both roll back together automatically, usually eliminating the need for explicit cleanup scripts.
- Reserve `AFTER_TEST_METHOD`-phased cleanup scripts for tests that intentionally forgo `@Transactional` rollback (because they need to verify genuinely committed behavior) — without automatic rollback as a safety net, explicit cleanup becomes the test author's responsibility again.
