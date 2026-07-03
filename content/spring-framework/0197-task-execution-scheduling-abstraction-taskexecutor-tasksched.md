---
card: spring-framework
gi: 197
slug: task-execution-scheduling-abstraction-taskexecutor-tasksched
title: "Task execution & scheduling abstraction (TaskExecutor/TaskScheduler)"
---

## 1. What it is

Spring provides `TaskExecutor` and `TaskScheduler` as portable abstractions over Java's executor and scheduling infrastructure. `TaskExecutor` wraps `java.util.concurrent.Executor`; `TaskScheduler` adds fixed-rate, fixed-delay, and cron-based scheduling.

```java
// TaskExecutor — fire-and-forget task submission
@Autowired TaskExecutor taskExecutor;

taskExecutor.execute(() -> System.out.println("Running on pool thread"));

// TaskScheduler — scheduled future or recurring tasks
@Autowired TaskScheduler scheduler;

scheduler.scheduleWithFixedDelay(
    () -> System.out.println("Heartbeat"),
    Duration.ofSeconds(5));

// @Scheduled annotation — declarative alternative (no injection required)
@Scheduled(fixedDelay = 5000)
public void heartbeat() { System.out.println("Heartbeat"); }
```

`@EnableScheduling` activates annotation-based scheduling; `@EnableAsync` activates `@Async`. Both build on Spring's `TaskExecutor` / `TaskScheduler` infrastructure.

## 2. Why & when

- **`TaskExecutor`** — run tasks on a thread pool without coupling to `ThreadPoolExecutor` directly; enables swapping implementations (sync in tests, async in prod).
- **`@Async`** — decouple method callers from long-running work; the method executes on a `TaskExecutor` thread pool.
- **`TaskScheduler` / `@Scheduled`** — periodic jobs: polling, cache refresh, cleanup, reporting.
- **Cron expression** — complex schedules (`@Scheduled(cron = "0 0 2 * * *")` = every day at 2 AM).
- **Don't use** `TaskScheduler` for one-shot delayed execution when the caller needs the result — use `CompletableFuture` with `@Async` instead.

## 3. Core concept

**`TaskExecutor` hierarchy:**

| Implementation | Use |
|---|---|
| `SyncTaskExecutor` | Executes in the calling thread — useful for tests |
| `SimpleAsyncTaskExecutor` | New thread per task — no pooling; do not use in production |
| `ThreadPoolTaskExecutor` | Wraps `ThreadPoolExecutor`; configurable core/max/queue |
| `ConcurrentTaskExecutor` | Wraps any `java.util.concurrent.Executor` |

**`TaskScheduler` implementations:**

| Implementation | Use |
|---|---|
| `ThreadPoolTaskScheduler` | Primary production scheduler; configurable pool size |
| `ConcurrentTaskScheduler` | Wraps a `ScheduledExecutorService` |

**`@Scheduled` trigger types:**

| Attribute | Meaning |
|---|---|
| `fixedDelay` | N ms after the LAST invocation completes |
| `fixedRate` | Every N ms from the START of previous invocation |
| `cron` | Cron expression — second, minute, hour, day, month, weekday |
| `initialDelay` | Wait N ms before first execution |

**Cron format** (6 fields): `second minute hour day-of-month month day-of-week`. Special: `*`=any, `?`=any (day fields), `-`=range, `/`=step, `L`=last, `W`=nearest weekday.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="tea" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="teb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- TaskExecutor -->
  <rect x="5" y="10" width="200" height="120" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="105" y="28" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">TaskExecutor</text>
  <text x="105" y="44" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">execute(Runnable)</text>
  <text x="105" y="62" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">ThreadPoolTaskExecutor</text>
  <text x="105" y="75" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">corePoolSize / maxPoolSize</text>
  <text x="105" y="87" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">queueCapacity / keepAlive</text>
  <text x="105" y="104" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Async uses this</text>
  <text x="105" y="117" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">submit(Callable) → Future</text>

  <!-- TaskScheduler -->
  <rect x="250" y="10" width="220" height="160" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="360" y="28" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">TaskScheduler</text>
  <text x="360" y="44" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ThreadPoolTaskScheduler</text>
  <text x="360" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">schedule(task, trigger)</text>
  <text x="360" y="73" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">scheduleAtFixedRate(task, period)</text>
  <text x="360" y="86" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">scheduleWithFixedDelay(task, delay)</text>
  <text x="360" y="102" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Scheduled uses this</text>
  <rect x="265" y="110" width="190" height="50" rx="3" fill="#1c2430" stroke="#79c0ff" stroke-width="1" opacity="0.7"/>
  <text x="360" y="126" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">cron: "0 0 2 * * *" = 2 AM daily</text>
  <text x="360" y="139" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fixedRate: every N ms from start</text>
  <text x="360" y="152" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fixedDelay: N ms after completion</text>

  <!-- Thread pool -->
  <rect x="520" y="10" width="175" height="120" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="607" y="28" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Thread Pool</text>
  <text x="607" y="45" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Worker threads pick tasks</text>
  <rect x="530" y="55" width="155" height="15" rx="3" fill="#6db33f" opacity="0.4"/>
  <text x="607" y="66" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">thread-1 [running task A]</text>
  <rect x="530" y="75" width="155" height="15" rx="3" fill="#6db33f" opacity="0.4"/>
  <text x="607" y="86" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">thread-2 [running task B]</text>
  <rect x="530" y="95" width="155" height="15" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="607" y="106" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">thread-3 [idle]</text>
  <text x="607" y="123" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">shared by @Async + @Scheduled</text>

  <line x1="207" y1="65" x2="248" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#tea)"/>
  <line x1="472" y1="90" x2="518" y2="65" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#teb)"/>

  <text x="350" y="185" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Both abstractions run on thread pools; TaskScheduler adds time-based trigger dispatch</text>
</svg>

`TaskExecutor` dispatches tasks; `TaskScheduler` adds time-based triggers. Both run on configurable thread pools.

## 5. Runnable example

Scenario: **inventory monitoring system** — async order processing + scheduled low-stock check.

### Level 1 — Basic

`ThreadPoolTaskExecutor` manual submission; `@Async` on a service method.

```java
// TaskExecBasic.java
import org.springframework.context.annotation.*;
import org.springframework.core.task.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.scheduling.concurrent.*;
import org.springframework.stereotype.*;
import java.util.concurrent.Future;

@Configuration
@EnableAsync
@ComponentScan
class TeConfig {
    @Bean(name = "taskExecutor")
    ThreadPoolTaskExecutor taskExecutor() {
        var exec = new ThreadPoolTaskExecutor();
        exec.setCorePoolSize(4);
        exec.setMaxPoolSize(10);
        exec.setQueueCapacity(25);
        exec.setThreadNamePrefix("inventory-");
        exec.initialize();
        return exec;
    }
}

@Service
class InventoryProcessorSvc {
    // @Async submits this method to the "taskExecutor" thread pool
    @Async("taskExecutor")
    public Future<String> processOrder(String orderId) throws InterruptedException {
        System.out.println("[Process] " + orderId + " on " + Thread.currentThread().getName());
        Thread.sleep(100); // simulate work
        return org.springframework.scheduling.annotation.AsyncResult.forValue(
            "Processed:" + orderId);
    }
}

@Service
class DirectExecDemo {
    private final TaskExecutor exec;
    DirectExecDemo(TaskExecutor exec) { this.exec = exec; }

    public void submitBatch(int count) {
        for (int i = 0; i < count; i++) {
            final int n = i;
            exec.execute(() -> System.out.println("[Direct] task-" + n
                + " on " + Thread.currentThread().getName()));
        }
    }
}

public class TaskExecBasic {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(TeConfig.class);

        // @Async method
        var svc = ctx.getBean(InventoryProcessorSvc.class);
        var futures = new java.util.ArrayList<Future<String>>();
        for (var id : new String[]{"ORD-A", "ORD-B", "ORD-C"}) {
            futures.add(svc.processOrder(id));
        }
        for (var f : futures) System.out.println("[Result] " + f.get());

        // Direct TaskExecutor
        ctx.getBean(DirectExecDemo.class).submitBatch(3);
        Thread.sleep(200);
        ctx.close();
    }
}
```

How to run: `java TaskExecBasic.java`

`@Async("taskExecutor")` names the specific executor to use. Without the qualifier, Spring uses the bean named `taskExecutor` (convention) or falls back to `SimpleAsyncTaskExecutor`. `exec.execute(Runnable)` submits a task; `Future.get()` blocks until it completes.

### Level 2 — Intermediate

`ThreadPoolTaskScheduler`; `@Scheduled(fixedDelay/fixedRate/cron)`; `@EnableScheduling`.

```java
// TaskSchedIntermediate.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.scheduling.concurrent.*;
import org.springframework.stereotype.*;
import java.time.*;
import java.util.concurrent.atomic.*;

@Configuration
@EnableScheduling
@ComponentScan
class TsIntermConfig {
    @Bean
    ThreadPoolTaskScheduler taskScheduler() {
        var scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(3);
        scheduler.setThreadNamePrefix("sched-");
        scheduler.initialize();
        return scheduler;
    }
}

@Component
class InventoryScheduler {
    private final AtomicInteger checkCount = new AtomicInteger(0);

    // Runs every 500ms after previous COMPLETES (delay between end and start)
    @Scheduled(fixedDelay = 500)
    public void checkLowStock() {
        int count = checkCount.incrementAndGet();
        System.out.printf("[LowStock] Check #%d at %s thread=%s%n",
            count, LocalTime.now().withNano(0),
            Thread.currentThread().getName());
        if (count >= 3) throw new RuntimeException("Stop scheduling for demo");
    }

    // fixedRate: starts every 1000ms regardless of how long the task takes
    @Scheduled(fixedRate = 1000, initialDelay = 300)
    public void syncWarehouse() {
        System.out.println("[Sync] Warehouse sync at " + LocalTime.now().withNano(0));
    }
}

public class TaskSchedIntermediate {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(TsIntermConfig.class);
        Thread.sleep(2500);  // let scheduler run a few cycles
        ctx.close();
        System.out.println("Context closed — scheduler stopped.");
    }
}
```

How to run: `java TaskSchedIntermediate.java`

`fixedDelay=500`: waits 500 ms after the previous execution completes before starting the next. `fixedRate=1000`: starts a new execution every 1000 ms from the PREVIOUS start time — if the task takes 1200 ms, the next invocation starts immediately after (no gap). `initialDelay=300`: first execution delayed 300 ms after context startup.

### Level 3 — Advanced

Cron expression; `TaskScheduler` programmatic scheduling; `SchedulingConfigurer` for dynamic schedule; graceful shutdown.

```java
// TaskSchedAdvanced.java
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.annotation.*;
import org.springframework.scheduling.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.scheduling.concurrent.*;
import org.springframework.scheduling.config.*;
import org.springframework.stereotype.*;
import java.time.*;
import java.time.format.*;
import java.util.concurrent.*;

@SpringBootApplication
@EnableScheduling
@EnableAsync
public class TaskSchedAdvanced {
    public static void main(String[] args) throws Exception {
        var ctx = SpringApplication.run(TaskSchedAdvanced.class, args);
        Thread.sleep(3500);
        SpringApplication.exit(ctx);
    }

    // Primary scheduler — poolSize=2 means at most 2 scheduled tasks run simultaneously
    @Bean
    ThreadPoolTaskScheduler taskScheduler() {
        var ts = new ThreadPoolTaskScheduler();
        ts.setPoolSize(2);
        ts.setThreadNamePrefix("app-sched-");
        ts.setAwaitTerminationSeconds(30); // graceful shutdown
        ts.setWaitForTasksToCompleteOnShutdown(true);
        ts.initialize();
        return ts;
    }
}

// Declarative cron scheduling
@Component
class ReportScheduler {
    // Cron: second minute hour day-of-month month day-of-week
    // "0/2 * * * * *" = every 2 seconds (demo purposes)
    @Scheduled(cron = "0/2 * * * * *")
    public void generateDailyReport() {
        System.out.println("[Report] Generating at " + LocalTime.now().format(
            DateTimeFormatter.ofPattern("HH:mm:ss")));
    }
}

// Programmatic scheduling via TaskScheduler
@Service
class DynamicScheduler {
    private final ThreadPoolTaskScheduler scheduler;
    private ScheduledFuture<?> currentTask;

    DynamicScheduler(ThreadPoolTaskScheduler scheduler) { this.scheduler = scheduler; }

    @org.springframework.boot.context.event.EventListener(ApplicationReadyEvent.class)
    public void start() {
        System.out.println("[Dynamic] Starting heartbeat task");
        // Schedule with fixed delay programmatically — can be cancelled/rescheduled at runtime
        currentTask = scheduler.scheduleWithFixedDelay(
            () -> System.out.println("[Heartbeat] at " + LocalTime.now().withNano(0)),
            Instant.now().plusMillis(500),   // first run: 500ms from now
            Duration.ofMillis(800));          // then every 800ms
    }

    public void reschedule(Duration newDelay) {
        if (currentTask != null) currentTask.cancel(false);
        currentTask = scheduler.scheduleWithFixedDelay(
            () -> System.out.println("[Heartbeat-rescheduled] at " + LocalTime.now().withNano(0)),
            Instant.now(),
            newDelay);
    }
}

// SchedulingConfigurer — customise the scheduler used by @Scheduled globally
@Configuration
class SchedulingConfig implements SchedulingConfigurer {
    private final ThreadPoolTaskScheduler taskScheduler;
    SchedulingConfig(ThreadPoolTaskScheduler taskScheduler) { this.taskScheduler = taskScheduler; }

    @Override
    public void configureTasks(ScheduledTaskRegistrar registrar) {
        registrar.setScheduler(taskScheduler);
        System.out.println("[Config] @Scheduled tasks will use " + taskScheduler.getThreadNamePrefix());
    }
}
```

How to run: `./mvnw spring-boot:run` in a Spring Boot project.

`SchedulingConfigurer` binds `@Scheduled` tasks to the custom `ThreadPoolTaskScheduler`. Without it, Spring Boot creates a single-threaded scheduler by default — all `@Scheduled` methods run serially. `currentTask.cancel(false)` cancels after current execution completes (false = don't interrupt). `setWaitForTasksToCompleteOnShutdown(true)` + `setAwaitTerminationSeconds(30)` provides graceful shutdown: running tasks complete before the JVM exits.

## 6. Walkthrough

Tracing `@Scheduled(fixedDelay = 500)` lifecycle:

**Step 1 — Context refresh. `@EnableScheduling` activates `ScheduledAnnotationBeanPostProcessor`.**

**Step 2 — `ScheduledAnnotationBeanPostProcessor` scans all beans for `@Scheduled` methods.** Finds `InventoryScheduler.checkLowStock`.

**Step 3 — `SchedulingConfigurer.configureTasks` called (if implemented):** registers the scheduler and any additional tasks.

**Step 4 — `checkLowStock` registered with `ThreadPoolTaskScheduler` as a `fixedDelay=500` trigger.**

**Step 5 — Context is running. At T=0:**
- Scheduler submits `checkLowStock()` to the thread pool.
- `thread=sched-1` prints `[LowStock] Check #1 at ...`.
- Task takes ~0 ms to complete.

**Step 6 — At T=0+500ms:** scheduler sees 500ms has passed since task completion → submits again.

**Step 7 — Same cycle repeats.** At Check #3, the method throws `RuntimeException`. The scheduler logs the exception; since it's a `fixedDelay` trigger, it reschedules again after the exception (the exception doesn't stop the scheduler).

**For `fixedRate=1000`:**
- At T=0: first run.
- At T=1000ms: second run begins regardless of whether first has finished.
- If task takes 1200ms, and second invocation starts at T=1000ms while first is still running → both run concurrently on separate pool threads.

**For cron `"0/2 * * * * *"`:**
- Fires at :00, :02, :04, :06, ... seconds of every minute. If `poolSize=1` and task takes 3 seconds, the :02 trigger is missed (queued or dropped depending on configuration).

## 7. Gotchas & takeaways

> **`@Scheduled` methods must be `void` and take no arguments.** They run in the scheduler thread pool — do not block for extended periods if `poolSize=1` (default in Spring Boot), as this delays all other scheduled tasks.

> **Default Spring Boot `ThreadPoolTaskScheduler` has `poolSize=1`** — all `@Scheduled` methods run serially. If one task blocks, all others are delayed. Configure `spring.task.scheduling.pool.size=N` in `application.properties` or define a custom `TaskScheduler` bean.

- **`fixedRate` overlapping:** if a `fixedRate` task takes longer than the rate, the next invocation begins immediately after, with potential concurrent execution. Limit pool size and use `fixedDelay` if overlap is not safe.
- **`@Async` + `@Scheduled` together:** do NOT annotate a `@Scheduled` method with `@Async` — the scheduler already runs the task on a pool thread. Adding `@Async` would dispatch it again to a second pool, creating unnecessary context switching. Use `@Async` on business method calls from within the scheduled method if you need further parallelism.
- **Graceful shutdown:** `ThreadPoolTaskScheduler.setWaitForTasksToCompleteOnShutdown(true)` + `setAwaitTerminationSeconds(N)` — Spring calls `shutdown()` on the executor at context close; with these settings, it waits for running tasks to complete up to N seconds.
- **Spring Boot properties:** `spring.task.execution.*` configures `ThreadPoolTaskExecutor` (for `@Async`); `spring.task.scheduling.*` configures `ThreadPoolTaskScheduler` (for `@Scheduled`). Check `TaskExecutionAutoConfiguration` and `TaskSchedulingAutoConfiguration`.
- **`@Scheduled` + `@Transactional`:** each invocation opens a new transaction. Do not annotate the `@Scheduled` method itself with `@Transactional` if it calls multiple transactional service methods — use separate `@Transactional` service calls instead to keep transaction scope tight.
