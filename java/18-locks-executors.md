# Java Locks, Executors, and Thread Pools

---

## 1. Lock Interface

`java.util.concurrent.locks.Lock` — explicit locking, more flexible than `synchronized`.

### Why use Lock over synchronized?

| Feature                  | synchronized | Lock |
|--------------------------|-------------|------|
| tryLock (non-blocking)   | No          | Yes  |
| tryLock with timeout     | No          | Yes  |
| Interruptible lock wait  | No          | Yes  |
| Multiple conditions      | No          | Yes  |
| Fair ordering            | No          | Yes  |
| Manual unlock            | No (auto)   | Yes (required) |

### Key Methods

| Method                          | Behavior |
|---------------------------------|----------|
| `lock()`                        | Blocks until lock acquired |
| `unlock()`                      | Releases lock (MUST be in finally) |
| `tryLock()`                     | Returns `true` if acquired immediately, `false` otherwise — never blocks |
| `tryLock(long time, TimeUnit u)`| Waits up to `time`, returns `false` on timeout |
| `lockInterruptibly()`           | Blocks but can be interrupted by `Thread.interrupt()` |

### Mandatory Template

```java
Lock lock = new ReentrantLock();

lock.lock();           // acquire
try {
    // critical section
} finally {
    lock.unlock();     // ALWAYS in finally — even if exception thrown
}
```

**What this does:** `finally` guarantees `unlock()` runs even if the critical section throws. Forgetting `finally` causes deadlock if exception escapes.

---

### Example 1 — Basic lock/unlock

```java
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class Counter {
    private int count = 0;
    private final Lock lock = new ReentrantLock();

    public void increment() {
        lock.lock();
        try {
            count++;
        } finally {
            lock.unlock();
        }
    }

    public int getCount() { return count; }

    public static void main(String[] args) throws InterruptedException {
        Counter c = new Counter();
        Thread t1 = new Thread(() -> { for (int i = 0; i < 1000; i++) c.increment(); });
        Thread t2 = new Thread(() -> { for (int i = 0; i < 1000; i++) c.increment(); });
        t1.start(); t2.start();
        t1.join();  t2.join();
        System.out.println(c.getCount()); // 2000
    }
}
```

**What this does:** Two threads increment a shared counter 1000 times each. `lock.lock()` in `finally` ensures no race condition. Without lock, `count++` (read-modify-write) can interleave and produce < 2000.

---

### Example 2 — tryLock() (non-blocking attempt)

```java
import java.util.concurrent.locks.ReentrantLock;

public class TryLockDemo {
    private final ReentrantLock lock = new ReentrantLock();

    public void doWork(String threadName) {
        if (lock.tryLock()) {            // returns immediately
            try {
                System.out.println(threadName + " acquired lock");
                Thread.sleep(100);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } finally {
                lock.unlock();
            }
        } else {
            System.out.println(threadName + " could not acquire lock — skipping");
        }
    }

    public static void main(String[] args) {
        TryLockDemo demo = new TryLockDemo();
        Thread t1 = new Thread(() -> demo.doWork("T1"));
        Thread t2 = new Thread(() -> demo.doWork("T2"));
        t1.start(); t2.start();
    }
}
// Output (one possible):
// T1 acquired lock
// T2 could not acquire lock — skipping
```

**What this does:** `tryLock()` returns `false` immediately if lock is held — no blocking. T2 skips rather than waiting. Useful for deadlock-avoidance, non-critical paths.

---

### Example 3 — tryLock with timeout

```java
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

public class TimeoutLockDemo {
    private final ReentrantLock lock = new ReentrantLock();

    public void doWork(String name) {
        try {
            if (lock.tryLock(200, TimeUnit.MILLISECONDS)) {
                try {
                    System.out.println(name + " got lock");
                    Thread.sleep(500);
                } finally {
                    lock.unlock();
                }
            } else {
                System.out.println(name + " timed out waiting for lock");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
// T1 starts, holds lock 500ms. T2 waits 200ms → times out and prints "timed out".
```

**What this does:** Thread waits up to 200ms for the lock. If not acquired in that window, it continues without blocking forever.

> ⚠️ **Pitfall:** `tryLock()` with no args and `tryLock(0, unit)` behave differently. `tryLock()` is non-fair (can barge ahead of waiting threads even on a fair lock). Always prefer `tryLock(0, TimeUnit.NANOSECONDS)` if you need fair semantics.

---

### Example 4 — lockInterruptibly()

```java
import java.util.concurrent.locks.ReentrantLock;

public class InterruptibleLock {
    private final ReentrantLock lock = new ReentrantLock();

    public void doWork() throws InterruptedException {
        lock.lockInterruptibly();   // throws InterruptedException if interrupted while waiting
        try {
            System.out.println(Thread.currentThread().getName() + " working");
            Thread.sleep(1000);
        } finally {
            lock.unlock();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        InterruptibleLock demo = new InterruptibleLock();
        Thread t1 = new Thread(() -> {
            try { demo.doWork(); } catch (InterruptedException e) {
                System.out.println("T1 interrupted while waiting for lock");
            }
        });
        Thread t2 = new Thread(() -> {
            try { demo.doWork(); } catch (InterruptedException e) {
                System.out.println("T2 interrupted while waiting for lock");
            }
        });
        t1.start();
        Thread.sleep(50);
        t2.start();
        Thread.sleep(50);
        t2.interrupt();   // interrupt T2 while it waits for lock held by T1
        t1.join(); t2.join();
    }
}
```

**What this does:** T2 waits for the lock (held by T1). When `t2.interrupt()` is called, `lockInterruptibly()` throws `InterruptedException` — T2 escapes. `lock()` would NOT respond to interrupts.

---

## 2. ReentrantLock

Same thread can acquire the lock multiple times — lock is reentrant. Hold count incremented each lock, decremented each unlock. Lock released when hold count reaches 0.

```
Thread acquires lock:
  lock()  →  holdCount = 1
  lock()  →  holdCount = 2   (reentrant — allowed)
  lock()  →  holdCount = 3
  unlock() → holdCount = 2
  unlock() → holdCount = 1
  unlock() → holdCount = 0  → lock RELEASED
```

### Example 1 — Reentrancy demonstration

```java
import java.util.concurrent.locks.ReentrantLock;

public class ReentrantDemo {
    private final ReentrantLock lock = new ReentrantLock();

    public void outer() {
        lock.lock();
        try {
            System.out.println("outer: holdCount = " + lock.getHoldCount()); // 1
            inner();
        } finally {
            lock.unlock();
        }
    }

    public void inner() {
        lock.lock();
        try {
            System.out.println("inner: holdCount = " + lock.getHoldCount()); // 2
        } finally {
            lock.unlock();
        }
        System.out.println("after inner unlock: holdCount = " + lock.getHoldCount()); // 1
    }

    public static void main(String[] args) {
        new ReentrantDemo().outer();
    }
}
// Output:
// outer: holdCount = 1
// inner: holdCount = 2
// after inner unlock: holdCount = 1
```

**What this does:** `outer()` holds lock (count=1), calls `inner()` which re-acquires same lock (count=2). Each `unlock()` decrements. No deadlock because same thread is allowed.

---

### Example 2 — isHeldByCurrentThread() guard

```java
import java.util.concurrent.locks.ReentrantLock;

public class HeldByCurrentThread {
    private final ReentrantLock lock = new ReentrantLock();

    public void safeMethod() {
        boolean alreadyHeld = lock.isHeldByCurrentThread();
        if (!alreadyHeld) lock.lock();
        try {
            System.out.println("Executing, holdCount=" + lock.getHoldCount());
            // do work
        } finally {
            if (!alreadyHeld) lock.unlock();
        }
    }
}
```

**What this does:** Conditionally acquires only if not already held by this thread. Useful when a method may be called both from locked and unlocked contexts.

---

### Example 3 — Fair vs Unfair lock

```java
import java.util.concurrent.locks.ReentrantLock;

ReentrantLock unfair = new ReentrantLock();        // default: unfair
ReentrantLock fair   = new ReentrantLock(true);    // fair: FIFO ordering

// Fair lock: threads acquire in the order they requested
// Unfair lock: newly arriving thread may barge past waiting threads (higher throughput, lower latency average)
```

**What this does:** Fair lock guarantees no starvation — threads are served in request order. Unfair (default) allows barging — faster on average but can starve waiting threads.

> ⚠️ **Pitfall:** Fair locks have significantly lower throughput. Use `fair=true` only when you specifically need FIFO ordering or starvation prevention. Don't use it by default.

---

### Example 4 — Full pattern with Condition

```java
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;
import java.util.LinkedList;
import java.util.Queue;

public class BoundedQueue<T> {
    private final Queue<T> queue = new LinkedList<>();
    private final int capacity;
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition notFull  = lock.newCondition();
    private final Condition notEmpty = lock.newCondition();

    public BoundedQueue(int capacity) { this.capacity = capacity; }

    public void put(T item) throws InterruptedException {
        lock.lock();
        try {
            while (queue.size() == capacity) notFull.await();  // wait until space
            queue.add(item);
            notEmpty.signal();  // wake one consumer
        } finally {
            lock.unlock();
        }
    }

    public T take() throws InterruptedException {
        lock.lock();
        try {
            while (queue.isEmpty()) notEmpty.await();  // wait until item
            T item = queue.poll();
            notFull.signal();   // wake one producer
            return item;
        } finally {
            lock.unlock();
        }
    }
}
```

**What this does:** Two `Condition` objects on the same lock allow producers and consumers to wait on separate conditions. With `synchronized`, only one condition (`Object.wait()`) is available. This is the key advantage of `ReentrantLock`.

---

## 3. ReadWriteLock / ReentrantReadWriteLock

Multiple threads can hold the read lock simultaneously, but the write lock is exclusive.

```
Read lock rules:
  Thread A (read)  ──┐
  Thread B (read)  ──┼── ALLOWED concurrently (no writer)
  Thread C (read)  ──┘

Write lock rules:
  Thread D (write) ── EXCLUSIVE — blocks all readers and other writers
                       must wait for all current readers to release
```

### State matrix

| State           | New read request | New write request |
|-----------------|-----------------|-------------------|
| No locks held   | Granted         | Granted           |
| Read lock(s)    | Granted         | Blocked           |
| Write lock held | Blocked         | Blocked           |

---

### Example 1 — Read-heavy cache

```java
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;
import java.util.HashMap;
import java.util.Map;

public class ReadWriteCache<K, V> {
    private final Map<K, V> map = new HashMap<>();
    private final ReadWriteLock rwLock = new ReentrantReadWriteLock();

    public V get(K key) {
        rwLock.readLock().lock();
        try {
            return map.get(key);    // many threads can read simultaneously
        } finally {
            rwLock.readLock().unlock();
        }
    }

    public void put(K key, V value) {
        rwLock.writeLock().lock();
        try {
            map.put(key, value);    // exclusive — no readers or writers during put
        } finally {
            rwLock.writeLock().unlock();
        }
    }
}
```

**What this does:** `get()` allows many concurrent readers — no blocking between read threads. `put()` blocks all readers and writers until write completes. Correct and fast for read-heavy workloads.

---

### Example 2 — Dry run: 3 readers vs 1 writer

```
Time →  0ms     50ms    100ms   150ms   200ms
T1 (read)   [==read==]
T2 (read)   [==read==]
T3 (read)   [==read==]
T4 (write)  BLOCKED BLOCKED [=write=]    <- waits for ALL readers to finish
T5 (read)   BLOCKED BLOCKED BLOCKED [==read==]  <- waits for write to finish

At 0ms: T1,T2,T3 all acquire readLock — concurrent OK
At 0ms: T4 requests writeLock — BLOCKED (readers active)
At 100ms: T1,T2,T3 release readLock — T4 unblocks, acquires writeLock
At 150ms: T4 releases writeLock — T5 unblocks, acquires readLock
```

---

### Example 3 — Lock downgrading (write → read)

```java
import java.util.concurrent.locks.ReentrantReadWriteLock;

public class LockDowngrade {
    private final ReentrantReadWriteLock rwl = new ReentrantReadWriteLock();
    private volatile boolean dataReady = false;
    private int data;

    public int readWithRefresh() {
        rwl.readLock().lock();
        if (!dataReady) {
            rwl.readLock().unlock();        // must release read before acquiring write
            rwl.writeLock().lock();
            try {
                if (!dataReady) {           // double-check
                    data = fetchData();
                    dataReady = true;
                }
                rwl.readLock().lock();      // acquire read BEFORE releasing write (downgrade)
            } finally {
                rwl.writeLock().unlock();   // release write — still hold read
            }
        }
        try {
            return data;
        } finally {
            rwl.readLock().unlock();
        }
    }

    private int fetchData() { return 42; }
}
```

**What this does:** Downgrade write lock to read lock by acquiring read while still holding write, then releasing write. Prevents another thread from modifying data between unlock-write and lock-read.

> ⚠️ **Pitfall:** Lock **upgrading** (read → write) is NOT supported. You must release the read lock before acquiring write. If two threads both hold read locks and both try to upgrade, deadlock occurs.

---

### Example 4 — getReadLockCount / isWriteLocked

```java
ReentrantReadWriteLock rwl = new ReentrantReadWriteLock();
rwl.readLock().lock();
System.out.println(rwl.getReadLockCount());   // 1
System.out.println(rwl.isWriteLocked());      // false
rwl.readLock().unlock();
```

**What this does:** Diagnostic methods — useful for logging, monitoring, or assertions in tests.

---

## 4. StampedLock [Java 8+]

Three modes: **optimistic read** (no lock, just a stamp — fastest), **read lock**, **write lock**.

```
Optimistic Read Pattern:
  stamp = tryOptimisticRead()   // no lock acquired, just get a stamp
  read shared data
  validate(stamp)               // true = no writer between stamp and now
    if false → data may be stale → fall back to real read lock
```

StampedLock is faster than `ReentrantReadWriteLock` for read-heavy because optimistic reads don't block writers and don't acquire any lock.

> ⚠️ **Pitfall:** `StampedLock` is **NOT reentrant**. Calling `writeLock()` from a thread that already holds a stamp causes deadlock. Do not use in recursive code.

---

### Example 1 — Optimistic read pattern

```java
import java.util.concurrent.locks.StampedLock;

public class Point {
    private double x, y;
    private final StampedLock sl = new StampedLock();

    public double distanceFromOrigin() {
        long stamp = sl.tryOptimisticRead();       // no lock — just stamp
        double currentX = x;
        double currentY = y;
        if (!sl.validate(stamp)) {                 // check: was data modified?
            stamp = sl.readLock();                 // fallback to real read lock
            try {
                currentX = x;
                currentY = y;
            } finally {
                sl.unlockRead(stamp);
            }
        }
        return Math.sqrt(currentX * currentX + currentY * currentY);
    }

    public void move(double deltaX, double deltaY) {
        long stamp = sl.writeLock();
        try {
            x += deltaX;
            y += deltaY;
        } finally {
            sl.unlockWrite(stamp);
        }
    }
}
```

**What this does:** `tryOptimisticRead()` returns a stamp without acquiring any lock. After reading `x` and `y`, `validate(stamp)` returns `true` only if no write happened since the stamp was issued. If a write occurred, fall back to a full read lock. Most reads succeed optimistically without ever acquiring a lock.

---

### Example 2 — Dry run: optimistic read with concurrent write

```
Scenario A — no writer intervenes:
  T1: stamp = tryOptimisticRead()   → stamp = 256
  T1: reads x=1.0, y=2.0
  T1: validate(256)                 → true (no write) → use x=1.0, y=2.0 ✓

Scenario B — writer intervenes:
  T1: stamp = tryOptimisticRead()   → stamp = 256
  T1: reads x=1.0                   (context switch)
  T2: writeLock() → changes x=5.0, y=6.0 → unlockWrite()
  T1: reads y=2.0                   (stale!)
  T1: validate(256)                 → false (write happened) → fall back to readLock
  T1: re-reads x=5.0, y=6.0        → correct ✓
```

---

### Example 3 — Write lock with StampedLock

```java
import java.util.concurrent.locks.StampedLock;

public class StampedWriteDemo {
    private int value = 0;
    private final StampedLock sl = new StampedLock();

    public void set(int v) {
        long stamp = sl.writeLock();
        try {
            value = v;
        } finally {
            sl.unlockWrite(stamp);
        }
    }

    public int get() {
        long stamp = sl.readLock();
        try {
            return value;
        } finally {
            sl.unlockRead(stamp);
        }
    }
}
```

**What this does:** Standard read/write lock usage with StampedLock. `stamp` is the token returned by lock acquisition and MUST be passed back to the corresponding unlock method.

---

### Example 4 — Converting read stamp to write stamp

```java
import java.util.concurrent.locks.StampedLock;

public class StampConvert {
    private double value = 0;
    private final StampedLock sl = new StampedLock();

    public void conditionalUpdate(double threshold) {
        long stamp = sl.readLock();
        try {
            while (value < threshold) {
                long ws = sl.tryConvertToWriteLock(stamp);  // atomic upgrade attempt
                if (ws != 0L) {
                    stamp = ws;             // conversion succeeded
                    value += 10;
                    break;
                } else {
                    sl.unlockRead(stamp);   // conversion failed, release and acquire write
                    stamp = sl.writeLock();
                }
            }
        } finally {
            sl.unlock(stamp);   // works for both read and write stamps
        }
    }
}
```

**What this does:** `tryConvertToWriteLock()` attempts atomic upgrade from read to write. Returns 0 if fails (other readers exist). `sl.unlock(stamp)` is a convenience that works for any stamp type.

---

## 5. ExecutorService

Manages a pool of threads. Decouples task submission from thread management.

```
         submit(task)
Client ──────────────► ExecutorService ──► Worker Thread 1
                           │           ──► Worker Thread 2
                       Task Queue      ──► Worker Thread 3
```

### Key Methods

| Method                                    | Description |
|-------------------------------------------|-------------|
| `execute(Runnable)`                       | Fire-and-forget, no return |
| `submit(Callable<T>) → Future<T>`         | Returns Future with result |
| `submit(Runnable) → Future<?>`            | Returns Future, result is null |
| `invokeAll(Collection<Callable<T>>)`      | Waits for ALL tasks, returns List<Future<T>> |
| `invokeAny(Collection<Callable<T>>) → T` | Returns first successful result, cancels rest |
| `shutdown()`                              | No new tasks; existing tasks run to completion |
| `shutdownNow()`                           | Interrupts running tasks; returns unstarted tasks |
| `awaitTermination(time, unit) → boolean`  | Blocks until terminated or timeout |
| `isShutdown()`                            | True after shutdown() called |
| `isTerminated()`                          | True when all tasks done after shutdown |

---

### Example 1 — execute vs submit

```java
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

ExecutorService pool = Executors.newFixedThreadPool(2);

// execute: fire-and-forget, exceptions swallowed (go to UncaughtExceptionHandler)
pool.execute(() -> System.out.println("Task via execute"));

// submit: returns Future — exceptions captured in Future, thrown on get()
Future<?> f = pool.submit(() -> System.out.println("Task via submit"));
f.get();  // blocks until done; re-throws exception if task threw

pool.shutdown();
```

**What this does:** `execute` swallows unchecked exceptions (only UncaughtExceptionHandler sees them). `submit` captures exceptions in the Future — `f.get()` rethrows them wrapped in `ExecutionException`. Prefer `submit` when you need error handling.

---

### Example 2 — invokeAll and invokeAny

```java
import java.util.List;
import java.util.Arrays;
import java.util.concurrent.*;

ExecutorService pool = Executors.newFixedThreadPool(3);

List<Callable<String>> tasks = Arrays.asList(
    () -> { Thread.sleep(100); return "Task A"; },
    () -> { Thread.sleep(200); return "Task B"; },
    () -> { Thread.sleep(50);  return "Task C"; }
);

// invokeAll — waits for ALL tasks
List<Future<String>> allResults = pool.invokeAll(tasks);
for (Future<String> f : allResults) {
    System.out.println(f.get());  // Task A, Task B, Task C (in submission order)
}

// invokeAny — returns first completed result
String first = pool.invokeAny(tasks);  // "Task C" (fastest — 50ms)
System.out.println("First done: " + first);

pool.shutdown();
```

**What this does:** `invokeAll` blocks until every task finishes, returning futures in submission order. `invokeAny` returns the first successful result and cancels all remaining tasks — useful for redundant queries (ask multiple servers, use first response).

---

### Example 3 — Proper shutdown pattern

```java
import java.util.concurrent.*;

public class ShutdownPattern {
    public static void shutdown(ExecutorService pool) {
        pool.shutdown();                                 // no new tasks
        try {
            if (!pool.awaitTermination(60, TimeUnit.SECONDS)) {
                pool.shutdownNow();                      // force-interrupt remaining
                if (!pool.awaitTermination(60, TimeUnit.SECONDS)) {
                    System.err.println("Pool did not terminate");
                }
            }
        } catch (InterruptedException e) {
            pool.shutdownNow();
            Thread.currentThread().interrupt();          // preserve interrupt status
        }
    }
}
```

**What this does:** Standard two-phase shutdown from Java documentation. `shutdown()` politely requests stop. `awaitTermination()` waits up to 60s. If still running, `shutdownNow()` interrupts threads. Restores interrupt flag if this thread itself is interrupted during wait.

> ⚠️ **Pitfall:** Calling `shutdown()` without `awaitTermination()` means the JVM may exit before tasks complete. Calling only `shutdownNow()` may interrupt tasks that need to finish cleanly. Always use the two-phase pattern.

---

### Example 4 — invokeAll with timeout

```java
List<Future<String>> futures = pool.invokeAll(tasks, 5, TimeUnit.SECONDS);
// Tasks that didn't finish in 5s are cancelled (future.isCancelled() == true)

for (Future<String> f : futures) {
    if (f.isCancelled()) {
        System.out.println("Task was cancelled (timed out)");
    } else {
        System.out.println(f.get());
    }
}
```

**What this does:** `invokeAll` with timeout cancels any task still running after 5 seconds. Already-completed tasks are unaffected.

---

## 6. Executors Factory Methods

### newFixedThreadPool(n)

```
n=3, 5 tasks submitted:
  [T1 T2 T3 | T4 T5 waiting in queue]
   active    queue (LinkedBlockingQueue, unbounded)

  T1 finishes → T4 dequeued and runs
  T2 finishes → T5 dequeued and runs
```

```java
ExecutorService fixed = Executors.newFixedThreadPool(4);
// 4 threads always alive, tasks queue up if all busy
// Use: CPU-bound tasks, limit parallelism to core count
```

---

### newCachedThreadPool()

```java
ExecutorService cached = Executors.newCachedThreadPool();
// Creates new threads as needed, reuses idle threads (idle timeout: 60s)
// 0 core threads, Integer.MAX_VALUE max — can create thousands of threads!
// Use: many short-lived tasks; DO NOT use for long-running tasks
```

> ⚠️ **Pitfall:** `newCachedThreadPool()` with slow tasks creates unbounded threads, exhausting memory/file-descriptors. Only safe when tasks are short (< few seconds).

---

### newSingleThreadExecutor()

```java
ExecutorService single = Executors.newSingleThreadExecutor();
// Single thread, unbounded queue — tasks run sequentially in submission order
// If thread dies from exception, a new one is created to replace it
// Use: ordered processing, event loop style
```

---

### newScheduledThreadPool(n)

```java
import java.util.concurrent.*;

ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(2);

// Run once after delay
scheduler.schedule(() -> System.out.println("delayed"), 5, TimeUnit.SECONDS);

// Run repeatedly: initial delay 1s, then every 3s
scheduler.scheduleAtFixedRate(
    () -> System.out.println("periodic"),
    1, 3, TimeUnit.SECONDS
);

// Run repeatedly: 3s gap BETWEEN completions (not start times)
scheduler.scheduleWithFixedDelay(
    () -> System.out.println("with-delay"),
    1, 3, TimeUnit.SECONDS
);
```

**What this does:** `scheduleAtFixedRate` triggers at fixed clock intervals regardless of task duration. `scheduleWithFixedDelay` waits fixed time after previous task completes — safer if task can take longer than the interval.

---

### ThreadPoolExecutor — Full Control

```java
import java.util.concurrent.*;

ThreadPoolExecutor executor = new ThreadPoolExecutor(
    2,                              // corePoolSize: threads always alive
    10,                             // maximumPoolSize: max threads
    60L, TimeUnit.SECONDS,          // keepAliveTime: idle non-core thread TTL
    new ArrayBlockingQueue<>(100),  // workQueue: bounded queue
    Executors.defaultThreadFactory(),
    new ThreadPoolExecutor.CallerRunsPolicy()  // rejection policy
);
```

**Thread creation logic:**

```
submit(task):
  activeThreads < corePoolSize?   → create new thread
  queue not full?                 → enqueue task
  activeThreads < maxPoolSize?    → create new thread
  else → RejectionHandler
```

**Rejection policies:**

| Policy              | Behavior |
|--------------------|----------|
| `AbortPolicy`       | Throws `RejectedExecutionException` (default) |
| `CallerRunsPolicy`  | Caller thread runs the task (backpressure) |
| `DiscardPolicy`     | Silently discards task |
| `DiscardOldestPolicy` | Discards oldest queued task, retries submit |

> ⚠️ **Pitfall:** With `LinkedBlockingQueue` (unbounded), `maximumPoolSize` is NEVER used — queue never fills, so extra threads are never created. Use `ArrayBlockingQueue` (bounded) to make `maximumPoolSize` meaningful.

---

## 7. Future\<T\>

Represents the result of an asynchronous computation.

### Key Methods

| Method                        | Description |
|-------------------------------|-------------|
| `get()`                       | Blocks until result available |
| `get(timeout, unit)`          | Blocks up to timeout, throws `TimeoutException` |
| `cancel(mayInterruptIfRunning)` | Attempts to cancel; returns false if already done |
| `isCancelled()`               | True if cancelled before completion |
| `isDone()`                    | True if completed (normally, exceptionally, or cancelled) |

---

### Example 1 — Basic get()

```java
import java.util.concurrent.*;

ExecutorService pool = Executors.newFixedThreadPool(2);

Future<Integer> future = pool.submit(() -> {
    Thread.sleep(1000);
    return 42;
});

System.out.println("Doing other work...");
Integer result = future.get();  // BLOCKS here until result ready
System.out.println("Result: " + result);  // Result: 42
pool.shutdown();
```

**What this does:** `submit` returns immediately with a `Future`. Main thread does other work. `get()` blocks until the callable finishes. Exceptions from the callable are wrapped in `ExecutionException` and thrown from `get()`.

---

### Example 2 — get with timeout + cancel

```java
Future<String> f = pool.submit(() -> {
    Thread.sleep(5000);
    return "done";
});

try {
    String result = f.get(2, TimeUnit.SECONDS);  // wait only 2s
} catch (TimeoutException e) {
    System.out.println("Took too long — cancelling");
    f.cancel(true);   // true = interrupt the running thread
    System.out.println("Cancelled: " + f.isCancelled());  // true
}
```

**What this does:** Limits wait to 2 seconds. If task doesn't finish, cancel it. `cancel(true)` sends interrupt to the worker thread — task must check `Thread.isInterrupted()` or use interruptible operations (`sleep`, `wait`, `lock`) to actually stop.

---

### Example 3 — Exception handling from Future

```java
Future<Integer> f = pool.submit(() -> {
    if (true) throw new RuntimeException("task failed");
    return 1;
});

try {
    f.get();
} catch (ExecutionException e) {
    System.out.println("Task threw: " + e.getCause().getMessage()); // task failed
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
}
```

**What this does:** `ExecutionException` wraps the original exception. Always call `getCause()` to get the actual task exception.

---

### Example 4 — isDone polling (non-blocking check)

```java
Future<String> f = pool.submit(() -> { Thread.sleep(500); return "result"; });

while (!f.isDone()) {
    System.out.println("Not done yet, doing other work...");
    Thread.sleep(100);
}
System.out.println(f.get());  // won't block — already done
```

**What this does:** Polling with `isDone()` avoids blocking. When `isDone()` is true, `get()` returns immediately.

### Limitations of Future — why CompletableFuture was introduced

| Limitation | Impact |
|------------|--------|
| `get()` blocks                    | Can't chain without blocking |
| No callback support               | Must poll or block |
| Can't combine multiple futures    | No `waitForAll` equivalent |
| Can't chain transformations       | Must call `get()` then transform |
| Can't manually complete           | Can't use for callback-based APIs |

---

## 8. Callable\<T\>

Like `Runnable` but: returns a value, can throw checked exceptions.

```
Runnable:  void run()            — no return, no checked exception
Callable:  V    call() throws Exception — returns V, can throw
```

### Example 1 — Callable basics

```java
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

Callable<String> task = () -> {
    Thread.sleep(100);
    return "Hello from Callable";
};

ExecutorService pool = Executors.newSingleThreadExecutor();
Future<String> future = pool.submit(task);
System.out.println(future.get());  // Hello from Callable
pool.shutdown();
```

**What this does:** Callable lambda infers return type from `Callable<String>`. `submit` accepts Callable and returns a typed `Future<String>`.

---

### Example 2 — Callable throwing checked exception

```java
Callable<Integer> riskyTask = () -> {
    if (Math.random() < 0.5) throw new Exception("Random failure");
    return 100;
};

Future<Integer> f = pool.submit(riskyTask);
try {
    System.out.println(f.get());
} catch (ExecutionException e) {
    System.out.println("Caught: " + e.getCause().getMessage());
}
```

**What this does:** Callable's `call()` declares `throws Exception`, so checked exceptions are legal. They're wrapped in `ExecutionException` by the executor and rethrown from `get()`.

---

### Example 3 — Multiple Callables with invokeAll

```java
import java.util.List;
import java.util.Arrays;
import java.util.concurrent.*;

ExecutorService pool = Executors.newFixedThreadPool(3);

List<Callable<Integer>> tasks = Arrays.asList(
    () -> 1 + 1,
    () -> 2 + 2,
    () -> 3 + 3
);

List<Future<Integer>> results = pool.invokeAll(tasks);
for (Future<Integer> r : results) {
    System.out.println(r.get());  // 2, 4, 6
}
pool.shutdown();
```

**What this does:** All three Callables run in parallel (pool has 3 threads). `invokeAll` returns futures in submission order after all complete.

---

### Example 4 — Callable vs Runnable for error handling

```java
ExecutorService pool = Executors.newFixedThreadPool(1);

// Runnable — exception disappears (no Future to catch it)
pool.execute(() -> {
    throw new RuntimeException("lost exception");  // goes to UncaughtExceptionHandler only
});

// Callable — exception captured in Future
Future<Void> f = pool.submit((Callable<Void>) () -> {
    throw new RuntimeException("captured exception");
});
try {
    f.get();  // throws ExecutionException wrapping RuntimeException
} catch (ExecutionException e) {
    System.out.println("Got it: " + e.getCause().getMessage()); // captured exception
}
pool.shutdown();
```

**What this does:** Key practical difference — `execute(Runnable)` silently swallows exceptions unless you set an `UncaughtExceptionHandler`. `submit(Callable)` stores the exception in the Future. Always prefer `submit` for tasks where exception handling matters.

> ⚠️ **Pitfall:** `submit(Runnable)` (not Callable) also captures exceptions in the Future, but `future.get()` returns `null` on success. The exception IS captured — don't use `execute` when you care about errors.
