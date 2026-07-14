---
card: microservices
gi: 474
slug: spring-cloud-kubernetes-integration
title: "Spring Cloud Kubernetes integration"
---

## 1. What it is

**Spring Cloud Kubernetes** lets a Spring Boot application use Kubernetes' own native primitives — its Service discovery, ConfigMaps, and Secrets — through familiar Spring Cloud abstractions (`DiscoveryClient`, `@ConfigurationProperties`-backed config sources), instead of requiring a separate service registry like Eureka or Consul. When your deployment platform *is* Kubernetes, this integration lets Spring lean on what the platform already provides rather than running a redundant, parallel system for the same job.

## 2. Why & when

You adopt Spring Cloud Kubernetes specifically when Kubernetes is your deployment target, because it's wasteful to run a separate service registry when the orchestrator you're already using does that job natively:

- **Kubernetes already tracks which Pods back which Service, and already load-balances between them.** Running a separate Eureka cluster on top of Kubernetes duplicates that exact capability — Spring Cloud Kubernetes lets your application query Kubernetes' own Service/Endpoints objects directly through the standard `DiscoveryClient` interface instead.
- **ConfigMaps and Secrets are already Kubernetes' native configuration mechanism.** Rather than maintaining a separate Spring Cloud Config Server, this integration lets a ConfigMap or Secret populate your application's Spring `Environment` directly, refreshed automatically when the underlying Kubernetes object changes.
- **Fewer moving parts means fewer things that can fail or drift out of sync.** A service registry that has to stay consistent with Kubernetes' own view of Pod health is one more system that can disagree with reality; querying Kubernetes directly removes that whole class of consistency problem.
- **You reach for this specifically when Kubernetes is the deployment platform** — for services deployed outside Kubernetes (bare VMs, a different orchestrator), a platform-agnostic registry like Eureka remains the right tool, since there's no native Kubernetes API to lean on there.

## 3. Core concept

Think of it like using a building's own directory board in the lobby to find which floor a company is on, rather than maintaining a separate, hand-updated spreadsheet that tries to track the same information — the lobby directory is already authoritative and always current, because it's literally generated from the building's own occupancy records; a parallel spreadsheet is redundant effort that can drift out of date.

Concretely:

1. **Service discovery**: Spring Cloud Kubernetes's `DiscoveryClient` implementation queries the Kubernetes API for Service and Endpoints objects matching a service name, returning the actual current set of healthy Pod IPs backing that Service — the same information Kubernetes itself uses for its own internal load balancing.
2. **Configuration**: A `ConfigMap` (for non-sensitive config) or `Secret` (for sensitive values) can be mounted as Spring `PropertySource`s, populating `@Value` or `@ConfigurationProperties`-bound fields exactly like a properties file would, but sourced from Kubernetes objects instead.
3. **Reactive config reload**: Some setups can watch a ConfigMap for changes and refresh the application's configuration at runtime without a restart, when paired with Spring Cloud's `@RefreshScope` mechanism.
4. **No separate registry infrastructure to run or maintain** — the "registry" is simply the Kubernetes control plane that's already running as part of the cluster, which every Pod already has API access to.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Spring Boot application queries the Kubernetes API directly for service discovery and configuration, instead of running a separate Eureka or Config Server">
  <rect x="20" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">order-service Pod</text>
  <text x="110" y="112" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">DiscoveryClient</text>

  <rect x="250" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Kubernetes API</text>
  <text x="340" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Services, Endpoints, ConfigMaps</text>

  <rect x="460" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="540" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">inventory-service Pods</text>
  <text x="540" y="112" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">actual healthy instances</text>

  <line x1="200" y1="100" x2="250" y2="100" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="430" y1="100" x2="460" y2="100" stroke="#8b949e" marker-end="url(#a1)"/>

  <text x="330" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no separate registry to run -- Kubernetes' own API is queried directly, using the standard DiscoveryClient interface</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The application's `DiscoveryClient` queries the Kubernetes API directly for a target Service's healthy backing Pods.

## 5. Runnable example

We can't call a real Kubernetes API from a plain Java file, but the interface-level behavior Spring Cloud Kubernetes provides — a standard `DiscoveryClient` returning Kubernetes-sourced instances instead of Eureka-sourced ones — is directly demonstrable by simulating the Kubernetes API layer. We start with a basic discovery lookup, extend it to configuration sourced from a simulated ConfigMap, then handle the hard case: a Pod that Kubernetes' Endpoints object reports as unready, which must be excluded from discovery results even though its container is technically running.

### Level 1 — Basic

```java
// File: K8sDiscoveryBasic.java -- models a DiscoveryClient querying a
// simulated Kubernetes API for a service's backing Pod IPs, the SAME
// interface a real application would use, sourced from Kubernetes instead
// of a separate registry like Eureka.
import java.util.*;

public class K8sDiscoveryBasic {
    // Simulates the Kubernetes API's Endpoints object for a given Service name.
    static Map<String, List<String>> kubernetesEndpoints = Map.of(
        "inventory-service", List.of("10.0.1.5", "10.0.1.9", "10.0.1.14")
    );

    interface DiscoveryClient {
        List<String> getInstances(String serviceName);
    }

    static class KubernetesDiscoveryClient implements DiscoveryClient {
        public List<String> getInstances(String serviceName) {
            System.out.println("[discovery] querying Kubernetes API for Service: " + serviceName);
            return kubernetesEndpoints.getOrDefault(serviceName, List.of());
        }
    }

    public static void main(String[] args) {
        DiscoveryClient discoveryClient = new KubernetesDiscoveryClient();
        List<String> instances = discoveryClient.getInstances("inventory-service");
        System.out.println("[order-service] discovered instances: " + instances);
    }
}
```

How to run: `java K8sDiscoveryBasic.java`

`KubernetesDiscoveryClient` implements the same `DiscoveryClient` interface any Spring Cloud discovery mechanism would, but its `getInstances` method reads from `kubernetesEndpoints` — standing in for Kubernetes' own Endpoints API — rather than from a separately-maintained registry, meaning application code calling `discoveryClient.getInstances(...)` doesn't need to know or care which backing mechanism is actually in use.

### Level 2 — Intermediate

```java
// File: K8sConfigMapBasic.java -- the SAME discovery mechanism, now
// EXTENDED with configuration sourced from a simulated ConfigMap, exactly
// like Spring Cloud Kubernetes populating a Spring Environment from a
// real Kubernetes ConfigMap object.
import java.util.*;

public class K8sConfigMapBasic {
    // Simulates a Kubernetes ConfigMap's key-value data.
    static Map<String, String> configMapData = Map.of(
        "inventory.cache.ttl-seconds", "300",
        "inventory.max-retries", "3"
    );

    static Map<String, List<String>> kubernetesEndpoints = Map.of(
        "inventory-service", List.of("10.0.1.5", "10.0.1.9", "10.0.1.14")
    );

    static class Environment {
        Map<String, String> properties = new HashMap<>();
        void loadFromConfigMap(Map<String, String> configMap) {
            properties.putAll(configMap);
            System.out.println("[environment] loaded " + configMap.size() + " properties from ConfigMap");
        }
        String get(String key) { return properties.get(key); }
    }

    public static void main(String[] args) {
        Environment env = new Environment();
        env.loadFromConfigMap(configMapData);

        int cacheTtl = Integer.parseInt(env.get("inventory.cache.ttl-seconds"));
        int maxRetries = Integer.parseInt(env.get("inventory.max-retries"));
        System.out.println("[app] configured cache TTL: " + cacheTtl + "s, max retries: " + maxRetries);

        List<String> instances = kubernetesEndpoints.get("inventory-service");
        System.out.println("[app] discovered instances: " + instances);
    }
}
```

How to run: `java K8sConfigMapBasic.java`

`Environment.loadFromConfigMap` copies every key from `configMapData` directly into the application's own property map, exactly like Spring's `PropertySource` mechanism pulling values from a real Kubernetes ConfigMap — `cacheTtl` and `maxRetries` are then read out through ordinary `env.get(...)` calls, with the application code never needing to know its configuration came from a Kubernetes object rather than a local `application.properties` file.

### Level 3 — Advanced

```java
// File: K8sDiscoveryReadinessFilter.java -- the SAME discovery client, now
// handling the PRODUCTION-FLAVORED hard case: Kubernetes' real Endpoints
// object tracks READY and NOT-READY addresses SEPARATELY (a Pod whose
// container is running but whose READINESS PROBE is failing shows up as
// a "not ready" address, not a normal one). Discovery must return ONLY
// ready addresses -- returning a not-ready Pod's IP would route traffic
// to an instance that just told Kubernetes it can't handle it.
import java.util.*;

public class K8sDiscoveryReadinessFilter {
    record EndpointAddress(String ip, boolean ready) {}

    // Simulates a real Kubernetes Endpoints object: some addresses ready, one not.
    static Map<String, List<EndpointAddress>> kubernetesEndpoints = Map.of(
        "inventory-service", List.of(
            new EndpointAddress("10.0.1.5", true),
            new EndpointAddress("10.0.1.9", false), // failing its readiness probe right now
            new EndpointAddress("10.0.1.14", true)
        )
    );

    interface DiscoveryClient {
        List<String> getInstances(String serviceName);
    }

    static class KubernetesDiscoveryClient implements DiscoveryClient {
        public List<String> getInstances(String serviceName) {
            List<EndpointAddress> allAddresses = kubernetesEndpoints.getOrDefault(serviceName, List.of());
            List<String> readyOnly = new ArrayList<>();
            for (EndpointAddress addr : allAddresses) {
                if (addr.ready()) {
                    readyOnly.add(addr.ip());
                } else {
                    System.out.println("[discovery] excluding " + addr.ip() + " -- NOT READY (failing readiness probe)");
                }
            }
            return readyOnly;
        }
    }

    public static void main(String[] args) {
        DiscoveryClient discoveryClient = new KubernetesDiscoveryClient();
        List<String> instances = discoveryClient.getInstances("inventory-service");
        System.out.println("[order-service] routable instances: " + instances);
        System.out.println("[order-service] note: 10.0.1.9's container is still RUNNING, just excluded from traffic");
    }
}
```

How to run: `java K8sDiscoveryReadinessFilter.java`

`EndpointAddress` carries a `ready` flag alongside each IP, modeling Kubernetes' real Endpoints object structure, which separates ready and not-ready addresses explicitly. `getInstances` loops over every address but only adds `ready()` ones to `readyOnly`, printing an explicit exclusion message for `10.0.1.9` — the returned list never includes a not-ready address, exactly like Spring Cloud Kubernetes' real discovery client filtering out Pods whose [readiness probe](0473-spring-boot-actuator-liveness-readiness-probes-for-kubernete.md) is currently failing.

## 6. Walkthrough

Trace `K8sDiscoveryReadinessFilter.main` in order. **First**, `discoveryClient.getInstances("inventory-service")` is called, and inside it, `allAddresses` is populated from `kubernetesEndpoints`, containing three `EndpointAddress` records — two `ready = true`, one `ready = false`.

**Next**, the loop processes the first address, `10.0.1.5` with `ready = true`. The `if (addr.ready())` check passes, so `readyOnly.add("10.0.1.5")` runs, and no exclusion message is printed for it.

**Then**, the loop reaches `10.0.1.9` with `ready = false`. The `if` check fails, so the `else` branch runs instead: it prints the exclusion message naming this specific IP and the reason, and critically, `readyOnly.add(...)` is never called for this address — it simply never enters the returned list.

**After that**, the loop processes `10.0.1.14` with `ready = true`, identical to the first address: it's added to `readyOnly` with no exclusion message.

**Finally**, `getInstances` returns `readyOnly`, which contains exactly `["10.0.1.5", "10.0.1.14"]` — `main` prints this as the routable instance list and adds a clarifying note that `10.0.1.9`'s container is still running, it's simply excluded from the traffic-eligible set, exactly mirroring how a real not-ready Kubernetes Pod stays alive and consuming resources while [readiness](0473-spring-boot-actuator-liveness-readiness-probes-for-kubernete.md) alone determines whether it appears in discovery results.

```
[discovery] excluding 10.0.1.9 -- NOT READY (failing readiness probe)
[order-service] routable instances: [10.0.1.5, 10.0.1.14]
[order-service] note: 10.0.1.9's container is still RUNNING, just excluded from traffic
```

## 7. Gotchas & takeaways

> Querying Kubernetes' Endpoints object without respecting the ready/not-ready distinction — treating every address the same regardless of readiness state — silently reintroduces exactly the problem [readiness probes](0473-spring-boot-actuator-liveness-readiness-probes-for-kubernete.md) exist to prevent: traffic gets routed to an instance that explicitly told the platform it isn't ready to handle it.
- Spring Cloud Kubernetes' real `DiscoveryClient` implementation already applies this ready/not-ready filtering correctly out of the box — this example demonstrates the underlying mechanism, not a gap you need to implement yourself.
- This integration is specifically valuable *because* it avoids running a redundant registry — evaluate it against your actual deployment target; a service that might run outside Kubernetes someday should keep its discovery abstraction platform-agnostic even if Kubernetes-specific discovery is used today.
- ConfigMap-backed configuration pairs naturally with Kubernetes' own rollout mechanics — updating a ConfigMap and triggering a rolling restart (or using a refresh mechanism) is a clean way to propagate configuration changes without rebuilding an image.
- Discovery results should always be treated as a snapshot that can change between calls — Pods scale up, scale down, and transition between ready and not-ready constantly, so code consuming a discovery client's result shouldn't cache it longer than a single operation's lifetime.
- When debugging "why isn't traffic reaching this Pod," checking its readiness probe status first is usually faster than assuming a discovery or networking bug — a Pod excluded from Endpoints because of a failing readiness check looks, from the outside, exactly like a Pod that was never discovered at all.
