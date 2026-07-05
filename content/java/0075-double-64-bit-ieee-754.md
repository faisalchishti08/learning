---
card: java
gi: 75
slug: double-64-bit-ieee-754
title: double (64-bit IEEE-754)
---

## 1. What it is

`double` is Java's double-precision, 64-bit floating-point primitive, defined by the IEEE 754 standard. It allocates 1 sign bit, 11 exponent bits, and 52 mantissa bits, providing roughly 15–16 significant decimal digits of precision and a range of approximately ±5×10⁻³²⁴ to ±1.8×10³⁰⁸. `double` is Java's default floating-point type — a bare decimal literal like `3.14` is a `double`, not a `float`.

```java
double pi      = 3.141592653589793;   // no suffix needed (default)
double avogadro = 6.022e23;           // scientific notation
double nano     = 1.5e-9;            // 1.5 nanoseconds in seconds
```

The boxed wrapper class is `Double`. Like `float`, `double` supports the special values `Double.POSITIVE_INFINITY`, `Double.NEGATIVE_INFINITY`, and `Double.NaN`.

## 2. Why & when

`double` is the workhorse floating-point type in Java:
- Scientific, financial-adjacent (as opposed to exact money), and engineering computations.
- All `Math` library methods take and return `double`.
- `DoubleStream` in the streams API works with `double` values.
- Any situation where `float`'s 7-digit precision is insufficient.

Prefer `double` over `float` unless you have a specific reason to save memory (large arrays) or an API constraint. Still, **never use `double` for monetary values** — binary floating point cannot represent `0.1` exactly, causing rounding errors that compound over financial calculations. Use `BigDecimal` for money.

## 3. Core concept

```java
// ---- Default type: no suffix needed ----
double x = 3.14;      // double literal
float  f = 3.14f;     // float requires f suffix

// ---- Precision: ~15 significant digits ----
double d1 = 1_000_000.5;
double d2 = 1_000_000.4;
System.out.println(d1 - d2);             // 0.09999847412109375  — still imprecise!
System.out.printf("%.15f%n", d1 - d2);  // 0.099998474121093750

double sum = 0.1 + 0.2;
System.out.println(sum);                 // 0.30000000000000004 (NOT 0.3)
System.out.println(sum == 0.3);          // false — never compare doubles with ==

// Safe comparison: use an epsilon (tolerance)
double epsilon = 1e-9;
System.out.println(Math.abs(sum - 0.3) < epsilon);   // true

// ---- Math library ----
System.out.println(Math.sqrt(2.0));      // 1.4142135623730951
System.out.println(Math.sin(Math.PI));   // ~1.22e-16 (not exactly 0.0)
System.out.println(Math.log(Math.E));    // 1.0
System.out.println(Math.pow(2.0, 10.0));// 1024.0

// ---- Special values ----
System.out.println(1.0 / 0.0);           // Infinity
System.out.println(0.0 / 0.0);           // NaN
System.out.println(Double.isNaN(0.0 / 0.0));      // true
System.out.println(Double.isInfinite(1.0 / 0.0)); // true

// ---- Widening / narrowing ----
float  f2  = 3.14f;
double d3  = f2;            // widening: exact, no cast needed
float  f3  = (float) d3;    // narrowing: explicit cast, may lose precision

// ---- Double.compare for correct ordering ----
System.out.println(Double.compare(Double.NaN, 1.0));    // positive (NaN sorts last)
System.out.println(Double.compare(-0.0, 0.0));          // negative (-0.0 < +0.0)

// ---- Bit representation ----
System.out.println(Long.toBinaryString(Double.doubleToLongBits(1.0)));
// 11111110000000000000000000000000000000000000000000000000000000
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="double 64-bit layout: 1 sign bit, 11 exponent bits, 52 mantissa bits, showing precision comparison with float">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>

  <!-- Bit layout -->
  <rect x="16" y="18" width="668" height="52" rx="4" fill="#1c2430"/>
  <text x="350" y="33" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">64-bit double memory layout</text>

  <!-- sign bit -->
  <rect x="24" y="38" width="18" height="26" rx="2" fill="#6db33f" opacity="0.9"/>
  <text x="33" y="53" fill="#0d1117" font-size="7" font-weight="bold" text-anchor="middle" font-family="monospace">S</text>

  <!-- exponent bits (11) -->
  <rect x="46" y="38" width="130" height="26" rx="2" fill="#79c0ff" opacity="0.75"/>
  <text x="111" y="53" fill="#0d1117" font-size="8" font-weight="bold" text-anchor="middle" font-family="monospace">Exponent (11 bits)</text>

  <!-- mantissa bits (52) -->
  <rect x="180" y="38" width="496" height="26" rx="2" fill="#8b949e" opacity="0.5"/>
  <text x="428" y="53" fill="#e6edf3" font-size="8" font-weight="bold" text-anchor="middle" font-family="monospace">Mantissa / Significand (52 bits)</text>

  <!-- labels -->
  <text x="33"  y="80" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="monospace">bit 63</text>
  <text x="111" y="80" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="monospace">bits 62–52</text>
  <text x="428" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">bits 51–0</text>

  <!-- Properties box -->
  <rect x="16" y="92" width="215" height="82" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="123" y="108" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">double range</text>
  <line x1="26" y1="114" x2="221" y2="114" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="127" fill="#e6edf3" font-size="7.5" font-family="monospace">max:  ≈ 1.8 × 10³⁰⁸</text>
  <text x="26" y="141" fill="#e6edf3" font-size="7.5" font-family="monospace">min+: ≈ 5.0 × 10⁻³²⁴</text>
  <text x="26" y="155" fill="#e6edf3" font-size="7.5" font-family="monospace">~15 significant digits</text>
  <text x="26" y="169" fill="#8b949e" font-size="7" font-family="monospace">default (field): 0.0</text>

  <!-- Precision trap box -->
  <rect x="243" y="92" width="215" height="82" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="108" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Precision pitfalls</text>
  <line x1="253" y1="114" x2="448" y2="114" stroke="#8b949e" stroke-width="0.5"/>
  <text x="253" y="127" fill="#e6edf3" font-size="7.5" font-family="monospace">0.1 + 0.2 ≠ 0.3</text>
  <text x="253" y="141" fill="#e6edf3" font-size="7.5" font-family="monospace">never use == to compare</text>
  <text x="253" y="155" fill="#6db33f" font-size="7.5" font-family="monospace">use epsilon: |a-b| &lt; 1e-9</text>
  <text x="253" y="169" fill="#8b949e" font-size="7" font-family="monospace">or BigDecimal for money</text>

  <!-- float vs double box -->
  <rect x="470" y="92" width="214" height="82" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="577" y="108" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">float vs double</text>
  <line x1="480" y1="114" x2="674" y2="114" stroke="#8b949e" stroke-width="0.5"/>
  <text x="480" y="127" fill="#e6edf3" font-size="7.5" font-family="monospace">float:  32-bit, 7 digits, f</text>
  <text x="480" y="141" fill="#e6edf3" font-size="7.5" font-family="monospace">double: 64-bit, 15 digits</text>
  <text x="480" y="155" fill="#6db33f" font-size="7.5" font-family="monospace">double = Java default</text>
  <text x="480" y="169" fill="#8b949e" font-size="7" font-family="monospace">Math.*  all take double</text>
</svg>

`double` allocates 1 sign, 11 exponent, and 52 mantissa bits — twice the mantissa width of `float`, giving about 15 significant decimal digits, but still subject to binary floating-point rounding.

## 5. Runnable example

Scenario: a simple physics simulator for a thrown ball — calculates trajectory, peak height, and landing time. The scenario grows from a basic kinematic formula to detecting numerical edge cases and finally to comparing `double` summation accuracy against `BigDecimal`.

### Level 1 — Basic

```java
public class DoubleBasic {
    static final double G = 9.80665;   // gravitational acceleration m/s²

    public static void main(String[] args) {
        double v0    = 25.0;   // initial velocity m/s
        double angle = 45.0;   // degrees

        // Convert angle to radians
        double rad   = Math.toRadians(angle);
        double vx    = v0 * Math.cos(rad);
        double vy    = v0 * Math.sin(rad);

        double timeOfFlight = 2.0 * vy / G;
        double range        = vx * timeOfFlight;
        double peakHeight   = (vy * vy) / (2.0 * G);

        System.out.printf("Initial velocity : %.2f m/s at %.1f°%n", v0, angle);
        System.out.printf("vx=%.4f m/s  vy=%.4f m/s%n", vx, vy);
        System.out.printf("Time of flight   : %.4f s%n", timeOfFlight);
        System.out.printf("Range            : %.4f m%n", range);
        System.out.printf("Peak height      : %.4f m%n", peakHeight);
    }
}
```

**How to run:** `java DoubleBasic.java`

`Math.toRadians`, `Math.cos`, and `Math.sin` all operate on `double`. `Math.cos(Math.PI / 4.0)` returns `0.7071067811865476` — 15 significant digits, far more than `float` provides. `printf` with `%.4f` rounds the output to 4 decimal places for display, but the underlying computation retains full double precision.

### Level 2 — Intermediate

Same ball simulator: plot the trajectory at discrete time steps, detect the peak, and show how `==` comparison fails on doubles while an epsilon-based comparison succeeds.

```java
public class DoubleIntermediate {
    static final double G = 9.80665;

    static double height(double vy0, double t) {
        return vy0 * t - 0.5 * G * t * t;
    }

    public static void main(String[] args) {
        double v0    = 25.0;
        double angle = Math.toRadians(45.0);
        double vx    = v0 * Math.cos(angle);
        double vy    = v0 * Math.sin(angle);

        double tFlight = 2.0 * vy / G;
        double dt      = tFlight / 10.0;    // 10 steps

        System.out.println("t(s)     x(m)     h(m)");
        System.out.println("-".repeat(32));

        double peakH   = Double.NEGATIVE_INFINITY;
        double peakT   = 0.0;

        for (int i = 0; i <= 10; i++) {
            double t = i * dt;
            double x = vx * t;
            double h = height(vy, t);
            if (h > peakH) { peakH = h; peakT = t; }
            System.out.printf("%.4f   %7.3f  %7.3f%n", t, x, h);
        }
        System.out.printf("%nPeak: h=%.4f m at t=%.4f s%n", peakH, peakT);

        // Demonstrate: == fails for double
        double expected = 0.5 * vy * vy / G;   // expected peak height
        System.out.printf("%nExpected peak h    : %.15f%n", expected);
        System.out.printf("height(vy, peakT)   : %.15f%n", peakH);
        System.out.println("== comparison      : " + (expected == peakH));
        System.out.println("epsilon comparison : "
            + (Math.abs(expected - peakH) < 1e-6));
    }
}
```

**How to run:** `java DoubleIntermediate.java`

`Double.NEGATIVE_INFINITY` initialises `peakH` so any real height — even zero — beats it on the first iteration. The discrete sampling with `dt = tFlight / 10.0` means the time grid may not land exactly at the theoretical peak (`t = vy / G`), so `expected == peakH` will likely be `false` even though the values are numerically close. The epsilon check `Math.abs(expected - peakH) < 1e-6` tolerates this discretisation error.

### Level 3 — Advanced

Same scenario: compare accumulated `double` running-sum error over thousands of steps against `BigDecimal` for a practical illustration of when to reach for exact arithmetic.

```java
import java.math.BigDecimal;
import java.math.MathContext;

public class DoubleAdvanced {
    static final double G = 9.80665;

    public static void main(String[] args) {
        // Sum heights across N tiny time steps and compare to exact answer
        double v0    = 25.0;
        double angle = Math.toRadians(45.0);
        double vy    = v0 * Math.sin(angle);
        double tPeak = vy / G;   // time to peak (theoretical)
        int    N     = 1_000_000;
        double dt    = tPeak / N;

        // naive double accumulation
        double sumDouble = 0.0;
        for (int i = 0; i < N; i++) {
            double t = i * dt;
            double dh = (vy - G * t) * dt;   // incremental height gain
            sumDouble += dh;
        }

        // BigDecimal — exact arithmetic (slow but precise)
        BigDecimal vyBD  = BigDecimal.valueOf(vy);
        BigDecimal gBD   = BigDecimal.valueOf(G);
        BigDecimal dtBD  = BigDecimal.valueOf(dt);
        BigDecimal sumBD = BigDecimal.ZERO;
        for (int i = 0; i < N; i++) {
            BigDecimal t  = BigDecimal.valueOf(i).multiply(dtBD);
            BigDecimal dh = vyBD.subtract(gBD.multiply(t)).multiply(dtBD);
            sumBD = sumBD.add(dh);
        }

        // Theoretical exact peak height: vy^2 / (2G)
        double exact = (vy * vy) / (2.0 * G);

        System.out.printf("Theoretical peak height : %.10f m%n", exact);
        System.out.printf("double sum   (%,d steps): %.10f   error: %.2e%n",
            N, sumDouble, Math.abs(sumDouble - exact));
        System.out.printf("BigDecimal   (%,d steps): %.10f   error: %.2e%n",
            N, sumBD.doubleValue(), Math.abs(sumBD.doubleValue() - exact));

        // Show how doubles get sorted correctly via Double.compare
        System.out.println();
        double[] vals = {Double.NaN, -0.0, 0.0, Double.NEGATIVE_INFINITY,
                         Double.POSITIVE_INFINITY, 1.5, -1.5};
        java.util.Arrays.sort(vals);   // uses Double.compare internally
        System.out.print("Sorted doubles (total order): ");
        for (double v : vals) System.out.printf("%.1f ", v);
        System.out.println();
    }
}
```

**How to run:** `java DoubleAdvanced.java`

Each incremental height step `dh = (vy - G*t) * dt` accumulates in `sumDouble` with a tiny rounding error per step. After 1,000,000 additions the accumulated error is typically on the order of 10⁻⁷. The `BigDecimal` version uses exact decimal arithmetic (to the precision of the `MathContext` or infinite precision for integers) — its accumulated error is essentially zero apart from the conversion to `double` at the end. The sort demonstrates `Double.compare`'s total ordering: `−∞ < negative < −0.0 < +0.0 < positive < +∞ < NaN`. Standard `<` and `>` operators cannot produce this ordering for `-0.0` and `NaN`.

## 6. Walkthrough

Execution trace through `DoubleAdvanced.main`:

**Initialisation.** `vy = 25.0 * Math.sin(Math.toRadians(45.0))` computes `25.0 * 0.7071067811865476 = 17.677669529663688` m/s. `tPeak = 17.677669529663688 / 9.80665 = 1.8027...` s. `dt = tPeak / 1_000_000`.

**Double loop.** On each iteration `t = i * dt` (itself a rounding of the exact value `i * tPeak / N`). `dh = (vy - G * t) * dt` is a first-order approximation to the continuous integral. Each `sumDouble += dh` rounds to 64-bit precision. Over 10⁶ iterations the error compounds but stays small because double has 15 significant digits and the error per step is roughly 10⁻¹⁶ × the value. The total accumulated error is typically O(10⁻⁷) — small but non-zero.

**BigDecimal loop.** `BigDecimal.valueOf(dt)` creates an exact decimal representation of the `double` value of `dt` (not an approximation). Each multiplication and subtraction is performed in exact decimal arithmetic. The final `sumBD.doubleValue()` converts back to `double`, introducing at most one final rounding error. The total error is therefore limited to that final conversion, typically O(10⁻¹⁵).

**Sort.** `Arrays.sort(double[])` calls `Double.compare` as its comparator, which uses a total ordering: `−∞` first, then negative finites in ascending order, then `−0.0`, then `+0.0`, then positive finites, then `+∞`, then `NaN` last. This ordering is consistent and avoids the `==` trap where `NaN` comparisons break sort invariants.

```
double sum loop:
  i=0: t=0,  dh = vy*dt           → sumDouble = vy*dt
  i=1: t=dt, dh = (vy - G*dt)*dt  → sumDouble = 2*vy*dt - G*dt²
  ...
  i=N-1: sum ≈ vy²/(2G) + ε  (ε ≈ 10⁻⁷)

BigDecimal sum loop:
  identical logic but exact arithmetic → sum = vy²/(2G) to BD precision
  .doubleValue() → single final rounding ε ≈ 10⁻¹⁵
```

## 7. Gotchas & takeaways

> **`0.1 + 0.2 != 0.3` in `double`.** Binary floating point cannot represent `0.1` or `0.2` exactly, so their sum has a tiny error. Never use `==` to compare `double` values; use `Math.abs(a - b) < epsilon` with an epsilon appropriate to your domain.

> **`Double.NaN != Double.NaN` — always.** Testing `d == Double.NaN` is a bug that always returns `false`. Use `Double.isNaN(d)` instead.

- `double` is the default floating-point type in Java — decimal literals without a suffix are `double`.
- It provides approximately 15–16 significant decimal digits and a range of ±1.8×10³⁰⁸.
- The special values `Infinity`, `-Infinity`, and `NaN` follow IEEE 754 rules: `NaN` is not equal to anything, including itself.
- Use `Double.compare` for sorting and total-order comparisons; `==` mishandles `NaN` and `-0.0`.
- Use an epsilon-based comparison when checking near-equality of computed values.
- Prefer `double` over `float` for general computation. Use `BigDecimal` for money or when exact decimal arithmetic is required.
- All `java.lang.Math` methods take and return `double`.
