---
card: spring-framework
gi: 458
slug: the-task-schema
title: "The task schema"
---

## 1. What it is

The `task` namespace (`xmlns:task="http://www.springframework.org/schema/task"`) is the XML equivalent of `@EnableScheduling`/`@Scheduled`/`@EnableAsync`/`@Async`: `<task:scheduled-tasks>` declares fixed-rate, fixed-delay, or cron-triggered method invocations, `<task:executor>` and `<task:scheduler>` configure the thread pools that run them, and `<task:annotation-driven>` activates `@Scheduled`/`@Async` annotation processing from XML.

```xml
<task:scheduled-tasks scheduler="myScheduler">
    <task:scheduled ref="reportJob" method="generate" cron="0 0 * * * *"/>
</task:scheduled-tasks>
<task:scheduler id="myScheduler" pool-size="5"/>
```

## 2. Why & when

Running code on a schedule — "every hour, on the hour" or "every 30 seconds after the previous run finishes" — needs a `TaskScheduler`, a thread pool, and trigger logic (cron parsing, fixed-rate/fixed-delay bookkeeping) behind the scenes. The `task` schema exists to configure all of that declaratively in XML, the same way `@Scheduled` does with annotations, so the actual scheduled method can be a plain, framework-agnostic Java method.

Reach for the `task` schema specifically when:

- You're maintaining legacy XML-configured Spring applications where scheduled jobs and thread-pool sizing are already declared this way, and need to add, modify, or trace a cron expression or executor configuration.
- You want scheduler and executor thread-pool sizing (`pool-size`, `queue-capacity`) expressed as XML attributes alongside the rest of an XML-first application's infrastructure configuration.
- You need `<task:annotation-driven>` specifically to activate `@Scheduled`/`@Async` processing in an application whose root configuration is XML rather than a `@Configuration` class (where `@EnableScheduling`/`@EnableAsync` would be used instead).

In new code, `@EnableScheduling` plus `@Scheduled` (or `@EnableAsync` plus `@Async`) on a `@Configuration` class is almost always simpler — the `task` schema mainly exists to support and explain XML configuration that predates those annotations.

## 3. Core concept

```
 <task:scheduler id="myScheduler" pool-size="5"/>
        |
        v
 registers a ThreadPoolTaskScheduler bean with a 5-thread pool

 <task:scheduled-tasks scheduler="myScheduler">
     <task:scheduled ref="reportJob" method="generate" cron="0 0 * * * *"/>
     <task:scheduled ref="cleanupJob" method="run" fixed-delay="30000"/>
 </task:scheduled-tasks>
        |
        v
 for EACH <task:scheduled>, registers a Trigger (CronTrigger or
 PeriodicTrigger) and schedules ref.method(...) against it on myScheduler

 <task:executor id="myExecutor" pool-size="4-10" queue-capacity="100"/>
        |
        v
 registers a ThreadPoolTaskExecutor for @Async method calls (separate concern
 from scheduling -- executors run async work, schedulers trigger timed work)
```

`task:scheduler` and `task:executor` are distinct: a scheduler decides *when* something runs, an executor decides *how many threads* run submitted work concurrently — `@Async` methods use an executor, `@Scheduled` methods use a scheduler (which is itself backed by a thread pool).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="task:scheduled-tasks wires a cron trigger against a plain method, run by a configured scheduler thread pool">
  <rect x="10" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;task:scheduled&gt;</text>
  <text x="95" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">cron="0 0 * * * *"</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CronTrigger + Scheduler</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">pool-size threads</text>

  <rect x="480" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">reportJob.generate()</text>
  <text x="555" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">plain method</text>

  <line x1="180" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="45" x2="475" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The trigger and scheduler live entirely in XML wiring; the scheduled method itself stays plain Java.

## 5. Runnable example

The scenario: a report-generation job that must run periodically. It starts with a basic fixed-rate schedule, adds a cron-based schedule for a second job with a dedicated thread pool, then adds `<task:executor>`-backed asynchronous dispatch so a slow job doesn't block the scheduler thread.

### Level 1 — Basic

Wire a single `<task:scheduled>` with `fixed-rate` against a plain method and observe it fire multiple times.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;

public class TaskSchemaLevel1 {

    public static class ReportJob {
        final AtomicInteger runs = new AtomicInteger();
        public void generate() {
            int n = runs.incrementAndGet();
            System.out.println("[reportJob] run #" + n + " at " + System.currentTimeMillis());
        }
    }

    public static void main(String[] args) throws InterruptedException {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:task="http://www.springframework.org/schema/task"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/task
                       https://www.springframework.org/schema/task/spring-task.xsd">

                <bean id="reportJob" class="TaskSchemaLevel1$ReportJob"/>

                <task:scheduler id="myScheduler" pool-size="2"/>

                <task:scheduled-tasks scheduler="myScheduler">
                    <task:scheduled ref="reportJob" method="generate" fixed-rate="300"/>
                </task:scheduled-tasks>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        ReportJob job = ctx.getBean(ReportJob.class);
        Thread.sleep(1100); // long enough for several 300ms ticks

        int runs = job.runs.get();
        System.out.println("total runs observed = " + runs);
        if (runs < 3) throw new AssertionError("Expected at least 3 runs in ~1.1s at fixed-rate=300ms, got " + runs);
        System.out.println("task:scheduled fixed-rate fired repeatedly -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-context` on the classpath, then `java TaskSchemaLevel1.java` on JDK 17+.

`<task:scheduler pool-size="2">` registers a `ThreadPoolTaskScheduler` with two threads. `<task:scheduled ref="reportJob" method="generate" fixed-rate="300"/>` schedules `reportJob.generate()` to run every 300 milliseconds, measured from the start of each execution to the start of the next — this is why sleeping ~1.1 seconds reliably observes at least 3 runs.

### Level 2 — Intermediate

Add a second job on a `cron` trigger, sharing the same scheduler, showing `fixed-rate` and `cron` triggers coexisting under one `<task:scheduled-tasks>` block.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;

public class TaskSchemaLevel2 {

    public static class ReportJob {
        final AtomicInteger runs = new AtomicInteger();
        public void generate() { runs.incrementAndGet(); }
    }

    public static class HeartbeatJob {
        final AtomicInteger runs = new AtomicInteger();
        public void beat() { runs.incrementAndGet(); }
    }

    public static void main(String[] args) throws InterruptedException {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:task="http://www.springframework.org/schema/task"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/task
                       https://www.springframework.org/schema/task/spring-task.xsd">

                <bean id="reportJob" class="TaskSchemaLevel2$ReportJob"/>
                <bean id="heartbeatJob" class="TaskSchemaLevel2$HeartbeatJob"/>

                <task:scheduler id="myScheduler" pool-size="3"/>

                <task:scheduled-tasks scheduler="myScheduler">
                    <task:scheduled ref="reportJob" method="generate" fixed-rate="300"/>
                    <task:scheduled ref="heartbeatJob" method="beat" cron="*/1 * * * * *"/>
                </task:scheduled-tasks>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        Thread.sleep(2200); // long enough for several 300ms ticks and ~2 cron ticks

        ReportJob reportJob = ctx.getBean(ReportJob.class);
        HeartbeatJob heartbeatJob = ctx.getBean(HeartbeatJob.class);
        System.out.println("reportJob runs = " + reportJob.runs.get() + ", heartbeatJob runs = " + heartbeatJob.runs.get());

        if (reportJob.runs.get() < 5) throw new AssertionError("Expected several fixed-rate runs");
        if (heartbeatJob.runs.get() < 1) throw new AssertionError("Expected at least one cron run");
        System.out.println("fixed-rate and cron triggers ran independently on the shared scheduler -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java TaskSchemaLevel2.java`.

`cron="*/1 * * * * *"` (Spring's cron format includes a leading seconds field) fires `heartbeatJob.beat()` once per second, independently of `reportJob`'s 300ms fixed-rate schedule — both triggers run on the same `myScheduler` thread pool but are tracked and fired independently, each by its own `Trigger` implementation (`PeriodicTrigger` for `fixed-rate`, `CronTrigger` for `cron`).

### Level 3 — Advanced

Add `<task:executor>` and dispatch a slow report generation asynchronously from within the scheduled method, so a long-running report doesn't monopolize a scheduler thread — the production-flavored pattern of "scheduler decides *when*, executor handles the *actual work* off to the side."

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.task.TaskExecutor;

import java.nio.charset.StandardCharsets;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public class TaskSchemaLevel3 {

    public static class ReportJob {
        private final TaskExecutor executor;
        final AtomicInteger triggered = new AtomicInteger();
        final AtomicInteger completed = new AtomicInteger();
        final CountDownLatch firstCompletion = new CountDownLatch(1);

        public ReportJob(TaskExecutor executor) { this.executor = executor; }

        // Called by the scheduler -- must return quickly, so the slow work is dispatched.
        public void generate() {
            triggered.incrementAndGet();
            executor.execute(() -> {
                try {
                    Thread.sleep(150); // simulate a slow report
                } catch (InterruptedException ignored) {
                    Thread.currentThread().interrupt();
                }
                completed.incrementAndGet();
                firstCompletion.countDown();
                System.out.println("[" + Thread.currentThread().getName() + "] report completed");
            });
        }
    }

    public static void main(String[] args) throws InterruptedException {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:task="http://www.springframework.org/schema/task"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/task
                       https://www.springframework.org/schema/task/spring-task.xsd">

                <task:executor id="reportExecutor" pool-size="2-4" queue-capacity="50"/>
                <task:scheduler id="myScheduler" pool-size="1"/>

                <bean id="reportJob" class="TaskSchemaLevel3$ReportJob">
                    <constructor-arg ref="reportExecutor"/>
                </bean>

                <task:scheduled-tasks scheduler="myScheduler">
                    <task:scheduled ref="reportJob" method="generate" fixed-rate="100"/>
                </task:scheduled-tasks>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        ReportJob job = ctx.getBean(ReportJob.class);
        boolean gotFirst = job.firstCompletion.await(3, TimeUnit.SECONDS);
        Thread.sleep(300); // let a few more triggers/completions accumulate

        System.out.println("triggered = " + job.triggered.get() + ", completed = " + job.completed.get());
        if (!gotFirst) throw new AssertionError("Expected at least one report to complete");
        if (job.triggered.get() <= job.completed.get() && job.triggered.get() < 3)
            throw new AssertionError("Expected the fast scheduler to trigger faster than the slow work completes");

        System.out.println("scheduler stayed responsive while executor ran the slow work -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java TaskSchemaLevel3.java`.

`<task:executor id="reportExecutor" pool-size="2-4" queue-capacity="50"/>` registers a `ThreadPoolTaskExecutor` separate from the scheduler's own thread pool. `generate()` (called by the scheduler, on the scheduler's single thread since `pool-size="1"`) does almost no work itself — it hands the actual 150ms simulated report off to `executor.execute(...)`, returning immediately. Because the scheduler thread isn't blocked for 150ms per tick, it can keep firing every 100ms as configured, which is why `triggered` climbs faster than `completed` — proving the separation of "when to run" (scheduler) from "who does the work" (executor) actually holds under a slow task.

## 6. Walkthrough

Trace Level 3's first few ticks.

1. **Context refresh**: `<task:executor>` registers `reportExecutor` (a `ThreadPoolTaskExecutor`, 2–4 threads, queue capacity 50). `<task:scheduler>` registers `myScheduler` (a `ThreadPoolTaskScheduler`, 1 thread). `<task:scheduled-tasks>` schedules `reportJob.generate` to run every 100ms on `myScheduler`.
2. **First tick (t≈0ms)**: `myScheduler`'s single thread calls `job.generate()`. Inside, `triggered` becomes 1, and `executor.execute(...)` submits the slow-report lambda to `reportExecutor`'s pool, then `generate()` returns immediately — the scheduler thread is free again almost instantly.
3. **`reportExecutor` picks up the submitted task** on one of its own pool threads (not the scheduler thread) and starts the simulated 150ms report.
4. **Second tick (t≈100ms)**: `myScheduler` calls `generate()` again since only ~100ms elapsed and the scheduler thread was never blocked. `triggered` becomes 2; a second report task is submitted to `reportExecutor`, which — since it has 2–4 threads — can run it concurrently with the first if the first hasn't finished.
5. **First report completes (t≈150ms)**: the first submitted lambda finishes sleeping, increments `completed` to 1, counts down `firstCompletion`, and logs which pool thread ran it.
6. **`main` observes**: `firstCompletion.await(3, SECONDS)` unblocks once step 5 happens; the program then sleeps a bit longer to let a few more ticks and completions accumulate.
7. **Final check**: the program prints `triggered` and `completed` counts and asserts the scheduler was able to trigger new runs faster than the slow work completed — direct evidence the 100ms scheduler cadence wasn't throttled by the 150ms task duration.

```
 myScheduler (1 thread) ticks every 100ms:
   t=0    -> generate() -> submit report#1 to reportExecutor -> returns immediately
   t=100  -> generate() -> submit report#2 to reportExecutor -> returns immediately
   t=150  -------------------------------------------- report#1 completes (on executor thread)
   t=200  -> generate() -> submit report#3 -> returns immediately
   t=250  -------------------------------------------- (about here) report#2 completes
```

## 7. Gotchas & takeaways

> **Gotcha:** if a `<task:scheduled>` method does its own slow work directly (no executor hand-off, as in Level 1 and 2), a single-threaded `task:scheduler` (`pool-size="1"`) will silently skip or delay subsequent ticks while the current one is still running for `fixed-rate`/`fixed-delay` triggers — the fix is exactly the Level 3 pattern: keep the scheduled method fast, and dispatch real work to a separate executor.

- `task:scheduler` and `task:executor` solve different problems — a scheduler decides *when* work runs (via triggers), an executor decides *how work runs concurrently* (via a thread pool) — and they're commonly used together, as in Level 3, rather than as substitutes for each other.
- `fixed-rate` measures from start-to-start of consecutive runs; `fixed-delay` (not shown here but available identically) measures from end-to-start — picking the wrong one is a common source of "why did this run twice as often as I expected" bugs.
- `cron` in the `task` schema uses Spring's own six-field cron format (seconds first), not the traditional five-field Unix cron format — a frequent source of off-by-one-field confusion when porting cron expressions from other systems.
- `<task:annotation-driven>` (not shown in the runnable examples here) is the XML equivalent of `@EnableScheduling`/`@EnableAsync` — reach for it specifically when you want `@Scheduled`/`@Async` annotations to work in an XML-rooted application context.
