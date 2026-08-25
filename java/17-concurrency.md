# Java Concurrency Fundamentals

---

## 1. Thread Lifecycle

**Plain English:** A thread is a lightweight unit of execution. Java threads pass through defined states from creation to termination. Understanding these states helps debug deadlocks, hangs, and performance issues.

**Technical:** The JVM maps Java threads to OS threads. The `Thread.State` enum defines six states. `thread.getState()` returns the current state.

```
ASCII — Thread State Diagram
─────────────────────────────────────────────────────────────────────
                        ┌──────────────────────────────────┐
                        │            NEW                   │
                        │  Thread created, not started     │
                        └──────────────┬───────────────────┘
                                       │ start()
                                       ▼
                        ┌──────────────────────────────────┐
                 ┌─────►│          RUNNABLE                │◄────────┐
                 │      │  Running or ready to run         │         │
                 │      └────┬──────────┬──────────┬───────┘         │
                 │           │          │          │                  │
               notify/    sleep(ms)  wait(ms)  synchronized       lock
             notifyAll    timeout    timeout     acquired         released
             interrupt    expires    expires                         │
                 │           │          │          │                  │
                 │           ▼          ▼          ▼                  │
                 │   ┌─────────────┐ ┌────────┐ ┌──────────────────┐ │
                 │   │TIMED_WAITING│ │WAITING │ │    BLOCKED       │─┘
                 │   │sleep(ms)    │ │wait()  │ │waiting for lock  │
                 │   │join(ms)     │ │join()  │ │on monitor entry  │
                 │   │wait(ms)     │ │park()  │ └──────────────────┘
                 │   └─────────────┘ └────┬───┘
                 └──────────────────────┘
                                       │ run() completes or throws
                                       ▼
                        ┌──────────────────────────────────┐
                        │          TERMINATED              │
                        │  run() returned or threw         │
                        └──────────────────────────────────┘

State Transitions:
  NEW          → RUNNABLE        : start()
  RUNNABLE     → TIMED_WAITING   : sleep(ms), wait(ms), join(ms)
  RUNNABLE     → WAITING         : wait(), join() (no timeout), LockSupport.park()
  RUNNABLE     → BLOCKED         : trying to enter synchronized block (lock held by another)
  BLOCKED      → RUNNABLE        : lock becomes available and thread wins it
  WAITING      → RUNNABLE        : notify() / notifyAll() / interrupt()
  TIMED_WAITING→ RUNNABLE        : timeout expires, notify(), interrupt()
  RUNNABLE     → TERMINATED      : run() returns or throws uncaught exception
─────────────────────────────────────────────────────────────────────
```

**Example 1 — Reading thread state:**
```java
Thread t = new Thread(() -> {
    try { Thread.sleep(2000); } catch (InterruptedException e) {}
});

System.out.println(t.getState()); // NEW
t.start();
System.out.println(t.getState()); // RUNNABLE (or TIMED_WAITING — race)
t.join();
System.out.println(t.getState()); // TERMINATED
```
**What this does:** Captures state before start, during sleep, and after completion. The middle print may show `TIMED_WAITING` if the sleep started before the print executes.

**Example 2 — Demonstrating BLOCKED state:**
```java
Object lock = new Object();

Thread t1 = new Thread(() -> {
    synchronized (lock) {
        try { Thread.sleep(3000); } catch (InterruptedException e) {}
    }
});

Thread t2 = new Thread(() -> {
    synchronized (lock) { /* tries to enter */ }
});

t1.start();
Thread.sleep(100); // let t1 acquire lock and sleep
t2.start();
Thread.sleep(100); // let t2 try to acquire
System.out.println(t2.getState()); // BLOCKED
```
**What this does:** t1 holds the lock while sleeping; t2 cannot enter the synchronized block so it enters BLOCKED state.

**Example 3 — Demonstrating WAITING state:**
```java
Object monitor = new Object();

Thread t = new Thread(() -> {
    synchronized (monitor) {
        try { monitor.wait(); } catch (InterruptedException e) {}
    }
});

t.start();
Thread.sleep(100);
System.out.println(t.getState()); // WAITING
synchronized (monitor) { monitor.notify(); }
t.join();
System.out.println(t.getState()); // TERMINATED
```
**What this does:** `wait()` releases the lock and suspends the thread into WAITING. `notify()` moves it back to RUNNABLE (after re-acquiring the lock).

> ⚠️ **Pitfall:** Calling `getState()` is a snapshot — states change between the call and the print. Never use state polling for synchronization logic.

> ⚠️ **Pitfall:** A thread in BLOCKED state is blocked on a monitor lock. A thread in WAITING state called `wait()` or `join()`. They look similar in thread dumps but have different causes and fixes.

---

## 2. Creating Threads

**Plain English:** Two classic ways to define what a thread does — extend `Thread` and override `run()`, or implement `Runnable` and pass it to a `Thread`. Runnable is almost always preferred.

**Technical:** `Thread` is a class that can be subclassed. `Runnable` is a `@FunctionalInterface` with a single `run()` method. Separation of task (`Runnable`) from thread management follows the single-responsibility principle and is required to use `ExecutorService`.

**Why Runnable over extending Thread:**
- Java has single inheritance — extending Thread wastes the one slot
- Tasks can be submitted to `ExecutorService`, thread pools, `CompletableFuture`
- The task (what to do) is decoupled from execution (how/when to run)

**Example 1 — Extending Thread:**
```java
class CounterThread extends Thread {
    private final String label;

    CounterThread(String label) { this.label = label; }

    @Override
    public void run() {
        for (int i = 1; i <= 3; i++) {
            System.out.println(label + " count: " + i);
        }
    }
}

// Usage
Thread t1 = new CounterThread("Thread-A");
Thread t2 = new CounterThread("Thread-B");
t1.start();
t2.start();
// Output (interleaved, order not guaranteed):
// Thread-A count: 1
// Thread-B count: 1
// Thread-A count: 2
// Thread-B count: 2
// ...
```
**What this does:** Each CounterThread instance IS a thread. `start()` schedules both; the OS interleaves their execution.

**Example 2 — Implementing Runnable:**
```java
class CounterTask implements Runnable {
    private final String label;

    CounterTask(String label) { this.label = label; }

    @Override
    public void run() {
        for (int i = 1; i <= 3; i++) {
            System.out.println(label + " count: " + i);
        }
    }
}

// Usage
Thread t1 = new Thread(new CounterTask("Task-A"));
Thread t2 = new Thread(new CounterTask("Task-B"));
t1.start();
t2.start();
```
**What this does:** The task is a plain object. The `Thread` wraps it. Same task can be passed to an executor without changing the class.

**Example 3 — Runnable as lambda (same task, minimal code):**
```java
Runnable task = () -> {
    for (int i = 1; i <= 3; i++) {
        System.out.println(Thread.currentThread().getName() + " count: " + i);
    }
};

new Thread(task, "Lambda-A").start();
new Thread(task, "Lambda-B").start();
// Output: Lambda-A count: 1 / Lambda-B count: 1 / ...
```
**What this does:** Same Runnable instance reused for two threads. Each thread gets its own call stack; the lambda's local variables (none here) are not shared.

**Example 4 — Why extending Thread is limiting:**
```java
// PROBLEM: can't submit to executor if task IS a Thread
class MyThread extends Thread { @Override public void run() {} }

// Can't do this cleanly:
// executor.submit(new MyThread()); — works but wasteful, thread inside thread

// With Runnable — clean:
class MyTask implements Runnable { @Override public void run() {} }
ExecutorService exec = Executors.newFixedThreadPool(4);
exec.submit(new MyTask()); // natural, decoupled
exec.shutdown();
```
**What this does:** Shows the executor pattern requires Runnable/Callable, not Thread subclasses.

> ⚠️ **Pitfall:** Never call `run()` directly — it executes in the CURRENT thread, no new thread is created. Always call `start()`.

---

## 3. Thread Methods

**Plain English:** The `Thread` class provides methods to control execution, handle interruption, set priority, and query state. Knowing each method's behavior prevents common bugs.

### 3a. start() vs run()

```java
Thread t = new Thread(() -> System.out.println(Thread.currentThread().getName()));

t.run();   // prints: main        ← executes in current thread, no new thread!
t.start(); // prints: Thread-0   ← creates new thread, executes there
```
**What this does:** `run()` is a plain method call. `start()` asks the JVM to create an OS thread and call `run()` on it.

> ⚠️ **Pitfall:** Calling `run()` instead of `start()` is one of the most common concurrency bugs. No exception is thrown — the code "works" but runs single-threaded.

### 3b. sleep()

```java
System.out.println("Before sleep: " + System.currentTimeMillis());
try {
    Thread.sleep(1000); // current thread sleeps 1 second
} catch (InterruptedException e) {
    Thread.currentThread().interrupt(); // restore interrupt flag
    System.out.println("Sleep interrupted");
}
System.out.println("After sleep: " + System.currentTimeMillis());
// Prints roughly 1000ms difference
```
**What this does:** `sleep()` is static — always sleeps the CALLING thread, not the thread object you call it on. Throws checked `InterruptedException`.

### 3c. join()

```java
Thread worker = new Thread(() -> {
    System.out.println("Worker started");
    try { Thread.sleep(500); } catch (InterruptedException e) {}
    System.out.println("Worker done");
});

worker.start();
System.out.println("Main waiting...");
worker.join();           // main thread blocks until worker finishes
System.out.println("Main continues");
// Output (in order):
// Worker started
// Main waiting...
// Worker done
// Main continues
```
**What this does:** `join()` makes the calling thread wait until the target thread terminates. `join(ms)` adds a timeout.

### 3d. interrupt(), isInterrupted(), interrupted()

```java
Thread t = new Thread(() -> {
    while (!Thread.currentThread().isInterrupted()) {
        // do work
        System.out.println("Working...");
    }
    System.out.println("Exiting cleanly");
});

t.start();
Thread.sleep(10);
t.interrupt(); // sets interrupt flag on t
t.join();
// Output: Working... (several times) then "Exiting cleanly"
```
**What this does:** `interrupt()` sets a flag. The thread polls `isInterrupted()` and exits when flagged.

```java
// interrupted() — static, checks AND CLEARS the flag
Thread.currentThread().interrupt(); // set flag
System.out.println(Thread.interrupted());  // true  (flag cleared)
System.out.println(Thread.interrupted());  // false (already cleared)

// isInterrupted() — instance, checks WITHOUT clearing
Thread t2 = new Thread(() -> {});
t2.interrupt();
System.out.println(t2.isInterrupted()); // true
System.out.println(t2.isInterrupted()); // true (flag still set)
```
**What this does:** Shows the critical difference — `interrupted()` is a one-shot read; `isInterrupted()` is repeatable.

| Method | Static? | Clears flag? |
|---|---|---|
| `interrupt()` | No | N/A (sets it) |
| `isInterrupted()` | No | No |
| `interrupted()` | Yes | Yes |

### 3e. yield(), setDaemon(), setName(), getPriority()

```java
// yield() — hint to scheduler to let other threads run
Thread.yield(); // no guarantee, rarely needed in application code

// Daemon threads — JVM exits when only daemons remain
Thread daemon = new Thread(() -> {
    while (true) { /* background monitor */ }
});
daemon.setDaemon(true); // must be called BEFORE start()
daemon.start();
// JVM will exit when main thread finishes, even if daemon is still looping

// Naming and priority
Thread t = new Thread(() -> {});
t.setName("payment-processor");
t.setPriority(Thread.MAX_PRIORITY); // 10; MIN=1, NORM=5
System.out.println(t.getName());    // payment-processor
System.out.println(t.getPriority()); // 10
```
**What this does:** Daemon threads are service threads — garbage collector is a daemon. Priority is a hint to the OS scheduler; not guaranteed.

> ⚠️ **Pitfall:** `setDaemon(true)` must be called before `start()`. Calling it after throws `IllegalThreadStateException`.

> ⚠️ **Pitfall:** When `sleep()` is interrupted, it clears the interrupt flag AND throws `InterruptedException`. Always restore the flag with `Thread.currentThread().interrupt()` in the catch block, or the interrupt signal is lost.

---

## 4. Race Conditions

**Plain English:** A race condition occurs when correctness depends on timing of thread execution. Shared mutable state accessed without synchronization produces unpredictable results.

**Technical:** CPU instruction `i++` is NOT atomic. It compiles to three operations: (1) read value from memory, (2) increment in register, (3) write back. Two threads can interleave these steps, causing lost updates.

```
ASCII — Two Threads Racing on Counter (expected final = 2, actual can be 1)
─────────────────────────────────────────────────────────────────────
Memory: counter = 0

Thread A                        Thread B
─────────────────────────────────────────────────────────────────────
1. READ  counter → reg_A = 0
                                2. READ  counter → reg_B = 0
3. ADD   reg_A + 1 = 1
4. WRITE reg_A → counter = 1
                                5. ADD   reg_B + 1 = 1
                                6. WRITE reg_B → counter = 1  ← lost A's update!

Final counter = 1, NOT 2
─────────────────────────────────────────────────────────────────────
```

**Example 1 — Demonstrating the race (unsynchronized counter):**
```java
class UnsafeCounter {
    int count = 0;
    void increment() { count++; } // NOT atomic: read → add → write
}

UnsafeCounter counter = new UnsafeCounter();

Runnable task = () -> {
    for (int i = 0; i < 1000; i++) counter.increment();
};

Thread t1 = new Thread(task);
Thread t2 = new Thread(task);
t1.start(); t2.start();
t1.join();  t2.join();

System.out.println(counter.count); // expected 2000, often < 2000
// e.g. prints: 1847, 1923, 1756 — different every run
```
**What this does:** Without synchronization, updates overwrite each other. The final value is non-deterministic and almost always less than 2000.

**Dry Run — Interleaving that causes loss (simplified, 2 increments each):**

| Step | Thread A action | reg_A | Thread B action | reg_B | counter |
|---|---|---|---|---|---|
| 1 | READ counter | 0 | | | 0 |
| 2 | | | READ counter | 0 | 0 |
| 3 | ADD reg_A+1 | 1 | | | 0 |
| 4 | WRITE reg_A | | | | 1 |
| 5 | READ counter | 1 | | | 1 |
| 6 | | | ADD reg_B+1 | 1 | 1 |
| 7 | | | WRITE reg_B | | 1 ← A's write overwritten! |
| 8 | ADD reg_A+1 | 2 | | | 1 |
| 9 | WRITE reg_A | | | | 2 |

**Expected: 4. Possible result: 2.**

**Example 2 — Check-then-act race:**
```java
class BankAccount {
    double balance = 100.0;

    void withdraw(double amount) {
        if (balance >= amount) {          // check
            // another thread can run here!
            balance -= amount;            // act
        }
    }
}
// Two threads each withdrawing 80: both pass the check, balance goes negative
```
**What this does:** The if-check and subtraction are not atomic together. Another thread can modify `balance` between the check and the subtraction.

**Example 3 — Race on a collection:**
```java
List<Integer> list = new ArrayList<>();

Runnable adder = () -> {
    for (int i = 0; i < 1000; i++) list.add(i);
};

Thread t1 = new Thread(adder);
Thread t2 = new Thread(adder);
t1.start(); t2.start();
t1.join();  t2.join();

System.out.println(list.size()); // expected 2000, may be < 2000 or throw ArrayIndexOutOfBoundsException
```
**What this does:** `ArrayList` is not thread-safe. Concurrent structural modifications corrupt internal state.

> ⚠️ **Pitfall:** Race conditions are timing-dependent. A program may work correctly in testing (low load, single CPU) but fail in production (high load, multi-core). Never assume "it works in testing" means it's thread-safe.

> ⚠️ **Pitfall:** Compound operations like `if (map.containsKey(k)) map.get(k)` are races even if `map` is a `ConcurrentHashMap`. Use `map.computeIfAbsent()` instead.

---

## 5. synchronized

**Plain English:** The `synchronized` keyword ensures only one thread at a time can execute a block. It also flushes memory, so threads see each other's writes.

**Technical:** `synchronized` acquires an intrinsic monitor lock (every Java object has one). It provides two guarantees: **mutual exclusion** (one thread at a time) and **happens-before** visibility (writes before releasing the lock are visible to threads that subsequently acquire the same lock).

**Lock types:**
```
synchronized method          → locks on `this`
synchronized static method   → locks on Class object (MyClass.class)
synchronized(obj) { }        → locks on `obj`
```

**Example 1 — Synchronized instance method (lock on `this`):**
```java
class SafeCounter {
    private int count = 0;

    public synchronized void increment() {
        count++; // only one thread can execute this at a time
    }

    public synchronized int getCount() {
        return count; // visibility: reads fresh value
    }
}

SafeCounter counter = new SafeCounter();
Runnable task = () -> {
    for (int i = 0; i < 1000; i++) counter.increment();
};

Thread t1 = new Thread(task);
Thread t2 = new Thread(task);
t1.start(); t2.start();
t1.join();  t2.join();

System.out.println(counter.getCount()); // always 2000
```
**What this does:** Both `increment()` and `getCount()` lock on the same object (`counter`), ensuring mutual exclusion and visibility.

**Dry Run — Two threads on synchronized increment (counter starts at 5):**

| Step | Thread A | Thread B | Lock holder | counter |
|---|---|---|---|---|
| 1 | tries increment() | tries increment() | free | 5 |
| 2 | acquires lock | BLOCKED | Thread A | 5 |
| 3 | reads count = 5 | BLOCKED | Thread A | 5 |
| 4 | writes count = 6 | BLOCKED | Thread A | 6 |
| 5 | releases lock | RUNNABLE | free | 6 |
| 6 | | acquires lock | Thread B | 6 |
| 7 | | reads count = 6 | Thread B | 6 |
| 8 | | writes count = 7 | Thread B | 7 |
| 9 | | releases lock | free | 7 |

**Always sequential. Final = 7.**

**Example 2 — Synchronized static method (lock on Class):**
```java
class Registry {
    private static int instanceCount = 0;

    public static synchronized void register() {
        instanceCount++; // lock on Registry.class, not on any instance
    }

    public static synchronized int getCount() {
        return instanceCount;
    }
}
// Safe across ALL instances — all threads share Registry.class as lock
```
**What this does:** Static synchronized methods protect static (class-level) state. Instance-level `synchronized` methods do NOT protect static fields.

**Example 3 — Synchronized block (fine-grained locking):**
```java
class OrderProcessor {
    private final Object inventoryLock = new Object();
    private final Object paymentLock   = new Object();
    private int inventory = 100;
    private double revenue = 0;

    void process(int qty, double price) {
        synchronized (inventoryLock) {
            inventory -= qty; // only locks inventory
        }
        // both can proceed here in parallel
        synchronized (paymentLock) {
            revenue += price; // only locks revenue
        }
    }
}
```
**What this does:** Two independent locks allow inventory and payment updates to proceed concurrently when accessing different data, reducing contention vs. locking on `this` for everything.

**Example 4 — Reentrancy (same thread re-acquires its own lock):**
```java
class Reentrant {
    public synchronized void outer() {
        System.out.println("outer");
        inner(); // calls synchronized method while already holding lock on this
    }

    public synchronized void inner() {
        System.out.println("inner"); // does NOT deadlock — same thread re-acquires
    }
}
new Reentrant().outer();
// Output: outer / inner — no deadlock
```
**What this does:** Java's intrinsic locks are reentrant. A thread holding a lock can acquire the same lock again without blocking itself.

> ⚠️ **Pitfall:** Synchronizing on DIFFERENT objects does not protect the same data. `synchronized(lockA)` in one method and `synchronized(lockB)` in another leaves the shared field unprotected.

> ⚠️ **Pitfall:** Synchronizing on a mutable reference (one that can be reassigned) is dangerous. If `lock = new Object()` happens, threads may acquire different locks. Always use `final` lock objects.

> ⚠️ **Pitfall:** Large synchronized blocks kill parallelism. Synchronize only the minimum code that needs mutual exclusion.

---

## 6. volatile

**Plain English:** Without `volatile`, each CPU core may cache a variable's value in its L1/L2 cache. One thread's write may not be visible to another thread reading from its own cache.

**Technical:** `volatile` ensures: (1) reads and writes go directly to main memory — no CPU cache; (2) prevents instruction reordering across a volatile read/write (happens-before). `volatile` does NOT make compound operations atomic.

```
ASCII — CPU Cache Problem (without volatile)
─────────────────────────────────────────────────────────────────────
Main Memory: running = true

Core 1 (Writer Thread)        Core 2 (Reader Thread)
L1 Cache: running = true      L1 Cache: running = true (stale copy)

  running = false;              while (running) { ... }
  writes to L1 only             reads from L1 — sees old true!
  may never flush to main       loops forever — never sees false
─────────────────────────────────────────────────────────────────────

With volatile: all reads/writes bypass cache → both cores see main memory value
─────────────────────────────────────────────────────────────────────
```

**Example 1 — Broken flag (without volatile):**
```java
class StopTask implements Runnable {
    boolean running = true; // NOT volatile — may never see update

    public void run() {
        while (running) { /* spin */ }
        System.out.println("stopped");
    }

    void stop() { running = false; }
}

StopTask task = new StopTask();
new Thread(task).start();
Thread.sleep(100);
task.stop();
// May print "stopped" OR may loop forever (JIT hoists `running` into register)
```
**What this does:** Without `volatile`, the JIT compiler can optimize `while(running)` into `while(true)` because it sees no write to `running` in that thread.

**Example 2 — Fixed flag (with volatile):**
```java
class SafeStopTask implements Runnable {
    volatile boolean running = true; // all threads see writes immediately

    public void run() {
        while (running) { /* spin */ }
        System.out.println("stopped"); // always reached after stop()
    }

    void stop() { running = false; }
}
```
**What this does:** `volatile` prevents the JIT optimization and ensures the write in `stop()` is visible to the spin loop.

**Example 3 — volatile does NOT fix i++ (still a race):**
```java
class VolatileCounter {
    volatile int count = 0;

    void increment() {
        count++; // STILL not atomic: read-modify-write are 3 separate volatile operations
    }
}
// Two threads incrementing 1000 times → result still < 2000
// volatile only guarantees each individual read/write is visible, not that the 3-step sequence is uninterrupted
```
**What this does:** Demonstrates that `volatile` is NOT a replacement for `synchronized` on compound operations. Use `AtomicInteger` for this.

**Example 4 — Double-checked locking (classic volatile use case):**
```java
class Singleton {
    private static volatile Singleton instance; // volatile required here

    private Singleton() {}

    public static Singleton getInstance() {
        if (instance == null) {                    // first check (no lock)
            synchronized (Singleton.class) {
                if (instance == null) {            // second check (with lock)
                    instance = new Singleton();    // volatile prevents partial construction visibility
                }
            }
        }
        return instance;
    }
}
```
**What this does:** Without `volatile`, another thread could see a non-null but partially constructed object due to instruction reordering. `volatile` creates a happens-before fence around the assignment.

| | volatile | synchronized |
|---|---|---|
| Visibility | Yes | Yes |
| Atomicity of compound ops | No | Yes |
| Mutual exclusion | No | Yes |
| Performance | Low overhead | Higher overhead |

> ⚠️ **Pitfall:** `volatile` on a reference makes the reference write/read visible, but NOT the fields of the referenced object. To publish an object safely, all its fields must be final (immutable), or synchronization is needed.

> ⚠️ **Pitfall:** `volatile` reads and writes cannot be cached, which has performance cost. Only use for genuinely shared flags or lightweight signaling, not as a general replacement for `synchronized`.

---

## 7. Atomic Variables

**Plain English:** `java.util.concurrent.atomic` classes provide thread-safe operations on single variables without using `synchronized`. They use hardware-level Compare-And-Swap (CAS) instructions — extremely fast.

**Technical:** CAS: "set value to `update` ONLY IF current value == `expected`". If another thread changed it first, CAS fails and the operation retries (spin loop internally). This is non-blocking and often faster than locking.

```
ASCII — Compare-And-Swap (CAS) Principle
─────────────────────────────────────────────────────────────────────
Memory location: value = 5

Thread A: compareAndSet(expected=5, update=6)
  1. Read value = 5
  2. Is 5 == expected(5)? YES
  3. Atomically swap: value = 6  ✓

Thread B (simultaneously): compareAndSet(expected=5, update=6)
  1. Read value = 5 (or 6 if A won)
  2. Is 6 == expected(5)? NO ← A already changed it
  3. CAS fails → retry loop reads new value (6), tries (6→7)
─────────────────────────────────────────────────────────────────────
```

**Example 1 — AtomicInteger: safe counter without synchronized:**
```java
import java.util.concurrent.atomic.AtomicInteger;

AtomicInteger counter = new AtomicInteger(0);

Runnable task = () -> {
    for (int i = 0; i < 1000; i++) {
        counter.incrementAndGet(); // atomic: read-increment-write in one CAS
    }
};

Thread t1 = new Thread(task);
Thread t2 = new Thread(task);
t1.start(); t2.start();
t1.join();  t2.join();

System.out.println(counter.get()); // always 2000
```
**What this does:** `incrementAndGet()` returns the new value. `getAndIncrement()` returns the old value. Both are atomic without any explicit locking.

**Example 2 — Key AtomicInteger methods:**
```java
AtomicInteger ai = new AtomicInteger(10);

System.out.println(ai.get());               // 10  — read
System.out.println(ai.getAndIncrement());   // 10  — read old, then +1 → value=11
System.out.println(ai.incrementAndGet());   // 12  — +1, then read new
System.out.println(ai.getAndAdd(5));        // 12  — read old, then +5 → value=17
System.out.println(ai.addAndGet(3));        // 20  — +3, then read new
System.out.println(ai.get());               // 20

ai.set(0);                                  // unconditional set
System.out.println(ai.get());               // 0
```
**What this does:** Shows the full API. "getAnd..." returns old value; "...AndGet" returns new value.

**Example 3 — compareAndSet (CAS): the fundamental primitive:**
```java
AtomicInteger value = new AtomicInteger(5);

boolean success1 = value.compareAndSet(5, 10); // expected=5, update=10
System.out.println(success1 + " " + value.get()); // true 10

boolean success2 = value.compareAndSet(5, 20); // expected=5 but value is now 10
System.out.println(success2 + " " + value.get()); // false 10 ← not changed

// CAS-based non-blocking increment (what AtomicInteger does internally):
AtomicInteger counter = new AtomicInteger(0);
int oldVal, newVal;
do {
    oldVal = counter.get();
    newVal = oldVal + 1;
} while (!counter.compareAndSet(oldVal, newVal)); // retry if another thread won
```
**What this does:** `compareAndSet` is the hardware-level primitive. The loop retries until the CAS succeeds (value hasn't changed since we read it).

**Dry Run — Two threads doing CAS increment from value=5:**

| Step | Thread A | Thread B | value |
|---|---|---|---|
| 1 | oldVal = 5 | oldVal = 5 | 5 |
| 2 | CAS(5→6): wins | | 6 |
| 3 | done, newVal=6 | CAS(5→6): fails (value is 6, not 5) | 6 |
| 4 | | re-read oldVal = 6 | 6 |
| 5 | | CAS(6→7): wins | 7 |

**Both increments applied. Final = 7.**

**Example 4 — AtomicReference and LongAdder:**
```java
import java.util.concurrent.atomic.*;

// AtomicBoolean — simple flag
AtomicBoolean started = new AtomicBoolean(false);
if (started.compareAndSet(false, true)) {
    System.out.println("I started it"); // only one thread prints this
}

// AtomicReference — CAS on object reference
AtomicReference<String> ref = new AtomicReference<>("initial");
ref.compareAndSet("initial", "updated"); // swap if still "initial"
System.out.println(ref.get()); // updated

// LongAdder — high-contention counter (Java 8+)
LongAdder adder = new LongAdder();
adder.increment();              // add 1
adder.add(5);                   // add 5
System.out.println(adder.sum()); // 6 — reads sum across all stripes

// LongAdder splits counter across multiple cells (stripes) by thread
// Under contention, threads update different cells → no CAS retry fights
// sum() combines all cells → slight inconsistency under concurrent adds (acceptable for stats)
```
**What this does:** `AtomicBoolean.compareAndSet(false, true)` is idiomatic for "do this exactly once" initialization. `LongAdder` trades memory for throughput when many threads increment simultaneously.

**AtomicLong vs LongAdder — When to use which:**

| | AtomicLong | LongAdder |
|---|---|---|
| Low contention | Excellent | Fine (slight overhead) |
| High contention | CAS retries → CPU spin | Striped cells → scales linearly |
| Need exact value any time | Yes | No (sum() is approximate under concurrency) |
| Use case | Sequence numbers, IDs | Statistics, counters, metrics |
| Memory | ~16 bytes | Variable (more cells under load) |

```java
// AtomicLong — use when you need consistent read after write
AtomicLong sequenceId = new AtomicLong(0);
long nextId = sequenceId.incrementAndGet(); // guaranteed unique IDs

// LongAdder — use for throughput metrics
LongAdder requestCount = new LongAdder();
// in each request handler: requestCount.increment()
// in metrics reporter: requestCount.sum()
```
**What this does:** Sequence generators need `AtomicLong` because every increment must be visible to every reader. Request counters use `LongAdder` because approximate stats under load are fine.

> ⚠️ **Pitfall:** `AtomicReference` compares by identity (`==`), not equality (`.equals()`). `compareAndSet` with a new String object will always fail even if the contents match. Use the SAME reference.

> ⚠️ **Pitfall:** CAS does not protect against the ABA problem: value goes A→B→A between your read and CAS. Your CAS succeeds even though the value changed. Use `AtomicStampedReference` (adds a version counter) when ABA matters (e.g., lock-free linked lists).

> ⚠️ **Pitfall:** `LongAdder.sum()` is eventually consistent — it may not reflect the most recent `increment()` call from another thread. Only `AtomicLong` guarantees a consistent snapshot.

---

## Quick Reference

```
Problem                          Solution
──────────────────────────────────────────────────────────────
Shared counter                   AtomicInteger / AtomicLong
Visibility-only flag             volatile boolean
Mutual exclusion + visibility    synchronized
One-time initialization          AtomicBoolean.compareAndSet
High-throughput counter          LongAdder
Safe object publish              volatile reference + final fields
Thread coordination (wait/notify) synchronized + wait/notify (or higher-level util)
```
