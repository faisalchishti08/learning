---
card: microservices
gi: 547
slug: spring-cloud-stream-event-driven
title: "Spring Cloud Stream (event-driven)"
---

## 1. What it is

**Spring Cloud Stream** provides a common programming model for building event-driven, message-based services, decoupling application code from any specific message broker (Kafka, RabbitMQ) behind a "binder" abstraction. Instead of writing code against Kafka's or RabbitMQ's specific client APIs directly, you write plain functions (`java.util.function.Function`, `Supplier`, `Consumer`) that Spring Cloud Stream automatically wires to message channels — publishing to, or consuming from, whichever broker is configured via the active binder, without the business logic itself ever referencing broker-specific concepts like topics, exchanges, or partitions directly.

## 2. Why & when

You reach for Spring Cloud Stream whenever a service produces or consumes messages, and you want the actual messaging logic decoupled from a specific broker's client API:

- **Coding directly against Kafka's or RabbitMQ's native client API couples business logic to that specific broker's concepts and configuration model** — switching brokers later (or supporting both, in different deployments) would require rewriting the actual message-handling code, not just reconfiguring it.
- **Spring Cloud Stream's functional programming model lets you express "what happens to a message" as a plain function**, independent of how that function is triggered or where its output goes — a `Function<OrderEvent, ShippingEvent>` reads naturally as "given an order event, produce a shipping event," with the actual subscription, publishing, serialization, and broker-specific wiring handled entirely by the framework based on configuration.
- **The binder abstraction is what makes a broker swap purely a configuration and dependency change** — replacing `spring-cloud-stream-binder-kafka` with `spring-cloud-stream-binder-rabbit` changes which broker your functions are actually wired to, without touching the functions' own code at all.
- **You reach for it specifically for event-driven, message-based communication between services** (as opposed to direct, synchronous request/response calls) — a natural fit whenever a service should react to something happening elsewhere, or broadcast that something happened, without a direct, blocking dependency on whoever's on the other end.

## 3. Core concept

Think of a mail sorting facility with universal chutes and slots, where any worker can define "when a package matching this description arrives, do this with it" without needing to know or care whether the package physically arrived by truck, train, or plane — the facility's own infrastructure handles the actual physical routing regardless of transport mode, and the worker's job description ("process packages of this kind") stays the same no matter which transport method happened to be used that day. Spring Cloud Stream's functional bindings play exactly this role: your function describes "given this kind of message, do this," and the framework's binder infrastructure handles the actual broker-specific mechanics of how that message physically arrived or where its output physically goes.

Concretely:

1. **A `Function<InputType, OutputType>` bean processes an incoming message and produces an outgoing one** — Spring Cloud Stream automatically subscribes it to an input binding and publishes its return value to an output binding, both named and configured externally, not in the function's own code.
2. **A `Supplier<OutputType>` bean produces messages without any input** — often paired with `@PollableBean` or a periodic trigger, useful for a service originating events rather than reacting to them.
3. **A `Consumer<InputType>` bean processes incoming messages with no output** — useful for a terminal action (writing to a database, triggering a side effect) that doesn't produce a further event.
4. **Binder-specific configuration (topic names, partition counts, consumer group IDs) lives entirely in `application.yml`**, keyed by the function's bean name — the function itself never references any of these broker-specific details directly, which is what allows the underlying broker to be swapped via configuration alone.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A plain Function bean is automatically wired to input and output message channels by Spring Cloud Stream's binder, which is swappable between Kafka and RabbitMQ via configuration alone">
  <rect x="20" y="80" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">input topic/queue</text>

  <rect x="250" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Function&lt;In, Out&gt;</text>
  <text x="340" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">plain business logic, no broker API</text>

  <rect x="500" y="80" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">output topic/queue</text>

  <line x1="160" y1="100" x2="250" y2="100" stroke="#8b949e" marker-end="url(#a12)"/>
  <line x1="430" y1="100" x2="500" y2="100" stroke="#8b949e" marker-end="url(#a12)"/>
  <text x="330" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">binder (Kafka or RabbitMQ) is a swappable configuration detail underneath</text>
  <defs><marker id="a12" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

A plain function is wired to input/output channels by the binder infrastructure, keeping the actual message broker a swappable configuration detail.

## 5. Runnable example

Scenario: processing an order-placed event into a shipping-requested event. We start with a plain Java model of broker-coupled message handling, extend it to a decoupled functional version, then show the real Spring Cloud Stream `Function` bean shape.

### Level 1 — Basic

```java
// File: BrokerCoupledHandling.java -- models code coupled DIRECTLY to
// a specific broker's API shape -- switching brokers means rewriting this.
public class BrokerCoupledHandling {
    // imagine this mirrors a specific broker client's actual API surface
    static void kafkaConsumerLoop() {
        String rawMessage = "{\"orderId\":\"42\",\"item\":\"widget\"}"; // "received" from a specific Kafka topic
        System.out.println("[Kafka-specific consumer] received: " + rawMessage);

        String shippingEvent = "{\"orderId\":\"42\",\"action\":\"ship\"}";
        System.out.println("[Kafka-specific producer] publishing to Kafka topic: " + shippingEvent);
    }

    public static void main(String[] args) {
        kafkaConsumerLoop();
        System.out.println("Problem: this logic is entangled with Kafka-specific consume/produce calls directly.");
    }
}
```

How to run: `java BrokerCoupledHandling.java`

The business logic (deciding to produce a shipping event from an order event) is entangled directly with broker-specific consume and produce calls — moving to RabbitMQ would require rewriting this method entirely, since the broker API and the business logic aren't separated at all.

### Level 2 — Intermediate

```java
// File: DecoupledFunctionalModel.java -- separates the BUSINESS LOGIC
// (a plain function) from the MESSAGING INFRASTRUCTURE (modeled here as
// a generic dispatcher that could be wired to ANY broker).
import java.util.function.Function;

public class DecoupledFunctionalModel {
    // pure business logic: given an order event, produce a shipping event -- NO broker API referenced at all
    static Function<String, String> orderToShipping = orderEventJson -> {
        String orderId = orderEventJson.replaceAll(".*\"orderId\":\"(\\d+)\".*", "$1");
        return "{\"orderId\":\"" + orderId + "\",\"action\":\"ship\"}";
    };

    // a GENERIC dispatcher, standing in for what a real binder does: receive from SOME source, apply the
    // function, publish to SOME destination -- the actual broker is irrelevant to this dispatching logic
    static void dispatch(Function<String, String> function, String incomingMessage) {
        System.out.println("[generic dispatcher] received: " + incomingMessage);
        String result = function.apply(incomingMessage);
        System.out.println("[generic dispatcher] publishing: " + result);
    }

    public static void main(String[] args) {
        dispatch(orderToShipping, "{\"orderId\":\"42\",\"item\":\"widget\"}");
        System.out.println("orderToShipping never referenced Kafka OR RabbitMQ -- only the dispatcher would need to change per broker.");
    }
}
```

How to run: `java DecoupledFunctionalModel.java`

`orderToShipping` is a plain `Function<String, String>` containing only business logic — no broker API appears anywhere in it. `dispatch` stands in for what Spring Cloud Stream's binder infrastructure does: receiving a message from wherever it actually came from, applying the function, and publishing wherever the result should actually go — the function itself stays identical regardless of which real broker `dispatch`'s real implementation would connect to.

### Level 3 — Advanced

```java
// File: SpringCloudStreamRealShape.java -- the REAL Spring Cloud Stream
// shape: a Function bean, automatically bound to input/output channels
// by the framework based on configuration, with NO broker-specific code.
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.function.Function;

public class SpringCloudStreamRealShape {

    record OrderPlacedEvent(String orderId, String item) {}
    record ShippingRequestedEvent(String orderId, String action) {}

    @Configuration
    static class StreamFunctions {

        // Spring Cloud Stream automatically binds this to an input channel ("orderToShipping-in-0")
        // and an output channel ("orderToShipping-out-0"), configured entirely in application.yml
        @Bean
        public Function<OrderPlacedEvent, ShippingRequestedEvent> orderToShipping() {
            return event -> {
                System.out.println("Processing order " + event.orderId() + " for item " + event.item());
                return new ShippingRequestedEvent(event.orderId(), "ship");
            };
        }
    }

    // application.yml (Kafka binder):
    //   spring.cloud.function.definition: orderToShipping
    //   spring.cloud.stream.bindings.orderToShipping-in-0.destination: order-placed-events
    //   spring.cloud.stream.bindings.orderToShipping-out-0.destination: shipping-requested-events
    //   spring.cloud.stream.kafka.binder.brokers: localhost:9092
    //
    // To switch to RabbitMQ: swap spring-cloud-stream-binder-kafka for
    // spring-cloud-stream-binder-rabbit, and replace the kafka.binder.* properties
    // with rabbit.binder.* -- the orderToShipping() FUNCTION above never changes.
}
```

How to run: requires `spring-cloud-stream` plus a binder dependency (`spring-cloud-stream-binder-kafka` or `spring-cloud-stream-binder-rabbit`), with `spring.cloud.function.definition` and the corresponding `spring.cloud.stream.bindings.*` properties configured; run in a Spring Boot application, publish an `OrderPlacedEvent`-shaped message to the configured input destination (a Kafka topic or RabbitMQ queue depending on the binder), and observe a corresponding `ShippingRequestedEvent`-shaped message published to the configured output destination.

`orderToShipping()` is a plain `Function<OrderPlacedEvent, ShippingRequestedEvent>` bean — nothing in it references Kafka, RabbitMQ, topics, or queues at all. Spring Cloud Stream inspects the function's name and type at startup, automatically creates the corresponding input/output bindings, and wires them to whatever binder and destination names are specified in `application.yml` — switching the entire underlying broker is purely a dependency and property-file change, with zero modification to this function.

## 6. Walkthrough

Trace what happens when a message representing `{"orderId": "42", "item": "widget"}` is published to the `order-placed-events` Kafka topic, assuming the Level 3 configuration is active:

1. **Spring Cloud Stream's Kafka binder, subscribed to the `order-placed-events` topic on behalf of the `orderToShipping-in-0` binding, receives the raw message.**
2. **The binder deserializes the raw message bytes into an `OrderPlacedEvent` object** (`orderId="42"`, `item="widget"`), using Spring's message conversion machinery configured for this binding — this deserialization logic lives entirely in the framework's binder layer, not in the `orderToShipping` function itself.
3. **The binder invokes `orderToShipping.apply(event)`** with the deserialized `OrderPlacedEvent`. Inside the function, the business logic runs: it logs the processing message and constructs a `ShippingRequestedEvent("42", "ship")` as the return value.
4. **The binder receives this returned `ShippingRequestedEvent` object** and serializes it (again, entirely within the framework's binder layer) into a message payload appropriate for the output binding's configured broker format.
5. **The binder publishes the serialized message to the `shipping-requested-events` topic** (as configured via `spring.cloud.stream.bindings.orderToShipping-out-0.destination`), completing the round-trip: one incoming Kafka message triggered the function, whose return value became one outgoing Kafka message on a different topic.

If this same application were reconfigured to use the RabbitMQ binder instead (swapping the Maven/Gradle dependency and the binder-specific properties in `application.yml`), the exact same five steps would occur, with steps 1, 2, 4, and 5 instead involving RabbitMQ queues and AMQP message formats rather than Kafka topics — step 3, the actual business logic inside `orderToShipping`, would be entirely unaffected, since it never referenced either broker directly.

## 7. Gotchas & takeaways

> **Gotcha:** Kafka and RabbitMQ have meaningfully different delivery and ordering semantics (Kafka's partition-based ordering and consumer group rebalancing versus RabbitMQ's queue-based delivery and acknowledgment model) — while Spring Cloud Stream's functional programming model decouples your *code* from either broker's API, it cannot fully abstract away every semantic difference between them; a function relying on strict message ordering within a partition (a Kafka-specific guarantee) may behave subtly differently if the underlying binder is later swapped to RabbitMQ, so broker-swapping still warrants careful review of any implicit ordering or delivery assumptions your function relies on.

- Spring Cloud Stream lets business logic be expressed as plain functions (`Function`, `Supplier`, `Consumer`), fully decoupled from any specific broker's client API.
- The binder abstraction (Kafka, RabbitMQ) is a swappable dependency and configuration detail — the functions themselves never reference broker-specific concepts directly.
- Input/output channel names, topic/queue names, and broker connection details all live in configuration (`application.yml`), keyed by function name, not in the function's own code.
- Broker-swapping is easier at the code level than at the semantics level — review any implicit ordering, delivery guarantee, or partitioning assumptions your function relies on before assuming a broker swap is entirely risk-free.
