---
card: microservices
gi: 149
slug: spring-for-apache-kafka-kafkatemplate-kafkalistener
title: "Spring for Apache Kafka (KafkaTemplate, @KafkaListener)"
---

## 1. What it is

Spring for Apache Kafka is the lower-level Spring integration for Kafka, sitting beneath (and independent of) Spring Cloud Stream's abstraction layer: `KafkaTemplate` provides a direct, imperative API for producing messages to Kafka, and `@KafkaListener` is a method-level annotation that subscribes a method directly to a Kafka topic, giving full, direct access to Kafka-specific concepts (partitions, offsets, consumer groups) without any broker-agnostic abstraction layer in between.

## 2. Why & when

[Spring Cloud Stream's binder abstraction](0145-spring-cloud-stream-binder-abstraction.md) is deliberately broker-agnostic, which is exactly the right trade-off when broker portability matters — but that same abstraction necessarily limits direct access to Kafka-specific features the abstraction doesn't generalize well (fine-grained manual partition assignment, direct offset seeking, Kafka transaction APIs, specific serializer/deserializer configuration). Spring for Apache Kafka trades away that broker-agnosticism for full, direct access to Kafka's actual API surface, wrapped just enough to remove Spring Boot boilerplate (auto-configured `ConsumerFactory`/`ProducerFactory`, simplified error handling, easy testing support).

Reach for Spring for Apache Kafka directly when a service is permanently committed to Kafka and needs fine-grained control that Spring Cloud Stream's abstraction doesn't expose, or when a team already has deep Kafka-specific operational expertise and prefers Kafka's own vocabulary (topics, partitions, consumer groups) directly in application code rather than through an abstraction layer. Use Spring Cloud Stream's functional model instead when broker portability, or the cleaner, framework-agnostic function-bean testing style, matters more than direct Kafka API access.

## 3. Core concept

`KafkaTemplate.send` publishes directly to a named Kafka topic, optionally with an explicit partition key; `@KafkaListener` on a method subscribes that method to a topic and consumer group, with the method's parameter receiving the deserialized message payload directly, no generic `Function`/`Consumer` interface involved.

```java
@Autowired KafkaTemplate<String, OrderPlaced> kafkaTemplate;

void placeOrder(int orderId, double total) {
    kafkaTemplate.send("order-events", String.valueOf(orderId), new OrderPlaced(orderId, total)); // direct Kafka API
}

@KafkaListener(topics = "order-events", groupId = "shipping-service") // Kafka-specific concepts, directly
void onOrderPlaced(OrderPlaced order) {
    scheduleShipment(order);
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="KafkaTemplate.send publishes directly to a named Kafka topic and partition key; an @KafkaListener-annotated method subscribes directly to that topic and consumer group, with no broker-agnostic abstraction layer between application code and the Kafka client API">
  <rect x="20" y="60" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">KafkaTemplate.send</text>
  <text x="95" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(topic, key, payload)</text>

  <rect x="240" y="60" width="160" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="87" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Kafka topic: order-events</text>

  <rect x="470" y="60" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">@KafkaListener</text>
  <text x="545" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">groupId=shipping-service</text>

  <line x1="170" y1="82" x2="238" y2="82" stroke="#8b949e" marker-end="url(#arr30)"/>
  <line x1="400" y1="82" x2="468" y2="82" stroke="#8b949e" marker-end="url(#arr30)"/>

  <defs>
    <marker id="arr30" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Both sides speak Kafka's own vocabulary directly — topics, partition keys, consumer groups — with no abstraction layer in between.

## 5. Runnable example

Scenario: an order-to-shipping flow modeled first with a raw, low-level Kafka client call (showing the boilerplate Spring removes), then with a simulated `KafkaTemplate`/`@KafkaListener`-style API that mirrors the real annotations' effect, and finally extended to show direct partition-key control and consumer-group-based competing consumption, both genuinely Kafka-specific capabilities.

### Level 1 — Basic

```java
// File: RawKafkaClientBoilerplate.java -- what direct Kafka client usage looks
// like WITHOUT Spring's simplification, for comparison.
import java.util.*;

public class RawKafkaClientBoilerplate {
    record OrderPlaced(int orderId, double total) {}

    // stands in for manually configuring a raw KafkaProducer: serializer config,
    // broker addresses, ack settings, retries, all assembled by hand
    static class RawKafkaProducerSetup {
        Map<String, List<OrderPlaced>> topics = new HashMap<>();
        void send(String topic, String key, OrderPlaced value) {
            // in reality: build a ProducerRecord, call producer.send(), handle the returned Future, etc.
            topics.computeIfAbsent(topic, t -> new ArrayList<>()).add(value);
            System.out.println("[raw client, manually configured] sent to " + topic + " key=" + key + ": " + value);
        }
    }

    public static void main(String[] args) {
        RawKafkaProducerSetup producer = new RawKafkaProducerSetup(); // lots of manual setup would precede this in reality
        producer.send("order-events", "42", new OrderPlaced(42, 99.90));
        System.out.println("Every producer/consumer needs this SAME manual setup repeated, without Spring's auto-configuration.");
    }
}
```

**How to run:** `javac RawKafkaClientBoilerplate.java && java RawKafkaClientBoilerplate` (JDK 17+).

### Level 2 — Intermediate

```java
// File: KafkaTemplateAndListener.java -- simulates KafkaTemplate.send and an
// @KafkaListener-annotated method, mirroring Spring's simplified, direct Kafka API.
import java.util.*;
import java.util.function.*;

public class KafkaTemplateAndListener {
    record OrderPlaced(int orderId, double total) {}

    // simulates Spring's auto-configured KafkaTemplate
    static class KafkaTemplate {
        Map<String, List<Object>> topics = new HashMap<>();
        List<BiConsumer<String, OrderPlaced>> listeners = new ArrayList<>();

        void send(String topic, String key, OrderPlaced value) { // the actual API Spring exposes
            topics.computeIfAbsent(topic, t -> new ArrayList<>()).add(value);
            System.out.println("[KafkaTemplate] sent to " + topic + " key=" + key + ": " + value);
            listeners.forEach(l -> l.accept(topic, value)); // simulates the broker delivering to a subscribed listener
        }

        // simulates registering a method annotated with @KafkaListener(topics = "...", groupId = "...")
        void registerListener(String topic, String groupId, Consumer<OrderPlaced> handler) {
            listeners.add((deliveredTopic, value) -> {
                if (deliveredTopic.equals(topic)) {
                    System.out.println("[@KafkaListener groupId=" + groupId + "] received: " + value);
                    handler.accept(value);
                }
            });
        }
    }

    public static void main(String[] args) {
        KafkaTemplate kafkaTemplate = new KafkaTemplate();

        // this represents the method body Spring would invoke for an @KafkaListener-annotated method
        kafkaTemplate.registerListener("order-events", "shipping-service", order ->
            System.out.println("  [shipping-service] scheduling shipment for order " + order.orderId()));

        kafkaTemplate.send("order-events", "42", new OrderPlaced(42, 99.90));
        System.out.println("Producer and consumer both used Kafka's own vocabulary (topic, key, groupId) DIRECTLY.");
    }
}
```

**How to run:** `javac KafkaTemplateAndListener.java && java KafkaTemplateAndListener` (JDK 17+).

Expected output:
```
[KafkaTemplate] sent to order-events key=42: OrderPlaced[orderId=42, total=99.9]
[@KafkaListener groupId=shipping-service] received: OrderPlaced[orderId=42, total=99.9]
  [shipping-service] scheduling shipment for order 42
```

### Level 3 — Advanced

```java
// File: PartitionKeysAndConsumerGroups.java -- direct control over partition
// keys, AND consumer-group-based competing consumption -- genuinely Kafka-specific capabilities.
import java.util.*;
import java.util.function.*;

public class PartitionKeysAndConsumerGroups {
    record OrderPlaced(int orderId, double total) {}

    static class KafkaTemplate {
        List<BiConsumer<String, OrderPlaced>> emailGroupListeners = new ArrayList<>(); // groupId = "email-service"
        List<BiConsumer<String, OrderPlaced>> shippingGroupListeners = new ArrayList<>(); // groupId = "shipping-service"
        int roundRobin = 0;

        void send(String topic, String partitionKey, OrderPlaced value) {
            int partition = Math.floorMod(partitionKey.hashCode(), 4); // DIRECT partition control via key, Kafka-specific
            System.out.println("[KafkaTemplate] sent to " + topic + " partition=" + partition + " key=" + partitionKey + ": " + value);

            // each CONSUMER GROUP gets its own full copy (pub/sub across groups)...
            emailGroupListeners.get(roundRobin % emailGroupListeners.size()).accept(topic, value); // ...but WITHIN a group, split (competing consumers)
            shippingGroupListeners.get(roundRobin % shippingGroupListeners.size()).accept(topic, value);
            roundRobin++;
        }

        void registerListener(String groupId, Consumer<OrderPlaced> handler) {
            BiConsumer<String, OrderPlaced> listener = (topic, value) -> handler.accept(value);
            if (groupId.equals("email-service")) emailGroupListeners.add(listener);
            else shippingGroupListeners.add(listener);
        }
    }

    public static void main(String[] args) {
        KafkaTemplate kafkaTemplate = new KafkaTemplate();

        // TWO instances in "email-service" group -- competing consumers WITHIN the group
        kafkaTemplate.registerListener("email-service", order -> System.out.println("  [email-service instance A] confirming order " + order.orderId()));
        kafkaTemplate.registerListener("email-service", order -> System.out.println("  [email-service instance B] confirming order " + order.orderId()));
        // ONE instance in "shipping-service" group -- an ENTIRELY independent group, gets its OWN full view
        kafkaTemplate.registerListener("shipping-service", order -> System.out.println("  [shipping-service] scheduling shipment for order " + order.orderId()));

        kafkaTemplate.send("order-events", "order-42", new OrderPlaced(42, 99.90));
        kafkaTemplate.send("order-events", "order-43", new OrderPlaced(43, 45.00));

        System.out.println("email-service's TWO instances split the traffic; shipping-service (separate group) saw BOTH orders independently.");
    }
}
```

**How to run:** `javac PartitionKeysAndConsumerGroups.java && java PartitionKeysAndConsumerGroups` (JDK 17+).

Expected output:
```
[KafkaTemplate] sent to order-events partition=... key=order-42: OrderPlaced[orderId=42, total=99.9]
  [email-service instance A] confirming order 42
  [shipping-service] scheduling shipment for order 42
[KafkaTemplate] sent to order-events partition=... key=order-43: OrderPlaced[orderId=43, total=45.0]
  [email-service instance B] confirming order 43
  [shipping-service] scheduling shipment for order 43
```

## 6. Walkthrough

1. **Level 1** — `RawKafkaProducerSetup` stands in for the manual assembly a plain Kafka client requires (serializer configuration, broker address list, acknowledgment settings) before a single message can be sent, none of which is shown as automated here.
2. **Level 2, `KafkaTemplate.send`** — mirrors the real `KafkaTemplate<K, V>.send(topic, key, value)` method signature directly; Spring auto-configures the underlying `ProducerFactory` from `application.yml` properties, removing exactly the manual setup Level 1 stood in for.
3. **Level 2, the listener as a direct method subscription** — `registerListener("order-events", "shipping-service", handler)` mirrors what `@KafkaListener(topics = "order-events", groupId = "shipping-service")` does on a real method: subscribing it directly to a topic and consumer group, with the framework handling deserialization and delivering the payload as a plain method parameter.
4. **Level 2, direct Kafka vocabulary throughout** — both the `send` call and the `registerListener` call use `topic`, `key`, and `groupId` as first-class, directly-named concepts — there is no generic `Function`/`Consumer` binding abstraction anywhere in this code, unlike the [Spring Cloud Stream functional model](0146-spring-cloud-stream-functional-programming-model-supplier-fu.md).
5. **Level 3, explicit partition key control** — `send` computes `Math.floorMod(partitionKey.hashCode(), 4)` directly and prints the resulting partition, exposing Kafka's partitioning mechanism explicitly rather than hiding it behind an abstraction — this level of direct control over which partition a message lands on is exactly the kind of fine-grained access Spring Cloud Stream's broker-agnostic layer does not expose as directly.
6. **Level 3, two consumer groups behaving differently** — `emailGroupListeners` (two registered instances) and `shippingGroupListeners` (one instance) are maintained as separate lists; `send` delivers to *one* member of `emailGroupListeners` (round-robin, competing-consumers style, per [consumer groups & partitions](0121-consumer-groups-partitions.md)) but to the single `shippingGroupListeners` member every time, since that group has only one instance.
7. **Level 3, tracing the two sends** — the first `send` call delivers to `email-service instance A` (round-robin index 0) and to `shipping-service`; the second `send` call delivers to `email-service instance B` (round-robin index 1) and to `shipping-service` again — demonstrating, with directly-modeled Kafka consumer-group semantics, that `email-service`'s two instances split the traffic between them while `shipping-service`, an independent group, receives every single order regardless of `email-service`'s internal instance count.

## 7. Gotchas & takeaways

> **Gotcha:** `@KafkaListener` methods, by default, run on the Kafka consumer's own polling thread — a slow or blocking operation inside a listener method delays that consumer's ability to poll for and process subsequent messages (and can trigger a consumer-group rebalance if polling stalls long enough); genuinely slow work inside a listener should be offloaded to a separate thread pool rather than run inline.

- Spring for Apache Kafka provides `KafkaTemplate` for direct, imperative message production and `@KafkaListener` for direct method-level topic subscription, both exposing Kafka's own vocabulary (topics, partitions, consumer groups) without a broker-agnostic abstraction layer.
- This trades away Spring Cloud Stream's broker portability for full, direct access to Kafka-specific capabilities like explicit partition key control and fine-grained consumer group configuration.
- Spring's auto-configuration removes the manual `ProducerFactory`/`ConsumerFactory` setup a raw Kafka client would otherwise require, while still exposing Kafka concepts directly rather than hiding them.
- Consumer group semantics (competing consumption within a group, independent full views across different groups) work exactly as with the raw Kafka client, since `@KafkaListener`'s `groupId` maps directly onto Kafka's own consumer group mechanism.
- Listener methods run on the Kafka consumer's polling thread by default; slow work inside them can stall polling and trigger unwanted consumer-group rebalances if not offloaded appropriately.
