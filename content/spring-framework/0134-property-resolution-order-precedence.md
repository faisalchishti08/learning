---
card: spring-framework
gi: 134
slug: property-resolution-order-precedence
title: "Property resolution order & precedence"
---

## 1. What it is

Property resolution order is the priority ranking Spring uses to decide which value a key resolves to when the same key appears in multiple `PropertySource` instances. The rule is simple: the **first** source in `MutablePropertySources` that contains the key wins. Spring searches sources in insertion order (highest priority = added first).

```
-Dapp.timeout=60    → systemProperties  (wins)
app.timeout=30      → application.properties  (loses)
```

## 2. Why & when

Understanding precedence is essential when:

- A property in `application.properties` is being silently overridden by an OS environment variable — and you don't know why.
- You need to ensure your test overrides win over production defaults.
- You're debugging a Spring Boot app where `spring.profiles.active` set in the properties file is being ignored because a command-line arg takes precedence.
- You're adding a custom `PropertySource` and need to place it at exactly the right priority.

## 3. Core concept

Default source stack in `StandardEnvironment` (highest to lowest):

1. **`systemProperties`** — JVM `-Dkey=value` flags.
2. **`systemEnvironment`** — OS environment variables (with relaxed key folding).

Spring Boot adds many more layers between and around these:

1. Command-line arguments (`--key=val`)
2. `SPRING_APPLICATION_JSON` (inline JSON as env var)
3. `@TestPropertySource` (test-only)
4. System properties (`-D`)
5. OS environment variables
6. `application-{profile}.properties` (profile-specific)
7. `application.properties` (base)
8. `@PropertySource` on `@Configuration` classes
9. Default properties (`SpringApplication.setDefaultProperties`)

The key rule: **higher in the list = higher priority**.

`Environment.getProperty(key)` calls `PropertySource.getProperty(key)` on each source in order and returns the first non-null result. For `@Value` injection, `PropertySourcesPlaceholderConfigurer` performs the same walk.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Priority stack (top = highest) -->
  <rect x="10" y="18" width="245" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="132" y="36" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">1. CLI args / -D system props (highest)</text>

  <rect x="10" y="50" width="245" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="132" y="68" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">2. OS environment variables</text>

  <rect x="10" y="82" width="245" height="28" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="132" y="100" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">3. Custom @PropertySource files</text>

  <rect x="10" y="114" width="245" height="28" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="132" y="132" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">4. application.properties (Boot)</text>

  <rect x="10" y="146" width="245" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="132" y="164" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">5. Default values (lowest)</text>

  <!-- Query -->
  <rect x="340" y="75" width="190" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="435" y="98" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">getProperty("key")</text>
  <text x="435" y="116" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">walk top → first non-null</text>

  <!-- Value -->
  <rect x="610" y="87" width="80" height="33" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="650" y="108" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">value</text>

  <line x1="257" y1="100" x2="337" y2="102" stroke="#6db33f" stroke-width="2" marker-end="url(#a134)"/>
  <line x1="532" y1="102" x2="607" y2="103" stroke="#79c0ff" stroke-width="2" marker-end="url(#b134)"/>
  <defs>
    <marker id="a134" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b134" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="190" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Sources checked in insertion order — first source with a non-null value wins</text>
</svg>

Priority is determined by source position; the first source containing the key returns its value.

## 5. Runnable example

### Level 1 — Basic

Demonstrate that system property (`-D`) overrides a file-based property.

```java
// ResolutionOrderBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.nio.file.*;

class AppInfo {
    @Value("${app.name}")    String name;
    @Value("${app.timeout}") int timeout;
    @Value("${app.mode:unknown}") String mode;

    public void print() {
        System.out.printf("name=%s  timeout=%d  mode=%s%n", name, timeout, mode);
    }
}

@Configuration
@PropertySource("classpath:app-order.properties")
@ComponentScan(basePackageClasses = ResolutionOrderBasic.class)
class OrderCfg {}

public class ResolutionOrderBasic {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("app-order.properties"),
            "app.name=FileApp\napp.timeout=30\napp.mode=file\n");

        System.out.println("=== No override ===");
        var ctx1 = new AnnotationConfigApplicationContext(OrderCfg.class);
        ctx1.getBean(AppInfo.class).print();
        ctx1.close();

        System.out.println("\n=== System property overrides ===");
        System.setProperty("app.name", "SystemApp");
        System.setProperty("app.timeout", "99");
        var ctx2 = new AnnotationConfigApplicationContext(OrderCfg.class);
        ctx2.getBean(AppInfo.class).print();  // name and timeout from -D; mode from file
        ctx2.close();

        System.clearProperty("app.name");
        System.clearProperty("app.timeout");
        Files.deleteIfExists(Path.of("app-order.properties"));
    }
}
```

How to run: `java ResolutionOrderBasic.java`

First run: all values from the properties file. Second run: `app.name` and `app.timeout` come from system properties (higher priority); `app.mode` still comes from the file (not in system properties).

### Level 2 — Intermediate

Inspect the resolution chain: show which source each key comes from.

```java
// ResolutionOrderInspect.java
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.nio.file.*;
import java.util.*;

public class ResolutionOrderInspect {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("inspect.properties"),
            "service.url=http://file-server\nservice.timeout=10\nservice.debug=true\n");

        System.setProperty("service.url", "http://sysprop-server");

        var ctx = new AnnotationConfigApplicationContext();
        ctx.getEnvironment().getPropertySources().addLast(
            new org.springframework.core.env.ResourcePropertySource(
                "fileSource", "classpath:inspect.properties"));

        // Also add a custom in-memory source
        ctx.getEnvironment().getPropertySources().addAfter("systemProperties",
            new MapPropertySource("customMiddle",
                Map.of("service.timeout", "99", "service.retry", "3")));

        ctx.register(Object.class);
        ctx.refresh();
        ConfigurableEnvironment env = ctx.getEnvironment();

        String[] keys = {"service.url", "service.timeout", "service.debug", "service.retry"};

        System.out.println("=== Key resolution trace ===");
        for (String key : keys) {
            String value = env.getProperty(key, "<absent>");
            // Find which source supplied it
            String source = "<default>";
            for (PropertySource<?> ps : env.getPropertySources()) {
                if (ps.containsProperty(key)) {
                    source = ps.getName();
                    break;
                }
            }
            System.out.printf("%-22s = %-25s (from: %s)%n", key, value, source);
        }

        System.out.println("\n=== Full source stack ===");
        env.getPropertySources().forEach(ps ->
            System.out.println("  " + ps.getName()));

        ctx.close();
        System.clearProperty("service.url");
        Files.deleteIfExists(Path.of("inspect.properties"));
    }
}
```

How to run: `java ResolutionOrderInspect.java`

The resolution trace shows exactly which source each key comes from: `service.url` from `systemProperties` (highest priority), `service.timeout` from `customMiddle` (inserted above `fileSource`), `service.debug` from `fileSource`, `service.retry` from `customMiddle`.

### Level 3 — Advanced

Full priority demonstration with six source layers and a dynamic mid-context override.

```java
// ResolutionOrderFull.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.nio.file.*;
import java.util.*;

class Config {
    @Value("${api.url}")       String apiUrl;
    @Value("${api.key}")       String apiKey;
    @Value("${api.timeout:30}") int timeout;
    @Value("${api.retries:3}")  int retries;

    public void show() {
        System.out.printf("url=%s key=%s timeout=%ds retries=%d%n",
            apiUrl, apiKey, timeout, retries);
    }
}

@Configuration
@PropertySource("classpath:api-base.properties")
@ComponentScan(basePackageClasses = ResolutionOrderFull.class)
class ApiCfg {}

public class ResolutionOrderFull {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("api-base.properties"),
            "api.url=http://base-api.com\napi.key=base-key\napi.timeout=10\n");

        System.out.println("=== Layer 1: file only ===");
        var ctx1 = new AnnotationConfigApplicationContext(ApiCfg.class);
        ctx1.getBean(Config.class).show();
        ctx1.close();

        System.out.println("\n=== Layer 2: file + custom MapPropertySource ===");
        var ctx2 = new AnnotationConfigApplicationContext();
        ctx2.getEnvironment().getPropertySources().addFirst(
            new MapPropertySource("devOverrides",
                Map.of("api.timeout", "5", "api.retries", "1")));
        ctx2.register(ApiCfg.class);
        ctx2.refresh();
        ctx2.getBean(Config.class).show();
        ctx2.close();

        System.out.println("\n=== Layer 3: custom + system property ===");
        System.setProperty("api.url", "http://sysprop-api.com");
        System.setProperty("api.key", "sysprop-key");
        var ctx3 = new AnnotationConfigApplicationContext();
        ctx3.getEnvironment().getPropertySources().addFirst(
            new MapPropertySource("devOverrides",
                Map.of("api.timeout", "5", "api.key", "dev-key")));
        ctx3.register(ApiCfg.class);
        ctx3.refresh();
        // api.key: systemProperties wins over devOverrides (system props are checked first)
        ctx3.getBean(Config.class).show();

        // Post-refresh: env.getProperty() sees current state, @Value fields don't change
        ctx3.getEnvironment().getPropertySources().addFirst(
            new MapPropertySource("runtimeHotfix", Map.of("api.timeout", "999")));
        System.out.println("env.api.timeout after hotfix: " +
            ctx3.getEnvironment().getProperty("api.timeout"));  // 999
        System.out.println("bean.timeout (unchanged):     " +
            ctx3.getBean(Config.class).timeout);                // still 5

        ctx3.close();
        System.clearProperty("api.url");
        System.clearProperty("api.key");
        Files.deleteIfExists(Path.of("api-base.properties"));
    }
}
```

How to run: `java ResolutionOrderFull.java`

Layer 2 shows `devOverrides` winning over the file for `api.timeout` and `api.retries`. Layer 3 shows system properties winning over `devOverrides` for `api.url` and `api.key`. The post-refresh hotfix shows that `env.getProperty()` updates immediately but `@Value` fields in beans don't re-inject.

## 6. Walkthrough

Execution for Level 3 Layer 3:

1. **`devOverrides` added first** — highest app-level priority.
2. **System properties** — already registered as `"systemProperties"` source, which is searched before `"devOverrides"` since it was already in the stack above it.
3. **`ctx.refresh()`** — `Config` bean instantiated. `@Value("${api.url}")` → `systemProperties` checked first → `"http://sysprop-api.com"`. `@Value("${api.key}")` → `systemProperties` → `"sysprop-key"`. `@Value("${api.timeout:30}")` → `systemProperties` (not present) → `devOverrides` (present: `"5"`) → `5`.
4. **`show()`** → `url=http://sysprop-api.com key=sysprop-key timeout=5s retries=1`.
5. **`addFirst("runtimeHotfix", ...)`** → `api.timeout=999` now at top.
6. **`env.getProperty("api.timeout")`** → `999` (new source wins).
7. **`ctx.getBean(Config.class).timeout`** → `5` (already injected at step 3 — not re-injected).

## 7. Gotchas & takeaways

> `@Value` injection is a **one-time** operation at bean instantiation. Changing `PropertySource` contents or adding new sources after `ctx.refresh()` does not re-inject fields. If you need dynamic property access post-startup, inject `Environment` and call `getProperty()` at call time — not at construction time.

> OS environment variable `MY_APP_TIMEOUT` and system property `my.app.timeout` can both provide a value for the key `my.app.timeout` — and `systemProperties` is checked before `systemEnvironment` by default. This is the standard precedence but can be changed by reordering sources.

- `SystemEnvironmentPropertySource` normalises OS env var names: `MY_APP_TIMEOUT` resolves `my.app.timeout`, `MY_APP_TIMEOUT`, and `MY-APP-TIMEOUT`.
- `addBefore("systemProperties", mySource)` makes `mySource` win over system properties — use with care, it inverts the expected precedence.
- Spring Boot extends this stack with ~15 additional source slots (profile-specific files, JNDI, servlet params, etc.) — all following the same first-non-null rule.
- `env.getPropertySources().iterator()` walks sources in descending priority order — useful for debugging resolution failures.
