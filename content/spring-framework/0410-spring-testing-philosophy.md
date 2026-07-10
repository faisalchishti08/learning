---
card: spring-framework
gi: 410
slug: spring-testing-philosophy
title: "Spring testing philosophy"
---

## 1. What it is

Spring's testing philosophy is a deliberate layering of test types, each trading off speed against realism: fast, isolated **unit tests** that don't touch Spring at all; **integration tests** that load a real (but cached) `ApplicationContext` to verify wiring and cross-bean interactions; and a small number of **end-to-end tests** that exercise the full stack, often over HTTP. Spring provides dedicated tooling for each layer rather than pushing you toward one style for everything.

```java
// Unit test — no Spring involved at all
class OrderCalculatorTest {
    @Test
    void appliesDiscount() {
        var calculator = new OrderCalculator();
        assertEquals(90.0, calculator.applyDiscount(100.0, 0.1));
    }
}
```

## 2. Why & when

Loading a full `ApplicationContext` for every test — even ones that only need to check a single method's arithmetic — is slow and tests more than you meant to test. Testing everything with mocks and no real Spring context, on the other hand, never verifies that your beans actually wire together correctly, that your `@Transactional` boundaries do what you think, or that your JPA mappings actually match your schema. Spring's philosophy is explicit about this trade-off: use plain, Spring-free unit tests for business logic in isolation (fastest, most numerous), use the Spring TestContext Framework for integration tests that need real wiring (slower, fewer, but catch real configuration bugs), and reserve full end-to-end tests for the handful of critical paths that need to be verified working exactly as they would in production (slowest, fewest).

This matters when deciding, for each piece of code you're about to test, which layer it belongs in:

- Pure business logic (calculations, validation rules, algorithms) with no Spring dependencies → plain unit test, no Spring context at all.
- A `@Service` that depends on a repository interface, where you want to verify the service's own logic without a real database → unit test with a mocked repository (Mockito), still no Spring context.
- Verifying that `@Transactional`, bean wiring, or a JPA repository's actual query behaves correctly against a real (often in-memory or containerized) database → Spring TestContext-based integration test.
- Verifying an HTTP endpoint's full request/response contract, security rules, and serialization → `@SpringBootTest` or `MockMvc`-based test, closer to end-to-end.

## 3. Core concept

```
                    Fewer, slower, more realistic
                              ^
                              |
                    End-to-end / @SpringBootTest(webEnvironment=RANDOM_PORT)
                              |
                    Integration tests (Spring TestContext, real ApplicationContext)
                              |
                    Unit tests with mocks (Mockito, no Spring context)
                              |
                    Pure unit tests (no Spring, no mocks, just objects)
                              v
                    More, faster, more isolated
```

This is Spring's take on the classic "testing pyramid": most tests should live at the bottom (fast, isolated, numerous), with progressively fewer, slower, more realistic tests as you move up — never inverted into a small number of slow end-to-end tests being your only safety net.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Testing pyramid: many fast unit tests at the base, fewer integration tests, fewest end-to-end tests at the top">
  <polygon points="320,20 420,90 220,90" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="62" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">End-to-end</text>

  <polygon points="220,90 420,90 480,150 160,150" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="126" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Integration (TestContext)</text>

  <polygon points="160,150 480,150 540,210 100,210" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="320" y="186" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Unit tests (fast, no Spring)</text>
</svg>

Width represents test count; height (from top to bottom) represents realism versus speed traded off at each layer.

## 5. Runnable example

### Level 1 — Basic

A pure unit test with no Spring involvement at all — the foundation of the pyramid, testing business logic in complete isolation.

```java
public class TestingPhilosophyBasic {

    static class OrderCalculator {
        double applyDiscount(double amount, double rate) {
            if (rate < 0 || rate > 1) throw new IllegalArgumentException("rate must be 0..1");
            return amount * (1 - rate);
        }
    }

    // A JUnit 5 test — normally in its own file, inlined here for a single runnable example.
    static void runTests() {
        var calculator = new OrderCalculator();

        double result = calculator.applyDiscount(100.0, 0.1);
        assert result == 90.0 : "Expected 90.0, got " + result;
        System.out.println("applyDiscount(100, 0.1) = " + result + " -- PASS");

        try {
            calculator.applyDiscount(100.0, 1.5);
            throw new AssertionError("Expected IllegalArgumentException");
        } catch (IllegalArgumentException e) {
            System.out.println("applyDiscount(100, 1.5) correctly threw: " + e.getMessage() + " -- PASS");
        }
    }

    public static void main(String[] args) {
        runTests();
    }
}
```

How to run: `java TestingPhilosophyBasic.java` (no dependencies beyond the JDK; in a real project this logic would be a JUnit 5 `@Test` method run via `mvn test`/`gradle test`).

No Spring context, no mocks, no test framework infrastructure — `OrderCalculator` is instantiated directly and its behavior verified with plain assertions. This runs in microseconds and requires nothing external, which is exactly why the base of the pyramid should be full of tests shaped like this one.

### Level 2 — Intermediate

A unit test for a `@Service` that depends on a repository, using Mockito to fake the dependency — still no Spring `ApplicationContext`, but now verifying logic that coordinates with a collaborator.

```java
import org.mockito.Mockito;

import java.util.Optional;

public class TestingPhilosophyIntermediate {

    record Order(long id, double amount, String status) {}

    interface OrderRepository {
        Optional<Order> findById(long id);
        void save(Order order);
    }

    static class OrderService {
        private final OrderRepository repository;
        OrderService(OrderRepository repository) { this.repository = repository; }

        void cancel(long orderId) {
            Order order = repository.findById(orderId)
                    .orElseThrow(() -> new IllegalArgumentException("Order not found: " + orderId));
            if ("SHIPPED".equals(order.status())) {
                throw new IllegalStateException("Cannot cancel a shipped order");
            }
            repository.save(new Order(order.id(), order.amount(), "CANCELLED"));
        }
    }

    public static void main(String[] args) {
        OrderRepository mockRepo = Mockito.mock(OrderRepository.class);
        Mockito.when(mockRepo.findById(1L))
                .thenReturn(Optional.of(new Order(1, 50.0, "PENDING")));

        OrderService service = new OrderService(mockRepo);
        service.cancel(1L);

        Mockito.verify(mockRepo).save(new Order(1, 50.0, "CANCELLED"));
        System.out.println("cancel() correctly saved order with status CANCELLED -- PASS");

        Mockito.reset(mockRepo);
        Mockito.when(mockRepo.findById(2L))
                .thenReturn(Optional.of(new Order(2, 75.0, "SHIPPED")));
        try {
            new OrderService(mockRepo).cancel(2L);
            throw new AssertionError("Expected IllegalStateException");
        } catch (IllegalStateException e) {
            System.out.println("cancel() correctly rejected shipped order: " + e.getMessage() + " -- PASS");
        }
    }
}
```

How to run: add `org.mockito:mockito-core` to the classpath, then `java TestingPhilosophyIntermediate.java`.

`Mockito.mock(OrderRepository.class)` creates a fake implementation with no real database behind it — `OrderService.cancel`'s branching logic (order not found, already shipped, otherwise cancel) is fully exercised without any Spring context or real persistence, keeping the test fast while still verifying the service's coordination logic against its dependency's contract.

### Level 3 — Advanced

The same `OrderService`, now tested through a real (in-memory, but genuinely Spring-managed) `ApplicationContext` with `@Transactional` test rollback — an actual Spring TestContext-based integration test, demonstrating the next layer up the pyramid and why it catches things the pure-mock unit test cannot (like whether the `@Transactional` boundary is even correctly applied).

```java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;

import javax.sql.DataSource;

public class TestingPhilosophyAdvanced {

    static class OrderService {
        private final JdbcTemplate jdbcTemplate;
        OrderService(JdbcTemplate jdbcTemplate) { this.jdbcTemplate = jdbcTemplate; }

        @Transactional
        void cancel(long orderId) {
            String status = jdbcTemplate.queryForObject(
                    "SELECT status FROM orders WHERE id = ?", String.class, orderId);
            if ("SHIPPED".equals(status)) {
                throw new IllegalStateException("Cannot cancel a shipped order");
            }
            jdbcTemplate.update("UPDATE orders SET status = 'CANCELLED' WHERE id = ?", orderId);
        }
    }

    @Configuration
    @EnableTransactionManagement
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:schema.sql") // CREATE TABLE orders(id BIGINT, status VARCHAR(20))
                    .build();
        }

        @Bean
        JdbcTemplate jdbcTemplate(DataSource dataSource) { return new JdbcTemplate(dataSource); }

        @Bean
        PlatformTransactionManager transactionManager(DataSource dataSource) {
            return new DataSourceTransactionManager(dataSource);
        }

        @Bean
        OrderService orderService(JdbcTemplate jdbcTemplate) { return new OrderService(jdbcTemplate); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(Config.class);
        JdbcTemplate jdbcTemplate = context.getBean(JdbcTemplate.class);
        OrderService service = context.getBean(OrderService.class);

        jdbcTemplate.update("INSERT INTO orders(id, status) VALUES (1, 'PENDING')");

        service.cancel(1L);
        String status = jdbcTemplate.queryForObject("SELECT status FROM orders WHERE id = 1", String.class);
        System.out.println("Order 1 status after cancel: " + status + " -- " + ("CANCELLED".equals(status) ? "PASS" : "FAIL"));

        context.close();
    }
}
```

How to run: add `spring-context`, `spring-jdbc`, `spring-tx`, and `com.h2database:h2` to the classpath, with a `schema.sql` on the classpath containing `CREATE TABLE orders(id BIGINT, status VARCHAR(20))`; then `java TestingPhilosophyAdvanced.java`. In a real JUnit test, this would use `@SpringJUnitConfig` and `@Transactional` on the test itself so each test method's changes roll back automatically (covered in the TestContext and transaction-management-in-tests cards).

Unlike Level 2's mocked repository, this test runs against a genuinely wired Spring context — a real `DataSource`, a real `JdbcTemplate`, and a real `PlatformTransactionManager` — verifying not just `OrderService`'s branching logic but that `@Transactional` and the SQL itself actually behave correctly together, something no amount of mocking `OrderRepository` in Level 2 could ever catch, because Level 2 never had a real repository implementation to get wrong in the first place.

## 6. Walkthrough

Trace why these three levels catch genuinely different classes of bugs, using a concrete hypothetical: suppose `cancel`'s SQL had a typo, `UPDATE orders SET staus = 'CANCELLED'` (misspelled column).

1. **Level 1 (pure unit test) can't catch it.** `OrderCalculator` never touches SQL at all — this bug class simply doesn't exist at this layer, by construction.
2. **Level 2 (mocked repository) can't catch it either.** The mock `OrderRepository.save(...)` is a Mockito stub — it has no real SQL behind it, so `Mockito.verify(mockRepo).save(...)` only confirms `OrderService` *called* `save` with the right argument, never that a real persistence layer would have accepted it. The typo lives entirely inside a real repository implementation, which this test never exercises.
3. **Level 3 (Spring TestContext integration test) catches it immediately.** `service.cancel(1L)` executes real SQL against a real (if embedded) H2 database — a misspelled `staus` column produces a genuine `BadSqlGrammarException` right there in the test run, because the SQL is genuinely parsed and executed, not mocked away.
4. **Why not make everything Level 3, then?** Spinning up an `ApplicationContext` and an embedded database for every single test — including ones that only check `OrderCalculator.applyDiscount`'s arithmetic — multiplies test suite runtime by orders of magnitude for no additional bug-catching power on that specific piece of logic. The pyramid shape isn't a compromise; it's the efficient allocation of "real infrastructure" testing to only the code that actually needs it.

```
Bug: SQL typo in the UPDATE statement inside OrderService.cancel

Level 1 (no Spring, no SQL involved)        -> cannot catch (wrong layer)
Level 2 (mocked repository, no real SQL)    -> cannot catch (mock has no SQL to typo)
Level 3 (real ApplicationContext, real DB)  -> CATCHES IT (real SQL actually runs)
```

## 7. Gotchas & takeaways

> Gotcha: a test suite with only Level 1/2-style unit tests and zero Level 3-style integration tests can pass at 100% while the application is fundamentally broken — every mock behaved exactly as configured, but nothing ever verified that the *real* wiring, SQL, or transaction boundaries actually work, which is precisely the class of bug that only shows up when real beans genuinely collaborate.

- Match the test type to what you're actually trying to verify: business logic in isolation → plain unit test; a service's coordination logic against a dependency's contract → mocked unit test; real wiring, SQL, or transactional behavior → Spring TestContext integration test.
- Keep the pyramid shape: many fast unit tests, fewer integration tests, fewest end-to-end tests — an inverted pyramid (mostly slow, realistic tests) makes the suite slow to run and slow to get feedback from.
- Mocking a dependency verifies your code called it correctly; it never verifies the dependency's real implementation is itself correct — that requires an integration test exercising the real implementation.
- The next several cards in this section (TestContext Framework, context caching, `@Transactional` in tests, `@Sql`) are all about making Level 3-style integration tests fast and manageable enough to write plenty of them, not just a token few.
