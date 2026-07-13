---
card: microservices
gi: 218
slug: externalized-configuration-12-factor
title: "Externalized configuration (12-factor)"
---

## 1. What it is

Externalized configuration means keeping settings that vary between environments — database URLs, credentials, feature flags, timeouts — completely outside the compiled application artifact, supplied instead at deploy or runtime through environment variables, config files, or a config server. It is the third factor of the [Twelve-Factor App](https://12factor.net) methodology: "store config in the environment."

## 2. Why & when

A build artifact (a JAR, a container image) that hard-codes a database URL or an API key can only ever run correctly against the one environment it was compiled for — deploying the same artifact to staging versus production would require rebuilding it with different values baked in, defeating the entire point of building once and deploying the identical artifact everywhere. Externalizing configuration breaks this coupling: the artifact is built exactly once, and the same artifact is deployed to development, staging, and production, with each environment supplying its own values from the outside at startup.

Externalize any value that legitimately differs by environment or deployment (URLs, credentials, feature flags, resource limits) or that must never be committed to source control (secrets). Values that are genuinely constant across every environment — a fixed business rule, an algorithm's internal constant — don't need externalizing; over-externalizing trivial constants just adds indirection without benefit.

## 3. Core concept

Externalized configuration works by having the application read settings from its surrounding environment at startup (or, with [dynamic refresh](0223-dynamic-runtime-configuration-refresh.md), continuously) rather than from values compiled into the code, so the identical build artifact behaves differently in each environment purely based on what's supplied around it.

```java
// BAD -- hard-coded, baked INTO the compiled artifact
String dbUrl = "jdbc:postgresql://prod-db.internal:5432/orders";

// GOOD -- read from the ENVIRONMENT at startup; the SAME artifact adapts per deployment
String dbUrl = System.getenv("DB_URL"); // supplied externally, differs per environment
if (dbUrl == null) throw new IllegalStateException("DB_URL must be set");
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One identical build artifact is deployed unchanged into three different environments -- development, staging, production -- each supplying its own externalized configuration values from the outside" >
  <rect x="250" y="15" width="140" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="40" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">ONE build artifact</text>

  <rect x="30" y="110" width="150" height="55" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="130" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Development</text>
  <text x="105" y="145" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">DB_URL=localhost</text>

  <rect x="245" y="110" width="150" height="55" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="130" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Staging</text>
  <text x="320" y="145" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">DB_URL=staging-db</text>

  <rect x="460" y="110" width="150" height="55" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="130" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Production</text>
  <text x="535" y="145" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">DB_URL=prod-db</text>

  <line x1="300" y1="55" x2="120" y2="108" stroke="#8b949e" marker-end="url(#arr218)"/>
  <line x1="320" y1="55" x2="320" y2="108" stroke="#8b949e" marker-end="url(#arr218)"/>
  <line x1="340" y1="55" x2="520" y2="108" stroke="#8b949e" marker-end="url(#arr218)"/>

  <defs>
    <marker id="arr218" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The same compiled artifact fans out to every environment; only the externally supplied configuration differs.

## 5. Runnable example

Scenario: a database-connecting service that starts with a hard-coded URL (unable to run against more than one environment without rebuilding), is refactored to read from an environment variable (the SAME artifact now adapts), and finally adds validation plus a documented default so missing or malformed external configuration fails fast with a clear error rather than silently misbehaving.

### Level 1 — Basic

```java
// File: HardCodedConfig.java -- the URL is BAKED IN; a different
// environment requires editing this file and recompiling.
public class HardCodedConfig {
    static final String DB_URL = "jdbc:postgresql://localhost:5432/orders"; // HARD-CODED

    public static void main(String[] args) {
        System.out.println("Connecting to: " + DB_URL);
        System.out.println("Deploying to production means EDITING this constant and REBUILDING.");
    }
}
```

**How to run:** `javac HardCodedConfig.java && java HardCodedConfig` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ExternalizedConfig.java -- reads DB_URL from the ENVIRONMENT;
// the SAME compiled class adapts to whatever environment it runs in.
public class ExternalizedConfig {
    public static void main(String[] args) {
        String dbUrl = System.getenv("DB_URL"); // READ from the environment, not hard-coded
        if (dbUrl == null) dbUrl = "jdbc:postgresql://localhost:5432/orders"; // a LOCAL DEV default
        System.out.println("Connecting to: " + dbUrl);
        System.out.println("This SAME .class file adapts per environment via DB_URL -- no recompilation needed.");
    }
}
```

**How to run:** `javac ExternalizedConfig.java && DB_URL="jdbc:postgresql://prod-db:5432/orders" java ExternalizedConfig` (JDK 17+); or run without the env var set to see the local default.

Expected output (with `DB_URL` set):
```
Connecting to: jdbc:postgresql://prod-db:5432/orders
This SAME .class file adapts per environment via DB_URL -- no recompilation needed.
```

### Level 3 — Advanced

```java
// File: ValidatedExternalizedConfig.java -- adds FAIL-FAST validation:
// a required value that's missing in a non-dev environment throws
// immediately with a clear message, rather than limping along broken.
public class ValidatedExternalizedConfig {
    record AppConfig(String dbUrl, String environment) {
        static AppConfig fromEnvironment() {
            String environment = System.getenv().getOrDefault("APP_ENV", "development");
            String dbUrl = System.getenv("DB_URL");

            if (dbUrl == null) {
                if (environment.equals("development")) {
                    dbUrl = "jdbc:postgresql://localhost:5432/orders"; // ONLY development gets a silent default
                } else {
                    // FAIL FAST: a non-dev environment with no DB_URL is a real misconfiguration
                    throw new IllegalStateException("DB_URL must be set explicitly when APP_ENV=" + environment);
                }
            }
            return new AppConfig(dbUrl, environment);
        }
    }

    public static void main(String[] args) {
        AppConfig devConfig = AppConfig.fromEnvironment(); // no env vars set -> falls back to dev default
        System.out.println("[" + devConfig.environment() + "] connecting to: " + devConfig.dbUrl());

        try {
            System.setProperty("APP_ENV_SIMULATION", "production"); // simulate a misconfigured prod deploy
            simulateMisconfiguredProduction();
        } catch (IllegalStateException e) {
            System.out.println("Caught expected fail-fast error: " + e.getMessage());
        }
    }

    static void simulateMisconfiguredProduction() {
        String environment = "production"; String dbUrl = null; // simulating: APP_ENV=production, DB_URL unset
        if (dbUrl == null && !environment.equals("development")) {
            throw new IllegalStateException("DB_URL must be set explicitly when APP_ENV=" + environment);
        }
    }
}
```

**How to run:** `javac ValidatedExternalizedConfig.java && java ValidatedExternalizedConfig` (JDK 17+).

Expected output:
```
[development] connecting to: jdbc:postgresql://localhost:5432/orders
Caught expected fail-fast error: DB_URL must be set explicitly when APP_ENV=production
```

## 6. Walkthrough

1. **Level 1, the coupling problem** — `DB_URL` is a `static final` constant compiled directly into the class file; running this program in any environment other than the one matching that hard-coded value requires editing the source and recompiling, which is exactly the coupling externalized configuration eliminates.
2. **Level 2, reading from the environment** — `System.getenv("DB_URL")` reads the value from the process environment at startup, external to the compiled `.class` file; the same compiled artifact, run with different `DB_URL` values set in its environment, connects to different databases without any recompilation.
3. **Level 2, a safe local default** — when `DB_URL` isn't set at all, the program falls back to a `localhost` default, which is a reasonable convenience for local development but, as Level 3 shows, becomes a real risk if that same silent fallback applies in production.
4. **Level 3, distinguishing environments** — `AppConfig.fromEnvironment()` first reads `APP_ENV` (defaulting to `"development"`) before deciding how to handle a missing `DB_URL`; this environment awareness is what lets the validation logic apply a convenient default only where it's safe to do so.
5. **Level 3, the fail-fast branch** — when `DB_URL` is missing and `environment` is anything other than `"development"`, `fromEnvironment()` throws `IllegalStateException` immediately, rather than either crashing later with a confusing connection error or silently defaulting to a `localhost` database that doesn't exist in production.
6. **Level 3, the output demonstrates both paths** — the first call (no environment variables set) resolves via the safe development default and prints its connection target; `simulateMisconfiguredProduction` reproduces the same validation logic for a `production` environment with no `DB_URL`, and the resulting `IllegalStateException` is caught and its message printed, showing the fail-fast behavior firing exactly when it should.

## 7. Gotchas & takeaways

> **Gotcha:** a "helpful" default that's safe in development (like falling back to `localhost`) is dangerous if it silently applies in every environment — an accidentally-missing `DB_URL` in production should fail loudly at startup, not quietly connect to the wrong database or crash mysteriously later; scope silent defaults to development only, as Level 3 does.

- Externalized configuration keeps environment-specific values (URLs, credentials, flags) outside the compiled artifact, so the identical build can be deployed unchanged to every environment.
- This is the third factor of the Twelve-Factor App methodology and underpins "build once, deploy everywhere."
- Values that genuinely differ by environment or must stay out of source control should be externalized; constants that never vary don't need it.
- Fail fast on missing required configuration in non-development environments rather than silently defaulting or failing later with a confusing error.
- Spring Boot's own mechanisms for this — covered next in [Spring Boot externalized configuration](0228-spring-boot-externalized-configuration-properties-yaml-env-a.md) — build directly on this same principle.
