---
card: java
gi: 178
slug: java-util-arrays-fill
title: java.util.Arrays.fill()
---

## 1. What it is

`java.util.Arrays.fill()` is a static utility method that sets **every element** of an array (or a specified sub-range of it) to the same given value, in place. It works on arrays of any primitive type and on object arrays, replacing what would otherwise be a manual `for` loop with a single, clear method call.

```java
int[] scores = new int[5];
java.util.Arrays.fill(scores, 100); // every element becomes 100
System.out.println(java.util.Arrays.toString(scores)); // [100, 100, 100, 100, 100]

int[] partial = new int[6];
java.util.Arrays.fill(partial, 1, 4, 9); // fill only indices 1..3 (toIndex exclusive) with 9
System.out.println(java.util.Arrays.toString(partial)); // [0, 9, 9, 9, 0, 0]
```

The four-argument form (`array, fromIndex, toIndex, value`) fills only the sub-range `[fromIndex, toIndex)` — `toIndex` is exclusive, matching the same convention used throughout `java.util.Arrays` and the wider Java collections API.

## 2. Why & when

`fill()` exists to replace the extremely common pattern of manually looping just to set every slot to the same starting value:

- **Initializing arrays to a non-default starting value** — array elements default to `0`/`false`/`null`, but a game board might need every cell to start as `'.'`, or a scoreboard might need every score to start at a specific baseline other than zero.
- **Resetting an array between uses** — clearing out old data by overwriting every slot with a sentinel value (like `-1` for "unset") before reusing the same array.
- **Filling a specific sub-range** — initializing only part of a larger array, leaving the rest at its original values, useful when different sections of one array represent different logical regions.

Reach for `fill()` instead of writing a manual loop whenever every element (or every element in a clear sub-range) needs to become the *same* value — for anything more complex, like computing each element from its index, a loop is still the right tool.

## 3. Core concept

```java
public class FillDemo {
    public static void main(String[] args) {
        boolean[] visited = new boolean[5];
        java.util.Arrays.fill(visited, false); // explicit, though false is already the default

        char[] board = new char[9];
        java.util.Arrays.fill(board, '.'); // every cell starts as an empty dot
        System.out.println(new String(board));

        String[] labels = new String[3];
        java.util.Arrays.fill(labels, "unassigned"); // works for object arrays too — same reference in every slot
        System.out.println(java.util.Arrays.toString(labels));
    }
}
```

For an object array like `String[] labels`, `fill()` puts the **same single reference** into every slot — here that's harmless since `String` is immutable, but filling an array of a *mutable* object type with `fill()` would mean every slot points to the exact same shared object, so mutating it through one index would be visible through every other index too.

## 4. Diagram

<svg viewBox="0 0 560 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An array of five zero-valued slots transformed by Arrays dot fill into five slots all holding the value 100">
  <rect x="8" y="8" width="544" height="114" rx="8" fill="#0d1117"/>
  <text x="280" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Arrays.fill(scores, 100)</text>

  <text x="60" y="50" fill="#8b949e" font-size="10" font-family="sans-serif">before:</text>
  <rect x="110" y="35" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="130" y="54" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">0</text>
  <rect x="150" y="35" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="170" y="54" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">0</text>
  <rect x="190" y="35" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="210" y="54" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">0</text>
  <rect x="230" y="35" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="250" y="54" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">0</text>
  <rect x="270" y="35" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="290" y="54" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">0</text>

  <text x="280" y="80" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">↓ every slot set to 100 ↓</text>

  <text x="60" y="105" fill="#8b949e" font-size="10" font-family="sans-serif">after:</text>
  <rect x="110" y="90" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="130" y="109" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">100</text>
  <rect x="150" y="90" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="170" y="109" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">100</text>
  <rect x="190" y="90" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="210" y="109" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">100</text>
  <rect x="230" y="90" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="250" y="109" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">100</text>
  <rect x="270" y="90" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="290" y="109" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">100</text>
</svg>

`fill()` overwrites every targeted slot with one identical value, in place.

## 5. Runnable example

Scenario: initializing and resetting a tic-tac-toe board — starting with a basic full-board fill, then extending to reset only a sub-range (a single row), then hardening into a "new game" method that fills the board and validates it was reset correctly before returning it.

### Level 1 — Basic

```java
public class BoardFillBasic {
    public static void main(String[] args) {
        char[] board = new char[9]; // 3x3 board, flattened into one array

        java.util.Arrays.fill(board, '.');
        System.out.println(new String(board));
    }
}
```

**How to run:** `java BoardFillBasic.java`

`Arrays.fill(board, '.')` sets all 9 slots to `'.'` in a single call, replacing what would otherwise take a manual `for` loop — `new String(board)` then converts the `char[]` into a printable `String`.

### Level 2 — Intermediate

Same board, now resetting only the middle row (a sub-range) back to empty after a player made moves there, leaving the rest of the board untouched.

```java
public class BoardFillIntermediate {
    public static void main(String[] args) {
        char[] board = new char[9];
        java.util.Arrays.fill(board, '.');

        board[3] = 'X'; board[4] = 'O'; board[5] = 'X'; // middle row gets some moves

        System.out.println("Before reset: " + new String(board));

        java.util.Arrays.fill(board, 3, 6, '.'); // reset only indices 3..5 (the middle row)

        System.out.println("After reset:  " + new String(board));
    }
}
```

**How to run:** `java BoardFillIntermediate.java`

`Arrays.fill(board, 3, 6, '.')` touches only indices `3`, `4`, `5` (since `toIndex=6` is exclusive) — the first row (indices `0-2`) and last row (indices `6-8`) are completely unaffected, demonstrating the sub-range form's precision.

### Level 3 — Advanced

Same board, now wrapped in a "new game" method that fills the board and then verifies, defensively, that every slot really was reset before handing the board back — useful as a sanity check in a larger game engine where the board array might be shared or reused across game instances.

```java
import java.util.Arrays;

public class BoardFillAdvanced {

    static char[] newGameBoard(int size) {
        char[] board = new char[size];
        Arrays.fill(board, '.');

        for (int i = 0; i < board.length; i++) {
            if (board[i] != '.') {
                throw new IllegalStateException("Board slot " + i + " failed to reset");
            }
        }
        return board;
    }

    public static void main(String[] args) {
        char[] board = newGameBoard(9);
        System.out.println("New board: " + new String(board));

        board[0] = 'X'; // simulate a move
        System.out.println("After a move: " + new String(board));

        char[] freshBoard = newGameBoard(9); // starting a second game
        System.out.println("Second game board: " + new String(freshBoard));
    }
}
```

**How to run:** `java BoardFillAdvanced.java`

`newGameBoard` calls `Arrays.fill` and then explicitly verifies every slot equals `'.'` before returning — this is a defensive double-check appropriate in a context where the fill's correctness is a precondition other code depends on; the verification loop will never actually trigger the `IllegalStateException` here since `Arrays.fill` is a reliable standard-library method, but it documents and guards the invariant explicitly.

## 6. Walkthrough

Trace `BoardFillAdvanced.main`:

**First call.** `newGameBoard(9)` allocates a fresh 9-element `char[]` (each element defaulting to `' '`, the default `char`), then `Arrays.fill(board, '.')` overwrites all 9 slots with `'.'`. The verification loop checks each of the 9 slots equals `'.'` — all pass, so no exception. Returns the board. `main` prints `"New board: ........."`.

**Simulated move.** `board[0] = 'X'` changes only index `0`. Printing now shows `"After a move: X........"`.

**Second call.** `newGameBoard(9)` runs completely independently — it allocates a **brand-new** `char[9]`, unrelated to the first `board` variable, fills it, verifies it, and returns it as `freshBoard`. Since `board` and `freshBoard` are different array objects, the earlier move (`board[0] = 'X'`) has no effect on `freshBoard` at all.

```
call 1: newGameBoard(9) -> board       = "........."
board[0] = 'X'          -> board       = "X........"
call 2: newGameBoard(9) -> freshBoard  = "........." (independent array, unaffected by board's move)
```

**Final output.** Three lines: `"New board: ........."`, `"After a move: X........."`, `"Second game board: ........."` — confirming the second board starts completely fresh regardless of what happened to the first.

## 7. Gotchas & takeaways

> **`Arrays.fill(objectArray, sameObject)` puts the identical object reference into every slot, not independent copies.** For an immutable type like `String` this is harmless, but for a mutable object, mutating the value through one index would be visible through every other index, since they all point at the exact same object in memory.

> **The sub-range form's `toIndex` is exclusive**, matching `Arrays.sort` and `Arrays.binarySearch`'s convention — `fill(array, 1, 4, x)` touches indices `1, 2, 3`, not `1, 2, 3, 4`. Forgetting this off-by-one when computing a sub-range is a common source of subtly wrong results.

- `Arrays.fill(array, value)` overwrites every element with the same value, in place.
- `Arrays.fill(array, fromIndex, toIndex, value)` restricts the fill to a sub-range, with `toIndex` exclusive.
- Works on primitive and object arrays alike, though filling an object array puts the same shared reference into every slot.
- Reach for `fill()` instead of a manual loop whenever every targeted element should become one identical value.
