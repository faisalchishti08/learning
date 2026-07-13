---
card: microservices
gi: 181
slug: legacy-spring-cloud-netflix-zuul-deprecated-awareness
title: "Legacy Spring Cloud Netflix Zuul (deprecated) awareness"
---

## 1. What it is

Zuul was Netflix's original API gateway, and Spring Cloud Netflix Zuul was the Spring integration wrapping it — the gateway solution Spring applications used before [Spring Cloud Gateway](0171-spring-cloud-gateway-reactive-webflux-based.md) existed. Zuul (both the original Netflix version and its Spring integration) is now in maintenance mode / deprecated in favor of Spring Cloud Gateway; awareness of it matters mainly for recognizing and migrating legacy systems that still use it, not for building anything new.

## 2. Why & when

Zuul 1.x was built on a blocking, servlet-based model with its own filter-chain architecture (pre, route, post, and error filter types) predating Spring Cloud Gateway's reactive foundation and its now-standard predicate/filter configuration style. Netflix itself moved away from actively developing Zuul in favor of other internal tools, and Spring's own ecosystem consolidated around Spring Cloud Gateway as the recommended, actively maintained gateway solution — meaning Zuul-based systems, while still functional, are running on an architecture that won't receive the ongoing feature development, performance improvements, or long-term community support that Spring Cloud Gateway does.

Recognize Zuul-based configuration when working in an older Spring Cloud codebase (`spring-cloud-starter-netflix-zuul` as a dependency, `zuul.routes.*` configuration properties, or filter classes extending `ZuulFilter`), and plan a migration to Spring Cloud Gateway when that codebase is due for modernization — not necessarily urgently, since Zuul continues to function, but as accumulating technical debt worth addressing deliberately rather than indefinitely. Do not use Zuul for any new gateway implementation; Spring Cloud Gateway is the only actively recommended choice for new Spring-based gateways today.

## 3. Core concept

Zuul's route configuration and filter model map conceptually onto Spring Cloud Gateway's predicate/filter model, but with different terminology and a different underlying execution model — recognizing this mapping is what makes a Zuul-to-Gateway migration tractable, since the concepts (route to a backend by path, filter requests before/after forwarding) carry over even though the specific APIs and configuration syntax do not.

```java
// ZUUL (legacy) -- route configuration via properties
zuul.routes.order-service.path: /orders/**
zuul.routes.order-service.url: http://order-service:8080

// ZUUL (legacy) -- a pre-filter, extending ZuulFilter
public class AuthZuulFilter extends ZuulFilter {
    public String filterType() { return "pre"; } // pre/route/post/error -- Zuul's OWN filter type vocabulary
    public Object run() { /* auth logic */ return null; }
}

// SPRING CLOUD GATEWAY (current) -- the CONCEPTUAL equivalent, different syntax
.route("order_route", r -> r.path("/orders/**").uri("http://order-service:8080"))
.filters(f -> f.filter(authGatewayFilter)) // GatewayFilter, not ZuulFilter
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Zuul's route and filter concepts map onto Spring Cloud Gateway's equivalent concepts: Zuul routes correspond to Gateway routes with path predicates, and Zuul's pre/route/post filter types correspond to Gateway's pre/post GatewayFilter phases" >
  <rect x="20" y="20" width="240" height="130" rx="8" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="140" y="40" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Zuul (deprecated)</text>
  <text x="40" y="65" fill="#e6edf3" font-size="7.5" font-family="sans-serif">zuul.routes.*</text>
  <text x="40" y="90" fill="#e6edf3" font-size="7.5" font-family="sans-serif">ZuulFilter (pre/route/post/error)</text>
  <text x="40" y="115" fill="#e6edf3" font-size="7.5" font-family="sans-serif">blocking, servlet-based</text>

  <rect x="360" y="20" width="260" height="130" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="40" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring Cloud Gateway (current)</text>
  <text x="380" y="65" fill="#e6edf3" font-size="7.5" font-family="sans-serif">RouteLocator / predicates</text>
  <text x="380" y="90" fill="#e6edf3" font-size="7.5" font-family="sans-serif">GatewayFilter (pre/post phases)</text>
  <text x="380" y="115" fill="#e6edf3" font-size="7.5" font-family="sans-serif">reactive OR virtual-thread MVC</text>

  <line x1="260" y1="85" x2="358" y2="85" stroke="#8b949e" marker-end="url(#arr62)"/>

  <defs>
    <marker id="arr62" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Zuul's concepts have direct, recognizable equivalents in Spring Cloud Gateway, making migration a translation exercise rather than a redesign.

## 5. Runnable example

Scenario: a legacy order-routing gateway that starts modeled in Zuul's route-and-filter style (showing the older architecture's shape), is migrated to the equivalent Spring Cloud Gateway style with the same routing and filtering behavior preserved, and finally demonstrates the migration mapping applied to a second, filter-heavy route, confirming the conceptual translation generalizes rather than being a one-off coincidence.

### Level 1 — Basic

```java
// File: ZuulStyleRouting.java -- models the SHAPE of Zuul's legacy route +
// filter-type configuration, for comparison with what replaces it.
import java.util.*;

public class ZuulStyleRouting {
    record ZuulRoute(String path, String url) {}

    // Zuul's filter TYPES were explicit strings: "pre", "route", "post", "error"
    interface ZuulFilter { String filterType(); String run(String path); }

    static ZuulFilter authFilter = new ZuulFilter() {
        public String filterType() { return "pre"; } // Zuul's OWN vocabulary
        public String run(String path) { System.out.println("  [ZuulFilter type=pre] auth check for " + path); return null; }
    };

    public static void main(String[] args) {
        Map<String, ZuulRoute> zuulRoutes = Map.of("order-service", new ZuulRoute("/orders/**", "http://order-service:8080"));

        String path = "/orders/42";
        authFilter.run(path);
        ZuulRoute route = zuulRoutes.get("order-service");
        System.out.println("[Zuul routing] " + path + " -> " + route.url());
        System.out.println("This is LEGACY Zuul's shape: zuul.routes.* config PLUS ZuulFilter classes with explicit filterType() strings.");
    }
}
```

**How to run:** `javac ZuulStyleRouting.java && java ZuulStyleRouting` (JDK 17+).

### Level 2 — Intermediate

```java
// File: MigratedToGatewayStyle.java -- the SAME routing and filtering behavior,
// expressed in Spring Cloud Gateway's route/predicate/filter model instead.
import java.util.*;
import java.util.function.*;

public class MigratedToGatewayStyle {
    record GatewayRoute(String id, Predicate<String> pathPredicate, String uri) {}
    interface GatewayFilter { String apply(String path, Supplier<String> next); }

    static GatewayFilter authGatewayFilter = (path, next) -> {
        System.out.println("  [GatewayFilter, pre-phase] auth check for " + path); // the PRE logic, same concept, NEW vocabulary
        return next.get();
    };

    public static void main(String[] args) {
        GatewayRoute orderRoute = new GatewayRoute(
            "order_route",
            p -> p.startsWith("/orders"), // the EQUIVALENT of Zuul's "path" property, now a predicate
            "http://order-service:8080");  // the EQUIVALENT of Zuul's "url" property

        String path = "/orders/42";
        if (orderRoute.pathPredicate().test(path)) {
            String result = authGatewayFilter.apply(path, () -> "[Gateway routing] " + path + " -> " + orderRoute.uri());
            System.out.println(result);
        }
        System.out.println("SAME routing outcome, SAME filter concept -- expressed in Spring Cloud Gateway's CURRENT vocabulary instead of Zuul's.");
    }
}
```

**How to run:** `javac MigratedToGatewayStyle.java && java MigratedToGatewayStyle` (JDK 17+).

Expected output:
```
  [GatewayFilter, pre-phase] auth check for /orders/42
[Gateway routing] /orders/42 -> http://order-service:8080
SAME routing outcome, SAME filter concept -- expressed in Spring Cloud Gateway's CURRENT vocabulary instead of Zuul's.
```

### Level 3 — Advanced

```java
// File: SecondRouteConfirmsGeneralization.java -- migrates a SECOND, more
// filter-heavy Zuul route (with a pre AND a post filter) to confirm the
// Zuul -> Gateway mapping generalizes, not just a one-off coincidence.
import java.util.*;
import java.util.function.*;

public class SecondRouteConfirmsGeneralization {
    // === the ZUUL-STYLE original, for a customer route with TWO filter types ===
    interface ZuulFilter { String filterType(); void run(String path); }
    static ZuulFilter zuulPreFilter = new ZuulFilter() {
        public String filterType() { return "pre"; }
        public void run(String path) { System.out.println("  [Zuul pre] validating request to " + path); }
    };
    static ZuulFilter zuulPostFilter = new ZuulFilter() {
        public String filterType() { return "post"; }
        public void run(String path) { System.out.println("  [Zuul post] adding response header for " + path); }
    };

    static void handleViaZuulStyle(String path) {
        zuulPreFilter.run(path);
        System.out.println("[Zuul routing] " + path + " -> http://customer-service:8081");
        zuulPostFilter.run(path);
    }

    // === the MIGRATED Spring Cloud Gateway equivalent -- SAME two-filter-phase behavior ===
    interface GatewayFilter { void apply(String path, Runnable next); }
    static GatewayFilter gatewayCombinedFilter = (path, next) -> {
        System.out.println("  [GatewayFilter, PRE phase] validating request to " + path); // maps from Zuul's "pre" type
        next.run();
        System.out.println("  [GatewayFilter, POST phase] adding response header for " + path); // maps from Zuul's "post" type
    };

    static void handleViaGatewayStyle(String path) {
        gatewayCombinedFilter.apply(path, () -> System.out.println("[Gateway routing] " + path + " -> http://customer-service:8081"));
    }

    public static void main(String[] args) {
        System.out.println("=== legacy Zuul-style handling ===");
        handleViaZuulStyle("/customers/7");

        System.out.println("\n=== migrated Spring Cloud Gateway-style handling ===");
        handleViaGatewayStyle("/customers/7");

        System.out.println("\nBoth Zuul's separate pre/post ZuulFilter TYPES and Gateway's single pre/post-phase GatewayFilter produced the IDENTICAL observable behavior -- the migration preserved behavior while modernizing the underlying model.");
    }
}
```

**How to run:** `javac SecondRouteConfirmsGeneralization.java && java SecondRouteConfirmsGeneralization` (JDK 17+).

Expected output:
```
=== legacy Zuul-style handling ===
  [Zuul pre] validating request to /customers/7
[Zuul routing] /customers/7 -> http://customer-service:8081
  [Zuul post] adding response header for /customers/7

=== migrated Spring Cloud Gateway-style handling ===
  [GatewayFilter, PRE phase] validating request to /customers/7
  [Gateway routing] /customers/7 -> http://customer-service:8081
  [GatewayFilter, POST phase] adding response header for /customers/7

Both Zuul's separate pre/post ZuulFilter TYPES and Gateway's single pre/post-phase GatewayFilter produced the IDENTICAL observable behavior -- the migration preserved behavior while modernizing the underlying model.
```

## 6. Walkthrough

1. **Level 1** — `zuulRoutes` models Zuul's `zuul.routes.*` property-based configuration as a simple map, and `authFilter`'s `filterType()` method returning the literal string `"pre"` mirrors how a real `ZuulFilter` subclass declares which of Zuul's four filter types (pre, route, post, error) it represents.
2. **Level 2, the routing concept translated** — `GatewayRoute`'s `pathPredicate` field replaces Zuul's `path` string property with an actual `Predicate<String>`, and `uri` replaces Zuul's `url` property; the underlying idea (map a path pattern to a backend address) is unchanged, only the representation.
3. **Level 2, the filter concept translated** — `authGatewayFilter` performs the identical logical action as `authFilter` from Level 1 (log an auth check before proceeding), but is expressed as a `GatewayFilter` taking a `next` continuation, rather than Zuul's separate `filterType()`-tagged class structure.
4. **Level 2, the observable equivalence** — both levels produce a log line for the auth check followed by a routing log line, in the same order, for the same input path — confirming the migration preserved the actual runtime behavior while changing only the code's shape and vocabulary.
5. **Level 3, a Zuul route using both pre and post filter types** — `handleViaZuulStyle` explicitly calls `zuulPreFilter.run(path)` before the routing log line and `zuulPostFilter.run(path)` after it, modeling how Zuul dispatches separately-typed filter instances at different points in the request lifecycle.
6. **Level 3, one Gateway filter spanning both phases** — `gatewayCombinedFilter`'s single lambda body contains logic both before and after calling `next.run()`, mirroring how a modern `GatewayFilter` (as covered in [gateway filters](0174-gateway-filters-pre-post-global.md)) expresses both pre- and post-phase logic within one implementation, rather than Zuul's separate pre-typed and post-typed filter classes.
7. **Level 3, confirming the mapping generalizes** — running both `handleViaZuulStyle` and `handleViaGatewayStyle` against the identical `"/customers/7"` path produces the same three-step sequence of log lines (pre-check, route, post-action) in both cases, just through structurally different code — this side-by-side comparison, applied to a second, filter-heavier route beyond the first example's simpler case, is what confirms the Zuul-to-Gateway conceptual mapping is a genuine, generalizable migration pattern rather than a coincidence specific to one simple route.

## 7. Gotchas & takeaways

> **Gotcha:** a Zuul-to-Gateway migration is a genuine architecture change, not a pure configuration find-and-replace — Zuul 1.x's blocking, servlet-based execution model differs fundamentally from Spring Cloud Gateway's reactive (or virtual-thread-based MVC) model, so a migration is also an opportunity (and often a necessity) to revisit any blocking assumptions baked into existing Zuul filter code, not just a mechanical translation of route configuration syntax.

- Zuul (and its Spring Cloud Netflix integration) is Spring's deprecated, legacy API gateway solution, superseded by Spring Cloud Gateway as the actively recommended choice.
- Zuul's route configuration and its pre/route/post/error `ZuulFilter` types have direct conceptual equivalents in Spring Cloud Gateway's predicate-based routes and pre/post-phase `GatewayFilter`s.
- Recognizing this conceptual mapping is what makes migrating a legacy Zuul-based gateway to Spring Cloud Gateway a tractable translation exercise rather than a from-scratch redesign.
- No new gateway implementation should be built on Zuul today; awareness of it is primarily useful for recognizing and planning migration of existing legacy systems.
- The migration is also an architectural shift (blocking servlet model to reactive or virtual-thread model), not merely a configuration syntax change, and existing filter logic should be reviewed for blocking assumptions during the migration, not just mechanically translated.
