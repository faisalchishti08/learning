---
card: java
gi: 18
slug: incubator-modules
title: Incubator modules
---

## 1. What it is

An **incubator module** is an experimental API shipped with the JDK under the `jdk.incubator.*` namespace. Where **preview features** are language/JVM-level experiments, incubator modules are **API-level** experiments — new library APIs that need real-world feedback before being standardised into a permanent `java.*` or `javax.*` package. Incubator modules require explicit opt-in via `--add-modules jdk.incubator.XXX`.

An incubator module can be promoted to a **standard module** or **dropped** in a future release. The key difference from preview features: incubator modules are stable enough to ship in the JDK but not stable enough to be permanent API.

## 2. Why & when

Incubator modules solve a bootstrapping problem: you cannot gather meaningful feedback on an API from the community without shipping it, but you cannot ship a permanent API before you have that feedback. The `jdk.incubator` namespace is a quarantine that makes the "this may change" signal explicit.

Recent incubator examples and their outcomes:
- **jdk.incubator.httpclient** (Java 9–10) → **java.net.http** (Java 11 final) — the modern HTTP client.
- **jdk.incubator.vector** (Java 16–21+) → still evolving, used for SIMD vector operations.
- **jdk.incubator.concurrent** (Java 19–20) → **java.util.concurrent** additions (StructuredTaskScope became final Java 21).

You use incubator modules when:
- Evaluating or providing feedback on a new JDK API before it's standardised.
- Using cutting-edge JDK capabilities (SIMD vectors, foreign function) in experiments.
- Building performance-critical code that needs a feature that isn't final yet.

## 3. Core concept

Incubator modules live in a separate namespace and require explicit module opt-in:

```
Without flag (won't compile/run):
  import jdk.incubator.vector.*;
  // ERROR: package jdk.incubator.vector is not visible

With flag:
  javac --add-modules jdk.incubator.vector  MyApp.java
  java  --add-modules jdk.incubator.vector  MyApp
```

**Lifecycle:**

```
JEP: Incubating → Standard (promoted to java.*)
                → Re-incubating (refined, stays incubator another release)
                → Dropped
```

You can list available incubator modules:
```
java --list-modules | grep incubator
```

**Comparison: Preview vs Incubator:**

| | Preview feature | Incubator module |
|---|---|---|
| What it is | Language/JVM change | New library API |
| Flag to enable | `--enable-preview` | `--add-modules jdk.incubator.X` |
| Package | Standard (`java.lang`, etc.) | `jdk.incubator.*` |
| Compilation warning | None | Warning: "using incubating module" |
| Example | Records, sealed classes | HTTP client v1, Vector API |

## 4. Diagram

<svg viewBox="0 0 680 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Incubator module lifecycle: JEP → incubator → standard or dropped">
  <defs>
    <marker id="ainc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ainc2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
  <!-- JEP -->
  <rect x="20" y="70" width="100" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="93"  fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JEP</text>
  <text x="70" y="108" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">proposal</text>

  <line x1="120" y1="95" x2="158" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ainc)"/>

  <!-- Incubator -->
  <rect x="160" y="60" width="160" height="70" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="240" y="86"  fill="#f0883e" font-size="12" text-anchor="middle" font-family="sans-serif">jdk.incubator.X</text>
  <text x="240" y="103" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">--add-modules required</text>
  <text x="240" y="117" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">warns: incubating module</text>

  <!-- Promote -->
  <line x1="320" y1="85" x2="398" y2="72" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ainc)"/>
  <text x="358" y="73" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">promote</text>

  <!-- Standard -->
  <rect x="400" y="55" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="465" y="77"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">java.* module</text>
  <text x="465" y="92"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">permanent API</text>

  <!-- Drop -->
  <line x1="320" y1="110" x2="398" y2="128" stroke="#f85149" stroke-width="1.5" marker-end="url(#ainc2)"/>
  <text x="358" y="128" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">drop</text>

  <rect x="400" y="115" width="130" height="42" rx="6" fill="#0d1117" stroke="#f85149" stroke-width="1.5"/>
  <text x="465" y="138" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Removed</text>

  <!-- Re-incubate loop -->
  <path d="M 240 60 Q 240 30 240 60" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="265" y="42" fill="#8b949e" font-size="8" font-family="sans-serif">re-incubate (refine)</text>
</svg>

Incubator module → feedback → promote to `java.*` or drop. Never permanent while in `jdk.incubator`.

## 5. Runnable example

Scenario: use the `jdk.incubator.vector` Vector API (available Java 16+) — one of the longest-running incubator APIs — to demonstrate SIMD-style vectorised arithmetic, and show the performance benefit vs scalar code.

### Level 1 — Basic

```java
// IncubatorCheck.java
// Run: java --add-modules jdk.incubator.vector IncubatorCheck.java
// If jdk.incubator.vector is not available: shows an informational message
public class IncubatorCheck {
    public static void main(String[] args) {
        System.out.println("Java version: " + Runtime.version());
        System.out.println("Checking for incubator modules...\n");

        boolean hasVector = moduleExists("jdk.incubator.vector");
        System.out.println("jdk.incubator.vector : " + (hasVector ? "PRESENT" : "absent"));
        System.out.println();
        System.out.println("To use incubator modules:");
        System.out.println("  java --add-modules jdk.incubator.vector  YourClass");
        System.out.println("  javac --add-modules jdk.incubator.vector YourClass.java");
        System.out.println();
        System.out.println("Warning emitted by JVM when using incubating modules:");
        System.out.println("  WARNING: Using incubator modules: jdk.incubator.vector");
    }

    static boolean moduleExists(String name) {
        return java.lang.ModuleLayer.boot().findModule(name).isPresent();
    }
}
```

**How to run:** `java IncubatorCheck.java` (no `--add-modules` needed — just probes)

To actually use the Vector API: `java --add-modules jdk.incubator.vector IncubatorCheck.java`.

### Level 2 — Intermediate

Same incubator probe extended to show what happens with and without `--add-modules` — and if the module is present, demonstrate a simple vectorised array sum.

```java
// VectorApiDemo.java
// Run: java --add-modules jdk.incubator.vector VectorApiDemo.java
// Without --add-modules: scalar path runs, vector path is skipped
public class VectorApiDemo {

    static final boolean VECTOR_AVAILABLE;

    static {
        boolean v = false;
        try {
            Class.forName("jdk.incubator.vector.VectorSpecies");
            v = true;
        } catch (ClassNotFoundException e) { /* not available */ }
        VECTOR_AVAILABLE = v;
    }

    // Scalar array sum (always available)
    static long scalarSum(int[] data) {
        long sum = 0;
        for (int x : data) sum += x;
        return sum;
    }

    public static void main(String[] args) {
        int N = 1_000_000;
        int[] data = new int[N];
        for (int i = 0; i < N; i++) data[i] = i % 100;

        System.out.println("Java version   : " + Runtime.version());
        System.out.println("Vector API     : " + (VECTOR_AVAILABLE ? "available (--add-modules jdk.incubator.vector)" : "NOT loaded"));
        System.out.println();

        // Scalar path
        long t0 = System.nanoTime();
        long scalarResult = scalarSum(data);
        long scalarMs = (System.nanoTime() - t0) / 1_000_000;
        System.out.printf("Scalar sum: %-15d in %dms%n", scalarResult, scalarMs);

        if (!VECTOR_AVAILABLE) {
            System.out.println("\nVector path skipped. Add --add-modules jdk.incubator.vector to enable.");
        } else {
            System.out.println("Vector path: available — see VectorApiAdvanced for implementation.");
        }
    }
}
```

**How to run:** `java --add-modules jdk.incubator.vector VectorApiDemo.java`

The `static {}` block tries `Class.forName` reflectively — this is how you safely degrade at runtime if the module wasn't added.

### Level 3 — Advanced

Same scenario grown to actually use the Vector API to compute a vectorised dot product, comparing it to the scalar version and showing the incubator warning.

```java
// VectorDotProduct.java
// Run: java --add-modules jdk.incubator.vector VectorDotProduct.java
import jdk.incubator.vector.*;

public class VectorDotProduct {
    // Use preferred species for this CPU's native SIMD width (128/256/512-bit)
    static final VectorSpecies<Float> SPECIES = FloatVector.SPECIES_PREFERRED;

    static float scalarDot(float[] a, float[] b) {
        float sum = 0;
        for (int i = 0; i < a.length; i++) sum += a[i] * b[i];
        return sum;
    }

    static float vectorDot(float[] a, float[] b) {
        int i = 0;
        int upperBound = SPECIES.loopBound(a.length);  // largest multiple of lane count
        FloatVector acc = FloatVector.zero(SPECIES);

        // Vectorised loop: processes SPECIES.length() elements per iteration
        for (; i < upperBound; i += SPECIES.length()) {
            FloatVector va = FloatVector.fromArray(SPECIES, a, i);
            FloatVector vb = FloatVector.fromArray(SPECIES, b, i);
            acc = va.fma(vb, acc);   // fused multiply-add: acc += va * vb
        }
        float sum = acc.reduceLanes(VectorOperators.ADD);

        // Scalar tail for remaining elements (if length not a multiple of lane count)
        for (; i < a.length; i++) sum += a[i] * b[i];
        return sum;
    }

    public static void main(String[] args) {
        // The JVM emits: WARNING: Using incubator modules: jdk.incubator.vector
        System.out.println("Vector species : " + SPECIES);
        System.out.println("Lane count     : " + SPECIES.length() + " floats per SIMD register");
        System.out.println("Bit width      : " + SPECIES.vectorBitSize() + " bits");
        System.out.println();

        int N = 2_000_000;
        float[] a = new float[N], b = new float[N];
        for (int i = 0; i < N; i++) { a[i] = (float)(i % 100) / 100f; b[i] = 1f; }

        // Warm up JIT
        for (int w = 0; w < 10; w++) { scalarDot(a, b); vectorDot(a, b); }

        // Measure
        int ROUNDS = 5;
        long scalarTotal = 0, vectorTotal = 0;
        float scalarResult = 0, vectorResult = 0;
        for (int r = 0; r < ROUNDS; r++) {
            long t0 = System.nanoTime(); scalarResult = scalarDot(a, b); scalarTotal += System.nanoTime() - t0;
            long t1 = System.nanoTime(); vectorResult = vectorDot(a, b); vectorTotal += System.nanoTime() - t1;
        }

        System.out.printf("Scalar dot product : %.2f  avg=%dms%n", scalarResult, scalarTotal/(ROUNDS*1_000_000));
        System.out.printf("Vector dot product : %.2f  avg=%dms%n", vectorResult, vectorTotal/(ROUNDS*1_000_000));
        System.out.printf("Speedup            : %.1fx%n",
            vectorTotal > 0 ? (double)scalarTotal / vectorTotal : 1.0);
        System.out.println();
        System.out.println("Note: jdk.incubator.vector is still incubating — expect the warning.");
        System.out.println("Production use: accept the warning or wait for standardisation.");
    }
}
```

**How to run:** `java --add-modules jdk.incubator.vector VectorDotProduct.java`

The JVM prints `WARNING: Using incubator modules: jdk.incubator.vector` before any output. This warning is intentional — it is the JVM telling you "this API is experimental." On a 256-bit SIMD CPU (most modern x86-64), `SPECIES.length()` is 8 floats, so the vector loop processes 8 elements per iteration vs the scalar loop's 1.

## 6. Walkthrough

Execution in `VectorDotProduct.main`:

1. **`FloatVector.SPECIES_PREFERRED`** — queries the JVM for the widest SIMD register the current CPU supports. On AVX2 (most modern Intel/AMD), this is 256 bits = 8 `float` lanes. On ARM NEON it's 128 bits = 4 lanes. On an old SSE2-only CPU it's 128 bits = 4 lanes.

2. **`SPECIES.loopBound(N)`** — returns the largest `i` such that `i + SPECIES.length() <= N`. This ensures the vectorised loop never reads past the array end. The remaining `N - upperBound` elements are processed by the scalar tail.

3. **`FloatVector.fromArray(SPECIES, a, i)`** — loads `SPECIES.length()` floats from array `a` starting at index `i` into a SIMD register. This is a single SIMD load instruction on x86 (VMOVUPS).

4. **`va.fma(vb, acc)`** — fused multiply-add: `acc = acc + va * vb` as a single SIMD instruction (VFMADD on AVX). Critically, this is done for all `SPECIES.length()` lanes simultaneously — one instruction, multiple data.

5. **`acc.reduceLanes(VectorOperators.ADD)`** — horizontally sums all lanes of `acc` into a single float. After the loop, this combines the partial sums from all SIMD lanes.

6. **Warm-up** — 10 rounds before measurement prime HotSpot's JIT to compile both methods. Without warm-up, the first measurement round shows interpreter performance.

Performance flow:
```
Array a[0..N-1], b[0..N-1]
  → Vector loop: processes 8 elements/iteration (256-bit SIMD)
      va = [a[i], a[i+1], ..., a[i+7]]
      vb = [b[i], b[i+1], ..., b[i+7]]
      acc += va * vb   (8 multiply-adds in one CPU instruction)
  → reduceLanes: acc[0]+acc[1]+...+acc[7]
  → Scalar tail: 0-7 remaining elements
= dot product (same numerical result as scalar)
```

## 7. Gotchas & takeaways

> **The incubator warning goes to stderr, not stdout.** Redirecting stdout to a file will still show the warning in the terminal. Suppress it with `--add-modules jdk.incubator.vector` in a `module-info.java` (adds it without the warning in modular apps) or accept it as expected.

> **Do not ship production libraries that `require jdk.incubator.vector` in `module-info.java`.** If the module is promoted (renamed) or dropped in the next release, your `module-info.java` breaks. Use `--add-modules` at launch time or guard with `Class.forName` reflection.

- Incubator modules live in `jdk.incubator.*`; require `--add-modules jdk.incubator.X` at compile and run time.
- The JVM emits a warning when incubator modules are loaded — this is intentional and expected.
- The Vector API (`jdk.incubator.vector`) is the longest-running incubator; use it for SIMD-level performance in numeric code.
- Preview feature = language experiment; incubator module = API experiment. Same idea, different level.
- List available incubator modules: `java --list-modules | grep incubator`.
- Historical path: `jdk.incubator.httpclient` (Java 9–10) → `java.net.http` (Java 11) — same pattern expected for Vector API.
