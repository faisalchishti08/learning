---
card: spring-framework
gi: 74
slug: predestroy-annotation
title: "@PreDestroy annotation"
---

## 1. What it is

`@PreDestroy` is a **JSR-250 annotation** (from `jakarta.annotation`) placed on a no-arg void method to tell Spring: "call this method just before this singleton bean is removed from the container." It is the preferred, framework-agnostic destroy callback — and it fires first among the three destroy mechanisms (`@PreDestroy` → `DisposableBean.destroy()` → XML `destroy-method`).

```java
import jakarta.annotation.PreDestroy;

@Component
public class WebSocketSessionManager {

    private final Map<String, Session> activeSessions = new ConcurrentHashMap<>();

    @PreDestroy
    public void closeAllSessions() {
        System.out.println("Closing " + activeSessions.size() + " active WebSocket sessions...");
        activeSessions.values().forEach(s -> s.close(1001, "Server shutting down"));
        activeSessions.clear();
    }
}
```

In one sentence: **`@PreDestroy` marks a singleton bean method to be called by Spring just before the container destroys the bean, making it the preferred destroy hook — JSR-250 (no Spring import), fires first among the three destroy mechanisms, never fires on prototype beans.**

## 2. Why & when

Use `@PreDestroy` to:

- **Release connections** — close sockets, JDBC connections, HTTP clients.
- **Flush buffers** — write pending metrics, drain in-flight messages.
- **De-register** — remove from a service registry, cancel a subscription, unregister an MBean.
- **Signal shutdown** — set a `volatile boolean shuttingDown = true` to let in-flight requests drain gracefully.
- **Join background threads** — interrupt and join executor threads cleanly.

Prefer `@PreDestroy` over `DisposableBean` for application beans — it does not import Spring-specific types. Both are equally reliable for singletons.

**`@PreDestroy` is NEVER called on prototype beans.** Same caveat as all destroy mechanisms.

## 3. Core concept

```
Destroy sequence (context.close() or registered JVM shutdown hook):
  @PreDestroy                               ← fires FIRST  (JSR-250)
  DisposableBean.destroy()                  ← fires SECOND (Spring API)
  destroy-method="..."                      ← fires LAST   (XML/annotation attr)

Bean destroy ordering:
  Beans are destroyed in REVERSE init order.
  If A→B→C (C depends on B depends on A), destroy: C, B, A.
  When C.@PreDestroy runs, B and A are still alive.

@PreDestroy method rules (identical to @PostConstruct):
  ✓ void return type
  ✓ no arguments
  ✓ may throw Exception (logged as warning, does NOT abort other destroys)
  ✓ called at most once per singleton instance
  ✗ NOT called on prototype beans
  ✗ NOT called on beans that failed construction
  ✗ NOT called if JVM is killed with SIGKILL (kill -9)

JVM shutdown hook:
  ConfigurableApplicationContext registers a hook automatically →
  context.close() IS called on System.exit(0) or Ctrl+C.
  Spring Boot registers this by default; raw Spring needs
  context.registerShutdownHook() or try-with-resources.
```

## 4. Diagram

<svg viewBox="0 0 680 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@PreDestroy position in destroy sequence and scope behaviour">
  <defs>
    <marker id="a74" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="b74" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="193" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@PreDestroy fires first — then DisposableBean.destroy() — then destroy-method</text>

  <!-- Destroy mechanism boxes (left=first, right=last) -->
  <rect x="10"  y="35" width="130" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="75"  y="52" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">① @PreDestroy</text>
  <text x="75"  y="65" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">JSR-250, fires FIRST ← HERE</text>

  <rect x="155" y="35" width="150" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="230" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">② DisposableBean.destroy()</text>
  <text x="230" y="65" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Spring API, fires SECOND</text>

  <rect x="320" y="35" width="115" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="377" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">③ destroy-method</text>
  <text x="377" y="65" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">XML attr, fires LAST</text>

  <line x1="140" y1="55" x2="153" y2="55" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a74)"/>
  <line x1="305" y1="55" x2="318" y2="55" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a74)"/>

  <!-- Scope panel -->
  <rect x="450" y="30" width="218" height="57" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="559" y="47" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@PreDestroy called?</text>
  <text x="462" y="62" fill="#6db33f" font-size="8" font-family="sans-serif">✓ singleton</text>
  <text x="462" y="76" fill="#e06c75" font-size="8" font-family="sans-serif">✗ prototype  ✗ SIGKILL  ✗ init failed</text>

  <!-- Timeline -->
  <rect x="10" y="90" width="655" height="100" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="108" fill="#8b949e" font-size="9" font-family="monospace">context.close() lifecycle for singleton beans (dependency chain A→B→C):</text>
  <line x1="12" y1="112" x2="662" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="22" y="128" fill="#6db33f" font-size="9" font-family="monospace">C.@PreDestroy   — B and A still alive, safe to call them in teardown</text>
  <text x="22" y="143" fill="#8b949e" font-size="9" font-family="monospace">C.destroy()     — C fully torn down</text>
  <text x="22" y="158" fill="#6db33f" font-size="9" font-family="monospace">B.@PreDestroy   — A still alive</text>
  <text x="22" y="173" fill="#8b949e" font-size="9" font-family="monospace">B.destroy() → A.@PreDestroy → A.destroy()   ← leaf node last</text>
</svg>

`@PreDestroy` fires first in the three-step destroy chain. Beans are destroyed in reverse creation order so each bean's `@PreDestroy` can safely use its dependencies.

## 5. Runnable example

Scenario: a `MetricsCollector` that accumulates counters in memory and must flush them to a (simulated) backend on shutdown.

### Level 1 — Basic

`@PreDestroy` flushes pending metrics before the bean is destroyed.

```java
// PreDestroyDemo.java — run with: java PreDestroyDemo.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class PreDestroyDemo {

    @interface PreDestroy {}

    static class MetricsCollector {
        private final Map<String, AtomicLong> counters = new ConcurrentHashMap<>();
        private boolean flushed = false;

        void increment(String metric) {
            if (flushed) throw new IllegalStateException("Collector already destroyed");
            counters.computeIfAbsent(metric, k -> new AtomicLong()).incrementAndGet();
        }

        long get(String metric) {
            AtomicLong v = counters.get(metric);
            return v == null ? 0 : v.get();
        }

        // @PreDestroy — called by Spring before container closes
        @PreDestroy
        void flush() {
            System.out.println("[@PreDestroy] flushing " + counters.size() + " metrics to backend:");
            counters.forEach((k, v) ->
                System.out.printf("  FLUSH metric='%s' value=%d%n", k, v.get()));
            counters.clear();
            flushed = true;
            System.out.println("[@PreDestroy] flush complete — collector closed");
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Container starting ===");
        MetricsCollector mc = new MetricsCollector();

        System.out.println("\n=== Application running ===");
        mc.increment("http.requests");
        mc.increment("http.requests");
        mc.increment("http.requests");
        mc.increment("http.errors");
        mc.increment("cache.hits");
        mc.increment("cache.hits");
        System.out.println("[LIVE] requests=" + mc.get("http.requests")
            + " errors=" + mc.get("http.errors")
            + " cache.hits=" + mc.get("cache.hits"));

        System.out.println("\n=== Context closing — @PreDestroy fires ===");
        mc.flush();   // Spring calls this

        System.out.println("\n=== After destroy ===");
        try { mc.increment("late.event"); }
        catch (IllegalStateException e) { System.out.println("[EXPECTED] " + e.getMessage()); }
    }
}
```

How to run: `java PreDestroyDemo.java`

`flush()` (the `@PreDestroy` method) drains all counters to the simulated backend before clearing them. After `flush()`, `increment()` throws — the collector refuses writes after teardown.

### Level 2 — Intermediate

`@PreDestroy` with graceful drain: stop accepting new work, wait for in-flight tasks to complete, then flush.

```java
// PreDestroyDemo2.java — run with: java PreDestroyDemo2.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class PreDestroyDemo2 {

    @interface PreDestroy {}

    static class AsyncMetricsCollector {
        private final String endpoint;
        private final ExecutorService flusher;
        private final Map<String, AtomicLong> buffer = new ConcurrentHashMap<>();
        private volatile boolean shutdownInitiated = false;
        private final AtomicInteger flushCount = new AtomicInteger();

        AsyncMetricsCollector(String endpoint) {
            this.endpoint = endpoint;
            this.flusher  = Executors.newSingleThreadExecutor(
                r -> new Thread(r, "metrics-flusher"));
            System.out.println("  [CONSTRUCT] AsyncMetricsCollector endpoint=" + endpoint);
        }

        void increment(String metric) {
            if (shutdownInitiated) {
                System.out.println("  [WARN] dropping metric '" + metric + "' — shutdown in progress");
                return;
            }
            buffer.computeIfAbsent(metric, k -> new AtomicLong()).incrementAndGet();
        }

        // Schedule a periodic flush (in a real app this would run on a timer)
        void periodicFlush() {
            int n = flushCount.incrementAndGet();
            Map<String, Long> snapshot = new LinkedHashMap<>();
            buffer.forEach((k, v) -> snapshot.put(k, v.getAndSet(0)));
            System.out.printf("  [PERIODIC FLUSH #%d] %s → %s%n", n, endpoint, snapshot);
        }

        @PreDestroy
        void shutdown() throws InterruptedException {
            System.out.println("  [@PreDestroy] initiating graceful shutdown...");
            shutdownInitiated = true;   // ① stop accepting new increments

            // ② flush any remaining buffered metrics
            System.out.println("  [@PreDestroy] final flush to " + endpoint + ":");
            buffer.forEach((k, v) -> {
                long val = v.get();
                if (val > 0) System.out.printf("    FINAL metric='%s' value=%d%n", k, val);
            });

            // ③ shut down the flusher thread
            flusher.shutdown();
            if (!flusher.awaitTermination(5, TimeUnit.SECONDS)) {
                System.out.println("  [@PreDestroy] WARN: forced shutdown");
                flusher.shutdownNow();
            }
            System.out.println("  [@PreDestroy] shutdown complete — totalFlushes=" + flushCount.get());
        }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== Container starting ===");
        AsyncMetricsCollector mc = new AsyncMetricsCollector("https://metrics.example.com/ingest");

        System.out.println("\n=== Application running (first window) ===");
        for (int i = 0; i < 5; i++) mc.increment("api.calls");
        mc.increment("api.errors");
        mc.periodicFlush();   // simulated timer tick

        System.out.println("\n=== Application running (second window) ===");
        for (int i = 0; i < 3; i++) mc.increment("api.calls");
        for (int i = 0; i < 2; i++) mc.increment("cache.misses");

        System.out.println("\n=== Context closing — @PreDestroy fires ===");
        mc.shutdown();

        System.out.println("\n=== After destroy ===");
        mc.increment("too.late");   // silently dropped — shutdownInitiated
    }
}
```

How to run: `java PreDestroyDemo2.java`

`@PreDestroy` executes a three-step graceful shutdown: set `shutdownInitiated=true` to reject new increments, flush all buffered metrics that haven't been sent in a periodic flush, then shut down the executor thread pool cleanly. After `@PreDestroy`, `increment()` silently drops new events rather than throwing — a common production pattern (log a warning, don't crash).

### Level 3 — Advanced

Dependency chain: two beans with `@PreDestroy`, destroyed in reverse init order. Each bean's `@PreDestroy` relies on its dependency still being alive.

```java
// PreDestroyDemo3.java — run with: java PreDestroyDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class PreDestroyDemo3 {

    @interface PreDestroy {}

    static final List<String> DESTROY_LOG = new ArrayList<>();

    // ── dependency: MetricsBackend (no deps) ─────────────────────────
    static class MetricsBackend {
        private final String url;
        private volatile boolean alive = true;
        private final List<String> received = new ArrayList<>();

        MetricsBackend(String url) {
            this.url = url;
            System.out.println("  [INIT] MetricsBackend url=" + url);
        }

        void send(String payload) {
            if (!alive) throw new IllegalStateException("MetricsBackend already destroyed");
            received.add(payload);
            System.out.println("  [BACKEND.send] " + payload + " → " + url);
        }

        int received() { return received.size(); }

        @PreDestroy
        void shutdown() {
            System.out.println("  [MetricsBackend.@PreDestroy] closing connection to " + url
                + " — total received=" + received.size());
            alive = false;
            DESTROY_LOG.add("MetricsBackend");
        }
    }

    // ── dependent: EventReporter (depends on MetricsBackend) ─────────
    static class EventReporter {
        private final MetricsBackend backend;
        private final Map<String, AtomicLong> counts = new ConcurrentHashMap<>();
        private volatile boolean accepting = true;

        EventReporter(MetricsBackend backend) {
            this.backend = backend;
            System.out.println("  [INIT] EventReporter (backend.alive=" + backend.alive + ")");
        }

        void record(String event) {
            if (!accepting) { System.out.println("  [WARN] dropping event '" + event + "' after shutdown"); return; }
            counts.computeIfAbsent(event, k -> new AtomicLong()).incrementAndGet();
        }

        // Fires FIRST (EventReporter depends on MetricsBackend, so it is destroyed first)
        @PreDestroy
        void flush() {
            System.out.println("  [EventReporter.@PreDestroy] flushing to backend (backend.alive="
                + backend.alive + " ← must be true)");
            accepting = false;  // stop new records

            // We can still call backend.send() because MetricsBackend is destroyed AFTER us
            counts.forEach((event, count) ->
                backend.send("event=" + event + " count=" + count.get()));

            System.out.println("  [EventReporter.@PreDestroy] done — backend received="
                + backend.received());
            DESTROY_LOG.add("EventReporter");
        }
    }

    // ── container simulation ──────────────────────────────────────────
    public static void main(String[] args) {
        System.out.println("=== Container startup ===");
        // Init order: MetricsBackend first (no deps), EventReporter second
        MetricsBackend backend  = new MetricsBackend("https://metrics.company.com/api/v2");
        EventReporter  reporter = new EventReporter(backend);

        System.out.println("\n=== Application running ===");
        reporter.record("user.login");
        reporter.record("user.login");
        reporter.record("page.view");
        reporter.record("page.view");
        reporter.record("page.view");
        reporter.record("purchase");

        System.out.println("\n=== Context closing — destroy in REVERSE init order ===");
        // Spring destroys reporter FIRST (it's the dependent)
        // MetricsBackend is still alive during reporter's @PreDestroy
        reporter.flush();    // EventReporter.@PreDestroy

        // THEN backend is destroyed
        backend.shutdown();  // MetricsBackend.@PreDestroy

        System.out.println("\n[DESTROY ORDER] " + DESTROY_LOG);
        // Should be [EventReporter, MetricsBackend] — reverse of [MetricsBackend, EventReporter]

        System.out.println("\n=== After full destroy ===");
        reporter.record("late.event");  // silently dropped — accepting=false
        try { backend.send("late.send"); }
        catch (IllegalStateException e) { System.out.println("[EXPECTED] " + e.getMessage()); }
    }
}
```

How to run: `java PreDestroyDemo3.java`

`MetricsBackend` is created first (no dependencies) and destroyed last. `EventReporter` depends on `MetricsBackend`, so it is created second and destroyed first. During `EventReporter.@PreDestroy`, `backend.alive` is still `true` — so the flush call to `backend.send()` succeeds. After `MetricsBackend.@PreDestroy`, `backend.alive` is `false` — any further `send()` throws.

## 6. Walkthrough

**Level 3 destroy sequence in detail:**

```
Container startup:
  new MetricsBackend("https://metrics.company.com/api/v2")
    → INIT MetricsBackend   alive=true
  new EventReporter(backend)
    → INIT EventReporter    accepting=true

Application running:
  reporter.record("user.login")  ×2  → counts={user.login:2}
  reporter.record("page.view")   ×3  → counts={user.login:2, page.view:3}
  reporter.record("purchase")    ×1  → counts={user.login:2, page.view:3, purchase:1}

context.close() — destroy in REVERSE init order:

  Step 1: reporter.flush()  ← EventReporter.@PreDestroy fires FIRST
    accepting = false        ← stop new records
    backend.alive = true     ← MetricsBackend still alive ✓
    backend.send("event=user.login count=2")    → BACKEND.send logged
    backend.send("event=page.view count=3")     → BACKEND.send logged
    backend.send("event=purchase count=1")      → BACKEND.send logged
    backend.received() = 3
    DESTROY_LOG = [EventReporter]

  Step 2: backend.shutdown()  ← MetricsBackend.@PreDestroy fires SECOND
    alive = false
    DESTROY_LOG = [EventReporter, MetricsBackend]

Post-destroy:
  reporter.record("late.event")  → silently dropped (accepting=false)
  backend.send("late.send")      → IllegalStateException (alive=false) ✓

DESTROY_LOG = [EventReporter, MetricsBackend]
  = reverse of init order [MetricsBackend, EventReporter] ✓
```

## 7. Gotchas & takeaways

> **`@PreDestroy` is NOT called on prototype beans.** Spring doesn't track prototype instances after creation. If you have a prototype bean with resources to release, use `ObjectProvider` + manual `BeanFactory.destroyBean(instance)`, or implement a custom `Scope`.

> **Exception from `@PreDestroy` is logged as a WARNING — shutdown continues.** Unlike init callbacks (which abort startup), destroy callbacks swallow exceptions so that other beans can still be destroyed. If your teardown can fail, check for success explicitly and log the failure.

- `@PreDestroy` fires on `context.close()` — Spring Boot calls this automatically. For raw Spring, call `context.registerShutdownHook()` or wrap in try-with-resources: `try (var ctx = new AnnotationConfigApplicationContext(...)) { ... }`.
- In a parent–child context setup (e.g., Spring MVC with a `DispatcherServlet` child context), `@PreDestroy` fires when the child context closes — which happens before the parent context closes.
- To verify your `@PreDestroy` fires in integration tests, use `ConfigurableApplicationContext.close()` explicitly or annotate the test with `@DirtiesContext(classMode = AFTER_CLASS)`.
- Import from `jakarta.annotation.PreDestroy` (Spring Boot 3+) or `javax.annotation.PreDestroy` (Spring Boot 2.x / Jakarta EE 8). The two are functionally identical — just different package names.
- Use `@PreDestroy` for signalling shutdown intent and `DisposableBean.destroy()` for the actual resource release if you want to separate concerns: `@PreDestroy` → "stop accepting new work", `destroy()` → "release the connection pool".
