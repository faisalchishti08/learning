---
card: java
gi: 732
slug: scoped-values-incubator
title: Scoped values (incubator)
---

## 1. What it is

**Java 20** (JEP 429) incubates **scoped values** (`jdk.incubator.concurrent.ScopedValue`), a new way to share immutable data across a thread and the methods it calls — and, importantly, across the child tasks it forks — without passing it explicitly as a parameter through every intermediate method. It targets the exact same "share context implicitly down a call stack" problem that `ThreadLocal` has solved since Java 1.2, but with a fundamentally different lifecycle: a scoped value is bound for the duration of a single, well-defined block of code (`ScopedValue.where(...).run(...)`), is immutable for that entire duration, and is automatically and reliably unbound the instant that block exits — no `remove()` call to forget, and no possibility of a stale value leaking into unrelated code that happens to reuse the same thread afterward. It was designed from the outset to work efficiently with the huge numbers of threads that [virtual threads](0725-virtual-threads-preview.md) make practical, which `ThreadLocal` was not.

## 2. Why & when

`ThreadLocal` has a set of well-known, long-standing problems that become sharper in a virtual-threads world. First, it's mutable and unscoped by design: any code with access to a `ThreadLocal` can call `.set()` at any point, and nothing enforces that whoever set it also cleans it up — forgetting a `.remove()` call, especially in thread-pool-reused platform threads, is a classic source of subtle context-leak bugs, where request A's data is still sitting in a `ThreadLocal` when request B's code runs on the same pooled thread. Second, every child thread spawned from a parent doesn't automatically see the parent's `ThreadLocal` values unless the more expensive `InheritableThreadLocal` is used, which then has to eagerly copy the entire value set to every child thread — a real cost when a program might create thousands or millions of cheap virtual threads, each needing to see the same handful of contextual values (a request ID, an authenticated user, a trace context) that a `StructuredTaskScope` forked. Scoped values solve both: they're bound immutably for exactly the lifetime of a block via `ScopedValue.where(...).run(...)` (impossible to forget to "unset," since the JVM does it automatically when the block exits), and they're designed to be cheaply and correctly visible to structured-concurrency child tasks forked within that block, without the eager, unconditional copying `InheritableThreadLocal` requires. Reach for scoped values instead of `ThreadLocal` for exactly the classic implicit-context use case — request-scoped identifiers, transaction context, security principals — especially in code that also uses virtual threads or structured concurrency.

## 3. Core concept

```java
static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

// Bind REQUEST_ID for the duration of this block only — automatically
// and reliably unbound the instant run() returns, even if it throws.
ScopedValue.where(REQUEST_ID, "req-42").run(() -> {
    processRequest(); // and anything IT calls can read REQUEST_ID.get()
});
// REQUEST_ID.get() here would throw — it's no longer bound.

static void processRequest() {
    System.out.println("Handling " + REQUEST_ID.get()); // reads the bound value
}
```

Unlike `ThreadLocal.set(...)`/`.remove()`, there's no separate call to undo the binding — the binding's entire lifetime is the `run()` (or `call()`) block itself.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A scoped value is bound only for the duration of a where().run() block; any method called within that block, and any structured-concurrency child task forked within it, can read the value, but it is automatically unbound the instant the block exits">
  <rect x="20" y="20" width="600" height="160" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">ScopedValue.where(REQUEST_ID, "req-42").run(() -&gt; { ... })</text>

  <rect x="60" y="70" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="150" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">processRequest()</text>

  <rect x="400" y="70" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="490" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">forked child task</text>

  <text x="330" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">both can call REQUEST_ID.get() and see "req-42"</text>
  <text x="330" y="200" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">outside this block: REQUEST_ID.get() throws — automatically unbound</text>
</svg>

The binding's lifetime is exactly the enclosing block — no manual cleanup, no possibility of leaking into unrelated code.

## 5. Runnable example

Scenario: a small request-processing pipeline needing a request ID visible to logging deep in the call stack, without threading it through every method parameter. It grows from basic scoped-value binding and reading, to comparing it directly against the equivalent `ThreadLocal` code to highlight the automatic-unbinding difference, to combining scoped values with [structured concurrency](0726-structured-concurrency-incubator.md) so forked subtasks correctly see the same bound context.

### Level 1 — Basic

```java
// File: ScopedValueBasic.java
// Run with --enable-preview --add-modules jdk.incubator.concurrent — Java 20 incubator.
import jdk.incubator.concurrent.ScopedValue;

public class ScopedValueBasic {
    static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

    static void logMessage(String message) {
        // No REQUEST_ID parameter was passed down through main -> handleRequest -> here.
        System.out.println("[" + REQUEST_ID.get() + "] " + message);
    }

    static void handleRequest() {
        logMessage("processing started");
        logMessage("processing finished");
    }

    public static void main(String[] args) {
        ScopedValue.where(REQUEST_ID, "req-42").run(ScopedValueBasic::handleRequest);
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview --add-modules jdk.incubator.concurrent ScopedValueBasic.java
java --enable-preview --add-modules jdk.incubator.concurrent ScopedValueBasic
```

Expected output:
```
[req-42] processing started
[req-42] processing finished
```

### Level 2 — Intermediate

```java
// File: ScopedValueVsThreadLocalIntermediate.java
// Directly contrasts ScopedValue's automatic unbinding against ThreadLocal's
// manual, forgettable cleanup — processing two "requests" on the same thread
// to show ScopedValue can never leak stale context between them.
import jdk.incubator.concurrent.ScopedValue;

public class ScopedValueVsThreadLocalIntermediate {
    static final ScopedValue<String> SCOPED_REQUEST_ID = ScopedValue.newInstance();
    static final ThreadLocal<String> THREAD_LOCAL_REQUEST_ID = new ThreadLocal<>();

    static void logScoped(String message) {
        String id = SCOPED_REQUEST_ID.isBound() ? SCOPED_REQUEST_ID.get() : "NONE";
        System.out.println("[scoped:" + id + "] " + message);
    }

    static void logThreadLocal(String message) {
        String id = THREAD_LOCAL_REQUEST_ID.get();
        System.out.println("[threadlocal:" + id + "] " + message);
    }

    public static void main(String[] args) {
        // Request A: properly bound in both mechanisms.
        ScopedValue.where(SCOPED_REQUEST_ID, "req-A").run(() -> logScoped("handling request A"));
        THREAD_LOCAL_REQUEST_ID.set("req-A");
        logThreadLocal("handling request A");
        THREAD_LOCAL_REQUEST_ID.remove(); // must remember to clean up!

        // Simulate a bug: someone forgets to set/bind before "request B" on the same thread.
        logScoped("handling request B (no binding this time)");   // safely reports NONE
        logThreadLocal("handling request B (forgot to set!)");    // would leak stale "req-A" if remove() above was skipped
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview --add-modules jdk.incubator.concurrent ScopedValueVsThreadLocalIntermediate.java
java --enable-preview --add-modules jdk.incubator.concurrent ScopedValueVsThreadLocalIntermediate
```

Expected output:
```
[scoped:req-A] handling request A
[threadlocal:req-A] handling request A
[scoped:NONE] handling request B (no binding this time)
[threadlocal:null] handling request B (forgot to set!)
```

### Level 3 — Advanced

```java
// File: ScopedValueStructuredAdvanced.java
// Combines ScopedValue with StructuredTaskScope: subtasks forked inside the
// bound block correctly see the SAME request ID, without it being passed
// as an explicit parameter or copied via InheritableThreadLocal.
import jdk.incubator.concurrent.ScopedValue;
import jdk.incubator.concurrent.StructuredTaskScope;
import java.util.concurrent.Future;

public class ScopedValueStructuredAdvanced {
    static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

    static String fetchUser() throws InterruptedException {
        Thread.sleep(30);
        return "user-data[" + REQUEST_ID.get() + "]"; // reads the value from the FORKING thread's binding
    }

    static String fetchOrders() throws InterruptedException {
        Thread.sleep(20);
        return "orders-data[" + REQUEST_ID.get() + "]";
    }

    static String handleRequest() throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            Future<String> userTask = scope.fork(ScopedValueStructuredAdvanced::fetchUser);
            Future<String> orderTask = scope.fork(ScopedValueStructuredAdvanced::fetchOrders);

            scope.join();
            scope.throwIfFailed();

            return userTask.resultNow() + " + " + orderTask.resultNow();
        }
    }

    public static void main(String[] args) throws Exception {
        String result1 = ScopedValue.where(REQUEST_ID, "req-100").call(ScopedValueStructuredAdvanced::handleRequest);
        String result2 = ScopedValue.where(REQUEST_ID, "req-200").call(ScopedValueStructuredAdvanced::handleRequest);

        System.out.println(result1);
        System.out.println(result2);
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview --add-modules jdk.incubator.concurrent ScopedValueStructuredAdvanced.java
java --enable-preview --add-modules jdk.incubator.concurrent ScopedValueStructuredAdvanced
```

Expected output:
```
user-data[req-100] + orders-data[req-100]
user-data[req-200] + orders-data[req-200]
```

## 6. Walkthrough

1. `ScopedValueStructuredAdvanced.main` calls `ScopedValue.where(REQUEST_ID, "req-100").call(...)`. This binds `REQUEST_ID` to `"req-100"` for the exact duration of the `handleRequest` call and everything it does, then invokes `handleRequest` and returns its result as `result1`.
2. Inside `handleRequest`, a `StructuredTaskScope.ShutdownOnFailure` is opened, and two subtasks are forked: `fetchUser` and `fetchOrders`. Each fork spawns a new (virtual) thread to run that method.
3. This is the key moment the example demonstrates: `fetchUser` and `fetchOrders`, running on **different threads** than the one that called `ScopedValue.where(...).call(...)`, both successfully call `REQUEST_ID.get()` and see `"req-100"` — the binding correctly propagates to structured-concurrency child tasks forked from within the bound block, without `REQUEST_ID` ever being passed as a parameter to either method.
4. Both subtasks complete (`Thread.sleep` standing in for simulated I/O), `scope.join()` waits for both, `throwIfFailed()` finds nothing to report, and `handleRequest` combines both results into one string, which becomes `result1`.
5. `main` then calls the entire sequence again with a **different** binding, `"req-200"`. Because each `ScopedValue.where(...).call(...)` invocation creates its own independent binding scope, the second call's subtasks see `"req-200"`, completely unaffected by the first call's now-already-exited `"req-100"` binding — there is no possibility of the second request accidentally observing the first request's ID, the exact class of bug `ThreadLocal` reuse (Level 2) makes possible if cleanup is forgotten.
6. Because `call()` (used here, returning a value) and `run()` (used in Levels 1 and 2, returning nothing) both fully complete — including waiting for every forked subtask via `scope.join()` — before returning, the `REQUEST_ID` binding remains valid for the *entire* duration any subtask might still read it; the binding cannot be prematurely torn down while a subtask is still legitimately using it, because structured concurrency's own rule (a scope cannot close until every subtask has terminated) and the scoped value's binding lifetime naturally line up.

```
main()
  |
  ScopedValue.where(REQUEST_ID, "req-100").call(handleRequest)
  |         [binding "req-100" starts]
  v
  handleRequest()
       |
       fork fetchUser()  ---- (different thread) ---- reads REQUEST_ID.get() = "req-100"
       fork fetchOrders() --- (different thread) ---- reads REQUEST_ID.get() = "req-100"
       |
       scope.join()  <- waits for both
  |         [binding "req-100" ends automatically when call() returns]
  v
result1 = "user-data[req-100] + orders-data[req-100]"

  (completely independent second binding follows, "req-200", same pattern)
```

## 7. Gotchas & takeaways

> This is an **incubator API** in Java 20 (`jdk.incubator.concurrent.ScopedValue`), layered on the also-preview [structured concurrency](0726-structured-concurrency-incubator.md) and [virtual threads](0725-virtual-threads-preview.md) features from the same era — it requires `--enable-preview --add-modules jdk.incubator.concurrent`, and continued to evolve (including relocating to `java.lang`) before eventual finalization in later JDKs.
- Calling `.get()` on a `ScopedValue` that isn't currently bound throws `NoSuchElementException` — checking `.isBound()` first (as Level 2 does) is the safe way to handle code paths that might run either inside or outside a binding.
- A `ScopedValue` binding is only visible to the thread that established it and to structured-concurrency subtasks forked *within* that binding's block — a thread started with plain `new Thread(...).start()` (rather than forked via `StructuredTaskScope`) from inside a bound block does **not** automatically inherit the binding, unlike `InheritableThreadLocal`; this is a deliberate design choice tying scoped-value propagation specifically to structured concurrency's well-defined parent-child task relationships.
- Rebinding the same `ScopedValue` to a different value is done by calling `ScopedValue.where(...)` again for a new, nested block — not by mutating the existing binding, since scoped values are immutable for their entire bound lifetime by design; this immutability is what makes them safe to read from multiple concurrently forked subtasks without synchronization.
- The core practical advantage over `ThreadLocal` demonstrated in Level 2 is structural, not just stylistic: it is *impossible* to forget to unbind a scoped value the way it's possible to forget a `ThreadLocal.remove()` call, because the unbinding isn't a separate step at all — it's an automatic consequence of the `where(...).run()`/`.call()` block ending.
