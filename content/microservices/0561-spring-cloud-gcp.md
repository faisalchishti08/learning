---
card: microservices
gi: 561
slug: spring-cloud-gcp
title: "Spring Cloud GCP"
---

## 1. What it is

**Spring Cloud GCP** completes the trio alongside [Spring Cloud AWS](0559-spring-cloud-aws.md) and [Spring Cloud Azure](0560-spring-cloud-azure.md): idiomatic Spring integration for Google Cloud Platform's managed services — Pub/Sub (messaging) via listener-style templates, Cloud Storage via a Spring `Resource` abstraction (letting `gs://` paths work with Spring's ordinary resource-loading idioms), and Secret Manager for centralized secrets, all authenticated through GCP's own identity mechanism (a service account, often auto-detected from the running compute environment — GCE, GKE, Cloud Run — without any credential file needing to be manually configured in most deployment scenarios).

## 2. Why & when

You reach for Spring Cloud GCP whenever your application runs on Google Cloud and needs to integrate with its managed messaging, storage, or secrets services in an idiomatically Spring way:

- **Google Cloud Pub/Sub is GCP's managed messaging service**, offering both push and pull delivery models; Spring Cloud GCP's `PubSubTemplate` (and reactive/listener-style conveniences built on it) lets application code publish and subscribe without hand-writing GCP client library boilerplate at every integration point.
- **A distinctive convenience of Spring Cloud GCP is treating Cloud Storage objects as ordinary Spring `Resource`s** — a `gs://my-bucket/my-file.txt` path can be injected via `@Value("gs://my-bucket/my-file.txt") Resource file` and read exactly like any other Spring `Resource` (a classpath resource, a filesystem file), letting code that already works with Spring's `Resource` abstraction transparently work with Cloud Storage objects too, with no GCS-specific code required at the call site.
- **Secret Manager integrates via `spring.config.import=sm://`**, letting secrets be sourced directly from GCP's managed secret store — the same pattern discussed for Vault, AWS Secrets Manager, and Azure Key Vault, applied to GCP's equivalent.
- **Authentication defaults to GCP's Application Default Credentials mechanism**, which automatically discovers the right service account credentials based on the running environment (a GCE VM's attached service account, a GKE pod's Workload Identity binding, a Cloud Run service's assigned service account) — application code and configuration typically never need to reference a credential file path directly when running on GCP compute.

## 3. Core concept

The same underlying philosophy as Spring Cloud AWS and Azure, now applied to GCP: idiomatic Spring glue over managed services you'd otherwise either hand-code against a raw client library or duplicate with separate self-hosted infrastructure. What's distinctive about the GCP integration specifically is how deeply it folds into Spring's *existing* abstractions rather than introducing entirely new ones — treating a Cloud Storage object as a plain `Resource` means code already written against Spring's generic resource-loading model works unchanged, simply pointed at a `gs://` URL instead of a `classpath:` or `file:` one.

Concretely:

1. **`PubSubTemplate.publish(topic, message)` and subscription-based listeners** wrap GCP Pub/Sub's publish/subscribe API in a Spring-friendly interface, handling serialization and acknowledgment (Pub/Sub's term for confirming successful message processing) without manual client setup at every call site.
2. **`@Value("gs://bucket-name/object-key") Resource gcsResource`** resolves a Cloud Storage object as an ordinary Spring `Resource`, injectable and readable (`gcsResource.getInputStream()`) exactly like any other resource type Spring already supports — no GCS-specific API calls needed in the consuming code.
3. **`spring.config.import=sm://my-secret/versions/latest`** fetches a secret directly from GCP Secret Manager, binding it into the `Environment` like any other configuration source.
4. **Application Default Credentials (ADC) resolves the right service account automatically** based on the compute environment — a GKE pod using Workload Identity, for instance, authenticates as a specific GCP service account bound to its Kubernetes service account, without any credential file or key needing to be mounted or referenced explicitly in most configurations.

## 4. Diagram

<svg viewBox="0 0 660 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Cloud GCP provides idiomatic Spring integration over Pub/Sub, Cloud Storage (as a Resource), and Secret Manager, authenticated via Application Default Credentials">
  <rect x="20" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">PubSubTemplate</text>
  <rect x="240" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">gs:// as Resource</text>
  <rect x="460" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Secret Manager (sm://)</text>

  <text x="330" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">authenticated via Application Default Credentials, auto-detected from the compute environment</text>
</svg>

Familiar Spring abstractions, including the generic Resource interface itself, provide idiomatic access to GCP's managed services.

## 5. Runnable example

Scenario: publishing an order event and reading a configuration file stored in Cloud Storage. We start with a plain Java model of manually reading a remote file versus treating it as a generic resource, extend it to a Pub/Sub publish model, then show the real Spring Cloud GCP shape.

### Level 1 — Basic

```java
// File: ManualRemoteFileHandling.java -- models handling a REMOTE
// storage object with STORAGE-SPECIFIC code, rather than a generic
// resource abstraction the rest of the codebase already understands.
public class ManualRemoteFileHandling {
    // imagine this represents GCS-SPECIFIC client code, tightly coupled to Cloud Storage's own API shape
    static String gcsSpecificReadObject(String bucket, String objectKey) {
        System.out.println("[GCS-specific client] reading gs://" + bucket + "/" + objectKey);
        return "downstream.pricing.timeout-ms=500";
    }

    public static void main(String[] args) {
        String contents = gcsSpecificReadObject("order-service-config", "application.properties");
        System.out.println("Contents: " + contents);
        System.out.println("Problem: reading this requires GCS-SPECIFIC code, different from reading a classpath or filesystem resource.");
    }
}
```

How to run: `java ManualRemoteFileHandling.java`

`gcsSpecificReadObject` is written specifically against a Cloud Storage-shaped API — code elsewhere in the same application that reads a classpath resource or a local file uses an entirely different API shape, meaning "read some content from somewhere" isn't a unified concept across these different sources.

### Level 2 — Intermediate

```java
// File: GenericResourceModel.java -- models treating DIFFERENT sources
// (classpath, filesystem, cloud storage) through ONE unified interface,
// exactly like Spring's Resource abstraction.
import java.util.*;
import java.util.function.Supplier;

public class GenericResourceModel {
    interface GenericResource { String readContents(); } // ONE interface, regardless of WHERE the data actually lives

    static GenericResource classpathResource(String path) {
        return () -> "classpath content for " + path;
    }
    static GenericResource gcsResource(String gsPath) {
        return () -> "GCS content for " + gsPath + " (fetched via Cloud Storage underneath, but caller doesn't know that)";
    }

    static void printResourceContents(GenericResource resource) {
        System.out.println(resource.readContents()); // caller code is IDENTICAL regardless of the actual source
    }

    public static void main(String[] args) {
        printResourceContents(classpathResource("application.properties"));
        printResourceContents(gcsResource("gs://order-service-config/application.properties"));
        System.out.println("SAME printResourceContents method works for BOTH sources -- no source-specific code at the call site.");
    }
}
```

How to run: `java GenericResourceModel.java`

`printResourceContents` depends only on the `GenericResource` interface — it works identically whether given a classpath-backed or GCS-backed implementation, exactly mirroring how Spring's `Resource` interface lets `gs://` paths be consumed by any code already written against the generic `Resource` abstraction, with zero GCS-specific code needed at the consuming call site.

### Level 3 — Advanced

```java
// File: SpringCloudGcpRealShape.java -- the REAL Spring Cloud GCP
// shape: gs:// injected as a plain Resource, and PubSubTemplate for messaging.
import com.google.cloud.spring.pubsub.core.PubSubTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

public class SpringCloudGcpRealShape {

    @Service
    static class OrderService {
        // a Cloud Storage object, injected as an ORDINARY Spring Resource -- no GCS-specific code needed here
        @Value("gs://order-service-config/pricing-notes.txt")
        private Resource pricingNotesResource;

        private final PubSubTemplate pubSubTemplate;
        OrderService(PubSubTemplate pubSubTemplate) { this.pubSubTemplate = pubSubTemplate; }

        void readPricingNotes() throws Exception {
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(pricingNotesResource.getInputStream(), StandardCharsets.UTF_8))) {
                System.out.println("Pricing notes: " + reader.readLine()); // reads EXACTLY like any other Spring Resource
            }
        }

        void publishOrderPlaced(String orderId) {
            pubSubTemplate.publish("order-events-topic", "{\"orderId\":\"" + orderId + "\"}");
            // GCP Pub/Sub handles delivery to every subscriber of "order-events-topic" from here
        }
    }

    // application.yml:
    //   spring.cloud.gcp.project-id: my-gcp-project
    // -- credentials resolved automatically via Application Default Credentials
    //    (e.g. a GKE pod's Workload Identity binding), no key file referenced.
}
```

How to run: requires `spring-cloud-gcp-starter-storage` and `spring-cloud-gcp-starter-pubsub`, running with Application Default Credentials resolvable (typically automatic on GCE/GKE/Cloud Run, or via `gcloud auth application-default login` locally), and `spring.cloud.gcp.project-id` configured; run and call `readPricingNotes()` to see the real GCS object's content read via the ordinary `Resource` API, and `publishOrderPlaced(...)` to see a message actually published to the real Pub/Sub topic.

`pricingNotesResource` is typed as plain `org.springframework.core.io.Resource` — the exact same interface used for classpath and filesystem resources throughout Spring — with `gs://` triggering Spring Cloud GCP's `Resource` implementation to fetch from Cloud Storage transparently underneath. `pubSubTemplate.publish(...)` handles the actual GCP Pub/Sub API interaction, letting `OrderService` remain unaware of the underlying REST/gRPC calls Pub/Sub publishing actually involves.

## 6. Walkthrough

Trace what happens when `readPricingNotes()` is called, against the Level 3 application:

1. **`pricingNotesResource.getInputStream()` is called.** Because this `Resource` was resolved from a `gs://order-service-config/pricing-notes.txt` value, Spring Cloud GCP's `Resource` implementation (rather than the classpath- or filesystem-backed implementations Spring provides by default) handles this call.
2. **Behind the scenes, this implementation authenticates to GCP using Application Default Credentials** (resolved automatically from the running environment's service account — say, a GKE pod's Workload Identity binding) and issues the actual Cloud Storage API request to fetch the object's contents.
3. **The object's byte stream is wrapped and returned as an ordinary `InputStream`**, exactly the same return type any other `Resource` implementation would provide — the calling code (`readPricingNotes`) has no branch, no special-case handling, and no awareness that this particular stream originated from a network call to Cloud Storage rather than a local file read.
4. **`readPricingNotes` reads and prints the first line**, completing exactly as it would for a classpath or filesystem resource — the only thing that differed anywhere in this flow was the `gs://` prefix on the originally-injected value.

Now trace `publishOrderPlaced("42")`: **`pubSubTemplate.publish("order-events-topic", "{\"orderId\":\"42\"}")` is called.** `PubSubTemplate`, authenticated via the same Application Default Credentials mechanism, serializes and publishes this message to the real `order-events-topic` Pub/Sub topic — any service with an active subscription to that topic (configured separately, in GCP itself or via a corresponding `@Component` using Spring Cloud GCP's Pub/Sub listener support) receives and processes this message asynchronously, entirely decoupled from `OrderService`'s own execution.

## 7. Gotchas & takeaways

> **Gotcha:** treating a `gs://` path as an ordinary `Resource` is convenient, but it can also obscure that a "simple" resource read is actually a network call to Cloud Storage — code that reads this resource frequently, in a hot path, without realizing it's making a remote call each time (rather than a fast local file read) can introduce unexpected latency or GCP API cost that isn't obvious from the code's own appearance; treat repeated reads of a `gs://`-backed `Resource` with the same care you'd give any other network-bound operation, including considering caching the content locally if it's read often and changes rarely.

- Spring Cloud GCP mirrors the Spring Cloud AWS/Azure philosophy for Google Cloud's managed services — Pub/Sub, Cloud Storage, Secret Manager — through idiomatic Spring abstractions.
- Its most distinctive convenience is exposing Cloud Storage objects as ordinary Spring `Resource`s, letting code already written against that generic interface work unchanged against `gs://` paths.
- Application Default Credentials resolves the right service account automatically based on the running compute environment, typically without any credential file needing to be referenced explicitly in application configuration.
- Be mindful that a `Resource`-shaped read against a `gs://` path is still a real network call underneath — the clean abstraction can obscure the latency and cost implications of reading it frequently in a hot code path.
