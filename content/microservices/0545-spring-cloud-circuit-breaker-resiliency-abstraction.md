---
card: microservices
gi: 545
slug: spring-cloud-circuit-breaker-resiliency-abstraction
title: "Spring Cloud Circuit Breaker (resiliency abstraction)"
---

## 1. What it is

**Spring Cloud Circuit Breaker** provides a common abstraction (`CircuitBreakerFactory`, `CircuitBreaker`) over multiple concrete circuit-breaker implementations — most commonly **Resilience4j** today, with Netflix Hystrix as the historical (now unmaintained) original — so application code can wrap a call to a potentially-unreliable downstream dependency in a circuit breaker without depending on any specific library's API directly. A circuit breaker monitors call failures to a dependency and, once failures exceed a threshold, "opens" — short-circuiting further calls immediately with a fast failure or fallback, instead of continuing to let every caller wait out the same failing dependency's timeout, and periodically testing whether the dependency has recovered before fully resuming normal calls.

## 2. Why & when

You wrap a downstream call in a circuit breaker whenever that dependency can fail or degrade in ways that would otherwise cascade back to every caller:

- **Without a circuit breaker, a failing or slow downstream dependency causes every caller to independently wait out the same timeout, repeatedly** — if a dependency is completely down, every single call to it still takes the full timeout duration to fail, wasting time and resources on calls that were never going to succeed, and potentially exhausting the caller's own thread pool or connection pool in the process (recreating exactly the [synchronous call chain](0522-synchronous-call-chains-death-star.md) cascading-failure risk).
- **A circuit breaker tracks the failure rate of calls to a dependency and, once it crosses a configured threshold, "opens" the circuit** — subsequent calls fail immediately (or invoke a fallback) without even attempting the actual call, protecting the caller from wasting time on calls very likely to fail anyway, and reducing load on an already-struggling dependency.
- **After a configured wait period, the circuit breaker moves to a "half-open" state**, allowing a small number of trial calls through to test whether the dependency has recovered — if those trial calls succeed, the circuit closes again (resuming normal calls); if they still fail, it reopens and waits again.
- **Using Spring Cloud Circuit Breaker's abstraction, rather than Resilience4j's API directly, means switching the underlying implementation** (unlikely today, since Resilience4j is the clear standard, but historically relevant when migrating away from Hystrix) **requires only a dependency and configuration change**, not a rewrite of every place a circuit breaker is used.

## 3. Core concept

Think of an electrical circuit breaker in a house, which is the literal namesake of this pattern: instead of letting a short circuit keep drawing dangerous current indefinitely (or forcing every appliance on the circuit to individually detect the fault and protect itself), the breaker trips once it detects a fault, cutting power immediately to prevent further damage. After some time, someone can attempt to reset it — if the underlying short is still there, it trips again instantly; if the fault has cleared, power resumes normally. A software circuit breaker applies the same idea to a failing downstream dependency: rather than letting every single caller independently discover and wait out the same failure, the breaker itself tracks the failure pattern and protects the wider system by failing fast once it's clear the dependency isn't currently working, periodically checking whether it's safe to resume.

Concretely:

1. **Closed state (normal operation)**: calls pass through to the actual dependency; the circuit breaker tracks the rolling failure rate of these calls.
2. **Open state (triggered)**: once the failure rate crosses a configured threshold within a configured window, the circuit "opens" — subsequent calls are immediately failed (or routed to a fallback) without attempting the real call at all, for a configured wait duration.
3. **Half-open state (testing recovery)**: after the wait duration elapses, the circuit allows a limited number of trial calls through to the real dependency — if enough of these succeed, the circuit closes (resuming normal operation); if they still fail, it reopens and the wait period restarts.
4. **A fallback function**, supplied alongside the protected call, defines what to return when the circuit is open (or when the call itself fails) — often a cached or default value, or a clearly-marked "service temporarily unavailable" response, rather than propagating the raw failure to the ultimate caller.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A circuit breaker cycles between closed (normal calls pass through), open (calls fail fast without trying), and half-open (limited trial calls test recovery) states based on observed failure rate">
  <rect x="20" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="100" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CLOSED</text>
  <text x="100" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">calls pass through normally</text>

  <rect x="250" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="330" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OPEN</text>
  <text x="330" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fail fast / fallback, no real call</text>

  <rect x="480" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="560" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">HALF-OPEN</text>
  <text x="560" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">limited trial calls test recovery</text>

  <line x1="180" y1="100" x2="250" y2="100" stroke="#8b949e" marker-end="url(#a10)"/>
  <text x="215" y="90" fill="#8b949e" font-size="7" text-anchor="middle">threshold breached</text>
  <line x1="410" y1="100" x2="480" y2="100" stroke="#8b949e" marker-end="url(#a10)"/>
  <text x="445" y="90" fill="#8b949e" font-size="7" text-anchor="middle">wait elapses</text>
  <path d="M 560 130 Q 330 180 100 130" stroke="#8b949e" fill="none" marker-end="url(#a10)"/>
  <text x="330" y="175" fill="#8b949e" font-size="7" text-anchor="middle">trial calls succeed</text>
  <defs><marker id="a10" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

The circuit cycles from closed to open once failures cross a threshold, then to half-open to test recovery, closing again if trial calls succeed.

## 5. Runnable example

Scenario: calling a flaky downstream pricing service. We start with a plain Java model of a basic failure-counting circuit breaker, extend it to add the half-open recovery-testing state, then show the real Spring Cloud Circuit Breaker (Resilience4j) shape with a fallback.

### Level 1 — Basic

```java
// File: BasicCircuitBreaker.java -- models the CORE idea: track recent
// failures, and once a threshold is crossed, OPEN the circuit and fail
// fast without even attempting the real call.
import java.util.*;

public class BasicCircuitBreaker {
    static int failureCount = 0;
    static final int FAILURE_THRESHOLD = 3;
    static boolean circuitOpen = false;

    static String callDependency(boolean simulateFailure) {
        if (circuitOpen) {
            return "FAST FAIL: circuit is OPEN, not even attempting the real call";
        }
        if (simulateFailure) {
            failureCount++;
            System.out.println("Call failed (failure #" + failureCount + ")");
            if (failureCount >= FAILURE_THRESHOLD) {
                circuitOpen = true;
                System.out.println("Threshold reached -- OPENING the circuit");
            }
            return "call failed";
        }
        return "call succeeded";
    }

    public static void main(String[] args) {
        System.out.println(callDependency(true));
        System.out.println(callDependency(true));
        System.out.println(callDependency(true)); // 3rd failure -- circuit opens
        System.out.println(callDependency(false)); // circuit is open -- fails fast, doesn't even try
    }
}
```

How to run: `java BasicCircuitBreaker.java`

`failureCount` accumulates with each failed call; once it reaches `FAILURE_THRESHOLD` (3), `circuitOpen` is set to `true`. The fourth call, despite `simulateFailure=false` (meaning it would have succeeded), never even attempts the real call — `circuitOpen` is checked first and the call fails fast, exactly the protective behavior a circuit breaker provides once it's determined a dependency is unreliable.

### Level 2 — Intermediate

```java
// File: HalfOpenRecovery.java -- adds the HALF-OPEN state: after a wait
// period, allow a LIMITED trial call through to test if the dependency
// has recovered, closing the circuit again if it succeeds.
import java.time.*;

public class HalfOpenRecovery {
    enum State { CLOSED, OPEN, HALF_OPEN }
    static State state = State.CLOSED;
    static int failureCount = 0;
    static final int FAILURE_THRESHOLD = 3;
    static Instant openedAt;
    static final Duration WAIT_DURATION = Duration.ofSeconds(30);

    static String call(boolean simulateFailure, Instant now) {
        if (state == State.OPEN) {
            if (Duration.between(openedAt, now).compareTo(WAIT_DURATION) >= 0) {
                state = State.HALF_OPEN; // wait elapsed -- allow ONE trial call through
                System.out.println("Wait period elapsed -- moving to HALF_OPEN, allowing a trial call");
            } else {
                return "FAST FAIL: still OPEN, wait period not yet elapsed";
            }
        }

        if (simulateFailure) {
            failureCount++;
            if (state == State.HALF_OPEN) {
                state = State.OPEN; openedAt = now; // trial call failed -- REOPEN
                System.out.println("Trial call FAILED -- back to OPEN");
            } else if (failureCount >= FAILURE_THRESHOLD) {
                state = State.OPEN; openedAt = now;
                System.out.println("Threshold reached -- OPENING");
            }
            return "call failed";
        } else {
            if (state == State.HALF_OPEN) {
                state = State.CLOSED; failureCount = 0; // trial call SUCCEEDED -- fully recovered, CLOSE
                System.out.println("Trial call SUCCEEDED -- circuit CLOSED, fully recovered");
            }
            return "call succeeded";
        }
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-01-01T00:00:00Z");
        call(true, t0); call(true, t0); call(true, t0); // opens after 3 failures
        System.out.println(call(false, t0.plusSeconds(10))); // still within wait period -- fast fail

        System.out.println(call(false, t0.plusSeconds(35))); // wait elapsed, trial call succeeds -- CLOSES
        System.out.println("Final state: " + state);
    }
}
```

How to run: `java HalfOpenRecovery.java`

At `t0+10s`, the wait period (30s) hasn't elapsed, so the call fails fast without even checking `simulateFailure`. At `t0+35s`, the wait period has elapsed, so the state moves to `HALF_OPEN` and the trial call is actually attempted — since `simulateFailure=false` this time, it succeeds, and the circuit fully closes, resetting `failureCount` to 0 and resuming normal operation.

### Level 3 — Advanced

```java
// File: SpringCloudCircuitBreakerRealShape.java -- the REAL Spring Cloud
// Circuit Breaker shape (backed by Resilience4j): wrapping a downstream
// call with a FALLBACK, using the common CircuitBreakerFactory abstraction.
import org.springframework.cloud.client.circuitbreaker.CircuitBreakerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

public class SpringCloudCircuitBreakerRealShape {

    @Service
    static class PricingClient {
        private final RestTemplate restTemplate;
        private final CircuitBreakerFactory circuitBreakerFactory; // the SHARED abstraction, backed by Resilience4j

        PricingClient(RestTemplate restTemplate, CircuitBreakerFactory circuitBreakerFactory) {
            this.restTemplate = restTemplate;
            this.circuitBreakerFactory = circuitBreakerFactory;
        }

        String getPrice(String item) {
            return circuitBreakerFactory.create("pricingServiceCircuitBreaker")
                .run(
                    () -> restTemplate.getForObject("http://pricing-service/prices/" + item, String.class), // the protected call
                    throwable -> fallbackPrice(item, throwable) // invoked on failure OR when circuit is open
                );
        }

        String fallbackPrice(String item, Throwable throwable) {
            System.out.println("Fallback invoked for " + item + " -- reason: " + throwable.getClass().getSimpleName());
            return "{\"item\":\"" + item + "\",\"price\":\"unavailable\",\"fallback\":true}";
        }
    }

    // resilience4j.circuitbreaker.instances.pricingServiceCircuitBreaker.sliding-window-size: 10
    // resilience4j.circuitbreaker.instances.pricingServiceCircuitBreaker.failure-rate-threshold: 50
    // resilience4j.circuitbreaker.instances.pricingServiceCircuitBreaker.wait-duration-in-open-state: 30s
}
```

How to run: requires `spring-cloud-starter-circuitbreaker-resilience4j`; run in a Spring Boot application with the corresponding `resilience4j.circuitbreaker.instances.pricingServiceCircuitBreaker.*` properties configured, and observe `getPrice` returning the real pricing response under normal conditions, but automatically falling back to the `"unavailable"` response (without even attempting the real call) once the pricing service's failure rate crosses the configured 50% threshold within the sliding window.

`circuitBreakerFactory.create("pricingServiceCircuitBreaker")` obtains a named circuit breaker instance (configuration for this specific name comes from `resilience4j.circuitbreaker.instances.pricingServiceCircuitBreaker.*` properties); `.run(supplier, fallback)` wraps the actual downstream call, automatically invoking `fallbackPrice` whenever the call fails *or* whenever the circuit is currently open — application code never needs to check the circuit's state explicitly; the abstraction handles routing to the fallback transparently.

## 6. Walkthrough

Trace what happens across several calls to `pricingClient.getPrice("widget")`, assuming the pricing service starts failing consistently partway through:

1. **Initial calls succeed normally.** `circuitBreakerFactory.create("pricingServiceCircuitBreaker").run(...)` attempts the real `restTemplate.getForObject(...)` call each time, which succeeds, and the circuit breaker's internal tracking records these as successes within its sliding window.
2. **The pricing service begins failing** (say, due to an incident). Subsequent `getPrice` calls attempt the real call, which now throws an exception (a connection timeout or 5xx response) — Resilience4j's tracking records these as failures, and `fallbackPrice` is invoked for each one, returning the `"unavailable"` response instead of propagating the raw exception to `getPrice`'s caller.
3. **Once the failure rate within the configured sliding window (10 calls) crosses the 50% threshold**, Resilience4j opens the circuit internally. Subsequent calls to `getPrice` no longer even attempt `restTemplate.getForObject(...)` at all — `.run(...)` immediately invokes `fallbackPrice` with a `CallNotPermittedException` (Resilience4j's specific signal that the circuit is open), skipping the real call entirely and returning the fallback response essentially instantly, rather than waiting out whatever timeout the real call would have needed.
4. **After the configured 30-second wait duration elapses**, Resilience4j allows a limited number of trial calls through in a half-open state. If the pricing service has recovered by then, these trial calls succeed, and the circuit closes, resuming normal `getPrice` behavior; if the service is still failing, the circuit reopens and the wait period restarts.

Throughout this entire sequence, `PricingClient.getPrice`'s own code never changes or checks circuit state explicitly — the exact same `.run(supplier, fallback)` call handles every state transition (closed, open, half-open) transparently, always either returning the real result or invoking the fallback, and never leaving the caller to handle a raw, unhandled exception from the underlying HTTP call.

## 7. Gotchas & takeaways

> **Gotcha:** the fallback function itself must be reliable and fast — if `fallbackPrice` (or any fallback) performs its own slow or failure-prone operation (say, querying a different backup service), a struggling primary dependency combined with a struggling fallback can still leave the caller waiting or failing, defeating the entire purpose of the circuit breaker; fallbacks should typically be simple, local, and nearly guaranteed to succeed quickly (a cached value, a hardcoded default, or a clearly-marked unavailable response).

- A circuit breaker protects callers from repeatedly waiting out (or being harmed by) a downstream dependency that's currently failing, by tracking failure rate and short-circuiting to a fallback once a threshold is crossed.
- The three states (closed, open, half-open) let the system recover automatically: trial calls in the half-open state test whether the dependency has healed, without requiring every caller to keep hammering a still-broken dependency indefinitely.
- Spring Cloud Circuit Breaker's `CircuitBreakerFactory` abstraction decouples application code from the specific underlying implementation (Resilience4j today) — the same benefit the [Spring Cloud Commons](0539-spring-cloud-commons-shared-abstractions.md) interfaces provide for discovery and load balancing.
- Keep fallback logic simple, fast, and reliable — a fallback that can itself fail or hang undermines the protection a circuit breaker is meant to provide.
