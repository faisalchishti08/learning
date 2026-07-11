---
card: spring-cloud
gi: 105
slug: sampling
title: "Sampling"
---

## 1. What it is

Sampling is the configurable decision, made once per trace (typically at the root span), about whether that trace's spans are actually recorded and exported to the tracing backend at all — `management.tracing.sampling.probability` controls what fraction of traces get sampled (`1.0` records everything, `0.1` records roughly 10%), trading complete trace coverage for reduced tracing overhead, network traffic, and backend storage cost.

```properties
management.tracing.sampling.probability=0.1
```

```java
// a custom sampler can override the default rate-based decision for specific criteria
@Bean
Sampler alwaysSampleErrors() {
    return Sampler.create(0.1f); // baseline 10%, combined with rate limiting or custom rules as needed
}
```

## 2. Why & when

Recording, exporting, and storing every single span for every single request is expensive at scale — a high-throughput service handling thousands of requests per second would generate a proportional volume of trace data, most of which (the successful, unremarkable requests) provides diminishing diagnostic value once a representative sample already exists. Sampling addresses this directly: the sampling decision is made once at the very start of a trace and propagated to every span across every service the trace touches (this is why the decision must travel *with* the trace context, alongside `traceId` and `spanId`, rather than being re-decided independently by each service), so a sampled trace is recorded completely end to end, and an unsampled trace produces essentially zero tracing overhead anywhere in the chain.

Reach for deliberate sampling configuration when:

- Trace volume at full (100%) sampling would be prohibitively expensive to export and store — a lower probability (1–10% is common for high-throughput production services) preserves representative visibility at a fraction of the cost.
- Development or staging environments benefit from `probability=1.0` (full sampling) precisely because trace volume is naturally low there and complete visibility during active debugging is more valuable than the (negligible, at that scale) storage cost.
- Certain traces are disproportionately valuable regardless of the baseline rate — traces containing an error, or traces exceeding a latency threshold — where a custom sampler (rather than pure uniform-probability sampling) can bias toward always capturing those specific, high-value traces.

## 3. Core concept

```
 sampling decision made ONCE, at the root span (request's origin):
   probability=0.1 -> roughly 1 in 10 traces: SAMPLED = true
                    -> roughly 9 in 10 traces: SAMPLED = false

 the decision PROPAGATES with the trace context to every downstream service:
   root span: SAMPLED=true  --> child span (service B): inherits SAMPLED=true, records fully
   root span: SAMPLED=false --> child span (service B): inherits SAMPLED=false, records NOTHING

 a service NEVER makes its own independent sampling decision for spans within an ALREADY-STARTED trace
 -- doing so would risk exactly the fragmented, inconsistent recording propagation mismatches (previous card) cause
```

Because the decision is fixed at the trace's origin and inherited everywhere downstream, a sampled trace is always complete (every span recorded), and an unsampled trace is always empty (zero spans recorded) — there's no in-between "partially sampled" trace under normal, consistent propagation.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sampling decision made once at the root span for trace one is true so every downstream span for that trace is recorded while the decision for trace two is false so none of its downstream spans are recorded despite an identical call chain">
  <rect x="20" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="95" y="38" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">trace-1 root: SAMPLED</text>
  <text x="95" y="52" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">probability roll: true</text>

  <rect x="240" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="315" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">service B: recorded</text>

  <rect x="460" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="535" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">service C: recorded</text>

  <rect x="20" y="120" width="150" height="40" rx="7" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="95" y="138" fill="#f85149" font-size="7.5" text-anchor="middle" font-family="sans-serif">trace-2 root: NOT sampled</text>
  <text x="95" y="152" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">probability roll: false</text>

  <rect x="240" y="120" width="150" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="315" y="145" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">service B: NOT recorded</text>

  <rect x="460" y="120" width="150" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="535" y="145" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">service C: NOT recorded</text>

  <defs><marker id="a105" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="170" y1="40" x2="240" y2="40" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a105)"/>
  <line x1="390" y1="40" x2="460" y2="40" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a105)"/>
  <line x1="170" y1="140" x2="240" y2="140" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a105)"/>
  <line x1="390" y1="140" x2="460" y2="140" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a105)"/>
</svg>

The exact same call chain, two different outcomes for two different traces — because sampling is decided once, per trace, and inherited consistently downstream.

## 5. Runnable example

The scenario: apply a probabilistic sampler across a large number of simulated traces, propagate the decision consistently down a multi-service call chain, and measure the resulting export volume — then extend with a custom rule that always samples error traces regardless of the baseline probability, mirroring a common production sampling strategy.

### Level 1 — Basic

A basic probabilistic sampler making one decision per trace.

```java
import java.util.*;

public class SamplingLevel1 {
    static class ProbabilisticSampler {
        double probability;
        Random random;
        ProbabilisticSampler(double probability, long seed) { this.probability = probability; this.random = new Random(seed); }
        boolean shouldSample() { return random.nextDouble() < probability; }
    }

    public static void main(String[] args) {
        ProbabilisticSampler sampler = new ProbabilisticSampler(0.1, 7); // sample ~10% of traces

        int sampledCount = 0;
        int totalTraces = 1000;
        for (int i = 0; i < totalTraces; i++) {
            if (sampler.shouldSample()) sampledCount++;
        }

        System.out.println(sampledCount + " of " + totalTraces + " traces sampled (~" + (100.0 * sampledCount / totalTraces) + "%)");
    }
}
```

How to run: `java SamplingLevel1.java`

Roughly 100 of the 1000 simulated traces are sampled, confirming the sampler's long-run behavior converges on the configured `0.1` probability even though each individual trace's outcome is an independent random decision.

### Level 2 — Intermediate

Propagate one trace's sampling decision consistently down a multi-service call chain, and confirm every service in a sampled trace records, while every service in an unsampled trace does not.

```java
import java.util.*;

public class SamplingLevel2 {
    record TraceContext(String traceId, boolean sampled) {}

    static class ProbabilisticSampler {
        double probability;
        Random random;
        ProbabilisticSampler(double probability, long seed) { this.probability = probability; this.random = new Random(seed); }
        boolean shouldSample() { return random.nextDouble() < probability; }
    }

    static int recordedSpanCount = 0;

    // the decision is made ONCE, at the trace's origin -- every downstream service just reads ctx.sampled()
    static void serviceCall(String serviceName, TraceContext ctx) {
        if (ctx.sampled()) {
            recordedSpanCount++;
            System.out.println(serviceName + ": span RECORDED (trace " + ctx.traceId() + ")");
        }
        // if not sampled: this service does NOTHING further -- no println, no recording, near-zero overhead
    }

    public static void main(String[] args) {
        ProbabilisticSampler sampler = new ProbabilisticSampler(0.5, 3);

        for (int traceNum = 1; traceNum <= 4; traceNum++) {
            boolean sampled = sampler.shouldSample(); // decided ONCE per trace, at the root
            TraceContext ctx = new TraceContext("trace-" + traceNum, sampled);

            System.out.println("-- trace-" + traceNum + " sampled=" + sampled + " --");
            serviceCall("gateway", ctx);
            serviceCall("order-service", ctx); // SAME ctx, SAME sampled decision, inherited
            serviceCall("payment-service", ctx);
        }

        System.out.println("total recorded spans across all traces: " + recordedSpanCount);
    }
}
```

How to run: `java SamplingLevel2.java`

For any trace where `sampled` came out `true`, all three `serviceCall` invocations print a recorded-span line (three spans recorded for that trace); for any trace where `sampled` came out `false`, none of the three calls print anything at all — the same `ctx` object, carrying the one decision made at the top, is passed unchanged to every downstream call, guaranteeing all-or-nothing recording per trace.

### Level 3 — Advanced

Add a custom sampling rule: always sample a trace containing an error, regardless of the baseline probability roll — a common production pattern ensuring the traces most worth investigating are never lost to random chance.

```java
import java.util.*;

public class SamplingLevel3 {
    record TraceContext(String traceId, boolean sampled) {}

    static class ProbabilisticSampler {
        double probability;
        Random random;
        ProbabilisticSampler(double probability, long seed) { this.probability = probability; this.random = new Random(seed); }
        boolean shouldSample() { return random.nextDouble() < probability; }
    }

    static int recordedSpanCount = 0;
    static int errorTracesAlwaysCaptured = 0;

    static void serviceCall(String serviceName, TraceContext ctx) {
        if (ctx.sampled()) {
            recordedSpanCount++;
            System.out.println(serviceName + ": span RECORDED (trace " + ctx.traceId() + ")");
        }
    }

    public static void main(String[] args) {
        ProbabilisticSampler baselineSampler = new ProbabilisticSampler(0.1, 11); // low baseline: 10%

        for (int traceNum = 1; traceNum <= 6; traceNum++) {
            boolean baselineDecision = baselineSampler.shouldSample();
            boolean hasError = (traceNum == 3 || traceNum == 5); // simulate two of six traces hitting an error

            // custom rule: an error trace is ALWAYS sampled, overriding an unlucky baseline "false" roll
            boolean finalDecision = baselineDecision || hasError;
            if (hasError && !baselineDecision) errorTracesAlwaysCaptured++;

            TraceContext ctx = new TraceContext("trace-" + traceNum, finalDecision);
            System.out.println("-- trace-" + traceNum + " hasError=" + hasError
                    + " baseline=" + baselineDecision + " final=" + finalDecision + " --");
            serviceCall("gateway", ctx);
            serviceCall("order-service", ctx);
        }

        System.out.println("error traces rescued by the override rule: " + errorTracesAlwaysCaptured);
        System.out.println("total recorded spans: " + recordedSpanCount);
    }
}
```

How to run: `java SamplingLevel3.java`

For `trace-3` and `trace-5` (the simulated error traces), `finalDecision` is forced to `true` via `baselineDecision || hasError` even on iterations where the low-probability `baselineSampler` alone would have rolled `false` — `errorTracesAlwaysCaptured` counts exactly how many of those error traces the override rule actually rescued from being dropped, demonstrating that a well-designed sampling strategy doesn't have to treat every trace uniformly: high-value traces (errors, in this case) can be biased toward guaranteed capture even under an aggressively low baseline rate.

## 6. Walkthrough

Trace the `trace-3` iteration in Level 3 (one of the simulated error traces).

1. `baselineDecision = baselineSampler.shouldSample()` rolls the probabilistic sampler's decision for this trace — with `probability=0.1`, this is very likely (but not certain) to be `false`.
2. `hasError = (traceNum == 3 || traceNum == 5)` evaluates `true` for `traceNum == 3`.
3. `finalDecision = baselineDecision || hasError` — because `hasError` is `true`, this expression evaluates `true` regardless of what `baselineDecision` was (Java's `||` still evaluates the right operand here since it's not short-circuited away — both operands are already computed values, not lazy calls), meaning this trace is guaranteed to be sampled.
4. If `baselineDecision` happened to be `false` (the likely case at a 10% baseline rate), the `if (hasError && !baselineDecision)` check is `true`, so `errorTracesAlwaysCaptured` increments — recording that the override rule, not the baseline probability, is what saved this particular trace from being dropped.
5. `ctx = new TraceContext("trace-3", true)` is constructed with the forced `true` decision, and both `serviceCall` invocations for `"gateway"` and `"order-service"` see `ctx.sampled() == true`, so both print recorded-span lines and both increment `recordedSpanCount`.
6. Without the override rule, this same trace would very likely (roughly 90% of the time, matching the low baseline probability) have been silently dropped — exactly the scenario the override exists to prevent for traces that are disproportionately valuable to have full visibility into.

```
trace-3: hasError=true
  baselineDecision (10% chance of true) -> likely false
  finalDecision = baselineDecision || hasError = false || true = true  <- override kicks in
  errorTracesAlwaysCaptured++            (this trace was RESCUED from being dropped)
  gateway, order-service both recorded   (full trace captured despite the low baseline rate)
```

## 7. Gotchas & takeaways

> **Gotcha:** deciding to sample based on information only known *after* a trace completes (whether it errored, how long it took) is fundamentally different from probabilistic sampling decided at the trace's start — "tail-based sampling" (deciding after the fact) requires buffering every span until the trace's outcome is known before deciding to keep or discard it, which is a meaningfully more complex and resource-intensive architecture than simple "head-based" probabilistic sampling decided once at the root; conflating the two, or assuming a simple probability setting alone can guarantee error traces are always captured, is a common misunderstanding.

- The sampling decision is made once, at a trace's origin, and must propagate unchanged to every downstream service for that trace — this consistency is what guarantees a sampled trace is always complete and an unsampled trace is always fully absent, never partially recorded.
- Lower sampling probabilities reduce tracing overhead and cost roughly proportionally, at the cost of losing visibility into a proportional share of individual requests — the right probability balances representative visibility against acceptable overhead for the specific service's traffic volume.
- Biasing sampling toward high-value traces (errors, high latency) rather than pure uniform randomness, as Level 3 modeled, captures disproportionately useful diagnostic data without requiring a high baseline rate across all traffic — a common and effective refinement over naive uniform-probability sampling alone.
- Development environments commonly run at `probability=1.0` precisely because low traffic volume there makes full sampling cheap, while production services commonly run at a much lower rate (often single-digit percentages) where traffic volume would otherwise make full sampling prohibitively expensive.
