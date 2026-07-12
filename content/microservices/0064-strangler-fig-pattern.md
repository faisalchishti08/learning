---
card: microservices
gi: 64
slug: strangler-fig-pattern
title: "Strangler fig pattern"
---

## 1. What it is

The strangler fig pattern is a strategy for migrating a monolith to microservices gradually, without a risky big-bang rewrite. It is named after the strangler fig vine, which grows around a host tree, slowly takes over its structural role, and eventually the original tree can be removed while the fig continues standing in its place. In software, a **routing facade** sits in front of the monolith and, request by request, redirects functionality to new services as they are built — while everything not yet migrated keeps flowing straight through to the old monolith, unchanged.

## 2. Why & when

Rewriting a large monolith from scratch is one of the riskiest moves in software: it takes a long time, the business does not stop needing new features while it happens, and the rewrite typically only proves itself correct on the day it fully replaces the old system — a single, high-stakes cutover. The strangler fig pattern avoids that all-or-nothing bet: each piece of functionality is migrated and verified independently, in production, behind the routing facade, while the rest of the system keeps working exactly as it did before. If a migrated piece has a problem, only that piece needs attention — the routing facade can even redirect that one route back to the monolith while the fix is made.

Reach for this pattern whenever you're decomposing an existing monolith with real, still-growing traffic and cannot afford extended downtime or a single giant cutover. It is far less relevant for a brand-new system with no existing monolith to strangle.

## 3. Core concept

A routing facade decides, per request, whether the new microservice or the old monolith should handle it — and that decision can change over time as more functionality migrates, without clients ever needing to know.

```
Client --> [Routing Facade] --route by path-->  /orders/**   -> NEW OrderService (migrated)
                                              -> everything else -> OLD Monolith (not yet migrated)
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A routing facade sits in front of client traffic, sending migrated routes to a new microservice and all other routes to the old monolith">
  <rect x="20" y="90" width="90" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="65" y="114" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Client</text>

  <rect x="180" y="80" width="160" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="260" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Routing Facade</text>
  <text x="260" y="122" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">routes by path/feature</text>

  <rect x="420" y="20" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService (NEW)</text>
  <text x="510" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">migrated routes</text>

  <rect x="420" y="150" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="172" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Monolith (OLD)</text>
  <text x="510" y="188" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">everything not yet migrated</text>

  <line x1="110" y1="110" x2="180" y2="110" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="340" y1="95" x2="420" y2="50" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="340" y1="125" x2="420" y2="170" stroke="#79c0ff" stroke-width="1.5"/>
</svg>

The facade grows the "new" side and shrinks the "old" side over time, one route at a time.

## 5. Runnable example

Scenario: a monolithic order-lookup endpoint, first replaced by a routing facade that hard-routes everything to the monolith (no behavior change yet), then extended to route the migrated `/orders/**` path to a new service, and finally hardened with a fallback so a new-service failure doesn't take the whole system down.

### Level 1 — Basic

```java
// File: MonolithOnly.java -- baseline: everything is handled by the
// "monolith" directly, nothing has been strangled yet.
import java.util.*;

public class MonolithOnly {
    static class Monolith {
        String handle(String path) {
            return "monolith handled: " + path;
        }
    }

    public static void main(String[] args) {
        Monolith monolith = new Monolith();
        for (String path : List.of("/orders/1", "/customers/9", "/reports/daily")) {
            System.out.println(monolith.handle(path));
        }
    }
}
```

**How to run:** `javac MonolithOnly.java && java MonolithOnly` (JDK 17+).

Expected output:
```
monolith handled: /orders/1
monolith handled: /customers/9
monolith handled: /reports/daily
```

Every request goes straight to the monolith. This is the pre-migration starting point.

### Level 2 — Intermediate

```java
// File: RoutingFacade.java -- introduce the routing facade. It routes
// the migrated /orders/** path to the NEW service, and routes everything
// else straight through to the monolith, unchanged.
import java.util.*;

public class RoutingFacade {
    static class Monolith {
        String handle(String path) { return "monolith handled: " + path; }
    }

    static class OrderService {
        String handle(String path) { return "OrderService (new) handled: " + path; }
    }

    static class Facade {
        Monolith monolith = new Monolith();
        OrderService orderService = new OrderService();

        String route(String path) {
            if (path.startsWith("/orders/")) {
                return orderService.handle(path);
            }
            return monolith.handle(path);
        }
    }

    public static void main(String[] args) {
        Facade facade = new Facade();
        for (String path : List.of("/orders/1", "/customers/9", "/reports/daily")) {
            System.out.println(facade.route(path));
        }
    }
}
```

**How to run:** `javac RoutingFacade.java && java RoutingFacade` (JDK 17+).

Expected output:
```
OrderService (new) handled: /orders/1
monolith handled: /customers/9
monolith handled: /reports/daily
```

Clients still call the same facade with the same paths, but `/orders/1` now silently flows to the new `OrderService`, while `/customers/9` and `/reports/daily` still flow to the monolith exactly as before — the strangling has begun, one route at a time, invisibly to the caller.

### Level 3 — Advanced

```java
// File: RoutingFacadeWithFallback.java -- harden the facade: if the new
// OrderService fails, fall back to the monolith rather than failing the
// whole request -- critical during migration, when the new service is
// still earning trust in production.
import java.util.*;
import java.util.function.Function;

public class RoutingFacadeWithFallback {
    static class Monolith {
        String handle(String path) { return "monolith handled: " + path; }
    }

    static class FlakyOrderService {
        String handle(String path) {
            if (path.equals("/orders/2")) {
                throw new RuntimeException("OrderService timeout for " + path);
            }
            return "OrderService (new) handled: " + path;
        }
    }

    static class Facade {
        Monolith monolith = new Monolith();
        FlakyOrderService orderService = new FlakyOrderService();

        String route(String path) {
            if (path.startsWith("/orders/")) {
                try {
                    return orderService.handle(path);
                } catch (RuntimeException e) {
                    System.out.println("  [fallback triggered: " + e.getMessage() + "]");
                    return monolith.handle(path); // fall back to the still-correct old path
                }
            }
            return monolith.handle(path);
        }
    }

    public static void main(String[] args) {
        Facade facade = new Facade();
        for (String path : List.of("/orders/1", "/orders/2", "/customers/9")) {
            System.out.println(facade.route(path));
        }
    }
}
```

**How to run:** `javac RoutingFacadeWithFallback.java && java RoutingFacadeWithFallback` (JDK 17+).

Expected output:
```
OrderService (new) handled: /orders/1
  [fallback triggered: OrderService timeout for /orders/2]
monolith handled: /orders/2
OrderService (new) handled: /customers/9
```

Note the last line: `/customers/9` doesn't start with `/orders/`, so it goes straight to the monolith, entirely unaffected by the new service's health.

## 6. Walkthrough

1. **Level 1** — `MonolithOnly.main` sends three paths through a single `Monolith.handle` method. This is the pre-strangling system: one deployable unit answering everything, which is the normal starting state before any decomposition work begins.
2. **Level 2** — `Facade.route` is introduced as the single entry point clients now call. Its logic is a simple `if`: paths starting with `/orders/` go to the newly built `OrderService`; everything else still goes to `Monolith.handle`, byte-for-byte the same as before. Running it against the same three paths shows `/orders/1` now answered by the new service while the other two are unchanged — this is the strangler fig pattern's central move: migrate one path prefix, verify it in production, and repeat for the next prefix later, without ever touching the paths still owned by the monolith.
3. **Level 3 — fallback under failure** — `FlakyOrderService.handle` is written to throw for `/orders/2`, simulating a new service that isn't fully trustworthy yet (a realistic mid-migration state). `Facade.route` now wraps the call to `orderService.handle` in a try/catch: on success, the new service's answer is returned and printed directly; on failure, a fallback message is printed and the *same request* is re-routed to `Monolith.handle` instead of the whole call failing.
4. **Tracing the three calls** — `/orders/1` hits the try branch, succeeds, and returns the new service's answer. `/orders/2` hits the try branch, throws, is caught, prints the `[fallback triggered: ...]` line, and then falls through to `monolith.handle("/orders/2")` — so the *same request path* is served correctly by the *old* system even though it matched the "migrated" route rule. `/customers/9` never enters the try branch at all, since it doesn't match the `/orders/` prefix, and goes straight to the monolith exactly as in Level 2.
5. **Why this matters operationally** — this fallback is what makes the strangler fig pattern low-risk in practice: a route can be "migrated" (present in the facade's routing rule) while still silently protected by the old, proven code path whenever the new service has a bad day. Once the new service has earned enough production trust, the fallback (and eventually the whole monolith code path for that route) can be removed — the vine has fully replaced that branch of the tree.

## 7. Gotchas & takeaways

> **Gotcha:** teams sometimes treat the strangler fig facade as a permanent piece of architecture rather than a temporary migration tool. Left in place indefinitely, the facade itself becomes a new piece of infrastructure to maintain forever, and the monolith it was meant to eventually retire never actually gets removed. Track migrated routes and revisit the monolith's remaining footprint on a schedule.

- The routing facade is the mechanism: it decides per-request whether traffic goes to a new microservice or the old monolith, and that mapping shifts over time.
- Migrate and verify one route (or feature) at a time in production — this is what avoids the all-or-nothing risk of a big-bang rewrite.
- A fallback from new service to old monolith, during the transition period, lets a not-yet-fully-trusted new service fail safely without breaking the whole system.
- Related to [branch by abstraction](0065-branch-by-abstraction.md), which applies a similar incremental-replacement idea at the code level rather than the request-routing level.
- The goal state is the monolith fully retired — the facade and any fallback paths should be actively removed once every route is confidently migrated, not left running forever "just in case."
