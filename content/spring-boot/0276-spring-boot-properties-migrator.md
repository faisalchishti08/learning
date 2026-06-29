---
card: spring-boot
gi: 276
slug: spring-boot-properties-migrator
title: Spring Boot Properties Migrator
---

## 1. What it is

**Spring Boot Properties Migrator** is a dependency you add temporarily during a Spring Boot major-version upgrade. At startup it:

1. Scans your `application.properties` / `application.yml` (and all profiles) for property keys that were **renamed or removed** between Spring Boot versions.
2. Logs a precise warning for every stale key, telling you the old key, the new key (if one exists), and the Boot version that changed it.
3. Where possible, **renames the key in memory at runtime** so your application still works during the migration window — you don't have to fix everything before the app can start.

The library lives at `org.springframework.boot:spring-boot-properties-migrator`. It is never included by default; you pull it in deliberately and remove it once the migration is complete.

## 2. Why & when

Spring Boot regularly renames, consolidates, or drops configuration properties across major and minor releases (e.g. `spring.datasource.url` is stable, but `management.endpoints.web.*` and `server.servlet.*` have shifted significantly between 2.x and 3.x). Without the migrator:

- Stale keys are silently ignored — the application starts, but the old configuration has no effect.
- You discover the breakage in production when a timeout is wrong, a port is wrong, or a health endpoint is missing.

The migrator makes the invisible visible: every renamed key produces a `WARN`-level log line during startup that names the replacement. You work through them once, update the config, and remove the dependency before shipping.

**Add it when:** upgrading between Spring Boot major/minor versions (2.7 → 3.0, 3.0 → 3.1, etc.).
**Remove it before:** committing production-ready code — it is never appropriate in a deployed artifact.

## 3. Core concept

The migrator ships a machine-generated file, `spring-configuration-metadata.json` (or `additional-spring-configuration-metadata.json`), that lists every property that was renamed or removed together with the version it changed. At startup, `PropertiesStartupContextCustomizer` reads your environment and cross-references it against this metadata.

For each stale key it finds, the migrator:

- Emits a `WARN` log: `The property 'old.key' has been renamed to 'new.key'`.
- Injects a copy of the value under the new key so the rest of the application sees the correct key.

For removed keys with no replacement it logs: `The property 'old.key' is no longer supported`.

The in-memory rename means your application still boots correctly *during* migration, but the moment you remove the migrator dependency (which you must), the stale key is gone and only the correct key is read. That is the forcing function to actually update the config files.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Properties Migrator scans application.properties at startup, logs warnings, and injects renamed keys into the Spring Environment">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arrW" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>

  <!-- application.properties -->
  <rect x="10" y="85" width="155" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="87" y="109" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">application.properties</text>
  <text x="87" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">old.key=value  ← stale</text>

  <!-- Migrator -->
  <rect x="200" y="60" width="180" height="110" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="88" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Properties Migrator</text>
  <text x="290" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reads metadata.json</text>
  <text x="290" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">cross-references env</text>
  <text x="290" y="140" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">logs WARN per stale key</text>
  <text x="290" y="156" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">injects new key in memory</text>

  <!-- Spring Environment -->
  <rect x="420" y="75" width="155" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="497" y="100" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Spring Environment</text>
  <text x="497" y="119" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new.key=value  ← injected</text>
  <text x="497" y="137" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">app boots correctly</text>

  <!-- WARN log box -->
  <rect x="200" y="188" width="180" height="38" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1"/>
  <text x="290" y="205" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">WARN: 'old.key' renamed</text>
  <text x="290" y="219" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">to 'new.key' (Boot 3.0)</text>

  <line x1="165" y1="115" x2="198" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="380" y1="115" x2="418" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="290" y1="170" x2="290" y2="186" stroke="#f0883e" stroke-width="1.5" marker-end="url(#arrW)"/>

  <text x="350" y="232" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Remove migrator before production — in-memory rename is a crutch, not a fix</text>
</svg>

The migrator bridges old config to the new Spring Environment at startup; the WARN log is your fix list.

## 5. Runnable example

We'll simulate a Spring Boot upgrade scenario: an `application.properties` has a property that was renamed, and we'll trace what the migrator detects.

### Level 1 — Basic

The simplest use: add the migrator dependency, observe a stale `management.security.enabled` key (removed in Boot 2.x) being flagged at startup.

```java
// MigratorDemo.java — run with: java MigratorDemo.java
// Simulates what the migrator does: detect stale keys and suggest replacements.
// (In a real app you add the dependency; here we reproduce the core logic manually.)

import java.util.*;

public class MigratorDemo {

    // Simulated migration metadata (subset of what spring-boot-properties-migrator ships)
    record Migration(String oldKey, String newKey, String sinceVersion, String reason) {}

    static final List<Migration> METADATA = List.of(
        new Migration("management.security.enabled",       null,
            "2.0", "Security auto-configuration was overhauled in Boot 2.0"),
        new Migration("spring.datasource.initialize",      "spring.sql.init.mode",
            "2.5", "Renamed as part of the SQL initialisation redesign"),
        new Migration("server.context-path",               "server.servlet.context-path",
            "2.0", "Moved under server.servlet.* namespace")
    );

    public static void main(String[] args) {
        // Simulate what an application.properties might look like after a 1.x → 3.x upgrade
        Map<String, String> applicationProperties = new LinkedHashMap<>();
        applicationProperties.put("server.port",                    "8080");            // fine
        applicationProperties.put("server.context-path",            "/api");            // stale!
        applicationProperties.put("spring.datasource.initialize",   "always");          // stale!
        applicationProperties.put("management.security.enabled",    "false");           // stale + removed!
        applicationProperties.put("spring.application.name",        "my-service");      // fine

        System.out.println("=== Spring Boot Properties Migrator (simulated) ===\n");
        System.out.println("Scanning " + applicationProperties.size() + " properties...\n");

        for (var entry : applicationProperties.entrySet()) {
            METADATA.stream()
                .filter(m -> m.oldKey().equals(entry.getKey()))
                .findFirst()
                .ifPresentOrElse(
                    m -> {
                        if (m.newKey() != null) {
                            System.out.printf("[WARN]  '%s' renamed to '%s' (since Boot %s)%n",
                                m.oldKey(), m.newKey(), m.sinceVersion());
                            System.out.printf("        In-memory: injecting '%s=%s'%n%n",
                                m.newKey(), entry.getValue());
                        } else {
                            System.out.printf("[WARN]  '%s' no longer supported (Boot %s): %s%n%n",
                                m.oldKey(), m.sinceVersion(), m.reason());
                        }
                    },
                    () -> System.out.printf("[OK]    '%s=%s'%n", entry.getKey(), entry.getValue())
                );
        }
    }
}
```

How to run: `java MigratorDemo.java`

The scan finds three stale keys among five. The two with replacements get their values injected under the new key so the app boots; the removed one is flagged with no injection.

### Level 2 — Intermediate

Now we add profile awareness and track the effective configuration after migration — exactly what a real migrator produces.

```java
// MigratorDemoV2.java — run with: java MigratorDemoV2.java
// Adds: profile-specific properties, effective-config report after migration.

import java.util.*;

public class MigratorDemoV2 {

    record Migration(String oldKey, String newKey, String sinceVersion) {}

    static final List<Migration> METADATA = List.of(
        new Migration("server.context-path",          "server.servlet.context-path", "2.0"),
        new Migration("spring.datasource.initialize", "spring.sql.init.mode",        "2.5"),
        new Migration("management.security.enabled",  null,                          "2.0")
    );

    public static void main(String[] args) {
        // Simulate application.properties (base) + application-prod.properties (profile)
        Map<String, String> base = new LinkedHashMap<>(Map.of(
            "server.port",               "8080",
            "server.context-path",       "/api",       // stale
            "spring.application.name",   "my-service"
        ));
        Map<String, String> prod = new LinkedHashMap<>(Map.of(
            "spring.datasource.initialize", "always",  // stale
            "management.security.enabled",  "false",   // stale + removed
            "spring.datasource.url",        "jdbc:postgresql://db:5432/prod"
        ));

        System.out.println("=== Properties Migrator — Profile-aware scan ===\n");
        migrate("application.properties [default]", base);
        migrate("application-prod.properties [prod]", prod);

        // Merge: profile overrides base; apply migration in-memory
        Map<String, String> effective = new LinkedHashMap<>(base);
        effective.putAll(prod);
        applyMigrations(effective);

        System.out.println("\n--- Effective Environment after migration ---");
        effective.forEach((k, v) -> System.out.printf("  %-45s = %s%n", k, v));
        System.out.println("\nFix the properties above and remove the migrator dependency.");
    }

    static void migrate(String source, Map<String, String> props) {
        System.out.println("\n[" + source + "]");
        List<Map.Entry<String,String>> injections = new ArrayList<>();
        List<String> toRemove = new ArrayList<>();
        for (var e : props.entrySet()) {
            METADATA.stream().filter(m -> m.oldKey().equals(e.getKey())).findFirst().ifPresent(m -> {
                if (m.newKey() != null) {
                    System.out.printf("  WARN  %-42s → %s%n", m.oldKey(), m.newKey());
                    injections.add(Map.entry(m.newKey(), e.getValue()));
                } else {
                    System.out.printf("  WARN  %-42s ← REMOVED in Boot %s (no replacement)%n",
                        m.oldKey(), m.sinceVersion());
                }
                toRemove.add(e.getKey());
            });
        }
        toRemove.forEach(props::remove);
        injections.forEach(e -> props.put(e.getKey(), e.getValue()));
    }

    static void applyMigrations(Map<String, String> env) {
        // Already done per-map in migrate(); this merges the result
    }
}
```

How to run: `java MigratorDemoV2.java`

Profile-specific files are scanned separately so the log makes clear *which file* owns each stale key. The effective environment at the end shows only the post-migration keys — this is the state the real Spring Environment holds during the migration window.

### Level 3 — Advanced

Full simulation: WARN log matches Boot's real format, tracks fix status, generates the `application.properties` diff you need to apply, and counts issues by severity.

```java
// MigratorDemoV3.java — run with: java MigratorDemoV3.java
// Adds: Boot-format WARN log, severity levels, generated diff, fix checklist.

import java.util.*;
import java.util.stream.*;

public class MigratorDemoV3 {

    enum Severity { RENAMED, REMOVED }

    record Migration(String oldKey, String newKey, String sinceVersion, Severity severity) {
        static Migration renamed(String old, String n, String v) {
            return new Migration(old, n, v, Severity.RENAMED);
        }
        static Migration removed(String old, String v) {
            return new Migration(old, null, v, Severity.REMOVED);
        }
    }

    record Finding(String source, String oldKey, String newKey,
                   String oldValue, Severity severity, String since) {}

    static final List<Migration> METADATA = List.of(
        Migration.renamed("server.context-path",          "server.servlet.context-path", "2.0"),
        Migration.renamed("spring.datasource.initialize", "spring.sql.init.mode",        "2.5"),
        Migration.removed("management.security.enabled",                                 "2.0"),
        Migration.renamed("endpoints.health.sensitive",   null,                          "2.0"),
        Migration.renamed("spring.http.encoding.charset", "server.servlet.encoding.charset", "2.3")
    );

    public static void main(String[] args) {
        Map<String,Map<String,String>> files = new LinkedHashMap<>();
        files.put("application.properties", new LinkedHashMap<>(Map.of(
            "server.port",               "8080",
            "server.context-path",       "/api",
            "spring.http.encoding.charset", "UTF-8",
            "spring.application.name",   "order-service"
        )));
        files.put("application-prod.properties", new LinkedHashMap<>(Map.of(
            "spring.datasource.initialize", "always",
            "management.security.enabled",  "false",
            "spring.datasource.url",        "jdbc:postgresql://db:5432/orders"
        )));

        System.out.println("""
            =========================================================
            spring-boot-properties-migrator — startup report
            =========================================================
            """);

        List<Finding> findings = new ArrayList<>();

        for (var file : files.entrySet()) {
            for (var prop : new ArrayList<>(file.getValue().entrySet())) {
                METADATA.stream()
                    .filter(m -> m.oldKey().equals(prop.getKey()))
                    .findFirst()
                    .ifPresent(m -> {
                        findings.add(new Finding(file.getKey(),
                            m.oldKey(), m.newKey(), prop.getValue(), m.severity(), m.sinceVersion()));
                        if (m.severity() == Severity.RENAMED && m.newKey() != null) {
                            // in-memory rename
                            file.getValue().remove(m.oldKey());
                            file.getValue().put(m.newKey(), prop.getValue());
                        }
                    });
            }
        }

        // Print Boot-style WARN log
        for (Finding f : findings) {
            if (f.severity() == Severity.RENAMED) {
                System.out.printf(
                    "WARN  PropertiesMigrationListener - Property source '%s':%n" +
                    "      'o.s.boot.context.properties.migrator' key '%s'%n" +
                    "      Replacement: '%s' (since %s)%n%n",
                    f.source(), f.oldKey(), f.newKey(), f.since());
            } else {
                System.out.printf(
                    "WARN  PropertiesMigrationListener - Property source '%s':%n" +
                    "      'o.s.boot.context.properties.migrator' key '%s'%n" +
                    "      Not supported (since %s) — remove it.%n%n",
                    f.source(), f.oldKey(), f.since());
            }
        }

        // Summary
        long renames  = findings.stream().filter(f -> f.severity() == Severity.RENAMED).count();
        long removals = findings.stream().filter(f -> f.severity() == Severity.REMOVED).count();
        System.out.printf("--- Summary: %d renamed, %d removed ---%n%n", renames, removals);

        // Generated diff
        System.out.println("=== Suggested diff for your config files ===");
        for (Finding f : findings) {
            System.out.printf("  [%s]%n", f.source());
            System.out.printf("  -  %s=%s%n", f.oldKey(), f.oldValue());
            if (f.newKey() != null)
                System.out.printf("  +  %s=%s%n%n", f.newKey(), f.oldValue());
            else
                System.out.printf("  (remove entirely — no replacement)%n%n");
        }

        System.out.println("=== Next steps ===");
        System.out.println("  1. Apply the diff above to each properties file.");
        System.out.println("  2. Re-run the app — no WARN lines should remain.");
        System.out.println("  3. Remove spring-boot-properties-migrator from pom.xml / build.gradle.");
        System.out.println("  4. Run full test suite.");
    }
}
```

How to run: `java MigratorDemoV3.java`

The output mirrors the real Boot startup log format, then produces a ready-to-apply diff and a four-step checklist. In a real project you'd apply the diff to the actual `.properties` files, rerun the app to confirm zero WARN lines, and delete the migrator dependency before merging.

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Properties migrator workflow: add dependency, fix stale keys from WARN log, re-run, remove dependency">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="10"  y="65" width="140" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80"  y="86" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">1. Add migrator</text>
  <text x="80"  y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">pom.xml / build.gradle</text>

  <rect x="185" y="65" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="255" y="86" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">2. Start app</text>
  <text x="255" y="104" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">read WARN lines</text>

  <rect x="360" y="65" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="430" y="86" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">3. Fix properties</text>
  <text x="430" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">apply suggested diff</text>

  <rect x="535" y="65" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="610" y="86" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">4. Remove migrator</text>
  <text x="610" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">before shipping</text>

  <line x1="150" y1="90" x2="183" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="325" y1="90" x2="358" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="500" y1="90" x2="533" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Repeat step 2–3 until startup shows zero WARN lines from PropertiesMigrationListener</text>
</svg>

## 6. Walkthrough

**What happens at application startup when the migrator is present:**

1. **Spring Environment is built.** Before any beans are created, Spring loads `application.properties`, `application-{profile}.properties`, environment variables, and system properties into a `ConfigurableEnvironment`.

2. **`PropertiesStartupContextCustomizer` runs.** This is the migrator's entry point — it implements `SpringApplicationRunListener` and fires early in the startup lifecycle, before `ApplicationContext` is refreshed.

3. **Metadata is read.** The migrator loads its bundled `additional-spring-configuration-metadata.json`. This JSON file (committed to the JAR at build time by the Spring team) maps every deprecated/renamed property key to its replacement and the Boot version that changed it.

4. **Cross-reference against the current Environment.** The customizer iterates every property source in the environment. For each source it finds matching stale keys.

5. **For each `RENAMED` key:** emits a `WARN` log via `PropertiesMigrationListener` (the logger name you'll see in the output), then injects the value under the new key by wrapping the property source in a `DeprecatedPropertiesPropertySource`. The old key is left in place but effectively shadowed.

6. **For each `REMOVED` key (no replacement):** logs `WARN` only. No injection — the property is noted as unsupported and the application proceeds without it. If your feature depended on it, it won't work.

7. **Application context is refreshed normally.** Beans pick up the environment as usual. Because the migrator injected new keys, they bind to the correct `@ConfigurationProperties` or `@Value` fields even though `application.properties` still has old keys.

8. **Your task:** read every WARN from `PropertiesMigrationListener`. For renames: update the config file. For removals: remove the key (and find the Boot 3.x way to achieve the same goal via code). Repeat until startup is clean.

9. **Remove the dependency.** Now the in-memory injection is gone. If you missed a key, the app either fails to start (if it was required) or behaves differently (if it was optional). Your test suite catches this.

**Concrete request/response analogy:**

| Stage | Real migrator | Level-3 simulation |
|---|---|---|
| Input | `application.properties` loaded into `Environment` | `files` map populated |
| Detection | `PropertiesStartupContextCustomizer` cross-refs metadata | `METADATA` stream filter |
| WARN log | `PropertiesMigrationListener` logs at startup | `printf` matching Boot format |
| Injection | `DeprecatedPropertiesPropertySource` wraps source | `file.getValue().put(newKey, value)` |
| Output | App boots; stale keys corrected in memory | Effective map + diff printed |

## 7. Gotchas & takeaways

> **Never leave the migrator in a production artifact.** The in-memory rename is a crutch to keep the app running during migration. It is not a permanent solution. Shipping the migrator means your real config is wrong, your startup is slower, and every deployment logs scary WARN lines that operators learn to ignore — until they miss a real warning.

> **Silently ignored properties are the danger the migrator prevents.** Without it, `server.context-path=/api` in a Boot 3.x app is simply ignored (the key doesn't exist in Boot 3.x's metadata), so your context path becomes `/`. The app starts fine; nothing in the startup log tells you the setting is gone.

- Add to Maven: `<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-properties-migrator</artifactId><scope>runtime</scope></dependency>`; Gradle: `runtimeOnly 'org.springframework.boot:spring-boot-properties-migrator'`.
- Only rename-equivalent keys are injected; `REMOVED` keys produce WARNs with no injection. Check each one manually — the behavior they controlled was redesigned, not just renamed.
- Run with all active profiles (`--spring.profiles.active=prod,staging`) to surface profile-specific stale keys — the migrator only sees properties active at runtime.
- `endpoints.*` (Spring Boot 1.x Actuator) was entirely restructured in 2.x; the migrator covers most renames but Actuator customizations often need hand-migration.
- After fixing, search for the migrator JAR in your build output (`find . -name "spring-boot-properties-migrator-*.jar"`) as a final sanity check before tagging a release.
