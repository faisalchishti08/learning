---
card: java
gi: 83
slug: scientific-notation-1-5e3
title: Scientific notation (1.5e3)
---

## 1. What it is

Scientific notation in Java allows floating-point literals to be written as a mantissa followed by `e` (or `E`) and a signed integer exponent, meaning "multiply by 10 raised to that power". The literal `1.5e3` means `1.5 × 10³ = 1500.0` and has type `double`. Adding the `f` suffix makes it a `float`.

```java
double speed    = 3.0e8;       // 300,000,000  m/s (speed of light, approx.)
double electron = 1.6e-19;     // 0.00000000000000000016 (electron charge in C)
float  gravity  = 9.8e0f;      // 9.8  (e0 = × 10^0 = × 1)
double avogadro = 6.022e23;    // Avogadro's number
double planck   = 6.626e-34;   // Planck's constant (J·s)
```

The exponent must be a plain integer (no decimal point); the mantissa may be a decimal with or without a decimal point. Both `e` and `E` are accepted.

## 2. Why & when

Scientific notation is the natural way to write:
- Very large numbers (astronomical distances, data sizes in exabytes).
- Very small numbers (nanosecond precision, quantum constants, floating-point tolerances).
- Quantities where the order of magnitude is more meaningful than the exact digit string (`1.0e-9` communicates "1 nanosecond" more clearly than `0.000000001`).

It is equivalent to the standard decimal or hex literal representation — the compiler produces identical bytecode — so it is purely a readability choice. Use it whenever the exponent form makes the physical meaning clearer.

## 3. Core concept

```java
// ---- Syntax variants ----
double a = 1.5e3;     // 1500.0   (double, default)
double b = 1.5E3;     // 1500.0   (E uppercase — identical)
double c = 1.5e+3;    // 1500.0   (explicit positive exponent — same)
double d = 1.5e-3;    // 0.0015   (negative exponent)
float  f = 1.5e3f;    // 1500.0f  (float with e-notation)
double g = 15e2;      // 1500.0   (no decimal point in mantissa)
double h = .5e1;      // 5.0      (leading dot OK)

// ---- Order of magnitude examples ----
double lightSpeed = 2.998e8;     // m/s
double earthMass  = 5.972e24;    // kg
double nanometer  = 1.0e-9;      // m
double pico       = 1.0e-12;     // m

System.out.printf("Speed of light : %.3e m/s%n", lightSpeed);
System.out.printf("Earth mass     : %.3e kg%n",  earthMass);
System.out.printf("Nanometer      : %.3e m%n",   nanometer);

// ---- e-notation in arithmetic ----
double area      = 3.14159 * (1.0e-3 * 1.0e-3);  // circle area, r = 1mm
System.out.printf("Circle area (r=1mm): %.3e m²%n", area);

// ---- Type rules (same as plain literals) ----
double plain = 6.022e23;   // double
float  flit  = 6.022e23f;  // float (loses precision — Avogadro as float)
System.out.printf("double Avogadro: %.6e%n", plain);
System.out.printf("float  Avogadro: %.6e%n", (double) flit);

// ---- Epsilon comparisons ----
double computed = 1.0 / 3.0 * 3.0;
double expected = 1.0;
boolean close   = Math.abs(computed - expected) < 1.0e-9;
System.out.println("1/3 * 3 ≈ 1.0 : " + close);  // true

// ---- %e format ----
System.out.printf("%.4e%n", 123_456.789);   // 1.2346e+05
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scientific notation anatomy: mantissa × 10^exponent, with examples of positive and negative exponents on a number line">
  <rect x="8" y="8" width="684" height="169" rx="8" fill="#0d1117"/>

  <!-- Token anatomy -->
  <rect x="16" y="18" width="668" height="52" rx="4" fill="#1c2430"/>
  <text x="350" y="33" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Scientific notation anatomy: 6.022e23</text>

  <!-- mantissa -->
  <rect x="80" y="38" width="100" height="26" rx="3" fill="#79c0ff" opacity="0.7"/>
  <text x="130" y="55" fill="#0d1117" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">6.022</text>

  <!-- e -->
  <rect x="184" y="38" width="28" height="26" rx="3" fill="#6db33f" opacity="0.9"/>
  <text x="198" y="55" fill="#0d1117" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">e</text>

  <!-- exponent -->
  <rect x="216" y="38" width="55" height="26" rx="3" fill="#8b949e" opacity="0.55"/>
  <text x="243" y="55" fill="#e6edf3" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">23</text>

  <!-- labels -->
  <text x="130"  y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">mantissa</text>
  <text x="198"  y="76" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">'e' marker</text>
  <text x="243"  y="76" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">×10²³</text>
  <text x="450"  y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">= 6.022 × 10²³ = 602 200 000 000 000 000 000 000</text>

  <!-- number line -->
  <rect x="16" y="90" width="668" height="72" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="350" y="106" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Magnitude scale — powers of 10</text>

  <line x1="36" y1="130" x2="664" y2="130" stroke="#8b949e" stroke-width="1.5"/>
  <!-- ticks and labels -->
  <line x1="80"  y1="125" x2="80"  y2="135" stroke="#8b949e" stroke-width="1"/>
  <text x="80"  y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">10⁻¹²</text>
  <text x="80"  y="158" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">pico</text>

  <line x1="170" y1="125" x2="170" y2="135" stroke="#8b949e" stroke-width="1"/>
  <text x="170" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">10⁻⁹</text>
  <text x="170" y="158" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">nano</text>

  <line x1="260" y1="125" x2="260" y2="135" stroke="#8b949e" stroke-width="1"/>
  <text x="260" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">10⁻⁶</text>
  <text x="260" y="158" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">micro</text>

  <line x1="350" y1="118" x2="350" y2="135" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="148" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">10⁰</text>
  <text x="350" y="158" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">1.0</text>

  <line x1="440" y1="125" x2="440" y2="135" stroke="#8b949e" stroke-width="1"/>
  <text x="440" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">10⁶</text>
  <text x="440" y="158" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">mega</text>

  <line x1="530" y1="125" x2="530" y2="135" stroke="#8b949e" stroke-width="1"/>
  <text x="530" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">10⁹</text>
  <text x="530" y="158" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">giga</text>

  <line x1="620" y1="125" x2="620" y2="135" stroke="#8b949e" stroke-width="1"/>
  <text x="620" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">10¹²</text>
  <text x="620" y="158" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">tera</text>
</svg>

`1.5e3` means `1.5 × 10³`; `e` followed by a positive integer shifts the decimal right, a negative integer shifts it left, spanning from quantum-scale constants to astronomical distances.

## 5. Runnable example

Scenario: a unit converter for physics constants — converts between SI units using scientific notation for tolerances, constants, and display. The example grows from simple magnitude conversion, to epsilon-based equality for computed results, to a comprehensive constants table with formatted scientific output.

### Level 1 — Basic

```java
public class ScientificNotationBasic {
    // Physical constants in SI units, expressed in scientific notation
    static final double SPEED_OF_LIGHT   = 2.998e8;   // m/s
    static final double ELECTRON_CHARGE  = 1.602e-19;  // C
    static final double AVOGADRO         = 6.022e23;   // mol^-1
    static final double PLANCK           = 6.626e-34;  // J·s

    public static void main(String[] args) {
        System.out.println("=== Physical constants ===");
        System.out.printf("Speed of light : %.3e m/s%n",  SPEED_OF_LIGHT);
        System.out.printf("Electron charge: %.3e C%n",    ELECTRON_CHARGE);
        System.out.printf("Avogadro       : %.3e mol⁻¹%n", AVOGADRO);
        System.out.printf("Planck         : %.3e J·s%n",  PLANCK);

        // Light travel time across 1 AU (1.496e11 m)
        double au     = 1.496e11;   // 1 astronomical unit in metres
        double tSec   = au / SPEED_OF_LIGHT;
        System.out.printf("%nLight travel time across 1 AU: %.1f minutes%n",
            tSec / 60.0);
    }
}
```

**How to run:** `java ScientificNotationBasic.java`

`2.998e8` compiles to the same `double` value as `299800000.0` — scientific notation is a source-code convenience, not a different numeric type. `1.496e11 / 2.998e8` is computed in normal `double` arithmetic. The result `tSec` is approximately 499 seconds, or about 8.3 minutes. `%.3e` in `printf` formats the output in scientific notation with 3 decimal places in the mantissa.

### Level 2 — Intermediate

Same converter: add unit-scale factors and demonstrate epsilon-based comparison for verifying computed values against known constants.

```java
public class ScientificNotationIntermediate {
    static final double C  = 2.998e8;    // speed of light m/s
    static final double H  = 6.626e-34;  // Planck constant
    static final double KB = 1.381e-23;  // Boltzmann constant J/K

    // Photon energy: E = h * c / λ
    static double photonEnergy(double wavelengthM) {
        return H * C / wavelengthM;
    }

    public static void main(String[] args) {
        // Visible light wavelengths in nm, converted to metres
        double[][] light = {
            {380e-9, 0},  // violet
            {450e-9, 0},  // blue
            {550e-9, 0},  // green
            {700e-9, 0},  // red
        };
        String[] colours = {"violet", "blue  ", "green ", "red   "};

        System.out.printf("%-8s  %-12s  %-14s%n", "Colour", "λ (nm)", "Energy (J)");
        System.out.println("-".repeat(40));
        for (int i = 0; i < light.length; i++) {
            double lambda = light[i][0];
            double energy = photonEnergy(lambda);
            System.out.printf("%-8s  %6.0f nm    %.4e J%n",
                colours[i], lambda * 1e9, energy);
        }

        // Epsilon comparison: verify thermal energy at 300K
        // kT = 1.381e-23 * 300 ≈ 4.143e-21 J
        double kT       = KB * 300.0;
        double expected = 4.143e-21;
        double epsilon  = 1.0e-24;   // tolerance

        System.out.printf("%nkT at 300K : %.4e J%n", kT);
        System.out.printf("expected   : %.4e J%n",   expected);
        System.out.printf("match (ε=%.0e): %b%n", epsilon,
            Math.abs(kT - expected) < epsilon);
    }
}
```

**How to run:** `java ScientificNotationIntermediate.java`

`380e-9` is `380 × 10⁻⁹ = 3.8 × 10⁻⁷` m (380 nm). `lambda * 1e9` converts back to nanometres for display. The epsilon `1.0e-24` is chosen to be about 3 orders of magnitude smaller than the values being compared (`~4e-21`), giving a tolerance that is tight enough to detect significant errors but wide enough to accept floating-point rounding. Choosing epsilon as a fixed constant like `1e-9` is often wrong; it should be proportional to the magnitude of the values compared — this example shows that `1.0e-24` is appropriate for energies on the order of `10⁻²¹`.

### Level 3 — Advanced

Same constants library: build a dimensional-analysis checker that verifies known relationships (like `E = mc²`) and uses scientific notation for tolerances, large products, and `printf` formatting at various precisions.

```java
import java.util.Map;
import java.util.LinkedHashMap;

public class ScientificNotationAdvanced {
    static final double C  = 2.99792458e8;  // exact speed of light
    static final double H  = 6.62607015e-34;
    static final double KB = 1.380649e-23;
    static final double NA = 6.02214076e23; // exact Avogadro (2019 SI)

    // Relative tolerance for comparison (5 significant digits)
    static boolean approxEqual(double a, double b) {
        if (a == 0 && b == 0) return true;
        return Math.abs(a - b) / Math.max(Math.abs(a), Math.abs(b)) < 1.0e-5;
    }

    public static void main(String[] args) {
        // E = m c² for 1 proton (mass 1.67262e-27 kg)
        double protonMass = 1.67262e-27;
        double restEnergy = protonMass * C * C;
        System.out.printf("Proton rest energy E=mc²: %.6e J%n", restEnergy);

        // Gas constant R = NA * KB
        double R         = NA * KB;
        double R_known   = 8.314462;   // J/(mol·K)
        System.out.printf("R = NA*KB : %.6f  known: %.6f  match: %b%n",
            R, R_known, approxEqual(R, R_known));

        // Stefan-Boltzmann from first principles: σ = 2π⁵kB⁴ / (15 h³ c²)
        double numerator   = 2.0 * Math.pow(Math.PI, 5) * Math.pow(KB, 4);
        double denominator = 15.0 * Math.pow(H, 3) * Math.pow(C, 2);
        double sigma       = numerator / denominator;
        double sigma_known = 5.670374e-8;  // W m⁻² K⁻⁴
        System.out.printf("σ (computed) : %.6e%n", sigma);
        System.out.printf("σ (known)    : %.6e%n", sigma_known);
        System.out.printf("match (1e-5) : %b%n", approxEqual(sigma, sigma_known));

        // Printf format comparison
        System.out.println("\n=== printf format options ===");
        double val = 6.62607015e-34;
        System.out.printf("%%e  : %e%n",   val);   // default 6 decimal places
        System.out.printf("%%.3e: %.3e%n", val);   // 3 decimal places
        System.out.printf("%%.10e: %.10e%n", val);  // 10 decimal places
        System.out.printf("%%g  : %g%n",   val);   // general: picks e or f
        System.out.printf("%%f  : %f%n",   val);   // fixed — shows as 0.000000
    }
}
```

**How to run:** `java ScientificNotationAdvanced.java`

`2.99792458e8` is the exact speed of light in metres per second as defined by the 2019 SI. Using more digits in the literal improves the accuracy of any derived calculation. `approxEqual` uses relative tolerance: `|a − b| / max(|a|, |b|) < 1e-5`. This is scale-independent — it works for both tiny and large values. `%g` in `printf` selects between `%e` and `%f` automatically based on the magnitude: for very small or very large values it uses exponential notation; for moderate values it uses fixed notation. `%f` formats `6.626e-34` as `0.000000` because there are not enough decimal places to show any non-zero digits.

## 6. Walkthrough

Execution trace through `ScientificNotationAdvanced.main`:

**`E = mc²`.** `protonMass = 1.67262e-27` is compiled to the nearest 64-bit IEEE 754 `double`. `C = 2.99792458e8`. `C * C = 8.987551787e16`. `protonMass * C * C` is performed left-to-right: `protonMass * C = 5.01070e-19`, then `× C` again. The result is approximately `1.503e-10` J — the rest energy of a proton.

**Gas constant `R`.** `NA * KB = 6.02214076e23 × 1.380649e-23 = 8.31446...`. The multiplication is computed as `double × double`. `approxEqual(8.31446..., 8.314462)` checks relative error: `|8.31446 − 8.31446| / 8.31446 < 1e-5` — true, confirming the constants are mutually consistent to at least 5 significant figures.

**Stefan-Boltzmann constant.** `Math.pow(KB, 4)` = `(1.380649e-23)^4` ≈ `3.627e-92`. `Math.pow(H, 3)` = `(6.62607015e-34)^3` ≈ `2.912e-100`. The numerator `2π⁵ × 3.627e-92` ≈ `7.125e-91`. The denominator `15 × 2.912e-100 × (2.998e8)^2` ≈ `1.256e-82`. The quotient is approximately `5.67e-8`, matching the known value.

**Printf formats.** `%e` always uses exponential notation. `%g` switches between `%e` and `%f` based on magnitude (exponent < −4 or > precision triggers `%e`). For `6.626e-34`, `%f` produces `0.000000` — the value is so small that all 6 decimal places are zero, making `%e` far more informative.

```
E = mc² execution:
  protonMass       = 1.67262e-27 kg
  C                = 2.99792458e8 m/s
  C * C            = 8.987551787368176e16 m²/s²
  protonMass * C²  = 1.50327...e-10 J
  printf %.6e      → 1.503274e-10
```

## 7. Gotchas & takeaways

> **`1e3` is a `double` literal, not an `int`.** Even though `1000` is a whole number, `1e3` is `1000.0` (a `double`). You cannot assign it to an `int` without a cast: `int x = (int) 1e3;`.

> **`%f` for very small scientific-notation values displays only zeros.** `System.out.printf("%f", 1.5e-9)` prints `0.000000`. Use `%e` or `%g` for values that span many orders of magnitude.

- Scientific notation literals use `e` or `E` followed by a signed integer exponent: `1.5e3 = 1500.0`.
- The type is `double` by default; append `f` or `F` for `float`.
- The exponent may be negative (`1.5e-3 = 0.0015`) or carry an explicit `+` sign (`1.5e+3`).
- `%.3e` in `printf` formats a value as scientific notation with 3 decimal places in the mantissa.
- Use relative epsilon comparisons (`|a - b| / max(|a|, |b|) < 1e-5`) when values span many orders of magnitude.
- `1e3` is `double` — not assignable to `int` without an explicit cast.
