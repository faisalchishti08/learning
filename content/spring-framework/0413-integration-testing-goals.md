---
card: spring-framework
gi: 413
slug: integration-testing-goals
title: "Integration testing goals"
---

## 1. What it is

Integration testing goals are the specific set of things a Spring integration test is meant to verify that a unit test structurally cannot: that beans are wired together correctly, that configuration (property placeholders, profiles, conditional beans) resolves the way you expect, that a repository's queries actually work against a real database schema, and that cross-cutting concerns (`@Transactional`, `@Cacheable`, security) apply where you think they do. Naming these goals explicitly is what keeps integration tests focused, rather than sprawling into slow re-tests of logic a unit test already covers.

```java
@SpringJUnitConfig(AppConfig.class)
class OrderRepositoryIntegrationTest {
    @Autowired OrderRepository repository; // verifies real wiring + real query behavior
}
```

## 2. Why & when

It's tempting to treat "integration test" as simply "a test that loads Spring" and then let it re-verify everything a unit test already checked, just slower. That wastes the expense of loading a real context without buying anything a cheaper unit test didn't already provide. Being explicit about what integration tests are *for* — wiring correctness, configuration correctness, real query correctness, cross-cutting-concern correctness — keeps them focused on the failure modes that only a real `ApplicationContext` can catch, and keeps the rest of your business-logic testing at the faster unit-test layer covered in the philosophy and mocking cards.

The concrete goals, and the failure each one catches that unit tests cannot:

- **Wiring correctness** — does the `ApplicationContext` even start? A missing `@Bean`, a circular dependency, or an unsatisfied `@Autowired` fails here, never in a unit test where dependencies are just passed to a constructor by hand.
- **Configuration correctness** — do `@Value` placeholders resolve to the right values, does a `@Profile`-gated bean activate under the right profile, does a `@ConditionalOnProperty` bean appear or not as expected?
- **Real query/persistence correctness** — does a Spring Data repository's derived query, or a `@Query` annotation, actually produce the SQL you think it does against a real (if embedded) schema?
- **Cross-cutting concern correctness** — does `@Transactional` actually roll back on the exception you expect, does `@Cacheable` actually cache, does a security rule actually block or allow the request?

## 3. Core concept

```
        Question a test needs to answer         Right test layer
        -----------------------------------     -----------------
        Is this calculation correct?             Unit test (no Spring)
        Does this service call its dependency
          with the right arguments?              Unit test (with mocks)
        Does the ApplicationContext even start?  Integration test
        Does @Value("${x}") resolve correctly?   Integration test
        Does this repository query actually
          return the right rows?                 Integration test
        Does @Transactional roll back correctly? Integration test
        Does the whole HTTP request/response
          contract work end-to-end?              End-to-end test
```

Each row is a distinct question with a distinct minimum-cost test layer that can actually answer it — picking a layer more expensive than the question requires wastes test-suite time; picking one cheaper than the question requires leaves a real bug uncaught.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four integration testing goals mapped to the specific failure each one catches">
  <rect x="10" y="20" width="145" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="82" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Wiring</text>
  <text x="82" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">context starts?</text>

  <rect x="170" y="20" width="145" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="242" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Configuration</text>
  <text x="242" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Value, @Profile</text>

  <rect x="330" y="20" width="145" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="402" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Persistence</text>
  <text x="402" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">real query results</text>

  <rect x="490" y="20" width="145" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="562" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Cross-cutting</text>
  <text x="562" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Transactional, caching</text>
</svg>

Four distinct, nameable goals — each maps to a real class of bug that only shows up when Spring's real machinery runs.

## 5. Runnable example

### Level 1 — Basic

An integration test targeting exactly one goal — wiring correctness — deliberately introducing a wiring bug (a missing bean) to show what this class of test catches that no unit test would.

```java
import org.springframework.beans.factory.NoSuchBeanDefinitionException;
import org.springframework.context.annotation.*;

public class IntegrationGoalsBasic {

    interface PaymentGateway { void charge(double amount); }

    static class OrderService {
        private final PaymentGateway paymentGateway;
        OrderService(PaymentGateway paymentGateway) { this.paymentGateway = paymentGateway; }
    }

    @Configuration
    static class BrokenConfig {
        @Bean
        OrderService orderService(PaymentGateway paymentGateway) { // needs a PaymentGateway bean
            return new OrderService(paymentGateway);
        }
        // BUG: no @Bean method producing a PaymentGateway -- wiring will fail
    }

    public static void main(String[] args) {
        try {
            var context = new AnnotationConfigApplicationContext(BrokenConfig.class);
            context.getBean(OrderService.class);
            throw new AssertionError("Expected context startup to fail");
        } catch (org.springframework.beans.factory.UnsatisfiedDependencyException e) {
            System.out.println("Correctly caught wiring failure: " + e.getMessage().split("\n")[0]);
            System.out.println("A unit test constructing OrderService by hand would NEVER catch this.");
        }
    }
}
```

How to run: add `spring-context` to the classpath, then `java IntegrationGoalsBasic.java`.

A unit test for `OrderService` would simply pass a hand-built (or mocked) `PaymentGateway` to its constructor directly — it would pass regardless of whether `BrokenConfig` correctly defines a `PaymentGateway` bean, because a unit test never asks Spring to do the wiring at all. Only actually starting the `ApplicationContext`, as this integration-goal test does, surfaces the missing-bean configuration error.

### Level 2 — Intermediate

Target configuration correctness: verify a `@Value`-injected property resolves as expected, and that a `@Profile`-gated bean only appears under the right profile — both classes of bug invisible to a unit test that never loads real Spring configuration.

```java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.core.env.StandardEnvironment;

public class IntegrationGoalsIntermediate {

    static class RetryPolicy {
        @Value("${retry.maxAttempts:3}")
        int maxAttempts;
    }

    interface Notifier { String describe(); }

    @Configuration
    static class Config {
        @Bean
        RetryPolicy retryPolicy() { return new RetryPolicy(); }

        @Bean
        @Profile("prod")
        Notifier prodNotifier() { return () -> "sends real emails via SES"; }

        @Bean
        @Profile("!prod")
        Notifier devNotifier() { return () -> "logs to console only"; }
    }

    public static void main(String[] args) {
        // Goal: verify property resolution.
        var propsContext = new AnnotationConfigApplicationContext();
        propsContext.getEnvironment().getPropertySources().addFirst(
                new org.springframework.core.env.MapPropertySource("test",
                        java.util.Map.of("retry.maxAttempts", "5")));
        propsContext.register(Config.class);
        propsContext.refresh();

        RetryPolicy policy = propsContext.getBean(RetryPolicy.class);
        System.out.println("retry.maxAttempts resolved to: " + policy.maxAttempts);
        if (policy.maxAttempts != 5) throw new AssertionError("Expected 5");
        System.out.println("Property resolution correct -- PASS");
        propsContext.close();

        // Goal: verify profile-gated bean selection.
        var devContext = new AnnotationConfigApplicationContext();
        devContext.getEnvironment().setActiveProfiles("local"); // NOT "prod"
        devContext.register(Config.class);
        devContext.refresh();

        Notifier notifier = devContext.getBean(Notifier.class);
        System.out.println("Active notifier under 'local' profile: " + notifier.describe());
        if (!notifier.describe().contains("console")) throw new AssertionError("Expected dev notifier");
        System.out.println("Profile-gated bean selection correct -- PASS");
        devContext.close();
    }
}
```

How to run: add `spring-context` to the classpath, then `java IntegrationGoalsIntermediate.java`.

Neither of these bugs (a wrong default value, an inverted `@Profile` condition) would be visible to a unit test — `RetryPolicy.maxAttempts` would simply be whatever a unit test's `new RetryPolicy()` leaves it as (`0`, since `@Value` never runs outside a container), and directly instantiating `new DevNotifier()` in a unit test would never exercise the `@Profile("!prod")` condition at all. Only a real `ApplicationContext`, with real property sources and real active profiles, can verify either.

### Level 3 — Advanced

Target cross-cutting-concern correctness: verify `@Transactional` actually rolls back on a runtime exception, against a real (embedded) database — the class of bug where the annotation is present but subtly misapplied (e.g., on a private method, or catching-and-swallowing the exception before it propagates) and only a genuine transactional integration test would catch it.

```java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;

public class IntegrationGoalsAdvanced {

    static class InventoryService {
        private final JdbcTemplate jdbcTemplate;
        InventoryService(JdbcTemplate jdbcTemplate) { this.jdbcTemplate = jdbcTemplate; }

        @Transactional
        void reserveStock(long productId, int quantity) {
            jdbcTemplate.update("UPDATE stock SET reserved = reserved + ? WHERE product_id = ?", quantity, productId);
            int available = jdbcTemplate.queryForObject(
                    "SELECT quantity - reserved FROM stock WHERE product_id = ?", Integer.class, productId);
            if (available < 0) {
                throw new IllegalStateException("Insufficient stock for product " + productId);
                // If @Transactional weren't correctly applied here, the UPDATE above
                // would still be committed despite this failure -- exactly the bug
                // this integration test exists to catch.
            }
        }
    }

    @Configuration
    @EnableTransactionManagement
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:stock-schema.sql") // CREATE TABLE stock(product_id BIGINT, quantity INT, reserved INT)
                    .build();
        }

        @Bean
        JdbcTemplate jdbcTemplate(DataSource dataSource) { return new JdbcTemplate(dataSource); }

        @Bean
        PlatformTransactionManager transactionManager(DataSource dataSource) {
            return new DataSourceTransactionManager(dataSource);
        }

        @Bean
        InventoryService inventoryService(JdbcTemplate jdbcTemplate) { return new InventoryService(jdbcTemplate); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(Config.class);
        JdbcTemplate jdbcTemplate = context.getBean(JdbcTemplate.class);
        InventoryService service = context.getBean(InventoryService.class);

        jdbcTemplate.update("INSERT INTO stock(product_id, quantity, reserved) VALUES (1, 5, 0)");

        try {
            service.reserveStock(1, 10); // more than available -- should throw AND roll back
            throw new AssertionError("Expected IllegalStateException");
        } catch (IllegalStateException e) {
            System.out.println("reserveStock correctly threw: " + e.getMessage());
        }

        Integer reserved = jdbcTemplate.queryForObject(
                "SELECT reserved FROM stock WHERE product_id = 1", Integer.class);
        System.out.println("Reserved count after failed attempt: " + reserved);
        if (reserved != 0) throw new AssertionError("Expected rollback to leave reserved at 0, was " + reserved);
        System.out.println("@Transactional correctly rolled back the UPDATE -- PASS");

        context.close();
    }
}
```

How to run: add `spring-context`, `spring-jdbc`, `spring-tx`, and `com.h2database:h2` to the classpath, with a `stock-schema.sql` on the classpath defining the `stock` table; then `java IntegrationGoalsAdvanced.java`.

This test's entire point is verifying something that requires a real transaction manager and a real database connection: that when `reserveStock` throws after already running an `UPDATE`, the transactional proxy genuinely rolls that `UPDATE` back rather than leaving a partial, inconsistent write committed. A unit test mocking `JdbcTemplate` could verify `update` was *called*, but could never verify that a real transaction boundary actually reverted its effects — that's specifically a cross-cutting-concern correctness goal only an integration test can address.

## 6. Walkthrough

Trace `IntegrationGoalsAdvanced.main`'s failing call, `service.reserveStock(1, 10)`:

1. **Transactional proxy intercepts the call.** Because `InventoryService` is a Spring-managed bean and `reserveStock` is `@Transactional`, calling it doesn't run the method body directly — a proxy begins a new database transaction first.
2. **UPDATE executes.** `jdbcTemplate.update("UPDATE stock SET reserved = reserved + 10 ...")` runs inside that transaction, setting `reserved` to `10` in the (not-yet-committed) transactional view of the data.
3. **Availability check.** The subsequent `SELECT quantity - reserved` query, still inside the same transaction, sees its own uncommitted `UPDATE` (5 - 10 = -5), so `available` is `-5`.
4. **Exception thrown.** Since `available < 0`, `reserveStock` throws `IllegalStateException`.
5. **Proxy catches the exception.** The transactional proxy wrapping `reserveStock` sees the `IllegalStateException` propagate out of the method body. Because `IllegalStateException` is an unchecked exception and no custom rollback rules were configured, Spring's default `@Transactional` behavior is to mark the transaction for rollback.
6. **Rollback executes.** Instead of committing, the transaction manager issues a database `ROLLBACK` — the `UPDATE` from step 2 is entirely undone, as if it had never happened.
7. **Exception re-thrown to caller.** The proxy re-throws the original `IllegalStateException` out to `main`'s `try/catch`, which catches it and prints the confirmation message.
8. **Verification query.** A fresh `SELECT reserved FROM stock WHERE product_id = 1` — outside the failed transaction, in its own new implicit transaction — reads `reserved = 0`, proving the rollback genuinely reverted the database to its pre-call state.

```
reserveStock(1, 10)
   -> @Transactional proxy: BEGIN
   -> UPDATE stock SET reserved = reserved + 10   (uncommitted)
   -> SELECT quantity - reserved -> -5
   -> available < 0 -> throw IllegalStateException
   -> proxy: ROLLBACK (undoes the UPDATE)
   -> exception re-thrown to caller
verification: SELECT reserved -> 0  (confirms rollback worked)
```

## 7. Gotchas & takeaways

> Gotcha: it's easy to write an integration test that *looks* like it's testing wiring, configuration, persistence, or transactional correctness but actually only re-tests business logic a unit test already covers — for example, asserting `available < 0` triggers an exception is a business-logic assertion (belongs in a unit test with a mocked `JdbcTemplate`), while asserting the *database row was actually rolled back* is the genuine integration-testing goal. Before writing an integration test, ask specifically which of the four goals (wiring, configuration, persistence, cross-cutting concerns) it's targeting — if the answer is "none of them," it likely belongs at a cheaper test layer instead.

- Integration tests exist to verify what only a real `ApplicationContext` can verify: wiring, configuration resolution, real query behavior, and cross-cutting concerns like transactions and caching.
- A unit test mocking a dependency can never catch a wiring bug, a misconfigured property, a broken query, or a misapplied `@Transactional` — these require the real container machinery running.
- Keep integration tests focused on one of these explicit goals rather than letting them redundantly re-verify business logic a faster unit test already covers.
- The next cards in this section (TestContext Framework, context caching, transaction management in tests) are the tooling that makes writing plenty of goal-focused integration tests fast enough to actually do.
