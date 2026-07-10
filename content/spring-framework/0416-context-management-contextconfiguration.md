---
card: spring-framework
gi: 416
slug: context-management-contextconfiguration
title: "Context management (@ContextConfiguration)"
---

## 1. What it is

`@ContextConfiguration` is the core annotation that tells the TestContext Framework exactly how to build the `ApplicationContext` for a test class — which `@Configuration` classes, XML files, or component classes to load, and optionally a custom `ContextLoader` for non-standard setups. `@SpringJUnitConfig` (seen in earlier cards) is simply a combined shorthand for `@ExtendWith(SpringExtension.class)` plus `@ContextConfiguration`.

```java
@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = { AppConfig.class, TestOverridesConfig.class })
class OrderServiceTest {
    @Autowired OrderService orderService;
}
```

## 2. Why & when

A test class often needs a slightly different configuration than the production application — swapping a real payment gateway bean for a fake one, adding a test-only `DataSource`, or loading only a subset of the full application's configuration to keep the test focused and fast. `@ContextConfiguration` is the explicit, declarative way to specify exactly that: not "load the whole application," but "load precisely these classes/files, in this combination."

Reach for `@ContextConfiguration` (directly, or via `@SpringJUnitConfig`'s shorthand) whenever you need to:

- Load a narrower slice of configuration than the full application, to keep a specific integration test fast and focused on what it's actually testing.
- Layer test-specific configuration on top of (or instead of) production configuration — for example, replacing an external API client bean with a stub implementation via an additional `@Configuration` class passed alongside the real ones.
- Combine multiple configuration sources (several `@Configuration` classes, or a mix of Java config and legacy XML) into one test context.

In Spring Boot projects, `@SpringBootTest` typically replaces explicit `@ContextConfiguration` for most tests (it auto-discovers the application's main configuration), but understanding `@ContextConfiguration` remains valuable for narrowly-scoped "slice" tests and for any Spring Framework project not using Spring Boot's auto-configuration.

## 3. Core concept

```
 @ContextConfiguration(
     classes = { AppConfig.class, TestOverridesConfig.class },
     initializers = { CustomInitializer.class }
 )
        |
        v
   MergedContextConfiguration built from:
     - explicit classes (or XML locations, or component classes)
     - inherited configuration from superclasses (unless @ContextConfiguration(inheritLocations=false))
     - active profiles, property sources, context customizers
        |
        v
   ContextLoader (usually SmartContextLoader) builds the ApplicationContext
     from that merged configuration
```

The "merged" part matters: `@ContextConfiguration` on a subclass adds to (or, with the right settings, replaces) configuration inherited from a superclass, which is how test base classes can establish shared configuration that individual test classes extend.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ContextConfiguration merges multiple configuration sources into one ApplicationContext">
  <rect x="10" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="85" y="44" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">AppConfig.class</text>

  <rect x="10" y="70" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="85" y="94" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">TestOverrides.class</text>

  <rect x="290" y="45" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="66" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MergedContext</text>
  <text x="380" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Configuration</text>

  <rect x="510" y="45" width="120" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="570" y="74" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>

  <line x1="160" y1="40" x2="285" y2="60" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="160" y1="90" x2="285" y2="75" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="470" y1="70" x2="505" y2="70" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Multiple sources merge into one configuration description before a single `ApplicationContext` is actually built from it.

## 5. Runnable example

### Level 1 — Basic

Layer a test-only override configuration on top of a "production" configuration, replacing a real dependency with a fake one purely through `@ContextConfiguration`'s class list — no test-specific code inside the service itself.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class ContextConfigBasic {

    interface PaymentGateway { String charge(double amount); }

    static class RealPaymentGateway implements PaymentGateway {
        public String charge(double amount) { throw new UnsupportedOperationException("real network call"); }
    }

    static class FakePaymentGateway implements PaymentGateway {
        public String charge(double amount) { return "FAKE-CHARGE-" + amount; }
    }

    static class OrderService {
        private final PaymentGateway paymentGateway;
        OrderService(PaymentGateway paymentGateway) { this.paymentGateway = paymentGateway; }
        String checkout(double amount) { return paymentGateway.charge(amount); }
    }

    @Configuration
    static class AppConfig {
        @Bean
        PaymentGateway paymentGateway() { return new RealPaymentGateway(); } // production bean
        @Bean
        OrderService orderService(PaymentGateway paymentGateway) { return new OrderService(paymentGateway); }
    }

    @Configuration
    static class TestOverridesConfig {
        @Bean
        @Primary // takes priority over AppConfig's RealPaymentGateway
        PaymentGateway fakePaymentGateway() { return new FakePaymentGateway(); }
    }

    @SpringJUnitConfig({AppConfig.class, TestOverridesConfig.class})
    static class OrderServiceTest {
        @Autowired OrderService orderService;

        @Test
        void checkoutUsesFakeGateway() {
            String result = orderService.checkout(49.99);
            System.out.println("checkout result: " + result);
            if (!result.startsWith("FAKE-CHARGE-")) throw new AssertionError("Expected fake gateway to be used");
            System.out.println("checkoutUsesFakeGateway -- PASS");
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

How to run: add `spring-test`, `spring-context`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java ContextConfigBasic.java`.

`@SpringJUnitConfig({AppConfig.class, TestOverridesConfig.class})` loads both configuration classes into one merged context; `@Primary` on `TestOverridesConfig`'s `fakePaymentGateway` bean means `OrderService`'s `PaymentGateway` dependency resolves to the fake, not `AppConfig`'s real one — the real network-calling implementation is never even instantiated during this test, entirely through configuration composition, with zero changes to `OrderService` or `AppConfig` themselves.

### Level 2 — Intermediate

Use a base test class establishing shared configuration, and a subclass adding to it via inherited `@ContextConfiguration` — showing how common test infrastructure gets factored out once and reused across multiple concrete test classes.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class ContextConfigIntermediate {

    static class AuditLog {
        java.util.List<String> entries = new java.util.ArrayList<>();
        void record(String entry) { entries.add(entry); }
    }

    @Configuration
    static class BaseTestConfig {
        @Bean
        AuditLog auditLog() { return new AuditLog(); } // shared by every test extending the base class
    }

    @SpringJUnitConfig(BaseTestConfig.class)
    static abstract class AbstractIntegrationTest {
        @Autowired AuditLog auditLog;
    }

    interface InventoryService { void reserve(String sku); }

    @Configuration
    static class InventoryTestConfig {
        @Bean
        InventoryService inventoryService(AuditLog auditLog) {
            return sku -> auditLog.record("reserved:" + sku);
        }
    }

    @ContextConfiguration(classes = InventoryTestConfig.class) // ADDS to the inherited BaseTestConfig
    static class InventoryServiceTest extends AbstractIntegrationTest {
        @Autowired InventoryService inventoryService;

        @Test
        void reservingRecordsToSharedAuditLog() {
            inventoryService.reserve("SKU-1");
            System.out.println("Audit log entries: " + auditLog.entries);
            if (!auditLog.entries.contains("reserved:SKU-1")) throw new AssertionError("Missing audit entry");
            System.out.println("reservingRecordsToSharedAuditLog -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(InventoryServiceTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: same dependencies as Level 1, then `java ContextConfigIntermediate.java`.

`AbstractIntegrationTest`'s `@SpringJUnitConfig(BaseTestConfig.class)` establishes shared, common test infrastructure (here, an `AuditLog` bean every subclass gets for free); `InventoryServiceTest`'s `@ContextConfiguration(classes = InventoryTestConfig.class)` — with no `inheritLocations = false` — *adds* `InventoryTestConfig` to the inherited `BaseTestConfig`, producing a merged context containing beans from both. This pattern lets a project establish one base class with shared test scaffolding (test databases, common fakes, shared utilities) that many concrete integration test classes extend without repeating that setup.

### Level 3 — Advanced

Use `@ContextHierarchy` (built on `@ContextConfiguration`) to model a genuine parent/child context relationship in a test — mirroring how a real web application often has a root application context and a child web context — and verify that bean visibility rules (child sees parent beans, parent doesn't see child beans) hold exactly as they would in production.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.NoSuchBeanDefinitionException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.ContextHierarchy;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class ContextConfigAdvanced {

    static class SharedInfrastructure {
        String describe() { return "shared root-level infrastructure"; }
    }

    static class WebSpecificBean {
        String describe() { return "web-layer-only bean"; }
    }

    @Configuration
    static class RootConfig {
        @Bean
        SharedInfrastructure sharedInfrastructure() { return new SharedInfrastructure(); }
    }

    @Configuration
    static class WebConfig {
        @Bean
        WebSpecificBean webSpecificBean() { return new WebSpecificBean(); }
    }

    @SpringJUnitConfig
    @ContextHierarchy({
            @ContextConfiguration(classes = RootConfig.class),
            @ContextConfiguration(classes = WebConfig.class)
    })
    static class HierarchyTest {
        @Autowired ApplicationContext context; // this is the CHILD (web) context

        @Test
        void childContextSeesBothLevels() {
            SharedInfrastructure fromParent = context.getBean(SharedInfrastructure.class);
            WebSpecificBean fromChild = context.getBean(WebSpecificBean.class);
            System.out.println("Child context resolved parent bean: " + fromParent.describe());
            System.out.println("Child context resolved its own bean: " + fromChild.describe());

            ApplicationContext parent = context.getParent();
            try {
                parent.getBean(WebSpecificBean.class);
                throw new AssertionError("Parent should NOT see child-only beans");
            } catch (NoSuchBeanDefinitionException e) {
                System.out.println("Confirmed: parent context correctly cannot see WebSpecificBean -- PASS");
            }
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(HierarchyTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: same dependencies as Level 1, then `java ContextConfigAdvanced.java`.

`@ContextHierarchy` with two `@ContextConfiguration` entries builds a genuine two-level context hierarchy: a parent context from `RootConfig` and a child context from `WebConfig`, with the child's parent reference wired to the actual parent context — exactly the relationship a real Spring MVC application has between its root `ApplicationContext` and its `DispatcherServlet`'s web-specific context (covered in the context hierarchies card next). The child context can resolve beans from either level, but the parent genuinely cannot see the child's beans, which this test explicitly verifies rather than assumes.

## 6. Walkthrough

Trace `ContextConfigAdvanced.HierarchyTest.childContextSeesBothLevels()`:

1. **Hierarchy construction.** Before the test method runs, the TestContext Framework processes the `@ContextHierarchy` annotation: it first builds a parent `ApplicationContext` from `RootConfig` (registering the `SharedInfrastructure` bean), then builds a child `ApplicationContext` from `WebConfig`, explicitly setting the parent context on the child via `setParent(...)`.
2. **Injection.** `@Autowired ApplicationContext context` on the test class is populated with the *child* context — the one the test's own `@ContextConfiguration` in the hierarchy list most directly corresponds to.
3. **Parent bean lookup via child.** `context.getBean(SharedInfrastructure.class)` is called on the child context. Because `SharedInfrastructure` isn't defined in the child's own bean definitions, the child's `getBean` call delegates up to its parent — this is standard `ApplicationContext` parent-delegation behavior, not anything special to testing — and finds it there, returning the parent-context-managed instance.
4. **Child bean lookup.** `context.getBean(WebSpecificBean.class)` finds this bean directly in the child context's own bean definitions, no delegation needed.
5. **Explicit parent retrieval.** `context.getParent()` returns the actual parent `ApplicationContext` instance built in step 1.
6. **Reverse lookup fails as expected.** `parent.getBean(WebSpecificBean.class)` is called directly on the *parent* — since parent contexts have no visibility into their children's bean definitions (delegation only flows child-to-parent, never the reverse), this correctly throws `NoSuchBeanDefinitionException`, and the test's `catch` block confirms this is the expected, correct behavior rather than treating it as a test failure.

```
RootConfig    -> parent ApplicationContext  [SharedInfrastructure]
WebConfig     -> child ApplicationContext   [WebSpecificBean], parent = RootConfig's context

child.getBean(SharedInfrastructure) -> not in child -> delegate to parent -> FOUND
child.getBean(WebSpecificBean)      -> found directly in child
parent.getBean(WebSpecificBean)     -> not in parent, no delegation upward from parent -> NoSuchBeanDefinitionException
```

## 7. Gotchas & takeaways

> Gotcha: `@ContextConfiguration` on a subclass *adds to* inherited configuration from a superclass by default — it does not replace it, which is usually what you want (Level 2's pattern) but can surprise you if you expected a subclass's `@ContextConfiguration` to fully override rather than merge with the parent class's. Use `@ContextConfiguration(inheritLocations = false)` (or the equivalent for component classes) when you specifically need a subclass to replace, not extend, its superclass's configuration.

- `@ContextConfiguration` (often used via the `@SpringJUnitConfig` shorthand) is the explicit, declarative description of exactly which configuration builds a test's `ApplicationContext` — narrower and more precise than loading "the whole application."
- Layering a test-only `@Configuration` class alongside production configuration (with `@Primary` or `@Bean` overriding) is a clean way to swap specific dependencies for test doubles without modifying production code or the class under test.
- Base test classes with their own `@SpringJUnitConfig`/`@ContextConfiguration` let you factor out shared test infrastructure that multiple concrete test classes extend and add to.
- `@ContextHierarchy` builds genuine parent/child context relationships in tests, useful for verifying the same bean-visibility rules (child sees parent, parent doesn't see child) that apply in real multi-context deployments like a Spring MVC application's root and web contexts.
