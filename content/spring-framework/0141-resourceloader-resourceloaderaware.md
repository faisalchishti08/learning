---
card: spring-framework
gi: 141
slug: resourceloader-resourceloaderaware
title: "ResourceLoader & ResourceLoaderAware"
---

## 1. What it is

`ResourceLoader` is the strategy interface for loading `Resource` objects from location strings. It maps a location prefix (`classpath:`, `file:`, `http:`, no-prefix) to the correct `Resource` implementation. `ApplicationContext` implements `ResourceLoader`, so every Spring context is also a resource factory.

`ResourceLoaderAware` is a callback interface: beans that implement it receive the `ResourceLoader` (usually the `ApplicationContext`) injected by the container.

```java
class MyBean implements ResourceLoaderAware {
    private ResourceLoader loader;

    @Override
    public void setResourceLoader(ResourceLoader resourceLoader) {
        this.loader = resourceLoader;
    }

    public void loadConfig() throws Exception {
        Resource r = loader.getResource("classpath:config/app.yaml");
        // use r...
    }
}
```

## 2. Why & when

- **Location-string based loading** — code receives a configurable path string from `@Value` and turns it into a `Resource` without knowing the prefix type.
- **Plugin / extension pattern** — a bean that loads user-provided resource paths (template files, config overrides) without being coupled to `ClassPathResource` or `FileSystemResource`.
- **Testing** — inject a custom `ResourceLoader` that returns mock resources.
- **Framework authoring** — implement `ResourceLoader` to define how your framework resolves resources.

Prefer `@Autowired ResourceLoader` over implementing `ResourceLoaderAware` in modern code — it's cleaner. Use `ResourceLoaderAware` only when you need the loader before `@Autowired` injection runs.

## 3. Core concept

`ResourceLoader` interface:

```
Resource getResource(String location)
ClassLoader getClassLoader()
```

`DefaultResourceLoader` prefix dispatch:

| Prefix | Resolved type |
|---|---|
| `classpath:` | `ClassPathResource` |
| `file:` | `FileSystemResource` |
| `http:` / `https:` | `UrlResource` |
| No prefix | Context-dependent (usually `ClassPathResource` in `DefaultResourceLoader`) |

`DefaultResourceLoader` is the standalone implementation. `ApplicationContext` inherits from it and overrides no-prefix resolution: in an `AbstractApplicationContext`, no-prefix paths resolve relative to the context's working directory or classpath depending on subclass.

`ResourcePatternResolver` extends `ResourceLoader` and adds `getResources(String pattern)` for wildcard patterns — covered in the next tutorial.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- ResourceLoader -->
  <rect x="10" y="30" width="180" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="100" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">&lt;&lt;ResourceLoader&gt;&gt;</text>
  <text x="100" y="68" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getResource(String location)</text>
  <text x="100" y="80" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getClassLoader()</text>

  <!-- DefaultResourceLoader -->
  <rect x="10" y="110" width="180" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">DefaultResourceLoader</text>
  <text x="100" y="142" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">standalone; prefix dispatch</text>

  <!-- ApplicationContext -->
  <rect x="10" y="158" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="177" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ApplicationContext (inherits)</text>

  <!-- Dispatch -->
  <rect x="260" y="20"  width="175" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="347" y="38"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">classpath: → ClassPathResource</text>
  <rect x="260" y="54"  width="175" height="28" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="347" y="72"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">file: → FileSystemResource</text>
  <rect x="260" y="88"  width="175" height="28" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="347" y="106" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">http: → UrlResource</text>
  <rect x="260" y="122" width="175" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="347" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(no prefix) → context-default</text>

  <defs>
    <marker id="a141" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="192" y1="57" x2="257" y2="57" stroke="#6db33f" stroke-width="2" marker-end="url(#a141)"/>

  <text x="350" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ResourceLoader.getResource(location) dispatches on prefix to the correct Resource type</text>
</svg>

`ResourceLoader.getResource()` maps location prefix to `Resource` type; `ApplicationContext` is the default `ResourceLoader` in Spring beans.

## 5. Runnable example

### Level 1 — Basic

`DefaultResourceLoader` standalone prefix dispatch; compare with `ApplicationContext`.

```java
// ResourceLoaderBasic.java
import org.springframework.context.annotation.*;
import org.springframework.core.io.*;
import java.nio.file.*;

public class ResourceLoaderBasic {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("loader-test.txt"), "classpath content");

        // Standalone DefaultResourceLoader
        ResourceLoader loader = new DefaultResourceLoader();

        String[] locations = {
            "classpath:loader-test.txt",
            "file:" + Path.of("loader-test.txt").toAbsolutePath(),
        };

        for (String loc : locations) {
            Resource r = loader.getResource(loc);
            System.out.printf("%-55s → [%s] exists=%b%n",
                loc, r.getClass().getSimpleName(), r.exists());
        }

        // ApplicationContext also implements ResourceLoader
        var ctx = new AnnotationConfigApplicationContext();
        ctx.register(Object.class);
        ctx.refresh();

        ResourceLoader ctxLoader = ctx;  // ApplicationContext IS a ResourceLoader
        Resource fromCtx = ctxLoader.getResource("classpath:loader-test.txt");
        System.out.println("\nFrom ApplicationContext:");
        System.out.println("  " + fromCtx.getClass().getSimpleName() +
            " exists=" + fromCtx.exists());
        System.out.println("  content: " +
            new String(fromCtx.getInputStream().readAllBytes()));

        ctx.close();
        Files.deleteIfExists(Path.of("loader-test.txt"));
    }
}
```

How to run: `java ResourceLoaderBasic.java`

`DefaultResourceLoader.getResource("classpath:...")` returns `ClassPathResource`. `"file:..."` returns `FileSystemResource`. `ApplicationContext` implements `ResourceLoader` and returns the same types.

### Level 2 — Intermediate

`ResourceLoaderAware` injection; `@Autowired ResourceLoader`; configurable path from `@Value`.

```java
// ResourceLoaderAwareDemo.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.core.io.*;
import java.nio.file.*;
import java.util.Properties;

// Option A: ResourceLoaderAware callback interface
class LegacyConfigService implements ResourceLoaderAware {
    private ResourceLoader loader;

    @Override
    public void setResourceLoader(ResourceLoader resourceLoader) {
        this.loader = resourceLoader;
        System.out.println("[LegacyConfigService] received ResourceLoader: " +
            resourceLoader.getClass().getSimpleName());
    }

    public Properties load(String location) throws Exception {
        Resource r = loader.getResource(location);
        var props = new Properties();
        props.load(r.getInputStream());
        return props;
    }
}

// Option B: @Autowired ResourceLoader (preferred in modern code)
class ModernConfigService {
    @Autowired ResourceLoader loader;

    @Value("${config.location:classpath:modern.properties}")
    String configLocation;

    public void printConfig() throws Exception {
        Resource r = loader.getResource(configLocation);
        System.out.println("[ModernConfigService] loading from: " + r.getDescription());
        var props = new Properties();
        props.load(r.getInputStream());
        props.forEach((k, v) -> System.out.println("  " + k + "=" + v));
    }
}

@Configuration
@ComponentScan(basePackageClasses = ResourceLoaderAwareDemo.class)
class LoaderCfg {
    @Bean LegacyConfigService legacyConfigService() { return new LegacyConfigService(); }
}

public class ResourceLoaderAwareDemo {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("legacy.properties"),
            "srv.host=legacy-host\nsrv.port=8080\n");
        Files.writeString(Path.of("modern.properties"),
            "api.timeout=10\napi.retries=3\napi.key=modern-key\n");

        var ctx = new AnnotationConfigApplicationContext(LoaderCfg.class);

        // Option A: ResourceLoaderAware
        var legacy = ctx.getBean(LegacyConfigService.class);
        var legacyProps = legacy.load("classpath:legacy.properties");
        System.out.println("[Legacy] srv.host=" + legacyProps.getProperty("srv.host"));

        // Option B: @Autowired
        var modern = ctx.getBean(ModernConfigService.class);
        modern.printConfig();

        ctx.close();
        Files.deleteIfExists(Path.of("legacy.properties"));
        Files.deleteIfExists(Path.of("modern.properties"));
    }
}
```

How to run: `java ResourceLoaderAwareDemo.java`

`LegacyConfigService` implements `ResourceLoaderAware` — Spring calls `setResourceLoader` during the post-processing phase. `ModernConfigService` uses `@Autowired ResourceLoader`, which is simpler and works everywhere `@Autowired` is supported.

### Level 3 — Advanced

Custom `ResourceLoader` that intercepts and overrides specific locations; protocol handler pattern; integration with `ApplicationContext`.

```java
// ResourceLoaderCustom.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.core.io.*;
import java.util.*;

// A custom ResourceLoader that intercepts "vault:key" locations
class VaultResourceLoader implements ResourceLoader {
    private final ResourceLoader delegate;
    private final Map<String, String> vaultStore;

    VaultResourceLoader(ResourceLoader delegate, Map<String, String> vaultStore) {
        this.delegate   = delegate;
        this.vaultStore = vaultStore;
    }

    @Override
    public Resource getResource(String location) {
        if (location.startsWith("vault:")) {
            String key = location.substring("vault:".length());
            String value = vaultStore.getOrDefault(key, "");
            System.out.println("[VaultLoader] resolved vault:" + key + " → " + value.length() + " chars");
            return new ByteArrayResource(value.getBytes(), "vault:" + key);
        }
        return delegate.getResource(location);
    }

    @Override
    public ClassLoader getClassLoader() { return delegate.getClassLoader(); }
}

class SecretReader {
    @Autowired ApplicationContext ctx;

    public String readSecret(String location) throws Exception {
        // Uses the ApplicationContext as ResourceLoader but can be overridden
        Resource r = ctx.getResource(location);
        return new String(r.getInputStream().readAllBytes()).trim();
    }
}

@Configuration
@ComponentScan(basePackageClasses = ResourceLoaderCustom.class)
class CustomLoaderCfg {}

public class ResourceLoaderCustom {
    public static void main(String[] args) throws Exception {
        // Demonstrate DefaultResourceLoader with custom protocol
        Map<String, String> vault = Map.of(
            "db/password",  "s3cr3t",
            "api/key",      "sk-live-xyz",
            "jwt/secret",   "my-jwt-hmac-key"
        );

        var baseLoader = new DefaultResourceLoader();
        var vaultLoader = new VaultResourceLoader(baseLoader, vault);

        System.out.println("=== Custom VaultResourceLoader ===");
        for (String loc : List.of("vault:db/password", "vault:api/key", "vault:jwt/secret")) {
            Resource r = vaultLoader.getResource(loc);
            System.out.printf("  %-30s → [%s] content=%s%n",
                loc, r.getClass().getSimpleName(),
                new String(r.getInputStream().readAllBytes()));
        }

        // Non-vault locations fall through to default
        java.nio.file.Files.writeString(java.nio.file.Path.of("app.txt"), "classpath-content");
        Resource fallthrough = vaultLoader.getResource("classpath:app.txt");
        System.out.println("  classpath fallthrough: " + fallthrough.getClass().getSimpleName() +
            " exists=" + fallthrough.exists());
        java.nio.file.Files.deleteIfExists(java.nio.file.Path.of("app.txt"));

        // ApplicationContext usage
        System.out.println("\n=== ApplicationContext as ResourceLoader ===");
        var ctx = new AnnotationConfigApplicationContext(CustomLoaderCfg.class);
        var reader = ctx.getBean(SecretReader.class);
        // ApplicationContext doesn't understand vault: — falls through to classpath default
        java.nio.file.Files.writeString(java.nio.file.Path.of("readable.txt"), "from classpath");
        System.out.println("classpath read: " + reader.readSecret("classpath:readable.txt"));
        java.nio.file.Files.deleteIfExists(java.nio.file.Path.of("readable.txt"));
        ctx.close();
    }
}
```

How to run: `java ResourceLoaderCustom.java`

`VaultResourceLoader` wraps `DefaultResourceLoader` as a delegate. It intercepts `vault:` locations and returns `ByteArrayResource` from the vault map. Non-vault locations fall through to the delegate. This is the decorator pattern for extending `ResourceLoader` with custom protocols.

## 6. Walkthrough

Execution for Level 3 `vault:db/password`:

1. **`vaultLoader.getResource("vault:db/password")`** → starts with `"vault:"`.
2. **`key = "db/password"`** → `vaultStore.get("db/password")` → `"s3cr3t"`.
3. **`new ByteArrayResource("s3cr3t".getBytes(), "vault:db/password")`** returned.
4. **`r.getClass().getSimpleName()`** → `"ByteArrayResource"`.
5. **`r.getInputStream().readAllBytes()`** → `"s3cr3t"`.

## 7. Gotchas & takeaways

> Implementing `ResourceLoaderAware` requires the bean to be in a Spring-managed context (a `BeanFactory` that supports the `Aware` callbacks). In plain Java without Spring, the `setResourceLoader` method is never called. Prefer `@Autowired ResourceLoader` which fails loudly at startup if the context doesn't support it.

> `DefaultResourceLoader` without a prefix resolves to `ClassPathResource`. `FileSystemXmlApplicationContext` resolves without-prefix to `FileSystemResource`. The resolution strategy differs by `ApplicationContext` subclass — always use explicit prefixes (`classpath:` or `file:`) in configurable location strings for predictable behavior.

- `ApplicationContext` implements both `ResourceLoader` and `ResourcePatternResolver` — you can inject it directly wherever either interface is needed.
- For bean injection, `@Autowired ResourceLoader` and `@Autowired ApplicationContext` both work — prefer the narrower type to signal intent.
- Custom `ResourceLoader` implementations are useful for testing (returning mock resources) and for supporting proprietary location schemes (e.g., `s3://bucket/key`, `vault:path/to/secret`).
- `ResourceLoader.getClassLoader()` returns the classloader used by the loader — useful when the loader needs to resolve relative classpath entries.
