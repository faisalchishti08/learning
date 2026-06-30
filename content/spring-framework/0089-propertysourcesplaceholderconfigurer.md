---
card: spring-framework
gi: 89
slug: propertysourcesplaceholderconfigurer
title: PropertySourcesPlaceholderConfigurer
---

## 1. What it is

`PropertySourcesPlaceholderConfigurer` (PSPC) is a built-in `BeanFactoryPostProcessor` that resolves **`${...}` property expressions** in bean definitions and `@Value` annotations by reading values from property sources (`.properties` files, system properties, environment variables).

Write `${db.url}` anywhere in your Spring config and PSPC replaces it with the actual value at startup — before any bean is instantiated.

## 2. Why & when

Hard-coding environment-specific values (database URLs, ports, API keys) into Java source files is brittle: you need a different build for dev, staging, and production. PSPC separates **configuration** from **code**:

- Keep secrets in `.properties` files or environment variables outside the JAR.
- Reference them via `${key}` — PSPC patches the bean definitions with real values at startup.
- Use `${key:defaultValue}` syntax for safe fallbacks when a key is missing.

In Spring Boot, `@ConfigurationProperties` and auto-configuration do most of this for you; in plain Spring, PSPC is the standard mechanism.

## 3. Core concept

PSPC extends `PlaceholderConfigurerSupport` and implements `BeanFactoryPostProcessor`. Its resolution algorithm:

1. Collect all registered `PropertySource`s in order (file sources, system properties, env vars).
2. Iterate every `BeanDefinition` in the factory.
3. For each string value containing `${...}`, look up the key in the property sources chain.
4. Replace the `${...}` token with the resolved value (or the default after the `:` if present).
5. Throw `IllegalArgumentException` if no value and no default.

The chain is searched in registration order — the first source that has the key wins.

## 4. Diagram

<svg viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="30" width="160" height="44" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">app.properties</text>
  <text x="90" y="68" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">db.url=jdbc:h2:mem</text>

  <rect x="10" y="90" width="160" height="44" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="115" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">System.properties</text>
  <text x="90" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">java.version, etc.</text>

  <rect x="10" y="150" width="160" height="44" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="175" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Env Variables</text>
  <text x="90" y="188" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">DB_URL, PORT, …</text>

  <rect x="265" y="90" width="175" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="352" y="114" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">PropertySources</text>
  <text x="352" y="130" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">PlaceholderConfigurer</text>

  <rect x="530" y="90" width="155" height="54" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="607" y="114" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">BeanDefinitions</text>
  <text x="607" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">${db.url} → jdbc:h2:mem</text>

  <line x1="172" y1="52" x2="263" y2="107" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a89)"/>
  <line x1="172" y1="112" x2="263" y2="117" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a89)"/>
  <line x1="172" y1="172" x2="263" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a89)"/>
  <line x1="442" y1="117" x2="527" y2="117" stroke="#79c0ff" stroke-width="2" marker-end="url(#b89)"/>
  <defs>
    <marker id="a89" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b89" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="220" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">PSPC merges all sources then rewrites every ${…} token in bean definitions</text>
</svg>

PSPC merges property sources and rewrites `${...}` tokens before any bean is instantiated.

## 5. Runnable example

### Level 1 — Basic

Resolve a single `${app.greeting}` property expression from a `.properties` file using PSPC.

```java
// PspcBasic.java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.stereotype.Component;
import java.util.Properties;

@Component
class Greeter {
    @Value("${app.greeting}")
    private String greeting;

    public void greet() { System.out.println(greeting); }
}

@Configuration
@ComponentScan
class BasicCfg {
    @Bean
    public static PropertySourcesPlaceholderConfigurer pspc() {
        var p = new PropertySourcesPlaceholderConfigurer();
        var props = new Properties();
        props.setProperty("app.greeting", "Hello from properties!");
        p.setProperties(props);
        return p;
    }
}

public class PspcBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(BasicCfg.class);
        ctx.getBean(Greeter.class).greet();
        ctx.close();
    }
}
```

How to run: `java PspcBasic.java`

`@Value("${app.greeting}")` is a property token expression; PSPC resolves it from the `Properties` object to `"Hello from properties!"` before `Greeter` is even constructed.

### Level 2 — Intermediate

Load values from an external `.properties` file and use default values for missing keys.

```java
// PspcFile.java — create src/app.properties alongside this file
// app.properties contents:
//   db.url=jdbc:h2:mem:testdb
//   db.timeout=5000

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

@Component
class DataSourceConfig {
    @Value("${db.url}")           private String url;
    @Value("${db.timeout:3000}")  private int timeout;   // default 3000 if missing
    @Value("${db.pool:10}")       private int poolSize;  // not in file — uses default

    public void print() {
        System.out.println("url     = " + url);
        System.out.println("timeout = " + timeout);
        System.out.println("pool    = " + poolSize);
    }
}

@Configuration
@ComponentScan
class FileCfg {
    @Bean
    public static PropertySourcesPlaceholderConfigurer pspc() {
        var p = new PropertySourcesPlaceholderConfigurer();
        p.setLocation(new ClassPathResource("app.properties"));
        p.setIgnoreUnresolvablePlaceholders(false); // fail fast on missing keys without defaults
        return p;
    }
}

public class PspcFile {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(FileCfg.class);
        ctx.getBean(DataSourceConfig.class).print();
        ctx.close();
    }
}
```

How to run: place `app.properties` on the classpath (same directory as the `.java` file when using `java PspcFile.java`), then run `java PspcFile.java`

`${db.timeout:3000}` uses the value from the file (`5000`). `${db.pool:10}` falls back to `10` because the key is absent. This is the default/fallback pattern used in every Spring application.

### Level 3 — Advanced

Layer multiple property sources (file → system properties → environment variables) so each environment can override values without touching code.

```java
// PspcLayered.java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.core.env.MutablePropertySources;
import org.springframework.core.env.PropertiesPropertySource;
import org.springframework.core.env.SystemEnvironmentPropertySource;
import org.springframework.stereotype.Component;
import java.util.Map;
import java.util.Properties;

@Component
class AppSettings {
    @Value("${server.port:8080}")  private int port;
    @Value("${server.host:localhost}") private String host;
    @Value("${server.env:development}") private String env;

    public void print() {
        System.out.printf("Running %s at %s:%d%n", env, host, port);
    }
}

@Configuration
@ComponentScan
class LayeredCfg {
    @Bean
    public static PropertySourcesPlaceholderConfigurer pspc() {
        var p = new PropertySourcesPlaceholderConfigurer();

        // Source 1 — defaults baked into the app
        var defaults = new Properties();
        defaults.setProperty("server.port", "8080");
        defaults.setProperty("server.host", "localhost");
        defaults.setProperty("server.env", "development");

        // Source 2 — simulate env-specific overrides (e.g., CI sets SERVER_PORT)
        // Spring's PropertySourcesPlaceholderConfigurer applies environment + system
        // properties automatically; here we manually layer an extra source.
        var sources = new MutablePropertySources();
        // Highest priority: any real system env vars (SERVER_PORT, SERVER_HOST, etc.)
        sources.addFirst(new SystemEnvironmentPropertySource("sysenv", System.getenv()));
        // Lower priority: file defaults
        sources.addLast(new PropertiesPropertySource("defaults", defaults));

        p.setPropertySources(sources);
        return p;
    }
}

public class PspcLayered {
    public static void main(String[] args) {
        // Try: SERVER_PORT=9090 java PspcLayered.java  — overrides port via env var
        var ctx = new AnnotationConfigApplicationContext(LayeredCfg.class);
        ctx.getBean(AppSettings.class).print();
        ctx.close();
    }
}
```

How to run: `java PspcLayered.java` (default output); or `SERVER_PORT=9090 java PspcLayered.java` to see the env-var override win.

Sources are searched in registration order: `sysenv` first (highest priority), then `defaults`. Setting `SERVER_PORT=9090` in the environment makes `${server.port}` resolve to `9090` instead of `8080` — zero code changes needed between environments.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **`AnnotationConfigApplicationContext` created** — Spring scans `LayeredCfg` and registers `AppSettings` and `pspc` as `BeanDefinition`s.
2. **PSPC instantiated early** — Spring sees a `static @Bean` returning a `BeanFactoryPostProcessor`. It creates `LayeredCfg.pspc()` before any other beans.
3. **`setPropertySources` called in `pspc()`** — a `MutablePropertySources` is built with `sysenv` at index 0 (first = highest priority) and `defaults` at index 1. The actual `System.getenv()` map is wrapped in `SystemEnvironmentPropertySource`, which normalises keys (`SERVER_PORT` → `server.port`) automatically.
4. **`postProcessBeanFactory` fires** (inherited from `PlaceholderConfigurerSupport`) — PSPC iterates all bean definitions. It finds `AppSettings`'s `BeanDefinition` whose properties reference `${server.port:8080}`.
5. **Property token resolution** — for `${server.port:8080}` it checks `sysenv` first. If `SERVER_PORT=9090` is set, the environment source returns `"9090"` and iteration stops. If not set, it falls through to `defaults` which returns `"8080"`. The `:8080` default is only used if neither source has the key.
6. **Bean definitions rewritten** — the string `"${server.port:8080}"` in `AppSettings`'s definition is replaced with the resolved value `"9090"` (or `"8080"`). Same for `host` and `env`.
7. **`AppSettings` instantiated** — the `@Value` fields are injected with the now-resolved strings. No unresolved `${...}` tokens remain.
8. **`print()` called** — outputs `Running development at localhost:9090`.

```
Running development at localhost:9090
```

The whole point: environment-specific config flows in via external sources; code never changes.

## 7. Gotchas & takeaways

> Declare PSPC as a **`static @Bean`**. If it's an instance method, Spring creates the `@Configuration` class first, which may try to evaluate `@Value` annotations before PSPC has run — and your `${...}` expressions won't be resolved.

> If you have multiple `PropertySourcesPlaceholderConfigurer` beans (common in large projects), set `setIgnoreUnresolvablePlaceholders(true)` on all but one, or they conflict trying to resolve each other's property tokens.

- `${key}` throws if the key is absent; `${key:default}` is safe.
- Source priority is first-registered first. Put highest-priority sources (env vars, secrets) at `addFirst`.
- Spring Boot's `@PropertySource` and `application.properties` use PSPC under the hood — you rarely configure it manually in Boot.
- PSPC resolves values at startup time — it is **not** dynamic; values don't change after the context starts.
- For type conversion beyond `String`, use `@ConfigurationProperties` (Boot) or Spring's `ConversionService`.
