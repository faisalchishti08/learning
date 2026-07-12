---
card: microservices
gi: 45
slug: right-sizing-services-granularity-decisions
title: "Right-sizing services (granularity decisions)"
---

## 1. What it is

**Right-sizing** is the concrete decision process for choosing a service's granularity once candidate boundaries have been identified: given two adjacent candidate services, should they be merged into one, split further, or kept as-is? This builds directly on [service granularity](0019-service-granularity-nano-micro-macro-mini-services.md)'s cost model — every split adds network hops and operational overhead — by turning that general awareness into a specific, repeatable decision for each pair of candidate boundaries under consideration.

## 2. Why & when

Granularity decisions are easy to get wrong in either direction, and both mistakes are costly to reverse later: merging two things that should stay separate recreates coupling that will need to be painfully un-merged once the coupling causes real problems; splitting two things that should stay together adds needless network overhead and coordination cost for no corresponding benefit. A deliberate, repeatable decision process — rather than an intuitive, one-off judgment call — produces more consistent, defensible boundaries across a whole system, especially when many different engineers are drawing boundaries for different parts of it.

Run a right-sizing decision explicitly whenever two candidate services are adjacent enough that merging them is plausible — don't just default to "smaller is better" or "fewer services is simpler"; make the specific tradeoff for that specific pair explicit.

## 3. Core concept

A concrete decision test for any two adjacent candidate services, A and B:

1. **Coupling check:** how often does a single business change require touching both A and B together? Frequent joint changes argue for merging.
2. **Traffic check:** does one need dramatically different scaling than the other (see [independent scalability](0014-independent-scalability.md))? A large difference argues for keeping them split.
3. **Team check:** can one team genuinely own both well, or does splitting them match how teams are actually organized (see [service per team](0043-service-per-team.md))?
4. **Data check:** do A and B need transactional consistency with each other (an all-or-nothing update spanning both)? Genuine need for that argues strongly for merging, since [decentralized data](0009-decentralized-data-management.md) across a split makes strict consistency hard.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four checks -- coupling, traffic, team, data -- each pushing a granularity decision toward merge or toward split">
  <g font-family="sans-serif">
    <rect x="20" y="30" width="280" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
    <text x="160" y="53" fill="#e6edf3" font-size="9" text-anchor="middle">Coupling: frequent joint changes?</text>
    <rect x="20" y="75" width="280" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
    <text x="160" y="98" fill="#e6edf3" font-size="9" text-anchor="middle">Traffic: dramatically different load?</text>
    <rect x="340" y="30" width="280" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
    <text x="480" y="53" fill="#e6edf3" font-size="9" text-anchor="middle">Team: one team owns both well?</text>
    <rect x="340" y="75" width="280" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
    <text x="480" y="98" fill="#e6edf3" font-size="9" text-anchor="middle">Data: needs strict transactional consistency?</text>
  </g>
  <text x="320" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">weigh all four -&gt; MERGE or SPLIT decision, per pair</text>
</svg>

Four checks per candidate pair, weighed together into a concrete merge-or-split decision.

## 5. Runnable example

Scenario: two candidate service pairs, evaluated against the four-check framework, producing concrete merge-or-split recommendations for each.

### Level 1 — Basic

```java
// File: SingleCheck.java -- deciding based on ONE check only
public class SingleCheck {
    public static void main(String[] args) {
        boolean changeTogetherFrequently = true; // OrderService and OrderValidationService change together 90% of the time
        String decision = changeTogetherFrequently ? "MERGE" : "SPLIT";
        System.out.println("Based on coupling alone: " + decision);
    }
}
```

**How to run:** `javac SingleCheck.java && java SingleCheck` (JDK 17+).

Expected output:
```
Based on coupling alone: MERGE
```

One check suggests merging, but this decision would be stronger with the other three checks weighed in — the next level does exactly that.

### Level 2 — Intermediate

```java
// File: FourCheckDecision.java -- weigh all FOUR checks for one candidate pair
import java.util.*;

public class FourCheckDecision {
    record CandidatePair(String serviceA, String serviceB, boolean frequentJointChanges, boolean similarTraffic, boolean oneTeamCanOwnBoth, boolean needsTransactionalConsistency) { }

    static String decide(CandidatePair pair) {
        int mergeVotes = 0;
        if (pair.frequentJointChanges()) mergeVotes++;
        if (pair.similarTraffic()) mergeVotes++; // similar traffic REDUCES the case for splitting
        if (pair.oneTeamCanOwnBoth()) mergeVotes++;
        if (pair.needsTransactionalConsistency()) mergeVotes++; // strongest single signal for merging

        return mergeVotes >= 3 ? "MERGE" : (mergeVotes <= 1 ? "SPLIT" : "BORDERLINE -- needs human judgment");
    }

    public static void main(String[] args) {
        CandidatePair pair = new CandidatePair("OrderService", "OrderValidationService", true, true, true, true);
        System.out.println(pair.serviceA() + " + " + pair.serviceB() + ": " + decide(pair));
    }
}
```

**How to run:** `javac FourCheckDecision.java && java FourCheckDecision` (JDK 17+).

Expected output:
```
OrderService + OrderValidationService: MERGE
```

All four checks point toward merging: frequent joint changes, similar traffic, one team can own both, and they need transactional consistency — a strong, multi-signal case, not just the single coupling observation from Level 1.

### Level 3 — Advanced

```java
// File: CompareMultiplePairs.java -- run the SAME decision process across
// THREE different candidate pairs, producing genuinely different verdicts.
import java.util.*;

public class CompareMultiplePairs {
    record CandidatePair(String serviceA, String serviceB, boolean frequentJointChanges, boolean similarTraffic, boolean oneTeamCanOwnBoth, boolean needsTransactionalConsistency) { }

    static String decide(CandidatePair pair) {
        int mergeVotes = 0;
        if (pair.frequentJointChanges()) mergeVotes++;
        if (pair.similarTraffic()) mergeVotes++;
        if (pair.oneTeamCanOwnBoth()) mergeVotes++;
        if (pair.needsTransactionalConsistency()) mergeVotes++;
        return mergeVotes >= 3 ? "MERGE" : (mergeVotes <= 1 ? "SPLIT" : "BORDERLINE -- needs human judgment");
    }

    public static void main(String[] args) {
        List<CandidatePair> pairs = List.of(
            new CandidatePair("OrderService", "OrderValidationService", true, true, true, true),   // strongly coupled
            new CandidatePair("OrderService", "RecommendationService", false, false, false, false), // genuinely independent
            new CandidatePair("OrderService", "ShippingService", true, false, true, false)          // mixed signals
        );

        for (CandidatePair pair : pairs) {
            System.out.println(pair.serviceA() + " + " + pair.serviceB() + ": " + decide(pair));
        }
    }
}
```

**How to run:** `javac CompareMultiplePairs.java && java CompareMultiplePairs` (JDK 17+).

Expected output:
```
OrderService + OrderValidationService: MERGE
OrderService + RecommendationService: SPLIT
OrderService + ShippingService: BORDERLINE -- needs human judgment
```

The production-flavored case: three different candidate pairs, three genuinely different, well-justified verdicts. `OrderService`+`OrderValidationService` clearly merges (4/4 signals agree). `OrderService`+`RecommendationService` clearly stays split (0/4 signals favor merging — they're genuinely independent concerns). `OrderService`+`ShippingService` lands in the middle, correctly flagged as needing a human decision rather than an automatic verdict, since the signals conflict (they change together and one team could plausibly own both, but they have different traffic profiles and no transactional dependency).

## 6. Walkthrough

1. For `OrderService`+`OrderValidationService`, `decide` checks each of the four boolean fields, all `true`: `mergeVotes` increments four times, ending at `4`. Since `4 >= 3`, the method returns `"MERGE"`.
2. For `OrderService`+`RecommendationService`, all four fields are `false`: `mergeVotes` stays `0`. Since `0 <= 1`, the method returns `"SPLIT"`.
3. For `OrderService`+`ShippingService`, `frequentJointChanges` and `oneTeamCanOwnBoth` are `true`, while `similarTraffic` and `needsTransactionalConsistency` are `false`. `mergeVotes` increments twice, ending at `2`. Since `2` is neither `>= 3` nor `<= 1`, the method falls into the middle branch and returns `"BORDERLINE -- needs human judgment"`.
4. The loop prints all three verdicts together, letting an architect or team lead see, at a glance, which candidate pairs are settled and which specifically need further discussion — a far more actionable output than a single blanket judgment about the whole system's granularity.

```
OrderService + OrderValidationService:  4/4 merge signals -> MERGE (clear)
OrderService + RecommendationService:   0/4 merge signals -> SPLIT (clear)
OrderService + ShippingService:         2/4 merge signals -> borderline, needs human judgment
```

## 7. Gotchas & takeaways

> **Gotcha:** these four checks are a decision *aid*, not a formula to blindly automate — the specific weighting (how many "votes" tip a decision) and even which checks matter most can vary by organization and by the specific pair being evaluated. Use this framework to structure and make explicit a discussion that would otherwise happen implicitly and inconsistently, not to remove human judgment from genuinely close calls.

- Right-sizing turns [service granularity](0019-service-granularity-nano-micro-macro-mini-services.md)'s general cost awareness into a concrete, repeatable decision process for each specific pair of candidate service boundaries.
- Four checks — coupling (joint changes), traffic (scaling needs), team ownership, and data consistency needs — each contribute independent evidence toward merging or splitting a given pair.
- A pair where all signals agree is a strong, low-risk decision either way; a pair with conflicting signals genuinely needs human judgment rather than a confident automatic verdict.
- Running this process explicitly, pair by pair, produces more consistent and more defensible granularity decisions across a system than relying purely on individual engineers' intuition.
