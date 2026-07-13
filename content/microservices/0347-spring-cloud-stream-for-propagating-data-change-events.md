---
card: microservices
gi: 347
slug: spring-cloud-stream-for-propagating-data-change-events
title: "Spring Cloud Stream for propagating data-change events"
---

## 1. What it is

**Spring Cloud Stream** lets a service publish and consume messages using plain Java functions (`Supplier`, `Function`, `Consumer` beans) without writing broker-specific code — the same application code can run against Kafka, RabbitMQ, or another supported broker just by swapping a **binder** dependency and configuration, with the messaging library's specifics (topics, exchanges, partitions) abstracted behind Spring Cloud Stream's own binding configuration.

## 2. Why & when

Propagating a data-change event — an `OrderPlaced` event feeding a [read model](0315-keeping-read-models-in-sync-via-events.md), a [reporting database](0316-reporting-analytics-database.md), or another service's [saga](0320-saga-pattern.md) step — requires publishing and consuming messages, and every messaging technology has its own client API. Spring Cloud Stream exists so that application code expressing "when this data changes, publish an event" or "when I receive this event, do this" doesn't need to be written against Kafka's `Producer`/`Consumer` API specifically, or RabbitMQ's channel API specifically — it's written once, as ordinary Java functions, and the binder handles the broker-specific plumbing.

Use Spring Cloud Stream when you want to propagate data-change events without tightly coupling your application code to one specific messaging technology's client library, or when a team maintains services on different brokers and wants a consistent programming model across them. For very broker-specific features (Kafka transactions, as in the earlier topic, or RabbitMQ-specific routing), you may still reach for that broker's native Spring integration directly — Spring Cloud Stream's abstraction is strongest for straightforward publish/consume patterns.

## 3. Core concept

A `Supplier<T>` bean produces outbound messages, a `Consumer<T>` bean processes inbound messages, and a `Function<T, R>` bean transforms an inbound message into an outbound one — Spring Cloud Stream's binder wires each to an actual broker destination (a Kafka topic, a RabbitMQ exchange) based on configuration, not code, so the same `Consumer<OrderPlacedEvent>` bean works whether the underlying broker is Kafka or RabbitMQ.

```java
@Bean
public Consumer<OrderPlacedEvent> handleOrderPlaced() {
    return event -> updateReadModel(event); // no Kafka or RabbitMQ API visible here at all
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code defines a plain Consumer function; Spring Cloud Stream's binder connects it to either a Kafka topic or a RabbitMQ exchange depending on configuration, with no broker-specific code in the function itself">
  <rect x="20" y="60" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Consumer&lt;OrderPlacedEvent&gt;</text>
  <text x="110" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">plain Java, no broker API</text>

  <line x1="200" y1="85" x2="270" y2="85" stroke="#8b949e" marker-end="url(#a347)"/>
  <rect x="280" y="60" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="340" y="88" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Binder</text>

  <line x1="400" y1="75" x2="470" y2="40" stroke="#3fb950" marker-end="url(#a347b)"/>
  <rect x="480" y="15" width="130" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="545" y="37" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Kafka topic</text>

  <line x1="400" y1="95" x2="470" y2="130" stroke="#f0883e" marker-end="url(#a347c)"/>
  <rect x="480" y="115" width="130" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="545" y="137" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">RabbitMQ exchange</text>

  <defs>
    <marker id="a347" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a347b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a347c" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

The same application-level `Consumer` function is wired to whichever broker the configured binder targets, with no broker-specific code in the function.

## 5. Runnable example

Scenario: a read-model consumer, first written directly against a simulated broker-specific client API, then rebuilt using a broker-agnostic function-based style matching Spring Cloud Stream's model, and finally shown running against two different simulated "binders" (Kafka-like and RabbitMQ-like) with zero changes to the consuming function itself.

### Level 1 — Basic

```java
// File: BrokerSpecificConsumer.java -- consumer code written DIRECTLY
// against a simulated broker client's specific API.
import java.util.*;

public class BrokerSpecificConsumer {
    record OrderPlacedEvent(String orderId) {}
    static Map<String, String> readModel = new HashMap<>();

    // Imagine this uses Kafka's actual Consumer/ConsumerRecord API directly.
    static void kafkaSpecificPollLoop(List<OrderPlacedEvent> simulatedKafkaRecords) {
        for (OrderPlacedEvent record : simulatedKafkaRecords) { // KAFKA-shaped API, e.g. ConsumerRecords iteration
            readModel.put(record.orderId(), "PLACED");
            System.out.println("kafka-specific consumer processed: " + record.orderId());
        }
    }

    public static void main(String[] args) {
        kafkaSpecificPollLoop(List.of(new OrderPlacedEvent("order-1")));
        System.out.println("Read model: " + readModel);
        System.out.println("This code is TIED to Kafka's specific consumer API shape -- switching brokers means rewriting it.");
    }
}
```

How to run: `java BrokerSpecificConsumer.java`

`kafkaSpecificPollLoop` is written in a shape specific to how a Kafka consumer might be polled and iterated — standing in for real Kafka client code. If the team later needed to switch to RabbitMQ, this method's structure (and everything using it) would need meaningful rewriting.

### Level 2 — Intermediate

```java
// File: BrokerAgnosticFunctionStyle.java -- the SAME logic expressed as
// a plain java.util.function.Consumer, matching Spring Cloud Stream's
// programming model -- NOTHING broker-specific appears in the function.
import java.util.*;
import java.util.function.Consumer;

public class BrokerAgnosticFunctionStyle {
    record OrderPlacedEvent(String orderId) {}
    static Map<String, String> readModel = new HashMap<>();

    // This is exactly the shape of a Spring Cloud Stream @Bean Consumer<T> function.
    static Consumer<OrderPlacedEvent> handleOrderPlaced() {
        return event -> {
            readModel.put(event.orderId(), "PLACED");
            System.out.println("broker-agnostic consumer processed: " + event.orderId());
        };
    }

    // Simulates the FRAMEWORK delivering messages to the function -- application code never sees this part.
    static void deliverMessages(Consumer<OrderPlacedEvent> handler, List<OrderPlacedEvent> messages) {
        messages.forEach(handler);
    }

    public static void main(String[] args) {
        Consumer<OrderPlacedEvent> handler = handleOrderPlaced();
        deliverMessages(handler, List.of(new OrderPlacedEvent("order-1")));

        System.out.println("Read model: " + readModel);
        System.out.println("This SAME function would work unchanged whether the binder targets Kafka OR RabbitMQ.");
    }
}
```

How to run: `java BrokerAgnosticFunctionStyle.java`

`handleOrderPlaced` returns a plain `Consumer<OrderPlacedEvent>` with zero broker-specific types or API calls inside it. `deliverMessages` stands in for Spring Cloud Stream's binder infrastructure, which is responsible for actually pulling messages off whichever broker is configured and calling this function — the function itself has no idea what broker delivered the message.

### Level 3 — Advanced

```java
// File: SameFunctionTwoBinders.java -- the IDENTICAL Consumer function is
// run against TWO different simulated binders (Kafka-like and
// RabbitMQ-like), with NO changes to the function itself -- only the
// binder configuration differs.
import java.util.*;
import java.util.function.Consumer;

public class SameFunctionTwoBinders {
    record OrderPlacedEvent(String orderId) {}
    static Map<String, String> readModel = new HashMap<>();

    // The ONE piece of application code -- completely broker-agnostic.
    static Consumer<OrderPlacedEvent> handleOrderPlaced() {
        return event -> {
            readModel.put(event.orderId(), "PLACED");
            System.out.println("  [handler] processed " + event.orderId());
        };
    }

    // Simulated Kafka binder -- delivers messages in its own KAFKA-shaped way internally, but calls the SAME function.
    static void kafkaBinderDeliver(Consumer<OrderPlacedEvent> handler, List<OrderPlacedEvent> topicMessages) {
        System.out.println("Kafka binder: polling topic 'orders'...");
        topicMessages.forEach(handler);
    }

    // Simulated RabbitMQ binder -- delivers messages in its own RABBITMQ-shaped way internally, but calls the SAME function.
    static void rabbitBinderDeliver(Consumer<OrderPlacedEvent> handler, List<OrderPlacedEvent> queueMessages) {
        System.out.println("RabbitMQ binder: consuming from queue 'orders.queue'...");
        queueMessages.forEach(handler);
    }

    public static void main(String[] args) {
        Consumer<OrderPlacedEvent> handler = handleOrderPlaced(); // built ONCE, application code never changes

        System.out.println("--- Configuration A: binder = kafka ---");
        kafkaBinderDeliver(handler, List.of(new OrderPlacedEvent("order-1")));

        System.out.println("--- Configuration B: binder = rabbit (SAME handler bean, different broker) ---");
        rabbitBinderDeliver(handler, List.of(new OrderPlacedEvent("order-2")));

        System.out.println("Read model (built by the SAME function, via TWO different brokers): " + readModel);
    }
}
```

How to run: `java SameFunctionTwoBinders.java`

`handler` is constructed exactly once from `handleOrderPlaced()` and never modified. `kafkaBinderDeliver` and `rabbitBinderDeliver` each simulate a different broker's delivery mechanism (polling a topic versus consuming from a queue), but both simply call the identical `handler` function with their respective messages. The final `readModel` shows entries from both `"order-1"` (delivered via the Kafka-style path) and `"order-2"` (delivered via the RabbitMQ-style path) — proving the same application logic served both, unmodified, exactly as Spring Cloud Stream's binder abstraction is designed to allow via configuration alone.

## 6. Walkthrough

Trace `SameFunctionTwoBinders.main` in order. **First**, `handler` is created once by calling `handleOrderPlaced()`, which returns a lambda closing over `readModel` — this single object is reused for both subsequent deliveries, with no per-broker variant needed.

**Next**, `kafkaBinderDeliver(handler, List.of(new OrderPlacedEvent("order-1")))` runs: it prints a Kafka-specific-sounding log line (standing in for the binder's internal, broker-specific polling logic) and then calls `topicMessages.forEach(handler)`, which invokes `handler.accept(...)` for the one message — inside the lambda, `readModel.put("order-1", "PLACED")` runs, and a processed-message log line prints.

**Then**, `rabbitBinderDeliver(handler, List.of(new OrderPlacedEvent("order-2")))` runs: it prints a RabbitMQ-specific-sounding log line and calls `queueMessages.forEach(handler)`, invoking the *exact same* `handler` object again — this time for `"order-2"`. Inside the lambda, `readModel.put("order-2", "PLACED")` runs.

**Finally**, `main` prints `readModel`, which contains entries for both `"order-1"` and `"order-2"` — both produced by calling the identical `handler` function, once via a simulated Kafka delivery path and once via a simulated RabbitMQ delivery path, with the application-level function itself completely unaware of and unaffected by which broker actually delivered each message.

```
handler = handleOrderPlaced()   -- built ONCE, broker-agnostic

kafkaBinderDeliver(handler, [order-1])  -> handler.accept(order-1) -> readModel[order-1]=PLACED
rabbitBinderDeliver(handler, [order-2]) -> handler.accept(order-2) -> readModel[order-2]=PLACED

Final readModel: {order-1: PLACED, order-2: PLACED}  -- same function, two different brokers
```

## 7. Gotchas & takeaways

> Spring Cloud Stream's abstraction covers common publish/consume patterns well, but broker-specific features (Kafka transactions, RabbitMQ's specific routing/exchange types) may require dropping down to that broker's native Spring integration for full control — don't expect every advanced, broker-specific capability to have an equivalent abstracted knob in Spring Cloud Stream's configuration.

- Spring Cloud Stream lets application code express publish/consume logic as plain `Supplier`/`Function`/`Consumer` beans, with broker specifics (Kafka, RabbitMQ, others) handled entirely by a configurable binder.
- The same function can run unmodified against different brokers, since binder configuration — not application code — determines which broker and destination a function is wired to.
- This is well suited to propagating data-change events (feeding [read models](0315-keeping-read-models-in-sync-via-events.md), [reporting databases](0316-reporting-analytics-database.md), or downstream services) without coupling that application logic to one specific broker's client library.
- For broker-specific advanced features, reach directly for that broker's native Spring integration (e.g., [Spring for Apache Kafka transactions](0345-spring-for-apache-kafka-transactions.md)) rather than expecting Spring Cloud Stream's abstraction to expose every capability.
