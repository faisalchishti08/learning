---
card: microservices
gi: 220
slug: environment-specific-configuration
title: "Environment-specific configuration"
---

## 1. What it is

Environment-specific configuration is the practice of maintaining distinct sets of configuration values for each deployment environment (development, staging, production) while keeping the application code and its structure identical across all of them — only the values differ, never the shape of the application consuming them.

## 2. Why & when

[Externalizing configuration](0218-externalized-configuration-12-factor.md) establishes that values live outside the artifact, but a real system usually needs more than one value per setting: a database URL that's `localhost` in development, a staging cluster in staging, and a production cluster in production. Without a structured way to organize these per-environment values, teams tend to either hard-code environment checks scattered through the codebase (`if (env.equals("prod")) {...}`, repeated at every call site) or maintain entirely separate, drifting codebases per environment — both of which reintroduce the coupling externalization was meant to remove.

Structure configuration by environment whenever a system runs in more than one place with different settings — nearly always true beyond a single-developer prototype. [Spring profiles](0230-spring-profiles.md), covered later in this section, is Spring's dedicated mechanism for this exact pattern.

## 3. Core concept

Environment-specific configuration organizes values into named groups (one per environment) and selects the active group at startup via a single piece of external input (an environment variable, a command-line flag) — the application code reads settings generically, without ever branching on which environment it's currently in.

```java
// environment-specific VALUES, organized by environment name
Map<String, Map<String, String>> configByEnvironment = Map.of(
    "development", Map.of("db.url", "jdbc:postgresql://localhost:5432/orders", "log.level", "DEBUG"),
    "staging",     Map.of("db.url", "jdbc:postgresql://staging-db:5432/orders", "log.level", "INFO"),
    "production",  Map.of("db.url", "jdbc:postgresql://prod-db:5432/orders",    "log.level", "WARN")
);
String activeEnv = System.getenv().getOrDefault("APP_ENV", "development"); // ONE selector, read once
Map<String, String> activeConfig = configByEnvironment.get(activeEnv); // application code reads GENERICALLY from here
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One APP_ENV selector picks which of three named configuration groups -- development, staging, production -- becomes the active configuration the application reads from generically" >
  <rect x="20" y="60" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">APP_ENV=staging</text>

  <rect x="220" y="15" width="150" height="35" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="295" y="37" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">development config</text>
  <rect x="220" y="60" width="150" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="295" y="82" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">staging config (ACTIVE)</text>
  <rect x="220" y="105" width="150" height="35" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="295" y="127" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">production config</text>

  <rect x="450" y="60" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="525" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Application code</text>

  <line x1="150" y1="82" x2="290" y2="78" stroke="#8b949e" marker-end="url(#arr220)"/>
  <line x1="295" y1="78" x2="448" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr220g)"/>

  <defs>
    <marker id="arr220" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="arr220g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

One selector activates exactly one named configuration group; application code never branches on the environment itself.

## 5. Runnable example

Scenario: a service that starts with configuration decisions branching on environment name scattered through its logic (fragile, error-prone to extend), refactors to select one pre-defined configuration group up front and read from it generically afterward, and finally adds a safeguard that rejects an unrecognized environment name loudly instead of silently falling through to a default.

### Level 1 — Basic

```java
// File: ScatteredEnvironmentChecks.java -- environment checks are
// SCATTERED through the logic; adding a new environment means finding
// and updating EVERY branch.
public class ScatteredEnvironmentChecks {
    static String currentEnv = "staging";

    static String getDbUrl() {
        if (currentEnv.equals("development")) return "jdbc:postgresql://localhost:5432/orders";
        else if (currentEnv.equals("staging")) return "jdbc:postgresql://staging-db:5432/orders";
        else return "jdbc:postgresql://prod-db:5432/orders";
    }

    static String getLogLevel() {
        if (currentEnv.equals("development")) return "DEBUG"; // the SAME branching, repeated for EVERY setting
        else if (currentEnv.equals("staging")) return "INFO";
        else return "WARN";
    }

    public static void main(String[] args) {
        System.out.println("DB URL: " + getDbUrl());
        System.out.println("Log level: " + getLogLevel());
        System.out.println("Each new setting repeats the SAME if/else environment branching.");
    }
}
```

**How to run:** `javac ScatteredEnvironmentChecks.java && java ScatteredEnvironmentChecks` (JDK 17+).

### Level 2 — Intermediate

```java
// File: GroupedByEnvironment.java -- configuration is GROUPED by
// environment ONCE; application code reads GENERICALLY afterward,
// with NO environment branching in the reading logic itself.
import java.util.*;

public class GroupedByEnvironment {
    static Map<String, Map<String, String>> configByEnvironment = Map.of(
        "development", Map.of("db.url", "jdbc:postgresql://localhost:5432/orders", "log.level", "DEBUG"),
        "staging",     Map.of("db.url", "jdbc:postgresql://staging-db:5432/orders", "log.level", "INFO"),
        "production",  Map.of("db.url", "jdbc:postgresql://prod-db:5432/orders",    "log.level", "WARN")
    );

    public static void main(String[] args) {
        String activeEnv = "staging"; // the ONE environment selector
        Map<String, String> activeConfig = configByEnvironment.get(activeEnv); // resolved ONCE

        System.out.println("DB URL: " + activeConfig.get("db.url")); // GENERIC read, no branching
        System.out.println("Log level: " + activeConfig.get("log.level")); // GENERIC read, no branching
        System.out.println("Adding a new setting needs NO new environment branching -- just a new key.");
    }
}
```

**How to run:** `javac GroupedByEnvironment.java && java GroupedByEnvironment` (JDK 17+).

Expected output:
```
DB URL: jdbc:postgresql://staging-db:5432/orders
Log level: INFO
Adding a new setting needs NO new environment branching -- just a new key.
```

### Level 3 — Advanced

```java
// File: RejectsUnrecognizedEnvironment.java -- a typo'd or unrecognized
// environment name is REJECTED loudly at startup, rather than silently
// falling through to some default that might be wrong for the deployment.
import java.util.*;

public class RejectsUnrecognizedEnvironment {
    static Map<String, Map<String, String>> configByEnvironment = Map.of(
        "development", Map.of("db.url", "jdbc:postgresql://localhost:5432/orders", "log.level", "DEBUG"),
        "staging",     Map.of("db.url", "jdbc:postgresql://staging-db:5432/orders", "log.level", "INFO"),
        "production",  Map.of("db.url", "jdbc:postgresql://prod-db:5432/orders",    "log.level", "WARN")
    );

    static Map<String, String> resolveConfig(String activeEnv) {
        Map<String, String> config = configByEnvironment.get(activeEnv);
        if (config == null) { // FAIL FAST -- no silent default for an unrecognized name
            throw new IllegalArgumentException(
                "Unrecognized APP_ENV '" + activeEnv + "' -- expected one of: " + configByEnvironment.keySet());
        }
        return config;
    }

    public static void main(String[] args) {
        Map<String, String> stagingConfig = resolveConfig("staging"); // valid -- resolves normally
        System.out.println("staging DB URL: " + stagingConfig.get("db.url"));

        try {
            resolveConfig("productoin"); // a TYPO -- should be rejected, not silently mis-resolved
        } catch (IllegalArgumentException e) {
            System.out.println("Caught expected error: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac RejectsUnrecognizedEnvironment.java && java RejectsUnrecognizedEnvironment` (JDK 17+).

Expected output:
```
staging DB URL: jdbc:postgresql://staging-db:5432/orders
Caught expected error: Unrecognized APP_ENV 'productoin' -- expected one of: [development, staging, production]
```

## 6. Walkthrough

1. **Level 1, branching everywhere** — `getDbUrl` and `getLogLevel` each independently re-implement the identical `if (currentEnv.equals(...))` chain; a third setting would require a third copy of this same chain, and a new environment name would require updating every one of these copies consistently.
2. **Level 2, grouping by environment once** — `configByEnvironment` organizes every setting under its owning environment name in one nested map, so the environment-to-value mapping exists in exactly one place rather than being re-derived by every reading method.
3. **Level 2, generic reads afterward** — `main` resolves `activeConfig` once via a single map lookup (`configByEnvironment.get(activeEnv)`), and every subsequent read (`activeConfig.get("db.url")`, `activeConfig.get("log.level")`) is a plain, environment-agnostic map access — no `if`/`else` branching appears anywhere in the reading logic.
4. **Level 3, validating the selector** — `resolveConfig` checks whether `configByEnvironment.get(activeEnv)` returned `null`, which happens whenever `activeEnv` doesn't match any known environment name exactly.
5. **Level 3, the typo scenario** — the second call passes `"productoin"` (a deliberate misspelling of `"production"`); because this string doesn't match any key in `configByEnvironment`, `resolveConfig` throws `IllegalArgumentException` with a message listing the valid options, rather than returning `null` (which would cause a confusing `NullPointerException` much later, far from the actual mistake) or silently matching a wrong environment.
6. **Level 3, why failing here matters** — catching this kind of misconfiguration at the single point where the environment is resolved, with a message naming the invalid value and the valid alternatives, turns what could be a hard-to-diagnose production incident (an unrecognized environment name somehow resolving to unexpected behavior) into an immediate, clear startup failure.

## 7. Gotchas & takeaways

> **Gotcha:** silently falling back to a default environment (or default config group) when the selector is missing or unrecognized is a common but risky shortcut — it can mask a genuine deployment mistake (an environment variable that failed to get set) by having the application quietly start with the wrong configuration instead of failing loudly; validate the selector explicitly, as Level 3 does.

- Environment-specific configuration groups settings by named environment, selected once via a single external input, so application code reads generically without branching on environment identity.
- This avoids both scattered environment checks throughout the codebase and the coupling that hard-coded, environment-specific builds would reintroduce.
- Structuring configuration this way scales cleanly as new settings are added — a new setting needs only a new key per environment group, not new branching logic.
- Reject an unrecognized or missing environment selector explicitly and loudly at startup, rather than silently defaulting to a possibly-wrong environment.
- Spring's own mechanism for this exact pattern, [Spring profiles](0230-spring-profiles.md), is covered later in this section.
