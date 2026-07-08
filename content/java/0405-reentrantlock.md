---
card: java
gi: 405
slug: reentrantlock
title: ReentrantLock
---

## 1. What it is

`ReentrantLock` (in `java.util.concurrent.locks`) is an explicit lock object that does the same fundamental job as a `synchronized` block — ensuring only one thread executes a critical section at a time — but as a regular object you call `.lock()` and `.unlock()` on, rather than a language keyword. "Reentrant" means the same thread can acquire the lock again while already holding it (e.g. a locked method calling another locked method on the same object) without deadlocking itself, exactly like `synchronized`. Unlike `synchronized`, it adds `tryLock()` (attempt to acquire without blocking, or with a timeout) and an optional **fairness** policy (first-come-first-served ordering among waiting threads).

## 2. Why & when

`synchronized` is simple and safe — the JVM automatically releases the lock even if an exception is thrown — but it's inflexible: you can't try to acquire it without blocking, can't time out a wait, can't interrupt a thread that's stuck waiting for it, and can't easily check whether it's currently held. `ReentrantLock` exists for the situations where you need that extra control: avoiding deadlock by backing off if a lock isn't available within a reasonable time (`tryLock(timeout, unit)`), allowing a blocked thread to be interrupted (`lockInterruptibly()`), or needing multiple independent wait conditions on one lock (see the Condition objects tutorial).

The cost of that flexibility is that **you must remember to unlock it yourself**, in a `finally` block — nothing does it automatically like `synchronized` does. Reach for `ReentrantLock` when you specifically need `tryLock`, fairness, interruptible waiting, or multiple `Condition`s; stick with `synchronized` for straightforward mutual exclusion where those extras aren't needed.

## 3. Core concept

```java
import java.util.concurrent.locks.ReentrantLock;

ReentrantLock lock = new ReentrantLock();

lock.lock();
try {
    // critical section: only one thread can be in here at a time
} finally {
    lock.unlock(); // MUST be in finally -- if the critical section throws, the lock still gets released
}
```

The `try/finally` pattern isn't optional decoration — it's the whole safety mechanism. With `synchronized`, the JVM releases the lock automatically on the way out, even via an exception. With `ReentrantLock`, if you forget the `finally` and the critical section throws, the lock stays held forever, and every other thread waiting on it deadlocks permanently.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads transferring money must both acquire the same ReentrantLock before touching shared account balances; the second thread waits until the first calls unlock">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <rect x="240" y="20" width="160" height="40" rx="6" fill="#1c2430" stroke="#e6edf3"/>
  <text x="320" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ReentrantLock (1 permit)</text>

  <rect x="30" y="90" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="115" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Thread A: lock() -&gt; acquired</text>

  <rect x="430" y="90" width="180" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="520" y="115" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Thread B: lock() -&gt; WAITS</text>

  <text x="320" y="155" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Thread B proceeds only after Thread A calls unlock() in its finally block</text>
</svg>

Only one thread holds the lock at a time; others attempting `.lock()` block until it's released.

## 5. Runnable example

Scenario: transferring money between two in-memory bank accounts — the same transfer operation, evolved from a naive unsynchronized version that loses money under concurrency, through a `ReentrantLock`-protected version, to one using `tryLock` with a timeout to avoid deadlocking when transfers happen in both directions at once.

### Level 1 — Basic

```java
public class BankTransferUnsafe {
    static int balanceA = 1000;
    static int balanceB = 1000;

    static void transfer(int amount) {
        balanceA -= amount; // NOT atomic as a pair -- another thread can interleave here
        balanceB += amount;
    }

    public static void main(String[] args) throws InterruptedException {
        Runnable job = () -> {
            for (int i = 0; i < 1000; i++) transfer(1);
        };

        Thread t1 = new Thread(job);
        Thread t2 = new Thread(job);
        t1.start(); t2.start();
        t1.join(); t2.join();

        System.out.println("A=" + balanceA + " B=" + balanceB + " total=" + (balanceA + balanceB) + " (expected 2000)");
    }
}
```

**How to run:** `java BankTransferUnsafe.java`

Two threads each transfer $1, 1000 times, with zero synchronization — updates to `balanceA` and `balanceB` can interleave (read-modify-write races on plain `int` fields), so the total printed is often *not* 2000, silently losing or duplicating money.

### Level 2 — Intermediate

```java
import java.util.concurrent.locks.ReentrantLock;

public class BankTransferLocked {
    static int balanceA = 1000;
    static int balanceB = 1000;
    static final ReentrantLock lock = new ReentrantLock();

    static void transfer(int amount) {
        lock.lock();
        try {
            balanceA -= amount;
            balanceB += amount;
        } finally {
            lock.unlock(); // always released, even if the critical section threw
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Runnable job = () -> {
            for (int i = 0; i < 1000; i++) transfer(1);
        };

        Thread t1 = new Thread(job);
        Thread t2 = new Thread(job);
        t1.start(); t2.start();
        t1.join(); t2.join();

        System.out.println("A=" + balanceA + " B=" + balanceB + " total=" + (balanceA + balanceB) + " (expected 2000)");
    }
}
```

**How to run:** `java BankTransferLocked.java`

Wrapping the two-field update in `lock.lock()` / `try` / `finally { lock.unlock(); }` makes it atomic as a unit — no other thread can execute `transfer` while one thread's decrement-then-increment is in progress. The total is now reliably 2000 every run.

### Level 3 — Advanced

```java
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

public class BankTransferTryLock {
    static int balanceA = 1000;
    static int balanceB = 1000;
    static final ReentrantLock lock = new ReentrantLock(true); // fair: first-come-first-served among waiters

    static boolean transfer(String label, int amount) throws InterruptedException {
        // tryLock with a timeout avoids blocking forever if the lock is heavily contested
        if (lock.tryLock(200, TimeUnit.MILLISECONDS)) {
            try {
                balanceA -= amount;
                balanceB += amount;
                return true;
            } finally {
                lock.unlock();
            }
        } else {
            System.out.println(label + ": could not acquire lock in time, skipping this transfer");
            return false;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Runnable job = () -> {
            String name = Thread.currentThread().getName();
            int succeeded = 0;
            for (int i = 0; i < 1000; i++) {
                try {
                    if (transfer(name, 1)) succeeded++;
                } catch (InterruptedException ignored) { }
            }
            System.out.println(name + " completed " + succeeded + " transfers");
        };

        Thread t1 = new Thread(job, "worker-1");
        Thread t2 = new Thread(job, "worker-2");
        t1.start(); t2.start();
        t1.join(); t2.join();

        System.out.println("A=" + balanceA + " B=" + balanceB + " total=" + (balanceA + balanceB));
    }
}
```

**How to run:** `java BankTransferTryLock.java`

`new ReentrantLock(true)` uses **fair ordering**: when multiple threads are waiting, the one that's been waiting longest acquires the lock next, preventing one thread from being starved indefinitely by another that keeps re-acquiring it. `tryLock(200, TimeUnit.MILLISECONDS)` additionally means a thread gives up and moves on after 200ms rather than blocking forever — the total still ends up consistent because every successful transfer that *does* happen is still correctly atomic.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `lock` is created with `fair=true`. Two worker threads, `worker-1` and `worker-2`, each attempt 1000 transfers of $1.

Each call to `transfer(label, 1)` first calls `lock.tryLock(200, TimeUnit.MILLISECONDS)`. If the lock is free, this returns `true` almost instantly, and the calling thread proceeds into the `try` block: `balanceA -= 1` then `balanceB += 1`. Because the fairness policy is enabled, if *both* threads happen to be waiting for the lock at the same moment, whichever has been waiting longer is granted it next — no thread can "cut the line" by repeatedly re-requesting the lock faster than the other.

Since 200ms is an extremely generous timeout for a critical section that only does two `int` field updates (which completes in nanoseconds), in practice `tryLock` almost always succeeds immediately for both threads — the "could not acquire lock in time" branch exists as a defensive safeguard for a heavily contested lock in a slower or more complex critical section, not something you'd expect to see fire here. Whichever thread doesn't currently hold the lock simply waits its (fair) turn.

Once a thread's `try` block finishes (the two field updates), the `finally { lock.unlock(); }` runs, releasing the lock so the next waiting thread (in fair order) can proceed. Each thread tallies how many of its 1000 attempted transfers actually succeeded in `succeeded`, and prints that count once its loop finishes.

After both threads finish (`join()` returns for each), `main` prints the final balances. Because every transfer that *did* succeed was fully atomic (protected by the lock for its entire decrement-and-increment), the sum `balanceA + balanceB` always remains exactly `2000`, regardless of how many transfers each thread individually completed or how their timing interleaved.

Expected output (exact per-worker transfer counts may vary slightly based on timing, but totals are stable):
```
worker-1 completed 1000 transfers
worker-2 completed 1000 transfers
A=1000 B=1000 total=2000
```

## 7. Gotchas & takeaways

> Unlike `synchronized`, `ReentrantLock` is **never released automatically**. If you call `.lock()` and the code that follows throws before reaching `.unlock()`, and that call isn't inside a `finally` block, the lock stays held forever — every other thread waiting on it deadlocks permanently. Always structure it as `lock.lock(); try { ... } finally { lock.unlock(); }`, with the `lock()` call itself *outside* the `try`.

- `ReentrantLock` does the same job as `synchronized` but as an explicit object with `.lock()`/`.unlock()`, adding `tryLock()` (non-blocking or timed acquisition) and an optional fairness policy.
- "Reentrant" means the same thread can safely acquire the lock multiple times (e.g. nested method calls) without deadlocking on itself — each `lock()` call must be matched by an `unlock()` call.
- Always release in a `finally` block — this is not automatic, unlike `synchronized`.
- `new ReentrantLock(true)` enables **fairness**: waiting threads are served in the order they started waiting, at some throughput cost compared to the default unfair mode.
- `tryLock()` and `tryLock(timeout, unit)` let a thread avoid blocking indefinitely — useful for avoiding deadlock scenarios where backing off and retrying is safer than waiting forever.
