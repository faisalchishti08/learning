---
card: java
gi: 891
slug: cas-compare-and-swap
title: CAS (compare-and-swap)
---

## 1. What it is

Compare-and-swap (CAS) is a single, hardware-supported atomic instruction: "read the current value of a memory location, and if it still equals the expected value, replace it with a new value — all as one indivisible operation." If another thread changed the value in between your read and your attempted write, the CAS simply fails (returns `false` or leaves the value unchanged), and you can detect that and retry. This is the low-level primitive underlying every class in `java.util.concurrent.atomic` (`AtomicInteger`, `AtomicLong`, `AtomicReference`, and friends) — it's how they achieve thread-safe updates *without* using locks at all.

## 2. Why & when

CAS matters because it enables **lock-free** algorithms: instead of a thread blocking (and potentially being descheduled while holding a lock, stalling every other thread that needs it), a thread attempting a CAS-based update simply retries in a loop if it loses the race, and crucially, some other thread's CAS necessarily *succeeded* in that same window — meaning the system as a whole always makes progress, even if any single thread occasionally has to retry. This matters for high-contention counters, flags, and references where lock overhead (context switching, potential priority inversion, or lock convoy effects) would hurt throughput more than the cost of an occasional CAS retry. You rarely write raw CAS loops yourself in application code — `AtomicInteger.incrementAndGet()` and friends already wrap this pattern correctly — but understanding it explains *why* those classes work, why they're a good building block, and what problem (the [ABA problem](0896-aba-problem-atomicstampedreference.md)) can arise from misusing them.

## 3. Core concept

```java
// The classic CAS-retry loop pattern, made explicit (this is essentially what
// AtomicInteger.incrementAndGet() does internally):
AtomicInteger counter = new AtomicInteger(0);

int oldValue, newValue;
do {
    oldValue = counter.get();               // read current value
    newValue = oldValue + 1;                // compute the new value based on it
} while (!counter.compareAndSet(oldValue, newValue)); // atomically swap IF unchanged; else retry
```

If another thread updated `counter` between the `get()` and the `compareAndSet()`, the CAS fails, the loop retries with a fresh read — no lock, no blocking, just a retry against the latest value.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads racing to CAS-update the same counter; the first thread's CAS succeeds, the second thread's CAS fails because the value changed, so it retries with a fresh read">
  <text x="320" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">counter starts at 5</text>

  <rect x="20" y="35" width="260" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">T1 reads 5, computes 6</text>
  <rect x="340" y="35" width="260" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="470" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">T2 reads 5, computes 6</text>

  <rect x="20" y="80" width="260" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">T1 CAS(5-&gt;6) SUCCEEDS</text>
  <rect x="340" y="80" width="260" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="470" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">T2 CAS(5-&gt;6) FAILS -- value is now 6, not 5</text>

  <rect x="340" y="125" width="260" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="470" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">T2 RETRIES: reads 6, computes 7, CAS succeeds</text>
  <line x1="470" y1="110" x2="470" y2="123" stroke="#8b949e" stroke-width="2" marker-end="url(#a25)"/>
  <defs><marker id="a25" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Only one of the two racing threads' CAS can succeed at a time; the loser simply retries with a fresh read — the final result (7) is correct with no lost update, and no lock was ever taken.*

## 5. Runnable example

Scenario: a shared counter under contention, growing from a synchronized (lock-based) version, to an explicit CAS-retry-loop version demonstrating the mechanism directly, to using `AtomicInteger`'s built-in atomic methods (which do exactly this internally) for the idiomatic, production version.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class LockBasedCounter {
    static int counter = 0;
    static final Object lock = new Object();

    static void increment() {
        synchronized (lock) {
            counter++;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(8);
        for (int i = 0; i < 100_000; i++) pool.submit(LockBasedCounter::increment);
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("counter = " + counter + " (correct, but every increment took a lock)");
    }
}
```

**How to run:** `java LockBasedCounter.java` (JDK 17+).

Expected output:
```
counter = 100000 (correct, but every increment took a lock)
```

Correct, but every single increment requires acquiring and releasing a lock — under heavy contention, this means threads blocking and potentially being descheduled while waiting.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class ExplicitCasRetryLoop {
    static AtomicInteger counter = new AtomicInteger(0);

    static void increment() {
        int oldValue, newValue;
        do {
            oldValue = counter.get();          // read
            newValue = oldValue + 1;           // compute
        } while (!counter.compareAndSet(oldValue, newValue)); // atomically swap IF unchanged, else retry
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(8);
        for (int i = 0; i < 100_000; i++) pool.submit(ExplicitCasRetryLoop::increment);
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("counter = " + counter.get() + " (correct, lock-free, via explicit CAS retry loop)");
    }
}
```

**How to run:** `java ExplicitCasRetryLoop.java`.

Expected output:
```
counter = 100000 (correct, lock-free, via explicit CAS retry loop)
```

The real-world concern added: making the CAS mechanism explicit — no thread ever blocks waiting for a lock; instead, a thread whose CAS fails (because another thread's CAS won the race first) simply loops back, re-reads the now-current value, recomputes, and tries again, until its own CAS eventually succeeds.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class IdiomaticAtomicMethods {
    static AtomicInteger counter = new AtomicInteger(0);
    static AtomicInteger casRetryEstimate = new AtomicInteger(0); // just for illustrating contention exists

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(8);

        for (int i = 0; i < 100_000; i++) {
            pool.submit(() -> {
                // incrementAndGet() does EXACTLY the get/compute/compareAndSet retry loop
                // from Level 2 internally -- this is the idiomatic way to write it in real code.
                counter.incrementAndGet();
            });
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("counter = " + counter.get() + " (idiomatic, same lock-free guarantee)");

        // updateAndGet lets you express an arbitrary CAS-retry-based update, e.g. "double, capped at 1000":
        AtomicInteger capped = new AtomicInteger(600);
        int result = capped.updateAndGet(v -> Math.min(v * 2, 1000));
        System.out.println("capped update result: " + result + " (600*2=1200, capped to 1000)");
    }
}
```

**How to run:** `java IdiomaticAtomicMethods.java`.

Expected output:
```
counter = 100000 (idiomatic, same lock-free guarantee)
capped update result: 1000 (600*2=1200, capped to 1000)
```

This adds the production-flavored hard case: recognizing that `AtomicInteger.incrementAndGet()` (and the more general `updateAndGet(IntUnaryOperator)`, which accepts an arbitrary function of the current value) are exactly the CAS-retry-loop pattern from Level 2, already correctly implemented — real code should almost always use these built-in methods rather than hand-writing the loop, since they're equally lock-free, well-tested, and more concise, while `updateAndGet` in particular lets you express arbitrarily complex atomic updates (like the capped-doubling shown) without manually managing the retry loop at all.

## 6. Walkthrough

Tracing a single call to `capped.updateAndGet(v -> Math.min(v * 2, 1000))` when `capped` currently holds `600`:

1. Internally, `updateAndGet` reads the current value of `capped` — `600`.
2. It applies the given function to that value: `Math.min(600 * 2, 1000) = Math.min(1200, 1000) = 1000`.
3. It then attempts a CAS: "if `capped` still equals `600`, atomically set it to `1000`." Since no other thread modified `capped` in this single-threaded example, the CAS succeeds on the first attempt.
4. `updateAndGet` returns the new value, `1000`, which is what gets printed.
5. Had another thread concurrently modified `capped` between steps 1 and 3 (e.g., changing it to `700`), the CAS in step 3 would fail (since the actual current value, `700`, no longer matches the expected `600`) — `updateAndGet` would then automatically retry: re-read the new current value (`700`), recompute the function (`Math.min(1400, 1000) = 1000`), and attempt the CAS again, repeating until it succeeds.
6. This retry-on-failure behavior is entirely internal to `updateAndGet` (and `incrementAndGet`, and every other atomic-update method on the `Atomic*` classes) — calling code never sees or handles a CAS failure directly; it always eventually gets back a definitively-applied new value once its logical CAS attempt succeeds.

## 7. Gotchas & takeaways

> **Gotcha:** a CAS-based retry loop can, in a worst-case scenario, retry indefinitely under extremely heavy, sustained contention (this is called "livelock" at the CAS level) — in practice this is rare for simple operations like increments, but for CAS loops with expensive recomputation logic between the read and the compare-and-swap, high contention can meaningfully hurt throughput compared to a lock that simply queues waiting threads.

- CAS is a single atomic hardware instruction: "if the value is still what I expect, swap it; otherwise, tell me it failed" — the foundation of every lock-free class in `java.util.concurrent.atomic`.
- A CAS-retry loop never blocks a thread the way a lock does — a failed CAS just means "someone else updated it first; read the new value and try again."
- Prefer the built-in methods (`incrementAndGet`, `compareAndSet`, `updateAndGet`, `accumulateAndGet`) over hand-writing your own retry loop — they're already correct, well-tested, and equally lock-free.
- CAS compares by value equality (for primitives) or reference equality (for objects via `AtomicReference`) — a value that changes from A to B and back to A between your read and your CAS attempt is invisible to a simple CAS, a subtlety known as the [ABA problem](0896-aba-problem-atomicstampedreference.md).
- Under extremely high contention with expensive per-attempt computation, a CAS-retry loop's repeated retries can sometimes underperform a well-tuned lock — measure rather than assume lock-free is always faster.
