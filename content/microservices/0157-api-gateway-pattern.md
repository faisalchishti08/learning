---
card: microservices
gi: 157
slug: api-gateway-pattern
title: "API gateway pattern"
---

## 1. What it is

The API gateway pattern places a single entry point in front of a microservices system, through which every external client request passes before being routed to whichever internal service actually handles it — clients talk to one gateway address, never directly to individual services, and the gateway is responsible for routing each request to the right place.

## 2. Why & when

Without a gateway, every client (a mobile app, a web frontend, a third-party integrator) needs to know the network location of every individual service it talks to, and any change to that internal topology — a service splitting in two, moving hosts, changing its API — becomes a breaking change every client must handle. A gateway absorbs that churn: clients depend on one stable entry point and a stable external API, while the internal service landscape can be restructured, renamed, or rebalanced freely behind it, as long as the gateway's routing rules are updated to match.

Introduce an API gateway once a system has more than a handful of independently deployable services that external clients need to reach, or as soon as internal service topology is expected to change over time in ways clients shouldn't have to track. For a system with one or two services and no expectation of client-facing complexity, a gateway can be premature infrastructure — it's a real piece of shared, must-be-highly-available infrastructure, not a free abstraction.

## 3. Core concept

A gateway maintains a routing table mapping incoming request patterns (paths, hostnames) to backend service locations, and forwards each matching request to the appropriate backend, returning that backend's response to the client — the client is entirely unaware of which specific backend actually handled its request.

```java
// client's perspective: ONE address, regardless of how many services exist behind it
GET https://api.example.com/orders/42     // gateway routes this to order-service
GET https://api.example.com/customers/7   // gateway routes this to customer-service

// gateway's routing table (conceptually)
routes.add("/orders/**", "http://order-service:8080");
routes.add("/customers/**", "http://customer-service:8081");
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple clients send requests to a single API gateway address; the gateway routes each request, based on its path, to the correct backend service, none of which are directly reachable by clients" >
  <rect x="20" y="30" width="110" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="75" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Mobile app</text>
  <rect x="20" y="130" width="110" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="75" y="150" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Web frontend</text>

  <rect x="230" y="70" width="160" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="99" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">API Gateway</text>

  <rect x="480" y="20" width="140" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="550" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">order-service</text>
  <rect x="480" y="80" width="140" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="550" y="102" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">customer-service</text>
  <rect x="480" y="140" width="140" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="550" y="162" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">payment-service</text>

  <line x1="130" y1="45" x2="228" y2="85" stroke="#8b949e" marker-end="url(#arr38)"/>
  <line x1="130" y1="145" x2="228" y2="105" stroke="#8b949e" marker-end="url(#arr38)"/>
  <line x1="390" y1="85" x2="478" y2="38" stroke="#8b949e" marker-end="url(#arr38)"/>
  <line x1="390" y1="95" x2="478" y2="98" stroke="#8b949e" marker-end="url(#arr38)"/>
  <line x1="390" y1="105" x2="478" y2="158" stroke="#8b949e" marker-end="url(#arr38)"/>

  <defs>
    <marker id="arr38" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Clients only ever address the gateway; the gateway alone knows how to reach individual backend services.

## 5. Runnable example

Scenario: a client accessing multiple services that starts with direct, per-service addressing (showing the coupling problem), introduces a gateway with a routing table to remove that coupling, and finally demonstrates the gateway absorbing an internal topology change — a service splitting into two — with zero impact on client-facing requests.

### Level 1 — Basic

```java
// File: DirectServiceAddressing.java -- clients know EVERY individual service's
// address directly; any topology change breaks every client.
import java.util.*;

public class DirectServiceAddressing {
    public static void main(String[] args) {
        // the CLIENT hard-codes each service's address
        String orderServiceUrl = "http://order-service.internal:8080";
        String customerServiceUrl = "http://customer-service.internal:8081";

        System.out.println("Client calls order-service directly at: " + orderServiceUrl + "/orders/42");
        System.out.println("Client calls customer-service directly at: " + customerServiceUrl + "/customers/7");
        System.out.println("If order-service ever moves, renames, or splits, EVERY client with this address hard-coded breaks.");
    }
}
```

**How to run:** `javac DirectServiceAddressing.java && java DirectServiceAddressing` (JDK 17+).

### Level 2 — Intermediate

```java
// File: GatewayWithRoutingTable.java -- clients address ONE gateway; the gateway's
// routing table, not the client, knows where each backend actually lives.
import java.util.*;
import java.util.function.*;

public class GatewayWithRoutingTable {
    static class ApiGateway {
        Map<String, String> routingTable = new LinkedHashMap<>(); // pathPrefix -> backend base URL
        void addRoute(String pathPrefix, String backendUrl) { routingTable.put(pathPrefix, backendUrl); }

        String handleRequest(String requestPath) {
            for (var route : routingTable.entrySet()) {
                if (requestPath.startsWith(route.getKey())) {
                    String backendUrl = route.getValue();
                    System.out.println("[gateway] " + requestPath + " -> routed to " + backendUrl);
                    return "response from " + backendUrl + requestPath;
                }
            }
            return "404 Not Found";
        }
    }

    public static void main(String[] args) {
        ApiGateway gateway = new ApiGateway();
        gateway.addRoute("/orders", "http://order-service.internal:8080");
        gateway.addRoute("/customers", "http://customer-service.internal:8081");

        // the CLIENT only ever addresses the gateway -- no backend URLs anywhere in client code
        System.out.println(gateway.handleRequest("/orders/42"));
        System.out.println(gateway.handleRequest("/customers/7"));
        System.out.println("Client code contains ZERO backend addresses -- only ever talks to the gateway.");
    }
}
```

**How to run:** `javac GatewayWithRoutingTable.java && java GatewayWithRoutingTable` (JDK 17+).

Expected output:
```
[gateway] /orders/42 -> routed to http://order-service.internal:8080
response from http://order-service.internal:8080/orders/42
[gateway] /customers/7 -> routed to http://customer-service.internal:8081
response from http://customer-service.internal:8081/customers/7
Client code contains ZERO backend addresses -- only ever talks to the gateway.
```

### Level 3 — Advanced

```java
// File: TopologyChangeAbsorbedByGateway.java -- order-service SPLITS into two
// separate services; the gateway's routing table absorbs this change, client code untouched.
import java.util.*;

public class TopologyChangeAbsorbedByGateway {
    static class ApiGateway {
        // routes now support MULTIPLE prefixes mapping to DIFFERENT backends for what was once one service
        List<Map.Entry<String, String>> routingTable = new ArrayList<>();
        void addRoute(String pathPrefix, String backendUrl) { routingTable.add(Map.entry(pathPrefix, backendUrl)); }

        String handleRequest(String requestPath) {
            // longest-prefix-match wins, so more specific routes can override a broader one
            Map.Entry<String, String> best = null;
            for (var route : routingTable) {
                if (requestPath.startsWith(route.getKey()) && (best == null || route.getKey().length() > best.getKey().length())) best = route;
            }
            if (best == null) return "404 Not Found";
            System.out.println("[gateway] " + requestPath + " -> routed to " + best.getValue());
            return "response from " + best.getValue() + requestPath;
        }
    }

    // simulates the SAME client-facing requests, run against the gateway BEFORE and AFTER a backend topology change
    static void simulateClientRequests(ApiGateway gateway) {
        System.out.println(gateway.handleRequest("/orders/42"));
        System.out.println(gateway.handleRequest("/orders/42/fulfillment-status"));
    }

    public static void main(String[] args) {
        System.out.println("=== BEFORE: order-service handles EVERYTHING under /orders ===");
        ApiGateway gatewayBefore = new ApiGateway();
        gatewayBefore.addRoute("/orders", "http://order-service.internal:8080");
        simulateClientRequests(gatewayBefore);

        System.out.println("\n=== order-service SPLITS: fulfillment logic moves to a NEW order-fulfillment-service ===");
        ApiGateway gatewayAfter = new ApiGateway();
        gatewayAfter.addRoute("/orders", "http://order-service.internal:8080"); // general order operations, unchanged
        gatewayAfter.addRoute("/orders/*/fulfillment-status", "http://order-fulfillment-service.internal:8090"); // NEW, more specific route
        simulateClientRequests(gatewayAfter);

        System.out.println("\nThe SAME two client-facing paths were used before and after -- clients issued IDENTICAL requests both times, unaware of the backend split.");
    }
}
```

**How to run:** `javac TopologyChangeAbsorbedByGateway.java && java TopologyChangeAbsorbedByGateway` (JDK 17+).

Expected output:
```
=== BEFORE: order-service handles EVERYTHING under /orders ===
[gateway] /orders/42 -> routed to http://order-service.internal:8080
response from http://order-service.internal:8080/orders/42
[gateway] /orders/42/fulfillment-status -> routed to http://order-service.internal:8080
response from http://order-service.internal:8080/orders/42/fulfillment-status

=== order-service SPLITS: fulfillment logic moves to a NEW order-fulfillment-service ===
[gateway] /orders/42 -> routed to http://order-service.internal:8080
response from http://order-service.internal:8080/orders/42
[gateway] /orders/42/fulfillment-status -> routed to http://order-fulfillment-service.internal:8090
response from http://order-fulfillment-service.internal:8090/orders/42/fulfillment-status

The SAME two client-facing paths were used before and after -- clients issued IDENTICAL requests both times, unaware of the backend split.
```

## 6. Walkthrough

1. **Level 1** — `orderServiceUrl` and `customerServiceUrl` are hard-coded string constants directly in what represents client code; both service addresses are baked into every place that needs to call them, with no indirection at all.
2. **Level 2, the routing table as the single source of truth** — `ApiGateway.routingTable` maps path prefixes to backend URLs; `handleRequest` iterates this table and forwards to whichever backend's prefix matches the incoming path, meaning the *client* only ever needs to know the gateway's own address.
3. **Level 2, the observable decoupling** — `main`'s calls to `gateway.handleRequest(...)` use only request paths, never backend URLs; the routing decision (which backend actually serves `/orders/42`) is made entirely inside the gateway, invisible to the calling code.
4. **Level 3, longest-prefix matching for overlapping routes** — `handleRequest` now finds the *longest* matching prefix among all routes rather than the first match, which is what allows a more specific route (`/orders/*/fulfillment-status`) to take precedence over a broader one (`/orders`) that would otherwise also match.
5. **Level 3, the "before" topology** — `gatewayBefore` has a single route sending everything under `/orders` to `order-service`; both simulated client requests, including the fulfillment-status one, are routed there.
6. **Level 3, the "after" topology, post-split** — `gatewayAfter` adds a new, more specific route for `/orders/*/fulfillment-status` pointing at a newly introduced `order-fulfillment-service`, while the original `/orders` route remains unchanged for everything else.
7. **Level 3, the client-facing requests never changing** — `simulateClientRequests` issues the *exact same two request paths* against both `gatewayBefore` and `gatewayAfter`; the only difference in the printed output is which backend URL the gateway internally routed the fulfillment-status request to — proving that a genuine internal service split was fully absorbed by updating only the gateway's routing table, with zero corresponding change required in any client-facing request.

## 7. Gotchas & takeaways

> **Gotcha:** because every external request passes through the gateway, it becomes a single point of failure and a shared performance bottleneck for the entire system if not built and operated with the same (or greater) reliability rigor as the services behind it — a gateway outage takes down access to every backend service simultaneously, even if every individual backend is perfectly healthy.

- The API gateway pattern gives clients a single, stable entry point, decoupling them from the actual network location and internal structure of backend services.
- A gateway's core responsibility is routing: matching incoming requests to the correct backend based on path, hostname, or other request attributes.
- This decoupling lets internal service topology change — services splitting, merging, moving — without breaking clients, as long as the gateway's routing rules are updated to match.
- Introduce a gateway once client-facing complexity or expected topology churn justifies the added infrastructure; it is a real, must-be-highly-available piece of shared infrastructure, not a free abstraction.
- Because all traffic flows through it, the gateway itself becomes a critical dependency requiring the same reliability engineering as the services it fronts.
