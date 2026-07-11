---
card: spring-cloud
gi: 133
slug: spring-cloud-azure
title: "Spring Cloud Azure"
---

## 1. What it is

Spring Cloud Azure integrates Microsoft Azure services into Spring's familiar abstractions the same way Spring Cloud AWS does for AWS — Azure Blob Storage through Spring's `Resource` abstraction, Azure Service Bus/Event Hubs as Spring Cloud Stream binders or `@ServiceBusListener`-style consumers, and Azure App Configuration / Key Vault as externalized configuration `PropertySource`s consumed via ordinary `@Value`/`@ConfigurationProperties` — plus Azure Active Directory (Microsoft Entra ID) integration for authentication, all configured through Spring Boot's standard auto-configuration and starter dependency model.

```java
@Value("azure-blob://my-container/config/settings.json")
Resource blobResource; // an Azure Blob Storage object, via Spring's ORDINARY Resource abstraction

@ServiceBusListener(destination = "order-queue")
void handleOrderMessage(OrderEvent event) { ... } // Azure Service Bus consumption, Spring Messaging-style
```

```properties
spring.config.import=azure-appconfiguration:
# Azure App Configuration values become ordinary @Value-bound properties, exactly like Vault or Parameter Store
```

## 2. Why & when

The exact same problem Spring Cloud AWS solves for AWS-hosted applications applies equally to Azure-hosted ones: an application needing Blob Storage access, Service Bus/Event Hubs messaging, and App Configuration/Key Vault-sourced settings would otherwise need to code directly against the Azure SDK's own client types and patterns, none of which resemble the Spring abstractions used elsewhere in the application. Spring Cloud Azure applies the identical "wrap the cloud-specific service behind a familiar Spring abstraction" pattern already established for AWS and (via Vault and Kubernetes) for secrets/configuration generally — so a team already comfortable with Spring's `Resource`, messaging listener, and `PropertySource` idioms can apply that same knowledge to an Azure deployment with minimal new concepts to learn.

Reach for Spring Cloud Azure when:

- Deploying a Spring Boot application onto Azure and needing to interact with Azure-native storage (Blob Storage), messaging (Service Bus, Event Hubs), or configuration/secrets (App Configuration, Key Vault) services through Spring-idiomatic code rather than the raw Azure SDK.
- Migrating or maintaining a multi-cloud codebase where the same architectural patterns (external configuration, message-driven processing, blob-style storage access) need to translate across AWS and Azure deployments — recognizing the parallel structure between Spring Cloud AWS and Spring Cloud Azure (same abstractions, different underlying cloud) makes that translation more direct.
- Needing Azure Active Directory-based authentication integrated into a Spring Security-secured application — Spring Cloud Azure provides starters specifically for this, following Spring Security's own OAuth2/OIDC conventions rather than a bespoke Azure-specific security model.

## 3. Core concept

```
 Azure service                Spring abstraction              (parallel to Spring Cloud AWS)
   Blob Storage         ->    Resource                          (parallel to: S3 -> Resource)
   Service Bus/Event Hubs ->  @ServiceBusListener / binder       (parallel to: SQS/SNS -> @SqsListener)
   App Configuration/Key Vault -> PropertySource                (parallel to: Parameter Store -> PropertySource)
   Azure AD (Entra ID)   ->    Spring Security OAuth2/OIDC       (Azure-specific; AWS equivalent differs)

 application code depends on the SPRING abstraction, not the Azure SDK directly --
 the SAME pattern already established for AWS, applied to a DIFFERENT cloud provider
```

Recognizing this parallel structure is the fastest path to understanding Spring Cloud Azure for anyone already familiar with Spring Cloud AWS — the wrapping pattern, not the specific cloud services, is what's being reapplied.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Azure Blob Storage Service Bus and App Configuration are each wrapped behind the same familiar Spring abstractions Resource listener annotations and PropertySource that Spring Cloud AWS already uses for the equivalent AWS services">
  <rect x="20" y="20" width="170" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="105" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Azure Blob Storage</text>
  <rect x="20" y="75" width="170" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="105" y="99" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service Bus / Event Hubs</text>
  <rect x="20" y="130" width="170" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="105" y="154" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">App Configuration / Key Vault</text>

  <rect x="270" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="345" y="44" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Resource</text>
  <rect x="270" y="75" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="345" y="99" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">@ServiceBusListener</text>
  <rect x="270" y="130" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="345" y="154" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">PropertySource</text>

  <rect x="490" y="75" width="130" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="555" y="99" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">application code</text>

  <defs><marker id="a133" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="190" y1="40" x2="270" y2="40" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a133)"/>
  <line x1="190" y1="95" x2="270" y2="95" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a133)"/>
  <line x1="190" y1="150" x2="270" y2="150" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a133)"/>
  <line x1="420" y1="95" x2="490" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a133)"/>
</svg>

Structurally identical to Spring Cloud AWS's own diagram — the abstraction layer is what stays consistent across cloud providers.

## 5. Runnable example

The scenario: model the same configuration-plus-messaging pattern used for the Spring Cloud AWS card, this time framed around Azure App Configuration and Service Bus, to make the parallel structure concrete. Start with App-Configuration-backed property resolution, then add Service-Bus-style listening, then combine both, explicitly comparing the resulting code shape to the equivalent AWS example.

### Level 1 — Basic

App Configuration values resolved as ordinary configuration properties.

```java
import java.util.*;

public class SpringCloudAzureLevel1 {
    // stands in for Azure App Configuration, integrated as a PropertySource
    static Map<String, String> appConfiguration = Map.of("order-service.rate-limit", "100/min");

    static String resolveProperty(String key) {
        return appConfiguration.get(key); // application code just reads a PROPERTY, no Azure SDK call visible here
    }

    public static void main(String[] args) {
        String rateLimit = resolveProperty("order-service.rate-limit");
        System.out.println("rate-limit (from App Configuration): " + rateLimit);
    }
}
```

How to run: `java SpringCloudAzureLevel1.java`

Structurally identical to the Spring Cloud AWS card's Parameter Store example — only the backing service's name changed, the calling pattern (`resolveProperty`, a plain-looking `@Value`-equivalent lookup) is the same.

### Level 2 — Intermediate

Add Service-Bus-style message listening through a Spring-Messaging-idiomatic interface.

```java
import java.util.*;
import java.util.function.Consumer;

public class SpringCloudAzureLevel2 {
    record OrderEvent(int orderId, String status) {}

    // models @ServiceBusListener -- application code registers a HANDLER, never polls Service Bus directly
    static class ServiceBusListenerRegistry {
        Map<String, List<Consumer<OrderEvent>>> listenersByQueue = new HashMap<>();
        void registerListener(String queueName, Consumer<OrderEvent> handler) {
            listenersByQueue.computeIfAbsent(queueName, k -> new ArrayList<>()).add(handler);
        }
        void simulateIncomingMessage(String queueName, OrderEvent event) {
            for (Consumer<OrderEvent> handler : listenersByQueue.getOrDefault(queueName, List.of())) handler.accept(event);
        }
    }

    public static void main(String[] args) {
        ServiceBusListenerRegistry serviceBus = new ServiceBusListenerRegistry();

        serviceBus.registerListener("order-queue", event ->
                System.out.println("handling order event: id=" + event.orderId() + " status=" + event.status()));

        serviceBus.simulateIncomingMessage("order-queue", new OrderEvent(42, "CONFIRMED"));
    }
}
```

How to run: `java SpringCloudAzureLevel2.java`

`serviceBus.registerListener` mirrors `@SqsListener`'s declarative registration style exactly — the actual Azure Service Bus receive/acknowledge mechanics are hidden entirely behind this registry, exactly as SQS's mechanics were hidden in the AWS card's equivalent example.

### Level 3 — Advanced

Combine both, with the App-Configuration-sourced value governing message-handling behavior — and an explicit side-by-side comparison confirming the code shape matches the AWS card's equivalent example structurally, differing only in service names.

```java
import java.util.*;
import java.util.function.Consumer;

public class SpringCloudAzureLevel3 {
    record OrderEvent(int orderId, String status) {}

    static Map<String, String> appConfiguration = Map.of("order-service.max-per-batch", "2");
    static String resolveProperty(String key) { return appConfiguration.get(key); }

    static class ServiceBusListenerRegistry {
        Map<String, List<Consumer<OrderEvent>>> listenersByQueue = new HashMap<>();
        void registerListener(String queueName, Consumer<OrderEvent> handler) {
            listenersByQueue.computeIfAbsent(queueName, k -> new ArrayList<>()).add(handler);
        }
        void simulateIncomingMessage(String queueName, OrderEvent event) {
            for (Consumer<OrderEvent> handler : listenersByQueue.getOrDefault(queueName, List.of())) handler.accept(event);
        }
    }

    public static void main(String[] args) {
        int maxPerBatch = Integer.parseInt(resolveProperty("order-service.max-per-batch"));
        System.out.println("configured max-per-batch (from App Configuration): " + maxPerBatch);

        List<OrderEvent> processedBatch = new ArrayList<>();
        ServiceBusListenerRegistry serviceBus = new ServiceBusListenerRegistry();

        serviceBus.registerListener("order-queue", event -> {
            if (processedBatch.size() >= maxPerBatch) {
                System.out.println("batch limit (" + maxPerBatch + ") reached -- deferring order " + event.orderId());
                return;
            }
            processedBatch.add(event);
            System.out.println("processed order " + event.orderId() + " (batch size now " + processedBatch.size() + ")");
        });

        serviceBus.simulateIncomingMessage("order-queue", new OrderEvent(1, "CONFIRMED"));
        serviceBus.simulateIncomingMessage("order-queue", new OrderEvent(2, "CONFIRMED"));
        serviceBus.simulateIncomingMessage("order-queue", new OrderEvent(3, "CONFIRMED")); // exceeds the configured limit
    }
}
```

How to run: `java SpringCloudAzureLevel3.java`

The output and control flow are identical to the Spring Cloud AWS card's Level 3 example (two orders processed, the third deferred once `maxPerBatch` is reached) — the only differences between this code and that card's equivalent are the class/variable names referencing Azure services instead of AWS ones; the actual application logic pattern (configuration-driven message-handling behavior, decoupled from any specific cloud SDK) is identical, which is precisely the point of both cards sharing this structure.

## 6. Walkthrough

Trace the third `simulateIncomingMessage` call in Level 3.

1. `maxPerBatch` is resolved once at startup from `resolveProperty("order-service.max-per-batch")`, yielding `2`, and captured by the listener lambda's closure.
2. The first message (`OrderEvent(1, "CONFIRMED")`) is delivered — `processedBatch.size() >= maxPerBatch` checks `0 >= 2`, `false`, so it's processed, bringing `processedBatch` to size `1`.
3. The second message similarly checks `1 >= 2`, `false`, and is processed, bringing `processedBatch` to size `2`.
4. The third message checks `2 >= 2`, `true` — the handler prints the deferral message and returns without modifying `processedBatch`, which stays at size `2`.
5. This is exactly the same control flow, driven by the exact same configuration-checked-against-batch-size logic, as the Spring Cloud AWS card's Level 3 walkthrough — confirming that once application code depends on Spring's own abstractions (a resolved property value, a registered message handler) rather than any cloud-specific SDK type, the actual business logic pattern transfers directly between cloud providers with no adaptation needed.

```
maxPerBatch = 2  (resolved from Azure App Configuration PropertySource)

message 1: batch.size()=0 >= 2? NO  -> processed, batch size now 1
message 2: batch.size()=1 >= 2? NO  -> processed, batch size now 2
message 3: batch.size()=2 >= 2? YES -> DEFERRED, batch size stays 2

IDENTICAL control flow to the Spring Cloud AWS card's equivalent example
```

## 7. Gotchas & takeaways

> **Gotcha:** despite the parallel abstraction structure, Azure Service Bus and AWS SQS have genuinely different delivery semantics and features in some respects (Service Bus supports sessions and native dead-lettering with somewhat different configuration than SQS's approach, for instance) — treating the two as fully interchangeable purely because both are wrapped behind a similarly-shaped Spring listener annotation risks missing service-specific behavior that still needs to be understood when actually configuring production message handling on either platform.

- Spring Cloud Azure applies the same "wrap the cloud service behind a familiar Spring abstraction" pattern Spring Cloud AWS already established, letting a team's existing Spring idioms (Resource, messaging listeners, PropertySource) carry over to an Azure deployment with minimal new concepts.
- Recognizing the direct service-to-abstraction parallels (Blob Storage ~ S3 ~ Resource; Service Bus ~ SQS ~ listener annotations; App Configuration/Key Vault ~ Parameter Store/Secrets Manager ~ PropertySource) is the fastest way to transfer existing Spring Cloud AWS knowledge to an Azure context.
- Azure Active Directory (Microsoft Entra ID) integration is one area without a direct AWS equivalent in this same pattern, since AWS's own identity model differs structurally — Spring Cloud Azure's AD integration instead builds on Spring Security's standard OAuth2/OIDC support.
- While the Spring-facing abstraction is deliberately similar across cloud providers, the underlying cloud service's own specific behaviors, configuration options, and operational characteristics still require direct familiarity — the abstraction simplifies the calling code's shape, not the need to understand what's actually happening underneath it.
