---
card: system-design
gi: 42
slug: spring-cloud-gateway-as-the-edge-gateway
title: Spring Cloud Gateway as the edge gateway
---

## 1. What it is

**Spring Cloud Gateway** is Spring's framework for building an API gateway (the edge-of-system component covered earlier in this section), configured declaratively as a set of **routes**, each matching incoming requests by criteria like path or header, and applying a chain of **filters** (for auth, rate limiting, header rewriting, and more) before forwarding to the right backend service.

## 2. Why & when

Building a custom API gateway by hand means implementing routing, filtering, and forwarding logic yourself. Spring Cloud Gateway gives you this out of the box, built on Spring's reactive, non-blocking foundation (Spring WebFlux), so it can handle a high volume of concurrent connections efficiently — a good fit for a component that, being the single edge entry point, sees every request to your entire system.

## 3. Core concept

**Routes and predicates:** a route defines *what* traffic it matches (a **predicate**, such as a path pattern) and *where* it sends matching traffic (the destination **URI**, often the address of a downstream service or, in a Spring Cloud setup, a logical service name resolved via service discovery).

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service-route
          uri: lb://user-service        # lb:// resolves via service discovery + client-side load balancing
          predicates:
            - Path=/users/**
        - id: order-service-route
          uri: lb://order-service
          predicates:
            - Path=/orders/**
```

**Filters:** each route can apply a chain of filters that run before the request is forwarded (and often after the response comes back). Built-in filters cover common cross-cutting concerns: `AddRequestHeader`, `RequestRateLimiter` (rate limiting, often backed by Redis), and `CircuitBreaker` (covered elsewhere as a resilience pattern). You can also write custom filters for logic specific to your system, like custom auth token validation.

**How this fits the request flow:** a request enters Spring Cloud Gateway, is matched against the configured predicates to select a route, passes through that route's filter chain (auth, rate limiting, header modification), and is then forwarded to the resolved backend service — mirroring the general API gateway role described earlier, now expressed as concrete Spring configuration.

## 4. Diagram

```
 Client --GET /users/42-------------------------->|
                                              Spring Cloud Gateway
                                                     |
                                       match predicate: Path=/users/**
                                                     |
                                       run filter chain: auth -> rate-limit
                                                     |
                                       forward to uri: lb://user-service
                                                     |
                                                     v
                                            User Service instance
                                       (chosen by client-side load balancer)
```
*Caption: the gateway matches a request to a route by predicate, runs its filter chain, then forwards to the resolved backend.*

## 5. Runnable example

### Artifact: a minimal Java sketch modeling Spring Cloud Gateway's route-matching and filter-chain behavior

```java
import java.util.*;
import java.util.function.*;

public class GatewayRouteSim {

    record Route(String id, String pathPredicate, String destination, List<Predicate<String>> filters) {}

    static boolean matchesPath(String pattern, String actualPath) {
        String prefix = pattern.replace("/**", "");
        return actualPath.startsWith(prefix);
    }

    static Optional<Route> findMatchingRoute(List<Route> routes, String path) {
        return routes.stream().filter(r -> matchesPath(r.pathPredicate(), path)).findFirst();
    }

    public static void main(String[] args) {
        Predicate<String> authFilter = path -> {
            System.out.println("  filter: auth check passed for " + path);
            return true;
        };
        Predicate<String> rateLimitFilter = path -> {
            System.out.println("  filter: rate limit check passed for " + path);
            return true;
        };

        List<Route> routes = List.of(
            new Route("user-service-route", "/users/**", "lb://user-service", List.of(authFilter, rateLimitFilter)),
            new Route("order-service-route", "/orders/**", "lb://order-service", List.of(authFilter, rateLimitFilter))
        );

        String incomingPath = "/users/42";
        System.out.println("Incoming request: GET " + incomingPath);

        Route matched = findMatchingRoute(routes, incomingPath)
            .orElseThrow(() -> new RuntimeException("404: no route matched"));
        System.out.println("Matched route: " + matched.id());

        boolean allFiltersPassed = matched.filters().stream().allMatch(f -> f.test(incomingPath));
        if (allFiltersPassed) {
            System.out.println("Forwarding to: " + matched.destination());
        }
    }
}
```

**How to run:** save as `GatewayRouteSim.java`, run `java GatewayRouteSim.java` (JDK 17+). A real Spring Cloud Gateway app needs the `spring-cloud-starter-gateway` dependency, with routes typically declared in `application.yml` as shown above, rather than in Java code.

## 6. Walkthrough

1. `Route` models one configured route: the path predicate it matches, its forwarding destination, and its ordered list of filters — matching the shape of a real Spring Cloud Gateway route definition.
2. `matchesPath` performs the same kind of prefix match a real `Path=/users/**` predicate performs, checking whether the incoming request's path falls under the route's configured pattern.
3. `findMatchingRoute` scans the configured routes and returns the first one whose predicate matches, mirroring how the gateway selects exactly one route per incoming request.
4. `main` sends a simulated `GET /users/42` request through this pipeline: it finds the matching route, runs each of that route's filters in order (auth, then rate limiting), and only forwards to the destination if every filter passes.
5. Output:
```
Incoming request: GET /users/42
Matched route: user-service-route
  filter: auth check passed for /users/42
  filter: rate limit check passed for /users/42
Forwarding to: lb://user-service
```
6. This traces the exact sequence a real Spring Cloud Gateway performs internally: predicate matching selects one route, its filter chain runs in order, and only a request that passes every filter is actually forwarded — any filter returning false would stop the request there, before reaching the backend.

## 7. Gotchas & takeaways

> **Gotcha:** ordering filters incorrectly, such as putting a filter that logs request details *before* the auth filter that would have rejected an unauthenticated request. Filter order matters — cheap, rejecting checks (like auth) should generally run before more expensive or side-effecting filters.

- Spring Cloud Gateway matches requests to routes using predicates (commonly path-based), then runs each route's filter chain before forwarding.
- The `lb://` URI scheme integrates with service discovery and client-side load balancing, so the gateway does not need a hardcoded backend address.
- Built on Spring WebFlux's non-blocking foundation, making it well suited to sit at the edge handling every incoming request to your system.
