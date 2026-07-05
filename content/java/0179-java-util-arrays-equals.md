---
card: java
gi: 179
slug: java-util-arrays-equals
title: java.util.Arrays.equals()
---

## 1. What it is

`java.util.Arrays.equals()` compares two arrays for **content equality** — same length, and every corresponding element equal — rather than reference equality. This matters because arrays in Java don't override `equals()` from `Object`, so the plain `==` operator (and the inherited `equals()` method) on two arrays only checks whether they are the exact same array object in memory, never whether they contain the same values.

```java
int[] a = { 1, 2, 3 };
int[] b = { 1, 2, 3 };

System.out.println(a == b);                       // false — different objects in memory
System.out.println(a.equals(b));                   // false — same reason: no content comparison
System.out.println(java.util.Arrays.equals(a, b)); // true — same length, same elements in order
```

`Arrays.equals` is overloaded for every primitive array type and for object arrays; for nested (multi-dimensional) arrays, `Arrays.deepEquals` is needed instead, since `Arrays.equals` only compares one level deep.

## 2. Why & when

This method exists precisely because `==` and the default `equals()` are almost never what you want when comparing arrays:

- **Checking if two arrays hold the same data** — verifying a computed result matches an expected array in a test, or checking if two configurations are identical.
- **Avoiding the classic beginner bug** — writing `if (arr1 == arr2)` or `if (arr1.equals(arr2))` expecting a content comparison, but silently getting a reference comparison that's almost always `false` even when the arrays "look the same."
- **Multi-dimensional arrays need `deepEquals`** — `Arrays.equals` on `int[][]` compares only the *outer* array's elements, which are themselves `int[]` references — two different row-arrays with identical contents would still compare as "not equal" by plain `equals`, since it doesn't recurse into nested arrays.

Reach for `Arrays.equals` (or `deepEquals` for nested arrays) any time "are these two arrays the same" means "do they contain the same values," which is true in the overwhelming majority of real use cases.

## 3. Core concept

```java
public class EqualsDemo {
    public static void main(String[] args) {
        int[][] grid1 = { {1, 2}, {3, 4} };
        int[][] grid2 = { {1, 2}, {3, 4} };

        System.out.println(java.util.Arrays.equals(grid1, grid2));     // false! compares only outer references
        System.out.println(java.util.Arrays.deepEquals(grid1, grid2)); // true — recurses into each row
    }
}
```

`Arrays.equals(grid1, grid2)` returns `false` because `grid1`'s elements are `int[]` row-references, and those specific row-objects differ between `grid1` and `grid2` even though their contents match — `Arrays.equals` doesn't look inside them; `Arrays.deepEquals` does exactly that, recursively comparing nested array contents.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two separate one dimensional arrays with identical contents 1 2 3 compared three ways: double equals is false, dot equals is false, Arrays dot equals is true">
  <rect x="8" y="8" width="604" height="154" rx="8" fill="#0d1117"/>
  <text x="310" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">int[] a = {1,2,3};  int[] b = {1,2,3};  (different objects, same content)</text>

  <rect x="80" y="40" width="120" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="60" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">a: [1,2,3]</text>
  <rect x="380" y="40" width="120" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="440" y="60" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">b: [1,2,3]</text>

  <text x="60" y="100" fill="#f85149" font-size="12" font-family="monospace">a == b            -&gt; false (different memory addresses)</text>
  <text x="60" y="122" fill="#f85149" font-size="12" font-family="monospace">a.equals(b)       -&gt; false (Object's default: same as ==)</text>
  <text x="60" y="144" fill="#6db33f" font-size="12" font-family="monospace">Arrays.equals(a,b) -&gt; true (compares length and every element)</text>
</svg>

Only `Arrays.equals` (or `deepEquals` for nested arrays) actually compares array *contents*.

## 5. Runnable example

Scenario: validating that a computed transformation matches an expected result — starting with a basic content comparison, then extending to compare a batch of arrays (checking a whole test suite passes), then hardening into comparing 2D arrays correctly with `deepEquals` versus the common but wrong shallow `equals`.

### Level 1 — Basic

```java
public class EqualsBasic {
    public static void main(String[] args) {
        int[] expected = { 2, 4, 6, 8 };
        int[] actual = { 2, 4, 6, 8 };

        boolean same = java.util.Arrays.equals(expected, actual);
        System.out.println("Arrays match: " + same);
    }
}
```

**How to run:** `java EqualsBasic.java`

`Arrays.equals(expected, actual)` compares both arrays' lengths and every corresponding element, printing `"Arrays match: true"` — despite `expected` and `actual` being two entirely separate array objects in memory.

### Level 2 — Intermediate

Same idea, now applied to a small batch of test cases, comparing each computed result against its expected array and reporting pass/fail per case.

```java
public class EqualsIntermediate {

    static int[] doubleAll(int[] input) {
        int[] result = new int[input.length];
        for (int i = 0; i < input.length; i++) {
            result[i] = input[i] * 2;
        }
        return result;
    }

    public static void main(String[] args) {
        int[][] inputs = { {1, 2}, {3, 4, 5}, {} };
        int[][] expectedOutputs = { {2, 4}, {6, 8, 10}, {} };

        for (int i = 0; i < inputs.length; i++) {
            int[] actual = doubleAll(inputs[i]);
            boolean pass = java.util.Arrays.equals(expectedOutputs[i], actual);
            System.out.println("Case " + i + ": " + (pass ? "PASS" : "FAIL"));
        }
    }
}
```

**How to run:** `java EqualsIntermediate.java`

Each test case's `expectedOutputs[i]` (one specific `int[]`) is compared against `actual` (a freshly computed, entirely separate `int[]` from `doubleAll`) using `Arrays.equals` — content comparison is exactly what's needed here since `doubleAll` never returns the same array object it was given.

### Level 3 — Advanced

Same testing idea, now applied to a function that returns a **2D** array, correctly using `deepEquals` and demonstrating why the shallow `Arrays.equals` would give a wrong (false negative) result on the same data.

```java
import java.util.Arrays;

public class EqualsAdvanced {

    static int[][] transpose(int[][] matrix) {
        int rows = matrix.length;
        int cols = matrix[0].length;
        int[][] result = new int[cols][rows];
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                result[c][r] = matrix[r][c];
            }
        }
        return result;
    }

    public static void main(String[] args) {
        int[][] input = { {1, 2, 3}, {4, 5, 6} };
        int[][] expected = { {1, 4}, {2, 5}, {3, 6} };

        int[][] actual = transpose(input);

        System.out.println("Shallow equals: " + Arrays.equals(expected, actual));     // false — misleading!
        System.out.println("Deep equals:    " + Arrays.deepEquals(expected, actual)); // true — correct check
    }
}
```

**How to run:** `java EqualsAdvanced.java`

`Arrays.equals(expected, actual)` compares `expected` and `actual` element by element, but each "element" here is itself an `int[]` row — and rows are compared by reference, so even rows with identical numbers are "not equal" to `Arrays.equals`; `Arrays.deepEquals` recurses one level deeper, comparing each pair of rows' actual contents, correctly reporting `true`.

## 6. Walkthrough

Trace both comparisons in `EqualsAdvanced.main` for `expected = {{1,4},{2,5},{3,6}}` and `actual = transpose(input)`:

**Computing `actual`.** `transpose` builds a new `3x2` array: `result[0] = [1,4]`, `result[1] = [2,5]`, `result[2] = [3,6]` — matching `expected`'s values, but as completely separate row-array objects from `expected`'s rows.

**`Arrays.equals(expected, actual)`.** This checks: same outer length (`3 == 3`, true so far), then compares `expected[0]` to `actual[0]` — but these are two *different* `int[]` objects, and `Arrays.equals`'s per-element comparison for object arrays uses each element's own `.equals()` — for an `int[]` element, that's the inherited reference-based `Object.equals()`, which is `false` since they're different objects. The overall result is `false` the moment the first row-pair fails this reference check.

**`Arrays.deepEquals(expected, actual)`.** This also checks the outer length matches, but for each pair of corresponding elements that are themselves arrays, it recursively calls `deepEquals` (or `equals` for primitive rows) *on their contents* instead of comparing references — so `expected[0] = [1,4]` and `actual[0] = [1,4]` are correctly recognized as equal by content, and the same holds for all three row pairs, giving an overall `true`.

```
expected[0] = [1,4] (object A)   actual[0] = [1,4] (object B, different object, same content)
Arrays.equals:      A == B by reference? no -> false immediately
Arrays.deepEquals:  recurse into A and B's contents -> [1,4] equals [1,4] -> true, continue to row 1...
```

**Final output.** `"Shallow equals: false"` followed by `"Deep equals:    true"` — demonstrating exactly why nested arrays require `deepEquals`.

## 7. Gotchas & takeaways

> **Plain `==` and the inherited `.equals()` on arrays only ever check reference identity — "is this the exact same object" — never content.** Two arrays holding identical values will both compare as unequal by `==` and by `.equals()` unless they happen to be literally the same object. Always use `Arrays.equals` (or `deepEquals`) for content comparison.

> **`Arrays.equals` on a multi-dimensional array only compares the outer array's elements as references, not their nested contents** — this silently gives `false` for two 2D arrays with genuinely identical numbers if the row-arrays themselves are separate objects, which they almost always are unless deliberately shared. Use `Arrays.deepEquals` for any array of arrays.

- Use `Arrays.equals(a, b)` for content comparison of one-dimensional arrays; never rely on `==` or the inherited `.equals()`.
- Use `Arrays.deepEquals(a, b)` for multi-dimensional (nested) arrays — `Arrays.equals` alone only compares one level deep.
- `Arrays.equals` requires matching length and every corresponding element equal, in the same order.
- This is one of the most common sources of confusion for programmers new to Java, since arrays "look like" they should support `==` for content the way some other languages' collections do.
