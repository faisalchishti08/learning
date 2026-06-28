---
card: spring-boot
gi: 251
slug: conditions-native-limitations
title: Conditions & native limitations
---

## 1. What it is

Spring's condition system (`@ConditionalOn*`) allows beans to be registered only when certain criteria are met — a property exists, a class is on the classpath, another bean is present, etc. In the standard JVM model these conditions are evaluated **at runtime startup**. In a GraalVM native image they are evaluated **once at AOT build time** and the decision is baked into the binary.

This means:

- A bean excluded at build time (`@ConditionalOnProperty(matchIfMissing=false)` and property not set during the build) is **not included** in the native binary — it cannot appear at runtime.
- A bean included at build time stays in the binary even if the condition would evaluate to `false` at runtime with a different configuration.

## 2. Why & when

This is the most common source of surprises when migrating a Spring Boot app to native images. Examples that break:

- **`@ConditionalOnProperty("feature.enabled")`** — if the property isn't set during `process-aot`, the bean is excluded. Setting the property at runtime (`FEATURE_ENABLED=true java -jar app.jar`) has no effect.
- **`@ConditionalOnMissingBean`** — resolved at build time based on the bean graph at that point. If you expect to override a bean at runtime via a configuration file, it won't work.
- **`@ConditionalOnClass`** — safe in native mode because classpath content is fixed at build time anyway; the class is present or absent before `process-aot` runs.

You need this knowledge when: deploying the same binary to multiple environments (dev/prod) with different feature flags, or when using externally-injected secrets to drive bean creation.

## 3. Core concept

Imagine baking a cake where you must decide *before baking* whether to add chocolate chips. On the JVM, you can decide at serving time by adding chips to the plate. With native images, the cake's contents are fixed when it goes in the oven. You can still vary the *frosting* (external config that doesn't drive bean selection), but not the cake's ingredients.

The rule of thumb:

| What you can vary at runtime | What must be fixed at build time |
|---|---|
| Property values used inside a bean | Whether a bean exists at all |
| Database URL, port, log level | Which datasource implementation is used |
| Feature flag *values* read by a bean | Feature flag *presence* that creates/skips a bean |

Spring AOT evaluates conditions using the environment present during `process-aot`. You can set properties for the AOT phase via:

1. An `application.properties` on the build classpath.
2. System properties passed to the Maven/Gradle command.
3. A dedicated `application-aot.properties` profile (activated automatically by Spring during AOT processing).

## 4. Diagram

<svg viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Conditions evaluated at build time vs runtime in native image vs JVM mode">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- JVM column -->
  <rect x="10" y="10" width="300" height="220" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="35" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">JVM Mode</text>

  <rect x="25" y="50" width="270" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Start: load all BeanDefinitions</text>
  <text x="160" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">All @ConditionalOn* present</text>

  <rect x="25" y="110" width="270" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="160" y="125" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Evaluate conditions at RUNTIME</text>
  <text x="160" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Using live environment / classpath</text>

  <rect x="25" y="170" width="270" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="185" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Register matching beans only</text>
  <text x="160" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Can re-evaluate each restart</text>

  <!-- Native column -->
  <rect x="390" y="10" width="300" height="220" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="540" y="35" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Native Mode</text>

  <rect x="405" y="50" width="270" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="540" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Build time: AOT processor evaluates</text>
  <text x="540" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ALL @ConditionalOn* — ONCE</text>

  <rect x="405" y="110" width="270" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="540" y="125" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Only matching beans compiled in</text>
  <text x="540" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Rest are eliminated from binary</text>

  <rect x="405" y="170" width="270" height="40" rx="5" fill="#1c2430" stroke="#8b1a1a" stroke-width="1"/>
  <text x="540" y="185" fill="#ff7b72" font-size="10" text-anchor="middle" font-family="sans-serif">Runtime: conditions NOT re-evaluated</text>
  <text x="540" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Binary is fixed — restart doesn't help</text>

  <text x="350" y="240" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">↑ key difference</text>
</svg>

In native mode, conditions are permanent build-time decisions; you cannot toggle beans with runtime properties.

## 5. Runnable example

```java
// ConditionsNativeDemo.java — run with: java ConditionsNativeDemo.java
// Illustrates the problem with @ConditionalOnProperty in native mode
// and shows the safe patterns to use instead.

import java.util.Map;

public class ConditionsNativeDemo {

    // Simulated bean container (replaces Spring's ApplicationContext)
    record Bean(String name, boolean included) {}

    public static void main(String[] args) {
        System.out.println("=== Conditions & Native Image Limitations ===\n");

        // Simulate AOT build phase: environment at build time
        Map<String, String> buildEnv = Map.of(
            "feature.cache.enabled", "true"
            // "feature.payment.enabled" is NOT set at build time
        );

        System.out.println("--- Build-time environment ---");
        buildEnv.forEach((k, v) -> System.out.println("  " + k + " = " + v));
        System.out.println();

        // AOT resolves conditions with buildEnv
        Bean cacheBean   = resolveCondition("cacheService",   "feature.cache.enabled",   buildEnv);
        Bean paymentBean = resolveCondition("paymentService", "feature.payment.enabled",  buildEnv);

        System.out.println("--- Beans compiled into native binary ---");
        System.out.println("  cacheService   : " + (cacheBean.included()   ? "INCLUDED" : "EXCLUDED"));
        System.out.println("  paymentService : " + (paymentBean.included() ? "INCLUDED" : "EXCLUDED"));
        System.out.println();

        // At runtime you set feature.payment.enabled=true — but it's too late
        Map<String, String> runtimeEnv = Map.of(
            "feature.cache.enabled",   "true",
            "feature.payment.enabled", "true"   // set at runtime
        );
        System.out.println("--- Runtime environment (after deployment) ---");
        runtimeEnv.forEach((k, v) -> System.out.println("  " + k + " = " + v));
        System.out.println();

        System.out.println("--- Result in native binary ---");
        System.out.println("  paymentService is still EXCLUDED — binary is fixed.");
        System.out.println("  Setting feature.payment.enabled=true at runtime has NO effect.\n");

        System.out.println("--- Safe patterns ---");
        System.out.println("  1. Set ALL condition properties before running mvn -Pnative package");
        System.out.println("  2. Use application-aot.properties to set build-time conditions");
        System.out.println("  3. Use runtime-only config (properties read inside a bean, not by @Conditional)");
        System.out.println("  4. Ship separate native binaries for different feature sets");
    }

    static Bean resolveCondition(String beanName, String prop, Map<String,String> env) {
        boolean included = env.containsKey(prop) && "true".equals(env.get(prop));
        System.out.printf("  Evaluating @ConditionalOnProperty(\"%s\") => %s%n",
            prop, included ? "MATCH (include bean)" : "NO MATCH (exclude bean)");
        return new Bean(beanName, included);
    }
}
```

**How to run:** `java ConditionsNativeDemo.java`

## 6. Walkthrough

- **`buildEnv`** — represents the environment available when `mvn -Pnative spring-boot:process-aot` runs. Only `feature.cache.enabled` is present.
- **`resolveCondition`** — simulates Spring AOT evaluating `@ConditionalOnProperty`. `cacheService` passes (property is `"true"`); `paymentService` fails (property absent → default `matchIfMissing=false`).
- **"Beans compiled into native binary"** — the AOT phase writes a `BeanDefinitionRegistrar` that only includes `cacheService`. `paymentService` is not referenced anywhere in the generated code; `native-image` eliminates it entirely during dead code removal.
- **`runtimeEnv`** — demonstrates that setting `feature.payment.enabled=true` via an environment variable at deployment time cannot resurrect a bean that was eliminated at build time. The generated registrar has no code path for `paymentService`.
- **Safe patterns** — the most practical fix is `application-aot.properties` in `src/main/resources`: Spring activates this profile automatically during `process-aot`, letting you set the "include everything" state for the build without affecting runtime defaults.

## 7. Gotchas & takeaways

> **`@ConditionalOnProperty` is a build-time door, not a runtime toggle.** If you have been using it as a feature flag readable from environment variables at runtime, that pattern breaks in native mode. Switch to a `@Value`-injected boolean property read *inside* the bean's method — that way the bean always exists and the runtime value controls behaviour.

> **`@ConditionalOnClass` is safe** because the classpath is identical between build time and native runtime — if a class is on the build classpath it's in the binary; if it isn't, it isn't. Only property- and bean-presence conditions are risky.

- `application-aot.properties` is the cleanest way to control build-time conditions: create it alongside `application.properties` and set all conditional properties to their "include" values.
- `@Profile` uses `@Conditional` under the hood — profile-specific beans are also locked at build time in native mode.
- `@ConditionalOnMissingBean` with auto-configuration is usually safe because Spring Boot's auto-configuration ordering is deterministic and controlled; user-override beans are always detected before the auto-config bean.
- Multiple native binaries per environment is the correct architectural pattern for truly divergent configurations.
- Check Spring Boot's AOT compatibility report: `mvn -Pnative spring-boot:process-aot` prints warnings for conditions that could not be deterministically resolved.
