---
card: spring-boot
gi: 89
slug: profile-specific-configuration-files
title: Profile-specific configuration files
---

## 1. What it is

A **profile-specific configuration file** is a properties or YAML file that Spring Boot loads **only when a matching profile is active**. The naming convention is:

```
application-{profile}.properties
application-{profile}.yml
```

For example: `application-dev.properties`, `application-prod.yml`.

Spring Boot automatically discovers and loads these files from the same locations it searches for `application.properties` (classpath root, classpath `/config`, file-system `./config/`, file-system `./`). The file's properties **overlay** the base `application.properties`: values in the profile file take precedence; keys that are absent in the profile file keep their base values.

## 2. Why & when

Profile-specific files separate environment concerns without requiring code changes or complex conditional logic. They are the primary mechanism for supplying environment-specific values:

- Database URLs and credentials differ between `dev`, `staging`, and `prod`.
- Pool sizes and timeout values are tuned differently per environment.
- Feature flags or third-party API keys change between environments.
- Logging verbosity is `DEBUG` in dev and `WARN` in prod.

The advantage over embedding environment-specific values in code is that the same compiled artifact can be deployed to any environment by simply providing the appropriate profile-specific file — either in the JAR or externally in a mounted config directory.

## 3. Core concept

Spring Boot loads configuration files in this order (last wins for duplicate keys):

```
1. application.properties          (always, base values)
2. application-{profile}.properties (for each active profile, in activation order)
3. External config dir (./config/application.properties + profile files)
```

If both `dev` and `cloud` are active:
- `application.properties` → base
- `application-dev.properties` → overlays base
- `application-cloud.properties` → overlays the result so far

Key rule: if the same key appears in two profile files, the **last one in the activation order** wins. `spring.profiles.active=dev,cloud` means `cloud` overrides `dev` for any shared key.

YAML files support multi-document syntax: a single `application.yml` can contain sections for multiple profiles using `---` separators and a `spring.config.activate.on-profile` key (Spring Boot 2.4+):

```yaml
# default section
server:
  port: 8080
---
spring:
  config:
    activate:
      on-profile: prod
server:
  port: 443
```

## 4. Diagram

<svg viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Property layering: base file always loads, then profile-specific files overlay in activation order, last key wins">
  <rect x="8" y="8" width="664" height="284" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Property Layering — active profiles: dev, cloud</text>

  <!-- Base layer -->
  <rect x="40" y="50" width="600" height="52" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">application.properties  (always loaded)</text>
  <text x="340" y="88" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">db.url=jdbc:h2:mem:base  |  server.port=8080  |  logging.level.root=INFO</text>

  <!-- dev layer -->
  <rect x="40" y="118" width="600" height="52" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="138" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">application-dev.properties  (loaded 2nd)</text>
  <text x="340" y="156" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">db.url=jdbc:h2:mem:devdb  |  logging.level.root=DEBUG</text>

  <!-- cloud layer -->
  <rect x="40" y="186" width="600" height="52" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="206" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">application-cloud.properties  (loaded 3rd, last wins)</text>
  <text x="340" y="224" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">server.port=443  |  db.url=jdbc:postgresql://cloud-db/app</text>

  <!-- Arrows -->
  <defs><marker id="lay" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="340" y1="103" x2="340" y2="116" stroke="#8b949e" stroke-width="1.5" marker-end="url(#lay)"/>
  <line x1="340" y1="171" x2="340" y2="184" stroke="#8b949e" stroke-width="1.5" marker-end="url(#lay)"/>

  <!-- Resolved -->
  <rect x="40" y="254" width="600" height="30" rx="5" fill="#0d1117" stroke="#f0883e" stroke-width="1.5"/>
  <text x="340" y="274" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">Resolved: db.url=…cloud-db/app | server.port=443 | logging.level.root=DEBUG</text>
</svg>

Each layer overrides only the keys it defines; unmentioned keys survive from lower layers.

## 5. Runnable example

```java
// ProfileConfigFiles.java — run: java ProfileConfigFiles.java  (JDK 17+)
// Simulates profile-specific property file loading and key-override layering.

import java.util.*;

public class ProfileConfigFiles {

    // Simulated property sources (in loading order)
    static Map<String, String> baseProps() {
        return new LinkedHashMap<>(Map.of(
            "db.url",              "jdbc:h2:mem:base",
            "server.port",         "8080",
            "logging.level.root",  "INFO",
            "app.name",            "my-service"
        ));
    }

    static Map<String, String> devProps() {
        return Map.of(
            "db.url",             "jdbc:h2:mem:devdb",
            "logging.level.root", "DEBUG"
        );
    }

    static Map<String, String> cloudProps() {
        return Map.of(
            "db.url",     "jdbc:postgresql://cloud-db.example.com/app",
            "server.port", "443"
        );
    }

    static Map<String, String> prodProps() {
        return Map.of(
            "db.url",              "jdbc:postgresql://prod-db.example.com/app",
            "server.port",         "443",
            "logging.level.root",  "WARN"
        );
    }

    static Map<String, String> resolve(List<String> activeProfiles) {
        Map<String, String> resolved = baseProps();
        for (String profile : activeProfiles) {
            Map<String, String> overlay = switch (profile) {
                case "dev"   -> devProps();
                case "cloud" -> cloudProps();
                case "prod"  -> prodProps();
                default      -> Map.of();
            };
            resolved.putAll(overlay);  // later profile wins on conflict
        }
        return resolved;
    }

    static void show(String label, List<String> profiles) {
        System.out.println("=== " + label + " ===");
        System.out.println("Active: " + profiles);
        resolve(profiles).forEach((k, v) -> System.out.printf("  %-25s = %s%n", k, v));
        System.out.println();
    }

    public static void main(String[] args) {
        show("No active profile (base only)", List.of());
        show("dev only",                      List.of("dev"));
        show("dev + cloud",                   List.of("dev", "cloud"));
        show("prod (overrides dev if both active — rare but shown)", List.of("dev", "prod"));
    }
}
```

**How to run:** `java ProfileConfigFiles.java`

In a real Spring Boot project, create `src/main/resources/application-dev.properties` with the dev keys; Spring Boot loads it automatically when `dev` is active.

## 6. Walkthrough

- `baseProps()` represents `application.properties`. All four keys have base values; every environment inherits them unless overridden.
- `devProps()` represents `application-dev.properties`. It overrides only `db.url` and `logging.level.root`. `server.port` and `app.name` are untouched — they keep their base values.
- `cloudProps()` represents `application-cloud.properties`. It overrides `db.url` and `server.port`. When both `dev` and `cloud` are active, `cloud` loads last and wins the `db.url` conflict because activation order is `dev,cloud` and `putAll` applies in iteration order.
- **"dev + cloud" scenario** shows the resolved `db.url` is the cloud PostgreSQL URL, not the H2 URL — because `cloud` loaded after `dev`. This is why order in `spring.profiles.active=dev,cloud` matters.
- `prodProps()` overrides all environment-sensitive keys, including resetting logging to `WARN`. When `prod` overlays `dev`, the debug logging set by `dev` is silenced — the last-loaded value always wins.
- In real Spring Boot, `resolve()` is what `ConfigFileApplicationListener` does internally, processing each profile source in activation order.

## 7. Gotchas & takeaways

> **Profile-specific files override base values, but only for keys they explicitly define.** A missing key in `application-prod.properties` does not reset the key to empty — it leaves the base value in place. This is often surprising: `logging.level.root=DEBUG` in `application.properties` persists in prod unless `application-prod.properties` explicitly sets `logging.level.root=WARN`.

> **In multi-document YAML, the `spring.config.activate.on-profile` key replaced `spring.profiles` in Spring Boot 2.4.** Using the old `spring.profiles: prod` syntax inside a `---` block still works in some versions but generates a deprecation warning. Always use the new form.

- Profile-specific files live in the same directories as `application.properties` — classpath root, `classpath:/config/`, or externally mounted `./config/`.
- Multiple profiles active simultaneously means multiple overlay files: `application-dev.properties` then `application-cloud.properties`, in activation order.
- When two profile files define the same key, the one belonging to the last-listed active profile wins.
- Sensitive production secrets should not be committed to `application-prod.properties`. Use environment variables or a secrets manager, and rely on profile files only for non-secret configuration.
- You can override profile-specific files with an external config directory — ideal for Kubernetes ConfigMap mounting.
