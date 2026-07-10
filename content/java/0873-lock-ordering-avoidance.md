---
card: java
gi: 873
slug: lock-ordering-avoidance
title: Lock ordering & avoidance
---

## 1. What it is

**Lock ordering** is the discipline of always acquiring multiple locks in the same, globally consistent order across every thread and every code path in the system — for example, always locking the object with the smaller ID before the one with the larger ID, regardless of which one a particular operation logically thinks of as "first." This directly eliminates the **circular wait** condition that [deadlock](0871-deadlock-causes-prevention.md) requires: if every thread agrees on the same total order for acquiring any set of locks, no cycle of "I hold X and wait for Y" / "I hold Y and wait for X" can ever form, because both threads would have acquired X before Y (or vice versa) in the same relative order.

## 2. Why & when

Any operation that touches two or more independently-locked objects at once is a deadlock candidate the moment the *order* in which those objects get locked can vary between calls — a transfer between account A and account B locks them in one order; a transfer in the opposite direction, called concurrently, might lock them in the reverse order, and that mismatch is exactly what creates a cycle. Establishing and enforcing a consistent lock order is the cheapest, most structural fix: it requires no retries, no timeouts, and no runtime detection — the deadlock simply becomes impossible by construction. Use it whenever locks are acquired based on data that varies by call (which object is "from" vs. "to", which node is the caller vs. callee) rather than a fixed, hardcoded relationship; derive the order from something intrinsic to the objects themselves (a unique ID, `System.identityHashCode()`, insertion order) rather than from argument position, method name, or any other property that could differ between two logically symmetric calls.

## 3. Core concept

```java
// Sort by intrinsic identity, not by argument order, before locking:
void safeOperation(Resource r1, Resource r2) {
    Resource first = System.identityHashCode(r1) < System.identityHashCode(r2) ? r1 : r2;
    Resource second = (first == r1) ? r2 : r1;
    synchronized (first) {
        synchronized (second) {
            // both locks held, in a globally consistent order -- no circular wait possible
        }
    }
}
```

Every call to `safeOperation`, no matter which resource is passed as `r1` versus `r2`, ends up locking the same physical pair of objects in the same relative order — so two concurrent, opposite-direction calls can never form a cycle.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads calling the same operation with arguments swapped both end up locking resource with lower identity first, so no circular wait can form">
  <rect x="20" y="20" width="260" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="43" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Thread 1: op(r1, r2) -&gt; locks LOWER id first</text>

  <rect x="340" y="20" width="260" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="470" y="43" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Thread 2: op(r2, r1) -&gt; ALSO locks LOWER id first</text>

  <rect x="180" y="90" width="280" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="113" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Same global order -- worst case: one waits briefly</text>

  <line x1="150" y1="55" x2="290" y2="88" stroke="#8b949e" stroke-width="2" marker-end="url(#a11)"/>
  <line x1="470" y1="55" x2="360" y2="88" stroke="#8b949e" stroke-width="2" marker-end="url(#a11)"/>
  <text x="320" y="150" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">No cycle possible: circular wait is structurally eliminated.</text>

  <defs><marker id="a11" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Regardless of argument order, both calls resolve to the same lock-acquisition order — a wait, never a cycle.*

## 5. Runnable example

Scenario: a graph of accounts that can transfer to each other in arbitrary pairs and directions, growing from the naive argument-order locking (deadlock-prone), to `identityHashCode`-based ordering (correct but needs a tie-break), to a fully general N-object locking helper that safely locks an arbitrary list of resources in one consistent global order.

### Level 1 — Basic

```java
public class ArgumentOrderLocking {
    static class Account {
        int balance = 1000;
    }

    // DEADLOCK-PRONE: lock order follows argument order, which can differ between calls
    static void transfer(Account from, Account to, int amount) {
        synchronized (from) {
            synchronized (to) {
                from.balance -= amount;
                to.balance += amount;
            }
        }
    }

    public static void main(String[] args) {
        Account a = new Account();
        Account b = new Account();
        // single-threaded: looks completely fine
        transfer(a, b, 100);
        transfer(b, a, 30);
        System.out.println("a=" + a.balance + ", b=" + b.balance);
        System.out.println("(this exact code deadlocks under real concurrent, opposite-direction calls)");
    }
}
```

**How to run:** `java ArgumentOrderLocking.java` (JDK 17+).

Expected output:
```
a=930, b=1070
(this exact code deadlocks under real concurrent, opposite-direction calls)
```

Single-threaded, nothing goes wrong. The danger is latent: `transfer(a, b, ...)` locks `a` then `b`; `transfer(b, a, ...)` locks `b` then `a` — the exact circular-wait setup, waiting to happen under real concurrency.

### Level 2 — Intermediate

```java
public class IdentityHashOrdering {
    static class Account {
        int balance = 1000;
    }

    static void transfer(Account from, Account to, int amount) {
        int h1 = System.identityHashCode(from);
        int h2 = System.identityHashCode(to);
        Account first, second;
        if (h1 < h2) { first = from; second = to; }
        else if (h1 > h2) { first = to; second = from; }
        else { // rare hash collision -- fall back to a stable tie-break so order is STILL consistent
            first = (from.hashCode() <= to.hashCode()) ? from : to; // any deterministic, symmetric rule works
            second = (first == from) ? to : from;
        }
        synchronized (first) {
            synchronized (second) {
                from.balance -= amount;
                to.balance += amount;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Account a = new Account();
        Account b = new Account();

        Thread t1 = new Thread(() -> { for (int i = 0; i < 1000; i++) transfer(a, b, 1); });
        Thread t2 = new Thread(() -> { for (int i = 0; i < 1000; i++) transfer(b, a, 1); });
        t1.start(); t2.start();
        t1.join(); t2.join();

        System.out.println("a=" + a.balance + ", b=" + b.balance + " (no deadlock, totals balance out)");
    }
}
```

**How to run:** `java IdentityHashOrdering.java`.

Expected output:
```
a=1000, b=1000 (no deadlock, totals balance out)
```

The real-world concern added: genuine concurrent, opposite-direction transfers (1000 each way) racing against each other, now safely ordered by `identityHashCode` rather than argument position — since both threads agree on the same physical lock order regardless of transfer direction, no cycle forms, and after equal numbers of transfers in both directions, both balances return to their starting point.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class GeneralNWayLockOrdering {
    static class Account {
        final String label;
        int balance = 1000;
        Account(String label) { this.label = label; }
    }

    // Locks an ARBITRARY list of accounts, always in the same global order (by identityHashCode,
    // with a stable tie-break), regardless of the order the caller happened to list them in.
    static void withAllLocked(List<Account> accounts, Runnable action) {
        List<Account> ordered = new ArrayList<>(accounts);
        ordered.sort(Comparator
            .comparingInt(System::identityHashCode)
            .thenComparing(acc -> acc.label)); // tie-break for identityHashCode collisions

        acquireInOrder(ordered, 0, action);
    }

    private static void acquireInOrder(List<Account> ordered, int index, Runnable action) {
        if (index == ordered.size()) {
            action.run(); // all locks held -- run the critical section
            return;
        }
        synchronized (ordered.get(index)) {
            acquireInOrder(ordered, index + 1, action); // recurse, locking the NEXT account in the fixed order
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Account a = new Account("A"), b = new Account("B"), c = new Account("C");
        ExecutorService pool = Executors.newFixedThreadPool(3);

        // Three different three-way "rotations" of money, each locking all 3 accounts,
        // submitted in different argument orders -- withAllLocked normalizes the order internally.
        pool.submit(() -> withAllLocked(List.of(a, b, c), () -> { a.balance -= 10; b.balance += 10; }));
        pool.submit(() -> withAllLocked(List.of(c, a, b), () -> { b.balance -= 10; c.balance += 10; }));
        pool.submit(() -> withAllLocked(List.of(b, c, a), () -> { c.balance -= 10; a.balance += 10; }));

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        int total = a.balance + b.balance + c.balance;
        System.out.println("a=" + a.balance + ", b=" + b.balance + ", c=" + c.balance);
        System.out.println("total=" + total + " (must remain 3000, no deadlock across 3 accounts)");
    }
}
```

**How to run:** `java GeneralNWayLockOrdering.java`.

Expected output shape (each individual balance's exact final value depends on scheduling order among the three concurrent operations, but the total is always exact):
```
a=1000, b=1000, c=1000
total=3000 (must remain 3000, no deadlock across 3 accounts)
```

This adds the production-flavored hard case: generalizing lock ordering beyond just two objects to an **arbitrary list** of resources, each call site passing them in whatever order is convenient for its own logic (`List.of(a,b,c)`, `List.of(c,a,b)`, `List.of(b,c,a)`) — `withAllLocked` internally sorts every such list into the same canonical global order before acquiring any locks, so no matter how many resources are involved or in what order callers list them, a consistent acquisition order across all three concurrent three-way operations rules out any possible cycle.

## 6. Walkthrough

Tracing `GeneralNWayLockOrdering.main`:

1. Three tasks are submitted, each calling `withAllLocked` with the same three `Account` objects but in different list orders (`[a,b,c]`, `[c,a,b]`, `[b,c,a]`).
2. Each call to `withAllLocked` first copies its input list and sorts it by `System.identityHashCode`, with a secondary sort by `label` as a tie-break for the rare case two objects hash identically — since `identityHashCode` and `label` are properties of the objects themselves, not of how the caller happened to list them, all three calls produce the **same** sorted order, say `[a, b, c]` (whatever the actual identity hashes dictate).
3. `acquireInOrder` is then called recursively: it synchronizes on `ordered.get(0)`, then recurses to synchronize on `ordered.get(1)` while still holding the first lock, and so on, until all three locks are held, at which point the base case runs the caller's `action`.
4. Because all three concurrently-running tasks agree on the exact same acquisition order (`a` before `b` before `c`), whichever task's thread reaches `synchronized (a)` first proceeds to acquire `b` and then `c` without any other task being able to hold `b` or `c` while waiting on `a` — the structural precondition for a cycle (some task holding a "later" lock while waiting on an "earlier" one) never arises.
5. Each task's `action` runs while holding all three locks, safely mutating exactly the two account balances it touches; the locks are released in reverse order as each recursive call returns.
6. After all three tasks complete, the total across `a`, `b`, and `c` is unchanged at 3000, since every operation both debits and credits exactly 10 between two of the three accounts, and no deadlock ever had a chance to occur, despite three different, independently-authored call sites each listing the three accounts in a different order.

## 7. Gotchas & takeaways

> **Gotcha:** `System.identityHashCode()` is not guaranteed unique — two different objects can (rarely) produce the same value. Any ordering scheme built on it needs a deterministic, symmetric tie-break (like a unique ID or, failing that, a secondary stable property) so that even in a collision, every thread still agrees on the same resulting order.

- Consistent lock ordering eliminates deadlock's circular-wait condition structurally — no retries, timeouts, or runtime detection needed, just discipline applied uniformly across every code path that acquires more than one lock.
- Derive the lock order from something intrinsic to the objects (a unique ID, `identityHashCode` with a tie-break, natural ordering) — never from call-site argument order, which can and will differ between logically symmetric operations.
- The pattern generalizes cleanly from two locks to an arbitrary N locks: sort the full set of resources into one canonical order before acquiring any of them, as `withAllLocked` demonstrates.
- Lock ordering only prevents *circular wait* — it does nothing about [livelock or starvation](0872-livelock-starvation.md), which come from different underlying causes (symmetric retry logic, unfair scheduling) and need their own fixes (jittered backoff, fair locks).
- When a consistent order genuinely can't be established (e.g., locks acquired dynamically from unrelated subsystems with no natural relationship), fall back to `tryLock` with a timeout and a release-and-retry loop, trading a structural guarantee for a bounded, recoverable one.
