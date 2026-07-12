---
card: microservices
gi: 106
slug: spring-cloud-openfeign-declarative-rest-clients
title: "Spring Cloud OpenFeign declarative REST clients"
---

## 1. What it is

Spring Cloud OpenFeign is a declarative REST client library, predating Spring's own [`@HttpExchange`](0105-spring-http-interface-httpexchange-declarative-clients.md) support, using its own `@FeignClient` annotation on an interface (plus standard Spring MVC annotations like `@GetMapping` reused for the client's own method declarations) to generate a working HTTP client. Its distinguishing feature relative to `@HttpExchange` is deep, built-in integration with the rest of the Spring Cloud ecosystem — particularly automatic client-side load balancing (see [Feign with Spring Cloud LoadBalancer](0107-feign-with-spring-cloud-loadbalancer.md)) when the target is specified as a logical service name rather than a hard-coded URL.

## 2. Why & when

Feign predates `@HttpExchange` by years and was, for a long time, the standard way to build declarative REST clients in the Spring Cloud ecosystem specifically — its `@FeignClient(name = "order-service")` style ties directly into Spring Cloud's [service discovery](service-discovery) and [client-side load balancing](0097-client-side-load-balancing-vs-server-side.md) machinery, resolving `"order-service"` to a concrete, currently-healthy instance address automatically, entirely transparent to the calling code.

Choose Feign specifically when you're already invested in the Spring Cloud ecosystem and want a declarative client with load-balancing and service-discovery integration built in with minimal extra configuration. For new projects not otherwise tied to Spring Cloud's service-discovery stack, Spring's own `@HttpExchange` is generally the leaner, more modern choice with fewer additional dependencies — Feign's main enduring advantage is specifically that tight Spring Cloud ecosystem integration.

## 3. Core concept

`@FeignClient`'s `name` attribute is a *logical* service name, resolved to a concrete instance address by the underlying load-balancer/service-discovery integration at call time — unlike `@HttpExchange`, which is typically configured against one fixed base URL per client.

```java
@FeignClient(name = "order-service")  // logical name, NOT a hard-coded host
interface OrderClient {
    @GetMapping("/orders/{id}")
    Order getOrder(@PathVariable int id);
}

// usage: identical to any other Spring bean
Order order = orderClient.getOrder(42);  // resolves "order-service" to a real instance automatically
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A FeignClient interface named order-service is resolved through a load balancer against a service registry to a concrete instance address at call time">
  <rect x="20" y="60" width="150" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="95" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@FeignClient("order-service")</text>

  <rect x="230" y="30" width="160" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="310" y="58" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service Registry</text>

  <rect x="230" y="100" width="160" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="122" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Load Balancer logic</text>
  <text x="310" y="138" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">picks a concrete instance</text>

  <rect x="450" y="65" width="160" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">order-service-2:8080</text>

  <line x1="170" y1="85" x2="230" y2="55" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="230" y1="55" x2="230" y2="120" stroke="#8b949e" stroke-width="1"/>
  <line x1="170" y1="85" x2="230" y2="125" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="390" y1="125" x2="450" y2="90" stroke="#6db33f" stroke-width="1.5"/>
</svg>

The logical service name is resolved through discovery and load-balancing to one concrete instance per call.

## 5. Runnable example

Scenario: an `OrderClient` interface, first configured against a hard-coded URL (the `@HttpExchange`-style pattern), then switched to a Feign-style logical service name resolved through a simulated registry and load balancer, then extended to show the resolution happening freshly on each call, automatically picking up a newly registered instance without any client reconfiguration.

### Level 1 — Basic

```java
// File: HardCodedUrlClient.java -- the client is configured against ONE
// FIXED URL -- if that instance goes away or a new one is added, the
// client configuration itself must change.
import java.util.*;

public class HardCodedUrlClient {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    static class FixedUrlClient {
        String fixedUrl; // HARD-CODED at construction
        FixedUrlClient(String fixedUrl) { this.fixedUrl = fixedUrl; }
        Order getOrder(int id) {
            System.out.println("  [calling fixed URL: " + fixedUrl + "/orders/" + id + "]");
            return orders.get(id);
        }
    }

    public static void main(String[] args) {
        FixedUrlClient client = new FixedUrlClient("http://order-service-1:8080");
        System.out.println(client.getOrder(42));
    }
}
```

**How to run:** `javac HardCodedUrlClient.java && java HardCodedUrlClient` (JDK 17+).

Expected output:
```
  [calling fixed URL: http://order-service-1:8080/orders/42]
Order[id=42, status=PLACED]
```

### Level 2 — Intermediate

```java
// File: FeignStyleLogicalName.java -- the client is configured against
// a LOGICAL service name; a registry + load balancer resolve it to a
// concrete instance at CALL TIME, not at configuration time.
import java.util.*;

public class FeignStyleLogicalName {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    static class ServiceRegistry {
        Map<String, List<String>> instancesByServiceName = new HashMap<>(Map.of(
            "order-service", List.of("order-service-1:8080", "order-service-2:8080")
        ));
        List<String> resolve(String serviceName) { return instancesByServiceName.get(serviceName); }
    }

    static class LoadBalancer {
        int roundRobinIndex = 0;
        String pick(List<String> instances) {
            String chosen = instances.get(roundRobinIndex % instances.size());
            roundRobinIndex++;
            return chosen;
        }
    }

    static class FeignStyleClient { // stands in for @FeignClient(name = "order-service")
        String serviceName;
        ServiceRegistry registry;
        LoadBalancer loadBalancer;
        FeignStyleClient(String serviceName, ServiceRegistry registry, LoadBalancer loadBalancer) {
            this.serviceName = serviceName; this.registry = registry; this.loadBalancer = loadBalancer;
        }
        Order getOrder(int id) {
            String instance = loadBalancer.pick(registry.resolve(serviceName)); // resolved FRESH each call
            System.out.println("  [resolved '" + serviceName + "' -> " + instance + ", GET /orders/" + id + "]");
            return orders.get(id);
        }
    }

    public static void main(String[] args) {
        FeignStyleClient client = new FeignStyleClient("order-service", new ServiceRegistry(), new LoadBalancer());
        System.out.println(client.getOrder(42));
        System.out.println(client.getOrder(42)); // a SECOND call -- resolves to a DIFFERENT instance
    }
}
```

**How to run:** `javac FeignStyleLogicalName.java && java FeignStyleLogicalName` (JDK 17+).

Expected output:
```
  [resolved 'order-service' -> order-service-1:8080, GET /orders/42]
Order[id=42, status=PLACED]
  [resolved 'order-service' -> order-service-2:8080, GET /orders/42]
Order[id=42, status=PLACED]
```

### Level 3 — Advanced

```java
// File: DynamicInstanceRegistration.java -- a NEW instance registers
// itself AFTER the client was already constructed -- the client picks it
// up automatically on the next call, with ZERO client reconfiguration,
// because resolution happens fresh every time, not once at startup.
import java.util.*;

public class DynamicInstanceRegistration {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    static class ServiceRegistry {
        Map<String, List<String>> instancesByServiceName = new HashMap<>();
        ServiceRegistry() { instancesByServiceName.put("order-service", new ArrayList<>(List.of("order-service-1:8080"))); }
        List<String> resolve(String serviceName) { return instancesByServiceName.get(serviceName); }
        void register(String serviceName, String instance) { instancesByServiceName.get(serviceName).add(instance); }
    }

    static class LoadBalancer {
        int roundRobinIndex = 0;
        String pick(List<String> instances) {
            String chosen = instances.get(roundRobinIndex % instances.size());
            roundRobinIndex++;
            return chosen;
        }
    }

    static class FeignStyleClient {
        String serviceName; ServiceRegistry registry; LoadBalancer loadBalancer;
        FeignStyleClient(String serviceName, ServiceRegistry registry, LoadBalancer loadBalancer) {
            this.serviceName = serviceName; this.registry = registry; this.loadBalancer = loadBalancer;
        }
        Order getOrder(int id) {
            String instance = loadBalancer.pick(registry.resolve(serviceName));
            System.out.println("  [resolved '" + serviceName + "' -> " + instance + "]");
            return orders.get(id);
        }
    }

    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();
        FeignStyleClient client = new FeignStyleClient("order-service", registry, new LoadBalancer());

        client.getOrder(42); // only 1 instance registered so far
        client.getOrder(42); // still only order-service-1

        System.out.println("--- order-service-2 registers itself dynamically ---");
        registry.register("order-service", "order-service-2:8080"); // client was NEVER reconfigured

        client.getOrder(42); // NOW picks up the new instance automatically
        client.getOrder(42);
    }
}
```

**How to run:** `javac DynamicInstanceRegistration.java && java DynamicInstanceRegistration` (JDK 17+).

Expected output:
```
  [resolved 'order-service' -> order-service-1:8080]
  [resolved 'order-service' -> order-service-1:8080]
--- order-service-2 registers itself dynamically ---
  [resolved 'order-service' -> order-service-1:8080]
  [resolved 'order-service' -> order-service-2:8080]
```

## 6. Walkthrough

1. **Level 1** — `FixedUrlClient` is constructed with a hard-coded `fixedUrl` string, and every call uses that exact URL. `main` calls `getOrder(42)` and the diagnostic shows the same fixed address every time — if `order-service-1` ever became unavailable or a second instance were added, this client's configuration itself would need to change to reflect that.
2. **Level 2 — resolving a logical name at call time** — `FeignStyleClient` is constructed with a `serviceName` string (`"order-service"`) rather than a concrete URL, plus references to a `ServiceRegistry` and `LoadBalancer`. Each call to `getOrder` calls `registry.resolve(serviceName)` to get the *current* list of instances, then `loadBalancer.pick(...)` to choose one — this resolution happens fresh on *every* call, not once at construction time. `main` calls `getOrder(42)` twice; the round-robin `LoadBalancer` picks `order-service-1` on the first call and `order-service-2` on the second, demonstrating that the client is genuinely spreading its calls across the registry's current instance list rather than being pinned to one.
3. **Level 3 — an instance appearing after the client was built** — `registry` starts with only `"order-service-1:8080"` registered. `main` calls `client.getOrder(42)` twice, and both resolve to `order-service-1` (the only instance available at that point) — the round-robin logic still increments its index each call, but with only one instance in the list, every index maps back to that same one instance.
4. **Tracing the dynamic registration** — after the two initial calls, `main` calls `registry.register("order-service", "order-service-2:8080")`, adding a second instance to the registry's list for `"order-service"` — critically, without touching `client` at all; `client`'s own fields (`serviceName`, `registry`, `loadBalancer`) are completely unchanged by this registration. The third call to `getOrder` calls `registry.resolve("order-service")` again, which *now* returns both instances, and the load balancer's round-robin index (having advanced twice already) picks `order-service-1` again for this third call, then `order-service-2` for the fourth.
5. **Why this matters for real Feign clients backed by service discovery** — this is exactly the behavior `@FeignClient(name = "order-service")` provides when paired with Spring Cloud's service discovery: a new instance registering itself (typically via a heartbeat to a registry like Eureka or Consul) becomes available to every existing Feign client automatically, on their very next call, with zero client-side reconfiguration or redeployment needed — the client was never told about specific instance addresses in the first place, only the logical service name it should resolve fresh every time.

## 7. Gotchas & takeaways

> **Gotcha:** Feign's `@FeignClient(name = "order-service")` style ties the client directly to Spring Cloud's service-discovery machinery (a registry like Eureka/Consul must actually be running and populated) — using Feign purely for its declarative interface style against a fixed URL, without ever using the logical-name/discovery integration, forfeits Feign's main distinguishing advantage over the simpler `@HttpExchange` approach.

- Feign predates `@HttpExchange` and remains distinguished mainly by its tight, built-in Spring Cloud service-discovery and load-balancing integration.
- `@FeignClient(name = "...")`'s logical service name is resolved to a concrete instance address fresh on every call, not fixed at client construction time — this is what lets new instances join rotation automatically.
- For projects not otherwise using Spring Cloud's service-discovery stack, Spring's own [`@HttpExchange`](0105-spring-http-interface-httpexchange-declarative-clients.md) is generally the leaner modern choice, with fewer additional dependencies.
- See [Feign with Spring Cloud LoadBalancer](0107-feign-with-spring-cloud-loadbalancer.md) for the specific load-balancing integration that makes Feign's logical-name resolution work, and [client-side load balancing](0097-client-side-load-balancing-vs-server-side.md) for the broader concept it implements.
- Dynamic instance registration (a new instance joining rotation with zero client reconfiguration) is a direct, practical benefit of resolving the target fresh on every call rather than caching a fixed address.
