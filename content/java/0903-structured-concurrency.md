---
card: java
gi: 903
slug: structured-concurrency
title: Structured concurrency
---

## 1. What it is

Structured concurrency treats a group of related concurrent subtasks as a single unit of work with a well-defined lifetime: they're all started together, and the code that started them cannot proceed past the point where it waits for them until *all* of them have either completed, failed, or been explicitly cancelled — mirroring how structured programming treats a block of sequential code as having one entry point and one exit point. In Java, this is realized through `StructuredTaskScope` (introduced as a preview/incubating API alongside virtual threads): you open a scope, `fork()` several subtasks onto it (each running on its own virtual thread), call `join()` to wait for them according to the scope's policy, and the scope's `close()` (typically via try-with-resources) guarantees that no subtask can outlive the scope, even if one of them fails.

## 2. Why & when

Unstructured concurrency — firing off tasks via a raw `ExecutorService` and separately, loosely tracking their `Future`s — has a well-known failure mode: if one subtask fails and you decide to abandon the whole operation, nothing automatically stops the *other* still-running subtasks; they keep consuming resources (threads, memory, backend connections) even though their result is now irrelevant, and if a bug leaves a `Future` un-awaited entirely, that subtask can leak indefinitely with no supervising code aware it's still running. Structured concurrency fixes this by construction: forked subtasks are scoped to their parent block, so cancelling or exiting the scope reliably cancels every subtask still running within it — you can never accidentally leave an orphaned subtask running past the point where its parent operation has moved on. Use it whenever you fan out to several concurrent subtasks that logically belong to one request or operation — fetching a user's profile and their preferences concurrently to build one page, where either failing should cancel the other rather than let it run to a now-useless completion.

## 3. Core concept

```java
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Subtask<String> userTask = scope.fork(() -> fetchUser(userId));
    Subtask<String> prefsTask = scope.fork(() -> fetchPreferences(userId));

    scope.join();            // waits for BOTH to finish (or one to fail, triggering shutdown of the other)
    scope.throwIfFailed();   // if either failed, rethrow that failure now

    String user = userTask.get();
    String prefs = prefsTask.get();
    // both succeeded -- combine and use them
} // scope.close(): guarantees NEITHER subtask can still be running past this point
```

`ShutdownOnFailure` is one built-in policy: the instant any forked subtask fails, it cancels every other subtask still running in the same scope, rather than waiting for them to finish pointlessly.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A structured task scope forks two subtasks; if one fails, the scope cancels the other immediately rather than letting it run to a useless completion, and the scope cannot close until both are accounted for">
  <rect x="240" y="15" width="160" height="30" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="35" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">StructuredTaskScope</text>

  <rect x="60" y="70" width="200" height="40" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="160" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Subtask A: FAILS</text>

  <rect x="380" y="70" width="200" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="480" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Subtask B: CANCELLED promptly</text>

  <line x1="320" y1="45" x2="160" y2="68" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a33)"/>
  <line x1="320" y1="45" x2="480" y2="68" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a33)"/>
  <line x1="160" y1="110" x2="480" y2="108" stroke="#f85149" stroke-width="2" stroke-dasharray="4" marker-end="url(#a33)"/>
  <text x="320" y="130" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">A's failure triggers immediate cancellation of B -- no orphaned, useless work</text>

  <rect x="180" y="150" width="280" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="170" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">scope.close() -- guarantees BOTH are done</text>
  <defs><marker id="a33" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*A failure in one forked subtask immediately cancels its siblings, and the scope cannot be exited until every subtask is accounted for — no orphaned work escapes the block.*

## 5. Runnable example

Scenario: building a user dashboard by fetching a profile and preferences concurrently, growing from unstructured `ExecutorService`/`Future` code that leaks a subtask on failure, to `StructuredTaskScope.ShutdownOnFailure` fixing that leak, to a version using `ShutdownOnSuccess` to race redundant lookups and take the first success.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class UnstructuredConcurrencyLeak {
    static String fetchUser(int id) throws InterruptedException {
        Thread.sleep(50);
        if (id == 999) throw new RuntimeException("user not found");
        return "User#" + id;
    }
    static String fetchPreferences(int id) throws InterruptedException {
        Thread.sleep(300); // deliberately slow, to expose the leak
        return "Preferences#" + id;
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor();
        Future<String> userFuture = pool.submit(() -> fetchUser(999)); // WILL fail
        Future<String> prefsFuture = pool.submit(() -> fetchPreferences(999)); // keeps running regardless

        try {
            String user = userFuture.get(); // throws ExecutionException immediately
            String prefs = prefsFuture.get();
            System.out.println(user + ", " + prefs);
        } catch (ExecutionException e) {
            System.out.println("user fetch failed: " + e.getCause().getMessage());
            System.out.println("but prefsFuture is STILL RUNNING in the background, unsupervised, for no useful purpose");
        }
        pool.shutdown(); // does NOT cancel already-submitted, in-flight tasks
        pool.awaitTermination(1, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java UnstructuredConcurrencyLeak.java` (JDK 21+, `StructuredTaskScope` used in later levels is a preview API — run with `--enable-preview` if required by your JDK version).

Expected output:
```
user fetch failed: user not found
but prefsFuture is STILL RUNNING in the background, unsupervised, for no useful purpose
```

The user-fetch failure is handled, but nothing stops `prefsFuture`'s already-submitted task from continuing to run its full 300ms in the background — wasted work that nobody is waiting for or will use, and in more complex real systems, a resource (a connection, a lock) that stays held longer than necessary.

### Level 2 — Intermediate

```java
import java.util.concurrent.StructuredTaskScope;

public class StructuredShutdownOnFailure {
    static String fetchUser(int id) throws InterruptedException {
        Thread.sleep(50);
        if (id == 999) throw new RuntimeException("user not found");
        return "User#" + id;
    }
    static String fetchPreferences(int id) throws InterruptedException {
        Thread.sleep(300);
        System.out.println("prefs fetch completed (should NOT print if properly cancelled early)");
        return "Preferences#" + id;
    }

    public static void main(String[] args) throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            var userTask = scope.fork(() -> fetchUser(999));       // WILL fail quickly
            var prefsTask = scope.fork(() -> fetchPreferences(999)); // would take much longer

            scope.join(); // waits for completion OR failure -- failure here cancels prefsTask promptly
            scope.throwIfFailed(e -> new RuntimeException("dashboard load failed: " + e.getMessage(), e));

            System.out.println(userTask.get() + ", " + prefsTask.get()); // unreachable -- throwIfFailed already threw
        } catch (RuntimeException e) {
            System.out.println("caught: " + e.getMessage());
            System.out.println("prefsTask was cancelled promptly -- no orphaned background work");
        }
    }
}
```

**How to run:** `java --enable-preview StructuredShutdownOnFailure.java` (JDK 21+; flag requirement depends on your specific JDK version's preview status for this API).

Expected output:
```
caught: dashboard load failed: user not found
prefsTask was cancelled promptly -- no orphaned background work
```

The real-world concern added: the instant `userTask` fails, `ShutdownOnFailure`'s policy cancels every other subtask in the same scope — `prefsTask` is interrupted before its 300ms sleep completes, so the "prefs fetch completed" message correctly never prints, and `scope.close()` (via try-with-resources) doesn't return control to the caller until both subtasks are fully accounted for, whether by completion or cancellation.

### Level 3 — Advanced

```java
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.TimeUnit;

public class StructuredShutdownOnSuccess {
    static String queryMirror(String name, int delayMs, boolean shouldFail) throws InterruptedException {
        Thread.sleep(delayMs);
        if (shouldFail) throw new RuntimeException(name + " unavailable");
        return name + " responded";
    }

    public static void main(String[] args) throws Exception {
        // ShutdownOnSuccess: races several redundant subtasks, takes the FIRST successful result,
        // and cancels the rest -- ideal for redundant, competing lookups where any success suffices.
        try (var scope = new StructuredTaskScope.ShutdownOnSuccess<String>()) {
            scope.fork(() -> queryMirror("mirror-A", 300, true));  // will fail
            scope.fork(() -> queryMirror("mirror-B", 100, false)); // expected winner
            scope.fork(() -> queryMirror("mirror-C", 250, false)); // would also succeed, but slower

            scope.join();
            String result = scope.result(); // the first SUCCESSFUL result; cancels the rest automatically
            System.out.println("winning result: " + result);
        } catch (Exception e) {
            System.out.println("all mirrors failed: " + e.getMessage());
        }
    }
}
```

**How to run:** `java --enable-preview StructuredShutdownOnSuccess.java` (JDK 21+).

Expected output:
```
winning result: mirror-B responded
```

This adds the production-flavored hard case: `ShutdownOnSuccess` races three redundant subtasks (mirror-A, which will fail; mirror-B, the fastest to succeed; mirror-C, slower but would also succeed) and takes the first one that completes *successfully* — mirror-A's failure alone doesn't end the race (unlike `ShutdownOnFailure`'s policy), since other subtasks might still succeed, but as soon as mirror-B succeeds, the scope cancels mirror-C's still-in-flight work rather than waiting for it pointlessly, demonstrating a second, distinct cancellation policy suited to a different concurrency pattern (racing for the first success, rather than failing fast together).

## 6. Walkthrough

Tracing `StructuredShutdownOnSuccess.main`:

1. Three subtasks are forked onto the scope essentially simultaneously, each running on its own virtual thread: mirror-A (300ms delay, will throw), mirror-B (100ms delay, will succeed), mirror-C (250ms delay, will succeed).
2. At around the 100ms mark, mirror-B's `queryMirror` call returns successfully with `"mirror-B responded"` — since the scope's policy is `ShutdownOnSuccess`, this first success triggers the scope to begin shutting down: any subtask still running (mirror-C, which still has roughly 150ms left; mirror-A, which still has roughly 200ms left) is interrupted/cancelled.
3. `scope.join()` returns once the scope has either recorded a success or determined every subtask has failed — here, it returns promptly after mirror-B's success is recorded and the cancellation of the others is underway.
4. `scope.result()` retrieves the first successful result recorded — `"mirror-B responded"` — without needing to wait for mirror-A's failure or mirror-C's would-be success to ever actually resolve, since both are cancelled as soon as mirror-B's success is recorded.
5. Because the scope is used inside a try-with-resources block, `scope.close()` runs automatically when the block exits, which enforces that no subtask (including the cancelled mirror-A and mirror-C) can still be running past this point — guaranteeing no orphaned virtual threads are left doing pointless work in the background, exactly the structural guarantee that unstructured `ExecutorService`/`Future` code cannot provide without significant extra manual bookkeeping.
6. The printed result confirms the race was won by the fastest successful subtask, with the other two definitively cleaned up rather than left to run to their own eventual (successful or failed) completion unsupervised.

## 7. Gotchas & takeaways

> **Gotcha:** `StructuredTaskScope` (as of the versions where it has shipped as a preview/incubating API) may require an `--enable-preview` flag and its exact API surface has evolved across JDK releases — check the specific JDK version's documentation for the current method names and required flags, since this is one of the more actively-evolving newer JDK APIs.

- Structured concurrency guarantees that a group of forked subtasks cannot outlive the scope that created them — the scope's `close()` (typically via try-with-resources) ensures every subtask is completed or cancelled before control returns to the caller.
- `ShutdownOnFailure`: the first subtask to fail cancels all its siblings — ideal for "all of these must succeed together" scenarios like fetching several pieces of data needed to build one response.
- `ShutdownOnSuccess`: the first subtask to succeed cancels all its siblings — ideal for racing redundant, competing operations where any single success is sufficient.
- Unstructured concurrency (raw `ExecutorService` + loosely-tracked `Future`s) has no equivalent built-in guarantee — a failed or abandoned operation can easily leave sibling subtasks running unsupervised, wasting resources with no code aware they're still active.
- Structured concurrency and virtual threads are designed to complement each other closely — forking many subtasks is cheap precisely because each one typically runs on its own virtual thread; see [scoped values](0904-scoped-values.md) for a related newer API designed to safely pass context into these forked subtasks without the pitfalls of `ThreadLocal`.
