---
card: microservices
gi: 51
slug: subdomains-core-supporting-generic
title: "Subdomains: core, supporting, generic"
---

## 1. What it is

While [decomposing by subdomain](0039-decompose-by-subdomain-ddd.md) covered using the core/supporting/generic classification as a technique for drawing service boundaries, this tutorial goes deeper into the classification judgment itself: how do you actually decide whether a given piece of the domain is core, supporting, or generic, especially when it isn't obvious? A concrete, repeatable scoring approach — weighing competitive differentiation, uniqueness to your business, and how much the business's success depends on getting it right — produces more consistent classifications than an intuitive, one-off judgment call, especially across a large domain with many subdomains to classify.

## 2. Why & when

Intuitive classification tends to be inconsistent across a team — one engineer might call a subdomain "core" because it's technically the most interesting or complex part to build, while the actual business reason something is core has nothing to do with technical complexity and everything to do with competitive differentiation. A subdomain can be enormously complex to implement (a generic "send an email reliably at scale" subsystem) while being entirely generic from a business-strategy perspective, and a subdomain can be relatively simple to implement (a specific pricing algorithm) while being the single most important thing the business does.

Use an explicit scoring approach whenever a subdomain's classification isn't immediately obvious, or when different stakeholders disagree — turning "I think this feels core" into "on these three specific dimensions, here's why" produces a classification that's easier to defend, revisit, and apply consistently across many subdomains.

## 3. Core concept

Three independent questions, each contributing evidence to a subdomain's classification:

1. **Differentiation:** does doing this well, specifically, make customers choose us over a competitor?
2. **Uniqueness:** is our approach to this genuinely different from how most other businesses solve it, or is it essentially the same problem everyone else has?
3. **Strategic dependency:** does the business's overall strategy specifically depend on getting this right, or would a merely adequate solution be sufficient?

High scores across all three point toward **core**; low scores across all three point toward **generic**; a mixed or moderate profile points toward **supporting**.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three scoring dimensions -- differentiation, uniqueness, strategic dependency -- combine to classify a subdomain as core, supporting, or generic">
  <g font-family="sans-serif">
    <rect x="20" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
    <text x="110" y="47" fill="#e6edf3" font-size="9" text-anchor="middle">Differentiation</text>
    <rect x="230" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
    <text x="320" y="47" fill="#e6edf3" font-size="9" text-anchor="middle">Uniqueness</text>
    <rect x="440" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
    <text x="530" y="47" fill="#e6edf3" font-size="9" text-anchor="middle">Strategic dependency</text>
  </g>
  <text x="320" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">high across all three -&gt; CORE   /   low across all three -&gt; GENERIC   /   mixed -&gt; SUPPORTING</text>
</svg>

Three independent scoring dimensions converge into a defensible core/supporting/generic classification.

## 5. Runnable example

Scenario: scoring several candidate subdomains from a delivery company against the three dimensions, first with a naive intuitive guess, then with explicit scoring, then applied across the whole domain to produce a consistent classification.

### Level 1 — Basic

```java
// File: IntuitiveGuess.java -- classify subdomains by GUT FEELING, no explicit criteria
public class IntuitiveGuess {
    public static void main(String[] args) {
        System.out.println("RouteOptimization: feels important... CORE? (not sure why, exactly)");
        System.out.println("Authentication: feels standard... GENERIC? (not sure why, exactly)");
    }
}
```

**How to run:** `javac IntuitiveGuess.java && java IntuitiveGuess` (JDK 17+).

Expected output:
```
RouteOptimization: feels important... CORE? (not sure why, exactly)
Authentication: feels standard... GENERIC? (not sure why, exactly)
```

These guesses might well be correct, but there's no explicit reasoning behind them — nothing to defend the classification with if a stakeholder disagrees, and nothing consistent to apply to the next subdomain.

### Level 2 — Intermediate

```java
// File: ScoredClassification.java -- score each subdomain on THREE explicit
// dimensions, then classify based on the scores.
import java.util.*;

public class ScoredClassification {
    record Scores(int differentiation, int uniqueness, int strategicDependency) { // each 1-10
        int average() { return (differentiation + uniqueness + strategicDependency) / 3; }
    }

    static String classify(Scores scores) {
        int avg = scores.average();
        if (avg >= 7) return "CORE";
        if (avg <= 3) return "GENERIC";
        return "SUPPORTING";
    }

    public static void main(String[] args) {
        Scores routeOptimization = new Scores(9, 8, 9); // this delivery company's actual edge
        Scores authentication = new Scores(1, 1, 2);    // a solved problem, same for almost any company

        System.out.println("RouteOptimization: avg=" + routeOptimization.average() + " -> " + classify(routeOptimization));
        System.out.println("Authentication: avg=" + authentication.average() + " -> " + classify(authentication));
    }
}
```

**How to run:** `javac ScoredClassification.java && java ScoredClassification` (JDK 17+).

Expected output:
```
RouteOptimization: avg=8 -> CORE
Authentication: avg=1 -> GENERIC
```

The same conclusions as the intuitive guess, but now backed by explicit, specific scores across three named dimensions — a classification that can be reviewed, challenged on a specific dimension, and applied consistently to the next subdomain.

### Level 3 — Advanced

```java
// File: ClassifyWholeDomain.java -- apply the SAME scoring consistently
// across the WHOLE domain, including a genuinely borderline case.
import java.util.*;

public class ClassifyWholeDomain {
    record Subdomain(String name, int differentiation, int uniqueness, int strategicDependency) {
        int average() { return (differentiation + uniqueness + strategicDependency) / 3; }
    }

    static String classify(Subdomain s) {
        int avg = s.average();
        if (avg >= 7) return "CORE";
        if (avg <= 3) return "GENERIC";
        return "SUPPORTING";
    }

    public static void main(String[] args) {
        List<Subdomain> subdomains = List.of(
            new Subdomain("RouteOptimization", 9, 8, 9),
            new Subdomain("Authentication", 1, 1, 2),
            new Subdomain("DriverScheduling", 5, 6, 5), // genuinely borderline -- necessary, somewhat differentiated
            new Subdomain("EmailNotifications", 2, 1, 1)
        );

        for (Subdomain s : subdomains) {
            System.out.println(s.name() + " (avg=" + s.average() + "): " + classify(s));
        }
    }
}
```

**How to run:** `javac ClassifyWholeDomain.java && java ClassifyWholeDomain` (JDK 17+).

Expected output:
```
RouteOptimization (avg=8): CORE
Authentication (avg=1): GENERIC
DriverScheduling (avg=5): SUPPORTING
EmailNotifications (avg=1): GENERIC
```

The production-flavored case: `DriverScheduling` scores in the middle across all three dimensions (`5, 6, 5`, averaging `5`) — genuinely necessary to the business and somewhat differentiated (good scheduling reduces driver idle time, a real competitive factor), but not as strategically central as `RouteOptimization`. The scoring approach correctly lands it in `SUPPORTING`, a defensible middle classification rather than forcing a binary core-or-generic call that wouldn't accurately reflect its real position.

## 6. Walkthrough

1. For each `Subdomain` in the list, the loop calls `s.average()`, which computes `(differentiation + uniqueness + strategicDependency) / 3` using integer division.
2. For `RouteOptimization`, `(9 + 8 + 9) / 3 = 26 / 3 = 8` (integer division truncates). `classify` checks `avg >= 7`, which is true, returning `"CORE"`.
3. For `DriverScheduling`, `(5 + 6 + 5) / 3 = 16 / 3 = 5`. `classify` checks `avg >= 7` (false), then `avg <= 3` (also false, since `5 > 3`), so it falls through to the default `"SUPPORTING"` branch.
4. For `EmailNotifications`, `(2 + 1 + 1) / 3 = 4 / 3 = 1`. `classify` checks `avg >= 7` (false), then `avg <= 3` (true, since `1 <= 3`), returning `"GENERIC"`.
5. The final printed list shows all four subdomains classified consistently by the same rule, applied identically regardless of which specific subdomain is being evaluated — the scoring criteria, not individual intuition, determined each outcome.

```
RouteOptimization:   (9+8+9)/3 = 8  -> CORE
DriverScheduling:    (5+6+5)/3 = 5  -> SUPPORTING (genuinely in between)
Authentication:      (1+1+2)/3 = 1  -> GENERIC
EmailNotifications:  (2+1+1)/3 = 1  -> GENERIC
```

## 7. Gotchas & takeaways

> **Gotcha:** the specific numeric scores are still subjective judgments — this framework doesn't eliminate judgment, it structures and makes it explicit and comparable. Different stakeholders may still score the same subdomain differently on a given dimension; the value is that the *disagreement itself* becomes specific and discussable ("we disagree on uniqueness, specifically") rather than a vague overall disagreement about the final label.

- A structured scoring approach — differentiation, uniqueness, and strategic dependency — produces more consistent and more defensible core/supporting/generic classifications than intuitive, one-off judgment calls.
- A subdomain's technical complexity has no necessary relationship to its business classification — a technically simple subdomain can be core, and a technically complex one can be entirely generic.
- Scoring explicitly surfaces genuinely borderline cases (like `DriverScheduling` landing squarely in `SUPPORTING`) as a legitimate, defensible classification, rather than forcing every subdomain into a binary core-or-generic decision.
- Applying the same scoring criteria consistently across a whole domain produces classifications that are comparable to each other, which matters when deciding where to allocate limited engineering investment across many subdomains at once.
