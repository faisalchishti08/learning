---
card: leetcode-patterns
gi: 426
slug: burst-balloons
title: Burst Balloons
---

## 1. What it is

Given `n` balloons in a row, each with a number on it, bursting a balloon at index `i` earns `nums[left] * nums[i] * nums[right]` coins, where `left` and `right` are the CURRENTLY ADJACENT balloons (after earlier bursts have removed others). Burst all the balloons to MAXIMIZE total coins. Example: `nums = [3, 1, 5, 8]` → `167`.

## 2. Why & when

Use this shape whenever bursting (removing) an item's reward depends on its CURRENT neighbors, which change as other items are removed — the "neighbors shift" nature makes a forward simulation intractable to reason about directly. The key trick: think about which balloon is burst LAST within a range, not first — that reframes the problem into a clean interval-DP split.

## 3. Core concept

**Key idea:** pad the array with a virtual `1` at both ends (so edge balloons have "neighbors" too). Build `dp[left][right]` = the maximum coins obtainable from bursting every balloon STRICTLY BETWEEN `left` and `right`, treating `left` and `right` themselves as never-burst boundary markers.

**Steps:**
1. Create `a = [1, nums[0], nums[1], ..., nums[n-1], 1]` (length `n+2`).
2. For every range `[left, right]` (processed by increasing length), try every `k` strictly between `left` and `right` as the LAST balloon burst in that range: `dp[left][right] = max over k of (dp[left][k] + dp[k][right] + a[left] * a[k] * a[right])`.
3. The answer is `dp[0][n+1]` (the range spanning both sentinel `1`s).

**Why choosing the LAST balloon burst (not the first) makes this work:** if balloon `k` is the LAST one burst inside `[left, right]`, then at the MOMENT it bursts, its only remaining neighbors are exactly `a[left]` and `a[right]` — everything else between them is already gone. This means bursting `k` last earns `a[left] * a[k] * a[right]`, a value that does NOT depend on what order the OTHER balloons in `[left, k]` and `[k, right]` were burst in — so those two sub-ranges can be solved completely independently, exactly like any other interval-DP split.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="balloon k chosen as the last one burst inside the range, so its neighbors at the moment of bursting are the range boundaries themselves">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">choose k as the LAST balloon burst in (left, right)</text>
    <text x="10" y="45">everything else in (left, k) and (k, right) is already gone by then</text>
    <rect x="60" y="60" width="60" height="26" fill="#30363d" stroke="#8b949e"/><text x="90" y="78" text-anchor="middle" font-size="10">left</text>
    <rect x="200" y="60" width="60" height="26" fill="#3fb950"/><text x="230" y="78" text-anchor="middle" font-size="10" fill="#0d1117">k</text>
    <rect x="340" y="60" width="60" height="26" fill="#30363d" stroke="#8b949e"/><text x="370" y="78" text-anchor="middle" font-size="10">right</text>
    <rect x="10" y="100" width="330" height="24" fill="#3fb950"/><text x="170" y="117" fill="#0d1117" text-anchor="middle" font-size="10">k's neighbors at burst time are exactly left and right -- a clean split</text>
  </g>
</svg>

Choosing k as the last balloon burst freezes its neighbors as the range's own boundaries, cleanly splitting the problem in two.

## 5. Runnable example

```java
// BurstBalloons.java
public class BurstBalloons {

    // KEY INSIGHT: pick k as the LAST balloon burst in the range, not
    // the first -- its neighbors at that moment are fixed (left and
    // right), letting the two sub-ranges be solved independently.

    static int maxCoins(int[] nums) {
        int n = nums.length;
        int[] a = new int[n + 2];
        a[0] = 1;
        a[n + 1] = 1;
        for (int i = 0; i < n; i++) a[i + 1] = nums[i];

        int[][] dp = new int[n + 2][n + 2];
        for (int len = 2; len <= n + 1; len++) {
            for (int left = 0; left + len <= n + 1; left++) {
                int right = left + len;
                int best = 0;
                for (int k = left + 1; k < right; k++) {
                    best = Math.max(best, dp[left][k] + dp[k][right] + a[left] * a[k] * a[right]);
                }
                dp[left][right] = best;
            }
        }
        return dp[0][n + 1];
    }

    public static void main(String[] args) {
        System.out.println(maxCoins(new int[]{3, 1, 5, 8}));
        // 167
        System.out.println(maxCoins(new int[]{1, 5}));
        // 10
    }
}
```

**How to run:** `java BurstBalloons.java`

## 6. Walkthrough

Trace the optimal order for `nums = [3, 1, 5, 8]` (padded `a = [1, 3, 1, 5, 8, 1]`):

| step | balloon burst | neighbors at burst time | coins earned |
|---|---|---|---|
| 1 | value 1 (index 2 in `a`) | 3, 5 | 3*1*5 = 15 |
| 2 | value 5 (index 3 in `a`) | 3, 8 | 3*5*8 = 120 |
| 3 | value 3 (index 1 in `a`) | 1, 8 | 1*3*8 = 24 |
| 4 | value 8 (index 4 in `a`) | 1, 1 | 1*8*1 = 8 |

Total `= 15 + 120 + 24 + 8 = 167`, matching the expected answer and the DP's computed `dp[0][5]`. Time complexity is O(n^3). Space is O(n^2).

## 7. Gotchas & takeaways

> Gotcha: choosing `k` as the FIRST balloon burst (instead of the LAST) breaks the independence needed for interval DP — after bursting `k` first, its former neighbors become adjacent to EACH OTHER, so the two "halves" are no longer separate sub-problems; only the "last burst" framing keeps them independent.

- Padding with sentinel `1`s at both ends lets edge balloons be treated uniformly, without special-casing "no neighbor on this side."
- `dp[left][right] = max over k of (dp[left][k] + dp[k][right] + a[left]*a[k]*a[right])`: identical shape to Minimum Score Triangulation, but MAXIMIZING and reasoning about "last action" rather than a fixed geometric structure.
- Related problems: Minimum Score Triangulation of Polygon (the same split-by-boundary idea, applied to a fixed geometric shape instead of a bursting order), Minimum Cost to Merge Stones (also splits a range, but the split points are constrained by a group-size parameter `K`).
