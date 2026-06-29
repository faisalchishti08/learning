---
card: spring-framework
gi: 28
slug: graceful-shutdown-close
title: Graceful shutdown & close()
---

## 1. What it is

**Graceful shutdown** means telling the Spring container to stop cleanly: finishing in-flight work, releasing resources, and calling destroy callbacks on every singleton bean — in the reverse order they were created.

The entry point is `ConfigurableApplicationContext.close()`:

```java
ConfigurableApplicationContext ctx =
    new AnnotationConfigApplicationContext(AppConfig.class);

// ... application runs ...

ctx.close();  // triggers graceful shutdown
```

Or register a JVM shutdown hook (preferred for long-running apps):

```java
ctx.registerShutdownHook();  // ctx.close() called automatically on JVM exit
```

During `close()`, Spring calls these callbacks on each bean (in reverse creation order):
1. `@PreDestroy` methods
2. `DisposableBean.destroy()`
3. Custom `destroyMethod` attribute from `@Bean(destroyMethod="...")`

In one sentence: **`close()` is the counterpart to `refresh()` — it tears down the container cleanly, firing destroy callbacks so beans can release database connections, thread pools, file handles, and other resources.**

## 2. Why & when

Without graceful shutdown:
- Database connection pools are abandoned, exhausting connections on the DB server.
- Thread pools keep running, blocking JVM exit or leaking threads.
- In-flight messages are lost rather than acknowledged.
- Temporary files are not deleted.
- Cache flush writes are skipped.

Call `close()` / `registerShutdownHook()` for any long-running Spring app (web server, batch job, message consumer, background service). In Spring Boot, `SpringApplication.run()` registers the shutdown hook automatically. In standalone `AnnotationConfigApplicationContext` apps you must register it manually.

Graceful shutdown also matters in cloud environments: when Kubernetes sends `SIGTERM` before killing a pod, the JVM shutdown hook fires `ctx.close()` — giving beans a window (typically 30 seconds) to drain work before the process dies.

## 3. Core concept

`close()` runs in four stages:

```
ctx.close()
  1. Mark context as closed (new getBean() calls throw)
  2. Publish ContextClosedEvent
  3. LifecycleProcessor.onClose() — stop SmartLifecycle beans
  4. destroySingletons()
       for each singleton in REVERSE creation order:
         @PreDestroy methods
         DisposableBean.destroy()
         destroyMethod (from @Bean annotation)
```

`registerShutdownHook()` registers a JVM `Runtime.addShutdownHook(Thread)` that calls `close()`. This thread fires when:
- `System.exit()` is called
- All non-daemon threads finish
- The OS sends `SIGTERM` (Ctrl+C, Kubernetes pod termination)

```
Bean creation order:  A → B → C
Destroy order:        C → B → A
```

The reverse order matters because C may depend on B; destroying B before C would break C's cleanup.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="close() four stages: mark closed, publish event, stop lifecycle, destroy singletons in reverse order">
  <defs>
    <marker id="a28" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Stage boxes -->
  <rect x="10"  y="60" width="145" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="82"  y="83" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">1. Mark closed</text>
  <text x="82"  y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">new getBean() throws</text>

  <rect x="178" y="60" width="145" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="250" y="83" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">2. ContextClosedEvent</text>
  <text x="250" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">listeners notified</text>

  <rect x="346" y="60" width="145" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="418" y="83" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">3. Lifecycle stop</text>
  <text x="418" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">SmartLifecycle.stop()</text>

  <rect x="514" y="60" width="156" height="56" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="592" y="83" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">4. destroySingletons</text>
  <text x="592" y="100" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">reverse creation order</text>

  <line x1="155" y1="88" x2="176" y2="88" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a28)"/>
  <line x1="323" y1="88" x2="344" y2="88" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a28)"/>
  <line x1="491" y1="88" x2="512" y2="88" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a28)"/>

  <!-- Destroy callbacks -->
  <rect x="400" y="148" width="200" height="68" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="500" y="168" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Per bean (reverse order):</text>
  <text x="500" y="183" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">① @PreDestroy methods</text>
  <text x="500" y="198" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">② DisposableBean.destroy()</text>
  <text x="500" y="213" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">③ @Bean(destroyMethod=...)</text>

  <line x1="592" y1="116" x2="592" y2="146" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a28)"/>

  <!-- registerShutdownHook -->
  <rect x="10" y="150" width="175" height="52" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="97" y="172" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">registerShutdownHook()</text>
  <text x="97" y="188" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JVM SIGTERM → calls close()</text>
</svg>

`close()` marks the context, fires events, stops lifecycle beans, then destroys singletons in reverse creation order. `registerShutdownHook()` wires this to JVM exit.

## 5. Runnable example

Scenario: a background job processor with a thread-pool worker and a database connection pool. Both must be released cleanly on shutdown.

### Level 1 — Basic

One bean with `@PreDestroy` — the simplest shutdown callback.

```java
// ShutdownDemo.java — run with: java ShutdownDemo.java
import java.util.*;
import java.util.concurrent.*;

public class ShutdownDemo {

    static class JobProcessor {
        private final ExecutorService pool = Executors.newFixedThreadPool(2);
        private volatile boolean running = true;

        void submit(String job) {
            if (!running) { System.out.println("  [WARN] Processor closed, rejecting: " + job); return; }
            pool.submit(() -> {
                System.out.println("  [JOB] Processing: " + job);
                try { Thread.sleep(10); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            });
        }

        // @PreDestroy equivalent — called by Spring on close()
        void destroy() throws InterruptedException {
            System.out.println("  [@PreDestroy] JobProcessor.destroy() — shutting down thread pool");
            running = false;
            pool.shutdown();
            boolean done = pool.awaitTermination(5, TimeUnit.SECONDS);
            System.out.println("  [@PreDestroy] Thread pool terminated: " + done);
        }
    }

    // Simulates container close() calling destroy callbacks
    static class Ctx {
        private final List<Object> beans = new ArrayList<>();
        void register(Object bean) { beans.add(bean); }
        void close() throws Exception {
            System.out.println("[CTX] close() — destroying singletons in reverse order...");
            List<Object> reversed = new ArrayList<>(beans);
            Collections.reverse(reversed);
            for (Object b : reversed) {
                var destroy = b.getClass().getDeclaredMethod("destroy");
                System.out.println("  Calling destroy on: " + b.getClass().getSimpleName());
                destroy.invoke(b);
            }
            System.out.println("[CTX] Shutdown complete.");
        }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();
        JobProcessor processor = new JobProcessor();
        ctx.register(processor);

        System.out.println("=== Application running ===");
        processor.submit("report-gen-001");
        processor.submit("email-batch-002");
        processor.submit("invoice-003");

        Thread.sleep(50);  // let jobs start

        System.out.println("\n=== Shutdown initiated ===");
        ctx.close();

        // After close(), new jobs are rejected
        processor.submit("too-late-job");
    }
}
```

How to run: `java ShutdownDemo.java`

`destroy()` mirrors `@PreDestroy`. It sets `running = false`, tells the executor to stop accepting new tasks, then waits up to 5 seconds for in-flight tasks to complete. After `close()`, the rejected job prints the warning.

### Level 2 — Intermediate

Three beans created in order A → B → C. Shutdown destroys C → B → A to respect dependency order.

```java
// ShutdownDemo2.java — run with: java ShutdownDemo2.java
import java.util.*;
import java.util.concurrent.*;

public class ShutdownDemo2 {

    // A: shared cache (created first, destroyed last)
    static class ResultCache {
        private final Map<String, String> store = new ConcurrentHashMap<>();
        void put(String k, String v) { store.put(k, v); }
        int size() { return store.size(); }
        void destroy() {
            System.out.println("  [@PreDestroy] ResultCache.destroy() — flushing " + store.size() + " entries to disk");
            store.clear();
        }
    }

    // B: database connection pool (depends on nothing, created second)
    static class ConnectionPool {
        private int active = 3;
        String borrow() { active--; return "conn-" + (3 - active); }
        void release(String c) { active++; }
        int available() { return active; }
        void destroy() throws InterruptedException {
            System.out.println("  [@PreDestroy] ConnectionPool.destroy() — closing " + (3 - active) + " active connections");
            Thread.sleep(30);  // simulate drain time
            active = 0;
            System.out.println("  [@PreDestroy] All connections closed.");
        }
    }

    // C: job processor (depends on B and C, created last, destroyed first)
    static class JobProcessor {
        private final ConnectionPool pool;
        private final ResultCache    cache;
        private volatile boolean     stopped = false;

        JobProcessor(ConnectionPool pool, ResultCache cache) {
            this.pool = pool; this.cache = cache;
        }

        void process(String job) {
            if (stopped) return;
            String conn = pool.borrow();
            String result = "result-for-" + job;
            System.out.println("  [JOB] " + job + " via " + conn + " → " + result);
            cache.put(job, result);
            pool.release(conn);
        }

        void destroy() {
            System.out.println("  [@PreDestroy] JobProcessor.destroy() — draining jobs");
            stopped = true;
            System.out.println("  [@PreDestroy] JobProcessor stopped. Pool available: " + pool.available());
        }
    }

    static class OrderedCtx {
        private final List<Object>  created = new ArrayList<>();  // creation order

        void register(Object bean) {
            created.add(bean);
            System.out.println("  [CTX] Bean registered: " + bean.getClass().getSimpleName());
        }

        void close() throws Exception {
            System.out.println("\n[CTX] close() — destroying in REVERSE creation order:");
            List<Object> reversed = new ArrayList<>(created);
            Collections.reverse(reversed);
            for (Object b : reversed) {
                try {
                    var m = b.getClass().getDeclaredMethod("destroy");
                    System.out.println("  Destroying: " + b.getClass().getSimpleName());
                    m.invoke(b);
                } catch (NoSuchMethodException ignored) {}
            }
            System.out.println("[CTX] Shutdown complete.");
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Container startup (creation order: A→B→C) ===");
        OrderedCtx ctx = new OrderedCtx();
        ResultCache    cache = new ResultCache();     // A
        ConnectionPool pool  = new ConnectionPool();  // B
        JobProcessor   jobs  = new JobProcessor(pool, cache);  // C
        ctx.register(cache);
        ctx.register(pool);
        ctx.register(jobs);

        System.out.println("\n=== Application running ===");
        jobs.process("order-gen-001");
        jobs.process("invoice-002");
        jobs.process("report-003");

        System.out.println("  Cache size: " + cache.size() + " | Pool available: " + pool.available());

        ctx.close();
    }
}
```

How to run: `java ShutdownDemo2.java`

Creation order A → B → C; destroy order C → B → A. `JobProcessor` stops first (no more borrowing from the pool), then the `ConnectionPool` drains, then the `ResultCache` flushes. If A was destroyed before C, `JobProcessor.destroy()` would call `pool.available()` on a closed pool — a real bug in production.

### Level 3 — Advanced

Add `registerShutdownHook()` — JVM exit fires `close()` automatically — and a `ContextClosedEvent` listener that logs shutdown intent before beans are destroyed.

```java
// ShutdownDemo3.java — run with: java ShutdownDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;

public class ShutdownDemo3 {

    record Job(String id, String payload) {}

    static class MessageQueue {
        private final Queue<Job> pending = new ConcurrentLinkedQueue<>();
        void enqueue(Job j) { pending.add(j); System.out.println("  [MQ] Enqueued: " + j.id()); }
        Optional<Job> poll() { return Optional.ofNullable(pending.poll()); }
        int size() { return pending.size(); }
    }

    static class JobWorker {
        private final MessageQueue mq;
        private volatile boolean   running = true;
        private final Thread       thread;

        JobWorker(MessageQueue mq) {
            this.mq = mq;
            this.thread = new Thread(this::processLoop, "job-worker");
            this.thread.setDaemon(true);
            this.thread.start();
        }

        void processLoop() {
            while (running || mq.size() > 0) {
                mq.poll().ifPresent(j -> {
                    System.out.println("  [WORKER] Processing: " + j.id() + " payload=" + j.payload());
                    try { Thread.sleep(20); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                });
            }
        }

        // Drain queue gracefully before dying
        void destroy() throws InterruptedException {
            System.out.println("  [@PreDestroy] JobWorker.destroy() — draining " + mq.size() + " remaining jobs...");
            running = false;
            thread.join(3000);  // wait up to 3s for drain
            System.out.println("  [@PreDestroy] JobWorker stopped. Remaining: " + mq.size());
        }
    }

    // Shutdown lifecycle context with event support
    static class LifecycleCtx {
        private final List<Object>   beans    = new ArrayList<>();
        private final List<Runnable> onClose  = new ArrayList<>();
        private boolean              closed   = false;

        void register(Object bean) { beans.add(bean); }
        void onContextClosed(Runnable listener) { onClose.add(listener); }

        void registerShutdownHook() {
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                System.out.println("\n[SHUTDOWN-HOOK] JVM exit detected — calling close()...");
                try { close(); } catch (Exception e) { e.printStackTrace(); }
            }, "shutdown-hook"));
            System.out.println("[CTX] Shutdown hook registered.");
        }

        void close() throws Exception {
            if (closed) return;
            closed = true;
            System.out.println("[CTX] Step 2: ContextClosedEvent → notifying listeners...");
            onClose.forEach(Runnable::run);

            System.out.println("[CTX] Step 4: destroySingletons (reverse order)...");
            List<Object> reversed = new ArrayList<>(beans);
            Collections.reverse(reversed);
            for (Object b : reversed) {
                try {
                    var m = b.getClass().getDeclaredMethod("destroy");
                    System.out.println("  Destroying: " + b.getClass().getSimpleName());
                    m.invoke(b);
                } catch (NoSuchMethodException ignored) {}
            }
            System.out.println("[CTX] Shutdown complete.");
        }
    }

    public static void main(String[] args) throws Exception {
        LifecycleCtx ctx = new LifecycleCtx();

        // ContextClosedEvent listener — logs before any bean is destroyed
        ctx.onContextClosed(() -> System.out.println("  [EVENT] ContextClosedEvent received — shutdown in progress"));

        MessageQueue mq     = new MessageQueue();
        JobWorker    worker = new JobWorker(mq);
        ctx.register(mq);
        ctx.register(worker);
        ctx.registerShutdownHook();

        System.out.println("=== App running — enqueuing jobs ===");
        mq.enqueue(new Job("j001", "generate-report"));
        mq.enqueue(new Job("j002", "send-invoices"));
        mq.enqueue(new Job("j003", "backup-data"));

        Thread.sleep(30);  // let worker pick up some

        System.out.println("\n=== Triggering shutdown (simulates SIGTERM) ===");
        ctx.close();  // in production this fires from the JVM shutdown hook
    }
}
```

How to run: `java ShutdownDemo3.java`

`ContextClosedEvent` fires first (step 2) — a chance to log or alert before any bean is destroyed. `JobWorker.destroy()` sets `running = false` but then calls `thread.join(3000)` — waiting up to 3 seconds for in-flight jobs to finish. Jobs already in the queue are drained. `MessageQueue.destroy()` has no cleanup needed so it is skipped. In a Kubernetes deployment, the 3-second drain window corresponds to the `terminationGracePeriodSeconds` budget.

## 6. Walkthrough

**Level 3 — `ctx.close()` execution:**

```
close()
  closed = false → set true (idempotent guard)

Step 2 — ContextClosedEvent:
  → onClose listener runs:
      "[EVENT] ContextClosedEvent received — shutdown in progress"

Step 4 — destroySingletons (reverse of [mq, worker] = [worker, mq]):
  → "Destroying: JobWorker"
      worker.destroy()
        → running = false
        → "[WORKER] Processing: j003 payload=backup-data"  (drain continues)
        → thread.join(3000) — waits for processLoop to exit
        → "[PreDestroy] JobWorker stopped. Remaining: 0"
  → "Destroying: MessageQueue"
      mq has no destroy() → NoSuchMethodException → skipped

"[CTX] Shutdown complete."
```

**Data state at each shutdown stage:**

| Stage | `mq.size()` | `worker.running` | Thread |
|---|---|---|---|
| Before close() | 3 | true | processing |
| After ContextClosedEvent | 2-3 | true | processing |
| destroy() called | 0-2 | false | draining |
| after thread.join | 0 | false | terminated |

## 7. Gotchas & takeaways

> **`@PreDestroy` is NOT called on prototype-scoped beans.** Spring manages the lifecycle of singleton beans; once it hands you a prototype instance, it forgets about it. You must call cleanup methods on prototypes yourself.

> **Calling `close()` twice is safe on `AbstractApplicationContext`** — it checks an `active` flag and is idempotent. The JVM shutdown hook and an explicit `close()` call can race; Spring handles this correctly.

- Always call `ctx.registerShutdownHook()` in standalone non-Boot Spring apps. Spring Boot does this automatically via `SpringApplication`.
- `@PreDestroy` runs synchronously on the shutdown thread. Long-running cleanup in `@PreDestroy` delays JVM exit — keep it under the `terminationGracePeriodSeconds` budget.
- Kubernetes sends `SIGTERM` to the JVM, which triggers the shutdown hook. The default grace period is 30 seconds. Spring Boot 2.3+ adds a configurable graceful shutdown period (`spring.lifecycle.timeout-per-shutdown-phase`) for stopping the web server before destroying beans.
- `DisposableBean.destroy()` runs after `@PreDestroy`. Both are supported; `@PreDestroy` is preferred for application code.
- A bean can implement `SmartLifecycle` instead of `@PreDestroy` for ordered, phase-based shutdown — useful for message consumers that need to stop before the connection factory closes.
