---
card: spring-boot
gi: 167
slug: amqp-rabbitmq
title: AMQP (RabbitMQ)
---

## 1. What it is

**AMQP (Advanced Message Queuing Protocol)** is an open standard wire protocol for message brokers. **RabbitMQ** is the most popular broker implementing it. Spring Boot auto-configures AMQP support via `spring-boot-starter-amqp`, providing `RabbitTemplate` for sending, `RabbitAdmin` for broker management, and `@RabbitListener` for consuming — all with a single dependency.

Unlike JMS (which is a Java-only API), AMQP is protocol-level, so any language can interoperate with RabbitMQ.

## 2. Why & when

**Why over JMS:** AMQP's exchange/binding/queue model is more flexible. You can broadcast, route by key, or fan-out using the same broker without changing producer code.

**When to use:**
- Complex routing rules: route `payment.*` messages to one queue, `shipping.*` to another.
- Multi-language microservices that share one broker (Python consumers, Java producers).
- Fan-out: one message → many queues (different teams each get a copy of every order).
- When you need the broker outside the JVM (RabbitMQ runs as a standalone server).

**Not ideal for:** log-style streams where replay and consumer lag tracking matter (use Kafka).

## 3. Core concept

AMQP adds an **exchange** layer between producer and queue:

1. **Producer** publishes to an **exchange** with a **routing key**.
2. **Exchange** applies binding rules to decide which **queues** receive the message.
3. **Consumer** reads from a **queue**.

Exchange types:
- `direct` — exact routing key match.
- `fanout` — all bound queues get a copy (routing key ignored).
- `topic` — pattern match (`orders.*`, `#.error`).
- `headers` — match by message headers.

Spring Boot auto-creates a `RabbitTemplate` and `RabbitAdmin`. Declare queues, exchanges, and bindings as `@Bean` and `RabbitAdmin` creates them on the broker at startup.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Producer publishes to exchange which routes to queues consumed by consumers">
  <!-- Producer -->
  <rect x="15" y="80" width="120" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="106" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Producer</text>
  <text x="75" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">RabbitTemplate</text>

  <!-- Arrow -->
  <line x1="140" y1="110" x2="215" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#ra)"/>
  <text x="178" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">routing key</text>

  <!-- Exchange -->
  <rect x="220" y="72" width="120" height="76" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="280" y="100" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Exchange</text>
  <text x="280" y="116" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">topic / direct</text>
  <text x="280" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">binding rules</text>

  <!-- Arrows to queues -->
  <line x1="345" y1="95" x2="420" y2="75" stroke="#6db33f" stroke-width="2" marker-end="url(#ra)"/>
  <line x1="345" y1="125" x2="420" y2="145" stroke="#6db33f" stroke-width="2" marker-end="url(#ra)"/>

  <!-- Queue A -->
  <rect x="425" y="52" width="110" height="44" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="480" y="74" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">orders.queue</text>
  <text x="480" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">orders.#</text>

  <!-- Queue B -->
  <rect x="425" y="122" width="110" height="44" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="480" y="144" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">audit.queue</text>
  <text x="480" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">#</text>

  <!-- Consumers -->
  <line x1="540" y1="74" x2="600" y2="74" stroke="#79c0ff" stroke-width="2" marker-end="url(#rb)"/>
  <rect x="605" y="55" width="85" height="38" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="647" y="79" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Consumer A</text>

  <line x1="540" y1="144" x2="600" y2="144" stroke="#79c0ff" stroke-width="2" marker-end="url(#rb)"/>
  <rect x="605" y="125" width="85" height="38" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="647" y="149" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Consumer B</text>

  <text x="350" y="210" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Exchange routes by binding pattern; both consumers receive matching messages</text>

  <defs>
    <marker id="ra" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Topic exchange fans messages to multiple queues based on routing-key patterns.

## 5. Runnable example

```java
// AmqpDemo.java — simulates RabbitMQ exchange/queue routing without a broker
// How to run: java AmqpDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add spring-boot-starter-amqp; use RabbitTemplate / @RabbitListener

import java.util.*;

public class AmqpDemo {

    record Message(String routingKey, String body) {}

    // Simulated exchange bindings: pattern -> queue name
    static final Map<String, String[]> bindings = new LinkedHashMap<>();
    static final Map<String, Queue<String>> brokerQueues = new LinkedHashMap<>();

    static void bindQueue(String pattern, String queueName) {
        bindings.put(pattern, new String[]{queueName});
        brokerQueues.putIfAbsent(queueName, new ArrayDeque<>());
    }

    // Topic exchange routing: '#' matches zero-or-more words, '*' matches exactly one
    static boolean matchesTopic(String pattern, String key) {
        String[] pp = pattern.split("\\.");
        String[] kk = key.split("\\.");
        return matchWords(pp, kk, 0, 0);
    }
    static boolean matchWords(String[] p, String[] k, int pi, int ki) {
        if (pi == p.length && ki == k.length) return true;
        if (pi < p.length && p[pi].equals("#"))
            return matchWords(p, k, pi + 1, ki) ||
                   (ki < k.length && matchWords(p, k, pi, ki + 1));
        if (pi < p.length && ki < k.length &&
            (p[pi].equals("*") || p[pi].equals(k[ki])))
            return matchWords(p, k, pi + 1, ki + 1);
        return false;
    }

    // Simulate exchange publish
    static void publish(String routingKey, String body) {
        System.out.println("[Producer] publish  key='" + routingKey + "'  body='" + body + "'");
        bindings.forEach((pattern, targets) -> {
            if (matchesTopic(pattern, routingKey)) {
                brokerQueues.get(targets[0]).offer(body);
                System.out.println("  -> routed to queue: " + targets[0]);
            }
        });
    }

    public static void main(String[] args) {
        System.out.println("=== AMQP / RabbitMQ Topic Exchange Demo ===\n");

        // Declare queues and bindings (RabbitAdmin does this in Spring Boot)
        bindQueue("orders.#",  "orders-queue");
        bindQueue("#",          "audit-queue");   // receives everything

        System.out.println("Bindings configured:\n");

        // Publish messages
        publish("orders.created", "Order #1001 placed");
        publish("orders.shipped", "Order #1001 shipped");
        publish("payments.failed", "Payment #P99 failed");

        System.out.println("\n--- Consumer processing ---");
        // @RabbitListener equivalent
        drainQueue("orders-queue", msg -> System.out.println("[OrdersConsumer] " + msg));
        drainQueue("audit-queue",  msg -> System.out.println("[AuditConsumer]  " + msg));
    }

    static void drainQueue(String name, java.util.function.Consumer<String> handler) {
        Queue<String> q = brokerQueues.get(name);
        System.out.println("\nQueue '" + name + "' (" + q.size() + " messages):");
        while (!q.isEmpty()) handler.accept(q.poll());
    }
}
```

**How to run:** `java AmqpDemo.java` — no dependencies needed.

## 6. Walkthrough

- **`bindQueue("orders.#", "orders-queue")`** sets up a topic binding: `orders.created`, `orders.shipped`, etc. all match. In Spring Boot this is a `@Bean TopicExchange` + `Binding`.
- **`bindQueue("#", "audit-queue")`** catches everything — the audit queue gets every message.
- **`publish`** simulates `RabbitTemplate.convertAndSend(exchange, routingKey, message)`.
- **`matchesTopic`** implements AMQP topic pattern matching (`#` = zero-or-more words, `*` = exactly one).
- **`drainQueue`** simulates `@RabbitListener(queues = "orders-queue")` on a method.
- Note `payments.failed` goes to `audit-queue` (bound to `#`) but not `orders-queue` (bound to `orders.#`).

## 7. Gotchas & takeaways

> `RabbitTemplate.convertAndSend` **does not block** waiting for a response. For request-reply patterns use `convertSendAndReceive`, but note it holds a thread while waiting.

> Queues **survive restarts only if declared durable** (`new Queue("name", true)`). Transient queues lose messages when RabbitMQ restarts.

- `spring.rabbitmq.host/port/username/password` configure the connection; no separate auto-start unlike Artemis.
- `@RabbitListener(queues = "my-queue")` on a Spring bean method is the simplest consumer.
- Use `MessageConverter` bean (e.g., `Jackson2JsonMessageConverter`) to auto-serialize/deserialize POJOs.
- `RabbitAdmin` auto-creates exchanges, queues, and bindings declared as beans — no manual broker setup during development.
- Dead-letter queues (`x-dead-letter-exchange`) handle messages that exceed retry limits.
