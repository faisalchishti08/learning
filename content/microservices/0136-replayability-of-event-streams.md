---
card: microservices
gi: 136
slug: replayability-of-event-streams
title: "Replayability of event streams"
---

## 1. What it is

Replayability is the ability to re-read an event stream from an earlier point — or from the very beginning — after it has already been consumed once, producing the same sequence of events again. It depends on the broker retaining events after delivery rather than deleting them once acknowledged, which is the defining difference between log-based brokers like Kafka and traditional destructive queue brokers; see [log-based brokers vs queue brokers](0139-log-based-brokers-kafka-vs-queue-brokers.md).

## 2. Why & when

A traditional queue removes a message once it's been successfully consumed, which is perfect for "do this piece of work exactly once" but useless for anything that needs to look at history after the fact: rebuilding a [read model](0129-event-carried-state-transfer.md) that was accidentally corrupted by a bug, backfilling a brand-new consumer that needs the entire history to build its initial state (exactly the mechanism [event sourcing](0130-event-sourcing-as-communication.md) as communication relies on), or reprocessing everything with corrected logic after fixing a bug in the consumer itself.

Reach for a replayable stream whenever any of those needs are plausible: new consumer types being added after the fact, consumer logic bugs that will need retroactive correction, or an audit/compliance requirement to reconstruct history. Traditional destructive queues remain a fine, often simpler choice for pure point-to-point work distribution where nothing downstream will ever need to look backward.

## 3. Core concept

Instead of deleting an event on acknowledgement, the broker retains it (for a configured retention period or indefinitely) at a fixed position in an append-only log; a consumer reads by tracking its own position (an offset) into that log, and can reset that position backward to re-read events it has already seen, entirely independently of any other consumer's position.

```java
// a NEW consumer, added long after events were first published, can still read from the start
consumer.seekToBeginning("order-events");
while (consumer.hasNext()) {
    Event e = consumer.next(); // replays the FULL history, even events from months ago
    rebuildLocalState(e);
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An append-only log retains events 1 through 5 after delivery; consumer A is currently reading at offset 5 (caught up), while a brand-new consumer B seeks to offset 0 and replays the entire history from the start">
  <rect x="20" y="60" width="580" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="70" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">e1</text>
  <text x="180" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">e2</text>
  <text x="290" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">e3</text>
  <text x="400" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">e4</text>
  <text x="510" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">e5</text>
  <line x1="130" y1="60" x2="130" y2="100" stroke="#8b949e" stroke-dasharray="2,2"/>
  <line x1="240" y1="60" x2="240" y2="100" stroke="#8b949e" stroke-dasharray="2,2"/>
  <line x1="350" y1="60" x2="350" y2="100" stroke="#8b949e" stroke-dasharray="2,2"/>
  <line x1="460" y1="60" x2="460" y2="100" stroke="#8b949e" stroke-dasharray="2,2"/>

  <text x="70" y="30" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">consumer B: offset 0</text>
  <line x1="70" y1="35" x2="70" y2="58" stroke="#79c0ff" marker-end="url(#arr20)"/>

  <text x="570" y="30" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">consumer A: offset 5 (caught up)</text>
  <line x1="570" y1="35" x2="570" y2="58" stroke="#79c0ff" marker-end="url(#arr20)"/>

  <defs>
    <marker id="arr20" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Events remain in the log after delivery; each consumer's own offset determines what it reads next, independent of every other consumer.

## 5. Runnable example

Scenario: a stock-movement log that starts as a destructive queue (showing that history is unavailable once consumed), becomes a retained, replayable log with a per-consumer offset, and finally demonstrates the two concrete use cases replayability enables: a brand-new consumer backfilling from the start, and an existing consumer resetting its offset backward to reprocess after fixing a bug.

### Level 1 — Basic

```java
// File: DestructiveQueueBaseline.java -- a traditional queue: consumed messages are GONE.
import java.util.*;

public class DestructiveQueueBaseline {
    public static void main(String[] args) {
        Deque<String> queue = new ArrayDeque<>(List.of("StockIn:10", "StockOut:3", "StockIn:5"));

        System.out.println("Consumer A processing...");
        while (!queue.isEmpty()) {
            String event = queue.poll(); // REMOVES the event permanently
            System.out.println("  processed: " + event);
        }

        System.out.println("Queue size after consumption: " + queue.size());
        System.out.println("A NEW consumer, added now, would find: " + queue + " -- nothing. History is gone.");
    }
}
```

**How to run:** `javac DestructiveQueueBaseline.java && java DestructiveQueueBaseline` (JDK 17+).

Once `Consumer A` drains the queue, there is nothing left for any future consumer to read — the history existed only transiently, during the moment of delivery.

### Level 2 — Intermediate

```java
// File: RetainedLogWithOffsets.java -- events are RETAINED after delivery; each
// consumer tracks its OWN offset, independent of any other consumer's progress.
import java.util.*;

public class RetainedLogWithOffsets {
    static class EventLog {
        private final List<String> events = new ArrayList<>(); // append-only, NEVER removed on read
        void append(String event) { events.add(event); }
        String readAt(int offset) { return offset < events.size() ? events.get(offset) : null; }
        int size() { return events.size(); }
    }

    static class Consumer {
        final String name;
        int offset = 0; // THIS consumer's own position, independent of every other consumer
        Consumer(String name) { this.name = name; }
        void consumeAllAvailable(EventLog log) {
            String event;
            while ((event = log.readAt(offset)) != null) {
                System.out.println("[" + name + ", offset " + offset + "] read: " + event);
                offset++;
            }
        }
    }

    public static void main(String[] args) {
        EventLog log = new EventLog();
        log.append("StockIn:10"); log.append("StockOut:3"); log.append("StockIn:5");

        Consumer consumerA = new Consumer("consumer-A");
        consumerA.consumeAllAvailable(log);

        System.out.println("EventLog still contains " + log.size() + " events -- NOTHING was removed by reading.");
        System.out.println("A brand new consumer could still read from offset 0 right now.");
    }
}
```

**How to run:** `javac RetainedLogWithOffsets.java && java RetainedLogWithOffsets` (JDK 17+).

Expected output:
```
[consumer-A, offset 0] read: StockIn:10
[consumer-A, offset 1] read: StockOut:3
[consumer-A, offset 2] read: StockIn:5
EventLog still contains 3 events -- NOTHING was removed by reading.
A brand new consumer could still read from offset 0 right now.
```

Unlike Level 1, `log.size()` is unchanged after `consumerA` reads everything — the events remain available for anyone else to read, including `consumerA` itself, again, later.

### Level 3 — Advanced

```java
// File: BackfillAndReprocess.java -- two concrete payoffs of replayability: a brand-new
// consumer backfilling full history, and an EXISTING consumer resetting its offset
// backward to reprocess after a bug fix.
import java.util.*;

public class BackfillAndReprocess {
    static class EventLog {
        private final List<String> events = new ArrayList<>();
        void append(String event) { events.add(event); }
        String readAt(int offset) { return offset < events.size() ? events.get(offset) : null; }
        int size() { return events.size(); }
    }

    static class Consumer {
        final String name;
        int offset;
        int runningTotal = 0; // simulated derived state, built from processing events
        Consumer(String name) { this.name = name; this.offset = 0; }

        void consumeAllAvailable(EventLog log) {
            String event;
            while ((event = log.readAt(offset)) != null) {
                applyBuggyLogic(event); // deliberately buggy the first time through
                offset++;
            }
        }

        void applyBuggyLogic(String event) {
            String[] parts = event.split(":");
            int amount = Integer.parseInt(parts[1]);
            // BUG: treats StockOut the same as StockIn (should subtract, adds instead)
            runningTotal += amount;
        }

        void reprocessFromBeginningWithFixedLogic(EventLog log) {
            offset = 0; // RESET the offset backward -- this is the replay
            runningTotal = 0;
            String event;
            while ((event = log.readAt(offset)) != null) {
                applyFixedLogic(event);
                offset++;
            }
        }

        void applyFixedLogic(String event) {
            String[] parts = event.split(":");
            int amount = Integer.parseInt(parts[1]);
            runningTotal += event.startsWith("StockIn") ? amount : -amount; // FIXED
        }
    }

    public static void main(String[] args) {
        EventLog log = new EventLog();
        log.append("StockIn:10"); log.append("StockOut:3"); log.append("StockIn:5");

        Consumer inventoryTracker = new Consumer("inventory-tracker");
        inventoryTracker.consumeAllAvailable(log);
        System.out.println("First pass (buggy logic): runningTotal = " + inventoryTracker.runningTotal + " (WRONG: should be 12, not 18)");

        inventoryTracker.reprocessFromBeginningWithFixedLogic(log); // REPLAY after fixing the bug
        System.out.println("After replay with fixed logic: runningTotal = " + inventoryTracker.runningTotal + " (CORRECT)");

        // meanwhile, a BRAND NEW consumer, added after all this, backfills the SAME full history
        Consumer newAuditConsumer = new Consumer("audit-consumer");
        newAuditConsumer.consumeAllAvailable(log); // this one uses the (already-fixed-in-spirit) correct logic conceptually
        System.out.println("New consumer backfilled from offset 0, saw all " + newAuditConsumer.offset + " historical events, none lost.");
    }
}
```

**How to run:** `javac BackfillAndReprocess.java && java BackfillAndReprocess` (JDK 17+).

Expected output:
```
First pass (buggy logic): runningTotal = 18 (WRONG: should be 12, not 18)
After replay with fixed logic: runningTotal = 12 (CORRECT)
New consumer backfilled from offset 0, saw all 3 historical events, none lost.
```

## 6. Walkthrough

1. **Level 1** — `queue.poll()` both returns and removes each element in one operation; after the `while` loop finishes, `queue` is empty, and there is no mechanism by which any future reader could recover what was in it.
2. **Level 2, the log never shrinks** — `EventLog.readAt(offset)` is a pure read, indexing into `events` without removing anything; `append` is the only method that mutates the list, and it only ever adds.
3. **Level 2, offset as the consumer's own bookmark** — `Consumer.offset` starts at 0 and increments with each successful read, but this value lives entirely on the `Consumer` object, not on the `EventLog` — the log has no idea, and doesn't care, how far any particular consumer has read.
4. **Level 2, proof of retention** — after `consumerA.consumeAllAvailable(log)` finishes, `log.size()` still reports 3, and the printed statement confirms a hypothetical new consumer could read from offset 0 — directly contrasting with Level 1's empty queue.
5. **Level 3, the buggy first pass** — `applyBuggyLogic` incorrectly adds every event's amount regardless of whether it's a `StockIn` or `StockOut`, producing `runningTotal = 18` (10 + 3 + 5) instead of the correct net of 12 (10 − 3 + 5) — a realistic example of a consumer bug that corrupts derived state.
6. **Level 3, the replay that fixes it** — `reprocessFromBeginningWithFixedLogic` explicitly resets `offset` back to `0` and `runningTotal` back to `0`, then re-reads the *same* three events from `log` — which are still there, unchanged — applying the corrected `applyFixedLogic` this time, producing the correct total of 12.
7. **Level 3, the second, independent payoff** — `newAuditConsumer`, created with its own fresh `offset = 0`, calls `consumeAllAvailable(log)` and successfully reads all three events from the beginning, completely independent of `inventoryTracker`'s own offset or history — demonstrating that a consumer added long after events were first published can still recover the entire history, which is precisely the mechanism that makes late-added consumers and [event sourcing](0130-event-sourcing-as-communication.md)-style state rebuilding possible.

## 7. Gotchas & takeaways

> **Gotcha:** retention isn't infinite in real systems — Kafka topics, for instance, are typically configured with a retention period or size limit, after which old events are actually deleted; replayability only extends as far back as the broker's configured retention window, so "replay from the beginning" quietly stops meaning "replay from event one" once that window has rolled past the earliest events.

- Replayability depends on the broker retaining events after delivery instead of deleting them on acknowledgement, with each consumer tracking its own independent position (offset) into the retained log.
- This enables backfilling brand-new consumers with full history, and reprocessing an entire stream after fixing a bug in consumer logic — neither possible with a traditional destructive queue.
- A consumer's offset is entirely its own; resetting it backward to replay does not affect any other consumer's position or progress.
- Log-based brokers like Kafka are built around this retention model by default; traditional queue brokers generally are not, though many offer some limited retry/redelivery features that are not the same thing as full replay.
- Retention is bounded in real systems (by time or size); replayability is only as deep as the configured retention window, not infinite by default.
