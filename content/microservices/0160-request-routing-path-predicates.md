---
card: microservices
gi: 160
slug: request-routing-path-predicates
title: "Request routing & path predicates"
---

## 1. What it is

Request routing is the gateway's core job of deciding which backend a given request should go to; a predicate is the boolean condition — matched against the request's path, method, headers, or query parameters — that determines whether a specific route applies. Path predicates specifically match against the request's URL path, often using patterns (`/orders/**`, `/orders/{id}`) rather than exact strings, so one route definition can match many concrete request paths.

## 2. Why & when

A hard-coded, exact-match routing table (`"/orders/42" -> order-service`) would need a new entry for every single possible request path, which is obviously unworkable — real systems have an effectively unbounded number of concrete paths (one per resource id) but a small, fixed number of *route shapes*. Path predicates solve this by matching a pattern against the structure of a path rather than its exact value, so one route definition (`/orders/**`) correctly handles every order-related request regardless of which specific order id appears in it.

Design path predicates to mirror the actual API structure being exposed: broad prefix patterns (`/orders/**`) for routing entire resource families to one backend, more specific patterns (`/orders/{id}/fulfillment-status`) when a sub-resource needs to go somewhere different, and predicates on other request attributes (HTTP method, headers) when path alone isn't a sufficient routing signal — for instance, routing `GET /orders/**` to a read-optimized replica service while `POST /orders/**` goes to the primary write service.

## 3. Core concept

A route consists of a predicate (does this request match?) and a destination; predicates are evaluated against each incoming request, generally in a defined priority order, with the request forwarded to the first (or best) matching route's destination.

```java
// path predicate with a wildcard segment -- matches /orders/42, /orders/999, etc., ALL of them
predicate: path("/orders/**") -> destination: order-service

// a MORE SPECIFIC predicate for a sub-resource, evaluated with higher priority
predicate: path("/orders/*/fulfillment-status") -> destination: order-fulfillment-service

// a predicate combining PATH and METHOD -- routes reads and writes differently
predicate: path("/orders/**") && method("GET")  -> destination: order-read-replica-service
predicate: path("/orders/**") && method("POST") -> destination: order-write-service
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three routes are evaluated for an incoming GET /orders/42 request; the most specific matching predicate (path plus method) wins over a broader path-only predicate" >
  <rect x="20" y="80" width="160" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">GET /orders/42</text>

  <rect x="240" y="20" width="220" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="350" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">path(/orders/**) &amp;&amp; method(GET) -- MATCH</text>

  <rect x="240" y="75" width="220" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="350" y="97" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">path(/orders/**) &amp;&amp; method(POST) -- no match</text>

  <rect x="240" y="130" width="220" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="350" y="152" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">path(/customers/**) -- no match</text>

  <line x1="180" y1="95" x2="238" y2="38" stroke="#8b949e" marker-end="url(#arr41)"/>

  <defs>
    <marker id="arr41" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each route's predicate is checked independently; only the route whose predicate genuinely matches receives the request.

## 5. Runnable example

Scenario: an order-gateway that starts with brittle exact-path matching (showing why it fails to scale), moves to wildcard path pattern matching that correctly handles any order id, and finally combines path patterns with HTTP method predicates to route reads and writes to different backends.

### Level 1 — Basic

```java
// File: ExactPathMatching.java -- routes must match the EXACT path string;
// fails the instant a new, unlisted order id appears.
import java.util.*;

public class ExactPathMatching {
    public static void main(String[] args) {
        Map<String, String> exactRoutes = new HashMap<>();
        exactRoutes.put("/orders/42", "order-service"); // only THIS specific id is routed correctly
        exactRoutes.put("/orders/43", "order-service");

        String[] incomingPaths = {"/orders/42", "/orders/999"}; // 999 was never explicitly registered
        for (String path : incomingPaths) {
            String backend = exactRoutes.getOrDefault(path, "404 - no route");
            System.out.println(path + " -> " + backend);
        }
        System.out.println("A NEW order id requires adding a NEW exact-match entry -- completely unworkable at real scale.");
    }
}
```

**How to run:** `javac ExactPathMatching.java && java ExactPathMatching` (JDK 17+).

### Level 2 — Intermediate

```java
// File: WildcardPathPatterns.java -- ONE route pattern correctly matches EVERY
// order id, using a wildcard segment instead of an exact string.
import java.util.*;
import java.util.regex.*;

public class WildcardPathPatterns {
    static class PathPredicate {
        Pattern compiled;
        String originalPattern;
        PathPredicate(String antStylePattern) {
            this.originalPattern = antStylePattern;
            // convert "/orders/**" style patterns into a regex -- ** matches ANY remaining path segments
            String regex = antStylePattern.replace("**", ".*").replace("*", "[^/]+");
            this.compiled = Pattern.compile("^" + regex + "$");
        }
        boolean matches(String path) { return compiled.matcher(path).matches(); }
    }

    record Route(PathPredicate predicate, String backend) {}

    public static void main(String[] args) {
        List<Route> routes = List.of(
            new Route(new PathPredicate("/orders/**"), "order-service"),
            new Route(new PathPredicate("/customers/**"), "customer-service"));

        String[] incomingPaths = {"/orders/42", "/orders/999", "/orders/999/items", "/customers/7"};
        for (String path : incomingPaths) {
            String backend = "404 - no route";
            for (Route route : routes) {
                if (route.predicate().matches(path)) { backend = route.backend(); break; }
            }
            System.out.println(path + " -> " + backend);
        }
        System.out.println("ONE '/orders/**' pattern correctly routed EVERY order-related path, regardless of id.");
    }
}
```

**How to run:** `javac WildcardPathPatterns.java && java WildcardPathPatterns` (JDK 17+).

Expected output:
```
/orders/42 -> order-service
/orders/999 -> order-service
/orders/999/items -> order-service
/customers/7 -> customer-service
ONE '/orders/**' pattern correctly routed EVERY order-related path, regardless of id.
```

### Level 3 — Advanced

```java
// File: PathAndMethodPredicates.java -- combining PATH pattern with HTTP METHOD
// to route reads and writes for the SAME resource to DIFFERENT backends.
import java.util.*;
import java.util.function.*;
import java.util.regex.*;

public class PathAndMethodPredicates {
    record Request(String method, String path) {}

    static class PathPredicate {
        Pattern compiled;
        PathPredicate(String antStylePattern) {
            String regex = antStylePattern.replace("**", ".*").replace("*", "[^/]+");
            this.compiled = Pattern.compile("^" + regex + "$");
        }
        boolean matches(String path) { return compiled.matcher(path).matches(); }
    }

    record Route(String name, Predicate<Request> predicate, String backend) {}

    public static void main(String[] args) {
        PathPredicate ordersPattern = new PathPredicate("/orders/**");

        List<Route> routes = List.of(
            // MORE SPECIFIC route (path + method) evaluated FIRST
            new Route("read-route", r -> ordersPattern.matches(r.path()) && r.method().equals("GET"), "order-read-replica-service"),
            new Route("write-route", r -> ordersPattern.matches(r.path()) && r.method().equals("POST"), "order-write-service"),
            // BROADER fallback for anything else under /orders
            new Route("fallback-route", r -> ordersPattern.matches(r.path()), "order-service"));

        Request[] incoming = {
            new Request("GET", "/orders/42"), new Request("POST", "/orders"), new Request("DELETE", "/orders/42")};

        for (Request req : incoming) {
            String matchedRouteName = "404 - no route";
            String backend = "404 - no route";
            for (Route route : routes) {
                if (route.predicate().test(req)) { matchedRouteName = route.name(); backend = route.backend(); break; }
            }
            System.out.println(req.method() + " " + req.path() + " -> [" + matchedRouteName + "] " + backend);
        }
        System.out.println("GET traffic went to the READ replica; POST traffic went to the WRITE service; DELETE fell back to the general service -- ALL from the SAME path pattern, differentiated by method.");
    }
}
```

**How to run:** `javac PathAndMethodPredicates.java && java PathAndMethodPredicates` (JDK 17+).

Expected output:
```
GET /orders/42 -> [read-route] order-read-replica-service
POST /orders -> [write-route] order-write-service
DELETE /orders/42 -> [fallback-route] order-service
GET traffic went to the READ replica; POST traffic went to the WRITE service; DELETE fell back to the general service -- ALL from the SAME path pattern, differentiated by method.
```

## 6. Walkthrough

1. **Level 1** — `exactRoutes` is a plain `Map<String, String>` keyed by the literal path string; `/orders/999`, never explicitly registered, correctly falls through to the `"404 - no route"` default, exposing that this approach requires foreknowledge of every possible concrete path.
2. **Level 2, compiling a pattern into a matcher** — `PathPredicate`'s constructor translates an Ant-style pattern (`**` for "any remaining segments", `*` for "exactly one segment") into an equivalent regular expression, giving `matches` a genuine structural test rather than an exact-string comparison.
3. **Level 2, one pattern matching many paths** — all three `/orders/...` test paths (`/orders/42`, `/orders/999`, `/orders/999/items`) match the single registered `"/orders/**"` predicate, because `**` is translated to `.*`, which matches any sequence of characters including further path segments.
4. **Level 2, routes remaining independent** — `/customers/7` correctly matches only the separately registered `"/customers/**"` route, demonstrating that multiple pattern-based routes coexist and are each evaluated independently against the incoming path.
5. **Level 3, layering a second predicate dimension** — each `Route`'s `predicate` is now a `Predicate<Request>` combining `ordersPattern.matches(r.path())` with a check on `r.method()`, meaning the routing decision now depends on two independent request attributes rather than path alone.
6. **Level 3, ordering by specificity** — `read-route` and `write-route`, both requiring a specific method *in addition to* the path pattern, are listed before the broader `fallback-route`, which matches on path alone; the `for` loop's `break` on first match means more specific routes are checked, and given priority, before the general fallback.
7. **Level 3, tracing the three requests** — `GET /orders/42` matches `read-route` (path matches, method is GET) and stops there without ever reaching `fallback-route`; `POST /orders` matches `write-route` similarly; `DELETE /orders/42` fails both `read-route` and `write-route`'s method checks, falls through to `fallback-route` (which only checks path), and is routed there — demonstrating a realistic combined-predicate routing setup where more specific rules take priority, and less specific rules serve as a catch-all for cases the specific rules don't address.

## 7. Gotchas & takeaways

> **Gotcha:** route evaluation order matters whenever more than one route's predicate could match the same request — placing a broad, catch-all predicate before a more specific one means the specific route is silently unreachable, since the broader one always matches first and short-circuits evaluation; route ordering (most specific first) is a real, easy-to-get-backward design decision, not an implementation detail.

- Path predicates let one route definition match an unbounded number of concrete request paths by matching structure (via patterns like `**` and `*`) rather than exact strings.
- Real gateways combine multiple predicate dimensions — path, HTTP method, headers, query parameters — to make more precise routing decisions than path alone can express.
- Route evaluation order matters when predicates can overlap; more specific routes need to be checked before broader, catch-all ones, or the specific route becomes unreachable.
- Designing path predicates to mirror the actual API's resource structure (`/orders/**` for the whole family, more specific patterns for sub-resources) keeps the routing table's structure aligned with the API's own structure.
- Combining path and method predicates enables realistic patterns like routing reads and writes for the same resource to different backend services.
