---
card: spring-integration
gi: 26
slug: resequencer
title: "Resequencer"
---

## 1. What it is

`@Resequencer` (via `ResequencingMessageHandler`) is an endpoint that reorders a stream of related messages back into their original sequence order before releasing them downstream — using the same `sequenceNumber`/`sequenceSize`/`correlationId` headers a `Splitter` (card 0024) stamps. Unlike `Aggregator` (card 0025), which combines a full group into one message, a `Resequencer` releases the *same number* of messages it received — just in the correct order — buffering out-of-order arrivals until their turn comes up.

## 2. Why & when

You reach for `Resequencer` specifically when downstream processing genuinely needs messages in their original order, but upstream concurrency (or an unreliable transport) can deliver them out of order:

- **Split items were processed concurrently (e.g., across an `ExecutorChannel`, card 0013), finishing in unpredictable order, but a downstream step assumes ordering** — a report generator that must print line items in their original sequence, even though they were validated in parallel and out of order.
- **Messages arrive from a transport that doesn't guarantee ordering** (some JMS configurations, multiple partitions in a partitioned log) but the business logic needs strict per-group ordering — a `Resequencer` reconstructs that order at the messaging layer rather than requiring every downstream consumer to handle out-of-order input itself.
- **You want ordering restored as a distinct, named, testable concern**, separate from whatever caused the disorder in the first place — keeping the "why did processing become concurrent" and "how do we get order back" concerns cleanly separated.

## 3. Core concept

Think of `Resequencer` like a teacher collecting a stack of numbered exam papers handed in out of order, and sorting them back into roll-number order before passing the stack along to be graded — no paper is added or removed, and none is combined with another; they're simply released in the correct sequence, holding back any paper whose turn hasn't come yet even if it physically arrived first.

```java
@Aggregator // Resequencer uses the SAME @Aggregator annotation with a ResequencingMessageGroupProcessor
@Bean
public MessageHandler resequencer() {
    ResequencingMessageHandler handler = new ResequencingMessageHandler(new SimpleMessageStore());
    handler.setReleasePartialSequences(true); // release in-order prefixes as they become available
    return handler;
}
```

Internally, a `Resequencer` is implemented using the same correlation/grouping machinery as `Aggregator`, just configured with a `ResequencingMessageGroupProcessor` instead of a combining one — it groups by correlation ID, but releases individual messages (in order) rather than combining them into one.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Resequencer receives messages out of order (3, 1, 2) and releases them in correct sequence order (1, 2, 3), buffering each until its turn">
  <text x="120" y="30" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">arrival order</text>
  <rect x="20" y="45" width="80" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="60" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">seq 3</text>
  <rect x="110" y="45" width="80" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="150" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">seq 1</text>
  <rect x="200" y="45" width="80" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="240" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">seq 2</text>

  <line x1="150" y1="80" x2="280" y2="110" stroke="#6db33f" stroke-width="1.5"/>

  <rect x="220" y="100" width="150" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="295" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Resequencer</text>
  <text x="295" y="138" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">buffer + reorder</text>

  <line x1="370" y1="127" x2="430" y2="127" stroke="#79c0ff" stroke-width="2" marker-end="url(#rs1)"/>

  <text x="510" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">release order</text>
  <rect x="440" y="115" width="70" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="135" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">seq 1</text>
  <rect x="515" y="115" width="70" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="135" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">seq 2</text>

  <defs>
    <marker id="rs1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Messages arriving as 3, 1, 2 are released in order 1, 2, (3 once it can complete the sequence) — same count in and out, just reordered.

## 5. Runnable example

The scenario: line items processed concurrently and completing out of order, needing sequential release for a report, starting with a basic resequencer, then partial-sequence release as consecutive items become ready, and finally combining it with `Splitter` (card 0024) for a realistic round trip.

### Level 1 — Basic

```java
// BasicResequencerDemo.java
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.*;

public class BasicResequencerDemo {
    public static void main(String[] args) {
        // simulate arrival order: seq 3, then seq 1, then seq 2
        List<Message<?>> arrivals = List.of(
            MessageBuilder.withPayload("item-C").setHeader("sequenceNumber", 3).setHeader("sequenceSize", 3).build(),
            MessageBuilder.withPayload("item-A").setHeader("sequenceNumber", 1).setHeader("sequenceSize", 3).build(),
            MessageBuilder.withPayload("item-B").setHeader("sequenceNumber", 2).setHeader("sequenceSize", 3).build()
        );

        // what a Resequencer does for you: buffer, then release ONLY when the next expected number is available
        Map<Integer, Message<?>> buffer = new TreeMap<>();
        int nextExpected = 1;
        for (Message<?> m : arrivals) {
            int seq = (Integer) m.getHeaders().get("sequenceNumber");
            buffer.put(seq, m);
            System.out.println("Buffered arrival: seq=" + seq + " (" + m.getPayload() + ")");
        }
        // release phase: walk in order, only what's available in sequence
        while (buffer.containsKey(nextExpected)) {
            System.out.println("RELEASED in order: " + buffer.get(nextExpected).getPayload());
            nextExpected++;
        }
    }
}
```

How to run: `java BasicResequencerDemo.java`. Expected output: three `Buffered arrival` lines in the actual (out-of-order) arrival order `seq=3, seq=1, seq=2`, followed by three `RELEASED in order` lines strictly as `item-A`, `item-B`, `item-C` — the release order is corrected even though the buffering order wasn't.

### Level 2 — Intermediate

With `releasePartialSequences` enabled, a resequencer doesn't wait for the *entire* group to arrive before releasing anything — it releases the longest available in-order prefix as soon as it exists, which matters for latency-sensitive flows where waiting for the last (possibly slow) item before releasing anything would be wasteful.

```java
// PartialReleaseResequencerDemo.java
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.*;

public class PartialReleaseResequencerDemo {
    public static void main(String[] args) {
        Map<Integer, Message<?>> buffer = new TreeMap<>();
        int[] nextExpected = {1};

        // a helper simulating "releasePartialSequences=true": release every consecutive run available NOW
        Runnable releaseAvailablePrefix = () -> {
            while (buffer.containsKey(nextExpected[0])) {
                System.out.println("RELEASED (partial-sequence): " + buffer.remove(nextExpected[0]).getPayload());
                nextExpected[0]++;
            }
        };

        // arrival 1: seq=1 arrives -> releases immediately, no need to wait for 2 or 3
        buffer.put(1, MessageBuilder.withPayload("item-A").build());
        releaseAvailablePrefix.run();

        // arrival 2: seq=3 arrives BEFORE seq=2 -> nothing releases yet (2 is still missing)
        buffer.put(3, MessageBuilder.withPayload("item-C").build());
        releaseAvailablePrefix.run();
        System.out.println("(seq=3 buffered, waiting on seq=2 before it can release)");

        // arrival 3: seq=2 finally arrives -> releases BOTH 2 and 3 in one pass, since the prefix is now complete
        buffer.put(2, MessageBuilder.withPayload("item-B").build());
        releaseAvailablePrefix.run();
    }
}
```

How to run: `java PartialReleaseResequencerDemo.java`. Expected output: `RELEASED (partial-sequence): item-A` immediately, then `(seq=3 buffered, waiting on seq=2 before it can release)`, then both `RELEASED (partial-sequence): item-B` and `RELEASED (partial-sequence): item-C` once `seq=2` finally arrives — `item-A` didn't have to wait for the rest of the group, but `item-C` (arriving early) still had to wait its turn.

### Level 3 — Advanced

A full split-then-resequence round trip: line items are processed concurrently (finishing in random order, exactly like `Aggregator`'s Level 3 example, card 0025), but here the goal is releasing each processed item individually, in original order, for a report generator that must print them sequentially rather than combining them into one summary.

```java
// SplitThenResequenceDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.*;
import java.util.concurrent.*;

public class SplitThenResequenceDemo {
    public static void main(String[] args) throws InterruptedException {
        List<String> items = List.of("intro", "body", "conclusion"); // must print in THIS order
        DirectChannel processed = new DirectChannel();
        CountDownLatch done = new CountDownLatch(items.size());

        Map<Integer, Message<?>> buffer = new ConcurrentHashMap<>();
        int[] nextExpected = {1};
        Object lock = new Object();

        processed.subscribe(m -> {
            synchronized (lock) {
                int seq = (Integer) m.getHeaders().get("sequenceNumber");
                buffer.put(seq, m);
                while (buffer.containsKey(nextExpected[0])) {
                    Message<?> release = buffer.remove(nextExpected[0]);
                    System.out.println("Report line " + nextExpected[0] + ": " + release.getPayload());
                    nextExpected[0]++;
                    done.countDown();
                }
            }
        });

        ExecutorService pool = Executors.newFixedThreadPool(3);
        for (int i = 0; i < items.size(); i++) {
            int seq = i + 1;
            String text = items.get(i);
            pool.submit(() -> { // simulate concurrent, out-of-order completion
                try { Thread.sleep((long) (Math.random() * 200)); } catch (InterruptedException ignored) {}
                processed.send(MessageBuilder.withPayload(text.toUpperCase())
                    .setHeader("sequenceNumber", seq).build());
            });
        }

        done.await();
        pool.shutdown();
    }
}
```

How to run: `java SplitThenResequenceDemo.java`. Expected output: exactly `Report line 1: INTRO`, `Report line 2: BODY`, `Report line 3: CONCLUSION`, always in that order — regardless of which of the three concurrent tasks actually finishes first, second, or third, due to the randomized processing delay.

## 6. Walkthrough

Tracing `SplitThenResequenceDemo` in execution order:

1. Three tasks are submitted to a thread pool, each carrying its original sequence number (1, 2, or 3) and each sleeping a random duration before sending its uppercased result to `processed` — this randomness means completion order is unpredictable across runs.
2. Whichever task finishes first (say, `seq=2`, "BODY") sends its message; the resequencer-shaped subscriber buffers it under key `2`, but `nextExpected` is still `1`, so the `while` loop's condition (`buffer.containsKey(1)`) is false — nothing is released yet.
3. If `seq=3` ("CONCLUSION") finishes next, it's buffered under key `3` — still no release, since `nextExpected` remains `1`.
4. Once `seq=1` ("INTRO") finally finishes and is buffered, the `while` loop's condition becomes true: it removes and prints entry `1`, increments `nextExpected` to `2`, then immediately checks again — entry `2` is *already* buffered (from step 2), so it releases that too, increments to `3`, checks again, finds entry `3` already buffered (from step 3), and releases that as well — all three release in one pass, back-to-back, once the missing prefix element finally arrives.
5. Each release calls `done.countDown()`, and once all three have been released, the main thread's `done.await()` unblocks.
6. The `synchronized (lock)` block ensures this buffer-and-release logic itself runs atomically even though multiple pool threads could call `processed`'s subscriber concurrently — without it, two threads could race on reading/updating `nextExpected`, potentially releasing out of order or double-releasing.

```
task(seq=2) finishes first  -> buffer={2}          nextExpected=1  -> no release (1 missing)
task(seq=3) finishes second -> buffer={2,3}          nextExpected=1  -> no release (1 missing)
task(seq=1) finishes last   -> buffer={1,2,3}         nextExpected=1  -> release 1, then 2, then 3 (all in one pass)
```

## 7. Gotchas & takeaways

> A `Resequencer` buffering an incomplete sequence (waiting on a message that will never arrive, e.g. `seq=2` in a 3-item group where the task producing it crashed) holds every later-arriving message hostage forever, exactly like `Aggregator`'s unbounded-wait hazard (card 0025) — a single missing message blocks the release of everything after it in the sequence, not just itself. Configure a timeout/expiry strategy for incomplete groups in production for the same reason `Aggregator` needs one.

- `Resequencer` reorders a stream of correlated, sequence-numbered messages back into original order, releasing the same count of messages it received — unlike `Aggregator` (card 0025), it doesn't combine them into one.
- Use it when concurrent or unordered upstream processing needs strict per-group ordering restored before a downstream step that assumes sequential order.
- With partial-sequence release enabled, a resequencer releases the longest available in-order prefix as soon as it exists, rather than waiting for the entire group — reducing latency for early-arriving items.
- A single missing sequence number blocks release of every later item in that group; always pair with a timeout/expiry strategy in production.
- `Resequencer` and `Aggregator` share the same underlying correlation/grouping machinery, differing only in what happens at release time: reorder-and-pass-through versus combine-into-one.
