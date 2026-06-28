---
card: spring-boot
gi: 169
slug: apache-pulsar
title: Apache Pulsar
---

## 1. What it is

**Apache Pulsar** is a cloud-native distributed messaging and streaming platform. Spring Boot 3.2+ auto-configures Pulsar via `spring-boot-starter-pulsar`, giving you `PulsarTemplate` for producing, `@PulsarListener` for consuming, and `PulsarAdmin` for topic management — with first-class reactive support via `ReactivePulsarTemplate`.

Pulsar separates the **broker** (stateless, handles routing) from **BookKeeper** (persistent storage), making it easier to scale each layer independently than Kafka's combined broker-storage model.

## 2. Why & when

**Pulsar vs Kafka:**
- **Geo-replication built-in:** Pulsar natively replicates topics across data centres without extra tooling.
- **Multi-tenancy:** namespaces and tenants are first-class — good for platforms serving multiple teams or customers.
- **Tiered storage:** automatically offload old data to object storage (S3, GCS) while the topic stays queryable.
- **Subscriptions:** four modes (exclusive, shared, failover, key-shared) give JMS-like and Kafka-like semantics on the same topic.

**When to use:**
- Multi-tenant SaaS platforms needing namespace isolation.
- Multi-region applications needing built-in geo-replication.
- Mixed workloads: some consumers need queue semantics, others need streaming.

## 3. Core concept

Key abstractions:

- **Tenant/Namespace/Topic:** three-level hierarchy (`persistent://tenant/namespace/topic`). Tenants isolate teams; namespaces isolate environments within a team.
- **Subscription:** named cursor into a topic. A subscription's mode controls how messages are delivered to its consumers.
  - `Exclusive`: one consumer per subscription.
  - `Shared`: messages round-robined across consumers (parallel processing, no ordering).
  - `Failover`: one active consumer, others on standby.
  - `Key-shared`: messages with the same key always go to the same consumer.
- **Schema:** Pulsar enforces message schemas at the broker (Avro, JSON, Protobuf) — schema evolution is governed.
- **Ledger (BookKeeper):** the actual storage unit, decoupled from the broker.

Spring Boot: `spring.pulsar.client.service-url=pulsar://localhost:6650`, `@PulsarListener(topics="my-topic", subscriptionName="my-sub")`.

## 4. Diagram

<svg viewBox="0 0 720 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pulsar architecture: producer to stateless broker, broker writes to BookKeeper, consumers via subscription">
  <!-- Producer -->
  <rect x="10" y="85" width="120" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="70" y="106" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Producer</text>
  <text x="70" y="121" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">PulsarTemplate</text>

  <!-- Arrow to broker -->
  <line x1="135" y1="110" x2="205" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#pa)"/>

  <!-- Broker -->
  <rect x="210" y="65" width="140" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="280" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Pulsar Broker</text>
  <text x="280" y="107" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(stateless routing)</text>
  <text x="280" y="124" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">subscriptions</text>
  <text x="280" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">schema registry</text>

  <!-- Arrow to BookKeeper -->
  <line x1="280" y1="160" x2="280" y2="185" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#pa)"/>
  <rect x="210" y="188" width="140" height="36" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="280" y="210" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">BookKeeper (storage)</text>

  <!-- Arrows to consumers -->
  <line x1="355" y1="95" x2="430" y2="75" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#pb)"/>
  <line x1="355" y1="125" x2="430" y2="145" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#pb)"/>

  <!-- Subscription A -->
  <rect x="435" y="55" width="155" height="44" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="512" y="74" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Shared Subscription</text>
  <text x="512" y="89" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@PulsarListener sub-A</text>

  <!-- Subscription B -->
  <rect x="435" y="125" width="155" height="44" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="512" y="144" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Exclusive Subscription</text>
  <text x="512" y="159" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@PulsarListener sub-B</text>

  <defs>
    <marker id="pa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="pb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Broker is stateless; BookKeeper holds the durable log. Multiple subscription modes on the same topic serve different consumers.

## 5. Runnable example

```java
// PulsarDemo.java — simulates Pulsar subscription modes without a broker
// How to run: java PulsarDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot 3.2+: add spring-boot-starter-pulsar; use PulsarTemplate / @PulsarListener

import java.util.*;

public class PulsarDemo {

    record Message(String key, String value) {}

    // Simulated persistent topic log (append-only)
    static final List<Message> topicLog = new ArrayList<>();

    // Subscriptions track their own cursor (offset)
    static final Map<String, Integer> cursors = new HashMap<>();

    static void produce(String key, String value) {
        topicLog.add(new Message(key, value));
        System.out.printf("[PulsarTemplate] -> key='%s' value='%s' (offset %d)%n",
                key, value, topicLog.size() - 1);
    }

    enum SubscriptionType { EXCLUSIVE, SHARED, KEY_SHARED }

    static void consume(String subName, SubscriptionType type, int numConsumers) {
        int cursor = cursors.getOrDefault(subName, 0);
        List<Message> pending = topicLog.subList(cursor, topicLog.size());
        System.out.println("\n[@PulsarListener subscription='" + subName + "' type=" + type + "]");

        if (type == SubscriptionType.EXCLUSIVE) {
            // Only one consumer active
            pending.forEach(m -> System.out.printf("  Consumer-0: key='%s' value='%s'%n", m.key(), m.value()));
        } else if (type == SubscriptionType.SHARED) {
            // Round-robin across consumers
            int c = 0;
            for (Message m : pending) {
                System.out.printf("  Consumer-%d: key='%s' value='%s'%n", c % numConsumers, m.key(), m.value());
                c++;
            }
        } else { // KEY_SHARED: same key always goes to same consumer
            Map<String, Integer> keyConsumer = new HashMap<>();
            int[] nextId = {0};
            for (Message m : pending) {
                int assignedConsumer = keyConsumer.computeIfAbsent(m.key(),
                        k -> nextId[0]++ % numConsumers);
                System.out.printf("  Consumer-%d: key='%s' value='%s'%n", assignedConsumer, m.key(), m.value());
            }
        }
        cursors.put(subName, topicLog.size());
    }

    public static void main(String[] args) {
        System.out.println("=== Apache Pulsar Demo ===\n");
        System.out.println("--- Producing to topic 'orders' ---");
        produce("user-A", "Order placed");
        produce("user-B", "Order placed");
        produce("user-A", "Order updated");
        produce("user-C", "Order placed");

        consume("sub-exclusive",  SubscriptionType.EXCLUSIVE,  1);
        consume("sub-shared",     SubscriptionType.SHARED,     3);
        consume("sub-key-shared", SubscriptionType.KEY_SHARED, 3);
    }
}
```

**How to run:** `java PulsarDemo.java`

## 6. Walkthrough

- **`topicLog`** is the immutable Pulsar topic log stored in BookKeeper. In the demo it's an in-memory list.
- **`cursors`** tracks each subscription's read position — Pulsar subscriptions, not consumers, hold the cursor.
- **`EXCLUSIVE`**: one consumer receives everything — highest throughput when no parallelism is needed.
- **`SHARED`**: round-robin across `numConsumers` — maximises throughput but loses per-key ordering.
- **`KEY_SHARED`**: same key always goes to the same consumer — ordering per key with parallelism across keys. Equivalent to Kafka's partition-key approach but without pre-declaring partitions.
- The final `cursors.put` advances the subscription cursor — in real Pulsar this is `consumer.acknowledge(msg)`.

## 7. Gotchas & takeaways

> `KEY_SHARED` subscriptions **require hash-based routing** — the broker routes by key hash. Adding consumers changes the hash ring, possibly rebalancing which consumer gets which key. Expect a brief reordering window during consumer group changes.

> Pulsar uses **acknowledgement-based retention**: messages are deleted only when all subscriptions acknowledge them. A slow/inactive subscription can cause unbounded topic growth — set retention policies.

- Spring Boot 3.2+ is required; older versions need the `spring-pulsar` community starter.
- `spring.pulsar.client.service-url=pulsar://localhost:6650` is the minimum config.
- `@PulsarListener(topics="persistent://tenant/ns/topic", subscriptionName="my-sub", subscriptionType=SubscriptionType.Shared)` wires a consumer.
- Use `PulsarTemplate` for fire-and-forget; `ReactivePulsarTemplate` for reactive pipelines.
- Pulsar's multi-tenancy: `spring.pulsar.defaults.topic-name=persistent://my-tenant/my-ns/my-topic` avoids repeating the hierarchy everywhere.
