---
card: microservices
gi: 202
slug: spring-cloud-loadbalancer-using-the-registry
title: "Spring Cloud LoadBalancer using the registry"
---

## 1. What it is

Spring Cloud LoadBalancer is Spring's client-side load-balancing library, built directly on top of the [`DiscoveryClient`](0200-spring-cloud-discoveryclient-abstraction.md) abstraction — it takes a logical service name, resolves it to the current list of registered instances via `DiscoveryClient`, applies a load-balancing strategy (round-robin by default) to pick one, and integrates transparently with `RestTemplate` and `WebClient` so ordinary HTTP client code can call a logical service name and have it automatically resolved and balanced, without the calling code performing discovery or instance selection itself.

## 2. Why & when

Manually calling `DiscoveryClient.getInstances(...)`, applying a selection strategy, and then making the actual HTTP call, as earlier examples in this course have modeled explicitly, is exactly the kind of boilerplate that gets repeated at every single call site needing to reach another service — error-prone to duplicate consistently and a genuine maintenance burden across a codebase with many outbound calls. Spring Cloud LoadBalancer packages this entire flow into a single, reusable integration: a `RestTemplate` or `WebClient` annotated as load-balancer-aware (`@LoadBalanced`) can be called with a logical service name directly in the URL, and the library transparently performs discovery, selection, and the actual call underneath, using `DiscoveryClient` as its data source the whole time.

Use Spring Cloud LoadBalancer whenever a Spring application needs to make [client-side discovery](0185-client-side-service-discovery.md) calls to other registered services — it's the standard, idiomatic way to combine `DiscoveryClient`'s registry access with actual HTTP calling in the Spring Cloud ecosystem, working with any `DiscoveryClient` implementation (Eureka, Consul, Kubernetes) interchangeably.

## 3. Core concept

A `RestTemplate` (or `WebClient`) marked `@LoadBalanced` intercepts calls made to a logical service name (used as if it were a hostname in the URL) and, before the actual HTTP request is sent, resolves that name via `DiscoveryClient`, selects an instance using the configured load-balancing strategy, and substitutes the instance's real address into the request — application code never sees or handles this resolution step directly.

```java
@Bean
@LoadBalanced // marks this RestTemplate as registry-aware
public RestTemplate restTemplate() { return new RestTemplate(); }

// application code calls a LOGICAL service name, as if it were a real hostname
String response = restTemplate.getForObject("http://order-service/orders/42", String.class);
// Spring Cloud LoadBalancer INTERCEPTS this, resolves "order-service" via DiscoveryClient,
// picks an instance, and substitutes the REAL address -- ALL transparently
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code calls restTemplate.getForObject with a logical service name in the URL; the load-balanced RestTemplate intercepts this, queries DiscoveryClient for current instances, selects one via round-robin, and issues the actual HTTP call to that instance's real address" >
  <rect x="20" y="70" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Application code</text>
  <text x="95" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">calls "order-service"</text>

  <rect x="230" y="55" width="180" height="65" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="78" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">@LoadBalanced client</text>
  <text x="320" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">DiscoveryClient lookup +</text>
  <text x="320" y="107" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">round-robin selection</text>

  <rect x="470" y="70" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Chosen instance</text>

  <line x1="170" y1="92" x2="228" y2="87" stroke="#8b949e" marker-end="url(#arr83)"/>
  <line x1="410" y1="87" x2="468" y2="92" stroke="#8b949e" marker-end="url(#arr83)"/>

  <defs>
    <marker id="arr83" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The logical-name call is intercepted, resolved, and load-balanced entirely before the real HTTP request goes out.

## 5. Runnable example

Scenario: an order-lookup call that starts with manual discovery-plus-selection-plus-call code repeated at every call site, refactors to a load-balancer-aware helper that hides all three steps behind a single logical-name-based call, and finally demonstrates the load balancer correctly adapting to a changing instance set between calls, purely through its underlying `DiscoveryClient` dependency, with no changes to calling code.

### Level 1 — Basic

```java
// File: ManualDiscoverSelectCall.java -- discovery, selection, AND the call
// itself are ALL hand-written at EVERY call site -- real, repeated boilerplate.
import java.util.*;

public class ManualDiscoverSelectCall {
    record ServiceInstance(String host, int port) {}
    static List<ServiceInstance> registry = List.of(new ServiceInstance("10.0.1.5", 8080), new ServiceInstance("10.0.1.6", 8080));
    static int roundRobinIndex = 0;

    static String callOrderService(String path) {
        List<ServiceInstance> instances = registry; // STEP 1: discover
        ServiceInstance chosen = instances.get(roundRobinIndex++ % instances.size()); // STEP 2: select
        return "calling " + chosen.host() + ":" + chosen.port() + path; // STEP 3: call
    }

    public static void main(String[] args) {
        System.out.println(callOrderService("/orders/42"));
        System.out.println("EVERY call site needing to reach a service repeats this SAME 3-step pattern by hand.");
    }
}
```

**How to run:** `javac ManualDiscoverSelectCall.java && java ManualDiscoverSelectCall` (JDK 17+).

### Level 2 — Intermediate

```java
// File: LoadBalancedRestTemplateStyle.java -- ONE reusable helper hides
// discovery+selection+call behind a call using a LOGICAL service name --
// mirroring @LoadBalanced RestTemplate's behavior.
import java.util.*;
import java.util.function.*;

public class LoadBalancedRestTemplateStyle {
    record ServiceInstance(String host, int port) {}
    interface DiscoveryClient { List<ServiceInstance> getInstances(String serviceId); }

    static class SimpleDiscoveryClient implements DiscoveryClient {
        public List<ServiceInstance> getInstances(String serviceId) {
            return List.of(new ServiceInstance("10.0.1.5", 8080), new ServiceInstance("10.0.1.6", 8080));
        }
    }

    // mirrors a @LoadBalanced RestTemplate: takes a LOGICAL name + path, does discovery+selection+call INTERNALLY
    static class LoadBalancedClient {
        DiscoveryClient discoveryClient;
        int roundRobinIndex = 0;
        LoadBalancedClient(DiscoveryClient discoveryClient) { this.discoveryClient = discoveryClient; }

        String getForObject(String serviceIdAndPath) { // e.g. "order-service/orders/42" -- LOGICAL name, like a URL
            String[] parts = serviceIdAndPath.split("/", 2);
            String serviceId = parts[0];
            String path = "/" + parts[1];

            List<ServiceInstance> instances = discoveryClient.getInstances(serviceId); // discovery, HIDDEN inside here
            ServiceInstance chosen = instances.get(roundRobinIndex++ % instances.size()); // selection, HIDDEN inside here
            return "calling " + chosen.host() + ":" + chosen.port() + path; // the actual call, HIDDEN inside here
        }
    }

    public static void main(String[] args) {
        LoadBalancedClient restTemplate = new LoadBalancedClient(new SimpleDiscoveryClient());

        // APPLICATION code: calls a LOGICAL name, exactly like real @LoadBalanced RestTemplate usage
        System.out.println(restTemplate.getForObject("order-service/orders/42"));
        System.out.println("Application code just calls a LOGICAL name -- discovery, selection, and the actual call are ALL hidden inside ONE reusable client.");
    }
}
```

**How to run:** `javac LoadBalancedRestTemplateStyle.java && java LoadBalancedRestTemplateStyle` (JDK 17+).

Expected output:
```
calling 10.0.1.5:8080/orders/42
Application code just calls a LOGICAL name -- discovery, selection, and the actual call are ALL hidden inside ONE reusable client.
```

### Level 3 — Advanced

```java
// File: AdaptsToChangingInstancesAutomatically.java -- the load-balanced
// client AUTOMATICALLY reflects instance changes, since it queries
// DiscoveryClient FRESH on every call -- NO changes needed to calling code.
import java.util.*;
import java.util.function.*;

public class AdaptsToChangingInstancesAutomatically {
    record ServiceInstance(String host, int port) {}
    interface DiscoveryClient { List<ServiceInstance> getInstances(String serviceId); }

    // a MUTABLE simulated registry, so we can change it mid-run
    static class MutableDiscoveryClient implements DiscoveryClient {
        List<ServiceInstance> instances = new ArrayList<>(List.of(new ServiceInstance("10.0.1.5", 8080), new ServiceInstance("10.0.1.6", 8080)));
        public List<ServiceInstance> getInstances(String serviceId) { return instances; } // FRESH read, every call
    }

    static class LoadBalancedClient {
        DiscoveryClient discoveryClient;
        int roundRobinIndex = 0;
        LoadBalancedClient(DiscoveryClient discoveryClient) { this.discoveryClient = discoveryClient; }
        String getForObject(String serviceIdAndPath) {
            String[] parts = serviceIdAndPath.split("/", 2);
            List<ServiceInstance> instances = discoveryClient.getInstances(parts[0]); // FRESH lookup EVERY call
            ServiceInstance chosen = instances.get(roundRobinIndex++ % instances.size());
            return "calling " + chosen.host() + ":" + chosen.port() + "/" + parts[1];
        }
    }

    public static void main(String[] args) {
        MutableDiscoveryClient discoveryClient = new MutableDiscoveryClient();
        LoadBalancedClient restTemplate = new LoadBalancedClient(discoveryClient); // built ONCE

        System.out.println("Before scale-up:");
        System.out.println("  " + restTemplate.getForObject("order-service/orders/1"));
        System.out.println("  " + restTemplate.getForObject("order-service/orders/2"));

        // SCALE UP: a third instance registers -- NOTHING about restTemplate itself changes
        discoveryClient.instances.add(new ServiceInstance("10.0.1.7", 8080));
        System.out.println("\nAfter scale-up to 3 instances (restTemplate object UNCHANGED):");
        System.out.println("  " + restTemplate.getForObject("order-service/orders/3"));
        System.out.println("  " + restTemplate.getForObject("order-service/orders/4"));
        System.out.println("  " + restTemplate.getForObject("order-service/orders/5"));

        System.out.println("\nThe SAME restTemplate object, with ZERO reconfiguration, correctly started including the NEW instance -- because it queries DiscoveryClient FRESH on every single call.");
    }
}
```

**How to run:** `javac AdaptsToChangingInstancesAutomatically.java && java AdaptsToChangingInstancesAutomatically` (JDK 17+).

Expected output:
```
Before scale-up:
  calling 10.0.1.5:8080/orders/1
  calling 10.0.1.6:8080/orders/2

After scale-up to 3 instances (restTemplate object UNCHANGED):
  calling 10.0.1.7:8080/orders/3
  calling 10.0.1.5:8080/orders/4
  calling 10.0.1.6:8080/orders/5

The SAME restTemplate object, with ZERO reconfiguration, correctly started including the NEW instance -- because it queries DiscoveryClient FRESH on every single call.
```

## 6. Walkthrough

1. **Level 1** — `callOrderService` performs all three steps (reading `registry`, computing `chosen` via round-robin indexing, and building the result string) inline, in one method; any second call site needing to reach `order-service` (or any other service) would need to duplicate this identical three-step structure.
2. **Level 2, hiding the three steps behind one call** — `LoadBalancedClient.getForObject` takes a single string combining the logical service name and path, and internally performs discovery (`discoveryClient.getInstances(serviceId)`), selection (round-robin indexing), and constructs the call result — all three steps still happen, but they're encapsulated in one reusable method rather than repeated inline.
3. **Level 2, the application-facing simplicity** — `main`'s call, `restTemplate.getForObject("order-service/orders/42")`, mirrors exactly how a real `@LoadBalanced RestTemplate.getForObject("http://order-service/orders/42", ...)` call looks from application code's perspective: a logical name used as if it were a real hostname.
4. **Level 3, discovery performed fresh on each call** — `MutableDiscoveryClient.getInstances` returns the live `instances` list directly (not a snapshot), and `LoadBalancedClient.getForObject` calls this method anew on every invocation, meaning it never caches or reuses a previous instance list across calls.
5. **Level 3, the pre-scale-up baseline** — the first two calls alternate between the two originally-registered instances (`10.0.1.5` then `10.0.1.6`), following the round-robin `roundRobinIndex` counter.
6. **Level 3, the scale-up event** — `discoveryClient.instances.add(new ServiceInstance("10.0.1.7", 8080))` adds a third instance directly to the mutable registry, entirely independent of `restTemplate`, which is never reconstructed or reconfigured.
7. **Level 3, the automatic adaptation observed** — the three post-scale-up calls correctly rotate among all *three* instances (continuing the round-robin sequence, now including `10.0.1.7`), purely because each call to `getForObject` triggers a fresh call to `discoveryClient.getInstances(...)`, which reflects the registry's current, updated state — this is exactly the mechanism by which a real `@LoadBalanced RestTemplate` (or `WebClient`) transparently adapts to a scaling event, a crashed instance, or any other registry change, since its underlying `DiscoveryClient` dependency is what determines the current instance list on every single call, with no caching or manual refresh logic that application code needs to manage.

## 7. Gotchas & takeaways

> **Gotcha:** the load-balancing strategy (round-robin by default) is pluggable but not automatically aware of instance health beyond what the underlying `DiscoveryClient` already filters — if a `DiscoveryClient` implementation returns an instance that's technically registered but momentarily struggling (a scenario a [circuit breaker](0177-gateway-circuit-breaker-filter-resilience4j.md) is specifically designed to protect against), the load balancer alone won't detect or route around that on its own; combining Spring Cloud LoadBalancer with a circuit breaker for calls to important dependencies is a common and recommended pairing precisely because they address different failure modes.

- Spring Cloud LoadBalancer combines `DiscoveryClient`'s instance data with an actual HTTP call, letting application code call a logical service name directly and have discovery, selection, and the real call handled transparently underneath.
- A `RestTemplate` or `WebClient` marked `@LoadBalanced` intercepts calls using a logical service name and resolves it to a real instance address before the request is actually sent.
- This eliminates the repeated discover-select-call boilerplate that would otherwise need to be written at every outbound call site.
- Because it queries `DiscoveryClient` fresh on each call, a load-balanced client automatically adapts to instance changes — scale-ups, crashes, restarts — with no reconfiguration or manual refresh needed.
- Load balancing alone doesn't address instance-level failure the way a circuit breaker does; pairing Spring Cloud LoadBalancer with a circuit breaker for important dependencies covers both concerns together.
