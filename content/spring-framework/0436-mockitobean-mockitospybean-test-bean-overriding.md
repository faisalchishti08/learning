---
card: spring-framework
gi: 436
slug: mockitobean-mockitospybean-test-bean-overriding
title: "@MockitoBean / @MockitoSpyBean (test bean overriding)"
---

## 1. What it is

`@MockitoBean` and `@MockitoSpyBean` (Spring Framework 6.2+, superseding Spring Boot's earlier `@MockBean`/`@SpyBean`) declaratively replace a bean in a test's `ApplicationContext` with a Mockito mock or spy — `@MockitoBean` substitutes a full mock (no real behavior unless stubbed), `@MockitoSpyBean` wraps the *real* bean, letting real method calls happen while still allowing verification and selective stubbing. Both are implemented via the `ContextCustomizer` mechanism covered in an earlier card, applied *before* context refresh, so every bean depending on the replaced type gets wired against the mock/spy correctly from the start.

```java
@SpringJUnitConfig(Config.class)
class OrderServiceTest {
    @MockitoBean PaymentGateway paymentGateway; // replaces the REAL bean, context-wide

    @Autowired OrderService orderService; // wired against the mock automatically

    @Test
    void test() {
        when(paymentGateway.charge(any())).thenReturn("mocked-result");
        // orderService genuinely uses the mock internally
    }
}
```

## 2. Why & when

The manual approach from the JUnit Jupiter support card — calling `context.getBeanFactory().registerSingleton(...)` after the context has already refreshed — has a real limitation: any bean already constructed and wired against the *original* bean definition keeps that original reference, unaffected by a late substitution. `@MockitoBean`/`@MockitoSpyBean` solve this properly by hooking into context construction *before* `refresh()`, via the same `ContextCustomizer` extension point, ensuring the mock or spy is in place from the very start — every dependent bean gets wired against it correctly, with zero manual `registerSingleton` calls and zero risk of the "already-wired" gotcha from that earlier card.

Reach for `@MockitoBean` when:

- A test needs a Spring-managed bean to be replaced with a fully controlled mock — an external API client, a payment gateway, anything you want zero real behavior from during this specific test.

Reach for `@MockitoSpyBean` when:

- You want *most* of a bean's real behavior to run, but need to verify specific interactions occurred, or selectively override just one method's behavior for one test — a spy wraps the real object, so unstubbed methods still execute genuinely.

Both replace context-wide by default (every dependent bean sees the mock/spy), scoped for the duration of the test class using them — after the test class finishes, the affected context is evicted from the cache (since it's now a customized, test-specific context) rather than corrupting other tests, exactly matching the `@DirtiesContext`-adjacent cache-key behavior from the context-customizers card.

## 3. Core concept

```
 @MockitoBean PaymentGateway paymentGateway;
        |
        v
 MockitoBean-aware ContextCustomizerFactory detects the field
        |
        v
 produces a ContextCustomizer that, BEFORE refresh():
     replaces the PaymentGateway bean definition/instance
     with Mockito.mock(PaymentGateway.class)
        |
        v
 context.refresh() -- EVERY bean needing PaymentGateway
                       (e.g. OrderService) gets wired against
                       the mock from the very start
        |
        v
 test field @MockitoBean PaymentGateway paymentGateway
   is injected with that SAME mock instance -- test can
   stub/verify it directly
```

Because this is a `ContextCustomizer`, it also participates in the context cache key — a test class using `@MockitoBean` gets its own cache entry, distinct from a test class using the real bean, exactly as the context-customizers card described.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MockitoBean substitutes a mock before context refresh so every dependent bean is wired against it">
  <rect x="10" y="20" width="170" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@MockitoBean field</text>

  <rect x="230" y="20" width="180" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ContextCustomizer</text>
  <text x="320" y="56" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">runs BEFORE refresh()</text>

  <rect x="460" y="20" width="170" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">every dependent bean</text>

  <rect x="230" y="110" width="180" height="44" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="137" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">context.refresh()</text>

  <line x1="180" y1="42" x2="225" y2="42" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="42" x2="455" y2="42" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="320" y1="64" x2="320" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The substitution happens before refresh, avoiding the "already-wired against the old bean" trap from manual, post-refresh substitution.

## 5. Runnable example

### Level 1 — Basic

`@MockitoBean` replacing a `PaymentGateway` dependency, with `OrderService` (a real bean depending on it) correctly wired against the mock from the start — no manual substitution code needed.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import static org.mockito.Mockito.when;

public class MockitoBeanBasic {

    interface PaymentGateway { String charge(double amount); }

    static class OrderService {
        private final PaymentGateway paymentGateway;
        OrderService(PaymentGateway paymentGateway) { this.paymentGateway = paymentGateway; }
        String checkout(double amount) { return paymentGateway.charge(amount); }
    }

    @Configuration
    static class Config {
        @Bean
        PaymentGateway paymentGateway() {
            return amount -> { throw new UnsupportedOperationException("real network call"); };
        }
        @Bean
        OrderService orderService(PaymentGateway paymentGateway) { return new OrderService(paymentGateway); }
    }

    @SpringJUnitConfig(Config.class)
    static class OrderServiceTest {
        @MockitoBean
        PaymentGateway paymentGateway; // replaces Config's real bean BEFORE context refresh

        @Autowired
        OrderService orderService; // wired against the mock automatically -- no manual substitution needed

        @Test
        void checkoutUsesTheMock() {
            when(paymentGateway.charge(49.99)).thenReturn("mocked-charge-result");

            String result = orderService.checkout(49.99);
            System.out.println("checkout result: " + result);
            if (!result.equals("mocked-charge-result")) throw new AssertionError("Expected the mock's stubbed result");
            System.out.println("checkoutUsesTheMock -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(OrderServiceTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: add `spring-test`, `spring-context`, `org.mockito:mockito-core`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java MockitoBeanBasic.java`.

`@MockitoBean PaymentGateway paymentGateway` both replaces the `Config`-declared real bean *and* injects the resulting mock into this test field, in one annotation — `OrderService`, constructed during context refresh, receives the mock automatically as its constructor dependency, since the substitution happened before refresh ran. Stubbing `paymentGateway.charge(49.99)` in the test body then genuinely affects what `orderService.checkout(49.99)` returns, proving the mock is the *same instance* the real `OrderService` bean is using internally.

### Level 2 — Intermediate

`@MockitoSpyBean` wrapping a real bean, letting most of its real behavior run while verifying specific calls and selectively overriding just one scenario — demonstrating the key difference from `@MockitoBean`'s full replacement.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.util.ArrayList;
import java.util.List;

import static org.mockito.Mockito.*;

public class MockitoSpyBeanIntermediate {

    static class AuditLogger {
        List<String> entries = new ArrayList<>();
        void log(String message) {
            entries.add(message); // REAL behavior -- a spy lets this genuinely run
            System.out.println("Real AuditLogger.log() executed: " + message);
        }
    }

    static class OrderService {
        private final AuditLogger auditLogger;
        OrderService(AuditLogger auditLogger) { this.auditLogger = auditLogger; }
        void placeOrder(String orderId) {
            auditLogger.log("Order placed: " + orderId);
        }
    }

    @Configuration
    static class Config {
        @Bean AuditLogger auditLogger() { return new AuditLogger(); }
        @Bean OrderService orderService(AuditLogger auditLogger) { return new OrderService(auditLogger); }
    }

    @SpringJUnitConfig(Config.class)
    static class OrderServiceSpyTest {
        @MockitoSpyBean
        AuditLogger auditLogger; // wraps the REAL AuditLogger -- real methods still execute

        @Autowired
        OrderService orderService;

        @Test
        void realLoggingHappensAndCanBeVerified() {
            orderService.placeOrder("order-1");

            // The REAL log() method ran -- entries genuinely contains the message.
            if (!auditLogger.entries.contains("Order placed: order-1")) {
                throw new AssertionError("Expected real AuditLogger behavior to have run");
            }
            System.out.println("Real behavior confirmed: " + auditLogger.entries);

            // AND we can still verify the call happened, exactly like with a full mock.
            verify(auditLogger).log("Order placed: order-1");
            System.out.println("realLoggingHappensAndCanBeVerified -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(OrderServiceSpyTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: same dependencies as Level 1, then `java MockitoSpyBeanIntermediate.java`.

Unlike `@MockitoBean`, `@MockitoSpyBean` doesn't replace the bean's real logic — `orderService.placeOrder(...)` triggers the *genuine* `AuditLogger.log(...)` method body (visible from the printed line and the mutated `entries` list), while Mockito's spy wrapper still records the call, letting `verify(auditLogger).log(...)` confirm it happened, exactly as it would against a full mock. This combination — real behavior plus verification — is what a spy offers that a plain mock cannot.

### Level 3 — Advanced

Combine `@MockitoBean` with Mockito's `@Answer`-based stubbing for a stateful mock that changes behavior across calls, and demonstrate the context-cache-key isolation between two test classes with different `@MockitoBean` usage — confirming they correctly get separate contexts, per the context-customizers mechanism underneath.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import static org.mockito.Mockito.when;

public class MockitoBeanAdvanced {

    interface InventoryService { int checkStock(String sku); }

    static class OrderValidator {
        private final InventoryService inventoryService;
        OrderValidator(InventoryService inventoryService) { this.inventoryService = inventoryService; }
        boolean canFulfill(String sku, int requestedQty) {
            return inventoryService.checkStock(sku) >= requestedQty;
        }
    }

    @Configuration
    static class Config {
        @Bean InventoryService inventoryService() {
            return sku -> { throw new UnsupportedOperationException("real inventory check"); };
        }
        @Bean OrderValidator orderValidator(InventoryService inventoryService) { return new OrderValidator(inventoryService); }
    }

    @SpringJUnitConfig(Config.class)
    static class LowStockScenarioTest {
        @MockitoBean
        InventoryService inventoryService; // this test class's OWN mock configuration

        @Autowired OrderValidator orderValidator;

        @Test
        void rejectsWhenStockIsLow() {
            when(inventoryService.checkStock("SKU-1")).thenReturn(2); // stubbed LOW for this scenario
            boolean canFulfill = orderValidator.canFulfill("SKU-1", 10);
            System.out.println("Can fulfill with low stock: " + canFulfill);
            if (canFulfill) throw new AssertionError("Expected rejection due to low stock");
            System.out.println("rejectsWhenStockIsLow -- PASS");
        }
    }

    @SpringJUnitConfig(Config.class) // SAME base configuration as LowStockScenarioTest
    static class HighStockScenarioTest {
        @MockitoBean
        InventoryService inventoryService; // a DIFFERENT test class's own mock -- own context, own stubbing

        @Autowired OrderValidator orderValidator;

        @Test
        void allowsWhenStockIsSufficient() {
            when(inventoryService.checkStock("SKU-1")).thenReturn(100); // stubbed HIGH for this scenario
            boolean canFulfill = orderValidator.canFulfill("SKU-1", 10);
            System.out.println("Can fulfill with high stock: " + canFulfill);
            if (!canFulfill) throw new AssertionError("Expected approval with sufficient stock");
            System.out.println("allowsWhenStockIsSufficient -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(LowStockScenarioTest.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(HighStockScenarioTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: same dependencies as Level 1, then `java MockitoBeanAdvanced.java`.

Both test classes use the identical `Config.class` but each has its own `@MockitoBean InventoryService` with entirely different stubbed behavior — because `@MockitoBean` participates in the context cache key (via the `ContextCustomizer` mechanism), these correctly get *separate* `ApplicationContext` instances, each with its own independently-stubbed mock, rather than one test's stubbing leaking into or conflicting with the other's. Without this cache-key participation, sharing a context between them could mean whichever test ran last "wins" the stubbing, producing flaky, order-dependent test results.

## 6. Walkthrough

Trace `MockitoBeanAdvanced.main`'s handling of the two test classes:

1. **`LowStockScenarioTest` processed first.** Its `@MockitoBean InventoryService` field, combined with `@SpringJUnitConfig(Config.class)`, produces a `MergedContextConfiguration` whose cache key includes this specific `@MockitoBean` customization (the field's type and test class identity, per the underlying `ContextCustomizer` implementation). No matching cache entry exists yet, so a fresh context is built, with `InventoryService` replaced by a mock before refresh.
2. **`rejectsWhenStockIsLow` runs.** `when(inventoryService.checkStock("SKU-1")).thenReturn(2)` stubs the mock; `orderValidator.canFulfill("SKU-1", 10)` calls into the real `OrderValidator`, which calls the mock, receiving `2` — since `2 < 10`, `canFulfill` returns `false`, and the test passes.
3. **`HighStockScenarioTest` processed next.** Despite using the *same* `Config.class`, its own `@MockitoBean InventoryService` field belongs to a *different* test class, producing a different cache key (per the context-customizers card's cache-key participation rule) — so this triggers a genuinely separate context build, with its own separate mock instance.
4. **`allowsWhenStockIsSufficient` runs.** `when(inventoryService.checkStock("SKU-1")).thenReturn(100)` stubs *this test's own* mock instance; `orderValidator.canFulfill("SKU-1", 10)` calls into *this context's* `OrderValidator`, receiving `100` — since `100 >= 10`, `canFulfill` returns `true`.
5. **No cross-contamination.** Because each test class got its own context and its own mock, `LowStockScenarioTest`'s stubbing (`returns 2`) never affects `HighStockScenarioTest`'s assertions (which need `returns 100`), and vice versa — exactly the isolation the cache-key participation guarantees, regardless of which test class happens to run first or second.

```
LowStockScenarioTest:  @MockitoBean (own cache key) -> own context, own mock -> stub returns 2  -> canFulfill=false -- PASS
HighStockScenarioTest: @MockitoBean (own cache key) -> own context, own mock -> stub returns 100 -> canFulfill=true  -- PASS

(two separate contexts, two separate mocks -- no interference despite identical Config.class)
```

## 7. Gotchas & takeaways

> Gotcha: because each distinct `@MockitoBean`/`@MockitoSpyBean` usage produces its own context cache entry, a test suite with many test classes each declaring slightly different mock configurations on otherwise-identical base configuration can defeat context caching broadly — exactly the same caution the context-caching card raised about `@TestPropertySource` variation, applying equally here. Grouping tests that need the same mock setup into fewer, larger test classes (using `@Nested` classes for scenario variation within one shared mock setup, per the nested-test-classes card) can reduce unnecessary context proliferation.

- `@MockitoBean`/`@MockitoSpyBean` substitute a mock/spy *before* context refresh (via the `ContextCustomizer` mechanism), avoiding the "already-wired against the old bean" trap that manual, post-refresh `registerSingleton` substitution has.
- `@MockitoBean` fully replaces a bean with no real behavior unless stubbed; `@MockitoSpyBean` wraps the real bean, letting genuine behavior run while still enabling verification and selective stubbing.
- Both participate in the test's context cache key, correctly isolating different test classes' mock configurations from each other — at the cost of each distinct configuration needing its own context build.
- `@MockitoSpyBean` is the right tool when a test needs to confirm a real interaction happened (verify a call) while still exercising genuine business logic, rather than replacing that logic entirely.
