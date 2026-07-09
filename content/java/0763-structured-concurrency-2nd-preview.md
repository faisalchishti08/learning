---
card: java
gi: 763
slug: structured-concurrency-2nd-preview
title: Structured concurrency (2nd preview)
---

## 1. What it is

**Java 22** (JEP 462) is the **second preview** of [structured concurrency](0754-structured-concurrency-preview.md), continuing from its first preview round in Java 21 (and two earlier incubator rounds before that). The core model — `StructuredTaskScope`, `fork`/`join`, subtasks that cannot outlive their enclosing scope, and the `ShutdownOnFailure`/`ShutdownOnSuccess` policies — carries forward unchanged. This round's refinements focus on tightening how a scope's subtasks interact with **nested scopes** (a subtask that itself opens another `StructuredTaskScope`) and clarifying timeout-based cancellation, so a scope can be told to shut itself down automatically after a fixed duration rather than requiring the calling code to implement that with a separate timer.

## 2. Why & when

Real fan-out/fan-in workloads are rarely a single flat level of concurrency — a request handler might fork three subtasks, one of which itself needs to fork two more subtasks to satisfy its own work, forming a small tree of nested scopes. This round's refinements come from exactly that kind of feedback: ensuring a nested `StructuredTaskScope`'s cancellation and failure propagation compose predictably with its parent scope's, so a failure three levels deep in a nested tree of scopes reliably and promptly cancels every sibling and ancestor scope waiting on it, rather than only the immediately enclosing one. The timeout refinement addresses another common real need directly: a fan-out call to several downstream services should have an overall deadline, not just individual failure-triggered cancellation — before this, achieving that meant a hand-rolled timer racing against `scope.join()`, adding complexity to what should be a simple, common requirement.

## 3. Core concept

```java
import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.StructuredTaskScope;

try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    var inventory = scope.fork(() -> callService("inventory"));
    var pricing = scope.fork(() -> callService("pricing"));

    scope.joinUntil(Instant.now().plus(Duration.ofSeconds(2))); // overall deadline
    scope.throwIfFailed();

    combine(inventory.get(), pricing.get());
}
```

`joinUntil(...)` waits for every subtask to finish, for a failure, or for the deadline to pass — whichever comes first — cancelling any still-running subtasks if the deadline is reached.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A structured task scope can now join with a deadline, and nested scopes propagate cancellation and failure consistently up and down the tree of scopes">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">scope.joinUntil(deadline) — subtasks race against an overall time limit</text>

  <rect x="60" y="90" width="200" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="160" y="120" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">outer scope</text>

  <rect x="300" y="90" width="280" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="440" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">subtask opens nested scope</text>
  <text x="440" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">failure/cancellation propagates consistently</text>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Refinements target multi-level fan-out and deadline-bounded fan-out alike</text>
</svg>

*A deadline and consistent nested-scope propagation round out the fan-out/fan-in model.*

## 5. Runnable example

Scenario: a dashboard fetch with an overall deadline, growing from unconditional join into deadline-bounded, nested-scope fan-out.

### Level 1 — Basic

```java
import java.time.Duration;
import java.util.concurrent.StructuredTaskScope;

public class DashboardNoDeadline {
    static String fetchUser() throws InterruptedException {
        Thread.sleep(Duration.ofMillis(100));
        return "user:ada";
    }

    static String fetchOrders() throws InterruptedException {
        Thread.sleep(Duration.ofMillis(150));
        return "orders:[42,43]";
    }

    public static void main(String[] args) throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            var user = scope.fork(DashboardNoDeadline::fetchUser);
            var orders = scope.fork(DashboardNoDeadline::fetchOrders);
            scope.join();
            scope.throwIfFailed();
            System.out.println(user.get() + " / " + orders.get());
        }
    }
}
```

**How to run:** `java --enable-preview --source 22 --add-modules jdk.incubator.concurrent DashboardNoDeadline.java` (JDK 22+; exact flags depend on your build).

This is the unconditional-join style from the first preview round: `scope.join()` waits as long as it takes for both subtasks, with no overall time limit.

### Level 2 — Intermediate

```java
import java.time.*;
import java.util.concurrent.*;

public class DashboardDeadline {
    static String fetchUser() throws InterruptedException {
        Thread.sleep(Duration.ofMillis(100));
        return "user:ada";
    }

    static String fetchOrders() throws InterruptedException {
        Thread.sleep(Duration.ofMillis(3000)); // deliberately slow
        return "orders:[42,43]";
    }

    public static void main(String[] args) throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            var user = scope.fork(DashboardDeadline::fetchUser);
            var orders = scope.fork(DashboardDeadline::fetchOrders);

            try {
                scope.joinUntil(Instant.now().plus(Duration.ofSeconds(1)));
                scope.throwIfFailed();
                System.out.println(user.get() + " / " + orders.get());
            } catch (TimeoutException e) {
                System.out.println("dashboard fetch timed out after 1s");
            }
        }
    }
}
```

**How to run:** `java --enable-preview --source 22 --add-modules jdk.incubator.concurrent DashboardDeadline.java`.

The real-world concern added: `fetchOrders` deliberately takes 3 seconds, but `scope.joinUntil(...)` enforces a 1-second overall deadline — when the deadline passes before both subtasks finish, `joinUntil` throws `TimeoutException`, and the scope's try-with-resources cleanup ensures the still-running `fetchOrders` subtask is cancelled rather than left running past the scope's lifetime.

### Level 3 — Advanced

```java
import java.time.*;
import java.util.concurrent.*;

public class DashboardNested {
    static String fetchUser() throws InterruptedException {
        Thread.sleep(Duration.ofMillis(100));
        return "user:ada";
    }

    // This "subtask" itself fans out to two further nested subtasks.
    static String fetchOrdersWithDetails() throws Exception {
        try (var nested = new StructuredTaskScope.ShutdownOnFailure()) {
            var orderIds = nested.fork(() -> {
                Thread.sleep(Duration.ofMillis(80));
                return "orders:[42,43]";
            });
            var orderDetails = nested.fork(() -> {
                Thread.sleep(Duration.ofMillis(120));
                return "details:[shipped,pending]";
            });
            nested.join();
            nested.throwIfFailed();
            return orderIds.get() + " " + orderDetails.get();
        }
    }

    public static void main(String[] args) throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            var user = scope.fork(DashboardNested::fetchUser);
            var orders = scope.fork(DashboardNested::fetchOrdersWithDetails);

            scope.joinUntil(Instant.now().plus(Duration.ofSeconds(2)));
            scope.throwIfFailed();

            System.out.println(user.get() + " / " + orders.get());
        }
    }
}
```

**How to run:** `java --enable-preview --source 22 --add-modules jdk.incubator.concurrent DashboardNested.java`.

This adds the production-flavored hard case: `fetchOrdersWithDetails` is itself a subtask of the **outer** scope, but it opens its **own nested** `StructuredTaskScope` to fan out into two further subtasks — a small tree of scopes two levels deep, with the outer scope's deadline (`joinUntil`, 2 seconds) still bounding the entire tree's total execution time, and failure at any level able to propagate correctly to whichever ancestor scope is waiting on it.

## 6. Walkthrough

Tracing `DashboardNested.main`:

1. `main` opens the outer scope and forks two subtasks: `fetchUser` (a leaf task, sleeps 100ms) and `fetchOrdersWithDetails` (which will itself open a nested scope).
2. Inside `fetchOrdersWithDetails`, a **nested** `StructuredTaskScope.ShutdownOnFailure` opens and forks two further subtasks: one sleeping 80ms, one sleeping 120ms.
3. `nested.join()` blocks until both of *these* inner subtasks complete — after roughly 120ms (the slower of the two), both finish successfully, `nested.throwIfFailed()` finds nothing to re-throw, and `fetchOrdersWithDetails` returns its combined string. The nested scope's try-with-resources block closes cleanly at this point, having waited for both its own subtasks.
4. Back at the outer level, `fetchOrdersWithDetails` (as a subtask of the outer scope) completes around 120ms after starting; `fetchUser` completed earlier, around 100ms.
5. `scope.joinUntil(Instant.now().plus(Duration.ofSeconds(2)))` was waiting on both outer subtasks; since both finish well within the 2-second deadline, `joinUntil` returns normally (no `TimeoutException`).
6. `scope.throwIfFailed()` finds no failures, and `main` prints the combined result from both `user.get()` and `orders.get()`.

Expected output:
```
user:ada / orders:[42,43] details:[shipped,pending]
```

If `fetchOrdersWithDetails`'s nested scope had instead taken longer than the outer scope's 2-second deadline, `joinUntil` at the outer level would throw `TimeoutException` before `orders.get()` is ever reached — and the outer scope's cleanup would cancel the still-running `fetchOrdersWithDetails` subtask, which in turn (through its own try-with-resources) would cancel its nested subtasks too, demonstrating cancellation propagating consistently down through a multi-level tree of scopes.

## 7. Gotchas & takeaways

> **Gotcha:** `joinUntil`'s deadline bounds `join`'s wait, not each individual subtask's execution — a subtask that ignores interruption (see the equivalent caveat in [structured concurrency (preview)](0754-structured-concurrency-preview.md)) can still keep running past the deadline in the background even after `joinUntil` has thrown `TimeoutException` and the calling code has moved on, until the scope's own cleanup forces the issue. Cancellation-responsive subtask code remains essential, deadline or not.

- Second preview round, Java 22 — refines nested-scope propagation and adds deadline-based joining (`joinUntil`) on top of the Java 21 preview's core model.
- `joinUntil(deadline)` throws `TimeoutException` if the deadline passes before all subtasks finish or one fails — giving fan-out/fan-in code a built-in overall time limit without a hand-rolled timer.
- Nested `StructuredTaskScope`s (a subtask that itself opens a scope) propagate cancellation and failure consistently across the whole tree, not just one level.
- Still a preview — continues converging from the Java 19/20 incubator rounds and Java 21's first preview toward eventual standardization.
- Combine with [scoped values (2nd preview)](0764-scoped-values-2nd-preview.md) for context that needs to be visible across every level of a nested scope tree, not just a single flat fan-out.
