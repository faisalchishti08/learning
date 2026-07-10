---
card: spring-framework
gi: 421
slug: dirtiescontext
title: "@DirtiesContext"
---

## 1. What it is

`@DirtiesContext` tells the TestContext Framework that a test has modified its `ApplicationContext` in a way that would corrupt it for reuse by later tests — a mutated singleton bean's internal state, a closed resource, anything not cleaned up by transaction rollback. When present, the framework removes that context from the cache after the annotated test (or class) runs, guaranteeing the next test needing an equivalent configuration gets a fresh, unmutated context instead of the tainted cached one.

```java
@Test
@DirtiesContext // this test mutates shared bean state -- don't let later tests reuse this context
void modifiesSharedCacheState() {
    someSingletonCache.evictAll(); // a permanent, non-transactional mutation
}
```

## 2. Why & when

Context caching (its own earlier card) is a significant performance win precisely because it assumes a cached context is safe to hand to the next test unchanged. That assumption breaks the moment a test mutates shared, non-transactional state — a singleton bean's mutable field, an in-memory counter, a closed connection pool — because the *next* test reusing that same cached context inherits whatever mess the previous test left behind, producing confusing, order-dependent failures that have nothing to do with the actual bug being tested. `@DirtiesContext` is the deliberate escape hatch: mark the specific test (or class) that causes this kind of pollution, and the framework evicts the tainted context rather than risking it being handed to another test.

Reach for `@DirtiesContext` when:

- A test mutates a singleton bean's internal, non-database state in a way that can't be undone by `@Transactional` rollback (which only covers database transactions, not arbitrary Java object state).
- A test closes, shuts down, or otherwise permanently alters an infrastructure bean (an embedded server, a connection pool) that other tests sharing the cached context would need intact.
- A test deliberately needs a completely fresh `ApplicationContext` for isolation reasons, even if nothing was technically mutated — occasionally useful, though this pattern trades away caching's performance benefit and should be used sparingly.

Overusing `@DirtiesContext` defeats the purpose of context caching — apply it narrowly, only to the specific tests that genuinely need it, not defensively across an entire test suite "just in case."

## 3. Core concept

```
 @Test
 @DirtiesContext
 void mutatesSharedState() {
     someSingletonBean.mutate();  // permanent, non-transactional change
 }
        |
        v
 after this test method completes:
        |
        v
 DirtiesContextTestExecutionListener removes THIS context from the cache
        |
        v
 next test needing the SAME configuration:
     cache miss (even though the key would otherwise match)
        |
        v
     framework builds a BRAND NEW ApplicationContext
     (fresh, unmutated singleton bean instances)
```

`@DirtiesContext` doesn't undo the mutation retroactively — the test that caused it still ran against the (now-mutated) context. What it guarantees is that no *subsequent* test inherits that mutated state, by forcing a rebuild for anyone who'd otherwise share the cache entry.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A test with DirtiesContext evicts the cached context, forcing the next matching test to build a fresh one">
  <rect x="10" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Test A</text>
  <text x="100" y="57" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@DirtiesContext, mutates state</text>

  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="48" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Cached context evicted</text>

  <rect x="450" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Test B (same config)</text>
  <text x="540" y="57" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">gets a FRESH context</text>

  <line x1="190" y1="43" x2="225" y2="43" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="43" x2="445" y2="43" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Test B never sees Test A's mutated singleton, at the cost of paying the context-build cost again.

## 5. Runnable example

### Level 1 — Basic

Two test classes sharing identical configuration; the first mutates a singleton's internal state and is annotated `@DirtiesContext`, and the second confirms it receives a fresh, unmutated instance rather than the polluted one.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class DirtiesContextBasic {

    static class MutableCounter {
        int value = 0;
    }

    @Configuration
    static class Config {
        @Bean
        MutableCounter counter() { return new MutableCounter(); }
    }

    @SpringJUnitConfig(Config.class)
    static class FirstTest {
        @Autowired MutableCounter counter;

        @Test
        @DirtiesContext // this test permanently mutates the shared singleton
        void mutatesTheCounter() {
            counter.value = 999;
            System.out.println("FirstTest set counter.value = " + counter.value);
        }
    }

    @SpringJUnitConfig(Config.class) // identical config -- would normally share the cached context
    static class SecondTest {
        @Autowired MutableCounter counter;

        @Test
        void seesAFreshCounter() {
            System.out.println("SecondTest sees counter.value = " + counter.value);
            if (counter.value != 0) {
                throw new AssertionError("Expected a fresh counter (0), but got " + counter.value
                        + " -- context was NOT correctly evicted!");
            }
            System.out.println("Confirmed: SecondTest received a fresh, unmutated context -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(FirstTest.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(SecondTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: add `spring-test`, `spring-context`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java DirtiesContextBasic.java`.

Without `@DirtiesContext` on `FirstTest.mutatesTheCounter`, `SecondTest` would share `FirstTest`'s cached context (identical `@SpringJUnitConfig(Config.class)`) and inherit `counter.value = 999` instead of a fresh `0` — a classic test-order-dependent failure. With `@DirtiesContext` present, the framework evicts the cache entry after `FirstTest` runs, forcing `SecondTest` to trigger a brand-new context build with a fresh `MutableCounter`.

### Level 2 — Intermediate

Compare `@DirtiesContext`'s different `MethodMode`/`ClassMode` granularities: evicting after just one method versus evicting after the entire class, and see the practical difference in how many rebuilds each triggers.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class DirtiesContextIntermediate {

    static int buildCount = 0;

    static class Marker {
        Marker() { buildCount++; }
    }

    @Configuration
    static class Config {
        @Bean Marker marker() { return new Marker(); }
    }

    @SpringJUnitConfig(Config.class)
    static class MethodLevelDirtiesTest {
        @Autowired Marker marker;

        @Test
        @DirtiesContext // ONLY this method's context gets evicted afterward
        void firstMethodDirtiesOnlyItself() {
            System.out.println("firstMethodDirtiesOnlyItself: build count so far = " + buildCount);
        }

        @Test
        void secondMethodGetsAFreshContextBecauseOfTheFirst() {
            // Because the PREVIOUS method was @DirtiesContext, this method also can't reuse it.
            System.out.println("secondMethodGetsAFreshContextBecauseOfTheFirst: build count so far = " + buildCount);
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(MethodLevelDirtiesTest.class))
                .build();
        launcher.execute(request);

        System.out.println("Total contexts built for this one test class: " + buildCount);
        if (buildCount != 2) throw new AssertionError("Expected 2 builds (one per method, due to @DirtiesContext), got " + buildCount);
        System.out.println("Confirmed: @DirtiesContext on one method forces a rebuild for the NEXT method too -- PASS");
    }
}
```

How to run: same dependencies as Level 1, then `java DirtiesContextIntermediate.java`.

Even within a *single* test class, `@DirtiesContext` on `firstMethodDirtiesOnlyItself` forces `secondMethodGetsAFreshContextBecauseOfTheFirst` to also get a freshly-built context, since the cache entry both methods would otherwise share was evicted after the first one ran — `buildCount` ends at `2`, not `1`, demonstrating that `@DirtiesContext`'s effect extends to *whatever test runs next needing that configuration*, not just "other classes."

### Level 3 — Advanced

A realistic scenario: a test that shuts down an embedded resource (simulating something like an embedded message broker or server being stopped mid-test-suite) uses `@DirtiesContext` specifically because the shutdown is irreversible and would break any later test reusing the same context — contrasted with a `@Transactional` test elsewhere in the same suite that needs no such annotation, since its mutations are already handled by rollback.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;

public class DirtiesContextAdvanced {

    static class FeatureFlagService {
        private boolean maintenanceModeEnabled = false;
        void enableMaintenanceMode() { this.maintenanceModeEnabled = true; } // irreversible for the test's purposes
        boolean isMaintenanceModeEnabled() { return maintenanceModeEnabled; }
    }

    @Configuration
    @EnableTransactionManagement
    static class Config {
        @Bean
        DataSource dataSource() {
            return new EmbeddedDatabaseBuilder()
                    .setType(EmbeddedDatabaseType.H2)
                    .addScript("classpath:orders-schema.sql")
                    .build();
        }
        @Bean JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
        @Bean PlatformTransactionManager transactionManager(DataSource ds) { return new DataSourceTransactionManager(ds); }
        @Bean FeatureFlagService featureFlagService() { return new FeatureFlagService(); }
    }

    @SpringJUnitConfig(Config.class)
    static class MixedConcernsTest {
        @Autowired JdbcTemplate jdbcTemplate;
        @Autowired FeatureFlagService featureFlagService;

        @Test
        @Transactional // database mutation IS covered by rollback -- no @DirtiesContext needed
        void databaseWriteIsAutomaticallyCleanedUp() {
            jdbcTemplate.update("INSERT INTO orders VALUES (1, 'test-order')");
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);
            System.out.println("databaseWriteIsAutomaticallyCleanedUp: count = " + count);
            if (count != 1) throw new AssertionError("Expected the insert to be visible");
            // No @DirtiesContext here: rollback (from @Transactional) handles this cleanly on its own.
        }

        @Test
        @DirtiesContext // Java-object-state mutation is NOT covered by transaction rollback
        void enablingMaintenanceModeIsIrreversibleForThisContext() {
            featureFlagService.enableMaintenanceMode();
            System.out.println("enablingMaintenanceModeIsIrreversibleForThisContext: flag = "
                    + featureFlagService.isMaintenanceModeEnabled());
            // @Transactional would NOT undo this -- it's plain Java object state, not a database write.
            // @DirtiesContext ensures no later test inherits maintenanceModeEnabled == true.
        }

        @Test
        void laterTestSeesAFreshFeatureFlagService() {
            // Runs against a freshly rebuilt context because the PREVIOUS test was @DirtiesContext.
            System.out.println("laterTestSeesAFreshFeatureFlagService: flag = "
                    + featureFlagService.isMaintenanceModeEnabled());
            if (featureFlagService.isMaintenanceModeEnabled()) {
                throw new AssertionError("Expected a fresh FeatureFlagService with maintenance mode OFF");
            }
            System.out.println("Confirmed: later test correctly got a fresh, unmutated FeatureFlagService -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(MixedConcernsTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: add `spring-test`, `spring-context`, `spring-jdbc`, `spring-tx`, `com.h2database:h2`, JUnit 5, and the JUnit Platform Launcher to the classpath, with `orders-schema.sql` on the classpath; then `java DirtiesContextAdvanced.java`.

This test class deliberately contrasts the two cleanup mechanisms side by side: `databaseWriteIsAutomaticallyCleanedUp` needs no `@DirtiesContext` because `@Transactional` rollback already handles its kind of mutation; `enablingMaintenanceModeIsIrreversibleForThisContext` needs `@DirtiesContext` specifically because plain Java object state (a boolean field on a singleton bean) is entirely outside what transaction rollback can undo — the only way to guarantee the next test doesn't inherit `maintenanceModeEnabled == true` is to evict the whole context.

## 6. Walkthrough

Trace `DirtiesContextAdvanced.MixedConcernsTest`'s three test methods, assuming default declaration order:

1. **`databaseWriteIsAutomaticallyCleanedUp` runs.** `@Transactional` starts a transaction; the `INSERT` happens inside it; the assertion passes; the transaction rolls back afterward. No `@DirtiesContext` involved — the context remains cached and valid for reuse, since nothing about it was permanently altered.
2. **`enablingMaintenanceModeIsIrreversibleForThisContext` runs next**, reusing the *same* still-cached context from step 1 (its configuration is identical, and step 1 didn't dirty anything). `featureFlagService.enableMaintenanceMode()` sets `maintenanceModeEnabled = true` directly on the singleton bean — a plain field mutation, with no transaction or rollback mechanism anywhere near it.
3. **`@DirtiesContext` triggers eviction.** After this test method completes, `DirtiesContextTestExecutionListener` sees the annotation and removes this context from the cache — the `ApplicationContext` (and its now-mutated `FeatureFlagService` singleton) is discarded, no longer available for any subsequent test to reuse.
4. **`laterTestSeesAFreshFeatureFlagService` runs.** It needs the same configuration (`@SpringJUnitConfig(Config.class)`), but since the cache entry was just evicted in step 3, this triggers a genuinely new context build — a fresh `FeatureFlagService` instance with `maintenanceModeEnabled` back at its default `false`.
5. **Assertion confirms isolation.** The test checks `isMaintenanceModeEnabled()` and finds `false`, proving the mutation from step 2 didn't leak forward — exactly the guarantee `@DirtiesContext` exists to provide for state that transaction rollback cannot reach.

```
Test 1 (@Transactional, no @DirtiesContext):
   INSERT -> assert -> ROLLBACK               [context stays cached, valid]

Test 2 (@DirtiesContext):
   featureFlagService.enableMaintenanceMode() [plain Java mutation, NOT undoable by rollback]
   -> after method: context EVICTED from cache

Test 3 (same config as 1 & 2):
   cache miss (due to eviction) -> BRAND NEW context built
   -> fresh FeatureFlagService -> maintenanceModeEnabled == false -- PASS
```

## 7. Gotchas & takeaways

> Gotcha: `@DirtiesContext` fixes test isolation at the cost of context-caching's performance benefit for whichever test runs next with matching configuration — overusing it (applying it defensively to many tests "just in case") can silently make a large test suite dramatically slower by defeating caching across much of the suite. Reserve it specifically for tests that mutate state transaction rollback genuinely cannot undo (plain Java object fields, closed/shutdown infrastructure beans), and prefer `@Transactional` rollback wherever the mutation is database-backed.

- `@DirtiesContext` evicts a test's `ApplicationContext` from the cache afterward, guaranteeing no later test inherits state the test mutated — it doesn't undo the mutation itself, only prevents it from leaking forward.
- Use it for mutations transaction rollback cannot reach: plain Java singleton field state, permanently shut-down infrastructure beans — not for database writes, which `@Transactional` already handles more cheaply.
- Its effect extends to whatever test runs next needing the same configuration, not just "other test classes" — even a subsequent method within the same class is affected, as Level 2 demonstrates.
- Apply it narrowly and only where genuinely needed; broad or defensive use quietly erodes the performance benefit the whole context-caching mechanism (from the earlier card) exists to provide.
