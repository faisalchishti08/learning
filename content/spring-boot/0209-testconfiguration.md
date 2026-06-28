---
card: spring-boot
gi: 209
slug: testconfiguration
title: "@TestConfiguration"
---

## 1. What it is

`@TestConfiguration` is a specialization of `@Configuration` for test-only bean definitions. Unlike a regular `@Configuration` class, `@TestConfiguration` is **not picked up by the main component scan** — it won't accidentally appear in the production context. It must be explicitly imported into a test via `@Import` or declared as a static inner class of the test class. It can add new beans or customize existing ones for the test scenario.

## 2. Why & when

Use `@TestConfiguration` when:
- You want to replace a real dependency with a test double (a fake, stub, or in-memory alternative) without using Mockito mocks.
- You need to configure a bean differently for tests (e.g., use a synchronous executor instead of async).
- You want to add test-only beans (e.g., a pre-seeded test data repository) without cluttering the production context.

Prefer `@MockitoBean` for simple stub/verify scenarios. Use `@TestConfiguration` when the replacement requires real logic (e.g., an in-memory implementation of an email sender that records sent emails for assertion).

## 3. Core concept

**As a static inner class** (auto-detected within the test class):
```java
@SpringBootTest
class OrderServiceTest {

    @Autowired OrderService orderService;

    @TestConfiguration
    static class TestBeans {
        @Bean
        EmailService emailService() {
            return new FakeEmailService(); // in-memory implementation
        }
    }

    @Test
    void createOrder_sendsEmail() {
        orderService.createOrder(new OrderRequest("alice", 99.99));
        // assert on FakeEmailService's recorded emails
    }
}
```

**Via `@Import`** (shared across multiple test classes):
```java
@TestConfiguration
public class TestEmailConfig {
    @Bean EmailService emailService() { return new FakeEmailService(); }
}

@SpringBootTest
@Import(TestEmailConfig.class)
class OrderIT { ... }
```

**Key rule:** `@TestConfiguration` with the same bean name **supplements** existing beans by default — it does NOT replace them. To replace an existing bean, the method must use `@Bean` on a method whose name matches an existing bean or use `@Primary`.

## 4. Diagram

<svg viewBox="0 0 680 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@TestConfiguration is excluded from main component scan; it is imported explicitly into a test via @Import or as a static inner class, adding or overriding beans in the test context">
  <!-- Main scan (excludes @TestConfiguration) -->
  <rect x="10" y="20" width="190" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Main Component Scan</text>
  <text x="105" y="58" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">✓ @Service, @Repository</text>
  <text x="105" y="72" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">✓ @Configuration classes</text>
  <text x="105" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">✗ @TestConfiguration (skipped)</text>

  <!-- @TestConfiguration -->
  <rect x="10" y="110" width="190" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@TestConfiguration</text>
  <text x="105" y="148" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">FakeEmailService @Bean</text>
  <text x="105" y="164" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">InMemoryMessageQueue @Bean</text>
  <text x="105" y="176" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(only active when @Import-ed)</text>

  <!-- @Import arrow -->
  <line x1="202" y1="145" x2="270" y2="110" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="5,2" marker-end="url(#tca)"/>
  <text x="245" y="135" fill="#79c0ff" font-size="8" font-family="sans-serif">@Import</text>

  <!-- Test context -->
  <rect x="275" y="30" width="265" height="140" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="407" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Test Context</text>
  <text x="407" y="72" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService (real)</text>
  <text x="407" y="89" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">OrderRepository (real)</text>
  <text x="407" y="106" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">EmailService = FakeEmailService</text>
  <text x="407" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(production EmailService replaced)</text>
  <text x="407" y="142" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">only in this test's context</text>
  <text x="407" y="158" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">production context unchanged</text>

  <line x1="202" y1="55" x2="273" y2="78" stroke="#6db33f" stroke-width="1.5" marker-end="url(#tcb)"/>

  <!-- static inner class path -->
  <rect x="555" y="75" width="115" height="60" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="612" y="97" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Alternative:</text>
  <text x="612" y="112" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">static inner class</text>
  <text x="612" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">auto-detected</text>

  <defs>
    <marker id="tca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="tcb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`@TestConfiguration` bypasses the main scan and is only active when explicitly imported — keeping test beans out of production while providing real implementations for test scenarios.

## 5. Runnable example

```java
// TestConfigurationDemo.java — demonstrates @TestConfiguration bean override and supplement patterns
// How to run: java TestConfigurationDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: @TestConfiguration + @Import or static inner class inside @SpringBootTest

import java.util.*;

public class TestConfigurationDemo {

    // Production interfaces and implementations
    interface EmailService {
        void send(String to, String subject, String body);
        List<String> getSentEmails(); // only needed for test assertions
    }

    static class SmtpEmailService implements EmailService {
        @Override
        public void send(String to, String subject, String body) {
            System.out.println("  [SMTP] Sending email to " + to + ": " + subject);
            // in real life: connects to SMTP server — unacceptable in tests
        }
        @Override public List<String> getSentEmails() { return List.of(); }
    }

    // @TestConfiguration bean — in-memory fake for testing
    static class FakeEmailService implements EmailService {
        private final List<String> sent = new ArrayList<>();
        @Override
        public void send(String to, String subject, String body) {
            sent.add(to + " | " + subject);
            System.out.println("  [FakeEmail] Recorded email to " + to + ": " + subject);
        }
        @Override public List<String> getSentEmails() { return Collections.unmodifiableList(sent); }
    }

    // Service that depends on EmailService
    static class OrderService {
        private final EmailService emailService;
        OrderService(EmailService emailService) { this.emailService = emailService; }

        String createOrder(String customer, double total) {
            String orderId = "ORD-" + System.currentTimeMillis() % 1000;
            emailService.send(customer + "@example.com",
                    "Order Confirmed: " + orderId,
                    "Your order total: $" + total);
            return orderId;
        }
    }

    // Simulates context with production EmailService
    static class ProductionContext {
        EmailService email = new SmtpEmailService();
        OrderService orders = new OrderService(email);
    }

    // Simulates context where @TestConfiguration overrides EmailService with FakeEmailService
    static class TestContext {
        FakeEmailService email = new FakeEmailService(); // @TestConfiguration @Bean
        OrderService orders = new OrderService(email);   // same OrderService, different EmailService
    }

    static void expect(boolean condition, String message) {
        if (!condition) throw new AssertionError("FAIL: " + message);
        System.out.println("  ✓ " + message);
    }

    public static void main(String[] args) {
        System.out.println("=== @TestConfiguration Demo ===\n");

        System.out.println("--- Production context (SMTP email) ---");
        ProductionContext prod = new ProductionContext();
        prod.orders.createOrder("alice", 99.99);
        System.out.println("  (Would fail in CI: no SMTP server)");

        System.out.println("\n--- Test context (@TestConfiguration FakeEmailService) ---");
        TestContext test = new TestContext();
        String orderId = test.orders.createOrder("alice", 99.99);
        String orderId2 = test.orders.createOrder("bob", 149.50);

        // Test assertions on the fake
        expect(test.email.getSentEmails().size() == 2,
               "two emails sent");
        expect(test.email.getSentEmails().get(0).contains("alice@example.com"),
               "first email to alice");
        expect(test.email.getSentEmails().get(1).contains("bob@example.com"),
               "second email to bob");
        System.out.println("  Recorded emails: " + test.email.getSentEmails());

        System.out.println("\n--- Real @TestConfiguration patterns ---");
        System.out.println("""
// Pattern 1: static inner class (auto-detected by @SpringBootTest)
@SpringBootTest
class OrderServiceTest {
    @Autowired OrderService   orderService;
    @Autowired FakeEmailService fakeEmail; // injected from inner @TestConfiguration

    @TestConfiguration
    static class TestBeans {
        @Bean @Primary
        FakeEmailService emailService() { return new FakeEmailService(); }
    }

    @Test void createOrder_sendsConfirmation() {
        orderService.createOrder(new OrderRequest("alice", 99.99));
        assertThat(fakeEmail.getSentEmails()).hasSize(1);
        assertThat(fakeEmail.getSentEmails().get(0)).contains("alice");
    }
}

// Pattern 2: shared via @Import
@TestConfiguration
public class FakeEmailConfig {
    @Bean @Primary EmailService emailService() { return new FakeEmailService(); }
}

@SpringBootTest
@Import(FakeEmailConfig.class)
class AnotherTest { ... }""");

        System.out.println("\nAll tests passed.");
    }
}
```

**How to run:** `java TestConfigurationDemo.java`

## 6. Walkthrough

- **Production context**: `SmtpEmailService` would connect to a real SMTP server — a side effect that must not happen in CI. The `TestContext` swaps it out with `FakeEmailService`.
- **`FakeEmailService`**: a real implementation (not a Mockito mock) that stores sent emails in a list. This lets tests assert on what was sent without any mocking framework.
- **`OrderService` is unchanged**: the key value of `@TestConfiguration` is that production beans (`OrderService`) remain unmodified — only the dependency (`EmailService`) is swapped.
- **Assertion pattern**: after calling `createOrder`, the test checks `fakeEmail.getSentEmails()` — a verification that only the fake supports. With a Mockito mock, you'd use `verify(email).send(...)` instead.
- The real code patterns show both the inner-class and `@Import` approaches.

## 7. Gotchas & takeaways

> `@TestConfiguration` does **not replace** an existing bean with the same type by default. If `SmtpEmailService` is a `@Component`, both it and the `FakeEmailService` from `@TestConfiguration` will exist in the context. Add `@Primary` to the test bean to resolve the ambiguity, or use `@MockitoBean` which always replaces.

> A `@TestConfiguration` placed in `src/test/java` at a **top-level package** (same as `@SpringBootApplication`) will still be found by the component scan — it is only excluded if it's in a different package or declared as a static inner class. The safest approach is the static inner class pattern.

- `@TestConfiguration` is inheritable: if a base test class imports it, all subclasses get the beans.
- Context cache: each distinct set of `@Import`-ed `@TestConfiguration` classes results in a separate cached context. Maximize reuse by sharing base test classes.
- `@Bean` methods in `@TestConfiguration` participate in the normal `@Autowired` injection — your test can inject `FakeEmailService` directly for assertions.
- Use `@TestConfiguration` for infrastructure fakes (email, payment gateways, external APIs); use `@MockitoBean` for behavioral stubs where call verification matters more than state inspection.
