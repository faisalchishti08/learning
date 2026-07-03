---
card: spring-framework
gi: 135
slug: propertysource-with-placeholders
title: "@PropertySource with placeholders"
---

## 1. What it is

`@PropertySource` accepts `${...}` substitution tokens in its `value` attribute — the property path itself can be resolved dynamically from already-registered sources. This lets the classpath location of a `.properties` file be determined at runtime rather than hard-coded.

```java
@PropertySource("classpath:${app.env:default}/config.properties")
@Configuration
class AppConfig {}
```

The `${app.env:default}` token resolves before the resource is loaded: if `app.env=prod` is in the environment, Spring loads `classpath:prod/config.properties`.

## 2. Why & when

Use `${...}` expressions in `@PropertySource` paths when:

- Config files are organized into per-environment directories (`dev/`, `prod/`, `staging/`) and the active directory is chosen at startup via a JVM flag.
- You want a single `@Configuration` class that works across environments without code changes.
- The profile name should also determine which properties file is loaded — keeping profile and config file selection in sync.
- You want a fallback path: `${custom.cfg:app}` resolves to `app` if `custom.cfg` is not set.

## 3. Core concept

Resolution order for `${...}` tokens inside `@PropertySource`:

1. The path string is parsed and any `${key:default}` tokens found.
2. Each token is resolved against the current `Environment` — using the same source priority stack that `getProperty()` uses.
3. The resolved string becomes the actual resource path.
4. Spring loads the `.properties` file from that path and registers it as a new `PropertySource`.

The colon in `${key:default}` separates the key from the fallback value; if the key is absent from all sources, the default string is used. Missing without a default throws `IllegalArgumentException`.

```
@PropertySource("classpath:${env}/app.properties")
           ↑                ↑
     literal prefix   substitution token — resolved before load
```

`ignoreResourceNotFound = true` can be combined with path tokens for optional config files that may not exist in all environments.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- Step 1: annotation string -->
  <rect x="10" y="30" width="220" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">@PropertySource("classpath:${env}/app.properties")</text>
  <text x="120" y="64" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">annotation string (literal)</text>

  <!-- Step 2: resolve token -->
  <rect x="270" y="30" width="180" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="50" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">env.getProperty("env") = "prod"</text>
  <text x="360" y="64" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">resolved via PropertySource stack</text>

  <!-- Step 3: resolved path -->
  <rect x="490" y="30" width="200" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="590" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">classpath:prod/app.properties</text>
  <text x="590" y="64" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">actual resource path loaded</text>

  <!-- Arrows -->
  <defs>
    <marker id="a135" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="b135" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="232" y1="50" x2="268" y2="50" stroke="#79c0ff" stroke-width="2" marker-end="url(#a135)"/>
  <line x1="452" y1="50" x2="488" y2="50" stroke="#6db33f" stroke-width="2" marker-end="url(#b135)"/>

  <!-- Bottom note -->
  <rect x="10" y="100" width="680" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Token resolution uses the SAME Environment sources that @Value uses</text>
  <text x="350" y="138" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">System props → env vars → other @PropertySource files registered earlier</text>

  <text x="350" y="182" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Resolved path used to load the file; loaded file becomes a new PropertySource added last</text>
</svg>

The substitution token in the path is resolved against the current environment before the resource is loaded.

## 5. Runnable example

### Level 1 — Basic

One `@PropertySource` path with an `${env:dev}` token; override via system property.

```java
// PropertySourceTokenBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.nio.file.*;

class AppSettings {
    @Value("${db.url}")      String dbUrl;
    @Value("${db.pool:5}")   int poolSize;
    @Value("${log.level:INFO}") String logLevel;

    public void print() {
        System.out.printf("db.url=%s  pool=%d  log=%s%n", dbUrl, poolSize, logLevel);
    }
}

@Configuration
@PropertySource("classpath:${target.env:dev}/settings.properties")
@ComponentScan(basePackageClasses = PropertySourceTokenBasic.class)
class TokenCfg {}

public class PropertySourceTokenBasic {
    public static void main(String[] args) throws Exception {
        // Create both env directories and files on classpath root
        Files.createDirectories(Path.of("dev"));
        Files.createDirectories(Path.of("prod"));
        Files.writeString(Path.of("dev/settings.properties"),
            "db.url=jdbc:h2:mem:dev\ndb.pool=2\nlog.level=DEBUG\n");
        Files.writeString(Path.of("prod/settings.properties"),
            "db.url=jdbc:postgresql://prod-db/app\ndb.pool=20\nlog.level=WARN\n");

        System.out.println("=== No token set → resolves to 'dev' ===");
        var ctx1 = new AnnotationConfigApplicationContext(TokenCfg.class);
        ctx1.getBean(AppSettings.class).print();
        ctx1.close();

        System.out.println("\n=== target.env=prod ===");
        System.setProperty("target.env", "prod");
        var ctx2 = new AnnotationConfigApplicationContext(TokenCfg.class);
        ctx2.getBean(AppSettings.class).print();
        ctx2.close();

        System.clearProperty("target.env");
        Files.deleteIfExists(Path.of("dev/settings.properties"));
        Files.deleteIfExists(Path.of("prod/settings.properties"));
    }
}
```

How to run: `java PropertySourceTokenBasic.java`

Without `target.env`, `${target.env:dev}` resolves to `"dev"` → loads `dev/settings.properties`. With `target.env=prod`, loads `prod/settings.properties`.

### Level 2 — Intermediate

Multiple `@PropertySource` annotations — base config plus an env-specific overlay, both using substitution tokens.

```java
// PropertySourceTokenMulti.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.nio.file.*;

class ServiceConfig {
    @Value("${api.host}")       String apiHost;
    @Value("${api.timeout:30}") int timeout;
    @Value("${feature.dark-mode:false}") boolean darkMode;
    @Value("${metrics.enabled:false}")   boolean metrics;

    public void print() {
        System.out.printf("host=%s timeout=%d dark=%b metrics=%b%n",
            apiHost, timeout, darkMode, metrics);
    }
}

@Configuration
@PropertySource("classpath:config/base.properties")
@PropertySource(
    value = "classpath:config/${deploy.env:local}-overrides.properties",
    ignoreResourceNotFound = true)
@ComponentScan(basePackageClasses = PropertySourceTokenMulti.class)
class MultiTokenCfg {}

public class PropertySourceTokenMulti {
    public static void main(String[] args) throws Exception {
        Files.createDirectories(Path.of("config"));

        // Base config — always loaded
        Files.writeString(Path.of("config/base.properties"),
            "api.host=localhost\napi.timeout=30\nfeature.dark-mode=false\nmetrics.enabled=false\n");

        // Env-specific overlays
        Files.writeString(Path.of("config/staging-overrides.properties"),
            "api.host=staging.api.acme.com\napi.timeout=10\nmetrics.enabled=true\n");
        Files.writeString(Path.of("config/prod-overrides.properties"),
            "api.host=api.acme.com\napi.timeout=5\nfeature.dark-mode=true\nmetrics.enabled=true\n");

        System.out.println("=== local (no overlay file → ignoreResourceNotFound) ===");
        var ctx1 = new AnnotationConfigApplicationContext(MultiTokenCfg.class);
        ctx1.getBean(ServiceConfig.class).print();
        ctx1.close();

        System.out.println("\n=== staging overlay ===");
        System.setProperty("deploy.env", "staging");
        var ctx2 = new AnnotationConfigApplicationContext(MultiTokenCfg.class);
        ctx2.getBean(ServiceConfig.class).print();
        ctx2.close();

        System.out.println("\n=== prod overlay ===");
        System.setProperty("deploy.env", "prod");
        var ctx3 = new AnnotationConfigApplicationContext(MultiTokenCfg.class);
        ctx3.getBean(ServiceConfig.class).print();
        ctx3.close();

        System.clearProperty("deploy.env");
        Files.deleteIfExists(Path.of("config/base.properties"));
        Files.deleteIfExists(Path.of("config/staging-overrides.properties"));
        Files.deleteIfExists(Path.of("config/prod-overrides.properties"));
    }
}
```

How to run: `java PropertySourceTokenMulti.java`

The base file is always loaded. The overlay file is optional (`ignoreResourceNotFound = true`) — if absent, only base values apply. When present, the overlay's values override base values because the overlay `PropertySource` is registered later (but `@Value` pulls from the highest-priority source, which is `systemProperties` first, then the last-added `PropertySource` wins for the same key when added by `@PropertySource`).

### Level 3 — Advanced

Programmatic `PropertySource` pre-seeding before context creation; path token resolved from that pre-seeded source; final source stack inspection.

```java
// PropertySourceTokenAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.nio.file.*;
import java.util.*;

class MultiEnvConfig {
    @Value("${db.url}")          String dbUrl;
    @Value("${cache.type}")      String cacheType;
    @Value("${mq.broker}")       String mqBroker;
    @Value("${region:global}")   String region;

    public void show() {
        System.out.printf("db=%s cache=%s mq=%s region=%s%n", dbUrl, cacheType, mqBroker, region);
    }
}

@Configuration
@PropertySource("classpath:envs/${runtime.env}/infra.properties")
@ComponentScan(basePackageClasses = PropertySourceTokenAdvanced.class)
class AdvTokenCfg {}

public class PropertySourceTokenAdvanced {
    static void run(String label, String env) throws Exception {
        System.out.println("=== " + label + " ===");

        // Create per-env files
        Files.createDirectories(Path.of("envs/" + env));
        Files.writeString(Path.of("envs/" + env + "/infra.properties"), switch (env) {
            case "blue" -> "db.url=jdbc:pg://blue-db/app\ncache.type=redis-cluster\nmq.broker=kafka-blue:9092\nregion=us-east-1\n";
            case "green" -> "db.url=jdbc:pg://green-db/app\ncache.type=redis-sentinel\nmq.broker=kafka-green:9092\nregion=eu-west-1\n";
            default    -> "db.url=jdbc:h2:mem:local\ncache.type=caffeine\nmq.broker=activemq://localhost:61616\n";
        });

        // Pre-seed the runtime.env token into the environment BEFORE the context reads @PropertySource
        var ctx = new AnnotationConfigApplicationContext();
        ctx.getEnvironment().getPropertySources().addFirst(
            new MapPropertySource("bootstrap",
                Map.of("runtime.env", env)));

        ctx.register(AdvTokenCfg.class);
        ctx.refresh();

        ctx.getBean(MultiEnvConfig.class).show();

        // Show the full source stack
        System.out.println("  Source stack:");
        ctx.getEnvironment().getPropertySources().forEach(ps ->
            System.out.println("    [" + ps.getName() + "] " + ps.getClass().getSimpleName()));

        ctx.close();
        // Cleanup
        Files.deleteIfExists(Path.of("envs/" + env + "/infra.properties"));
    }

    public static void main(String[] args) throws Exception {
        run("local", "local");
        run("blue deployment", "blue");
        run("green deployment", "green");
    }
}
```

How to run: `java PropertySourceTokenAdvanced.java`

The `bootstrap` `MapPropertySource` is inserted as the highest-priority source before `ctx.register()`. When `ctx.refresh()` processes `@PropertySource("classpath:envs/${runtime.env}/infra.properties")`, the token `${runtime.env}` resolves to the value from `bootstrap`. The loaded `infra.properties` file becomes a new source in the stack.

## 6. Walkthrough

Execution for Level 3 "blue deployment":

1. **`addFirst("bootstrap", Map.of("runtime.env","blue"))`** — highest-priority source registered.
2. **`ctx.register(AdvTokenCfg.class)`** — class registered but not yet processed.
3. **`ctx.refresh()`** — `ConfigurationClassPostProcessor` runs; encounters `@PropertySource("classpath:envs/${runtime.env}/infra.properties")`.
4. **Token resolution** — `env.getProperty("runtime.env")` → `"blue"` (from `bootstrap`).
5. **Resource load** — `classpath:envs/blue/infra.properties` loaded → registered as a `PropertiesPropertySource("classpath:envs/blue/infra.properties")`.
6. **Bean instantiation** — `MultiEnvConfig` fields injected. `@Value("${db.url}")` → walks sources → found in `infra` source → `"jdbc:pg://blue-db/app"`.
7. **`show()`** → `db=jdbc:pg://blue-db/app cache=redis-cluster mq=kafka-blue:9092 region=us-east-1`.

## 7. Gotchas & takeaways

> The token in `@PropertySource` is resolved at `ctx.refresh()` time when `ConfigurationClassPostProcessor` processes `@Configuration` classes. If you need the token to come from a file that is also loaded via `@PropertySource`, there is a chicken-and-egg problem: you cannot use a token whose value is defined in the same file. Pre-seed bootstrap tokens via system properties or a `MapPropertySource` added before `refresh()`.

> `${key}` without a default (no colon) throws `IllegalArgumentException` at startup if the key is absent. Use `${key:fallback}` to provide a safe default value, especially for optional environment-specific paths.

- Substitution tokens in `@PropertySource` paths use the same resolution logic as `@Value` tokens — the full `Environment` source stack.
- `ignoreResourceNotFound = true` makes the file optional — combine with a fallback default in the token (`${env:local}`) so the path is always syntactically valid even when the file doesn't exist.
- Multiple `@PropertySource` annotations load files in declaration order, each registered with lower priority than the previous. Override order: last wins for the same key when using `@PropertySource` alone (no system properties involved).
- In Spring Boot, this pattern is superseded by profile-specific `application-{profile}.properties` files — but the substitution token mechanism remains useful in plain Spring contexts.
