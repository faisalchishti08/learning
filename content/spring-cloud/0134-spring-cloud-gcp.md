---
card: spring-cloud
gi: 134
slug: spring-cloud-gcp
title: "Spring Cloud GCP"
---

## 1. What it is

Spring Cloud GCP integrates Google Cloud Platform services into Spring's familiar abstractions, completing the same three-way pattern established by Spring Cloud AWS and Spring Cloud Azure — Google Cloud Storage through Spring's `Resource` abstraction, Pub/Sub as a Spring Cloud Stream binder or `@PubSubListener`-style consumer, and GCP Secret Manager / Runtime Configurator as externalized configuration `PropertySource`s consumed via ordinary `@Value`/`@ConfigurationProperties`, alongside dedicated support for Cloud SQL, Firestore, and BigQuery through equally Spring-idiomatic interfaces.

```java
@Value("gs://my-bucket/config/settings.json")
Resource gcsResource; // a Google Cloud Storage object, via Spring's ORDINARY Resource abstraction

@PubSubListener(subscription = "order-queue-sub")
void handleOrderMessage(OrderEvent event) { ... } // Pub/Sub consumption, Spring Messaging-style
```

```properties
spring.config.import=sm://order-service/rate-limit
# GCP Secret Manager values become ordinary @Value-bound properties, exactly like AWS Parameter Store or Azure App Configuration
```

## 2. Why & when

The same underlying problem Spring Cloud AWS and Spring Cloud Azure solve for their respective clouds applies identically to GCP: an application needing Cloud Storage access, Pub/Sub messaging, and Secret Manager-sourced configuration would otherwise require coding directly against the Google Cloud client libraries, each with their own client setup and API shape unrelated to Spring's existing abstractions. Spring Cloud GCP applies the exact same "wrap the cloud-specific service behind a familiar Spring abstraction" pattern a third time — at this point, a team that has seen this pattern applied to any one of the three major clouds already understands the shape it takes for the others, since the underlying abstraction (`Resource`, a listener annotation, `PropertySource`) is what stays constant, only the specific cloud service and starter dependency changes.

Reach for Spring Cloud GCP when:

- Deploying a Spring Boot application onto GCP and needing Cloud Storage, Pub/Sub, or Secret Manager/Runtime Configurator integration through Spring-idiomatic code rather than the raw Google Cloud client libraries.
- Working with GCP-specific managed services with dedicated Spring Cloud GCP support beyond the storage/messaging/config trio — Cloud SQL (simplified connection setup via Cloud SQL Socket Factory integration), Firestore (Spring Data-style repositories), and BigQuery (a Spring-idiomatic client wrapper) all have their own dedicated integrations worth knowing about for GCP-specific workloads.
- Building or maintaining a genuinely multi-cloud Spring codebase — having internalized the shared abstraction pattern across AWS, Azure, and GCP (`Resource` for object storage, a listener annotation for pub/sub-style messaging, `PropertySource` for externalized config/secrets) makes reasoning about equivalent functionality across all three straightforward, rather than needing to relearn each cloud's approach from scratch.

## 3. Core concept

```
 GCP service                     Spring abstraction              (same pattern as AWS and Azure)
   Cloud Storage             ->  Resource                          (S3 / Blob Storage -> Resource)
   Pub/Sub                   ->  @PubSubListener / binder          (SQS / Service Bus -> listener annotation)
   Secret Manager / Runtime Configurator -> PropertySource         (Parameter Store / App Config -> PropertySource)
   Cloud SQL, Firestore, BigQuery -> dedicated Spring-idiomatic integrations (GCP-specific, no direct AWS/Azure parallel)

 THIRD cloud, SAME wrapping pattern -- application code depends on the Spring abstraction,
 the specific cloud provider becomes a STARTER DEPENDENCY choice, not an application-code choice
```

By the third cloud provider following this identical pattern, the pattern itself — not any individual cloud's specifics — is what's actually worth internalizing as the transferable skill.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cloud Storage Pub Sub and Secret Manager are wrapped behind the same Resource listener annotation and PropertySource abstractions completing the identical pattern already seen for AWS and Azure across all three major cloud providers">
  <rect x="20" y="20" width="170" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="105" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Cloud Storage</text>
  <rect x="20" y="75" width="170" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="105" y="99" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Pub/Sub</text>
  <rect x="20" y="130" width="170" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="105" y="154" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Secret Manager</text>

  <rect x="270" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="345" y="44" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Resource</text>
  <rect x="270" y="75" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="345" y="99" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">@PubSubListener</text>
  <rect x="270" y="130" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="345" y="154" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">PropertySource</text>

  <rect x="490" y="75" width="130" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="555" y="99" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">application code</text>

  <defs><marker id="a134" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="190" y1="40" x2="270" y2="40" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a134)"/>
  <line x1="190" y1="95" x2="270" y2="95" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a134)"/>
  <line x1="190" y1="150" x2="270" y2="150" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a134)"/>
  <line x1="420" y1="95" x2="490" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a134)"/>
</svg>

The third repetition of the identical structure seen in the AWS and Azure cards — by this point, the pattern itself is the takeaway.

## 5. Runnable example

The scenario: the same configuration-plus-messaging pattern once more, this time for GCP Secret Manager and Pub/Sub, with an explicit generalization step showing all three clouds' examples can be driven by one shared, cloud-agnostic core function. Start with Secret-Manager-backed property resolution, then add Pub/Sub-style listening, then generalize into one function usable regardless of which cloud's naming is used, proving the actual application logic never needed to differ across any of the three cards.

### Level 1 — Basic

Secret Manager values resolved as ordinary configuration properties.

```java
import java.util.*;

public class SpringCloudGcpLevel1 {
    static Map<String, String> secretManager = Map.of("order-service.rate-limit", "100/min");

    static String resolveProperty(String key) {
        return secretManager.get(key);
    }

    public static void main(String[] args) {
        String rateLimit = resolveProperty("order-service.rate-limit");
        System.out.println("rate-limit (from Secret Manager): " + rateLimit);
    }
}
```

How to run: `java SpringCloudGcpLevel1.java`

Once again structurally identical to both the AWS and Azure cards' equivalent examples — the pattern has now been demonstrated three times, across three cloud providers' terminology, with no change to the actual calling code shape.

### Level 2 — Intermediate

Add Pub/Sub-style message listening through the same Spring-Messaging-idiomatic interface shape.

```java
import java.util.*;
import java.util.function.Consumer;

public class SpringCloudGcpLevel2 {
    record OrderEvent(int orderId, String status) {}

    static class PubSubListenerRegistry {
        Map<String, List<Consumer<OrderEvent>>> listenersBySubscription = new HashMap<>();
        void registerListener(String subscriptionName, Consumer<OrderEvent> handler) {
            listenersBySubscription.computeIfAbsent(subscriptionName, k -> new ArrayList<>()).add(handler);
        }
        void simulateIncomingMessage(String subscriptionName, OrderEvent event) {
            for (Consumer<OrderEvent> handler : listenersBySubscription.getOrDefault(subscriptionName, List.of())) handler.accept(event);
        }
    }

    public static void main(String[] args) {
        PubSubListenerRegistry pubSub = new PubSubListenerRegistry();

        pubSub.registerListener("order-queue-sub", event ->
                System.out.println("handling order event: id=" + event.orderId() + " status=" + event.status()));

        pubSub.simulateIncomingMessage("order-queue-sub", new OrderEvent(42, "CONFIRMED"));
    }
}
```

How to run: `java SpringCloudGcpLevel2.java`

`pubSub.registerListener` mirrors both `@SqsListener` and `@ServiceBusListener`'s registration style exactly — three cloud providers, three sets of terminology, one identical Spring Messaging-idiomatic calling pattern underneath.

### Level 3 — Advanced

Generalize the combined configuration-plus-messaging logic into one genuinely cloud-agnostic function, taking a resolved property value and a listener registry as parameters — proving the actual application-level business logic was never coupled to any specific cloud's naming or SDK in the first place.

```java
import java.util.*;
import java.util.function.Consumer;
import java.util.function.Function;

public class SpringCloudGcpLevel3 {
    record OrderEvent(int orderId, String status) {}

    interface ListenerRegistry {
        void registerListener(String destination, Consumer<OrderEvent> handler);
        void simulateIncomingMessage(String destination, OrderEvent event);
    }

    static class PubSubListenerRegistry implements ListenerRegistry {
        Map<String, List<Consumer<OrderEvent>>> listeners = new HashMap<>();
        public void registerListener(String destination, Consumer<OrderEvent> handler) {
            listeners.computeIfAbsent(destination, k -> new ArrayList<>()).add(handler);
        }
        public void simulateIncomingMessage(String destination, OrderEvent event) {
            for (Consumer<OrderEvent> handler : listeners.getOrDefault(destination, List.of())) handler.accept(event);
        }
    }

    // CLOUD-AGNOSTIC business logic -- works with ANY ListenerRegistry implementation, from ANY cloud provider
    static void wireUpBatchLimitedHandler(ListenerRegistry registry, String destination, int maxPerBatch, List<OrderEvent> processedBatch) {
        registry.registerListener(destination, event -> {
            if (processedBatch.size() >= maxPerBatch) {
                System.out.println("batch limit (" + maxPerBatch + ") reached -- deferring order " + event.orderId());
                return;
            }
            processedBatch.add(event);
            System.out.println("processed order " + event.orderId() + " (batch size now " + processedBatch.size() + ")");
        });
    }

    public static void main(String[] args) {
        int maxPerBatch = 2; // resolved from ANY of the three clouds' config/secrets services -- identical logic either way
        List<OrderEvent> processedBatch = new ArrayList<>();

        ListenerRegistry pubSub = new PubSubListenerRegistry(); // could equally be an SQS or Service Bus registry
        wireUpBatchLimitedHandler(pubSub, "order-queue-sub", maxPerBatch, processedBatch);

        pubSub.simulateIncomingMessage("order-queue-sub", new OrderEvent(1, "CONFIRMED"));
        pubSub.simulateIncomingMessage("order-queue-sub", new OrderEvent(2, "CONFIRMED"));
        pubSub.simulateIncomingMessage("order-queue-sub", new OrderEvent(3, "CONFIRMED"));
    }
}
```

How to run: `java SpringCloudGcpLevel3.java`

`wireUpBatchLimitedHandler` is written entirely against the `ListenerRegistry` interface — it would work completely unchanged if handed a hypothetical `SqsListenerRegistry` or `ServiceBusListenerRegistry` implementing the same interface, proving conclusively that the actual batch-limiting business logic in all three cloud cards' examples was never genuinely coupled to AWS, Azure, or GCP specifically; only the concrete registry implementation (standing in for each cloud's specific starter dependency) differs.

## 6. Walkthrough

Trace `wireUpBatchLimitedHandler` and the third incoming message in Level 3.

1. `wireUpBatchLimitedHandler(pubSub, "order-queue-sub", 2, processedBatch)` calls `registry.registerListener(...)` — because `registry`'s runtime type is `PubSubListenerRegistry`, this adds the handler lambda to `listeners.get("order-queue-sub")`'s list, but note this dispatch happens purely through the `ListenerRegistry` interface; the method body never references `PubSubListenerRegistry` by name.
2. The first two `simulateIncomingMessage` calls deliver `OrderEvent(1, ...)` and `OrderEvent(2, ...)` — each triggers the registered lambda, which checks `processedBatch.size() >= maxPerBatch` (`0 >= 2` then `1 >= 2`, both `false`), so both are added to `processedBatch`, bringing it to size `2`.
3. The third call delivers `OrderEvent(3, ...)` — the lambda checks `processedBatch.size() >= maxPerBatch`, now `2 >= 2`, `true`, so it prints the deferral message and returns without modifying `processedBatch`.
4. This is the identical control flow demonstrated in both the Spring Cloud AWS and Spring Cloud Azure cards' Level 3 examples — but here, `wireUpBatchLimitedHandler` is explicitly factored out as a standalone, interface-driven function, making visible and undeniable what was already true in the other two cards: this logic never actually depended on which cloud's messaging service was involved, only on the `ListenerRegistry` interface's contract.

```
wireUpBatchLimitedHandler(ANY ListenerRegistry, destination, maxPerBatch=2, processedBatch):
  registers ONE handler, cloud-agnostic

message 1: batch.size()=0 >= 2? NO  -> processed, batch size now 1
message 2: batch.size()=1 >= 2? NO  -> processed, batch size now 2
message 3: batch.size()=2 >= 2? YES -> DEFERRED

SAME wireUpBatchLimitedHandler function would produce IDENTICAL behavior against
an SqsListenerRegistry or ServiceBusListenerRegistry implementing the same interface
```

## 7. Gotchas & takeaways

> **Gotcha:** GCP Pub/Sub, like AWS SQS and Azure Service Bus, is at-least-once delivery by default — the same idempotency concern flagged in the Spring Cloud AWS card applies identically here, and it's worth explicitly re-confirming rather than assuming a cloud-agnostic abstraction somehow also abstracts away each underlying messaging service's own delivery guarantees, which it does not and should not.

- Spring Cloud GCP completes the three-cloud pattern established across this trio of cards — Cloud Storage, Pub/Sub, and Secret Manager wrapped behind the same `Resource`, listener annotation, and `PropertySource` abstractions already used for AWS and Azure.
- Having seen this identical wrapping pattern applied to all three major cloud providers, the transferable insight is the pattern itself: application business logic written against Spring's own abstractions, rather than any specific cloud SDK, remains portable across cloud providers by construction, as Level 3's `wireUpBatchLimitedHandler` demonstrates concretely.
- GCP-specific integrations beyond the storage/messaging/config trio — Cloud SQL, Firestore, BigQuery — don't have a direct one-to-one parallel in the AWS or Azure cards, reflecting genuine differences in each cloud's own service catalog rather than a gap in the abstraction pattern itself.
- Regardless of which cloud provider's Spring Cloud integration is in use, each underlying managed service's own operational characteristics and guarantees (delivery semantics, consistency models, quota/throttling behavior) still require direct understanding — the shared Spring abstraction simplifies application code's shape, not the need to know what the actual cloud service underneath it does.
