---
card: spring-framework
gi: 71
slug: initializingbean-afterpropertiesset
title: InitializingBean / afterPropertiesSet()
---

## 1. What it is

`InitializingBean` is a Spring interface with one method — `afterPropertiesSet()` — that Spring calls **after all properties have been injected** into the bean. It is one of three ways to hook into the init phase; the others are `@PostConstruct` (fires first) and XML `init-method` (fires last).

```java
import org.springframework.beans.factory.InitializingBean;

@Component
public class ReportGenerator implements InitializingBean {

    @Value("${reports.output-dir}")
    private String outputDir;

    @Override
    public void afterPropertiesSet() throws Exception {
        // runs AFTER @Value injection, AFTER @Autowired wiring
        Path dir = Paths.get(outputDir);
        if (!Files.exists(dir)) Files.createDirectories(dir);
        System.out.println("Report output dir ready: " + dir);
    }
}
```

In one sentence: **`InitializingBean.afterPropertiesSet()` is a Spring-native init callback invoked after all bean properties are set, used to validate configuration, open resources, or perform post-injection setup — fires after `@PostConstruct` and before `init-method`.**

## 2. Why & when

Use `afterPropertiesSet()` when:

- You are writing Spring infrastructure code or a library bean where JSR-250 annotations (`@PostConstruct`) are less appropriate — Spring Framework itself uses `InitializingBean` widely (e.g., `AbstractBeanFactory`, `JdbcTemplate`, `LocalContainerEntityManagerFactoryBean`).
- You need to validate that injected properties are consistent with each other (multi-field validation that can't be done with `@Value` alone).
- You want IDE-enforced implementation — the interface keeps the method signature contract explicit.

Prefer `@PostConstruct` for application-level beans to avoid coupling to Spring's API. Use `InitializingBean` for framework-level beans or when you want a compile-time guarantee that the method is correctly named and throws `Exception`.

## 3. Core concept

```
Bean initialization sequence:
  1. Constructor called
  2. @Autowired / @Value dependencies injected (BeanPostProcessor phase)
  3. @PostConstruct methods (CommonAnnotationBeanPostProcessor)    ← fires FIRST
  4. InitializingBean.afterPropertiesSet()                        ← fires SECOND
  5. init-method="..." (XML/annotation attribute)                 ← fires LAST
  6. Bean ready for use

When to call afterPropertiesSet():
  ✓ All @Value properties are set     → safe to read @Value fields
  ✓ All @Autowired beans are wired    → safe to call injected collaborators
  ✓ XML <property> values are applied → safe to read XML-configured fields
  ✗ ApplicationContext not yet full   → not all sibling beans may be started
     (use SmartLifecycle for that)

Exception handling:
  afterPropertiesSet() throws Exception → checked exception aborts context startup
  BeanInitializationException wraps it  → context fails to start, app exits
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="InitializingBean position in Spring init sequence">
  <defs>
    <marker id="a71" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="188" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">InitializingBean fires in the middle of the three init mechanisms</text>

  <!-- Boxes -->
  <rect x="10"  y="35" width="80" height="38" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="50"  y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">① construct</text>
  <text x="50"  y="64" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">new Bean()</text>

  <rect x="105" y="35" width="100" height="38" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">② inject</text>
  <text x="155" y="64" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">@Autowired / @Value</text>

  <rect x="220" y="35" width="120" height="38" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="280" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">③ @PostConstruct</text>
  <text x="280" y="64" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">JSR-250, fires FIRST</text>

  <rect x="355" y="35" width="135" height="38" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="422" y="52" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">④ afterPropertiesSet()</text>
  <text x="422" y="64" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">InitializingBean ← YOU ARE HERE</text>

  <rect x="505" y="35" width="90" height="38" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="550" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">⑤ init-method</text>
  <text x="550" y="64" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">XML attr, fires LAST</text>

  <!-- Arrows -->
  <line x1="90"  y1="54" x2="103" y2="54" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a71)"/>
  <line x1="205" y1="54" x2="218" y2="54" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a71)"/>
  <line x1="340" y1="54" x2="353" y2="54" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a71)"/>
  <line x1="490" y1="54" x2="503" y2="54" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a71)"/>

  <!-- Comparison table -->
  <rect x="10" y="90" width="655" height="90" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="108" fill="#8b949e" font-size="9" font-family="monospace">Mechanism          Order   Coupling    Exception    Typical use</text>
  <line x1="12" y1="112" x2="662" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="22" y="127" fill="#8b949e" font-size="9" font-family="monospace">@PostConstruct     1st     JSR-250     ✓ (wrapped)  Application beans</text>
  <text x="22" y="142" fill="#6db33f" font-size="9" font-family="monospace">afterPropertiesSet 2nd     Spring API  ✓ (direct)   Framework/infra beans</text>
  <text x="22" y="157" fill="#8b949e" font-size="9" font-family="monospace">init-method=""     3rd     None        ✓ (wrapped)  Legacy / XML config</text>
  <text x="22" y="172" fill="#79c0ff" font-size="8" font-family="sans-serif">All three may coexist; Spring calls them in order 1–2–3 on the same bean.</text>
</svg>

`afterPropertiesSet()` sits between `@PostConstruct` (first) and `init-method` (last) in the init chain. It couples your class to Spring's API; `@PostConstruct` does not.

## 5. Runnable example

Scenario: a `DataSourceValidator` that checks a JDBC URL format and minimum pool size after injection — fails context startup if configuration is invalid.

### Level 1 — Basic

Minimal `InitializingBean` implementation: validate a required config property.

```java
// InitializingBeanDemo.java — run with: java InitializingBeanDemo.java

public class InitializingBeanDemo {

    // ── simulated Spring interface ────────────────────────────────────
    interface InitializingBean { void afterPropertiesSet() throws Exception; }

    static class DataSourceValidator implements InitializingBean {
        private String jdbcUrl;
        private int    minPoolSize;

        void setJdbcUrl(String jdbcUrl)           { this.jdbcUrl = jdbcUrl; }
        void setMinPoolSize(int minPoolSize)       { this.minPoolSize = minPoolSize; }

        @Override
        public void afterPropertiesSet() throws Exception {
            System.out.println("[afterPropertiesSet] validating DataSource config...");
            if (jdbcUrl == null || !jdbcUrl.startsWith("jdbc:"))
                throw new IllegalStateException("jdbcUrl must start with 'jdbc:' — got: " + jdbcUrl);
            if (minPoolSize < 1)
                throw new IllegalStateException("minPoolSize must be >= 1 — got: " + minPoolSize);
            System.out.println("[afterPropertiesSet] OK — url=" + jdbcUrl + " minPoolSize=" + minPoolSize);
        }

        String status() { return "DataSource[url=" + jdbcUrl + ",min=" + minPoolSize + "]"; }
    }

    // ── simulated container ───────────────────────────────────────────
    static DataSourceValidator createBean(String url, int min) throws Exception {
        DataSourceValidator bean = new DataSourceValidator();
        bean.setJdbcUrl(url);          // ② inject
        bean.setMinPoolSize(min);      // ② inject
        bean.afterPropertiesSet();     // ④ Spring calls this
        return bean;
    }

    public static void main(String[] args) {
        System.out.println("=== Valid config ===");
        try {
            DataSourceValidator ds = createBean("jdbc:mysql://localhost:3306/mydb", 5);
            System.out.println("[READY] " + ds.status());
        } catch (Exception e) {
            System.out.println("[FAIL] " + e.getMessage());
        }

        System.out.println("\n=== Invalid URL (no jdbc: prefix) ===");
        try {
            createBean("mysql://localhost:3306/mydb", 5);
        } catch (Exception e) {
            System.out.println("[FAIL — expected] " + e.getMessage());
        }

        System.out.println("\n=== Invalid pool size ===");
        try {
            createBean("jdbc:postgresql://host/db", 0);
        } catch (Exception e) {
            System.out.println("[FAIL — expected] " + e.getMessage());
        }
    }
}
```

How to run: `java InitializingBeanDemo.java`

`afterPropertiesSet()` validates `jdbcUrl` starts with `"jdbc:"` and `minPoolSize >= 1`. Invalid config throws `IllegalStateException` — in a real Spring context this aborts startup. Valid config prints `[READY]`.

### Level 2 — Intermediate

`InitializingBean` with multi-field cross-validation and resource setup: open a thread pool sized to configuration.

```java
// InitializingBeanDemo2.java — run with: java InitializingBeanDemo2.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class InitializingBeanDemo2 {

    interface InitializingBean { void afterPropertiesSet() throws Exception; }
    interface DisposableBean   { void destroy()            throws Exception; }

    static class AsyncEmailSender implements InitializingBean, DisposableBean {
        private String smtpHost;
        private int    smtpPort;
        private int    workerThreads;
        private String fromAddress;

        // set by injection
        void setSmtpHost(String v)     { this.smtpHost      = v; }
        void setSmtpPort(int v)        { this.smtpPort       = v; }
        void setWorkerThreads(int v)   { this.workerThreads  = v; }
        void setFromAddress(String v)  { this.fromAddress    = v; }

        private ExecutorService executor;
        private final AtomicInteger sent = new AtomicInteger();

        @Override
        public void afterPropertiesSet() throws Exception {
            System.out.println("[afterPropertiesSet] validating AsyncEmailSender...");

            // cross-field validation
            if (smtpHost == null || smtpHost.isBlank())
                throw new IllegalStateException("smtpHost is required");
            if (smtpPort < 1 || smtpPort > 65535)
                throw new IllegalStateException("smtpPort out of range: " + smtpPort);
            if (workerThreads < 1 || workerThreads > 20)
                throw new IllegalStateException("workerThreads must be 1–20: " + workerThreads);
            if (fromAddress == null || !fromAddress.contains("@"))
                throw new IllegalStateException("fromAddress invalid: " + fromAddress);

            // resource setup — safe because all fields are injected
            executor = Executors.newFixedThreadPool(workerThreads,
                r -> { Thread t = new Thread(r, "email-worker"); t.setDaemon(true); return t; });

            System.out.printf("[afterPropertiesSet] OK — smtp=%s:%d from=%s workers=%d%n",
                smtpHost, smtpPort, fromAddress, workerThreads);
        }

        Future<String> send(String to, String subject) {
            if (executor == null) throw new IllegalStateException("not initialised");
            return executor.submit(() -> {
                Thread.sleep(10); // simulate send latency
                int n = sent.incrementAndGet();
                System.out.printf("  [SENT #%d] to=%s subject='%s' via %s:%d%n",
                    n, to, subject, smtpHost, smtpPort);
                return "ok:" + n;
            });
        }

        @Override
        public void destroy() {
            System.out.println("[destroy] shutting down executor, sent=" + sent.get());
            executor.shutdownNow();
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Valid config ===");
        AsyncEmailSender sender = new AsyncEmailSender();
        sender.setSmtpHost("smtp.example.com");
        sender.setSmtpPort(587);
        sender.setWorkerThreads(3);
        sender.setFromAddress("noreply@example.com");
        sender.afterPropertiesSet();

        var f1 = sender.send("alice@example.com", "Welcome");
        var f2 = sender.send("bob@example.com",   "Order shipped");
        var f3 = sender.send("carol@example.com", "Password reset");
        System.out.println("[RESULTS] " + f1.get() + " " + f2.get() + " " + f3.get());
        sender.destroy();

        System.out.println("\n=== Invalid fromAddress ===");
        try {
            AsyncEmailSender bad = new AsyncEmailSender();
            bad.setSmtpHost("smtp.example.com");
            bad.setSmtpPort(587);
            bad.setWorkerThreads(3);
            bad.setFromAddress("not-an-email");
            bad.afterPropertiesSet();
        } catch (IllegalStateException e) {
            System.out.println("[FAIL — expected] " + e.getMessage());
        }
    }
}
```

How to run: `java InitializingBeanDemo2.java`

`afterPropertiesSet()` runs cross-field validation (all four fields depend on each other) then creates the thread pool. The pool is ready immediately when `send()` is called because init is complete before the bean is used. Invalid `fromAddress` aborts before the pool is created — no leaked threads.

### Level 3 — Advanced

Framework-style bean: `afterPropertiesSet()` performs type-checking, wires sub-components, and verifies a dependency implements the right contract.

```java
// InitializingBeanDemo3.java — run with: java InitializingBeanDemo3.java
import java.util.*;
import java.util.function.*;

public class InitializingBeanDemo3 {

    interface InitializingBean   { void afterPropertiesSet() throws Exception; }
    interface MessageConverter<T> { T convert(String raw);   String name(); }
    interface MessageSink         { void accept(Object msg); }

    // ── framework bean: MessagePipeline ───────────────────────────────
    static class MessagePipeline<T> implements InitializingBean {
        private MessageConverter<T> converter;   // injected
        private MessageSink         sink;         // injected
        private String              pipelineName;
        private int                 maxBatchSize = 100;

        void setConverter(MessageConverter<T> v)  { this.converter     = v; }
        void setSink(MessageSink v)               { this.sink          = v; }
        void setPipelineName(String v)            { this.pipelineName  = v; }
        void setMaxBatchSize(int v)               { this.maxBatchSize  = v; }

        private final List<T> buffer = new ArrayList<>();

        @Override
        public void afterPropertiesSet() throws Exception {
            System.out.println("[afterPropertiesSet] initialising pipeline '" + pipelineName + "'");

            // required dependency checks
            Objects.requireNonNull(converter, "converter is required");
            Objects.requireNonNull(sink,      "sink is required");
            if (pipelineName == null || pipelineName.isBlank())
                throw new IllegalStateException("pipelineName is required");
            if (maxBatchSize < 1 || maxBatchSize > 10_000)
                throw new IllegalStateException("maxBatchSize must be 1–10000: " + maxBatchSize);

            // verify converter produces the right type at init time, not at first message
            String testInput = "__init_probe__";
            try {
                T sample = converter.convert(testInput);
                System.out.printf("[afterPropertiesSet] converter '%s' probe OK → %s%n",
                    converter.name(), sample.getClass().getSimpleName());
            } catch (Exception e) {
                throw new IllegalStateException("converter '" + converter.name()
                    + "' failed probe: " + e.getMessage(), e);
            }

            // pre-allocate buffer capacity
            buffer.ensureCapacity(maxBatchSize);
            System.out.printf("[afterPropertiesSet] pipeline '%s' ready (maxBatch=%d converter=%s)%n",
                pipelineName, maxBatchSize, converter.name());
        }

        void receive(String rawMessage) {
            T converted = converter.convert(rawMessage);
            buffer.add(converted);
            if (buffer.size() >= maxBatchSize) flush();
        }

        void flush() {
            if (buffer.isEmpty()) return;
            System.out.printf("[FLUSH] pipeline='%s' batch=%d items%n", pipelineName, buffer.size());
            buffer.forEach(sink::accept);
            buffer.clear();
        }
    }

    // ── application beans ─────────────────────────────────────────────
    static class JsonOrderConverter implements MessageConverter<Map<String, Object>> {
        @Override
        public Map<String, Object> convert(String raw) {
            if (raw.startsWith("__init_probe__")) return Map.of("probe", true);
            // simplified JSON parse — just split key=value for demo
            Map<String, Object> m = new LinkedHashMap<>();
            for (String kv : raw.replaceAll("[{}\" ]", "").split(","))
                if (kv.contains(":")) { String[] p = kv.split(":", 2); m.put(p[0], p[1]); }
            return m;
        }
        @Override public String name() { return "JsonOrderConverter"; }
    }

    static class DatabaseSink implements MessageSink {
        private final List<Object> stored = new ArrayList<>();
        @Override public void accept(Object msg) {
            stored.add(msg);
            System.out.println("  [DB INSERT] " + msg);
        }
        int count() { return stored.size(); }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Valid pipeline ===");
        DatabaseSink sink = new DatabaseSink();

        MessagePipeline<Map<String, Object>> pipeline = new MessagePipeline<>();
        pipeline.setPipelineName("order-ingest");
        pipeline.setConverter(new JsonOrderConverter());
        pipeline.setSink(sink);
        pipeline.setMaxBatchSize(3);
        pipeline.afterPropertiesSet();

        System.out.println();
        pipeline.receive("{\"id\":\"1\",\"item\":\"book\",\"qty\":\"2\"}");
        pipeline.receive("{\"id\":\"2\",\"item\":\"pen\",\"qty\":\"5\"}");
        pipeline.receive("{\"id\":\"3\",\"item\":\"notebook\",\"qty\":\"1\"}");
        // batch full → auto-flush
        pipeline.receive("{\"id\":\"4\",\"item\":\"ruler\",\"qty\":\"3\"}");
        pipeline.flush(); // explicit flush for remainder

        System.out.println("[SINK COUNT] " + sink.count());

        System.out.println("\n=== Missing sink → fail at init ===");
        try {
            MessagePipeline<Map<String, Object>> bad = new MessagePipeline<>();
            bad.setPipelineName("broken");
            bad.setConverter(new JsonOrderConverter());
            // sink deliberately not set
            bad.afterPropertiesSet();
        } catch (Exception e) {
            System.out.println("[FAIL — expected] " + e.getMessage());
        }
    }
}
```

How to run: `java InitializingBeanDemo3.java`

`afterPropertiesSet()` acts as a framework-level init guard: it null-checks injected collaborators, validates configuration bounds, and runs a converter probe at startup. If any check fails, the context fails to start — `MessagePipeline` is never exposed in an invalid state. The probe catches a bad converter at init time rather than at first message.

## 6. Walkthrough

**Level 3 init sequence in detail:**

```
new MessagePipeline<>()                          ← ① constructor
pipeline.setPipelineName("order-ingest")          ← ② injection (setter)
pipeline.setConverter(new JsonOrderConverter())   ← ② injection (setter)
pipeline.setSink(sink)                            ← ② injection (setter)
pipeline.setMaxBatchSize(3)                       ← ② injection (setter)
pipeline.afterPropertiesSet()                     ← ④ Spring calls this:
  Objects.requireNonNull(converter) → OK          ← validate required deps
  Objects.requireNonNull(sink)      → OK          ← validate required deps
  pipelineName is not blank         → OK          ← validate config
  maxBatchSize 3 in [1,10000]       → OK          ← validate config
  converter.convert("__init_probe__") → {probe=true}   ← probe at startup
  buffer.ensureCapacity(3)          → buffer ready
  [afterPropertiesSet] pipeline 'order-ingest' ready

pipeline.receive(msg1..3)  → buffer fills to 3 → FLUSH (auto)
pipeline.receive(msg4)     → buffer=[msg4]
pipeline.flush()           → FLUSH (explicit)
```

## 7. Gotchas & takeaways

> **`InitializingBean` couples your class to Spring's API.** Prefer `@PostConstruct` for application beans. Use `InitializingBean` for framework/library beans where you own both the bean and the container, or where an interface contract is important for clarity and compile-time safety.

> **Order relative to `@PostConstruct`**: if both are present on the same bean, `@PostConstruct` fires first. `afterPropertiesSet()` fires second. Both fire before any XML `init-method`. Do not rely on both doing the same thing; deduplicate.

- Throwing any `Exception` from `afterPropertiesSet()` aborts context startup and wraps into `BeanCreationException`.
- `afterPropertiesSet()` is NOT called for prototype beans on every `getBean()` call — it is called only once, right after the first construction of that prototype instance.
- Spring itself uses `InitializingBean` in over 100 classes — e.g., `JdbcTemplate.afterPropertiesSet()` validates `dataSource != null`, `LocalContainerEntityManagerFactoryBean.afterPropertiesSet()` builds the JPA `EntityManagerFactory`.
- Combine with `@DependsOn` if `afterPropertiesSet()` calls a collaborator bean that must be fully initialised first.
