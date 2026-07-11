---
card: spring-cloud
gi: 48
slug: route-metadata-configuration-java-dsl-vs-yaml
title: "Route metadata & configuration (Java DSL vs YAML)"
---

## 1. What it is

Every Gateway route example so far has been YAML, but routes can equally be defined in Java using the `RouteLocatorBuilder` fluent DSL — and either way, a route can carry arbitrary **metadata**, key-value pairs attached to the route definition that custom filters or predicates can read at request time, without that data affecting routing or filtering logic on its own.

```java
@Bean
RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
    return builder.routes()
        .route("orders-route", r -> r.path("/orders/**")
                .filters(f -> f.addRequestHeader("X-Gateway-Source", "gateway")
                                .stripPrefix(1))
                .metadata("owner", "payments-team")
                .metadata("responseTimeoutMs", 3000)
                .uri("lb://orders-service"))
        .build();
}
```

## 2. Why & when

YAML configuration is declarative and easy to read at a glance, but it can't express conditional logic, computed values, or anything that depends on environment-specific Java code. The Java DSL trades that readability for full programmatic control — building routes from a list fetched at startup, applying the same filter chain to many routes via a loop, or computing a route's URI dynamically. Metadata, independent of which style defines the route, is the mechanism for attaching arbitrary extra information a custom filter can look up without polluting the predicate/filter list itself.

Choose based on what the routing setup actually needs:

- YAML for straightforward, mostly-static routing — the large majority of real Gateway configurations, and the easiest for a team to review and reason about at a glance.
- The Java DSL when routes need to be built programmatically — generated from a database of tenant configurations, computed based on active feature flags, or built with shared filter chains via a loop instead of copy-pasted YAML blocks.
- Metadata whenever a custom filter needs route-specific configuration that isn't a standard predicate or filter argument — a per-route timeout, an owning team for alerting, a feature flag name to check.

## 3. Core concept

```
 YAML route:
   spring.cloud.gateway.routes[]:
     - id, uri, predicates[], filters[], metadata{}

 Java DSL route (equivalent):
   builder.routes().route(id, r -> r.path(...).filters(...).metadata(...).uri(...)).build()

 metadata is read at request time by custom code:
   exchange.getRoute().getMetadata().get("responseTimeoutMs")
```

Both styles produce the same underlying `Route` objects; metadata is a side-channel for extra, filter-readable configuration that neither predicates nor filters directly consume.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="YAML and Java DSL route definitions both compile down to the same Route object, which a custom filter can read metadata from at request time">
  <rect x="30" y="20" width="230" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="145" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">YAML config</text>
  <text x="145" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">declarative, static</text>

  <rect x="370" y="20" width="230" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Java DSL (RouteLocatorBuilder)</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">programmatic, dynamic</text>

  <line x1="145" y1="70" x2="290" y2="105" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a48)"/>
  <line x1="485" y1="70" x2="350" y2="105" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a48)"/>

  <rect x="230" y="110" width="180" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="135" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Route object + metadata</text>

  <line x1="320" y1="150" x2="320" y2="175" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a48)"/>
  <text x="320" y="188" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">custom filter reads metadata at request time</text>

  <defs><marker id="a48" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both configuration styles converge on the same runtime `Route` representation; metadata rides along for any custom logic to consult.

## 5. Runnable example

The scenario: model routes carrying custom per-route metadata a filter reads at request time — a per-route timeout. Start with YAML-equivalent static route definitions, then add the Java-DSL-style programmatic construction, then add a custom filter that consults metadata to apply per-route behavior.

### Level 1 — Basic

Static, YAML-equivalent route definitions with metadata attached.

```java
import java.util.*;

public class RouteMetadataLevel1 {
    record Route(String id, String uri, Map<String, Object> metadata) {}

    static List<Route> routes = List.of(
            new Route("orders-route", "lb://orders-service", Map.of("owner", "payments-team", "responseTimeoutMs", 3000)),
            new Route("billing-route", "lb://billing-service", Map.of("owner", "billing-team", "responseTimeoutMs", 8000))
    );

    public static void main(String[] args) {
        for (Route r : routes) {
            System.out.println(r.id() + " -> owner=" + r.metadata().get("owner")
                    + ", timeout=" + r.metadata().get("responseTimeoutMs") + "ms");
        }
    }
}
```

How to run: `java RouteMetadataLevel1.java`

Two routes carry different metadata values, exactly as they would if written in YAML — metadata is just data attached to the route, not yet doing anything on its own.

### Level 2 — Intermediate

Build the same routes programmatically, in a style mirroring the Java DSL — including a case where the DSL's flexibility genuinely helps: generating routes from a list rather than repeating structure.

```java
import java.util.*;
import java.util.stream.*;

public class RouteMetadataLevel2 {
    record Route(String id, String uri, Map<String, Object> metadata) {}

    record TenantConfig(String tenantId, String backendService, int timeoutMs) {}

    // imagine this list came from a database of active tenants at startup -- impossible to express cleanly in static YAML
    static List<TenantConfig> tenants = List.of(
            new TenantConfig("acme-corp", "acme-orders-service", 2000),
            new TenantConfig("globex", "globex-orders-service", 5000)
    );

    static List<Route> buildRoutesFromTenants(List<TenantConfig> tenants) {
        return tenants.stream()
                .map(t -> new Route(t.tenantId() + "-route", "lb://" + t.backendService(),
                        Map.of("tenant", t.tenantId(), "responseTimeoutMs", t.timeoutMs())))
                .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Route> routes = buildRoutesFromTenants(tenants);
        for (Route r : routes) {
            System.out.println(r.id() + " -> " + r.uri() + ", timeout=" + r.metadata().get("responseTimeoutMs") + "ms");
        }
    }
}
```

How to run: `java RouteMetadataLevel2.java`

`buildRoutesFromTenants` generates a `Route` per tenant from a dynamic list — this is exactly the kind of scenario where the Java DSL earns its keep over YAML: the number and shape of routes depends on data (here, a hardcoded stand-in for a database query) that isn't known until the application actually runs.

### Level 3 — Advanced

Add a custom filter that reads the `responseTimeoutMs` metadata at request time and applies it as an actual per-route timeout — the payoff of attaching metadata in the first place.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Supplier;

public class RouteMetadataLevel3 {
    record Route(String id, String uri, Map<String, Object> metadata) {}
    record Response(int status, String body) {}

    static List<Route> routes = List.of(
            new Route("orders-route", "lb://orders-service", Map.of("responseTimeoutMs", 200)),
            new Route("billing-route", "lb://billing-service", Map.of("responseTimeoutMs", 2000))
    );

    // custom filter: applies the route's own configured timeout, read from metadata
    static Response callWithMetadataTimeout(Route route, Supplier<Response> backendCall) throws Exception {
        int timeoutMs = (int) route.metadata().getOrDefault("responseTimeoutMs", 5000);
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<Response> future = executor.submit(backendCall::get);
        try {
            return future.get(timeoutMs, TimeUnit.MILLISECONDS);
        } catch (TimeoutException e) {
            future.cancel(true);
            return new Response(504, "Gateway Timeout after " + timeoutMs + "ms (route: " + route.id() + ")");
        } finally {
            executor.shutdown();
        }
    }

    public static void main(String[] args) throws Exception {
        Supplier<Response> slowBackend = () -> {
            try { Thread.sleep(500); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
            return new Response(200, "{\"orderId\":42}");
        };

        // orders-route's 200ms timeout is too short for this slow backend call -- times out
        System.out.println(callWithMetadataTimeout(routes.get(0), slowBackend));

        // billing-route's 2000ms timeout comfortably covers the same 500ms delay -- succeeds
        System.out.println(callWithMetadataTimeout(routes.get(1), slowBackend));
    }
}
```

How to run: `java RouteMetadataLevel3.java`

`callWithMetadataTimeout` reads `responseTimeoutMs` straight out of the route's metadata map and applies it as a real timeout on the backend call — this is a custom filter reading route-specific configuration that has no dedicated built-in `GatewayFilter` factory for it, exactly the use case metadata is designed for. The same `slowBackend` (a simulated 500ms call) times out against `orders-route`'s tight 200ms budget but succeeds comfortably against `billing-route`'s more generous 2000ms budget.

## 6. Walkthrough

Trace both calls in Level 3.

1. `callWithMetadataTimeout(routes.get(0), slowBackend)` runs first — it reads `route.metadata().getOrDefault("responseTimeoutMs", 5000)` for `orders-route`, getting `200`. It submits `backendCall::get` to a single-thread executor and calls `future.get(200, MILLISECONDS)`.
2. `slowBackend` sleeps `500ms` before returning — since `500 > 200`, `future.get` throws `TimeoutException` before the backend call finishes. The `catch` block cancels the still-running future and returns a `504` response naming the specific route (`orders-route`) and its configured timeout, useful for debugging which route's budget was exceeded.
3. `callWithMetadataTimeout(routes.get(1), slowBackend)` runs next — it reads `responseTimeoutMs` for `billing-route`, getting `2000`. The same `slowBackend` call is submitted, this time with a `2000ms` budget against its `500ms` actual delay.
4. Since `500 < 2000`, `future.get` returns the real `Response(200, "{\"orderId\":42}")` well before the timeout fires — the call succeeds, printed as the successful response.
5. The two outcomes for the identical backend call demonstrate the entire point of route metadata: request-time behavior (here, how long to wait before giving up) is driven by data attached to the specific route, without that data needing to be a first-class predicate or filter concept.

```
orders-route:  metadata.responseTimeoutMs = 200   |  backend takes 500ms -> TIMEOUT -> 504
billing-route: metadata.responseTimeoutMs = 2000  |  backend takes 500ms -> within budget -> 200
```

## 7. Gotchas & takeaways

> **Gotcha:** metadata is inert by default — attaching `metadata("responseTimeoutMs", 3000)` to a route does nothing on its own; it only has an effect once a custom filter (like `callWithMetadataTimeout` here) is actually written to read and act on it. It's easy to add metadata expecting some built-in behavior to pick it up automatically, when in fact no such behavior exists unless you write it.

- YAML is the right default for most routing configuration — readable, reviewable, and sufficient for the majority of static route setups.
- Reach for the Java DSL specifically when routes need to be computed, generated from external data, or share complex filter-building logic that would otherwise mean copy-pasting large YAML blocks.
- Route metadata is a general-purpose side channel for route-specific configuration that has no dedicated predicate or filter — it's most useful paired with a custom `GatewayFilter` that reads it, as shown here.
- Because both YAML and the Java DSL compile down to the same underlying `Route` representation, they can be mixed in one application if needed — some routes defined declaratively, others generated dynamically — though most teams pick one style for consistency.
