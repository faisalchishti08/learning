---
card: spring-framework
gi: 430
slug: nested-test-classes
title: "@Nested test classes"
---

## 1. What it is

JUnit 5's `@Nested` lets you group related test methods into inner classes within a test class, and Spring's TestContext Framework fully supports this — a `@Nested` class inherits (or can override) its enclosing class's Spring configuration, letting you organize a large integration test suite by scenario or state while still sharing (or deliberately varying) the underlying `ApplicationContext`.

```java
@SpringJUnitConfig(Config.class)
class OrderServiceTest {
    @Autowired OrderService orderService;

    @Nested
    class WhenOrderIsPending {
        @Test void canBeCancelled() { ... }
    }

    @Nested
    class WhenOrderIsShipped {
        @Test void cannotBeCancelled() { ... }
    }
}
```

## 2. Why & when

A large integration test class covering many scenarios for one piece of functionality can become a long, flat list of test methods with unclear grouping — `testCancelWhenPending`, `testCancelWhenShipped`, `testCancelWhenAlreadyCancelled`, and so on, with the shared "cancel" context only conveyed through naming convention. `@Nested` classes let you express that grouping structurally: an outer class establishes shared setup and injected dependencies, and each `@Nested` inner class represents one scenario or state, with its own focused set of test methods and (optionally) its own additional setup specific to that scenario.

Reach for `@Nested` test organization when:

- A test class has natural groupings of scenarios (different starting states, different input categories) that would benefit from visual and structural separation, not just naming conventions.
- Different scenarios need different additional setup (different seed data, different mocked behavior) layered on top of shared outer-class configuration.
- You want test output (in an IDE or CI report) to reflect the grouping — `@Nested` classes render as a hierarchy in most JUnit 5-aware test reporters, making large suites easier to navigate.

## 3. Core concept

```
 @SpringJUnitConfig(Config.class)      <- outer class's configuration
 class OrderServiceTest {
     @Autowired OrderService orderService;   <- inherited by every @Nested class below

     @Nested
     class WhenOrderIsPending {
         // inherits OrderServiceTest's ApplicationContext and injected fields
         @Test void canBeCancelled() { ... }
     }

     @Nested
     @SpringJUnitConfig(DifferentConfig.class)  // a @Nested class CAN override configuration
     class WhenUsingAlternateGateway {
         @Test void behavesDifferently() { ... }
     }
 }
```

By default, a `@Nested` class inherits its enclosing class's `@ContextConfiguration`/`@SpringJUnitConfig` (and therefore shares the same cached context, per the context-caching card) — but it can declare its own configuration to override that inheritance when a specific scenario genuinely needs different beans or settings.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Outer test class configuration inherited by nested classes representing different scenarios">
  <rect x="200" y="15" width="240" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OrderServiceTest (outer)</text>

  <rect x="30" y="110" width="220" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Nested WhenOrderIsPending</text>
  <text x="140" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">inherits outer config</text>

  <rect x="390" y="110" width="220" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Nested WhenOrderIsShipped</text>
  <text x="500" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">inherits outer config</text>

  <line x1="280" y1="59" x2="150" y2="105" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="360" y1="59" x2="490" y2="105" stroke="#8b949e" stroke-width="1.5"/>
</svg>

Two focused scenario groupings, sharing (by default) the same underlying context as their enclosing class.

## 5. Runnable example

### Level 1 — Basic

An outer test class establishing shared injection, with two `@Nested` classes grouping scenario-specific tests — the most common `@Nested` usage pattern.

```java
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class NestedTestBasic {

    record Order(long id, String status) {}

    static class OrderService {
        boolean canCancel(Order order) { return !"SHIPPED".equals(order.status()); }
    }

    @Configuration
    static class Config {
        @Bean OrderService orderService() { return new OrderService(); }
    }

    @SpringJUnitConfig(Config.class)
    static class OrderServiceTest {
        @Autowired OrderService orderService; // shared by BOTH nested classes below

        @Nested
        class WhenOrderIsPending {
            @Test
            void canBeCancelled() {
                boolean result = orderService.canCancel(new Order(1, "PENDING"));
                System.out.println("Pending order canCancel: " + result);
                if (!result) throw new AssertionError("Expected pending orders to be cancellable");
                System.out.println("WhenOrderIsPending.canBeCancelled -- PASS");
            }
        }

        @Nested
        class WhenOrderIsShipped {
            @Test
            void cannotBeCancelled() {
                boolean result = orderService.canCancel(new Order(2, "SHIPPED"));
                System.out.println("Shipped order canCancel: " + result);
                if (result) throw new AssertionError("Expected shipped orders to NOT be cancellable");
                System.out.println("WhenOrderIsShipped.cannotBeCancelled -- PASS");
            }
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(OrderServiceTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: add `spring-test`, `spring-context`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java NestedTestBasic.java`.

Both `WhenOrderIsPending` and `WhenOrderIsShipped` access `orderService` — a field declared on the *outer* `OrderServiceTest` class — without redeclaring or re-injecting it; JUnit 5's `@Nested` inner classes have implicit access to their enclosing instance's fields, and Spring's dependency injection populated that field once on the outer instance. The test output structure (via most IDEs and JUnit 5-aware reporters) shows this grouping visually, distinguishing it from a flat list of `testCanBeCancelledWhenPending`/`testCannotBeCancelledWhenShipped` methods.

### Level 2 — Intermediate

A `@Nested` class overriding the outer class's configuration entirely — verifying behavior under a specific, different bean setup without affecting the outer class or its sibling `@Nested` classes.

```java
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class NestedTestIntermediate {

    interface PaymentGateway { String charge(double amount); }

    static class StandardGateway implements PaymentGateway {
        public String charge(double amount) { return "STANDARD-CHARGE-" + amount; }
    }

    static class SlowRetryingGateway implements PaymentGateway {
        public String charge(double amount) { return "RETRYING-CHARGE-" + amount; }
    }

    @Configuration
    static class DefaultConfig {
        @Bean PaymentGateway paymentGateway() { return new StandardGateway(); }
    }

    @Configuration
    static class SlowGatewayConfig {
        @Bean PaymentGateway paymentGateway() { return new SlowRetryingGateway(); }
    }

    @SpringJUnitConfig(DefaultConfig.class)
    static class PaymentTest {
        @Autowired PaymentGateway paymentGateway;

        @Test
        void usesStandardGatewayByDefault() {
            String result = paymentGateway.charge(50.0);
            System.out.println("Outer class result: " + result);
            if (!result.startsWith("STANDARD-")) throw new AssertionError("Expected standard gateway");
            System.out.println("usesStandardGatewayByDefault -- PASS");
        }

        @Nested
        @SpringJUnitConfig(SlowGatewayConfig.class) // OVERRIDES the outer class's configuration entirely
        class WithSlowGatewayScenario {
            @Autowired PaymentGateway paymentGateway; // re-declared: resolves against THIS nested class's own context

            @Test
            void usesSlowRetryingGatewayInThisScenario() {
                String result = paymentGateway.charge(50.0);
                System.out.println("Nested class result: " + result);
                if (!result.startsWith("RETRYING-")) throw new AssertionError("Expected the slow retrying gateway");
                System.out.println("usesSlowRetryingGatewayInThisScenario -- PASS");
            }
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(PaymentTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: same dependencies as Level 1, then `java NestedTestIntermediate.java`.

`WithSlowGatewayScenario`'s own `@SpringJUnitConfig(SlowGatewayConfig.class)` replaces the inherited configuration rather than merging with it — its own `paymentGateway` field resolves against a completely separate `ApplicationContext` built from `SlowGatewayConfig`, distinct from the outer `PaymentTest` class's context built from `DefaultConfig`. The outer class's test (`usesStandardGatewayByDefault`) is entirely unaffected by this nested override, since each gets its own independently-resolved (and independently cached) context.

### Level 3 — Advanced

Deeply nested scenarios (`@Nested` within `@Nested`) modeling a decision tree of test conditions, combined with `@Transactional` seeded state at the outer level that every nested scenario builds on — a realistic pattern for testing a business rule with several interacting conditions.

```java
import org.junit.jupiter.api.Nested;
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

public class NestedTestAdvanced {

    @Configuration
    @EnableTransactionManagement
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:accounts-schema.sql") // CREATE TABLE accounts(id BIGINT, balance DECIMAL, frozen BOOLEAN)
                    .build();
        }
        @Bean JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
        @Bean PlatformTransactionManager transactionManager(DataSource ds) { return new DataSourceTransactionManager(ds); }
    }

    @SpringJUnitConfig(Config.class)
    @Transactional // applies to every @Test method, including in @Nested classes -- all rolled back
    static class WithdrawalRulesTest {
        @Autowired JdbcTemplate jdbcTemplate;

        @Nested
        @Sql(statements = "INSERT INTO accounts VALUES (1, 100.00, false)") // seeded for THIS nested group only
        class WhenAccountIsActive {

            @Test
            void withdrawalWithinBalanceSucceeds() {
                Integer balance = jdbcTemplate.queryForObject(
                        "SELECT balance FROM accounts WHERE id = 1", Integer.class);
                System.out.println("Active account balance: " + balance);
                if (balance != 100) throw new AssertionError("Expected seeded balance of 100");
                System.out.println("withdrawalWithinBalanceSucceeds -- PASS");
            }

            @Nested
            class AndRequestedAmountExceedsBalance {
                @Test
                void withdrawalShouldBeRejected() {
                    // Deepest level of nesting: still sees the SAME seeded row from the parent @Nested class.
                    Integer balance = jdbcTemplate.queryForObject(
                            "SELECT balance FROM accounts WHERE id = 1", Integer.class);
                    boolean wouldBeRejected = 150.00 > balance; // requesting more than available
                    System.out.println("Requesting 150 against balance " + balance + " rejected: " + wouldBeRejected);
                    if (!wouldBeRejected) throw new AssertionError("Expected over-balance withdrawal to be rejected");
                    System.out.println("withdrawalShouldBeRejected -- PASS");
                }
            }
        }

        @Nested
        @Sql(statements = "INSERT INTO accounts VALUES (2, 500.00, true)") // different seed for THIS nested group
        class WhenAccountIsFrozen {
            @Test
            void anyWithdrawalIsRejectedRegardlessOfBalance() {
                Boolean frozen = jdbcTemplate.queryForObject(
                        "SELECT frozen FROM accounts WHERE id = 2", Boolean.class);
                System.out.println("Account 2 frozen: " + frozen);
                if (!frozen) throw new AssertionError("Expected the seeded account to be frozen");
                System.out.println("anyWithdrawalIsRejectedRegardlessOfBalance -- PASS");
            }
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(WithdrawalRulesTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: add `spring-test`, `spring-context`, `spring-jdbc`, `spring-tx`, `com.h2database:h2`, JUnit 5, and the JUnit Platform Launcher to the classpath, with `accounts-schema.sql` on the classpath; then `java NestedTestAdvanced.java`.

The outer class's `@Transactional` applies to every test method at every nesting depth, including `AndRequestedAmountExceedsBalance` two levels deep — each test method still gets its own transaction that rolls back afterward. Each `@Nested` class's own `@Sql` seeds data specific to that scenario group (`WhenAccountIsActive` seeds account `1`; `WhenAccountIsFrozen` seeds account `2`), and the doubly-nested `AndRequestedAmountExceedsBalance` class inherits both the outer `@Transactional` behavior and its immediate parent `@Nested` class's `@Sql` seed, demonstrating that these declarative test annotations compose correctly across nesting depth, not just one level.

## 6. Walkthrough

Trace `NestedTestAdvanced.WithdrawalRulesTest.WhenAccountIsActive.AndRequestedAmountExceedsBalance.withdrawalShouldBeRejected()`:

1. **Transaction begins.** Because the outermost `WithdrawalRulesTest` class is `@Transactional`, and this annotation's effect extends through nested classes, `TransactionalTestExecutionListener` starts a fresh transaction before this specific test method runs — exactly as it would for a top-level test method.
2. **Nested `@Sql` seeding.** The immediately enclosing `@Nested class WhenAccountIsActive` carries `@Sql(statements = "INSERT INTO accounts VALUES (1, 100.00, false)")`. This seed script runs before the test method, inside the same transaction from step 1 — seeding account `1` with a `100.00` balance.
3. **Doubly-nested test body runs.** `withdrawalShouldBeRejected()` (declared on `AndRequestedAmountExceedsBalance`, nested inside `WhenAccountIsActive`, nested inside `WithdrawalRulesTest`) queries the seeded balance, confirms it's `100`, and checks whether a hypothetical `150.00` withdrawal request would exceed it — which it does, so `wouldBeRejected` is `true`, and the assertion passes.
4. **Transaction rolls back.** After the method completes, the same rollback behavior from step 1 applies — the seeded account row from step 2 is undone, leaving the database clean for whatever test (nested or not) runs next.
5. **Sibling `@Nested` class is unaffected.** `WhenAccountIsFrozen`'s own test, `anyWithdrawalIsRejectedRegardlessOfBalance`, runs with its *own* `@Sql`-seeded account `2` — since each `@Nested` class's `@Sql` annotation applies specifically to test methods within that class (and its own nested classes), `WhenAccountIsActive`'s account `1` seed never appears in `WhenAccountIsFrozen`'s tests, and vice versa.

```
WithdrawalRulesTest (@Transactional -- applies at every nesting depth)
   WhenAccountIsActive (@Sql: seed account 1, balance 100)
        withdrawalWithinBalanceSucceeds() -- sees account 1
        AndRequestedAmountExceedsBalance (nested one level deeper)
            withdrawalShouldBeRejected() -- STILL sees account 1 (inherited seed + inherited transaction)
   WhenAccountIsFrozen (@Sql: seed account 2, balance 500, frozen)
        anyWithdrawalIsRejectedRegardlessOfBalance() -- sees ONLY account 2, never account 1
```

## 7. Gotchas & takeaways

> Gotcha: a `@Nested` class that declares its own `@ContextConfiguration`/`@SpringJUnitConfig` *replaces* the inherited configuration entirely rather than merging with it (Level 2) — but a `@Nested` class's own `@Sql`/`@Transactional`/other `TestExecutionListener`-backed annotations *compose additively* with the enclosing class's (Level 3). These are genuinely different inheritance behaviors for different annotation categories, and conflating them (expecting a nested `@ContextConfiguration` override to also somehow merge, or expecting a nested `@Sql` to replace rather than add to the parent's) is a real source of confusion when nesting gets deep.

- `@Nested` test classes let you structurally group related test scenarios, sharing the enclosing class's injected fields and (by default) its `ApplicationContext`, rather than relying purely on test-method naming conventions to convey grouping.
- A `@Nested` class can override its enclosing class's Spring configuration entirely by declaring its own `@ContextConfiguration`/`@SpringJUnitConfig`, useful for scenarios that genuinely need a different bean setup.
- Transactional behavior and `@Sql` seeding compose additively across nesting depth — an outer `@Transactional` still applies to a doubly-nested test method, and each nesting level's own `@Sql` adds its scenario-specific seed data on top of whatever ancestors already seeded.
- Nested test organization pays off most in large integration test classes with clear scenario groupings — for small, flat test classes, plain top-level test methods remain simpler and don't need this structure.
