---
card: java
gi: 871
slug: deadlock-causes-prevention
title: Deadlock (causes & prevention)
---

## 1. What it is

A **deadlock** is a state where two or more threads are each waiting for a lock (or resource) that another thread in the same group already holds, and none of them can ever proceed — every thread is stuck forever. The classic minimal case is two threads and two locks: Thread A holds Lock 1 and waits for Lock 2, while Thread B holds Lock 2 and waits for Lock 1. Neither can release what it holds until it gets what it's waiting for, and neither ever will — a permanent standstill with no exception thrown and no error logged, just threads that silently never make progress again.

## 2. Why & when

Deadlock is a risk any time code acquires more than one lock at a time — which happens naturally whenever an operation needs to touch two or more shared, independently-locked resources, like transferring money between two bank accounts, or two objects that reference and lock each other. Understanding the four necessary conditions for deadlock (mutual exclusion, hold-and-wait, no preemption, circular wait) matters because breaking just *one* of them prevents deadlock entirely — in practice, the easiest one to break is **circular wait**: if every thread that needs multiple locks always acquires them in the same, globally-agreed order, a cycle can never form. Recognize the risk whenever you write code that nests `synchronized` blocks or holds one lock while trying to acquire another, especially when the objects being locked are chosen dynamically (e.g., based on method arguments) rather than in a fixed, hardcoded order.

## 3. Core concept

```java
// DEADLOCK-PRONE: lock order depends on argument order, not on the objects' identity
void transfer(Account from, Account to, int amount) {
    synchronized (from) {
        synchronized (to) {
            from.balance -= amount;
            to.balance += amount;
        }
    }
}
// transfer(a, b, 10) run concurrently with transfer(b, a, 10) can deadlock:
// thread 1 locks a, waits for b; thread 2 locks b, waits for a -- circular wait, forever.
```

The bug isn't the nested locking itself — it's that two concurrent calls can lock the *same two objects* in *opposite orders*, creating exactly the cycle deadlock requires.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Thread 1 holds lock A and waits for lock B; Thread 2 holds lock B and waits for lock A -- a circular wait with no possible progress">
  <rect x="40" y="20" width="160" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Thread 1 holds A</text>

  <rect x="440" y="20" width="160" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="520" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Thread 2 holds B</text>

  <rect x="40" y="120" width="160" height="40" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="120" y="145" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Lock B (unavailable)</text>

  <rect x="440" y="120" width="160" height="40" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="520" y="145" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Lock A (unavailable)</text>

  <line x1="120" y1="60" x2="120" y2="118" stroke="#f85149" stroke-width="2" marker-end="url(#a9)"/>
  <text x="130" y="90" fill="#f85149" font-size="10" font-family="sans-serif">waits for</text>

  <line x1="520" y1="60" x2="520" y2="118" stroke="#f85149" stroke-width="2" marker-end="url(#a9)"/>
  <text x="530" y="90" fill="#f85149" font-size="10" font-family="sans-serif">waits for</text>

  <line x1="200" y1="140" x2="436" y2="140" stroke="#f85149" stroke-width="1" stroke-dasharray="3"/>
  <line x1="600" y1="140" x2="600" y2="30" stroke="#f85149" stroke-width="1" stroke-dasharray="3"/>
  <text x="320" y="180" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Circular wait: neither thread can ever proceed</text>

  <defs><marker id="a9" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker></defs>
</svg>

*Each thread holds what the other needs and needs what the other holds — a cycle with no possible resolution.*

## 5. Runnable example

Scenario: transferring funds between two accounts, growing from a deadlock-prone naive version (reproduced with a deliberately widened race window so it reliably hangs), to a lock-ordering fix, to a `tryLock`-with-timeout fallback that detects and recovers from potential deadlock instead of merely avoiding it structurally.

### Level 1 — Basic

```java
public class DeadlockProne {
    static class Account {
        int balance = 1000;
    }

    static void transfer(Account from, Account to, int amount) {
        synchronized (from) {
            try { Thread.sleep(50); } catch (InterruptedException ignored) {} // widen the race window
            synchronized (to) {
                from.balance -= amount;
                to.balance += amount;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Account a = new Account();
        Account b = new Account();

        Thread t1 = new Thread(() -> transfer(a, b, 100)); // locks a, then wants b
        Thread t2 = new Thread(() -> transfer(b, a, 50));  // locks b, then wants a -- OPPOSITE order

        t1.start();
        t2.start();

        // In a real run, this likely HANGS FOREVER -- both threads deadlocked.
        // We use a timed join here just to demonstrate detection rather than hang the whole build.
        t1.join(2000);
        t2.join(2000);
        System.out.println("t1 alive (still deadlocked)? " + t1.isAlive());
        System.out.println("t2 alive (still deadlocked)? " + t2.isAlive());
    }
}
```

**How to run:** `java DeadlockProne.java` (JDK 17+). Note: this program is deliberately deadlock-prone; the timed `join(2000)` calls are only there so the demonstration exits instead of hanging forever.

Expected output (both threads genuinely deadlocked and still alive after the timeout):
```
t1 alive (still deadlocked)? true
t2 alive (still deadlocked)? true
```

`t1` locks `a` then waits for `b`; `t2` locks `b` then waits for `a` — a textbook circular wait. Both threads are stuck permanently; the JVM detects nothing and throws no exception.

### Level 2 — Intermediate

```java
public class LockOrderingFix {
    static class Account {
        final int id; // used purely to establish a consistent global lock order
        int balance = 1000;
        Account(int id) { this.id = id; }
    }

    static void transfer(Account from, Account to, int amount) {
        Account first = from.id < to.id ? from : to;  // ALWAYS lock the lower id first
        Account second = first == from ? to : from;
        synchronized (first) {
            synchronized (second) {
                from.balance -= amount;
                to.balance += amount;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Account a = new Account(1);
        Account b = new Account(2);

        Thread t1 = new Thread(() -> transfer(a, b, 100)); // wants to lock a then b -- but ordering forces id order
        Thread t2 = new Thread(() -> transfer(b, a, 50));  // wants to lock b then a -- ordering ALSO forces id order

        t1.start();
        t2.start();
        t1.join();
        t2.join();

        System.out.println("account a balance = " + a.balance);
        System.out.println("account b balance = " + b.balance);
        System.out.println("no deadlock -- both transfers completed");
    }
}
```

**How to run:** `java LockOrderingFix.java`.

Expected output:
```
account a balance = 950
account b balance = 1050
no deadlock -- both transfers completed
```

The real-world concern added: regardless of which direction a transfer moves money, both threads now agree to lock `Account` objects in a fixed order determined by `id`, not by argument position — breaking the circular-wait condition entirely, so no deadlock can occur no matter how the two threads interleave.

### Level 3 — Advanced

```java
import java.util.concurrent.locks.*;
import java.util.concurrent.*;

public class TryLockWithTimeoutFallback {
    static class Account {
        final int id;
        final ReentrantLock lock = new ReentrantLock();
        int balance = 1000;
        Account(int id) { this.id = id; }
    }

    static boolean transfer(Account from, Account to, int amount) throws InterruptedException {
        long deadline = System.currentTimeMillis() + 500;
        while (System.currentTimeMillis() < deadline) {
            if (from.lock.tryLock(50, TimeUnit.MILLISECONDS)) {
                try {
                    if (to.lock.tryLock(50, TimeUnit.MILLISECONDS)) {
                        try {
                            from.balance -= amount;
                            to.balance += amount;
                            return true; // success
                        } finally {
                            to.lock.unlock();
                        }
                    }
                    // couldn't get `to` -- release `from` and retry, breaking any potential deadlock
                } finally {
                    from.lock.unlock();
                }
            }
            // brief backoff before retrying, reducing the chance of repeatedly colliding with another retrier
            Thread.sleep(10);
        }
        return false; // gave up -- caller can log, retry later, or alert
    }

    public static void main(String[] args) throws InterruptedException {
        Account a = new Account(1);
        Account b = new Account(2);
        ExecutorService pool = Executors.newFixedThreadPool(2);

        Future<Boolean> f1 = pool.submit(() -> transfer(a, b, 100)); // a -> b
        Future<Boolean> f2 = pool.submit(() -> transfer(b, a, 50));  // b -> a, opposite direction

        try {
            System.out.println("transfer 1 succeeded? " + f1.get());
            System.out.println("transfer 2 succeeded? " + f2.get());
        } catch (ExecutionException e) {
            System.out.println("unexpected error: " + e.getCause());
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("final: a=" + a.balance + ", b=" + b.balance);
    }
}
```

**How to run:** `java TryLockWithTimeoutFallback.java`.

Expected output:
```
transfer 1 succeeded? true
transfer 2 succeeded? true
final: a=950, b=1050
```

This adds the production-flavored hard case: even *without* a fixed lock order, using `tryLock(timeout)` instead of a plain blocking `lock()` means a thread that can't get the second lock within its timeout releases the first one and retries, rather than holding it forever — this breaks the "hold-and-wait" deadlock condition instead of the "circular wait" condition, giving deadlock *recovery* as a safety net even in code that (for whatever structural reason) can't easily enforce a consistent lock order.

## 6. Walkthrough

Tracing `TryLockWithTimeoutFallback` when both `transfer(a, b, 100)` and `transfer(b, a, 50)` happen to race:

1. Say thread 1 (running `transfer(a, b, 100)`) calls `from.lock.tryLock(50ms)` on `a` and succeeds, while thread 2 (running `transfer(b, a, 50)`) calls `from.lock.tryLock(50ms)` on `b` and also succeeds — at this instant, both threads hold exactly one lock each, mirroring the classic deadlock setup.
2. Thread 1 then calls `to.lock.tryLock(50ms)` on `b` — but thread 2 already holds it, so this call blocks for up to 50ms, then returns `false` if `b` still isn't free.
3. Symmetrically, thread 2's `tryLock` on `a` also very likely times out, since thread 1 still holds it.
4. Because both `tryLock` calls failed, both threads' `finally` blocks release the one lock they *did* acquire (`from.lock.unlock()`) — this is the critical difference from a plain nested `synchronized`, which offers no way to "give up and release" a lock it already entered.
5. Both threads then sleep 10ms and retry from the top of the `while` loop — since the two prior attempts already released their locks, there's no permanent deadlock; on a subsequent retry (very likely, given randomized OS thread scheduling), one thread manages to acquire both locks before the other grabs even the first one, and completes its transfer.
6. Once one transfer fully commits and releases both locks, the other thread's next retry finds both locks free, acquires them, and completes as well.
7. Both `Future.get()` calls in `main` return `true`, and the final balances (`a=950`, `b=1050`) confirm both transfers succeeded exactly once each, with no deadlock and no lost or duplicated funds — despite the initial lock-acquisition race mirroring the exact pattern that would permanently deadlock under plain nested `synchronized`.

## 7. Gotchas & takeaways

> **Gotcha:** deadlock produces **no exception, no error, no log line** by default — the affected threads simply stop making progress forever. Diagnosing it in production typically requires a thread dump (`jstack` or a monitoring tool), which will explicitly report "Found one Java-level deadlock" along with the exact lock-holding/waiting cycle.

- Deadlock requires four conditions simultaneously (mutual exclusion, hold-and-wait, no preemption, circular wait) — breaking any one prevents it; consistent [lock ordering](0873-lock-ordering-avoidance.md) is usually the cheapest fix, since it eliminates circular wait entirely.
- When lock order can't be fixed structurally, `tryLock(timeout)` with a release-and-retry loop trades a hang for a bounded, recoverable delay.
- Never nest locks acquired in an order that depends on caller-supplied argument order — always derive the order from something intrinsic and consistent, like an object's ID or `hashCode()`.
- A deadlock between just two threads and two locks is the simplest case; larger deadlocks can form cycles across three or more threads and locks, which are harder to spot by code review alone — thread dumps or dedicated deadlock-detection tooling become more valuable as the system grows.
- Test deadlock-prone code under real concurrent load, not just single-threaded — as `DeadlockProne` shows, code can look completely correct in isolation and only reveal the bug under genuine thread interleaving.
