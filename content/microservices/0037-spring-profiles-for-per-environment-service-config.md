---
card: microservices
gi: 37
slug: spring-profiles-for-per-environment-service-config
title: Spring profiles for per-environment service config
---

## 1. What it is

**Spring profiles** let a single service artifact — the exact same `.jar` file — behave differently depending on which environment it's running in, by activating a named set of configuration (`application-dev.yml`, `application-staging.yml`, `application-prod.yml`) at startup rather than baking environment-specific values into the code or requiring a separate build per environment. A service built once as `orders-service.jar` can run in development with an in-memory database and verbose logging, or in production with a real database connection pool and minimal logging, purely by activating a different profile (`--spring.profiles.active=prod`) at launch — with zero code changes and zero rebuilding.

```java
@Configuration
@Profile("prod") // this bean is ONLY created when the "prod" profile is active
public class ProductionDataSourceConfig {
    @Bean DataSource dataSource() { return /* real connection pool */ null; }
}
```

## 2. Why & when

Building a separate artifact per environment — one `.jar` for dev, a different one for staging, a different one for production — reintroduces exactly the risk [infrastructure automation](0010-infrastructure-automation.md) exists to eliminate: what's tested in staging is no longer, strictly, the same artifact that runs in production, since each was compiled or configured slightly differently. Profiles avoid this by keeping the build artifact identical across every environment, and moving all environment-specific difference into configuration selected at startup.

Use profiles for any configuration that genuinely differs by environment — database connection details, logging verbosity, feature flags for gradual rollout, external service URLs — while keeping business logic entirely profile-independent. If you find yourself writing `if (profile.equals("prod")) { ... }` directly inside business logic, that's usually a sign the difference belongs in configuration (a profile-specific bean or property), not in conditional code paths scattered through the application.

## 3. Core concept

The same artifact, different configuration selected at launch:

```
orders-service.jar                     (built ONCE)
        |
   --spring.profiles.active=dev    -> loads application-dev.yml    -> H2 in-memory DB, DEBUG logging
   --spring.profiles.active=staging -> loads application-staging.yml -> shared test DB, INFO logging
   --spring.profiles.active=prod   -> loads application-prod.yml   -> production DB pool, WARN logging
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One built artifact, orders-service.jar, is launched with different active profiles to produce different environment-specific configuration without rebuilding">
  <rect x="250" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">orders-service.jar</text>

  <rect x="30" y="100" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="122" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">profile: dev</text>
  <text x="105" y="138" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">H2, DEBUG logging</text>

  <rect x="245" y="100" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="122" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">profile: staging</text>
  <text x="320" y="138" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">shared DB, INFO logging</text>

  <rect x="460" y="100" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="122" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">profile: prod</text>
  <text x="535" y="138" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">real DB pool, WARN logging</text>

  <line x1="290" y1="60" x2="105" y2="100" stroke="#8b949e" stroke-width="1"/>
  <line x1="320" y1="60" x2="320" y2="100" stroke="#8b949e" stroke-width="1"/>
  <line x1="350" y1="60" x2="535" y2="100" stroke="#8b949e" stroke-width="1"/>
</svg>

One built artifact, three different configurations selected purely by which profile is active at launch.

## 5. Runnable example

Scenario: a service whose database and logging configuration must differ by environment, first hardcoded (forcing a rebuild per environment), then profile-driven with a single artifact, then extended to show profile-specific bean selection.

### Level 1 — Basic

```java
// File: HardcodedConfig.java -- environment baked directly into the code,
// requiring a REBUILD to change environments.
public class HardcodedConfig {
    static final String DATABASE_URL = "jdbc:h2:mem:devdb"; // hardcoded for DEV -- changing this means editing code + rebuilding
    static final String LOG_LEVEL = "DEBUG";

    public static void main(String[] args) {
        System.out.println("connecting to: " + DATABASE_URL + ", log level: " + LOG_LEVEL);
    }
}
```

**How to run:** `javac HardcodedConfig.java && java HardcodedConfig` (JDK 17+).

Expected output:
```
connecting to: jdbc:h2:mem:devdb, log level: DEBUG
```

To run this same service against a production database, someone would need to edit `DATABASE_URL` directly and recompile — meaning the artifact tested in development is never, strictly, the same artifact that runs in production.

### Level 2 — Intermediate

```java
// File: ProfileDrivenConfig.java -- the SAME artifact, environment
// selected via a launch-time argument, mirroring --spring.profiles.active.
import java.util.*;

public class ProfileDrivenConfig {
    static Map<String, Map<String, String>> profileConfigs = Map.of(
        "dev", Map.of("databaseUrl", "jdbc:h2:mem:devdb", "logLevel", "DEBUG"),
        "staging", Map.of("databaseUrl", "jdbc:postgresql://staging-db:5432/orders", "logLevel", "INFO"),
        "prod", Map.of("databaseUrl", "jdbc:postgresql://prod-db-cluster:5432/orders", "logLevel", "WARN")
    );

    public static void main(String[] args) {
        String activeProfile = args.length > 0 ? args[0] : "dev"; // selected at LAUNCH TIME, not compile time
        Map<String, String> config = profileConfigs.get(activeProfile);
        System.out.println("active profile: " + activeProfile);
        System.out.println("connecting to: " + config.get("databaseUrl") + ", log level: " + config.get("logLevel"));
    }
}
```

**How to run:** `javac ProfileDrivenConfig.java && java ProfileDrivenConfig prod` (JDK 17+). Try also `java ProfileDrivenConfig dev` or with no argument.

Expected output (for `java ProfileDrivenConfig prod`):
```
active profile: prod
connecting to: jdbc:postgresql://prod-db-cluster:5432/orders, log level: WARN
```

The exact same compiled `.class` file (no rebuild) produces entirely different configuration depending on the `activeProfile` argument passed at launch — precisely mirroring how `--spring.profiles.active=prod` selects `application-prod.yml` for the same, unmodified `.jar`.

### Level 3 — Advanced

```java
// File: ProfileSpecificBeans.java -- profiles selecting entire BEAN
// IMPLEMENTATIONS, not just property values, mirroring @Profile-annotated beans.
import java.util.*;

public class ProfileSpecificBeans {
    interface DataSource { String describe(); void connect(); }

    static class DevDataSource implements DataSource { // stands in for a @Profile("dev") bean
        public String describe() { return "in-memory H2 (fast, resets on restart)"; }
        public void connect() { System.out.println("connected to in-memory H2"); }
    }

    static class ProdDataSource implements DataSource { // stands in for a @Profile("prod") bean
        int poolSize = 20;
        public String describe() { return "production PostgreSQL pool (size=" + poolSize + ")"; }
        public void connect() { System.out.println("connected via pooled connection (pool size " + poolSize + ")"); }
    }

    // models Spring's @Profile-based bean SELECTION -- only ONE implementation is chosen, based on active profile
    static DataSource selectDataSourceForProfile(String activeProfile) {
        return switch (activeProfile) {
            case "prod" -> new ProdDataSource();
            default -> new DevDataSource(); // dev and any unrecognized profile fall back to a safe default
        };
    }

    public static void main(String[] args) {
        String activeProfile = args.length > 0 ? args[0] : "dev";
        DataSource dataSource = selectDataSourceForProfile(activeProfile);

        System.out.println("profile: " + activeProfile + " -> " + dataSource.describe());
        dataSource.connect(); // the calling code is IDENTICAL regardless of which implementation was selected
    }
}
```

**How to run:** `javac ProfileSpecificBeans.java && java ProfileSpecificBeans prod` (JDK 17+). Try also `java ProfileSpecificBeans dev`.

Expected output (for `java ProfileSpecificBeans prod`):
```
profile: prod -> production PostgreSQL pool (size=20)
connected via pooled connection (pool size 20)
```

The production-flavored payoff: `selectDataSourceForProfile` doesn't just swap a string value — it selects an entirely different `DataSource` *implementation*, with genuinely different behavior (`ProdDataSource` tracks a real pool size; `DevDataSource` doesn't need to). The calling code in `main` (`dataSource.connect()`) is completely unaware of which implementation it received — exactly how `@Profile`-annotated beans work in a real Spring service: the profile decides *which bean* satisfies a given interface, and the rest of the application depends only on the interface.

## 6. Walkthrough

1. `String activeProfile = args.length > 0 ? args[0] : "dev"` reads the launch-time argument — for `java ProfileSpecificBeans prod`, this becomes `"prod"`.
2. `selectDataSourceForProfile("prod")` runs its `switch` statement: the case `"prod"` matches, so it constructs and returns a `new ProdDataSource()` — the `default` branch (which would have constructed a `DevDataSource`) is never reached.
3. Back in `main`, `dataSource` now holds a `ProdDataSource` instance, but typed only as the `DataSource` interface — `main`'s remaining code has no compile-time or run-time way to distinguish which concrete class it's holding, beyond calling the interface's own methods.
4. `dataSource.describe()` resolves, at run time, to `ProdDataSource.describe()`, returning `"production PostgreSQL pool (size=20)"` — reading `ProdDataSource`'s own `poolSize` field, something `DevDataSource` doesn't even have.
5. `dataSource.connect()` resolves to `ProdDataSource.connect()`, printing the pool-size-aware connection message — again, entirely different behavior from what `DevDataSource.connect()` would have printed, selected purely by which profile was active at launch, with zero changes to `main`'s own code.

```
java ProfileSpecificBeans prod
        |
activeProfile = "prod"
        |
selectDataSourceForProfile("prod") -> ProdDataSource (chosen over DevDataSource)
        |
dataSource.describe() / .connect()  -- calling code UNCHANGED, behavior driven by WHICH bean was selected
```

## 7. Gotchas & takeaways

> **Gotcha:** it's easy to accidentally let a "dev-only convenience" default leak into production if the profile-selection logic has a permissive fallback — `selectDataSourceForProfile`'s `default -> new DevDataSource()` branch means *any* unrecognized or misspelled profile name (a typo like `"prd"` instead of `"prod"`) silently falls back to the dev configuration rather than failing loudly. In a real service, prefer failing fast on an unrecognized profile over silently defaulting to a potentially unsafe configuration.

- Spring profiles let one built artifact behave differently per environment by activating different named configuration sets at launch, rather than requiring a separate build or hardcoded environment-specific values.
- The core benefit is artifact integrity: the exact same `.jar` tested in staging is the exact same `.jar` that runs in production, with only its active profile differing — eliminating the risk of environment-specific build drift.
- Profiles can select entire bean implementations (`@Profile`-annotated beans), not just property values — letting genuinely different behavior (a real connection pool versus an in-memory database) be chosen purely by environment, while calling code depends only on a shared interface.
- Business logic itself should stay profile-independent — if application code branches directly on which profile is active, that's usually a sign the difference belongs in configuration or bean selection instead.
