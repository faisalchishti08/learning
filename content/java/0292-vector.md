---
card: java
gi: 292
slug: vector
title: Vector
---

## 1. What it is

`Vector` is a legacy, resizable array implementation of `List`, present since Java 1.0 — before the modern Collections Framework existed. It behaves much like `ArrayList`, but every one of its methods is `synchronized`, meaning it is safe to share across multiple threads without external locking, at the cost of that locking overhead on every call, even in single-threaded code.

```java
import java.util.Vector;

public class VectorDemo {
    public static void main(String[] args) {
        Vector<String> names = new Vector<>();
        names.add("Alice");
        names.add("Bob");
        names.addElement("Carol"); // legacy Vector-specific method, same as add

        System.out.println(names);
        System.out.println(names.get(1));
    }
}
```

`add`/`get` are the modern `List` methods `Vector` also supports; `addElement` is Vector's original, pre-Collections-Framework method — both do the same thing, a reminder that `Vector` predates `List` and was retrofitted to implement it.

## 2. Why & when

`Vector` was Java's original growable array, written before generics, before the Collections Framework, and before Java had a clear story about thread safety in collections. Every method being synchronized was Java's earliest (and now considered heavy-handed) answer to "how do multiple threads share a list safely."

- **Historical thread safety** — synchronizing every method meant a `Vector` could be handed to multiple threads without the caller needing to add their own locking.
- **Legacy API compatibility** — some very old APIs (and `Stack`, which extends `Vector`) still expose `Vector` in their signatures.
- **Retrofitted into List** — when the Collections Framework arrived in Java 1.2, `Vector` was retrofitted to implement `List` so it could interoperate with newer code, but it kept its old synchronized methods and Vector-specific method names (`addElement`, `elementAt`, `firstElement`) for backward compatibility.

For new code, prefer `ArrayList` (unsynchronized, faster for single-threaded use — which is the overwhelming majority of cases) combined with `Collections.synchronizedList` or a proper concurrent collection like `CopyOnWriteArrayList` when true thread safety is required. Per-method synchronization on `Vector` does **not** make compound operations (like "check size, then add") atomic anyway, so it rarely solves real concurrency problems on its own.

## 3. Core concept

```java
import java.util.Vector;

public class VectorCore {
    public static void main(String[] args) {
        Vector<Integer> numbers = new Vector<>(2); // initial capacity hint
        for (int i = 1; i <= 5; i++) {
            numbers.add(i);
        }
        System.out.println("Size: " + numbers.size());
        System.out.println("Capacity grows automatically as needed: " + numbers);
    }
}
```

`new Vector<>(2)` only hints at initial internal array size (a performance detail, avoiding early resizes) — it does **not** limit how many elements can be added; `Vector` grows its backing array automatically, exactly like `ArrayList`, whenever it runs out of room.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Vector and ArrayList have the same backing array structure, but every Vector method is wrapped in a lock">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="250" height="90" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="52" fill="#f85149" font-size="12" text-anchor="middle" font-family="monospace">Vector</text>
  <text x="155" y="72" fill="#8b949e" font-size="9" text-anchor="middle">every method: synchronized</text>
  <text x="155" y="90" fill="#8b949e" font-size="9" text-anchor="middle">lock overhead even single-threaded</text>

  <rect x="320" y="30" width="250" height="90" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="445" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">ArrayList</text>
  <text x="445" y="72" fill="#8b949e" font-size="9" text-anchor="middle">no synchronization</text>
  <text x="445" y="90" fill="#8b949e" font-size="9" text-anchor="middle">faster; wrap externally if needed</text>
</svg>

Same resizable-array idea; `Vector` pays a locking tax on every call whether or not you need thread safety.

## 5. Runnable example

Scenario: a shared list of connected client names, evolved from a single-threaded `Vector` usage into a multi-threaded scenario that shows what `Vector`'s per-method synchronization does and does not protect against.

### Level 1 — Basic

```java
import java.util.Vector;

public class VectorBasic {
    public static void main(String[] args) {
        Vector<String> clients = new Vector<>();
        clients.add("client-1");
        clients.add("client-2");
        clients.add("client-3");

        for (String client : clients) {
            System.out.println("Connected: " + client);
        }
    }
}
```

**How to run:** `java VectorBasic.java`

Single-threaded usage — `Vector` behaves exactly like `ArrayList` here, just with unused synchronization overhead on every call.

### Level 2 — Intermediate

Same client list, now shared safely across two threads that each add entries concurrently, demonstrating that individual `add` calls are safe without external locks.

```java
import java.util.Vector;

public class VectorIntermediate {
    public static void main(String[] args) throws InterruptedException {
        Vector<String> clients = new Vector<>();

        Runnable addA = () -> {
            for (int i = 1; i <= 500; i++) clients.add("A-" + i);
        };
        Runnable addB = () -> {
            for (int i = 1; i <= 500; i++) clients.add("B-" + i);
        };

        Thread t1 = new Thread(addA);
        Thread t2 = new Thread(addB);
        t1.start();
        t2.start();
        t1.join();
        t2.join();

        System.out.println("Total clients: " + clients.size()); // reliably 1000, no lost updates
    }
}
```

**How to run:** `java VectorIntermediate.java`

Two threads call `add` 500 times each concurrently; because each individual `add` is synchronized, no update is ever lost — the final size is reliably `1000` every run, which would **not** be guaranteed with a plain (unsynchronized) `ArrayList` under the same concurrent access.

### Level 3 — Advanced

Same shared client list, now demonstrating the classic gotcha: per-method synchronization does **not** make a *compound* operation (check-then-act) atomic, so a race condition still exists across multiple calls, fixed here by synchronizing on the `Vector` itself for the compound operation.

```java
import java.util.Vector;

public class VectorAdvanced {
    static void addIfAbsent(Vector<String> clients, String name) {
        // BUG if unsynchronized: two threads can both pass contains() before either adds,
        // producing a duplicate -- contains() + add() together are NOT atomic even though
        // each individually is thread-safe.
        synchronized (clients) {
            if (!clients.contains(name)) {
                clients.add(name);
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Vector<String> clients = new Vector<>();

        Runnable attempt = () -> addIfAbsent(clients, "client-shared");

        Thread[] threads = new Thread[20];
        for (int i = 0; i < threads.length; i++) {
            threads[i] = new Thread(attempt);
            threads[i].start();
        }
        for (Thread t : threads) t.join();

        long count = clients.stream().filter(c -> c.equals("client-shared")).count();
        System.out.println("Occurrences of client-shared: " + count); // always exactly 1
    }
}
```

**How to run:** `java VectorAdvanced.java`

Twenty threads race to add the same name; without the explicit `synchronized (clients)` block wrapping *both* the `contains` check and the `add`, two threads could each see `contains` return `false` before either has added the entry, producing duplicates — `Vector`'s own per-method synchronization only protects each individual call, not the sequence of two calls together.

## 6. Walkthrough

Trace `VectorAdvanced.main` step by step.

**Setup.** An empty `Vector<String> clients` and a `Runnable attempt` that calls `addIfAbsent(clients, "client-shared")` are defined. Twenty `Thread` objects are created, each running `attempt`, and all twenty are started in a tight loop — so, in practice, many of them attempt to run `addIfAbsent` at nearly the same instant.

**Inside `addIfAbsent` (any one thread).** The thread enters `synchronized (clients)` — this acquires the intrinsic lock on the `clients` object itself. If another thread is already inside this same block, this thread blocks here until that lock is released. Only one thread at a time can be inside the block for this particular `clients` instance.

**Once the lock is held.** `clients.contains(name)` checks whether `"client-shared"` is already present — the first thread to get the lock sees `false` (nothing has been added yet), so it proceeds to `clients.add(name)`, inserting the one and only copy. The lock is released as the thread exits the `synchronized` block.

**Every subsequent thread.** Each of the remaining nineteen threads, in turn, acquires the same lock (one at a time, serialized), calls `contains`, and this time sees `true` — the entry is already there — so `add` is skipped. No duplicates are ever created, because the check-then-act pair is now atomic with respect to every other thread trying the same pair.

**Without the `synchronized` block** (a hypothetical, not what this code does): two threads could both call `contains` and both see `false` *before* either had called `add` — each proceeding independently — resulting in `"client-shared"` being added twice. This is exactly the bug the explicit lock prevents.

**Final count.** `clients.stream().filter(...).count()` scans the final list and counts exactly one occurrence of `"client-shared"`, confirming the compound check-then-add was correctly serialized across all twenty threads.

```
20 threads, each running: synchronized(clients) { if (!contains) add }

Thread 1:  lock acquired -> contains=false -> add -> unlock
Thread 2:  lock acquired -> contains=true  -> skip -> unlock
...
Thread 20: lock acquired -> contains=true  -> skip -> unlock

Result: clients contains "client-shared" exactly once.
```

**Output:**
```
Occurrences of client-shared: 1
```

## 7. Gotchas & takeaways

> `Vector`'s built-in synchronization protects **individual method calls**, not sequences of calls. A "check-then-act" pattern like `if (!vector.contains(x)) vector.add(x)` is **not** atomic just because `contains` and `add` are each individually synchronized — a race condition can still occur between the two calls, exactly as demonstrated above. You must add your own explicit `synchronized` block (or use a proper concurrent collection) to make compound operations atomic.

> Iterating a `Vector` with a `for-each` loop while another thread modifies it will still throw `ConcurrentModificationException`, exactly as with `ArrayList` — per-method synchronization does not make the iterator itself safe against concurrent structural changes.

- `Vector` is a legacy, synchronized, resizable-array `List` implementation, functionally similar to `ArrayList` but with locking on every method.
- Prefer `ArrayList` for single-threaded use (the common case) — it is faster with no downside when thread safety isn't needed.
- For genuine concurrent use, prefer `Collections.synchronizedList(new ArrayList<>())` (explicit intent) or `CopyOnWriteArrayList` over `Vector`.
- Per-method synchronization does not make multi-call sequences atomic — wrap compound check-then-act operations in your own `synchronized` block.
