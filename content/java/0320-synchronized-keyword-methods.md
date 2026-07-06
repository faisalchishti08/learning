---
card: java
gi: 320
slug: synchronized-keyword-methods
title: synchronized keyword (methods)
---

## 1. What it is

Marking a method `synchronized` means only one thread at a time can be executing that method **on the same object instance** (for instance methods) or **for the same class** (for static methods) — any other thread attempting to call it must wait until the first thread finishes. This is Java's built-in mechanism for protecting shared, mutable state from being corrupted by concurrent access.

```java
public class SynchronizedDemo {
    static int counter = 0;

    static synchronized void increment() {
        counter++;
    }

    public static void main(String[] args) throws InterruptedException {
        Thread[] threads = new Thread[100];
        for (int i = 0; i < 100; i++) {
            threads[i] = new Thread(SynchronizedDemo::increment);
            threads[i].start();
        }
        for (Thread t : threads) t.join();

        System.out.println("Final counter: " + counter); // reliably 100
    }
}
```

`static synchronized void increment()` ensures that even with 100 threads calling it concurrently, only one thread at a time can actually execute `counter++` — without `synchronized`, this same code would very likely produce a final count *less* than 100, due to lost updates from unsynchronized concurrent increments.

## 2. Why & when

Multiple threads reading and writing the same shared, mutable data without coordination is a data race: operations that look atomic in source code (like `counter++`) are actually multiple separate steps (read, increment, write) under the hood, and two threads interleaving those steps can lose updates or see inconsistent state. `synchronized` methods provide mutual exclusion — a guarantee that only one thread executes the protected code at a time — solving this class of problem.

- **Protecting shared mutable state** — any time multiple threads read and write the same field(s), synchronizing the methods that touch it prevents lost updates and inconsistent intermediate states.
- **Compound operations that must be atomic** — a "check-then-act" sequence (like checking a balance before withdrawing) needs to happen as one indivisible unit from other threads' perspective; wrapping it in a `synchronized` method achieves that.
- **Simplicity** — for straightforward cases, `synchronized` methods are easier to read and reason about correctly than manually managing lower-level locks.

Synchronize any method that reads or writes shared mutable state accessed by multiple threads. For instance methods, the lock is the object instance itself (`this`) — different instances have independent locks, so synchronized instance methods on two different objects never block each other. For static methods, the lock is the class object itself, shared across all instances. Over-synchronizing (locking far more than necessary) hurts performance by serializing work that didn't actually need to be serialized; under-synchronizing risks real correctness bugs — getting the boundary right matters.

## 3. Core concept

```java
public class SynchronizedCore {
    static class Account {
        private int balance = 100;

        synchronized void withdraw(int amount) {
            if (balance >= amount) {
                balance -= amount;
                System.out.println(Thread.currentThread().getName() + " withdrew " + amount + ", balance now " + balance);
            } else {
                System.out.println(Thread.currentThread().getName() + " denied: insufficient funds (balance " + balance + ")");
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Account account = new Account();
        Runnable task = () -> account.withdraw(60);

        Thread t1 = new Thread(task);
        Thread t2 = new Thread(task);
        t1.start();
        t2.start();
        t1.join();
        t2.join();
    }
}
```

With `withdraw` synchronized, the check (`balance >= amount`) and the act (`balance -= amount`) happen as one atomic unit with respect to other threads calling `withdraw` on the *same* `account` object — exactly one of the two threads succeeds (leaving `balance` at 40), and the other is correctly denied, since it can't observe the pre-withdrawal balance of 100 anymore by the time it gets the lock.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads call a synchronized method on the same object; the second must wait until the first releases the lock">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#6db33f" font-size="10" font-family="monospace">Thread 1: ---acquire lock---[in withdraw()]---release lock---</text>
  <text x="20" y="65" fill="#79c0ff" font-size="10" font-family="monospace">Thread 2: ---try acquire===BLOCKED===acquire---[in withdraw()]---release---</text>
  <text x="20" y="105" fill="#8b949e" font-size="9">Thread 2 cannot enter withdraw() on the SAME object until Thread 1's lock is released.</text>
</svg>

Only one thread at a time holds the lock for a given object's synchronized methods; others queue up and wait their turn.

## 5. Runnable example

Scenario: a shared bank account subject to concurrent withdrawals, evolved from an unsynchronized (buggy) version into a correctly synchronized one, then into a version demonstrating that synchronizing on the correct object matters — synchronizing on the wrong thing provides no real protection at all.

### Level 1 — Basic

```java
public class SynchronizedBasic {
    static class Account {
        private int balance = 1000;

        void withdraw(int amount) { // NOT synchronized -- intentionally buggy
            if (balance >= amount) {
                try { Thread.sleep(1); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                balance -= amount;
            }
        }

        int getBalance() { return balance; }
    }

    public static void main(String[] args) throws InterruptedException {
        Account account = new Account();
        Thread[] threads = new Thread[20];
        for (int i = 0; i < 20; i++) {
            threads[i] = new Thread(() -> account.withdraw(100));
            threads[i].start();
        }
        for (Thread t : threads) t.join();

        System.out.println("Final balance: " + account.getBalance() + " (expected 0 if all 20 withdrawals of 100 succeeded correctly)");
    }
}
```

**How to run:** `java SynchronizedBasic.java`

Twenty threads each attempt to withdraw 100 from a 1000 balance — without synchronization, the small `Thread.sleep(1)` between the check and the deduction makes it very likely multiple threads pass the check before any of them actually deducts, so the final balance frequently comes out *negative* (more was withdrawn than the balance ever actually had), a visible demonstration of the race condition.

### Level 2 — Intermediate

Same account, now with `withdraw` properly synchronized, fixing the race by making the check-then-deduct sequence atomic with respect to other threads.

```java
public class SynchronizedIntermediate {
    static class Account {
        private int balance = 1000;

        synchronized void withdraw(int amount) { // FIXED: now synchronized
            if (balance >= amount) {
                try { Thread.sleep(1); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                balance -= amount;
            }
        }

        synchronized int getBalance() { return balance; }
    }

    public static void main(String[] args) throws InterruptedException {
        Account account = new Account();
        Thread[] threads = new Thread[20];
        for (int i = 0; i < 20; i++) {
            threads[i] = new Thread(() -> account.withdraw(100));
            threads[i].start();
        }
        for (Thread t : threads) t.join();

        System.out.println("Final balance: " + account.getBalance() + " (never negative now)");
    }
}
```

**How to run:** `java SynchronizedIntermediate.java`

With `withdraw` synchronized, each thread must fully complete its check-then-deduct sequence (including the artificial `Thread.sleep(1)`) before another thread can even begin its own call to `withdraw` on the same `account` — the final balance is now reliably `0`, exactly `1000 - (20 * ... )` capped correctly since once the balance is insufficient, later threads correctly see the updated, lower balance and are denied.

### Level 3 — Advanced

Same account, now demonstrating a real, subtle mistake: synchronizing on the wrong lock object (a `new Object()` created fresh inside the method, rather than the shared account instance) provides **no actual protection**, since each call synchronizes on a *different* object — contrasted with correctly synchronizing on `this` (the shared account), which properly serializes access.

```java
public class SynchronizedAdvanced {
    static class BrokenAccount {
        private int balance = 1000;

        void withdraw(int amount) {
            Object wrongLock = new Object(); // BUG: a NEW object every single call -- provides no real mutual exclusion
            synchronized (wrongLock) {
                if (balance >= amount) {
                    try { Thread.sleep(1); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                    balance -= amount;
                }
            }
        }
        int getBalance() { return balance; }
    }

    static class FixedAccount {
        private int balance = 1000;

        void withdraw(int amount) {
            synchronized (this) { // FIXED: the SAME object for every call on this instance
                if (balance >= amount) {
                    try { Thread.sleep(1); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                    balance -= amount;
                }
            }
        }
        synchronized int getBalance() { return balance; }
    }

    static int runWithdrawals(Runnable withdrawTask) throws InterruptedException {
        Thread[] threads = new Thread[20];
        for (int i = 0; i < 20; i++) {
            threads[i] = new Thread(withdrawTask);
            threads[i].start();
        }
        for (Thread t : threads) t.join();
        return -1; // caller reads balance separately
    }

    public static void main(String[] args) throws InterruptedException {
        BrokenAccount broken = new BrokenAccount();
        runWithdrawals(() -> broken.withdraw(100));
        System.out.println("Broken account (wrong lock) final balance: " + broken.getBalance() + " (often negative!)");

        FixedAccount fixed = new FixedAccount();
        runWithdrawals(() -> fixed.withdraw(100));
        System.out.println("Fixed account (correct lock) final balance: " + fixed.getBalance() + " (never negative)");
    }
}
```

**How to run:** `java SynchronizedAdvanced.java`

`BrokenAccount.withdraw` creates a brand-new `Object` as its lock **every single time it's called** — since `synchronized (wrongLock)` only excludes other threads trying to acquire that *same* object's lock, and no two calls ever share the same `wrongLock` instance, this provides zero actual mutual exclusion between concurrent calls, reproducing the exact race condition from Level 1 despite the code superficially looking "synchronized"; `FixedAccount.withdraw` correctly synchronizes on `this` — the one, shared account instance — genuinely serializing access exactly as `synchronized` methods in Level 2 did.

## 6. Walkthrough

Trace why `BrokenAccount` fails while `FixedAccount` succeeds, step by step.

**Inside `BrokenAccount.withdraw`, called by two threads nearly simultaneously.** Thread A calls `withdraw(100)`: `Object wrongLock = new Object()` creates lock object `#A`, and Thread A enters `synchronized (#A) { ... }`. At essentially the same moment, Thread B calls `withdraw(100)`: it creates its *own*, entirely distinct lock object `#B`, and enters `synchronized (#B) { ... }`. Since `#A` and `#B` are different objects, the JVM's lock mechanism sees no conflict whatsoever — both threads proceed to check `balance >= amount` and, after their respective `Thread.sleep(1)`, deduct from `balance`, completely unaware of each other. This is exactly the same race condition as the unsynchronized Level 1 code, just with `synchronized` syntax present but structurally powerless.

**Inside `FixedAccount.withdraw`, called by the same two threads.** Thread A calls `withdraw(100)` and enters `synchronized (this)` — acquiring the lock on the one `FixedAccount` instance shared by both threads. Thread B, calling `withdraw(100)` on that *same* instance, attempts `synchronized (this)` too, but since Thread A already holds that exact lock, Thread B blocks, waiting. Only after Thread A completes its entire `withdraw` call (check, sleep, deduct) and exits the `synchronized` block does Thread B acquire the lock and proceed — by which point it correctly sees the *updated* `balance`, exactly as the properly-synchronized Level 2 version behaved.

**Running both scenarios with 20 threads each.** For `BrokenAccount`, the lack of real mutual exclusion means many threads can pass the `balance >= amount` check before any of them has actually deducted, leading to far more than the balance's worth of successful-looking deductions — the final balance frequently prints as a large negative number. For `FixedAccount`, genuine mutual exclusion means each of the 20 threads' check-then-deduct sequences happens strictly one at a time, so the final balance is reliably and correctly `0` (10 successful withdrawals of 100 each, with the remaining 10 correctly denied once the balance is insufficient).

```
BrokenAccount: each call creates its OWN lock object -> synchronized blocks NEVER actually conflict
  Thread A: synchronized(#A) { check, sleep, deduct }
  Thread B: synchronized(#B) { check, sleep, deduct }   <- runs freely in parallel, no real exclusion

FixedAccount: every call locks on the SAME "this" -> synchronized blocks genuinely serialize
  Thread A: synchronized(account) { check, sleep, deduct }
  Thread B: synchronized(account) { ...BLOCKED until A finishes... } { check, sleep, deduct }
```

**Output (illustrative — the broken account's exact negative value varies by run):**
```
Broken account (wrong lock) final balance: -900 (often negative!)
Fixed account (correct lock) final balance: 0 (never negative)
```

## 7. Gotchas & takeaways

> `synchronized` only provides mutual exclusion between calls that lock on the **exact same object**. Synchronizing on a freshly created object (`new Object()` created inside the method, as in `BrokenAccount`), on a different field, or on a per-call local variable provides **zero** real protection — it looks synchronized but structurally can never block a competing call. Always synchronize on a single, shared, stable object (typically `this` for instance methods, or the class object for static ones).

> Instance `synchronized` methods lock on `this`, so two different object instances have entirely independent locks — a thread inside `account1.withdraw(...)` never blocks a different thread inside `account2.withdraw(...)`, even for two `Account` instances of the same class. If shared state needs protecting across multiple objects, a shared, common lock object is needed instead.

- `synchronized` methods ensure only one thread at a time executes that method on a given object (instance methods) or class (static methods), preventing race conditions on shared mutable state.
- Instance methods lock on `this`; static methods lock on the class object — different instances have independent locks.
- The lock object must be the exact same object across all competing calls — locking on a per-call or per-instance-varying object provides no real mutual exclusion, despite appearing synchronized.
- Synchronize methods that touch shared mutable state accessed by multiple threads; avoid over-synchronizing work that doesn't actually need serialization, since it needlessly hurts concurrency.
