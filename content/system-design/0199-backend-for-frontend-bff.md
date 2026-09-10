---
card: system-design
gi: 199
slug: backend-for-frontend-bff
title: Backend-for-frontend (BFF)
---

## 1. What it is

A **backend-for-frontend (BFF)** is a thin backend service built for one specific client — a mobile app, a web app, a smart-TV app — that sits between that client and the underlying [microservices](0196-microservices.md). It aggregates and reshapes data from multiple services into exactly the response shape that one client needs.

## 2. Why & when

Different clients have very different needs from the same backend. A mobile app wants a small, flattened response to save bandwidth and battery; a web dashboard wants a rich, deeply nested response with everything on one screen. If every microservice tries to satisfy every client directly, its API balloons with client-specific fields and optional parameters, and a change for one client risks breaking another.

A BFF fixes this by giving each client its own dedicated aggregation layer. The mobile BFF calls the same underlying services as the web BFF, but shapes the response differently, and each BFF evolves independently as its own client's needs change. Use a BFF when you have genuinely different clients with different data and performance needs calling the same set of backend services — not for a single web app with no other client, where a plain [API gateway](0197-service-oriented-architecture-soa.md) or direct calls are enough.

## 3. Core concept

- **One BFF per client type**, not one BFF for all clients. A mobile BFF and a web BFF are separate deployable services, each owned (ideally) by the team that owns that client.
- **Aggregation.** A BFF calls several backend services in one request-handling cycle and combines their results into one response, so the client makes one network call instead of many.
- **Client-specific shaping.** The same underlying data can come back different sizes and shapes from different BFFs — a mobile BFF drops fields the mobile UI never shows; a web BFF includes them.
- **No business logic duplication.** A BFF should not reimplement business rules that belong in the underlying services (e.g. pricing logic) — it only aggregates and reshapes. If a rule is duplicated across BFFs, it will eventually drift out of sync.
- **Distinct from a general API gateway.** A single shared API gateway routes and applies cross-cutting concerns (auth, rate limiting) for all clients uniformly. A BFF is deliberately client-specific and does real response shaping, not just routing.

## 4. Diagram

```
   Mobile App                          Web App
       |                                   |
       v                                   v
 +--------------+                   +----------------+
 | Mobile BFF   |                   |  Web BFF        |
 | (small,      |                   |  (rich, nested   |
 |  flattened   |                   |   response)      |
 |  response)   |                   |                  |
 +------+-------+                   +--------+---------+
        |                                    |
        +-----------------+------------------+
                           |
             calls the SAME underlying services
                           |
        +------------------+-------------------+
        |                  |                    |
        v                  v                    v
   OrdersService     UserService         RecommendationService
```
*Caption: both BFFs call the same three backend services, but each shapes the combined response for its own client — mobile gets less data, web gets more.*

## 5. Runnable example

**Level 1 — Basic.** One BFF aggregates two backend calls into a single response.

**Level 2 — Intermediate.** Two BFFs (mobile and web) call the same three backend services but return different response shapes from the same underlying data.

**Level 3 — Advanced.** A BFF calls backend services in parallel (simulated) and handles one of them failing without failing the whole aggregated response — a common real-world BFF concern.

```java
// BffDemo.java
import java.util.*;
import java.util.concurrent.*;

public class BffDemo {

    // ---------- Backend services (shared by every BFF) ----------
    record Order(String id, double amount, String status) {}
    record User(String id, String name, String email) {}
    record Recommendation(String productName) {}

    static class OrdersService {
        Order getLatestOrder(String userId) { return new Order("ORD-501", 89.99, "SHIPPED"); }
    }
    static class UserService {
        User getUser(String userId) { return new User(userId, "Priya Shah", "priya@example.com"); }
    }
    static class RecommendationService {
        List<Recommendation> getRecommendations(String userId) {
            return List.of(new Recommendation("Wireless mouse"), new Recommendation("Laptop stand"));
        }
        List<Recommendation> getRecommendationsFailing(String userId) {
            throw new RuntimeException("recommendation-service timeout");
        }
    }

    // ---------- Level 1: one BFF, basic aggregation ----------
    static String basicBff(OrdersService orders, UserService users, String userId) {
        Order order = orders.getLatestOrder(userId);
        User user = users.getUser(userId);
        return String.format("{ user: \"%s\", latestOrder: \"%s ($%.2f)\" }",
            user.name(), order.id(), order.amount());
    }

    // ---------- Level 2: two client-specific BFFs, same backend calls ----------
    static String mobileBff(OrdersService orders, UserService users, RecommendationService recs, String userId) {
        Order order = orders.getLatestOrder(userId);
        User user = users.getUser(userId);
        // Mobile: small, flattened - no email, no full recommendation list.
        return String.format("{ name: \"%s\", orderStatus: \"%s\" }", user.name(), order.status());
    }

    static String webBff(OrdersService orders, UserService users, RecommendationService recs, String userId) {
        Order order = orders.getLatestOrder(userId);
        User user = users.getUser(userId);
        List<Recommendation> recommendations = recs.getRecommendations(userId);
        // Web: rich, nested - includes email and full recommendation list.
        StringBuilder recNames = new StringBuilder();
        for (Recommendation r : recommendations) recNames.append(r.productName()).append(", ");
        return String.format(
            "{ user: { name: \"%s\", email: \"%s\" }, order: { id: \"%s\", amount: %.2f, status: \"%s\" }, recommendations: [%s] }",
            user.name(), user.email(), order.id(), order.amount(), order.status(), recNames.toString().trim());
    }

    // ---------- Level 3: parallel calls, one backend fails, BFF degrades gracefully ----------
    static String resilientBff(OrdersService orders, UserService users, RecommendationService recs, String userId)
            throws InterruptedException, ExecutionException {
        ExecutorService pool = Executors.newFixedThreadPool(3);
        Future<Order> orderFuture = pool.submit(() -> orders.getLatestOrder(userId));
        Future<User> userFuture = pool.submit(() -> users.getUser(userId));
        Future<List<Recommendation>> recFuture = pool.submit(() -> recs.getRecommendationsFailing(userId));

        Order order = orderFuture.get();
        User user = userFuture.get();
        String recSection;
        try {
            List<Recommendation> recommendations = recFuture.get();
            recSection = recommendations.toString();
        } catch (ExecutionException e) {
            recSection = "[] (recommendations unavailable: " + e.getCause().getMessage() + ")";
        }
        pool.shutdown();
        return String.format("{ name: \"%s\", order: \"%s\", recommendations: %s }",
            user.name(), order.id(), recSection);
    }

    public static void main(String[] args) throws Exception {
        OrdersService orders = new OrdersService();
        UserService users = new UserService();
        RecommendationService recs = new RecommendationService();

        System.out.println("Level 1 - basic aggregation:");
        System.out.println("  " + basicBff(orders, users, "U-1"));

        System.out.println("\nLevel 2 - two client-specific shapes from the same backend calls:");
        System.out.println("  mobile: " + mobileBff(orders, users, recs, "U-1"));
        System.out.println("  web:    " + webBff(orders, users, recs, "U-1"));

        System.out.println("\nLevel 3 - one backend call fails, BFF still responds:");
        System.out.println("  " + resilientBff(orders, users, recs, "U-1"));
    }
}
```

**How to run:** `java BffDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `basicBff` calls `orders.getLatestOrder(...)` and `users.getUser(...)` — two backend calls — and combines both results into one JSON-shaped string. The caller of the BFF made one call and got everything it needed.
2. **Level 2:** `mobileBff` and `webBff` both call the same three backend services (`orders`, `users`, `recs`), but `mobileBff` only reads `user.name()` and `order.status()`, ignoring email and recommendations entirely, while `webBff` includes every field, including the full recommendation list. The underlying data is identical — the shaping differs per client.
3. **Level 3:** `resilientBff` submits all three backend calls to a thread pool so they run concurrently rather than one after another — this models the real-world practice of parallelizing independent backend calls inside a BFF to keep response time low.
4. `orderFuture.get()` and `userFuture.get()` both succeed normally. `recFuture.get()` throws an `ExecutionException`, because `getRecommendationsFailing` always throws — this simulates the recommendation service being down or timing out.
5. The `catch` block does not let that one failure crash the whole response. It substitutes a fallback string noting the recommendations are unavailable, and the method still returns a complete, valid response with the order and user data intact — exactly the graceful-degradation behavior a real BFF needs when one of several backend dependencies is unhealthy.

## 7. Gotchas & takeaways

> **Gotcha:** letting business logic creep into a BFF — for example, computing a discounted price inside the mobile BFF instead of asking the pricing service for it — creates duplicate logic that silently drifts out of sync between the mobile and web BFFs. Keep BFFs to aggregation and shaping only.

- One BFF per client type, not one BFF shared across very different clients — sharing defeats the purpose.
- A BFF should own no data of its own; it is a read-and-reshape layer over services that do own data.
- Parallelize independent backend calls inside a BFF, and handle partial failure explicitly — a BFF that fails entirely because one minor backend call failed is worse than the services it aggregates.
- If you only have one client (a single web app), you probably do not need a BFF yet — introduce it once a second, meaningfully different client shows up.
