---
card: spring-framework
gi: 426
slug: context-customizers
title: "Context customizers"
---

## 1. What it is

A `ContextCustomizer` is a hook that lets you programmatically modify a test's `ConfigurableApplicationContext` right before it's refreshed — registering extra beans, adding property sources, or applying any other `BeanFactory`/`Environment`-level customization that doesn't fit cleanly into a declarative annotation. `ContextCustomizerFactory` is the companion interface that inspects a test class and decides whether (and how) to produce a customizer for it, and critically, participates in the context cache key so customizations that differ between test classes correctly force separate context builds.

```java
class MetricsContextCustomizer implements ContextCustomizer {
    @Override
    public void customizeContext(ConfigurableApplicationContext context, MergedContextConfiguration mergedConfig) {
        context.getBeanFactory().registerSingleton("testMetricsRegistry", new SimpleMeterRegistry());
    }
}
```

## 2. Why & when

Most test customization needs are covered by existing annotations (`@TestPropertySource`, `@ActiveProfiles`, `@Sql`), but occasionally you need something more programmatic: registering a bean built from logic too complex to express as a static `@Bean` method conveniently reusable across many test classes, or building custom test infrastructure (like Spring Boot's own `@MockBean`/`@SpyBean` support, which is itself implemented via this exact mechanism) that needs to hook directly into context construction. `ContextCustomizer`/`ContextCustomizerFactory` is that lower-level extension point — it's what several of Spring Boot's own testing annotations are built on top of.

Reach for a custom `ContextCustomizer` when:

- Building reusable test infrastructure meant to apply automatically based on some marker (an annotation, a naming convention) across many test classes, without each one repeating boilerplate `@Bean` methods.
- You need programmatic control over context construction that a declarative annotation can't express cleanly — conditionally registering beans based on complex logic, or customizing the `Environment`/`BeanFactory` directly.
- You're building a testing library or framework extension (similar in spirit to how Spring Boot's own test slice annotations work) meant to be reused across projects.

For most day-to-day test authoring, the existing declarative annotations (covered in earlier cards) cover the common cases — reach for a custom `ContextCustomizer` specifically when you're building reusable test infrastructure, not for one-off test-specific needs.

## 3. Core concept

```
 Test class
        |
        v
 ContextCustomizerFactory.createContextCustomizer(testClass, configAttributes)
        |
        | returns a ContextCustomizer, or null if not applicable to this test class
        v
 ContextCustomizer becomes part of the MergedContextConfiguration
   (participates in the CACHE KEY -- two test classes with different
    customizers get different cache entries, even with identical @ContextConfiguration)
        |
        v
 during context loading, AFTER beans are registered but BEFORE refresh():
        |
        v
 customizer.customizeContext(context, mergedConfig)
        |
        | can register extra singletons, modify the Environment,
        | add BeanFactoryPostProcessors, etc.
        v
 context.refresh() completes with the customization applied
```

Because the customizer is part of the cache key, the framework correctly treats two test classes with different customizations as needing separate contexts, even if their `@ContextConfiguration` classes are otherwise identical — this is exactly the mechanism that lets something like Spring Boot's `@MockBean` (different mocked beans between test classes) coexist correctly with context caching.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ContextCustomizerFactory produces a customizer that modifies the context before refresh and participates in the cache key">
  <rect x="10" y="20" width="180" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ContextCustomizerFactory</text>

  <rect x="240" y="20" width="180" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ContextCustomizer</text>

  <rect x="470" y="20" width="160" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">customizeContext(...)</text>

  <rect x="240" y="110" width="180" height="44" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="137" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">part of the cache key</text>

  <line x1="190" y1="42" x2="235" y2="42" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="42" x2="465" y2="42" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="330" y1="64" x2="330" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The customizer both modifies the context and, by becoming part of the cache key, correctly prevents cache collisions between differently-customized test classes.

## 5. Runnable example

### Level 1 — Basic

A minimal `ContextCustomizer` that registers an extra singleton bean directly into the `BeanFactory`, applied via `ContextCustomizerFactories`.

```java
import org.junit.jupiter.api.Test;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.*;
import org.springframework.test.context.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.util.List;

public class ContextCustomizerBasic {

    static class TestClock {
        long fixedMillis = 1_700_000_000_000L; // a fixed instant, useful for deterministic tests
    }

    static class SingletonRegisteringCustomizer implements ContextCustomizer {
        @Override
        public void customizeContext(ConfigurableApplicationContext context, MergedContextConfiguration mergedConfig) {
            context.getBeanFactory().registerSingleton("testClock", new TestClock());
        }

        @Override
        public boolean equals(Object obj) { return obj instanceof SingletonRegisteringCustomizer; }
        @Override
        public int hashCode() { return SingletonRegisteringCustomizer.class.hashCode(); }
    }

    static class SingletonRegisteringCustomizerFactory implements ContextCustomizerFactory {
        @Override
        public ContextCustomizer createContextCustomizer(Class<?> testClass,
                                                           List<ContextConfigurationAttributes> configAttributes) {
            return new SingletonRegisteringCustomizer();
        }
    }

    @Configuration
    static class Config {}

    @SpringJUnitConfig(Config.class)
    @ContextCustomizerFactories(SingletonRegisteringCustomizerFactory.class)
    static class ClockTest {
        @org.springframework.beans.factory.annotation.Autowired
        TestClock testClock; // never declared as a @Bean in Config -- registered by the customizer instead

        @Test
        void customizerRegisteredTheBean() {
            System.out.println("testClock.fixedMillis = " + testClock.fixedMillis);
            if (testClock.fixedMillis != 1_700_000_000_000L) throw new AssertionError("Unexpected value");
            System.out.println("customizerRegisteredTheBean -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(ClockTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: add `spring-test`, `spring-context`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java ContextCustomizerBasic.java`.

`TestClock` is never declared as a `@Bean` anywhere in `Config` — it's registered directly into the `BeanFactory` by `SingletonRegisteringCustomizer.customizeContext(...)`, called by the framework as part of context construction because `@ContextCustomizerFactories` points at a factory that produces this customizer. Overriding `equals`/`hashCode` on the customizer matters because these are used when computing the context cache key, covered next.

### Level 2 — Intermediate

Demonstrate the cache-key participation directly: two test classes with identical `@ContextConfiguration` but *different* customizers get separate cached contexts, exactly mirroring how a differing `@TestPropertySource` value would (from the context-caching card).

```java
import org.junit.jupiter.api.Test;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.*;
import org.springframework.test.context.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.util.List;
import java.util.Objects;

public class ContextCustomizerIntermediate {

    static int contextBuildCount = 0;

    static class BuildCounter {
        BuildCounter() { contextBuildCount++; }
    }

    static class LabelingCustomizer implements ContextCustomizer {
        private final String label;
        LabelingCustomizer(String label) { this.label = label; }

        @Override
        public void customizeContext(ConfigurableApplicationContext context, MergedContextConfiguration mergedConfig) {
            context.getBeanFactory().registerSingleton("customizerLabel", label);
        }

        @Override
        public boolean equals(Object obj) {
            return obj instanceof LabelingCustomizer other && Objects.equals(this.label, other.label);
        }
        @Override
        public int hashCode() { return label.hashCode(); }
    }

    static class AlphaCustomizerFactory implements ContextCustomizerFactory {
        @Override
        public ContextCustomizer createContextCustomizer(Class<?> testClass, List<ContextConfigurationAttributes> attrs) {
            return new LabelingCustomizer("alpha");
        }
    }

    static class BetaCustomizerFactory implements ContextCustomizerFactory {
        @Override
        public ContextCustomizer createContextCustomizer(Class<?> testClass, List<ContextConfigurationAttributes> attrs) {
            return new LabelingCustomizer("beta");
        }
    }

    @Configuration
    static class Config {
        @Bean BuildCounter buildCounter() { return new BuildCounter(); }
    }

    @SpringJUnitConfig(Config.class)
    @ContextCustomizerFactories(AlphaCustomizerFactory.class)
    static class AlphaTest {
        @org.springframework.beans.factory.annotation.Autowired String customizerLabel;
        @Test void checkLabel() { System.out.println("AlphaTest label: " + customizerLabel); }
    }

    @SpringJUnitConfig(Config.class) // SAME configuration class as AlphaTest
    @ContextCustomizerFactories(BetaCustomizerFactory.class) // but a DIFFERENT customizer
    static class BetaTest {
        @org.springframework.beans.factory.annotation.Autowired String customizerLabel;
        @Test void checkLabel() { System.out.println("BetaTest label: " + customizerLabel); }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(AlphaTest.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(BetaTest.class))
                .build();
        launcher.execute(request);

        System.out.println("Total contexts built: " + contextBuildCount);
        if (contextBuildCount != 2) throw new AssertionError("Expected 2 (different customizers forced separate contexts), got " + contextBuildCount);
        System.out.println("Confirmed: different customizers correctly produced different cache entries -- PASS");
    }
}
```

How to run: same dependencies as Level 1, then `java ContextCustomizerIntermediate.java`.

`AlphaTest` and `BetaTest` both use `Config.class` — identical `@ContextConfiguration` — but their `@ContextCustomizerFactories` produce customizers with different `label` values, and `LabelingCustomizer.equals`/`hashCode` are defined by that `label`. This means the two test classes' `MergedContextConfiguration` cache keys genuinely differ, and `contextBuildCount` ends at `2`, proving the framework correctly avoided sharing a cached context between two test classes whose customizations meaningfully differ.

### Level 3 — Advanced

A `ContextCustomizerFactory` that inspects the test class for a custom marker annotation and conditionally produces a customizer only for classes that need it — the actual pattern reusable test infrastructure libraries use (similar in spirit to how Spring Boot's `@MockBean` support decides whether to activate at all for a given test class).

```java
import org.junit.jupiter.api.Test;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.*;
import org.springframework.core.annotation.AnnotatedElementUtils;
import org.springframework.test.context.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.lang.annotation.*;
import java.util.List;
import java.util.Objects;

public class ContextCustomizerAdvanced {

    @Target(ElementType.TYPE)
    @Retention(RetentionPolicy.RUNTIME)
    @interface WithFakeClock {
        long millis();
    }

    static class FakeClock {
        final long fixedMillis;
        FakeClock(long fixedMillis) { this.fixedMillis = fixedMillis; }
    }

    static class FakeClockCustomizer implements ContextCustomizer {
        private final long millis;
        FakeClockCustomizer(long millis) { this.millis = millis; }

        @Override
        public void customizeContext(ConfigurableApplicationContext context, MergedContextConfiguration mergedConfig) {
            context.getBeanFactory().registerSingleton("fakeClock", new FakeClock(millis));
        }

        @Override
        public boolean equals(Object obj) {
            return obj instanceof FakeClockCustomizer other && this.millis == other.millis;
        }
        @Override
        public int hashCode() { return Long.hashCode(millis); }
    }

    // Only activates for test classes actually annotated @WithFakeClock -- otherwise contributes nothing.
    static class FakeClockCustomizerFactory implements ContextCustomizerFactory {
        @Override
        public ContextCustomizer createContextCustomizer(Class<?> testClass, List<ContextConfigurationAttributes> attrs) {
            WithFakeClock annotation = AnnotatedElementUtils.findMergedAnnotation(testClass, WithFakeClock.class);
            if (annotation == null) {
                return null; // this test class doesn't want a fake clock -- no customization applied
            }
            return new FakeClockCustomizer(annotation.millis());
        }
    }

    @Configuration
    static class Config {}

    @SpringJUnitConfig(Config.class)
    @ContextCustomizerFactories(FakeClockCustomizerFactory.class)
    @WithFakeClock(millis = 1_700_000_000_000L)
    static class TestWithFakeClock {
        @org.springframework.beans.factory.annotation.Autowired FakeClock fakeClock;

        @Test
        void fakeClockWasRegistered() {
            System.out.println("fakeClock.fixedMillis = " + fakeClock.fixedMillis);
            if (fakeClock.fixedMillis != 1_700_000_000_000L) throw new AssertionError("Wrong fixed time");
            System.out.println("fakeClockWasRegistered -- PASS");
        }
    }

    @SpringJUnitConfig(Config.class)
    @ContextCustomizerFactories(FakeClockCustomizerFactory.class)
    // NOTE: no @WithFakeClock here -- the factory should produce NO customizer for this class
    static class TestWithoutFakeClock {
        @org.springframework.beans.factory.annotation.Autowired
        org.springframework.context.ApplicationContext context;

        @Test
        void noFakeClockIsRegistered() {
            boolean hasFakeClock = context.getBeanNamesForType(FakeClock.class).length > 0;
            System.out.println("FakeClock bean present: " + hasFakeClock);
            if (hasFakeClock) throw new AssertionError("Did NOT expect a FakeClock bean without @WithFakeClock");
            System.out.println("noFakeClockIsRegistered -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(TestWithFakeClock.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(TestWithoutFakeClock.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: same dependencies as Level 1, then `java ContextCustomizerAdvanced.java`.

`FakeClockCustomizerFactory.createContextCustomizer` returns `null` for any test class not annotated `@WithFakeClock` — the framework treats a `null` return as "this factory contributes nothing for this test class," so `TestWithoutFakeClock` genuinely gets no `FakeClock` bean at all. This conditional-activation pattern (inspect the test class, decide whether to contribute a customization) is exactly how reusable test-infrastructure libraries build annotation-driven features without requiring every test class using the base configuration to opt in explicitly to unrelated customizations.

## 6. Walkthrough

Trace `ContextCustomizerAdvanced.main`'s handling of the two contrasting test classes:

1. **Factory invoked for `TestWithFakeClock`.** As the framework prepares this class's `MergedContextConfiguration`, it calls `FakeClockCustomizerFactory.createContextCustomizer(TestWithFakeClock.class, ...)`. `AnnotatedElementUtils.findMergedAnnotation(testClass, WithFakeClock.class)` finds the `@WithFakeClock(millis = 1_700_000_000_000L)` annotation present on this class, so the factory returns a real `FakeClockCustomizer` configured with that value.
2. **Context built, customized.** During context construction, `customizeContext(...)` runs, registering a `FakeClock` singleton with `fixedMillis = 1_700_000_000_000L` directly into the `BeanFactory`.
3. **Test verifies.** `TestWithFakeClock.fakeClockWasRegistered()` receives the injected `FakeClock` and confirms its value matches what the annotation specified.
4. **Factory invoked for `TestWithoutFakeClock`.** The same factory is consulted again for this different test class. This time, `findMergedAnnotation(testClass, WithFakeClock.class)` finds nothing (this class has no `@WithFakeClock` annotation), so the factory returns `null`.
5. **No customization applied.** Because the factory returned `null` for this class, no `FakeClockCustomizer` becomes part of its `MergedContextConfiguration` at all — the context builds with exactly the beans `Config` declares, nothing more.
6. **Test verifies the negative.** `TestWithoutFakeClock.noFakeClockIsRegistered()` checks `context.getBeanNamesForType(FakeClock.class)` and finds it empty, confirming the factory's conditional logic correctly skipped customization for a class that didn't ask for it.

```
TestWithFakeClock:     @WithFakeClock present    -> factory returns FakeClockCustomizer -> FakeClock bean registered
TestWithoutFakeClock:  @WithFakeClock absent      -> factory returns null                -> no customization, no FakeClock bean
```

## 7. Gotchas & takeaways

> Gotcha: a `ContextCustomizer` implementation that doesn't correctly override `equals`/`hashCode` (or overrides them incorrectly) can silently corrupt context caching — two test classes that *should* share a cached context (because their customization is genuinely equivalent) end up with separate ones because the default `Object.equals` never considers them equal, or conversely, two test classes with *different* customization intent could incorrectly appear "equal" and wrongly share a context if `equals` is implemented too loosely. Always implement `equals`/`hashCode` based on whatever state actually determines the customizer's behavior, exactly as Level 2's `LabelingCustomizer` does with its `label` field.

- `ContextCustomizer`/`ContextCustomizerFactory` is the programmatic extension point underneath context construction — used for registering beans or applying customization too complex for a declarative annotation, and it's what several of Spring Boot's own test annotations are built on.
- A customizer becomes part of the test's context cache key, so correctly implementing `equals`/`hashCode` on it is essential for context caching to behave correctly across test classes with differing customizations.
- A `ContextCustomizerFactory` can return `null` to contribute nothing for a given test class, enabling conditional, annotation-driven activation — the standard pattern for building reusable, opt-in test infrastructure.
- Reach for this lower-level mechanism when building reusable test infrastructure meant to apply across many test classes; for one-off, test-specific needs, the declarative annotations from earlier cards are simpler and sufficient.
