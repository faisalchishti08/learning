---
card: java
gi: 904
slug: scoped-values
title: Scoped values
---

## 1. What it is

`ScopedValue<T>` (introduced as a preview API alongside virtual threads and structured concurrency) is a way to bind an immutable value to a well-defined **dynamic scope** — you call `ScopedValue.where(KEY, value).run(() -> { ... })`, and inside that lambda (and anything it calls, including forked structured-concurrency subtasks), `KEY.get()` retrieves the bound value. The instant `run()` returns, the binding is gone — there is no `set()` method, no way to leave a value bound past the scope that established it, and no way to leak or forget to clean it up, unlike [`ThreadLocal`](0897-threadlocal.md).

## 2. Why & when

`ScopedValue` was designed specifically to address the two well-known pitfalls of `ThreadLocal` covered in earlier tutorials: [memory leaks](0899-threadlocal-memory-leaks.md) from forgetting to `remove()` on pooled threads, and `InheritableThreadLocal`'s awkward, snapshot-based, one-directional propagation to child threads that doesn't interact cleanly with [structured concurrency](0903-structured-concurrency.md)'s forked subtasks. Because a scoped value's binding is tied to the lexical/dynamic extent of a `run()` call rather than to a specific thread's long-lived storage, it cannot outlive its scope by construction — there's no equivalent of "forgetting to clean up," since there's nothing to clean up; the binding simply ends when `run()` returns. Scoped values are also automatically and correctly inherited by subtasks forked within a `StructuredTaskScope` inside the bound scope, making the two APIs a natural pairing for propagating context (a request ID, an authenticated user, a tracing span) into concurrently-forked work without any of `ThreadLocal`'s pitfalls. Use `ScopedValue` for exactly this kind of read-mostly, contextual, effectively-final data that a call tree (including its concurrently forked subtasks) needs to access without threading it through every method signature explicitly.

## 3. Core concept

```java
static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

ScopedValue.where(REQUEST_ID, "req-abc123").run(() -> {
    handleRequest(); // REQUEST_ID.get() returns "req-abc123" anywhere inside this call tree
}); // binding is GONE the instant run() returns -- nothing to clean up, no leak possible

void handleRequest() {
    System.out.println(REQUEST_ID.get()); // works, even though it's not passed as a parameter
}
```

There is no `remove()` because there is nothing to remove — the binding's lifetime is exactly the duration of the `run()` call, enforced by the language/API itself rather than by programmer discipline.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ScopedValue.where(...).run(...) establishes a binding visible to everything called within it, including forked structured concurrency subtasks, and the binding disappears automatically the instant run returns">
  <rect x="180" y="15" width="280" height="35" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="37" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ScopedValue.where(ID, "req-1").run(() -&gt; {</text>

  <rect x="60" y="70" width="220" height="35" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="170" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">handleRequest() sees ID="req-1"</text>

  <rect x="360" y="70" width="220" height="35" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="470" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">forked subtask ALSO sees ID="req-1"</text>

  <line x1="320" y1="50" x2="170" y2="68" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a34)"/>
  <line x1="320" y1="50" x2="470" y2="68" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a34)"/>

  <rect x="180" y="130" width="280" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="320" y="150" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">}) -- binding is GONE, automatically, no cleanup needed</text>
  <defs><marker id="a34" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Everything inside the `run()` call — including forked structured-concurrency subtasks — sees the bound value; nothing outside it ever can, and there's no manual cleanup step.*

## 5. Runnable example

Scenario: propagating a request ID through a request-handling call tree that also fans out concurrent subtasks, growing from `ThreadLocal` (which needs manual cleanup and doesn't cleanly propagate to unrelated executor-submitted tasks), to `ScopedValue` for automatic, leak-proof binding, to combining it with `StructuredTaskScope` so forked subtasks correctly and automatically inherit the bound value.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class ThreadLocalRequiresCleanup {
    static final ThreadLocal<String> REQUEST_ID = new ThreadLocal<>();

    static void handleRequest(String id) {
        REQUEST_ID.set(id);
        try {
            processRequest();
        } finally {
            REQUEST_ID.remove(); // MUST remember this, every time, on every code path
        }
    }

    static void processRequest() {
        System.out.println("processing with request ID: " + REQUEST_ID.get());
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor();
        pool.submit(() -> handleRequest("req-1")).get(1, TimeUnit.SECONDS);
        pool.shutdown();
        pool.awaitTermination(1, TimeUnit.SECONDS);
        System.out.println("(works, but relies entirely on remembering the remove() call in finally, every time)");
    }
}
```

**How to run:** `java ThreadLocalRequiresCleanup.java` (JDK 21+).

Expected output:
```
processing with request ID: req-1
(works, but relies entirely on remembering the remove() call in finally, every time)
```

Correct, but entirely dependent on disciplined, manual cleanup — see [`ThreadLocal` memory leaks](0899-threadlocal-memory-leaks.md) for what happens when that discipline lapses on a pooled thread.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class ScopedValueAutomaticCleanup {
    static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

    static void handleRequest(String id) {
        ScopedValue.where(REQUEST_ID, id).run(() -> {
            processRequest();
        }); // binding automatically gone here -- no remove() call exists or is needed
    }

    static void processRequest() {
        System.out.println("processing with request ID: " + REQUEST_ID.get());
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor();
        pool.submit(() -> handleRequest("req-1")).get(1, TimeUnit.SECONDS);
        pool.shutdown();
        pool.awaitTermination(1, TimeUnit.SECONDS);
        System.out.println("(binding was automatically cleared when run() returned -- nothing to forget)");
    }
}
```

**How to run:** `java --enable-preview ScopedValueAutomaticCleanup.java` (JDK 21+; flag requirement depends on your JDK version's preview status for this API).

Expected output:
```
processing with request ID: req-1
(binding was automatically cleared when run() returned -- nothing to forget)
```

The real-world concern added: the binding's entire lifetime is scoped to the `run()` call — there's no `remove()` method to forget, no leak risk on pooled threads, and no possibility of a stale value lingering into some later, unrelated task run on the same pooled (virtual) thread.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class ScopedValueWithStructuredConcurrency {
    static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

    static String fetchUserData() throws InterruptedException {
        Thread.sleep(50);
        return "user-data[" + REQUEST_ID.get() + "]"; // reads the bound value from WITHIN a forked subtask
    }

    static String fetchOrderHistory() throws InterruptedException {
        Thread.sleep(50);
        return "order-history[" + REQUEST_ID.get() + "]"; // ALSO correctly sees the same bound value
    }

    static String handleRequest(String id) throws Exception {
        return ScopedValue.where(REQUEST_ID, id).call(() -> {
            try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
                var userTask = scope.fork(ScopedValueWithStructuredConcurrency::fetchUserData);
                var orderTask = scope.fork(ScopedValueWithStructuredConcurrency::fetchOrderHistory);

                scope.join();
                scope.throwIfFailed();

                return userTask.get() + " + " + orderTask.get();
            }
        });
    }

    public static void main(String[] args) throws Exception {
        String result = handleRequest("req-42");
        System.out.println("combined result: " + result);
        System.out.println("both forked subtasks correctly inherited REQUEST_ID from the enclosing scope");
    }
}
```

**How to run:** `java --enable-preview ScopedValueWithStructuredConcurrency.java` (JDK 21+).

Expected output:
```
combined result: user-data[req-42] + order-history[req-42]
both forked subtasks correctly inherited REQUEST_ID from the enclosing scope
```

This adds the production-flavored hard case: `REQUEST_ID`'s binding, established once via `ScopedValue.where(...).call(...)`, is correctly and automatically visible inside **two separately forked** `StructuredTaskScope` subtasks (`fetchUserData` and `fetchOrderHistory`), each running on its own virtual thread — demonstrating that scoped values propagate cleanly into structured concurrency's forked work without any manual passing, `InheritableThreadLocal`-style snapshot copying, or cleanup code, and without any risk of the binding leaking past the `call()` invocation that established it.

## 6. Walkthrough

Tracing `ScopedValueWithStructuredConcurrency.handleRequest("req-42")`:

1. `ScopedValue.where(REQUEST_ID, "req-42").call(() -> {...})` establishes a binding: for the duration of the lambda passed to `call`, any code that calls `REQUEST_ID.get()` — on this thread, or on any thread involved in structured concurrency forked from within this scope — will see `"req-42"`.
2. Inside the lambda, a `StructuredTaskScope.ShutdownOnFailure` is opened, and two subtasks are forked: `fetchUserData` and `fetchOrderHistory`, each dispatched to run on its own virtual thread.
3. Even though these forked subtasks run on *different* threads from the one that called `where(...).call(...)`, the scoped-value binding is correctly propagated to them — this is a deliberate, built-in integration between `ScopedValue` and `StructuredTaskScope`, specifically designed so forked subtasks see the same bindings as their parent scope without any extra plumbing.
4. `fetchUserData`, running on its own virtual thread, calls `REQUEST_ID.get()` and correctly retrieves `"req-42"` — not `null`, and not some snapshot taken at an earlier, possibly-stale moment, but the actual binding established by the enclosing `call()` invocation.
5. `fetchOrderHistory`, running on a *different* virtual thread from `fetchUserData`, independently also calls `REQUEST_ID.get()` and also correctly retrieves `"req-42"` — both forked subtasks see the identical, correct binding, entirely independently of each other.
6. `scope.join()` waits for both subtasks; since neither fails, `scope.throwIfFailed()` does nothing, and `userTask.get()` / `orderTask.get()` retrieve each subtask's computed string, which are concatenated and returned from the `call()` lambda.
7. Once `call()` returns, the `ScopedValue` binding for `REQUEST_ID` is gone entirely — any code running after this point (outside the `where(...).call(...)` invocation) that called `REQUEST_ID.get()` without a new binding in effect would find no value bound at all, confirming the binding's lifetime was exactly the extent of the `call()` invocation, with no possibility of it lingering or leaking.

## 7. Gotchas & takeaways

> **Gotcha:** `ScopedValue` (like `StructuredTaskScope`) is a preview API as of the JDK versions where it was introduced, and its exact method names and required compiler/runtime flags (`--enable-preview`) may have changed across releases — verify against your specific JDK version's documentation, and expect this area of the platform to continue evolving.

- `ScopedValue<T>` binds an immutable value for the exact dynamic extent of a `run()`/`call()` invocation — the binding is automatically and unconditionally gone the instant that call returns, with no `remove()` method and no possibility of forgetting cleanup.
- This directly addresses [`ThreadLocal`'s memory leak risk](0899-threadlocal-memory-leaks.md) on pooled threads, since there's no long-lived, thread-attached storage that can outlive the logical operation it was meant to serve.
- Scoped values are automatically and correctly inherited by subtasks forked within a [`StructuredTaskScope`](0903-structured-concurrency.md) established inside the bound scope — a clean, built-in integration that `InheritableThreadLocal`'s one-time-snapshot model doesn't provide as naturally, especially for concurrently forked (rather than sequentially created) child work.
- Use `ScopedValue` for read-mostly, contextual data (request IDs, authenticated principals, tracing context) that a call tree — including its concurrently forked subtasks — needs without threading it through every method signature explicitly.
- Because bindings are immutable for their scope's duration (there's no `set()` to change a binding mid-scope, only nested `where(...).call(...)` invocations to establish a new, more deeply nested binding), scoped values are not a general-purpose replacement for all `ThreadLocal` use cases — specifically, they're not suited for genuinely mutable, per-thread state that needs to change over the life of a thread rather than being fixed for a well-defined scope.
