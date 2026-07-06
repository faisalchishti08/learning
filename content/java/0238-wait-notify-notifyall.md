---
card: java
gi: 238
slug: wait-notify-notifyall
title: wait() / notify() / notifyAll()
---

## 1. What it is

`wait()`, `notify()`, and `notifyAll()` are `final` methods inherited from `Object` that let threads coordinate around a shared object's monitor lock: a thread calling `wait()` inside a `synchronized` block releases the lock and pauses until another thread calls `notify()` (wakes one waiting thread) or `notifyAll()` (wakes every waiting thread) on that same object. They are the lowest-level building block Java provides for making one thread wait until another thread signals that some condition has changed.

```java
class Box {
    private String item;

    synchronized void put(String item) {
        this.item = item;
        notifyAll(); // wake up any thread waiting in take()
    }

    synchronized String take() throws InterruptedException {
        while (item == null) {
            wait(); // release the lock and pause until notified
        }
        String result = item;
        item = null;
        return result;
    }
}
```

`take()` calls `wait()` in a loop whenever `item` is `null`, releasing `Box`'s lock while paused so another thread can call `put()`; once `put()` sets `item` and calls `notifyAll()`, the waiting thread wakes, re-acquires the lock, re-checks the loop condition, and finally proceeds since `item` is no longer `null`.

## 2. Why & when

`wait`/`notify`/`notifyAll` exist to solve a specific coordination problem: a thread needs to pause until some condition becomes true, without either busy-looping (wasting CPU checking repeatedly) or missing a signal that arrives while it wasn't looking.

- **Efficient waiting** — a thread that calls `wait()` is truly suspended (using no CPU) until woken, unlike a `while (!condition) { }` spin loop that burns CPU cycles checking constantly.
- **Producer/consumer coordination** — the classic use case, shown in the `Box` example, is one thread producing data (`put`) and another consuming it (`take`), where the consumer must wait until data actually exists.
- **Historical foundation for higher-level tools** — `java.util.concurrent` (blocking queues, locks, executors — covered in dedicated concurrency topics) is built on these same underlying ideas, but provides much safer, higher-level abstractions; `wait`/`notify` is rarely used directly in modern application code, but understanding it explains what those higher-level tools are doing underneath.

Use `wait`/`notify`/`notifyAll` directly only when you have a genuine reason to work at this low level (often in teaching contexts or very specific performance-sensitive code); for real production coordination between threads, prefer `java.util.concurrent` classes like `BlockingQueue`, which implement this same pattern correctly and safely without requiring you to manage the synchronized-block-and-loop discipline yourself.

## 3. Core concept

```java
class Signal {
    private boolean ready = false;

    synchronized void await() throws InterruptedException {
        while (!ready) {   // ALWAYS a loop, never a plain "if" — see gotchas
            wait();
        }
    }

    synchronized void signalReady() {
        ready = true;
        notifyAll(); // notifyAll, not notify, unless you are certain only one waiter can ever proceed
    }
}
```

`wait()` must always be called inside a `synchronized` block on the same object being waited on, and must always be wrapped in a `while` loop re-checking the actual condition (`ready`, here) rather than a one-time `if` — this loop is what protects against spurious wakeups and missed-signal races, both explained in the gotchas.

## 4. Diagram

<svg viewBox="0 0 600 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Thread A calls wait and releases the lock and pauses, thread B acquires the lock changes state and calls notifyAll, thread A wakes reacquires the lock and rechecks its condition">
  <rect x="8" y="8" width="584" height="194" rx="8" fill="#0d1117"/>

  <rect x="30" y="20" width="160" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Thread A: wait()</text>
  <line x1="110" y1="50" x2="110" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <rect x="30" y="85" width="160" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="110" y="105" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">lock released, paused</text>

  <rect x="400" y="20" width="160" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="40" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Thread B: acquires lock</text>
  <line x1="480" y1="50" x2="480" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <rect x="400" y="85" width="160" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="105" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">changes state, notifyAll()</text>

  <line x1="400" y1="100" x2="190" y2="130" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4"/>

  <rect x="30" y="140" width="160" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="160" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">A wakes, re-acquires lock</text>
  <line x1="110" y1="170" x2="110" y2="185" stroke="#8b949e" stroke-width="1.5"/>
  <text x="300" y="195" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">A re-checks the while condition before proceeding, in case it wasn't really true yet.</text>
</svg>

`wait()` releases the lock and pauses; `notifyAll()` wakes waiters, who must re-acquire the lock and re-check their condition.

## 5. Runnable example

Scenario: a single-slot mailbox shared between a producer and a consumer thread, evolved from a basic wait/notify pair into a version handling multiple waiting consumers correctly, then hardened against spurious wakeups and interruption.

### Level 1 — Basic

```java
public class WaitNotifyBasic {
    static class Mailbox {
        private String message;

        synchronized void send(String msg) {
            message = msg;
            notify(); // wake the one waiting thread, if any
        }

        synchronized String receive() throws InterruptedException {
            while (message == null) {
                wait();
            }
            String result = message;
            message = null;
            return result;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Mailbox mailbox = new Mailbox();

        Thread consumer = new Thread(() -> {
            try {
                System.out.println("Consumer received: " + mailbox.receive());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
        consumer.start();

        Thread.sleep(100); // give the consumer time to start waiting
        mailbox.send("hello");

        consumer.join();
    }
}
```

**How to run:** `java WaitNotifyBasic.java`

The consumer thread starts, enters `receive()`, finds `message == null`, and calls `wait()`, releasing the `Mailbox` lock and pausing; the main thread then calls `send("hello")`, which sets `message` and calls `notify()`, waking the consumer, which re-acquires the lock, re-checks the loop (now `false`, since `message` is set), and returns `"hello"`.

### Level 2 — Intermediate

Same mailbox, now with *multiple* consumer threads waiting — demonstrating why `notifyAll()` (waking every waiter so they can all re-check the condition) is generally safer than `notify()` (which wakes only one, arbitrarily chosen, waiting thread) when more than one thread might be waiting.

```java
import java.util.concurrent.atomic.AtomicInteger;

public class WaitNotifyIntermediate {
    static class Mailbox {
        private String message;

        synchronized void send(String msg) {
            message = msg;
            notifyAll(); // wake ALL waiters so every one gets a chance to re-check the condition
        }

        synchronized String receive() throws InterruptedException {
            while (message == null) {
                wait();
            }
            String result = message;
            message = null; // only the FIRST consumer to re-check will find a non-null message
            return result;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Mailbox mailbox = new Mailbox();
        AtomicInteger received = new AtomicInteger(0);

        Runnable consumerTask = () -> {
            try {
                mailbox.receive();
                received.incrementAndGet();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        };

        Thread c1 = new Thread(consumerTask);
        Thread c2 = new Thread(consumerTask);
        c1.start();
        c2.start();

        Thread.sleep(100);
        mailbox.send("one message"); // only ONE consumer will actually consume it
        c1.join();

        System.out.println("Received count after one send: " + received.get()); // 1
        mailbox.send("second message"); // wakes the still-waiting consumer
        c2.join();
        System.out.println("Received count after two sends: " + received.get()); // 2
    }
}
```

**How to run:** `java WaitNotifyIntermediate.java`

Both consumers wait; `notifyAll()` wakes both when a message arrives, but the `while` loop guarantees only the first one to re-acquire the lock actually sees `message != null` and consumes it — the other re-checks the loop, finds `message == null` again (since it was reset to `null`), and calls `wait()` again to keep waiting.

### Level 3 — Advanced

Same mailbox, now demonstrating why the condition must be re-checked in a `while` loop rather than a one-time `if` — this defends against both "spurious wakeups" (the JVM is allowed to wake a waiting thread without any `notify` call at all, a rare but real possibility) and the case where a woken thread loses a race to consume the message.

```java
public class WaitNotifyAdvanced {
    static class Mailbox {
        private String message;
        private int spuriousWakeupSimulator = 0;

        synchronized void send(String msg) {
            message = msg;
            notifyAll();
        }

        synchronized String receive() throws InterruptedException {
            while (message == null) { // MUST be while, not if — see explanation
                spuriousWakeupSimulator++;
                wait();
            }
            String result = message;
            message = null;
            return result;
        }

        synchronized int getWakeupAttempts() { return spuriousWakeupSimulator; }
    }

    public static void main(String[] args) throws InterruptedException {
        Mailbox mailbox = new Mailbox();

        Thread consumer = new Thread(() -> {
            try {
                String msg = mailbox.receive();
                System.out.println("Consumer got: " + msg);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
        consumer.start();

        Thread.sleep(50);
        // Simulate a spurious wakeup attempt: notifyAll with no message set yet
        synchronized (mailbox) {
            mailbox.notifyAll(); // consumer wakes, but message is STILL null -> loop keeps it waiting
        }

        Thread.sleep(50);
        mailbox.send("real message"); // the genuine signal

        consumer.join();
        System.out.println("Total wait-loop re-checks: " + mailbox.getWakeupAttempts()); // 2 or more
    }
}
```

**How to run:** `java WaitNotifyAdvanced.java`

The stray `mailbox.notifyAll()` call (simulating a spurious or premature wakeup, or simply a notify that happened before any real data was ready) wakes the consumer out of `wait()`, but because `receive()` re-checks its condition in a `while` loop, it correctly notices `message` is still `null` and calls `wait()` again instead of incorrectly proceeding — only the later, genuine `send("real message")` actually lets it return.

## 6. Walkthrough

Trace the sequence of events across the two threads in `WaitNotifyAdvanced.main`, in the order they actually happen.

**Consumer thread starts and calls `mailbox.receive()`.** It acquires `mailbox`'s lock (entering the `synchronized` method), checks `message == null` — `true` (no message yet) — increments `spuriousWakeupSimulator` to `1`, and calls `wait()`, which releases the lock and suspends the consumer thread.

**Main thread sleeps 50ms, then calls `mailbox.notifyAll()` directly** (inside its own `synchronized (mailbox)` block, needed because `notifyAll` also requires holding the lock). This wakes the consumer thread, but note: `message` is still `null` at this point — nothing set it.

**Consumer thread wakes from `wait()`.** Before it can proceed past the `wait()` call, it must first re-acquire `mailbox`'s lock (waiting if the main thread still holds it). Once reacquired, execution returns to the top of the `while` loop, which re-checks `message == null` — still `true`, since no `send` has happened yet — so it increments `spuriousWakeupSimulator` to `2` and calls `wait()` again, going back to sleep.

**Main thread sleeps another 50ms, then calls `mailbox.send("real message")`.** This acquires the lock, sets `message = "real message"`, and calls `notifyAll()`, waking the consumer again.

**Consumer thread wakes a second time.** Re-acquires the lock, re-checks the loop: `message == null` is now `false` (it holds `"real message"`), so the loop exits. `result` is set to `"real message"`, `message` is reset to `null`, and `receive()` returns `"real message"`.

**Consumer prints its result**, then the main thread's `consumer.join()` returns, and the final line prints the accumulated wakeup-attempt count.

```
consumer: message==null -> wait() #1 (spuriousWakeupSimulator=1)
main:     notifyAll() with message still null (simulated spurious/premature wake)
consumer: wakes, re-checks while -> still null -> wait() #2 (spuriousWakeupSimulator=2)
main:     send("real message") -> message set, notifyAll()
consumer: wakes, re-checks while -> message present -> exits loop -> returns "real message"
```

**Final output.**
```
Consumer got: real message
Total wait-loop re-checks: 2
```
This demonstrates precisely why `wait()` must always be inside a `while` loop re-checking the real condition: the consumer was woken twice, but only proceeded on the second wake, once the condition it actually cared about was genuinely true.

## 7. Gotchas & takeaways

> **Always call `wait()` inside a `while` loop that re-checks the actual condition, never a one-time `if`.** The Java specification explicitly allows "spurious wakeups" — a thread can return from `wait()` without any `notify`/`notifyAll` call ever happening — and even without that, multiple waiters can race to consume a single signal, as `WaitNotifyIntermediate` showed. A `while` loop protects against both cases; an `if` does not.

> **`notify()` wakes exactly one waiting thread, chosen arbitrarily by the JVM — this can cause "lost wakeup" bugs if the wrong thread is woken for the wrong reason.** `notifyAll()` is almost always the safer default, since every waiter gets a chance to re-check its own condition; use `notify()` only when you are certain all waiting threads are interchangeable and only one should ever proceed per signal.

- `wait()` must be called inside a `synchronized` block on the object being waited on; it releases that lock while paused and requires re-acquiring it before returning.
- `notify()` wakes one arbitrary waiting thread; `notifyAll()` wakes all of them — prefer `notifyAll()` unless you have a specific, verified reason to use `notify()`.
- Always wrap `wait()` in a `while` loop re-checking the real condition, to guard against spurious wakeups and races between multiple waiters.
- Modern code should generally prefer `java.util.concurrent` utilities (like `BlockingQueue`) over hand-rolled `wait`/`notify`, which implement this same coordination pattern correctly with far less room for subtle bugs.
