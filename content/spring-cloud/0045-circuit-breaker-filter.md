---
card: spring-cloud
gi: 45
slug: circuit-breaker-filter
title: "Circuit breaker filter"
---

## 1. What it is

The `CircuitBreaker` GatewayFilter wraps a route's backend call in a circuit breaker (backed by Resilience4j): if the backend fails repeatedly, the circuit "opens" and Gateway stops even attempting to call it for a cooldown period, immediately returning a fallback response instead — protecting both the failing backend from further load and the gateway itself from piling up slow, doomed requests.

```yaml
filters:
  - name: CircuitBreaker
    args:
      name: ordersCircuitBreaker
      fallbackUri: forward:/fallback/orders
```

```java
@RestController
class FallbackController {
    @GetMapping("/fallback/orders")
    Map<String, String> ordersFallback() {
        return Map.of("message", "orders-service is temporarily unavailable, please try again shortly");
    }
}
```

## 2. Why & when

`Retry` (covered earlier) helps with transient, one-off failures, but retrying a backend that's genuinely down or overwhelmed just adds more load to an already-struggling service and makes callers wait through every retry attempt before eventually failing anyway. A circuit breaker instead tracks the failure rate over a rolling window, and once it crosses a threshold, stops sending traffic entirely for a cooldown period — failing fast with an immediate fallback instead of making every caller wait out a doomed call.

Reach for `CircuitBreaker` when:

- A backend's failure could cascade — if it's slow or down, letting every gateway request pile up waiting on it can exhaust gateway resources and take down healthy routes too.
- You want a defined fallback behavior (a cached response, a friendly error, a degraded feature) instead of every caller individually experiencing a raw connection timeout or 5xx error.
- The failure pattern is sustained, not just an isolated blip — circuit breakers and retries are complementary, often used together: retry a handful of times, and if the failure rate stays high across many requests, trip the breaker.

## 3. Core concept

```
 CLOSED (normal):     requests flow through to the backend
        |
        |  failure rate crosses threshold over a rolling window
        v
 OPEN:                requests immediately return the fallback, backend is NOT called at all
        |
        |  after a cooldown period
        v
 HALF_OPEN:           a limited number of trial requests are allowed through
        |
        |-- succeed enough -> back to CLOSED
        |-- still failing   -> back to OPEN, cooldown resets
```

The breaker tracks aggregate health and stops sending traffic the moment it looks bad, rather than letting every individual request discover the failure the hard way.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The circuit breaker cycles between closed, open, and half open states based on the observed failure rate and a cooldown timer">
  <rect x="30" y="20" width="150" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">CLOSED</text>

  <rect x="245" y="20" width="150" height="50" rx="8" fill="#e6494930" stroke="#e64949" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OPEN</text>

  <rect x="460" y="20" width="150" height="50" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="535" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">HALF_OPEN</text>

  <line x1="180" y1="45" x2="243" y2="45" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a45)"/>
  <text x="210" y="35" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">threshold</text>

  <line x1="395" y1="45" x2="458" y2="45" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a45)"/>
  <text x="425" y="35" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">cooldown</text>

  <line x1="535" y1="75" x2="320" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a45)"/>
  <text x="450" y="115" fill="#8b949e" font-size="6.5" font-family="sans-serif">trial fails -&gt; back to OPEN</text>

  <line x1="480" y1="70" x2="140" y2="70" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a45)"/>
  <text x="320" y="90" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">trial succeeds -&gt; back to CLOSED</text>

  <defs><marker id="a45" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The breaker moves between three states based purely on observed outcomes and elapsed cooldown time, never on manual intervention.

## 5. Runnable example

The scenario: protect calls to a flaky `orders-service` with a circuit breaker. Start with an unprotected direct call, then add failure-rate tracking that trips the breaker, then add the half-open trial and recovery cycle.

### Level 1 — Basic

Unprotected calls — every request waits out every failure directly.

```java
import java.util.function.Supplier;

public class CircuitBreakerLevel1 {
    record Response(int status, String body) {}

    static Response callBackend(Supplier<Response> backend) {
        return backend.get(); // no protection at all -- every failure is fully absorbed by the caller
    }

    public static void main(String[] args) {
        int[] callCount = {0};
        Supplier<Response> flakyBackend = () -> {
            callCount[0]++;
            return new Response(503, "Service Unavailable"); // this backend is down, every call fails
        };

        for (int i = 0; i < 5; i++) {
            Response r = callBackend(flakyBackend);
            System.out.println("call " + i + " -> " + r.status());
        }
        System.out.println("total backend calls made: " + callCount[0]); // 5 -- all wasted on a dead backend
    }
}
```

How to run: `java CircuitBreakerLevel1.java`

Every one of the five calls reaches the backend directly, even though it's clearly down after the first failure — no protection, no fallback, and the backend keeps taking traffic it can't serve.

### Level 2 — Intermediate

Add failure-rate tracking over a rolling window, tripping the breaker open once the threshold is crossed.

```java
import java.util.*;
import java.util.function.Supplier;

public class CircuitBreakerLevel2 {
    record Response(int status, String body) {}

    static class CircuitBreaker {
        enum State { CLOSED, OPEN }
        State state = State.CLOSED;
        Deque<Boolean> window = new ArrayDeque<>(); // true = failure, sliding window of recent outcomes
        int windowSize = 5;
        double failureThreshold = 0.5; // trip if >= 50% of the window failed

        Response call(Supplier<Response> backend, Response fallback) {
            if (state == State.OPEN) {
                return fallback; // backend is NOT called at all while open
            }
            Response result = backend.get();
            recordOutcome(result.status() >= 500);
            return result;
        }

        void recordOutcome(boolean failed) {
            window.addLast(failed);
            if (window.size() > windowSize) window.removeFirst();
            if (window.size() == windowSize) {
                long failures = window.stream().filter(b -> b).count();
                if ((double) failures / windowSize >= failureThreshold) {
                    state = State.OPEN;
                    System.out.println("[breaker] threshold crossed -- OPENING circuit");
                }
            }
        }
    }

    public static void main(String[] args) {
        CircuitBreaker breaker = new CircuitBreaker();
        Supplier<Response> flakyBackend = () -> new Response(503, "Service Unavailable");
        Response fallback = new Response(200, "{\"message\":\"temporarily unavailable\"}");

        for (int i = 0; i < 8; i++) {
            Response r = breaker.call(flakyBackend, fallback);
            System.out.println("call " + i + " -> " + r.status() + " (state=" + breaker.state + ")");
        }
    }
}
```

How to run: `java CircuitBreakerLevel2.java`

`recordOutcome` tracks a sliding window of the last 5 outcomes; once the window fills and at least 50% are failures, `state` flips to `OPEN`. From that point on, `call` returns `fallback` immediately without ever invoking `backend.get()` — the backend stops receiving traffic entirely, and every caller after that gets a fast, predictable fallback response instead of a slow failure.

### Level 3 — Advanced

Add the cooldown-driven `HALF_OPEN` recovery cycle: after a cooldown period, allow a trial request through, and either close the circuit (backend recovered) or reopen it (still failing).

```java
import java.util.*;
import java.util.function.Supplier;

public class CircuitBreakerLevel3 {
    record Response(int status, String body) {}

    static class CircuitBreaker {
        enum State { CLOSED, OPEN, HALF_OPEN }
        State state = State.CLOSED;
        Deque<Boolean> window = new ArrayDeque<>();
        int windowSize = 5;
        double failureThreshold = 0.5;
        long openedAtMs = -1;
        long cooldownMs = 1000;

        Response call(Supplier<Response> backend, Response fallback, long nowMs) {
            if (state == State.OPEN) {
                if (nowMs - openedAtMs >= cooldownMs) {
                    state = State.HALF_OPEN;
                    System.out.println("[breaker] cooldown elapsed -- HALF_OPEN, allowing a trial request");
                } else {
                    return fallback;
                }
            }
            if (state == State.HALF_OPEN) {
                Response result = backend.get();
                if (result.status() < 500) {
                    state = State.CLOSED;
                    window.clear();
                    System.out.println("[breaker] trial succeeded -- CLOSING circuit");
                    return result;
                } else {
                    state = State.OPEN;
                    openedAtMs = nowMs;
                    System.out.println("[breaker] trial failed -- back to OPEN, cooldown reset");
                    return fallback;
                }
            }
            Response result = backend.get();
            recordOutcome(result.status() >= 500, nowMs);
            return result;
        }

        void recordOutcome(boolean failed, long nowMs) {
            window.addLast(failed);
            if (window.size() > windowSize) window.removeFirst();
            if (window.size() == windowSize) {
                long failures = window.stream().filter(b -> b).count();
                if ((double) failures / windowSize >= failureThreshold) {
                    state = State.OPEN;
                    openedAtMs = nowMs;
                    System.out.println("[breaker] threshold crossed -- OPENING circuit");
                }
            }
        }
    }

    public static void main(String[] args) {
        CircuitBreaker breaker = new CircuitBreaker();
        Response fallback = new Response(200, "{\"message\":\"temporarily unavailable\"}");
        boolean[] recovered = {false};
        Supplier<Response> backend = () -> recovered[0]
                ? new Response(200, "{\"orderId\":42}")
                : new Response(503, "Service Unavailable");

        for (int i = 0; i < 5; i++) System.out.println("call " + i + " -> " + breaker.call(backend, fallback, i * 100).status());

        recovered[0] = true; // backend comes back to life
        System.out.println("call 5 (t=1600ms) -> " + breaker.call(backend, fallback, 1600).status()); // cooldown elapsed, trial call
    }
}
```

How to run: `java CircuitBreakerLevel3.java`

The first five calls (`t=0` to `t=400`) fill the sliding window with failures and trip the breaker `OPEN` around the fifth call. At `t=1600`, more than the `1000ms` cooldown has passed since the breaker opened, so `call` transitions to `HALF_OPEN` and allows exactly one trial request through — since `recovered[0]` is now `true`, that trial succeeds, and the breaker immediately closes, ready to resume normal traffic.

## 6. Walkthrough

Trace the sequence in Level 3.

1. Calls `0` through `4` run with `recovered[0] = false`, so `backend` always returns `503`. Each call goes through the `state == CLOSED` path (initially), calling `backend.get()` directly and recording the failure via `recordOutcome`. Once the fifth outcome fills the 5-slot window with all failures, the failure ratio (`5/5 = 1.0`) crosses the `0.5` threshold, and `state` flips to `OPEN` with `openedAtMs` set to the current `nowMs`.
2. `recovered[0] = true` runs — this models `orders-service` actually recovering (a restart completes, the dependency it needed comes back), independent of the breaker's own state, which still shows `OPEN` at this point.
3. The final call passes `nowMs = 1600`. `call` checks `state == OPEN`, computes `1600 - openedAtMs`, and since that's `>= 1000` (the cooldown), transitions to `HALF_OPEN` and prints the transition message.
4. Still inside the same `call` invocation, the `state == HALF_OPEN` branch now runs: it invokes `backend.get()` for a single trial request. Because `recovered[0]` is `true`, this returns `200`, which is `< 500`, so the breaker sets `state = CLOSED`, clears the failure window, prints the recovery message, and returns the successful `200` response directly to the caller — the very first real traffic to reach the backend since the breaker opened.

```
calls 0-4: backend down -> window fills with failures -> OPEN at call 4
   (calls after that, before t=1600, would all hit the fallback immediately)

t=1600: cooldown (1000ms) has elapsed since opening
   -> HALF_OPEN -> one trial call allowed through
   -> backend has recovered -> trial succeeds -> CLOSED
```

## 7. Gotchas & takeaways

> **Gotcha:** while `HALF_OPEN`, only a limited number of trial requests are allowed through (this example uses just one) — if many concurrent requests arrive during that window, letting all of them through as "trials" defeats the purpose (a still-struggling backend gets hit with a burst right as it's trying to recover). Real circuit breaker implementations cap the number of concurrent trial calls explicitly.

- A circuit breaker fails fast once it's confident the backend is unhealthy, sparing both the backend from pointless additional load and callers from waiting out doomed requests one at a time.
- `Retry` and `CircuitBreaker` are complementary, not redundant — retry absorbs brief, isolated blips; the circuit breaker protects against sustained failure across many requests.
- The `fallbackUri` should return something genuinely useful to the caller (a cached value, a clear "try again shortly" message) rather than just another generic error — it's the difference callers actually experience during an outage.
- Circuit breaker thresholds (window size, failure ratio, cooldown duration) are workload-specific tuning — too sensitive and normal traffic blips trip it unnecessarily; too lax and it fails to protect a genuinely struggling backend in time.
