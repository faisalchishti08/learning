---
card: spring-cloud
gi: 4
slug: spring-cloud-commons-shared-abstractions
title: "Spring Cloud Commons (shared abstractions)"
---

## 1. What it is

Spring Cloud Commons defines the shared interfaces — `DiscoveryClient`, `ServiceRegistry`, `LoadBalancerClient` — that every concrete Spring Cloud implementation (Eureka, Consul, Kubernetes, Zookeeper) implements the same way. Application code programs against these Commons interfaces, never against a vendor-specific API directly.

```java
@Autowired DiscoveryClient discoveryClient; // Commons interface

List<ServiceInstance> instances = discoveryClient.getInstances("payment-service");
// Works identically whether the backing registry is Eureka, Consul, or Kubernetes' own DNS-based discovery.
```

## 2. Why & when

Without Commons, switching a discovery backend from Eureka to Consul would mean rewriting every piece of application code that talks to service discovery — different client APIs, different method names, different data shapes. Commons exists specifically to prevent that: application code is written once, against `DiscoveryClient`/`ServiceRegistry`, and the actual registry implementation is swapped by changing a dependency, not by rewriting business logic.

Reach for Spring Cloud Commons' abstractions when:

- Writing application code that needs service discovery or client-side load balancing — always code against `DiscoveryClient`/`LoadBalancerClient`, never a vendor-specific client directly.
- You want the freedom to switch discovery backends later (on-prem Eureka to a cloud provider's native discovery, say) without touching application logic.
- Building a library or shared component meant to work across teams that might each choose a different underlying registry.

## 3. Core concept

```
                    Spring Cloud Commons (interfaces)
                    DiscoveryClient, ServiceRegistry, LoadBalancerClient
                              ^        ^        ^
                              |        |        |
                    EurekaDiscoveryClient  ConsulDiscoveryClient  KubernetesDiscoveryClient
                    (implementation)        (implementation)       (implementation)

 Application code depends ONLY on the interface -- swapping the dependency swaps the implementation,
 with ZERO changes to application code that calls discoveryClient.getInstances(...).
```

Application code is written once against the interface; the concrete registry implementation is a pluggable dependency choice.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code depends on a Commons interface, which three different registry implementations each satisfy">
  <rect x="230" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Application code</text>

  <line x1="320" y1="65" x2="320" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a25)"/>

  <rect x="200" y="100" width="240" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="125" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">DiscoveryClient (interface)</text>

  <line x1="250" y1="140" x2="120" y2="160" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="320" y1="140" x2="320" y2="160" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="390" y1="140" x2="520" y2="160" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>

  <text x="120" y="168" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Eureka</text>
  <text x="320" y="168" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Consul</text>
  <text x="520" y="168" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Kubernetes</text>
</svg>

Application code depends only on the Commons interface; several concrete registries can each implement it interchangeably.

## 5. Runnable example

The scenario: application code discovering and calling a payment service, evolving from code hardcoded against a specific registry's own API, to code written against a shared Commons-style interface, to swapping the concrete implementation without touching a single line of application code — the actual payoff of the abstraction.

### Level 1 — Basic

Show the vendor-locked baseline: application code calling a specific registry's own API directly.

```java
import java.util.*;

public class CommonsLevel1 {
    public static void main(String[] args) {
        EurekaSpecificClient eurekaClient = new EurekaSpecificClient();
        eurekaClient.registerInstance("payment-service", "10.0.1.5:8081");

        // Application code calls EUREKA-SPECIFIC methods directly -- tightly coupled to this one vendor.
        List<String> instances = eurekaClient.lookupEurekaInstances("payment-service");
        System.out.println("Found via Eureka-specific API: " + instances);
    }
}

// A stand-in for a vendor-specific discovery client with its own API shape.
class EurekaSpecificClient {
    private final Map<String, List<String>> registry = new HashMap<>();
    void registerInstance(String serviceId, String address) {
        registry.computeIfAbsent(serviceId, k -> new ArrayList<>()).add(address);
    }
    List<String> lookupEurekaInstances(String serviceId) { return registry.getOrDefault(serviceId, List.of()); }
}
```

How to run: `java CommonsLevel1.java`

Application code calls `lookupEurekaInstances` — a method name and shape specific to this one vendor's client — meaning any switch to a different registry requires rewriting every call site that uses it.

### Level 2 — Intermediate

Add a Commons-style `DiscoveryClient` interface, with a Eureka-flavored implementation behind it — application code now depends only on the interface.

```java
import java.util.*;

public class CommonsLevel2 {
    public static void main(String[] args) {
        DiscoveryClient discoveryClient = new EurekaDiscoveryClient(); // concrete choice made ONCE, here
        discoveryClient.register("payment-service", "10.0.1.5:8081");

        printInstances(discoveryClient); // application code depends ONLY on the interface
    }

    // Application-level function -- knows nothing about Eureka specifically.
    static void printInstances(DiscoveryClient client) {
        System.out.println("Found via Commons interface: " + client.getInstances("payment-service"));
    }
}

// Stands in for org.springframework.cloud.client.discovery.DiscoveryClient.
interface DiscoveryClient {
    void register(String serviceId, String address);
    List<String> getInstances(String serviceId);
}

class EurekaDiscoveryClient implements DiscoveryClient {
    private final Map<String, List<String>> registry = new HashMap<>();
    public void register(String serviceId, String address) {
        registry.computeIfAbsent(serviceId, k -> new ArrayList<>()).add(address);
    }
    public List<String> getInstances(String serviceId) { return registry.getOrDefault(serviceId, List.of()); }
}
```

How to run: `java CommonsLevel2.java`

`printInstances` accepts a `DiscoveryClient` — the Commons interface — and never references `EurekaDiscoveryClient` by name; the concrete implementation choice is made exactly once, at the point where the client object is constructed.

### Level 3 — Advanced

Swap the concrete implementation from Eureka-style to Consul-style, with the *exact same* application code from Level 2 reused unchanged — demonstrating the actual portability payoff.

```java
import java.util.*;

public class CommonsLevel3 {
    public static void main(String[] args) {
        System.out.println("--- Running with Eureka-backed discovery ---");
        runApplication(new EurekaDiscoveryClient());

        System.out.println("--- Running with Consul-backed discovery (SAME application code) ---");
        runApplication(new ConsulDiscoveryClient());
    }

    // The ENTIRE "application" -- identical in both runs, regardless of which DiscoveryClient it's given.
    static void runApplication(DiscoveryClient discoveryClient) {
        discoveryClient.register("payment-service", "10.0.1.5:8081");
        discoveryClient.register("payment-service", "10.0.1.6:8081");
        List<String> instances = discoveryClient.getInstances("payment-service");
        System.out.println("payment-service instances: " + instances);
    }
}

interface DiscoveryClient {
    void register(String serviceId, String address);
    List<String> getInstances(String serviceId);
}

class EurekaDiscoveryClient implements DiscoveryClient {
    private final Map<String, List<String>> registry = new HashMap<>();
    public void register(String serviceId, String address) {
        registry.computeIfAbsent(serviceId, k -> new ArrayList<>()).add(address);
    }
    public List<String> getInstances(String serviceId) { return registry.getOrDefault(serviceId, List.of()); }
}

// A DIFFERENT concrete implementation, internally structured completely differently, but satisfying the SAME interface.
class ConsulDiscoveryClient implements DiscoveryClient {
    private final Map<String, Set<String>> catalog = new TreeMap<>(); // different internal structure entirely
    public void register(String serviceId, String address) {
        catalog.computeIfAbsent(serviceId, k -> new TreeSet<>()).add(address);
    }
    public List<String> getInstances(String serviceId) {
        return new ArrayList<>(catalog.getOrDefault(serviceId, Set.of()));
    }
}
```

How to run: `java CommonsLevel3.java`

`runApplication` is defined exactly once and called with two structurally different `DiscoveryClient` implementations — `EurekaDiscoveryClient` backed by a `HashMap<String, List<String>>`, `ConsulDiscoveryClient` backed by a completely different `TreeMap<String, Set<String>>` — yet `runApplication` itself never changes, because it only ever calls methods declared on the shared `DiscoveryClient` interface.

## 6. Walkthrough

Execution starts in `main` for Level 3. `runApplication` is called twice, once per discovery client implementation.

The first call constructs an `EurekaDiscoveryClient`, registers two addresses for `payment-service`, and retrieves them:

```
--- Running with Eureka-backed discovery ---
payment-service instances: [10.0.1.5:8081, 10.0.1.6:8081]
```

The second call passes a `ConsulDiscoveryClient` instead — internally, this implementation stores data in a sorted `TreeMap`/`TreeSet` rather than a `HashMap`/`ArrayList`, a genuinely different data structure and insertion-order behavior — but `runApplication`'s own code is byte-for-byte identical between the two calls:

```
--- Running with Consul-backed discovery (SAME application code) ---
payment-service instances: [10.0.1.5:8081, 10.0.1.6:8081]
```

In a real Spring Cloud application, this exact substitutability is what happens when a project swaps its `spring-cloud-starter-netflix-eureka-client` dependency for `spring-cloud-starter-consul-discovery` — Spring Boot's autoconfiguration wires up whichever `DiscoveryClient` implementation is on the classpath, and every `@Autowired DiscoveryClient` in the application continues working unchanged, because the application was written against Commons' interface from the start.

## 7. Gotchas & takeaways

> Gotcha: the portability Commons provides only holds if application code consistently avoids importing vendor-specific classes — reaching for a Eureka-specific type "just this once" for a feature the Commons interface doesn't expose reintroduces the exact coupling the abstraction exists to prevent, and often silently, since it usually still compiles and runs fine until someone actually tries to switch registries.

> Gotcha: different registry implementations can have subtly different semantics even behind the same interface — how quickly a newly registered instance becomes visible, how a deregistered instance is detected, whether health checks are active or passive — Commons standardizes the *API shape*, not every operational behavior underneath it.

- Spring Cloud Commons defines the shared interfaces (`DiscoveryClient`, `ServiceRegistry`, `LoadBalancerClient`) that every concrete registry implementation satisfies identically.
- Application code should always be written against these Commons interfaces, never a vendor-specific client API, to preserve the ability to swap the underlying registry later.
- Swapping implementations is a dependency change, not an application code change — Spring Boot's autoconfiguration wires up whichever concrete implementation is on the classpath.
- The abstraction covers API shape, not every operational nuance — different registries can still behave subtly differently underneath the same shared interface.
