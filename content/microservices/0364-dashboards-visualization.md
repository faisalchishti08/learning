---
card: microservices
gi: 364
slug: dashboards-visualization
title: "Dashboards & visualization"
---

## 1. What it is

**Dashboards** are visual, at-a-glance summaries of a system's metrics (typically the [RED](0356-red-method-rate-errors-duration.md), [USE](0357-use-method-utilization-saturation-errors.md), or [four golden signals](0358-four-golden-signals-latency-traffic-errors-saturation.md)), rendered as graphs, gauges, and tables — usually via a tool like Grafana or a cloud provider's monitoring console, reading from the same metrics store that alerting rules evaluate. Where an alert tells you something specific is wrong, a dashboard lets a human quickly scan overall system health, spot trends, and drill into a specific service when something looks off.

## 2. Why & when

Raw metric data — numbers in a time-series database — isn't something a human can usefully scan directly; a dashboard's graphs turn that data into a shape a human can recognize at a glance ("that line is trending up," "that gauge is in the red zone"). Dashboards serve a different purpose than alerts: an alert interrupts you when a specific defined condition is met, while a dashboard is something you actively look at — during an incident to understand what's happening, during a calm period to spot a slow-building trend before it becomes an incident, or just as part of a regular health check.

Build a dashboard for every service covering at minimum its RED or four-golden-signals metrics, and build a system-wide dashboard giving an overview across all services for at-a-glance health checks. Design dashboards to answer specific questions quickly (is this service healthy right now, what does the request rate look like over the last hour) rather than cramming in every metric that exists — a cluttered dashboard with fifty panels is often less useful during an actual incident than a focused one with the five metrics that actually matter for that service.

## 3. Core concept

A dashboard panel queries a metrics backend for a time range and renders the result as a graph, single-value gauge, or table; multiple panels are arranged together, often with a shared time-range selector so an investigator can zoom into the same window across every panel simultaneously to correlate behavior across metrics.

```java
record DashboardPanel(String title, String metricQuery, String visualizationType) {}
DashboardPanel latencyPanel = new DashboardPanel("p99 Latency", "histogram_quantile(0.99, request_duration_seconds)", "line-graph");
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A dashboard with four panels arranged in a grid: request rate line graph, error rate line graph, p99 latency line graph, and a saturation gauge -- all sharing the same time range selector">
  <rect x="20" y="20" width="290" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="165" y="55" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Request Rate (line graph)</text>
  <rect x="330" y="20" width="290" height="60" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="475" y="55" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Error Rate (line graph)</text>
  <rect x="20" y="90" width="290" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="165" y="125" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">p99 Latency (line graph)</text>
  <rect x="330" y="90" width="290" height="60" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="475" y="125" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Saturation (gauge)</text>
</svg>

Multiple panels, sharing a common time range, let an investigator correlate different signals for the same window at a glance.

## 5. Runnable example

Scenario: a service's metric data presented first as an unreadable dump of raw numbers, then rendered as simple ASCII "graphs" mimicking a dashboard's visual shape, and finally combined into a multi-panel view with a shared time window, letting a viewer correlate a latency spike with a saturation spike at the same moment.

### Level 1 — Basic

```java
// File: RawNumbersUnreadable.java -- metric data as a raw list of
// numbers; a human cannot quickly spot a trend or a problem in this form.
import java.util.*;

public class RawNumbersUnreadable {
    public static void main(String[] args) {
        int[] latenciesMs = {80, 82, 85, 90, 400, 3200, 3400, 200, 90, 85};
        System.out.println("Raw latency data: " + Arrays.toString(latenciesMs));
        System.out.println("Somewhere in there is a problem -- but scanning raw numbers, it's slow to spot exactly where or how bad.");
    }
}
```

How to run: `java RawNumbersUnreadable.java`

The raw array does contain a clear spike (`400`, `3200`, `3400`), but a human scanning a printed array of numbers has to consciously parse and compare each value — this doesn't scale to real dashboards with thousands of data points, where a spike could be easy to miss entirely without visual rendering.

### Level 2 — Intermediate

```java
// File: AsciiBarGraph.java -- renders the SAME data as a simple ASCII bar
// graph, mimicking what a dashboard panel would show visually -- the
// spike is now IMMEDIATELY obvious at a glance.
import java.util.*;

public class AsciiBarGraph {
    static void renderBarGraph(String title, int[] values, int scale) {
        System.out.println(title + ":");
        for (int v : values) {
            int bars = Math.min(v / scale, 60); // cap bar length so huge values don't overflow the display
            System.out.println("  " + "#".repeat(bars) + " (" + v + "ms)");
        }
    }

    public static void main(String[] args) {
        int[] latenciesMs = {80, 82, 85, 90, 400, 3200, 3400, 200, 90, 85};
        renderBarGraph("Latency over time", latenciesMs, 50);
        System.out.println("The spike is now IMMEDIATELY visible as a shape, not something you have to mentally compare numbers to find.");
    }
}
```

How to run: `java AsciiBarGraph.java`

`renderBarGraph` converts each numeric value into a proportional bar of `#` characters, mimicking the visual shape a real dashboard's line or bar graph would show. The spike in the middle of the data is now unmistakable at a glance — exactly the value visualization adds over raw numbers: a shape a human recognizes instantly, without needing to consciously compare individual values.

### Level 3 — Advanced

```java
// File: CorrelatedMultiPanelDashboard.java -- renders TWO panels
// (latency and saturation) side by side over the SAME time window,
// letting a viewer visually CORRELATE the latency spike with a
// saturation spike happening at the EXACT same moment.
import java.util.*;

public class CorrelatedMultiPanelDashboard {
    static void renderPanel(String title, int[] values, int scale, int width) {
        System.out.println(title + ":");
        for (int i = 0; i < values.length; i++) {
            int bars = Math.min(values[i] / scale, width);
            System.out.println("  t=" + i + " " + "#".repeat(bars) + " (" + values[i] + ")");
        }
    }

    public static void main(String[] args) {
        int[] latenciesMs =      {80, 82, 85, 90, 400, 3200, 3400, 200, 90, 85};
        int[] saturationPercent = {60, 62, 65, 70, 85,  98,   99,  80, 65, 60};

        renderPanel("Panel 1: Latency (ms)", latenciesMs, 50, 60);
        System.out.println();
        renderPanel("Panel 2: Saturation (%)", saturationPercent, 2, 60);

        System.out.println();
        System.out.println("Notice: BOTH panels spike together at t=5 and t=6 -- visually correlating latency to a SATURATED resource, at the SAME moment.");
    }
}
```

How to run: `java CorrelatedMultiPanelDashboard.java`

Both panels are rendered over the identical time indices (`t=0` through `t=9`), and both show their largest bars at exactly `t=5` and `t=6` — the latency spike and the saturation spike align perfectly. A viewer scanning both panels side by side (exactly as a real multi-panel dashboard sharing one time-range selector would present them) can immediately connect the two: the latency spike coincides with a resource nearing full saturation, suggesting the saturated resource is the likely cause — a correlation that would be far harder to notice from either panel's raw numbers in isolation.

## 6. Walkthrough

Trace `CorrelatedMultiPanelDashboard.main` in order. **First**, `renderPanel("Panel 1: Latency (ms)", latenciesMs, 50, 60)` runs: for each index `i` from `0` to `9`, it computes `bars = min(latenciesMs[i] / 50, 60)` and prints a line with that many `#` characters. At `i=5` and `i=6`, `latenciesMs` values are `3200` and `3400`, giving `bars = min(64, 60) = 60` and `min(68, 60) = 60` respectively — both capped at the maximum width, producing visibly long bars compared to the short bars at every other index.

**Next**, `renderPanel("Panel 2: Saturation (%)", saturationPercent, 2, 60)` runs the same way over `saturationPercent`. At `i=5` and `i=6`, the values are `98` and `99`, giving `bars = min(49, 60) = 49` and `min(49, 60) = 49` — again the longest bars in this panel, clearly standing out from the shorter bars surrounding them.

**Because both panels are printed using the same time index `i` as their x-axis**, a viewer scanning both blocks of output sees the longest bars in *both* panels line up at the exact same `t=5` and `t=6` positions.

**Finally**, `main` prints a closing observation explicitly pointing out this alignment — the same correlation a real dashboard's shared time-range selector is designed to make visually obvious, letting an investigator connect a latency problem to its likely resource-saturation cause without needing to manually cross-reference two separate data sources.

```
Panel 1 (Latency):    t=4:short  t=5:LONG  t=6:LONG  t=7:short  ...
Panel 2 (Saturation): t=4:medium t=5:LONG  t=6:LONG  t=7:medium ...
                              ^^^^^^^^^^^^^^^^
                        Both spike TOGETHER at t=5,6 -- visually correlated
```

## 7. Gotchas & takeaways

> A dashboard crammed with dozens of panels, all showing every metric that exists, is often *less* useful during an actual incident than a focused dashboard with just the handful of metrics that matter most for that service — too many panels forces an investigator to hunt for the relevant signal instead of seeing it immediately.

- Dashboards render metric data visually (graphs, gauges) so a human can quickly recognize trends and problems that would be slow or impossible to spot in raw numeric form.
- Multiple panels sharing a common time-range selector let an investigator visually correlate different signals for the same window, often quickly revealing likely cause-and-effect relationships (a saturation spike coinciding with a latency spike).
- Build service-level dashboards around [RED](0356-red-method-rate-errors-duration.md) or the [four golden signals](0358-four-golden-signals-latency-traffic-errors-saturation.md), plus a system-wide overview dashboard, and keep each dashboard focused rather than exhaustive.
- Dashboards and [alerting](0363-alerting-on-call.md) complement each other: alerts interrupt you when a specific condition fires; dashboards are what you actively consult to understand the broader picture, both during an incident and during routine health checks.
