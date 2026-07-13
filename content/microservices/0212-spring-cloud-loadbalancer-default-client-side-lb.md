---
card: microservices
gi: 212
slug: spring-cloud-loadbalancer-default-client-side-lb
title: "Spring Cloud LoadBalancer (default client-side LB)"
---

## 1. What it is

Spring Cloud LoadBalancer is Spring Cloud's own default client-side load-balancing implementation — replacing the older, now-deprecated Netflix Ribbon — providing round-robin selection out of the box, built directly on the [`DiscoveryClient`](0200-spring-cloud-discoveryclient-abstraction.md) abstraction, and integrating transparently with `@LoadBalanced` `RestTemplate`/`WebClient` exactly as described for [Spring Cloud LoadBalancer using the registry](0202-spring-cloud-loadbalancer-using-the-registry.md), with round-robin as its configurable default algorithm.

## 2. Why & when

Netflix Ribbon, the previous default client-side load balancer in the Spring Cloud ecosystem, entered maintenance mode as Netflix moved away from actively developing it, and Spring Cloud needed a modern, actively-maintained replacement built natively on its own `DiscoveryClient` and reactive foundations rather than depending on an externally-maintained, increasingly stagnant library. Spring Cloud LoadBalancer is that replacement: a from-scratch implementation designed specifically for Spring Cloud's current architecture, providing the same essential capability (client-side selection among discovered instances) with round-robin as a sensible, simple default and a pluggable architecture for customization.

Use Spring Cloud LoadBalancer as the default choice for client-side load balancing in any current Spring Cloud application — it's automatically included and activated when `@LoadBalanced` is used with `RestTemplate` or `WebClient`, requiring no additional configuration for the common case. Reach for custom configuration (covered in [custom LoadBalancer configuration](0214-custom-loadbalancer-configuration-serviceinstancelistsupplie.md)) only when the default round-robin behavior genuinely doesn't fit a specific use case's needs.

## 3. Core concept

Spring Cloud LoadBalancer's default `RoundRobinLoadBalancer` implementation maintains a rotating index per service, resolved via `DiscoveryClient`-provided instances, and this entire mechanism activates automatically the moment `@LoadBalanced` is applied to a `RestTemplate` or `WebClient` bean, with zero additional configuration required for standard round-robin behavior.

```java
@Bean
@LoadBalanced // activates Spring Cloud LoadBalancer AUTOMATICALLY, round-robin by default
public RestTemplate restTemplate() { return new RestTemplate(); }

// application code: calls a logical name, gets ROUND-ROBIN distribution across
// DiscoveryClient-resolved instances, with ZERO explicit load-balancing code
String response = restTemplate.getForObject("http://order-service/orders/42", String.class);
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An @LoadBalanced RestTemplate call is intercepted by Spring Cloud LoadBalancer, which uses DiscoveryClient to resolve the current instances and its default RoundRobinLoadBalancer to select one, requiring zero explicit balancing code from the application" >
  <rect x="20" y="55" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@LoadBalanced call</text>

  <rect x="230" y="30" width="180" height="90" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#8b949e" font-size="8" font-family="sans-serif">Spring Cloud LoadBalancer</text>
  <text x="250" y="75" fill="#e6edf3" font-size="7.5" font-family="sans-serif">DiscoveryClient.getInstances()</text>
  <text x="250" y="100" fill="#e6edf3" font-size="7.5" font-family="sans-serif">RoundRobinLoadBalancer.choose()</text>

  <rect x="470" y="55" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Chosen instance</text>

  <line x1="170" y1="77" x2="228" y2="77" stroke="#8b949e" marker-end="url(#arr91)"/>
  <line x1="410" y1="77" x2="468" y2="77" stroke="#8b949e" marker-end="url(#arr91)"/>

  <defs>
    <marker id="arr91" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Discovery resolution and round-robin selection both happen automatically inside the `@LoadBalanced` mechanism.

## 5. Runnable example

Scenario: an order-lookup call that starts with a legacy-style, hand-integrated third-party balancing library (contrasting with the modern replacement), models Spring Cloud LoadBalancer's default round-robin activation via `@LoadBalanced`, and finally demonstrates the built-in default working correctly across a realistic call volume with zero custom configuration, confirming the "just works out of the box" default experience.

### Level 1 — Basic

```java
// File: LegacyThirdPartyLibraryIntegration.java -- models the OLDER pattern:
// a SEPARATE, externally-maintained library needing its OWN manual integration.
import java.util.*;

public class LegacyThirdPartyLibraryIntegration {
    // stands in for the OLDER Netflix Ribbon-style integration -- required its OWN
    // configuration classes, its OWN client wrapper, and was in MAINTENANCE MODE
    static class LegacyRibbonClient {
        List<String> instances = List.of("order-a", "order-b");
        int index = 0;
        String choose() { return instances.get(index++ % instances.size()); }
        // + ribbon.NFLoadBalancerRuleClassName config, + separate client per service, + more legacy ceremony
    }

    public static void main(String[] args) {
        LegacyRibbonClient client = new LegacyRibbonClient();
        System.out.println("Legacy client chose: " + client.choose());
        System.out.println("This depended on a SEPARATE, increasingly stagnant third-party library requiring its OWN integration ceremony.");
    }
}
```

**How to run:** `javac LegacyThirdPartyLibraryIntegration.java && java LegacyThirdPartyLibraryIntegration` (JDK 17+).

### Level 2 — Intermediate

```java
// File: SpringCloudLoadBalancerDefault.java -- models Spring Cloud
// LoadBalancer's DEFAULT activation: round-robin, built NATIVELY on
// DiscoveryClient, activated by ONE annotation, NO third-party library.
import java.util.*;
import java.util.function.*;

public class SpringCloudLoadBalancerDefault {
    record ServiceInstance(String host, int port) {}
    interface DiscoveryClient { List<ServiceInstance> getInstances(String serviceId); }

    static class SimpleDiscoveryClient implements DiscoveryClient {
        public List<ServiceInstance> getInstances(String serviceId) { return List.of(new ServiceInstance("10.0.1.5", 8080), new ServiceInstance("10.0.1.6", 8080)); }
    }

    // models Spring Cloud LoadBalancer's built-in RoundRobinLoadBalancer -- the NATIVE, DEFAULT implementation
    static class RoundRobinLoadBalancer {
        DiscoveryClient discoveryClient;
        int index = 0;
        RoundRobinLoadBalancer(DiscoveryClient discoveryClient) { this.discoveryClient = discoveryClient; }
        ServiceInstance choose(String serviceId) {
            List<ServiceInstance> instances = discoveryClient.getInstances(serviceId);
            return instances.get(index++ % instances.size());
        }
    }

    // models an @LoadBalanced RestTemplate -- INTERCEPTS logical-name calls automatically
    static class LoadBalancedRestTemplate {
        RoundRobinLoadBalancer loadBalancer;
        LoadBalancedRestTemplate(RoundRobinLoadBalancer loadBalancer) { this.loadBalancer = loadBalancer; }
        String getForObject(String serviceIdAndPath) {
            String[] parts = serviceIdAndPath.split("/", 2);
            ServiceInstance chosen = loadBalancer.choose(parts[0]);
            return "GET " + chosen.host() + ":" + chosen.port() + "/" + parts[1];
        }
    }

    public static void main(String[] args) {
        LoadBalancedRestTemplate restTemplate = new LoadBalancedRestTemplate(new RoundRobinLoadBalancer(new SimpleDiscoveryClient()));

        System.out.println(restTemplate.getForObject("order-service/orders/42"));
        System.out.println(restTemplate.getForObject("order-service/orders/43"));
        System.out.println("ROUND-ROBIN, out of the box, built on DiscoveryClient natively -- ZERO third-party library, ZERO extra configuration.");
    }
}
```

**How to run:** `javac SpringCloudLoadBalancerDefault.java && java SpringCloudLoadBalancerDefault` (JDK 17+).

Expected output:
```
GET 10.0.1.5:8080/orders/42
GET 10.0.1.6:8080/orders/43
ROUND-ROBIN, out of the box, built on DiscoveryClient natively -- ZERO third-party library, ZERO extra configuration.
```

### Level 3 — Advanced

```java
// File: DefaultBehaviorAtRealisticVolume.java -- confirms the DEFAULT
// round-robin behavior produces PERFECTLY even distribution at a REALISTIC
// call volume, with NO custom configuration -- the "just works" default experience.
import java.util.*;

public class DefaultBehaviorAtRealisticVolume {
    record ServiceInstance(String host, int port) {}
    interface DiscoveryClient { List<ServiceInstance> getInstances(String serviceId); }

    static class SimpleDiscoveryClient implements DiscoveryClient {
        public List<ServiceInstance> getInstances(String serviceId) {
            return List.of(new ServiceInstance("10.0.1.5", 8080), new ServiceInstance("10.0.1.6", 8080), new ServiceInstance("10.0.1.7", 8080));
        }
    }

    static class RoundRobinLoadBalancer {
        DiscoveryClient discoveryClient;
        int index = 0;
        RoundRobinLoadBalancer(DiscoveryClient discoveryClient) { this.discoveryClient = discoveryClient; }
        ServiceInstance choose(String serviceId) {
            List<ServiceInstance> instances = discoveryClient.getInstances(serviceId);
            return instances.get(index++ % instances.size());
        }
    }

    public static void main(String[] args) {
        RoundRobinLoadBalancer loadBalancer = new RoundRobinLoadBalancer(new SimpleDiscoveryClient()); // DEFAULT, no customization

        Map<String, Integer> callCounts = new TreeMap<>();
        int totalCalls = 900;
        for (int i = 0; i < totalCalls; i++) {
            ServiceInstance chosen = loadBalancer.choose("order-service");
            callCounts.merge(chosen.host(), 1, Integer::sum);
        }

        System.out.println("Distribution across " + totalCalls + " calls (DEFAULT round-robin, NO configuration): " + callCounts);
        boolean perfectlyEven = callCounts.values().stream().allMatch(count -> count == totalCalls / 3);
        System.out.println("Perfectly even: " + perfectlyEven + " -- the DEFAULT is production-ready without any tuning for a uniform-capacity fleet.");
    }
}
```

**How to run:** `javac DefaultBehaviorAtRealisticVolume.java && java DefaultBehaviorAtRealisticVolume` (JDK 17+).

Expected output:
```
Distribution across 900 calls (DEFAULT round-robin, NO configuration): {10.0.1.5=300, 10.0.1.6=300, 10.0.1.7=300}
Perfectly even: true -- the DEFAULT is production-ready without any tuning for a uniform-capacity fleet.
```

## 6. Walkthrough

1. **Level 1** — `LegacyRibbonClient` represents the older Netflix Ribbon integration pattern, and its code comment enumerates the additional ceremony that approach historically required (specific configuration properties, per-service client wrappers) beyond what Spring Cloud LoadBalancer needs today.
2. **Level 2, the default implementation built on `DiscoveryClient`** — `RoundRobinLoadBalancer` takes a `DiscoveryClient` directly in its constructor and implements `choose` using only that interface, mirroring how Spring Cloud LoadBalancer's actual default implementation is built natively against the same abstraction covered earlier, rather than against any external, separately-maintained library.
3. **Level 2, the `@LoadBalanced` interception modeled** — `LoadBalancedRestTemplate.getForObject` parses a combined service-name-and-path string and delegates instance resolution and selection entirely to `loadBalancer`, mirroring how a real `@LoadBalanced RestTemplate` transparently intercepts calls to logical service names.
4. **Level 2, the demonstrated simplicity** — `main` constructs the load-balanced client with a single line and immediately makes two calls that correctly alternate between the two discovered instances, with the final comment emphasizing that this required zero third-party library integration or extra configuration beyond the default setup.
5. **Level 3, scaling to a realistic call volume** — `totalCalls` is set to 900 (cleanly divisible by the three-instance discovery result), and the loop calls `loadBalancer.choose("order-service")` that many times, tallying results per host.
6. **Level 3, verifying exact, even distribution** — `perfectlyEven` checks that every instance's count equals exactly `totalCalls / 3` (300); because the round-robin index increments deterministically on every call, this exact, non-approximate distribution is guaranteed by construction, not merely statistically likely.
7. **Level 3, the "just works" default experience confirmed** — the final printed statement makes the practical point explicit: for a fleet of instances with genuinely uniform capacity (the common case), Spring Cloud LoadBalancer's default round-robin behavior, activated purely by adding `@LoadBalanced` with no further configuration, produces exactly the even distribution a well-functioning load balancer should provide — custom configuration, covered separately, becomes relevant only once this default behavior genuinely doesn't fit a specific, non-uniform scenario.

## 7. Gotchas & takeaways

> **Gotcha:** Spring Cloud LoadBalancer's default `RoundRobinLoadBalancer` does not incorporate health status filtering or zone awareness out of the box in its most basic configuration — achieving [health-check-aware](0209-health-check-aware-load-balancing.md) or [zone-aware](0207-zone-locality-aware-load-balancing.md) behavior typically requires either relying on the underlying `DiscoveryClient` implementation to already filter unhealthy instances (which most production-grade registry integrations do) or configuring additional `ServiceInstanceListSupplier` filtering explicitly, rather than assuming the default balancer alone provides these capabilities.

- Spring Cloud LoadBalancer is Spring Cloud's modern, natively-built default client-side load balancer, replacing the deprecated, externally-maintained Netflix Ribbon.
- It provides round-robin selection out of the box, built directly on the `DiscoveryClient` abstraction, and activates automatically wherever `@LoadBalanced` is applied to a `RestTemplate` or `WebClient`.
- This requires zero additional configuration for standard, uniform-capacity load distribution — the default behavior is production-ready as-is for that common case.
- Being built natively on Spring Cloud's own `DiscoveryClient` abstraction, rather than depending on an external, increasingly stagnant library, is the core architectural improvement over the older Ribbon-based approach.
- The default round-robin implementation doesn't automatically add health-check awareness or zone locality on its own — those capabilities depend on either the underlying `DiscoveryClient`'s own filtering or additional explicit configuration.
