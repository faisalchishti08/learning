---
card: system-design
gi: 119
slug: spring-for-apache-kafka-kafkatemplate-kafkalistener
title: Spring for Apache Kafka (KafkaTemplate / @KafkaListener)
---

## 1. What it is

**Spring for Apache Kafka** is Spring's library for producing and consuming messages on an [event stream like Kafka](0112-event-streaming-vs-message-queues.md), from ordinary Spring code. **`KafkaTemplate`** is the class you call to publish a message onto a topic. **`@KafkaListener`** is an annotation you put on a method to make it automatically run whenever a message arrives on a topic — Spring handles polling the broker, deserializing the message, and invoking your method.

## 2. Why & when

Working with Kafka's raw client library directly means manually managing a producer or consumer object, polling loops, serialization, and offset commits. Spring for Apache Kafka wraps all of this in familiar Spring idioms: `KafkaTemplate` behaves like other Spring template classes (`RestTemplate`, `JdbcTemplate`), and `@KafkaListener` behaves like `@RequestMapping` — you write a plain method, and the framework wires it to the underlying mechanics. Use it in any Spring Boot service that needs to publish to, or consume from, Kafka topics — the standard choice for [event streaming](0112-event-streaming-vs-message-queues.md) in a Spring-based system.

## 3. Core concept

- **`KafkaTemplate<K, V>`:** an injectable bean; call `kafkaTemplate.send(topic, key, value)` to publish a message. The key determines the [partition](0113-brokers-topics-partitions.md) the message lands in.
- **`@KafkaListener(topics = "...")`:** put this on a method; Spring Kafka runs a background consumer that polls the topic and invokes your method with each message's payload (and optionally its key, partition, and headers).
- **Consumer groups:** `@KafkaListener(groupId = "...")` assigns the listener to a consumer group; multiple instances of your service in the same group act as [competing consumers](0110-message-queues-point-to-point.md) across the topic's partitions.
- **Serialization:** configured via Spring Boot properties (`spring.kafka.producer.value-serializer`, `spring.kafka.consumer.value-deserializer`), commonly JSON, so your method can send and receive plain Java objects instead of raw bytes.
- **Acknowledgment modes:** by default, Spring Kafka commits the offset automatically after your listener method returns without throwing; manual acknowledgment (`Acknowledgment.acknowledge()`) gives you explicit control, useful for building [idempotent](0116-idempotent-consumers.md), reliable consumers.

## 4. Diagram

```
  Producer side:                       Consumer side:

  @RestController                      @KafkaListener(topics="orders", groupId="shipping-service")
       |                                      |
       v                                      v
  OrderService                          handleOrderEvent(OrderEvent event)
       |                                      |
       v                                      v
  kafkaTemplate.send("orders", orderId, event)   Spring Kafka polls broker,
       |                                          deserializes JSON -> OrderEvent,
       v                                          invokes this method
  Kafka broker: topic "orders", partitioned by orderId
```
*Caption: `KafkaTemplate` sends from the producer side; `@KafkaListener` receives on the consumer side, with Spring handling polling and deserialization in between.*

## 5. Runnable example

**Level 1 — Basic.** A `KafkaTemplate`-style send and an `@KafkaListener`-style receive, modeled without a real broker.

**Level 2 — Realistic config.** Send a JSON-serializable record, and route it by key to a simulated partition, as Spring Kafka would.

**Level 3 — Consumer group semantics.** Two listener instances in the same group split a topic's partitions between them.

```java
// SpringKafkaDemo.java
import java.util.*;
import java.util.function.*;

public class SpringKafkaDemo {

    // Models what @KafkaListener wires up: a topic name mapped to listener methods, grouped by consumer group.
    record OrderEvent(String orderId, String status) {}

    static Map<String, List<Consumer<OrderEvent>>> listenersByTopic = new HashMap<>();

    // Models KafkaTemplate.send(topic, key, value).
    static void kafkaTemplateSend(String topic, String key, OrderEvent event) {
        System.out.println("KafkaTemplate: sending to topic '" + topic + "' key=" + key + " value=" + event);
        for (Consumer<OrderEvent> listener : listenersByTopic.getOrDefault(topic, List.of())) {
            listener.accept(event); // Spring Kafka deserializes and invokes the @KafkaListener method
        }
    }

    // Models @KafkaListener(topics = "orders", groupId = "...") registering a listener method.
    static void kafkaListener(String topic, Consumer<OrderEvent> listenerMethod) {
        listenersByTopic.computeIfAbsent(topic, t -> new ArrayList<>()).add(listenerMethod);
    }

    public static void main(String[] args) {
        // Level 1 & 2: producer publishes; a consumer's @KafkaListener-style method reacts.
        kafkaListener("orders", event ->
            System.out.println("  [shipping-service listener] handling: " + event + " -> scheduling shipment"));

        kafkaTemplateSend("orders", "order-1", new OrderEvent("order-1", "PLACED"));

        // Level 3: two listener "instances" in the same consumer group, each handling a different partition.
        List<OrderEvent> handledByInstanceA = new ArrayList<>();
        List<OrderEvent> handledByInstanceB = new ArrayList<>();

        // Reset listeners for a clean group demo, modeling two @KafkaListener instances of the same service.
        listenersByTopic.put("orders", new ArrayList<>());
        int numInstances = 2;
        List<List<Consumer<OrderEvent>>> instances = List.of(
            List.of((Consumer<OrderEvent>) handledByInstanceA::add),
            List.of((Consumer<OrderEvent>) handledByInstanceB::add)
        );

        List<OrderEvent> incoming = List.of(
            new OrderEvent("order-2", "PLACED"), new OrderEvent("order-3", "PLACED"),
            new OrderEvent("order-4", "PLACED"), new OrderEvent("order-5", "PLACED")
        );
        for (int i = 0; i < incoming.size(); i++) {
            // Kafka assigns each partition to exactly one instance in the group; here modeled by round-robin.
            instances.get(i % numInstances).get(0).accept(incoming.get(i));
        }
        System.out.println("instance A (group member 1) handled: " + handledByInstanceA);
        System.out.println("instance B (group member 2) handled: " + handledByInstanceB);
        System.out.println("-> same consumer group, work split across instances - no message handled by both");
    }
}
```

**How to run:** save as `SpringKafkaDemo.java`, then run `java SpringKafkaDemo.java`. (This models Spring Kafka's wiring in plain Java; a real Spring Boot app would use `@SpringBootApplication`, `KafkaTemplate<String, OrderEvent>`, and `@KafkaListener(topics = "orders", groupId = "shipping-service")` with the `spring-kafka` dependency.)

## 6. Walkthrough

1. `kafkaTemplateSend` models `KafkaTemplate.send(topic, key, value)`: it prints the send, then calls every registered listener for that topic — standing in for the broker delivering the message and Spring Kafka invoking the `@KafkaListener` method.
2. The Level 1/2 listener registered via `kafkaListener("orders", ...)` reacts to the `OrderEvent` for `"order-1"`, printing that it is scheduling a shipment — this is the shape of a real `@KafkaListener` method: it receives a deserialized object, not raw bytes.
3. Level 3 resets the topic's listeners and models two consumer instances of the same service (`instanceA`, `instanceB`) in the same consumer group, each represented by its own list collecting the events it handled.
4. The loop distributes four incoming events round-robin between the two instances, modeling how Kafka assigns different partitions of a topic to different members of the same consumer group.
5. The final print shows `handledByInstanceA` and `handledByInstanceB` each with two distinct events and no overlap — confirming the competing-consumers behavior: scaling up `@KafkaListener` instances in the same `groupId` splits the topic's total work, rather than duplicating it.

## 7. Gotchas & takeaways

> Gotcha: Spring Kafka's default automatic offset commit happens once your `@KafkaListener` method returns without throwing — if the method's logic can partially succeed (e.g. it writes to a database, then a network call fails), the offset is still committed as if it fully succeeded, and Kafka will not redeliver the message. Combine business-logic transactions with manual acknowledgment (`AckMode.MANUAL`) when partial failure inside the listener method is possible.

- `KafkaTemplate` sends messages to a topic; `@KafkaListener` marks a method to automatically receive and process messages from a topic, hiding the underlying polling and deserialization.
- Consumer group membership (`groupId`) determines competing-consumer behavior: multiple instances in the same group split a topic's partitions, rather than each seeing every message.
- Acknowledgment mode controls exactly when Spring Kafka considers a message processed, which matters directly for at-least-once versus accidental at-most-once behavior.
- Related concepts: [Brokers & topics/partitions](0113-brokers-topics-partitions.md) (what `KafkaTemplate`'s key argument routes into), [Delivery semantics](0114-delivery-semantics-at-most-at-least-exactly-once.md) (governed by the acknowledgment mode chosen here).
