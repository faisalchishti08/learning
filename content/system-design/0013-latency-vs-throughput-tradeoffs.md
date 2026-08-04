---
card: system-design
gi: 13
slug: latency-vs-throughput-tradeoffs
title: Latency vs throughput tradeoffs
---

## 1. What it is

**Latency** is how long a single request takes, from start to finish. **Throughput** is how many requests a system can process per unit of time, such as requests per second. They sound related, but improving one can make the other worse. A system with excellent throughput can still have terrible latency for any one user, and a system tuned for the fastest possible single request can process fewer requests overall.

Think of a highway: throughput is how many cars pass a point per hour; latency is how long one specific car takes to drive the whole route. Adding more lanes raises throughput, but a single car's trip time barely changes. Batching cars into a slow-moving convoy could raise throughput further, while making each individual car's trip slower.

## 2. Why & when

You reason about this tradeoff whenever a design decision speeds up the system in aggregate but slows down individual requests, or vice versa. It comes up constantly with batching (grouping many small requests into one bigger operation) and with buffering or queueing (holding requests briefly to process them more efficiently). Naming this tradeoff explicitly shows the interviewer you understand that "faster" is not one single dimension.

## 3. Core concept

**Why the two can conflict:** batching is the clearest example. Suppose a database write takes 5 ms of fixed overhead per write, no matter the batch size. Writing 100 records one at a time costs `100 × 5 ms = 500 ms` of overhead total, but each individual record's write latency is low (5 ms). Batching all 100 records into one write cuts total overhead to just 5 ms — hugely better throughput — but now the first record in the batch has to wait for all 99 others to arrive before it is written, and its own **latency** grows if the system waits to fill a batch.

**The general pattern:**
- **Increasing throughput** often means processing things in bigger groups, or overlapping more work at once (more parallel workers). This amortizes fixed costs but can add waiting time for any single item.
- **Reducing latency** often means processing each request as soon as it arrives, immediately, without waiting to batch it with others — which can waste capacity that batching would have used more efficiently.

**When to prioritize which:** prioritize low latency for interactive, user-facing requests (a user waiting for a page to load). Prioritize high throughput for background, bulk work where no single item's timing matters (a nightly analytics job processing billions of log lines). Many real systems use both: an interactive path optimized for latency, and a background path optimized for throughput.

## 4. Diagram

```
 ONE AT A TIME (low latency, lower throughput)
 [req]->done  [req]->done  [req]->done     each request finishes fast,
                                             but fixed overhead paid every time

 BATCHED (higher throughput, higher latency per item)
 [req][req][req][req] --wait to fill batch--> [ALL WRITTEN AT ONCE]
                                                fixed overhead paid ONCE,
                                                but first item waited longest
```
*Caption: batching raises throughput by amortizing overhead, but makes individual requests wait longer — the core latency/throughput tension.*

## 5. Runnable example

### Artifact: a Java simulation comparing per-request vs batched write latency and throughput

```java
public class LatencyThroughputTradeoff {

    static final int FIXED_OVERHEAD_MS = 5;
    static final int RECORD_COUNT = 100;

    public static void main(String[] args) {
        // One at a time: overhead paid on every single write.
        int totalTimeOneAtATime = RECORD_COUNT * FIXED_OVERHEAD_MS;
        int latencyPerRecordOneAtATime = FIXED_OVERHEAD_MS;

        // Batched: overhead paid once for the whole batch.
        int totalTimeBatched = FIXED_OVERHEAD_MS;
        // The first record in the batch waits for the whole batch to be written.
        int worstCaseLatencyBatched = FIXED_OVERHEAD_MS;

        double throughputOneAtATime = RECORD_COUNT / (totalTimeOneAtATime / 1000.0);
        double throughputBatched = RECORD_COUNT / (totalTimeBatched / 1000.0);

        System.out.println("One at a time:");
        System.out.println("  Total time: " + totalTimeOneAtATime + " ms");
        System.out.println("  Latency per record: " + latencyPerRecordOneAtATime + " ms");
        System.out.printf("  Throughput: %.0f records/sec%n", throughputOneAtATime);

        System.out.println("Batched (all 100 in one write):");
        System.out.println("  Total time: " + totalTimeBatched + " ms");
        System.out.println("  Worst-case latency (first record queued): " + worstCaseLatencyBatched + " ms");
        System.out.printf("  Throughput: %.0f records/sec%n", throughputBatched);
    }
}
```

**How to run:** save as `LatencyThroughputTradeoff.java`, run `java LatencyThroughputTradeoff.java` (JDK 17+).

## 6. Walkthrough

1. `FIXED_OVERHEAD_MS` models a constant cost paid by every database write operation, regardless of how many records it contains.
2. The "one at a time" branch multiplies that fixed overhead by the number of records, since it is paid on every single write; each record's own latency stays low, at just the fixed overhead.
3. The "batched" branch pays the fixed overhead only once for the entire group of 100 records, since they are all written together.
4. Both branches compute throughput as records processed divided by total time taken.
5. Output:
```
One at a time:
  Total time: 500 ms
  Latency per record: 5 ms
  Throughput: 200 records/sec
Batched (all 100 in one write):
  Total time: 5 ms
  Worst-case latency (first record queued): 5 ms
  Throughput: 20000 records/sec
```
6. This numeric gap (200 vs 20,000 records/sec) is the throughput win from batching. The tradeoff hides in a detail the code above simplifies: in a real system, records for a batch usually arrive over time and the system must *wait* to accumulate a full batch before writing, which adds real waiting time to a single record's latency — a cost this simulation does not model, but a real design must account for.

## 7. Gotchas & takeaways

> **Gotcha:** assuming a change that improves one number (like throughput) automatically improves the system overall. It can silently make individual request latency worse — measure both, and know which one your users actually feel.

- Latency is what one user experiences; throughput is what the system handles in aggregate. They are different axes, not the same thing measured two ways.
- Batching and buffering usually trade latency for throughput; state this tradeoff explicitly when you propose them.
- Match your optimization target to the use case: low latency for interactive, user-facing paths; high throughput for background, bulk work.
