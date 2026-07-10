---
card: spring-framework
gi: 415
slug: applicationcontext-caching-in-tests
title: "ApplicationContext caching in tests"
---

## 1. What it is

`ApplicationContext` caching is the TestContext Framework's optimization of reusing an already-built `ApplicationContext` across multiple test classes, instead of constructing a fresh one for every test class that needs Spring wiring. The framework computes a **cache key** from everything that affects how a context would be built (configuration classes, active profiles, property sources, context customizers, and more) — two test classes with an identical key share the exact same context instance.

```java
@SpringJUnitConfig(AppConfig.class)
class FirstTest { /* uses the context built from AppConfig */ }

@SpringJUnitConfig(AppConfig.class)  // IDENTICAL key -- reuses the SAME context as FirstTest
class SecondTest { /* gets the cached context, no rebuild */ }
```

## 2. Why & when

Building an `ApplicationContext` isn't free — component scanning, bean instantiation, `@PostConstruct` callbacks, potentially opening real (if embedded) database connections all take real time. A test suite with hundreds of integration test classes, each rebuilding an equivalent context from scratch, could spend most of its runtime on context construction rather than actually running assertions. Context caching exists specifically to make that non-issue: as long as two test classes ask for configuration that produces an identical cache key, the framework reuses the same context, and the expensive construction work happens once regardless of how many test classes share that configuration.

Understanding this matters because it explains real, sometimes surprising test-suite behavior:

- Why a large integration test suite with consistent configuration (many test classes pointing at the same `@ContextConfiguration`) can run much faster than the naive per-class cost would suggest.
- Why a seemingly tiny configuration difference between two test classes (a different active profile, a different property override) can silently double your context-build count, because it produces a different cache key.
- Why `@DirtiesContext` (its own card) exists at all — it's the deliberate escape hatch for the rare case where a test *mutates* shared context state in a way that would corrupt the next test reusing that same cached context.

## 3. Core concept

```
 Test class A: @ContextConfiguration(classes=X.class)
 Test class B: @ContextConfiguration(classes=X.class)          -> SAME key -> SAME cached context
 Test class C: @ContextConfiguration(classes=X.class, profiles="dev")  -> DIFFERENT key -> new context
 Test class D: @ContextConfiguration(classes=Y.class)            -> DIFFERENT key -> new context

               Context cache (keyed by MergedContextConfiguration)
        key(A) == key(B)  -->  one shared ApplicationContext instance
        key(C)             -->  its own separate ApplicationContext instance
        key(D)             -->  its own separate ApplicationContext instance
```

The cache key isn't just "which configuration class" — it includes active profiles, property sources, context initializers, and several other factors, all of which must match exactly for two test classes to share a context.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple test classes with matching configuration share one cached context; a differing profile gets its own">
  <rect x="10" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="85" y="44" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Test A (no profile)</text>

  <rect x="10" y="70" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="85" y="94" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Test B (no profile)</text>

  <rect x="10" y="120" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="85" y="144" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Test C (profile=dev)</text>

  <rect x="280" y="45" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="73" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Cached context #1</text>

  <rect x="280" y="115" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="143" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Separate context #2</text>

  <line x1="160" y1="40" x2="275" y2="60" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="160" y1="90" x2="275" y2="68" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="160" y1="140" x2="275" y2="138" stroke="#8b949e" stroke-width="1.5"/>
</svg>

Only an exact configuration match reuses a cached context — even one differing detail (like an active profile) forces a separate build.

## 5. Runnable example

### Level 1 — Basic

Two test classes with identical `@SpringJUnitConfig` configuration, proving via a bean's constructor side effect that the context (and therefore the bean) is built only once and shared.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class ContextCachingBasic {

    static int constructionCount = 0;

    static class Widget {
        Widget() { constructionCount++; }
    }

    @Configuration
    static class Config {
        @Bean
        Widget widget() { return new Widget(); }
    }

    @SpringJUnitConfig(Config.class)
    static class FirstTest {
        @Autowired Widget widget;
        @Test void test1() { System.out.println("FirstTest sees widget: " + System.identityHashCode(widget)); }
    }

    @SpringJUnitConfig(Config.class)
    static class SecondTest {
        @Autowired Widget widget;
        @Test void test2() { System.out.println("SecondTest sees widget: " + System.identityHashCode(widget)); }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(FirstTest.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(SecondTest.class))
                .build();
        launcher.execute(request);

        System.out.println("Widget constructed " + constructionCount + " time(s) across both test classes.");
        if (constructionCount != 1) throw new AssertionError("Expected exactly 1 construction, got " + constructionCount);
        System.out.println("Context caching confirmed -- PASS");
    }
}
```

How to run: add `spring-test`, `spring-context`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java ContextCachingBasic.java`.

Even though `FirstTest` and `SecondTest` are separate classes running separate `@Test` methods, `constructionCount` ends at `1`, not `2` — the TestContext Framework recognized both classes' `@SpringJUnitConfig(Config.class)` as producing an identical cache key and reused the same `ApplicationContext` (and therefore the same singleton `Widget` bean) for both.

### Level 2 — Intermediate

Vary the active profile between two otherwise-identical test classes, showing that this single difference is enough to force two separate context builds — the cache key includes more than just the configuration class list.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class ContextCachingIntermediate {

    static int contextBuildCount = 0;

    static class ContextMarker {
        ContextMarker() { contextBuildCount++; }
    }

    @Configuration
    static class Config {
        @Bean
        ContextMarker contextMarker() { return new ContextMarker(); }
    }

    @SpringJUnitConfig(Config.class)
    static class NoProfileTest {
        @Autowired ContextMarker marker;
        @Test void test1() { System.out.println("NoProfileTest marker: " + System.identityHashCode(marker)); }
    }

    @SpringJUnitConfig(Config.class)
    @ActiveProfiles("dev") // this ONE difference changes the cache key
    static class DevProfileTest {
        @Autowired ContextMarker marker;
        @Test void test2() { System.out.println("DevProfileTest marker: " + System.identityHashCode(marker)); }
    }

    @SpringJUnitConfig(Config.class) // no profile again -- matches NoProfileTest's key
    static class AnotherNoProfileTest {
        @Autowired ContextMarker marker;
        @Test void test3() { System.out.println("AnotherNoProfileTest marker: " + System.identityHashCode(marker)); }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(NoProfileTest.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(DevProfileTest.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(AnotherNoProfileTest.class))
                .build();
        launcher.execute(request);

        System.out.println("Total contexts built: " + contextBuildCount);
        if (contextBuildCount != 2) throw new AssertionError("Expected exactly 2 context builds, got " + contextBuildCount);
        System.out.println("Confirmed: NoProfileTest + AnotherNoProfileTest shared one context;"
                + " DevProfileTest's differing profile forced a second -- PASS");
    }
}
```

How to run: same dependencies as Level 1, then `java ContextCachingIntermediate.java`.

`contextBuildCount` ends at `2`, not `1` or `3` — `NoProfileTest` and `AnotherNoProfileTest` share a cached context (identical key: same configuration class, no active profile), while `DevProfileTest`'s `@ActiveProfiles("dev")` produces a genuinely different cache key, forcing its own separate context build even though it uses the exact same `Config` class. This is the concrete mechanism behind the earlier warning that a "tiny" configuration difference can silently double your context-build count across a large test suite.

### Level 3 — Advanced

Observe the cache's size limit and eviction behavior: Spring's default context cache has a maximum size (32 by default, though configurable), and once exceeded, the least-recently-used context is evicted and closed — demonstrated here by deliberately creating more distinct configurations than the cache can hold, using a small custom-sized cache via the `spring.test.context.cache.maxSize` system property.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.context.event.ContextClosedEvent;
import org.springframework.context.event.EventListener;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class ContextCachingAdvanced {

    static int closedContextCount = 0;

    @Configuration
    static class Config {
        @Bean
        Object marker() { return new Object(); }

        @EventListener(ContextClosedEvent.class)
        void onClose() {
            closedContextCount++;
            System.out.println("A cached context was evicted and closed. Total closed: " + closedContextCount);
        }
    }

    // Each of these has a DIFFERENT property value, so each gets its OWN cache entry.
    @SpringJUnitConfig(Config.class)
    @TestPropertySource(properties = "app.instance=1")
    static class Variant1 { @Test void t() {} }

    @SpringJUnitConfig(Config.class)
    @TestPropertySource(properties = "app.instance=2")
    static class Variant2 { @Test void t() {} }

    @SpringJUnitConfig(Config.class)
    @TestPropertySource(properties = "app.instance=3")
    static class Variant3 { @Test void t() {} }

    public static void main(String[] args) {
        // Force a tiny cache size to make eviction observable without creating 32+ variants.
        System.setProperty("spring.test.context.cache.maxSize", "2");

        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(Variant1.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(Variant2.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(Variant3.class))
                .build();
        launcher.execute(request);

        System.out.println("With cache maxSize=2 and 3 distinct configurations, "
                + "at least one context had to be evicted before all tests finished.");
        System.out.println("Contexts closed during the run: " + closedContextCount);
    }
}
```

How to run: same dependencies as Level 1, then `java ContextCachingAdvanced.java`.

Three test classes, three distinct `@TestPropertySource` values, means three distinct cache keys — with the cache capped at `maxSize=2` (via the `spring.test.context.cache.maxSize` system property), the framework can hold at most two contexts simultaneously; loading the third forces it to evict and close the least-recently-used one, which the `@EventListener(ContextClosedEvent.class)` bean detects and counts. In a real test suite with the default `maxSize` of 32, this eviction only becomes relevant once you have more than 32 distinct configurations in play — but the mechanism is exactly what protects a large suite from unbounded memory growth as it accumulates cached contexts over its full run.

## 6. Walkthrough

Trace `ContextCachingAdvanced.main`'s run across its three test classes, assuming they execute in declared order:

1. **`Variant1` runs.** Its cache key (configuration class + `app.instance=1` property) is new, so the framework builds a fresh `ApplicationContext`. The cache now holds 1 entry (within the `maxSize=2` limit).
2. **`Variant2` runs.** Its cache key (`app.instance=2`) is also new and different from `Variant1`'s. The framework builds a second context. The cache now holds 2 entries — exactly at the configured limit.
3. **`Variant3` runs.** Its cache key (`app.instance=3`) is new again — a third, distinct configuration. Building it would exceed `maxSize=2`, so before (or as part of) adding this third context, the framework evicts the least-recently-used cached entry — `Variant1`'s context, since it hasn't been touched since step 1 — and closes it.
4. **Eviction triggers `ContextClosedEvent`.** Closing `Variant1`'s context publishes a `ContextClosedEvent` within that context; the `Config` bean's `@EventListener(ContextClosedEvent.class)` method fires, incrementing `closedContextCount` and printing the eviction notice — but only within *that specific context instance*, since each cached context has its own independent set of beans and listeners.
5. **`Variant3`'s context is built and cached**, bringing the cache back to 2 entries (`Variant2` and `Variant3`), with `Variant1`'s now permanently evicted and unavailable for reuse — a hypothetical fourth test class matching `Variant1`'s old configuration would have to rebuild it from scratch.
6. **Final count.** By the end of the run, `closedContextCount` reflects however many evictions occurred during the process — with exactly 3 distinct configurations and a cap of 2, at least one eviction is guaranteed, though the exact count can depend on execution order and any remaining contexts the test framework closes at JVM shutdown.

```
maxSize = 2

Variant1 (instance=1) -> new context -> cache: [V1]
Variant2 (instance=2) -> new context -> cache: [V1, V2]           (at capacity)
Variant3 (instance=3) -> new context needed -> evict LRU (V1) -> cache: [V2, V3]
                                              -> V1's ContextClosedEvent fires
```

## 7. Gotchas & takeaways

> Gotcha: a large test suite with many *slightly* different configurations (different `@TestPropertySource` values, different active profile combinations, different mock bean setups via `@MockBean` in Spring Boot) can silently defeat context caching almost entirely — each variant gets its own cache entry, and if the number of distinct variants exceeds `maxSize`, contexts start being evicted and rebuilt repeatedly across the suite, quietly turning what looked like a well-cached test suite into one paying near-full context-build cost anyway. Standardizing test configuration (fewer distinct property/profile combinations across test classes) is a direct lever for keeping a large suite fast.

- Context caching reuses an `ApplicationContext` across test classes whose full configuration (classes, profiles, properties, and more) produces an identical cache key — it's what keeps a large integration test suite's runtime from scaling linearly with test class count.
- Any difference in configuration — even a single property value or active profile — produces a different cache key and forces a separate context build, so minimizing unnecessary configuration variation across test classes directly improves suite speed.
- The cache has a bounded size (default 32, configurable via `spring.test.context.cache.maxSize`); exceeding it evicts the least-recently-used context, which can reintroduce rebuild cost for suites with many distinct configurations.
- `@DirtiesContext` (a separate card) is the explicit override for tests that mutate shared context state in ways that would corrupt reuse — reach for it only when a test genuinely needs a guaranteed-fresh context, since it opts that test (and potentially subsequent ones) out of caching's performance benefit.
