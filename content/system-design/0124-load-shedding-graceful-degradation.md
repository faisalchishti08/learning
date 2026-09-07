---
card: system-design
gi: 124
slug: load-shedding-graceful-degradation
title: Load shedding & graceful degradation
---

## 1. What it is

**Load shedding** deliberately rejects some incoming requests when a system is at or near capacity, so it can keep serving the requests it does accept well, instead of accepting everything and serving all of them badly (or crashing). **Graceful degradation** is serving a reduced, simpler version of a response under heavy load — skipping a non-essential feature — rather than either a full response or an outright failure.

## 2. Why & when

A system with no limit on accepted work degrades badly under overload: queues grow unboundedly, response times climb for every request including ones that could have been served quickly, and eventually the whole system can crash, serving nobody. Deliberately rejecting the excess (load shedding) or simplifying the response (graceful degradation) protects the requests the system *can* still handle well. Use load shedding at the edge of a system (an API gateway, a load balancer) to prevent overload from reaching internal services in the first place. Use graceful degradation inside a service, for features that are valuable but not essential to the core request — showing a product page without personalized recommendations rather than failing the whole page load.

## 3. Core concept

- **Load shedding — reject excess requests:** once a system is at capacity (measured by queue depth, CPU, or concurrent request count), new requests are rejected immediately with a clear response (e.g. HTTP 503 Service Unavailable), rather than queued indefinitely.
- **Shedding strategy — which requests to reject:** a common approach is to prioritize: reject low-priority or non-critical requests (background sync jobs) before rejecting high-priority ones (a checkout request), rather than shedding randomly.
- **Graceful degradation — simplify, don't fail:** identify non-essential parts of a response (a "related products" widget, a real-time counter) and skip them under load, returning the essential parts fast rather than failing the entire request waiting for a slow, non-essential dependency.
- **Circuit breaking as a trigger:** a failing or slow downstream dependency often triggers graceful degradation directly — if a recommendations service times out, skip it and return the response without recommendations rather than waiting or failing.
- **Fast failure over slow failure:** rejecting a request immediately, with a clear error, is far better for the caller (and for the system) than accepting it and taking a very long time to eventually fail — a fast, clean rejection lets the caller retry elsewhere or back off promptly.

## 4. Diagram

```
                     Incoming requests (rate rising)
                              |
                    Is the system at capacity?
                     /                    \
                   NO                     YES
                    |                       |
              process normally    Is this request low-priority?
                                     /              \
                                   YES               NO
                                    |                 |
                          REJECT (503,          Try graceful degradation:
                          shed the load)         skip non-essential parts,
                                                  return a reduced response
```
*Caption: at capacity, low-priority requests are shed outright; essential requests get a reduced, faster response instead of a full failure.*

## 5. Runnable example

**Level 1 — Basic.** Reject new requests once a simple concurrency limit is reached.

**Level 2 — Priority-aware shedding.** Shed only low-priority requests first when near capacity, protecting high-priority ones.

**Level 3 — Graceful degradation.** Serve a reduced response by skipping a slow, non-essential dependency instead of failing the whole request.

```java
// LoadSheddingDemo.java
import java.util.*;

public class LoadSheddingDemo {

    static int capacity = 3;
    static int currentLoad = 0;

    record Request(String id, String priority) {}

    static String handleRequest(Request req) {
        if (currentLoad >= capacity) {
            return "503 REJECTED (at capacity)";
        }
        currentLoad++;
        return "200 OK (processed)";
    }

    // Level 2: priority-aware shedding - reject low-priority requests first when near capacity.
    static String handleWithPriority(Request req, int nearCapacityThreshold) {
        if (currentLoad >= capacity) return "503 REJECTED (fully at capacity)";
        if (currentLoad >= nearCapacityThreshold && req.priority().equals("low")) {
            return "503 REJECTED (low-priority shed, nearing capacity)";
        }
        currentLoad++;
        return "200 OK (processed, priority=" + req.priority() + ")";
    }

    public static void main(String[] args) {
        // Level 1: plain capacity limit.
        List<Request> requests = List.of(
            new Request("r1", "normal"), new Request("r2", "normal"),
            new Request("r3", "normal"), new Request("r4", "normal") // 4th request exceeds capacity=3
        );
        for (Request r : requests) System.out.println(r.id() + ": " + handleRequest(r));

        // Level 2: reset load; near capacity, shed low-priority requests before high-priority ones.
        currentLoad = 0;
        List<Request> mixedRequests = List.of(
            new Request("checkout-1", "high"), new Request("background-sync-1", "low"),
            new Request("checkout-2", "high"), new Request("background-sync-2", "low")
        );
        int nearCapacityThreshold = 2;
        System.out.println("--- priority-aware shedding, threshold=" + nearCapacityThreshold + " ---");
        for (Request r : mixedRequests) System.out.println(r.id() + " (" + r.priority() + "): " + handleWithPriority(r, nearCapacityThreshold));

        // Level 3: graceful degradation - skip a slow, non-essential dependency instead of failing.
        boolean recommendationsServiceHealthy = false; // simulating a slow/failing downstream dependency
        String productPageCore = "Product: Wireless Mouse, $25.99";
        String response;
        if (recommendationsServiceHealthy) {
            response = productPageCore + " | Recommended: Mouse Pad, USB Hub";
        } else {
            response = productPageCore + " | (recommendations unavailable, showing core content only)";
        }
        System.out.println("product page response under degraded mode: " + response);
    }
}
```

**How to run:** save as `LoadSheddingDemo.java`, then run `java LoadSheddingDemo.java`.

## 6. Walkthrough

1. Level 1's `handleRequest` checks `currentLoad >= capacity` before accepting; the first three requests succeed and raise `currentLoad` to `3`, so the fourth request is rejected outright with a `503`.
2. Level 2's `handleWithPriority` adds a second check: once `currentLoad` reaches `nearCapacityThreshold` (here, `2`), any further `"low"` priority request is rejected even though the hard `capacity` limit has not been hit yet — this protects room for `"high"` priority requests still to come.
3. Running the mixed list shows both `checkout-1` and `checkout-2` (high priority) getting processed, while `background-sync-1` and `background-sync-2` (low priority) are shed once the threshold is reached — exactly the prioritized shedding strategy, protecting the requests that matter most.
4. Level 3 sets `recommendationsServiceHealthy = false`, modeling a slow or failing downstream dependency; the code branches to build a response with `productPageCore` alone, explicitly noting recommendations are unavailable.
5. The final printed response shows the essential product information still delivered successfully, with the non-essential recommendations section simply omitted — this is graceful degradation: the request as a whole succeeds, just with reduced functionality, rather than failing entirely while waiting on (or erroring from) the slow dependency.

## 7. Gotchas & takeaways

> Gotcha: load shedding only helps if the rejection itself is cheap. If checking "should I shed this request?" requires as much work as actually processing it (e.g. a database lookup to check a user's priority tier), the shedding logic itself can become the new bottleneck under the exact overload conditions it was meant to protect against. Keep the shed-or-accept decision fast and based on already-available information.

- Load shedding rejects excess requests outright once a system nears capacity, protecting the requests it can still serve well.
- Prioritized shedding rejects lower-priority work first, preserving capacity for the requests that matter most.
- Graceful degradation keeps a request succeeding by skipping non-essential parts of the response, rather than failing the whole request over a slow or failing non-critical dependency.
- Related concepts: [Backpressure & flow control](0117-backpressure-flow-control.md) (a related mechanism operating earlier, on the buffering layer), [Throughput vs latency](0125-throughput-vs-latency.md) (the trade-off shedding directly protects).
