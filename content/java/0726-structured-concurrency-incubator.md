---
card: java
gi: 726
slug: structured-concurrency-incubator
title: Structured concurrency (incubator)
---

## 1. What it is

**Java 19** (JEP 428) incubates **structured concurrency**: an API (`jdk.incubator.concurrent.StructuredTaskScope`) for treating a group of related concurrent subtasks as one unit of work with a single lifetime, rather than as independent threads whose fates must be tracked and joined manually. It builds directly on [virtual threads](0725-virtual-threads-preview.md) — each subtask typically runs on its own virtual thread — but its purpose is orthogonal: where virtual threads make it *cheap* to spawn many concurrent tasks, structured concurrency makes it *safe and easy to reason about* what happens when you do. The core rule is simple: a `StructuredTaskScope` cannot exit (its `close()` cannot return) until every subtask it forked has completed, one way or another — success, failure, or cancellation. Being an incubator API in Java 19, it requires `--add-modules jdk.incubator.concurrent` and was still evolving toward finalization.

## 2. Why & when

Traditional concurrent code that fires off several threads or `Future`s to do related work in parallel — call service A and service B concurrently, then combine their results — has a well-known set of failure modes that are easy to get wrong: if task A fails, does the code remember to cancel task B, or does B keep running to no purpose, wasting resources and possibly outliving the method that spawned it (a "thread leak")? If the calling thread is interrupted or times out, do the child tasks get interrupted too, or do they keep running in the background, detached from anything tracking them? Exceptions thrown in a background thread, and the coordination logic to correctly propagate, aggregate, or ignore them, tend to be hand-rolled ad hoc with `CompletableFuture.allOf`, manual `ExecutorService` bookkeeping, or raw `Thread` + shared state — all error-prone, and all difficult to get right consistently across a codebase. Structured concurrency solves this by enforcing, at the API level, that concurrent subtasks are *scoped*: they're forked within a block, and that block cannot complete until all subtasks are accounted for. This gives concurrent code the same reliable nesting and lifetime guarantees that structured *sequential* code has always had from `try`/`catch`/`finally` blocks — a subtask's lifetime is strictly bounded by the scope that created it, cancellation and error propagation are automatic rather than manually wired, and a debugger or thread dump can show the parent-child relationship between tasks clearly. Reach for `StructuredTaskScope` any time a method needs to run a small number of related, unrelated-in-implementation subtasks concurrently and must combine their results (or fail fast if one fails) before returning.

## 3. Core concept

```java
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Future<String> userTask  = scope.fork(() -> fetchUser(id));
    Future<String> orderTask = scope.fork(() -> fetchOrders(id));

    scope.join();           // wait for both to finish (or one to fail)
    scope.throwIfFailed();  // re-throw if either subtask threw

    return new Response(userTask.resultNow(), orderTask.resultNow());
} // scope.close() guarantees every forked subtask has terminated before this line finishes
```

`ShutdownOnFailure` is a policy: if any subtask fails, the scope cancels the others automatically, so no subtask outlives the failed operation.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A StructuredTaskScope forks child subtasks that run concurrently; the scope cannot exit until every subtask has completed, and a ShutdownOnFailure policy cancels remaining siblings the moment one subtask fails">
  <rect x="20" y="20" width="600" height="180" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">try (var scope = new StructuredTaskScope.ShutdownOnFailure())</text>

  <rect x="60" y="60" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="150" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">fork(fetchUser)</text>

  <rect x="400" y="60" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="490" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">fork(fetchOrders)</text>

  <text x="330" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">scope.join() — waits for BOTH to finish</text>
  <text x="330" y="165" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">if one throws, the other is cancelled automatically</text>
  <text x="330" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">scope cannot close() until both subtasks have terminated</text>
</svg>

The scope's own lifetime cannot end before every child task it started has ended, one way or another.

## 5. Runnable example

Scenario: an "aggregate results from two services" operation, growing from a basic two-task fan-out/fan-in, to a failure-propagating version where either subtask failing cancels its sibling and fails fast, to a version with a hard deadline that cancels all subtasks if the combined operation takes too long — the realistic shape of a backend endpoint calling multiple downstream services.

### Level 1 — Basic

```java
// File: ScopeBasic.java
// Run with --enable-preview --add-modules jdk.incubator.concurrent — Java 19 incubator.
import jdk.incubator.concurrent.StructuredTaskScope;
import java.util.concurrent.*;

public class ScopeBasic {
    static String fetchUser(int id) throws InterruptedException {
        Thread.sleep(50); // simulated network call
        return "user-" + id;
    }

    static String fetchOrders(int id) throws InterruptedException {
        Thread.sleep(70); // simulated network call
        return "orders-for-" + id;
    }

    public static void main(String[] args) throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            Future<String> userTask = scope.fork(() -> fetchUser(42));
            Future<String> orderTask = scope.fork(() -> fetchOrders(42));

            scope.join();
            scope.throwIfFailed();

            System.out.println("Combined: " + userTask.resultNow() + " + " + orderTask.resultNow());
        }
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview --add-modules jdk.incubator.concurrent ScopeBasic.java
java --enable-preview --add-modules jdk.incubator.concurrent ScopeBasic
```

Expected output:
```
Combined: user-42 + orders-for-42
```

### Level 2 — Intermediate

```java
// File: ScopeFailureIntermediate.java
// The SAME two-task fan-out, but now one subtask fails — demonstrating
// ShutdownOnFailure's automatic cancellation of the sibling task.
import jdk.incubator.concurrent.StructuredTaskScope;
import java.util.concurrent.*;

public class ScopeFailureIntermediate {
    static String fetchUser(int id) throws InterruptedException {
        Thread.sleep(200); // deliberately slow, so we can observe it get cancelled
        System.out.println("fetchUser finished (should NOT print if cancelled correctly)");
        return "user-" + id;
    }

    static String fetchOrders(int id) throws InterruptedException {
        Thread.sleep(30);
        throw new RuntimeException("orders service unavailable for id=" + id);
    }

    public static void main(String[] args) {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            Future<String> userTask = scope.fork(() -> fetchUser(42));
            Future<String> orderTask = scope.fork(() -> fetchOrders(42));

            scope.join();
            scope.throwIfFailed(); // this line throws, since orderTask failed
        } catch (Exception e) {
            System.out.println("Operation failed as expected: " + e.getCause().getMessage());
        }
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview --add-modules jdk.incubator.concurrent ScopeFailureIntermediate.java
java --enable-preview --add-modules jdk.incubator.concurrent ScopeFailureIntermediate
```

Expected output (the "fetchUser finished" line should NOT appear — it was cancelled):
```
Operation failed as expected: orders service unavailable for id=42
```

### Level 3 — Advanced

```java
// File: ScopeDeadlineAdvanced.java
// Adds a hard deadline via joinUntil — if the combined operation takes too
// long, ALL subtasks are cancelled together, the production-flavored
// pattern for enforcing a service-level timeout across fan-out calls.
import jdk.incubator.concurrent.StructuredTaskScope;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.concurrent.*;

public class ScopeDeadlineAdvanced {
    static String fetchFast(String name, long delayMs) throws InterruptedException {
        Thread.sleep(delayMs);
        return name + " completed in " + delayMs + "ms";
    }

    static String runWithDeadline(long deadlineMs, long... delaysMs) throws InterruptedException {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            Future<String>[] tasks = new Future[delaysMs.length];
            for (int i = 0; i < delaysMs.length; i++) {
                int idx = i;
                tasks[i] = scope.fork(() -> fetchFast("task-" + idx, delaysMs[idx]));
            }

            Instant deadline = Instant.now().plus(deadlineMs, ChronoUnit.MILLIS);
            try {
                scope.joinUntil(deadline);
            } catch (TimeoutException e) {
                return "TIMED OUT after " + deadlineMs + "ms — all subtasks cancelled";
            }
            scope.throwIfFailed();

            StringBuilder sb = new StringBuilder();
            for (Future<String> t : tasks) sb.append(t.resultNow()).append("; ");
            return sb.toString();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println(runWithDeadline(500, 50, 80, 60)); // all fast enough
        System.out.println(runWithDeadline(100, 50, 300, 60)); // one too slow -> timeout
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview --add-modules jdk.incubator.concurrent ScopeDeadlineAdvanced.java
java --enable-preview --add-modules jdk.incubator.concurrent ScopeDeadlineAdvanced
```

Expected output:
```
task-0 completed in 50ms; task-1 completed in 80ms; task-2 completed in 60ms; 
TIMED OUT after 100ms — all subtasks cancelled
```

## 6. Walkthrough

1. `ScopeDeadlineAdvanced.main` calls `runWithDeadline` twice: once with all delays comfortably under the deadline, once with one delay (`300ms`) that will exceed the `100ms` deadline.
2. Inside `runWithDeadline`, a `StructuredTaskScope.ShutdownOnFailure` is opened, and `scope.fork(...)` is called once per delay — each call immediately starts a new subtask (backed by a virtual thread) and returns a `Future<String>` that will hold its eventual result.
3. `scope.joinUntil(deadline)` is the key structural difference from the earlier levels' plain `scope.join()`: it waits for all forked subtasks to complete, but only until the given `Instant` — if the deadline passes first, it throws `TimeoutException` instead of returning normally.
4. For the first call (`runWithDeadline(500, 50, 80, 60)`), all three subtasks finish well within 500ms, so `joinUntil` returns normally, `throwIfFailed()` finds nothing to report, and the loop collects each `Future`'s result via `resultNow()` (safe to call here specifically because `join`/`joinUntil` already guaranteed every subtask has terminated).
5. For the second call (`runWithDeadline(100, 50, 300, 60)`), `task-0` and `task-2` finish quickly, but `task-1` is still sleeping when the 100ms deadline arrives. `joinUntil` throws `TimeoutException` — and, critically, before that exception propagates out of the `try`-with-resources block, the `StructuredTaskScope`'s `close()` method (invoked automatically) forcibly interrupts and cancels **every** subtask that hasn't finished yet, including `task-1`, which never gets to complete its `Thread.sleep(300)`.
6. This is the core guarantee structured concurrency provides that manual `Future`/`ExecutorService` bookkeeping does not automatically give you: the timeout on the *scope* is a timeout on the *entire group* of subtasks together, and no subtask can outlive that group's failure — there's no possibility of `task-1` continuing to run silently in the background after `runWithDeadline` has already returned its `"TIMED OUT"` message to the caller.
7. In the earlier `ScopeFailureIntermediate` example, the same underlying mechanism produces a different visible effect: `fetchOrders` throwing an exception triggers `ShutdownOnFailure`'s policy immediately, canceling `fetchUser`'s still-running virtual thread before its artificially slow `200ms` sleep completes — which is exactly why the `"fetchUser finished"` line never prints.

```
runWithDeadline(100, 50, 300, 60)
      |
      v
fork task-0 (50ms)   fork task-1 (300ms)   fork task-2 (60ms)
      |                     |                     |
   finishes            still running          finishes
   at 50ms                                    at 60ms
      |                     |                     |
      +----- scope.joinUntil(deadline @ 100ms) ----+
                             |
                     deadline passes (100ms)
                             |
                             v
                    TimeoutException thrown
                             |
                             v
              scope.close() cancels task-1 (still running)
                             |
                             v
                  "TIMED OUT ... all subtasks cancelled"
```

## 7. Gotchas & takeaways

> This is an **incubator API** (`jdk.incubator.concurrent`) in Java 19, layered on the also-preview [virtual threads](0725-virtual-threads-preview.md) feature — it requires both `--enable-preview` and `--add-modules jdk.incubator.concurrent`, and its exact class and method names (`StructuredTaskScope`, `ShutdownOnFailure`) continued to evolve — including package relocation to `java.util.concurrent` — before eventual finalization in later JDKs.
- `Future.resultNow()` (used throughout these examples) is only safe to call **after** `scope.join()`/`joinUntil()` has returned successfully — calling it on a subtask that hasn't completed throws `IllegalStateException`; the structured-concurrency contract is what makes calling it immediately after `join()` provably safe.
- `ShutdownOnFailure` is one policy among several — `StructuredTaskScope.ShutdownOnSuccess` is the mirror-image policy for "race several redundant tasks, take the first successful result, cancel the rest," useful for calling the same operation against multiple redundant replicas and using whichever answers first.
- The scope's `close()` — called automatically by `try`-with-resources — is what enforces the "no subtask can outlive its scope" guarantee; a `StructuredTaskScope` opened without a `try`-with-resources block (or one from which `close()` is never called) loses this safety guarantee entirely, so always use it as a resource.
- Subtasks forked within a scope automatically inherit `ScopedValue`/thread-local-like context propagation in the finalized version of this API — even in this Java 19 incubator round, the design's intent is that a subtask feels like "the same logical operation, just running concurrently," not an unrelated detached thread.
- Structured concurrency and virtual threads are complementary, not the same feature: virtual threads make forking many concurrent tasks cheap; `StructuredTaskScope` makes managing their combined lifetime, error propagation, and cancellation safe and automatic.
