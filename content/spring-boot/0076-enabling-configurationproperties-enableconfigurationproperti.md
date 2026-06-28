---
card: spring-boot
gi: 76
slug: enabling-configurationproperties-enableconfigurationproperti
title: "Enabling @ConfigurationProperties (@EnableConfigurationProperties / @ConfigurationPropertiesScan)"
---

## 1. What it is

Annotating a class with `@ConfigurationProperties` does not automatically register it as a Spring bean. The annotation only marks the class as a binding candidate — it still needs to be picked up by the application context. Spring Boot provides three ways to do that:

1. **`@Component` on the class itself** — the simplest approach; Spring's component scan finds it.
2. **`@EnableConfigurationProperties(MyProps.class)`** on a `@Configuration` class — explicitly registers named classes without touching them.
3. **`@ConfigurationPropertiesScan`** — tells Spring Boot to search a package for all `@ConfigurationProperties` classes and register them automatically.

Choosing the right registration strategy is a design decision: `@Component` couples the class to Spring, `@EnableConfigurationProperties` is explicit and testable, and `@ConfigurationPropertiesScan` is convenient for applications with many properties classes.

In one sentence: **Spring Boot needs an extra registration step to turn a `@ConfigurationProperties`-annotated class into a live bean — three strategies exist, each with different trade-offs.**

## 2. Why & when

A `@ConfigurationProperties` class without registration is inert. This matters for three scenarios:

- **Library authors** should never put `@Component` on internal classes because that forces library users to accept those beans into their own component scan. `@EnableConfigurationProperties` lets the library's auto-configuration register the class explicitly.
- **Constructor-binding classes and records** cannot be annotated with `@Component` and also be processed by the constructor-binding mechanism in all Spring Boot versions. Registering via `@EnableConfigurationProperties` or `@ConfigurationPropertiesScan` avoids the conflict.
- **Large applications** with many configuration classes benefit from `@ConfigurationPropertiesScan` — it replaces a long list of `@EnableConfigurationProperties(A.class, B.class, C.class, ...)` entries with a single scan declaration.

## 3. Core concept

**Strategy 1: `@Component`**

Placing `@Component` (or a stereotype such as `@Service`) directly on the `@ConfigurationProperties` class makes it eligible for component scanning. Spring Boot's `@SpringBootApplication` implicitly includes `@ComponentScan` rooted at the application's package, so any class in that package tree is picked up.

```
@Component               ← Spring scans, registers as bean
@ConfigurationProperties(prefix = "app")
public class AppProps { ... }
```

Trade-off: the class now depends on Spring (the `@Component` import) and must live in the component-scan path. It cannot be easily used outside a Spring context.

**Strategy 2: `@EnableConfigurationProperties`**

Placed on any `@Configuration` class, this annotation takes an array of `@ConfigurationProperties` classes and registers each as a bean named `<prefix>-<fully-qualified-class-name>`. The configuration properties class itself needs no Spring annotations.

```
@Configuration
@EnableConfigurationProperties({ AppProps.class, DbProps.class })
public class AppConfig { }
```

This is the **idiomatic approach for library auto-configuration** because the configuration class stays a plain POJO and control stays with the `@Configuration` class.

**Strategy 3: `@ConfigurationPropertiesScan`**

Introduced in Spring Boot 2.2, this annotation (placed on the main class or any `@Configuration` class) triggers a classpath scan for all `@ConfigurationProperties` classes within the specified base packages. Without a `basePackages` argument it defaults to the package of the annotated class.

```
@SpringBootApplication
@ConfigurationPropertiesScan("com.example.config")
public class App { ... }
```

Every `@ConfigurationProperties` class found in `com.example.config` is registered automatically without any individual declaration.

**How they differ from component scan**

`@ConfigurationPropertiesScan` specifically registers classes via `ConfigurationPropertiesBeanRegistrar` (not the general `BeanDefinitionRegistry`). This means the resulting beans get special metadata (prefix, binding type) that the binder uses, and validation is triggered automatically.

## 4. Diagram

<svg viewBox="0 0 700 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three strategies for registering @ConfigurationProperties classes as Spring beans">

  <!-- Central bean context box -->
  <rect x="270" y="120" width="165" height="80" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="352" y="152" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Context</text>
  <text x="352" y="170" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">registered bean</text>
  <text x="352" y="186" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(ready to inject)</text>

  <!-- Strategy 1: @Component -->
  <rect x="20" y="20" width="200" height="80" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="46" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Strategy 1</text>
  <text x="120" y="64" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">@Component</text>
  <text x="120" y="82" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">on the props class itself</text>
  <line x1="220" y1="60" x2="268" y2="140" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#d1)"/>

  <!-- Strategy 2: @EnableConfigurationProperties -->
  <rect x="20" y="160" width="200" height="90" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="185" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Strategy 2</text>
  <text x="120" y="203" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">@EnableConfigurationProperties</text>
  <text x="120" y="219" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">(AppProps.class)</text>
  <text x="120" y="237" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">explicit, library-safe</text>
  <line x1="220" y1="200" x2="268" y2="180" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#d2)"/>

  <!-- Strategy 3: @ConfigurationPropertiesScan -->
  <rect x="490" y="90" width="200" height="100" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="590" y="115" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Strategy 3</text>
  <text x="590" y="133" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">@ConfigurationPropertiesScan</text>
  <text x="590" y="151" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">("com.example.config")</text>
  <text x="590" y="169" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">auto-discover all in package</text>
  <line x1="490" y1="145" x2="437" y2="162" stroke="#6db33f" stroke-width="1.5" marker-end="url(#d3)"/>

  <!-- Injected into service -->
  <rect x="270" y="240" width="165" height="60" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="352" y="264" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Your Service</text>
  <text x="352" y="282" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Autowired AppProps props</text>
  <line x1="352" y1="200" x2="352" y2="238" stroke="#6db33f" stroke-width="1.5" marker-end="url(#d4)"/>

  <defs>
    <marker id="d1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="d2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="d3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="d4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

All three paths lead to the same outcome — a registered bean in the Spring context — but they differ in where the registration decision lives and what constraints they impose on the class.

## 5. Runnable example

```java
// src/main/resources/application.yml
// server:
//   custom:
//     max-connections: 100
//     idle-timeout: 30s
// cache:
//   ttl: 5m
//   max-size: 500

// ---- Plain POJO — no @Component ----
package com.example.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import java.time.Duration;

@ConfigurationProperties(prefix = "server.custom")
public class ServerProps {
    private int maxConnections;
    private Duration idleTimeout;

    public int      getMaxConnections()                    { return maxConnections; }
    public void     setMaxConnections(int maxConnections)  { this.maxConnections = maxConnections; }
    public Duration getIdleTimeout()                       { return idleTimeout; }
    public void     setIdleTimeout(Duration idleTimeout)   { this.idleTimeout = idleTimeout; }
}

// ---- Record — also no @Component ----
package com.example.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import java.time.Duration;

@ConfigurationProperties(prefix = "cache")
public record CacheProps(Duration ttl, int maxSize) {}

// ---- Registration via @EnableConfigurationProperties ----
package com.example.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(ServerProps.class)
public class InfraConfig {
    // ServerProps is now a bean — no @Component needed on ServerProps
}

// ---- Main class using @ConfigurationPropertiesScan for the record ----
package com.example;

import com.example.config.CacheProps;
import com.example.config.ServerProps;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
@ConfigurationPropertiesScan("com.example.config")  // picks up CacheProps (and re-registers ServerProps harmlessly)
public class EnablePropsApp {

    public static void main(String[] args) {
        SpringApplication.run(EnablePropsApp.class, args);
    }

    @Bean
    CommandLineRunner run(ServerProps server, CacheProps cache) {
        return args -> {
            System.out.println("maxConnections = " + server.getMaxConnections());
            System.out.println("idleTimeout    = " + server.getIdleTimeout());
            System.out.println("cache.ttl      = " + cache.ttl());
            System.out.println("cache.maxSize  = " + cache.maxSize());
        };
    }
}
```

**How to run:** add the YAML block to `application.yml`, then run `./mvnw spring-boot:run`. Expected output:

```
maxConnections = 100
idleTimeout    = PT30S
cache.ttl      = PT5M
cache.maxSize  = 500
```

## 6. Walkthrough

- **`ServerProps`** — a plain class with no Spring annotations. It binds to `server.custom.*` properties but is not yet a bean.
- **`CacheProps`** — a Java record. Records also lack `@Component`, so they are also not auto-registered.
- **`@EnableConfigurationProperties(ServerProps.class)`** on `InfraConfig` — this is the explicit-registration path. Spring Boot registers `ServerProps` as a bean under the name `server.custom-com.example.config.ServerProps`. The `InfraConfig` class is the appropriate place for this declaration because `InfraConfig` owns the infrastructure wiring.
- **`@ConfigurationPropertiesScan("com.example.config")`** on the main class — scans the `com.example.config` package for all `@ConfigurationProperties` classes. It finds both `ServerProps` and `CacheProps`. If a class was already registered via `@EnableConfigurationProperties`, the scan is smart enough not to create a duplicate bean.
- **`CommandLineRunner run(ServerProps server, CacheProps cache)`** — both beans are injected by type. They are now first-class Spring beans that can appear in any injection point, just like any `@Component`-annotated class.
- **Why `idleTimeout` prints `PT30S`** — Spring Boot parses `"30s"` using `DurationConverter` and converts it to a `java.time.Duration`. The default `toString()` representation of a `Duration` is ISO-8601 format (`PT30S` = 30 seconds).

## 7. Gotchas & takeaways

> Using `@Component` on a `@ConfigurationProperties` class that also uses constructor binding (via `@ConstructorBinding` or a Java record) can cause Spring Boot to **attempt JavaBean binding instead** in some versions, because `@Component` triggers standard component registration before the constructor-binding processor runs. The safe pattern for constructor-binding targets is to omit `@Component` and register via `@EnableConfigurationProperties` or `@ConfigurationPropertiesScan`.

> If you use `@ConfigurationPropertiesScan` without specifying `basePackages`, it defaults to the package of the annotated class. Any `@ConfigurationProperties` class in a **sibling or parent package** will not be found. Forgetting this is a common source of "bean not found" errors when the application package structure is not flat.

- `@EnableConfigurationProperties` is the right choice for library auto-configuration — it keeps your POJO free of Spring annotations and lets library users see clearly which classes are being registered.
- `@ConfigurationPropertiesScan` is the most ergonomic choice for application code with many config classes — one line replaces a growing list of explicit registrations.
- Both `@EnableConfigurationProperties` and `@ConfigurationPropertiesScan` trigger validation (JSR-303) when `@Validated` is present on the class, exactly as `@Component` would.
- The bean name generated by `@EnableConfigurationProperties` is `<prefix>-<fully-qualified-class-name>`, which is deliberately ugly to avoid collisions with user-defined beans. Inject by type, not by name.
- Spring Boot's own auto-configurations use `@EnableConfigurationProperties` extensively — searching for it in the `spring-boot-autoconfigure` jar is a great way to see real-world examples.
