---
card: spring-boot
gi: 168
slug: apache-kafka
title: Apache Kafka
---

## 1. What it is

**Apache Kafka** is a distributed event-streaming platform — a high-throughput, fault-tolerant log of records. Spring Boot auto-configures Kafka support via `spring-boot-starter-kafka`, providing `KafkaTemplate` for producing, `@KafkaListener` for consuming, and auto-wired `KafkaAdmin` for topic management.

Unlike JMS/AMQP queues, Kafka keeps messages on disk for a configurable retention period. Any consumer can re-read past messages at any offset — the log is immutable.

## 2. Why & when

**Why Kafka over RabbitMQ:**
- **Throughput:** millions of messages per second, horizontally partitioned.
- **Replay:** consumers can rewind and re-process events from any point.
- **Ordering:** messages in a partition are strictly ordered.
- **Fan-out without queues:** multiple consumer groups each get the full stream independently.

**When to use:**
- Event sourcing, audit logs, activity feeds.
- Stream processing pipelines (Kafka Streams, Flink, Spark Streaming).
- Decoupling microservices where downstream consumers join or leave without affecting producers.

**Not ideal for:** simple task queues, request-reply, or environments where running Kafka is operationally prohibitive.

## 3. Core concept

Key abstractions:

- **Topic:** named category of records, split into **partitions**.
- **Partition:** ordered, immutable log segment. Parallelism unit — Kafka spreads partitions across brokers.
- **Offset:** integer position of a record within a partition. Consumers track their own offset.
- **Consumer group:** a set of consumers that divide partitions among themselves. Two groups both receive every message (fan-out is free).
- **Producer:** publishes records to a topic, optionally with a key to control which partition.

Spring Boot properties: `spring.kafka.bootstrap-servers`, `spring.kafka.consumer.group-id`, `spring.kafka.consumer.auto-offset-reset`.

## 4. Diagram

<svg viewBox="0 0 720 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Kafka producer writes to partitions of a topic; two consumer groups read independently">
  <!-- Producer -->
  <rect x="10" y="85" width="110" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="65" y="107" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Producer</text>
  <text x="65" y="123" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">KafkaTemplate</text>

  <!-- Arrow -->
  <line x1="125" y1="110" x2="185" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#ka)"/>

  <!-- Topic box -->
  <rect x="190" y="40" width="280" height="145" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="63" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Topic: orders</text>

  <!-- Partitions -->
  <rect x="210" y="72" width="240" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="330" y="92" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Partition 0 — [0][1][2][3]→</text>

  <rect x="210" y="108" width="240" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="330" y="128" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Partition 1 — [0][1][2]→</text>

  <rect x="210" y="144" width="240" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="330" y="164" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Partition 2 — [0][1]→</text>

  <!-- Arrows to consumers -->
  <line x1="475" y1="90" x2="545" y2="75" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#kb)"/>
  <line x1="475" y1="140" x2="545" y2="155" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#kb)"/>

  <!-- Consumer Group A -->
  <rect x="550" y="55" width="150" height="44" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="625" y="74" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Consumer Group A</text>
  <text x="625" y="89" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@KafkaListener group-id=A</text>

  <!-- Consumer Group B -->
  <rect x="550" y="133" width="150" height="44" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="625" y="152" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Consumer Group B</text>
  <text x="625" y="167" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@KafkaListener group-id=B</text>

  <text x="360" y="210" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Each group maintains its own offset — both groups receive every message independently</text>

  <defs>
    <marker id="ka" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="kb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Two consumer groups each read the full topic independently; partitions give intra-group parallelism.

## 5. Runnable example

```java
// KafkaDemo.java — simulates Kafka topic/partition/consumer-group model
// How to run: java KafkaDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add spring-boot-starter-kafka; use KafkaTemplate / @KafkaListener

import java.util.*;

public class KafkaDemo {

    // Partition is an ordered list of records (offset = index)
    static final List<List<String>> topic = new ArrayList<>();
    static final int NUM_PARTITIONS = 3;

    // Consumer group tracks offset per partition
    static final Map<String, int[]> groupOffsets = new HashMap<>();

    static {
        for (int i = 0; i < NUM_PARTITIONS; i++) topic.add(new ArrayList<>());
    }

    // Assign partition by key hash (same key always same partition — ordering guarantee)
    static void produce(String key, String value) {
        int partition = Math.abs(key.hashCode()) % NUM_PARTITIONS;
        topic.get(partition).add(value);
        System.out.printf("[KafkaTemplate] key='%s' -> partition=%d  value='%s'%n", key, partition, value);
    }

    static void consumeGroup(String groupId) {
        int[] offsets = groupOffsets.computeIfAbsent(groupId, k -> new int[NUM_PARTITIONS]);
        System.out.println("\n[@KafkaListener group='" + groupId + "']");
        for (int p = 0; p < NUM_PARTITIONS; p++) {
            List<String> partition = topic.get(p);
            while (offsets[p] < partition.size()) {
                System.out.printf("  partition=%d offset=%d  msg='%s'%n",
                        p, offsets[p], partition.get(offsets[p]));
                offsets[p]++;
            }
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Apache Kafka Demo ===\n");
        System.out.println("--- Producing messages ---");
        produce("user-1", "User 1 placed order");
        produce("user-2", "User 2 placed order");
        produce("user-1", "User 1 updated profile");
        produce("user-3", "User 3 placed order");
        produce("user-2", "User 2 cancelled order");

        // Consumer Group A reads all messages
        consumeGroup("analytics");

        // Consumer Group B also reads all messages independently (different group)
        consumeGroup("notifications");

        // Replay: Group A re-reads from offset 0 on partition 0
        System.out.println("\n--- Replay: analytics re-reads partition 0 from offset 0 ---");
        groupOffsets.get("analytics")[0] = 0;
        consumeGroup("analytics");
    }
}
```

**How to run:** `java KafkaDemo.java` — no broker needed.

## 6. Walkthrough

- **`produce`** hashes the key to pick a partition — same key always lands in same partition, preserving per-key ordering (critical: all user-1 events stay ordered).
- **`topic`** is a list of partition logs; each entry is an ordered, immutable list of records.
- **`groupOffsets`** tracks committed offsets per group per partition — each group is independent.
- **`consumeGroup("analytics")`** then **`consumeGroup("notifications")`** both read all messages. In real Kafka these are two separate applications.
- The replay block resets `analytics` group's partition-0 offset to 0, demonstrating Kafka's rewind capability — impossible with JMS/AMQP queues.

## 7. Gotchas & takeaways

> Kafka messages in the same **partition** are ordered; across partitions there is **no global ordering**. If you need all events for a user to be ordered, always use the same partition key (`userId`).

> `auto-offset-reset=earliest` is critical for new consumer groups that join after messages were already produced. Without it, new consumers miss all historical data.

- `spring.kafka.bootstrap-servers=localhost:9092` is the only required property.
- `@KafkaListener(topics = "orders", groupId = "my-service")` auto-starts a listener container.
- `KafkaTemplate.send(topic, key, value)` returns a `CompletableFuture` — check it to handle send failures.
- Consumers in the same group split partitions; add more consumer instances up to the partition count for parallelism.
- Use `spring.kafka.consumer.enable-auto-commit=false` and `AckMode.MANUAL` for at-least-once guarantees.
