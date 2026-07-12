---
card: microservices
gi: 107
slug: feign-with-spring-cloud-loadbalancer
title: "Feign with Spring Cloud LoadBalancer"
---

## 1. What it is

Spring Cloud LoadBalancer is the client-side load-balancing component that [Spring Cloud OpenFeign](0106-spring-cloud-openfeign-declarative-rest-clients.md) uses under the hood to resolve a `@FeignClient`'s logical service name into a concrete instance address on every call. When a `@FeignClient(name = "order-service")` interface's method is invoked, Spring Cloud LoadBalancer intercepts the call, queries the current service discovery client for `"order-service"`'s known instances, applies a load-balancing strategy (round-robin by default) to pick one, and only then does the actual HTTP call go out to that specific instance.

## 2. Why & when

Without a load-balancing layer, a `@FeignClient` configured with a logical name would have no mechanism to actually turn that name into a real address — the logical name is meaningless without something translating it. Spring Cloud LoadBalancer is that translation layer specifically for the Spring Cloud ecosystem, replacing the older, now-deprecated Netflix Ribbon library, and it's what makes [client-side load balancing](0097-client-side-load-balancing-vs-server-side.md) concretely happen for Feign (and other Spring Cloud-aware clients like a load-balanced `RestClient`/`WebClient`) rather than being an abstract idea.

This component is automatically active whenever you use `@FeignClient` with a logical service name inside a Spring Cloud application with `spring-cloud-starter-loadbalancer` on the classpath — you typically don't invoke it directly, but understanding its mechanism (query discovery, apply a strategy, pick one instance, per call) clarifies exactly what's happening whenever a `@FeignClient` method is called.

## 3. Core concept

The load balancer sits between the Feign-generated proxy and the actual network call, intercepting every invocation to resolve the target instance fresh, and — critically — this per-call resolution is what lets it also skip an instance it has separately learned is unhealthy.

```
FeignClient.getOrder(42)
        |
   Spring Cloud LoadBalancer intercepts
        |
   query ServiceDiscovery for "order-service" instances
        |
   apply strategy (round-robin, or skip known-unhealthy) -> pick ONE instance
        |
   actual HTTP call goes to THAT instance
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Feign client call is intercepted by Spring Cloud LoadBalancer, which queries service discovery and applies a strategy to select one healthy instance before the actual HTTP call proceeds">
  <rect x="20" y="60" width="130" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="85" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">FeignClient call</text>

  <rect x="190" y="45" width="180" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="280" y="68" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring Cloud</text>
  <text x="280" y="83" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">LoadBalancer</text>
  <text x="280" y="103" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">query + strategy + pick</text>

  <rect x="410" y="20" width="200" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Service Discovery</text>

  <rect x="410" y="110" width="200" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="135" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">chosen instance</text>

  <line x1="150" y1="85" x2="190" y2="85" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="370" y1="65" x2="410" y2="40" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="370" y1="105" x2="410" y2="130" stroke="#6db33f" stroke-width="1.5"/>
</svg>

The load balancer intercepts every Feign call to translate a logical name into a concrete, currently-healthy target.

## 5. Runnable example

Scenario: a `@FeignClient`-style call, first with no load-balancing interception at all (a hard-coded target, showing what's missing), then with `LoadBalancer` interception added, querying discovery and applying round-robin, then extended so the load balancer also tracks and skips an instance it has learned is unhealthy — the practical combination of [client-side load balancing](0097-client-side-load-balancing-vs-server-side.md)'s two concerns working together specifically within the Feign call path.

### Level 1 — Basic

```java
// File: NoLoadBalancerInterception.java -- the Feign-style call goes
// DIRECTLY to a hard-coded target -- no interception, no resolution step.
public class NoLoadBalancerInterception {
    static class FeignStyleClient {
        String getOrder(int id) {
            String target = "order-service-1:8080"; // HARD-CODED -- nothing resolves this
            return "called " + target + " for order " + id;
        }
    }

    public static void main(String[] args) {
        FeignStyleClient client = new FeignStyleClient();
        System.out.println(client.getOrder(42));
    }
}
```

**How to run:** `javac NoLoadBalancerInterception.java && java NoLoadBalancerInterception` (JDK 17+).

Expected output:
```
called order-service-1:8080 for order 42
```

### Level 2 — Intermediate

```java
// File: LoadBalancerInterception.java -- the LoadBalancer INTERCEPTS the
// call, queries discovery, applies round-robin -- exactly the mechanism
// behind a @FeignClient(name = "order-service") call.
import java.util.*;

public class LoadBalancerInterception {
    static class ServiceDiscovery {
        List<String> instancesFor(String serviceName) {
            return List.of("order-service-1:8080", "order-service-2:8080", "order-service-3:8080");
        }
    }

    static class SpringCloudLoadBalancer {
        ServiceDiscovery discovery;
        int roundRobinIndex = 0;
        SpringCloudLoadBalancer(ServiceDiscovery discovery) { this.discovery = discovery; }

        String choose(String serviceName) { // THE INTERCEPTION POINT
            List<String> instances = discovery.instancesFor(serviceName);
            String chosen = instances.get(roundRobinIndex % instances.size());
            roundRobinIndex++;
            return chosen;
        }
    }

    static class FeignStyleClient {
        SpringCloudLoadBalancer loadBalancer;
        FeignStyleClient(SpringCloudLoadBalancer loadBalancer) { this.loadBalancer = loadBalancer; }
        String getOrder(int id) {
            String target = loadBalancer.choose("order-service"); // resolved via the load balancer, not hard-coded
            return "called " + target + " for order " + id;
        }
    }

    public static void main(String[] args) {
        FeignStyleClient client = new FeignStyleClient(new SpringCloudLoadBalancer(new ServiceDiscovery()));
        for (int i = 0; i < 3; i++) System.out.println(client.getOrder(42));
    }
}
```

**How to run:** `javac LoadBalancerInterception.java && java LoadBalancerInterception` (JDK 17+).

Expected output:
```
called order-service-1:8080 for order 42
called order-service-2:8080 for order 42
called order-service-3:8080 for order 42
```

### Level 3 — Advanced

```java
// File: SkippingUnhealthyInstance.java -- the LoadBalancer ALSO tracks
// instances it has learned are unhealthy (via a failed call) and skips
// them on future selections -- combining round-robin with health awareness.
import java.util.*;

public class SkippingUnhealthyInstance {
    static class ServiceDiscovery {
        List<String> instancesFor(String serviceName) {
            return List.of("order-service-1:8080", "order-service-2:8080", "order-service-3:8080");
        }
    }

    static class SpringCloudLoadBalancer {
        ServiceDiscovery discovery;
        int roundRobinIndex = 0;
        Set<String> knownUnhealthy = new HashSet<>();
        SpringCloudLoadBalancer(ServiceDiscovery discovery) { this.discovery = discovery; }

        String choose(String serviceName) {
            List<String> healthy = new ArrayList<>();
            for (String instance : discovery.instancesFor(serviceName)) {
                if (!knownUnhealthy.contains(instance)) healthy.add(instance);
            }
            String chosen = healthy.get(roundRobinIndex % healthy.size());
            roundRobinIndex++;
            return chosen;
        }

        void markUnhealthy(String instance) { knownUnhealthy.add(instance); }
    }

    static class FeignStyleClient {
        SpringCloudLoadBalancer loadBalancer;
        FeignStyleClient(SpringCloudLoadBalancer loadBalancer) { this.loadBalancer = loadBalancer; }

        String getOrder(int id) {
            String target = loadBalancer.choose("order-service");
            if (target.equals("order-service-2:8080")) { // simulate: instance 2 is flaky
                loadBalancer.markUnhealthy(target);
                return "call to " + target + " FAILED -- marked unhealthy";
            }
            return "called " + target + " for order " + id;
        }
    }

    public static void main(String[] args) {
        FeignStyleClient client = new FeignStyleClient(new SpringCloudLoadBalancer(new ServiceDiscovery()));
        for (int i = 0; i < 4; i++) System.out.println(client.getOrder(42));
    }
}
```

**How to run:** `javac SkippingUnhealthyInstance.java && java SkippingUnhealthyInstance` (JDK 17+).

Expected output:
```
called order-service-1:8080 for order 42
call to order-service-2:8080 FAILED -- marked unhealthy
called order-service-1:8080 for order 42
called order-service-3:8080 for order 42
```

## 6. Walkthrough

1. **Level 1** — `getOrder` uses a hard-coded `target` string directly — there's no discovery, no strategy, no interception step of any kind. `main` calls it once and gets back a message referencing that fixed target — this is what a `@FeignClient` call would look like if it had no load-balancer integration wired in at all (essentially, a plain point-to-point client).
2. **Level 2 — inserting the interception point** — `SpringCloudLoadBalancer.choose(serviceName)` is the method standing in for what Spring Cloud LoadBalancer does automatically behind a `@FeignClient(name = "order-service")` call: query `ServiceDiscovery` for the service's current instance list, then apply round-robin selection. `FeignStyleClient.getOrder` now calls `loadBalancer.choose("order-service")` instead of using any hard-coded target. `main` calls `getOrder` three times, and the printed targets cycle through all three registered instances in turn — demonstrating the load balancer genuinely spreading calls across the discovered instance pool.
3. **Level 3 — combining round-robin with health tracking** — `SpringCloudLoadBalancer` gains a `knownUnhealthy` set and a `markUnhealthy` method, alongside a `choose` method that now filters the discovered instance list down to only healthy ones before applying round-robin — mirroring how a real load balancer combines instance selection with health awareness (whether learned from failed calls directly, as here, or from separate active health checks).
4. **Tracing the four calls** — call 1: `healthy` is all three instances, `roundRobinIndex % 3 = 0`, chosen is `order-service-1`, `getOrder` sees it's not the flaky one, returns success, `roundRobinIndex` becomes 1. Call 2: still all three healthy (nothing marked yet), `1 % 3 = 1`, chosen is `order-service-2`, `getOrder`'s check matches the flaky-instance condition, calls `loadBalancer.markUnhealthy("order-service-2:8080")`, and returns the failure message, `roundRobinIndex` becomes 2. Call 3: `healthy` is now filtered down to `[order-service-1, order-service-3]` (instance 2 excluded), `roundRobinIndex` is 2, `2 % 2 = 0`, chosen is `healthy.get(0)`, which is `order-service-1` again, `roundRobinIndex` becomes 3. Call 4: `healthy` is still `[order-service-1, order-service-3]`, `3 % 2 = 1`, chosen is `healthy.get(1)`, which is `order-service-3`.
5. **The general mechanism this demonstrates regardless of the exact indices** — once an instance is marked unhealthy, it's excluded from the `healthy` list on every subsequent `choose` call, so round-robin only cycles among instances currently believed healthy — combining the "spread load evenly" benefit of round-robin with the "don't send traffic to something known to be broken" benefit of health tracking, both happening automatically inside the load balancer's interception point, invisible to `FeignStyleClient.getOrder`'s own calling code.

## 7. Gotchas & takeaways

> **Gotcha:** health tracking based purely on a client's own observed call failures (as modeled here) never re-includes a genuinely recovered instance without some separate expiration or active re-check mechanism — see the identical caution in [client-side load balancing](0097-client-side-load-balancing-vs-server-side.md) for the same underlying issue.

- Spring Cloud LoadBalancer is the component that actually resolves a `@FeignClient`'s logical service name into a concrete instance address, replacing the older, deprecated Netflix Ribbon.
- It intercepts every call to query current service discovery data and apply a load-balancing strategy (round-robin by default), fresh on each invocation.
- Combining round-robin selection with health-awareness (skipping instances known to be failing) is a natural, common pairing — both concerns live inside the same interception point.
- This entire mechanism is what makes [Feign's logical-name resolution](0106-spring-cloud-openfeign-declarative-rest-clients.md) actually work — the `@FeignClient` annotation alone declares intent; Spring Cloud LoadBalancer is what fulfills it.
- See [client-side load balancing vs server-side](0097-client-side-load-balancing-vs-server-side.md) for the broader conceptual comparison this component is a concrete Spring Cloud implementation of.
