---
card: spring-boot
gi: 39
slug: disabling-specific-auto-configuration-classes-exclude
title: Disabling specific auto-configuration classes (exclude)
---

## 1. What it is

**Disabling specific auto-configuration** is the mechanism for telling Spring Boot to completely ignore a particular auto-configuration class — preventing it from applying any of its beans, regardless of classpath conditions.

There are three ways to do this:

**1. Annotation `exclude` attribute:**
```java
@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)
public class MyApp { ... }
```

**2. `spring.autoconfigure.exclude` property** (useful when you can't access the class at compile time):
```properties
spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration
```

**3. `excludeName` attribute** (uses string class name — avoids a compile-time dependency):
```java
@SpringBootApplication(excludeName =
    "org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration")
public class MyApp { ... }
```

## 2. Why & when

Excluding is stronger than the gradual replacement approach (tutorial 38). Use it when:

- An auto-configuration class causes **startup failures** (e.g. `DataSourceAutoConfiguration` requires a DB URL, but your service has no database).
- A third-party starter auto-configures something that conflicts with your setup and `@ConditionalOnMissingBean` alone isn't enough to suppress it.
- You want to guarantee a bean is **never** created by auto-configuration, not just backed off.
- Testing: exclude heavyweight configurations in unit tests for faster startup.

**Do not use `exclude` as a first resort.** If providing your own `@Bean` is enough (tutorial 38), prefer that — it is less fragile if the auto-configuration class name changes between Spring Boot versions.

## 3. Core concept

Think of auto-configuration like a default menu at a restaurant. Gradual replacement (tutorial 38) is ordering a custom dish instead of the default — you still eat here. Exclusion is saying "remove that dish from the menu entirely" — nobody at your table can order it, even by accident.

The `exclude` attribute is processed by `AutoConfigurationImportSelector` very early in the startup, **before** any auto-configuration class is loaded:

1. The selector builds the full candidate list from `AutoConfiguration.imports`.
2. It reads `exclude` / `excludeName` / `spring.autoconfigure.exclude`.
3. Excluded class names are removed from the candidate list.
4. Remaining candidates go through `@Conditional` evaluation and are applied.

Because exclusion happens before class loading, the excluded auto-configuration's `@Bean` methods never run — even if their `@Conditional` conditions would have passed.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Excluded auto-configuration removed from candidate list before conditions are evaluated">
  <!-- Candidate list -->
  <rect x="20" y="30" width="220" height="170" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="54" fill="#8b949e" font-size="12" font-family="monospace" text-anchor="middle">Full candidate list</text>

  <rect x="36" y="64" width="188" height="30" rx="5" fill="#3d2020" stroke="#f85149" stroke-width="1"/>
  <text x="130" y="84" fill="#f85149" font-size="10" font-family="monospace" text-anchor="middle">DataSourceAutoConfig ⛔ excluded</text>

  <rect x="36" y="102" width="188" height="30" rx="5" fill="#2d3748" stroke="#6db33f" stroke-width="1"/>
  <text x="130" y="122" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">DispatcherServletAutoConfig</text>

  <rect x="36" y="140" width="188" height="30" rx="5" fill="#2d3748" stroke="#6db33f" stroke-width="1"/>
  <text x="130" y="160" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">JacksonAutoConfig</text>

  <!-- Exclude source -->
  <rect x="20" y="210" width="220" height="22" rx="5" fill="#2d3748" stroke="#f85149" stroke-width="1"/>
  <text x="130" y="225" fill="#f85149" font-size="10" font-family="monospace" text-anchor="middle">@SpringBootApp(exclude=DataSource…)</text>

  <!-- After exclusion list -->
  <rect x="290" y="30" width="220" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="400" y="54" fill="#6db33f" font-size="12" font-family="monospace" text-anchor="middle">After exclusion</text>

  <rect x="306" y="64" width="188" height="30" rx="5" fill="#2d3748" stroke="#6db33f" stroke-width="1"/>
  <text x="400" y="84" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">DispatcherServletAutoConfig</text>

  <rect x="306" y="102" width="188" height="30" rx="5" fill="#2d3748" stroke="#6db33f" stroke-width="1"/>
  <text x="400" y="122" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">JacksonAutoConfig</text>

  <!-- Context -->
  <rect x="560" y="60" width="80" height="100" rx="6" fill="#16202e" stroke="#6db33f" stroke-width="1.5"/>
  <text x="600" y="84" fill="#6db33f" font-size="10" font-family="sans-serif" text-anchor="middle">Context</text>
  <text x="600" y="104" fill="#e6edf3" font-size="9" font-family="monospace" text-anchor="middle">dispatcher</text>
  <text x="600" y="120" fill="#e6edf3" font-size="9" font-family="monospace" text-anchor="middle">Servlet</text>
  <text x="600" y="140" fill="#e6edf3" font-size="9" font-family="monospace" text-anchor="middle">objectMapper</text>

  <!-- Arrows -->
  <line x1="242" y1="120" x2="288" y2="120" stroke="#6db33f" stroke-width="2" marker-end="url(#d1)"/>
  <line x1="510" y1="100" x2="558" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#d1)"/>

  <defs>
    <marker id="d1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

`DataSourceAutoConfiguration` is removed from the candidate list before condition evaluation; only the remaining two proceed to the context.

## 5. Runnable example

```java
// ExcludeAutoConfigDemo.java
// How to run: java ExcludeAutoConfigDemo.java  (JDK 17+)
// Simulates how Spring Boot removes excluded auto-configurations
// from the candidate list before @Conditional evaluation.

import java.util.*;

public class ExcludeAutoConfigDemo {

    record AutoConfig(String name, boolean conditionPasses) {}

    public static void main(String[] args) {
        // Full candidate list (from AutoConfiguration.imports)
        List<AutoConfig> candidates = new ArrayList<>(List.of(
            new AutoConfig("DataSourceAutoConfiguration",          true),
            new AutoConfig("DispatcherServletAutoConfiguration",   true),
            new AutoConfig("JacksonAutoConfiguration",             true),
            new AutoConfig("MongoAutoConfiguration",               false)
        ));

        // Exclusions declared via @SpringBootApplication(exclude=...)
        // or spring.autoconfigure.exclude
        Set<String> excluded = Set.of("DataSourceAutoConfiguration");

        System.out.println("=== Exclusion phase (before @Conditional evaluation) ===");
        candidates.removeIf(cfg -> {
            if (excluded.contains(cfg.name())) {
                System.out.println("  ⛔ Removed from candidates: " + cfg.name());
                return true;
            }
            return false;
        });

        System.out.println("\n=== @Conditional evaluation (remaining candidates) ===");
        List<String> applied = new ArrayList<>();
        for (AutoConfig cfg : candidates) {
            if (cfg.conditionPasses()) {
                applied.add(cfg.name());
                System.out.println("  ✅ Applied: " + cfg.name());
            } else {
                System.out.println("  ❌ Skipped (condition false): " + cfg.name());
            }
        }

        System.out.println("\n=== Applied auto-configurations ===");
        applied.forEach(c -> System.out.println("  " + c));
        System.out.println("\nNote: DataSourceAutoConfiguration never ran — no DB beans in context.");
    }
}
```

**How to run:** `java ExcludeAutoConfigDemo.java`

Expected output:
```
=== Exclusion phase (before @Conditional evaluation) ===
  ⛔ Removed from candidates: DataSourceAutoConfiguration

=== @Conditional evaluation (remaining candidates) ===
  ✅ Applied: DispatcherServletAutoConfiguration
  ✅ Applied: JacksonAutoConfiguration
  ❌ Skipped (condition false): MongoAutoConfiguration

=== Applied auto-configurations ===
  DispatcherServletAutoConfiguration
  JacksonAutoConfiguration

Note: DataSourceAutoConfiguration never ran — no DB beans in context.
```

## 6. Walkthrough

- `candidates` is built from `AutoConfiguration.imports` — all potential auto-configurations.
- `excluded` simulates the `exclude` attribute on `@SpringBootApplication` or the `spring.autoconfigure.exclude` property. Both sources are merged in real Spring Boot.
- `candidates.removeIf(...)` is the exclusion phase: excluded classes are removed from the list entirely, before any `@Conditional` check.
- The remaining candidates are evaluated: `MongoAutoConfiguration` fails its condition (Mongo JAR not present) and is also skipped — but for a different reason than exclusion.
- `DataSourceAutoConfiguration` never appears in the applied list and never creates `dataSource`, `entityManagerFactory`, or any of its derived beans.

## 7. Gotchas & takeaways

> Excluding a class that is **not** on the candidate list (not in any `AutoConfiguration.imports`) causes `IllegalStateException: The following classes could not be excluded because they are not auto-configuration classes` in Spring Boot 2.x. In Spring Boot 3.x the error message improved. Always verify the class name before excluding.

> If you exclude an auto-configuration that other auto-configurations depend on (via `@AutoConfigureAfter`), those dependent configs may fail or silently skip — the ordering chain breaks. Check the condition evaluation report with `--debug` after excluding anything.

- Three ways to exclude: annotation `exclude` (compile-time, safest), `excludeName` (string, no compile dependency), `spring.autoconfigure.exclude` property (runtime, great for environment-specific disabling).
- Exclusion is not the same as `@ConditionalOnMissingBean` back-off — excluded classes never run at all.
- Prefer gradual replacement (own `@Bean`) over exclusion when possible; exclusion is all-or-nothing for a config class.
- In test slices (`@WebMvcTest`, `@DataJpaTest`) many auto-configurations are already excluded to speed up tests — check the slice's documentation before adding your own exclusions.
