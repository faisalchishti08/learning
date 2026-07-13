---
card: microservices
gi: 357
slug: use-method-utilization-saturation-errors
title: "USE method (Utilization, Saturation, Errors)"
---

## 1. What it is

The **USE method** is a standard set of three metrics for every *resource* (CPU, memory, disk I/O, a connection pool, a thread pool) rather than for requests: **Utilization** (the percentage of time the resource is busy doing work), **Saturation** (the amount of work queued up waiting for the resource, beyond what it's currently handling), and **Errors** (the count of error events specific to that resource, like failed disk writes or dropped connections). Where the [RED method](0356-red-method-rate-errors-duration.md) looks at services from the request side, USE looks at the underlying resources those requests actually consume.

## 2. Why & when

RED metrics can tell you a service is slow, but not *why* — the actual bottleneck could be CPU-bound work, an exhausted connection pool, memory pressure, or disk contention, and RED's request-level view doesn't distinguish between these. USE metrics target exactly this gap: by tracking utilization and saturation for each individual resource a service depends on, you can identify which specific resource is the bottleneck behind a RED-detected slowdown, rather than guessing.

Use USE metrics for every finite resource a service depends on — CPU, memory, a database connection pool, a thread pool, disk I/O — especially ones with a hard capacity limit, since saturation past that limit is exactly where request queuing and latency spikes originate. Pair USE with RED: RED metrics tell you *that* a service is degraded from the outside; USE metrics for its underlying resources tell you *which resource* and *why*, from the inside.

## 3. Core concept

Utilization is typically a percentage: `busyTime / totalTime`. Saturation is a queue depth or a count of work waiting beyond current capacity — for a connection pool, this might be "requests waiting for a connection because all connections are currently checked out." Errors are resource-specific failure counts, distinct from request-level errors: a connection pool exhaustion error, a disk write failure, an out-of-memory event.

```java
double utilization = busyConnections / (double) totalPoolSize; // e.g. 8/10 = 80% utilized
int saturation = requestsWaitingForConnection; // queued beyond capacity
int errors = connectionAcquisitionFailures; // resource-specific failures
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three panels for a connection pool: Utilization showing percentage busy, Saturation showing queued requests waiting for a connection, Errors showing connection acquisition failures">
  <rect x="20" y="20" width="185" height="130" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="112" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Utilization</text>
  <text x="112" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">% of capacity busy</text>

  <rect x="228" y="20" width="185" height="130" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="45" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Saturation</text>
  <text x="320" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">work queued, waiting</text>

  <rect x="435" y="20" width="185" height="130" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="528" y="45" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Errors</text>
  <text x="528" y="65" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">resource-specific failures</text>
</svg>

Utilization, Saturation, and Errors track a resource's health directly, revealing bottlenecks that request-level metrics alone can't pinpoint.

## 5. Runnable example

Scenario: a database connection pool under increasing load, first observed only via request-level latency (mysterious slowdown, cause unclear), then diagnosed with USE metrics revealing the pool itself is the bottleneck, and finally extended to alert specifically on saturation before it becomes a full outage.

### Level 1 — Basic

```java
// File: OnlyRequestLatencyVisible.java -- only REQUEST-level latency is
// tracked; the slowdown is visible, but its ROOT CAUSE is a mystery.
import java.util.*;

public class OnlyRequestLatencyVisible {
    static List<Long> requestLatenciesMs = new ArrayList<>();

    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) requestLatenciesMs.add(50L);  // early requests: fast
        for (int i = 0; i < 5; i++) requestLatenciesMs.add(2000L); // later requests: suddenly slow

        System.out.println("Request latencies: " + requestLatenciesMs);
        System.out.println("Latency clearly increased -- but WHY? CPU? Memory? A connection pool? "
                + "Request-level metrics alone can't say.");
    }
}
```

How to run: `java OnlyRequestLatencyVisible.java`

The recorded latencies clearly show a slowdown partway through, but nothing in this data indicates *why* — is the service CPU-bound, memory-constrained, or waiting on some other finite resource? RED-style request metrics alone can detect that something is wrong without explaining what.

### Level 2 — Intermediate

```java
// File: UseMetricsRevealThePool.java -- USE metrics for the connection
// pool specifically REVEAL it as the bottleneck: rising utilization and
// saturation correlate exactly with when latency started climbing.
import java.util.*;

public class UseMetricsRevealThePool {
    record PoolSnapshot(int timeStep, int busyConnections, int poolSize, int waitingForConnection) {}
    static List<PoolSnapshot> poolHistory = new ArrayList<>();

    static double utilization(PoolSnapshot s) { return 100.0 * s.busyConnections() / s.poolSize(); }

    public static void main(String[] args) {
        poolHistory.add(new PoolSnapshot(1, 3, 10, 0));  // 30% utilized, no queue -- healthy
        poolHistory.add(new PoolSnapshot(2, 6, 10, 0));  // 60% utilized, still no queue
        poolHistory.add(new PoolSnapshot(3, 10, 10, 4)); // 100% utilized, 4 requests QUEUED -- saturation begins
        poolHistory.add(new PoolSnapshot(4, 10, 10, 9)); // still 100%, saturation WORSENING

        System.out.println("Connection pool USE metrics over time:");
        for (PoolSnapshot s : poolHistory) {
            System.out.println("  t=" + s.timeStep() + ": utilization=" + utilization(s) + "%, saturation="
                    + s.waitingForConnection() + " requests waiting");
        }
        System.out.println("Utilization hit 100% and saturation started RISING at t=3 -- EXACTLY when request latency spiked in Level 1.");
    }
}
```

How to run: `java UseMetricsRevealThePool.java`

Each `PoolSnapshot` captures the connection pool's own utilization and saturation at a point in time. The data shows utilization climbing to `100%` and saturation (queued, waiting requests) beginning to rise at `t=3` — correlating directly with the moment request latency spiked in Level 1's data. This is exactly the diagnostic value of USE metrics: they pinpoint the connection pool, specifically, as the resource behind the observed slowdown, something request-level latency alone could never show.

### Level 3 — Advanced

```java
// File: AlertOnSaturationBeforeOutage.java -- alerts specifically on
// RISING saturation, catching the problem BEFORE the pool is fully
// exhausted and requests start failing outright, not just slowing down.
import java.util.*;

public class AlertOnSaturationBeforeOutage {
    record PoolSnapshot(int timeStep, int busyConnections, int poolSize, int waitingForConnection) {}
    static List<PoolSnapshot> poolHistory = new ArrayList<>();

    static double utilization(PoolSnapshot s) { return 100.0 * s.busyConnections() / s.poolSize(); }

    static void checkSaturationAlert(PoolSnapshot s) {
        if (s.waitingForConnection() > 0 && utilization(s) >= 90) {
            System.out.println("  ALERT at t=" + s.timeStep() + ": pool at " + utilization(s) + "% utilization with "
                    + s.waitingForConnection() + " requests QUEUED -- act BEFORE this becomes a full outage (e.g. scale the pool, investigate slow queries holding connections).");
        }
    }

    public static void main(String[] args) {
        poolHistory.add(new PoolSnapshot(1, 3, 10, 0));
        poolHistory.add(new PoolSnapshot(2, 6, 10, 0));
        poolHistory.add(new PoolSnapshot(3, 9, 10, 1));  // saturation JUST beginning
        poolHistory.add(new PoolSnapshot(4, 10, 10, 9)); // saturation SEVERE

        for (PoolSnapshot s : poolHistory) {
            System.out.println("t=" + s.timeStep() + ": utilization=" + utilization(s) + "%, saturation=" + s.waitingForConnection());
            checkSaturationAlert(s);
        }
        System.out.println("The alert fired at t=3, while saturation was STILL mild (1 request waiting) -- giving time to react BEFORE t=4's severe backlog.");
    }
}
```

How to run: `java AlertOnSaturationBeforeOutage.java`

`checkSaturationAlert` fires as soon as utilization crosses `90%` *and* there's any nonzero queue at all — deliberately triggering early, at `t=3` when only 1 request is waiting, rather than waiting until the situation is already severe at `t=4` with 9 requests queued. This is the practical value of tracking saturation specifically: it gives an early-warning signal while the problem is still small and recoverable (add pool capacity, kill a slow query holding a connection), rather than only noticing once the pool is already deeply backed up and users are experiencing serious delays or outright failures.

## 6. Walkthrough

Trace `AlertOnSaturationBeforeOutage.main` in order. **First**, the loop processes `t=1` (`busyConnections=3, waitingForConnection=0`): it prints the utilization (`30%`) and saturation (`0`), then calls `checkSaturationAlert`. Inside, `s.waitingForConnection() > 0` is `false` (it's `0`), so the `&&` short-circuits and no alert fires.

**At `t=2`** (`busyConnections=6, waitingForConnection=0`), the same happens: utilization is `60%`, but `waitingForConnection` is still `0`, so no alert fires.

**At `t=3`** (`busyConnections=9, waitingForConnection=1`), utilization is `90%` and `waitingForConnection` is `1`, which is greater than `0`. Both conditions of `checkSaturationAlert`'s `if` are now true (`90 >= 90` and `1 > 0`), so the alert fires, printing a message that the pool is significantly loaded with a queue just beginning to form.

**At `t=4`** (`busyConnections=10, waitingForConnection=9`), utilization is `100%` and the queue has grown to `9` — the alert condition is still true, and it fires again, but by this point the situation has already progressed to a much more severe backlog than at `t=3`.

**Finally**, `main` prints a closing observation: because the alert fired at `t=3`, while the queue was still just `1` request deep, an operator would have had a window to react — scaling the pool, or investigating whatever was holding connections too long — *before* the situation deteriorated to `t=4`'s much more serious 9-request backlog.

```
t=1: util=30%, sat=0   -> no alert
t=2: util=60%, sat=0   -> no alert
t=3: util=90%, sat=1   -> ALERT fires (early warning, still mild)
t=4: util=100%, sat=9  -> ALERT fires again (now severe -- t=3's warning gave time to act first)
```

## 7. Gotchas & takeaways

> Utilization alone, without saturation, can be misleading: a resource can sit at 100% utilization briefly under normal bursty load without ever queuing work, which is healthy — sustained high utilization *combined with* rising saturation is the real signal that a resource is becoming a genuine bottleneck, not utilization by itself.

- USE — Utilization, Saturation, Errors — targets individual *resources* (CPU, memory, connection pools, thread pools), complementing the [RED method](0356-red-method-rate-errors-duration.md)'s request-centric view.
- Saturation (queued work waiting beyond current capacity) is often the most actionable of the three, since it can be caught rising *before* a resource becomes fully exhausted and starts causing outright failures.
- Apply USE metrics to every finite resource a service depends on, especially ones with a hard capacity ceiling, to pinpoint the specific bottleneck behind a RED-detected slowdown.
- Together with RED and the [four golden signals](0358-four-golden-signals-latency-traffic-errors-saturation.md), USE completes a layered view: RED shows service-level symptoms, USE shows resource-level root causes.
