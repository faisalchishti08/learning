---
card: system-design
gi: 115
slug: message-ordering-guarantees
title: Message ordering guarantees
---

## 1. What it is

**Message ordering** describes whether messages are guaranteed to be processed in the same sequence they were produced. Most real messaging systems only guarantee order **within a single partition** (or a single queue with one consumer) — never across an entire topic split into many partitions, and never across multiple unrelated queues.

## 2. Why & when

Some data genuinely depends on order: an "AccountCreated" event must be processed before an "AccountUpdated" event for the same account, or a stock's "PriceUpdated" events must be applied in sequence, not scrambled. You need to actively design for ordering — by routing related messages to the same partition using a shared key — any time out-of-order processing would produce a wrong result, not just a delayed one. If message order genuinely does not matter for your use case (independent, self-contained tasks), you can ignore this concern entirely and gain more parallelism by spreading messages freely across partitions.

## 3. Core concept

- **Ordering scope = one partition:** within [a single partition](0113-brokers-topics-partitions.md), messages are appended and read in strict order. Across different partitions of the same topic, there is no ordering relationship at all.
- **Guaranteeing order for related messages:** produce all messages for one logical entity (one `accountId`, one `orderId`) using the same key, so they always land in the same partition and are processed in the order they were sent.
- **Multiple consumers break ordering if misused:** if several consumer threads read from the *same* partition concurrently and process messages in parallel, they can finish out of order even though they received them in order — a single-threaded consumer per partition (or a per-key processing lock) is needed to actually preserve the guarantee end-to-end.
- **Global ordering does not scale:** forcing every message across an entire topic into one strict order requires a single partition (or a single queue with one consumer), which puts a hard ceiling on throughput — you trade parallelism for order.
- **Reordering causes:** network retries that resend an earlier message after a later one already arrived, or a producer sending to multiple partitions round-robin instead of by key, both break ordering guarantees if you needed one.

## 4. Diagram

```
Topic "account-events", partitioned by accountId:

  Partition 0 (accountId "acc-1" always routes here):
    [AccountCreated acc-1] -> [AccountUpdated acc-1] -> [AccountClosed acc-1]
    STRICT ORDER preserved - all 3 events for acc-1 land here, in sequence.

  Partition 1 (accountId "acc-2" always routes here):
    [AccountCreated acc-2] -> [AccountUpdated acc-2]

  NO ordering relationship between Partition 0's events and
  Partition 1's events - they can be processed in either relative order.
```
*Caption: strict order is guaranteed only within one partition; routing by a consistent key keeps one entity's events together and in sequence.*

## 5. Runnable example

**Level 1 — Basic.** Route events by key to partitions, and confirm one entity's events stay in order within its partition.

**Level 2 — Broken ordering from concurrent processing.** Process one partition's messages with multiple threads and show they can finish out of order.

**Level 3 — Fix: single-threaded processing per partition.** Restore correct order by processing each partition sequentially.

```java
// MessageOrdering.java
import java.util.*;
import java.util.concurrent.*;

public class MessageOrdering {

    static int partitionFor(String key, int numPartitions) {
        return Math.abs(key.hashCode()) % numPartitions;
    }

    public static void main(String[] args) throws InterruptedException {
        int numPartitions = 2;

        // Level 1: route events by accountId key; same account always lands in the same partition, in order.
        record Event(String accountId, String type) {}
        List<Event> events = List.of(
            new Event("acc-1", "Created"),
            new Event("acc-2", "Created"),
            new Event("acc-1", "Updated"),
            new Event("acc-1", "Closed")
        );

        Map<Integer, List<Event>> partitionLogs = new TreeMap<>();
        for (Event e : events) {
            int p = partitionFor(e.accountId(), numPartitions);
            partitionLogs.computeIfAbsent(p, k -> new ArrayList<>()).add(e);
        }
        int acc1Partition = partitionFor("acc-1", numPartitions);
        System.out.println("acc-1's events, in partition " + acc1Partition + ": " + partitionLogs.get(acc1Partition));
        System.out.println("-> Created, Updated, Closed - in the exact order they were produced");

        // Level 2: concurrent processing of ONE partition's messages breaks the effective order.
        List<Event> acc1Events = partitionLogs.get(acc1Partition);
        List<String> processedOrderConcurrent = Collections.synchronizedList(new ArrayList<>());
        ExecutorService pool = Executors.newFixedThreadPool(3);
        CountDownLatch latch = new CountDownLatch(acc1Events.size());
        for (Event e : acc1Events) {
            pool.submit(() -> {
                try { Thread.sleep(new Random().nextInt(20)); } catch (InterruptedException ignored) {} // simulated variable work time
                processedOrderConcurrent.add(e.type());
                latch.countDown();
            });
        }
        latch.await();
        pool.shutdown();
        System.out.println("processed order with 3 concurrent threads on ONE partition: " + processedOrderConcurrent);
        System.out.println("-> likely NOT [Created, Updated, Closed] - ordering broken by concurrent processing");

        // Level 3: fix - process the same partition's messages single-threaded, in sequence.
        List<String> processedOrderSequential = new ArrayList<>();
        for (Event e : acc1Events) {
            processedOrderSequential.add(e.type()); // one at a time, in the log's order
        }
        System.out.println("processed order single-threaded per partition: " + processedOrderSequential);
        System.out.println("-> [Created, Updated, Closed] - correct order restored");
    }
}
```

**How to run:** save as `MessageOrdering.java`, then run `java MessageOrdering.java`.

## 6. Walkthrough

1. Level 1 routes four events by `accountId` into 2 partitions using the same `partitionFor` hash used for topic partitioning; all three `acc-1` events land in the same partition, in their original production order, printed as `[Created, Updated, Closed]`.
2. Level 2 submits `acc-1`'s three events to a thread pool of 3 workers, each sleeping a random, short amount of time before recording that it "processed" its event — modeling three consumer threads racing to handle messages from the same partition concurrently.
3. Because each thread's random sleep can finish in any order, `processedOrderConcurrent` frequently comes out as something other than `[Created, Updated, Closed]` — for example, `[Updated, Created, Closed]` — demonstrating that reading messages in order does not guarantee *processing* them in order if multiple threads handle one partition's messages in parallel.
4. Level 3 processes the same `acc1Events` list with a plain sequential `for` loop, one event fully handled before the next starts.
5. `processedOrderSequential` always comes out as `[Created, Updated, Closed]`, showing that preserving order end-to-end requires not just reading a partition in order, but also processing that partition's messages one at a time, in that same order.

## 7. Gotchas & takeaways

> Gotcha: increasing consumer parallelism (adding threads, or adding partitions) is often the first instinct for scaling a messaging system, but doing so naively — without keeping each logical entity's messages confined to one partition and processed sequentially within it — silently breaks any ordering guarantee your application depends on. Verify which specific messages actually need order before parallelizing.

- Strict ordering is guaranteed only within a single partition or single-consumer queue, never across an entire topic or across queues.
- Routing related messages by a consistent key keeps them in the same partition, preserving their relative order.
- Concurrent processing of one partition's messages can still break effective order, even though the messages were read in order — a single-threaded (or per-key-locked) consumer is what actually preserves it.
- Related concepts: [Brokers & topics/partitions](0113-brokers-topics-partitions.md) (the physical structure this ordering guarantee is scoped to), [Idempotent consumers](0116-idempotent-consumers.md) (a related but separate concern about duplicate, not out-of-order, delivery).
