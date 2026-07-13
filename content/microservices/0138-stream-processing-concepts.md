---
card: microservices
gi: 138
slug: stream-processing-concepts
title: "Stream processing concepts"
---

## 1. What it is

Stream processing is continuously computing over an unbounded, ongoing sequence of events as they arrive, rather than waiting for a complete, fixed dataset before running a computation. Where a traditional batch job reads a finished file and produces one final answer, a stream processor reads events one (or a small batch) at a time, forever, updating its output incrementally as new events keep arriving.

## 2. Why & when

Batch processing has an inherent latency floor: results are only as fresh as the last batch run, which might be hourly, nightly, or triggered manually — fine for a monthly sales report, unacceptable for fraud detection that needs to flag a suspicious transaction within seconds, not after tonight's batch job runs. Stream processing removes that floor by treating "new data arrived" as the trigger for computation itself, producing continuously updated results with latency measured in milliseconds to seconds rather than the batch interval.

Reach for stream processing when a computation's usefulness depends on low latency — real-time dashboards, fraud detection, live inventory counts, anomaly alerting — or when the "dataset" is genuinely unbounded and never has a natural "finished" point, like a continuous log of user activity. Batch processing remains simpler and often cheaper for analysis where near-real-time results add no real value over next-morning results.

## 3. Core concept

A stream processing job defines a computation once — a filter, a transformation, an aggregation — and the processing engine applies it continuously to every new event as it arrives, maintaining any necessary running state (like a running total) between events rather than recomputing from scratch each time.

```java
// batch: read EVERYTHING, then compute ONE final answer
double totalSales = readEntireFile("sales.csv").stream().mapToDouble(Sale::amount).sum();

// stream: compute CONTINUOUSLY as each new event arrives, maintaining running state
double[] runningTotal = {0};
eventStream.forEach(sale -> {
    runningTotal[0] += sale.amount();
    publishUpdatedTotal(runningTotal[0]); // a FRESH answer after every single new event
});
```

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Batch processing waits for a complete, bounded dataset before producing one final result; stream processing computes continuously as each new unbounded event arrives, producing incrementally updated results the whole time">
  <text x="150" y="25" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Batch</text>
  <rect x="30" y="45" width="240" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="67" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">complete, bounded dataset</text>
  <rect x="120" y="100" width="60" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="120" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">1 result</text>
  <line x1="150" y1="80" x2="150" y2="98" stroke="#8b949e" marker-end="url(#arr21)"/>

  <text x="480" y="25" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Stream</text>
  <rect x="360" y="45" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="390" y="65" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">e1</text>
  <rect x="430" y="45" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="460" y="65" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">e2</text>
  <rect x="500" y="45" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="530" y="65" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">e3...</text>
  <rect x="360" y="100" width="60" height="28" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="390" y="119" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">r1</text>
  <rect x="430" y="100" width="60" height="28" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="460" y="119" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">r2</text>
  <rect x="500" y="100" width="60" height="28" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="530" y="119" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">r3...</text>
  <line x1="390" y1="75" x2="390" y2="98" stroke="#8b949e" marker-end="url(#arr21)"/>
  <line x1="460" y1="75" x2="460" y2="98" stroke="#8b949e" marker-end="url(#arr21)"/>
  <line x1="530" y1="75" x2="530" y2="98" stroke="#8b949e" marker-end="url(#arr21)"/>

  <defs>
    <marker id="arr21" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Batch produces one answer from a closed dataset; streaming produces a fresh, incremental answer after every new event.

## 5. Runnable example

Scenario: a sales-total computation that starts as a batch job (highlighting its inherent latency), becomes a streaming computation maintaining running state incrementally, and finally adds a real-time alert derived from the running stream state, demonstrating a capability batch processing structurally cannot offer.

### Level 1 — Basic

```java
// File: BatchTotal.java -- a traditional batch job: wait for everything, then compute one answer.
import java.util.*;

public class BatchTotal {
    record Sale(String product, double amount) {}

    public static void main(String[] args) {
        // simulates: a "file" that only becomes available once ALL of today's sales are in
        List<Sale> completeDataset = List.of(
            new Sale("widget", 25.00), new Sale("gadget", 40.00), new Sale("widget", 15.00));

        System.out.println("Waiting for the COMPLETE dataset before computing anything...");
        double total = completeDataset.stream().mapToDouble(Sale::amount).sum();
        System.out.println("Batch result (available only AFTER all data arrived): total = " + total);
    }
}
```

**How to run:** `javac BatchTotal.java && java BatchTotal` (JDK 17+).

The total is only known once every sale in the dataset has already happened and been collected — there is no partial answer available while sales are still coming in.

### Level 2 — Intermediate

```java
// File: StreamingTotal.java -- computes a FRESH total after every single new sale, continuously.
import java.util.*;
import java.util.function.*;

public class StreamingTotal {
    record Sale(String product, double amount) {}

    static class StreamProcessor {
        double runningTotal = 0; // state MAINTAINED across events, not recomputed from scratch
        List<Consumer<Double>> onUpdate = new ArrayList<>();

        void onEvent(Sale sale) {
            runningTotal += sale.amount(); // INCREMENTAL update
            onUpdate.forEach(handler -> handler.accept(runningTotal));
        }
    }

    public static void main(String[] args) {
        StreamProcessor processor = new StreamProcessor();
        processor.onUpdate.add(total -> System.out.println("  updated running total: " + total));

        // sales arrive ONE AT A TIME, over "time" -- each produces an immediate, fresh result
        processor.onEvent(new Sale("widget", 25.00));
        processor.onEvent(new Sale("gadget", 40.00));
        processor.onEvent(new Sale("widget", 15.00));

        System.out.println("Final running total: " + processor.runningTotal + " (was ALSO available, correctly, after EACH individual sale)");
    }
}
```

**How to run:** `javac StreamingTotal.java && java StreamingTotal` (JDK 17+).

Expected output:
```
  updated running total: 25.0
  updated running total: 65.0
  updated running total: 80.0
Final running total: 80.0 (was ALSO available, correctly, after EACH individual sale)
```

Unlike Level 1, a correct, up-to-date total exists after every individual sale — not just once all three sales have happened.

### Level 3 — Advanced

```java
// File: RealTimeAlerting.java -- derives a real-time alert from streaming state,
// something batch processing structurally cannot offer (an alert only after a full batch is pointless).
import java.util.*;
import java.util.function.*;

public class RealTimeAlerting {
    record Sale(String product, double amount, long timestampMillis) {}

    static class FraudDetectionProcessor {
        // running state: total spent per product in the last "window" (simplified, no real windowing here)
        Map<String, Double> spendByProduct = new HashMap<>();
        double alertThreshold;
        FraudDetectionProcessor(double alertThreshold) { this.alertThreshold = alertThreshold; }

        void onEvent(Sale sale) {
            double newTotal = spendByProduct.merge(sale.product(), sale.amount(), Double::sum); // incremental update
            System.out.println("[t=" + sale.timestampMillis() + "] " + sale.product() + " running total: " + newTotal);
            if (newTotal > alertThreshold) {
                System.out.println("  *** ALERT: " + sale.product() + " spend (" + newTotal + ") exceeded threshold (" + alertThreshold + ") -- fired IMMEDIATELY, not after a batch window ***");
            }
        }
    }

    public static void main(String[] args) {
        FraudDetectionProcessor processor = new FraudDetectionProcessor(100.0);

        processor.onEvent(new Sale("gift-card", 40.00, 0));
        processor.onEvent(new Sale("gift-card", 35.00, 500));
        processor.onEvent(new Sale("gift-card", 30.00, 900)); // this one crosses the threshold

        System.out.println("Total elapsed: 900ms. A daily batch job would not have surfaced this for HOURS.");
    }
}
```

**How to run:** `javac RealTimeAlerting.java && java RealTimeAlerting` (JDK 17+).

Expected output:
```
[t=0] gift-card running total: 40.0
[t=500] gift-card running total: 75.0
[t=900] gift-card running total: 105.0
  *** ALERT: gift-card spend (105.0) exceeded threshold (100.0) -- fired IMMEDIATELY, not after a batch window ***
Total elapsed: 900ms. A daily batch job would not have surfaced this for HOURS.
```

## 6. Walkthrough

1. **Level 1** — `completeDataset.stream().mapToDouble(Sale::amount).sum()` runs exactly once, and only after `completeDataset` (standing in for a finished, closed input) is fully assembled; nothing about this design supports asking "what's the total so far" partway through.
2. **Level 2, state carried between events** — `StreamProcessor.runningTotal` is a field on the processor object, not a local variable recomputed inside a single method call; `onEvent` reads and updates it incrementally on every single invocation.
3. **Level 2, three separate, complete answers** — each of the three calls to `processor.onEvent` in `main` triggers `onUpdate`'s handler with a fully valid, correct running total *at that moment*, not just once at the very end — there are three complete answers here where Level 1 produced exactly one.
4. **Level 3, deriving a business decision from streaming state** — `FraudDetectionProcessor.spendByProduct` accumulates a running total *per product*, using `merge` to add each new sale's amount to that product's existing total; this is the same incremental-state pattern as Level 2, applied per-key instead of globally.
5. **Level 3, the alert check runs on every event** — immediately after updating `newTotal`, `onEvent` checks whether it has crossed `alertThreshold` and, if so, prints an alert *at that moment* — this check runs after every single sale, not on some later schedule.
6. **Level 3, tracing the three events** — the first two `gift-card` sales bring the running total to 40.0 then 75.0, neither crossing the 100.0 threshold; the third sale brings it to 105.0, crossing the threshold, and the alert fires immediately as part of processing that specific event, at simulated timestamp 900ms.
7. **Level 3, why this is structurally a streaming-only capability** — a batch job computing the same total would only produce *a* result once its batch window closes (an hour, a day); it has no notion of "check after every single new sale" because it never sees sales individually, only the whole accumulated batch — the alert firing at t=900ms, mid-stream, based on the exact event that crossed the threshold, is the concrete capability streaming provides that batch processing cannot replicate without effectively becoming a stream processor itself.

## 7. Gotchas & takeaways

> **Gotcha:** stream processing's low latency comes with real complexity costs — handling out-of-order or late-arriving events, deciding how to bound otherwise-unbounded aggregations (see [windowing & aggregation](0143-windowing-aggregation.md)), and managing potentially large amounts of running state; don't reach for stream processing purely because it sounds more sophisticated than batch when a nightly batch job would answer the actual business question just as well.

- Stream processing computes continuously over an unbounded sequence of events, producing incrementally updated results, in contrast to batch processing's single result from a complete, bounded dataset.
- The core mechanism is maintaining running state (a running total, a per-key aggregate) between events, updated incrementally rather than recomputed from scratch.
- Low-latency use cases — fraud detection, live dashboards, real-time alerting — are where streaming's value is concrete and measurable; it enables decisions and alerts that a batch job's inherent latency floor cannot support.
- Batch processing remains simpler, often cheaper, and entirely adequate for analysis where near-real-time freshness adds no real business value.
- Streaming introduces real complexity around out-of-order events and bounding otherwise-infinite aggregations, which is not free and should be weighed against the actual latency requirement.
