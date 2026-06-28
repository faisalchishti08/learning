---
card: spring-boot
gi: 166
slug: jms-activemq-artemis
title: JMS (ActiveMQ Artemis)
---

## 1. What it is

**JMS (Java Message Service)** is a Java API for sending messages between two programs without them needing to be connected at the same time. Spring Boot auto-configures JMS when it detects **ActiveMQ Artemis** on the classpath, giving you a ready-to-use `JmsTemplate` and `@JmsListener` support with zero boilerplate.

ActiveMQ Artemis is the embedded broker Spring Boot can run in-process, so you can develop and test JMS code without spinning up a separate server.

## 2. Why & when

**Why:** HTTP is synchronous — the sender waits for the receiver. JMS lets you fire-and-forget: the sender drops a message in a queue and moves on. The receiver processes it when it's ready. This decouples services in time.

**When to use:**
- Long-running jobs (email sending, PDF generation) that must not block the HTTP response.
- Work queues where you need guaranteed delivery and retry on failure.
- Point-to-point communication between two services where exactly-one-consumer semantics matter.

**Not ideal for:** high-throughput event streams (use Kafka) or browser-push notifications (use WebSocket/SSE).

## 3. Core concept

JMS has two messaging models:

1. **Queue (point-to-point):** One producer, one consumer. Each message is delivered to exactly one receiver. Think of a ticketing kiosk — one ticket goes to one person.
2. **Topic (publish-subscribe):** One producer, many consumers all get a copy. Think of a newsletter.

Spring Boot auto-configuration path with Artemis:
1. Add `spring-boot-starter-artemis` dependency.
2. Spring Boot detects Artemis on classpath, creates an in-process broker automatically if no remote URL is set.
3. A `JmsTemplate` bean appears — use it to send. A `DefaultJmsListenerContainerFactory` appears — annotate methods with `@JmsListener` to consume.

Key properties: `spring.artemis.mode` (`embedded` or `native`), `spring.artemis.host`, `spring.artemis.port`.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JMS producer sends to queue, broker holds message, consumer receives">
  <!-- Producer -->
  <rect x="20" y="70" width="140" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="100" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Producer</text>
  <text x="90" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">JmsTemplate.send()</text>

  <!-- Arrow to broker -->
  <line x1="165" y1="105" x2="260" y2="105" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>

  <!-- Broker / Queue -->
  <rect x="265" y="55" width="150" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="82" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Artemis Broker</text>
  <rect x="285" y="92" width="110" height="26" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="340" y="110" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Queue / Topic</text>
  <text x="340" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">guaranteed delivery</text>

  <!-- Arrow to consumer -->
  <line x1="420" y1="105" x2="515" y2="105" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>

  <!-- Consumer -->
  <rect x="520" y="70" width="140" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="590" y="100" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Consumer</text>
  <text x="590" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@JmsListener</text>

  <text x="340" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Producer and consumer run independently; broker persists messages between them</text>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Producer and consumer never call each other directly — the broker holds messages between them.

## 5. Runnable example

```java
// JmsDemo.java — illustrates JMS send/receive using plain javax/jakarta messaging API
// How to run: java JmsDemo.java  (JDK 17+; simulates the contract without a broker)
// In a real Spring Boot project add spring-boot-starter-artemis and use JmsTemplate/@JmsListener

import java.util.ArrayDeque;
import java.util.Queue;

public class JmsDemo {

    // Simulated message queue (in real JMS this lives in the broker)
    static final Queue<String> queue = new ArrayDeque<>();

    // Producer: sends messages to the queue
    static void jmsTemplateSend(String destination, String payload) {
        System.out.println("[Producer] Sending to '" + destination + "': " + payload);
        queue.offer("[" + destination + "] " + payload);
    }

    // Consumer: @JmsListener equivalent — processes one message
    static void onMessage(String message) {
        System.out.println("[Consumer] @JmsListener received: " + message);
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== JMS (ActiveMQ Artemis) Demo ===\n");

        // 1. Producer sends two messages
        jmsTemplateSend("orders.queue", "Order #1001: 2x Widget");
        jmsTemplateSend("orders.queue", "Order #1002: 1x Gadget");

        System.out.println("\n[Broker] Queue depth: " + queue.size() + " messages\n");

        // 2. Consumer processes messages asynchronously
        Thread.sleep(500); // simulate async gap
        while (!queue.isEmpty()) {
            onMessage(queue.poll());
        }

        System.out.println("\n[Broker] Queue depth after processing: " + queue.size());
        System.out.println("\nIn Spring Boot: add spring-boot-starter-artemis,");
        System.out.println("inject JmsTemplate to send, annotate method with @JmsListener to receive.");
    }
}
```

**How to run:** `java JmsDemo.java` — no dependencies needed. Output shows the producer/broker/consumer lifecycle.

## 6. Walkthrough

- **`jmsTemplateSend`** simulates `JmsTemplate.convertAndSend(destination, payload)` — real Spring wraps serialisation and connection management.
- **`queue.offer`** acts as the broker queue — in Artemis this persists to disk for guaranteed delivery.
- **`Thread.sleep(500)`** represents the key JMS benefit: the producer finished and moved on; the consumer processes later, independently.
- **`onMessage`** simulates a `@JmsListener`-annotated method — Spring calls it on a background thread for each incoming message.
- The consumer loop drains the queue, matching what `DefaultJmsListenerContainerFactory` does with concurrent listener threads in production.

Real Spring Boot setup: `spring.artemis.mode=embedded` uses an in-process broker; switch to `spring.artemis.mode=native` with `spring.artemis.host`/`port` for a remote broker.

## 7. Gotchas & takeaways

> `JmsTemplate` is **synchronous by default** when calling `receiveAndConvert()` — it blocks waiting for a message. Always use `@JmsListener` for non-blocking consumption.

> Embedded Artemis stores messages **in-memory only** unless you configure persistence (`spring.artemis.embedded.persistent=true`). Restart = lost messages if not configured.

- Add `spring-boot-starter-artemis` for embedded broker; no separate server needed in dev/test.
- `JmsTemplate.convertAndSend(destination, object)` uses a `MessageConverter` (default: `SimpleMessageConverter` for strings, `MappingJackson2MessageConverter` for JSON).
- `@JmsListener(destination = "orders.queue")` on a method wires it as a listener automatically.
- Topic vs queue: inject `pubSubDomain = true` on the `@JmsListener` or `JmsListenerContainerFactory` for topic semantics.
- For production: set acknowledgement mode, configure dead-letter queues, and tune listener concurrency.
