---
card: microservices
gi: 159
slug: reverse-proxy-vs-api-gateway
title: "Reverse proxy vs API gateway"
---

## 1. What it is

A reverse proxy forwards incoming requests to one or more backend servers based on simple, largely static rules — typically just the request's path or hostname — and returns the backend's response, with minimal awareness of what the request or response actually contains. An [API gateway](0157-api-gateway-pattern.md) is a reverse proxy with substantially more application-layer intelligence layered on top: authentication, request/response transformation, protocol translation, rate limiting per client, and request aggregation across multiple backends.

## 2. Why & when

Every API gateway technically performs reverse proxying as part of what it does — routing a request to a backend and returning the response — but not every reverse proxy is sophisticated enough to be called an API gateway. A plain reverse proxy (nginx configured with simple `location` blocks, or a basic load balancer) is lightweight, fast, and easy to reason about, and is entirely sufficient when all that's needed is "send requests matching this path to that backend pool." An API gateway earns its additional complexity and operational weight specifically when the edge needs to make decisions based on request *content* (headers, tokens, body) rather than just its address, or needs to actively transform requests and responses rather than pass them through unchanged.

Choose a plain reverse proxy when routing needs are simple and static, and no cross-cutting business-adjacent logic (auth, per-client rate limits, aggregation) needs to happen at the edge. Choose an API gateway when the edge genuinely needs application-layer awareness — inspecting a JWT to authenticate a request, rewriting a request body before forwarding it, or combining responses from several backends into one. Using a full API gateway for what a simple reverse proxy would handle just as well adds unnecessary operational surface area; using a bare reverse proxy where gateway-level intelligence is actually needed pushes that missing logic awkwardly into individual backend services instead.

## 3. Core concept

A reverse proxy's routing decision depends only on the request's address-like attributes (path, host, method); an API gateway's decision-making additionally inspects and can modify the request's content and can call out to other systems (an auth service, multiple backends) before producing a response.

```java
// REVERSE PROXY: routing decided PURELY by path -- no content inspection
if (path.startsWith("/orders")) forwardTo(orderServicePool);

// API GATEWAY: routing (or REJECTION) decided by request CONTENT, with transformation
String token = request.header("Authorization");
if (!jwtValidator.isValid(token)) return unauthorized();          // content-aware decision
Request transformed = addInternalHeaders(request, extractClaims(token)); // active transformation
return forwardTo(orderServicePool, transformed);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A reverse proxy routes purely by path, passing requests through unchanged. An API gateway inspects request content such as an auth token, transforms the request, and only then routes it to a backend" >
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Reverse proxy</text>
  <rect x="30" y="40" width="100" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="80" y="62" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">request</text>
  <rect x="180" y="40" width="100" height="35" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="230" y="62" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">path match</text>
  <text x="230" y="90" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">unchanged, forwarded</text>
  <line x1="130" y1="57" x2="178" y2="57" stroke="#8b949e" marker-end="url(#arr40)"/>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">API gateway</text>
  <rect x="360" y="40" width="100" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="410" y="62" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">request</text>
  <rect x="510" y="40" width="100" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="560" y="58" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">auth+transform</text>
  <text x="560" y="90" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">content inspected &amp; MODIFIED</text>
  <line x1="460" y1="57" x2="508" y2="57" stroke="#8b949e" marker-end="url(#arr40)"/>

  <defs>
    <marker id="arr40" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

A reverse proxy passes requests through; a gateway actively inspects and transforms them before forwarding.

## 5. Runnable example

Scenario: a request-handling front door that starts as a simple path-based reverse proxy, is extended with authentication and transformation to become a genuine API gateway, and finally demonstrates a case a plain reverse proxy structurally cannot handle — aggregating responses from two backends into one combined result for the client.

### Level 1 — Basic

```java
// File: PlainReverseProxy.java -- routing decided PURELY by path; content is
// never inspected, never modified.
import java.util.*;

public class PlainReverseProxy {
    static class ReverseProxy {
        Map<String, String> pathToBackend = new LinkedHashMap<>();
        void addRoute(String pathPrefix, String backend) { pathToBackend.put(pathPrefix, backend); }

        String forward(String path, String requestBody) {
            for (var route : pathToBackend.entrySet()) {
                if (path.startsWith(route.getKey())) {
                    System.out.println("[reverse proxy] " + path + " -> " + route.getValue() + " (body passed through UNCHANGED)");
                    return route.getValue() + " received: " + requestBody; // request body is NEVER inspected or modified
                }
            }
            return "404";
        }
    }

    public static void main(String[] args) {
        ReverseProxy proxy = new ReverseProxy();
        proxy.addRoute("/orders", "order-service");
        System.out.println(proxy.forward("/orders/42", "{}"));
        System.out.println("No auth check, no transformation -- PURE path-based forwarding.");
    }
}
```

**How to run:** `javac PlainReverseProxy.java && java PlainReverseProxy` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ApiGatewayWithAuthAndTransform.java -- the SAME routing, now with
// content-aware authentication AND active request transformation -- genuine gateway behavior.
import java.util.*;

public class ApiGatewayWithAuthAndTransform {
    record Request(String path, String authHeader, String body) {}

    static class ApiGateway {
        Map<String, String> pathToBackend = new LinkedHashMap<>();
        void addRoute(String pathPrefix, String backend) { pathToBackend.put(pathPrefix, backend); }

        String handle(Request request) {
            // CONTENT-AWARE decision: reverse proxies don't do this
            if (request.authHeader() == null || !request.authHeader().startsWith("Bearer ")) {
                return "401 Unauthorized";
            }
            String userId = request.authHeader().replace("Bearer user-", ""); // extracted from the TOKEN itself

            // ACTIVE TRANSFORMATION: inject an internal header the backend needs but the client never sent
            String transformedBody = request.body().replace("{}", "{\"authenticatedUserId\":\"" + userId + "\"}");

            for (var route : pathToBackend.entrySet()) {
                if (request.path().startsWith(route.getKey())) {
                    System.out.println("[api gateway] " + request.path() + " -> " + route.getValue() + " (body TRANSFORMED, user injected)");
                    return route.getValue() + " received: " + transformedBody;
                }
            }
            return "404";
        }
    }

    public static void main(String[] args) {
        ApiGateway gateway = new ApiGateway();
        gateway.addRoute("/orders", "order-service");

        System.out.println(gateway.handle(new Request("/orders/42", "Bearer user-alice", "{}")));
        System.out.println(gateway.handle(new Request("/orders/42", null, "{}"))); // no token -- REJECTED before ever reaching order-service
    }
}
```

**How to run:** `javac ApiGatewayWithAuthAndTransform.java && java ApiGatewayWithAuthAndTransform` (JDK 17+).

Expected output:
```
[api gateway] /orders/42 -> order-service (body TRANSFORMED, user injected)
order-service received: {"authenticatedUserId":"alice"}
401 Unauthorized
```

Unlike Level 1, the request is rejected outright when unauthenticated, and the successfully authenticated request's body is actively rewritten before ever reaching the backend — both genuinely content-aware, gateway-level behaviors.

### Level 3 — Advanced

```java
// File: RequestAggregationBeyondProxying.java -- the gateway combines responses
// from TWO SEPARATE backends into ONE response -- something a plain reverse proxy
// structurally cannot do, since it only ever forwards to a SINGLE backend per request.
import java.util.*;

public class RequestAggregationBeyondProxying {
    record OrderSummary(int orderId, double total) {}
    record CustomerInfo(String name, String email) {}
    record CombinedOrderView(int orderId, double total, String customerName, String customerEmail) {}

    static class ApiGateway {
        // simulates calling two DIFFERENT backend services
        OrderSummary callOrderService(int orderId) {
            System.out.println("[gateway] calling order-service for order " + orderId);
            return new OrderSummary(orderId, 99.90);
        }
        CustomerInfo callCustomerService(int customerId) {
            System.out.println("[gateway] calling customer-service for customer " + customerId);
            return new CustomerInfo("Alice", "alice@example.com");
        }

        // ONE client-facing endpoint, backed by TWO backend calls, combined into ONE response --
        // a plain reverse proxy has no notion of "call two backends and merge the results"
        CombinedOrderView getOrderDetailView(int orderId, int customerId) {
            OrderSummary order = callOrderService(orderId);
            CustomerInfo customer = callCustomerService(customerId);
            return new CombinedOrderView(order.orderId(), order.total(), customer.name(), customer.email());
        }
    }

    public static void main(String[] args) {
        ApiGateway gateway = new ApiGateway();
        CombinedOrderView view = gateway.getOrderDetailView(42, 7);

        System.out.println("Client receives ONE combined response: " + view);
        System.out.println("This required TWO backend calls and a merge step -- structurally beyond what a reverse proxy's single-backend-per-request model can express.");
    }
}
```

**How to run:** `javac RequestAggregationBeyondProxying.java && java RequestAggregationBeyondProxying` (JDK 17+).

Expected output:
```
[gateway] calling order-service for order 42
[gateway] calling customer-service for customer 7
Client receives ONE combined response: CombinedOrderView[orderId=42, total=99.9, customerName=Alice, customerEmail=alice@example.com]
This required TWO backend calls and a merge step -- structurally beyond what a reverse proxy's single-backend-per-request model can express.
```

## 6. Walkthrough

1. **Level 1** — `ReverseProxy.forward` checks only `path` against `pathToBackend`'s keys and forwards `requestBody` completely unexamined and unmodified; there is no concept of authentication, content inspection, or transformation anywhere in this class.
2. **Level 2, the added content awareness** — `ApiGateway.handle` inspects `request.authHeader()` *before* making any routing decision, and rejects the request entirely with `401 Unauthorized` if that header is missing or malformed — a decision based on request content, not address.
3. **Level 2, active transformation** — for an authenticated request, `handle` extracts a `userId` from the auth header and rewrites `request.body()` to inject `authenticatedUserId`, meaning the backend receives a body genuinely different from what the client sent — a plain reverse proxy's pass-through model has no equivalent step.
4. **Level 2, the two outcomes compared** — the authenticated call's printed backend response shows the injected `authenticatedUserId` field, while the unauthenticated call never reaches the backend routing logic at all, both behaviors requiring the gateway to understand request *content*, not merely its destination path.
5. **Level 3, two independent backend calls** — `getOrderDetailView` calls `callOrderService` and `callCustomerService` as two entirely separate operations against two different backend services, each returning its own distinct record type (`OrderSummary`, `CustomerInfo`).
6. **Level 3, merging into one response shape** — the method constructs a `CombinedOrderView` by pulling specific fields from both results, producing a response shape that exists nowhere in either individual backend's own API — this composition step is the gateway's own logic, not a pass-through of any single backend's response.
7. **Level 3, why this is structurally beyond reverse proxying** — a reverse proxy's fundamental model is "one incoming request maps to one outgoing request to one backend, and its response is passed back largely as-is"; `getOrderDetailView` breaks that model on two counts — one client-facing request triggers two backend calls, and the client's actual response is synthesized from both, neither of which a simple path-based forwarding rule can express, which is exactly the additional application-layer capability that distinguishes an API gateway from a plain reverse proxy.

## 7. Gotchas & takeaways

> **Gotcha:** because content inspection and transformation cost real CPU time per request (parsing tokens, rewriting bodies, calling multiple backends), an API gateway inherently adds more request latency than a plain reverse proxy — using full gateway machinery for traffic that only ever needed simple path-based forwarding is paying that latency cost for capability the traffic never uses.

- A reverse proxy routes requests based on address-like attributes (path, host) and passes them through largely unmodified; an API gateway additionally inspects and can transform request content, and can call multiple backends per client request.
- Every API gateway performs reverse proxying as part of its behavior, but a plain reverse proxy lacks a gateway's application-layer intelligence.
- Choose a plain reverse proxy for simple, static, path-based routing with no need for content-aware decisions; choose a full API gateway when authentication, transformation, or cross-backend aggregation genuinely need to happen at the edge.
- Request aggregation — combining responses from multiple backends into one client-facing response — is a capability structurally beyond a reverse proxy's one-request-to-one-backend model.
- API gateway capabilities come with real added latency per request; matching the tool to the actual routing complexity needed avoids paying for unused capability.
