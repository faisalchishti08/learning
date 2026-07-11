---
card: spring-cloud
gi: 40
slug: gateway-overview-reactive-netty
title: "Gateway overview (reactive, Netty)"
---

## 1. What it is

Spring Cloud Gateway is a single entry point that sits in front of a set of backend services, matching each incoming request against configured routes and forwarding it to the right backend — while also applying cross-cutting concerns like authentication, rate limiting, and request rewriting along the way. It's built on Spring WebFlux and runs on Netty, a non-blocking, event-loop-based server, rather than the traditional one-thread-per-request Servlet model.

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: orders-route
          uri: lb://orders-service
          predicates:
            - Path=/orders/**
```

## 2. Why & when

Without a gateway, every client (web app, mobile app, third party) needs to know the address of every individual backend service, and every service must independently implement its own authentication, rate limiting, and CORS handling. A gateway centralizes that: clients talk to one address, and the gateway decides where each request actually goes and what happens to it on the way, using service discovery (`lb://orders-service` resolves through Eureka/Consul/Zookeeper, covered in the previous section) instead of hardcoded backend addresses.

Reach for Spring Cloud Gateway when:

- Multiple backend services need a unified external-facing address, with routing decided by path, host, header, or other request attributes.
- Cross-cutting concerns — auth, rate limiting, retries, request/response rewriting — should live in one place instead of being duplicated across every backend service.
- The system is expected to handle many concurrent, mostly-I/O-bound connections (a classic gateway workload) where Netty's non-blocking event loop uses far fewer threads than a blocking one-thread-per-request model would need.

## 3. Core concept

```
 client request
     |
     v
 Spring Cloud Gateway (Netty, non-blocking event loop)
     |
     |-- match request against configured Routes (predicates decide "does this route apply?")
     |-- apply Filters (modify the request/response, add headers, rate-limit, etc.)
     |
     v
 forward to resolved backend (often via load-balanced service discovery: lb://service-name)
```

The gateway is a routing and filtering layer, not a backend itself — its whole job is deciding where a request goes and what happens to it in transit.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client request arrives at Spring Cloud Gateway, which matches it against a route and forwards it to the resolved backend service via service discovery">
  <rect x="30" y="80" width="120" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="105" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">client</text>

  <rect x="230" y="60" width="180" height="80" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring Cloud Gateway</text>
  <text x="320" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">(Netty, non-blocking)</text>
  <text x="320" y="114" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">match route -&gt; run filters</text>

  <rect x="490" y="30" width="130" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="555" y="51" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">orders-service</text>
  <rect x="490" y="136" width="130" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="555" y="157" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billing-service</text>

  <line x1="150" y1="100" x2="228" y2="100" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a40)"/>
  <line x1="410" y1="85" x2="488" y2="50" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a40)"/>
  <line x1="410" y1="115" x2="488" y2="150" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a40)"/>

  <defs><marker id="a40" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One client-facing address fans out to the correct backend based on route matching inside the gateway.

## 5. Runnable example

The scenario: route incoming requests to the right backend by path. Start with a naive if/else router, then model it as Gateway's Route/Predicate structure, then add non-blocking, concurrent request handling to reflect the reactive/Netty execution model.

### Level 1 — Basic

A naive router: an if/else chain deciding where a request goes.

```java
public class GatewayOverviewLevel1 {
    static String route(String path) {
        if (path.startsWith("/orders/")) return "orders-service";
        if (path.startsWith("/billing/")) return "billing-service";
        return "404";
    }

    public static void main(String[] args) {
        System.out.println("/orders/42  -> " + route("/orders/42"));
        System.out.println("/billing/7  -> " + route("/billing/7"));
        System.out.println("/unknown/1  -> " + route("/unknown/1"));
    }
}
```

How to run: `java GatewayOverviewLevel1.java`

This is routing's bare essence — decide a destination from the request path — but it's hardcoded logic, not the declarative, composable Route/Predicate model Gateway actually uses.

### Level 2 — Intermediate

Model Gateway's real structure: a list of `Route` objects, each with a `Predicate` deciding whether it matches, evaluated in order until one matches.

```java
import java.util.*;
import java.util.function.Predicate;

public class GatewayOverviewLevel2 {
    record Route(String id, String uri, Predicate<String> predicate) {}

    static List<Route> routes = List.of(
            new Route("orders-route", "lb://orders-service", path -> path.startsWith("/orders/")),
            new Route("billing-route", "lb://billing-service", path -> path.startsWith("/billing/"))
    );

    static Optional<Route> matchRoute(String path) {
        return routes.stream().filter(r -> r.predicate().test(path)).findFirst();
    }

    public static void main(String[] args) {
        for (String path : List.of("/orders/42", "/billing/7", "/unknown/1")) {
            Optional<Route> matched = matchRoute(path);
            System.out.println(path + " -> " + matched.map(Route::uri).orElse("404 no route matched"));
        }
    }
}
```

How to run: `java GatewayOverviewLevel2.java`

Each `Route` pairs a target `uri` (a service-discovery-resolvable address, `lb://orders-service`) with a `Predicate<String>` deciding whether it applies — this is exactly Gateway's own model: routes are evaluated in order, and the first one whose predicate matches wins. Configuration (YAML, as shown in section 1) declares these routes instead of writing them in code.

### Level 3 — Advanced

Add non-blocking, concurrent handling of multiple in-flight requests using a single-threaded event loop simulation — reflecting why Netty can serve many concurrent connections without one thread per request.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Predicate;

public class GatewayOverviewLevel3 {
    record Route(String id, String uri, Predicate<String> predicate) {}

    static List<Route> routes = List.of(
            new Route("orders-route", "lb://orders-service", path -> path.startsWith("/orders/")),
            new Route("billing-route", "lb://billing-service", path -> path.startsWith("/billing/"))
    );

    static Optional<Route> matchRoute(String path) {
        return routes.stream().filter(r -> r.predicate().test(path)).findFirst();
    }

    // simulates a non-blocking backend call: returns a CompletableFuture instead of blocking the caller thread
    static CompletableFuture<String> forwardAsync(String path, ScheduledExecutorService eventLoop) {
        Optional<Route> matched = matchRoute(path);
        if (matched.isEmpty()) return CompletableFuture.completedFuture(path + " -> 404");
        CompletableFuture<String> future = new CompletableFuture<>();
        long simulatedLatencyMs = path.contains("42") ? 100 : 30; // different backends, different latency
        eventLoop.schedule(() -> future.complete(path + " -> " + matched.get().uri() + " (done)"),
                simulatedLatencyMs, TimeUnit.MILLISECONDS);
        return future;
    }

    public static void main(String[] args) throws Exception {
        // ONE thread models Netty's event loop -- it dispatches all requests without blocking on any of them
        ScheduledExecutorService eventLoop = Executors.newSingleThreadScheduledExecutor();

        List<String> incoming = List.of("/orders/42", "/billing/7", "/orders/1", "/billing/3");
        List<CompletableFuture<String>> inFlight = new ArrayList<>();
        for (String path : incoming) {
            inFlight.add(forwardAsync(path, eventLoop)); // dispatched immediately, none of these block
        }

        System.out.println("all " + inFlight.size() + " requests dispatched without blocking the event loop thread");
        CompletableFuture.allOf(inFlight.toArray(new CompletableFuture[0])).get();
        for (CompletableFuture<String> f : inFlight) System.out.println(f.get());

        eventLoop.shutdown();
    }
}
```

How to run: `java GatewayOverviewLevel3.java`

A single `ScheduledExecutorService` thread stands in for Netty's event loop: all four requests are dispatched to it immediately in the first loop, and none of them block that thread while "waiting" for their simulated backend latency — each schedules a callback and returns control right away, exactly like a real non-blocking I/O call registering a completion callback instead of parking a thread. The confirmation that all four are "dispatched without blocking" before any of them actually finishes is the point: one thread is handling many concurrent in-flight requests.

## 6. Walkthrough

Trace Level 3's execution.

1. `eventLoop`, a single-threaded scheduled executor, is created — this models Netty's event loop, which in a real Gateway deployment is typically a handful of threads (not thousands) handling potentially thousands of concurrent connections.
2. The first loop calls `forwardAsync` once per incoming path. Inside each call, `matchRoute` runs synchronously (fast, in-memory route matching), then a `CompletableFuture` is created and a callback is *scheduled* on the event loop rather than the method blocking until the backend responds — this models the real distinction: WebFlux/Netty registers a continuation and immediately frees the thread to handle the next request, instead of a Servlet thread sitting idle waiting on I/O.
3. Because none of the four `forwardAsync` calls block, all four are dispatched in rapid succession, and the `println` confirming "all 4 requests dispatched without blocking the event loop thread" runs before any backend call has actually "completed" — proof the thread was never stuck waiting on any single request.
4. `CompletableFuture.allOf(...).get()` blocks *this* test-driver thread (not the event loop) until all four scheduled callbacks have fired — in a real Gateway, nothing plays this blocking role; each request's response is written back to its own client connection as its own future completes.
5. The final loop prints each future's resolved value — `/orders/42` and `/orders/1` route to `orders-service`, `/billing/7` and `/billing/3` route to `billing-service`, each annotated `(done)` once its simulated backend latency elapsed and its callback fired on the shared event-loop thread.

```
event loop thread:  dispatch req1 -> dispatch req2 -> dispatch req3 -> dispatch req4
                          |              |               |               |
                    (no blocking -- each registers a callback and returns)
                          |              |               |               |
                     callback1        callback2       callback3       callback4
                    fires later      fires later     fires later     fires later
                    (as each backend call actually finishes, in any order)
```

## 7. Gotchas & takeaways

> **Gotcha:** because Gateway is WebFlux/Netty-based, any blocking code accidentally introduced into a custom filter (a synchronous JDBC call, `Thread.sleep`, a blocking HTTP client) stalls the shared event-loop thread for *every* in-flight request being processed by that thread, not just the one that triggered it — a single blocking call can silently degrade throughput for the whole gateway instance.

- Gateway's Netty/WebFlux foundation means it scales concurrent connections with a small, fixed thread pool, rather than needing one thread per in-flight request — well suited to a gateway's typically I/O-bound, high-concurrency workload.
- Routes are evaluated in order, and the first matching predicate wins — route ordering in configuration matters, especially when predicates could overlap.
- `lb://service-name` ties routing directly into service discovery (Eureka/Consul/Zookeeper from the previous section) — the gateway never needs a hardcoded backend address.
- Because everything is reactive, any custom logic added to Gateway (custom filters, custom predicates) must itself stay non-blocking, or it undermines the entire performance model the gateway is built on.
