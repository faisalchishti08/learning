---
card: java
gi: 412
slug: atomic-types-atomicinteger-atomiclong-atomicreference
title: Atomic types (AtomicInteger, AtomicLong, AtomicReference)
---

## 1. What it is

The `java.util.concurrent.atomic` classes — `AtomicInteger`, `AtomicLong`, `AtomicReference<V>`, and others — wrap a single value and provide thread-safe operations on it **without using locks**. Instead, they rely on the CPU's compare-and-swap (CAS) instruction: `compareAndSet(expected, newValue)` atomically checks "is the current value still what I expect?" and, if so, updates it — all in one indivisible hardware-level step. Convenience methods like `incrementAndGet()`, `addAndGet(delta)`, and `updateAndGet(function)` build on this to make common patterns simple to write correctly.

## 2. Why & when

A plain `int` counter shared across threads (`count++`) is not thread-safe — `++` is actually three separate steps (read, increment, write), and two threads can interleave those steps and lose an update. The traditional fix is `synchronized` or a `ReentrantLock` around the increment, but that means every increment pays the cost of acquiring and releasing a lock, and threads must wait in line even for a trivially fast operation.

Atomic classes give you the same correctness without a lock: `incrementAndGet()` performs the read-modify-write as one atomic CAS operation, retrying automatically (in a tight loop, invisibly) if another thread's CAS won the race first. For simple, single-variable state — counters, flags, a single shared reference that gets swapped — this is both simpler to write and typically faster under contention than lock-based alternatives, because there's no thread ever *blocked* waiting; contending threads just retry immediately.

## 3. Core concept

```java
import java.util.concurrent.atomic.AtomicInteger;

AtomicInteger counter = new AtomicInteger(0);

counter.incrementAndGet();               // atomic: read + add 1 + write, as one step
counter.addAndGet(5);                    // atomic: read + add 5 + write
counter.compareAndSet(6, 100);           // atomic: "if current value is still 6, set it to 100" -- true if it succeeded
counter.updateAndGet(current -> current * 2); // atomic: apply an arbitrary function to the current value
```

`compareAndSet` is the primitive everything else builds on: it's how you safely say "update this value, but only if nobody else changed it since I last looked" — the foundation of lock-free programming.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads racing to increment an AtomicInteger via compareAndSet: one succeeds, the other retries automatically with the updated value">
  <rect x="8" y="8" width="624" height="164" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">AtomicInteger value: 5</text>

  <rect x="30" y="40" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Thread A: CAS(5 -&gt; 6) succeeds</text>

  <rect x="380" y="40" width="220" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="490" y="65" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Thread B: CAS(5 -&gt; 6) FAILS (value now 6)</text>

  <text x="490" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">retries automatically:</text>
  <rect x="380" y="105" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Thread B: CAS(6 -&gt; 7) succeeds</text>
</svg>

A failed CAS doesn't corrupt anything — it just means "try again with the current value," which `incrementAndGet()` and friends do automatically.

## 5. Runnable example

Scenario: a request counter and a "current leader" reference shared across worker threads — the same shared state, evolved from a broken plain-`int` counter, through `AtomicInteger`'s lock-free correctness, to `AtomicReference` safely swapping an immutable configuration object under concurrent access.

### Level 1 — Basic

```java
public class RequestCounterBroken {
    static int count = 0; // plain int -- NOT thread-safe

    public static void main(String[] args) throws InterruptedException {
        Runnable job = () -> {
            for (int i = 0; i < 100_000; i++) count++; // read-modify-write race
        };

        Thread t1 = new Thread(job);
        Thread t2 = new Thread(job);
        t1.start(); t2.start();
        t1.join(); t2.join();

        System.out.println("count = " + count + " (expected 200000)");
    }
}
```

**How to run:** `java RequestCounterBroken.java`

`count++` is not atomic — it's read, add 1, write, as three separate steps — so two threads can both read the same value before either writes back, silently losing increments. The printed total is usually less than 200000, and varies run to run.

### Level 2 — Intermediate

```java
import java.util.concurrent.atomic.AtomicInteger;

public class RequestCounterAtomic {
    static final AtomicInteger count = new AtomicInteger(0);

    public static void main(String[] args) throws InterruptedException {
        Runnable job = () -> {
            for (int i = 0; i < 100_000; i++) count.incrementAndGet(); // atomic, lock-free
        };

        Thread t1 = new Thread(job);
        Thread t2 = new Thread(job);
        t1.start(); t2.start();
        t1.join(); t2.join();

        System.out.println("count = " + count.get() + " (expected 200000)");
    }
}
```

**How to run:** `java RequestCounterAtomic.java`

`incrementAndGet()` performs the read-modify-write as one indivisible CAS-based step — no increments are ever lost, no matter how the two threads' 100,000 calls each interleave, and no lock was ever explicitly acquired.

### Level 3 — Advanced

```java
import java.util.concurrent.atomic.AtomicReference;

public class ConfigSwapAtomicReference {
    record Config(int maxConnections, String mode) { }

    static final AtomicReference<Config> current =
        new AtomicReference<>(new Config(10, "normal"));

    static void enterMaintenanceMode() {
        // Atomically swap the ENTIRE config object -- readers never see a half-updated config,
        // since each read gets either the old Config or the new one, never a mix of both fields.
        current.updateAndGet(old -> new Config(0, "maintenance"));
    }

    public static void main(String[] args) throws InterruptedException {
        Runnable reader = () -> {
            for (int i = 0; i < 3; i++) {
                Config snapshot = current.get(); // always a fully-formed, consistent Config
                System.out.println(Thread.currentThread().getName()
                    + " sees maxConnections=" + snapshot.maxConnections() + " mode=" + snapshot.mode());
                try { Thread.sleep(20); } catch (InterruptedException ignored) { }
            }
        };

        Thread r1 = new Thread(reader, "reader-1");
        Thread switcher = new Thread(() -> {
            try { Thread.sleep(15); } catch (InterruptedException ignored) { }
            enterMaintenanceMode();
            System.out.println("Switched to maintenance mode");
        });

        r1.start(); switcher.start();
        r1.join(); switcher.join();
    }
}
```

**How to run:** `java ConfigSwapAtomicReference.java`

`AtomicReference<Config>` guarantees every reader's `current.get()` returns a **fully-formed** `Config` object — either the old one (`maxConnections=10, mode=normal`) or the new one (`maxConnections=0, mode=maintenance`), never a torn mix of old and new field values, because the entire object reference is swapped atomically in one step rather than mutating individual fields in place.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `current` holds a `Config(10, "normal")`. Two threads start: `reader-1`, which reads `current` three times with a 20ms pause between reads, and `switcher`, which sleeps 15ms and then calls `enterMaintenanceMode()`.

`reader-1`'s first iteration happens almost immediately (before 15ms have passed), so `current.get()` returns the original `Config(10, "normal")` — printed as `"maxConnections=10 mode=normal"`. It then sleeps 20ms.

Around the 15ms mark, `switcher` wakes up and calls `enterMaintenanceMode()`, which internally calls `current.updateAndGet(old -> new Config(0, "maintenance"))`. This reads the current reference (`Config(10, "normal")`), computes a brand-new `Config(0, "maintenance")` object, and atomically swaps `current`'s internal reference to point at this new object — this whole operation is one atomic step, so no thread can ever observe a state "in between" the old and new config. `switcher` then prints `"Switched to maintenance mode"`.

`reader-1`'s second iteration fires around the 20ms mark (after its first sleep) — since the swap already happened by 15ms, `current.get()` now returns the new `Config(0, "maintenance")`, printed accordingly. The third iteration, around 40ms, sees the same maintenance config, since nothing has changed it again.

Both threads finish, and the program exits. The key guarantee demonstrated: no reader ever sees a "half-updated" config (e.g. `maxConnections=0` paired incorrectly with `mode="normal"`) — each read is a clean, atomic snapshot of one specific `Config` instance.

Expected output (exact interleaving of "sees" lines around the switch may shift slightly with timing, but no reader ever prints a mixed old/new combination):
```
reader-1 sees maxConnections=10 mode=normal
Switched to maintenance mode
reader-1 sees maxConnections=0 mode=maintenance
reader-1 sees maxConnections=0 mode=maintenance
```

## 7. Gotchas & takeaways

> Atomic classes make **a single variable's** updates thread-safe, but they do **not** make a sequence of operations across multiple atomic variables atomic as a group. Incrementing an `AtomicInteger` and then separately updating an `AtomicReference` based on it are still two independent atomic steps with a race window between them — if several fields need to change together consistently, bundle them into one immutable object behind a single `AtomicReference` (exactly as `Config` does above), or use a `Lock`.

- `AtomicInteger`/`AtomicLong`/`AtomicReference` provide lock-free, thread-safe operations on a single variable using CAS (compare-and-swap) under the hood.
- `incrementAndGet()`, `addAndGet(delta)`, and `updateAndGet(function)` all perform their read-modify-write as one atomic step — no lost updates, no explicit locking.
- `compareAndSet(expected, newValue)` is the underlying primitive: "update only if the value hasn't changed since I last checked" — the building block of lock-free algorithms.
- `AtomicReference<V>` is especially useful for atomically swapping an entire immutable object (like the `Config` record above), so readers never observe a partially-updated combination of fields.
- Atomic classes are ideal for simple, independent counters, flags, or single-object state; for coordinating multiple related pieces of state together, a `Lock` or a single `AtomicReference` wrapping one combined immutable object is usually clearer and safer.
