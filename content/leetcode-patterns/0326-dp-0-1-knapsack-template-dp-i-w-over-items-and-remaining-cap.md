---
card: leetcode-patterns
gi: 326
slug: dp-0-1-knapsack-template-dp-i-w-over-items-and-remaining-cap
title: DP: 0/1 Knapsack — template: dp[i][w] over items and remaining capacity
---

## 1. What it is

This page gives the reusable template for 0/1 Knapsack problems: a 2D table `dp[i][w]` filled row by row over items, and column by column over remaining capacity, plus the standard SPACE-OPTIMIZED 1D version.

## 2. Why & when

Use the 2D template when you are first learning the pattern, or when you need to RECONSTRUCT which items were chosen (the full table lets you trace back the decisions). Use the 1D-optimized version once you are comfortable with the pattern and only need the final answer, since it cuts memory from O(n · capacity) to O(capacity).

## 3. Core concept

**Template A — 2D table.**
1. Create `dp[n+1][capacity+1]`, with `dp[0][w] = 0` for all `w` (no items means zero value) and `dp[i][0] = 0` for all `i` (zero capacity means nothing fits).
2. For `i` from `1` to `n`, for `w` from `0` to `capacity`: `dp[i][w] = dp[i-1][w]` (skip); if `weights[i-1] <= w`, also consider `dp[i-1][w - weights[i-1]] + values[i-1]` (take), and keep the better of the two.
3. The answer is `dp[n][capacity]`.

**Template B — 1D space-optimized.**
1. Create `dp[capacity+1]`, all zeros.
2. For each item, loop `w` from `capacity` DOWN TO the item's weight (descending order is essential): `dp[w] = max(dp[w], dp[w - weight] + value)`.
3. The answer is `dp[capacity]`.

**Why the 1D version needs a DESCENDING loop:** `dp[w - weight]` must still refer to the value from BEFORE the current item was considered (equivalent to row `i-1` in the 2D version). Looping `w` upward would let an early update at a smaller `w` get read again later in the SAME item's pass, effectively allowing that item to be used twice — descending order guarantees every `dp[w - weight]` read happens before that slot is overwritten for the current item.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="1D array update looping capacity from high to low, showing why descending order prevents reusing the same item twice">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">item weight=3, value=5; dp array before this item: [0,0,0,4,4,4,4]</text>
    <text x="10" y="45">descending w=6: dp[6]=max(dp[6], dp[3]+5)=max(4,4+5)=9</text>
    <text x="10" y="65">descending w=5: dp[5]=max(dp[5], dp[2]+5)=max(4,0+5)=5</text>
    <text x="10" y="85">descending w=3: dp[3]=max(dp[3], dp[0]+5)=max(4,0+5)=5</text>
    <rect x="10" y="100" width="260" height="24" fill="#3fb950"/><text x="140" y="117" fill="#0d1117" text-anchor="middle" font-size="10">each dp[w-3] read is the PRE-item value, correctly</text>
  </g>
</svg>

Reading `dp[w - weight]` before it gets overwritten (by processing high `w` first) is what keeps each item used at most once.

## 5. Runnable example

```java
// Knapsack01Template.java
public class Knapsack01Template {

    // Template A: 2D table.
    static int knapsack2D(int[] weights, int[] values, int capacity) {
        int n = weights.length;
        int[][] dp = new int[n + 1][capacity + 1];
        for (int i = 1; i <= n; i++) {
            for (int w = 0; w <= capacity; w++) {
                dp[i][w] = dp[i - 1][w];
                if (weights[i - 1] <= w) {
                    dp[i][w] = Math.max(dp[i][w], dp[i - 1][w - weights[i - 1]] + values[i - 1]);
                }
            }
        }
        return dp[n][capacity];
    }

    // Template B: 1D space-optimized -- descending w loop is required.
    static int knapsack1D(int[] weights, int[] values, int capacity) {
        int[] dp = new int[capacity + 1];
        for (int i = 0; i < weights.length; i++) {
            for (int w = capacity; w >= weights[i]; w--) {
                dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
            }
        }
        return dp[capacity];
    }

    public static void main(String[] args) {
        int[] weights = {1, 3, 4, 5};
        int[] values = {1, 4, 5, 7};
        System.out.println(knapsack2D(weights, values, 7));
        // 9
        System.out.println(knapsack1D(weights, values, 7));
        // 9
    }
}
```

**How to run:** `java Knapsack01Template.java`

## 6. Walkthrough

1. `knapsack2D` fills a `5 x 8` table (`n+1` rows, `capacity+1` columns), row by row, each cell depending only on the row above.
2. `knapsack1D` processes the SAME logical computation using one array of size `8`, overwritten IN PLACE for each item, always scanning from `capacity` down to the item's own weight.
3. Both return `9` for `weights=[1,3,4,5]`, `values=[1,4,5,7]`, `capacity=7` — confirming the space-optimized version computes the identical answer with far less memory.
4. Tracing `knapsack1D`'s array after each item confirms no item's value gets added twice: after the weight-3 item, `dp[3..7]` reflect using it at most once each, since higher indices were updated before lower ones could feed back into them within the same item's pass.
5. This template applies directly to Partition Equal Subset Sum, Target Sum, and every other 0/1 knapsack problem on this card — only the meaning of "weight," "value," and "capacity" changes per problem.

## 7. Gotchas & takeaways

> Gotcha: using an ASCENDING loop in the 1D version (`for w = weight to capacity`) silently converts the problem into UNBOUNDED knapsack (each item reusable any number of times), since `dp[w - weight]` could then reflect an update already made for the CURRENT item, letting it be picked again.

- 2D table: easier to understand and to reconstruct which items were chosen; O(n · capacity) space.
- 1D array: same answer, O(capacity) space; requires the descending-loop discipline to preserve the "each item once" guarantee.
- The transition itself (`skip` vs `take`, keep the better) is identical between both templates — only the indexing and loop direction differ.
