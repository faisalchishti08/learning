---
card: spring-framework
gi: 126
slug: propertysource
title: "@PropertySource"
---

## 1. What it is

`@PropertySource` adds a `.properties` file (or any `PropertySource` resource) to Spring's `Environment` so that key-value pairs from that file become available via `@Value("${key}")` and `Environment.getProperty("key")`. It is typically placed on a `@Configuration` class.

```java
@Configuration
@PropertySource("classpath:app.properties")
class AppConfig {
    @Autowired Environment env;
    @Bean String greeting() { return env.getProperty("app.greeting"); }
}
```

## 2. Why & when

- **Externalised configuration** — keep environment-specific values (URLs, credentials, timeouts) out of source code in `.properties` files.
- **Multiple environments** — load `app-dev.properties` vs `app-prod.properties` based on an active profile.
- **Library defaults** — a library ships default property values in its JAR; the consuming app can override them by registering a higher-priority `PropertySource`.
- **`@Value` resolution** — `@PropertySource` is the standard way to make `@Value("${...}")` work without Spring Boot's auto-wiring of `application.properties`.

## 3. Core concept

`@PropertySource` attributes:

| Attribute | Default | Effect |
|---|---|---|
| `value` | required | Resource path(s) — `classpath:app.properties` |
| `name` | auto | Name for the `PropertySource` in the `Environment` |
| `encoding` | `""` (platform) | Character encoding of the file |
| `ignoreResourceNotFound` | `false` | If `true`, missing file is silently skipped |
| `factory` | `DefaultPropertySourceFactory` | Custom parser for non-.properties formats |

Multiple `@PropertySource` annotations stack — use `@PropertySources({...})` for an array or just repeat `@PropertySource` (Java 8+ repeatable annotation).

The loaded `PropertySource` is added to the `Environment`'s `MutablePropertySources` — lower priority than system properties and environment variables by default. Override order matters when the same key exists in multiple sources.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- Files -->
  <rect x="10" y="40" width="145" height="115" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="82" y="63" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Files on classpath</text>
  <text x="82" y="83" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">app.properties</text>
  <text x="82" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">db.properties</text>
  <text x="82" y="117" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">mail.properties</text>
  <text x="82" y="137" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">key=value pairs</text>

  <!-- @PropertySource -->
  <rect x="250" y="60" width="200" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="83" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@PropertySource</text>
  <text x="350" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">adds to Environment</text>
  <text x="350" y="117" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">MutablePropertySources</text>

  <!-- Environment -->
  <rect x="545" y="40" width="145" height="115" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="617" y="63" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Environment</text>
  <text x="617" y="83" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">getProperty("key")</text>
  <text x="617" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">→ @Value("${key}")</text>
  <text x="617" y="117" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">→ @ConfigurationProperties</text>
  <text x="617" y="134" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">→ SpEL resolution</text>

  <line x1="157" y1="97" x2="247" y2="97" stroke="#8b949e" stroke-width="2" marker-end="url(#a126)"/>
  <line x1="452" y1="97" x2="542" y2="97" stroke="#6db33f" stroke-width="2" marker-end="url(#b126)"/>
  <defs>
    <marker id="a126" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="b126" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <text x="350" y="180" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Properties file loaded into Environment → resolved by @Value and getProperty()</text>
</svg>

`@PropertySource` loads key-value pairs into the `Environment`; `@Value` and `getProperty()` resolve them at injection time.

## 5. Runnable example

### Level 1 — Basic

Load a single properties file and inject values with `@Value`.

```java
// PropertySourceBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.nio.file.*;

class AppSettings {
    @Value("${app.name}")    String name;
    @Value("${app.version}") String version;
    @Value("${app.debug:false}") boolean debug;  // default false if absent

    public void print() {
        System.out.println("App: " + name + " v" + version + " debug=" + debug);
    }
}

@Configuration
@PropertySource("classpath:app-basic.properties")
@ComponentScan(basePackageClasses = PropertySourceBasic.class)
class BasicCfg {}

public class PropertySourceBasic {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("app-basic.properties"),
            "app.name=MyShop\napp.version=1.0\napp.debug=true\n");

        var ctx = new AnnotationConfigApplicationContext(BasicCfg.class);
        ctx.getBean(AppSettings.class).print();
        ctx.close();
        Files.deleteIfExists(Path.of("app-basic.properties"));
    }
}
```

How to run: `java PropertySourceBasic.java`

`@PropertySource("classpath:app-basic.properties")` loads the file into the `Environment`. `@Value("${app.name}")` resolves to `"MyShop"`. The `${app.debug:false}` default fires if the key is absent.

### Level 2 — Intermediate

Multiple `@PropertySource` files; read via `Environment` and inject into a service.

```java
// PropertySourceMultiple.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import java.nio.file.*;

class DbConfig {
    @Value("${db.url}")      String url;
    @Value("${db.user}")     String user;
    @Value("${db.password}") String password;
    @Value("${db.pool.size:5}") int poolSize;

    public String summary() {
        return url + " user=" + user + " pool=" + poolSize;
    }
}

class MailConfig {
    @Value("${mail.host}")   String host;
    @Value("${mail.port:25}") int port;
    @Value("${mail.from}")   String from;

    public String summary() { return host + ":" + port + " from=" + from; }
}

class ServiceConfig {
    @Value("${service.name}")    String name;
    @Value("${service.timeout}") int timeout;

    @Autowired private DbConfig   db;
    @Autowired private MailConfig mail;

    public void status() {
        System.out.println("Service: " + name + " timeout=" + timeout + "s");
        System.out.println("DB:   " + db.summary());
        System.out.println("Mail: " + mail.summary());
    }
}

@Configuration
@PropertySource("classpath:db.properties")
@PropertySource("classpath:mail.properties")
@PropertySource("classpath:service.properties")
@ComponentScan(basePackageClasses = PropertySourceMultiple.class)
class MultiPropCfg {}

public class PropertySourceMultiple {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("db.properties"),
            "db.url=jdbc:postgresql://localhost/shop\ndb.user=shop\ndb.password=secret\ndb.pool.size=10\n");
        Files.writeString(Path.of("mail.properties"),
            "mail.host=smtp.acme.com\nmail.port=587\nmail.from=noreply@acme.com\n");
        Files.writeString(Path.of("service.properties"),
            "service.name=ShopService\nservice.timeout=30\n");

        var ctx = new AnnotationConfigApplicationContext(MultiPropCfg.class);
        ctx.getBean(ServiceConfig.class).status();
        ctx.close();

        Files.deleteIfExists(Path.of("db.properties"));
        Files.deleteIfExists(Path.of("mail.properties"));
        Files.deleteIfExists(Path.of("service.properties"));
    }
}
```

How to run: `java PropertySourceMultiple.java`

Three separate `@PropertySource` annotations load three files. Each `@Value` resolves from whichever file contains the key. If the same key appeared in multiple files, the last-loaded file would win.

### Level 3 — Advanced

`ignoreResourceNotFound = true` for optional overrides, plus programmatic `Environment` access and a custom `PropertySourceFactory` for YAML-style loading.

```java
// PropertySourceAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import org.springframework.core.io.*;
import org.springframework.core.io.support.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

// Custom PropertySourceFactory: parses simple key=value with support for "!override" prefix
class OverridablePropertySourceFactory implements PropertySourceFactory {
    @Override
    public org.springframework.core.env.PropertySource<?> createPropertySource(
            String name, EncodedResource resource) throws IOException {
        Properties props = new Properties();
        props.load(resource.getInputStream());
        // Strip any leading "!override " from values (demo custom parsing)
        props.replaceAll((k, v) -> v.toString().startsWith("!override ")
            ? v.toString().substring(10) : v);
        return new PropertiesPropertySource(name != null ? name : resource.toString(), props);
    }
}

class FeatureFlags {
    @Value("${feature.search:off}")         String search;
    @Value("${feature.recommendations:off}") String recs;
    @Value("${feature.darkMode:off}")        String darkMode;

    public void print() {
        System.out.println("search=" + search + " recs=" + recs + " darkMode=" + darkMode);
    }
}

class SystemInfo {
    @Autowired Environment env;

    public void inspect() {
        System.out.println("Active profiles: " +
            Arrays.toString(env.getActiveProfiles()));
        System.out.println("feature.search = " +
            env.getProperty("feature.search", "not set"));

        // Walk all property sources in order
        ((AbstractEnvironment) env).getPropertySources().forEach(ps ->
            System.out.println("  PropertySource: " + ps.getName()));
    }
}

@Configuration
@PropertySource("classpath:features-base.properties")
@PropertySource(
    value = "classpath:features-override.properties",
    ignoreResourceNotFound = true,           // optional override file
    factory = OverridablePropertySourceFactory.class
)
@ComponentScan(basePackageClasses = PropertySourceAdvanced.class)
class FeatCfg {}

public class PropertySourceAdvanced {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("features-base.properties"),
            "feature.search=on\nfeature.recommendations=off\nfeature.darkMode=off\n");
        // Write optional override
        Files.writeString(Path.of("features-override.properties"),
            "feature.recommendations=!override on\nfeature.darkMode=!override on\n");

        System.out.println("=== With override file ===");
        var ctx1 = new AnnotationConfigApplicationContext(FeatCfg.class);
        ctx1.getBean(FeatureFlags.class).print();
        ctx1.getBean(SystemInfo.class).inspect();
        ctx1.close();

        // Remove override — ignoreResourceNotFound keeps context alive
        Files.deleteIfExists(Path.of("features-override.properties"));
        System.out.println("\n=== Without override file (ignored) ===");
        var ctx2 = new AnnotationConfigApplicationContext(FeatCfg.class);
        ctx2.getBean(FeatureFlags.class).print();
        ctx2.close();

        Files.deleteIfExists(Path.of("features-base.properties"));
    }
}
```

How to run: `java PropertySourceAdvanced.java`

The custom `OverridablePropertySourceFactory` strips a leading `!override ` tag. `ignoreResourceNotFound = true` means that if the override file doesn't exist, the context starts normally with base values only.

## 6. Walkthrough

Execution for Level 3 "with override file":

1. **`FeatCfg` processed** — `@PropertySource("classpath:features-base.properties")` loaded first. `feature.search=on`, `feature.recommendations=off`, `feature.darkMode=off` added to `Environment`.
2. **Second `@PropertySource` processed** — `OverridablePropertySourceFactory.createPropertySource()` called. Loads `features-override.properties`, strips `!override ` prefix → `feature.recommendations=on`, `feature.darkMode=on`.
3. **Override source added to `Environment`** — since it was added after the base, when resolving a key Spring searches sources in reverse insertion order — the override source is checked first and wins for `feature.recommendations` and `feature.darkMode`.
4. **`FeatureFlags` injected** — `@Value("${feature.search}")` → `"on"` (from base), `${feature.recommendations}` → `"on"` (from override), `${feature.darkMode}` → `"on"` (from override).
5. **`SystemInfo.inspect()`** — prints active profiles (none) and all property source names.

Expected output (second run, no override):
```
=== Without override file (ignored) ===
search=on recs=off darkMode=off
```

## 7. Gotchas & takeaways

> `@PropertySource` adds properties at **lower priority** than JVM system properties (`-D`) and OS environment variables. If `APP_NAME` is set in the environment, it will override `app.name` from your properties file — which is usually the desired behaviour in containerised deployments, but surprises developers debugging locally.

> Loaded property files do NOT automatically enable `${...}` resolution for `@Value` — you also need a `PropertySourcesPlaceholderConfigurer` bean. In XML-configured apps you declare it explicitly. In `@Configuration` apps, `AnnotationConfigApplicationContext` registers it automatically. In older contexts, you may need to add it manually.

- `@PropertySource` is repeatable in Java 8+: you can stack it multiple times on the same class without `@PropertySources`.
- Files are loaded in declaration order. Later sources are searched first (LIFO priority) — so the last `@PropertySource` wins for duplicate keys.
- `ignoreResourceNotFound = true` is essential for optional override files in multi-environment setups.
- Custom `PropertySourceFactory` lets you parse YAML, JSON, or other formats — a common use case for YAML properties files in non-Boot Spring apps.
