---
card: system-design
gi: 190
slug: dashboards-slo-based-alerting
title: Dashboards & SLO-based alerting
---

## 1. What it is

A **dashboard** visualizes [metrics](0187-metrics-counters-gauges-histograms.md) over time — request rate, error rate, latency — so a human can quickly assess a system's health at a glance. An **SLO (Service Level Objective)** is a specific, measurable reliability target (e.g. "99.9% of requests succeed in under 200ms, measured over 30 days"), and **SLO-based alerting** triggers an alert not from an arbitrary threshold, but from tracking how fast the system is consuming its allowed "error budget" against that objective — alerting early enough to act, but not so eagerly that every minor blip pages someone.

## 2. Why & when

A simple threshold alert ("page if error rate exceeds 5%") is easy to set up but easy to get wrong: too sensitive, and it pages for noise; too lenient, and it misses real problems until they are already severe. SLO-based alerting instead starts from a concrete reliability promise (the SLO) and calculates an **error budget** — the total amount of allowed failure over a period — then alerts based on the *rate* at which that budget is being consumed, which naturally distinguishes a brief blip from a sustained, budget-threatening trend. Use dashboards for humans to explore and understand system health visually; use SLO-based alerting to page someone only when a real, budget-threatening trend is actually happening.

## 3. Core concept

- **SLO (Service Level Objective):** a specific target, like "99.9% availability over 30 days," derived from what users actually need, not an arbitrary round number.
- **Error budget:** the inverse of the SLO — a 99.9% SLO allows a 0.1% error budget, which over 30 days is a fixed, calculable amount of allowed downtime or failed requests.
- **Burn rate:** how fast the error budget is being consumed relative to a steady, sustainable pace — a burn rate of 1x means you are on track to exactly exhaust the budget at the end of the period; a burn rate of 10x means the budget will be exhausted in a small fraction of that time if the current failure rate continues.
- **Multi-window, multi-burn-rate alerting:** rather than one alert on one threshold, well-designed SLO alerting checks the burn rate over multiple time windows (e.g. both the last 5 minutes and the last 1 hour) — a very high burn rate over a short window catches fast, severe outages; a moderate burn rate over a longer window catches slower, creeping degradation.
- **Dashboards visualize the data behind the alert:** the dashboard shows the raw metrics and the current burn rate trend, giving the on-call responder the context needed to actually diagnose the issue once paged, not just the fact that something is wrong.

## 4. Diagram

```
   SLO: 99.9% success rate over 30 days -> error budget: 0.1% of requests may fail

   error budget consumed over time:
   |                                              100% (budget exhausted)
   |                                    __/
   |                          _________/    <- burn rate INCREASING (something is degrading)
   |                _________/
   |______/\/\/\/\_/                        <- normal, slow, steady consumption
   |___________________________________________ time (30-day window)

   ALERT fires when the CURRENT burn rate, projected forward,
   would exhaust the budget FAR sooner than the end of the period
   -- not from a single arbitrary error-rate threshold
```
*Caption: alerting on the rate of error-budget consumption, not a fixed threshold, distinguishes a brief blip from a genuine, worsening trend worth waking someone up for.*

## 5. Runnable example

**Level 1 — Basic.** Compute a total error budget from an SLO target and a time window.

**Level 2 — Track burn rate: how fast the budget is being consumed right now.** Compare it to a sustainable pace.

**Level 3 — Multi-window alerting.** Check burn rate over both a short and a long window before deciding to alert.

```java
// SloAlertingDemo.java
import java.util.*;

public class SloAlertingDemo {

    // Level 1: derive the total error budget from the SLO target and the measurement window.
    static double errorBudgetFraction(double sloTargetFraction) {
        return 1.0 - sloTargetFraction; // e.g. 99.9% SLO -> 0.1% error budget
    }

    // Level 2: burn rate - how fast the CURRENT observed error rate consumes the budget, relative to a sustainable pace.
    // A burn rate of 1.0 means "consuming the budget exactly on pace to use it all by the end of the window."
    static double burnRate(double observedErrorRate, double errorBudgetFraction) {
        return observedErrorRate / errorBudgetFraction;
    }

    // Level 3: multi-window check - only alert if BOTH a short window is severely burning AND a longer window confirms it's not just noise.
    static boolean shouldAlert(double shortWindowBurnRate, double longWindowBurnRate) {
        boolean fastSevereBurn = shortWindowBurnRate >= 14.4;  // e.g. would exhaust a 30-day budget in ~1 hour
        boolean sustainedModerateBurn = longWindowBurnRate >= 6.0; // confirms it's not a one-off short blip
        return fastSevereBurn && sustainedModerateBurn;
    }

    public static void main(String[] args) {
        double sloTarget = 0.999; // 99.9% success rate
        double budget = errorBudgetFraction(sloTarget);
        System.out.println("SLO: " + (sloTarget * 100) + "% -> error budget: " + (budget * 100) + "%");

        // Level 2: a brief, isolated blip - high SHORT-window burn rate, but the longer window shows it's not sustained.
        double blipShortWindowRate = 0.02;  // 2% error rate in the last 5 minutes - a real spike
        double blipLongWindowRate = 0.0015; // but only 0.15% over the last hour - mostly fine, this was brief
        double blipShortBurn = burnRate(blipShortWindowRate, budget);
        double blipLongBurn = burnRate(blipLongWindowRate, budget);
        System.out.println("brief blip: short-window burn rate=" + String.format("%.1f", blipShortBurn) + "x, long-window burn rate=" + String.format("%.1f", blipLongBurn) + "x");
        System.out.println("should alert: " + shouldAlert(blipShortBurn, blipLongBurn) + " (short spike, but not sustained - correctly does NOT page)");

        // Level 3: a genuine, sustained outage - both windows show a severe, ongoing burn rate.
        double outageShortWindowRate = 0.02;  // same 2% short-term rate...
        double outageLongWindowRate = 0.018;  // ...but ALSO sustained at 1.8% over the last hour - this is real
        double outageShortBurn = burnRate(outageShortWindowRate, budget);
        double outageLongBurn = burnRate(outageLongWindowRate, budget);
        System.out.println("sustained outage: short-window burn rate=" + String.format("%.1f", outageShortBurn) + "x, long-window burn rate=" + String.format("%.1f", outageLongBurn) + "x");
        System.out.println("should alert: " + shouldAlert(outageShortBurn, outageLongBurn) + " (sustained across both windows - correctly PAGES on-call)");
    }
}
```

**How to run:** save as `SloAlertingDemo.java`, then run `java SloAlertingDemo.java`.

## 6. Walkthrough

1. `errorBudgetFraction(0.999)` computes `1.0 - 0.999 = 0.001`, so a 99.9% SLO allows a 0.1% error budget — this is the fixed total amount of allowed failure over the measurement window.
2. For the "brief blip" scenario, `burnRate(0.02, 0.001) = 20.0`, a very high burn rate over the short window — on its own, this looks alarming, exactly the kind of number a naive single-threshold alert would fire on immediately.
3. `burnRate(0.0015, 0.001) = 1.5` for the long window shows a much more modest, close-to-sustainable rate over the last hour — meaning the short-window spike was brief and did not represent a sustained trend.
4. `shouldAlert(20.0, 1.5)` checks `fastSevereBurn` (`20.0 >= 14.4`, true) but `sustainedModerateBurn` (`1.5 >= 6.0`, false) — since both conditions are required, the method returns `false`, correctly suppressing an alert for what was just a brief, self-resolving blip.
5. For the "sustained outage" scenario, both the short-window burn rate (20.0) and the long-window burn rate (18.0, well above 6.0) are severe; `shouldAlert(20.0, 18.0)` finds both conditions true and returns `true`, correctly triggering an alert — the multi-window check is what distinguishes this genuine, ongoing problem from the earlier blip that shared the exact same short-window burn rate but was not actually sustained.

## 7. Gotchas & takeaways

> Gotcha: alerting on a single time window alone (even a well-chosen threshold) forces a tradeoff between catching fast, severe outages quickly and avoiding false alarms from brief, self-resolving blips — you cannot tune one window to do both well at once; multi-window alerting exists specifically because these are genuinely different failure shapes that need different detection sensitivities.

- SLO-based alerting starts from a concrete reliability promise and calculates a burn rate, rather than relying on an arbitrary fixed threshold.
- A single burn-rate number, checked over just one time window, cannot reliably distinguish a brief blip from a sustained, budget-threatening trend — checking multiple windows together is what makes that distinction possible.
- Dashboards give humans the visual context to diagnose an issue once alerted; the alert itself should be reserved for genuinely budget-threatening trends, not every observable fluctuation.
- Related concepts: [Metrics (counters, gauges, histograms)](0187-metrics-counters-gauges-histograms.md) (the raw data an SLO's error rate is computed from), [The RED & USE methods](0189-the-red-use-methods.md) (a framework for deciding which underlying metrics feed into an SLO), [On-call, runbooks & incident response](0191-on-call-runbooks-incident-response.md) (what actually happens once an alert like this fires).
