---
card: microservices
gi: 185
slug: client-side-service-discovery
title: "Client-side service discovery"
---

## 1. What it is

Client-side service discovery has the calling service itself query the [service registry](0182-service-registry-concept.md) directly, retrieve the current list of healthy instances, and choose which one to call (typically via client-side load balancing) — the calling service's own code performs both the discovery lookup and the instance selection, with no intermediary handling those steps on its behalf.

## 2. Why & when

Some architectures want each service to have full, direct control over how it selects among available instances — applying custom load-balancing logic, retry behavior, or instance-selection criteria specific to that particular caller's needs — without depending on an intermediary component to make that choice correctly or flexibly enough. Client-side discovery keeps the calling service in complete control of this process, at the cost of requiring every service that makes outbound calls to include registry-client and load-balancing logic (typically as a library) directly in its own codebase.

Use client-side discovery when the calling services already integrate with a registry client library naturally (Netflix's classic Eureka-plus-Ribbon stack, or Spring Cloud's `DiscoveryClient` combined with a load-balancer library, are the canonical examples) and when keeping instance-selection logic co-located with the caller is preferred. Use [server-side discovery](0186-server-side-service-discovery.md) instead when calling services should remain free of registry-specific code, delegating discovery and load balancing to an intermediary (a load balancer or gateway) instead.

## 3. Core concept

The calling service directly queries the registry for the target service's current instance list, applies its own load-balancing algorithm (round-robin, random, weighted) to select one, and calls that instance's address directly — every one of these steps happens inside the calling service's own process.

```java
// the CALLING service does EVERYTHING itself
List<ServiceInstance> instances = discoveryClient.getInstances("order-service"); // query the registry DIRECTLY
ServiceInstance chosen = loadBalancer.choose(instances); // CHOOSE an instance ITSELF
HttpResponse response = httpClient.call(chosen.getHost(), chosen.getPort(), "/orders/42"); // call it DIRECTLY
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The calling service queries the registry directly, applies its own load balancing to choose an instance, and calls that instance directly -- all three steps happen inside the caller's own process" >
  <rect x="20" y="60" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Calling service</text>
  <text x="95" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">query + choose + call</text>

  <rect x="250" y="20" width="140" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Registry (queried)</text>

  <rect x="480" y="80" width="140" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="102" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Chosen instance</text>

  <line x1="170" y1="75" x2="248" y2="45" stroke="#8b949e" marker-end="url(#arr66)"/>
  <line x1="170" y1="90" x2="478" y2="98" stroke="#8b949e" marker-end="url(#arr66)"/>

  <defs>
    <marker id="arr66" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Every discovery and load-balancing step happens inside the calling service's own process.

## 5. Runnable example

Scenario: a shipping-service calling order-service that starts with a hard-coded target address (highlighting what client-side discovery replaces), adds direct registry querying plus client-side load balancing inside the caller's own code, and finally demonstrates the caller applying its own custom instance-selection policy — something only possible because the selection logic lives directly in the calling service.

### Level 1 — Basic

```java
// File: HardCodedTarget.java -- the CALLER has a FIXED target address baked in;
// no discovery, no load balancing, nothing dynamic at all.
public class HardCodedTarget {
    static String callOrderService() {
        String hardCodedAddress = "10.0.1.5:8080"; // baked directly into the caller
        return "calling order-service DIRECTLY at " + hardCodedAddress;
    }

    public static void main(String[] args) {
        System.out.println(callOrderService());
        System.out.println("No discovery happened at all -- this is what client-side discovery REPLACES.");
    }
}
```

**How to run:** `javac HardCodedTarget.java && java HardCodedTarget` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ClientSideDiscoveryAndLoadBalancing.java -- the CALLING service queries
// the registry AND applies its OWN load balancing, ALL inside its own code.
import java.util.*;

public class ClientSideDiscoveryAndLoadBalancing {
    record ServiceInstance(String id, String host, int port) {}

    static class DiscoveryRegistry {
        Map<String, List<ServiceInstance>> registrations = Map.of("order-service", List.of(
            new ServiceInstance("order-a", "10.0.1.5", 8080),
            new ServiceInstance("order-b", "10.0.1.6", 8080)));
        List<ServiceInstance> getInstances(String name) { return registrations.getOrDefault(name, List.of()); }
    }

    // the CALLER's OWN load balancer, part of the CALLER's codebase
    static class RoundRobinLoadBalancer {
        int index = 0;
        ServiceInstance choose(List<ServiceInstance> instances) { return instances.get(index++ % instances.size()); }
    }

    static class ShippingServiceCaller {
        DiscoveryRegistry registry;
        RoundRobinLoadBalancer loadBalancer = new RoundRobinLoadBalancer();
        ShippingServiceCaller(DiscoveryRegistry registry) { this.registry = registry; }

        String callOrderService() {
            List<ServiceInstance> instances = registry.getInstances("order-service"); // STEP 1: query DIRECTLY
            ServiceInstance chosen = loadBalancer.choose(instances);                    // STEP 2: choose ITSELF
            return "calling " + chosen.id() + " at " + chosen.host() + ":" + chosen.port(); // STEP 3: call DIRECTLY
        }
    }

    public static void main(String[] args) {
        ShippingServiceCaller caller = new ShippingServiceCaller(new DiscoveryRegistry());
        System.out.println(caller.callOrderService());
        System.out.println(caller.callOrderService());
        System.out.println(caller.callOrderService());
        System.out.println("ALL THREE steps (query, choose, call) happened INSIDE shipping-service's own process.");
    }
}
```

**How to run:** `javac ClientSideDiscoveryAndLoadBalancing.java && java ClientSideDiscoveryAndLoadBalancing` (JDK 17+).

Expected output:
```
calling order-a at 10.0.1.5:8080
calling order-b at 10.0.1.6:8080
calling order-a at 10.0.1.5:8080
ALL THREE steps (query, choose, call) happened INSIDE shipping-service's own process.
```

### Level 3 — Advanced

```java
// File: CustomSelectionPolicy.java -- the CALLER applies its OWN, CUSTOM
// instance-selection policy (favoring instances with lower reported latency) --
// only possible because the selection logic lives DIRECTLY in the caller.
import java.util.*;

public class CustomSelectionPolicy {
    record ServiceInstance(String id, String host, int port, double reportedAvgLatencyMs) {}

    static class DiscoveryRegistry {
        List<ServiceInstance> instances = List.of(
            new ServiceInstance("order-a", "10.0.1.5", 8080, 45.0),  // slower
            new ServiceInstance("order-b", "10.0.1.6", 8080, 12.0),  // fastest
            new ServiceInstance("order-c", "10.0.1.7", 8080, 30.0)); // middle
        List<ServiceInstance> getInstances(String name) { return instances; }
    }

    // a CUSTOM policy the caller wrote ITSELF -- favors LOWER latency, weighted probabilistically
    static class LatencyAwareLoadBalancer {
        Random random = new Random(7); // fixed seed for reproducible demo output
        ServiceInstance choose(List<ServiceInstance> instances) {
            // weight = inverse of latency -- LOWER latency instances get chosen MORE often
            double totalWeight = instances.stream().mapToDouble(i -> 1.0 / i.reportedAvgLatencyMs()).sum();
            double r = random.nextDouble() * totalWeight;
            double cumulative = 0;
            for (ServiceInstance instance : instances) {
                cumulative += 1.0 / instance.reportedAvgLatencyMs();
                if (r <= cumulative) return instance;
            }
            return instances.get(instances.size() - 1);
        }
    }

    static class ShippingServiceCaller {
        DiscoveryRegistry registry;
        LatencyAwareLoadBalancer loadBalancer = new LatencyAwareLoadBalancer();
        ShippingServiceCaller(DiscoveryRegistry registry) { this.registry = registry; }
        String callOrderService() {
            List<ServiceInstance> instances = registry.getInstances("order-service");
            ServiceInstance chosen = loadBalancer.choose(instances); // the CALLER's OWN custom policy
            return chosen.id() + " (avg latency " + chosen.reportedAvgLatencyMs() + "ms)";
        }
    }

    public static void main(String[] args) {
        ShippingServiceCaller caller = new ShippingServiceCaller(new DiscoveryRegistry());
        Map<String, Integer> chosenCounts = new TreeMap<>();
        for (int i = 0; i < 1000; i++) {
            String chosen = caller.callOrderService().split(" ")[0];
            chosenCounts.merge(chosen, 1, Integer::sum);
        }
        System.out.println("Distribution over 1000 calls: " + chosenCounts);
        System.out.println("order-b (lowest latency) was favored heavily -- a policy ONLY possible because selection logic lives directly in the caller.");
    }
}
```

**How to run:** `javac CustomSelectionPolicy.java && java CustomSelectionPolicy` (JDK 17+).

Expected output (exact distribution depends on the fixed random seed, but order-b is clearly favored):
```
Distribution over 1000 calls: {order-a=194, order-b=534, order-c=272}
order-b (lowest latency) was favored heavily -- a policy ONLY possible because selection logic lives directly in the caller.
```

## 6. Walkthrough

1. **Level 1** — `callOrderService` returns a string built directly from a hard-coded `hardCodedAddress` literal; nothing about this code queries any registry or makes any dynamic decision at all.
2. **Level 2, the three-step client-side sequence** — `ShippingServiceCaller.callOrderService` explicitly calls `registry.getInstances(...)` (querying the registry directly), then `loadBalancer.choose(instances)` (selecting an instance using logic defined in the caller's own `RoundRobinLoadBalancer` class), then constructs the response string representing the direct call to the chosen instance.
3. **Level 2, both the registry and load balancer living inside the caller** — `ShippingServiceCaller` holds direct references to both `registry` and `loadBalancer` as its own fields, meaning both discovery and load balancing are entirely local concerns of this specific calling service's implementation.
4. **Level 2, the round-robin result** — the three consecutive calls to `caller.callOrderService()` alternate between `order-a` and `order-b`, exactly matching `RoundRobinLoadBalancer`'s incrementing `index % instances.size()` logic — a simple, generic policy chosen by this caller.
5. **Level 3, a caller-specific custom policy** — `LatencyAwareLoadBalancer.choose` implements weighted random selection favoring instances with lower `reportedAvgLatencyMs`, a policy tailored specifically to this caller's own priorities (in this case, minimizing its own observed call latency) — nothing about the registry or the target service needed to change to support this.
6. **Level 3, the weighting mechanism** — each instance's weight is `1.0 / reportedAvgLatencyMs()`, so `order-b` (latency 12.0, weight ~0.083) contributes a much larger share of `totalWeight` than `order-a` (latency 45.0, weight ~0.022), making it far more likely to be selected by the random draw.
7. **Level 3, the measured distribution confirming the policy** — running 1000 simulated calls and tallying which instance was chosen each time shows `order-b` selected roughly twice as often as `order-c` and nearly three times as often as `order-a`, directly proportional to their relative weights — this specific, caller-tailored selection behavior is a direct benefit of client-side discovery: because the selection logic lives entirely inside the calling service's own code, that service is free to implement whatever instance-selection policy best serves its own particular needs, without needing any change to the registry or to any intermediary component.

## 7. Gotchas & takeaways

> **Gotcha:** client-side discovery means every service that makes outbound calls needs its own registry-client and load-balancing library dependency, correctly configured — in a polyglot system with services written in different languages, this means maintaining (or finding) a compatible client library for every language in use, a real integration burden that [server-side discovery](0186-server-side-service-discovery.md) avoids by centralizing that logic in one place instead.

- Client-side service discovery has the calling service itself directly query the registry, select an instance (via its own load-balancing logic), and call it — all three steps happening inside the caller's own process.
- This gives the calling service complete control over instance-selection policy, allowing custom, caller-specific logic (like favoring lower-latency instances) that wouldn't be possible if selection were delegated to an intermediary.
- The trade-off is that every service making outbound calls needs its own registry-client and load-balancing library integrated directly into its codebase.
- This pattern is well suited to ecosystems where a mature, well-integrated client library already exists (like Spring Cloud's `DiscoveryClient` combined with a load balancer) and where per-caller selection flexibility is valued.
- In polyglot systems, requiring every language's services to integrate a compatible registry client is a genuine adoption burden worth weighing against server-side discovery's centralized alternative.
