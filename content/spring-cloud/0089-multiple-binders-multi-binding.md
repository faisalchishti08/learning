---
card: spring-cloud
gi: 89
slug: multiple-binders-multi-binding
title: "Multiple binders & multi-binding"
---

## 1. What it is

A single application can use more than one binder simultaneously — say, Kafka for high-throughput internal event streams and RabbitMQ for a specific integration with a legacy system that only speaks RabbitMQ — configured through named binder instances under `spring.cloud.stream.binders.*`, with each individual binding explicitly assigned to the binder it should use.

```properties
spring.cloud.stream.binders.kafka-binder.type=kafka
spring.cloud.stream.binders.rabbit-binder.type=rabbit

spring.cloud.stream.bindings.handleOrder-in-0.binder=kafka-binder
spring.cloud.stream.bindings.handleOrder-in-0.destination=order-placed-events

spring.cloud.stream.bindings.legacyExport-out-0.binder=rabbit-binder
spring.cloud.stream.bindings.legacyExport-out-0.destination=legacy-export-queue
```

## 2. Why & when

The earlier binder abstraction card covered swapping *the entire application's* broker choice; multi-binding covers the more nuanced case of one application genuinely needing *different* brokers for *different* bindings simultaneously — not a migration in progress, but a deliberate, permanent architecture where different integrations have different broker requirements.

Reach for multiple binders when:

- A service needs to consume from or publish to two genuinely different messaging systems at once — a high-throughput internal Kafka-based event stream, plus a specific integration point with a partner or legacy system that only supports RabbitMQ (or vice versa).
- Different bindings within the same application have meaningfully different requirements — Kafka's strength in high-throughput, partitioned, replayable streams for internal events, versus RabbitMQ's routing flexibility for a more complex, rule-based integration with an external system.
- A gradual migration from one broker to another is underway, and some bindings have already moved to the new broker while others temporarily remain on the old one — multi-binding lets both coexist cleanly during the transition period.

## 3. Core concept

```
 spring.cloud.stream.binders.kafka-binder.type=kafka     <- named binder instance #1
 spring.cloud.stream.binders.rabbit-binder.type=rabbit    <- named binder instance #2

 EACH individual binding explicitly names which binder instance it uses:
   handleOrder-in-0.binder=kafka-binder     -> this binding uses Kafka
   legacyExport-out-0.binder=rabbit-binder  -> this binding uses RabbitMQ

 within ONE application, ONE service, ONE deployed process
```

Binder selection happens per-binding, not application-wide — different functions in the same application can transparently use entirely different messaging technologies.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One application has two functions, one bound to a Kafka binder for high throughput internal events and another bound to a RabbitMQ binder for a legacy integration, both coexisting in the same deployed process">
  <rect x="20" y="20" width="600" height="160" rx="10" fill="#1c243020" stroke="#8b949e" stroke-width="1.3" stroke-dasharray="4,3"/>
  <text x="320" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ONE application (one deployed process)</text>

  <rect x="60" y="65" width="220" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="170" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">handleOrder</text>
  <text x="170" y="103" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">binder: kafka-binder</text>

  <rect x="360" y="65" width="220" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="470" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">legacyExport</text>
  <text x="470" y="103" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">binder: rabbit-binder</text>

  <line x1="170" y1="115" x2="170" y2="150" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a89)"/>
  <line x1="470" y1="115" x2="470" y2="150" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a89)"/>

  <rect x="60" y="155" width="220" height="20" rx="4" fill="#6db33f30" stroke="#6db33f" stroke-width="1"/>
  <text x="170" y="169" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Kafka broker</text>

  <rect x="360" y="155" width="220" height="20" rx="4" fill="#e6494930" stroke="#e64949" stroke-width="1"/>
  <text x="470" y="169" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">RabbitMQ broker</text>

  <defs><marker id="a89" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two functions in the same application, each independently connected to a genuinely different broker technology, coexisting cleanly.

## 5. Runnable example

The scenario: one `billing-service` process that consumes internal order events from Kafka and separately publishes a legacy export feed to RabbitMQ. Start with a single-binder model (the limitation), then add named binder selection per binding, then run both bindings independently within one application.

### Level 1 — Basic

Single-binder model — every binding forced onto the same broker, even when that doesn't actually fit.

```java
public class MultiBinderLevel1 {
    record OrderPlaced(String orderId, double amount) {}
    record LegacyExportRecord(String orderId, double amount) {}

    // both bindings forced through the SAME broker, even though the legacy system only speaks RabbitMQ
    static void publishToSingleBroker(String destination, Object payload) {
        System.out.println("[single broker] publishing to '" + destination + "': " + payload);
    }

    public static void main(String[] args) {
        publishToSingleBroker("order-placed-events", new OrderPlaced("42", 199.99));
        publishToSingleBroker("legacy-export-queue", new LegacyExportRecord("42", 199.99));
        // if the legacy system genuinely only supports RabbitMQ, and this "single broker" is Kafka,
        // this second publish call would simply never reach it
    }
}
```

How to run: `java MultiBinderLevel1.java`

Both destinations are published through the same, single broker abstraction — if the legacy system genuinely only integrates via RabbitMQ and this application's sole binder is Kafka, the second call is fundamentally unable to reach its intended destination, no matter how it's configured.

### Level 2 — Intermediate

Add named binder selection per binding, modeling how each binding explicitly declares which concrete binder it uses.

```java
import java.util.*;

public class MultiBinderLevel2 {
    record OrderPlaced(String orderId, double amount) {}
    record LegacyExportRecord(String orderId, double amount) {}

    interface Binder { void publish(String destination, Object payload); }

    static class KafkaBinder implements Binder {
        public void publish(String destination, Object payload) {
            System.out.println("[kafka-binder] producer.send(\"" + destination + "\", " + payload + ")");
        }
    }
    static class RabbitBinder implements Binder {
        public void publish(String destination, Object payload) {
            System.out.println("[rabbit-binder] channel.basicPublish(\"" + destination + "-exchange\", ..., " + payload + ")");
        }
    }

    // each binding maps EXPLICITLY to a named binder instance
    static Map<String, Binder> binders = Map.of(
            "kafka-binder", new KafkaBinder(),
            "rabbit-binder", new RabbitBinder()
    );

    static void publish(String bindingName, String binderName, String destination, Object payload) {
        binders.get(binderName).publish(destination, payload);
    }

    public static void main(String[] args) {
        publish("handleOrder-out-0", "kafka-binder", "order-placed-events", new OrderPlaced("42", 199.99));
        publish("legacyExport-out-0", "rabbit-binder", "legacy-export-queue", new LegacyExportRecord("42", 199.99));
    }
}
```

How to run: `java MultiBinderLevel2.java`

Each `publish` call explicitly names both its binding and which concrete `binderName` it uses — `handleOrder-out-0` correctly routes through `KafkaBinder`, while `legacyExport-out-0` correctly routes through `RabbitBinder`, genuinely reaching two different broker technologies from within the same application, exactly matching two `spring.cloud.stream.bindings.*.binder` properties pointing at two different `spring.cloud.stream.binders.*` configurations.

### Level 3 — Advanced

Run both bindings as part of one coherent application flow — an order event triggers both an internal Kafka publish and a RabbitMQ-based legacy export, confirming both genuinely independent code paths work correctly together within a single process.

```java
import java.util.*;
import java.util.function.Function;

public class MultiBinderLevel3 {
    record OrderPlaced(String orderId, double amount) {}
    record InvoiceRequested(String orderId, double amount) {}
    record LegacyExportRecord(String orderId, double amount, String format) {}

    interface Binder { void publish(String destination, Object payload); }

    static class KafkaBinder implements Binder {
        List<String> published = new ArrayList<>();
        public void publish(String destination, Object payload) {
            published.add(destination + ": " + payload);
            System.out.println("[kafka-binder] " + destination + " <- " + payload);
        }
    }
    static class RabbitBinder implements Binder {
        List<String> published = new ArrayList<>();
        public void publish(String destination, Object payload) {
            published.add(destination + ": " + payload);
            System.out.println("[rabbit-binder] " + destination + " <- " + payload);
        }
    }

    static KafkaBinder kafkaBinder = new KafkaBinder();
    static RabbitBinder rabbitBinder = new RabbitBinder();

    // handleOrder is bound to kafka-binder -- internal, high-throughput event
    static Function<OrderPlaced, InvoiceRequested> handleOrder =
            order -> new InvoiceRequested(order.orderId(), order.amount());

    // exportToLegacy is bound to rabbit-binder -- separate integration, different broker entirely
    static Function<OrderPlaced, LegacyExportRecord> exportToLegacy =
            order -> new LegacyExportRecord(order.orderId(), order.amount(), "LEGACY_XML_V1");

    public static void main(String[] args) {
        OrderPlaced incoming = new OrderPlaced("42", 199.99);

        // both functions process the SAME source event, but publish through TWO DIFFERENT binders
        InvoiceRequested invoiceEvent = handleOrder.apply(incoming);
        kafkaBinder.publish("invoice-requested-events", invoiceEvent);

        LegacyExportRecord exportRecord = exportToLegacy.apply(incoming);
        rabbitBinder.publish("legacy-export-queue", exportRecord);

        System.out.println("kafka-binder published: " + kafkaBinder.published.size() + " message(s)");
        System.out.println("rabbit-binder published: " + rabbitBinder.published.size() + " message(s)");
    }
}
```

How to run: `java MultiBinderLevel3.java`

`handleOrder` and `exportToLegacy` both process the same `incoming` order, but their outputs are published through two entirely separate, independently-tracked `Binder` instances — `kafkaBinder` receives the internal `InvoiceRequested` event, and `rabbitBinder` receives the legacy-formatted export record. Both binders' `published` lists confirm exactly one message each, demonstrating that one application, one incoming event, and two entirely different downstream messaging integrations can coexist cleanly, each function bound to the broker technology that actually fits its specific purpose.

## 6. Walkthrough

Trace the flow in Level 3.

1. `incoming`, a single `OrderPlaced` event, is created once — this models one real order event arriving at this service, perhaps itself consumed from yet another binding.
2. `handleOrder.apply(incoming)` runs, producing `InvoiceRequested("42", 199.99)` — this is the same kind of internal event transformation covered in earlier cards, intended for high-throughput internal consumption.
3. `kafkaBinder.publish("invoice-requested-events", invoiceEvent)` runs — this models `handleOrder`'s output binding being configured with `binder=kafka-binder`, so Spring Cloud Stream routes this specific publish through the Kafka binder instance, adding an entry to `kafkaBinder.published`.
4. `exportToLegacy.apply(incoming)` runs next, on the *same* `incoming` order — producing `LegacyExportRecord("42", 199.99, "LEGACY_XML_V1")`, a differently-shaped record intended specifically for the legacy integration.
5. `rabbitBinder.publish("legacy-export-queue", exportRecord)` runs — this models `exportToLegacy`'s output binding being configured with `binder=rabbit-binder`, routing this publish through the entirely separate RabbitMQ binder instance, adding an entry to `rabbitBinder.published`.
6. The final two `println` calls confirm each binder handled exactly one message, and inspecting the earlier console output shows genuinely different destination strings and payload shapes flowing through each — proof that both integrations ran correctly and independently within this single execution, triggered by one shared source event.

```
incoming: OrderPlaced("42", 199.99)
    |
    +--> handleOrder()      --> InvoiceRequested   --> kafkaBinder.publish("invoice-requested-events", ...)
    |
    +--> exportToLegacy()   --> LegacyExportRecord  --> rabbitBinder.publish("legacy-export-queue", ...)

ONE source event, TWO independent downstream integrations, TWO different broker technologies
```

## 7. Gotchas & takeaways

> **Gotcha:** each named binder instance typically needs its own separate connection configuration (`spring.cloud.stream.kafka.binder.brokers`, `spring.cloud.stream.rabbit.binder.host`, and so on) — forgetting to fully configure connection details for a *second* binder (easy to do when copy-pasting from a single-binder setup) produces connection failures specifically for the bindings using that binder, while the first binder's bindings continue working normally, which can make the root cause non-obvious at first glance.

- Multi-binding is a deliberate architectural choice for genuinely needing different broker technologies simultaneously — a migration in progress, differing requirements per integration, or a specific legacy integration constraint — not a default or common setup for most applications.
- Binder selection happens per-binding (`spring.cloud.stream.bindings.<binding>.binder=<binder-name>`), so different functions in the same application can transparently target completely different messaging technologies with no interaction or interference between them.
- Each named binder instance requires its own complete, correctly-configured connection details — treat each one as an independent broker connection to configure and monitor, not an extension of the first.
- This capability builds directly on the binder abstraction from the earlier card — multi-binding is really just "use the abstraction's swappability more than once, simultaneously, within one application," rather than a fundamentally different mechanism.
