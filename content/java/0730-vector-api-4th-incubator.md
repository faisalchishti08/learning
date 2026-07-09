---
card: java
gi: 730
slug: vector-api-4th-incubator
title: Vector API (4th incubator)
---

## 1. What it is

**Java 19** (JEP 426) is the **fourth incubator** round of the [Vector API](0722-vector-api-3rd-incubator.md), continuing to refine `jdk.incubator.vector` for expressing computations that reliably compile to SIMD CPU instructions. This round's headline addition is **initial support for the ARM Scalable Vector Extension (SVE)** on top of the existing x86 (AVX) and ARM NEON backends — meaning vector code written once against the API's hardware-agnostic `VectorSpecies` abstraction now has another real hardware target it can lower to efficiently, without any change to the Java source. The programming model itself — species, lanes, masks, vector operations — carries over unchanged from the third incubator round covered in [Java 18](0722-vector-api-3rd-incubator.md); this release is about backend coverage and refinement, not API redesign.

## 2. Why & when

Each incubator round of the Vector API exists to widen real-world hardware coverage and sand down rough edges found through actual use, before the API is considered stable enough to finalize. ARM-based server hardware (and SVE specifically, a *scalable* vector instruction set where the hardware vector width isn't fixed at compile time the way x86's AVX register widths are) had become an increasingly important target for JVM workloads by this point, particularly for cloud deployments moving toward ARM-based server chips. Adding SVE support matters because the entire value proposition of the Vector API is portability with performance: a developer writes one vectorized Java algorithm, and `SPECIES_PREFERRED` picks the best available width for *whatever* CPU the code actually runs on — x86 with AVX2's 256 bits, ARM NEON's 128 bits, or now ARM SVE's variable width (128 to 2048 bits depending on the specific chip). Without SVE support, that portability promise would have a real gap on an increasingly common class of hardware. As with the third incubator, use this API for genuinely CPU-bound numeric hot loops — the same due-diligence caveat applies: this is still an incubator module requiring `--add-modules jdk.incubator.vector`, and the API kept evolving through further incubator rounds before eventual finalization.

## 3. Core concept

```java
import jdk.incubator.vector.*;

// Unchanged from the 3rd incubator round — the programming model is stable;
// what's new in Java 19 is another hardware backend (ARM SVE) it can target.
static final VectorSpecies<Float> SPECIES = FloatVector.SPECIES_PREFERRED;

static void dotProductStep(float[] a, float[] b, float[] partialSums, int i) {
    FloatVector va = FloatVector.fromArray(SPECIES, a, i);
    FloatVector vb = FloatVector.fromArray(SPECIES, b, i);
    va.fma(vb, FloatVector.fromArray(SPECIES, partialSums, i)).intoArray(partialSums, i);
}
```

The same source compiles to AVX instructions on x86, NEON instructions on most ARM chips, or SVE instructions on SVE-capable ARM hardware — `SPECIES.length()` reflects whichever is actually running underneath.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same Vector API Java source code compiles down to different SIMD instruction sets depending on the CPU it runs on: AVX on x86, NEON or SVE on ARM">
  <rect x="230" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">one Java source file</text>

  <line x1="280" y1="70" x2="150" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a9)"/>
  <line x1="320" y1="70" x2="320" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a9)"/>
  <line x1="360" y1="70" x2="490" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a9)"/>

  <rect x="40" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="130" y="142" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">x86: AVX</text>
  <text x="130" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">fixed 256-bit</text>

  <rect x="230" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="142" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ARM: NEON</text>
  <text x="320" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">fixed 128-bit</text>

  <rect x="420" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#3fb950"/>
  <text x="510" y="142" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">ARM: SVE (new, Java 19)</text>
  <text x="510" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">scalable, 128-2048 bit</text>

  <defs><marker id="a9" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

Java 19 widens the Vector API's hardware reach to include ARM's scalable vector extension, no source change required.

## 5. Runnable example

Scenario: computing a dot product of two float arrays — a fundamental operation in linear algebra and machine learning. It grows from a scalar baseline, to a vectorized version using the fused multiply-add (`fma`) operation for both speed and precision, to a version that reduces the vector's lanes into a single scalar sum using the API's built-in horizontal reduction, on whatever hardware width happens to be available.

### Level 1 — Basic

```java
// File: DotProductBasic.java
public class DotProductBasic {
    static float dotProduct(float[] a, float[] b) {
        float sum = 0f;
        for (int i = 0; i < a.length; i++) {
            sum += a[i] * b[i];
        }
        return sum;
    }

    public static void main(String[] args) {
        float[] a = {1, 2, 3, 4, 5, 6, 7, 8};
        float[] b = {8, 7, 6, 5, 4, 3, 2, 1};
        System.out.println("Dot product: " + dotProduct(a, b));
    }
}
```

**How to run:**
```
java DotProductBasic.java
```

Expected output:
```
Dot product: 120.0
```

### Level 2 — Intermediate

```java
// File: DotProductIntermediate.java
// Run with --add-modules jdk.incubator.vector — incubator module in Java 19.
// The SAME dot product, vectorized using fused multiply-add (fma), which
// computes (a*b)+c in one step with a single rounding, more accurately and
// often faster than a separate multiply followed by an add.
import jdk.incubator.vector.*;

public class DotProductIntermediate {
    static final VectorSpecies<Float> SPECIES = FloatVector.SPECIES_PREFERRED;

    static float dotProduct(float[] a, float[] b) {
        System.out.println("Lane width on this machine: " + SPECIES.length());
        FloatVector sumVector = FloatVector.zero(SPECIES);

        int i = 0;
        int bound = SPECIES.loopBound(a.length);
        for (; i < bound; i += SPECIES.length()) {
            FloatVector va = FloatVector.fromArray(SPECIES, a, i);
            FloatVector vb = FloatVector.fromArray(SPECIES, b, i);
            sumVector = va.fma(vb, sumVector); // sumVector = (va * vb) + sumVector
        }

        float sum = sumVector.reduceLanes(VectorOperators.ADD); // horizontal sum of all lanes
        for (; i < a.length; i++) { // scalar tail for any leftover elements
            sum += a[i] * b[i];
        }
        return sum;
    }

    public static void main(String[] args) {
        float[] a = {1, 2, 3, 4, 5, 6, 7, 8};
        float[] b = {8, 7, 6, 5, 4, 3, 2, 1};
        System.out.println("Dot product: " + dotProduct(a, b));
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.vector DotProductIntermediate.java
```

Expected output (lane width varies by CPU):
```
Lane width on this machine: 8
Dot product: 120.0
```

### Level 3 — Advanced

```java
// File: DotProductAdvanced.java
// Handles an array size that's NOT a multiple of the lane width using a
// masked final block instead of a separate scalar tail loop, and computes
// dot products across a batch of vector pairs — the production-flavored
// shape of a small linear-algebra routine.
import jdk.incubator.vector.*;

public class DotProductAdvanced {
    static final VectorSpecies<Float> SPECIES = FloatVector.SPECIES_PREFERRED;

    static float dotProduct(float[] a, float[] b) {
        FloatVector sumVector = FloatVector.zero(SPECIES);

        int i = 0;
        int bound = SPECIES.loopBound(a.length);
        for (; i < bound; i += SPECIES.length()) {
            FloatVector va = FloatVector.fromArray(SPECIES, a, i);
            FloatVector vb = FloatVector.fromArray(SPECIES, b, i);
            sumVector = va.fma(vb, sumVector);
        }

        if (i < a.length) {
            VectorMask<Float> mask = SPECIES.indexInRange(i, a.length);
            FloatVector va = FloatVector.fromArray(SPECIES, a, i, mask);
            FloatVector vb = FloatVector.fromArray(SPECIES, b, i, mask);
            sumVector = va.fma(vb, sumVector, mask); // masked fma: unmasked lanes pass sumVector through unchanged
        }

        return sumVector.reduceLanes(VectorOperators.ADD);
    }

    public static void main(String[] args) {
        // 13 elements: deliberately not a multiple of typical lane widths (4/8).
        float[] a = new float[13];
        float[] b = new float[13];
        for (int i = 0; i < 13; i++) { a[i] = i + 1; b[i] = 13 - i; }

        float result = dotProduct(a, b);
        System.out.println("Lane width: " + SPECIES.length());
        System.out.println("Dot product of 13-element vectors: " + result);

        // Batch: compute dot products for 3 independent pairs.
        float[][] batchA = {{1, 2, 3}, {4, 5, 6}, {0, 0, 1}};
        float[][] batchB = {{1, 0, 0}, {1, 1, 1}, {2, 2, 2}};
        for (int k = 0; k < batchA.length; k++) {
            System.out.println("batch[" + k + "] dot product: " + dotProduct(batchA[k], batchB[k]));
        }
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.vector DotProductAdvanced.java
```

Expected output (lane width varies by CPU; results are deterministic):
```
Lane width: 8
Dot product of 13-element vectors: 455.0
batch[0] dot product: 1.0
batch[1] dot product: 15.0
batch[2] dot product: 2.0
```

## 6. Walkthrough

1. `DotProductAdvanced.main` builds two 13-element `float` arrays — a length deliberately not a clean multiple of common lane widths (4 or 8), exercising the masked-remainder path this level adds over Level 2's separate scalar tail loop.
2. Inside `dotProduct`, `FloatVector.zero(SPECIES)` creates an all-zero vector accumulator, `sumVector`, with as many lanes as the current hardware supports (`SPECIES.length()`).
3. The main loop processes full-width chunks: for each chunk, `va.fma(vb, sumVector)` computes, per lane, `(va[lane] * vb[lane]) + sumVector[lane]` in a single fused operation — this is a **fused multiply-add**, computed with one rounding step rather than a separate multiply followed by a separate add, which is both typically faster (many CPUs have a dedicated FMA instruction) and slightly more numerically accurate.
4. After the main loop, if `i < a.length` (here, after processing 8 of 13 elements at an 8-lane width, 5 remain), a `VectorMask` is built via `SPECIES.indexInRange(i, a.length)`, marking exactly the 5 real remaining lanes as active and the rest as inactive.
5. The masked `va.fma(vb, sumVector, mask)` call performs the same fused multiply-add, but only for the masked-active lanes; for inactive lanes, `sumVector`'s existing value passes through unchanged rather than being corrupted by reading past the array's real data — this is what makes it safe to build a full-width vector even when fewer than a full width of real elements remain.
6. `sumVector.reduceLanes(VectorOperators.ADD)` performs a **horizontal reduction**: it sums all of `sumVector`'s lanes together into one scalar `float` — turning the lane-wise accumulated partial products into the single dot-product total. This single call replaces what would otherwise require a manual loop extracting and summing each lane individually.
7. The batch loop at the end calls the exact same `dotProduct` method on three small, independent array pairs — demonstrating that the vectorized routine's correctness doesn't depend on array size being conveniently large or lane-aligned; the masked path handles even a 3-element array running on an 8-lane machine correctly (all 3 elements masked-active, the other 5 lanes masked-off).

```
13 elements, 8-lane hardware
index: 0                 8           13
       |------- 8 -------|--- 5 --->
       [ full FMA vector ][ masked FMA: 5 real + 3 masked-off lanes ]
                |                        |
                +---------- accumulate into sumVector ----------+
                                    |
                                    v
                    sumVector.reduceLanes(ADD) -> single float total
```

## 7. Gotchas & takeaways

> This is still an **incubator module** (`jdk.incubator.vector`) in Java 19 — its fourth incubator round — requiring `--add-modules jdk.incubator.vector`; the addition of ARM SVE backend support in this release changes what hardware the API can target efficiently, but does not change the stability status of the API surface itself, which continued through further incubator rounds before finalization.
- `fma` (fused multiply-add) is preferred over a separate multiply and add specifically for accumulation patterns like dot products: it's often faster on hardware with a dedicated FMA instruction, and it avoids an intermediate rounding step, giving a slightly more accurate result than `va.mul(vb).add(sumVector)` would.
- `reduceLanes(VectorOperators.ADD)` (horizontal reduction) is comparatively expensive relative to the lane-wise operations inside the main loop — the idiomatic pattern is exactly what's shown here: accumulate lane-wise across the whole loop first, and call `reduceLanes` only once at the very end, not per iteration.
- ARM SVE's defining characteristic — a **scalable** vector width not fixed at compile time — is exactly why `SPECIES_PREFERRED` (rather than a hardcoded width) is the idiomatic choice: code written against a fixed width like 256 bits would not automatically benefit from wider SVE hardware, while `SPECIES_PREFERRED`-based code picks up whatever width the specific chip it runs on actually provides.
- As with the third incubator round, masked operations (Level 3) are generally the more idiomatic choice over a separate scalar tail loop (Level 2) for irregular array sizes — they keep the entire computation inside the vectorized code path, at the cost of a small amount of added conceptual complexity around mask construction.
