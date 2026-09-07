---
card: system-design
gi: 113
slug: brokers-topics-partitions
title: Brokers & topics/partitions
---

## 1. What it is

A **broker** is a server that stores messages and routes them between producers and consumers; a cluster of brokers works together to handle a system's full messaging load. A **topic** is a named category of messages (e.g. `"orders"`, `"clicks"`). Each topic is split into **partitions** — ordered, independent logs that together make up the topic — so the topic's data and load can be spread across multiple brokers instead of living on just one.

## 2. Why & when

A single broker, and a single unsplit log, can only handle so much throughput and storage before it becomes a bottleneck — the same fundamental limit that motivates database sharding. Partitioning a topic across multiple brokers lets you scale a topic's write and read throughput horizontally, the same way sharding scales a database. You need to understand partitions specifically because they determine two things you must design around: how a message is routed to a partition (usually by a key, like sharding's partition key), and that ordering is only guaranteed *within* one partition, not across the whole topic.

## 3. Core concept

- **Broker:** one server in the cluster; it stores some partitions and serves the producers/consumers that read or write to them.
- **Topic:** a logical name a producer publishes to and a consumer subscribes to (e.g. `"orders"`).
- **Partition:** one ordered log within a topic. A topic with 4 partitions has 4 independent, ordered sequences of messages, which can live on different brokers.
- **Partition key:** producers usually specify a key (e.g. `orderId`); the same key always routes to the same partition (typically via `hash(key) % numPartitions`), guaranteeing all messages for that key stay in order relative to each other.
- **Ordering scope:** message order is only guaranteed within a single partition. Two messages in different partitions have no ordering guarantee relative to each other, even if produced by the same producer.
- **Parallelism via partitions:** within one consumer group, each partition is read by only one consumer instance at a time, so the number of partitions is the upper bound on how many consumer instances can process a topic in parallel.

## 4. Diagram

```
Topic "orders", 3 partitions, spread across 2 brokers:

  Broker 1                         Broker 2
  +----------------+               +----------------+
  | Partition 0     |               | Partition 2     |
  | [o1][o4][o7]... |               | [o3][o6][o9]... |
  +----------------+               +----------------+
  | Partition 1     |
  | [o2][o5][o8]... |
  +----------------+

  Producer sends order with key="cust-42" -> always routes to
  the SAME partition (e.g. partition 1) -> orders for cust-42
  stay strictly ordered relative to each other.
```
*Caption: a topic's partitions can live on different brokers; a message's key determines which single partition it lands in, and order is guaranteed only within that partition.*

## 5. Runnable example

**Level 1 — Basic.** Route messages to partitions by hashing their key, modeling a topic split across partitions.

**Level 2 — Per-partition ordering.** Confirm messages with the same key land in the same partition, in order; different keys may land elsewhere.

**Level 3 — Consumer parallelism bound.** Show that with 3 partitions, only 3 consumer instances can process a topic in parallel — a 4th sits idle.

```java
// BrokersTopicsPartitions.java
import java.util.*;

public class BrokersTopicsPartitions {

    static int numPartitions = 3;

    static int partitionFor(String key) {
        return Math.abs(key.hashCode()) % numPartitions;
    }

    public static void main(String[] args) {
        // Level 1 & 2: route messages by key; same key always lands on the same partition.
        List<Map.Entry<String, String>> messages = List.of(
            Map.entry("cust-42", "order-A"),
            Map.entry("cust-99", "order-B"),
            Map.entry("cust-42", "order-C"), // same key as order-A
            Map.entry("cust-42", "order-D")  // same key again
        );

        Map<Integer, List<String>> partitions = new TreeMap<>();
        for (var entry : messages) {
            int p = partitionFor(entry.getKey());
            partitions.computeIfAbsent(p, k -> new ArrayList<>()).add(entry.getValue());
        }
        System.out.println("partition layout: " + partitions);

        List<String> cust42Messages = partitions.get(partitionFor("cust-42"));
        System.out.println("all cust-42 messages landed in partition " + partitionFor("cust-42") + ": " + cust42Messages);
        System.out.println("-> order-A, order-C, order-D are all in the SAME partition, in the order they were produced");

        // Level 3: consumer parallelism is bounded by partition count.
        int numPartitionsForTopic = 3;
        int numConsumerInstances = 4;
        Map<Integer, Integer> consumerAssignedToPartition = new TreeMap<>();
        int idleConsumers = 0;
        for (int c = 0; c < numConsumerInstances; c++) {
            if (c < numPartitionsForTopic) consumerAssignedToPartition.put(c, c); // consumer c owns partition c
            else idleConsumers++;
        }
        System.out.println("consumer-to-partition assignment: " + consumerAssignedToPartition);
        System.out.println("idle consumers (more instances than partitions): " + idleConsumers);
    }
}
```

**How to run:** save as `BrokersTopicsPartitions.java`, then run `java BrokersTopicsPartitions.java`.

## 6. Walkthrough

1. `partitionFor` hashes a key modulo `numPartitions`, mirroring how a real broker like Kafka assigns a message to a partition using its key.
2. The `messages` list has three entries keyed `"cust-42"` and one keyed `"cust-99"`; the loop groups each message's value into the partition its key maps to, and `partitions` shows the resulting layout across the 3 partitions.
3. Looking up `partitions.get(partitionFor("cust-42"))` returns `[order-A, order-C, order-D]` in that exact order — confirming all messages for one key land in the same single partition, and preserve their production order there.
4. Level 3 assigns 4 consumer instances against a topic with only 3 partitions; the loop assigns consumers `0`, `1`, `2` to partitions `0`, `1`, `2`, and consumer `3` gets nothing.
5. The final counts show `idleConsumers = 1` — a direct, concrete demonstration that adding a 4th consumer instance did nothing for parallel throughput, since a topic's partition count is a hard ceiling on how many consumers within one group can work on it simultaneously.

## 7. Gotchas & takeaways

> Gotcha: if you need more consumer parallelism later, you must increase the topic's partition count — but doing so on an already-running topic reshuffles which key maps to which partition (since the modulo denominator changes), which can break the "same key always goes to the same partition, in order" guarantee for keys already in flight. Plan partition count generously up front, the same way you would plan a database's initial shard count.

- A broker stores and serves partitions; a topic is a logical name split into multiple ordered partitions, which can be spread across brokers for scale.
- A message's key determines its partition, guaranteeing strict order only for messages sharing that key, not across the whole topic.
- The number of partitions caps how many consumer instances in one consumer group can process a topic in parallel.
- Related concepts: [Hash-based sharding](0091-hash-based-sharding.md) (the same key-routing idea applied to databases), [Message ordering guarantees](0115-message-ordering-guarantees.md) (the per-partition ordering promise explained further), [Event streaming vs message queues](0112-event-streaming-vs-message-queues.md) (the broader model partitions belong to).
