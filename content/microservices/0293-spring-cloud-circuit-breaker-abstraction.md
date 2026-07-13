---
card: microservices
gi: 293
slug: spring-cloud-circuit-breaker-abstraction
title: "Spring Cloud Circuit Breaker abstraction"
---

## 1. What it is

Spring Cloud Circuit Breaker is a thin abstraction layer that provides a single, consistent API for circuit breaking (`CircuitBreakerFactory` and `ReactiveCircuitBreakerFactory`) over multiple underlying implementations — Resilience4j being the dominant one in current Spring projects, with Netflix Hystrix as a legacy (now unmaintained) option. Application code depends only on Spring's `CircuitBreaker` interface, not on Resilience4j-specific types, so the underlying implementation can in principle be swapped by changing a starter dependency, without touching business logic that uses circuit breakers.

## 2. Why & when

Before this abstraction existed, Spring applications using Hystrix wrote code directly against Hystrix's API (`@HystrixCommand`, `HystrixCommand` objects); when Hystrix went into maintenance mode, migrating to Resilience4j meant rewriting every call site. Spring Cloud Circuit Breaker exists specifically to prevent that kind of lock-in going forward: business logic calls `circuitBreakerFactory.create("name").run(supplier, fallback)`, and the actual circuit-breaking implementation underneath is an infrastructure/configuration concern, selected by which starter is on the classpath (`spring-cloud-starter-circuitbreaker-resilience4j` is the standard modern choice).

Use this abstraction when writing new Spring Boot code that needs circuit breaking and there's value in not hard-coding a dependency on Resilience4j's specific API — which is nearly always true for application code, since implementation-specific *configuration* (thresholds, sliding window sizes) is done separately anyway via `application.yml`, and doesn't require touching the abstraction. For code that needs Resilience4j-specific features not exposed by the abstraction (like its detailed event publishing), calling Resilience4j's API directly, or using its `@CircuitBreaker` annotation (see [Resilience4j annotations](0295-resilience4j-annotations-circuitbreaker-retry-bulkhead-ratel.md)), remains an option.

## 3. Core concept

`CircuitBreakerFactory.create(name)` returns a `CircuitBreaker` instance; `.run(supplier, fallbackFunction)` executes the supplier through it, invoking the fallback on any failure (including an open circuit).

```java
import org.springframework.cloud.client.circuitbreaker.CircuitBreakerFactory;
import org.springframework.stereotype.Service;

@Service
class PaymentService {
    private final CircuitBreakerFactory circuitBreakerFactory;
    private final PaymentClient paymentClient;

    PaymentService(CircuitBreakerFactory circuitBreakerFactory, PaymentClient paymentClient) {
        this.circuitBreakerFactory = circuitBreakerFactory;
        this.paymentClient = paymentClient;
    }

    String chargeCard(String orderId) {
        return circuitBreakerFactory.create("chargeCard") // NAME maps to a NAMED config in application.yml
                .run(() -> paymentClient.charge(orderId),  // primary call
                     throwable -> "FALLBACK: charge queued for retry"); // invoked on ANY failure
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code depends only on Spring's CircuitBreakerFactory interface; underneath, a pluggable implementation -- Resilience4j today, historically Hystrix -- actually performs the circuit breaking, selected by which starter dependency is on the classpath rather than by application code">
  <rect x="30" y="30" width="220" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="140" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Application code</text>
  <text x="140" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">depends on CircuitBreakerFactory</text>

  <line x1="140" y1="80" x2="140" y2="110" stroke="#8b949e" marker-end="url(#arr293)"/>

  <rect x="30" y="115" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="139" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Spring Cloud abstraction</text>

  <line x1="250" y1="135" x2="340" y2="90" stroke="#8b949e" marker-end="url(#arr293)"/>
  <line x1="250" y1="135" x2="340" y2="140" stroke="#8b949e" marker-end="url(#arr293)"/>

  <rect x="350" y="70" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="425" y="92" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Resilience4j (current)</text>

  <rect x="350" y="120" width="150" height="35" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="425" y="142" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Hystrix (legacy)</text>

  <defs><marker id="arr293" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Application code targets the stable abstraction; the concrete implementation is a swappable dependency choice.

## 5. Runnable example

Scenario: a Spring service calling a payment client directly with no protection, extended to wrap it with `CircuitBreakerFactory` and a fallback so failures degrade gracefully, and finally configuring the underlying Resilience4j behavior declaratively via `application.yml` (thresholds, wait duration) without touching the abstraction-based application code at all.

### Level 1 — Basic

```java
// File: PaymentServiceNoProtection.java -- calls the payment client
// directly; any failure propagates straight to the caller with no
// circuit breaking at all.
public class PaymentServiceNoProtection {
    static class PaymentClient {
        int callCount = 0;
        String charge(String orderId) {
            callCount++;
            throw new RuntimeException("payment-gateway unreachable");
        }
    }

    static class PaymentService {
        final PaymentClient paymentClient;
        PaymentService(PaymentClient paymentClient) { this.paymentClient = paymentClient; }
        String chargeCard(String orderId) { return paymentClient.charge(orderId); }
    }

    public static void main(String[] args) {
        PaymentService service = new PaymentService(new PaymentClient());
        try {
            System.out.println(service.chargeCard("order-1"));
        } catch (Exception e) {
            System.out.println("chargeCard FAILED with a raw exception: " + e.getMessage());
        }
    }
}
```

How to run: `java PaymentServiceNoProtection.java`

`chargeCard` calls `paymentClient.charge` directly, and since the gateway is simulated as unreachable, the exception propagates straight out to the caller with no protection, no fallback, and no tracking of repeated failures across calls.

### Level 2 — Intermediate

```java
// File: SpringCloudCircuitBreakerWrapped.java -- a hand-rolled stand-in
// for Spring Cloud's CircuitBreakerFactory abstraction (the real
// interface is org.springframework.cloud.client.circuitbreaker.CircuitBreakerFactory,
// backed by spring-cloud-starter-circuitbreaker-resilience4j in a real
// project) showing the SAME application code pattern: create a named
// circuit breaker, run the call with a fallback.
public class SpringCloudCircuitBreakerWrapped {
    // Stands in for org.springframework.cloud.client.circuitbreaker.CircuitBreaker
    interface CircuitBreaker {
        <T> T run(java.util.function.Supplier<T> supplier, java.util.function.Function<Throwable, T> fallback);
    }
    // Stands in for CircuitBreakerFactory -- the ABSTRACTION application code depends on.
    static class SimpleCircuitBreakerFactory {
        java.util.Map<String, Integer> failureCounts = new java.util.HashMap<>();
        CircuitBreaker create(String name) {
            return new CircuitBreaker() {
                public <T> T run(java.util.function.Supplier<T> supplier, java.util.function.Function<Throwable, T> fallback) {
                    try { return supplier.get(); }
                    catch (Throwable t) {
                        failureCounts.merge(name, 1, Integer::sum);
                        return fallback.apply(t);
                    }
                }
            };
        }
    }

    static class PaymentClient {
        String charge(String orderId) { throw new RuntimeException("payment-gateway unreachable"); }
    }

    static class PaymentService {
        final SimpleCircuitBreakerFactory circuitBreakerFactory;
        final PaymentClient paymentClient;
        PaymentService(SimpleCircuitBreakerFactory circuitBreakerFactory, PaymentClient paymentClient) {
            this.circuitBreakerFactory = circuitBreakerFactory; this.paymentClient = paymentClient;
        }
        String chargeCard(String orderId) {
            return circuitBreakerFactory.create("chargeCard")
                    .run(() -> paymentClient.charge(orderId),
                         throwable -> "FALLBACK: charge queued for retry (" + throwable.getMessage() + ")");
        }
    }

    public static void main(String[] args) {
        PaymentService service = new PaymentService(new SimpleCircuitBreakerFactory(), new PaymentClient());
        System.out.println(service.chargeCard("order-1"));
        System.out.println(service.chargeCard("order-2"));
    }
}
```

How to run: `java SpringCloudCircuitBreakerWrapped.java`

`chargeCard` now goes through the abstraction: `circuitBreakerFactory.create("chargeCard").run(...)`. Both calls fail against the simulated gateway, but instead of a raw exception reaching the caller, the fallback function returns a graceful degraded message. Note that `PaymentService` never references anything Resilience4j-specific — in a real Spring Boot app, `CircuitBreakerFactory` here would be the actual `org.springframework.cloud.client.circuitbreaker.CircuitBreakerFactory` bean, auto-configured by whichever starter (Resilience4j) is on the classpath, injected exactly like any other Spring bean.

### Level 3 — Advanced

```java
// File: SpringBootActualUsage.java -- the REAL Spring Boot shape: a
// @Service using the actual org.springframework.cloud.client.circuitbreaker
// API, with the underlying Resilience4j behavior configured externally
// via application.yml rather than in code, demonstrating the separation
// between the portable application code and the implementation-specific config.
/*
// build.gradle / pom.xml: spring-cloud-starter-circuitbreaker-resilience4j

package com.example.payments;

import org.springframework.cloud.client.circuitbreaker.CircuitBreakerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.*;

@Service
class PaymentService {
    private final CircuitBreakerFactory circuitBreakerFactory;
    private final PaymentClient paymentClient;

    PaymentService(CircuitBreakerFactory circuitBreakerFactory, PaymentClient paymentClient) {
        this.circuitBreakerFactory = circuitBreakerFactory;
        this.paymentClient = paymentClient;
    }

    public String chargeCard(String orderId) {
        return circuitBreakerFactory.create("chargeCard")
                .run(() -> paymentClient.charge(orderId),
                     throwable -> "FALLBACK: charge queued for retry");
    }
}

@RestController
class PaymentController {
    private final PaymentService paymentService;
    PaymentController(PaymentService paymentService) { this.paymentService = paymentService; }

    @PostMapping("/orders/{orderId}/charge")
    public String charge(@PathVariable String orderId) { return paymentService.chargeCard(orderId); }
}
*/

// application.yml -- the RESILIENCE4J-SPECIFIC config, entirely separate
// from the application code above, which never mentions Resilience4j:
//
// resilience4j:
//   circuitbreaker:
//     instances:
//       chargeCard:
//         failure-rate-threshold: 50
//         sliding-window-size: 10
//         minimum-number-of-calls: 5
//         wait-duration-in-open-state: 15s
//         permitted-number-of-calls-in-half-open-state: 3

public class SpringBootActualUsage {
    public static void main(String[] args) {
        System.out.println("See the commented Spring Boot source and application.yml above:");
        System.out.println("- PaymentService and PaymentController use ONLY org.springframework.cloud.client.circuitbreaker types.");
        System.out.println("- ALL Resilience4j-specific tuning (thresholds, window size, wait duration) lives in application.yml.");
        System.out.println("- Swapping to a different CircuitBreaker implementation would require ZERO changes to PaymentService.");
    }
}
```

How to run: `java SpringBootActualUsage.java` (prints an explanation; the real code lives in the comment block as it would appear in an actual Spring Boot project, since a live Spring context requires a running Spring Boot application rather than a bare `java File.java` invocation)

The commented Spring Boot code shows the pattern exactly as it appears in production: `PaymentService` depends only on `CircuitBreakerFactory`, an interface from `spring-cloud-commons`. All the Resilience4j-specific tuning — failure rate threshold, sliding window size, wait duration in the open state — lives entirely in `application.yml`, tied to the circuit breaker's *name* (`chargeCard`), not referenced anywhere in the Java code. This is the concrete benefit of the abstraction: changing resilience behavior is a configuration change, and even switching the underlying implementation library would not require touching `PaymentService` at all.

## 6. Walkthrough

Trace a request through the (commented) Spring Boot version end to end, as `POST /orders/order-1/charge` with an empty body. **First**, Spring's `DispatcherServlet` routes the request to `PaymentController.charge`, extracting `orderId="order-1"` from the path variable.

**`charge` calls `paymentService.chargeCard("order-1")`.** Inside, `chargeCard` calls `circuitBreakerFactory.create("chargeCard")` — this looks up (or lazily creates) the circuit breaker instance named `"chargeCard"`, which Spring Cloud's Resilience4j auto-configuration has already wired up using the settings under `resilience4j.circuitbreaker.instances.chargeCard` in `application.yml` (failure-rate-threshold 50%, sliding-window-size 10, etc.) — this is the layer where the abstraction and the concrete implementation meet, entirely outside application code.

**`.run(supplier, fallback)` is called.** If the circuit is closed, the supplier (`() -> paymentClient.charge(orderId)`) executes, making the real outbound call to the payment gateway. Suppose this call fails (gateway timeout).

**Request/response shape at the client boundary** (what `paymentClient.charge` would have sent):
```
POST https://payment-gateway.internal/charge
Content-Type: application/json

{"orderId":"order-1"}
```
which times out with no response received.

**Back inside `.run`**, the circuit breaker records this failure against its sliding window (contributing to the failure-rate calculation configured in `application.yml`) and, because the call threw, invokes the `fallback` function instead of propagating the exception — returning `"FALLBACK: charge queued for retry"`.

**This string flows back up** through `chargeCard`, through `PaymentController.charge`, and becomes the HTTP response body:
```
HTTP/1.1 200 OK
Content-Type: text/plain

FALLBACK: charge queued for retry
```

**State transformation across layers**: the raw HTTP request enters at the controller layer → is delegated to the service layer, which wraps the actual outbound call in the circuit-breaker abstraction → the abstraction layer delegates to the Resilience4j implementation layer (configured via YAML, invisible to the Java code) → a failure at the network layer flows back up through each layer, transformed at the circuit-breaker layer from a raw exception into a graceful fallback value → and finally reaches the HTTP response layer as a normal 200 OK rather than a 500 error.

## 7. Gotchas & takeaways

> The circuit breaker's *name* passed to `create(name)` is the link between application code and its YAML configuration — a typo in that name silently falls back to Resilience4j's global default configuration instead of the intended named settings, with no compile-time or obvious runtime error to catch the mistake.

- Application code should depend on `org.springframework.cloud.client.circuitbreaker.CircuitBreakerFactory`, never directly on Resilience4j types, to keep the implementation swappable and the business logic focused.
- All implementation-specific tuning belongs in configuration (`application.yml`), tied to the circuit breaker's name — this is also what makes per-dependency tuning easy, since each named instance can have its own thresholds.
- For reactive Spring WebFlux applications, use `ReactiveCircuitBreakerFactory` instead, which returns a `Mono`/`Flux`-friendly `run` method rather than a blocking one.
- Hystrix is in maintenance mode and should not be chosen for new projects; `spring-cloud-starter-circuitbreaker-resilience4j` is the standard modern starter for this abstraction.
