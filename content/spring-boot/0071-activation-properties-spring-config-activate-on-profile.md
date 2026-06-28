---
card: spring-boot
gi: 71
slug: activation-properties-spring-config-activate-on-profile
title: Activation properties (spring.config.activate.on-profile)
---

## 1. What it is

`spring.config.activate.on-profile` is a property you place inside a config document (a file or a `---`-separated section) that tells Spring Boot: "only include this document's properties when the stated profile(s) are active." It is the **conditional switch** for config documents.

The key sits under a reserved Spring namespace and is consumed by the config-loading machinery before any beans are created — it never reaches your application code.

```yaml
spring:
  config:
    activate:
      on-profile: "prod"   # this document only applies in prod
```

It replaces the older `spring.profiles` key (deprecated in Boot 2.4, removed in Boot 3.0).

## 2. Why & when

Without activation properties, you need a separate file for every profile: `application-dev.yml`, `application-prod.yml`, `application-staging.yml`. Each file implicitly activates when its profile is active. That works but scatters your config across the filesystem.

`spring.config.activate.on-profile` lets you **keep everything in one file** and annotate each section explicitly. It is also the only way to conditionally activate a document inside an **imported** file — profile-named files (`application-prod.yml`) only work for files Spring Boot finds via its standard search; imported files do not get that treatment automatically.

Use it when:

- You want to colocate base config and environment overrides in a single file.
- You are importing a shared config file and want parts of it to be environment-specific.
- You need **profile expressions** — logical AND/OR/NOT across profile names.

## 3. Core concept

Think of `spring.config.activate.on-profile` like an `#ifdef` in C, or a feature flag at the config layer. The document exists in the file, but Spring treats it as invisible unless the condition is true.

**Profile expressions** (Spring Boot 2.4+) give you full boolean logic:

| Expression | Meaning |
|------------|---------|
| `prod` | Active when `prod` profile is on |
| `prod | staging` | Active when either `prod` or `staging` is on |
| `prod & eu` | Active when both `prod` and `eu` are on |
| `!dev` | Active when `dev` profile is NOT on |
| `(prod | staging) & !test` | Compound expression |

Profiles are activated by:
- `spring.profiles.active` property or environment variable (`SPRING_PROFILES_ACTIVE`)
- `SpringApplication.setAdditionalProfiles()` in code
- `@ActiveProfiles` in tests

**Processing order matters:** Spring reads documents top to bottom within a file. If Document 3 activates on `prod` and sets `log.level=WARN`, and Document 4 also activates on `prod` and sets `log.level=ERROR`, Document 4 wins because it comes later.

## 4. Diagram

<svg viewBox="0 0 700 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="spring.config.activate.on-profile: documents filtered by active profiles at load time">
  <rect width="700" height="280" rx="10" fill="#0d1117"/>

  <!-- File representation -->
  <rect x="20" y="15" width="250" height="250" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="145" y="38" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">application.yml</text>

  <!-- Doc 1: always -->
  <rect x="35" y="48" width="220" height="48" rx="4" fill="#161b22" stroke="#6db33f" stroke-width="1"/>
  <text x="50" y="66" fill="#8b949e" font-size="9" font-family="sans-serif">always loaded</text>
  <text x="50" y="82" fill="#e6edf3" font-size="10" font-family="monospace">log.level: INFO</text>

  <text x="145" y="108" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="monospace">---</text>

  <!-- Doc 2: prod -->
  <rect x="35" y="116" width="220" height="52" rx="4" fill="#161b22" stroke="#f0883e" stroke-width="1"/>
  <text x="50" y="133" fill="#f0883e" font-size="9" font-family="sans-serif">on-profile: prod</text>
  <text x="50" y="150" fill="#e6edf3" font-size="10" font-family="monospace">log.level: WARN</text>
  <text x="50" y="163" fill="#e6edf3" font-size="10" font-family="monospace">db.pool-size: 20</text>

  <text x="145" y="183" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="monospace">---</text>

  <!-- Doc 3: prod & eu -->
  <rect x="35" y="191" width="220" height="52" rx="4" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="50" y="208" fill="#79c0ff" font-size="9" font-family="sans-serif">on-profile: prod &amp; eu</text>
  <text x="50" y="225" fill="#e6edf3" font-size="10" font-family="monospace">db.host: eu-db.prod.svc</text>
  <text x="50" y="240" fill="#e6edf3" font-size="10" font-family="monospace">gdpr.enabled: true</text>

  <!-- Profile filter column -->
  <rect x="295" y="15" width="135" height="250" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="363" y="38" fill="#8b949e" font-size="10" font-weight="bold" text-anchor="middle" font-family="sans-serif">Active profiles</text>

  <text x="363" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">(none)</text>
  <text x="363" y="150" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">prod</text>
  <text x="363" y="217" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">prod, eu</text>

  <!-- Result column -->
  <rect x="458" y="15" width="220" height="250" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="568" y="38" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">Merged result</text>

  <!-- result row 1 -->
  <text x="478" y="66" fill="#8b949e" font-size="9" font-family="sans-serif">Profile: (none)</text>
  <text x="478" y="82" fill="#e6edf3" font-size="10" font-family="monospace">log.level=INFO</text>
  <line x1="468" y1="95" x2="668" y2="95" stroke="#30363d" stroke-width="1"/>

  <!-- result row 2 -->
  <text x="478" y="112" fill="#f0883e" font-size="9" font-family="sans-serif">Profile: prod</text>
  <text x="478" y="128" fill="#e6edf3" font-size="10" font-family="monospace">log.level=WARN ← doc2</text>
  <text x="478" y="144" fill="#e6edf3" font-size="10" font-family="monospace">db.pool-size=20</text>
  <line x1="468" y1="157" x2="668" y2="157" stroke="#30363d" stroke-width="1"/>

  <!-- result row 3 -->
  <text x="478" y="175" fill="#79c0ff" font-size="9" font-family="sans-serif">Profile: prod, eu</text>
  <text x="478" y="191" fill="#e6edf3" font-size="10" font-family="monospace">log.level=WARN</text>
  <text x="478" y="207" fill="#e6edf3" font-size="10" font-family="monospace">db.pool-size=20</text>
  <text x="478" y="223" fill="#e6edf3" font-size="10" font-family="monospace">db.host=eu-db...</text>
  <text x="478" y="239" fill="#e6edf3" font-size="10" font-family="monospace">gdpr.enabled=true</text>

  <!-- arrows -->
  <line x1="432" y1="72" x2="454" y2="72" stroke="#8b949e" stroke-width="1.2" marker-end="url(#aa)"/>
  <line x1="432" y1="147" x2="454" y2="135" stroke="#f0883e" stroke-width="1.2" marker-end="url(#ab)"/>
  <line x1="432" y1="217" x2="454" y2="207" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#ac)"/>

  <defs>
    <marker id="aa" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="ab" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker>
    <marker id="ac" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Each document is evaluated independently. Documents whose profile expression evaluates to `false` are completely ignored. Multiple matching documents are merged in top-to-bottom order — later keys win.

## 5. Runnable example

```java
// File: ActivationDemo.java
// Spring Boot — run with: ./gradlew bootRun  OR  mvn spring-boot:run
//
// src/main/resources/application.yml:
//
// # Document 1 — base, always loaded
// app:
//   region: global
//   log-level: INFO
//   db-pool: 5
//   gdpr: false
//
// ---
// # Document 2 — prod only
// spring:
//   config:
//     activate:
//       on-profile: "prod"
// app:
//   log-level: WARN
//   db-pool: 20
//
// ---
// # Document 3 — prod AND eu together (profile expression)
// spring:
//   config:
//     activate:
//       on-profile: "prod & eu"
// app:
//   region: eu-west-1
//   gdpr: true
//
// ---
// # Document 4 — dev OR test (OR expression)
// spring:
//   config:
//     activate:
//       on-profile: "dev | test"
// app:
//   log-level: DEBUG

package com.example;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ActivationDemo implements CommandLineRunner {

    @Value("${app.region}")
    private String region;

    @Value("${app.log-level}")
    private String logLevel;

    @Value("${app.db-pool}")
    private int dbPool;

    @Value("${app.gdpr}")
    private boolean gdpr;

    public static void main(String[] args) {
        SpringApplication.run(ActivationDemo.class, args);
    }

    @Override
    public void run(String... args) {
        System.out.println("region   : " + region);
        System.out.println("log-level: " + logLevel);
        System.out.println("db-pool  : " + dbPool);
        System.out.println("gdpr     : " + gdpr);
    }
}
```

**How to run (try each to see the different results):**

```bash
# Base config only
./gradlew bootRun
# → log-level=INFO, db-pool=5, region=global, gdpr=false

# prod profile — doc 2 activates
./gradlew bootRun --args='--spring.profiles.active=prod'
# → log-level=WARN, db-pool=20, region=global, gdpr=false

# prod + eu — doc 2 AND doc 3 activate
./gradlew bootRun --args='--spring.profiles.active=prod,eu'
# → log-level=WARN, db-pool=20, region=eu-west-1, gdpr=true

# dev — doc 4 activates (OR expression)
./gradlew bootRun --args='--spring.profiles.active=dev'
# → log-level=DEBUG, db-pool=5, region=global, gdpr=false
```

## 6. Walkthrough

- **Document 1** has no `spring.config.activate` key, so it loads unconditionally. It sets the defaults every environment starts from.
- **Document 2** (`on-profile: "prod"`) — Spring evaluates the expression `prod` against the list of active profiles. If `prod` is in the list, the document is merged: `app.log-level` becomes `WARN` and `app.db-pool` becomes `20`. `app.region` and `app.gdpr` are not defined here, so they retain their values from Document 1.
- **Document 3** (`on-profile: "prod & eu"`) — the `&` operator requires **both** `prod` and `eu` to be active. Running with just `--spring.profiles.active=prod` leaves this document inactive. Running with `prod,eu` activates both Documents 2 and 3; since Document 3 comes after Document 2, its `app.region=eu-west-1` and `app.gdpr=true` override any earlier value for those keys.
- **Document 4** (`on-profile: "dev | test"`) — activates when either `dev` or `test` is active. A developer running the app locally doesn't need to know about Documents 2 and 3; they just activate the `dev` profile and get `DEBUG` logging automatically.
- **`@Value("${app.log-level}")`** — the bean sees only the final resolved value. The profile logic is entirely in the config layer and is invisible to application code.

## 7. Gotchas & takeaways

> `spring.config.activate.on-profile` can only appear in documents **after the first `---` separator** in a multi-document file, or at the root of a standalone file (like `application-prod.yml`). Setting it in the first document of a multi-document file has no effect — that document is always loaded.

> The old key `spring.profiles` (not `spring.config.activate.on-profile`) is **removed in Spring Boot 3.0**. If you are on Boot 3.x and use `spring.profiles: prod` inside a document, Boot silently ignores it — the document loads unconditionally and you end up with all settings applied regardless of profile. Switch to the full `spring.config.activate.on-profile` key.

- Profile expressions support `|` (OR), `&` (AND), `!` (NOT), and parentheses for grouping — a significant improvement over the old comma-separated `spring.profiles` which only supported OR.
- When multiple documents match and define the same key, the **last matching document wins** within a single file.
- `on-profile` is evaluated at config-load time, before any Spring beans are created. It cannot reference bean state or environment values.
- Keep profile expressions simple — complex expressions like `(prod | staging) & !test & eu` are hard to reason about. Consider splitting into separate files if the logic gets convoluted.
- `spring.profiles.active` itself must not be set inside an `on-profile`-gated document — by the time Boot evaluates that document, the active profiles are already fixed.
