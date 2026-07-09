---
card: java
gi: 691
slug: stream-mapmulti-later-vector-api-incubator
title: Stream.mapMulti (later) / Vector API (incubator)
---

## 1. What it is

**Java 16** introduced the **Vector API** as its first **incubator module** (JEP 338) — an experimental API (`jdk.incubator.vector`) for expressing computations that compile down to CPU **SIMD** (Single Instruction, Multiple Data) instructions, letting a single operation act on several values (e.g. 4 or 8 `int`s) in parallel at the hardware level, rather than one at a time. (`Stream.mapMulti`, referenced alongside it in this topic's title, arrived in a later JDK release as a complementary stream-flattening method; it is covered here for context but was not itself part of Java 16 — the Vector API incubator is the actual Java 16 feature.) Incubator modules (a mechanism introduced earlier for exactly this purpose) let the JDK ship an experimental, non-final API under `jdk.incubator.*` so real-world usage can shape the design before it's finalized as a standard part of `java.base`.

## 2. Why & when

Numerically intensive code — image processing, machine learning kernels, physics simulations, cryptography — often has tight inner loops that process large arrays of numbers, and modern CPUs can execute the same arithmetic operation on multiple data elements simultaneously via SIMD instruction sets (SSE, AVX on x86; NEON on ARM). Before the Vector API, Java code couldn't directly express "add these 8 numbers to these other 8 numbers in one CPU instruction" — the JIT compiler's auto-vectorization could sometimes recognize vectorizable loop patterns and generate SIMD instructions automatically, but this was unreliable and non-portable across the different vector-instruction widths different CPUs support. The Vector API gives developers an explicit, portable way to write vectorized code that the JVM compiles to whatever SIMD width the actual running hardware supports, abstracting away the CPU-specific details. Reach for it (understanding it remained an evolving incubator API for years after Java 16) only in numerically-heavy, performance-critical inner loops where profiling has shown scalar array processing is the bottleneck — it is not a general-purpose replacement for ordinary loops or streams.

## 3. Core concept

```java
// Requires: --add-modules jdk.incubator.vector (module was incubating as of Java 16)
import jdk.incubator.vector.*;

static final VectorSpecies<Integer> SPECIES = IntVector.SPECIES_PREFERRED;

static void addArrays(int[] a, int[] b, int[] result) {
    int i = 0;
    int upperBound = SPECIES.loopBound(a.length);
    for (; i < upperBound; i += SPECIES.length()) {
        IntVector va = IntVector.fromArray(SPECIES, a, i);
        IntVector vb = IntVector.fromArray(SPECIES, b, i);
        va.add(vb).intoArray(result, i);
    }
    for (; i < a.length; i++) { // scalar tail for remaining elements
        result[i] = a[i] + b[i];
    }
}
```

`SPECIES.length()` reports how many `int`s fit in one hardware vector register on the *actual running CPU* — the same source code adapts to whatever SIMD width is available, rather than hard-coding a specific width.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scalar addition processes one element per instruction; vector addition processes several elements in one SIMD instruction">
  <rect x="20" y="20" width="280" height="150" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Scalar loop</text>
  <text x="160" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">a[0]+b[0] -> r[0]  (1 instr)</text>
  <text x="160" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">a[1]+b[1] -> r[1]  (1 instr)</text>
  <text x="160" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">a[2]+b[2] -> r[2]  (1 instr)</text>
  <text x="160" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">a[3]+b[3] -> r[3]  (1 instr)</text>
  <text x="160" y="155" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">4 instructions total</text>

  <rect x="340" y="20" width="280" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Vector (SIMD) op</text>
  <text x="480" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">[a0,a1,a2,a3] + [b0,b1,b2,b3]</text>
  <text x="480" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">-> [r0,r1,r2,r3]</text>
  <text x="480" y="130" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">1 SIMD instruction total</text>
</svg>

The same four additions happen either as four separate scalar instructions or as one instruction operating on a whole vector register.

## 5. Runnable example

Scenario: adding two large arrays of integers — first a plain scalar loop as the baseline, then the same computation expressed with the Vector API's explicit SIMD operations (with a scalar tail loop for any leftover elements that don't fill a whole vector), then a version that also computes a dot product, showing a second, slightly more involved vectorized reduction.

### Level 1 — Basic

```java
// File: ScalarAdd.java
public class ScalarAdd {
    public static void main(String[] args) {
        int[] a = new int[1000];
        int[] b = new int[1000];
        for (int i = 0; i < a.length; i++) { a[i] = i; b[i] = i * 2; }

        int[] result = new int[a.length];
        for (int i = 0; i < a.length; i++) {
            result[i] = a[i] + b[i];
        }

        System.out.println("result[0] = " + result[0]);
        System.out.println("result[999] = " + result[999]);
    }
}
```

**How to run:** `java ScalarAdd.java`

Expected output:
```
result[0] = 0
result[999] = 2997
```

### Level 2 — Intermediate

```java
// File: VectorAdd.java
// Requires the incubating Vector API module (Java 16+): --add-modules jdk.incubator.vector
import jdk.incubator.vector.IntVector;
import jdk.incubator.vector.VectorSpecies;

public class VectorAdd {
    static final VectorSpecies<Integer> SPECIES = IntVector.SPECIES_PREFERRED;

    static void addArrays(int[] a, int[] b, int[] result) {
        int i = 0;
        int upperBound = SPECIES.loopBound(a.length);
        for (; i < upperBound; i += SPECIES.length()) {
            IntVector va = IntVector.fromArray(SPECIES, a, i);
            IntVector vb = IntVector.fromArray(SPECIES, b, i);
            va.add(vb).intoArray(result, i);
        }
        for (; i < a.length; i++) { // scalar tail for elements that don't fill a full vector
            result[i] = a[i] + b[i];
        }
    }

    public static void main(String[] args) {
        int[] a = new int[1000];
        int[] b = new int[1000];
        for (int i = 0; i < a.length; i++) { a[i] = i; b[i] = i * 2; }

        int[] result = new int[a.length];
        addArrays(a, b, result);

        System.out.println("Vector width (ints per SIMD register): " + SPECIES.length());
        System.out.println("result[0] = " + result[0]);
        System.out.println("result[999] = " + result[999]);
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.vector VectorAdd.java
```

Expected output (the JVM prints a one-time incubator warning to stderr; the vector width depends on the CPU's actual SIMD capability — 4, 8, or 16 are common):
```
WARNING: Using incubator modules: jdk.incubator.vector
Vector width (ints per SIMD register): 4
result[0] = 0
result[999] = 2997
```

The results are numerically identical to the scalar version — the Vector API changes *how* the CPU executes the addition (several elements per instruction instead of one), not the mathematical result. `SPECIES.loopBound(a.length)` computes the largest multiple of the vector width that fits within `a.length`, and the trailing scalar loop handles any remaining elements (here, 1000 isn't necessarily a multiple of the vector width, so the tail loop matters).

### Level 3 — Advanced

```java
// File: VectorDotProduct.java
// Requires: --add-modules jdk.incubator.vector
import jdk.incubator.vector.IntVector;
import jdk.incubator.vector.VectorSpecies;

public class VectorDotProduct {
    static final VectorSpecies<Integer> SPECIES = IntVector.SPECIES_PREFERRED;

    static long dotProduct(int[] a, int[] b) {
        int i = 0;
        int upperBound = SPECIES.loopBound(a.length);
        IntVector accVector = IntVector.zero(SPECIES);

        for (; i < upperBound; i += SPECIES.length()) {
            IntVector va = IntVector.fromArray(SPECIES, a, i);
            IntVector vb = IntVector.fromArray(SPECIES, b, i);
            accVector = accVector.add(va.mul(vb));
        }

        long sum = accVector.reduceLanes(jdk.incubator.vector.VectorOperators.ADD);

        for (; i < a.length; i++) { // scalar tail
            sum += (long) a[i] * b[i];
        }
        return sum;
    }

    static long dotProductScalar(int[] a, int[] b) {
        long sum = 0;
        for (int i = 0; i < a.length; i++) {
            sum += (long) a[i] * b[i];
        }
        return sum;
    }

    public static void main(String[] args) {
        int[] a = new int[1000];
        int[] b = new int[1000];
        for (int i = 0; i < a.length; i++) { a[i] = i % 100; b[i] = (i % 100) + 1; }

        long vectorResult = dotProduct(a, b);
        long scalarResult = dotProductScalar(a, b);

        System.out.println("Vector dot product:  " + vectorResult);
        System.out.println("Scalar dot product:   " + scalarResult);
        System.out.println("Results match: " + (vectorResult == scalarResult));
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.vector VectorDotProduct.java
```

Expected output:
```
WARNING: Using incubator modules: jdk.incubator.vector
Vector dot product:  3333000
Scalar dot product:   3333000
Results match: true
```

Level 3 computes a **dot product** — multiply corresponding elements, then sum everything — using vectorized multiply (`va.mul(vb)`) accumulated into a running vector (`accVector.add(...)`), only reducing the vector down to a single scalar sum via `reduceLanes(ADD)` once, at the very end, rather than after every element. This "accumulate as a vector, reduce once" pattern is the standard idiom for vectorizing a reduction like a dot product, sum, or similar aggregation.

## 6. Walkthrough

1. `dotProduct` first computes `upperBound = SPECIES.loopBound(a.length)` — the largest multiple of the hardware's vector width that's `<= a.length` — so the main vectorized loop never reads past the array's bounds in chunks of `SPECIES.length()`.
2. `IntVector accVector = IntVector.zero(SPECIES)` creates a vector of zeros, one lane per element the hardware vector register holds — this will accumulate partial products across all loop iterations, lane by lane, rather than being reduced to a scalar on every iteration (which would defeat the purpose of vectorizing).
3. Inside the main loop, `IntVector.fromArray(SPECIES, a, i)` and `...(SPECIES, b, i)` load `SPECIES.length()` consecutive elements from `a` and `b` starting at index `i` into two vector registers (`va`, `vb`) in one memory operation each.
4. `va.mul(vb)` performs an element-wise multiply across all lanes in a single SIMD instruction, producing a vector of `SPECIES.length()` partial products; `accVector.add(...)` then adds that whole vector into the running `accVector`, again as one SIMD instruction — two vector operations replace what would otherwise be `SPECIES.length()` separate scalar multiply-and-add operations.
5. After the main loop finishes (having processed `upperBound` elements, `SPECIES.length()` at a time), `accVector.reduceLanes(VectorOperators.ADD)` performs a **horizontal reduction**: it sums all the lanes *within* `accVector` down to one single `long` value — this is the one point where the vectorized partial sums collapse into a genuine scalar total.
6. The trailing `for` loop then handles any remaining elements from `upperBound` to `a.length - 1` (elements that didn't fill a complete vector register) using plain scalar multiply-and-accumulate, added onto `sum`.
7. `main` calls both `dotProduct` (vectorized) and `dotProductScalar` (a conventional single-element-at-a-time loop) on the same input arrays and prints both results alongside a direct equality check — confirming the vectorized computation produces the mathematically identical answer, just computed via a different, hardware-parallel execution strategy.

```
main loop (vectorized): for i in steps of SPECIES.length():
    va = load a[i..i+width)
    vb = load b[i..i+width)
    accVector += va * vb      (all lanes, in parallel)
                    │
      after loop: reduceLanes(ADD) -> single scalar partial sum
                    │
tail loop (scalar): for remaining i: sum += a[i]*b[i]
                    │
                 final sum
```

## 7. Gotchas & takeaways

> The Vector API was an **incubator module** (`jdk.incubator.vector`) starting in Java 16 — it required `--add-modules jdk.incubator.vector` on both compilation and execution, its package and class names could still change between JDK releases, and it remained in incubation status for many releases after Java 16 before eventual finalization. Code written against the Java 16 incubator API may not compile unchanged against later incubator revisions.

- The Vector API only helps when a computation is genuinely data-parallel across array elements — it's the wrong tool for control-flow-heavy or branch-dependent logic.
- Always include a scalar "tail loop" for the remainder — `SPECIES.loopBound(length)` almost never equals the array's full length unless that length happens to be an exact multiple of the hardware vector width.
- `SPECIES.length()` (the number of elements per vector register) is **hardware-dependent** and can differ across CPUs; portable code must never hard-code a specific width and should always query it via the `VectorSpecies`.
- For a reduction (sum, dot product, min/max), accumulate using vector operations across the whole loop and call `reduceLanes(...)` **once** at the end — reducing to a scalar on every iteration defeats the purpose of vectorizing.
- Before reaching for the Vector API, confirm via profiling that a scalar loop is actually the bottleneck, and check whether the JIT's existing auto-vectorization already handles the simple case adequately — explicit vectorization adds real code complexity that's only worth it when the performance win is measured and significant.
