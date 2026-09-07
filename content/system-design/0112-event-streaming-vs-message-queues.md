---
card: system-design
gi: 112
slug: event-streaming-vs-message-queues
title: Event streaming vs message queues
---

## 1. What it is

A traditional **message queue** treats a message as a task: once a consumer processes and acknowledges it, the message is typically removed from the queue for good. **Event streaming** (as in Apache Kafka) treats a message as a durable, ordered record on an append-only log: it stays on the log for a configured retention period regardless of whether any consumer has read it, and any consumer can read from any position in that log, including replaying messages from the past.

## 2. Why & when

Choose a message queue when messages represent one-off tasks to be done once and then discarded — send this email, process this order — and you do not need any consumer to look at a message again after it is handled. Choose event streaming when messages represent facts about things that happened, which multiple consumers may want to read independently, at different times, and possibly more than once — for example, replaying all of last week's clicks to rebuild an analytics dashboard, or letting a brand-new service catch up on the full history of an event type it did not exist to consume when the events first occurred.

## 3. Core concept

- **Consumption model:** a queue message is generally consumed once, by one consumer (see [point-to-point](0110-message-queues-point-to-point.md)), then gone. A stream's log entry stays put; a consumer reads it by tracking its own position (an **offset**) in the log, independent of any other consumer's position.
- **Replay:** a stream consumer can rewind its offset and re-read messages it already processed, or a brand-new consumer can start from the very beginning of the log — a queue generally cannot do this once a message is acknowledged and removed.
- **Retention:** streams retain messages for a configured time or size limit (e.g. 7 days), regardless of consumption; queues typically retain a message only until it is acknowledged.
- **Ordering:** a stream's log preserves a strict append order per partition, which every consumer sees identically; a queue's ordering guarantee is often weaker once multiple competing consumers are involved.
- **Multiple independent consumer groups:** several completely independent consumer groups can each read the full stream at their own pace, each with its own separate offset — like the pub/sub fan-out model, but with a persistent, replayable history behind it.

## 4. Diagram

```
MESSAGE QUEUE:                          EVENT STREAM (append-only log):

  [msg1][msg2][msg3] -> consumed        [e1][e2][e3][e4][e5][e6] ...(retained)
  msg1 ack'd -> REMOVED from queue         ^offset=2 (group A: analytics)
  msg2 ack'd -> REMOVED from queue                  ^offset=4 (group B: fraud-check)

  Once consumed, gone.                   Both groups read the SAME log
                                          independently; e1-e6 all still
                                          present, replayable by a new group.
```
*Caption: a queue removes a message once consumed; a stream keeps every message on the log, letting independent consumer groups read it at their own pace, even in the past.*

## 5. Runnable example

**Level 1 — Basic.** Model a queue where messages disappear once consumed.

**Level 2 — Model a stream** where messages stay on the log and a consumer tracks its own offset.

**Level 3 — Replay.** A second, independent consumer group reads the same stream from the beginning, after the first group has already moved ahead.

```java
// StreamVsQueue.java
import java.util.*;

public class StreamVsQueue {

    public static void main(String[] args) {
        // Level 1: queue - messages are removed once consumed.
        Queue<String> queue = new LinkedList<>(List.of("order-1", "order-2", "order-3"));
        String consumed = queue.poll();
        System.out.println("queue consumed: " + consumed + ", queue now: " + queue);
        System.out.println("-> 'order-1' is GONE; no consumer can ever read it again from this queue");

        // Level 2: stream - an append-only log; consumers track their own offset, messages are NOT removed.
        List<String> log = new ArrayList<>(List.of("click-1", "click-2", "click-3", "click-4"));
        int analyticsOffset = 0;

        System.out.println("--- consumer group 'analytics' reads the stream ---");
        while (analyticsOffset < log.size()) {
            System.out.println("analytics reads offset " + analyticsOffset + ": " + log.get(analyticsOffset));
            analyticsOffset++;
        }
        System.out.println("log still has everything: " + log + " (nothing removed)");

        // Level 3: a brand-new, independent consumer group replays the SAME log from the beginning.
        int fraudCheckOffset = 0; // this group has its own, completely independent offset
        System.out.println("--- new consumer group 'fraud-check' starts from offset 0, even though analytics is already at offset " + analyticsOffset + " ---");
        while (fraudCheckOffset < 2) { // only reads the first 2 for this example
            System.out.println("fraud-check reads offset " + fraudCheckOffset + ": " + log.get(fraudCheckOffset));
            fraudCheckOffset++;
        }
        System.out.println("analytics offset unaffected by fraud-check: still " + analyticsOffset);
    }
}
```

**How to run:** save as `StreamVsQueue.java`, then run `java StreamVsQueue.java`.

## 6. Walkthrough

1. Level 1 uses a plain `Queue`; calling `poll()` both returns and removes `"order-1"`, so the queue afterward only holds `order-2` and `order-3` — once consumed, that message is unrecoverable from this queue.
2. Level 2 models a stream as an `ArrayList` that is never mutated by reading; the `analytics` consumer tracks its own `analyticsOffset` integer and advances it as it reads, but `log` itself stays fully intact and unchanged afterward.
3. The print confirming `log still has everything` demonstrates the core structural difference: reading from a stream does not remove anything, unlike the queue's `poll()`.
4. Level 3 introduces a second consumer group, `fraud-check`, with its own separate `fraudCheckOffset` starting at `0` — even though `analytics` has already advanced past every message.
5. `fraud-check` successfully reads `click-1` and `click-2` from the beginning of the same `log`, and the final print confirms `analytics`'s own offset was completely unaffected — proving the two consumer groups read the same durable log fully independently of each other.

## 7. Gotchas & takeaways

> Gotcha: because a stream retains data by time or size, not by "has everyone read this yet", a slow or stalled consumer group can find its needed messages have expired and been deleted by retention before it ever reads them. A queue has no equivalent risk, since messages simply wait until consumed — but a stream needs its retention window sized generously enough for the slowest consumer group you expect to support.

- A queue treats messages as one-time tasks, removed once consumed; a stream treats messages as durable, replayable facts on a retained, append-only log.
- Streams support multiple independent consumer groups reading the same data at their own pace, including a brand-new group starting from the very beginning.
- Choose streams for replay, audit, and multiple independent readers of history; choose queues for simple, one-time task distribution.
- Related concepts: [Brokers & topics/partitions](0113-brokers-topics-partitions.md) (how a stream's log is physically organized), [Publish/subscribe](0111-publish-subscribe.md) (the delivery pattern streams extend with durability and replay).
