---
card: java
gi: 857
slug: happens-before-relationship
title: Happens-before relationship
---

## 1. What it is

The **happens-before relationship** is the Java Memory Model's (JMM) formal definition of when one thread's action is *guaranteed* to be visible to another thread — if action A happens-before action B, then every memory effect of A (every field it wrote) is guaranteed visible to the thread performing B. Without an established happens-before relationship between two actions on different threads, the JMM makes **no visibility guarantee at all** — a write on one thread might never become visible to a read on another thread, might become visible only after an unpredictable delay, or might appear to happen in a different order than the program's source code suggests, due to compiler optimizations, CPU instruction reordering, or CPU cache effects. Happens-before edges come from a specific, enumerated set of sources: a thread's `start()` call happens-before anything the started thread does; everything a thread does happens-before another thread's successful `join()` on it; a `volatile` write happens-before a subsequent `volatile` read of the same field; and releasing a `synchronized` lock happens-before another thread's subsequent acquisition of that same lock.

## 2. Why & when

Without this formal guarantee system, the JMM would have to promise that *every* write by any thread is immediately visible to *every* other thread in program order — a guarantee that would forbid essentially all the CPU and compiler optimizations (instruction reordering, caching values in registers, store buffering) that make modern hardware fast. Happens-before exists as the precise contract: the JMM guarantees visibility and ordering **only** across the specific edges the language defines, and says nothing at all about visibility in their absence — which is exactly what allows the JVM and CPU to freely reorder and cache everything else. Understanding this matters directly for writing correct concurrent code: any time one thread needs to reliably see another thread's write, there must be an actual happens-before edge connecting that write to that read — a shared plain field with no `volatile`, no `synchronized`, and no other happens-before source connecting the writer and reader provides **no** visibility guarantee whatsoever, regardless of how reliably it might appear to work in casual testing.

## 3. Core concept

```java
// NO happens-before edge between the writer and reader threads below --
// the JMM makes NO guarantee the reader will EVER see "ready" become true.
class NoGuarantee {
    boolean ready = false; // plain field, no volatile
    void writer() { ready = true; }
    void reader() { while (!ready) { /* may spin forever, per the JMM's letter */ } }
}

// WITH a happens-before edge -- volatile establishes it between the write and the read:
class WithGuarantee {
    volatile boolean ready = false;
    void writer() { ready = true; } // this volatile write happens-before...
    void reader() { while (!ready) { } } // ...this volatile read of the SAME field
}
```

The two classes look almost identical, but only `WithGuarantee` has a JMM-defined happens-before edge connecting the writer's action to the reader's — `NoGuarantee`'s `reader()` might, per the specification's letter, never observe `ready` becoming `true` at all, even though it very often appears to "work" in casual testing on typical hardware.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A volatile write on one thread happens-before a subsequent volatile read of the same field on another thread, guaranteeing every prior write by the writer thread is visible to the reader thread">
  <rect x="40" y="30" width="220" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">thread A: data = 42;</text>
  <text x="150" y="72" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">volatile ready = true;</text>

  <line x1="260" y1="57" x2="340" y2="57" stroke="#79c0ff" stroke-width="2" marker-end="url(#a857)"/>
  <text x="300" y="45" fill="#79c0ff" font-size="9" text-anchor="middle">happens-before</text>

  <rect x="350" y="30" width="230" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="465" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">thread B: if (ready)</text>
  <text x="465" y="72" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">  read data -- guaranteed 42</text>

  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The volatile read/write pair guarantees visibility not just of "ready" itself,</text>
  <text x="320" y="158" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">but of EVERY write thread A made before setting "ready", including the plain "data" field</text>

  <defs><marker id="a857" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

*A single `volatile` write/read pair carries visibility for every ordinary write that happened before it on the writing thread.*

## 5. Runnable example

Scenario: publishing a computed configuration value from a background thread to be safely read by the main thread, growing from the unsafe pattern with no happens-before edge, to the volatile-based fix, to a `synchronized`-block-based alternative demonstrating the monitor-lock happens-before source.

### Level 1 — Basic

```java
public class NoHappensBeforeRisk {
    static boolean ready = false; // plain field -- NO happens-before guarantee connects writer and reader
    static int data = 0;

    public static void main(String[] args) throws InterruptedException {
        Thread writer = new Thread(() -> {
            data = 42;
            ready = true; // this write has NO guaranteed visibility to another thread's read of "ready"
        });

        writer.start();
        writer.join(); // NOTE: join() itself DOES create a happens-before edge here,
                        // which is exactly why THIS particular example happens to be safe --
                        // see Level 2 for the version that removes that edge and is genuinely risky.
        System.out.println("data (guaranteed correct here, because of join()): " + data);
    }
}
```

**How to run:** `java NoHappensBeforeRisk.java` (JDK 17+).

Expected output:
```
data (guaranteed correct here, because of join()): 42
```

This specific example is actually safe — but only because `join()` itself is one of the JMM's happens-before sources (everything the joined thread did happens-before the `join()` call returning), not because plain fields are safe in general. The next level removes that accidental safety net to show the genuine risk.

### Level 2 — Intermediate

```java
public class GenuineRiskWithoutJoin {
    static volatile boolean stop = false; // used only to end the demo cleanly, not the field under test
    static boolean ready = false; // plain field -- the field actually being tested for visibility
    static int data = 0;

    public static void main(String[] args) throws InterruptedException {
        Thread reader = new Thread(() -> {
            long spins = 0;
            while (!ready && !stop) { spins++; } // busy-wait, with NO guaranteed visibility of "ready"'s write
            System.out.println("reader: saw ready become true after " + spins + " spins, data = " + data);
        });

        reader.start();
        Thread.sleep(50);

        data = 42;
        ready = true; // writing a PLAIN field from a different thread than the one reading it

        Thread.sleep(200); // give the reader a chance to notice, WITHOUT relying on join()
        stop = true; // end the demo regardless of whether "ready" was ever observed
        reader.join();
    }
}
```

**How to run:** `java GenuineRiskWithoutJoin.java`. On most current mainstream JVMs and typical hardware, this will usually appear to work correctly (the reader does observe `ready` becoming `true` within the 200ms window) — but this is **not** a guarantee the JMM provides; it "happens to work" due to how common JIT compilers and CPU architectures currently behave, not because the code is actually correct per the specification.

Expected output shape (illustrative — behavior is not formally guaranteed):
```
reader: saw ready become true after 384726 spins, data = 42
```

The real-world concern added: this version removes the `join()`-based happens-before edge, leaving `ready` and `data` connected between the two threads by **nothing** the JMM recognizes as a guarantee. It commonly "works" in practice on typical desktop/server JVMs, but the specification explicitly permits a compliant JVM to never let the reader observe the write at all (perhaps because the reader's `while (!ready)` check gets optimized into reading a cached value once and looping forever) — this is precisely the class of bug that's notoriously difficult to reproduce reliably, since it depends on JIT optimization decisions and hardware memory model details outside the program's control.

### Level 3 — Advanced

```java
public class TwoWaysToFixIt {
    // FIX 1: volatile -- establishes a happens-before edge on every write/read pair of THIS field.
    static volatile boolean readyVolatile = false;
    static int dataForVolatile = 0;

    // FIX 2: synchronized -- monitor lock release/acquire also establishes happens-before.
    static final Object lock = new Object();
    static boolean readySynchronized = false;
    static int dataForSynchronized = 0;

    public static void main(String[] args) throws InterruptedException {
        // Fix 1 in action:
        Thread volatileWriter = new Thread(() -> {
            dataForVolatile = 100;
            readyVolatile = true; // volatile WRITE
        });
        Thread volatileReader = new Thread(() -> {
            while (!readyVolatile) { } // volatile READ -- happens-before guarantees dataForVolatile is visible once this exits
            System.out.println("volatile fix: dataForVolatile = " + dataForVolatile);
        });
        volatileReader.start();
        volatileWriter.start();
        volatileWriter.join();
        volatileReader.join();

        // Fix 2 in action:
        Thread syncWriter = new Thread(() -> {
            synchronized (lock) {
                dataForSynchronized = 200;
                readySynchronized = true;
            } // releasing the lock HERE happens-before another thread's subsequent acquisition of it
        });
        Thread syncReader = new Thread(() -> {
            boolean seenReady = false;
            while (!seenReady) {
                synchronized (lock) { // acquiring the SAME lock re-establishes visibility
                    seenReady = readySynchronized;
                }
            }
            System.out.println("synchronized fix: dataForSynchronized = " + dataForSynchronized);
        });
        syncReader.start();
        syncWriter.start();
        syncWriter.join();
        syncReader.join();
    }
}
```

**How to run:** `java TwoWaysToFixIt.java`. Both fixes are deterministic and guaranteed correct per the JMM, unlike the risky Level 2 example.

Expected output:
```
volatile fix: dataForVolatile = 100
synchronized fix: dataForSynchronized = 200
```

This adds the production-flavored hard case: two genuinely correct, JMM-guaranteed fixes side by side. `volatile`'s happens-before edge applies specifically to that one field's write/read pairs. `synchronized`'s happens-before edge is broader — it applies to *releasing* a monitor lock happens-before a *subsequent acquisition* of that *same* lock by another thread, which is why `syncReader` must actually enter its own `synchronized (lock)` block (re-acquiring the same lock object `syncWriter` released) to correctly receive the visibility guarantee — simply reading `readySynchronized` outside any `synchronized` block would reintroduce the exact same risk as the plain-field version.

## 6. Walkthrough

Tracing the `synchronized` fix in `TwoWaysToFixIt.main`:

1. `syncWriter` enters `synchronized (lock)`, writes `dataForSynchronized = 200` and then `readySynchronized = true`, both as ordinary (non-volatile) field writes, and then exits the `synchronized` block — releasing the monitor lock on `lock`.
2. `syncReader` runs a loop that repeatedly enters its own `synchronized (lock)` block (acquiring the same lock object) and reads `readySynchronized` into a local variable, `seenReady`.
3. The JMM's happens-before rule for monitor locks states: releasing a lock happens-before any subsequent acquisition of that *same* lock by another thread. So the first time `syncReader`'s loop iteration acquires `lock` **after** `syncWriter` has released it, that acquisition is guaranteed to see every write `syncWriter` made *before* releasing the lock — not just `readySynchronized`, but `dataForSynchronized` too, exactly as with the `volatile` case's broader visibility guarantee.
4. Once `seenReady` reads as `true` inside one of `syncReader`'s synchronized blocks, the loop exits, and `dataForSynchronized` is printed — guaranteed by the happens-before edge to correctly show `200`, not a stale or partially-visible value.
5. Both fixes ultimately rely on the same underlying JMM principle — establish a recognized happens-before edge between the writing and reading actions — just using two different sources of that edge (`volatile` field access versus monitor lock release/acquisition), each appropriate in different situations (`volatile` for a single flag or reference; `synchronized` when a broader critical section of multiple related operations needs to be treated as one atomic, visible unit).

## 7. Gotchas & takeaways

> **Gotcha:** code that appears to work reliably in casual testing without any actual happens-before edge (like `GenuineRiskWithoutJoin`'s pattern) is not proof of correctness — it's evidence that the *current* JIT compiler and hardware happen not to reorder or cache in a way that breaks it *today*, on *this* machine. A JVM upgrade, a different CPU architecture, or even a change elsewhere in the program that affects JIT optimization decisions can silently break code that was never actually guaranteed to work in the first place.

- A happens-before relationship is the JMM's formal guarantee that one thread's action is visible to another thread's subsequent action — without it, there is **no** visibility guarantee at all, regardless of how reliably code appears to work in practice.
- Established happens-before sources include: thread `start()` (happens-before anything the started thread does), thread `join()` (everything the joined thread did happens-before the join returning), `volatile` write (happens-before a subsequent `volatile` read of the same field), and monitor lock release (happens-before a subsequent acquisition of that same lock).
- A shared plain field with no `volatile`, `synchronized`, or other happens-before source connecting a writer thread and a reader thread provides no visibility guarantee whatsoever, even if it commonly "appears to work" in testing.
- `volatile` and `synchronized` both establish happens-before edges, but through different mechanisms — `volatile` per individual field access; `synchronized` per lock release/acquisition pair, covering everything written inside the critical section.
- Never rely on informal testing to validate cross-thread visibility — identify the actual happens-before edge the code depends on, and confirm it's genuinely present via `volatile`, `synchronized`, or another recognized JMM source.
