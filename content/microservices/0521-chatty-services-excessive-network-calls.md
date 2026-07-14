---
card: microservices
gi: 521
slug: chatty-services-excessive-network-calls
title: "Chatty services / excessive network calls"
---

## 1. What it is

**Chatty services** is the anti-pattern where satisfying one logical operation requires many separate network round-trips between services (or between a client and a service), instead of a small number of coarser-grained calls. Each individual call might look harmless, but network latency is paid per round-trip, not per byte transferred, so a design that makes fifty small calls to answer one question can be far slower than one call that returns everything needed — even if the fifty calls, added up, transfer less data overall.

## 2. Why & when

You watch for chatty designs because the cost is latency multiplication, and it's easy to introduce accidentally by mirroring an in-process object model onto network calls:

- **A local method call and a network call have wildly different costs.** Calling `getName()` on an in-memory object costs nanoseconds; calling a remote service's `getName()` endpoint costs at minimum a network round-trip — often single-digit milliseconds on a good day, much more under load or across regions. Treating remote calls like local ones, one field at a time, multiplies that cost by however many fields you need.
1. **The classic trigger is an N+1 pattern**: fetching a list of N items with one call, then making one additional call *per item* to fetch its details — for 100 items, that's 101 network round-trips where a well-designed API would need one or two.
- **It often creeps in through natural, incremental development** — an endpoint that fetches an order works fine; later, a "get the customer's name for this order" need gets bolted on as one more call per order in a loop, and nobody notices until the order list page is rendering 200 orders and making 200 extra calls to do it.
- **The fix is almost always batching or restructuring the API**: a bulk endpoint that accepts many IDs and returns many results in one round-trip, a response that embeds related data the caller would otherwise need a separate call for, or a query language (like GraphQL) that lets the caller specify exactly what's needed in one request.

## 3. Core concept

Think of a customer at a hardware store counter asking for one item, walking back to a shelf, discovering they need a second item, walking back to the counter, then realizing they need a third — one trip per item, when a single trip with a written list would have gotten everything in one round-trip to the shelves. The individual walk isn't slow; taking fifty of them back to back is. Bringing a shopping list up front — batching the requests into one trip — is the fix, and it works precisely because the *cost of walking* dominates the *cost of picking up an item*, exactly like network latency dominates the cost of processing a tiny request on a fast server.

Concretely:

1. **Each network round-trip pays a fixed latency cost** (connection overhead, serialization, the physical time for a request to travel and a response to return) regardless of how little data it carries — this cost doesn't shrink just because the payload is small.
2. **N sequential round-trips cost roughly N times that fixed latency**, even if each individual call is fast, because they're paid one after another rather than overlapped or eliminated.
3. **Batching combines many small requests into one (or a few) larger ones**, paying the fixed round-trip cost once (or a handful of times) instead of N times, even though the total bytes transferred may be similar or even slightly larger.
4. **The alternative to batching is parallelizing the round-trips** (firing all N requests concurrently instead of one after another) — this helps when batching isn't possible, but still costs N times the *resources* (connections, threads), just not N times the *wall-clock time*; true batching is usually still the better fix when the API can support it.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Chatty design: one round-trip per item, latency adds up sequentially. Batched design: one round-trip for all items, latency paid once">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Chatty: N round-trips</text>
  <rect x="20" y="35" width="60" height="24" rx="3" fill="#1c2430" stroke="#f0883e"/>
  <text x="50" y="51" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">call 1</text>
  <rect x="90" y="35" width="60" height="24" rx="3" fill="#1c2430" stroke="#f0883e"/>
  <text x="120" y="51" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">call 2</text>
  <rect x="160" y="35" width="60" height="24" rx="3" fill="#1c2430" stroke="#f0883e"/>
  <text x="190" y="51" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">call 3</text>
  <text x="250" y="51" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">... N times</text>
  <text x="150" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">total time = N x round-trip latency</text>

  <text x="500" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Batched: 1 round-trip</text>
  <rect x="420" y="35" width="220" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="530" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">1 call: all N items' data</text>
  <text x="530" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">total time = 1 x round-trip latency</text>
</svg>

Round-trip latency is paid per call; batching pays it once regardless of how many items are involved.

## 5. Runnable example

Scenario: rendering an order list that needs each order's customer name. We start with the chatty N+1 version (one extra call per order), extend it to a parallelized version (still N calls, but concurrent), then handle the proper fix: a batch endpoint that fetches all needed customer names in one round-trip.

### Level 1 — Basic

```java
// File: ChattyNPlusOne.java -- the N+1 ANTI-PATTERN: one network call
// to list orders, then ONE MORE CALL PER ORDER to get its customer name.
import java.util.*;
import java.util.concurrent.*;

public class ChattyNPlusOne {
    static List<String> fetchOrderIds() { return List.of("order-1", "order-2", "order-3", "order-4", "order-5"); }

    // simulates a real network round-trip: fixed latency regardless of how little data comes back
    static String fetchCustomerNameForOrder(String orderId) throws InterruptedException {
        Thread.sleep(50); // 50ms simulated network round-trip
        return "Customer-" + orderId;
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        List<String> orderIds = fetchOrderIds(); // call #1
        for (String orderId : orderIds) {
            String customerName = fetchCustomerNameForOrder(orderId); // one MORE call, per order
            System.out.println(orderId + " -> " + customerName);
        }
        System.out.println("Total time: " + (System.currentTimeMillis() - start) + "ms for " + (1 + orderIds.size()) + " sequential calls");
    }
}
```

How to run: `java ChattyNPlusOne.java`

One call fetches 5 order IDs, then the loop makes 5 *more* sequential calls, one per order, each paying the full 50ms simulated round-trip. Total time is roughly 250ms (5 x 50ms) even though the actual data transferred (5 customer names) is tiny — the cost is entirely dominated by the number of round-trips, not the payload size.

### Level 2 — Intermediate

```java
// File: ChattyParallelized.java -- still N calls, but fired CONCURRENTLY
// instead of sequentially, trading wall-clock time for resource usage.
import java.util.*;
import java.util.concurrent.*;

public class ChattyParallelized {
    static List<String> fetchOrderIds() { return List.of("order-1", "order-2", "order-3", "order-4", "order-5"); }

    static String fetchCustomerNameForOrder(String orderId) throws InterruptedException {
        Thread.sleep(50);
        return "Customer-" + orderId;
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        List<String> orderIds = fetchOrderIds();
        ExecutorService pool = Executors.newFixedThreadPool(orderIds.size()); // one thread per call, fired concurrently
        List<Future<String>> futures = new ArrayList<>();
        for (String orderId : orderIds) {
            futures.add(pool.submit(() -> orderId + " -> " + fetchCustomerNameForOrder(orderId)));
        }
        for (Future<String> f : futures) System.out.println(f.get());
        pool.shutdown();
        System.out.println("Total time: " + (System.currentTimeMillis() - start) + "ms -- faster, but still N separate network connections/calls");
    }
}
```

How to run: `java ChattyParallelized.java`

All 5 calls are submitted to a thread pool at once instead of one after another, so the 50ms round-trips overlap — total wall-clock time drops to roughly 50ms instead of 250ms. This genuinely helps latency, but it's still 5 separate network calls, 5 separate connections, and 5x the load on the downstream service compared to a single batched request — it treats the symptom (wall-clock time) without addressing the actual cause (too many round-trips).

### Level 3 — Advanced

```java
// File: BatchedFix.java -- the PROPER FIX: ONE call that accepts ALL
// the order IDs and returns ALL the customer names in a single round-trip.
import java.util.*;

public class BatchedFix {
    static List<String> fetchOrderIds() { return List.of("order-1", "order-2", "order-3", "order-4", "order-5"); }

    // ONE network call, taking a batch of IDs, returning a batch of results -- the round-trip cost is paid ONCE
    static Map<String, String> fetchCustomerNamesBatch(List<String> orderIds) throws InterruptedException {
        Thread.sleep(50); // still 50ms, but ONCE for the whole batch, not once per item
        Map<String, String> results = new LinkedHashMap<>();
        for (String orderId : orderIds) results.put(orderId, "Customer-" + orderId);
        return results;
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        List<String> orderIds = fetchOrderIds(); // call #1
        Map<String, String> customerNames = fetchCustomerNamesBatch(orderIds); // call #2 -- the ONLY other call, batched
        for (String orderId : orderIds) {
            System.out.println(orderId + " -> " + customerNames.get(orderId));
        }
        System.out.println("Total time: " + (System.currentTimeMillis() - start) + "ms for just 2 total calls, regardless of order count");
    }
}
```

How to run: `java BatchedFix.java`

`fetchCustomerNamesBatch` takes the entire list of order IDs and returns a map of all their customer names in one call — the simulated 50ms round-trip cost is paid exactly once, not five times. Total time is roughly 100ms (2 calls: list orders, then batch-fetch names) regardless of whether there are 5 orders or 5,000 — the round-trip count no longer scales with the number of items, which is the actual structural fix, not just a faster way of paying the same N round-trips.

## 6. Walkthrough

Trace `BatchedFix.main` end to end, contrasting the round-trip count with Level 1:

1. **`fetchOrderIds()` is called** — this simulates one network round-trip to a list endpoint, e.g. `GET /orders` returning `{"orderIds": ["order-1", ..., "order-5"]}`. This is call #1, identical in both the chatty and batched versions.
2. **`fetchCustomerNamesBatch(orderIds)` is called with the full list of 5 IDs** — conceptually equivalent to `POST /customers/batch` with body `{"orderIds": ["order-1", "order-2", "order-3", "order-4", "order-5"]}`.
3. **The simulated "server" processes the entire batch in one pass** (`Thread.sleep(50)` represents the one round-trip's latency), building a response map covering all 5 IDs at once — conceptually the response body would look like `{"order-1": "Customer-order-1", ..., "order-5": "Customer-order-5"}`.
4. **`main` receives the whole `customerNames` map back from that single call**, and the subsequent loop over `orderIds` does purely local map lookups (`customerNames.get(orderId)`) — no further network calls happen inside the loop at all.
5. **Total elapsed time is the sum of exactly two round-trips** (list orders, batch-fetch names) — contrast directly with Level 1, where the loop itself contained the network calls, so elapsed time scaled linearly with the number of orders (5 orders = 5 extra round-trips; 500 orders would mean 500 extra round-trips).

The structural lesson: in the chatty version, the *loop* is where the network calls live, so the call count scales with the data size. In the batched version, the network call happens *once*, outside the loop, with the loop only iterating over already-fetched, already-local data — moving the network call outside the loop, and making it accept/return a collection, is the entire fix.

## 7. Gotchas & takeaways

> **Gotcha:** parallelizing chatty calls (Level 2) improves wall-clock latency but not the underlying problem — it still opens N connections and puts N times the request load on the downstream service; under real concurrent traffic from many clients doing this simultaneously, the downstream service can be overwhelmed by connection and request volume even though each individual client's *perceived* latency looks fine.

- Watch for the N+1 pattern specifically: one call to get a list, then one more call per list item — this is the most common source of chatty design and often creeps in unnoticed as a "just one more field" addition.
- Round-trip latency is paid per call regardless of payload size, so batching many small requests into one is usually a bigger win than optimizing what's inside each individual small request.
- Parallelizing sequential calls trades wall-clock latency for concurrent resource usage; it's a real improvement but not a substitute for actually reducing the number of round-trips via batching.
- Design APIs to accept and return collections where a caller is likely to need many related items at once — a bulk endpoint costs little extra to build and prevents an entire class of future chattiness.
