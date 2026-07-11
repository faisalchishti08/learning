---
card: spring-cloud
gi: 132
slug: spring-cloud-aws-s3-sqs-sns-parameter-store-secrets-manager
title: "Spring Cloud AWS (S3, SQS, SNS, Parameter Store, Secrets Manager)"
---

## 1. What it is

Spring Cloud AWS integrates several AWS services into familiar Spring abstractions — S3 objects accessible through Spring's `Resource` abstraction, SQS/SNS as Spring Cloud Stream or Spring Messaging destinations (with `@SqsListener` for consuming), and AWS Parameter Store / Secrets Manager as externalized configuration `PropertySource`s consumed via ordinary `@Value`/`@ConfigurationProperties` — so application code interacts with AWS infrastructure through the same Spring idioms already used for local files, message queues, and configuration, rather than through AWS's own SDK types directly.

```java
@Value("s3://my-bucket/config/settings.json")
Resource s3Resource; // an S3 object, consumed through Spring's ORDINARY Resource abstraction

@SqsListener("order-queue")
void handleOrderMessage(OrderEvent event) { ... } // SQS consumption, Spring Messaging-style
```

```properties
spring.config.import=aws-parameterstore:/order-service/
# Parameter Store values become ordinary @Value-bound properties, exactly like Vault (an earlier card)
```

## 2. Why & when

An application running on AWS commonly needs to read/write S3 objects, publish/consume SQS or SNS messages, and pull configuration from Parameter Store or secrets from Secrets Manager — and doing all of this through the raw AWS SDK directly means learning and coding against several separate, AWS-specific APIs, each with its own client setup, credential handling, and error model, none of which resembles the Spring abstractions already used elsewhere in the application. Spring Cloud AWS closes this gap the same way Spring Cloud Vault did for HashiCorp Vault (an earlier card) and Spring Cloud Kubernetes did for Kubernetes ConfigMaps/Secrets (also earlier cards): AWS-specific services are wrapped behind Spring's own already-familiar abstractions — `Resource` for S3, `@SqsListener`/messaging templates for SQS/SNS, `PropertySource` for Parameter Store/Secrets Manager — so application code reads mostly like it would for any other Spring-idiomatic resource, file, or externalized configuration source.

Reach for Spring Cloud AWS when:

- Reading or writing S3 objects from a Spring application — using Spring's `Resource` abstraction (`s3://bucket/key`) keeps S3 access consistent with how the rest of the application already treats classpath resources, filesystem resources, and URLs.
- Consuming or publishing SQS/SNS messages — `@SqsListener` and the corresponding messaging templates provide a Spring Messaging-idiomatic interface, avoiding direct AWS SDK polling/receive-message boilerplate.
- Sourcing configuration from Parameter Store or secrets from Secrets Manager — both integrate as `PropertySource`s exactly like Vault or Kubernetes ConfigMaps/Secrets did in earlier cards, letting `@Value`/`@ConfigurationProperties` bindings work identically regardless of which of these backends actually supplies a given property.

## 3. Core concept

```
 raw AWS SDK approach:                     Spring Cloud AWS approach:
   S3Client.getObject(...)                   Resource s3Resource = ...;  s3Resource.getInputStream()
   SqsClient.receiveMessage(...)              @SqsListener("queue") void handle(Message m) { ... }
   SsmClient.getParameter(...)                @Value("${param}") String value;  (via PropertySource)

 EACH AWS service wrapped behind the SAME Spring abstraction already used for
 the non-AWS equivalent (files/URLs, message listeners, externalized properties)
```

Application code written against these Spring abstractions carries no direct AWS SDK type references in its own business logic — the AWS-specific integration lives entirely within Spring Cloud AWS's own implementation of each abstraction.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three separate AWS services S3 SQS and Parameter Store are each wrapped behind a familiar Spring abstraction Resource for S3 a listener annotation for SQS and PropertySource for Parameter Store letting application code use consistent Spring idioms rather than the raw AWS SDK">
  <rect x="20" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="95" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">S3</text>
  <rect x="20" y="75" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="95" y="99" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">SQS / SNS</text>
  <rect x="20" y="130" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="95" y="154" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Parameter Store</text>

  <rect x="260" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="335" y="44" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Resource</text>
  <rect x="260" y="75" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="335" y="99" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">@SqsListener</text>
  <rect x="260" y="130" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="335" y="154" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">PropertySource</text>

  <rect x="480" y="75" width="140" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="550" y="99" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">application code</text>

  <defs><marker id="a132" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="170" y1="40" x2="260" y2="40" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a132)"/>
  <line x1="170" y1="95" x2="260" y2="95" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a132)"/>
  <line x1="170" y1="150" x2="260" y2="150" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a132)"/>
  <line x1="410" y1="95" x2="480" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a132)"/>
</svg>

Three distinct AWS services, three familiar Spring abstractions — one consistent style of application code consuming all three.

## 5. Runnable example

The scenario: model reading configuration from a Parameter-Store-style source and consuming SQS-style messages through Spring-idiomatic abstractions, proving application code stays clean of raw AWS SDK types. Start with Parameter-Store-backed configuration resolution, then add SQS-style message listening, then combine both in a small application that reads its configuration and reacts to queued messages, mirroring realistic combined usage.

### Level 1 — Basic

Parameter Store values resolved as ordinary configuration properties.

```java
import java.util.*;

public class SpringCloudAwsLevel1 {
    // stands in for AWS Parameter Store, integrated as a PropertySource
    static Map<String, String> parameterStore = Map.of("/order-service/rate-limit", "100/min");

    static String resolveProperty(String key) {
        return parameterStore.get(key); // application code just reads a PROPERTY, no AWS SDK call visible here
    }

    public static void main(String[] args) {
        String rateLimit = resolveProperty("/order-service/rate-limit");
        System.out.println("rate-limit (from Parameter Store): " + rateLimit);
    }
}
```

How to run: `java SpringCloudAwsLevel1.java`

`resolveProperty` reads a value that happens to be sourced from Parameter Store, but the calling code looks exactly like reading any other Spring property — no `SsmClient`, no AWS-specific request/response types appear anywhere in this application-facing code.

### Level 2 — Intermediate

Add SQS-style message listening through a Spring Messaging-idiomatic interface, decoupled from raw AWS SQS polling mechanics.

```java
import java.util.*;
import java.util.function.Consumer;

public class SpringCloudAwsLevel2 {
    record OrderEvent(int orderId, String status) {}

    // models the @SqsListener mechanism -- application code registers a HANDLER, never polls SQS directly
    static class SqsListenerRegistry {
        Map<String, List<Consumer<OrderEvent>>> listenersByQueue = new HashMap<>();
        void registerListener(String queueName, Consumer<OrderEvent> handler) {
            listenersByQueue.computeIfAbsent(queueName, k -> new ArrayList<>()).add(handler);
        }
        // models the underlying SQS polling infrastructure delivering a message to registered listeners
        void simulateIncomingMessage(String queueName, OrderEvent event) {
            for (Consumer<OrderEvent> handler : listenersByQueue.getOrDefault(queueName, List.of())) {
                handler.accept(event);
            }
        }
    }

    public static void main(String[] args) {
        SqsListenerRegistry sqs = new SqsListenerRegistry();

        // application code: register a handler, Spring-Messaging-style -- NO raw SQS receive-message loop anywhere
        sqs.registerListener("order-queue", event ->
                System.out.println("handling order event: id=" + event.orderId() + " status=" + event.status()));

        sqs.simulateIncomingMessage("order-queue", new OrderEvent(42, "CONFIRMED"));
    }
}
```

How to run: `java SpringCloudAwsLevel2.java`

`sqs.registerListener` is the only integration point application code touches — it declares "when a message arrives on `order-queue`, run this handler," exactly matching `@SqsListener`'s declarative style, with all the actual SQS polling/receiving mechanics hidden entirely inside `SqsListenerRegistry` (standing in for Spring Cloud AWS's own listener container implementation).

### Level 3 — Advanced

Combine Parameter-Store-backed configuration and SQS-style listening in one small application, where the configured rate limit actually governs how the message handler behaves — mirroring a realistic application using both integrations together.

```java
import java.util.*;
import java.util.function.Consumer;

public class SpringCloudAwsLevel3 {
    record OrderEvent(int orderId, String status) {}

    static Map<String, String> parameterStore = Map.of("/order-service/max-per-batch", "2");

    static String resolveProperty(String key) { return parameterStore.get(key); }

    static class SqsListenerRegistry {
        Map<String, List<Consumer<OrderEvent>>> listenersByQueue = new HashMap<>();
        void registerListener(String queueName, Consumer<OrderEvent> handler) {
            listenersByQueue.computeIfAbsent(queueName, k -> new ArrayList<>()).add(handler);
        }
        void simulateIncomingMessage(String queueName, OrderEvent event) {
            for (Consumer<OrderEvent> handler : listenersByQueue.getOrDefault(queueName, List.of())) handler.accept(event);
        }
    }

    public static void main(String[] args) {
        int maxPerBatch = Integer.parseInt(resolveProperty("/order-service/max-per-batch")); // config-driven behavior
        System.out.println("configured max-per-batch: " + maxPerBatch);

        List<OrderEvent> processedBatch = new ArrayList<>();
        SqsListenerRegistry sqs = new SqsListenerRegistry();

        sqs.registerListener("order-queue", event -> {
            if (processedBatch.size() >= maxPerBatch) {
                System.out.println("batch limit (" + maxPerBatch + ") reached -- deferring order " + event.orderId());
                return;
            }
            processedBatch.add(event);
            System.out.println("processed order " + event.orderId() + " (batch size now " + processedBatch.size() + ")");
        });

        sqs.simulateIncomingMessage("order-queue", new OrderEvent(1, "CONFIRMED"));
        sqs.simulateIncomingMessage("order-queue", new OrderEvent(2, "CONFIRMED"));
        sqs.simulateIncomingMessage("order-queue", new OrderEvent(3, "CONFIRMED")); // exceeds the configured limit
    }
}
```

How to run: `java SpringCloudAwsLevel3.java`

The first two messages are processed normally, but the third is deferred, because `processedBatch.size()` (`2`) has already reached `maxPerBatch` (also `2`, resolved from the Parameter-Store-backed `resolveProperty` call at startup) — this demonstrates both integrations working together naturally: configuration sourced from Parameter Store governs runtime behavior inside an SQS message handler, with neither integration point requiring any AWS SDK-specific code in the application's own business logic.

## 6. Walkthrough

Trace the third `simulateIncomingMessage` call in Level 3.

1. `maxPerBatch` was resolved once at the start of `main`, via `resolveProperty("/order-service/max-per-batch")`, returning `"2"`, parsed to the integer `2` — this value is captured by the listener lambda's closure and remains fixed for the remainder of the program.
2. The first `simulateIncomingMessage` call delivers `OrderEvent(1, "CONFIRMED")` to the registered handler — inside, `processedBatch.size() >= maxPerBatch` checks `0 >= 2`, which is `false`, so the event is added to `processedBatch` (now size `1`) and a processed-order message is printed.
3. The second call delivers `OrderEvent(2, "CONFIRMED")` — `processedBatch.size() >= maxPerBatch` checks `1 >= 2`, still `false`, so this event is also added (`processedBatch` now size `2`) and printed as processed.
4. The third call delivers `OrderEvent(3, "CONFIRMED")` — this time `processedBatch.size() >= maxPerBatch` checks `2 >= 2`, which is `true`, so the handler's `if` branch runs, printing the deferral message and returning immediately without adding this event to `processedBatch` — `processedBatch` remains at size `2`.
5. The configured `maxPerBatch` value, sourced entirely from the (simulated) Parameter Store `PropertySource`, directly controlled this runtime behavior — changing that one configuration value (without touching any application code) would change how many orders the handler processes before deferring, exactly mirroring how a real Spring Cloud AWS-integrated application's `@Value`-bound Parameter Store property can govern SQS message-handling behavior with the configuration and messaging integrations composing cleanly together.

```
maxPerBatch = 2  (resolved from Parameter Store PropertySource)

message 1: processedBatch.size()=0 >= 2? NO  -> processed, batch size now 1
message 2: processedBatch.size()=1 >= 2? NO  -> processed, batch size now 2
message 3: processedBatch.size()=2 >= 2? YES -> DEFERRED, batch size stays 2
```

## 7. Gotchas & takeaways

> **Gotcha:** SQS message delivery is at-least-once by default — a message handler (whether via `@SqsListener` in a real application or the modeled `registerListener` here) may be invoked more than once for the same logical message under certain failure/redelivery scenarios, so handler logic that isn't idempotent (safe to run more than once with the same input without incorrect side effects) risks double-processing. This is a genuine SQS-level concern independent of Spring Cloud AWS's own abstraction, and designing handlers with idempotency in mind is standard practice when consuming SQS, exactly as it is for the broker-based Spring Cloud Stream consumers covered in earlier Messaging cards.

- Spring Cloud AWS's core value is wrapping AWS-specific services (S3, SQS/SNS, Parameter Store, Secrets Manager) behind Spring's own already-familiar abstractions (`Resource`, `@SqsListener`/messaging templates, `PropertySource`), keeping application code idiomatic and largely free of direct AWS SDK type references.
- Parameter Store and Secrets Manager integrate as externalized configuration sources exactly like Vault (an earlier card) and Kubernetes ConfigMaps/Secrets (also earlier cards) — the same `@Value`/`@ConfigurationProperties` consumption pattern works identically regardless of which of these backends actually supplies a given property.
- `@SqsListener` and Spring's messaging templates provide a declarative, Spring-Messaging-idiomatic interface over SQS/SNS, hiding the underlying polling/receive-message mechanics inside Spring Cloud AWS's own listener container implementation, similar in spirit to how Spring Cloud Stream abstracts broker-specific messaging mechanics in earlier cards.
- Application-level concerns genuinely specific to the underlying AWS service (SQS's at-least-once delivery semantics requiring idempotent handlers, S3's eventual consistency characteristics for certain operations) still apply regardless of which Spring abstraction wraps them — the abstraction simplifies the *interface*, not the underlying service's own operational characteristics and guarantees.
