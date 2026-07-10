---
card: spring-framework
gi: 429
slug: testng-support
title: "TestNG support"
---

## 1. What it is

Spring provides TestNG integration through `AbstractTestNGSpringContextTests` (and `AbstractTransactionalTestNGSpringContextTests` for transactional tests) — base classes a TestNG test extends, rather than an annotation-driven `@RunWith`/`@ExtendWith` mechanism, since TestNG's own extensibility model is built around inheritance and listeners differently than JUnit's. Underneath, it drives the exact same `TestContextManager` and `TestExecutionListener` chain that `SpringRunner` (JUnit 4) and `SpringExtension` (JUnit 5) use.

```java
@ContextConfiguration(classes = AppConfig.class)
public class OrderServiceTest extends AbstractTestNGSpringContextTests {
    @Autowired OrderService orderService; // injected via TestContextManager, same as JUnit

    @Test
    public void processesOrder() { ... }
}
```

## 2. Why & when

TestNG is a JUnit alternative popular in some organizations and legacy codebases, offering built-in features JUnit historically lacked (native test grouping, more flexible dependency-between-tests declarations, built-in parallel execution config). Spring's core testing value — real wiring, transaction management, context caching — is independent of which test framework you're using, so Spring provides an equivalent integration point for TestNG users, built on the identical underlying TestContext Framework covered throughout this section.

You'll use Spring's TestNG support when:

- Your project or organization has standardized on TestNG rather than JUnit, for its grouping, parameterization, or parallel-execution features.
- Maintaining an existing TestNG-based test suite that needs Spring context management, dependency injection, or transactional test support.

If you're starting a new project with no existing TestNG investment, JUnit 5 with `SpringExtension` (the previous cards) is the more common and better-documented path in the current Spring ecosystem — but understanding this integration matters for teams already committed to TestNG.

## 3. Core concept

```
 class OrderServiceTest extends AbstractTestNGSpringContextTests {
     @Autowired OrderService orderService;
     @Test public void ... { }
 }
        |
        v
 AbstractTestNGSpringContextTests implements TestNG's
 lifecycle interfaces (@BeforeClass, @BeforeMethod, etc.)
        |
        | internally delegates to
        v
 TestContextManager   <-- SAME class SpringRunner and SpringExtension use
        |
        v
 chain of TestExecutionListeners (DependencyInjection, Transactional, SqlScripts, ...)
```

`AbstractTestNGSpringContextTests` is functionally the TestNG-flavored sibling of `SpringRunner`/`SpringExtension` — a different integration surface (base class vs. runner vs. extension) wired into the identical underlying machinery.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three different test-framework integration surfaces all drive the same TestContextManager">
  <rect x="10" y="15" width="180" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="100" y="39" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JUnit 4: SpringRunner</text>

  <rect x="10" y="65" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="100" y="89" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JUnit 5: SpringExtension</text>

  <rect x="10" y="115" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="100" y="139" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">TestNG: AbstractTestNGSpringContextTests</text>

  <rect x="380" y="70" width="230" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">TestContextManager</text>

  <line x1="190" y1="35" x2="375" y2="80" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="190" y1="85" x2="375" y2="92" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="190" y1="135" x2="375" y2="105" stroke="#8b949e" stroke-width="1.2"/>
</svg>

All three test-framework integrations converge on identical Spring-side behavior.

## 5. Runnable example

### Level 1 — Basic

A minimal TestNG-based Spring test extending `AbstractTestNGSpringContextTests`, showing the same `@Autowired` injection seen throughout this section, now driven by TestNG rather than JUnit.

```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.testng.AbstractTestNGSpringContextTests;
import org.testng.annotations.Test;

public class TestNgBasic {

    static class GreetingService { String greet(String name) { return "Hello, " + name; } }

    @Configuration
    static class Config {
        @Bean GreetingService greetingService() { return new GreetingService(); }
    }

    @ContextConfiguration(classes = Config.class)
    public static class GreetingServiceTest extends AbstractTestNGSpringContextTests {
        @Autowired
        GreetingService greetingService;

        @Test
        public void greetsByName() {
            String result = greetingService.greet("Ada");
            System.out.println("TestNG result: " + result);
            if (!result.equals("Hello, Ada")) throw new AssertionError("Unexpected: " + result);
            System.out.println("greetsByName -- PASS");
        }
    }

    public static void main(String[] args) {
        // Simulating what a TestNG runner does when it executes this class.
        org.testng.TestNG testng = new org.testng.TestNG();
        testng.setTestClasses(new Class[]{GreetingServiceTest.class});
        testng.run();
    }
}
```

How to run: add `spring-test`, `spring-context`, and `org.testng:testng` to the classpath, then `java TestNgBasic.java`.

Extending `AbstractTestNGSpringContextTests` is the entire integration point — no `@RunWith` or `@ExtendWith` needed, since TestNG's extensibility model is inheritance-based. `@ContextConfiguration(classes = Config.class)` works identically to how it's used with JUnit, since it's the same core annotation processed by the same `TestContextManager`.

### Level 2 — Intermediate

`AbstractTransactionalTestNGSpringContextTests` for automatic `@Transactional` rollback behavior — the TestNG equivalent of the JUnit `@Transactional` test class pattern from the transaction-management-in-tests card, plus TestNG's native test grouping feature used to separate fast and slow tests.

```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.testng.AbstractTransactionalTestNGSpringContextTests;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.testng.annotations.Test;

import javax.sql.DataSource;

public class TestNgIntermediate {

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
        @Bean JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
        @Bean PlatformTransactionManager transactionManager(DataSource ds) { return new DataSourceTransactionManager(ds); }
    }

    @ContextConfiguration(classes = Config.class)
    // Extending the "Transactional" variant means every @Test method automatically rolls back,
    // without needing a separate @Transactional annotation -- the base class already implies it.
    public static class OrderInsertTest extends AbstractTransactionalTestNGSpringContextTests {
        @Autowired
        JdbcTemplate jdbcTemplate;

        @Test(groups = "fast")
        public void insertVisibleWithinTest() {
            jdbcTemplate.update("INSERT INTO orders VALUES (1, 'PENDING')");
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);
            System.out.println("Count within TestNG transactional test: " + count);
            if (count != 1) throw new AssertionError("Expected 1");
        }

        @Test(groups = "fast", dependsOnMethods = "insertVisibleWithinTest") // TestNG-native test ordering
        public void previousInsertShouldBeGone() {
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);
            System.out.println("Count in next TestNG test method: " + count);
            if (count != 0) throw new AssertionError("Expected rollback to have cleaned up, got " + count);
            System.out.println("Confirmed: automatic rollback under TestNG -- PASS");
        }
    }

    public static void main(String[] args) {
        org.testng.TestNG testng = new org.testng.TestNG();
        testng.setTestClasses(new Class[]{OrderInsertTest.class});
        testng.run();
    }
}
```

How to run: add `spring-test`, `spring-context`, `spring-jdbc`, `spring-tx`, `com.h2database:h2`, and `org.testng:testng` to the classpath, with `orders-schema.sql` on the classpath; then `java TestNgIntermediate.java`.

`AbstractTransactionalTestNGSpringContextTests` (rather than the plain `AbstractTestNGSpringContextTests`) bakes in transactional test rollback automatically, without a separate `@Transactional` annotation needed — a slightly different convention than JUnit's approach, where `@Transactional` is always explicit. `@Test(groups = "fast", dependsOnMethods = "...")` uses TestNG's native grouping and inter-test dependency declaration — a capability with no direct JUnit 5 equivalent, historically one of TestNG's distinguishing features.

### Level 3 — Advanced

Combine TestNG's parameterized testing (`@Factory`/`@DataProvider`) with Spring-managed dependency injection — verifying business logic across multiple input scenarios while still exercising real, injected Spring beans, showcasing a TestNG-specific capability alongside Spring's context management.

```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.testng.AbstractTestNGSpringContextTests;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

public class TestNgAdvanced {

    static class DiscountCalculator {
        double apply(double amount, double rate) {
            if (rate < 0 || rate > 1) throw new IllegalArgumentException("rate must be 0..1");
            return amount * (1 - rate);
        }
    }

    @Configuration
    static class Config {
        @Bean DiscountCalculator discountCalculator() { return new DiscountCalculator(); }
    }

    @ContextConfiguration(classes = Config.class)
    public static class DiscountCalculatorTest extends AbstractTestNGSpringContextTests {
        @Autowired
        DiscountCalculator discountCalculator; // the SAME injected bean used across every data-provided case

        @DataProvider(name = "discountScenarios")
        public Object[][] discountScenarios() {
            return new Object[][]{
                    {100.0, 0.10, 90.0},
                    {200.0, 0.25, 150.0},
                    {50.0, 0.0, 50.0},
                    {80.0, 1.0, 0.0},
            };
        }

        @Test(dataProvider = "discountScenarios")
        public void appliesDiscountAcrossScenarios(double amount, double rate, double expected) {
            double result = discountCalculator.apply(amount, rate);
            System.out.println("apply(" + amount + ", " + rate + ") = " + result + " (expected " + expected + ")");
            if (Math.abs(result - expected) > 0.001) {
                throw new AssertionError("Mismatch for amount=" + amount + " rate=" + rate);
            }
        }

        @Test(expectedExceptions = IllegalArgumentException.class)
        public void rejectsOutOfRangeRate() {
            discountCalculator.apply(100.0, 1.5); // TestNG's expectedExceptions, no try/catch needed
        }
    }

    public static void main(String[] args) {
        org.testng.TestNG testng = new org.testng.TestNG();
        testng.setTestClasses(new Class[]{DiscountCalculatorTest.class});
        testng.run();
        System.out.println("All data-provided scenarios and the exception case ran against ONE shared, "
                + "context-cached DiscountCalculator bean.");
    }
}
```

How to run: same dependencies as Level 1, then `java TestNgAdvanced.java`.

`@DataProvider` + `@Test(dataProvider = "discountScenarios")` runs `appliesDiscountAcrossScenarios` once per row in the returned `Object[][]`, each time against the *same* Spring-injected `discountCalculator` field — TestNG's native parameterization mechanism, distinct from JUnit 5's separate `@ParameterizedTest` extension, composed here directly with Spring's dependency injection with no extra glue code. `@Test(expectedExceptions = ...)` is TestNG's declarative exception-expectation syntax, an alternative to JUnit 5's `assertThrows(...)` or a manual `try/catch`.

## 6. Walkthrough

Trace `TestNgAdvanced.DiscountCalculatorTest`'s execution across its data-provided scenarios:

1. **Context built once.** When TestNG first runs any `@Test` method in `DiscountCalculatorTest`, Spring's `TestContextManager` (invoked via the inherited `AbstractTestNGSpringContextTests` lifecycle hooks) builds the `ApplicationContext` from `Config` and injects `discountCalculator` into the test instance.
2. **`@DataProvider` supplies rows.** TestNG calls `discountScenarios()`, receiving a `4x3` array of `{amount, rate, expected}` triples.
3. **`appliesDiscountAcrossScenarios` runs four times**, once per row, each invocation receiving that row's three values as method parameters — TestNG handles this looping and parameter-binding natively, without any Spring involvement in the parameterization itself.
4. **Each invocation calls the same injected bean.** `discountCalculator.apply(amount, rate)` is called against the identical `DiscountCalculator` instance every time — since Spring's context caching (from the earlier card) means the bean is a singleton built once and reused, not reconstructed per data row.
5. **Assertion per row.** Each invocation independently compares its computed `result` against that row's `expected` value, failing (and being reported by TestNG) individually if a specific scenario's math is wrong, without affecting the other three scenarios.
6. **Exception-case test runs separately.** `rejectsOutOfRangeRate()` calls `discountCalculator.apply(100.0, 1.5)` — the same injected bean once more — and TestNG's `expectedExceptions = IllegalArgumentException.class` attribute means the test *passes* specifically because that exception was thrown; if no exception (or a different one) had been thrown, TestNG would report this test as failed.

```
Context built once (Spring, via AbstractTestNGSpringContextTests)
   discountCalculator injected

@DataProvider discountScenarios() -> 4 rows

appliesDiscountAcrossScenarios(100.0, 0.10, 90.0)  -> uses SAME discountCalculator -> PASS
appliesDiscountAcrossScenarios(200.0, 0.25, 150.0) -> uses SAME discountCalculator -> PASS
appliesDiscountAcrossScenarios(50.0, 0.0, 50.0)    -> uses SAME discountCalculator -> PASS
appliesDiscountAcrossScenarios(80.0, 1.0, 0.0)     -> uses SAME discountCalculator -> PASS

rejectsOutOfRangeRate() -> apply(100.0, 1.5) -> throws IllegalArgumentException -> expectedExceptions matches -> PASS
```

## 7. Gotchas & takeaways

> Gotcha: `AbstractTransactionalTestNGSpringContextTests` bakes in transactional rollback implicitly (by extending it, every test method behaves as if `@Transactional`), which differs from JUnit's convention of always requiring an explicit `@Transactional` annotation — a team maintaining both JUnit and TestNG test suites side by side needs to remember this asymmetry, since a TestNG test extending the transactional base class rolls back automatically with no annotation visibly signaling that behavior to a reader skimming the code.

- Spring's TestNG support (`AbstractTestNGSpringContextTests`/`AbstractTransactionalTestNGSpringContextTests`) drives the identical underlying `TestContextManager`/`TestExecutionListener` machinery as `SpringRunner` (JUnit 4) and `SpringExtension` (JUnit 5) — the same context caching, dependency injection, and transactional behavior apply regardless of test framework.
- The integration surface differs by design: inheritance (TestNG's base classes) versus a runner (JUnit 4) versus an extension (JUnit 5) — reflecting each framework's own native extensibility model, not a difference in Spring's actual behavior.
- TestNG-native features (`@DataProvider` parameterization, `groups`/`dependsOnMethods` test ordering, `expectedExceptions`) compose directly with Spring-injected beans, since Spring's context management operates independently of TestNG's own test-execution features.
- For new projects without existing TestNG investment, JUnit 5 with `SpringExtension` remains the more common and better-supported path in the current Spring ecosystem.
