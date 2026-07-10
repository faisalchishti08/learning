---
card: java
gi: 878
slug: completionservice
title: CompletionService
---

## 1. What it is

`CompletionService<V>` (typically `ExecutorCompletionService<V>`) decouples submitting tasks from collecting their results *in the order they actually finish*, rather than the order you submitted them. It wraps an `ExecutorService` and adds a completion queue: you `submit()` `Callable`s as usual, but instead of calling `get()` on each individual `Future` in submission order (which forces you to wait for task #1 even if task #3 finished first), you call `take()` (blocking) or `poll()` (non-blocking or timed) on the `CompletionService` itself, which hands you whichever `Future` completed next, regardless of submission order.

## 2. Why & when

Plain `Future.get()` in a loop over a list of submitted tasks forces you to process results in submission order — if task #1 happens to be the slowest of the batch, you're stuck waiting for it even though tasks #2 through #10 might have already finished. This is wasteful whenever you don't actually care about order and just want to react to each result as soon as it's ready — fanning out several independent queries and processing whichever comes back first, or racing several redundant requests and using the first successful one. `CompletionService` is the direct fix: it gives you results in *completion* order, letting you start processing early results immediately instead of blocking on an artificial submission-order constraint.

## 3. Core concept

```java
ExecutorService pool = Executors.newFixedThreadPool(4);
CompletionService<Integer> ecs = new ExecutorCompletionService<>(pool);

for (Callable<Integer> task : tasks) {
    ecs.submit(task); // same as pool.submit(task), but also registers with the completion queue
}

for (int i = 0; i < tasks.size(); i++) {
    Future<Integer> completed = ecs.take(); // blocks until the NEXT task to finish is ready -- any order
    System.out.println("got a result: " + completed.get());
}
```

`take()` returns whichever submitted task's `Future` is next to complete — you never have to guess or wait on a specific one.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three tasks submitted in order 1,2,3 but finishing in order 3,1,2; CompletionService.take returns them in the order they actually complete">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Submitted: task1, task2, task3 (in that order)</text>

  <rect x="20" y="35" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">task1 -- finishes 2nd</text>
  <rect x="220" y="35" width="180" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="310" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">task2 -- finishes 3rd</text>
  <rect x="420" y="35" width="180" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="510" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">task3 -- finishes 1st</text>

  <text x="320" y="95" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">take() call order:</text>
  <rect x="120" y="110" width="120" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="180" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">1st take() -&gt; task3</text>
  <rect x="260" y="110" width="120" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="130" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">2nd take() -&gt; task1</text>
  <rect x="400" y="110" width="120" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="460" y="130" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">3rd take() -&gt; task2</text>
</svg>

*Results arrive via `take()` in completion order — the fastest task, `task3`, is the first one your code ever sees, even though it was submitted last.*

## 5. Runnable example

Scenario: querying several mirror servers for the same data (simulated with variable delays) and using whichever responds first, growing from a naive submission-order-blocking version, to a correct `CompletionService` version, to a version that races redundant requests and cancels the losers once a winner is found.

### Level 1 — Basic

```java
import java.util.concurrent.*;
import java.util.*;

public class SubmissionOrderBlocking {
    static int queryMirror(String name, int delayMs) throws InterruptedException {
        Thread.sleep(delayMs);
        return name.hashCode();
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(3);
        List<Future<Integer>> futures = new ArrayList<>();
        futures.add(pool.submit(() -> queryMirror("slow-mirror", 300)));
        futures.add(pool.submit(() -> queryMirror("fast-mirror", 50)));
        futures.add(pool.submit(() -> queryMirror("medium-mirror", 150)));

        long start = System.currentTimeMillis();
        // Forced to wait for futures.get(0) FIRST, even though it's the SLOWEST -- wastes the fast result
        Integer firstResult = futures.get(0).get();
        System.out.println("first result obtained after " + (System.currentTimeMillis() - start) + "ms (waited for the SLOW one)");
        pool.shutdown();
    }
}
```

**How to run:** `java SubmissionOrderBlocking.java` (JDK 17+).

Expected output shape:
```
first result obtained after 300ms (waited for the SLOW one)
```

Even though `fast-mirror` finishes in 50ms, calling `get()` on `futures.get(0)` (the slow one, submitted first) forces the caller to wait the full 300ms — the fast result is sitting ready and unused the whole time.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class CompletionServiceOrder {
    static int queryMirror(String name, int delayMs) throws InterruptedException {
        Thread.sleep(delayMs);
        return name.hashCode();
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(3);
        CompletionService<Integer> ecs = new ExecutorCompletionService<>(pool);

        ecs.submit(() -> queryMirror("slow-mirror", 300));
        ecs.submit(() -> queryMirror("fast-mirror", 50));
        ecs.submit(() -> queryMirror("medium-mirror", 150));

        long start = System.currentTimeMillis();
        Future<Integer> firstCompleted = ecs.take(); // returns whichever finishes FIRST, not submission order
        System.out.println("first result obtained after " + (System.currentTimeMillis() - start) + "ms (the FAST one, as expected)");
        System.out.println("result value: " + firstCompleted.get());

        pool.shutdown();
    }
}
```

**How to run:** `java CompletionServiceOrder.java`.

Expected output shape:
```
first result obtained after 50ms (the FAST one, as expected)
result value: ...
```

The real-world concern added: `ecs.take()` returns the fastest-completing task's `Future` first, regardless of submission order — the caller gets useful results as soon as they're actually ready, rather than being artificially blocked by whichever task happened to be submitted first.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.*;

public class RaceAndCancelLosers {
    static int queryMirror(String name, int delayMs) throws InterruptedException {
        Thread.sleep(delayMs);
        return name.hashCode();
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(4);
        CompletionService<Integer> ecs = new ExecutorCompletionService<>(pool);

        Map<Future<Integer>, String> namesByFuture = new HashMap<>();
        record MirrorTask(String name, int delayMs) {}
        List<MirrorTask> mirrors = List.of(
            new MirrorTask("mirror-A", 400),
            new MirrorTask("mirror-B", 250),
            new MirrorTask("mirror-C", 100),  // expected winner
            new MirrorTask("mirror-D", 350)
        );

        for (MirrorTask m : mirrors) {
            Future<Integer> f = ecs.submit(() -> queryMirror(m.name(), m.delayMs()));
            namesByFuture.put(f, m.name());
        }

        Future<Integer> winner = ecs.take(); // first to complete -- our authoritative result
        System.out.println("winner: " + namesByFuture.get(winner) + ", value=" + winner.get());

        // Cancel every OTHER task -- we don't need redundant, slower results anymore
        int cancelledCount = 0;
        for (Future<Integer> f : namesByFuture.keySet()) {
            if (f != winner && f.cancel(true)) {
                cancelledCount++;
            }
        }
        System.out.println("cancelled " + cancelledCount + " redundant, slower requests");

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java RaceAndCancelLosers.java`.

Expected output:
```
winner: mirror-C, value=...
cancelled 3 redundant, slower requests
```

This adds the production-flavored hard case: submitting several redundant requests to different mirrors, using `CompletionService` to grab the *first* one that finishes, and then explicitly `cancel(true)`-ing the remaining, still-in-flight `Future`s — since their results are no longer needed, freeing up the pool's threads and avoiding wasted work rather than letting all four requests run to completion regardless.

## 6. Walkthrough

Tracing `RaceAndCancelLosers.main`:

1. Four tasks are submitted via `ecs.submit(...)`, one per simulated mirror, each with a different artificial delay (400ms, 250ms, 100ms, 350ms) — all four begin running concurrently on the 4-thread pool.
2. `namesByFuture` records which `Future` corresponds to which mirror's name, since `CompletionService` itself only hands back `Future` objects, not the original task metadata.
3. `ecs.take()` blocks until the *first* task to complete is ready — since `mirror-C`'s delay (100ms) is the shortest, its `Future` becomes available first and is returned, regardless of the fact that `mirror-A` was submitted before it.
4. `namesByFuture.get(winner)` looks up which mirror actually won, and `winner.get()` retrieves its computed value (already complete, so this call returns immediately without blocking).
5. The loop over `namesByFuture.keySet()` then calls `cancel(true)` on every `Future` *except* the winner — for `mirror-A`, `mirror-B`, and `mirror-D`, which are still sleeping inside their respective `Thread.sleep` calls, `cancel(true)` interrupts them, causing `InterruptedException` to propagate out of their `queryMirror` calls and abandon those tasks early, rather than letting them run their full artificial delay to completion for no purpose.
6. `cancel()` returns `true` for each of these three, since they were successfully interrupted before completing (a task that had *already* finished by the time `cancel` is called would instead return `false`), so `cancelledCount` reaches 3.
7. `pool.shutdown()` and `awaitTermination` then wait for the (now-interrupted) tasks to actually unwind and the pool to fully quiesce before the program exits.

## 7. Gotchas & takeaways

> **Gotcha:** `CompletionService.submit()` still requires you to keep your own mapping (like `namesByFuture` above) from `Future` back to whatever metadata you care about (a mirror's name, a request ID) — the completion queue only ever hands you `Future` objects, stripped of any association with which specific task they came from, unless you track that yourself.

- Use `CompletionService` whenever you don't need results in submission order and want to react to whichever task finishes first — it eliminates the "stuck waiting on the slowest submitted task" problem of a plain list of `Future`s.
- `take()` blocks until the next result is ready; `poll()` (with or without a timeout) lets you check without blocking indefinitely.
- Racing redundant requests and cancelling the losers via `cancel(true)` once a winner is found is a common, effective pattern for latency-sensitive systems willing to trade some wasted work for a faster typical response.
- `CompletionService` wraps an existing `ExecutorService` — you still need to create, size, and eventually shut down that underlying pool yourself.
- For coordinating and combining results from several async operations with richer composition (chaining, combining, handling failures) rather than just "first to finish wins," see [`CompletableFuture`](0879-completablefuture-creation-supplyasync-runasync.md) and its combinators.
