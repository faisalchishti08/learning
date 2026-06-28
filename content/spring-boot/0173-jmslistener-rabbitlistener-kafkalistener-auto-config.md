---
card: spring-boot
gi: 173
slug: jmslistener-rabbitlistener-kafkalistener-auto-config
title: "@JmsListener / @RabbitListener / @KafkaListener auto-config"
---

## 1. What it is

`@JmsListener`, `@RabbitListener`, and `@KafkaListener` are Spring annotations that turn plain bean methods into message consumers. Spring Boot auto-configures the underlying listener container factories for each technology when the matching starter is on the classpath — so annotating a method is all you need to start consuming messages without any boilerplate infrastructure code.

All three follow the same pattern: declare a bean, annotate a method, Spring wires the rest.

## 2. Why & when

**Why this matters:** Without auto-config you would need to manually create `DefaultMessageListenerContainer` (JMS), `SimpleMessageListenerContainer` (RabbitMQ), or `ConcurrentMessageListenerContainer` (Kafka) — each with its own connection factory, error handler, and thread pool. Auto-config creates these factories with sensible defaults based on properties.

**When to use:**
- Any Spring Boot service that consumes from JMS (Artemis), RabbitMQ, or Kafka.
- Prefer `@KafkaListener` over `@RabbitListener` when you need replay, strict ordering, or high throughput.
- Use `@JmsListener` when talking to existing enterprise systems using JMS APIs.
- Mix all three in one application if you bridge different messaging systems.

## 3. Core concept

Each annotation maps to an auto-configured listener container factory:

| Annotation | Starter | Auto-configured factory |
|---|---|---|
| `@JmsListener` | `spring-boot-starter-artemis` / `-activemq` | `DefaultJmsListenerContainerFactory` |
| `@RabbitListener` | `spring-boot-starter-amqp` | `SimpleRabbitListenerContainerFactory` |
| `@KafkaListener` | `spring-boot-starter-kafka` | `ConcurrentKafkaListenerContainerFactory` |

Auto-config reads properties:
- JMS: `spring.jms.*` (concurrency, session acknowledge mode).
- AMQP: `spring.rabbitmq.*` (host, port, concurrency, acknowledge mode).
- Kafka: `spring.kafka.consumer.*` (group-id, auto-offset-reset, deserializer).

Common features across all three:
- **Concurrency:** set via the annotation (`concurrency = "3-10"` for RabbitMQ, `concurrency = "3"` for Kafka) or properties.
- **Error handling:** pluggable `ErrorHandler` / `ConsumerAwareErrorHandler` / `CommonErrorHandler`.
- **Manual acknowledgement:** switch from auto-ack to manual ack for at-least-once guarantees.
- **Payload conversion:** a `MessageConverter` bean converts bytes/JSON to POJOs automatically.

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three messaging brokers each paired with Spring auto-configured listener container and annotation-driven consumer method">
  <!-- JMS path -->
  <rect x="10" y="25" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="65" y="49" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Artemis / JMS</text>

  <line x1="124" y1="45" x2="190" y2="45" stroke="#6db33f" stroke-width="1.5" marker-end="url(#la)"/>
  <rect x="195" y="28" width="150" height="34" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="270" y="45" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">DefaultJmsListenerContainer</text>
  <text x="270" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Factory (auto-config)</text>

  <line x1="348" y1="45" x2="415" y2="45" stroke="#6db33f" stroke-width="1.5" marker-end="url(#la)"/>
  <rect x="420" y="20" width="280" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="38" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@JmsListener(destination="orders.queue")</text>
  <text x="560" y="53" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">void onOrder(Order order) { ... }</text>

  <!-- AMQP path -->
  <rect x="10" y="85" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="65" y="109" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RabbitMQ / AMQP</text>

  <line x1="124" y1="105" x2="190" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#la)"/>
  <rect x="195" y="88" width="150" height="34" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="270" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">SimpleRabbitListener</text>
  <text x="270" y="117" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ContainerFactory (auto-config)</text>

  <line x1="348" y1="105" x2="415" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#la)"/>
  <rect x="420" y="80" width="280" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="98" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@RabbitListener(queues="orders-queue")</text>
  <text x="560" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">void onOrder(Order order) { ... }</text>

  <!-- Kafka path -->
  <rect x="10" y="145" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="65" y="169" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Apache Kafka</text>

  <line x1="124" y1="165" x2="190" y2="165" stroke="#6db33f" stroke-width="1.5" marker-end="url(#la)"/>
  <rect x="195" y="148" width="150" height="34" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="270" y="165" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">ConcurrentKafkaListener</text>
  <text x="270" y="177" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ContainerFactory (auto-config)</text>

  <line x1="348" y1="165" x2="415" y2="165" stroke="#6db33f" stroke-width="1.5" marker-end="url(#la)"/>
  <rect x="420" y="140" width="280" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="158" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@KafkaListener(topics="orders", groupId="svc")</text>
  <text x="560" y="173" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">void onOrder(Order order) { ... }</text>

  <defs>
    <marker id="la" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Each broker has its own auto-configured factory; the annotation wires the consumer method to that factory.

## 5. Runnable example

```java
// ListenerAutoConfigDemo.java — demonstrates all three listener annotations conceptually
// How to run: java ListenerAutoConfigDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add the appropriate starter and the annotations work as shown

import java.util.*;
import java.util.function.Consumer;

public class ListenerAutoConfigDemo {

    // Simulated listener container factory — starts/stops listeners
    static class ListenerContainer {
        final String type;
        final String destination;
        final Consumer<String> handler;
        final int concurrency;

        ListenerContainer(String type, String destination, Consumer<String> handler, int concurrency) {
            this.type = type; this.destination = destination;
            this.handler = handler; this.concurrency = concurrency;
        }

        void deliver(String message) {
            System.out.printf("[%s container -> %s] thread-%d handling: '%s'%n",
                    type, destination, (int)(Math.random() * concurrency), message);
            handler.accept(message);
        }
    }

    // === Simulated @JmsListener ===
    // @JmsListener(destination = "orders.queue")
    static void jmsOnOrder(String payload) {
        System.out.println("  [JmsListener] processed: " + payload);
    }

    // === Simulated @RabbitListener ===
    // @RabbitListener(queues = "notifications-queue")
    static void rabbitOnNotification(String payload) {
        System.out.println("  [RabbitListener] processed: " + payload);
    }

    // === Simulated @KafkaListener ===
    // @KafkaListener(topics = "events", groupId = "demo-group")
    static void kafkaOnEvent(String payload) {
        System.out.println("  [KafkaListener] processed: " + payload);
    }

    public static void main(String[] args) {
        System.out.println("=== @JmsListener / @RabbitListener / @KafkaListener Auto-config Demo ===\n");

        // Spring Boot auto-config creates these factories from starters + properties
        List<ListenerContainer> containers = List.of(
            new ListenerContainer("DefaultJmsListenerContainerFactory",
                "orders.queue",           ListenerAutoConfigDemo::jmsOnOrder,          1),
            new ListenerContainer("SimpleRabbitListenerContainerFactory",
                "notifications-queue",    ListenerAutoConfigDemo::rabbitOnNotification, 3),
            new ListenerContainer("ConcurrentKafkaListenerContainerFactory",
                "events [group=demo]",    ListenerAutoConfigDemo::kafkaOnEvent,         5)
        );

        System.out.println("--- Delivering messages to each listener ---\n");
        containers.get(0).deliver("Order #1001: Widget x2");
        containers.get(0).deliver("Order #1002: Gadget x1");

        containers.get(1).deliver("User signup: alice@example.com");
        containers.get(1).deliver("Payment confirmed: #P99");

        containers.get(2).deliver("user.login: {userId:42}");
        containers.get(2).deliver("product.viewed: {sku:W100}");

        System.out.println("\n--- Key differences ---");
        System.out.println("JMS:     session-based ack, transactional, exactly-once possible");
        System.out.println("AMQP:    channel-based ack, prefetch count, dead-letter exchange");
        System.out.println("Kafka:   offset commit, consumer group rebalancing, replay supported");
    }
}
```

**How to run:** `java ListenerAutoConfigDemo.java`

## 6. Walkthrough

- **`ListenerContainer`** mimics what Spring's auto-configured factory creates per `@*Listener`-annotated method. The factory reads the annotation's metadata (destination/queue/topic, concurrency) and sets up the polling loop.
- **`concurrency`** shows the key difference: Kafka's `ConcurrentKafkaListenerContainerFactory` defaults to 1 but can be raised up to the partition count; RabbitMQ's factory supports variable concurrency with a min-max range.
- **`deliver`** simulates the poll-decode-dispatch cycle: the container pulls from the broker, deserialises the payload via `MessageConverter`, and calls the annotated method.
- The three printouts show each annotation working against its own broker abstraction, but the developer-facing code is identical in structure.

## 7. Gotchas & takeaways

> `@KafkaListener` without `groupId` **falls back to the application name** as the group ID — easy to forget, causes two applications to share a group unintentionally.

> `@RabbitListener` uses **auto-ack by default**. If your method throws an exception after the ack, the message is lost. Set `acknowledgeMode: MANUAL` and inject `Channel` + `long deliveryTag` to ack explicitly.

- Multiple `@JmsListener`/`@RabbitListener`/`@KafkaListener` methods can coexist in one Spring Boot app.
- Custom `*ListenerContainerFactory` beans override the auto-configured one: name it exactly `jmsListenerContainerFactory`, `rabbitListenerContainerFactory`, or `kafkaListenerContainerFactory`.
- `@KafkaListener(topicPattern = "orders\\..*")` subscribes to all topics matching a regex — useful for multi-tenant setups.
- Inject `Acknowledgment ack` (Kafka) or `Channel channel, long tag` (AMQP) for manual offset/ack control.
- Spring Boot Actuator exposes listener container metrics via `spring.jms.*`, `rabbitmq.*`, and `kafka.consumer.*` metric families.
