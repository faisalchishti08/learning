---
card: microservices
gi: 563
slug: putting-it-together-gateway-discovery-config-resiliency-trac
title: "Putting it together: Gateway + Discovery + Config + Resiliency + Tracing"
---

## 1. What it is

This topic is a capstone: assembling [Gateway](0543-spring-cloud-gateway-edge-routing.md), [Discovery](0542-spring-cloud-netflix-eureka.md)/[LoadBalancer](0544-spring-cloud-loadbalancer-client-side-lb.md), [Config](0541-spring-cloud-config-centralized-config.md), [Circuit Breaker](0545-spring-cloud-circuit-breaker-resiliency-abstraction.md), and [Tracing](0550-spring-cloud-sleuth-micrometer-tracing-tracing.md) into one coherent request path, rather than understanding each piece in isolation. A single incoming request in a real Spring Cloud system touches all five concerns in sequence: it arrives at the gateway, gets routed to a discovered instance, that instance reads its configuration, calls a downstream service through a circuit breaker, and every hop along the way is traced — seeing how these pieces compose is what turns individually-understood building blocks into an actual working system.

## 2. Why & when

You need to understand the full composition, not just each piece individually, because the pieces interact in ways that only become visible when assembled:

- **Each individual Spring Cloud module was discussed on its own, but a real request never touches just one of them** — a request entering the system passes through the gateway, gets discovered and load-balanced to a specific instance, that instance's behavior is shaped by centrally-managed configuration, its calls to further downstream services are protected by circuit breakers, and the entire journey is stitched together by tracing. Understanding each piece alone doesn't automatically reveal how they hand off to each other.
- **Failure and performance characteristics compound across this whole chain** — a slow response might originate from a stale discovery cache routing to an unhealthy instance, whose slow response then trips a circuit breaker at a different hop, all visible only by tracing the full path end to end, not by examining any single component's logs.
- **Configuration changes propagate through this whole system differently depending on where they land** — a Config Server update affecting a circuit breaker's timeout threshold, refreshed via `@RefreshScope`, changes behavior at the instance level; a gateway route change affects behavior at the edge; understanding which layer a given configuration change actually affects requires seeing the full picture.
- **You need this integrated view specifically when debugging a production issue that spans the whole request path**, or when designing a new service that needs to participate correctly in an existing system already using all five pieces together — reasoning about "why is this one request slow" or "where should this new service's resiliency configuration live" requires the composed mental model, not five separate ones.

## 3. Core concept

Think of a package's journey through a full logistics network: it arrives at a regional sorting facility (the gateway), gets routed to whichever specific delivery truck is currently available and healthy for that destination (discovery + load balancing), the truck driver follows route instructions that corporate updates centrally and pushes to every truck (centralized configuration), the driver has a backup plan if a specific delivery point is temporarily unreachable rather than getting stuck forever (circuit breaker), and a single tracking number follows the package through every single one of these steps, letting anyone reconstruct exactly what happened to this specific package from pickup to delivery (tracing). No single station in this network operates in isolation — the sorting facility's routing decision affects which truck gets the package, the truck's ability to work around a blocked delivery point affects overall delivery time, and the tracking number is what ties every step back into one coherent, followable story.

Concretely, tracing a request through the assembled system:

1. **The request arrives at [Spring Cloud Gateway](0543-spring-cloud-gateway-edge-routing.md)**, matching a route predicate, having filters applied, with [Micrometer Tracing](0550-spring-cloud-sleuth-micrometer-tracing-tracing.md) generating (or propagating) a trace ID at this entry point.
2. **The gateway's `lb://` destination is resolved via [Spring Cloud LoadBalancer](0544-spring-cloud-loadbalancer-client-side-lb.md)**, which queries the active [`DiscoveryClient`](0542-spring-cloud-netflix-eureka.md) for currently-healthy instances and selects one — the trace ID propagates in the outgoing request's headers.
3. **The selected instance receives the request.** Its behavior (a timeout value, a feature flag) is shaped by configuration fetched from [Spring Cloud Config](0541-spring-cloud-config-centralized-config.md) at startup, potentially refreshable via `@RefreshScope` without a redeploy. The trace ID is picked up from the incoming request and stamped into this instance's logs via MDC.
4. **If this instance needs to call a further downstream service**, that call is wrapped in a [circuit breaker](0545-spring-cloud-circuit-breaker-resiliency-abstraction.md) — protecting against that dependency's potential slowness or failure, with a fallback response if the circuit is open. The trace ID continues propagating to this next hop too.
5. **Throughout this entire chain, every hop's logs and generated spans share the same trace ID**, letting the full journey — gateway routing decision, discovered instance, configuration values in effect, circuit breaker state, downstream call outcome — be reconstructed as one coherent, end-to-end story.

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request flows through Gateway, Discovery/LoadBalancer, a service instance shaped by Config, a Circuit-Breaker-protected downstream call, all tied together by a shared trace ID">
  <rect x="20" y="20" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Gateway</text>
  <text x="90" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">route + trace-id gen</text>

  <rect x="200" y="20" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="270" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Discovery + LB</text>
  <text x="270" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">pick healthy instance</text>

  <rect x="380" y="20" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service instance</text>
  <text x="450" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">config-driven behavior</text>

  <rect x="560" y="20" width="80" height="50" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="600" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Downstream</text>
  <text x="600" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">circuit-breaker guarded</text>

  <line x1="160" y1="45" x2="200" y2="45" stroke="#8b949e" marker-end="url(#a18)"/>
  <line x1="340" y1="45" x2="380" y2="45" stroke="#8b949e" marker-end="url(#a18)"/>
  <line x1="520" y1="45" x2="560" y2="45" stroke="#8b949e" marker-end="url(#a18)"/>

  <rect x="20" y="110" width="620" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ONE trace ID ties every hop's logs/spans together, end to end</text>
  <defs><marker id="a18" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

Every hop plays a distinct role, but a shared trace ID is what ties the full journey into one reconstructable story.

## 5. Runnable example

Scenario: a checkout request flowing through all five concerns. We start with a plain Java model of the composed flow, extend it to show config-driven behavior variance, then trace the fully-assembled request path in detail.

### Level 1 — Basic

```java
// File: ComposedFlowBasic.java -- models the CORE composed sequence:
// gateway route -> discovered instance -> config-shaped processing ->
// circuit-breaker-guarded downstream call, all sharing ONE trace ID.
import java.util.*;

public class ComposedFlowBasic {
    static String traceId = "abc123"; // generated ONCE, at the gateway, propagated throughout

    static String gatewayRoute(String path) {
        System.out.println("[trace=" + traceId + "][Gateway] routing " + path + " to order-service");
        return discoverAndCallInstance();
    }

    static String discoverAndCallInstance() {
        String chosenInstance = "10.0.5.2:8080"; // resolved via discovery + load balancing
        System.out.println("[trace=" + traceId + "][Discovery+LB] chose instance " + chosenInstance);
        return serviceInstanceHandle();
    }

    static String serviceInstanceHandle() {
        int timeoutMs = 500; // sourced from centralized config
        System.out.println("[trace=" + traceId + "][OrderService] processing with configured timeout=" + timeoutMs + "ms");
        return circuitBreakerProtectedCall();
    }

    static String circuitBreakerProtectedCall() {
        System.out.println("[trace=" + traceId + "][CircuitBreaker] calling downstream pricing-service");
        return "{\"orderId\":\"42\",\"price\":\"$42.00\"}";
    }

    public static void main(String[] args) {
        System.out.println(gatewayRoute("/api/orders/42"));
    }
}
```

How to run: `java ComposedFlowBasic.java`

Every log line across all four stages carries the same `trace=abc123` prefix — this models exactly what a real assembled system produces: gateway routing, discovery/load-balancing selection, config-driven processing, and a circuit-breaker-guarded downstream call, all reconstructable as one coherent story purely by filtering for a shared trace ID.

### Level 2 — Intermediate

```java
// File: ConfigDrivenVariance.java -- shows how a CONFIG CHANGE (a
// refreshed timeout value) changes behavior at the INSTANCE level,
// without touching the gateway or discovery logic at all.
import java.util.*;

public class ConfigDrivenVariance {
    static Map<String, Integer> centralConfig = new HashMap<>(Map.of("pricing.timeout-ms", 500));

    static String processWithCurrentConfig(String traceId) {
        int timeoutMs = centralConfig.get("pricing.timeout-ms"); // re-read on every call, reflecting the CURRENT value
        System.out.println("[trace=" + traceId + "] processing with timeout=" + timeoutMs + "ms");
        return timeoutMs < 200 ? "FAST_FAIL_RISK" : "SAFE_MARGIN";
    }

    public static void main(String[] args) {
        System.out.println("Before config change: " + processWithCurrentConfig("trace-1"));

        centralConfig.put("pricing.timeout-ms", 100); // a refresh event updates the CENTRAL value
        System.out.println("After config change (via /actuator/refresh): " + processWithCurrentConfig("trace-2"));
    }
}
```

How to run: `java ConfigDrivenVariance.java`

`processWithCurrentConfig` re-reads `centralConfig` on every call, so updating the timeout value (simulating a Config Server change plus a refresh event) immediately changes the instance's behavior — this is exactly how a real `@RefreshScope` bean's `@Value`-bound field reacts to a centrally-managed configuration change without any redeploy, and it happens entirely independently of the gateway's routing logic or the discovery mechanism's instance selection, which remain unaffected by this specific change.

### Level 3 — Advanced

```java
// File: FullyAssembledFlow.java -- the FULL composed flow with a
// FAILURE scenario: the downstream pricing-service is slow, tripping
// the circuit breaker, with the trace ID reconstructing exactly WHERE
// the slowness originated.
import java.util.*;
import java.util.concurrent.*;

public class FullyAssembledFlow {
    static String traceId = "def456";
    static AtomicInteger pricingFailureCount = new AtomicInteger(0);
    static final int FAILURE_THRESHOLD = 3;
    static volatile boolean circuitOpen = false;

    static String gatewayRoute(String path) {
        log("Gateway", "routing " + path);
        return discoverAndCallInstance();
    }
    static String discoverAndCallInstance() {
        log("Discovery+LB", "chose instance 10.0.5.2:8080 (healthy per discovery)");
        return serviceInstanceHandle();
    }
    static String serviceInstanceHandle() {
        log("OrderService", "processing, configured pricing timeout=500ms");
        return circuitBreakerProtectedCall();
    }
    static String circuitBreakerProtectedCall() {
        if (circuitOpen) {
            log("CircuitBreaker", "OPEN -- fast-failing without calling pricing-service, using fallback");
            return "{\"orderId\":\"42\",\"price\":\"unavailable\",\"fallback\":true}";
        }
        boolean pricingCallFails = true; // simulating pricing-service currently being slow/unhealthy
        if (pricingCallFails) {
            int count = pricingFailureCount.incrementAndGet();
            log("CircuitBreaker", "downstream call FAILED (failure #" + count + ")");
            if (count >= FAILURE_THRESHOLD) {
                circuitOpen = true;
                log("CircuitBreaker", "threshold reached -- OPENING circuit for future calls");
            }
            return "{\"orderId\":\"42\",\"price\":\"unavailable\",\"fallback\":true}";
        }
        return "{\"orderId\":\"42\",\"price\":\"$42.00\"}";
    }

    static void log(String component, String message) {
        System.out.println("[trace=" + traceId + "][" + component + "] " + message);
    }

    public static void main(String[] args) {
        for (int i = 1; i <= 4; i++) {
            System.out.println("--- request " + i + " ---");
            System.out.println(gatewayRoute("/api/orders/42"));
        }
    }
}
```

How to run: `java FullyAssembledFlow.java`

Across four simulated requests, the first three each attempt the real downstream pricing call, fail, and increment `pricingFailureCount`; by the third failure, `circuitOpen` flips to `true`; the fourth request's `circuitBreakerProtectedCall` immediately fast-fails using the fallback, without even attempting the real downstream call — every log line throughout all four requests shares the same `trace=def456` prefix, letting someone reviewing these logs later reconstruct the *entire* story: routing, instance selection, configured timeout, and exactly when and why the circuit breaker tripped, purely from filtering logs by trace ID.

## 6. Walkthrough

Trace `FullyAssembledFlow.main`'s full four-request sequence end to end, focusing on how each layer's role becomes visible only when the whole chain is assembled:

1. **Request 1**: `gatewayRoute` logs the routing decision; `discoverAndCallInstance` logs the instance selection; `serviceInstanceHandle` logs the configured timeout; `circuitBreakerProtectedCall` attempts the real downstream call, which fails (simulated), incrementing `pricingFailureCount` to 1 — the circuit stays closed, but this specific request's response already reflects the fallback price.
2. **Requests 2 and 3 repeat the identical sequence** — each attempts the real downstream call, each fails, and `pricingFailureCount` reaches 3 by the end of request 3, at which point `circuitOpen` flips to `true` and a log line explicitly records this transition.
3. **Request 4's `circuitBreakerProtectedCall` checks `circuitOpen` first**, finds it `true`, and immediately returns the fallback response *without* attempting the real downstream call at all — a structurally different path through the same method than requests 1-3 took.
4. **Reviewing all four requests' logs together (filterable by the shared `trace=def456` prefix, though here all four happen to share one trace ID for illustration — in a real system each request would generate its own trace ID, with the *circuit breaker's own internal state* being what's shared across requests, not the trace ID itself)** reveals the full story: three consecutive downstream failures, a circuit breaker tripping in response, and a fourth request correctly avoiding a doomed real call thanks to that tripped circuit — a narrative that requires seeing gateway routing, instance selection, configuration, and circuit-breaker state together, not any one of them in isolation.

The key insight this composed example demonstrates: circuit breaker state (open/closed) persists *across* multiple requests and is shared fleet-wide for a given circuit breaker instance/configuration, while a trace ID is normally scoped to *one single request's* journey — understanding which pieces of state are per-request (trace ID, the specific discovered instance chosen) versus which are longer-lived and shared (circuit breaker state, configuration values) is exactly the kind of insight that only emerges from seeing the whole assembled system, not from studying gateway routing, discovery, configuration, and circuit breakers as isolated topics.

## 7. Gotchas & takeaways

> **Gotcha:** debugging "why was this one request slow" by looking only at the service instance's own logs, without tracing the full path back through discovery and the gateway, can lead to incorrectly blaming the instance itself for slowness that actually originated from a stale discovery cache routing to an already-struggling instance, or from a downstream circuit breaker that had just tripped moments before — always reconstruct the *full* traced path before attributing a slow request's root cause to any single component.

- A request in a real Spring Cloud system passes through gateway routing, discovery-based instance selection, configuration-shaped behavior, and circuit-breaker-guarded downstream calls in sequence — understanding each piece alone doesn't reveal how they hand off to each other.
- Trace IDs scope to one request's journey across all these hops; circuit breaker state and configuration values are longer-lived, shared across many requests — recognizing which kind of state each piece of the system carries is essential for correctly diagnosing behavior.
- Configuration changes (like a refreshed timeout) affect the instance-level layer specifically; a gateway route change affects the edge layer; understanding which layer a given change actually reaches is easier once you have the full composed picture.
- When debugging a production issue spanning this whole chain, reconstruct the full traced path (gateway, discovery, instance, downstream call) before attributing root cause to any single component in isolation.
