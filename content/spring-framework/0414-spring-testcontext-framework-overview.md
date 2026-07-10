---
card: spring-framework
gi: 414
slug: spring-testcontext-framework-overview
title: "Spring TestContext Framework overview"
---

## 1. What it is

The Spring TestContext Framework is the infrastructure that makes JUnit (or TestNG) tests Spring-aware: it loads and manages an `ApplicationContext` for a test class, injects dependencies into test fields via `@Autowired`, manages transactions around test methods, and caches contexts across tests so repeated test classes with identical configuration don't each pay the cost of a fresh context. `@ExtendWith(SpringExtension.class)` (or the shorthand `@SpringJUnitConfig`) is the entry point that wires a test class into this infrastructure.

```java
@SpringJUnitConfig(AppConfig.class)
class OrderServiceIntegrationTest {
    @Autowired OrderService orderService; // injected by the TestContext Framework

    @Test
    void processesOrder() {
        orderService.process(new Order(1, 100.0));
    }
}
```

## 2. Why & when

Without this framework, an integration test would need to manually build an `ApplicationContext` in a `@BeforeEach`/`@BeforeAll` method, manually pull beans out of it, and manually manage cleanup — tedious, and easy to get subtly wrong (forgetting to close a context, rebuilding an identical context for every single test method unnecessarily). The TestContext Framework standardizes all of that: declare which configuration to load via an annotation, declare which fields to inject via `@Autowired`, and let the framework handle context lifecycle, injection, and — critically — caching, so an entire test class (or even multiple test classes sharing identical configuration) can reuse one already-loaded context instead of rebuilding it per test method.

This is the mechanism underneath essentially every Spring integration test you'll write, whether directly (`@SpringJUnitConfig` in plain Spring Framework projects) or indirectly (`@SpringBootTest` in Spring Boot projects, which is built on the same TestContext Framework underneath). Understanding it explains:

- Why `@Autowired` fields in a test class get populated at all — it's the framework's `DependencyInjectionTestExecutionListener` doing that work before each test method runs.
- Why running many test classes with the same `@ContextConfiguration` is much faster than the naive "one context per test method" approach would suggest — context caching (covered in its own card) is a first-class feature here, not an incidental optimization.
- Why some test annotations (`@Transactional`, `@Sql`, `@DirtiesContext`) behave the way they do — they're all `TestExecutionListener` implementations plugged into this same framework.

## 3. Core concept

```
  @SpringJUnitConfig(AppConfig.class)
  class MyTest {
        |
        v
  SpringExtension (JUnit 5 extension) hooks into the test lifecycle
        |
        v
  TestContextManager  -- orchestrates a chain of TestExecutionListeners:
        |
        +-- DependencyInjectionTestExecutionListener  (populates @Autowired fields)
        +-- TransactionalTestExecutionListener        (wraps @Transactional test methods)
        +-- SqlScriptsTestExecutionListener            (runs @Sql scripts before/after)
        +-- ... (more listeners, each handling one concern)
        |
        v
  Context loaded (or reused from cache) via a ContextLoader,
  keyed by the exact configuration (classes, profiles, property sources, ...)
```

The framework itself doesn't know about transactions, SQL scripts, or dependency injection directly — it's a pluggable pipeline of `TestExecutionListener`s, each contributing one piece of test lifecycle behavior, composed together by the `TestContextManager`.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TestContextManager runs a chain of listeners around a cached ApplicationContext for each test method">
  <rect x="10" y="20" width="180" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@SpringJUnitConfig test</text>

  <rect x="230" y="20" width="180" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">TestContextManager</text>

  <rect x="450" y="20" width="170" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="535" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Context cache (keyed)</text>

  <rect x="130" y="120" width="380" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">TestExecutionListeners (ordered chain)</text>
  <text x="320" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DependencyInjection -&gt; Transactional -&gt; SqlScripts -&gt; ...</text>

  <line x1="190" y1="42" x2="225" y2="42" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="42" x2="445" y2="42" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="320" y1="64" x2="320" y2="115" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The `TestContextManager` is the coordinator; the listener chain and the context cache are the two pieces of machinery it drives around every test method.

## 5. Runnable example

### Level 1 — Basic

A minimal `@SpringJUnitConfig` test showing `@Autowired` field injection into the test class itself — the most basic capability the TestContext Framework provides.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class TestContextBasic {

    static class GreetingService {
        String greet(String name) { return "Hello, " + name; }
    }

    @Configuration
    static class Config {
        @Bean
        GreetingService greetingService() { return new GreetingService(); }
    }

    @SpringJUnitConfig(Config.class)
    static class GreetingServiceTest {
        @Autowired
        GreetingService greetingService; // populated by the TestContext Framework, not by hand

        @Test
        void greetsByName() {
            String result = greetingService.greet("Ada");
            if (!result.equals("Hello, Ada")) throw new AssertionError("Unexpected: " + result);
            System.out.println("greetsByName -- PASS");
        }
    }

    public static void main(String[] args) {
        // Simulating what a JUnit 5 runner does: run the @Test method through the TestContext machinery.
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(GreetingServiceTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printTo(new java.io.PrintWriter(System.out));
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: add `spring-test`, `spring-context`, `org.junit.jupiter:junit-jupiter`, and `org.junit.platform:junit-platform-launcher` to the classpath, then `java TestContextBasic.java`. In a real project this test class would simply be run via `mvn test`/`gradle test` — the `main` method here exists only to make the example self-contained and runnable as one file.

`@SpringJUnitConfig(Config.class)` is shorthand for `@ExtendWith(SpringExtension.class)` plus `@ContextConfiguration(classes = Config.class)` — it tells the TestContext Framework which configuration to load. Before `greetsByName()` runs, the framework's `DependencyInjectionTestExecutionListener` sets the `greetingService` field, so the test method can use it directly without any manual context lookup.

### Level 2 — Intermediate

Two separate test classes with identical configuration, demonstrating that they share one cached context rather than each building their own — visible by printing from a `@Bean`'s constructor to show it only runs once across both test classes.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class TestContextIntermediate {

    static class ExpensiveResource {
        ExpensiveResource() {
            System.out.println("ExpensiveResource constructed (should happen ONCE, not per test class)");
        }
    }

    @Configuration
    static class SharedConfig {
        @Bean
        ExpensiveResource expensiveResource() { return new ExpensiveResource(); }
    }

    @SpringJUnitConfig(SharedConfig.class)
    static class FirstTest {
        @Autowired ExpensiveResource resource;

        @Test
        void usesResource() {
            System.out.println("FirstTest using: " + System.identityHashCode(resource));
        }
    }

    @SpringJUnitConfig(SharedConfig.class) // IDENTICAL configuration -- same cache key
    static class SecondTest {
        @Autowired ExpensiveResource resource;

        @Test
        void alsoUsesResource() {
            System.out.println("SecondTest using: " + System.identityHashCode(resource));
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(FirstTest.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(SecondTest.class))
                .build();
        launcher.execute(request);
        System.out.println("If both identityHashCodes above match, the context (and its bean) was cached and reused.");
    }
}
```

How to run: same dependencies as Level 1, then `java TestContextIntermediate.java`. Expect `"ExpensiveResource constructed"` to print exactly once, and both `identityHashCode` values printed by the two test classes to match.

Even though `FirstTest` and `SecondTest` are entirely separate classes, they declare identical configuration (`SharedConfig.class`), so the TestContext Framework's context cache recognizes this and reuses the exact same `ApplicationContext` — and therefore the exact same singleton `ExpensiveResource` bean instance — for both, rather than constructing it twice. The context caching card explores this mechanism and its cache-key rules in more depth.

### Level 3 — Advanced

A test class that combines multiple `TestExecutionListener`-backed features at once — `@Autowired` injection, `@Transactional` test methods (auto-rolled-back), and `@Sql` script execution — showing how the TestContext Framework composes several independent concerns around the same test method without any of them needing to know about each other.

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

public class TestContextAdvanced {

    @Configuration
    @EnableTransactionManagement
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:products-schema.sql") // CREATE TABLE products(id BIGINT, name VARCHAR(100))
                    .build();
        }

        @Bean
        JdbcTemplate jdbcTemplate(DataSource dataSource) { return new JdbcTemplate(dataSource); }

        @Bean
        PlatformTransactionManager transactionManager(DataSource dataSource) {
            return new DataSourceTransactionManager(dataSource);
        }
    }

    @SpringJUnitConfig(Config.class)
    @Transactional // every @Test method runs in a transaction rolled back afterward
    static class ProductQueryTest {
        @Autowired JdbcTemplate jdbcTemplate; // listener #1: dependency injection

        @Test
        @Sql("classpath:seed-products.sql")   // listener #2: runs before this specific test method
        void countsSeededProducts() {
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM products", Integer.class);
            System.out.println("Seeded product count: " + count);
            if (count != 2) throw new AssertionError("Expected 2 seeded products, got " + count);

            jdbcTemplate.update("INSERT INTO products VALUES (99, 'Temp')"); // will be rolled back
            System.out.println("countsSeededProducts -- PASS (this insert will be rolled back automatically)");
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
        System.out.println("Test run complete. The @Sql-inserted rows and the manual INSERT were both rolled back.");
    }
}
```

How to run: add `spring-test`, `spring-context`, `spring-jdbc`, `spring-tx`, `com.h2database:h2`, JUnit 5, and the JUnit Platform Launcher to the classpath, with `products-schema.sql` and `seed-products.sql` (inserting 2 rows) on the classpath, then `java TestContextAdvanced.java`.

Three independent `TestExecutionListener`s cooperate around `countsSeededProducts()` without any explicit coordination in the test code: `DependencyInjectionTestExecutionListener` populates `jdbcTemplate` before the method runs; `SqlScriptsTestExecutionListener` runs `seed-products.sql` (because of the method-level `@Sql`) inside the same transaction the class-level `@Transactional` started; `TransactionalTestExecutionListener` rolls that whole transaction back after the method completes — meaning both the seeded rows and the test's own manual `INSERT` disappear, leaving the database exactly as it was before the test ran, ready for the next test method with no manual cleanup code.

## 6. Walkthrough

Trace one execution of `TestContextAdvanced.ProductQueryTest.countsSeededProducts()`:

1. **Context resolution.** The `TestContextManager` for `ProductQueryTest` resolves its `@SpringJUnitConfig(Config.class)` configuration, checks the context cache for a match, and — on a cold run — builds a new `ApplicationContext` from `Config`, including the embedded H2 `DataSource`, `JdbcTemplate`, and `PlatformTransactionManager`.
2. **Dependency injection.** Before the test method runs, `DependencyInjectionTestExecutionListener` sets the `jdbcTemplate` field on the test instance from the now-loaded context.
3. **Transaction begins.** Because the class is annotated `@Transactional`, `TransactionalTestExecutionListener` starts a new database transaction before the test method executes — everything the method does to the database from here happens inside this one transaction.
4. **`@Sql` script runs.** `SqlScriptsTestExecutionListener` sees the method-level `@Sql("classpath:seed-products.sql")` and executes that script's `INSERT` statements — inside the same already-open transaction from step 3 — inserting the two seed rows.
5. **Test body executes.** `countsSeededProducts()` queries `SELECT COUNT(*) FROM products`, seeing the two seeded rows plus none of any other test's data (since each test method gets this same fresh-transaction treatment), asserts the count is `2`, then performs its own additional `INSERT`.
6. **Transaction rolled back.** After the method returns (successfully, in this case), `TransactionalTestExecutionListener`'s post-method hook issues a `ROLLBACK` rather than a `COMMIT` — undoing both the `@Sql` script's inserts and the test method's own manual insert in one stroke.
7. **Context remains cached.** The `ApplicationContext` itself is *not* torn down after the rollback — only the transaction is rolled back. The same context (and the same underlying `DataSource`/schema) is ready to be reused by the next test method or test class with matching configuration, per the context-caching behavior from Level 2.

```
ProductQueryTest.countsSeededProducts()
   TestContextManager: resolve context (cache hit or build)
   DependencyInjectionTestExecutionListener: inject jdbcTemplate
   TransactionalTestExecutionListener: BEGIN
   SqlScriptsTestExecutionListener: run seed-products.sql (2 rows inserted, in-transaction)
   test body: SELECT COUNT(*) -> 2 -> assert OK -> INSERT one more row
   TransactionalTestExecutionListener: ROLLBACK  (undoes both inserts)
   context stays cached for the next test
```

## 7. Gotchas & takeaways

> Gotcha: the order `TestExecutionListener`s run in matters and is largely fixed by the framework (dependency injection happens before transaction start, which happens before `@Sql` scripts run within that transaction, by default) — writing a test that assumes a different ordering (e.g., expecting `@Sql` data to be visible to a `@BeforeEach` method that runs *before* the transaction listener's "before test method" phase) can silently see stale or missing data. When ordering surprises come up, checking which listener owns which lifecycle phase (via the framework's documented default listener order) resolves the confusion faster than guessing.

- `@SpringJUnitConfig` (or its Spring Boot equivalent, `@SpringBootTest`) is the entry point into the TestContext Framework — it hooks a test class into a pipeline of independent `TestExecutionListener`s.
- Context caching is a first-class feature, not an incidental optimization — test classes with identical configuration automatically share one loaded context, which is why writing many small, focused integration test classes doesn't multiply your test suite's startup cost the way it might naively seem to.
- `@Autowired` field injection, `@Transactional` test rollback, and `@Sql` script execution are all implemented as separate, composable `TestExecutionListener`s — each contributes its piece independently, letting you mix and match features per test class.
- Because listeners compose, features "just work" together (transactional rollback undoing both `@Sql`-seeded and manually-inserted data) without you writing any glue code connecting them.
