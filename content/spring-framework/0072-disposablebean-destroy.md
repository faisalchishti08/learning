---
card: spring-framework
gi: 72
slug: disposablebean-destroy
title: DisposableBean / destroy()
---

## 1. What it is

`DisposableBean` is a Spring interface with one method — `destroy()` — that Spring calls on **singleton beans just before the context is closed**. It is the interface-based counterpart to `@PreDestroy` (fires first) and XML `destroy-method` (fires last).

```java
import org.springframework.beans.factory.DisposableBean;

@Component
public class ThreadPoolManager implements DisposableBean {

    private final ExecutorService executor = Executors.newFixedThreadPool(4);

    @Override
    public void destroy() throws Exception {
        System.out.println("Shutting down thread pool...");
        executor.shutdown();
        if (!executor.awaitTermination(30, TimeUnit.SECONDS)) {
            executor.shutdownNow();
        }
        System.out.println("Thread pool shut down.");
    }
}
```

In one sentence: **`DisposableBean.destroy()` is a Spring-native destroy callback called on singleton beans at context close, used to release resources — it fires after `@PreDestroy` and before XML `destroy-method`, and is never called on prototype beans.**

## 2. Why & when

Use `destroy()` when:

- Writing Spring infrastructure or library beans where coupling to Spring's API is acceptable or intentional.
- You need compile-time enforcement that the destroy method exists — the interface keeps the signature exact and the IDE warns if it is not implemented.
- You want parity with `InitializingBean` in the same class.

Prefer `@PreDestroy` for application-level beans. Use `DisposableBean` for framework-level beans or when interface-enforced teardown is valuable (e.g., Spring's own `AbstractApplicationContext`, `JdbcTemplate`, `LocalContainerEntityManagerFactoryBean`).

**Critical: `DisposableBean.destroy()` is NEVER called on prototype beans.** Spring creates prototypes on demand but doesn't track them — cleanup is the caller's responsibility.

## 3. Core concept

```
Destroy sequence (context.close() or JVM shutdown hook):
  @PreDestroy methods (CommonAnnotationBeanPostProcessor)    ← fires FIRST
  DisposableBean.destroy()                                   ← fires SECOND
  destroy-method="..." (XML/annotation attribute)            ← fires LAST

When destroy() is NOT called:
  ✗ Prototype-scoped beans — caller is responsible
  ✗ Beans that fail during init (never fully registered)
  ✗ If context.close() is not called (e.g. JVM killed with SIGKILL)
  ✓ JVM shutdown hook: ConfigurableApplicationContext registers
      a JVM shutdown hook via Runtime.getRuntime().addShutdownHook()
      so context.close() IS called on Ctrl+C or System.exit()

Destroy order: REVERSE of init order
  Init:    A → B → C (C depends on B which depends on A)
  Destroy: C → B → A (C destroyed first; A is still alive when C tears down)
```

## 4. Diagram

<svg viewBox="0 0 680 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DisposableBean position in Spring destroy sequence">
  <defs>
    <marker id="a72" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="b72" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="193" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">DisposableBean fires in the middle of the three destroy mechanisms</text>

  <!-- Destroy sequence (right-to-left: bean is alive → being destroyed) -->
  <rect x="10"  y="35" width="120" height="38" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="70"  y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">① @PreDestroy</text>
  <text x="70"  y="64" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">JSR-250, fires FIRST</text>

  <rect x="145" y="35" width="145" height="38" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="217" y="52" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">② DisposableBean.destroy()</text>
  <text x="217" y="64" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">Spring interface ← YOU ARE HERE</text>

  <rect x="305" y="35" width="115" height="38" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="362" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">③ destroy-method</text>
  <text x="362" y="64" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">XML attr, fires LAST</text>

  <!-- Arrows (left to right = fires first to last) -->
  <line x1="130" y1="54" x2="143" y2="54" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a72)"/>
  <line x1="290" y1="54" x2="303" y2="54" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a72)"/>

  <!-- Scope comparison -->
  <rect x="440" y="30" width="228" height="58" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="553" y="47" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Destroy callback called?</text>
  <text x="452" y="63" fill="#6db33f" font-size="8" font-family="sans-serif">✓ singleton</text>
  <text x="452" y="78" fill="#e06c75" font-size="8" font-family="sans-serif">✗ prototype  ✗ SIGKILL  ✗ init failure</text>

  <!-- Prototype note -->
  <rect x="10" y="90" width="655" height="100" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="108" fill="#8b949e" font-size="9" font-family="monospace">Comparison: DisposableBean vs @PreDestroy vs destroy-method</text>
  <line x1="12" y1="112" x2="662" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="22" y="127" fill="#8b949e" font-size="9" font-family="monospace">@PreDestroy        1st  JSR-250     singleton + prototype(*) app beans</text>
  <text x="22" y="142" fill="#6db33f" font-size="9" font-family="monospace">DisposableBean     2nd  Spring API  singleton only           infra beans</text>
  <text x="22" y="157" fill="#8b949e" font-size="9" font-family="monospace">destroy-method=""  3rd  None        singleton only           legacy / XML</text>
  <text x="22" y="172" fill="#79c0ff" font-size="8" font-family="sans-serif">(*) @PreDestroy is also NOT called on prototypes — same caveat applies to all mechanisms.</text>
</svg>

`destroy()` sits between `@PreDestroy` (first) and `destroy-method` (last). None of the three mechanisms are called on prototype beans.

## 5. Runnable example

Scenario: a `CacheManager` that pre-loads entries at startup and must flush dirty entries and close connections at shutdown.

### Level 1 — Basic

Minimal `DisposableBean` implementation: release a resource on context close.

```java
// DisposableBeanDemo.java — run with: java DisposableBeanDemo.java
import java.util.*;

public class DisposableBeanDemo {

    interface DisposableBean { void destroy() throws Exception; }

    static class InMemoryCache implements DisposableBean {
        private final String name;
        private final Map<String, String> store = new LinkedHashMap<>();
        private boolean closed = false;

        InMemoryCache(String name) {
            this.name = name;
            System.out.println("  [CONSTRUCT] InMemoryCache '" + name + "'");
        }

        void put(String key, String value) {
            if (closed) throw new IllegalStateException("Cache '" + name + "' is closed");
            store.put(key, value);
        }

        String get(String key) {
            if (closed) throw new IllegalStateException("Cache '" + name + "' is closed");
            return store.get(key);
        }

        @Override
        public void destroy() throws Exception {
            System.out.println("  [destroy] flushing cache '" + name + "' — "
                + store.size() + " entries");
            store.clear();
            closed = true;
            System.out.println("  [destroy] cache '" + name + "' closed");
        }
    }

    // ── simulated container ───────────────────────────────────────────
    public static void main(String[] args) throws Exception {
        System.out.println("=== Container starting ===");
        InMemoryCache cache = new InMemoryCache("product-cache");

        System.out.println("\n=== Application running ===");
        cache.put("p:1", "Notebook");
        cache.put("p:2", "Pen");
        cache.put("p:3", "Ruler");
        System.out.println("[GET p:2] " + cache.get("p:2"));

        System.out.println("\n=== Context closing (destroy called) ===");
        cache.destroy();  // Spring calls this at context.close()

        System.out.println("\n=== After close ===");
        try {
            cache.get("p:1");
        } catch (IllegalStateException e) {
            System.out.println("[EXPECTED] " + e.getMessage());
        }
    }
}
```

How to run: `java DisposableBeanDemo.java`

`destroy()` clears the store and marks the cache closed. After `destroy()`, calling `get()` throws `IllegalStateException` — the cache refuses use after teardown.

### Level 2 — Intermediate

`DisposableBean` with both `@PreDestroy` and `destroy()` — shows both fire and their order.

```java
// DisposableBeanDemo2.java — run with: java DisposableBeanDemo2.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class DisposableBeanDemo2 {

    interface DisposableBean { void destroy() throws Exception; }
    @interface PreDestroy    {} // marker

    static class FileUploadService implements DisposableBean {
        private final String bucketName;
        private final ExecutorService uploadPool;
        private final AtomicInteger uploadCount   = new AtomicInteger();
        private final AtomicInteger pendingCount  = new AtomicInteger();
        private volatile boolean shutdownInitiated = false;
        private final List<String> shutdownLog     = new ArrayList<>();

        FileUploadService(String bucketName, int threads) {
            this.bucketName = bucketName;
            this.uploadPool = Executors.newFixedThreadPool(threads,
                r -> new Thread(r, "upload-worker"));
            System.out.println("  [CONSTRUCT] FileUploadService bucket=" + bucketName);
        }

        Future<String> upload(String filename) {
            if (shutdownInitiated)
                throw new IllegalStateException("Service shutting down — no new uploads");
            pendingCount.incrementAndGet();
            return uploadPool.submit(() -> {
                try {
                    Thread.sleep(20 + (long)(Math.random() * 30)); // simulate upload
                    int n = uploadCount.incrementAndGet();
                    System.out.printf("  [UPLOAD #%d] %s → s3://%s/%s%n",
                        n, filename, bucketName, filename);
                    return "s3://" + bucketName + "/" + filename;
                } finally {
                    pendingCount.decrementAndGet();
                }
            });
        }

        // Fires FIRST (simulated @PreDestroy)
        // @PreDestroy
        void preDestroy() {
            System.out.println("  [@PreDestroy] marking shutdown initiated — no new uploads accepted");
            shutdownInitiated = true;
            shutdownLog.add("@PreDestroy: shutdownInitiated=true");
        }

        // Fires SECOND (DisposableBean)
        @Override
        public void destroy() throws Exception {
            System.out.println("  [destroy] draining " + pendingCount.get() + " pending uploads...");
            shutdownLog.add("destroy: draining pool pending=" + pendingCount.get());
            uploadPool.shutdown();
            boolean clean = uploadPool.awaitTermination(5, TimeUnit.SECONDS);
            if (!clean) {
                System.out.println("  [destroy] WARN: forced shutdown after timeout");
                uploadPool.shutdownNow();
            }
            System.out.println("  [destroy] upload pool stopped — total uploaded: " + uploadCount.get());
            shutdownLog.add("destroy: pool stopped, uploaded=" + uploadCount.get());
            System.out.println("  [destroy] shutdown log: " + shutdownLog);
        }
    }

    public static void main(String[] args) throws Exception {
        FileUploadService svc = new FileUploadService("my-bucket", 3);

        System.out.println("\n=== Submitting uploads ===");
        List<Future<String>> futures = new ArrayList<>();
        for (String f : List.of("report.pdf", "image.png", "data.csv", "archive.zip"))
            futures.add(svc.upload(f));

        System.out.println("\n=== Context closing ===");
        svc.preDestroy();  // @PreDestroy fires first

        // test that new uploads are rejected after preDestroy
        try { svc.upload("rejected.txt"); }
        catch (IllegalStateException e) { System.out.println("  [EXPECTED] " + e.getMessage()); }

        svc.destroy();     // DisposableBean.destroy() fires second

        System.out.println("\n=== Results ===");
        for (Future<String> f : futures)
            System.out.println("[RESULT] " + (f.isDone() ? f.get() : "cancelled"));
    }
}
```

How to run: `java DisposableBeanDemo2.java`

`preDestroy()` (simulating `@PreDestroy`) fires first and marks the service as shutting down — new upload attempts are rejected. `destroy()` (simulating `DisposableBean`) fires second and drains in-flight uploads via `awaitTermination()`. The shutdown log confirms the order.

### Level 3 — Advanced

Multi-bean dependency graph: destroy order is reverse of init order, and each bean's `destroy()` asserts that its dependencies are still alive.

```java
// DisposableBeanDemo3.java — run with: java DisposableBeanDemo3.java
import java.util.*;

public class DisposableBeanDemo3 {

    interface DisposableBean { void destroy() throws Exception; }

    static final List<String> INIT_LOG    = new ArrayList<>();
    static final List<String> DESTROY_LOG = new ArrayList<>();

    static class MqConnection implements DisposableBean {
        boolean alive = true;
        MqConnection() { INIT_LOG.add("MqConnection"); System.out.println("  [INIT] MqConnection: connected"); }
        void publish(String msg) {
            if (!alive) throw new IllegalStateException("MqConnection already destroyed");
            System.out.println("  [MQ] publish: " + msg);
        }
        @Override public void destroy() {
            System.out.println("  [DESTROY] MqConnection: disconnecting");
            alive = false;
            DESTROY_LOG.add("MqConnection");
        }
    }

    static class EventBus implements DisposableBean {
        private final MqConnection mq;
        EventBus(MqConnection mq) { this.mq = mq; INIT_LOG.add("EventBus"); System.out.println("  [INIT] EventBus: ready (mq.alive=" + mq.alive + ")"); }
        void emit(String event) { mq.publish("event=" + event); }
        @Override public void destroy() {
            System.out.println("  [DESTROY] EventBus: shutting down (mq.alive=" + mq.alive + " ← should be true)");
            DESTROY_LOG.add("EventBus");
        }
    }

    static class OrderProcessor implements DisposableBean {
        private final EventBus bus;
        OrderProcessor(EventBus bus) { this.bus = bus; INIT_LOG.add("OrderProcessor"); System.out.println("  [INIT] OrderProcessor: ready"); }
        void process(String orderId) { bus.emit("order.processed:" + orderId); }
        @Override public void destroy() {
            System.out.println("  [DESTROY] OrderProcessor: last flush");
            bus.emit("order.processor.shutdown");  // still works — EventBus not yet destroyed
            DESTROY_LOG.add("OrderProcessor");
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Container startup (init order) ===");
        // init in dependency order: MqConnection first (no deps), then EventBus, then OrderProcessor
        MqConnection   mq   = new MqConnection();
        EventBus       bus  = new EventBus(mq);
        OrderProcessor proc = new OrderProcessor(bus);

        System.out.println("\n[INIT ORDER] " + INIT_LOG);

        System.out.println("\n=== Application running ===");
        proc.process("ORD-001");
        proc.process("ORD-002");

        System.out.println("\n=== Context close (destroy in REVERSE init order) ===");
        // Spring destroys in reverse order: OrderProcessor first (its deps still alive), MqConnection last
        proc.destroy();  // can still use EventBus and MqConnection ✓
        bus.destroy();   // can still use MqConnection ✓
        mq.destroy();    // last to die

        System.out.println("\n[DESTROY ORDER] " + DESTROY_LOG);
        System.out.println("[REVERSE OF INIT?] "
            + new ArrayList<>(List.of("OrderProcessor","EventBus","MqConnection")).equals(DESTROY_LOG));

        System.out.println("\n=== After full destroy — mq is dead ===");
        try { mq.publish("late message"); }
        catch (IllegalStateException e) { System.out.println("[EXPECTED] " + e.getMessage()); }
    }
}
```

How to run: `java DisposableBeanDemo3.java`

Init order: `MqConnection` → `EventBus` → `OrderProcessor`. Destroy order is reversed: `OrderProcessor` first (still uses `EventBus`/`MqConnection` in its teardown), `EventBus` second (can still verify `mq.alive=true`), `MqConnection` last. This guarantees each bean's `destroy()` can safely call its dependencies.

## 6. Walkthrough

**Level 3 destroy sequence in detail:**

```
Context.close() arrives:
  Spring destroys beans in REVERSE creation order:

  proc.destroy()
    "last flush" → bus.emit("order.processor.shutdown")
              → mq.publish("event=order.processor.shutdown")  ← MQ still alive ✓
    DESTROY_LOG = [OrderProcessor]

  bus.destroy()
    prints "mq.alive=true" ← MQ still alive ✓
    DESTROY_LOG = [OrderProcessor, EventBus]

  mq.destroy()
    disconnects → alive=false
    DESTROY_LOG = [OrderProcessor, EventBus, MqConnection]

  mq.publish("late message") → IllegalStateException ← MQ dead ✓

DESTROY_LOG == reverse(INIT_LOG)?
  INIT_LOG    = [MqConnection, EventBus, OrderProcessor]
  DESTROY_LOG = [OrderProcessor, EventBus, MqConnection]  ✓ reversed
```

## 7. Gotchas & takeaways

> **`DisposableBean.destroy()` is never called on prototype beans.** Spring releases prototype beans after creation and does not track them. If you need prototype teardown, use `ObjectProvider`, `BeanFactory.destroyBean(bean)`, or a custom `Scope` implementation.

> **`destroy()` fires AFTER `@PreDestroy`.** If both are on the same bean, `@PreDestroy` fires first. Do not duplicate teardown logic across both — put high-level signaling in `@PreDestroy` and actual resource release in `destroy()`.

- Throwing `Exception` from `destroy()` logs a warning but does NOT abort the rest of the shutdown sequence — other beans' destroy methods still run.
- Spring's JVM shutdown hook (`ConfigurableApplicationContext.registerShutdownHook()`) means `destroy()` is called on `System.exit(0)` or `Ctrl+C` but NOT on `SIGKILL` (kill -9).
- `@Bean(destroyMethod="")` suppresses auto-detection of `close()` / `shutdown()` methods — use this for externally-managed beans (e.g., `DataSource` from a connection pool library that manages its own lifecycle).
- Spring scans for `close()` or `shutdown()` as implicit `destroy-method` on `@Bean` declarations — if your class has such a method and you do NOT want Spring to call it, explicitly set `@Bean(destroyMethod="")`.
