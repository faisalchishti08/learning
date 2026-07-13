---
card: microservices
gi: 448
slug: horizontal-pod-autoscaling
title: "Horizontal Pod Autoscaling"
---

## 1. What it is

**Horizontal Pod Autoscaling (HPA)** is a Kubernetes control loop that automatically adjusts the replica count of a [Deployment](0447-pods-deployments-services-ingress.md) based on observed metrics — most commonly CPU or memory utilization, but also custom or external metrics like queue depth or requests-per-second. "Horizontal" distinguishes it from *vertical* scaling (giving one Pod more CPU/memory): HPA changes *how many* Pods exist, not how big any single Pod is. It's the same reconciliation idea from [container orchestration (Kubernetes) concepts](0446-container-orchestration-kubernetes-concepts.md), just applied to a computed *desired replica count* instead of a fixed one.

## 2. Why & when

You need HPA the moment a service's load varies enough that a fixed replica count is either wasteful most of the time or insufficient at peak:

- **Fixed replica counts force a bad trade-off.** Size for peak load, and you pay for idle capacity most of the day. Size for average load, and requests queue up or fail during traffic spikes. HPA lets the replica count track actual demand instead of a guess.
- **Traffic patterns are rarely flat.** A checkout service might see 10x its baseline load during a sale; a batch-triggered service might see near-zero load overnight. HPA scales up ahead of sustained demand and scales back down once it passes, within bounds you configure.
- **Manual scaling is too slow.** By the time a human notices elevated latency, checks a dashboard, and manually bumps replica count, the spike may already be causing failures. An automated control loop reacts continuously, on the order of seconds.
- **You should configure HPA for any service with variable load and a horizontally scalable design** — which, per [twelve-factor app principles](0442-twelve-factor-app-principles.md), a stateless microservice generally is. Services with meaningfully constant load can reasonably run with a fixed replica count and skip HPA.

## 3. Core concept

Think of HPA like cruise control that also adds or removes passenger cars from a train based on how crowded each car is. If the average car is packed far beyond comfortable capacity, the system couples on more cars; if cars are running mostly empty, it uncouples some — but it doesn't do this car-by-car on every single reading, because trains (and services) shouldn't be jolting passengers by constantly attaching and detaching cars every time crowding fluctuates for a moment.

Concretely, the mechanics are:

1. **A metrics source** (CPU utilization, memory, or a custom metric) is sampled periodically for the Pods behind a Deployment.
2. **A formula computes desired replicas** from current replicas and the ratio of observed to target utilization: roughly `desiredReplicas = ceil(currentReplicas * currentUtilization / targetUtilization)`. If utilization is at exactly the target, no change is needed; above target, scale up; below target, scale down.
3. **`minReplicas` and `maxReplicas` bounds** clamp the computed value, so autoscaling can never scale a service to zero (losing it entirely) or beyond whatever capacity or cost ceiling you've set.
4. **A stabilization window prevents flapping.** Scaling up immediately protects availability, but scaling down immediately on every momentarily-low reading causes the replica count to oscillate — scale down, traffic ticks up again, scale back up, repeat. Real HPA implementations require a period of consistently low utilization before actually scaling down, while still reacting to scale-up conditions quickly.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HPA reads utilization metrics from Pods, computes a desired replica count clamped between min and max, and asks the Deployment to reconcile toward it, scaling up immediately but scaling down only after a stabilization window">
  <rect x="20" y="100" width="150" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="95" y="125" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Metrics</text>
  <text x="95" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CPU / memory / custom</text>

  <rect x="230" y="90" width="180" height="80" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="115" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">HPA controller</text>
  <text x="320" y="132" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">desired = ceil(current * util/target)</text>
  <text x="320" y="147" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">clamp to [min, max]</text>

  <rect x="470" y="100" width="150" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="545" y="125" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Deployment</text>
  <text x="545" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reconciles Pod count</text>

  <line x1="170" y1="130" x2="230" y2="130" stroke="#79c0ff" marker-end="url(#a1)"/>
  <line x1="410" y1="130" x2="470" y2="130" stroke="#f0883e" marker-end="url(#a2)"/>

  <text x="320" y="200" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">scale UP: applied immediately</text>
  <text x="320" y="218" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">scale DOWN: only after N consecutive low readings</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
  </defs>
</svg>

The controller computes a desired replica count from live metrics, clamps it to configured bounds, then asks the Deployment to reconcile toward it — scaling up fast, scaling down cautiously.

## 5. Runnable example

Scenario: an `order-service` behind HPA, targeting 50% CPU utilization. We start with the bare scaling formula, add min/max bounds so it can never over- or under-shoot configured limits, then handle the hard case: oscillating load that would cause constant flapping under a naive always-react policy, fixed by scaling up immediately but requiring a stabilization window before scaling down.

### Level 1 — Basic

```java
// File: HpaBasic.java -- models the CORE HPA formula: given current
// replicas and current CPU utilization vs a target, compute how many
// replicas SHOULD exist to bring utilization back to the target.
public class HpaBasic {
    static int desiredReplicas(int currentReplicas, double currentUtilizationPct, double targetUtilizationPct) {
        double ratio = currentUtilizationPct / targetUtilizationPct;
        return (int) Math.ceil(currentReplicas * ratio);
    }

    public static void main(String[] args) {
        int currentReplicas = 2;
        double targetUtilizationPct = 50.0;

        double[] observedUtilization = { 50.0, 90.0, 30.0 };
        for (double util : observedUtilization) {
            int desired = desiredReplicas(currentReplicas, util, targetUtilizationPct);
            System.out.println("current=" + currentReplicas + " observedCPU=" + util + "% target=" + targetUtilizationPct
                    + "% -> desiredReplicas=" + desired);
        }
    }
}
```

How to run: `java HpaBasic.java`

The formula scales replicas proportionally to how far utilization is from target: at exactly 50% (the target) with 2 replicas, desired stays at 2. At 90% (1.8x target), desired jumps to `ceil(2 * 1.8) = 4`. At 30% (0.6x target), desired would drop to `ceil(2 * 0.6) = 2` (unchanged here since it rounds up to the same value) — the mechanical core of HPA, with no bounds or smoothing yet.

### Level 2 — Intermediate

```java
// File: HpaWithBounds.java -- the SAME formula, now clamped to a
// configured [minReplicas, maxReplicas] range so autoscaling can never
// scale to zero (losing the service) or beyond the cluster's budget.
public class HpaWithBounds {
    static int minReplicas = 2;
    static int maxReplicas = 6;

    static int desiredReplicas(int currentReplicas, double currentUtilizationPct, double targetUtilizationPct) {
        double ratio = currentUtilizationPct / targetUtilizationPct;
        int raw = (int) Math.ceil(currentReplicas * ratio);
        int clamped = Math.max(minReplicas, Math.min(maxReplicas, raw));
        if (clamped != raw) {
            System.out.println("  (raw computed " + raw + ", clamped to [" + minReplicas + "," + maxReplicas + "] -> " + clamped + ")");
        }
        return clamped;
    }

    public static void main(String[] args) {
        int currentReplicas = 2;
        double targetUtilizationPct = 50.0;

        double[] observedUtilization = { 10.0, 400.0, 50.0 };
        for (double util : observedUtilization) {
            int desired = desiredReplicas(currentReplicas, util, targetUtilizationPct);
            System.out.println("current=" + currentReplicas + " observedCPU=" + util + "% -> desiredReplicas=" + desired);
            currentReplicas = desired;
        }
    }
}
```

How to run: `java HpaWithBounds.java`

A near-idle reading of 10% would compute a raw desired count of 1 (`ceil(2 * 0.2) = 1`), but `minReplicas = 2` clamps it back up — HPA never scales a service out of existence just because it's briefly quiet. A spike to 400% would compute a raw desired count of 16, but `maxReplicas = 6` clamps it down — protecting the cluster (and the budget) from an unbounded scale-out, even under an extreme spike.

### Level 3 — Advanced

```java
// File: HpaWithStabilization.java -- the SAME clamped formula, now
// handling a PRODUCTION-FLAVORED hard case: load that oscillates tick to
// tick. Scaling down immediately on every low reading causes constant
// flapping (scale down, then immediately back up, over and over). A real
// HPA scales UP immediately (to protect availability) but only scales DOWN
// after a stabilization window of consistently low readings.
import java.util.*;

public class HpaWithStabilization {
    static final int MIN_REPLICAS = 2;
    static final int MAX_REPLICAS = 6;
    static final double TARGET_UTIL = 50.0;
    static final int SCALE_DOWN_STABILIZATION_TICKS = 3;

    static int rawDesired(int currentReplicas, double utilizationPct) {
        double ratio = utilizationPct / TARGET_UTIL;
        int raw = (int) Math.ceil(currentReplicas * ratio);
        return Math.max(MIN_REPLICAS, Math.min(MAX_REPLICAS, raw));
    }

    public static void main(String[] args) {
        double[] utilizationOverTime = { 90, 20, 85, 15, 90, 10, 10, 10, 10 };

        System.out.println("--- naive: scale down immediately on every low reading ---");
        int naiveReplicas = 2;
        int naiveScaleEvents = 0;
        for (int tick = 0; tick < utilizationOverTime.length; tick++) {
            int desired = rawDesired(naiveReplicas, utilizationOverTime[tick]);
            if (desired != naiveReplicas) {
                System.out.println("tick " + tick + ": util=" + utilizationOverTime[tick] + "% -> " + naiveReplicas + " -> " + desired);
                naiveScaleEvents++;
                naiveReplicas = desired;
            }
        }
        System.out.println("naive total scale events: " + naiveScaleEvents);

        System.out.println();
        System.out.println("--- stabilized: scale up immediately, scale down only after "
                + SCALE_DOWN_STABILIZATION_TICKS + " consecutive low ticks ---");
        int stableReplicas = 2;
        int stableScaleEvents = 0;
        int consecutiveLowTicks = 0;
        for (int tick = 0; tick < utilizationOverTime.length; tick++) {
            int desired = rawDesired(stableReplicas, utilizationOverTime[tick]);

            if (desired > stableReplicas) {
                System.out.println("tick " + tick + ": util=" + utilizationOverTime[tick] + "% -> SCALE UP " + stableReplicas + " -> " + desired);
                stableReplicas = desired;
                stableScaleEvents++;
                consecutiveLowTicks = 0;
            } else if (desired < stableReplicas) {
                consecutiveLowTicks++;
                if (consecutiveLowTicks >= SCALE_DOWN_STABILIZATION_TICKS) {
                    System.out.println("tick " + tick + ": util=" + utilizationOverTime[tick] + "% -> SCALE DOWN " + stableReplicas + " -> " + desired
                            + " (after " + consecutiveLowTicks + " consecutive low ticks)");
                    stableReplicas = desired;
                    stableScaleEvents++;
                    consecutiveLowTicks = 0;
                } else {
                    System.out.println("tick " + tick + ": util=" + utilizationOverTime[tick] + "% -> low reading #" + consecutiveLowTicks
                            + ", holding at " + stableReplicas + " (stabilization window not yet met)");
                }
            } else {
                consecutiveLowTicks = 0;
            }
        }
        System.out.println("stabilized total scale events: " + stableScaleEvents);
    }
}
```

How to run: `java HpaWithStabilization.java`

The same `utilizationOverTime` sequence is fed through two policies. The naive policy reacts to every single reading, scaling up and down repeatedly as utilization oscillates between high and low ticks — six scale events for nine ticks of input. The stabilized policy still scales up immediately whenever `desired > stableReplicas` (protecting availability without delay), but only commits a scale-down once `consecutiveLowTicks` reaches `SCALE_DOWN_STABILIZATION_TICKS`, resetting that counter any time a higher reading arrives — producing far fewer, more deliberate scaling actions from identical input.

## 6. Walkthrough

Trace the stabilized loop in `HpaWithStabilization.main` in order. **First**, `stableReplicas = 2` and `consecutiveLowTicks = 0`.

**Next**, tick 0 reads `util=90`. `rawDesired(2, 90)` computes `ceil(2 * 90/50) = 4`, clamped within bounds to `4`. Since `4 > 2`, this is a scale-up: it applies immediately, `stableReplicas` becomes `4`, and `consecutiveLowTicks` resets to `0`.

**Then**, tick 1 reads `util=20`. `rawDesired(4, 20)` computes `ceil(4 * 20/50) = 2`, which is less than the current `4` — a candidate scale-down. `consecutiveLowTicks` increments to `1`, which is below the `3`-tick stabilization threshold, so the code holds at `4` instead of scaling down. Tick 2 (`util=85`) immediately overrides this: `rawDesired(4, 85) = ceil(4*1.7) = 7`, clamped to `6` (max), which is `> 4`, so it scales up right away to `6` and resets `consecutiveLowTicks` to `0` — the one low reading from tick 1 never accumulated toward anything.

**Ticks 3 and 5** (`util=15`, then `util=10`) each compute a desired value below `6` and increment `consecutiveLowTicks` to `1`, then `2` — note tick 4 (`util=90`) computes a raw desired of `11`, clamped to the already-current `6`, so it's treated as "no change" and doesn't reset the counter, since `stableReplicas` was already at its max. **Finally**, tick 6 (`util=10`) pushes `consecutiveLowTicks` to `3`, meeting the threshold — tick 7 (`util=10`) also computes a low desired count, and by then `consecutiveLowTicks` reaches `3` and the scale-down to `2` finally commits.

```
--- naive: scale down immediately on every low reading ---
tick 0: util=90.0% -> 2 -> 4
tick 1: util=20.0% -> 4 -> 2
tick 2: util=85.0% -> 2 -> 4
tick 3: util=15.0% -> 4 -> 2
tick 4: util=90.0% -> 2 -> 4
tick 5: util=10.0% -> 4 -> 2
naive total scale events: 6

--- stabilized: scale up immediately, scale down only after 3 consecutive low ticks ---
tick 0: util=90.0% -> SCALE UP 2 -> 4
tick 1: util=20.0% -> low reading #1, holding at 4 (stabilization window not yet met)
tick 2: util=85.0% -> SCALE UP 4 -> 6
tick 3: util=15.0% -> low reading #1, holding at 6 (stabilization window not yet met)
tick 5: util=10.0% -> low reading #1, holding at 6 (stabilization window not yet met)
tick 6: util=10.0% -> low reading #2, holding at 6 (stabilization window not yet met)
tick 7: util=10.0% -> SCALE DOWN 6 -> 2 (after 3 consecutive low ticks)
stabilized total scale events: 3
```

## 7. Gotchas & takeaways

> A stabilization window that only guards scale-down (not scale-up) is a deliberate asymmetry, not an oversight: reacting slowly to rising load risks dropped requests and cascading latency right when the service needs capacity most, while reacting slowly to falling load only costs a little extra spend on Pods that are briefly idle — the two mistakes have very different costs, so the policy should be asymmetric too.

- The core formula (`desiredReplicas = ceil(current * util/target)`) is proportional, not a fixed step — a bigger gap between observed and target utilization produces a bigger jump in replica count, converging faster than a naive "add one, remove one" policy.
- Always set `minReplicas` above zero for any service that must stay available, and set `maxReplicas` to whatever ceiling your cluster capacity or budget actually allows — an unclamped autoscaler is one traffic spike away from either outage or runaway cost.
- Without a stabilization window on scale-down, oscillating load causes constant Pod churn — extra scheduling overhead, cold-start latency on every new Pod (see [graceful startup & shutdown](0444-graceful-startup-shutdown.md)), and noisy scaling events that make real incidents harder to spot in logs.
- HPA scales the Pod count behind a Service; it doesn't change what each Pod reads at startup — that's the concern of [ConfigMaps & Secrets](0449-configmaps-secrets.md).
- CPU/memory-based HPA is the simplest starting point, but custom or external metrics (queue depth, requests-per-second) often track real load more accurately than CPU alone, especially for I/O-bound services.
