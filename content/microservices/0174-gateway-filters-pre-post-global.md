---
card: microservices
gi: 174
slug: gateway-filters-pre-post-global
title: "Gateway filters (pre / post / global)"
---

## 1. What it is

Spring Cloud Gateway filters modify a request before it's forwarded to a backend (pre-filters) or modify the response before it's returned to the client (post-filters), attached either to a specific route or applied uniformly to every route as global filters — the concrete Spring Cloud Gateway mechanism implementing the [ordered filter chain](0163-cross-cutting-concerns-at-the-gateway-auth-logging-metrics.md) concept discussed generally for gateway cross-cutting concerns.

## 2. Why & when

A single filter often needs to act at two distinct points in a request's lifecycle — add a header before forwarding, then log the response status after it comes back — and Spring Cloud Gateway's filter model supports this directly: a filter's logic runs once as the request passes through on its way to the backend (its "pre" phase) and again as the response passes back through on its way to the client (its "post" phase), both defined in the same filter implementation. Route-specific filters apply only to requests matching that particular route's predicates, while global filters run for every route uniformly, giving a natural way to express "this applies to just orders" versus "this applies to everything."

Attach a filter to a specific route when its logic is genuinely route-specific — adding a header only order-service needs, rewriting only order-related paths. Use a global filter for concerns that should apply uniformly across every route — authentication, request logging, standard response headers — mirroring the same "does this concern apply everywhere or just here" judgment call behind any cross-cutting concern's placement.

## 3. Core concept

A `GatewayFilter` receives the exchange (the request/response pair) and a reference to the rest of the filter chain; it can inspect and modify the request before calling the chain (the pre phase), and inspect and modify the response after the chain's downstream processing completes (the post phase), both within one filter's implementation.

```java
// a filter with BOTH pre and post logic, in ONE implementation
GatewayFilter loggingFilter = (exchange, chain) -> {
    System.out.println("PRE: " + exchange.getRequest().getPath());          // runs BEFORE forwarding
    return chain.filter(exchange).then(Mono.fromRunnable(() ->
        System.out.println("POST: " + exchange.getResponse().getStatusCode()))); // runs AFTER the response comes back
};

// route-specific: applies ONLY to routes that reference it
.filters(f -> f.filter(loggingFilter))

// global: applies to EVERY route automatically
@Bean
public GlobalFilter globalLoggingFilter() { return loggingFilter; }
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request passes through a filter's pre-phase logic on the way to the backend; the backend's response passes back through the same filter's post-phase logic on the way to the client, both defined within one filter implementation" >
  <rect x="20" y="70" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Request</text>

  <rect x="220" y="30" width="200" height="110" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#8b949e" font-size="8" font-family="sans-serif">ONE Filter</text>
  <text x="240" y="75" fill="#e6edf3" font-size="8" font-family="sans-serif">PRE: log request path</text>
  <text x="240" y="120" fill="#e6edf3" font-size="8" font-family="sans-serif">POST: log response status</text>

  <rect x="500" y="70" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Backend</text>

  <line x1="120" y1="90" x2="218" y2="70" stroke="#8b949e" marker-end="url(#arr55)"/>
  <line x1="420" y1="70" x2="498" y2="90" stroke="#8b949e" marker-end="url(#arr55)"/>
  <line x1="498" y1="105" x2="420" y2="120" stroke="#8b949e" marker-end="url(#arr55)"/>
  <line x1="218" y1="120" x2="120" y2="100" stroke="#8b949e" marker-end="url(#arr55)"/>

  <defs>
    <marker id="arr55" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The request and response both pass through the same filter, once on the way in and once on the way back.

## 5. Runnable example

Scenario: a gateway logging system that starts with a pre-only filter (showing an incomplete view of request handling), extends it to a genuine pre/post filter capturing both the request and the resulting response together, and finally demonstrates the route-specific versus global filter distinction by applying one filter only to order routes and another filter to every route uniformly.

### Level 1 — Basic

```java
// File: PreOnlyFilter.java -- logs ONLY the incoming request; the OUTCOME
// (success? failure? how long did it take?) is never captured at all.
import java.util.function.*;

public class PreOnlyFilter {
    interface Handler { String handle(String path); }

    static String preOnlyFilter(String path, Handler next) {
        System.out.println("PRE: incoming request to " + path); // logs the request...
        return next.handle(path); // ...but NOTHING logs what happened AFTER
    }

    public static void main(String[] args) {
        String result = preOnlyFilter("/orders/42", path -> "200 OK, backend response for " + path);
        System.out.println("Result: " + result);
        System.out.println("The log shows the request happened, but says NOTHING about the outcome.");
    }
}
```

**How to run:** `javac PreOnlyFilter.java && java PreOnlyFilter` (JDK 17+).

### Level 2 — Intermediate

```java
// File: PreAndPostFilter.java -- ONE filter implementation with BOTH a pre-phase
// (before forwarding) and a post-phase (after the response comes back).
import java.util.function.*;

public class PreAndPostFilter {
    interface Handler { String handle(String path); }
    interface Filter { String apply(String path, Handler next); }

    static Filter loggingFilter = (path, next) -> {
        System.out.println("PRE: " + path); // pre-phase: BEFORE calling next
        long start = System.currentTimeMillis();
        String response = next.handle(path); // the actual forwarded call
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("POST: " + path + " -> " + response + " (" + elapsed + "ms)"); // post-phase: AFTER next returns
        return response;
    };

    public static void main(String[] args) {
        Handler backend = path -> "200 OK, backend response for " + path;
        String result = loggingFilter.apply("/orders/42", backend);
        System.out.println("Client receives: " + result);
    }
}
```

**How to run:** `javac PreAndPostFilter.java && java PreAndPostFilter` (JDK 17+).

Expected output (timing approximate):
```
PRE: /orders/42
POST: /orders/42 -> 200 OK, backend response for /orders/42 (0ms)
Client receives: 200 OK, backend response for /orders/42
```

Unlike Level 1, the log now shows both the incoming request AND its outcome, including timing — a complete picture, captured in one filter implementation.

### Level 3 — Advanced

```java
// File: RouteSpecificVsGlobalFilter.java -- ONE filter applies to EVERY route
// (global); a SECOND filter applies ONLY to order routes (route-specific).
import java.util.*;
import java.util.function.*;

public class RouteSpecificVsGlobalFilter {
    interface Handler { String handle(String path); }
    interface Filter { String apply(String path, Handler next); }

    // GLOBAL filter: runs for EVERY route, no matter what
    static Filter globalAuthFilter = (path, next) -> {
        System.out.println("[GLOBAL filter] auth check for " + path);
        return next.handle(path);
    };

    // ROUTE-SPECIFIC filter: only attached to order routes -- customer routes never see it
    static Filter orderSpecificHeaderFilter = (path, next) -> {
        System.out.println("[ROUTE-SPECIFIC filter, orders only] injecting X-Order-Context header for " + path);
        return next.handle(path);
    };

    static Handler buildChain(List<Filter> filters, Handler finalHandler) {
        Handler chain = finalHandler;
        for (int i = filters.size() - 1; i >= 0; i--) {
            Filter filter = filters.get(i);
            Handler next = chain;
            chain = path -> filter.apply(path, next);
        }
        return chain;
    }

    public static void main(String[] args) {
        Handler backend = path -> "200 OK for " + path;

        // ORDER route: BOTH the global filter AND the order-specific filter apply
        Handler orderRoutePipeline = buildChain(List.of(globalAuthFilter, orderSpecificHeaderFilter), backend);
        System.out.println("=== handling /orders/42 ===");
        System.out.println(orderRoutePipeline.handle("/orders/42"));

        // CUSTOMER route: ONLY the global filter applies -- orderSpecificHeaderFilter is NEVER in its chain
        Handler customerRoutePipeline = buildChain(List.of(globalAuthFilter), backend);
        System.out.println("\n=== handling /customers/7 ===");
        System.out.println(customerRoutePipeline.handle("/customers/7"));
    }
}
```

**How to run:** `javac RouteSpecificVsGlobalFilter.java && java RouteSpecificVsGlobalFilter` (JDK 17+).

Expected output:
```
=== handling /orders/42 ===
[GLOBAL filter] auth check for /orders/42
[ROUTE-SPECIFIC filter, orders only] injecting X-Order-Context header for /orders/42
200 OK for /orders/42

=== handling /customers/7 ===
[GLOBAL filter] auth check for /customers/7
200 OK for /customers/7
```

## 6. Walkthrough

1. **Level 1** — `preOnlyFilter` prints one log line before calling `next.handle(path)` and returns whatever that call produces without any further logging, meaning the printed log has no record of the response's content, status, or timing at all.
2. **Level 2, one implementation, two phases** — `loggingFilter`'s lambda body contains code both *before* (`System.out.println("PRE: ...")`) and *after* (`System.out.println("POST: ...")`) the call to `next.handle(path)`; both blocks live in the same filter definition, sharing local variables like `start` between the two phases.
3. **Level 2, the complete picture captured** — the printed output now includes both the pre-phase log line and a post-phase log line showing the actual response content and elapsed time, directly resolving Level 1's incomplete view.
4. **Level 3, a filter meant for everyone** — `globalAuthFilter` is included in `List.of(...)` for *both* `orderRoutePipeline` and `customerRoutePipeline`, modeling how a global filter in real Spring Cloud Gateway configuration is automatically included in every route's chain without needing to be individually attached to each one.
5. **Level 3, a filter meant for one route type** — `orderSpecificHeaderFilter` is included only in the list building `orderRoutePipeline`; `customerRoutePipeline`'s filter list contains only `globalAuthFilter`, meaning `orderSpecificHeaderFilter`'s code never runs at all when handling a customer-related request.
6. **Level 3, tracing the order route** — `orderRoutePipeline.handle("/orders/42")` runs `globalAuthFilter` first (printing its log line), which calls `next.handle`, entering `orderSpecificHeaderFilter` (printing its own log line), which calls the final `backend` handler.
7. **Level 3, tracing the customer route and the contrast** — `customerRoutePipeline.handle("/customers/7")` runs *only* `globalAuthFilter` before reaching `backend` directly, with no order-specific log line appearing anywhere in that section's output — this side-by-side comparison makes concrete the real distinction between a global filter (present in every route's chain automatically) and a route-specific filter (present only where explicitly attached), exactly mirroring how Spring Cloud Gateway's `GlobalFilter` beans versus per-route `filters(...)` configuration behave in a real application.

## 7. Gotchas & takeaways

> **Gotcha:** the order in which multiple global filters run relative to each other is determined by an explicit ordering mechanism (implementing `Ordered` or using `@Order`), not by declaration order alone — two global filters with no explicit ordering can run in an unpredictable relative sequence, which matters a great deal if one filter's behavior depends on another having already run (an auth filter needing to run before a filter that reads the authenticated user's identity, for instance).

- Spring Cloud Gateway filters can act both before a request is forwarded (pre-phase) and after the response returns (post-phase), both expressible within a single filter implementation.
- Route-specific filters apply only to routes they're explicitly attached to; global filters apply automatically to every route in the gateway.
- This filter model is the concrete Spring Cloud Gateway mechanism implementing the general ordered-filter-chain approach to gateway cross-cutting concerns.
- Choosing route-specific versus global placement for a filter mirrors the broader judgment call of whether a concern applies uniformly across the whole gateway or only to a specific subset of routes.
- Multiple global filters' relative execution order needs explicit configuration (via `Ordered` or `@Order`) when one filter's correctness depends on another having already run — declaration order alone doesn't guarantee this.
