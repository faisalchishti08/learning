---
card: spring-cloud
gi: 49
slug: actuator-api-for-gateway
title: "Actuator API for gateway"
---

## 1. What it is

Spring Boot Actuator exposes a dedicated `/actuator/gateway` set of endpoints for inspecting and even modifying Gateway's live routing configuration: `/actuator/gateway/routes` lists every currently active route, `/actuator/gateway/routes/{id}` inspects one route in detail, and (when enabled) `POST`/`DELETE` on `/actuator/gateway/routes/{id}` let routes be added or removed at runtime without a restart.

```properties
management.endpoint.gateway.enabled=true
management.endpoints.web.exposure.include=gateway,health,info
```

```
GET /actuator/gateway/routes
```

```json
[
  {
    "route_id": "orders-route",
    "uri": "lb://orders-service",
    "predicates": ["Paths: [/orders/**], match trailing slash: true"],
    "filters": ["[[AddRequestHeader ...]]", "[[StripPrefix ...]]"]
  }
]
```

## 2. Why & when

Route configuration usually lives in static YAML or the Java DSL, but *verifying* what's actually active — especially after a deploy, or when multiple configuration sources (YAML plus programmatic routes plus a discovery-driven route) combine — is exactly what the Actuator gateway endpoints are for. They answer "what did Gateway actually load?" directly from the running instance, rather than requiring you to trust that configuration matches intent.

Reach for the Actuator gateway API when:

- Debugging why a request isn't routing as expected — inspecting `/actuator/gateway/routes/{id}` shows the exact predicates and filters Gateway is evaluating, catching typos or misconfigured patterns that are easy to miss by eye in YAML.
- Confirming a deploy actually picked up an intended route change, without needing to trigger a real request and observe its behavior indirectly.
- Building operational tooling around Gateway — a dashboard that visualizes active routes, or an automated check that asserts expected routes exist after a rollout.

## 3. Core concept

```
 GET  /actuator/gateway/routes           -> list every active route
 GET  /actuator/gateway/routes/{id}      -> inspect one route's predicates & filters in detail
 POST /actuator/gateway/routes/{id}      -> add or replace a route definition at runtime (if enabled)
 DELETE /actuator/gateway/routes/{id}    -> remove a route at runtime (if enabled)
 POST /actuator/gateway/refresh          -> force Gateway to reload its route definitions
```

The endpoint surface mirrors CRUD operations against the live, in-memory route table Gateway is actually using to make routing decisions.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An operator queries the actuator gateway routes endpoint, which reads directly from the same in memory route table the gateway uses to route real traffic">
  <rect x="30" y="70" width="150" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">operator / tool</text>

  <line x1="180" y1="90" x2="250" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a49)"/>
  <text x="215" y="80" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">GET /actuator/gateway/routes</text>

  <rect x="255" y="20" width="330" height="140" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="420" y="40" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Gateway instance</text>

  <rect x="280" y="55" width="130" height="80" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="345" y="80" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">live in-memory</text>
  <text x="345" y="94" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">route table</text>

  <rect x="430" y="55" width="130" height="80" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="495" y="80" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">actual routing</text>
  <text x="495" y="94" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">of real traffic</text>

  <line x1="410" y1="95" x2="428" y2="95" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a49)"/>

  <defs><marker id="a49" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The Actuator endpoint reads from the exact same route table that's actively routing production traffic, so what it reports is always ground truth.

## 5. Runnable example

The scenario: model an operator using the gateway Actuator API to inspect and manage routes at runtime. Start with a read-only route listing, then add single-route inspection, then add runtime route addition and a forced refresh.

### Level 1 — Basic

Model `GET /actuator/gateway/routes`: list every currently active route.

```java
import java.util.*;

public class GatewayActuatorLevel1 {
    record Route(String id, String uri, List<String> predicates, List<String> filters) {}

    static List<Route> liveRoutes = new ArrayList<>(List.of(
            new Route("orders-route", "lb://orders-service", List.of("Path=/orders/**"), List.of("StripPrefix=1")),
            new Route("billing-route", "lb://billing-service", List.of("Path=/billing/**"), List.of())
    ));

    static List<Route> getRoutes() { return liveRoutes; } // GET /actuator/gateway/routes

    public static void main(String[] args) {
        System.out.println("GET /actuator/gateway/routes ->");
        for (Route r : getRoutes()) {
            System.out.println("  " + r.id() + " -> " + r.uri());
        }
    }
}
```

How to run: `java GatewayActuatorLevel1.java`

`getRoutes()` returns exactly the live route table — this is the simplest and most-used gateway Actuator endpoint: a quick sanity check of what routes actually exist on a running instance.

### Level 2 — Intermediate

Add single-route inspection with full predicate and filter detail, modeling `GET /actuator/gateway/routes/{id}`.

```java
import java.util.*;

public class GatewayActuatorLevel2 {
    record Route(String id, String uri, List<String> predicates, List<String> filters) {}

    static List<Route> liveRoutes = List.of(
            new Route("orders-route", "lb://orders-service",
                    List.of("Path=/orders/**", "Method=GET,POST"),
                    List.of("AddRequestHeader=X-Gateway-Source,gateway", "StripPrefix=1")),
            new Route("billing-route", "lb://billing-service", List.of("Path=/billing/**"), List.of())
    );

    static Optional<Route> getRoute(String id) { // GET /actuator/gateway/routes/{id}
        return liveRoutes.stream().filter(r -> r.id().equals(id)).findFirst();
    }

    public static void main(String[] args) {
        System.out.println("GET /actuator/gateway/routes/orders-route ->");
        getRoute("orders-route").ifPresent(r -> {
            System.out.println("  uri: " + r.uri());
            System.out.println("  predicates: " + r.predicates());
            System.out.println("  filters: " + r.filters());
        });

        System.out.println("GET /actuator/gateway/routes/unknown-route ->");
        System.out.println("  " + (getRoute("unknown-route").isPresent() ? "found" : "404 Not Found"));
    }
}
```

How to run: `java GatewayActuatorLevel2.java`

`getRoute(id)` surfaces the full detail of one route — every configured predicate and filter, exactly as Gateway is evaluating them — which is what makes this endpoint valuable for debugging: a route that "isn't matching" can be inspected directly to confirm its predicates are actually what you intended, rather than what you meant to type in YAML.

### Level 3 — Advanced

Add runtime route addition (`POST`) and a forced refresh, modeling adding a new route without restarting the gateway.

```java
import java.util.*;
import java.util.concurrent.*;

public class GatewayActuatorLevel3 {
    record Route(String id, String uri, List<String> predicates, List<String> filters) {}

    static Map<String, Route> liveRoutes = new ConcurrentHashMap<>();
    static {
        liveRoutes.put("orders-route", new Route("orders-route", "lb://orders-service", List.of("Path=/orders/**"), List.of()));
    }

    static List<Route> getRoutes() { return new ArrayList<>(liveRoutes.values()); }

    static void addOrReplaceRoute(Route route) { // POST /actuator/gateway/routes/{id}
        liveRoutes.put(route.id(), route);
        System.out.println("[actuator] route added/replaced: " + route.id());
    }

    static void deleteRoute(String id) { // DELETE /actuator/gateway/routes/{id}
        liveRoutes.remove(id);
        System.out.println("[actuator] route removed: " + id);
    }

    static void refresh() { // POST /actuator/gateway/refresh
        System.out.println("[actuator] route cache refreshed -- " + liveRoutes.size() + " routes now active");
    }

    public static void main(String[] args) {
        System.out.println("before: " + getRoutes().stream().map(Route::id).toList());

        // an operator (or an automated process) adds a new route at runtime, no restart needed
        addOrReplaceRoute(new Route("promotions-route", "lb://promotions-service", List.of("Path=/promotions/**"), List.of()));
        refresh();

        System.out.println("after add: " + getRoutes().stream().map(Route::id).toList());

        deleteRoute("orders-route"); // decommissioning a route, e.g. during a migration
        refresh();

        System.out.println("after delete: " + getRoutes().stream().map(Route::id).toList());
    }
}
```

How to run: `java GatewayActuatorLevel3.java`

`addOrReplaceRoute` and `deleteRoute` directly mutate the live route table (a `ConcurrentHashMap` here, standing in for Gateway's internal thread-safe route store, since real traffic could be routing concurrently with an operator's changes) — this models `POST`/`DELETE /actuator/gateway/routes/{id}` genuinely changing routing behavior on a running instance without any restart or redeploy. `refresh()` models forcing Gateway to reload and re-index its route definitions, which some configuration sources (like a database-backed route repository) require explicitly after a change.

## 6. Walkthrough

Trace Level 3's sequence.

1. The first `println` calls `getRoutes()` and prints `[orders-route]` — this models an operator's initial `GET /actuator/gateway/routes` call, confirming only the one statically-configured route exists before any changes.
2. `addOrReplaceRoute(new Route("promotions-route", ...))` runs — this models a `POST` to `/actuator/gateway/routes/promotions-route` with a JSON body describing the new route's URI, predicates, and filters. The map is updated immediately, and `refresh()` is called right after, modeling a real deployment where some route sources need an explicit refresh signal to pick up the change.
3. The second `println` shows `getRoutes()` now returns both `orders-route` and `promotions-route` — confirming, exactly as an operator would via the real endpoint, that the new route is genuinely active and routable, without ever restarting the process.
4. `deleteRoute("orders-route")` runs — this models a `DELETE /actuator/gateway/routes/orders-route` call, perhaps as part of decommissioning that route during a service migration. The map entry is removed and `refresh()` is called again.
5. The final `println` shows only `promotions-route` remains — the whole lifecycle (add, verify, delete, verify) happened entirely through the Actuator API, with each step immediately observable via the same read endpoint used at the start.

```
GET  /actuator/gateway/routes           -> [orders-route]
POST /actuator/gateway/routes/promotions-route  -> added
POST /actuator/gateway/refresh          -> route cache reloaded
GET  /actuator/gateway/routes           -> [orders-route, promotions-route]
DELETE /actuator/gateway/routes/orders-route    -> removed
GET  /actuator/gateway/routes           -> [promotions-route]
```

## 7. Gotchas & takeaways

> **Gotcha:** runtime route mutation via `POST`/`DELETE /actuator/gateway/routes/{id}` only affects the *running instance's* in-memory route table — it does not persist back to the YAML file or database the routes were originally configured from. A restart or redeploy reverts to whatever the static configuration says, silently undoing any runtime changes unless they're also reflected in the actual configuration source.

- `/actuator/gateway/routes` and `/actuator/gateway/routes/{id}` are read-only and safe to use liberally for debugging — they report exactly what's active, which is the most reliable way to confirm routing configuration actually took effect.
- Runtime route mutation endpoints are powerful but should generally be locked down (via Spring Security, `management.endpoint.gateway.enabled`, or network-level access control) in production — they let anyone with access change live routing behavior instantly.
- Actuator's gateway endpoints, like all Actuator endpoints, need explicit exposure via `management.endpoints.web.exposure.include` — they're not on by default, a deliberate security default worth remembering when they "don't seem to exist" on a fresh setup.
- Combining the Actuator gateway API with monitoring tooling (a dashboard, an automated post-deploy check) turns "trust that the YAML deployed correctly" into "verify the actual running route table matches intent."
