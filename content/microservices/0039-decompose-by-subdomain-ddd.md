---
card: microservices
gi: 39
slug: decompose-by-subdomain-ddd
title: Decompose by subdomain (DDD)
---

## 1. What it is

**Decomposing by subdomain** uses Domain-Driven Design's strategic classification of a business domain into three kinds of subdomain: the **core domain** (what makes this business genuinely distinctive and competitive — worth the most investment and your best engineers), **supporting subdomains** (necessary for the business but not itself a competitive differentiator — custom-built, but not where you innovate), and **generic subdomains** (a solved problem shared across many businesses — authentication, payment processing infrastructure, email sending — often better bought or adopted off-the-shelf than built from scratch). Each subdomain becomes a candidate service boundary, but critically, the *classification* also tells you how much investment each one deserves.

## 2. Why & when

Unlike [decomposing by business capability](0038-decompose-by-business-capability.md), which asks "what does the business do," subdomain decomposition asks a sharper question: "which of these things is actually the reason customers choose us, versus necessary infrastructure, versus a completely generic, already-solved problem?" This distinction matters practically: a core-domain service (say, a logistics company's route-optimization engine) deserves your best engineers and significant custom investment, while a generic-subdomain concern (sending transactional emails) is often better handled by an existing service or library than by a team building and maintaining custom code.

Use subdomain classification specifically when deciding not just *where* to draw a boundary but *how much engineering investment* that boundary deserves — a common and costly mistake is investing core-domain-level effort into a generic subdomain (reinventing authentication from scratch) while under-investing in the actual core domain that differentiates the business.

## 3. Core concept

The three-way classification, and its practical consequence:

| Subdomain type | Definition | Investment level |
|---|---|---|
| Core | Your competitive differentiator | High — best engineers, custom-built, iterated on constantly |
| Supporting | Necessary, but not differentiating | Medium — custom-built, but simpler, less iteration |
| Generic | A solved problem, shared across businesses | Low — buy, adopt an existing library/service, or use a standard solution |

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Core subdomains get high investment, supporting subdomains medium investment, generic subdomains low investment via buying or adopting existing solutions">
  <rect x="30" y="30" width="180" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Core</text>
  <text x="120" y="75" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">competitive</text>
  <text x="120" y="88" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">differentiator</text>
  <text x="120" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">HIGH investment</text>

  <rect x="230" y="45" width="170" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="315" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Supporting</text>
  <text x="315" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">MEDIUM investment</text>

  <rect x="420" y="55" width="190" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="515" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Generic</text>
  <text x="515" y="93" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">LOW investment (buy/adopt)</text>
</svg>

Three subdomain types, each warranting a different level of custom engineering investment.

## 5. Runnable example

Scenario: classifying a delivery company's subdomains, first as a flat unclassified list, then classified into core/supporting/generic, then used to drive a concrete build-vs-buy recommendation per subdomain.

### Level 1 — Basic

```java
// File: FlatSubdomainList.java -- subdomains listed WITHOUT classification
public class FlatSubdomainList {
    public static void main(String[] args) {
        String[] subdomains = { "RouteOptimization", "Authentication", "DriverScheduling", "EmailNotifications" };
        System.out.println("Subdomains identified (unclassified):");
        for (String s : subdomains) System.out.println("  - " + s);
    }
}
```

**How to run:** `javac FlatSubdomainList.java && java FlatSubdomainList` (JDK 17+).

Expected output:
```
Subdomains identified (unclassified):
  - RouteOptimization
  - Authentication
  - DriverScheduling
  - EmailNotifications
```

A flat list gives no guidance on where to focus engineering investment — all four subdomains look equally important at this stage.

### Level 2 — Intermediate

```java
// File: ClassifiedSubdomains.java -- classify each subdomain into
// core, supporting, or generic
import java.util.*;

public class ClassifiedSubdomains {
    enum SubdomainType { CORE, SUPPORTING, GENERIC }
    record Subdomain(String name, SubdomainType type) { }

    public static void main(String[] args) {
        List<Subdomain> subdomains = List.of(
            new Subdomain("RouteOptimization", SubdomainType.CORE),      // THE thing this delivery company competes on
            new Subdomain("DriverScheduling", SubdomainType.SUPPORTING), // necessary, but not the differentiator
            new Subdomain("Authentication", SubdomainType.GENERIC),      // a solved problem, same for almost any company
            new Subdomain("EmailNotifications", SubdomainType.GENERIC)   // also a solved, generic problem
        );

        for (Subdomain s : subdomains) System.out.println(s.name() + ": " + s.type());
    }
}
```

**How to run:** `javac ClassifiedSubdomains.java && java ClassifiedSubdomains` (JDK 17+).

Expected output:
```
RouteOptimization: CORE
DriverScheduling: SUPPORTING
Authentication: GENERIC
EmailNotifications: GENERIC
```

Each subdomain now has an explicit classification, based on whether it's what the company actually competes on (`RouteOptimization`), necessary infrastructure (`DriverScheduling`), or a widely-solved problem (`Authentication`, `EmailNotifications`).

### Level 3 — Advanced

```java
// File: InvestmentRecommendation.java -- turn the classification into a
// CONCRETE build-vs-buy recommendation and engineering allocation per subdomain.
import java.util.*;

public class InvestmentRecommendation {
    enum SubdomainType { CORE, SUPPORTING, GENERIC }
    record Subdomain(String name, SubdomainType type) { }

    static String recommend(Subdomain s) {
        return switch (s.type()) {
            case CORE -> "BUILD custom, assign your BEST engineers, invest heavily and iterate continuously";
            case SUPPORTING -> "BUILD custom, but keep it simple -- necessary, not a place to over-invest";
            case GENERIC -> "BUY or ADOPT an existing solution -- building this from scratch wastes engineering effort on a solved problem";
        };
    }

    public static void main(String[] args) {
        List<Subdomain> subdomains = List.of(
            new Subdomain("RouteOptimization", SubdomainType.CORE),
            new Subdomain("DriverScheduling", SubdomainType.SUPPORTING),
            new Subdomain("Authentication", SubdomainType.GENERIC),
            new Subdomain("EmailNotifications", SubdomainType.GENERIC)
        );

        Map<SubdomainType, Integer> countByType = new EnumMap<>(SubdomainType.class);
        for (Subdomain s : subdomains) {
            System.out.println(s.name() + " (" + s.type() + "): " + recommend(s));
            countByType.merge(s.type(), 1, Integer::sum);
        }
        System.out.println("Engineering effort should be allocated in that priority order: " + countByType.getOrDefault(SubdomainType.CORE, 0) + " core, " + countByType.getOrDefault(SubdomainType.SUPPORTING, 0) + " supporting, " + countByType.getOrDefault(SubdomainType.GENERIC, 0) + " generic (buy where possible)");
    }
}
```

**How to run:** `javac InvestmentRecommendation.java && java InvestmentRecommendation` (JDK 17+).

Expected output:
```
RouteOptimization (CORE): BUILD custom, assign your BEST engineers, invest heavily and iterate continuously
DriverScheduling (SUPPORTING): BUILD custom, but keep it simple -- necessary, not a place to over-invest
Authentication (GENERIC): BUY or ADOPT an existing solution -- building this from scratch wastes engineering effort on a solved problem
EmailNotifications (GENERIC): BUY or ADOPT an existing solution -- building this from scratch wastes engineering effort on a solved problem
```

The production-flavored payoff: `recommend` turns an abstract classification into a concrete, actionable instruction per subdomain — most usefully, it flags that `Authentication` and `EmailNotifications`, despite being real subdomains the business genuinely needs, are candidates for buying or adopting an existing solution rather than custom engineering effort, freeing that effort for `RouteOptimization`, the subdomain that actually matters competitively.

## 6. Walkthrough

1. The loop iterates each `Subdomain` in `subdomains`, calling `recommend(s)` for each one.
2. For `RouteOptimization`, `s.type()` is `CORE`, so the `switch` expression's `case CORE` branch returns the "build custom, best engineers" recommendation.
3. For `DriverScheduling`, `s.type()` is `SUPPORTING`, matching the "build custom, but keep it simple" branch.
4. For `Authentication` and `EmailNotifications`, `s.type()` is `GENERIC` in both cases, so both get the "buy or adopt" recommendation — the same conclusion reached independently for two unrelated subdomains, simply because both share the same classification.
5. `countByType.merge(s.type(), 1, Integer::sum)` tallies how many subdomains fall into each category as the loop proceeds, ending with `CORE=1, SUPPORTING=1, GENERIC=2`.
6. The final print summarizes the whole classification's practical conclusion: engineering priority should go to the one core subdomain first, with the two generic subdomains ideally not consuming custom engineering effort at all.

```
RouteOptimization  -> CORE       -> build, best engineers, heavy investment
DriverScheduling   -> SUPPORTING -> build, simple, moderate investment
Authentication     -> GENERIC    -> buy/adopt, minimal custom investment
EmailNotifications -> GENERIC    -> buy/adopt, minimal custom investment
```

## 7. Gotchas & takeaways

> **Gotcha:** subdomain classification is specific to *your* business, not universal — `Authentication` is generic for a delivery company, but for a company whose actual product *is* an identity/authentication platform, `Authentication` would be their core domain, deserving the highest investment. Never copy another company's classification wholesale; always classify based on what specifically makes your business competitive.

- Subdomain decomposition classifies each part of the domain as core (your competitive differentiator), supporting (necessary but not differentiating), or generic (a solved problem, better bought than built).
- Unlike capability-based decomposition, subdomain classification directly informs how much engineering investment each resulting service deserves, not just where its boundary should sit.
- A common, costly mistake is over-investing in generic subdomains (reinventing solved problems) while under-investing in the actual core domain that differentiates the business competitively.
- Re-evaluate classification periodically — a subdomain that was generic at one point (a simple internal search feature) can become core if the business's competitive strategy shifts to focus on it.
