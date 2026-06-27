---
card: spring-boot
gi: 44
slug: autoconfigureorder
title: "@AutoConfigureOrder"
---

## 1. What it is

`@AutoConfigureOrder` is an annotation that assigns an **absolute integer priority** to an auto-configuration class within the auto-configuration phase. It is the auto-configuration equivalent of Spring's `@Order` annotation.

```java
@AutoConfiguration
@AutoConfigureOrder(Ordered.LOWEST_PRECEDENCE)   // apply last
public class FallbackAutoConfiguration { ... }
```

Lower numbers mean higher priority (applied earlier). `Ordered.HIGHEST_PRECEDENCE` = `Integer.MIN_VALUE`; `Ordered.LOWEST_PRECEDENCE` = `Integer.MAX_VALUE`.

## 2. Why & when

While `@AutoConfigureBefore` / `@AutoConfigureAfter` (tutorial 43) express **relative** ordering between named classes, `@AutoConfigureOrder` provides **absolute** positioning without naming specific classes.

Use `@AutoConfigureOrder` when:
- You want an auto-configuration to run as early or as late as possible in the auto-configuration phase (e.g. a fallback or catch-all configuration).
- The auto-configuration does not depend on any specific other auto-configuration but simply needs to be prioritised globally.
- You are writing infrastructure-level auto-configurations that must be in place before domain-level ones.

In practice, `@AutoConfigureOrder` is used much less than `@AutoConfigureBefore`/`@AutoConfigureAfter`. Relative ordering is usually more robust because it does not require knowing absolute positions of other configurations.

## 3. Core concept

Think of auto-configurations on a conveyor belt. `@AutoConfigureBefore/After` are like inter-item ties ("this box must come right after that crate"). `@AutoConfigureOrder` is like a priority lane — a number that determines how early in the queue an item sits regardless of its neighbours.

How Spring Boot uses these values:

1. Spring reads `@AutoConfigureBefore` and `@AutoConfigureAfter` from all candidate auto-configurations and builds a dependency graph.
2. It reads `@AutoConfigureOrder` (and also `@Order` on auto-configuration classes) to add a secondary sort key.
3. Topological sort is performed using the dependency graph; ties (no relative dependency) are broken by the `@AutoConfigureOrder` value.
4. The resulting sorted list is the application order.

Constants to know:
- `Ordered.HIGHEST_PRECEDENCE` = `Integer.MIN_VALUE` — first.
- `Ordered.LOWEST_PRECEDENCE` = `Integer.MAX_VALUE` — last.
- Default (no annotation) = `0`.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@AutoConfigureOrder values determining priority on a conveyor belt timeline">
  <!-- Timeline -->
  <line x1="40" y1="130" x2="620" y2="130" stroke="#8b949e" stroke-width="2" marker-end="url(#ord)"/>
  <text x="330" y="160" fill="#8b949e" font-size="11" font-family="sans-serif" text-anchor="middle">auto-configuration application order (lowest value = first)</text>

  <!-- Box A: HIGHEST_PRECEDENCE -->
  <rect x="50" y="70" width="150" height="52" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="125" y="92" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">InfraAutoConfig</text>
  <text x="125" y="108" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">@AutoConfigureOrder</text>
  <text x="125" y="122" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">HIGHEST_PRECEDENCE</text>
  <line x1="125" y1="122" x2="125" y2="130" stroke="#6db33f" stroke-width="1.5"/>

  <!-- Box B: default 0 -->
  <rect x="260" y="70" width="150" height="52" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="335" y="92" fill="#e6edf3" font-size="10" font-family="monospace" text-anchor="middle">DataSourceAutoConfig</text>
  <text x="335" y="108" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">@AutoConfigureOrder</text>
  <text x="335" y="122" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">0 (default)</text>
  <line x1="335" y1="122" x2="335" y2="130" stroke="#8b949e" stroke-width="1.5"/>

  <!-- Box C: LOWEST_PRECEDENCE -->
  <rect x="460" y="70" width="150" height="52" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="535" y="92" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">FallbackAutoConfig</text>
  <text x="535" y="108" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">@AutoConfigureOrder</text>
  <text x="535" y="122" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">LOWEST_PRECEDENCE</text>
  <line x1="535" y1="122" x2="535" y2="130" stroke="#79c0ff" stroke-width="1.5"/>

  <!-- Tick marks -->
  <line x1="125" y1="130" x2="125" y2="140" stroke="#6db33f" stroke-width="2"/>
  <line x1="335" y1="130" x2="335" y2="140" stroke="#8b949e" stroke-width="2"/>
  <line x1="535" y1="130" x2="535" y2="140" stroke="#79c0ff" stroke-width="2"/>

  <defs>
    <marker id="ord" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

`HIGHEST_PRECEDENCE` (min int) runs first, default `0` is in the middle, `LOWEST_PRECEDENCE` (max int) runs last.

## 5. Runnable example

```java
// AutoConfigureOrderDemo.java
// How to run: java AutoConfigureOrderDemo.java  (JDK 17+)
// Demonstrates how @AutoConfigureOrder integers sort auto-configuration classes.

import java.lang.annotation.*;
import java.util.*;

@Retention(RetentionPolicy.RUNTIME)
@interface AutoConfigureOrder { int value() default 0; }

// ── simulated auto-configuration classes ─────────────────────────
@AutoConfigureOrder(Integer.MIN_VALUE)   // HIGHEST_PRECEDENCE
class InfraAutoConfiguration {
    static final String NAME = "InfraAutoConfiguration";
    static final String BEAN = "infraBean (logging, metrics setup)";
}

@AutoConfigureOrder(0)                   // default — not normally needed
class DataSourceAutoConfiguration {
    static final String NAME = "DataSourceAutoConfiguration";
    static final String BEAN = "dataSource";
}

@AutoConfigureOrder(100)                 // slightly lower priority than default
class WebMvcAutoConfiguration {
    static final String NAME = "WebMvcAutoConfiguration";
    static final String BEAN = "dispatcherServlet, viewResolver";
}

@AutoConfigureOrder(Integer.MAX_VALUE)   // LOWEST_PRECEDENCE
class FallbackAutoConfiguration {
    static final String NAME = "FallbackAutoConfiguration";
    static final String BEAN = "fallbackHandler (catch-all)";
}

public class AutoConfigureOrderDemo {

    record Entry(int order, String name, String bean) {}

    public static void main(String[] args) {
        List<Entry> entries = List.of(
            new Entry(FallbackAutoConfiguration.class.getAnnotation(AutoConfigureOrder.class).value(),
                FallbackAutoConfiguration.NAME, FallbackAutoConfiguration.BEAN),
            new Entry(WebMvcAutoConfiguration.class.getAnnotation(AutoConfigureOrder.class).value(),
                WebMvcAutoConfiguration.NAME, WebMvcAutoConfiguration.BEAN),
            new Entry(InfraAutoConfiguration.class.getAnnotation(AutoConfigureOrder.class).value(),
                InfraAutoConfiguration.NAME, InfraAutoConfiguration.BEAN),
            new Entry(DataSourceAutoConfiguration.class.getAnnotation(AutoConfigureOrder.class).value(),
                DataSourceAutoConfiguration.NAME, DataSourceAutoConfiguration.BEAN)
        );

        // Sort by @AutoConfigureOrder value (lower = earlier)
        List<Entry> sorted = entries.stream()
            .sorted(Comparator.comparingInt(Entry::order))
            .toList();

        System.out.println("=== Auto-configuration order (@AutoConfigureOrder) ===");
        System.out.printf("%-6s %-44s %-15s %s%n", "Rank", "Class", "Order value", "Beans created");
        System.out.println("-".repeat(100));
        for (int i = 0; i < sorted.size(); i++) {
            Entry e = sorted.get(i);
            String orderStr = e.order() == Integer.MIN_VALUE ? "MIN_VALUE"
                            : e.order() == Integer.MAX_VALUE ? "MAX_VALUE"
                            : String.valueOf(e.order());
            System.out.printf("%-6d %-44s %-15s %s%n", i + 1, e.name(), orderStr, e.bean());
        }
    }
}
```

**How to run:** `java AutoConfigureOrderDemo.java`

Expected output:
```
=== Auto-configuration order (@AutoConfigureOrder) ===
Rank   Class                                        Order value     Beans created
----------------------------------------------------------------------------------------------------
1      InfraAutoConfiguration                       MIN_VALUE       infraBean (logging, metrics setup)
2      DataSourceAutoConfiguration                  0               dataSource
3      WebMvcAutoConfiguration                      100             dispatcherServlet, viewResolver
4      FallbackAutoConfiguration                    MAX_VALUE       fallbackHandler (catch-all)
```

## 6. Walkthrough

- Each auto-configuration class carries an `@AutoConfigureOrder` annotation with an integer value. Spring Boot reads this annotation from each class after sorting by the dependency graph.
- The list is intentionally shuffled before sorting to prove the sort is driven by the integer value, not insertion order.
- `Comparator.comparingInt(Entry::order)` is the exact comparison Spring Boot uses as a secondary sort (after topological dependency ordering).
- `InfraAutoConfiguration` (MIN_VALUE = `Integer.MIN_VALUE`) sorts first — it sets up cross-cutting infrastructure before domain beans exist.
- `FallbackAutoConfiguration` (MAX_VALUE = `Integer.MAX_VALUE`) sorts last — it acts as a catch-all, providing defaults only if everything else has run.

## 7. Gotchas & takeaways

> `@AutoConfigureOrder` is a **tie-breaker**, not an override. If `@AutoConfigureBefore`/`@AutoConfigureAfter` constraints already determine the order between two classes, the `@AutoConfigureOrder` values are irrelevant for those two classes. The integer is only consulted when the dependency graph does not constrain a pair.

> Do not confuse `@AutoConfigureOrder` with `@Order`. Plain `@Order` on a `@Configuration` class affects the order of user configurations (components discovered via scanning). `@AutoConfigureOrder` only applies within the auto-configuration phase.

- Use constants from `org.springframework.core.Ordered`: `HIGHEST_PRECEDENCE` and `LOWEST_PRECEDENCE`.
- When writing a foundation/infrastructure auto-configuration that must precede all others, use `HIGHEST_PRECEDENCE`.
- When writing a fallback that should only apply if nothing else has provided a bean, combine `@AutoConfigureOrder(LOWEST_PRECEDENCE)` with `@ConditionalOnMissingBean`.
- Arbitrary integers between `HIGHEST_PRECEDENCE` and `LOWEST_PRECEDENCE` are valid — space them out (e.g. multiples of 100) to leave room for future insertions.
- Verify final order via the condition evaluation report (`--debug`) or Spring Boot Actuator's `/actuator/conditions` endpoint.
