---
card: microservices
gi: 282
slug: fallback-methods-default-responses
title: "Fallback methods & default responses"
---

## 1. What it is

A fallback method is code that runs in place of the primary call when that call fails — whether from a thrown exception, a [circuit breaker](0250-circuit-breaker-pattern.md) being open, a [timeout](0280-timeout-pattern-timelimiter.md), or exhausted [retries](0259-retry-pattern.md) — so the caller still gets *some* usable response instead of an error propagating all the way up. Resilience4j and Spring Cloud CircuitBreaker both support attaching a fallback function directly to a protected call, invoked automatically whenever the primary path fails.

## 2. Why & when

Not every failure needs to become a user-visible error. If a "recommended products" service is down, showing a generic, non-personalized set of popular products is almost always a better user experience than showing an error page or a blank section — the core page (e.g., a shopping cart) can still function. Fallbacks turn a hard failure of one dependency into graceful degradation of the overall system: the feature that depended on it gets worse, not broken.

Use a fallback wherever there is a reasonable degraded response — a cached value, a default/generic value, an empty result, or a simplified computation that doesn't need the failing dependency. Do not use a fallback to silently hide failures that genuinely need to surface as errors (e.g., a payment call failing should not "fall back" to pretending the payment succeeded).

## 3. Core concept

A fallback function has the same return type as the primary call and typically receives the triggering exception, so it can react differently to different failure causes if needed.

```java
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import java.util.function.Supplier;
import io.vavr.control.Try;

CircuitBreaker circuitBreaker = CircuitBreaker.ofDefaults("recommendations");
Supplier<List<String>> decorated = CircuitBreaker.decorateSupplier(circuitBreaker,
        () -> recommendationService.getPersonalized(userId));

List<String> result = Try.ofSupplier(decorated)
        .recover(throwable -> genericPopularProductsFallback()) // FALLBACK on ANY failure
        .get();
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A primary call is attempted first; if it succeeds its result flows to the caller, but if it fails for any reason the fallback method runs instead and its result flows to the caller, so the caller always receives a usable response either way">
  <rect x="30" y="20" width="160" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">primary call</text>

  <line x1="190" y1="40" x2="280" y2="40" stroke="#8b949e"/>
  <text x="235" y="30" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fails</text>
  <line x1="280" y1="40" x2="280" y2="90" stroke="#8b949e" marker-end="url(#arr282)"/>

  <rect x="200" y="95" width="160" height="40" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="280" y="119" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">fallback method</text>

  <line x1="110" y1="60" x2="490" y2="140" stroke="#8b949e" stroke-dasharray="2,2"/>
  <line x1="360" y1="115" x2="480" y2="115" stroke="#8b949e" marker-end="url(#arr282)"/>

  <rect x="480" y="60" width="140" height="90" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="105" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">caller always gets</text>
  <text x="550" y="120" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">a usable response</text>

  <defs><marker id="arr282" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Success or failure of the primary call, the caller ends up with a usable response — degraded, but not broken.

## 5. Runnable example

Scenario: a product page that fails outright when its recommendation dependency fails, extended to add a generic-fallback so the page degrades gracefully instead of erroring, and finally differentiating the fallback response based on the specific failure type (timeout vs open circuit vs generic error) for better observability and user messaging.

### Level 1 — Basic

```java
// File: NoFallbackFailsHard.java -- when the recommendations call
// fails, the ENTIRE page-rendering call fails with it, even though
// recommendations are a non-essential part of the page.
public class NoFallbackFailsHard {
    static java.util.List<String> getPersonalizedRecommendations(String userId) {
        throw new RuntimeException("recommendation-service unreachable");
    }

    static String renderProductPage(String userId) {
        java.util.List<String> recs = getPersonalizedRecommendations(userId); // no protection at all
        return "Product Page for " + userId + " with recommendations: " + recs;
    }

    public static void main(String[] args) {
        try {
            System.out.println(renderProductPage("user-42"));
        } catch (Exception e) {
            System.out.println("ENTIRE page failed to render: " + e.getMessage());
        }
    }
}
```

How to run: `java NoFallbackFailsHard.java`

The recommendations call throws, and because nothing catches or degrades it, the whole `renderProductPage` call fails — the entire page, including the core product details that had nothing to do with recommendations, is lost because of one non-essential dependency.

### Level 2 — Intermediate

```java
// File: GenericFallback.java -- wraps the recommendations call so ANY
// failure falls back to a generic, non-personalized list, letting the
// rest of the page render normally.
import java.util.List;
import java.util.function.Supplier;

public class GenericFallback {
    static List<String> getPersonalizedRecommendations(String userId) {
        throw new RuntimeException("recommendation-service unreachable");
    }

    static List<String> withFallback(Supplier<List<String>> primary, List<String> fallbackValue) {
        try {
            return primary.get();
        } catch (Exception e) {
            System.out.println("  (recommendations failed: " + e.getMessage() + " -- using generic fallback)");
            return fallbackValue;
        }
    }

    static String renderProductPage(String userId) {
        List<String> recs = withFallback(
                () -> getPersonalizedRecommendations(userId),
                List.of("Popular Item A", "Popular Item B", "Popular Item C"));
        return "Product Page for " + userId + " with recommendations: " + recs;
    }

    public static void main(String[] args) {
        System.out.println(renderProductPage("user-42"));
    }
}
```

How to run: `java GenericFallback.java`

The recommendations call still throws, but `withFallback` catches the exception and substitutes a hardcoded generic list instead of letting the failure propagate. `renderProductPage` completes successfully and prints a full page with the generic recommendations in place of personalized ones — the user sees a slightly worse but fully functional page instead of an error.

### Level 3 — Advanced

```java
// File: DifferentiatedFallback.java -- distinguishes WHY the call failed
// (timeout vs a marker "circuit open" exception vs generic error) and
// tailors both the fallback content and a user-facing status message
// accordingly, which is valuable for observability and UX.
import java.util.List;
import java.util.concurrent.TimeoutException;

public class DifferentiatedFallback {
    static class CircuitOpenException extends RuntimeException {
        CircuitOpenException(String msg) { super(msg); }
    }

    record PageSection(List<String> items, String statusMessage) {}

    static List<String> getPersonalizedRecommendations(String userId, String failureMode) {
        if (failureMode.equals("timeout")) throw new RuntimeException(new TimeoutException("call exceeded 2s"));
        if (failureMode.equals("circuit-open")) throw new CircuitOpenException("circuit breaker OPEN, not attempting call");
        throw new RuntimeException("unexpected server error");
    }

    static PageSection withDifferentiatedFallback(String userId, String failureMode) {
        try {
            List<String> recs = getPersonalizedRecommendations(userId, failureMode);
            return new PageSection(recs, "personalized");
        } catch (CircuitOpenException e) {
            // Dependency is KNOWN to be unhealthy -- serve cached data, don't even hint at an error.
            return new PageSection(List.of("Cached: Item A", "Cached: Item B"), "using cached recommendations");
        } catch (RuntimeException e) {
            if (e.getCause() instanceof TimeoutException) {
                // Slow but maybe transient -- generic fallback, log for investigation.
                return new PageSection(List.of("Popular Item A", "Popular Item B"), "recommendations delayed, showing popular items");
            }
            // Unexpected error -- most conservative fallback, flag loudly for on-call.
            return new PageSection(List.of(), "recommendations unavailable");
        }
    }

    public static void main(String[] args) {
        for (String mode : new String[]{"timeout", "circuit-open", "server-error"}) {
            PageSection section = withDifferentiatedFallback("user-42", mode);
            System.out.println(mode + " -> items=" + section.items() + " status=\"" + section.statusMessage() + "\"");
        }
    }
}
```

How to run: `java DifferentiatedFallback.java`

Three different failure causes are simulated: a timeout, an already-open circuit breaker, and a generic server error. Each is caught by a different branch and produces a different fallback: a known-unhealthy circuit gets cached data with no error framing at all (since the system already knows about the outage), a timeout gets a generic-but-labeled fallback (since it might be transient), and a truly unexpected error gets the most conservative fallback (empty list, explicit "unavailable" status) so it's visibly flagged rather than silently smoothed over. This differentiated handling gives both a better user experience and better signal for whoever is monitoring the system.

## 6. Walkthrough

Trace `DifferentiatedFallback.main` for `mode="circuit-open"`. **First**, the loop calls `withDifferentiatedFallback("user-42", "circuit-open")`, which enters the `try` block and calls `getPersonalizedRecommendations(userId, "circuit-open")`.

**Inside that method**, the `failureMode.equals("circuit-open")` branch throws a `CircuitOpenException` — standing in for what a real `CircuitBreaker.decorateSupplier` wrapper would throw when the breaker is in the OPEN state and refusing to even attempt the call (see [circuit breaker pattern](0250-circuit-breaker-pattern.md)).

**Back in `withDifferentiatedFallback`**, this exception is caught by the first `catch (CircuitOpenException e)` block specifically (Java matches the most specific applicable catch clause first). Since a known-open circuit means the dependency has already been confirmed unhealthy (not just possibly slow), the fallback serves cached data directly, with a status message that doesn't alarm the user — `"using cached recommendations"` reads as normal, not as an error state.

**Contrast with `mode="timeout"`**: `getPersonalizedRecommendations` instead throws a plain `RuntimeException` wrapping a `TimeoutException` as its cause. This does not match the `CircuitOpenException` catch clause, so it falls to the second `catch (RuntimeException e)` block, where `e.getCause() instanceof TimeoutException` is checked and matches — producing the "delayed, showing popular items" fallback, a softer framing since a single timeout might just be transient.

**Contrast with `mode="server-error"`**: the thrown `RuntimeException` has no `TimeoutException` cause, so it falls through to the final `else`-equivalent path inside the second catch block, returning the most conservative fallback: an empty item list and an explicit `"recommendations unavailable"` status, appropriate for a genuinely unexpected condition that should be visible rather than papered over.

**Finally**, `main` prints each mode's resulting `PageSection`, showing three distinctly different but all *usable* results for what were three different underlying failures.

```
getPersonalizedRecommendations() throws
        |
        +-- CircuitOpenException ------> cached data, calm status
        +-- RuntimeException(TimeoutException) --> generic data, "delayed" status
        +-- RuntimeException(other) ----> empty data, "unavailable" status (loud)
```

## 7. Gotchas & takeaways

> A fallback that silently returns a plausible-looking default can hide a real, ongoing outage from monitoring if the failure is never logged or metered — always record that the fallback path was taken, even when the user-facing experience looks fine.

- Fallbacks turn hard failures into graceful degradation; they are appropriate for non-essential or cacheable data, not for operations where a wrong or stale answer is actively harmful (e.g., payments, inventory decrement).
- Differentiate fallback behavior by failure cause when it's cheap to do so — a known-unhealthy dependency (open circuit) and a one-off timeout deserve different framing and different logging.
- Always emit a metric or log entry when a fallback is invoked; a healthy-looking dashboard built entirely from fallback responses can mask a real outage.
- Keep fallback logic itself simple and fast — a fallback that can also fail or block defeats the purpose of protecting the caller.
