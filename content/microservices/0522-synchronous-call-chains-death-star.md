---
card: microservices
gi: 522
slug: synchronous-call-chains-death-star
title: "Synchronous call chains (death star)"
---

## 1. What it is

A **synchronous call chain** (often nicknamed a "death star" when drawn out, because the resulting diagram of every service calling several others synchronously looks like a dense, radiating mesh) is what happens when a single incoming request triggers a long sequence of blocking, waits-for-the-answer calls through many services before a response can be returned. Service A calls B, which calls C, which calls D — each one blocking until the next responds — so the total response time is the *sum* of every hop's latency, and a failure anywhere in the chain fails the entire request.

## 2. Why & when

You watch for synchronous call chains because their cost compounds invisibly as a system grows, one reasonable-looking call at a time:

- **Latency adds up linearly with chain depth.** If each hop takes 50ms, a chain four services deep costs at least 200ms before any single service has done anything slow — and that's the *best* case, assuming nothing in the chain is under load or momentarily degraded.
- **Availability multiplies, not adds, in the wrong direction.** If each service in a four-deep chain is independently 99.9% available, the *chain's* effective availability is roughly 0.999^4 ≈ 99.6% — worse than any single link, because the whole chain fails if *any* link fails. Depth directly erodes availability, even when every individual service is healthy on its own.
- **It creates a hidden dependency graph that's hard to reason about.** A team owning Service A may not realize a request to their service ultimately depends on Service D's health three hops away, until D has an incident and A's on-call is paged for an outage they can't explain from A's own code.
- **The fix is usually one of: breaking the chain with asynchronous messaging** (A publishes an event, D reacts later, instead of A waiting for D's answer), **caching** (so a hop doesn't need to happen at all for most requests), or **restructuring so the caller gathers data in parallel rather than nested sequentially**, when all the data really is needed synchronously.

## 3. Core concept

Think of a customer support call that gets transferred from agent to agent to agent, each one saying "let me check with someone else" and putting the customer on hold while they do — the customer's total wait time is the sum of every transfer's hold time, and if any one of those agents is unavailable, the whole call stalls entirely, even though the first three agents did their part fine. A well-designed process either resolves the call at the first point of contact (caching/local data), or gathers input from several colleagues in parallel while the customer waits once (parallel calls instead of nested sequential ones), rather than chaining transfers one after another.

Concretely:

1. **A synchronous call chain's response time is bounded below by the sum of every hop's latency** — even if every service is perfectly healthy, depth alone imposes a latency floor that no amount of per-service optimization can beat, only removing hops can.
2. **A synchronous call chain's availability is bounded above by the product of every hop's availability** — a chain is only as reliable as *all* of its links combined, which is always worse than its weakest single link.
3. **Depth is often invisible from any single service's code** — each individual call in the chain looks like a normal, reasonable dependency; the compounding cost only becomes visible when you trace the full path a request actually takes end to end.
4. **The structural fixes are: shorten the chain** (does D's answer really need to block A's response, or can A respond and let D's result arrive asynchronously later), **flatten nested sequential calls into parallel ones** (if B and C don't depend on each other, call them concurrently instead of B-then-C), **or remove hops via caching** (serve D's answer from a cache A already has, skipping the live call entirely).

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A synchronous call chain of depth four adds latency at each hop and multiplies availability risk down the chain">
  <rect x="20" y="30" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="80" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">A (gateway)</text>
  <rect x="180" y="30" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="240" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">B</text>
  <rect x="340" y="30" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="400" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">C</text>
  <rect x="500" y="30" width="120" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="560" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">D (flaky today)</text>

  <line x1="140" y1="50" x2="180" y2="50" stroke="#8b949e" marker-end="url(#a3)"/>
  <line x1="300" y1="50" x2="340" y2="50" stroke="#8b949e" marker-end="url(#a3)"/>
  <line x1="460" y1="50" x2="500" y2="50" stroke="#8b949e" marker-end="url(#a3)"/>

  <text x="330" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">latency: 50ms + 50ms + 50ms = 150ms minimum, every request</text>
  <text x="330" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">availability: 0.999 x 0.999 x 0.995(D) = ~99.3% -- worse than any one link</text>
  <text x="330" y="160" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">D having a bad day fails EVERY request through A, B, and C too</text>

  <defs><marker id="a3" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

Each hop in a synchronous chain adds to latency and multiplies availability risk; the chain is never faster or more reliable than the sum/product of its parts.

## 5. Runnable example

Scenario: a checkout gateway that needs order validation, pricing, and shipping-estimate data. We start with a deep nested synchronous chain, extend it to flatten independent calls into parallel ones, then handle the hard case: breaking the chain further by making the non-critical hop asynchronous, so its failure doesn't fail checkout at all.

### Level 1 — Basic

```java
// File: DeathStarChain.java -- a DEEP, NESTED synchronous chain:
// Gateway -> Validation -> Pricing -> Shipping, each blocking on the next.
public class DeathStarChain {
    static int callLatencyMs(String service) { return 50; } // simulated per-hop latency

    static String shipping(String orderId) throws InterruptedException {
        Thread.sleep(callLatencyMs("shipping"));
        return "shipping-estimate:3days";
    }
    static String pricing(String orderId) throws InterruptedException {
        Thread.sleep(callLatencyMs("pricing"));
        String shippingResult = shipping(orderId); // NESTED call: pricing waits on shipping
        return "price:$42.00," + shippingResult;
    }
    static String validation(String orderId) throws InterruptedException {
        Thread.sleep(callLatencyMs("validation"));
        String pricingResult = pricing(orderId); // NESTED call: validation waits on pricing (which waits on shipping)
        return "valid:true," + pricingResult;
    }
    static String gateway(String orderId) throws InterruptedException {
        return validation(orderId); // gateway waits on the ENTIRE chain beneath it
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        System.out.println(gateway("order-42"));
        System.out.println("Total: " + (System.currentTimeMillis() - start) + "ms (3 sequential hops: validation -> pricing -> shipping)");
    }
}
```

How to run: `java DeathStarChain.java`

Each function calls the next and waits for its result before returning its own — `gateway` waits on `validation`, which waits on `pricing`, which waits on `shipping`. Total time is the sum of all three simulated hops (~150ms), and if `shipping` were unavailable, `pricing`, `validation`, and `gateway` would all fail too, even though pricing and validation logic themselves are perfectly fine.

### Level 2 — Intermediate

```java
// File: FlattenedParallel.java -- pricing and shipping don't actually
// depend on EACH OTHER'S result, only on the order ID -- so call them
// IN PARALLEL instead of nesting one inside the other.
import java.util.concurrent.*;

public class FlattenedParallel {
    static String validation(String orderId) throws InterruptedException {
        Thread.sleep(50);
        return "valid:true";
    }
    static CompletableFuture<String> pricingAsync(String orderId) {
        return CompletableFuture.supplyAsync(() -> { sleep(50); return "price:$42.00"; });
    }
    static CompletableFuture<String> shippingAsync(String orderId) {
        return CompletableFuture.supplyAsync(() -> { sleep(50); return "shipping-estimate:3days"; });
    }
    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { throw new RuntimeException(e); } }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        String validationResult = validation("order-42"); // still sequential: must happen first
        CompletableFuture<String> pricingFuture = pricingAsync("order-42");   // fired concurrently
        CompletableFuture<String> shippingFuture = shippingAsync("order-42"); // fired concurrently
        String result = validationResult + "," + pricingFuture.get() + "," + shippingFuture.get();
        System.out.println(result);
        System.out.println("Total: " + (System.currentTimeMillis() - start) + "ms (validation THEN pricing+shipping in parallel)");
    }
}
```

How to run: `java FlattenedParallel.java`

Since pricing and shipping don't depend on each other, they're launched concurrently via `CompletableFuture`, rather than nested inside each other. Total time drops to roughly 100ms (50ms validation + 50ms for pricing/shipping running concurrently), instead of Level 1's 150ms — the chain depth is unchanged for validation, but pricing and shipping no longer add to each other's latency.

### Level 3 — Advanced

```java
// File: AsyncNonCritical.java -- shipping estimate is NICE TO HAVE, not
// required for checkout to succeed -- make it fully asynchronous so its
// failure or slowness NEVER blocks or fails the checkout response.
import java.util.concurrent.*;

public class AsyncNonCritical {
    static String validation(String orderId) { sleep(50); return "valid:true"; }
    static CompletableFuture<String> pricingAsync(String orderId) {
        return CompletableFuture.supplyAsync(() -> { sleep(50); return "price:$42.00"; })
            .orTimeout(300, TimeUnit.MILLISECONDS);
    }
    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { throw new RuntimeException(e); } }

    // shipping is fire-and-forget: checkout does NOT wait for it, and its result
    // (or failure) is delivered later via a callback/event, never on checkout's critical path
    static void publishShippingEstimateRequestAsync(String orderId) {
        CompletableFuture.runAsync(() -> {
            sleep(2000); // simulate a slow or flaky shipping service -- completely irrelevant to checkout now
            System.out.println("[async] shipping estimate for " + orderId + " ready (delivered via event later, not blocking checkout)");
        });
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        String validationResult = validation("order-42");
        String pricingResult = pricingAsync("order-42").get();
        publishShippingEstimateRequestAsync("order-42"); // NOT awaited -- checkout proceeds without it
        System.out.println("Checkout response: " + validationResult + "," + pricingResult + ",shipping:pending");
        System.out.println("Checkout total: " + (System.currentTimeMillis() - start) + "ms -- shipping's 2000ms never touched this");
    }
}
```

How to run: `java AsyncNonCritical.java`

`publishShippingEstimateRequestAsync` is called but never `.get()`-ed or awaited — checkout's response is built and returned using only `validation` and `pricing`'s results, completing in roughly 100ms regardless of how long the shipping estimate actually takes (simulated here as 2000ms, dramatically slower than everything else). The shipping estimate still completes eventually and prints its own message, but on its own time, fully decoupled from checkout's response — checkout's chain has been shortened from three hops to two, with the third demoted to a background concern.

## 6. Walkthrough

Trace `AsyncNonCritical.main` end to end:

1. **`validation("order-42")` runs synchronously**, sleeping 50ms and returning `"valid:true"` — this remains on the critical path because checkout genuinely cannot proceed without knowing the order is valid.
2. **`pricingAsync("order-42").get()` runs next**, submitting the pricing work and immediately blocking on `.get()` (with a 300ms safety timeout) — pricing also remains on the critical path, since checkout needs a price to confirm.
3. **`publishShippingEstimateRequestAsync("order-42")` is called**, which submits a background task via `runAsync` and returns *immediately* without any `.get()` or `.join()` — `main` does not wait for this call at all.
4. **`main` immediately proceeds to build and print the checkout response**, using only `validationResult` and `pricingResult` — the response explicitly reports `shipping:pending` rather than a real estimate, an honest reflection that this data isn't available yet.
5. **`main` prints the total elapsed time**, roughly 100ms — the sum of validation (50ms) and pricing (50ms), completely unaffected by the shipping task's 2000ms simulated duration, because that task is running independently in the background.
6. **Roughly 2000ms later, the background task completes** and prints its own message, entirely disconnected from the checkout response that was already returned to the caller ~1900ms earlier. In a real system, this would deliver its result via an event, webhook, or a later poll/update to the order record — the customer's checkout confirmation isn't held hostage waiting for it.

Contrast the total shape with Level 1: Level 1's `gateway` call couldn't return until all three hops finished, sequentially, and any hop's failure would have failed the whole request. Here, checkout's response depends on exactly two hops, and the third hop's slowness (or even outright failure) has zero effect on checkout succeeding or on how fast it succeeds.

## 7. Gotchas & takeaways

> **Gotcha:** flattening nested calls into parallel calls (Level 2) reduces latency but does *not* fix the availability multiplication problem — if shipping is required for the response to be considered valid, shipping being down still fails checkout, just as fast as before; only demoting a hop to genuinely non-critical and asynchronous (Level 3) removes it from the failure chain entirely.

- A synchronous chain's latency floor is the sum of every hop's latency, and its availability ceiling is the product of every hop's availability — depth alone costs you on both axes, regardless of how healthy each individual service is.
- Before assuming two calls must be sequential, check whether one actually depends on the other's *result* — if not, running them in parallel is a free latency win with no correctness risk.
- The real fix for a genuinely non-critical dependency is to remove it from the synchronous path entirely — asynchronous, fire-and-forget, event-driven — not just to make the synchronous call faster or run it in parallel.
- Draw out the actual call graph a request traverses, not just the calls your own service makes directly — "death star" coupling is invisible from inside any single service and only shows up when you trace the full depth end to end.
