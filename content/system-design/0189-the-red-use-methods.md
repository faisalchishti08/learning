---
card: system-design
gi: 189
slug: the-red-use-methods
title: The RED & USE methods
---

## 1. What it is

The **RED method** is a simple framework for monitoring any request-driven service, defining exactly three metrics to track for every service: **R**ate (requests per second), **E**rrors (the rate of failed requests), and **D**uration (how long requests take, typically as a latency [histogram](0187-metrics-counters-gauges-histograms.md)). The **USE method** is a complementary framework for monitoring resources (CPU, disk, network), defining three different metrics: **U**tilization (how busy the resource is), **S**aturation (how much work is queued waiting for it), and **E**rrors (resource-level error events).

## 2. Why & when

Faced with a service to monitor for the first time, it is easy to either monitor too little (missing an obvious signal) or too much (drowning in metrics that do not actually help diagnose problems). RED and USE exist because most operational questions about a system reduce to a small, well-understood set of signals — these frameworks give you a starting checklist so you do not have to invent one from scratch every time. Use RED for any service handling requests (an API, a microservice); use USE for any underlying resource that request-driven services depend on (a server's CPU, a disk, a network link, a connection pool).

## 3. Core concept

- **Rate:** requests per second, the raw volume of traffic a service is handling right now — a sudden drop can indicate an upstream problem, and a sudden spike can indicate a real surge or a misbehaving client.
- **Errors:** the rate (or percentage) of requests failing — tracked separately from total rate, since a service can have high volume and still be perfectly healthy, or low volume and still be badly broken.
- **Duration:** latency, ideally as percentiles from a histogram (not just an average) — this is what [tail latency](0126-tail-latency-percentiles-p50-p95-p99.md) analysis is built on.
- **Utilization:** the percentage of time a resource is busy doing work — high utilization alone is not necessarily bad (a fully-utilized CPU doing useful work is fine), but it often precedes saturation.
- **Saturation:** the amount of work queued up waiting for a resource, beyond what it can currently service — this is the leading indicator that a resource is becoming a genuine bottleneck, often visible before utilization even reaches 100%.

## 4. Diagram

```
   RED (for a REQUEST-DRIVEN service, e.g. an API):
   Rate:      -----/\--/\----/\-----   (requests/sec over time)
   Errors:    ----------/\-----------   (error rate - watch for spikes)
   Duration:  p50=20ms  p95=80ms  p99=400ms   (a latency histogram, not just an average)

   USE (for a RESOURCE, e.g. a CPU or disk):
   Utilization: 85% busy               <- how much of the resource's capacity is in use
   Saturation:  12 requests queued      <- work waiting because the resource is fully busy
   Errors:      2 disk I/O errors/min   <- resource-level failures, distinct from request errors
```
*Caption: RED covers what a service is doing (its traffic); USE covers the health of the resources that service depends on underneath.*

## 5. Runnable example

**Level 1 — Basic.** Compute RED metrics (rate, error rate, duration percentile) from a stream of simulated requests.

**Level 2 — Compute USE metrics for an underlying resource.** Track utilization and saturation for a connection pool.

**Level 3 — Correlate a RED symptom with a USE root cause.** Show rising request duration explained by rising resource saturation.

```java
// RedUseDemo.java
import java.util.*;

public class RedUseDemo {

    static class RequestRecord {
        final boolean failed;
        final int durationMs;
        RequestRecord(boolean failed, int durationMs) { this.failed = failed; this.durationMs = durationMs; }
    }

    // Level 1: RED metrics, computed from a batch of requests over a fixed time window.
    static void printRedMetrics(List<RequestRecord> requests, double windowSeconds) {
        double rate = requests.size() / windowSeconds;
        long errorCount = requests.stream().filter(r -> r.failed).count();
        double errorRate = (double) errorCount / requests.size();
        List<Integer> durations = requests.stream().map(r -> r.durationMs).sorted().toList();
        int p50 = durations.get((int) (durations.size() * 0.50));
        int p99 = durations.get(Math.min(durations.size() - 1, (int) (durations.size() * 0.99)));
        System.out.println("  RATE: " + String.format("%.1f", rate) + " req/sec");
        System.out.println("  ERRORS: " + String.format("%.1f", errorRate * 100) + "% (" + errorCount + "/" + requests.size() + ")");
        System.out.println("  DURATION: p50=" + p50 + "ms, p99=" + p99 + "ms");
    }

    // Level 2: USE metrics for a resource - a connection pool.
    static class ConnectionPool {
        final int totalConnections;
        int busyConnections;
        int queuedWaiters;
        ConnectionPool(int totalConnections) { this.totalConnections = totalConnections; }

        double utilization() { return (double) busyConnections / totalConnections; }
        int saturation() { return queuedWaiters; }
    }

    static void printUseMetrics(ConnectionPool pool) {
        System.out.println("  UTILIZATION: " + String.format("%.0f", pool.utilization() * 100) + "% (" + pool.busyConnections + "/" + pool.totalConnections + " connections busy)");
        System.out.println("  SATURATION: " + pool.saturation() + " requests queued, waiting for a free connection");
    }

    public static void main(String[] args) {
        // Level 1: a healthy period - low error rate, reasonable latency.
        List<RequestRecord> healthyPeriod = new ArrayList<>();
        for (int i = 0; i < 100; i++) healthyPeriod.add(new RequestRecord(i % 50 == 0, 20 + (i % 30)));
        System.out.println("RED metrics - healthy period:");
        printRedMetrics(healthyPeriod, 10.0);

        // Level 3: a degraded period - the connection pool is saturated, causing requests to queue and slow down.
        ConnectionPool pool = new ConnectionPool(10);
        pool.busyConnections = 10; // fully utilized
        pool.queuedWaiters = 25;    // and 25 MORE requests waiting for a free connection
        System.out.println("USE metrics - the connection pool, during the SAME degraded period:");
        printUseMetrics(pool);

        List<RequestRecord> degradedPeriod = new ArrayList<>();
        for (int i = 0; i < 100; i++) degradedPeriod.add(new RequestRecord(i % 20 == 0, 300 + (i % 400))); // much slower now
        System.out.println("RED metrics - the SAME degraded period (duration has spiked):");
        printRedMetrics(degradedPeriod, 10.0);

        System.out.println("correlation: RED shows duration spiked; USE shows WHY - the connection pool is saturated (25 queued), not just busy.");
    }
}
```

**How to run:** save as `RedUseDemo.java`, then run `java RedUseDemo.java`.

## 6. Walkthrough

1. `printRedMetrics(healthyPeriod, 10.0)` computes `rate = 100 / 10.0 = 10.0` requests/sec, an error rate around 2% (every 50th request marked failed), and duration percentiles from the sorted `durations` list; since durations here only range from 20-49ms, both `p50` and `p99` come out low, reflecting a healthy, fast service.
2. `printUseMetrics(pool)` reports `utilization = 10/10 = 100%` and `saturation = 25` — the pool is not just busy, it has a real backlog of 25 requests waiting for a connection that is not available, which is the leading indicator of a genuine bottleneck, distinct from utilization alone.
3. `printRedMetrics(degradedPeriod, 10.0)` computes duration percentiles from a much wider, slower range (300-699ms instead of 20-49ms), producing dramatically higher `p50` and `p99` values than the healthy period — this is the *symptom* that would show up first on a dashboard or alert.
4. Reading the two sets of output together tells the real diagnostic story: the RED metrics show duration has spiked (a symptom visible from the service's own perspective), and the USE metrics for the underlying connection pool resource show exactly why — it is fully utilized *and* saturated with 25 queued requests, meaning new requests must wait for a connection to free up before they can even start being served, directly explaining the latency spike.
5. This is the intended relationship between the two frameworks: RED tells you *that* something is wrong with a service's observable behavior; USE, applied to the resources that service depends on, is often where you find *why* — without checking USE metrics, the connection-pool saturation (the actual root cause) would have remained invisible, even with perfect RED metrics on the service itself.

## 7. Gotchas & takeaways

> Gotcha: monitoring only utilization for a resource, without also tracking saturation, can miss a serious bottleneck — a resource sitting at 70% utilization looks "fine" by that number alone, but if requests are already queuing because of bursty demand patterns, saturation will show the real problem that utilization alone hides; always track both together for any shared resource.

- RED gives a minimal, sufficient checklist for monitoring any request-driven service: rate, errors, and duration.
- USE gives the same for underlying resources: utilization, saturation, and errors — and saturation is often the more important, earlier warning signal than utilization alone.
- A RED-level symptom (rising duration) is often best explained by checking USE metrics on the resources that service depends on.
- Related concepts: [Metrics (counters, gauges, histograms)](0187-metrics-counters-gauges-histograms.md) (the underlying metric types RED and USE are built from), [Dashboards & SLO-based alerting](0190-dashboards-slo-based-alerting.md) (where RED and USE metrics are typically visualized and alerted on), [Tail latency & percentiles (p50/p95/p99)](0126-tail-latency-percentiles-p50-p95-p99.md) (the deeper treatment of the "D" in RED).
