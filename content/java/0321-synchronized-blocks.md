---
card: java
gi: 321
slug: synchronized-blocks
title: synchronized blocks
---

## 1. What it is

A `synchronized` **block** lets you lock on a specific object for just a portion of a method, rather than the entire method — `synchronized (lockObject) { ... }` only excludes other threads trying to acquire the lock on that *same* `lockObject`, for the duration of the block, giving finer-grained control than marking a whole method `synchronized`.

```java
public class SynchronizedBlockDemo {
    static int counter = 0;
    static final Object lock = new Object();

    static void increment() {
        System.out.println("Doing unrelated work first..."); // NOT synchronized -- no shared state touched here
        synchronized (lock) {
            counter++; // only THIS part needs protection
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread[] threads = new Thread[50];
        for (int i = 0; i < 50; i++) {
            threads[i] = new Thread(SynchronizedBlockDemo::increment);
            threads[i].start();
        }
        for (Thread t : threads) t.join();
        System.out.println("Final counter: " + counter); // reliably 50
    }
}
```

Only the `counter++` line is inside the `synchronized (lock)` block — the `println` before it runs freely, unsynchronized, on every thread simultaneously, while only the actual shared-state mutation is protected, minimizing how much code needs to run one-thread-at-a-time.

## 2. Why & when

A `synchronized` method locks for its **entire** duration, even the parts that don't touch shared state — if a method does significant unrelated work (logging, formatting, I/O) alongside a small critical section that actually needs protection, synchronizing the whole method needlessly serializes all of that unrelated work too, hurting concurrency for no correctness benefit. Synchronized blocks let you lock only what actually needs it.

- **Minimizing the critical section** — locking for as short a time as possible reduces contention, letting more threads make progress concurrently on the parts of the method that don't need protection.
- **Locking on something other than `this`** — sometimes the right lock object isn't the enclosing instance at all, but a dedicated lock object, a different shared resource, or a specific field — a synchronized block can lock on any object you choose, while a synchronized method is always tied to `this` (or the class, for static methods).
- **Protecting multiple related fields together** — when several fields must be updated consistently as a group, a block lets you wrap exactly that group of statements, no more and no less.

Prefer a synchronized block over a synchronized method whenever only part of a method's work touches shared state, or when you need to lock on something other than the enclosing object itself. Always lock on a stable, shared, `final` object reference — never on something that changes or is created anew per call, which (as seen with the `synchronized` methods topic) silently defeats the whole point.

## 3. Core concept

```java
public class SynchronizedBlockCore {
    static class Cache {
        private final Object lock = new Object(); // a dedicated lock object, distinct from `this`
        private String cachedValue;

        String getOrCompute(java.util.function.Supplier<String> computation) {
            synchronized (lock) {
                if (cachedValue == null) {
                    cachedValue = computation.get(); // expensive computation, protected from duplication
                }
                return cachedValue;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Cache cache = new Cache();
        Runnable task = () -> System.out.println(Thread.currentThread().getName() + ": " + cache.getOrCompute(() -> {
            System.out.println(Thread.currentThread().getName() + " computing...");
            return "computed-value";
        }));

        Thread t1 = new Thread(task, "T1");
        Thread t2 = new Thread(task, "T2");
        t1.start();
        t2.start();
        t1.join();
        t2.join();
    }
}
```

`lock` is a dedicated, `final` `Object` created once, specifically to guard `cachedValue` — using a separate lock object (rather than `this`) means other synchronized code on the same `Cache` instance, if any existed, wouldn't be needlessly blocked by cache computation, and vice versa; only one of the two threads will ever actually print "computing...", since the `synchronized` block prevents both from racing into the expensive computation simultaneously.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Only the critical section inside the synchronized block requires exclusive access, work outside it runs freely and concurrently">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="10" font-family="monospace">method: [unsynchronized work] [synchronized(lock){critical section}] [unsynchronized work]</text>
  <rect x="230" y="45" width="180" height="35" rx="4" fill="#1c2430" stroke="#f85149"/>
  <text x="320" y="67" fill="#f85149" font-size="9" text-anchor="middle">only this part excludes other threads</text>
  <text x="20" y="105" fill="#8b949e" font-size="9">Everything outside the synchronized block can run concurrently across as many threads as needed.</text>
</svg>

Only the code physically inside the `synchronized` block is subject to mutual exclusion.

## 5. Runnable example

Scenario: a shared statistics tracker recording measurements from multiple threads, evolved from an overly broad synchronized-method version into a synchronized-block version that minimizes the critical section, then into a version using a dedicated lock object to protect two related fields consistently together.

### Level 1 — Basic

```java
public class SynchronizedBlockBasic {
    static class Stats {
        private int count = 0;
        private double sum = 0;

        synchronized void record(double value) { // entire method synchronized -- coarse-grained
            System.out.println("Recording " + value + " (some setup work here too)");
            count++;
            sum += value;
        }

        synchronized double average() { return count == 0 ? 0 : sum / count; }
    }

    public static void main(String[] args) throws InterruptedException {
        Stats stats = new Stats();
        Thread[] threads = new Thread[10];
        for (int i = 0; i < 10; i++) {
            double value = i + 1;
            threads[i] = new Thread(() -> stats.record(value));
            threads[i].start();
        }
        for (Thread t : threads) t.join();

        System.out.println("Average: " + stats.average());
    }
}
```

**How to run:** `java SynchronizedBlockBasic.java`

Correct, but the entire `record` method — including its `println`, which touches no shared state — runs under the lock, meaning all ten threads' console output is unnecessarily serialized along with the actual data update.

### Level 2 — Intermediate

Same statistics tracker, now using a synchronized block to protect only the actual shared-state update, letting the unrelated `println` work happen freely and concurrently.

```java
public class SynchronizedBlockIntermediate {
    static class Stats {
        private final Object lock = new Object();
        private int count = 0;
        private double sum = 0;

        void record(double value) {
            System.out.println("Recording " + value + " (some setup work here too)"); // unsynchronized, runs freely
            synchronized (lock) {
                count++;
                sum += value;
            }
        }

        double average() {
            synchronized (lock) {
                return count == 0 ? 0 : sum / count;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Stats stats = new Stats();
        Thread[] threads = new Thread[10];
        for (int i = 0; i < 10; i++) {
            double value = i + 1;
            threads[i] = new Thread(() -> stats.record(value));
            threads[i].start();
        }
        for (Thread t : threads) t.join();

        System.out.println("Average: " + stats.average());
    }
}
```

**How to run:** `java SynchronizedBlockIntermediate.java`

The `println` calls from all ten threads can now interleave freely, running concurrently without waiting on each other, while `count++` and `sum += value` remain correctly protected as an atomic pair inside the `synchronized (lock)` block — the final average is identical and correct, but the unrelated work is no longer needlessly serialized.

### Level 3 — Advanced

Same tracker, now adding a `min`/`max` tracking feature that must be updated consistently together with `count`/`sum` — demonstrating a synchronized block correctly protecting a **group** of related fields as one atomic unit, which is precisely the scenario where fine-grained per-field locking (or no locking) would be incorrect.

```java
public class SynchronizedBlockAdvanced {
    static class Stats {
        private final Object lock = new Object();
        private int count = 0;
        private double sum = 0;
        private double min = Double.POSITIVE_INFINITY;
        private double max = Double.NEGATIVE_INFINITY;

        void record(double value) {
            System.out.println("Recording " + value);
            synchronized (lock) { // all four fields updated together, atomically
                count++;
                sum += value;
                if (value < min) min = value;
                if (value > max) max = value;
            }
        }

        String snapshot() {
            synchronized (lock) { // reading all four fields consistently, as of one instant
                if (count == 0) return "no data";
                return String.format("count=%d, avg=%.2f, min=%.2f, max=%.2f", count, sum / count, min, max);
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Stats stats = new Stats();
        double[] values = {3.5, 7.2, 1.1, 9.8, 4.4, 6.6, 2.2, 8.8, 5.5, 0.9};

        Thread[] threads = new Thread[values.length];
        for (int i = 0; i < values.length; i++) {
            double value = values[i];
            threads[i] = new Thread(() -> stats.record(value));
            threads[i].start();
        }
        for (Thread t : threads) t.join();

        System.out.println(stats.snapshot());
    }
}
```

**How to run:** `java SynchronizedBlockAdvanced.java`

Because `count`, `sum`, `min`, and `max` are all updated inside the **same** `synchronized (lock)` block, a `snapshot()` call reading all four (also inside a `synchronized (lock)` block) will never see an inconsistent combination — like a `count` that's already been incremented but a `sum` that hasn't yet reflected the corresponding value — since no other thread can be mid-update while `snapshot` holds the lock.

## 6. Walkthrough

Trace two threads racing to call `record` in `SynchronizedBlockAdvanced`, step by step, focusing on why grouping the four fields together matters.

**Thread A calls `record(9.8)`.** It prints its message (unsynchronized, runs immediately). It then enters `synchronized (lock)`: `count++` (say, from 4 to 5), `sum += 9.8`, and since `9.8` is larger than the current `max`, `max = 9.8`. All three field updates happen while Thread A exclusively holds `lock` — no other thread can be inside this block or `snapshot()`'s block at the same time.

**Thread B calls `snapshot()` at nearly the same moment.** It attempts `synchronized (lock)` — if Thread A currently holds the lock (mid-update), Thread B blocks until Thread A's block finishes completely. This is the crucial guarantee: Thread B can never observe a state where, say, `count` has already been incremented to 5 but `max` hasn't yet been updated to reflect `9.8` — it either sees the state entirely *before* Thread A's update (count=4, old max) or entirely *after* (count=5, max=9.8), never a mixture of the two.

**Why this matters for correctness.** If `count`, `sum`, `min`, and `max` were protected by *separate* locks (or not grouped into one block at all), a reader could observe `count` already incremented while `max` still holds its old value — a genuinely inconsistent snapshot that doesn't correspond to any single, real moment in the program's actual history. Grouping all four updates (and all four reads) under the same lock is what prevents this.

**All ten threads eventually complete.** Each one's `record` call fully executes its `synchronized` block before any other thread's block can begin (for calls that overlap in time) — over all ten calls, `count` ends at 10, `sum` reflects the sum of all ten values, and `min`/`max` correctly reflect the smallest (0.9) and largest (9.8) values across the whole set, regardless of the actual order in which the ten threads happened to execute.

```
record(9.8) by Thread A:                    snapshot() by Thread B:
  synchronized(lock) {                        synchronized(lock) {
    count++        (4 -> 5)                     -- blocks here if A holds the lock --
    sum += 9.8                                   read count, sum, min, max
    max = 9.8       (since 9.8 > old max)         -- always a CONSISTENT combination
  }                                            }
```

**Output (illustrative — exact "Recording" order varies by run, but the final snapshot is deterministic):**
```
Recording 3.5
Recording 7.2
...
count=10, avg=5.00, min=0.90, max=9.80
```

## 7. Gotchas & takeaways

> A synchronized block only protects fields that are **actually accessed inside it**. If `min`/`max` were read or written anywhere else in the class *outside* a `synchronized (lock)` block — even just for a quick, seemingly harmless read — that access would race against the protected updates, undermining the whole guarantee. Every access to state guarded by a particular lock must go through that same lock, consistently, everywhere in the class.

> The lock object itself (`lock` in these examples) should be `final` and never reassigned — if a new `Object` could ever be assigned to `lock` after some threads have already captured a reference to the old one, different threads could end up synchronizing on different objects, silently breaking mutual exclusion exactly like the "wrong lock" mistake covered for synchronized methods.

- `synchronized (lockObject) { ... }` locks only for the block's duration and only on the specified object, offering finer control than synchronizing an entire method.
- Minimize the code inside a synchronized block to reduce contention — only the actual shared-state access needs protection.
- A dedicated, `final` lock object (rather than always using `this`) lets you choose exactly what's being protected, independent of the enclosing object's own locking.
- When multiple related fields must stay consistent with each other, protect all reads and writes of that whole group under the same lock — protecting them separately can still allow inconsistent, "torn" reads.
