---
card: microservices
gi: 163
slug: cross-cutting-concerns-at-the-gateway-auth-logging-metrics
title: "Cross-cutting concerns at the gateway (auth, logging, metrics)"
---

## 1. What it is

Cross-cutting concerns at the gateway are the specific set of [edge service responsibilities](0158-edge-service-responsibilities.md) implemented as a chain of filters (or interceptors) that every request passes through in a defined order — typically authentication, then structured logging, then metrics collection — each filter handling one concern and passing the request to the next, with the final backend call only happening once every filter in the chain has allowed the request through.

## 2. Why & when

Authentication, logging, and metrics collection are needed on essentially every request, and implementing them as an ordered chain of independent, composable filters — rather than one large, tangled block of conditional logic — lets each concern be developed, tested, and reasoned about in isolation, and lets the chain's composition itself (which filters run, and in what order) be configured or reordered without touching any individual filter's implementation. This filter-chain structure is the concrete mechanism most real gateways (Spring Cloud Gateway, nginx with Lua modules, Envoy) use to implement the "cross-cutting concerns belong at the edge" principle in practice.

Structure gateway cross-cutting logic as an ordered filter chain whenever more than one such concern needs to run per request — which is nearly always true in practice, since authentication, logging, and metrics are close to universal requirements. Keep each filter narrowly scoped to exactly one concern; a filter that starts handling multiple unrelated responsibilities loses the composability and independent testability that motivated the filter-chain structure in the first place.

## 3. Core concept

Each filter receives the request, does its own work, and either short-circuits the chain (rejecting the request outright) or calls the next filter in sequence; the chain's order determines which concerns run before which — authentication typically runs first, so unauthenticated requests never reach logging or metrics filters meant only for legitimate traffic.

```java
// a FILTER CHAIN: each filter does ONE thing, then calls next.handle(request) to continue
Filter authFilter = (request, next) -> {
    if (!isAuthenticated(request)) return unauthorized(); // SHORT-CIRCUITS -- chain stops here
    return next.handle(request);
};
Filter loggingFilter = (request, next) -> {
    log(request); // runs ONLY for authenticated requests
    return next.handle(request);
};
Filter metricsFilter = (request, next) -> {
    long start = System.nanoTime();
    Response response = next.handle(request);
    recordLatency(System.nanoTime() - start);
    return response;
};
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request flows through an ordered filter chain: authentication first, then logging, then metrics, then finally the backend call; an unauthenticated request is rejected by the auth filter before reaching any later filter" >
  <rect x="20" y="60" width="100" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Request</text>

  <rect x="160" y="60" width="100" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="210" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Auth filter</text>

  <rect x="300" y="60" width="100" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Logging</text>

  <rect x="440" y="60" width="100" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Metrics</text>

  <rect x="440" y="130" width="100" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="490" y="152" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Backend</text>

  <line x1="120" y1="82" x2="158" y2="82" stroke="#8b949e" marker-end="url(#arr44)"/>
  <line x1="260" y1="82" x2="298" y2="82" stroke="#8b949e" marker-end="url(#arr44)"/>
  <line x1="400" y1="82" x2="438" y2="82" stroke="#8b949e" marker-end="url(#arr44)"/>
  <line x1="490" y1="105" x2="490" y2="128" stroke="#8b949e" marker-end="url(#arr44)"/>

  <defs>
    <marker id="arr44" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each filter runs in order and hands off to the next; a rejection anywhere short-circuits everything after it.

## 5. Runnable example

Scenario: an order-gateway that starts with all cross-cutting logic tangled into one monolithic method (showing the maintainability problem), refactors it into a composable ordered filter chain with auth, logging, and metrics as separate filters, and finally demonstrates reordering the chain and adding a fourth filter without modifying any existing filter's code.

### Level 1 — Basic

```java
// File: MonolithicHandling.java -- auth, logging, and metrics ALL tangled into
// ONE method; hard to test, reorder, or extend independently.
public class MonolithicHandling {
    record Request(String authToken, String path) {}

    static String handle(Request request) {
        // auth, logging, AND metrics all mixed together, in a fixed, hard-coded order
        if (request.authToken() == null) return "401 Unauthorized";
        System.out.println("[log] " + request.path());
        long start = System.nanoTime();
        String result = "backend response for " + request.path();
        System.out.println("[metrics] latency: " + (System.nanoTime() - start) + "ns");
        return result;
    }

    public static void main(String[] args) {
        System.out.println(handle(new Request("valid-token", "/orders/42")));
        System.out.println("Reordering auth/logging/metrics, or adding a FOURTH concern, means editing this ONE tangled method.");
    }
}
```

**How to run:** `javac MonolithicHandling.java && java MonolithicHandling` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ComposableFilterChain.java -- auth, logging, and metrics as SEPARATE,
// independently defined filters, composed into an ordered chain.
import java.util.*;
import java.util.function.*;

public class ComposableFilterChain {
    record Request(String authToken, String path) {}
    interface Handler { String handle(Request request); }
    interface Filter { String apply(Request request, Handler next); }

    static Filter authFilter = (request, next) -> {
        if (request.authToken() == null) { System.out.println("[auth filter] REJECTED -- no token"); return "401 Unauthorized"; }
        System.out.println("[auth filter] passed");
        return next.handle(request);
    };
    static Filter loggingFilter = (request, next) -> {
        System.out.println("[logging filter] " + request.path());
        return next.handle(request);
    };
    static Filter metricsFilter = (request, next) -> {
        long start = System.nanoTime();
        String result = next.handle(request);
        System.out.println("[metrics filter] latency: " + (System.nanoTime() - start) + "ns");
        return result;
    };

    static Handler buildChain(List<Filter> filters, Handler finalHandler) {
        Handler chain = finalHandler;
        for (int i = filters.size() - 1; i >= 0; i--) { // wrap from the END backward, so filters.get(0) runs FIRST
            Filter filter = filters.get(i);
            Handler next = chain;
            chain = request -> filter.apply(request, next);
        }
        return chain;
    }

    public static void main(String[] args) {
        Handler backendCall = request -> "backend response for " + request.path();
        Handler pipeline = buildChain(List.of(authFilter, loggingFilter, metricsFilter), backendCall);

        System.out.println(pipeline.handle(new Request("valid-token", "/orders/42")));
        System.out.println("Each filter is a SEPARATE, independently testable unit of code.");
    }
}
```

**How to run:** `javac ComposableFilterChain.java && java ComposableFilterChain` (JDK 17+).

Expected output:
```
[auth filter] passed
[logging filter] /orders/42
[metrics filter] latency: ...ns
backend response for /orders/42
Each filter is a SEPARATE, independently testable unit of code.
```

### Level 3 — Advanced

```java
// File: ReorderedChainWithNewFilter.java -- REORDER the existing filters AND add
// a FOURTH, new filter -- with ZERO changes to any of the three original filter implementations.
import java.util.*;

public class ReorderedChainWithNewFilter {
    record Request(String authToken, String path, String clientId) {}
    interface Handler { String handle(Request request); }
    interface Filter { String apply(Request request, Handler next); }

    // the THREE original filters, UNCHANGED from Level 2
    static Filter authFilter = (request, next) -> {
        if (request.authToken() == null) { System.out.println("[auth] REJECTED"); return "401 Unauthorized"; }
        System.out.println("[auth] passed");
        return next.handle(request);
    };
    static Filter loggingFilter = (request, next) -> {
        System.out.println("[logging] " + request.path());
        return next.handle(request);
    };
    static Filter metricsFilter = (request, next) -> {
        long start = System.nanoTime();
        String result = next.handle(request);
        System.out.println("[metrics] latency: " + (System.nanoTime() - start) + "ns");
        return result;
    };

    // a NEW, FOURTH filter -- rate limiting, added WITHOUT touching the other three
    static Map<String, Integer> requestCounts = new HashMap<>();
    static Filter rateLimitFilter = (request, next) -> {
        int count = requestCounts.merge(request.clientId(), 1, Integer::sum);
        if (count > 2) { System.out.println("[rate-limit] REJECTED -- too many requests from " + request.clientId()); return "429 Too Many Requests"; }
        System.out.println("[rate-limit] passed (" + count + "/2)");
        return next.handle(request);
    };

    static Handler buildChain(List<Filter> filters, Handler finalHandler) {
        Handler chain = finalHandler;
        for (int i = filters.size() - 1; i >= 0; i--) {
            Filter filter = filters.get(i);
            Handler next = chain;
            chain = request -> filter.apply(request, next);
        }
        return chain;
    }

    public static void main(String[] args) {
        Handler backendCall = request -> "backend response for " + request.path();

        // rate-limit now runs FIRST (before even auth), and metrics wraps the WHOLE chain --
        // a REORDERED, EXTENDED pipeline, assembled purely by changing the buildChain() call's LIST
        Handler pipeline = buildChain(List.of(metricsFilter, rateLimitFilter, authFilter, loggingFilter), backendCall);

        Request req = new Request("valid-token", "/orders/42", "client-A");
        System.out.println(pipeline.handle(req));
        System.out.println(pipeline.handle(req));
        System.out.println(pipeline.handle(req)); // THIRD request from client-A -- exceeds the rate limit
    }
}
```

**How to run:** `javac ReorderedChainWithNewFilter.java && java ReorderedChainWithNewFilter` (JDK 17+).

Expected output (latency values vary):
```
[rate-limit] passed (1/2)
[auth] passed
[logging] /orders/42
[metrics] latency: ...ns
backend response for /orders/42
[rate-limit] passed (2/2)
[auth] passed
[logging] /orders/42
[metrics] latency: ...ns
backend response for /orders/42
[rate-limit] REJECTED -- too many requests from client-A
429 Too Many Requests
```

## 6. Walkthrough

1. **Level 1** — `handle` performs the auth check, the log statement, and the timing measurement all inline, in a fixed sequence baked directly into the method body; changing the order or adding a new concern means editing this single method's internals directly.
2. **Level 2, filters as independent functions** — `authFilter`, `loggingFilter`, and `metricsFilter` are each defined as a `Filter` (a function taking a request and a `next` handler); none of them know about, or depend on, the existence of the others.
3. **Level 2, assembling the chain** — `buildChain` wraps filters from the last one in the list backward to the first, so that calling the resulting `chain.handle(request)` runs `filters.get(0)` first, and each filter's call to `next.handle(request)` invokes the next filter in the originally-specified order.
4. **Level 2, tracing one request through the chain** — `pipeline.handle(request)` first enters `authFilter`, which (given a non-null token) calls `next.handle(request)`, entering `loggingFilter`, which calls its own `next.handle(request)`, entering `metricsFilter`, which calls the final `backendCall` and then measures the elapsed time around that call before returning.
5. **Level 3, adding a new filter without touching old ones** — `rateLimitFilter` is defined as a completely new `Filter` implementation, tracking per-client request counts in `requestCounts`; none of `authFilter`, `loggingFilter`, or `metricsFilter`'s source code changed at all to accommodate it.
6. **Level 3, reordering purely via the list argument** — `buildChain(List.of(metricsFilter, rateLimitFilter, authFilter, loggingFilter), backendCall)` places `metricsFilter` first (so it now times the *entire* remaining chain, including auth and rate-limit checks) and `rateLimitFilter` second (so it runs before authentication, rejecting excessive request volume even from unauthenticated clients) — this entire restructuring was accomplished by changing only the order of items in one list, not by editing any filter's implementation.
7. **Level 3, the rate limit triggering on the third request** — the first two calls to `pipeline.handle(req)` both pass the rate-limit filter's `count > 2` check (reaching counts of 1 and 2), but the third call pushes `count` to 3, triggering the rejection branch and returning `"429 Too Many Requests"` without ever reaching `authFilter`, `loggingFilter`, or the backend call — demonstrating a fully reordered, extended pipeline built entirely through composition, with every original filter's implementation left completely untouched.

## 7. Gotchas & takeaways

> **Gotcha:** filter order is not merely a stylistic choice — placing `metricsFilter` (which measures latency) outside `authFilter` versus inside it produces genuinely different measurements: one includes the auth check's own latency in every recorded metric, the other doesn't, and getting this backward silently skews performance data in a way that's easy to miss until someone tries to reconcile gateway-reported latency against backend-reported latency and finds a persistent, unexplained gap.

- Structuring gateway cross-cutting concerns as an ordered chain of independent, single-purpose filters keeps each concern separately testable and lets the chain's composition (order, membership) be changed without modifying any individual filter's implementation.
- Filters commonly short-circuit the chain (returning a rejection) rather than calling `next`, which is how earlier filters like authentication can prevent a request from ever reaching later filters or the backend.
- Chain order has real, observable consequences — which filters run before which determines both correctness (unauthenticated requests reaching logging/metrics meant only for legitimate traffic) and the precise scope of what each filter measures or protects.
- Adding a new cross-cutting concern (like rate limiting) should be possible by adding one new filter and adjusting the chain's composition, without touching any existing filter's code — that composability is the entire point of the pattern.
- Real gateways (Spring Cloud Gateway, Envoy, nginx with modules) implement this exact filter-chain structure natively, making it directly applicable, not just a simplified teaching model.
