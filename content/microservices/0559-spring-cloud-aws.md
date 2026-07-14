---
card: microservices
gi: 559
slug: spring-cloud-aws
title: "Spring Cloud AWS"
---

## 1. What it is

**Spring Cloud AWS** integrates AWS-managed services into Spring's own abstractions, so application code interacts with SQS queues, SNS topics, S3 buckets, and Parameter Store/Secrets Manager configuration through familiar Spring idioms (`@SqsListener`, a `S3Template`, `@Value`-bound configuration) rather than the raw AWS SDK directly. The goal mirrors [Spring Cloud Kubernetes](0554-spring-cloud-kubernetes.md)'s philosophy applied to AWS specifically: when your deployment platform (AWS) already provides messaging, storage, and secrets infrastructure, integrate with those managed services through Spring's conventions rather than either hand-coding raw AWS SDK calls everywhere or standing up separate infrastructure AWS already provides equivalents for.

## 2. Why & when

You reach for Spring Cloud AWS whenever your application runs on AWS and needs to use its managed messaging, storage, or configuration services, and you want that integration to feel idiomatically Spring rather than raw-SDK:

- **Using the AWS SDK directly means writing boilerplate client setup, request/response object construction, and polling loops by hand** at every place your code needs to send an SQS message or read an S3 object — Spring Cloud AWS wraps this in familiar annotations and templates, similar in spirit to how [Spring Cloud Stream](0547-spring-cloud-stream-event-driven.md) wraps generic message-broker interaction.
- **`@SqsListener` lets a method be triggered automatically when a message arrives on a configured SQS queue**, without hand-writing a polling loop — conceptually similar to a `@KafkaListener` or `@RabbitListener`, but for AWS's own managed queue service.
- **`spring.config.import=aws-parameterstore:` (or `aws-secretsmanager:`) lets configuration values be sourced directly from AWS's own managed configuration/secrets services**, exactly mirroring the pattern discussed for [Spring Cloud Vault](0553-spring-cloud-vault.md) and [Spring Cloud Kubernetes](0554-spring-cloud-kubernetes.md)'s ConfigMap integration — reuse the cloud platform's own native configuration service rather than standing up a separate Config Server when you're already committed to AWS.
- **You reach for this specifically when deployed on AWS and using its managed services** — the value proposition doesn't apply to a deployment target that isn't AWS, in which case you'd reach for the equivalent Spring Cloud Stream binder (for a self-managed broker), Vault (for secrets), or Kubernetes-native integration instead.

## 3. Core concept

Recall the "already-provided-by-the-platform" philosophy from [Spring Cloud Kubernetes](0554-spring-cloud-kubernetes.md): when your deployment platform already has native, managed capabilities for a given concern, integrate with those directly through familiar abstractions rather than duplicating them. Spring Cloud AWS applies the identical philosophy to AWS specifically — instead of running your own message broker for queuing when SQS already exists, or your own Config Server when Parameter Store already exists, Spring Cloud AWS provides the Spring-idiomatic glue to use AWS's own managed versions of these capabilities directly.

Concretely:

1. **`@SqsListener("my-queue")` on a method** automatically subscribes it to receive and process messages from the named SQS queue, handling polling, deserialization, and (by default) message deletion after successful processing — the method body contains only the actual message-handling business logic.
2. **`S3Template` provides a higher-level, Spring-idiomatic API over S3 object operations** (upload, download, list) compared to constructing raw AWS SDK `PutObjectRequest`/`GetObjectRequest` objects by hand at every call site.
3. **`spring.config.import=aws-parameterstore:/config/order-service/` fetches configuration values from AWS Systems Manager Parameter Store** under that path prefix, binding them into the application's `Environment` exactly like any other configuration source — `aws-secretsmanager:` does the equivalent for AWS Secrets Manager.
4. **Spring Cloud AWS also integrates with IAM-based authentication** for these services, using the standard AWS credential provider chain — application code doesn't manage AWS access keys directly in most deployment scenarios, relying instead on the underlying compute environment's (an EC2 instance role, an ECS task role, an EKS pod's IAM role) native AWS identity.

## 4. Diagram

<svg viewBox="0 0 660 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Cloud AWS provides idiomatic Spring integration (annotations, templates, config import) over AWS's own managed SQS, S3, and Parameter Store/Secrets Manager services">
  <rect x="20" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@SqsListener -&gt; SQS</text>
  <rect x="240" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">S3Template -&gt; S3</text>
  <rect x="460" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">config.import -&gt; Parameter Store</text>

  <text x="330" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Spring-idiomatic glue over AWS's own already-managed infrastructure</text>
</svg>

Familiar Spring annotations and templates provide idiomatic access to AWS's own already-managed messaging, storage, and configuration services.

## 5. Runnable example

Scenario: processing an order event delivered via SQS, and reading configuration from Parameter Store. We start with a plain Java model of raw-SDK-style polling boilerplate, extend it to an annotation-driven listener model, then show the real Spring Cloud AWS shape.

### Level 1 — Basic

```java
// File: RawSdkPollingBoilerplate.java -- models the BOILERPLATE a raw
// AWS SDK approach requires: manually polling, deserializing, and
// deleting messages, repeated at every place this pattern is needed.
import java.util.*;

public class RawSdkPollingBoilerplate {
    static Queue<String> simulatedSqsQueue = new LinkedList<>(List.of("{\"orderId\":\"42\"}"));

    static void manualPollLoop() {
        while (!simulatedSqsQueue.isEmpty()) {
            String rawMessage = simulatedSqsQueue.poll(); // manual receive
            System.out.println("Manually received: " + rawMessage);
            // manual deserialization, manual business logic, manual "delete message" call would go here
            System.out.println("Manually processing and deleting message...");
        }
    }

    public static void main(String[] args) {
        manualPollLoop();
        System.out.println("This exact polling/deserialize/delete pattern repeats at EVERY queue-consuming call site.");
    }
}
```

How to run: `java RawSdkPollingBoilerplate.java`

`manualPollLoop` hand-writes the receive-process-delete cycle directly — this same boilerplate structure would need to be duplicated at every place in a codebase that consumes from a different SQS queue, with plenty of room for small inconsistencies between them.

### Level 2 — Intermediate

```java
// File: AnnotationDrivenListenerModel.java -- models the ANNOTATION-
// DRIVEN idea: a plain method marked as a listener, with the framework
// handling polling/deserialization/deletion automatically.
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class AnnotationDrivenListenerModel {
    @Retention(RetentionPolicy.RUNTIME)
    @interface SqsListenerSim { String value(); }

    static class OrderProcessor {
        @SqsListenerSim("order-events-queue")
        public void handleOrderEvent(String messageBody) {
            System.out.println("Processing order event: " + messageBody); // PURE business logic, no polling code here
        }
    }

    // a simplified dispatcher, standing in for what Spring Cloud AWS's real
    // listener container does: find annotated methods, poll THEIR queue, invoke them
    static void dispatchIncomingMessage(Object bean, String queueName, String messageBody) throws Exception {
        for (Method method : bean.getClass().getMethods()) {
            SqsListenerSim annotation = method.getAnnotation(SqsListenerSim.class);
            if (annotation != null && annotation.value().equals(queueName)) {
                method.invoke(bean, messageBody); // framework calls the plain business method
            }
        }
    }

    public static void main(String[] args) throws Exception {
        OrderProcessor processor = new OrderProcessor();
        dispatchIncomingMessage(processor, "order-events-queue", "{\"orderId\":\"42\"}");
    }
}
```

How to run: `java AnnotationDrivenListenerModel.java`

`handleOrderEvent` contains only business logic — no polling loop, no manual deserialization or deletion code. `dispatchIncomingMessage` stands in for Spring Cloud AWS's real listener container, which discovers `@SqsListener`-annotated methods, handles the actual polling against the real SQS queue, and invokes the plain method with the deserialized message body.

### Level 3 — Advanced

```java
// File: SpringCloudAwsRealShape.java -- the REAL Spring Cloud AWS
// shape: @SqsListener for messaging, config.import for Parameter Store,
// with NO raw AWS SDK boilerplate in application code.
import io.awspring.cloud.sqs.annotation.SqsListener;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

public class SpringCloudAwsRealShape {

    record OrderEvent(String orderId, String item) {}

    @Component
    static class OrderEventProcessor {
        @Value("${downstream.pricing.timeout-ms}") // sourced from AWS Parameter Store via spring.config.import
        private int pricingTimeoutMs;

        @SqsListener("order-events-queue") // Spring Cloud AWS handles polling, deserialization, and deletion automatically
        public void handleOrderEvent(OrderEvent event) {
            System.out.println("Processing order " + event.orderId() + " for " + event.item()
                + " (pricing timeout configured as " + pricingTimeoutMs + "ms)");
        }
    }

    // application.yml:
    //   spring.config.import: aws-parameterstore:/config/order-service/
    //   spring.cloud.aws.sqs.region: us-east-1
    // -- credentials resolved automatically via the standard AWS credential provider chain
    //    (e.g. an EC2/ECS/EKS instance's own IAM role), no access keys hardcoded anywhere.
}
```

How to run: requires `spring-cloud-aws-starter-sqs` and `spring-cloud-aws-starter-parameter-store`, running with valid AWS credentials available via the standard credential provider chain (an IAM role in most deployment scenarios), and `spring.cloud.aws.sqs.region` plus the queue and Parameter Store path configured; run via `mvn spring-boot:run`, send a message to the real `order-events-queue` SQS queue, and observe `handleOrderEvent` invoked automatically with the deserialized `OrderEvent`, using a `pricingTimeoutMs` value sourced from the real Parameter Store path.

`handleOrderEvent` contains zero AWS SDK code — `@SqsListener("order-events-queue")` is the single annotation that wires this method to receive real SQS messages, and `@Value("${downstream.pricing.timeout-ms}")` is populated from AWS Parameter Store via `spring.config.import`, exactly as it would be from any other Spring configuration source.

## 6. Walkthrough

Trace what happens when a message is published to the real `order-events-queue` SQS queue, against the Level 3 application:

1. **Spring Cloud AWS's SQS listener container, running as a background component of the application, continuously polls the configured `order-events-queue`** (using AWS's long-polling mechanism underneath, to avoid unnecessary API calls when the queue is empty).
2. **A new message, containing a JSON body like `{"orderId":"42","item":"widget"}`, arrives in the queue** (published by some other part of the system — perhaps an order-placement service).
3. **The listener container receives this message via its next poll**, and because `handleOrderEvent`'s parameter type is `OrderEvent`, it deserializes the message body's JSON into an `OrderEvent` instance using Spring's standard message-conversion machinery.
4. **The listener container invokes `handleOrderEvent(event)`** with the deserialized object — the method reads `pricingTimeoutMs` (already bound at bean-creation time from Parameter Store) and prints its processing message.
5. **Because `handleOrderEvent` completes without throwing an exception, Spring Cloud AWS's listener container automatically deletes the message from the SQS queue** — signaling to SQS that this message has been successfully processed and should not be redelivered.
6. **If `handleOrderEvent` had instead thrown an exception, the message would *not* be deleted**, and SQS's own visibility timeout and redelivery mechanism would make the message available for another poll attempt after that timeout expires — application code gets this retry-on-failure behavior for free, purely from not calling any explicit "delete" step itself, without hand-writing any error-handling or retry logic.

## 7. Gotchas & takeaways

> **Gotcha:** because a failed listener method leaves the message undeleted for SQS's automatic redelivery, `handleOrderEvent`'s logic must be safely retriable (idempotent) — if processing partially succeeds before throwing (say, it already updated a database record, then failed on a subsequent step), a redelivered message reprocessing from scratch can produce duplicate or inconsistent effects unless the handler is written defensively against exactly this retry scenario.

- Spring Cloud AWS provides idiomatic Spring integration (`@SqsListener`, `S3Template`, `spring.config.import`) over AWS's own managed messaging, storage, and configuration services, avoiding both raw-SDK boilerplate and unnecessary duplicate infrastructure.
- `@SqsListener` handles polling, deserialization, and message deletion automatically — application code contains only business logic, with failure handling (via SQS's own redelivery mechanism) available for free by simply letting an exception propagate.
- Configuration and secrets can be sourced directly from AWS Parameter Store or Secrets Manager via `spring.config.import`, mirroring the same pattern used for Vault and Kubernetes ConfigMaps elsewhere in the Spring Cloud ecosystem.
- Because failed messages are automatically retried via SQS's redelivery, listener methods must be written to handle being invoked more than once for the same message safely.
