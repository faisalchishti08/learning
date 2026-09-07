---
card: system-design
gi: 125
slug: throughput-vs-latency
title: Throughput vs latency
---

## 1. What it is

**Latency** is how long a single request takes, from start to finish — measured in time (milliseconds). **Throughput** is how many requests a system can complete per unit of time — measured in a rate (requests per second). They are related but distinct: a system can have low latency (each request is fast) but low throughput (it can only handle a few at a time), or high throughput but high latency (it processes huge volume, but each individual request takes a while).

## 2. Why & when

Optimizing for the wrong one causes real problems: a system tuned purely for throughput (e.g. batching requests to process many at once) can make individual requests wait longer for their batch to fill up, hurting latency for interactive users. A system tuned purely for low latency (processing everything immediately, one at a time) can leave capacity underused and cap overall throughput lower than a batched approach could achieve. Know which one your specific use case actually needs: an interactive user-facing API needs low latency (users notice delay directly); a nightly batch data pipeline needs high throughput (total completion time matters, not any single record's processing time).

## 3. Core concept

- **Latency:** time for one request, from the client's perspective — send, wait, receive response.
- **Throughput:** requests completed per second, from the system's perspective — a capacity measure, not a per-request measure.
- **The relationship via concurrency (Little's Law):** roughly, `throughput = concurrency / latency` — for a fixed level of concurrent in-flight requests, lower latency per request directly yields higher throughput.
- **Batching trades latency for throughput:** grouping several requests together to process at once (see [batching & request coalescing](0127-batching-request-coalescing.md)) can raise total throughput, but each individual request now waits for the batch to be ready — a latency cost for a throughput gain.
- **Concurrency trades resource usage for both:** processing more requests in parallel can raise throughput without directly hurting each request's own latency — until the underlying resources (CPU, database connections) become the bottleneck, at which point added concurrency starts increasing latency instead (queueing).
- **They must both be measured, not assumed:** a system can look fine on average throughput while individual users experience unacceptable latency — this is why latency is more often examined as [percentiles](0126-tail-latency-percentiles-p50-p95-p99.md), not just an average.

## 4. Diagram

```
LOW LATENCY, LOW THROUGHPUT:          HIGH THROUGHPUT, HIGHER LATENCY (batched):

  req1: [--5ms--] done                 req1,req2,req3,req4 queue up...
  req2:          [--5ms--] done        (wait up to 20ms for batch to fill)
  req3:                   [--5ms--]    [-----process all 4 at once-----] done
  (one at a time, fast each, but        (req1 actually took 20+ms total,
   only 200 req/sec max this way)        but system processed 4 per batch
                                          -> higher requests/sec overall)
```
*Caption: processing one at a time keeps latency low but caps throughput; batching raises throughput at the cost of each request's own latency.*

## 5. Runnable example

**Level 1 — Basic.** Measure latency (time per request) and throughput (requests per second) for a one-at-a-time strategy.

**Level 2 — Batching trade-off.** Compare per-request latency and total throughput when requests are batched instead.

**Level 3 — Concurrency's effect.** Show throughput rising with concurrency until a bottleneck caps it, and how latency rises past that point.

```java
// ThroughputVsLatency.java
import java.util.*;

public class ThroughputVsLatency {

    static int processingTimeMs = 5; // simulated fixed cost to actually do the work for one request

    public static void main(String[] args) {
        // Level 1: one-at-a-time - low latency per request, throughput bounded by 1000/processingTimeMs.
        int numRequests = 10;
        long totalTimeOneAtATime = (long) numRequests * processingTimeMs;
        double throughputOneAtATime = 1000.0 * numRequests / totalTimeOneAtATime;
        System.out.println("one-at-a-time: latency per request = " + processingTimeMs + "ms, "
            + "throughput = " + throughputOneAtATime + " req/sec");

        // Level 2: batching - wait for a batch to fill, then process all at once.
        int batchSize = 4;
        int batchWaitMs = 15; // time spent waiting for the batch to fill
        int batchProcessMs = 8; // time to process the whole batch together (cheaper per-item than one-by-one)
        int latencyPerRequestBatched = batchWaitMs + batchProcessMs; // a request in this batch waits, THEN processes
        double throughputBatched = 1000.0 * batchSize / (batchWaitMs + batchProcessMs);
        System.out.println("batched (size=" + batchSize + "): latency per request = " + latencyPerRequestBatched + "ms (HIGHER), "
            + "throughput = " + throughputBatched + " req/sec (HIGHER)");

        // Level 3: concurrency - throughput rises with concurrency, until a bottleneck (e.g. 4 DB connections) caps it.
        int maxConcurrency = 4; // e.g. a connection pool limit
        for (int concurrency = 1; concurrency <= 6; concurrency++) {
            int effectiveConcurrency = Math.min(concurrency, maxConcurrency);
            double throughputAtConcurrency = 1000.0 * effectiveConcurrency / processingTimeMs;
            double latencyAtConcurrency = processingTimeMs * ((double) concurrency / effectiveConcurrency); // queueing once past the cap
            System.out.printf("concurrency=%d -> throughput=%.1f req/sec, latency=%.1fms%s%n",
                concurrency, throughputAtConcurrency, latencyAtConcurrency,
                concurrency > maxConcurrency ? " (queueing past the bottleneck)" : "");
        }
    }
}
```

**How to run:** save as `ThroughputVsLatency.java`, then run `java ThroughputVsLatency.java`.

## 6. Walkthrough

1. Level 1 computes throughput for processing requests one at a time: with a fixed `5ms` cost per request, the theoretical maximum throughput is `1000 / 5 = 200` requests per second, and each request's own latency stays exactly `5ms`.
2. Level 2 models batching: a request must first wait up to `batchWaitMs` for the batch to fill, then the whole batch is processed together in `batchProcessMs`. `latencyPerRequestBatched` (`23ms`) is clearly worse than the one-at-a-time `5ms`.
3. But `throughputBatched` computes to processing 4 requests every `23ms`, which works out higher than the one-at-a-time throughput — the trade is explicit: worse latency per request, better total throughput.
4. Level 3 loops `concurrency` from 1 up to 6, capping the *effective* concurrency at `maxConcurrency = 4` (modeling a resource limit like a connection pool). While `concurrency <= 4`, throughput rises linearly and latency stays flat at `5ms`.
5. Once `concurrency` exceeds `4`, `effectiveConcurrency` stays capped at `4` (throughput plateaus), but `latencyAtConcurrency` starts rising, since extra requests must now queue behind the 4 that can actually run — demonstrating that pushing concurrency past a real bottleneck no longer buys more throughput, it only adds queueing latency.

## 7. Gotchas & takeaways

> Gotcha: a dashboard showing "throughput is fine" says nothing about whether individual users are having a good experience — a system can sustain high average throughput while a meaningful fraction of requests suffer badly degraded latency, especially once concurrency pushes past a real bottleneck. Always pair a throughput number with a latency number (ideally at a high percentile) before declaring a system healthy.

- Latency measures time for one request; throughput measures requests completed per unit time — related, but not the same thing, and not always improved by the same changes.
- Batching typically raises throughput at the cost of individual request latency; the right choice depends on whether your workload is interactive or bulk/batch in nature.
- Increasing concurrency raises throughput only until a real bottleneck is hit, after which additional concurrency adds queueing latency instead of more throughput.
- Related concepts: [Tail latency & percentiles (p50/p95/p99)](0126-tail-latency-percentiles-p50-p95-p99.md) (why latency needs more than an average to understand), [Batching & request coalescing](0127-batching-request-coalescing.md) (the specific technique explored in Level 2), [Load shedding & graceful degradation](0124-load-shedding-graceful-degradation.md) (protecting latency for accepted requests by rejecting excess).
