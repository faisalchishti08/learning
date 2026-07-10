---
card: java
gi: 865
slug: synchronized-blocks-monitor-objects
title: synchronized blocks & monitor objects
---

## 1. What it is

A `synchronized` **block** lets you lock on an explicitly chosen object for only a portion of a method, instead of locking the entire method on `this`: `synchronized (someObject) { ... }` acquires that object's monitor for the duration of the block and releases it when the block exits. The object named in the parentheses — any object at all, not necessarily `this` — is called the **monitor object** (or lock object). This gives you two things a full `synchronized` method can't: locking only the critical section rather than the whole method body, and choosing a **dedicated, private lock object** instead of implicitly locking on `this`.

## 2. Why & when

Use a `synchronized` block instead of a `synchronized` method whenever part of a method doesn't need protection (expensive computation, logging, I/O) — locking only the small critical section reduces how long other threads are blocked, directly improving throughput under contention. Use a dedicated private lock object (`private final Object lock = new Object();`) instead of locking on `this` whenever the object is otherwise accessible to outside code — if external code can also call `synchronized (yourObject)`, it can accidentally (or maliciously) hold your lock and stall your own internal synchronization, a class of bug that a private lock object makes impossible, since nothing outside the class can ever obtain a reference to it. This is standard practice in any class designed to be safely used as a library or exposed to code you don't fully control.

## 3. Core concept

```java
class Cache {
    private final Object lock = new Object(); // private monitor -- nobody outside can lock on it
    private final Map<String, String> data = new HashMap<>();

    String get(String key) {
        String cheapPreCheck = key.trim(); // no lock needed for this part
        synchronized (lock) {
            return data.get(cheapPreCheck); // only the shared-state access is protected
        }
    }
}
```

Locking on a private `lock` field instead of `this` means no external code — not even a subclass overriding a method — can ever accidentally synchronize on the same object and interfere with this class's internal locking.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A method with an unprotected preamble, then a synchronized block guarding only the shared-state access, then an unprotected epilogue">
  <rect x="20" y="60" width="160" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="100" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">preamble (no lock)</text>

  <rect x="200" y="40" width="240" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="65" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">synchronized (lock) {</text>
  <text x="320" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">critical section</text>
  <text x="320" y="115" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">}</text>

  <rect x="460" y="60" width="160" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="540" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">epilogue (no lock)</text>

  <line x1="180" y1="85" x2="196" y2="85" stroke="#8b949e" stroke-width="2" marker-end="url(#a4)"/>
  <line x1="440" y1="85" x2="456" y2="85" stroke="#8b949e" stroke-width="2" marker-end="url(#a4)"/>
  <defs><marker id="a4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Only the middle section blocks other threads; the preamble and epilogue run fully concurrently across threads.*

## 5. Runnable example

Scenario: a simple statistics tracker that computes an expensive summary string, growing from locking too much, to locking only the critical section, to using a dedicated private lock object separate from a second piece of state guarded by its own lock.

### Level 1 — Basic

```java
public class WholeMethodLocking {
    static class Stats {
        private long total = 0;
        private long count = 0;

        synchronized void record(long value) { // locks `this` for the ENTIRE method
            String label = describeSlowly(value); // expensive, doesn't touch shared state
            total += value;
            count++;
            System.out.println("recorded " + label);
        }

        private String describeSlowly(long value) {
            try { Thread.sleep(5); } catch (InterruptedException ignored) {}
            return "value=" + value;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Stats stats = new Stats();
        Thread t1 = new Thread(() -> stats.record(10));
        Thread t2 = new Thread(() -> stats.record(20));
        long start = System.currentTimeMillis();
        t1.start(); t2.start();
        t1.join(); t2.join();
        System.out.println("elapsed ~" + (System.currentTimeMillis() - start) + "ms (serialized by the whole-method lock)");
    }
}
```

**How to run:** `java WholeMethodLocking.java` (JDK 17+).

Expected output shape:
```
recorded value=10
recorded value=20
elapsed ~10ms (serialized by the whole-method lock)
```

Because `record` is `synchronized` on the whole method, the two threads' calls to the slow `describeSlowly` are needlessly serialized too, even though that part touches no shared state — elapsed time is roughly the sum of both sleeps rather than running them in parallel.

### Level 2 — Intermediate

```java
public class SynchronizedBlockOnly {
    static class Stats {
        private long total = 0;
        private long count = 0;

        void record(long value) {
            String label = describeSlowly(value); // runs OUTSIDE the lock -- fully concurrent
            synchronized (this) { // only this small part touches shared state
                total += value;
                count++;
            }
            System.out.println("recorded " + label);
        }

        private String describeSlowly(long value) {
            try { Thread.sleep(5); } catch (InterruptedException ignored) {}
            return "value=" + value;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Stats stats = new Stats();
        Thread t1 = new Thread(() -> stats.record(10));
        Thread t2 = new Thread(() -> stats.record(20));
        long start = System.currentTimeMillis();
        t1.start(); t2.start();
        t1.join(); t2.join();
        System.out.println("elapsed ~" + (System.currentTimeMillis() - start) + "ms (the two slow calls now overlap)");
    }
}
```

**How to run:** `java SynchronizedBlockOnly.java`.

Expected output shape:
```
recorded value=10
recorded value=20
elapsed ~5ms (the two slow calls now overlap)
```

The real-world concern added: moving the expensive, state-free work (`describeSlowly`) outside the `synchronized` block so the two threads' slow calls genuinely run in parallel, while the actual shared-state update (`total`, `count`) is still correctly protected — cutting elapsed time roughly in half compared to whole-method locking.

### Level 3 — Advanced

```java
public class DedicatedLockObjects {
    static class Stats {
        private final Object valueLock = new Object(); // private monitor for total/count
        private final Object logLock = new Object();   // separate private monitor for the log
        private long total = 0;
        private long count = 0;
        private final StringBuilder log = new StringBuilder();

        void record(long value) {
            synchronized (valueLock) { // guards ONLY total/count
                total += value;
                count++;
            }
            synchronized (logLock) { // guards ONLY the log -- independent of valueLock
                log.append("recorded ").append(value).append('\n');
            }
        }

        synchronized long average() { // NOTE: locking `this` here would NOT be consistent
            synchronized (valueLock) {
                return count == 0 ? 0 : total / count;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Stats stats = new Stats();
        Runnable task = () -> {
            for (int i = 1; i <= 100; i++) stats.record(i);
        };
        Thread t1 = new Thread(task);
        Thread t2 = new Thread(task);
        t1.start(); t2.start();
        t1.join(); t2.join();

        System.out.println("average = " + stats.average() + " (expected 50, unaffected by log contention)");
    }
}
```

**How to run:** `java DedicatedLockObjects.java`.

Expected output:
```
average = 50 (expected 50, unaffected by log contention)
```

This adds the production-flavored hard case: two **independent** pieces of shared state (`total`/`count` versus `log`), each guarded by its own dedicated private lock object, so contention on the log (which every call touches) never blocks the numeric bookkeeping and vice versa. Note the bug fixed along the way: `average()` correctly locks `valueLock` (the same lock `record` uses to protect `total`/`count`) rather than accidentally locking `this` or `logLock`, which would let a reader race with a writer.

## 6. Walkthrough

Tracing two concurrent calls to `record(v)` from `t1` and `t2`:

1. Both threads call `record`, and each first attempts `synchronized (valueLock) { total += value; count++; }` — whichever thread acquires `valueLock` first runs its two-line update atomically; the other blocks briefly, then runs its own update once the lock is released.
2. Because `valueLock` guards nothing except `total` and `count`, this brief exclusion is the only serialization point for the numeric bookkeeping — it's as small as the critical section actually needs to be.
3. Each thread then separately acquires `logLock` to append its own line to `log` — since `logLock` is a different object from `valueLock`, a thread doing its log append does not block another thread doing its numeric update, and vice versa; the two critical sections run independently.
4. After both threads finish their 100 iterations each, `main` calls `stats.average()`, which first acquires the `synchronized` lock on `this` (the method itself is declared `synchronized`) and then, inside that, also acquires `valueLock` before reading `total` and `count`.
5. Re-acquiring `valueLock` here (even though `this` is already locked) is what actually makes the read consistent with `record`'s writes — since `record` never locks `this`, only locking `this` in `average()` would provide no real exclusion against it; the nested `synchronized (valueLock)` is what matters.
6. The final division `total / count` — with `total = (1+...+100)*2 = 10100` and `count = 200` — yields `50`, printed as the confirmed, race-free average.

## 7. Gotchas & takeaways

> **Gotcha:** it's easy to write a method that locks the *wrong* object out of habit — for example, locking `this` in a "reader" method when the corresponding "writer" method actually protects its state with a private field like `valueLock`. Two methods that don't share the same lock object provide **zero** mutual exclusion between each other, no matter how `synchronized`-looking the code is; see `average()` above, which must deliberately reuse `valueLock`.
- A `synchronized` block only needs to wrap the smallest section that actually touches shared, mutable state — moving expensive, state-free work outside the block reduces contention and improves throughput.
- Prefer a dedicated `private final Object lock = new Object();` over locking on `this` whenever the object is exposed to code you don't control, so nothing external can accidentally interfere with your internal synchronization.
- Independent pieces of shared state can (and often should) be guarded by independent lock objects, so contention on one doesn't stall access to the other.
- Every method that touches a given piece of shared state must consistently lock the *same* object — mixing `this`, a private field, and other objects across different methods that touch the same data silently breaks the mutual exclusion.
- `synchronized` blocks are exception-safe: the lock is released automatically even if the block throws, exactly like a `synchronized` method.
