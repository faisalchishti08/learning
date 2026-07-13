---
card: microservices
gi: 241
slug: design-for-failure-principle
title: "Design for failure principle"
---

## 1. What it is

Design for failure is the principle that a distributed system should be architected on the explicit assumption that its dependencies, network links, and even its own instances *will* fail — not as a rare exception to plan a fallback for later, but as a certainty to design around from the start, so failure handling is built into the system's structure rather than bolted on as an afterthought.

## 2. Why & when

Building a system first for the happy path, then trying to add failure handling afterward, tends to produce shallow, inconsistent protection — a timeout added here, a retry added there, wherever a production incident happened to expose a gap, with no coherent strategy connecting them. Designing for failure from the outset, informed by understanding [why distributed systems fail](0239-why-distributed-systems-fail-partial-failure.md) through partial failure, means every dependency call is written with an explicit answer to "what happens when this fails," every service is built assuming its own instances can be killed and restarted at any moment, and failure handling becomes a first-class part of the architecture rather than defensive patches layered on top of it.

Apply this principle from a service's initial design, not after its first production outage — retrofitting resilience into a system built without this assumption is real, disruptive work, while building it in from the start is comparatively cheap. Every subsequent pattern in this section (circuit breakers, retries, bulkheads, graceful degradation) is a concrete technique for implementing this principle in a specific situation.

## 3. Core concept

Designing for failure means every external dependency call is wrapped with an explicit failure-handling decision made at design time — not "we'll add a try/catch if it breaks in production," but "here is exactly what this code does when this specific call fails, decided before it ships."

```java
// NOT designed for failure -- the happy path ONLY; no decision has been made about failure at all
String recommendations = recommendationService.getRecommendations(userId); // if this throws, what SHOULD happen? Undecided.

// DESIGNED for failure -- the failure behavior is an EXPLICIT, DELIBERATE part of the design
String recommendations;
try {
    recommendations = recommendationService.getRecommendations(userId);
} catch (Exception e) {
    // a DELIBERATE decision: recommendations are NON-ESSENTIAL -- degrade gracefully rather than fail the whole page
    recommendations = FALLBACK_GENERIC_RECOMMENDATIONS;
    metrics.increment("recommendations.fallback_used");
}
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Retrofitting resilience after the fact means patching gaps discovered by production incidents one at a time; designing for failure from the start means every dependency call has an explicit, deliberate failure-handling decision built in from day one" >
  <rect x="20" y="15" width="280" height="55" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="37" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Retrofitted: patch after each incident</text>
  <text x="160" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">inconsistent, reactive coverage</text>

  <rect x="340" y="15" width="280" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="37" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Designed for failure: decided upfront</text>
  <text x="480" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">every call has a deliberate answer</text>

  <rect x="160" y="100" width="320" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="122" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Same underlying failures WILL occur either way</text>

  <line x1="160" y1="70" x2="260" y2="98" stroke="#8b949e" marker-end="url(#arr241)"/>
  <line x1="480" y1="70" x2="400" y2="98" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr241g)"/>

  <defs>
    <marker id="arr241" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="arr241g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Failure is a certainty either way; the difference is whether the response to it was decided deliberately or discovered under production pressure.

## 5. Runnable example

Scenario: a product page assembling data from three dependencies, first built with no explicit failure handling anywhere (any one dependency's failure crashes the whole page), then redesigned upfront with an explicit, deliberate essential-vs-non-essential classification for each dependency, and finally showing the same design surviving a new dependency being added later, because the pattern established up front naturally accommodates it.

### Level 1 — Basic

```java
// File: NoFailureDesign.java -- happy-path ONLY; if ANY dependency call
// throws, the ENTIRE page fails, even for data that wasn't essential.
public class NoFailureDesign {
    static String getPricing(String productId) { return "$25.00"; }
    static String getReviews(String productId) { throw new RuntimeException("reviews service unavailable"); } // simulated failure
    static String getRecommendations(String productId) { return "Related: Widget B, Widget C"; }

    public static void main(String[] args) {
        String pricing = getPricing("prod-1");
        String reviews = getReviews("prod-1"); // THROWS -- nothing here decided what should happen
        String recommendations = getRecommendations("prod-1"); // never even reached
        System.out.println(pricing + " | " + reviews + " | " + recommendations);
    }
}
```

**How to run:** `javac NoFailureDesign.java && java NoFailureDesign` (JDK 17+) — this will throw an uncaught exception and crash, by design, to illustrate the problem.

### Level 2 — Intermediate

```java
// File: DeliberateFailureDesign.java -- EVERY dependency call has an
// EXPLICIT, deliberate answer for failure, decided as part of the design,
// classifying each as ESSENTIAL (page fails without it) or NON-ESSENTIAL
// (page degrades gracefully).
public class DeliberateFailureDesign {
    static String getPricing(String productId) { return "$25.00"; }
    static String getReviews(String productId) { throw new RuntimeException("reviews service unavailable"); }
    static String getRecommendations(String productId) { return "Related: Widget B, Widget C"; }

    static String fetchEssential(String label, java.util.function.Supplier<String> call) {
        return call.get(); // ESSENTIAL -- let a failure here propagate; the page genuinely cannot render without it
    }

    static String fetchNonEssential(String label, java.util.function.Supplier<String> call, String fallback) {
        try {
            return call.get();
        } catch (Exception e) {
            System.out.println("  [design decision] " + label + " is NON-ESSENTIAL -- degrading to fallback");
            return fallback; // NON-ESSENTIAL -- deliberately degrade rather than fail the whole page
        }
    }

    public static void main(String[] args) {
        String pricing = fetchEssential("pricing", () -> getPricing("prod-1")); // pricing is ESSENTIAL, by design
        String reviews = fetchNonEssential("reviews", () -> getReviews("prod-1"), "Reviews unavailable"); // NON-essential, by design
        String recommendations = fetchNonEssential("recommendations", () -> getRecommendations("prod-1"), "No recommendations");

        System.out.println(pricing + " | " + reviews + " | " + recommendations);
    }
}
```

**How to run:** `javac DeliberateFailureDesign.java && java DeliberateFailureDesign` (JDK 17+).

Expected output:
```
  [design decision] reviews is NON-ESSENTIAL -- degrading to fallback
$25.00 | Reviews unavailable | Related: Widget B, Widget C
```

### Level 3 — Advanced

```java
// File: NewDependencyFitsExistingDesign.java -- a NEW dependency (shipping
// estimate) is added LATER; because the essential/non-essential PATTERN
// was established upfront, adding it correctly is a small, guided decision,
// not a fresh, ad-hoc question each time.
import java.util.function.*;

public class NewDependencyFitsExistingDesign {
    static String getPricing(String productId) { return "$25.00"; }
    static String getReviews(String productId) { throw new RuntimeException("reviews service unavailable"); }
    static String getRecommendations(String productId) { return "Related: Widget B, Widget C"; }
    static String getShippingEstimate(String productId) { throw new RuntimeException("shipping service unavailable"); } // NEW dependency

    static String fetchEssential(String label, Supplier<String> call) { return call.get(); }

    static String fetchNonEssential(String label, Supplier<String> call, String fallback) {
        try { return call.get(); }
        catch (Exception e) {
            System.out.println("  [design decision] " + label + " is NON-ESSENTIAL -- degrading to fallback");
            return fallback;
        }
    }

    public static void main(String[] args) {
        String pricing = fetchEssential("pricing", () -> getPricing("prod-1"));
        String reviews = fetchNonEssential("reviews", () -> getReviews("prod-1"), "Reviews unavailable");
        String recommendations = fetchNonEssential("recommendations", () -> getRecommendations("prod-1"), "No recommendations");
        // adding the NEW dependency required just ONE line, using the SAME established pattern -- an explicit, deliberate choice
        String shipping = fetchNonEssential("shipping estimate", () -> getShippingEstimate("prod-1"), "Shipping estimate unavailable");

        System.out.println(pricing + " | " + reviews + " | " + recommendations + " | " + shipping);
        System.out.println("The NEW dependency was added using the SAME deliberate pattern -- no ad-hoc, undecided failure handling crept in.");
    }
}
```

**How to run:** `javac NewDependencyFitsExistingDesign.java && java NewDependencyFitsExistingDesign` (JDK 17+).

Expected output:
```
  [design decision] reviews is NON-ESSENTIAL -- degrading to fallback
  [design decision] shipping estimate is NON-ESSENTIAL -- degrading to fallback
$25.00 | Reviews unavailable | Related: Widget B, Widget C | Shipping estimate unavailable
```

## 6. Walkthrough

1. **Level 1, the undesigned baseline** — `getReviews` throws, and because nothing in `main` has decided what should happen in that case, the exception propagates uncaught, crashing the entire page — including the unrelated `getRecommendations` call that would have succeeded if it had ever been reached; nothing about this failure mode was a deliberate choice, it's simply what happens by default when no decision was made.
2. **Level 2, classifying dependencies deliberately** — `fetchEssential` and `fetchNonEssential` represent two different, explicit design decisions made about each dependency ahead of time: `pricing` is deemed essential (the page genuinely can't render meaningfully without a price), while `reviews` and `recommendations` are deemed non-essential (the page is still useful without them).
3. **Level 2, the graceful outcome** — when `getReviews` throws inside `fetchNonEssential`, the exception is caught and a fallback string is substituted, and execution continues to `getRecommendations` normally; the final printed line shows a complete, still-useful page despite one dependency having failed — this is the direct, designed consequence of the essential/non-essential classification made in step 1, not an accident of exception handling.
4. **Level 3, a new dependency introduced later** — `getShippingEstimate` is added as a new capability, and rather than requiring a fresh, from-scratch decision about how to handle its potential failure, it's wired through the *same* `fetchNonEssential` helper already established for `reviews` and `recommendations`.
5. **Level 3, the design paying off over time** — adding this new, also-failing dependency required exactly one line of new code following an existing, well-understood pattern, and it behaves consistently with every other non-essential dependency already in the page — no ad-hoc "let's just wrap this one in a try/catch real quick" decision was needed, because the pattern for making that decision was already established.
6. **Level 3, the resulting page still complete** — despite *two* dependencies (`reviews` and `shipping`) failing simultaneously in this final version, the page still renders completely, with clear fallback text for each — demonstrating that a system designed for failure from the outset accommodates new failure points gracefully as the system grows, rather than each new dependency reintroducing the same undesigned risk Level 1 started with.

## 7. Gotchas & takeaways

> **Gotcha:** classifying a dependency as "non-essential" is itself a real design decision with consequences — silently swallowing a failure and returning a fallback can mask a genuine, worsening problem (a dependency that's been down for hours, quietly degrading every page) if that fallback usage isn't also monitored and alerted on; "designed for failure" means deciding both how to degrade *and* how to notice that degradation is happening, not just adding a `catch` block and moving on.

- Designing for failure means treating dependency and instance failure as a certainty to architect around from the start, not an exception to patch reactively after an incident.
- Every external dependency call should have an explicit, deliberate answer to "what happens when this fails," decided as part of the design rather than left undecided until production reveals the gap.
- Classifying dependencies as essential versus non-essential, and handling each deliberately and consistently, is a concrete application of this principle that scales cleanly as new dependencies are added.
- This principle is the foundation the rest of this section's specific patterns (circuit breakers, retries, bulkheads, graceful degradation) build on as concrete implementations.
- Gracefully degrading on a dependency's failure must be paired with monitoring that degradation, or a genuinely serious, ongoing outage can go unnoticed behind a silently-triggering fallback.
