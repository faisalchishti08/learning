---
card: system-design
gi: 120
slug: spring-amqp-rabbitmq
title: Spring AMQP / RabbitMQ
---

## 1. What it is

**Spring AMQP** is Spring's library for working with message brokers that speak the Advanced Message Queuing Protocol (AMQP), most commonly **RabbitMQ**. Unlike Kafka's topic-and-partition model, RabbitMQ routes messages through **exchanges** to **queues** based on routing rules, giving more flexible routing patterns at the cost of not retaining messages for replay the way a Kafka log does. `RabbitTemplate` sends messages; `@RabbitListener` marks a method to receive them — the same template/annotation shape as Spring Kafka, applied to a different kind of broker.

## 2. Why & when

Choose Spring AMQP/RabbitMQ when your messaging needs are closer to task distribution and flexible routing than to a durable, replayable event log: a classic [point-to-point work queue](0110-message-queues-point-to-point.md), routing a message to different queues based on its type or attributes, or needing complex fan-out patterns (send to multiple queues based on a routing key, not just "everyone subscribed to this exact topic"). Kafka tends to fit better for high-throughput event streams that need replay; RabbitMQ tends to fit better for classic task-queue and flexible-routing scenarios.

## 3. Core concept

- **Exchange:** the entry point a producer publishes to; it does not store messages itself, but routes them to one or more queues based on the exchange's type and a routing key.
- **Exchange types:** a **direct** exchange routes a message to the queue(s) bound with a matching routing key exactly; a **topic** exchange matches routing keys with wildcard patterns (e.g. `orders.*.created`); a **fanout** exchange ignores the routing key and sends to every bound queue (similar to [pub/sub](0111-publish-subscribe.md)).
- **Queue:** where messages actually sit until a consumer picks them up — RabbitMQ's queues behave like the [point-to-point queues](0110-message-queues-point-to-point.md) already covered, with competing consumers.
- **Binding:** the rule connecting an exchange to a queue, with an optional routing key pattern, defining which messages published to that exchange end up in that queue.
- **`RabbitTemplate` and `@RabbitListener`:** `rabbitTemplate.convertAndSend(exchange, routingKey, message)` publishes; `@RabbitListener(queues = "...")` marks a method to consume from a specific queue — note this listens on a queue directly, not an exchange, since exchanges do not store messages.

## 4. Diagram

```
  Producer                Exchange "orders-exchange" (type: topic)
     |                           |
     v                           |  routing key "orders.eu.created"
  rabbitTemplate.convertAndSend  |
  ("orders-exchange",            +----- binding "orders.eu.*" -----> Queue "eu-orders"
   "orders.eu.created", msg)     |
                                 +----- binding "orders.*.created" -> Queue "all-created-orders"

  A single publish can match MULTIPLE bindings and land in
  MULTIPLE queues, unlike Kafka's single-topic-partition model.

  @RabbitListener(queues = "eu-orders")   <- consumes directly from a queue
```
*Caption: an exchange routes one published message to any number of bound queues based on routing-key rules, before any consumer is involved.*

## 5. Runnable example

**Level 1 — Basic.** A direct exchange routes a message to the one queue bound with a matching routing key.

**Level 2 — Topic exchange with wildcard routing.** A message matches multiple bindings and lands in multiple queues.

**Level 3 — `@RabbitListener`-style consumption.** A listener consumes from one specific queue, independent of which exchange or routing key delivered the message there.

```java
// SpringAmqpDemo.java
import java.util.*;
import java.util.function.*;

public class SpringAmqpDemo {

    record Binding(String routingKeyPattern, String queueName) {
        boolean matches(String routingKey) {
            String regex = routingKeyPattern.replace(".", "\\.").replace("*", "[^.]+");
            return routingKey.matches(regex);
        }
    }

    static List<Binding> bindings = new ArrayList<>();
    static Map<String, List<String>> queues = new HashMap<>();

    // Models rabbitTemplate.convertAndSend(exchange, routingKey, message).
    static void rabbitTemplateSend(String routingKey, String message) {
        for (Binding b : bindings) {
            if (b.matches(routingKey)) {
                queues.computeIfAbsent(b.queueName(), q -> new ArrayList<>()).add(message);
            }
        }
    }

    public static void main(String[] args) {
        // Level 1: direct-style binding - exact routing key match.
        bindings.add(new Binding("orders.eu.created", "eu-orders-exact"));
        rabbitTemplateSend("orders.eu.created", "order-100");
        System.out.println("eu-orders-exact queue: " + queues.get("eu-orders-exact"));

        // Level 2: topic exchange with wildcard bindings - one message can match multiple queues.
        bindings.add(new Binding("orders.eu.*", "eu-orders-any-status"));
        bindings.add(new Binding("orders.*.created", "all-created-orders"));

        rabbitTemplateSend("orders.eu.created", "order-101");

        System.out.println("eu-orders-exact queue: " + queues.get("eu-orders-exact"));
        System.out.println("eu-orders-any-status queue: " + queues.get("eu-orders-any-status"));
        System.out.println("all-created-orders queue: " + queues.get("all-created-orders"));
        System.out.println("-> ONE publish matched THREE bindings, landing the same message in three separate queues");

        // A message for a different region/status should NOT match the eu-specific bindings.
        rabbitTemplateSend("orders.us.shipped", "order-102");
        System.out.println("after a US 'shipped' event, eu-orders-exact still: " + queues.get("eu-orders-exact") + " (unaffected)");

        // Level 3: @RabbitListener-style consumption - a listener consumes from ONE specific queue.
        Consumer<String> euOrdersListener = msg -> System.out.println("  [@RabbitListener(queues=\"eu-orders-any-status\")] processing: " + msg);
        for (String msg : queues.getOrDefault("eu-orders-any-status", List.of())) {
            euOrdersListener.accept(msg);
        }
    }
}
```

**How to run:** save as `SpringAmqpDemo.java`, then run `java SpringAmqpDemo.java`. (A real Spring Boot app would declare `Exchange`, `Queue`, and `Binding` beans via `@Configuration`, inject `RabbitTemplate`, and use `@RabbitListener(queues = "eu-orders-any-status")` with the `spring-boot-starter-amqp` dependency.)

## 6. Walkthrough

1. `Binding.matches` converts a routing-key pattern like `"orders.eu.*"` into a regular expression, letting `*` stand in for exactly one dot-separated segment — modeling RabbitMQ's topic-exchange wildcard matching.
2. Level 1 registers one exact binding and sends a message with the matching routing key; it lands in `eu-orders-exact`, as printed.
3. Level 2 adds two more, wildcard-based bindings, then sends `"order-101"` with routing key `"orders.eu.created"`. This single routing key matches all three registered bindings (`orders.eu.created`, `orders.eu.*`, and `orders.*.created`), so `rabbitTemplateSend` places the message into three separate queues.
4. Sending `"order-102"` with routing key `"orders.us.shipped"` matches none of the EU-specific bindings, so `eu-orders-exact` remains unchanged — confirming the routing key genuinely determines placement.
5. Level 3 models `@RabbitListener(queues = "eu-orders-any-status")` as a plain method reading everything currently in that one queue — showing that a consumer only cares about which *queue* it listens to, entirely decoupled from whatever exchange or routing key logic put messages there.

## 7. Gotchas & takeaways

> Gotcha: because a topic exchange can route one message into several queues at once, the same logical event can be processed by several unrelated consumers, each unaware of the others — this is by design (similar to pub/sub) but means changing a binding's routing-key pattern can silently start (or stop) delivering messages to a queue whose consumer was not touched at all. Review bindings carefully before changing routing-key patterns in a live system.

- Spring AMQP wraps RabbitMQ's exchange-and-queue model in the same `Template`/`@Listener` shape Spring uses for Kafka, but the underlying routing model is different and more flexible.
- An exchange routes a published message to zero, one, or many bound queues based on its type (direct, topic, fanout) and the routing key; queues, not exchanges, are what `@RabbitListener` actually consumes from.
- Topic exchanges with wildcard bindings let one event fan out to multiple, independently defined queues without the producer knowing about any of them.
- Related concepts: [Message queues (point-to-point)](0110-message-queues-point-to-point.md) (what a RabbitMQ queue itself behaves like once a consumer attaches), [Publish/subscribe](0111-publish-subscribe.md) (the pattern a fanout exchange most resembles), [Spring for Apache Kafka](0119-spring-for-apache-kafka-kafkatemplate-kafkalistener.md) (the topic-and-partition alternative for event streaming).
