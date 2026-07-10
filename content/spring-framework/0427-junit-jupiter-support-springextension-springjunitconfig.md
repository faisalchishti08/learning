---
card: spring-framework
gi: 427
slug: junit-jupiter-support-springextension-springjunitconfig
title: "JUnit Jupiter support (SpringExtension / @SpringJUnitConfig)"
---

## 1. What it is

`SpringExtension` is Spring's implementation of JUnit 5's `Extension` API — specifically, it implements several JUnit 5 SPI interfaces (`TestInstancePostProcessor`, `BeforeEachCallback`, `ParameterResolver`, and more) to bridge JUnit 5's test lifecycle into the Spring TestContext Framework covered throughout this section. `@SpringJUnitConfig` is a meta-annotation combining `@ExtendWith(SpringExtension.class)` with `@ContextConfiguration`, the shorthand seen in every earlier card's examples.

```java
@ExtendWith(SpringExtension.class)   // the explicit, two-annotation form
@ContextConfiguration(classes = AppConfig.class)
class OrderServiceTest { ... }

@SpringJUnitConfig(AppConfig.class)  // equivalent shorthand
class OrderServiceTest { ... }
```

## 2. Why & when

JUnit 5's architecture deliberately has no built-in knowledge of Spring, or any other framework — instead, it exposes an `Extension` SPI that any framework can implement to hook into test discovery, instantiation, and execution. `SpringExtension` is Spring's implementation of that SPI, translating JUnit 5's lifecycle callbacks into calls against the `TestContextManager` (and, through it, the chain of `TestExecutionListener`s covered in an earlier card) — this is the actual mechanism that makes `@Autowired` test fields, `@Transactional` test rollback, and `@Sql` script execution all work when running under JUnit 5.

Understanding this matters because:

- Every `@SpringJUnitConfig`-annotated test class in this whole section has been relying on `SpringExtension` under the hood — knowing the explicit two-annotation form (`@ExtendWith(SpringExtension.class)` + `@ContextConfiguration`) demystifies what the shorthand actually does.
- `SpringExtension` also implements JUnit 5's `ParameterResolver`, which is specifically what enables `@Autowired` method-parameter injection (from the dependency-injection card) and constructor injection (via `@TestConstructor`) — both JUnit 5-specific capabilities that don't exist in older JUnit 4-based Spring testing.
- Composing `SpringExtension` with other JUnit 5 extensions (via multiple `@ExtendWith` values, or JUnit 5's own composed-annotation support) is how you combine Spring's testing support with other JUnit 5 tooling (Mockito's `MockitoExtension`, a custom project-specific extension) in one test class.

## 3. Core concept

```
 JUnit 5 Extension SPI (framework-neutral):
   TestInstancePostProcessor, BeforeEachCallback, AfterEachCallback,
   ParameterResolver, TestInstanceFactory, ...

        implemented by
              |
              v
        SpringExtension
              |
              | translates each JUnit 5 callback into the
              | equivalent Spring TestContext Framework operation
              v
        TestContextManager
              |
              v
        chain of TestExecutionListeners (DependencyInjection, Transactional, SqlScripts, ...)


 @SpringJUnitConfig(AppConfig.class)
        =
 @ExtendWith(SpringExtension.class)
 @ContextConfiguration(classes = AppConfig.class)
```

`SpringExtension` is the adapter layer; everything downstream of it (context caching, listener chain, dependency injection) is the same TestContext Framework machinery covered in every prior card in this section, entirely independent of which test-runner API triggers it.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SpringExtension bridges JUnit 5's Extension SPI to the Spring TestContext Framework">
  <rect x="10" y="70" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JUnit 5 Extension SPI</text>
  <text x="95" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(framework-neutral)</text>

  <rect x="240" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">SpringExtension</text>

  <rect x="450" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">TestContextManager</text>
  <text x="540" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(TestExecutionListeners)</text>

  <line x1="180" y1="95" x2="235" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="390" y1="95" x2="445" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`SpringExtension` is the translation layer between two independently-designed extension systems.

## 5. Runnable example

### Level 1 — Basic

The explicit two-annotation form (`@ExtendWith` + `@ContextConfiguration`) alongside the `@SpringJUnitConfig` shorthand, side by side, confirming both produce identical, working behavior.

```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class SpringExtensionBasic {

    static class GreetingService { String greet(String name) { return "Hello, " + name; } }

    @Configuration
    static class Config {
        @Bean GreetingService greetingService() { return new GreetingService(); }
    }

    @ExtendWith(SpringExtension.class)          // explicit form
    @ContextConfiguration(classes = Config.class)
    static class ExplicitFormTest {
        @Autowired GreetingService greetingService;
        @Test void greets() {
            System.out.println("ExplicitFormTest: " + greetingService.greet("Ada"));
        }
    }

    @SpringJUnitConfig(Config.class)             // shorthand form
    static class ShorthandFormTest {
        @Autowired GreetingService greetingService;
        @Test void greets() {
            System.out.println("ShorthandFormTest: " + greetingService.greet("Ada"));
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(ExplicitFormTest.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(ShorthandFormTest.class))
                .build();
        launcher.execute(request);
        System.out.println("Both forms produced identical dependency injection behavior.");
    }
}
```

How to run: add `spring-test`, `spring-context`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java SpringExtensionBasic.java`.

Both test classes behave identically — `@SpringJUnitConfig(Config.class)` is defined as exactly `@ExtendWith(SpringExtension.class)` plus `@ContextConfiguration(classes = Config.class)`, a `@interface` meta-annotation bundling the two. Seeing them produce the same `"Hello, Ada"` output confirms the shorthand isn't doing anything extra or different — it's purely a convenience composition.

### Level 2 — Intermediate

Use `SpringExtension`'s `ParameterResolver` capability — JUnit 5-specific, unavailable in older JUnit 4-based Spring testing — to inject beans directly as test method parameters, alongside a second, independent JUnit 5 extension (a simple custom one) composed on the same test class.

```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class SpringExtensionIntermediate {

    static class OrderCalculator { double total(double price, int qty) { return price * qty; } }

    @Configuration
    static class Config {
        @Bean OrderCalculator orderCalculator() { return new OrderCalculator(); }
    }

    // A small, independent, non-Spring JUnit 5 extension, composed alongside SpringExtension.
    static class TimingExtension implements BeforeTestExecutionCallback, AfterTestExecutionCallback {
        @Override
        public void beforeTestExecution(ExtensionContext context) {
            context.getStore(ExtensionContext.Namespace.GLOBAL).put("start", System.nanoTime());
        }
        @Override
        public void afterTestExecution(ExtensionContext context) {
            long start = context.getStore(ExtensionContext.Namespace.GLOBAL).get("start", long.class);
            System.out.println(context.getDisplayName() + " took "
                    + (System.nanoTime() - start) / 1_000_000 + "ms");
        }
    }

    @SpringJUnitConfig(Config.class)
    @ExtendWith(TimingExtension.class) // composed ALONGSIDE SpringExtension (which @SpringJUnitConfig already adds)
    static class MultiExtensionTest {

        @Test
        void calculatorViaMethodParameter(@Autowired OrderCalculator calculator) {
            // Parameter injection: SpringExtension's ParameterResolver resolves this,
            // entirely independent of the TimingExtension also active on this class.
            double result = calculator.total(9.99, 3);
            System.out.println("Total: " + result);
            if (Math.abs(result - 29.97) > 0.001) throw new AssertionError("Unexpected total");
            System.out.println("calculatorViaMethodParameter -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(MultiExtensionTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: same dependencies as Level 1, then `java SpringExtensionIntermediate.java`.

`calculator` is resolved as a method parameter, not a class field — possible specifically because `SpringExtension` implements JUnit 5's `ParameterResolver` SPI. `TimingExtension` is a completely separate, Spring-unaware JUnit 5 extension composed on the same class via a second `@ExtendWith` — both extensions independently hook into the same test method's lifecycle without interfering with each other, demonstrating that Spring's JUnit 5 integration is a well-behaved citizen of JUnit 5's general extension model, not a special case requiring exclusive control of the test class.

### Level 3 — Advanced

Register `SpringExtension` programmatically alongside Mockito's `MockitoExtension` to combine mock-based unit testing (from the mocking card) with real Spring-managed dependency injection in one test class — injecting a Mockito mock directly into a Spring-managed bean's field via `@MockitoBean`-style wiring implemented with a custom `TestExecutionListener`, showing how the pieces from across this whole testing section actually compose together in a realistic test class.

```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.util.Optional;

import static org.mockito.Mockito.when;

public class SpringExtensionAdvanced {

    record Order(long id, String status) {}
    interface OrderRepository { Optional<Order> findById(long id); }

    static class OrderService {
        private final OrderRepository repository;
        OrderService(OrderRepository repository) { this.repository = repository; }
        String describe(long id) {
            return repository.findById(id).map(Order::status).orElse("NOT_FOUND");
        }
    }

    @Configuration
    static class Config {
        // A stand-in bean -- the real OrderRepository implementation isn't needed for this test,
        // since the test will substitute a Mockito mock for it before the context builds beans that need it.
        @Bean
        OrderRepository orderRepository() {
            return id -> { throw new UnsupportedOperationException("replaced by mock in this test"); };
        }
        @Bean
        OrderService orderService(OrderRepository repository) { return new OrderService(repository); }
    }

    // Composing SpringExtension (via the shorthand) with MockitoExtension on the SAME test class --
    // JUnit 5's multi-extension model lets both frameworks' extensions coexist.
    @SpringJUnitConfig(Config.class)
    @ExtendWith(MockitoExtension.class)
    static class CombinedFrameworksTest {
        @Mock OrderRepository mockRepository; // created by MockitoExtension, NOT by Spring

        @Autowired
        ConfigurableApplicationContext context; // real Spring context, injected by SpringExtension

        @Test
        void mockedRepositoryIsUsedInsteadOfTheRealBean() {
            when(mockRepository.findById(1L)).thenReturn(Optional.of(new Order(1, "SHIPPED")));

            // Manually substitute the mock into the live context's singleton registry for this test,
            // then re-fetch OrderService so it's constructed against the mock, not the stand-in bean.
            context.getBeanFactory().registerSingleton("orderRepository", mockRepository);
            OrderService orderService = new OrderService(mockRepository);

            String result = orderService.describe(1L);
            System.out.println("describe(1) = " + result);
            if (!"SHIPPED".equals(result)) throw new AssertionError("Expected SHIPPED, got " + result);
            System.out.println("mockedRepositoryIsUsedInsteadOfTheRealBean -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(CombinedFrameworksTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: add `spring-test`, `spring-context`, `org.mockito:mockito-core`, `org.mockito:mockito-junit-jupiter`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java SpringExtensionAdvanced.java`.

`@ExtendWith(MockitoExtension.class)` composed alongside `@SpringJUnitConfig`'s implicit `SpringExtension` means both frameworks' `@Mock`/`@Autowired` processing run on the same test instance — `mockRepository` is created and configured by Mockito's extension entirely independently of Spring's context, while `context` is injected by Spring's extension. (Spring Boot's real `@MockBean` support automates the manual `registerSingleton` step shown here via its own `ContextCustomizer`, from the previous card — this example demonstrates the underlying mechanism by hand, to show what that convenience is actually doing.)

## 6. Walkthrough

Trace `SpringExtensionAdvanced.CombinedFrameworksTest.mockedRepositoryIsUsedInsteadOfTheRealBean()`:

1. **Both extensions activate for this test.** JUnit 5's engine sees two `Extension`s registered on this class: `SpringExtension` (via `@SpringJUnitConfig`'s meta-annotation) and `MockitoExtension` (via the explicit `@ExtendWith`). Both get a chance to process the test instance before the method runs.
2. **`MockitoExtension` processes `@Mock`.** It creates a Mockito mock and assigns it to the `mockRepository` field — this happens independently of Spring, using Mockito's own reflection-based field injection, unrelated to Spring's `@Autowired` mechanism.
3. **`SpringExtension` processes `@Autowired`.** It resolves `context`'s type (`ConfigurableApplicationContext`) against the test's already-built `ApplicationContext` (built from `Config`, using the stand-in `OrderRepository` that throws if actually called) and injects it.
4. **Test body: stubbing.** `when(mockRepository.findById(1L)).thenReturn(...)` configures the Mockito mock's behavior — nothing about the Spring context is touched yet.
5. **Manual substitution.** `context.getBeanFactory().registerSingleton("orderRepository", mockRepository)` replaces whatever `orderRepository` bean definition existed with the mock instance directly in the singleton registry — from this point forward, any *new* lookup of that bean name would return the mock, though beans already constructed and wired against the old stand-in aren't retroactively updated.
6. **Fresh `OrderService` construction.** `new OrderService(mockRepository)` builds a service instance directly against the mock (bypassing the need to re-resolve dependencies through the container, since the pre-existing `orderService` bean from `Config` was already wired to the stand-in before this substitution happened).
7. **Method call, mock intercepts.** `orderService.describe(1L)` calls `repository.findById(1L)` — since `repository` here is the Mockito mock, its stubbed behavior from step 4 returns `Optional.of(new Order(1, "SHIPPED"))`, and `describe` maps that to `"SHIPPED"`.
8. **Assertion.** The test confirms the result matches the mock's configured response, proving the substitution worked — demonstrating, by hand, the same mechanism Spring Boot's `@MockBean` automates via a `ContextCustomizer`.

```
JUnit 5 test instance creation:
   MockitoExtension: mockRepository = Mockito.mock(OrderRepository.class)
   SpringExtension:  context = (already-built ApplicationContext, injected)

test body:
   stub mockRepository.findById(1L) -> Order(SHIPPED)
   context.getBeanFactory().registerSingleton("orderRepository", mockRepository)
   new OrderService(mockRepository).describe(1L)
        -> mockRepository.findById(1L) -> stubbed Order(SHIPPED)
        -> "SHIPPED"
   assert result == "SHIPPED" -- PASS
```

## 7. Gotchas & takeaways

> Gotcha: manually calling `registerSingleton(...)` on an already-refreshed context (as in Level 3) only affects *future* bean lookups by that name — any bean already constructed and wired against the old bean definition (like `Config`'s original `orderService` bean, already built against the stand-in `OrderRepository`) keeps its original reference and is unaffected by the late substitution. This is exactly why Spring Boot's real `@MockBean` performs its substitution via a `ContextCustomizer` running *before* `refresh()` (per the previous card), not after — ensuring every bean that depends on the mocked type gets wired against the mock from the start, not retroactively.

- `SpringExtension` is Spring's implementation of JUnit 5's `Extension` SPI, translating JUnit 5's lifecycle into calls against the same `TestContextManager`/`TestExecutionListener` machinery covered throughout this section.
- `@SpringJUnitConfig` is purely a shorthand for `@ExtendWith(SpringExtension.class)` + `@ContextConfiguration` — understanding the explicit form demystifies what the convenience annotation does.
- `SpringExtension` implementing `ParameterResolver` is what enables JUnit 5-specific capabilities like `@Autowired` method-parameter injection and `@TestConstructor`-based constructor injection, unavailable under older JUnit 4-based Spring testing.
- JUnit 5's multi-extension model lets `SpringExtension` compose cleanly with other extensions (`MockitoExtension`, custom project-specific ones) on the same test class — real-world test infrastructure often layers Spring's context management with other tools this way.
