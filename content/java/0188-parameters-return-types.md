---
card: java
gi: 188
slug: parameters-return-types
title: Parameters & return types
---

## 1. What it is

**Parameters** are the named inputs a method declares in its parentheses — values the caller supplies each time the method is invoked. The **return type** is the type of value the method hands back to its caller via a `return` statement, declared just before the method's name; a method that produces no value at all declares `void` and needs no `return` value (though a bare `return;` may still be used to exit early).

```java
//      return type   name    parameters
static  double        area(   double width, double height  ) {
    return width * height; // must match the declared return type, double
}
```

Every parameter has a declared type and a name; every non-`void` method must return a value matching its declared return type on *every* possible execution path, or the code fails to compile.

## 2. Why & when

Parameters and return types together define a method's **contract** — exactly what it needs to do its job, and exactly what it promises to hand back:

- **Parameters make methods flexible and reusable** — `area(width, height)` works for any rectangle, not just one hard-coded size, because the actual values are supplied fresh at each call site.
- **Return types make results usable** — a method that computes something needs a way to hand that result back to whoever called it, so the caller can use it in further computation, store it, or print it.
- **`void` for pure side effects** — some methods exist purely to *do* something (print output, modify a field, write to a file) rather than compute and hand back a value; these declare `void` and have no return value.
- **Multiple parameters model methods that genuinely need several independent inputs** — order and type both matter, and the caller must supply arguments matching the declared parameter list exactly (though automatic widening, like passing an `int` where a `double` is expected, is allowed).

You choose parameters and a return type based on what the method genuinely needs as input and what it needs to hand back — a method that only prints something typically needs no return type beyond `void`; a method that computes something almost always should return that computed value rather than just printing it, so the result stays reusable by the caller.

## 3. Core concept

```java
public class ParamReturnDemo {

    static double celsiusToFahrenheit(double celsius) { // one parameter, returns a double
        return celsius * 9.0 / 5.0 + 32.0;
    }

    static void printTemperature(double celsius) { // one parameter, returns nothing (void)
        System.out.println(celsius + "°C = " + celsiusToFahrenheit(celsius) + "°F");
    }

    public static void main(String[] args) {
        double result = celsiusToFahrenheit(100.0); // captures the returned value
        System.out.println(result); // 212.0

        printTemperature(0.0); // no value to capture — the method only prints
    }
}
```

`celsiusToFahrenheit` returns a `double` that `main` captures into `result` for further use; `printTemperature` is declared `void` because its entire job is to produce console output as a side effect, with nothing meaningful to hand back to its caller.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A method box showing celsius flowing in as a parameter, and a computed fahrenheit value flowing back out as the return value, contrasted with a void method that only produces console output with no return arrow">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <text x="60" y="45" fill="#79c0ff" font-size="11" font-family="monospace">celsius=100.0</text>
  <line x1="150" y1="42" x2="200" y2="42" stroke="#79c0ff" stroke-width="2" marker-end="url(#p1)"/>
  <rect x="200" y="25" width="160" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="280" y="47" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">celsiusToFahrenheit</text>
  <line x1="360" y1="42" x2="410" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#p2)"/>
  <text x="470" y="45" fill="#3fb950" font-size="11" font-family="monospace">returns 212.0</text>

  <text x="60" y="110" fill="#79c0ff" font-size="11" font-family="monospace">celsius=0.0</text>
  <line x1="140" y1="107" x2="200" y2="107" stroke="#79c0ff" stroke-width="2" marker-end="url(#p1)"/>
  <rect x="200" y="90" width="160" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="280" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">printTemperature (void)</text>
  <text x="440" y="112" fill="#8b949e" font-size="10" font-family="sans-serif">no return value — only prints</text>

  <defs>
    <marker id="p1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="p2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Parameters flow in; a return value flows back out — unless the method is `void`, which has no outgoing value.

## 5. Runnable example

Scenario: a simple grade-calculation utility — starting with a basic method taking one parameter and returning a value, then extending to a method with multiple parameters, then hardening into a method returning a richer computed result (via a small object) rather than just one primitive value.

### Level 1 — Basic

```java
public class GradeBasic {

    static char letterGrade(int score) {
        if (score >= 90) return 'A';
        if (score >= 80) return 'B';
        if (score >= 70) return 'C';
        return 'F';
    }

    public static void main(String[] args) {
        System.out.println(letterGrade(85)); // B
        System.out.println(letterGrade(95)); // A
    }
}
```

**How to run:** `java GradeBasic.java`

`letterGrade(int score)` has one `int` parameter and returns a `char` — every branch of the `if` chain returns a value matching the declared `char` return type, satisfying the requirement that every possible path return something of the correct type.

### Level 2 — Intermediate

Same idea, extended to take **two** parameters — the raw score and a boolean indicating whether extra credit applies — computing an adjusted grade from both inputs together.

```java
public class GradeIntermediate {

    static char letterGrade(int score, boolean hasExtraCredit) {
        int adjusted = hasExtraCredit ? score + 5 : score;
        if (adjusted >= 90) return 'A';
        if (adjusted >= 80) return 'B';
        if (adjusted >= 70) return 'C';
        return 'F';
    }

    public static void main(String[] args) {
        System.out.println(letterGrade(85, false)); // B
        System.out.println(letterGrade(85, true));  // A — extra credit pushes it over 90
    }
}
```

**How to run:** `java GradeIntermediate.java`

The second parameter, `hasExtraCredit`, changes how `adjusted` is computed before the same grading logic runs — both parameters are genuinely needed together to determine the result, and the method's single `char` return type still cleanly captures the one meaningful output.

### Level 3 — Advanced

Same grading logic, now returning a richer result — a small `GradeResult` object bundling both the letter grade and the adjusted numeric score — since a caller might reasonably need both pieces of information, which a single `char` return value cannot carry on its own.

```java
public class GradeAdvanced {

    static class GradeResult {
        char letter;
        int adjustedScore;
        GradeResult(char letter, int adjustedScore) {
            this.letter = letter;
            this.adjustedScore = adjustedScore;
        }
        public String toString() {
            return letter + " (" + adjustedScore + " points)";
        }
    }

    static GradeResult evaluate(int score, boolean hasExtraCredit) {
        int adjusted = hasExtraCredit ? Math.min(100, score + 5) : score; // cap at 100
        char letter;
        if (adjusted >= 90) letter = 'A';
        else if (adjusted >= 80) letter = 'B';
        else if (adjusted >= 70) letter = 'C';
        else letter = 'F';
        return new GradeResult(letter, adjusted);
    }

    public static void main(String[] args) {
        GradeResult r1 = evaluate(85, false);
        GradeResult r2 = evaluate(98, true); // extra credit would exceed 100, capped

        System.out.println(r1);
        System.out.println(r2);
    }
}
```

**How to run:** `java GradeAdvanced.java`

`evaluate` returns a single `GradeResult` object rather than a bare `char`, letting the method hand back **two** related pieces of information (`letter` and `adjustedScore`) together as one cohesive return value — `Math.min(100, score + 5)` also demonstrates a return-type-compatible expression being used directly as an argument to another method call.

## 6. Walkthrough

Trace `evaluate(98, true)` from `GradeAdvanced.main`:

**Adjusted score.** `hasExtraCredit` is `true`, so `adjusted = Math.min(100, 98 + 5)`. `98 + 5` is `103`; `Math.min(100, 103)` returns `100` (the smaller of the two) — the cap prevents an unrealistic score above 100.

**Letter grade.** `adjusted (100) >= 90` is `true`, so `letter = 'A'`.

**Construct and return.** `new GradeResult('A', 100)` builds the result object, and `return` hands it back to the caller.

**Print.** `r2.toString()` (called implicitly by `println`) produces `"A (100 points)"`.

```
evaluate(98, true)
  adjusted = min(100, 98+5) = min(100, 103) = 100
  100 >= 90 -> letter = 'A'
  returns GradeResult('A', 100)
```

**Contrast with `r1 = evaluate(85, false)`.** `hasExtraCredit` is `false`, so `adjusted = score = 85` unchanged. `85 >= 80` (not `>= 90`), so `letter = 'B'`. Returns `GradeResult('B', 85)`, printed as `"B (85 points)"`.

## 7. Gotchas & takeaways

> **Every non-`void` method must return a value of the declared type on every possible code path — the compiler verifies this exhaustively.** An `if`/`else if` chain without a final `else` (or fallback `return`) that could "fall through" without returning anything is a compile error; `GradeBasic.letterGrade` avoids this specifically because its last line, `return 'F';`, unconditionally covers every case not caught by the earlier `if`s.

> **A method can return at most one value directly — bundling several related results requires returning an object** (as `GradeResult` does), an array, or a collection. Trying to "return two things" by declaring two separate return types isn't possible; the method's single declared return type is fixed.

- Parameters are the method's declared inputs; the return type is what it promises to hand back to its caller.
- `void` methods perform side effects (like printing) and hand back no value at all.
- Every path through a non-`void` method must return a value matching the declared return type, or the code won't compile.
- To return more than one related value from a single method, bundle them into an object (or array/collection) and return that.
