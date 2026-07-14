---
card: microservices
gi: 556
slug: spring-cloud-task-short-lived-microservices
title: "Spring Cloud Task (short-lived microservices)"
---

## 1. What it is

**Spring Cloud Task** is designed for short-lived Spring Boot applications — a task that starts, does one bounded piece of work (a batch data-processing job, a scheduled cleanup, a one-off migration), and exits, rather than running indefinitely as a long-lived, request-serving service. It automatically records each execution's lifecycle (start time, end time, exit code, exception if any) into a shared datastore, giving operational visibility into "did this task run, when, and did it succeed" for something that, unlike a typical microservice, doesn't stay up long enough to be monitored the way a running service would be.

## 2. Why & when

You reach for Spring Cloud Task specifically for bounded, finite units of work, where a normal long-running service's operational model (health checks on a running process, monitoring an always-on endpoint) doesn't apply:

- **A long-running microservice's health is monitored by checking a running process** — health endpoints, uptime, request metrics. A task that runs for thirty seconds and exits has no "uptime" to speak of; the operationally meaningful question is entirely different — "did the last run succeed, when did it last run, how long did it take" — and Spring Cloud Task is built specifically to answer exactly these questions for short-lived executions.
- **Every task execution is recorded to a shared `TaskRepository`** (backed by a relational database) — start time, end time, exit code, and any exception message, giving a durable, queryable history of every past run, which is exactly the kind of record a normal long-running service doesn't need (since you'd just check if the process is currently up), but a short-lived task absolutely does.
- **Tasks integrate naturally with Spring Batch** (for structured, step-based batch jobs) and with schedulers (a cron trigger, or orchestrated by [Spring Cloud Data Flow](0557-spring-cloud-data-flow-pipeline-orchestration.md)) — Task provides the execution-tracking layer underneath, regardless of what triggers a given run or how internally structured the work is.
- **You reach for it whenever you're building something that's fundamentally "run once, do a bounded thing, exit" rather than "stay up and serve requests continuously"** — a nightly reconciliation job, a one-off data migration, a scheduled report generator are all natural fits; an always-on REST API is not.

## 3. Core concept

Think of the difference between a store that's open continuously (a long-running service, whose "health" you'd check by seeing if the lights are on and someone's at the register right now) versus a delivery driver who makes one bounded trip, drops off a package, and is done (a task, whose "health" isn't about whether they're currently active at this exact moment, but about a *logged history*: did today's delivery happen, when did it start, when did it finish, did it succeed or hit a problem along the way). You wouldn't check a delivery driver's "uptime" the way you'd check a store's — you'd check the delivery log. Spring Cloud Task is exactly that delivery log for short-lived Spring Boot executions.

Concretely:

1. **`@EnableTask` on a Spring Boot application** activates Spring Cloud Task's lifecycle tracking — at application startup, a new row is created in the `TASK_EXECUTION` table recording the start time and a generated execution ID.
2. **When the application's `main` method returns (the task completes, whether successfully or via an exception)**, Spring Cloud Task updates that same row with the end time and exit code (0 for success, non-zero for failure), and, if an exception occurred, records its message.
3. **The `TaskRepository` (backed by a relational database configured via normal Spring datasource properties) persists this history durably**, queryable independently of whether any given task execution's process is still running — you can ask "show me every execution of this task in the last week, and which ones failed" at any time, long after the process itself has exited.
4. **Task executions can be linked to Spring Batch job executions** (if the task's work is structured as a Spring Batch job internally), giving a combined view: which task execution triggered which specific batch job run, and that job's own step-level execution details.

## 4. Diagram

<svg viewBox="0 0 660 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A short-lived task starts, does bounded work, and exits, with Spring Cloud Task recording its start time, end time, and exit status to a durable, queryable repository">
  <rect x="20" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">task starts</text>
  <rect x="200" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="270" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">bounded work runs</text>
  <rect x="380" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">process exits</text>

  <line x1="160" y1="80" x2="200" y2="80" stroke="#8b949e" marker-end="url(#a16)"/>
  <line x1="340" y1="80" x2="380" y2="80" stroke="#8b949e" marker-end="url(#a16)"/>

  <rect x="520" y="60" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="580" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">TASK_EXECUTION</text>
  <line x1="90" y1="100" x2="580" y2="60" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="330" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">durable, queryable record: start, end, exit code, exception -- long after the process itself is gone</text>
  <defs><marker id="a16" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

Spring Cloud Task's repository records a durable history of every run, independent of whether any given process is still alive.

## 5. Runnable example

Scenario: a nightly reconciliation task whose execution history needs tracking. We start with a plain Java model of a task with no history tracking (the gap), extend it to a self-recording task, then show the real Spring Cloud Task shape.

### Level 1 — Basic

```java
// File: UntrackedTask.java -- a task that runs and exits with NO
// recorded history at all -- once it's done, there's no record of it.
public class UntrackedTask {
    static void doReconciliationWork() {
        System.out.println("Reconciling inventory counts...");
    }

    public static void main(String[] args) {
        doReconciliationWork();
        System.out.println("Task finished. But was there a record of WHEN this ran, or whether it succeeded? No.");
    }
}
```

How to run: `java UntrackedTask.java`

Once this process exits, there's no durable record anywhere of when it ran, how long it took, or whether it succeeded — if someone asks "did last night's reconciliation actually run?" days later, there's nothing to check against, since the only signal (this process being alive) disappeared the moment it exited.

### Level 2 — Intermediate

```java
// File: SelfRecordingTask.java -- models a task that RECORDS its own
// execution history to a shared, durable store -- closing that gap.
import java.time.*;
import java.util.*;

public class SelfRecordingTask {
    record TaskExecution(long id, Instant startTime, Instant endTime, int exitCode, String exceptionMessage) {}
    static List<TaskExecution> taskExecutionHistory = new ArrayList<>(); // models a durable TASK_EXECUTION table

    static void runTracked(Runnable work, Instant startTime) {
        long executionId = taskExecutionHistory.size() + 1;
        int exitCode = 0;
        String exceptionMessage = null;
        try {
            work.run();
        } catch (Exception e) {
            exitCode = 1;
            exceptionMessage = e.getMessage();
        }
        taskExecutionHistory.add(new TaskExecution(executionId, startTime, Instant.now(), exitCode, exceptionMessage));
    }

    public static void main(String[] args) {
        runTracked(() -> System.out.println("Reconciling inventory counts..."), Instant.now());
        runTracked(() -> { throw new RuntimeException("downstream inventory service unavailable"); }, Instant.now());

        System.out.println("--- Task execution history (queryable LONG after each process exited) ---");
        for (TaskExecution execution : taskExecutionHistory) {
            System.out.println(execution);
        }
    }
}
```

How to run: `java SelfRecordingTask.java`

`runTracked` wraps the actual work, recording a `TaskExecution` entry (including exit code and exception message on failure) into `taskExecutionHistory` regardless of whether the work succeeded or threw — this durable history is exactly what remains queryable long after any individual task's process has exited, closing the gap demonstrated in Level 1.

### Level 3 — Advanced

```java
// File: SpringCloudTaskRealShape.java -- the REAL Spring Cloud Task
// shape: @EnableTask automatically records execution history to a
// TASK_EXECUTION table, with NO manual tracking code needed.
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.task.configuration.EnableTask;
import org.springframework.context.annotation.Bean;

public class SpringCloudTaskRealShape {

    @SpringBootApplication
    @EnableTask // activates automatic TASK_EXECUTION tracking for this application's ENTIRE run
    static class ReconciliationTaskApplication {
        public static void main(String[] args) {
            SpringApplication.run(ReconciliationTaskApplication.class, args);
        }

        @Bean
        public CommandLineRunner reconcile() {
            return args -> {
                System.out.println("Reconciling inventory counts...");
                // if this throws, Spring Cloud Task records a NON-ZERO exit code
                // and the exception message in TASK_EXECUTION automatically
            };
        }
    }
    // application.yml:
    //   spring.datasource.url: jdbc:postgresql://task-db:5432/task_metadata
    //   -- Spring Cloud Task creates/uses TASK_EXECUTION and related tables here automatically.
}
```

How to run: requires `spring-cloud-starter-task` and a configured `DataSource` pointed at a database Spring Cloud Task can create its `TASK_EXECUTION` (and related) tables in; run via `java -jar reconciliation-task.jar`, then query `SELECT * FROM TASK_EXECUTION ORDER BY START_TIME DESC` against that database to see a durable record of this run's start time, end time, and exit code, entirely independent of the process itself (which has already exited by the time you run that query).

`@EnableTask` is the single annotation that activates automatic lifecycle recording — `reconcile()`'s `CommandLineRunner` body contains no tracking code of its own at all; Spring Cloud Task wraps the entire application run, creating a `TASK_EXECUTION` row at startup and updating it with the end time and exit status when the application terminates, whether that termination is a clean exit or an uncaught exception.

## 6. Walkthrough

Trace what happens when the Level 3 application is run as a scheduled nightly job, and the `reconcile()` bean throws an exception due to a downstream outage:

1. **The application starts.** Because of `@EnableTask`, Spring Cloud Task's auto-configuration inserts a new row into `TASK_EXECUTION`, recording `START_TIME = now()`, a generated `TASK_EXECUTION_ID`, and the task's name (derived from the application's name).
2. **The `reconcile()` `CommandLineRunner` executes.** It attempts to reconcile inventory counts, but the downstream inventory service it depends on is unavailable, causing it to throw an exception.
3. **Spring Boot's own application-runner infrastructure propagates this exception**, and Spring Cloud Task's lifecycle listener catches it as part of the application's shutdown sequence (rather than letting it silently vanish along with the exiting process).
4. **Spring Cloud Task updates the `TASK_EXECUTION` row created in step 1**: setting `END_TIME = now()`, `EXIT_CODE` to a non-zero value, and recording the exception's message in the `EXIT_MESSAGE`/`ERROR_MESSAGE` column.
5. **The JVM process exits** (with a non-zero exit code, which a surrounding orchestration layer — a cron job runner, Kubernetes CronJob, or Spring Cloud Data Flow — can also observe directly at the process level).
6. **Some time later — hours, days, whenever someone needs to check — a query against `TASK_EXECUTION`** (`SELECT * FROM TASK_EXECUTION WHERE TASK_NAME = 'reconciliation-task' ORDER BY START_TIME DESC LIMIT 5`) reveals this specific failed run: its start time, its (short) duration, its non-zero exit code, and the recorded exception message — a durable, queryable answer to "did last night's reconciliation run, and if it failed, why," long after the process itself is gone.

## 7. Gotchas & takeaways

> **Gotcha:** Spring Cloud Task records an execution's outcome based on how the application's main run completes — if a task spawns background threads that continue running (or fail silently) after the main thread returns and the application is considered "done," those background failures won't be reflected in the recorded exit code or message unless the task's own code explicitly waits for and surfaces their outcome before allowing the application to terminate.

- Spring Cloud Task is designed for bounded, short-lived executions where "uptime monitoring" doesn't apply — the operationally meaningful question is "did the last run succeed," answered by a durable execution history rather than a currently-running process.
- `@EnableTask` automatically records start time, end time, exit code, and exception details to a `TASK_EXECUTION` table, with zero manual tracking code needed in the task's own business logic.
- This execution history remains queryable indefinitely, long after any individual task's process has exited — exactly the visibility a short-lived execution needs that a long-running service's health-check model doesn't provide.
- Ensure any background work a task spawns is actually awaited before the task's main execution completes, or its outcome won't be reflected in the recorded exit status at all.
