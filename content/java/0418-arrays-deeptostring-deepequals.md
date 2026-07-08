---
card: java
gi: 418
slug: arrays-deeptostring-deepequals
title: Arrays.deepToString / deepEquals
---

## 1. What it is

`Arrays.deepToString(Object[])` and `Arrays.deepEquals(Object[], Object[])`, added in Java 5, are the array-of-arrays-aware counterparts to `Arrays.toString()` and `Arrays.equals()`. Where the plain versions only look one level deep — printing or comparing an array's immediate elements — the `deep` versions **recurse** into any nested arrays they find, correctly printing or comparing multi-dimensional arrays (like a 2D grid) instead of showing meaningless internal references or reporting them as unequal when they aren't.

## 2. Why & when

In Java, a "2D array" (`int[][]`) is really an array of array references — each row is a separate `int[]` object. `Arrays.toString()` on a 2D array prints the outer array's elements, which are those inner array *references*, giving unhelpful output like `[[I@1b6d3586, [I@4554617c]` instead of the actual numbers. Similarly, `Arrays.equals()` on two 2D arrays compares those same references with `==`, meaning two 2D arrays with identical contents but different object instances are reported as unequal — a common and confusing bug when writing tests that compare nested arrays or matrices.

`deepToString` and `deepEquals` exist specifically to fix this: they detect nested arrays and recurse into them, giving you the readable, structurally-correct output and comparison you actually want. You reach for these any time you're working with multi-dimensional arrays or arrays of arrays — printing a matrix for debugging, or writing unit test assertions that compare nested array structures for equal content rather than equal references.

## 3. Core concept

```java
import java.util.Arrays;

int[][] grid = {{1, 2}, {3, 4}};

System.out.println(Arrays.toString(grid));      // [[I@1b6d3586, [I@4554617c] -- useless, shows references
System.out.println(Arrays.deepToString(grid));   // [[1, 2], [3, 4]] -- recurses into each row

int[][] grid2 = {{1, 2}, {3, 4}}; // same CONTENT, different objects entirely

System.out.println(Arrays.equals(grid, grid2));      // false -- compares row REFERENCES, which differ
System.out.println(Arrays.deepEquals(grid, grid2));  // true -- recurses and compares actual contents
```

The rule of thumb: whenever an array's elements are themselves arrays (any dimensionality beyond 1D), reach for the `deep` variant — the plain `toString`/`equals` versions are only correct for arrays of non-array elements (like `int[]` or `String[]`).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Arrays.toString on a 2D array prints the row references directly; Arrays.deepToString recurses into each row to print actual values">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">int[][] grid = {{1,2},{3,4}}</text>

  <text x="20" y="55" fill="#f85149" font-size="11" font-family="sans-serif">Arrays.toString(grid) -- only 1 level deep:</text>
  <rect x="30" y="65" width="280" height="30" rx="4" fill="#1c2430" stroke="#f85149"/>
  <text x="170" y="85" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">[[I@1b6d3586, [I@4554617c]</text>

  <text x="20" y="120" fill="#6db33f" font-size="11" font-family="sans-serif">Arrays.deepToString(grid) -- recurses into each row:</text>
  <rect x="30" y="130" width="200" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="130" y="150" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">[[1, 2], [3, 4]]</text>
</svg>

Plain `toString`/`equals` stop at the outer array; `deepToString`/`deepEquals` recurse through every nested level.

## 5. Runnable example

Scenario: debugging and testing a simple 2D grid representing a tic-tac-toe-style board — the same grid, evolved from confusing reference-based output, through correct `deepToString` printing, to a `deepEquals`-based test comparing two independently-constructed boards for equal content.

### Level 1 — Basic

```java
import java.util.Arrays;

public class GridPrintBroken {
    public static void main(String[] args) {
        char[][] board = {
            {'X', 'O', 'X'},
            {'O', 'X', 'O'},
            {'X', 'X', 'O'}
        };

        System.out.println(Arrays.toString(board)); // prints array references, not the board's contents
    }
}
```

**How to run:** `java GridPrintBroken.java`

`Arrays.toString(board)` only looks one level deep — since `board`'s elements are themselves `char[]` arrays (not primitive values), it prints their internal reference strings (something like `[[C@1b6d3586, ...]`), which is completely useless for actually seeing what the board looks like.

### Level 2 — Intermediate

```java
import java.util.Arrays;

public class GridPrintFixed {
    public static void main(String[] args) {
        char[][] board = {
            {'X', 'O', 'X'},
            {'O', 'X', 'O'},
            {'X', 'X', 'O'}
        };

        System.out.println(Arrays.deepToString(board)); // recurses into each row -- shows real contents
    }
}
```

**How to run:** `java GridPrintFixed.java`

`Arrays.deepToString(board)` recurses into each row array and prints its actual character contents, giving genuinely useful, human-readable output for debugging the board's state.

### Level 3 — Advanced

```java
import java.util.Arrays;

public class GridEqualityTest {
    static char[][] buildBoard() {
        // Constructs a board with the SAME content as another, but as entirely separate array objects
        return new char[][] {
            {'X', 'O', 'X'},
            {'O', 'X', 'O'},
            {'X', 'X', 'O'}
        };
    }

    public static void main(String[] args) {
        char[][] board1 = buildBoard();
        char[][] board2 = buildBoard(); // separate objects, identical content

        System.out.println("Same object? " + (board1 == board2));
        System.out.println("Arrays.equals (shallow, wrong for 2D): " + Arrays.equals(board1, board2));
        System.out.println("Arrays.deepEquals (correct for 2D): " + Arrays.deepEquals(board1, board2));

        // A genuinely different board, for contrast
        char[][] board3 = {
            {'X', 'O', 'X'},
            {'O', 'X', 'O'},
            {'X', 'O', 'O'} // last row differs: X,O,O instead of X,X,O
        };
        System.out.println("board1 vs board3 deepEquals: " + Arrays.deepEquals(board1, board3));
    }
}
```

**How to run:** `java GridEqualityTest.java`

`board1` and `board2` hold identical *content* but are entirely separate array objects (and so are each of their row arrays) — `Arrays.equals` incorrectly reports them as unequal because it compares row references with `==`, while `Arrays.deepEquals` correctly reports them as equal because it recurses down to the actual `char` values. `board3`, with genuinely different content in its last row, is correctly reported as unequal by `deepEquals`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `buildBoard()` is called twice, producing `board1` and `board2` — two entirely separate `char[][]` objects (and separate row objects within each), even though every character they contain is identical.

`board1 == board2` compares object references directly — since these are two distinct objects created by two separate calls to `buildBoard()`, this is `false`, printed as `"Same object? false"`.

`Arrays.equals(board1, board2)` iterates the *outer* array only, comparing `board1[0] == board2[0]`, `board1[1] == board2[1]`, `board1[2] == board2[2]` — each of these compares two `char[]` row *references*. Since `board1`'s rows and `board2`'s rows are separate objects (even though their contents match), every one of these `==` comparisons is `false`, so `Arrays.equals` returns `false` overall — printed as `"Arrays.equals (shallow, wrong for 2D): false"`, demonstrating the bug.

`Arrays.deepEquals(board1, board2)` also iterates the outer array, but for each pair of elements that are themselves arrays, it recurses — calling the equivalent of `Arrays.equals` (or `deepEquals` again, for arrays nested even deeper) on `board1[0]` vs `board2[0]`'s actual `char` contents: `'X'=='X'`, `'O'=='O'`, `'X'=='X'`, all true. The same check passes for rows 1 and 2. Since every row's content matches, `deepEquals` returns `true` overall — printed as `"Arrays.deepEquals (correct for 2D): true"`.

Finally, `board3` is constructed with its last row deliberately different (`{'X', 'O', 'O'}` instead of `{'X', 'X', 'O'}`). `Arrays.deepEquals(board1, board3)` recurses through rows 0 and 1 successfully (they match), but on row 2, comparing `'X','X','O'` against `'X','O','O'`, the second character differs (`'X'` vs `'O'`), so that row's recursive comparison returns `false`, which propagates up to make the overall `deepEquals` call return `false` — printed as `"board1 vs board3 deepEquals: false"`.

Expected output:
```
Same object? false
Arrays.equals (shallow, wrong for 2D): false
Arrays.deepEquals (correct for 2D): true
board1 vs board3 deepEquals: false
```

## 7. Gotchas & takeaways

> `Arrays.equals()` (and `Arrays.toString()`) only operate **one level deep**. Applying them to a 2D (or deeper) array doesn't throw an error or warn you — it silently compares/prints the inner array *references* instead of their contents, which looks like working code but produces wrong results (`false` for genuinely equal-content arrays, or unreadable `@hashcode` strings when printed). Always reach for `Arrays.deepEquals`/`Arrays.deepToString` the moment an array's elements are themselves arrays.

- `Arrays.toString()`/`Arrays.equals()` are correct for arrays of non-array elements (`int[]`, `String[]`, etc.) — they only become a problem once nesting is involved.
- `Arrays.deepToString()`/`Arrays.deepEquals()` recurse into any nested arrays, at any depth, printing or comparing actual contents rather than references.
- A very common real-world trigger: writing a unit test that asserts two 2D arrays (or arrays of arrays) are equal using `assertEquals` or `Arrays.equals` — this silently passes or fails incorrectly unless the deep variant is used.
- `Arrays.deepHashCode()` is the corresponding recursive hash code method, useful if nested arrays are ever used as keys or need consistent hashing (though using arrays as map keys is itself best avoided in favor of `List` or a dedicated wrapper).
- The rule of thumb: if `T[]`'s element type `T` is itself an array type, use the `deep` methods; otherwise the plain methods are correct and sufficient.
