---
card: java
gi: 173
slug: multi-dimensional-arrays
title: Multi-dimensional arrays
---

## 1. What it is

A **multi-dimensional array** is, in Java, really an **array of arrays** — a `int[][] grid` is an array where each element is itself an `int[]`. There is no true built-in "2D block of memory" the way some languages have; `grid[i]` gives you row `i` (an `int[]`), and `grid[i][j]` gives you the element at column `j` of that row. This "array of arrays" model is what allows Java's jagged arrays (covered next) to exist at all.

```java
int[][] grid = new int[3][4]; // 3 rows, each with 4 columns
grid[1][2] = 99;              // row 1, column 2
System.out.println(grid[1][2]); // 99
System.out.println(grid.length);    // 3 — number of rows
System.out.println(grid[0].length); // 4 — number of columns in row 0
```

`grid.length` is the number of rows; `grid[i].length` is the number of columns *in that specific row* — a distinction that matters once jagged (uneven) arrays enter the picture.

## 2. Why & when

Multi-dimensional arrays model data that naturally has more than one axis:

- **Grids and boards** — a tic-tac-toe board, a chessboard, a spreadsheet, pixels in an image (`int[][]` or `int[][][]` for width, height, colour channels).
- **Tables of related values** — a seating chart (`row`, `seat`), a matrix for mathematical operations, a lookup table indexed by two keys.
- **Higher dimensions when needed** — `int[][][] cube` for a 3D voxel grid — Java allows arbitrarily many dimensions, though beyond 2 or 3 it's often clearer to use a class or a flat array with computed indices.

You reach for a 2D array specifically when your data is naturally row-and-column shaped and both dimensions are known at creation time (or can grow as jagged rows); if the data is really "a list of independent things," a `List<List<T>>` or an array of objects usually models the domain more clearly.

## 3. Core concept

```java
public class GridDemo {
    public static void main(String[] args) {
        int[][] grid = new int[3][4]; // 3 rows, 4 columns each, all initialized to 0

        for (int row = 0; row < grid.length; row++) {
            for (int col = 0; col < grid[row].length; col++) {
                grid[row][col] = row * 10 + col; // fill each cell with a computed value
            }
        }

        for (int row = 0; row < grid.length; row++) {
            System.out.println(java.util.Arrays.toString(grid[row]));
        }
    }
}
```

The outer loop walks rows (`0` to `grid.length - 1`); the inner loop walks columns *within that specific row* (`0` to `grid[row].length - 1`) — writing `grid[row].length` rather than reusing the outer bound is what makes this pattern correctly handle jagged arrays too, since each row could in principle have a different length.

## 4. Diagram

<svg viewBox="0 0 500 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A 2D array shown as grid dot length equals 3 rows, each row itself being a separate one dimensional array of 4 columns, with grid row 1 column 2 pointing at a specific cell">
  <rect x="8" y="8" width="484" height="204" rx="8" fill="#0d1117"/>
  <text x="250" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">grid (int[][], grid.length == 3 rows)</text>

  <text x="30" y="55" fill="#79c0ff" font-size="11" font-family="sans-serif">grid[0]</text>
  <rect x="100" y="40" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="150" y="40" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="200" y="40" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="250" y="40" width="50" height="30" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="105" fill="#79c0ff" font-size="11" font-family="sans-serif">grid[1]</text>
  <rect x="100" y="90" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="150" y="90" width="50" height="30" fill="#1c2430" stroke="#6db33f"/>
  <rect x="200" y="90" width="50" height="30" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="225" y="110" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">99</text>
  <rect x="250" y="90" width="50" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="360" y="110" fill="#79c0ff" font-size="9" font-family="sans-serif">grid[1][2] = 99</text>

  <text x="30" y="155" fill="#79c0ff" font-size="11" font-family="sans-serif">grid[2]</text>
  <rect x="100" y="140" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="150" y="140" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="200" y="140" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="250" y="140" width="50" height="30" fill="#1c2430" stroke="#6db33f"/>

  <text x="250" y="195" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Each grid[row] is itself an independent int[] — an "array of arrays."</text>
</svg>

`grid[row][col]`: first index picks the row-array, second index picks the element within it.

## 5. Runnable example

Scenario: managing a small movie theatre's seating chart — starting with a basic 2D array creation and fill, then extending to book and check individual seats, then hardening into a method that reports total available seats per row and overall occupancy.

### Level 1 — Basic

```java
public class TheatreBasic {
    public static void main(String[] args) {
        boolean[][] seats = new boolean[3][5]; // 3 rows, 5 seats each, all false ("empty")

        System.out.println("Rows: " + seats.length);
        System.out.println("Seats per row: " + seats[0].length);
    }
}
```

**How to run:** `java TheatreBasic.java`

`new boolean[3][5]` allocates 3 row-arrays, each holding 5 `boolean` values defaulted to `false` — `seats.length` reports the row count (`3`), `seats[0].length` reports that row's seat count (`5`).

### Level 2 — Intermediate

Same theatre, now booking specific seats and checking their status through both indices.

```java
public class TheatreIntermediate {
    public static void main(String[] args) {
        boolean[][] seats = new boolean[3][5];

        seats[0][2] = true; // book row 0, seat 2
        seats[1][4] = true; // book row 1, seat 4

        for (int row = 0; row < seats.length; row++) {
            for (int seat = 0; seat < seats[row].length; seat++) {
                System.out.print(seats[row][seat] ? "X" : ".");
            }
            System.out.println();
        }
    }
}
```

**How to run:** `java TheatreIntermediate.java`

`seats[0][2] = true` writes into row `0`'s array at column `2`; the nested loop then prints every row as a line of `X` (booked) and `.` (empty) characters, giving a visual seating chart across all 3 rows and 5 seats.

### Level 3 — Advanced

Same theatre, now with jagged rows (the back row has fewer seats due to a walkway) and a method reporting occupancy correctly despite the rows having different lengths.

```java
public class TheatreAdvanced {

    static void printOccupancy(boolean[][] seats) {
        int totalSeats = 0;
        int totalBooked = 0;
        for (int row = 0; row < seats.length; row++) {
            int bookedInRow = 0;
            for (int seat = 0; seat < seats[row].length; seat++) { // use THIS row's own length
                if (seats[row][seat]) {
                    bookedInRow++;
                }
            }
            totalSeats += seats[row].length;
            totalBooked += bookedInRow;
            System.out.println("Row " + row + ": " + bookedInRow + "/" + seats[row].length + " booked");
        }
        System.out.println("Overall: " + totalBooked + "/" + totalSeats + " booked");
    }

    public static void main(String[] args) {
        boolean[][] seats = {
            new boolean[5],       // front row: 5 seats
            new boolean[5],       // middle row: 5 seats
            new boolean[3]        // back row: only 3 seats (walkway takes the rest)
        };

        seats[0][2] = true;
        seats[2][0] = true;
        seats[2][1] = true;

        printOccupancy(seats);
    }
}
```

**How to run:** `java TheatreAdvanced.java`

The inner loop's bound is `seats[row].length`, **not** a shared constant — this is essential here because the back row (`seats[2]`) genuinely has only 3 seats while the other rows have 5; using a single shared bound for all rows would either miss seats in shorter rows or throw `ArrayIndexOutOfBoundsException` reaching past them.

## 6. Walkthrough

Trace `printOccupancy(seats)` for the theatre configured in Level 3:

**Row 0.** `seats[0].length` is `5`. Scanning columns `0..4`: only `seats[0][2]` is `true` (from `seats[0][2] = true`), so `bookedInRow = 1`. Prints `"Row 0: 1/5 booked"`. Running totals: `totalSeats = 5`, `totalBooked = 1`.

**Row 1.** `seats[1].length` is `5`. No seat in this row was set to `true`, so `bookedInRow = 0`. Prints `"Row 1: 0/5 booked"`. Running totals: `totalSeats = 10`, `totalBooked = 1`.

**Row 2.** `seats[2].length` is `3` (the shorter, jagged row). Scanning columns `0..2`: both `seats[2][0]` and `seats[2][1]` are `true`, `seats[2][2]` is `false`, so `bookedInRow = 2`. Prints `"Row 2: 2/3 booked"`. Running totals: `totalSeats = 13`, `totalBooked = 3`.

**Final line.** After the loop, `System.out.println("Overall: 3/13 booked")`.

```
Row 0 (5 seats): . . X . .   -> 1 booked
Row 1 (5 seats): . . . . .   -> 0 booked
Row 2 (3 seats): X X .       -> 2 booked
Overall: 3 booked / 13 total seats
```

## 7. Gotchas & takeaways

> **Java has no true 2D array type — `int[][]` is an array of `int[]` references.** This is *why* jagged arrays (rows of different lengths) are legal in Java, unlike in languages with genuine rectangular matrix types. It also means `grid[0]` alone is a perfectly valid, complete `int[]` you can pass around independently.

> **Always use `array[row].length` for the inner loop bound, not a single shared "number of columns" constant**, unless you are certain every row is the same length. Assuming uniform length when rows might be jagged is a common source of `ArrayIndexOutOfBoundsException` or silently-skipped elements.

- `grid[i][j]`: the first index selects a row (itself an independent array); the second selects an element within that row.
- `grid.length` is the row count; `grid[i].length` is that specific row's column count — they can differ if the array is jagged.
- `new Type[rows][cols]` creates a fully rectangular array upfront, with every row the same length and every element defaulted.
- Nested loops over 2D arrays should use `grid[row].length` (not the outer bound) as the inner loop's limit, to correctly and safely handle jagged rows.
