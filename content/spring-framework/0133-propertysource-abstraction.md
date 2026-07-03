---
card: spring-framework
gi: 133
slug: propertysource-abstraction
title: "PropertySource abstraction"
---

## 1. What it is

`PropertySource<T>` is Spring's base class for any source of key-value pairs — a properties file, JVM system properties, OS environment variables, JNDI, a database, a remote config service. Each source is a named container with a `getProperty(String key)` method.

Spring stacks multiple `PropertySource` instances in a `MutablePropertySources` list. When resolving a key, Spring searches sources in order from highest to lowest priority, returning the first non-null value found.

```java
PropertySource<?> mySource = new MapPropertySource("mySource",
    Map.of("app.mode", "fast", "app.timeout", "30"));
ctx.getEnvironment().getPropertySources().addFirst(mySource);
```

## 2. Why & when

- **Custom config sources** — read properties from a database table, a Vault secret, a remote HTTP endpoint, or a custom format.
- **Priority control** — insert your source at the right position (`addFirst`, `addLast`, `addBefore`, `addAfter`) to control override precedence.
- **Testing** — inject a `MapPropertySource` to override specific properties without touching real files.
- **Auditing** — iterate `getPropertySources()` to see the full stack of where a property could come from.

## 3. Core concept

Key `PropertySource` subtypes:

| Class | Backed by |
|---|---|
| `PropertiesPropertySource` | `java.util.Properties` |
| `MapPropertySource` | `Map<String, Object>` |
| `SystemEnvironmentPropertySource` | OS environment variables (case/underscore folding) |
| `CommandLinePropertySource` | CLI arguments (`--key=value`) |
| `ResourcePropertySource` | `.properties` file via Spring `Resource` |
| `CompositePropertySource` | Multiple sources aggregated under one name |

`MutablePropertySources` operations:
- `addFirst(source)` — highest priority.
- `addLast(source)` — lowest priority.
- `addBefore(name, source)` — just above the named source.
- `addAfter(name, source)` — just below the named source.
- `remove(name)` — remove a source by name.
- `replace(name, source)` — swap a source.

`SystemEnvironmentPropertySource` applies relaxed binding: `MY_APP_URL` resolves queries for `my.app.url`, `MY_APP_URL`, or `my_app_url` — important for Kubernetes / Docker deployments.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- Stack -->
  <rect x="10"  y="25"  width="240" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="130" y="45"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">1. commandLineArgs (highest)</text>

  <rect x="10"  y="60"  width="240" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="80"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">2. systemProperties (-Dkey=val)</text>

  <rect x="10"  y="95"  width="240" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="115" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">3. systemEnvironment (OS env)</text>

  <rect x="10"  y="130" width="240" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="150" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">4. @PropertySource files (custom)</text>

  <!-- Label -->
  <text x="130" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">first non-null value wins</text>

  <!-- Resolution arrow -->
  <rect x="340" y="55" width="185" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="432" y="78" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">env.getProperty("k")</text>
  <text x="432" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">walks sources top→down</text>
  <text x="432" y="115" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">returns first non-null</text>

  <!-- Output -->
  <rect x="600" y="75" width="90" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="645" y="93" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">value</text>
  <text x="645" y="107" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">or null</text>

  <line x1="252" y1="95" x2="337" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#a133)"/>
  <line x1="527" y1="95" x2="597" y2="95" stroke="#79c0ff" stroke-width="2" marker-end="url(#b133)"/>
  <defs>
    <marker id="a133" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b133" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`PropertySource` stack is searched top-to-bottom; the first source with a non-null value for the requested key wins.

## 5. Runnable example

### Level 1 — Basic

Add a `MapPropertySource` and verify priority over a lower-priority `PropertiesPropertySource`.

```java
// PropertySourceAbstractionBasic.java
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.util.*;

public class PropertySourceAbstractionBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext();
        ConfigurableEnvironment env = ctx.getEnvironment();

        // Lower-priority source (added last → lowest priority)
        Properties base = new Properties();
        base.setProperty("app.name",    "BaseApp");
        base.setProperty("app.version", "1.0");
        base.setProperty("app.debug",   "false");
        env.getPropertySources().addLast(
            new PropertiesPropertySource("base", base));

        // Higher-priority source (added first → wins for any key it contains)
        env.getPropertySources().addFirst(
            new MapPropertySource("override",
                Map.of("app.name", "OverriddenApp", "app.debug", "true")));

        ctx.register(Object.class);   // dummy — no beans needed
        ctx.refresh();

        System.out.println("app.name    = " + env.getProperty("app.name"));    // from override
        System.out.println("app.version = " + env.getProperty("app.version")); // from base
        System.out.println("app.debug   = " + env.getProperty("app.debug"));   // from override

        // Inspect the full stack
        System.out.println("\nProperty sources in priority order:");
        env.getPropertySources().forEach(ps ->
            System.out.println("  [" + ps.getName() + "] " + ps.getClass().getSimpleName()));

        ctx.close();
    }
}
```

How to run: `java PropertySourceAbstractionBasic.java`

`"override"` was added first → highest priority. For `app.name` and `app.debug`, the override source wins. For `app.version`, only the base source has it, so it falls through.

### Level 2 — Intermediate

Custom `PropertySource` that reads from a simulated database table.

```java
// PropertySourceAbstractionCustom.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.util.*;

// Simulated DB property source
class DatabasePropertySource extends PropertySource<Map<String, String>> {
    public DatabasePropertySource(String name) {
        super(name, loadFromDb());
    }

    private static Map<String, String> loadFromDb() {
        System.out.println("[DB] loading properties from config table");
        return Map.of(
            "feature.payment", "stripe",
            "feature.shipping", "fedex",
            "service.timeout",  "60"
        );
    }

    @Override
    public Object getProperty(String name) {
        return getSource().get(name);
    }
}

class FeatureConfig {
    @Value("${feature.payment}")  String payment;
    @Value("${feature.shipping}") String shipping;
    @Value("${service.timeout}")  int timeout;
    @Value("${app.name:MyApp}")   String appName;   // default if absent

    public void print() {
        System.out.println("payment=" + payment + " shipping=" + shipping
            + " timeout=" + timeout + " app=" + appName);
    }
}

@Configuration
@ComponentScan(basePackageClasses = PropertySourceAbstractionCustom.class)
class PropCfg {}

public class PropertySourceAbstractionCustom {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext();

        // Add our custom DB source (lower priority than system props)
        ctx.getEnvironment().getPropertySources()
           .addLast(new DatabasePropertySource("dbConfig"));

        ctx.register(PropCfg.class);
        ctx.refresh();

        ctx.getBean(FeatureConfig.class).print();

        // Override at runtime via system property (higher priority)
        System.out.println("\n-- Override feature.payment via system property --");
        System.setProperty("feature.payment", "paypal");
        // Re-read via environment (not re-injected — already in FeatureConfig)
        System.out.println("env.getProperty = " +
            ctx.getEnvironment().getProperty("feature.payment"));
        System.clearProperty("feature.payment");

        ctx.close();
    }
}
```

How to run: `java PropertySourceAbstractionCustom.java`

`DatabasePropertySource` extends `PropertySource<Map<String,String>>` and returns values from the simulated DB map. The system property override demonstrates that higher-priority sources (system properties) win at `env.getProperty()` time.

### Level 3 — Advanced

`CompositePropertySource` aggregating multiple sources; dynamic source replacement; source-level inspection.

```java
// PropertySourceAbstractionAdvanced.java
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.util.*;

public class PropertySourceAbstractionAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext();
        ConfigurableEnvironment env = ctx.getEnvironment();

        // Build a composite source that aggregates region + environment settings
        var composite = new CompositePropertySource("infraConfig");
        composite.addPropertySource(new MapPropertySource("region",
            Map.of("region.name", "us-east-1", "region.az", "a")));
        composite.addPropertySource(new MapPropertySource("envSettings",
            Map.of("deploy.strategy", "blue-green", "replicas", "3")));

        // Add composite as a medium-priority source
        env.getPropertySources().addLast(composite);

        ctx.register(Object.class);
        ctx.refresh();

        System.out.println("=== Property resolution ===");
        System.out.println("region.name:     " + env.getProperty("region.name"));
        System.out.println("deploy.strategy: " + env.getProperty("deploy.strategy"));
        System.out.println("replicas:        " + env.getProperty("replicas"));

        // Inspect sources
        System.out.println("\n=== Full source stack ===");
        printSources(env.getPropertySources(), 0);

        // Dynamic replacement — swap in a different region config
        env.getPropertySources().replace("infraConfig",
            new MapPropertySource("infraConfig",
                Map.of("region.name", "eu-west-1", "region.az", "b",
                       "deploy.strategy", "rolling", "replicas", "5")));

        System.out.println("\n=== After source replacement ===");
        System.out.println("region.name:     " + env.getProperty("region.name"));
        System.out.println("deploy.strategy: " + env.getProperty("deploy.strategy"));
        System.out.println("replicas:        " + env.getProperty("replicas"));

        ctx.close();
    }

    static void printSources(PropertySources sources, int indent) {
        String pad = " ".repeat(indent * 2);
        for (PropertySource<?> ps : sources) {
            System.out.println(pad + "[" + ps.getName() + "] " + ps.getClass().getSimpleName());
            if (ps instanceof CompositePropertySource cps) {
                printSources(cps, indent + 1);
            }
        }
    }
}
```

How to run: `java PropertySourceAbstractionAdvanced.java`

`CompositePropertySource` wraps two `MapPropertySource` objects. `replace()` swaps the composite with a plain `MapPropertySource` dynamically. The `printSources` helper shows nested sources within the composite.

## 6. Walkthrough

Execution for Level 3:

1. **`CompositePropertySource("infraConfig")` created** — contains `region` and `envSettings` sub-sources.
2. **`addLast(composite)`** — lowest priority in the environment.
3. **`env.getProperty("region.name")`** — searches: systemProperties → systemEnvironment → infraConfig → found in `region` sub-source → `"us-east-1"`.
4. **`printSources()`** — shows full tree including the composite's children.
5. **`replace("infraConfig", new MapPropertySource(...))`** — swaps the composite with a flat map. Same key `"infraConfig"` keeps the position in the stack.
6. **`env.getProperty("region.name")`** → now reads from the replacement map → `"eu-west-1"`.

Expected output (abbreviated):
```
=== Property resolution ===
region.name:     us-east-1
deploy.strategy: blue-green
replicas:        3

=== Full source stack ===
[systemProperties] PropertiesPropertySource
[systemEnvironment] SystemEnvironmentPropertySource
[infraConfig] CompositePropertySource
  [region] MapPropertySource
  [envSettings] MapPropertySource

=== After source replacement ===
region.name:     eu-west-1
deploy.strategy: rolling
replicas:        5
```

## 7. Gotchas & takeaways

> `@Value` injection happens at bean instantiation time — after `ctx.refresh()`. Changing `PropertySource` values or swapping sources after `ctx.refresh()` does NOT re-inject already-created beans. The change affects `env.getProperty()` calls but not `@Value` fields that have already been resolved.

> `SystemEnvironmentPropertySource` applies relaxed key matching: OS env var `MY_APP_TIMEOUT` resolves the key `my.app.timeout`, `MY_APP_TIMEOUT`, and `MY-APP-TIMEOUT`. This is intentional for containerised deployments but can mask configuration mistakes.

- Source names must be unique in a `MutablePropertySources` — `addFirst`/`addLast` will throw if a source with the same name already exists.
- `PropertySource.containsProperty(key)` lets you check existence before resolving — useful in custom conditions.
- For Spring Boot: auto-configuration layers many sources (`application.properties`, profile-specific files, command-line args, Config Server) using this same mechanism.
- `StandardEnvironment.customizePropertySources()` is the extension point for creating application-level environment subclasses that add default sources.
