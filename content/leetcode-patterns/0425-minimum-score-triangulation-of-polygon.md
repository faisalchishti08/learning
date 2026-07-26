---
card: leetcode-patterns
gi: 425
slug: minimum-score-triangulation-of-polygon
title: Minimum Score Triangulation of Polygon
---

## 1. What it is

Given the values of a convex polygon's vertices (in order around the polygon), split it into triangles using non-crossing diagonals. The score of one triangle is the product of its three vertex values; the score of the whole triangulation is the SUM of every triangle's score. Return the MINIMUM possible total score. Example: `values = [1, 2, 3]` → `6` (the only triangle: `1 * 2 * 3`).

## 2. Why & when

Use this shape whenever a problem asks you to triangulate a polygon (or, more generally, fully split a range using nested boundary-based pieces) to minimize or maximize a total score, where each piece's score depends only on its THREE boundary vertices. This is a direct application of interval DP: a range of consecutive polygon vertices, split at a third vertex.

## 3. Core concept

**Key idea:** build `dp[i][j]` = the minimum triangulation score for the polygon FAN formed by vertices `i` through `j` (as if `i` and `j` were connected by a single edge, closing off a smaller polygon).

**Steps:**
1. Base case: `dp[i][i+1] = 0` (two adjacent vertices form only an EDGE, not a triangle — no score yet).
2. For each range `[i, j]` with `j - i >= 2`, try every vertex `k` strictly between `i` and `j` as the THIRD point of a triangle with `i` and `j`: `dp[i][j] = min over k of (dp[i][k] + dp[k][j] + values[i] * values[k] * values[j])`.
3. The answer is `dp[0][n-1]`.

**Why it is correct:** any full triangulation of the range `[i, j]` must include EXACTLY ONE triangle that uses the edge `(i, j)` as one of its sides — call its third vertex `k`. That triangle splits the rest of the polygon into two independent smaller pieces, `[i, k]` and `[k, j]`, each triangulated optimally on its own. Trying every possible `k` and taking the minimum finds the true best triangulation.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="polygon range i to j split by choosing vertex k which forms one triangle and leaves two smaller polygon ranges">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">edge (i, j) is always part of exactly one triangle -- try every third vertex k</text>
    <circle cx="80" cy="100" r="4" fill="#e6edf3"/><text x="70" y="120" font-size="10">i</text>
    <circle cx="200" cy="50" r="4" fill="#3fb950"/><text x="200" y="40" font-size="10">k</text>
    <circle cx="320" cy="100" r="4" fill="#e6edf3"/><text x="320" y="120" font-size="10">j</text>
    <line x1="80" y1="100" x2="200" y2="50" stroke="#8b949e"/>
    <line x1="200" y1="50" x2="320" y2="100" stroke="#8b949e"/>
    <line x1="80" y1="100" x2="320" y2="100" stroke="#f0883e" stroke-width="2"/>
    <text x="10" y="145">score(i,k,j) + dp[i][k] (left piece) + dp[k][j] (right piece)</text>
  </g>
</svg>

Every triangulation of a range has exactly one triangle sitting on its outer edge, splitting the rest into two smaller pieces.

## 5. Runnable example

```java
// MinimumScoreTriangulationOfPolygon.java
public class MinimumScoreTriangulationOfPolygon {

    // KEY INSIGHT: the edge (i, j) belongs to exactly one triangle in
    // any triangulation -- try every third vertex k and recurse on the
    // two independent pieces it creates.

    static int minScoreTriangulation(int[] values) {
        int n = values.length;
        int[][] dp = new int[n][n];

        for (int len = 2; len < n; len++) {
            for (int i = 0; i + len < n; i++) {
                int j = i + len;
                int best = Integer.MAX_VALUE;
                for (int k = i + 1; k < j; k++) {
                    best = Math.min(best, dp[i][k] + dp[k][j] + values[i] * values[k] * values[j]);
                }
                dp[i][j] = best;
            }
        }
        return dp[0][n - 1];
    }

    public static void main(String[] args) {
        System.out.println(minScoreTriangulation(new int[]{1, 2, 3}));
        // 6
        System.out.println(minScoreTriangulation(new int[]{3, 7, 4, 5}));
        // 144
    }
}
```

**How to run:** `java MinimumScoreTriangulationOfPolygon.java`

## 6. Walkthrough

Trace `dp` for `values = [3, 7, 4, 5]`:

| range | best k | score |
|---|---|---|
| [0,1],[1,2],[2,3] | (edges, no triangle) | 0, 0, 0 |
| [0,2] | k=1 | dp[0][1]+dp[1][2]+3*7*4 = 84 |
| [1,3] | k=2 | dp[1][2]+dp[2][3]+7*4*5 = 140 |
| [0,3] | k=1: 0+140+(3*7*5)=245; k=2: 84+0+(3*4*5)=84+60=144 | min = 144 |

`dp[0][3] = 144`, matching the expected answer, achieved by choosing `k=2` at the top level. Time complexity is O(n^3). Space is O(n^2).

## 7. Gotchas & takeaways

> Gotcha: the base case is for ADJACENT vertices (`dp[i][i+1] = 0`, an edge, not a triangle), not for a single vertex — a range needs at least THREE distinct vertices (`j - i >= 2`) before any triangle, and therefore any score, exists.

- `dp[i][j] = min over k of (dp[i][k] + dp[k][j] + values[i]*values[k]*values[j])`: the direct interval-DP template, with the boundary cost being the product of the three vertex values.
- The polygon's vertex ORDER matters — `values[i]`, `values[k]`, `values[j]` must be in their given cyclic order for the triangle to be valid (non-crossing), which the range-based `i < k < j` indexing enforces automatically.
- Related problems: Burst Balloons (a very similar structure, but MAXIMIZING a product-based score, with padded sentinel values at both array ends).
