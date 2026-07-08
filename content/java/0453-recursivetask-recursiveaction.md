---
card: java
gi: 453
slug: recursivetask-recursiveaction
title: RecursiveTask / RecursiveAction
---

## 1. What it is

`RecursiveTask<V>` and `RecursiveAction`, added in Java 7 alongside `ForkJoinPool`, are the base classes for writing divide-and-conquer parallel algorithms: override `compute()` to either return a value (`RecursiveTask<V>`) or perform work with no return value (`RecursiveAction`). Inside `compute()`, a task checks whether its chunk of work is small enough to handle directly; if not, it splits into smaller subtasks, `fork()`s some of them to run asynchronously, computes others directly, and `join()`s the forked ones to combine results.

## 2. Why & when

Splitting a large recursive computation (summing a huge array, sorting, searching a tree) across multiple threads by hand — manually managing which thread does what, and how partial results combine back together — is exactly the kind of bookkeeping that's easy to get wrong and tedious to write correctly every time. `RecursiveTask`/`RecursiveAction` give a structured template for exactly this pattern: check a size threshold, split if too large, fork one half to run concurrently while computing the other half directly, then join and combine. Running on a `ForkJoinPool`'s work-stealing scheduler (the previous tutorial) means idle worker threads automatically pick up whichever subtasks are ready, without you managing thread assignment yourself.

You reach for these any time a problem naturally decomposes into "split into two roughly-equal halves, solve each, combine" — summing or transforming large arrays, parallel sorting, or tree/graph traversal where independent subtrees can be processed concurrently.

## 3. Core concept

```java
import java.util.concurrent.*;

class SumTask extends RecursiveTask<Long> {
    int[] array; int start, end;
    // ... constructor ...

    @Override
    protected Long compute() {
        if (end - start <= THRESHOLD) {
            long sum = 0;
            for (int i = start; i < end; i++) sum += array[i]; // small enough: just do it directly
            return sum;
        }
        int mid = (start + end) / 2;
        SumTask left = new SumTask(array, start, mid);
        SumTask right = new SumTask(array, mid, end);
        left.fork();                          // run left half ASYNCHRONOUSLY on another worker
        long rightResult = right.compute();   // compute right half on THIS thread, right now
        return left.join() + rightResult;     // wait for left, then combine both halves
    }
}

long total = ForkJoinPool.commonPool().invoke(new SumTask(data, 0, data.length));
```

The `THRESHOLD` check is essential: splitting all the way down to individual elements would create far more tasks than useful, since each task has real overhead — the threshold decides the cutoff where "just compute it directly" beats "keep splitting."

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A RecursiveTask splits a large range into two halves once it exceeds a size threshold, forking one half to run concurrently while computing the other directly, then joins and combines both results">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <rect x="230" y="20" width="180" height="34" rx="6" fill="#1c2430" stroke="#e6edf3"/><text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">whole range: [0, 5000)</text>

  <rect x="60" y="80" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="150" y="102" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">left.fork() -&gt; async</text>
  <rect x="400" y="80" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="490" y="102" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">right.compute() -&gt; here</text>

  <line x1="320" y1="54" x2="150" y2="78" stroke="#8b949e" marker-end="url(art1)"/>
  <line x1="320" y1="54" x2="490" y2="78" stroke="#8b949e" marker-end="url(art1)"/>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">left.join() waits for the async half, then results are combined: leftSum + rightSum</text>
  <defs><marker id="art1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One half runs concurrently (forked); the other runs on the current thread directly — both eventually joined together.

## 5. Runnable example

Scenario: processing a large array in two ways — doubling every element in place, and summing the result — the same array, evolved from a `RecursiveAction` that doubles values with no return value, through a `RecursiveTask<Long>` that computes and returns a sum, to combining both operations on a custom-sized pool and verifying the parallel result against a sequential baseline.

### Level 1 — Basic

```java
import java.util.concurrent.*;
import java.util.Arrays;

public class DoubleArrayAction extends RecursiveAction {
    static final int THRESHOLD = 1000;
    final int[] array;
    final int start, end;

    DoubleArrayAction(int[] array, int start, int end) {
        this.array = array; this.start = start; this.end = end;
    }

    @Override
    protected void compute() {
        if (end - start <= THRESHOLD) {
            for (int i = start; i < end; i++) array[i] *= 2; // small enough: just do it directly
            return;
        }
        int mid = (start + end) / 2;
        DoubleArrayAction left = new DoubleArrayAction(array, start, mid);
        DoubleArrayAction right = new DoubleArrayAction(array, mid, end);
        invokeAll(left, right); // fork both halves and wait for both to finish
    }

    public static void main(String[] args) {
        int[] data = new int[5000];
        Arrays.fill(data, 1);

        ForkJoinPool.commonPool().invoke(new DoubleArrayAction(data, 0, data.length));

        System.out.println("First 5 values: " + Arrays.toString(Arrays.copyOf(data, 5)));
        System.out.println("All doubled correctly: " + Arrays.stream(data).allMatch(v -> v == 2));
    }
}
```

**How to run:** `java DoubleArrayAction.java`

`RecursiveAction` has no return value — `compute()` returns `void`. `invokeAll(left, right)` is a convenience method that forks *both* subtasks and waits for both to complete, a clean shorthand for the common "split into exactly two, run both, wait for both" case where you don't need to combine any results.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.Arrays;

public class SumArrayTask extends RecursiveTask<Long> {
    static final int THRESHOLD = 1000;
    final int[] array;
    final int start, end;

    SumArrayTask(int[] array, int start, int end) {
        this.array = array; this.start = start; this.end = end;
    }

    @Override
    protected Long compute() {
        if (end - start <= THRESHOLD) {
            long sum = 0;
            for (int i = start; i < end; i++) sum += array[i];
            return sum;
        }
        int mid = (start + end) / 2;
        SumArrayTask left = new SumArrayTask(array, start, mid);
        SumArrayTask right = new SumArrayTask(array, mid, end);
        left.fork();               // run left half asynchronously
        long rightResult = right.compute(); // compute right half on THIS thread
        long leftResult = left.join();       // wait for the forked left half, then combine
        return leftResult + rightResult;
    }

    public static void main(String[] args) {
        int[] data = new int[5000];
        Arrays.fill(data, 1);

        long total = ForkJoinPool.commonPool().invoke(new SumArrayTask(data, 0, data.length));
        System.out.println("Sum of 5000 ones: " + total);
    }
}
```

**How to run:** `java SumArrayTask.java`

`RecursiveTask<Long>`'s `compute()` returns an actual value. The `left.fork(); ... right.compute(); ... left.join()` pattern (rather than `invokeAll`) is the classic idiom for exactly-two-way splits that need to combine results: fork one half to run elsewhere, compute the other half directly on the current thread (avoiding wasting the current thread by having it just wait), then join the forked half once you need its result.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.Arrays;

public class ParallelPipeline {
    static final int THRESHOLD = 2000;

    static class DoubleAction extends RecursiveAction {
        final int[] array; final int start, end;
        DoubleAction(int[] array, int start, int end) { this.array = array; this.start = start; this.end = end; }
        @Override protected void compute() {
            if (end - start <= THRESHOLD) {
                for (int i = start; i < end; i++) array[i] *= 2;
                return;
            }
            int mid = (start + end) / 2;
            invokeAll(new DoubleAction(array, start, mid), new DoubleAction(array, mid, end));
        }
    }

    static class SumTask extends RecursiveTask<Long> {
        final int[] array; final int start, end;
        SumTask(int[] array, int start, int end) { this.array = array; this.start = start; this.end = end; }
        @Override protected Long compute() {
            if (end - start <= THRESHOLD) {
                long sum = 0;
                for (int i = start; i < end; i++) sum += array[i];
                return sum;
            }
            int mid = (start + end) / 2;
            SumTask left = new SumTask(array, start, mid);
            SumTask right = new SumTask(array, mid, end);
            left.fork();
            long rightResult = right.compute();
            return left.join() + rightResult;
        }
    }

    public static void main(String[] args) {
        int size = 20_000;
        int[] data = new int[size];
        for (int i = 0; i < size; i++) data[i] = i % 7; // varied, non-trivial values

        // Sequential baseline for verification
        long sequentialSum = 0;
        for (int v : data) sequentialSum += v * 2L;

        ForkJoinPool customPool = new ForkJoinPool(4);
        customPool.invoke(new DoubleAction(data, 0, data.length));
        long parallelSum = customPool.invoke(new SumTask(data, 0, data.length));
        customPool.shutdown();

        System.out.println("Sequential baseline: " + sequentialSum);
        System.out.println("Parallel result: " + parallelSum);
        System.out.println("Results match: " + (sequentialSum == parallelSum));
    }
}
```

**How to run:** `java ParallelPipeline.java`

Both operations (doubling, then summing) run on the same custom, fixed-size `ForkJoinPool`, and the parallel result is checked against a straightforward sequential computation over the original data — a standard, worthwhile practice whenever introducing parallelism, since a correctness bug in a fork/join task (an off-by-one in the split boundary, a missed combine step) can easily produce a subtly wrong result that's hard to spot without an independent check.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `data` is a 20,000-element array where `data[i] = i % 7` — varied, non-trivial values (not all the same, unlike the earlier examples' array of all-ones). `sequentialSum` is computed with a plain loop: `sum += v * 2L` for every element — this establishes the expected final answer independently of any parallel logic.

`customPool.invoke(new DoubleAction(data, 0, data.length))` starts the doubling phase. `DoubleAction.compute()` checks if its range (`20000` elements) exceeds `THRESHOLD` (`2000`) — it does, so it splits at the midpoint and calls `invokeAll` on both halves; each half recursively does the same check, continuing to split until a sub-range is at or below 2000 elements, at which point it directly doubles every value in that sub-range in place. Once `invoke` returns, every element of `data` has been doubled — `data[i]` is now `(i % 7) * 2`.

`customPool.invoke(new SumTask(data, 0, data.length))` starts the summing phase, using the *already-doubled* `data`. Following the same split-and-recurse pattern (but with `SumTask`'s `fork`/`compute`/`join` combine logic rather than `invokeAll`), it eventually sums all the small sub-ranges and combines them back up through nested `leftResult + rightResult` additions, producing `parallelSum` — the sum of every doubled element.

Since doubling every element and then summing is mathematically the same as summing the original values and then doubling the total (`sum(2 * x_i) == 2 * sum(x_i)`), `parallelSum` should exactly equal `sequentialSum`, which was computed as `sum(v * 2)` directly from the original (pre-doubling) values. The final `System.out.println("Results match: ...")` confirms this.

Expected output:
```
Sequential baseline: 119994
Parallel result: 119994
Results match: true
```

## 7. Gotchas & takeaways

> Never call `compute()` directly on a task object as an ordinary method call from outside the fork/join framework's own recursive structure, and never mix `fork()`/`join()` calls with blocking I/O or long external waits inside `compute()` — fork/join tasks are meant to be short-lived, CPU-bound units of work; blocking one for an extended, unrelated reason can starve the whole pool's limited worker thread count, since work-stealing assumes workers are usually busy computing, not waiting on something external.

- `RecursiveAction` (`compute()` returns `void`) and `RecursiveTask<V>` (`compute()` returns `V`) are the two base classes for fork/join divide-and-conquer algorithms.
- The size threshold at which a task stops splitting and just computes directly is a critical tuning parameter — too low creates excessive task overhead, too high loses potential parallelism; there's no universal "right" value, it depends on the workload.
- `fork()` schedules a subtask to run asynchronously (potentially stolen by another worker); `join()` blocks until that forked subtask completes and returns its result; `invokeAll(a, b)` is a convenient shorthand for forking multiple subtasks and waiting for all of them.
- The classic two-way-split idiom is `left.fork(); rightResult = right.compute(); leftResult = left.join();` — computing the right half directly on the current thread (rather than also forking it) avoids wasting that thread just waiting.
- Verifying a parallel computation's result against an independent sequential baseline is a valuable habit, since subtle bugs in split/combine logic can silently produce a wrong (but plausible-looking) answer.
