---
card: system-design
gi: 129
slug: profiling-finding-bottlenecks
title: Profiling & finding bottlenecks
---

## 1. What it is

**Profiling** is measuring where a program actually spends its time and resources, rather than guessing. A **bottleneck** is the specific part of a system that limits its overall speed or throughput — improving anything else does nothing for overall performance until the bottleneck itself is addressed, since the whole system can only go as fast as its slowest constrained part.

## 2. Why & when

Performance intuition is frequently wrong: the part of the code that "feels slow" to read is often not where the actual time goes, while an innocuous-looking line (an unindexed database query run in a loop) can dominate total runtime. Profiling replaces guessing with measurement, showing exactly where time and resources are spent. Profile before optimizing anything — optimizing a part of the system that is not the bottleneck wastes effort and can even make the code more complex for zero performance gain.

## 3. Core concept

- **CPU profiling:** measures which functions consume the most CPU time, either by sampling the call stack periodically or by instrumenting every function call; identifies computationally expensive code.
- **Memory profiling:** measures allocation patterns and object retention, useful for finding memory leaks or excessive garbage-collection pressure from creating too many short-lived objects.
- **Database query profiling:** measures which queries are slow, or run far more often than expected (a classic case: an "N+1 query" problem, where a loop unintentionally issues one query per iteration instead of one query total).
- **Distributed tracing:** for a request spanning multiple services, traces show how much time was spent in each service and each network hop, revealing which specific service or call is the actual bottleneck in a multi-service request.
- **The bottleneck principle (Theory of Constraints):** a system's overall throughput is capped by its single most constrained resource; speeding up any non-bottleneck part has no effect on overall throughput until the bottleneck itself moves.
- **Measure again after fixing:** once you address one bottleneck, a *different* part of the system becomes the new bottleneck — profiling is an iterative process, not a one-time task.

## 4. Diagram

```
Request timeline, broken down by where time is actually spent:

  [ Parse request: 1ms ]
  [ Business logic: 3ms ]
  [ Database query (in a loop, N+1 problem): 180ms ]  <- THE BOTTLENECK
  [ Serialize response: 2ms ]

  Total request time: 186ms

  Optimizing "parse request" from 1ms to 0.1ms saves 0.9ms total (0.5%).
  Fixing the N+1 query (180ms -> 15ms) saves 165ms total (89%).

  -> effort should go where the profiler points, not where code "looks slow".
```
*Caption: a profiler reveals which part of the timeline actually dominates total time — usually not the part that looks complex or interesting to optimize.*

## 5. Runnable example

**Level 1 — Basic.** Time each stage of a request manually to find where time actually goes.

**Level 2 — Reveal an N+1 query pattern.** Compare a naive per-item query loop against one batched query.

**Level 3 — Confirm the fix by re-measuring, and check the new bottleneck.**

```java
// ProfilingBottlenecks.java
import java.util.*;

public class ProfilingBottlenecks {

    static Map<Integer, String> simulatedDatabase = new HashMap<>();
    static { for (int i = 1; i <= 20; i++) simulatedDatabase.put(i, "item-" + i); }

    static String queryOne(int id) {
        try { Thread.sleep(2); } catch (InterruptedException ignored) {} // simulated per-query latency
        return simulatedDatabase.get(id);
    }

    static List<String> queryBatch(List<Integer> ids) {
        try { Thread.sleep(5); } catch (InterruptedException ignored) {} // ONE round trip, regardless of batch size
        List<String> results = new ArrayList<>();
        for (int id : ids) results.add(simulatedDatabase.get(id));
        return results;
    }

    public static void main(String[] args) {
        // Level 1: time each stage of handling one "request" to find where time actually goes.
        long t0 = System.nanoTime();
        String parsed = "request-payload"; // parsing: trivial
        long t1 = System.nanoTime();

        List<Integer> idsToFetch = new ArrayList<>();
        for (int i = 1; i <= 20; i++) idsToFetch.add(i);

        List<String> naiveResults = new ArrayList<>();
        for (int id : idsToFetch) naiveResults.add(queryOne(id)); // Level 2: N+1 pattern - one query PER item
        long t2 = System.nanoTime();

        String serialized = naiveResults.toString(); // serializing: trivial
        long t3 = System.nanoTime();

        double parseMs = (t1 - t0) / 1_000_000.0;
        double queryMs = (t2 - t1) / 1_000_000.0;
        double serializeMs = (t3 - t2) / 1_000_000.0;
        System.out.printf("parse: %.1fms, database (N+1 loop): %.1fms, serialize: %.1fms%n", parseMs, queryMs, serializeMs);
        System.out.println("-> the database stage clearly dominates: THIS is the bottleneck, not parsing or serializing");

        // Level 3: fix the N+1 pattern with one batched query, then re-measure to confirm the fix.
        long t4 = System.nanoTime();
        List<String> batchedResults = queryBatch(idsToFetch); // ONE query for all 20 ids
        long t5 = System.nanoTime();
        double batchedQueryMs = (t5 - t4) / 1_000_000.0;

        System.out.printf("after fix - database (batched): %.1fms (was %.1fms)%n", batchedQueryMs, queryMs);
        System.out.println("results match: " + naiveResults.equals(batchedResults));
        System.out.println("-> now re-profile: with the database fixed, check whether parse/serialize (still ~"
            + String.format("%.1f", parseMs + serializeMs) + "ms combined) has become the new relative bottleneck");
    }
}
```

**How to run:** save as `ProfilingBottlenecks.java`, then run `java ProfilingBottlenecks.java`.

## 6. Walkthrough

1. The code records timestamps (`t0` through `t3`) around each logical stage of handling a request: parsing, the database loop, and serialization — this is the manual equivalent of what a profiler automates.
2. `queryOne` is called once per id inside the loop over `idsToFetch`, each call paying a simulated `2ms` round trip; with 20 ids, this alone costs roughly `40ms` — the classic N+1 pattern, where a loop issues one query per item instead of a single query for all of them.
3. The printed per-stage breakdown shows the database stage taking dramatically longer than parsing or serialization, both of which are near-instant by comparison — pointing clearly and specifically at where optimization effort should go.
4. Level 3's `queryBatch` fetches all 20 ids in a single simulated round trip costing `5ms` total, regardless of how many ids are requested — replacing 20 round trips with 1.
5. The final comparison prints the batched query's time (`~5ms`) against the original N+1 loop's time (`~40ms`), and confirms `naiveResults.equals(batchedResults)` is `true` — the fix produced the identical correct result, just far faster — while the closing note explicitly reminds you that after fixing this bottleneck, the next profiling pass should check whether a different stage (parsing, serialization) is now the relatively largest cost.

## 7. Gotchas & takeaways

> Gotcha: profiling a code path under unrealistic test conditions (a tiny dataset, an empty cache that would normally be warm, a single user instead of realistic concurrency) can point at the wrong bottleneck entirely — a query that looks trivially fast against 20 test rows might be the dominant cost against 20 million real rows. Profile against production-like data volume and concurrency whenever possible.

- Profiling measures where a system actually spends time and resources, replacing guesswork with evidence before you optimize anything.
- A bottleneck is the single most constrained part of a system; fixing anything else does not improve overall performance until the bottleneck itself is addressed.
- The N+1 query pattern — one query per loop iteration instead of one batched query — is a common, high-impact bottleneck that profiling reliably reveals.
- Related concepts: [Batching & request coalescing](0127-batching-request-coalescing.md) (the direct fix demonstrated here), [Throughput vs latency](0125-throughput-vs-latency.md) (the metrics profiling is ultimately in service of improving).
