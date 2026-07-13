---
card: microservices
gi: 158
slug: edge-service-responsibilities
title: "Edge service responsibilities"
---

## 1. What it is

Edge service responsibilities are the set of concerns that belong at the boundary between external clients and an internal microservices system — routing, authentication, TLS termination, rate limiting, request logging, and response transformation — kept deliberately separate from business logic, which stays inside individual backend services. "The edge" is the architectural layer, and the [API gateway](0157-api-gateway-pattern.md) is typically the concrete component that implements it.

## 2. Why & when

If every backend service implements its own authentication check, its own rate limiting, its own TLS handling, and its own request logging format, that cross-cutting logic gets duplicated across every service, drifts out of sync as each copy evolves independently, and pollutes each service's codebase with concerns unrelated to its actual business responsibility. Centralizing these concerns at the edge means each backend service can trust that requests reaching it have already been authenticated, rate-limited, and logged consistently — the service's own code stays focused purely on its business logic, and the cross-cutting policies live and evolve in exactly one place.

Push a concern to the edge when it applies uniformly across most or all backend services and doesn't require business-specific knowledge to enforce — authentication, TLS termination, basic rate limiting, and access logging are the classic cases. Keep a concern inside a specific backend service when it requires that service's own business context to make the right decision — a rate limit specifically tied to a customer's subscription tier, for instance, needs data the edge typically doesn't have.

## 3. Core concept

Cross-cutting request handling happens once, at the edge, before a request ever reaches business logic; the backend service's own code can assume every request arriving at it has already passed through this shared layer.

```java
// at the EDGE, once, for every request regardless of which backend it's headed to
if (!authenticate(request)) return unauthorized();
if (rateLimiter.exceeded(request.clientId())) return tooManyRequests();
logAccess(request);
Response response = forwardToBackend(request);
logResponse(response);

// INSIDE the backend service -- pure business logic, no auth/rate-limit/logging code at all
Order processOrder(OrderRequest request) { return orderService.place(request); }
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request passes through the edge layer's authentication, rate limiting, and logging checks before reaching a backend service, which contains only pure business logic with no duplicated cross-cutting code">
  <rect x="20" y="20" width="280" height="90" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="40" fill="#8b949e" font-size="8" font-family="sans-serif">EDGE (cross-cutting, once)</text>
  <text x="45" y="62" fill="#e6edf3" font-size="8" font-family="sans-serif">auth -&gt; rate limit -&gt; log -&gt; TLS</text>

  <rect x="360" y="45" width="180" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="450" y="70" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">order-service</text>
  <text x="450" y="140" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">pure business logic, no duplicated concerns</text>

  <line x1="300" y1="65" x2="358" y2="65" stroke="#8b949e" marker-end="url(#arr39)"/>

  <defs>
    <marker id="arr39" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Cross-cutting checks happen once, at the edge; the backend service sees only requests that have already passed them.

## 5. Runnable example

Scenario: two backend services that start by each duplicating their own authentication and logging logic (showing the drift risk), refactor those concerns into a shared edge layer sitting in front of both, and finally demonstrate updating the shared policy once at the edge and seeing that change apply consistently to every backend without touching either service's code.

### Level 1 — Basic

```java
// File: DuplicatedCrossCuttingLogic.java -- EACH service implements its OWN
// authentication and logging, independently -- a recipe for drift.
import java.util.*;

public class DuplicatedCrossCuttingLogic {
    record Request(String clientToken, String path) {}

    static class OrderService {
        boolean authenticate(Request r) { return r.clientToken().startsWith("valid-"); } // service-specific copy #1
        void logAccess(Request r) { System.out.println("[order-service log] " + r.path()); } // copy #1
        String handle(Request r) {
            if (!authenticate(r)) return "401 Unauthorized";
            logAccess(r);
            return "order data";
        }
    }
    static class CustomerService {
        boolean authenticate(Request r) { return r.clientToken() != null && r.clientToken().length() > 5; } // SUBTLY DIFFERENT copy #2 -- already drifted!
        void logAccess(Request r) { System.out.println("[customer-service LOG] path=" + r.path()); } // different FORMAT, copy #2
        String handle(Request r) {
            if (!authenticate(r)) return "401 Unauthorized";
            logAccess(r);
            return "customer data";
        }
    }

    public static void main(String[] args) {
        Request req = new Request("valid-token-123", "/orders/42");
        System.out.println(new OrderService().handle(req));
        System.out.println(new CustomerService().handle(req));
        System.out.println("Two DIFFERENT authentication rules and TWO different log formats, already inconsistent after just 2 services.");
    }
}
```

**How to run:** `javac DuplicatedCrossCuttingLogic.java && java DuplicatedCrossCuttingLogic` (JDK 17+).

### Level 2 — Intermediate

```java
// File: SharedEdgeLayer.java -- authentication and logging live ONCE, at the edge;
// both backend services contain ONLY business logic.
import java.util.*;
import java.util.function.*;

public class SharedEdgeLayer {
    record Request(String clientToken, String path) {}

    // ONE shared edge layer -- the ONLY place auth and logging rules live
    static class EdgeLayer {
        boolean authenticate(Request r) { return r.clientToken() != null && r.clientToken().startsWith("valid-"); }
        void logAccess(Request r) { System.out.println("[edge access log] path=" + r.path()); }

        String handleRequest(Request r, Function<Request, String> backendHandler) {
            if (!authenticate(r)) return "401 Unauthorized";
            logAccess(r);
            return backendHandler.apply(r); // ONLY reached after auth + logging succeed
        }
    }

    // backend services: PURE business logic, no auth or logging code anywhere
    static String orderServiceLogic(Request r) { return "order data for " + r.path(); }
    static String customerServiceLogic(Request r) { return "customer data for " + r.path(); }

    public static void main(String[] args) {
        EdgeLayer edge = new EdgeLayer();
        Request req = new Request("valid-token-123", "/orders/42");

        System.out.println(edge.handleRequest(req, SharedEdgeLayer::orderServiceLogic));
        System.out.println(edge.handleRequest(req, SharedEdgeLayer::customerServiceLogic));
        System.out.println("ONE consistent auth rule, ONE consistent log format, applied uniformly to BOTH backends.");
    }
}
```

**How to run:** `javac SharedEdgeLayer.java && java SharedEdgeLayer` (JDK 17+).

Expected output:
```
[edge access log] path=/orders/42
order data for /orders/42
[edge access log] path=/orders/42
customer data for /orders/42
ONE consistent auth rule, ONE consistent log format, applied uniformly to BOTH backends.
```

### Level 3 — Advanced

```java
// File: PolicyChangeAppliesEverywhere.java -- updating the auth policy ONCE, at
// the edge, applies to EVERY backend automatically -- no per-service changes needed.
import java.util.*;
import java.util.function.*;

public class PolicyChangeAppliesEverywhere {
    record Request(String clientToken, String path) {}

    static class EdgeLayer {
        Predicate<Request> authPolicy; // the auth RULE is now pluggable, changeable in ONE place
        EdgeLayer(Predicate<Request> authPolicy) { this.authPolicy = authPolicy; }

        void logAccess(Request r) { System.out.println("[edge access log] path=" + r.path()); }

        String handleRequest(Request r, Function<Request, String> backendHandler) {
            if (!authPolicy.test(r)) return "401 Unauthorized";
            logAccess(r);
            return backendHandler.apply(r);
        }
    }

    static String orderServiceLogic(Request r) { return "order data for " + r.path(); }
    static String customerServiceLogic(Request r) { return "customer data for " + r.path(); }
    static String paymentServiceLogic(Request r) { return "payment data for " + r.path(); }

    public static void main(String[] args) {
        // OLD policy: any token starting with "valid-"
        EdgeLayer edgeV1 = new EdgeLayer(r -> r.clientToken() != null && r.clientToken().startsWith("valid-"));
        Request oldStyleToken = new Request("valid-token-123", "/orders/42");

        System.out.println("=== BEFORE policy change ===");
        System.out.println(edgeV1.handleRequest(oldStyleToken, PolicyChangeAppliesEverywhere::orderServiceLogic));
        System.out.println(edgeV1.handleRequest(oldStyleToken, PolicyChangeAppliesEverywhere::customerServiceLogic));
        System.out.println(edgeV1.handleRequest(oldStyleToken, PolicyChangeAppliesEverywhere::paymentServiceLogic));

        // POLICY UPGRADE: tokens must now also carry a minimum length AND a new prefix --
        // changed in EXACTLY ONE place, the edge's authPolicy
        EdgeLayer edgeV2 = new EdgeLayer(r -> r.clientToken() != null && r.clientToken().startsWith("bearer-") && r.clientToken().length() > 15);
        Request newStyleToken = new Request("bearer-abcdef123456", "/orders/42");
        Request staleOldToken = new Request("valid-token-123", "/orders/42"); // the OLD token format, now correctly rejected everywhere

        System.out.println("\n=== AFTER policy change (edge updated ONCE) ===");
        System.out.println(edgeV2.handleRequest(newStyleToken, PolicyChangeAppliesEverywhere::orderServiceLogic));
        System.out.println(edgeV2.handleRequest(newStyleToken, PolicyChangeAppliesEverywhere::customerServiceLogic));
        System.out.println(edgeV2.handleRequest(newStyleToken, PolicyChangeAppliesEverywhere::paymentServiceLogic));
        System.out.println(edgeV2.handleRequest(staleOldToken, PolicyChangeAppliesEverywhere::orderServiceLogic) + " (old token format correctly rejected, everywhere, automatically)");
    }
}
```

**How to run:** `javac PolicyChangeAppliesEverywhere.java && java PolicyChangeAppliesEverywhere` (JDK 17+).

Expected output:
```
=== BEFORE policy change ===
[edge access log] path=/orders/42
order data for /orders/42
[edge access log] path=/orders/42
customer data for /orders/42
[edge access log] path=/orders/42
payment data for /orders/42

=== AFTER policy change (edge updated ONCE) ===
[edge access log] path=/orders/42
order data for /orders/42
[edge access log] path=/orders/42
customer data for /orders/42
[edge access log] path=/orders/42
payment data for /orders/42
401 Unauthorized (old token format correctly rejected, everywhere, automatically)
```

## 6. Walkthrough

1. **Level 1** — `OrderService.authenticate` and `CustomerService.authenticate` implement two *subtly different* rules (`startsWith("valid-")` versus a bare length check), and their `logAccess` methods produce two differently-formatted log lines — this divergence happened with only two services, illustrating how quickly duplicated cross-cutting logic drifts.
2. **Level 2, one shared implementation** — `EdgeLayer.authenticate` and `EdgeLayer.logAccess` are each defined exactly once; `handleRequest` calls them before invoking whichever `backendHandler` function was passed in, meaning every backend's requests pass through the identical checks.
3. **Level 2, backend services reduced to pure logic** — `orderServiceLogic` and `customerServiceLogic` contain nothing but their respective business responses, with no authentication or logging code anywhere in either — that responsibility has moved entirely to `EdgeLayer`.
4. **Level 2, the consistency achieved** — both calls to `edge.handleRequest` in `main` produce identically-formatted log lines and apply the identical authentication rule, directly resolving the Level 1 drift.
5. **Level 3, making the policy itself pluggable** — `EdgeLayer`'s constructor now accepts a `Predicate<Request> authPolicy`, so the specific authentication rule is data passed into the edge layer rather than logic hard-coded inside it.
6. **Level 3, the policy upgrade** — `edgeV2` is constructed with a stricter predicate requiring a `"bearer-"` prefix and a minimum token length; this is the *only* code change made anywhere in this example to implement the new policy.
7. **Level 3, the change applying uniformly and automatically** — all three backend calls under `edgeV2` (`orderServiceLogic`, `customerServiceLogic`, `paymentServiceLogic`) are governed by the identical new policy without any of those three functions being touched, and `staleOldToken` (valid under the old policy) is correctly rejected against all of them — demonstrating that a single edge-level policy change propagates its effect to every backend service simultaneously, which is precisely the operational leverage centralizing cross-cutting concerns at the edge provides over duplicating that logic per service.

## 7. Gotchas & takeaways

> **Gotcha:** not every cross-cutting-seeming concern actually belongs at the edge — a rate limit that needs to vary based on a customer's specific subscription tier, or an authorization check that depends on fine-grained, resource-specific business rules (can this specific user modify this specific order?), typically needs business context the edge doesn't have, and pushing it there either forces the edge to fetch business data it shouldn't own, or produces an incorrect, oversimplified policy.

- Edge service responsibilities are the cross-cutting concerns (authentication, TLS termination, rate limiting, logging) that belong at the system's external boundary, kept separate from business logic inside individual backend services.
- Centralizing these concerns at the edge prevents the duplication and inevitable drift that results from every backend service implementing its own copy.
- Backend services benefit from being able to assume incoming requests have already passed edge-level checks, keeping their own code focused purely on business logic.
- A concern belongs at the edge when it applies uniformly and doesn't require business-specific context; a concern belongs inside a specific service when it genuinely needs that service's own business knowledge to enforce correctly.
- Updating a policy at the edge propagates that change to every backend service simultaneously, without touching any individual service's code — a direct, measurable benefit of this separation.
