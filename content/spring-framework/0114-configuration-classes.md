---
card: spring-framework
gi: 114
slug: configuration-classes
title: "@Configuration classes"
---

## 1. What it is

A `@Configuration` class is Spring's Java-based replacement for XML bean configuration. It is a class annotated with `@Configuration` that contains `@Bean` methods — each method defines one bean. Spring processes these classes specially: it wraps them in a **CGLIB proxy** so that calling one `@Bean` method from another method inside the same class goes through the proxy and returns the singleton from the context, not a fresh Java object.

## 2. Why & when

`@Configuration` is the standard place to declare beans you can't auto-detect with `@ComponentScan`:

- Third-party classes you can't annotate with `@Component`.
- Beans that require multi-step construction.
- Beans whose type or behaviour varies based on environment or conditions.
- Infrastructure beans (data sources, connection factories, security configs).

In modern Spring Boot apps you write `@Configuration` classes for infrastructure. Business logic beans are usually component-scanned.

## 3. Core concept

`@Configuration` is itself `@Component`-meta-annotated, so component scanning finds and registers it. Spring then processes its `@Bean` methods via `ConfigurationClassPostProcessor` (a `BeanFactoryPostProcessor`).

The critical behaviour: CGLIB proxying of `@Configuration`. When you call `dataSource()` from inside `entityManagerFactory()` (both `@Bean` methods on the same class), the proxy intercepts the call and returns the singleton already in the context rather than constructing a new one:

```java
@Configuration
class AppConfig {
    @Bean DataSource dataSource() { return new HikariDataSource(); }

    @Bean EntityManagerFactory emf() {
        // this.dataSource() goes through CGLIB proxy → returns singleton
        return new LocalContainerEntityManagerFactoryBean(dataSource());
    }
}
```

Without CGLIB (i.e., in `@Component` "lite mode"), calling `dataSource()` directly would create a second `DataSource` instance.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <!-- Config class -->
  <rect x="10" y="60" width="175" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="97" y="83"  fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">@Configuration</text>
  <text x="97" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Bean dataSource()</text>
  <text x="97" y="115" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Bean repository()</text>
  <text x="97" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Bean service()</text>

  <!-- CGLIB Proxy -->
  <rect x="280" y="75" width="155" height="54" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="357" y="100" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">CGLIB Proxy</text>
  <text x="357" y="115" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">intercepts @Bean calls</text>

  <!-- Bean factory -->
  <rect x="530" y="60" width="160" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="610" y="83"  fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Bean Factory</text>
  <text x="610" y="100" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">dataSource (1 instance)</text>
  <text x="610" y="115" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">repository (1 instance)</text>
  <text x="610" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">service (1 instance)</text>

  <line x1="187" y1="105" x2="277" y2="102" stroke="#79c0ff" stroke-width="2" marker-end="url(#a114)"/>
  <line x1="437" y1="102" x2="527" y2="102" stroke="#6db33f" stroke-width="2" marker-end="url(#b114)"/>
  <defs>
    <marker id="a114" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="b114" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <text x="350" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">CGLIB wraps the @Configuration class so inter-@Bean calls return singletons, not new objects</text>
</svg>

CGLIB proxies the `@Configuration` class; inter-bean method calls route through the proxy to the container's singleton registry.

## 5. Runnable example

### Level 1 — Basic

A `@Configuration` class with two `@Bean` methods, demonstrating that Spring manages them as singletons.

```java
// ConfigBasic.java
import org.springframework.context.annotation.*;

class EmailService {
    private final String host;
    EmailService(String host) { this.host = host; }
    public void send(String msg) { System.out.println("[EMAIL via " + host + "] " + msg); }
}

class AlertService {
    private final EmailService email;
    AlertService(EmailService e) { this.email = e; }
    public void alert(String msg) { email.send("ALERT: " + msg); }
}

@Configuration
class AppConfig {
    @Bean
    public EmailService emailService() {
        System.out.println("Creating EmailService");
        return new EmailService("smtp.example.com");
    }

    @Bean
    public AlertService alertService() {
        // Calling emailService() goes through CGLIB proxy → returns the singleton
        System.out.println("Creating AlertService");
        return new AlertService(emailService());
    }
}

public class ConfigBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppConfig.class);
        ctx.getBean(AlertService.class).alert("Disk 95% full");

        // Only one EmailService was created despite two calls to emailService()
        var e1 = ctx.getBean(EmailService.class);
        var e2 = ctx.getBean(EmailService.class);
        System.out.println("Same EmailService singleton: " + (e1 == e2));
        ctx.close();
    }
}
```

How to run: `java ConfigBasic.java`

`"Creating EmailService"` appears only once even though `emailService()` is called both by `alertService()` and then by two `getBean()` calls. CGLIB ensures the method returns the cached singleton.

### Level 2 — Intermediate

Multiple `@Configuration` classes split by layer, showing how Spring merges them and how they can import each other.

```java
// ConfigLayered.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import java.util.*;

// Data layer config
@Configuration
class DataConfig {
    @Bean
    public Map<String, String> inMemoryDb() {
        var db = new HashMap<String, String>();
        db.put("U1", "Alice");
        db.put("U2", "Bob");
        return db;
    }

    @Bean
    public UserStore userStore(Map<String, String> inMemoryDb) {
        return new UserStore(inMemoryDb);
    }
}

class UserStore {
    private final Map<String, String> db;
    UserStore(Map<String, String> db) { this.db = db; }
    public String find(String id) { return db.getOrDefault(id, "Unknown"); }
}

// Service layer config — imports data config
@Configuration
@Import(DataConfig.class)
class ServiceConfig {
    @Autowired private UserStore userStore;

    @Bean
    public UserService userService() {
        return new UserService(userStore);
    }
}

class UserService {
    private final UserStore store;
    UserService(UserStore s) { this.store = s; }
    public String get(String id) { return "User: " + store.find(id); }
}

public class ConfigLayered {
    public static void main(String[] args) {
        // Register only the top-level config — @Import brings in DataConfig
        var ctx = new AnnotationConfigApplicationContext(ServiceConfig.class);
        System.out.println(ctx.getBean(UserService.class).get("U1"));
        System.out.println(ctx.getBean(UserService.class).get("U3"));
        ctx.close();
    }
}
```

How to run: `java ConfigLayered.java`

`ServiceConfig` imports `DataConfig` — Spring processes both. `@Autowired UserStore` in `ServiceConfig` receives the `userStore` bean from `DataConfig`.

### Level 3 — Advanced

A full configuration hierarchy with conditional beans, environment-based overrides, and demonstrating CGLIB proxy identity.

```java
// ConfigAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.context.*;

interface Notifier { void notify(String msg); }

class EmailNotifier implements Notifier {
    public void notify(String msg) { System.out.println("[EMAIL] " + msg); }
}

class SmsNotifier implements Notifier {
    public void notify(String msg) { System.out.println("[SMS] " + msg); }
}

class OrderProcessor {
    private final Notifier notifier;
    private final String env;
    OrderProcessor(Notifier n, String env) { this.notifier = n; this.env = env; }
    public void process(int id) {
        System.out.println("[" + env + "] processing order " + id);
        notifier.notify("Order " + id + " done");
    }
}

@Configuration
class NotifierConfig {
    @Value("${app.env:dev}")
    private String env;

    @Bean
    public Notifier notifier() {
        System.out.println("Creating Notifier for env=" + env);
        return "prod".equals(env) ? new SmsNotifier() : new EmailNotifier();
    }
}

@Configuration
@Import(NotifierConfig.class)
class ProcessorConfig {
    @Autowired private Notifier notifier;

    @Value("${app.env:dev}")
    private String env;

    @Bean
    public OrderProcessor orderProcessor() {
        return new OrderProcessor(notifier, env);
    }
}

public class ConfigAdvanced {
    public static void main(String[] args) {
        // Run in dev mode
        System.out.println("=== dev mode ===");
        var ctx1 = new AnnotationConfigApplicationContext(ProcessorConfig.class);
        ctx1.getBean(OrderProcessor.class).process(1);

        // Confirm the notifier() method was called only once (singleton)
        var n1 = ctx1.getBean(Notifier.class);
        var n2 = ctx1.getBean(Notifier.class);
        System.out.println("Notifier singleton: " + (n1 == n2));

        // Show that the config class itself is a CGLIB subclass
        System.out.println("Config class: " + ctx1.getBean(NotifierConfig.class).getClass().getName());
        ctx1.close();

        // Run in prod mode
        System.out.println("\n=== prod mode ===");
        System.setProperty("app.env", "prod");
        var ctx2 = new AnnotationConfigApplicationContext(ProcessorConfig.class);
        ctx2.getBean(OrderProcessor.class).process(2);
        ctx2.close();
        System.clearProperty("app.env");
    }
}
```

How to run: `java ConfigAdvanced.java`

The config class name printed will contain `$$EnhancerBySpringCGLIB$$` — proof that Spring wraps it. The `notifier()` method is called once despite being referenced from multiple places.

## 6. Walkthrough

Execution order for the Level 3 dev-mode run:

1. **`AnnotationConfigApplicationContext` created with `ProcessorConfig`** — `ConfigurationClassPostProcessor` finds `@Import(NotifierConfig.class)` and adds `NotifierConfig` to the processing queue.
2. **CGLIB proxies created** for both `NotifierConfig` and `ProcessorConfig`.
3. **`NotifierConfig.notifier()` called by Spring** to register the `notifier` bean. `env = "dev"` (default). `new EmailNotifier()` created. Bean registered as `"notifier"`.
4. **`ProcessorConfig.orderProcessor()` called** — `@Autowired Notifier notifier` resolved to the `EmailNotifier` singleton. `new OrderProcessor(emailNotifier, "dev")` created.
5. **`process(1)` called** — prints `[dev] processing order 1`, then `[EMAIL] Order 1 done`.
6. **`ctx.getBean(Notifier.class)` × 2** — both return the same `EmailNotifier` singleton. `n1 == n2` → true.
7. **`getBean(NotifierConfig.class).getClass().getName()`** — returns a CGLIB-enhanced class name confirming proxy wrapping.

Expected output:
```
=== dev mode ===
Creating Notifier for env=dev
[dev] processing order 1
[EMAIL] Order 1 done
Notifier singleton: true
Config class: NotifierConfig$$SpringCGLIB$$0

=== prod mode ===
Creating Notifier for env=prod
[prod] processing order 2
[SMS] Order 2 done
```

## 7. Gotchas & takeaways

> Calling a `@Bean` method directly from within the same `@Configuration` class **only** returns the singleton if the class is processed by Spring (i.e., found by component scanning or explicitly registered). If you call the method on a raw instance of the class (not the Spring-managed proxy), you get a plain new object each time.

> `@Configuration` cannot be `final` — CGLIB subclasses the config class, and Java cannot subclass a `final` class. Spring throws at startup if you annotate a final class with `@Configuration`.

- The CGLIB proxy means `@Configuration` classes must have a no-arg constructor (or Spring must be able to create a subclass via `objenesis`).
- `@Bean` methods in `@Configuration` are overridden by CGLIB; in `@Component` (lite mode) they are plain Java methods — no singleton guarantee for inter-method calls.
- Use `@Import` to compose multiple `@Configuration` classes instead of putting everything in one file.
- `@Configuration(proxyBeanMethods = false)` opts out of CGLIB — same as lite mode, discussed in the next tutorial.
