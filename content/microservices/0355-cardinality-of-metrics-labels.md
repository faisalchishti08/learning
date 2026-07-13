---
card: microservices
gi: 355
slug: cardinality-of-metrics-labels
title: "Cardinality of metrics & labels"
---

## 1. What it is

**Cardinality** of a metric is the number of distinct combinations of label (tag) values that metric can take on — a metric with labels `service` (10 possible values) and `statusCode` (say, 5 possible values) has a cardinality of up to `10 × 5 = 50` distinct time series. Adding a label with many possible values (like `userId`, which might have millions of distinct values) multiplies the metric's cardinality by that many, often turning a cheap, manageable metric into one that's prohibitively expensive to store and query.

## 2. Why & when

Metrics systems (Prometheus and similar) store one separate time series per unique combination of label values a metric is ever recorded with. A metric like `http_requests_total` with labels `method` and `status` stays cheap because both have a small, fixed set of possible values. The moment someone adds a label like `userId` or `orderId` to that same metric — intending to make it more useful for drilling into a specific user's or order's requests — the number of distinct time series explodes to one per unique ID ever seen, often into the millions, which can overwhelm a metrics backend's memory and query performance, sometimes catastrophically (a "cardinality explosion").

Keep metric labels restricted to values from small, bounded sets — service name, HTTP method, status code class (`2xx`/`4xx`/`5xx` rather than the exact numeric code, if code values might be tracked per unique error type), environment, region. Never attach a label whose possible values are effectively unbounded or grow with user/entity count (user ID, order ID, session ID, raw error messages) — that specific, per-entity detail belongs in logs or traces, which are built to handle high-cardinality data, not in metrics, which are not.

## 3. Core concept

A metric's total cardinality is the product of each of its labels' distinct value counts. Adding a bounded label (say, 5 possible values) multiplies cardinality by 5; adding an unbounded label (millions of possible values, growing over time) multiplies cardinality by that ever-growing number, which is precisely what makes it dangerous — the cost doesn't just increase, it becomes essentially unbounded and keeps growing as long as the label keeps seeing new values.

```java
// LOW cardinality: bounded labels -- safe.
counter.labels("order-service", "GET", "200").increment();

// HIGH cardinality: an UNBOUNDED label -- one new time series PER unique user, forever.
counter.labels("order-service", "GET", "200", userId).increment(); // DANGEROUS
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A metric with bounded labels service (10 values) and status (5 values) has 50 time series; adding an unbounded userId label (millions of values) multiplies cardinality into the millions">
  <rect x="20" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#3fb950"/>
  <text x="160" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">service (10) x status (5)</text>
  <text x="160" y="60" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">= 50 time series -- CHEAP</text>

  <rect x="340" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="480" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">... x userId (millions)</text>
  <text x="480" y="60" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">= MILLIONS of time series -- EXPLOSION</text>

  <text x="320" y="140" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">One unbounded label turns a cheap metric into an unmanageable one.</text>
</svg>

Cardinality multiplies across labels; one unbounded label is enough to explode an otherwise cheap metric.

## 5. Runnable example

Scenario: a request-counting metric, first shown safely bounded, then broken by adding a high-cardinality `userId` label (simulated storage blowing up), and finally fixed by moving the per-user detail to logs (where high cardinality is fine) while keeping the metric itself bounded.

### Level 1 — Basic

```java
// File: BoundedCardinalityMetric.java -- labels are all from small,
// FIXED sets; the number of distinct time series stays small and stable.
import java.util.*;

public class BoundedCardinalityMetric {
    static Map<String, Integer> timeSeries = new HashMap<>(); // key = label combination, simulating a metrics backend

    static void recordRequest(String service, String method, String statusClass) {
        String key = service + "|" + method + "|" + statusClass;
        timeSeries.merge(key, 1, Integer::sum);
    }

    public static void main(String[] args) {
        String[] services = {"order-service", "payment-service"};
        String[] methods = {"GET", "POST"};
        String[] statusClasses = {"2xx", "4xx", "5xx"};

        for (int i = 0; i < 1000; i++) { // 1000 REQUESTS, but bounded labels
            recordRequest(services[i % 2], methods[i % 2], statusClasses[i % 3]);
        }

        System.out.println("1000 requests recorded, but only " + timeSeries.size()
                + " distinct time series -- bounded labels keep cardinality LOW regardless of traffic volume.");
    }
}
```

How to run: `java BoundedCardinalityMetric.java`

Even with 1000 requests recorded, `timeSeries` never exceeds `2 × 2 × 3 = 12` distinct keys, because every label (`service`, `method`, `statusClass`) is drawn from a small, fixed set of possible values — traffic volume has no bearing on cardinality here, only the number of distinct label *combinations* does.

### Level 2 — Intermediate

```java
// File: UnboundedCardinalityExplosion.java -- adds a userId label; the
// number of distinct time series now grows with the number of DISTINCT
// USERS, not staying bounded, even with the SAME request volume.
import java.util.*;

public class UnboundedCardinalityExplosion {
    static Map<String, Integer> timeSeries = new HashMap<>();

    static void recordRequest(String service, String method, String statusClass, String userId) {
        String key = service + "|" + method + "|" + statusClass + "|" + userId; // userId: UNBOUNDED values
        timeSeries.merge(key, 1, Integer::sum);
    }

    public static void main(String[] args) {
        String[] services = {"order-service", "payment-service"};
        String[] methods = {"GET", "POST"};
        String[] statusClasses = {"2xx", "4xx", "5xx"};

        for (int i = 0; i < 1000; i++) {
            String userId = "user-" + i; // EVERY request has a DIFFERENT user in this simulation -- worst case, but realistic at scale
            recordRequest(services[i % 2], methods[i % 2], statusClasses[i % 3], userId);
        }

        System.out.println("1000 requests recorded, and now " + timeSeries.size()
                + " distinct time series -- ONE per unique user, cardinality EXPLODED to match request volume!");
    }
}
```

How to run: `java UnboundedCardinalityExplosion.java`

With `userId` added as a label, `timeSeries.size()` grows to (in this worst-case simulation) the full `1000` — one distinct time series per request, since every request happened to come from a different user. In a real system with millions of users, this same pattern means the metric's cardinality scales with the *total number of users who have ever made a request*, an ever-growing number that has nothing to do with how "interesting" or manageable the underlying data actually is.

### Level 3 — Advanced

```java
// File: MoveHighCardinalityToLogs.java -- keeps the METRIC bounded (as in
// Level 1), and moves the per-user DETAIL to a separate, high-cardinality-
// friendly LOG instead -- getting BOTH aggregate visibility (cheap) AND
// per-user detail (available, but in the right tool).
import java.util.*;

public class MoveHighCardinalityToLogs {
    static Map<String, Integer> timeSeries = new HashMap<>(); // bounded metric -- cheap, aggregate
    static List<String> requestLogs = new ArrayList<>();       // unbounded detail -- fine for LOGS, not metrics

    static void recordRequest(String service, String method, String statusClass, String userId, String correlationId) {
        String metricKey = service + "|" + method + "|" + statusClass; // NO userId here -- stays bounded
        timeSeries.merge(metricKey, 1, Integer::sum);

        requestLogs.add("[" + correlationId + "] " + service + " " + method + " " + statusClass + " user=" + userId); // per-user DETAIL lives HERE
    }

    public static void main(String[] args) {
        String[] services = {"order-service", "payment-service"};
        String[] methods = {"GET", "POST"};
        String[] statusClasses = {"2xx", "4xx", "5xx"};

        for (int i = 0; i < 1000; i++) {
            recordRequest(services[i % 2], methods[i % 2], statusClasses[i % 3], "user-" + i, "corr-" + i);
        }

        System.out.println("Metric time series: " + timeSeries.size() + " -- STILL bounded, cheap, unaffected by 1000 unique users.");
        System.out.println("Request logs: " + requestLogs.size() + " entries -- per-user DETAIL fully preserved, just in the right place.");
        System.out.println("Need to investigate a SPECIFIC user? Search the LOGS by userId or correlationId -- metrics stay healthy either way.");
    }
}
```

How to run: `java MoveHighCardinalityToLogs.java`

`recordRequest` now updates `timeSeries` using only the bounded `metricKey` (no `userId`), keeping the metric's cardinality exactly as low as Level 1's, regardless of how many unique users make requests. The per-user detail — `userId`, `correlationId` — is instead appended to `requestLogs`, a structure built to handle exactly this kind of high-cardinality, per-event detail. The final printout shows both: a small, stable number of metric time series, and a full, unbounded log of every individual request, each still searchable by user or correlation ID when needed — the best of both worlds, each concern handled by the tool suited to it.

## 6. Walkthrough

Trace `MoveHighCardinalityToLogs.main` in order. **First**, the loop runs 1000 times, each iteration calling `recordRequest` with a cycling `service`, `method`, `statusClass`, and a unique `userId` and `correlationId` per iteration (`"user-0"` through `"user-999"`, `"corr-0"` through `"corr-999"`).

**Inside each `recordRequest` call**, `metricKey` is built from only `service`, `method`, and `statusClass` — never `userId` — so `timeSeries.merge(metricKey, 1, Integer::sum)` only ever touches one of the (at most) `2 × 2 × 3 = 12` possible bounded keys, incrementing whichever one matches this iteration's combination.

**In the same call**, a separate log line is appended to `requestLogs`, including the full per-request detail: `correlationId`, `service`, `method`, `statusClass`, and `userId` — this list grows by exactly one entry per call, all 1000 of them, with no attempt to bound or aggregate it, since logs are the appropriate place for this level of detail.

**Finally**, after the loop completes, `main` prints `timeSeries.size()`, which is at most `12` regardless of how many distinct users were involved, and `requestLogs.size()`, which is exactly `1000` — one full log entry per request. The closing message points out that investigating a specific user's behavior means searching the logs (by `userId` or `correlationId`), not adding that dimension to the metric, which would have reintroduced the exact cardinality explosion Level 2 demonstrated.

```
1000 requests, cycling through 2 services x 2 methods x 3 statusClasses, each with a UNIQUE userId
timeSeries (bounded: service+method+statusClass only) -> at most 12 distinct keys, regardless of user count
requestLogs (unbounded: includes userId, correlationId) -> exactly 1000 entries, full per-request detail preserved
```

## 7. Gotchas & takeaways

> A cardinality explosion often isn't noticed until it's already caused a production incident — a metrics backend running out of memory, or queries against a dashboard suddenly timing out — because the cost grows gradually as more distinct label values accumulate over time, rather than failing immediately when the offending label is first added.

- A metric's cardinality is the product of its labels' distinct value counts; one unbounded label (user ID, order ID, raw error text) is enough to explode an otherwise cheap metric.
- Keep metric labels restricted to small, bounded sets of values (service name, method, status class, environment); never attach per-entity identifiers as metric labels.
- High-cardinality, per-entity detail belongs in logs or traces, which are built to handle it, correlated back to metrics via shared context like a [correlation ID](0351-correlation-ids-request-ids.md), not smuggled into a metric's own labels.
- This concern shapes how you implement the [RED method](0356-red-method-rate-errors-duration.md), [USE method](0357-use-method-utilization-saturation-errors.md), and [four golden signals](0358-four-golden-signals-latency-traffic-errors-saturation.md) metrics discussed next — each of those relies on metrics whose labels must stay deliberately bounded to remain affordable at scale.
