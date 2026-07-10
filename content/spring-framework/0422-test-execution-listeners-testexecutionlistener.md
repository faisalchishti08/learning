---
card: spring-framework
gi: 422
slug: test-execution-listeners-testexecutionlistener
title: "Test execution listeners (TestExecutionListener)"
---

## 1. What it is

`TestExecutionListener` is the extension interface underneath everything the TestContext Framework does around a test method — `DependencyInjectionTestExecutionListener` (populates `@Autowired` fields), `TransactionalTestExecutionListener` (`@Transactional` rollback), and `SqlScriptsTestExecutionListener` (`@Sql` scripts) are all just implementations of this one interface, registered in an ordered chain. You can write and register your own to hook into the same lifecycle for cross-cutting test concerns of your own.

```java
class TimingTestExecutionListener implements TestExecutionListener {
    @Override
    public void beforeTestMethod(TestContext testContext) {
        testContext.setAttribute("start", System.nanoTime());
    }
    @Override
    public void afterTestMethod(TestContext testContext) {
        long elapsed = System.nanoTime() - (long) testContext.getAttribute("start");
        System.out.println(testContext.getTestMethod().getName() + " took " + elapsed / 1_000_000 + "ms");
    }
}
```

## 2. Why & when

The built-in listeners cover the common cases, but a project often has its own cross-cutting test concerns: logging test timing, resetting a shared external fixture (a WireMock server, a test message queue) between tests, capturing diagnostic output only when a test fails, or applying an organization-specific convention automatically across every test class. Writing this as a `TestExecutionListener` means it applies uniformly, in the right lifecycle position relative to the framework's own listeners, without every test class needing to remember to call some setup/teardown method manually.

Reach for a custom `TestExecutionListener` when:

- You have test setup/teardown logic that should apply consistently across many test classes, and copy-pasting a `@BeforeEach`/`@AfterEach` into every one of them would be error-prone or easy to forget.
- You need to hook into a lifecycle point `@BeforeEach`/`@AfterEach` can't reach cleanly — before/after the *entire test class* (not just each method), or with access to the `TestContext`'s `ApplicationContext` and test outcome information.
- You're building reusable test infrastructure for a team or organization (a base annotation bundling several listeners) rather than one-off logic for a single test class.

## 3. Core concept

```
 interface TestExecutionListener {
     void beforeTestClass(TestContext tc)
     void prepareTestInstance(TestContext tc)
     void beforeTestMethod(TestContext tc)
     void beforeTestExecution(TestContext tc)
     void afterTestExecution(TestContext tc)
     void afterTestMethod(TestContext tc)
     void afterTestClass(TestContext tc)
 }
        |
        v
 TestContextManager holds an ORDERED LIST of listeners:
   [ ServletTestExecutionListener,
     DirtiesContextBeforeModesTestExecutionListener,
     DependencyInjectionTestExecutionListener,
     DirtiesContextTestExecutionListener,
     TransactionalTestExecutionListener,
     SqlScriptsTestExecutionListener,
     ... your custom listener(s), if registered ...
   ]
        |
        v
 for each lifecycle event, EVERY listener's corresponding method
 is invoked, in order (reverse order for the "after" callbacks)
```

Each method on the interface has a default no-op implementation (it's declared with `default` methods), so a custom listener only needs to override the specific lifecycle hooks it actually cares about.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TestContextManager invokes an ordered chain of listeners around each test method, including a custom one">
  <rect x="10" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">beforeTestMethod</text>

  <rect x="240" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="315" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Test runs</text>

  <rect x="470" y="70" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">afterTestMethod</text>

  <line x1="160" y1="95" x2="235" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="390" y1="95" x2="465" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">every registered listener's corresponding method fires, in order</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Your custom listener slots into this same before/after bracket around every test method.

## 5. Runnable example

### Level 1 — Basic

A minimal custom `TestExecutionListener` that logs entry and exit of every test method, registered explicitly via `@TestExecutionListeners`.

```java
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.*;
import org.springframework.test.context.TestContext;
import org.springframework.test.context.TestExecutionListener;
import org.springframework.test.context.TestExecutionListeners;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.test.context.support.DependencyInjectionTestExecutionListener;

public class ListenerBasic {

    static class LoggingTestExecutionListener implements TestExecutionListener {
        @Override
        public void beforeTestMethod(TestContext testContext) {
            System.out.println(">>> Starting: " + testContext.getTestMethod().getName());
        }

        @Override
        public void afterTestMethod(TestContext testContext) {
            System.out.println("<<< Finished: " + testContext.getTestMethod().getName());
        }
    }

    @Configuration
    static class Config {}

    @SpringJUnitConfig(Config.class)
    @TestExecutionListeners({
            DependencyInjectionTestExecutionListener.class, // keep the default DI behavior
            LoggingTestExecutionListener.class               // add our custom one
    })
    static class ExampleTest {
        @Test
        void doesSomething() {
            System.out.println("    (test body running)");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(ExampleTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: add `spring-test`, `spring-context`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java ListenerBasic.java`. Expect `">>> Starting..."`, then the test body's print, then `"<<< Finished..."`.

`@TestExecutionListeners({...})` explicitly replaces the framework's default listener set with exactly the ones listed — which is why `DependencyInjectionTestExecutionListener` is included explicitly even though we're not using `@Autowired` here, to illustrate that omitting a default listener genuinely disables its behavior, not just adds to it (covered further in Level 2).

### Level 2 — Intermediate

Use `mergeMode = MergeMode.MERGE_WITH_DEFAULTS` to *add* a custom listener alongside the framework's defaults instead of replacing them, and demonstrate a listener that captures per-test timing using `TestContext`'s attribute storage to pass data between lifecycle callbacks.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.TestContext;
import org.springframework.test.context.TestExecutionListener;
import org.springframework.test.context.TestExecutionListeners;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class ListenerIntermediate {

    static class GreetingService {
        String greet(String name) {
            try { Thread.sleep(20); } catch (InterruptedException ignored) {}
            return "Hello, " + name;
        }
    }

    static class TimingTestExecutionListener implements TestExecutionListener {
        @Override
        public void beforeTestMethod(TestContext testContext) {
            testContext.setAttribute("startNanos", System.nanoTime());
        }

        @Override
        public void afterTestMethod(TestContext testContext) {
            long start = (long) testContext.getAttribute("startNanos");
            long elapsedMs = (System.nanoTime() - start) / 1_000_000;
            System.out.println(testContext.getTestMethod().getName() + " took " + elapsedMs + "ms");
        }
    }

    @Configuration
    static class Config {
        @Bean GreetingService greetingService() { return new GreetingService(); }
    }

    @SpringJUnitConfig(Config.class)
    @TestExecutionListeners(
            listeners = TimingTestExecutionListener.class,
            mergeMode = TestExecutionListeners.MergeMode.MERGE_WITH_DEFAULTS // ADDS to defaults, doesn't replace
    )
    static class TimedTest {
        @Autowired GreetingService greetingService; // still works: DependencyInjectionTestExecutionListener still runs

        @Test
        void greetingIsTimed() {
            String result = greetingService.greet("Ada");
            System.out.println("Result: " + result);
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(TimedTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: same dependencies as Level 1, then `java ListenerIntermediate.java`.

`mergeMode = MERGE_WITH_DEFAULTS` keeps the framework's built-in listeners (including `DependencyInjectionTestExecutionListener`, which is why `@Autowired GreetingService` still works) while *adding* `TimingTestExecutionListener` to the chain, rather than replacing the whole set as Level 1 did explicitly. `testContext.setAttribute(...)`/`getAttribute(...)` is the mechanism for passing data between a listener's own `before*` and `after*` callbacks — the `TestContext` object is the same instance across a test method's full lifecycle.

### Level 3 — Advanced

A listener that captures diagnostic state specifically when a test *fails* (not on every run), using `TestContext.getTestException()` — useful for dumping extra debugging context (like a snapshot of a mutable bean's state) only when something actually goes wrong, keeping passing-test output clean.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.TestContext;
import org.springframework.test.context.TestExecutionListener;
import org.springframework.test.context.TestExecutionListeners;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.util.ArrayList;
import java.util.List;

public class ListenerAdvanced {

    static class OrderQueue {
        List<String> pending = new ArrayList<>();
        void add(String order) { pending.add(order); }
    }

    static class FailureDiagnosticsListener implements TestExecutionListener {
        @Override
        public void afterTestMethod(TestContext testContext) {
            Throwable failure = testContext.getTestException();
            if (failure != null) {
                System.out.println("=== TEST FAILED: " + testContext.getTestMethod().getName() + " ===");
                System.out.println("Failure: " + failure.getMessage());

                // Dump extra diagnostic state from the ApplicationContext, only because it failed.
                OrderQueue queue = testContext.getApplicationContext().getBean(OrderQueue.class);
                System.out.println("OrderQueue state at time of failure: " + queue.pending);
                System.out.println("=====================================");
            }
        }
    }

    @Configuration
    static class Config {
        @Bean OrderQueue orderQueue() { return new OrderQueue(); }
    }

    @SpringJUnitConfig(Config.class)
    @TestExecutionListeners(
            listeners = FailureDiagnosticsListener.class,
            mergeMode = TestExecutionListeners.MergeMode.MERGE_WITH_DEFAULTS
    )
    static class DiagnosticsTest {
        @Autowired OrderQueue orderQueue;

        @Test
        void aPassingTestProducesNoExtraOutput() {
            orderQueue.add("order-1");
            System.out.println("aPassingTestProducesNoExtraOutput ran normally");
        }

        @Test
        void aFailingTestTriggersDiagnostics() {
            orderQueue.add("order-2");
            orderQueue.add("order-3");
            throw new AssertionError("Deliberately failing to demonstrate the diagnostics listener");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(DiagnosticsTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        System.out.println("Test run summary: " + listener.getSummary().getTestsFailedCount() + " failed, "
                + listener.getSummary().getTestsSucceededCount() + " succeeded (this failure was expected).");
    }
}
```

How to run: same dependencies as Level 1, then `java ListenerAdvanced.java`.

`testContext.getTestException()` returns `null` for a passing test (so `aPassingTestProducesNoExtraOutput` produces no diagnostic output at all) and the actual thrown exception for a failing one — `FailureDiagnosticsListener` uses this to conditionally dump extra state (the `OrderQueue`'s contents at the moment of failure) only when it's actually useful, via `testContext.getApplicationContext().getBean(...)` to reach directly into the test's live Spring context from inside the listener.

## 6. Walkthrough

Trace `ListenerAdvanced.DiagnosticsTest.aFailingTestTriggersDiagnostics()`:

1. **Before-method phase.** The framework's default listeners run their `beforeTestMethod` callbacks (dependency injection populates `orderQueue`); `FailureDiagnosticsListener` has no `beforeTestMethod` override, so nothing happens for it at this point.
2. **Test body executes.** `orderQueue.add("order-2")` and `orderQueue.add("order-3")` run, mutating the shared `OrderQueue` bean's `pending` list to `["order-2", "order-3"]`.
3. **Assertion throws.** `throw new AssertionError(...)` propagates out of the test method — JUnit 5 catches this and records the test as failed, but the TestContext Framework's `afterTestMethod` phase still runs regardless of pass/fail (this is a deliberate framework guarantee, the same guarantee that makes `@Transactional` rollback work correctly even on a failing test).
4. **`afterTestMethod` phase runs, in listener order.** Each registered listener's `afterTestMethod` fires; when it's `FailureDiagnosticsListener`'s turn, `testContext.getTestException()` returns the `AssertionError` thrown in step 3 (non-null, since the test failed).
5. **Diagnostic dump.** Because `failure != null`, the listener prints the failure message and then calls `testContext.getApplicationContext().getBean(OrderQueue.class)` — retrieving the *exact same* `OrderQueue` singleton instance the test itself used — and prints its `pending` list, showing `["order-2", "order-3"]` exactly as it stood at the moment of failure.
6. **Contrast with the passing test.** For `aPassingTestProducesNoExtraOutput`, the same `afterTestMethod` callback runs, but `testContext.getTestException()` returns `null` (no failure), so the `if` block is skipped entirely — no diagnostic noise for a test that didn't need it.

```
aFailingTestTriggersDiagnostics()
   beforeTestMethod: inject orderQueue
   test body: orderQueue.add("order-2"), add("order-3") -> throw AssertionError
   afterTestMethod (framework's other listeners): run as normal
   afterTestMethod (FailureDiagnosticsListener):
        getTestException() -> AssertionError (non-null)
        -> print failure message
        -> getBean(OrderQueue.class) -> pending == ["order-2", "order-3"]
        -> print diagnostic dump
```

## 7. Gotchas & takeaways

> Gotcha: `@TestExecutionListeners({...})` with the default `mergeMode` (`MergeMode.REPLACE_DEFAULTS`) silently disables every built-in listener not explicitly re-listed — a test class adding a custom listener this way can unexpectedly lose `@Autowired` injection, `@Transactional` rollback, or `@Sql` script execution if those listeners aren't included in the explicit list. Use `mergeMode = MergeMode.MERGE_WITH_DEFAULTS` (Levels 2–3) unless you specifically intend to replace the framework's default behavior entirely.

- `TestExecutionListener` is the extension point underneath every built-in test feature (`@Autowired` injection, `@Transactional` rollback, `@Sql` scripts) — writing your own lets you add project-specific cross-cutting test behavior using the same mechanism.
- Each interface method has a no-op default, so a custom listener only needs to override the specific lifecycle hooks (`beforeTestMethod`, `afterTestMethod`, `beforeTestClass`, etc.) it actually needs.
- `TestContext.setAttribute`/`getAttribute` lets a listener pass data between its own before- and after-phase callbacks, since the same `TestContext` instance persists across a test method's lifecycle.
- `TestContext.getTestException()` is `null` for a passing test and the actual failure for a failing one — the standard way to write diagnostics-on-failure-only listeners without cluttering passing-test output.
