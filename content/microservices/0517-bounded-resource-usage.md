---
card: microservices
gi: 517
slug: bounded-resource-usage
title: "Bounded resource usage"
---

## 1. What it is

**Bounded resource usage** means every queue, thread pool, connection pool, and in-memory buffer in a service has an explicit, finite maximum size, instead of being allowed to grow without limit. When a bound is reached, the service makes a deliberate choice — reject new work, apply backpressure, or shed load — rather than letting memory or threads grow until the process runs out of resources and crashes or grinds to a halt. It's the discipline of designing for "what happens when this fills up" as a first-class case, not an afterthought.

## 2. Why & when

You bound resources deliberately because unbounded ones fail in the worst possible way — slowly, then all at once, usually under the exact peak load when failing gracefully matters most:

- **An unbounded queue in front of a slow consumer just grows.** If producers add work faster than a consumer can drain it, an unbounded queue absorbs the difference silently, using more and more memory, until the process runs out of heap and crashes — taking down whatever *was* being processed along with whatever was waiting.
- **A bounded queue turns that same overload into an explicit, immediate decision**: once full, either the producer blocks (backpressure) or new work is rejected outright (load shedding) — both are worse for the specific request that gets rejected, but far better for the service's overall survival and its ability to keep serving everything already accepted.
- **This applies to every unbounded resource, not just queues** — thread pools that spawn a new thread per request under load, in-memory caches with no eviction, buffers that grow to hold an entire unbounded response — all fail the same way: fine under normal load, catastrophic exactly when load spikes.
- **You choose the bound based on what "failing" should look like** — a bounded queue with a fast-reject policy fails fast and cheaply; a bounded queue with a blocking-producer policy applies backpressure upstream instead, which is preferable when the caller can usefully slow down.

## 3. Core concept

Think of a restaurant's kitchen with a physical order rail that can hold at most 20 tickets. If the rail could grow infinitely, the kitchen would happily accept every order coming in during a rush, building up hundreds of pending tickets that will all eventually go out cold and late, or never at all once the kitchen simply can't function anymore. A rail capped at 20 forces an explicit decision once it's full: the host stops seating new tables (backpressure) or tells arriving customers "kitchen's at capacity, try back in 10 minutes" (load shedding) — either way the kitchen keeps functioning for the 20 tickets it already committed to, instead of collapsing under an unbounded backlog.

Concretely:

1. **Every resource that can grow under load needs an explicit maximum**: queue depth, thread pool size, connection pool size, cache entry count, request body size.
2. **Reaching the bound triggers a deliberate policy**, decided in advance: reject-immediately (fail fast, cheap), block-the-producer (backpressure, propagates the slowdown upstream), or evict-oldest (bounded cache).
3. **The choice of policy depends on what's acceptable to lose or delay** — rejecting a request outright is appropriate when the caller can retry; blocking a producer thread is appropriate when propagating slowness upstream is safer than silently queuing unboundedly.
4. **Bounding resources trades "rare total failure" for "frequent partial failure"** — some requests get rejected or delayed under peak load, but the service as a whole keeps running and recovers once load subsides, instead of crashing and needing a restart.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Unbounded queue grows without limit under overload until the process runs out of memory; bounded queue rejects or blocks once full, keeping the service alive">
  <text x="150" y="24" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Unbounded queue</text>
  <rect x="20" y="40" width="260" height="34" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">queue: 50,000 items and growing...</text>
  <rect x="20" y="84" width="260" height="34" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">heap exhausted -- process crashes</text>
  <text x="150" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">everything, including work already accepted, is lost</text>

  <text x="510" y="24" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Bounded queue</text>
  <rect x="380" y="40" width="260" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">queue: 500/500 -- FULL</text>
  <rect x="380" y="84" width="260" height="34" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">new work: rejected (503) or producer blocks</text>
  <text x="510" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the 500 already accepted keep processing normally</text>
</svg>

An unbounded queue fails catastrophically once memory runs out; a bounded queue fails one request at a time and keeps running.

## 5. Runnable example

Scenario: a task-processing service accepting work faster than it can process it. We start with an unbounded queue that silently grows, extend it to a bounded queue that rejects work once full, then handle the hard case: a bounded queue with a configurable policy (reject-fast vs. block-with-timeout) so callers can choose the right failure mode for their situation.

### Level 1 — Basic

```java
// File: UnboundedQueueDemo.java -- an UNBOUNDED queue: producers can
// add work forever, with no limit, regardless of how fast it's consumed.
import java.util.concurrent.*;

public class UnboundedQueueDemo {
    public static void main(String[] args) throws InterruptedException {
        LinkedBlockingQueue<String> queue = new LinkedBlockingQueue<>(); // no capacity given = unbounded
        for (int i = 1; i <= 5; i++) {
            queue.put("task-" + i); // always succeeds, no matter how full the queue gets
        }
        System.out.println("Queue size: " + queue.size() + " (would keep growing under real overload, unbounded)");
    }
}
```

How to run: `java UnboundedQueueDemo.java`

`new LinkedBlockingQueue<>()` with no capacity argument has no maximum size — `put()` always succeeds immediately. Under real load where producers outpace the consumer, this queue would grow without any limit, silently consuming memory until the process runs out.

### Level 2 — Intermediate

```java
// File: BoundedQueueDemo.java -- a BOUNDED queue: capacity is capped,
// and adding to a full queue fails immediately instead of growing.
import java.util.concurrent.*;

public class BoundedQueueDemo {
    public static void main(String[] args) {
        ArrayBlockingQueue<String> queue = new ArrayBlockingQueue<>(3); // hard cap of 3
        for (int i = 1; i <= 5; i++) {
            boolean accepted = queue.offer("task-" + i); // non-blocking: fails instead of waiting or growing
            System.out.println("task-" + i + " -> " + (accepted ? "accepted (queue size=" + queue.size() + ")" : "REJECTED, queue full"));
        }
    }
}
```

How to run: `java BoundedQueueDemo.java`

`ArrayBlockingQueue<>(3)` has a fixed capacity of 3. `offer()` (unlike `put()`) never blocks or grows the queue — it returns `false` immediately once full. Tasks 1-3 are accepted; tasks 4 and 5 are explicitly rejected, which is the deliberate, visible failure this pattern is designed to produce instead of silent unbounded growth.

### Level 3 — Advanced

```java
// File: PolicyBoundedQueue.java -- a bounded queue with a CONFIGURABLE
// policy: reject-fast for latency-sensitive callers, or block-with-timeout
// (backpressure) for callers that can tolerate a bounded wait.
import java.util.concurrent.*;

public class PolicyBoundedQueue {
    enum Policy { REJECT_FAST, BLOCK_WITH_TIMEOUT }

    static boolean submit(ArrayBlockingQueue<String> queue, String task, Policy policy) throws InterruptedException {
        switch (policy) {
            case REJECT_FAST:
                return queue.offer(task); // fails immediately if full -- for callers who'd rather retry elsewhere
            case BLOCK_WITH_TIMEOUT:
                return queue.offer(task, 200, TimeUnit.MILLISECONDS); // waits up to 200ms for room, THEN gives up
            default:
                throw new IllegalArgumentException();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ArrayBlockingQueue<String> queue = new ArrayBlockingQueue<>(2);
        queue.put("existing-1");
        queue.put("existing-2"); // queue is now full: 2/2

        // A latency-sensitive caller: fail immediately rather than wait.
        boolean fastResult = submit(queue, "urgent-task", Policy.REJECT_FAST);
        System.out.println("REJECT_FAST on full queue -> accepted=" + fastResult + " (returned instantly)");

        // A tolerant caller: willing to wait briefly for a consumer to free a slot.
        ExecutorService consumer = Executors.newSingleThreadExecutor();
        consumer.submit(() -> {
            try {
                Thread.sleep(100); // consumer drains one item after 100ms
                queue.take();
                System.out.println("[consumer] drained one item, freeing a slot");
            } catch (InterruptedException ignored) {}
        });

        long start = System.currentTimeMillis();
        boolean blockResult = submit(queue, "tolerant-task", Policy.BLOCK_WITH_TIMEOUT);
        System.out.println("BLOCK_WITH_TIMEOUT -> accepted=" + blockResult + " after " + (System.currentTimeMillis() - start) + "ms (waited for consumer to free a slot)");
        consumer.shutdown();
    }
}
```

How to run: `java PolicyBoundedQueue.java`

`REJECT_FAST` uses `offer(task)` with no wait — it fails the instant the queue is full, appropriate when the caller would rather get an immediate error and retry elsewhere than sit waiting. `BLOCK_WITH_TIMEOUT` uses `offer(task, 200, MILLISECONDS)`, which waits up to 200ms for a slot to open before giving up — appropriate when applying backpressure to the caller (making it wait briefly) is preferable to an instant rejection. In the demo, the consumer thread frees a slot after 100ms, so the tolerant submission succeeds at roughly the 100ms mark, well inside its 200ms budget — demonstrating the bound is still enforced (it would have failed at 200ms if the consumer never freed a slot), just with a grace period the fast policy doesn't get.

## 6. Walkthrough

Trace `PolicyBoundedQueue.main` end to end:

1. **The queue is created with capacity 2**, and two `put()` calls fill it completely (`existing-1`, `existing-2`) — the queue is now at its hard bound, 2/2.
2. **`submit(queue, "urgent-task", REJECT_FAST)` is called.** Internally this calls `queue.offer("urgent-task")` with no wait argument. Because the queue is full, `offer` returns `false` immediately — no blocking, no growth. The caller sees `accepted=false` in effectively zero time, and can immediately decide to retry elsewhere, return an error to *its* caller, or shed the request.
3. **A single-threaded consumer executor is started**, scheduled to sleep 100ms and then call `queue.take()`, which removes one item (`existing-1`) and logs that it drained a slot.
4. **Concurrently, `submit(queue, "tolerant-task", BLOCK_WITH_TIMEOUT)` is called.** Internally this calls `queue.offer("tolerant-task", 200, MILLISECONDS)`. Because the queue is still full at this instant, the calling thread blocks — but only up to 200ms.
5. **At roughly the 100ms mark, the consumer's `take()` fires**, removing `existing-1` and freeing one slot in the queue.
6. **The blocked `offer(...)` call, which has been waiting since roughly time zero, notices the freed slot and succeeds** — it inserts `tolerant-task` and returns `true`, roughly 100ms after it started waiting, well under its 200ms ceiling.
7. **`main` prints the elapsed time** for the blocking call, demonstrating it resolved via the consumer's drain rather than via timing out.

The key structural contrast: `REJECT_FAST` converts overload into an instant, cheap failure signal the caller can act on immediately; `BLOCK_WITH_TIMEOUT` converts overload into a bounded wait that resolves successfully if the system recovers capacity in time, and only fails if it doesn't — both are deliberate, bounded outcomes, and neither lets the queue itself grow past its cap of 2.

## 7. Gotchas & takeaways

> **Gotcha:** a bounded queue with an unbounded *timeout* on the blocking path (or a `put()` instead of a time-bounded `offer()`) isn't actually bounded in the way that matters — the caller thread can now hang indefinitely waiting for room, which just moves the unbounded-growth problem from "queue memory" to "blocked caller threads," another resource that can now be exhausted instead.

- Every queue, pool, and buffer needs an explicit maximum size — "it'll be fine most of the time" is exactly the load profile that unbounded resources fail under, at the worst possible moment.
- Choose the overload policy deliberately: reject-fast for latency-sensitive callers who can retry elsewhere, block-with-timeout (backpressure) for callers who can tolerate a bounded wait.
- A bound only truly bounds the system if every step of the fallback path is also bounded — an unbounded wait on a "bounded" queue just relocates the problem.
- Bounding resources trades rare, catastrophic total failure for frequent, cheap partial failure (rejected requests) — a trade that's almost always worth making for service survivability under peak load.
