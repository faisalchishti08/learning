---
card: spring-cloud
gi: 41
slug: routes-predicates-filters-model
title: "Routes, Predicates & Filters model"
---

## 1. What it is

Every Gateway route is built from three pieces: an **ID** (a name), a target **URI** (where matching requests go), a list of **Predicates** (conditions that must *all* be true for the route to match — an implicit AND), and a list of **Filters** (transformations applied to the request on the way in and/or the response on the way out).

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: orders-route
          uri: lb://orders-service
          predicates:
            - Path=/orders/**
            - Method=GET,POST
          filters:
            - AddRequestHeader=X-Gateway-Source, gateway
            - StripPrefix=1
```

## 2. Why & when

A single predicate (just path matching, say) is often not precise enough — real routing decisions frequently depend on a combination of path, HTTP method, headers, and query parameters together. And routing alone doesn't cover what actually needs to happen to a request or response in transit (adding headers, rewriting paths, retrying). Splitting the model into predicates (decide *if* this route applies) and filters (decide *what happens* once it does) keeps both concerns independently composable.

Understand this model deeply because:

- Every single Gateway route you'll ever write is expressed in these terms — predicates and filters are the entire configuration surface.
- Multiple predicates on one route combine with AND logic, not OR — getting this wrong is a common source of "why isn't my route matching" bugs.
- Filters run in a defined order and can be route-specific or global (global filters are covered in a later card) — understanding ordering matters once more than one filter touches the same request.

## 3. Core concept

```
 Route = { id, uri, predicates: [P1, P2, ...], filters: [F1, F2, ...] }

 matching:  route applies  <=>  P1(request) AND P2(request) AND ... all true

 processing (once matched):
   request  -> F1 -> F2 -> ... -> forwarded to uri
   response <- F1 <- F2 <- ... <- received from uri
```

Predicates gate whether a route is even considered; filters form a pipeline both requests pass through going in and responses pass through coming back.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request is checked against all predicates with AND logic, and if every predicate passes it flows through a chain of filters before being forwarded to the target URI">
  <rect x="20" y="20" width="600" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Predicates: Path=/orders/** AND Method=GET,POST</text>
  <text x="320" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ALL must be true for the route to match</text>

  <line x1="320" y1="70" x2="320" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a41)"/>

  <rect x="60" y="100" width="150" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.3"/>
  <text x="135" y="124" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">F1: AddRequestHeader</text>

  <rect x="245" y="100" width="150" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.3"/>
  <text x="320" y="124" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">F2: StripPrefix</text>

  <rect x="430" y="100" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="505" y="124" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">forwarded to uri</text>

  <line x1="210" y1="120" x2="243" y2="120" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a41)"/>
  <line x1="395" y1="120" x2="428" y2="120" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a41)"/>

  <text x="320" y="185" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">response flows back through the same filters in reverse</text>

  <defs><marker id="a41" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Predicates gate entry into the route; filters form an ordered pipeline the request and response both pass through.

## 5. Runnable example

The scenario: build a route matcher and filter pipeline for `orders-service`, starting with single-predicate matching, then combining multiple predicates with AND logic, then adding an ordered filter chain that transforms the request on the way in.

### Level 1 — Basic

A single predicate: path matching only.

```java
import java.util.function.Predicate;

public class RoutesPredicatesLevel1 {
    record Request(String path, String method) {}

    static Predicate<Request> pathPredicate(String prefix) {
        return req -> req.path().startsWith(prefix);
    }

    public static void main(String[] args) {
        Predicate<Request> matchesOrders = pathPredicate("/orders/");

        System.out.println(matchesOrders.test(new Request("/orders/42", "GET")));   // true
        System.out.println(matchesOrders.test(new Request("/billing/7", "GET")));   // false
    }
}
```

How to run: `java RoutesPredicatesLevel1.java`

A `Predicate<Request>` decides match/no-match from a single request attribute — this is `Path=/orders/**` in isolation, before combining it with anything else.

### Level 2 — Intermediate

Combine multiple predicates with AND logic, modeling `Path=/orders/**` plus `Method=GET,POST` together.

```java
import java.util.*;
import java.util.function.Predicate;

public class RoutesPredicatesLevel2 {
    record Request(String path, String method) {}
    record Route(String id, String uri, List<Predicate<Request>> predicates) {
        boolean matches(Request req) {
            return predicates.stream().allMatch(p -> p.test(req)); // AND across ALL predicates
        }
    }

    static Predicate<Request> pathPredicate(String prefix) { return req -> req.path().startsWith(prefix); }
    static Predicate<Request> methodPredicate(Set<String> methods) { return req -> methods.contains(req.method()); }

    static List<Route> routes = List.of(
            new Route("orders-route", "lb://orders-service",
                    List.of(pathPredicate("/orders/"), methodPredicate(Set.of("GET", "POST"))))
    );

    public static void main(String[] args) {
        List<Request> requests = List.of(
                new Request("/orders/42", "GET"),    // matches both predicates
                new Request("/orders/42", "DELETE"), // fails method predicate
                new Request("/billing/7", "GET")     // fails path predicate
        );

        for (Request req : requests) {
            boolean matched = routes.get(0).matches(req);
            System.out.println(req.method() + " " + req.path() + " -> matches orders-route: " + matched);
        }
    }
}
```

How to run: `java RoutesPredicatesLevel2.java`

`Route.matches` uses `allMatch`, the direct expression of AND logic across every predicate — `DELETE /orders/42` fails even though the path matches, because the method predicate alone is enough to reject it; this is exactly why adding a second predicate to a route only ever narrows what it matches, never widens it.

### Level 3 — Advanced

Add an ordered filter chain that runs once a route matches, transforming the request on the way through — modeling `AddRequestHeader` and `StripPrefix` applied in sequence.

```java
import java.util.*;
import java.util.function.Predicate;
import java.util.function.UnaryOperator;

public class RoutesPredicatesLevel3 {
    static class Request {
        String path;
        String method;
        Map<String, String> headers = new LinkedHashMap<>();
        Request(String path, String method) { this.path = path; this.method = method; }
        Request copy() {
            Request r = new Request(path, method);
            r.headers.putAll(headers);
            return r;
        }
    }

    record Route(String id, String uri, List<Predicate<Request>> predicates, List<UnaryOperator<Request>> filters) {
        boolean matches(Request req) { return predicates.stream().allMatch(p -> p.test(req)); }
        Request applyFilters(Request req) {
            Request current = req;
            for (UnaryOperator<Request> filter : filters) current = filter.apply(current); // run in declared order
            return current;
        }
    }

    static UnaryOperator<Request> addRequestHeader(String name, String value) {
        return req -> { Request r = req.copy(); r.headers.put(name, value); return r; };
    }

    static UnaryOperator<Request> stripPrefix(int parts) {
        return req -> {
            Request r = req.copy();
            String[] segments = r.path.split("/", -1);
            // segments[0] is empty (leading slash); strip `parts` path segments after it
            StringBuilder sb = new StringBuilder();
            for (int i = 1 + parts; i < segments.length; i++) sb.append("/").append(segments[i]);
            r.path = sb.length() == 0 ? "/" : sb.toString();
            return r;
        };
    }

    public static void main(String[] args) {
        Route ordersRoute = new Route("orders-route", "lb://orders-service",
                List.of(req -> req.path.startsWith("/orders/")),
                List.of(addRequestHeader("X-Gateway-Source", "gateway"), stripPrefix(1)));

        Request incoming = new Request("/orders/42", "GET");
        if (ordersRoute.matches(incoming)) {
            Request forwarded = ordersRoute.applyFilters(incoming);
            System.out.println("original path: " + incoming.path);
            System.out.println("forwarded path: " + forwarded.path);
            System.out.println("forwarded headers: " + forwarded.headers);
            System.out.println("forwarded to: " + ordersRoute.uri());
        }
    }
}
```

How to run: `java RoutesPredicatesLevel3.java`

`applyFilters` runs each filter in declared order, threading the (immutable-per-step, via `copy()`) request through the chain: `addRequestHeader` first stamps `X-Gateway-Source: gateway`, then `stripPrefix(1)` removes the first path segment, turning `/orders/42` into `/42` — exactly what a real `StripPrefix=1` filter does before forwarding to a backend that doesn't expect the `/orders` prefix in its own routes.

## 6. Walkthrough

Trace the single request through Level 3 end to end.

1. `incoming` is built as `Request("/orders/42", "GET")` with no headers — this models the raw HTTP request as it first arrives at the gateway.
2. `ordersRoute.matches(incoming)` runs — the route has one predicate, `req.path.startsWith("/orders/")`, which evaluates `true` for `/orders/42`. Since `allMatch` over a single-element list just checks that one condition, the route is selected.
3. `ordersRoute.applyFilters(incoming)` runs — inside it, `current` starts as `incoming`, then the loop applies each filter in order. The first filter, `addRequestHeader("X-Gateway-Source", "gateway")`, produces a *new* `Request` copy with that header added, leaving the path untouched.
4. The second filter, `stripPrefix(1)`, runs on that already-header-stamped copy — it splits the path `/orders/42` into segments `["", "orders", "42"]`, skips the leading empty segment plus the 1 segment being stripped (`orders`), and rebuilds the path from what remains: `/42`.
5. The final `println` calls show the net effect: the original path `/orders/42` became the forwarded path `/42` (so `orders-service` itself doesn't need to know it was reached via an `/orders` prefix), the header `X-Gateway-Source=gateway` was added along the way, and the whole thing gets forwarded to `lb://orders-service` — service discovery then resolves that to a real instance address, the topic of the earlier Service Discovery section.

```
incoming: path=/orders/42, headers={}
   |
   v  F1: addRequestHeader
path=/orders/42, headers={X-Gateway-Source=gateway}
   |
   v  F2: stripPrefix(1)
path=/42, headers={X-Gateway-Source=gateway}
   |
   v
forwarded to lb://orders-service
```

## 7. Gotchas & takeaways

> **Gotcha:** predicates combine with AND, not OR — a route with `Path=/orders/**` and `Method=GET,POST` will silently reject a `DELETE /orders/42` request (falling through to check the next route, or ultimately return 404) rather than matching with a "method not allowed" error. If you actually want either-or matching across different paths, that requires separate routes, not multiple predicates on one route.

- Every Gateway route reduces to exactly this shape: an ID, a target URI, an AND-combined list of predicates, and an ordered list of filters — internalizing this model makes reading and writing any Gateway YAML configuration straightforward.
- Filter order matters and is exactly the declaration order in configuration — reordering `AddRequestHeader` and `StripPrefix` wouldn't change this particular example's outcome, but many real filter combinations are order-sensitive (e.g. a filter that reads a header another filter is about to add).
- Filters conceptually apply on both the request path (going in) and the response path (coming back) — this example only modeled the request side; response-side transformation follows the same ordered-pipeline idea in reverse.
- Because routes are evaluated top to bottom and the first full-predicate-match wins, put more specific routes before more general ones when their predicates could otherwise both match the same request.
