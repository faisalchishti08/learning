---
card: microservices
gi: 543
slug: spring-cloud-gateway-edge-routing
title: "Spring Cloud Gateway (edge/routing)"
---

## 1. What it is

**Spring Cloud Gateway** is Spring's API gateway — a reactive, [WebFlux-based](0535-spring-webflux-reactor-for-reactive-scalability.md) edge service that sits in front of a microservices fleet, routing incoming requests to the correct backend service based on configurable predicates (path, header, host) and applying filters along the way (adding headers, rewriting paths, rate limiting, circuit breaking) — a single, deliberate front door for external traffic instead of every client needing to know the fleet's internal service topology directly.

## 2. Why & when

You reach for an API gateway once a fleet grows past a single service, because exposing every internal service directly to external clients creates real coupling and operational problems:

- **Without a gateway, external clients need to know each individual service's address and call it directly** — every internal restructuring (splitting a service, renaming one, changing its port) becomes a breaking change for every external client, tightly coupling your internal architecture to the outside world's expectations.
- **A gateway centralizes cross-cutting concerns that would otherwise be duplicated across every individual service**: authentication token validation, rate limiting, request logging, CORS handling, and TLS termination can live in one place rather than being reimplemented (and potentially implemented inconsistently) in every backend service.
- **Routing rules (predicates and filters) let the gateway make external URLs stable even as the internal service topology changes** — `/api/orders/**` can route to `order-service` today and a completely restructured internal service tomorrow, with external clients never noticing, since the externally-visible path contract stayed the same.
- **Built on WebFlux, the gateway is designed for high-throughput, low-latency request proxying** — since it's fundamentally I/O-bound (receive a request, forward it, receive a response, forward that back), the non-blocking, event-loop-based WebFlux model is a natural fit, letting a modest number of gateway instances handle very high request volumes without needing a thread per in-flight proxied request.

## 3. Core concept

Think of a large office building's single reception desk, versus visitors wandering the building trying to find the right department themselves. The reception desk knows the current floor and room number for every department (even as departments move between floors over time), checks visitor badges once at the door rather than requiring every individual office to re-verify identity, and can turn away a visitor who's clearly not authorized before they ever reach an actual department. Visitors only ever need to know "go to reception, ask for Accounting" — never the actual, potentially-changing internal room number — exactly the role a gateway plays for external API clients relative to an internal, evolving fleet of services.

Concretely:

1. **A route consists of a predicate (when should this rule match) and one or more filters (what to do to the request/response) plus a destination URI** — e.g., "if the path starts with `/api/orders/`, strip that prefix and forward to `lb://order-service`" (`lb://` indicating the destination should be resolved via load-balanced service discovery, not a hardcoded address).
2. **Predicates can match on path, HTTP method, header value, host, and more**, and can be combined, letting a single gateway serve many different backend services under one external hostname, differentiated purely by path or header rules.
3. **Filters modify the request before forwarding it, or the response before returning it** — adding an authentication header, stripping a path prefix, adding a correlation ID, rewriting the response body, or applying rate limiting per client.
4. **Because the gateway itself is built on WebFlux, and typically forwards requests using the reactive `WebClient` underneath**, a request being proxied doesn't tie up a dedicated thread for the full round-trip duration to the backend service — the same non-blocking benefits discussed for WebFlux directly apply to how the gateway handles proxying at scale.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="External clients call one gateway; the gateway matches a route's predicate, applies filters, and forwards to the correct internal service via load-balanced discovery">
  <rect x="20" y="80" width="120" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="80" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">external client</text>

  <rect x="220" y="60" width="200" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="82" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Cloud Gateway</text>
  <text x="320" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">predicate: /api/orders/**</text>
  <text x="320" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">filters: strip prefix, add header</text>

  <rect x="480" y="45" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="66" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-service</text>
  <rect x="480" y="90" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="111" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">inventory-service</text>

  <line x1="140" y1="100" x2="220" y2="100" stroke="#8b949e" marker-end="url(#a8)"/>
  <line x1="420" y1="80" x2="480" y2="62" stroke="#8b949e" marker-end="url(#a8)"/>
  <line x1="420" y1="120" x2="480" y2="107" stroke="#8b949e" marker-end="url(#a8)"/>
  <defs><marker id="a8" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

External clients only ever address the gateway; route predicates and filters decide which internal service actually handles each request.

## 5. Runnable example

Scenario: routing external requests to two different backend services based on path. We start with a plain Java model of the predicate-match-and-forward idea, extend it to add a filter that modifies the request, then show the real Spring Cloud Gateway route configuration.

### Level 1 — Basic

```java
// File: BasicRoutingModel.java -- models the CORE gateway idea: match
// a request's path against a predicate, forward to the matched destination.
import java.util.*;
import java.util.function.Predicate;

public class BasicRoutingModel {
    record Route(Predicate<String> pathMatches, String destination) {}

    static List<Route> routes = List.of(
        new Route(path -> path.startsWith("/api/orders/"), "order-service"),
        new Route(path -> path.startsWith("/api/inventory/"), "inventory-service")
    );

    static String routeRequest(String path) {
        for (Route route : routes) {
            if (route.pathMatches().test(path)) return "Forwarding to " + route.destination();
        }
        return "404: no route matched";
    }

    public static void main(String[] args) {
        System.out.println(routeRequest("/api/orders/42"));
        System.out.println(routeRequest("/api/inventory/widget"));
        System.out.println(routeRequest("/api/unknown/path"));
    }
}
```

How to run: `java BasicRoutingModel.java`

Each `Route`'s `pathMatches` predicate is checked in order against the incoming path; the first match determines the forwarding destination — exactly the core mechanism Spring Cloud Gateway's path predicates implement, just expressed here as plain Java lambdas instead of the framework's declarative route configuration.

### Level 2 — Intermediate

```java
// File: RoutingWithFilters.java -- adds a FILTER step: modifying the
// request (stripping a path prefix, adding a header) before forwarding.
import java.util.*;
import java.util.function.*;

public class RoutingWithFilters {
    record ForwardedRequest(String path, Map<String, String> headers) {}

    static ForwardedRequest applyStripPrefixFilter(String originalPath, int segmentsToStrip) {
        String[] parts = originalPath.split("/", segmentsToStrip + 2);
        String strippedPath = "/" + parts[parts.length - 1];
        return new ForwardedRequest(strippedPath, new HashMap<>());
    }

    static ForwardedRequest applyAddHeaderFilter(ForwardedRequest request, String key, String value) {
        Map<String, String> newHeaders = new HashMap<>(request.headers());
        newHeaders.put(key, value);
        return new ForwardedRequest(request.path(), newHeaders);
    }

    public static void main(String[] args) {
        ForwardedRequest stripped = applyStripPrefixFilter("/api/orders/42", 1); // strips "/api" prefix
        ForwardedRequest withHeader = applyAddHeaderFilter(stripped, "X-Gateway-Forwarded", "true");
        System.out.println("Forwarded request: path=" + withHeader.path() + ", headers=" + withHeader.headers());
    }
}
```

How to run: `java RoutingWithFilters.java`

`applyStripPrefixFilter` and `applyAddHeaderFilter` model exactly the transformation Spring Cloud Gateway's `StripPrefix` and `AddRequestHeader` filters perform: the external path `/api/orders/42` becomes the internal path `/orders/42` (the `/api` segment stripped), and a header is added marking the request as gateway-forwarded — both changes happening before the request is actually sent to the backend service.

### Level 3 — Advanced

```java
// File: GatewayRealShape.java -- the REAL Spring Cloud Gateway route
// configuration, using the Java DSL to define predicates and filters
// for TWO different backend services under one gateway.
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

public class GatewayRealShape {

    @Configuration
    static class RouteConfig {
        @Bean
        public RouteLocator routes(RouteLocatorBuilder builder) {
            return builder.routes()
                .route("orders-route", r -> r
                    .path("/api/orders/**")
                    .filters(f -> f
                        .stripPrefix(1) // /api/orders/42 -> /orders/42 forwarded to order-service
                        .addRequestHeader("X-Gateway-Forwarded", "true"))
                    .uri("lb://order-service")) // lb:// -- resolved via load-balanced service discovery
                .route("inventory-route", r -> r
                    .path("/api/inventory/**")
                    .filters(f -> f
                        .stripPrefix(1)
                        .circuitBreaker(c -> c.setName("inventoryCircuitBreaker").setFallbackUri("forward:/fallback/inventory")))
                    .uri("lb://inventory-service"))
                .build();
        }
    }
}
```

How to run: requires `spring-cloud-starter-gateway` (which brings in WebFlux transitively) plus a discovery client (e.g., `spring-cloud-starter-netflix-eureka-client`) for `lb://` resolution; run via `mvn spring-boot:run` and call `GET /api/orders/42` against the gateway's own port to see it forwarded (with prefix stripped and header added) to a real `order-service` instance resolved through service discovery.

`.path("/api/orders/**")` is the route predicate; `.stripPrefix(1)` and `.addRequestHeader(...)` are filters applied to the matching request before forwarding; `.uri("lb://order-service")` is the destination, resolved through the same load-balanced discovery mechanism discussed for [Spring Cloud Commons](0539-spring-cloud-commons-shared-abstractions.md) — the gateway never hardcodes a specific `order-service` instance's address, exactly avoiding the [hardcoded location anti-pattern](0526-hardcoded-service-locations.md) at the edge, not just internally.

## 6. Walkthrough

Trace a request to `GET /api/orders/42` arriving at the gateway configured as in Level 3, end to end:

1. **The gateway's route-matching logic evaluates each configured route's predicate against the incoming request**, in order. The `"orders-route"`'s predicate `.path("/api/orders/**")` matches `/api/orders/42`; the `"inventory-route"`'s predicate does not.
2. **The matched route's filter chain executes.** `.stripPrefix(1)` removes the first path segment (`/api`), transforming the forwarded path to `/orders/42`. `.addRequestHeader("X-Gateway-Forwarded", "true")` adds that header to the outgoing request.
3. **The route's destination `lb://order-service` is resolved.** Because of the `lb://` scheme, the gateway's load-balancer integration queries the active `DiscoveryClient` for currently-healthy `order-service` instances (exactly as described for [Spring Cloud Commons](0539-spring-cloud-commons-shared-abstractions.md)), and selects one — say, `10.0.5.2:8080`.
4. **The gateway issues an internal request** (using its own reactive HTTP client, built on WebFlux/`WebClient`) to `http://10.0.5.2:8080/orders/42`, carrying the added `X-Gateway-Forwarded: true` header, and no longer carrying the original `/api` prefix.
5. **`order-service` at `10.0.5.2:8080` receives and handles this request** exactly as it would any other incoming request to `/orders/42`, unaware of the external `/api/orders/42` path the original client actually used.
6. **`order-service`'s response flows back through the gateway to the original external client** — the gateway forwards the response body and status largely as-is (unless additional response filters were configured to transform it further), and the whole round-trip happened without the gateway ever dedicating a thread to block on `order-service`'s response, since it's built on WebFlux's non-blocking model throughout.

Request/response shape (conceptually):

```
Client -> Gateway:  GET /api/orders/42
Gateway -> order-service:  GET /orders/42
                            X-Gateway-Forwarded: true
order-service -> Gateway:  200 OK  {"orderId":"42"}
Gateway -> Client:  200 OK  {"orderId":"42"}
```

## 7. Gotchas & takeaways

> **Gotcha:** Spring Cloud Gateway is built on WebFlux, meaning custom filters that need to run any blocking code (a blocking database call, a legacy blocking client library) inside the filter chain reintroduce the exact thread-blocking problem WebFlux is meant to avoid — and because the gateway typically runs with a small, fixed number of event-loop threads handling potentially very high request volumes, a blocking custom filter can degrade the entire gateway's throughput far more severely than the same mistake would in a traditional servlet-based application.

- A gateway centralizes cross-cutting concerns (auth, rate limiting, logging, CORS) that would otherwise need to be duplicated, and potentially implemented inconsistently, across every backend service.
- Routes combine a predicate (when this rule applies) with filters (what to do to the request/response) and a destination — `lb://` destinations resolve through the same discovery abstraction used elsewhere in Spring Cloud, avoiding hardcoded backend addresses at the edge too.
- Because it's WebFlux-based, avoid blocking calls inside custom gateway filters — they undermine the non-blocking model the gateway depends on for handling high request volumes with a small thread pool.
- External API paths, stabilized by the gateway's routing rules, can stay stable even as the internal service topology (which service actually handles a given path) changes over time — decoupling external contract stability from internal architectural freedom.
