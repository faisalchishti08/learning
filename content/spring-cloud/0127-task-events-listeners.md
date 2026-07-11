---
card: spring-cloud
gi: 127
slug: task-events-listeners
title: "Task events & listeners"
---

## 1. What it is

Spring Cloud Task publishes Spring application events at key lifecycle points — `TaskExecutionListener`'s `onTaskStartup`/`onTaskEnd`/`onTaskFailed` callbacks (and, when a message broker binding is configured, the same events can be published as actual messages onto a stream) — letting application code react to a task's own lifecycle transitions (send a notification on failure, trigger a downstream process on successful completion) without polling the `TaskExecution` table for changes.

```java
@Component
class TaskNotifier implements TaskExecutionListener {
    public void onTaskEnd(TaskExecution taskExecution) {
        System.out.println("task '" + taskExecution.getTaskName() + "' finished, exitCode=" + taskExecution.getExitCode());
    }
    public void onTaskFailed(TaskExecution taskExecution, Throwable throwable) {
        alertingService.notifyFailure(taskExecution.getTaskName(), throwable);
    }
}
```

```properties
spring.cloud.task.events.enabled=true
spring.cloud.stream.bindings.task-events.destination=task-events-topic
```

## 2. Why & when

The `TaskExplorer` query API from the previous card is pull-based — something has to actively query it to notice a task finished or failed, which means either polling on a timer (adding latency between the actual event and its detection) or building custom logic to watch for changes. Task events flip this to a push-based model: `TaskExecutionListener` callbacks fire synchronously, in-process, at the exact moment a lifecycle transition happens, and (when stream bindings are configured) the same transitions are additionally published as messages onto a broker, letting entirely separate applications react to a task's lifecycle in near-real-time without needing direct database access to the `TaskExecution` table at all.

Reach for task events when:

- Reacting immediately to a task's completion or failure matters — sending an alert the moment a critical batch job fails, or triggering a downstream process the moment an import task successfully completes, both benefit from push-based notification over polling latency.
- The reacting logic lives in-process, within the same application as the task itself — `TaskExecutionListener` callbacks are the direct, lightweight mechanism for this, requiring no message broker at all.
- The reacting logic lives in a *separate* application or service — publishing task events onto a Spring Cloud Stream binding lets other services subscribe to a task's lifecycle transitions as ordinary stream messages, using the same event-driven patterns established in earlier Messaging cards.

## 3. Core concept

```
 task lifecycle:
   STARTUP  -> onTaskStartup(taskExecution) fires
   ... task does its work ...
   SUCCESS  -> onTaskEnd(taskExecution) fires
   OR
   FAILURE  -> onTaskFailed(taskExecution, throwable) fires, THEN onTaskEnd(taskExecution) still fires too

 in-process reaction:               TaskExecutionListener beans -- called SYNCHRONOUSLY, in the SAME JVM
 cross-process reaction (optional): the SAME transitions ALSO published as messages, if stream bindings are configured
   -> any OTHER application subscribed to that stream destination reacts independently
```

`onTaskFailed` and `onTaskEnd` are not mutually exclusive — a failed task still triggers `onTaskEnd` afterward, so listener code needs to handle both callbacks deliberately rather than assuming only one fires per execution.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A task lifecycle transition triggers an in process listener callback synchronously and optionally the same transition is published as a message onto a stream destination letting a separate application react independently">
  <rect x="20" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="95" y="44" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">task lifecycle event</text>

  <rect x="250" y="20" width="180" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="340" y="44" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">TaskExecutionListener (in-process)</text>

  <rect x="250" y="100" width="180" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="340" y="124" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">stream destination (optional)</text>

  <rect x="480" y="100" width="140" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="550" y="124" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">other application</text>

  <defs><marker id="a127" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="170" y1="40" x2="250" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a127)"/>
  <line x1="130" y1="60" x2="300" y2="100" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3" marker-end="url(#a127)"/>
  <line x1="430" y1="120" x2="480" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a127)"/>
</svg>

One lifecycle transition, two possible reaction paths — always the in-process listener, optionally also a broker-mediated broadcast to other applications.

## 5. Runnable example

The scenario: model `TaskExecutionListener`-style callbacks firing on task lifecycle transitions, first in-process only, then extended to also publish onto a simulated stream for a separate consuming application. Start with a single in-process listener reacting to success and failure, then add multiple listeners (mirroring several concerns reacting independently to the same transitions), then add stream-style publishing so a separate, decoupled component reacts too.

### Level 1 — Basic

A single in-process listener reacting to task success and failure via callback methods.

```java
public class TaskEventsLevel1 {
    interface TaskExecutionListener {
        void onTaskEnd(String taskName, int exitCode);
        void onTaskFailed(String taskName, String errorMessage);
    }

    static class ConsoleNotifier implements TaskExecutionListener {
        public void onTaskEnd(String taskName, int exitCode) {
            System.out.println("[listener] task '" + taskName + "' ended, exitCode=" + exitCode);
        }
        public void onTaskFailed(String taskName, String errorMessage) {
            System.out.println("[listener] task '" + taskName + "' FAILED: " + errorMessage);
        }
    }

    static void runTask(String taskName, Runnable work, TaskExecutionListener listener) {
        try {
            work.run();
            listener.onTaskEnd(taskName, 0);
        } catch (RuntimeException e) {
            listener.onTaskFailed(taskName, e.getMessage()); // onTaskFailed fires FIRST
            listener.onTaskEnd(taskName, 1);                  // onTaskEnd STILL fires afterward
        }
    }

    public static void main(String[] args) {
        TaskExecutionListener listener = new ConsoleNotifier();

        runTask("import-orders", () -> System.out.println("  ... import succeeds ..."), listener);
        runTask("cleanup-records", () -> { throw new RuntimeException("disk full"); }, listener);
    }
}
```

How to run: `java TaskEventsLevel1.java`

The failed `"cleanup-records"` run triggers *both* `onTaskFailed` and `onTaskEnd`, in that order — confirming both callbacks fire for a failure, not just one, exactly matching the real `TaskExecutionListener` contract's behavior.

### Level 2 — Intermediate

Add multiple listeners reacting independently to the same lifecycle transitions, mirroring several unrelated application concerns (logging, alerting) both observing the same task.

```java
import java.util.*;

public class TaskEventsLevel2 {
    interface TaskExecutionListener {
        void onTaskEnd(String taskName, int exitCode);
        void onTaskFailed(String taskName, String errorMessage);
    }

    static class LoggingListener implements TaskExecutionListener {
        public void onTaskEnd(String taskName, int exitCode) { System.out.println("[log] " + taskName + " ended, exitCode=" + exitCode); }
        public void onTaskFailed(String taskName, String errorMessage) { System.out.println("[log] " + taskName + " FAILED: " + errorMessage); }
    }

    static class AlertingListener implements TaskExecutionListener {
        public void onTaskEnd(String taskName, int exitCode) { /* alerting only cares about FAILURES, not every end */ }
        public void onTaskFailed(String taskName, String errorMessage) {
            System.out.println("[ALERT] paging on-call for '" + taskName + "': " + errorMessage);
        }
    }

    static void runTask(String taskName, Runnable work, List<TaskExecutionListener> listeners) {
        try {
            work.run();
            for (TaskExecutionListener l : listeners) l.onTaskEnd(taskName, 0);
        } catch (RuntimeException e) {
            for (TaskExecutionListener l : listeners) l.onTaskFailed(taskName, e.getMessage());
            for (TaskExecutionListener l : listeners) l.onTaskEnd(taskName, 1);
        }
    }

    public static void main(String[] args) {
        List<TaskExecutionListener> listeners = List.of(new LoggingListener(), new AlertingListener());

        runTask("cleanup-records", () -> { throw new RuntimeException("disk full"); }, listeners);
    }
}
```

How to run: `java TaskEventsLevel2.java`

Both `LoggingListener` and `AlertingListener` react to the same single failure independently — `LoggingListener` logs it, `AlertingListener` pages on-call, and each listener's own `onTaskEnd`/`onTaskFailed` implementations decide independently what (if anything) to actually do with a given callback, exactly mirroring how several unrelated `@Component` beans implementing `TaskExecutionListener` in a real application would each react to the same task lifecycle transitions according to their own separate concerns.

### Level 3 — Advanced

Add stream-style publishing: the same lifecycle transitions are additionally published onto a simulated message stream, letting an entirely separate, decoupled "application" (modeled as a subscriber with no direct reference to the task-running code) react independently.

```java
import java.util.*;
import java.util.function.Consumer;

public class TaskEventsLevel3 {
    record TaskEvent(String taskName, String type, int exitCode, String errorMessage) {}

    interface TaskExecutionListener {
        void onTaskEnd(String taskName, int exitCode);
        void onTaskFailed(String taskName, String errorMessage);
    }

    // models publishing task events onto a Spring Cloud Stream destination
    static class StreamPublishingListener implements TaskExecutionListener {
        List<Consumer<TaskEvent>> subscribers = new ArrayList<>();
        void subscribe(Consumer<TaskEvent> subscriber) { subscribers.add(subscriber); }

        public void onTaskEnd(String taskName, int exitCode) {
            publish(new TaskEvent(taskName, "END", exitCode, null));
        }
        public void onTaskFailed(String taskName, String errorMessage) {
            publish(new TaskEvent(taskName, "FAILED", -1, errorMessage));
        }
        void publish(TaskEvent event) {
            for (Consumer<TaskEvent> subscriber : subscribers) subscriber.accept(event); // fan-out, like a real broker
        }
    }

    static void runTask(String taskName, Runnable work, TaskExecutionListener listener) {
        try {
            work.run();
            listener.onTaskEnd(taskName, 0);
        } catch (RuntimeException e) {
            listener.onTaskFailed(taskName, e.getMessage());
            listener.onTaskEnd(taskName, 1);
        }
    }

    public static void main(String[] args) {
        StreamPublishingListener streamListener = new StreamPublishingListener();

        // a SEPARATE, decoupled "application" -- has NO direct reference to runTask or the task itself
        streamListener.subscribe(event -> {
            if (event.type().equals("FAILED")) {
                System.out.println("[downstream service] received FAILED event for '" + event.taskName() + "': " + event.errorMessage());
            }
        });

        runTask("import-orders", () -> System.out.println("  ... import succeeds ..."), streamListener);
        runTask("cleanup-records", () -> { throw new RuntimeException("disk full"); }, streamListener);
    }
}
```

How to run: `java TaskEventsLevel3.java`

The subscriber lambda registered via `streamListener.subscribe(...)` reacts only to the `"cleanup-records"` failure, correctly ignoring the successful `"import-orders"` `END` event (its own filtering logic checks `event.type().equals("FAILED")`) — this subscriber models a completely separate downstream application that has no direct code-level reference to `runTask` or the task-running logic at all; it only ever sees `TaskEvent` messages arriving through `publish`, exactly mirroring how a real Spring Cloud Stream consumer in an entirely different deployed service reacts to task lifecycle events published onto a shared broker destination.

## 6. Walkthrough

Trace the `"cleanup-records"` failure's full event path in Level 3.

1. `runTask("cleanup-records", () -> { throw ... }, streamListener)` calls `work.run()`, which throws `RuntimeException("disk full")`, caught by the surrounding `catch` block.
2. `listener.onTaskFailed("cleanup-records", "disk full")` is called on `streamListener` — inside, this constructs `new TaskEvent("cleanup-records", "FAILED", -1, "disk full")` and calls `publish(event)`.
3. `publish` iterates `subscribers` (currently one entry, the lambda registered in `main`), calling `subscriber.accept(event)` — inside the lambda, `event.type().equals("FAILED")` evaluates `true`, so it prints the downstream-service reaction line.
4. Back in `runTask`'s `catch` block, `listener.onTaskEnd("cleanup-records", 1)` is called next — this constructs `new TaskEvent("cleanup-records", "END", 1, null)` and again calls `publish`, again reaching the same subscriber lambda, but this time `event.type().equals("FAILED")` evaluates `false` (the type is `"END"`, not `"FAILED"`), so the lambda's `if` body doesn't execute, and nothing is printed for this second event.
5. The net effect: exactly one line of output from the subscriber, for the `FAILED` event specifically — the subscriber received *both* events (`FAILED` then `END`) through the identical `publish`/`accept` mechanism, but its own internal filtering logic decided which one was actually worth reacting to, exactly as a real downstream Spring Cloud Stream consumer would filter incoming task-event messages by type according to its own specific concerns.

```
runTask("cleanup-records", failingWork, streamListener):
  work.run() throws "disk full"
  onTaskFailed -> publish(TaskEvent(FAILED, "disk full")) -> subscriber.accept -> type=="FAILED"? YES -> prints reaction
  onTaskEnd    -> publish(TaskEvent(END, exitCode=1))      -> subscriber.accept -> type=="FAILED"? NO  -> no output
```

## 7. Gotchas & takeaways

> **Gotcha:** `onTaskFailed` and `onTaskEnd` both fire for a failed task execution, in that order — a listener implementation that only handles `onTaskEnd` and assumes `exitCode != 0` alone is sufficient to detect failure will work, but a listener that only implements `onTaskFailed` and forgets `onTaskEnd` still fires afterward (potentially with logic that assumes success) risks double-counting or mishandling the failure case. Deliberately deciding what each callback should (and shouldn't) do, given both will be called for a failure, avoids this class of bug.

- Task events flip `TaskExplorer`'s pull-based query model to a push-based one — listener callbacks fire synchronously at the exact moment of a lifecycle transition, eliminating the detection latency inherent to polling.
- Multiple `TaskExecutionListener` beans can coexist, each reacting to the same lifecycle transitions according to its own independent concern (logging, alerting, metrics) — Spring simply invokes every registered listener bean for each transition, with no listener needing awareness of any other.
- Stream-published task events extend this reactivity beyond the single application's own JVM, letting entirely separate, decoupled services react to a task's lifecycle without any direct code-level coupling to the task-running application — built on the same Spring Cloud Stream mechanisms covered in earlier Messaging cards.
- This card closes the Spring Cloud Task trio: `@EnableTask` records execution history (an earlier card), `TaskExplorer` queries it (the previous card), and task events/listeners react to it in near-real-time — together giving short-lived, batch-style applications the observability and reactivity long-running services get from their own monitoring stacks.
