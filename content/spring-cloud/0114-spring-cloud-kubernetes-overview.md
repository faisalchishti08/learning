---
card: spring-cloud
gi: 114
slug: spring-cloud-kubernetes-overview
title: "Spring Cloud Kubernetes overview"
---

## 1. What it is

Spring Cloud Kubernetes lets Spring Cloud applications deployed on Kubernetes reuse Kubernetes' own native platform capabilities — ConfigMaps and Secrets for configuration, the Kubernetes API for service discovery, kube-proxy/Services for load balancing — through the exact same Spring Cloud abstractions (`Environment` properties, `DiscoveryClient`, `@LoadBalanced`) that earlier cards covered for Config Server, Eureka, and Ribbon/LoadBalancer, so an application already written against those Spring Cloud interfaces needs little or no code change to run natively on Kubernetes instead of a standalone Spring Cloud stack.

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-kubernetes-client</artifactId>
</dependency>
```

```properties
spring.cloud.kubernetes.config.enabled=true
spring.cloud.kubernetes.discovery.enabled=true
```

## 2. Why & when

Kubernetes already natively provides most of what a standalone Spring Cloud microservices stack (Config Server, Eureka, Ribbon) was built to provide independently — ConfigMaps/Secrets for externalized configuration, the Kubernetes API and DNS for service discovery, and Services/kube-proxy for load balancing — so running a Spring Cloud application that still depends on a separately-deployed Config Server and Eureka *inside* a Kubernetes cluster duplicates infrastructure the platform already offers. Spring Cloud Kubernetes bridges this gap: it implements Spring Cloud's own `DiscoveryClient`, `PropertySource`, and related interfaces backed by Kubernetes' native APIs instead of Eureka/Config Server, so application code written against those Spring Cloud abstractions works unchanged, while the actual underlying implementation shifts to Kubernetes-native mechanisms.

Reach for Spring Cloud Kubernetes when:

- Deploying a Spring Cloud application onto Kubernetes and wanting to eliminate redundant infrastructure — replacing a standalone Eureka server and Config Server with Kubernetes' own native service discovery and ConfigMaps/Secrets simplifies the overall deployment.
- Migrating an existing Spring Cloud Netflix (Eureka-based) application onto Kubernetes — Spring Cloud Kubernetes's `DiscoveryClient` implementation is a drop-in replacement for Eureka's, requiring dependency and configuration changes rather than application code rewrites, in most cases.
- Wanting configuration and discovery behavior that stays consistent with how the rest of the Kubernetes ecosystem (non-Spring workloads, platform tooling) already observes and manages the cluster — since Spring Cloud Kubernetes reads the exact same ConfigMaps, Secrets, and Service objects any other Kubernetes-aware tooling would.

## 3. Core concept

```
 standalone Spring Cloud stack (pre-Kubernetes):
   Config Server (separately deployed) -> application's Environment
   Eureka (separately deployed)        -> application's DiscoveryClient

 Spring Cloud Kubernetes (running IN Kubernetes):
   Kubernetes ConfigMaps/Secrets (platform-native) -> application's Environment  (SAME interface)
   Kubernetes API / Service objects (platform-native) -> application's DiscoveryClient (SAME interface)

 application code calling Environment.getProperty(...) or DiscoveryClient.getInstances(...)
 -- UNCHANGED regardless of which implementation is actually backing those calls
```

The Spring Cloud abstraction layer is what makes this substitution possible — application code was never coupled to Eureka or Config Server directly, only to the neutral Spring Cloud interfaces sitting in front of them.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code calling the same Spring Cloud DiscoveryClient and Environment interfaces can be backed either by a standalone Eureka and Config Server stack or by Kubernetes native ConfigMaps Secrets and the Kubernetes API with no change to the calling code">
  <rect x="220" y="20" width="200" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">DiscoveryClient / Environment</text>
  <text x="320" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">neutral Spring Cloud interfaces</text>

  <rect x="30" y="120" width="220" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="140" y="142" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">standalone Eureka + Config Server</text>
  <text x="140" y="156" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">separately deployed</text>

  <rect x="390" y="120" width="220" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="500" y="142" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Kubernetes API + ConfigMaps/Secrets</text>
  <text x="500" y="156" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">platform-native</text>

  <defs><marker id="a114" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="280" y1="66" x2="160" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a114)"/>
  <line x1="360" y1="66" x2="480" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a114)"/>
</svg>

Two structurally different backing infrastructures, one unchanged application-facing abstraction — the essence of Spring Cloud Kubernetes's value.

## 5. Runnable example

The scenario: model the same `DiscoveryClient`-shaped lookup backed first by a Eureka-style registry, then by a Kubernetes-API-style registry, proving application code calling the interface is unaffected by which backs it. Start with a Eureka-backed lookup, then swap in a Kubernetes-backed lookup with identical calling code, then add ConfigMap-backed property resolution alongside it, mirroring the combined discovery-plus-config value Spring Cloud Kubernetes provides.

### Level 1 — Basic

A Eureka-style discovery lookup — the standalone-stack baseline.

```java
import java.util.*;

public class SpringCloudK8sLevel1 {
    interface DiscoveryClient { List<String> getInstances(String serviceId); }

    static class EurekaDiscoveryClient implements DiscoveryClient {
        public List<String> getInstances(String serviceId) {
            System.out.println("querying Eureka registry for: " + serviceId);
            return List.of("10.0.1.5:8080", "10.0.1.6:8080");
        }
    }

    static void callService(DiscoveryClient discovery, String serviceId) {
        List<String> instances = discovery.getInstances(serviceId);
        System.out.println("found instances: " + instances);
    }

    public static void main(String[] args) {
        DiscoveryClient discovery = new EurekaDiscoveryClient();
        callService(discovery, "order-service");
    }
}
```

How to run: `java SpringCloudK8sLevel1.java`

`callService` depends only on the `DiscoveryClient` interface, never on `EurekaDiscoveryClient` directly — this is the exact same decoupling pattern earlier cards established for Spring Cloud LoadBalancer and Feign, and it's what makes the Kubernetes substitution in the next level possible with zero changes to `callService` itself.

### Level 2 — Intermediate

Swap in a Kubernetes-API-backed implementation of the same interface — `callService` is completely unchanged.

```java
import java.util.*;

public class SpringCloudK8sLevel2 {
    interface DiscoveryClient { List<String> getInstances(String serviceId); }

    static class EurekaDiscoveryClient implements DiscoveryClient {
        public List<String> getInstances(String serviceId) {
            return List.of("10.0.1.5:8080", "10.0.1.6:8080");
        }
    }

    // models Spring Cloud Kubernetes's implementation -- queries the Kubernetes API for Endpoints of a Service
    static class KubernetesDiscoveryClient implements DiscoveryClient {
        public List<String> getInstances(String serviceId) {
            System.out.println("querying Kubernetes API for Endpoints of Service: " + serviceId);
            return List.of("10.244.0.12:8080", "10.244.0.13:8080"); // pod IPs, from the Service's Endpoints object
        }
    }

    // UNCHANGED from Level 1 -- this is the entire point
    static void callService(DiscoveryClient discovery, String serviceId) {
        List<String> instances = discovery.getInstances(serviceId);
        System.out.println("found instances: " + instances);
    }

    public static void main(String[] args) {
        System.out.println("-- via Eureka --");
        callService(new EurekaDiscoveryClient(), "order-service");

        System.out.println("-- via Kubernetes (SAME callService code) --");
        callService(new KubernetesDiscoveryClient(), "order-service");
    }
}
```

How to run: `java SpringCloudK8sLevel2.java`

`callService`'s source code is identical across both calls — only the constructed `DiscoveryClient` implementation differs, exactly mirroring how switching `spring-cloud-starter-netflix-eureka-client` for `spring-cloud-starter-kubernetes-client` in a real application's dependencies changes the discovery backend without requiring any change to code that calls `DiscoveryClient.getInstances(...)`.

### Level 3 — Advanced

Add ConfigMap-backed property resolution alongside Kubernetes-based discovery, showing the combined "configuration plus discovery, both platform-native" value Spring Cloud Kubernetes provides as a coherent whole.

```java
import java.util.*;

public class SpringCloudK8sLevel3 {
    interface DiscoveryClient { List<String> getInstances(String serviceId); }
    interface PropertySource { String getProperty(String key); }

    static class KubernetesDiscoveryClient implements DiscoveryClient {
        public List<String> getInstances(String serviceId) {
            System.out.println("querying Kubernetes API for Endpoints of Service: " + serviceId);
            return List.of("10.244.0.12:8080", "10.244.0.13:8080");
        }
    }

    // models reading a ConfigMap's data as Spring Environment properties
    static class ConfigMapPropertySource implements PropertySource {
        Map<String, String> configMapData;
        ConfigMapPropertySource(Map<String, String> configMapData) { this.configMapData = configMapData; }
        public String getProperty(String key) {
            System.out.println("reading '" + key + "' from ConfigMap-backed PropertySource");
            return configMapData.get(key);
        }
    }

    static void startApplication(DiscoveryClient discovery, PropertySource config) {
        String rateLimit = config.getProperty("app.rate-limit");
        System.out.println("configured rate limit: " + rateLimit);

        List<String> paymentServiceInstances = discovery.getInstances("payment-service");
        System.out.println("discovered payment-service instances: " + paymentServiceInstances);
    }

    public static void main(String[] args) {
        DiscoveryClient discovery = new KubernetesDiscoveryClient();
        PropertySource config = new ConfigMapPropertySource(Map.of("app.rate-limit", "100/min"));

        startApplication(discovery, config); // BOTH config and discovery are Kubernetes-native, unified in one call
    }
}
```

How to run: `java SpringCloudK8sLevel3.java`

`startApplication` reads configuration and performs service discovery through two separate, cleanly-typed interfaces, both of which happen to be backed by Kubernetes-native mechanisms in this run — `startApplication` itself has no Kubernetes-specific code anywhere in it, exactly mirroring how a real Spring Boot application's `@Value`-bound properties and `DiscoveryClient` usage work identically whether backed by Config Server/Eureka or by Spring Cloud Kubernetes's ConfigMap/Kubernetes-API implementations.

## 6. Walkthrough

Trace `startApplication` in Level 3.

1. `startApplication(discovery, config)` is called with a `KubernetesDiscoveryClient` and a `ConfigMapPropertySource`, both already constructed.
2. `config.getProperty("app.rate-limit")` runs — inside `ConfigMapPropertySource.getProperty`, `println` reports the ConfigMap-backed lookup, then `configMapData.get("app.rate-limit")` returns `"100/min"` from the map that was constructed to model a real ConfigMap's `data` section.
3. The `println` in `startApplication` reports `"configured rate limit: 100/min"`.
4. `discovery.getInstances("payment-service")` runs next — inside `KubernetesDiscoveryClient.getInstances`, `println` reports the Kubernetes-API-backed query, then a fixed list of two pod IPs is returned, modeling what a real query against a Kubernetes Service's `Endpoints` object would return: the current set of healthy pod IPs backing that Service.
5. The final `println` reports the discovered instance list — both operations (`config.getProperty` and `discovery.getInstances`) ran through their respective interfaces, and `startApplication`'s own code never distinguished "this is Kubernetes-backed" from any other possible backing implementation; it simply called the interfaces it was given.

```
startApplication(kubernetesDiscovery, configMapConfig):
  config.getProperty("app.rate-limit")     -> ConfigMap lookup -> "100/min"
  discovery.getInstances("payment-service") -> Kubernetes API Endpoints lookup -> [pod-ip-1, pod-ip-2]

startApplication's OWN code: zero Kubernetes-specific logic, purely interface calls
```

## 7. Gotchas & takeaways

> **Gotcha:** Spring Cloud Kubernetes has two client implementation styles — a `fabric8`-based one and a Kubernetes-Java-client-based one (`spring-cloud-starter-kubernetes-client`, shown in this card's dependency) — and mixing dependencies from both, or assuming they're interchangeable in every configuration detail, can produce confusing classpath or behavior issues; picking one consistently for a given application is the safer path, per the current Spring Cloud Kubernetes documentation's guidance.

- Spring Cloud Kubernetes's core value is letting Spring Cloud's own neutral abstractions (`DiscoveryClient`, `Environment`/`PropertySource`) be backed by Kubernetes-native mechanisms instead of standalone infrastructure like Eureka or Config Server, without requiring application code that already targets those abstractions to change.
- This substitution works specifically because well-written Spring Cloud application code was never coupled to Eureka or Config Server directly in the first place — it depended on the neutral interfaces those implementations happened to satisfy, the same decoupling principle covered for LoadBalancer and Feign in earlier cards.
- Migrating an existing Eureka-based application onto Kubernetes with Spring Cloud Kubernetes is primarily a dependency and configuration change, not an application-logic rewrite, provided the application's discovery and configuration code was already written against Spring Cloud's abstractions rather than Eureka-specific types.
- The following cards in this section cover the specific Kubernetes-native mechanisms Spring Cloud Kubernetes builds on — ConfigMap/Secrets as a PropertySource, discovery via the Kubernetes API, native load balancing, config reload on change, and leader election — each one a concrete piece of the overview this card introduces.
