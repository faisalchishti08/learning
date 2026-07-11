---
card: spring-cloud
gi: 42
slug: route-predicate-factories-path-host-method-header-query-etc
title: "Route predicate factories (Path, Host, Method, Header, Query, etc.)"
---

## 1. What it is

Route predicate factories are Gateway's built-in library of ready-made predicates — `Path`, `Host`, `Method`, `Header`, `Query`, `Cookie`, `RemoteAddr`, `After`/`Before`/`Between` (time-based), and more — each configurable with arguments in YAML, so most routing logic never needs custom Java code at all.

```yaml
predicates:
  - Path=/orders/**
  - Host=api.example.com,admin.example.com
  - Method=GET,POST
  - Header=X-Request-Type, internal
  - Query=version, v2
  - Cookie=session, valid
```

## 2. Why & when

The previous card modeled the predicate-combination mechanism by hand; in practice, almost every routing need is covered by these built-in factories, configured declaratively rather than coded. Knowing the catalog well means most routing requirements can be expressed purely in YAML, reserving custom predicate code for genuinely unusual cases.

Reach for specific factories based on what's actually distinguishing the traffic:

- `Path` for URL-structure-based routing — the most common case, matching request paths against Ant-style patterns like `/orders/**`.
- `Host` for routing based on which domain/subdomain a request arrived on — useful when one gateway instance serves multiple external hostnames differently.
- `Method` to restrict a route to specific HTTP verbs, often combined with `Path` to route `GET /orders/**` differently from `POST /orders/**`.
- `Header` and `Query` for routing based on custom request metadata — API versioning via a header or query parameter, internal-vs-external traffic tagging, feature-flag-driven routing.
- `Before`/`After`/`Between` for time-windowed routes — useful for scheduled maintenance-mode redirects or temporary traffic diversions.

## 3. Core concept

```
 Path=/orders/**        -> Ant-style path pattern match
 Host=api.example.com   -> matches the request's Host header
 Method=GET,POST        -> matches the HTTP method
 Header=name,regex       -> matches if header 'name' exists and matches regex
 Query=name,regex        -> matches if query param 'name' exists and matches regex
 Cookie=name,regex       -> matches if cookie 'name' exists and matches regex

 all configured factories on one route combine with AND (from the previous card)
```

Each factory is a small, focused, independently testable matcher; routes compose them together to express precise conditions.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple predicate factories each inspect a different part of the same request, and a route combines several of them together with AND logic">
  <rect x="30" y="20" width="200" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="130" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Path=/orders/**</text>

  <rect x="30" y="70" width="200" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="130" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Method=GET,POST</text>

  <rect x="30" y="120" width="200" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="130" y="145" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Header=X-Type,internal</text>

  <rect x="330" y="70" width="130" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">AND</text>
  <text x="395" y="106" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">all must pass</text>

  <rect x="500" y="70" width="110" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="555" y="99" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">route matches</text>

  <line x1="230" y1="40" x2="328" y2="80" stroke="#8b949e" stroke-width="1" marker-end="url(#a42)"/>
  <line x1="230" y1="90" x2="328" y2="95" stroke="#8b949e" stroke-width="1" marker-end="url(#a42)"/>
  <line x1="230" y1="140" x2="328" y2="110" stroke="#8b949e" stroke-width="1" marker-end="url(#a42)"/>
  <line x1="460" y1="95" x2="498" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a42)"/>

  <defs><marker id="a42" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each factory inspects one facet of the request; the route as a whole requires every configured factory to agree.

## 5. Runnable example

The scenario: route API traffic for `orders-service` using several predicate factories together — path plus header-based API versioning, growing to include method restriction, then a time-windowed maintenance override.

### Level 1 — Basic

`Path` and `Header` factories combined for version-aware routing.

```java
import java.util.*;
import java.util.function.Predicate;

public class PredicateFactoriesLevel1 {
    record Request(String path, Map<String, String> headers) {}

    static Predicate<Request> pathFactory(String prefix) {
        return req -> req.path().startsWith(prefix);
    }

    static Predicate<Request> headerFactory(String name, String expectedValue) {
        return req -> expectedValue.equals(req.headers().get(name));
    }

    public static void main(String[] args) {
        Predicate<Request> v2OrdersRoute = pathFactory("/orders/").and(headerFactory("X-Api-Version", "v2"));

        Request r1 = new Request("/orders/42", Map.of("X-Api-Version", "v2"));
        Request r2 = new Request("/orders/42", Map.of("X-Api-Version", "v1"));

        System.out.println("v2 header -> matches: " + v2OrdersRoute.test(r1));
        System.out.println("v1 header -> matches: " + v2OrdersRoute.test(r2));
    }
}
```

How to run: `java PredicateFactoriesLevel1.java`

`Predicate.and` is Java's own AND-combinator, standing in for how Gateway internally combines multiple configured factories on one route — `r2` fails purely because its header value doesn't match, even though its path does.

### Level 2 — Intermediate

Add `Method` factory alongside `Path` and `Header`, modeling a route that only applies to write operations on the v2 API.

```java
import java.util.*;
import java.util.function.Predicate;

public class PredicateFactoriesLevel2 {
    record Request(String path, String method, Map<String, String> headers) {}

    static Predicate<Request> pathFactory(String prefix) { return req -> req.path().startsWith(prefix); }
    static Predicate<Request> headerFactory(String name, String value) { return req -> value.equals(req.headers().get(name)); }
    static Predicate<Request> methodFactory(Set<String> methods) { return req -> methods.contains(req.method()); }

    public static void main(String[] args) {
        Predicate<Request> v2OrdersWrites = pathFactory("/orders/")
                .and(headerFactory("X-Api-Version", "v2"))
                .and(methodFactory(Set.of("POST", "PUT", "DELETE")));

        List<Request> requests = List.of(
                new Request("/orders/42", "POST", Map.of("X-Api-Version", "v2")),
                new Request("/orders/42", "GET", Map.of("X-Api-Version", "v2")),   // fails method
                new Request("/orders/42", "POST", Map.of("X-Api-Version", "v1"))   // fails header
        );

        for (Request req : requests) {
            System.out.println(req.method() + " " + req.path() + " v=" + req.headers().get("X-Api-Version")
                    + " -> matches: " + v2OrdersWrites.test(req));
        }
    }
}
```

How to run: `java PredicateFactoriesLevel2.java`

Chaining a third `.and(...)` narrows the match further still — a `GET` request fails the `methodFactory` check even with a correct path and header, since this route is deliberately scoped to only write operations, perhaps routed to a different backend instance pool optimized for writes.

### Level 3 — Advanced

Add a time-windowed `Between` factory, modeling a maintenance-mode route that only applies during a scheduled window — and confirm it correctly stops matching once the window closes.

```java
import java.util.*;
import java.util.function.Predicate;

public class PredicateFactoriesLevel3 {
    record Request(String path, String method, Map<String, String> headers, long timestampSeconds) {}

    static Predicate<Request> pathFactory(String prefix) { return req -> req.path().startsWith(prefix); }
    static Predicate<Request> headerFactory(String name, String value) { return req -> value.equals(req.headers().get(name)); }
    static Predicate<Request> methodFactory(Set<String> methods) { return req -> methods.contains(req.method()); }
    static Predicate<Request> betweenFactory(long startSeconds, long endSeconds) {
        return req -> req.timestampSeconds() >= startSeconds && req.timestampSeconds() < endSeconds;
    }

    public static void main(String[] args) {
        // maintenance window: seconds 1000 to 2000 on some reference clock
        Predicate<Request> maintenanceRedirect = pathFactory("/orders/").and(betweenFactory(1000, 2000));

        Predicate<Request> v2OrdersWrites = pathFactory("/orders/")
                .and(headerFactory("X-Api-Version", "v2"))
                .and(methodFactory(Set.of("POST", "PUT", "DELETE")));

        List<Request> requests = List.of(
                new Request("/orders/42", "POST", Map.of("X-Api-Version", "v2"), 1500), // during maintenance window
                new Request("/orders/42", "POST", Map.of("X-Api-Version", "v2"), 2500)  // after the window closes
        );

        for (Request req : requests) {
            boolean maintenance = maintenanceRedirect.test(req);
            boolean normal = v2OrdersWrites.test(req);
            String decision = maintenance ? "maintenance-route" : (normal ? "orders-route" : "no match");
            System.out.println("t=" + req.timestampSeconds() + "s -> " + decision);
        }
    }
}
```

How to run: `java PredicateFactoriesLevel3.java`

At `t=1500`, `betweenFactory(1000, 2000)` evaluates `true` (1500 falls in `[1000, 2000)`), so the request is directed to the maintenance route regardless of what the normal `v2OrdersWrites` predicate would have said — this models a real Gateway configuration where the maintenance route is ordered *before* the normal route, so it intercepts matching traffic first during its active window. At `t=2500`, the window has closed, `betweenFactory` returns `false`, and the request falls through to the normal `orders-route` instead — the maintenance route stops intercepting anything the instant its configured window ends, with no manual toggle needed.

## 6. Walkthrough

Trace both requests in Level 3 in order.

1. The first request arrives with `timestampSeconds=1500`. Route evaluation (in a real Gateway, this is route order in the configured list) checks `maintenanceRedirect` first: `pathFactory("/orders/")` passes, and `betweenFactory(1000, 2000)` evaluates `1500 >= 1000 && 1500 < 2000`, both true, so the whole `and`-chain returns `true`. The request is routed to the maintenance handler without `v2OrdersWrites` even needing to be checked (in a real config, Gateway would stop at the first matching route in list order).
2. The second request arrives with `timestampSeconds=2500`. `maintenanceRedirect` now evaluates `betweenFactory(1000, 2000)` as `2500 >= 1000 && 2500 < 2000` — the second clause is false, so the whole predicate is `false`, and the maintenance route doesn't match.
3. Evaluation falls through to `v2OrdersWrites`: `pathFactory` passes, `headerFactory("X-Api-Version", "v2")` passes (the header is present and correct), `methodFactory(Set.of("POST", "PUT", "DELETE"))` passes (`POST` is in the set) — all three conditions hold, so this request routes normally to `orders-route`.
4. The printed decisions confirm the intended behavior: identical requests except for timestamp are routed completely differently purely based on whether they fall inside the configured maintenance window — no code change, no manual route toggling, just the natural evaluation of a time-based predicate against the current moment.

```
t=1500 (inside [1000,2000))  -> maintenanceRedirect matches -> maintenance-route
t=2500 (outside window)      -> maintenanceRedirect fails
                              -> falls through to v2OrdersWrites -> orders-route
```

## 7. Gotchas & takeaways

> **Gotcha:** `Between`/`After`/`Before` predicates compare against the server's clock at request time — if the gateway's clock drifts or its timezone configuration is wrong relative to what the operator intended, a maintenance window can start or end at the wrong wall-clock moment with no error or warning, just silently wrong routing.

- The built-in predicate factory catalog (`Path`, `Host`, `Method`, `Header`, `Query`, `Cookie`, `RemoteAddr`, `After`/`Before`/`Between`, and others) covers the overwhelming majority of routing needs without custom code.
- Route ordering in configuration matters most when predicates could overlap, as with the maintenance-route example — put the more specific or time-sensitive route earlier so it's checked first.
- Combining several factories on one route (as with `Path` + `Header` + `Method`) is how fine-grained routing decisions — API versioning, write-vs-read splitting, internal-vs-external traffic — get expressed purely in configuration.
- `Header` and `Query` factories accept a regex for the value, not just an exact string match, which allows pattern-based routing (`Header=X-Api-Version,v[0-9]+`) without writing custom predicate code.
