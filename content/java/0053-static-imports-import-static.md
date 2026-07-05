---
card: java
gi: 53
slug: static-imports-import-static
title: Static imports (import static)
---

## 1. What it is

**`import static`** imports a **static member** (field or method) of a class so you can use it by its short name without the class prefix:

```java
// Without static import
double r = Math.sqrt(Math.pow(3, 2) + Math.pow(4, 2));

// With static import
import static java.lang.Math.sqrt;
import static java.lang.Math.pow;
double r = sqrt(pow(3, 2) + pow(4, 2));
```

`import static` was added in Java 5. It only works for `static` members — instance methods and fields cannot be statically imported.

## 2. Why & when

Use `import static` when:
- **Mathematical code** — `sqrt`, `abs`, `PI`, `log` from `Math` without the `Math.` prefix.
- **JUnit assertions** — `assertEquals(expected, actual)` instead of `Assertions.assertEquals(...)`.
- **Named constants** — `HttpStatus.OK` → import the constant directly.
- **Enum values in switch** — import enum constants for cleaner `case` clauses.

Avoid `import static` when:
- The origin of the method/constant isn't obvious without the class prefix.
- Importing from multiple classes creates ambiguity about which `sort` or `max` is being called.
- It's used just to save typing — clarity matters more than brevity.

Rule of thumb: static imports improve readability for well-known APIs (Math, Assertions), but obscure it for domain-specific helpers.

## 3. Core concept

```java
// Syntax
import static <package>.<Class>.<member>;       // specific member
import static <package>.<Class>.*;              // all static members (wildcard)

// Examples
import static java.lang.Math.PI;               // constant
import static java.lang.Math.sqrt;             // method
import static java.lang.Math.*;                // all Math constants & methods
import static java.util.Collections.sort;      // static method
import static java.util.Collections.emptyList; // static method
import static org.junit.jupiter.api.Assertions.*;  // JUnit assertion methods
import static java.nio.file.StandardOpenOption.*;  // enum constants

// Enum constants
import static java.time.DayOfWeek.MONDAY;
import static java.time.DayOfWeek.FRIDAY;
// Then: if (day == MONDAY) { ... }

// Constants
import static java.lang.System.out;     // import System.out
// Then: out.println("hello");          // rare — confusing

// Wildcard on enum:
import static java.nio.file.StandardOpenOption.*;
// Then: Files.write(path, data, CREATE, TRUNCATE_EXISTING, WRITE);
// Instead of: Files.write(path, data, StandardOpenOption.CREATE, ...);
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="import static resolves static member names at compile time, allowing usage without class prefix">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>

  <!-- Without import static -->
  <rect x="20" y="20" width="310" height="130" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="175" y="40" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Without import static</text>
  <text x="35" y="60"  fill="#8b949e" font-size="8" font-family="monospace">// no import needed for Math (java.lang)</text>
  <text x="35" y="76"  fill="#e6edf3" font-size="9" font-family="monospace">double c = Math.sqrt(</text>
  <text x="35" y="89"  fill="#e6edf3" font-size="9" font-family="monospace">    Math.pow(a, 2) +</text>
  <text x="35" y="102" fill="#e6edf3" font-size="9" font-family="monospace">    Math.pow(b, 2));</text>
  <text x="35" y="117" fill="#8b949e" font-size="8" font-family="monospace">assertEquals(5.0, Math.round(c));</text>
  <text x="35" y="138" fill="#8b949e" font-size="7" font-family="sans-serif">class prefix required everywhere</text>

  <!-- With import static -->
  <rect x="350" y="20" width="330" height="130" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="515" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">With import static</text>
  <text x="365" y="57"  fill="#79c0ff" font-size="9" font-family="monospace">import static java.lang.Math.*;</text>
  <text x="365" y="70"  fill="#79c0ff" font-size="9" font-family="monospace">import static org.junit.jupiter</text>
  <text x="365" y="82"  fill="#79c0ff" font-size="9" font-family="monospace">  .api.Assertions.assertEquals;</text>
  <text x="365" y="100" fill="#e6edf3" font-size="9" font-family="monospace">double c = sqrt(</text>
  <text x="365" y="113" fill="#e6edf3" font-size="9" font-family="monospace">    pow(a, 2) + pow(b, 2));</text>
  <text x="365" y="126" fill="#e6edf3" font-size="9" font-family="monospace">assertEquals(5.0, round(c));</text>
  <text x="365" y="143" fill="#6db33f" font-size="7" font-family="sans-serif">cleaner for known APIs</text>
</svg>

`import static` is a compile-time alias. The compiler resolves `sqrt(...)` to `Math.sqrt(...)` in bytecode — identical to writing `Math.sqrt(...)` by hand.

## 5. Runnable example

Scenario: a geometry calculation library that uses `Math` constants and methods, with test-style assertions using `import static`.

### Level 1 — Basic

```java
// StaticImportBasic.java — Math methods and constants via import static
import static java.lang.Math.PI;
import static java.lang.Math.sqrt;
import static java.lang.Math.pow;
import static java.lang.Math.abs;
import static java.lang.Math.round;

public class StaticImportBasic {
    public static void main(String[] args) {
        System.out.println("=== Static import demo: geometry ===\n");

        // Circle
        double radius = 5.0;
        double circumference = 2 * PI * radius;
        double area          = PI * pow(radius, 2);
        System.out.printf("Circle (r=%.1f):%n", radius);
        System.out.printf("  Circumference: %.4f%n", circumference);
        System.out.printf("  Area:          %.4f%n", area);

        // Right triangle (Pythagorean theorem)
        double a = 3.0, b = 4.0;
        double hypotenuse = sqrt(pow(a, 2) + pow(b, 2));
        System.out.printf("%nTriangle (a=%.1f, b=%.1f):%n", a, b);
        System.out.printf("  Hypotenuse: %.4f%n", hypotenuse);

        // Comparison (abs for distance)
        double x1 = 2.0, x2 = 7.5;
        double distance = abs(x2 - x1);
        System.out.printf("%nDistance from %.1f to %.1f: %.1f%n", x1, x2, distance);

        // Rounding
        System.out.printf("PI rounded: %d%n", round(PI));

        System.out.println("\n[ Without static import these would be: ]");
        System.out.println("  Math.PI, Math.sqrt(...), Math.pow(...), Math.abs(...), Math.round(...)");
        System.out.println("  Same bytecode — purely a source-level convenience.");
    }
}
```

**How to run:** `java StaticImportBasic.java`

`PI`, `sqrt`, `pow`, `abs`, `round` all resolve to `Math.*` via static import. The bytecode is identical to writing `Math.PI`, `Math.sqrt(...)`, etc. The only difference is readability — for math-heavy code this is significant.

### Level 2 — Intermediate

Same geometry scenario extended with enum constant imports and `Collections` static methods — two more common static import patterns.

```java
// StaticImportEnum.java — enum constants + Collections via static import
import static java.util.Collections.sort;
import static java.util.Collections.unmodifiableList;
import static java.util.Collections.max;
import static java.util.Collections.min;
import static java.lang.Math.*;
import static java.time.DayOfWeek.MONDAY;
import static java.time.DayOfWeek.FRIDAY;
import static java.time.DayOfWeek.SATURDAY;
import static java.time.DayOfWeek.SUNDAY;

import java.util.*;
import java.time.*;

public class StaticImportEnum {

    enum Shape { CIRCLE, TRIANGLE, SQUARE, HEXAGON }

    public static void main(String[] args) {
        System.out.println("=== Static import: enum + Collections ===\n");

        // --- Enum constants ---
        DayOfWeek today = LocalDate.now().getDayOfWeek();
        boolean isWeekend = (today == SATURDAY || today == SUNDAY);
        boolean isWeekday = (today == MONDAY || today == FRIDAY);

        System.out.println("Today is: " + today);
        System.out.println("Weekend: " + isWeekend);
        System.out.println("Mon or Fri: " + isWeekday);

        // --- Collections static methods ---
        List<Double> areas = new ArrayList<>();
        areas.add(PI * pow(5, 2));   // circle r=5
        areas.add(0.5 * 3 * 4);     // triangle
        areas.add(pow(6, 2));        // square side=6
        areas.add(3 * sqrt(3) / 2 * pow(4, 2)); // hexagon side=4

        sort(areas);   // instead of Collections.sort(areas)
        System.out.println("\nAreas sorted: " + areas.stream()
            .map(a -> String.format("%.2f", a)).toList());
        System.out.printf("Smallest: %.2f%n", min(areas));  // instead of Collections.min
        System.out.printf("Largest:  %.2f%n", max(areas));

        // Immutable view
        List<Double> immutable = unmodifiableList(areas);
        System.out.println("Immutable: " + immutable.size() + " items");

        // --- Without static import these would be: ---
        System.out.println("\n[ Without static import ]");
        System.out.println("  DayOfWeek.SATURDAY, DayOfWeek.SUNDAY");
        System.out.println("  Collections.sort(...), Collections.min(...), Collections.max(...)");
        System.out.println("  Collections.unmodifiableList(...)");
    }
}
```

**How to run:** `java StaticImportEnum.java`

Importing `DayOfWeek` enum constants (`MONDAY`, `FRIDAY`, `SATURDAY`, `SUNDAY`) makes the `if` conditions read like natural language: `today == SATURDAY || today == SUNDAY`. This is the most readable use case for static imports.

### Level 3 — Advanced

Same geometry scenario grown to simulate a JUnit-style test class where static imports from `Assertions` and `Math` make the test code concise and readable — the production pattern.

```java
// StaticImportAssertions.java — JUnit-style assertions with static imports
import static java.lang.Math.*;

// Simulating JUnit Assertions (without depending on JUnit)
public class StaticImportAssertions {

    // Our minimal assertion library (simulates JUnit)
    static class Assert {
        static int passCount = 0, failCount = 0;

        static void assertEquals(double expected, double actual, double delta, String msg) {
            if (abs(expected - actual) <= delta) {
                passCount++;
                System.out.printf("  PASS: %s (expected=%.4f actual=%.4f)%n", msg, expected, actual);
            } else {
                failCount++;
                System.out.printf("  FAIL: %s (expected=%.4f actual=%.4f diff=%.4f)%n",
                    msg, expected, actual, abs(expected - actual));
            }
        }

        static void assertEquals(double expected, double actual, String msg) {
            assertEquals(expected, actual, 1e-10, msg);
        }

        static void assertTrue(boolean condition, String msg) {
            if (condition) { passCount++; System.out.println("  PASS: " + msg); }
            else           { failCount++; System.out.println("  FAIL: " + msg); }
        }

        static void summary() {
            System.out.printf("%n=== Results: %d passed, %d failed ===%n", passCount, failCount);
        }
    }

    // Static import from our Assert class would require it to be in a separate file.
    // Using direct calls here to show the pattern; in real JUnit:
    // import static org.junit.jupiter.api.Assertions.*;

    // Geometry functions under test
    static double circleArea(double r)      { return PI * pow(r, 2); }
    static double hypotenuse(double a, double b) { return sqrt(pow(a, 2) + pow(b, 2)); }
    static double hexagonArea(double side)  { return 3 * sqrt(3) / 2 * pow(side, 2); }
    static double circleCircumference(double r)  { return 2 * PI * r; }

    public static void main(String[] args) {
        System.out.println("=== Geometry test suite (static import demo) ===\n");

        // Math static imports used throughout — no Math. prefix needed
        double DELTA = 1e-6;

        // Circle
        Assert.assertEquals(PI * 25,            circleArea(5),          DELTA, "circleArea(5)");
        Assert.assertEquals(2 * PI * 5,         circleCircumference(5), DELTA, "circleCircumference(5)");
        Assert.assertEquals(PI * 0,             circleArea(0),          DELTA, "circleArea(0)");

        // Pythagorean triples
        Assert.assertEquals(5.0,                hypotenuse(3, 4),       DELTA, "3-4-5 triangle");
        Assert.assertEquals(13.0,               hypotenuse(5, 12),      DELTA, "5-12-13 triangle");
        Assert.assertEquals(sqrt(2),            hypotenuse(1, 1),       DELTA, "isoceles 45-45-90");
        Assert.assertEquals(2.0,                hypotenuse(sqrt(3), 1), DELTA, "30-60-90");

        // Hexagon
        Assert.assertEquals(3 * sqrt(3) / 2 * 16, hexagonArea(4), DELTA, "hexagonArea(4)");

        // Math constants
        Assert.assertTrue(abs(PI - 3.14159265) < 1e-7, "PI precision");
        Assert.assertTrue(abs(E  - 2.71828182) < 1e-7, "E precision");
        Assert.assertTrue(pow(2, 10) == 1024, "2^10 == 1024");
        Assert.assertTrue(floor(3.9) == 3.0, "floor(3.9)");
        Assert.assertTrue(ceil(3.1)  == 4.0, "ceil(3.1)");
        Assert.assertTrue(max(3, 7)  == 7,   "max(3,7)");
        Assert.assertTrue(min(3, 7)  == 3,   "min(3,7)");

        Assert.summary();

        System.out.println("\n[ In real JUnit tests the pattern is: ]");
        System.out.println("  import static org.junit.jupiter.api.Assertions.*;");
        System.out.println("  import static java.lang.Math.*;");
        System.out.println();
        System.out.println("  @Test void testCircleArea() {");
        System.out.println("    assertEquals(PI * 25, circleArea(5), 1e-6);");
        System.out.println("  }");
        System.out.println();
        System.out.println("  // No 'Math.' or 'Assertions.' prefix needed — clean and readable");
    }
}
```

**How to run:** `java StaticImportAssertions.java`

In real JUnit 5 tests, `import static org.junit.jupiter.api.Assertions.*` makes `assertEquals`, `assertTrue`, `assertThrows`, etc. callable without the `Assertions.` prefix — the dominant reason `import static` exists in modern Java code.

## 6. Walkthrough

Execution trace in `StaticImportAssertions.main`:

**Import resolution.** `import static java.lang.Math.*` imports all public static fields and methods from `Math`: `PI`, `E`, `sqrt`, `pow`, `abs`, `floor`, `ceil`, `max`, `min`, `round`, `log`, `sin`, `cos`, `tan`, etc.

**`circleArea(5)`.** Calls `PI * pow(r, 2)`. After static import, both `PI` and `pow` are bare names. `javac` resolves them to `Math.PI` and `Math.pow(r, 2)` — the bytecode contains `getstatic java/lang/Math.PI` and `invokestatic java/lang/Math.pow`.

**`hypotenuse(3, 4)`.** Computes `sqrt(pow(3, 2) + pow(4, 2)) = sqrt(9 + 16) = sqrt(25) = 5.0`. The static import makes this formula read like a math textbook — exactly the readability benefit intended.

**`Assert.assertEquals(expected, actual, delta, msg)`.** Calls `abs(expected - actual) <= delta` — `abs` is the static-imported `Math.abs`. If the check passes, `passCount++` and a `PASS` line is printed. If not, `failCount++` and a `FAIL` line is printed.

**Ambiguity resolution.** If two different `import static` statements imported a method with the same name (e.g., both `import static java.util.Collections.sort` and `import static java.util.Arrays.sort`), the compiler would produce an error on the `sort(...)` call. You'd need to qualify it: `Collections.sort(...)` or `Arrays.sort(...)`.

## 7. Gotchas & takeaways

> **Wildcard static imports (`import static Math.*`) can cause silent ambiguity.** If you have `import static java.lang.Math.*` and also define a local method named `abs`, the local method shadows the static import. No error — just confusing behaviour. Explicit single-member static imports (`import static java.lang.Math.abs`) make the source of each name unambiguous.

> **`import static System.out` is legal but almost always wrong.** `out.println("hello")` is shorter but baffling to anyone who hasn't seen it before. The confusion cost far outweighs the brevity gain — `System.out.println` is clear; `out.println` is a puzzle.

- Best use cases: `Math.*`, JUnit `Assertions.*`, enum constants in switch/condition.
- `import static` is compile-time only — same bytecode as the qualified form.
- Ambiguity between two static imports with the same name = compile error.
- A local variable/method with the same name shadows the static import (no warning).
- Avoid `import static` for obscure utility classes — it hides where behaviour comes from.
