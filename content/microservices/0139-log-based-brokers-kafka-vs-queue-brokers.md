---
card: microservices
gi: 139
slug: log-based-brokers-kafka-vs-queue-brokers
title: "Log-based brokers (Kafka) vs queue brokers"
---

## 1. What it is

Log-based brokers (Kafka being the dominant example) and traditional queue brokers (RabbitMQ, ActiveMQ, and similar) both move messages from producers to consumers, but differ fundamentally in the underlying storage model: a queue broker treats a message as consumed and typically removes it once delivered and acknowledged, while a log-based broker retains every message in an append-only, [replayable](0136-replayability-of-event-streams.md) log, tracking each consumer's read position (offset) independently rather than deleting anything on read.

## 2. Why & when

These two models optimize for genuinely different things. A queue broker's per-message tracking (which consumer has it, has it been acked, does it need redelivery) is well-suited to complex per-message routing, priority queues, and fine-grained delivery guarantees for individual units of work — think task queues, RPC-style request/reply, or work that needs sophisticated routing rules. A log-based broker's simpler, sequential, high-throughput append-and-read model trades away that per-message routing sophistication for very high throughput, natural [replayability](0136-replayability-of-event-streams.md), and [ordering guarantees](0119-message-ordering-guarantees.md) within a partition — well suited to event streaming, [event sourcing](0130-event-sourcing-as-communication.md), and multiple independent consumers needing the full history.

Reach for a queue broker when the workload is genuinely queue-shaped: discrete tasks, complex routing rules, request/reply patterns, or scenarios needing sophisticated per-message delivery guarantees. Reach for a log-based broker when the workload is stream-shaped: a continuous flow of events multiple different consumers need to read (possibly at different times, possibly replaying history), especially at high volume where throughput matters more than per-message routing flexibility.

## 3. Core concept

A queue broker's core primitive is "give me the next unclaimed message and let me acknowledge it"; a log-based broker's core primitive is "let me read from a specific position in this ordered, retained log, and let me track my own position myself."

```java
// queue broker mental model: messages disappear once claimed and acked
Message msg = queueBroker.receive();  // removes it from availability to others
msg.ack();                             // and now it's gone entirely

// log-based broker mental model: messages stay; the CONSUMER tracks its own offset
long myOffset = 1057;
List<Event> batch = logBroker.readFrom("order-events", partition = 3, offset = myOffset);
myOffset += batch.size(); // I track my own progress; the log itself never shrinks
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Queue broker: messages are removed from the queue once claimed and acknowledged. Log-based broker: messages remain in an append-only log after being read; each consumer tracks its own offset independently">
  <text x="150" y="20" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Queue broker</text>
  <rect x="30" y="40" width="240" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">[msg1] [msg2] [msg3]</text>
  <text x="150" y="95" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">claimed msg REMOVED from queue</text>

  <text x="480" y="20" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Log-based broker</text>
  <rect x="360" y="40" width="240" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">[e1] [e2] [e3] [e4] [e5]</text>
  <text x="420" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">consumer A: offset 2</text>
  <text x="540" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">consumer B: offset 5</text>
  <text x="480" y="115" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">all 5 events remain, each consumer's offset is independent</text>

  <defs>
    <marker id="arr22" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Queue brokers empty as they're consumed; log-based brokers retain everything, with progress tracked per consumer.

## 5. Runnable example

Scenario: a stock-price-tick processing system implemented first with a queue-broker mental model (showing that history vanishes once consumed), then reimplemented with a log-based mental model (showing retention and per-consumer offsets), and finally demonstrating the log-based model's key advantage — a slow consumer falling behind never blocks a fast one, and a new consumer can join and read history that a queue would have already discarded.

### Level 1 — Basic

```java
// File: QueueBrokerModel.java -- consumed messages are GONE; a second consumer
// competing for the SAME queue only gets what's left, never a full independent view.
import java.util.*;

public class QueueBrokerModel {
    public static void main(String[] args) {
        Deque<String> queue = new ArrayDeque<>(List.of("tick:100.5", "tick:101.2", "tick:100.9"));

        System.out.println("consumer-fast claiming and acking messages:");
        while (!queue.isEmpty()) {
            String msg = queue.poll(); // claimed AND removed -- gone for everyone else
            System.out.println("  claimed & acked: " + msg);
        }

        System.out.println("queue now: " + queue + " -- a SECOND consumer wanting its OWN full view of all 3 ticks is out of luck.");
    }
}
```

**How to run:** `javac QueueBrokerModel.java && java QueueBrokerModel` (JDK 17+).

Once `consumer-fast` claims and acks every message, nothing remains — a queue broker has no notion of a second, independent reader wanting to see the same messages again.

### Level 2 — Intermediate

```java
// File: LogBasedBrokerModel.java -- events are RETAINED; two consumers each get
// their OWN full, independent view via separately-tracked offsets.
import java.util.*;

public class LogBasedBrokerModel {
    static class Log {
        private final List<String> events = new ArrayList<>(); // append-only, NEVER shrinks on read
        void append(String e) { events.add(e); }
        List<String> readFrom(long offset) { return offset < events.size() ? events.subList((int) offset, events.size()) : List.of(); }
    }

    static class Consumer {
        final String name;
        long offset = 0; // THIS consumer's own tracked position
        Consumer(String name) { this.name = name; }
        void readAvailable(Log log) {
            List<String> batch = log.readFrom(offset);
            for (String e : batch) System.out.println("[" + name + ", offset " + offset++ + "] " + e);
        }
    }

    public static void main(String[] args) {
        Log log = new Log();
        log.append("tick:100.5"); log.append("tick:101.2"); log.append("tick:100.9");

        Consumer consumerFast = new Consumer("consumer-fast");
        Consumer consumerSlow = new Consumer("consumer-slow"); // hasn't read anything YET
        consumerFast.readAvailable(log);

        System.out.println("consumer-slow hasn't read yet -- but the events are STILL THERE:");
        consumerSlow.readAvailable(log); // gets its OWN full view, independent of consumer-fast

        System.out.println("Both consumers saw all 3 ticks, independently, from the SAME retained log.");
    }
}
```

**How to run:** `javac LogBasedBrokerModel.java && java LogBasedBrokerModel` (JDK 17+).

Expected output:
```
[consumer-fast, offset 0] tick:100.5
[consumer-fast, offset 1] tick:101.2
[consumer-fast, offset 2] tick:100.9
consumer-slow hasn't read yet -- but the events are STILL THERE:
[consumer-slow, offset 0] tick:100.5
[consumer-slow, offset 1] tick:101.2
[consumer-slow, offset 2] tick:100.9
```

Unlike Level 1, `consumer-slow` gets its own complete view of all three events, entirely independent of what `consumer-fast` already read.

### Level 3 — Advanced

```java
// File: SlowConsumerNeverBlocksFast.java -- a genuinely slow consumer falling
// behind never blocks a fast one, AND a brand-new consumer can join and read
// history a queue broker would have already discarded.
import java.util.*;

public class SlowConsumerNeverBlocksFast {
    static class Log {
        private final List<String> events = new ArrayList<>();
        void append(String e) { events.add(e); }
        List<String> readFrom(long offset) { return offset < events.size() ? events.subList((int) offset, events.size()) : List.of(); }
        int size() { return events.size(); }
    }

    static class Consumer {
        final String name;
        long offset = 0;
        Consumer(String name) { this.name = name; }
        void readAvailable(Log log) {
            List<String> batch = log.readFrom(offset);
            for (String e : batch) offset++;
            System.out.println("[" + name + "] caught up to offset " + offset + " (read " + batch.size() + " new event(s))");
        }
    }

    public static void main(String[] args) {
        Log log = new Log();
        Consumer fastAnalytics = new Consumer("fast-analytics");
        Consumer slowMlPipeline = new Consumer("slow-ml-pipeline"); // deliberately falls behind

        // simulate 5 ticks arriving; fast-analytics reads after EVERY tick, slow-ml-pipeline only occasionally
        for (int i = 1; i <= 5; i++) {
            log.append("tick:" + (100 + i * 0.3));
            fastAnalytics.readAvailable(log); // stays fully caught up every time
            if (i == 5) slowMlPipeline.readAvailable(log); // only catches up once, at the very end
        }

        System.out.println("Log still contains all " + log.size() + " ticks. slow-ml-pipeline fell behind for 4 ticks, then caught up in ONE read of all of them.");
        System.out.println("fast-analytics was NEVER blocked or slowed down by slow-ml-pipeline's lag -- their offsets are fully independent.");

        // a BRAND NEW consumer, joining now, can still read the FULL history --
        // a queue broker would have discarded these the moment fast-analytics acked them
        Consumer newDashboard = new Consumer("new-dashboard");
        newDashboard.readAvailable(log);
    }
}
```

**How to run:** `javac SlowConsumerNeverBlocksFast.java && java SlowConsumerNeverBlocksFast` (JDK 17+).

Expected output (abbreviated for the loop, full run shows 5 fast-analytics lines):
```
[fast-analytics] caught up to offset 1 (read 1 new event(s))
[fast-analytics] caught up to offset 2 (read 1 new event(s))
[fast-analytics] caught up to offset 3 (read 1 new event(s))
[fast-analytics] caught up to offset 4 (read 1 new event(s))
[fast-analytics] caught up to offset 5 (read 1 new event(s))
[slow-ml-pipeline] caught up to offset 5 (read 5 new event(s))
Log still contains all 5 ticks. slow-ml-pipeline fell behind for 4 ticks, then caught up in ONE read of all of them.
fast-analytics was NEVER blocked or slowed down by slow-ml-pipeline's lag -- their offsets are fully independent.
[new-dashboard] caught up to offset 5 (read 5 new event(s))
```

## 6. Walkthrough

1. **Level 1** — `queue.poll()` both claims and removes each message in a single operation; by the time `consumer-fast`'s loop ends, `queue` is empty, structurally preventing any second consumer from ever seeing what was there.
2. **Level 2, retained storage** — `Log.append` only ever adds to `events`; `readFrom(offset)` is a pure, non-destructive read using `subList`, meaning any consumer, at any time, can ask for everything from any offset onward.
3. **Level 2, independent per-consumer offsets** — `consumerFast` and `consumerSlow` are two separate `Consumer` objects, each with its own `offset` field starting at 0; `consumerFast.readAvailable(log)` advances only `consumerFast.offset`, leaving `consumerSlow.offset` untouched at 0.
4. **Level 2, both get full, independent views** — when `consumerSlow.readAvailable(log)` finally runs, it reads from its own offset 0 and receives all three events, completely unaffected by the fact that `consumerFast` already read (but did not remove) those same three events.
5. **Level 3, a genuinely uneven consumption pattern** — the loop appends one tick at a time and has `fastAnalytics` read after every single append, keeping it always caught up, while `slowMlPipeline` only reads once, after all five ticks have been appended.
6. **Level 3, the slow consumer's single catch-up read** — `slowMlPipeline.readAvailable(log)` is called only on the final iteration, and its single call returns all five accumulated events in one batch (`read 5 new event(s)`), because nothing was ever discarded while it was "behind" — there was never a queue with limited capacity being exceeded, just a log patiently waiting to be read.
7. **Level 3, the two payoffs demonstrated together** — `fastAnalytics`'s five separate, prompt catch-ups show that a fast consumer's throughput is never gated by a slower one sharing the same log; `newDashboard`, created and reading for the first time only *after* all five ticks were already appended and already read by the other two consumers, still successfully retrieves the complete history in its first call — exactly the retention property a queue broker's destructive read model cannot offer.

## 7. Gotchas & takeaways

> **Gotcha:** a log-based broker's retained-history model means storage grows continuously unless bounded by a retention policy (time-based or size-based) — unlike a queue broker, where successful consumption naturally keeps storage small, a log-based broker needs deliberate retention configuration or storage will grow without bound.

- Queue brokers remove messages once claimed and acknowledged; log-based brokers retain messages in an append-only log and let each consumer track its own read position independently.
- Queue brokers suit complex per-message routing, task distribution, and request/reply patterns; log-based brokers suit high-throughput event streaming, multiple independent readers, and workloads needing [replayability](0136-replayability-of-event-streams.md).
- A slow consumer reading from a log-based broker never blocks or is blocked by a faster consumer, since their read positions are fully independent — this isn't automatically true of every queue broker's competing-consumers model.
- A brand-new consumer can join a log-based broker and read the full retained history; a queue broker has typically already discarded anything already claimed and acknowledged by existing consumers.
- Log-based brokers require deliberate retention policy configuration to bound storage growth, a concern queue brokers largely avoid by design.
