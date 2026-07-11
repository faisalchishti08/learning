---
card: spring-cloud
gi: 64
slug: feign-circuit-breaker-fallbacks
title: "Feign + Circuit Breaker fallbacks"
---

## 1. What it is

Feign integrates directly with Resilience4j circuit breakers (the same underlying mechanism as the Gateway `CircuitBreaker` filter, covered earlier): setting `spring.cloud.openfeign.circuitbreaker.enabled=true` wraps every method call on a Feign client in a circuit breaker, and a `fallback` class implementing the same client interface supplies a default response whenever the circuit is open or the real call fails.

```java
@FeignClient(name = "billing-service", fallback = BillingClientFallback.class)
public interface BillingClient {
    @GetMapping("/invoices/{id}")
    Invoice getInvoice(@PathVariable String id);
}

@Component
class BillingClientFallback implements BillingClient {
    @Override
    public Invoice getInvoice(String id) {
        return new Invoice(id, 0.0); // degraded default, returned when billing-service is unavailable
    }
}
```

## 2. Why & when

The Gateway-level `CircuitBreaker` filter (covered earlier) protects the gateway's routing layer; this card is the client-side counterpart — protecting *any* code that calls another service through Feign, not just traffic passing through a gateway. Wrapping a Feign client in a circuit breaker means a struggling `billing-service` doesn't cascade into every caller hanging or failing outright; instead, calls fail fast once the breaker opens, and the fallback supplies a reasonable default so the calling code can often continue functioning in a degraded, but not fully broken, state.

Reach for Feign circuit breaker fallbacks when:

- A downstream service's occasional unavailability shouldn't take down the calling service entirely — a sensible default (cached data, a neutral value, an empty result) lets the caller degrade gracefully instead of failing every dependent operation.
- The calling code's own callers (or a UI) can meaningfully handle a degraded response — showing "price unavailable" instead of crashing an entire page is a real, common product design choice this pattern supports directly.
- You want the same resilience benefits the Gateway `CircuitBreaker` filter provides, but for calls made directly between services rather than calls passing through a gateway.

## 3. Core concept

```
 billingClient.getInvoice(id)
        |
        v
 circuit breaker wraps the call
        |
    CLOSED -> call billing-service directly -> success or failure recorded
        |
    OPEN (too many recent failures) -> skip the real call entirely -> use fallback immediately
        |
    HALF_OPEN (cooldown elapsed) -> allow a trial call -> close or reopen based on its result
        |
 either the real response OR the fallback's response is returned -- same method signature either way
```

The calling code never needs to know which path was taken — both the real call and the fallback satisfy the exact same interface.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Feign client call is wrapped in a circuit breaker that either forwards to the real backend when closed or returns the fallback implementation's response when open, transparently to the caller">
  <rect x="20" y="70" width="170" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billingClient.getInvoice(id)</text>

  <rect x="250" y="60" width="150" height="60" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">circuit breaker</text>
  <text x="325" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">CLOSED / OPEN / HALF_OPEN</text>

  <rect x="460" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="535" y="41" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">real billing-service</text>

  <rect x="460" y="130" width="150" height="34" rx="6" fill="#e6494930" stroke="#e64949" stroke-width="1.2"/>
  <text x="535" y="151" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">BillingClientFallback</text>

  <line x1="190" y1="90" x2="248" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a64)"/>
  <line x1="400" y1="75" x2="458" y2="40" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a64)"/>
  <line x1="400" y1="105" x2="458" y2="145" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a64)"/>

  <defs><marker id="a64" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Whichever path the breaker takes, the caller receives a value satisfying the exact same interface contract — no special-casing needed at the call site.

## 5. Runnable example

The scenario: protect `BillingClient.getInvoice` with a circuit breaker and fallback. Start with an unprotected client (failures propagate directly), then add the fallback mechanism, then add the full circuit breaker state machine deciding when to use it.

### Level 1 — Basic

Unprotected: a failure propagates directly to the caller.

```java
public class FeignFallbackLevel1 {
    record Invoice(String id, double amount) {}

    interface BillingClient {
        Invoice getInvoice(String id);
    }

    static BillingClient realClient = id -> { throw new RuntimeException("billing-service is down"); };

    public static void main(String[] args) {
        try {
            Invoice invoice = realClient.getInvoice("42");
            System.out.println(invoice);
        } catch (RuntimeException e) {
            System.out.println("caller sees a raw failure: " + e.getMessage());
        }
    }
}
```

How to run: `java FeignFallbackLevel1.java`

Without any protection, the calling code must handle a raw exception directly — every caller of `getInvoice` has to decide what to do about `billing-service` being down, individually and repeatedly.

### Level 2 — Intermediate

Add a fallback implementation of the same interface, used whenever the real call fails.

```java
public class FeignFallbackLevel2 {
    record Invoice(String id, double amount) {}

    interface BillingClient {
        Invoice getInvoice(String id);
    }

    static BillingClient realClient = id -> { throw new RuntimeException("billing-service is down"); };

    static BillingClient fallback = id -> new Invoice(id, 0.0); // degraded default -- same interface

    static BillingClient withFallback(BillingClient real, BillingClient fallback) {
        return id -> {
            try {
                return real.getInvoice(id);
            } catch (RuntimeException e) {
                System.out.println("[fallback] real call failed (" + e.getMessage() + "), using fallback");
                return fallback.getInvoice(id);
            }
        };
    }

    public static void main(String[] args) {
        BillingClient protectedClient = withFallback(realClient, fallback);
        Invoice invoice = protectedClient.getInvoice("42"); // never throws -- always gets SOME Invoice back
        System.out.println("caller received: " + invoice);
    }
}
```

How to run: `java FeignFallbackLevel2.java`

`withFallback` wraps `realClient`, catching any exception and delegating to `fallback` instead — the calling code now always receives a valid `Invoice`, either the real one or the degraded default, and never has to handle a raw exception from this call at all.

### Level 3 — Advanced

Add the full circuit breaker state machine deciding when to bypass the real call entirely (once it's clearly failing repeatedly) versus still attempting it — combining this card's fallback mechanism with the earlier circuit breaker card's state machine.

```java
import java.util.*;

public class FeignFallbackLevel3 {
    record Invoice(String id, double amount) {}

    interface BillingClient { Invoice getInvoice(String id); }

    static BillingClient fallback = id -> new Invoice(id, 0.0);

    static class CircuitBreaker {
        enum State { CLOSED, OPEN, HALF_OPEN }
        State state = State.CLOSED;
        Deque<Boolean> window = new ArrayDeque<>();
        int windowSize = 3;
        double failureThreshold = 0.6;
        long openedAtMs = -1;
        long cooldownMs = 500;

        Invoice call(String id, BillingClient real, long nowMs) {
            if (state == State.OPEN) {
                if (nowMs - openedAtMs >= cooldownMs) { state = State.HALF_OPEN; }
                else { System.out.println("[breaker OPEN] skipping real call, using fallback directly"); return fallback.getInvoice(id); }
            }
            try {
                Invoice result = real.getInvoice(id);
                recordOutcome(false, nowMs);
                if (state == State.HALF_OPEN) { state = State.CLOSED; window.clear(); System.out.println("[breaker] trial succeeded -- CLOSED"); }
                return result;
            } catch (RuntimeException e) {
                recordOutcome(true, nowMs);
                if (state == State.HALF_OPEN) { state = State.OPEN; openedAtMs = nowMs; System.out.println("[breaker] trial failed -- back to OPEN"); }
                System.out.println("[breaker] real call failed, using fallback");
                return fallback.getInvoice(id);
            }
        }

        void recordOutcome(boolean failed, long nowMs) {
            window.addLast(failed);
            if (window.size() > windowSize) window.removeFirst();
            if (window.size() == windowSize) {
                long failures = window.stream().filter(b -> b).count();
                if ((double) failures / windowSize >= failureThreshold && state == State.CLOSED) {
                    state = State.OPEN; openedAtMs = nowMs;
                    System.out.println("[breaker] threshold crossed -- OPENING");
                }
            }
        }
    }

    public static void main(String[] args) {
        boolean[] serviceDown = {true};
        BillingClient realClient = id -> {
            if (serviceDown[0]) throw new RuntimeException("billing-service is down");
            return new Invoice(id, 199.99);
        };

        CircuitBreaker breaker = new CircuitBreaker();
        for (int i = 0; i < 3; i++) System.out.println("call " + i + " -> " + breaker.call("42", realClient, i * 100));

        // this call arrives while OPEN and within cooldown -- fallback used WITHOUT even attempting the real call
        System.out.println("call 3 -> " + breaker.call("42", realClient, 350));

        serviceDown[0] = false; // service recovers
        System.out.println("call 4 (t=700ms, cooldown elapsed) -> " + breaker.call("42", realClient, 700));
    }
}
```

How to run: `java FeignFallbackLevel3.java`

The first three calls fail (service down), tripping the breaker `OPEN`. The fourth call, while still within the cooldown window, skips the real call entirely and goes straight to the fallback — no wasted attempt against a service already known to be failing. The final call, after the cooldown has elapsed and the service has genuinely recovered, triggers a `HALF_OPEN` trial that succeeds, closing the breaker and returning the real `Invoice` again.

## 6. Walkthrough

Trace the calls in Level 3.

1. Calls `0` through `2` (at `t=0, 100, 200`) each invoke `breaker.call`, which is currently `CLOSED`, so each attempts `real.getInvoice("42")` directly. Since `serviceDown[0]` is `true`, each throws, caught by the `catch` block, which calls `recordOutcome(true, nowMs)` and returns `fallback.getInvoice("42")`. After the third failure, `recordOutcome` finds the 3-slot window full of failures (`3/3 = 1.0 >= 0.6`), tripping `state` to `OPEN`.
2. The fourth call (`t=350`) finds `state == OPEN`; it checks `350 - openedAtMs < 500` (the cooldown hasn't elapsed yet, since the breaker just opened around `t=200`), so it prints the "skipping real call" message and returns `fallback.getInvoice("42")` directly — `real.getInvoice` is never even attempted this time, sparing the already-struggling service another doomed request.
3. Before the fifth call, `serviceDown[0] = false` runs — the service has genuinely recovered, independent of the breaker's own state, which is still `OPEN`.
4. The fifth call (`t=700`) finds `state == OPEN` and checks `700 - openedAtMs >= 500` — enough time has passed, so it transitions to `HALF_OPEN`. Falling through to the `try` block, it calls `real.getInvoice("42")`, which now succeeds (the service is back). `recordOutcome(false, 700)` records success, and since `state == HALF_OPEN`, it closes the breaker, printing the recovery message, and returns the genuine `Invoice("42", 199.99)`.

```
calls 0-2: service down -> failures recorded -> breaker OPENS after call 2
call 3 (t=350, still in cooldown): OPEN -> fallback used directly, real call skipped entirely
call 4 (t=700, cooldown elapsed): OPEN -> HALF_OPEN trial -> service recovered -> succeeds -> CLOSED
```

## 7. Gotchas & takeaways

> **Gotcha:** the fallback class must implement the *entire* Feign client interface, not just the method that's failing — if `BillingClient` has five methods and only `getInvoice` typically fails, `BillingClientFallback` still needs reasonable implementations for all five, or calls to the others through the fallback path throw `UnsupportedOperationException`-style errors instead of degrading gracefully.

- Feign's circuit breaker integration is the client-side, per-call-site counterpart to the Gateway `CircuitBreaker` filter — same underlying Resilience4j mechanism, applied at a different layer of the system.
- A well-designed fallback returns something genuinely useful to the caller — a cached last-known value, a sensible default, an explicitly "unavailable" marker the UI can render meaningfully — not just null or a generic empty object that might silently propagate as if it were real data.
- The fallback interface constraint (implementing the full client interface) is a real design cost — it's worth asking, for each Feign client, whether every method genuinely needs (or can sensibly have) a fallback, or whether some should simply propagate the failure.
- `spring.cloud.openfeign.circuitbreaker.enabled=true` is an application-wide switch; per-client fallback classes are then opt-in via the `fallback` attribute on each `@FeignClient` that wants one — clients without a configured fallback still get circuit breaker protection, just without a graceful degraded response.
