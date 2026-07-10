---
card: java
gi: 860
slug: data-races
title: Data races
---

## 1. What it is

A **data race** occurs, by the Java Memory Model's formal definition, when two or more threads access the same variable concurrently, at least one of those accesses is a write, and there is no [happens-before](0857-happens-before-relationship.md) relationship ordering the accesses relative to each other. The JMM makes an especially strong statement about programs containing data races: they have **no defined behavior at all** — not just "the result of this specific race is unpredictable," but the compiler and JVM are permitted to assume data-race-free execution when optimizing, meaning a genuine data race can, in principle, produce behavior that looks bizarre or impossible relative to the source code (though in practice, most observed effects are the familiar "stale value" or "lost update" kind covered elsewhere in this section).

## 2. Why & when

This formal definition matters because it's stricter than the intuitive notion of "two threads touched the same variable at almost the same time" — a data race specifically requires the *absence* of any happens-before edge between the conflicting accesses, which is exactly the condition [`synchronized`](0857-happens-before-relationship.md), [`volatile`](0858-volatile-semantics.md), and the `Atomic*` classes are each designed to prevent, each in their own way. Recognizing a data race in code — shared mutable state, accessed by multiple threads, with at least one write, and no synchronization mechanism connecting the accesses — is the single most important diagnostic skill in concurrent programming, because a data-race-containing program isn't merely "occasionally wrong under heavy load"; it's formally undefined, meaning testing it extensively on one machine provides no genuine assurance about its behavior on another machine, JVM version, or even a different run under different optimization decisions.

## 3. Core concept

```java
// A genuine data race: shared mutable state, no happens-before edge connecting the accesses.
class RaceExample {
    int sharedValue = 0; // plain field
    void writer() { sharedValue = 42; }      // a WRITE
    void reader() { System.out.println(sharedValue); } // a READ, concurrent with the write, no synchronization
}
// If writer() and reader() run on different threads with no join/volatile/synchronized connecting them,
// this IS a data race by the JMM's formal definition -- regardless of what value actually gets printed.

// NOT a data race: proper synchronization establishes a happens-before edge.
class RaceFreeExample {
    volatile int sharedValue = 0; // volatile write/read pairs ARE ordered by a happens-before edge
    void writer() { sharedValue = 42; }
    void reader() { System.out.println(sharedValue); } // guaranteed to see 42, once the write has happened
}
```

The two classes look nearly identical, but only one satisfies the JMM's formal absence-of-data-race condition — the difference is entirely in whether a recognized happens-before edge connects the writing and reading actions.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A data race requires concurrent access to the same variable, at least one write, and no happens-before edge connecting the accesses">
  <g font-family="sans-serif">
    <rect x="40" y="30" width="180" height="45" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
    <text x="130" y="57" fill="#e6edf3" font-size="10" text-anchor="middle">same variable</text>

    <rect x="240" y="30" width="180" height="45" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
    <text x="330" y="57" fill="#e6edf3" font-size="10" text-anchor="middle">at least one WRITE</text>

    <rect x="440" y="30" width="180" height="45" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
    <text x="530" y="57" fill="#e6edf3" font-size="10" text-anchor="middle">NO happens-before edge</text>
  </g>
  <text x="320" y="110" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">ALL THREE conditions together = data race = formally UNDEFINED behavior</text>
  <text x="320" y="135" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Fix any ONE condition (usually by adding a happens-before edge) and the race is eliminated</text>
</svg>

*All three conditions must hold simultaneously for a genuine data race — removing any one (typically by establishing a happens-before edge) eliminates it.*

## 5. Runnable example

Scenario: a shared results buffer accumulated by a worker and read by the main thread, growing from a demonstrated, genuine data race, through identifying and fixing it with proper synchronization, to a realistic multi-field scenario requiring the whole update to be treated as one atomic, race-free unit.

### Level 1 — Basic

```java
public class GenuineDataRace {
    static int result = 0; // plain field, NO synchronization connects writer and reader

    public static void main(String[] args) throws InterruptedException {
        Thread writer = new Thread(() -> {
            result = 42; // a WRITE, with no happens-before edge to any reader
        });
        writer.start();

        // Reading "result" here, concurrently with writer's write, with NOTHING connecting the two
        // accesses, is a genuine data race by the JMM's definition -- regardless of what prints below.
        System.out.println("result read concurrently (formally undefined): " + result);

        writer.join(); // note: this happens AFTER the race-condition read above, so it doesn't help here
    }
}
```

**How to run:** `java GenuineDataRace.java` (JDK 17+). This will likely print `0` most runs (since the main thread's read probably executes before the writer thread has even started running its single instruction), but occasionally might print `42`, and per the JMM's formal definition, no particular outcome is actually guaranteed — this is exactly the "no defined behavior" consequence of a genuine data race.

Expected output shape (either value is a "valid" demonstration of the underlying point):
```
result read concurrently (formally undefined): 0
```

This is a genuine data race: `result` is written by `writer` and read by `main`, concurrently, with no `join()`, `volatile`, or `synchronized` connecting the two accesses *before* the read happens. The read's outcome is formally undefined — whichever value happens to print is not a guarantee about future runs, different JVMs, or different hardware.

### Level 2 — Intermediate

```java
public class RaceFixedWithJoin {
    static int result = 0;

    public static void main(String[] args) throws InterruptedException {
        Thread writer = new Thread(() -> {
            result = 42;
        });
        writer.start();
        writer.join(); // establishes a happens-before edge: everything writer did happens-before this returning

        // NOW this read is race-free -- join() connects the write to this read with a guaranteed edge.
        System.out.println("result read AFTER join() (guaranteed correct): " + result);
    }
}
```

**How to run:** `java RaceFixedWithJoin.java`.

Expected output:
```
result read AFTER join() (guaranteed correct): 42
```

The real-world concern added: simply moving the read to **after** `writer.join()` eliminates the data race entirely — `join()` is a recognized happens-before source, so `result`'s write is now guaranteed visible to the subsequent read, with a deterministic, always-correct outcome, unlike the previous version's formally undefined read.

### Level 3 — Advanced

```java
public class MultiFieldRaceFixed {
    static final Object lock = new Object();
    static int sum = 0;
    static int count = 0; // sum and count must ALWAYS be updated and read together, consistently

    static void record(int value) {
        synchronized (lock) { // atomicity + visibility + ordering for BOTH fields together
            sum += value;
            count++;
        }
    }

    static double average() {
        synchronized (lock) { // re-acquiring the SAME lock guarantees a consistent (sum, count) pair
            return count == 0 ? 0.0 : (double) sum / count;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread recorder = new Thread(() -> {
            for (int v : new int[]{10, 20, 30, 40}) record(v);
        });
        recorder.start();
        recorder.join();

        System.out.println("average (guaranteed consistent sum/count pair): " + average());
    }
}
```

**How to run:** `java MultiFieldRaceFixed.java`.

Expected output:
```
average (guaranteed consistent sum/count pair): 25.0
```

This adds the production-flavored hard case: a data race is possible not just on a single variable, but across a **pair** of related variables that must be observed consistently together. If `sum` and `count` were each individually made `volatile` but updated in two separate, unsynchronized steps, a reader could observe a `sum` reflecting one more recorded value than `count` does (or vice versa) — individually race-free per-field, but still logically inconsistent as a pair. Wrapping both fields' updates *and* both fields' reads in the same `synchronized (lock)` block eliminates this entirely, guaranteeing `average()` always sees a `sum` and `count` that correspond to exactly the same set of `record` calls.

## 6. Walkthrough

Tracing `MultiFieldRaceFixed.main`:

1. `recorder` calls `record(v)` four times in sequence, each call entering `synchronized (lock)`, updating both `sum` and `count`, and exiting.
2. Because both fields are updated within the same critical section on every call, there is never a moment (observable through the same lock) where `sum` reflects a different number of recorded values than `count` does — they're always updated together, as one atomic unit, from any other thread's perspective that also uses this lock.
3. `main` calls `recorder.join()`, establishing a happens-before edge between everything `recorder` did (all four `record` calls) and the subsequent code in `main`.
4. `average()` is called, which itself enters `synchronized (lock)` before reading `sum` and `count` together — even though the `join()` from step 3 would already guarantee visibility here, using the same lock for the read as was used for the writes is the more general, robust pattern that would remain correct even in a version of this program with multiple concurrent readers not connected to the writer via `join()`.
5. The computed average, `(10+20+30+40)/4 = 25.0`, is printed — correctly reflecting all four recorded values consistently, with no possibility of having read a `sum` that included one value while `count` reflected a different number of recordings.

## 7. Gotchas & takeaways

> **Gotcha:** a data race being formally "undefined behavior" does not mean it will necessarily crash or produce an obviously wrong value every time — it very often silently "happens to work" during testing (as the JMM's specification allows, since defined behavior is a superset of what's possible, not a prohibition on correct-looking outcomes). The danger is precisely that a program with a genuine data race can pass all its tests reliably on one machine and JVM, then behave differently — subtly or dramatically — under a JIT recompilation, a different CPU architecture, or increased concurrent load in production.

- A data race requires all three conditions simultaneously: concurrent access to the same variable, at least one write among those accesses, and no happens-before relationship connecting them.
- The JMM defines a program containing a genuine data race as having **no defined behavior at all** for that access — not merely "unpredictable in a bounded way."
- Fixing a data race means establishing a happens-before edge between the conflicting accesses — via `volatile`, `synchronized`, `join()`, or another recognized JMM source.
- A data race can exist across multiple related fields even if each individual field is itself race-free (e.g., each independently `volatile`) — related fields that must be observed consistently together need to be updated and read within the *same* synchronized unit.
- Never treat a data race's apparent "correct" behavior during testing as proof of safety — the formal absence of a happens-before edge is the only thing that actually matters, regardless of what any particular test run happens to observe.
