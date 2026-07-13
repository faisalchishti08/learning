---
card: microservices
gi: 151
slug: spring-amqp-rabbitmq-rabbittemplate-rabbitlistener
title: "Spring AMQP / RabbitMQ (RabbitTemplate, @RabbitListener)"
---

## 1. What it is

Spring AMQP is the lower-level Spring integration for RabbitMQ, parallel in role to [Spring for Apache Kafka](0149-spring-for-apache-kafka-kafkatemplate-kafkalistener.md): `RabbitTemplate` provides a direct, imperative API for publishing messages to a RabbitMQ exchange with a routing key, and `@RabbitListener` is a method-level annotation that subscribes a method directly to a named queue, exposing RabbitMQ's own AMQP concepts — exchanges, routing keys, bindings, queues — without a broker-agnostic abstraction layer in between.

## 2. Why & when

RabbitMQ's routing model is genuinely richer than a simple named-topic model: an exchange (direct, topic, fanout, or headers-based) decides how an incoming message's routing key gets matched against one or more queue bindings, enabling sophisticated fan-out and selective routing patterns that don't map cleanly onto Spring Cloud Stream's simpler, more broker-agnostic destination model. Spring AMQP exposes this routing model directly, letting application code declare exchanges, queues, and bindings explicitly and publish with fine-grained routing key control.

Reach for Spring AMQP directly when a service is committed to RabbitMQ specifically and needs its distinctive routing capabilities — topic-pattern routing, fanout broadcast to multiple queues, header-based routing — or needs fine control over queue properties (TTL, max length, priority) that a broker-agnostic abstraction wouldn't expose as directly. Use [Spring Cloud Stream](0147-spring-cloud-stream-kafka-rabbitmq-pulsar-binders.md)'s RabbitMQ binder instead when broker portability or the simpler functional binding model outweighs the need for RabbitMQ's full routing flexibility.

## 3. Core concept

`RabbitTemplate.convertAndSend` publishes to a named exchange with a specific routing key; RabbitMQ's exchange type and the queue's binding pattern together determine which queue(s) actually receive the message; `@RabbitListener` on a method subscribes it directly to a named queue, with the framework handling deserialization of the delivered payload.

```java
@Autowired RabbitTemplate rabbitTemplate;

void placeOrder(int orderId, String region) {
    // routing key "order.us.42" -- a TOPIC exchange can route this based on PATTERN matching
    rabbitTemplate.convertAndSend("order-exchange", "order." + region + "." + orderId, new OrderPlaced(orderId));
}

@RabbitListener(queues = "us-orders-queue") // bound to order-exchange with pattern "order.us.*"
void onUsOrder(OrderPlaced order) { processUsOrder(order); }
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RabbitTemplate publishes to a topic exchange with a routing key like order.us.42; the exchange routes the message to queues whose bindings pattern-match the routing key, and an @RabbitListener-annotated method consumes directly from one of those queues" >
  <rect x="20" y="70" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">RabbitTemplate</text>
  <text x="85" y="106" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">key: order.us.42</text>

  <rect x="200" y="60" width="150" height="65" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="275" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">order-exchange</text>
  <text x="275" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">type: topic</text>
  <text x="275" y="112" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">pattern match routing</text>

  <rect x="410" y="30" width="200" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="52" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">us-orders-queue (order.us.*)</text>
  <rect x="410" y="130" width="200" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="510" y="152" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">eu-orders-queue (order.eu.*) -- no match</text>

  <line x1="150" y1="92" x2="198" y2="92" stroke="#8b949e" marker-end="url(#arr32)"/>
  <line x1="350" y1="85" x2="408" y2="48" stroke="#8b949e" marker-end="url(#arr32)"/>

  <defs>
    <marker id="arr32" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The routing key `order.us.42` matches `us-orders-queue`'s binding pattern but not `eu-orders-queue`'s — routing decided entirely by the exchange, not by application code.

## 5. Runnable example

Scenario: an order-routing service modeled first with a single, undifferentiated destination (no real routing), then with a simulated topic exchange applying pattern-based routing to multiple queues, and finally extended to show a fanout exchange broadcasting to every bound queue regardless of routing key, contrasting the two exchange types' fundamentally different behavior.

### Level 1 — Basic

```java
// File: SingleUndifferentiatedQueue.java -- everything goes to ONE queue; no
// routing decision is ever made, the problem RabbitMQ's exchange model solves.
import java.util.*;

public class SingleUndifferentiatedQueue {
    record OrderPlaced(int orderId, String region) {}

    public static void main(String[] args) {
        List<OrderPlaced> theOnlyQueue = new ArrayList<>();
        theOnlyQueue.add(new OrderPlaced(42, "us"));
        theOnlyQueue.add(new OrderPlaced(43, "eu"));

        System.out.println("Every consumer of this queue sees BOTH us and eu orders, with no routing distinction at all: " + theOnlyQueue);
        System.out.println("A consumer that only cares about US orders has to filter manually, every time.");
    }
}
```

**How to run:** `javac SingleUndifferentiatedQueue.java && java SingleUndifferentiatedQueue` (JDK 17+).

### Level 2 — Intermediate

```java
// File: TopicExchangeRouting.java -- simulates a RabbitMQ topic exchange:
// routing key PATTERNS on queue bindings determine which queue(s) receive a message.
import java.util.*;
import java.util.function.*;

public class TopicExchangeRouting {
    record OrderPlaced(int orderId, String region) {}

    static class TopicExchange {
        // each binding is a (pattern, queue) pair -- "*" matches exactly one routing-key segment
        record Binding(String pattern, List<OrderPlaced> queue, String queueName) {}
        List<Binding> bindings = new ArrayList<>();

        void bindQueue(String pattern, String queueName) {
            bindings.add(new Binding(pattern, new ArrayList<>(), queueName));
        }

        void publish(String routingKey, OrderPlaced message) {
            System.out.println("[RabbitTemplate] publishing with routingKey='" + routingKey + "': " + message);
            for (Binding b : bindings) {
                if (matches(b.pattern(), routingKey)) {
                    b.queue().add(message);
                    System.out.println("  -> matched binding '" + b.pattern() + "', routed to " + b.queueName());
                }
            }
        }

        // simplified pattern match: "*" matches exactly one dot-separated segment
        boolean matches(String pattern, String routingKey) {
            String[] patternParts = pattern.split("\\.");
            String[] keyParts = routingKey.split("\\.");
            if (patternParts.length != keyParts.length) return false;
            for (int i = 0; i < patternParts.length; i++) {
                if (!patternParts[i].equals("*") && !patternParts[i].equals(keyParts[i])) return false;
            }
            return true;
        }
    }

    public static void main(String[] args) {
        TopicExchange orderExchange = new TopicExchange();
        orderExchange.bindQueue("order.us.*", "us-orders-queue");
        orderExchange.bindQueue("order.eu.*", "eu-orders-queue");

        orderExchange.publish("order.us.42", new OrderPlaced(42, "us"));
        orderExchange.publish("order.eu.43", new OrderPlaced(43, "eu"));

        System.out.println("us-orders-queue: " + orderExchange.bindings.get(0).queue());
        System.out.println("eu-orders-queue: " + orderExchange.bindings.get(1).queue());
    }
}
```

**How to run:** `javac TopicExchangeRouting.java && java TopicExchangeRouting` (JDK 17+).

Expected output:
```
[RabbitTemplate] publishing with routingKey='order.us.42': OrderPlaced[orderId=42, region=us]
  -> matched binding 'order.us.*', routed to us-orders-queue
[RabbitTemplate] publishing with routingKey='order.eu.43': OrderPlaced[orderId=43, region=eu]
  -> matched binding 'order.eu.*', routed to eu-orders-queue
us-orders-queue: [OrderPlaced[orderId=42, region=us]]
eu-orders-queue: [OrderPlaced[orderId=43, region=eu]]
```

Each order lands only in the queue whose binding pattern matches its routing key — the exchange, not application code, made this routing decision.

### Level 3 — Advanced

```java
// File: FanoutVsTopicExchange.java -- a FANOUT exchange broadcasts to EVERY bound
// queue regardless of routing key, contrasted directly against topic exchange's selective routing.
import java.util.*;

public class FanoutVsTopicExchange {
    record OrderPlaced(int orderId, String region) {}

    static class FanoutExchange { // ignores routing key ENTIRELY -- every bound queue gets everything
        List<List<OrderPlaced>> boundQueues = new ArrayList<>();
        List<String> queueNames = new ArrayList<>();
        void bindQueue(String queueName) { boundQueues.add(new ArrayList<>()); queueNames.add(queueName); }
        void publish(String ignoredRoutingKey, OrderPlaced message) {
            System.out.println("[FanoutExchange] publishing (routing key IGNORED): " + message);
            for (int i = 0; i < boundQueues.size(); i++) {
                boundQueues.get(i).add(message);
                System.out.println("  -> broadcast to " + queueNames.get(i));
            }
        }
    }

    public static void main(String[] args) {
        FanoutExchange auditExchange = new FanoutExchange(); // e.g. for audit-logging EVERY order, regardless of region
        auditExchange.bindQueue("audit-log-queue");
        auditExchange.bindQueue("analytics-queue");
        auditExchange.bindQueue("fraud-detection-queue");

        auditExchange.publish("order.us.42", new OrderPlaced(42, "us")); // routing key is IRRELEVANT to a fanout exchange
        auditExchange.publish("order.eu.43", new OrderPlaced(43, "eu"));

        System.out.println("audit-log-queue:       " + auditExchange.boundQueues.get(0));
        System.out.println("analytics-queue:       " + auditExchange.boundQueues.get(1));
        System.out.println("fraud-detection-queue: " + auditExchange.boundQueues.get(2));
        System.out.println("ALL THREE queues received BOTH orders -- fanout ignores routing key entirely, unlike topic exchange's pattern-selective routing.");
    }
}
```

**How to run:** `javac FanoutVsTopicExchange.java && java FanoutVsTopicExchange` (JDK 17+).

Expected output:
```
[FanoutExchange] publishing (routing key IGNORED): OrderPlaced[orderId=42, region=us]
  -> broadcast to audit-log-queue
  -> broadcast to analytics-queue
  -> broadcast to fraud-detection-queue
[FanoutExchange] publishing (routing key IGNORED): OrderPlaced[orderId=43, region=eu]
  -> broadcast to audit-log-queue
  -> broadcast to analytics-queue
  -> broadcast to fraud-detection-queue
audit-log-queue:       [OrderPlaced[orderId=42, region=us], OrderPlaced[orderId=43, region=eu]]
analytics-queue:       [OrderPlaced[orderId=42, region=us], OrderPlaced[orderId=43, region=eu]]
fraud-detection-queue: [OrderPlaced[orderId=42, region=us], OrderPlaced[orderId=43, region=eu]]
```

## 6. Walkthrough

1. **Level 1** — `theOnlyQueue` receives both a `"us"` and an `"eu"` order with no distinguishing routing mechanism at all; any consumer wanting only US orders must inspect and filter every message manually, since nothing upstream ever made a routing decision.
2. **Level 2, declaring bindings with patterns** — `bindQueue("order.us.*", "us-orders-queue")` registers a `Binding` associating a routing-key pattern with a named queue, mirroring RabbitMQ's actual `@Queue`/`@Binding`/`@Exchange` declaration style in Spring AMQP.
3. **Level 2, matching at publish time** — `publish` calls `matches(b.pattern(), routingKey)` for every registered binding, and only appends the message to a queue whose pattern genuinely matches; `"order.us.42"` matches `"order.us.*"` (the `*` matching the final `"42"` segment) but not `"order.eu.*"`.
4. **Level 2, the routing decision made externally** — neither the publisher nor any consumer contains an `if (region.equals("us"))` check; the exchange's pattern-matching logic alone determined that `"us-orders-queue"` received the US order and `"eu-orders-queue"` did not — exactly mirroring how a real RabbitMQ topic exchange performs routing independent of both publisher and consumer code.
5. **Level 3, a fanout exchange ignoring the routing key entirely** — `FanoutExchange.publish` takes a `routingKey` parameter but never reads it in its logic; every single bound queue receives every published message, unconditionally, which is the defining behavior of a fanout exchange as opposed to a topic exchange's selective, pattern-based routing.
6. **Level 3, three queues bound for different purposes** — `audit-log-queue`, `analytics-queue`, and `fraud-detection-queue` are bound to the same `FanoutExchange`, modeling a realistic use case: broadcasting every order event to multiple independent downstream concerns that each need to see everything, unlike Level 2's region-selective routing.
7. **Level 3, the contrast made explicit** — both orders (US and EU) appear in all three queues' final contents, directly demonstrating that fanout exchange behavior is structurally different from — not just a special case of — topic exchange's pattern-matched selective routing shown in Level 2; choosing the wrong exchange type for a given use case (fanout when selective routing was needed, or vice versa) produces either unwanted broadcast noise or missing messages.

## 7. Gotchas & takeaways

> **Gotcha:** exchange type is chosen once, at declaration time, and changing it later (say, from `direct` to `topic`) generally requires deleting and recreating the exchange in RabbitMQ, since exchange type is immutable for a given exchange name — plan the routing model (direct, topic, fanout, or headers) deliberately up front rather than assuming it can be adjusted freely later without any migration.

- Spring AMQP exposes RabbitMQ's own routing model directly: `RabbitTemplate` publishes with an explicit routing key to a named exchange, and `@RabbitListener` subscribes a method to a named queue.
- A topic exchange routes based on pattern-matching the routing key against each bound queue's binding pattern, enabling selective, hierarchical routing that a simple named-destination model can't express.
- A fanout exchange ignores the routing key entirely and broadcasts every message to every bound queue, suited to "every interested consumer needs to see everything" use cases.
- This direct exposure of RabbitMQ's routing model is Spring AMQP's key trade-off versus Spring Cloud Stream's broker-agnostic abstraction: more routing power, at the cost of RabbitMQ-specific application code.
- Exchange type is fixed at declaration time and generally cannot be changed for an existing exchange without recreating it, making the initial choice of exchange type a genuinely consequential, hard-to-reverse decision.
