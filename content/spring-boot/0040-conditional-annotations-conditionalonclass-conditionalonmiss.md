---
card: spring-boot
gi: 40
slug: conditional-annotations-conditionalonclass-conditionalonmiss
title: "@Conditional annotations (@ConditionalOnClass, @ConditionalOnMissingBean, etc.)"
---

## 1. What it is

`@Conditional` annotations let a Spring `@Bean` or `@Configuration` be registered **only when a specific condition is true** at application startup. They are the engine that makes auto-configuration smart: instead of always registering a bean, Spring evaluates a condition first and only creates the bean if the condition passes.

Spring Boot ships a rich library of ready-made conditions:

| Annotation | Passes when… |
|---|---|
| `@ConditionalOnClass(Foo.class)` | `Foo` is on the classpath |
| `@ConditionalOnMissingClass("com.Foo")` | `Foo` is NOT on the classpath |
| `@ConditionalOnBean(Foo.class)` | a `Foo` bean already exists in the context |
| `@ConditionalOnMissingBean(Foo.class)` | NO `Foo` bean exists in the context |
| `@ConditionalOnProperty("spring.datasource.url")` | a property is set (and optionally has a specific value) |
| `@ConditionalOnWebApplication` | the app is a web (servlet) application |
| `@ConditionalOnExpression("${flag:false}")` | a SpEL expression evaluates to true |

## 2. Why & when

Without `@Conditional`, auto-configuration classes would have to register every possible bean upfront and let them collide. Instead, each auto-configuration bean carries the exact conditions under which it should exist, making the context predictable and avoiding conflicts.

Use `@Conditional` annotations:
- When writing your own auto-configuration or starter.
- When a bean should only exist in certain environments (`@ConditionalOnProperty("feature.enabled", havingValue = "true")`).
- When a bean depends on another bean being present (`@ConditionalOnBean`).
- When a bean should only be created if nobody else created one (`@ConditionalOnMissingBean`).

## 3. Core concept

Think of `@Conditional` as an **entry gate**. Before the factory (Spring context) lets a bean in, the gate checks a condition. If the condition passes, the bean is admitted; if not, the gate stays shut and the bean is never created. The gate is evaluated once at startup; it does not re-evaluate at runtime.

Evaluation order matters:
- `@ConditionalOnClass` is evaluated at class-load time: if the class is missing, the whole config class may not even be loaded (Spring uses ASM byte-code reading, not reflection, to avoid `ClassNotFoundException`).
- `@ConditionalOnBean` and `@ConditionalOnMissingBean` are evaluated after the current phase of bean definitions is registered — so bean order in the context matters.
- Conditions on auto-configuration classes are evaluated **after** all user `@Configuration` is processed, giving user beans priority.

You can stack multiple conditions on one `@Bean` — all must pass:
```java
@Bean
@ConditionalOnClass(DataSource.class)
@ConditionalOnMissingBean(DataSource.class)
@ConditionalOnProperty(prefix = "spring.datasource", name = "url")
public DataSource dataSource() { ... }
```

## 4. Diagram

<svg viewBox="0 0 660 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple @Conditional annotations acting as gates before a bean is created">
  <!-- Bean creation pipeline -->
  <text x="20" y="30" fill="#e6edf3" font-size="13" font-family="monospace">@Bean dataSource()</text>

  <!-- Gate 1 -->
  <rect x="20" y="48" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="70" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">@ConditionalOnClass</text>
  <text x="110" y="88" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">DataSource on classpath?</text>

  <!-- Arrow 1 pass -->
  <line x1="200" y1="72" x2="238" y2="72" stroke="#6db33f" stroke-width="2" marker-end="url(#c1)"/>
  <text x="220" y="66" fill="#6db33f" font-size="10" font-family="sans-serif">✅</text>

  <!-- Gate 2 -->
  <rect x="240" y="48" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="70" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">@ConditionalOnMissing</text>
  <text x="330" y="88" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">DataSource    Bean</text>

  <!-- Arrow 2 pass -->
  <line x1="420" y1="72" x2="458" y2="72" stroke="#6db33f" stroke-width="2" marker-end="url(#c1)"/>
  <text x="440" y="66" fill="#6db33f" font-size="10" font-family="sans-serif">✅</text>

  <!-- Gate 3 -->
  <rect x="460" y="48" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="70" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">@ConditionalOnProperty</text>
  <text x="550" y="88" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">spring.datasource.url set?</text>

  <!-- Arrow 3 pass to bean -->
  <line x1="550" y1="98" x2="550" y2="136" stroke="#6db33f" stroke-width="2" marker-end="url(#c1)"/>
  <text x="558" y="120" fill="#6db33f" font-size="10" font-family="sans-serif">✅ all pass</text>

  <!-- Bean box -->
  <rect x="400" y="138" width="300" height="44" rx="6" fill="#16202e" stroke="#6db33f" stroke-width="2"/>
  <text x="550" y="165" fill="#e6edf3" font-size="12" font-family="monospace" text-anchor="middle">dataSource bean created ✅</text>

  <!-- Fail path from gate 2 -->
  <line x1="330" y1="98" x2="330" y2="190" stroke="#f85149" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#c2)"/>
  <rect x="200" y="192" width="240" height="40" rx="6" fill="#3d2020" stroke="#f85149" stroke-width="1"/>
  <text x="320" y="210" fill="#f85149" font-size="11" font-family="monospace" text-anchor="middle">❌ skip — user DataSource exists</text>
  <text x="275" y="152" fill="#f85149" font-size="10" font-family="sans-serif">if bean exists</text>

  <defs>
    <marker id="c1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
    <marker id="c2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/>
    </marker>
  </defs>
</svg>

All three conditions must pass for the bean to be created; any single failure causes the entire `@Bean` to be skipped.

## 5. Runnable example

```java
// ConditionalDemo.java
// How to run: java ConditionalDemo.java  (JDK 17+)
// Demonstrates @ConditionalOnClass, @ConditionalOnMissingBean,
// and @ConditionalOnProperty logic without Spring on the classpath.

import java.util.*;

public class ConditionalDemo {

    // ── simulate the environment ────────────────────────────────────
    static Set<String>    classpath   = Set.of("HikariCP", "spring-webmvc");
    static Map<String, String> beans  = new LinkedHashMap<>();
    static Map<String, String> props  = Map.of("spring.datasource.url", "jdbc:postgresql://db/prod");

    public static void main(String[] args) {
        System.out.println("=== Conditional bean registration ===\n");

        // ── scenario 1: all conditions pass ─────────────────────────
        tryRegister("dataSource", "HikariDataSource",
            conditionalOnClass("HikariCP")
            && conditionalOnMissingBean("dataSource")
            && conditionalOnProperty("spring.datasource.url"));

        // ── scenario 2: ConditionalOnMissingBean fails (bean just registered) ─
        tryRegister("dataSource", "TomcatDataSource",
            conditionalOnClass("HikariCP")
            && conditionalOnMissingBean("dataSource")
            && conditionalOnProperty("spring.datasource.url"));

        // ── scenario 3: ConditionalOnClass fails (Mongo not on classpath) ─
        tryRegister("mongoClient", "MongoClient",
            conditionalOnClass("spring-data-mongodb")
            && conditionalOnMissingBean("mongoClient"));

        // ── scenario 4: ConditionalOnProperty fails (no such property) ─
        tryRegister("emailSender", "SmtpEmailSender",
            conditionalOnClass("spring-webmvc")
            && conditionalOnProperty("mail.host"));

        System.out.println("\n=== Final beans in context ===");
        beans.forEach((k, v) -> System.out.printf("  %-14s → %s%n", k, v));
    }

    static boolean conditionalOnClass(String cls) {
        boolean ok = classpath.contains(cls);
        if (!ok) System.out.println("  @ConditionalOnClass('" + cls + "') → ❌ not on classpath");
        return ok;
    }

    static boolean conditionalOnMissingBean(String name) {
        boolean ok = !beans.containsKey(name);
        if (!ok) System.out.println("  @ConditionalOnMissingBean('" + name + "') → ❌ already exists");
        return ok;
    }

    static boolean conditionalOnProperty(String key) {
        boolean ok = props.containsKey(key);
        if (!ok) System.out.println("  @ConditionalOnProperty('" + key + "') → ❌ not set");
        return ok;
    }

    static void tryRegister(String name, String impl, boolean pass) {
        System.out.print("Bean '" + name + "' (" + impl + "): ");
        if (pass) {
            beans.put(name, impl);
            System.out.println("✅ registered");
        } else {
            System.out.println("skipped");
        }
        System.out.println();
    }
}
```

**How to run:** `java ConditionalDemo.java`

Expected output:
```
=== Conditional bean registration ===

Bean 'dataSource' (HikariDataSource): ✅ registered

Bean 'dataSource' (TomcatDataSource):
  @ConditionalOnMissingBean('dataSource') → ❌ already exists
skipped

Bean 'mongoClient' (MongoClient):
  @ConditionalOnClass('spring-data-mongodb') → ❌ not on classpath
skipped

Bean 'emailSender' (SmtpEmailSender):
  @ConditionalOnProperty('mail.host') → ❌ not set
skipped

=== Final beans in context ===
  dataSource     → HikariDataSource
```

## 6. Walkthrough

- Scenario 1: all three conditions pass → `dataSource` is registered as `HikariDataSource`.
- Scenario 2: same bean name is attempted again (simulating a second auto-config trying to provide a fallback). `conditionalOnMissingBean` fails because `dataSource` was just registered — the second attempt is skipped. This is exactly how `DataSourceAutoConfiguration` and a user-supplied `DataSource` coexist.
- Scenario 3: `spring-data-mongodb` is not in `classpath`, so `conditionalOnClass` returns false. `MongoClient` is never considered — conditions short-circuit.
- Scenario 4: `mail.host` is not in `props` → `conditionalOnProperty` fails. The email sender bean is skipped.
- Only `dataSource` ends up in the context, showing that four candidate beans collapsed to one.

## 7. Gotchas & takeaways

> `@ConditionalOnBean` is evaluated against beans **already registered** at the point the condition is checked. If you use it on a user `@Configuration` class (rather than in auto-configuration), and the required bean hasn't been defined yet, the condition can wrongly return false. Prefer `@ConditionalOnBean` in auto-configuration, where ordering is controlled.

> `@ConditionalOnClass` uses ASM byte-code introspection to check for the class, not `Class.forName()`. This means the class doesn't need to be loadable to evaluate the condition — preventing `ClassNotFoundException` during startup if the class is absent.

- Conditions are evaluated in the order they appear; once one fails, the remaining conditions for that bean are not checked.
- Combine `@ConditionalOnClass` (classpath guard) with `@ConditionalOnMissingBean` (override guard) for robust auto-configuration beans.
- `@ConditionalOnProperty` has `havingValue` and `matchIfMissing` attributes for fine-grained property matching.
- Write your own condition by implementing `Condition` and using `@Conditional(MyCondition.class)`.
- The condition evaluation report (`--debug` or `logging.level.org.springframework.boot.autoconfigure=DEBUG`) shows which conditions passed or failed for every candidate.
