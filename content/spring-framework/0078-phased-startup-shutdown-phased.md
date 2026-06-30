---
card: spring-framework
gi: 78
slug: phased-startup-shutdown-phased
title: Phased startup/shutdown (Phased)
---

## 1. What it is

`Phased` is a Spring interface with a single method — `getPhase(): int` — that lets a `SmartLifecycle` bean declare its position in the startup and shutdown ordering. Lower phase numbers start earlier and stop later; higher phase numbers start later and stop earlier. The `Phased` interface itself doesn't do anything on its own — it is meaningful only when implemented by a `SmartLifecycle` bean.

```java
import org.springframework.context.SmartLifecycle;

@Component
public class WebServer implements SmartLifecycle {

    // Start LAST (other infrastructure ready first), stop FIRST (drain before infra shuts)
    @Override
    public int getPhase() { return Integer.MAX_VALUE; }

    @Override public boolean isAutoStartup() { return true; }
    @Override public void    start()         { /* bind to port */ }
    @Override public void    stop(Runnable c){ /* drain connections, then c.run() */ }
    @Override public boolean isRunning()     { return /* port bound */ false; }
}
```

In one sentence: **`Phased.getPhase()` assigns an integer priority to `SmartLifecycle` beans — lower phase starts first/stops last (infrastructure), higher phase starts last/stops first (end-user-facing), enabling deterministic ordered startup and shutdown.**

## 2. Why & when

Use explicit phases when:

- A bean must start **before** other beans have started (e.g., a broker connection that consumers depend on).
- A web-facing bean must start **after** all infrastructure is ready (e.g., only expose an HTTP port after the database pool is connected).
- On shutdown, you need to stop accepting requests **before** infrastructure tears down — so in-flight requests can complete.

Typical phase conventions:

| Phase range       | Use case |
|-------------------|----------|
| `Integer.MIN_VALUE` .. `-1` | Spring messaging infrastructure, topic registries |
| `0` (default)     | Application pollers, event buses |
| `1` .. `MAX_VALUE` | Web server / HTTP listeners (start last, stop first) |

If you don't care about ordering, the default `getPhase()=0` is fine.

## 3. Core concept

```
Startup ordering (lower phase = starts first):
  Phase -1000   → Spring broker infrastructure starts
  Phase -100    → Database pool starts (SmartLifecycle bean)
  Phase 0       → Application pollers / event consumers start
  Phase 1000    → Web server binds to port (last to start)

Shutdown ordering (REVERSE — higher phase = stops first):
  Phase 1000    → Web server stops accepting new requests (first to stop)
  Phase 0       → Application pollers / event consumers stop
  Phase -100    → Database pool closes (last to stop among app beans)
  Phase -1000   → Spring broker infrastructure stops

Key rule:
  startOrder:   sort ascending  (MIN_VALUE first)
  stopOrder:    sort descending (MAX_VALUE first)
  → A bean that started LAST stops FIRST.

DefaultLifecycleProcessor groups beans by phase:
  All phase-N beans start together (in parallel within a phase).
  Spring waits for all beans in phase N to start before moving to phase N+1.
  Same for shutdown: all phase-N beans stop together before moving to phase N-1.

timeout per phase: configurable on DefaultLifecycleProcessor (default 30s).
  If a stop(callback) in phase N doesn't call callback within 30s, Spring
  logs a warning and moves to the next phase anyway.
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Phase ordering: startup bottom-to-top, shutdown top-to-bottom">
  <defs>
    <marker id="a78u" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="a78d" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="198" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Phase ordering: low phase starts first / stops last</text>

  <!-- Phase blocks (bottom=low phase=starts first) -->
  <rect x="60" y="30" width="340" height="34" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="230" y="48" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Phase Integer.MAX_VALUE — Web server (binds port)</text>
  <text x="230" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">starts LAST • stops FIRST</text>

  <rect x="60" y="74" width="340" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="230" y="92" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Phase 0 (default) — Application pollers / event buses</text>
  <text x="230" y="102" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">middle</text>

  <rect x="60" y="118" width="340" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="230" y="136" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Phase -100 — Database pool</text>
  <text x="230" y="146" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">starts before phase 0</text>

  <rect x="60" y="162" width="340" height="34" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="230" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Phase Integer.MIN_VALUE — Spring broker infra</text>
  <text x="230" y="190" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">starts FIRST • stops LAST</text>

  <!-- Startup arrow (upward) -->
  <line x1="435" y1="187" x2="435" y2="45" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a78u)"/>
  <text x="510" y="125" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">STARTUP</text>
  <text x="510" y="138" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">↑ low phase first</text>

  <!-- Shutdown arrow (downward) -->
  <line x1="580" y1="45" x2="580" y2="187" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a78d)"/>
  <text x="635" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SHUTDOWN</text>
  <text x="635" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">↓ high phase first</text>
</svg>

Lower phase starts first (infrastructure ready before application). Shutdown reverses: higher phase stops first (HTTP port drained before broker disconnects).

## 5. Runnable example

Scenario: a three-layer system — database pool (phase -100), order processor (phase 0), HTTP frontend (phase MAX_VALUE) — must start in that order and shut down in reverse.

### Level 1 — Basic

Three `SmartLifecycle` beans with explicit phases; container starts them in phase order.

```java
// PhasedDemo.java — run with: java PhasedDemo.java
import java.util.*;

public class PhasedDemo {

    interface SmartLifecycle {
        boolean isAutoStartup();
        int     getPhase();
        void    start();
        void    stop(Runnable callback);
        boolean isRunning();
    }

    static abstract class BaseBean implements SmartLifecycle {
        protected volatile boolean running = false;
        protected final String name;
        BaseBean(String name) { this.name = name; }
        @Override public boolean isAutoStartup() { return true; }
        @Override public boolean isRunning()     { return running; }
        @Override public void stop(Runnable cb)  { running = false; System.out.println("[stop  phase=" + getPhase() + "] " + name); cb.run(); }
    }

    static class DatabasePool    extends BaseBean { DatabasePool()    { super("DatabasePool");    } @Override public int getPhase() { return -100;             } @Override public void start() { running = true; System.out.println("[start phase=-100 ] DatabasePool    — DB connections open"); } }
    static class OrderProcessor  extends BaseBean { OrderProcessor()  { super("OrderProcessor");  } @Override public int getPhase() { return 0;                } @Override public void start() { running = true; System.out.println("[start phase=0    ] OrderProcessor  — processing enabled"); } }
    static class HttpFrontend    extends BaseBean { HttpFrontend()    { super("HttpFrontend");    } @Override public int getPhase() { return Integer.MAX_VALUE; } @Override public void start() { running = true; System.out.println("[start phase=MAX  ] HttpFrontend    — port 8080 bound"); } }

    static void simulateContainer(List<SmartLifecycle> beans) throws InterruptedException {
        System.out.println("--- context.refresh(): startup in phase order ---");
        List<SmartLifecycle> startOrder = new ArrayList<>(beans);
        startOrder.sort(Comparator.comparingInt(SmartLifecycle::getPhase));
        for (SmartLifecycle b : startOrder) if (b.isAutoStartup()) b.start();

        System.out.println("\n--- Application running ---");
        Thread.sleep(200);

        System.out.println("\n--- context.close(): shutdown in REVERSE phase order ---");
        List<SmartLifecycle> stopOrder = new ArrayList<>(beans);
        stopOrder.sort(Comparator.comparingInt(SmartLifecycle::getPhase).reversed());
        for (SmartLifecycle b : stopOrder) if (b.isRunning()) b.stop(() -> {});
    }

    public static void main(String[] args) throws InterruptedException {
        simulateContainer(List.of(new DatabasePool(), new OrderProcessor(), new HttpFrontend()));
    }
}
```

How to run: `java PhasedDemo.java`

Startup order: `DatabasePool` (phase -100) → `OrderProcessor` (phase 0) → `HttpFrontend` (phase MAX). Shutdown reverses: `HttpFrontend` → `OrderProcessor` → `DatabasePool`. The HTTP port is bound last (so DB and processors are ready) and drained first (so no in-flight request touches a stopped processor).

### Level 2 — Intermediate

Add timeout-per-phase enforcement: if a bean's `stop(callback)` takes too long, Spring logs a warning and moves on.

```java
// PhasedDemo2.java — run with: java PhasedDemo2.java
import java.util.*;
import java.util.concurrent.*;

public class PhasedDemo2 {

    interface SmartLifecycle { boolean isAutoStartup(); int getPhase(); void start(); void stop(Runnable cb); boolean isRunning(); }

    // ── Fast-stopping bean ────────────────────────────────────────────
    static class HttpFrontend implements SmartLifecycle {
        private volatile boolean running = false;
        @Override public boolean isAutoStartup() { return true; }
        @Override public int     getPhase()      { return 1000; }
        @Override public void    start()         { running = true; System.out.println("[start phase=1000] HttpFrontend — port bound"); }
        @Override public void    stop(Runnable cb) {
            System.out.println("[stop  phase=1000] HttpFrontend — closing port");
            running = false;
            cb.run(); // immediate — fast
        }
        @Override public boolean isRunning() { return running; }
    }

    // ── Slow-stopping bean (simulates a stuck shutdown) ───────────────
    static class SlowConsumer implements SmartLifecycle {
        private volatile boolean running = false;
        @Override public boolean isAutoStartup() { return true; }
        @Override public int     getPhase()      { return 0; }
        @Override public void    start()         { running = true; System.out.println("[start phase=0   ] SlowConsumer — consuming"); }
        @Override public void    stop(Runnable cb) {
            System.out.println("[stop  phase=0   ] SlowConsumer — draining (this will be slow)...");
            running = false;
            // Simulates a consumer that takes 800ms to drain
            new Thread(() -> {
                try { Thread.sleep(800); } catch (InterruptedException ignored) {}
                System.out.println("[stop  phase=0   ] SlowConsumer — drain complete, calling callback");
                cb.run();
            }).start();
        }
        @Override public boolean isRunning() { return running; }
    }

    // ── Fast infra bean ───────────────────────────────────────────────
    static class BrokerInfra implements SmartLifecycle {
        private volatile boolean running = false;
        @Override public boolean isAutoStartup() { return true; }
        @Override public int     getPhase()      { return -100; }
        @Override public void    start()         { running = true; System.out.println("[start phase=-100] BrokerInfra — broker connected"); }
        @Override public void    stop(Runnable cb) {
            System.out.println("[stop  phase=-100] BrokerInfra — disconnecting");
            running = false;
            cb.run();
        }
        @Override public boolean isRunning() { return running; }
    }

    // ── Phase-aware container with per-phase timeout ──────────────────
    static void runContainer(List<SmartLifecycle> beans, long phaseTimeoutMs) throws InterruptedException {
        System.out.println("--- Startup ---");
        List<SmartLifecycle> sorted = new ArrayList<>(beans);
        sorted.sort(Comparator.comparingInt(SmartLifecycle::getPhase));
        for (SmartLifecycle b : sorted) if (b.isAutoStartup()) b.start();

        Thread.sleep(300);
        System.out.println("\n--- Shutdown (phaseTimeout=" + phaseTimeoutMs + "ms) ---");

        // Group by phase descending
        Map<Integer, List<SmartLifecycle>> byPhase = new TreeMap<>(Comparator.reverseOrder());
        for (SmartLifecycle b : beans) if (b.isRunning()) byPhase.computeIfAbsent(b.getPhase(), k -> new ArrayList<>()).add(b);

        for (Map.Entry<Integer, List<SmartLifecycle>> entry : byPhase.entrySet()) {
            int phase = entry.getKey();
            List<SmartLifecycle> group = entry.getValue();
            System.out.println("[PHASE " + phase + "] stopping " + group.size() + " bean(s) in parallel...");
            CountDownLatch latch = new CountDownLatch(group.size());
            for (SmartLifecycle b : group) b.stop(latch::countDown);
            boolean completed = latch.await(phaseTimeoutMs, TimeUnit.MILLISECONDS);
            if (!completed)
                System.out.println("  WARN: phase " + phase + " did not complete within " + phaseTimeoutMs + "ms — moving on");
            else
                System.out.println("  phase " + phase + " complete");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        runContainer(List.of(new HttpFrontend(), new SlowConsumer(), new BrokerInfra()),
            500); // 500ms timeout — SlowConsumer takes 800ms → timeout warning
    }
}
```

How to run: `java PhasedDemo2.java`

`SlowConsumer` (phase 0) takes 800ms to drain but the timeout is 500ms — Spring logs a warning and moves on to phase -100 (`BrokerInfra`). `HttpFrontend` (phase 1000) stops fast. This mirrors `DefaultLifecycleProcessor`'s real behaviour.

### Level 3 — Advanced

Production pattern: web server starts last / stops first; a health-check bean flips the readiness probe before the HTTP port closes, giving load balancers time to drain traffic.

```java
// PhasedDemo3.java — run with: java PhasedDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class PhasedDemo3 {

    interface SmartLifecycle { boolean isAutoStartup(); int getPhase(); void start(); void stop(Runnable cb); boolean isRunning(); }

    static final List<String> LOG = Collections.synchronizedList(new ArrayList<>());

    // Phase -200: DB pool
    static class DbPool implements SmartLifecycle {
        volatile boolean open = false;
        @Override public boolean isAutoStartup() { return true; }
        @Override public int     getPhase()      { return -200; }
        @Override public void    start()         { open=true;  LOG.add("DbPool.start");  System.out.println("[phase=-200] DbPool.start()  — connections open"); }
        @Override public void    stop(Runnable cb){ open=false; LOG.add("DbPool.stop");  System.out.println("[phase=-200] DbPool.stop()  — connections closed"); cb.run(); }
        @Override public boolean isRunning()     { return open; }
    }

    // Phase 0: order service
    static class OrderService implements SmartLifecycle {
        private final DbPool db;
        volatile boolean ready = false;
        private final AtomicInteger processed = new AtomicInteger();
        OrderService(DbPool db) { this.db = db; }
        @Override public boolean isAutoStartup() { return true; }
        @Override public int     getPhase()      { return 0; }
        @Override public void    start()         { ready=true; LOG.add("OrderService.start"); System.out.println("[phase=0   ] OrderService.start() — db.open=" + db.open); }
        void process(String id)                  { if (ready) { processed.incrementAndGet(); System.out.println("  [PROCESS] " + id); } }
        @Override public void    stop(Runnable cb){ ready=false; LOG.add("OrderService.stop"); System.out.println("[phase=0   ] OrderService.stop() — processed=" + processed.get()); cb.run(); }
        @Override public boolean isRunning()     { return ready; }
    }

    // Phase 9000: readiness probe (flip DOWN before HTTP port closes — LB drains traffic)
    static class ReadinessProbe implements SmartLifecycle {
        volatile boolean ready = false;
        @Override public boolean isAutoStartup() { return true; }
        @Override public int     getPhase()      { return 9000; }
        @Override public void    start()         { ready=true;  LOG.add("ReadinessProbe.start"); System.out.println("[phase=9000] ReadinessProbe.start() — /readyz → 200 OK"); }
        @Override public void    stop(Runnable cb){ ready=false; LOG.add("ReadinessProbe.stop"); System.out.println("[phase=9000] ReadinessProbe.stop()  — /readyz → 503 (LB will drain)"); try { Thread.sleep(200); } catch (InterruptedException ignored) {} cb.run(); }
        @Override public boolean isRunning()     { return ready; }
        String status() { return ready ? "200 OK" : "503 Service Unavailable"; }
    }

    // Phase MAX: HTTP server (bind port LAST, close port FIRST after readiness flips)
    static class HttpServer implements SmartLifecycle {
        private final ReadinessProbe probe;
        private final OrderService   svc;
        volatile boolean bound = false;
        HttpServer(ReadinessProbe p, OrderService s) { this.probe = p; this.svc = s; }
        @Override public boolean isAutoStartup() { return true; }
        @Override public int     getPhase()      { return Integer.MAX_VALUE; }
        @Override public void    start()         { bound=true; LOG.add("HttpServer.start"); System.out.println("[phase=MAX ] HttpServer.start()  — port 8080 bound (readyz=" + probe.status() + ")"); }
        void handle(String req)                  { System.out.println("  [HTTP] " + req + " → svc.ready=" + svc.ready); if (svc.ready) svc.process(req); }
        @Override public void    stop(Runnable cb){ bound=false; LOG.add("HttpServer.stop"); System.out.println("[phase=MAX ] HttpServer.stop()  — port 8080 closed (readyz=" + probe.status() + ")"); cb.run(); }
        @Override public boolean isRunning()     { return bound; }
    }

    static void run(List<SmartLifecycle> beans) throws InterruptedException {
        System.out.println("=== STARTUP (low phase first) ===");
        List<SmartLifecycle> up = new ArrayList<>(beans);
        up.sort(Comparator.comparingInt(SmartLifecycle::getPhase));
        for (SmartLifecycle b : up) if (b.isAutoStartup()) b.start();
        System.out.println("[START LOG] " + LOG.stream().filter(s -> s.endsWith(".start")).toList());

        System.out.println("\n=== APPLICATION ===");
        Thread.sleep(300);

        System.out.println("\n=== SHUTDOWN (high phase first) ===");
        List<SmartLifecycle> down = new ArrayList<>(beans);
        down.sort(Comparator.comparingInt(SmartLifecycle::getPhase).reversed());
        CountDownLatch latch = new CountDownLatch(down.size());
        // Stop each phase group sequentially
        Map<Integer, List<SmartLifecycle>> groups = new TreeMap<>(Comparator.reverseOrder());
        for (SmartLifecycle b : down) if (b.isRunning()) groups.computeIfAbsent(b.getPhase(), k -> new ArrayList<>()).add(b);
        for (var e : groups.entrySet()) {
            CountDownLatch pl = new CountDownLatch(e.getValue().size());
            for (SmartLifecycle b : e.getValue()) b.stop(pl::countDown);
            pl.await(3, TimeUnit.SECONDS);
        }
        System.out.println("[STOP LOG]  " + LOG.stream().filter(s -> s.endsWith(".stop")).toList());
    }

    public static void main(String[] args) throws InterruptedException {
        DbPool         db    = new DbPool();
        OrderService   svc   = new OrderService(db);
        ReadinessProbe probe = new ReadinessProbe();
        HttpServer     http  = new HttpServer(probe, svc);

        run(List.of(db, svc, probe, http));
    }
}
```

How to run: `java PhasedDemo3.java`

Startup: `DbPool` (-200) → `OrderService` (0) → `ReadinessProbe` (9000) → `HttpServer` (MAX). HTTP port is bound only after DB and services are ready, and the readiness probe is already flipped to `200 OK`. Shutdown: `HttpServer` closes the port first (MAX), then `ReadinessProbe` flips to `503` (giving load balancers 200ms to drain), then `OrderService` stops, then `DbPool` last.

## 6. Walkthrough

**Level 3 startup sequence in detail:**

```
context.refresh() — sorted by phase ascending:

  getPhase=-200   DbPool.start()
    open=true → connections established
    LOG=[DbPool.start]

  getPhase=0      OrderService.start()
    db.open=true ✓ (DB is ready because lower phase started first)
    ready=true → order processing enabled
    LOG=[DbPool.start, OrderService.start]

  getPhase=9000   ReadinessProbe.start()
    ready=true → /readyz returns 200 OK
    LOG=[..., ReadinessProbe.start]

  getPhase=MAX    HttpServer.start()
    bound=true → port 8080 bound
    readyz=200 OK ✓ (probe already flipped before port opened)
    LOG=[..., HttpServer.start]

context.close() — sorted by phase descending:

  getPhase=MAX    HttpServer.stop()       → port closed
  getPhase=9000   ReadinessProbe.stop()   → /readyz=503, sleep 200ms (LB drains)
  getPhase=0      OrderService.stop()     → processing disabled, processed=N
  getPhase=-200   DbPool.stop()           → connections closed
```

## 7. Gotchas & takeaways

> **Beans in the same phase start in parallel, not sequentially.** If two beans both have `getPhase()=0`, `DefaultLifecycleProcessor` starts them concurrently and waits for both. Don't assume ordering within a phase — use different phase numbers if you need explicit ordering.

> **`getPhase()` only matters for `SmartLifecycle` beans.** Plain `Lifecycle` beans (without `SmartLifecycle`) are all treated as phase 0 and only start/stop when `context.start()` / `context.stop()` are called explicitly — not automatically on `context.refresh()`.

- Spring's own messaging infrastructure uses `Integer.MIN_VALUE` for its `SmartLifecycle` beans. Don't use `Integer.MIN_VALUE` in application code unless you genuinely need to start before Spring's own infrastructure.
- `DefaultLifecycleProcessor.timeoutPerShutdownPhase` defaults to 30 seconds. Set it lower in tests to speed up teardown: `((DefaultLifecycleProcessor) ctx.getBean(LifecycleProcessor.class)).setTimeoutPerShutdownPhase(1000)`.
- If a bean throws from `start()`, the exception propagates and the context refresh fails — handle startup errors carefully in `start()`.
- In Spring Boot, you rarely need to tune phases manually — Spring Boot's auto-configuration uses appropriate phases for embedded servers, message listeners, etc. Check the defaults before overriding.
