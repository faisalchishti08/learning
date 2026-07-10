---
card: java
gi: 863
slug: double-checked-locking
title: Double-checked locking
---

## 1. What it is

**Double-checked locking** is a pattern for lazily initializing a shared singleton with minimal synchronization overhead: check whether the instance already exists (no lock, fast path), and only if it doesn't, acquire a lock and check *again* (in case another thread just finished creating it) before creating it. It's called "double-checked" because the null-check happens both outside and inside the lock. Done correctly in modern Java, the field holding the instance **must** be declared `volatile` — without that, the pattern is famously broken, because a reading thread can observe a non-null reference to an object whose constructor hasn't finished running.

## 2. Why & when

The motivation is performance: once a singleton is created, every subsequent call to its accessor would otherwise pay the cost of acquiring a lock just to read a reference that never changes again. Double-checked locking lets the fast, common case (already initialized) skip the lock entirely, while still guaranteeing thread-safe, exactly-once initialization for the rare, slow case (first call). It matters for framework or library code and hot-path singletons that are read extremely frequently and must be lazily created — for example, a globally shared expensive-to-construct resource pool. Before reaching for it, seriously consider the eager-initialization alternative or the initialization-on-demand holder idiom — both are simpler and free of the classic pitfalls; double-checked locking is worth using specifically when initialization must stay lazy *and* the field's value may legitimately depend on runtime configuration not available at class-load time.

## 3. Core concept

```java
class Singleton {
    private static volatile Singleton instance; // MUST be volatile

    static Singleton getInstance() {
        Singleton local = instance;         // 1st (unsynchronized) check
        if (local == null) {
            synchronized (Singleton.class) {
                local = instance;           // 2nd check, now holding the lock
                if (local == null) {
                    instance = local = new Singleton();
                }
            }
        }
        return local;
    }
}
```

Without `volatile`, the JVM is allowed to make the write to `instance` visible to another thread *before* the constructor's writes to the new object's own fields are visible — so a second thread's first check could see a non-null `instance` that still points at a half-constructed object. `volatile` closes exactly that hole by ensuring the reference write happens only after full construction is visible.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads calling getInstance concurrently, first check unsynchronized, second check inside the lock, only one thread constructs the singleton">
  <rect x="20" y="20" width="280" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Thread A: 1st check -- instance == null</text>

  <rect x="340" y="20" width="280" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="480" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Thread B: 1st check -- instance == null</text>

  <rect x="20" y="80" width="280" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="105" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">A acquires lock, 2nd check null -&gt; creates</text>

  <rect x="340" y="80" width="280" height="40" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="480" y="105" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">B waits for lock...</text>

  <rect x="340" y="140" width="280" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="480" y="165" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">B acquires lock, 2nd check NOT null -&gt; reuses</text>

  <line x1="160" y1="60" x2="160" y2="78" stroke="#6db33f" stroke-width="2" marker-end="url(#a2)"/>
  <line x1="480" y1="60" x2="480" y2="78" stroke="#8b949e" stroke-width="2" marker-end="url(#a2)"/>
  <line x1="480" y1="120" x2="480" y2="138" stroke="#f0883e" stroke-width="2" marker-end="url(#a2)"/>

  <defs><marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Only the first thread to reach the second check actually constructs the singleton; every other thread's second check finds it already there and reuses it.*

## 5. Runnable example

Scenario: a lazily-initialized, expensive-to-construct `ConnectionPool` singleton, starting with a naive (unsafe) version, then the correct double-checked-locking version, then a version that also handles construction failure without permanently poisoning the singleton.

### Level 1 — Basic

```java
public class NaiveLazySingleton {
    static class ConnectionPool {
        ConnectionPool() {
            System.out.println("expensive construction running...");
        }
    }

    static ConnectionPool instance; // NOT volatile, NOT synchronized -- unsafe under concurrency

    static ConnectionPool getInstance() {
        if (instance == null) {
            instance = new ConnectionPool();
        }
        return instance;
    }

    public static void main(String[] args) {
        // single-threaded demonstration -- looks fine here, but is unsafe under concurrent access
        ConnectionPool p1 = getInstance();
        ConnectionPool p2 = getInstance();
        System.out.println("same instance? " + (p1 == p2));
    }
}
```

**How to run:** `java NaiveLazySingleton.java` (JDK 17+).

Expected output:
```
expensive construction running...
same instance? true
```

Single-threaded, this looks correct. The problem only appears under real concurrency: two threads could both see `instance == null` at the same time and both construct a `ConnectionPool`, or worse, one thread could see a non-null `instance` that still points at a half-constructed object.

### Level 2 — Intermediate

```java
public class DoubleCheckedLocking {
    static class ConnectionPool {
        final int size;
        ConnectionPool(int size) {
            this.size = size;
            System.out.println("constructing pool of size " + size + " on " + Thread.currentThread().getName());
        }
    }

    private static volatile ConnectionPool instance; // volatile -- required for correctness

    static ConnectionPool getInstance() {
        ConnectionPool local = instance;          // 1st check, no lock
        if (local == null) {
            synchronized (DoubleCheckedLocking.class) {
                local = instance;                 // 2nd check, holding the lock
                if (local == null) {
                    instance = local = new ConnectionPool(10);
                }
            }
        }
        return local;
    }

    public static void main(String[] args) throws InterruptedException {
        Runnable task = () -> {
            ConnectionPool p = getInstance();
            System.out.println(Thread.currentThread().getName() + " got pool with size " + p.size);
        };
        Thread t1 = new Thread(task, "t1");
        Thread t2 = new Thread(task, "t2");
        t1.start();
        t2.start();
        t1.join();
        t2.join();
    }
}
```

**How to run:** `java DoubleCheckedLocking.java`.

Expected output shape (construction happens exactly once, on whichever thread wins the race):
```
constructing pool of size 10 on t1
t1 got pool with size 10
t2 got pool with size 10
```

The real-world concern added: genuine multithreaded access, with the `volatile` field and the two-level check guaranteeing the constructor runs exactly once, no matter which thread happens to arrive first, and guaranteeing every thread sees a fully-constructed `ConnectionPool` — never a half-built one.

### Level 3 — Advanced

```java
public class DoubleCheckedLockingWithFailureHandling {
    static class ConnectionPool {
        final int size;
        ConnectionPool(int size) {
            if (size <= 0) throw new IllegalStateException("bad config: size=" + size);
            this.size = size;
        }
    }

    private static volatile ConnectionPool instance;
    private static volatile int configuredSize = -1; // simulate config that might be briefly invalid

    static ConnectionPool getInstance() {
        ConnectionPool local = instance;
        if (local == null) {
            synchronized (DoubleCheckedLockingWithFailureHandling.class) {
                local = instance;
                if (local == null) {
                    // if construction throws, `instance` stays null -- next caller gets a fresh attempt
                    // instead of being permanently poisoned by a partially-applied field
                    local = new ConnectionPool(configuredSize);
                    instance = local;
                }
            }
        }
        return local;
    }

    public static void main(String[] args) throws InterruptedException {
        Thread firstAttempt = new Thread(() -> {
            try {
                getInstance();
            } catch (IllegalStateException e) {
                System.out.println("first attempt failed as expected: " + e.getMessage());
            }
        });
        firstAttempt.start();
        firstAttempt.join();

        configuredSize = 20; // fix the config before retrying
        ConnectionPool p = getInstance();
        System.out.println("second attempt succeeded, size = " + p.size);
    }
}
```

**How to run:** `java DoubleCheckedLockingWithFailureHandling.java`.

Expected output:
```
first attempt failed as expected: bad config: size=-1
second attempt succeeded, size = 20
```

This adds the production-flavored hard case: what happens if construction *throws*. Because `instance` is only assigned **after** `new ConnectionPool(...)` returns successfully, a failed construction attempt leaves `instance` still `null` rather than poisoning the singleton with a partial or garbage value — the next call to `getInstance()` gets a clean retry, which is exactly the behavior you want when initialization can legitimately fail due to bad configuration.

## 6. Walkthrough

Tracing `DoubleCheckedLockingWithFailureHandling.main`:

1. `firstAttempt` thread calls `getInstance()`. The first check reads `instance` — it's `null`, so it enters the `synchronized` block.
2. Inside the lock, the second check re-reads `instance` — still `null` (no other thread has succeeded yet) — so it proceeds to construct: `new ConnectionPool(configuredSize)` with `configuredSize == -1`.
3. The constructor's `if (size <= 0) throw ...` fires immediately, before `this.size` is ever meaningfully used and before `instance = local` executes — so the exception propagates out of `getInstance()`, and critically, the static `instance` field remains `null`.
4. `main` catches the exception (propagated up through the thread, printed inside the lambda) and prints the failure message.
5. `main` fixes `configuredSize = 20`, then calls `getInstance()` itself. The first check again reads `instance == null` (the earlier failed attempt never assigned it), so it re-enters the lock, re-checks (still `null`), and this time constructs successfully with `size = 20`, assigning `instance = local`.
6. The final `println` confirms the second, corrected attempt succeeded and produced a pool of size 20 — and any future caller now finds `instance` non-null on the very first, lock-free check.

## 7. Gotchas & takeaways

> **Gotcha:** double-checked locking is **broken** without `volatile` on the instance field. Before Java 5 formalized the memory model fix, and in any code that forgets the keyword, a thread's first check can see a non-null reference to an object whose constructor hasn't finished writing all its fields yet — a classic, hard-to-reproduce heisenbug that only shows up under real concurrent load.

- The instance-holding field must be `volatile`; skipping it silently reintroduces the exact race the pattern exists to prevent.
- Double-checked locking's whole point is to make the **already-initialized** read path lock-free — the `synchronized` block is only ever entered on the first few racing calls.
- If construction can fail, only assign the field after construction succeeds, so a failed attempt doesn't permanently poison the singleton with a partial value.
- For the common case of a singleton with no runtime-dependent construction, the simpler and equally lazy **initialization-on-demand holder idiom** (a nested static class, initialized by the JVM's own class-loading guarantees) sidesteps double-checked locking entirely and is usually preferable.
- Reach for [`AtomicReference`](0858-volatile-semantics.md)'s `compareAndSet`, or a `java.util.concurrent` primitive, when the initialization logic is more complex than a simple assignment.
