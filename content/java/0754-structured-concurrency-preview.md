---
card: java
gi: 754
slug: structured-concurrency-preview
title: Structured concurrency (preview)
---

## 1. What it is

**Java 21** (JEP 453) is the **first preview** round of [structured concurrency](0736-structured-concurrency-2nd-incubator.md), following two incubator rounds in Java 19 and Java 20. `StructuredTaskScope` remains the core type: it lets a group of related concurrent subtasks be treated as a single unit of work, forked via `scope.fork(...)`, and guaranteed not to outlive the scope that created them — `scope.join()` blocks until every subtask completes (or a shutdown policy like `ShutdownOnFailure` cancels the rest early), and the scope cannot be closed while any subtask is still running. Moving to preview (rather than incubator) means it still requires `--enable-preview`, but the API is now closer to its eventual final shape.

## 2. Why & when

"Unstructured" concurrency — spawning threads or submitting tasks to an `ExecutorService` and letting them run independently of the code that created them — has a well-known failure mode: if the parent code returns, throws, or is cancelled, nothing automatically stops the child tasks it spawned, which can keep running, keep holding resources, and keep able to fail in ways nobody is watching for anymore. Structured concurrency borrows a discipline from structured *sequential* programming (where a block's control flow can't jump past its own closing brace) and applies it to concurrency: a `StructuredTaskScope` behaves like a block — subtasks forked inside it cannot outlive it, errors in any subtask are visible to the code that opened the scope, and cancellation naturally propagates to still-running siblings when using a policy like `ShutdownOnFailure`. This preview round, following the incubator rounds, is where the design gets tested more broadly ahead of standardization — the fundamentals (the try-with-resources-based scope, the two built-in shutdown policies, `fork`/`join`) remain what earlier incubator rounds established, with the API now under closer scrutiny for its eventual permanent form.

## 3. Core concept

```java
import java.util.concurrent.StructuredTaskScope;

try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    var user = scope.fork(() -> fetchUser());
    var orders = scope.fork(() -> fetchOrders());

    scope.join();           // wait for both, or stop early if either fails
    scope.throwIfFailed();  // re-throw the first failure, if any

    combine(user.get(), orders.get());
} // scope closes here — guaranteed no subtask outlives this block
```

If either `fetchUser()` or `fetchOrders()` throws, `ShutdownOnFailure` cancels the other subtask immediately rather than waiting for it to finish pointlessly.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A StructuredTaskScope forks subtasks that cannot outlive the scope; join waits for completion or early cancellation via a shutdown policy, and the scope closes only once every subtask is done">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">try (var scope = new StructuredTaskScope.ShutdownOnFailure()) { ... }</text>

  <rect x="60" y="80" width="220" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="170" y="110" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">fork(fetchUser)</text>
  <rect x="360" y="80" width="220" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="470" y="110" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">fork(fetchOrders)</text>

  <rect x="140" y="150" width="360" height="36" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="173" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">scope.join() — one subtask failing cancels the other, never leaked</text>
</svg>

*Subtasks are bounded by the scope's lifetime, and failures propagate — no orphaned concurrent work.*

## 5. Runnable example

Scenario: fetching a user profile and their recent orders concurrently to build a dashboard response, growing from sequential calls to a full structured-concurrency fan-out/fan-in.

### Level 1 — Basic

```java
import java.time.Duration;

public class DashboardSequential {
    static String fetchUser() throws InterruptedException {
        Thread.sleep(Duration.ofMillis(100));
        return "user:ada";
    }

    static String fetchOrders() throws InterruptedException {
        Thread.sleep(Duration.ofMillis(150));
        return "orders:[42,43]";
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.nanoTime();
        String user = fetchUser();
        String orders = fetchOrders();
        System.out.println(user + " / " + orders);
        System.out.printf("elapsed: %.0fms%n", (System.nanoTime() - start) / 1e6);
    }
}
```

**How to run:** `java DashboardSequential.java` (JDK 21+).

This calls both fetches one after another — total time is roughly 100ms + 150ms = 250ms, even though the two calls have no dependency on each other and could run at the same time.

### Level 2 — Intermediate

```java
import java.time.Duration;
import java.util.concurrent.*;

public class DashboardStructured {
    static String fetchUser() throws InterruptedException {
        Thread.sleep(Duration.ofMillis(100));
        return "user:ada";
    }

    static String fetchOrders() throws InterruptedException {
        Thread.sleep(Duration.ofMillis(150));
        return "orders:[42,43]";
    }

    public static void main(String[] args) throws Exception {
        long start = System.nanoTime();
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            var user = scope.fork(DashboardStructured::fetchUser);
            var orders = scope.fork(DashboardStructured::fetchOrders);

            scope.join();
            scope.throwIfFailed();

            System.out.println(user.get() + " / " + orders.get());
        }
        System.out.printf("elapsed: %.0fms%n", (System.nanoTime() - start) / 1e6);
    }
}
```

**How to run:** `java --enable-preview --source 21 --add-modules jdk.incubator.concurrent DashboardStructured.java` (Java 21's preview status for this feature still ships under the incubator module name in some builds — check your exact JDK build's required flags).

The real-world concern added: both fetches run **concurrently** as forked subtasks, so the total elapsed time drops to roughly 150ms (the slower of the two), not the sum of both — and if either subtask throws, `ShutdownOnFailure` ensures the other is cancelled rather than left running to no purpose.

### Level 3 — Advanced

```java
import java.time.Duration;
import java.util.concurrent.*;

public class DashboardAdvanced {
    static String fetchUser(boolean fail) throws InterruptedException {
        Thread.sleep(Duration.ofMillis(100));
        if (fail) throw new RuntimeException("user service unavailable");
        return "user:ada";
    }

    static String fetchOrders() throws InterruptedException {
        Thread.sleep(Duration.ofMillis(500)); // deliberately slow, to observe early cancellation
        return "orders:[42,43]";
    }

    static String buildDashboard(boolean simulateUserFailure) throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            var user = scope.fork(() -> fetchUser(simulateUserFailure));
            var orders = scope.fork(DashboardAdvanced::fetchOrders);

            scope.join();
            scope.throwIfFailed(RuntimeException::new);

            return user.get() + " / " + orders.get();
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println(buildDashboard(false));

        long start = System.nanoTime();
        try {
            buildDashboard(true);
        } catch (RuntimeException e) {
            double elapsed = (System.nanoTime() - start) / 1e6;
            System.out.printf("failed fast after %.0fms: %s%n", elapsed, e.getCause().getMessage());
        }
    }
}
```

**How to run:** `java --enable-preview --source 21 --add-modules jdk.incubator.concurrent DashboardAdvanced.java`.

This adds the production-flavored hard case: `fetchOrders` is deliberately slow (500ms) while `fetchUser` can be made to fail quickly (after 100ms). When it does fail, `ShutdownOnFailure` cancels the still-running `fetchOrders` subtask immediately rather than waiting the full 500ms — demonstrating the core value proposition of structured concurrency's failure handling: a failing sibling doesn't leave the healthy ones running to no purpose.

## 6. Walkthrough

Tracing `buildDashboard(true)` (the failing case):

1. The scope opens, and `scope.fork(() -> fetchUser(true))` and `scope.fork(DashboardAdvanced::fetchOrders)` both start immediately as separate subtasks (each on its own virtual thread).
2. `fetchOrders` begins sleeping for 500ms. `fetchUser(true)` begins sleeping for 100ms.
3. After roughly 100ms, `fetchUser`'s sleep ends and it throws `RuntimeException("user service unavailable")`.
4. Because the scope uses `ShutdownOnFailure`, this failure triggers the scope's shutdown policy **immediately**: the still-sleeping `fetchOrders` subtask is signaled for cancellation (its thread is interrupted) rather than being left to run its full 500ms.
5. `scope.join()`, which was blocking until this point, returns once shutdown has been triggered and all subtasks have reached a terminal state (including the now-cancelled `fetchOrders`).
6. `scope.throwIfFailed(RuntimeException::new)` sees that a subtask failed and re-throws — wrapping the original failure using the supplied factory — propagating it out of `buildDashboard` before `user.get()` or `orders.get()` are ever called.
7. Back in `main`, the `catch (RuntimeException e)` block catches this, and the elapsed time printed is close to 100ms (roughly when `fetchUser` failed), not 500ms (when `fetchOrders` would otherwise have finished) — the concrete, timed proof that cancellation propagated to the sibling subtask rather than letting it run to completion uselessly.

Expected output shape:
```
user:ada / orders:[42,43]
failed fast after 10Xms: user service unavailable
```

## 7. Gotchas & takeaways

> **Gotcha:** structured concurrency's guarantee is about **lifetime containment**, not about magically making cancellation instantaneous — a subtask's code still needs to be cancellation-responsive (checking `Thread.interrupted()`, or performing interruptible blocking operations like `Thread.sleep`) for `ShutdownOnFailure` to actually stop it promptly. A subtask stuck in a tight, non-blocking, non-checking loop won't be interrupted just because the scope wants to shut down.

- Preview in Java 21 (up from incubator in Java 19 and Java 20) — check your exact JDK build for whether `--add-modules jdk.incubator.concurrent` is still required alongside `--enable-preview`.
- `try (var scope = new StructuredTaskScope.ShutdownOnFailure())` guarantees no forked subtask outlives the scope's block.
- `ShutdownOnFailure` cancels sibling subtasks the moment any one fails; `ShutdownOnSuccess` is the mirror policy for "stop once any one succeeds" (e.g., racing redundant calls).
- Designed to compose directly with [scoped values](0753-scoped-values-preview.md): a scoped value bound before opening the scope is visible to every subtask it forks.
- Subtasks must actually respond to interruption (via blocking calls or explicit checks) for cancellation to take effect promptly — structured concurrency provides the containment discipline, not automatic preemption.
