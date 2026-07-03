---
card: spring-framework
gi: 137
slug: mutablepropertysources-configurableenvironment
title: "MutablePropertySources / ConfigurableEnvironment"
---

## 1. What it is

`ConfigurableEnvironment` extends `Environment` with mutation capabilities: it exposes `getPropertySources()` which returns the live `MutablePropertySources` collection. `MutablePropertySources` is an ordered list of `PropertySource` objects where position controls priority — first source checked wins.

```java
ConfigurableEnvironment env = ctx.getEnvironment();
MutablePropertySources sources = env.getPropertySources();
sources.addFirst(new MapPropertySource("bootstrap", Map.of("key", "value")));
```

## 2. Why & when

- **Test setup** — inject known values before context refresh without touching files.
- **Bootstrap config** — load a remote config (Vault, ConfigServer) and inject it at highest priority before any `@PropertySource` file is processed.
- **Dynamic override** — replace a `PropertySource` at runtime to change environment-resolved values without restarting.
- **Source introspection** — iterate the stack to debug which source is providing a key.

## 3. Core concept

`MutablePropertySources` operations and their priority effects:

| Method | Priority effect |
|---|---|
| `addFirst(source)` | Highest priority — checked first |
| `addLast(source)` | Lowest priority — checked last |
| `addBefore(name, source)` | Just above the named source |
| `addAfter(name, source)` | Just below the named source |
| `replace(name, source)` | Swaps at same position |
| `remove(name)` | Removes by name |
| `contains(name)` | Checks if named source exists |

`ConfigurableEnvironment` also provides:
- `setActiveProfiles(String...)` — set active profiles.
- `setDefaultProfiles(String...)` — set fallback profile.
- `merge(ConfigurableEnvironment)` — merge another environment's sources and profiles (used in parent-child contexts).

The default source names in `StandardEnvironment`:
- `"systemProperties"` — `System.getProperties()`.
- `"systemEnvironment"` — `System.getenv()`.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- ConfigurableEnvironment box -->
  <rect x="10" y="20" width="210" height="160" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="115" y="40" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ConfigurableEnvironment</text>

  <rect x="22" y="50" width="186" height="22" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="115" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">getPropertySources() → MutablePropertySources</text>

  <rect x="22" y="78" width="186" height="22" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="115" y="93" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">setActiveProfiles(String...)</text>

  <rect x="22" y="106" width="186" height="22" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="115" y="121" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">setDefaultProfiles(String...)</text>

  <rect x="22" y="134" width="186" height="22" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="115" y="149" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">merge(ConfigurableEnvironment)</text>

  <!-- MutablePropertySources -->
  <rect x="280" y="20" width="200" height="160" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="380" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">MutablePropertySources</text>

  <rect x="292" y="52" width="176" height="18" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">index 0 — highest priority</text>
  <rect x="292" y="74" width="176" height="18" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="380" y="87" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">index 1</text>
  <rect x="292" y="96" width="176" height="18" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="380" y="109" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">index 2</text>
  <rect x="292" y="118" width="176" height="18" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="380" y="131" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">index N — lowest priority</text>
  <text x="380" y="162" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">addFirst/addLast/addBefore/addAfter/replace</text>

  <!-- Arrow -->
  <defs>
    <marker id="a137" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="222" y1="100" x2="277" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#a137)"/>

  <text x="570" y="105" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">getProperty(key)</text>
  <text x="570" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">walks index 0 → N</text>
</svg>

`ConfigurableEnvironment` exposes `MutablePropertySources` for full source management; priority = insertion order, index 0 first.

## 5. Runnable example

### Level 1 — Basic

Inspect default sources and add a custom high-priority source.

```java
// MutableSourcesBasic.java
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.util.*;

public class MutableSourcesBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext();
        ConfigurableEnvironment env = ctx.getEnvironment();

        System.out.println("=== Default sources ===");
        env.getPropertySources().forEach(ps ->
            System.out.println("  [" + ps.getName() + "] " + ps.getClass().getSimpleName()));

        // Check default source names
        System.out.println("contains systemProperties: " +
            env.getPropertySources().contains("systemProperties"));
        System.out.println("contains systemEnvironment: " +
            env.getPropertySources().contains("systemEnvironment"));

        // Add a high-priority source
        env.getPropertySources().addFirst(
            new MapPropertySource("override",
                Map.of("app.name", "BootstrappedApp", "env.tier", "blue")));

        System.out.println("\n=== After addFirst ===");
        env.getPropertySources().forEach(ps ->
            System.out.println("  [" + ps.getName() + "]"));

        ctx.register(Object.class);
        ctx.refresh();

        System.out.println("\napp.name  = " + env.getProperty("app.name"));
        System.out.println("env.tier  = " + env.getProperty("env.tier"));
        System.out.println("java.home = " + env.getProperty("java.home")); // from systemProperties
        ctx.close();
    }
}
```

How to run: `java MutableSourcesBasic.java`

Default sources are `systemProperties` and `systemEnvironment`. After `addFirst`, the custom source is at index 0 and is searched first.

### Level 2 — Intermediate

`addBefore` / `addAfter` to fine-tune positioning; `replace` to swap a source.

```java
// MutableSourcesPosition.java
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.util.*;

public class MutableSourcesPosition {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext();
        ConfigurableEnvironment env = ctx.getEnvironment();
        MutablePropertySources sources = env.getPropertySources();

        // Add baseline source last
        sources.addLast(new MapPropertySource("baseline",
            Map.of("db.url", "jdbc:h2:mem:base", "db.pool", "5",
                   "feature.x", "off")));

        // Add a "deployment" source above baseline but below system props
        sources.addAfter("systemEnvironment",
            new MapPropertySource("deployment",
                Map.of("db.url", "jdbc:pg://deploy-db/app", "deploy.region", "eu-west-1")));

        System.out.println("=== Initial stack ===");
        sources.forEach(ps -> System.out.println("  " + ps.getName()));

        ctx.register(Object.class);
        ctx.refresh();

        System.out.println("\n=== Resolution ===");
        System.out.println("db.url         = " + env.getProperty("db.url"));         // from deployment
        System.out.println("db.pool        = " + env.getProperty("db.pool"));        // from baseline
        System.out.println("deploy.region  = " + env.getProperty("deploy.region"));  // from deployment
        System.out.println("feature.x      = " + env.getProperty("feature.x"));     // from baseline

        // Replace the deployment source to simulate a config refresh
        sources.replace("deployment",
            new MapPropertySource("deployment",
                Map.of("db.url", "jdbc:pg://primary-db/app", "deploy.region", "us-east-1")));

        System.out.println("\n=== After replace ===");
        System.out.println("db.url        = " + env.getProperty("db.url"));
        System.out.println("deploy.region = " + env.getProperty("deploy.region"));

        ctx.close();
    }
}
```

How to run: `java MutableSourcesPosition.java`

`addAfter("systemEnvironment", ...)` places `deployment` below `systemEnvironment` but above `baseline`. `replace` swaps the source at the same stack position. `db.url` from `deployment` wins over `baseline` because `deployment` is higher in the stack.

### Level 3 — Advanced

`merge()` for parent-child context environments; programmatic profile management; full stack inspection.

```java
// MutableSourcesMerge.java
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.util.*;

public class MutableSourcesMerge {
    public static void main(String[] args) {
        // Parent context — "infrastructure" config
        var parentCtx = new AnnotationConfigApplicationContext();
        ConfigurableEnvironment parentEnv = parentCtx.getEnvironment();
        parentEnv.getPropertySources().addFirst(
            new MapPropertySource("infraConfig",
                Map.of("db.url", "jdbc:pg://shared-db/app",
                       "mq.broker", "kafka:9092",
                       "region", "eu-west-1")));
        parentEnv.setActiveProfiles("prod");
        parentCtx.register(Object.class);
        parentCtx.refresh();

        System.out.println("=== Parent context sources ===");
        parentEnv.getPropertySources().forEach(ps ->
            System.out.println("  " + ps.getName()));

        // Child context — merges parent's environment
        var childCtx = new AnnotationConfigApplicationContext();
        ConfigurableEnvironment childEnv = childCtx.getEnvironment();

        // Add child-specific source first
        childEnv.getPropertySources().addFirst(
            new MapPropertySource("serviceConfig",
                Map.of("service.name", "OrderService",
                       "service.port", "8080",
                       "db.url", "jdbc:pg://service-db/orders")));  // overrides parent's db.url

        // Merge parent environment: parent's sources added after child's existing sources
        childEnv.merge(parentEnv);

        childCtx.setParent(parentCtx);
        childCtx.register(Object.class);
        childCtx.refresh();

        System.out.println("\n=== Child context sources after merge ===");
        childEnv.getPropertySources().forEach(ps ->
            System.out.println("  " + ps.getName()));

        System.out.println("\n=== Child resolution ===");
        System.out.println("service.name = " + childEnv.getProperty("service.name")); // child
        System.out.println("db.url       = " + childEnv.getProperty("db.url"));       // child wins over parent
        System.out.println("mq.broker    = " + childEnv.getProperty("mq.broker"));   // from parent
        System.out.println("region       = " + childEnv.getProperty("region"));       // from parent

        System.out.println("Active profiles: " +
            Arrays.toString(childEnv.getActiveProfiles()));  // inherited from parent

        childCtx.close();
        parentCtx.close();
    }
}
```

How to run: `java MutableSourcesMerge.java`

`childEnv.merge(parentEnv)` copies parent's `PropertySource` objects to the end of the child's source list, and merges active/default profiles. Child's own sources have higher priority. `db.url` is overridden by the child's `serviceConfig`; `mq.broker` falls through to the parent's `infraConfig`.

## 6. Walkthrough

Execution for Level 3:

1. **Parent** creates `infraConfig` source with `db.url=jdbc:pg://shared-db/app`, activates `"prod"`.
2. **Child** creates `serviceConfig` with `db.url=jdbc:pg://service-db/orders` (overrides parent's db.url).
3. **`childEnv.merge(parentEnv)`** — appends parent's sources to end of child's stack: `[systemProperties, systemEnvironment, serviceConfig, infraConfig, ...]`. Copies `"prod"` to child's active profiles.
4. **`childEnv.getProperty("db.url")`** → walks stack → `serviceConfig` hit first → `"jdbc:pg://service-db/orders"`.
5. **`childEnv.getProperty("mq.broker")`** → `serviceConfig` (absent) → `infraConfig` hit → `"kafka:9092"`.
6. **`getActiveProfiles()`** → `["prod"]` (inherited from parent via merge).

## 7. Gotchas & takeaways

> `MutablePropertySources.addFirst` throws `IllegalArgumentException` if a source with the same name already exists. Use `contains(name)` before adding, or use `replace(name, source)` to swap an existing source. Source names must be unique within one `MutablePropertySources` instance.

> `merge()` copies source references, not values — if you mutate a `MapPropertySource` after merging, both parent and child see the change. Use a defensive copy if isolation is needed.

- `ConfigurableEnvironment` is obtained via `ctx.getEnvironment()` before `ctx.refresh()` — mutations before refresh affect bean creation; mutations after refresh affect `env.getProperty()` calls but not already-injected `@Value` fields.
- `StandardEnvironment` (used in tests and standalone apps) starts with only `systemProperties` and `systemEnvironment`. Spring Boot's `StandardServletEnvironment` adds several more including servlet context params.
- The source name `"systemProperties"` is the reliable reference point for `addBefore`/`addAfter` — use it to slot custom sources into a predictable position.
- Iterating `env.getPropertySources()` yields sources in descending priority order (index 0 first).
