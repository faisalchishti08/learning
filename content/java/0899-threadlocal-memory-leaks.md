---
card: java
gi: 899
slug: threadlocal-memory-leaks
title: ThreadLocal memory leaks
---

## 1. What it is

A `ThreadLocal` memory leak happens when a `ThreadLocal` variable is `set()` on a long-lived thread (almost always a thread-pool worker) but never `remove()`d, and the object holding a reference to the `ThreadLocal` itself (or a classloader containing it) would otherwise be eligible for garbage collection. Because the thread's internal storage map keeps a strong reference to the stored value for as long as the thread lives, and pool threads can live for the entire lifetime of the application, that value — and everything it in turn references — is kept alive indefinitely, even though logically nothing "in use" needs it anymore.

## 2. Why & when

This is a particularly common and painful class of leak in application servers and any long-running service built on thread pools, because the leaked objects are often large (a whole request context, a database connection wrapper, a custom classloader in application-server redeployment scenarios) and the leak is invisible in ordinary testing — it only manifests as slowly growing memory usage over the lifetime of a long-running process, sometimes over days or weeks, making it hard to correlate back to a specific `set()` call. It matters specifically whenever `ThreadLocal.set()` is called on a thread that is *pooled* (an `ExecutorService`'s worker threads, an application server's request-handling threads) rather than a short-lived, one-off `Thread` that terminates and is garbage-collected soon after finishing — a terminated thread's storage (and everything in it) becomes collectible immediately, so leaks are strictly a pooled-thread phenomenon.

## 3. Core concept

```java
static final ThreadLocal<byte[]> LARGE_BUFFER = new ThreadLocal<>();

void handleTask() {
    LARGE_BUFFER.set(new byte[10_000_000]); // 10MB, stored in THIS pooled thread's storage
    doWork();
    // If remove() is never called here, this 10MB stays referenced by the pool thread
    // for as long as that thread lives -- potentially the entire application lifetime,
    // even though this specific task finished long ago.
    LARGE_BUFFER.remove(); // ESSENTIAL -- without this, the leak accumulates per pooled thread
}
```

Because a pool typically has a small, fixed number of threads, the leak doesn't grow *unboundedly* per task — but each of those few threads can end up permanently pinning whatever the *last* task that forgot to clean up happened to store, and the risk compounds when the leaked object references something much larger (like an entire classloader).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A long-lived pool thread's internal ThreadLocal storage map holding a strong reference to a large object set by a task that finished long ago and never called remove, keeping it alive indefinitely">
  <rect x="20" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Pool worker thread</text>

  <rect x="20" y="80" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Thread's ThreadLocalMap</text>
  <text x="110" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">strong ref to stored value</text>

  <rect x="280" y="80" width="180" height="50" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="370" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Leaked 10MB buffer</text>
  <text x="370" y="118" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">task finished LONG ago</text>

  <line x1="110" y1="60" x2="110" y2="78" stroke="#8b949e" stroke-width="2" marker-end="url(#a31)"/>
  <line x1="200" y1="105" x2="276" y2="105" stroke="#f85149" stroke-width="2" marker-end="url(#a31)"/>

  <text x="320" y="160" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Never garbage collected -- the thread's own reference chain keeps it alive as long as the pool exists.</text>
  <defs><marker id="a31" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*The pool thread itself, not any application-level reference, is what keeps the leaked object alive — it never gets collected while the thread lives.*

## 5. Runnable example

Scenario: a pooled task handler storing per-task context in a `ThreadLocal`, growing from a version that leaks (never cleans up), to demonstrating the leak concretely by observing retained memory, to a properly cleaned-up version using a `try`/`finally` discipline that eliminates the leak entirely.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class LeakingThreadLocal {
    static final ThreadLocal<byte[]> TASK_BUFFER = new ThreadLocal<>();

    static void handleTask(int taskId) {
        TASK_BUFFER.set(new byte[1_000_000]); // 1MB per task, allocated and stored
        // ... do work using TASK_BUFFER.get() ...
        // BUG: no remove() call here -- the 1MB stays referenced by this pool thread FOREVER
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(4); // only 4 threads, REUSED across many tasks
        for (int i = 0; i < 100; i++) {
            final int id = i;
            pool.submit(() -> handleTask(id));
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("100 tasks completed -- but each of the 4 pool threads now permanently");
        System.out.println("retains a 1MB buffer from whichever task last ran on it and never cleaned up");
    }
}
```

**How to run:** `java LeakingThreadLocal.java` (JDK 17+).

Expected output:
```
100 tasks completed -- but each of the 4 pool threads now permanently
retains a 1MB buffer from whichever task last ran on it and never cleaned up
```

Although only 4MB total is leaked here (one 1MB buffer per pool thread, since each thread's storage only holds its *most recent* value for a given `ThreadLocal` key, overwritten by each new `set()`), in a real system with many distinct `ThreadLocal` variables, larger objects, or classloader references, this pattern compounds into a serious, slow, hard-to-diagnose memory growth problem.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.lang.ref.*;

public class ObservingTheLeak {
    static final ThreadLocal<Object> TASK_BUFFER = new ThreadLocal<>();
    static ReferenceQueue<Object> refQueue = new ReferenceQueue<>();

    static void handleTaskLeaking(int taskId, WeakReference<Object>[] tracker) {
        Object buffer = new byte[1_000_000];
        tracker[0] = new WeakReference<>(buffer, refQueue); // track collectibility WITHOUT itself preventing GC
        TASK_BUFFER.set(buffer); // stored in pool thread's storage -- prevents the weak ref from clearing
        // no remove() -- buffer remains strongly reachable via the pool thread's ThreadLocalMap
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(1); // single thread for a clean, deterministic demo
        WeakReference<Object>[] tracker = new WeakReference[1];

        pool.submit(() -> handleTaskLeaking(1, tracker)).get(); // wait for it to run, ignoring checked exceptions here

        System.gc(); // request GC (best-effort, but typically sufficient for this small heap in a demo)
        Thread.sleep(200);

        boolean stillReferenced = tracker[0].get() != null;
        System.out.println("buffer still reachable after GC (because the pool thread still holds it)? " + stillReferenced);
        pool.shutdown();
    }
}
```

**How to run:** `java ObservingTheLeak.java`. (Note: `System.gc()` is only a request; behavior can vary slightly across JVMs, but the pool-thread-held reference reliably prevents collection regardless.)

Expected output:
```
buffer still reachable after GC (because the pool thread still holds it)? true
```

The real-world concern added: using a `WeakReference` to observe collectibility directly demonstrates that the buffer survives a garbage collection cycle specifically *because* the pool thread's `ThreadLocalMap` still holds a strong reference to it — nothing in application code references the buffer anymore (the task finished, `tracker` itself only holds a `WeakReference`), yet it's still alive purely due to the leaked `ThreadLocal` entry on the long-lived pool thread.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.lang.ref.*;

public class ProperCleanupFixesTheLeak {
    static final ThreadLocal<Object> TASK_BUFFER = new ThreadLocal<>();
    static ReferenceQueue<Object> refQueue = new ReferenceQueue<>();

    static void handleTaskProperly(int taskId, WeakReference<Object>[] tracker) {
        Object buffer = new byte[1_000_000];
        tracker[0] = new WeakReference<>(buffer, refQueue);
        TASK_BUFFER.set(buffer);
        try {
            // ... do work using TASK_BUFFER.get() ...
        } finally {
            TASK_BUFFER.remove(); // ESSENTIAL -- clears this thread's storage entry entirely, not just to null
        }
    }

    public static void main(String[] args) throws InterruptedException, ExecutionException {
        ExecutorService pool = Executors.newFixedThreadPool(1);
        WeakReference<Object>[] tracker = new WeakReference[1];

        pool.submit(() -> handleTaskProperly(1, tracker)).get();

        System.gc();
        Thread.sleep(200);

        boolean stillReferenced = tracker[0].get() != null;
        System.out.println("buffer still reachable after GC (with proper remove())? " + stillReferenced);
        System.out.println("proper remove() lets the buffer become collectible as soon as the task finishes");
        pool.shutdown();
    }
}
```

**How to run:** `java ProperCleanupFixesTheLeak.java`.

Expected output shape (`System.gc()` is best-effort, so this is very likely but not absolutely guaranteed by the JLS to show `false` on every JVM/run):
```
buffer still reachable after GC (with proper remove())? false
proper remove() lets the buffer become collectible as soon as the task finishes
```

This adds the production-flavored hard case: wrapping the exact same `set()` call in a `try`/`finally` block that calls `TASK_BUFFER.remove()` unconditionally — this removes the entry from the pool thread's `ThreadLocalMap` entirely (not merely overwriting it with `null`, which would still leave an entry, just holding a `null` value instead of the buffer), letting the buffer become eligible for garbage collection the moment the task finishes, rather than lingering for the rest of the pool thread's lifetime.

## 6. Walkthrough

Contrasting the two versions' effect on garbage collection:

1. In `ObservingTheLeak`, `handleTaskLeaking` calls `TASK_BUFFER.set(buffer)` but never calls `remove()`. Internally, this stores an entry in the pool thread's own `ThreadLocalMap` (a specialized hash map every `Thread` object carries), mapping the `TASK_BUFFER` `ThreadLocal` instance to the 1MB `buffer` object — this entry is a **strong reference**, meaning the garbage collector will never reclaim `buffer` as long as the thread (and hence its map) exists.
2. After the task returns, nothing in `main`'s own code still references `buffer` directly (only a `WeakReference` does, which by definition doesn't prevent collection on its own) — but the pool thread itself, sitting idle waiting for its next task, still holds the strong reference inside its `ThreadLocalMap`.
3. `System.gc()` requests a collection cycle; the garbage collector traces reachability from GC roots (including live threads and their `ThreadLocalMap`s) and finds `buffer` is still strongly reachable via the pool thread — so it is *not* collected, and `tracker[0].get()` still returns the object afterward.
4. In `ProperCleanupFixesTheLeak`, the identical setup instead wraps the work in `try { ... } finally { TASK_BUFFER.remove(); }` — `remove()` deletes the entry from the pool thread's `ThreadLocalMap` entirely, severing the strong-reference chain from the thread to `buffer`.
5. Once that entry is removed, nothing in the entire application (not the pool thread, not any application code) holds a strong reference to `buffer` anymore — only the `WeakReference` in `tracker` does, which doesn't count for reachability purposes.
6. `System.gc()` this time finds `buffer` is *not* reachable from any GC root, and collects it — `tracker[0].get()` afterward correctly returns `null`, confirming the object was reclaimed exactly because the `ThreadLocal` entry was properly cleaned up.

## 7. Gotchas & takeaways

> **Gotcha:** overwriting a `ThreadLocal` with `set(null)` is **not** the same as calling `remove()` — `set(null)` still leaves an entry in the thread's `ThreadLocalMap` (just holding `null` as its value), whereas `remove()` deletes the entry itself. For most single-object leaks this distinction barely matters memory-wise (a `null` reference doesn't keep the *old* large object alive), but `remove()` is still the semantically correct and idiomatic way to signal "this thread is done with this variable," and matters more if the `ThreadLocal` value type itself has significant retained structure beyond the immediate reference.

- `ThreadLocal` memory leaks occur specifically on long-lived, pooled threads — a `set()` without a matching `remove()` keeps the stored value (and anything it references) alive for as long as that pool thread exists, regardless of whether the originating task has long since finished.
- Always pair every `set()` on a value that a pooled thread might handle with a `remove()` in a `finally` block, guaranteeing cleanup even if the task's own work throws an exception.
- The leak is invisible in short-lived-thread scenarios (a plain `new Thread(...).start()` that runs once and terminates) — it's strictly a consequence of thread reuse, making `ExecutorService`-based code the primary risk area.
- In application servers specifically, `ThreadLocal` leaks holding references to a web application's own classes/classloader are a notorious, historically significant cause of "classloader leaks" that prevent memory from being reclaimed even after redeploying or undeploying an application.
- When designing new per-thread context propagation, especially alongside virtual threads, consider whether [scoped values](0904-scoped-values.md) — which are inherently bound to a well-defined lexical scope and cannot outlive it — might sidestep this entire class of leak by construction, rather than relying on programmer discipline to always remember `remove()`.
