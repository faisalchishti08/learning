---
card: microservices
gi: 245
slug: graceful-degradation
title: "Graceful degradation"
---

## 1. What it is

Graceful degradation is a system's ability to continue providing reduced, but still useful, functionality when part of it fails, rather than failing completely — a product page that still shows price and description with reviews missing, instead of showing nothing at all when the reviews service is unavailable.

## 2. Why & when

Treating every dependency as equally critical means any single dependency's failure takes down the entire feature depending on it, even when that dependency's contribution was genuinely non-essential to the feature's core value — exactly the undifferentiated failure handling [designing for failure](0241-design-for-failure-principle.md) argues against. Graceful degradation requires classifying functionality by how essential it actually is, and deliberately designing a reduced-but-functional fallback for everything below "absolutely essential," so a non-essential dependency's failure produces a smaller, less complete experience instead of no experience at all.

Apply graceful degradation to any feature composed of multiple, independently-failing pieces where not all of them are equally critical to the feature's core value — nearly every real product surface. Apply it more cautiously (or not at all) where a partial, degraded result could actively mislead a user in a harmful way — showing a stale or partial account balance, for instance, is often worse than showing a clear "temporarily unavailable" message.

## 3. Core concept

Graceful degradation classifies each contributing piece of functionality and defines an explicit fallback for anything non-essential, so a failure in one piece narrows the response rather than eliminating it — the essential/non-essential classification itself is the deliberate design decision that determines what "graceful" actually means for a given feature.

```java
// a page assembled from MULTIPLE independent pieces, each classified by essentiality
PageResponse buildProductPage(String productId) {
    String pricing = fetchEssential(() -> pricingService.getPrice(productId)); // ESSENTIAL -- no meaningful page without it
    String reviews = fetchWithFallback(() -> reviewService.getReviews(productId), "Reviews temporarily unavailable"); // NON-essential
    String recommendations = fetchWithFallback(() -> recommendationService.get(productId), List.of()); // NON-essential, empty is fine

    return new PageResponse(pricing, reviews, recommendations); // STILL a complete, useful page even if reviews/recommendations failed
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A full-functionality response includes pricing, reviews, and recommendations; when the reviews dependency fails, a gracefully degraded response still includes pricing and recommendations, with reviews replaced by a fallback message, rather than the whole page failing" >
  <rect x="20" y="20" width="270" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Full response</text>
  <text x="155" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">pricing + reviews + recommendations</text>

  <rect x="350" y="20" width="270" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Degraded response</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">pricing + [reviews fallback] + recommendations</text>

  <rect x="180" y="110" width="280" height="35" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="132" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">reviews dependency FAILS</text>

  <line x1="320" y1="108" x2="320" y2="78" stroke="#8b949e" marker-end="url(#arr245)"/>

  <defs>
    <marker id="arr245" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The response narrows rather than disappears; only the failed, non-essential piece is missing from an otherwise complete page.

## 5. Runnable example

Scenario: a product page assembled with no degradation strategy (any failure kills the whole page), refactored to degrade gracefully per-piece with independently-designed fallbacks, and finally extended to add a "degradation level" indicator so the caller (and monitoring) can distinguish a fully healthy response from a partially degraded one, rather than a degraded page looking identical to a fully healthy one.

### Level 1 — Basic

```java
// File: AllOrNothingPage.java -- ANY dependency failing means the
// ENTIRE page fails -- no notion of "partial but useful" exists.
public class AllOrNothingPage {
    static String getPricing(String productId) { return "$25.00"; }
    static String getReviews(String productId) { throw new RuntimeException("reviews unavailable"); }
    static java.util.List<String> getRecommendations(String productId) { return java.util.List.of("Widget B", "Widget C"); }

    public static void main(String[] args) {
        try {
            String pricing = getPricing("prod-1");
            String reviews = getReviews("prod-1"); // THROWS -- takes down EVERYTHING below it too
            var recommendations = getRecommendations("prod-1"); // never reached
            System.out.println(pricing + " | " + reviews + " | " + recommendations);
        } catch (RuntimeException e) {
            System.out.println("ENTIRE page failed: " + e.getMessage() + " -- even pricing, which succeeded, is now unavailable to the user.");
        }
    }
}
```

**How to run:** `javac AllOrNothingPage.java && java AllOrNothingPage` (JDK 17+).

### Level 2 — Intermediate

```java
// File: GracefullyDegradedPage.java -- reviews DEGRADES to a fallback
// message instead of failing the page; the REST of the page stays intact.
import java.util.*;
import java.util.function.*;

public class GracefullyDegradedPage {
    static String getPricing(String productId) { return "$25.00"; }
    static String getReviews(String productId) { throw new RuntimeException("reviews unavailable"); }
    static List<String> getRecommendations(String productId) { return List.of("Widget B", "Widget C"); }

    static <T> T fetchWithFallback(Supplier<T> call, T fallback) {
        try { return call.get(); }
        catch (Exception e) { return fallback; } // DEGRADE gracefully rather than propagate
    }

    public static void main(String[] args) {
        String pricing = getPricing("prod-1"); // ESSENTIAL -- no fallback needed OR wanted; let it fail loudly if it fails
        String reviews = fetchWithFallback(() -> getReviews("prod-1"), "Reviews temporarily unavailable");
        List<String> recommendations = fetchWithFallback(() -> getRecommendations("prod-1"), List.of());

        System.out.println(pricing + " | " + reviews + " | " + recommendations);
        System.out.println("The page is STILL useful, despite reviews failing.");
    }
}
```

**How to run:** `javac GracefullyDegradedPage.java && java GracefullyDegradedPage` (JDK 17+).

Expected output:
```
$25.00 | Reviews temporarily unavailable | [Widget B, Widget C]
The page is STILL useful, despite reviews failing.
```

### Level 3 — Advanced

```java
// File: DegradationLevelTracked.java -- tracks and reports a DEGRADATION
// LEVEL alongside the response, so callers/monitoring can distinguish a
// FULLY healthy response from a PARTIALLY degraded one, rather than
// both looking identical.
import java.util.*;
import java.util.function.*;

public class DegradationLevelTracked {
    record PageResult<T>(T value, boolean degraded, String reason) {}
    record PageResponse(String pricing, PageResult<String> reviews, PageResult<List<String>> recommendations) {
        boolean isFullyHealthy() { return !reviews.degraded() && !recommendations.degraded(); }
        List<String> degradedComponents() {
            List<String> degraded = new ArrayList<>();
            if (reviews.degraded()) degraded.add("reviews: " + reviews.reason());
            if (recommendations.degraded()) degraded.add("recommendations: " + recommendations.reason());
            return degraded;
        }
    }

    static String getPricing(String productId) { return "$25.00"; }
    static String getReviews(String productId) { throw new RuntimeException("reviews service timeout"); }
    static List<String> getRecommendations(String productId) { return List.of("Widget B", "Widget C"); } // this one SUCCEEDS

    static <T> PageResult<T> fetchTracked(Supplier<T> call, T fallback) {
        try { return new PageResult<>(call.get(), false, null); }
        catch (Exception e) { return new PageResult<>(fallback, true, e.getMessage()); }
    }

    public static void main(String[] args) {
        String pricing = getPricing("prod-1");
        PageResult<String> reviews = fetchTracked(() -> getReviews("prod-1"), "Reviews temporarily unavailable");
        PageResult<List<String>> recommendations = fetchTracked(() -> getRecommendations("prod-1"), List.of());

        PageResponse page = new PageResponse(pricing, reviews, recommendations);

        System.out.println("Pricing: " + page.pricing());
        System.out.println("Reviews: " + page.reviews().value());
        System.out.println("Recommendations: " + page.recommendations().value());
        System.out.println("\nFully healthy? " + page.isFullyHealthy());
        System.out.println("Degraded components: " + page.degradedComponents());
    }
}
```

**How to run:** `javac DegradationLevelTracked.java && java DegradationLevelTracked` (JDK 17+).

Expected output:
```
Pricing: $25.00
Reviews: Reviews temporarily unavailable
Recommendations: [Widget B, Widget C]

Fully healthy? false
Degraded components: [reviews: reviews service timeout]
```

## 6. Walkthrough

1. **Level 1, no notion of partial success** — `getReviews` throwing causes the `try` block to abort entirely at that line, meaning `getRecommendations` is never even called and `pricing` (which *did* succeed) is discarded along with everything else — the entire page fails as a single, indivisible unit even though only one of its three pieces actually had a problem.
2. **Level 2, per-piece fallback** — `fetchWithFallback` catches any exception from its `call` and substitutes `fallback` instead of letting it propagate; wrapping `getReviews` and `getRecommendations` in this helper (while deliberately leaving `getPricing` unwrapped, since it's essential) means a failure in either non-essential piece produces a reasonable default rather than aborting the whole page.
3. **Level 2, the resulting complete-but-partial page** — the final printed line includes real pricing, a fallback message for reviews, and (in this particular run) real recommendations, since `getRecommendations` doesn't actually fail in this example — this demonstrates a page that degrades exactly where needed and stays fully functional everywhere else.
4. **Level 3, making degradation observable** — `PageResult<T>` pairs a value with a `degraded` boolean and an optional `reason`, so a caller (or a monitoring system) can distinguish "this value is the real data" from "this value is a fallback substituted after a failure" — a distinction Level 2's plain fallback values couldn't express at all.
5. **Level 3, aggregating degradation status** — `PageResponse.isFullyHealthy()` checks whether *any* tracked component is degraded, and `degradedComponents()` lists exactly which ones are, along with their specific failure reasons; this gives a single, structured signal for whether the page a user just received was fully complete or quietly missing something.
6. **Level 3, why this matters beyond just serving a nicer page** — printing `isFullyHealthy()` as `false` and `degradedComponents()` naming `reviews` specifically means this degradation event is now *observable*, not just silently absorbed — exactly the monitoring gap flagged as a risk in [designing for failure](0241-design-for-failure-principle.md): without this kind of explicit tracking, a reviews dependency that's been broken for hours would degrade every single page view invisibly, with no signal anywhere indicating that anything was ever wrong.

## 7. Gotchas & takeaways

> **Gotcha:** graceful degradation is not always the right choice — for functionality where a partial or stale result could actively mislead rather than merely inconvenience (an account balance, an inventory count near zero, anything a user might act on incorrectly), failing clearly and visibly is often safer than degrading silently to a plausible-looking but wrong value; degrade gracefully for genuinely non-essential, low-stakes functionality, and fail loudly and visibly for anything where a wrong-but-plausible answer could cause real harm.

- Graceful degradation lets a feature continue providing reduced but still useful functionality when a non-essential dependency fails, rather than failing completely.
- It requires an explicit, deliberate classification of each contributing piece as essential or non-essential, and a designed fallback for everything in the latter category — the classification itself is the real design decision.
- Tracking and reporting *whether* a given response was degraded (not just silently substituting a fallback) is what makes degradation observable, distinguishing it from a genuinely healthy response for monitoring and alerting purposes.
- This pattern is a concrete, feature-level application of the broader [design for failure principle](0241-design-for-failure-principle.md).
- Degradation isn't universally appropriate — for functionality where a wrong-but-plausible partial result could mislead a user into a harmful decision, failing visibly is often the safer choice than degrading silently.
