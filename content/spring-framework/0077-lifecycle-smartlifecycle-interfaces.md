---
card: spring-framework
gi: 77
slug: lifecycle-smartlifecycle-interfaces
title: Lifecycle & SmartLifecycle interfaces
---

## 1. What it is

`Lifecycle` and `SmartLifecycle` are Spring interfaces for beans that need to **start and stop in response to the container's start/stop signal** — distinct from `@PostConstruct` / `@PreDestroy` which fire at bean creation/destruction. `Lifecycle` provides `start()`, `stop()`, and `isRunning()`. `SmartLifecycle` extends it with `getPhase()` (ordering), `isAutoStartup()` (start on context refresh), and an async-aware `stop(Runnable callback)`.

```java
@Component
public class BackgroundPoller implements SmartLifecycle {

    private Thread pollerThread;
    private volatile boolean running = false;

    @Override public boolean isAutoStartup() { return true; }
    @Override public int     getPhase()      { return 0; }

    @Override
    public void start() {
        running = true;
        pollerThread = new Thread(() -> {
            while (running) { poll(); sleep(5000); }
        }, "poller");
        pollerThread.setDaemon(true);
        pollerThread.start();
    }

    @Override
    public void stop(Runnable callback) {
        running = false;
        // signal the poller to stop, then call callback when truly stopped
        new Thread(() -> {
            try { pollerThread.join(10_000); } catch (InterruptedException ignored) {}
            callback.run();  // MUST call this — tells Spring shutdown can proceed
        }).start();
    }

    @Override public boolean isRunning() { return running; }
    private void poll()  { /* fetch messages */ }
    private void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException ignored) {} }
}
```

In one sentence: **`Lifecycle` / `SmartLifecycle` let beans participate in container start/stop signals (independent of creation/destruction), with `SmartLifecycle` adding auto-start, phase-based ordering, and async shutdown via a completion callback.**

## 2. Why & when

Use `Lifecycle` / `SmartLifecycle` for:

- **Background threads / pollers** — start polling after the context is fully refreshed; stop gracefully on shutdown.
- **Message listeners / consumers** — start consuming after all dependencies are wired.
- **Scheduled executors** — start task execution when the context is live; drain and stop cleanly.
- **External connections** — connect to a message broker after the application is ready.

Do NOT use `Lifecycle` / `SmartLifecycle` if you just need post-injection setup — `@PostConstruct` is the right tool. `Lifecycle.start()` fires on `context.refresh()` (for `SmartLifecycle` with `isAutoStartup()=true`) or on an explicit `context.start()` — after all beans are fully initialised.

**Key difference from `@PostConstruct`**: `@PostConstruct` fires during bean creation (before context is fully refreshed). `SmartLifecycle.start()` fires after ALL beans are created and the context is fully refreshed.

## 3. Core concept

```
Lifecycle interface:
  void start()
  void stop()
  boolean isRunning()

SmartLifecycle extends Lifecycle:
  boolean isAutoStartup()   // true → start() called on context.refresh()
  int     getPhase()        // lower phase number = starts EARLIER, stops LATER
  void    stop(Runnable callback)  // async-capable stop; MUST call callback.run()
                                   // when done (even if stop was synchronous)

Startup order:   lower phase → earlier start
  Phase Integer.MIN_VALUE starts FIRST.
  Phase 0 is the default. Spring infrastructure beans use negative phases.

Shutdown order:  higher phase → earlier stop (reverse of startup)
  Phase 2147483647 stops FIRST.
  Phase 0 stops before phase -1 (poller stops before messaging infra).

Timeline relative to bean lifecycle:
  ① Bean construction (new Bean())
  ② Dependency injection
  ③ @PostConstruct / afterPropertiesSet / init-method   ← bean creation callbacks
  ④ Context refresh completes
  ⑤ SmartLifecycle.start()                             ← Lifecycle start (ALL beans ready)
  ... application running ...
  ⑥ context.stop() or context.close()
  ⑦ SmartLifecycle.stop(callback) → callback.run()     ← Lifecycle stop
  ⑧ @PreDestroy / destroy() / destroy-method           ← bean destruction callbacks
```

## 4. Diagram

<svg viewBox="0 0 680 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SmartLifecycle phase ordering and timeline vs PostConstruct">
  <defs>
    <marker id="a77" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b77" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="203" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">SmartLifecycle: start after context refresh, stop before bean destruction</text>

  <!-- Timeline (horizontal) -->
  <line x1="15" y1="55" x2="660" y2="55" stroke="#8b949e" stroke-width="1"/>
  <text x="338" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Time →</text>

  <!-- Milestones -->
  <circle cx="60"  cy="55" r="5" fill="#8b949e"/>
  <text x="60"  y="73" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">construct</text>
  <text x="60"  y="83" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">+ inject</text>

  <circle cx="175" cy="55" r="5" fill="#8b949e"/>
  <text x="175" y="73" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@PostConstruct</text>
  <text x="175" y="83" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">init callbacks</text>

  <circle cx="305" cy="55" r="6" fill="#6db33f"/>
  <text x="305" y="73" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">context.refresh()</text>
  <text x="305" y="83" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">ALL beans ready</text>

  <circle cx="425" cy="55" r="6" fill="#6db33f"/>
  <text x="425" y="73" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">SmartLifecycle</text>
  <text x="425" y="83" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">.start()</text>

  <circle cx="545" cy="55" r="5" fill="#8b949e"/>
  <text x="545" y="73" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">stop(callback)</text>

  <circle cx="630" cy="55" r="5" fill="#8b949e"/>
  <text x="630" y="73" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@PreDestroy</text>

  <!-- Phase ordering table -->
  <rect x="10" y="95" width="655" height="110" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="113" fill="#8b949e" font-size="9" font-family="monospace">Phase ordering — startup: lower phase first; shutdown: higher phase first</text>
  <line x1="12" y1="117" x2="662" y2="117" stroke="#8b949e" stroke-width="0.5"/>
  <text x="22" y="132" fill="#8b949e" font-size="9" font-family="monospace">getPhase()  Startup  Shutdown  Typical use</text>
  <line x1="12" y1="136" x2="662" y2="136" stroke="#8b949e" stroke-width="0.4" stroke-dasharray="3,3"/>
  <text x="22" y="151" fill="#8b949e" font-size="9" font-family="monospace">-2147...    1st      LAST      Spring infra (MessageListenerContainer)</text>
  <text x="22" y="166" fill="#79c0ff" font-size="9" font-family="monospace">0 (default) middle   middle    Application pollers / event buses</text>
  <text x="22" y="181" fill="#6db33f" font-size="9" font-family="monospace">2147...     LAST     1st       Graceful request drain before infra stops</text>
  <text x="22" y="195" fill="#8b949e" font-size="7.5" font-family="sans-serif">Rule: SmartLifecycle.stop(callback) MUST call callback.run() — Spring hangs if not.</text>
</svg>

`SmartLifecycle.start()` fires after the context is fully refreshed — all beans are ready. Shutdown is the reverse: higher phases stop first.

## 5. Runnable example

Scenario: a `BackgroundJobRunner` that polls for work — it must start only after all beans are wired (not during construction) and stop gracefully when the context shuts down.

### Level 1 — Basic

A `Lifecycle` bean: `start()` launches a poller thread, `stop()` signals it to stop.

```java
// SmartLifecycleDemo.java — run with: java SmartLifecycleDemo.java
import java.util.concurrent.atomic.*;

public class SmartLifecycleDemo {

    // ── simulated Spring Lifecycle interface ──────────────────────────
    interface Lifecycle { void start(); void stop(); boolean isRunning(); }

    static class BackgroundPoller implements Lifecycle {
        private volatile boolean running = false;
        private Thread thread;
        private final AtomicInteger pollCount = new AtomicInteger();

        @Override
        public void start() {
            System.out.println("[Lifecycle.start()] launching poller thread");
            running = true;
            thread = new Thread(() -> {
                while (running) {
                    int n = pollCount.incrementAndGet();
                    System.out.println("  [POLL #" + n + "] checking for new jobs...");
                    try { Thread.sleep(300); } catch (InterruptedException e) { break; }
                }
                System.out.println("  [POLL] thread exited cleanly");
            }, "job-poller");
            thread.setDaemon(true);
            thread.start();
        }

        @Override
        public void stop() {
            System.out.println("[Lifecycle.stop()] stopping poller (polls=" + pollCount.get() + ")");
            running = false;
            thread.interrupt();
            try { thread.join(2000); } catch (InterruptedException ignored) {}
            System.out.println("[Lifecycle.stop()] poller stopped");
        }

        @Override public boolean isRunning() { return running; }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== Phase 1: bean creation (@PostConstruct equivalent) ===");
        BackgroundPoller poller = new BackgroundPoller();
        System.out.println("[BEAN CREATED] isRunning=" + poller.isRunning() + " — not yet started");

        System.out.println("\n=== Phase 2: context.refresh() → Lifecycle.start() ===");
        poller.start();

        System.out.println("\n=== Application running for ~1 second ===");
        Thread.sleep(1100);

        System.out.println("\n=== context.stop() → Lifecycle.stop() ===");
        poller.stop();

        System.out.println("[AFTER STOP] isRunning=" + poller.isRunning());
    }
}
```

How to run: `java SmartLifecycleDemo.java`

`BackgroundPoller` is created but NOT started during construction. `start()` (called by Spring after `context.refresh()`) launches the poller thread. `stop()` signals the thread to exit and waits for it to join. `isRunning()` reflects current state.

### Level 2 — Intermediate

`SmartLifecycle` with `isAutoStartup()`, `getPhase()`, and async `stop(Runnable callback)`.

```java
// SmartLifecycleDemo2.java — run with: java SmartLifecycleDemo2.java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class SmartLifecycleDemo2 {

    // ── simulated SmartLifecycle interface ────────────────────────────
    interface SmartLifecycle {
        boolean isAutoStartup();
        int     getPhase();
        void    start();
        void    stop(Runnable callback);
        boolean isRunning();
    }

    static class MetricsCollectorLifecycle implements SmartLifecycle {
        private final ScheduledExecutorService scheduler =
            Executors.newSingleThreadScheduledExecutor(r -> new Thread(r, "metrics-flush"));
        private final AtomicInteger flushCount = new AtomicInteger();
        private volatile boolean running = false;
        private ScheduledFuture<?> task;

        // Auto-start when context refreshes; no explicit context.start() needed
        @Override public boolean isAutoStartup() { return true; }

        // Phase 0: start after infrastructure (negative phases), stop before infra
        @Override public int getPhase() { return 0; }

        @Override
        public void start() {
            System.out.println("[SmartLifecycle.start()] scheduling metrics flush every 400ms");
            running = true;
            task = scheduler.scheduleAtFixedRate(() -> {
                int n = flushCount.incrementAndGet();
                System.out.println("  [METRICS FLUSH #" + n + "] flushing counters to backend");
            }, 0, 400, TimeUnit.MILLISECONDS);
        }

        @Override
        public void stop(Runnable callback) {
            // Async stop: cancel task, shutdown scheduler, THEN signal Spring via callback
            System.out.println("[SmartLifecycle.stop(callback)] draining scheduler...");
            running = false;
            task.cancel(false);  // don't interrupt in-progress flush
            scheduler.shutdown();
            new Thread(() -> {
                try {
                    if (!scheduler.awaitTermination(3, TimeUnit.SECONDS)) {
                        scheduler.shutdownNow();
                    }
                } catch (InterruptedException e) {
                    scheduler.shutdownNow();
                }
                System.out.println("[SmartLifecycle.stop(callback)] scheduler drained, flushCount="
                    + flushCount.get() + " — calling callback");
                callback.run();  // ← CRITICAL: must call this so Spring's shutdown can proceed
            }, "metrics-stopper").start();
        }

        @Override public boolean isRunning() { return running; }
    }

    // ── Simulated context.refresh() + context.close() ────────────────
    static void simulateContextRefreshAndClose(SmartLifecycle bean) throws InterruptedException {
        System.out.println("--- context.refresh() ---");
        if (bean.isAutoStartup()) {
            System.out.println("[context] isAutoStartup=true → calling start() phase=" + bean.getPhase());
            bean.start();
        }

        System.out.println("\n--- Application running for ~1.5 seconds ---");
        Thread.sleep(1500);

        System.out.println("\n--- context.close() → stop(callback) ---");
        CountDownLatch latch = new CountDownLatch(1);
        bean.stop(latch::countDown);  // Spring waits for callback before proceeding with shutdown
        latch.await(5, TimeUnit.SECONDS);
        System.out.println("[context] callback received — proceeding with bean destruction (@PreDestroy...)");
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== Bean creation (all wiring done) ===");
        MetricsCollectorLifecycle mc = new MetricsCollectorLifecycle();
        System.out.println("[CREATED] isRunning=" + mc.isRunning() + " isAutoStartup=" + mc.isAutoStartup());

        simulateContextRefreshAndClose(mc);
        System.out.println("[DONE] isRunning=" + mc.isRunning());
    }
}
```

How to run: `java SmartLifecycleDemo2.java`

`isAutoStartup()` returning `true` means Spring calls `start()` automatically after `context.refresh()`. `stop(Runnable callback)` is asynchronous — it spins up a stopper thread, drains the scheduler, then calls `callback.run()` to signal Spring that the bean is fully stopped. Spring's shutdown waits for the callback before proceeding to `@PreDestroy`.

### Level 3 — Advanced

Two `SmartLifecycle` beans with different phases — a message consumer (`phase=0`) that depends on a message broker (`phase=-1`); broker starts first, consumer stops first on shutdown.

```java
// SmartLifecycleDemo3.java — run with: java SmartLifecycleDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class SmartLifecycleDemo3 {

    interface SmartLifecycle {
        boolean isAutoStartup();
        int     getPhase();
        void    start();
        void    stop(Runnable callback);
        boolean isRunning();
    }

    static final List<String> START_LOG = new ArrayList<>();
    static final List<String> STOP_LOG  = new ArrayList<>();

    // ── Phase -1: message broker infrastructure ───────────────────────
    static class FakeBrokerConnection implements SmartLifecycle {
        private volatile boolean connected = false;
        @Override public boolean isAutoStartup() { return true; }
        @Override public int     getPhase()      { return -1; }  // starts BEFORE phase 0

        @Override
        public void start() {
            System.out.println("[Phase -1] FakeBrokerConnection.start() — connecting to broker");
            connected = true;
            START_LOG.add("FakeBrokerConnection");
            System.out.println("[Phase -1] connected=true");
        }

        @Override
        public void stop(Runnable callback) {
            System.out.println("[Phase -1] FakeBrokerConnection.stop() — disconnecting (consumer should be stopped first)");
            connected = false;
            STOP_LOG.add("FakeBrokerConnection");
            callback.run();  // synchronous — just call immediately
        }

        @Override public boolean isRunning() { return connected; }
        boolean isConnected() { return connected; }
    }

    // ── Phase 0: message consumer (depends on broker being connected) ─
    static class MessageConsumer implements SmartLifecycle {
        private final FakeBrokerConnection broker;
        private volatile boolean consuming = false;
        private final AtomicInteger msgCount = new AtomicInteger();
        private Thread consumerThread;

        MessageConsumer(FakeBrokerConnection broker) { this.broker = broker; }

        @Override public boolean isAutoStartup() { return true; }
        @Override public int     getPhase()      { return 0; }   // starts AFTER phase -1

        @Override
        public void start() {
            if (!broker.isConnected())
                throw new IllegalStateException("Cannot start consumer — broker not connected!");
            System.out.println("[Phase  0] MessageConsumer.start() — broker.connected=" + broker.isConnected()
                + " (must be true ✓)");
            consuming = true;
            consumerThread = new Thread(() -> {
                while (consuming) {
                    int n = msgCount.incrementAndGet();
                    System.out.println("  [MSG #" + n + "] consumed via " + broker.isConnected());
                    try { Thread.sleep(350); } catch (InterruptedException e) { break; }
                }
            }, "consumer");
            consumerThread.setDaemon(true);
            consumerThread.start();
            START_LOG.add("MessageConsumer");
        }

        @Override
        public void stop(Runnable callback) {
            System.out.println("[Phase  0] MessageConsumer.stop() — draining consumer (messages=" + msgCount.get() + ")");
            consuming = false;
            consumerThread.interrupt();
            new Thread(() -> {
                try { consumerThread.join(3000); } catch (InterruptedException ignored) {}
                STOP_LOG.add("MessageConsumer");
                System.out.println("[Phase  0] MessageConsumer stopped — calling callback");
                callback.run();  // MUST call — Spring waits for this
            }).start();
        }

        @Override public boolean isRunning() { return consuming; }
    }

    // ── Container simulation with phase ordering ───────────────────────
    static void lifecycle(List<SmartLifecycle> beans) throws InterruptedException {
        System.out.println("=== context.refresh() — startup in PHASE ORDER (lower first) ===");
        // Sort by phase ascending for startup
        List<SmartLifecycle> startOrder = new ArrayList<>(beans);
        startOrder.sort(Comparator.comparingInt(SmartLifecycle::getPhase));
        for (SmartLifecycle b : startOrder) {
            if (b.isAutoStartup()) b.start();
        }
        System.out.println("[START LOG] " + START_LOG);

        System.out.println("\n=== Application running for ~1.2 seconds ===");
        Thread.sleep(1200);

        System.out.println("\n=== context.close() — shutdown in REVERSE PHASE ORDER (higher first) ===");
        // Sort by phase descending for shutdown (higher phase stops first)
        List<SmartLifecycle> stopOrder = new ArrayList<>(beans);
        stopOrder.sort(Comparator.comparingInt(SmartLifecycle::getPhase).reversed());
        CountDownLatch latch = new CountDownLatch(stopOrder.size());
        for (SmartLifecycle b : stopOrder) {
            if (b.isRunning()) b.stop(latch::countDown);
            else latch.countDown();
        }
        latch.await(5, TimeUnit.SECONDS);
        System.out.println("[STOP LOG]  " + STOP_LOG);
    }

    public static void main(String[] args) throws InterruptedException {
        FakeBrokerConnection broker   = new FakeBrokerConnection();
        MessageConsumer      consumer = new MessageConsumer(broker);
        lifecycle(List.of(broker, consumer));
        System.out.println("[ASSERT] start order correct (broker first): "
            + List.of("FakeBrokerConnection","MessageConsumer").equals(START_LOG));
        System.out.println("[ASSERT] stop order reversed (consumer first): "
            + List.of("MessageConsumer","FakeBrokerConnection").equals(STOP_LOG));
    }
}
```

How to run: `java SmartLifecycleDemo3.java`

`FakeBrokerConnection` has `phase=-1` so it starts first (broker connects). `MessageConsumer` has `phase=0` so it starts second (can safely use the broker). On shutdown, the order reverses: `MessageConsumer` stops first (drains messages), then `FakeBrokerConnection` stops (disconnects). The assertions verify both logs.

## 6. Walkthrough

**Level 3 phase lifecycle trace:**

```
context.refresh():
  Sort by phase ascending: FakeBrokerConnection(-1) → MessageConsumer(0)

  FakeBrokerConnection.start()      phase=-1
    connected=true
    START_LOG=[FakeBrokerConnection]

  MessageConsumer.start()           phase=0
    broker.isConnected() = true ✓ (would throw if false)
    consuming=true, consumerThread launched
    START_LOG=[FakeBrokerConnection, MessageConsumer]

Application 1.2 seconds:
  MSG #1, #2, #3... consumed

context.close():
  Sort by phase descending: MessageConsumer(0) → FakeBrokerConnection(-1)

  MessageConsumer.stop(callback)    phase=0 — stops FIRST
    consuming=false, thread interrupted
    [waits up to 3s for join]
    STOP_LOG=[MessageConsumer]
    callback.run() → latch countdown

  FakeBrokerConnection.stop(callback)  phase=-1 — stops SECOND
    connected=false
    STOP_LOG=[MessageConsumer, FakeBrokerConnection]
    callback.run()

[ASSERT] start=[FakeBrokerConnection, MessageConsumer] ✓
[ASSERT] stop =[MessageConsumer, FakeBrokerConnection] ✓ (reversed)
```

## 7. Gotchas & takeaways

> **`stop(Runnable callback)` MUST call `callback.run()` — even on failure.** If you forget to call it, Spring's shutdown will hang indefinitely waiting for the phase to complete. Wrap in try-finally: `try { doStop(); } finally { callback.run(); }`.

> **`SmartLifecycle.start()` fires AFTER `@PostConstruct`.** It fires only after the entire context is refreshed — all beans, all `@PostConstruct` methods. This is the right hook for starting a thread that calls other beans. `@PostConstruct` fires too early (sibling beans may not be ready).

- `isRunning()` must return `false` before `start()` is called and `true` after. Spring checks it to avoid calling `start()` twice (e.g., if context is refreshed multiple times).
- Beans implementing only the basic `Lifecycle` (not `SmartLifecycle`) are NOT auto-started — you must call `context.start()` explicitly.
- Spring's `DefaultLifecycleProcessor` uses a configurable `timeoutPerShutdownPhase` (default 30 seconds) — if all `stop(callback)` calls in a phase don't complete within the timeout, Spring moves on anyway.
- Use `SmartLifecycle` for infrastructure and application-level start/stop. Use `ApplicationListener<ContextRefreshedEvent>` for one-time "context is ready" notifications.
