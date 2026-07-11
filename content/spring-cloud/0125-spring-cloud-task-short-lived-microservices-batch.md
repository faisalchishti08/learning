---
card: spring-cloud
gi: 125
slug: spring-cloud-task-short-lived-microservices-batch
title: "Spring Cloud Task (short-lived microservices/batch)"
---

## 1. What it is

Spring Cloud Task turns a Spring Boot application into a tracked, short-lived process — one that starts, runs some finite unit of work (a data import, a cleanup job, a report generation), and exits, with Spring Cloud Task automatically recording that execution's start time, end time, exit code, and any exception in a database-backed `TaskExecution` record, giving batch-style, run-and-terminate applications the same kind of execution history and observability that long-running services get from their own uptime and monitoring.

```java
@SpringBootApplication
@EnableTask
public class ImportOrdersTask {
    public static void main(String[] args) {
        SpringApplication.run(ImportOrdersTask.class, args);
    }
}
```

```java
@Component
class ImportRunner implements CommandLineRunner {
    public void run(String... args) {
        // do the actual import work, then the application exits naturally
    }
}
```

## 2. Why & when

A long-running Spring Boot service (a `@RestController`-based microservice) and a short-lived, run-once process (a nightly data import, an ad-hoc report job) have fundamentally different lifecycles, but both are commonly built with Spring Boot for the same reasons — dependency injection, configuration management, the broader Spring ecosystem. Without Spring Cloud Task, a short-lived Spring Boot application that simply runs and exits leaves no record of having run at all beyond whatever the process's own logs happened to capture — no queryable history of "did this job run last night, did it succeed, how long did it take, what was the exit code." `@EnableTask` adds exactly this: a `TaskExecution` record persisted to a database the moment the application starts, updated with the end time and exit code the moment it finishes, giving batch-style jobs the same kind of structured execution history a long-running service's own monitoring stack would otherwise be relied on to provide.

Reach for Spring Cloud Task when:

- Building a short-lived, run-to-completion Spring Boot application (a scheduled batch job, a one-off migration script, a data processing pipeline stage) and wanting a queryable, persistent record of every execution — when it ran, how long it took, whether it succeeded.
- Running batch-style jobs within a broader Spring Cloud Data Flow orchestration (a later card) — Data Flow's own task orchestration and monitoring builds directly on the `TaskExecution` records Spring Cloud Task produces.
- Needing to correlate a specific job run with downstream effects or troubleshoot a specific failed run — a `TaskExecution`'s recorded start/end time and exit code gives a concrete, queryable anchor for that investigation, rather than relying purely on scattered log timestamps.

## 3. Core concept

```
 application starts (main() runs)
        |
        v
 @EnableTask intercepts startup:
   INSERT a new TaskExecution row: {taskName, startTime, executionId, ...}
        |
        v
 application does its actual work (CommandLineRunner, ApplicationRunner, or any bean's own logic)
        |
        v
 application finishes (successfully OR with an exception)
        |
        v
 @EnableTask intercepts shutdown:
   UPDATE the TaskExecution row: {endTime, exitCode, exitMessage, (exception details if any)}
        |
        v
 process EXITS -- but the TaskExecution record PERSISTS, queryable long after the process is gone
```

The application code itself needs no awareness of `TaskExecution` at all for the basic case — `@EnableTask` alone wraps the application's entire lifecycle with this recording behavior automatically.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A short lived application starts does its work and exits while EnableTask automatically records a TaskExecution row at startup and updates it at shutdown leaving a persistent queryable history after the process itself has terminated">
  <rect x="20" y="20" width="140" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="90" y="44" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">app starts</text>

  <rect x="230" y="20" width="180" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">does the actual work</text>

  <rect x="480" y="20" width="140" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="550" y="44" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">app exits</text>

  <rect x="150" y="100" width="340" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="122" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">TaskExecution row</text>
  <text x="320" y="136" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">INSERT at start, UPDATE at end -- PERSISTS after exit</text>

  <defs><marker id="a125" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="160" y1="40" x2="230" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a125)"/>
  <line x1="410" y1="40" x2="480" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a125)"/>
  <line x1="90" y1="60" x2="250" y2="100" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,3" marker-end="url(#a125)"/>
  <line x1="550" y1="60" x2="390" y2="100" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,3" marker-end="url(#a125)"/>
</svg>

The process itself is transient; the `TaskExecution` record it leaves behind is not — that record is precisely what makes a run-and-exit application's history queryable long after the process has terminated.

## 5. Runnable example

The scenario: model the `TaskExecution` lifecycle — a record created at start, updated at end, persisting after the modeled process "exits" — for a successful run and a failed run, then query execution history across several runs. Start with a single successful task execution recorded end to end, then add a failed execution capturing the exception, then add querying history across multiple runs to show the persistent, queryable value this record provides.

### Level 1 — Basic

A single task execution: a record created at start, updated at successful completion.

```java
import java.util.*;

public class SpringCloudTaskLevel1 {
    static class TaskExecution {
        String taskName;
        long startTime;
        Long endTime;
        Integer exitCode;
        TaskExecution(String taskName) { this.taskName = taskName; this.startTime = System.currentTimeMillis(); }
    }

    static List<TaskExecution> executionHistory = new ArrayList<>(); // stands in for the TaskExecution DB table

    static void runTask(String taskName, Runnable work) {
        TaskExecution execution = new TaskExecution(taskName);
        executionHistory.add(execution); // recorded IMMEDIATELY at start, before any work runs
        System.out.println(taskName + ": TaskExecution created, id in history now: " + executionHistory.size());

        work.run(); // the actual application logic

        execution.endTime = System.currentTimeMillis();
        execution.exitCode = 0; // success
        System.out.println(taskName + ": completed, exitCode=" + execution.exitCode);
    }

    public static void main(String[] args) {
        runTask("import-orders", () -> System.out.println("  ... doing the actual import work ..."));
    }
}
```

How to run: `java SpringCloudTaskLevel1.java`

`runTask` records the `TaskExecution` before the actual work runs (so even a crash mid-work would leave a start record) and updates it with `endTime`/`exitCode` only after the work completes — this two-phase recording is exactly what `@EnableTask` does automatically around a real application's own lifecycle.

### Level 2 — Intermediate

Add a failed execution, capturing the exception rather than losing that information when the process would otherwise simply crash and exit.

```java
import java.util.*;

public class SpringCloudTaskLevel2 {
    static class TaskExecution {
        String taskName;
        long startTime;
        Long endTime;
        Integer exitCode;
        String exitMessage;
        TaskExecution(String taskName) { this.taskName = taskName; this.startTime = System.currentTimeMillis(); }
    }

    static List<TaskExecution> executionHistory = new ArrayList<>();

    static void runTask(String taskName, Runnable work) {
        TaskExecution execution = new TaskExecution(taskName);
        executionHistory.add(execution);

        try {
            work.run();
            execution.exitCode = 0;
            execution.exitMessage = "completed successfully";
        } catch (RuntimeException e) {
            execution.exitCode = 1;
            execution.exitMessage = "FAILED: " + e.getMessage(); // the failure is CAPTURED, not just an uncaught crash
        } finally {
            execution.endTime = System.currentTimeMillis();
        }

        System.out.println(taskName + ": exitCode=" + execution.exitCode + " message=" + execution.exitMessage);
    }

    public static void main(String[] args) {
        runTask("import-orders", () -> System.out.println("  ... import succeeds ..."));

        runTask("cleanup-stale-records", () -> {
            throw new RuntimeException("database connection lost mid-cleanup");
        });
    }
}
```

How to run: `java SpringCloudTaskLevel2.java`

The second `runTask` call's `work.run()` throws, but the surrounding `try`/`catch`/`finally` still records a complete `TaskExecution` with `exitCode=1` and a descriptive `exitMessage`, rather than letting the exception propagate uncaught and losing that diagnostic information — this is exactly the value `@EnableTask` provides for a real application: even a genuinely crashing task still leaves behind a queryable, informative execution record rather than just a vanished process and scattered log lines.

### Level 3 — Advanced

Add querying execution history across multiple runs — filtering by task name, finding the most recent failure, and computing a success rate, mirroring the kind of operational queries a real `TaskExecution` repository (the next card) supports.

```java
import java.util.*;
import java.util.stream.*;

public class SpringCloudTaskLevel3 {
    static class TaskExecution {
        String taskName;
        long startTime;
        Long endTime;
        Integer exitCode;
        String exitMessage;
        TaskExecution(String taskName) { this.taskName = taskName; this.startTime = System.currentTimeMillis(); }
        long durationMs() { return endTime - startTime; }
        boolean succeeded() { return exitCode != null && exitCode == 0; }
    }

    static List<TaskExecution> executionHistory = new ArrayList<>();

    static void runTask(String taskName, Runnable work) {
        TaskExecution execution = new TaskExecution(taskName);
        executionHistory.add(execution);
        try {
            work.run();
            execution.exitCode = 0;
        } catch (RuntimeException e) {
            execution.exitCode = 1;
            execution.exitMessage = e.getMessage();
        } finally {
            execution.endTime = System.currentTimeMillis();
        }
    }

    static List<TaskExecution> findByTaskName(String taskName) {
        return executionHistory.stream().filter(e -> e.taskName.equals(taskName)).toList();
    }

    static double successRate(String taskName) {
        List<TaskExecution> runs = findByTaskName(taskName);
        long successCount = runs.stream().filter(TaskExecution::succeeded).count();
        return (double) successCount / runs.size();
    }

    public static void main(String[] args) {
        runTask("import-orders", () -> {});
        runTask("import-orders", () -> { throw new RuntimeException("timeout"); });
        runTask("import-orders", () -> {});
        runTask("cleanup-stale-records", () -> {});

        System.out.println("import-orders runs: " + findByTaskName("import-orders").size());
        System.out.println("import-orders success rate: " + successRate("import-orders"));

        Optional<TaskExecution> lastFailure = findByTaskName("import-orders").stream()
                .filter(e -> !e.succeeded())
                .reduce((first, second) -> second); // finds the LAST (most recent) failure in the filtered list
        System.out.println("last import-orders failure message: " + lastFailure.map(e -> e.exitMessage).orElse("none"));
    }
}
```

How to run: `java SpringCloudTaskLevel3.java`

`findByTaskName("import-orders")` filters the shared `executionHistory` down to exactly the three `"import-orders"` runs (excluding the unrelated `"cleanup-stale-records"` run), `successRate` computes `2/3 ≈ 0.667` (two successes, one failure), and `lastFailure` correctly identifies the single failed run's `exitMessage` (`"timeout"`) — this is precisely the kind of operational history querying a real, database-backed `TaskExecution` repository enables across potentially thousands of historical runs, letting an operator answer "how reliable has this job been" or "what went wrong last time it failed" without digging through raw process logs.

## 6. Walkthrough

Trace the `successRate("import-orders")` computation in Level 3.

1. `findByTaskName("import-orders")` filters `executionHistory` (four total entries) down to the three whose `taskName` equals `"import-orders"` — the fourth entry, `"cleanup-stale-records"`, is correctly excluded.
2. `runs.stream().filter(TaskExecution::succeeded).count()` iterates these three entries, calling `succeeded()` on each — for the first (`work` was a no-op, so `exitCode=0`), `succeeded()` returns `true`. For the second (`work` threw, so `exitCode=1`), `succeeded()` returns `false`. For the third (again a no-op, `exitCode=0`), `succeeded()` returns `true`.
3. `count()` sums the `true` results, yielding `successCount = 2`.
4. `(double) successCount / runs.size()` computes `2 / 3`, cast to `double` division (avoiding integer-division truncation because `successCount` was explicitly cast to `double` first), yielding approximately `0.667`.
5. This value is returned and printed — an operator reading this output immediately knows two-thirds of `"import-orders"` runs have historically succeeded, a concrete, queryable metric that would otherwise require manually parsing and correlating scattered process logs across potentially many separate job invocations spread across days or weeks.

```
executionHistory: [import-orders(success), import-orders(FAILED: timeout), import-orders(success), cleanup-stale-records(success)]

findByTaskName("import-orders") -> [success, FAILED, success]   (3 of 4 total entries)
successCount = 2 (two of the three have exitCode == 0)
successRate = 2 / 3 ≈ 0.667
```

## 7. Gotchas & takeaways

> **Gotcha:** `@EnableTask` records execution history but does not itself provide retry, scheduling, or orchestration logic — a task application that fails simply exits with a recorded failure; something else (a cron job, Spring Cloud Data Flow's own scheduling, an external orchestrator) is responsible for deciding whether and when to retry. Confusing `@EnableTask`'s execution-tracking role with a full job-scheduling/retry framework's role is a common early misunderstanding.

- Spring Cloud Task's core value is giving short-lived, run-to-completion Spring Boot applications the same kind of persistent, queryable execution history that a long-running service's monitoring stack would otherwise provide — without it, a batch job's history is limited to whatever scattered log lines happened to be captured.
- The two-phase recording (a record created at start, updated at end) ensures even a task that crashes mid-execution leaves behind a start record and, where the crash is caught, a descriptive failure record — rather than simply vanishing with no trace beyond process logs.
- Querying execution history (by task name, by success/failure, by time range) is what turns individual `TaskExecution` records into genuinely useful operational insight — the next card covers the `TaskExecution` repository API that supports exactly this kind of querying against a real, persistent, database-backed history.
- Spring Cloud Task is a natural fit within a broader Spring Cloud Data Flow orchestration (a later card in this section), where Data Flow's own task launching and monitoring builds directly on the execution records `@EnableTask` produces.
