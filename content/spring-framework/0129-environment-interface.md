---
card: spring-framework
gi: 129
slug: environment-interface
title: "Environment interface"
---

## 1. What it is

The `Environment` interface is Spring's abstraction over **profiles** and **property sources**. It answers two questions: (1) which profiles are active right now, and (2) what value does a given property key resolve to, considering the full priority-ordered stack of property sources.

```java
@Autowired Environment env;
// Profile queries
env.getActiveProfiles();           // ["prod", "us-east"]
env.acceptsProfiles("prod");       // true
// Property queries
env.getProperty("db.url");         // "jdbc:postgresql://..."
env.getRequiredProperty("api.key"); // throws if absent
```

## 2. Why & when

Inject `Environment` when you need runtime access to profiles or properties without committing to a specific key at annotation time. Common use cases:

- **Dynamic configuration** — a factory method chooses which implementation to instantiate based on a property value.
- **Profile-driven branching** — inside a `@Bean` method, pick a datasource URL based on the active profile.
- **Property-existence checks** — verify that a required key is present before constructing a bean that depends on it.
- **Testing** — set up `StandardEnvironment` or `MockEnvironment` in tests to control which properties and profiles are visible.

## 3. Core concept

`Environment` extends `PropertyResolver`:

```
Environment
  ├── getActiveProfiles()    → String[]
  ├── getDefaultProfiles()   → String[]
  ├── acceptsProfiles(...)   → boolean          (vararg or ProfileExpression)
  └── [PropertyResolver]
        ├── getProperty(key)            → String or null
        ├── getProperty(key, default)   → String
        ├── getProperty(key, type)      → T
        ├── getRequiredProperty(key)    → String (throws MissingKeyException)
        └── containsProperty(key)       → boolean
```

`ConfigurableEnvironment` (the mutable subtype) adds:

- `setActiveProfiles(...)` — programmatically activate profiles.
- `getPropertySources()` — access the `MutablePropertySources` for adding/removing sources.
- `merge(ConfigurableEnvironment parent)` — merge profiles and sources from a parent.

Spring Boot provides `StandardServletEnvironment` (for web) and `StandardEnvironment` (for standalone) as the default implementations.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Environment box -->
  <rect x="10" y="40" width="200" height="125" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="63" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Environment</text>
  <text x="110" y="82" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">getActiveProfiles()</text>
  <text x="110" y="98" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">acceptsProfiles("prod")</text>
  <text x="110" y="118" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">──────────────────</text>
  <text x="110" y="133" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">getProperty("key")</text>
  <text x="110" y="149" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">getRequiredProperty()</text>

  <!-- Property sources (ordered) -->
  <rect x="290" y="40" width="185" height="125" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="382" y="63" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">PropertySources (ordered)</text>
  <text x="382" y="82" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">1. System properties (-D)</text>
  <text x="382" y="98" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">2. Env variables (OS)</text>
  <text x="382" y="114" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">3. @PropertySource files</text>
  <text x="382" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">4. Default values</text>
  <text x="382" y="148" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">first source wins</text>

  <!-- Consumers -->
  <rect x="560" y="40" width="132" height="125" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="626" y="63" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Consumers</text>
  <text x="626" y="83" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Value("${k}")</text>
  <text x="626" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Profile check</text>
  <text x="626" y="117" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Conditional</text>
  <text x="626" y="134" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">env.getProperty()</text>

  <line x1="212" y1="102" x2="287" y2="102" stroke="#6db33f" stroke-width="2" marker-end="url(#a129)"/>
  <line x1="477" y1="102" x2="557" y2="102" stroke="#79c0ff" stroke-width="2" marker-end="url(#b129)"/>
  <defs>
    <marker id="a129" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b129" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Environment unifies profiles and property resolution behind one interface</text>
</svg>

`Environment` is the single API for both profile state and property resolution.

## 5. Runnable example

### Level 1 — Basic

Inject `Environment` and use it to query profiles and a property.

```java
// EnvironmentBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;

class InfoService {
    @Autowired Environment env;

    public void printInfo() {
        System.out.println("Active profiles: " +
            java.util.Arrays.toString(env.getActiveProfiles()));
        System.out.println("Default profiles: " +
            java.util.Arrays.toString(env.getDefaultProfiles()));
        System.out.println("Is 'prod' active? " + env.acceptsProfiles("prod"));

        System.out.println("db.url = " +
            env.getProperty("db.url", "NOT SET"));
        System.out.println("app.name = " +
            env.getProperty("app.name", "NOT SET"));
    }
}

@Configuration
@ComponentScan(basePackageClasses = EnvironmentBasic.class)
class EnvCfg {}

public class EnvironmentBasic {
    public static void main(String[] args) {
        System.setProperty("db.url", "jdbc:h2:mem:test");
        System.setProperty("app.name", "EnvironmentDemo");

        var ctx = new AnnotationConfigApplicationContext(EnvCfg.class);
        ctx.getBean(InfoService.class).printInfo();
        ctx.close();

        System.clearProperty("db.url");
        System.clearProperty("app.name");
    }
}
```

How to run: `java EnvironmentBasic.java`

Properties set via `System.setProperty()` are immediately visible through `env.getProperty()` — system properties are a built-in `PropertySource` with high priority. No profiles are active by default; `acceptsProfiles("prod")` returns `false`.

### Level 2 — Intermediate

Use `Environment` inside a `@Bean` method to choose an implementation based on active profiles and a property value.

```java
// EnvironmentConditional.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;

interface NotificationSender { void send(String msg); }
class EmailSender implements NotificationSender {
    public void send(String msg) { System.out.println("[EMAIL] " + msg); }
}
class SmsSender implements NotificationSender {
    public void send(String msg) { System.out.println("[SMS] " + msg); }
}
class LogSender implements NotificationSender {
    public void send(String msg) { System.out.println("[LOG] " + msg); }
}

@Configuration
class NotifCfg {
    @Autowired Environment env;

    @Bean
    public NotificationSender notificationSender() {
        String channel = env.getProperty("notify.channel", "log");
        boolean isProd = env.acceptsProfiles("prod");
        System.out.println("[Config] channel=" + channel + " prod=" + isProd);

        if (isProd) {
            return "sms".equals(channel) ? new SmsSender() : new EmailSender();
        }
        return new LogSender();
    }
}

public class EnvironmentConditional {
    static void run(String channel, String... profiles) {
        System.setProperty("notify.channel", channel);
        var ctx = new AnnotationConfigApplicationContext();
        if (profiles.length > 0) ctx.getEnvironment().setActiveProfiles(profiles);
        ctx.register(NotifCfg.class);
        ctx.refresh();
        ctx.getBean(NotificationSender.class).send("Order shipped");
        ctx.close();
        System.clearProperty("notify.channel");
        System.out.println();
    }

    public static void main(String[] args) {
        run("log");              // dev: always log
        run("email", "prod");   // prod + email
        run("sms",   "prod");   // prod + sms
    }
}
```

How to run: `java EnvironmentConditional.java`

`notificationSender()` reads `notify.channel` and checks the `"prod"` profile via `env`. The factory creates the correct sender at context startup. The caller sets profiles programmatically via `ctx.getEnvironment().setActiveProfiles()` before `ctx.refresh()`.

### Level 3 — Advanced

`ConfigurableEnvironment` to add a custom `PropertySource`, inspect the full source stack, and read typed properties.

```java
// EnvironmentAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.util.*;

// Application service that needs runtime config
class PaymentService {
    @Autowired Environment env;

    public void process(String orderId, double amount) {
        String provider = env.getRequiredProperty("payment.provider");
        int retries     = env.getProperty("payment.retries", Integer.class, 3);
        boolean sandbox = env.getProperty("payment.sandbox", Boolean.class, false);

        System.out.printf("[Payment] order=%s amount=$%.2f provider=%s retries=%d sandbox=%b%n",
            orderId, amount, provider, retries, sandbox);
    }
}

@Configuration
@ComponentScan(basePackageClasses = EnvironmentAdvanced.class)
class AdvEnvCfg {}

public class EnvironmentAdvanced {
    public static void main(String[] args) {
        // Build context
        var ctx = new AnnotationConfigApplicationContext();

        // Add a high-priority custom property source before refresh
        ConfigurableEnvironment env = ctx.getEnvironment();

        // In-memory properties (highest priority after system props)
        Properties appProps = new Properties();
        appProps.setProperty("payment.provider", "stripe");
        appProps.setProperty("payment.retries",  "5");
        appProps.setProperty("payment.sandbox",  "true");
        env.getPropertySources().addFirst(
            new PropertiesPropertySource("appConfig", appProps));

        ctx.register(AdvEnvCfg.class);
        ctx.getEnvironment().setActiveProfiles("staging");
        ctx.refresh();

        // Inspect all property sources in priority order
        System.out.println("=== Property source stack (first = highest priority) ===");
        env.getPropertySources().forEach(ps ->
            System.out.println("  " + ps.getName() + " [" + ps.getClass().getSimpleName() + "]"));

        System.out.println("\n=== Typed property resolution ===");
        System.out.println("payment.retries (int):    " +
            env.getProperty("payment.retries", Integer.class));
        System.out.println("payment.sandbox (boolean): " +
            env.getProperty("payment.sandbox", Boolean.class));
        System.out.println("payment.timeout (default): " +
            env.getProperty("payment.timeout", Integer.class, 30));

        System.out.println("\n=== Profiles ===");
        System.out.println("Active: " + Arrays.toString(env.getActiveProfiles()));
        System.out.println("Accepts 'staging': " + env.acceptsProfiles("staging"));
        System.out.println("Accepts 'prod':    " + env.acceptsProfiles("prod"));

        System.out.println("\n=== Process payment ===");
        ctx.getBean(PaymentService.class).process("ORD-001", 299.99);

        ctx.close();
    }
}
```

How to run: `java EnvironmentAdvanced.java`

`addFirst()` makes the custom `PropertiesPropertySource` the highest-priority source. `getProperty(key, Integer.class)` performs automatic type conversion. `getProperty(key, Integer.class, 30)` provides a typed default.

## 6. Walkthrough

Execution for Level 3:

1. **`AnnotationConfigApplicationContext` created** — `ctx.getEnvironment()` returns a `StandardEnvironment`.
2. **`addFirst(new PropertiesPropertySource("appConfig", appProps))`** — inserts `appConfig` at position 0 (highest priority).
3. **`setActiveProfiles("staging")`** — marks `"staging"` as active.
4. **`ctx.refresh()`** — beans created. `PaymentService` gets `@Autowired Environment`.
5. **Property source stack printed** — `appConfig` first, then system properties, system environment, etc.
6. **Typed resolution** — `getProperty("payment.retries", Integer.class)` → `5` (from `appConfig`). `getProperty("payment.timeout", Integer.class, 30)` → `30` (default, key absent).
7. **`process("ORD-001", 299.99)`** → reads `provider=stripe`, `retries=5`, `sandbox=true`.

Expected output (abbreviated):
```
=== Property source stack (first = highest priority) ===
  appConfig [PropertiesPropertySource]
  systemProperties [PropertiesPropertySource]
  systemEnvironment [SystemEnvironmentPropertySource]

=== Typed property resolution ===
payment.retries (int):    5
payment.sandbox (boolean): true
payment.timeout (default): 30

=== Profiles ===
Active: [staging]
Accepts 'staging': true
Accepts 'prod':    false

=== Process payment ===
[Payment] order=ORD-001 amount=$299.99 provider=stripe retries=5 sandbox=true
```

## 7. Gotchas & takeaways

> `getRequiredProperty(key)` throws `IllegalStateException` (not `NullPointerException`) when the key is absent. Use it for mandatory config; use `getProperty(key, defaultValue)` for optional config with a fallback.

> You must add custom `PropertySource`s to `ConfigurableEnvironment` **before** `ctx.refresh()` — after refresh, beans are already instantiated and `@Value` fields are already injected. Post-refresh source additions have no effect on already-created beans.

- `acceptsProfiles("!prod")` — the `!` prefix negates. `acceptsProfiles("prod | staging")` uses the expression syntax (Spring 5.1+).
- `env.getProperty(key, Integer.class)` performs `ConversionService`-backed type conversion from string to the requested type.
- `MockEnvironment` in spring-test provides a programmable environment for unit tests without starting a full context.
- `Environment` beans are pre-registered — `@Autowired Environment env` always resolves without declaring a `@Bean`.
