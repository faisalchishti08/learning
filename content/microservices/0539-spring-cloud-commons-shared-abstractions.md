---
card: microservices
gi: 539
slug: spring-cloud-commons-shared-abstractions
title: "Spring Cloud Commons (shared abstractions)"
---

## 1. What it is

**Spring Cloud Commons** is the foundational sub-project that defines the common interfaces (`DiscoveryClient`, `ServiceInstance`, `LoadBalancerClient`) implemented by every concrete Spring Cloud discovery and load-balancing integration (Eureka, Consul, Kubernetes, ZooKeeper). It's the shared vocabulary that lets application code depend on "a discovery client" and "a load balancer" abstractly, so swapping the underlying discovery mechanism — say, from Eureka to Kubernetes' native service discovery — requires only a dependency and configuration change, never a change to the business code that calls `discoveryClient.getInstances("order-service")`.

## 2. Why & when

You benefit from Spring Cloud Commons's abstraction layer specifically because it decouples application code from any one specific discovery or load-balancing technology:

- **Without a shared interface, switching discovery mechanisms would mean rewriting application code.** If your code called Eureka's specific client API directly, moving to Kubernetes-native discovery later would require touching every place that API was used; against the `DiscoveryClient` interface, only the underlying implementation bean changes.
- **`ServiceInstance` is a common representation of "a running instance of a service"** — host, port, metadata — regardless of whether that instance's existence was learned from Eureka, Consul, or Kubernetes' own API; code working with `ServiceInstance` objects doesn't need to know or care which one supplied them.
- **`LoadBalancerClient` (implemented concretely by [Spring Cloud LoadBalancer](0544-spring-cloud-loadbalancer-client-side-lb.md)) is the common interface for choosing one instance among several** — again, application code depends on the abstraction, and the actual load-balancing algorithm or instance source is a pluggable implementation detail.
- **You benefit from this layer any time there's a realistic chance your discovery mechanism might change**, or when you're writing a library or shared internal tool meant to work across teams that might use different concrete discovery backends — coding directly against a specific vendor's API forecloses that flexibility from the start.

## 3. Core concept

Think of a universal remote control's standardized button layout (power, volume, channel) that works across many different brands of TV, versus a remote hardwired to one specific TV model's proprietary infrared codes. The universal remote's buttons are the shared abstraction — pressing "volume up" always means the same thing to whoever's holding it, regardless of which actual TV brand is plugged in behind the scenes; only the remote's internal translation to brand-specific signals differs per TV. Spring Cloud Commons's interfaces play exactly this role: application code presses the same abstract "buttons" (`getInstances`, `choose`), and the concrete discovery/load-balancing implementation underneath translates that into whatever protocol Eureka, Consul, or Kubernetes actually speaks.

Concretely:

1. **`DiscoveryClient.getInstances(serviceId)`** returns a `List<ServiceInstance>` for a named logical service — the calling code has no idea whether this list came from querying Eureka's registry, Consul's catalog, or Kubernetes' Endpoints API.
2. **`ServiceInstance`** exposes common fields (`getHost()`, `getPort()`, `getMetadata()`) that every concrete discovery integration populates from its own native representation, giving calling code one consistent shape to work with regardless of source.
3. **`@LoadBalanced` on a `RestTemplate` or `WebClient.Builder` bean** activates Spring Cloud LoadBalancer's interception, so a call using a logical service name (`http://order-service/orders/42`) is automatically resolved to a specific instance's real host and port at call time, via the same `DiscoveryClient` abstraction underneath.
4. **Swapping the concrete implementation is a dependency and configuration change**: replacing `spring-cloud-starter-netflix-eureka-client` with `spring-cloud-starter-kubernetes-client-discovery` (for example) changes which `DiscoveryClient` bean gets registered, with zero changes required to any code that only depends on the `DiscoveryClient`/`ServiceInstance` interfaces.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code depends only on the DiscoveryClient interface; concrete implementations for Eureka, Consul, or Kubernetes plug in underneath without changing any calling code">
  <rect x="230" y="20" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Application code: DiscoveryClient</text>

  <line x1="290" y1="60" x2="130" y2="110" stroke="#8b949e"/>
  <line x1="330" y1="60" x2="330" y2="110" stroke="#8b949e"/>
  <line x1="370" y1="60" x2="530" y2="110" stroke="#8b949e"/>

  <rect x="40" y="110" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Eureka implementation</text>
  <rect x="240" y="110" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Consul implementation</text>
  <rect x="440" y="110" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Kubernetes implementation</text>
</svg>

Application code depends only on the shared interface; the concrete discovery backend is a swappable implementation detail underneath.

## 5. Runnable example

Scenario: resolving a service's instances through an abstract interface. We start with a plain Java model of the abstraction gap without it, extend it to an interface-based version with two swappable implementations, then handle the real Spring Cloud Commons shape with `@LoadBalanced`.

### Level 1 — Basic

```java
// File: DirectVendorCoupling.java -- calling a SPECIFIC discovery
// vendor's API directly -- switching vendors later means rewriting this code.
import java.util.*;

public class DirectVendorCoupling {
    // imagine this is Eureka's actual client API, called directly
    static List<String> eurekaGetInstances(String serviceId) {
        return List.of("10.0.5.2:8080", "10.0.5.9:8080");
    }

    public static void main(String[] args) {
        List<String> instances = eurekaGetInstances("order-service"); // hardcoded to Eureka's specific API shape
        System.out.println("Instances (via Eureka-specific call): " + instances);
        System.out.println("Problem: switching to Consul or Kubernetes means rewriting every call site like this one.");
    }
}
```

How to run: `java DirectVendorCoupling.java`

`eurekaGetInstances` represents calling a specific vendor's discovery API directly — every place in the codebase that needs service instances would need to call this exact method, tying the entire codebase to Eureka specifically.

### Level 2 — Intermediate

```java
// File: AbstractDiscoveryClient.java -- introduces a SHARED interface;
// application code depends on the INTERFACE, not any specific vendor.
import java.util.*;

public class AbstractDiscoveryClient {
    interface DiscoveryClient { List<String> getInstances(String serviceId); }

    static class EurekaDiscoveryClient implements DiscoveryClient {
        public List<String> getInstances(String serviceId) { return List.of("10.0.5.2:8080", "10.0.5.9:8080"); }
    }
    static class ConsulDiscoveryClient implements DiscoveryClient {
        public List<String> getInstances(String serviceId) { return List.of("10.0.6.3:9090"); }
    }

    // application code depends ONLY on the interface
    static void printInstances(DiscoveryClient client, String serviceId) {
        System.out.println("Instances for " + serviceId + " (via " + client.getClass().getSimpleName() + "): " + client.getInstances(serviceId));
    }

    public static void main(String[] args) {
        printInstances(new EurekaDiscoveryClient(), "order-service");
        printInstances(new ConsulDiscoveryClient(), "order-service"); // SAME calling code, different backend swapped in
    }
}
```

How to run: `java AbstractDiscoveryClient.java`

`printInstances` depends only on the `DiscoveryClient` interface — swapping `EurekaDiscoveryClient` for `ConsulDiscoveryClient` requires zero changes to `printInstances` itself, exactly mirroring how Spring Cloud Commons lets you swap discovery backends without touching business code.

### Level 3 — Advanced

```java
// File: SpringCloudCommonsRealShape.java -- the REAL Spring Cloud Commons
// shape: @LoadBalanced RestTemplate resolving a LOGICAL service name to a
// real instance automatically, via the DiscoveryClient abstraction underneath.
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;

public class SpringCloudCommonsRealShape {

    @Configuration
    static class RestTemplateConfig {
        @Bean
        @LoadBalanced // activates load-balanced, service-name-based resolution
        public RestTemplate restTemplate() { return new RestTemplate(); }
    }

    @Service
    static class OrderClient {
        private final RestTemplate restTemplate;
        private final DiscoveryClient discoveryClient; // the SHARED abstraction, regardless of backend

        OrderClient(RestTemplate restTemplate, DiscoveryClient discoveryClient) {
            this.restTemplate = restTemplate;
            this.discoveryClient = discoveryClient;
        }

        void logAvailableInstances() {
            List<ServiceInstance> instances = discoveryClient.getInstances("order-service");
            instances.forEach(i -> System.out.println("Discovered instance: " + i.getHost() + ":" + i.getPort()));
        }

        String fetchOrder(String orderId) {
            // "order-service" is a LOGICAL name -- resolved to a real instance by LoadBalancerClient underneath
            return restTemplate.getForObject("http://order-service/orders/" + orderId, String.class);
        }
    }
}
```

How to run: requires `spring-cloud-starter-loadbalancer` plus a concrete discovery starter (`spring-cloud-starter-netflix-eureka-client`, `spring-cloud-starter-consul-discovery`, or a Kubernetes equivalent) on the classpath; run in a Spring Boot application registered with the corresponding discovery backend, and observe `fetchOrder` correctly reaching a real instance regardless of which discovery starter is configured.

`OrderClient` depends on `DiscoveryClient` and calls `restTemplate.getForObject("http://order-service/...")` using a logical name, not a real address — neither line of code changes at all whether the actual discovery backend is Eureka, Consul, or Kubernetes; only the dependency added to the build and the corresponding configuration properties differ.

## 6. Walkthrough

Trace `fetchOrder("42")` end to end, assuming a Eureka-backed discovery configuration is active:

1. **`restTemplate.getForObject("http://order-service/orders/42", String.class)` is called.** Because this `RestTemplate` bean is annotated `@LoadBalanced`, Spring Cloud LoadBalancer's interceptor recognizes `order-service` as a logical service name rather than a real hostname.
2. **The interceptor calls into the `LoadBalancerClient`**, which in turn queries the active `DiscoveryClient` implementation — here, the Eureka-backed one — for `getInstances("order-service")`.
3. **The Eureka `DiscoveryClient` implementation queries the Eureka registry** (over the network, behind the scenes) and returns a `List<ServiceInstance>` — say, two instances at `10.0.5.2:8080` and `10.0.5.9:8080` — translated from Eureka's own internal registry format into the common `ServiceInstance` shape.
4. **The `LoadBalancerClient` selects one instance from that list** (via round-robin or another configured strategy) — say, `10.0.5.2:8080`.
5. **The original request URL is rewritten from the logical `http://order-service/orders/42` to the concrete `http://10.0.5.2:8080/orders/42`**, and *that* concrete request is what's actually sent over the network.
6. **The response comes back from the real instance and is returned to `fetchOrder`'s caller** — completely transparently; nothing in `OrderClient`'s code ever referenced `10.0.5.2` directly.

If this same code ran against a Consul-backed discovery configuration instead, steps 1, 4, 5, and 6 would be identical — only step 3 would differ, querying Consul's catalog instead of Eureka's registry, translated into the same common `ServiceInstance` shape either way.

## 7. Gotchas & takeaways

> **Gotcha:** `@LoadBalanced` only activates logical-name resolution for the specific `RestTemplate`/`WebClient.Builder` bean it's applied to — a plain, un-annotated `RestTemplate` bean elsewhere in the same application will treat `http://order-service/...` as a literal (and non-existent) hostname and fail with a DNS resolution error, a subtle and easy-to-miss configuration mistake.

- Spring Cloud Commons's `DiscoveryClient`/`ServiceInstance`/`LoadBalancerClient` interfaces are what let application code stay decoupled from any one specific discovery or load-balancing vendor.
- Swapping discovery backends (Eureka to Consul to Kubernetes) is a dependency and configuration change, not a code change, as long as application code depends only on these shared interfaces rather than a vendor-specific API directly.
- `@LoadBalanced` is the marker that activates logical-service-name resolution for a specific `RestTemplate`/`WebClient.Builder` bean — it must be applied explicitly per bean, not assumed to apply globally.
- Writing shared internal libraries or tools against these common interfaces, rather than a specific vendor's API, keeps them usable across teams that might have chosen different concrete discovery backends.
