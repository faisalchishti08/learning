---
card: microservices
gi: 363
slug: alerting-on-call
title: "Alerting & on-call"
---

## 1. What it is

**Alerting** is the automated system that watches metrics (often the [four golden signals](0358-four-golden-signals-latency-traffic-errors-saturation.md) or an [error budget's burn rate](0359-sli-slo-sla-error-budgets.md)) and, when a defined condition is met, notifies a human. **On-call** is the rotation of engineers responsible for responding to those alerts, typically outside normal working hours as well as during them, so that a production issue gets a human's attention promptly regardless of when it occurs.

## 2. Why & when

Dashboards are only useful if someone is actively looking at them; a metric silently crossing a dangerous threshold at 3am does nobody any good if no automated system notices and tells a human. Alerting closes this gap by converting "a condition that matters" into "a page sent to whoever is on-call right now." On-call exists because production issues don't wait for business hours, and someone needs to be reachable and responsible for responding when they occur.

Define alerts for conditions that are both genuinely actionable (something a human can and should do something about) and rare enough not to become background noise — an alert that fires constantly for a condition nobody acts on trains the on-call engineer to ignore it, which is far more dangerous than having no alert at all (this is "alert fatigue"). Base alerts on symptoms that matter to users (elevated error rate, high latency, error budget burning fast) rather than every possible internal signal, and route each alert to the specific team actually responsible for the affected service, so the person paged has both the context and the authority to act.

## 3. Core concept

An alert rule is a condition evaluated continuously against live metrics (`error rate > 5% for 5 minutes`); when it becomes true, the alerting system notifies the current on-call engineer (via page, SMS, phone call — something that reliably reaches someone even if they're asleep). A well-designed alert distinguishes urgency: a page (wake someone up, respond now) versus a lower-urgency notification (look at this during business hours) — not every actionable condition deserves to interrupt someone's sleep.

```java
record AlertRule(String name, java.util.function.Predicate<Metrics> condition, String severity) {}
AlertRule highErrorRate = new AlertRule("HighErrorRate", m -> m.errorRatePercent() > 5.0, "PAGE");
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A metric crosses an alert threshold; the alerting system evaluates the rule as true and pages the current on-call engineer via phone, who acknowledges and begins investigating">
  <rect x="20" y="60" width="160" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="100" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Metric crosses threshold</text>

  <line x1="180" y1="77" x2="250" y2="77" stroke="#8b949e" marker-end="url(#a363)"/>
  <rect x="260" y="60" width="150" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="335" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Alert rule fires</text>

  <line x1="410" y1="77" x2="480" y2="77" stroke="#8b949e" marker-end="url(#a363)"/>
  <rect x="490" y="60" width="130" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="555" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Pages on-call</text>

  <text x="320" y="140" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">The on-call engineer acknowledges and begins investigating, at any hour.</text>

  <defs><marker id="a363" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

An alert rule continuously evaluates live metrics and, when it fires, notifies whoever is currently on-call.

## 5. Runnable example

Scenario: a metric stream that crosses a dangerous threshold, first with no alerting at all (silently unnoticed), then fixed with a basic alert rule paging the on-call engineer, and finally extended to distinguish urgency levels so not every condition wakes someone up at 3am.

### Level 1 — Basic

```java
// File: NoAlertingSilentFailure.java -- error rate spikes dangerously,
// but NOTHING notices or notifies anyone -- purely reactive discovery only.
import java.util.*;

public class NoAlertingSilentFailure {
    record MetricSnapshot(int t, double errorRatePercent) {}
    static List<MetricSnapshot> history = new ArrayList<>();

    public static void main(String[] args) {
        history.add(new MetricSnapshot(1, 0.2));
        history.add(new MetricSnapshot(2, 0.3));
        history.add(new MetricSnapshot(3, 45.0)); // MAJOR spike -- but nobody is notified!

        for (MetricSnapshot s : history) System.out.println("t=" + s.t() + ": error rate = " + s.errorRatePercent() + "%");
        System.out.println("The 45% spike at t=3 is SEVERE -- but with NO alerting, nobody finds out until a customer complains.");
    }
}
```

How to run: `java NoAlertingSilentFailure.java`

The error rate data clearly shows a severe spike at `t=3`, but nothing in this code observes that data proactively — someone would only discover this by manually checking a dashboard, or worse, by a customer reporting a problem, potentially hours after the spike actually occurred.

### Level 2 — Intermediate

```java
// File: BasicAlertPagesOnCall.java -- an alert rule EVALUATES the metric
// stream continuously and PAGES the current on-call engineer the moment
// the threshold is crossed.
import java.util.*;

public class BasicAlertPagesOnCall {
    record MetricSnapshot(int t, double errorRatePercent) {}
    static List<MetricSnapshot> history = new ArrayList<>();
    static String currentOnCall = "alice"; // the rotation's current engineer

    static void evaluateAlert(MetricSnapshot s) {
        if (s.errorRatePercent() > 5.0) {
            System.out.println("  ALERT FIRED at t=" + s.t() + ": error rate " + s.errorRatePercent()
                    + "% exceeds 5% threshold -- PAGING " + currentOnCall + " NOW.");
        }
    }

    public static void main(String[] args) {
        history.add(new MetricSnapshot(1, 0.2));
        history.add(new MetricSnapshot(2, 0.3));
        history.add(new MetricSnapshot(3, 45.0));

        for (MetricSnapshot s : history) {
            System.out.println("t=" + s.t() + ": error rate = " + s.errorRatePercent() + "%");
            evaluateAlert(s);
        }
    }
}
```

How to run: `java BasicAlertPagesOnCall.java`

`evaluateAlert` runs against every incoming snapshot, and at `t=3`, `45.0 > 5.0` is true, triggering an immediate page to `currentOnCall`. Unlike Level 1, the severe spike is now caught the moment it happens, not discovered later — `alice` (or whoever is on-call at the time) is notified in real time, giving her the chance to investigate and respond promptly rather than someone finding out after the fact.

### Level 3 — Advanced

```java
// File: TieredUrgencyAlerting.java -- distinguishes URGENCY: a
// severe error-rate spike PAGES on-call immediately (wakes someone up),
// while a milder, sustained rise sends a lower-urgency NOTIFICATION
// (review during business hours) -- not every actionable condition
// deserves to interrupt someone's sleep.
import java.util.*;

public class TieredUrgencyAlerting {
    record MetricSnapshot(int t, double errorRatePercent) {}
    static List<MetricSnapshot> history = new ArrayList<>();
    static String currentOnCall = "alice";

    static void evaluateAlert(MetricSnapshot s) {
        if (s.errorRatePercent() > 20.0) {
            System.out.println("  PAGE (urgent) at t=" + s.t() + ": error rate " + s.errorRatePercent()
                    + "% -- waking up " + currentOnCall + " NOW, this cannot wait.");
        } else if (s.errorRatePercent() > 1.0) {
            System.out.println("  NOTIFICATION (low urgency) at t=" + s.t() + ": error rate " + s.errorRatePercent()
                    + "% -- flagged for review during business hours, NOT worth waking anyone up for.");
        }
    }

    public static void main(String[] args) {
        history.add(new MetricSnapshot(1, 0.2));  // healthy, no alert
        history.add(new MetricSnapshot(2, 1.5));  // mildly elevated -- low-urgency notification only
        history.add(new MetricSnapshot(3, 45.0)); // severe -- urgent page

        for (MetricSnapshot s : history) {
            System.out.println("t=" + s.t() + ": error rate = " + s.errorRatePercent() + "%");
            evaluateAlert(s);
        }
        System.out.println("Tiered urgency means on-call is NOT woken for every minor blip -- only for genuinely severe conditions.");
    }
}
```

How to run: `java TieredUrgencyAlerting.java`

`evaluateAlert` now checks two thresholds in order: anything above `20%` triggers an urgent page (worth waking someone up for), while anything above `1%` but at or below `20%` triggers only a lower-urgency notification (worth a look during business hours, but not urgent enough to interrupt sleep). At `t=2` (`1.5%`), the milder condition fires a notification, not a page; at `t=3` (`45.0%`), the severe condition fires an urgent page. This distinction is exactly what prevents alert fatigue — if every mild fluctuation paged on-call the same way a genuine crisis did, engineers would quickly learn to ignore pages altogether, defeating the entire purpose of having them.

## 6. Walkthrough

Trace `TieredUrgencyAlerting.main` in order. **At `t=1`** (`errorRatePercent=0.2`), `evaluateAlert` checks `0.2 > 20.0` (false), then `0.2 > 1.0` (also false) — neither branch fires, so no output beyond the raw metric print.

**At `t=2`** (`errorRatePercent=1.5`), `evaluateAlert` checks `1.5 > 20.0` (false), then `1.5 > 1.0` (true) — the `else if` branch fires, printing a low-urgency notification message rather than a page.

**At `t=3`** (`errorRatePercent=45.0`), `evaluateAlert` checks `45.0 > 20.0` (true) — the first `if` branch fires immediately, printing an urgent page message; because this is an `if`/`else if` chain, the second condition is never even evaluated once the first matches.

**Finally**, `main` prints a closing observation explaining that this tiered approach means on-call is only woken for the genuinely severe `t=3` condition, while the milder `t=2` elevation is queued for a calmer, business-hours review — preserving the on-call engineer's attention (and sleep) for conditions that truly warrant it.

```
t=1: 0.2%  -> no alert
t=2: 1.5%  -> NOTIFICATION (low urgency, review during business hours)
t=3: 45.0% -> PAGE (urgent, wake on-call NOW)
```

## 7. Gotchas & takeaways

> Alerts that fire frequently for conditions nobody actually acts on train on-call engineers to dismiss pages reflexively — a phenomenon called alert fatigue — which is far more dangerous than having no alert at all, because it means even a *genuinely* critical page might get ignored or delayed. Regularly prune and tune alert rules based on whether they actually led to meaningful action; delete or adjust ones that don't.

- Alerting automatically watches metrics for defined conditions and notifies whoever is currently on-call; on-call is the rotation of engineers responsible for responding, day or night.
- Base alerts on symptoms that matter to users (error rate, latency, error budget burn rate) and route them to the team with both the context and the authority to act.
- Distinguish urgency: reserve urgent pages (interrupting sleep) for genuinely severe conditions, and use lower-urgency notifications for milder issues that can wait for business hours.
- Alert fatigue — too many low-value pages — is a real, common failure mode; regularly review and prune alert rules that don't lead to meaningful action.
