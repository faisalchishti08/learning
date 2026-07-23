---
card: leetcode-patterns
gi: 254
slug: kth-smallest-number-in-multiplication-table
title: Kth Smallest Number in Multiplication Table
---

## 1. What it is

A multiplication table has `m` rows and `n` columns, where the cell at `(row, col)` (1-indexed) holds `row * col`. Given `m`, `n`, and `k`, return the `k`-th smallest value in the table. Example: `m = 3`, `n = 3`, `k = 5` → `3` (the sorted table values are `1,1,2,2,3,3,4,6,9`, and the 5th is `3`).

## 2. Why & when

The table has up to `m * n` cells — far too many to sort directly for large inputs. But "how many cells hold a value `<= x`?" is easy to compute directly (row by row) and grows monotonically with `x`. Use this shape whenever a problem asks for the k-th smallest value in an implicitly huge, structured collection, and you can count "how many values are `<= x`" without listing them all.

## 3. Core concept

**Key idea:** binary search over candidate VALUES `x` (from `1` to `m * n`), not over table positions. For each `x`, count how many cells hold a value `<= x`: for row `r`, the count of columns `c` where `r * c <= x` is `min(n, x / r)` (capped at `n` columns). Summing over all rows gives `countLessOrEqual(x)`. Find the smallest `x` where this count is `>= k` — that `x` is the k-th smallest value.

**Steps:**
1. Set `lo = 1`, `hi = m * n`.
2. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`.
3. Compute `count = countLessOrEqual(mid)`: for each row `r` from `1` to `m`, add `min(n, mid / r)`.
4. If `count >= k`, `mid` might be the answer or the answer might be smaller: set `hi = mid`.
5. Otherwise, `mid` is too small: set `lo = mid + 1`.
6. When the loop ends, `lo == hi` is the k-th smallest value.

**Why it is correct:** `countLessOrEqual(x)` is monotonically non-decreasing as `x` increases (a larger threshold only ever includes as many or more cells). "Is `countLessOrEqual(x) >= k`?" is therefore false for small `x` and true from some point onward — and that flip point is exactly the k-th smallest value, because it is the smallest `x` for which at least `k` cells hold a value `<= x`. The value must actually appear in the table (not just be "between" two table values), since `countLessOrEqual` only changes at values that ARE achievable as `row * col` for some row.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="3x3 table, x=3, row1 has 3 cells at most 3, row2 has 1 cell, row3 has 1 cell, total count 5">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">m=3, n=3, k=5; counting cells &lt;= x=3</text>
    <text x="10" y="45">row 1: min(3, 3/1)=3 cells (1,2,3)</text>
    <text x="10" y="65">row 2: min(3, 3/2)=1 cell (2)</text>
    <text x="10" y="85">row 3: min(3, 3/3)=1 cell (3)</text>
    <rect x="10" y="95" width="30" height="24" fill="#3fb950"/><text x="25" y="112" fill="#0d1117" text-anchor="middle" font-size="9">5</text>
    <text x="45" y="112">total count = 3+1+1 = 5 &gt;= k=5</text>
    <text x="10" y="140">x=3 is the 5th smallest value in the table</text>
  </g>
</svg>

Counting how many cells are at most `x`, row by row, avoids ever generating or sorting the full table.

## 5. Runnable example

```java
// KthSmallestNumberInMultiplicationTable.java
public class KthSmallestNumberInMultiplicationTable {

    // Level 1 -- Brute force: generate every cell value into an array
    // of size m*n, sort it, and return the (k-1)-th element. Correct,
    // but O(m*n*log(m*n)) time and O(m*n) space -- infeasible for
    // large m and n.

    // KEY INSIGHT: countLessOrEqual(x) can be computed in O(m) time
    // directly, row by row, without generating any cell values. Since
    // this count is monotonic in x, binary search over x finds the
    // k-th smallest value in O(m log(m*n)) time and O(1) space.

    // Level 2 -- Optimal: binary search on the answer.
    static int findKthNumber(int m, int n, int k) {
        int lo = 1, hi = m * n;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (countLessOrEqual(m, n, mid) >= k) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    static int countLessOrEqual(int m, int n, int x) {
        int count = 0;
        for (int row = 1; row <= m; row++) {
            count += Math.min(n, x / row);
        }
        return count;
    }

    // Level 3 -- Hardened: works unchanged when m == 1 or n == 1 (the
    // table degenerates to a single row or column), since the row
    // loop and the min(n, x/row) formula still apply correctly.

    public static void main(String[] args) {
        System.out.println(findKthNumber(3, 3, 5));
        // 3
    }
}
```

**How to run:** `java KthSmallestNumberInMultiplicationTable.java`

## 6. Walkthrough

Trace `findKthNumber(3, 3, 5)`, `lo=1, hi=9`:

| lo | hi | mid | countLessOrEqual(mid) | >= 5? | action |
|---|---|---|---|---|---|
| 1 | 9 | 5 | row1:3+row2:2+row3:1=6 | yes | hi = 5 |
| 1 | 5 | 3 | row1:3+row2:1+row3:1=5 | yes | hi = 3 |
| 1 | 3 | 2 | row1:2+row2:1+row3:0=3 | no | lo = 3 |
| 3 | 3 | — | — | loop ends | return 3 |

The result `3` matches the expected 5th smallest value from the manually sorted list `1,1,2,2,3,3,4,6,9`. Time complexity is O(m · log(m·n)), since each count computation is O(m) and the search runs O(log(m·n)) times. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: it is tempting to also loop over columns inside `countLessOrEqual`, but that is unnecessary — for a fixed row `r`, the count of columns `c` (from `1` to `n`) where `r * c <= x` has the closed form `min(n, x / r)`, computed in O(1) per row instead of O(n) per row.

- This problem generalizes the "count of values `<= x`" trick to a 2D structure, where the count itself needs its own small derivation (here, a per-row division) rather than a direct array lookup.
- The answer is guaranteed to be an actual table value (some `row * col`), because `countLessOrEqual` only changes at achievable products, so the binary search never lands on a "gap" value that doesn't really appear in the table.
- Related problems: Median of Two Sorted Arrays (another binary search over an implicit structure rather than a raw array), Successful Pairs of Spells and Potions (a related "count how many satisfy a product threshold" idea, per query).
