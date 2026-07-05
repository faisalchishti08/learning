---
card: java
gi: 166
slug: array-declaration-syntax-int-vs-int-x
title: Array declaration syntax (int[] vs int x[])
---

## 1. What it is

Java supports two syntaxes for declaring an array variable: the **C-style** form places the brackets after the variable name (`int x[]`), while the **Java-style** form places them after the type (`int[] x`). Both compile to exactly the same thing — a variable of type "array of `int`" — but the Java-style form is universally preferred because it keeps the type (`int[]`, "array of int") together as one visual unit, rather than splitting it across the declaration.

```java
int[] x;      // Java style (preferred): the type is "int[]" — clearly "an array of int"
int y[];      // C style (legal, but discouraged): the type is still "int[]", just written awkwardly

int[] a, b;   // BOTH a and b are int[] — brackets attached to the type apply to every variable in the list
int c[], d;   // c is int[], but d is a PLAIN int — brackets only attach to the variable they're written after!
```

The last example is the real, practical danger of the C-style form: brackets written after an individual variable name only apply to *that* variable, not to every variable declared on the same line — a mistake that's easy to make and easy to miss when reading the code quickly.

## 2. Why & when

Java retains the C-style syntax purely for backward compatibility with C/C++ programmers transitioning to Java in its early days — it has no functional advantage and one clear, well-known pitfall:

- **Always prefer `Type[] name`** — it reads naturally as "this variable's type is array-of-`Type`," matching how the rest of Java's type system works.
- **Never mix declaration styles or declare multiple array variables with per-variable brackets on one line** — as shown above, `int c[], d;` silently produces one array variable and one plain `int` variable on the very same line, which is a subtle, easy-to-miss bug waiting to happen.
- **Style guides and linters universally flag the C-style form** — modern Java code should never use `int x[]`; it exists in the language purely for legacy reasons and shows up occasionally only in very old code or textbooks.

## 3. Core concept

```java
public class ArraySyntaxDemo {
    public static void main(String[] args) {
        int[] preferred;       // Java style: clearly "array of int"
        int legacy[];          // C style: legal, but avoid this

        preferred = new int[]{ 1, 2, 3 };
        legacy = new int[]{ 4, 5, 6 };

        System.out.println(preferred[0] + ", " + legacy[0]); // "1, 4" — both work identically

        int[] arr1, arr2;      // BOTH are int[] — brackets on the type apply to the whole declaration list
        int arr3[], notArray;  // arr3 is int[], but notArray is a PLAIN int, NOT an array!

        arr1 = new int[]{ 1 };
        arr2 = new int[]{ 2 };
        arr3 = new int[]{ 3 };
        notArray = 42; // a plain int — cannot be indexed, cannot call .length

        System.out.println(arr1[0] + ", " + arr2[0] + ", " + arr3[0] + ", " + notArray);
    }
}
```

`legacy` behaves identically to `preferred` at runtime — the C-style syntax is purely cosmetic, not a different kind of array. But `arr3[], notArray` on one line demonstrates the real hazard: only `arr3` becomes an array; `notArray` is declared as a completely ordinary `int`, despite sharing a declaration line with an array variable.

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Array declaration diagram: the line int arr3 brackets comma notArray declares arr3 as an array of int because the brackets are attached directly to arr3's name, while notArray on the same line has no brackets attached to it and is therefore an ordinary plain int, not an array." >
  <rect x="8" y="8" width="684" height="139" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">int arr3[], notArray;  — brackets attach PER VARIABLE in C-style form</text>

  <rect x="60" y="45" width="30" height="26" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="75" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">int</text>
  <rect x="100" y="45" width="60" height="26" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="130" y="62" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">arr3[]</text>
  <text x="130" y="85" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">IS an array (int[])</text>

  <rect x="230" y="45" width="90" height="26" rx="3" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="275" y="62" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">notArray</text>
  <text x="275" y="85" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">is a PLAIN int, NOT an array!</text>

  <text x="350" y="120" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Prefer int[] arr3, notArray; instead — brackets on the TYPE apply to every variable declared, with no ambiguity.</text>
</svg>

Brackets attached to an individual variable name in C-style form apply only to that one variable, not the whole declaration line.

## 5. Runnable example

Scenario: declaring variables to hold student test scores for several classes — starting with the discouraged C-style declaration (to observe the ambiguity directly), then switching to the preferred Java-style form, then hardening the code into a small utility that safely initializes multiple related array variables using the unambiguous, consistent style.

### Level 1 — Basic (C-style, showing the ambiguity)

```java
public class ScoresBuggy {
    public static void main(String[] args) {
        int classAScores[], classBAverage; // classAScores is int[], classBAverage is a PLAIN int!

        classAScores = new int[]{ 85, 92, 78 };
        classBAverage = 88; // just a single number, NOT an array — easy to miss when skimming the declaration

        System.out.println("Class A scores: " + classAScores.length);
        System.out.println("Class B average: " + classBAverage);
    }
}
```

**How to run:** `java ScoresBuggy.java`

At first glance, `classAScores[], classBAverage` might look like it declares two related array variables — but only `classAScores` is actually `int[]`; `classBAverage` is a completely ordinary `int`, because the brackets in C-style declarations attach only to the specific name they immediately follow, not to every name in the comma-separated list.

### Level 2 — Intermediate (fixed with Java-style)

Same variables, now declared with the preferred `Type[] name` syntax and on **separate lines** (or with brackets clearly on the type for a shared declaration), removing any ambiguity about which variables are arrays.

```java
public class ScoresFixed {
    public static void main(String[] args) {
        int[] classAScores;
        int classBAverage; // clearly a single int — no ambiguity, one declaration per concept

        classAScores = new int[]{ 85, 92, 78 };
        classBAverage = 88;

        System.out.println("Class A scores: " + classAScores.length);
        System.out.println("Class B average: " + classBAverage);
    }
}
```

**How to run:** `java ScoresFixed.java`

Declaring `classAScores` and `classBAverage` on separate lines, each with its own clear type, removes any risk of misreading which variable is an array — this is both stylistically preferred and functionally identical to `ScoresBuggy`'s (accidental) behavior, but far less error-prone to write and to review.

### Level 3 — Advanced

Same scoring system, now declaring **multiple genuinely related array variables** together using the Java-style form, where brackets correctly attach to the shared type and apply uniformly to every variable in the list — demonstrating the one case where declaring several arrays on one line is both convenient and unambiguous.

```java
import java.util.Arrays;

public class ScoresAdvanced {

    static double average(int[] scores) {
        if (scores == null || scores.length == 0) {
            return 0.0;
        }
        int sum = 0;
        for (int score : scores) sum += score;
        return (double) sum / scores.length;
    }

    public static void main(String[] args) {
        int[] classA, classB, classC; // ALL THREE are int[] — brackets on the shared type apply to every name

        classA = new int[]{ 85, 92, 78 };
        classB = new int[]{ 70, 88, 95, 60 };
        classC = new int[]{ 100, 99, 98 };

        int[][] allClasses = { classA, classB, classC };
        String[] labels = { "Class A", "Class B", "Class C" };

        for (int i = 0; i < allClasses.length; i++) {
            System.out.println(labels[i] + ": " + Arrays.toString(allClasses[i])
                              + " -> average " + average(allClasses[i]));
        }
    }
}
```

**How to run:** `java ScoresAdvanced.java`

`int[] classA, classB, classC;` declares all three variables as `int[]` in one line — because the brackets are attached to the shared type `int[]` rather than to any individual variable name, this form has none of the ambiguity that `int classA[], classB, classC;` (C-style) would have introduced; every name in this list is unambiguously an array. `allClasses` then groups the three arrays into a `int[][]` (an array of arrays) purely for convenient iteration, with `average(...)` computing each class's mean score independently.

## 6. Walkthrough

Trace the loop over `allClasses = { classA, classB, classC }`:

**i = 0.** `allClasses[0]` is `classA`, containing `{85, 92, 78}`. `Arrays.toString(classA)` produces `"[85, 92, 78]"`. `average(classA)`: `sum = 85+92+78 = 255`; `scores.length = 3`; returns `255.0 / 3 = 85.0`. Prints `"Class A: [85, 92, 78] -> average 85.0"`.

**i = 1.** `allClasses[1]` is `classB`, containing `{70, 88, 95, 60}`. `average(classB)`: `sum = 70+88+95+60 = 313`; `length = 4`; returns `313.0 / 4 = 78.25`. Prints `"Class B: [70, 88, 95, 60] -> average 78.25"`.

**i = 2.** `allClasses[2]` is `classC`, containing `{100, 99, 98}`. `average(classC)`: `sum = 297`; `length = 3`; returns `99.0`. Prints `"Class C: [100, 99, 98] -> average 99.0"`.

```
classA = {85, 92, 78}        -> average = 255/3  = 85.0
classB = {70, 88, 95, 60}    -> average = 313/4  = 78.25
classC = {100, 99, 98}       -> average = 297/3  = 99.0
```

**Final output.** The three lines print each class's contents and computed average exactly as traced, demonstrating that all three variables declared together on one line (`classA, classB, classC`) are genuinely, unambiguously arrays — a direct consequence of the brackets being attached to the shared `int[]` type rather than to any individual name.

## 7. Gotchas & takeaways

> **In C-style array declarations, brackets attach to the individual variable name they immediately follow, not to the entire comma-separated declaration list** — `int a[], b;` declares `a` as `int[]` but `b` as a plain `int`. This is easy to miss when skimming code, and is one of the main reasons the C-style form is discouraged.

> **The Java-style form (`int[] a, b;`) has no such ambiguity — brackets on the shared type apply uniformly to every variable named on that line**, making it both the conventional and the safer choice whenever declaring one or more array variables together.

- `Type[] name` (Java style) and `Type name[]` (C style) compile to identical array types — the difference is purely syntactic, not behavioral.
- Always use the Java-style form (`int[] x`), since it keeps the array type as one visual unit and avoids the well-known per-variable-bracket ambiguity of the C-style form.
- Never mix array and non-array variable declarations with C-style per-variable brackets on a single line — the ambiguity is real and easy to overlook.
- When declaring several array variables together, `Type[] a, b, c;` is unambiguous precisely because the brackets belong to the type, not to any one name.
