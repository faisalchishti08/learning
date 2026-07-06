---
card: java
gi: 322
slug: wait-notify-notifyall-coordination
title: wait / notify / notifyAll coordination
---

## 1. What it is

`wait()`, `notify()`, and `notifyAll()` are methods on every Java object (inherited from `Object`) used for threads to coordinate around a shared condition. A thread calls `wait()` inside a `synchronized` block to release the lock and pause until another thread calls `notify()` (wakes one waiting thread) or `notifyAll()` (wakes all waiting threads) on that same object.

```java
public class WaitNotifyDemo {
    static final Object lock = new Object();
    static boolean ready = false;

    public static void main(String[] args) throws InterruptedException {
        Thread waiter = new Thread(() -> {
            synchronized (lock) {
                while (!ready) {
                    try { lock.wait(); } catch (InterruptedException e) { return; }
                }
                System.out.println("Waiter: condition became true, proceeding.");
            }
        });
        waiter.start();

        Thread.sleep(300); // let the waiter start waiting first
        synchronized (lock) {
            ready = true;
            lock.notify(); // wake the waiting thread
        }
        waiter.join();
    }
}
```

`lock.wait()` must be called while holding `lock`'s monitor (inside a `synchronized (lock)` block) — it releases that lock and blocks the calling thread until another thread calls `lock.notify()`/`lock.notifyAll()` on the same object, at which point the waiting thread re-acquires the lock before continuing.

## 2. Why & when

Sometimes a thread needs to wait for some condition to become true before it can proceed, and simply looping and re-checking that condition repeatedly (a technique called "busy-waiting" or "spinning") wastes CPU. `wait`/`notify` let a thread sleep efficiently — consuming no CPU at all — until specifically woken up by another thread that changed the relevant condition.

- **Producer/consumer coordination** — a consumer thread waits until a producer thread has data ready, without spinning in a tight loop checking a flag over and over.
- **Efficient blocking** — unlike `Thread.sleep` (which wakes up unconditionally after a fixed time regardless of whether anything relevant changed), `wait()` only wakes when explicitly notified (or interrupted), making it the right tool when a thread genuinely doesn't know how long it will need to wait.
- **Building blocking data structures** — classic bounded queues and similar structures use `wait`/`notify` internally to block producers when full and consumers when empty.

Always call `wait()` inside a loop checking the actual condition (`while (!ready) lock.wait();`, not `if (!ready) lock.wait();`) — a thread can wake up from `wait()` for reasons other than the condition actually being true (a "spurious wakeup," or another thread's notification about an unrelated condition change), so re-checking after waking is mandatory, not optional. Modern code often prefers higher-level `java.util.concurrent` tools (`BlockingQueue`, `CountDownLatch`, `Condition`) over raw `wait`/`notify`, since those tools handle many of `wait`/`notify`'s subtle correctness requirements for you — but understanding this mechanism is foundational to understanding what those higher-level tools do internally.

## 3. Core concept

```java
public class WaitNotifyCore {
    static final Object lock = new Object();
    static int sharedValue = 0;
    static boolean valueReady = false;

    public static void main(String[] args) throws InterruptedException {
        Thread consumer = new Thread(() -> {
            synchronized (lock) {
                while (!valueReady) { // loop, not a single if -- guards against spurious wakeups
                    try { lock.wait(); } catch (InterruptedException e) { return; }
                }
                System.out.println("Consumer read: " + sharedValue);
            }
        });
        consumer.start();

        synchronized (lock) {
            sharedValue = 42;
            valueReady = true;
            lock.notifyAll(); // wake ALL waiting threads (here, just the one consumer)
        }
        consumer.join();
    }
}
```

`notifyAll()` wakes every thread currently waiting on `lock` (here, just the one `consumer`), each of which then re-acquires the lock (one at a time) and re-checks its `while` condition — the consumer's loop condition, `!valueReady`, is now `false`, so it exits the loop and proceeds to read `sharedValue`, which is guaranteed to be `42` since both writes happened before the `notifyAll()` inside the same synchronized block.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A waiting thread releases the lock while blocked in wait, then reacquires it upon being notified and rechecking its condition">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10" font-family="monospace">Consumer: synchronized(lock){ while(!ready) lock.wait(); ... }</text>
  <text x="20" y="55" fill="#8b949e" font-size="9">wait() releases the lock and blocks -- lock is FREE for others while waiting</text>
  <text x="20" y="90" fill="#6db33f" font-size="10" font-family="monospace">Producer: synchronized(lock){ ready=true; lock.notifyAll(); }</text>
  <text x="20" y="115" fill="#8b949e" font-size="9">notifyAll() wakes waiters; each must RE-ACQUIRE the lock before continuing</text>
  <text x="20" y="145" fill="#f85149" font-size="9">Consumer re-checks "while(!ready)" after waking -- never assumes the condition is now true.</text>
</svg>

`wait()` releases the lock while blocked; waking requires re-acquiring the lock and re-verifying the condition.

## 5. Runnable example

Scenario: a simple single-slot producer/consumer handoff, evolved from a basic one-shot wait/notify signal into a repeated producer/consumer loop, then into a version correctly using `notifyAll` and a proper condition-check loop to handle multiple consumers safely.

### Level 1 — Basic

```java
public class WaitNotifyBasic {
    static final Object lock = new Object();
    static String message = null;

    public static void main(String[] args) throws InterruptedException {
        Thread consumer = new Thread(() -> {
            synchronized (lock) {
                while (message == null) {
                    try { lock.wait(); } catch (InterruptedException e) { return; }
                }
                System.out.println("Consumer received: " + message);
            }
        });
        consumer.start();

        Thread.sleep(200); // ensure consumer is waiting before we produce
        synchronized (lock) {
            message = "Hello from producer!";
            lock.notify();
        }
        consumer.join();
    }
}
```

**How to run:** `java WaitNotifyBasic.java`

A single producer/consumer handoff: the consumer waits until `message` is set, then the producer sets it and calls `notify()` to wake the consumer — the simplest possible demonstration of the coordination pattern.

### Level 2 — Intermediate

Same handoff, now repeated multiple times in a loop, with the producer and consumer alternating — demonstrating that `wait`/`notify` supports an ongoing back-and-forth, not just a single one-time signal.

```java
public class WaitNotifyIntermediate {
    static final Object lock = new Object();
    static String message = null;
    static boolean done = false;

    public static void main(String[] args) throws InterruptedException {
        Thread consumer = new Thread(() -> {
            synchronized (lock) {
                while (!done) {
                    while (message == null && !done) {
                        try { lock.wait(); } catch (InterruptedException e) { return; }
                    }
                    if (message != null) {
                        System.out.println("Consumer received: " + message);
                        message = null;
                        lock.notify(); // tell the producer it can produce again
                    }
                }
            }
        });
        consumer.start();

        for (int i = 1; i <= 3; i++) {
            synchronized (lock) {
                message = "Message " + i;
                lock.notify();
                while (message != null) { // wait until the consumer has taken it
                    lock.wait();
                }
            }
        }
        synchronized (lock) {
            done = true;
            lock.notify();
        }
        consumer.join();
    }
}
```

**How to run:** `java WaitNotifyIntermediate.java`

Producer and consumer now alternate: the producer sets a message and waits for the consumer to clear it before producing the next one, and the consumer waits for a message, consumes it, clears it, and notifies the producer — this back-and-forth handoff, repeated three times, demonstrates `wait`/`notify` as an ongoing coordination mechanism rather than a single one-shot signal.

### Level 3 — Advanced

Same handoff pattern, now generalized to support **multiple consumer threads** competing for messages from one producer, correctly using `notifyAll()` (since `notify()` only wakes one arbitrarily-chosen waiter, which could leave other legitimately-waiting consumers stuck) and a robust condition-check loop that handles the case where a woken consumer finds the message already taken by a different consumer.

```java
public class WaitNotifyAdvanced {
    static final Object lock = new Object();
    static String message = null;
    static boolean done = false;

    static void consumerLoop(String name) {
        while (true) {
            synchronized (lock) {
                while (message == null && !done) {
                    try { lock.wait(); } catch (InterruptedException e) { return; }
                }
                if (message != null) {
                    System.out.println(name + " consumed: " + message);
                    message = null;
                    lock.notifyAll(); // wake the producer AND any other still-waiting consumers
                } else if (done) {
                    return; // no more messages will ever come
                }
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread c1 = new Thread(() -> consumerLoop("Consumer-1"));
        Thread c2 = new Thread(() -> consumerLoop("Consumer-2"));
        c1.start();
        c2.start();

        for (int i = 1; i <= 4; i++) {
            synchronized (lock) {
                while (message != null) { // wait for the previous message to be taken
                    lock.wait();
                }
                message = "Message " + i;
                lock.notifyAll(); // wake BOTH consumers -- only one will actually get the message
            }
        }
        synchronized (lock) {
            done = true;
            lock.notifyAll();
        }
        c1.join();
        c2.join();
    }
}
```

**How to run:** `java WaitNotifyAdvanced.java`

With two consumers, `notifyAll()` (not `notify()`) is essential: if the producer used `notify()`, it might wake a consumer that then finds `message == null` again (because a *different*, non-woken consumer somehow got to it first, or the message was already cleared) and would need to go back to waiting anyway — `notifyAll()` wakes both consumers, each of which re-acquires the lock (one at a time, since they still need the lock to check the condition) and re-checks `while (message == null && !done)`, so whichever one actually finds a real message present consumes it, and the other correctly loops back to waiting.

## 6. Walkthrough

Trace one produce/consume cycle in `WaitNotifyAdvanced.main` step by step, assuming `Consumer-1` and `Consumer-2` are both already waiting when the producer produces "Message 1".

**Producer produces.** In the `for` loop's first iteration, the main thread acquires `lock`, finds `message == null` (true initially, so its own `while (message != null) wait()` guard doesn't block), sets `message = "Message 1"`, and calls `lock.notifyAll()`. This wakes **both** `Consumer-1` and `Consumer-2`, which were blocked inside their own `lock.wait()` calls — but waking up from `wait()` doesn't mean they immediately run; each must first re-acquire `lock`, which only one can hold at a time.

**One consumer wins the race to re-acquire the lock.** Say `Consumer-1` re-acquires `lock` first. It re-checks `while (message == null && !done)` — `message` is `"Message 1"`, not `null`, so the loop condition is `false`, and it exits the wait loop. It prints `"Consumer-1 consumed: Message 1"`, sets `message = null`, and calls `lock.notifyAll()` again (waking the producer, which is waiting in its own `while (message != null) wait()` loop, and also re-waking `Consumer-2`, which hasn't gotten a chance to check anything yet). `Consumer-1` then releases the lock as it exits its `synchronized` block.

**`Consumer-2` gets its turn.** It re-acquires `lock` (having been woken by `Consumer-1`'s `notifyAll()`), re-checks its condition: `message == null` is now `true` again (since `Consumer-1` already cleared it) and `done` is still `false`, so its `while` condition remains `true` — it calls `lock.wait()` again, correctly going back to sleep rather than mistakenly trying to consume a message that isn't there anymore.

**The producer gets its turn.** Having also been woken by `Consumer-1`'s `notifyAll()`, the producer re-acquires `lock` in its own `while (message != null) wait()` check — `message` is now `null` (cleared by `Consumer-1`), so this condition is `false`, and the producer's wait loop exits, letting the `for` loop proceed to its second iteration, producing `"Message 2"`.

**The cycle repeats** for messages 2, 3, and 4, with the two consumers essentially taking turns (though which specific consumer gets any given message depends on scheduling and isn't deterministic) — the key correctness property is that every message is consumed by exactly one consumer, and no consumer ever "sees" the same message another already took, because the `while` re-check after waking prevents acting on a stale or already-consumed condition.

```
Producer: sets message, notifyAll() -> wakes BOTH consumers

Consumer-1 (wins the race for the lock first):
  re-check: message != null -> consumes it, clears message, notifyAll()

Consumer-2 (gets the lock next):
  re-check: message == null again -> goes back to wait() (correctly, no double-consumption)

Producer (gets the lock next):
  re-check: message == null -> proceeds to produce the NEXT message
```

**Output (illustrative — which consumer gets which message varies by run):**
```
Consumer-1 consumed: Message 1
Consumer-2 consumed: Message 2
Consumer-1 consumed: Message 3
Consumer-2 consumed: Message 4
```

## 7. Gotchas & takeaways

> `wait()` must always be called inside a loop that re-checks the actual condition, never a single `if`. A thread can wake from `wait()` due to a "spurious wakeup" (permitted by the Java specification, though rare in practice) or because `notifyAll()` woke multiple threads but the condition is only actually true for one of them — as clearly demonstrated by `Consumer-2` correctly going back to sleep after finding the message already gone.

> Calling `wait()`, `notify()`, or `notifyAll()` outside a `synchronized` block on that same object throws `IllegalMonitorStateException` — these methods fundamentally require the calling thread to already hold the object's monitor lock, since `wait()`'s whole mechanism (releasing the lock atomically with beginning to wait) depends on it.

- `wait()` releases the held lock and blocks until `notify()`/`notifyAll()` is called on the same object, then re-acquires the lock before continuing.
- Always call `wait()` inside a `while` loop re-checking the real condition — never assume waking up means the condition is now true.
- Use `notifyAll()` (not `notify()`) whenever multiple threads might be waiting for potentially different reasons, or when you can't guarantee any arbitrarily-woken single thread is the "correct" one to proceed.
- For most real applications, prefer higher-level `java.util.concurrent` utilities (`BlockingQueue`, `CountDownLatch`, `Condition`) over raw `wait`/`notify`, reserving this mechanism for understanding how those tools work underneath.
