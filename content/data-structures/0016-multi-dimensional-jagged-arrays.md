---
card: data-structures
gi: 16
slug: multi-dimensional-jagged-arrays
title: Multi-dimensional & jagged arrays
---

## 1. What it is

A **multi-dimensional array** models a grid — rows and columns, like `int[][] grid = new int[3][4]`. In Java this is not one contiguous block; it is an **array of arrays**: `grid` is an array of 3 references, each pointing to its own separate `int[4]` row. A **jagged array** takes this a step further and lets each row have a *different* length, since each row is an independently allocated array.

## 2. Why & when

Use a rectangular 2D array when every row genuinely has the same width, like a fixed game board or a matrix in linear algebra. Use a jagged array when rows naturally differ in length, like an adjacency list for a graph (each node has a different number of neighbors) or a triangular table. Knowing that Java arrays-of-arrays are really separate objects explains why rows can have different lengths at all.

## 3. Core concept

**The structure: an outer array of references.** `new int[3][4]` allocates one outer `int[3]` array, whose 3 slots are references, plus 3 separate inner `int[4]` arrays. Reading `grid[1][2]` first follows the reference in `grid[1]` to find the second row, then indexes into that row's 3rd slot.

**Why rows can be jagged.** Because each row is a fully independent array object, nothing requires them to be the same length. `int[][] jagged = new int[3][];` allocates only the outer array; each `jagged[i] = new int[someLength];` is a separate allocation you control.

**Cost of the extra indirection.** A true 2D access in Java costs two array lookups (outer, then inner), versus one lookup plus arithmetic for a flattened 1D array simulating a grid (`flat[row * width + col]`). The flattened form is more cache-friendly for large rectangular grids, at the cost of manual index math.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An outer array of 3 references, each pointing to an inner row array of a different length">
  <g font-family="sans-serif" font-size="12">
    <text x="100" y="20" fill="#8b949e" text-anchor="middle">outer array (references)</text>
    <rect x="30" y="30" width="60" height="30" fill="#161b22" stroke="#79c0ff"/><text x="60" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">row0</text>
    <rect x="30" y="60" width="60" height="30" fill="#161b22" stroke="#79c0ff"/><text x="60" y="80" fill="#e6edf3" text-anchor="middle" font-size="10">row1</text>
    <rect x="30" y="90" width="60" height="30" fill="#161b22" stroke="#79c0ff"/><text x="60" y="110" fill="#e6edf3" text-anchor="middle" font-size="10">row2</text>

    <line x1="90" y1="45" x2="200" y2="45" stroke="#79c0ff" marker-end="url(#a3)"/>
    <line x1="90" y1="75" x2="200" y2="75" stroke="#79c0ff" marker-end="url(#a3)"/>
    <line x1="90" y1="105" x2="200" y2="115" stroke="#79c0ff" marker-end="url(#a3)"/>
    <defs><marker id="a3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#79c0ff"/></marker></defs>

    <rect x="200" y="30" width="140" height="26" fill="#0d1117" stroke="#3fb950"/><text x="270" y="47" fill="#e6edf3" text-anchor="middle" font-size="10">[1, 2, 3, 4]</text>
    <rect x="200" y="60" width="80" height="26" fill="#0d1117" stroke="#3fb950"/><text x="240" y="77" fill="#e6edf3" text-anchor="middle" font-size="10">[5, 6]</text>
    <rect x="200" y="105" width="200" height="26" fill="#0d1117" stroke="#3fb950"/><text x="300" y="122" fill="#e6edf3" text-anchor="middle" font-size="10">[7, 8, 9, 10, 11]</text>

    <text x="320" y="170" fill="#79c0ff" text-anchor="middle">each row is a separate array object — rows can have different lengths (jagged)</text>
  </g>
</svg>

The outer array holds only references. Each row is its own independently sized array object, so nothing forces rows to match in length.

## 5. Runnable example

```java
// MultiDimensionalJaggedArrays.java
import java.util.Arrays;

public class MultiDimensionalJaggedArrays {

    // Basic: a true rectangular 2D array, every row the same width.
    static void basicLevel() {
        int[][] grid = new int[3][4]; // 3 rows, each exactly 4 columns
        grid[1][2] = 99;
        System.out.println("basic: grid -> " + Arrays.deepToString(grid));
        System.out.println("basic: row lengths -> " + grid[0].length + ", " + grid[1].length + ", " + grid[2].length);
    }

    // Intermediate: a jagged array, each row a different length.
    static void intermediateLevel() {
        int[][] jagged = new int[3][]; // only the outer array is allocated so far
        jagged[0] = new int[]{1, 2, 3, 4};
        jagged[1] = new int[]{5, 6};
        jagged[2] = new int[]{7, 8, 9, 10, 11};
        System.out.println("intermediate: jagged -> " + Arrays.deepToString(jagged));
        for (int i = 0; i < jagged.length; i++) {
            System.out.println("intermediate: row " + i + " length -> " + jagged[i].length);
        }
    }

    // Advanced: building a jagged adjacency list for a small graph (a real use of jagged arrays).
    static void advancedLevel() {
        // node 0 -> [1,2], node 1 -> [0], node 2 -> [0,3], node 3 -> [2]
        int[][] adjacency = {
            {1, 2},
            {0},
            {0, 3},
            {2}
        };
        for (int node = 0; node < adjacency.length; node++) {
            System.out.println("advanced: node " + node + " neighbors -> " + Arrays.toString(adjacency[node]));
        }
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `MultiDimensionalJaggedArrays.java`, then run `java MultiDimensionalJaggedArrays.java`.

## 6. Walkthrough

1. `basicLevel()` allocates `grid` as `new int[3][4]`. Java actually allocates the outer `int[3]` array of references, then eagerly allocates 3 inner `int[4]` arrays, one per row, all the same length.
2. `grid[1][2] = 99` follows the reference in `grid[1]` to find row 1's array, then writes index 2 of that row — two lookups total.
3. `intermediateLevel()` allocates only the outer array with `new int[3][]`, leaving each row `null` until explicitly assigned. Each `jagged[i] = new int[]{...}` is an independent allocation, so the three rows end up with lengths 4, 2, and 5.
4. Printing each row's length confirms they differ — this is only possible because rows are separate array objects, not slices of one shared block.
5. `advancedLevel()` uses a jagged array as a graph adjacency list: node 0 has 2 neighbors, node 1 has 1, and so on — exactly the case where a rectangular array would waste space padding shorter rows.

## 7. Gotchas & takeaways

> Gotcha: `new int[3][]` leaves every row as `null`, not an empty array — indexing into an unassigned row (`jagged[0][0]` before `jagged[0]` is set) throws `NullPointerException`, not `ArrayIndexOutOfBoundsException`. Always assign every row before reading from it.

- Java has no true multi-dimensional array type — `int[][]` is an array of array *references*, which is why jagged rows are possible.
- A jagged array's rows can have different lengths because each row is its own independent array object.
- Rectangular 2D access costs two array lookups; a flattened 1D array (`row * width + col`) trades manual index math for better cache locality.
- Related concepts: [Contiguous memory & cache locality](0017-contiguous-memory-cache-locality.md) (why flattening can be faster), [Arrays as objects in the JVM](0013-arrays-as-objects-in-the-jvm.md).
