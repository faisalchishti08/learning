---
card: java
gi: 859
slug: atomicity-vs-visibility-vs-ordering
title: Atomicity vs visibility vs ordering
---

## 1. What it is

Correct concurrent code depends on three distinct, independently-failing properties, and fixing one does not fix the others. **Atomicity** means a sequence of operations completes as a single, indivisible unit — no other thread can observe (or interleave with) a partially-completed state. **Visibility** means a write made by one thread is guaranteed to be observable by another thread's subsequent read — without a proper [happens-before](0857-happens-before-relationship.md) edge, a write might never become visible to another thread at all. **Ordering** means the sequence of operations, as another thread observes them, matches what the program's source order implies — without an ordering guarantee, the compiler and CPU are free to reorder independent operations for performance, and another thread might observe effects in a different order than the code was written in. Each of `synchronized`, `volatile`, and the `Atomic*` classes provides a different combination of these three guarantees.

## 2. Why & when

Treating "thread safety" as one single, monolithic property leads directly to exactly the kind of subtle bug this section keeps returning to: `volatile` provides visibility and ordering but not atomicity (fixing it doesn't fix a lost-update race on a compound operation); a plain `synchronized` block provides all three within its scope, but at the cost of exclusive locking (only one thread executes the block at a time); `AtomicInteger` provides atomicity for its specific single-variable operations, along with visibility, but doesn't extend that atomicity to a sequence involving multiple different variables. Correctly reasoning about a piece of concurrent code means asking, for each shared piece of mutable state: does this need atomicity (is it read-then-written based on its own current value)? Does it need visibility (can another thread's read happen without any other synchronization connecting it to this write)? Does the order of multiple related operations, as observed by another thread, matter? A fix aimed at only one of these three questions, when more than one actually applies, leaves the code still broken along whichever dimension wasn't addressed.

## 3. Core concept

```java
// ATOMICITY problem alone: a plain int, incremented by multiple threads.
int plainCounter = 0;
void increment() { plainCounter++; } // races: lost updates possible

// VISIBILITY problem alone: a plain boolean flag, no synchronization connecting writer and reader.
boolean ready = false;
void setReady() { ready = true; } // may never become visible to another thread's read

// ORDERING problem: two independent writes, whose RELATIVE order matters to a reader,
// but nothing prevents the compiler/CPU from reordering them since they don't depend on each other.
int a = 0, b = 0;
void writeBoth() { a = 1; b = 2; } // a reader might see b=2 before a=1, absent an ordering guarantee

// Each of these needs a DIFFERENT fix: AtomicInteger for the first, volatile for the second,
// and either volatile (with careful field design) or synchronized for the third.
```

Three different-looking bugs, three different underlying properties failing, three different appropriate fixes — none of which substitutes for either of the others.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three independent concurrency properties: atomicity, visibility, and ordering, each addressed by a different tool">
  <g font-family="sans-serif">
    <rect x="20" y="30" width="190" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="115" y="55" fill="#e6edf3" font-size="11" text-anchor="middle">Atomicity</text>
    <text x="115" y="75" fill="#8b949e" font-size="9" text-anchor="middle">no partial state observed</text>
    <text x="115" y="90" fill="#3fb950" font-size="9" text-anchor="middle">fixed by: AtomicX / synchronized</text>

    <rect x="225" y="30" width="190" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
    <text x="320" y="55" fill="#e6edf3" font-size="11" text-anchor="middle">Visibility</text>
    <text x="320" y="75" fill="#8b949e" font-size="9" text-anchor="middle">writes reach other threads</text>
    <text x="320" y="90" fill="#3fb950" font-size="9" text-anchor="middle">fixed by: volatile / synchronized</text>

    <rect x="430" y="30" width="190" height="70" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
    <text x="525" y="55" fill="#e6edf3" font-size="11" text-anchor="middle">Ordering</text>
    <text x="525" y="75" fill="#8b949e" font-size="9" text-anchor="middle">observed sequence matches source</text>
    <text x="525" y="90" fill="#3fb950" font-size="9" text-anchor="middle">fixed by: volatile / synchronized</text>
  </g>
  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">synchronized provides all three within its scope; volatile provides only visibility + ordering;</text>
  <text x="320" y="158" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Atomic* classes provide atomicity + visibility for their own single-variable operations</text>
</svg>

*Three independent failure modes — fixing one leaves the other two exactly as broken as before.*

## 5. Runnable example

Scenario: a shared statistics recorder combining a counter, a status flag, and a pair of related fields, growing from isolating each property's failure independently, to combining the correct fix for each, to a single coherent example requiring all three simultaneously.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class AtomicityAloneBroken {
    static int counter = 0; // plain int -- no atomicity guarantee

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(4);
        for (int t = 0; t < 4; t++) {
            pool.submit(() -> {
                for (int i = 0; i < 10_000; i++) counter++;
            });
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        System.out.println("expected: 40000, actual: " + counter + " (atomicity problem alone)");
    }
}
```

**How to run:** `java AtomicityAloneBroken.java` (JDK 17+). The actual count will likely be less than 40000.

Expected output shape:
```
expected: 40000, actual: 34827 (atomicity problem alone)
```

This isolates the atomicity failure specifically: `counter` is perfectly visible across threads (no `volatile` needed for that part, since the threads happen to synchronize incidentally via the pool's own internals for this simple case) — the problem is purely that `counter++` isn't one indivisible operation.

### Level 2 — Intermediate

```java
import java.util.concurrent.atomic.*;
import java.util.concurrent.*;

public class EachPropertyFixedSeparately {
    static AtomicInteger counter = new AtomicInteger(0); // FIXES atomicity
    static volatile boolean recordingActive = true;       // FIXES visibility (and ordering, for this simple flag)

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(4);
        for (int t = 0; t < 4; t++) {
            pool.submit(() -> {
                while (recordingActive) {
                    counter.incrementAndGet(); // atomic -- no lost updates
                }
            });
        }

        Thread.sleep(50);
        recordingActive = false; // guaranteed visible to all 4 threads promptly, thanks to volatile

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("final counter (every increment correctly counted): " + counter.get());
    }
}
```

**How to run:** `java EachPropertyFixedSeparately.java`.

Expected output shape:
```
final counter (every increment correctly counted): 6218347
```

The real-world concern added: `AtomicInteger` fixes the atomicity problem for `counter`'s increments; `volatile` fixes the visibility problem for `recordingActive`'s stop signal — two independent fixes, each addressing exactly one of the two properties actually at risk in this particular piece of code, neither substituting for the other.

### Level 3 — Advanced

```java
import java.util.concurrent.atomic.*;

public class AllThreePropertiesTogether {
    // A "statistics snapshot" that needs ALL THREE properties simultaneously:
    // - atomicity: min and max must be updated together, consistently, as one logical unit
    // - visibility: a reader thread must see the latest values
    // - ordering: min/max must never be observed in an inconsistent relative state (e.g. min > max)
    static final Object lock = new Object();
    static int min = Integer.MAX_VALUE;
    static int max = Integer.MIN_VALUE;
    static volatile boolean hasData = false;

    static void record(int value) {
        synchronized (lock) { // provides atomicity (min+max updated as one unit) AND visibility/ordering
            if (value < min) min = value;
            if (value > max) max = value;
        }
        hasData = true; // volatile -- signals "there is now data to read" with a visibility guarantee
    }

    static void printSnapshot() {
        if (!hasData) {
            System.out.println("no data recorded yet");
            return;
        }
        synchronized (lock) { // re-acquiring the SAME lock guarantees seeing min/max consistently together
            System.out.println("min=" + min + ", max=" + max + " (never inconsistent relative to each other)");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread recorder = new Thread(() -> {
            for (int v : new int[]{5, 12, 3, 47, 8}) record(v);
        });
        recorder.start();
        recorder.join();

        printSnapshot();
    }
}
```

**How to run:** `java AllThreePropertiesTogether.java`.

Expected output:
```
min=3, max=47 (never inconsistent relative to each other)
```

This adds the production-flavored hard case: a scenario requiring all three properties at once, correctly addressed by combining tools. The `synchronized (lock)` block around both `min` and `max` updates provides **atomicity** (both fields update together as one unit, so a reader can never observe, say, a new `max` paired with a stale `min`), plus visibility and ordering for both fields via the monitor lock's happens-before guarantee. `hasData`, a simple one-directional flag, correctly uses just `volatile` — it doesn't need the broader atomicity `synchronized` provides, since it's never read-then-conditionally-written based on its own value.

## 6. Walkthrough

Tracing `AllThreePropertiesTogether.main`:

1. `recorder` calls `record(v)` for each of the five values in sequence. Each call enters `synchronized (lock)`, conditionally updates `min` and/or `max`, and exits the block — because both fields are updated within the same critical section, no other thread could ever observe (via the same lock) a state where only one of the two has been updated for a given call.
2. After the `synchronized` block, `hasData = true` is set (a `volatile` write) — signaling that at least one recording has occurred. Since this happens after every `record` call, by the time the main thread joins `recorder`, `hasData` is `true`.
3. `main` calls `recorder.join()` — this itself is a happens-before source (everything `recorder` did happens-before the join returning), so even without the `volatile`/`synchronized` mechanisms, `main`'s subsequent reads would technically be safe *in this specific case*, purely because of `join()`'s own guarantee. The `volatile`/`synchronized` design remains correct and would still be necessary in a version of this code where multiple concurrent readers check `printSnapshot()` without a `join()`-based happens-before edge available.
4. `printSnapshot()` checks `hasData` (true), then re-enters `synchronized (lock)` to read `min` and `max` together — this re-acquisition of the same lock the writer used ensures the reader sees a fully consistent, atomically-updated pair of values, never a partial or torn combination.
5. The printed result, `min=3, max=47`, correctly reflects the true minimum and maximum of the five recorded values — reliably atomic across the pair, reliably visible from the recording thread to whichever thread calls `printSnapshot()`, and reliably ordered with respect to each other.

## 7. Gotchas & takeaways

> **Gotcha:** it's tempting to reach for `volatile` on every shared field as a blanket "make it thread-safe" habit — but `volatile` only ever addresses visibility and ordering for that individual field, never atomicity across multiple related fields or across a read-modify-write sequence on that same field. Diagnosing *which* of the three properties a specific piece of shared state actually needs (sometimes more than one) is the necessary step before reaching for any particular tool.

- Atomicity, visibility, and ordering are three distinct concurrency properties that can each fail independently — fixing one does not fix the others.
- `volatile` provides visibility and ordering for a single field's individual accesses, but never atomicity for compound (read-modify-write) operations on that field.
- `Atomic*` classes provide atomicity (and visibility) for their own specific single-variable operations, but not automatically across multiple different variables updated together.
- `synchronized` provides all three properties within its critical section's scope — atomicity for everything inside the block as a unit, plus visibility and ordering via the monitor lock's happens-before guarantee.
- Before choosing a concurrency tool for a piece of shared mutable state, explicitly ask which of the three properties it actually needs — sometimes more than one — rather than defaulting to whichever tool is most familiar.
