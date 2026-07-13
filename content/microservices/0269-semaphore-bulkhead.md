---
card: microservices
gi: 269
slug: semaphore-bulkhead
title: "Semaphore bulkhead"
---

## 1. What it is

A semaphore bulkhead is a [bulkhead](0267-bulkhead-pattern.md) implemented using a counting semaphore rather than a dedicated thread pool — the protected call still executes on the caller's own thread, but a semaphore limits how many callers can be inside the protected call simultaneously, rejecting any caller that arrives once the permitted concurrency limit is already reached.

## 2. Why & when

A [thread-pool bulkhead](0268-thread-pool-bulkhead.md) provides strong isolation by moving execution to separate threads, but that thread hand-off has real overhead — for a call that's fast and non-blocking (a reactive, asynchronous call already running on an event loop, for instance), submitting it to yet another thread pool just to bound its concurrency adds unnecessary context-switching cost for no additional benefit, since the call was never going to tie up the caller's thread in a blocking way regardless. A semaphore bulkhead achieves the same concurrency-limiting protection — capping how many calls to a specific dependency can be in flight at once — without the overhead of thread hand-off, since the call still runs on whichever thread the caller was already using; the semaphore's only job is deciding, cheaply, whether to allow the call to proceed at all.

Use a semaphore bulkhead for calls that are fast, non-blocking, or already running in a reactive/asynchronous execution model, where the overhead of a separate thread pool would be unnecessary and where you want to cap concurrency without the added complexity of managing a dedicated `ExecutorService`.

## 3. Core concept

A semaphore bulkhead acquires a permit from a fixed-size semaphore before proceeding with the protected call, releasing it when the call completes (successfully or not); a caller arriving when no permits are available is rejected immediately (or, depending on configuration, waits briefly up to a maximum wait duration) — the call itself always runs on the calling thread, never handed off elsewhere.

```java
Semaphore bulkheadPermits = new Semaphore(10); // caps CONCURRENT calls to 10, no dedicated thread pool involved

<T> T callWithSemaphoreBulkhead(Supplier<T> operation) {
    if (!bulkheadPermits.tryAcquire()) {
        throw new BulkheadFullException("bulkhead at capacity, call rejected"); // REJECTED immediately, cheap check
    }
    try {
        return operation.get(); // executes on THIS SAME thread -- no hand-off to another pool
    } finally {
        bulkheadPermits.release(); // ALWAYS release, whether the call succeeded or threw
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A caller thread acquires a permit from a semaphore before proceeding, executes the protected call directly on its own thread without any hand-off, and releases the permit when finished -- a caller arriving when no permits remain is rejected immediately" >
  <rect x="20" y="65" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Caller thread</text>

  <rect x="220" y="65" width="150" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="295" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Semaphore (permits)</text>
  <text x="295" y="102" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">acquire / release</text>

  <rect x="450" y="65" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="525" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Call runs on SAME thread</text>

  <line x1="150" y1="87" x2="218" y2="87" stroke="#8b949e" marker-end="url(#arr269)"/>
  <line x1="370" y1="87" x2="448" y2="87" stroke="#8b949e" marker-end="url(#arr269)"/>

  <defs>
    <marker id="arr269" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

No thread hand-off occurs — the semaphore only decides whether the caller's own thread is permitted to proceed.

## 5. Runnable example

Scenario: a fast, non-blocking call protected unnecessarily by a thread-pool bulkhead (paying hand-off overhead for no real benefit), refactored to a semaphore bulkhead achieving the identical concurrency cap without that overhead, and finally comparing measured overhead directly between the two approaches for a high-volume, fast call pattern, quantifying the cost difference concretely.

### Level 1 — Basic

```java
// File: ThreadPoolForFastCall.java -- uses a THREAD POOL to protect a
// FAST, non-blocking call -- paying HAND-OFF overhead for a call that
// never needed it.
import java.util.concurrent.*;

public class ThreadPoolForFastCall {
    static ExecutorService threadPoolBulkhead = Executors.newFixedThreadPool(10);

    static String fastNonBlockingCall() { return "result"; } // genuinely FAST -- no blocking I/O at all

    public static void main(String[] args) throws Exception {
        int callCount = 10000;
        long start = System.nanoTime();
        for (int i = 0; i < callCount; i++) {
            Future<String> future = threadPoolBulkhead.submit(ThreadPoolForFastCall::fastNonBlockingCall); // HAND-OFF to another thread
            future.get(); // wait for it -- paying the FULL round-trip cost, for a call that took NO time itself
        }
        long elapsedMillis = (System.nanoTime() - start) / 1_000_000;
        System.out.println(callCount + " fast calls via THREAD POOL bulkhead: " + elapsedMillis + "ms total");
        threadPoolBulkhead.shutdown();
    }
}
```

**How to run:** `javac ThreadPoolForFastCall.java && java ThreadPoolForFastCall` (JDK 17+).

### Level 2 — Intermediate

```java
// File: SemaphoreForFastCall.java -- the SAME concurrency cap, via a
// SEMAPHORE -- the call runs DIRECTLY on the caller's OWN thread, NO
// hand-off overhead.
import java.util.concurrent.*;

public class SemaphoreForFastCall {
    static Semaphore semaphoreBulkhead = new Semaphore(10); // the SAME "10 concurrent" cap as Level 1's pool size

    static String fastNonBlockingCall() { return "result"; }

    static String callWithSemaphoreBulkhead() {
        if (!semaphoreBulkhead.tryAcquire()) throw new RuntimeException("bulkhead full");
        try {
            return fastNonBlockingCall(); // runs DIRECTLY here -- no thread hand-off AT ALL
        } finally {
            semaphoreBulkhead.release();
        }
    }

    public static void main(String[] args) {
        int callCount = 10000;
        long start = System.nanoTime();
        for (int i = 0; i < callCount; i++) {
            callWithSemaphoreBulkhead(); // NO Future, NO submit -- runs INLINE, on the SAME thread
        }
        long elapsedMillis = (System.nanoTime() - start) / 1_000_000;
        System.out.println(callCount + " fast calls via SEMAPHORE bulkhead: " + elapsedMillis + "ms total");
    }
}
```

**How to run:** `javac SemaphoreForFastCall.java && java SemaphoreForFastCall` (JDK 17+).

Expected output (both approaches complete, but semaphore is dramatically faster for this call pattern):
```
10000 fast calls via SEMAPHORE bulkhead: 3ms total
```

### Level 3 — Advanced

```java
// File: DirectOverheadComparison.java -- runs BOTH approaches back to
// back against the IDENTICAL fast-call workload, printing a DIRECT,
// measured comparison of the hand-off overhead.
import java.util.concurrent.*;

public class DirectOverheadComparison {
    static ExecutorService threadPoolBulkhead = Executors.newFixedThreadPool(10);
    static Semaphore semaphoreBulkhead = new Semaphore(10);
    static String fastNonBlockingCall() { return "result"; }

    static long measureThreadPoolApproach(int callCount) throws Exception {
        long start = System.nanoTime();
        for (int i = 0; i < callCount; i++) {
            Future<String> future = threadPoolBulkhead.submit(DirectOverheadComparison::fastNonBlockingCall);
            future.get();
        }
        return (System.nanoTime() - start) / 1_000_000;
    }

    static long measureSemaphoreApproach(int callCount) {
        long start = System.nanoTime();
        for (int i = 0; i < callCount; i++) {
            if (!semaphoreBulkhead.tryAcquire()) continue;
            try { fastNonBlockingCall(); } finally { semaphoreBulkhead.release(); }
        }
        return (System.nanoTime() - start) / 1_000_000;
    }

    public static void main(String[] args) throws Exception {
        int callCount = 20000;
        long threadPoolTime = measureThreadPoolApproach(callCount);
        long semaphoreTime = measureSemaphoreApproach(callCount);

        System.out.println("Thread-pool bulkhead: " + threadPoolTime + "ms for " + callCount + " fast calls");
        System.out.println("Semaphore bulkhead: " + semaphoreTime + "ms for " + callCount + " fast calls");
        System.out.println("\nFor a FAST, non-blocking call, the semaphore approach avoids the hand-off overhead entirely --");
        System.out.println("roughly " + (threadPoolTime / Math.max(semaphoreTime, 1)) + "x less overhead in this measurement.");
        threadPoolBulkhead.shutdown();
    }
}
```

**How to run:** `javac DirectOverheadComparison.java && java DirectOverheadComparison` (JDK 17+).

Expected output (exact numbers vary by machine, but the qualitative gap is consistent and significant):
```
Thread-pool bulkhead: 850ms for 20000 fast calls
Semaphore bulkhead: 5ms for 20000 fast calls

For a FAST, non-blocking call, the semaphore approach avoids the hand-off overhead entirely --
roughly 170x less overhead in this measurement.
```

## 6. Walkthrough

1. **Level 1, the hand-off cost for every single fast call** — each iteration calls `threadPoolBulkhead.submit(...)`, which queues the call for execution on a separate thread, and then `future.get()`, which blocks the calling thread until that separate thread picks up and completes the (essentially instantaneous) work; even though `fastNonBlockingCall` itself does almost nothing, every single call pays the overhead of thread scheduling, context switching, and inter-thread communication involved in the submit-and-wait cycle.
2. **Level 2, bypassing the hand-off entirely** — `callWithSemaphoreBulkhead` calls `fastNonBlockingCall()` directly, inline, on whatever thread is currently executing `main`'s loop; the semaphore's `tryAcquire`/`release` calls are cheap, in-memory operations that don't involve any thread scheduling or hand-off at all.
3. **Level 2, the same concurrency guarantee, without the cost** — `semaphoreBulkhead`, initialized with 10 permits, provides the identical "at most 10 concurrent calls" guarantee as Level 1's 10-thread pool would under genuinely concurrent access, but here, running sequentially in a single-threaded loop for the demo, the semaphore's overhead is negligible compared to the thread pool's submit-and-wait machinery.
4. **Level 3, measuring both approaches against the identical workload** — `measureThreadPoolApproach` and `measureSemaphoreApproach` both run `fastNonBlockingCall` 20000 times, using their respective bulkhead mechanisms, with elapsed time measured precisely around each approach's full loop.
5. **Level 3, the dramatic, measured overhead gap** — the printed results show the thread-pool approach taking hundreds of milliseconds for 20000 calls, while the semaphore approach completes the identical 20000 calls in a handful of milliseconds — a difference of one or two orders of magnitude, entirely attributable to the thread-pool approach's per-call submission, scheduling, and cross-thread result-retrieval overhead, none of which the semaphore approach incurs.
6. **Level 3, the concrete lesson this measurement supports** — this gap is specifically pronounced *because* `fastNonBlockingCall` does essentially no real work — for a genuinely slow, blocking call (as in the [thread-pool bulkhead](0268-thread-pool-bulkhead.md) topic's own examples), the thread-pool approach's overhead becomes comparatively negligible next to the call's own duration, and its thread-isolation benefit becomes the dominant consideration instead; the choice between semaphore and thread-pool bulkheads should be driven by whether the protected call is fast/non-blocking (favoring semaphore, as measured here) or slow/blocking (favoring thread-pool, for its stronger isolation), not applied as a one-size-fits-all default in either direction.

## 7. Gotchas & takeaways

> **Gotcha:** because a semaphore bulkhead runs the protected call on the caller's own thread with no isolation between threads, a call that unexpectedly *does* block for a long time (despite being assumed fast) will tie up the calling thread directly, exactly the problem a thread-pool bulkhead is specifically designed to avoid — a semaphore bulkhead's concurrency cap protects against too many *simultaneous* calls, but provides no protection against any individual call blocking the calling thread if that call turns out to be slower than assumed.

- A semaphore bulkhead limits concurrent calls to a dependency using a counting semaphore, with the protected call still executing directly on the caller's own thread — no hand-off to a separate pool.
- This avoids the thread-scheduling and context-switching overhead a thread-pool bulkhead incurs, which matters significantly for fast, high-volume, non-blocking calls, as directly measured in this example.
- The concurrency-limiting guarantee itself is equivalent between the two approaches — both cap "at most N concurrent calls to this dependency" — differing only in implementation mechanism and overhead characteristics.
- Semaphore bulkheads suit fast, non-blocking, or already-asynchronous calls; [thread-pool bulkheads](0268-thread-pool-bulkhead.md) suit slow, blocking calls where isolating the caller's own thread specifically matters.
- A semaphore bulkhead provides no protection against an individual call blocking the calling thread — if a call assumed to be fast turns out to block unexpectedly, that blocking directly affects the caller, unlike with a thread-pool bulkhead's stronger thread-level isolation.
