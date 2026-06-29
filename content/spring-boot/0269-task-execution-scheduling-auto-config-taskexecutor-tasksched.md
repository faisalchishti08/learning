---
card: spring-boot
gi: 269
slug: task-execution-scheduling-auto-config-taskexecutor-tasksched
title: Task execution & scheduling auto-config (TaskExecutor/TaskScheduler)
---

## 1. What it is

Spring Boot auto-configures two key concurrency abstractions when their starters or annotations are present:

- **`TaskExecutor`** (`ThreadPoolTaskExecutor`) — a thread pool for `@Async` methods and programmatic task submission. Activated by `@EnableAsync` or when Spring detects async capability is needed.
- **`TaskScheduler`** (`ThreadPoolTaskScheduler`) — a scheduled thread pool for `@Scheduled` methods. Activated by `@EnableScheduling`.

Both are configurable via `spring.task.execution.*` and `spring.task.scheduling.*` properties respectively. Without any configuration they use sensible defaults (8-core pool, bounded queue, etc.).

## 2. Why & when

**`@Async`** is used when a controller or service must trigger work without blocking the HTTP thread:
- Sending a welcome email after user registration.
- Processing an uploaded file in the background.
- Fanning out to multiple services in parallel.

**`@Scheduled`** is used for periodic or cron-driven tasks:
- Polling an external API every 30 seconds.
- Running a nightly report at 2 AM.
- Expiring stale database records every hour.

Auto-configuration removes the boilerplate of configuring thread pools manually. You add `@EnableAsync` / `@EnableScheduling` to a configuration class (or `@SpringBootApplication`) and Spring Boot provides production-ready pools with correct rejections handlers and shutdown behaviour.

## 3. Core concept

Auto-configuration creates the following beans when absent:

| Annotation | Bean created | Type | Properties prefix |
|---|---|---|---|
| `@EnableAsync` | `applicationTaskExecutor` | `ThreadPoolTaskExecutor` | `spring.task.execution` |
| `@EnableScheduling` | `taskScheduler` | `ThreadPoolTaskScheduler` | `spring.task.scheduling` |

Key `spring.task.execution.*` properties:

```properties
spring.task.execution.pool.core-size=8
spring.task.execution.pool.max-size=16
spring.task.execution.pool.queue-capacity=100
spring.task.execution.pool.keep-alive=60s
spring.task.execution.thread-name-prefix=task-
spring.task.execution.shutdown.await-termination=true
spring.task.execution.shutdown.await-termination-period=30s
```

Key `spring.task.scheduling.*` properties:

```properties
spring.task.scheduling.pool.size=1       # single-threaded by default
spring.task.scheduling.thread-name-prefix=scheduling-
spring.task.scheduling.shutdown.await-termination=true
spring.task.scheduling.shutdown.await-termination-period=30s
```

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TaskExecutor and TaskScheduler auto-configuration wiring to @Async and @Scheduled methods">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- @Async path -->
  <rect x="10" y="30" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="80" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@EnableAsync</text>

  <rect x="200" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ThreadPoolTaskExecutor</text>
  <text x="290" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">spring.task.execution.*</text>

  <rect x="440" y="20" width="120" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">@Async</text>
  <text x="500" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">methods run</text>

  <!-- @Scheduled path -->
  <rect x="10" y="150" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="80" y="175" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@EnableScheduling</text>

  <rect x="200" y="140" width="180" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="165" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ThreadPoolTaskScheduler</text>
  <text x="290" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">spring.task.scheduling.*</text>

  <rect x="440" y="140" width="120" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="165" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">@Scheduled</text>
  <text x="500" y="183" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">cron / fixed rate</text>

  <line x1="150" y1="50" x2="198" y2="50" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="380" y1="50" x2="438" y2="50" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="150" y1="170" x2="198" y2="170" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="380" y1="170" x2="438" y2="170" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="225" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Both auto-configured with shutdown coordination — in-flight tasks drain before JVM exit</text>
</svg>

`@EnableAsync` and `@EnableScheduling` trigger auto-configuration of matching thread pools with graceful shutdown support.

## 5. Runnable example

```java
// TaskAutoConfigDemo.java — run with: java TaskAutoConfigDemo.java
// Simulates @Async and @Scheduled execution using the same
// thread pool configuration Spring Boot auto-provides.

import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class TaskAutoConfigDemo {

    // Simulated ThreadPoolTaskExecutor (Spring Boot creates this for @Async)
    static final ThreadPoolExecutor TASK_EXECUTOR = new ThreadPoolExecutor(
        4,   // corePoolSize  — spring.task.execution.pool.core-size=4
        8,   // maxPoolSize   — spring.task.execution.pool.max-size=8
        60L, TimeUnit.SECONDS,
        new LinkedBlockingQueue<>(50), // queueCapacity — spring.task.execution.pool.queue-capacity=50
        r -> {
            Thread t = new Thread(r, "task-" + TASK_COUNTER.incrementAndGet());
            t.setDaemon(true);
            return t;
        }
    );

    // Simulated ScheduledThreadPoolExecutor (Spring Boot creates for @Scheduled)
    static final ScheduledExecutorService SCHEDULER = Executors.newScheduledThreadPool(
        1, // pool.size=1 (default) — spring.task.scheduling.pool.size=1
        r -> {
            Thread t = new Thread(r, "scheduling-" + SCHED_COUNTER.incrementAndGet());
            t.setDaemon(true);
            return t;
        }
    );

    static final AtomicInteger TASK_COUNTER = new AtomicInteger();
    static final AtomicInteger SCHED_COUNTER = new AtomicInteger();

    public static void main(String[] args) throws Exception {
        System.out.println("=== Task Execution & Scheduling Auto-config Demo ===\n");
        printConfig();
        runAsyncExample();
        runSchedulingExample();
        shutdown();
    }

    static void printConfig() {
        System.out.println("--- application.properties ---");
        System.out.println("""
            # @Async thread pool:
            spring.task.execution.pool.core-size=4
            spring.task.execution.pool.max-size=16
            spring.task.execution.pool.queue-capacity=100
            spring.task.execution.shutdown.await-termination=true
            spring.task.execution.shutdown.await-termination-period=30s
            spring.task.execution.thread-name-prefix=task-

            # @Scheduled thread pool:
            spring.task.scheduling.pool.size=2
            spring.task.scheduling.shutdown.await-termination=true
            spring.task.scheduling.shutdown.await-termination-period=30s
            spring.task.scheduling.thread-name-prefix=scheduling-
            """);
    }

    // Simulates calling an @Async service method
    static void runAsyncExample() throws Exception {
        System.out.println("--- @Async example ---");
        System.out.println("  // In a Spring app:");
        System.out.println("  // @Async public CompletableFuture<String> processOrder(int id) { ... }");
        System.out.println("  // Called from controller — returns immediately, runs on task-* thread");
        System.out.println();

        var futures = new CompletableFuture[5];
        for (int i = 1; i <= 5; i++) {
            final int orderId = i;
            futures[i-1] = CompletableFuture.supplyAsync(() -> {
                try { Thread.sleep(100); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                return "Order " + orderId + " processed by " + Thread.currentThread().getName();
            }, TASK_EXECUTOR);
        }

        for (var f : futures) System.out.println("  " + f.get());
        System.out.println();
    }

    // Simulates @Scheduled(fixedRate=1000) and @Scheduled(cron="0 0 2 * * ?")
    static void runSchedulingExample() throws Exception {
        System.out.println("--- @Scheduled example ---");
        System.out.println("  // @Scheduled(fixedDelay=5000) → runs every 5s after previous run completes");
        System.out.println("  // @Scheduled(fixedRate=5000)  → runs every 5s from start of previous run");
        System.out.println("  // @Scheduled(cron=\"0 0 2 * * ?\") → runs daily at 2 AM");
        System.out.println();

        var counter = new AtomicInteger(0);
        SCHEDULER.scheduleAtFixedRate(
            () -> System.out.println("  [" + Thread.currentThread().getName() + "] Scheduled tick #" + counter.incrementAndGet()),
            0, 300, TimeUnit.MILLISECONDS
        );

        Thread.sleep(1000); // let 3 ticks fire
    }

    static void shutdown() throws InterruptedException {
        System.out.println("\n--- Graceful shutdown (await-termination=true, period=30s) ---");
        SCHEDULER.shutdown();
        TASK_EXECUTOR.shutdown();
        SCHEDULER.awaitTermination(5, TimeUnit.SECONDS);
        TASK_EXECUTOR.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("  All tasks drained. JVM can exit.");
    }
}
```

**How to run:** `java TaskAutoConfigDemo.java`

## 6. Walkthrough

- **`corePoolSize=4`** — the number of threads always kept alive. If fewer than 4 tasks are running, the extra threads wait. Spring Boot's default is `8` (matching typical server CPU count).
- **`maxPoolSize=8`** — threads beyond `corePoolSize` are created when the queue is full. The pool shrinks back to `corePoolSize` after `keepAlive` seconds of idleness.
- **`queue-capacity=50`** — tasks wait here when all threads are busy. If the queue fills up and max pool is exhausted, the rejection handler fires. Spring Boot's default rejection policy logs a warning and runs the task on the caller's thread (preventing data loss).
- **`await-termination=true` + period** — when the JVM receives `SIGTERM`, Spring waits for the thread pool to drain in-flight tasks for up to `await-termination-period` before force-stopping. Critical for `@Async` methods that write to databases.
- **Scheduler single thread** — `spring.task.scheduling.pool.size=1` (default) means `@Scheduled` tasks run one at a time. If two scheduled tasks overlap (one is still running when the next fires), the second waits. Increase `pool.size` for independent concurrent schedules.

## 7. Gotchas & takeaways

> **`@Async` requires `@EnableAsync` on a configuration class.** Putting it on `@SpringBootApplication` works. Without it, `@Async` methods run synchronously on the caller's thread — no exception, just no async behaviour.

> **The auto-configured `TaskExecutor` is a single shared pool for all `@Async` methods.** If one service submits many long tasks, it can starve other services' async methods. For isolation, define a named `@Bean("myExecutor") ThreadPoolTaskExecutor` and reference it: `@Async("myExecutor")`.

- `@Scheduled(cron="...")` uses Spring's cron expression (6 fields: second minute hour day month weekday). Standard Unix cron has 5 fields — add a leading `0` for the seconds field.
- `@Scheduled(fixedDelay=5000)` counts delay from the *end* of the last execution; `fixedRate=5000` counts from the *start*. Choose based on whether overlapping runs would be a problem.
- `CompletableFuture<T>` is the recommended return type for `@Async` methods — supports composition and lets the caller join if needed.
- Profile the pool with Actuator: `/actuator/metrics/executor.pool.size` shows live pool size.
