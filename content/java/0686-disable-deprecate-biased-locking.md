---
card: java
gi: 686
slug: disable-deprecate-biased-locking
title: Disable & deprecate biased locking
---

## 1. What it is

**Java 15 disabled biased locking by default and deprecated it for future removal** (JEP 374). Biased locking was a JVM-internal optimization for `synchronized` blocks: when a lock was repeatedly acquired by the *same* thread with no contention from other threads (a very common pattern for objects like collections created and used entirely within one thread, or `StringBuffer`-style objects treated as if single-threaded), the JVM could "bias" the lock toward that thread, letting it re-acquire the lock via an extremely cheap check instead of a full atomic compare-and-swap operation. Java 15 flipped `-XX:+UseBiasedLocking` to `false` by default (it can still be explicitly re-enabled) and marked the whole mechanism deprecated, signaling it would eventually be removed outright.

## 2. Why & when

Biased locking delivered real performance wins when it was introduced (Java 6, mid-2000s), because at that time, uncontended locks were extremely common and the cost difference between a biased check and a full atomic CAS was more significant relative to overall hardware performance. By the mid-2010s, two things had shifted: modern CPUs made plain atomic compare-and-swap operations dramatically cheaper than they used to be, narrowing the performance gap biased locking was designed to close; and biased locking's implementation had become one of the most complex parts of the JVM's synchronization machinery — its "bulk rebias" and "bulk revoke" mechanisms, needed to handle a lock transitioning from one thread's bias to contention with another thread, added substantial code complexity and subtle correctness-critical corner cases for a shrinking performance benefit. The JDK team's own analysis found many modern workloads no longer benefited enough to justify that complexity. If you notice a *measurable* regression after upgrading to Java 15+ that profiling traces to synchronized-block overhead on genuinely single-thread-dominated locks, you can still pass `-XX:+UseBiasedLocking` to restore the old default temporarily while you investigate — but treat that as a stopgap, since the mechanism is deprecated and slated for eventual removal.

## 3. Core concept

```bash
# Java 6–14: biased locking enabled by default
java MyApp   # equivalent to: java -XX:+UseBiasedLocking MyApp

# Java 15 onward: biased locking disabled by default, and deprecated
java MyApp   # equivalent to: java -XX:-UseBiasedLocking MyApp

# Still possible on Java 15+ to explicitly opt back in (deprecated, may print a warning):
java -XX:+UseBiasedLocking MyApp
```

The `synchronized` keyword and all locking semantics in application code are completely unaffected — this change is purely about which low-level optimization strategy the JVM uses internally to implement those semantics efficiently.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A lock's internal state machine: unlocked, biased toward one thread for cheap re-acquisition, or revoked to a full atomic-CAS-based lock under contention">
  <rect x="20" y="80" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="105" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Unlocked</text>
  <text x="100" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no owner</text>

  <line x1="180" y1="100" x2="230" y2="70" stroke="#79c0ff" stroke-width="2" marker-end="url(#a1)"/>
  <text x="205" y="60" fill="#79c0ff" font-size="9" font-family="sans-serif">acquire (biased)</text>

  <rect x="240" y="30" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="55" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Biased to Thread A</text>
  <text x="330" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">cheap re-acquire, no CAS</text>

  <line x1="330" y1="90" x2="330" y2="140" stroke="#f85149" stroke-width="2" marker-end="url(#a2)"/>
  <text x="410" y="120" fill="#f85149" font-size="9" font-family="sans-serif">Thread B contends</text>

  <rect x="240" y="150" width="180" height="60" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="330" y="175" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Revoked / CAS-based</text>
  <text x="330" y="192" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">full atomic locking, both threads</text>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

Biased locking's benefit only appears in the top path; the "revoke to CAS-based locking" transition itself carries a cost that undermines the benefit once any real contention occurs.

## 5. Runnable example

Scenario: a single-threaded counter using `synchronized` heavily — first as a plain benchmark comparing default (Java 15+, biased locking off) versus explicitly re-enabled biased locking, then adding a second contending thread to show why the "bias revocation" cost matters, then a broader takeaway program that measures both the single-thread and contended cases together and prints a summary a developer could use to decide whether biased locking is worth exploring for a specific workload.

### Level 1 — Basic

```java
// File: SingleThreadLockBenchmark.java
public class SingleThreadLockBenchmark {
    static final Object lock = new Object();
    static long counter = 0;

    public static void main(String[] args) {
        long start = System.nanoTime();
        for (int i = 0; i < 50_000_000; i++) {
            synchronized (lock) {
                counter++;
            }
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("Single-threaded synchronized increments: " + counter);
        System.out.println("Elapsed: " + elapsedMs + " ms");
    }
}
```

**How to run:**
```
java SingleThreadLockBenchmark.java
```

Expected output (exact timing varies by machine):
```
Single-threaded synchronized increments: 50000000
Elapsed: 141 ms
```

On a JDK between versions 15 and 17, you could additionally compare this against `java -XX:+UseBiasedLocking SingleThreadLockBenchmark.java` to re-enable the legacy optimization; on later JDKs the flag was removed outright and `java` refuses to start with `Unrecognized VM option 'UseBiasedLocking'`, which is itself a concrete illustration of "deprecated" eventually becoming "gone."

### Level 2 — Intermediate

```java
// File: ContendedLockBenchmark.java
public class ContendedLockBenchmark {
    static final Object lock = new Object();
    static long counter = 0;

    public static void main(String[] args) throws InterruptedException {
        int iterationsPerThread = 20_000_000;

        long start = System.nanoTime();
        Thread t1 = new Thread(() -> {
            for (int i = 0; i < iterationsPerThread; i++) {
                synchronized (lock) { counter++; }
            }
        });
        Thread t2 = new Thread(() -> {
            for (int i = 0; i < iterationsPerThread; i++) {
                synchronized (lock) { counter++; }
            }
        });

        t1.start();
        t2.start();
        t1.join();
        t2.join();

        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("Two-thread contended increments: " + counter);
        System.out.println("Elapsed: " + elapsedMs + " ms");
    }
}
```

**How to run:**
```
java ContendedLockBenchmark.java
```

Expected output (exact timing varies by machine):
```
Two-thread contended increments: 40000000
Elapsed: 788 ms
```

On a JDK where `-XX:+UseBiasedLocking` is still recognized (versions 15–17), re-running with that flag added lets you compare directly: with two genuinely contending threads, biased locking's "revocation" overhead can make the legacy re-enabled run no better, or even worse, than the Java 15+ default of disabled biased locking — precisely the finding that justified the default change.

Once a second thread genuinely contends for `lock`, any bias previously established toward the first thread must be **revoked** — a relatively expensive, safepoint-related operation — before the lock can transition to ordinary contended locking. This revocation cost is exactly why the JDK team concluded biased locking's benefit had become marginal or even net-negative on many real, contended workloads, justifying the Java 15 default change.

### Level 3 — Advanced

```java
// File: LockingSummary.java
public class LockingSummary {
    static final Object lock = new Object();
    static long counter = 0;

    static long timeSingleThreaded(int iterations) {
        counter = 0;
        long start = System.nanoTime();
        for (int i = 0; i < iterations; i++) {
            synchronized (lock) { counter++; }
        }
        return (System.nanoTime() - start) / 1_000_000;
    }

    static long timeContended(int iterationsPerThread) throws InterruptedException {
        counter = 0;
        long start = System.nanoTime();
        Runnable task = () -> {
            for (int i = 0; i < iterationsPerThread; i++) {
                synchronized (lock) { counter++; }
            }
        };
        Thread t1 = new Thread(task);
        Thread t2 = new Thread(task);
        t1.start();
        t2.start();
        t1.join();
        t2.join();
        return (System.nanoTime() - start) / 1_000_000;
    }

    public static void main(String[] args) throws InterruptedException {
        long singleMs = timeSingleThreaded(30_000_000);
        long contendedMs = timeContended(15_000_000);

        System.out.println("Single-threaded: " + singleMs + " ms for 30,000,000 increments");
        System.out.println("Two-thread contended: " + contendedMs + " ms for 30,000,000 increments");
        System.out.println();
        System.out.println("Interpretation: compare these numbers against the same program run with");
        System.out.println("-XX:+UseBiasedLocking to see whether this specific workload still benefits");
        System.out.println("from the legacy optimization Java 15+ no longer enables by default.");
    }
}
```

**How to run:**
```
java LockingSummary.java
```

Expected output (numbers vary by hardware):
```
Single-threaded: 68 ms for 30,000,000 increments
Two-thread contended: 592 ms for 30,000,000 increments

Interpretation: compare these numbers against the same program run with
-XX:+UseBiasedLocking to see whether this specific workload still benefits
from the legacy optimization Java 15+ no longer enables by default.
```

On a JDK version where `-XX:+UseBiasedLocking` is still recognized (15 through 17), running `java -XX:+UseBiasedLocking LockingSummary.java` and comparing its two numbers against the default run above is exactly the investigative step the program's own closing message suggests.

Level 3 packages both the single-threaded and contended cases into one program with a clear side-by-side structure, mirroring how a developer investigating a genuine post-upgrade regression would actually approach the question: measure both scenarios under the new default, then measure again with `-XX:+UseBiasedLocking` explicitly re-enabled, and compare — rather than assuming either flag setting is universally better.

## 6. Walkthrough

1. `LockingSummary.main` calls `timeSingleThreaded(30_000_000)` first. Inside, `counter` is reset to `0`, a `System.nanoTime()` baseline is taken, and a tight loop performs 30 million `synchronized (lock) { counter++; }` operations from a single thread — the exact scenario biased locking was designed to accelerate: the same thread re-acquiring the same lock repeatedly with zero contention.
2. On a pre-Java-15 JVM (or Java 15+ run with `-XX:+UseBiasedLocking` explicitly), the JVM would detect this single-thread-only acquisition pattern and bias the lock toward that thread after its first acquisition, letting every subsequent `synchronized` block re-enter via a cheap check rather than a full atomic operation. On Java 15+'s new default, every acquisition instead goes through the (now much cheaper on modern hardware than it was in the mid-2000s) lightweight/CAS-based locking path directly, without ever attempting a bias.
3. `timeSingleThreaded` returns the elapsed milliseconds, which `main` stores in `singleMs` and later prints.
4. `main` next calls `timeContended(15_000_000)`, which resets `counter` again and launches **two** threads, each running the identical loop of 15 million `synchronized` increments (adding up to the same 30 million total operations as the single-threaded case, for a fair comparison) — but now genuinely contending for the same `lock` object concurrently.
5. If biased locking were active and the lock had previously been biased toward some earlier thread, the very first acquisition attempt by the *second* contending thread here would force a **bias revocation**: a relatively expensive operation (historically requiring a safepoint — a brief pause where all application threads stop — in older JVM implementations of biased locking) that transitions the lock from "biased to one specific thread" to "available for full contended locking by any thread." Only after that revocation completes can normal contended synchronization proceed.
6. `timeContended` returns its own elapsed time, stored in `contendedMs`.
7. `main` prints both timings, followed by an explanatory note directing the reader to re-run the exact same program with `-XX:+UseBiasedLocking` added and compare the two sets of numbers — since the *actual* answer to "does biased locking help my workload" depends on real contention patterns that vary by application, and Java 15's change simply flips which behavior is the default rather than removing the choice outright (as of Java 15; a later release did remove the mechanism entirely).

```
timeSingleThreaded(30M) ──► one thread, zero contention
                                (biased locking's ideal case, if enabled)
timeContended(15M + 15M) ──► two threads, real contention
                                (forces bias revocation, if biased locking enabled)
        │
        ▼
compare singleMs / contendedMs across:
   default (Java 15+: biased locking OFF)
   vs. -XX:+UseBiasedLocking (legacy behavior restored)
```

## 7. Gotchas & takeaways

> Re-enabling biased locking via `-XX:+UseBiasedLocking` on Java 15+ still **works** (the flag wasn't removed, just the default flipped, and the whole mechanism was marked deprecated) — but relying on it as a permanent fix rather than a temporary stopgap is risky, since deprecated JVM flags are explicit candidates for removal in a future release, and indeed this exact mechanism was removed outright in a later JDK version.

- This change affects `-XX:+UseBiasedLocking`'s **default value**, not the `synchronized` keyword's semantics — correctness of `synchronized` blocks is completely unaffected; only the internal optimization strategy changed.
- The performance impact of this default flip is workload-dependent: applications dominated by single-thread-only lock usage (a fairly common historical pattern that motivated biased locking's original introduction) are the ones most likely to notice any difference; heavily contended or already-lock-free/`java.util.concurrent`-based code is unaffected either way.
- Always measure before assuming a regression is caused by this change — profile with a tool like async-profiler or JFR to confirm synchronized-block overhead is actually the bottleneck before reaching for `-XX:+UseBiasedLocking` as a fix.
- Modern concurrent code increasingly favors `java.util.concurrent` primitives (`ReentrantLock`, atomic classes, concurrent collections) over raw `synchronized` blocks specifically because those primitives' performance does not depend on this kind of JVM-internal lock-biasing heuristic at all.
- This deprecation is part of a broader, ongoing JVM trend of removing complex, narrowly-beneficial optimizations (similar in spirit to CMS's removal — see [CMS GC removed](0674-cms-gc-removed.md)) once their maintenance cost outweighs their shrinking performance benefit on modern hardware.
