---
card: microservices
gi: 147
slug: spring-cloud-stream-kafka-rabbitmq-pulsar-binders
title: "Spring Cloud Stream Kafka / RabbitMQ / Pulsar binders"
---

## 1. What it is

The Kafka, RabbitMQ, and Pulsar binders are the concrete implementations of Spring Cloud Stream's [binder abstraction](0145-spring-cloud-stream-binder-abstraction.md) — `spring-cloud-stream-binder-kafka`, `spring-cloud-stream-binder-rabbit`, and `spring-cloud-stream-binder-pulsar` are separate artifacts, each translating the generic binding contract into that specific broker's real client API, connection handling, and broker-specific configuration properties.

## 2. Why & when

The binder abstraction only delivers on its promise of broker-agnostic application code if a real binder implementation exists to plug in underneath it — these three artifacts are what make "switch the broker via configuration" an actual, working capability rather than a theoretical one. Each binder also exposes broker-specific configuration extensions (`spring.cloud.stream.kafka.bindings.*`, `spring.cloud.stream.rabbit.bindings.*`, `spring.cloud.stream.pulsar.bindings.*`) for tuning behavior that only makes sense for that particular broker — Kafka's partition count and replication factor, RabbitMQ's exchange type and routing keys, Pulsar's subscription type.

Choose the Kafka binder for high-throughput event streaming with strong ordering-within-partition and [replayability](0136-replayability-of-event-streams.md) needs. Choose the RabbitMQ binder for classic queue-based messaging with sophisticated routing (topic exchanges, header-based routing) and lower operational complexity for moderate throughput. Choose the Pulsar binder when multi-tenancy, tiered storage, or Pulsar's unified queue-and-streaming model specifically fit the workload. Only one binder is normally active per binding in a given deployment, selected via configuration and the binder dependency present on the classpath.

## 3. Core concept

The same generic `Function`/`Supplier`/`Consumer` bean is bound to a destination; only the binder-specific configuration block, and which binder starter dependency is on the classpath, determines which broker actually carries the traffic — the business logic bean itself is unaware of and unaffected by this choice.

```java
@Bean
public Function<OrderPlaced, ShippingRequested> orderToShippingRequest() {
    return order -> new ShippingRequested(order.orderId(), order.address()); // IDENTICAL across all three binders
}
```
```yaml
# application.yml -- ONLY this changes between Kafka, RabbitMQ, and Pulsar deployments
spring.cloud.stream.kafka.bindings.orderToShippingRequest-in-0.consumer.autoCommitOffset: false
# spring.cloud.stream.rabbit.bindings.orderToShippingRequest-in-0.consumer.exchangeType: topic
# spring.cloud.stream.pulsar.bindings.orderToShippingRequest-in-0.consumer.subscriptionType: Shared
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One identical Function bean is bound, via configuration alone, to three different concrete binder implementations -- Kafka, RabbitMQ, or Pulsar -- each with its own broker-specific configuration extension" >
  <rect x="230" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="48" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Function bean (identical)</text>

  <rect x="20" y="110" width="170" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="134" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Kafka binder</text>
  <rect x="235" y="110" width="170" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="134" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">RabbitMQ binder</text>
  <rect x="450" y="110" width="170" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="134" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Pulsar binder</text>

  <line x1="280" y1="65" x2="120" y2="108" stroke="#8b949e" stroke-dasharray="2,2" marker-end="url(#arr28)"/>
  <line x1="320" y1="65" x2="320" y2="108" stroke="#8b949e" marker-end="url(#arr28)"/>
  <line x1="360" y1="65" x2="520" y2="108" stroke="#8b949e" stroke-dasharray="2,2" marker-end="url(#arr28)"/>
  <text x="320" y="175" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">only ONE active per deployment, selected by config + classpath</text>

  <defs>
    <marker id="arr28" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The same bean can be wired to any of the three binders; broker-specific tuning lives entirely in configuration, not code.

## 5. Runnable example

Scenario: an order-transformation service modeled first with a single hard-coded binder (no flexibility), then refactored to select among three concrete binder implementations at startup based on configuration, and finally extended to show each binder applying its own broker-specific configuration extension (partition count for Kafka, exchange type for RabbitMQ) without touching the shared business logic.

### Level 1 — Basic

```java
// File: SingleHardCodedBinder.java -- only ONE binder implementation exists; no
// real choice, standing in for what a project looks like before adopting the abstraction fully.
import java.util.function.*;

public class SingleHardCodedBinder {
    record OrderPlaced(int orderId, String address) {}
    record ShippingRequested(int orderId, String address) {}

    static class KafkaOnlyBinder {
        void bindAndRun(Function<OrderPlaced, ShippingRequested> fn, OrderPlaced input) {
            System.out.println("[Kafka-only binder] " + fn.apply(input));
        }
    }

    public static void main(String[] args) {
        Function<OrderPlaced, ShippingRequested> transform = order -> new ShippingRequested(order.orderId(), order.address());
        new KafkaOnlyBinder().bindAndRun(transform, new OrderPlaced(42, "123 Main St"));
        System.out.println("Only Kafka is even an option here -- switching brokers means writing a NEW binder class.");
    }
}
```

**How to run:** `javac SingleHardCodedBinder.java && java SingleHardCodedBinder` (JDK 17+).

### Level 2 — Intermediate

```java
// File: SelectableBinderImplementations.java -- THREE real binder implementations
// exist; ONE is selected at startup, purely by configuration, for the SAME function bean.
import java.util.function.*;

public class SelectableBinderImplementations {
    record OrderPlaced(int orderId, String address) {}
    record ShippingRequested(int orderId, String address) {}

    interface StreamBinder {
        void bindAndRun(Function<OrderPlaced, ShippingRequested> fn, OrderPlaced input);
    }
    static class KafkaBinder implements StreamBinder {
        public void bindAndRun(Function<OrderPlaced, ShippingRequested> fn, OrderPlaced input) {
            System.out.println("[Kafka binder] " + fn.apply(input));
        }
    }
    static class RabbitBinder implements StreamBinder {
        public void bindAndRun(Function<OrderPlaced, ShippingRequested> fn, OrderPlaced input) {
            System.out.println("[RabbitMQ binder] " + fn.apply(input));
        }
    }
    static class PulsarBinder implements StreamBinder {
        public void bindAndRun(Function<OrderPlaced, ShippingRequested> fn, OrderPlaced input) {
            System.out.println("[Pulsar binder] " + fn.apply(input));
        }
    }

    static StreamBinder selectBinder(String configuredBinderType) {
        return switch (configuredBinderType) { // simulates reading spring.cloud.stream.default-binder / classpath choice
            case "kafka" -> new KafkaBinder();
            case "rabbit" -> new RabbitBinder();
            case "pulsar" -> new PulsarBinder();
            default -> throw new IllegalArgumentException("unknown binder: " + configuredBinderType);
        };
    }

    public static void main(String[] args) {
        Function<OrderPlaced, ShippingRequested> transform = order -> new ShippingRequested(order.orderId(), order.address());
        OrderPlaced sampleOrder = new OrderPlaced(42, "123 Main St");

        for (String binderType : new String[]{"kafka", "rabbit", "pulsar"}) {
            selectBinder(binderType).bindAndRun(transform, sampleOrder); // SAME transform bean, three different binders
        }
        System.out.println("The transform function's source code was used, unmodified, by all three binders.");
    }
}
```

**How to run:** `javac SelectableBinderImplementations.java && java SelectableBinderImplementations` (JDK 17+).

Expected output:
```
[Kafka binder] ShippingRequested[orderId=42, address=123 Main St]
[RabbitMQ binder] ShippingRequested[orderId=42, address=123 Main St]
[Pulsar binder] ShippingRequested[orderId=42, address=123 Main St]
The transform function's source code was used, unmodified, by all three binders.
```

### Level 3 — Advanced

```java
// File: BrokerSpecificExtensionConfig.java -- each binder ALSO applies its own
// broker-specific configuration extension, distinct from the shared binding config.
import java.util.*;
import java.util.function.*;

public class BrokerSpecificExtensionConfig {
    record OrderPlaced(int orderId, String address) {}
    record ShippingRequested(int orderId, String address) {}
    record KafkaExtension(int partitionCount, boolean autoCommitOffset) {}
    record RabbitExtension(String exchangeType, String routingKey) {}
    record PulsarExtension(String subscriptionType) {}

    interface StreamBinder { void bindAndRun(Function<OrderPlaced, ShippingRequested> fn, OrderPlaced input); }

    static class KafkaBinder implements StreamBinder {
        KafkaExtension extension;
        KafkaBinder(KafkaExtension extension) { this.extension = extension; }
        public void bindAndRun(Function<OrderPlaced, ShippingRequested> fn, OrderPlaced input) {
            System.out.println("[Kafka binder, partitions=" + extension.partitionCount() + ", autoCommit=" + extension.autoCommitOffset() + "] " + fn.apply(input));
        }
    }
    static class RabbitBinder implements StreamBinder {
        RabbitExtension extension;
        RabbitBinder(RabbitExtension extension) { this.extension = extension; }
        public void bindAndRun(Function<OrderPlaced, ShippingRequested> fn, OrderPlaced input) {
            System.out.println("[RabbitMQ binder, exchangeType=" + extension.exchangeType() + ", routingKey=" + extension.routingKey() + "] " + fn.apply(input));
        }
    }
    static class PulsarBinder implements StreamBinder {
        PulsarExtension extension;
        PulsarBinder(PulsarExtension extension) { this.extension = extension; }
        public void bindAndRun(Function<OrderPlaced, ShippingRequested> fn, OrderPlaced input) {
            System.out.println("[Pulsar binder, subscriptionType=" + extension.subscriptionType() + "] " + fn.apply(input));
        }
    }

    public static void main(String[] args) {
        Function<OrderPlaced, ShippingRequested> transform = order -> new ShippingRequested(order.orderId(), order.address());
        OrderPlaced sampleOrder = new OrderPlaced(42, "123 Main St");

        List<StreamBinder> configuredBinders = List.of(
            new KafkaBinder(new KafkaExtension(6, false)),          // Kafka-SPECIFIC config
            new RabbitBinder(new RabbitExtension("topic", "orders.#")), // RabbitMQ-SPECIFIC config
            new PulsarBinder(new PulsarExtension("Shared")));           // Pulsar-SPECIFIC config

        for (StreamBinder binder : configuredBinders) {
            binder.bindAndRun(transform, sampleOrder); // the SAME transform, each binder applying ITS OWN extension config
        }
        System.out.println("Broker-specific tuning lives entirely in each binder's own extension -- 'transform' never sees any of it.");
    }
}
```

**How to run:** `javac BrokerSpecificExtensionConfig.java && java BrokerSpecificExtensionConfig` (JDK 17+).

Expected output:
```
[Kafka binder, partitions=6, autoCommit=false] ShippingRequested[orderId=42, address=123 Main St]
[RabbitMQ binder, exchangeType=topic, routingKey=orders.#] ShippingRequested[orderId=42, address=123 Main St]
[Pulsar binder, subscriptionType=Shared] ShippingRequested[orderId=42, address=123 Main St]
Broker-specific tuning lives entirely in each binder's own extension -- 'transform' never sees any of it.
```

## 6. Walkthrough

1. **Level 1** — `KafkaOnlyBinder` is the sole implementation available; there is no interface separating "the concept of a binder" from "this specific Kafka implementation," so any future need for RabbitMQ or Pulsar would require writing an entirely new, separate integration path.
2. **Level 2, three implementations of one interface** — `KafkaBinder`, `RabbitBinder`, and `PulsarBinder` all implement `StreamBinder`; `selectBinder` chooses among them based on a string that stands in for real configuration (`spring.cloud.stream.default-binder` and which binder starter is on the classpath).
3. **Level 2, one function, three binders** — the loop in `main` calls `selectBinder(binderType).bindAndRun(transform, sampleOrder)` for each of the three type strings, passing the *identical* `transform` function object each time — proving that the business logic requires no modification to work with any of the three.
4. **Level 3, extension configuration per binder** — `KafkaExtension`, `RabbitExtension`, and `PulsarExtension` each model the kind of broker-specific tuning knobs that only make sense for that particular broker (partition count for Kafka, exchange type for RabbitMQ, subscription type for Pulsar) — none of these concepts translate meaningfully to the other two brokers.
5. **Level 3, each binder carrying its own config** — `KafkaBinder`, `RabbitBinder`, and `PulsarBinder` are now constructed with their respective extension objects, and each `bindAndRun` implementation prints its own broker-specific settings alongside the shared transformation result.
6. **Level 3, the shared function stays untouched** — across all three constructions in `configuredBinders`, `transform` is passed as-is; nothing about `KafkaExtension`'s `partitionCount` or `RabbitExtension`'s `exchangeType` is visible to, or needed by, the transformation logic itself.
7. **Level 3, the practical takeaway made concrete** — this mirrors exactly how real Spring Cloud Stream configuration separates the broker-agnostic `spring.cloud.stream.bindings.*` properties (destination names, content type) from broker-specific `spring.cloud.stream.kafka.bindings.*` / `.rabbit.bindings.*` / `.pulsar.bindings.*` extensions — the function bean's Java code only ever needs to change if the *business logic* changes, never when broker-specific tuning changes.

## 7. Gotchas & takeaways

> **Gotcha:** a binder-specific extension property configured for the wrong binder (a `spring.cloud.stream.kafka.bindings.*` property present while only the RabbitMQ binder is on the classpath) is typically just silently ignored rather than causing a startup error — double-check which binder is actually active in each environment rather than assuming a broker-specific setting is taking effect just because it's present in configuration.

- The Kafka, RabbitMQ, and Pulsar binders are separate, concrete implementations of Spring Cloud Stream's binder abstraction, each translating the generic binding contract into that broker's actual client API.
- Each binder exposes its own configuration extension for tuning behavior specific to that broker, kept separate from the shared, broker-agnostic binding configuration.
- The choice of binder — driven by which starter dependency is on the classpath and configuration like `spring.cloud.stream.default-binder` — determines which broker actually carries traffic for a given function bean, without that bean's code changing at all.
- Kafka suits high-throughput streaming with strong per-partition ordering and replay; RabbitMQ suits classic queue-based routing at moderate throughput; Pulsar suits multi-tenant and tiered-storage requirements.
- Only one binder is normally active per binding in a deployment; broker-specific configuration for an inactive binder is generally just ignored rather than flagged as an error.
