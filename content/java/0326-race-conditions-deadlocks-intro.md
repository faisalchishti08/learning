---
card: java
gi: 326
slug: race-conditions-deadlocks-intro
title: Race conditions & deadlocks (intro)
---

## 1. What it is

A **race condition** happens when two or more threads access shared mutable state, at least one of them writes to it, and the final result depends on the unpredictable timing of which thread runs when — the program "races" between threads and the outcome is not guaranteed to be correct or consistent. A **deadlock** is a different failure mode: two or more threads each hold a lock the other needs, and each waits forever for the other to release it, so none of them ever makes progress again.

```java
public class RaceDemo {
    static int counter = 0; // shared, unsynchronized -- a race condition waiting to happen

    public static void main(String[] args) throws InterruptedException {
        Runnable increment = () -> {
            for (int i = 0; i < 100_000; i++) counter++; // read-modify-write, not atomic
        };
        Thread t1 = new Thread(increment);
        Thread t2 = new Thread(increment);
        t1.start(); t2.start();
        t1.join(); t2.join();
        System.out.println("Expected 200000, got: " + counter); // often less than 200000
    }
}
```

Both threads read, increment, and write `counter` independently; when their operations interleave, one thread's increment can be overwritten by the other's, silently losing updates.

## 2. Why & when

Race conditions arise because `counter++` is not one CPU-level operation — it is read, add one, then write back — and between any of those steps, another thread can slip in and change the same field. Deadlocks arise from lock ordering: if thread A locks resource X then waits for Y, while thread B locks Y then waits for X, neither can ever proceed.

- **Any shared mutable field, collection, or resource touched by more than one thread** without synchronization is a candidate for a race condition — counters, caches, shared lists, flags with compound updates.
- **Multiple locks acquired in different orders by different code paths** is the classic setup for deadlock — a "transfer money between two accounts" method that locks the source account then the destination is a textbook example if a concurrent transfer locks them in the opposite order.
- **Recognizing symptoms** matters as much as recognizing causes: races often show up as "it works 99% of the time" flaky bugs; deadlocks show up as a program that hangs completely, with all relevant threads stuck in `BLOCKED` state forever.

Both problems are avoided the same general way: minimize shared mutable state, use proper synchronization (`synchronized`, locks, atomic classes) for anything shared, and always acquire multiple locks in a single, consistent global order across the whole codebase.

## 3. Core concept

```java
public class DeadlockCore {
    static final Object lockA = new Object();
    static final Object lockB = new Object();

    public static void main(String[] args) throws InterruptedException {
        Thread t1 = new Thread(() -> {
            synchronized (lockA) {
                sleep(50);
                synchronized (lockB) { System.out.println("t1 got both locks"); }
            }
        });
        Thread t2 = new Thread(() -> {
            synchronized (lockB) { // opposite order from t1 -- the deadlock trigger
                sleep(50);
                synchronized (lockA) { System.out.println("t2 got both locks"); }
            }
        });
        t1.start(); t2.start();
        t1.join(3000); t2.join(3000);
        System.out.println("t1 alive: " + t1.isAlive() + ", t2 alive: " + t2.isAlive());
    }

    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) {} }
}
```

**How to run:** `java DeadlockCore.java`

`t1` locks `lockA` then waits for `lockB`; `t2` locks `lockB` then waits for `lockA` — after the 50ms sleep, each thread holds the lock the other needs and neither can ever proceed, so `join(3000)` times out and both threads print as still alive.

## 4. Diagram

<svg viewBox="0 0 600 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="deadlock cycle: t1 holds lockA waiting for lockB, t2 holds lockB waiting for lockA">
  <rect x="8" y="8" width="584" height="164" rx="8" fill="#0d1117"/>
  <rect x="40" y="30" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="55" fill="#79c0ff" font-size="11" text-anchor="middle">Thread t1</text>
  <rect x="40" y="120" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="145" fill="#6db33f" font-size="11" text-anchor="middle">lockA (held by t1)</text>

  <rect x="420" y="30" width="120" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="480" y="55" fill="#f85149" font-size="11" text-anchor="middle">Thread t2</text>
  <rect x="420" y="120" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="145" fill="#6db33f" font-size="11" text-anchor="middle">lockB (held by t2)</text>

  <text x="170" y="150" fill="#8b949e" font-size="10">t1 waits for lockB →</text>
  <text x="270" y="50" fill="#8b949e" font-size="10">← t2 waits for lockA</text>
</svg>

Each thread holds one lock and waits on the other, forming a cycle with no possible exit — the definition of deadlock.

## 5. Runnable example

Scenario: a bank-account transfer between two accounts, evolved from an unsynchronized version with a real race condition, into a synchronized-but-deadlock-prone version, into a production-style fix using a consistent global lock ordering to eliminate the deadlock entirely.

### Level 1 — Basic

```java
public class TransferBasic {
    static int accountA = 1000;
    static int accountB = 1000;

    public static void main(String[] args) throws InterruptedException {
        Runnable transferAtoB = () -> {
            for (int i = 0; i < 1000; i++) {
                accountA -= 1; // NOT synchronized -- a race condition
                accountB += 1;
            }
        };
        Thread t1 = new Thread(transferAtoB);
        Thread t2 = new Thread(transferAtoB);
        t1.start(); t2.start();
        t1.join(); t2.join();
        System.out.println("A=" + accountA + " B=" + accountB + " total=" + (accountA + accountB));
    }
}
```

**How to run:** `java TransferBasic.java`

The total should always stay 2000 (money is only moved, never created or destroyed), but because `accountA -= 1` and `accountB += 1` are each read-modify-write races between `t1` and `t2`, some updates get lost — running this repeatedly can print totals that drift away from 2000, a direct, visible consequence of the race condition.

### Level 2 — Intermediate

```java
public class TransferIntermediate {
    static int accountA = 1000;
    static int accountB = 1000;
    static final Object lockA = new Object();
    static final Object lockB = new Object();

    public static void main(String[] args) throws InterruptedException {
        Thread t1 = new Thread(() -> transfer(lockA, lockB, true));
        Thread t2 = new Thread(() -> transfer(lockB, lockA, false)); // opposite lock order!
        t1.start(); t2.start();
        t1.join(3000); t2.join(3000);
        System.out.println("t1 alive: " + t1.isAlive() + ", t2 alive: " + t2.isAlive());
    }

    static void transfer(Object first, Object second, boolean aToB) {
        synchronized (first) {
            try { Thread.sleep(10); } catch (InterruptedException e) {}
            synchronized (second) {
                if (aToB) { accountA -= 1000; accountB += 1000; }
                else { accountB -= 1000; accountA += 1000; }
                System.out.println("Transfer complete, A=" + accountA + " B=" + accountB);
            }
        }
    }
}
```

**How to run:** `java TransferIntermediate.java`

The race condition on the balances is now fixed — both locks are held while updating — but `t1` acquires `lockA` then `lockB` while `t2` acquires `lockB` then `lockA`, the classic inconsistent lock ordering, which reliably deadlocks: both threads print as still alive after the 3-second timeout, and "Transfer complete" never prints for either.

### Level 3 — Advanced

```java
public class TransferAdvanced {
    static int accountA = 1000;
    static int accountB = 1000;
    static final Object lockA = new Object();
    static final Object lockB = new Object();

    public static void main(String[] args) throws InterruptedException {
        Thread t1 = new Thread(() -> transfer(true));
        Thread t2 = new Thread(() -> transfer(false));
        t1.start(); t2.start();
        t1.join(3000); t2.join(3000);
        System.out.println("t1 alive: " + t1.isAlive() + ", t2 alive: " + t2.isAlive());
        System.out.println("Final A=" + accountA + " B=" + accountB + " total=" + (accountA + accountB));
    }

    // Both directions ALWAYS lock in the same global order: lockA before lockB.
    static void transfer(boolean aToB) {
        synchronized (lockA) {
            try { Thread.sleep(10); } catch (InterruptedException e) {}
            synchronized (lockB) {
                if (aToB) { accountA -= 1000; accountB += 1000; }
                else { accountB -= 1000; accountA += 1000; }
                System.out.println("Transfer complete, A=" + accountA + " B=" + accountB);
            }
        }
    }
}
```

**How to run:** `java TransferAdvanced.java`

By making every call site acquire `lockA` before `lockB`, regardless of transfer direction, no thread can ever hold one lock while waiting for the other in reverse — this eliminates the deadlock (both transfers complete, threads terminate, `isAlive()` prints `false`) while keeping the balances race-free (total remains 2000).

## 6. Walkthrough

Execution starts in `main`, which creates `t1` and `t2` and starts them nearly simultaneously — from this point their execution interleaves unpredictably.

`t1` calls `transfer(true)` and enters `synchronized (lockA)`, acquiring `lockA`. `t2` calls `transfer(false)` and also tries `synchronized (lockA)` first — because both directions now use the same lock order, `t2` blocks waiting for `lockA` to be released, instead of grabbing `lockB` and creating the reverse-order deadlock seen in Level 2.

`t1`, holding `lockA` alone, sleeps 10ms (simulating some work between acquiring the two locks), then enters `synchronized (lockB)`, acquiring the second lock. With both locks held, it updates `accountA -= 1000` and `accountB += 1000`, prints "Transfer complete, A=0 B=2000", then releases `lockB`, and finally releases `lockA` as it exits both synchronized blocks.

Only now does `t2`'s blocked attempt to acquire `lockA` succeed. It sleeps 10ms, acquires `lockB`, updates the balances in the opposite direction (`accountB -= 1000`, `accountA += 1000`), prints "Transfer complete, A=1000 B=1000", and releases both locks.

Back in `main`, `t1.join(3000)` and `t2.join(3000)` both return quickly because both threads have already terminated — `isAlive()` prints `false` for both, and the final balances print as `A=1000 B=1000` with `total=2000`, confirming no money was lost and no deadlock occurred.

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="t1 acquires lockA then lockB and completes; t2 waits for lockA, then acquires it after t1 releases, then completes">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">t1: lock(A) → sleep(10) → lock(B) → update balances → unlock(B) → unlock(A)</text>
  <text x="20" y="55" fill="#f85149" font-size="10">t2: lock(A) BLOCKS until t1 releases it (same order avoids reverse-wait cycle)</text>
  <text x="20" y="80" fill="#f85149" font-size="10">t2: (after t1 done) lock(A) → sleep(10) → lock(B) → update balances → unlock(B) → unlock(A)</text>
  <text x="20" y="110" fill="#6db33f" font-size="10">Result: both transfers complete sequentially, total stays 2000, no deadlock.</text>
</svg>

## 7. Gotchas & takeaways

> A program that "usually works" is not proof of correctness under concurrency — race conditions and deadlocks are timing-dependent, so a bug can pass thousands of test runs and still fail in production under different load or hardware.

- A race condition needs shared mutable state plus at least one writer plus no synchronization — remove any one of those three and the race disappears.
- Deadlock requires a *cycle* of threads each holding a lock another needs — the standard fix is a single, consistent global lock-acquisition order everywhere in the codebase.
- `synchronized` fixes races but does not automatically fix deadlocks — you can synchronize correctly and still deadlock if lock ordering is inconsistent.
- Symptoms differ: races often look like occasional wrong answers ("it worked 999 times, then didn't"); deadlocks look like a total hang, with threads stuck in `BLOCKED` state forever (visible in a thread dump).
- Prefer higher-level concurrency utilities (`java.util.concurrent` classes, `ReentrantLock` with tryLock timeouts, atomic classes) over hand-rolled locking wherever possible — they are easier to reason about and harder to misuse.
