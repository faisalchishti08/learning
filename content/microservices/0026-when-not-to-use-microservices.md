---
card: microservices
gi: 26
slug: when-not-to-use-microservices
title: When NOT to use microservices
---

## 1. What it is

Knowing when *not* to use microservices is as important as knowing their benefits. Microservices are a poor fit when: the team is small enough that a monolith's simplicity outweighs any coordination benefit from splitting; the domain's boundaries aren't yet well understood, so any service split is likely to draw the wrong lines; the system has no genuine need for independent scaling or deployment (load is uniform, releases already happen together); or the organization lacks the operational maturity (monitoring, automated deployment, on-call practices) to safely run many independent services. In each of these cases, adopting microservices adds real, measurable cost without a matching benefit.

## 2. Why & when

Every one of the reasons *for* microservices (see [Benefits](0023-benefits-scalability-agility-fault-isolation-tech-diversity.md)) has a mirror-image condition under which it simply doesn't apply. A five-person team building a new product has no cross-team coordination problem to solve — there's only one team. A system whose domain boundaries are still being discovered (a startup iterating on its core business model) risks drawing service boundaries in the wrong place, and refactoring across a wrong service boundary is far more expensive than refactoring across a wrong class boundary within one codebase.

Check these conditions honestly, ideally before adopting microservices, but also periodically for teams already running them: has the domain understanding solidified enough that current service boundaries make sense, or would a monolith-first approach have avoided some now-expensive rework? Is the team's operational maturity actually keeping pace with however many services exist?

## 3. Core concept

Four concrete disqualifying conditions, each with its own diagnostic:

| Condition | Diagnostic question |
|---|---|
| Small team | Would this team's coordination actually improve, or is there only one team to begin with? |
| Unclear domain boundaries | Are the proposed service boundaries based on genuine, tested understanding, or guesses that will likely need to change? |
| No scaling/deployment need | Does any part of this system have a measurably different load or release cadence than the rest? |
| Low operational maturity | Can the team currently deploy, monitor, and safely operate even ONE service reliably? |

If most of these point toward "no," a monolith — possibly a well-structured, modular one — is very likely the better starting point.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four conditions, each a signal microservices are premature: small team, unclear domain, no scaling need, low operational maturity">
  <g font-family="sans-serif">
    <rect x="20" y="20" width="140" height="55" rx="6" fill="#1c2430" stroke="#f0883e"/>
    <text x="90" y="45" fill="#e6edf3" font-size="8" text-anchor="middle">Small team</text>
    <text x="90" y="60" fill="#8b949e" font-size="7" text-anchor="middle">one team, no split need</text>

    <rect x="180" y="20" width="140" height="55" rx="6" fill="#1c2430" stroke="#f0883e"/>
    <text x="250" y="45" fill="#e6edf3" font-size="8" text-anchor="middle">Unclear domain</text>
    <text x="250" y="60" fill="#8b949e" font-size="7" text-anchor="middle">boundaries still guesses</text>

    <rect x="340" y="20" width="140" height="55" rx="6" fill="#1c2430" stroke="#f0883e"/>
    <text x="410" y="45" fill="#e6edf3" font-size="8" text-anchor="middle">No scaling need</text>
    <text x="410" y="60" fill="#8b949e" font-size="7" text-anchor="middle">uniform load/release</text>

    <rect x="500" y="20" width="120" height="55" rx="6" fill="#1c2430" stroke="#f0883e"/>
    <text x="560" y="45" fill="#e6edf3" font-size="8" text-anchor="middle">Low maturity</text>
    <text x="560" y="60" fill="#8b949e" font-size="7" text-anchor="middle">can't run 1 service well</text>
  </g>
  <text x="320" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">most "yes" answers -&gt; a well-structured monolith is the better starting point</text>
</svg>

Four disqualifying conditions; several present at once is a strong signal to stay a monolith.

## 5. Runnable example

Scenario: an automated readiness checker evaluating whether a hypothetical team should adopt microservices, growing from a single check into a full weighted recommendation.

### Level 1 — Basic

```java
// File: ReadinessCheckBasic.java -- a single, simple check
public class ReadinessCheckBasic {
    public static void main(String[] args) {
        int teamSize = 4;
        boolean readyForMicroservices = teamSize >= 8; // a rough heuristic: microservices need MULTIPLE teams to benefit
        System.out.println("team size: " + teamSize + " -- ready for microservices: " + readyForMicroservices);
    }
}
```

**How to run:** `javac ReadinessCheckBasic.java && java ReadinessCheckBasic` (JDK 17+).

Expected output:
```
team size: 4 -- ready for microservices: false
```

A single, crude check based only on team size. It correctly flags a small team as not ready, but it's too narrow — a large team with an unclear domain or no operational maturity could pass this one check while still being a poor fit.

### Level 2 — Intermediate

```java
// File: ReadinessCheckMultipleFactors.java -- check ALL FOUR disqualifying conditions
public class ReadinessCheckMultipleFactors {
    record ReadinessInputs(int teamSize, boolean domainBoundariesUnderstood, boolean hasDifferentiatedLoad, boolean hasAutomatedDeployment) { }

    static java.util.List<String> evaluate(ReadinessInputs inputs) {
        java.util.List<String> concerns = new java.util.ArrayList<>();
        if (inputs.teamSize() < 8) concerns.add("team too small to benefit from independent deployability");
        if (!inputs.domainBoundariesUnderstood()) concerns.add("domain boundaries not yet understood -- risk of wrong service splits");
        if (!inputs.hasDifferentiatedLoad()) concerns.add("no differentiated load/release cadence -- independent scaling offers little benefit");
        if (!inputs.hasAutomatedDeployment()) concerns.add("no automated deployment -- cannot safely operate many services");
        return concerns;
    }

    public static void main(String[] args) {
        ReadinessInputs earlyStartup = new ReadinessInputs(5, false, false, false);
        var concerns = evaluate(earlyStartup);
        System.out.println("concerns found: " + concerns.size());
        for (String c : concerns) System.out.println("  - " + c);
    }
}
```

**How to run:** `javac ReadinessCheckMultipleFactors.java && java ReadinessCheckMultipleFactors` (JDK 17+).

Expected output:
```
concerns found: 4
  - team too small to benefit from independent deployability
  - domain boundaries not yet understood -- risk of wrong service splits
  - no differentiated load/release cadence -- independent scaling offers little benefit
  - no automated deployment -- cannot safely operate many services
```

All four conditions are checked independently, and a genuinely early-stage startup fails every one of them — a clear, specific signal (not just a single number) for why microservices would be premature here.

### Level 3 — Advanced

```java
// File: ReadinessCheckRecommendation.java -- compare TWO teams and produce
// a concrete recommendation for each, based on how many concerns apply.
import java.util.*;

public class ReadinessCheckRecommendation {
    record ReadinessInputs(String teamName, int teamSize, boolean domainBoundariesUnderstood, boolean hasDifferentiatedLoad, boolean hasAutomatedDeployment) { }

    static List<String> evaluate(ReadinessInputs inputs) {
        List<String> concerns = new ArrayList<>();
        if (inputs.teamSize() < 8) concerns.add("team too small");
        if (!inputs.domainBoundariesUnderstood()) concerns.add("domain boundaries unclear");
        if (!inputs.hasDifferentiatedLoad()) concerns.add("no differentiated load");
        if (!inputs.hasAutomatedDeployment()) concerns.add("no automated deployment");
        return concerns;
    }

    static String recommend(ReadinessInputs inputs) {
        int concernCount = evaluate(inputs).size();
        if (concernCount == 0) return "microservices are a reasonable fit";
        if (concernCount <= 2) return "consider monolith-first, revisit once remaining concerns are addressed";
        return "strongly recommend a monolith for now";
    }

    public static void main(String[] args) {
        ReadinessInputs earlyStartup = new ReadinessInputs("EarlyStartup", 5, false, false, false);
        ReadinessInputs establishedCompany = new ReadinessInputs("EstablishedCo", 40, true, true, true);

        for (ReadinessInputs inputs : List.of(earlyStartup, establishedCompany)) {
            List<String> concerns = evaluate(inputs);
            System.out.println(inputs.teamName() + ": " + concerns.size() + " concerns, recommendation: " + recommend(inputs));
        }
    }
}
```

**How to run:** `javac ReadinessCheckRecommendation.java && java ReadinessCheckRecommendation` (JDK 17+).

Expected output:
```
EarlyStartup: 4 concerns, recommendation: strongly recommend a monolith for now
EstablishedCo: 0 concerns, recommendation: microservices are a reasonable fit
```

The production-flavored case: two genuinely different organizations produce genuinely different, actionable recommendations from the exact same evaluation logic. `EarlyStartup`, still discovering its domain with a small team and no deployment automation, gets a clear, specific "not yet" — while `EstablishedCo`, with a large team, understood domain boundaries, differentiated load, and automated deployment already in place, gets a "reasonable fit."

## 6. Walkthrough

1. `evaluate(earlyStartup)` checks each of the four fields on `earlyStartup` in turn: `teamSize()` is `5`, less than `8`, so `"team too small"` is added; `domainBoundariesUnderstood()` is `false`, so `"domain boundaries unclear"` is added; the same happens for the remaining two fields, both `false`. The result is a list of all four concerns.
2. `recommend(earlyStartup)` calls `evaluate` again, gets a list of size `4`, and since `4 > 2`, returns `"strongly recommend a monolith for now"`.
3. `evaluate(establishedCompany)` checks the same four fields on `establishedCompany`: `teamSize()` is `40` (not less than `8`, no concern added), and all three boolean fields are `true` (no concerns added for any of them) — the result is an empty list.
4. `recommend(establishedCompany)` gets a list of size `0`, and since `concernCount == 0`, returns `"microservices are a reasonable fit"`.
5. The final loop prints both organizations' concern counts and recommendations side by side, making the contrast between a premature and a ready organization concrete and specific rather than a vague, general "it depends."

```
EarlyStartup:    teamSize=5 (small), domain=false, load=false, deploy=false -> 4 concerns -> "monolith for now"
EstablishedCo:   teamSize=40, domain=true, load=true, deploy=true          -> 0 concerns -> "reasonable fit"
```

## 7. Gotchas & takeaways

> **Gotcha:** these conditions can change independently over time — a team might grow past the "small team" threshold while still lacking automated deployment, or gain deployment maturity while the domain remains poorly understood. Re-run this kind of readiness check periodically rather than treating a single early "not ready" (or "ready") verdict as permanent.

- Microservices are a poor fit for a small team, an unclear or still-evolving domain, a system with no genuine differentiated scaling or deployment need, or an organization lacking the operational maturity to run many services safely.
- Each disqualifying condition mirrors one of microservices' core benefits — check whether that specific benefit's precondition genuinely holds before assuming the architecture will pay off.
- A concrete, multi-factor readiness check (rather than a single gut-feel judgment) produces a specific, actionable list of what's actually missing, not just a yes/no verdict.
- See [monolith-first strategy](0027-monolith-first-strategy.md) for the concrete alternative: start with a well-structured monolith and extract services only once real boundaries and genuine scaling needs have emerged.
