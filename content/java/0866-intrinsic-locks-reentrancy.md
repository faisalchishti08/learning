---
card: java
gi: 866
slug: intrinsic-locks-reentrancy
title: Intrinsic locks & reentrancy
---

## 1. What it is

Every Java object has a built-in ("intrinsic") lock, also called its **monitor** — this is what `synchronized` methods and blocks acquire and release. Intrinsic locks are **reentrant**: if a thread already holds an object's lock and calls another method (or the same method again, e.g. recursively) that also needs to acquire that same lock, it succeeds immediately instead of blocking on itself. The JVM tracks a per-thread hold count for the lock; each nested `synchronized` entry on an already-held lock increments the count, and each exit decrements it — the lock is only actually released back to other threads once the count returns to zero.

## 2. Why & when

Reentrancy exists because it's extremely common for a `synchronized` method to call another `synchronized` method on the same object — a public method delegating to a private helper, an overridden method calling `super.method()`, or a recursive algorithm. Without reentrancy, a thread would deadlock against itself the instant it tried to re-enter its own lock, making `synchronized` all but unusable for any nontrivial class. You benefit from this property any time you design a class with several `synchronized` methods that call each other, or a `synchronized` method that recurses — you don't need to think about it, since the JVM's intrinsic locks are reentrant by default, but you need to understand it to know when it's *not* the safety net you might assume it is (see the gotcha about a subclass acquiring a *different* lock than a superclass method).

## 3. Core concept

```java
class Node {
    synchronized void outer() {
        System.out.println("in outer, calling inner...");
        inner(); // re-enters the SAME lock (this) -- succeeds immediately, does not block
    }

    synchronized void inner() {
        System.out.println("in inner");
    }
}
// A single thread calling outer() acquires `this`'s lock once for outer(),
// then acquires it AGAIN for inner() -- hold count becomes 2, then drops back to 1, then 0.
```

If intrinsic locks were not reentrant, `outer()` calling `inner()` on the same thread would block forever, since the thread would be waiting for a lock it itself already holds and has no way to release until `outer()` returns.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single thread entering outer, acquiring the lock, calling inner which re-enters the same lock, hold count going 1 then 2 then back to 1 then 0">
  <rect x="40" y="20" width="560" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Thread T calls outer() -- acquires lock, hold count = 1</text>

  <rect x="90" y="80" width="460" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="105" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">T calls inner() -- SAME thread, SAME lock, hold count = 2</text>

  <rect x="90" y="130" width="460" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="150" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">inner() returns -- hold count = 1</text>

  <rect x="40" y="170" width="560" height="10" fill="none"/>
  <text x="320" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">outer() returns -- hold count = 0, lock fully released</text>

  <line x1="320" y1="60" x2="320" y2="78" stroke="#79c0ff" stroke-width="2" marker-end="url(#a5)"/>
  <line x1="320" y1="120" x2="320" y2="128" stroke="#8b949e" stroke-width="2" marker-end="url(#a5)"/>
  <defs><marker id="a5" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

*The same thread re-entering its own lock succeeds immediately; only a different thread would actually block.*

## 5. Runnable example

Scenario: a recursive factorial-with-logging class that must synchronize its shared log, growing from a version that would deadlock without reentrancy (shown conceptually), to relying on real reentrancy for recursion, to a subclass-overriding case where a mismatched lock object silently breaks the safety reentrancy normally provides.

### Level 1 — Basic

```java
public class ReentrantRecursion {
    static class Calculator {
        private long callCount = 0;

        synchronized long factorial(int n) {
            callCount++; // shared state, protected by this method's lock
            if (n <= 1) return 1;
            return n * factorial(n - 1); // RE-ENTERS the same lock on `this` -- works fine
        }

        synchronized long getCallCount() {
            return callCount;
        }
    }

    public static void main(String[] args) {
        Calculator calc = new Calculator();
        long result = calc.factorial(5);
        System.out.println("factorial(5) = " + result);
        System.out.println("recursive calls made = " + calc.getCallCount());
    }
}
```

**How to run:** `java ReentrantRecursion.java` (JDK 17+).

Expected output:
```
factorial(5) = 120
recursive calls made = 5
```

Each recursive call to `factorial` re-acquires the same `this` lock the outer call already holds — without reentrancy, this recursive, `synchronized`-on-itself pattern would deadlock on the very first recursive call.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class ReentrancyUnderConcurrency {
    static class Calculator {
        private long callCount = 0;
        synchronized long factorial(int n) {
            callCount++;
            if (n <= 1) return 1;
            return n * factorial(n - 1);
        }
        synchronized long getCallCount() { return callCount; }
    }

    public static void main(String[] args) throws InterruptedException {
        Calculator calc = new Calculator();
        ExecutorService pool = Executors.newFixedThreadPool(4);
        for (int i = 0; i < 20; i++) {
            final int n = 5;
            pool.submit(() -> System.out.println("factorial(" + n + ") = " + calc.factorial(n)));
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("total recursive calls across all threads = " + calc.getCallCount());
    }
}
```

**How to run:** `java ReentrancyUnderConcurrency.java`.

Expected output shape (line order varies, final count is exact):
```
factorial(5) = 120
... (20 lines total)
total recursive calls across all threads = 100
```

The real-world concern added: multiple threads now compete for the *outermost* call to `factorial`, but each individual thread's own chain of recursive re-entries into its already-held lock is unaffected — reentrancy is per-thread, so it never interacts badly with other threads also trying to acquire the lock. Twenty threads times five recursive calls each correctly totals 100.

### Level 3 — Advanced

```java
public class SubclassLockMismatch {
    static class Base {
        protected final Object baseLock = new Object();
        void baseOperation() {
            synchronized (baseLock) {
                System.out.println("Base.baseOperation holding baseLock");
                extensionHook();
            }
        }
        void extensionHook() { /* overridden by subclasses */ }
    }

    static class BuggySubclass extends Base {
        private final Object subclassLock = new Object(); // A DIFFERENT lock object!
        @Override
        void extensionHook() {
            // This does NOT reenter baseLock -- it's a totally different monitor,
            // so if another thread already holds subclassLock, THIS WOULD BLOCK,
            // even though the current thread already holds baseLock.
            synchronized (subclassLock) {
                System.out.println("BuggySubclass.extensionHook holding a DIFFERENT lock (no reentrancy relationship to baseLock)");
            }
        }
    }

    public static void main(String[] args) {
        BuggySubclass obj = new BuggySubclass();
        obj.baseOperation(); // works fine here because nothing else is contending for subclassLock
        System.out.println("completed without contention -- but note: this was NOT true reentrancy,");
        System.out.println("just two independent locks that happened not to be contended concurrently");
    }
}
```

**How to run:** `java SubclassLockMismatch.java`.

Expected output:
```
Base.baseOperation holding baseLock
BuggySubclass.extensionHook holding a DIFFERENT lock (no reentrancy relationship to baseLock)
completed without contention -- but note: this was NOT true reentrancy,
just two independent locks that happened not to be contended concurrently
```

This adds the production-flavored hard case: reentrancy only protects re-entry into the **same lock object**. `BuggySubclass.extensionHook` acquires `subclassLock`, a completely different monitor from `baseLock` — this happens to run fine in the single-threaded demo above, but if another thread were concurrently holding `subclassLock` while this thread held `baseLock` and tried to enter `extensionHook`, it would simply block, waiting like any unrelated lock acquisition; there is no reentrancy relationship between the two different lock objects, regardless of which class "logically" owns the call chain.

## 6. Walkthrough

Tracing `SubclassLockMismatch.main` calling `obj.baseOperation()`:

1. `baseOperation()` enters `synchronized (baseLock)`, acquiring `baseLock`'s monitor for the current thread — hold count on `baseLock` becomes 1.
2. Still holding `baseLock`, it calls `extensionHook()`, which — thanks to overriding — dispatches to `BuggySubclass.extensionHook()`.
3. `BuggySubclass.extensionHook()` enters `synchronized (subclassLock)` — a completely unrelated `Object` instance from `baseLock`. This is a fresh lock acquisition, not a reentrant one; it happens to succeed instantly here only because no other thread currently holds `subclassLock`.
4. The nested block prints its message, then exits, releasing `subclassLock` (hold count back to 0 for that lock).
5. Control returns to `baseOperation()`, which exits its `synchronized (baseLock)` block, releasing `baseLock`.
6. `main` prints the two follow-up lines, making explicit that the apparent smoothness here was **not** intrinsic-lock reentrancy at work — it was simply two independent, uncontended locks. Had a second thread been holding `subclassLock` at the moment `extensionHook()` ran, step 3 would have blocked that thread, even though it already held `baseLock` — a genuine, easily-missed deadlock risk in class hierarchies that mix different lock objects across base and subclass.

## 7. Gotchas & takeaways

> **Gotcha:** reentrancy is a property of a specific **lock object**, not of "the current call stack" in general. A subclass method that locks on a *different* object than its superclass — even while called from inside a method that already holds the superclass's lock — gets no reentrancy benefit and can deadlock under contention, exactly like acquiring any two unrelated locks in an inconsistent order.

- Intrinsic locks (acquired via `synchronized`) are reentrant per-thread: the same thread can re-acquire a lock it already holds, tracked via an internal hold count.
- Reentrancy is what makes `synchronized` methods safely callable from other `synchronized` methods on the same object, including recursively.
- Reentrancy never extends across *different* lock objects — locking `this` in one method and a private field in another provides zero reentrant relationship between them, even if one call leads directly to the other.
- Be careful in class hierarchies: a subclass overriding a method that a superclass calls from within a `synchronized` block should either use the same lock object or think carefully about whether a different lock is intentional and deadlock-safe.
- Reentrancy applies equally to [`ReentrantLock`](0867-reentrantlock-fairness.md) (hence the name) — the same per-thread hold-count behavior, but as an explicit, non-implicit API.
