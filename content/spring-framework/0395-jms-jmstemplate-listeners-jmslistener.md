---
card: spring-framework
gi: 395
slug: jms-jmstemplate-listeners-jmslistener
title: "JMS (JmsTemplate, listeners, @JmsListener)"
---

## 1. What it is

Spring's JMS support wraps the Java Message Service API — the standard Java interface for messaging brokers like ActiveMQ or Artemis — with the same template pattern used elsewhere in Spring. `JmsTemplate` sends messages without you managing connections, sessions, or producers by hand, and `@JmsListener` lets a plain method become a message consumer just by annotating it, without writing a manual `MessageListener` implementation.

```java
@Service
class OrderNotifier {
    private final JmsTemplate jmsTemplate;
    OrderNotifier(JmsTemplate jmsTemplate) { this.jmsTemplate = jmsTemplate; }

    void notifyOrderPlaced(String orderId) {
        jmsTemplate.convertAndSend("orders.queue", orderId);
    }

    @JmsListener(destination = "orders.queue")
    void onOrderPlaced(String orderId) {
        System.out.println("Processing order: " + orderId);
    }
}
```

## 2. Why & when

Raw JMS requires opening a `Connection`, starting a `Session`, creating a `MessageProducer` or `MessageConsumer`, and carefully closing all of it — plus translating exceptions from JMS's checked `JMSException` into something your code can reasonably handle. `JmsTemplate` exists for the same reason `JdbcTemplate` exists for JDBC: it handles resource lifecycle and exception translation so your code only expresses *what* to send or *what* to do with a received message.

Reach for Spring's JMS support when:

- Your system already uses a JMS broker (ActiveMQ, Artemis, IBM MQ) for asynchronous communication between services.
- You need reliable, decoupled, asynchronous processing — a request that shouldn't block the caller (e.g., "send this email" or "process this order") gets queued instead of handled inline.
- You want automatic retry/redelivery semantics that a message broker provides out of the box, rather than building retry logic into synchronous HTTP calls.

If your organization is standardizing on lighter-weight or cloud-native messaging (Kafka, RabbitMQ via AMQP, or cloud pub/sub), you'd use Spring's dedicated support for those instead — JMS specifically applies when the broker speaks the JMS protocol.

## 3. Core concept

```
Producer side:                          Consumer side:

 OrderNotifier                           @JmsListener method
      |                                        ^
      v                                        |
 JmsTemplate.convertAndSend(dest, obj)     DefaultMessageListenerContainer
      |                                        ^
      v                                        |
 MessageConverter (Object -> Message)      MessageConverter (Message -> Object)
      |                                        ^
      v                                        |
        JMS Broker (queue/topic: "orders.queue")
```

`JmsTemplate` on the send side and the listener container on the receive side are mirror images of each other: both hide connection/session management, and both delegate object-to-`Message` conversion to a shared `MessageConverter`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JmsTemplate sends to a queue, a listener container delivers to an annotated method">
  <rect x="10" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JmsTemplate.send()</text>

  <rect x="245" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="92" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Broker</text>
  <text x="320" y="108" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">orders.queue</text>

  <rect x="480" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@JmsListener</text>
  <text x="555" y="108" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">onOrderPlaced()</text>

  <line x1="160" y1="95" x2="240" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <line x1="395" y1="95" x2="475" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

The producer and the consumer never talk to each other directly — both only ever talk to the broker.

## 5. Runnable example

### Level 1 — Basic

An embedded ActiveMQ broker (running in-process, so no external server is needed) with a plain `JmsTemplate` send and a manually configured `MessageListener` receive, using raw JMS to show the moving parts before wrapping them.

```java
import jakarta.jms.ConnectionFactory;
import org.apache.activemq.artemis.jms.client.ActiveMQJMSConnectionFactory;
import org.springframework.jms.core.JmsTemplate;
import org.springframework.jms.listener.SimpleMessageListenerContainer;

public class JmsBasic {

    public static void main(String[] args) throws InterruptedException {
        // Embedded broker via Artemis "vm" (in-VM) connector — no separate process needed for this demo.
        ConnectionFactory connectionFactory = new ActiveMQJMSConnectionFactory("vm://0");

        JmsTemplate jmsTemplate = new JmsTemplate(connectionFactory);

        SimpleMessageListenerContainer container = new SimpleMessageListenerContainer();
        container.setConnectionFactory(connectionFactory);
        container.setDestinationName("orders.queue");
        container.setMessageListener(message ->
                System.out.println("Received: " + message));
        container.start();

        jmsTemplate.convertAndSend("orders.queue", "order-42");

        Thread.sleep(500); // demo-only: let the async listener print before main exits
        container.stop();
    }
}
```

How to run: add `spring-jms` and an embedded broker (e.g. `org.apache.activemq:artemis-jakarta-server` or run against a local ActiveMQ instance's URL instead of `vm://0`), then `java JmsBasic.java`.

`JmsTemplate.convertAndSend` opens a connection, sends the string as a JMS `TextMessage`, and closes the connection — one call replaces roughly a dozen lines of raw JMS API calls. `SimpleMessageListenerContainer` runs in the background on its own thread, invoking the `MessageListener` callback whenever a message arrives on `orders.queue`.

### Level 2 — Intermediate

Real applications don't manage a `SimpleMessageListenerContainer` by hand — they use `@JmsListener` inside a Spring context, and they send/receive typed objects (not raw strings) via a configured `MessageConverter`.

```java
import jakarta.jms.ConnectionFactory;
import org.apache.activemq.artemis.jms.client.ActiveMQJMSConnectionFactory;
import org.springframework.context.annotation.*;
import org.springframework.jms.annotation.EnableJms;
import org.springframework.jms.annotation.JmsListener;
import org.springframework.jms.core.JmsTemplate;
import org.springframework.jms.support.converter.MappingJackson2MessageConverter;
import org.springframework.jms.support.converter.MessageType;

import java.io.Serializable;

public class JmsIntermediate {

    record OrderPlaced(String orderId, int quantity) implements Serializable {}

    @Configuration
    @EnableJms
    static class JmsConfig {
        @Bean
        ConnectionFactory connectionFactory() {
            return new ActiveMQJMSConnectionFactory("vm://0");
        }

        @Bean
        JmsTemplate jmsTemplate(ConnectionFactory cf) {
            JmsTemplate template = new JmsTemplate(cf);
            template.setMessageConverter(jacksonConverter());
            return template;
        }

        @Bean
        MappingJackson2MessageConverter jacksonConverter() {
            var converter = new MappingJackson2MessageConverter();
            converter.setTargetType(MessageType.TEXT);
            converter.setTypeIdPropertyName("_type");
            return converter;
        }
    }

    @org.springframework.stereotype.Component
    static class OrderListener {
        @JmsListener(destination = "orders.queue")
        void onOrderPlaced(OrderPlaced order) {
            System.out.println("Processing " + order.quantity() + "x for order " + order.orderId());
        }
    }

    public static void main(String[] args) throws InterruptedException {
        var context = new AnnotationConfigApplicationContext(JmsConfig.class, OrderListener.class);
        JmsTemplate jmsTemplate = context.getBean(JmsTemplate.class);

        jmsTemplate.convertAndSend("orders.queue", new OrderPlaced("order-42", 3));

        Thread.sleep(500);
        context.close();
    }
}
```

How to run: add `spring-jms`, `spring-context`, Jackson, and an embedded/real broker dependency, then `java JmsIntermediate.java`.

`@EnableJms` activates the infrastructure that scans for `@JmsListener`-annotated methods and wires a `DefaultJmsListenerContainerFactory` behind the scenes — you never construct a listener container manually. The `MappingJackson2MessageConverter` serializes `OrderPlaced` to JSON text on send, and `@JmsListener`'s parameter type (`OrderPlaced`) tells Spring what to deserialize incoming messages into automatically.

### Level 3 — Advanced

Production JMS listeners need error handling: an exception in the listener shouldn't silently swallow the message, and unrecoverable failures need somewhere to go (a dead-letter queue) instead of retrying forever. This adds concurrency, acknowledgment control, and an error handler.

```java
import jakarta.jms.ConnectionFactory;
import org.apache.activemq.artemis.jms.client.ActiveMQJMSConnectionFactory;
import org.springframework.context.annotation.*;
import org.springframework.jms.annotation.EnableJms;
import org.springframework.jms.annotation.JmsListener;
import org.springframework.jms.config.DefaultJmsListenerContainerFactory;
import org.springframework.jms.core.JmsTemplate;
import org.springframework.jms.support.converter.MappingJackson2MessageConverter;
import org.springframework.jms.support.converter.MessageType;
import org.springframework.util.ErrorHandler;

import java.io.Serializable;
import java.util.concurrent.atomic.AtomicInteger;

public class JmsAdvanced {

    record OrderPlaced(String orderId, int quantity) implements Serializable {}

    @Configuration
    @EnableJms
    static class JmsConfig {
        @Bean
        ConnectionFactory connectionFactory() {
            return new ActiveMQJMSConnectionFactory("vm://0");
        }

        @Bean
        MappingJackson2MessageConverter jacksonConverter() {
            var converter = new MappingJackson2MessageConverter();
            converter.setTargetType(MessageType.TEXT);
            converter.setTypeIdPropertyName("_type");
            return converter;
        }

        @Bean
        JmsTemplate jmsTemplate(ConnectionFactory cf, MappingJackson2MessageConverter conv) {
            JmsTemplate template = new JmsTemplate(cf);
            template.setMessageConverter(conv);
            return template;
        }

        @Bean
        DefaultJmsListenerContainerFactory jmsListenerContainerFactory(
                ConnectionFactory cf, MappingJackson2MessageConverter conv) {
            var factory = new DefaultJmsListenerContainerFactory();
            factory.setConnectionFactory(cf);
            factory.setMessageConverter(conv);
            factory.setConcurrency("3-10");           // scale 3 to 10 concurrent consumers
            factory.setSessionTransacted(true);        // ack only after listener returns cleanly
            factory.setErrorHandler(errorHandler());
            return factory;
        }

        @Bean
        ErrorHandler errorHandler() {
            return t -> System.err.println("Listener error, message will be redelivered: " + t.getMessage());
        }
    }

    @org.springframework.stereotype.Component
    static class OrderListener {
        private final AtomicInteger attempts = new AtomicInteger();

        @JmsListener(destination = "orders.queue", containerFactory = "jmsListenerContainerFactory")
        void onOrderPlaced(OrderPlaced order) {
            if (attempts.incrementAndGet() < 2) {
                throw new IllegalStateException("Simulated transient failure, will redeliver");
            }
            System.out.println("Successfully processed order " + order.orderId() + " on attempt " + attempts.get());
        }
    }

    public static void main(String[] args) throws InterruptedException {
        var context = new AnnotationConfigApplicationContext(JmsConfig.class, OrderListener.class);
        JmsTemplate jmsTemplate = context.getBean(JmsTemplate.class);

        jmsTemplate.convertAndSend("orders.queue", new OrderPlaced("order-42", 3));

        Thread.sleep(1000); // demo-only: allow the transactional redelivery to occur
        context.close();
    }
}
```

How to run: same dependencies as Level 2, then `java JmsAdvanced.java`.

`setSessionTransacted(true)` means the session only commits (acknowledging the message to the broker) if the listener method returns normally — an exception rolls the session back, and the broker redelivers the message, which is exactly why the demo listener succeeds "on attempt 2" without any manual retry code. `setConcurrency("3-10")` lets the container scale its consumer threads with load. The `ErrorHandler` bean logs each failed delivery instead of letting it disappear silently.

## 6. Walkthrough

Trace `JmsAdvanced.main` end to end:

1. **Context starts.** Spring builds the `ConnectionFactory`, `JmsTemplate`, and a `DefaultJmsListenerContainerFactory` configured for transactions, concurrency, and error handling; `@EnableJms` scans `OrderListener` and registers its `@JmsListener` method against that factory, starting a live `DefaultMessageListenerContainer` with 3 initial consumer threads listening on `orders.queue`.
2. **Send.** `jmsTemplate.convertAndSend("orders.queue", new OrderPlaced("order-42", 3))` uses the Jackson converter to turn the record into a JSON `TextMessage` and publishes it to the broker.

   ```
   Message on orders.queue:
     body: {"_type":"...JmsAdvanced$OrderPlaced","orderId":"order-42","quantity":3}
   ```
3. **First delivery attempt.** One of the container's consumer threads picks up the message, the Jackson converter deserializes it back into an `OrderPlaced` record, and calls `onOrderPlaced(order)`.
4. **Simulated failure.** Inside the listener, `attempts.incrementAndGet()` returns `1`, which is less than `2`, so the method throws `IllegalStateException`.
5. **Transactional rollback.** Because `setSessionTransacted(true)` is set, the container rolls back the JMS session instead of acknowledging the message — from the broker's point of view, the message was never successfully consumed, so it stays eligible for redelivery. The registered `ErrorHandler` also runs, printing the error.
6. **Second delivery attempt.** The broker redelivers the same message (often to the same or another consumer thread in the pool). `attempts.incrementAndGet()` now returns `2`, the `if` condition is false, and the method completes normally, printing `"Successfully processed order order-42 on attempt 2"`.
7. **Commit.** Because the listener returned without throwing, the container commits the session, which acknowledges the message to the broker — it will not be redelivered again.

```
send OrderPlaced --> broker queue
   consumer picks up --> listener throws --> rollback --> broker keeps message
   broker redelivers --> listener succeeds --> commit --> message removed
```

## 7. Gotchas & takeaways

> Gotcha: without `setSessionTransacted(true)` (or an equivalent acknowledgment mode), the default auto-acknowledge behavior acknowledges the message as soon as it's *delivered*, not after the listener finishes successfully — an exception thrown mid-processing can silently lose the message instead of triggering redelivery. Always set an explicit acknowledgment strategy that matches your durability requirements.

- `JmsTemplate` and `@JmsListener` mirror `JdbcTemplate`/`@Transactional` in spirit: both hide low-level resource management behind a small, focused API surface.
- Configure a `MessageConverter` explicitly (Jackson-based, in most modern code) so producers and consumers exchange typed domain objects instead of hand-rolled string parsing.
- Set concurrency (`factory.setConcurrency("min-max")`) to match expected load — a single consumer thread serializes all message processing, which is rarely what you want in production.
- Pair transactional or client-acknowledge sessions with a dead-letter queue configuration on the broker so messages that fail redelivery repeatedly don't loop forever — that configuration lives on the broker, not in Spring, but Spring's redelivery behavior is what feeds it.
