---
card: system-design
gi: 223
slug: autoscaling-horizontal-pod-autoscaling
title: Autoscaling (horizontal pod autoscaling)
---

## 1. What it is

**Autoscaling** automatically adjusts the number of running instances of a service based on real-time demand, instead of running a fixed number sized for peak load at all times. **Horizontal Pod Autoscaling (HPA)** is [Kubernetes](0217-kubernetes-pods-deployments-services.md)'s specific mechanism for this: it watches a metric (commonly CPU or memory usage, or a custom metric like request queue length) and adjusts a deployment's replica count up or down to keep that metric near a target value.

## 2. Why & when

Running a fixed number of instances sized for peak traffic wastes money most of the time (most systems are not at peak most of the time) and risks being under-provisioned if actual peak exceeds what was planned for. Autoscaling solves both: capacity grows automatically as real demand grows, and shrinks back down (saving cost) once demand drops, without anyone manually watching dashboards and adjusting replica counts.

Use autoscaling for any service whose load varies meaningfully over time — daily traffic cycles, weekly patterns, unpredictable spikes — which describes most production services. A service with genuinely constant, predictable load gets less benefit from autoscaling and can run a fixed replica count reliably, though even then, autoscaling as a safety net for unexpected spikes is usually still worth the modest added complexity.

## 3. Core concept

- **Target metric and target value.** HPA is configured with a metric (e.g. average CPU utilization across pods) and a target value (e.g. 70%). It continuously compares the current metric against the target and computes how many replicas would bring the average back to the target.
- **Scale-out and scale-in are asymmetric by design.** Scaling out (adding replicas) usually happens quickly, to absorb a load spike before it causes problems. Scaling in (removing replicas) is deliberately slower and more conservative, to avoid "flapping" — rapidly adding and removing replicas in response to normal, brief fluctuations in load.
- **Cooldown/stabilization windows.** HPA waits a period after a scaling action before considering another one, and often looks at a rolling window of recent metric values rather than the single latest reading — this smooths out noisy, short-lived spikes that should not trigger a scaling action.
- **Minimum and maximum replica bounds.** A minimum ensures the service never scales down to zero (or below a safe floor) even during a lull; a maximum caps cost and protects downstream dependencies (like a database) from being overwhelmed by an unbounded number of instances all connecting to it at once.
- **Custom metrics beyond CPU.** CPU is a reasonable default proxy for load, but is not always the right signal — a queue-processing service scales better on queue length, and an API might scale better on requests-per-second or p99 latency directly.

## 4. Diagram

```
   time ---->

   load:    low        low       SPIKE       SPIKE       back to low     low
   replicas: 2          2          2 -> 5      5 (holds     5 -> 2         2
                                    (fast        briefly,     (slow scale-
                                     scale-out)  cooldown)     in, avoids
                                                                flapping)

           HPA control loop, runs continuously:
             1. read current metric (e.g. avg CPU = 85%, target = 70%)
             2. compute desired replicas = current_replicas * (current_metric / target_metric)
             3. respect min/max bounds and cooldown window
             4. update the Deployment's replica count if it changed
```
*Caption: scale-out reacts quickly to rising load; scale-in deliberately lags behind falling load, so a brief dip does not trigger an immediate, wasteful scale-down that then has to scale back out moments later.*

## 5. Runnable example

**Level 1 — Basic.** Compute the desired replica count from a current metric reading and a target, using HPA's actual formula.

**Level 2 — Intermediate.** Run the control loop over a series of metric readings, applying min/max bounds.

**Level 3 — Advanced.** Add asymmetric cooldowns — fast scale-out, slow scale-in with a stabilization window — and show it prevents flapping on a noisy metric series.

```java
// AutoscalingDemo.java
import java.util.*;

public class AutoscalingDemo {

    // ---------- Level 1: the HPA replica-count formula ----------
    static int desiredReplicas(int currentReplicas, double currentMetric, double targetMetric) {
        // This is literally Kubernetes HPA's core formula.
        return (int) Math.ceil(currentReplicas * (currentMetric / targetMetric));
    }

    // ---------- Level 2: control loop with min/max bounds ----------
    static class Autoscaler {
        int currentReplicas;
        int minReplicas, maxReplicas;
        double targetCpuPercent;

        Autoscaler(int startReplicas, int minReplicas, int maxReplicas, double targetCpuPercent) {
            this.currentReplicas = startReplicas;
            this.minReplicas = minReplicas; this.maxReplicas = maxReplicas; this.targetCpuPercent = targetCpuPercent;
        }

        void tick(double observedCpuPercent) {
            int raw = desiredReplicas(currentReplicas, observedCpuPercent, targetCpuPercent);
            int bounded = Math.max(minReplicas, Math.min(maxReplicas, raw));
            if (bounded != currentReplicas) {
                System.out.println("    CPU=" + observedCpuPercent + "% -> raw desired=" + raw +
                    " -> bounded=" + bounded + " (was " + currentReplicas + ")");
                currentReplicas = bounded;
            } else {
                System.out.println("    CPU=" + observedCpuPercent + "% -> stays at " + currentReplicas + " replicas");
            }
        }
    }

    // ---------- Level 3: asymmetric cooldown - fast scale-out, slow scale-in ----------
    static class CooldownAwareAutoscaler extends Autoscaler {
        int ticksSinceLastScaleIn = 0;
        int scaleInCooldownTicks;

        CooldownAwareAutoscaler(int startReplicas, int minReplicas, int maxReplicas,
                                  double targetCpuPercent, int scaleInCooldownTicks) {
            super(startReplicas, minReplicas, maxReplicas, targetCpuPercent);
            this.scaleInCooldownTicks = scaleInCooldownTicks;
        }

        @Override
        void tick(double observedCpuPercent) {
            ticksSinceLastScaleIn++;
            int raw = desiredReplicas(currentReplicas, observedCpuPercent, targetCpuPercent);
            int bounded = Math.max(minReplicas, Math.min(maxReplicas, raw));

            if (bounded > currentReplicas) {
                System.out.println("    CPU=" + observedCpuPercent + "% -> SCALE OUT " +
                    currentReplicas + " -> " + bounded + " (fast, no cooldown)");
                currentReplicas = bounded;
                ticksSinceLastScaleIn = 0; // reset - don't scale in right after scaling out
            } else if (bounded < currentReplicas) {
                if (ticksSinceLastScaleIn < scaleInCooldownTicks) {
                    System.out.println("    CPU=" + observedCpuPercent + "% -> would scale IN to " + bounded +
                        ", but COOLDOWN active (" + ticksSinceLastScaleIn + "/" + scaleInCooldownTicks +
                        " ticks) -> staying at " + currentReplicas);
                } else {
                    System.out.println("    CPU=" + observedCpuPercent + "% -> SCALE IN " +
                        currentReplicas + " -> " + bounded + " (cooldown satisfied)");
                    currentReplicas = bounded;
                    ticksSinceLastScaleIn = 0;
                }
            } else {
                System.out.println("    CPU=" + observedCpuPercent + "% -> stays at " + currentReplicas + " replicas");
            }
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - the core HPA formula:");
        System.out.println("  currentReplicas=2, currentCPU=85%, targetCPU=70% -> desired=" +
            desiredReplicas(2, 85, 70));

        System.out.println("\nLevel 2 - control loop with min=2, max=6 bounds:");
        Autoscaler autoscaler = new Autoscaler(2, 2, 6, 70);
        for (double cpu : new double[]{40, 90, 95, 30, 20}) autoscaler.tick(cpu);

        System.out.println("\nLevel 3 - cooldown-aware autoscaler, noisy metric series (avoids flapping):");
        CooldownAwareAutoscaler cooldownAutoscaler = new CooldownAwareAutoscaler(2, 2, 6, 70, 3);
        double[] noisyReadings = {85, 60, 82, 55, 58, 50, 45};
        for (double cpu : noisyReadings) cooldownAutoscaler.tick(cpu);
    }
}
```

**How to run:** `java AutoscalingDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `desiredReplicas(2, 85, 70)` applies the formula `currentReplicas * (currentMetric / targetMetric)` — `2 * (85/70) = 2.43`, rounded up to `3`. This single formula is the mathematical core of HPA: if CPU is running above target, it scales proportionally to bring the *average* back down toward target.
2. **Level 2:** `autoscaler.tick(40)` computes a raw desired replica count below the current 2 (since 40% is under the 70% target), but `Math.max(minReplicas, ...)` clamps it to the floor of 2 — the printed line shows it stays at 2, not scaling below the configured minimum.
3. `autoscaler.tick(90)` and `autoscaler.tick(95)` each push the raw desired count up; the second of the two shows the replica count growing further as CPU stays high. `autoscaler.tick(30)` and `autoscaler.tick(20)` then bring it back down — each `tick` call is completely independent, reacting only to that one reading, with no memory of the readings before it.
4. **Level 3:** `cooldownAutoscaler.tick(85)` triggers a scale-out immediately (`bounded > currentReplicas`), since scale-out has no cooldown — and it resets `ticksSinceLastScaleIn` to 0, meaning a scale-in cannot happen again until 3 more ticks pass.
5. The next several readings (`60, 82, 55, 58, 50, 45`) fluctuate — some would compute a lower desired replica count than current. Each of these finds `ticksSinceLastScaleIn < scaleInCooldownTicks` (3) and prints `"COOLDOWN active"`, staying at the current replica count instead of scaling in immediately. Only once three full ticks have passed since the last scale-out does a scale-in actually happen — this is exactly the asymmetric behavior the diagram describes: fast to react to rising load, deliberately slow to react to falling load, so a brief dip in the middle of the noisy series does not trigger an immediate scale-down that would likely have to reverse moments later.

## 7. Gotchas & takeaways

> **Gotcha:** autoscaling on CPU alone can miss the real bottleneck — a service that is I/O-bound (waiting on a slow database or downstream call) can show low CPU usage while still being completely overwhelmed and unable to serve requests. Choose the metric that actually reflects the service's real bottleneck, which is sometimes a custom metric like queue depth or in-flight request count, not CPU.

- Always set both a minimum and a maximum replica bound — the minimum protects against scaling to zero during a lull, and the maximum protects downstream dependencies (databases, rate-limited third-party APIs) from being overwhelmed by unbounded scale-out.
- Use asymmetric cooldowns deliberately — fast scale-out to absorb real spikes quickly, slower scale-in to avoid flapping on noisy, short-lived dips, exactly as Level 3 demonstrates.
- Pick the target metric based on what actually constrains the service's capacity, not by defaulting to CPU because it is the easiest one to enable.
- Autoscaling assumes the underlying infrastructure can actually provide new capacity quickly — pair it with fast-starting [containers](0216-containers-images.md) and a [Kubernetes](0217-kubernetes-pods-deployments-services.md) cluster with enough headroom, or the "fast" scale-out in theory becomes slow in practice.
