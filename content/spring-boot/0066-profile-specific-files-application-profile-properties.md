---
card: spring-boot
gi: 66
slug: profile-specific-files-application-profile-properties
title: Profile-specific files (application-{profile}.properties)
---

## 1. What it is

**Profile-specific config files** are named `application-{profile}.properties` (or `.yml`), where `{profile}` matches the name of an active Spring profile. Spring Boot loads them automatically alongside the base `application.properties`, and the profile-specific file **overlays** (patches) the base — it doesn't replace it.

```
src/main/resources/
  application.properties          ← always loaded (base config)
  application-dev.properties      ← loaded when profile "dev" is active
  application-prod.properties     ← loaded when profile "prod" is active
  application-test.yml            ← loaded when profile "test" is active
```

Activate a profile via `--spring.profiles.active=dev` (CLI), `SPRING_PROFILES_ACTIVE=prod` (env var), or `spring.profiles.active=test` in `application.properties`.

## 2. Why & when

Every non-trivial application runs in at least three environments: **dev**, **staging/QA**, and **prod**. Each environment needs different values for:

- Database URLs (local H2 vs. staging MySQL vs. prod RDS)
- Log levels (DEBUG in dev, WARN in prod)
- External service endpoints (mock server in dev, real API in prod)
- Connection pool sizes, timeouts, feature flags

Without profile-specific files you either:
- Keep all environments in `application.properties` behind comments (error-prone, cluttered).
- Use env vars for every difference (dozens of variables, easy to forget one).
- Maintain separate source branches per environment (merge hell).

Profile-specific files let you keep the **base config in one file** (committed to git, safe defaults) and put **environment-specific overrides in separate files** (also in git, clearly named, reviewed like code). The base config stays DRY; the diff between environments is visible and explicit.

Use them when:
- You have two or more environments with meaningfully different config.
- You want environment config reviewed in pull requests like any other code.
- You want to see exactly what changes between dev and prod in a single `diff`.

## 3. Core concept

Think of the base `application.properties` as a **form with default values pre-filled**. A profile-specific file is a **correction sheet** stapled on top. You only write on the correction sheet what needs to change — everything else comes from the original form. The combined result is what the app reads.

**Loading order within the config-data source tier:**

```
1. application.properties          (base, lowest priority in this tier)
2. application-{profile}.properties (overlay, higher priority)
```

A key defined in `application-prod.properties` overrides the same key in `application.properties`. A key in `application.properties` that has no counterpart in the profile file keeps its base value.

**Multiple active profiles:**

You can activate several profiles at once:

```bash
--spring.profiles.active=prod,monitoring
```

Both `application-prod.properties` and `application-monitoring.properties` are loaded. If they both define the same key, the **last profile in the list wins** (`monitoring` in this example).

**Profile groups (Spring Boot 2.4+):**

```properties
# application.properties
spring.profiles.group.production=prod,monitoring,security
```

Then `--spring.profiles.active=production` activates all three member profiles in one shot.

**Where profile files are searched:**

The same location search as the base file: classpath root, classpath `/config/`, working directory, working directory `/config/`. Files outside the JAR (working directory) override files inside the JAR (classpath) within the same priority tier.

## 4. Diagram

<svg viewBox="0 0 700 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Base application.properties overlaid by profile-specific file when profile is active">
  <defs>
    <marker id="arr66" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/>
    </marker>
    <marker id="arr66b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Base file -->
  <rect x="20" y="30" width="230" height="120" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="36" y="52" fill="#8b949e" font-size="11" font-family="sans-serif">application.properties (base)</text>
  <text x="36" y="72" fill="#e6edf3" font-size="12" font-family="monospace">server.port=8080</text>
  <text x="36" y="90" fill="#e6edf3" font-size="12" font-family="monospace">log.level=INFO</text>
  <text x="36" y="108" fill="#e6edf3" font-size="12" font-family="monospace">db.url=jdbc:h2:mem:dev</text>
  <text x="36" y="126" fill="#e6edf3" font-size="12" font-family="monospace">app.debug=false</text>

  <!-- Profile file -->
  <rect x="20" y="180" width="230" height="100" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.8"/>
  <text x="36" y="202" fill="#6db33f" font-size="11" font-family="sans-serif">application-prod.properties</text>
  <text x="36" y="224" fill="#6db33f" font-size="12" font-family="monospace">db.url=jdbc:mysql://prod/shop</text>
  <text x="36" y="242" fill="#6db33f" font-size="12" font-family="monospace">log.level=WARN</text>
  <text x="36" y="264" fill="#8b949e" font-size="11" font-family="monospace">(only overrides these 2)</text>

  <!-- Arrows to merge -->
  <line x1="254" y1="90"  x2="390" y2="150" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr66)"/>
  <line x1="254" y1="230" x2="390" y2="170" stroke="#6db33f" stroke-width="2"   marker-end="url(#arr66)"/>

  <!-- Merged result -->
  <rect x="394" y="90" width="265" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="410" y="112" fill="#8b949e" font-size="11" font-family="sans-serif">merged Environment (prod active)</text>
  <text x="410" y="133" fill="#e6edf3" font-size="12" font-family="monospace">server.port = 8080    ← base</text>
  <text x="410" y="153" fill="#6db33f" font-size="12" font-family="monospace">log.level   = WARN    ← prod</text>
  <text x="410" y="173" fill="#6db33f" font-size="12" font-family="monospace">db.url      = jdbc:mysql://...</text>
  <text x="410" y="193" fill="#e6edf3" font-size="12" font-family="monospace">app.debug   = false   ← base</text>

  <!-- Active profile label -->
  <rect x="290" y="278" width="200" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="390" y="298" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">--spring.profiles.active=prod</text>
</svg>

*The profile file only needs to list keys that differ from the base. Everything else silently inherits from `application.properties`. Unset keys in the profile file are not blanked — they pass through from the base.*

## 5. Runnable example

```java
// ProfileConfigDemo.java — Spring Boot 3.x project

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class ProfileConfigDemo {

    @Value("${db.url}")
    private String dbUrl;

    @Value("${log.level}")
    private String logLevel;

    @Value("${server.port}")
    private int port;

    @Value("${app.debug:false}")
    private boolean debug;

    @GetMapping("/env")
    public String env() {
        return String.format(
            "port=%d | db=%s | log=%s | debug=%b",
            port, dbUrl, logLevel, debug
        );
    }

    public static void main(String[] args) {
        SpringApplication.run(ProfileConfigDemo.class, args);
    }
}
```

`src/main/resources/application.properties` (base — always loaded):
```properties
server.port=8080
db.url=jdbc:h2:mem:devdb
log.level=DEBUG
app.debug=false
```

`src/main/resources/application-dev.properties` (dev overlay):
```properties
app.debug=true
```

`src/main/resources/application-prod.properties` (prod overlay):
```properties
server.port=8443
db.url=jdbc:mysql://prod-host:3306/shop
log.level=WARN
```

**How to run:**

```bash
# Default (no profile) — base config only
./mvnw spring-boot:run
# http://localhost:8080/env
# port=8080 | db=jdbc:h2:mem:devdb | log=DEBUG | debug=false

# Dev profile
./mvnw spring-boot:run -Dspring-boot.run.arguments=--spring.profiles.active=dev
# http://localhost:8080/env
# port=8080 | db=jdbc:h2:mem:devdb | log=DEBUG | debug=true
#   ↑ only app.debug changed; everything else came from base

# Prod profile
./mvnw spring-boot:run -Dspring-boot.run.arguments=--spring.profiles.active=prod
# http://localhost:8443/env
# port=8443 | db=jdbc:mysql://prod-host:3306/shop | log=WARN | debug=false
#   ↑ three keys overridden; app.debug came from base (false)
```

## 6. Walkthrough

1. `application.properties` is always loaded. It defines all four properties with sensible defaults (local H2 DB, DEBUG logging, port 8080).
2. When the `dev` profile is active, Spring Boot also loads `application-dev.properties`. It defines only `app.debug=true`. The other three keys come unchanged from the base.
3. When the `prod` profile is active, Spring Boot loads `application-prod.properties` instead. It overrides three keys. `app.debug` is not mentioned in the prod file, so the base value `false` is used — the prod file doesn't need to explicitly set everything, only the differences.
4. Notice `server.port=8443` in the prod file — this overrides Tomcat's listen port, so the prod run starts on 8443 not 8080.
5. Profile activation via `--spring.profiles.active=prod` is itself a property, so it can also be set in `application.properties` as `spring.profiles.active=dev` (useful to make `dev` the default for local development without needing a flag every time).

## 7. Gotchas & takeaways

> A profile-specific file **overlays**, it does not replace, the base file. This is almost always what you want — but it means you cannot "blank out" a key by omitting it from the profile file. If you need a key absent in one profile, set it to an empty string explicitly: `my.key=`.

> If you set `spring.profiles.active=dev` in `application.properties` as a convenience default, remember that anyone running a production deployment must ensure the prod profile is activated explicitly — otherwise the application quietly uses dev defaults in production.

- File name pattern: `application-{profile}.properties` or `application-{profile}.yml`. The `{profile}` part is case-sensitive on case-sensitive filesystems (Linux). Use lowercase profile names to avoid surprises.
- Multiple profiles at once: `--spring.profiles.active=prod,monitoring` loads both profile files; the last profile in the list wins if both define the same key.
- Profile groups (`spring.profiles.group.production=prod,monitoring`) let you activate a named set of profiles with a single name — great for keeping prod activation simple.
- You can define profile-specific config in a **single YAML file** using `---` document separators and `spring.config.activate.on-profile:` — useful for small projects, but can get unwieldy as the config grows. Separate files scale better.
- Profile-specific files outside the JAR (in the working directory or its `/config/` subdirectory) override profile-specific files inside the JAR — giving ops teams a clean override path without rebuilding.
- Keep secrets out of all config files, even profile-specific ones. Use environment variables or a secrets manager and reference them in the profile file only if necessary (e.g., `db.password=${DB_PASSWORD}`).
