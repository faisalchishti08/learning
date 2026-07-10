---
card: java
gi: 890
slug: exchanger
title: Exchanger
---

## 1. What it is

`Exchanger<V>` is a synchronization point for exactly **two** threads to swap objects: each thread calls `exchange(myObject)`, which blocks until the *other* thread also calls `exchange`, at which point both calls return — but each thread receives the *other* thread's object, not its own. It's a rendezvous point specifically built for pairwise handoff, distinct from a queue (which has no notion of "pairing" a specific producer with a specific consumer) or a barrier (which coordinates arrival, not the actual exchange of data).

## 2. Why & when

Use `Exchanger` when exactly two threads need to repeatedly swap buffers or data structures — the classic example is a producer filling one buffer while a consumer drains another, then swapping the two buffers once both are ready, so the producer immediately starts filling the buffer the consumer just finished with, and vice versa, without ever needing an extra copy or a shared queue. This "double buffering" pattern shows up in data pipelines, simulations exchanging state between two cooperating threads, and any producer/consumer pair where you want zero-copy handoff of a whole batch at a time rather than item-by-item queuing. It only ever works for exactly two parties — for anything involving more threads, look to [`Phaser`](0889-phaser.md), [`CyclicBarrier`](0887-cyclicbarrier.md), or a proper concurrent queue instead.

## 3. Core concept

```java
Exchanger<List<Integer>> exchanger = new Exchanger<>();

// Producer thread:
List<Integer> fullBuffer = fillBuffer();
List<Integer> emptyBuffer = exchanger.exchange(fullBuffer); // blocks until consumer also calls exchange
// emptyBuffer is now available to fill again -- consumer got fullBuffer

// Consumer thread:
List<Integer> emptyBuffer = new ArrayList<>();
List<Integer> fullBuffer = exchanger.exchange(emptyBuffer); // blocks until producer also calls exchange
// fullBuffer is now available to process -- producer got emptyBuffer
```

Both threads call `exchange()` with their own object; both block until the other arrives, and then both return holding what the *other* thread brought.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Producer thread calls exchange with a full buffer, consumer thread calls exchange with an empty buffer, both block until the other arrives, then swap so the producer gets the empty buffer and the consumer gets the full one">
  <rect x="20" y="20" width="200" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Producer: exchange(fullBuf)</text>

  <rect x="420" y="20" width="200" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="520" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Consumer: exchange(emptyBuf)</text>

  <rect x="220" y="90" width="200" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">RENDEZVOUS -- both arrive, swap</text>

  <line x1="120" y1="60" x2="280" y2="88" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a24)"/>
  <line x1="520" y1="60" x2="360" y2="88" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a24)"/>

  <text x="120" y="145" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Producer now has emptyBuf</text>
  <text x="520" y="145" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Consumer now has fullBuf</text>
  <defs><marker id="a24" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Both threads block until the other arrives at the exchange point; each leaves holding what the other one brought.*

## 5. Runnable example

Scenario: a producer/consumer pair processing data in batches with double buffering, growing from a naive shared-queue version with per-item locking overhead, to a correct `Exchanger`-based double-buffer swap, to a version handling a graceful shutdown signal through the exchanged data itself.

### Level 1 — Basic

```java
import java.util.concurrent.*;
import java.util.*;

public class QueueBasedHandoff {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Integer> queue = new LinkedBlockingQueue<>();

        Thread producer = new Thread(() -> {
            for (int i = 0; i < 10; i++) {
                queue.offer(i); // one item at a time -- per-item synchronization overhead
            }
        });
        Thread consumer = new Thread(() -> {
            int received = 0;
            while (received < 10) {
                Integer item = queue.poll();
                if (item != null) { received++; System.out.println("processed " + item); }
            }
        });
        producer.start(); consumer.start();
        producer.join(); consumer.join();
    }
}
```

**How to run:** `java QueueBasedHandoff.java` (JDK 17+).

Expected output shape:
```
processed 0
processed 1
... (10 lines total)
```

Works, but each individual item requires its own synchronized handoff through the queue — for workloads naturally organized in whole batches, this is more fine-grained synchronization than necessary.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.*;

public class ExchangerDoubleBuffer {
    public static void main(String[] args) throws InterruptedException {
        Exchanger<List<Integer>> exchanger = new Exchanger<>();

        Thread producer = new Thread(() -> {
            List<Integer> buffer = new ArrayList<>();
            try {
                for (int batch = 0; batch < 3; batch++) {
                    buffer.clear();
                    for (int i = 0; i < 5; i++) buffer.add(batch * 5 + i); // fill a whole batch
                    System.out.println("producer filled batch: " + buffer);
                    buffer = exchanger.exchange(buffer); // hand off the FULL batch, get back an empty one
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        Thread consumer = new Thread(() -> {
            List<Integer> buffer = new ArrayList<>(); // starts empty
            try {
                for (int batch = 0; batch < 3; batch++) {
                    buffer = exchanger.exchange(buffer); // hand off the EMPTY buffer, get back a full one
                    System.out.println("consumer processing batch: " + buffer);
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        producer.start(); consumer.start();
        producer.join(); consumer.join();
    }
}
```

**How to run:** `java ExchangerDoubleBuffer.java`.

Expected output shape (producer/consumer lines interleave per batch):
```
producer filled batch: [0, 1, 2, 3, 4]
consumer processing batch: [0, 1, 2, 3, 4]
producer filled batch: [5, 6, 7, 8, 9]
consumer processing batch: [5, 6, 7, 8, 9]
producer filled batch: [10, 11, 12, 13, 14]
consumer processing batch: [10, 11, 12, 13, 14]
```

The real-world concern added: entire batches of 5 items are exchanged in a single synchronization point, rather than 5 separate item-by-item handoffs — the producer immediately gets an empty buffer back to start refilling, while the consumer gets the full one to process, with no extra copying of the underlying `List`.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.*;

public class ExchangerWithShutdownSignal {
    static final List<Integer> POISON_PILL = List.of(); // sentinel: empty list signals "no more data"

    public static void main(String[] args) throws InterruptedException {
        Exchanger<List<Integer>> exchanger = new Exchanger<>();

        Thread producer = new Thread(() -> {
            List<Integer> buffer = new ArrayList<>();
            try {
                for (int batch = 0; batch < 3; batch++) {
                    buffer.clear();
                    for (int i = 0; i < 5; i++) buffer.add(batch * 5 + i);
                    buffer = exchanger.exchange(buffer);
                }
                // Done producing -- exchange the POISON_PILL to tell the consumer to stop.
                exchanger.exchange(POISON_PILL);
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        Thread consumer = new Thread(() -> {
            List<Integer> buffer = new ArrayList<>();
            try {
                while (true) {
                    buffer = exchanger.exchange(buffer);
                    if (buffer.isEmpty()) {
                        System.out.println("consumer received shutdown signal, stopping");
                        break;
                    }
                    System.out.println("consumer processing batch: " + buffer);
                }
            } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        producer.start(); consumer.start();
        producer.join(); consumer.join();
        System.out.println("both threads finished cleanly");
    }
}
```

**How to run:** `java ExchangerWithShutdownSignal.java`.

Expected output shape:
```
consumer processing batch: [0, 1, 2, 3, 4]
consumer processing batch: [5, 6, 7, 8, 9]
consumer processing batch: [10, 11, 12, 13, 14]
consumer received shutdown signal, stopping
both threads finished cleanly
```

This adds the production-flavored hard case: signaling clean shutdown through the exchange mechanism itself, using a sentinel value (`POISON_PILL`, an empty list distinguishable from any real batch) rather than a separate flag or interrupt — the producer's final `exchange(POISON_PILL)` call, after all real batches are done, is what tells the consumer to stop its loop, keeping both threads' termination logic expressed through the same `Exchanger` they already use for data handoff.

## 6. Walkthrough

Tracing `ExchangerWithShutdownSignal.main`:

1. The producer and consumer threads run through three rounds of the same double-buffering exchange as Level 2 — each round, the producer fills a batch of 5 integers and exchanges it for whatever (empty, initially) buffer the consumer offers; the consumer exchanges its buffer for the producer's full one and processes it.
2. After the loop of three batches completes, the producer has no more real data to send — instead of simply exiting (which would leave the consumer's next `exchange()` call blocked forever, waiting for a partner that will never arrive), it calls `exchanger.exchange(POISON_PILL)`, offering the special empty-list sentinel.
3. The consumer's loop, still running, calls `exchanger.exchange(buffer)` for its fourth iteration — since the producer is now offering `POISON_PILL`, the exchange completes and the consumer receives that empty list back.
4. The consumer's `if (buffer.isEmpty())` check recognizes this as the shutdown signal (distinguishable from any real batch, which always contains exactly 5 elements) and prints the shutdown message, then breaks out of its `while (true)` loop instead of calling `exchange()` again.
5. Both threads' `run()` methods now return normally — the producer after its shutdown exchange, the consumer after breaking its loop — so `producer.join()` and `consumer.join()` in `main` both return without hanging.
6. The final `println` confirms both threads terminated cleanly, having coordinated their own shutdown entirely through the same `Exchanger` object used for the actual data handoff, with no separate flag, interrupt, or external signal needed.

## 7. Gotchas & takeaways

> **Gotcha:** `Exchanger` only ever supports **exactly two** parties — a third thread calling `exchange()` on the same `Exchanger` instance will simply queue up waiting for its own partner, potentially pairing unpredictably with whichever of the other two threads calls `exchange()` next, which is almost certainly not the intended behavior for anything designed as a strict producer/consumer pair.

- `Exchanger<V>` is a rendezvous point for exactly two threads to swap objects — each `exchange()` call blocks until the other thread also calls it, and each returns holding the other's object.
- The classic use case is double-buffering: swap a full buffer for an empty one (or vice versa) so both a producer and a consumer can each keep working on their own buffer without ever needing an additional copy or a shared, lockable queue.
- Because it only supports two parties, `Exchanger` is not a substitute for a general-purpose concurrent queue when more than two threads are involved — use `BlockingQueue` or the appropriate multi-party coordination tool instead.
- A sentinel/poison-pill value exchanged through the same mechanism is a clean way to signal shutdown without adding a separate coordination channel, as long as the sentinel is unambiguously distinguishable from any real data.
- `exchange()` has a timed overload (`exchange(V, long, TimeUnit)`) for bounding how long a thread is willing to wait for its partner, avoiding an indefinite block if the other thread never arrives (e.g., due to a bug or crash).
