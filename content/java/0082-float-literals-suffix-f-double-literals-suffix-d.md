---
card: java
gi: 82
slug: float-literals-suffix-f-double-literals-suffix-d
title: float literals (suffix f) & double literals (suffix d)
---

## 1. What it is

A floating-point literal is a number written with a decimal point, an exponent, or a suffix that makes its type explicit. Without any suffix, a decimal floating-point literal is always a `double`. The `f` (or `F`) suffix forces type `float`; the `d` (or `D`) suffix explicitly marks type `double` (though it is redundant and rarely written).

```java
double d1 = 3.14;       // double — default, no suffix needed
double d2 = 3.14d;      // double — explicit but redundant
float  f1 = 3.14f;      // float  — f suffix required
float  f2 = 3.14F;      // float  — uppercase F, same value
// float bad = 3.14;    // COMPILE ERROR: double cannot be assigned to float without cast
```

Both `float` and `double` literals may use scientific (exponential) notation with `e` or `E`. Hex floating-point literals with the `0x` prefix and `p` exponent are also legal (used in low-level code), but rare.

## 2. Why & when

The suffix matters for three reasons:

1. **Type safety** — `float f = 3.14;` is a compile error because `3.14` is a `double` literal and narrowing from `double` to `float` is not implicit. The `f` suffix is not optional.
2. **Arithmetic promotion** — `1.0f + 2.0f` is `float` arithmetic; `1.0 + 2.0` is `double`. Mixing them widens the `float` to `double`.
3. **Explicit documentation** — writing `3.14d` in a method call that accepts `double` signals deliberate intent, though most developers omit it.

Use `f` for `float` constants in graphics or large numeric arrays. Use plain decimal (implicitly `double`) for all other floating-point work.

## 3. Core concept

```java
// ---- Type defaults ----
double plain    = 1.5;      // double (default)
float  withF    = 1.5f;     // float
double withD    = 1.5d;     // double (explicit, rare)

// ---- Compile error without f ----
// float pi = 3.14159;   // error: incompatible types — possible lossy conversion
float pi = 3.14159f;     // OK

// ---- Precision difference ----
float  fVal = 1.0f / 3.0f;
double dVal = 1.0  / 3.0;
System.out.printf("float  1/3 : %.20f%n", (double) fVal);
System.out.printf("double 1/3 : %.20f%n", dVal);
// float:  0.33333334326744079590
// double: 0.33333333333333331483   (more precise)

// ---- Mixed arithmetic: float + double → double ----
float  a = 1.1f;
double b = 2.2;
double result = a + b;   // a widened to double first
float  fResult = a + 2.2f;   // both float → float result

// ---- Special float/double literals ----
float  fInf  = Float.POSITIVE_INFINITY;   // same as 1.0f / 0.0f
double dInf  = Double.POSITIVE_INFINITY;  // same as 1.0 / 0.0
float  fNaN  = Float.NaN;
double dNaN  = Double.NaN;

// ---- Hex floating-point literals (low-level, rare) ----
double hexFP = 0x1.8p1;   // hex mantissa 1.8 × 2^1 = 3.0
System.out.println(hexFP); // 3.0

// ---- Widening / narrowing ----
float  fSmall = 1.23456789f;
double fromF  = fSmall;             // widening: safe, no cast
float  back   = (float) fromF;      // narrowing: explicit cast required
double literal = 1.23456789012345;
float narrow   = (float) literal;   // loses digits
System.out.printf("original double : %.15f%n", literal);
System.out.printf("narrowed float  : %.15f%n", (double) narrow);
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Floating-point literal suffixes: no suffix means double, f/F means float, d/D means double explicitly; precision and mixed arithmetic widening rules">
  <rect x="8" y="8" width="684" height="169" rx="8" fill="#0d1117"/>

  <!-- Token row -->
  <rect x="16" y="18" width="668" height="52" rx="4" fill="#1c2430"/>
  <text x="350" y="33" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Floating-point literal suffixes</text>

  <!-- 3.14 (no suffix) -->
  <rect x="40" y="38" width="120" height="26" rx="3" fill="#6db33f" opacity="0.75"/>
  <text x="100" y="55" fill="#0d1117" font-size="11" font-weight="bold" text-anchor="middle" font-family="monospace">3.14</text>

  <!-- 3.14f -->
  <rect x="180" y="38" width="120" height="26" rx="3" fill="#79c0ff" opacity="0.7"/>
  <text x="240" y="55" fill="#0d1117" font-size="11" font-weight="bold" text-anchor="middle" font-family="monospace">3.14f</text>

  <!-- 3.14d -->
  <rect x="320" y="38" width="120" height="26" rx="3" fill="#8b949e" opacity="0.5"/>
  <text x="380" y="55" fill="#e6edf3" font-size="11" font-weight="bold" text-anchor="middle" font-family="monospace">3.14d</text>

  <!-- 3.14F -->
  <rect x="460" y="38" width="120" height="26" rx="3" fill="#79c0ff" opacity="0.5"/>
  <text x="520" y="55" fill="#0d1117" font-size="11" font-weight="bold" text-anchor="middle" font-family="monospace">3.14F</text>

  <!-- labels -->
  <text x="100" y="76" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">double (default)</text>
  <text x="240" y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">float</text>
  <text x="380" y="76" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">double (explicit)</text>
  <text x="520" y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">float (uppercase)</text>

  <!-- Precision box -->
  <rect x="16" y="90" width="310" height="72" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="171" y="106" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Precision comparison</text>
  <line x1="26" y1="112" x2="316" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="126" fill="#e6edf3" font-size="8" font-family="monospace">float  1/3: 0.3333333_43...</text>
  <text x="26" y="140" fill="#e6edf3" font-size="8" font-family="monospace">double 1/3: 0.3333333_33...</text>
  <text x="26" y="154" fill="#8b949e" font-size="7.5" font-family="monospace">float  ~7 sig digits</text>
  <text x="26" y="167" fill="#8b949e" font-size="7.5" font-family="monospace">double ~15 sig digits</text>

  <!-- Mixed arithmetic box -->
  <rect x="338" y="90" width="346" height="72" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="511" y="106" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Mixed arithmetic widening</text>
  <line x1="348" y1="112" x2="674" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="348" y="126" fill="#e6edf3" font-size="8" font-family="monospace">float  + float  → float</text>
  <text x="348" y="140" fill="#e6edf3" font-size="8" font-family="monospace">float  + double → double</text>
  <text x="348" y="154" fill="#e6edf3" font-size="8" font-family="monospace">double + double → double</text>
  <text x="348" y="167" fill="#8b949e" font-size="7.5" font-family="monospace">float → double widening: safe</text>
</svg>

A bare decimal literal is `double`; the `f`/`F` suffix is mandatory for `float`; mixing `float` and `double` in an expression widens the `float` to `double`.

## 5. Runnable example

Scenario: a physics simulation that tracks the position of a particle — the same computation is performed in `float` and `double` to compare accumulated precision loss, growing from simple position update, to tracking divergence over many steps, to a benchmark of `float[]` vs `double[]` memory and speed.

### Level 1 — Basic

```java
public class FloatDoubleLiteralsBasic {
    public static void main(String[] args) {
        // Step size and acceleration as typed literals
        float  dtF  = 0.016f;     // ~60fps frame delta in seconds (float)
        double dtD  = 0.016;      // same value as double
        float  accF = 9.80665f;   // gravity (float)
        double accD = 9.80665;    // gravity (double)

        // Simulate 60 steps
        float  posF = 0.0f;
        double posD = 0.0;
        float  velF = 0.0f;
        double velD = 0.0;

        for (int i = 0; i < 60; i++) {
            velF += accF * dtF;
            posF += velF * dtF;
            velD += accD * dtD;
            posD += velD * dtD;
        }

        System.out.printf("After 60 steps (1 second of simulation):%n");
        System.out.printf("  float  position : %.10f m%n", (double) posF);
        System.out.printf("  double position : %.10f m%n", posD);
        System.out.printf("  difference      : %.2e m%n", Math.abs(posD - posF));
    }
}
```

**How to run:** `java FloatDoubleLiteralsBasic.java`

`0.016f` is a `float` literal — the `f` suffix is required because `0.016` is a `double` and assigning a `double` to `float` requires an explicit cast without the suffix. `9.80665f` similarly. After 60 steps the float and double results diverge by a small but visible amount, demonstrating precision loss accumulated over many additions of `float` values.

### Level 2 — Intermediate

Same particle: extend the simulation to 3 600 steps (one minute) and chart the growing divergence at every 600 steps.

```java
public class FloatDoubleLiteralsIntermediate {
    public static void main(String[] args) {
        float  dtF = 0.016f;
        double dtD = 0.016;
        float  gF  = 9.80665f;
        double gD  = 9.80665;

        float  posF = 0.0f, velF = 0.0f;
        double posD = 0.0,  velD = 0.0;

        System.out.printf("%-8s  %-18s  %-18s  %s%n",
            "Step", "float pos(m)", "double pos(m)", "diff");
        System.out.println("-".repeat(68));

        for (int i = 1; i <= 3_600; i++) {
            velF += gF * dtF;
            posF += velF * dtF;
            velD += gD * dtD;
            posD += velD * dtD;

            if (i % 600 == 0) {
                System.out.printf("%-8d  %-18.6f  %-18.6f  %.2e%n",
                    i, (double) posF, posD, Math.abs(posD - posF));
            }
        }

        // Demonstrate: float literal in a method that expects double
        double area = Math.PI * Math.pow(2.5, 2);        // 2.5 is double
        float  fRad = 2.5f;
        double areaF = Math.PI * Math.pow(fRad, 2);      // fRad widened to double
        System.out.printf("%nCircle area (double literal 2.5) : %.10f%n", area);
        System.out.printf("Circle area (float  literal 2.5f) : %.10f%n", areaF);
        System.out.printf("Difference                         : %.2e%n",
            Math.abs(area - areaF));
    }
}
```

**How to run:** `java FloatDoubleLiteralsIntermediate.java`

`Math.pow(fRad, 2)` takes `double` parameters; `fRad` is widened from `float` to `double` automatically. However, the widened value of `2.5f` is `2.5` exactly (2.5 is representable in both float and double), so the areas are equal here. The simulation columns show increasing divergence between `float` and `double` positions as accumulated rounding errors compound over thousands of steps.

### Level 3 — Advanced

Same simulation: benchmark `float[]` vs `double[]` memory usage and processing time for 1 million position samples, then show the hex floating-point literal for bit-precise constant specification.

```java
public class FloatDoubleLiteralsAdvanced {
    static float[]  simulateFloat(int n, float dt, float g) {
        float[] pos = new float[n];
        float v = 0.0f;
        for (int i = 0; i < n; i++) {
            v += g * dt;
            pos[i] = (i == 0) ? 0.0f : pos[i - 1] + v * dt;
        }
        return pos;
    }

    static double[] simulateDouble(int n, double dt, double g) {
        double[] pos = new double[n];
        double v = 0.0;
        for (int i = 0; i < n; i++) {
            v += g * dt;
            pos[i] = (i == 0) ? 0.0 : pos[i - 1] + v * dt;
        }
        return pos;
    }

    public static void main(String[] args) {
        int N = 1_000_000;

        long t1 = System.nanoTime();
        float[]  fArr = simulateFloat(N, 0.016f, 9.80665f);
        long t2 = System.nanoTime();
        double[] dArr = simulateDouble(N, 0.016, 9.80665);
        long t3 = System.nanoTime();

        System.out.printf("Simulation of %,d steps:%n", N);
        System.out.printf("  float[]  time   : %,d ns%n", t2 - t1);
        System.out.printf("  double[] time   : %,d ns%n", t3 - t2);
        System.out.printf("  float[]  memory : ~%,d KB%n", N * 4 / 1024);
        System.out.printf("  double[] memory : ~%,d KB%n", N * 8 / 1024);
        System.out.printf("  final float pos : %.6f m%n", (double) fArr[N - 1]);
        System.out.printf("  final double pos: %.6f m%n", dArr[N - 1]);
        System.out.printf("  divergence      : %.2e m%n",
            Math.abs(dArr[N - 1] - fArr[N - 1]));

        // Hex floating-point literal: exact bit-level specification
        // 0x1.8p1 = (1 + 8/16) * 2^1 = 1.5 * 2 = 3.0
        double exactThree = 0x1.8p1;
        float  exactHalf  = 0x1.0p-1f;   // 1.0 * 2^-1 = 0.5f
        System.out.printf("%nHex FP: 0x1.8p1  = %.1f%n", exactThree);
        System.out.printf("Hex FP: 0x1.0p-1f = %.1f%n", (double) exactHalf);
    }
}
```

**How to run:** `java FloatDoubleLiteralsAdvanced.java`

`float[]` uses 4 bytes per element; `double[]` uses 8 bytes — so `float[]` halves the memory footprint for the same number of samples. The time difference on modern hardware is often small because memory bandwidth dominates, but `float` arithmetic on SIMD-capable CPUs can process twice as many values per vector operation. The hex floating-point literal `0x1.8p1` uses base-16 mantissa notation: `1.8` in hex is `1 + 8/16 = 1.5`, scaled by `2^1 = 2`, giving exactly `3.0`. Hex FP literals allow exact specification of constants without decimal rounding.

## 6. Walkthrough

Execution trace through `FloatDoubleLiteralsAdvanced.main`:

**`simulateFloat`.** On each iteration `v += g * dt` is `float + float * float`; both `g` and `dt` are `float` literals, so the arithmetic stays in 32-bit. `pos[i] = pos[i-1] + v * dt` stores a 32-bit result. Over 1 000 000 steps, each rounding error is around `ulp(pos[i])`, and they accumulate.

**`simulateDouble`.** Identical logic but `g = 9.80665` and `dt = 0.016` are `double` literals. 64-bit arithmetic produces roughly twice the significant digits per step. The final positions diverge by an amount that grows with step count.

**Memory.** `new float[1_000_000]` allocates `4 × 10⁶ = 4 MB`. `new double[1_000_000]` allocates `8 × 10⁶ = 8 MB`. The `N * 4 / 1024` arithmetic is `int` — overflow-safe here because `4_000_000 / 1024 = 3906`, well within `int` range.

**Hex FP literal `0x1.8p1`.** The compiler parses it as: hex significand `0x1.8` (= `1.5` in decimal) × `2^1`. Result: `3.0`. This notation is especially useful in cryptography, signal processing, and JVM/compiler implementation where exact bit-level constants matter and decimal rounding would be ambiguous.

```
Literal type decision:
  3.14       → double (default, no suffix)
  3.14f      → float  (f suffix)
  3.14F      → float  (uppercase F, same)
  3.14d      → double (explicit, redundant)

Mixed arithmetic:
  float f = 1.1f;
  double d = 2.2;
  f + d  →  (double)f + d  → double result
  f + 2.2f → float result
```

## 7. Gotchas & takeaways

> **`float f = 3.14;` is a compile error.** The literal `3.14` is a `double` and Java does not implicitly narrow `double` to `float`. Write `3.14f` or use an explicit cast `(float) 3.14`.

> **`float f = 0.1f; double d = f;` does NOT give `0.1`.** Widening a `float` to `double` preserves the float's binary representation with trailing zeros in the mantissa — it does not recover the "original" decimal value. `(double) 0.1f` is approximately `0.10000000149011612`, not `0.1`.

- A bare decimal floating-point literal (`3.14`, `1.5e3`) is a `double` by default.
- `f` or `F` suffix → `float`; required, never optional when assigning to a `float`.
- `d` or `D` suffix → `double`; legal but redundant and rarely written.
- `float + double` → `double` (the `float` widens before the operation).
- Narrowing `double → float` requires an explicit cast and may lose precision.
- Hex floating-point literals (`0x1.8p1`) specify exact IEEE 754 bit patterns — useful in low-level numeric code.
