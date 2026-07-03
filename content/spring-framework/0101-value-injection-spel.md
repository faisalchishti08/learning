---
card: spring-framework
gi: 101
slug: value-injection-spel
title: "@Value injection & SpEL"
---

## 1. What it is

`@Value` injects scalar values — strings, numbers, booleans — into Spring beans from three sources:

1. **Property expressions** `${key}` — reads from the property environment (`application.properties`, system properties, env vars).
2. **Spring Expression Language (SpEL)** `#{expression}` — evaluates arbitrary expressions at wiring time: arithmetic, bean method calls, collection projections, conditionals.
3. **Literal values** — `@Value("42")` or `@Value("hello")` for hard-coded constants (rarely useful).

## 2. Why & when

Use `@Value` when you need to inject configuration or computed scalars without creating a full `@ConfigurationProperties` class:

- Inject a timeout value from `application.properties`.
- Set a field to the result of a simple calculation or environment lookup.
- Reference another bean's property: `#{someBean.maxRetries}`.
- Inject OS environment info: `#{systemEnvironment['HOME']}`.

For groups of related properties, prefer `@ConfigurationProperties` (Spring Boot). For one-off scalar injections in plain Spring, `@Value` is idiomatic.

## 3. Core concept

`@Value` is processed by `AutowiredAnnotationBeanPostProcessor` with the help of `StringValueResolver`. The resolution chain:

- `${...}` — handed to `PropertySourcesPlaceholderConfigurer`; resolved from the `Environment` property sources.
- `#{...}` — handed to `SpelExpressionParser`; the expression is evaluated against the `ApplicationContext` as the root object, so it can access `@beans`, `systemProperties`, `systemEnvironment`, and any Java expression.
- Both can be nested: `#{${max.retries:3} * 2}` — read property then double it.

SpEL expression capabilities used with `@Value`:

| Expression | Example | Result |
|---|---|---|
| Literal | `#{42}` | `42` |
| Bean property | `#{configBean.timeout}` | value of `timeout` field |
| Method call | `#{T(Math).random()}` | random double |
| Collection | `#{list.size()}` | list size |
| Conditional | `#{flag ? 'A' : 'B'}` | ternary |
| System property | `#{systemProperties['user.home']}` | home dir |

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <!-- Sources -->
  <rect x="10" y="30" width="155" height="44" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="87" y="53" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">app.properties</text>
  <text x="87" y="67" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">${key} resolution</text>

  <rect x="10" y="100" width="155" height="44" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="87" y="123" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">SpEL Engine</text>
  <text x="87" y="137" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">#{expr} evaluation</text>

  <!-- @Value -->
  <rect x="265" y="65" width="185" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="357" y="90" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">@Value resolver</text>
  <text x="357" y="106" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">${…} → properties  #{…} → SpEL</text>

  <!-- Bean field -->
  <rect x="545" y="65" width="145" height="54" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="617" y="90" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Bean field/param</text>
  <text x="617" y="106" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">injected value</text>

  <line x1="167" y1="52" x2="262" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a101)"/>
  <line x1="167" y1="122" x2="262" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a101)"/>
  <line x1="452" y1="92" x2="542" y2="92" stroke="#79c0ff" stroke-width="2" marker-end="url(#b101)"/>
  <defs>
    <marker id="a101" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b101" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="195" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">${key} reads properties · #{expr} evaluates SpEL against the ApplicationContext</text>
</svg>

`@Value` dispatches to the property resolver or the SpEL engine depending on the `${` vs `#{` prefix.

## 5. Runnable example

### Level 1 — Basic

Inject simple property values and a literal into a mail-sender service.

```java
// ValueBasic.java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.stereotype.Service;
import java.util.Properties;

@Service
class MailService {
    @Value("${mail.host:smtp.example.com}")   // property with default
    private String host;

    @Value("${mail.port:587}")
    private int port;

    @Value("TLS")                             // literal constant
    private String protocol;

    public void send(String to, String subject) {
        System.out.printf("Sending via %s:%d [%s] → %s: %s%n",
            host, port, protocol, to, subject);
    }
}

@Configuration
@ComponentScan
class ValCfg {
    @Bean public static PropertySourcesPlaceholderConfigurer pspc() {
        var p = new PropertySourcesPlaceholderConfigurer();
        var props = new Properties();
        props.setProperty("mail.host", "smtp.mycompany.com");
        props.setProperty("mail.port", "465");
        p.setProperties(props);
        return p;
    }
}

public class ValueBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ValCfg.class);
        ctx.getBean(MailService.class).send("alice@example.com", "Welcome!");
        ctx.close();
    }
}
```

How to run: `java ValueBasic.java`

`${mail.host}` and `${mail.port}` resolve from the registered `Properties` object. `"TLS"` is injected verbatim. The `:default` syntax means the property is optional — if absent, the default value is used.

### Level 2 — Intermediate

Add SpEL expressions to compute derived values and read system properties.

```java
// ValueSpel.java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.stereotype.*;
import java.util.Properties;

@Component("appConfig")
class AppConfig {
    public int getBaseTimeout() { return 3000; }
    public String getEnvironment() { return "production"; }
}

@Service
class ApiClient {
    // SpEL: call method on another bean
    @Value("#{appConfig.baseTimeout * 2}")
    private int timeout;

    // SpEL: ternary based on bean property
    @Value("#{appConfig.environment == 'production' ? 'https://api.example.com' : 'http://localhost:8080'}")
    private String baseUrl;

    // SpEL: system property
    @Value("#{systemProperties['user.name']}")
    private String runningUser;

    // SpEL: T() type reference for static method
    @Value("#{T(java.lang.Runtime).getRuntime().availableProcessors()}")
    private int cpuCount;

    public void printConfig() {
        System.out.println("timeout   = " + timeout + " ms");
        System.out.println("baseUrl   = " + baseUrl);
        System.out.println("user      = " + runningUser);
        System.out.println("cpus      = " + cpuCount);
    }
}

@Configuration
@ComponentScan
class SpelCfg {
    @Bean public static PropertySourcesPlaceholderConfigurer pspc() {
        return new PropertySourcesPlaceholderConfigurer();
    }
}

public class ValueSpel {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SpelCfg.class);
        ctx.getBean(ApiClient.class).printConfig();
        ctx.close();
    }
}
```

How to run: `java ValueSpel.java`

`#{appConfig.baseTimeout * 2}` navigates to the `appConfig` bean, calls `getBaseTimeout()`, and doubles it. The ternary switches the URL based on environment. `systemProperties['user.name']` reads the JVM system property at wiring time.

### Level 3 — Advanced

Combine `${property}` references inside SpEL expressions, inject a list, and use conditional SpEL to handle a missing property gracefully.

```java
// ValueAdvanced.java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.stereotype.*;
import java.util.*;

@Component("featureFlags")
class FeatureFlags {
    private final Map<String, Boolean> flags = Map.of(
        "newCheckout", true,
        "darkMode", false
    );
    public boolean isEnabled(String feature) {
        return flags.getOrDefault(feature, false);
    }
}

@Service
class CheckoutService {
    // Nest ${property} inside #{} — read property then use in SpEL
    @Value("#{${checkout.timeout:5000} > 3000 ? 'HIGH' : 'LOW'}")
    private String timeoutTier;

    // SpEL: call method on another bean with argument
    @Value("#{featureFlags.isEnabled('newCheckout')}")
    private boolean newCheckoutEnabled;

    // SpEL: split a comma-separated property into a List
    @Value("#{'${checkout.allowedCurrencies:USD,EUR,GBP}'.split(',')}")
    private List<String> allowedCurrencies;

    // SpEL: safe navigation — returns null instead of NPE if systemEnvironment key missing
    @Value("#{systemEnvironment['CHECKOUT_REGION'] ?: 'US'}")
    private String region;

    public void printConfig() {
        System.out.println("timeoutTier        = " + timeoutTier);
        System.out.println("newCheckout active = " + newCheckoutEnabled);
        System.out.println("currencies         = " + allowedCurrencies);
        System.out.println("region             = " + region);
    }
}

@Configuration
@ComponentScan
class AdvCfg {
    @Bean public static PropertySourcesPlaceholderConfigurer pspc() {
        var p = new PropertySourcesPlaceholderConfigurer();
        var props = new Properties();
        props.setProperty("checkout.timeout", "6000");
        props.setProperty("checkout.allowedCurrencies", "USD,EUR,GBP,JPY");
        p.setProperties(props);
        return p;
    }
}

public class ValueAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AdvCfg.class);
        ctx.getBean(CheckoutService.class).printConfig();
        ctx.close();
    }
}
```

How to run: `java ValueAdvanced.java`

`#{${checkout.timeout:5000} > 3000 ? 'HIGH' : 'LOW'}` first resolves `${checkout.timeout:5000}` to `"6000"`, then SpEL evaluates `6000 > 3000` → `"HIGH"`. The `?.` safe-navigation operator (`?:` Elvis) returns `"US"` when `CHECKOUT_REGION` env var is absent.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Context starts** — scans `AdvCfg`, finds `FeatureFlags`, `CheckoutService`, and the `pspc` BFPP.
2. **PSPC runs first** — reads `checkout.timeout=6000` and `checkout.allowedCurrencies=USD,EUR,GBP,JPY` from the `Properties` object into the `Environment`.
3. **`FeatureFlags` constructed** — `Map.of(...)` initialised; bean named `featureFlags`.
4. **`CheckoutService` constructed** — `AutowiredAnnotationBeanPostProcessor` processes four `@Value` fields.

   **Field `timeoutTier`**: expression `#{${checkout.timeout:5000} > 3000 ? 'HIGH' : 'LOW'}`. Step A: `${checkout.timeout:5000}` → `"6000"` (from properties). Step B: SpEL evaluates `6000 > 3000` → `true` → `"HIGH"`. Injected.

   **Field `newCheckoutEnabled`**: `#{featureFlags.isEnabled('newCheckout')}` → SpEL resolves bean `featureFlags`, calls `isEnabled("newCheckout")` → `true`. Injected.

   **Field `allowedCurrencies`**: `#{'USD,EUR,GBP,JPY'.split(',')}`. Step A: `${checkout.allowedCurrencies:USD,EUR,GBP}` → `"USD,EUR,GBP,JPY"`. Step B: SpEL calls `.split(',')` → `String[]` → Spring converts to `List<String>`. Injected.

   **Field `region`**: `#{systemEnvironment['CHECKOUT_REGION'] ?: 'US'}` — `systemEnvironment` is a built-in SpEL variable. Key absent → `null` → Elvis `?:` → `"US"`. Injected.

5. **`printConfig()` called** — all four values printed.

Expected output:
```
timeoutTier        = HIGH
newCheckout active = true
currencies         = [USD, EUR, GBP, JPY]
region             = US
```

## 7. Gotchas & takeaways

> `${key}` and `#{expr}` are **not interchangeable**. `${featureFlags.isEnabled('x')}` tries to find a property key literally named `featureFlags.isEnabled('x')` — it fails. Bean navigation and method calls require `#{...}`.

> SpEL expressions in `@Value` are evaluated **once at wiring time** — they are not live bindings. If `featureFlags` changes after the context starts, injected `@Value` fields will not update.

- Default syntax: `${key:defaultValue}` — colon separates key from default.
- Elvis operator in SpEL: `#{expr ?: fallback}` — returns `fallback` when `expr` is `null`.
- To inject a literal `$` or `#` string, escape them: `@Value("\\${literal}")`.
- `@Value` works on constructor parameters, setter parameters, and fields.
- For bulk configuration injection into a POJO, prefer `@ConfigurationProperties` — it's type-safe, validates, and documents the structure in one place.
