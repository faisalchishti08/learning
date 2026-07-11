---
card: spring-cloud
gi: 126
slug: taskexecution-repository
title: "TaskExecution & repository"
---

## 1. What it is

`TaskExplorer` is Spring Cloud Task's read-only query API over the persisted `TaskExecution` records — offering methods like `getTaskExecutionsByName`, `getLatestTaskExecutionForTaskName`, and `getRunningTaskExecutions` — letting application code (a monitoring dashboard, an admin endpoint, another part of the same or a different application) query a task's execution history programmatically, exactly the same operations modeled by hand in the previous card's `findByTaskName`/`successRate` helpers, but backed by a real, persistent database table rather than an in-memory list.

```java
@Autowired TaskExplorer taskExplorer;

List<TaskExecution> recentRuns = taskExplorer.getTaskExecutionsByName("import-orders", Pageable.ofSize(10));
TaskExecution latest = taskExplorer.getLatestTaskExecutionForTaskName("import-orders");
List<TaskExecution> currentlyRunning = taskExplorer.getRunningTaskExecutions("import-orders", Pageable.unpaged());
```

```sql
-- the underlying table TaskExplorer queries against
SELECT * FROM TASK_EXECUTION WHERE TASK_NAME = 'import-orders' ORDER BY START_TIME DESC;
```

## 2. Why & when

A `TaskExecution` record's value is limited if it's only ever inserted and never queried back — the whole point of persisting execution history is to actually use it later, whether that's a dashboard showing recent job runs, an alert checking whether a scheduled task's last run failed, or a diagnostic tool investigating a specific historical execution's details. `TaskExplorer` provides this query capability as a proper Spring-managed bean, backed by the same database table `@EnableTask` writes to, so any part of an application (or, commonly, a separate monitoring/admin service with its own read access to that same database) can build meaningful operational tooling on top of task execution history without writing raw SQL or reimplementing the query logic themselves.

Reach for `TaskExplorer` when:

- Building a dashboard or admin view showing recent task runs, their status, and duration — `getTaskExecutionsByName` (paginated) is the direct building block for exactly this kind of view.
- Implementing an alert or health check that needs to know whether a scheduled task's most recent run succeeded — `getLatestTaskExecutionForTaskName` gives direct access to exactly that one record without needing to fetch and filter a larger history.
- Detecting currently-in-progress executions — useful for preventing overlapping runs of the same task, or simply surfacing "this job is currently running" in an operational view — `getRunningTaskExecutions` (records with a start time but no end time yet) answers this directly.

## 3. Core concept

```
 TASK_EXECUTION table (populated automatically by @EnableTask):
   EXECUTION_ID | TASK_NAME       | START_TIME | END_TIME | EXIT_CODE
   1            | import-orders   | ...        | ...      | 0
   2            | import-orders   | ...        | ...      | 1
   3            | import-orders   | ...        | NULL     | NULL    <- currently running (no end time yet)
   4            | cleanup-records | ...        | ...      | 0

 TaskExplorer methods query this table WITHOUT application code writing SQL:
   getTaskExecutionsByName("import-orders", ...)     -> rows 1, 2, 3
   getLatestTaskExecutionForTaskName("import-orders") -> row 3 (most recent start time)
   getRunningTaskExecutions("import-orders", ...)     -> row 3 (END_TIME IS NULL)
```

`TaskExplorer` is deliberately read-only — writing/updating `TaskExecution` records remains `@EnableTask`'s own internal responsibility, keeping the query API's role cleanly separated from the recording mechanism.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EnableTask writes TaskExecution rows into a shared database table while TaskExplorer provides a separate read only query API over the same table letting a dashboard or alerting tool read execution history without writing raw SQL">
  <rect x="20" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="95" y="44" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">@EnableTask (writes)</text>

  <rect x="245" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">TASK_EXECUTION table</text>

  <rect x="470" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="545" y="44" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">TaskExplorer (reads)</text>

  <rect x="470" y="100" width="150" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="545" y="124" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">dashboard / alerting</text>

  <defs><marker id="a126" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="170" y1="40" x2="245" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a126)"/>
  <line x1="395" y1="40" x2="470" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a126)"/>
  <line x1="545" y1="60" x2="545" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a126)"/>
</svg>

Writing and reading are cleanly split into two separate concerns, both operating against the same underlying table.

## 5. Runnable example

The scenario: model `TaskExplorer`'s core query methods against a simulated execution table populated by the previous card's recording mechanism. Start with `getTaskExecutionsByName`, then add `getLatestTaskExecutionForTaskName`, then add `getRunningTaskExecutions` distinguishing in-progress executions from completed ones, mirroring the three most commonly used real query operations.

### Level 1 — Basic

`getTaskExecutionsByName`, filtering a simulated table by task name.

```java
import java.util.*;

public class TaskExplorerLevel1 {
    static class TaskExecution {
        String taskName;
        long startTime;
        Long endTime;
        Integer exitCode;
        TaskExecution(String taskName, long startTime, Long endTime, Integer exitCode) {
            this.taskName = taskName; this.startTime = startTime; this.endTime = endTime; this.exitCode = exitCode;
        }
    }

    static class TaskExplorer {
        List<TaskExecution> table;
        TaskExplorer(List<TaskExecution> table) { this.table = table; }

        List<TaskExecution> getTaskExecutionsByName(String taskName) {
            return table.stream().filter(e -> e.taskName.equals(taskName)).toList();
        }
    }

    public static void main(String[] args) {
        List<TaskExecution> table = List.of(
                new TaskExecution("import-orders", 1000, 1500, 0),
                new TaskExecution("import-orders", 2000, 2600, 1),
                new TaskExecution("cleanup-records", 3000, 3200, 0)
        );

        TaskExplorer explorer = new TaskExplorer(table);
        List<TaskExecution> importRuns = explorer.getTaskExecutionsByName("import-orders");
        System.out.println("import-orders executions found: " + importRuns.size());
    }
}
```

How to run: `java TaskExplorerLevel1.java`

`getTaskExecutionsByName` correctly returns only the two `"import-orders"` entries, excluding the unrelated `"cleanup-records"` entry — this is the direct query-API equivalent of the previous card's hand-written `findByTaskName` helper, now framed as `TaskExplorer`'s own dedicated method.

### Level 2 — Intermediate

Add `getLatestTaskExecutionForTaskName`, returning only the single most recent execution rather than the full history.

```java
import java.util.*;

public class TaskExplorerLevel2 {
    static class TaskExecution {
        String taskName;
        long startTime;
        Long endTime;
        Integer exitCode;
        TaskExecution(String taskName, long startTime, Long endTime, Integer exitCode) {
            this.taskName = taskName; this.startTime = startTime; this.endTime = endTime; this.exitCode = exitCode;
        }
    }

    static class TaskExplorer {
        List<TaskExecution> table;
        TaskExplorer(List<TaskExecution> table) { this.table = table; }

        List<TaskExecution> getTaskExecutionsByName(String taskName) {
            return table.stream().filter(e -> e.taskName.equals(taskName)).toList();
        }

        Optional<TaskExecution> getLatestTaskExecutionForTaskName(String taskName) {
            return getTaskExecutionsByName(taskName).stream()
                    .max(Comparator.comparingLong(e -> e.startTime)); // the LATEST by start time, not insertion order
        }
    }

    public static void main(String[] args) {
        List<TaskExecution> table = List.of(
                new TaskExecution("import-orders", 1000, 1500, 0),
                new TaskExecution("import-orders", 3000, 3600, 1), // MOST recent, and it FAILED
                new TaskExecution("import-orders", 2000, 2600, 0)  // inserted out of chronological order, deliberately
        );

        TaskExplorer explorer = new TaskExplorer(table);
        Optional<TaskExecution> latest = explorer.getLatestTaskExecutionForTaskName("import-orders");

        latest.ifPresent(e -> System.out.println("latest run: startTime=" + e.startTime + " exitCode=" + e.exitCode));
    }
}
```

How to run: `java TaskExplorerLevel2.java`

`getLatestTaskExecutionForTaskName` correctly identifies the execution with `startTime=3000` as the latest, even though it wasn't the last element inserted into `table` — `Comparator.comparingLong(e -> e.startTime)` sorts by the actual start time value, not by list position, exactly mirroring how a real database query with `ORDER BY START_TIME DESC LIMIT 1` retrieves the genuinely most recent row regardless of insertion order.

### Level 3 — Advanced

Add `getRunningTaskExecutions`, distinguishing currently-in-progress executions (no `endTime` yet) from completed ones, and use it to prevent launching an overlapping run of the same task — a common, practical use of this query.

```java
import java.util.*;

public class TaskExplorerLevel3 {
    static class TaskExecution {
        String taskName;
        long startTime;
        Long endTime; // null while STILL RUNNING
        Integer exitCode;
        TaskExecution(String taskName, long startTime, Long endTime, Integer exitCode) {
            this.taskName = taskName; this.startTime = startTime; this.endTime = endTime; this.exitCode = exitCode;
        }
    }

    static class TaskExplorer {
        List<TaskExecution> table;
        TaskExplorer(List<TaskExecution> table) { this.table = table; }

        List<TaskExecution> getTaskExecutionsByName(String taskName) {
            return table.stream().filter(e -> e.taskName.equals(taskName)).toList();
        }

        List<TaskExecution> getRunningTaskExecutions(String taskName) {
            return getTaskExecutionsByName(taskName).stream()
                    .filter(e -> e.endTime == null) // no end time recorded yet -- STILL in progress
                    .toList();
        }
    }

    // models a launcher deciding whether to start a new run, avoiding overlap with an already-running instance
    static boolean tryLaunch(TaskExplorer explorer, String taskName) {
        List<TaskExecution> running = explorer.getRunningTaskExecutions(taskName);
        if (!running.isEmpty()) {
            System.out.println("REFUSING to launch '" + taskName + "' -- " + running.size() + " instance(s) already running");
            return false;
        }
        System.out.println("launching '" + taskName + "' -- no overlapping instance detected");
        return true;
    }

    public static void main(String[] args) {
        List<TaskExecution> table = new ArrayList<>(List.of(
                new TaskExecution("import-orders", 1000, 1500, 0),   // completed
                new TaskExecution("import-orders", 5000, null, null) // STILL RUNNING (no endTime)
        ));

        TaskExplorer explorer = new TaskExplorer(table);

        boolean launched = tryLaunch(explorer, "import-orders"); // should be REFUSED -- one is already running
        System.out.println("launch attempt result: " + launched);

        boolean cleanupLaunched = tryLaunch(explorer, "cleanup-records"); // different task, no running instances
        System.out.println("launch attempt result: " + cleanupLaunched);
    }
}
```

How to run: `java TaskExplorerLevel3.java`

`tryLaunch(explorer, "import-orders")` correctly refuses to launch, because `getRunningTaskExecutions` finds the second table entry (`endTime=null`) still in progress; `tryLaunch(explorer, "cleanup-records")` succeeds, since no entries for that task name exist in `table` at all — this pattern (checking `getRunningTaskExecutions` before launching a new instance) is a practical, common safeguard against accidentally running two overlapping instances of a task that assumes exclusive access to some resource, built directly on `TaskExplorer`'s query capability.

## 6. Walkthrough

Trace `tryLaunch(explorer, "import-orders")` in Level 3.

1. `explorer.getRunningTaskExecutions("import-orders")` is called — internally, `getTaskExecutionsByName("import-orders")` filters `table` down to both `"import-orders"` entries, then `.filter(e -> e.endTime == null)` further narrows this to only the second entry, whose `endTime` field is `null`.
2. `getRunningTaskExecutions` returns a single-element list containing that still-running execution.
3. Back in `tryLaunch`, `running.isEmpty()` evaluates `false` (the list has one element), so the `if (!running.isEmpty())` condition is `true`.
4. The method prints the refusal message, correctly reporting `"1 instance(s) already running"`, and returns `false`.
5. `main`'s `println` confirms `launch attempt result: false` — the launcher correctly avoided starting a second, overlapping `"import-orders"` execution while one was already mid-run, exactly the safeguard a real task launcher (whether custom code or Spring Cloud Data Flow's own scheduler) commonly implements using `TaskExplorer.getRunningTaskExecutions` to check before triggering a new run.

```
table: [import-orders(completed), import-orders(RUNNING, endTime=null)]

tryLaunch("import-orders"):
  getRunningTaskExecutions("import-orders") -> filters to endTime==null -> [1 running instance]
  running.isEmpty()? false -> REFUSE to launch

tryLaunch("cleanup-records"):
  getRunningTaskExecutions("cleanup-records") -> no entries AT ALL for this name -> []
  running.isEmpty()? true -> LAUNCH proceeds
```

## 7. Gotchas & takeaways

> **Gotcha:** `getRunningTaskExecutions` identifies executions with no recorded `endTime`, which technically includes both genuinely-still-running tasks *and* tasks whose process crashed so abruptly that `@EnableTask`'s own shutdown-recording logic never got a chance to run (a killed process, an out-of-memory crash bypassing normal shutdown hooks) — a stale "running" record from a task that actually died ungracefully weeks ago can incorrectly block new launches indefinitely unless separately detected and cleaned up (typically via a timeout-based staleness check layered on top of this query).

- `TaskExplorer` provides a clean, dedicated read API over `TaskExecution` history, keeping query logic out of raw SQL and out of application code that would otherwise need to reimplement the same filtering repeatedly.
- `getTaskExecutionsByName` and `getLatestTaskExecutionForTaskName` are the natural building blocks for dashboards and simple health checks; `getRunningTaskExecutions` is specifically useful for overlap-prevention and "what's currently in progress" operational views.
- Because `TaskExplorer` is read-only, it cleanly separates the query concern from `@EnableTask`'s own write/recording concern (the previous card) — application code building monitoring or launch-guarding logic depends only on `TaskExplorer`, never needing direct write access to the underlying table.
- A "still running" record based purely on a missing `endTime` needs care in production, since it can't distinguish a genuinely in-progress task from one whose process crashed too abruptly to record its own completion — production overlap-prevention logic typically layers a reasonable staleness/timeout check on top of this basic query.
