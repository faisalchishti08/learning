---
card: system-design
gi: 215
slug: api-gateway-bff-composition
title: API gateway & BFF composition
---

## 1. What it is

An **API gateway** is a single entry point that sits in front of a system's [microservices](0196-microservices.md), applying cross-cutting concerns — authentication, rate limiting, routing, request logging — uniformly for every client and every service. When combined with [backend-for-frontend (BFF)](0199-backend-for-frontend-bff.md) services behind it, the gateway becomes the shared outer layer, while each BFF handles client-specific aggregation and response shaping.

## 2. Why & when

Without a gateway, every client calls every microservice directly, and every microservice must independently implement authentication, rate limiting, and logging — the same concerns duplicated across every service. An API gateway centralizes these concerns once, so individual services can focus purely on their own business logic and trust that the gateway already validated the request.

Layering BFFs behind the gateway solves a different, complementary problem: the gateway's cross-cutting concerns are the same for every client, but the *response shape* each client needs is not (see [backend-for-frontend](0199-backend-for-frontend-bff.md)). Use a plain gateway (no BFFs) when all your clients need roughly the same data shapes. Add BFFs behind the gateway once you have meaningfully different clients — the gateway still handles auth and rate limiting for all of them uniformly, while each BFF aggregates and shapes data for its one client type.

## 3. Core concept

- **Gateway responsibilities (apply to every request, every client).** Authentication/authorization (validate the token once, so downstream services do not each re-implement it), rate limiting (per API key or per user), routing (which service handles this path), and often request/response logging and metrics for observability.
- **BFF responsibilities (specific to one client).** Aggregating multiple backend calls into one response, and reshaping that response for one client's exact needs — concerns the gateway deliberately does NOT handle, because they differ per client.
- **Layering order matters.** The gateway sits in front of the BFFs, not behind them — every request hits the gateway first (auth, rate limit), and only requests that pass those checks reach the appropriate BFF, which then calls the underlying services.
- **Gateway routes to the right BFF, not directly to services.** The gateway's routing table maps `mobile.api.example.com/*` (or a header/path indicating client type) to the mobile BFF, and `web.api.example.com/*` to the web BFF — the gateway does not need to know what each BFF does internally, only where to send the request.
- **Avoid duplicating logic between the layers.** Auth and rate limiting belong at the gateway, once. Aggregation and response shaping belong at the BFF, once, per client. Putting business logic in the gateway (or auth logic in a BFF) blurs the boundary and creates the same duplication problem this layered structure exists to prevent.

## 4. Diagram

```
   Mobile App              Web App
       |                       |
       v                       v
   +----------------------------------+
   |            API Gateway             |
   |  - authenticate every request      |
   |  - rate limit per client            |
   |  - route to the correct BFF          |
   +------------------+-----------------+
                       |
        +---------------+----------------+
        v                                 v
   +-------------+                 +---------------+
   |  Mobile BFF  |                 |   Web BFF      |
   | (aggregates, |                 | (aggregates,    |
   |  small shape)|                 |  rich shape)     |
   +------+-------+                 +-------+---------+
          |                                  |
          +----------------+-----------------+
                            |
             calls the SAME underlying microservices
                            |
        +--------------------+----------------------+
        v                    v                       v
   OrdersService       UserService          RecommendationService
```
*Caption: every request passes through the gateway exactly once for cross-cutting checks, then is routed to the BFF that shapes the response for that specific client.*

## 5. Runnable example

**Level 1 — Basic.** A gateway that authenticates and rate-limits a request before it reaches any backend logic.

**Level 2 — Intermediate.** The gateway routes an authenticated, allowed request to the correct BFF based on client type.

**Level 3 — Advanced.** A request that fails at the gateway (bad auth, or rate-limited) never reaches a BFF at all — showing the layering enforced in code, and the BFF still doing its own aggregation once a request does arrive.

```java
// GatewayBffCompositionDemo.java
import java.util.*;

public class GatewayBffCompositionDemo {

    // ---------- Backend services, shared by every BFF ----------
    static String getOrderSummary(String userId) { return "order ORD-501 ($89.99, SHIPPED)"; }
    static String getUserProfile(String userId) { return "Priya Shah"; }

    // ---------- BFFs: client-specific aggregation, no auth/rate-limit logic here ----------
    static String mobileBff(String userId) {
        return "{ name: \"" + getUserProfile(userId) + "\", order: \"" + getOrderSummary(userId) + "\" }";
    }
    static String webBff(String userId) {
        return "{ user: { name: \"" + getUserProfile(userId) + "\" }, order: { summary: \"" +
            getOrderSummary(userId) + "\" }, extraDetailForWeb: true }";
    }

    // ---------- Level 1 & 2: the gateway - auth, rate limiting, routing ----------
    static class Gateway {
        Set<String> validTokens = Set.of("token-mobile-abc", "token-web-xyz");
        Map<String, Integer> remainingByToken = new HashMap<>();
        int limitPerToken = 2;

        String handle(String token, String clientType, String userId) {
            // Step 1: authenticate - applies to EVERY request, regardless of client type.
            if (!validTokens.contains(token)) {
                return "401 Unauthorized - invalid token, request never reaches a BFF";
            }
            // Step 2: rate limit - applies to EVERY request, regardless of client type.
            int remaining = remainingByToken.getOrDefault(token, limitPerToken);
            if (remaining <= 0) {
                return "429 Too Many Requests - request never reaches a BFF";
            }
            remainingByToken.put(token, remaining - 1);

            // Step 3: route to the correct BFF - ONLY reached if auth and rate limit both passed.
            if (clientType.equals("mobile")) return "200 OK (via Mobile BFF): " + mobileBff(userId);
            if (clientType.equals("web")) return "200 OK (via Web BFF): " + webBff(userId);
            return "404 Not Found - unknown client type";
        }
    }

    public static void main(String[] args) {
        Gateway gateway = new Gateway();

        System.out.println("Level 1 - auth and rate limiting happen BEFORE any BFF logic runs:");
        System.out.println("  bad token: " + gateway.handle("token-fake", "mobile", "U-1"));

        System.out.println("\nLevel 2 - valid token routes to the correct BFF:");
        System.out.println("  mobile client: " + gateway.handle("token-mobile-abc", "mobile", "U-1"));
        System.out.println("  web client:    " + gateway.handle("token-web-xyz", "web", "U-1"));

        System.out.println("\nLevel 3 - rate limit exhausted: further requests never reach a BFF at all:");
        System.out.println("  mobile request 2 (uses remaining budget): " +
            gateway.handle("token-mobile-abc", "mobile", "U-1"));
        System.out.println("  mobile request 3 (budget exhausted): " +
            gateway.handle("token-mobile-abc", "mobile", "U-1"));
    }
}
```

**How to run:** `java GatewayBffCompositionDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `gateway.handle("token-fake", "mobile", "U-1")` is called first. Step 1 inside `handle` checks `validTokens.contains(token)`, finds `"token-fake"` is not a recognized token, and returns `"401 Unauthorized"` immediately — neither `mobileBff` nor any backend service method is ever called. The request never got past the gateway's first check.
2. **Level 2:** `gateway.handle("token-mobile-abc", "mobile", "U-1")` passes both the auth check and the rate-limit check (this is the first request on this token, so `remaining` starts at `limitPerToken = 2`). Only then does `handle` reach step 3 and call `mobileBff(userId)`, which itself calls `getUserProfile` and `getOrderSummary` to build its small, client-specific response shape.
3. `gateway.handle("token-web-xyz", "web", "U-1")` goes through the same auth and rate-limit steps with a *different* valid token, and is routed to `webBff` instead, which calls the **same** two backend methods but builds a richer response shape — this mirrors exactly the aggregation-with-different-shaping behavior from [backend-for-frontend](0199-backend-for-frontend-bff.md), now sitting behind a shared gateway.
4. **Level 3:** the mobile token's second call (`"mobile request 2"`) succeeds — `remainingByToken` for `"token-mobile-abc"` was `1` after the first successful call in Level 2, so this call passes with `remaining = 1` before being decremented to `0`.
5. **The third call on the same token** finds `remaining <= 0` at step 2 and returns `"429 Too Many Requests"` — again, before step 3's routing logic ever runs, so `mobileBff` is not called a third time. This is the layering enforced directly in the code: `handle`'s three steps run strictly in order, and any failure at an earlier step short-circuits everything after it, including all BFF and backend-service logic.

## 7. Gotchas & takeaways

> **Gotcha:** putting business logic (like response aggregation) inside the gateway itself, "just this once for convenience," breaks the layering this pattern is built on — the gateway becomes a second place business logic can change, and every new client type now needs a change to the shared gateway instead of just adding a new BFF behind it.

- Keep the gateway's responsibilities limited to concerns that are genuinely the same for every client: authentication, rate limiting, routing, and observability.
- Keep aggregation and response shaping in the BFF layer, one BFF per client type, exactly as described in [backend-for-frontend](0199-backend-for-frontend-bff.md).
- Order matters: auth and rate-limit checks must run before any BFF or backend logic, so a rejected request costs as little server work as possible.
- This two-layer structure (shared gateway, per-client BFFs) is a common production shape for a [microservices](0196-microservices.md) system serving several different client types — treat it as the default starting point once you have more than one client and more than a couple of cross-cutting concerns to enforce.
