---
card: spring-cloud
gi: 29
slug: eureka-client-registration-discovery
title: "Eureka Client registration & discovery"
---

## 1. What it is

Eureka Client is the library side of the previous card's story: add `spring-cloud-starter-netflix-eureka-client` to a service and configure `eureka.client.service-url.defaultZone`, and that service automatically registers itself with Eureka Server on startup, sends heartbeats in the background, and gains the ability to look up *other* registered services by name instead of by hardcoded address.

```properties
spring.application.name=orders-service
eureka.client.service-url.defaultZone=http://localhost:8761/eureka/
```

No extra annotation is required to register — adding the client dependency and pointing it at a Eureka Server is enough; `@EnableDiscoveryClient` (covered earlier in Spring Cloud Commons) makes the intent explicit but Spring Boot autoconfigures it either way when the starter is on the classpath.

## 2. Why & when

Eureka Server (the previous card) is only useful once something registers with it and something else queries it. Eureka Client is that "something": every instance of every service links this in so it both announces itself and can resolve other services by name. This closes the loop between "the registry exists" and "callers actually use it instead of hardcoded URLs."

Reach for Eureka Client when:

- A service needs to be discoverable by other services — it should register itself, rather than an operator manually configuring every caller with its address.
- A service needs to call other services by logical name (`billing-service`) and let the client resolve that name to a live instance, rather than embedding IP addresses or hostnames in configuration.
- You want registration and heartbeating handled automatically by a background thread, without hand-rolling that logic in application code.

## 3. Core concept

```
   Eureka Client (inside orders-service)
        |
        |--- on startup: POST /eureka/apps/ORDERS-SERVICE  (register)
        |--- every 30s:  PUT  /eureka/apps/ORDERS-SERVICE/{id}  (heartbeat)
        |--- on demand:  GET  /eureka/apps/BILLING-SERVICE  (discover)
        |--- on shutdown: DELETE /eureka/apps/ORDERS-SERVICE/{id}  (deregister)
```

The client is symmetric: the same library both publishes this instance's presence and resolves other instances' presence, using the same registry.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="orders-service registers itself with Eureka Server, then queries the same server to discover billing-service before calling it directly">
  <rect x="30" y="90" width="140" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="115" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">orders-service</text>

  <rect x="250" y="20" width="140" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Eureka Server</text>

  <rect x="470" y="90" width="140" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="115" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">billing-service</text>

  <line x1="130" y1="90" x2="280" y2="60" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a29)"/>
  <text x="170" y="75" fill="#8b949e" font-size="7" font-family="sans-serif">1. register</text>

  <line x1="540" y1="90" x2="360" y2="60" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a29)"/>
  <text x="480" y="75" fill="#8b949e" font-size="7" font-family="sans-serif">1. register</text>

  <line x1="150" y1="90" x2="290" y2="65" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="3,3" marker-end="url(#a29)"/>
  <text x="150" y="150" fill="#8b949e" font-size="7" font-family="sans-serif">2. "who is billing-service?"</text>

  <line x1="170" y1="115" x2="465" y2="115" stroke="#79c0ff" stroke-width="1.4" marker-end="url(#a29)"/>
  <text x="320" y="175" fill="#8b949e" font-size="7" font-family="sans-serif">3. direct call to resolved address</text>

  <defs><marker id="a29" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both services register with the shared server; a caller then discovers and calls the other directly — traffic never flows through Eureka itself.

## 5. Runnable example

The scenario: `orders-service` needs to call `billing-service`. Start with a hardcoded address, then add self-registration and discovery, then add client-side load balancing across multiple discovered instances.

### Level 1 — Basic

Hardcoded address — the problem this feature solves.

```java
public class EurekaClientLevel1 {
    static String BILLING_SERVICE_URL = "http://10.0.2.1:8080"; // hardcoded -- breaks if it moves

    static String callBilling(String orderId) {
        return "GET " + BILLING_SERVICE_URL + "/invoices/" + orderId;
    }

    public static void main(String[] args) {
        System.out.println(callBilling("order-42"));
    }
}
```

How to run: `java EurekaClientLevel1.java`

If `billing-service` restarts on a different host, or scales to a second instance, this hardcoded URL is now wrong or incomplete, and nothing in `orders-service` knows about it.

### Level 2 — Intermediate

Add a shared registry (standing in for Eureka Server) that both services register with, and resolve `billing-service` by name instead of by hardcoded address.

```java
import java.util.*;

public class EurekaClientLevel2 {
    static Map<String, List<String>> registry = new HashMap<>();

    static void register(String service, String address) {
        registry.computeIfAbsent(service, k -> new ArrayList<>()).add(address);
        System.out.println(service + " registered at " + address);
    }

    static Optional<String> discoverOne(String service) {
        List<String> instances = registry.getOrDefault(service, List.of());
        return instances.isEmpty() ? Optional.empty() : Optional.of(instances.get(0));
    }

    static String callBilling(String orderId) {
        String address = discoverOne("billing-service")
                .orElseThrow(() -> new IllegalStateException("no instances of billing-service"));
        return "GET " + address + "/invoices/" + orderId;
    }

    public static void main(String[] args) {
        register("orders-service", "10.0.1.5:8080");
        register("billing-service", "10.0.2.1:8080");

        System.out.println(callBilling("order-42"));
    }
}
```

How to run: `java EurekaClientLevel2.java`

`register` models what the Eureka Client does automatically on startup; `discoverOne` models a `GET /eureka/apps/billing-service` lookup. `callBilling` no longer hardcodes an address — it resolves `billing-service` by name at call time, so moving or restarting `billing-service` no longer breaks `orders-service`, as long as it re-registers.

### Level 3 — Advanced

Add multiple `billing-service` instances and client-side round-robin load balancing (what Spring Cloud LoadBalancer does under the hood when combined with `@LoadBalanced RestTemplate` or a service-name-based `WebClient`).

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class EurekaClientLevel3 {
    static Map<String, List<String>> registry = new HashMap<>();
    static AtomicInteger counter = new AtomicInteger(0);

    static void register(String service, String address) {
        registry.computeIfAbsent(service, k -> new ArrayList<>()).add(address);
    }

    static String discoverRoundRobin(String service) {
        List<String> instances = registry.getOrDefault(service, List.of());
        if (instances.isEmpty()) throw new IllegalStateException("no instances of " + service);
        int i = counter.getAndIncrement() % instances.size();
        return instances.get(i);
    }

    static String callBilling(String orderId) {
        String address = discoverRoundRobin("billing-service");
        return "GET " + address + "/invoices/" + orderId;
    }

    public static void main(String[] args) {
        register("billing-service", "10.0.2.1:8080");
        register("billing-service", "10.0.2.2:8080");
        register("billing-service", "10.0.2.3:8080");

        // simulate five sequential calls from orders-service
        for (int i = 0; i < 5; i++) {
            System.out.println(callBilling("order-" + i));
        }
    }
}
```

How to run: `java EurekaClientLevel3.java`

`discoverRoundRobin` no longer returns just the first instance — it cycles through all known instances of `billing-service` one at a time, spreading the five calls across three instances (`.1`, `.2`, `.3`, `.1`, `.2`). This is exactly the value of client-side discovery: `orders-service` gets the full list of live instances from the registry and decides for itself how to balance load, with no central load balancer in the request path.

## 6. Walkthrough

Trace Level 3, since it shows the full register-then-discover-then-balance cycle.

1. Three `register("billing-service", ...)` calls run first — each models a separate `billing-service` instance starting up, connecting to Eureka Server, and issuing its own `POST /eureka/apps/BILLING-SERVICE` registration. After this, the registry map holds `billing-service -> [.1, .2, .3]`.
2. The loop calls `callBilling("order-0")` through `callBilling("order-4")` — each call first hits `discoverRoundRobin("billing-service")`, which reads the *current* instance list from the registry (a real Eureka Client caches this list locally and refreshes it periodically, rather than calling the server on every request).
3. `discoverRoundRobin` picks an index using an ever-incrementing counter modulo the instance count — call 0 gets `.1`, call 1 gets `.2`, call 2 gets `.3`, call 3 wraps back to `.1`, call 4 gets `.2`.
4. Each resolved address is spliced into a request string: `"GET " + address + "/invoices/" + orderId`. In a real system this is where an HTTP client (`RestTemplate`, `WebClient`) would actually send the request to that address and return a response, e.g. `200 OK` with a JSON invoice body.
5. Five requests fan out roughly evenly across three instances, which is the practical benefit: no single `billing-service` instance is overwhelmed just because it happened to register first.

```
registry: billing-service -> [.1, .2, .3]

call 0 -> idx 0 -> .1
call 1 -> idx 1 -> .2
call 2 -> idx 2 -> .3
call 3 -> idx 0 -> .1   (wrapped)
call 4 -> idx 1 -> .2
```

## 7. Gotchas & takeaways

> **Gotcha:** the Eureka Client caches the registry locally and refreshes it on an interval (30 seconds by default) — a newly registered instance may not be visible to other clients immediately, and a newly deregistered one may still receive a small number of calls for a short window after it leaves. Design for eventual consistency, not instant consistency.

- `spring.application.name` is the identity a service registers under — it must be set, or Eureka registers the instance under a generic default that other services can't meaningfully discover.
- Discovery-by-name plus client-side load balancing removes the need for a separate load balancer or reverse proxy sitting in front of every internal service call.
- Round-robin is the simplest balancing strategy; real client-side load balancers also support zone-aware and weighted-response-time strategies (covered later under region & zone awareness).
- Because the client caches results locally, a service can usually still resolve other services briefly even if Eureka Server itself becomes temporarily unavailable.
