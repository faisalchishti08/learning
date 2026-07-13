---
card: microservices
gi: 348
slug: debezium-spring-for-cdc-based-outbox
title: "Debezium + Spring for CDC-based outbox"
---

## 1. What it is

**Debezium**, combined with Spring, implements the [transactional outbox pattern](0331-transactional-outbox-pattern.md)'s relay side using [Change Data Capture](0333-change-data-capture-cdc.md) instead of a hand-built polling or event-publishing loop: a Spring service writes to its own outbox table exactly as the outbox pattern requires (atomically, in the same local transaction as the business change), and Debezium — tailing the database's [transaction log](0332-transaction-log-tailing.md) directly — detects each new outbox row the instant it commits and publishes it to Kafka, with no application code needed to do the actual relaying.

## 2. Why & when

Earlier topics showed the outbox pattern's relay implemented as a [polling publisher](0334-polling-publisher-pattern.md) — a scheduled query against the outbox table. That works, but it adds recurring query load and a polling-interval delay. Debezium's "outbox event router" is a purpose-built connector that specifically watches an outbox table via CDC and, the moment a row commits, transforms it into a properly-formed Kafka message (using the outbox row's columns to determine the target topic, message key, and payload) — combining the reliability of the outbox pattern with the low-latency, low-overhead relay mechanism of log tailing, without a team needing to write and operate that relay itself.

Use Debezium's outbox event router when a Spring service already writes to an outbox table (application-side) and you want the most reliable, lowest-latency, and least-custom-code way to get those rows onto Kafka — this combination is effectively the production-grade version of the polling-publisher outbox examples shown earlier, trading the operational simplicity of polling for Debezium's more sophisticated (and more capable) CDC-based relay.

## 3. Core concept

The Spring service's transaction writes both the business row and an outbox row (with a well-known shape: an `aggregate_type`, `aggregate_id`, `type`, and `payload` column, by Debezium's outbox convention) atomically, exactly as any outbox implementation requires. Debezium, running as a separate connector process (or embedded), tails the database's transaction log, recognizes new rows in the outbox table specifically, and — using its outbox event router single message transform — publishes each one to Kafka, deriving the topic and key from the outbox row's own columns, then effectively "deletes" its job (the outbox table itself can be trimmed independently, since Debezium reads from the log, not the table's current contents).

```java
@Transactional
public void placeOrder(Order order) {
    orderRepository.save(order);
    outboxRepository.save(new OutboxEvent("Order", order.getId(), "OrderPlaced", toJson(order)));
} // Debezium's log-tailing connector picks this row up and publishes to Kafka -- no relay code needed
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring service commits an order row and an outbox row atomically; Debezium tails the transaction log, detects the new outbox row, and publishes it to Kafka using the outbox event router transform -- no relay code written by the team">
  <rect x="20" y="20" width="260" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Spring @Transactional</text>
  <text x="150" y="60" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">order row + outbox row, atomically</text>

  <line x1="150" y1="80" x2="150" y2="110" stroke="#8b949e" marker-end="url(#a348)"/>
  <rect x="30" y="110" width="240" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="132" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Transaction log (Debezium tails this)</text>

  <line x1="270" y1="127" x2="380" y2="127" stroke="#79c0ff" marker-end="url(#a348b)"/>
  <rect x="390" y="90" width="220" height="70" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="500" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Debezium outbox event router</text>
  <text x="500" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no team-written relay code</text>
  <text x="500" y="144" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; publishes to Kafka</text>

  <defs>
    <marker id="a348" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a348b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The application writes the outbox row atomically; Debezium's log-tailing connector detects and publishes it to Kafka, with no hand-written relay.

## 5. Runnable example

Scenario: an order-placement flow, first shown with a hand-written polling relay (from earlier in this section, for comparison), then rebuilt as a simulated Debezium-style log-tailing router that reacts to outbox commits with no polling at all, and finally extended to show the router deriving the Kafka topic and key directly from the outbox row's own columns, exactly as Debezium's outbox event router convention specifies.

### Level 1 — Basic

```java
// File: HandWrittenPollingRelay.java -- the polling-publisher approach
// from earlier in this section, shown again here for direct comparison.
import java.util.*;

public class HandWrittenPollingRelay {
    record OutboxRow(int id, String payload) {}
    static List<OutboxRow> outboxTable = new ArrayList<>();
    static List<String> kafkaTopic = new ArrayList<>();
    static int lastPublishedId = -1;

    static void placeOrder(String orderId) {
        outboxTable.add(new OutboxRow(outboxTable.size(), "OrderPlaced:" + orderId));
        System.out.println("transaction committed: order " + orderId + " + outbox row");
    }

    static void pollAndPublish() { // TEAM-WRITTEN relay code -- must be built and operated
        for (OutboxRow row : outboxTable) {
            if (row.id() <= lastPublishedId) continue;
            kafkaTopic.add(row.payload());
            lastPublishedId = row.id();
            System.out.println("poll: published " + row.payload());
        }
    }

    public static void main(String[] args) {
        placeOrder("order-1");
        System.out.println("--- waiting for the next scheduled poll cycle ---");
        pollAndPublish();
        System.out.println("kafkaTopic: " + kafkaTopic);
    }
}
```

How to run: `java HandWrittenPollingRelay.java`

`pollAndPublish` is team-written and team-operated relay code — a scheduled query, a loop, tracked position — exactly as covered in the [polling publisher pattern](0334-polling-publisher-pattern.md). This works, but it's infrastructure the team built and must maintain.

### Level 2 — Intermediate

```java
// File: DebeziumStyleLogTailingRouter.java -- NO polling code at all; a
// simulated Debezium connector reacts the INSTANT the outbox transaction
// commits, by tailing the transaction log directly.
import java.util.*;
import java.util.function.Consumer;

public class DebeziumStyleLogTailingRouter {
    record OutboxRow(String aggregateType, String aggregateId, String eventType, String payload) {}
    static List<Consumer<OutboxRow>> logTailers = new ArrayList<>(); // Debezium attaches here, as a log reader
    static List<String> kafkaTopic = new ArrayList<>();

    static void commitOrderAndOutboxRow(String orderId) { // the ONLY code the Spring team writes
        OutboxRow row = new OutboxRow("Order", orderId, "OrderPlaced", "{\"orderId\":\"" + orderId + "\"}");
        System.out.println("transaction committed: order " + orderId + " + outbox row (Debezium sees this via the log)");
        logTailers.forEach(tailer -> tailer.accept(row)); // NO polling -- notified IMMEDIATELY via the log
    }

    public static void main(String[] args) {
        // This registration IS Debezium's outbox event router -- NOT team-written relay code, just configuration in reality.
        logTailers.add(row -> {
            kafkaTopic.add(row.payload());
            System.out.println("Debezium outbox router: detected commit via log tail, published " + row.payload() + " to Kafka INSTANTLY");
        });

        commitOrderAndOutboxRow("order-1"); // no poll cycle to wait for at all

        System.out.println("kafkaTopic: " + kafkaTopic);
    }
}
```

How to run: `java DebeziumStyleLogTailingRouter.java`

`commitOrderAndOutboxRow` is the only code the Spring application team writes — it commits the outbox row and notifies attached log tailers, standing in for Debezium detecting the commit via the transaction log the instant it happens, with zero polling delay and no team-written relay loop. The router registered in `main` mirrors Debezium's outbox event router, which in a real deployment is pure configuration, not code the team builds or maintains.

### Level 3 — Advanced

```java
// File: RouterDerivesTopicAndKeyFromOutboxColumns.java -- the router
// derives the KAFKA TOPIC and MESSAGE KEY directly from the outbox row's
// own columns (aggregateType, aggregateId), exactly as Debezium's outbox
// event router convention specifies -- different aggregate types route
// to different topics automatically.
import java.util.*;
import java.util.function.Consumer;

public class RouterDerivesTopicAndKeyFromOutboxColumns {
    record OutboxRow(String aggregateType, String aggregateId, String eventType, String payload) {}
    record KafkaMessage(String topic, String key, String payload) {}
    static List<Consumer<OutboxRow>> logTailers = new ArrayList<>();
    static Map<String, List<KafkaMessage>> kafkaTopics = new HashMap<>(); // simulates MULTIPLE real topics

    static void commitOutboxRow(String aggregateType, String aggregateId, String eventType, String payload) {
        OutboxRow row = new OutboxRow(aggregateType, aggregateId, eventType, payload);
        System.out.println("transaction committed: " + aggregateType + "/" + aggregateId + " outbox row");
        logTailers.forEach(tailer -> tailer.accept(row));
    }

    public static void main(String[] args) {
        // Debezium's outbox event router, configured (not coded) to derive topic from aggregateType, key from aggregateId.
        logTailers.add(row -> {
            String topic = row.aggregateType().toLowerCase() + "-events"; // e.g. "order" -> "order-events"
            KafkaMessage message = new KafkaMessage(topic, row.aggregateId(), row.payload());
            kafkaTopics.computeIfAbsent(topic, k -> new ArrayList<>()).add(message);
            System.out.println("Debezium router: routed " + row.eventType() + " to topic '" + topic
                    + "' with key '" + row.aggregateId() + "' -- DERIVED entirely from the outbox row's own columns");
        });

        commitOutboxRow("Order", "order-1", "OrderPlaced", "{\"orderId\":\"order-1\"}");
        commitOutboxRow("Payment", "payment-1", "PaymentProcessed", "{\"paymentId\":\"payment-1\"}");

        System.out.println("order-events topic: " + kafkaTopics.get("order-events"));
        System.out.println("payment-events topic: " + kafkaTopics.get("payment-events"));
        System.out.println("Two DIFFERENT aggregate types automatically routed to two DIFFERENT topics, with NO per-aggregate routing code written.");
    }
}
```

How to run: `java RouterDerivesTopicAndKeyFromOutboxColumns.java`

Both `commitOutboxRow` calls go through the identical router logic, but because the first row's `aggregateType` is `"Order"` and the second's is `"Payment"`, the router computes different topic names (`"order-events"` and `"payment-events"`) purely from that one column — no explicit `if aggregateType == "Order" then ... else if ... "Payment"` branching was written anywhere. The message key is likewise derived directly from `aggregateId`, ensuring all events for the same entity land on the same key (and therefore the same partition, preserving per-entity ordering) automatically.

## 6. Walkthrough

Trace `RouterDerivesTopicAndKeyFromOutboxColumns.main` in order. **First**, `commitOutboxRow("Order", "order-1", "OrderPlaced", ...)` runs: it constructs an `OutboxRow` and calls every registered log tailer with it — here, the one router lambda.

**Inside the router**, `topic` is computed as `row.aggregateType().toLowerCase() + "-events"`, which evaluates to `"order-events"` since `aggregateType` is `"Order"`. A `KafkaMessage` is built with this topic, `key=row.aggregateId()` (`"order-1"`), and the original payload, and it's appended to `kafkaTopics.get("order-events")` (created fresh via `computeIfAbsent`).

**Next**, `commitOutboxRow("Payment", "payment-1", "PaymentProcessed", ...)` runs the same way: the router computes `topic = "payment-events"` this time, since `aggregateType` is `"Payment"`, and appends a new `KafkaMessage` to a *different* list in `kafkaTopics`, keyed by `"payment-events"`.

**Finally**, `main` prints both `kafkaTopics.get("order-events")` and `kafkaTopics.get("payment-events")`, showing each contains exactly the one message routed to it — confirming that the same router logic, with no per-type branching written by hand, correctly separated the two aggregate types into their own topics purely by reading the outbox row's own `aggregateType` column.

```
commitOutboxRow(Order, order-1, ...)     -> router computes topic="order-events",   key="order-1"   -> routed there
commitOutboxRow(Payment, payment-1, ...) -> router computes topic="payment-events", key="payment-1" -> routed there
kafkaTopics: {order-events: [order-1 msg], payment-events: [payment-1 msg]}  -- automatic routing, no per-type code
```

## 7. Gotchas & takeaways

> Debezium's outbox event router relies on the outbox table following its expected column convention (`aggregate_type`, `aggregate_id`, `type`/`event type`, `payload`, and typically an `id`) — deviating from this shape without adjusting the router's configuration means the connector won't route messages correctly, or at all. Check the specific Debezium version's documented outbox table schema before building against it.

- Debezium + Spring implements the [transactional outbox pattern](0331-transactional-outbox-pattern.md)'s relay via [Change Data Capture](0333-change-data-capture-cdc.md), giving the reliability of the outbox pattern with the low-latency, low-overhead delivery of [transaction log tailing](0332-transaction-log-tailing.md).
- The Spring application still writes its outbox row exactly as any outbox implementation requires — atomically, within the business transaction; Debezium handles everything from there.
- Debezium's outbox event router derives the Kafka topic and message key directly from the outbox row's own columns (typically aggregate type and aggregate ID), automatically routing different entity types to different topics with no per-type application code.
- This combination is effectively a production-grade replacement for a hand-written [polling publisher](0334-polling-publisher-pattern.md) relay, trading a small amount of connector configuration and operational complexity for lower latency and no team-maintained relay code.
