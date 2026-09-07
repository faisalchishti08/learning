---
card: system-design
gi: 126
slug: tail-latency-percentiles-p50-p95-p99
title: Tail latency & percentiles (p50/p95/p99)
---

## 1. What it is

A **latency percentile** describes what fraction of requests finished at or below a given time. **p50** (the median) is the latency below which 50% of requests finish. **p95** is the latency below which 95% finish. **p99** is the same for 99%. **Tail latency** refers specifically to the slower end — p95, p99, and beyond — the requests that take noticeably longer than typical.

## 2. Why & when

An average latency hides exactly the information that matters most: it can look perfectly healthy even while a meaningful number of real users experience a slow, frustrating request. A handful of very slow outliers barely move an average, but they show up clearly at p95 or p99. Track tail latency, not just averages, any time you care about the actual experience of real users, since even 1% of requests being slow means 1 in 100 users has a bad time — and at scale, that can be thousands of people per day.

## 3. Core concept

- **Average is misleading:** one request taking 10 seconds among 99 requests taking 10ms barely changes the average (about 108ms), but it is a genuinely terrible experience for that one user, and hints at a real, recurring problem if it happens regularly.
- **p50 (median):** the "typical" experience — useful as a baseline, but says nothing about how bad the worst experiences are.
- **p95 / p99:** the slower tail — these tell you what your less-lucky users, or your less-lucky requests (larger inputs, cache misses, contended locks), actually experience.
- **Why tails matter more at scale:** if a service is called multiple times to render one page (search results calling five backend services), the odds that *at least one* of those calls lands in the slow tail rise quickly — a single slow p99 call can dominate the overall page's latency even though it's "only" 1% of calls.
- **SLOs (Service Level Objectives) are usually stated at a percentile:** "p99 latency under 200ms" is a far more meaningful target than "average latency under 50ms", because it bounds the experience of the worst-affected users directly, not just the typical one.

## 4. Diagram

```
100 sorted request latencies (fastest to slowest), in ms:

  [10, 11, 12, 13, ... , 15 (this is p50/median, position 50) ...
   ... , 40 (this is p95, position 95) ...
   ... , 95 (this is p99, position 99), 5000 (position 100, an outlier)]

  AVERAGE of all 100 = ~62ms   <- distorted upward by the one 5000ms outlier
  p50 = 15ms   <- the typical request
  p95 = 40ms   <- 95% of requests are this fast or faster
  p99 = 95ms   <- the slowest 1% start here
```
*Caption: percentiles describe the actual distribution's shape; a single extreme outlier can distort an average far more than it distorts p50 or even p99.*

## 5. Runnable example

**Level 1 — Basic.** Compute p50, p95, and p99 from a sorted list of latencies.

**Level 2 — Average vs percentile.** Show how one outlier distorts the average far more than it distorts p99.

**Level 3 — Compound tail risk.** Simulate a page that calls 5 backend services, and compute the odds at least one call is slow.

```java
// TailLatency.java
import java.util.*;

public class TailLatency {

    static double percentile(List<Integer> sortedLatencies, double p) {
        int index = (int) Math.ceil(p / 100.0 * sortedLatencies.size()) - 1;
        index = Math.max(0, Math.min(index, sortedLatencies.size() - 1));
        return sortedLatencies.get(index);
    }

    public static void main(String[] args) {
        // Level 1: 100 latencies, mostly fast, a few slower - compute percentiles.
        List<Integer> latencies = new ArrayList<>();
        Random rand = new Random(42);
        for (int i = 0; i < 95; i++) latencies.add(10 + rand.nextInt(20)); // most requests: 10-30ms
        for (int i = 0; i < 4; i++) latencies.add(80 + rand.nextInt(40));  // a slower tail: 80-120ms
        latencies.add(5000); // one extreme outlier

        Collections.sort(latencies);
        System.out.println("p50 (median): " + percentile(latencies, 50) + "ms");
        System.out.println("p95: " + percentile(latencies, 95) + "ms");
        System.out.println("p99: " + percentile(latencies, 99) + "ms");

        // Level 2: compare to the average - see how much the single outlier distorts it.
        double average = latencies.stream().mapToInt(Integer::intValue).average().orElse(0);
        System.out.printf("average: %.1fms (distorted upward by the single 5000ms outlier)%n", average);
        System.out.println("-> average looks much worse than p50/p95, yet says nothing about how MANY users are affected");

        // Level 3: compound tail risk - a page calling 5 backend services, each with a 1% chance of a slow (p99) response.
        double chanceOneCallIsSlow = 0.01; // 1% of calls land in the p99+ tail
        int numCalls = 5;
        double chanceAllCallsFast = Math.pow(1 - chanceOneCallIsSlow, numCalls);
        double chanceAtLeastOneSlow = 1 - chanceAllCallsFast;
        System.out.printf("with %d backend calls per page, each with a %.0f%% chance of hitting the slow tail:%n", numCalls, chanceOneCallIsSlow * 100);
        System.out.printf("chance the WHOLE PAGE is slow (at least one call is slow) = %.1f%%%n", chanceAtLeastOneSlow * 100);
        System.out.println("-> a 1% per-call tail becomes a much bigger risk once several calls are combined into one page");
    }
}
```

**How to run:** save as `TailLatency.java`, then run `java TailLatency.java`.

## 6. Walkthrough

1. `latencies` is built to resemble a realistic distribution: 95 fast requests (10–30ms), 4 moderately slow ones (80–120ms), and one extreme outlier (5000ms) — then sorted ascending.
2. `percentile` finds the value at the position corresponding to a given percentage of the sorted list; `percentile(latencies, 50)` lands inside the fast group, `percentile(latencies, 95)` lands near the boundary of the fast/slow groups, and `percentile(latencies, 99)` lands inside the moderately-slow group.
3. The `average` calculation sums all 101 values and divides by the count; because it includes the single `5000ms` value, it comes out noticeably higher than even p95 or p99 — despite only one of 101 requests actually being that slow.
4. This directly illustrates the gotcha: a system whose average looks concerning might actually have excellent p50/p95/p99, if the average is being pulled by one rare, extreme value, while a system with fine-looking averages could have a genuinely bad p99 affecting many more users.
5. Level 3 computes `chanceAtLeastOneSlow` using the complement rule: the probability all 5 independent calls are fast, subtracted from 1. Even with only a 1% per-call chance of hitting the slow tail, combining 5 calls raises the chance that the overall page experience is slow to roughly 4.9% — showing why tail latency compounds and matters even more in systems with many internal calls per user-facing request.

## 7. Gotchas & takeaways

> Gotcha: percentiles computed by simply averaging percentiles from multiple servers (e.g. "average of each server's own p99") are not mathematically valid — you cannot average percentiles like you can average simple sums. Percentiles must be computed from the full, combined set of raw latency values across all servers, not from an average of each server's separately computed percentile.

- Percentiles describe the shape of a latency distribution; p50 shows the typical case, while p95 and p99 reveal the tail experience an average can hide entirely.
- A single extreme outlier can distort an average far more than it distorts even a high percentile, making averages a poor tool for judging user experience.
- Combining several calls into one user-facing operation compounds tail risk: even a small per-call chance of hitting the slow tail becomes a much larger chance that the whole operation is slow.
- Related concepts: [Throughput vs latency](0125-throughput-vs-latency.md) (the broader trade-off percentiles help you evaluate correctly), [Load shedding & graceful degradation](0124-load-shedding-graceful-degradation.md) (a common response to protecting tail latency under load).
