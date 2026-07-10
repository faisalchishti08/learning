---
card: java
gi: 864
slug: synchronized-methods
title: synchronized methods
---

## 1. What it is

Marking an entire method `synchronized` makes the JVM acquire a lock before running the method body and release it when the method returns (normally or via exception). For an **instance** method, the lock acquired is the monitor of `this` — the object the method was called on. For a **static** method, the lock acquired is the monitor of the class's `Class` object itself, shared across every instance. Only one thread can be executing inside any `synchronized` method that shares the same lock object at a time; every other thread calling it blocks until the lock is released.

## 2. Why & when

Synchronized methods are the simplest way to make a whole operation on an object thread-safe: if every method that touches an object's mutable state is `synchronized`, no two threads can ever interleave their reads and writes of that state, eliminating data races on it. Use them when an object has one or two pieces of related mutable state and most or all of its methods need protecting — a simple counter, a small in-memory cache, a mutable bank-account-style object. They are the wrong tool when you need finer-grained control (locking only part of a method, or using two different locks for two different pieces of state), or when contention is high and you need a lock with more features, such as fairness or interruptibility — that's when [`ReentrantLock`](0867-reentrantlock-fairness.md) becomes the better choice.

## 3. Core concept

```java
class Counter {
    private int count = 0;

    public synchronized void increment() { // acquires lock on `this`
        count++;
    } // releases lock on `this`, even if an exception were thrown

    public synchronized int get() {        // acquires the SAME lock on `this`
        return count;
    }

    public static synchronized void resetGlobalStats() { // locks Counter.class, not any instance
        // ...
    }
}
```

`increment()` and `get()` share the same lock (`this`), so calls to either from different threads are mutually exclusive with each other — a thread cannot read a value while another thread is midway through updating it.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads calling synchronized methods on the same object; only one holds the monitor at a time, the other blocks and waits">
  <rect x="20" y="20" width="220" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="130" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Thread A: increment() -- holds lock</text>

  <rect x="260" y="20" width="220" height="40" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="370" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Thread B: get() -- BLOCKED, waiting</text>

  <rect x="260" y="90" width="220" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="370" y="115" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Thread B: get() -- now holds lock</text>

  <line x1="130" y1="60" x2="130" y2="150" stroke="#6db33f" stroke-width="2" stroke-dasharray="4"/>
  <text x="130" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">A releases lock on return</text>
  <line x1="240" y1="150" x2="365" y2="105" stroke="#79c0ff" stroke-width="2" marker-end="url(#a3)"/>

  <defs><marker id="a3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

*Both methods share the same monitor (`this`), so Thread B cannot enter `get()` until Thread A finishes and releases the lock, even though the two methods look unrelated in the source.*

## 5. Runnable example

Scenario: a shared `BankAccount` object, starting with an unsynchronized (buggy) version, then correctly synchronized, then extended with a `synchronized` transfer method that must lock two accounts without deadlocking.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class UnsynchronizedAccount {
    static class BankAccount {
        int balance = 0;
        void deposit(int amount) {
            balance = balance + amount; // read, add, write -- not atomic, NOT synchronized
        }
    }

    public static void main(String[] args) throws InterruptedException {
        BankAccount account = new BankAccount();
        ExecutorService pool = Executors.newFixedThreadPool(4);
        for (int i = 0; i < 1000; i++) {
            pool.submit(() -> account.deposit(1));
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("expected 1000, got " + account.balance + " (likely less, due to lost updates)");
    }
}
```

**How to run:** `java UnsynchronizedAccount.java` (JDK 17+).

Expected output shape:
```
expected 1000, got 947 (likely less, due to lost updates)
```

Without synchronization, concurrent `deposit` calls race on the read-modify-write of `balance`, silently losing updates — the exact count varies by run.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class SynchronizedAccount {
    static class BankAccount {
        private int balance = 0;

        synchronized void deposit(int amount) { // locks `this`
            balance = balance + amount;
        }

        synchronized int getBalance() { // same lock as deposit -- mutually exclusive with it
            return balance;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        BankAccount account = new BankAccount();
        ExecutorService pool = Executors.newFixedThreadPool(4);
        for (int i = 0; i < 1000; i++) {
            pool.submit(() -> account.deposit(1));
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("expected 1000, got " + account.getBalance() + " (always exact, now correctly synchronized)");
    }
}
```

**How to run:** `java SynchronizedAccount.java`.

Expected output:
```
expected 1000, got 1000 (always exact, now correctly synchronized)
```

The real-world concern added: making the read-modify-write of `balance` atomic by wrapping it in a `synchronized` method, and also synchronizing the *read* (`getBalance`) with the same lock, so a reader never observes a value mid-update. Every one of the 1000 concurrent deposits is now correctly counted.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class SynchronizedTransfer {
    static class BankAccount {
        private final String id;
        private int balance;
        BankAccount(String id, int balance) { this.id = id; this.balance = balance; }

        synchronized void withdraw(int amount) { balance -= amount; }
        synchronized void deposit(int amount) { balance += amount; }
        synchronized int getBalance() { return balance; }
    }

    // Transfers between two accounts, always locking in a FIXED global order to avoid deadlock
    static void transfer(BankAccount from, BankAccount to, int amount) {
        BankAccount first = from.id.compareTo(to.id) < 0 ? from : to;
        BankAccount second = first == from ? to : from;
        synchronized (first) {
            synchronized (second) {
                from.withdraw(amount);
                to.deposit(amount);
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        BankAccount a = new BankAccount("A", 500);
        BankAccount b = new BankAccount("B", 500);

        ExecutorService pool = Executors.newFixedThreadPool(4);
        for (int i = 0; i < 100; i++) {
            pool.submit(() -> transfer(a, b, 1)); // a -> b
            pool.submit(() -> transfer(b, a, 1)); // b -> a, opposite direction
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        System.out.println("account A: " + a.getBalance());
        System.out.println("account B: " + b.getBalance());
        System.out.println("total: " + (a.getBalance() + b.getBalance()) + " (must stay 1000, no deadlock, no lost funds)");
    }
}
```

**How to run:** `java SynchronizedTransfer.java`.

Expected output shape (exact per-account split varies, total is always exact):
```
account A: 500
account B: 500
total: 1000 (must stay 1000, no deadlock, no lost funds)
```

This adds the production-flavored hard case: transferring between *two* locked objects at once, in both directions concurrently (some threads transfer A→B, others B→A). Locking `from` then `to` naively would deadlock, since two opposite-direction transfers could each hold one account's lock while waiting for the other's. The fix orders the locks by a fixed, consistent key (`id`) regardless of transfer direction, so every thread acquires the two locks in the same global order — see [lock ordering & avoidance](0873-lock-ordering-avoidance.md) for the general pattern.

## 6. Walkthrough

Tracing one call to `transfer(a, b, 1)` versus a concurrent `transfer(b, a, 1)`:

1. Both calls compute `first`/`second` by comparing `"A".compareTo("B")`, which is negative, so **both** calls agree `first = a`, `second = b`, regardless of which direction the money is actually moving.
2. Whichever thread reaches `synchronized (first)` (i.e., `synchronized (a)`) first acquires `a`'s monitor; the other thread blocks at that same line.
3. The winning thread then acquires `synchronized (second)` (`b`'s monitor) — since it already holds `a` and no other thread can hold `b` while trying to acquire `a` (both threads agree on the order), this second acquisition always succeeds without waiting on a thread that is itself waiting on this one.
4. Inside both locks, `from.withdraw(amount)` and `to.deposit(amount)` run — each of those is itself `synchronized` on the respective account, which is harmless re-entrant-style safety on top of the outer lock already held.
5. The nested `synchronized` blocks release in reverse order as the method returns: `second`'s monitor first, then `first`'s.
6. The blocked thread from step 2 now acquires `a`, then `b`, and performs its own transfer — with the same fixed ordering, so it never deadlocks against the first thread, no matter which direction its transfer moves money.
7. After all 200 submitted transfers complete, `getBalance()` on each account (itself `synchronized`, so it never reads mid-update) confirms the total is unchanged at 1000, with no lost or duplicated funds.

## 7. Gotchas & takeaways

> **Gotcha:** `synchronized` on an instance method locks `this` — but if some code elsewhere also synchronizes on the *same object* using a plain `synchronized (someObject) { }` block, or if the object is exposed and another class locks on it for an unrelated reason, you can get surprising, hard-to-trace contention or deadlocks between logically unrelated pieces of code that happen to share a lock object.

- A `synchronized` instance method locks `this`; a `synchronized` static method locks the class object — these are different locks, so mixing them does not automatically synchronize instance and static state together.
- Methods marked `synchronized` on the same object are mutually exclusive with **each other**, not just with themselves — a reader method and a writer method sharing the lock correctly prevent torn reads.
- When an operation needs two objects' locks at once (like a transfer), always acquire them in a fixed, globally-agreed order to avoid [deadlock](0871-deadlock-causes-prevention.md).
- `synchronized` locks are reentrant: a thread already holding a lock can call another `synchronized` method that needs the same lock without blocking on itself — see [intrinsic locks & reentrancy](0866-intrinsic-locks-reentrancy.md).
- For finer control than "lock the whole method" — partial-method locking, timed or interruptible acquisition, or multiple independent read/write locks — reach for explicit lock objects such as [`ReentrantLock`](0867-reentrantlock-fairness.md) or [`ReadWriteLock`](0868-readwritelock.md) instead.
