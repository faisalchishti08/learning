---
card: system-design
gi: 127
slug: batching-request-coalescing
title: Batching & request coalescing
---

## 1. What it is

**Batching** groups multiple individual operations into one combined operation, processed together — for example, writing 100 database rows in a single `INSERT` statement instead of 100 separate ones. **Request coalescing** is a related idea: when multiple callers ask for the exact same thing at nearly the same time, combine them into a single underlying request, and give all the callers the one result, instead of making the same expensive call multiple times redundantly.

## 2. Why & when

Each individual operation — a network round trip, a database statement, a disk write — carries fixed overhead on top of its actual work. Doing 100 of them separately pays that fixed overhead 100 times; batching them pays it once. Use batching whenever you have many small, similar operations that could be combined, and the added latency of waiting briefly to form a batch is acceptable (see [throughput vs latency](0125-throughput-vs-latency.md) for that trade-off). Use request coalescing specifically when multiple concurrent callers might ask for the identical piece of data or trigger the identical expensive computation at nearly the same time — a classic case is many requests hitting a cold cache for the same key simultaneously.

## 3. Core concept

- **Batching by size or time:** collect requests until either a maximum batch size is reached, or a maximum wait time elapses (whichever comes first), then process the whole batch together.
- **Amortized overhead:** the fixed cost of a round trip or transaction is paid once per batch instead of once per item, so the *per-item* cost drops as the batch grows.
- **Request coalescing (the "thundering herd" fix):** if 50 concurrent requests all ask for the same uncached value, coalescing ensures only the *first* one triggers the actual expensive work; the other 49 wait for that one result and all receive it, rather than 50 independent computations of the same answer.
- **In-flight request tracking:** coalescing needs a way to recognize "a request for this exact key is already in progress" — typically a map from key to a pending result (a `Future` or `CompletableFuture`) that later callers can simply attach to.
- **Batching APIs:** many systems provide native batch operations (a `BatchGetItem` in DynamoDB, a JDBC batch `executeBatch()`) specifically because batching is common enough to deserve first-class support.

## 4. Diagram

```
BATCHING:                              REQUEST COALESCING:

  write(row1)  \                        50 concurrent requests for key "user-42"
  write(row2)   \                              |  |  |  ... (50 of them)
  write(row3)    +-- collected into ONE          v  v  v
  ...           /    batch write               all attach to the SAME
  write(row100)/     (1 round trip,             in-flight request
               instead of 100)                          |
                                                          v
                                                  ONE actual fetch of "user-42"
                                                          |
                                              +-----------+-----------+
                                              v                       v
                                       all 50 callers          result cached for
                                       receive the SAME         any FUTURE request
                                       single result
```
*Caption: batching combines many operations into one round trip; coalescing combines many concurrent identical requests into one underlying computation.*

## 5. Runnable example

**Level 1 — Basic.** Batch several writes into one combined operation instead of many separate ones.

**Level 2 — Request coalescing.** Multiple concurrent callers for the same key trigger only one actual fetch.

**Level 3 — Time-or-size batch trigger.** A batch flushes either when full or after a maximum wait, whichever comes first.

```java
// BatchingCoalescing.java
import java.util.*;
import java.util.concurrent.*;

public class BatchingCoalescing {

    static int simulatedRoundTripCostMs = 20; // fixed overhead per round trip, paid once per batch or call

    public static void main(String[] args) throws Exception {
        // Level 1: batching - combine 100 writes into batches of 10, instead of 100 individual round trips.
        int numWrites = 100, batchSize = 10;
        int individualRoundTrips = numWrites; // one round trip per write, unbatched
        int batchedRoundTrips = (int) Math.ceil((double) numWrites / batchSize);
        System.out.println("unbatched: " + individualRoundTrips + " round trips x " + simulatedRoundTripCostMs
            + "ms = " + (individualRoundTrips * simulatedRoundTripCostMs) + "ms total overhead");
        System.out.println("batched (size=" + batchSize + "): " + batchedRoundTrips + " round trips x " + simulatedRoundTripCostMs
            + "ms = " + (batchedRoundTrips * simulatedRoundTripCostMs) + "ms total overhead");

        // Level 2: request coalescing - many concurrent callers for the same key share ONE underlying fetch.
        Map<String, CompletableFuture<String>> inFlight = new ConcurrentHashMap<>();
        int[] actualFetchCount = {0};

        java.util.function.Function<String, CompletableFuture<String>> fetchCoalesced = key ->
            inFlight.computeIfAbsent(key, k -> CompletableFuture.supplyAsync(() -> {
                actualFetchCount[0]++;
                return "value-for-" + k; // the real, expensive fetch happens only here
            }));

        ExecutorService pool = Executors.newFixedThreadPool(10);
        List<Future<String>> results = new ArrayList<>();
        for (int i = 0; i < 50; i++) {
            results.add(pool.submit(() -> fetchCoalesced.apply("user-42").get()));
        }
        for (Future<String> f : results) f.get(); // wait for all 50 callers
        pool.shutdown();

        System.out.println("50 concurrent requests for the same key -> actual fetches performed: " + actualFetchCount[0]);

        // Level 3: batch flushes on whichever comes first - size limit, or a max wait time.
        List<String> pendingBatch = new ArrayList<>();
        int maxBatchSize = 5;
        long batchStartTime = System.currentTimeMillis();
        long maxWaitMs = 50;

        String[] incoming = {"item1", "item2", "item3"}; // fewer than maxBatchSize arrive
        for (String item : incoming) pendingBatch.add(item);

        boolean sizeTriggered = pendingBatch.size() >= maxBatchSize;
        boolean timeTriggered = (System.currentTimeMillis() - batchStartTime) >= maxWaitMs;
        System.out.println("batch has " + pendingBatch.size() + " items after a short wait; size trigger=" + sizeTriggered + ", time trigger=" + timeTriggered);
        System.out.println("-> in a real system, this batch would flush once maxWaitMs elapses, even though it never filled up");
    }
}
```

**How to run:** save as `BatchingCoalescing.java`, then run `java BatchingCoalescing.java`.

## 6. Walkthrough

1. Level 1 compares `individualRoundTrips` (100, one per write) against `batchedRoundTrips` (10, one per group of 10 writes); multiplying each by the fixed `simulatedRoundTripCostMs` shows the batched total overhead is a tenth of the unbatched total — the direct payoff of amortizing fixed per-round-trip cost across more items.
2. Level 2's `fetchCoalesced` uses `inFlight.computeIfAbsent`, which atomically checks whether a `CompletableFuture` for a key already exists; if not, it creates one that runs the actual fetch and increments `actualFetchCount`. If a future for that key already exists, `computeIfAbsent` returns the *existing* future instead of creating a new one.
3. Fifty threads all call `fetchCoalesced.apply("user-42")` concurrently; because they all share the same key, only the very first one to reach `computeIfAbsent` triggers the real fetch — every other caller receives the same, already-in-flight `CompletableFuture`.
4. The final printed `actualFetchCount[0]` is `1`, not `50` — confirming that all 50 concurrent callers were coalesced into a single underlying fetch, and all 50 received that one result once it completed.
5. Level 3 models a batch that only received 3 of its `maxBatchSize = 5` items before a check runs; `sizeTriggered` is `false` since the batch is not full, and in a real implementation, `timeTriggered` becoming `true` after `maxWaitMs` elapses would be what forces the batch to flush anyway, ensuring items are never held indefinitely just because a batch never fully fills.

## 7. Gotchas & takeaways

> Gotcha: request coalescing only works correctly for read-like operations where identical requests should genuinely produce an identical, shareable result. Coalescing writes (e.g. two different "increment this counter" requests) would silently drop one of the operations, since only the first one actually runs — never coalesce requests whose individual side effects need to happen independently.

- Batching amortizes the fixed overhead of a round trip or transaction across many items, raising throughput at some cost to individual item latency.
- Request coalescing collapses multiple concurrent identical requests into one underlying operation, directly preventing redundant, duplicated work (a "thundering herd").
- A batch should flush on whichever comes first — reaching its size limit or a maximum wait time — so items are never held indefinitely.
- Related concepts: [Throughput vs latency](0125-throughput-vs-latency.md) (the trade-off batching makes explicit), [Connection reuse & pooling](0128-connection-reuse-pooling.md) (another technique for amortizing fixed per-operation overhead).
