---
card: microservices
gi: 354
slug: sampling-strategies
title: "Sampling strategies"
---

## 1. What it is

**Sampling** in distributed tracing is the decision about which requests get their full [trace](0352-distributed-tracing-concepts-trace-span-context-propagation.md) — all spans, fully recorded and exported — versus which requests are traced minimally or not at all, made necessary because recording and storing a complete trace for every single request at high volume is often too expensive in storage and processing cost to do continuously. A **sampling strategy** is the specific rule used to decide, per request, whether to sample it.

## 2. Why & when

A system handling thousands of requests per second, each producing several spans across several services, would generate an enormous volume of tracing data if every single request were fully recorded — often far more than is practical or affordable to store, ship, and query. Sampling trades completeness for cost: instead of recording every trace, you record a representative subset, cheap enough to store and analyze continuously, while still capturing enough data to understand typical and problematic behavior.

Use head-based sampling (deciding at the start of a trace, often a simple percentage) as a cheap default when you mainly need a representative sample of typical traffic for aggregate analysis. Use tail-based sampling (deciding only after a trace completes, based on its actual outcome) when you specifically care about capturing every error or unusually slow request in full detail, even at low overall traffic volume — since head-based sampling, chosen randomly in advance, will predictably miss most rare, interesting requests simply because they're rare. Many production systems combine both: a low head-based rate for general visibility, plus a tail-based rule that always keeps errors and outliers regardless of the head-based decision.

## 3. Core concept

**Head-based sampling** makes the sample/don't-sample decision at the very start of a trace (commonly: generate a random number, sample if below a threshold like 1%), and that decision is then propagated to every downstream service via the trace context's sampling flag (see [W3C Trace Context / B3](0353-trace-context-w3c-trace-context-b3-headers.md)) — cheap, but blind to how the request actually turns out. **Tail-based sampling** buffers all spans for a trace until it completes, then decides whether to keep or discard the whole trace based on its actual outcome (an error occurred, latency exceeded a threshold) — more accurate for catching the requests you actually care about, but requires buffering complete traces before the keep/discard decision, adding memory and processing cost.

```java
// Head-based: decided BEFORE the request's outcome is known.
boolean sampled = Math.random() < 0.01; // 1% of ALL requests, regardless of outcome

// Tail-based: decided AFTER the request completes, based on its outcome.
boolean keep = trace.hasError() || trace.totalDurationMs() > 1000;
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Head-based sampling decides at the START, before the outcome is known, keeping a random 1 percent. Tail-based sampling buffers the whole trace and decides at the END, keeping errors and slow traces regardless of a random draw">
  <rect x="30" y="20" width="270" height="150" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="165" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Head-based</text>
  <text x="165" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">decide at the START</text>
  <text x="165" y="86" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">random ~1%, outcome unknown</text>
  <text x="165" y="104" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">cheap, but blind to outcome</text>

  <rect x="340" y="20" width="270" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="475" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Tail-based</text>
  <text x="475" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">decide at the END</text>
  <text x="475" y="86" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">keep errors/outliers ALWAYS</text>
  <text x="475" y="104" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">accurate, but needs buffering</text>
</svg>

Head-based sampling decides blindly and cheaply upfront; tail-based sampling decides accurately but only after buffering the full outcome.

## 5. Runnable example

Scenario: a stream of requests with a mix of fast, slow, and erroring ones, first sampled head-based (missing most of the interesting rare cases purely by chance), then fixed with tail-based sampling that reliably captures every error and slow request, and finally combined into a hybrid strategy matching real production practice.

### Level 1 — Basic

```java
// File: HeadBasedSampling.java -- decides to sample BEFORE the request's
// outcome is known, using a fixed low percentage; interesting rare cases
// are missed purely by chance.
import java.util.*;

public class HeadBasedSampling {
    record RequestOutcome(String id, boolean error, long durationMs) {}

    static boolean headBasedDecision() { return Math.random() < 0.10; } // 10%, decided with NO knowledge of outcome

    public static void main(String[] args) {
        List<RequestOutcome> requests = List.of(
                new RequestOutcome("r1", false, 50), new RequestOutcome("r2", false, 45),
                new RequestOutcome("r3", true, 30),   // an ERROR -- but sampling doesn't know that yet
                new RequestOutcome("r4", false, 4500), // a SLOW outlier -- also unknown at decision time
                new RequestOutcome("r5", false, 55));

        int sampledErrors = 0, sampledSlow = 0, totalSampled = 0;
        for (RequestOutcome r : requests) {
            boolean sampled = headBasedDecision(); // BLIND to r.error() and r.durationMs()
            if (sampled) {
                totalSampled++;
                if (r.error()) sampledErrors++;
                if (r.durationMs() > 1000) sampledSlow++;
            }
        }
        System.out.println("Sampled " + totalSampled + "/" + requests.size() + " requests (head-based, ~10% random)");
        System.out.println("Sampled errors: " + sampledErrors + "/1 actual errors, sampled slow: " + sampledSlow + "/1 actual slow requests");
        System.out.println("With only 10% sampled randomly, the ONE error and ONE slow request are OFTEN missed entirely.");
    }
}
```

How to run: `java HeadBasedSampling.java`

`headBasedDecision` makes its keep/discard choice with `Math.random()`, entirely independent of whether the request being decided about is the error or the slow outlier. Across many runs, a request's actual importance (being an error, being slow) has no bearing on whether it happens to be sampled — with only 10% sampled overall, the rare error and rare slow request are frequently among the 90% that get discarded, purely by chance.

### Level 2 — Intermediate

```java
// File: TailBasedSampling.java -- decides AFTER the request completes,
// based on its ACTUAL outcome; every error and every slow request is
// reliably kept, regardless of any random draw.
import java.util.*;

public class TailBasedSampling {
    record RequestOutcome(String id, boolean error, long durationMs) {}

    static boolean tailBasedDecision(RequestOutcome outcome) { // decided AFTER seeing the outcome
        return outcome.error() || outcome.durationMs() > 1000;
    }

    public static void main(String[] args) {
        List<RequestOutcome> requests = List.of(
                new RequestOutcome("r1", false, 50), new RequestOutcome("r2", false, 45),
                new RequestOutcome("r3", true, 30),
                new RequestOutcome("r4", false, 4500),
                new RequestOutcome("r5", false, 55));

        List<String> keptTraces = new ArrayList<>();
        for (RequestOutcome r : requests) {
            if (tailBasedDecision(r)) keptTraces.add(r.id());
        }

        System.out.println("Kept traces (tail-based): " + keptTraces + " -- BOTH the error (r3) AND the slow request (r4) reliably captured.");
        System.out.println("Kept " + keptTraces.size() + "/" + requests.size() + " total -- fewer overall, but ALWAYS the interesting ones.");
    }
}
```

How to run: `java TailBasedSampling.java`

`tailBasedDecision` only runs after each request's full outcome (`error`, `durationMs`) is known, and it deterministically keeps any request that erred or exceeded the latency threshold. Both `r3` (the error) and `r4` (the slow outlier) are reliably kept every single time this runs — unlike head-based sampling's chance-dependent outcome — because the decision is based on the actual result, not a random draw made in ignorance of it.

### Level 3 — Advanced

```java
// File: HybridSamplingStrategy.java -- combines BOTH: a low head-based
// rate captures a representative sample of NORMAL traffic (for aggregate
// analysis), while a tail-based rule ALWAYS additionally keeps errors and
// outliers, regardless of the head-based draw -- matching common
// production practice.
import java.util.*;

public class HybridSamplingStrategy {
    record RequestOutcome(String id, boolean error, long durationMs) {}

    static boolean headBasedDecision() { return Math.random() < 0.10; } // 10% baseline for general visibility
    static boolean tailBasedOverride(RequestOutcome outcome) { return outcome.error() || outcome.durationMs() > 1000; }

    static boolean shouldKeep(RequestOutcome outcome, boolean headDecision) {
        return headDecision || tailBasedOverride(outcome); // EITHER reason is enough to keep it
    }

    public static void main(String[] args) {
        List<RequestOutcome> requests = List.of(
                new RequestOutcome("r1", false, 50), new RequestOutcome("r2", false, 45),
                new RequestOutcome("r3", true, 30),
                new RequestOutcome("r4", false, 4500),
                new RequestOutcome("r5", false, 55));

        List<String> keptForAggregateVisibility = new ArrayList<>();
        List<String> keptForInterestingCases = new ArrayList<>();

        for (RequestOutcome r : requests) {
            boolean headDecision = headBasedDecision();
            boolean tailOverride = tailBasedOverride(r);
            if (shouldKeep(r, headDecision)) {
                if (headDecision) keptForAggregateVisibility.add(r.id());
                if (tailOverride) keptForInterestingCases.add(r.id());
            }
        }

        System.out.println("Kept for aggregate visibility (head-based, random subset): " + keptForAggregateVisibility);
        System.out.println("Kept for interesting cases (tail-based, ALWAYS reliable): " + keptForInterestingCases
                + " -- guaranteed to include r3 (error) and r4 (slow), regardless of the random draw.");
    }
}
```

How to run: `java HybridSamplingStrategy.java`

`shouldKeep` combines both decisions with a logical OR: a request is kept if the head-based random draw selected it, *or* if the tail-based rule flags it as an error or outlier — meaning `r3` and `r4` are always in `keptForInterestingCases` regardless of chance, while `keptForAggregateVisibility` varies run to run based on `headBasedDecision`'s randomness, giving a representative baseline sample of otherwise-uninteresting traffic. This mirrors real production tracing setups, which typically run exactly this combination: a low, cheap baseline rate for general visibility, plus guaranteed capture of the requests that actually matter for debugging.

## 6. Walkthrough

Trace `HybridSamplingStrategy.main` in order (focusing on `r3`, the error). **First**, the loop reaches `r3` (`error=true, durationMs=30`). `headBasedDecision()` is called and returns `true` or `false` at random — assume, for this trace, it happens to return `false` (not selected by the random baseline sample).

**Next**, `tailBasedOverride(r3)` is called: `r3.error()` is `true`, so the `||` short-circuits and the method returns `true` regardless of `durationMs`.

**Then**, `shouldKeep(r3, headDecision=false)` is called: `headDecision || tailBasedOverride(r3)` evaluates `false || true`, which is `true` — `r3` is kept.

**Back in the loop**, since `shouldKeep` returned `true`, the code checks `if (headDecision)` — `false`, so `r3` is *not* added to `keptForAggregateVisibility` — and `if (tailOverride)` — `true`, so `r3` *is* added to `keptForInterestingCases`.

**The same reasoning applies to `r4`** (the slow request, `durationMs=4500`): `tailBasedOverride(r4)` returns `true` because `4500 > 1000`, so regardless of its own random `headDecision`, `r4` is guaranteed to end up in `keptForInterestingCases`.

**For `r1`, `r2`, and `r5`** (all fast, no error), `tailBasedOverride` returns `false` for each, so whether they're kept at all depends entirely on their own random `headDecision` — some runs will include a few of them in `keptForAggregateVisibility`, others won't, but none of them will ever appear in `keptForInterestingCases`, since they never trigger the tail-based override.

```
r3 (error):      headDecision=maybe -> tailOverride=TRUE (error)      -> ALWAYS kept, in keptForInterestingCases
r4 (slow):       headDecision=maybe -> tailOverride=TRUE (>1000ms)    -> ALWAYS kept, in keptForInterestingCases
r1,r2,r5 (normal):headDecision=random -> tailOverride=FALSE           -> kept ONLY if the random draw selects them
```

## 7. Gotchas & takeaways

> A pure head-based sampling strategy at a low rate will, by design, miss most rare error conditions — if errors occur in 0.1% of requests and you sample 1% of traffic at random, you'll capture roughly 1% of those errors, not all of them. If reliably catching every error trace matters (it usually does), a tail-based or hybrid strategy is necessary, not optional.

- Head-based sampling decides at the start of a trace, cheaply, but blind to the eventual outcome — good for a representative baseline of typical traffic.
- Tail-based sampling decides after a trace completes, based on its actual outcome (errors, high latency), reliably capturing the traces that matter most for debugging, at the cost of buffering full trace data before deciding.
- A hybrid approach — a low head-based baseline plus a tail-based override that always keeps errors and outliers — is common production practice, combining cheap aggregate visibility with reliable capture of the interesting cases.
- Sampling decisions and rates interact directly with [metric cardinality](0355-cardinality-of-metrics-labels.md) concerns and with the volume/cost tradeoffs of your tracing backend — tune the rate to your actual traffic volume and storage budget.
