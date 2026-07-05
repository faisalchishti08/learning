---
card: java
gi: 136
slug: for-loop-init-condition-update
title: for loop (init; condition; update)
---

## 1. What it is

The classic `for` loop packs three pieces of loop machinery into one header, separated by semicolons: an **initialization** (runs once, before anything else), a **condition** (checked before every pass, like `while`), and an **update** (runs after every pass, before the condition is re-checked). All three are optional, but the common form declares a counter, bounds it, and advances it in one place.

```java
for (int i = 0; i < 5; i++) {
    System.out.println("i = " + i);
}
// prints i = 0 through i = 4 — the loop stops once i < 5 becomes false
```

`int i = 0` runs exactly once. `i < 5` is checked before each iteration. `i++` runs after each iteration's body finishes, immediately before the next condition check.

## 2. Why & when

`for` is the idiomatic choice whenever a loop has a **known counting pattern** — a variable that starts somewhere, is bounded by a condition, and is advanced by a fixed step each time:

- Iterating a fixed number of times, or over the indices of an array or `List`.
- Any loop where the "moving parts" (start, stop condition, step) are best read together, in one place, rather than scattered across the loop body like a hand-rolled `while` would require.
- Counting up, counting down, or stepping by something other than 1 (`i += 2`), all expressed naturally in the update clause.

Prefer `while` instead when the loop's continuation depends purely on a condition with no natural "counter" (see [while loop](0134-while-loop.md)). Prefer the enhanced `for` (`for (Type item : collection)`, covered separately) when you just need to visit every element of a collection or array without caring about the index at all.

## 3. Core concept

```java
public class ForDemo {
    public static void main(String[] args) {
        // Counting up
        for (int i = 0; i < 5; i++) {
            System.out.println("up: " + i);
        }

        // Counting down
        for (int i = 5; i > 0; i--) {
            System.out.println("down: " + i);
        }

        // Stepping by 2
        for (int i = 0; i <= 10; i += 2) {
            System.out.println("even: " + i);
        }
    }
}
```

Each header shows all three parts — init, condition, update — read together left to right: "start `i` at some value; keep going while some condition holds; after each pass, change `i` by some step."

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="For loop diagram: init runs once, then condition is checked; if true the body runs, then the update runs, then the condition is re-checked; if false the loop exits.">
  <rect x="8" y="8" width="684" height="179" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">for (init; condition; update) { body }</text>

  <rect x="30" y="42" width="110" height="28" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="61" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">init (once)</text>

  <path d="M 140 56 L 220 56" stroke="#e6edf3" stroke-width="2" marker-end="url(#a)"/>
  <rect x="220" y="42" width="130" height="28" rx="15" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="285" y="61" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">condition?</text>

  <path d="M 350 56 L 430 56" stroke="#79c0ff" stroke-width="2" marker-end="url(#a)"/>
  <text x="390" y="46" fill="#79c0ff" font-size="8.5" font-family="sans-serif">true</text>
  <rect x="430" y="42" width="100" height="28" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="61" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">body</text>

  <path d="M 480 70 L 480 100" stroke="#e6edf3" stroke-width="2" marker-end="url(#a)"/>
  <rect x="430" y="100" width="100" height="28" rx="6" fill="#1c2430" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="480" y="119" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">update</text>

  <path d="M 430 114 C 285 114 285 84 285 70" stroke="#e6edf3" stroke-width="2" fill="none" marker-end="url(#a)"/>
  <text x="330" y="145" fill="#8b949e" font-size="8.5" font-family="sans-serif">back to condition check</text>

  <path d="M 285 42 L 285 20 L 600 20 L 600 42" stroke="#f85149" stroke-width="2" fill="none" marker-end="url(#b)"/>
  <rect x="565" y="42" width="90" height="28" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="610" y="61" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">exit</text>
  <text x="610" y="90" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="sans-serif">false</text>

  <text x="350" y="170" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">init runs once; condition and update repeat every pass, in that order after the body.</text>
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e6edf3"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

Init runs exactly once; condition and update alternate with the body on every subsequent pass.

## 5. Runnable example

Scenario: computing and printing a simple multiplication table row by row — starting with a basic fixed-count loop, then adding a second, nested counting dimension, then hardening it to build the table into a reusable, bounds-checked data structure.

### Level 1 — Basic

```java
public class TableBasic {
    public static void main(String[] args) {
        int n = 5;
        for (int i = 1; i <= 10; i++) {
            System.out.println(n + " x " + i + " = " + (n * i));
        }
    }
}
```

**How to run:** `java TableBasic.java`

`int i = 1` runs once before the loop starts. Before each pass, `i <= 10` is checked; after each pass's body finishes printing one line, `i++` advances the counter. The loop runs exactly 10 times, for `i` equal to `1` through `10`.

### Level 2 — Intermediate

Same multiplication table, now **nested**: an outer `for` loop drives the multiplicand (`n` itself, from 1 to 5), and an inner `for` loop drives `i` as before — a natural extension once a fixed count is needed in two dimensions at once.

```java
public class TableIntermediate {
    public static void main(String[] args) {
        for (int n = 1; n <= 5; n++) {
            for (int i = 1; i <= 10; i++) {
                System.out.println(n + " x " + i + " = " + (n * i));
            }
            System.out.println("---");
        }
    }
}
```

**How to run:** `java TableIntermediate.java`

The outer loop's update (`n++`) only runs after the *entire* inner loop has finished all 10 of its passes — so the inner loop's full init/condition/update cycle repeats fresh for every value of `n`. This is the standard shape of a nested `for` loop: the inner loop is, from the outer loop's perspective, just one (multi-line) statement in its body.

### Level 3 — Advanced

Same nested table, now storing the results into a 2D array using loop counters as indices, and validating the requested table size before looping — a real production concern, since building into a fixed-size array requires the loop bounds to exactly match the array's dimensions.

```java
public class TableAdvanced {

    static int[][] buildTable(int rows, int cols) {
        if (rows <= 0 || cols <= 0) {
            throw new IllegalArgumentException("rows and cols must be positive");
        }
        int[][] table = new int[rows][cols];
        for (int n = 0; n < rows; n++) {
            for (int i = 0; i < cols; i++) {
                table[n][i] = (n + 1) * (i + 1); // +1 so the table starts at 1x1, not 0x0
            }
        }
        return table;
    }

    public static void main(String[] args) {
        int[][] table = buildTable(5, 10);

        for (int n = 0; n < table.length; n++) {
            StringBuilder row = new StringBuilder();
            for (int i = 0; i < table[n].length; i++) {
                row.append(table[n][i]).append("\t");
            }
            System.out.println(row.toString().trim());
        }
    }
}
```

**How to run:** `java TableAdvanced.java`

`buildTable` uses two nested `for` loops whose counters (`n`, `i`) double as array indices directly (`table[n][i]`) — a very common pattern. `table.length` and `table[n].length` are used as the loop bounds instead of hardcoded numbers, so the printing loops automatically match whatever dimensions `buildTable` actually produced, rather than risking a mismatch between a hardcoded bound and the array's real size.

## 6. Walkthrough

Trace `buildTable(2, 3)` conceptually (a smaller table, for clarity):

**Validation.** `rows = 2`, `cols = 3`, both positive, so no exception is thrown. `table = new int[2][3]` allocates a 2-row, 3-column array, all initialized to `0`.

**Outer loop init.** `n = 0`. Condition `n < rows` → `0 < 2` → `true`.

**Inner loop, n = 0.** `i` runs `0`, `1`, `2` (condition `i < cols` fails once `i` reaches `3`). Each pass sets `table[0][i] = (0+1) * (i+1)`, producing `table[0] = {1, 2, 3}`.

**Outer update.** `n++` makes `n = 1`. Condition `1 < 2` → `true`.

**Inner loop, n = 1.** `i` again runs `0` through `2`, setting `table[1][i] = (1+1) * (i+1)`, producing `table[1] = {2, 4, 6}`.

**Outer update.** `n++` makes `n = 2`. Condition `2 < 2` → `false` — outer loop exits.

```
n=0: i=0 table[0][0]=1  i=1 table[0][1]=2  i=2 table[0][2]=3
n=1: i=0 table[1][0]=2  i=1 table[1][1]=4  i=2 table[1][2]=6
n=2: condition n<2 fails -> outer loop exits
```

**Printing.** `main`'s own nested loops walk `table.length` (2) rows and, for each, `table[n].length` (3) columns, building `"1\t2\t3"` for row 0 and `"2\t4\t6"` for row 1 (trimmed of the trailing tab), and printing each row on its own line.

## 7. Gotchas & takeaways

> **A loop variable declared in the `for` header (`for (int i = ...)`) only exists inside the loop** — it goes out of scope the moment the loop ends, so you cannot read its final value after the closing brace unless you declare it *outside* the loop instead.

> **Nested loops reusing the same variable name in inner and outer headers shadow each other correctly (each `int i` or `int n` is scoped to its own loop), but reusing the exact same variable name for both loops in the same scope is a compile error** — Java requires each `for` header's declared variable to be uniquely named within its enclosing scope.

- The three clauses run in a strict order: init once, then repeatedly condition → body → update → condition → ...
- Use `for` when there's a natural counter with a known start, bound, and step; use `while` when the stopping condition isn't naturally expressed as a counter.
- Loop counters make excellent array indices — `table[n][i]` is a standard nested-loop pattern for 2D arrays.
- Prefer `array.length` (or `list.size()`) over a hardcoded bound so loops stay correct if the underlying data's size changes.
