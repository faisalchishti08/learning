---
card: java
gi: 884
slug: recursivetask-recursiveaction
title: RecursiveTask / RecursiveAction
---

## 1. What it is

`RecursiveTask<V>` and `RecursiveAction` are the two base classes for writing fork/join computations to run on a `ForkJoinPool`. Both require implementing a single method, `compute()`, containing the "if small enough, solve directly; otherwise, split and recurse" logic. `RecursiveTask<V>` is for computations that **produce a result** — `compute()` returns a `V` (summing an array, finding a maximum, merging sorted halves). `RecursiveAction` is for computations that **produce no result**, just a side effect — `compute()` returns `void` (recursively sorting an array in place, applying a transformation to each element in a range).

## 2. Why & when

Use `RecursiveTask<V>` whenever the divide-and-conquer algorithm needs to combine subresults into a final answer — this is the more common case, covering searching, aggregating, and reducing. Use `RecursiveAction` when the recursive work only mutates shared state or performs side effects with nothing to return — an in-place parallel sort, or applying a function to every element of an array segment. Both share the same fork/join discipline: pick a **threshold** below which the work is cheap enough to just do directly (avoiding the overhead of creating and scheduling more tasks than necessary), and above the threshold, split into (typically two) roughly equal subtasks, `fork()` one, `compute()` (or recurse into) the other directly on the current thread, then `join()` the forked one — see [`ForkJoinPool` & work-stealing](0883-forkjoinpool-work-stealing.md) for why this specific pattern (fork one, compute the other directly) is what keeps the calling thread productively busy instead of idling.

## 3. Core concept

```java
class MaxTask extends RecursiveTask<Integer> {
    final int[] arr; final int from, to;
    MaxTask(int[] arr, int from, int to) { this.arr = arr; this.from = from; this.to = to; }
    static final int THRESHOLD = 1000;

    protected Integer compute() {
        if (to - from <= THRESHOLD) {
            int max = Integer.MIN_VALUE;
            for (int i = from; i < to; i++) max = Math.max(max, arr[i]);
            return max; // base case -- solve directly, produces a VALUE
        }
        int mid = (from + to) / 2;
        MaxTask left = new MaxTask(arr, from, mid);
        left.fork();
        int rightMax = new MaxTask(arr, mid, to).compute();
        int leftMax = left.join();
        return Math.max(leftMax, rightMax); // combine subresults
    }
}

class DoubleAction extends RecursiveAction {
    final int[] arr; final int from, to;
    DoubleAction(int[] arr, int from, int to) { this.arr = arr; this.from = from; this.to = to; }
    static final int THRESHOLD = 1000;

    protected void compute() {
        if (to - from <= THRESHOLD) {
            for (int i = from; i < to; i++) arr[i] *= 2; // base case -- mutate in place, no return value
            return;
        }
        int mid = (from + to) / 2;
        DoubleAction left = new DoubleAction(arr, from, mid);
        left.fork();
        new DoubleAction(arr, mid, to).compute();
        left.join();
    }
}
```

Both classes share the identical split/fork/join skeleton; the only difference is whether `compute()` returns a combinable value (`RecursiveTask<V>`) or just performs a side effect (`RecursiveAction`).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A recursive task tree splitting until reaching a base-case threshold, then combining results back up for RecursiveTask, or just completing side effects for RecursiveAction">
  <rect x="260" y="15" width="120" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="35" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">whole range</text>

  <rect x="140" y="70" width="120" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="200" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">left half</text>
  <rect x="380" y="70" width="120" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="440" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">right half</text>

  <rect x="80" y="125" width="90" height="28" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="125" y="144" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">base case</text>
  <rect x="230" y="125" width="90" height="28" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="275" y="144" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">base case</text>
  <rect x="320" y="125" width="90" height="28" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="365" y="144" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">base case</text>
  <rect x="470" y="125" width="90" height="28" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="515" y="144" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">base case</text>

  <text x="320" y="180" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">RecursiveTask: results flow back UP and combine. RecursiveAction: no results, just side effects.</text>
</svg>

*The split-and-recurse structure is identical for both; only whether values flow back up (`RecursiveTask`) or not (`RecursiveAction`) differs.*

## 5. Runnable example

Scenario: finding the maximum value in a large array, growing from a sequential scan, to a `RecursiveTask<Integer>` fork/join version, to a combined pipeline that first uses a `RecursiveAction` to transform the array in place, then a `RecursiveTask` to find the max of the transformed data.

### Level 1 — Basic

```java
public class SequentialMax {
    public static void main(String[] args) {
        int size = 10_000_000;
        int[] data = new int[size];
        for (int i = 0; i < size; i++) data[i] = (i * 37) % 1_000_003;

        int max = Integer.MIN_VALUE;
        for (int v : data) max = Math.max(max, v); // single-threaded scan
        System.out.println("max = " + max);
    }
}
```

**How to run:** `java SequentialMax.java` (JDK 17+).

Expected output shape (exact value depends on the data-generation formula, but is deterministic):
```
max = 1000001
```

Correct, but single-threaded — the scan uses only one core regardless of how many are available.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class RecursiveTaskMax {
    static class MaxTask extends RecursiveTask<Integer> {
        final int[] arr; final int from, to;
        static final int THRESHOLD = 50_000;

        MaxTask(int[] arr, int from, int to) { this.arr = arr; this.from = from; this.to = to; }

        @Override
        protected Integer compute() {
            if (to - from <= THRESHOLD) {
                int max = Integer.MIN_VALUE;
                for (int i = from; i < to; i++) max = Math.max(max, arr[i]);
                return max;
            }
            int mid = (from + to) / 2;
            MaxTask left = new MaxTask(arr, from, mid);
            left.fork();
            int rightMax = new MaxTask(arr, mid, to).compute();
            int leftMax = left.join();
            return Math.max(leftMax, rightMax);
        }
    }

    public static void main(String[] args) {
        int size = 10_000_000;
        int[] data = new int[size];
        for (int i = 0; i < size; i++) data[i] = (i * 37) % 1_000_003;

        ForkJoinPool pool = new ForkJoinPool();
        int max = pool.invoke(new MaxTask(data, 0, size));
        System.out.println("max = " + max + " (computed via parallel RecursiveTask)");
        pool.shutdown();
    }
}
```

**How to run:** `java RecursiveTaskMax.java`.

Expected output:
```
max = 1000001 (computed via parallel RecursiveTask)
```

The real-world concern added: the same computation now splits recursively across all available cores via `ForkJoinPool`, using `RecursiveTask<Integer>` to combine each subtree's local maximum into the overall result — correctness is identical to the sequential version, but the work is spread across cores.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.Arrays;

public class ActionThenTaskPipeline {
    // RecursiveAction: doubles every element in place, no return value
    static class DoubleAction extends RecursiveAction {
        final int[] arr; final int from, to;
        static final int THRESHOLD = 50_000;

        DoubleAction(int[] arr, int from, int to) { this.arr = arr; this.from = from; this.to = to; }

        @Override
        protected void compute() {
            if (to - from <= THRESHOLD) {
                for (int i = from; i < to; i++) arr[i] = arr[i] * 2;
                return;
            }
            int mid = (from + to) / 2;
            DoubleAction left = new DoubleAction(arr, from, mid);
            left.fork();
            new DoubleAction(arr, mid, to).compute();
            left.join();
        }
    }

    // RecursiveTask: finds the max, returning a VALUE
    static class MaxTask extends RecursiveTask<Integer> {
        final int[] arr; final int from, to;
        static final int THRESHOLD = 50_000;

        MaxTask(int[] arr, int from, int to) { this.arr = arr; this.from = from; this.to = to; }

        @Override
        protected Integer compute() {
            if (to - from <= THRESHOLD) {
                int max = Integer.MIN_VALUE;
                for (int i = from; i < to; i++) max = Math.max(max, arr[i]);
                return max;
            }
            int mid = (from + to) / 2;
            MaxTask left = new MaxTask(arr, from, mid);
            left.fork();
            int rightMax = new MaxTask(arr, mid, to).compute();
            int leftMax = left.join();
            return Math.max(leftMax, rightMax);
        }
    }

    public static void main(String[] args) {
        int size = 10_000_000;
        int[] data = new int[size];
        for (int i = 0; i < size; i++) data[i] = (i * 37) % 1_000_003;
        int originalMax = Arrays.stream(data).max().getAsInt();

        ForkJoinPool pool = new ForkJoinPool();

        // Step 1: mutate in place via RecursiveAction -- no result to combine, just a side effect
        pool.invoke(new DoubleAction(data, 0, size));

        // Step 2: find the max of the NOW-DOUBLED array via RecursiveTask -- produces a value
        int doubledMax = pool.invoke(new MaxTask(data, 0, size));

        System.out.println("original max: " + originalMax);
        System.out.println("doubled max: " + doubledMax + " (expected exactly 2x original)");
        pool.shutdown();
    }
}
```

**How to run:** `java ActionThenTaskPipeline.java`.

Expected output:
```
original max: 1000001
doubled max: 2000002 (expected exactly 2x original)
```

This adds the production-flavored hard case: composing a `RecursiveAction` (mutate the array in place, no return value) and a `RecursiveTask` (compute a result from the now-mutated data) as two sequential fork/join phases on the same underlying array — demonstrating that both base classes coexist naturally in a real pipeline, each used for the kind of work it's actually suited to, sharing the same pool and the same split/fork/join discipline.

## 6. Walkthrough

Tracing `ActionThenTaskPipeline.main`:

1. `pool.invoke(new DoubleAction(data, 0, size))` starts the first phase: the top-level `DoubleAction` checks `size - 0 > THRESHOLD`, splits into two halves, forks the left half, and recursively computes the right half directly on the calling thread — this repeats down to base cases of at most `THRESHOLD` elements each, where the loop `arr[i] = arr[i] * 2` actually mutates the shared `data` array in place.
2. Because `RecursiveAction.compute()` returns `void`, there's nothing to combine on the way back up — each `join()` call simply waits for its forked sibling to finish mutating its portion of the array, with no result value to merge.
3. `pool.invoke(...)` for the `DoubleAction` blocks `main` until every recursive subtask has completed its portion of the doubling, guaranteeing the entire `data` array is fully doubled before phase one returns.
4. `pool.invoke(new MaxTask(data, 0, size))` starts the second phase on the *same*, now-doubled `data` array — this time using `RecursiveTask<Integer>`, so each base case computes a local maximum over its small range and *returns* it, and each combining step (`Math.max(leftMax, rightMax)`) merges two subresults into one, all the way back up to a single overall maximum.
5. Because every element was doubled in phase one before phase two ever begins, the maximum found in phase two is guaranteed to be exactly twice the maximum that existed in the original, undoubled array — `main`'s final comparison (`originalMax` computed once via a simple sequential stream, `doubledMax` computed via the parallel `MaxTask`) confirms this relationship holds exactly.
6. Both phases reuse the *same* `ForkJoinPool` instance, demonstrating that a single pool can host multiple, sequentially-run fork/join computations, whether they return a value or just perform side effects.

## 7. Gotchas & takeaways

> **Gotcha:** always call `fork()` on one subtask and `compute()` **directly** (not `fork()` then `join()` immediately) on the other — forking *both* halves and then joining both wastes the opportunity to keep the current thread doing useful work itself; it should always compute one half inline while its sibling potentially runs (or gets stolen) elsewhere.

- `RecursiveTask<V>` returns a combinable value from `compute()`; `RecursiveAction` returns nothing, just performs a side effect — pick based on whether your algorithm needs to merge subresults.
- Both follow the identical discipline: below a chosen threshold, solve directly (base case); above it, split, `fork()` one half, `compute()` the other directly, then `join()` the forked half.
- Choosing the threshold is a tuning decision — too small and per-task overhead dominates; too large and you lose parallelism and work-stealing's ability to rebalance uneven workloads; profile with your actual data size and hardware.
- Multiple independent fork/join computations (a `RecursiveAction` phase followed by a `RecursiveTask` phase, as shown above) can share the same `ForkJoinPool` instance sequentially, each `invoke()` call blocking until that phase fully completes before the next begins.
- Never perform blocking I/O or wait on unrelated locks inside `compute()` — see the [`ForkJoinPool` & work-stealing](0883-forkjoinpool-work-stealing.md) tutorial for why this undermines the fork/join model's efficiency, and understand how these tasks interact with the shared JVM-wide [common pool](0885-common-pool.md) when no explicit pool is provided.
