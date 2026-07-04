---
card: spring-framework
gi: 198
slug: scheduled-enablescheduling
title: "@Scheduled & @EnableScheduling"
---

## 1. What it is

`@EnableScheduling` activates Spring's background task scheduler, and `@Scheduled` marks a method that should run automatically on a fixed schedule — no external job framework needed. Together they give you a cron-like engine built right into your Spring application context.

You put `@EnableScheduling` once on a `@Configuration` class, then annotate any Spring-managed bean method with `@Scheduled(fixedRate=…)`, `@Scheduled(fixedDelay=…)`, or `@Scheduled(cron="…")`. Spring registers the method with its internal `ThreadPoolTaskScheduler` and fires it at the specified interval.

## 2. Why & when

Scheduled tasks are everywhere: sending nightly email digests, purging expired sessions, polling an external API for updates, flushing metrics to a monitoring system. The alternatives are:

- **Quartz Scheduler** — powerful but complex, needs a database for clustering.
- **OS cron** — fragile, separate deployment, not aware of your app state.
- **Spring's @Scheduled** — zero extra dependencies, runs inside the application process, shares beans/transactions/datasources naturally.

Use `@Scheduled` when the scheduling logic is simple to moderate and you want it integrated with Spring's lifecycle. Add Quartz only when you need distributed, persistent, fault-tolerant job storage.

## 3. Core concept

Think of `@EnableScheduling` as hiring a timekeeper and `@Scheduled` as giving that timekeeper a list of alarms. The timekeeper runs a background thread and fires each alarm at the right moment.

Three trigger modes:
- **`fixedRate`** — run every N ms, measured from *start* of previous run (overlaps if the task takes longer than the rate).
- **`fixedDelay`** — run N ms *after the previous run finishes* (gap is always N, no overlap).
- **`cron`** — calendar-based expression (see the next topic). Best for "every day at 2 AM" logic.

All three accept an `initialDelay` to hold off the first execution after startup.

The annotated method must return `void` and take no arguments (or optionally a `ScheduledTaskRegistrar` if you register programmatically).

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg">
  <!-- Scheduler thread -->
  <rect x="20" y="80" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="106" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">ThreadPool</text>
  <text x="100" y="125" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">TaskScheduler</text>

  <!-- Arrow to method -->
  <line x1="180" y1="110" x2="280" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="230" y="102" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">fires trigger</text>

  <!-- @Scheduled method -->
  <rect x="280" y="80" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="370" y="106" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">@Scheduled method</text>
  <text x="370" y="125" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">runs in scheduler thread</text>

  <!-- Arrow to side effect -->
  <line x1="460" y1="110" x2="560" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="510" y="102" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">side effect</text>

  <!-- Side effect box -->
  <rect x="560" y="80" width="70" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="595" y="106" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">DB/API</text>
  <text x="595" y="123" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">email…</text>

  <!-- Rate label -->
  <text x="100" y="165" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">fixedRate / fixedDelay / cron</text>

  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>
</svg>

The scheduler thread pool fires the method; the method performs its work (DB write, HTTP call, etc.) and returns — the scheduler records the next fire time.

## 5. Runnable example

One scenario: a **counter service** that periodically logs its heartbeat, then accumulates work, then handles slow-execution overlap.

### Level 1 — Basic

The simplest scheduled task: print a message every 2 seconds.

```java
// SchedulingDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;

@Configuration
@EnableScheduling
@ComponentScan
public class SchedulingDemo {
    public static void main(String[] args) throws InterruptedException {
        var ctx = new AnnotationConfigApplicationContext(SchedulingDemo.class);
        Thread.sleep(7000);
        ctx.close();
    }
}

@org.springframework.stereotype.Component
class HeartbeatTask {
    private int count = 0;

    @Scheduled(fixedRate = 2000)
    public void beat() {
        System.out.printf("Heartbeat #%d at %s%n",
            ++count, java.time.LocalTime.now());
    }
}
```

How to run: `java -cp spring-context.jar:. SchedulingDemo.java` (use a Spring Boot fat-jar in practice)

`@EnableScheduling` wires up the scheduler; `@Scheduled(fixedRate=2000)` fires `beat()` every 2 000 ms. Three beats fire before `Thread.sleep(7000)` ends and the context closes.

---

### Level 2 — Intermediate

Real-world concern: the task does actual work (accumulates pending items from a queue) and we need `fixedDelay` so a slow batch doesn't stack up concurrent runs.

```java
// SchedulingDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

@Configuration
@EnableScheduling
@ComponentScan
public class SchedulingDemo {
    public static void main(String[] args) throws InterruptedException {
        var ctx = new AnnotationConfigApplicationContext(SchedulingDemo.class);
        // Simulate items arriving
        var queue = ctx.getBean(WorkQueue.class);
        for (int i = 1; i <= 6; i++) { queue.add("item-" + i); Thread.sleep(800); }
        Thread.sleep(3000);
        ctx.close();
    }
}

@org.springframework.stereotype.Component
class WorkQueue {
    final BlockingQueue<String> q = new LinkedBlockingQueue<>();
    void add(String item) { q.offer(item); System.out.println("Queued: " + item); }

    @Scheduled(fixedDelay = 2000, initialDelay = 1000)
    public void flush() throws InterruptedException {
        var batch = new java.util.ArrayList<String>();
        q.drainTo(batch);
        if (!batch.isEmpty()) {
            System.out.println("Flushing batch: " + batch);
            Thread.sleep(500); // simulate DB write
        }
    }
}
```

How to run: same as Level 1

`fixedDelay = 2000` waits 2 s *after flush() finishes* before scheduling the next run, so a slow flush never overlaps itself. `initialDelay = 1000` gives the context 1 s to warm up before the first execution.

---

### Level 3 — Advanced

Production concern: configure a named scheduler bean with a custom thread pool so scheduled tasks don't starve each other, and demonstrate `@Scheduled` picking it up via `SchedulingConfigurer`.

```java
// SchedulingDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.scheduling.config.*;
import org.springframework.scheduling.concurrent.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

@Configuration
@EnableScheduling
@ComponentScan
public class SchedulingDemo implements SchedulingConfigurer {

    @Override
    public void configureTasks(ScheduledTaskRegistrar registrar) {
        var pool = new ThreadPoolTaskScheduler();
        pool.setPoolSize(3);
        pool.setThreadNamePrefix("sched-");
        pool.initialize();
        registrar.setTaskScheduler(pool);
    }

    public static void main(String[] args) throws InterruptedException {
        var ctx = new AnnotationConfigApplicationContext(SchedulingDemo.class);
        Thread.sleep(9000);
        ctx.close();
    }
}

@org.springframework.stereotype.Component
class MetricsTask {
    private final AtomicLong counter = new AtomicLong();

    @Scheduled(fixedRate = 1500)
    public void exportMetrics() {
        long val = counter.incrementAndGet();
        System.out.printf("[%s] metrics export #%d%n",
            Thread.currentThread().getName(), val);
    }

    @Scheduled(fixedRate = 3000)
    public void auditLog() {
        System.out.printf("[%s] audit snapshot at counter=%d%n",
            Thread.currentThread().getName(), counter.get());
    }
}
```

How to run: `java -cp spring-context.jar:spring-beans.jar:. SchedulingDemo.java`

`SchedulingConfigurer.configureTasks` injects a `ThreadPoolTaskScheduler` with 3 threads so `exportMetrics` (every 1.5 s) and `auditLog` (every 3 s) run concurrently. Thread names (`sched-1`, `sched-2`) confirm separate threads. Without a custom pool, Spring uses a single-threaded default, which serialises all tasks.

## 6. Walkthrough

**Startup:** `AnnotationConfigApplicationContext` scans for `@Component` beans. When it processes `@EnableScheduling` on the configuration class, it registers a `ScheduledAnnotationBeanPostProcessor` in the context.

**Bean post-processing:** After each bean is created, `ScheduledAnnotationBeanPostProcessor.postProcessAfterInitialization` inspects every method. It finds `@Scheduled` on `MetricsTask.exportMetrics` and `MetricsTask.auditLog`.

**Task registration:** Each `@Scheduled` method is wrapped in a `ScheduledMethodRunnable` and registered with the `TaskScheduler`. For `fixedRate=1500`, Spring computes `nextFireTime = now + 1500` and creates a recurring `ScheduledFuture`.

**Execution:** At `t=1500 ms`, the scheduler thread pool picks `exportMetrics`, wraps it in a try/catch, calls `MetricsTask.exportMetrics()`, records the actual start time, and schedules the *next* fire at `actualStart + 1500`. For `fixedDelay`, the next fire would be `actualEnd + delay`.

**Thread safety:** Both tasks share the `AtomicLong counter`. `fixedRate` can fire before the previous run finishes *if the pool has spare threads*, so state must be thread-safe — hence `AtomicLong` rather than `int`.

**Shutdown:** `ctx.close()` calls `destroy()` on `ThreadPoolTaskScheduler`, cancels all `ScheduledFuture`s, and awaits thread termination (configurable timeout).

**Expected console output (excerpt):**
```
[sched-1] metrics export #1
[sched-2] audit snapshot at counter=1
[sched-1] metrics export #2
[sched-1] metrics export #3
[sched-2] audit snapshot at counter=3
```

## 7. Gotchas & takeaways

> **Default scheduler has ONE thread.** Without a custom `TaskScheduler`, all `@Scheduled` methods share a single-threaded executor. One slow task blocks every other task. Always configure a pool for production.

> **`fixedRate` can stack.** If a `fixedRate` task takes longer than its rate *and* the pool has spare threads, two instances run concurrently against shared state. Use `fixedDelay` or `@Async` + locking for tasks that must not overlap.

- `@EnableScheduling` goes on one `@Configuration` class only — duplicating it across modules is harmless but wastes resources.
- Scheduled methods must be `void` and have no parameters; Spring silently ignores a return value.
- `initialDelay` is measured from context startup, not from the first trigger — useful for health-check warmup windows.
- In Spring Boot, `@EnableScheduling` is available but you still need to add it explicitly; it is *not* auto-configured.
- To disable scheduling in tests, exclude `SchedulingConfiguration` or set `spring.task.scheduling.pool.size=0`.
