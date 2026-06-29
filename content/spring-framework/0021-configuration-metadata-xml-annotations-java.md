---
card: spring-framework
gi: 21
slug: configuration-metadata-xml-annotations-java
title: Configuration metadata (XML, annotations, Java)
---

## 1. What it is

Spring needs to know which classes are beans and how to wire them. You communicate this through **configuration metadata** — instructions that tell the IoC container what to create, how to create it, and how to connect it.

Spring supports three formats:

| Format | How it works | Introduced |
|---|---|---|
| **XML** | `<bean>` elements in `applicationContext.xml` | Spring 1.x |
| **Annotations** | `@Component`, `@Service`, `@Repository`, `@Controller` on classes | Spring 2.5 |
| **Java config** | `@Configuration` classes with `@Bean` factory methods | Spring 3.0 |

All three produce the same internal result: `BeanDefinition` objects inside `DefaultListableBeanFactory`. The container does not care which format you used — the runtime behaviour is identical.

In one sentence: **Configuration metadata is how you describe your beans to the IoC container, and Spring supports XML, annotation, and Java-class formats interchangeably.**

## 2. Why & when

**XML** was the original approach. Every dependency is explicit, visible in one file, and requires no recompilation to change. The drawback is verbosity — a medium app can have thousands of `<bean>` lines, and the XML is disconnected from the Java class it describes.

**Annotations** move metadata into the class itself (`@Service`, `@Autowired`). Less to maintain, but configuration is now scattered across every source file and cannot be changed without recompiling.

**Java config** (`@Configuration`) gives type-safe, IDE-navigable, refactor-friendly configuration in regular Java. It is the current Spring recommendation. Spring Boot uses it exclusively.

In practice, most modern apps use Java config (`@Configuration` + `@Bean`) for infrastructure beans and annotation scanning (`@ComponentScan`) for application classes. XML survives in legacy systems.

## 3. Core concept

All three formats converge on the same internal model:

```
XML <bean>        ─┐
@Component scan   ─┼──► BeanDefinition (beanClass, scope, deps) ──► container creates bean
@Bean method      ─┘
```

A `BeanDefinition` stores:
- The bean's class
- Its scope (singleton / prototype / etc.)
- Constructor args / property values
- Init and destroy method names
- Whether it is lazy

**XML example:**
```xml
<bean id="orderService" class="com.example.OrderService">
    <constructor-arg ref="emailService"/>
</bean>
```

**Annotation example:**
```java
@Service
public class OrderService {
    @Autowired EmailService email;
}
```

**Java config example:**
```java
@Configuration
public class AppConfig {
    @Bean
    public OrderService orderService(EmailService email) {
        return new OrderService(email);
    }
}
```

All three create an `OrderService` singleton wired with an `EmailService`. The container treats them identically after parsing.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three configuration metadata formats converging to BeanDefinition then container beans">
  <defs>
    <marker id="a21" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- XML -->
  <rect x="10" y="30" width="150" height="52" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="52" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">XML</text>
  <text x="85" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;bean id="..." class="..."/&gt;</text>

  <!-- Annotations -->
  <rect x="10" y="105" width="150" height="52" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="127" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Annotations</text>
  <text x="85" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Component / @Autowired</text>

  <!-- Java config -->
  <rect x="10" y="178" width="150" height="38" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="196" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java Config</text>
  <text x="85" y="211" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@Configuration / @Bean</text>

  <!-- BeanDefinition registry -->
  <rect x="245" y="70" width="170" height="80" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="330" y="95" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">BeanDefinition</text>
  <text x="330" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">beanClass, scope</text>
  <text x="330" y="127" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">constructor-args, properties</text>
  <text x="330" y="141" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">init/destroy methods</text>

  <!-- Arrows to BeanDefinition -->
  <line x1="160" y1="56" x2="243" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a21)"/>
  <line x1="160" y1="131" x2="243" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a21)"/>
  <line x1="160" y1="197" x2="243" y2="140" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a21)"/>

  <!-- Container -->
  <rect x="490" y="85" width="175" height="56" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="577" y="108" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">IoC Container</text>
  <text x="577" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">creates + wires beans</text>

  <line x1="415" y1="110" x2="488" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#a21)"/>
  <text x="451" y="104" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">reads</text>

  <text x="340" y="210" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">All three formats produce identical BeanDefinitions — the container sees no difference</text>
</svg>

XML, annotations, and Java config are parsed into the same `BeanDefinition` model. The container instantiates beans from definitions, not from the format used to declare them.

## 5. Runnable example

Scenario: a notification pipeline (`NotificationService`) wired with an `EmailSender` and an `SmsSender`. We implement the same wiring three ways: XML-style, annotation-style, and Java-config-style — all in plain Java to keep it self-contained.

### Level 1 — Basic

XML-style: metadata is stored in a separate structure (simulating `<bean>` definitions), looked up by name string — no compile-time safety.

```java
// ConfigMetaDemo.java — run with: java ConfigMetaDemo.java
import java.util.*;
import java.util.function.*;

public class ConfigMetaDemo {

    interface Sender { void send(String to, String msg); }
    static class EmailSender implements Sender {
        public void send(String to, String msg) {
            System.out.println("  [EMAIL → " + to + "] " + msg);
        }
    }
    static class SmsSender implements Sender {
        public void send(String to, String msg) {
            System.out.println("  [SMS → " + to + "] " + msg);
        }
    }
    static class NotificationService {
        private final Sender email;
        private final Sender sms;
        NotificationService(Sender email, Sender sms) { this.email = email; this.sms = sms; }
        void notify(String user, String message) {
            email.send(user + "@example.com", message);
            sms.send("+1-555-" + user.hashCode() % 10000, message);
        }
    }

    // --- XML-style metadata: string-keyed bean definitions ---
    static class XmlBeanRegistry {
        private final Map<String, Supplier<Object>> defs  = new LinkedHashMap<>();
        private final Map<String, Object>           cache = new LinkedHashMap<>();

        void define(String name, Supplier<Object> factory) { defs.put(name, factory); }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) {
            return (T) cache.computeIfAbsent(name, k -> defs.get(k).get());
        }
    }

    public static void main(String[] args) {
        System.out.println("=== XML-style configuration metadata ===\n");

        XmlBeanRegistry ctx = new XmlBeanRegistry();
        // Simulates: <bean id="emailSender" class="EmailSender"/>
        ctx.define("emailSender", EmailSender::new);
        // Simulates: <bean id="smsSender"  class="SmsSender"/>
        ctx.define("smsSender",   SmsSender::new);
        // Simulates: <bean id="notificationService" class="NotificationService">
        //              <constructor-arg ref="emailSender"/>
        //              <constructor-arg ref="smsSender"/>
        //            </bean>
        ctx.define("notificationService",
            () -> new NotificationService(
                ctx.getBean("emailSender"),
                ctx.getBean("smsSender")
            )
        );

        NotificationService svc = ctx.getBean("notificationService");
        svc.notify("alice", "Your order shipped!");
        svc.notify("bob",   "Payment confirmed.");
    }
}
```

How to run: `java ConfigMetaDemo.java`

Beans are looked up by string name. Typos cause runtime errors, not compile errors — the main drawback of XML configuration. The wiring is explicit and centralized, but fragile.

### Level 2 — Intermediate

Annotation-style: beans declare themselves (`@Component`) and their dependencies (`@Autowired`). The container scans classes and auto-wires by type — no central registry file.

```java
// ConfigMetaDemo2.java — run with: java ConfigMetaDemo2.java
import java.lang.annotation.*;
import java.util.*;

public class ConfigMetaDemo2 {

    @Retention(RetentionPolicy.RUNTIME) @interface Component  { String value() default ""; }
    @Retention(RetentionPolicy.RUNTIME) @interface Autowired  {}

    interface Sender { void send(String to, String msg); }

    @Component("emailSender")
    static class EmailSender implements Sender {
        public void send(String to, String msg) {
            System.out.println("  [EMAIL → " + to + "] " + msg);
        }
    }

    @Component("smsSender")
    static class SmsSender implements Sender {
        public void send(String to, String msg) {
            System.out.println("  [SMS → " + to + "] " + msg);
        }
    }

    @Component("notificationService")
    static class NotificationService {
        private final Sender email;
        private final Sender sms;

        @Autowired
        NotificationService(Sender email, Sender sms) {
            this.email = email;
            this.sms   = sms;
        }

        void notify(String user, String message) {
            email.send(user + "@example.com", message);
            sms.send("+1-555-" + user.hashCode() % 10000, message);
        }
    }

    // --- Annotation-scanning container ---
    static class AnnotationContainer {
        private final Map<String, Object>  named = new LinkedHashMap<>();
        private final Map<Class<?>, Object> typed = new LinkedHashMap<>();

        void scan(Class<?>... classes) throws Exception {
            // First pass: instantiate all @Component beans using first constructor
            for (Class<?> cls : classes) {
                if (!cls.isAnnotationPresent(Component.class)) continue;
                var ctor = cls.getDeclaredConstructors()[0];
                if (ctor.getParameterCount() == 0) {
                    Object bean = ctor.newInstance();
                    register(cls.getAnnotation(Component.class).value(), cls, bean);
                }
            }
            // Second pass: wire @Autowired constructors using already-created beans
            for (Class<?> cls : classes) {
                if (!cls.isAnnotationPresent(Component.class)) continue;
                for (var ctor : cls.getDeclaredConstructors()) {
                    if (!ctor.isAnnotationPresent(Autowired.class)) continue;
                    Object[] deps = Arrays.stream(ctor.getParameterTypes())
                        .map(typed::get).toArray();
                    Object bean = ctor.newInstance(deps);
                    register(cls.getAnnotation(Component.class).value(), cls, bean);
                }
            }
        }

        void register(String name, Class<?> cls, Object bean) {
            named.put(name, bean);
            for (Class<?> iface : cls.getInterfaces()) typed.put(iface, bean);
            typed.put(cls, bean);
            System.out.println("  [SCAN] registered: " + name);
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) { return (T) typed.get(type); }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Annotation-style configuration metadata ===\n");

        AnnotationContainer ctx = new AnnotationContainer();
        ctx.scan(EmailSender.class, SmsSender.class, NotificationService.class);

        System.out.println();
        NotificationService svc = ctx.getBean(NotificationService.class);
        svc.notify("alice", "Your order shipped!");
        svc.notify("bob",   "Payment confirmed.");
    }
}
```

How to run: `java ConfigMetaDemo2.java`

Beans announce themselves via `@Component` and declare dependencies via `@Autowired`. The container resolves wiring by type — no string names in lookup, no central config file. Adding a new `SmsSender` implementation requires only adding it and possibly a qualifier, not editing an XML file.

### Level 3 — Advanced

Java-config style: a plain `@Configuration` class with `@Bean` methods. Type-safe, IDE-navigable, and still supports conditional wiring and factory logic.

```java
// ConfigMetaDemo3.java — run with: java ConfigMetaDemo3.java
import java.lang.annotation.*;
import java.util.*;
import java.util.function.*;

public class ConfigMetaDemo3 {

    @Retention(RetentionPolicy.RUNTIME) @interface Configuration {}
    @Retention(RetentionPolicy.RUNTIME) @interface Bean { String value() default ""; }

    interface Sender  { void send(String to, String msg); }
    interface Auditor { void audit(String event); }

    static class EmailSender implements Sender {
        private final String host;
        EmailSender(String host) { this.host = host; }
        public void send(String to, String msg) {
            System.out.println("  [EMAIL via " + host + " → " + to + "] " + msg);
        }
    }
    static class SmsSender implements Sender {
        public void send(String to, String msg) {
            System.out.println("  [SMS → " + to + "] " + msg);
        }
    }
    static class DbAuditor implements Auditor {
        public void audit(String event) { System.out.println("  [AUDIT] " + event); }
    }
    static class NotificationService {
        private final Sender  email;
        private final Sender  sms;
        private final Auditor auditor;
        NotificationService(Sender email, Sender sms, Auditor auditor) {
            this.email = email; this.sms = sms; this.auditor = auditor;
        }
        void notify(String user, String message) {
            email.send(user + "@example.com", message);
            sms.send("+1-555-" + Math.abs(user.hashCode()) % 10000, message);
            auditor.audit("notify user=" + user + " msg=" + message);
        }
    }

    // --- Java-config style: @Configuration class with @Bean methods ---
    @Configuration
    static class AppConfig {
        // Factory logic: smtp host from a property (type-safe, IDE-navigable)
        @Bean("emailSender")
        Sender emailSender() { return new EmailSender("smtp.example.com"); }

        @Bean("smsSender")
        Sender smsSender() { return new SmsSender(); }

        @Bean("auditor")
        Auditor auditor() { return new DbAuditor(); }

        // Dependencies declared as method parameters — container injects them
        @Bean("notificationService")
        NotificationService notificationService(Sender emailSender, Sender smsSender, Auditor auditor) {
            return new NotificationService(emailSender, smsSender, auditor);
        }
    }

    // --- Container that processes @Configuration classes ---
    static class JavaConfigContainer {
        private final Map<String, Object>  named = new LinkedHashMap<>();
        private final Map<Class<?>, Object> typed = new LinkedHashMap<>();

        void process(Object config) throws Exception {
            var configClass = config.getClass();
            // Collect all @Bean methods; call no-arg ones first
            var beanMethods = Arrays.stream(configClass.getDeclaredMethods())
                .filter(m -> m.isAnnotationPresent(Bean.class))
                .sorted(Comparator.comparingInt(m -> m.getParameterCount()))
                .toList();

            for (var method : beanMethods) {
                Object[] args = Arrays.stream(method.getParameterTypes())
                    .map(t -> typed.values().stream()
                        .filter(b -> t.isInstance(b)).findFirst()
                        .orElseThrow(() -> new RuntimeException("No bean of type: " + t)))
                    .toArray();
                Object bean = method.invoke(config, args);
                String name = method.getAnnotation(Bean.class).value();
                if (name.isEmpty()) name = method.getName();
                named.put(name, bean);
                typed.put(method.getReturnType(), bean);
                System.out.println("  [JAVA CONFIG] @Bean " + name + " → " + bean.getClass().getSimpleName());
            }
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) typed.entrySet().stream()
                .filter(e -> type.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst()
                .orElseThrow(() -> new RuntimeException("No bean: " + type));
        }
        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) named.get(name); }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Java-config (@Configuration/@Bean) metadata ===\n");

        JavaConfigContainer ctx = new JavaConfigContainer();
        ctx.process(new AppConfig());

        System.out.println();
        NotificationService svc = ctx.getBean(NotificationService.class);
        svc.notify("alice", "Your order shipped!");
        System.out.println();
        svc.notify("bob", "Payment confirmed.");

        System.out.println("\n--- All three formats produce the same runtime beans ---");
        System.out.println("XML: string-keyed, no compile safety, great for legacy");
        System.out.println("Annotations: scattered across classes, minimal config files");
        System.out.println("Java config: type-safe, IDE-navigable, current standard");
    }
}
```

How to run: `java ConfigMetaDemo3.java`

`AppConfig` is a plain Java class. `@Bean` methods are factory methods — you can add conditional logic, read environment variables, or call external services inside them. The container invokes them via reflection and caches the results as singletons. This is exactly what Spring's `AnnotationConfigApplicationContext` does with real `@Configuration` classes.

## 6. Walkthrough

**Level 3 execution — container processing `AppConfig`:**

1. `ctx.process(new AppConfig())` collects all `@Bean`-annotated methods via reflection.
2. Methods are sorted by parameter count (no-arg first). So `emailSender()`, `smsSender()`, `auditor()` run before `notificationService(...)`.
3. `emailSender()` → no params → `new EmailSender("smtp.example.com")` → stored as `"emailSender"` and typed as `Sender`.
4. `smsSender()` → no params → `new SmsSender()` → also stored as `Sender` type (overwrites — real Spring uses qualifiers here).
5. `auditor()` → `new DbAuditor()` → stored as `Auditor`.
6. `notificationService(Sender, Sender, Auditor)` → 3 params → container resolves by type → injects `emailSender`, the last `Sender` (smsSender), and `auditor` → `new NotificationService(...)`.

**`svc.notify("alice", "Your order shipped!")` execution:**
```
notify("alice", "Your order shipped!")
  → email.send("alice@example.com", "Your order shipped!")
      → [EMAIL via smtp.example.com → alice@example.com] Your order shipped!
  → sms.send("+1-555-XXXX", "Your order shipped!")
      → [SMS → +1-555-XXXX] Your order shipped!
  → auditor.audit("notify user=alice msg=Your order shipped!")
      → [AUDIT] notify user=alice msg=Your order shipped!
```

**Data state at each layer:**

| Step | Input | Result |
|---|---|---|
| Container parses `@Bean` methods | `AppConfig` class | 4 `BeanDefinition`-like entries |
| `emailSender()` invoked | none | `EmailSender("smtp.example.com")` |
| `notificationService(...)` invoked | 3 resolved beans | `NotificationService` wired |
| `notify("alice", ...)` called | user + message | email + SMS + audit log outputs |

## 7. Gotchas & takeaways

> **Java config and annotations can be mixed freely.** `@ComponentScan` on a `@Configuration` class activates annotation scanning for `@Component` classes; `@Bean` methods handle infrastructure beans (DataSource, RestTemplate). This hybrid is the standard Spring Boot pattern.

> **XML, annotation, and Java config can coexist in one application** — Spring merges their `BeanDefinition`s into one registry. Use `@ImportResource("classpath:legacy.xml")` in a `@Configuration` class to pull in XML beans.

- Java config (`@Configuration` + `@Bean`) is the current Spring recommendation for new code.
- `@Bean` methods in `@Configuration` classes are proxied by CGLIB so that calling `emailSender()` from within the config returns the same singleton (not a new instance).
- `@ComponentScan(basePackages = "com.example")` tells Spring which packages to scan for `@Component` classes — without it, annotation-based beans are not discovered.
- Prefer constructor injection in `@Bean` method signatures — the container passes the required beans as parameters, maintaining the same DI contract as annotations.
- XML configuration is still valid and fully supported — do not migrate just for the sake of it; migrate when you are already refactoring a component.
