---
card: java
gi: 181
slug: java-util-arrays-tostring-deeptostring
title: java.util.Arrays.toString() / deepToString()
---

## 1. What it is

`java.util.Arrays.toString()` builds a human-readable `String` representation of a one-dimensional array's contents, like `"[1, 2, 3]"`. `java.util.Arrays.deepToString()` does the same thing but **recurses** into nested arrays, so a multi-dimensional array prints all its inner values too, rather than each row's internal identifier. Neither method modifies the array — they only produce a `String` describing it.

```java
int[] flat = { 1, 2, 3 };
System.out.println(flat);                     // [I@1b6d3586 — useless memory-address-style text
System.out.println(java.util.Arrays.toString(flat)); // [1, 2, 3] — actually readable

int[][] nested = { {1, 2}, {3, 4} };
System.out.println(java.util.Arrays.toString(nested));     // [[I@..., [I@...] — still useless, one level too shallow
System.out.println(java.util.Arrays.deepToString(nested)); // [[1, 2], [3, 4]] — fully readable
```

Plain `System.out.println(array)` (or string concatenation with `+`) never calls a useful `toString` on an array, because arrays don't override `Object.toString()` — you must explicitly call `Arrays.toString` (or `deepToString` for nested arrays) to get readable output.

## 2. Why & when

Arrays inherit the default `Object.toString()`, which just prints the type and a hash code (like `[I@1b6d3586`) — essentially useless for debugging or display, so the standard library provides purpose-built formatting methods instead:

- **Debugging** — printing an array's contents while tracking down a bug is one of the most common things a programmer does; `Arrays.toString` makes this actually legible.
- **Logging and output** — displaying computed results to a user or in a log file.
- **Testing** — comparing expected vs. actual output in test failure messages, so a mismatch is immediately readable rather than showing two meaningless hash codes.

Use `Arrays.toString` for any one-dimensional array; use `Arrays.deepToString` specifically for arrays of arrays (2D or deeper) — using the non-deep version on nested arrays produces the same kind of useless hash-code text one level down.

## 3. Core concept

```java
public class ToStringDemo {
    public static void main(String[] args) {
        String[] names = { "Ann", "Bo", "Cy" };
        System.out.println(java.util.Arrays.toString(names)); // [Ann, Bo, Cy]

        int[][] matrix = { {1, 0}, {0, 1} };
        System.out.println(java.util.Arrays.deepToString(matrix)); // [[1, 0], [0, 1]]

        int[][][] cube = { {{1}, {2}}, {{3}, {4}} };
        System.out.println(java.util.Arrays.deepToString(cube)); // [[[1], [2]], [[3], [4]]] — recurses to any depth
    }
}
```

`deepToString` recurses to **any depth**, not just one level — a 3D array's `deepToString` output correctly nests three levels of brackets, since the method calls itself recursively wherever it finds an array-typed element rather than a plain value.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A 2D array printed with plain println showing useless hash-code text, with Arrays dot toString on the outer array still showing hash codes for the rows, and Arrays dot deepToString correctly showing the full nested numeric contents">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <text x="300" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">int[][] nested = {{1,2},{3,4}};</text>

  <text x="30" y="55" fill="#f85149" font-size="11" font-family="monospace">println(nested)           -&gt; [[I@4dc63996  (useless)</text>
  <text x="30" y="85" fill="#f85149" font-size="11" font-family="monospace">Arrays.toString(nested)   -&gt; [[I@..., [I@...]  (still useless — one level too shallow)</text>
  <text x="30" y="115" fill="#6db33f" font-size="11" font-family="monospace">Arrays.deepToString(nested) -&gt; [[1, 2], [3, 4]]  (correct, fully readable)</text>
</svg>

Only `deepToString` recurses far enough to render a nested array's actual numeric contents.

## 5. Runnable example

Scenario: debugging a small inventory system's stock levels — starting with basic readable output for a flat array, then extending to a per-warehouse 2D layout needing `deepToString`, then hardening into a debug-logging helper that automatically picks the right method based on the data's shape.

### Level 1 — Basic

```java
public class InventoryToStringBasic {
    public static void main(String[] args) {
        int[] stockLevels = { 42, 17, 0, 88 };

        System.out.println("Raw println: " + stockLevels);
        System.out.println("Arrays.toString: " + java.util.Arrays.toString(stockLevels));
    }
}
```

**How to run:** `java InventoryToStringBasic.java`

The raw `+ stockLevels` concatenation produces something like `"Raw println: [I@<hashcode>"`, while `Arrays.toString(stockLevels)` produces the actually useful `"Arrays.toString: [42, 17, 0, 88]"` — the difference is stark and immediately demonstrates why the utility method exists.

### Level 2 — Intermediate

Same inventory, now organized per warehouse as a 2D array, requiring `deepToString` for readable output.

```java
public class InventoryToStringIntermediate {
    public static void main(String[] args) {
        int[][] stockByWarehouse = {
            { 42, 17, 0 },   // warehouse 0
            { 88, 5, 12 }    // warehouse 1
        };

        System.out.println("Shallow: " + java.util.Arrays.toString(stockByWarehouse));
        System.out.println("Deep:    " + java.util.Arrays.deepToString(stockByWarehouse));
    }
}
```

**How to run:** `java InventoryToStringIntermediate.java`

`Arrays.toString(stockByWarehouse)` treats each row (an `int[]`) as a single opaque element and prints its hash-code-style text; `Arrays.deepToString` recognizes each row is itself an array and recurses into it, correctly printing `"[[42, 17, 0], [88, 5, 12]]"`.

### Level 3 — Advanced

Same inventory data, now with a small debug helper that inspects whether a given object is actually an array of arrays and picks `toString` or `deepToString` accordingly — useful in a logging utility that might receive either shape.

```java
import java.util.Arrays;

public class InventoryToStringAdvanced {

    static String describe(Object array) {
        if (array instanceof int[][] nested) {
            return Arrays.deepToString(nested);
        } else if (array instanceof int[] flat) {
            return Arrays.toString(flat);
        }
        return String.valueOf(array);
    }

    public static void main(String[] args) {
        int[] flatStock = { 42, 17, 0, 88 };
        int[][] nestedStock = { {42, 17}, {0, 88} };

        System.out.println(describe(flatStock));
        System.out.println(describe(nestedStock));
        System.out.println(describe("not an array")); // falls through to plain toString
    }
}
```

**How to run:** `java InventoryToStringAdvanced.java`

`array instanceof int[][] nested` uses Java's **pattern-matching `instanceof`** to check the runtime shape of the argument and, if it matches, bind it directly to a properly-typed local variable `nested` in one step — this lets `describe` correctly route flat arrays to `Arrays.toString` and 2D arrays to `Arrays.deepToString` without the caller needing to know or specify which method applies.

## 6. Walkthrough

Trace `describe(nestedStock)` for `nestedStock = {{42, 17}, {0, 88}}`:

**Type check.** `array instanceof int[][] nested` evaluates whether the runtime object referred to by `array` (declared as `Object`) is actually an `int[][]`. It is, so the check succeeds, and `nested` is bound to that same array, now typed as `int[][]` rather than `Object`.

**Deep formatting.** `return Arrays.deepToString(nested)` recurses: for the outer array, each element (`{42,17}` and `{0,88}`) is itself an array, so `deepToString` formats each one as `"[42, 17]"` and `"[0, 88]"` respectively, then wraps the pair in outer brackets: `"[[42, 17], [0, 88]]"`.

**For `describe(flatStock)`,** the first `instanceof` check (`int[][]`) fails since `flatStock` is only one-dimensional; the second check (`int[]`) succeeds, so `Arrays.toString(flat)` runs instead, producing `"[42, 17, 0, 88]"`.

**For `describe("not an array")`,** both `instanceof` checks fail (a `String` is neither `int[][]` nor `int[]`), so execution falls through to `String.valueOf(array)`, which returns `"not an array"` unchanged.

```
describe(flatStock)    -> instanceof int[]?  yes -> Arrays.toString    -> "[42, 17, 0, 88]"
describe(nestedStock)  -> instanceof int[][]? yes -> Arrays.deepToString -> "[[42, 17], [0, 88]]"
describe("not array")  -> neither matches -> String.valueOf -> "not an array"
```

**Final output.** Three lines printed in that order: `[42, 17, 0, 88]`, `[[42, 17], [0, 88]]`, `not an array`.

## 7. Gotchas & takeaways

> **`System.out.println(array)` or `"text" + array` never calls a meaningful `toString()` — arrays don't override `Object.toString()`.** The result is always the unhelpful `ClassName@hashcode` form. Always call `Arrays.toString` (or `deepToString`) explicitly for readable array output.

> **`Arrays.toString` on a multi-dimensional array only formats the outer level — each row still prints as a useless hash code**, since each row is itself an array and `toString` doesn't recurse. Reach for `Arrays.deepToString` the moment you're formatting anything with more than one dimension.

- `Arrays.toString(array)` gives readable output for one-dimensional arrays; plain `println`/`+` on an array never does.
- `Arrays.deepToString(array)` recurses into nested arrays of any depth, correctly rendering multi-dimensional contents.
- Neither method modifies the array — both simply build and return a descriptive `String`.
- Both are invaluable for debugging, logging, and writing clear test-failure messages when working with array data.
