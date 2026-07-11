---
card: spring-cloud
gi: 44
slug: global-filters
title: "Global filters"
---

## 1. What it is

Global filters run on *every* route, automatically, without being listed in any individual route's `filters` configuration — in contrast to the route-scoped `GatewayFilter` factories from the previous card, which only apply to the routes that explicitly reference them. Gateway ships several built-in global filters (routing, load balancing, metrics), and applications can register their own by implementing `GlobalFilter`.

```java
@Component
public class RequestLoggingGlobalFilter implements GlobalFilter, Ordered {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        long start = System.currentTimeMillis();
        return chain.filter(exchange).then(Mono.fromRunnable(() -> {
            long duration = System.currentTimeMillis() - start;
            System.out.println(exchange.getRequest().getPath() + " took " + duration + "ms");
        }));
    }

    @Override
    public int getOrder() { return Ordered.LOWEST_PRECEDENCE; }
}
```

## 2. Why & when

Some cross-cutting behavior genuinely applies to *every* request the gateway handles — request logging, a correlation ID stamped on everything, a global security check — and repeating the same `GatewayFilter` factory reference on every single route's configuration would be redundant and easy to forget on a newly added route. Global filters guarantee that behavior applies uniformly, once, without per-route configuration.

Reach for a global filter when:

- The behavior genuinely applies to every route, present and future — logging, tracing/correlation ID propagation, a blanket authentication check.
- You want to guarantee new routes automatically inherit the behavior without anyone remembering to configure it per-route.
- The logic combines both request-phase and response-phase behavior around the *entire* routing decision, not just a single route's specific transformation.

## 3. Core concept

```
 request arrives
     |
     v
 GLOBAL filters (run on every route, in Order)
     |
     v
 route-specific GatewayFilters (only for the matched route, from the previous card)
     |
     v
 forwarded to backend
     |
     v  (response flows back)
 route-specific GatewayFilters (reverse order)
     |
     v
 GLOBAL filters (reverse order)
     |
     v
 response sent to client
```

Global filters wrap around every route uniformly; route-specific filters only wrap the route they're configured on.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A global filter wraps every route uniformly, running before and after any route-specific filters regardless of which route a request matches">
  <rect x="20" y="20" width="600" height="160" rx="10" fill="#1c243020" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="320" y="40" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Global Filter (applies to every route)</text>

  <rect x="60" y="70" width="220" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="170" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">orders-route</text>
  <text x="170" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">route-specific filters</text>
  <text x="170" y="122" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">(only this route)</text>

  <rect x="360" y="70" width="220" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="470" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">billing-route</text>
  <text x="470" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">route-specific filters</text>
  <text x="470" y="122" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">(only this route)</text>

  <defs><marker id="a44" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The global filter's boundary encloses every route; each route's own filters only apply inside its own boundary.

## 5. Runnable example

The scenario: build a filter chain that models a global request-logging filter wrapping two different routes, growing to include ordering between multiple global filters, then adding a global filter that can short-circuit the chain entirely (an auth check).

### Level 1 — Basic

A single global filter (logging) wrapping a route-specific filter.

```java
import java.util.function.Function;

public class GlobalFiltersLevel1 {
    static String globalLoggingFilter(String routeId, Function<String, String> next, String path) {
        System.out.println("[global] before routing: " + path);
        String result = next.apply(path);
        System.out.println("[global] after routing: " + result + " (via " + routeId + ")");
        return result;
    }

    static String routeSpecificFilter(String path) {
        return path.replace("/api", ""); // route-specific transformation, e.g. StripPrefix
    }

    public static void main(String[] args) {
        String result = globalLoggingFilter("orders-route", GlobalFiltersLevel1::routeSpecificFilter, "/api/orders/42");
        System.out.println("final: " + result);
    }
}
```

How to run: `java GlobalFiltersLevel1.java`

`globalLoggingFilter` wraps around whatever route-specific logic runs (`next`), printing before and after — this is exactly the wrapping relationship global filters have with route-specific ones: they run *around* the entire routing decision, not as part of any one route's own filter list.

### Level 2 — Intermediate

Add multiple global filters with explicit ordering, modeling `Ordered.getOrder()` controlling which global filter runs first.

```java
import java.util.*;
import java.util.function.Function;

public class GlobalFiltersLevel2 {
    interface NamedFilter {
        String name();
        int order(); // lower runs first, mirrors Ordered.getOrder()
        String apply(String path, Function<String, String> next);
    }

    static NamedFilter loggingFilter = new NamedFilter() {
        public String name() { return "logging"; }
        public int order() { return 0; }
        public String apply(String path, Function<String, String> next) {
            System.out.println("[logging] before: " + path);
            String result = next.apply(path);
            System.out.println("[logging] after: " + result);
            return result;
        }
    };

    static NamedFilter correlationIdFilter = new NamedFilter() {
        public String name() { return "correlation-id"; }
        public int order() { return 1; }
        public String apply(String path, Function<String, String> next) {
            System.out.println("[correlation-id] stamping X-Correlation-Id=abc-123");
            return next.apply(path);
        }
    };

    static String buildChain(List<NamedFilter> filters, Function<String, String> routeLogic, String path) {
        // fold the filters right-to-left so the lowest-order filter ends up outermost
        Function<String, String> chain = routeLogic;
        for (int i = filters.size() - 1; i >= 0; i--) {
            NamedFilter f = filters.get(i);
            Function<String, String> inner = chain;
            chain = p -> f.apply(p, inner);
        }
        return chain.apply(path);
    }

    public static void main(String[] args) {
        List<NamedFilter> globalFilters = new ArrayList<>(List.of(correlationIdFilter, loggingFilter));
        globalFilters.sort(Comparator.comparingInt(NamedFilter::order)); // logging (0) before correlation-id (1)

        buildChain(globalFilters, path -> path.replace("/api", ""), "/api/orders/42");
    }
}
```

How to run: `java GlobalFiltersLevel2.java`

Sorting by `order()` and folding right-to-left means the lowest-order filter (`loggingFilter`, order `0`) ends up outermost, wrapping everything else — its "before" print happens first and its "after" print happens last, exactly like `Ordered.getOrder()` controlling relative global filter execution in real Gateway.

### Level 3 — Advanced

Add a global filter that can short-circuit the chain entirely — an authentication check that returns an error response directly, without ever calling the route-specific logic or reaching the backend.

```java
import java.util.*;
import java.util.function.Function;

public class GlobalFiltersLevel3 {
    record Response(int status, String body) {}

    interface NamedFilter {
        String name();
        int order();
        Response apply(Request req, Function<Request, Response> next);
    }

    record Request(String path, Map<String, String> headers) {}

    static NamedFilter authFilter = new NamedFilter() {
        public String name() { return "auth"; }
        public int order() { return -10; } // very low order -- runs before everything else
        public Response apply(Request req, Function<Request, Response> next) {
            if (!"valid-token".equals(req.headers().get("Authorization"))) {
                System.out.println("[auth] rejected, short-circuiting the chain");
                return new Response(401, "Unauthorized"); // never calls next() -- backend is never reached
            }
            System.out.println("[auth] accepted, continuing");
            return next.apply(req);
        }
    };

    static NamedFilter loggingFilter = new NamedFilter() {
        public String name() { return "logging"; }
        public int order() { return 0; }
        public Response apply(Request req, Function<Request, Response> next) {
            System.out.println("[logging] before: " + req.path());
            Response result = next.apply(req);
            System.out.println("[logging] after: " + result.status());
            return result;
        }
    };

    static Response buildChain(List<NamedFilter> filters, Function<Request, Response> routeLogic, Request req) {
        Function<Request, Response> chain = routeLogic;
        for (int i = filters.size() - 1; i >= 0; i--) {
            NamedFilter f = filters.get(i);
            Function<Request, Response> inner = chain;
            chain = r -> f.apply(r, inner);
        }
        return chain.apply(req);
    }

    public static void main(String[] args) {
        List<NamedFilter> globalFilters = new ArrayList<>(List.of(loggingFilter, authFilter));
        globalFilters.sort(Comparator.comparingInt(NamedFilter::order)); // auth (-10) before logging (0)

        Function<Request, Response> backendCall = req -> new Response(200, "{\"orderId\":42}");

        System.out.println("-- unauthenticated request --");
        Response r1 = buildChain(globalFilters, backendCall, new Request("/orders/42", Map.of()));
        System.out.println("result: " + r1.status() + " " + r1.body());

        System.out.println("-- authenticated request --");
        Response r2 = buildChain(globalFilters, backendCall,
                new Request("/orders/42", Map.of("Authorization", "valid-token")));
        System.out.println("result: " + r2.status() + " " + r2.body());
    }
}
```

How to run: `java GlobalFiltersLevel3.java`

Sorted by order, `authFilter` (`-10`) wraps *outside* `loggingFilter` (`0`), so it runs first. For the unauthenticated request, `authFilter` returns `401` directly without ever calling `next.apply(req)` — `loggingFilter` and `backendCall` never execute at all, meaning the backend is completely shielded from unauthenticated traffic. For the authenticated request, `authFilter` calls `next.apply(req)`, which invokes `loggingFilter`, which in turn calls `backendCall`, producing the real `200` response that flows back out through both filters.

## 6. Walkthrough

Trace the unauthenticated request in Level 3 first, since it demonstrates the short-circuit behavior most clearly.

1. `buildChain` is called with `globalFilters` sorted so `authFilter` (order `-10`) is outermost, wrapping `loggingFilter` (order `0`), which wraps `backendCall`.
2. The chain is invoked with the unauthenticated `Request` — execution enters `authFilter.apply` first. It checks `req.headers().get("Authorization")` against `"valid-token"`; the headers map is empty, so the check fails.
3. `authFilter` prints `[auth] rejected, short-circuiting the chain` and immediately returns `new Response(401, "Unauthorized")` — critically, it never calls `next.apply(req)`, so `loggingFilter` never runs and `backendCall` never runs. The backend service is never even contacted.
4. The final `println` shows `401 Unauthorized` — exactly what a real global auth filter accomplishes: rejecting invalid requests at the gateway's edge, before they ever reach (or add load to) any backend service.
5. For the second, authenticated request, `authFilter` finds a matching `Authorization` header, prints `[auth] accepted, continuing`, and calls `next.apply(req)` — this invokes `loggingFilter`, which prints its "before" message, calls `backendCall` (producing the real `200` response), then prints its "after" message before returning the response back up through `authFilter` unchanged.

```
sorted global filters: [authFilter(-10), loggingFilter(0)]

unauthenticated:
  authFilter -> check fails -> return 401 directly (short-circuit)
  (loggingFilter and backendCall never run)

authenticated:
  authFilter -> check passes -> next()
    loggingFilter -> before -> next()
      backendCall -> 200
    loggingFilter -> after
  authFilter -> returns 200 unchanged
```

## 7. Gotchas & takeaways

> **Gotcha:** a low-order (early-running) global filter that short-circuits the chain, like the `authFilter` here, prevents every filter and route logic ordered *after* it from ever running — including things like request logging. If you want to log rejected requests too, the logging filter needs to run *before* the auth filter (a lower order still), or the auth filter itself needs to log on rejection, as it does here.

- Global filters apply to every route automatically — no per-route configuration, which is exactly the point when the behavior genuinely needs to be universal.
- `Ordered.getOrder()` (lower values run earlier, wrapping outside higher-order filters) controls relative execution among multiple global filters, and it's the same ordering mechanism route-specific filters use.
- A global filter can short-circuit the entire chain by not calling the next filter/handler — this is the standard pattern for authentication, IP allow/deny lists, and other "reject before doing any real work" concerns.
- Because global filters wrap every route, keep them fast and side-effect-light — expensive logic here adds latency to literally every request the gateway processes, unlike a route-specific filter that only affects its own route's traffic.
