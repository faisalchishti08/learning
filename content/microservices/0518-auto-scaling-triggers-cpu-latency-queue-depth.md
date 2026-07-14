---
card: microservices
gi: 518
slug: auto-scaling-triggers-cpu-latency-queue-depth
title: "Auto-scaling triggers (CPU, latency, queue depth)"
---

## 1. What it is

**Auto-scaling triggers** are the specific metrics an orchestrator watches to decide when to add or remove service instances automatically — most commonly CPU utilization, request latency (or its close cousin, p99 response time), and queue depth (how much work is waiting to be processed). Instead of a human watching a dashboard and manually scaling a deployment up or down, the orchestrator continuously compares the live metric against a target threshold and adjusts the instance count itself, within configured minimum and maximum bounds.

## 2. Why & when

You configure auto-scaling triggers because manual scaling reacts too slowly to real traffic patterns, and because different services are bottlenecked by different resources:

- **CPU-based triggers** work well for compute-bound services, where request handling genuinely consumes CPU cycles proportional to load — a batch image-resizing service scales cleanly on CPU because CPU usage is a direct, honest proxy for how busy it actually is.
- **Latency-based triggers** work better for services where CPU stays low even under real overload — an I/O-bound service waiting on a slow downstream database might sit at 20% CPU while its response times balloon, because the bottleneck is elsewhere entirely; scaling on CPU here would never trigger, while scaling on latency catches the real problem directly.
- **Queue-depth triggers** suit services fronted by a message queue or work queue — a growing backlog is a direct, leading signal that consumers can't keep up, often visible *before* latency or CPU metrics even move, since a full queue means work is piling up rather than actively causing high CPU.
- **The right trigger (or combination) depends on where the actual bottleneck lives** — picking CPU for an I/O-bound service, or queue depth for a service with no queue in front of it, means the auto-scaler simply never reacts to real overload, silently defeating the entire point of auto-scaling.

## 3. Core concept

Think of a call center deciding when to bring in more staff. Watching agents' "typing speed" (a CPU-like metric) tells you nothing if the real bottleneck is callers stuck on hold — agents might be typing at a leisurely pace while the hold queue balloons, because the actual constraint is call volume, not agent effort. Watching hold-queue length (queue depth) or average wait time (latency) directly measures the thing that actually matters to callers, and triggers staffing decisions on the metric that's actually failing, rather than one that happens to be easy to measure but doesn't reflect the real bottleneck.

Concretely:

1. **A metric is sampled continuously** (CPU%, p95/p99 latency, queue depth) and compared against a configured target — for example, "keep average CPU near 60%" or "keep queue depth under 100."
2. **When the metric exceeds the target for a sustained period** (not a single instantaneous spike — most auto-scalers require the breach to persist across several sampling intervals to avoid reacting to noise), the orchestrator adds instances.
3. **When the metric falls comfortably below the target for a sustained period**, the orchestrator removes instances, down to a configured minimum — never scaling to zero for a service that must stay available.
4. **Scaling has lag**: new instances take time to start, warm up, and start actually absorbing load, so the trigger threshold is usually set with headroom (e.g., scale at 60% CPU, not 95%) so the service survives the ramp-up window without becoming overloaded first.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Different bottlenecks need different auto-scaling triggers: CPU for compute-bound work, latency or queue depth for I/O-bound or queue-fronted work">
  <rect x="20" y="20" width="190" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="115" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">compute-bound service</text>
  <text x="115" y="62" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">trigger: CPU % -&gt; scale</text>

  <rect x="235" y="20" width="190" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="330" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">I/O-bound service (low CPU)</text>
  <text x="330" y="62" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">trigger: p99 latency -&gt; scale</text>

  <rect x="450" y="20" width="190" height="60" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="545" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">queue-fronted consumer</text>
  <text x="545" y="62" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">trigger: queue depth -&gt; scale</text>

  <text x="330" y="115" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">using CPU for the I/O-bound service would show 20% CPU</text>
  <text x="330" y="132" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">even while p99 latency balloons -- the scaler would never trigger</text>
</svg>

The right trigger measures the resource that's actually the bottleneck; a mismatched trigger can leave real overload invisible to the auto-scaler.

## 5. Runnable example

Scenario: a simplified auto-scaler deciding instance count for a queue-backed worker service. We start with a basic CPU-only scaling decision, extend it to also consider queue depth, then handle the hard case: requiring a metric to breach its threshold for multiple consecutive samples (not just one spike) before scaling, to avoid flapping.

### Level 1 — Basic

```java
// File: AutoScalerBasic.java -- a BASIC scaler: decides to scale up
// or down based on a single CPU reading, once, with no history.
public class AutoScalerBasic {
    static String decide(double cpuPercent, double targetCpu) {
        if (cpuPercent > targetCpu) return "SCALE UP";
        if (cpuPercent < targetCpu * 0.5) return "SCALE DOWN";
        return "HOLD";
    }

    public static void main(String[] args) {
        double targetCpu = 60.0;
        double[] samples = {45.0, 75.0, 30.0};
        for (double cpu : samples) {
            System.out.println("CPU=" + cpu + "% -> " + decide(cpu, targetCpu));
        }
    }
}
```

How to run: `java AutoScalerBasic.java`

Each CPU reading is judged in isolation against the target: above target scales up, well below scales down, otherwise holds steady. This is a reasonable first cut, but a single noisy spike (a brief GC pause, a momentary burst) would trigger a scaling action that a sustained trend wouldn't have warranted.

### Level 2 — Intermediate

```java
// File: AutoScalerMultiMetric.java -- extends the scaler to consider
// BOTH CPU and queue depth, since a queue-fronted worker can be
// overloaded (growing backlog) even while CPU looks moderate.
public class AutoScalerMultiMetric {
    static String decide(double cpuPercent, int queueDepth, double targetCpu, int targetQueueDepth) {
        boolean cpuBreach = cpuPercent > targetCpu;
        boolean queueBreach = queueDepth > targetQueueDepth;
        if (cpuBreach || queueBreach) {
            return "SCALE UP (cpuBreach=" + cpuBreach + ", queueBreach=" + queueBreach + ")";
        }
        if (cpuPercent < targetCpu * 0.5 && queueDepth < targetQueueDepth / 4) return "SCALE DOWN";
        return "HOLD";
    }

    public static void main(String[] args) {
        // CPU looks moderate (45%), but the queue is badly backed up (400 vs target 100) --
        // a CPU-only scaler would have missed this entirely.
        System.out.println(decide(45.0, 400, 60.0, 100));
        System.out.println(decide(30.0, 10, 60.0, 100));
    }
}
```

How to run: `java AutoScalerMultiMetric.java`

Scaling up now triggers if *either* metric breaches its threshold, since either one alone indicates real overload for a queue-fronted worker. The first call demonstrates exactly the scenario CPU-only scaling misses: CPU at 45% (below the 60% target) would say "hold," but queue depth at 400 (way over the target of 100) correctly forces `SCALE UP` — the backlog is growing even though CPU doesn't show it, because the bottleneck here is downstream processing capacity, not CPU cycles.

### Level 3 — Advanced

```java
// File: AutoScalerSustained.java -- requires a metric to breach its
// threshold for MULTIPLE CONSECUTIVE samples before scaling, to avoid
// reacting to a single noisy spike (flapping).
import java.util.*;

public class AutoScalerSustained {
    static final int REQUIRED_CONSECUTIVE_BREACHES = 3;
    Deque<Boolean> recentBreaches = new ArrayDeque<>();

    boolean recordSampleAndCheck(double cpuPercent, double targetCpu) {
        boolean breach = cpuPercent > targetCpu;
        recentBreaches.addLast(breach);
        if (recentBreaches.size() > REQUIRED_CONSECUTIVE_BREACHES) recentBreaches.removeFirst();
        // scale up only if we have enough history AND every recent sample breached
        return recentBreaches.size() == REQUIRED_CONSECUTIVE_BREACHES
            && recentBreaches.stream().allMatch(b -> b);
    }

    public static void main(String[] args) {
        AutoScalerSustained scaler = new AutoScalerSustained();
        double targetCpu = 60.0;
        // a brief spike to 90%, then back to normal -- should NOT trigger scaling
        double[] noisySpike = {50.0, 90.0, 45.0, 50.0};
        for (double cpu : noisySpike) {
            boolean scaleUp = scaler.recordSampleAndCheck(cpu, targetCpu);
            System.out.println("sample CPU=" + cpu + "% -> scaleUp=" + scaleUp + " (history=" + scaler.recentBreaches + ")");
        }

        System.out.println("--- now a SUSTAINED overload ---");
        AutoScalerSustained scaler2 = new AutoScalerSustained();
        double[] sustainedOverload = {70.0, 75.0, 80.0, 85.0};
        for (double cpu : sustainedOverload) {
            boolean scaleUp = scaler2.recordSampleAndCheck(cpu, targetCpu);
            System.out.println("sample CPU=" + cpu + "% -> scaleUp=" + scaleUp + " (history=" + scaler2.recentBreaches + ")");
        }
    }
}
```

How to run: `java AutoScalerSustained.java`

`recentBreaches` is a sliding window of the last `REQUIRED_CONSECUTIVE_BREACHES` (3) samples; scaling only triggers once *all three* most recent samples breached the threshold. In the "noisy spike" run, the single 90% reading is surrounded by normal readings, so the window never fills with three consecutive breaches — `scaleUp` stays `false` throughout, correctly ignoring the transient spike. In the "sustained overload" run, CPU stays above 60% for three consecutive samples in a row (75%, 80%, 85% — the window fills with three `true` values once the third sample lands), and `scaleUp` flips to `true` at that point — correctly reacting to a real, sustained trend rather than noise.

## 6. Walkthrough

Trace the "sustained overload" run of `AutoScalerSustained.main` end to end:

1. **Sample 1: CPU=70%.** `recordSampleAndCheck` computes `breach = true` (70 > 60), pushes `true` onto `recentBreaches` (now `[true]`, size 1). Since size (1) != required (3), returns `false` — not enough history yet to confirm a sustained trend.
2. **Sample 2: CPU=75%.** `breach = true`, pushed (`[true, true]`, size 2). Still size != 3, returns `false`.
3. **Sample 3: CPU=80%.** `breach = true`, pushed (`[true, true, true]`, size 3). Now size == 3 *and* every entry is `true` — `recordSampleAndCheck` returns `true`. This is the first sample where the sustained-breach condition is actually met.
4. **Sample 4: CPU=85%.** `breach = true`, pushed; since the deque is now over its cap of 3, `removeFirst()` evicts the oldest entry, keeping the window at exactly 3 (`[true, true, true]`, the most recent three). Still all `true`, so `scaleUp` stays `true` — the sustained condition continues to hold as long as the trend continues.

Contrast with the "noisy spike" run: at sample 2 (the 90% spike), the window becomes `[false, true]` (from `50.0, 90.0`) — size 2, not yet 3, so no decision either way. At sample 3 (back to 45%), the window becomes `[false, true, false]` — size 3, but *not* all `true`, so `scaleUp` returns `false`. The single spike is absorbed into the window and outvoted by the surrounding normal samples, exactly the behavior that prevents flapping on transient noise.

The general shape: a real auto-scaler (Kubernetes HPA, AWS Auto Scaling) applies this same idea via a configured "stabilization window" or evaluation-period count, so a metric has to genuinely trend past its threshold — not just spike once — before the orchestrator commits to the cost and disruption of adding or removing instances.

## 7. Gotchas & takeaways

> **Gotcha:** picking a trigger metric that doesn't reflect the actual bottleneck (CPU for an I/O-bound service, no trigger at all for a queue-fronted worker) means the auto-scaler can look perfectly healthy on its dashboard while real requests are timing out or a backlog silently grows unbounded — the absence of a scaling event is not the same as the absence of overload.

- Match the trigger to the actual bottleneck: CPU for compute-bound work, latency for I/O-bound work where CPU stays low under real overload, queue depth for anything fronted by a work queue.
- Require a sustained breach across multiple samples (not one spike) before scaling, or the system will flap — scaling up and down repeatedly in response to noise, which is disruptive and costly on its own.
- Set trigger thresholds with headroom below the true breaking point, since new instances take real time to start and warm up — scaling "just in time" at 95% CPU usually means the service is already overloaded before help arrives.
- Multiple triggers can and often should combine (as in Level 2) — a service can be simultaneously CPU-bound under one workload and queue-bound under another, and a single-metric scaler will blind-spot whichever isn't being watched.
