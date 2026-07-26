---
card: leetcode-patterns
gi: 438
slug: paint-house
title: Paint House
---

## 1. What it is

There are `n` houses in a row, each to be painted one of 3 colors (red, blue, or green), with a different cost per house per color. No two ADJACENT houses may share the same color. Return the MINIMUM total cost to paint all houses. Example: `costs = [[17,2,17],[16,16,5],[14,3,19]]` → `10` (blue, green, blue).

## 2. Why & when

Use this shape whenever a problem assigns one of a SMALL, FIXED set of labels (here, 3 colors) to each position in a sequence, with a rule forbidding the SAME label on adjacent positions. This is state-machine DP outside the stock-trading domain — the "states" are simply the possible colors, and the "transition rule" is just "not the same color as before."

## 3. Core concept

**Key idea:** track three running totals — the minimum cost to paint everything SO FAR, ending the current house in EACH of the 3 colors.

**Steps:**
1. Initialize `red = costs[0][0]`, `blue = costs[0][1]`, `green = costs[0][2]` (the cost of painting house `0` each color).
2. For each subsequent house `i`: the new cost of painting it RED is `costs[i][0] + min(prevBlue, prevGreen)` (any color except red from the house before); similarly for `blue` and `green`, each excluding its OWN previous value.
3. The answer is `min(red, blue, green)` after the last house.

**Why excluding the SAME color from the previous house is enough (no need to track a full color history):** the "no two adjacent houses the same color" rule only ever looks ONE house back — it never restricts a color based on houses further back. So the minimum cost of ending house `i` in color `X` depends only on the minimum cost of ending house `i-1` in any color OTHER than `X`, which is exactly what `min(prevBlue, prevGreen)` (for `X = red`) captures.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="three running totals for red blue and green, each house's color cost built from the other two colors best total from the house before">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">red(i) = costs[i][red] + min(blue(i-1), green(i-1))</text>
    <text x="10" y="45" font-weight="bold">blue(i) = costs[i][blue] + min(red(i-1), green(i-1))</text>
    <text x="10" y="70" font-weight="bold">green(i) = costs[i][green] + min(red(i-1), blue(i-1))</text>
    <rect x="10" y="90" width="330" height="24" fill="#3fb950"/><text x="175" y="107" fill="#0d1117" text-anchor="middle" font-size="10">each color excludes only itself from the house before</text>
  </g>
</svg>

Each color's running total only ever excludes its own value from the house immediately before it.

## 5. Runnable example

```java
// PaintHouse.java
public class PaintHouse {

    // KEY INSIGHT: the "no adjacent match" rule only looks one house
    // back -- each color's new cost only needs to exclude its OWN
    // previous value, not track a full color history.

    static int minCost(int[][] costs) {
        int n = costs.length;
        if (n == 0) return 0;
        int red = costs[0][0], blue = costs[0][1], green = costs[0][2];

        for (int i = 1; i < n; i++) {
            int newRed = costs[i][0] + Math.min(blue, green);
            int newBlue = costs[i][1] + Math.min(red, green);
            int newGreen = costs[i][2] + Math.min(red, blue);
            red = newRed;
            blue = newBlue;
            green = newGreen;
        }
        return Math.min(red, Math.min(blue, green));
    }

    public static void main(String[] args) {
        System.out.println(minCost(new int[][]{{17, 2, 17}, {16, 16, 5}, {14, 3, 19}}));
        // 10
    }
}
```

**How to run:** `java PaintHouse.java`

## 6. Walkthrough

Trace `minCost([[17,2,17],[16,16,5],[14,3,19]])`:

| house | red | blue | green |
|---|---|---|---|
| 0 | 17 | 2 | 17 |
| 1 | 16+min(2,17)=18 | 16+min(17,17)=33 | 5+min(17,2)=7 |
| 2 | 14+min(33,7)=21 | 3+min(18,7)=10 | 19+min(18,33)=37 |

Final `min(21, 10, 37) = 10`, matching the expected answer, achieved by painting house `0` blue (`2`), house `1` green (`5`), house `2` blue (`3`): total `2 + 5 + 3 = 10`. Time complexity is O(n) (3 colors is a constant). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: computing `newRed`, `newBlue`, `newGreen` from the OLD `red`, `blue`, `green` (not from partially-updated new values) is essential — updating `red` in place and then using it while computing `newBlue` would incorrectly let a house's blue cost depend on ITS OWN just-computed red cost, rather than the PREVIOUS house's values.

- Three running totals, each excluding only its OWN previous value: the minimal state-machine DP needed for a "no repeated adjacent label" constraint.
- This generalizes directly to Paint House II, where the fixed count of `3` colors becomes an arbitrary `k`, requiring a smarter way to find "the best OTHER color" than checking just two values.
- Related problems: Paint House II (the same idea, generalized to `k` colors, needing the two smallest previous values instead of three named ones).
