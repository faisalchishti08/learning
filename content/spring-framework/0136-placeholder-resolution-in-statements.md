---
card: spring-framework
gi: 136
slug: placeholder-resolution-in-statements
title: "Placeholder resolution in statements"
---

## 1. What it is

`PropertySourcesPlaceholderConfigurer` (PSPC) processes `${key}` substitution expressions embedded in `@Value` annotations, XML `<property value="${key}"/>` declarations, and `@PropertySource` path strings. It replaces each `${key:default}` token with the resolved value from the `Environment`'s `PropertySource` stack before the bean is instantiated.

```java
@Value("${server.port:8080}") int port;
@Value("${app.name}-${app.version}") String fullName;
```

## 2. Why & when

- **Externalized config** — move environment-specific values out of code into `.properties` files or environment variables.
- **Default values** — `${key:fallback}` prevents startup failure when a key is absent.
- **Composed tokens** — `${a}-${b}` builds derived strings from multiple keys.
- **XML migration** — XML beans using `${...}` property references continue working after moving to Java config.

PSPC is the bean post-processor that makes `@Value` work with `PropertySource`s in standalone Spring contexts. Spring Boot auto-configures it; in plain Spring it must be declared explicitly (or use `@PropertySource` which triggers it automatically).

## 3. Core concept

How PSPC resolves a `${key:default}` token:

1. Receives the raw string `"${server.port:8080}"`.
2. Extracts key `"server.port"` and default `"8080"`.
3. Calls `env.getProperty("server.port")` — walks the source stack.
4. Returns the first non-null value; uses `"8080"` if all sources return null.
5. Replaces the token with the resolved string value.
6. Target field's type conversion happens after resolution: `"8080"` → `int 8080`.

Token forms:

| Form | Behavior |
|---|---|
| `${key}` | Required; `IllegalArgumentException` if absent |
| `${key:default}` | Optional; fallback to `"default"` if absent |
| `${a}-${b}` | Multiple tokens in one string |
| `${outer.${inner}}` | Nested resolution (inner resolved first) |

`PropertySourcesPlaceholderConfigurer` implements `BeanFactoryPostProcessor` — it runs before any bean is instantiated.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- Source stack -->
  <rect x="10" y="30" width="155" height="25" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="87" y="47" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">systemProperties (-D)</text>

  <rect x="10" y="60" width="155" height="25" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="87" y="77" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">systemEnvironment</text>

  <rect x="10" y="90" width="155" height="25" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="87" y="107" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">@PropertySource files</text>

  <text x="87" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">PropertySource stack</text>

  <!-- PSPC -->
  <rect x="210" y="65" width="195" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="307" y="88" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">PSPC</text>
  <text x="307" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BeanFactoryPostProcessor</text>
  <text x="307" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">resolves ${key:default}</text>

  <!-- Resolved value -->
  <rect x="460" y="75" width="170" height="45" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="97" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">injected value</text>
  <text x="545" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">type-converted for @Value</text>

  <defs>
    <marker id="a136" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b136" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <line x1="167" y1="95" x2="207" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#a136)"/>
  <line x1="407" y1="95" x2="457" y2="95" stroke="#79c0ff" stroke-width="2" marker-end="url(#b136)"/>
  <text x="350" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">PSPC runs before bean instantiation — resolves all ${...} tokens using the Environment source stack</text>
</svg>

`PropertySourcesPlaceholderConfigurer` processes `${...}` tokens against the full source stack before beans are created.

## 5. Runnable example

### Level 1 — Basic

Simple `@Value` tokens with and without defaults.

```java
// PlaceholderBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.nio.file.*;

class AppServer {
    @Value("${server.host:localhost}") String host;
    @Value("${server.port:8080}")      int port;
    @Value("${server.debug:false}")    boolean debug;

    public void info() {
        System.out.printf("http://%s:%d (debug=%b)%n", host, port, debug);
    }
}

@Configuration
@PropertySource("classpath:server.properties")
@ComponentScan(basePackageClasses = PlaceholderBasic.class)
class ServerCfg {}

public class PlaceholderBasic {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("server.properties"),
            "server.host=myapp.local\nserver.port=9090\n");
        // server.debug absent → uses default

        var ctx = new AnnotationConfigApplicationContext(ServerCfg.class);
        ctx.getBean(AppServer.class).info();
        ctx.close();

        // Override port via system property
        System.out.println("\n--- system property override ---");
        System.setProperty("server.port", "443");
        var ctx2 = new AnnotationConfigApplicationContext(ServerCfg.class);
        ctx2.getBean(AppServer.class).info();
        ctx2.close();

        System.clearProperty("server.port");
        Files.deleteIfExists(Path.of("server.properties"));
    }
}
```

How to run: `java PlaceholderBasic.java`

`server.host` and `server.port` come from the properties file. `server.debug` uses the `:false` default because it's absent from all sources. The second run shows the system property overriding the file value for `server.port`.

### Level 2 — Intermediate

Composed tokens, nested resolution, and list injection.

```java
// PlaceholderComposed.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.nio.file.*;
import java.util.*;

class ApiClientConfig {
    @Value("${api.scheme}://${api.host}:${api.port}/${api.path}") String baseUrl;
    @Value("${api.timeout.${api.env:dev}}") int timeout;  // nested: resolves inner first
    @Value("${api.tags:tagA,tagB}")        List<String> tags;
    @Value("${api.retry.max:3}")           int maxRetry;

    public void print() {
        System.out.println("baseUrl=" + baseUrl + " timeout=" + timeout +
            "s tags=" + tags + " maxRetry=" + maxRetry);
    }
}

@Configuration
@PropertySource("classpath:api.properties")
@ComponentScan(basePackageClasses = PlaceholderComposed.class)
class ApiCfg {}

public class PlaceholderComposed {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("api.properties"),
            "api.scheme=https\n" +
            "api.host=api.acme.com\n" +
            "api.port=443\n" +
            "api.path=v2\n" +
            "api.env=prod\n" +
            "api.timeout.dev=30\n" +
            "api.timeout.prod=5\n" +
            "api.tags=orders,payments,inventory\n");

        var ctx = new AnnotationConfigApplicationContext(ApiCfg.class);
        ctx.getBean(ApiClientConfig.class).print();
        ctx.close();

        // Switch env to dev
        System.out.println("\n--- dev env ---");
        System.setProperty("api.env", "dev");
        var ctx2 = new AnnotationConfigApplicationContext(ApiCfg.class);
        ctx2.getBean(ApiClientConfig.class).print();  // timeout uses dev value
        ctx2.close();
        System.clearProperty("api.env");
        Files.deleteIfExists(Path.of("api.properties"));
    }
}
```

How to run: `java PlaceholderComposed.java`

`${api.scheme}://${api.host}:${api.port}/${api.path}` composes four tokens into one URL. `${api.timeout.${api.env:dev}}` resolves inner `${api.env}` first (`"prod"`) then outer `api.timeout.prod`. `List<String>` auto-splits the comma-separated `api.tags` value.

### Level 3 — Advanced

Strict vs lenient resolver; custom `PropertySourcesPlaceholderConfigurer` with `ignoreUnresolvablePlaceholders`; multi-file resolution.

```java
// PlaceholderAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import java.nio.file.*;

class ServiceCfg {
    @Value("${service.name}")          String name;
    @Value("${service.region:global}") String region;
    @Value("${service.secret:MISSING}") String secret;  // intentionally missing in main file
    @Value("${build.version:0.0.0}")   String version;

    public void show() {
        System.out.printf("name=%s region=%s secret=%s version=%s%n",
            name, region, secret, version);
    }
}

@Configuration
@PropertySource("classpath:svc-base.properties")
@PropertySource(value = "classpath:svc-secrets.properties", ignoreResourceNotFound = true)
@ComponentScan(basePackageClasses = PlaceholderAdvanced.class)
class SvcCfg {
    @Bean
    public static PropertySourcesPlaceholderConfigurer pspc() {
        var cfg = new PropertySourcesPlaceholderConfigurer();
        cfg.setIgnoreUnresolvablePlaceholders(false); // strict — fail if key truly absent and no default
        return cfg;
    }
}

public class PlaceholderAdvanced {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("svc-base.properties"),
            "service.name=PaymentService\nservice.region=eu-west-1\nbuild.version=2.4.1\n");

        System.out.println("=== Without secrets file ===");
        var ctx1 = new AnnotationConfigApplicationContext(SvcCfg.class);
        ctx1.getBean(ServiceCfg.class).show();  // service.secret uses :MISSING default
        ctx1.close();

        System.out.println("\n=== With secrets file ===");
        Files.writeString(Path.of("svc-secrets.properties"),
            "service.secret=sk-live-abc123\n");
        var ctx2 = new AnnotationConfigApplicationContext(SvcCfg.class);
        ctx2.getBean(ServiceCfg.class).show();  // service.secret from secrets file
        ctx2.close();

        Files.deleteIfExists(Path.of("svc-base.properties"));
        Files.deleteIfExists(Path.of("svc-secrets.properties"));
    }
}
```

How to run: `java PlaceholderAdvanced.java`

Without the secrets file: `service.secret` falls back to `"MISSING"` (the `:MISSING` default). With the secrets file present: the value is resolved from the file. The explicit `PropertySourcesPlaceholderConfigurer` bean with `setIgnoreUnresolvablePlaceholders(false)` enforces strict resolution — any key without a default and absent from all sources throws at startup.

## 6. Walkthrough

Execution for Level 3 "With secrets file":

1. **`svc-base.properties`** registered as a source (via `@PropertySource`).
2. **`svc-secrets.properties`** registered as a lower-priority source (via second `@PropertySource`, `ignoreResourceNotFound = true` — file exists so it loads).
3. **`SvcCfg` `@Bean pspc()`** — `PropertySourcesPlaceholderConfigurer` registered as `BeanFactoryPostProcessor`.
4. **`ctx.refresh()` → PSPC runs** before bean instantiation. Processes `ServiceCfg` field metadata:
   - `${service.name}` → `systemProperties` (absent) → `svc-base` → `"PaymentService"`.
   - `${service.region:eu-west-1}` → not in system → `"eu-west-1"` from `svc-base`.
   - `${service.secret:MISSING}` → not in system → not in `svc-base` → `"sk-live-abc123"` from `svc-secrets`.
   - `${build.version:0.0.0}` → `"2.4.1"` from `svc-base`.
5. **`ServiceCfg` bean instantiated** with resolved values.
6. **`show()`** → `name=PaymentService region=eu-west-1 secret=sk-live-abc123 version=2.4.1`.

## 7. Gotchas & takeaways

> In a plain Spring context, `@Value("${key}")` resolution ONLY works if a `PropertySourcesPlaceholderConfigurer` is registered as a bean. `@PropertySource` on a `@Configuration` class that also has `@Value` fields causes PSPC to be auto-registered. Without it, unresolved tokens appear literally as `"${key}"` strings — a silent failure.

> `${key}` without a colon default throws `IllegalArgumentException` at context startup if the key is absent — not at the `@Value` call site. This fails fast, which is intentional, but can surprise when optional config is expected.

- Declare `PropertySourcesPlaceholderConfigurer` as a `static @Bean` (not instance) so it can process other beans in the same `@Configuration` class.
- `${...}` tokens in `@Value` strings are resolved by PSPC; `#{...}` expressions are resolved by Spring Expression Language (SpEL) — a different processor.
- Nested resolution `${outer.${inner}}` resolves the inner token first; avoid deep nesting as it reduces readability.
- Comma-separated `@Value("${keys}") List<String>` automatically splits on commas — useful for multi-value properties like enabled features or allowed hosts.
