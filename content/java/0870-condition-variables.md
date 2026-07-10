---
card: java
gi: 870
slug: condition-variables
title: Condition variables
---

## 1. What it is

A **condition variable**, in Java represented by `java.util.concurrent.locks.Condition` (obtained from a `Lock` via `lock.newCondition()`), lets a thread that holds a lock release it and go to sleep until some other thread signals that a condition it's waiting for might now be true — then reacquires the lock automatically before waking up. It's the explicit-lock equivalent of an object's built-in `wait()`/`notify()`/`notifyAll()` methods, but with the crucial improvement that a single `Lock` can have **multiple** independent `Condition`s, each representing a different thing threads might be waiting for (e.g., "queue not empty" versus "queue not full"), instead of the single, undifferentiated wait-set every plain object monitor has.

## 2. Why & when

Use a condition variable whenever a thread needs to block until some state change happens that it cannot busy-wait for efficiently — a bounded queue that's full (producers must wait) or empty (consumers must wait), a connection pool with no free connections, a barrier waiting for N threads to arrive. The key discipline is always waiting in a **loop**, re-checking the actual condition after waking up, never assuming a single `await()` return means the condition is now true — a **spurious wakeup** (the thread waking up without any real signal, which the JVM is explicitly permitted to do) or another thread beating you to the resource after being signaled are both legitimate reasons the condition might still be false when you wake up. Prefer condition variables over ad hoc polling loops with `Thread.sleep` — polling wastes CPU and adds latency, while a proper `await()`/`signal()` pair wakes exactly when (and shortly after) the state actually changes.

## 3. Core concept

```java
Lock lock = new ReentrantLock();
Condition notEmpty = lock.newCondition();
Queue<Integer> queue = new LinkedList<>();

void put(int value) {
    lock.lock();
    try {
        queue.add(value);
        notEmpty.signal(); // wake ONE waiting consumer (if any)
    } finally { lock.unlock(); }
}

int take() throws InterruptedException {
    lock.lock();
    try {
        while (queue.isEmpty()) {      // ALWAYS a loop, never `if`
            notEmpty.await();           // releases lock, sleeps, reacquires lock before returning
        }
        return queue.poll();
    } finally { lock.unlock(); }
}
```

`await()` atomically releases the lock and suspends the thread; when signaled (or spuriously woken), it reacquires the lock before returning — the `while` loop then re-checks the actual condition rather than trusting the wakeup itself.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A consumer thread awaits on an empty-queue condition, releasing the lock while waiting; a producer adds an item, signals, and the consumer reacquires the lock and rechecks before proceeding">
  <rect x="20" y="20" width="260" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Consumer: queue empty -&gt; await() (releases lock)</text>

  <rect x="330" y="20" width="280" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Producer: acquires lock, adds item, signal()</text>

  <rect x="20" y="90" width="260" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="150" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Consumer wakes, REACQUIRES lock</text>

  <rect x="20" y="150" width="260" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="175" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">while-loop re-checks: queue not empty -&gt; proceed</text>

  <line x1="150" y1="60" x2="150" y2="88" stroke="#8b949e" stroke-width="2" stroke-dasharray="4"/>
  <line x1="470" y1="60" x2="150" y2="105" stroke="#6db33f" stroke-width="2" marker-end="url(#a8)"/>
  <line x1="150" y1="130" x2="150" y2="148" stroke="#8b949e" stroke-width="2" marker-end="url(#a8)"/>
  <defs><marker id="a8" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*`await()` releases the lock while sleeping; `signal()` wakes the consumer, which reacquires the lock and re-checks the actual condition before proceeding.*

## 5. Runnable example

Scenario: a small bounded blocking queue, growing from a broken busy-wait/polling version, to a correct single-condition `await`/`signal` version, to a full producer–consumer with two separate conditions (not-empty and not-full) so producers and consumers each wait on exactly the condition relevant to them.

### Level 1 — Basic

```java
public class BusyWaitQueue {
    static class Box {
        private Integer value = null;
        boolean hasValue() { return value != null; }

        void put(int v) {
            synchronized (this) { value = v; }
        }

        int take() throws InterruptedException {
            while (!hasValue()) {
                Thread.sleep(1); // POLLING -- wastes CPU, adds up to 1ms latency
            }
            synchronized (this) {
                int v = value;
                value = null;
                return v;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Box box = new Box();
        Thread consumer = new Thread(() -> {
            try {
                System.out.println("consumed: " + box.take());
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        consumer.start();
        Thread.sleep(20);
        box.put(42);
        consumer.join();
    }
}
```

**How to run:** `java BusyWaitQueue.java` (JDK 17+).

Expected output:
```
consumed: 42
```

Works, but the consumer burns CPU cycles continuously polling `hasValue()` every millisecond instead of truly sleeping until data is ready — wasteful and adds unnecessary latency.

### Level 2 — Intermediate

```java
import java.util.concurrent.locks.*;

public class ConditionAwaitSignal {
    static class Box {
        private final Lock lock = new ReentrantLock();
        private final Condition hasValue = lock.newCondition();
        private Integer value = null;

        void put(int v) {
            lock.lock();
            try {
                value = v;
                hasValue.signal(); // wake a waiting consumer, if any
            } finally { lock.unlock(); }
        }

        int take() throws InterruptedException {
            lock.lock();
            try {
                while (value == null) { // loop, not if -- guards against spurious wakeups
                    hasValue.await(); // releases lock while waiting, reacquires before returning
                }
                int v = value;
                value = null;
                return v;
            } finally { lock.unlock(); }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Box box = new Box();
        Thread consumer = new Thread(() -> {
            try {
                System.out.println("consumed: " + box.take() + " (woke via signal, not polling)");
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        consumer.start();
        Thread.sleep(20);
        box.put(42);
        consumer.join();
    }
}
```

**How to run:** `java ConditionAwaitSignal.java`.

Expected output:
```
consumed: 42 (woke via signal, not polling)
```

The real-world concern added: the consumer truly sleeps (no CPU spinning) via `hasValue.await()`, waking only when `put` calls `hasValue.signal()` — and it still re-checks `value == null` in a `while` loop after waking, correctly handling the theoretical case of a spurious wakeup or another consumer having already claimed the value.

### Level 3 — Advanced

```java
import java.util.concurrent.locks.*;
import java.util.*;
import java.util.concurrent.*;

public class TwoConditionBoundedQueue {
    static class BoundedQueue {
        private final Lock lock = new ReentrantLock();
        private final Condition notEmpty = lock.newCondition(); // consumers wait here
        private final Condition notFull = lock.newCondition();  // producers wait here
        private final Queue<Integer> queue = new LinkedList<>();
        private final int capacity;

        BoundedQueue(int capacity) { this.capacity = capacity; }

        void put(int value) throws InterruptedException {
            lock.lock();
            try {
                while (queue.size() == capacity) {
                    notFull.await(); // producer waits on its OWN condition, not notEmpty
                }
                queue.add(value);
                notEmpty.signal(); // wake a consumer specifically
            } finally { lock.unlock(); }
        }

        int take() throws InterruptedException {
            lock.lock();
            try {
                while (queue.isEmpty()) {
                    notEmpty.await(); // consumer waits on ITS own condition
                }
                int v = queue.poll();
                notFull.signal(); // wake a producer specifically -- there's now room
                return v;
            } finally { lock.unlock(); }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        BoundedQueue q = new BoundedQueue(2); // capacity of 2 -- forces producers to wait
        ExecutorService pool = Executors.newFixedThreadPool(2);

        pool.submit(() -> {
            try {
                for (int i = 1; i <= 5; i++) {
                    q.put(i);
                    System.out.println("produced " + i);
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        pool.submit(() -> {
            try {
                for (int i = 1; i <= 5; i++) {
                    Thread.sleep(30); // consume slower than production, to force capacity waits
                    System.out.println("consumed " + q.take());
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("done -- producers correctly waited on notFull when the queue hit capacity 2");
    }
}
```

**How to run:** `java TwoConditionBoundedQueue.java`.

Expected output shape (interleaving of "produced"/"consumed" lines varies, but all five of each print, in order within each role):
```
produced 1
produced 2
consumed 1
produced 3
consumed 2
produced 4
consumed 3
produced 5
consumed 4
consumed 5
done -- producers correctly waited on notFull when the queue hit capacity 2
```

This adds the production-flavored hard case: two independent conditions sharing the same lock, each representing a different thing a thread might be waiting for. A producer waiting on `notFull` is only ever woken by a consumer's `notFull.signal()` (never by another producer's `signal()` on `notEmpty`), and vice versa — this targeted signaling avoids the "thundering herd" problem of using a single condition (and hence `signalAll()`) for two logically distinct wake-up reasons.

## 6. Walkthrough

Tracing the bounded queue reaching capacity:

1. The producer calls `put(3)` after the queue already holds `{1, 2}` (capacity 2). It acquires `lock`, finds `queue.size() == capacity` true, and calls `notFull.await()` — this atomically releases `lock` and suspends the producer thread.
2. The consumer, running concurrently, calls `take()`, acquires the now-free `lock`, finds the queue non-empty, polls off `1`, and calls `notFull.signal()` — this wakes the producer that was suspended in step 1 (or would wake one if multiple were waiting), but does **not** yet let it proceed, since the woken thread must first reacquire `lock`, which the consumer still holds until it releases it in `finally`.
3. Once the consumer's `take()` call finishes (releasing `lock`), the producer's `await()` call reacquires `lock` and returns, re-entering its `while (queue.size() == capacity)` loop — this time finding `queue.size() == 1 < capacity`, so it exits the loop and proceeds to `queue.add(3)`, then calls `notEmpty.signal()` in case a consumer is waiting on that condition.
4. This exact request/response-style handoff repeats for the remaining values, with producers occasionally blocking on `notFull` (since the consumer sleeps 30ms between takes, letting the producer race ahead and fill the two-slot buffer) and consumers occasionally blocking on `notEmpty` (briefly, right after taking the last item, before the next `put`).
5. By the end, all five values have been produced and consumed exactly once each, in FIFO order (since the underlying `LinkedList` used as `queue` preserves insertion order), and the final `println` confirms the whole exchange completed without deadlock or lost signals.

## 7. Gotchas & takeaways

> **Gotcha:** always call `await()` inside a `while` loop that re-checks the actual condition, never inside an `if`. Both spurious wakeups (permitted by the JVM with no real signal at all) and "stolen" signals (another thread reacquiring the lock and consuming the resource before the woken thread gets its turn) mean the condition you were waiting for might still be false the moment `await()` returns.

- A single `Lock` can have multiple independent `Condition`s — use separate conditions for logically distinct wait reasons (like "not empty" vs. "not full") so a `signal()` wakes only threads that could plausibly proceed.
- `await()` atomically releases the lock while suspending and reacquires it before returning — you never manually juggle lock release/reacquire around a wait.
- Prefer `signal()` (wakes one waiter) over `signalAll()` (wakes every waiter) when only one waiting thread can actually make progress, to avoid a thundering-herd of threads all waking up, reacquiring the lock one at a time, and finding the condition still false for all but one of them.
- `Condition` is the explicit-lock analogue of `Object.wait()`/`notify()`/`notifyAll()` — the same "always loop, never assume" discipline applies to both.
- For many common producer–consumer patterns, `java.util.concurrent`'s ready-made blocking queues (`ArrayBlockingQueue`, `LinkedBlockingQueue`) already implement exactly this kind of condition-variable coordination internally — reach for those before hand-rolling your own unless you need custom wake conditions.
