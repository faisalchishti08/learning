---
card: system-design
gi: 35
slug: api-gateway-role-at-the-edge
title: API gateway role at the edge
---

## 1. What it is

An **API gateway** is a single entry point that sits at the **edge** of a system — the boundary between the outside world and your internal services — and handles cross-cutting concerns (authentication, rate limiting, routing) before forwarding requests to the appropriate internal microservice. It is a specialized reverse proxy: instead of just balancing load across identical servers, it understands your system's *different services* and routes intelligently between them.

## 2. Why & when

In a microservices architecture with many internal services, you do not want every client to know about, or directly call, dozens of individual internal service addresses, nor do you want to duplicate authentication and rate-limiting logic inside every single service. An API gateway centralizes these concerns in one place, at the edge, so internal services can stay focused purely on their own business logic. You introduce one as soon as a design has more than a couple of internal services that need a unified, secured, public-facing entry point.

## 3. Core concept

**What an API gateway typically handles, in one place, so individual services do not have to:**

- **Routing:** forwarding `/users/*` to the user service, `/orders/*` to the order service, and so on — content-aware routing, similar to L7 load balancing, but organized around distinct *services* rather than identical server replicas.
- **Authentication & authorization:** verifying a client's identity (e.g. validating a token) once, at the edge, rather than every internal service re-implementing that check.
- **Rate limiting:** enforcing how many requests a client can make in a given time window, protecting internal services from being overwhelmed by a single misbehaving or malicious client.
- **Request/response transformation:** adapting an external-facing API shape to whatever internal services actually expect, letting internal services evolve independently of the external contract.
- **Aggregation:** in some designs, combining results from multiple internal service calls into a single response for the client, reducing the number of round trips a client needs to make.

**How it differs from a plain load balancer:** a load balancer typically spreads traffic across *identical* replicas of the *same* service. An API gateway routes across *different* services, each doing something different, and adds policy logic (auth, rate limiting) beyond simple traffic distribution. In practice, many real systems use a load balancer in front of each individual service, and an API gateway one layer above that, routing between the different services.

## 4. Diagram

```
 Client
   |
   v
 API Gateway (edge)
   |-- auth check ---------------|
   |-- rate limit check ---------|
   |
   +--/users/*----------> User Service (behind its own load balancer)
   +--/orders/*---------> Order Service (behind its own load balancer)
   +--/payments/*-------> Payment Service (behind its own load balancer)

   (client only ever talks to the gateway; never calls a service directly)
```
*Caption: the gateway centralizes auth and rate limiting once, then routes each request to the correct internal service.*

## 5. Runnable example

### Artifact: a Java simulation of a minimal API gateway performing auth, rate limiting, and routing before reaching a service

```java
import java.util.*;

public class ApiGatewaySim {

    static final Map<String, Integer> requestCountThisWindow = new HashMap<>();
    static final int RATE_LIMIT_PER_CLIENT = 3;

    static boolean isAuthenticated(String token) {
        return token != null && token.startsWith("valid-");
    }

    static boolean isWithinRateLimit(String clientId) {
        int count = requestCountThisWindow.merge(clientId, 1, Integer::sum);
        return count <= RATE_LIMIT_PER_CLIENT;
    }

    static String routeToService(String path) {
        if (path.startsWith("/users")) return "User Service";
        if (path.startsWith("/orders")) return "Order Service";
        return "404 Not Found - no matching service";
    }

    static String handleRequest(String clientId, String token, String path) {
        if (!isAuthenticated(token)) {
            return "401 Unauthorized";
        }
        if (!isWithinRateLimit(clientId)) {
            return "429 Too Many Requests";
        }
        String service = routeToService(path);
        return "200 OK -> routed to " + service;
    }

    public static void main(String[] args) {
        System.out.println(handleRequest("clientA", "valid-token-xyz", "/users/42"));
        System.out.println(handleRequest("clientA", null, "/orders/1"));           // no token
        System.out.println(handleRequest("clientA", "valid-token-xyz", "/orders/1"));
        System.out.println(handleRequest("clientA", "valid-token-xyz", "/orders/2"));
        System.out.println(handleRequest("clientA", "valid-token-xyz", "/orders/3")); // 4th request, over limit
    }
}
```

**How to run:** save as `ApiGatewaySim.java`, run `java ApiGatewaySim.java` (JDK 17+).

## 6. Walkthrough

1. `isAuthenticated` performs the gateway's auth check, simplified to a token prefix check standing in for real token validation.
2. `isWithinRateLimit` tracks per-client request counts and rejects any request beyond the configured limit — this state lives centrally in the gateway, not duplicated in every service.
3. `routeToService` performs the gateway's routing decision, mapping a URL path prefix to the correct internal service name.
4. `handleRequest` runs these checks in order — auth first, then rate limit, then routing — mirroring a real gateway's request pipeline, where a request is rejected as early as possible if it fails any earlier check.
5. `main` sends five requests: a valid one, one with no token, two more valid ones, and a fifth that exceeds the rate limit of 3 requests for `clientA`.
6. Output:
```
200 OK -> routed to User Service
401 Unauthorized
200 OK -> routed to Order Service
200 OK -> routed to Order Service
429 Too Many Requests
```
7. Note the fifth request is rejected by the rate limiter *before* ever reaching `routeToService` — this is exactly the value of centralizing these checks at the edge: the internal Order Service never even sees the request that would have exceeded its client's quota.

## 7. Gotchas & takeaways

> **Gotcha:** letting the API gateway itself contain business logic beyond routing and cross-cutting concerns. If the gateway starts making decisions specific to one service's domain (like calculating an order's total price), it becomes a hidden coupling point that every service change must also touch — keep it strictly to routing, auth, rate limiting, and similar cross-cutting concerns.

- An API gateway centralizes auth, rate limiting, and routing at the edge, so individual services do not duplicate that logic.
- It differs from a plain load balancer by routing across *different* services, not just identical replicas of one service.
- Keep business logic out of the gateway; it should orchestrate access to services, not implement their domain logic.
