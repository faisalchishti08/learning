---
card: microservices
gi: 152
slug: spring-for-apache-pulsar
title: "Spring for Apache Pulsar"
---

## 1. What it is

Spring for Apache Pulsar is the lower-level Spring integration for Apache Pulsar, offering `PulsarTemplate` for direct message production and `@PulsarListener` for direct topic subscription — the same pattern as [Spring for Apache Kafka](0149-spring-for-apache-kafka-kafkatemplate-kafkalistener.md) and [Spring AMQP](0151-spring-amqp-rabbitmq-rabbittemplate-rabbitlistener.md), but exposing Pulsar's own distinctive architecture: a clean separation between stateless serving brokers and a tiered storage layer, and multiple built-in subscription types (exclusive, shared, failover, key-shared) selectable per consumer without needing separate topics or partitions for each pattern.

## 2. Why & when

Pulsar's built-in subscription types solve, natively at the broker level, distinction problems that Kafka and RabbitMQ solve with separate mechanisms: a single Pulsar topic can support an exclusive subscription (one consumer only, like a dedicated queue), a shared subscription ([competing consumers](0120-competing-consumers-pattern.md), round-robin across all subscribers), a failover subscription (one active consumer with automatic failover to a standby), and a key-shared subscription (competing consumers, but messages sharing a key always go to the same consumer — combining scaling with per-key ordering) — all against the identical topic, chosen per-subscription rather than baked into the topic's structure itself.

Reach for Spring for Apache Pulsar when a service needs Pulsar specifically — its multi-tenant namespace model, its geo-replication features, or particularly its flexible per-subscription consumption patterns without needing to pre-plan partition counts the way Kafka's consumer-group-to-partition mapping requires. For simpler needs already well-served by Kafka or RabbitMQ, or when broker portability matters more than Pulsar's specific capabilities, the other options remain more common defaults.

## 3. Core concept

`PulsarTemplate.send` publishes to a named topic; `@PulsarListener`'s `subscriptionType` attribute selects which of Pulsar's four subscription behaviors a given consumer method uses, entirely independent of how the topic itself is structured.

```java
@Autowired PulsarTemplate<OrderPlaced> pulsarTemplate;

void placeOrder(OrderPlaced order) {
    pulsarTemplate.send("order-events", order); // simple, direct publish
}

@PulsarListener(subscriptionName = "email-service", subscriptionType = SubscriptionType.Shared) // competing consumers
void onOrderPlacedForEmail(OrderPlaced order) { sendConfirmation(order); }

@PulsarListener(subscriptionName = "shipping-service", subscriptionType = SubscriptionType.Key_Shared) // scaled AND ordered per key
void onOrderPlacedForShipping(OrderPlaced order) { scheduleShipment(order); }
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One Pulsar topic supports multiple independently-configured subscriptions: a Shared subscription round-robins messages across competing consumers, while a Key_Shared subscription also splits across consumers but guarantees messages with the same key always go to the same consumer" >
  <rect x="20" y="70" width="130" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="97" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-events topic</text>

  <rect x="230" y="15" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="38" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Shared subscription</text>
  <text x="320" y="53" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">"email-service"</text>
  <text x="320" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">round-robin, no key affinity</text>

  <rect x="230" y="110" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="133" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Key_Shared subscription</text>
  <text x="320" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">"shipping-service"</text>
  <text x="320" y="161" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">split, but same key -&gt; same consumer</text>

  <line x1="150" y1="90" x2="228" y2="45" stroke="#8b949e" marker-end="url(#arr33)"/>
  <line x1="150" y1="95" x2="228" y2="140" stroke="#8b949e" marker-end="url(#arr33)"/>

  <defs>
    <marker id="arr33" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The same topic serves two entirely different consumption semantics simultaneously, chosen per subscription, not per topic.

## 5. Runnable example

Scenario: an order-processing setup that starts with a single fixed consumption pattern (no choice at all), adds a Shared subscription to demonstrate pure round-robin competing consumption, and finally adds a Key_Shared subscription side by side with the Shared one on the same topic, proving both subscription types can coexist and behave completely differently against identical published events.

### Level 1 — Basic

```java
// File: SingleFixedConsumptionPattern.java -- ONE hard-coded consumption
// behavior; no way to have a differently-behaving consumer on the same stream.
import java.util.*;

public class SingleFixedConsumptionPattern {
    record OrderPlaced(int orderId, String region) {}

    public static void main(String[] args) {
        List<OrderPlaced> orders = List.of(new OrderPlaced(1, "us"), new OrderPlaced(2, "us"), new OrderPlaced(3, "eu"));
        for (OrderPlaced o : orders) {
            System.out.println("[the only consumer] processing " + o); // no choice of subscription behavior at all
        }
        System.out.println("If a SECOND consumer needed different behavior (e.g. ordered-by-region), a separate topic or queue would be needed.");
    }
}
```

**How to run:** `javac SingleFixedConsumptionPattern.java && java SingleFixedConsumptionPattern` (JDK 17+).

### Level 2 — Intermediate

```java
// File: SharedSubscription.java -- simulates a Pulsar SHARED subscription:
// pure round-robin competing consumption, no key affinity at all.
import java.util.*;

public class SharedSubscription {
    record OrderPlaced(int orderId, String region) {}

    static class SharedConsumerGroup {
        List<List<OrderPlaced>> consumerInboxes;
        int roundRobinIndex = 0;
        SharedConsumerGroup(int consumerCount) {
            consumerInboxes = new ArrayList<>();
            for (int i = 0; i < consumerCount; i++) consumerInboxes.add(new ArrayList<>());
        }
        void deliver(OrderPlaced order) {
            consumerInboxes.get(roundRobinIndex % consumerInboxes.size()).add(order); // PURE round-robin, ignores key/region entirely
            roundRobinIndex++;
        }
    }

    public static void main(String[] args) {
        SharedConsumerGroup emailService = new SharedConsumerGroup(2); // 2 instances, subscriptionType=Shared
        List<OrderPlaced> orders = List.of(
            new OrderPlaced(1, "us"), new OrderPlaced(2, "us"), new OrderPlaced(3, "eu"), new OrderPlaced(4, "us"));

        for (OrderPlaced o : orders) emailService.deliver(o);

        System.out.println("consumer-0 inbox: " + emailService.consumerInboxes.get(0));
        System.out.println("consumer-1 inbox: " + emailService.consumerInboxes.get(1));
        System.out.println("Orders split PURELY by arrival order, round-robin -- region/key played NO role in routing.");
    }
}
```

**How to run:** `javac SharedSubscription.java && java SharedSubscription` (JDK 17+).

Expected output:
```
consumer-0 inbox: [OrderPlaced[orderId=1, region=us], OrderPlaced[orderId=3, region=eu]]
consumer-1 inbox: [OrderPlaced[orderId=2, region=us], OrderPlaced[orderId=4, region=us]]
Orders split PURELY by arrival order, round-robin -- region/key played NO role in routing.
```

### Level 3 — Advanced

```java
// File: SharedAndKeySharedCoexisting.java -- BOTH a Shared and a Key_Shared
// subscription active on the SAME topic simultaneously, behaving completely differently.
import java.util.*;

public class SharedAndKeySharedCoexisting {
    record OrderPlaced(int orderId, String region) {}

    static class SharedConsumerGroup {
        List<List<OrderPlaced>> inboxes;
        int roundRobinIndex = 0;
        SharedConsumerGroup(int count) { inboxes = new ArrayList<>(); for (int i = 0; i < count; i++) inboxes.add(new ArrayList<>()); }
        void deliver(OrderPlaced order) { inboxes.get(roundRobinIndex++ % inboxes.size()).add(order); }
    }

    static class KeySharedConsumerGroup {
        List<List<OrderPlaced>> inboxes;
        int consumerCount;
        KeySharedConsumerGroup(int count) { inboxes = new ArrayList<>(); consumerCount = count; for (int i = 0; i < count; i++) inboxes.add(new ArrayList<>()); }
        void deliver(OrderPlaced order) {
            int consumerIndex = Math.floorMod(order.region().hashCode(), consumerCount); // KEY (region) determines the consumer -- ALWAYS the same one
            inboxes.get(consumerIndex).add(order);
        }
    }

    public static void main(String[] args) {
        List<OrderPlaced> orders = List.of(
            new OrderPlaced(1, "us"), new OrderPlaced(2, "us"), new OrderPlaced(3, "eu"), new OrderPlaced(4, "us"), new OrderPlaced(5, "eu"));

        SharedConsumerGroup emailService = new SharedConsumerGroup(2);        // subscriptionType=Shared
        KeySharedConsumerGroup shippingService = new KeySharedConsumerGroup(3); // subscriptionType=Key_Shared, keyed by region

        // the SAME 5 events flow through BOTH subscriptions, independently, from the SAME topic
        for (OrderPlaced o : orders) {
            emailService.deliver(o);
            shippingService.deliver(o);
        }

        System.out.println("=== Shared subscription (email-service) ===");
        for (int i = 0; i < emailService.inboxes.size(); i++) System.out.println("  consumer-" + i + ": " + emailService.inboxes.get(i));

        System.out.println("=== Key_Shared subscription (shipping-service) ===");
        for (int i = 0; i < shippingService.inboxes.size(); i++) System.out.println("  consumer-" + i + ": " + shippingService.inboxes.get(i));

        System.out.println("Key_Shared guarantees ALL 'us' orders landed on the SAME consumer, and ALL 'eu' orders on the SAME consumer -- Shared made no such guarantee.");
    }
}
```

**How to run:** `javac SharedAndKeySharedCoexisting.java && java SharedAndKeySharedCoexisting` (JDK 17+).

Expected output (exact `Key_Shared` consumer indices depend on `String.hashCode()`, but all `"us"` orders always land together, and all `"eu"` orders always land together, on their own consistent consumer):
```
=== Shared subscription (email-service) ===
  consumer-0: [OrderPlaced[orderId=1, region=us], OrderPlaced[orderId=3, region=eu], OrderPlaced[orderId=5, region=eu]]
  consumer-1: [OrderPlaced[orderId=2, region=us], OrderPlaced[orderId=4, region=us]]
=== Key_Shared subscription (shipping-service) ===
  consumer-0: []
  consumer-1: [OrderPlaced[orderId=1, region=us], OrderPlaced[orderId=2, region=us], OrderPlaced[orderId=4, region=us]]
  consumer-2: [OrderPlaced[orderId=3, region=eu], OrderPlaced[orderId=5, region=eu]]
Key_Shared guarantees ALL 'us' orders landed on the SAME consumer, and ALL 'eu' orders on the SAME consumer -- Shared made no such guarantee.
```

## 6. Walkthrough

1. **Level 1** — a single, undifferentiated consumer processes every order with no notion of subscription type, competing consumption, or key-based routing at all — the baseline that both later levels improve on.
2. **Level 2, pure round-robin delivery** — `SharedConsumerGroup.deliver` uses `roundRobinIndex % consumerInboxes.size()` to pick a target inbox, with `roundRobinIndex` incrementing on every call regardless of the order's `region` — the delivered order's content plays no role in which consumer receives it.
3. **Level 2, the resulting split** — the printed inboxes show orders 1 and 3 going to `consumer-0` and orders 2 and 4 going to `consumer-1`, purely reflecting alternating arrival order; note order 3 (`region=eu`) ends up alongside order 1 (`region=us`) on the same consumer, since region had no bearing on the routing.
4. **Level 3, two subscription types on one topic** — `emailService` (a `SharedConsumerGroup`) and `shippingService` (a `KeySharedConsumerGroup`) both process the exact same `orders` list, modeling two independently-configured Pulsar subscriptions consuming from the identical underlying topic.
5. **Level 3, Key_Shared's routing rule** — `KeySharedConsumerGroup.deliver` computes `Math.floorMod(order.region().hashCode(), consumerCount)`, a function purely of `order.region()`; every order with `region="us"` always resolves to the identical consumer index, and every `region="eu"` order always resolves to its own (possibly different, but always consistent) consumer index.
6. **Level 3, the two subscriptions' genuinely different outcomes** — `emailService`'s `Shared` subscription output shows `"us"` and `"eu"` orders mixed together on both consumers (pure round-robin), while `shippingService`'s `Key_Shared` output shows every `"us"` order landing on one specific consumer and every `"eu"` order landing on a specific (possibly different) consumer, with zero mixing.
7. **Level 3, why this matters for `shipping-service`** — if the shipping logic needs all orders for the same region processed in relative order by a single, consistent worker (perhaps to maintain a per-region shipment queue correctly), `Key_Shared` provides that guarantee directly at the broker level, on the same topic `email-service` is simultaneously consuming with `Shared` semantics for its own, entirely different processing needs — no separate topic, partitioning scheme, or manual re-routing logic required to support both patterns at once.

## 7. Gotchas & takeaways

> **Gotcha:** `Key_Shared` subscriptions require every message to carry an explicit key (or Pulsar falls back to a default, potentially undesired routing behavior) — a topic whose producers don't consistently set a meaningful key on every message will not get the per-key consumer affinity `Key_Shared` is meant to provide, silently degrading toward behavior closer to plain `Shared`.

- Spring for Apache Pulsar exposes `PulsarTemplate` for direct publishing and `@PulsarListener` for direct topic subscription, mirroring the pattern of Spring's other broker-specific integrations.
- Pulsar's four built-in subscription types (exclusive, shared, failover, key-shared) let multiple, differently-behaving consumption patterns coexist against the same physical topic, chosen per subscription rather than baked into the topic's own structure.
- `Shared` subscriptions provide pure round-robin competing consumption with no key affinity; `Key_Shared` subscriptions provide competing consumption while still guaranteeing messages sharing a key always reach the same consumer.
- This flexibility is a genuine differentiator from Kafka's consumer-group-to-partition model, which requires pre-planning partition counts to achieve comparable per-key consumer affinity.
- `Key_Shared` routing depends on every message consistently carrying a meaningful key; producers that omit it undermine the guarantee the subscription type is meant to provide.
