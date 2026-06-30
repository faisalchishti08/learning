---
card: spring-framework
gi: 90
slug: propertyoverrideconfigurer
title: PropertyOverrideConfigurer
---

## 1. What it is

`PropertyOverrideConfigurer` is a `BeanFactoryPostProcessor` that overrides bean **property values** from an external `.properties` file using the naming convention `beanName.propertyName=value`. It targets bean properties directly rather than resolving `${...}` placeholders.

Where `PropertySourcesPlaceholderConfigurer` fills placeholders you explicitly placed in config, `PropertyOverrideConfigurer` overrides whatever the bean definition already says — you can change the value without touching the original config at all.

## 2. Why & when

Use `PropertyOverrideConfigurer` when:

- You want to override bean property values from an external file **without modifying the original bean definitions**.
- You have multiple deployment environments and want a "patch" file per environment that overrides specific values.
- You need to externally tune existing third-party library beans whose source you can't change.

Example: a `DataSource` bean already has `url=jdbc:postgresql://prod-db/mydb` in one config; a test override file sets `dataSource.url=jdbc:h2:mem:testdb` at test time.

## 3. Core concept

The properties file uses a two-part key: `beanName.propertyName=value`.

Spring's `PropertyOverrideConfigurer`:
1. Reads the properties file.
2. For each entry `beanName.propertyName=value`, finds the `BeanDefinition` for `beanName`.
3. Sets or replaces the property value for `propertyName` in that definition.
4. If a property is not in the file, the original bean definition value is kept.

Multiple properties files can be stacked; later files override earlier ones. If a bean name or property is unknown, it silently skips (or throws, based on `setIgnoreInvalidKeys`).

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="50" width="195" height="110" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="108" y="72" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">override.properties</text>
  <text x="108" y="92" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">dataSource.url=jdbc:h2:…</text>
  <text x="108" y="109" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">scheduler.poolSize=5</text>
  <text x="108" y="126" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">mailer.host=smtp.test</text>

  <rect x="280" y="70" width="170" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="365" y="95" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">PropertyOverride</text>
  <text x="365" y="111" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Configurer</text>

  <rect x="530" y="50" width="155" height="110" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="607" y="72" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">BeanDefinitions</text>
  <text x="607" y="92" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">dataSource.url ← jdbc:h2</text>
  <text x="607" y="109" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">scheduler.poolSize ← 5</text>
  <text x="607" y="126" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">mailer.host ← smtp.test</text>

  <line x1="207" y1="105" x2="277" y2="97" stroke="#6db33f" stroke-width="2" marker-end="url(#a90)"/>
  <line x1="452" y1="97" x2="527" y2="97" stroke="#79c0ff" stroke-width="2" marker-end="url(#b90)"/>
  <defs>
    <marker id="a90" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b90" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="190" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">beanName.propertyName=value patches the definition before instantiation</text>
</svg>

`PropertyOverrideConfigurer` patches specific bean properties using `bean.property=value` keys.

## 5. Runnable example

### Level 1 — Basic

A simple bean with two properties; an in-memory properties object overrides one of them.

```java
// PocBasic.java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.context.support.PropertyOverrideConfigurer;
import org.springframework.stereotype.Component;
import java.util.Properties;

@Component
class MailSender {
    // Default values set on the bean itself
    private String host = "smtp.prod.example.com";
    private int port = 587;

    public void setHost(String h) { this.host = h; }
    public void setPort(int p)    { this.port = p; }

    public void print() {
        System.out.println("Mail → " + host + ":" + port);
    }
}

@Configuration
@ComponentScan
class PocBasicCfg {
    @Bean
    public static PropertyOverrideConfigurer poc() {
        var p = new PropertyOverrideConfigurer();
        var props = new Properties();
        // Override just the host; port keeps its default (587)
        props.setProperty("mailSender.host", "smtp.test.example.com");
        p.setProperties(props);
        return p;
    }
}

public class PocBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PocBasicCfg.class);
        ctx.getBean(MailSender.class).print();
        ctx.close();
    }
}
```

How to run: `java PocBasic.java`

The bean default is `smtp.prod.example.com`, but the properties object overrides just `host` via `mailSender.host`. The `port` is untouched and stays `587`.

### Level 2 — Intermediate

Override multiple beans from a `.properties` file, and use `setIgnoreInvalidKeys(true)` to silently skip unknown keys.

```java
// PocFile.java
// Create test-override.properties on the classpath:
//   dataSource.url=jdbc:h2:mem:testdb
//   dataSource.username=sa
//   scheduler.poolSize=3

import org.springframework.context.annotation.*;
import org.springframework.context.support.PropertyOverrideConfigurer;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

@Component
class DataSource {
    private String url = "jdbc:postgresql://prod/mydb";
    private String username = "prod_user";
    public void setUrl(String u) { this.url = u; }
    public void setUsername(String u) { this.username = u; }
    public void print() { System.out.println("DS: " + url + " / " + username); }
}

@Component
class Scheduler {
    private int poolSize = 10;
    public void setPoolSize(int s) { this.poolSize = s; }
    public void print() { System.out.println("Scheduler poolSize: " + poolSize); }
}

@Configuration
@ComponentScan
class FileCfg {
    @Bean
    public static PropertyOverrideConfigurer poc() {
        var p = new PropertyOverrideConfigurer();
        p.setLocation(new ClassPathResource("test-override.properties"));
        p.setIgnoreInvalidKeys(true); // skip unknown bean/property names silently
        return p;
    }
}

public class PocFile {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(FileCfg.class);
        ctx.getBean(DataSource.class).print();
        ctx.getBean(Scheduler.class).print();
        ctx.close();
    }
}
```

How to run: place `test-override.properties` on the classpath, then `java PocFile.java`

Both `dataSource` and `scheduler` beans are patched by the external file. Any key in the file that refers to a non-existent bean or property is silently ignored because of `setIgnoreInvalidKeys(true)`.

### Level 3 — Advanced

Layer two `PropertyOverrideConfigurer` beans: a base `defaults.properties` and an environment-specific `env-override.properties`, ordered by `@Order` so the env file wins.

```java
// PocLayered.java
// defaults.properties:
//   apiClient.baseUrl=https://api.prod.example.com
//   apiClient.timeout=5000
//   apiClient.retries=3
//
// env-override.properties (simulated by second configurer):
//   apiClient.baseUrl=https://api.staging.example.com
//   apiClient.timeout=2000

import org.springframework.context.annotation.*;
import org.springframework.context.support.PropertyOverrideConfigurer;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import java.util.Properties;

@Component
class ApiClient {
    private String baseUrl = "https://api.default.example.com";
    private int timeout   = 3000;
    private int retries   = 1;

    public void setBaseUrl(String u) { this.baseUrl = u; }
    public void setTimeout(int t)    { this.timeout = t; }
    public void setRetries(int r)    { this.retries = r; }

    public void print() {
        System.out.printf("API: %s  timeout=%d  retries=%d%n", baseUrl, timeout, retries);
    }
}

@Configuration
@ComponentScan
class LayeredCfg {
    @Bean @Order(1)                   // runs first — base defaults
    public static PropertyOverrideConfigurer defaults() {
        var p = new PropertyOverrideConfigurer();
        var props = new Properties();
        props.setProperty("apiClient.baseUrl", "https://api.prod.example.com");
        props.setProperty("apiClient.timeout", "5000");
        props.setProperty("apiClient.retries", "3");
        p.setProperties(props);
        return p;
    }

    @Bean @Order(2)                   // runs second — env-specific overrides win
    public static PropertyOverrideConfigurer envOverride() {
        var p = new PropertyOverrideConfigurer();
        var props = new Properties();
        props.setProperty("apiClient.baseUrl", "https://api.staging.example.com");
        props.setProperty("apiClient.timeout", "2000");
        // retries is NOT overridden — keeps the value set by defaults()
        p.setProperties(props);
        return p;
    }
}

public class PocLayered {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(LayeredCfg.class);
        ctx.getBean(ApiClient.class).print();
        ctx.close();
    }
}
```

How to run: `java PocLayered.java`

The `defaults` configurer sets all three properties. The `envOverride` configurer then overwrites `baseUrl` and `timeout`. `retries` was not in the override — it keeps the value from `defaults` (`3`). This is the real-world pattern of layered configuration: base → environment patch.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Spring loads `LayeredCfg`** — discovers `@ComponentScan` and registers `ApiClient`, `defaults`, and `envOverride` as `BeanDefinition`s. `ApiClient` has no property value overrides yet.
2. **Both POC beans instantiated early** — because they return `BeanFactoryPostProcessor`, Spring creates them in `@Order` sequence (1 first, then 2).
3. **`defaults.postProcessBeanFactory` fires** — reads the `Properties` object and patches `ApiClient`'s definition: `baseUrl` set to `"https://api.prod.example.com"`, `timeout` to `"5000"`, `retries` to `"3"`. The `BeanDefinition` now carries these property values.
4. **`envOverride.postProcessBeanFactory` fires** — reads its properties and patches `ApiClient`'s definition again: `baseUrl` becomes `"https://api.staging.example.com"`, `timeout` becomes `"2000"`. `retries` is not in this properties set, so the `"3"` from step 3 remains.
5. **`ApiClient` instantiated** — Spring calls the default constructor, then calls `setBaseUrl("https://api.staging.example.com")`, `setTimeout(2000)`, `setRetries(3)` using standard JavaBean setter injection.
6. **`main` calls `print()`** — outputs the final resolved values.

Expected output:
```
API: https://api.staging.example.com  timeout=2000  retries=3
```

## 7. Gotchas & takeaways

> `PropertyOverrideConfigurer` requires **JavaBean setter methods** (`setXxx`) on the target bean. It doesn't work with `@Value` field injection or constructor injection — it calls `setUrl(...)` etc. directly via reflection.

> The key format is strictly `beanName.propertyName`. If you use `dataSource.url` but the bean is named `myDataSource`, nothing is overridden and there's no error (unless `setIgnoreInvalidKeys(false)`, which is the default — it actually does throw on invalid keys, so set `true` for silent skipping).

- Both `PropertySourcesPlaceholderConfigurer` and `PropertyOverrideConfigurer` are BFPPs — register both as `static @Bean`.
- `PropertyOverrideConfigurer` **replaces** whatever the bean definition already has; you don't need to put `${...}` in the original config.
- Multiple configurers are ordered by `@Order` or `Ordered`; later ones overwrite earlier ones for the same key.
- This is less common in Spring Boot (which uses `application.properties` + profile files for the same effect) but is standard in plain Spring for environment patching.
