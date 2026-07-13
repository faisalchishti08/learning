---
card: microservices
gi: 177
slug: gateway-circuit-breaker-filter-resilience4j
title: "Gateway circuit breaker filter (Resilience4j)"
---

## 1. What it is

Spring Cloud Gateway's circuit breaker filter, backed by Resilience4j, wraps a route's backend calls with circuit-breaker logic directly at the gateway — after a configured failure threshold is crossed for a given backend, the circuit "opens" and the gateway stops even attempting calls to that backend for a cooldown period, immediately returning a fallback response instead, protecting both the struggling backend from further load and the gateway's own resources from piling up on calls likely to fail anyway.

## 2. Why & when

When a backend service starts failing or responding slowly, continuing to send it the same volume of traffic makes the problem worse, not better — a struggling service under continued load is less likely to recover, and every gateway request still waiting on that struggling backend ties up gateway resources (threads or, in the reactive model, in-flight request state) that could otherwise serve healthy traffic. A circuit breaker at the gateway detects this failure pattern automatically and, once a threshold is crossed, stops sending traffic to the struggling backend entirely for a cooldown period, giving it room to recover while immediately failing fast (or falling back gracefully) for requests that would otherwise wait and likely fail anyway.

Apply a circuit breaker filter to any route where backend failures are plausible and where failing fast (or falling back) is preferable to letting every request wait out a slow or failing backend's full timeout individually. This is especially valuable for [request aggregation](0165-request-aggregation-composition.md) scenarios, where one struggling backend among several being called shouldn't be allowed to degrade the entire aggregated response's latency.

## 3. Core concept

The circuit breaker tracks recent call outcomes for a given backend; once the failure rate crosses a configured threshold within a rolling window, the circuit transitions to "open," and subsequent calls are short-circuited immediately (returning a fallback) without even attempting the backend call, until a cooldown period elapses and the circuit moves to "half-open" to cautiously test whether the backend has recovered.

```java
.filters(f -> f.circuitBreaker(config -> config
    .setName("orderServiceCircuitBreaker")
    .setFallbackUri("forward:/fallback/orders"))) // called INSTEAD of the backend once the circuit is open

// Resilience4j config: open the circuit after 50% failures in the last 10 calls, stay open 30 seconds
resilience4j.circuitbreaker.instances.orderServiceCircuitBreaker.failure-rate-threshold: 50
resilience4j.circuitbreaker.instances.orderServiceCircuitBreaker.sliding-window-size: 10
resilience4j.circuitbreaker.instances.orderServiceCircuitBreaker.wait-duration-in-open-state: 30s
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A circuit breaker cycles through three states: CLOSED, where calls pass through normally; OPEN, where calls are short-circuited to a fallback immediately after a failure threshold is crossed; and HALF-OPEN, where a cooldown period has elapsed and a few test calls are allowed through to check for recovery" >
  <rect x="20" y="60" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="89" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">CLOSED</text>

  <rect x="250" y="60" width="140" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="320" y="89" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OPEN</text>

  <rect x="480" y="60" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="89" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">HALF-OPEN</text>

  <line x1="160" y1="85" x2="248" y2="85" stroke="#8b949e" marker-end="url(#arr58)"/>
  <text x="205" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">threshold crossed</text>

  <line x1="390" y1="85" x2="478" y2="85" stroke="#8b949e" marker-end="url(#arr58)"/>
  <text x="435" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">cooldown elapses</text>

  <path d="M550,110 Q550,150 90,150 Q90,150 90,112" fill="none" stroke="#8b949e" marker-end="url(#arr58)"/>
  <text x="320" y="163" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">test calls succeed -&gt; back to CLOSED</text>

  <defs>
    <marker id="arr58" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The circuit cycles between allowing traffic, blocking it entirely, and cautiously testing recovery.

## 5. Runnable example

Scenario: a gateway route calling a failing backend that starts with no circuit breaker (showing every request waiting out the full failure), adds a circuit breaker that opens after a failure threshold and short-circuits subsequent calls to a fallback, and finally demonstrates the half-open recovery test cycle, closing the circuit again once the backend genuinely recovers.

### Level 1 — Basic

```java
// File: NoCircuitBreaker.java -- EVERY request waits out the FULL failing-backend
// timeout individually, even once it's clear the backend is down.
public class NoCircuitBreaker {
    static boolean backendIsDown = true;

    static String callBackend() {
        if (backendIsDown) throw new RuntimeException("backend timeout after waiting the FULL configured timeout");
        return "200 OK";
    }

    public static void main(String[] args) {
        for (int i = 1; i <= 5; i++) {
            try {
                System.out.println("Request " + i + ": " + callBackend());
            } catch (RuntimeException e) {
                System.out.println("Request " + i + ": FAILED -- " + e.getMessage() + " (paid the FULL wait cost, again)");
            }
        }
        System.out.println("ALL 5 requests paid the full failure cost individually -- nothing learned from the first failure.");
    }
}
```

**How to run:** `javac NoCircuitBreaker.java && java NoCircuitBreaker` (JDK 17+).

### Level 2 — Intermediate

```java
// File: CircuitBreakerOpensAndFallsBack.java -- after a FAILURE THRESHOLD, the
// circuit OPENS and subsequent calls short-circuit to a fallback INSTANTLY.
public class CircuitBreakerOpensAndFallsBack {
    enum State { CLOSED, OPEN }

    static class CircuitBreaker {
        State state = State.CLOSED;
        int consecutiveFailures = 0;
        int failureThreshold = 2;

        String call(java.util.function.Supplier<String> backendCall, java.util.function.Supplier<String> fallback) {
            if (state == State.OPEN) {
                System.out.println("  [circuit OPEN] short-circuiting to fallback, NOT calling backend at all");
                return fallback.get();
            }
            try {
                String result = backendCall.get();
                consecutiveFailures = 0; // success resets the failure count
                return result;
            } catch (RuntimeException e) {
                consecutiveFailures++;
                System.out.println("  [circuit CLOSED] failure " + consecutiveFailures + "/" + failureThreshold);
                if (consecutiveFailures >= failureThreshold) {
                    state = State.OPEN;
                    System.out.println("  [circuit] threshold crossed -- OPENING the circuit");
                }
                return fallback.get();
            }
        }
    }

    static boolean backendIsDown = true;
    static String callBackend() { if (backendIsDown) throw new RuntimeException("backend timeout"); return "200 OK"; }
    static String fallbackResponse() { return "200 OK (fallback: cached data)"; }

    public static void main(String[] args) {
        CircuitBreaker cb = new CircuitBreaker();
        for (int i = 1; i <= 5; i++) {
            System.out.println("Request " + i + ": " + cb.call(CircuitBreakerOpensAndFallsBack::callBackend, CircuitBreakerOpensAndFallsBack::fallbackResponse));
        }
        System.out.println("Requests 3-5 NEVER even attempted the backend call -- instant fallback, sparing both the client's wait AND the struggling backend's load.");
    }
}
```

**How to run:** `javac CircuitBreakerOpensAndFallsBack.java && java CircuitBreakerOpensAndFallsBack` (JDK 17+).

Expected output:
```
  [circuit CLOSED] failure 1/2
Request 1: 200 OK (fallback: cached data)
  [circuit CLOSED] failure 2/2
  [circuit] threshold crossed -- OPENING the circuit
Request 2: 200 OK (fallback: cached data)
  [circuit OPEN] short-circuiting to fallback, NOT calling backend at all
Request 3: 200 OK (fallback: cached data)
  [circuit OPEN] short-circuiting to fallback, NOT calling backend at all
Request 4: 200 OK (fallback: cached data)
  [circuit OPEN] short-circuiting to fallback, NOT calling backend at all
Request 5: 200 OK (fallback: cached data)
Requests 3-5 NEVER even attempted the backend call -- instant fallback, sparing both the client's wait AND the struggling backend's load.
```

### Level 3 — Advanced

```java
// File: HalfOpenRecoveryTest.java -- after a COOLDOWN, the circuit tries a
// LIMITED test call (HALF-OPEN); if it succeeds, the circuit CLOSES again --
// full recovery, detected automatically.
import java.util.function.*;

public class HalfOpenRecoveryTest {
    enum State { CLOSED, OPEN, HALF_OPEN }

    static class CircuitBreaker {
        State state = State.CLOSED;
        int consecutiveFailures = 0;
        int failureThreshold = 2;
        long openedAtMillis;
        long cooldownMillis = 100; // shortened for the demo

        String call(Supplier<String> backendCall, Supplier<String> fallback) {
            if (state == State.OPEN) {
                if (System.currentTimeMillis() - openedAtMillis >= cooldownMillis) {
                    state = State.HALF_OPEN; // cooldown elapsed -- cautiously test recovery
                    System.out.println("  [circuit] cooldown elapsed -- transitioning to HALF_OPEN, allowing ONE test call");
                } else {
                    System.out.println("  [circuit OPEN] still cooling down, short-circuiting to fallback");
                    return fallback.get();
                }
            }
            try {
                String result = backendCall.get(); // in HALF_OPEN, this IS the test call
                if (state == State.HALF_OPEN) {
                    state = State.CLOSED; // test call SUCCEEDED -- fully recovered
                    consecutiveFailures = 0;
                    System.out.println("  [circuit] test call SUCCEEDED -- CLOSING the circuit, backend has recovered");
                }
                return result;
            } catch (RuntimeException e) {
                consecutiveFailures++;
                if (state == State.HALF_OPEN) {
                    state = State.OPEN; // test call FAILED -- back to OPEN, backend still not ready
                    openedAtMillis = System.currentTimeMillis();
                    System.out.println("  [circuit] test call FAILED -- still not recovered, back to OPEN");
                } else if (consecutiveFailures >= failureThreshold) {
                    state = State.OPEN;
                    openedAtMillis = System.currentTimeMillis();
                    System.out.println("  [circuit] threshold crossed -- OPENING the circuit");
                }
                return fallback.get();
            }
        }
    }

    static boolean backendIsDown = true;
    static String callBackend() { if (backendIsDown) throw new RuntimeException("backend timeout"); return "200 OK, genuinely from backend"; }
    static String fallbackResponse() { return "200 OK (fallback: cached data)"; }

    public static void main(String[] args) throws InterruptedException {
        CircuitBreaker cb = new CircuitBreaker();

        for (int i = 1; i <= 2; i++) System.out.println("Request " + i + ": " + cb.call(HalfOpenRecoveryTest::callBackend, HalfOpenRecoveryTest::fallbackResponse));

        Thread.sleep(150); // wait past the cooldown

        backendIsDown = false; // the backend has ACTUALLY recovered by now
        System.out.println("Request 3 (after cooldown, backend RECOVERED): " + cb.call(HalfOpenRecoveryTest::callBackend, HalfOpenRecoveryTest::fallbackResponse));
        System.out.println("Request 4 (circuit fully CLOSED again): " + cb.call(HalfOpenRecoveryTest::callBackend, HalfOpenRecoveryTest::fallbackResponse));
    }
}
```

**How to run:** `javac HalfOpenRecoveryTest.java && java HalfOpenRecoveryTest` (JDK 17+).

Expected output:
```
  [circuit CLOSED] failure 1/2
Request 1: 200 OK (fallback: cached data)
  [circuit CLOSED] failure 2/2
  [circuit] threshold crossed -- OPENING the circuit
Request 2: 200 OK (fallback: cached data)
  [circuit] cooldown elapsed -- transitioning to HALF_OPEN, allowing ONE test call
  [circuit] test call SUCCEEDED -- CLOSING the circuit, backend has recovered
Request 3 (after cooldown, backend RECOVERED): 200 OK, genuinely from backend
Request 4 (circuit fully CLOSED again): 200 OK, genuinely from backend
```

## 6. Walkthrough

1. **Level 1** — every one of the five requests calls `callBackend()` directly, and every single one throws (since `backendIsDown` never changes), meaning each request individually pays whatever cost `"backend timeout after waiting the FULL configured timeout"` represents — nothing about the first failure informed how the subsequent four requests were handled.
2. **Level 2, tracking failures toward a threshold** — `CircuitBreaker.call` increments `consecutiveFailures` on each caught exception while `state == CLOSED`, and checks this count against `failureThreshold` (2) after each failure.
3. **Level 2, the circuit opening** — after the second consecutive failure (request 2), `consecutiveFailures >= failureThreshold` becomes true, setting `state = State.OPEN`; from this point forward, `call`'s very first check (`if (state == State.OPEN)`) short-circuits immediately to `fallback.get()` without ever invoking `backendCall.get()` at all.
4. **Level 2, requests 3 through 5 short-circuiting** — the printed log for these three requests shows only the `"[circuit OPEN] short-circuiting..."` line, with no corresponding failure-counting or backend-invocation log line, directly confirming the backend was never actually called for these requests.
5. **Level 3, the cooldown timer** — `openedAtMillis` records when the circuit opened; each subsequent call while `state == OPEN` checks whether `System.currentTimeMillis() - openedAtMillis >= cooldownMillis` has elapsed, and only transitions to `HALF_OPEN` once that condition is met.
6. **Level 3, the half-open test call** — once in `HALF_OPEN` state, `call` proceeds to actually invoke `backendCall.get()` (unlike the fully-open state's unconditional short-circuit), treating this one call as a deliberate, cautious test of whether the backend has recovered.
7. **Level 3, the successful recovery** — `main` sets `backendIsDown = false` (simulating the backend genuinely coming back online) before the third request, and after `Thread.sleep(150)` has elapsed past the 100ms cooldown, that third request's call correctly transitions to `HALF_OPEN`, attempts the backend call, succeeds, and the `catch` block's absence means the success path executes: `state = State.CLOSED` and `consecutiveFailures = 0` — the fourth request then proceeds through the normal `CLOSED`-state path entirely, confirming the circuit has genuinely and automatically recovered based on the backend's real, observed health, not on any fixed timer alone.

## 7. Gotchas & takeaways

> **Gotcha:** a circuit breaker's fallback response needs to be genuinely useful, or safe, in place of the real backend response — returning stale cached data, a degraded but functional response, or a clear "temporarily unavailable" signal are all reasonable fallback strategies, but a fallback that silently returns incorrect or misleading data (rather than clearly signaling degraded service) can cause worse downstream problems than the original backend failure would have, especially if callers can't distinguish a fallback response from a genuine one.

- Spring Cloud Gateway's Resilience4j-backed circuit breaker filter stops sending traffic to a struggling backend once a failure threshold is crossed, protecting both the backend from continued load and the gateway from resources tied up waiting on calls likely to fail.
- The circuit cycles through three states: closed (normal operation, tracking failures), open (short-circuiting immediately to a fallback, no backend calls attempted), and half-open (a cautious test call after a cooldown, to check for recovery).
- A successful half-open test call closes the circuit, resuming normal traffic; a failed one reopens it, restarting the cooldown.
- This pattern is especially valuable in request aggregation scenarios, where one struggling backend among several shouldn't be allowed to degrade an entire aggregated response's latency.
- The fallback response returned while the circuit is open needs to be genuinely useful or clearly signal degraded service — a misleading fallback can create worse problems than the original failure.
