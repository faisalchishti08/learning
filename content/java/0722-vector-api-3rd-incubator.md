---
card: java
gi: 722
slug: vector-api-3rd-incubator
title: Vector API (3rd incubator)
---

## 1. What it is

**Java 18** (JEP 417) is the **third incubator** round of the **Vector API**, a pure-Java API (`jdk.incubator.vector`) for expressing vector computations that reliably compile to the **SIMD** (Single Instruction, Multiple Data) instructions available on modern CPUs — AVX on x86, NEON on ARM. Instead of processing one `int` or `float` at a time in a loop and hoping the JIT compiler's auto-vectorizer notices the pattern, code written against the Vector API explicitly operates on a `Vector` of several lanes at once (8 `int`s, 4 `double`s, etc., depending on the platform's hardware width), and the JIT reliably lowers those operations to the matching SIMD instructions. Like the [Foreign Function & Memory API](0721-foreign-function-memory-api-2nd-incubator.md) it shares release cadence with, it is still incubating in Java 18 — usable, but requiring `--add-modules jdk.incubator.vector` and expected to keep evolving before finalization.

## 2. Why & when

Modern CPUs can perform the same arithmetic operation on several numbers simultaneously in a single instruction — add eight pairs of `int`s in one CPU cycle instead of eight separate cycles, for example. The JIT compiler's auto-vectorizer *tries* to spot loops that could use this, but it's fundamentally a best-effort heuristic: small changes to loop structure, bounds checks, or method inlining can silently defeat it, and there's no reliable way for a developer to know whether a hot loop actually got vectorized without inspecting generated assembly. The Vector API removes that guesswork by making vectorization an explicit part of the program's source code — a developer writes `FloatVector.fromArray(...).add(...)` and knows, by construction, that this becomes SIMD instructions on any platform the JVM supports, with a graceful fallback to scalar operations only on hardware that lacks the relevant width. This matters for numerically intensive workloads: image and signal processing, machine-learning inference, physics simulation, cryptography, or any tight numeric loop currently limited by CPU throughput rather than memory bandwidth. It is not a general-purpose replacement for ordinary array loops — the API adds real complexity (species, lanes, masks) that only pays off when a loop is genuinely a performance bottleneck.

## 3. Core concept

```java
import jdk.incubator.vector.*;

static final VectorSpecies<Integer> SPECIES = IntVector.SPECIES_PREFERRED;

// Scalar (one int at a time):
for (int i = 0; i < a.length; i++) c[i] = a[i] + b[i];

// Vector API (several ints per instruction, hardware-dependent width):
for (int i = 0; i < SPECIES.loopBound(a.length); i += SPECIES.length()) {
    IntVector va = IntVector.fromArray(SPECIES, a, i);
    IntVector vb = IntVector.fromArray(SPECIES, b, i);
    va.add(vb).intoArray(c, i);
}
```

`SPECIES.length()` reports how many `int`s fit in one hardware vector register on the *current* machine (commonly 4 or 8) — the same source code adapts to whatever width the CPU it's running on actually supports.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A scalar loop processes one element per iteration; the Vector API processes several elements per iteration using one SIMD instruction, using however many lanes the current CPU supports">
  <text x="160" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Scalar loop</text>
  <rect x="20" y="30" width="30" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="55" y="30" width="30" height="30" fill="#1c2430" stroke="#8b949e"/>
  <rect x="90" y="30" width="30" height="30" fill="#1c2430" stroke="#8b949e"/>
  <rect x="125" y="30" width="30" height="30" fill="#1c2430" stroke="#8b949e"/>
  <text x="80" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">one add per cycle</text>

  <text x="480" y="20" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Vector API (SIMD)</text>
  <rect x="380" y="30" width="220" height="30" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="51" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">8 lanes added in ONE instruction</text>
  <text x="490" y="80" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">SPECIES.length() elements per cycle</text>

  <line x1="200" y1="45" x2="360" y2="45" stroke="#8b949e" stroke-width="1" stroke-dasharray="4"/>
</svg>

The same addition, done one lane at a time versus several lanes per CPU instruction.

## 5. Runnable example

Scenario: adding two arrays element-wise, the classic starting point for SIMD. It grows from a scalar baseline, to the vectorized version using `SPECIES.loopBound` for the bulk of the array with a scalar "tail loop" for the remainder, to a masked version handling an array whose length is *not* a multiple of the vector width in one pass — the real-world hard case any fixed-width SIMD loop must handle correctly.

### Level 1 — Basic

```java
// File: VectorAddBasic.java
// Run with --add-modules jdk.incubator.vector — incubator module in Java 18.
public class VectorAddBasic {
    public static void main(String[] args) {
        int[] a = {1, 2, 3, 4, 5, 6, 7, 8};
        int[] b = {10, 20, 30, 40, 50, 60, 70, 80};
        int[] c = new int[a.length];

        // Plain scalar loop — the baseline this example will vectorize.
        for (int i = 0; i < a.length; i++) {
            c[i] = a[i] + b[i];
        }

        System.out.println("Result: " + java.util.Arrays.toString(c));
    }
}
```

**How to run:**
```
java VectorAddBasic.java
```

Expected output:
```
Result: [11, 22, 33, 44, 55, 66, 77, 88]
```

### Level 2 — Intermediate

```java
// File: VectorAddIntermediate.java
// The SAME element-wise addition, now expressed with the Vector API,
// processing SPECIES.length() elements per loop iteration with an explicit
// scalar "tail loop" for any leftover elements that don't fill a full vector.
import jdk.incubator.vector.*;

public class VectorAddIntermediate {
    static final VectorSpecies<Integer> SPECIES = IntVector.SPECIES_PREFERRED;

    public static void main(String[] args) {
        int[] a = {1, 2, 3, 4, 5, 6, 7, 8, 9};   // 9 elements: not necessarily a multiple of SPECIES.length()
        int[] b = {10, 20, 30, 40, 50, 60, 70, 80, 90};
        int[] c = new int[a.length];

        System.out.println("Vector lane width on this machine: " + SPECIES.length());

        int i = 0;
        int bound = SPECIES.loopBound(a.length); // largest index that's a full multiple of SPECIES.length()
        for (; i < bound; i += SPECIES.length()) {
            IntVector va = IntVector.fromArray(SPECIES, a, i);
            IntVector vb = IntVector.fromArray(SPECIES, b, i);
            va.add(vb).intoArray(c, i);
        }
        // Scalar tail loop: handles the remaining elements that don't fill a full vector.
        for (; i < a.length; i++) {
            c[i] = a[i] + b[i];
        }

        System.out.println("Result: " + java.util.Arrays.toString(c));
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.vector VectorAddIntermediate.java
```

Expected output (lane width varies by CPU; result is identical regardless):
```
Vector lane width on this machine: 8
Result: [11, 22, 33, 44, 55, 66, 77, 88, 99]
```

### Level 3 — Advanced

```java
// File: VectorAddAdvanced.java
// Replaces the separate scalar tail loop with a MASKED vector operation,
// handling the remainder in a single vectorized pass instead of a second
// scalar loop — the production-flavored technique for irregular array sizes.
import jdk.incubator.vector.*;

public class VectorAddAdvanced {
    static final VectorSpecies<Integer> SPECIES = IntVector.SPECIES_PREFERRED;

    static void vectorAdd(int[] a, int[] b, int[] c) {
        int i = 0;
        int upperBound = SPECIES.loopBound(a.length);
        for (; i < upperBound; i += SPECIES.length()) {
            IntVector va = IntVector.fromArray(SPECIES, a, i);
            IntVector vb = IntVector.fromArray(SPECIES, b, i);
            va.add(vb).intoArray(c, i);
        }
        // Masked tail: process the remainder with a vector operation too,
        // using a mask so lanes beyond the array's real length are inert.
        if (i < a.length) {
            VectorMask<Integer> mask = SPECIES.indexInRange(i, a.length);
            IntVector va = IntVector.fromArray(SPECIES, a, i, mask);
            IntVector vb = IntVector.fromArray(SPECIES, b, i, mask);
            va.add(vb).intoArray(c, i, mask);
        }
    }

    public static void main(String[] args) {
        int[] a = new int[19]; // deliberately awkward size relative to typical lane widths (4/8)
        int[] b = new int[19];
        for (int i = 0; i < a.length; i++) { a[i] = i + 1; b[i] = (i + 1) * 10; }
        int[] c = new int[a.length];

        vectorAdd(a, b, c);

        System.out.println("Lane width: " + SPECIES.length());
        System.out.println("Result: " + java.util.Arrays.toString(c));
    }
}
```

**How to run:**
```
java --add-modules jdk.incubator.vector VectorAddAdvanced.java
```

Expected output (lane width varies by CPU; result is deterministic):
```
Lane width: 8
Result: [11, 22, 33, 44, 55, 66, 77, 88, 99, 110, 121, 132, 143, 154, 165, 176, 187, 198, 209]
```

## 6. Walkthrough

1. `VectorAddAdvanced.main` builds two 19-element arrays — a size chosen deliberately so it is **not** an exact multiple of the machine's vector lane width (commonly 4 or 8 for `int`), forcing the "leftover elements" case every real vectorized loop must handle.
2. `vectorAdd(a, b, c)` first computes `SPECIES.loopBound(a.length)` — the largest index that's a clean multiple of `SPECIES.length()`. For a 19-element array on an 8-lane machine, this is `16` (two full vectors of 8 fit; the 17th through 19th elements don't).
3. The main loop runs from `i = 0` to `i = 16` in steps of `8`: each iteration loads 8 `int`s from `a` and 8 from `b` into `IntVector`s via `fromArray`, adds them lane-by-lane in a single SIMD instruction, and writes the 8-wide result back into `c` via `intoArray` — this is the bulk of the work, done at full hardware width.
4. After the main loop, `i` is `16` and `a.length` is `19` — three elements remain (indices 16, 17, 18). Rather than falling back to a plain scalar loop (as Level 2 did), `SPECIES.indexInRange(i, a.length)` builds a `VectorMask` marking lanes 0, 1, 2 of the *next* vector as "in range" and lanes 3 through 7 as "out of range."
5. `IntVector.fromArray(SPECIES, a, i, mask)` then loads a full 8-lane vector, but the masked lanes are loaded safely (not reading past the end of the array) and the corresponding output lanes in `intoArray(c, i, mask)` are simply not written — only indices 16, 17, 18 of `c` actually get updated by this masked operation.
6. The result is that all 19 elements get correctly summed using exactly two vectorized code paths (the full-width loop and one masked operation) and zero scalar arithmetic — a technique that matters at scale, since a separate scalar tail loop (Level 2's approach) is simpler to read but leaves the last few elements unvectorized on every single call.

```
19 elements, 8-lane hardware
index:  0                    16          19
        |--------- 16 -------|-- 3 -->
        [ full vector ][ full vector ][ masked partial vector ]
             8 lanes         8 lanes      3 real + 5 masked-off lanes
```

## 7. Gotchas & takeaways

> This is an **incubator module** (`jdk.incubator.vector`) in Java 18 — it requires `--add-modules jdk.incubator.vector`, and — this being its **third** incubator round — the exact API shape (class names, method signatures) had already changed across earlier rounds and continued changing in later JDKs before eventual finalization. Code written against Java 18's incubator surface is not guaranteed to compile unmodified against a later JDK's finalized Vector API.
- `SPECIES.length()` is **hardware-dependent** — the same Java source code run on different CPUs may use 4, 8, or 16 lanes per vector, depending on what SIMD instruction sets (SSE, AVX2, AVX-512, NEON, etc.) are available. This is deliberate: the code adapts to the machine rather than hard-coding a width.
- Forgetting the tail — whether via a scalar loop (Level 2) or a masked operation (Level 3) — is the single most common Vector API bug: processing only `SPECIES.loopBound(length)` elements silently drops the remainder whenever the array length isn't an exact multiple of the lane width.
- Masked operations (`VectorMask`, `indexInRange`) are generally the more idiomatic and often faster approach for irregular remainders, since they avoid a separate scalar code path entirely — but they add real conceptual overhead, so a straightforward scalar tail loop is a perfectly reasonable choice when the loop isn't in an extremely hot path.
- The Vector API pays off specifically for CPU-bound numeric loops — array addition, dot products, image kernels, cryptographic primitives. For I/O-bound or already memory-bandwidth-limited code, the added complexity of explicit vectorization typically isn't worth it; profile first, then reach for the Vector API only where the numbers justify it.
