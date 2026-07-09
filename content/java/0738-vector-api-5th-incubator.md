---
card: java
gi: 738
slug: vector-api-5th-incubator
title: Vector API (5th incubator)
---

## 1. What it is

**Java 20** (JEP 438) is the **fifth incubator** round of the [Vector API](0730-vector-api-4th-incubator.md), continuing to refine `jdk.incubator.vector`. The core programming model — `VectorSpecies`, lane-based operations, masks, fused multiply-add, horizontal reductions — remains stable from the fourth incubator round covered in [Java 19](0730-vector-api-4th-incubator.md). This round focuses on further performance work and API refinement for the ARM Scalable Vector Extension (SVE) backend introduced in the previous round, alongside continued bug fixes and small API adjustments gathered from real-world incubator usage across both x86 and ARM targets.

## 2. Why & when

By its fifth incubator round, the Vector API's core abstraction had proven itself across two major hardware families (x86 AVX and ARM NEON/SVE); the remaining work at this stage is the kind of maturing that only comes from sustained real usage — performance tuning for specific instruction sequences the JIT compiler generates, closing gaps in operations exposed only on some hardware backends, and refining edge-case behavior for masked and cross-lane operations. This is a normal, expected part of the JEP incubation and preview process for any sufficiently complex API: rather than finalizing after one or two rounds and living with any remaining rough edges permanently, the platform team continued incubating the Vector API release after release specifically so real-world numeric workloads (machine learning kernels, image processing, scientific computing) could exercise it in practice and report friction before its design was locked in. For an application developer, the practical guidance from this round is the same as prior rounds: it remains a genuinely useful tool for CPU-bound numeric hot loops today, with the caveat that the exact API surface was still not yet finalized and continued to see refinement in subsequent JDK releases.

## 3. Core concept

```java
import jdk.incubator.vector.*;

// The programming model is unchanged from the 4th incubator round (Java 19) —
// this round is about backend maturity and refinement, not new concepts.
static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;

static double[] elementWiseMax(double[] a, double[] b) {
    double[] result = new double[a.length];
    int i = 0;
    int bound = SPECIES.loopBound(a.length);
    for (; i < bound; i += SPECIES.length()) {
        DoubleVector va = DoubleVector.fromArray(SPECIES, a, i);
        DoubleVector vb = DoubleVector.fromArray(SPECIES, b, i);
        va.max(vb).intoArray(result, i);
    }
    for (; i < a.length; i++) result[i] = Math.max(a[i], b[i]);
    return result;
}
```

Continuity of the API across incubator rounds means code written against the fourth round's surface generally continues to work with this fifth round with little or no change.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Successive Vector API incubator rounds add hardware backend maturity and refinement on top of an unchanged core programming model of species, lanes, and vector operations">
  <rect x="20" y="20" width="600" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Stable core: VectorSpecies, lanes, masks, fma, reduceLanes</text>

  <rect x="20" y="90" width="180" height="50" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="110" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">3rd incubator (Java 18)</text>

  <rect x="230" y="90" width="180" height="50" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="320" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">4th incubator (Java 19)</text>
  <text x="320" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ARM SVE backend</text>

  <rect x="440" y="90" width="180" height="50" rx="8" fill="#0f1620" stroke="#3fb950"/>
  <text x="530" y="112" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">5th incubator (Java 20)</text>
  <text x="530" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SVE refinement, tuning</text>
</svg>

Each round refines hardware backend maturity on top of an already-stable core programming model.

## 5. Runnable example

Scenario: normalizing a batch of numeric readings (clamping values into a valid range, then scaling), a common pre-processing step in numeric and machine-learning pipelines. It grows from a scalar clamp-and-scale baseline, to a vectorized version using `min`/`max` lane operations for clamping, to a version processing a full 2D batch of readings with masked handling for a ragged final row — the realistic shape of a small numeric pre-processing kernel.

### Level 1 — Basic

```java
// File: ClampScaleBasic.java
public class ClampScaleBasic {
    static double[] clampAndScale(double[] values, double min, double max, double scale) {
        double[] result = new double[values.length];
        for (int i = 0; i < values.length; i++) {
            double clamped = Math.max(min, Math.min(max, values[i]));
            result[i] = clamped * scale;
        }
        return result;
    }

    public static void main(String[] args) {
        double[] readings = {-5.0, 3.2, 12.8, 7.0, 20.5, 1.1};
        double[] normalized = clampAndScale(readings, 0.0, 10.0, 0.5);
        System.out.println(java.util.Arrays.toString(normalized));
    }
}
```

**How to run:**
```
java ClampScaleBasic.java
```

Expected output:
```
[0.0, 1.6, 5.0, 3.5, 5.0, 0.55]
```

### Level 2 — Intermediate

```java
// File: ClampScaleIntermediate.java
// Run with --add-modules jdk.incubator.vector — incubator module in Java 20.
// The SAME clamp-and-scale operation, vectorized using lane-wise min/max/mul.
import jdk.incubator.vector.*;

public class ClampScaleIntermediate {
    static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;

    static double[] clampAndScale(double[] values, double min, double max, double scale) {
        System.out.println("Lane width on this machine: " + SPECIES.length());
        double[] result = new double[values.length];

        int i = 0;
        int bound = SPECIES.loopBound(values.length);
        for (; i < bound; i += SPECIES.length()) {
            DoubleVector v = DoubleVector.fromArray(SPECIES, values, i);
            DoubleVector clamped = v.min(max).max(min); // lane-wise clamp
            clamped.mul(scale).intoArray(result, i);
        }
        for (; i < values.length; i++) { // scalar tail
            double clamped = Math.max(min, Math.min(max, values[i]));
            result[i] = clamped * scale;
        }
        return result;
    }

    public static void main(String[] args) {
        double[] readings = {-5.0, 3.2, 12.8, 7.0, 20.5, 1.1};
        double[] normalized = clampAndScale(readings, 0.0, 10.0, 0.5);
        System.out.println(java.util.Arrays.toString(normalized));
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.vector ClampScaleIntermediate.java
```

Expected output (lane width varies by CPU):
```
Lane width on this machine: 4
[0.0, 1.6, 5.0, 3.5, 5.0, 0.55]
```

### Level 3 — Advanced

```java
// File: ClampScaleBatchAdvanced.java
// Processes a full 2D batch of readings (rows of possibly ragged length),
// using a masked final block per row instead of a scalar tail loop — the
// production-flavored shape of a small numeric pre-processing kernel
// applied across many independent rows.
import jdk.incubator.vector.*;

public class ClampScaleBatchAdvanced {
    static final VectorSpecies<Double> SPECIES = DoubleVector.SPECIES_PREFERRED;

    static void clampAndScaleInPlace(double[] row, double min, double max, double scale) {
        int i = 0;
        int bound = SPECIES.loopBound(row.length);
        for (; i < bound; i += SPECIES.length()) {
            DoubleVector v = DoubleVector.fromArray(SPECIES, row, i);
            v.min(max).max(min).mul(scale).intoArray(row, i);
        }
        if (i < row.length) {
            VectorMask<Double> mask = SPECIES.indexInRange(i, row.length);
            DoubleVector v = DoubleVector.fromArray(SPECIES, row, i, mask);
            v.min(max).max(min).mul(scale).intoArray(row, i, mask);
        }
    }

    public static void main(String[] args) {
        double[][] batch = {
                {-5.0, 3.2, 12.8, 7.0, 20.5, 1.1, 9.9},
                {2.0, -1.0, 15.0},
                {6.5, 6.5, 6.5, 6.5, 6.5}
        };

        System.out.println("Lane width: " + SPECIES.length());
        for (int row = 0; row < batch.length; row++) {
            clampAndScaleInPlace(batch[row], 0.0, 10.0, 0.5);
            System.out.println("row " + row + ": " + java.util.Arrays.toString(batch[row]));
        }
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.vector ClampScaleBatchAdvanced.java
```

Expected output (lane width varies by CPU; results are deterministic):
```
Lane width: 4
row 0: [0.0, 1.6, 5.0, 3.5, 5.0, 0.55, 5.0]
row 1: [1.0, 0.0, 5.0]
row 2: [3.25, 3.25, 3.25, 3.25, 3.25]
```

## 6. Walkthrough

1. `ClampScaleBatchAdvanced.main` builds a ragged batch of three rows with different lengths (7, 3, and 5 elements) — deliberately including rows both longer and shorter than a typical lane width (commonly 2 or 4 for `double`), exercising the masked-remainder path on every row, not just the last one.
2. For each row, `clampAndScaleInPlace` runs the main vectorized loop over `SPECIES.loopBound(row.length)` full-width chunks: `v.min(max)` clamps each lane's value down to at most `max`, `.max(min)` then clamps it up to at least `min`, and `.mul(scale)` scales the clamped result — three lane-wise vector operations chained together, each processing a full vector's worth of elements per call, then written back with `intoArray`.
3. For row 0 (7 elements) on, say, a 4-lane machine, the main loop processes indices 0–3 as one full vector; `i` is then `4`, and since `4 < 7`, the masked block runs: `SPECIES.indexInRange(4, 7)` marks lanes corresponding to indices 4, 5, 6 as active and the 4th lane (which would read past the array) as inactive, so `DoubleVector.fromArray(SPECIES, row, 4, mask)` safely loads only the real remaining elements, and the same three chained operations (`min`, `max`, `mul`) apply only to the active lanes when writing back via the masked `intoArray`.
4. For row 1 (only 3 elements, shorter than the 4-lane width), `SPECIES.loopBound(3)` is `0` — the main loop doesn't execute at all — so the *entire* row is processed by the masked block alone, with `SPECIES.indexInRange(0, 3)` marking the first 3 lanes active and the 4th inactive. This demonstrates the masked path correctly handling a row shorter than a single vector's width, not just leftover remainders after full chunks.
5. For row 2 (5 elements, all identical value `6.5`), the main loop processes one full 4-lane chunk (all clamped to `6.5`, since it's within `[0, 10]`, then scaled to `3.25`), and the masked block handles the final single remaining element the same way.
6. Every row's transformation is written back **in place** into `batch[row]` via `intoArray`, since `clampAndScaleInPlace` takes the row array directly and writes into it rather than allocating a new result array — a deliberate simplification here showing that vectorized operations write through to whatever array reference they're given, exactly like scalar array-index assignment would.
7. The printed results confirm correctness across all three ragged rows: values outside `[0, 10]` were clamped before scaling (`-5.0 -> 0 -> 0.0`; `20.5 -> 10 -> 5.0`), and every row, regardless of whether it was longer than, shorter than, or an exact multiple of the hardware's lane width, produced the correct scalar-equivalent result.

```
row 0 (7 elements, 4-lane hardware)
index: 0        4      7
       |-- 4 ---|-- 3 (masked) -->
       [full vector: min/max/mul][masked vector: 3 real + 1 masked-off lane]

row 1 (3 elements, 4-lane hardware)
index: 0   3
       |-- 3 (masked only) -->
       [masked vector: 3 real + 1 masked-off lane]   <- loopBound(3) == 0, main loop skipped entirely
```

## 7. Gotchas & takeaways

> This is still an **incubator module** (`jdk.incubator.vector`) in Java 20 — its fifth incubator round — requiring `--add-modules jdk.incubator.vector`; ongoing refinement of the ARM SVE backend and general performance tuning were this round's focus, with continued incubation (and further API adjustment) in subsequent JDK releases before eventual finalization.
- Chaining lane-wise operations (`v.min(max).max(min).mul(scale)`, as used throughout this example) is idiomatic and efficient — each call returns a new vector, and the JIT compiler is expected to fuse this chain into an efficient sequence of SIMD instructions rather than materializing intermediate arrays.
- The masked path correctly and safely handles rows *shorter* than one full vector width (Level 3's row 1), not just leftover remainders after full-width chunks — `SPECIES.loopBound` simply returns `0` when the whole input is shorter than one lane width, so the entire computation naturally falls through to the masked block alone.
- Processing a *batch* of independent rows (rather than one flat array) is a common realistic shape for numeric kernels — each row's vectorization is entirely independent of the others, and nothing prevents combining this pattern with ordinary parallel streams or virtual threads across rows for additional coarse-grained parallelism on top of the fine-grained SIMD parallelism within each row.
- As with every incubator round of this API so far, the sustained investment across five successive JDK releases reflects how seriously reliable, portable SIMD access is treated as a long-term Java platform goal — worth learning now for genuinely CPU-bound numeric code, while continuing to expect the exact API surface to keep settling until formal finalization.
