---
card: java
gi: 883
slug: forkjoinpool-work-stealing
title: ForkJoinPool & work-stealing
---

## 1. What it is

`ForkJoinPool` is a specialized `ExecutorService` designed for **divide-and-conquer** computation: a large task is recursively split ("forked") into smaller subtasks, which run in parallel and are later recombined ("joined") into a final result. Its distinguishing internal feature is **work-stealing**: each worker thread has its own local deque (double-ended queue) of subtasks, pushing and popping from one end for its own work, while *idle* worker threads that run out of their own work can "steal" tasks from the *opposite* end of a busy thread's deque. This keeps all cores productively busy even when the recursive splitting produces wildly uneven amounts of work per branch.

## 2. Why & when

A regular fixed thread pool is a poor fit for recursive divide-and-conquer algorithms: each level of recursion would need to submit new tasks to the same pool and then block waiting for them, and if every thread in the pool is blocked waiting on its own subtasks, the pool can deadlock (no threads left to actually run the submitted subtasks). `ForkJoinPool`'s worker threads are designed to keep working on *other* available tasks while waiting for their own forked subtasks to complete, and work-stealing balances load automatically — a thread whose subtree happens to be small finishes early and steals work from a thread still churning through a larger subtree, rather than sitting idle. Use `ForkJoinPool` (or the higher-level `RecursiveTask`/`RecursiveAction`, or parallel streams, which use it internally) for genuinely recursive, splittable, CPU-bound computations — parallel sorting, parallel search, recursive aggregation over a tree or large array. It is a poor fit for I/O-bound or blocking work, since a worker thread blocked on I/O (rather than cooperating with the fork/join model) can't be "stolen from" or usefully repurposed the way CPU-bound forked tasks can.

## 3. Core concept

```java
ForkJoinPool pool = new ForkJoinPool(); // defaults to Runtime.getRuntime().availableProcessors() threads
long result = pool.invoke(new SumTask(array, 0, array.length));
// Internally: SumTask.compute() checks if the range is small enough to compute directly;
// if not, it forks two halves, each becomes its own subtask on some worker's local deque,
// and idle workers steal from busy workers' deques to keep every core occupied.
```

The pool itself is just the thread-management machinery; the actual splitting logic lives in `RecursiveTask`/`RecursiveAction` subclasses (see the next tutorial), which `ForkJoinPool` is specifically built to run efficiently.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two worker threads each with their own deque of tasks; worker 2 finishes its own small deque early and steals a task from the opposite end of worker 1's larger deque">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Worker 1 -- large subtree, own deque</text>
  <rect x="20" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="90" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="160" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="230" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="55" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">own end</text>
  <text x="255" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">steal end</text>

  <text x="480" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Worker 2 -- small subtree, finishes early</text>
  <rect x="440" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-dasharray="3"/>
  <text x="470" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">empty</text>

  <line x1="440" y1="60" x2="290" y2="45" stroke="#f0883e" stroke-width="2" stroke-dasharray="5" marker-end="url(#a19)"/>
  <text x="380" y="90" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Worker 2 steals a task from Worker 1's deque</text>

  <text x="320" y="150" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Both workers stay busy -- load automatically balances across uneven subtrees.</text>
  <defs><marker id="a19" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker></defs>
</svg>

*A worker pushes/pops its own tasks from one end of its deque; idle workers steal from the other end of a busy worker's deque, keeping every core occupied despite uneven splits.*

## 5. Runnable example

Scenario: summing a large array, growing from a plain sequential sum, to a naive `ForkJoinPool` submission using a plain `Runnable` (missing the point of fork/join), to a properly recursive divide-and-conquer sum that lets work-stealing balance load across an intentionally uneven workload.

### Level 1 — Basic

```java
public class SequentialSum {
    public static void main(String[] args) {
        int size = 20_000_000;
        long[] data = new long[size];
        for (int i = 0; i < size; i++) data[i] = i;

        long start = System.currentTimeMillis();
        long sum = 0;
        for (long v : data) sum += v; // single-threaded, uses only one core
        System.out.println("sum = " + sum);
        System.out.println("elapsed ~" + (System.currentTimeMillis() - start) + "ms (single core)");
    }
}
```

**How to run:** `java SequentialSum.java` (JDK 17+).

Expected output shape:
```
sum = 199999990000000
elapsed ~40ms (single core)
```

Correct, but only ever uses one CPU core — on a multi-core machine, this leaves most of the available compute capacity completely idle.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class NaiveForkJoinSubmission {
    static long sumRange(long[] data, int from, int to) {
        long sum = 0;
        for (int i = from; i < to; i++) sum += data[i];
        return sum;
    }

    public static void main(String[] args) throws Exception {
        int size = 20_000_000;
        long[] data = new long[size];
        for (int i = 0; i < size; i++) data[i] = i;

        ForkJoinPool pool = new ForkJoinPool(); // defaults to availableProcessors() threads

        // Naive: manually splitting into a FIXED number of chunks up front (not truly recursive
        // divide-and-conquer), submitted as plain Callables -- this works but doesn't let
        // work-stealing rebalance if one chunk happens to take longer than the others.
        int chunks = Runtime.getRuntime().availableProcessors();
        int chunkSize = size / chunks;
        var futures = new Future[chunks];
        for (int c = 0; c < chunks; c++) {
            int from = c * chunkSize;
            int to = (c == chunks - 1) ? size : from + chunkSize;
            futures[c] = pool.submit(() -> sumRange(data, from, to));
        }

        long total = 0;
        for (Future f : futures) total += (Long) f.get();
        System.out.println("sum = " + total);
        pool.shutdown();
    }
}
```

**How to run:** `java NaiveForkJoinSubmission.java`.

Expected output:
```
sum = 199999990000000
```

Correct and uses all cores, but the chunking is fixed and manual — if the actual work per chunk turns out uneven (which this example's uniform array doesn't show, but real workloads often are), the threads handling smaller chunks simply finish early and sit idle, since there's no recursive splitting for work-stealing to redistribute.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class RecursiveWorkStealingSum {
    static long[] data;

    static class SumTask extends RecursiveTask<Long> {
        final int from, to;
        SumTask(int from, int to) { this.from = from; this.to = to; }

        static final int THRESHOLD = 10_000;

        @Override
        protected Long compute() {
            if (to - from <= THRESHOLD) {
                long sum = 0;
                for (int i = from; i < to; i++) sum += data[i];
                return sum;
            }
            int mid = (from + to) / 2;
            SumTask left = new SumTask(from, mid);
            SumTask right = new SumTask(mid, to);
            left.fork();                    // submit left half to be run asynchronously (possibly stolen)
            long rightResult = right.compute(); // compute right half on THIS thread directly
            long leftResult = left.join();       // wait for the forked left half (steals work in the meantime if idle)
            return leftResult + rightResult;
        }
    }

    public static void main(String[] args) {
        int size = 20_000_000;
        data = new long[size];
        for (int i = 0; i < size; i++) data[i] = i; // uniform here, but recursive splitting handles UNEVEN work too

        ForkJoinPool pool = new ForkJoinPool();
        long start = System.currentTimeMillis();
        long sum = pool.invoke(new SumTask(0, size));
        System.out.println("sum = " + sum);
        System.out.println("elapsed ~" + (System.currentTimeMillis() - start) + "ms (all cores, auto-balanced)");
        pool.shutdown();
    }
}
```

**How to run:** `java RecursiveWorkStealingSum.java`.

Expected output shape (correctness is exact; elapsed time is machine-dependent but uses all cores):
```
sum = 199999990000000
elapsed ~15ms (all cores, auto-balanced)
```

This adds the production-flavored hard case: genuine recursive divide-and-conquer via `RecursiveTask`, splitting down to a small threshold before computing directly. Because `left.fork()` hands the left half off as an independent task any idle worker thread can pick up (or steal), while the current thread proceeds directly to `right.compute()`, the workload naturally spreads across however many cores are available and automatically rebalances if some subtrees happen to take longer than others — unlike the fixed, manual chunking in Level 2, this scales correctly to genuinely uneven recursive workloads (a tree search, a recursive algorithm with data-dependent branch costs) without any hand-tuned chunk sizing.

## 6. Walkthrough

Tracing `RecursiveWorkStealingSum.main`'s call to `pool.invoke(new SumTask(0, 20_000_000))`:

1. `pool.invoke(...)` submits the top-level `SumTask` and blocks the calling thread until it fully completes, returning the final `Long` sum.
2. Inside `compute()`, since `20,000,000 - 0` far exceeds `THRESHOLD` (10,000), the task splits: `mid = 10,000,000`, creating `left = SumTask(0, 10_000_000)` and `right = SumTask(10_000_000, 20_000_000)`.
3. `left.fork()` schedules `left` to run asynchronously — it's pushed onto the *current* worker thread's own local deque, available for that same thread to resume later, or for an idle *different* worker thread to steal from the opposite end.
4. The current thread does **not** wait idly for `left` — it immediately calls `right.compute()` directly, recursively repeating this same split-and-fork process on the right half, keeping itself productively busy the whole time.
5. Each recursive split continues until a task's range is small enough (`<= THRESHOLD`), at which point `compute()` just sums that small range directly and returns — this is the base case that actually does real work.
6. Meanwhile, if the pool has multiple worker threads (matching available cores), any thread that finishes its own local work early can steal a still-pending forked task from another busy thread's deque — since the recursive splitting produces many small, independent tasks, there's ample opportunity for this rebalancing to happen automatically, without any code explicitly managing it.
7. Once `right.compute()` returns its half's sum, `left.join()` retrieves the result of the forked left half — if it hasn't finished yet, the calling thread can itself help execute pending tasks (including, potentially, subtasks of `left` or others) while waiting, rather than blocking uselessly.
8. The two halves' sums are added and returned up through each level of the recursive call stack, eventually producing the single, correct total sum back at the top-level `invoke()` call.

## 7. Gotchas & takeaways

> **Gotcha:** `ForkJoinPool` (and its `RecursiveTask`/`RecursiveAction` model) is built for CPU-bound, splittable computation — using it for blocking I/O work defeats the point of work-stealing, since a worker thread genuinely blocked on I/O (not cooperatively yielding via `fork`/`join`) can't be usefully "stolen from," and can even reduce the pool's effective parallelism below its configured thread count.

- Work-stealing lets idle threads pull tasks from busy threads' deques, automatically balancing load across genuinely uneven recursive workloads without manual chunk-size tuning.
- Split down to a sensible threshold (not too fine — task overhead dominates; not too coarse — load balancing opportunities shrink) — 1,000 to 10,000+ elements per leaf task is a common starting range, tuned by measurement.
- `fork()` schedules a subtask asynchronously (potentially stealable); computing the "other half" directly on the current thread, then `join()`-ing the forked half, is the standard pattern that keeps the current thread productively busy rather than idly waiting.
- `ForkJoinPool` is what powers Java's parallel streams (`.parallelStream()`) internally — understanding fork/join mechanics helps explain parallel streams' performance characteristics and pitfalls.
- Avoid blocking calls (I/O, `Thread.sleep`, lock acquisition on contended locks) inside `RecursiveTask.compute()` — see [`RecursiveTask`/`RecursiveAction`](0884-recursivetask-recursiveaction.md) and the [common pool](0885-common-pool.md) tutorials for how this interacts with shared pool usage.
