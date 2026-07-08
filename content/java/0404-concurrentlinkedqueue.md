---
card: java
gi: 404
slug: concurrentlinkedqueue
title: ConcurrentLinkedQueue
---

## 1. What it is

`ConcurrentLinkedQueue<E>` is an unbounded, thread-safe queue built on a **lock-free** linked-node algorithm — instead of using `synchronized` blocks or explicit locks internally, it uses atomic compare-and-swap (CAS) operations to safely add (`offer`) and remove (`poll`) nodes even under heavy concurrent access from many threads. Unlike `BlockingQueue` implementations, it has no blocking methods: `poll()` on an empty queue returns `null` immediately rather than waiting.

## 2. Why & when

`ArrayBlockingQueue` and `LinkedBlockingQueue` use locks internally to coordinate `put`/`take`; under very high contention (many threads hammering the queue simultaneously), lock-based coordination means threads spend time waiting for the lock rather than doing work. `ConcurrentLinkedQueue` avoids that entirely — its lock-free CAS-based implementation lets multiple threads add and remove elements concurrently without ever blocking each other on a lock, which can mean substantially better throughput under heavy concurrent load.

The tradeoff is that it has **no blocking API** — there's no `take()` that waits for an item to appear, and no way to bound its capacity. You reach for `ConcurrentLinkedQueue` specifically when you want a thread-safe queue for a **non-blocking, poll-and-move-on** style of work (a shared work queue where a worker checks "is there anything for me right now?" rather than committing to wait), and you don't need backpressure. If you need threads to *wait* for items or *block* when full, use a `BlockingQueue` implementation instead.

## 3. Core concept

```java
ConcurrentLinkedQueue<String> queue = new ConcurrentLinkedQueue<>();

queue.offer("task-1");           // adds -- never blocks, queue is unbounded
queue.offer("task-2");

String next = queue.poll();      // removes and returns the head, or null if empty -- never blocks
if (next == null) {
    // decide what to do: retry later, do other work, exit -- YOUR choice, not the queue's
}
```

`offer` and `add` behave identically here (since the queue is unbounded, `offer` never fails); the important method is `poll()`, which is non-blocking — contrast this directly with `BlockingQueue.take()`, which would wait.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ConcurrentLinkedQueue poll returns null immediately on an empty queue, unlike BlockingQueue take which waits">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="28" fill="#e6edf3" font-size="11" font-family="sans-serif">Empty queue, thread calls poll() vs take():</text>

  <rect x="30" y="45" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="70" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ConcurrentLinkedQueue.poll()</text>
  <text x="140" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">returns null IMMEDIATELY</text>

  <rect x="380" y="45" width="220" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="490" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">BlockingQueue.take()</text>
  <text x="490" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">BLOCKS until an item arrives</text>

  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same "empty queue" situation, two very different behaviours -- pick deliberately.</text>
</svg>

Non-blocking `poll()` vs. blocking `take()` is the defining behavioural difference to choose between.

## 5. Runnable example

Scenario: a lightweight logging pipeline where worker threads pull log lines to flush to disk — the same log queue, evolved from single-threaded polling, through concurrent producers, to a graceful drain-and-shutdown pattern that avoids busy-waiting.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class LogQueueBasic {
    public static void main(String[] args) {
        ConcurrentLinkedQueue<String> logs = new ConcurrentLinkedQueue<>();

        logs.offer("INFO: server started");
        logs.offer("INFO: request received");
        logs.offer("ERROR: connection timeout");

        String line;
        while ((line = logs.poll()) != null) { // poll() returns null once empty -- clean loop exit
            System.out.println("Flushing: " + line);
        }
        System.out.println("Queue drained: " + logs.isEmpty());
    }
}
```

**How to run:** `java LogQueueBasic.java`

`poll()` returning `null` on an empty queue makes for a clean drain loop: keep polling until you get `null`, no special "is it empty" check needed beforehand, and no blocking involved at any point.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class LogQueueConcurrentProducers {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentLinkedQueue<String> logs = new ConcurrentLinkedQueue<>();

        Runnable producer = () -> {
            String name = Thread.currentThread().getName();
            for (int i = 1; i <= 100; i++) {
                logs.offer(name + " log-" + i); // never blocks, queue grows as needed
            }
        };

        Thread p1 = new Thread(producer, "server-A");
        Thread p2 = new Thread(producer, "server-B");
        Thread p3 = new Thread(producer, "server-C");
        p1.start(); p2.start(); p3.start();
        p1.join(); p2.join(); p3.join();

        int count = 0;
        while (logs.poll() != null) count++;
        System.out.println("Total log lines collected: " + count + " (expected 300)");
    }
}
```

**How to run:** `java LogQueueConcurrentProducers.java`

Three producer threads call `offer()` concurrently with no external synchronization and no lock contention slowing them down — `ConcurrentLinkedQueue`'s lock-free design safely interleaves all 300 additions, and draining afterward confirms exactly 300 log lines were captured with none lost or corrupted.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class LogQueueGracefulDrain {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentLinkedQueue<String> logs = new ConcurrentLinkedQueue<>();
        AtomicBoolean producingDone = new AtomicBoolean(false);

        Thread producer = new Thread(() -> {
            for (int i = 1; i <= 50; i++) {
                logs.offer("log-" + i);
                try { Thread.sleep(2); } catch (InterruptedException ignored) { }
            }
            producingDone.set(true); // signal: no more logs will be added
        });

        Thread flusher = new Thread(() -> {
            int flushed = 0;
            while (!producingDone.get() || !logs.isEmpty()) {
                String line = logs.poll();
                if (line != null) {
                    flushed++;
                } else {
                    // queue momentarily empty but producer isn't done -- avoid a hot busy-loop
                    try { Thread.sleep(1); } catch (InterruptedException ignored) { }
                }
            }
            System.out.println("Flusher finished: " + flushed + " lines");
        });

        producer.start();
        flusher.start();
        producer.join();
        flusher.join();
    }
}
```

**How to run:** `java LogQueueGracefulDrain.java`

Since `ConcurrentLinkedQueue` has no blocking `take()`, the flusher thread must combine `poll()` with its own exit condition (`producingDone` flag) and a small `Thread.sleep(1)` to avoid **busy-waiting** (spinning in a tight loop burning CPU) whenever the queue is momentarily empty but more logs are still coming.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `producingDone` starts as `false`; `producer` and `flusher` threads both start immediately.

**Producer thread:** loops 50 times, each iteration calling `logs.offer("log-" + i)` (a non-blocking, lock-free insert) and then sleeping 2ms — this pacing means the flusher will frequently catch up and find the queue empty between insertions. After the 50th log is added, `producingDone.set(true)` records that no more logs are coming.

**Flusher thread:** loops on the condition `!producingDone.get() || !logs.isEmpty()` — meaning "keep looping as long as either producing isn't finished yet, OR there's still something left in the queue" (this `||` matters: even after `producingDone` flips to `true`, the loop must keep draining any remaining items before it can exit). Each iteration calls `logs.poll()`. If it returns a real line, `flushed` is incremented (simulating writing it to disk). If it returns `null` — which happens often here, since the producer paces itself at one log every 2ms — the flusher sleeps 1ms rather than immediately re-polling in a tight, CPU-wasting spin.

This dance continues: producer adds a log roughly every 2ms, flusher usually finds it (or finds nothing and briefly sleeps) until, after the 50th log, `producingDone` becomes `true`. On the flusher's next loop check, if the queue is now empty and `producingDone` is `true`, the whole condition `!true || !true` evaluates to `false`, and the loop exits. If a couple of logs were still unflushed at that moment, the `!logs.isEmpty()` part of the condition keeps the loop going until they're drained too.

Both threads then finish, and the flusher prints its final count.

Expected output:
```
Flusher finished: 50 lines
```

## 7. Gotchas & takeaways

> `ConcurrentLinkedQueue` has **no blocking methods** — `poll()` on empty returns `null` instantly rather than waiting. Looping on `poll()` without any pacing (no sleep, no other exit condition) when the queue might be empty turns into a **busy-wait**, spinning the CPU at 100% for no useful work. If you need a thread to genuinely wait for the next item, use a `BlockingQueue` (`take()`) instead.

- Lock-free via CAS (compare-and-swap) internally — no thread ever blocks another just to add or remove an element, which can mean better throughput than lock-based `BlockingQueue`s under heavy contention.
- Always unbounded — there is no capacity limit and no way to add backpressure; a runaway producer can grow it indefinitely.
- `offer()`/`add()` never block or fail (aside from `null` elements, which aren't allowed); `poll()` never blocks either, returning `null` immediately if empty.
- Best fit: a shared, non-blocking work queue where consumers check in periodically rather than committing to wait — not a producer-consumer pipeline that needs one side to pause.
- If you need waiting/blocking semantics, reach for `ArrayBlockingQueue` or `LinkedBlockingQueue` (see the previous tutorial) instead.
