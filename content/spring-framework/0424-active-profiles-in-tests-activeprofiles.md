---
card: spring-framework
gi: 424
slug: active-profiles-in-tests-activeprofiles
title: "Active profiles in tests (@ActiveProfiles)"
---

## 1. What it is

`@ActiveProfiles` sets which Spring profiles are active for a test's `ApplicationContext`, controlling which `@Profile`-gated beans get registered — the test-time equivalent of setting `spring.profiles.active` when running a real application. It's how a test class opts into (or explicitly excludes) profile-specific configuration without touching any real deployment configuration.

```java
@SpringJUnitConfig(Config.class)
@ActiveProfiles("test")
class PaymentServiceTest {
    @Autowired PaymentGateway paymentGateway; // resolves to whichever @Profile("test") bean matches
}
```

## 2. Why & when

Applications commonly use `@Profile` to swap implementations by environment — a real payment gateway in production, a fake one in development, an in-memory one for tests. Without `@ActiveProfiles`, a test's `ApplicationContext` activates no profiles by default, meaning any bean gated behind a specific `@Profile` (including a `"test"` profile meant specifically for this scenario) simply won't be registered, likely causing a `NoSuchBeanDefinitionException` or, worse, silently falling back to a different bean than intended if multiple profile-gated candidates exist.

Reach for `@ActiveProfiles` when:

- Your application configuration uses `@Profile` to swap real implementations for test-friendly ones (an in-memory repository instead of a real database client, a stub external-service client instead of one making real network calls).
- You want to verify profile-specific configuration itself behaves correctly — testing that a `@Profile("prod")` bean's settings are what you expect, by activating `"prod"` specifically in a test.
- You need different test classes to exercise the application under different profile combinations, to confirm behavior is correct across environments without deploying to each one.

## 3. Core concept

```
 @ActiveProfiles({"test", "in-memory-db"})
        |
        v
 Environment.setActiveProfiles("test", "in-memory-db")
        |
        v
 during context refresh, EVERY @Bean method / @Component is checked:
        |
        +-- no @Profile annotation           -> always registered
        +-- @Profile("test")                  -> registered (matches active profile)
        +-- @Profile("prod")                  -> SKIPPED (doesn't match)
        +-- @Profile("!test")                 -> SKIPPED (negation of an active profile)
        +-- @Profile({"test", "staging"})     -> registered (any listed profile matching is enough)
```

Profile matching happens once, during context construction — it's not something that changes dynamically during a test run; the active profile set is fixed for the whole lifetime of that particular `ApplicationContext`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ActiveProfiles selects which Profile-gated beans get registered in the test context">
  <rect x="10" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="85" y="44" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Profile("test")</text>

  <rect x="10" y="70" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="85" y="94" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Profile("prod")</text>

  <rect x="10" y="120" width="150" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="85" y="144" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">no @Profile</text>

  <rect x="300" y="65" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="390" y="87" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@ActiveProfiles("test")</text>
  <text x="390" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">test's ApplicationContext</text>

  <line x1="160" y1="40" x2="295" y2="80" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="160" y1="140" x2="295" y2="100" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="160" y1="90" x2="240" y2="90" stroke="#8b949e" stroke-width="1" stroke-dasharray="3"/>
  <text x="200" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">skipped</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Only beans with no `@Profile` restriction, or a matching one, make it into the resulting context.

## 5. Runnable example

### Level 1 — Basic

Two `@Profile`-gated beans for the same interface, and a test activating one profile to confirm the correct implementation is wired in.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class ActiveProfilesBasic {

    interface PaymentGateway { String charge(double amount); }

    @Configuration
    static class Config {
        @Bean
        @Profile("prod")
        PaymentGateway realGateway() { return amount -> { throw new UnsupportedOperationException("real network call"); }; }

        @Bean
        @Profile("test")
        PaymentGateway fakeGateway() { return amount -> "FAKE-CHARGE-" + amount; }
    }

    @SpringJUnitConfig(Config.class)
    @ActiveProfiles("test")
    static class PaymentGatewayTest {
        @Autowired PaymentGateway paymentGateway;

        @Test
        void resolvesToFakeGatewayUnderTestProfile() {
            String result = paymentGateway.charge(29.99);
            System.out.println("Result: " + result);
            if (!result.startsWith("FAKE-CHARGE-")) throw new AssertionError("Expected the fake gateway to be active");
            System.out.println("resolvesToFakeGatewayUnderTestProfile -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(PaymentGatewayTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: add `spring-test`, `spring-context`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java ActiveProfilesBasic.java`.

Without `@ActiveProfiles("test")`, neither `@Profile`-gated bean would be registered at all, and `@Autowired PaymentGateway` would fail with `NoSuchBeanDefinitionException` — activating `"test"` specifically selects `fakeGateway`, and `realGateway` (gated behind `"prod"`) is never even instantiated, so its `UnsupportedOperationException` body is never reached.

### Level 2 — Intermediate

Combine `@ActiveProfiles` with `@Profile`'s negation syntax (`!profileName`) and multiple simultaneously active profiles, showing both real-world patterns for expressing "everything except this specific environment" and "this feature is on only when both conditions hold."

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class ActiveProfilesIntermediate {

    static class DebugLogger { String describe() { return "verbose debug logging enabled"; } }
    static class FeatureXBean { String describe() { return "feature X active"; } }

    @Configuration
    static class Config {
        @Bean
        @Profile("!prod") // active in every profile EXCEPT prod -- common for dev-only tooling
        DebugLogger debugLogger() { return new DebugLogger(); }

        @Bean
        @Profile({"beta", "internal"}) // active if EITHER "beta" OR "internal" is active
        FeatureXBean featureXBean() { return new FeatureXBean(); }
    }

    @SpringJUnitConfig(Config.class)
    @ActiveProfiles({"test", "internal"}) // multiple profiles active simultaneously
    static class MultiProfileTest {
        @Autowired org.springframework.context.ApplicationContext context;

        @Test
        void debugLoggerIsActiveBecauseProdIsNotAmongActiveProfiles() {
            DebugLogger logger = context.getBean(DebugLogger.class);
            System.out.println("DebugLogger: " + logger.describe());
            System.out.println("debugLoggerIsActiveBecauseProdIsNotAmongActiveProfiles -- PASS");
        }

        @Test
        void featureXIsActiveBecauseInternalProfileMatches() {
            FeatureXBean feature = context.getBean(FeatureXBean.class);
            System.out.println("FeatureXBean: " + feature.describe());
            System.out.println("featureXIsActiveBecauseInternalProfileMatches -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(MultiProfileTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: same dependencies as Level 1, then `java ActiveProfilesIntermediate.java`.

`@Profile("!prod")` matches because `"prod"` isn't among the test's active profiles (`"test"`, `"internal"`) — negation checks absence, not a specific active match. `@Profile({"beta", "internal"})` matches because `"internal"` (one of the two active profiles here) satisfies the OR-style multi-value profile expression, even though `"beta"` isn't active — a bean's `@Profile` list only needs *one* match, not all of them.

### Level 3 — Advanced

Use `@ActiveProfilesResolver` for computing active profiles programmatically rather than as a fixed static list — useful when the right profile combination depends on some runtime condition (an environment variable, a system property, or CI-specific detection) rather than being knowable purely from the annotation itself.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.ActiveProfilesResolver;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class ActiveProfilesAdvanced {

    static class CiOnlyReporter { String describe() { return "CI-specific test reporting enabled"; } }
    static class LocalDevTools { String describe() { return "local developer convenience tools enabled"; } }

    @Configuration
    static class Config {
        @Bean
        @Profile("ci")
        CiOnlyReporter ciOnlyReporter() { return new CiOnlyReporter(); }

        @Bean
        @Profile("local")
        LocalDevTools localDevTools() { return new LocalDevTools(); }
    }

    static class EnvironmentAwareProfilesResolver implements ActiveProfilesResolver {
        @Override
        public String[] resolve(Class<?> testClass) {
            // Computed at test-startup time, not hardcoded in the annotation --
            // e.g. detect a CI environment variable a real pipeline would set.
            boolean runningInCi = System.getenv("CI") != null || System.getProperty("simulate.ci", "false").equals("true");
            return runningInCi ? new String[]{"ci"} : new String[]{"local"};
        }
    }

    @SpringJUnitConfig(Config.class)
    @ActiveProfiles(resolver = EnvironmentAwareProfilesResolver.class)
    static class EnvironmentAwareTest {
        @Autowired org.springframework.context.ApplicationContext context;

        @Test
        void resolvesProfileBasedOnEnvironment() {
            boolean hasCiReporter = context.getBeanNamesForType(CiOnlyReporter.class).length > 0;
            boolean hasLocalTools = context.getBeanNamesForType(LocalDevTools.class).length > 0;
            System.out.println("CiOnlyReporter present: " + hasCiReporter);
            System.out.println("LocalDevTools present: " + hasLocalTools);

            if (hasCiReporter == hasLocalTools) {
                throw new AssertionError("Expected EXACTLY one of the two profile-gated beans to be present");
            }
            System.out.println("Exactly one profile-specific bean is active, based on the resolved environment -- PASS");
        }
    }

    public static void main(String[] args) {
        // Simulate running this "as if" in a CI environment for this demonstration.
        System.setProperty("simulate.ci", "true");

        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(EnvironmentAwareTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: same dependencies as Level 1, then `java ActiveProfilesAdvanced.java`.

`@ActiveProfiles(resolver = EnvironmentAwareProfilesResolver.class)` replaces the usual static string list with a class implementing `ActiveProfilesResolver.resolve(Class<?> testClass)`, called once when the test's `Environment` is being prepared — letting the actual set of active profiles depend on runtime conditions (here, an environment variable a real CI pipeline would set) rather than being fixed at compile time in the annotation.

## 6. Walkthrough

Trace `ActiveProfilesAdvanced.EnvironmentAwareTest.resolvesProfileBasedOnEnvironment()` under the simulated CI condition:

1. **System property set.** Before the launcher runs, `main` sets `simulate.ci=true`, standing in for a real `CI` environment variable a genuine pipeline would already have set.
2. **Resolver invoked.** As the TestContext Framework prepares `EnvironmentAwareTest`'s `Environment`, it sees `@ActiveProfiles(resolver = EnvironmentAwareProfilesResolver.class)` and calls `resolve(EnvironmentAwareTest.class)` on a new instance of that resolver, rather than reading a static `value`/`profiles` attribute.
3. **Runtime decision.** Inside `resolve`, `System.getProperty("simulate.ci", "false").equals("true")` evaluates to `true` (given step 1), so the method returns `new String[]{"ci"}`.
4. **Profiles activated.** The returned array (`["ci"]`) becomes the test's active profile set, exactly as if `@ActiveProfiles("ci")` had been written directly — except the actual value was computed, not hardcoded.
5. **Context builds accordingly.** During refresh, `CiOnlyReporter`'s `@Profile("ci")` matches the now-active `"ci"` profile, so it's registered; `LocalDevTools`'s `@Profile("local")` doesn't match, so it's skipped.
6. **Assertion.** The test finds `CiOnlyReporter` present and `LocalDevTools` absent — confirming the resolver's runtime decision correctly drove which profile-gated beans made it into the context, without the test class itself hardcoding which environment it expected to run in.

```
System property simulate.ci=true (standing in for a real CI env var)
   -> EnvironmentAwareProfilesResolver.resolve() -> ["ci"]
   -> Environment active profiles = ["ci"]
   -> context refresh: CiOnlyReporter (@Profile("ci")) registered
                        LocalDevTools (@Profile("local")) skipped
   -> test confirms exactly the CI-specific bean is present
```

## 7. Gotchas & takeaways

> Gotcha: forgetting `@ActiveProfiles` entirely on a test whose configuration relies on `@Profile`-gated beans is a common source of `NoSuchBeanDefinitionException` at test-context-startup time — the error message names the missing bean type, but the actual root cause (no matching profile is active) is easy to miss if you're not specifically thinking about profiles. When a bean "should obviously be there" but the context fails to start, checking whether it's `@Profile`-gated and whether the right profile is active is a fast first diagnostic step.

- `@ActiveProfiles` is the test-time equivalent of `spring.profiles.active`, controlling exactly which `@Profile`-gated beans get registered in a test's `ApplicationContext`.
- `@Profile`'s negation (`!name`) and multi-value (`{"a", "b"}`, OR-matched) syntaxes work identically in tests as in production configuration — no test-specific profile-matching rules.
- Multiple profiles can be active simultaneously; a bean's `@Profile` list only needs one matching (non-negated) entry, or its negation condition to hold, to be included.
- `ActiveProfilesResolver` computes the active profile set programmatically at test-startup time, useful when the right profiles depend on a runtime condition (environment detection, a system property) rather than a fixed, known-in-advance list.
