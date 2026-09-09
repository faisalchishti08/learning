---
card: system-design
gi: 187
slug: metrics-counters-gauges-histograms
title: Metrics (counters, gauges, histograms)
---

## 1. What it is

**Metrics** are numeric measurements of a system's behavior, recorded over time. A **counter** only ever goes up (or resets to zero), used for things you count, like total requests served. A **gauge** can go up or down, representing a current value at a point in time, like the number of active connections right now. A **histogram** records the distribution of a set of values (like request latencies), letting you later compute percentiles (p50, p95, p99), not just an average.

## 2. Why & when

Logs tell you what happened in a specific event, but answering "how many requests failed in the last hour" or "what does our p99 latency look like right now" by scanning individual log lines does not scale, and was never really what logs were designed for. Metrics are aggregated numbers, cheap to store and query even at very high volume, purpose-built for exactly these kinds of questions — trends, rates, and distributions over time. Use counters for anything you count (requests, errors), gauges for anything with a current level (queue depth, memory usage), and histograms for anything where the *distribution* matters more than a single average (latency, response size).

## 3. Core concept

- **Counter — monotonically increasing:** `requestsTotal.increment()` on every request; you query it as a *rate* (increase over a time window), not as a raw cumulative total, since the total by itself is rarely meaningful.
- **Gauge — a snapshot value:** `activeConnections.set(currentCount)`, read at query time as whatever it currently is — unlike a counter, it can legitimately decrease.
- **Histogram — bucketed distribution:** instead of storing every individual value, a histogram counts how many observations fell into each of several buckets (e.g. `<10ms`, `<50ms`, `<100ms`, `<500ms`), from which percentiles can be estimated.
- **Why averages mislead, and percentiles matter:** an average latency can look fine even while a meaningful fraction of users experience terrible latency, if a few very fast requests pull the average down; a p99 (99th percentile) directly answers "what does the worst 1% of users experience," which an average simply cannot.
- **Labels/tags for dimensionality:** a metric is usually tagged with labels (e.g. `endpoint=/checkout`, `status=500`), letting you slice the same underlying metric by any combination of those dimensions later.

## 4. Diagram

```
   COUNTER (requests_total):           GAUGE (active_connections):
   |----/                              5 -\
   |   /                                4  \_/\
   |  /                                 3      \
   | /                                  2        \___
   |/______________ time                1____________ time
   only ever increases                  goes up AND down freely

   HISTOGRAM (request_latency_ms):
   bucket <10ms:   ||||||||||||||||||||||||  (2400 requests)
   bucket <50ms:   ||||||||||               (900 requests)
   bucket <100ms:  |||                       (280 requests)
   bucket <500ms:  |                         (18 requests)
                                              -> p99 falls somewhere in the <500ms bucket
```
*Caption: a counter only ever climbs, a gauge freely moves up and down, and a histogram's bucket counts let you estimate any percentile after the fact.*

## 5. Runnable example

**Level 1 — Basic.** A counter (increment-only) and a gauge (set to any value).

**Level 2 — A histogram, recording individual observations into fixed buckets.** Compute an approximate percentile from the bucket counts.

**Level 3 — Tagged metrics, sliced by a label.** Track the same metric separately per endpoint.

```java
// MetricsDemo.java
import java.util.*;

public class MetricsDemo {

    // Level 1: counter - only ever increments.
    static class Counter {
        long value = 0;
        void increment() { value++; }
    }

    // Level 1: gauge - can be set to any value, up or down.
    static class Gauge {
        double value = 0;
        void set(double v) { value = v; }
    }

    // Level 2: histogram - counts observations into fixed latency buckets.
    static class Histogram {
        final int[] bucketUpperBoundsMs = {10, 50, 100, 500, Integer.MAX_VALUE};
        final long[] bucketCounts = new long[bucketUpperBoundsMs.length];
        long totalObservations = 0;

        void observe(int latencyMs) {
            totalObservations++;
            for (int i = 0; i < bucketUpperBoundsMs.length; i++) {
                if (latencyMs <= bucketUpperBoundsMs[i]) { bucketCounts[i]++; break; }
            }
        }

        // Approximate percentile: find the bucket where the cumulative count crosses the target percentile.
        String approximatePercentileBucket(double percentile) {
            long target = (long) (totalObservations * percentile);
            long cumulative = 0;
            for (int i = 0; i < bucketUpperBoundsMs.length; i++) {
                cumulative += bucketCounts[i];
                if (cumulative >= target) return "<= " + bucketUpperBoundsMs[i] + "ms";
            }
            return "unknown";
        }
    }

    // Level 3: tagged metrics - the SAME kind of metric, tracked separately per label value.
    static Map<String, Counter> requestsByEndpoint = new HashMap<>();

    static void recordRequest(String endpoint) {
        requestsByEndpoint.computeIfAbsent(endpoint, e -> new Counter()).increment();
    }

    public static void main(String[] args) {
        // Level 1: a simple counter and gauge.
        Counter requestsTotal = new Counter();
        Gauge activeConnections = new Gauge();
        for (int i = 0; i < 5; i++) requestsTotal.increment();
        activeConnections.set(12);
        activeConnections.set(9); // gauges freely move down, unlike counters
        System.out.println("requests_total: " + requestsTotal.value + " (only ever goes up)");
        System.out.println("active_connections: " + activeConnections.value + " (currently 9, was 12 a moment ago)");

        // Level 2: histogram of realistic latencies - mostly fast, with a long tail of slow ones.
        Histogram latencyHistogram = new Histogram();
        int[] sampleLatencies = {5, 8, 6, 7, 9, 20, 15, 30, 45, 40, 60, 90, 200, 480, 5, 6, 8, 7};
        for (int latency : sampleLatencies) latencyHistogram.observe(latency);
        System.out.println("latency histogram bucket counts: " + Arrays.toString(latencyHistogram.bucketCounts));
        System.out.println("approximate p50: " + latencyHistogram.approximatePercentileBucket(0.50));
        System.out.println("approximate p99: " + latencyHistogram.approximatePercentileBucket(0.99));

        // Level 3: the same "requests" counter, but sliced by endpoint via labels.
        recordRequest("/checkout"); recordRequest("/checkout"); recordRequest("/checkout");
        recordRequest("/search");
        System.out.println("requests by endpoint: /checkout=" + requestsByEndpoint.get("/checkout").value
            + ", /search=" + requestsByEndpoint.get("/search").value);
    }
}
```

**How to run:** save as `MetricsDemo.java`, then run `java MetricsDemo.java`.

## 6. Walkthrough

1. `requestsTotal.increment()` is called five times, each simply incrementing `value` by one, ending at `5` — this models a counter's fundamental property: it only ever climbs, never resets except by design (e.g. on process restart).
2. `activeConnections.set(12)` followed by `activeConnections.set(9)` shows the gauge legitimately decreasing — something a counter structurally cannot do, since a gauge represents a current snapshot, not an accumulating total.
3. Each call to `latencyHistogram.observe(latency)` finds the *first* bucket boundary the latency is less than or equal to, and increments that bucket's count; the sample data (mostly small values like 5-9ms, with a long tail up to 480ms) lands mostly in the `<=10ms` bucket, with progressively fewer observations in the higher buckets — printing the bucket counts shows this distribution directly, which no single average number could convey.
4. `approximatePercentileBucket(0.50)` computes `target = totalObservations * 0.50` and walks the buckets accumulating counts until the cumulative count reaches that target; since most observations are fast, this lands in a low bucket (`<=10ms`), correctly reflecting that the *median* request is fast.
5. `approximatePercentileBucket(0.99)` computes a much higher `target`, and the cumulative walk has to reach nearly all observations before crossing it — landing in the `<=500ms` bucket, correctly capturing that the slowest 1% of requests (the `480ms` observation) is dramatically worse than the median, exactly the kind of tail behavior an average would have hidden by blending it in with all the fast requests.

## 7. Gotchas & takeaways

> Gotcha: adding too many label combinations to a single metric (e.g. tagging by `userId` on a high-cardinality metric with millions of distinct users) causes "cardinality explosion" — the underlying time-series storage has to track a separate series for every unique label combination, which can silently overwhelm a metrics backend; reserve labels for low-cardinality dimensions (endpoint, status code, region), not unbounded identifiers.

- Counters, gauges, and histograms each answer a different kind of question, and choosing the wrong type for a given measurement produces misleading or unusable data.
- A histogram's bucketed distribution is what makes percentile-based analysis possible — an average alone hides exactly the tail behavior that often matters most.
- Labels let one metric be sliced along multiple dimensions later, but high-cardinality labels can overwhelm a metrics system if used carelessly.
- Related concepts: [The RED & USE methods](0189-the-red-use-methods.md) (a framework for deciding which metrics to actually collect), [Tail latency & percentiles (p50/p95/p99)](0126-tail-latency-percentiles-p50-p95-p99.md) (the deeper treatment of why percentiles matter), [Micrometer metrics + Prometheus](0192-micrometer-metrics-prometheus.md) (a concrete Java library implementing exactly these metric types).
