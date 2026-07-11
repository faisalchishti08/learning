---
card: spring-cloud
gi: 10
slug: discoveryclient-abstraction
title: "DiscoveryClient abstraction"
---

## 1. What it is

`DiscoveryClient` is the Commons interface specifically for the *read* side of service discovery — listing known service ids and looking up the current instances of a named service. It's the interface introduced conceptually in the Commons card; this card looks at its actual method surface and how application code uses it directly, before the next card covers the annotation that wires everything together automatically.

```java
public interface DiscoveryClient {
    String description();
    List<ServiceInstance> getInstances(String serviceId);
    List<String> getServices();
}
```

## 2. Why & when

`ServiceRegistry` (previous card) is how an instance announces itself; `DiscoveryClient` is how any other instance finds it. Together they're the two halves of the same system: every registered instance is discoverable, and `DiscoveryClient` is the read API that makes that discovery actually usable from application code.

Reach for `DiscoveryClient` directly when:

- Writing code that needs to enumerate available instances of a service manually — for a custom load-balancing strategy, a health-check dashboard, or diagnostic tooling.
- You want to see *all* currently known service ids (`getServices()`) rather than looking up one specific service by name.
- Understanding what a higher-level abstraction (like `@LoadBalanced RestTemplate` or Spring Cloud OpenFeign, covered in later cards) is actually doing underneath — they're built on top of exactly this interface.

Most application code doesn't call `DiscoveryClient` directly for making service-to-service calls — a load-balanced HTTP client (a later card) is the more common, higher-level entry point. `DiscoveryClient` is the foundation those tools are built on.

## 3. Core concept

```
 interface DiscoveryClient {
     List<String> getServices();                      -- every known service id
     List<ServiceInstance> getInstances(String id);     -- every current instance of ONE service
 }

 discoveryClient.getServices()
   -> ["payment-service", "inventory-service", "order-service"]

 discoveryClient.getInstances("payment-service")
   -> [ ServiceInstance(host=10.0.1.5, port=8081),
        ServiceInstance(host=10.0.1.6, port=8081) ]
```

`getServices()` answers "what exists"; `getInstances(id)` answers "where is it, right now" for one specific service.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="getServices returns a list of known service names, and getInstances for one of those names returns its current instance locations">
  <rect x="20" y="30" width="220" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="55" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">getServices()</text>

  <line x1="240" y1="50" x2="300" y2="50" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a30)"/>

  <rect x="310" y="30" width="300" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="460" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">[payment-service, inventory-service, ...]</text>

  <rect x="20" y="100" width="220" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="125" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">getInstances("payment-service")</text>

  <line x1="240" y1="120" x2="300" y2="120" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a30)"/>

  <rect x="310" y="100" width="300" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="460" y="125" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">[10.0.1.5:8081, 10.0.1.6:8081]</text>

  <defs><marker id="a30" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`getServices` lists what's known; `getInstances` resolves one service name down to its concrete current locations.

## 5. Runnable example

The scenario: a diagnostic tool that inspects a running discovery registry, evolving from a bare instance-lookup call, to enumerating every known service and its instance count, to a health-summary tool that cross-references instance status — the kind of tooling built directly on `DiscoveryClient` rather than through a higher-level HTTP client abstraction.

### Level 1 — Basic

Model the bare `getInstances` lookup against an in-memory stand-in registry.

```java
import java.util.*;

public class DiscoveryClientLevel1 {
    public static void main(String[] args) {
        DiscoveryClientImpl discoveryClient = new DiscoveryClientImpl();
        discoveryClient.register("payment-service", new ServiceInstance("10.0.1.5", 8081));
        discoveryClient.register("payment-service", new ServiceInstance("10.0.1.6", 8081));

        List<ServiceInstance> instances = discoveryClient.getInstances("payment-service");
        System.out.println("payment-service instances: " + instances);
    }
}

class ServiceInstance {
    String host; int port;
    ServiceInstance(String host, int port) { this.host = host; this.port = port; }
    public String toString() { return host + ":" + port; }
}

// Stands in for org.springframework.cloud.client.discovery.DiscoveryClient.
class DiscoveryClientImpl {
    private final Map<String, List<ServiceInstance>> registrations = new HashMap<>();
    void register(String serviceId, ServiceInstance instance) {
        registrations.computeIfAbsent(serviceId, k -> new ArrayList<>()).add(instance);
    }
    List<ServiceInstance> getInstances(String serviceId) { return registrations.getOrDefault(serviceId, List.of()); }
}
```

How to run: `java DiscoveryClientLevel1.java`

`getInstances("payment-service")` returns every currently registered instance of that one named service — the fundamental building block every higher-level discovery-aware tool in Spring Cloud is built on.

### Level 2 — Intermediate

Add `getServices()`, enumerating every known service id, and use it to build a simple inventory report across the whole registry.

```java
import java.util.*;

public class DiscoveryClientLevel2 {
    public static void main(String[] args) {
        DiscoveryClientImpl discoveryClient = new DiscoveryClientImpl();
        discoveryClient.register("payment-service", new ServiceInstance("10.0.1.5", 8081));
        discoveryClient.register("payment-service", new ServiceInstance("10.0.1.6", 8081));
        discoveryClient.register("inventory-service", new ServiceInstance("10.0.2.5", 8082));
        discoveryClient.register("order-service", new ServiceInstance("10.0.3.5", 8083));

        System.out.println("Known services and instance counts:");
        for (String serviceId : discoveryClient.getServices()) {
            int count = discoveryClient.getInstances(serviceId).size();
            System.out.println("  " + serviceId + ": " + count + " instance(s)");
        }
    }
}

class ServiceInstance {
    String host; int port;
    ServiceInstance(String host, int port) { this.host = host; this.port = port; }
    public String toString() { return host + ":" + port; }
}

class DiscoveryClientImpl {
    private final Map<String, List<ServiceInstance>> registrations = new HashMap<>();
    void register(String serviceId, ServiceInstance instance) {
        registrations.computeIfAbsent(serviceId, k -> new ArrayList<>()).add(instance);
    }
    List<ServiceInstance> getInstances(String serviceId) { return registrations.getOrDefault(serviceId, List.of()); }
    List<String> getServices() { return new ArrayList<>(registrations.keySet()); }
}
```

How to run: `java DiscoveryClientLevel2.java`

`getServices()` provides the full inventory of what's registered, and looping over it with `getInstances` builds a complete picture of the running system's topology — exactly the kind of diagnostic or dashboard tooling that's built directly on `DiscoveryClient` rather than through a load-balanced HTTP client.

### Level 3 — Advanced

Add a health-summary tool cross-referencing instance metadata (a simulated health status per instance) to flag services that have zero *healthy* instances — a genuinely useful diagnostic that goes beyond raw counts.

```java
import java.util.*;

public class DiscoveryClientLevel3 {
    public static void main(String[] args) {
        DiscoveryClientImpl discoveryClient = new DiscoveryClientImpl();
        discoveryClient.register("payment-service", new ServiceInstance("10.0.1.5", 8081, true));
        discoveryClient.register("payment-service", new ServiceInstance("10.0.1.6", 8081, false)); // unhealthy
        discoveryClient.register("inventory-service", new ServiceInstance("10.0.2.5", 8082, false)); // ALL unhealthy
        discoveryClient.register("order-service", new ServiceInstance("10.0.3.5", 8083, true));

        System.out.println("Service health summary:");
        for (String serviceId : discoveryClient.getServices()) {
            List<ServiceInstance> instances = discoveryClient.getInstances(serviceId);
            long healthyCount = instances.stream().filter(i -> i.healthy).count();

            String status = healthyCount == 0 ? "CRITICAL -- no healthy instances"
                : healthyCount < instances.size() ? "DEGRADED"
                : "HEALTHY";
            System.out.println("  " + serviceId + ": " + healthyCount + "/" + instances.size() + " healthy -- " + status);
        }
    }
}

class ServiceInstance {
    String host; int port; boolean healthy;
    ServiceInstance(String host, int port, boolean healthy) { this.host = host; this.port = port; this.healthy = healthy; }
    public String toString() { return host + ":" + port; }
}

class DiscoveryClientImpl {
    private final Map<String, List<ServiceInstance>> registrations = new HashMap<>();
    void register(String serviceId, ServiceInstance instance) {
        registrations.computeIfAbsent(serviceId, k -> new ArrayList<>()).add(instance);
    }
    List<ServiceInstance> getInstances(String serviceId) { return registrations.getOrDefault(serviceId, List.of()); }
    List<String> getServices() { return new ArrayList<>(registrations.keySet()); }
}
```

How to run: `java DiscoveryClientLevel3.java`

The loop computes `healthyCount` per service and classifies it into `HEALTHY`, `DEGRADED`, or `CRITICAL` — `inventory-service` has exactly one instance and it's unhealthy, so `healthyCount == 0` and the whole service is flagged `CRITICAL`, a signal that's invisible from a raw instance *count* alone (which would show "1 instance" with no indication that instance can't actually serve traffic).

## 6. Walkthrough

Execution starts in `main` for Level 3. Four services are registered with a mix of healthy and unhealthy instance metadata. The loop iterates every service id from `getServices()`.

For `payment-service`, `instances` has two entries, one healthy — `healthyCount = 1`, and since `0 < healthyCount < instances.size()`, the status resolves to `DEGRADED`:

```
Service health summary:
  payment-service: 1/2 healthy -- DEGRADED
```

For `inventory-service`, its single instance is unhealthy — `healthyCount = 0` — triggering the `CRITICAL` branch:

```
  inventory-service: 0/1 healthy -- CRITICAL -- no healthy instances
```

`order-service`, with its one healthy instance, resolves to `HEALTHY`. In a real Spring Cloud application, this kind of summary is exactly what monitoring dashboards or custom health-aggregation endpoints build on top of `DiscoveryClient.getServices()`/`getInstances()`, often combined with each `ServiceInstance`'s metadata map (covered in the next card) to carry richer health or version information than a plain boolean flag.

## 7. Gotchas & takeaways

> Gotcha: `DiscoveryClient.getInstances(...)` typically reflects the registry's *last known* state, which is periodically refreshed rather than updated in real time — an instance that just crashed may still appear in the results for a short window until the registry's own health-check/heartbeat mechanism notices and removes it, so code consuming this API should generally still handle a call failing against a "known good" instance gracefully.

> Gotcha: iterating `getServices()` for every request (rather than caching and periodically refreshing the list) can add unnecessary registry load in a system with many services — for anything beyond occasional diagnostic tooling, prefer the higher-level, load-balancer-integrated clients (a later card) that handle this caching and refresh concern already.

- `DiscoveryClient` is the read-side Commons interface for service discovery: `getServices()` lists known service ids, `getInstances(id)` resolves one service to its current instance locations.
- It's the foundation higher-level tools (load-balanced HTTP clients, Feign) are built on — most application code calls those higher-level tools rather than `DiscoveryClient` directly.
- Direct usage is most common for diagnostic tooling, dashboards, or custom logic that needs to enumerate the whole registry rather than just resolve one service call.
- Registry state is eventually consistent, not real-time — code built on `DiscoveryClient` results should still handle an individual instance turning out to be unreachable.
