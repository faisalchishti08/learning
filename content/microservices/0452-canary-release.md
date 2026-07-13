---
card: microservices
gi: 452
slug: canary-release
title: "Canary release"
---

## 1. What it is

A **canary release** routes a small percentage of real production traffic to a new version while the rest continues to the stable version, then gradually increases that percentage as confidence grows — checking observed metrics like error rate and latency at each step before advancing. Unlike [blue-green deployment](0451-blue-green-deployment.md)'s all-at-once switch, a canary exposes the new version to real traffic incrementally, so a defect is caught while it's only affecting a small fraction of users, not everyone.

## 2. Why & when

You reach for a canary release when you want real production signal on a new version before it handles all traffic, without exposing every user to a potential defect at once:

- **Smoke tests and staging environments can't fully replicate production.** Real user traffic has data shapes, concurrency patterns, and edge cases that pre-production testing structurally can't reproduce — a canary gets you real signal by exposing the new version to a controlled slice of the real thing.
- **Blast radius scales with the traffic percentage, not with time.** If the new version has a defect, a canary at 5% traffic means roughly 5% of requests are affected while it's being evaluated — compare to a rolling deployment, where a defect isn't caught until it's already live on some fraction of *instances*, potentially serving 100% of traffic on those instances.
- **The ramp itself is the safety mechanism.** Each stage (say 5%, then 25%, then 50%, then 100%) is a checkpoint: advancing only happens if the observed error rate (or other health signal) stays within an acceptable threshold, and a spike at any stage triggers a rollback before the next, larger stage is ever reached.
- **You use this for changes where you want real-traffic validation but can't or don't want to run two complete parallel environments** — canary needs only a traffic-splitting router and a way to observe both versions' metrics separately, which is typically cheaper to operate than full blue-green duplication.

## 3. Core concept

The name comes from the historical practice of miners carrying a caged canary into a mine: the canary was more sensitive to dangerous gas than a human, so if it showed distress, miners knew to retreat before anyone was seriously harmed — a small, controlled exposure that provides an early warning before a much larger, riskier exposure. A canary release applies exactly this idea to traffic: expose a small slice of real users to the new version first, watch closely, and only expand that exposure once it's clearly safe.

Concretely, the mechanics are:

1. **A traffic router splits requests by percentage** between the stable version and the canary version, typically based on a routing key like request count, user ID hash, or a random weighted choice.
2. **The ramp advances in stages**, each stage exposing a larger percentage — a common pattern is something like 5% → 25% → 50% → 100%, though exact stages vary by risk tolerance.
3. **Each stage is gated on an observed health signal**, most commonly error rate, but also latency, resource usage, or business metrics — advancing to the next, larger stage only happens if the current stage's signal stays within an acceptable threshold.
4. **A stage failure triggers rollback, not just a pause.** If a threshold is breached, traffic is routed entirely back to the stable version immediately — the earlier and smaller the stage at which this happens, the fewer users were ever affected.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A canary ramp advances through increasing traffic percentages, checking error rate at each stage, and rolls all traffic back to stable the moment a stage's error rate exceeds threshold">
  <rect x="20" y="30" width="90" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="65" y="55" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">5%</text>
  <text x="65" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OK, advance</text>

  <rect x="130" y="30" width="90" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="175" y="55" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">25%</text>
  <text x="175" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OK, advance</text>

  <rect x="240" y="30" width="90" height="50" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="285" y="55" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">50%</text>
  <text x="285" y="70" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">error spike!</text>

  <rect x="350" y="30" width="90" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="395" y="55" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">100%</text>
  <text x="395" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">never reached</text>

  <line x1="110" y1="55" x2="130" y2="55" stroke="#6db33f" marker-end="url(#a1)"/>
  <line x1="220" y1="55" x2="240" y2="55" stroke="#6db33f" marker-end="url(#a1)"/>
  <line x1="330" y1="55" x2="350" y2="55" stroke="#8b949e" stroke-dasharray="2,2"/>

  <path d="M 285 80 C 200 130 100 130 65 80" fill="none" stroke="#f0883e" stroke-width="2" marker-end="url(#a2)"/>
  <text x="175" y="150" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">automatic rollback: route 100% of traffic back to stable</text>

  <text x="320" y="200" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">only 50% of users were ever briefly exposed, not 100%</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
  </defs>
</svg>

Each ramp stage is gated on an observed error rate; a threshold breach at any stage rolls all traffic back to the stable version rather than advancing further.

## 5. Runnable example

Scenario: an `order-service` canary release from `v1` (stable) to `v2` (canary). We start with the bare percentage-based traffic split, add a multi-stage ramp gated on error rate at each step, then handle the hard case: a bug that only manifests once the canary is handling enough real load (a connection-pool exhaustion issue invisible at low traffic), triggering an automatic rollback mid-ramp.

### Level 1 — Basic

```java
// File: CanaryBasic.java -- models the CORE idea: route a SMALL PERCENTAGE
// of live traffic to the new version (the canary), while the rest keeps
// going to the stable version, and observe the split.
import java.util.*;

public class CanaryBasic {
    static String route(int requestIndex, int canaryPercent) {
        // deterministic stand-in for a weighted random router
        int bucket = requestIndex % 100;
        return bucket < canaryPercent ? "v2 (canary)" : "v1 (stable)";
    }

    public static void main(String[] args) {
        int canaryPercent = 10;
        Map<String, Integer> counts = new LinkedHashMap<>();
        counts.put("v1 (stable)", 0);
        counts.put("v2 (canary)", 0);

        for (int i = 0; i < 100; i++) {
            String target = route(i, canaryPercent);
            counts.merge(target, 1, Integer::sum);
        }

        System.out.println("Routing 100 requests with canaryPercent=" + canaryPercent + "%:");
        counts.forEach((version, count) -> System.out.println("  " + version + ": " + count + " requests"));
    }
}
```

How to run: `java CanaryBasic.java`

`route` assigns each request to a bucket `0-99` and sends it to the canary only if its bucket falls below `canaryPercent` — a deterministic stand-in for a weighted random or hash-based traffic split. With `canaryPercent = 10`, exactly 10 of the 100 simulated requests land on `v2`, and the other 90 stay on the proven `v1` — the entire mechanism a canary release relies on: routing by percentage, not by an all-or-nothing switch.

### Level 2 — Intermediate

```java
// File: CanaryWithRampAndErrorGate.java -- the SAME percentage routing,
// now RAMPED through increasing stages (5% -> 25% -> 50% -> 100%), with
// an error-rate check gating each step before advancing to the next.
import java.util.*;

public class CanaryWithRampAndErrorGate {
    static final double ERROR_RATE_THRESHOLD = 0.03; // 3%
    static final int[] RAMP_STAGES = { 5, 25, 50, 100 };

    // Simulated observed error rate for the canary at a given traffic percentage.
    static double observeErrorRate(int percent) {
        return 0.01; // steady, healthy 1% error rate at every stage in Level 2
    }

    public static void main(String[] args) {
        for (int stage : RAMP_STAGES) {
            double errorRate = observeErrorRate(stage);
            System.out.println("Stage " + stage + "%: canary error rate = " + (errorRate * 100) + "%");

            if (errorRate > ERROR_RATE_THRESHOLD) {
                System.out.println("  error rate exceeds " + (ERROR_RATE_THRESHOLD * 100) + "% threshold -- HALTING ramp at " + stage + "%");
                return;
            }
            System.out.println("  within threshold -- advancing ramp");
        }
        System.out.println("Ramp complete: canary now receives 100% of traffic (promoted to stable).");
    }
}
```

How to run: `java CanaryWithRampAndErrorGate.java`

`RAMP_STAGES` defines the increasing traffic percentages, and the loop only proceeds to the next stage if `observeErrorRate` stays at or below `ERROR_RATE_THRESHOLD`. Since Level 2's simulated error rate is a steady, healthy `1%` at every stage, the ramp sails through all four stages and the canary is fully promoted — the happy path with the gating mechanism now visibly in place.

### Level 3 — Advanced

```java
// File: CanaryWithAutoRollback.java -- the SAME ramp-and-gate logic, now
// handling a PRODUCTION-FLAVORED hard case: the canary looks healthy at
// low traffic percentages but its error rate SPIKES once it receives
// enough real load to expose a concurrency bug -- requiring an automatic
// rollback that routes ALL traffic back to the stable version immediately.
import java.util.*;

public class CanaryWithAutoRollback {
    static final double ERROR_RATE_THRESHOLD = 0.03; // 3%
    static final int[] RAMP_STAGES = { 5, 25, 50, 100 };

    // The canary is fine at low traffic, but a connection-pool exhaustion
    // bug only manifests once it's handling 50% of real traffic.
    static double observeErrorRate(int percent) {
        if (percent < 50) return 0.01;
        return 0.12; // 12% error rate once load crosses the bug's trigger point
    }

    public static void main(String[] args) {
        int currentCanaryPercent = 0;

        for (int stage : RAMP_STAGES) {
            currentCanaryPercent = stage;
            double errorRate = observeErrorRate(stage);
            System.out.println("Stage " + stage + "%: canary error rate = " + (errorRate * 100) + "%");

            if (errorRate > ERROR_RATE_THRESHOLD) {
                System.out.println("  error rate exceeds " + (ERROR_RATE_THRESHOLD * 100)
                        + "% threshold -- AUTOMATIC ROLLBACK: routing 100% of traffic back to stable v1");
                currentCanaryPercent = 0;
                System.out.println("  canary traffic percentage now: " + currentCanaryPercent + "%");
                System.out.println("Final outcome: rollback completed at stage " + stage
                        + "% -- only " + stage + "% of users were ever briefly exposed to the bug, not 100%.");
                return;
            }
            System.out.println("  within threshold -- advancing ramp");
        }
        System.out.println("Ramp complete: canary now receives 100% of traffic (promoted to stable).");
    }
}
```

How to run: `java CanaryWithAutoRollback.java`

`observeErrorRate` models a bug that's completely invisible below 50% traffic (a connection pool sized fine for a fraction of load, but exhausted once real concurrent usage crosses a threshold) — exactly the kind of defect low-percentage stages and pre-production testing structurally cannot surface. The ramp sails through 5% and 25% exactly as in Level 2, then hits the spike at 50% and immediately rolls back, rather than continuing to 100% and exposing every user to a 12% error rate.

## 6. Walkthrough

Trace `CanaryWithAutoRollback.main` in order. **First**, `currentCanaryPercent` starts at `0`, and the loop begins iterating `RAMP_STAGES = {5, 25, 50, 100}`.

**Next**, stage `5`: `currentCanaryPercent` becomes `5`, and `observeErrorRate(5)` returns `0.01` (since `5 < 50`). `0.01` is not greater than `ERROR_RATE_THRESHOLD` (`0.03`), so the code prints "within threshold" and the loop continues to the next stage. Stage `25` behaves identically — `observeErrorRate(25)` also returns `0.01` because `25 < 50` — advancing again.

**Then**, stage `50`: `currentCanaryPercent` becomes `50`, and `observeErrorRate(50)` now takes the `else` branch (`50` is not `< 50`), returning `0.12`. This time `0.12 > 0.03` is `true`, so the rollback branch executes: it prints the threshold-exceeded message, sets `currentCanaryPercent = 0` (routing all traffic back to stable), prints the confirmation, and prints the final summary noting that only stage `50`'s traffic (50% of users) was ever briefly exposed.

**Finally**, the method returns immediately from inside the loop — stage `100` in `RAMP_STAGES` is never reached, meaning no user ever saw 100% canary exposure to the buggy version, which is the entire point of gating each stage individually rather than deploying to everyone at once.

```
Stage 5%: canary error rate = 1.0%
  within threshold -- advancing ramp
Stage 25%: canary error rate = 1.0%
  within threshold -- advancing ramp
Stage 50%: canary error rate = 12.0%
  error rate exceeds 3.0% threshold -- AUTOMATIC ROLLBACK: routing 100% of traffic back to stable v1
  canary traffic percentage now: 0%
Final outcome: rollback completed at stage 50% -- only 50% of users were ever briefly exposed to the bug, not 100%.
```

## 7. Gotchas & takeaways

> A canary ramp is only as good as its error-rate observation window at each stage. Advancing too quickly — checking error rate for only a few seconds at 5% traffic — can miss a slow-building problem (a memory leak, a connection pool draining gradually) that would have shown up given more observation time; the ramp's safety depends as much on *how long* each stage is held as on the percentage itself.

- Route splitting should be sticky per user or session where user experience matters (the same user shouldn't flip between versions request to request) — a simple per-request random split, as shown here for clarity, is fine for stateless backend traffic but can be jarring for user-facing flows.
- The earlier a bad canary is caught, the smaller its blast radius — this is why starting the ramp at a small percentage (5%, not 50%) matters even though it means a slower rollout.
- A canary release and a [feature toggles for deployment decoupling](0454-feature-toggles-for-deployment-decoupling.md) rollout solve a similar-sounding problem differently: canary ramps traffic to a *deployed instance* of new code, while a feature toggle ramps exposure to a *code path* already deployed everywhere — they're often combined, but they operate at different layers.
- Unlike blue-green's atomic all-or-nothing switch (see [blue-green deployment](0451-blue-green-deployment.md)), a canary's gradual ramp means old and new versions serve real traffic simultaneously for the ramp's duration — the new version must be API- and data-compatible with the old one throughout, same as during a rolling deployment.
- Automating the rollback decision (rather than requiring a human to notice and act) is what makes the small-blast-radius promise actually hold under real incident timelines — a canary with only manual rollback is much slower to react than the automated threshold check shown in Level 3.
