---
card: spring-boot
gi: 37
slug: how-auto-configuration-works-autoconfiguration-imports
title: How auto-configuration works (AutoConfiguration.imports)
---

## 1. What it is

Spring Boot auto-configuration works through a **well-defined discovery file** named `AutoConfiguration.imports` located at `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` inside each JAR. This plain text file lists one auto-configuration class name per line. When Spring Boot starts, it reads every such file from every JAR on the classpath and processes the listed classes as potential configuration.

Before Spring Boot 2.7, the file was `META-INF/spring.factories` under the key `org.springframework.boot.autoconfigure.EnableAutoConfiguration`. The `AutoConfiguration.imports` file is the modern (2.7+) replacement for that section of `spring.factories`.

```
# META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration
org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration
org.springframework.boot.autoconfigure.web.servlet.DispatcherServletAutoConfiguration
```

## 2. Why & when

The file solves the **"how does Spring Boot know what to auto-configure?"** question. Without it, Spring Boot would have to scan every class on the classpath looking for auto-configuration classes — prohibitively slow. The file acts as an explicit index: processing is O(lines in file) instead of O(classes on classpath).

Know this file when:
- Writing your own Spring Boot starter (you must create this file).
- Debugging "why is X auto-configured even though I didn't ask for it?"
- Understanding why removing a starter JAR removes auto-configuration.
- Migrating from Spring Boot < 2.7 where `spring.factories` was used instead.

## 3. Core concept

Think of `AutoConfiguration.imports` as the **table of contents** in a technical manual. The manual (Spring Boot's autoconfigure JAR) has hundreds of chapters (auto-configuration classes). Rather than reading every page to find chapter headings, the reader opens the table of contents (the imports file) and jumps directly to relevant chapters.

The full processing pipeline:

1. `@EnableAutoConfiguration` activates `AutoConfigurationImportSelector`.
2. The selector calls `SpringFactoriesLoader.loadFactoryNames()` (for `spring.factories`) or reads all `AutoConfiguration.imports` files from the classpath.
3. The resulting list of class names is **de-duplicated and filtered** by any `exclude` attributes.
4. Each remaining class is loaded; Spring evaluates its `@Conditional` annotations.
5. Only classes whose conditions pass are imported into the application context.
6. Auto-configuration classes are sorted by `@AutoConfigureBefore` / `@AutoConfigureAfter` / `@AutoConfigureOrder` before being applied.

## 4. Diagram

<svg viewBox="0 0 660 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AutoConfiguration.imports discovery pipeline from JAR files to application context">
  <!-- JAR files -->
  <rect x="20" y="20" width="160" height="50" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="42" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">spring-boot-</text>
  <text x="100" y="60" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">autoconfigure.jar</text>

  <rect x="20" y="84" width="160" height="50" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="106" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">my-starter.jar</text>
  <text x="100" y="122" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">(custom)</text>

  <!-- File label -->
  <rect x="20" y="148" width="160" height="40" rx="6" fill="#1a2332" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="165" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">META-INF/spring/</text>
  <text x="100" y="181" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">AutoConfig.imports</text>

  <!-- Selector -->
  <rect x="220" y="90" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="310" y="115" fill="#6db33f" font-size="12" font-family="monospace" text-anchor="middle">AutoConfiguration</text>
  <text x="310" y="133" fill="#6db33f" font-size="12" font-family="monospace" text-anchor="middle">ImportSelector</text>

  <!-- Condition eval -->
  <rect x="440" y="60" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="540" y="85" fill="#6db33f" font-size="11" font-family="sans-serif" text-anchor="middle">@Conditional evaluation</text>

  <!-- Applied configs -->
  <rect x="440" y="118" width="200" height="40" rx="6" fill="#16202e" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="143" fill="#e6edf3" font-size="11" font-family="monospace" text-anchor="middle">passing configs → context</text>

  <!-- Skipped configs -->
  <rect x="440" y="170" width="200" height="40" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="540" y="195" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">failing configs → skip</text>

  <!-- Arrows -->
  <line x1="180" y1="45" x2="218" y2="110" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#h1)"/>
  <line x1="180" y1="109" x2="218" y2="120" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#h1)"/>
  <line x1="180" y1="165" x2="218" y2="130" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#h1)"/>
  <line x1="400" y1="120" x2="438" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#h1)"/>
  <line x1="540" y1="100" x2="540" y2="116" stroke="#6db33f" stroke-width="2" marker-end="url(#h1)"/>
  <line x1="540" y1="158" x2="540" y2="168" stroke="#8b949e" stroke-width="1.5" marker-end="url(#h1)"/>

  <defs>
    <marker id="h1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

Each JAR contributes its `AutoConfiguration.imports` file; the selector merges all lists, evaluates conditions, and applies only passing configurations.

## 5. Runnable example

```java
// AutoConfigImportsDemo.java
// How to run: java AutoConfigImportsDemo.java  (JDK 17+)
// Simulates reading AutoConfiguration.imports files from multiple "JARs"
// and processing the merged candidate list.

import java.util.*;

public class AutoConfigImportsDemo {

    record AutoConfigEntry(String className, String jar, boolean conditionPasses) {}

    public static void main(String[] args) {
        // Simulated contents of AutoConfiguration.imports from two JARs
        List<AutoConfigEntry> springBootEntries = List.of(
            new AutoConfigEntry(
                "org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration",
                "spring-boot-autoconfigure.jar", true),
            new AutoConfigEntry(
                "org.springframework.boot.autoconfigure.mongo.MongoAutoConfiguration",
                "spring-boot-autoconfigure.jar", false),  // Mongo not on classpath
            new AutoConfigEntry(
                "org.springframework.boot.autoconfigure.web.servlet.DispatcherServletAutoConfiguration",
                "spring-boot-autoconfigure.jar", true)
        );

        List<AutoConfigEntry> customStarterEntries = List.of(
            new AutoConfigEntry(
                "com.example.starter.MyServiceAutoConfiguration",
                "my-starter.jar", true)
        );

        // Merge all imports files (as ImportSelector does)
        List<AutoConfigEntry> allCandidates = new ArrayList<>();
        allCandidates.addAll(springBootEntries);
        allCandidates.addAll(customStarterEntries);

        System.out.println("=== AutoConfiguration.imports — merged candidate list ===");
        System.out.printf("%-70s %-30s %s%n", "Class", "JAR", "Condition");
        System.out.println("-".repeat(115));

        List<String> applied = new ArrayList<>();

        for (AutoConfigEntry entry : allCandidates) {
            String status = entry.conditionPasses() ? "✅ PASS" : "❌ SKIP";
            System.out.printf("%-70s %-30s %s%n",
                entry.className(), entry.jar(), status);
            if (entry.conditionPasses()) applied.add(entry.className());
        }

        System.out.println("\n=== Applied auto-configurations ===");
        applied.forEach(c -> System.out.println("  " + c));
    }
}
```

**How to run:** `java AutoConfigImportsDemo.java`

Expected output:
```
=== AutoConfiguration.imports — merged candidate list ===
Class                                                                  JAR                            Condition
-------------------------------------------------------------------------------------------------------------------
org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration spring-boot-autoconfigure.jar ✅ PASS
org.springframework.boot.autoconfigure.mongo.MongoAutoConfiguration    spring-boot-autoconfigure.jar ❌ SKIP
org.springframework.boot.autoconfigure.web.servlet.DispatcherServletAu spring-boot-autoconfigure.jar ✅ PASS
com.example.starter.MyServiceAutoConfiguration                         my-starter.jar                ✅ PASS

=== Applied auto-configurations ===
  org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration
  org.springframework.boot.autoconfigure.web.servlet.DispatcherServletAutoConfiguration
  com.example.starter.MyServiceAutoConfiguration
```

## 6. Walkthrough

- `springBootEntries` and `customStarterEntries` represent the contents of two separate `AutoConfiguration.imports` files, one from `spring-boot-autoconfigure.jar` and one from a custom starter.
- `allCandidates` is the merged list — exactly what `AutoConfigurationImportSelector.getCandidateConfigurations()` returns before filtering.
- `entry.conditionPasses()` simulates `@Conditional` annotation evaluation. In real Spring this is handled by `ConditionEvaluator`, which checks `@ConditionalOnClass`, `@ConditionalOnMissingBean`, `@ConditionalOnProperty`, etc.
- `MongoAutoConfiguration` passes the condition check as `false` because `spring-data-mongodb` is not on the simulated classpath — it is silently skipped.
- `MyServiceAutoConfiguration` from the custom starter is merged and processed exactly like Spring Boot's built-in ones — the mechanism is the same.

## 7. Gotchas & takeaways

> If you write a custom starter and forget to create `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`, your auto-configuration class will never be discovered — it won't cause an error, it just silently won't run. Always verify by running with `--debug`.

> The old `spring.factories` file (key `org.springframework.boot.autoconfigure.EnableAutoConfiguration`) still works in Spring Boot 2.7 and 3.x for backwards compatibility, but Spring Boot 3.x logs a deprecation warning. Migrate to `AutoConfiguration.imports` for new starters.

- `AutoConfiguration.imports` is a plain text file — one fully-qualified class name per line, `#` for comments.
- The file must live at `META-INF/spring/` (not `META-INF/` directly) for Spring Boot 2.7+.
- Spring Boot reads **every** `AutoConfiguration.imports` on the classpath and merges them — multiple starters coexist without conflict.
- Duplicates are de-duplicated before condition evaluation — listing the same class twice is harmless.
- Use `spring-boot-autoconfigure-processor` annotation processor when writing auto-configuration to validate the file at build time.
