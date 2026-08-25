# Java Concurrent Collections

## Overview

The `java.util.concurrent` package provides thread-safe collections designed for high-concurrency scenarios. Unlike synchronized wrappers (`Collections.synchronizedMap`), these use lock striping, CAS operations, and copy-on-write to minimize contention.

---

## 1. ConcurrentHashMap

### What is it

Thread-safe `HashMap` replacement. Uses **lock striping** (segment-level locking in Java 7, CAS + bin-level synchronized in Java 8+). Multiple threads can read and write simultaneously as long as they target different bins.

### Visual Diagram — Java 8+ Internal Structure

```
ConcurrentHashMap (Java 8+):
  Internal array of "bins" (like HashMap)
  
  bin[0]: [A=1] → null
  bin[1]: [B=2] → [E=5] → null   ← linked list (turns to tree at 8+ entries)
  bin[2]: null
  bin[3]: [C=3] → null
  bin[4]: [D=4] → null
  
  Write to bin[1]: synchronized on bin[1]'s head node only
  Write to bin[3]: synchronized on bin[3]'s head node only
  ↑ Both writes can happen concurrently — different bins!
  
  Read: CAS (compare-and-swap), usually NO lock needed
  
  vs. Hashtable / synchronizedMap: lock on THE WHOLE MAP for every operation
```

### Example 1 — Basic Usage and Atomic Operations

```java
import java.util.concurrent.*;
import java.util.*;

public class ConcurrentHashMapDemo {
    public static void main(String[] args) throws Exception {
        ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();

        // putIfAbsent — atomic: only puts if key not present
        map.putIfAbsent("a", 1);
        map.putIfAbsent("a", 99); // does nothing — "a" already exists
        System.out.println(map.get("a")); // 1

        // computeIfAbsent — compute value if key missing
        map.computeIfAbsent("b", k -> k.length()); // b → 1
        System.out.println(map.get("b")); // 1

        // compute — always recompute (null removes)
        map.compute("a", (k, v) -> v == null ? 1 : v + 10);
        System.out.println(map.get("a")); // 11

        // merge — combine existing with new value
        map.merge("a", 5, Integer::sum); // 11 + 5 = 16
        System.out.println(map.get("a")); // 16

        // Parallel counting example
        ConcurrentHashMap<String, Integer> freq = new ConcurrentHashMap<>();
        List<String> words = List.of("apple", "banana", "apple", "cherry", "banana", "apple");

        words.forEach(word ->
            freq.merge(word, 1, Integer::sum) // thread-safe word count
        );
        System.out.println(freq); // {apple=3, banana=2, cherry=1}
    }
}
```

**What this does:** `putIfAbsent`, `computeIfAbsent`, `compute`, `merge` are all atomic operations — no external synchronization needed. `merge` is the idiomatic word-count pattern.

### Example 2 — forEach, reduce, search (Bulk Operations)

```java
import java.util.concurrent.*;

public class CHMBulkOps {
    public static void main(String[] args) {
        ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();
        map.put("a", 1); map.put("b", 2); map.put("c", 3); map.put("d", 4);

        // forEach with parallelism threshold
        // threshold=1: use parallelism aggressively
        // threshold=Long.MAX_VALUE: sequential
        map.forEach(2, (k, v) -> System.out.println(k + "=" + v));

        // reduce — parallel reduction
        int sum = map.reduce(1, (k, v) -> v, Integer::sum);
        System.out.println("Sum: " + sum); // 10

        // search — find first matching entry (parallel)
        String found = map.search(1, (k, v) -> v > 2 ? k : null);
        System.out.println("First > 2: " + found); // c or d (order not guaranteed)

        // mappingCount() — long, safer than size() for huge maps
        System.out.println("Count: " + map.mappingCount()); // 4
    }
}
```

**What this does:** Bulk operations parallelize work across entries using the parallelism threshold. `mappingCount()` returns a `long` — prefer over `size()` for maps with >Integer.MAX_VALUE entries.

### Dry Run — compute for Word Frequency (Thread-Safe)

```
freq.merge("apple", 1, Integer::sum)  called by 3 threads concurrently:

Thread 1: merge("apple", 1, sum) → no entry → put("apple", 1) [atomic]
Thread 2: merge("apple", 1, sum) → entry=1  → compute(1+1=2) [atomic]  
Thread 3: merge("apple", 1, sum) → entry=2  → compute(2+1=3) [atomic]

Result: {"apple": 3} — guaranteed correct, no race conditions
Without CHM (using HashMap): threads 1,2,3 might all see null, all put 1 → result = 1 (WRONG)
```

---

## 2. CopyOnWriteArrayList

### What is it

Thread-safe `List` where every **write** creates a fresh copy of the entire array. Reads are completely lock-free. Ideal for rarely-written, frequently-read lists (event listener registries, caches).

### Visual Diagram

```
Initial: array = [A, B, C]   (ref points to this)

Thread 1 reads: reads [A, B, C] (no lock, sees old array)

Thread 2 adds D:
  1. Copy array  → [A, B, C, D] (new array)
  2. Append D
  3. Atomic update reference → new array

Thread 1 still reading old [A, B, C] — snapshot isolation
Thread 3 reads after write: sees [A, B, C, D]

Cost: O(n) per write (full copy)
Benefit: O(1) lock-free reads, iterator never throws ConcurrentModificationException
```

### Example 1 — Safe Iteration During Modification

```java
import java.util.concurrent.*;
import java.util.*;

public class COWArrayListDemo {
    public static void main(String[] args) throws Exception {
        CopyOnWriteArrayList<String> list = new CopyOnWriteArrayList<>();
        list.addAll(List.of("A", "B", "C"));

        // Iterator snapshots the array at creation time
        // Safe even if another thread modifies the list
        Iterator<String> it = list.iterator();

        // Another thread adds while we iterate
        Thread adder = new Thread(() -> list.add("D"));
        adder.start();
        adder.join();

        // This iterator still sees [A, B, C] — snapshot
        while (it.hasNext()) System.out.print(it.next() + " "); // A B C
        System.out.println();

        // New iterator sees the updated list
        System.out.println(list); // [A, B, C, D]

        // addIfAbsent — atomic
        list.addIfAbsent("B"); // does nothing — B exists
        list.addIfAbsent("E"); // adds E
        System.out.println(list); // [A, B, C, D, E]
    }
}
```

**What this does:** Iterators are never invalidated — they snapshot on creation. This is why `CopyOnWriteArrayList` never throws `ConcurrentModificationException`. Trade-off: writes are expensive.

> ⚠️ **Pitfall:** Never use `CopyOnWriteArrayList` for write-heavy workloads. Every `add()` copies the entire backing array — O(n) cost and heavy GC pressure. Use it only when reads >> writes.

---

## 3. CopyOnWriteArraySet

### What is it

Thread-safe `Set` backed by `CopyOnWriteArrayList`. Same copy-on-write semantics — great for small, infrequently updated sets (like event listener sets).

### Example 1

```java
import java.util.concurrent.*;
import java.util.*;

public class COWArraySetDemo {
    public static void main(String[] args) {
        CopyOnWriteArraySet<String> set = new CopyOnWriteArraySet<>();
        set.add("A"); set.add("B"); set.add("C");
        set.add("A"); // duplicate — ignored (Set semantics)

        System.out.println(set); // [A, B, C]
        System.out.println(set.size()); // 3

        // Safe iteration + modification
        for (String s : set) {
            System.out.print(s + " "); // A B C
            // set.add("X"); would not throw ConcurrentModificationException
        }
    }
}
```

---

## 4. BlockingQueue Implementations

### What is it

`BlockingQueue` extends `Queue` with blocking `put()` (waits if full) and `take()` (waits if empty). Foundation of producer-consumer patterns.

### Visual Diagram

```
BlockingQueue<T>
│
├── ArrayBlockingQueue<T>      bounded, array-backed, FIFO
├── LinkedBlockingQueue<T>     optionally bounded, linked nodes, FIFO
├── PriorityBlockingQueue<T>   unbounded, heap-ordered (natural/Comparator)
├── DelayQueue<T>              unbounded, elements become available after delay
├── SynchronousQueue<T>        zero capacity — put() blocks until take() called
└── LinkedTransferQueue<T>     unbounded, extends SynchronousQueue semantics

Key operations:
  put(e)       blocks if full
  take()       blocks if empty
  offer(e)     returns false if full (no block)
  poll()       returns null if empty (no block)
  offer(e,t,u) blocks up to timeout t
  poll(t,u)    blocks up to timeout t
```

### Example 1 — Producer-Consumer with ArrayBlockingQueue

```java
import java.util.concurrent.*;

public class ProducerConsumer {
    public static void main(String[] args) throws Exception {
        BlockingQueue<Integer> queue = new ArrayBlockingQueue<>(5); // capacity 5

        Thread producer = new Thread(() -> {
            try {
                for (int i = 1; i <= 10; i++) {
                    queue.put(i); // blocks if queue full (5 items)
                    System.out.println("Produced: " + i + " | size=" + queue.size());
                }
                queue.put(-1); // poison pill — signals consumer to stop
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        Thread consumer = new Thread(() -> {
            try {
                while (true) {
                    int val = queue.take(); // blocks if queue empty
                    if (val == -1) break;   // poison pill
                    System.out.println("Consumed: " + val);
                    Thread.sleep(50); // simulate processing
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        producer.start();
        consumer.start();
        producer.join();
        consumer.join();
    }
}
```

**What this does:** Classic producer-consumer. `put()` auto-throttles the producer when the queue is at capacity. `take()` blocks the consumer when empty. The poison pill (-1) signals graceful shutdown.

### Example 2 — LinkedBlockingQueue and SynchronousQueue

```java
import java.util.concurrent.*;

public class QueueTypes {
    public static void main(String[] args) throws Exception {
        // LinkedBlockingQueue — optionally bounded (default: Integer.MAX_VALUE)
        // Good for high-throughput (separate head/tail locks)
        LinkedBlockingQueue<String> lbq = new LinkedBlockingQueue<>(100);
        lbq.put("task1");
        lbq.put("task2");
        System.out.println(lbq.take()); // task1 (FIFO)

        // SynchronousQueue — zero capacity "hand-off" queue
        // put() blocks until another thread calls take()
        SynchronousQueue<String> sq = new SynchronousQueue<>();

        Thread passer = new Thread(() -> {
            try {
                System.out.println("Passing: hello");
                sq.put("hello"); // blocks until someone takes
            } catch (InterruptedException e) {}
        });
        passer.start();

        Thread.sleep(50);
        System.out.println("Received: " + sq.take()); // unblocks passer
        passer.join();
    }
}
```

**What this does:** `SynchronousQueue` is useful when you want a direct hand-off between threads — the producer blocks until the consumer is ready. Used internally by `Executors.newCachedThreadPool()`.

---

## 5. ConcurrentLinkedQueue / ConcurrentLinkedDeque

### What is it

Lock-free, non-blocking queue/deque using CAS operations. No blocking — `poll()` returns null if empty (unlike `BlockingQueue`). Best for high-throughput scenarios where blocking is unacceptable.

### Example 1

```java
import java.util.concurrent.*;

public class CLQDemo {
    public static void main(String[] args) throws Exception {
        ConcurrentLinkedQueue<String> queue = new ConcurrentLinkedQueue<>();

        // Multiple threads can safely add/remove
        queue.offer("A"); queue.offer("B"); queue.offer("C");

        System.out.println(queue.poll());  // A (removes)
        System.out.println(queue.peek());  // B (does not remove)
        System.out.println(queue.size());  // 2 (O(n) — avoid in hot path!)

        // Deque — double-ended
        ConcurrentLinkedDeque<Integer> deque = new ConcurrentLinkedDeque<>();
        deque.addFirst(1); deque.addLast(2); deque.addFirst(0);
        System.out.println(deque); // [0, 1, 2]
        System.out.println(deque.pollFirst()); // 0
        System.out.println(deque.pollLast());  // 2
    }
}
```

> ⚠️ **Pitfall:** `ConcurrentLinkedQueue.size()` is O(n) — traverses entire queue. Never call it in a performance-critical loop. Use a separate `AtomicInteger` counter if you need size.

---

## 6. Decision Guide

```
Scenario                                 | Use
-----------------------------------------|----------------------------------
Concurrent read/write map                | ConcurrentHashMap
Atomic map operations (merge, compute)   | ConcurrentHashMap
Read-heavy list (listeners, snapshots)   | CopyOnWriteArrayList
Producer-consumer with backpressure      | ArrayBlockingQueue / LinkedBlockingQueue
Thread pool task queue                   | LinkedBlockingQueue
Direct hand-off between threads          | SynchronousQueue
Lock-free high-throughput queue          | ConcurrentLinkedQueue
Priority-ordered concurrent processing   | PriorityBlockingQueue
Concurrent set                           | ConcurrentHashMap.newKeySet() or CopyOnWriteArraySet

DO NOT use:
  Hashtable                      → use ConcurrentHashMap
  Collections.synchronizedMap()  → use ConcurrentHashMap (finer locking)
  Vector                         → use CopyOnWriteArrayList or synchronized ArrayList
```

---

## Quick Reference

```
ConcurrentHashMap:
  putIfAbsent(k,v)           atomic: put if absent
  computeIfAbsent(k, fn)     atomic: compute if absent
  compute(k, (k,v)->v2)      atomic: always recompute
  merge(k, v, fn)            atomic: combine old + new
  forEach(threshold, fn)     parallel iteration
  reduce(threshold, xform, reducer) parallel reduction

CopyOnWriteArrayList:
  add/remove → O(n) copy    read/iterate → O(1) lock-free
  addIfAbsent(e)             atomic

BlockingQueue:
  put(e)    blocks if full   take()      blocks if empty
  offer(e)  false if full    poll()      null if empty
  offer(e,t,u) timed         poll(t,u)   timed

Implementations:
  ArrayBlockingQueue(n)      bounded FIFO
  LinkedBlockingQueue()      unbounded (MAX_VALUE) FIFO
  PriorityBlockingQueue()    heap-ordered
  SynchronousQueue()         zero-capacity hand-off
```
