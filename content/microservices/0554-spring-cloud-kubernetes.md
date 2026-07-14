---
card: microservices
gi: 554
slug: spring-cloud-kubernetes
title: "Spring Cloud Kubernetes"
---

## 1. What it is

**Spring Cloud Kubernetes** integrates Spring Cloud's abstractions with Kubernetes' own native capabilities, rather than introducing separate infrastructure for them: it provides a [`DiscoveryClient`](0539-spring-cloud-commons-shared-abstractions.md) implementation backed by Kubernetes' Service/Endpoints API (instead of Eureka or Consul), a configuration source backed by Kubernetes ConfigMaps and Secrets (instead of a separate Config Server), and readiness/liveness probe integration with Spring Boot Actuator's health endpoints. The core idea: when your deployment platform already provides service discovery, configuration storage, and health-check orchestration, reuse those native capabilities through Spring's existing abstractions rather than layering redundant Spring Cloud infrastructure (Eureka, Config Server) on top of a platform that already does the same job.

## 2. Why & when

You reach for Spring Cloud Kubernetes specifically when deploying onto Kubernetes, to avoid running duplicate infrastructure Kubernetes already provides natively:

- **Kubernetes already has its own service discovery** — a Kubernetes `Service` object provides a stable DNS name and virtual IP that load-balances across the currently-ready `Pod`s backing it, using its own `Endpoints`/`EndpointSlice` mechanism, entirely independent of Eureka or Consul. Running Eureka *on top of* Kubernetes for the same purpose is redundant infrastructure solving a problem Kubernetes has already solved.
- **Kubernetes already has native configuration and secret storage** — `ConfigMap`s and `Secret`s are first-class Kubernetes objects, mountable as files or environment variables into a Pod. Spring Cloud Kubernetes's config source lets Spring read these directly as `PropertySource`s, avoiding the need for a separate Spring Cloud Config Server when Kubernetes' own primitives already suffice.
- **Kubernetes already has native health-check orchestration** — liveness and readiness probes are how Kubernetes decides whether to restart a container (liveness) or route traffic to it (readiness); Spring Boot Actuator's `/actuator/health/liveness` and `/actuator/health/readiness` endpoints are specifically designed to be probed by Kubernetes directly, without any Spring Cloud Kubernetes-specific glue needed for this particular integration (it's built into Spring Boot's Actuator support for Kubernetes probes).
- **You reach for this module specifically when Kubernetes is your deployment target** — the value proposition is entirely about not duplicating infrastructure Kubernetes already provides; on a non-Kubernetes deployment target, this module simply doesn't apply, and you'd reach for Eureka, Consul, or Spring Cloud Config instead.

## 3. Core concept

Think of moving into an apartment building that already has its own building-wide directory board, its own mail-slot system for building-wide notices, and its own building manager who checks on tenants regularly — bringing your own separate directory service, your own separate notice board, and hiring your own separate building-wide wellness-checker would be pure duplication of what the building already provides natively. Spring Cloud Kubernetes is choosing to use the building's existing directory board (Kubernetes Services), existing mail-slot system (ConfigMaps/Secrets), and existing building manager (liveness/readiness probes) directly, through the same Spring abstractions you'd otherwise point at Eureka or Consul, rather than bringing redundant infrastructure into a building that already has it.

Concretely:

1. **`spring-cloud-starter-kubernetes-client-discovery` (or the fabric8-based variant)** implements `DiscoveryClient` by querying the Kubernetes API server for `Endpoints`/`EndpointSlice` objects backing a named `Service` — application code depending on `DiscoveryClient` needs zero changes from an Eureka- or Consul-backed setup.
2. **`spring-cloud-starter-kubernetes-client-config`** reads `ConfigMap`s and `Secret`s (matching the application's name, by convention) directly from the Kubernetes API and exposes them as Spring `PropertySource`s, feeding `@Value`/`@ConfigurationProperties` bindings exactly as any other configuration source would.
3. **Spring Boot Actuator's Kubernetes probe support** exposes `/actuator/health/liveness` (should this container be restarted?) and `/actuator/health/readiness` (should traffic be routed to this container right now?) as separate, specifically-scoped health groups, matching exactly what a Kubernetes `livenessProbe`/`readinessProbe` configuration expects to check.
4. **None of this requires running Eureka, Consul, or a separate Config Server** — the Kubernetes API server itself is the single source of truth for discovery and configuration, and the kubelet (Kubernetes' per-node agent) is the "health checker," all infrastructure that already exists as part of running Kubernetes at all.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Instead of layering Eureka, Config Server, and custom health checks on top of Kubernetes, Spring Cloud Kubernetes reuses Kubernetes' own Service discovery, ConfigMaps/Secrets, and liveness/readiness probes directly">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Redundant (avoid)</text>
  <rect x="20" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Eureka + Config Server ON TOP of K8s</text>
  <text x="150" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">duplicate infrastructure, extra operational burden</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Cloud Kubernetes</text>
  <rect x="380" y="35" width="260" height="55" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">K8s Services + ConfigMaps/Secrets</text>
  <text x="510" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">+ liveness/readiness probes</text>
  <text x="510" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reuses infrastructure Kubernetes already provides</text>
</svg>

Reusing Kubernetes' own native discovery, configuration, and health-check mechanisms avoids duplicating infrastructure it already provides.

## 5. Runnable example

Scenario: a service discovering another via Kubernetes-native mechanisms. We start with a plain Java model contrasting duplicated versus reused infrastructure, extend it to a ConfigMap-style configuration model, then show the real Spring Cloud Kubernetes/Actuator configuration.

### Level 1 — Basic

```java
// File: DuplicatedVsReusedInfra.java -- models the CORE trade-off:
// running a SEPARATE registry versus reusing the platform's OWN one.
import java.util.*;

public class DuplicatedVsReusedInfra {
    // models Kubernetes' OWN Endpoints data -- already maintained by the platform, no separate registry needed
    static Map<String, List<String>> kubernetesEndpoints = new HashMap<>(Map.of(
        "order-service", List.of("10.1.2.3", "10.1.2.4")
    ));

    static List<String> discoverViaKubernetesNative(String serviceName) {
        return kubernetesEndpoints.getOrDefault(serviceName, List.of()); // reads what K8s ALREADY tracks
    }

    public static void main(String[] args) {
        System.out.println("Discovered via Kubernetes' own Endpoints API: " + discoverViaKubernetesNative("order-service"));
        System.out.println("No separate Eureka server needed -- Kubernetes already maintains this data as part of running Pods behind a Service.");
    }
}
```

How to run: `java DuplicatedVsReusedInfra.java`

`kubernetesEndpoints` models data Kubernetes already maintains natively as part of routing traffic to Pods behind a `Service` — `discoverViaKubernetesNative` simply reads this existing data rather than requiring a separate registry (Eureka) to independently track the same information redundantly.

### Level 2 — Intermediate

```java
// File: ConfigMapAsPropertySource.java -- models reading a Kubernetes
// ConfigMap DIRECTLY as configuration, instead of a separate Config Server.
import java.util.*;

public class ConfigMapAsPropertySource {
    // models a ConfigMap's data, as Kubernetes itself would store and expose it
    static Map<String, String> configMapData = Map.of(
        "downstream.pricing.timeout-ms", "500",
        "feature.new-checkout.enabled", "true"
    );

    static String readProperty(String key) {
        return configMapData.get(key); // reads DIRECTLY from what Kubernetes already stores
    }

    public static void main(String[] args) {
        System.out.println("pricing timeout: " + readProperty("downstream.pricing.timeout-ms"));
        System.out.println("new checkout enabled: " + readProperty("feature.new-checkout.enabled"));
        System.out.println("No separate Config Server needed -- ConfigMap IS the configuration source.");
    }
}
```

How to run: `java ConfigMapAsPropertySource.java`

`configMapData` models a Kubernetes `ConfigMap`'s key-value data — `readProperty` reads it directly, exactly as Spring Cloud Kubernetes's config source does for real `@Value`/`@ConfigurationProperties` bindings, with no separate Config Server needed since the ConfigMap itself already holds the configuration.

### Level 3 — Advanced

```java
// File: SpringCloudKubernetesRealShape.java -- the REAL Spring Cloud
// Kubernetes shape: discovery via K8s Services, config via ConfigMaps,
// and Actuator's NATIVE liveness/readiness probe support.
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

public class SpringCloudKubernetesRealShape {

    @SpringBootApplication
    @EnableDiscoveryClient
    static class OrderServiceApplication {
        public static void main(String[] args) { SpringApplication.run(OrderServiceApplication.class, args); }
        // application.yml:
        //   spring.cloud.kubernetes.discovery.enabled: true
        //   spring.config.import: kubernetes:  -- reads ConfigMaps/Secrets matching this app's name
        //   management.endpoint.health.probes.enabled: true  -- exposes /actuator/health/liveness + /readiness
    }

    @RestController
    static class ConfigController {
        @Value("${downstream.pricing.timeout-ms}") // sourced from a ConfigMap, via spring.config.import: kubernetes:
        private int pricingTimeoutMs;

        @GetMapping("/config-debug")
        public String debug() { return "pricingTimeoutMs=" + pricingTimeoutMs; }
    }

    // Kubernetes Deployment YAML would include:
    //   livenessProbe:  httpGet: { path: /actuator/health/liveness,  port: 8080 }
    //   readinessProbe: httpGet: { path: /actuator/health/readiness, port: 8080 }
    // -- Kubernetes itself calls these, using Spring Boot's OWN built-in probe support, no extra glue needed.
}
```

How to run: requires `spring-cloud-starter-kubernetes-client-all` (or the specific discovery/config starters), running inside an actual Kubernetes cluster with appropriate RBAC permissions to read `Endpoints`/`ConfigMap`s, and a Kubernetes `Deployment` manifest configuring `livenessProbe`/`readinessProbe` against the Actuator paths; deploy via `kubectl apply` and observe the application discovering peer services through Kubernetes' own `Service` objects and reading configuration from a matching `ConfigMap`, with Kubernetes itself managing restarts and traffic routing via the standard probe endpoints.

`ConfigController.pricingTimeoutMs` is populated from a Kubernetes `ConfigMap` via `spring.config.import: kubernetes:`, exactly mirroring how it would be populated from a Config Server elsewhere — and the `livenessProbe`/`readinessProbe` configuration in the Kubernetes Deployment manifest points directly at Spring Boot Actuator's own built-in probe endpoints, requiring no Spring Cloud Kubernetes-specific code for that particular piece, since Spring Boot's Kubernetes probe support is already native to Actuator itself.

## 6. Walkthrough

Trace what happens when Kubernetes detects a Pod's readiness probe failing, in a cluster running the Level 3 application:

1. **Kubernetes' kubelet, per the configured `readinessProbe`, periodically calls `GET /actuator/health/readiness` on the Pod.** This endpoint aggregates Spring Boot Actuator's readiness-scoped health indicators — say, one checking that a required downstream connection pool is initialized and healthy.
2. **If that downstream connection pool becomes unavailable** (its own health indicator reports `DOWN`), the aggregated `/actuator/health/readiness` response also reports `DOWN` (or an HTTP status outside the expected success range).
3. **Kubernetes' kubelet marks this Pod as not-ready**, and — critically — removes it from the `Endpoints`/`EndpointSlice` object backing the corresponding `Service`, meaning traffic is no longer routed to this Pod via that Service's virtual IP or DNS name.
4. **Any other service's `DiscoveryClient.getInstances("order-service")` call, resolved through Spring Cloud Kubernetes' discovery implementation querying the same `Endpoints`/`EndpointSlice` data**, correctly excludes this now-not-ready Pod — exactly the same discovery-reacts-to-health-state behavior discussed for Consul, but here driven entirely by Kubernetes' own native readiness mechanism, with no separate health-check system involved at all.
5. **If the underlying issue also causes the `/actuator/health/liveness` endpoint to report unhealthy** (a distinct, typically narrower set of checks — is the application in a genuinely unrecoverable, deadlocked, or corrupted state, as opposed to merely "not ready to serve traffic right now"), Kubernetes' kubelet would instead restart the container entirely, based on the separately-configured `livenessProbe` — a different remediation action for a different signal.

## 7. Gotchas & takeaways

> **Gotcha:** conflating liveness and readiness into a single health check (or configuring both probes against the same endpoint with the same underlying checks) can cause Kubernetes to restart a container for a transient, recoverable condition (like a temporarily unavailable downstream dependency) that should only have caused it to be marked not-ready and removed from traffic — not restarted; keep the liveness check narrowly scoped to "is this process itself unrecoverably broken" and the readiness check broader ("can this instance currently serve traffic correctly right now"), matching Spring Boot Actuator's own default separation of these two probe groups.

- Spring Cloud Kubernetes reuses Kubernetes' own native Service discovery, ConfigMap/Secret configuration, and liveness/readiness probe mechanisms through Spring's existing abstractions, avoiding duplicate infrastructure (Eureka, Config Server) on a platform that already provides equivalent capabilities.
- Application code depending on `DiscoveryClient` or `@Value`/`@ConfigurationProperties` needs zero changes moving to Kubernetes-native discovery and configuration — only the dependency and Kubernetes manifest configuration differ.
- Spring Boot Actuator's liveness and readiness health groups are specifically designed to be probed by Kubernetes directly — keep their scopes distinct, since they trigger different remediation actions (restart versus traffic removal).
- This module's value is entirely specific to Kubernetes deployment — on other platforms, reach for Eureka, Consul, ZooKeeper, or Spring Cloud Config instead.
