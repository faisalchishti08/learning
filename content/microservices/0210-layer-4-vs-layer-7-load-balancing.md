---
card: microservices
gi: 210
slug: layer-4-vs-layer-7-load-balancing
title: "Layer 4 vs Layer 7 load balancing"
---

## 1. What it is

Layer 4 (transport-layer) load balancing makes its routing decision based only on TCP/UDP-level information — source and destination IP address and port — without inspecting the actual content of the traffic at all. Layer 7 (application-layer) load balancing inspects the actual application protocol content (HTTP headers, paths, cookies) to make a routing decision, exactly like the [request routing](0160-request-routing-path-predicates.md) and [request/response transformation](0161-request-response-transformation.md) an [API gateway](0157-api-gateway-pattern.md) performs.

## 2. Why & when

Layer 4 balancing is fast and simple precisely because it never has to parse or understand the traffic it's forwarding — it operates purely on connection-level metadata, making it well suited to raw throughput and protocol-agnostic forwarding (it works identically for HTTP, gRPC, a database protocol, or anything else running over TCP). Layer 7 balancing trades away some of that speed and protocol-agnosticism for the ability to make genuinely content-aware decisions — routing based on a URL path, a specific header, or a cookie value — which is exactly what's needed for the kind of application-aware routing an API gateway performs, but is unnecessary and wasteful overhead for traffic where content awareness adds no value.

Use Layer 4 balancing for raw, protocol-agnostic throughput where the routing decision genuinely doesn't need to know anything about the traffic's content — balancing raw TCP connections across database replicas, for instance. Use Layer 7 balancing whenever the routing decision needs to inspect actual request content — path-based routing, header-based routing, cookie-based sticky sessions — which describes most of what an API gateway or application-aware load balancer does.

## 3. Core concept

A Layer 4 balancer's decision function has access only to connection-level attributes (source/destination IP and port); a Layer 7 balancer's decision function has access to the fully parsed application-layer request, letting it inspect and route on the path, headers, cookies, or body.

```java
// LAYER 4: decision based ONLY on connection-level info -- content is INVISIBLE
ServiceInstance chooseLayer4(String sourceIp, int sourcePort) {
    return roundRobin.choose(instances); // could ALSO hash sourceIp for consistency, but STILL no content awareness
}

// LAYER 7: decision based on the ACTUAL PARSED request content
ServiceInstance chooseLayer7(HttpRequest request) {
    if (request.path().startsWith("/orders")) return orderServiceInstances.next();
    if (request.header("X-Beta-User") != null) return betaInstances.next();
    return defaultInstances.next(); // content-AWARE routing, impossible at Layer 4
}
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Layer 4 balancer routes based only on TCP connection metadata, blind to content. A Layer 7 balancer parses the actual HTTP request and routes based on path, headers, or other application-level content" >
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Layer 4</text>
  <rect x="30" y="40" width="240" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">TCP: srcIP:port -&gt; dstIP:port (content BLIND)</text>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Layer 7</text>
  <rect x="360" y="40" width="240" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">HTTP: path, headers, cookies</text>
  <text x="480" y="74" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(content AWARE)</text>
</svg>

Layer 4 forwards blind to content; Layer 7 parses and routes based on it.

## 5. Runnable example

Scenario: a mixed order-service and customer-service traffic stream that starts with a simulated Layer 4 balancer unable to distinguish traffic types (routing purely by connection round-robin), adds a simulated Layer 7 balancer that inspects request paths to route correctly by service, and finally demonstrates Layer 7's additional capability — header-based routing to a beta backend — something structurally impossible at Layer 4 regardless of algorithm sophistication.

### Level 1 — Basic

```java
// File: Layer4ContentBlindRouting.java -- routes PURELY by connection round-robin;
// CANNOT distinguish order-service traffic from customer-service traffic AT ALL.
import java.util.*;

public class Layer4ContentBlindRouting {
    record TcpConnection(String sourceIp, int sourcePort) {} // Layer 4 has ONLY this info -- no path, no headers

    public static void main(String[] args) {
        List<String> allBackends = List.of("backend-1", "backend-2", "backend-3", "backend-4"); // a MIX of order-service and customer-service instances
        int index = 0;

        // TWO logically different requests, but Layer 4 CANNOT tell them apart -- both are just "a TCP connection"
        TcpConnection orderRequest = new TcpConnection("10.5.1.1", 54321);
        TcpConnection customerRequest = new TcpConnection("10.5.1.2", 54322);

        System.out.println("Order-service request routed (round-robin, content-blind) to: " + allBackends.get(index++ % allBackends.size()));
        System.out.println("Customer-service request routed (round-robin, content-blind) to: " + allBackends.get(index++ % allBackends.size()));
        System.out.println("Layer 4 has NO WAY to route order-service traffic specifically to order-service backends -- it can't SEE the difference.");
    }
}
```

**How to run:** `javac Layer4ContentBlindRouting.java && java Layer4ContentBlindRouting` (JDK 17+).

### Level 2 — Intermediate

```java
// File: Layer7PathAwareRouting.java -- INSPECTS the actual HTTP path and
// routes order-service and customer-service traffic to the CORRECT backend pools.
import java.util.*;

public class Layer7PathAwareRouting {
    record HttpRequest(String path) {} // Layer 7 has the FULL parsed request

    static class Layer7Balancer {
        List<String> orderBackends = List.of("order-a", "order-b");
        List<String> customerBackends = List.of("customer-a", "customer-b");
        int orderIndex = 0, customerIndex = 0;

        String route(HttpRequest request) {
            if (request.path().startsWith("/orders")) return orderBackends.get(orderIndex++ % orderBackends.size()); // CONTENT-AWARE
            if (request.path().startsWith("/customers")) return customerBackends.get(customerIndex++ % customerBackends.size());
            return "404";
        }
    }

    public static void main(String[] args) {
        Layer7Balancer balancer = new Layer7Balancer();

        System.out.println("Order request -> " + balancer.route(new HttpRequest("/orders/42")));
        System.out.println("Customer request -> " + balancer.route(new HttpRequest("/customers/7")));
        System.out.println("Order request -> " + balancer.route(new HttpRequest("/orders/43")));
        System.out.println("Layer 7 correctly routed EACH request type to its OWN dedicated backend pool -- IMPOSSIBLE at Layer 4.");
    }
}
```

**How to run:** `javac Layer7PathAwareRouting.java && java Layer7PathAwareRouting` (JDK 17+).

Expected output:
```
Order request -> order-a
Customer request -> customer-a
Order request -> order-b
Layer 7 correctly routed EACH request type to its OWN dedicated backend pool -- IMPOSSIBLE at Layer 4.
```

### Level 3 — Advanced

```java
// File: Layer7HeaderBasedBetaRouting.java -- ADDITIONALLY routes based on a
// HEADER value -- beta users get a DIFFERENT backend than regular users making
// the IDENTICAL path request -- a capability structurally UNAVAILABLE at Layer 4.
import java.util.*;

public class Layer7HeaderBasedBetaRouting {
    record HttpRequest(String path, Map<String, String> headers) {}

    static class Layer7Balancer {
        List<String> stableOrderBackends = List.of("order-stable-a", "order-stable-b");
        List<String> betaOrderBackends = List.of("order-beta-a");
        int stableIndex = 0, betaIndex = 0;

        String route(HttpRequest request) {
            if (!request.path().startsWith("/orders")) return "404";
            // TWO requests with the IDENTICAL path can route DIFFERENTLY, based on a HEADER --
            // this decision requires PARSING the request, something Layer 4 fundamentally cannot do
            if ("true".equals(request.headers().get("X-Beta-User"))) {
                return betaOrderBackends.get(betaIndex++ % betaOrderBackends.size());
            }
            return stableOrderBackends.get(stableIndex++ % stableOrderBackends.size());
        }
    }

    public static void main(String[] args) {
        Layer7Balancer balancer = new Layer7Balancer();

        HttpRequest regularUser = new HttpRequest("/orders/42", Map.of());
        HttpRequest betaUser = new HttpRequest("/orders/42", Map.of("X-Beta-User", "true")); // IDENTICAL path

        System.out.println("Regular user request (path=/orders/42): " + balancer.route(regularUser));
        System.out.println("Beta user request (SAME path=/orders/42, but X-Beta-User header): " + balancer.route(betaUser));
        System.out.println("Regular user request again: " + balancer.route(regularUser));

        System.out.println("\nTWO requests with the IDENTICAL path routed to DIFFERENT backend pools, based purely on a HEADER -- Layer 4 sees ONLY TCP metadata and could NEVER make this distinction, no matter how sophisticated its algorithm.");
    }
}
```

**How to run:** `javac Layer7HeaderBasedBetaRouting.java && java Layer7HeaderBasedBetaRouting` (JDK 17+).

Expected output:
```
Regular user request (path=/orders/42): order-stable-a
Beta user request (SAME path=/orders/42, but X-Beta-User header): order-beta-a
Regular user request again: order-stable-b

TWO requests with the IDENTICAL path routed to DIFFERENT backend pools, based purely on a HEADER -- Layer 4 sees ONLY TCP metadata and could NEVER make this distinction, no matter how sophisticated its algorithm.
```

## 6. Walkthrough

1. **Level 1** — `TcpConnection` carries only `sourceIp` and `sourcePort`, deliberately modeling exactly what information is visible at Layer 4; the two conceptually different requests (order-related versus customer-related) are indistinguishable from this data alone, so both are routed by the identical, content-blind round-robin logic.
2. **Level 1, the structural limitation stated directly** — the final printed comment isn't merely a design choice being illustrated but a genuine, structural fact: no algorithm operating only on `TcpConnection`-level data could ever route order traffic specifically to order backends, because the information needed to make that distinction (the HTTP path) simply isn't present at that layer.
3. **Level 2, the parsed request as the decision input** — `Layer7Balancer.route` receives an `HttpRequest` carrying a fully-parsed `path` field, and its `if` checks (`request.path().startsWith("/orders")`) directly inspect that content — something structurally unavailable to a Layer 4 decision function.
4. **Level 2, the correctly separated backend pools** — each of the three test requests is routed to the appropriate pool (`orderBackends` or `customerBackends`) based on its path, with each pool maintaining its own independent round-robin index, directly resolving Level 1's inability to make this distinction at all.
5. **Level 3, a header-based distinction on an identical path** — `regularUser` and `betaUser` share the *exact same* `path` value (`"/orders/42"`), differing only in the presence of an `"X-Beta-User"` header — this is deliberately chosen to demonstrate that even Layer 7's path-awareness alone (as shown in Level 2) wouldn't be enough here; the decision requires inspecting headers specifically.
6. **Level 3, the header check driving a different routing outcome** — `route` checks `request.headers().get("X-Beta-User")` and branches to an entirely different backend pool (`betaOrderBackends` versus `stableOrderBackends`) purely based on that header's value, despite both requests otherwise looking identical at the path level.
7. **Level 3, why this is impossible at Layer 4, definitively** — the final printed comment makes the core architectural point explicit: two requests indistinguishable at the TCP connection level (same general traffic pattern, potentially even the same client IP) can carry completely different HTTP-level content, and any routing decision needing to act on that content — a header, a cookie, a path segment — requires the balancer to have actually parsed the application-layer protocol, which is the defining, structural difference between Layer 7 and Layer 4 load balancing, not merely a difference in typical configuration or algorithm sophistication.

## 7. Gotchas & takeaways

> **Gotcha:** Layer 7 load balancing's content-awareness comes at a real, measurable performance cost — parsing and inspecting every request's headers, path, and potentially body adds CPU overhead and latency per request compared to Layer 4's simple connection forwarding, which is why extremely high-throughput, protocol-agnostic scenarios (raw database connection balancing, for instance) often deliberately choose Layer 4 specifically to avoid that overhead, even when a Layer 7 balancer would technically also work.

- Layer 4 load balancing routes based only on TCP/UDP connection metadata (source/destination IP and port), remaining entirely blind to the actual content of the traffic it forwards.
- Layer 7 load balancing parses the actual application-layer protocol (HTTP paths, headers, cookies) and makes routing decisions based on that content, which is what an API gateway's request routing and transformation capabilities fundamentally rely on.
- Some routing decisions — like distinguishing traffic by URL path or by a specific header value — are structurally impossible at Layer 4, regardless of how sophisticated the balancing algorithm is, because the required information simply isn't visible at that layer.
- Layer 4 balancing's protocol-agnosticism and simplicity make it well suited to high-throughput, content-irrelevant forwarding scenarios like raw database connection balancing.
- Layer 7's content-awareness comes at a real performance cost from parsing and inspecting each request, a deliberate trade-off worth making only when that content awareness is genuinely needed for the routing decision.
