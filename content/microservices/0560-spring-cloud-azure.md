---
card: microservices
gi: 560
slug: spring-cloud-azure
title: "Spring Cloud Azure"
---

## 1. What it is

**Spring Cloud Azure** provides the equivalent idiomatic Spring integration for Microsoft Azure's managed services that [Spring Cloud AWS](0559-spring-cloud-aws.md) provides for AWS: Spring-friendly access to Azure Service Bus (queues and topics) via listener annotations, Azure Blob Storage via a template abstraction, and Azure App Configuration/Key Vault for centralized configuration and secrets — all authenticated through Azure's own identity mechanisms (managed identity, service principals) rather than application code juggling raw connection strings or SDK client setup directly.

## 2. Why & when

You reach for Spring Cloud Azure specifically when your application runs on Azure and needs to integrate with its managed messaging, storage, and configuration services in an idiomatically Spring way:

- **Azure Service Bus is Azure's managed messaging service** (comparable in role to AWS SQS/SNS or RabbitMQ), supporting both simple queues and richer publish-subscribe topics with subscription filters — Spring Cloud Azure's `@ServiceBusListener`-style annotations let a method be triggered automatically on message arrival, without hand-written polling or connection management code.
- **Azure Blob Storage integration provides a Spring-idiomatic template** for upload/download/list operations, similar in spirit to Spring Cloud AWS's `S3Template`, sparing application code from directly constructing Azure SDK client objects and request builders at every call site.
- **Azure App Configuration and Key Vault integrate via `spring.config.import`**, letting configuration values and secrets be sourced directly from these managed Azure services — the same pattern discussed for [Spring Cloud Vault](0553-spring-cloud-vault.md) and [Spring Cloud AWS](0559-spring-cloud-aws.md)'s Parameter Store integration, applied to Azure's equivalents.
- **Authentication defaults to Azure's managed identity mechanism** where available (an App Service, AKS pod, or VM's system-assigned or user-assigned managed identity), avoiding the need to embed connection strings or credentials directly in application configuration — mirroring the IAM-role-based credential resolution discussed for Spring Cloud AWS, applied to Azure's own identity model.

## 3. Core concept

The underlying philosophy is identical to Spring Cloud AWS, just pointed at a different cloud provider's managed services: rather than hand-writing raw Azure SDK boilerplate at every integration point, or standing up separate infrastructure (a self-hosted message broker, a separate secrets vault) when Azure already provides managed equivalents, Spring Cloud Azure supplies the Spring-idiomatic glue — annotations, templates, and configuration-import mechanisms — over Azure's own Service Bus, Blob Storage, App Configuration, and Key Vault.

Concretely:

1. **`@ServiceBusListener("order-events-queue")` on a method** subscribes it to receive and process Service Bus messages automatically, with Spring Cloud Azure handling the underlying connection, message deserialization, and completion/abandonment semantics (Service Bus's terms for "acknowledge successfully processed" versus "let this message be redelivered or dead-lettered").
2. **A `BlobStorageTemplate`-style abstraction wraps common blob operations** (upload, download, list a container's contents) behind a Spring-friendly API, rather than requiring direct use of Azure's `BlobServiceClient` and its associated builder objects at every call site.
3. **`spring.config.import=azure-app-configuration:` and `azure-keyvault:` fetch configuration and secrets respectively**, binding them into the application's `Environment` exactly like any other Spring configuration source.
4. **Managed identity authentication means an Azure-hosted application (App Service, AKS, a VM) can access these services using its own assigned Azure identity**, without embedding a connection string, access key, or client secret directly in application configuration — the credential resolution happens transparently, based on the identity of the compute environment the application is actually running in.

## 4. Diagram

<svg viewBox="0 0 660 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Cloud Azure provides idiomatic Spring integration over Azure Service Bus, Blob Storage, and App Configuration/Key Vault, authenticated via managed identity">
  <rect x="20" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@ServiceBusListener</text>
  <rect x="240" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Blob Storage template</text>
  <rect x="460" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">App Config / Key Vault</text>

  <text x="330" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">authenticated transparently via Azure managed identity, no embedded credentials</text>
</svg>

Familiar Spring abstractions over Azure's managed messaging, storage, and configuration services, authenticated via managed identity.

## 5. Runnable example

Scenario: processing an order event via Service Bus, with configuration from App Configuration. We start with a plain Java model of manual connection-string-based access, extend it to a managed-identity model, then show the real Spring Cloud Azure shape.

### Level 1 — Basic

```java
// File: ConnectionStringBoilerplate.java -- models the RISK of manually
// embedding a connection string directly in application code/config.
public class ConnectionStringBoilerplate {
    // a hardcoded connection string -- a STANDING credential, embedded directly
    static final String SERVICE_BUS_CONNECTION_STRING = "Endpoint=sb://my-bus.servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=SECRET_VALUE_HERE";

    static void connectUsingConnectionString() {
        System.out.println("Connecting using embedded connection string: " + SERVICE_BUS_CONNECTION_STRING.substring(0, 40) + "...");
        System.out.println("Problem: this credential is embedded directly, valid indefinitely, and must be manually rotated everywhere it's used.");
    }

    public static void main(String[] args) {
        connectUsingConnectionString();
    }
}
```

How to run: `java ConnectionStringBoilerplate.java`

A hardcoded connection string is a standing, long-lived credential embedded directly in code or configuration — anyone with access to it can use it indefinitely, and rotating it requires updating every place it's configured, exactly the static-secret risk discussed for [Spring Cloud Vault](0553-spring-cloud-vault.md).

### Level 2 — Intermediate

```java
// File: ManagedIdentityModel.java -- models AUTHENTICATING via the
// compute environment's OWN identity, with NO embedded credential at all.
public class ManagedIdentityModel {
    // models querying the environment's OWN assigned identity, rather than a hardcoded secret
    static String resolveIdentityToken(String currentComputeEnvironmentIdentity) {
        return "token-for-identity:" + currentComputeEnvironmentIdentity; // issued dynamically, tied to WHO is asking
    }

    static void connectUsingManagedIdentity(String appServiceManagedIdentityName) {
        String token = resolveIdentityToken(appServiceManagedIdentityName);
        System.out.println("Connecting using managed identity token: " + token);
        System.out.println("No embedded connection string anywhere -- credential resolved dynamically from the environment's own identity.");
    }

    public static void main(String[] args) {
        connectUsingManagedIdentity("order-service-app-service-identity");
    }
}
```

How to run: `java ManagedIdentityModel.java`

`resolveIdentityToken` models Azure's managed identity mechanism: a token issued dynamically based on *which* compute resource (an App Service, an AKS pod) is actually asking, rather than a static, long-lived secret embedded anywhere — no connection string needs to be stored, rotated, or protected as a standing artifact at all.

### Level 3 — Advanced

```java
// File: SpringCloudAzureRealShape.java -- the REAL Spring Cloud Azure
// shape: @ServiceBusListener plus App Configuration import, with
// managed identity authentication configured, no secrets in code.
import com.azure.spring.messaging.servicebus.core.annotation.ServiceBusListener;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

public class SpringCloudAzureRealShape {

    record OrderEvent(String orderId, String item) {}

    @Component
    static class OrderEventProcessor {
        @Value("${downstream.pricing.timeout-ms}") // sourced from Azure App Configuration via spring.config.import
        private int pricingTimeoutMs;

        @ServiceBusListener(destination = "order-events-queue") // handles connection, deserialization, completion automatically
        public void handleOrderEvent(OrderEvent event) {
            System.out.println("Processing order " + event.orderId() + " for " + event.item()
                + " (pricing timeout configured as " + pricingTimeoutMs + "ms)");
        }
    }

    // application.yml:
    //   spring.config.import: azure-app-configuration:
    //   spring.cloud.azure.appconfiguration.stores[0].endpoint: https://my-app-config.azconfig.io
    //   spring.cloud.azure.credential.managed-identity-enabled: true
    // -- authenticates via THIS App Service/AKS pod's OWN managed identity, no client secret configured anywhere.
}
```

How to run: requires `spring-cloud-azure-starter-servicebus` and `spring-cloud-azure-starter-appconfiguration`, deployed to an Azure compute environment (App Service, AKS, a VM) with a managed identity assigned and granted appropriate RBAC access to the Service Bus namespace and App Configuration store; run and observe `handleOrderEvent` invoked automatically for real Service Bus messages, using `pricingTimeoutMs` sourced from the real App Configuration store, with zero credentials embedded in application configuration.

`handleOrderEvent` contains no Azure SDK connection code — `@ServiceBusListener` handles the connection and message lifecycle, and `spring.cloud.azure.credential.managed-identity-enabled: true` means authentication happens transparently based on the running compute environment's own assigned Azure identity, exactly mirroring the IAM-role-based credential resolution discussed for Spring Cloud AWS.

## 6. Walkthrough

Trace what happens when a message arrives on the real `order-events-queue` Service Bus queue, against the Level 3 application:

1. **Spring Cloud Azure's Service Bus listener container, authenticated via the App Service's managed identity, maintains an active connection to the configured Service Bus namespace**, established without any connection string or client secret configured in the application at all — Azure's own identity infrastructure verified the App Service's managed identity has permission to access this Service Bus namespace when the connection was first established.
2. **A message arrives on `order-events-queue`.** The listener container receives it and, because `handleOrderEvent`'s parameter type is `OrderEvent`, deserializes the message body's JSON accordingly.
3. **`handleOrderEvent(event)` is invoked** — it reads `pricingTimeoutMs` (bound at startup from Azure App Configuration, itself accessed via the same managed identity) and prints its processing message.
4. **Because `handleOrderEvent` completes without exception, Spring Cloud Azure automatically "completes" the message** — Service Bus's term for acknowledging successful processing, removing it from the queue.
5. **If `handleOrderEvent` had thrown an exception instead, the message would be "abandoned"** (made available for redelivery, up to Service Bus's configured max delivery count) or moved to a dead-letter queue, depending on configuration — application code gets this retry/dead-letter behavior without writing any explicit error-handling logic for it.

## 7. Gotchas & takeaways

> **Gotcha:** managed identity requires the RBAC role assignments granting that identity access to each specific Azure resource (the Service Bus namespace, the App Configuration store) to be configured correctly in Azure itself — a missing role assignment surfaces as an authorization failure at connection time, which can be confusing to diagnose if you're expecting managed identity to "just work" without realizing the corresponding Azure-side permission grant is a separate, required step.

- Spring Cloud Azure mirrors Spring Cloud AWS's philosophy for Azure's own managed services — Service Bus, Blob Storage, App Configuration, Key Vault — through idiomatic Spring annotations, templates, and configuration-import mechanisms.
- Managed identity authentication avoids embedding connection strings or client secrets directly in application configuration, resolving credentials transparently based on the running compute environment's own Azure identity.
- `@ServiceBusListener` handles connection management, deserialization, and message completion/dead-lettering automatically — application code contains only business logic.
- Managed identity's transparent authentication still requires explicit, correctly-configured RBAC role assignments on the Azure side — it isn't automatic just because the application code doesn't mention credentials.
