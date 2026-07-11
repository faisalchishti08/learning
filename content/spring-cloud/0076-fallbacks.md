---
card: spring-cloud
gi: 76
slug: fallbacks
title: "Fallbacks"
---

## 1. What it is

A fallback is the value or behavior substituted in when a protected call doesn't succeed — whether it failed outright, tripped a circuit breaker, was rejected by a bulkhead or rate limiter, or ran past a time limiter's deadline. Every resilience pattern in this section (circuit breaker, bulkhead, rate limiter, retry, time limiter) can terminate in the same place: a fallback function that turns "this didn't work" into a usable result, and Resilience4j lets these patterns be composed together so one shared fallback handles failure from any of them.

```java
CircuitBreaker cb = circuitBreakerFactory.create("billing-service");

Invoice invoice = cb.run(
    () -> withBulkheadAndRetry(() -> billingClient.getInvoice(orderId)), // the protected operation, possibly itself wrapped
    throwable -> {
        if (throwable instanceof BulkheadFullException) return cachedInvoiceOrDefault(orderId);
        if (throwable instanceof TimeoutException) return new Invoice(orderId, 0.0);
        return new Invoice(orderId, 0.0); // generic degraded default for everything else
    }
);
```

## 2. Why & when

Individual cards in this section covered fallbacks in their own specific context — a circuit breaker's fallback, a Feign fallback class, a time limiter's fallback function. This card is about fallback design as its own discipline, applicable regardless of which resilience pattern triggered it: what makes a *good* fallback, how to distinguish failure causes within one fallback function, and how composed protection (several patterns wrapping the same call) still resolves to one coherent fallback behavior.

Think carefully about fallback design when:

- A fallback that returns misleadingly "normal-looking" data (silently returning `0.0` for a price, say) can cause worse downstream problems than an explicit failure would have — sometimes the right fallback is an explicit "unavailable" signal, not a fabricated value.
- Multiple resilience patterns protect the same call (bulkhead + circuit breaker + retry, a common real combination) — the fallback function needs to handle whichever one actually triggered, ideally distinguishing them via exception type rather than treating every failure identically.
- A cached last-known-good value is available — often a substantially better fallback than either a hardcoded default or an error, since it reflects real (if potentially stale) data rather than an invented stand-in.

## 3. Core concept

```
 protected call fails for ANY reason:
   - circuit breaker OPEN         -> CallNotPermittedException
   - bulkhead full                -> BulkheadFullException
   - rate limiter exhausted       -> RequestNotPermitted
   - time limiter deadline passed -> TimeoutException
   - the call itself threw        -> whatever exception the operation actually raised

 ALL of these funnel into the SAME fallback function
 a well-designed fallback distinguishes them (via exception type) rather than treating every failure identically
```

One fallback function, one place to decide how each *kind* of failure should degrade — not a single, undifferentiated "something went wrong" response.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Several different resilience patterns protecting the same call can each fail for a different reason, and all of those distinct failure types funnel into one shared fallback function that can distinguish and respond to each appropriately">
  <rect x="20" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="90" y="41" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">circuit breaker OPEN</text>

  <rect x="180" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="250" y="41" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">bulkhead full</text>

  <rect x="340" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="410" y="41" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">time limiter timeout</text>

  <rect x="500" y="20" width="120" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="560" y="41" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">real call threw</text>

  <line x1="90" y1="54" x2="280" y2="100" stroke="#8b949e" stroke-width="1"/>
  <line x1="250" y1="54" x2="290" y2="100" stroke="#8b949e" stroke-width="1"/>
  <line x1="410" y1="54" x2="330" y2="100" stroke="#8b949e" stroke-width="1"/>
  <line x1="560" y1="54" x2="350" y2="100" stroke="#8b949e" stroke-width="1"/>

  <rect x="220" y="105" width="200" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="125" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">fallback function</text>
  <text x="320" y="140" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">inspect exception type, respond appropriately</text>

  <defs><marker id="a76" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every distinct way a protected call can fail converges on one fallback function, which can (and should) tell them apart.

## 5. Runnable example

The scenario: design a fallback for `getInvoice` that handles multiple distinct failure causes appropriately. Start with a single generic fallback (no distinction), then differentiate by exception type, then add a cached-value fallback that's genuinely better than a fabricated default.

### Level 1 — Basic

A single, undifferentiated fallback — every failure gets the exact same treatment.

```java
import java.util.function.Function;

public class FallbacksLevel1 {
    record Invoice(String id, double amount) {}

    static class BulkheadFullException extends RuntimeException { BulkheadFullException() { super("bulkhead full"); } }
    static class TimeoutException extends RuntimeException { TimeoutException() { super("timed out"); } }

    static Function<Throwable, Invoice> genericFallback = throwable -> new Invoice("unknown", 0.0);

    public static void main(String[] args) {
        Invoice fromBulkheadFailure = genericFallback.apply(new BulkheadFullException());
        Invoice fromTimeout = genericFallback.apply(new TimeoutException());

        System.out.println("bulkhead failure fallback: " + fromBulkheadFailure);
        System.out.println("timeout fallback: " + fromTimeout);
        // identical output for two VERY different underlying problems
    }
}
```

How to run: `java FallbacksLevel1.java`

Both failure causes produce the exact same fallback response — a bulkhead rejection (this application is overloaded) and a timeout (the dependency is slow) are treated identically, losing information that could have driven a more appropriate response to each.

### Level 2 — Intermediate

Differentiate the fallback by exception type, responding appropriately to each distinct failure cause.

```java
import java.util.function.Function;

public class FallbacksLevel2 {
    record Invoice(String id, double amount, String status) {}

    static class BulkheadFullException extends RuntimeException { BulkheadFullException() { super("bulkhead full"); } }
    static class TimeoutException extends RuntimeException { TimeoutException() { super("timed out"); } }
    static class InvoiceNotFoundException extends RuntimeException { InvoiceNotFoundException() { super("not found"); } }

    static Function<Throwable, Invoice> differentiatedFallback = throwable -> {
        if (throwable instanceof InvoiceNotFoundException) {
            return new Invoice("unknown", 0.0, "NOT_FOUND"); // a genuine business fact, not a system failure
        }
        if (throwable instanceof BulkheadFullException || throwable instanceof TimeoutException) {
            return new Invoice("unknown", -1.0, "TEMPORARILY_UNAVAILABLE"); // system overload/slowness -- try again later
        }
        return new Invoice("unknown", -1.0, "UNKNOWN_ERROR");
    };

    public static void main(String[] args) {
        System.out.println(differentiatedFallback.apply(new InvoiceNotFoundException()));
        System.out.println(differentiatedFallback.apply(new BulkheadFullException()));
        System.out.println(differentiatedFallback.apply(new TimeoutException()));
    }
}
```

How to run: `java FallbacksLevel2.java`

`differentiatedFallback` now inspects the actual exception type and returns a `status` field distinguishing a genuine "not found" business outcome from a "temporarily unavailable" system-level failure — the calling UI or downstream logic can meaningfully react differently to each (show "no such invoice" versus "try again shortly"), instead of collapsing every failure into an indistinguishable generic response.

### Level 3 — Advanced

Add a cached-value fallback: when the failure is system-level (not a genuine "not found"), check a local cache for a recent, real value before falling back to a fabricated default — a substantially better degraded experience than always inventing a substitute value.

```java
import java.util.*;
import java.util.function.Function;

public class FallbacksLevel3 {
    record Invoice(String id, double amount, String status) {}

    static class BulkheadFullException extends RuntimeException { BulkheadFullException() { super("bulkhead full"); } }
    static class TimeoutException extends RuntimeException { TimeoutException() { super("timed out"); } }
    static class InvoiceNotFoundException extends RuntimeException { InvoiceNotFoundException() { super("not found"); } }

    static Map<String, Invoice> localCache = new HashMap<>(Map.of(
            "42", new Invoice("42", 199.99, "CACHED") // a real value seen on a previous successful call
    ));

    static Function<String, Function<Throwable, Invoice>> cacheAwareFallback = requestedId -> throwable -> {
        if (throwable instanceof InvoiceNotFoundException) {
            return new Invoice(requestedId, 0.0, "NOT_FOUND");
        }
        // system-level failure -- prefer a real cached value over a fabricated one, if we have one
        Invoice cached = localCache.get(requestedId);
        if (cached != null) {
            System.out.println("[fallback] using cached value for " + requestedId + " instead of a fabricated default");
            return cached;
        }
        return new Invoice(requestedId, -1.0, "TEMPORARILY_UNAVAILABLE"); // no cache available -- genuinely degraded
    };

    public static void main(String[] args) {
        // invoice 42 has a cached value from a prior successful call -- system failure should use it
        System.out.println(cacheAwareFallback.apply("42").apply(new TimeoutException()));

        // invoice 999 was never successfully fetched before -- no cache available, genuinely degraded
        System.out.println(cacheAwareFallback.apply("999").apply(new BulkheadFullException()));
    }
}
```

How to run: `java FallbacksLevel3.java`

For invoice `"42"`, the fallback finds a real cached value (from some earlier successful call) and returns it directly, marked `"CACHED"` — the caller gets genuinely accurate (if potentially slightly stale) data instead of an invented substitute, a meaningfully better degraded experience. For invoice `"999"`, which has no cache entry, the fallback correctly falls through to the honest `"TEMPORARILY_UNAVAILABLE"` response, since there's no real data to offer instead.

## 6. Walkthrough

Trace both calls in Level 3.

1. `cacheAwareFallback.apply("42").apply(new TimeoutException())` runs first — `cacheAwareFallback.apply("42")` returns a `Function<Throwable, Invoice>` closed over `requestedId = "42"`. That function is then applied to a `TimeoutException`. The `instanceof InvoiceNotFoundException` check fails (it's a `TimeoutException`), so execution falls through to the cache lookup: `localCache.get("42")` finds the pre-populated entry, prints the "using cached value" message, and returns it directly.
2. `cacheAwareFallback.apply("999").apply(new BulkheadFullException())` runs next — same structure, `requestedId = "999"` this time. The `instanceof` check again fails (it's a `BulkheadFullException`). `localCache.get("999")` returns `null`, since no prior successful call ever cached anything for that ID. The method falls through to the final line, returning `new Invoice("999", -1.0, "TEMPORARILY_UNAVAILABLE")` — an honest signal that no data, cached or otherwise, is currently available.
3. The two printed results show the fallback correctly distinguishing three different situations across these examples: a genuine "not found" (Level 2), a system failure with a usable cache hit (this level's first call), and a system failure with no cache to fall back on (this level's second call) — three meaningfully different outcomes from what a single undifferentiated fallback (Level 1) would have collapsed into one identical response every time.

```
requestedId="42",  TimeoutException      -> cache HIT -> return real cached Invoice(42, 199.99, CACHED)
requestedId="999", BulkheadFullException -> cache MISS -> return Invoice(999, -1.0, TEMPORARILY_UNAVAILABLE)
```

## 7. Gotchas & takeaways

> **Gotcha:** a cache-based fallback can silently serve arbitrarily stale data if the cache is never invalidated or refreshed — for data where staleness has real consequences (a price that's since changed, a stock level that's since sold out), an unrefreshed cache fallback can be actively misleading rather than merely "slightly outdated." Pair cached fallbacks with a reasonable freshness check, or at minimum, surface the fact that the value is cached (as `"CACHED"` does here) so downstream logic or the UI can decide how to treat it.

- Every resilience pattern in this section can terminate in a fallback — designing that fallback thoughtfully, rather than treating it as an afterthought, is what actually determines the quality of a system's degraded-mode behavior.
- Distinguishing failure causes by exception type inside the fallback lets each kind of failure produce an appropriately different response, rather than collapsing every possible problem into one indistinguishable generic answer.
- A genuinely business-level outcome (like "not found") should usually be handled differently from a system-level failure (timeout, overload, circuit open) — the former is real information about the requested resource; the latter is a statement about current infrastructure health.
- A cached last-known-good value, when available, is frequently the best possible fallback — more useful to the caller than a fabricated default, and more honest than pretending the system is fully healthy.
