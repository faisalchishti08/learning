---
card: spring-boot
gi: 86
slug: adding-active-profiles
title: Adding active profiles
---

## 1. What it is

**Activating a profile** tells Spring Boot which named configuration contexts to switch on for a given run. Spring Boot reads the active profile list from several sources and merges them in a defined precedence order.

The three most common activation mechanisms are:
1. `spring.profiles.active` property (command-line argument, environment variable, or inside `application.properties`).
2. `spring.profiles.include` — permanently adds profiles on top of whatever is active (used in profile-specific files to stack further profiles).
3. Programmatic activation via `SpringApplication.setAdditionalProfiles(…)` or `ConfigurableEnvironment`.

Understanding *where* to set `spring.profiles.active` — and which source wins when several sources disagree — is as important as knowing the property itself.

## 2. Why & when

Different deployment contexts need different activation mechanisms:

- **Local dev** — set in `application.properties` or an IDE run-configuration.
- **CI/CD** — pass as a JVM system property (`-Dspring.profiles.active=ci`) or environment variable (`SPRING_PROFILES_ACTIVE=ci`).
- **Container/cloud** — set as a container environment variable; this overrides file-based settings automatically because of Spring Boot's property-source precedence.
- **Tests** — use `@ActiveProfiles("test")` on the test class so the profile is set before the context loads.

Getting the mechanism right means the same artifact works in every environment without rebuilding.

## 3. Core concept

Spring Boot's property sources are ordered by precedence (highest first):

| Priority | Source |
|---|---|
| 1 | Command-line arguments (`--spring.profiles.active=prod`) |
| 2 | `SPRING_PROFILES_ACTIVE` OS environment variable |
| 3 | JVM system property (`-Dspring.profiles.active=prod`) |
| 4 | `spring.profiles.active` in `application.properties` (inside JAR) |
| 5 | `spring.profiles.active` in a profile-specific file being loaded |

`spring.profiles.include` is special: it is **additive** — it can only add profiles, never remove them. It is evaluated in the profile-specific file being loaded, so `application-dev.properties` can include `logging` to always enable a logging profile whenever dev is active.

For tests, `@ActiveProfiles` is the idiomatic way; it bypasses all property-source precedence and directly sets the active profiles before context creation.

## 4. Diagram

<svg viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Profile activation priority: command-line at the top overrides env var, which overrides JVM property, which overrides application.properties">
  <rect x="8" y="8" width="664" height="284" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="34" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Profile Activation — Precedence Order (highest → lowest)</text>

  <!-- Source rows -->
  <rect x="30" y="50" width="560" height="36" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="55" y="64" fill="#f85149" font-size="10" font-family="sans-serif" font-weight="bold">① HIGHEST</text>
  <text x="160" y="64" fill="#e6edf3" font-size="11" font-family="monospace">--spring.profiles.active=prod</text>
  <text x="160" y="78" fill="#8b949e" font-size="10" font-family="sans-serif">command-line argument to java / mvn spring-boot:run</text>

  <rect x="30" y="95" width="560" height="36" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="55" y="109" fill="#f0883e" font-size="10" font-family="sans-serif" font-weight="bold">②</text>
  <text x="160" y="109" fill="#e6edf3" font-size="11" font-family="monospace">SPRING_PROFILES_ACTIVE=prod</text>
  <text x="160" y="123" fill="#8b949e" font-size="10" font-family="sans-serif">OS environment variable (used in Docker / Kubernetes)</text>

  <rect x="30" y="140" width="560" height="36" rx="6" fill="#1c2430" stroke="#e3b341" stroke-width="1.5"/>
  <text x="55" y="154" fill="#e3b341" font-size="10" font-family="sans-serif" font-weight="bold">③</text>
  <text x="160" y="154" fill="#e6edf3" font-size="11" font-family="monospace">-Dspring.profiles.active=prod</text>
  <text x="160" y="168" fill="#8b949e" font-size="10" font-family="sans-serif">JVM system property (useful for IDE run configs)</text>

  <rect x="30" y="185" width="560" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="55" y="199" fill="#6db33f" font-size="10" font-family="sans-serif" font-weight="bold">④</text>
  <text x="160" y="199" fill="#e6edf3" font-size="11" font-family="monospace">spring.profiles.active=dev  (application.properties)</text>
  <text x="160" y="213" fill="#8b949e" font-size="10" font-family="sans-serif">packaged inside the JAR — good default for local dev only</text>

  <rect x="30" y="230" width="560" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="55" y="244" fill="#8b949e" font-size="10" font-family="sans-serif" font-weight="bold">⑤ LOWEST</text>
  <text x="160" y="244" fill="#e6edf3" font-size="11" font-family="monospace">spring.profiles.include=logging  (in application-dev.properties)</text>
  <text x="160" y="258" fill="#8b949e" font-size="10" font-family="sans-serif">additive only — stacks extra profiles on top of what's already active</text>

  <!-- Arrow label -->
  <text x="620" y="155" fill="#8b949e" font-size="10" font-family="sans-serif" transform="rotate(-90,620,155)">wins →</text>
</svg>

Higher-numbered sources can be overridden by lower-numbered (higher-priority) sources at deploy time — this is the "externalize everything" principle.

## 5. Runnable example

```java
// ActivatingProfiles.java — run: java ActivatingProfiles.java  (JDK 17+)
// Demonstrates multiple ways to activate profiles in a self-contained simulation.

import java.util.*;

public class ActivatingProfiles {

    // Simulates Spring Boot's profile resolver
    static List<String> resolveActiveProfiles(
            String cmdLine,      // --spring.profiles.active
            String envVar,       // SPRING_PROFILES_ACTIVE
            String jvmProp,      // -Dspring.profiles.active
            String appProps      // spring.profiles.active in application.properties
    ) {
        // Highest-priority source wins; the rest are ignored for active list.
        // include is always additive (simplified: we skip include here)
        if (cmdLine != null && !cmdLine.isBlank())   return Arrays.asList(cmdLine.split(","));
        if (envVar  != null && !envVar.isBlank())    return Arrays.asList(envVar.split(","));
        if (jvmProp != null && !jvmProp.isBlank())   return Arrays.asList(jvmProp.split(","));
        if (appProps != null && !appProps.isBlank())  return Arrays.asList(appProps.split(","));
        return List.of("default");   // Spring Boot's built-in fallback
    }

    static String describeContext(List<String> profiles) {
        if (profiles.contains("prod"))    return "PostgreSQL | no DevTools | pool=20";
        if (profiles.contains("staging")) return "PostgreSQL-staging | no DevTools | pool=5";
        return                                     "H2 in-memory | DevTools active | pool=2";
    }

    public static void main(String[] args) {
        System.out.println("=== Scenario 1: only application.properties sets a profile ===");
        var p1 = resolveActiveProfiles(null, null, null, "dev");
        System.out.println("Active: " + p1 + "  →  " + describeContext(p1));

        System.out.println();
        System.out.println("=== Scenario 2: env var overrides application.properties ===");
        var p2 = resolveActiveProfiles(null, "prod", null, "dev");
        System.out.println("Active: " + p2 + "  →  " + describeContext(p2));

        System.out.println();
        System.out.println("=== Scenario 3: command-line overrides everything ===");
        var p3 = resolveActiveProfiles("staging", "prod", "dev", "dev");
        System.out.println("Active: " + p3 + "  →  " + describeContext(p3));

        System.out.println();
        System.out.println("=== Scenario 4: nothing set — 'default' profile is used ===");
        var p4 = resolveActiveProfiles(null, null, null, null);
        System.out.println("Active: " + p4 + "  →  " + describeContext(p4));

        System.out.println();
        System.out.println("=== Scenario 5: multiple profiles simultaneously ===");
        var p5 = resolveActiveProfiles(null, null, null, "dev,cloud,logging");
        System.out.println("Active: " + p5 + "  →  " + describeContext(p5));
    }
}
```

**How to run:** `java ActivatingProfiles.java`

In a real Spring Boot app you'd use:
- `./mvnw spring-boot:run -Dspring-boot.run.profiles=prod`
- `java -jar app.jar --spring.profiles.active=prod`
- `SPRING_PROFILES_ACTIVE=prod java -jar app.jar`

## 6. Walkthrough

- `resolveActiveProfiles` mimics Spring Boot's `StandardEnvironment` property-source chain. The first non-blank value wins; the rest are ignored. This is the single most important thing to understand about profile activation.
- **Scenario 1**: `application.properties` sets `dev` — the happy local-dev case. The profile file `application-dev.properties` will be loaded automatically in real Spring Boot.
- **Scenario 2**: an environment variable (`SPRING_PROFILES_ACTIVE=prod`) overrides the packaged `application.properties`. This is how Docker containers and Kubernetes deployments override the default without rebuilding the JAR.
- **Scenario 3**: the command-line argument wins over everything — useful for one-off manual overrides or when the same JAR must be tested in multiple environments on the same machine.
- **Scenario 4**: nothing is set, so Spring Boot activates the built-in `"default"` profile. Beans annotated `@Profile("default")` register; no profile-specific property file is loaded.
- **Scenario 5**: comma-separated values activate multiple profiles at once. All three files `application-dev.properties`, `application-cloud.properties`, and `application-logging.properties` would be loaded in real Spring Boot.

## 7. Gotchas & takeaways

> **Never set `spring.profiles.active=prod` inside `application.properties` in a shared repository.** If the JAR is deployed to production it works — but any developer who checks out the code and runs locally gets the production profile. Set it in `.gitignore`-d local files or leave it blank and activate via the command-line in CI/CD.

> **`spring.profiles.active` inside `application-prod.properties` does NOT recursively activate more profiles.** You cannot "chain-activate" profiles that way. Use `spring.profiles.include` for additive stacking, or the `profile groups` feature (Spring Boot 2.4+).

- `spring.profiles.active` replaces the entire active set; `spring.profiles.include` appends to it.
- For tests, `@ActiveProfiles("test")` is the idiomatic mechanism — no property files or JVM flags needed.
- The active profiles are logged at `INFO` level during startup — always check there first when behavior seems wrong.
- Comma-separate multiple profiles: `--spring.profiles.active=prod,cloud` activates both simultaneously.
- In Spring Boot 2.4+, setting `spring.profiles.active` inside a profile-specific file is forbidden; use profile groups instead.
