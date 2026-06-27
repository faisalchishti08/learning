---
card: spring-boot
gi: 43
slug: autoconfiguration-ordering-autoconfigurebefore-after
title: "@AutoConfiguration & ordering (@AutoConfigureBefore/After)"
---

## 1. What it is

`@AutoConfigureBefore` and `@AutoConfigureAfter` are annotations that control the **relative ordering** of Spring Boot auto-configuration classes. They express a dependency relationship: "apply me before X" or "apply me only after X has been applied."

```java
@AutoConfiguration
@AutoConfigureAfter(DataSourceAutoConfiguration.class)
public class JpaRepositoriesAutoConfiguration {
    // safe to reference DataSource here because DataSourceAutoConfiguration ran first
}
```

These annotations are used exclusively inside auto-configuration classes. They have no effect on user-defined `@Configuration` classes.

## 2. Why & when

Auto-configuration classes are discovered from a flat list in `AutoConfiguration.imports`. Without ordering, Spring Boot can apply them in any order, which breaks configurations that depend on beans created by another auto-configuration.

Classic example: `JpaRepositoriesAutoConfiguration` needs a `DataSource` bean (created by `DataSourceAutoConfiguration`). If JPA repositories are configured before the `DataSource` bean exists, the `EntityManagerFactory` cannot be created.

Use `@AutoConfigureAfter` when your auto-configuration:
- Uses a bean that another auto-configuration provides.
- Inherits from or extends functionality of another auto-configuration.

Use `@AutoConfigureBefore` when your auto-configuration:
- Provides something that another auto-configuration consumes.
- Must set up a precondition before another auto-configuration runs.

## 3. Core concept

Think of auto-configurations as tasks on a project board. Normally tasks are picked up in any order. `@AutoConfigureBefore` and `@AutoConfigureAfter` add arrows between tasks: "task B cannot start until task A is done." Spring Boot topologically sorts the auto-configuration candidate list using these arrows before applying any of them.

Key rules:
1. Ordering affects **application order** within the auto-configuration phase only. All auto-configurations still run after all user `@Configuration` classes.
2. If the referenced class is not in the candidate list (excluded or not on classpath), the ordering annotation is ignored — no error.
3. Circular ordering (A after B, B after A) raises a `BeanDefinitionParsingException`.
4. For absolute position (not relative), use `@AutoConfigureOrder` (tutorial 44).

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@AutoConfigureAfter causing JpaRepositoriesAutoConfiguration to run after DataSourceAutoConfiguration">
  <!-- Timeline arrow -->
  <line x1="40" y1="180" x2="620" y2="180" stroke="#8b949e" stroke-width="2" marker-end="url(#tl)"/>
  <text x="330" y="220" fill="#8b949e" font-size="11" font-family="sans-serif" text-anchor="middle">auto-configuration application order →</text>

  <!-- User config phase -->
  <rect x="40" y="120" width="120" height="50" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="100" y="140" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">User</text>
  <text x="100" y="156" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">@Config</text>
  <line x1="100" y1="170" x2="100" y2="180" stroke="#8b949e" stroke-width="1.5"/>

  <!-- DataSourceAutoConfiguration -->
  <rect x="200" y="80" width="160" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="280" y="104" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">DataSource</text>
  <text x="280" y="120" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">AutoConfig</text>
  <text x="280" y="140" fill="#e6edf3" font-size="10" font-family="monospace" text-anchor="middle">→ dataSource bean</text>
  <text x="280" y="156" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">(no ordering needed)</text>
  <line x1="280" y1="170" x2="280" y2="180" stroke="#6db33f" stroke-width="2"/>

  <!-- JpaRepositoriesAutoConfiguration -->
  <rect x="420" y="40" width="180" height="130" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="510" y="64" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">JpaRepositories</text>
  <text x="510" y="80" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">AutoConfig</text>
  <text x="510" y="100" fill="#6db33f" font-size="9" font-family="monospace" text-anchor="middle">@AutoConfigureAfter</text>
  <text x="510" y="116" fill="#6db33f" font-size="9" font-family="monospace" text-anchor="middle">(DataSourceAutoConfig)</text>
  <text x="510" y="140" fill="#e6edf3" font-size="10" font-family="monospace" text-anchor="middle">→ entityManager</text>
  <text x="510" y="156" fill="#e6edf3" font-size="10" font-family="monospace" text-anchor="middle">→ txManager</text>
  <line x1="510" y1="170" x2="510" y2="180" stroke="#79c0ff" stroke-width="2"/>

  <!-- Ordering arrow between the two -->
  <line x1="362" y1="125" x2="418" y2="125" stroke="#6db33f" stroke-width="1.8" stroke-dasharray="4,3" marker-end="url(#tl)"/>
  <text x="390" y="115" fill="#6db33f" font-size="10" font-family="sans-serif" text-anchor="middle">after</text>

  <defs>
    <marker id="tl" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

`@AutoConfigureAfter(DataSourceAutoConfiguration.class)` ensures `JpaRepositoriesAutoConfiguration` always runs after `DataSourceAutoConfiguration`, so the `DataSource` bean exists when JPA needs it.

## 5. Runnable example

```java
// AutoConfigOrderDemo.java
// How to run: java AutoConfigOrderDemo.java  (JDK 17+)
// Simulates @AutoConfigureAfter/@AutoConfigureBefore topological sort
// without Spring on the classpath.

import java.lang.annotation.*;
import java.util.*;

@Retention(RetentionPolicy.RUNTIME)
@interface AutoConfigureAfter { Class<?>[] value(); }

@Retention(RetentionPolicy.RUNTIME)
@interface AutoConfigureBefore { Class<?>[] value(); }

// ── auto-configuration classes ────────────────────────────────────
@AutoConfigureAfter({}) // no dep — runs early
class DataSourceAutoConfiguration {
    static String apply() { return "dataSource bean"; }
}

@AutoConfigureAfter(DataSourceAutoConfiguration.class)
class HibernateJpaAutoConfiguration {
    static String apply() { return "entityManagerFactory, transactionManager"; }
}

@AutoConfigureAfter(HibernateJpaAutoConfiguration.class)
class JpaRepositoriesAutoConfiguration {
    static String apply() { return "jpaRepositories proxy beans"; }
}

@AutoConfigureBefore(JpaRepositoriesAutoConfiguration.class)
class FlywayAutoConfiguration {
    // schema migrations must run before JPA repositories are initialized
    static String apply() { return "flywayMigration (schema ready)"; }
}

public class AutoConfigOrderDemo {

    record Node(String name, Class<?> cls, List<String> after, List<String> before) {}

    public static void main(String[] args) throws Exception {
        List<Class<?>> candidates = List.of(
            DataSourceAutoConfiguration.class,
            HibernateJpaAutoConfiguration.class,
            JpaRepositoriesAutoConfiguration.class,
            FlywayAutoConfiguration.class
        );

        // Build ordering graph
        Map<String, Node> nodes = new LinkedHashMap<>();
        for (Class<?> cls : candidates) {
            List<String> after = new ArrayList<>();
            List<String> before = new ArrayList<>();
            if (cls.isAnnotationPresent(AutoConfigureAfter.class))
                for (Class<?> dep : cls.getAnnotation(AutoConfigureAfter.class).value())
                    after.add(dep.getSimpleName());
            if (cls.isAnnotationPresent(AutoConfigureBefore.class))
                for (Class<?> dep : cls.getAnnotation(AutoConfigureBefore.class).value())
                    before.add(dep.getSimpleName());
            nodes.put(cls.getSimpleName(), new Node(cls.getSimpleName(), cls, after, before));
        }

        // Convert @Before to reverse @After edges, then topological sort (Kahn's algorithm)
        Map<String, Set<String>> deps = new LinkedHashMap<>();
        Map<String, Integer> inDegree = new LinkedHashMap<>();
        for (String n : nodes.keySet()) { deps.put(n, new LinkedHashSet<>()); inDegree.put(n, 0); }

        for (Node node : nodes.values()) {
            for (String dep : node.after()) {
                deps.get(dep).add(node.name());   // dep must come before node
                inDegree.merge(node.name(), 1, Integer::sum);
            }
            for (String successor : node.before()) {
                deps.get(node.name()).add(successor); // node must come before successor
                inDegree.merge(successor, 1, Integer::sum);
            }
        }

        Queue<String> queue = new ArrayDeque<>();
        inDegree.forEach((n, d) -> { if (d == 0) queue.add(n); });
        List<String> order = new ArrayList<>();
        while (!queue.isEmpty()) {
            String n = queue.poll();
            order.add(n);
            for (String next : deps.get(n)) {
                if (inDegree.merge(next, -1, Integer::sum) == 0) queue.add(next);
            }
        }

        System.out.println("=== Auto-configuration application order ===");
        for (int i = 0; i < order.size(); i++) {
            String name = order.get(i);
            var applyMethod = nodes.get(name).cls().getDeclaredMethod("apply");
            String beans = (String) applyMethod.invoke(null);
            System.out.printf("%d. %-44s → %s%n", i + 1, name, beans);
        }
    }
}
```

**How to run:** `java AutoConfigOrderDemo.java`

Expected output:
```
=== Auto-configuration application order ===
1. DataSourceAutoConfiguration             → dataSource bean
2. FlywayAutoConfiguration                 → flywayMigration (schema ready)
3. HibernateJpaAutoConfiguration           → entityManagerFactory, transactionManager
4. JpaRepositoriesAutoConfiguration        → jpaRepositories proxy beans
```

## 6. Walkthrough

- `AutoConfigureAfter` and `AutoConfigureBefore` are simulated with real Java annotations so reflection can read them.
- For each class, the code reads both annotations and translates them into directed edges: `@AutoConfigureAfter(A)` means A → current class; `@AutoConfigureBefore(B)` means current class → B.
- Kahn's algorithm (in-degree topological sort) processes nodes with no remaining dependencies first, producing the linearised application order.
- `FlywayAutoConfiguration` has `@AutoConfigureBefore(JpaRepositoriesAutoConfiguration.class)`, so it runs before JPA repositories (schema must be ready before Hibernate scans entities).
- The output shows `Flyway` (index 2) before `JpaRepositories` (index 4), confirming the `@Before` constraint is satisfied.

## 7. Gotchas & takeaways

> `@AutoConfigureAfter` and `@AutoConfigureBefore` only affect **relative order within the auto-configuration phase**. They cannot make an auto-configuration run before user `@Configuration` classes — that ordering is fixed: user config always wins.

> Referencing a class that is not on the classpath in these annotations is safe — the reference is by class literal so it must compile, but Spring ignores the ordering constraint if the referenced auto-configuration is not active. Prefer `@AutoConfigureAfter` with `name` (string) attribute to avoid compile-time dependencies between modules.

- Use `@AutoConfigureAfter` (not `@DependsOn`) for ordering between auto-configurations; `@DependsOn` is for bean-level ordering within a single context phase.
- Circular constraints (`A after B, B after A`) cause `BeanDefinitionParsingException` at startup.
- In Spring Boot 3.x, `@AutoConfiguration(after = ..., before = ...)` combines the class annotation and ordering into one declaration.
- Check ordering is correct by running with `--debug` and reading the "Positive matches" section in order.
