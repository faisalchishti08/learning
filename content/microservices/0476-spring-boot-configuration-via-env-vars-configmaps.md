---
card: microservices
gi: 476
slug: spring-boot-configuration-via-env-vars-configmaps
title: "Spring Boot configuration via env vars / ConfigMaps"
---

## 1. What it is

Spring Boot's `Environment` abstraction lets configuration come from **environment variables** — with a well-defined naming convention that maps automatically onto standard `application.properties`-style keys — allowing a container image to stay entirely generic while a Kubernetes ConfigMap (or Secret) injects environment variables at deploy time to configure it differently per environment, with **no rebuild** required between staging and production.

## 2. Why & when

You configure via environment variables (backed by ConfigMaps) whenever the same build artifact needs to run correctly across multiple environments without being rebuilt for each one:

- **Baking environment-specific config into the image violates the "one artifact, promoted everywhere" principle.** [Artifact versioning and promotion](0464-artifact-versioning-promotion.md) depends on the *exact same* artifact moving from staging to production — if staging and production configuration were baked in at build time, you'd need separate images per environment, breaking that guarantee entirely.
- **The twelve-factor app methodology specifically recommends config via environment variables** for exactly this reason — it's a widely-adopted, well-understood convention that keeps configuration cleanly separated from code.
- **Kubernetes ConfigMaps are the natural mechanism for supplying those environment variables per deployment.** A `Deployment` spec references a ConfigMap, and Kubernetes injects its keys as environment variables into the container at Pod startup — the same image, different ConfigMap per environment, produces correctly different behavior.
- **You use this from the very first deployment of any containerized Spring Boot service** — even a single-environment service benefits from config being external to the image, since secrets rotation, tuning, and future multi-environment needs are all far easier without a rebuild-per-change habit baked in.

## 3. Core concept

Think of a rental apartment versus a custom-built house: the apartment (the container image) is built once, generically, and each tenant (each environment) simply brings their own furniture and settings (environment variables from a ConfigMap) without the building itself needing to change. A custom-built house baked to one family's exact preferences would need actual construction work to serve a different family — exactly the rebuild Spring Boot's externalized configuration avoids.

Concretely:

1. **Spring Boot's relaxed binding maps environment variable names onto configuration property keys automatically** — an environment variable named `SPRING_DATASOURCE_URL` binds to the property `spring.datasource.url`, following a documented, predictable convention (uppercase, underscores replacing dots and hyphens).
2. **A Kubernetes ConfigMap declares key-value pairs** for non-sensitive configuration — cache TTLs, feature flags, external service URLs that differ per environment.
3. **The Deployment spec references the ConfigMap**, telling Kubernetes to inject its keys as environment variables into the container when the Pod starts.
4. **The same container image is deployed with a different ConfigMap per environment** — staging's Deployment references a staging ConfigMap, production's references a production one, with the image itself completely unchanged between them.
5. **Sensitive values (passwords, API keys) use a Kubernetes Secret instead of a ConfigMap**, injected the same way but stored and handled with Kubernetes' additional access controls around Secret objects.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same container image is deployed to staging and production with different ConfigMaps, producing different environment variables and different behavior without a rebuild" >
  <rect x="20" y="20" width="620" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">order-service:1.4.2 -- ONE image, never rebuilt per environment</text>

  <rect x="40" y="90" width="270" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="175" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">staging ConfigMap</text>
  <text x="175" y="129" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">CACHE_TTL_SECONDS=30</text>

  <rect x="350" y="90" width="270" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="485" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">production ConfigMap</text>
  <text x="485" y="129" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">CACHE_TTL_SECONDS=600</text>

  <line x1="200" y1="65" x2="200" y2="90" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="460" y1="65" x2="460" y2="90" stroke="#8b949e" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The identical image reads different environment variables per deployment, sourced from a different ConfigMap in each environment.

## 5. Runnable example

Scenario: a configuration loader that reads environment-variable-style keys and binds them onto application settings, exactly like Spring Boot's relaxed binding. We start with a basic single-environment binding, extend it to the same code loading two different ConfigMaps for two environments, then handle the hard case: a required configuration key missing entirely from one environment's ConfigMap, which must fail with a clear error rather than silently defaulting to something wrong.

### Level 1 — Basic

```java
// File: EnvVarConfigBasic.java -- models Spring Boot's relaxed binding:
// an environment-variable-style key (SPRING_DATASOURCE_URL) is mapped
// onto a dotted configuration property (spring.datasource.url).
import java.util.*;

public class EnvVarConfigBasic {
    static String relaxedBind(Map<String, String> envVars, String propertyKey) {
        // Mirrors Spring's convention: dots/hyphens become underscores, uppercased.
        String envVarName = propertyKey.toUpperCase().replace(".", "_").replace("-", "_");
        return envVars.get(envVarName);
    }

    public static void main(String[] args) {
        Map<String, String> envVars = Map.of(
            "SPRING_DATASOURCE_URL", "jdbc:postgresql://prod-db:5432/orders",
            "SERVER_PORT", "8080"
        );

        String dbUrl = relaxedBind(envVars, "spring.datasource.url");
        String port = relaxedBind(envVars, "server.port");
        System.out.println("[config] spring.datasource.url = " + dbUrl);
        System.out.println("[config] server.port = " + port);
    }
}
```

How to run: `java EnvVarConfigBasic.java`

`relaxedBind` implements the exact naming transformation Spring Boot's real relaxed binding performs: dots become underscores and the whole key is uppercased, so `"spring.datasource.url"` is looked up as `"SPRING_DATASOURCE_URL"` in the environment map — application code only ever deals with the clean, dotted property name; the environment-variable naming convention is an implementation detail this function hides.

### Level 2 — Intermediate

```java
// File: EnvVarConfigPerEnvironment.java -- the SAME binding logic, now
// applied to TWO DIFFERENT simulated ConfigMaps -- staging and
// production -- producing DIFFERENT configuration from the exact SAME
// binding code, modeling one image deployed with two different ConfigMaps.
import java.util.*;

public class EnvVarConfigPerEnvironment {
    static String relaxedBind(Map<String, String> envVars, String propertyKey) {
        String envVarName = propertyKey.toUpperCase().replace(".", "_").replace("-", "_");
        return envVars.get(envVarName);
    }

    static void printConfig(String environmentName, Map<String, String> envVars) {
        String cacheTtl = relaxedBind(envVars, "cache.ttl-seconds");
        String dbUrl = relaxedBind(envVars, "spring.datasource.url");
        System.out.println("[" + environmentName + "] cache.ttl-seconds = " + cacheTtl + ", spring.datasource.url = " + dbUrl);
    }

    public static void main(String[] args) {
        Map<String, String> stagingConfigMap = Map.of(
            "CACHE_TTL_SECONDS", "30",
            "SPRING_DATASOURCE_URL", "jdbc:postgresql://staging-db:5432/orders"
        );
        Map<String, String> productionConfigMap = Map.of(
            "CACHE_TTL_SECONDS", "600",
            "SPRING_DATASOURCE_URL", "jdbc:postgresql://prod-db:5432/orders"
        );

        System.out.println("[image] order-service:1.4.2 -- the SAME artifact, deployed twice");
        printConfig("staging", stagingConfigMap);
        printConfig("production", productionConfigMap);
    }
}
```

How to run: `java EnvVarConfigPerEnvironment.java`

`printConfig` runs the exact same `relaxedBind` calls regardless of which environment's map is passed in — no `if (environmentName.equals("production"))` branching exists anywhere in this code. The different output values come entirely from the different `envVars` map each call receives, exactly mirroring how the same container image produces different runtime behavior purely because Kubernetes injected a different ConfigMap's values as its environment variables.

### Level 3 — Advanced

```java
// File: EnvVarConfigMissingKey.java -- the SAME per-environment binding,
// now handling the PRODUCTION-FLAVORED hard case: a REQUIRED
// configuration key is MISSING from one environment's ConfigMap entirely
// (e.g. someone forgot to add it when creating the staging ConfigMap).
// The application must FAIL LOUDLY and SPECIFICALLY at startup, not
// silently proceed with a null or default value that could cause a
// hard-to-diagnose failure much later, deep inside request handling.
import java.util.*;

public class EnvVarConfigMissingKey {
    static String relaxedBind(Map<String, String> envVars, String propertyKey) {
        String envVarName = propertyKey.toUpperCase().replace(".", "_").replace("-", "_");
        return envVars.get(envVarName);
    }

    static String requireProperty(Map<String, String> envVars, String propertyKey) {
        String value = relaxedBind(envVars, propertyKey);
        if (value == null) {
            throw new IllegalStateException(
                "required configuration property '" + propertyKey + "' is missing -- "
                + "expected environment variable '" + propertyKey.toUpperCase().replace(".", "_").replace("-", "_")
                + "' was not set (check the ConfigMap for this environment)");
        }
        return value;
    }

    static void startApplication(String environmentName, Map<String, String> envVars) {
        System.out.println("[" + environmentName + "] starting application, validating required configuration...");
        try {
            String dbUrl = requireProperty(envVars, "spring.datasource.url");
            String cacheTtl = requireProperty(envVars, "cache.ttl-seconds");
            System.out.println("[" + environmentName + "] startup SUCCESSFUL: db=" + dbUrl + " cacheTtl=" + cacheTtl);
        } catch (IllegalStateException e) {
            System.out.println("[" + environmentName + "] STARTUP FAILED: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        Map<String, String> productionConfigMap = Map.of(
            "CACHE_TTL_SECONDS", "600",
            "SPRING_DATASOURCE_URL", "jdbc:postgresql://prod-db:5432/orders"
        );
        // Someone forgot to add SPRING_DATASOURCE_URL to the staging ConfigMap.
        Map<String, String> incompleteStagingConfigMap = Map.of(
            "CACHE_TTL_SECONDS", "30"
        );

        startApplication("production", productionConfigMap);
        System.out.println();
        startApplication("staging", incompleteStagingConfigMap);
    }
}
```

How to run: `java EnvVarConfigMissingKey.java`

`requireProperty` wraps `relaxedBind` with an explicit `null` check, throwing an `IllegalStateException` that names both the missing dotted property key and the exact environment variable name Kubernetes was expected to inject — actionable information for whoever's debugging a broken staging ConfigMap. `startApplication` for `"production"` succeeds because both required keys are present, while `"staging"`'s call throws on the second `requireProperty` call, since `incompleteStagingConfigMap` never defines `SPRING_DATASOURCE_URL` — the `catch` block in `startApplication` reports the failure clearly rather than letting the application silently start with a broken or missing database URL.

## 6. Walkthrough

Trace `EnvVarConfigMissingKey.main` in order. **First**, `startApplication("production", productionConfigMap)` runs. Inside its `try` block, `requireProperty(envVars, "spring.datasource.url")` calls `relaxedBind`, which finds `"SPRING_DATASOURCE_URL"` present in `productionConfigMap` and returns its value — not `null`, so no exception is thrown. The same happens for `"cache.ttl-seconds"`. Both required properties resolve successfully, so the success message prints with both values.

**Next**, `startApplication("staging", incompleteStagingConfigMap)` runs. Its `try` block first calls `requireProperty(envVars, "spring.datasource.url")` — `relaxedBind` looks up `"SPRING_DATASOURCE_URL"` in `incompleteStagingConfigMap`, which doesn't contain that key at all, so `relaxedBind` returns `null`.

**Then**, back inside `requireProperty`, the `if (value == null)` check is `true`, so it constructs and throws an `IllegalStateException` naming both the dotted property (`spring.datasource.url`) and the exact environment variable name that was expected but missing.

**After that**, this exception propagates directly out of `requireProperty` and out of the first line inside `startApplication`'s `try` block — the second `requireProperty` call (for `cache.ttl-seconds`) never executes at all, since the first one already threw.

**Finally**, `startApplication`'s `catch (IllegalStateException e)` block catches the exception and prints a clear "STARTUP FAILED" message including the full, specific reason — mirroring how a real Spring Boot application should fail fast and loud at startup when required configuration is missing, rather than starting up successfully and only failing much later, deep inside a request handler trying to use a `null` database URL.

```
[production] starting application, validating required configuration...
[production] startup SUCCESSFUL: db=jdbc:postgresql://prod-db:5432/orders cacheTtl=600

[staging] starting application, validating required configuration...
[staging] STARTUP FAILED: required configuration property 'spring.datasource.url' is missing -- expected environment variable 'SPRING_DATASOURCE_URL' was not set (check the ConfigMap for this environment)
```

## 7. Gotchas & takeaways

> An application that starts up successfully despite missing required configuration — silently falling back to a `null` or a hardcoded default — defers the failure to whenever that configuration is first actually used, which is often deep inside a request handler, far from the real root cause and far harder to diagnose than a clear startup-time error would have been.
- Fail fast on missing required configuration at startup, exactly as `requireProperty` does — Spring Boot's own `@ConfigurationProperties` validation (paired with `@Validated` and Bean Validation annotations) provides this same fail-fast behavior for real applications.
- Use ConfigMaps for non-sensitive configuration and Kubernetes Secrets for anything sensitive (credentials, API keys) — both inject as environment variables the same way, but Secrets get additional access-control and at-rest handling from Kubernetes.
- This mechanism is what actually makes [artifact versioning and promotion](0464-artifact-versioning-promotion.md) practical — the same immutable artifact behaving correctly in every environment depends entirely on configuration being externalized rather than baked into the image.
- Keep environment-variable-derived configuration validated and documented — a growing, undocumented set of expected environment variables is a common source of "works in one environment, breaks in another" surprises.
- Test startup failure paths deliberately, not just the happy path — deploying a ConfigMap with a typo'd or missing key should be caught immediately and loudly during a canary or staging rollout, not discovered by a confused on-call engineer during an incident.
