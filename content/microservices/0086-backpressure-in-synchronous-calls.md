---
card: microservices
gi: 86
slug: backpressure-in-synchronous-calls
title: "Backpressure in synchronous calls"
---

## 1. What it is

Backpressure is what happens — intentionally or accidentally — when a system pushes back against incoming work it cannot currently handle, rather than accepting unlimited requests and collapsing under the load. In synchronous, [request/response](0075-synchronous-request-response-model.md) systems, this typically means bounding the number of concurrent in-flight requests a service will accept (via a limited thread pool or connection pool) and rejecting or queuing anything beyond that bound, rather than letting unlimited requests queue up in unbounded memory until the service runs out of resources and fails catastrophically for everyone.

## 2. Why & when

Every synchronous service has a real, finite capacity — a limited number of threads, database connections, or CPU cores — beyond which it simply cannot process more work at once, no matter how many requests arrive. Without backpressure, a burst of traffic beyond that capacity causes requests to queue up unbounded: memory grows, response times climb for every request (including ones that would otherwise have been fast), and eventually the service either runs out of memory or every request times out anyway — a failure mode far worse than cleanly rejecting the excess up front. Backpressure converts an uncontrolled, system-wide collapse into a controlled, partial degradation: some requests get a fast, clear rejection, while requests within capacity continue to be served normally and promptly.

Apply backpressure at any synchronous entry point that could plausibly receive more concurrent load than it can actually process — an API gateway, a service's own HTTP endpoint, a connection pool to a downstream dependency. It matters most for the services deepest in a dependency chain, since without it, an overload there can cascade backward through every caller in the chain (see [chained synchronous calls](0075-synchronous-request-response-model.md)).

## 3. Core concept

A bounded pool accepts work up to its capacity; requests beyond that capacity are rejected immediately (fast failure) rather than queued indefinitely (slow, cascading failure).

```
Capacity: 3 concurrent requests
Request 1, 2, 3 arrive -> accepted, processing
Request 4 arrives      -> REJECTED immediately (fast, clear failure)
                           NOT queued indefinitely behind 1, 2, 3
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bounded pool of three worker slots accepts three requests; a fourth request is rejected immediately rather than queued indefinitely">
  <rect x="20" y="20" width="600" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Bounded pool (capacity=3)</text>
  <rect x="60" y="55" width="80" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="100" y="77" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">req 1</text>
  <rect x="180" y="55" width="80" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="220" y="77" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">req 2</text>
  <rect x="300" y="55" width="80" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="340" y="77" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">req 3</text>
  <rect x="440" y="55" width="140" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="510" y="77" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">(no room)</text>

  <rect x="260" y="140" width="150" height="35" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="335" y="162" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">req 4: REJECTED immediately</text>
  <line x1="335" y1="140" x2="335" y2="100" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3"/>
</svg>

Capacity is fixed; excess load is rejected fast rather than queued and left to degrade everything.

## 5. Runnable example

Scenario: a service receiving concurrent requests, first with unbounded acceptance causing every request to slow down together as load grows, then fixed with a bounded pool that rejects excess load immediately, then extended to add a small bounded *queue* on top of the pool — a common middle ground between "reject immediately" and "accept unlimited."

### Level 1 — Basic

```java
// File: UnboundedAcceptance.java -- accept EVERY request into an
// unbounded queue -- as load grows past real capacity, EVERY request's
// wait time grows too, including ones that arrived early.
import java.util.*;
import java.util.concurrent.*;

public class UnboundedAcceptance {
    static ExecutorService pool = Executors.newFixedThreadPool(2); // real capacity: 2 concurrent workers

    static int process(int requestId) throws InterruptedException {
        Thread.sleep(100); // simulated processing time
        return requestId;
    }

    public static void main(String[] args) throws Exception {
        List<Future<Integer>> futures = new ArrayList<>();
        for (int i = 1; i <= 5; i++) {
            int id = i;
            futures.add(pool.submit(() -> process(id))); // ALL 5 accepted, queued behind only 2 workers
        }
        for (Future<Integer> f : futures) {
            System.out.println("Completed request: " + f.get());
        }
        pool.shutdown();
    }
}
```

**How to run:** `javac UnboundedAcceptance.java && java UnboundedAcceptance` (JDK 17+).

Expected output:
```
Completed request: 1
Completed request: 2
Completed request: 3
Completed request: 4
Completed request: 5
```

All 5 requests eventually complete, but with only 2 real workers, requests 3, 4, and 5 each wait behind earlier ones — with no limit on how many requests could be queued this way, a large enough burst could queue thousands of requests, each waiting longer and longer, and consuming memory the whole time.

### Level 2 — Intermediate

```java
// File: BoundedRejection.java -- accept ONLY as many CONCURRENT requests
// as real capacity allows; reject anything beyond that IMMEDIATELY.
import java.util.concurrent.*;

public class BoundedRejection {
    static Semaphore capacity = new Semaphore(2); // real capacity: 2 concurrent requests

    static String handleRequest(int requestId) {
        if (!capacity.tryAcquire()) { // non-blocking: fail FAST if no capacity, don't wait
            return "request " + requestId + ": REJECTED (503, no capacity)";
        }
        try {
            Thread.sleep(50); // simulated processing time
            return "request " + requestId + ": completed";
        } catch (InterruptedException e) {
            return "request " + requestId + ": interrupted";
        } finally {
            capacity.release();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        // simulate 2 requests holding capacity WHILE a 3rd arrives
        Thread worker1 = new Thread(() -> System.out.println(handleRequest(1)));
        Thread worker2 = new Thread(() -> System.out.println(handleRequest(2)));
        worker1.start();
        worker2.start();
        Thread.sleep(10); // let workers 1 and 2 acquire capacity first
        System.out.println(handleRequest(3)); // capacity is full -- rejected immediately, no wait
        worker1.join();
        worker2.join();
    }
}
```

**How to run:** `javac BoundedRejection.java && java BoundedRejection` (JDK 17+).

Expected output (order of request 1/2 completion may vary slightly, but request 3 always rejects immediately):
```
request 3: REJECTED (503, no capacity)
request 1: completed
request 2: completed
```

Request 3 gets an immediate, clear rejection instead of waiting behind requests 1 and 2 — its caller finds out right away that capacity is exhausted, rather than experiencing an unexplained delay.

### Level 3 — Advanced

```java
// File: BoundedQueueThenReject.java -- a common middle ground: allow a
// SMALL bounded queue on top of the worker pool (absorb brief bursts),
// but still reject once even that queue fills -- never grow unbounded.
import java.util.concurrent.*;

public class BoundedQueueThenReject {
    static ThreadPoolExecutor pool = new ThreadPoolExecutor(
        2, 2,                                  // 2 core/max worker threads -- real capacity
        0L, TimeUnit.MILLISECONDS,
        new ArrayBlockingQueue<>(1),           // a SMALL bounded queue -- absorbs 1 extra request
        new ThreadPoolExecutor.AbortPolicy()   // reject (throw) once pool AND queue are both full
    );

    static String process(int requestId) throws InterruptedException {
        Thread.sleep(50);
        return "request " + requestId + ": completed";
    }

    public static void main(String[] args) throws InterruptedException {
        for (int i = 1; i <= 4; i++) {
            int id = i;
            try {
                pool.submit(() -> {
                    try { System.out.println(process(id)); }
                    catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                });
                System.out.println("request " + id + ": accepted (worker or queue slot found)");
            } catch (RejectedExecutionException e) {
                System.out.println("request " + id + ": REJECTED (pool AND queue both full)");
            }
        }
        Thread.sleep(200); // let accepted work finish before shutdown
        pool.shutdown();
    }
}
```

**How to run:** `javac BoundedQueueThenReject.java && java BoundedQueueThenReject` (JDK 17+).

Expected output (interleaving of "accepted"/"completed" lines may vary, but exactly 3 requests are accepted and request 4 is rejected):
```
request 1: accepted (worker or queue slot found)
request 2: accepted (worker or queue slot found)
request 3: accepted (worker or queue slot found)
request 4: REJECTED (pool AND queue both full)
request 1: completed
request 2: completed
request 3: completed
```

## 6. Walkthrough

1. **Level 1** — a fixed thread pool with 2 workers accepts all 5 submitted tasks via `pool.submit`, since `ExecutorService`'s default internal queue is unbounded. `main` collects all 5 `Future`s and blocks on each via `.get()`, printing completions in submission order. All 5 requests do eventually complete, but requests 3, 4, and 5 each had to wait behind earlier ones with no limit on how much further queuing could occur under heavier load — a large burst here would keep queuing invisibly, consuming memory and stretching every request's latency, with no early warning to any caller.
2. **Level 2 — rejecting immediately instead of queuing** — `capacity` is a `Semaphore` initialized with `2` permits, representing real processing capacity. `handleRequest` calls `capacity.tryAcquire()`, a *non-blocking* check: if a permit is available, it's taken and the request proceeds; if not, the method returns a rejection message immediately, without waiting at all. `main` starts two threads that each successfully acquire a permit and begin their simulated 50ms of work, then (after a short sleep to let them start) calls `handleRequest(3)` on the main thread directly — with both permits already held, `tryAcquire()` returns `false` immediately, and request 3's rejection prints right away, well before requests 1 and 2 finish.
3. **Level 3 — a small buffer before rejecting** — `ThreadPoolExecutor` is configured with exactly 2 core/max threads (matching Level 2's real capacity) plus a small `ArrayBlockingQueue<>(1)` — room for exactly one extra request to wait briefly — and an `AbortPolicy`, which throws `RejectedExecutionException` once both the 2 worker slots and the 1 queue slot are all occupied.
4. **Tracing the four submissions** — request 1 finds a free worker thread and is accepted, printing its "accepted" line immediately. Request 2 similarly finds the second free worker thread and is accepted. Request 3 finds both worker threads busy, but the queue has room (its 1 slot is empty), so it's accepted into the queue and will run as soon as a worker frees up. Request 4 finds both worker threads busy *and* the queue's single slot already occupied by request 3 — `pool.submit` throws `RejectedExecutionException`, caught by `main`'s try/catch, printing the rejection line for request 4.
5. **Contrasting the three levels** — Level 1 would have quietly queued all 5 requests, potentially into the thousands under a large enough burst, with degrading service for everyone. Level 2 rejects the instant real capacity is exhausted, with zero tolerance for even a brief burst. Level 3 strikes a middle ground: it absorbs one request's worth of brief burst via the small bounded queue, but still guarantees a hard ceiling — once that queue is also full, new requests are rejected immediately rather than piling up without bound, giving both some burst tolerance and a hard backpressure limit.

## 7. Gotchas & takeaways

> **Gotcha:** an unbounded queue in front of a bounded worker pool (as in Level 1, where the `ExecutorService`'s internal queue has no size limit) provides zero real backpressure, even though the worker pool itself is bounded — the illusion of a capacity limit is undermined entirely by an unbounded queue sitting in front of it. Always bound the queue too, or skip it and reject immediately, as Level 2 and 3 both do.

- Backpressure converts an unbounded, system-wide collapse under overload into a controlled, partial degradation: some requests fail fast and clearly, while requests within real capacity continue to be served promptly.
- A non-blocking capacity check (Level 2's `tryAcquire`) rejects excess load immediately, with no added latency for the rejected request or for requests already being served.
- A small, explicitly bounded queue (Level 3) can absorb brief bursts without sacrificing the hard ceiling that real backpressure requires — the key word is *bounded*; an unbounded queue defeats the purpose entirely.
- Apply backpressure at every synchronous entry point in a chain, especially the deepest, most heavily depended-upon services — without it, one overloaded service's queue can quietly cascade slowness back through every caller in the chain (see [synchronous request/response model](0075-synchronous-request-response-model.md)).
- This is the synchronous counterpart to flow control in asynchronous, event-driven systems — the same underlying problem (a consumer that can't keep up with incoming work) solved with a different mechanism appropriate to the request/response shape.
