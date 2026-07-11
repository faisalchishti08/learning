---
card: spring-cloud
gi: 52
slug: spring-cloud-loadbalancer-client-side
title: "Spring Cloud LoadBalancer (client-side)"
---

## 1. What it is

Spring Cloud LoadBalancer is the client-side load balancer used throughout Spring Cloud whenever a caller resolves a service by name (`lb://orders-service`, or a `@LoadBalanced RestTemplate`/`WebClient`) and needs to pick *which* of potentially several live instances actually receives each call. It replaced Netflix Ribbon as the default, and it pulls its instance list directly from whichever discovery client is active — Eureka, Consul, or Zookeeper, all covered in the earlier Service Discovery section.

```java
@Bean
@LoadBalanced
WebClient.Builder loadBalancedWebClientBuilder() {
    return WebClient.builder();
}
```

```java
// resolves "billing-service" to a live instance address before the call actually goes out
webClientBuilder.build().get().uri("http://billing-service/invoices/42").retrieve();
```

## 2. Why & when

Earlier cards touched on client-side discovery informally (a caller looking up instances and picking one, from the Eureka Client card). Spring Cloud LoadBalancer is the actual, reusable component that formalizes that: it sits between "I want to call billing-service" and "here's the exact instance address to connect to," making the load-balancing decision itself pluggable — round-robin by default, but swappable for custom strategies — without application code needing to know which discovery mechanism is behind it.

Reach for (or rather, rely on — it's largely automatic once configured) Spring Cloud LoadBalancer when:

- Any code calls another service by logical name through `@LoadBalanced RestTemplate`/`WebClient`/`RestClient`, Feign (a later card), or `lb://` URIs in Gateway routes — LoadBalancer is what actually resolves the name to a concrete instance underneath all of these.
- Multiple instances of a downstream service need traffic spread across them without a separate, centralized load balancer sitting in the request path.
- The load-balancing strategy itself needs customization — zone-aware balancing, a custom weighting scheme — beyond the round-robin default (covered in later cards in this run).

## 3. Core concept

```
 caller code:  http://billing-service/invoices/42
                        |
                        v
        Spring Cloud LoadBalancer intercepts the call
                        |
        1. asks the active DiscoveryClient (Eureka/Consul/Zookeeper) for live instances of "billing-service"
        2. applies a load-balancing algorithm to pick ONE instance from that list
                        |
                        v
        actual HTTP call goes to the chosen instance's real address
```

LoadBalancer is the glue between "logical service name" (what code expresses intent with) and "one concrete instance address" (what actually receives the network call).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client code calls a logical service name, LoadBalancer resolves it through the discovery client to a list of instances and picks one using its configured algorithm">
  <rect x="20" y="70" width="140" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">http://billing-service/...</text>

  <rect x="220" y="60" width="200" height="60" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Spring Cloud LoadBalancer</text>
  <text x="320" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">resolve name -&gt; pick 1 instance</text>

  <rect x="470" y="20" width="140" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="540" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">DiscoveryClient</text>

  <rect x="470" y="130" width="140" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="540" y="150" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">chosen instance</text>

  <line x1="160" y1="90" x2="218" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a52)"/>
  <line x1="420" y1="75" x2="468" y2="45" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a52)"/>
  <line x1="420" y1="105" x2="468" y2="140" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a52)"/>

  <defs><marker id="a52" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

LoadBalancer consults discovery for the live instance list, then makes the pick — the actual network call only happens after that decision.

## 5. Runnable example

The scenario: resolve `billing-service` calls through a LoadBalancer-shaped abstraction. Start with a hardcoded direct call, then plug in a discovery-backed instance list, then add pluggable load-balancing strategy selection.

### Level 1 — Basic

Hardcoded direct call — the coupling LoadBalancer removes.

```java
public class LoadBalancerLevel1 {
    static String callBilling(String invoiceId) {
        return "GET http://10.0.2.1:8080/invoices/" + invoiceId; // hardcoded, single instance, no balancing
    }

    public static void main(String[] args) {
        System.out.println(callBilling("42"));
    }
}
```

How to run: `java LoadBalancerLevel1.java`

Only one instance is ever called, hardcoded directly — if it moves, scales, or a second instance is added, this code has no way to notice or adapt.

### Level 2 — Intermediate

Plug in a discovery-backed instance list (standing in for a real `DiscoveryClient`) and pick from it.

```java
import java.util.*;

public class LoadBalancerLevel2 {
    interface DiscoveryClient {
        List<String> getInstances(String serviceName);
    }

    static DiscoveryClient discovery = serviceName -> switch (serviceName) {
        case "billing-service" -> List.of("10.0.2.1:8080", "10.0.2.2:8080", "10.0.2.3:8080");
        default -> List.of();
    };

    interface LoadBalancer {
        String choose(List<String> instances);
    }

    static LoadBalancer firstInstance = instances -> instances.get(0); // naive: always picks the first one

    static String callService(String serviceName, String path, LoadBalancer lb) {
        List<String> instances = discovery.getInstances(serviceName);
        if (instances.isEmpty()) throw new IllegalStateException("no instances for " + serviceName);
        String chosen = lb.choose(instances);
        return "GET http://" + chosen + path;
    }

    public static void main(String[] args) {
        for (int i = 0; i < 3; i++) {
            System.out.println(callService("billing-service", "/invoices/42", firstInstance));
        }
    }
}
```

How to run: `java LoadBalancerLevel2.java`

`callService` now genuinely resolves through discovery every time, but the `firstInstance` strategy always returns the same instance regardless of how many are available — this demonstrates the two separate concerns (discovering instances vs. choosing among them) before the second one gets a real strategy.

### Level 3 — Advanced

Make the load-balancing strategy pluggable and swap in a real round-robin implementation, confirming traffic actually spreads across all discovered instances.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class LoadBalancerLevel3 {
    interface DiscoveryClient { List<String> getInstances(String serviceName); }

    static DiscoveryClient discovery = serviceName -> switch (serviceName) {
        case "billing-service" -> List.of("10.0.2.1:8080", "10.0.2.2:8080", "10.0.2.3:8080");
        default -> List.of();
    };

    interface LoadBalancer { String choose(List<String> instances); }

    static class RoundRobinLoadBalancer implements LoadBalancer {
        AtomicInteger counter = new AtomicInteger(0);
        public String choose(List<String> instances) {
            return instances.get(counter.getAndIncrement() % instances.size());
        }
    }

    static class RandomLoadBalancer implements LoadBalancer {
        java.util.Random random = new java.util.Random(42); // fixed seed for reproducible output
        public String choose(List<String> instances) {
            return instances.get(random.nextInt(instances.size()));
        }
    }

    static String callService(String serviceName, String path, LoadBalancer lb) {
        List<String> instances = discovery.getInstances(serviceName);
        String chosen = lb.choose(instances);
        return "GET http://" + chosen + path;
    }

    public static void main(String[] args) {
        LoadBalancer roundRobin = new RoundRobinLoadBalancer();
        System.out.println("-- round robin --");
        for (int i = 0; i < 5; i++) System.out.println(callService("billing-service", "/invoices/" + i, roundRobin));

        LoadBalancer random = new RandomLoadBalancer();
        System.out.println("-- random --");
        for (int i = 0; i < 5; i++) System.out.println(callService("billing-service", "/invoices/" + i, random));
    }
}
```

How to run: `java LoadBalancerLevel3.java`

The `LoadBalancer` interface is now genuinely pluggable — `RoundRobinLoadBalancer` cycles deterministically through every instance in turn, while `RandomLoadBalancer` picks unpredictably (seeded here purely for reproducible example output). Swapping strategies requires no change to `callService` or `discovery` at all — exactly the separation of concerns real Spring Cloud LoadBalancer maintains between instance discovery and instance selection.

## 6. Walkthrough

Trace the round-robin section of Level 3.

1. `roundRobin`, a fresh `RoundRobinLoadBalancer`, starts with `counter = 0`.
2. The loop calls `callService("billing-service", "/invoices/" + i, roundRobin)` five times. Each call first invokes `discovery.getInstances("billing-service")`, returning the same three-address list every time — this models a real `DiscoveryClient` call, cached locally in a real implementation rather than re-fetched on every single request.
3. Each call to `roundRobin.choose(instances)` reads `counter.getAndIncrement()`, which returns the *current* value and then increments it — call 0 gets index `0 % 3 = 0` (`.1`), call 1 gets index `1 % 3 = 1` (`.2`), call 2 gets index `2 % 3 = 2` (`.3`), call 3 wraps to index `0` again (`.1`), call 4 gets index `1` (`.2`).
4. The five printed lines show requests distributed as `.1, .2, .3, .1, .2` — every instance receives a roughly even share of traffic purely from the counter-and-modulo mechanism, with zero coordination needed between separate calls (the shared `counter` state is all that's required).
5. The `random` section repeats the same `callService` flow but with a different `LoadBalancer` implementation swapped in — the discovery step is identical; only the selection logic differs, confirming the two concerns are genuinely decoupled.

```
counter: 0 -> 1 -> 2 -> 3 -> 4
index:   0 -> 1 -> 2 -> 0 -> 1   (each mod 3)
picked: .1 -> .2 -> .3 -> .1 -> .2
```

## 7. Gotchas & takeaways

> **Gotcha:** the instance list LoadBalancer works from is only as fresh as the underlying `DiscoveryClient`'s cache — if that cache hasn't refreshed since an instance was deregistered (a real, if usually brief, window with Eureka's polling-based client, covered earlier), LoadBalancer can still pick a now-dead instance, resulting in a failed call that then needs retry logic (a later card) to recover from.

- LoadBalancer cleanly separates "which instances exist" (the discovery client's job) from "which one gets this particular call" (the load-balancing algorithm's job) — understanding this split makes both easier to reason about and customize independently.
- Round-robin is the sensible default for most workloads: simple, and it spreads load evenly without needing any state beyond a counter.
- Because the strategy is pluggable, workload-specific needs (zone-awareness, weighted balancing, sticky sessions) can be layered in without touching any calling code — later cards build on exactly this pluggability.
- LoadBalancer is what actually executes behind `lb://` URIs (Gateway routes), `@LoadBalanced RestTemplate`/`WebClient`, and Feign clients (a later card) — it's a shared, foundational piece used across nearly every inter-service call pattern in Spring Cloud.
