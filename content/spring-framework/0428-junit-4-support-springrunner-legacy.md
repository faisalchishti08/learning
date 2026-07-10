---
card: spring-framework
gi: 428
slug: junit-4-support-springrunner-legacy
title: "JUnit 4 support (SpringRunner) [legacy]"
---

## 1. What it is

`SpringRunner` (and its older, deprecated-in-favor-of alias `SpringJUnit4ClassRunner`) is Spring's integration with JUnit 4's `Runner` SPI — the JUnit 4-era equivalent of `SpringExtension` from the previous card, wiring the same underlying TestContext Framework into JUnit 4's older, single-runner test execution model. It's explicitly legacy: relevant for maintaining older codebases still on JUnit 4, not for new test code.

```java
@RunWith(SpringRunner.class)              // JUnit 4's runner mechanism -- one runner per test class
@ContextConfiguration(classes = AppConfig.class)
public class OrderServiceTest {
    @Autowired OrderService orderService;

    @Test
    public void processesOrder() { ... }
}
```

## 2. Why & when

JUnit 4 predates JUnit 5's `Extension` SPI — its extensibility model is `@RunWith(SomeRunner.class)`, where exactly one `Runner` implementation controls a test class's entire execution. `SpringRunner` is Spring's implementation of that single-runner contract, and it's what every Spring test written before JUnit 5's widespread adoption (roughly pre-2018, though plenty of long-lived codebases still carry JUnit 4 tests) uses to get the same dependency injection, transaction management, and context caching covered throughout this section.

You'll encounter `SpringRunner` when:

- Maintaining an existing codebase with a substantial JUnit 4 test suite not yet migrated to JUnit 5 — understanding it is necessary to read, modify, and extend that existing test code correctly.
- Working with a dependency or testing library that still assumes JUnit 4's `Runner` model (increasingly rare, but not extinct).

For any new test code, use `SpringExtension`/`@SpringJUnitConfig` (JUnit 5) instead — `SpringRunner` is presented here specifically as legacy knowledge for reading and maintaining existing code, not as a recommended starting point. JUnit 4's single-runner limitation is itself a real constraint the JUnit 5 `Extension` model was designed to fix: `@RunWith` accepts exactly one runner class, meaning composing Spring's test support with, say, Mockito's own JUnit 4 runner on the same class required a special dual-purpose runner or JUnit 4's `@Rule` mechanism instead — the multi-extension composition Level 3 of the previous card demonstrated so simply under JUnit 5 was considerably more awkward under JUnit 4.

## 3. Core concept

```
 JUnit 4                                    JUnit 5
 --------                                   --------
 @RunWith(SpringRunner.class)               @ExtendWith(SpringExtension.class)
 (exactly ONE runner per class)             (MULTIPLE extensions composable)

 SpringRunner
        |
        v
 SpringJUnit4ClassRunner (implementation)
        |
        v
 TestContextManager                          TestContextManager
        |                                            |
        v                                            v
 same TestExecutionListener chain             same TestExecutionListener chain
 (DependencyInjection, Transactional, SqlScripts, ...)
```

Both `SpringRunner` and `SpringExtension` ultimately drive the exact same `TestContextManager`/`TestExecutionListener` machinery — the difference is entirely in which JUnit version's extensibility API each one implements, not in what Spring-side behavior they provide.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JUnit 4's SpringRunner and JUnit 5's SpringExtension both drive the same underlying TestContextManager">
  <rect x="10" y="20" width="180" height="44" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JUnit 4: SpringRunner</text>

  <rect x="10" y="120" width="180" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="147" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JUnit 5: SpringExtension</text>

  <rect x="380" y="70" width="230" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">TestContextManager</text>
  <text x="495" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same underlying behavior</text>

  <line x1="190" y1="42" x2="375" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="190" y1="142" x2="375" y2="102" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two different front doors into identical underlying test infrastructure.

## 5. Runnable example

### Level 1 — Basic

A minimal JUnit 4-style test using `SpringRunner`, showing the same `@Autowired` field injection behavior JUnit 5 examples throughout this section have demonstrated, just through JUnit 4's API.

```java
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringRunner;

public class SpringRunnerBasic {

    static class GreetingService { String greet(String name) { return "Hello, " + name; } }

    @Configuration
    static class Config {
        @Bean GreetingService greetingService() { return new GreetingService(); }
    }

    @RunWith(SpringRunner.class)
    @ContextConfiguration(classes = Config.class)
    public static class GreetingServiceTest {
        @Autowired
        public GreetingService greetingService; // JUnit 4 requires public fields for @RunWith-based tests

        @Test
        public void greetsByName() {
            String result = greetingService.greet("Ada");
            System.out.println("JUnit 4 SpringRunner result: " + result);
            if (!result.equals("Hello, Ada")) throw new AssertionError("Unexpected: " + result);
            System.out.println("greetsByName -- PASS");
        }
    }

    public static void main(String[] args) {
        // Simulating what JUnit 4's own runner infrastructure does when it executes a test class.
        org.junit.runner.JUnitCore core = new org.junit.runner.JUnitCore();
        org.junit.runner.Result result = core.run(GreetingServiceTest.class);
        System.out.println("Tests run: " + result.getRunCount() + ", failures: " + result.getFailureCount());
        result.getFailures().forEach(f -> System.out.println("FAILURE: " + f));
    }
}
```

How to run: add `spring-test`, `spring-context`, and `junit:junit:4.13.2` (JUnit 4) to the classpath, then `java SpringRunnerBasic.java`.

`@RunWith(SpringRunner.class)` is JUnit 4's single-runner declaration — it hands control of this test class's entire lifecycle to `SpringRunner`, which internally creates a `TestContextManager` and drives the same dependency-injection listener the JUnit 5 examples throughout this section relied on via `SpringExtension`. Note the `public` field requirement — a JUnit 4 convention not shared by JUnit 5, which permits package-private test classes and fields.

### Level 2 — Intermediate

`@Transactional` test rollback under JUnit 4's `SpringRunner` — confirming the exact same transactional test behavior from the transaction-management-in-tests card works identically, since it's the same `TransactionalTestExecutionListener` underneath regardless of which JUnit version drives it.

```java
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;

public class SpringRunnerIntermediate {

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

    @RunWith(SpringRunner.class)
    @ContextConfiguration(classes = Config.class)
    @Transactional
    public static class OrderInsertTest {
        @Autowired
        public JdbcTemplate jdbcTemplate;

        @Test
        public void insertVisibleWithinTest() {
            jdbcTemplate.update("INSERT INTO orders VALUES (1, 'PENDING')");
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);
            System.out.println("Count within JUnit 4 transactional test: " + count);
            if (count != 1) throw new AssertionError("Expected 1");
        }

        @Test
        public void previousTestsInsertShouldBeGone() {
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);
            System.out.println("Count in a separate test method, same JUnit 4 SpringRunner class: " + count);
            if (count != 0) throw new AssertionError("Expected rollback to have cleaned up, got " + count);
            System.out.println("Confirmed: same @Transactional rollback semantics under JUnit 4 -- PASS");
        }
    }

    public static void main(String[] args) {
        org.junit.runner.JUnitCore core = new org.junit.runner.JUnitCore();
        org.junit.runner.Result result = core.run(OrderInsertTest.class);
        System.out.println("Tests run: " + result.getRunCount() + ", failures: " + result.getFailureCount());
        result.getFailures().forEach(f -> System.out.println("FAILURE: " + f));
    }
}
```

How to run: add `spring-test`, `spring-context`, `spring-jdbc`, `spring-tx`, `com.h2database:h2`, and JUnit 4 to the classpath, with `orders-schema.sql` on the classpath; then `java SpringRunnerIntermediate.java`.

This test class's behavior is indistinguishable from the JUnit 5 `@Transactional` example in the transaction-management-in-tests card — same rollback semantics, same cross-method isolation — because `SpringRunner` and `SpringExtension` both delegate to the identical `TransactionalTestExecutionListener`. The only differences are surface-level JUnit 4 conventions: `@RunWith` instead of `@ExtendWith`, `public class`/`public void` method signatures, and `org.junit.Test` instead of `org.junit.jupiter.api.Test`.

### Level 3 — Advanced

Illustrate JUnit 4's single-runner limitation directly: combining Spring's test support with Mockito under JUnit 4 requires either giving up one framework's runner (using `@Rule`/`MockitoJUnit.rule()` instead of Mockito's own runner) or a dual-purpose runner — shown here using `MockitoJUnitRunner`'s rule-based alternative alongside `SpringRunner`, contrasted with how trivially this composed under JUnit 5's multi-extension model in the previous card.

```java
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnit;
import org.mockito.junit.MockitoRule;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Optional;

import static org.mockito.Mockito.when;

public class SpringRunnerAdvanced {

    record Order(long id, String status) {}
    interface OrderRepository { Optional<Order> findById(long id); }

    static class OrderService {
        private final OrderRepository repository;
        OrderService(OrderRepository repository) { this.repository = repository; }
        String describe(long id) { return repository.findById(id).map(Order::status).orElse("NOT_FOUND"); }
    }

    @Configuration
    static class Config {
        @Bean
        OrderRepository orderRepository() {
            return id -> { throw new UnsupportedOperationException("replaced by mock in this test"); };
        }
    }

    // JUnit 4 permits only ONE @RunWith -- SpringRunner is used here, and Mockito's participation
    // is added via @Rule instead of its own competing @RunWith(MockitoJUnitRunner.class).
    // (Contrast with JUnit 5's Level 3 example in the previous card: @ExtendWith accepts MULTIPLE values.)
    @RunWith(SpringRunner.class)
    @ContextConfiguration(classes = Config.class)
    public static class RuleBasedCombinationTest {
        @Rule
        public MockitoRule mockitoRule = MockitoJUnit.rule(); // Mockito's participation via @Rule, not @RunWith

        @Mock
        public OrderRepository mockRepository;

        @Autowired
        public ConfigurableApplicationContext context;

        @Test
        public void mockedRepositoryWorksAlongsideSpringContext() {
            when(mockRepository.findById(1L)).thenReturn(Optional.of(new Order(1, "SHIPPED")));

            OrderService orderService = new OrderService(mockRepository);
            String result = orderService.describe(1L);

            System.out.println("describe(1) = " + result);
            if (!"SHIPPED".equals(result)) throw new AssertionError("Expected SHIPPED, got " + result);
            System.out.println("mockedRepositoryWorksAlongsideSpringContext -- PASS");
            System.out.println("Spring context also available: " + (context != null));
        }
    }

    public static void main(String[] args) {
        org.junit.runner.JUnitCore core = new org.junit.runner.JUnitCore();
        org.junit.runner.Result result = core.run(RuleBasedCombinationTest.class);
        System.out.println("Tests run: " + result.getRunCount() + ", failures: " + result.getFailureCount());
        result.getFailures().forEach(f -> System.out.println("FAILURE: " + f));
    }
}
```

How to run: add `spring-test`, `spring-context`, `org.mockito:mockito-core`, and JUnit 4 to the classpath, then `java SpringRunnerAdvanced.java`.

`@Rule public MockitoRule mockitoRule = MockitoJUnit.rule()` is JUnit 4's `@Rule` mechanism — a different, older extensibility point than `@RunWith`, and one that *can* coexist with a single chosen runner (`SpringRunner`, here) since `@Rule` doesn't compete for the single-runner slot the way a second `@RunWith` would. This is measurably more ceremony than JUnit 5's `@ExtendWith(SpringExtension.class)` alongside `@ExtendWith(MockitoExtension.class)` from the previous card — a concrete illustration of why JUnit 5's multi-extension model was designed the way it was, and why new Spring test code should default to `SpringExtension` rather than `SpringRunner`.

## 6. Walkthrough

Trace `SpringRunnerAdvanced.RuleBasedCombinationTest.mockedRepositoryWorksAlongsideSpringContext()`:

1. **`SpringRunner` takes ownership of the class.** Because `@RunWith(SpringRunner.class)` is JUnit 4's single-runner declaration, `SpringRunner` controls this test class's entire execution — instantiating the test class, building the Spring `ApplicationContext` from `Config`, and driving the `TestContextManager`/listener chain exactly as `SpringExtension` would under JUnit 5.
2. **Spring's dependency injection runs.** As part of `SpringRunner`'s lifecycle handling, `@Autowired public ConfigurableApplicationContext context` is populated with the real, built Spring context.
3. **Mockito's `@Rule` activates independently.** `MockitoRule`, being a JUnit 4 `TestRule` (not a `Runner`), wraps around the already-runner-controlled test method execution — JUnit 4's rule mechanism allows multiple rules (and one runner) to layer around a test method, which is exactly how Mockito's `@Mock` field processing happens here without needing its own `@RunWith`.
4. **`mockRepository` is created and ready.** By the time the test method body runs, Mockito's rule has already processed the `@Mock` annotation and assigned a real Mockito mock to `mockRepository`.
5. **Test body: stubbing and use.** `when(mockRepository.findById(1L)).thenReturn(...)` configures the mock; `new OrderService(mockRepository)` builds a service directly against it (bypassing the Spring context's own `orderRepository` bean, similar to the manual-substitution pattern from the previous card's JUnit 5 example).
6. **Assertion.** `orderService.describe(1L)` returns `"SHIPPED"`, confirming the mock's stubbed behavior took effect — while `context` (Spring-injected) remains available and usable in the same test method, demonstrating both frameworks' contributions coexist correctly, just via a different composition mechanism (`@Rule` rather than a second `@RunWith` or `@ExtendWith`) than JUnit 5 offers.

```
JUnit 4 test class execution:
   SpringRunner (the ONE allowed @RunWith):
        builds ApplicationContext from Config
        injects @Autowired context
   MockitoRule (@Rule, layers around the runner-controlled method):
        processes @Mock -> mockRepository created

test body:
   stub mockRepository.findById(1L) -> Order(SHIPPED)
   new OrderService(mockRepository).describe(1L) -> "SHIPPED"
   assert result == "SHIPPED" -- PASS
   context (from SpringRunner) still available
```

## 7. Gotchas & takeaways

> Gotcha: JUnit 4 test classes and methods conventionally need to be `public` (unlike JUnit 5, which relaxed this requirement) — a common migration-era mistake is copying a JUnit 5-style package-private test class under `@RunWith(SpringRunner.class)` and having it silently fail to run at all (JUnit 4's discovery mechanism simply skips non-public test classes/methods rather than erroring loudly), rather than throwing a clear error explaining the visibility requirement.

- `SpringRunner` is JUnit 4's integration point into the exact same `TestContextManager`/`TestExecutionListener` machinery `SpringExtension` uses under JUnit 5 — the underlying Spring behavior (dependency injection, `@Transactional` rollback, `@Sql` scripts, context caching) is identical regardless of which one drives it.
- New test code should use `SpringExtension`/`@SpringJUnitConfig` (JUnit 5) — `SpringRunner` is presented here as legacy knowledge for reading and maintaining existing JUnit 4 codebases, not as a recommended starting point.
- JUnit 4's single-runner (`@RunWith`) model is a real limitation JUnit 5's multi-extension (`@ExtendWith`) model was specifically designed to fix — composing Spring's test support with another framework's JUnit integration is measurably more ceremony under JUnit 4 (via `@Rule`) than under JUnit 5 (via multiple `@ExtendWith` values).
- JUnit 4 conventionally requires `public` test classes and methods; JUnit 5 relaxed this — a common source of silent (non-erroring) test-discovery failures when migrating or mixing styles.
