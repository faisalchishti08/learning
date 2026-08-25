# Java Memory Model (JMM)

## Overview

The Java Memory Model (JMM) defines how threads interact through shared memory. It specifies **visibility** (when writes become visible to other threads) and **ordering** (what reordering of operations is allowed). Without JMM guarantees, multi-threaded programs have unpredictable behavior.

---

## 1. The Problem — Visibility and Reordering

### Visual Diagram — Without JMM Guarantees

```
CPU architecture has:
  CPU 1           CPU 2
  ┌────────┐      ┌────────┐
  │ L1 $ │      │ L1 $ │
  │ L2 $ │      │ L2 $ │
  └────────┘      └────────┘
       └─────┬─────┘
             ▼
          Main Memory

Thread 1 writes x=1:
  → stored in CPU 1's L1 cache
  → NOT immediately flushed to main memory
  → Thread 2 on CPU 2 reads x → may still see x=0 ← VISIBILITY PROBLEM

Compiler/CPU reordering:
  Code:       Thread 1 does: a=1; b=2;
  Actual:     CPU may execute b=2 then a=1 (if no dependency)
              Thread 2 may see b=2 before a=1 ← ORDERING PROBLEM
```

### Example 1 — Visibility Bug Without volatile

```java
public class VisibilityBug {
    static boolean stop = false; // NO volatile — dangerous!

    public static void main(String[] args) throws Exception {
        Thread worker = new Thread(() -> {
            int count = 0;
            while (!stop) { // may loop forever — sees cached stop=false
                count++;
            }
            System.out.println("Stopped at: " + count);
        });

        worker.start();
        Thread.sleep(100);
        stop = true; // written to main memory — but worker may not see it!
        worker.join(1000);
        // May timeout — worker may never see stop=true
        System.out.println("Main done");
    }
}
```

**What this does:** Without `volatile`, the JVM may cache `stop` in a register for the worker thread. The write `stop = true` in main may never be visible to the worker. The fix: `volatile boolean stop = false`.

---

## 2. Happens-Before Relationship

### What is it

The JMM defines **happens-before** (HB) — a guarantee that if action A HB action B, then A's effects are visible to B. The key rules:

### Visual Diagram — Happens-Before Rules

```
Rule 1: Program order within a thread
  All actions in a single thread happen-before subsequent actions in that thread.
  a=1; b=2;  → a=1 HB b=2 (within same thread)

Rule 2: Monitor lock (synchronized)
  unlock(monitor) HB lock(monitor) [any thread locking same monitor]
  
Rule 3: volatile write → volatile read
  write(volatile x) HB read(volatile x) [all subsequent reads]

Rule 4: Thread start
  ThreadA.start() HB all actions in ThreadA

Rule 5: Thread join
  All actions in ThreadA HB ThreadA.join() returns

Rule 6: Static initializer
  Static initializer completes HB first access to that class

Rule 7: Transitivity
  If A HB B and B HB C, then A HB C

Practical meaning:
  If write W HB read R:
    - W's value is visible to R
    - All writes before W (in program order) are also visible to R
```

### Example 1 — volatile Establishes HB

```java
public class VolatileHB {
    static int data = 0;
    static volatile boolean ready = false; // volatile creates HB

    static void writer() {
        data = 42;       // (1) write data
        ready = true;    // (2) write volatile ready
        // (1) HB (2) via program order
    }

    static void reader() {
        while (!ready) {} // spin until ready
        // The volatile read of ready HB here
        // volatile write (2) HB volatile read (this read)
        // By transitivity: (1) HB (this point)
        // Therefore: data == 42 is GUARANTEED visible
        System.out.println(data); // guaranteed: 42
    }

    public static void main(String[] args) throws Exception {
        Thread t1 = new Thread(VolatileHB::reader);
        Thread t2 = new Thread(VolatileHB::writer);
        t1.start();
        Thread.sleep(10);
        t2.start();
        t1.join(); t2.join();
    }
}
```

**What this does:** The volatile write to `ready` establishes happens-before for the volatile read. Because `data=42` happens-before the volatile write (program order), transitivity guarantees `data==42` is visible to the reader.

### Dry Run — HB Chain

```
Thread 1 (writer):
  data = 42     [action A]
  ready = true  [volatile write B]
  A HB B (program order)

Thread 2 (reader):
  read ready     [volatile read C]  ← sees true
  C HB D (program order)
  read data      [action D]

HB chain:
  A (data=42) HB B (volatile write) HB C (volatile read) HB D (read data)
  Therefore: D sees data=42 ← GUARANTEED
```

---

## 3. volatile

### What is it

`volatile` on a variable guarantees: (1) visibility — writes are immediately visible to all threads, (2) no reordering across the write/read. Does NOT guarantee atomicity for compound operations.

### Example 1 — volatile Correct vs Wrong Use

```java
import java.util.concurrent.atomic.*;

public class VolatileUsage {
    // CORRECT: single write from one thread, multiple readers
    volatile boolean flag = false;
    volatile int configVersion = 0;

    // WRONG: volatile does NOT make compound operations atomic
    volatile int counter = 0;

    void wrongIncrement() {
        counter++; // read-modify-write: NOT atomic even with volatile!
        // counter++ expands to:
        //   int tmp = counter; // read
        //   tmp = tmp + 1;     // modify
        //   counter = tmp;     // write
        // Two threads can both read 5, both compute 6, both write 6 → count stays 5!
    }

    // CORRECT for counter: use AtomicInteger
    AtomicInteger atomicCounter = new AtomicInteger(0);
    void correctIncrement() {
        atomicCounter.incrementAndGet(); // atomic read-modify-write via CAS
    }

    // volatile for flags/state (single writer)
    void stop() { flag = true; }
    boolean shouldStop() { return flag; }
}
```

**What this does:** `volatile` works correctly for single-writer scenarios (flag, config version). Fails for read-modify-write patterns (increment, compare-and-swap). Use `AtomicInteger/Long/Reference` for compound operations.

---

## 4. synchronized and Memory Visibility

### Example 1 — synchronized Establishes Full Visibility

```java
public class SynchronizedVisibility {
    int x = 0;
    int y = 0;

    // synchronized on same object creates happens-before
    synchronized void write(int x, int y) {
        this.x = x;
        this.y = y;
    }

    synchronized int[] read() {
        return new int[]{x, y}; // if any write() HB this read(), sees consistent state
    }

    // Double-checked locking — correct with volatile [Java 5+]
    private volatile Object instance = null;

    Object getInstance() {
        if (instance == null) {             // first check (no lock)
            synchronized (this) {
                if (instance == null) {     // second check (with lock)
                    instance = new Object(); // volatile write — publish safely
                }
            }
        }
        return instance; // volatile read — sees fully constructed object
    }
}
```

**What this does:** Double-checked locking requires `volatile` on the field. Without `volatile`, the JIT may reorder the write to `instance` before the object is fully constructed — another thread sees a partially initialized object.

---

## 5. Safe Publication

### What is it

An object is "safely published" if all threads see its fully initialized state. Unsafe publication can lead to partially constructed objects being visible.

### Visual Diagram — Safe vs Unsafe Publication

```
UNSAFE: plain field write (no synchronization)
  Thread 1: obj = new ComplexObject(); // may be reordered — ref visible before fields init
  Thread 2: if (obj != null) obj.use(); // may see obj with default-initialized fields!

SAFE publication methods:
  1. Initialize in static field:     static final Obj INSTANCE = new Obj(); ← class loading HB
  2. volatile field:                 volatile Obj ref = new Obj(); ← volatile HB
  3. Synchronized write then read:   synchronized publish, synchronized read ← lock HB
  4. Concurrent collection:          ConcurrentHashMap.put() then get() ← CHM internal HB
  5. Thread start:                   start() HB all actions in thread ← pass via start
  6. final fields:                   final fields are safe after constructor completes ← JMM guarantee
```

### Example 1 — Safe Publication with final and volatile

```java
public class SafePublication {
    // Safe: final fields (JMM guarantees final fields are visible after constructor)
    static class ImmutablePoint {
        final int x, y; // final guarantees safe publication
        ImmutablePoint(int x, int y) { this.x = x; this.y = y; }
    }

    // Safe: static final (class initialization HB any use)
    static final ImmutablePoint ORIGIN = new ImmutablePoint(0, 0);

    // Safe: volatile reference to mutable object
    // Note: only the REFERENCE is volatile — object fields still need synchronization
    volatile ImmutablePoint current = ORIGIN;

    void update(int x, int y) {
        current = new ImmutablePoint(x, y); // volatile write — safe publication
    }

    ImmutablePoint getCurrent() {
        return current; // volatile read — sees fully constructed ImmutablePoint
    }
}
```

**What this does:** `final` fields are the simplest safe publication — after the constructor completes, any thread that sees the object reference also sees the final fields' values. Key insight: `volatile ref = new Immutable()` is safe; `volatile ref = new Mutable()` only guarantees the ref, not Mutable's non-volatile fields.

---

## 6. Memory Ordering and Fences

### Visual Diagram — Ordering Effects

```
Reordering types the JMM prohibits (with the right primitives):
  LoadLoad:   read(a); read(b) → b may be read before a without barrier
  StoreStore: write(a); write(b) → b may be written before a without barrier
  LoadStore:  read(a); write(b) → write may happen before read without barrier
  StoreLoad:  write(a); read(b) → most expensive — volatile read/write prevents this

volatile write creates: StoreStore + StoreLoad barrier (after)
volatile read creates:  LoadLoad + LoadStore barrier (before)
synchronized: both (monitor exit = full fence, monitor enter = full fence)

CPU-level: Java maps these to platform-specific fence instructions
  x86: mostly TSO (total store order) — cheaper
  ARM: weakly ordered — more fences needed
```

### Example 1 — AtomicReference for Safe CAS

```java
import java.util.concurrent.atomic.*;

public class AtomicReferenceDemo {
    record Config(String host, int port) {}

    // Atomic reference — thread-safe reference swap
    static AtomicReference<Config> config =
        new AtomicReference<>(new Config("localhost", 8080));

    static void updateConfig(String host, int port) {
        Config oldConfig;
        Config newConfig;
        do {
            oldConfig = config.get();
            newConfig = new Config(host, port);
        } while (!config.compareAndSet(oldConfig, newConfig));
        // compareAndSet: atomic compare and swap
        // If config still equals oldConfig, replace with newConfig and return true
        // If another thread changed config, loop and retry
    }

    public static void main(String[] args) throws Exception {
        System.out.println(config.get()); // Config[host=localhost, port=8080]

        Thread t1 = new Thread(() -> updateConfig("server1", 443));
        Thread t2 = new Thread(() -> updateConfig("server2", 80));
        t1.start(); t2.start();
        t1.join(); t2.join();

        // One of the two updates won — atomically consistent
        System.out.println(config.get());
    }
}
```

**What this does:** Compare-and-swap (CAS) is the foundation of lock-free programming. `compareAndSet` atomically reads the current value, compares to expected, and writes new value only if equal — all in one CPU instruction.

---

## Quick Reference

```
Happens-before establishes visibility:
  Program order (within thread)
  synchronized unlock → lock
  volatile write → volatile read
  Thread.start() → thread actions
  thread actions → Thread.join()
  Static init → first class use
  Transitivity

volatile:
  Visibility: YES — writes immediately visible
  Ordering:   YES — no reordering across volatile access
  Atomicity:  NO  — counter++ still not atomic

synchronized:
  Visibility: YES — full memory fence on lock/unlock
  Ordering:   YES — no reordering out of synchronized block
  Atomicity:  YES — mutual exclusion

Safe publication:
  final fields      → safe after constructor
  static final      → safe via class loading
  volatile write    → safe reference publication
  synchronized      → safe with matching lock
  Concurrent coll.  → safe via internal HB

Atomic classes:
  AtomicInteger/Long/Boolean      atomic r-m-w primitives
  AtomicReference<T>              atomic reference swap
  compareAndSet(expected, update) CAS — basis of lock-free
```
