---
card: java
gi: 770
slug: vector-api-7th-incubator
title: Vector API (7th incubator)
---

## 1. What it is

**Java 22** (JEP 460) is the **seventh incubator** round of the [Vector API](0756-vector-api-6th-incubator.md), continuing to refine `jdk.incubator.vector`. The core programming model — `VectorSpecies`, lane-based operations, masks, fused multiply-add, horizontal reductions, and direct off-heap `MemorySegment` load/store from the sixth round — remains stable. This round's focus is further performance tuning for hardware backends, alongside API refinements that improve how vector computations compose with newly-standardized JDK features shipping in this same release, particularly [structured concurrency](0763-structured-concurrency-2nd-preview.md) and [scoped values](0764-scoped-values-2nd-preview.md), both now in their second preview round.

## 2. Why & when

By the seventh incubator round, the Vector API's fundamentals had been validated across many hardware generations and JDK releases; the ongoing work at this stage is precisely the kind of long-tail refinement expected from any sufficiently important, still-incubating API — continued performance tuning for specific CPU instruction sequences, and closer attention to how vectorized numeric code fits into the broader concurrency story the JDK has been building in parallel (virtual threads, structured concurrency, scoped values). A common real shape this refinement targets: a data-processing pipeline that fans out large numeric workloads across many virtual-thread-backed subtasks via structured concurrency, with each subtask internally using vectorized SIMD operations for its slice of the work, and shared configuration or context propagated via scoped values — this round's incubator feedback specifically covers making that combination work smoothly, rather than requiring workarounds where the pieces don't quite compose. For application developers, the practical guidance remains the same as prior incubator rounds: genuinely useful for CPU-bound numeric hot loops today, still incubating and thus subject to change before eventual standardization.

## 3. Core concept

```java
import jdk.incubator.vector.*;
import java.util.concurrent.StructuredTaskScope;

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
```

Combined with a `StructuredTaskScope` fanning out `sumChunk` calls across several chunks of a large array, this is the concrete "vectorized computation plus structured concurrency" pattern this round's refinements target.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Structured concurrency fans out across chunks of data, with each forked subtask internally using vectorized SIMD operations to process its chunk" >
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">StructuredTaskScope forks one subtask per data chunk</text>

  <rect x="20" y="90" width="180" height="50" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="110" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">subtask 1</text>
  <text x="110" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">vectorized sumChunk</text>

  <rect x="230" y="90" width="180" height="50" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="320" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">subtask 2</text>
  <text x="320" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">vectorized sumChunk</text>

  <rect x="440" y="90" width="180" height="50" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="530" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">subtask 3</text>
  <text x="530" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">vectorized sumChunk</text>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Concurrency for fan-out, SIMD for the per-chunk numeric work — two orthogonal kinds of parallelism</text>
</svg>

*Structured concurrency handles task-level fan-out; the Vector API handles data-level parallelism within each task.*

## 5. Runnable example

Scenario: summing a very large array, growing from a single vectorized pass into a structured-concurrency fan-out where each subtask does its own vectorized work.

### Level 1 — Basic

```java
import jdk.incubator.vector.*;

public class VectorSumBasic {
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

**How to run:** `java --add-modules jdk.incubator.vector VectorSumBasic.java` (JDK 22+).

This is a single-threaded vectorized sum over a 1,000,000-element array — the familiar Vector API pattern, establishing the baseline before adding concurrency.

### Level 2 — Intermediate

```java
import jdk.incubator.vector.*;
import java.util.concurrent.*;
import java.util.*;

public class VectorSumStructured {
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

        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            List<StructuredTaskScope.Subtask<Double>> subtasks = new ArrayList<>();
            for (int c = 0; c < chunkCount; c++) {
                int start = c * chunkSize;
                int end = (c == chunkCount - 1) ? data.length : start + chunkSize;
                subtasks.add(scope.fork(() -> sumChunk(data, start, end)));
            }
            scope.join();
            scope.throwIfFailed();

            double total = 0;
            for (var subtask : subtasks) total += subtask.get();
            System.out.println("total: " + total);
        }
    }
}
```

**How to run:** `java --add-modules jdk.incubator.vector --enable-preview --source 22 VectorSumStructured.java`.

The real-world concern added: the array is split into four chunks, each summed by a **separately forked structured-concurrency subtask**, with each subtask internally still using vectorized SIMD operations for its own slice — combining task-level concurrency (via `StructuredTaskScope`) with data-level parallelism (via the Vector API) as two independent, composable layers.

### Level 3 — Advanced

```java
import jdk.incubator.vector.*;
import java.util.concurrent.*;
import java.util.*;

public class VectorSumWithContext {
    static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;
    static final ScopedValue<String> JOB_ID = ScopedValue.newInstance();

    static double sumChunk(double[] data, int start, int end) {
        DoubleVector acc = DoubleVector.zero(SPECIES);
        int i = start;
        int bound = start + SPECIES.loopBound(end - start);
        for (; i < bound; i += SPECIES.length()) {
            acc = acc.add(DoubleVector.fromArray(SPECIES, data, i));
        }
        double total = acc.reduceLanes(VectorOperators.ADD);
        for (; i < end; i++) total += data[i];
        System.out.println("[" + JOB_ID.get() + "] chunk [" + start + "," + end + ") -> " + total);
        return total;
    }

    static double runJob(String jobId, double[] data, int chunkCount) throws Exception {
        return ScopedValue.where(JOB_ID, jobId).call(() -> {
            int chunkSize = data.length / chunkCount;
            try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
                List<StructuredTaskScope.Subtask<Double>> subtasks = new ArrayList<>();
                for (int c = 0; c < chunkCount; c++) {
                    int start = c * chunkSize;
                    int end = (c == chunkCount - 1) ? data.length : start + chunkSize;
                    subtasks.add(scope.fork(() -> sumChunk(data, start, end)));
                }
                scope.join();
                scope.throwIfFailed();

                double total = 0;
                for (var subtask : subtasks) total += subtask.get();
                return total;
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
    }

    public static void main(String[] args) throws Exception {
        double[] data = new double[4_000_000];
        for (int i = 0; i < data.length; i++) data[i] = 2.0;

        double total = runJob("job-42", data, 4);
        System.out.println("job-42 total: " + total);
    }
}
```

**How to run:** `java --add-modules jdk.incubator.vector --enable-preview --source 22 VectorSumWithContext.java`.

This adds the production-flavored hard case: a **scoped value (`JOB_ID`)** bound once in `runJob`, visible inside every vectorized `sumChunk` call even though each runs as a separately forked structured-concurrency subtask — demonstrating the exact three-way combination this round's refinements targeted: task fan-out via `StructuredTaskScope`, per-chunk data parallelism via the Vector API, and shared context via scoped values, all composing correctly together.

## 6. Walkthrough

Tracing `VectorSumWithContext.main`:

1. `main` builds a 4,000,000-element array filled with `2.0` and calls `runJob("job-42", data, 4)`.
2. `runJob` binds `JOB_ID` to `"job-42"` via `ScopedValue.where(...).call(...)`, then opens a `StructuredTaskScope` and forks four subtasks, each calling `sumChunk` over a distinct quarter of `data`.
3. Each `sumChunk` call — running on its own thread as a forked subtask — reads `JOB_ID.get()`, which correctly returns `"job-42"` because the subtask was forked from within the scoped value's bound dynamic extent, exactly as designed.
4. Each subtask's vectorized loop sums its chunk (each chunk holds 1,000,000 elements all equal to `2.0`, so each chunk's sum is `2,000,000.0`), prints a per-chunk diagnostic line tagged with the job ID, and returns its partial sum.
5. `scope.join()` waits for all four subtasks; `scope.throwIfFailed()` finds no failures. `runJob` collects all four partial sums (`2,000,000.0` each) into `total = 8,000,000.0` and returns it from the scoped-value `call(...)` block.
6. Back in `main`, the returned `total` is printed.

Expected output:
```
[job-42] chunk [0,1000000) -> 2000000.0
[job-42] chunk [1000000,2000000) -> 2000000.0
[job-42] chunk [2000000,3000000) -> 2000000.0
[job-42] chunk [3000000,4000000) -> 2000000.0
job-42 total: 8000000.0
```

(The four chunk lines may print in any interleaving, since the subtasks run concurrently — but each line correctly shows `job-42` as its `JOB_ID`, confirming scoped-value propagation into vectorized, concurrently-forked subtasks works as intended.)

## 7. Gotchas & takeaways

> **Gotcha:** combining the Vector API with structured concurrency introduces **two independent levels of parallelism** — data-level (SIMD lanes within one chunk) and task-level (multiple chunks processed concurrently). Over-splitting into too many small chunks can leave each subtask's per-chunk work too small to amortize the overhead of forking a subtask at all; chunk sizes should be large enough that the vectorized work inside each one dominates the fork/join overhead surrounding it.

- Seventh incubator round, Java 22 — still `jdk.incubator.vector`, requiring `--add-modules jdk.incubator.vector`.
- This round's refinements focus on smoother composition with [structured concurrency](0763-structured-concurrency-2nd-preview.md) and [scoped values](0764-scoped-values-2nd-preview.md), both in their second preview round in this same release.
- Structured concurrency handles fan-out across tasks; the Vector API handles data parallelism within each task — treat them as orthogonal, composable layers, not competing approaches.
- Scoped values propagate correctly into subtasks that themselves perform vectorized computation, letting shared context (job IDs, configuration, tracing data) reach deep into a concurrent, vectorized pipeline.
- Still incubating — expect continued refinement before eventual standardization; chunk your workload generously enough that per-chunk vectorized work dominates fork/join overhead.
