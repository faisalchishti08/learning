---
card: spring-boot
gi: 33
slug: configuration-classes-import
title: Configuration classes & @Import
---

## 1. What it is

A **configuration class** in Spring is a plain Java class annotated with `@Configuration`. It is the Java-based replacement for XML bean definitions — you write `@Bean` methods inside it and Spring calls those methods to create and register objects (beans) in the application context.

`@Import` is a companion annotation that lets one configuration class **pull in** another configuration class (or any component) without relying on component scanning. It is Spring's way of composing modular configurations explicitly.

```java
@Configuration
@Import({SecurityConfig.class, DataSourceConfig.class})
public class AppConfig {
    @Bean
    public SomeService someService() {
        return new SomeService();
    }
}
```

## 2. Why & when

Before Java-based configuration (Spring 3.0+), all bean wiring was done in XML files. `@Configuration` makes the same wiring **type-safe**, **IDE-navigable**, and **refactor-friendly**.

Use `@Configuration` when:
- You want to define beans in Java rather than XML.
- You need conditional bean creation (pair with `@Conditional`).
- You are writing a library or auto-configuration that others import.

Use `@Import` when:
- You want to split configuration into focused classes (security, persistence, web) and assemble them explicitly.
- You want a parent config to pull in child configs without enabling component scanning.
- You write `@EnableXxx` annotations (e.g. `@EnableScheduling`) — those annotations use `@Import` internally to bring in the scheduling infrastructure.

## 3. Core concept

Think of `@Configuration` classes like **recipe books** and `@Import` like **a bookshelf index**. Each recipe book (`@Configuration` class) describes how to make a set of dishes (beans). The shelf index (`@Import`) tells the chef exactly which books to open without having to search the whole kitchen.

Key rules:
1. A `@Configuration` class is itself a Spring bean — it is instantiated by Spring and its `@Bean` methods are intercepted (proxied) so that calling one `@Bean` method from another within the same config returns the **same** singleton, not a new instance.
2. `@Import` takes one or more classes. Those classes can be: another `@Configuration`, a plain `@Component`, or an `ImportSelector` / `ImportBeanDefinitionRegistrar` for programmatic imports.
3. Classes brought in via `@Import` are fully registered — their own `@Bean` methods and `@Import` declarations are honoured.

## 4. Diagram

<svg viewBox="0 0 660 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@Import pulling SecurityConfig and DataSourceConfig into AppConfig">
  <!-- AppConfig box -->
  <rect x="220" y="20" width="220" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="48" fill="#6db33f" font-size="13" font-family="monospace" font-weight="bold" text-anchor="middle">AppConfig</text>
  <text x="330" y="68" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">@Configuration</text>
  <text x="330" y="86" fill="#79c0ff" font-size="11" font-family="monospace" text-anchor="middle">@Import({Security, DS})</text>

  <!-- SecurityConfig -->
  <rect x="40" y="170" width="200" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="198" fill="#79c0ff" font-size="12" font-family="monospace" text-anchor="middle">SecurityConfig</text>
  <text x="140" y="216" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">@Configuration</text>
  <text x="140" y="232" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">@Bean PasswordEncoder…</text>

  <!-- DataSourceConfig -->
  <rect x="420" y="170" width="200" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="520" y="198" fill="#79c0ff" font-size="12" font-family="monospace" text-anchor="middle">DataSourceConfig</text>
  <text x="520" y="216" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">@Configuration</text>
  <text x="520" y="232" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">@Bean DataSource…</text>

  <!-- Arrows -->
  <line x1="280" y1="100" x2="160" y2="170" stroke="#6db33f" stroke-width="1.8" stroke-dasharray="6,3" marker-end="url(#imp)"/>
  <line x1="380" y1="100" x2="500" y2="170" stroke="#6db33f" stroke-width="1.8" stroke-dasharray="6,3" marker-end="url(#imp)"/>

  <text x="190" y="142" fill="#6db33f" font-size="11" font-family="sans-serif">@Import</text>
  <text x="430" y="142" fill="#6db33f" font-size="11" font-family="sans-serif">@Import</text>

  <defs>
    <marker id="imp" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

`AppConfig` pulls in `SecurityConfig` and `DataSourceConfig` via `@Import`; Spring processes all three as if they were found by scanning.

## 5. Runnable example

```java
// ConfigurationImportDemo.java
// How to run: java ConfigurationImportDemo.java  (JDK 17+)
// Simulates @Configuration + @Import composition without a real Spring context.

import java.lang.annotation.*;
import java.util.*;

@Retention(RetentionPolicy.RUNTIME) @interface Configuration {}
@Retention(RetentionPolicy.RUNTIME) @interface Bean {}
@Retention(RetentionPolicy.RUNTIME) @interface Import {
    Class<?>[] value();
}

// ── child configs ───────────────────────────────────────────────────
@Configuration
class SecurityConfig {
    @Bean public String passwordEncoder() { return "BCryptPasswordEncoder"; }
}

@Configuration
class DataSourceConfig {
    @Bean public String dataSource() { return "HikariDataSource(url=jdbc:h2:mem:demo)"; }
}

// ── root config imports both ────────────────────────────────────────
@Configuration
@Import({SecurityConfig.class, DataSourceConfig.class})
class AppConfig {
    @Bean public String appService() { return "AppService"; }
}

// ── minimal "context" that honours @Import ──────────────────────────
public class ConfigurationImportDemo {

    static Map<String, String> context = new LinkedHashMap<>();

    public static void main(String[] args) throws Exception {
        register(AppConfig.class);

        System.out.println("=== Beans registered in context ===");
        context.forEach((k, v) -> System.out.println("  " + k + " → " + v));
    }

    static void register(Class<?> cfg) throws Exception {
        if (context.containsKey(cfg.getSimpleName())) return; // avoid cycles

        // honour @Import first (depth-first, like Spring)
        if (cfg.isAnnotationPresent(Import.class)) {
            for (Class<?> imported : cfg.getAnnotation(Import.class).value()) {
                register(imported);
            }
        }

        // register @Bean methods from this config
        for (var method : cfg.getDeclaredMethods()) {
            if (method.isAnnotationPresent(Bean.class)) {
                Object instance = cfg.getDeclaredConstructor().newInstance();
                String beanValue = (String) method.invoke(instance);
                context.put(method.getName(), beanValue);
                System.out.println("Registered bean '" + method.getName()
                    + "' from " + cfg.getSimpleName());
            }
        }
    }
}
```

**How to run:** `java ConfigurationImportDemo.java`

Expected output:
```
Registered bean 'passwordEncoder' from SecurityConfig
Registered bean 'dataSource' from DataSourceConfig
Registered bean 'appService' from AppConfig
=== Beans registered in context ===
  passwordEncoder → BCryptPasswordEncoder
  dataSource → HikariDataSource(url=jdbc:h2:mem:demo)
  appService → AppService
```

## 6. Walkthrough

- Custom `@Configuration`, `@Bean`, `@Import` annotations mirror Spring's real ones so the demo compiles without Spring on the classpath.
- `register(AppConfig.class)` is called first. It checks `@Import` and recurses into `SecurityConfig` then `DataSourceConfig` before processing `AppConfig`'s own `@Bean` methods — exactly Spring's depth-first import order.
- `context.containsKey(cfg.getSimpleName())` guards against importing the same config twice (Spring does this too via a seen-set).
- Each `@Bean` method is invoked reflectively on a fresh instance of the config class. In real Spring, the config class is **CGLIB-proxied**, so a second call to the same `@Bean` method returns the cached singleton instead of creating a new object.
- The output shows beans from imported configs appearing **before** beans from the importing config, demonstrating that `@Import` declarations are processed first.

## 7. Gotchas & takeaways

> `@Configuration` classes are CGLIB-proxied by default. This means `@Bean` methods **cannot be `final`** or **in a `final` class** — CGLIB can't subclass them and you'll get an `IllegalStateException` at startup.

> Using `@Import` is explicit and predictable; using component scan is implicit and can register unexpected classes if your base package is too broad. For library code, always prefer `@Import`.

- `@Configuration` is stronger than `@Component` — it enables inter-bean method call interception (singleton guarantee). `@Component` with `@Bean` methods does **not** proxy them.
- Imported configs are registered exactly as if Spring found them by scanning — their `@Bean`, `@Import`, and `@Conditional` annotations are all honoured.
- `@Import` accepts `ImportSelector` and `ImportBeanDefinitionRegistrar` for programmatic, dynamic imports — the mechanism behind `@EnableXxx` annotations.
- Avoid circular imports (A imports B, B imports A). Spring will often detect this and throw, but the error message can be confusing.
- Use `@ImportAutoConfiguration` (Spring Boot-specific) in test slices to import only the auto-configuration classes you need.
