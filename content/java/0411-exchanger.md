---
card: java
gi: 411
slug: exchanger
title: Exchanger
---

## 1. What it is

`Exchanger<V>` is a synchronization point for exactly **two** threads to swap objects with each other. Each thread calls `exchange(myObject)`, passing in the object it wants to hand off; the call blocks until the *other* thread also calls `exchange(...)`, at which point both calls return simultaneously — each thread receiving the object the other one passed in. It's a rendezvous for a pair, not a general multi-thread coordination tool.

## 2. Why & when

Some two-thread pipelines work in alternating "fill one buffer while the other is being processed" rounds — a classic example is a producer thread filling a buffer with data while a consumer thread simultaneously processes the *previous* buffer, and periodically they need to swap: the producer hands off its full buffer and gets back an empty one to keep filling, while the consumer hands off its now-empty buffer and gets the full one to start processing. Coordinating this with a `BlockingQueue` works too, but `Exchanger` expresses the "swap" intent directly and avoids any intermediate copying or queueing overhead — the two objects are handed off directly, thread to thread.

You reach for `Exchanger` specifically when exactly two threads need to repeatedly trade data back and forth in lockstep — it's a narrower, more specialized tool than `BlockingQueue`, useful for double-buffering pipelines and similar two-party handoff patterns.

## 3. Core concept

```java
import java.util.concurrent.Exchanger;

Exchanger<String> exchanger = new Exchanger<>();

// Thread A:
String fromB = exchanger.exchange("hello from A"); // blocks until B also calls exchange

// Thread B:
String fromA = exchanger.exchange("hello from B"); // blocks until A also calls exchange

// After both return: A's fromB == "hello from B", B's fromA == "hello from A"
```

Both threads must call `exchange()` before either one proceeds — think of it as two people meeting at a designated spot to trade bags: neither can leave with the other's bag until both have actually shown up.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Producer thread hands its full buffer to an Exchanger and receives an empty buffer back from the consumer thread, and vice versa, at the same instant">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <rect x="30" y="55" width="160" height="44" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="82" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Producer: has FULL buffer</text>

  <rect x="450" y="55" width="160" height="44" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="82" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Consumer: has EMPTY buffer</text>

  <line x1="190" y1="65" x2="445" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ax1)"/>
  <text x="320" y="58" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">full buffer -&gt;</text>
  <line x1="445" y1="90" x2="190" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ax2)"/>
  <text x="320" y="103" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;- empty buffer</text>

  <text x="320" y="135" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Both exchange() calls return at the same moment -- producer now fills the empty one, consumer processes the full one</text>
  <defs><marker id="ax1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker><marker id="ax2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

Each side gives up what it's holding and receives what the other side was holding, at the same instant.

## 5. Runnable example

Scenario: a double-buffered logging pipeline where a producer thread fills a batch of log entries while a consumer thread flushes the previous batch to disk, swapping buffers at each round — the same double-buffer swap, evolved from a single exchange, through repeated rounds, to a version with a timed exchange so the pipeline can shut down gracefully instead of hanging if one side stops.

### Level 1 — Basic

```java
import java.util.concurrent.Exchanger;
import java.util.ArrayList;
import java.util.List;

public class LogBufferSingleSwap {
    public static void main(String[] args) throws InterruptedException {
        Exchanger<List<String>> exchanger = new Exchanger<>();

        Thread producer = new Thread(() -> {
            List<String> buffer = new ArrayList<>(List.of("log1", "log2", "log3"));
            try {
                List<String> empty = exchanger.exchange(buffer); // hands over the full buffer
                System.out.println("Producer received buffer of size " + empty.size() + " back");
            } catch (InterruptedException ignored) { }
        });

        Thread consumer = new Thread(() -> {
            List<String> emptyBuffer = new ArrayList<>();
            try {
                List<String> full = exchanger.exchange(emptyBuffer); // hands over the empty buffer
                System.out.println("Consumer received: " + full);
            } catch (InterruptedException ignored) { }
        });

        producer.start(); consumer.start();
        producer.join(); consumer.join();
    }
}
```

**How to run:** `java LogBufferSingleSwap.java`

The producer's full buffer and the consumer's empty buffer trade places in one `exchange()` round-trip — the producer ends up holding the (now empty) buffer the consumer had, and the consumer ends up holding the (full) buffer the producer had.

### Level 2 — Intermediate

```java
import java.util.concurrent.Exchanger;
import java.util.ArrayList;
import java.util.List;

public class LogBufferMultipleRounds {
    public static void main(String[] args) throws InterruptedException {
        Exchanger<List<String>> exchanger = new Exchanger<>();

        Thread producer = new Thread(() -> {
            List<String> buffer = new ArrayList<>();
            try {
                for (int round = 1; round <= 3; round++) {
                    buffer.add("log-round-" + round + "-a");
                    buffer.add("log-round-" + round + "-b");
                    System.out.println("Producer filled round " + round + ": " + buffer);
                    buffer = exchanger.exchange(buffer); // swap: get back an empty buffer to refill
                }
            } catch (InterruptedException ignored) { }
        });

        Thread consumer = new Thread(() -> {
            List<String> buffer = new ArrayList<>();
            try {
                for (int round = 1; round <= 3; round++) {
                    buffer = exchanger.exchange(buffer); // swap: hand over empty, receive full
                    System.out.println("Consumer flushing round " + round + ": " + buffer);
                    buffer.clear(); // "flush" then reuse the (now empty) list for the next round
                }
            } catch (InterruptedException ignored) { }
        });

        producer.start(); consumer.start();
        producer.join(); consumer.join();
    }
}
```

**How to run:** `java LogBufferMultipleRounds.java`

The same `exchanger` handles three full round-trips of swaps, one per loop iteration on each side — each round, the producer fills a fresh buffer while the consumer flushes what it received last round, and then they trade again, forming a genuine double-buffered pipeline.

### Level 3 — Advanced

```java
import java.util.concurrent.Exchanger;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.TimeUnit;
import java.util.ArrayList;
import java.util.List;

public class LogBufferTimedShutdown {
    public static void main(String[] args) throws InterruptedException {
        Exchanger<List<String>> exchanger = new Exchanger<>();

        Thread producer = new Thread(() -> {
            List<String> buffer = new ArrayList<>();
            try {
                for (int round = 1; round <= 2; round++) {
                    buffer.add("log-round-" + round);
                    System.out.println("Producer filled round " + round);
                    buffer = exchanger.exchange(buffer, 500, TimeUnit.MILLISECONDS);
                }
                // Round 3: producer is "done" and stops calling exchange -- consumer must not hang forever
                System.out.println("Producer finished producing.");
            } catch (InterruptedException ignored) {
            } catch (TimeoutException e) {
                System.out.println("Producer: exchange timed out, giving up.");
            }
        });

        Thread consumer = new Thread(() -> {
            List<String> buffer = new ArrayList<>();
            try {
                for (int round = 1; round <= 3; round++) { // consumer expects one more round than producer sends
                    buffer = exchanger.exchange(buffer, 500, TimeUnit.MILLISECONDS);
                    System.out.println("Consumer flushed round " + round + ": " + buffer);
                    buffer.clear();
                }
            } catch (InterruptedException ignored) {
            } catch (TimeoutException e) {
                System.out.println("Consumer: no partner for round 3 within 500ms, shutting down cleanly.");
            }
        });

        producer.start(); consumer.start();
        producer.join(); consumer.join();
    }
}
```

**How to run:** `java LogBufferTimedShutdown.java`

`exchange(buffer, 500, TimeUnit.MILLISECONDS)` bounds how long a thread waits for its partner — since the producer stops after 2 rounds but the consumer expects a 3rd, the consumer's final `exchange()` call would otherwise block forever waiting for a partner that will never arrive; the timeout lets it detect this and shut down cleanly instead of hanging the whole program.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example, starting `producer` and `consumer` threads that share one `exchanger`.

**Round 1:** the producer adds `"log-round-1"` to its buffer, prints a fill message, then calls `exchanger.exchange(buffer, 500, TimeUnit.MILLISECONDS)`. Concurrently, the consumer calls the same `exchange()` with its own (initially empty) buffer. Once both threads have called `exchange()`, both calls return together: the producer receives the consumer's empty buffer (ready to refill for round 2), and the consumer receives the producer's buffer containing `"log-round-1"`, which it prints and then clears.

**Round 2:** the same pattern repeats — producer fills a fresh buffer with `"log-round-2"`, both sides call `exchange()`, both return together, consumer flushes `"log-round-2"`.

**Round 3:** here the two loops diverge. The producer's `for` loop only runs 2 iterations (`round <= 2`), so after round 2's exchange, the producer's loop ends, it prints `"Producer finished producing."`, and the producer thread simply finishes — it never calls `exchange()` a third time. The consumer's loop, however, runs 3 iterations (`round <= 3`), so it calls `exchange()` a third time, expecting a partner.

Since no thread (the producer is done) will ever call `exchange()` again, the consumer's third `exchange(buffer, 500, TimeUnit.MILLISECONDS)` call has no partner to pair with — after waiting the full 500ms, it throws `TimeoutException` instead of blocking forever. The consumer's `catch (TimeoutException e)` block catches this and prints a clean shutdown message, ending the consumer thread's loop gracefully rather than deadlocking the program.

Expected output:
```
Producer filled round 1
Consumer flushed round 1: [log-round-1]
Producer filled round 2
Consumer flushed round 2: [log-round-2]
Producer finished producing.
Consumer: no partner for round 3 within 500ms, shutting down cleanly.
```

## 7. Gotchas & takeaways

> `Exchanger` is strictly for **exactly two** threads. If a third thread calls `exchange()` on the same `Exchanger` instance while two others are already paired up, its call simply waits for the *next* available partner — there's no way to coordinate three or more threads through one `Exchanger`. For more than two parties, use `CyclicBarrier` (rendezvous, no data exchange) or a `BlockingQueue`/`Exchanger` combination designed for that specific structure.

- Both threads must call `exchange()` for either one to proceed — it's a true two-party rendezvous, not a queue.
- The timed overload, `exchange(object, timeout, unit)`, throws `TimeoutException` if no partner shows up in time — essential for avoiding an indefinite hang if one side of the pair stops participating.
- Best fit: double-buffering pipelines where two threads repeatedly swap "the thing I'm done with" for "the thing you're done with," in lockstep.
- Unlike a `BlockingQueue`, there's no intermediate storage — the handoff is direct, one object for another, at the exact moment both threads are ready.
- If the number of participants might not always be exactly two, or you need more flexible many-to-many coordination, a `BlockingQueue` is usually the more robust choice.
