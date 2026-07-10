---
card: java
gi: 897
slug: threadlocal
title: ThreadLocal
---

## 1. What it is

`ThreadLocal<T>` gives each thread its own independent, private copy of a variable — calling `get()`/`set()` on the same `ThreadLocal` instance from different threads reads and writes completely separate values, with no sharing and therefore no need for any synchronization at all between them. Internally, each `Thread` object carries its own small map from `ThreadLocal` instances to values; a `ThreadLocal.get()` call looks up the value in the *calling* thread's own map, never anyone else's.

## 2. Why & when

Use `ThreadLocal` when you need per-thread state that would otherwise require passing an extra parameter through every method call in a chain — the classic example is a per-request context object (a `SimpleDateFormat` instance, since it's famously not thread-safe and expensive to create; a user/session context for the current request in a web server handling many requests on a pool of threads; a per-thread database connection or transaction handle). Rather than threading that context as an explicit parameter through dozens of method signatures, you store it in a `ThreadLocal` and any code running on that same thread can retrieve it via `get()` without it needing to be passed around at all. This works especially well with thread-per-request server models, where each incoming request is handled start-to-finish on one dedicated thread — but requires real care with thread *pools*, where a "thread" outlives any single request and can leak stale data into the next one unless explicitly cleaned up.

## 3. Core concept

```java
static final ThreadLocal<SimpleDateFormat> DATE_FORMAT =
    ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd")); // one instance PER THREAD, created lazily

String formatted = DATE_FORMAT.get().format(new Date()); // each thread gets its OWN SimpleDateFormat, never shared
```

`SimpleDateFormat` is not thread-safe, but since each thread has its own private instance (created once per thread via the lazy initializer, then reused), there's no possibility of two threads corrupting each other's formatting state, and no synchronization overhead either.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One ThreadLocal variable accessed by three different threads, each seeing its own independent, private value with no sharing between them">
  <rect x="240" y="20" width="160" height="35" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ThreadLocal&lt;T&gt; variable</text>

  <rect x="20" y="90" width="150" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Thread 1: value = X</text>
  <rect x="245" y="90" width="150" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Thread 2: value = Y</text>
  <rect x="470" y="90" width="150" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="545" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Thread 3: value = Z</text>

  <line x1="290" y1="55" x2="120" y2="88" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a29)"/>
  <line x1="320" y1="55" x2="320" y2="88" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a29)"/>
  <line x1="350" y1="55" x2="520" y2="88" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a29)"/>

  <text x="320" y="155" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Same variable reference, three completely independent values -- no sharing, no synchronization needed.</text>
  <defs><marker id="a29" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Each thread's `get()`/`set()` calls on the same `ThreadLocal` reference operate on that thread's own, entirely separate value.*

## 5. Runnable example

Scenario: formatting dates and carrying a per-request context across a simulated thread-pool-based server, growing from an unsafe shared instance, to `ThreadLocal` for safe per-thread instances, to a realistic pooled-thread scenario demonstrating the stale-data leak risk and the `remove()` fix.

### Level 1 — Basic

```java
import java.text.*;
import java.util.*;
import java.util.concurrent.*;

public class SharedDateFormatBug {
    static SimpleDateFormat sharedFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss"); // NOT thread-safe, shared

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(8);
        Set<String> results = ConcurrentHashMap.newKeySet();

        for (int i = 0; i < 100; i++) {
            final long time = System.currentTimeMillis() + i * 1000L;
            pool.submit(() -> {
                String formatted = sharedFormat.format(new Date(time)); // RACE on shared, mutable internal state
                results.add(formatted);
            });
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("distinct results: " + results.size() + " (expected 100 -- fewer or malformed values indicate corruption)");
    }
}
```

**How to run:** `java SharedDateFormatBug.java` (JDK 17+).

Expected output shape (may show fewer than 100 distinct results, or occasionally throw an exception, since `SimpleDateFormat` is documented as not thread-safe):
```
distinct results: 94 (expected 100 -- fewer or malformed values indicate corruption)
```

`SimpleDateFormat.format()` mutates internal state (a shared `Calendar` instance) during formatting — concurrent calls from multiple threads on the *same* instance can corrupt each other's in-progress formatting, producing wrong or duplicate results.

### Level 2 — Intermediate

```java
import java.text.*;
import java.util.*;
import java.util.concurrent.*;

public class ThreadLocalDateFormat {
    static final ThreadLocal<SimpleDateFormat> FORMAT =
        ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd HH:mm:ss"));

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(8);
        Set<String> results = ConcurrentHashMap.newKeySet();

        for (int i = 0; i < 100; i++) {
            final long time = System.currentTimeMillis() + i * 1000L;
            pool.submit(() -> {
                String formatted = FORMAT.get().format(new Date(time)); // each thread's OWN SimpleDateFormat instance
                results.add(formatted);
            });
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("distinct results: " + results.size() + " (correctly 100 -- no cross-thread interference)");
    }
}
```

**How to run:** `java ThreadLocalDateFormat.java`.

Expected output:
```
distinct results: 100 (correctly 100 -- no cross-thread interference)
```

The real-world concern added: each of the 8 pool threads gets its own private `SimpleDateFormat` instance (created once, lazily, the first time that thread calls `FORMAT.get()`, then reused for every subsequent call on that same thread) — no two threads ever touch the same `SimpleDateFormat` object, eliminating the corruption entirely with no synchronization needed.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class PooledThreadLeakAndFix {
    // Per-request context -- simulates something like a request ID or user session
    static final ThreadLocal<String> REQUEST_CONTEXT = new ThreadLocal<>(); // no default -- null until set()

    static void handleRequest(int requestId, boolean cleanupProperly) {
        REQUEST_CONTEXT.set("request-" + requestId);
        try {
            processRequest();
        } finally {
            if (cleanupProperly) {
                REQUEST_CONTEXT.remove(); // ESSENTIAL for pooled threads -- clears this thread's stored value
            }
            // if NOT cleaned up, the next request handled on this SAME pooled thread
            // could incorrectly see a STALE value left over from a PREVIOUS, unrelated request.
        }
    }

    static void processRequest() {
        // Some deep call, far from where the context was set, retrieving it WITHOUT it being passed as a parameter
        String context = REQUEST_CONTEXT.get();
        // (would do real work using `context` here)
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(1); // single thread, REUSED across "requests"
        AtomicInteger staleReadsDetected = new AtomicInteger(0);

        // First "request" WITHOUT cleanup -- leaves stale state behind on the pooled thread
        pool.submit(() -> handleRequest(1, false)).get(1, TimeUnit.SECONDS);

        // Second "request", same pooled thread -- check if it incorrectly inherits request 1's context
        Future<?> leakCheck = pool.submit(() -> {
            String leftover = REQUEST_CONTEXT.get(); // should be null for a FRESH request, but isn't, without cleanup
            if ("request-1".equals(leftover)) {
                staleReadsDetected.incrementAndGet();
                System.out.println("LEAK: request 2 saw stale context from request 1: " + leftover);
            }
            REQUEST_CONTEXT.remove(); // clean up now, properly, before the next real request
        });

        try { leakCheck.get(1, TimeUnit.SECONDS); } catch (Exception e) { /* ignore for demo */ }

        // Third "request" WITH proper cleanup this time -- should see a clean slate
        pool.submit(() -> handleRequest(3, true)).get(1, TimeUnit.SECONDS);
        Future<?> cleanCheck = pool.submit(() -> {
            String shouldBeNull = REQUEST_CONTEXT.get();
            System.out.println("after proper cleanup, context = " + shouldBeNull + " (expected null)");
        });
        try { cleanCheck.get(1, TimeUnit.SECONDS); } catch (Exception e) { /* ignore for demo */ }

        pool.shutdown();
        System.out.println("stale reads detected: " + staleReadsDetected.get() + " (demonstrates the leak risk without remove())");
    }
}
```

**How to run:** `java PooledThreadLeakAndFix.java`.

Expected output:
```
LEAK: request 2 saw stale context from request 1: request-1
after proper cleanup, context = null (expected null)
stale reads detected: 1 (demonstrates the leak risk without remove())
```

This adds the production-flavored hard case: a **pooled** thread (not a fresh thread per task) reused across multiple simulated "requests." Because a thread pool's threads are long-lived and reused, `ThreadLocal` values set during one task **persist** into the next task run on that same thread unless explicitly cleared via `remove()` — demonstrated concretely by request 2 incorrectly observing request 1's leftover context. The fix (calling `REQUEST_CONTEXT.remove()` in a `finally` block, as `handleRequest(3, true)` does) ensures each new task starts with a clean slate, regardless of what any previous task on that same pooled thread happened to leave behind.

## 6. Walkthrough

Tracing the leak scenario in `PooledThreadLeakAndFix.main`:

1. `pool.submit(() -> handleRequest(1, false))` runs on the pool's single worker thread. `handleRequest` calls `REQUEST_CONTEXT.set("request-1")`, storing that string into *this specific thread's* private `ThreadLocal` storage map. Because `cleanupProperly` is `false`, the `finally` block skips calling `remove()`.
2. The task returns, but the pool's worker thread itself does **not** get destroyed or reset — it simply becomes idle, waiting for the next submitted task, with its `ThreadLocal` storage map still containing `REQUEST_CONTEXT -> "request-1"`.
3. The second submitted task runs on that *same* worker thread (since the pool has only one thread) and calls `REQUEST_CONTEXT.get()` — because `ThreadLocal.get()` looks up the value in the *calling thread's* own storage, and this is literally the same thread as before, it retrieves the leftover `"request-1"` value, even though this task has nothing to do with request 1.
4. The check `"request-1".equals(leftover)` correctly detects this as a leak, increments `staleReadsDetected`, and prints the warning — this is the exact bug that occurs in real thread-pool-based servers when per-request `ThreadLocal` state isn't cleaned up.
5. That same task then calls `REQUEST_CONTEXT.remove()` to clean up before returning, so the leaked state doesn't propagate further.
6. The third submitted task calls `handleRequest(3, true)` — this time, `cleanupProperly` is `true`, so its `finally` block calls `REQUEST_CONTEXT.remove()` after processing, clearing the thread's storage for that key entirely (not just overwriting it with `null`, but removing the entry).
7. The final check task calls `REQUEST_CONTEXT.get()` and correctly observes `null`, since `remove()` was properly called after request 3 — demonstrating that disciplined cleanup (always in a `finally` block, symmetric with every `set()`) prevents the exact kind of cross-task data leakage that a naive, thread-per-request mental model (which doesn't hold for pooled threads) would otherwise miss.

## 7. Gotchas & takeaways

> **Gotcha:** in any thread-pool-based system (which is the overwhelmingly common case for real servers), a `ThreadLocal.set()` without a matching `remove()` leaks that value into whatever *next* task happens to run on the same pooled thread — this is a genuine, historically common source of subtle, hard-to-reproduce bugs (and even security issues, if sensitive per-request data like an authenticated user ID leaks into a subsequent, unrelated request) in real production systems.

- `ThreadLocal<T>` gives each thread its own independent copy of a variable — no sharing, no synchronization needed between threads for accessing it.
- Ideal for per-thread state that would otherwise need to be threaded as an explicit parameter through many layers of method calls — per-thread formatters, per-request contexts, per-thread connections.
- In any thread-pool-based system, always pair every `set()` with a `remove()` in a `finally` block — pooled threads are reused across many logically distinct tasks, and a forgotten `remove()` leaks state from one task into the next.
- `ThreadLocal.withInitial(Supplier<T>)` provides a lazy per-thread default, computed once per thread on first access, rather than requiring every thread to explicitly `set()` a value before its first `get()`.
- `ThreadLocal` does not solve any concurrency problem about *shared* state — it deliberately avoids sharing altogether; if threads genuinely need to communicate or share data, `ThreadLocal` is the wrong tool entirely, and an appropriate shared, synchronized structure (or one of the [atomic classes](0892-atomicinteger-atomiclong-atomicreference.md)) is needed instead.
