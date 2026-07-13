---
card: microservices
gi: 358
slug: four-golden-signals-latency-traffic-errors-saturation
title: "Four golden signals (latency, traffic, errors, saturation)"
---

## 1. What it is

The **four golden signals** (from Google's Site Reliability Engineering practice) are **latency** (how long requests take), **traffic** (how much demand the system is experiencing), **errors** (the rate of failed requests), and **saturation** (how "full" the system is, in terms of its most constrained resource). It's essentially the [RED method](0356-red-method-rate-errors-duration.md)'s three request-facing signals (duration, rate, errors — renamed latency, traffic, errors) plus one resource-facing signal (saturation) folded in from the [USE method](0357-use-method-utilization-saturation-errors.md), giving a single, slightly broader standard checklist for any service's dashboard.

## 2. Why & when

RED alone (rate, errors, duration) covers a service from the request side well, but omits any signal about *why* a service might be about to degrade — a service can still show acceptable rate, errors, and duration right up until the moment its most constrained resource saturates and things fall apart quickly. The four golden signals close this gap by explicitly including saturation as a fourth, mandatory dashboard signal, so a team watching a service's health isn't blindsided by a resource quietly approaching its limit even while request-level metrics still look fine.

Use the four golden signals as the minimum dashboard for any production service, request-driven or not — this framing is broad enough to apply even to background workers or batch processors that don't have a clean "request rate" the way an API does (traffic there might be "jobs processed per minute," and saturation might be "queue depth"). It's a close cousin of RED with saturation folded in, and pairs with the [SLI/SLO/SLA](0359-sli-slo-sla-error-budgets.md) framework, where these four signals commonly become the specific SLIs a team defines targets against.

## 3. Core concept

Latency should be tracked as a distribution (percentiles), exactly as in RED, since an average hides tail latency. Traffic is a demand measure appropriate to the service's own nature (requests/sec for an API, messages/sec for a consumer, jobs/min for a batch processor). Errors is the failure rate or percentage. Saturation is the utilization of whatever resource is the service's actual bottleneck — CPU, memory, a connection pool, a queue depth — and, critically, it's the signal most likely to predict an incident *before* the other three visibly degrade.

```java
record GoldenSignals(double latencyP99Ms, double trafficPerSecond, double errorPercentage, double saturationPercentage) {}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four panels: Latency (p99 response time), Traffic (demand rate), Errors (failure percentage), Saturation (how full the most constrained resource is) -- one dashboard, four signals">
  <rect x="15" y="20" width="145" height="130" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="87" y="45" fill="#79c0ff" font-size="10.5" text-anchor="middle" font-family="sans-serif">Latency</text>
  <text x="87" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">p99 response time</text>

  <rect x="170" y="20" width="145" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="242" y="45" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">Traffic</text>
  <text x="242" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">demand rate</text>

  <rect x="325" y="20" width="145" height="130" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="397" y="45" fill="#f85149" font-size="10.5" text-anchor="middle" font-family="sans-serif">Errors</text>
  <text x="397" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">% failed</text>

  <rect x="480" y="20" width="145" height="130" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="552" y="45" fill="#f0883e" font-size="10.5" text-anchor="middle" font-family="sans-serif">Saturation</text>
  <text x="552" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">how full, resource-wise</text>
</svg>

Four signals on one dashboard give both a request-facing view (latency, traffic, errors) and an early-warning resource view (saturation).

## 5. Runnable example

Scenario: a service dashboard tracking only three RED-style signals that look acceptable right up until a sudden failure, then extended with the fourth signal (saturation) that would have predicted the failure in advance, and finally combined into a single composite health check that a team could actually alert on.

### Level 1 — Basic

```java
// File: ThreeSignalsOnlyMissWarning.java -- only latency, traffic, and
// errors are tracked; all look ACCEPTABLE right up until a sudden failure.
import java.util.*;

public class ThreeSignalsOnlyMissWarning {
    record Snapshot(int t, double latencyP99Ms, double trafficPerSec, double errorPct) {}
    static List<Snapshot> history = new ArrayList<>();

    public static void main(String[] args) {
        history.add(new Snapshot(1, 80, 100, 0.1));
        history.add(new Snapshot(2, 85, 105, 0.1));
        history.add(new Snapshot(3, 90, 110, 0.2)); // still looks FINE
        history.add(new Snapshot(4, 9000, 20, 45.0)); // SUDDEN collapse, no warning from these 3 alone

        System.out.println("Tracking only latency/traffic/errors:");
        for (Snapshot s : history) System.out.println("  t=" + s.t() + ": p99=" + s.latencyP99Ms() + "ms, traffic=" + s.trafficPerSec()
                + "/s, errors=" + s.errorPct() + "%");
        System.out.println("t=1 through t=3 all look healthy -- then SUDDEN collapse at t=4, with NO earlier warning signal from these three alone.");
    }
}
```

How to run: `java ThreeSignalsOnlyMissWarning.java`

Snapshots at `t=1` through `t=3` all show healthy, gently rising latency, stable traffic, and low error rates — nothing in these three signals hints at the sudden collapse at `t=4`. Whatever was building up toward that failure was invisible to this particular set of three metrics.

### Level 2 — Intermediate

```java
// File: SaturationPredictsTheCollapse.java -- adds SATURATION, the
// fourth signal; it was RISING steadily the whole time, predicting the
// t=4 collapse well in advance.
import java.util.*;

public class SaturationPredictsTheCollapse {
    record Snapshot(int t, double latencyP99Ms, double trafficPerSec, double errorPct, double saturationPct) {}
    static List<Snapshot> history = new ArrayList<>();

    public static void main(String[] args) {
        history.add(new Snapshot(1, 80, 100, 0.1, 60));
        history.add(new Snapshot(2, 85, 105, 0.1, 75));
        history.add(new Snapshot(3, 90, 110, 0.2, 92)); // saturation ALREADY high, even though the other 3 still look fine
        history.add(new Snapshot(4, 9000, 20, 45.0, 100)); // fully saturated -- THIS is where things collapsed

        System.out.println("Tracking all FOUR golden signals:");
        for (Snapshot s : history) System.out.println("  t=" + s.t() + ": p99=" + s.latencyP99Ms() + "ms, traffic=" + s.trafficPerSec()
                + "/s, errors=" + s.errorPct() + "%, SATURATION=" + s.saturationPct() + "%");
        System.out.println("Saturation crossed 90% at t=3, BEFORE the collapse at t=4 -- this WAS the early warning the other three missed.");
    }
}
```

How to run: `java SaturationPredictsTheCollapse.java`

The same three signals from Level 1 are present, but now paired with `saturationPct`, which climbs steadily from `60%` to `92%` by `t=3` — well before latency, errors, or traffic show any sign of trouble. This is exactly the predictive value the fourth golden signal adds: saturation was already at a concerning level a full time step before the other three signals gave any indication something was wrong.

### Level 3 — Advanced

```java
// File: CompositeHealthCheckOnFourSignals.java -- combines all FOUR
// signals into ONE composite health check a team can actually alert on,
// specifically weighting saturation as an EARLY-WARNING trigger distinct
// from the other three's LAGGING-indicator role.
import java.util.*;

public class CompositeHealthCheckOnFourSignals {
    record Snapshot(int t, double latencyP99Ms, double trafficPerSec, double errorPct, double saturationPct) {}
    static List<Snapshot> history = new ArrayList<>();

    static String healthStatus(Snapshot s) {
        if (s.errorPct() > 10 || s.latencyP99Ms() > 1000) return "CRITICAL (lagging indicators already bad)";
        if (s.saturationPct() > 90) return "WARNING (saturation predicts trouble ahead, other signals still OK)";
        return "HEALTHY";
    }

    public static void main(String[] args) {
        history.add(new Snapshot(1, 80, 100, 0.1, 60));
        history.add(new Snapshot(2, 85, 105, 0.1, 75));
        history.add(new Snapshot(3, 90, 110, 0.2, 92));
        history.add(new Snapshot(4, 9000, 20, 45.0, 100));

        for (Snapshot s : history) System.out.println("t=" + s.t() + ": " + healthStatus(s));
        System.out.println("The composite check flags a WARNING at t=3 -- a full time step BEFORE the t=4 CRITICAL collapse.");
    }
}
```

How to run: `java CompositeHealthCheckOnFourSignals.java`

`healthStatus` checks the lagging indicators (errors, latency) first — if either is already bad, it's `CRITICAL`. Otherwise, it checks saturation specifically as a leading indicator — if saturation is high even while the other signals still look fine, it reports `WARNING`, distinct from and earlier than a full `CRITICAL`. Running this across all four snapshots shows `HEALTHY` at `t=1` and `t=2`, `WARNING` at `t=3` (saturation flagged it, nothing else had), and `CRITICAL` at `t=4` — demonstrating that a composite check built around all four signals, with saturation weighted as an early-warning trigger, gives a team a meaningful window to react before the situation becomes a full incident.

## 6. Walkthrough

Trace `CompositeHealthCheckOnFourSignals.main` in order. **At `t=1`**, `healthStatus` checks `errorPct() > 10` (`0.1 > 10` is false) and `latencyP99Ms() > 1000` (`80 > 1000` is false), so it falls through to check `saturationPct() > 90` (`60 > 90` is false too) — the method returns `"HEALTHY"`.

**At `t=2`**, the same checks run: errors and latency are still both low, and saturation (`75`) is still under `90`, so `"HEALTHY"` is returned again.

**At `t=3`**, errors (`0.2`) and latency (`90`) are still both well under their critical thresholds, so the first `if` is false. But `saturationPct()` is now `92`, which *is* greater than `90` — the second `if` fires, and the method returns `"WARNING (saturation predicts trouble ahead, other signals still OK)"`.

**At `t=4`**, `errorPct()` is `45.0`, which is greater than `10` — the very first condition of the first `if` is now true, so the method short-circuits and returns `"CRITICAL (lagging indicators already bad)"` immediately, without needing to check latency or saturation at all.

**Finally**, `main` prints all four statuses in order and a closing observation: the `WARNING` at `t=3` appeared one full time step before the `CRITICAL` at `t=4`, giving exactly the kind of advance notice that including saturation as a distinct, weighted signal is meant to provide.

```
t=1: HEALTHY
t=2: HEALTHY
t=3: WARNING  (saturation=92% flags trouble; errors/latency still fine)
t=4: CRITICAL (errors=45%, latency=9000ms -- now unmistakably broken)
```

## 7. Gotchas & takeaways

> Treating saturation as "just another number on the dashboard," equally weighted with the other three, misses its specific value as a *leading* indicator — errors and latency are lagging indicators (they tell you something already went wrong), while saturation, tracked and alerted on distinctly, can warn you *before* it does.

- The four golden signals — latency, traffic, errors, saturation — extend RED's three request-facing signals with a resource-facing saturation signal borrowed from USE.
- Saturation is uniquely valuable as an early-warning, leading indicator, often rising well before latency or errors show any visible degradation.
- Apply these four signals as the minimum dashboard for any production service, adapting "traffic" and "saturation" to fit non-request-driven services (batch jobs, consumers) as needed.
- These four signals commonly become the concrete metrics a team defines [SLIs, SLOs, and error budgets](0359-sli-slo-sla-error-budgets.md) against, covered next.
