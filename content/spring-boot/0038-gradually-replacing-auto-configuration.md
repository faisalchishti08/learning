---
card: spring-boot
gi: 38
slug: gradually-replacing-auto-configuration
title: Gradually replacing auto-configuration
---

## 1. What it is

**Gradually replacing auto-configuration** is the practice of selectively overriding individual pieces of Spring Boot's default setup with your own beans, rather than disabling auto-configuration wholesale. Because most Spring Boot auto-configuration classes use `@ConditionalOnMissingBean`, you can replace any single auto-configured bean simply by providing your own `@Bean` of the same type — Spring Boot's auto-configuration backs off automatically.

```java
@Configuration
public class MyDataSourceConfig {
    @Bean                     // your bean wins; DataSourceAutoConfiguration backs off
    public DataSource dataSource() {
        return DataSourceBuilder.create()
            .url("jdbc:postgresql://prod-db:5432/mydb")
            .build();
    }
}
```

No `exclude` needed, no XML, no flags — just define the bean.

## 2. Why & when

Auto-configuration defaults are good starting points but rarely perfect for production. You might need:
- A custom `DataSource` with a specific JDBC URL or connection pool settings.
- A `Jackson ObjectMapper` configured with custom serializers.
- A `TaskExecutor` with tuned thread-pool sizes.

Disabling an entire auto-configuration class (`@EnableAutoConfiguration(exclude = ...)`) is heavy-handed — it removes all beans the class defines. The gradual replacement approach is surgical: you replace only what you need to change and keep everything else.

Use this pattern whenever the auto-configured default is almost right but needs one adjustment.

## 3. Core concept

The mechanism rests on `@ConditionalOnMissingBean`. This annotation on an auto-configuration `@Bean` method says: "only create this bean if no bean of this type already exists in the context." User `@Configuration` classes are processed **before** auto-configurations, so your bean is already in the context when the auto-configuration runs — the condition fails and the auto-configured version is skipped.

Steps Spring Boot takes:

1. Process all user `@Configuration` and `@ComponentScan` beans first.
2. Run auto-configuration classes (they have lower priority).
3. For each `@Bean` in an auto-configuration that is guarded by `@ConditionalOnMissingBean`, check if the context already has a bean of that type.
4. If yes → skip. Your bean is used.
5. If no → create the default bean.

The result: you get fine-grained control with minimal code.

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="User @Bean overrides auto-configured bean via @ConditionalOnMissingBean">
  <!-- Phase 1: user beans -->
  <rect x="20" y="20" width="260" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="150" y="44" fill="#6db33f" font-size="12" font-family="monospace" text-anchor="middle">Phase 1 — User Config</text>
  <rect x="36" y="54" width="228" height="42" rx="5" fill="#2d3748" stroke="#79c0ff" stroke-width="1"/>
  <text x="150" y="72" fill="#79c0ff" font-size="11" font-family="monospace" text-anchor="middle">@Bean DataSource myDS()</text>
  <text x="150" y="88" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">→ registered in context</text>

  <!-- Phase 2: auto-config -->
  <rect x="20" y="130" width="260" height="100" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="150" y="154" fill="#8b949e" font-size="12" font-family="monospace" text-anchor="middle">Phase 2 — AutoConfig</text>
  <rect x="36" y="164" width="228" height="52" rx="5" fill="#2d3748" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="150" y="183" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">@ConditionalOnMissingBean</text>
  <text x="150" y="199" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">DataSource → ❌ skip</text>
  <text x="150" y="213" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">(bean already exists)</text>

  <!-- Arrow between phases -->
  <line x1="150" y1="110" x2="150" y2="128" stroke="#6db33f" stroke-width="1.5" marker-end="url(#g1)"/>

  <!-- Context box -->
  <rect x="360" y="60" width="270" height="80" rx="8" fill="#16202e" stroke="#6db33f" stroke-width="2"/>
  <text x="495" y="84" fill="#6db33f" font-size="12" font-family="sans-serif" font-weight="bold" text-anchor="middle">Application Context</text>
  <text x="495" y="108" fill="#e6edf3" font-size="11" font-family="monospace" text-anchor="middle">dataSource → myDS (custom)</text>
  <text x="495" y="126" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">auto-config default never created</text>

  <!-- Arrow to context -->
  <line x1="282" y1="70" x2="358" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#g1)"/>

  <defs>
    <marker id="g1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

User bean is registered first; the auto-configured bean's `@ConditionalOnMissingBean` fails, so it never runs.

## 5. Runnable example

```java
// GradualReplaceDemo.java
// How to run: java GradualReplaceDemo.java  (JDK 17+)
// Simulates @ConditionalOnMissingBean: auto-configured beans
// back off when the user provides a bean of the same type.

import java.util.*;

public class GradualReplaceDemo {

    // ── Simulate bean registry ──────────────────────────────────────
    static Map<String, String> context = new LinkedHashMap<>();

    // ── Step 1: user config beans (processed FIRST) ─────────────────
    static void applyUserConfig() {
        System.out.println("=== Phase 1: User @Configuration ===");
        registerBean("dataSource", "CustomHikariDS(url=jdbc:postgresql://prod:5432/db)",
            "MyDataSourceConfig");
        // User did NOT define ObjectMapper → auto-config will supply the default
    }

    // ── Step 2: auto-config beans (processed AFTER user beans) ──────
    static void applyAutoConfig() {
        System.out.println("\n=== Phase 2: Auto-Configuration (@ConditionalOnMissingBean) ===");

        // DataSourceAutoConfiguration
        conditionalOnMissingBean("dataSource",
            "DefaultHikariDS(url=jdbc:h2:mem:test)",
            "DataSourceAutoConfiguration");

        // JacksonAutoConfiguration — not overridden by user
        conditionalOnMissingBean("objectMapper",
            "ObjectMapper(default settings)",
            "JacksonAutoConfiguration");
    }

    static void registerBean(String name, String value, String source) {
        context.put(name, value);
        System.out.println("  ✅ Registered '" + name + "' from " + source);
    }

    static void conditionalOnMissingBean(String name, String value, String source) {
        if (context.containsKey(name)) {
            System.out.println("  ❌ Skipped '" + name + "' from " + source
                + " — bean already in context");
        } else {
            registerBean(name, value, source);
        }
    }

    public static void main(String[] args) {
        applyUserConfig();
        applyAutoConfig();

        System.out.println("\n=== Final context ===");
        context.forEach((k, v) -> System.out.printf("  %-14s → %s%n", k, v));
    }
}
```

**How to run:** `java GradualReplaceDemo.java`

Expected output:
```
=== Phase 1: User @Configuration ===
  ✅ Registered 'dataSource' from MyDataSourceConfig

=== Phase 2: Auto-Configuration (@ConditionalOnMissingBean) ===
  ❌ Skipped 'dataSource' from DataSourceAutoConfiguration — bean already in context
  ✅ Registered 'objectMapper' from JacksonAutoConfiguration

=== Final context ===
  dataSource     → CustomHikariDS(url=jdbc:postgresql://prod:5432/db)
  objectMapper   → ObjectMapper(default settings)
```

## 6. Walkthrough

- `applyUserConfig()` registers the user-defined `dataSource` bean first, simulating the fact that Spring processes user `@Configuration` classes before auto-configurations.
- `conditionalOnMissingBean` checks if the name already exists in `context`. If it does, the auto-configured default is skipped — this is `@ConditionalOnMissingBean` in action.
- `DataSourceAutoConfiguration`'s default bean is skipped because `dataSource` already exists.
- `JacksonAutoConfiguration`'s `objectMapper` is applied because the user didn't define one — the default is used.
- The final context has a custom `dataSource` and a default `objectMapper`, illustrating gradual replacement: you only override what you need, the rest auto-configures normally.

## 7. Gotchas & takeaways

> `@ConditionalOnMissingBean` checks by **type** by default, not by name. If you define a class that **extends** the auto-configured type (e.g. `class MyDataSource extends HikariDataSource`), the condition sees a `DataSource` already in context and backs off — even if you wanted both. Use `@ConditionalOnMissingBean(name = "dataSource")` to check by name instead.

> Putting your replacement `@Bean` inside a `@SpringBootApplication` class works but is messy. Prefer a dedicated `@Configuration` class so the replacement intent is clear.

- The order guarantee (user config before auto-config) is structural in Spring Boot — do not use `@Order` or `@DependsOn` to enforce it.
- If the auto-configuration class has multiple `@Bean` methods, `@ConditionalOnMissingBean` on each is checked independently — you can replace some beans and keep others from the same auto-config.
- This is the recommended replacement pattern. Use `exclude` only when you want to remove the entire auto-configuration with all its beans.
- Use `spring.autoconfigure.report=true` (or `--debug`) to verify which beans backed off and why.
