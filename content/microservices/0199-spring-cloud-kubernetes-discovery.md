---
card: microservices
gi: 199
slug: spring-cloud-kubernetes-discovery
title: "Spring Cloud Kubernetes discovery"
---

## 1. What it is

Spring Cloud Kubernetes bridges Spring Cloud's common `DiscoveryClient` abstraction to [Kubernetes' native service discovery](0192-discovery-in-container-kubernetes-environments.md) — a Spring application can call the same standard `DiscoveryClient` API it would use with Eureka or Consul, but the actual instance data behind it comes from Kubernetes' own `Endpoints`/`EndpointSlice` objects, requiring no separate registry (no Eureka Server, no Consul cluster) to be deployed at all.

## 2. Why & when

A Spring application written against Eureka's or Consul's specific client library is coupled to that specific registry technology, which becomes awkward when the same application (or the same codebase, reused across environments) needs to run on Kubernetes, where a separate registry is redundant infrastructure duplicating what the platform already provides. Spring Cloud Kubernetes solves this by implementing Spring Cloud's standard `DiscoveryClient` interface on top of the Kubernetes API directly, letting application code written against the generic `DiscoveryClient` abstraction work unmodified whether the underlying platform is Eureka, Consul, or Kubernetes itself.

Use Spring Cloud Kubernetes when a Spring application is deployed on Kubernetes and needs to perform discovery through the standard Spring Cloud `DiscoveryClient` API (perhaps because the same codebase also needs to run against Eureka or Consul in a different environment), rather than relying purely on Kubernetes' own DNS-based service resolution directly. If application code has no need for the `DiscoveryClient` abstraction specifically and can rely on Kubernetes' native DNS resolution alone, this integration may be unnecessary overhead.

## 3. Core concept

Spring Cloud Kubernetes implements the `DiscoveryClient` interface by querying the Kubernetes API server for `Endpoints` matching a requested service name, translating Kubernetes' native Pod/Service model into the same `ServiceInstance` objects a Eureka- or Consul-backed `DiscoveryClient` would return — application code calling `discoveryClient.getInstances("order-service")` is unaware of which underlying platform actually answered the query.

```java
@Autowired DiscoveryClient discoveryClient; // the SAME standard interface, regardless of backend

List<ServiceInstance> instances = discoveryClient.getInstances("order-service");
// on Eureka: queried FROM Eureka Server
// on Consul: queried FROM Consul
// on Kubernetes (Spring Cloud Kubernetes): queried FROM the Kubernetes API, translating Endpoints -> ServiceInstance
// the CALLING CODE is IDENTICAL in all three cases
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code calls the standard DiscoveryClient interface; Spring Cloud Kubernetes implements that interface by querying the Kubernetes API server's Endpoints data and translating it into ServiceInstance objects, requiring no separate registry deployment" >
  <rect x="20" y="70" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">DiscoveryClient</text>

  <rect x="240" y="60" width="180" height="65" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring Cloud Kubernetes</text>
  <text x="330" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">translates Endpoints -&gt;</text>
  <text x="330" y="111" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">ServiceInstance</text>

  <rect x="470" y="70" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Kubernetes API</text>

  <line x1="170" y1="92" x2="238" y2="92" stroke="#8b949e" marker-end="url(#arr80)"/>
  <line x1="420" y1="92" x2="468" y2="92" stroke="#8b949e" marker-end="url(#arr80)"/>

  <defs>
    <marker id="arr80" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Application code never touches the Kubernetes-specific API directly; the standard interface hides that translation entirely.

## 5. Runnable example

Scenario: an order-consuming service that starts calling a Eureka-specific client API directly (showing the coupling this abstraction avoids), refactors to the standard `DiscoveryClient` interface backed by a simulated Kubernetes-querying implementation, and finally demonstrates the same application code working unmodified against two different simulated backend implementations, proving the abstraction genuinely decouples application logic from the specific discovery technology.

### Level 1 — Basic

```java
// File: EurekaSpecificClientCoupling.java -- application code calls a EUREKA-
// SPECIFIC client directly; porting this to Kubernetes means REWRITING this code.
import java.util.*;

public class EurekaSpecificClientCoupling {
    static class EurekaClient { // a SPECIFIC, non-portable client type
        List<String> getApplicationInstances(String appName) { return List.of("10.0.1.5:8080", "10.0.1.6:8080"); }
    }

    static class ShippingServiceCaller {
        EurekaClient eurekaClient; // COUPLED to Eureka specifically
        ShippingServiceCaller(EurekaClient eurekaClient) { this.eurekaClient = eurekaClient; }
        List<String> findOrderServiceInstances() { return eurekaClient.getApplicationInstances("order-service"); } // Eureka-SPECIFIC method name
    }

    public static void main(String[] args) {
        ShippingServiceCaller caller = new ShippingServiceCaller(new EurekaClient());
        System.out.println(caller.findOrderServiceInstances());
        System.out.println("This code is COUPLED to EurekaClient's specific API -- deploying on Kubernetes instead would require REWRITING it.");
    }
}
```

**How to run:** `javac EurekaSpecificClientCoupling.java && java EurekaSpecificClientCoupling` (JDK 17+).

### Level 2 — Intermediate

```java
// File: StandardDiscoveryClientAbstraction.java -- application code depends on
// the STANDARD abstraction; the Kubernetes-specific translation happens BEHIND it.
import java.util.*;
import java.util.function.*;

public class StandardDiscoveryClientAbstraction {
    record ServiceInstance(String host, int port) {}

    interface DiscoveryClient { List<ServiceInstance> getInstances(String serviceName); } // the PORTABLE, standard interface

    // simulates Spring Cloud Kubernetes' implementation of DiscoveryClient
    static class KubernetesDiscoveryClient implements DiscoveryClient {
        record K8sEndpoint(String ip, int port) {}
        Map<String, List<K8sEndpoint>> simulatedKubernetesApi = Map.of(
            "order-service", List.of(new K8sEndpoint("10.0.1.5", 8080), new K8sEndpoint("10.0.1.6", 8080)));

        public List<ServiceInstance> getInstances(String serviceName) {
            System.out.println("  [Spring Cloud Kubernetes] querying Kubernetes API for Endpoints of '" + serviceName + "'");
            return simulatedKubernetesApi.getOrDefault(serviceName, List.of()).stream()
                .map(ep -> new ServiceInstance(ep.ip(), ep.port())) // TRANSLATION: Endpoint -> ServiceInstance
                .toList();
        }
    }

    static class ShippingServiceCaller {
        DiscoveryClient discoveryClient; // the STANDARD interface -- NOT coupled to Kubernetes specifically
        ShippingServiceCaller(DiscoveryClient discoveryClient) { this.discoveryClient = discoveryClient; }
        List<ServiceInstance> findOrderServiceInstances() { return discoveryClient.getInstances("order-service"); } // STANDARD method name
    }

    public static void main(String[] args) {
        ShippingServiceCaller caller = new ShippingServiceCaller(new KubernetesDiscoveryClient());
        System.out.println(caller.findOrderServiceInstances());
        System.out.println("ShippingServiceCaller's code depends ONLY on the standard DiscoveryClient interface -- NOT on anything Kubernetes-specific.");
    }
}
```

**How to run:** `javac StandardDiscoveryClientAbstraction.java && java StandardDiscoveryClientAbstraction` (JDK 17+).

Expected output:
```
  [Spring Cloud Kubernetes] querying Kubernetes API for Endpoints of 'order-service'
[ServiceInstance[host=10.0.1.5, port=8080], ServiceInstance[host=10.0.1.6, port=8080]]
ShippingServiceCaller's code depends ONLY on the standard DiscoveryClient interface -- NOT on anything Kubernetes-specific.
```

### Level 3 — Advanced

```java
// File: SameCodeTwoBackends.java -- the IDENTICAL ShippingServiceCaller code
// works UNCHANGED against BOTH a Kubernetes-backed AND a Eureka-backed
// DiscoveryClient implementation -- proving GENUINE portability.
import java.util.*;

public class SameCodeTwoBackends {
    record ServiceInstance(String host, int port) {}
    interface DiscoveryClient { List<ServiceInstance> getInstances(String serviceName); }

    static class KubernetesDiscoveryClient implements DiscoveryClient {
        public List<ServiceInstance> getInstances(String serviceName) {
            System.out.println("  [backend: Kubernetes] querying via Kubernetes API");
            return List.of(new ServiceInstance("10.0.1.5", 8080), new ServiceInstance("10.0.1.6", 8080));
        }
    }
    static class EurekaDiscoveryClient implements DiscoveryClient {
        public List<ServiceInstance> getInstances(String serviceName) {
            System.out.println("  [backend: Eureka] querying via Eureka's REST API");
            return List.of(new ServiceInstance("10.0.1.5", 8080), new ServiceInstance("10.0.1.6", 8080), new ServiceInstance("10.0.1.7", 8080));
        }
    }

    // this class is IDENTICAL to StandardDiscoveryClientAbstraction's version -- UNCHANGED, reused verbatim
    static class ShippingServiceCaller {
        DiscoveryClient discoveryClient;
        ShippingServiceCaller(DiscoveryClient discoveryClient) { this.discoveryClient = discoveryClient; }
        List<ServiceInstance> findOrderServiceInstances() { return discoveryClient.getInstances("order-service"); }
    }

    public static void main(String[] args) {
        System.out.println("=== running in a Kubernetes environment ===");
        ShippingServiceCaller onK8s = new ShippingServiceCaller(new KubernetesDiscoveryClient());
        System.out.println(onK8s.findOrderServiceInstances());

        System.out.println("\n=== running in a Eureka environment ===");
        ShippingServiceCaller onEureka = new ShippingServiceCaller(new EurekaDiscoveryClient());
        System.out.println(onEureka.findOrderServiceInstances());

        System.out.println("\nShippingServiceCaller.java's SOURCE CODE never changed between these two environments -- ONLY the injected DiscoveryClient implementation did.");
    }
}
```

**How to run:** `javac SameCodeTwoBackends.java && java SameCodeTwoBackends` (JDK 17+).

Expected output:
```
=== running in a Kubernetes environment ===
  [backend: Kubernetes] querying via Kubernetes API
[ServiceInstance[host=10.0.1.5, port=8080], ServiceInstance[host=10.0.1.6, port=8080]]

=== running in a Eureka environment ===
  [backend: Eureka] querying via Eureka's REST API
[ServiceInstance[host=10.0.1.5, port=8080], ServiceInstance[host=10.0.1.6, port=8080], ServiceInstance[host=10.0.1.7, port=8080]]

ShippingServiceCaller.java's SOURCE CODE never changed between these two environments -- ONLY the injected DiscoveryClient implementation did.
```

## 6. Walkthrough

1. **Level 1** — `ShippingServiceCaller.findOrderServiceInstances` calls `eurekaClient.getApplicationInstances(...)`, a method name and type specific to `EurekaClient`; moving this application to Kubernetes would require finding and rewriting every place this specific method is called.
2. **Level 2, the standard interface as the caller's only dependency** — `ShippingServiceCaller` now holds a `DiscoveryClient discoveryClient` field, an interface type, and calls only `discoveryClient.getInstances("order-service")`, a method defined generically, not tied to any specific registry technology.
3. **Level 2, the Kubernetes-specific translation isolated** — `KubernetesDiscoveryClient.getInstances` is the *only* place in this program that references `simulatedKubernetesApi` (standing in for actual Kubernetes API calls) and performs the translation from `K8sEndpoint` to the generic `ServiceInstance` shape — this translation logic is entirely contained within the implementation, invisible to `ShippingServiceCaller`.
4. **Level 2, the caller's genuine ignorance of the backend** — nothing in `ShippingServiceCaller`'s class definition mentions Kubernetes, `K8sEndpoint`, or any Kubernetes-specific concept at all — it only knows about the `DiscoveryClient` interface and the generic `ServiceInstance` type.
5. **Level 3, two separate `DiscoveryClient` implementations** — `KubernetesDiscoveryClient` and `EurekaDiscoveryClient` each implement the identical `DiscoveryClient` interface but with entirely different internal logic and even different simulated results (three instances from Eureka versus two from Kubernetes, modeling that the two backends might genuinely have different registration data at any given moment).
6. **Level 3, one caller class, reused verbatim** — the code comment explicitly notes that `ShippingServiceCaller` in this file is unchanged from Level 2's version; `main` constructs two separate `ShippingServiceCaller` instances, each injected with a different `DiscoveryClient` implementation, but neither construction required any change to `ShippingServiceCaller`'s own source code.
7. **Level 3, the concrete proof of portability** — both `onK8s.findOrderServiceInstances()` and `onEureka.findOrderServiceInstances()` successfully return correctly-shaped `ServiceInstance` lists, each reflecting their respective backend's actual data, using the identical calling code — this is the concrete payoff Spring Cloud Kubernetes (and Spring Cloud's `DiscoveryClient` abstraction more broadly) provides: application logic written once against the standard interface genuinely works unmodified across fundamentally different discovery backends, whether that's Eureka, Consul, or Kubernetes' own native API.

## 7. Gotchas & takeaways

> **Gotcha:** the `DiscoveryClient` abstraction covers the common-denominator operations (list instances, get instance metadata) well, but Kubernetes-specific concepts that don't map cleanly onto other registries' models (namespaces, specific label-selector syntax, Kubernetes-specific annotations) may require dropping down to Spring Cloud Kubernetes' own Kubernetes-specific APIs when genuinely needed — the portability the standard abstraction provides is real but not unlimited, mirroring the same trade-off any generic abstraction over multiple underlying implementations makes.

- Spring Cloud Kubernetes implements Spring Cloud's standard `DiscoveryClient` interface using Kubernetes' native `Endpoints`/`EndpointSlice` data as the underlying source, requiring no separate registry deployment.
- Application code written against the standard `DiscoveryClient` interface works unmodified regardless of whether the underlying discovery backend is Eureka, Consul, or Kubernetes itself.
- This decouples application logic from any specific registry technology, letting the same codebase run correctly across environments using genuinely different discovery infrastructure.
- The abstraction's translation work (converting a specific backend's native data shape into the generic `ServiceInstance` type) is entirely contained within each backend's `DiscoveryClient` implementation, invisible to application code.
- The standard abstraction covers common discovery operations well but may not expose every Kubernetes-specific capability (namespaces, custom label selectors) — genuinely Kubernetes-specific needs may require using Spring Cloud Kubernetes' own specific APIs directly rather than the generic abstraction alone.
