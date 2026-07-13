---
card: microservices
gi: 299
slug: spring-cloud-gateway-resilience-filters
title: "Spring Cloud Gateway resilience filters"
---

## 1. What it is

Spring Cloud Gateway, the API gateway sitting in front of a microservices fleet, provides built-in `GatewayFilter` implementations for several resilience patterns — a `CircuitBreaker` filter (backed by Resilience4j), a `Retry` filter, and a `RequestRateLimiter` filter (commonly backed by Redis) — applied declaratively per route, in `application.yml` or via the Java route-builder API, rather than requiring each downstream service to implement its own protection independently.

## 2. Why & when

Applying resilience patterns at the gateway, rather than only inside each individual downstream service, has a distinct advantage: it protects the *whole system* from a client's perspective at a single, central point, and it can shield downstream services from problematic traffic before that traffic ever reaches them — a misbehaving client hammering a route can be rate-limited at the gateway without every individual service needing its own client-aware rate limiting logic. It also gives operators one place to look and one place to configure baseline protections uniformly across many routes.

This complements, rather than replaces, resilience patterns implemented inside each service — the gateway protects the edge and the aggregate; per-service circuit breakers and bulkheads (see [Resilience4j integration](0294-resilience4j-integration-circuit-breaker-retry-bulkhead-rate.md)) protect that service's own specific calls to its own dependencies. Use gateway-level filters for cross-cutting concerns applied uniformly to routes (rate limiting per client, a circuit breaker around an entire downstream service, retrying idempotent GET routes) and service-level Resilience4j for the finer-grained protection of specific internal dependency calls a service makes.

## 3. Core concept

Filters are configured per route; the `CircuitBreaker` filter names a Resilience4j circuit breaker instance and a fallback URI, the `Retry` filter configures attempts and status codes to retry on.

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: inventory-route
          uri: lb://inventory-service
          predicates:
            - Path=/api/inventory/**
          filters:
            - name: CircuitBreaker
              args:
                name: inventoryCB
                fallbackUri: forward:/fallback/inventory
            - name: Retry
              args:
                retries: 3
                statuses: BAD_GATEWAY,SERVICE_UNAVAILABLE
                methods: GET
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 10
                redis-rate-limiter.burstCapacity: 20
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client request enters the gateway and passes through a chain of resilience filters attached to the matching route -- rate limiter, retry, circuit breaker -- before being forwarded to the actual downstream service, protecting the service from problematic or excessive traffic before it ever arrives">
  <rect x="20" y="60" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">client</text>

  <line x1="120" y1="80" x2="200" y2="80" stroke="#8b949e" marker-end="url(#arr299)"/>
  <rect x="210" y="30" width="330" height="100" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="375" y="48" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Gateway route filter chain</text>

  <rect x="225" y="60" width="90" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="270" y="82" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">RateLimiter</text>
  <rect x="325" y="60" width="90" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="370" y="82" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Retry</text>
  <rect x="425" y="60" width="90" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="470" y="82" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">CircuitBreaker</text>

  <line x1="540" y1="80" x2="600" y2="80" stroke="#8b949e" marker-end="url(#arr299)"/>
  <text x="600" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">downstream</text>
  <text x="600" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">service</text>

  <defs><marker id="arr299" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Requests pass through the route's filter chain, each filter contributing its own protection, before reaching the downstream service.

## 5. Runnable example

Scenario: a plain proxying gateway route with no protection that forwards every request straight to a failing service, extended to add a hand-rolled stand-in for the gateway's `CircuitBreaker` filter with a fallback route, and finally composing rate limiting, retry, and circuit breaking together per request, mirroring the full filter chain a real Spring Cloud Gateway route applies.

### Level 1 — Basic

```java
// File: PlainProxyNoProtection.java -- a "gateway" that forwards every
// request directly to the downstream service with no filters at all.
public class PlainProxyNoProtection {
    static int downstreamCallCount = 0;
    static String callDownstream(String path) {
        downstreamCallCount++;
        throw new RuntimeException("502 Bad Gateway: inventory-service unreachable");
    }

    static String routeRequest(String path) {
        return callDownstream(path); // NO protection of any kind
    }

    public static void main(String[] args) {
        for (int i = 1; i <= 5; i++) {
            try { System.out.println("Request " + i + ": " + routeRequest("/api/inventory/sku-123")); }
            catch (Exception e) { System.out.println("Request " + i + ": FAILED -- " + e.getMessage()); }
        }
        System.out.println("Downstream calls made: " + downstreamCallCount + " (every request hit the broken service directly)");
    }
}
```

How to run: `java PlainProxyNoProtection.java`

Every one of the 5 requests is forwarded straight through to the failing downstream service and fails with a raw 502-style error — the gateway adds no value beyond simple proxying, and the already-struggling downstream service receives full, unmitigated load from every client request.

### Level 2 — Intermediate

```java
// File: CircuitBreakerFilterWithFallback.java -- a hand-rolled stand-in
// for Spring Cloud Gateway's CircuitBreaker filter (the real
// configuration is the 'name'/'fallbackUri' args on a route's
// CircuitBreaker filter, backed by Resilience4j): once the breaker
// trips, requests are routed to a fallback response instead of the
// downstream service.
public class CircuitBreakerFilterWithFallback {
    enum State { CLOSED, OPEN }
    static State circuitState = State.CLOSED;
    static int consecutiveFailures = 0;
    static final int threshold = 2;
    static int downstreamCallCount = 0;

    static String callDownstream(String path) {
        downstreamCallCount++;
        throw new RuntimeException("502 Bad Gateway");
    }

    static String fallbackResponse(String path) {
        return "200 OK (fallback): cached inventory data for " + path;
    }

    static String routeRequestWithCircuitBreaker(String path) {
        if (circuitState == State.OPEN) return fallbackResponse(path); // gateway-level FALLBACK route
        try {
            String result = callDownstream(path);
            consecutiveFailures = 0;
            return result;
        } catch (Exception e) {
            consecutiveFailures++;
            if (consecutiveFailures >= threshold) circuitState = State.OPEN;
            return fallbackResponse(path); // gateway routes to fallback on failure TOO, not just when already open
        }
    }

    public static void main(String[] args) {
        for (int i = 1; i <= 5; i++) {
            System.out.println("Request " + i + ": " + routeRequestWithCircuitBreaker("/api/inventory/sku-123"));
        }
        System.out.println("Downstream calls actually made: " + downstreamCallCount + " out of 5 requests");
    }
}
```

How to run: `java CircuitBreakerFilterWithFallback.java`

Every request now routes through `routeRequestWithCircuitBreaker`. Requests 1 and 2 still attempt the downstream call (which fails both times, tripping the breaker after the 2nd failure), but the gateway routes both of them to `fallbackResponse` rather than surfacing a raw 502 to the client. Requests 3-5 find the circuit already open and skip the downstream attempt entirely, going straight to the fallback. `downstreamCallCount` stays at 2 instead of 5 — the downstream service is protected from 3 of the 5 requests, and every client request still gets a `200 OK`, exactly matching what a real gateway route's `CircuitBreaker` filter configured with a `fallbackUri` provides.

### Level 3 — Advanced

```java
// File: FullGatewayFilterChain.java -- composes rate limiting, retry,
// and circuit breaking together per request, mirroring a real gateway
// route's full filter chain (RequestRateLimiter -> Retry -> CircuitBreaker
// -> downstream), each filter contributing independently.
public class FullGatewayFilterChain {
    // RequestRateLimiter stand-in: simple per-window counter (real gateway uses a Redis-backed token bucket).
    static int requestsThisWindow = 0;
    static final int rateLimit = 3;

    enum State { CLOSED, OPEN }
    static State circuitState = State.CLOSED;
    static int consecutiveFailures = 0;
    static final int threshold = 2;
    static int downstreamCallCount = 0;

    static String callDownstream(String path) {
        downstreamCallCount++;
        throw new RuntimeException("502 Bad Gateway");
    }

    static String callDownstreamWithRetry(String path, int maxRetries) {
        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            try { return callDownstream(path); }
            catch (Exception e) { if (attempt == maxRetries) throw e; }
        }
        throw new IllegalStateException("unreachable");
    }

    static String routeRequest(String path) {
        // FILTER 1: RequestRateLimiter -- runs FIRST, cheapest check.
        requestsThisWindow++;
        if (requestsThisWindow > rateLimit) return "429 Too Many Requests (rate limiter filter)";

        // FILTER 2 + 3: CircuitBreaker wraps Retry (per recommended composition).
        if (circuitState == State.OPEN) return "200 OK (circuit breaker fallback, cached data)";
        try {
            String result = callDownstreamWithRetry(path, 2);
            consecutiveFailures = 0;
            return result;
        } catch (Exception e) {
            consecutiveFailures++;
            if (consecutiveFailures >= threshold) circuitState = State.OPEN;
            return "200 OK (circuit breaker fallback, cached data)";
        }
    }

    public static void main(String[] args) {
        for (int i = 1; i <= 6; i++) {
            System.out.println("Request " + i + ": " + routeRequest("/api/inventory/sku-123"));
        }
        System.out.println("Downstream calls actually made: " + downstreamCallCount + " (across 6 client requests, each with up to 2 retries)");
    }
}
```

How to run: `java FullGatewayFilterChain.java`

Six client requests hit `routeRequest`, which applies the full filter chain in order. Request 1 passes the rate limiter (1 <= 3), then its retry-wrapped downstream call fails both attempts (2 real calls), tripping `consecutiveFailures` to 1. Request 2 similarly passes the rate limiter, retries twice more (2 more real calls, total 4), tripping the breaker open. Request 3 passes the rate limiter but finds the circuit already open, going straight to the cached fallback with zero downstream calls. Request 4, the 4th request this window, fails the *rate limiter* check outright (`requestsThisWindow=4 > rateLimit=3`), never even reaching the circuit-breaker logic — a 429 response. Requests 5 and 6 are also rate-limited. This demonstrates the layered protection a real gateway route provides: even before the circuit breaker's own protection kicks in, the rate limiter independently caps how many requests can even attempt to reach the downstream service in a given window.

## 6. Walkthrough

Trace `FullGatewayFilterChain.main`'s first four requests in order. **Request 1**: `routeRequest` increments `requestsThisWindow` to 1; `1 > 3` is false, so the rate-limiter filter passes. `circuitState` is `CLOSED`, so it proceeds to `callDownstreamWithRetry(path, 2)`, which internally attempts `callDownstream` twice (both fail, `downstreamCallCount` reaches 2), then re-throws after exhausting its 2 retries. Back in `routeRequest`, this is caught: `consecutiveFailures` becomes 1 (below threshold 2), and the method returns the cached fallback string.

**Request 2**: `requestsThisWindow` becomes 2, still `<= 3`, rate limiter passes. Circuit still `CLOSED`. `callDownstreamWithRetry` runs its 2 attempts again — `downstreamCallCount` reaches 4 — and fails again. `consecutiveFailures` becomes 2, meeting the threshold, so `circuitState` flips to `OPEN`. The method still returns the fallback string (the caller sees the same graceful response either way).

**Request 3**: `requestsThisWindow` becomes 3, still `<= 3`, rate limiter passes. But now `circuitState == State.OPEN` is checked *first* among the remaining logic, so `routeRequest` returns the fallback string immediately — `callDownstreamWithRetry` is never invoked, and `downstreamCallCount` stays at 4.

**Request 4**: `requestsThisWindow` becomes 4. The check `4 > 3` is now true — the rate-limiter filter itself rejects this request with `"429 Too Many Requests"`, before the circuit-breaker check or any downstream logic is even reached. This is a distinctly different failure mode from requests 1-3: it's the *gateway's own local rate accounting* that stops this request, entirely independent of the downstream service's health.

**Data flow across the filter chain layers**: each request enters at the rate-limiter layer (a pure in-memory counter check) → if it passes, proceeds to the circuit-breaker layer (checks shared, request-independent breaker state) → if the breaker is closed, proceeds to the retry layer (attempts the real call up to 2 times) → the retry layer's final outcome (success or exhausted failure) flows back up to update the circuit-breaker layer's failure count → and the final response (real data, cached fallback, or a 429) flows back to the client.

```
request -> requestsThisWindow++ > limit? --yes--> 429 (rate limiter filter, no further layers reached)
                    |no
                    v
           circuit OPEN? --yes--> fallback (no downstream call)
                    |no
                    v
           retry-wrapped downstream call --> success: real data
                                         \-> exhausted: fallback + failure count++
```

## 7. Gotchas & takeaways

> Gateway-level rate limiting and circuit breaking protect the downstream service from the aggregate of *all* client traffic through that route, but they do not replace per-dependency resilience inside each service — a service still needs its own protection for calls it makes to *its own* downstream dependencies that the gateway never sees.

- Applying resilience filters at the gateway centralizes cross-cutting protection (rate limiting, circuit breaking, retry) for entire routes, rather than requiring every individual downstream service to reimplement the same logic.
- Order matters in the filter chain just as it does for programmatic Resilience4j composition — a cheap rate-limiter check placed before an expensive downstream call (with retries) avoids wasting retry attempts on traffic that was always going to be rejected, echoing the [fail-fast pattern](0286-fail-fast-pattern.md).
- The `RequestRateLimiter` filter's default Redis-backed implementation makes it inherently a form of [distributed rate limiting](0278-distributed-rate-limiting-redis-backed.md), correctly enforcing a shared limit across multiple gateway instances.
- A `CircuitBreaker` filter's `fallbackUri` typically points to another route within the same gateway (e.g., `forward:/fallback/inventory`), which can itself apply further logic (like serving cached data) rather than just returning a static error message.
