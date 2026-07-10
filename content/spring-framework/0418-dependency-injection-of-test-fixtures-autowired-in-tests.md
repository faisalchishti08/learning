---
card: spring-framework
gi: 418
slug: dependency-injection-of-test-fixtures-autowired-in-tests
title: "Dependency injection of test fixtures (@Autowired in tests)"
---

## 1. What it is

The TestContext Framework injects dependencies directly into test class fields using the exact same `@Autowired` annotation used everywhere else in Spring — the difference is that the injection target is a test fixture (the test class itself), not application code. Fields, setter methods, and even test method parameters (via JUnit 5's parameter resolution, bridged by `SpringExtension`) can all receive beans from the test's `ApplicationContext`.

```java
@SpringJUnitConfig(AppConfig.class)
class OrderServiceTest {
    @Autowired OrderService orderService;   // field injection
    @Autowired JdbcTemplate jdbcTemplate;   // multiple fields, same mechanism

    @Test
    void test(@Autowired ProductRepository repository) { // method parameter injection
        // ...
    }
}
```

## 2. Why & when

Without this, a test needing several real, correctly-wired collaborators would have to manually call `context.getBean(...)` for each one, repeated in every test method or hoisted into a `@BeforeEach` — mechanical boilerplate that obscures what the test is actually about. `@Autowired` on test fields removes that boilerplate entirely: declare what you need, and the framework populates it before each test method runs, using exactly the same autowiring resolution rules (by type, disambiguated by `@Qualifier` when needed) that apply to application beans.

This matters for every integration test that needs real, container-managed collaborators — which is most of them, since the whole point of an integration test (per the testing-goals card) is exercising real wiring rather than hand-constructed or mocked objects. Method-parameter injection (via JUnit 5's `ParameterResolver` mechanism, which `SpringExtension` implements) is specifically useful when you want a bean scoped to just one test method rather than shared as a field across the whole class.

## 3. Core concept

```
 @SpringJUnitConfig(Config.class)
 class MyTest {
     @Autowired Foo foo;         <- field injection: populated before EVERY @Test method
        |
        v
 DependencyInjectionTestExecutionListener.beforeTestMethod(context)
        |
        | for each @Autowired field/method on the test instance:
        v
     resolve the bean from the ApplicationContext by type (+ @Qualifier if needed)
        |
        v
     set the field via reflection
```

Field injection happens once per test method invocation (not once per class) — since the framework re-resolves and re-injects before every `@Test`, even though the underlying beans themselves are typically singletons shared across all those injections (unless scoped otherwise).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DependencyInjectionTestExecutionListener populates Autowired test fields before each test method runs">
  <rect x="10" y="70" width="190" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>
  <text x="105" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(cached, per earlier card)</text>

  <rect x="260" y="70" width="230" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="375" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DependencyInjection</text>
  <text x="375" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">TestExecutionListener</text>

  <rect x="540" y="70" width="90" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Test</text>

  <line x1="200" y1="95" x2="255" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="490" y1="95" x2="535" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The listener sits between the (possibly cached) context and the test method, wiring one to the other on every run.

## 5. Runnable example

### Level 1 — Basic

Field injection of a single bean, and confirmation that it's re-injected (though pointing at the same singleton) before each of two different `@Test` methods.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class AutowiredTestBasic {

    static class Clock {
        String now() { return "fixed-time-for-test"; }
    }

    @Configuration
    static class Config {
        @Bean Clock clock() { return new Clock(); }
    }

    @SpringJUnitConfig(Config.class)
    static class ClockTest {
        @Autowired Clock clock; // populated by the framework before EACH @Test method

        @Test
        void firstTest() {
            System.out.println("firstTest sees clock: " + System.identityHashCode(clock));
            if (clock == null) throw new AssertionError("clock was not injected");
        }

        @Test
        void secondTest() {
            System.out.println("secondTest sees clock: " + System.identityHashCode(clock));
            if (clock == null) throw new AssertionError("clock was not injected");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(ClockTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
        System.out.println("Both identityHashCodes above should match: same singleton, reinjected each time.");
    }
}
```

How to run: add `spring-test`, `spring-context`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java AutowiredTestBasic.java`.

Both `firstTest` and `secondTest` print the same `identityHashCode` for `clock`, confirming that although the framework re-runs its injection logic before every test method (a fresh JUnit 5 test instance is typically created per method by default), it resolves to the same singleton `Clock` bean from the shared, cached `ApplicationContext` each time — not a new instance per test.

### Level 2 — Intermediate

Combine field injection with JUnit 5 method-parameter injection, and use `@Qualifier` to disambiguate when more than one bean of the same type exists — both realistic needs once a test class's dependencies grow.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class AutowiredTestIntermediate {

    interface Notifier { String send(String message); }

    @Configuration
    static class Config {
        @Bean
        @Qualifier("email")
        Notifier emailNotifier() { return msg -> "EMAIL: " + msg; }

        @Bean
        @Qualifier("sms")
        Notifier smsNotifier() { return msg -> "SMS: " + msg; }
    }

    @SpringJUnitConfig(Config.class)
    static class NotifierTest {
        @Autowired @Qualifier("email")
        Notifier emailNotifier; // field injection, disambiguated

        @Test
        void emailNotifierWorks() {
            String result = emailNotifier.send("hello");
            System.out.println(result);
            if (!result.startsWith("EMAIL:")) throw new AssertionError("Wrong notifier injected");
            System.out.println("emailNotifierWorks -- PASS");
        }

        @Test
        void smsNotifierViaMethodParameter(@Autowired @Qualifier("sms") Notifier smsNotifier) {
            // Method-parameter injection: scoped to just this one test method, not a class field.
            String result = smsNotifier.send("hello");
            System.out.println(result);
            if (!result.startsWith("SMS:")) throw new AssertionError("Wrong notifier injected");
            System.out.println("smsNotifierViaMethodParameter -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(NotifierTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: same dependencies as Level 1, then `java AutowiredTestIntermediate.java`.

With two `Notifier` beans present, plain `@Autowired Notifier` alone would be ambiguous — `@Qualifier("email")`/`@Qualifier("sms")` resolve that ambiguity exactly as they would in application code. `smsNotifierViaMethodParameter`'s parameter injection demonstrates that a bean needed by only one specific test method doesn't need to become a class-wide field — `SpringExtension` implements JUnit 5's `ParameterResolver` interface specifically to support this narrower scoping.

### Level 3 — Advanced

Inject a test-specific bean that exists *only* in test configuration (not part of any production configuration) alongside real application beans, and use constructor injection at the test-class level (supported since Spring 5.2 via `TestConstructor`) instead of field injection — showing an alternative injection style some teams prefer for its immutability.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.TestConstructor;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.util.concurrent.atomic.AtomicInteger;

public class AutowiredTestAdvanced {

    static class OrderIdGenerator {
        AtomicInteger counter = new AtomicInteger();
        long next() { return counter.incrementAndGet(); }
    }

    static class OrderService {
        private final OrderIdGenerator idGenerator;
        OrderService(OrderIdGenerator idGenerator) { this.idGenerator = idGenerator; }
        long createOrder() { return idGenerator.next(); }
    }

    // Test-only spy wrapping the real generator to record every id it produced during a test.
    static class RecordingIdGenerator extends OrderIdGenerator {
        java.util.List<Long> generatedIds = new java.util.ArrayList<>();
        @Override
        long next() {
            long id = super.next();
            generatedIds.add(id);
            return id;
        }
    }

    @Configuration
    static class ProductionConfig {
        @Bean
        OrderIdGenerator orderIdGenerator() { return new OrderIdGenerator(); } // real bean
        @Bean
        OrderService orderService(OrderIdGenerator idGenerator) { return new OrderService(idGenerator); }
    }

    @Configuration
    static class TestOnlyConfig {
        @Bean
        @Primary
        RecordingIdGenerator recordingIdGenerator() { return new RecordingIdGenerator(); } // test-only override
    }

    @SpringJUnitConfig({ProductionConfig.class, TestOnlyConfig.class})
    @TestConstructor(autowireMode = TestConstructor.AutowireMode.ALL) // enable constructor injection for this test
    static class OrderServiceTest {
        private final OrderService orderService;
        private final RecordingIdGenerator recordingIdGenerator; // test-only bean, injected via constructor

        OrderServiceTest(OrderService orderService, RecordingIdGenerator recordingIdGenerator) {
            this.orderService = orderService;
            this.recordingIdGenerator = recordingIdGenerator;
        }

        @Test
        void createdOrdersAreRecorded() {
            long id1 = orderService.createOrder();
            long id2 = orderService.createOrder();

            System.out.println("Created order ids: " + id1 + ", " + id2);
            System.out.println("Recorded by test spy: " + recordingIdGenerator.generatedIds);
            if (!recordingIdGenerator.generatedIds.equals(java.util.List.of(id1, id2))) {
                throw new AssertionError("Recording spy did not capture the expected ids");
            }
            System.out.println("createdOrdersAreRecorded -- PASS");
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

How to run: same dependencies as Level 1, then `java AutowiredTestAdvanced.java`.

`@TestConstructor(autowireMode = TestConstructor.AutowireMode.ALL)` tells the framework to inject the test class's constructor parameters directly, rather than requiring `@Autowired` on fields — the resulting `orderService`/`recordingIdGenerator` fields can be `final`, an immutability benefit field injection can't offer. `TestOnlyConfig`'s `@Primary RecordingIdGenerator` bean transparently replaces `ProductionConfig`'s plain `OrderIdGenerator` everywhere it's autowired (including inside the real `OrderService`), while still being independently injectable into the test itself by its own concrete type — letting the test both exercise real production wiring *and* directly inspect what happened, without `OrderService` or `ProductionConfig` needing any test-awareness.

## 6. Walkthrough

Trace `AutowiredTestAdvanced.OrderServiceTest.createdOrdersAreRecorded()`:

1. **Context assembly.** The merged configuration (`ProductionConfig` + `TestOnlyConfig`) is built: `ProductionConfig` defines `orderIdGenerator` (a plain `OrderIdGenerator`) and `orderService` (which needs an `OrderIdGenerator`); `TestOnlyConfig` defines `recordingIdGenerator`, a `RecordingIdGenerator` (subclass of `OrderIdGenerator`) marked `@Primary`.
2. **Bean resolution for `OrderService`.** When the context wires `orderService`'s constructor parameter (type `OrderIdGenerator`), it finds *two* candidates — the plain one from `ProductionConfig` and the `@Primary` `RecordingIdGenerator` from `TestOnlyConfig` (since `RecordingIdGenerator extends OrderIdGenerator`, it qualifies as a candidate). The `@Primary` annotation breaks the tie, so `orderService` actually receives the `RecordingIdGenerator` instance — completely transparently to `OrderService`'s own code, which only knows about the `OrderIdGenerator` type.
3. **Test constructor injection.** Because of `@TestConstructor(autowireMode = ALL)`, the framework resolves `OrderServiceTest`'s constructor parameters directly: `OrderService` (the one real bean, now internally holding the recording generator) and `RecordingIdGenerator` (resolved by its own concrete type, finding the same `@Primary` bean instance from step 2).
4. **Test body: first call.** `orderService.createOrder()` calls into `OrderService.createOrder()`, which calls `idGenerator.next()` — but `idGenerator` here is actually the `RecordingIdGenerator` instance (per step 2), so its overridden `next()` runs: it calls `super.next()` (incrementing the counter to `1`), appends `1L` to `generatedIds`, and returns `1`.
5. **Second call.** Same flow, `counter` increments to `2`, `generatedIds` becomes `[1, 2]`.
6. **Assertion.** The test's own `recordingIdGenerator` field — injected via the test constructor, and confirmed to be the *same* instance `OrderService` was actually using internally — has `generatedIds` equal to `[id1, id2]`, exactly the two ids `createOrder()` returned, proving the whole chain (test-only override, transparent injection into production code, direct test inspection) worked correctly.

```
ProductionConfig: orderIdGenerator (plain), orderService(needs OrderIdGenerator)
TestOnlyConfig:   recordingIdGenerator (@Primary, extends OrderIdGenerator)

wiring: orderService's OrderIdGenerator dependency -> resolves to @Primary RecordingIdGenerator
test constructor: (OrderService, RecordingIdGenerator) -> both resolve, RecordingIdGenerator is the SAME instance

createOrder() -> RecordingIdGenerator.next() -> records id -> generatedIds grows
test asserts generatedIds matches the ids actually returned
```

## 7. Gotchas & takeaways

> Gotcha: field injection (`@Autowired` on a field) requires either a no-args constructor or, for JUnit 5 in default per-method test instance lifecycle, works transparently — but mixing `@TestConstructor` constructor injection with `@PER_CLASS` test instance lifecycle or certain other JUnit 5 lifecycle configurations can interact in non-obvious ways. When constructor injection behaves unexpectedly, checking the test instance lifecycle mode is often the fastest way to diagnose it.

- `@Autowired` in tests uses the exact same resolution rules (by type, `@Qualifier` to disambiguate) as application code — nothing test-specific about the mechanism itself, only about what it's injecting into.
- Method-parameter injection (via `SpringExtension`'s `ParameterResolver` support) scopes a bean to one test method rather than the whole class, useful when only a single test needs a particular collaborator.
- `@TestConstructor(autowireMode = ALL)` enables constructor injection for test classes, letting test fixture fields be `final` — an immutability benefit over field injection, at the cost of a slightly less familiar pattern for teams used to field-based test injection.
- Layering a `@Primary` test-only bean (like a recording spy extending the real type) over production configuration is a clean way to both exercise real wiring *and* directly inspect what happened during a test, without adding any test-awareness to production code.
