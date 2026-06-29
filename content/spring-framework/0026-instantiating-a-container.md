---
card: spring-framework
gi: 26
slug: instantiating-a-container
title: Instantiating a container
---

## 1. What it is

**Instantiating a container** means choosing the right `ApplicationContext` implementation and calling its constructor (or build method) to create a live, fully-wired Spring IoC container.

Every Spring application starts with one of these constructors:

```java
// XML on the classpath
ApplicationContext ctx =
    new ClassPathXmlApplicationContext("applicationContext.xml");

// XML on the filesystem
ApplicationContext ctx =
    new FileSystemXmlApplicationContext("/etc/app/beans.xml");

// Java config or @Component scan
ApplicationContext ctx =
    new AnnotationConfigApplicationContext(AppConfig.class);

// Spring Boot (wraps the above)
ConfigurableApplicationContext ctx =
    SpringApplication.run(MyApp.class, args);
```

All four produce an `ApplicationContext`. After the constructor returns, all singleton beans are alive, all dependencies are injected, and the container is ready for `getBean()`.

In one sentence: **Instantiating a container means calling the right `ApplicationContext` constructor for your configuration source — XML classpath, XML filesystem, Java config, or Spring Boot — which triggers `refresh()` and delivers a fully-wired context.**

## 2. Why & when

You instantiate a container:

- **At application start** — every Spring app creates exactly one root `ApplicationContext` (or root + child for web apps).
- **In integration tests** — tests that need real Spring wiring create a test context.
- **In tools and scripts** — a command-line tool may create a temporary context to access Spring beans.
- **In framework code** — libraries that need optional Spring integration create a context lazily.

The choice of implementation depends on your configuration format:

| Configuration format | Context to use |
|---|---|
| XML on classpath | `ClassPathXmlApplicationContext` |
| XML on filesystem | `FileSystemXmlApplicationContext` |
| Java `@Configuration` | `AnnotationConfigApplicationContext` |
| Spring Boot | `SpringApplication.run()` |
| Programmatic / mixed | `GenericApplicationContext` |

## 3. Core concept

All `ApplicationContext` implementations share the same constructor contract:

1. Parse configuration (XML, annotations, or Java config) into `BeanDefinition` objects.
2. Call `refresh()` — the 12-step lifecycle that creates all singletons.
3. Return a live context.

The critical implication: **if `refresh()` fails, the constructor throws and no context is returned.** A missing bean, a circular dependency, or a bad property value surfaces as a startup exception — not a runtime error. This fail-fast behaviour is the primary advantage of `ApplicationContext` over raw `BeanFactory`.

```
Constructor called
  → parseConfiguration()     [XML/annotations/Java config → BeanDefinitions]
  → refresh()
      → postProcessBeanFactory()
      → registerBeanPostProcessors()
      → initMessageSource()
      → finishBeanFactoryInitialization()  ← all singletons created HERE
      → ContextRefreshedEvent fired
  → constructor returns
```

If any singleton fails to wire, `finishBeanFactoryInitialization()` throws `BeanCreationException`, the whole `refresh()` aborts, and you get a clear stack trace.

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four ApplicationContext constructors converging to refresh and live container">
  <defs>
    <marker id="a26" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Four constructors -->
  <rect x="10" y="10" width="175" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="97" y="33" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ClassPathXmlApplicationContext</text>

  <rect x="10" y="60" width="175" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="97" y="83" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">FileSystemXmlApplicationContext</text>

  <rect x="10" y="110" width="175" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="97" y="133" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">AnnotationConfigApplicationContext</text>

  <rect x="10" y="160" width="175" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="97" y="183" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">SpringApplication.run() [Boot]</text>

  <!-- refresh() block -->
  <rect x="265" y="75" width="170" height="70" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="350" y="98" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">refresh()</text>
  <text x="350" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">parse → postProcess</text>
  <text x="350" y="131" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">finishBeanFactoryInit</text>

  <line x1="185" y1="28"  x2="263" y2="95"  stroke="#8b949e" stroke-width="1.5" marker-end="url(#a26)"/>
  <line x1="185" y1="78"  x2="263" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a26)"/>
  <line x1="185" y1="128" x2="263" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a26)"/>
  <line x1="185" y1="178" x2="263" y2="125" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a26)"/>

  <!-- Live context -->
  <rect x="510" y="80" width="160" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="590" y="105" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Live Context</text>
  <text x="590" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">singletons ready</text>

  <line x1="435" y1="110" x2="508" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#a26)"/>

  <!-- Failure path -->
  <rect x="265" y="175" width="170" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="198" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BeanCreationException → thrown</text>
  <line x1="350" y1="145" x2="350" y2="173" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#a26)"/>
  <text x="390" y="165" fill="#8b949e" font-size="8" font-family="sans-serif">on failure</text>
</svg>

All four constructors feed into the same `refresh()` lifecycle. On success the live context is returned. On failure `BeanCreationException` propagates out of the constructor.

## 5. Runnable example

Scenario: a payments gateway application that boots with a `PaymentService` and `AuditLogger`. We evolve from the minimal single-bean context to a multi-config context with fail-fast error detection.

### Level 1 — Basic

The simplest container: one `@Configuration` class, one bean, one `getBean()` call.

```java
// ContainerInstDemo.java — run with: java ContainerInstDemo.java
import java.lang.annotation.*;
import java.util.*;

public class ContainerInstDemo {

    @Retention(RetentionPolicy.RUNTIME) @interface Configuration {}
    @Retention(RetentionPolicy.RUNTIME) @interface Bean {}

    record Payment(int id, String payer, double amount) {}

    static class PaymentService {
        private int nextId = 100;
        Payment process(String payer, double amount) {
            Payment p = new Payment(nextId++, payer, amount);
            System.out.println("  [PAYMENT] " + p);
            return p;
        }
    }

    @Configuration
    static class AppConfig {
        @Bean PaymentService paymentService() { return new PaymentService(); }
    }

    // --- Minimal ApplicationContext instantiation simulation ---
    static class AppCtx {
        private final Map<Class<?>, Object> beans = new LinkedHashMap<>();

        AppCtx(Class<?> configClass) throws Exception {
            System.out.println("[CTX] Instantiating container from: " + configClass.getSimpleName());
            Object config = configClass.getDeclaredConstructors()[0].newInstance();
            for (var m : configClass.getDeclaredMethods()) {
                if (!m.isAnnotationPresent(Bean.class)) continue;
                Object bean = m.invoke(config);
                beans.put(m.getReturnType(), bean);
                System.out.println("  @Bean ready: " + m.getReturnType().getSimpleName());
            }
            System.out.println("[CTX] refresh() complete — container live\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) beans.entrySet().stream()
                .filter(e -> type.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst()
                .orElseThrow(() -> new RuntimeException("No bean: " + type.getSimpleName()));
        }
    }

    public static void main(String[] args) throws Exception {
        // One line to instantiate the container — mirrors:
        // ApplicationContext ctx = new AnnotationConfigApplicationContext(AppConfig.class);
        AppCtx ctx = new AppCtx(AppConfig.class);

        PaymentService svc = ctx.getBean(PaymentService.class);
        svc.process("alice", 125.00);
        svc.process("bob",   250.00);
    }
}
```

How to run: `java ContainerInstDemo.java`

`new AppCtx(AppConfig.class)` mirrors `new AnnotationConfigApplicationContext(AppConfig.class)`. By the time the constructor returns, `paymentService` is a fully initialized singleton. The calling code just calls `getBean()` — it never knows how the bean was created.

### Level 2 — Intermediate

Multiple config classes: split infrastructure (`InfraConfig`) from application beans (`AppConfig`). The container merges both at instantiation time.

```java
// ContainerInstDemo2.java — run with: java ContainerInstDemo2.java
import java.lang.annotation.*;
import java.util.*;

public class ContainerInstDemo2 {

    @Retention(RetentionPolicy.RUNTIME) @interface Configuration {}
    @Retention(RetentionPolicy.RUNTIME) @interface Bean {}

    record Payment(int id, String payer, double amount) {}

    static class AuditLogger {
        private final List<String> log = new ArrayList<>();
        void log(String event) {
            log.add(event);
            System.out.println("  [AUDIT] " + event);
        }
        List<String> getLog() { return Collections.unmodifiableList(log); }
    }

    static class PaymentService {
        private final AuditLogger audit;
        private int nextId = 100;
        PaymentService(AuditLogger audit) { this.audit = audit; }
        Payment process(String payer, double amount) {
            Payment p = new Payment(nextId++, payer, amount);
            System.out.println("  [PAYMENT] " + p);
            audit.log("payment id=" + p.id() + " payer=" + payer + " amount=" + amount);
            return p;
        }
    }

    @Configuration
    static class InfraConfig {
        @Bean AuditLogger auditLogger() { return new AuditLogger(); }
    }

    @Configuration
    static class AppConfig {
        @Bean PaymentService paymentService(AuditLogger audit) {
            return new PaymentService(audit);
        }
    }

    // --- Multi-config container ---
    static class MultiConfigCtx {
        private final Map<Class<?>, Object> typed = new LinkedHashMap<>();
        private final Map<String,   Object> named = new LinkedHashMap<>();

        MultiConfigCtx(Object... configs) throws Exception {
            System.out.println("[CTX] Instantiating container from " + configs.length + " config(s)...");
            // Pass 1: collect all @Bean definitions and create no-arg beans
            List<Object[]> deferred = new ArrayList<>();
            for (Object config : configs) {
                for (var m : config.getClass().getDeclaredMethods()) {
                    if (!m.isAnnotationPresent(Bean.class)) continue;
                    if (m.getParameterCount() == 0) {
                        Object bean = m.invoke(config);
                        register(m.getName(), m.getReturnType(), bean);
                    } else {
                        deferred.add(new Object[]{config, m});
                    }
                }
            }
            // Pass 2: wire beans with dependencies
            for (Object[] entry : deferred) {
                Object config = entry[0];
                var m = (java.lang.reflect.Method) entry[1];
                Object[] deps = Arrays.stream(m.getParameterTypes())
                    .map(t -> typed.entrySet().stream()
                        .filter(e -> t.isAssignableFrom(e.getKey()))
                        .map(Map.Entry::getValue).findFirst()
                        .orElseThrow(() -> new RuntimeException("Missing dep: " + t.getSimpleName())))
                    .toArray();
                register(m.getName(), m.getReturnType(), m.invoke(config, deps));
            }
            System.out.println("[CTX] refresh() complete — container live\n");
        }

        void register(String name, Class<?> type, Object bean) {
            typed.put(type, bean);
            named.put(name, bean);
            System.out.println("  @Bean ready: " + name + " (" + bean.getClass().getSimpleName() + ")");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) typed.entrySet().stream()
                .filter(e -> type.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst()
                .orElseThrow();
        }
    }

    public static void main(String[] args) throws Exception {
        // Mirrors: new AnnotationConfigApplicationContext(InfraConfig.class, AppConfig.class)
        MultiConfigCtx ctx = new MultiConfigCtx(new InfraConfig(), new AppConfig());

        PaymentService svc = ctx.getBean(PaymentService.class);
        svc.process("alice", 125.00);
        svc.process("bob",   4999.99);

        System.out.println("\nAudit log: " + ctx.getBean(AuditLogger.class).getLog());
    }
}
```

How to run: `java ContainerInstDemo2.java`

`InfraConfig` provides `AuditLogger`. `AppConfig` provides `PaymentService` that depends on `AuditLogger`. The multi-config container resolves cross-config dependencies by resolving no-arg beans first, then wired beans. The calling code sees one context — the split across configs is invisible.

### Level 3 — Advanced

Fail-fast: container instantiation detects a missing dependency and throws at startup, before the application serves any requests.

```java
// ContainerInstDemo3.java — run with: java ContainerInstDemo3.java
import java.lang.annotation.*;
import java.util.*;

public class ContainerInstDemo3 {

    @Retention(RetentionPolicy.RUNTIME) @interface Configuration {}
    @Retention(RetentionPolicy.RUNTIME) @interface Bean {}

    record Payment(int id, String payer, double amount) {}

    static class FraudChecker {
        boolean isFraud(double amount) { return amount > 9000.0; }
    }

    static class AuditLogger {
        void log(String e) { System.out.println("  [AUDIT] " + e); }
    }

    // Requires BOTH FraudChecker AND AuditLogger
    static class PaymentService {
        private final FraudChecker checker;
        private final AuditLogger  audit;
        private int nextId = 1;
        PaymentService(FraudChecker checker, AuditLogger audit) {
            this.checker = checker; this.audit = audit;
        }
        Payment process(String payer, double amount) {
            if (checker.isFraud(amount)) {
                audit.log("FRAUD BLOCKED payer=" + payer + " amount=" + amount);
                throw new RuntimeException("Payment blocked: fraud detected");
            }
            Payment p = new Payment(nextId++, payer, amount);
            System.out.println("  [PAYMENT] " + p);
            audit.log("processed id=" + p.id());
            return p;
        }
    }

    // --- Missing AuditLogger → container throws at startup ---
    @Configuration
    static class IncompleteConfig {
        @Bean FraudChecker fraudChecker() { return new FraudChecker(); }
        // AuditLogger intentionally omitted!
        @Bean PaymentService paymentService(FraudChecker checker, AuditLogger audit) {
            return new PaymentService(checker, audit);
        }
    }

    // --- Complete config ---
    @Configuration
    static class CompleteConfig {
        @Bean FraudChecker fraudChecker() { return new FraudChecker(); }
        @Bean AuditLogger  auditLogger()  { return new AuditLogger();  }
        @Bean PaymentService paymentService(FraudChecker checker, AuditLogger audit) {
            return new PaymentService(checker, audit);
        }
    }

    static class FailFastCtx {
        private final Map<Class<?>, Object> typed = new LinkedHashMap<>();

        FailFastCtx(Object config) throws Exception {
            System.out.println("[CTX] Starting refresh with: " + config.getClass().getSimpleName());
            List<Object[]> deferred = new ArrayList<>();
            for (var m : config.getClass().getDeclaredMethods()) {
                if (!m.isAnnotationPresent(Bean.class)) continue;
                if (m.getParameterCount() == 0) {
                    Object bean = m.invoke(config);
                    typed.put(m.getReturnType(), bean);
                    System.out.println("  Ready: " + m.getReturnType().getSimpleName());
                } else {
                    deferred.add(new Object[]{config, m});
                }
            }
            for (Object[] entry : deferred) {
                var m = (java.lang.reflect.Method) entry[1];
                Object[] deps = Arrays.stream(m.getParameterTypes())
                    .map(t -> {
                        Object dep = typed.entrySet().stream()
                            .filter(e -> t.isAssignableFrom(e.getKey()))
                            .map(Map.Entry::getValue).findFirst().orElse(null);
                        if (dep == null) throw new RuntimeException(
                            "BeanCreationException: No qualifying bean of type '"
                            + t.getSimpleName() + "' required by '"
                            + m.getReturnType().getSimpleName() + "'");
                        return dep;
                    }).toArray();
                Object bean = m.invoke(config, deps);
                typed.put(m.getReturnType(), bean);
                System.out.println("  Ready: " + m.getReturnType().getSimpleName());
            }
            System.out.println("[CTX] refresh() complete\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) typed.entrySet().stream()
                .filter(e -> type.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst()
                .orElseThrow();
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Attempt 1: Incomplete config (missing AuditLogger) ===");
        try {
            FailFastCtx ctx = new FailFastCtx(new IncompleteConfig());
            ctx.getBean(PaymentService.class).process("alice", 100.0);
        } catch (Exception e) {
            System.out.println("  STARTUP FAILED: " + e.getMessage());
        }

        System.out.println("\n=== Attempt 2: Complete config ===");
        try {
            FailFastCtx ctx = new FailFastCtx(new CompleteConfig());
            PaymentService svc = ctx.getBean(PaymentService.class);
            svc.process("alice", 250.00);
            System.out.println();
            try { svc.process("mallory", 15000.00); }
            catch (RuntimeException e) { System.out.println("  " + e.getMessage()); }
        } catch (Exception e) {
            System.out.println("  UNEXPECTED: " + e.getMessage());
        }
    }
}
```

How to run: `java ContainerInstDemo3.java`

`IncompleteConfig` omits `AuditLogger`. The container throws at startup — before any `process()` call can happen. `CompleteConfig` succeeds. This fail-fast property means misconfigured apps crash at boot, not silently at the point when a user triggers the broken code path.

## 6. Walkthrough

**Level 3 — fail-fast container instantiation:**

**Attempt 1 (incomplete config):**
```
FailFastCtx(new IncompleteConfig())
  → Pass 1 (no-arg beans): fraudChecker() → FraudChecker ready
  → Pass 2 (wired beans): paymentService(FraudChecker, AuditLogger)
      → resolve FraudChecker → found ✓
      → resolve AuditLogger  → NOT FOUND → RuntimeException:
          "BeanCreationException: No qualifying bean of type 'AuditLogger'
           required by 'PaymentService'"
  Constructor throws → no context returned
```

**Attempt 2 (complete config):**
```
FailFastCtx(new CompleteConfig())
  → Pass 1: fraudChecker() → FraudChecker ready
             auditLogger()  → AuditLogger ready
  → Pass 2: paymentService(FraudChecker, AuditLogger)
      → resolve FraudChecker → found ✓
      → resolve AuditLogger  → found ✓
      → new PaymentService(fraudChecker, auditLogger) → ready
  → "[CTX] refresh() complete"
```

**`svc.process("mallory", 15000.00):`**
```
process("mallory", 15000.00)
  → checker.isFraud(15000.00) → 15000 > 9000 → true
  → audit.log("FRAUD BLOCKED payer=mallory amount=15000.0")
      → "[AUDIT] FRAUD BLOCKED payer=mallory amount=15000.0"
  → throw RuntimeException("Payment blocked: fraud detected")
```

**Container instantiation path summary:**

| Step | Action | Output |
|---|---|---|
| Parse config | read `@Bean` methods | list of `BeanDefinition` entries |
| No-arg beans | invoke zero-param `@Bean` methods | `FraudChecker`, `AuditLogger` singletons |
| Wired beans | resolve deps + invoke | `PaymentService` singleton |
| Refresh complete | all singletons cached | context returned to caller |
| Missing dep | dep not in context | `BeanCreationException` thrown from constructor |

## 7. Gotchas & takeaways

> **If the container constructor throws, you have no context.** Catch the exception at the outermost entry point (e.g., `public static void main`) and treat it as a fatal startup error. There is no partial context to clean up.

> **Container instantiation is synchronous and single-threaded by default.** All singletons are created on the thread that calls the constructor. For extremely slow beans (network calls in `@PostConstruct`), startup can take seconds. Use `@Lazy` on those beans to defer creation until first use.

- Always close the context when the application exits: `((ConfigurableApplicationContext) ctx).close()` triggers `@PreDestroy` and `DisposableBean` callbacks for all singletons.
- In unit tests, create a fresh context per test class (not per test method) — context creation is expensive. Spring's `@SpringJUnitConfig` caches the context automatically.
- `SpringApplication.run()` registers a JVM shutdown hook automatically; manual `AnnotationConfigApplicationContext` does not — call `ctx.registerShutdownHook()` to get the same behaviour.
- Multiple `ApplicationContext` instances can coexist (parent-child hierarchy). Child beans can see parent beans; parent beans cannot see child beans — used by Spring MVC (root context + dispatcher context).
- If you need the context to survive without blocking the main thread (e.g., web app), call `ctx.registerShutdownHook()` and let the web server's thread pool keep the JVM alive.
