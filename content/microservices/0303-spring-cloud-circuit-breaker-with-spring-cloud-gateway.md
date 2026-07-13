---
card: microservices
gi: 303
slug: spring-cloud-circuit-breaker-with-spring-cloud-gateway
title: "Spring Cloud Circuit Breaker with Spring Cloud Gateway"
---

## 1. What it is

Spring Cloud Gateway's `CircuitBreaker` filter is itself built on the [Spring Cloud Circuit Breaker abstraction](0293-spring-cloud-circuit-breaker-abstraction.md) covered earlier in this section — the same `CircuitBreakerFactory`/`ReactiveCircuitBreakerFactory` interface used in application code is what the gateway's filter uses internally to wrap each route's proxied call. This means gateway-level circuit breaking is configured the same way as service-level circuit breaking (named instances in `application.yml` under `resilience4j.circuitbreaker.instances`), and understanding one directly transfers to understanding the other.

## 2. Why & when

This topic exists specifically to close the loop between two things covered separately earlier in this section: [Spring Cloud Circuit Breaker abstraction](0293-spring-cloud-circuit-breaker-abstraction.md) (the portable API, usable in any Spring bean) and [Spring Cloud Gateway resilience filters](0299-spring-cloud-gateway-resilience-filters.md) (the gateway's built-in filters). The gateway's `CircuitBreaker` filter is not a separate, gateway-specific circuit-breaking implementation — it is the exact same abstraction, applied at the routing layer instead of inside a service's business logic, configured with the exact same `resilience4j.circuitbreaker.instances.<name>` YAML structure used for any other named circuit breaker in the application.

Recognizing this unification matters practically: a team debugging a route-level circuit breaker doesn't need to learn a separate configuration model — the same mental model, the same metrics via Micrometer, and the same tuning knobs (`failureRateThreshold`, `slidingWindowSize`, `waitDurationInOpenState`) apply whether the circuit breaker is named `inventoryCB` for a gateway route or `inventory` for a service-level `@CircuitBreaker` annotation on an internal client call.

## 3. Core concept

The gateway's `CircuitBreaker` filter references a circuit breaker by name, exactly like `CircuitBreakerFactory.create(name)` does in application code, and both draw their configuration from the same `resilience4j.circuitbreaker.instances` YAML block.

```yaml
resilience4j:
  circuitbreaker:
    instances:
      inventoryCB:                          # used by the GATEWAY's CircuitBreaker filter
        failure-rate-threshold: 50
        sliding-window-size: 10
        wait-duration-in-open-state: 15s
      inventory:                            # used by a SERVICE's @CircuitBreaker(name="inventory")
        failure-rate-threshold: 40
        sliding-window-size: 20

spring:
  cloud:
    gateway:
      routes:
        - id: inventory-route
          uri: lb://inventory-service
          filters:
            - name: CircuitBreaker
              args:
                name: inventoryCB           # SAME resolution mechanism as CircuitBreakerFactory.create("inventoryCB")
                fallbackUri: forward:/fallback/inventory
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Both a gateway route's CircuitBreaker filter and a service bean's CircuitBreakerFactory usage resolve named circuit breaker instances from the exact same underlying Resilience4j registry, configured by the exact same application.yml structure, so both layers share one consistent mental model">
  <rect x="30" y="20" width="220" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="140" y="44" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Gateway CircuitBreaker filter</text>

  <rect x="390" y="20" width="220" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="500" y="44" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">@CircuitBreaker in a @Service</text>

  <line x1="140" y1="60" x2="280" y2="110" stroke="#8b949e" marker-end="url(#arr303)"/>
  <line x1="500" y1="60" x2="360" y2="110" stroke="#8b949e" marker-end="url(#arr303)"/>

  <rect x="230" y="115" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="135" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">SAME Resilience4j registry</text>
  <text x="320" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">SAME application.yml config</text>

  <defs><marker id="arr303" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Gateway filters and service-level annotations are two different entry points into the exact same underlying circuit breaker mechanism.

## 5. Runnable example

Scenario: two separately implemented circuit breakers (one hand-rolled for a "gateway route," one for a "service call") that duplicate logic and drift independently, extended to a shared circuit breaker registry both the gateway layer and the service layer resolve names from — mirroring the real unification — and finally demonstrating that a circuit tripped via gateway-layer traffic is immediately visible to (and affects) service-layer code checking the same named instance, since they share the exact same underlying state.

### Level 1 — Basic

```java
// File: DuplicatedSeparateCircuitBreakers.java -- a gateway filter and a
// service call EACH implement their own independent circuit breaker
// logic, even when conceptually protecting the same downstream
// dependency -- they can drift out of sync and provide inconsistent protection.
public class DuplicatedSeparateCircuitBreakers {
    enum State { CLOSED, OPEN }

    static class GatewayCircuitBreaker {
        State state = State.CLOSED;
        int failures = 0;
        boolean recordAndCheck(boolean failed) {
            if (state == State.OPEN) return false;
            if (failed) { failures++; if (failures >= 2) state = State.OPEN; }
            return state != State.OPEN;
        }
    }
    static class ServiceCircuitBreaker {
        State state = State.CLOSED;
        int failures = 0;
        boolean recordAndCheck(boolean failed) {
            if (state == State.OPEN) return false;
            if (failed) { failures++; if (failures >= 2) state = State.OPEN; }
            return state != State.OPEN;
        }
    }

    public static void main(String[] args) {
        GatewayCircuitBreaker gatewayCB = new GatewayCircuitBreaker();
        ServiceCircuitBreaker serviceCB = new ServiceCircuitBreaker();

        // Gateway-layer traffic trips ITS breaker...
        gatewayCB.recordAndCheck(true);
        gatewayCB.recordAndCheck(true);
        System.out.println("Gateway breaker state: " + gatewayCB.state);

        // ...but a service-layer call, checking a COMPLETELY SEPARATE breaker
        // instance, has no idea the dependency is already known to be failing.
        System.out.println("Service breaker state: " + serviceCB.state + " (unaware of gateway's observations, will attempt the call anyway)");
    }
}
```

How to run: `java DuplicatedSeparateCircuitBreakers.java`

The gateway's circuit breaker trips open after observing two failures from route traffic, but the service-layer circuit breaker is a completely independent object that never learns about this — it stays `CLOSED` and would still attempt calls to the already-known-unhealthy dependency, duplicating both the tracking effort and, worse, providing inconsistent protection depending on which code path happens to notice the failures first.

### Level 2 — Intermediate

```java
// File: SharedNamedRegistry.java -- BOTH the "gateway filter" and the
// "service call" resolve their circuit breaker from the SAME shared,
// named registry -- mirroring how Spring Cloud Gateway's CircuitBreaker
// filter and a @Service's CircuitBreakerFactory usage both draw from the
// SAME underlying Resilience4j CircuitBreakerRegistry.
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class SharedNamedRegistry {
    enum State { CLOSED, OPEN }
    static class CircuitBreaker {
        State state = State.CLOSED;
        int failures = 0;
        boolean recordAndCheck(boolean failed) {
            if (state == State.OPEN) return false;
            if (failed) { failures++; if (failures >= 2) state = State.OPEN; }
            return state != State.OPEN;
        }
    }

    // ONE shared registry, keyed by name -- exactly like Resilience4j's
    // CircuitBreakerRegistry, which both CircuitBreakerFactory.create(name)
    // (service layer) and the gateway's CircuitBreaker filter's 'name' arg
    // resolve against.
    static final Map<String, CircuitBreaker> registry = new ConcurrentHashMap<>();
    static CircuitBreaker resolve(String name) { return registry.computeIfAbsent(name, k -> new CircuitBreaker()); }

    public static void main(String[] args) {
        // Gateway route traffic resolves "inventoryCB" ...
        CircuitBreaker gatewayView = resolve("inventoryCB");
        gatewayView.recordAndCheck(true);
        gatewayView.recordAndCheck(true);
        System.out.println("Gateway route observed 2 failures, breaker now: " + gatewayView.state);

        // ...and a service bean ALSO resolves "inventoryCB" (same name!) --
        // it gets the SAME shared instance, already OPEN.
        CircuitBreaker serviceView = resolve("inventoryCB");
        System.out.println("Service-layer code resolving the SAME name sees: " + serviceView.state
                + " (identical object: " + (gatewayView == serviceView) + ")");
    }
}
```

How to run: `java SharedNamedRegistry.java`

Both the "gateway" call site and the "service" call site resolve the circuit breaker via the identical `resolve("inventoryCB")` call against a shared registry — `computeIfAbsent` guarantees they get the exact same object instance (confirmed by the printed `true` for the reference equality check). Once the gateway-layer traffic trips it open, the service-layer code immediately sees `OPEN` too, because there was never a second, separate breaker to begin with — this is precisely what happens in a real Spring Boot app when a gateway route's `CircuitBreaker` filter and a `@Service`'s `@CircuitBreaker` annotation are (perhaps inadvertently, perhaps deliberately) configured with the same instance name.

### Level 3 — Advanced

```java
// File: DeliberateSharedVsIsolatedNaming.java -- demonstrates the
// PRACTICAL configuration choice this unification enables: deliberately
// using the SAME name to share circuit-breaking state between a gateway
// route and a service's internal calls to the SAME physical dependency,
// versus deliberately using DIFFERENT names to keep them isolated when
// that's actually desired (e.g., the gateway protects against one
// downstream instance while the service calls a different internal
// endpoint on the same logical service).
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class DeliberateSharedVsIsolatedNaming {
    enum State { CLOSED, OPEN }
    static class CircuitBreaker {
        State state = State.CLOSED;
        int failures = 0;
        boolean recordAndCheck(boolean failed) {
            if (state == State.OPEN) return false;
            if (failed) { failures++; if (failures >= 2) state = State.OPEN; }
            return state != State.OPEN;
        }
    }
    static final Map<String, CircuitBreaker> registry = new ConcurrentHashMap<>();
    static CircuitBreaker resolve(String name) { return registry.computeIfAbsent(name, k -> new CircuitBreaker()); }

    public static void main(String[] args) {
        System.out.println("-- Scenario A: SHARED name, deliberate coordination --");
        resolve("inventory").recordAndCheck(true);
        resolve("inventory").recordAndCheck(true);
        System.out.println("Gateway route (name='inventory') AND service bean (name='inventory') "
                + "now BOTH see: " + resolve("inventory").state + " -- coordinated protection of the SAME dependency");

        System.out.println("-- Scenario B: ISOLATED names, deliberate separation --");
        resolve("inventoryGatewayRoute").recordAndCheck(true);
        resolve("inventoryGatewayRoute").recordAndCheck(true);
        System.out.println("Gateway route (name='inventoryGatewayRoute') tripped: " + resolve("inventoryGatewayRoute").state);
        System.out.println("Service bean (name='inventoryInternalClient') unaffected: " + resolve("inventoryInternalClient").state
                + " -- deliberately isolated, e.g. because they call DIFFERENT endpoints on the inventory service");
    }
}
```

How to run: `java DeliberateSharedVsIsolatedNaming.java`

Scenario A shows both layers deliberately using the identical name `"inventory"`, so failures observed at the gateway layer immediately and correctly affect service-layer behavior toward the same dependency — appropriate when both layers are genuinely calling the same underlying endpoint and should share fate. Scenario B shows deliberately different names (`"inventoryGatewayRoute"` vs `"inventoryInternalClient"`), keeping the two circuit breakers fully isolated — appropriate when the gateway route and the internal service client are actually calling different endpoints, or when isolating their failure domains is intentional so a problem visible at the edge doesn't unnecessarily also trip protection for an unrelated internal call path. This naming choice — share or isolate — is a deliberate architectural decision enabled directly by understanding that both layers draw from the same underlying named registry.

## 6. Walkthrough

Trace `DeliberateSharedVsIsolatedNaming.main`'s Scenario A. **First**, `resolve("inventory")` is called twice in a row within the first two lines, each followed immediately by `.recordAndCheck(true)`. Because `resolve` uses `computeIfAbsent`, the first call creates a fresh `CircuitBreaker` and stores it under key `"inventory"`; the second call finds it already present and returns the *same* object — both `recordAndCheck(true)` invocations operate on one shared `CircuitBreaker` instance.

**Call 1**: `state` is `CLOSED`, so it checks `if (failed)` — true, increments `failures` to 1, which is `< 2`, so `state` stays `CLOSED`.

**Call 2**: `state` is still `CLOSED`, `failed` is true again, `failures` becomes 2, meeting the threshold, so `state` flips to `OPEN`.

**The final `resolve("inventory").state` print** calls `resolve` a third time — `computeIfAbsent` again finds the existing entry (no new object created) and returns the same, now-`OPEN` instance. The printed message correctly shows `OPEN`, framed as both the gateway route and the service bean observing this shared state, since — conceptually — both would have been calling `resolve("inventory")` (or, in real Spring code, both `CircuitBreakerFactory.create("inventory")` from a service bean and the gateway's `CircuitBreaker` filter configured with `name: inventory` would resolve to the exact same entry in Resilience4j's actual `CircuitBreakerRegistry`).

**Scenario B follows an analogous sequence** but against two entirely separate map keys (`"inventoryGatewayRoute"` and `"inventoryInternalClient"`), so `computeIfAbsent` creates two distinct `CircuitBreaker` objects — tripping one via `recordAndCheck` calls has no effect whatsoever on the other, since they were never the same object to begin with.

```
resolve("inventory") called from "gateway" call site -> creates entry, returns CB#1
resolve("inventory") called AGAIN (same key)          -> returns the SAME CB#1
   .recordAndCheck(true) x2 on CB#1 -> CB#1.state = OPEN
resolve("inventory") called from "service" call site  -> returns the SAME CB#1, already OPEN
```

## 7. Gotchas & takeaways

> Using the same circuit breaker name across a gateway route and a service's internal calls is a deliberate coordination choice, not an automatic default that "just happens to be convenient" — verify the two call sites are genuinely protecting the same physical dependency before sharing a name, or an unrelated failure domain can end up incorrectly tripping protection for a call path that was actually fine.

- The gateway's `CircuitBreaker` filter and a `@Service`'s `CircuitBreakerFactory`/`@CircuitBreaker` usage are two different entry points into the exact same Resilience4j circuit breaker registry and the exact same `application.yml` configuration model — there is no separate "gateway circuit breaker" implementation to learn.
- Deliberately sharing a name across layers coordinates protection for genuinely the same dependency; deliberately using different names keeps failure domains isolated when that's the correct architectural choice.
- Because they share the same underlying mechanism, [metrics via Micrometer](0297-resilience4j-metrics-via-micrometer.md) work identically for gateway-level and service-level circuit breakers — the same dashboard and alerting patterns apply to both without any special-casing.
- This unification is a direct benefit of the Spring Cloud Circuit Breaker abstraction's design: because the gateway itself is just another consumer of `CircuitBreakerFactory`, adding circuit breaking to a new layer of the system never requires learning a new configuration model, only deciding on a naming strategy.
