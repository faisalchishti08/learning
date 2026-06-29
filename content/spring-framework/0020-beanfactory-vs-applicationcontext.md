---
card: spring-framework
gi: 20
slug: beanfactory-vs-applicationcontext
title: BeanFactory vs ApplicationContext
---

## 1. What it is

`BeanFactory` and `ApplicationContext` are both Spring IoC containers, but at different levels of capability:

| Feature | BeanFactory | ApplicationContext |
|---|---|---|
| Bean creation & DI | Yes | Yes (extends BeanFactory) |
| Singleton instantiation | Lazy (on first `getBean()`) | Eager (at `refresh()`) |
| `BeanPostProcessor` auto-detect | **No** — must be registered manually | **Yes** — auto-detected from context |
| `BeanFactoryPostProcessor` auto-detect | **No** | **Yes** |
| Event publishing | **No** | **Yes** (`ApplicationEventPublisher`) |
| i18n / MessageSource | **No** | **Yes** |
| Resource loading | Basic | Full (`ResourcePatternResolver`) |
| Environment / profiles | **No** | **Yes** |

`ApplicationContext` is a superset — it extends `BeanFactory`, so every `BeanFactory` operation works on an `ApplicationContext`. In production you always use `ApplicationContext`.

In one sentence: **`BeanFactory` is the minimal bean registry; `ApplicationContext` is the fully-featured application container — use `ApplicationContext` unless you have an extreme resource constraint.**

## 2. Why & when

**When to use `BeanFactory`:**
- Standalone library that ships Spring as an optional dependency and must minimise classpath size.
- Memory-constrained environments (Android, embedded systems) where eager singleton creation is too expensive at startup.
- Framework internals — Spring itself uses `DefaultListableBeanFactory` as the underlying engine.

**When to use `ApplicationContext` (nearly always):**
- Any web application, REST API, batch job, or CLI tool.
- Whenever you use `@Transactional`, `@Scheduled`, `@Async`, or AOP — these rely on `BeanPostProcessor` auto-detection.
- Whenever you publish or listen for application events.
- Whenever you read properties via `@Value` or `Environment` — both require `ApplicationContext`.

The cost of `ApplicationContext`'s eager initialisation is negligible in modern JVMs; the benefit (fail-fast startup, full feature set) far outweighs it.

## 3. Core concept

`BeanFactory` is the engine room. `ApplicationContext` is the fully staffed ship:

```
BeanFactory  →  stores bean definitions + creates beans on demand
                  +
ApplicationContext adds:
  • BeanFactoryPostProcessor auto-detection (modify definitions before creation)
  • BeanPostProcessor auto-detection       (wrap beans in proxies after creation)
  • MessageSource                           (i18n message resolution)
  • ApplicationEventMulticaster             (event bus)
  • EnvironmentCapable                      (property sources, profiles)
  • ResourcePatternResolver                 (classpath:/**, file: URLs)
  • SmartLifecycle management               (ordered start/stop)
```

**The critical difference — `BeanPostProcessor` auto-detection:**

With raw `BeanFactory` you must call `factory.addBeanPostProcessor(new AutowiredAnnotationBeanPostProcessor())` manually before any `getBean()` call. If you forget, `@Autowired` does nothing. With `ApplicationContext`, any bean that implements `BeanPostProcessor` is automatically detected and applied.

This is why `@Transactional`, `@Scheduled`, `@Cache`, and AOP proxies require `ApplicationContext` — they are implemented via `BeanPostProcessor`s that `ApplicationContext` registers automatically.

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BeanFactory vs ApplicationContext feature comparison with inheritance hierarchy">
  <defs>
    <marker id="a20" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- BeanFactory column -->
  <rect x="10" y="10" width="300" height="48" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="30" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">BeanFactory</text>
  <text x="160" y="48" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getBean  •  containsBean  •  isSingleton  •  getType</text>

  <!-- ApplicationContext column -->
  <rect x="370" y="10" width="300" height="48" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="520" y="30" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>
  <text x="520" y="48" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">extends BeanFactory + all features below</text>

  <!-- Feature rows -->
  <rect x="10"  y="80" width="300" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Lazy init — bean created on first getBean()</text>

  <rect x="370" y="80" width="300" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="520" y="100" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Eager init — all singletons at refresh() ✓</text>

  <rect x="10"  y="120" width="300" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BeanPostProcessor: manual addBeanPostProcessor()</text>

  <rect x="370" y="120" width="300" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="520" y="140" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">BeanPostProcessor: auto-detected from context ✓</text>

  <rect x="10"  y="160" width="300" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">No events, no i18n, no Environment</text>

  <rect x="370" y="160" width="300" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="520" y="180" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Events + i18n + Environment + profiles ✓</text>

  <rect x="10"  y="200" width="300" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="220" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DefaultListableBeanFactory (standalone)</text>

  <rect x="370" y="200" width="300" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="520" y="220" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">AnnotationConfigApplicationContext (common) ✓</text>

  <!-- Middle arrow -->
  <line x1="310" y1="34" x2="368" y2="34" stroke="#6db33f" stroke-width="2" marker-end="url(#a20)"/>
  <text x="339" y="28" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">extends</text>

  <text x="340" y="258" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Use ApplicationContext in all production code. BeanFactory for library/embedded use only.</text>
</svg>

`ApplicationContext` is a proper superset. Every row on the left is supported by `ApplicationContext` too — the right column only lists what's *added*.

## 5. Runnable example

Scenario: a `UserService` that manages user registration. We first wire it through a `BeanFactory`-style container (manual, minimal), then through an `ApplicationContext`-style container (auto BeanPostProcessor, events, environment) — using the same `UserService` class in both.

### Level 1 — Basic

`BeanFactory`-style: manual registration, lazy init, **no** auto-detection of post-processors.

```java
// BFvsAC.java — run with: java BFvsAC.java
import java.util.*;
import java.util.function.*;

public class BFvsAC {

    record User(int id, String name, String email) {}

    interface PasswordEncoder { String encode(String raw); }
    static class BcryptEncoder implements PasswordEncoder {
        public String encode(String raw) { return "bcrypt:" + raw.hashCode(); }
    }

    static class UserService {
        private final PasswordEncoder encoder;
        private final List<User> db = new ArrayList<>();
        private int nextId = 1;

        UserService(PasswordEncoder encoder) { this.encoder = encoder; }

        User register(String name, String email, String password) {
            User u = new User(nextId++, name, email);
            System.out.println("Registered: " + u + " pwd=" + encoder.encode(password));
            return u;
        }
        List<User> findAll() { return Collections.unmodifiableList(db); }
    }

    // --- BeanFactory-style: purely manual ---
    static class MinimalBeanFactory {
        private final Map<Class<?>, Supplier<?>> defs  = new LinkedHashMap<>();
        private final Map<Class<?>, Object>      cache = new LinkedHashMap<>();

        <T> void register(Class<T> type, Supplier<T> factory) { defs.put(type, factory); }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            // No auto post-processors. No events. Lazy only.
            return (T) cache.computeIfAbsent(type, k -> {
                System.out.println("  [LAZY INIT] " + type.getSimpleName());
                return defs.get(k).get();
            });
        }
    }

    public static void main(String[] args) {
        System.out.println("=== BeanFactory-style container ===\n");

        MinimalBeanFactory factory = new MinimalBeanFactory();
        factory.register(PasswordEncoder.class, BcryptEncoder::new);
        factory.register(UserService.class,
            () -> new UserService(factory.getBean(PasswordEncoder.class)));

        System.out.println("-- After registration: nothing created yet --\n");

        UserService users = factory.getBean(UserService.class);
        users.register("alice", "alice@example.com", "secret1");
        users.register("bob",   "bob@example.com",   "secret2");
    }
}
```

How to run: `java BFvsAC.java`

Both beans are created lazily only when `getBean(UserService.class)` is first called. No events, no property resolution, no automatic post-processors — the developer is responsible for everything.

### Level 2 — Intermediate

`ApplicationContext`-style: eager init, automatic `BeanPostProcessor` for logging (analogous to `@Transactional` AOP proxy), and property environment.

```java
// BFvsAC2.java — run with: java BFvsAC2.java
import java.util.*;
import java.util.function.*;

public class BFvsAC2 {

    record User(int id, String name, String email) {}
    interface PasswordEncoder { String encode(String raw); }
    static class BcryptEncoder implements PasswordEncoder {
        public String encode(String raw) { return "bcrypt:" + raw.hashCode(); }
    }

    // BeanPostProcessor — applied automatically in ApplicationContext-style container
    interface BeanPostProcessor {
        Object postProcess(Object bean, String name);
    }

    static class AuditLoggingPostProcessor implements BeanPostProcessor {
        public Object postProcess(Object bean, String name) {
            System.out.println("  [POST-PROCESSOR] Applied audit logging to: " + name);
            return bean;  // real Spring: return CGLIB/JDK proxy here
        }
    }

    static class UserService {
        private final PasswordEncoder encoder;
        private final String maxUsers;
        private int nextId = 1;

        UserService(PasswordEncoder encoder, String maxUsers) {
            this.encoder  = encoder;
            this.maxUsers = maxUsers;
        }

        User register(String name, String email, String password) {
            User u = new User(nextId++, name, email);
            System.out.println("Registered: " + u + " (max=" + maxUsers + ") pwd=" + encoder.encode(password));
            return u;
        }
    }

    // --- ApplicationContext-style: eager, auto post-processors, environment ---
    static class SimpleAppContext {
        private final Map<String, Supplier<?>>  defs       = new LinkedHashMap<>();
        private final Map<String, Object>       singletons = new LinkedHashMap<>();
        private final List<BeanPostProcessor>   postProcs  = new ArrayList<>();
        private final Map<String, String>       env        = new LinkedHashMap<>();

        void setEnv(String key, String value)  { env.put(key, value); }
        String getProperty(String key, String def) { return env.getOrDefault(key, def); }

        <T> void register(String name, Supplier<T> factory) { defs.put(name, factory); }
        void addPostProcessor(BeanPostProcessor pp)         { postProcs.add(pp); }

        // Eager: instantiate all singletons at refresh()
        void refresh() {
            System.out.println("[REFRESH] Instantiating all singletons...");
            for (Map.Entry<String, Supplier<?>> e : defs.entrySet()) {
                Object bean = e.getValue().get();
                for (BeanPostProcessor pp : postProcs) bean = pp.postProcess(bean, e.getKey());
                singletons.put(e.getKey(), bean);
                System.out.println("  Ready: " + e.getKey());
            }
            System.out.println("[REFRESH] Complete — context ready.\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name, Class<T> type) {
            Object b = singletons.get(name);
            if (b == null) throw new RuntimeException("No bean: " + name);
            return type.cast(b);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== ApplicationContext-style container ===\n");

        SimpleAppContext ctx = new SimpleAppContext();
        ctx.setEnv("users.max", "1000");
        ctx.addPostProcessor(new AuditLoggingPostProcessor());  // auto-applied to ALL beans

        ctx.register("passwordEncoder", BcryptEncoder::new);
        ctx.register("userService", () -> new UserService(
            ctx.getBean("passwordEncoder", PasswordEncoder.class),
            ctx.getProperty("users.max", "500")
        ));

        ctx.refresh();  // EAGER: all beans created NOW, post-processors applied

        UserService users = ctx.getBean("userService", UserService.class);
        users.register("alice", "alice@example.com", "secret1");
        users.register("bob",   "bob@example.com",   "secret2");
    }
}
```

How to run: `java BFvsAC2.java`

All beans are created at `refresh()` — before any `getBean()` call. `AuditLoggingPostProcessor` is applied automatically to every bean without manual registration per-bean. `getProperty("users.max", "500")` reads from the environment map — the equivalent of Spring's `@Value("${users.max:500}")`.

### Level 3 — Advanced

Add event publishing to the `ApplicationContext`-style container. `UserService` fires a `UserRegisteredEvent`; an `EmailNotifier` listens — zero coupling between them.

```java
// BFvsAC3.java — run with: java BFvsAC3.java
import java.util.*;
import java.util.function.*;

public class BFvsAC3 {

    record User(int id, String name, String email) {}
    record UserRegisteredEvent(User user) {}

    interface PasswordEncoder { String encode(String raw); }
    static class BcryptEncoder implements PasswordEncoder {
        public String encode(String raw) { return "bcrypt:" + raw.hashCode(); }
    }

    interface ApplicationListener<E> { void onEvent(E event); }

    static class UserService {
        private final PasswordEncoder encoder;
        private Consumer<UserRegisteredEvent> publisher;  // set by context
        private int nextId = 1;

        UserService(PasswordEncoder encoder) { this.encoder = encoder; }
        void setPublisher(Consumer<UserRegisteredEvent> p) { this.publisher = p; }

        User register(String name, String email, String password) {
            User u = new User(nextId++, name, email);
            System.out.println("UserService: registered " + u);
            if (publisher != null) publisher.accept(new UserRegisteredEvent(u));
            return u;
        }
    }

    static class EmailNotifier implements ApplicationListener<UserRegisteredEvent> {
        public void onEvent(UserRegisteredEvent e) {
            System.out.println("  [EMAIL] Welcome email → " + e.user().email());
        }
    }

    // --- Full ApplicationContext-style: eager + post-processors + events + environment ---
    static class FullAppContext {
        private final Map<String, Object>                    beans    = new LinkedHashMap<>();
        private final Map<Class<?>, List<ApplicationListener<?>>> listeners = new HashMap<>();
        private final Map<String, String>                    env      = new HashMap<>();

        void setEnv(String k, String v) { env.put(k, v); }
        String prop(String k, String d) { return env.getOrDefault(k, d); }

        void registerBean(String name, Object bean) { beans.put(name, bean); }

        @SuppressWarnings("unchecked")
        <E> void on(Class<E> type, ApplicationListener<E> l) {
            listeners.computeIfAbsent(type, k -> new ArrayList<>()).add(l);
        }

        @SuppressWarnings("unchecked")
        <E> void publishEvent(E event) {
            List<ApplicationListener<?>> ls = listeners.getOrDefault(event.getClass(), List.of());
            ls.forEach(l -> ((ApplicationListener<E>)l).onEvent(event));
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name, Class<T> type) { return type.cast(beans.get(name)); }
    }

    public static void main(String[] args) {
        System.out.println("=== Full ApplicationContext-style ===\n");

        FullAppContext ctx = new FullAppContext();
        ctx.setEnv("smtp.host", "smtp.example.com");

        // Wire beans
        PasswordEncoder encoder = new BcryptEncoder();
        UserService userService  = new UserService(encoder);
        EmailNotifier notifier   = new EmailNotifier();

        // Wire event publishing into UserService
        userService.setPublisher(ctx::publishEvent);

        // Register beans in context
        ctx.registerBean("passwordEncoder", encoder);
        ctx.registerBean("userService",     userService);
        ctx.registerBean("emailNotifier",   notifier);

        // Register listeners — ApplicationContext auto-discovers @EventListener beans
        ctx.on(UserRegisteredEvent.class, notifier);

        System.out.println("SMTP host: " + ctx.prop("smtp.host", "(none)") + "\n");

        userService.register("alice", "alice@example.com", "secret1");
        System.out.println();
        userService.register("bob", "bob@example.com", "secret2");

        System.out.println("\n=== Context comparison summary ===");
        System.out.println("BeanFactory:       lazy init, manual post-processors, no events");
        System.out.println("ApplicationContext: eager init, auto post-processors, events + env + i18n");
    }
}
```

How to run: `java BFvsAC3.java`

`EmailNotifier` never appears in `UserService`'s constructor. The event bus decouples them. `ctx.publishEvent()` delivers the `UserRegisteredEvent` to all registered listeners — exactly how Spring's `ApplicationContext.publishEvent()` works. The context holds the environment map for property resolution without touching service code.

## 6. Walkthrough

**Level 1 (BeanFactory-style) — lazy init flow:**
```
factory.register("userService", ...)   → stores Supplier, nothing created
factory.getBean(UserService.class)     → cache miss → [LAZY INIT] PasswordEncoder
                                                    → [LAZY INIT] UserService
                                                    → both cached
second getBean(UserService.class)      → cache hit → no re-init
```

**Level 2 (ApplicationContext-style) — eager init at `refresh()`:**
```
ctx.refresh()
  → foreach bean in registration order:
      → "passwordEncoder": BcryptEncoder() created → post-processor applied → cached
      → "userService":     UserService() created   → post-processor applied → cached
  → "[REFRESH] Complete"

ctx.getBean("userService")  → cache hit (already created at refresh)
```

**Level 3 — event flow when `register("alice", ...)` is called:**
```
userService.register("alice", "alice@example.com", "secret1")
  → User(1, "alice", "alice@example.com") created
  → publisher.accept(new UserRegisteredEvent(user))     ← publisher = ctx::publishEvent
      → ctx.publishEvent(event)
          → listeners for UserRegisteredEvent: [emailNotifier]
          → emailNotifier.onEvent(event)
              → "[EMAIL] Welcome email → alice@example.com"
```

No direct reference from `UserService` to `EmailNotifier` anywhere in the class body. The context owns the wiring.

## 7. Gotchas & takeaways

> **`@Transactional`, `@Async`, and all AOP-based annotations require `ApplicationContext`.** They work via `BeanPostProcessor` auto-detection. With a raw `BeanFactory` these annotations are silently ignored unless you manually add `AutowiredAnnotationBeanPostProcessor`, `AsyncAnnotationBeanPostProcessor`, etc.

> **`BeanFactory` eager init: you must call `factory.preInstantiateSingletons()` on `DefaultListableBeanFactory` to force eager creation.** `ApplicationContext.refresh()` does this for you automatically.

- Always use `ApplicationContext` in application code — never `BeanFactory` unless you have measured a startup-time constraint that justifies it.
- `BeanFactory` is still the right type for method parameters in framework code that only needs bean lookup, not the full context.
- `ApplicationContext` is itself a `BeanFactory` — you can always pass it where a `BeanFactory` is expected.
- Spring Boot's `SpringApplication.run()` returns a `ConfigurableApplicationContext` which extends both `ApplicationContext` and `Closeable` — use try-with-resources in non-web tests.
- Profile-specific beans (`@Profile("prod")`) require `ApplicationContext.getEnvironment().setActiveProfiles(...)` before `refresh()` — `BeanFactory` has no profile concept.
