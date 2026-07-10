---
card: java
gi: 872
slug: livelock-starvation
title: Livelock & starvation
---

## 1. What it is

**Livelock** is when threads are *not* blocked — they're actively running, repeatedly changing state in response to each other — but the system as a whole never makes real progress, because every thread keeps "politely" backing off for the other, over and over, forever. It's deadlock's more embarrassing cousin: instead of freezing silently, the threads burn CPU busily doing nothing useful. **Starvation** is a related but distinct problem: a thread is repeatedly denied access to a resource it needs (a lock, CPU time, a turn in a queue) because other threads keep getting priority over it — it isn't deadlocked or livelocked, it's just perpetually unlucky, and in principle could still eventually run, but never actually does under the observed conditions.

## 2. Why & when

Livelock most often shows up in code written specifically to *avoid* deadlock via retry-and-back-off logic (like "if I can't get both locks, release what I have and try again") — if every competing thread's back-off logic is symmetric and deterministic, they can end up perfectly, repeatedly colliding and backing off in lockstep, never making progress. The fix is usually to add **randomized** backoff (jitter) so competing threads eventually desynchronize, or to give one thread priority to break the symmetry. Starvation typically comes from an **unfair** lock or scheduler policy under sustained heavy contention — a fast, frequently-arriving thread can repeatedly "barge in" ahead of a thread that's been patiently waiting, especially with default (unfair) `synchronized` or `ReentrantLock` semantics; the fix is a fair lock (see [`ReentrantLock` & fairness](0867-reentrantlock-fairness.md)) or a scheduling policy that explicitly bounds how long any one requester can be skipped over.

## 3. Core concept

```java
// LIVELOCK-PRONE: two "polite" threads that both back off identically when they can't proceed
void politeTransfer(Account from, Account to) {
    while (true) {
        if (from.lock.tryLock()) {
            try {
                if (to.lock.tryLock()) {
                    try { /* do the work */ return; }
                    finally { to.lock.unlock(); }
                }
            } finally { from.lock.unlock(); } // release and retry -- but WITHOUT any randomness
        }
        // no delay, or a FIXED delay -- if both threads do this in lockstep, neither ever wins
    }
}
```

If two threads both back off the *same* way every time, they can keep re-colliding on every retry — technically running, technically "trying," but never actually completing.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads repeatedly acquiring one lock, failing to get the second, releasing, and retrying in perfect lockstep -- livelock, no progress despite constant activity">
  <rect x="20" y="20" width="260" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="43" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">T1: lock A, try B -- fails, release A</text>

  <rect x="340" y="20" width="260" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="470" y="43" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">T2: lock B, try A -- fails, release B</text>

  <rect x="20" y="70" width="260" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="93" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">T1: retries -- lock A again...</text>

  <rect x="340" y="70" width="260" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="470" y="93" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">T2: retries -- lock B again...</text>

  <line x1="150" y1="55" x2="150" y2="68" stroke="#8b949e" stroke-width="2" marker-end="url(#a10)"/>
  <line x1="470" y1="55" x2="470" y2="68" stroke="#8b949e" stroke-width="2" marker-end="url(#a10)"/>
  <text x="320" y="130" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">Both threads active, both "trying" -- neither ever succeeds. Repeats forever.</text>
  <defs><marker id="a10" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Unlike deadlock, both threads are constantly doing work — just never anything that actually finishes.*

## 5. Runnable example

Scenario: two accounts being "politely" transferred between, growing from a livelock-prone symmetric-backoff version (bounded so the demo terminates), to a jittered-backoff fix, to a version that also protects against starvation using a fair lock so no thread is perpetually skipped.

### Level 1 — Basic

```java
import java.util.concurrent.locks.*;
import java.util.concurrent.atomic.*;

public class LivelockProne {
    static class Account {
        final ReentrantLock lock = new ReentrantLock();
    }

    static AtomicInteger attempts = new AtomicInteger(0);

    static boolean politeTransfer(Account from, Account to) {
        for (int i = 0; i < 20; i++) { // bounded so this demo terminates -- real livelock has no bound
            attempts.incrementAndGet();
            if (from.lock.tryLock()) {
                try {
                    if (to.lock.tryLock()) {
                        try { return true; } finally { to.lock.unlock(); }
                    }
                    // couldn't get `to` -- release `from` immediately and retry, NO delay, NO randomness
                } finally { from.lock.unlock(); }
            }
        }
        return false; // gave up after the bound -- a real livelock would spin forever
    }

    public static void main(String[] args) throws InterruptedException {
        Account a = new Account();
        Account b = new Account();

        Thread t1 = new Thread(() -> System.out.println("t1 succeeded? " + politeTransfer(a, b)));
        Thread t2 = new Thread(() -> System.out.println("t2 succeeded? " + politeTransfer(b, a)));
        t1.start(); t2.start();
        t1.join(); t2.join();
        System.out.println("total attempts made across both threads: " + attempts.get());
    }
}
```

**How to run:** `java LivelockProne.java` (JDK 17+).

Expected output shape (a real, unbounded livelock might never print anything at all; this bounded version demonstrates wasted attempts):
```
t1 succeeded? false
t2 succeeded? false
total attempts made across both threads: 40
```

Both threads keep acquiring their first lock, failing on the second (because the other thread grabbed it in the opposite order at nearly the same instant), releasing, and retrying — with no randomness in the retry timing, they can keep re-colliding attempt after attempt, exhausting the bound without ever succeeding.

### Level 2 — Intermediate

```java
import java.util.concurrent.locks.*;
import java.util.concurrent.atomic.*;
import java.util.concurrent.ThreadLocalRandom;

public class JitteredBackoffFix {
    static class Account {
        final ReentrantLock lock = new ReentrantLock();
    }

    static AtomicInteger attempts = new AtomicInteger(0);

    static boolean politeTransfer(Account from, Account to) throws InterruptedException {
        for (int i = 0; i < 20; i++) {
            attempts.incrementAndGet();
            if (from.lock.tryLock()) {
                try {
                    if (to.lock.tryLock()) {
                        try { return true; } finally { to.lock.unlock(); }
                    }
                } finally { from.lock.unlock(); }
            }
            // RANDOM backoff -- breaks the lockstep symmetry that causes livelock
            Thread.sleep(ThreadLocalRandom.current().nextInt(1, 10));
        }
        return false;
    }

    public static void main(String[] args) throws InterruptedException {
        Account a = new Account();
        Account b = new Account();

        Thread t1 = new Thread(() -> {
            try { System.out.println("t1 succeeded? " + politeTransfer(a, b)); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        Thread t2 = new Thread(() -> {
            try { System.out.println("t2 succeeded? " + politeTransfer(b, a)); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        t1.start(); t2.start();
        t1.join(); t2.join();
        System.out.println("total attempts made across both threads: " + attempts.get() + " (usually far fewer than the worst case)");
    }
}
```

**How to run:** `java JitteredBackoffFix.java`.

Expected output shape (attempt count is much lower and progress is now reliable):
```
t1 succeeded? true
t2 succeeded? true
total attempts made across both threads: 3 (usually far fewer than the worst case)
```

The real-world concern added: a small **randomized** delay before each retry. Because the two threads' backoff durations are no longer identical or synchronized, they very quickly desynchronize — one of them ends up retrying slightly before or after the other, breaking the perfect collision pattern and letting one of them successfully acquire both locks.

### Level 3 — Advanced

```java
import java.util.concurrent.locks.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class FairLockAvoidsStarvation {
    static final ReentrantLock fairLock = new ReentrantLock(true); // fair -- prevents starvation
    static final AtomicInteger[] serviceOrder = new AtomicInteger[1];

    public static void main(String[] args) throws InterruptedException {
        serviceOrder[0] = new AtomicInteger(0);
        int workers = 6;
        CountDownLatch startGate = new CountDownLatch(1);
        ExecutorService pool = Executors.newFixedThreadPool(workers);
        int[] serviceRank = new int[workers];

        for (int i = 0; i < workers; i++) {
            final int id = i;
            pool.submit(() -> {
                try {
                    startGate.await(); // release all workers at once, maximizing contention
                    fairLock.lock();
                    try {
                        serviceRank[id] = serviceOrder[0].incrementAndGet();
                    } finally {
                        fairLock.unlock();
                    }
                } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            });
        }

        startGate.countDown();
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        for (int i = 0; i < workers; i++) {
            System.out.println("worker " + i + " served at rank " + serviceRank[i]);
        }
        System.out.println("with a FAIR lock, every worker is guaranteed eventual service -- none starves");
    }
}
```

**How to run:** `java FairLockAvoidsStarvation.java`.

Expected output shape (exact ranks vary by submission/thread-arrival order, but crucially every worker gets a distinct rank 1 through 6 — none is skipped):
```
worker 0 served at rank 1
worker 1 served at rank 2
worker 2 served at rank 3
worker 3 served at rank 4
worker 4 served at rank 5
worker 5 served at rank 6
with a FAIR lock, every worker is guaranteed eventual service -- none starves
```

This adds the production-flavored hard case: under sustained heavy contention with an **unfair** lock, a fast or luckily-scheduled thread can keep barging ahead of others indefinitely, starving them. Using `new ReentrantLock(true)` (fair mode) guarantees strict FIFO acquisition order, so every one of the six workers is served exactly once, in a well-defined order, with no possibility that any single worker is passed over forever.

## 6. Walkthrough

Tracing `FairLockAvoidsStarvation.main`:

1. Six worker tasks are submitted, each immediately blocking on `startGate.await()` so all six are ready to contend for `fairLock` at essentially the same instant, once released.
2. `startGate.countDown()` releases all six workers simultaneously, maximizing real contention on `fairLock`.
3. Because `fairLock` was constructed with `true`, its internal wait queue grants the lock strictly in the order requests were registered — even though all six requests arrive in a tight burst, the JVM records a definite arrival order and honors it, rather than letting scheduling luck or CPU cache effects let one thread repeatedly cut in line.
4. Each worker, once granted the lock, increments the shared `serviceOrder` counter and records its own resulting rank into `serviceRank[id]`, then releases the lock — allowing the fair queue to grant it to the next-in-line waiter.
5. After all six workers finish, `main` prints each worker's assigned rank. Because the lock is fair, the six ranks are guaranteed to be a permutation of 1 through 6 — no rank is skipped, and critically, no single worker could have been made to wait behind an unbounded number of "cutting" newcomers, which is exactly the starvation risk an *unfair* lock would carry under the same contention pattern.
6. The final `println` underscores the key difference from livelock: here, every thread performed useful work and finished — nothing spun uselessly; fairness is about *order* and *eventual service*, not about avoiding wasted busy-work the way jittered backoff fixes livelock.

## 7. Gotchas & takeaways

> **Gotcha:** livelock is easy to introduce by accident specifically when *fixing* deadlock with a naive "release and retry" pattern — if the retry logic is perfectly deterministic and symmetric across competing threads, you can trade a silent, permanent freeze (deadlock) for a noisy, permanent spin (livelock), which is not obviously better and can be harder to notice since CPU usage looks "busy" rather than idle.

- Livelock: threads are active and changing state, but the system never converges to actual progress — usually caused by symmetric, deterministic retry/backoff logic colliding repeatedly.
- The standard fix for livelock is randomized backoff (jitter) so competing threads' retry timings desynchronize, or breaking symmetry by giving one thread explicit priority.
- Starvation: a thread is repeatedly denied a resource due to unfair scheduling or unfair lock policy, even though it isn't blocked or deadlocked — it's simply never lucky enough to win the race.
- The standard fix for starvation under lock contention is a fair lock (`new ReentrantLock(true)`), which guarantees FIFO acquisition order at some throughput cost.
- Livelock and starvation are both harder to detect than deadlock — there's no thread-dump signature that flags them the way "Found one Java-level deadlock" does; they usually surface as unexplained slowness, high CPU with no throughput, or specific requests that never seem to complete.
