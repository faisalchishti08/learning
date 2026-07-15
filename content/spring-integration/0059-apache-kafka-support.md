---
card: spring-integration
gi: 59
slug: apache-kafka-support
title: "Apache Kafka support"
---

## 1. What it is

Kafka support (`Kafka.inboundChannelAdapter(...)`/`Kafka.outboundChannelAdapter(...)`, built on Spring for Apache Kafka) connects a flow to a Kafka cluster. Unlike JMS's queues (card 0057, messages removed once consumed) or AMQP's exchange-routed queues (card 0058), a Kafka *topic* is a durable, ordered, append-only log, partitioned across multiple brokers — consumers don't remove messages when reading them; instead, each independent consumer group tracks its own read position (*offset*) within the log, meaning the same message can be re-read by re-setting that offset, and multiple independent consumer groups can each read the entire topic from the beginning, completely independently of one another.

## 2. Why & when

You reach for Kafka support specifically when the integration point is a Kafka cluster, or when Kafka's log-based, replay-capable model fits the use case better than a traditional message broker's consume-once model:

- **You're integrating with an existing Kafka-based event streaming platform** — Kafka is a very common backbone for event-driven microservices architectures, and Kafka support lets a flow produce to and consume from Kafka topics directly.
- **A message needs to be replayable or re-processed** — because Kafka doesn't remove messages on consumption, a consumer can reset its offset and re-read historical messages (within the topic's retention window), useful for reprocessing after a bug fix, backfilling a new downstream system, or recovering from a consumer-side failure without any data loss.
- **Ordering within a partition, combined with horizontal scalability across partitions, is needed** — Kafka guarantees strict ordering *within* a single partition, while a topic's multiple partitions allow parallel consumption across a consumer group's members, a specific ordering/throughput tradeoff neither a plain JMS queue nor an AMQP queue provides in quite the same shape.

## 3. Core concept

Think of a Kafka topic like a shared, append-only ledger book that anyone can read from any page they choose, as opposed to JMS's post office box (card 0057), where a letter is gone the moment it's picked up. Multiple different readers (consumer groups) can each keep their own personal bookmark in the same ledger, flipping back to re-read earlier pages whenever they need to, without affecting anyone else's bookmark or removing any content from the book — the ledger itself just keeps growing as new entries are appended, and old pages remain readable until the book's retention policy eventually discards them.

```java
@Bean
public IntegrationFlow kafkaOutboundFlow(KafkaTemplate<String, Order> kafkaTemplate) {
    return IntegrationFlow.from("outgoingOrders")
        .handle(Kafka.outboundChannelAdapter(kafkaTemplate)
            .topic("orders")
            .messageKey(m -> ((Order) m.getPayload()).id())) // same key -> same partition -> preserves ORDER
        .get();
}

@Bean
public IntegrationFlow kafkaInboundFlow(ConsumerFactory<String, Order> consumerFactory) {
    return IntegrationFlow.from(Kafka.messageDrivenChannelAdapter(consumerFactory, "orders"))
        .handle((Order order, headers) -> orderService.process(order))
        .get();
}
```

The `messageKey` on the outbound side is what determines which partition a given message lands in — messages with the same key always go to the same partition, which is what preserves their relative order (Kafka only guarantees ordering *within* a partition, not across the whole topic).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Kafka topic is a partitioned, append-only log; messages with the same key land in the same partition, preserving order within that partition; multiple independent consumer groups can each read the whole topic at their own pace and offset">
  <rect x="20" y="30" width="180" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="52" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">partition 0: [m1, m3, m5, ...]</text>
  <rect x="20" y="75" width="180" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="97" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">partition 1: [m2, m4, ...]</text>
  <text x="110" y="18" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">topic: orders (append-only log)</text>

  <line x1="200" y1="50" x2="270" y2="40" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#kf1)"/>
  <line x1="200" y1="50" x2="270" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#kf1)"/>

  <rect x="280" y="15" width="160" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="39" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">consumer group A (offset=3)</text>

  <rect x="280" y="75" width="160" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="360" y="99" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">consumer group B (offset=1)</text>

  <text x="360" y="140" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">both groups read the SAME log independently, at their OWN offsets</text>

  <defs>
    <marker id="kf1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Messages persist in the log regardless of consumption; independent consumer groups each track their own read position without affecting each other.

## 5. Runnable example

The scenario: an order-events topic feeding multiple independent consumer groups, simulated with an in-memory append-only log standing in for a real Kafka broker, starting with a basic append-and-read demonstration, then key-based partitioning preserving per-key order, and finally two independent consumer groups reading the same log at their own separate offsets, including a replay.

### Level 1 — Basic

```java
// KafkaLogBasicsDemo.java
// Simulates a Kafka topic as an in-memory append-only list standing in for a real broker,
// since connecting to an actual Kafka cluster requires external infrastructure.
import java.util.*;

public class KafkaLogBasicsDemo {
    static List<String> topicLog = new ArrayList<>(); // an append-only "log" — nothing is ever removed

    static void produce(String message) {
        topicLog.add(message);
        System.out.println("Appended to log (offset " + (topicLog.size() - 1) + "): " + message);
    }

    static String consumeAt(int offset) {
        return topicLog.get(offset); // reading does NOT remove or modify the log at all
    }

    public static void main(String[] args) {
        produce("order-1-created");
        produce("order-2-created");
        produce("order-1-shipped");

        System.out.println("\nConsumer reads offset 0: " + consumeAt(0));
        System.out.println("Consumer reads offset 0 AGAIN: " + consumeAt(0) + " (still there — reading doesn't remove it)");
    }
}
```

How to run: `java KafkaLogBasicsDemo.java`. Expected output: three "Appended to log" lines with increasing offsets, then `Consumer reads offset 0: order-1-created` and `Consumer reads offset 0 AGAIN: order-1-created (still there — reading doesn't remove it)` — reading the same offset twice returned the identical message both times, unlike a JMS queue (card 0057), where consuming a message removes it from the destination.

### Level 2 — Intermediate

Key-based partitioning: messages sharing the same key land in the same partition, preserving their relative order, while messages with different keys can land in different partitions with no ordering guarantee relative to each other.

```java
// KeyedPartitioningDemo.java
import java.util.*;

public class KeyedPartitioningDemo {
    static int numPartitions = 2;
    static Map<Integer, List<String>> partitions = new HashMap<>();

    static int partitionFor(String key) {
        return Math.abs(key.hashCode()) % numPartitions; // same key -> ALWAYS the same partition
    }

    static void produce(String key, String message) {
        int partition = partitionFor(key);
        partitions.computeIfAbsent(partition, p -> new ArrayList<>()).add(message);
    }

    public static void main(String[] args) {
        // messages for order-1 and order-2, interleaved in send order
        produce("order-1", "order-1: created");
        produce("order-2", "order-2: created");
        produce("order-1", "order-1: paid");
        produce("order-2", "order-2: paid");
        produce("order-1", "order-1: shipped");

        System.out.println("Partition " + partitionFor("order-1") + " (order-1's messages, IN ORDER): "
            + partitions.get(partitionFor("order-1")));
        System.out.println("Partition " + partitionFor("order-2") + " (order-2's messages, IN ORDER): "
            + partitions.get(partitionFor("order-2")));
    }
}
```

How to run: `java KeyedPartitioningDemo.java`. Expected output (partition numbers depend on hash values, but the ordering guarantee holds regardless): each order's own messages appear in their partition in exactly the order they were produced — `order-1`'s three events (`created`, `paid`, `shipped`) appear in that exact sequence within whichever partition `order-1`'s key hashes to, since same-key messages always land in the same partition, and within a partition, Kafka never reorders.

### Level 3 — Advanced

Two independent consumer groups reading the same log at their own separate offsets, including one group replaying from an earlier offset — demonstrating that consumption never affects the underlying log or any other consumer group's independent position within it.

```java
// IndependentConsumerGroupsDemo.java
import java.util.*;

public class IndependentConsumerGroupsDemo {
    static List<String> topicLog = new ArrayList<>();
    static Map<String, Integer> groupOffsets = new HashMap<>(); // EACH group tracks its OWN offset

    static void produce(String message) { topicLog.add(message); }

    static String consumeNext(String groupId) {
        int offset = groupOffsets.getOrDefault(groupId, 0);
        if (offset >= topicLog.size()) return null;
        String message = topicLog.get(offset);
        groupOffsets.put(groupId, offset + 1); // ONLY this group's offset advances
        return message;
    }

    public static void main(String[] args) {
        produce("order-1-created");
        produce("order-1-paid");
        produce("order-1-shipped");

        System.out.println("Group 'fulfillment-service' consuming:");
        System.out.println("  " + consumeNext("fulfillment-service"));
        System.out.println("  " + consumeNext("fulfillment-service"));

        System.out.println("Group 'analytics-service' consuming (INDEPENDENTLY, unaffected by fulfillment's position):");
        System.out.println("  " + consumeNext("analytics-service"));

        // fulfillment-service REPLAYS from the beginning — resets ITS OWN offset, nobody else affected
        groupOffsets.put("fulfillment-service", 0);
        System.out.println("\nGroup 'fulfillment-service' REPLAYING from offset 0:");
        System.out.println("  " + consumeNext("fulfillment-service"));

        System.out.println("Group 'analytics-service' continues from where it left off (offset 1), UNAFFECTED:");
        System.out.println("  " + consumeNext("analytics-service"));
    }
}
```

How to run: `java IndependentConsumerGroupsDemo.java`. Expected output: `fulfillment-service` reads `order-1-created` then `order-1-paid`; `analytics-service`, starting fresh, independently reads `order-1-created` from its own offset 0 (unaffected by fulfillment's position at offset 2); after `fulfillment-service` resets to offset 0 and replays, it re-reads `order-1-created` again; and `analytics-service`, whose own offset was never touched by fulfillment's reset, continues correctly from its own offset 1, reading `order-1-paid` — each group's position is completely independent, and replaying one group's offset has zero effect on any other group or on the underlying log itself.

## 6. Walkthrough

Tracing `IndependentConsumerGroupsDemo` in execution order:

1. Three messages are appended to `topicLog` before any consumption happens — `groupOffsets` starts empty, meaning both consumer groups implicitly begin at offset `0`.
2. `consumeNext("fulfillment-service")` is called twice: the first call reads `topicLog.get(0)` (`"order-1-created"`) and advances `groupOffsets["fulfillment-service"]` to `1`; the second call reads `topicLog.get(1)` (`"order-1-paid"`) and advances that same group's offset to `2` — only `fulfillment-service`'s own tracked offset changed across these two calls.
3. `consumeNext("analytics-service")` is called for the first time — since `groupOffsets` has no entry for `"analytics-service"` yet, `getOrDefault(groupId, 0)` returns `0`, so this call reads `topicLog.get(0)` — the *same* first message `fulfillment-service` already read two steps ago — completely independently, since `analytics-service` has its own separate offset entry.
4. The code explicitly resets `groupOffsets.put("fulfillment-service", 0)`, simulating an operator or application deciding to replay `fulfillment-service`'s consumption from the beginning — this only touches the `"fulfillment-service"` key in the map; `"analytics-service"`'s entry (currently `1`) is untouched.
5. `consumeNext("fulfillment-service")` is called again — it now reads from the *reset* offset `0`, re-reading `"order-1-created"` a second time from `fulfillment-service`'s perspective, then advancing its offset to `1` again.
6. `consumeNext("analytics-service")` is called one more time — since its offset was never touched by `fulfillment-service`'s reset, it correctly reads from its own offset `1` (`"order-1-paid"`), continuing exactly where it had left off, completely oblivious to the fact that another consumer group had just replayed part of the log.

```
topicLog: [order-1-created, order-1-paid, order-1-shipped]   (never mutated by reads)

fulfillment-service offset: 0 -> read[0] -> 1 -> read[1] -> 2 -> RESET to 0 -> read[0] AGAIN -> 1
analytics-service    offset: 0 -> read[0] -> 1 -> (untouched by fulfillment's reset) -> read[1] -> 2
```

## 7. Gotchas & takeaways

> Choosing a message key purely for even load distribution across partitions (e.g., a random or round-robin key) sacrifices Kafka's per-key ordering guarantee entirely — if a use case genuinely needs all events for a given entity (an order, a user) processed in order, the key *must* be that entity's identifier, even if it means some partitions receive more traffic than others for particularly active entities. There's a real tradeoff between perfectly even partition load and preserving meaningful per-entity ordering, and it needs to be a deliberate choice, not an accident of whatever key happened to be convenient.

- A Kafka topic is a durable, partitioned, append-only log — unlike JMS queues (card 0057) or AMQP queues (card 0058), consuming a message doesn't remove it; consumers track their own independent read position (offset) within the log.
- Use Kafka support when replayability, independent multi-consumer-group reading of the same event stream, or the specific ordering-within-partition/parallelism-across-partitions tradeoff fits the use case.
- Messages sharing the same key always land in the same partition, preserving their relative order; messages with different keys may land in different partitions, with no ordering guarantee across partitions.
- Multiple independent consumer groups can each read the entire topic at their own pace and offset, completely unaffected by each other — resetting one group's offset to replay history has zero effect on any other group or on the underlying log.
- Choosing a message key is a genuine design decision balancing per-entity ordering against even partition load distribution — this tradeoff should be made deliberately based on the actual ordering requirements of the data.
