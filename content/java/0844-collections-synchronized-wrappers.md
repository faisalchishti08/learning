---
card: java
gi: 844
slug: collections-synchronized-wrappers
title: Collections.synchronized* wrappers
---

## 1. What it is

`Collections.synchronizedList(list)`, `synchronizedSet(set)`, `synchronizedMap(map)`, and their siblings wrap an existing, ordinary (non-thread-safe) collection with a version where every individual method call is synchronized on a single internal lock (by default, the wrapper object itself). This gives the wrapped collection the same basic thread-safety guarantee [`Vector`](0814-vector-legacy-synchronized.md)/[`Hashtable`](0826-hashtable-legacy.md) provide — no single method call can corrupt the collection's internal structure under concurrent access — while letting you start from any `List`/`Set`/`Map` implementation, not just those two legacy classes specifically.

## 2. Why & when

Before [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md) and [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md) existed, `Collections.synchronizedX(...)` was the standard way to make an arbitrary collection thread-safe for basic operations. It still has a legitimate, narrow use today: wrapping a collection that must genuinely support both reads and writes under concurrent access, where the read/write ratio doesn't favor `CopyOnWriteArrayList`'s copy-on-write tradeoff, and where sorted iteration order (favoring `ConcurrentSkipListMap`) isn't needed. The critical thing to understand — repeating the exact same lesson from `Vector` and `Hashtable` — is that per-method synchronization only protects *individual* calls; both compound operations (check-then-act) and, critically, **iteration** require the caller to take out an explicit lock on the wrapper for the entire duration, something the wrapper's own internal synchronization cannot provide automatically.

## 3. Core concept

```java
List<String> syncList = Collections.synchronizedList(new ArrayList<>());
syncList.add("a"); // this individual call is synchronized internally -- safe

// Iteration REQUIRES manual external synchronization on the SAME lock the wrapper uses --
// the documentation for Collections.synchronizedList explicitly requires this pattern:
synchronized (syncList) {
    for (String item : syncList) { // safe ONLY because of the enclosing synchronized block
        System.out.println(item);
    }
}
// Without the synchronized(syncList) block, a concurrent structural modification during
// this iteration can still throw ConcurrentModificationException, exactly as with a plain ArrayList.
```

The wrapper synchronizes on itself (`syncList`), so any external code that also needs exclusive access — like the iteration loop above — must synchronize on that exact same object to actually be mutually exclusive with the wrapper's own internal locking.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Individual method calls on a synchronized wrapper are automatically protected, but iterating the wrapper requires the caller to manually synchronize on the wrapper object for the whole loop">
  <rect x="40" y="30" width="260" height="55" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="170" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">syncList.add(x)</text>
  <text x="170" y="72" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">automatically synchronized</text>

  <rect x="340" y="30" width="260" height="55" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="470" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">for (x : syncList) { ... }</text>
  <text x="470" y="72" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">needs an EXTERNAL synchronized block</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Iteration is multiple internal calls (hasNext/next) -- only an external lock makes the WHOLE loop atomic</text>
</svg>

*A single method call is automatically safe; a whole iteration loop is many calls, and needs the caller's own `synchronized` block.*

## 5. Runnable example

Scenario: a shared audit-log list accessed by multiple threads, growing from basic thread-safe individual operations, through the iteration pitfall a synchronized wrapper doesn't automatically solve, to the correct externally-synchronized iteration pattern.

### Level 1 — Basic

```java
import java.util.*;
import java.util.concurrent.*;

public class AuditLogBasic {
    public static void main(String[] args) throws InterruptedException {
        List<String> auditLog = Collections.synchronizedList(new ArrayList<>());

        ExecutorService pool = Executors.newFixedThreadPool(4);
        for (int i = 0; i < 4; i++) {
            final int id = i;
            pool.submit(() -> auditLog.add("entry-from-thread-" + id));
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        System.out.println("total entries: " + auditLog.size());
        System.out.println("entries: " + auditLog);
    }
}
```

**How to run:** `java AuditLogBasic.java` (JDK 17+). Exact entry order can vary by thread scheduling, but the count is always exactly 4 and no exception ever occurs.

Expected output shape:
```
total entries: 4
entries: [entry-from-thread-2, entry-from-thread-0, entry-from-thread-1, entry-from-thread-3]
```

Individual `add` calls from four different threads are each internally synchronized, so all four succeed correctly without corrupting the list's internal structure — the basic guarantee works exactly as intended.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.concurrent.*;

public class AuditLogIterationPitfall {
    public static void main(String[] args) throws InterruptedException {
        List<String> auditLog = Collections.synchronizedList(new ArrayList<>());
        for (int i = 0; i < 100; i++) {
            auditLog.add("entry-" + i);
        }

        ExecutorService pool = Executors.newFixedThreadPool(2);

        // Thread A: iterates the list WITHOUT an external synchronized block -- the gotcha.
        Future<?> iterationTask = pool.submit(() -> {
            try {
                int count = 0;
                for (String entry : auditLog) { // NOT protected by a synchronized(auditLog) block
                    count++;
                    Thread.sleep(1); // simulate slow processing, widening the race window
                }
                System.out.println("iteration completed, count: " + count);
            } catch (ConcurrentModificationException e) {
                System.out.println("caught: ConcurrentModificationException during unprotected iteration");
            } catch (InterruptedException ignored) {}
        });

        // Thread B: concurrently mutates the SAME list while Thread A is iterating it.
        pool.submit(() -> {
            for (int i = 0; i < 20; i++) {
                auditLog.add("concurrent-entry-" + i);
            }
        });

        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);
        iterationTask.get();
    }
}
```

**How to run:** `java AuditLogIterationPitfall.java`. Results are timing-dependent — `ConcurrentModificationException` is likely (though not strictly guaranteed on every single run) given the artificial delay widening the race window.

Expected output shape:
```
caught: ConcurrentModificationException during unprotected iteration
```

The real-world concern added: proving that `Collections.synchronizedList` alone does **not** protect an in-progress iteration from a concurrent structural modification happening on another thread — the wrapper's internal per-call synchronization has nothing to do with the fail-fast [iterator mechanism](0847-fail-fast-iterators-concurrentmodificationexception.md) that a plain for-each loop still uses underneath, and that mechanism still detects and reports the concurrent modification exactly as it would for an unwrapped `ArrayList`.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class AuditLogCorrectIteration {
    public static void main(String[] args) throws InterruptedException {
        List<String> auditLog = Collections.synchronizedList(new ArrayList<>());
        for (int i = 0; i < 100; i++) {
            auditLog.add("entry-" + i);
        }

        ExecutorService pool = Executors.newFixedThreadPool(2);

        Future<?> iterationTask = pool.submit(() -> {
            int count;
            // The documented, correct pattern: synchronize on the SAME object the wrapper
            // itself synchronizes on, for the ENTIRE duration of the iteration.
            synchronized (auditLog) {
                count = 0;
                for (String entry : auditLog) {
                    count++;
                }
            }
            System.out.println("iteration completed safely, count: " + count);
        });

        pool.submit(() -> {
            for (int i = 0; i < 20; i++) {
                auditLog.add("concurrent-entry-" + i);
            }
        });

        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);
        iterationTask.get();

        System.out.println("final total size: " + auditLog.size());
    }
}
```

**How to run:** `java AuditLogCorrectIteration.java`. Deterministic — always completes without exception.

Expected output shape:
```
iteration completed safely, count: 100
final total size: 120
```

This adds the production-flavored hard case: wrapping the entire iteration in `synchronized (auditLog) { ... }`, acquiring the exact same lock object `Collections.synchronizedList` uses internally for its own per-method synchronization. This makes the whole loop mutually exclusive with any other thread's `add`/`remove`/other calls on `auditLog` — the concurrent writer thread's `add` calls simply block until the iterating thread releases the lock (by exiting the `synchronized` block), guaranteeing the iteration always sees a consistent 100-element view, with the writer's 20 additional entries only becoming visible afterward.

## 6. Walkthrough

Tracing `AuditLogCorrectIteration.main`:

1. `auditLog` is a `Collections.synchronizedList`-wrapped `ArrayList`, pre-populated with 100 entries.
2. Two tasks are submitted: one iterates `auditLog` inside a `synchronized (auditLog) { ... }` block; the other calls `auditLog.add(...)` twenty times in a loop, with no explicit synchronization of its own (relying only on the wrapper's automatic per-call locking).
3. Whichever task's thread acquires the `auditLog` object's intrinsic lock first proceeds; if it's the iteration task, the entire `for` loop over `auditLog` runs to completion — reading `hasNext()`/`next()` repeatedly — all while holding the lock, so the writer thread's `add` calls (which also need to acquire that same lock internally, per `Collections.synchronizedList`'s own implementation) simply block and wait.
4. Once the iteration's `synchronized` block exits, releasing the lock, the writer thread's twenty queued `add` calls proceed normally, no longer contending with anything.
5. The iteration task reports `count: 100` — the exact size the list had when iteration began, with no concurrent modification able to interfere, since the lock excluded the writer for the iteration's entire duration. The final `auditLog.size()`, checked after both tasks have fully completed, correctly reports `120` (100 original plus 20 concurrently added), confirming both threads' work succeeded correctly and in a well-defined order relative to each other.

## 7. Gotchas & takeaways

> **Gotcha:** `Collections.synchronizedList`/`Set`/`Map`'s own Javadoc explicitly documents the requirement to manually synchronize on the wrapper object during iteration — it is not an implementation detail or edge case, but a documented, expected part of using these wrappers correctly. Skipping the external `synchronized` block during iteration is a common, easy-to-miss bug that only manifests under actual concurrent load, often passing unnoticed in single-threaded testing.

- `Collections.synchronizedList/Set/Map(...)` synchronizes every individual method call on the returned wrapper, giving basic per-call thread safety to any underlying collection.
- Iteration (a for-each loop, or any use of `iterator()`) is **not** automatically protected — it must be wrapped in an explicit `synchronized (wrapperObject) { ... }` block covering the entire loop, exactly as documented by the JDK.
- This mirrors the exact same lesson from [`Vector`](0814-vector-legacy-synchronized.md)/[`Hashtable`](0826-hashtable-legacy.md): per-method synchronization never makes multi-call sequences (including iteration) atomic on its own.
- For modern code, [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md) (with its weakly consistent, exception-free iterators) or [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md) (with its snapshot iterators) often provide better iteration ergonomics than a `synchronized` wrapper, at the cost of different tradeoffs each makes elsewhere.
- Choose `Collections.synchronizedX(...)` specifically when wrapping an arbitrary existing collection type for basic thread safety is the simplest fit, and when the code correctly follows the external-synchronization-during-iteration requirement throughout.
