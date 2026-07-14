---
card: microservices
gi: 544
slug: spring-cloud-loadbalancer-client-side-lb
title: "Spring Cloud LoadBalancer (client-side LB)"
---

## 1. What it is

**Spring Cloud LoadBalancer** is the client-side load-balancing implementation used throughout Spring Cloud (the concrete backing behind `@LoadBalanced` `RestTemplate`/`WebClient` calls discussed in [Spring Cloud Commons](0539-spring-cloud-commons-shared-abstractions.md)), replacing the older, now-deprecated Netflix Ribbon. "Client-side" is the key distinction: rather than every request going through a centralized load-balancer server that decides which backend instance to route to (server-side load balancing, like a traditional hardware load balancer or [API gateway](0543-spring-cloud-gateway-edge-routing.md) in front of a service), each *calling* service instance itself queries service discovery for the current list of healthy instances and chooses one directly, distributing load without any separate load-balancer infrastructure in the request path at all.

## 2. Why & when

You rely on client-side load balancing specifically for internal, service-to-service calls where introducing a separate load-balancer hop for every call would add unnecessary latency and infrastructure:

- **Server-side load balancing (a hardware load balancer, or a gateway) adds a network hop**: the caller sends to the load balancer, which then forwards to a chosen backend instance — every call pays for that extra hop's latency, and the load balancer itself becomes a piece of infrastructure to scale and keep highly available.
- **Client-side load balancing eliminates that extra hop for internal calls**: the calling service queries service discovery directly (an operation that's typically cached locally and refreshed periodically, so it's cheap per-call), picks an instance using a configured strategy, and calls that instance directly — no separate load-balancer process sits between the two services at all.
- **This is well suited to internal, service-to-service traffic** where every calling service already participates in the same service-discovery ecosystem — for external, edge traffic entering the system from outside, an [API gateway](0543-spring-cloud-gateway-edge-routing.md) (itself potentially using this same client-side load balancing internally when it forwards to backend services) is still the more appropriate front door, since external clients generally aren't, and shouldn't be, integrated directly with your internal service discovery.
- **The default round-robin strategy distributes calls evenly across healthy instances**, and Spring Cloud LoadBalancer supports pluggable strategies (weighted, zone-aware, or custom) for cases where evenly-distributed round-robin isn't the right fit — for instance, preferring instances in the same availability zone as the caller to reduce cross-zone network cost and latency.

## 3. Core concept

Think of the difference between calling a company's main switchboard, which then decides which specific support agent to connect you to (server-side: one central decision-maker in the path of every call), versus each caller in the company already having a shared, regularly-updated list of which support agents are currently available and simply picking one themselves, directly, without going through a switchboard at all (client-side: the decision happens at the caller, with no extra hop). The second approach removes the switchboard as a piece of infrastructure and as a potential bottleneck or single point of failure for every single call, at the cost of every caller needing to maintain (or fetch) that shared, current list of available agents themselves.

Concretely:

1. **`@LoadBalanced` on a `RestTemplate`/`WebClient.Builder` bean activates client-side load balancing** for that specific client — a call using a logical service name (`http://order-service/...`) is intercepted before the request is actually sent.
2. **The `LoadBalancerClient` queries the active `DiscoveryClient`** (Eureka, Consul, Kubernetes, whichever is configured) for the current list of healthy instances registered under that logical name.
3. **A load-balancing strategy (algorithm) selects one instance from that list** — round-robin by default, cycling through instances evenly across successive calls, though weighted or zone-preference strategies can be configured instead.
4. **The logical URL is rewritten to the chosen instance's actual address**, and *that* concrete request is what's actually sent over the network — all of this happens locally, within the calling service's own process, with no separate load-balancer server involved in the request path at all.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Server-side load balancing routes every call through a separate load-balancer hop; client-side load balancing has the caller query discovery and pick an instance directly, with no extra hop">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server-side LB</text>
  <rect x="20" y="35" width="90" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="65" y="56" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">caller</text>
  <rect x="140" y="35" width="90" height="34" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="185" y="56" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">LB server</text>
  <rect x="260" y="35" width="90" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="305" y="56" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance</text>
  <line x1="110" y1="52" x2="140" y2="52" stroke="#8b949e" marker-end="url(#a9)"/>
  <line x1="230" y1="52" x2="260" y2="52" stroke="#8b949e" marker-end="url(#a9)"/>
  <text x="185" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">every call: extra hop through the LB server</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Client-side LB</text>
  <rect x="430" y="35" width="90" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="475" y="56" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">caller</text>
  <rect x="560" y="35" width="90" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="605" y="56" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance</text>
  <line x1="520" y1="52" x2="560" y2="52" stroke="#8b949e" marker-end="url(#a9)"/>
  <text x="545" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">caller picks directly -- no extra hop, no separate LB server</text>
  <defs><marker id="a9" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

Server-side load balancing routes every call through an extra hop; client-side load balancing has the caller select an instance directly, with none.

## 5. Runnable example

Scenario: a caller distributing calls across multiple healthy instances. We start with a plain Java model of round-robin selection, extend it to combine it with a discovery lookup, then show the real Spring Cloud LoadBalancer configuration alongside `@LoadBalanced`.

### Level 1 — Basic

```java
// File: RoundRobinBasic.java -- models the CORE round-robin selection
// idea: cycle through a known list of instances evenly, call by call.
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class RoundRobinBasic {
    static List<String> instances = List.of("10.0.5.2:8080", "10.0.5.9:8080", "10.0.5.14:8080");
    static AtomicInteger counter = new AtomicInteger(0);

    static String chooseInstance() {
        int index = counter.getAndIncrement() % instances.size();
        return instances.get(index);
    }

    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) System.out.println("call " + i + " -> " + chooseInstance());
    }
}
```

How to run: `java RoundRobinBasic.java`

`chooseInstance` cycles through the three known instances evenly using modular arithmetic on an incrementing counter — five calls land on indices 0, 1, 2, 0, 1, distributing load roughly evenly across all three instances without favoring any single one.

### Level 2 — Intermediate

```java
// File: DiscoveryBackedRoundRobin.java -- combines round-robin selection
// with a FRESH discovery lookup each time, so the instance LIST itself
// can change between calls (an instance added or removed) and selection
// still works correctly against whatever is CURRENTLY registered.
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class DiscoveryBackedRoundRobin {
    static List<String> registeredInstances = new ArrayList<>(List.of("10.0.5.2:8080", "10.0.5.9:8080"));
    static AtomicInteger counter = new AtomicInteger(0);

    static List<String> discover(String serviceName) { return registeredInstances; } // simulates a discovery query

    static String chooseInstance(String serviceName) {
        List<String> current = discover(serviceName); // FRESH lookup, every call
        if (current.isEmpty()) throw new IllegalStateException("no healthy instances for " + serviceName);
        int index = counter.getAndIncrement() % current.size();
        return current.get(index);
    }

    public static void main(String[] args) {
        for (int i = 0; i < 3; i++) System.out.println("call " + i + " -> " + chooseInstance("order-service"));

        registeredInstances.add("10.0.5.14:8080"); // a THIRD instance joins the fleet
        for (int i = 3; i < 6; i++) System.out.println("call " + i + " -> " + chooseInstance("order-service") + " (now spreading across 3 instances)");
    }
}
```

How to run: `java DiscoveryBackedRoundRobin.java`

`chooseInstance` calls `discover(serviceName)` fresh on every invocation rather than caching a fixed list once — so when `registeredInstances` grows to three entries partway through, subsequent calls' modulo arithmetic automatically adjusts (now `% 3` instead of `% 2`), correctly incorporating the newly-registered instance into the rotation without any code change, exactly mirroring how real client-side load balancing reacts to a fleet's size changing.

### Level 3 — Advanced

```java
// File: SpringCloudLoadBalancerRealShape.java -- the REAL Spring Cloud
// LoadBalancer shape: @LoadBalanced activates client-side load balancing
// for a WebClient, resolved through DiscoveryClient + a configurable strategy.
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.cloud.loadbalancer.annotation.LoadBalancerClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

public class SpringCloudLoadBalancerRealShape {

    @Configuration
    static class WebClientConfig {
        @Bean
        @LoadBalanced // activates client-side load balancing for THIS WebClient.Builder
        public WebClient.Builder loadBalancedWebClientBuilder() {
            return WebClient.builder();
        }
    }

    @Service
    static class OrderClient {
        private final WebClient webClient;
        OrderClient(WebClient.Builder loadBalancedWebClientBuilder) {
            this.webClient = loadBalancedWebClientBuilder.build();
        }

        Mono<String> fetchOrder(String orderId) {
            // "order-service" is a LOGICAL name; client-side LB resolves it to a
            // real, currently-healthy instance address, chosen via round-robin (default)
            return webClient.get()
                .uri("http://order-service/orders/" + orderId)
                .retrieve()
                .bodyToMono(String.class);
        }
    }

    // Custom load-balancing STRATEGY configuration example (zone-preference instead of plain round-robin):
    // @LoadBalancerClient(name = "order-service", configuration = ZonePreferenceLoadBalancerConfig.class)
    // -- would let calls PREFER instances in the caller's own availability zone when available.
}
```

How to run: requires `spring-cloud-starter-loadbalancer`, `spring-boot-starter-webflux`, and a discovery client dependency (Eureka, Consul, or Kubernetes); run in a Spring Boot application registered with the corresponding discovery backend, and repeatedly call `fetchOrder(...)` to observe requests distributed round-robin across the currently-registered `order-service` instances.

`@LoadBalanced` on the `WebClient.Builder` bean is the single annotation that activates client-side load balancing — every call made through `webClient` built from it treats the hostname portion of the URI (`order-service`) as a logical service name rather than a literal DNS hostname, resolved via the same `DiscoveryClient` abstraction discussed for [Spring Cloud Commons](0539-spring-cloud-commons-shared-abstractions.md), with Spring Cloud LoadBalancer's default round-robin strategy choosing which specific instance handles each call.

## 6. Walkthrough

Trace three successive calls to `orderClient.fetchOrder(...)`, assuming two `order-service` instances (`10.0.5.2:8080` and `10.0.5.9:8080`) are currently registered and healthy:

1. **The first call to `fetchOrder("1")` builds a request to `http://order-service/orders/1`.** Because `webClient` was built from the `@LoadBalanced` builder, Spring Cloud LoadBalancer's exchange filter function intercepts this request before it's actually sent, recognizing `order-service` as a logical name.
2. **The filter queries the active `DiscoveryClient` for `order-service`'s current healthy instances**, receiving `[10.0.5.2:8080, 10.0.5.9:8080]` (potentially from a locally-cached, periodically-refreshed list, depending on the discovery backend's client configuration).
3. **The default round-robin strategy selects the first instance in rotation**, say `10.0.5.2:8080`, and the request is actually sent there — `http://10.0.5.2:8080/orders/1`.
4. **The second call to `fetchOrder("2")` repeats steps 1-2**, but the round-robin strategy's internal counter has advanced, so this time it selects `10.0.5.9:8080` — the request goes to `http://10.0.5.9:8080/orders/2`.
5. **The third call to `fetchOrder("3")` wraps back around**, selecting `10.0.5.2:8080` again — over these three calls, load has been distributed roughly evenly between the two instances, entirely through logic running locally within the calling service's own process, with no separate load-balancer server having been involved in any of these three requests at all.

Contrast this with what would happen if these calls instead went through a server-side load balancer (or gateway) in front of `order-service`: each of the three calls above would first travel to that load balancer, which would then forward to a chosen instance — an extra network hop paid on every single one of these three calls, entirely avoided here by resolving and selecting the instance directly within the caller.

## 7. Gotchas & takeaways

> **Gotcha:** client-side load balancing means every calling service needs its own, correctly-configured discovery client integration — if a caller's local discovery cache becomes stale (say, due to a misconfigured refresh interval) it can keep selecting an instance that's actually already unhealthy or gone, a failure mode that's entirely local to that one caller and can be harder to notice than a centralized load balancer's health-check-driven behavior, since there's no single, shared point where "we've stopped routing to this dead instance" is visibly enforced for every caller at once.

- Client-side load balancing eliminates the extra network hop of a separate load-balancer server, at the cost of every calling service needing its own correctly-configured discovery integration.
- `@LoadBalanced` is the marker that activates this behavior for a specific `RestTemplate`/`WebClient.Builder` bean, resolving logical service names via `DiscoveryClient` and choosing an instance via a configurable strategy (round-robin by default).
- Best suited for internal, service-to-service traffic within a fleet already participating in the same service discovery ecosystem; external, edge traffic is still better served by a dedicated [API gateway](0543-spring-cloud-gateway-edge-routing.md).
- Pluggable strategies beyond simple round-robin (zone-aware, weighted) let you tune instance selection for specific topology or capacity concerns, configured per named client via `@LoadBalancerClient`.
