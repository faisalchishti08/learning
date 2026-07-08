---
card: java
gi: 407
slug: condition-objects
title: Condition objects
---

## 1. What it is

A `Condition` (from `java.util.concurrent.locks`) is the `Lock`-based replacement for `Object.wait()`/`notify()`/`notifyAll()`. You create one from a `Lock` via `lock.newCondition()`, then call `condition.await()` to release the lock and block until signalled, and `condition.signal()`/`signalAll()` to wake up one or all waiting threads. The key advantage over the built-in `wait`/`notify`: a single `Lock` can have **multiple** `Condition`s, each representing a distinct wait scenario, rather than being limited to one wait-set per monitor.

## 2. Why & when

`wait()`/`notify()` (used with `synchronized`) give you exactly one wait condition per object — if a bounded buffer needs to make producer threads wait for "not full" and consumer threads wait for "not empty," both have to share the same wait-set, so `notify()` can wake up the wrong kind of thread (a consumer notifying when it should wake a producer, but instead waking another consumer, which finds nothing to do and goes back to waiting — wasted wake-ups, or in the worst case, missed signals under complex conditions).

`Condition` objects fix this directly: create one `Condition` per distinct wait scenario from the same `Lock` (e.g. `notFull` and `notEmpty`), and `signal()` on the *specific* condition that's now true, waking only the threads actually waiting for that condition. You reach for `Condition` any time you're implementing a custom concurrent data structure (a bounded buffer, a custom barrier, a producer-consumer queue) with more than one distinct "wait until X" scenario — which is exactly the situation `BlockingQueue` already solves internally using this same mechanism.

## 3. Core concept

```java
import java.util.concurrent.locks.*;

Lock lock = new ReentrantLock();
Condition notEmpty = lock.newCondition(); // consumers wait on THIS when the buffer is empty
Condition notFull = lock.newCondition();  // producers wait on THIS when the buffer is full

lock.lock();
try {
    while (bufferIsEmpty()) {
        notEmpty.await(); // releases the lock, blocks, re-acquires the lock automatically once signalled
    }
    // ... take an item ...
    notFull.signal(); // wake ONE producer waiting for "not full", since we just freed a slot
} finally {
    lock.unlock();
}
```

The `while` loop (not `if`) around `await()` is essential: a thread woken by `signal()` must **re-check** the condition, because by the time it re-acquires the lock, another thread might have already changed things again (a "spurious wakeup" or a race won by a different thread).

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One Lock with two separate Conditions: notEmpty for consumers waiting on an empty buffer, notFull for producers waiting on a full buffer">
  <rect x="8" y="8" width="624" height="194" rx="8" fill="#0d1117"/>
  <rect x="240" y="15" width="160" height="34" rx="6" fill="#1c2430" stroke="#e6edf3"/>
  <text x="320" y="37" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Lock (bounded buffer)</text>

  <rect x="40" y="80" width="200" height="44" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="140" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Condition: notEmpty</text>
  <text x="140" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">consumers await() here</text>

  <rect x="400" y="80" width="200" height="44" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="500" y="100" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Condition: notFull</text>
  <text x="500" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">producers await() here</text>

  <line x1="320" y1="49" x2="140" y2="80" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="320" y1="49" x2="500" y2="80" stroke="#8b949e" stroke-dasharray="3,2"/>

  <text x="140" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">producer calls notEmpty.signal()</text>
  <text x="500" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">consumer calls notFull.signal()</text>
  <text x="320" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Each side wakes only the threads actually waiting for ITS specific condition.</text>
</svg>

Two independent wait-sets on one lock — signalling one never disturbs threads waiting on the other.

## 5. Runnable example

Scenario: implementing a small bounded buffer from scratch (the same job a `BlockingQueue` does internally) — the same buffer, evolved from a single-condition version that wakes the wrong kind of thread, through the correct two-condition producer/consumer split, to a version using a timed `awaitNanos` to avoid waiting forever, plus `signalAll` for correctness with multiple waiters.

### Level 1 — Basic

```java
import java.util.concurrent.locks.*;
import java.util.LinkedList;

public class BoundedBufferOneCondition {
    static final int CAPACITY = 3;
    static final LinkedList<Integer> buffer = new LinkedList<>();
    static final Lock lock = new ReentrantLock();
    static final Condition changed = lock.newCondition(); // ONE condition shared by producer AND consumer

    static void put(int value) throws InterruptedException {
        lock.lock();
        try {
            while (buffer.size() == CAPACITY) changed.await(); // waits for ANY change, not specifically "not full"
            buffer.add(value);
            System.out.println("Put " + value + " (size=" + buffer.size() + ")");
            changed.signalAll(); // must wake everyone, since we don't know who's actually interested
        } finally {
            lock.unlock();
        }
    }

    static int take() throws InterruptedException {
        lock.lock();
        try {
            while (buffer.isEmpty()) changed.await();
            int value = buffer.removeFirst();
            System.out.println("Took " + value + " (size=" + buffer.size() + ")");
            changed.signalAll();
            return value;
        } finally {
            lock.unlock();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        for (int i = 1; i <= 5; i++) put(i > CAPACITY ? i : i); // fill past capacity would block -- kept small here
        for (int i = 1; i <= 3; i++) take();
    }
}
```

**How to run:** `java BoundedBufferOneCondition.java`

With only one shared `Condition`, every `signalAll()` must wake **every** waiting thread (producers and consumers alike), even though only one specific kind actually has anything useful to do — this works correctly but wastes wake-ups under real concurrent load, since woken threads that find their condition still false just go straight back to waiting.

### Level 2 — Intermediate

```java
import java.util.concurrent.locks.*;
import java.util.LinkedList;

public class BoundedBufferTwoConditions {
    static final int CAPACITY = 3;
    static final LinkedList<Integer> buffer = new LinkedList<>();
    static final Lock lock = new ReentrantLock();
    static final Condition notFull = lock.newCondition();  // producers wait HERE
    static final Condition notEmpty = lock.newCondition(); // consumers wait HERE

    static void put(int value) throws InterruptedException {
        lock.lock();
        try {
            while (buffer.size() == CAPACITY) notFull.await();
            buffer.add(value);
            System.out.println("Put " + value + " (size=" + buffer.size() + ")");
            notEmpty.signal(); // wake ONE consumer -- we just added something for it to take
        } finally {
            lock.unlock();
        }
    }

    static int take() throws InterruptedException {
        lock.lock();
        try {
            while (buffer.isEmpty()) notEmpty.await();
            int value = buffer.removeFirst();
            System.out.println("Took " + value + " (size=" + buffer.size() + ")");
            notFull.signal(); // wake ONE producer -- we just freed a slot
            return value;
        } finally {
            lock.unlock();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread producer = new Thread(() -> {
            try { for (int i = 1; i <= 5; i++) put(i); } catch (InterruptedException ignored) { }
        });
        Thread consumer = new Thread(() -> {
            try { for (int i = 1; i <= 5; i++) take(); } catch (InterruptedException ignored) { }
        });
        producer.start(); consumer.start();
        producer.join(); consumer.join();
    }
}
```

**How to run:** `java BoundedBufferTwoConditions.java`

Splitting into `notFull` and `notEmpty` (both created from the *same* `lock`) means each `signal()` targets exactly the kind of thread that can actually make progress — a producer signals `notEmpty` (only consumers wait there), a consumer signals `notFull` (only producers wait there) — no wasted wake-ups, and the producer/consumer pair now runs concurrently rather than sequentially.

### Level 3 — Advanced

```java
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.*;
import java.util.LinkedList;

public class BoundedBufferTimedAwait {
    static final int CAPACITY = 2;
    static final LinkedList<Integer> buffer = new LinkedList<>();
    static final Lock lock = new ReentrantLock();
    static final Condition notFull = lock.newCondition();
    static final Condition notEmpty = lock.newCondition();

    static boolean put(int value, long timeoutMs) throws InterruptedException {
        lock.lock();
        try {
            long remaining = TimeUnit.MILLISECONDS.toNanos(timeoutMs);
            while (buffer.size() == CAPACITY) {
                if (remaining <= 0) return false; // gave up waiting -- buffer stayed full too long
                remaining = notFull.awaitNanos(remaining); // returns remaining time, re-check the loop condition
            }
            buffer.add(value);
            System.out.println("Put " + value + " (size=" + buffer.size() + ")");
            notEmpty.signalAll(); // signalAll: safe default when multiple consumers might be waiting
            return true;
        } finally {
            lock.unlock();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        put(1, 100); // succeeds: buffer empty
        put(2, 100); // succeeds: buffer now at capacity (2)
        boolean thirdSucceeded = put(3, 200); // buffer full, nobody consuming -- times out
        System.out.println("Third put succeeded: " + thirdSucceeded);
    }
}
```

**How to run:** `java BoundedBufferTimedAwait.java`

`notFull.awaitNanos(remaining)` waits for at most the given time and returns how much time was left — using it in a loop lets a producer give up gracefully after a bounded total wait, instead of blocking forever if no consumer ever shows up to free a slot. `signalAll()` (rather than `signal()`) is the safer default whenever more than one thread might legitimately be waiting on the same condition — `signal()` only guarantees waking *one*, which is fine if exactly one waiter can make use of it, but risky otherwise.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example, with an empty buffer of capacity 2.

`put(1, 100)`: acquires `lock`. The `while (buffer.size() == CAPACITY)` check is `false` (buffer is empty, capacity is 2), so the loop body never runs — no waiting needed. `buffer.add(1)` makes the buffer `[1]`, prints `"Put 1 (size=1)"`, and `notEmpty.signalAll()` runs — but since no thread is currently waiting on `notEmpty` (there's no consumer thread in this example), this signal has no effect; it's harmless to call even with no waiters. `lock.unlock()` releases the lock.

`put(2, 100)`: same path — `buffer.size()` is 1, not yet at capacity 2, so no wait occurs. `buffer.add(2)` makes the buffer `[1, 2]`, prints `"Put 2 (size=2)"`.

`put(3, 200)`: now `buffer.size() == CAPACITY` (2 == 2) is `true`, so the `while` loop body executes. `remaining` starts as 200ms converted to nanoseconds. `notFull.awaitNanos(remaining)` releases `lock` and blocks — but since there is no consumer thread ever calling `take()` in this example, nothing will ever call `notFull.signal()`/`signalAll()` to wake it early, so `awaitNanos` simply times out after the requested duration and returns a value ≤ 0 (or very close to it) representing however much time was left (essentially none). Back in the loop, `remaining` is updated to this near-zero value; the `while` condition is re-checked — `buffer.size() == CAPACITY` is still `true` (nothing removed anything) — so the loop checks `if (remaining <= 0) return false;`, which is now `true`, and `put` returns `false` without ever adding the third value.

`main` prints the result: since `put(3, 200)` returned `false`, `"Third put succeeded: false"` is printed, correctly reflecting that the buffer stayed full for the entire timeout with no consumer ever freeing a slot.

Expected output:
```
Put 1 (size=1)
Put 2 (size=2)
Third put succeeded: false
```

## 7. Gotchas & takeaways

> Always call `await()` (or `awaitNanos`) inside a **`while` loop** that re-checks the actual condition, never an `if`. A thread can wake from `await()` for reasons other than "the condition I care about is now true" (spurious wakeups, or another thread winning a race to consume the thing you were waiting for) — re-checking in a loop is the only way to be safe.

- `Condition` is the `Lock`-based replacement for `Object.wait()`/`notify()`/`notifyAll()`, created via `lock.newCondition()`.
- A single `Lock` can back multiple independent `Condition`s — each representing a distinct "wait until X" scenario, so signalling one never disturbs threads waiting on another.
- `signal()` wakes exactly one waiting thread; `signalAll()` wakes all of them — prefer `signalAll()` unless you're certain only one waiter can ever usefully proceed.
- `awaitNanos(nanos)` (and the `await(time, unit)` overload) let a thread give up waiting after a bounded time, returning how much time remains so a caller can retry in a loop with a shrinking budget.
- This exact producer/consumer, two-condition pattern is what `ArrayBlockingQueue`/`LinkedBlockingQueue` implement internally — understanding `Condition` demystifies how those classes work under the hood.
