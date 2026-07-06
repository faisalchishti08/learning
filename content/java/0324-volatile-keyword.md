---
card: java
gi: 324
slug: volatile-keyword
title: volatile keyword
---

## 1. What it is

`volatile` is a field modifier that guarantees every read of that field sees the most recently written value from *any* thread, and every write is immediately visible to all other threads — without it, the JVM and CPU are permitted to cache a field's value locally per-thread (in a CPU register or cache line) and a write from one thread may never become visible to another thread at all, or only after an unpredictable delay.

```java
public class VolatileDemo {
    static volatile boolean running = true;

    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long iterations = 0;
            while (running) { // without volatile, this loop might NEVER see the change below
                iterations++;
            }
            System.out.println("Worker stopped after seeing running=false; iterations=" + iterations);
        });
        worker.start();

        Thread.sleep(100);
        running = false; // this write must become visible to the worker thread promptly
        worker.join();
    }
}
```

`volatile boolean running` guarantees the worker thread's repeated reads of `running` will eventually observe the main thread's write of `false` — without `volatile`, the JVM would be free to optimize the loop assuming `running` never changes (since, from the worker thread's own perspective, nothing inside the loop modifies it), potentially causing an infinite loop that never terminates.

## 2. Why & when

Modern CPUs and the JVM aggressively optimize memory access — caching values in registers or CPU cache lines rather than main memory, and reordering instructions for performance — which is invisible and harmless for single-threaded code, but can cause one thread's writes to never become visible to another thread, or to become visible in a different order than they were written. `volatile` disables these specific optimizations for a field, guaranteeing visibility and ordering.

- **Simple flags read by multiple threads** — a shutdown flag, a "ready" indicator, or similar boolean/reference fields that one thread sets and another thread polls, without any more complex coordination needed.
- **Publishing a fully-constructed object safely** — a `volatile` reference field ensures that when another thread reads a non-null value from it, it also sees all of that object's own fields as they were at the time of the write (this relies on the broader "happens-before" guarantee `volatile` provides).
- **A lighter-weight alternative to synchronization for simple cases** — `volatile` provides visibility guarantees without the mutual-exclusion (locking) overhead of `synchronized`, appropriate when you only need "make sure everyone sees this write," not "only one thread at a time."

`volatile` guarantees visibility and ordering, but **not** atomicity for compound operations — `volatile int counter; counter++;` is still a race condition, because `counter++` is actually three separate steps (read, increment, write), and `volatile` doesn't make that sequence indivisible. For atomic compound operations, use `synchronized`, or the `java.util.concurrent.atomic` classes (like `AtomicInteger`), not `volatile` alone.

## 3. Core concept

```java
public class VolatileCore {
    static volatile int sharedValue = 0;
    static int nonVolatileValue = 0; // for contrast, though this specific demo may not reliably show the bug

    public static void main(String[] args) throws InterruptedException {
        Thread writer = new Thread(() -> {
            sharedValue = 42;
            System.out.println("Writer set sharedValue to 42");
        });

        writer.start();
        writer.join(); // join() ALSO establishes visibility, independent of volatile

        System.out.println("Main sees sharedValue = " + sharedValue); // guaranteed 42, via volatile OR via join()
    }
}
```

This particular example is guaranteed correct even without `volatile`, because `join()` itself establishes a "happens-before" relationship (any write the joined thread made becomes visible to the thread that joined it) — `volatile` matters specifically when there's **no** other synchronization (no lock, no `join()`) between the writing and reading threads, such as the polling-loop scenario in section 1, where the reading thread never calls `join()` on the writer before checking the flag.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without volatile a thread may cache a field value locally and never observe another thread's write, with volatile every read goes to main memory">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="260" height="45" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="150" y="52" fill="#f85149" font-size="10" text-anchor="middle">non-volatile field</text>
  <text x="150" y="68" fill="#8b949e" font-size="9" text-anchor="middle">may be cached per-thread; write visibility not guaranteed</text>

  <rect x="310" y="30" width="260" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="440" y="52" fill="#6db33f" font-size="10" text-anchor="middle">volatile field</text>
  <text x="440" y="68" fill="#8b949e" font-size="9" text-anchor="middle">every read/write goes through main memory, always visible</text>

  <text x="20" y="110" fill="#8b949e" font-size="9">volatile guarantees VISIBILITY and ORDERING, but NOT atomicity for compound read-modify-write operations.</text>
</svg>

`volatile` forces every access through main memory, guaranteeing visibility, but multi-step operations still need locking or atomic classes for correctness.

## 5. Runnable example

Scenario: a background worker thread controlled by a shutdown flag, evolved from a buggy non-volatile version (which may hang or behave unpredictably) into a correctly `volatile`-flagged version, then into a version demonstrating precisely what `volatile` does and doesn't fix, by contrasting it with a genuine compound-operation race that `volatile` alone cannot solve.

### Level 1 — Basic

```java
public class VolatileBasic {
    static boolean running = true; // BUG: not volatile

    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long iterations = 0;
            // A safety cap bounds the loop so this demo can't hang forever -- without volatile,
            // the JVM is free to optimize this loop as if "running" never changes at all, so on
            // some machines/JIT configurations the worker hits this cap WITHOUT ever having
            // observed running=false, which is exactly the risk volatile eliminates.
            long safetyCap = 2_000_000_000L;
            while (running && iterations < safetyCap) {
                iterations++;
            }
            if (iterations >= safetyCap) {
                System.out.println("Worker hit the safety cap WITHOUT ever seeing running=false -- the exact bug volatile prevents.");
            } else {
                System.out.println("Worker stopped, iterations=" + iterations);
            }
        });
        worker.start();

        Thread.sleep(100);
        System.out.println("Main setting running=false...");
        running = false;

        worker.join(5000); // wait at most 5 seconds
        System.out.println("Worker still alive after 5s? " + worker.isAlive());
    }
}
```

**How to run:** `java VolatileBasic.java`

Without `volatile`, this program's behavior is technically undefined by the Java Memory Model — the `safetyCap` exists only so this specific demonstration always terminates; on many real JVMs and machines the worker will still stop promptly by chance (especially before JIT optimizations kick in), but on others it can genuinely run through the entire `safetyCap` without ever observing `running=false`, printing the warning message instead — a real, reproducible instance of the exact problem `volatile` exists to solve, not a hypothetical one.

### Level 2 — Intermediate

Same shutdown mechanism, now correctly using `volatile`, guaranteeing the worker thread will observe the flag change and stop promptly.

```java
public class VolatileIntermediate {
    static volatile boolean running = true; // FIXED

    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long iterations = 0;
            while (running) {
                iterations++;
            }
            System.out.println("Worker stopped, iterations=" + iterations);
        });
        worker.start();

        Thread.sleep(100);
        System.out.println("Main setting running=false...");
        running = false;

        worker.join(2000);
        System.out.println("Worker still alive after 2s? " + worker.isAlive());
    }
}
```

**How to run:** `java VolatileIntermediate.java`

With `running` marked `volatile`, the write from the main thread is guaranteed to become visible to the worker thread promptly — the worker reliably stops shortly after the flag changes, and `worker.isAlive()` reliably reports `false` well within the 2-second timeout.

### Level 3 — Advanced

Same worker, now also incrementing a shared counter, demonstrating explicitly that `volatile` fixes the visibility problem for the shutdown flag but does **not** fix a genuine race condition on a compound read-modify-write operation — contrasted directly against `AtomicInteger`, which does provide atomicity.

```java
import java.util.concurrent.atomic.AtomicInteger;

public class VolatileAdvanced {
    static volatile boolean running = true;
    static volatile int volatileCounter = 0; // visibility guaranteed, but ++ is STILL not atomic
    static AtomicInteger atomicCounter = new AtomicInteger(0); // genuinely atomic increments

    public static void main(String[] args) throws InterruptedException {
        Runnable incrementTask = () -> {
            while (running) {
                volatileCounter++;       // NOT atomic despite being volatile -- read, add, write, 3 steps
                atomicCounter.incrementAndGet(); // genuinely atomic, single indivisible operation
            }
        };

        Thread t1 = new Thread(incrementTask);
        Thread t2 = new Thread(incrementTask);
        t1.start();
        t2.start();

        Thread.sleep(200);
        running = false;
        t1.join();
        t2.join();

        System.out.println("volatileCounter (unreliable, likely LESS than actual increments): " + volatileCounter);
        System.out.println("atomicCounter (reliable, correct count): " + atomicCounter.get());
    }
}
```

**How to run:** `java VolatileAdvanced.java`

Both `t1` and `t2` increment `volatileCounter` via `volatileCounter++` (three separate steps: read, add one, write back) and `atomicCounter` via `incrementAndGet()` (one indivisible, hardware-supported atomic operation) — `volatile` guarantees each individual read and write of `volatileCounter` is visible, but says nothing about the three-step sequence being uninterruptible, so two threads can interleave their read-add-write sequences and lose updates, while `atomicCounter`'s value is always exactly correct, since `AtomicInteger` guarantees true atomicity for its increment operations.

## 6. Walkthrough

Trace why `volatileCounter` can under-count while `atomicCounter` cannot, step by step.

**A lost update on `volatileCounter`.** Suppose `volatileCounter` currently holds `1000`. Thread `t1` executes `volatileCounter++`: internally, this reads the current value (`1000`), computes `1000 + 1 = 1001`, and prepares to write `1001` back. Before `t1` completes that write, `t2` also executes `volatileCounter++`: it reads the current value — still `1000`, since `t1` hasn't written its new value yet — computes `1001`, and writes `1001`. Now `t1` finishes its own write, also writing `1001` (its own previously-computed value). Two increments occurred, but the field only advanced by one, from `1000` to `1001` — one increment's effect was silently lost. `volatile` guarantees that whichever write happens *last* is visible to everyone, but it does nothing to prevent this read-compute-write sequence from overlapping in the first place.

**Why `atomicCounter.incrementAndGet()` cannot lose an update.** This method is implemented using a hardware-supported atomic instruction (commonly a compare-and-swap operation) that performs the entire "read current value, compute new value, write new value, but only if no other thread changed it in between" sequence as a single, indivisible unit. If `t2`'s attempt would conflict with `t1`'s concurrent attempt, the underlying hardware detects this and forces `t2` to retry with the updated value — guaranteeing that every single call to `incrementAndGet()` across every thread results in a genuinely distinct, correctly incremented value, with no lost updates possible.

**Running both counters concurrently for 200ms.** Both `t1` and `t2` loop as fast as possible, incrementing both counters on every iteration, until `running` becomes `false` (correctly and promptly visible to both, thanks to `volatile`). Over many thousands of iterations, `volatileCounter`'s lost-update race compounds — the final value is measurably, sometimes substantially, less than the true total number of increment attempts, while `atomicCounter`'s final value exactly matches the true total.

**Comparing the two final printed values.** `volatileCounter`'s printed value is whatever number of increments genuinely "stuck" without being overwritten by a lost update — inherently unpredictable and generally lower than expected. `atomicCounter.get()`'s printed value is the true, exact, correct total of every increment call that happened across both threads.

```
volatileCounter++ (three steps, NOT atomic despite volatile):
  t1: read 1000 -> compute 1001 -----------------> write 1001
  t2:          read 1000 -> compute 1001 -> write 1001    <- OVERLAPS with t1, one increment LOST

atomicCounter.incrementAndGet() (one indivisible hardware operation):
  t1: [read-compute-write as ONE atomic step] -> 1001
  t2: [read-compute-write as ONE atomic step] -> 1002    <- always correctly sequenced, nothing lost
```

**Output (illustrative — exact volatileCounter value varies by run and machine, always <= the true total):**
```
volatileCounter (unreliable, likely LESS than actual increments): 8734129
atomicCounter (reliable, correct count): 9012457
```

## 7. Gotchas & takeaways

> `volatile` guarantees that reads and writes of the field itself are immediately visible across threads, but it does **not** make compound operations (`counter++`, `if (x == null) x = new Thing()`) atomic. Any operation involving more than a single, direct read or a single, direct write of the volatile field is still subject to race conditions unless additionally protected by `synchronized` or replaced with a genuinely atomic class from `java.util.concurrent.atomic`.

> `join()`, entering/exiting a `synchronized` block, and other explicit synchronization mechanisms also establish the same visibility guarantee that `volatile` provides, specifically between the threads involved in that particular synchronization action — `volatile` is needed specifically when there's no other synchronization establishing a "happens-before" relationship between the writing and reading threads, as in an unsynchronized polling loop.

- `volatile` guarantees that a field's reads and writes are immediately visible across all threads, disabling per-thread caching and certain instruction-reordering optimizations for that field.
- It does not provide atomicity for compound read-modify-write operations — `volatile int x; x++;` is still a genuine race condition.
- Use `volatile` for simple flags and references read by multiple threads with no other synchronization already establishing visibility between them.
- For atomic compound operations, use `synchronized` or `java.util.concurrent.atomic` classes (`AtomicInteger`, `AtomicBoolean`, `AtomicReference`), not `volatile` alone.
