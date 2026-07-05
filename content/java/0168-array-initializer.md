---
card: java
gi: 168
slug: array-initializer
title: Array initializer { }
---

## 1. What it is

An **array initializer** is a curly-brace list of values (`{ 1, 2, 3 }`) that both creates an array and fills it with specific values in a single expression, without needing to write `new Type[size]` explicitly followed by individual assignments. It comes in two forms: the short form, usable only at the point of declaration (`int[] a = {1, 2, 3};`), and the full form, usable anywhere an expression is expected (`int[] a; a = new int[]{1, 2, 3};`).

```java
int[] a = { 1, 2, 3 };              // short form: only legal at the point of declaration
int[] b;
b = new int[]{ 4, 5, 6 };            // full form: legal anywhere, including reassignment or as a method argument

// int[] c; c = { 7, 8, 9 };         // ILLEGAL — short form only works combined with a declaration
```

The full form, `new int[]{...}`, is required whenever you're not simultaneously declaring the variable — passing an array literal directly as a method argument, returning one from a method, or reassigning an already-declared variable all require this form, since the short form's compactness only works at declaration time.

## 2. Why & when

Array initializers exist purely for **convenience** when you already know an array's exact contents upfront:

- **Small, fixed, known collections of values** — days of the week, a lookup table, test data — writing them inline is far more readable than separate `new` plus individual index assignments.
- **The full form (`new Type[]{...}`) whenever the short form's declaration-only restriction doesn't fit** — passing array literals as arguments, building one inside a return statement, or reassigning an existing variable.
- **Multi-dimensional initializers** nest naturally: `int[][] grid = {{1,2},{3,4}};` builds a 2×2 grid in one expression, each inner `{...}` becoming one row.

For arrays whose contents are computed or not known until runtime, `new Type[size]` followed by a loop filling in each element (as in the previous topic) remains the correct approach — initializers are for genuinely known, literal data.

## 3. Core concept

```java
public class InitializerDemo {
    public static void main(String[] args) {
        // Short form — only valid combined with declaration
        int[] primes = { 2, 3, 5, 7, 11 };

        // Full form — required for reassignment or when not declaring at the same time
        int[] moreDigits;
        moreDigits = new int[]{ 13, 17, 19 };

        // Nested initializer for a 2D array
        int[][] grid = {
            { 1, 2, 3 },
            { 4, 5, 6 }
        };

        System.out.println(java.util.Arrays.toString(primes));
        System.out.println(java.util.Arrays.toString(moreDigits));
        System.out.println(java.util.Arrays.deepToString(grid)); // deepToString handles nested arrays properly
    }
}
```

`java.util.Arrays.deepToString` (rather than the ordinary `toString`) is needed specifically for multi-dimensional arrays — `toString` on a `int[][]` would only print each row's memory-address-like identifier, not its actual contents, while `deepToString` recursively renders every nested array's real values.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Array initializer diagram: the short form int array primes equals curly brace two comma three comma five closing brace both creates the array and fills every slot with its listed value in one single expression, valid only at the point of declaration." >
  <rect x="8" y="8" width="684" height="134" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">int[] primes = { 2, 3, 5, 7, 11 };  — create AND fill in one expression</text>

  <rect x="180" y="45" width="60" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="210" y="67" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="240" y="45" width="60" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="270" y="67" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">3</text>
  <rect x="300" y="45" width="60" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="67" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">5</text>
  <rect x="360" y="45" width="60" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="390" y="67" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">7</text>
  <rect x="420" y="45" width="60" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="67" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">11</text>

  <text x="330" y="100" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">length is automatically 5, inferred from the count of values listed —</text>
  <text x="330" y="115" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">no need to separately specify a size.</text>
</svg>

An initializer both allocates the exact right size and fills every slot in a single, compact expression.

## 5. Runnable example

Scenario: representing a simple game board's initial known layout and configuration constants — starting with basic single-dimension initializers for known constants, then extending to a 2D initializer for the board itself, then hardening it into a method that accepts and validates initializer-built data passed in via the full form.

### Level 1 — Basic

```java
public class BoardConfigBasic {
    public static void main(String[] args) {
        String[] playerNames = { "Alice", "Bob" };
        int[] startingScores = { 0, 0 };

        for (int i = 0; i < playerNames.length; i++) {
            System.out.println(playerNames[i] + " starts with score " + startingScores[i]);
        }
    }
}
```

**How to run:** `java BoardConfigBasic.java`

Both `playerNames` and `startingScores` are created and filled in a single expression each, at the point of declaration — this short form is ideal here since both arrays' complete, known contents are being specified directly in the source code, with no need for a separate `new String[2]` followed by two individual assignments.

### Level 2 — Intermediate

Same board configuration, now representing the **board layout itself** as a 2D array using a nested initializer, where each inner `{...}` becomes one row.

```java
public class BoardConfigIntermediate {
    public static void main(String[] args) {
        char[][] board = {
            { '.', '.', 'X' },
            { '.', 'O', '.' },
            { 'X', '.', '.' }
        };

        for (char[] row : board) {
            StringBuilder line = new StringBuilder();
            for (char cell : row) {
                line.append(cell).append(' ');
            }
            System.out.println(line.toString().trim());
        }
    }
}
```

**How to run:** `java BoardConfigIntermediate.java`

The outer `{...}` contains three inner `{...}` groups, each becoming one row of `board` — this nested initializer both allocates the full 3×3 `char[][]` and fills every one of its 9 cells in a single expression, with `board.length` automatically becoming `3` (three rows) and each `board[i].length` becoming `3` (three columns), all inferred purely from the shape of the literal itself.

### Level 3 — Advanced

Same board setup, now passing initializer-built data into a validating method using the **full form** (`new char[][]{...}`), since passing a literal directly as a method argument requires the full form — the short form only works at the point of a variable's own declaration, not as an argument expression.

```java
public class BoardConfigAdvanced {

    static void printValidatedBoard(char[][] board) {
        if (board == null || board.length == 0) {
            throw new IllegalArgumentException("Board cannot be null or empty");
        }
        int expectedCols = board[0].length;
        for (char[] row : board) {
            if (row.length != expectedCols) {
                throw new IllegalArgumentException("All rows must have the same length");
            }
        }

        for (char[] row : board) {
            StringBuilder line = new StringBuilder();
            for (char cell : row) {
                line.append(cell).append(' ');
            }
            System.out.println(line.toString().trim());
        }
    }

    public static void main(String[] args) {
        // Full form required here: passing an array literal directly as a method argument
        printValidatedBoard(new char[][]{
            { '.', '.', 'X' },
            { '.', 'O', '.' },
            { 'X', '.', '.' }
        });

        try {
            printValidatedBoard(new char[][]{
                { '.', '.', 'X' },
                { '.', 'O' } // uneven row length — deliberately malformed
            });
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java BoardConfigAdvanced.java`

`printValidatedBoard(new char[][]{ ... })` uses the full form directly inline as a method call argument — this is precisely the situation the short form (`{...}` alone, with no `new char[][]`) cannot handle, since there's no simultaneous variable declaration happening here. Inside the method, every row's length is checked against `board[0].length` before printing anything, catching a malformed, uneven "jagged" board (where one row has fewer columns than the others) as an explicit, clear error rather than allowing it to print an inconsistent, confusing board layout.

## 6. Walkthrough

Trace `printValidatedBoard` for the second, deliberately malformed call:

**Building the argument.** `new char[][]{ {'.', '.', 'X'}, {'.', 'O'} }` constructs a 2-row array where row 0 has 3 columns but row 1 has only 2 — this is legal Java (arrays of arrays don't require uniform row lengths, unlike a true rectangular matrix), but is not valid input for this particular board representation.

**Null/empty check.** `board` is neither `null` nor length-`0`, so this guard doesn't throw.

**Column-count validation.** `expectedCols = board[0].length = 3` (from the first row). The loop checks each row: `board[0].length` is `3`, matching `expectedCols` — no exception yet. `board[1].length` is `2`, which does **not** match `expectedCols` (`3`) — the guard clause throws `IllegalArgumentException("All rows must have the same length")` immediately.

```
board = [ ['.','.', 'X'], ['.','O'] ]   (row 0 has 3 cols, row 1 has 2 cols)
expectedCols = board[0].length = 3
row 0: length 3 == 3 -> OK
row 1: length 2 != 3 -> THROW "All rows must have the same length"
```

**Final output.** The first, well-formed call prints the 3×3 board's three rows (`". . X"`, `". O ."`, `"X . ."`), each trimmed of its trailing space. The second call's exception is caught in `main`, printing `"Rejected: All rows must have the same length"` — the malformed board is never actually printed at all, since the validation runs to completion before any row-printing code executes.

## 7. Gotchas & takeaways

> **The short-form initializer (`{...}` with no `new Type[]`) is legal only at the exact point of a variable's declaration — it cannot be used for reassignment, as a method argument, or as a return value.** `int[] a; a = {1, 2, 3};` (reassigning after declaration) and `someMethod({1, 2, 3})` (passing directly as an argument) are both compile errors; both require the full form, `new int[]{1, 2, 3}`.

> **A nested array initializer for a multi-dimensional array does not require every inner array to be the same length** — `int[][] jagged = {{1,2,3}, {4,5}};` is entirely legal Java, producing a "jagged" array where row lengths genuinely differ. If your logic assumes a rectangular shape (every row the same length), validate that explicitly, since the language itself won't enforce it for you.

- The short-form initializer (`{...}`) both allocates and fills an array in one expression, but only at the point of declaration.
- The full form (`new Type[]{...}` or `new Type[][]{...}`) is required anywhere else — reassignment, method arguments, return values — and behaves identically otherwise.
- Nested initializers build multi-dimensional arrays naturally, with each inner `{...}` becoming one row; row lengths are not required to match, so validate rectangularity explicitly if your logic depends on it.
- Use `java.util.Arrays.deepToString` (not plain `toString`) to print a multi-dimensional array's actual contents rather than internal identifiers.
