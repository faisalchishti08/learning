---
card: java
gi: 780
slug: vector-api-8th-incubator
title: Vector API (8th incubator)
---

## 1. What it is

**Java 23** (JEP 469) is the **eighth incubator** round of the [Vector API](0770-vector-api-7th-incubator.md), continuing to refine `jdk.incubator.vector`. The core programming model — `VectorSpecies`, lane-based SIMD operations, masks, fused multiply-add, horizontal reductions, and off-heap `MemorySegment` load/store — remains stable and unchanged. This round updates the API's integration story to track this same release's other in-flight concurrency previews: [structured concurrency's third preview](0777-structured-concurrency-3rd-preview.md), which redesigned `StructuredTaskScope` around `Joiner` and `open(...)`, and [scoped values' third preview](0778-scoped-values-3rd-preview.md) — confirming vectorized numeric work continues to compose cleanly with both, even as their surrounding APIs keep evolving underneath it.

## 2. Why & when

An incubating API that gets used alongside other, still-changing previewing APIs has to keep re-proving compatibility every time one of those neighbors reshapes its surface — and Java 23 is a release where that neighbor reshaped significantly: `StructuredTaskScope.ShutdownOnFailure`/`ShutdownOnSuccess` subclassing was replaced by `StructuredTaskScope.open(Joiner)`. Code that fans a large numeric workload out across structured-concurrency subtasks, with each subtask internally using vectorized SIMD operations on its slice, needs to migrate its fork/join code to the new `Joiner`-based shape — but the vectorized inner loop inside each subtask needs no changes at all, since the Vector API and the concurrency layer around it remain orthogonal, composable pieces. This round is exactly that: confirming (and demonstrating) that the same "structured concurrency for task-level fan-out, Vector API for data-level parallelism within each task" pattern from the seventh incubator still holds, now expressed through Java 23's redesigned concurrency API.

## 3. Core concept

```java
import jdk.incubator.vector.*;
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;

static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;

static double sumChunk(double[] data, int start, int end) {
    DoubleVector acc = DoubleVector.zero(SPECIES);
    int i = start;
    int bound = start + SPECIES.loopBound(end - start);
    for (; i < bound; i += SPECIES.length()) {
        acc = acc.add(DoubleVector.fromArray(SPECIES, data, i));
    }
    double total = acc.reduceLanes(VectorOperators.ADD);
    for (; i < end; i++) total += data[i];
    return total;
}

try (var scope = StructuredTaskScope.open(Joiner.<Double>awaitAllSuccessfulOrThrow())) {
    var subtask = scope.fork(() -> sumChunk(data, 0, data.length / 2));
    // ... more forks, then scope.join() ...
}
```

`sumChunk`'s vectorized body is identical to the seventh incubator's version — only the surrounding `StructuredTaskScope` construction changed, to Java 23's `open(Joiner)` shape.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The vectorized per-chunk summing logic is unchanged from the previous incubator round; only the surrounding structured concurrency API used to fan work out across chunks was redesigned in Java 23">
  <rect x="20" y="20" width="280" height="50" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="160" y="50" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">sumChunk(...) — vectorized, unchanged</text>

  <rect x="340" y="20" width="280" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">StructuredTaskScope.open(Joiner) — new in Java 23</text>

  <text x="320" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The Vector API and the concurrency API around it evolve independently</text>

  <rect x="120" y="120" width="400" height="40" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="320" y="145" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Both layers still compose correctly together</text>
</svg>

*A stable, incubating numeric API riding on top of an evolving, previewing concurrency API — with a clean seam between the two.*

## 5. Runnable example

Scenario: summing a very large array across concurrently vectorized chunks, migrated to Java 23's redesigned structured concurrency API, then extended with a custom `Joiner` that reports partial progress as chunks complete.

### Level 1 — Basic

```java
import jdk.incubator.vector.*;

public class VectorSumEighthBasic {
    static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;

    static double sum(double[] data) {
        DoubleVector acc = DoubleVector.zero(SPECIES);
        int i = 0;
        int bound = SPECIES.loopBound(data.length);
        for (; i < bound; i += SPECIES.length()) {
            acc = acc.add(DoubleVector.fromArray(SPECIES, data, i));
        }
        double total = acc.reduceLanes(VectorOperators.ADD);
        for (; i < data.length; i++) total += data[i];
        return total;
    }

    public static void main(String[] args) {
        double[] data = new double[1_000_000];
        for (int i = 0; i < data.length; i++) data[i] = 1.0;
        System.out.println("sum: " + sum(data));
    }
}
```

**How to run:** `java --add-modules jdk.incubator.vector VectorSumEighthBasic.java` (JDK 23+).

The unchanged single-threaded vectorized baseline — identical in shape to the seventh incubator's version, since the Vector API itself has no new capability this round.

### Level 2 — Intermediate

```java
import jdk.incubator.vector.*;
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;
import java.util.concurrent.StructuredTaskScope.Subtask;
import java.util.*;

public class VectorSumOpenJoiner {
    static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;

    static double sumChunk(double[] data, int start, int end) {
        DoubleVector acc = DoubleVector.zero(SPECIES);
        int i = start;
        int bound = start + SPECIES.loopBound(end - start);
        for (; i < bound; i += SPECIES.length()) {
            acc = acc.add(DoubleVector.fromArray(SPECIES, data, i));
        }
        double total = acc.reduceLanes(VectorOperators.ADD);
        for (; i < end; i++) total += data[i];
        return total;
    }

    public static void main(String[] args) throws Exception {
        double[] data = new double[8_000_000];
        for (int i = 0; i < data.length; i++) data[i] = 1.0;

        int chunkCount = 4;
        int chunkSize = data.length / chunkCount;

        try (var scope = StructuredTaskScope.open(Joiner.<Double>awaitAllSuccessfulOrThrow())) {
            List<Subtask<Double>> subtasks = new ArrayList<>();
            for (int c = 0; c < chunkCount; c++) {
                int start = c * chunkSize;
                int end = (c == chunkCount - 1) ? data.length : start + chunkSize;
                subtasks.add(scope.fork(() -> sumChunk(data, start, end)));
            }
            scope.join();

            double total = 0;
            for (var subtask : subtasks) total += subtask.get();
            System.out.println("total: " + total);
        }
    }
}
```

**How to run:** `java --add-modules jdk.incubator.vector --enable-preview --source 23 VectorSumOpenJoiner.java`.

The real-world concern added: the fan-out is expressed through Java 23's redesigned `StructuredTaskScope.open(Joiner.awaitAllSuccessfulOrThrow())` instead of `new ShutdownOnFailure()` — `sumChunk`'s vectorized body needed zero changes to migrate; only the scope construction and `scope.fork(...)`'s return type (`Subtask<Double>` instead of a raw `Future`) changed.

### Level 3 — Advanced

```java
import jdk.incubator.vector.*;
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;
import java.util.concurrent.StructuredTaskScope.Subtask;
import java.util.*;

public class VectorSumProgressJoiner {
    static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;

    static double sumChunk(int chunkId, double[] data, int start, int end) {
        DoubleVector acc = DoubleVector.zero(SPECIES);
        int i = start;
        int bound = start + SPECIES.loopBound(end - start);
        for (; i < bound; i += SPECIES.length()) {
            acc = acc.add(DoubleVector.fromArray(SPECIES, data, i));
        }
        double total = acc.reduceLanes(VectorOperators.ADD);
        for (; i < end; i++) total += data[i];
        return total;
    }

    // Custom Joiner: sums results as they arrive and prints progress per chunk.
    static Joiner<Double, Double> progressReportingSum(int totalChunks) {
        return new Joiner<Double, Double>() {
            private double runningTotal = 0;
            private int completed = 0;

            @Override
            public synchronized boolean onComplete(Subtask<? extends Double> subtask) {
                runningTotal += subtask.get();
                completed++;
                System.out.println("progress: " + completed + "/" + totalChunks + ", running total: " + runningTotal);
                return false; // wait for every chunk
            }

            @Override
            public synchronized Double result() { return runningTotal; }
        };
    }

    public static void main(String[] args) throws Exception {
        double[] data = new double[8_000_000];
        for (int i = 0; i < data.length; i++) data[i] = 1.0;

        int chunkCount = 4;
        int chunkSize = data.length / chunkCount;

        try (var scope = StructuredTaskScope.open(progressReportingSum(chunkCount))) {
            for (int c = 0; c < chunkCount; c++) {
                int id = c;
                int start = c * chunkSize;
                int end = (c == chunkCount - 1) ? data.length : start + chunkSize;
                scope.fork(() -> sumChunk(id, data, start, end));
            }
            double total = scope.join();
            System.out.println("final total: " + total);
        }
    }
}
```

**How to run:** `java --add-modules jdk.incubator.vector --enable-preview --source 23 VectorSumProgressJoiner.java`.

This adds the production-flavored hard case: a **custom `Joiner`** that accumulates each vectorized chunk's result as it completes and prints running progress — showing that the new `Joiner` interface's `onComplete` callback composes correctly with subtasks doing genuine SIMD numeric work, and that `scope.join()` itself now directly returns the accumulated value (`Double`) via the joiner's `result()`, rather than requiring the caller to loop over subtasks and sum them manually afterward.

## 6. Walkthrough

Tracing `VectorSumProgressJoiner.main`:

1. `main` builds an 8,000,000-element array of `1.0`s and opens a scope using the custom `progressReportingSum(4)` joiner.
2. Four subtasks are forked, each calling `sumChunk` over a distinct 2,000,000-element quarter of `data` — each subtask's body runs the same vectorized SIMD loop unchanged from the seventh incubator's version.
3. As each subtask finishes (in whatever order the underlying virtual threads happen to complete), the scope invokes the joiner's `onComplete(subtask)`: it adds that subtask's chunk sum (`2,000,000.0`) to `runningTotal`, increments `completed`, and prints a progress line — all inside a `synchronized` block, since `onComplete` can be invoked concurrently by different completing subtasks.
4. Each call to `onComplete` returns `false`, telling the scope this joiner never wants to stop early — it always waits for all four chunks.
5. Once all four subtasks have completed and reported through `onComplete`, `scope.join()` returns, internally calling the joiner's `result()` method, which returns the fully accumulated `runningTotal`.
6. `main` prints the value `scope.join()` returned directly as `"final total"` — no manual loop over subtask results is needed, since the custom joiner already folded them together as they arrived.

Expected output (the four progress lines may interleave in any completion order, but the running total after all four always matches):
```
progress: 1/4, running total: 2000000.0
progress: 2/4, running total: 4000000.0
progress: 3/4, running total: 6000000.0
progress: 4/4, running total: 8000000.0
final total: 8000000.0
```

## 7. Gotchas & takeaways

> **Gotcha:** a custom `Joiner`'s `onComplete` runs concurrently as different subtasks finish — mutating shared state inside it (like `runningTotal` and `completed` above) needs proper synchronization, exactly as with any other concurrently-invoked callback. This has nothing to do with the Vector API itself, but it's an easy trap when migrating fan-out code from the old subclass-based scopes (whose result-collection loop ran safely on a single thread after `join()`) to a custom `Joiner` (whose `onComplete` runs on multiple threads as work completes).

- Eighth incubator round, Java 23 (JEP 469) — still `jdk.incubator.vector`, requiring `--add-modules jdk.incubator.vector`; no new vectorized operations this round.
- Confirms compatibility with [structured concurrency's redesigned `open(Joiner)` API](0777-structured-concurrency-3rd-preview.md) and [scoped values' third preview](0778-scoped-values-3rd-preview.md), both shipping in this same release.
- Migrating vectorized fan-out code from the old scope subclasses to `open(Joiner)` only touches the surrounding concurrency code — the vectorized per-chunk logic itself is unaffected.
- A custom `Joiner` can accumulate subtask results directly (via `onComplete`/`result()`), letting `scope.join()` return the final combined value instead of requiring a manual post-loop over subtasks.
- Still incubating — the numeric API's stability across seven prior rounds makes it low-risk for CPU-bound hot loops today, but it remains subject to change before eventual standardization.
