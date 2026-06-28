---
card: spring-boot
gi: 88
slug: programmatically-setting-profiles
title: Programmatically setting profiles
---

## 1. What it is

Beyond property files and environment variables, Spring Boot lets you activate profiles **in code** before the application context is created. The two main entry points are:

1. **`SpringApplication.setAdditionalProfiles(String... profiles)`** — permanently adds profiles to the active set, in addition to whatever is already specified externally.
2. **`SpringApplicationBuilder.profiles(String... profiles)`** — fluent alternative when building the application with the builder API.
3. **`ConfigurableEnvironment.setActiveProfiles(String... profiles)`** — replaces the active set outright; useful inside an `ApplicationContextInitializer`.
4. **`ConfigurableEnvironment.addActiveProfile(String profile)`** — appends a single profile without replacing others; the most surgical option.

The word "programmatically" means profile activation happens inside your Java `main` method (or an initialiser) rather than in a file or CLI argument.

## 2. Why & when

Property-file or environment-variable activation is the right default — it keeps configuration external and environment-specific. Programmatic activation is appropriate when:

- You compute the active profile from the runtime environment (e.g. AWS region, a custom ENV token, a feature-flag service) that isn't directly mapped to `spring.profiles.active`.
- You write a **test initialiser** that activates a `test` profile before any `@SpringBootTest` context loads, ensuring a consistent baseline even if developers forget `@ActiveProfiles`.
- You need to activate a profile **conditionally** — for example, activate `cloud` only when a particular environment variable is non-null.
- You are building an embedded Spring Boot application inside a larger program and have no control over JVM args or environment variables.

Programmatic activation is additive with external activation (by default). If the user passes `--spring.profiles.active=prod`, and your code calls `setAdditionalProfiles("metrics")`, both `prod` and `metrics` end up active.

## 3. Core concept

Spring Boot resolves active profiles in two phases:

**Phase 1 — environment is prepared:** the `SpringApplication` reads `spring.profiles.active` from all external sources, then adds any profiles set via `setAdditionalProfiles`. The result is stored in `ConfigurableEnvironment.activeProfiles`.

**Phase 2 — context is refreshed:** beans are registered, profile-specific properties files are loaded. At this point active profiles are frozen; you cannot add more.

The implication: **programmatic profile calls must happen before `SpringApplication.run`** (or inside an `ApplicationContextInitializer` that runs in phase 1). Calling `environment.addActiveProfile` inside a `@PostConstruct` or a `@Bean` factory method is too late — the context is already being built.

```
main()
  └─ SpringApplication
       ├─ prepareEnvironment()   ← programmatic profiles go here
       │    ├─ load external spring.profiles.active
       │    └─ apply setAdditionalProfiles(…)
       └─ refreshContext()       ← beans & property files read active profiles (frozen)
```

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Lifecycle showing where programmatic profile calls are valid (before refreshContext) and where they are too late (after)">
  <rect x="8" y="8" width="664" height="264" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">When Programmatic Profile Activation Is Valid</text>

  <!-- Timeline -->
  <line x1="60" y1="130" x2="620" y2="130" stroke="#30363d" stroke-width="2"/>

  <!-- Phases -->
  <rect x="60" y="100" width="160" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="140" y="122" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">main()</text>
  <text x="140" y="138" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">setAdditionalProfiles()</text>
  <text x="140" y="151" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SpringApplication.run()</text>

  <rect x="240" y="100" width="160" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="122" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">prepareEnvironment</text>
  <text x="320" y="138" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">external sources merged</text>
  <text x="320" y="151" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">✓ addActiveProfile() OK here</text>

  <rect x="420" y="100" width="160" height="60" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="500" y="122" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">refreshContext</text>
  <text x="500" y="138" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">beans created</text>
  <text x="500" y="151" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">✗ TOO LATE — profiles frozen</text>

  <!-- Arrow -->
  <defs>
    <marker id="pa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <line x1="220" y1="130" x2="238" y2="130" stroke="#8b949e" stroke-width="1.5" marker-end="url(#pa)"/>
  <line x1="400" y1="130" x2="418" y2="130" stroke="#8b949e" stroke-width="1.5" marker-end="url(#pa)"/>

  <!-- Legend -->
  <rect x="60" y="185" width="280" height="66" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="80" y="202" fill="#6db33f" font-size="10" font-family="sans-serif" font-weight="bold">✓ Valid locations</text>
  <text x="80" y="218" fill="#e6edf3" font-size="10" font-family="monospace">SpringApplication.setAdditionalProfiles()</text>
  <text x="80" y="232" fill="#e6edf3" font-size="10" font-family="monospace">SpringApplicationBuilder.profiles()</text>
  <text x="80" y="246" fill="#e6edf3" font-size="10" font-family="monospace">ApplicationContextInitializer#initialize()</text>

  <rect x="360" y="185" width="280" height="66" rx="6" fill="#0d1117" stroke="#f85149" stroke-width="1"/>
  <text x="380" y="202" fill="#f85149" font-size="10" font-family="sans-serif" font-weight="bold">✗ Too late</text>
  <text x="380" y="218" fill="#e6edf3" font-size="10" font-family="monospace">@PostConstruct method</text>
  <text x="380" y="232" fill="#e6edf3" font-size="10" font-family="monospace">@Bean factory method</text>
  <text x="380" y="246" fill="#e6edf3" font-size="10" font-family="monospace">CommandLineRunner / ApplicationRunner</text>
</svg>

Profile activation must happen in the environment-preparation phase, before context refresh.

## 5. Runnable example

```java
// ProgrammaticProfiles.java — run: java ProgrammaticProfiles.java  (JDK 17+)
// Simulates the two valid ways to add profiles programmatically before context creation.

import java.util.*;

public class ProgrammaticProfiles {

    // ── Simulated SpringApplication ──────────────────────────────────────────

    static class SpringApplication {
        private final List<String> additionalProfiles = new ArrayList<>();
        private String externalActive = System.getenv("SPRING_PROFILES_ACTIVE");

        /** Equivalent to SpringApplication.setAdditionalProfiles(...) */
        public SpringApplication setAdditionalProfiles(String... profiles) {
            additionalProfiles.addAll(Arrays.asList(profiles));
            return this;
        }

        /** Equivalent to SpringApplication.run(...) */
        public void run() {
            Set<String> active = new LinkedHashSet<>();
            // Phase 1: external sources
            if (externalActive != null && !externalActive.isBlank())
                active.addAll(Arrays.asList(externalActive.split(",")));
            // Phase 1: additional (programmatic)
            active.addAll(additionalProfiles);
            // Fallback
            if (active.isEmpty()) active.add("default");

            System.out.println("Final active profiles : " + active);
            active.forEach(p ->
                System.out.println("  → applying application-" + p + ".properties"));
        }
    }

    // ── Conditional profile logic (real-world pattern) ───────────────────────

    static String detectEnvironment() {
        // In production: read from AWS metadata, K8s downward API, etc.
        String region = System.getenv("AWS_REGION");
        return (region != null) ? "cloud" : null;
    }

    // ── Main ─────────────────────────────────────────────────────────────────

    public static void main(String[] args) {
        System.out.println("=== Basic: setAdditionalProfiles ===");
        new SpringApplication()
            .setAdditionalProfiles("metrics")
            .run();

        System.out.println();
        System.out.println("=== Conditional: add 'cloud' only when AWS_REGION is set ===");
        SpringApplication app = new SpringApplication()
            .setAdditionalProfiles("metrics");
        String env = detectEnvironment();
        if (env != null) {
            app.setAdditionalProfiles(env);
            System.out.println("AWS_REGION detected — activating 'cloud' profile");
        } else {
            System.out.println("No AWS_REGION — 'cloud' profile skipped");
        }
        app.run();

        System.out.println();
        System.out.println("=== SpringApplicationBuilder equivalent ===");
        // In real Spring Boot:
        // new SpringApplicationBuilder(App.class)
        //     .profiles("metrics", "cloud")
        //     .run(args);
        System.out.println("SpringApplicationBuilder.profiles(\"metrics\", \"cloud\").run(args)");
        System.out.println("  → same effect as setAdditionalProfiles, fluent API");
    }
}
```

**How to run:** `java ProgrammaticProfiles.java`

Set `AWS_REGION=us-east-1` before running to see the conditional branch activate.

## 6. Walkthrough

- `additionalProfiles` list accumulates profiles from `setAdditionalProfiles`. In real Spring Boot this list is merged into `ConfigurableEnvironment` during `prepareEnvironment`.
- `externalActive` simulates `SPRING_PROFILES_ACTIVE`. External sources are processed first (higher priority); additional profiles are appended after — they cannot override the external set, only extend it.
- `run()` merges both sources into `active`, falling back to `"default"` if neither source provides anything. This mirrors `AbstractEnvironment.getActiveProfiles()` behaviour.
- **Conditional activation** — `detectEnvironment()` returns `"cloud"` only when an environment variable proves we are in AWS. This pattern is cleaner than shell-script gymnastics around `SPRING_PROFILES_ACTIVE`: the logic lives in Java, is testable, and is visible to readers of the code.
- The `SpringApplicationBuilder` comment shows the fluent equivalent — same semantics, just chained. Useful when you also need to set `sources`, `bannerMode`, or `web-application-type` in one expression.
- There is no explicit `@PostConstruct` or `@Bean` call here — deliberately. Both would be too late; `run()` represents the freeze point.

## 7. Gotchas & takeaways

> **`setAdditionalProfiles` adds to the active set; it never replaces externally-set profiles.** If `SPRING_PROFILES_ACTIVE=prod` is in the environment and you call `setAdditionalProfiles("metrics")`, the result is `prod,metrics`. There is no way to remove an externally-set profile programmatically — that is by design.

> **Do not call `environment.addActiveProfile()` inside a `@Bean` method or `@PostConstruct`.** The context is already refreshing; profile-conditional bean registration and profile-specific property loading already happened. Your call has no effect on which beans were created — it only confuses observers.

- Use `setAdditionalProfiles` for always-needed cross-cutting profiles (`metrics`, `tracing`) that should be active regardless of environment.
- Use `ApplicationContextInitializer` for complex scenarios where you need access to the `ConfigurableEnvironment` before any beans are created.
- Conditional profile logic (reading runtime metadata) belongs in `main()` or an initializer, not inside beans.
- `SpringApplicationBuilder.profiles()` is strictly equivalent to `SpringApplication.setAdditionalProfiles()` — choose whichever fits the builder style you prefer.
- All programmatic profiles appear in the startup log alongside externally-set ones (`INFO - The following profiles are active: prod, metrics`).
