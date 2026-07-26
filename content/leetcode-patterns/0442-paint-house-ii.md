---
card: leetcode-patterns
gi: 442
slug: paint-house-ii
title: Paint House II
---

## 1. What it is

Same setup as Paint House, but now there are `k` colors instead of exactly `3`. Return the minimum total cost to paint all houses so that no two adjacent houses share a color. Example: `costs = [[1,5,3],[2,9,4]]` → `5` (color `0` house `0` with color `0` (cost `1`), house `1` with color `2` (cost `4`): total `5`).

## 2. Why & when

Use this shape whenever Paint House's "no adjacent match" idea needs to generalize to an ARBITRARY number of colors `k`, not just a fixed `3`. Naively adapting Paint House's approach (for each color, take the min of all `k-1` OTHER colors) costs O(n * k^2) — for large `k`, tracking only the SMALLEST and SECOND-SMALLEST previous costs (across all colors) reduces this to O(n * k).

## 3. Core concept

**Key idea:** instead of tracking one running value per color, track just TWO numbers after each house: `min1` (the smallest total cost among all colors so far) and `min2` (the second-smallest), along with WHICH color achieved `min1`.

**Steps:**
1. For house `0`, `min1`/`min2`/`min1Color` come directly from its costs.
2. For each subsequent house, for EVERY color `c`: its new cost is `costs[i][c] + (min1 if c != min1Color else min2)` — use the overall best previous cost, UNLESS this color IS the one that achieved it, in which case fall back to the second-best.
3. After computing every color's new cost for this house, find the new `min1`, `min2`, and `min1Color` among them.
4. The answer is `min1` after the last house.

**Why tracking only the top two previous values (instead of all `k`) is enough:** for any color `c`, the best compatible previous total is either the OVERALL minimum (if `c` did not achieve it) or the SECOND overall minimum (if `c` did achieve it, since `c` cannot follow itself). No color ever needs to know about the third-smallest value or beyond — only whether IT was the specific color that held the top spot.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each color choosing the overall smallest previous total unless it was the color that achieved it in which case it falls back to the second smallest">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">color c's best previous total = min1, UNLESS c achieved min1 -- then min2</text>
    <rect x="10" y="40" width="330" height="24" fill="#3fb950"/><text x="175" y="57" fill="#0d1117" text-anchor="middle" font-size="10">only 2 numbers tracked, not one per color -- O(n*k), not O(n*k^2)</text>
  </g>
</svg>

Tracking only the best and second-best previous totals (and which color achieved the best) is enough for every color's decision.

## 5. Runnable example

```java
// PaintHouseII.java
public class PaintHouseII {

    // KEY INSIGHT: every color only ever needs the overall smallest
    // previous total, or the second-smallest if IT was the color that
    // achieved the smallest -- no need to track all k colors' values.

    static int minCostII(int[][] costs) {
        int n = costs.length;
        if (n == 0) return 0;
        int k = costs[0].length;
        int prevMin1 = 0, prevMin2 = 0, prevMin1Color = -1;

        for (int i = 0; i < n; i++) {
            int curMin1 = Integer.MAX_VALUE, curMin2 = Integer.MAX_VALUE, curMin1Color = -1;
            for (int c = 0; c < k; c++) {
                int cost = costs[i][c] + (c == prevMin1Color ? prevMin2 : prevMin1);
                if (cost < curMin1) {
                    curMin2 = curMin1;
                    curMin1 = cost;
                    curMin1Color = c;
                } else if (cost < curMin2) {
                    curMin2 = cost;
                }
            }
            prevMin1 = curMin1;
            prevMin2 = curMin2;
            prevMin1Color = curMin1Color;
        }
        return prevMin1;
    }

    public static void main(String[] args) {
        System.out.println(minCostII(new int[][]{{1, 5, 3}, {2, 9, 4}}));
        // 5
    }
}
```

**How to run:** `java PaintHouseII.java`

## 6. Walkthrough

Trace `minCostII([[1,5,3],[2,9,4]])`:

| house | color 0 cost | color 1 cost | color 2 cost | min1 (color) | min2 |
|---|---|---|---|---|---|
| 0 | 1 | 5 | 3 | 1 (color 0) | 3 |
| 1 | 2+min2(3)=5 | 9+min1(1)=10 | 4+min1(1)=5 | 5 (color 0, tie broken by first found) | 5 |

Final `min1 = 5`, matching the expected answer: house `0` uses color `0` (cost `1`), house `1` uses color `2` (cost `4`), total `5`. Time complexity is O(n*k). Space is O(1) beyond the input.

## 7. Gotchas & takeaways

> Gotcha: when a color `c` equals `prevMin1Color`, it MUST fall back to `prevMin2`, not `prevMin1` — using `prevMin1` here would silently allow that color to follow ITSELF from the previous house, violating the adjacency rule the whole problem is built around.

- Tracking only `min1`, `min2`, and WHICH color achieved `min1` is the entire optimization over Paint House's "check every other color" approach — it reduces O(k) work per color down to O(1) work per color.
- This is a direct generalization of Paint House: with `k = 3`, this same idea (top-2 tracking) also works, just with more bookkeeping than necessary for such a small, fixed color count.
- Related problems: Paint House (the `k=3` special case, simple enough to name each color's variable directly instead of tracking top-2 values).
