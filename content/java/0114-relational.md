---
card: java
gi: 114
slug: relational
title: Relational < > <= >=
---

## 1. What it is

The relational operators `<`, `>`, `<=`, and `>=` compare two numeric operands and produce a `boolean` indicating whether the ordering relationship holds. Like the arithmetic operators, they apply binary numeric promotion first (widening `byte`/`short`/`char` operands to `int`, then to the widest type present), so the comparison always happens between two values of the same type. Unlike `==`, the relational operators only work on numeric primitives (and `char`, since it is numeric) — they cannot be applied directly to objects; ordering comparisons between objects go through `Comparable.compareTo()` or a `Comparator` instead.

```java
System.out.println(5 < 10);        // true
System.out.println(5.5 >= 5.5);    // true
System.out.println('a' < 'b');      // true — chars compare by their numeric code point (97 < 98)

int i = 5;
long l = 10_000_000_000L;
System.out.println(i < l);          // true — i is promoted to long before comparing
```

Relational operators involving `NaN` are a special case worth remembering: **every** relational comparison with `NaN` as either operand returns `false`, even `NaN < 1`, `NaN > 1`, and `NaN >= NaN` — there is no ordering relationship with `NaN` at all (see [Floating-point special values](0101-floating-point-special-values-nan-infinity-0-0.md)).

## 2. Why & when

Relational operators are the backbone of loop conditions, range checks, and sorting logic:

- Loop bounds: `for (int i = 0; i < n; i++)`.
- Range validation: `if (age >= 0 && age <= 120)`.
- Manual comparison logic before `Comparable`/`Comparator` were as ubiquitous, and still used inline for simple numeric decisions.

The main pitfalls are: comparing `NaN` (which always yields `false`, meaning code that assumes "either `a < b` or `a >= b` must be true" can be wrong when a `NaN` is involved), and comparing `char` values numerically when a locale-aware or case-insensitive string comparison was actually intended (comparing individual `char`s is a code-point comparison, not a linguistic one).

## 3. Core concept

```java
public class RelationalDemo {
    public static void main(String[] args) {
        // Basic numeric comparisons
        System.out.println("5 < 10:  " + (5 < 10));     // true
        System.out.println("5 <= 5:  " + (5 <= 5));       // true
        System.out.println("10 > 5:  " + (10 > 5));        // true
        System.out.println("5 >= 10: " + (5 >= 10));        // false

        // char compares by numeric code point
        char a = 'a', b = 'b';
        System.out.println("'a' < 'b': " + (a < b));    // true (97 < 98)

        // Mixed-type comparison: promotion applies, same as arithmetic
        byte small = 10;
        long big = 10_000_000_000L;
        System.out.println("small < big: " + (small < big));  // true, byte promoted to long

        // NaN breaks the usual "exactly one of <, ==, > holds" assumption
        double nan = Double.NaN;
        System.out.println("nan < 1.0:  " + (nan < 1.0));    // false
        System.out.println("nan > 1.0:  " + (nan > 1.0));    // false
        System.out.println("nan == 1.0: " + (nan == 1.0));   // false
        System.out.println("nan >= nan: " + (nan >= nan));    // false — even compared to itself!
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="NaN comparison diagram: for ordinary numbers exactly one of less than, equal, greater than is true, but for NaN all three relational comparisons against any value, including itself, evaluate to false.">
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Ordinary numbers vs. NaN — the "exactly one holds" rule breaks</text>

  <text x="170" y="46" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">5 compared to 10 (ordinary)</text>
  <rect x="30" y="56" width="80" height="30" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="70" y="76" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">5 &lt; 10: true</text>
  <rect x="120" y="56" width="80" height="30" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">5 == 10: false</text>
  <rect x="210" y="56" width="80" height="30" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="250" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">5 &gt; 10: false</text>
  <text x="170" y="100" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Exactly ONE of the three is true.</text>

  <text x="530" y="46" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">NaN compared to 10</text>
  <rect x="410" y="56" width="80" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="450" y="76" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">NaN &lt; 10: false</text>
  <rect x="500" y="56" width="80" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="76" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">NaN == 10: false</text>
  <rect x="590" y="56" width="80" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="630" y="76" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">NaN &gt; 10: false</text>
  <text x="530" y="100" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">ALL THREE are false — NaN is unordered.</text>
</svg>

For ordinary numbers exactly one relational result is true; `NaN` breaks that guarantee entirely.

## 5. Runnable example

Scenario: a grading tool that classifies scores into letter grades using chained relational comparisons — extended to handle an edge case where an invalid (NaN) score could otherwise silently pass validation.

### Level 1 — Basic

```java
public class GradingBasic {

    static char letterGrade(double score) {
        if (score >= 90) return 'A';
        if (score >= 80) return 'B';
        if (score >= 70) return 'C';
        if (score >= 60) return 'D';
        return 'F';
    }

    public static void main(String[] args) {
        double[] scores = { 95.5, 82.0, 71.3, 55.0 };
        for (double score : scores) {
            System.out.println("Score " + score + " -> Grade " + letterGrade(score));
        }
    }
}
```

**How to run:** `java GradingBasic.java`

Each `if (score >= threshold)` check is a straightforward relational comparison; because they are checked in descending order, the first one that matches determines the grade, and any score not meeting even the lowest threshold falls through to `'F'`. This works cleanly for all ordinary numeric inputs.

### Level 2 — Intermediate

Same grading tool, now validating the input score is within a sane range before grading, explicitly checking for `NaN` because `NaN >= 90` is `false` (as is every other threshold check), which would otherwise silently produce a grade of `'F'` for genuinely invalid, uncomputed data.

```java
public class GradingIntermediate {

    static char letterGrade(double score) {
        if (Double.isNaN(score)) {
            throw new IllegalArgumentException("Cannot grade a NaN score");
        }
        if (score < 0 || score > 100) {
            throw new IllegalArgumentException("Score out of range: " + score);
        }
        if (score >= 90) return 'A';
        if (score >= 80) return 'B';
        if (score >= 70) return 'C';
        if (score >= 60) return 'D';
        return 'F';
    }

    public static void main(String[] args) {
        double[] scores = { 95.5, Double.NaN, 71.3, 105.0 };
        for (double score : scores) {
            try {
                System.out.println("Score " + score + " -> Grade " + letterGrade(score));
            } catch (IllegalArgumentException e) {
                System.out.println("Score " + score + " -> Rejected: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java GradingIntermediate.java`

Without the explicit `Double.isNaN` check, a `NaN` score (perhaps produced upstream by a `0.0 / 0.0` division bug when averaging an empty set of sub-scores) would silently fall through *every single* `>=` check — since `NaN >= 90`, `NaN >= 80`, and so on are all `false` — landing on the final `return 'F'` and masking the underlying data problem as if the student had simply failed. The explicit check turns this into a loud, clear rejection instead.

### Level 3 — Advanced

Same grading tool, now sorting a roster of students by score using `Comparable`/`compareTo` (which internally uses relational-style logic but returns an `int`), and handling ties with a secondary comparison, demonstrating the transition from raw relational operators to the idiomatic multi-field comparison pattern.

```java
import java.util.*;

public class GradingAdvanced {

    record Student(String name, double score) implements Comparable<Student> {
        @Override
        public int compareTo(Student other) {
            // Primary: score descending (higher score first) — note operand order for descending
            int scoreCompare = Double.compare(other.score, this.score);
            if (scoreCompare != 0) return scoreCompare;
            // Tie-break: name ascending, alphabetical
            return this.name.compareTo(other.name);
        }
    }

    public static void main(String[] args) {
        List<Student> roster = new ArrayList<>(List.of(
            new Student("Charlie", 88.0),
            new Student("Alice", 92.0),
            new Student("Bob", 88.0),     // ties with Charlie on score
            new Student("Dana", 79.5)
        ));

        Collections.sort(roster);   // uses compareTo, which internally relies on relational-style comparison

        System.out.println("Ranked roster:");
        for (int i = 0; i < roster.size(); i++) {
            Student s = roster.get(i);
            System.out.printf("  %d. %-8s %.1f%n", i + 1, s.name(), s.score());
        }
    }
}
```

**How to run:** `java GradingAdvanced.java`

`Double.compare(other.score, this.score)` is the safe, `NaN`-aware alternative to writing `this.score > other.score ? 1 : (this.score < other.score ? -1 : 0)` by hand — critically, unlike raw `<`/`>`, `Double.compare` defines a total ordering that *does* handle `NaN` consistently (treating it as greater than any other value, including positive infinity), so a sort will not silently misbehave if a `NaN` score sneaks in. The tie-break `this.name.compareTo(other.name)` only runs when `scoreCompare == 0`, giving a deterministic secondary order for students with identical scores — Bob and Charlie both have `88.0`, so alphabetical order (`Bob` before `Charlie`) decides between them.

## 6. Walkthrough

Trace `Collections.sort(roster)` comparing `Bob` (`88.0`) and `Charlie` (`88.0`):

**`compareTo` is invoked** (by the sort algorithm) as `bob.compareTo(charlie)` (or the reverse, depending on the sort's internal comparisons — the result is consistent either way due to the contract `compareTo` must satisfy).

**Primary comparison.** `Double.compare(charlie.score, bob.score)` computes `Double.compare(88.0, 88.0)`, which returns `0` because the two `double` values are equal — this is exactly analogous to what `88.0 == 88.0` would tell you, but expressed as a three-way result (`negative`, `zero`, `positive`) rather than a `boolean`.

**Tie-break fires.** Since `scoreCompare == 0`, the method falls through to `this.name.compareTo(other.name)`, i.e., `bob.name.compareTo(charlie.name)` = `"Bob".compareTo("Charlie")`. String comparison here works character by character using the same underlying code-point ordering that `char` relational operators use: `'B'` (66) versus `'C'` (67) — `66 < 67`, so `"Bob".compareTo("Charlie")` returns a negative number.

**Result.** A negative `compareTo` result means `bob` sorts *before* `charlie` in ascending order — matching the alphabetical tie-break intent.

```
compareTo(Bob, Charlie):
  Double.compare(88.0, 88.0) = 0        <- scores tie
        |
        v
  "Bob".compareTo("Charlie")
    'B' (66) vs 'C' (67)  ->  66 < 67  -> negative result
        |
        v
  overall compareTo result: negative  ->  Bob sorts before Charlie
```

**Final output.** After sorting, the roster is ordered by descending score (Alice's `92.0` first, then the `88.0` tie broken alphabetically as Bob then Charlie, then Dana's `79.5` last), printed with rank numbers `1` through `4`.

## 7. Gotchas & takeaways

> **Every relational comparison (`<`, `>`, `<=`, `>=`, and even `==`) involving `NaN` returns `false`.** Code that assumes "if `a < threshold` is false, then `a >= threshold` must be true" silently breaks when `a` is `NaN` — both comparisons return `false`. Explicitly check `Double.isNaN` before relational logic when the value could be `NaN`.

> **`char` relational comparisons compare numeric code points, not linguistic/locale order.** `'a' < 'A'` is `false` (lowercase code points are numerically higher than uppercase in ASCII/Unicode), which may surprise you if you expected case-insensitive or dictionary ordering — use `String.compareToIgnoreCase` or a `Collator` for locale-aware text comparison.

- `<`, `>`, `<=`, `>=` work on numeric primitives (including `char`, compared by code point) and apply the same binary numeric promotion as arithmetic operators.
- They cannot be applied directly to objects — use `Comparable.compareTo()` or a `Comparator` for object ordering.
- `Double.compare`/`Float.compare` provide a well-defined total ordering (including a consistent, if unusual, treatment of `NaN`) that raw relational operators do not.
- Always guard against `NaN` explicitly when a value's validity is in question, since it silently fails every ordering check rather than throwing or standing out.
