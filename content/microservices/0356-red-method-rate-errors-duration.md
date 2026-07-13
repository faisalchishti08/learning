---
card: microservices
gi: 356
slug: red-method-rate-errors-duration
title: "RED method (Rate, Errors, Duration)"
---

## 1. What it is

The **RED method** is a simple, standard set of three metrics to track for every request-driven service: **Rate** (requests per second), **Errors** (the rate or percentage of failed requests), and **Duration** (how long requests take, typically as a distribution — p50, p95, p99 — rather than a single average). Tracking these three for every service gives a consistent, comparable baseline health view across an entire microservices system.

## 2. Why & when

With dozens of services, each potentially instrumented differently by different teams, comparing "is this service healthy" across the system becomes hard unless there's a shared, minimal standard everyone tracks. RED gives exactly that minimal, request-centric standard: any service that handles requests (which is nearly every microservice) can be summarized by these three numbers, letting an on-call engineer look at any service's dashboard and immediately understand its basic health, without needing to learn that service's bespoke metrics first.

Apply RED to every request-handling service as a baseline, in addition to (not instead of) any service-specific metrics that matter for its particular domain. It pairs naturally with the [four golden signals](0358-four-golden-signals-latency-traffic-errors-saturation.md) (which add saturation) and complements the [USE method](0357-use-method-utilization-saturation-errors.md) (which focuses on resources rather than requests) — RED is specifically the request-facing view, most directly useful for understanding user-facing service health.

## 3. Core concept

Rate is a simple counter of requests over time, divided by the time window (requests per second). Errors is the count or percentage of those requests that failed, typically tracked as its own counter incremented alongside the rate counter. Duration is captured as a histogram or summary — not a single average, since an average can hide a long tail of slow requests behind a good typical case — commonly reported as percentiles (p50 for typical experience, p99 for the worst 1% of requests).

```java
Counter requestsTotal = Counter.build("requests_total", "service", "method").register();
Counter errorsTotal = Counter.build("errors_total", "service", "method").register();
Histogram requestDuration = Histogram.build("request_duration_seconds", "service", "method").register();
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three panels: Rate showing requests per second over time, Errors showing error percentage, Duration showing a latency histogram with p50 and p99 marked">
  <rect x="20" y="20" width="185" height="130" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="112" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Rate</text>
  <text x="112" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">requests / second</text>

  <rect x="228" y="20" width="185" height="130" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="320" y="45" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Errors</text>
  <text x="320" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">% of requests failed</text>

  <rect x="435" y="20" width="185" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="528" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Duration</text>
  <text x="528" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">p50 / p95 / p99 latency</text>
</svg>

Rate, Errors, and Duration together give a consistent, minimal baseline health view for any request-handling service.

## 5. Runnable example

Scenario: a stream of requests with a mix of latencies and some failures, first summarized only with a misleading average duration, then fixed with proper RED metrics including percentiles, and finally extended to compute all three per-service so a dashboard can compare services consistently.

### Level 1 — Basic

```java
// File: MisleadingAverageOnly.java -- summarizes duration with a single
// AVERAGE, which hides the fact that a meaningful fraction of requests
// are much slower than "typical."
import java.util.*;

public class MisleadingAverageOnly {
    static List<Long> durationsMs = new ArrayList<>();

    public static void main(String[] args) {
        for (int i = 0; i < 99; i++) durationsMs.add(50L); // 99 FAST requests
        durationsMs.add(5000L); // ONE very slow request

        double average = durationsMs.stream().mapToLong(Long::longValue).average().orElse(0);
        System.out.println("Average duration: " + average + "ms -- looks FINE at a glance!");
        System.out.println("But 1 out of 100 requests actually took 5000ms -- the average HIDES this entirely.");
    }
}
```

How to run: `java MisleadingAverageOnly.java`

The computed average (`~99.5ms`) looks perfectly healthy, but it's dragged only slightly by the one 5000ms outlier among 99 fast requests — a single average number completely obscures the fact that any specific unlucky user could be experiencing a 100x slower response than "typical," which is exactly the kind of tail latency a percentile-based view is designed to surface.

### Level 2 — Intermediate

```java
// File: ProperRedMetrics.java -- computes Rate, Errors, and Duration
// (as PERCENTILES, not an average) -- the standard RED trio.
import java.util.*;

public class ProperRedMetrics {
    record RequestResult(boolean error, long durationMs) {}
    static List<RequestResult> results = new ArrayList<>();

    static double rate(double windowSeconds) { return results.size() / windowSeconds; }
    static double errorPercentage() {
        long errors = results.stream().filter(RequestResult::error).count();
        return 100.0 * errors / results.size();
    }
    static long percentile(int p) {
        List<Long> sorted = results.stream().map(RequestResult::durationMs).sorted().toList();
        int index = (int) Math.ceil(p / 100.0 * sorted.size()) - 1;
        return sorted.get(Math.max(index, 0));
    }

    public static void main(String[] args) {
        for (int i = 0; i < 97; i++) results.add(new RequestResult(false, 50));
        results.add(new RequestResult(true, 30));   // 1 error
        results.add(new RequestResult(false, 5000)); // 1 slow
        results.add(new RequestResult(false, 55));

        System.out.println("Rate: " + rate(10) + " req/s (over a 10s window)");
        System.out.println("Errors: " + errorPercentage() + "%");
        System.out.println("Duration p50: " + percentile(50) + "ms, p99: " + percentile(99) + "ms");
        System.out.println("p99 CORRECTLY reveals the slow tail that the average in Level 1 hid.");
    }
}
```

How to run: `java ProperRedMetrics.java`

`percentile(99)` sorts all durations and picks the value at the 99th-percentile index, which correctly surfaces the `5000ms` outlier as representative of the worst 1% of requests — information the single average from Level 1 completely lost. Combined with `rate` (requests per second) and `errorPercentage` (the fraction that failed), this gives the full standard RED picture: how much traffic, how much of it failed, and what the actual latency distribution looks like.

### Level 3 — Advanced

```java
// File: RedPerServiceDashboard.java -- computes RED metrics PER SERVICE,
// so a dashboard can compare multiple services consistently using the
// SAME three numbers for each.
import java.util.*;
import java.util.stream.*;

public class RedPerServiceDashboard {
    record RequestResult(String service, boolean error, long durationMs) {}
    static List<RequestResult> results = new ArrayList<>();

    static void printRedFor(String service, double windowSeconds) {
        List<RequestResult> serviceResults = results.stream().filter(r -> r.service().equals(service)).toList();
        double rate = serviceResults.size() / windowSeconds;
        double errorPct = 100.0 * serviceResults.stream().filter(RequestResult::error).count() / serviceResults.size();
        List<Long> sortedDurations = serviceResults.stream().map(RequestResult::durationMs).sorted().toList();
        long p99 = sortedDurations.get((int) Math.max(0, Math.ceil(0.99 * sortedDurations.size()) - 1));

        System.out.println(service + " -- Rate: " + rate + " req/s, Errors: " + errorPct + "%, p99: " + p99 + "ms");
    }

    public static void main(String[] args) {
        for (int i = 0; i < 95; i++) results.add(new RequestResult("order-service", false, 60));
        results.add(new RequestResult("order-service", true, 40));
        for (int i = 0; i < 3; i++) results.add(new RequestResult("order-service", false, 65));

        for (int i = 0; i < 80; i++) results.add(new RequestResult("payment-service", false, 200));
        for (int i = 0; i < 20; i++) results.add(new RequestResult("payment-service", true, 3000)); // payment-service is UNHEALTHY

        printRedFor("order-service", 10);
        printRedFor("payment-service", 10);
        System.out.println("The SAME three metrics, computed the SAME way, immediately show payment-service is the unhealthy one.");
    }
}
```

How to run: `java RedPerServiceDashboard.java`

`printRedFor` filters `results` down to one service at a time and applies the identical rate/error-percentage/p99 computation regardless of which service is being examined. Comparing the two printed lines directly shows `order-service` healthy (low error rate, low p99) and `payment-service` unhealthy (a 20% error rate and a 3000ms p99) — because both services are summarized with the exact same three metrics, an on-call engineer can compare them at a glance without needing service-specific knowledge of either one.

## 6. Walkthrough

Trace `RedPerServiceDashboard.main` in order. **First**, 99 `order-service` results are added (95 fast successes, 1 error, 3 slightly-slower successes) and 100 `payment-service` results are added (80 successes at `200ms`, 20 errors at `3000ms`).

**Next**, `printRedFor("order-service", 10)` runs. It filters `results` to the 99 `order-service` entries, computes `rate = 99 / 10 = 9.9` requests/sec, computes `errorPct` as `100.0 * 1 / 99 ≈ 1.01%` (only the one error), and sorts all 99 durations to find `p99` — since durations are mostly `60` with a few `65`s and one `40`, the 99th-percentile value lands among the higher, but still fast, values, well under `100ms`.

**Then**, `printRedFor("payment-service", 10)` runs. It filters to the 100 `payment-service` entries, computes `rate = 100 / 10 = 10.0` requests/sec, computes `errorPct` as `100.0 * 20 / 100 = 20.0%` — a full fifth of requests failing — and sorts all 100 durations; since 20 of them are `3000ms`, the 99th-percentile index falls well within that slow group, so `p99` comes out at `3000ms`.

**Finally**, `main` prints a closing comparison, noting that the identical metric computation applied to both services immediately reveals `payment-service`'s much higher error rate and dramatically worse p99 latency — exactly the kind of at-a-glance, cross-service comparability the RED method is designed to provide.

```
order-service:   rate=9.9 req/s,  errors≈1.0%,  p99≈65ms   -- HEALTHY
payment-service: rate=10.0 req/s, errors=20.0%, p99=3000ms -- UNHEALTHY, immediately visible
```

## 7. Gotchas & takeaways

> Reporting only an average duration (as in Level 1) hides tail latency — the exact experience of the unluckiest users — behind a number that looks fine in aggregate. Always report duration as percentiles (at least p50 and p99), never as a single average, for RED's Duration metric to be meaningful.

- RED — Rate, Errors, Duration — is a minimal, standard set of metrics for any request-handling service, giving consistent, comparable baseline health across an entire microservices system.
- Duration must be tracked as a distribution (percentiles), not a single average, or tail latency problems remain invisible.
- Apply RED metrics to every service as a baseline, alongside (not instead of) service-specific metrics that matter for its own domain.
- Keep RED's labels (service name, method) bounded per [cardinality](0355-cardinality-of-metrics-labels.md) guidance; pair with the [USE method](0357-use-method-utilization-saturation-errors.md) for resource-level health and the [four golden signals](0358-four-golden-signals-latency-traffic-errors-saturation.md) for a slightly broader standard view.
