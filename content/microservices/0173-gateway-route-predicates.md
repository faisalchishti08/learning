---
card: microservices
gi: 173
slug: gateway-route-predicates
title: "Gateway route predicates"
---

## 1. What it is

Spring Cloud Gateway's route predicates are the built-in, composable conditions a route uses to decide whether it should handle a given request — beyond simple [path matching](0160-request-routing-path-predicates.md), Spring Cloud Gateway ships predicates for HTTP method, header presence/value, query parameter presence/value, cookie value, host, and time-based windows (before/after/between specific timestamps), all combinable with logical AND on a single route.

## 2. Why & when

Real routing decisions often need more than "does the path match" — routing based on a feature-flag header to send a percentage of traffic to a new backend version, restricting a route to only be active during a specific maintenance or promotional window, or differentiating traffic by an API key's tier encoded in a header, all require inspecting request attributes beyond the path. Spring Cloud Gateway's built-in predicate library covers the common cases directly, as configuration, without needing custom code for routing logic that fits one of these standard shapes.

Reach for built-in predicates whenever a routing decision can be expressed using the request's path, method, headers, query parameters, cookies, host, or time window — which covers the large majority of real-world gateway routing needs. Reach for a [custom `GatewayFilterFactory`](0175-gateway-custom-gatewayfilterfactory.md) or custom predicate only when the routing logic genuinely can't be expressed as a combination of these standard building blocks.

## 3. Core concept

Multiple predicates on one route combine with AND semantics — a request must satisfy every predicate on a route for that route to match; different routes, each with their own predicate combinations, are evaluated in order, and the first fully-matching route wins.

```java
// path AND header AND time-window predicates, ALL must match for this route
.route("beta_route", r -> r
    .path("/orders/**")
    .and().header("X-Beta-User", "true")
    .and().before(ZonedDateTime.parse("2026-12-31T23:59:59Z"))
    .uri("http://order-service-v2:8080"))
// a route with just path, for everyone else
.route("stable_route", r -> r.path("/orders/**").uri("http://order-service-v1:8080"))
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request matching path, header, and time-window predicates simultaneously routes to the beta service; a request matching only path falls through to the stable route" >
  <rect x="20" y="70" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="94" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Request</text>

  <rect x="220" y="20" width="220" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">beta_route:</text>
  <text x="330" y="57" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">path AND header AND time-window</text>
  <text x="330" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">ALL must match</text>

  <rect x="220" y="110" width="220" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="135" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">stable_route: path only</text>

  <line x1="150" y1="90" x2="218" y2="50" stroke="#8b949e" marker-end="url(#arr54)"/>
  <line x1="150" y1="95" x2="218" y2="130" stroke="#8b949e" marker-end="url(#arr54)"/>

  <defs>
    <marker id="arr54" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

More specific predicate combinations narrow which requests a route matches; a request failing any one predicate falls through to the next route.

## 5. Runnable example

Scenario: an order-service routing setup that starts with simple path-only matching, adds a header predicate to route beta users to a new backend version, and finally combines header and time-window predicates so beta routing is active only for beta users during a specific rollout window, falling back to stable routing afterward.

### Level 1 — Basic

```java
// File: PathOnlyPredicate.java -- ONE predicate dimension: path. Every request
// matching the path goes to the SAME backend, regardless of anything else about it.
import java.util.*;

public class PathOnlyPredicate {
    record Request(String path, Map<String, String> headers) {}

    public static void main(String[] args) {
        Request request = new Request("/orders/42", Map.of("X-Beta-User", "true"));
        String backend = request.path().startsWith("/orders") ? "order-service-v1" : "404";
        System.out.println(request.path() + " -> " + backend);
        System.out.println("The 'X-Beta-User' header was IGNORED entirely -- path-only predicate can't differentiate on it.");
    }
}
```

**How to run:** `javac PathOnlyPredicate.java && java PathOnlyPredicate` (JDK 17+).

### Level 2 — Intermediate

```java
// File: PathAndHeaderPredicate.java -- combining PATH and HEADER predicates
// with AND semantics -- BOTH must match for the beta route to apply.
import java.util.*;
import java.util.function.*;

public class PathAndHeaderPredicate {
    record Request(String path, Map<String, String> headers) {}
    record Route(String name, Predicate<Request> predicate, String backend) {}

    public static void main(String[] args) {
        List<Route> routes = List.of(
            new Route("beta_route",
                r -> r.path().startsWith("/orders") && "true".equals(r.headers().get("X-Beta-User")), // PATH *and* HEADER
                "order-service-v2"),
            new Route("stable_route", r -> r.path().startsWith("/orders"), "order-service-v1")); // path ONLY -- catch-all

        Request betaUser = new Request("/orders/42", Map.of("X-Beta-User", "true"));
        Request regularUser = new Request("/orders/43", Map.of());

        for (Request req : List.of(betaUser, regularUser)) {
            String backend = "404";
            for (Route route : routes) { if (route.predicate().test(req)) { backend = route.backend(); break; } }
            System.out.println(req.path() + " (headers=" + req.headers() + ") -> " + backend);
        }
    }
}
```

**How to run:** `javac PathAndHeaderPredicate.java && java PathAndHeaderPredicate` (JDK 17+).

Expected output:
```
/orders/42 (headers={X-Beta-User=true}) -> order-service-v2
/orders/43 (headers={}) -> order-service-v1
```

The beta user, carrying the header, matches `beta_route`'s combined predicate and reaches the new backend; the regular user, lacking that header, falls through to `stable_route`.

### Level 3 — Advanced

```java
// File: PathHeaderAndTimeWindowPredicate.java -- adds a THIRD predicate dimension:
// a time window. The beta route is ONLY active during the rollout window,
// even for beta users -- outside it, everyone falls back to stable, automatically.
import java.time.*;
import java.util.*;
import java.util.function.*;

public class PathHeaderAndTimeWindowPredicate {
    record Request(String path, Map<String, String> headers, Instant requestTime) {}
    record Route(String name, Predicate<Request> predicate, String backend) {}

    public static void main(String[] args) {
        Instant rolloutStart = Instant.parse("2026-06-01T00:00:00Z");
        Instant rolloutEnd = Instant.parse("2026-06-30T23:59:59Z");

        List<Route> routes = List.of(
            new Route("beta_route",
                r -> r.path().startsWith("/orders")
                    && "true".equals(r.headers().get("X-Beta-User"))
                    && !r.requestTime().isBefore(rolloutStart)
                    && !r.requestTime().isAfter(rolloutEnd),  // path AND header AND time-window -- ALL THREE
                "order-service-v2"),
            new Route("stable_route", r -> r.path().startsWith("/orders"), "order-service-v1"));

        Request betaDuringRollout = new Request("/orders/42", Map.of("X-Beta-User", "true"), Instant.parse("2026-06-15T12:00:00Z"));
        Request betaAfterRollout = new Request("/orders/44", Map.of("X-Beta-User", "true"), Instant.parse("2026-07-15T12:00:00Z"));
        Request regularDuringRollout = new Request("/orders/43", Map.of(), Instant.parse("2026-06-15T12:00:00Z"));

        for (Request req : List.of(betaDuringRollout, betaAfterRollout, regularDuringRollout)) {
            String backend = "404";
            for (Route route : routes) { if (route.predicate().test(req)) { backend = route.backend(); break; } }
            System.out.println(req.path() + " at " + req.requestTime() + " (beta=" + req.headers().containsKey("X-Beta-User") + ") -> " + backend);
        }
    }
}
```

**How to run:** `javac PathHeaderAndTimeWindowPredicate.java && java PathHeaderAndTimeWindowPredicate` (JDK 17+).

Expected output:
```
/orders/42 at 2026-06-15T12:00:00Z (beta=true) -> order-service-v2
/orders/44 at 2026-07-15T12:00:00Z (beta=true) -> order-service-v1
/orders/43 at 2026-06-15T12:00:00Z (beta=false) -> order-service-v1
```

## 6. Walkthrough

1. **Level 1** — `request.path().startsWith("/orders")` is the *only* check performed, so the `"X-Beta-User"` header, despite being present in the request, has no effect at all on the routing outcome — every request matching the path lands on the same single backend.
2. **Level 2, the combined predicate** — `beta_route`'s predicate is a single lambda checking `r.path().startsWith("/orders") && "true".equals(r.headers().get("X-Beta-User"))`, evaluating both conditions with logical AND; only a request satisfying *both* clauses matches this route.
3. **Level 2, the fallback route's simplicity** — `stable_route`'s predicate checks only the path, making it a catch-all for any order-related request that didn't already match the more specific `beta_route` earlier in the routes list.
4. **Level 2, tracing the two test requests** — `betaUser` satisfies both of `beta_route`'s conditions and is routed to `order-service-v2`; `regularUser`, lacking the header, fails `beta_route`'s predicate, falls through to `stable_route`'s path-only check (which it satisfies), and is routed to `order-service-v1`.
5. **Level 3, adding the time-window condition** — `beta_route`'s predicate now includes `!r.requestTime().isBefore(rolloutStart) && !r.requestTime().isAfter(rolloutEnd)`, an inclusive range check requiring the request's timestamp to fall within the configured rollout window, combined with AND alongside the existing path and header checks.
6. **Level 3, a beta user during the window** — `betaDuringRollout`'s timestamp (`2026-06-15`) falls within `[rolloutStart, rolloutEnd]`, and it carries the beta header, so all three of `beta_route`'s conditions are satisfied, routing it to `order-service-v2`.
7. **Level 3, a beta user outside the window, and the automatic fallback** — `betaAfterRollout` carries the identical beta header as `betaDuringRollout`, but its timestamp (`2026-07-15`) falls after `rolloutEnd`, failing the time-window condition; because `beta_route`'s predicate requires *all three* conditions to hold, this single failed condition is enough to disqualify the route entirely, and the request falls through to `stable_route` — demonstrating that adding a time-window predicate automatically and correctly retires a beta rollout without requiring any manual intervention to disable it once the configured window closes, purely as a consequence of how the combined predicate evaluates.

## 7. Gotchas & takeaways

> **Gotcha:** predicates combine with AND, never OR, within a single route — expressing "match if the path is `/orders/**` OR the header `X-Legacy-Client` is present" requires either two separate routes (one per condition) pointing at the same backend, or a custom predicate; there is no built-in way to express OR logic within one route's predicate chain, and reaching for two routes with identical destinations is the standard workaround.

- Spring Cloud Gateway's built-in route predicates cover path, method, header, query parameter, cookie, host, and time-window matching, combinable with AND on a single route.
- Combining multiple predicate types lets a route express precise, multi-dimensional routing conditions — a specific path, from a specific client segment, during a specific time window — entirely as declarative configuration.
- Routes are evaluated in order, and a request falls through to the next route whenever it fails any one of the current route's combined predicate conditions.
- Time-window predicates are especially useful for automatically retiring temporary routing rules (beta rollouts, promotional periods) without requiring manual cleanup once the window closes.
- Built-in predicates only support AND combination within one route; expressing OR logic requires multiple routes sharing a destination, or a custom predicate implementation.
