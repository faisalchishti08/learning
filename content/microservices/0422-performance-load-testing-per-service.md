---
card: microservices
gi: 422
slug: performance-load-testing-per-service
title: "Performance & load testing per service"
---

## 1. What it is

**Performance testing** measures how a service behaves under expected and extreme load — its latency at various percentiles, its maximum sustainable throughput, and how gracefully (or not) it degrades as load increases — by sending it real, simulated traffic and measuring the results, rather than guessing from code review alone. **Load testing** is the specific technique of generating that traffic: ramping request volume up to a target level (or beyond it) and observing what happens. Done **per service**, this means measuring one service's own capacity and behavior in isolation, which is both more actionable (you know exactly which service needs tuning) and more tractable (you don't need the whole system running at scale) than only ever load testing the system as a whole.

## 2. Why & when

You reach for performance testing whenever a service's capacity is a real question with a real business consequence — before a launch, before a known traffic spike (a sale event, a marketing campaign), or any time latency or throughput requirements are part of what "correct" means for a service, not just its functional behavior.

- **Correctness and performance are different questions, and passing one says nothing about the other.** A service can return the exactly right response, every time, in a functional test suite, and still fall over under 10x its normal traffic because a database connection pool is too small or an algorithm that's fine at low volume turns out to be quadratic.
- **Capacity limits are specific to each service and change with every deploy.** A new feature, a new dependency, a new query — any of these can silently shrink a service's safe operating envelope, and the only reliable way to know the new envelope is to measure it, not assume it's unchanged.
- **Per-service testing localizes the bottleneck.** If you only ever load test the whole system end to end, a slowdown tells you "the system is slow," but not which of a dozen services is the actual bottleneck. Testing each service's own capacity in isolation (with its dependencies either real or realistically stubbed) tells you precisely where the ceiling is.
- **Percentiles matter more than averages.** An average latency of 80ms can hide a p99 of 4 seconds affecting one in a hundred users — and in a system with many services chained together, that one-in-a-hundred slow response at each hop compounds, so knowing your own service's tail latency, not just its average, is essential.

You run performance tests as a recurring practice — not a one-time pre-launch checkbox — because capacity changes with every meaningful code change, and ideally as an automated gate in CI/CD that flags a regression (a new deploy that dropped throughput by 30%, or pushed p99 latency past a defined budget) before it ships.

## 3. Core concept

Picture stress-testing a bridge before it opens. You don't just check that one car can cross it safely — you measure how many cars per minute it can handle before traffic backs up, what happens as trucks (heavier load) join the mix, and at what point the bridge itself, not just traffic flow, becomes unsafe. Performance testing does the same thing for a service: not just "does it work," but "how much can it handle, how does it behave as load increases, and where exactly does it break."

Three key metrics anchor any load test:

1. **Latency percentiles** — not the average, but specific points in the distribution: p50 (median), p95, p99. A p99 of 2 seconds means 1% of requests take *at least* 2 seconds — often the difference between "feels fast" and "some users are having a bad time," and the number that matters most for [SLIs and SLOs](0359-sli-slo-sla-error-budgets.md).
2. **Throughput** — requests per second the service can sustain while staying within its latency and error-rate targets, not the peak it can briefly absorb before falling over.
3. **Error rate under load** — whether requests start failing (timeouts, 5xxs, connection refusals) as load increases, and at what load level that starts happening.

Load tests come in a few common shapes, each answering a different question:

| Test type | Question it answers |
|---|---|
| **Load test** | Can the service handle its expected, normal peak traffic? |
| **Stress test** | At what point does the service break, and how does it fail (gracefully or catastrophically)? |
| **Soak test** | Does the service stay healthy under sustained load over a long period (catching memory leaks, connection leaks, slow degradation)? |
| **Spike test** | Can the service handle a sudden, sharp jump in traffic (a flash sale, a viral link)? |

Testing per service, rather than only the whole system, means isolating a target service and sending it traffic directly (or through the same gateway path a real request would take), with its own downstream dependencies either real (for the most realistic numbers) or virtualized with realistic latency (see [service virtualization](0419-service-virtualization-stubbing-dependencies.md)) so the numbers reflect the service's *own* processing capacity and aren't dominated by a dependency's separate bottleneck.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A load generator ramps request volume against a target service while a latency histogram shows most requests fast but a long tail of slow ones, illustrating why p99 latency matters more than the average" font-family="sans-serif">
  <rect x="30" y="30" width="120" height="45" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="57" fill="#79c0ff" font-size="10" text-anchor="middle">Load generator</text>
  <line x1="150" y1="52" x2="230" y2="52" stroke="#79c0ff" stroke-width="2"/>
  <text x="190" y="42" fill="#79c0ff" font-size="9" text-anchor="middle">ramping RPS</text>

  <rect x="230" y="30" width="140" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="57" fill="#e6edf3" font-size="10" text-anchor="middle">Target service</text>

  <text x="320" y="110" fill="#e6edf3" font-size="11" text-anchor="middle">Latency distribution</text>
  <rect x="60" y="200" width="14" height="10" fill="#6db33f"/>
  <rect x="90" y="185" width="14" height="25" fill="#6db33f"/>
  <rect x="120" y="150" width="14" height="60" fill="#6db33f"/>
  <rect x="150" y="130" width="14" height="80" fill="#6db33f"/>
  <rect x="180" y="145" width="14" height="65" fill="#6db33f"/>
  <rect x="210" y="175" width="14" height="35" fill="#6db33f"/>
  <rect x="240" y="195" width="14" height="15" fill="#79c0ff"/>
  <rect x="270" y="205" width="14" height="5" fill="#f0883e"/>
  <rect x="300" y="207" width="14" height="3" fill="#f85149"/>
  <line x1="150" y1="120" x2="150" y2="215" stroke="#8b949e" stroke-dasharray="2,2"/>
  <text x="150" y="225" fill="#8b949e" font-size="8" text-anchor="middle">p50</text>
  <line x1="270" y1="120" x2="270" y2="215" stroke="#8b949e" stroke-dasharray="2,2"/>
  <text x="270" y="225" fill="#8b949e" font-size="8" text-anchor="middle">p99</text>
  <text x="480" y="170" fill="#f85149" font-size="9" text-anchor="middle">the long tail (p99) is invisible</text>
  <text x="480" y="184" fill="#f85149" font-size="9" text-anchor="middle">in an AVERAGE latency number</text>
</svg>

A load test ramps traffic against a target service and reveals its full latency distribution, where the long tail (p99) matters more than the average for real user experience.

## 5. Runnable example

Scenario: an `OrderLookupService` endpoint we load test. We first measure latency and throughput at a normal load level, then compute proper percentiles (not just an average) at higher load, then run a stress test that ramps load until the service's error rate crosses a threshold, identifying its actual breaking point.

### Level 1 — Basic

```java
// File: LoadTestBasicThroughput.java -- simulate a load test at a FIXED
// request rate, measuring average latency and throughput -- the simplest
// possible load test, useful as a starting baseline.
import java.util.*;

public class LoadTestBasicThroughput {
    // Simulates a service call with latency that grows slightly as
    // internal load (a shared resource, e.g. a connection pool) fills up.
    static long simulateOrderLookup(int concurrentInFlight) {
        long baseLatencyMs = 20;
        long congestionPenaltyMs = Math.max(0, (concurrentInFlight - 10)) * 3L; // penalty kicks in past 10 in-flight
        return baseLatencyMs + congestionPenaltyMs;
    }

    public static void main(String[] args) {
        int totalRequests = 200;
        int concurrentInFlight = 5; // fixed, modest concurrency for this basic test
        List<Long> latencies = new ArrayList<>();

        for (int i = 0; i < totalRequests; i++) {
            latencies.add(simulateOrderLookup(concurrentInFlight));
        }

        double avgLatency = latencies.stream().mapToLong(Long::longValue).average().orElse(0);
        System.out.println("Requests: " + totalRequests + ", concurrency: " + concurrentInFlight);
        System.out.println("Average latency: " + avgLatency + "ms");
    }
}
```

How to run: `java LoadTestBasicThroughput.java`

`simulateOrderLookup` models a service whose latency stays flat at low concurrency but starts climbing once the number of in-flight requests exceeds 10 — a simplified stand-in for a real resource limit like a JDBC connection pool. At a fixed, modest concurrency of 5, every simulated call returns the same 20ms baseline latency, so the average is unremarkable. This is a useful sanity check but, as the next level shows, an average alone hides exactly the information that matters most.

### Level 2 — Intermediate

```java
// File: LoadTestPercentiles.java -- the SAME service, now under HIGHER,
// VARIABLE concurrency, measuring PERCENTILES (p50/p95/p99) instead of
// just an average -- revealing a long tail the average alone would hide.
import java.util.*;

public class LoadTestPercentiles {
    static final Random random = new Random(7);

    static long simulateOrderLookup(int concurrentInFlight) {
        long baseLatencyMs = 20;
        long congestionPenaltyMs = Math.max(0, (concurrentInFlight - 10)) * 3L;
        // Occasionally (5% of calls) a request hits a slow path (e.g. a cache miss
        // forcing a real database read) -- this is what creates the long tail.
        long cacheMissPenaltyMs = random.nextDouble() < 0.05 ? 400 : 0;
        return baseLatencyMs + congestionPenaltyMs + cacheMissPenaltyMs;
    }

    static long percentile(List<Long> sortedLatencies, double p) {
        int index = (int) Math.ceil(p * sortedLatencies.size()) - 1;
        return sortedLatencies.get(Math.max(0, Math.min(index, sortedLatencies.size() - 1)));
    }

    public static void main(String[] args) {
        int totalRequests = 1000;
        int concurrentInFlight = 25; // higher load than Level 1
        List<Long> latencies = new ArrayList<>();

        for (int i = 0; i < totalRequests; i++) {
            latencies.add(simulateOrderLookup(concurrentInFlight));
        }

        List<Long> sorted = new ArrayList<>(latencies);
        Collections.sort(sorted);
        double avg = latencies.stream().mapToLong(Long::longValue).average().orElse(0);

        System.out.println("Requests: " + totalRequests + ", concurrency: " + concurrentInFlight);
        System.out.println("Average latency: " + String.format("%.1f", avg) + "ms");
        System.out.println("p50: " + percentile(sorted, 0.50) + "ms");
        System.out.println("p95: " + percentile(sorted, 0.95) + "ms");
        System.out.println("p99: " + percentile(sorted, 0.99) + "ms");
        System.out.println("The average looks fine; p99 tells the real story about the long tail.");
    }
}
```

How to run: `java LoadTestPercentiles.java`

`simulateOrderLookup` now has two sources of latency variation: a congestion penalty from concurrency (as before) and a 5%-probability "cache miss" penalty that adds 400ms — modeling a realistic long-tail cause, where most requests are served from a fast path but a meaningful minority hit a much slower one. `percentile` sorts all recorded latencies and picks out specific rank positions. The output makes the core lesson concrete: the average latency, dragged only slightly by the 5% of slow requests, looks perfectly healthy, while p99 — which specifically captures that slow tail — reveals a dramatically worse number, exactly the gap that a real user experiencing the slow path (and a real SLO tracking p99, per [SLI/SLO/SLA & error budgets](0359-sli-slo-sla-error-budgets.md)) would actually feel.

### Level 3 — Advanced

```java
// File: LoadTestStressFindBreakingPoint.java -- a STRESS TEST: ramp
// concurrency upward in steps until the service's error rate crosses a
// threshold, identifying the ACTUAL breaking point -- the production-
// flavored question "how much traffic can this service really handle
// before it falls over, and how does it fail?"
import java.util.*;

public class LoadTestStressFindBreakingPoint {
    static final Random random = new Random(11);
    static final int MAX_POOL_SIZE = 30; // a hard resource limit, e.g. a connection pool

    record CallResult(boolean succeeded, long latencyMs) {}

    static CallResult simulateOrderLookup(int concurrentInFlight) {
        if (concurrentInFlight > MAX_POOL_SIZE) {
            // past the hard limit, requests are REJECTED outright (e.g. pool exhausted, connection refused)
            return new CallResult(false, 0);
        }
        long baseLatencyMs = 20;
        long congestionPenaltyMs = Math.max(0, (concurrentInFlight - 10)) * 5L;
        boolean timedOut = congestionPenaltyMs > 200 && random.nextDouble() < 0.5; // severe congestion sometimes times out
        if (timedOut) return new CallResult(false, 5000); // a slow failure: worse than a fast rejection
        return new CallResult(true, baseLatencyMs + congestionPenaltyMs);
    }

    public static void main(String[] args) {
        int[] concurrencyLevels = {5, 15, 25, 32, 40};
        double errorRateThreshold = 0.05; // stress test's "breaking point" definition: >5% errors
        boolean brokenPointFound = false;

        for (int concurrency : concurrencyLevels) {
            int requestsAtThisLevel = 200;
            int errors = 0;
            long totalLatency = 0;
            for (int i = 0; i < requestsAtThisLevel; i++) {
                CallResult result = simulateOrderLookup(concurrency);
                if (!result.succeeded()) errors++;
                totalLatency += result.latencyMs();
            }
            double errorRate = (double) errors / requestsAtThisLevel;
            double avgLatency = (double) totalLatency / requestsAtThisLevel;

            System.out.printf("concurrency=%-3d errorRate=%.1f%% avgLatency=%.1fms%n",
                    concurrency, errorRate * 100, avgLatency);

            if (!brokenPointFound && errorRate > errorRateThreshold) {
                brokenPointFound = true;
                System.out.println("  -> BREAKING POINT FOUND at concurrency=" + concurrency
                        + " (error rate " + (errorRate * 100) + "% exceeds " + (errorRateThreshold * 100) + "% threshold)");
            }
        }
    }
}
```

How to run: `java LoadTestStressFindBreakingPoint.java`

This ramps concurrency through five levels (5, 15, 25, 32, 40) instead of testing a single fixed load, mirroring how a real stress test steps traffic upward to find the exact point where a service's behavior changes qualitatively — not just "slower," but "failing." `MAX_POOL_SIZE` models a hard resource ceiling (like a JDBC connection pool size); once concurrency exceeds it, requests are rejected outright. Below that hard ceiling, severe congestion can still cause slow timeouts, which is deliberately modeled as *worse* than a fast rejection (`5000ms` instead of failing immediately) — a realistic and important distinction, because a service that fails fast under overload is far easier for callers to handle gracefully (their own timeouts and circuit breakers react quickly) than one that fails slowly, tying up caller resources while it does.

## 6. Walkthrough

Trace `LoadTestStressFindBreakingPoint.main` across its five concurrency levels. **First**, at `concurrency=5`, every one of the 200 simulated calls has `concurrentInFlight` (5) well under `MAX_POOL_SIZE` (30) and under the congestion threshold (10), so `congestionPenaltyMs` is 0, no timeouts occur, and the loop records a 0% error rate with a low average latency around 20ms.

**Next**, at `concurrency=15`, `congestionPenaltyMs` becomes `(15-10)*5 = 25`, still well under the 200ms threshold that can trigger a timeout, so this level still reports 0% errors, with average latency ticking up modestly to around 45ms.

**Then**, at `concurrency=25`, `congestionPenaltyMs` becomes `(25-10)*5 = 75` — still under 200, so still no timeouts, but average latency has climbed further, to around 95ms, showing degradation *before* any actual failures appear — an important signal in its own right for anyone watching latency-based alerts.

At `concurrency=32`, two things happen simultaneously: `32 > MAX_POOL_SIZE` (30) means some in-flight requests are now hitting the hard rejection path, *and* `congestionPenaltyMs` for requests within the pool limit would be `(30-10)*5 = 100`, still under the 200ms timeout trigger in this simplified model — so at this level the errors are dominated by outright pool-exhaustion rejections rather than timeouts. This is very likely the level where `errorRate` first exceeds the 5% threshold, since every call simulated with `concurrentInFlight = 32` exceeds `MAX_POOL_SIZE` and is rejected, giving a 100% error rate at this level in this simplified model — printing the "BREAKING POINT FOUND" message.

**Finally**, `concurrency=40` is tested too (a stress test intentionally keeps pushing past the first sign of breakage, to understand the full failure curve, not just the first crack), showing the error rate stays high, confirming the service has genuinely passed its safe operating envelope rather than just having a momentary blip.

```
concurrency=5   errorRate=0.0% avgLatency=20.0ms
concurrency=15  errorRate=0.0% avgLatency=45.0ms
concurrency=25  errorRate=0.0% avgLatency=95.0ms
concurrency=32  errorRate=100.0% avgLatency=0.0ms
  -> BREAKING POINT FOUND at concurrency=32 (error rate 100.0% exceeds 5.0% threshold)
concurrency=40  errorRate=100.0% avgLatency=0.0ms
```

## 7. Gotchas & takeaways

> Load testing a service with its downstream dependencies fully mocked to return instantly can produce numbers that are wildly optimistic and useless for capacity planning — a service's real bottleneck is often a downstream call, a database, or a shared connection pool, none of which a zero-latency stub exercises. Use [service virtualization](0419-service-virtualization-stubbing-dependencies.md) configured with *realistic* latency for dependencies you must stub, or better, run against real dependencies at realistic scale wherever practical.

- Measure percentiles (p95, p99), not just averages — an average latency can look perfectly healthy while a meaningful fraction of real users have a genuinely bad experience, exactly as Level 2 demonstrates.
- Run load, stress, soak, and spike tests for different questions: normal-capacity confidence, breaking-point discovery, long-duration stability, and sudden-traffic resilience are not the same test.
- A fast failure (an immediate rejection) is usually far better for system-wide resiliency than a slow one (a timeout) — a slow failure ties up caller resources and can cascade, exactly the concern [chaos and resiliency testing](0421-chaos-resiliency-testing.md) is designed to catch when combined with load.
- Test per service to localize bottlenecks precisely, but periodically validate with a full-system load test too — per-service capacity numbers can be optimistic if they don't account for shared infrastructure (a shared database, a shared network) under simultaneous load from multiple services.
- Wire performance testing into CI/CD as a recurring, automated gate — capacity is not a fact you establish once before launch; it shifts with every meaningful code change, and a regression caught in CI is far cheaper than one discovered during a real traffic spike.
