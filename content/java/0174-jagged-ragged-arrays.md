---
card: java
gi: 174
slug: jagged-ragged-arrays
title: Jagged (ragged) arrays
---

## 1. What it is

A **jagged array** (also called a **ragged array**) is a multi-dimensional array whose rows are **not all the same length** — because Java implements `int[][]` as an array of independently-sized `int[]` row-arrays (as the previous topic explained), nothing forces those rows to be equal in length. Each row can be created, or initialized, with whatever size makes sense for it.

```java
int[][] jagged = new int[3][];  // 3 rows, but no column count yet — each row starts as null
jagged[0] = new int[]{ 1 };
jagged[1] = new int[]{ 1, 2, 3 };
jagged[2] = new int[]{ 1, 2 };

System.out.println(jagged[0].length); // 1
System.out.println(jagged[1].length); // 3
System.out.println(jagged[2].length); // 2
```

`new int[3][]` (note the empty second bracket) creates only the **outer** array of 3 row-references, each initially `null`; each row must then be separately assigned its own array, of whatever length is appropriate.

## 2. Why & when

Jagged arrays exist because real-world "table-like" data is often genuinely uneven:

- **A triangular structure** — Pascal's triangle, where row `i` has `i + 1` elements.
- **Per-item variable data** — a list of students, each with a different number of grades; a list of sentences, each with a different number of words after splitting.
- **Sparse or irregular layouts** — a theatre with a walkway removing seats from one row (as in the previous topic's Level 3), or a calendar month where some weeks have fewer visible days.

You reach for a jagged array specifically when the "rectangular" (every row same length) assumption of a plain 2D array doesn't fit your data; if all rows genuinely are — or should be — the same length, a uniform `new Type[rows][cols]` is simpler and communicates that invariant more clearly.

## 3. Core concept

```java
public class JaggedDemo {
    public static void main(String[] args) {
        int[][] triangle = new int[4][]; // 4 rows, each row's length still undecided

        for (int row = 0; row < triangle.length; row++) {
            triangle[row] = new int[row + 1]; // row 0 has 1 element, row 1 has 2, etc.
            for (int col = 0; col <= row; col++) {
                triangle[row][col] = col;
            }
        }

        for (int[] r : triangle) {
            System.out.println(java.util.Arrays.toString(r));
        }
    }
}
```

`triangle[row] = new int[row + 1]` assigns a **freshly sized** row array on each iteration — row `0` gets 1 slot, row `1` gets 2, row `2` gets 3, row `3` gets 4 — building a triangular shape where `triangle[row].length` genuinely differs from row to row, which is the defining feature of a jagged array.

## 4. Diagram

<svg viewBox="0 0 500 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A triangular jagged array where row 0 has one cell, row 1 has two cells, row 2 has three cells, and row 3 has four cells, each row a different length">
  <rect x="8" y="8" width="484" height="184" rx="8" fill="#0d1117"/>
  <text x="250" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">triangle[row] = new int[row + 1] — each row a different length</text>

  <rect x="230" y="40" width="40" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="278" y="60" fill="#8b949e" font-size="9" font-family="sans-serif">row 0: length 1</text>

  <rect x="210" y="80" width="40" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="250" y="80" width="40" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="298" y="100" fill="#8b949e" font-size="9" font-family="sans-serif">row 1: length 2</text>

  <rect x="190" y="120" width="40" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="230" y="120" width="40" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="270" y="120" width="40" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="318" y="140" fill="#8b949e" font-size="9" font-family="sans-serif">row 2: length 3</text>

  <rect x="170" y="160" width="40" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="210" y="160" width="40" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="250" y="160" width="40" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="290" y="160" width="40" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="338" y="180" fill="#8b949e" font-size="9" font-family="sans-serif">row 3: length 4</text>
</svg>

Each row's length is chosen independently — jagged arrays have no requirement that rows match.

## 5. Runnable example

Scenario: storing each student's individual quiz scores, where different students have taken different numbers of quizzes — starting with basic jagged creation, then extending to compute per-student averages, then hardening into a method that safely handles a student with zero quizzes recorded.

### Level 1 — Basic

```java
public class StudentScoresBasic {
    public static void main(String[] args) {
        int[][] scores = {
            { 85, 90, 78 },      // student 0 took 3 quizzes
            { 92, 88 },          // student 1 took 2 quizzes
            { 70, 75, 80, 65 }   // student 2 took 4 quizzes
        };

        for (int student = 0; student < scores.length; student++) {
            System.out.println("Student " + student + " took " + scores[student].length + " quizzes");
        }
    }
}
```

**How to run:** `java StudentScoresBasic.java`

Each row of `scores` has a different length (`3`, `2`, `4`) — this is a jagged array built directly from a nested initializer, since nothing requires the inner `{...}` groups to match in size.

### Level 2 — Intermediate

Same data, now computing each student's average score, correctly using each row's own `.length` as the divisor.

```java
public class StudentScoresIntermediate {
    public static void main(String[] args) {
        int[][] scores = {
            { 85, 90, 78 },
            { 92, 88 },
            { 70, 75, 80, 65 }
        };

        for (int student = 0; student < scores.length; student++) {
            int sum = 0;
            for (int quiz : scores[student]) {
                sum += quiz;
            }
            double average = (double) sum / scores[student].length;
            System.out.println("Student " + student + " average: " + average);
        }
    }
}
```

**How to run:** `java StudentScoresIntermediate.java`

`scores[student].length` (not a shared constant) is used as the divisor for each student's own average — essential here since student 1 took only 2 quizzes while student 2 took 4, and dividing by the wrong count would silently produce an incorrect average.

### Level 3 — Advanced

Same scenario, now hardened against a student with **zero** recorded quizzes — an empty row (`new int[0]`) — which would otherwise cause a division by zero.

```java
public class StudentScoresAdvanced {

    static String describeAverage(int[] studentScores) {
        if (studentScores.length == 0) {
            return "no quizzes recorded";
        }
        int sum = 0;
        for (int quiz : studentScores) {
            sum += quiz;
        }
        double average = (double) sum / studentScores.length;
        return "average " + average;
    }

    public static void main(String[] args) {
        int[][] scores = {
            { 85, 90, 78 },
            { 92, 88 },
            {},                 // student 2: enrolled late, no quizzes yet
            { 70, 75, 80, 65 }
        };

        for (int student = 0; student < scores.length; student++) {
            System.out.println("Student " + student + ": " + describeAverage(scores[student]));
        }
    }
}
```

**How to run:** `java StudentScoresAdvanced.java`

`if (studentScores.length == 0)` is checked before any division happens, so a student with an empty row (`{}`, a legal zero-length array) is reported as `"no quizzes recorded"` rather than crashing with `ArithmeticException` or producing `NaN` from a `0.0 / 0` division.

## 6. Walkthrough

Trace `describeAverage` across all four students in `StudentScoresAdvanced`:

**Student 0.** `scores[0] = {85, 90, 78}`, length `3`, not zero. Sum is `85 + 90 + 78 = 253`. Average is `253.0 / 3 ≈ 84.33`. Returns `"average 84.33..."`.

**Student 1.** `scores[1] = {92, 88}`, length `2`. Sum is `180`. Average is `90.0`. Returns `"average 90.0"`.

**Student 2.** `scores[2] = {}`, an empty array literal — `.length` is `0`. The guard `studentScores.length == 0` is true, so the method returns immediately with `"no quizzes recorded"`, never reaching the summing loop at all.

**Student 3.** `scores[3] = {70, 75, 80, 65}`, length `4`. Sum is `290`. Average is `72.5`. Returns `"average 72.5"`.

```
student 0: length 3, sum 253 -> average 84.33
student 1: length 2, sum 180 -> average 90.0
student 2: length 0 -> guard fires -> "no quizzes recorded" (no division attempted)
student 3: length 4, sum 290 -> average 72.5
```

**Final output.** Four lines, one per student, each prefixed `"Student N: "` followed by either an average or the "no quizzes recorded" message — exactly the return values traced above, printed in student order.

## 7. Gotchas & takeaways

> **`new int[3][]` allocates only the outer array — each of the 3 rows starts out `null`**, not an empty array. Accessing `jagged[0].length` before assigning `jagged[0] = new int[...]` throws `NullPointerException`, not `ArrayIndexOutOfBoundsException` — a common point of confusion since the failure mode differs from the usual array-bounds mistake.

> **An empty row (`new int[0]` or `{}`) is a legal, non-null array of length `0`** — it is a completely different situation from a `null` row. Always check `.length == 0` for "no elements" and reserve null-checks for "row not yet assigned at all."

- A jagged array is an array of arrays where the inner arrays are allowed to have different lengths.
- `new Type[n][]` creates only the outer array; each inner row must be separately assigned before use, or it stays `null`.
- Never assume a shared column count across rows — always read each row's own `.length` when processing a jagged array.
- Distinguish a `null` row (never assigned) from a legally empty row of length `0` (assigned, but holding nothing) — they require different handling.
