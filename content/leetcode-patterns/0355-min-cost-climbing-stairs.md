---
card: leetcode-patterns
gi: 355
slug: min-cost-climbing-stairs
title: Min Cost Climbing Stairs
---

## 1. What it is

Given an array `cost` where `cost[i]` is the cost to step ON stair `i`, return the MINIMUM total cost to reach the TOP of the staircase (one step past the last index), starting from either stair `0` or stair `1`, moving 1 or 2 stairs at a time. Example: `cost = [10,15,20]` → `15` (start at stair 1, pay `15`, then step 2 stairs to the top).

## 2. Why & when

This is Climbing Stairs with a cost attached to each stair, and the combining step changed from COUNTING (`+`) to MINIMIZING (`min`). Use this shape whenever a "move 1 or 2 steps" problem asks for the cheapest (or most valuable) path rather than the number of paths.

## 3. Core concept

**Key idea:** build `dp[i]` = the minimum cost to REACH stair `i` (having already paid for stair `i`, if `i` is a real stair), for every `i` from `0` to `n` (where `n = cost.length` represents the "top," one past the last stair).

**Steps:**
1. Base cases: `dp[0] = 0`, `dp[1] = 0` (you can START at either stair 0 or 1 for free, without needing to have paid to arrive there).
2. For `i` from `2` to `n`: `dp[i] = min(dp[i-1] + cost[i-1], dp[i-2] + cost[i-2])` (arrive at `i` from one step back, paying that stair's cost, or from two steps back, paying that stair's cost).
3. Return `dp[n]`.

**Why it is correct:** to reach position `i`, the LAST move is either a 1-step from `i-1` or a 2-step from `i-2`; in both cases, you must have paid the cost of the stair you JUST LEFT. Taking the minimum over both options at every position guarantees the cheapest path, since any optimal path's second-to-last position is one of these two choices.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array for cost 10,15,20 showing dp of 3 as the minimum of two arrival options">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">cost=[10,15,20]; dp[0]=0, dp[1]=0</text>
    <text x="10" y="45">dp[2] = min(dp[1]+cost[1], dp[0]+cost[0]) = min(15, 10) = 10</text>
    <text x="10" y="65">dp[3] = min(dp[2]+cost[2], dp[1]+cost[1]) = min(30, 15) = 15</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[3] = 15 (top reached via stair 1)</text>
  </g>
</svg>

Each arrival cost is the minimum of two options: one step back plus that stair's price, or two steps back plus that stair's price.

## 5. Runnable example

```java
// MinCostClimbingStairs.java
public class MinCostClimbingStairs {

    // KEY INSIGHT: same "last step is 1 or 2" recurrence as Climbing
    // Stairs, but combining with min(...) + cost instead of counting.

    static int minCostClimbingStairs(int[] cost) {
        int n = cost.length;
        int prev2 = 0, prev1 = 0;
        for (int i = 2; i <= n; i++) {
            int curr = Math.min(prev1 + cost[i - 1], prev2 + cost[i - 2]);
            prev2 = prev1;
            prev1 = curr;
        }
        return prev1;
    }

    public static void main(String[] args) {
        System.out.println(minCostClimbingStairs(new int[]{10, 15, 20}));
        // 15
        System.out.println(minCostClimbingStairs(new int[]{1, 100, 1, 1, 1, 100, 1, 1, 100, 1}));
        // 6
    }
}
```

**How to run:** `java MinCostClimbingStairs.java`

## 6. Walkthrough

Trace `minCostClimbingStairs([10,15,20])`, `n=3`:

| i | prev2 (dp[i-2]) | prev1 (dp[i-1]) | curr |
|---|---|---|---|
| start | 0 | 0 | - |
| 2 | 0 | 10 | min(0+15, 0+10)=10 |
| 3 | 10 | 15 | min(10+20, 0+15)=15 |

Final `prev1 = 15`, matching the expected `15`. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: indexing `cost[i-1]` and `cost[i-2]` (not `cost[i]`) inside the loop is easy to get backwards — `dp[i]` represents having ARRIVED at position `i` without needing to pay for it, so the cost paid belongs to whichever stair you stepped FROM, not the destination.

- `dp[i] = min(dp[i-1] + cost[i-1], dp[i-2] + cost[i-2])`, base cases `dp[0]=dp[1]=0`: the minimize variant of the Fibonacci/Linear template.
- The "top" is position `n = cost.length`, one PAST the last real stair — it costs nothing to stand there, only to arrive.
- Related problems: Climbing Stairs (identical recurrence shape, counting paths instead of minimizing cost), House Robber (also a `max`/`min` combine over 1-or-2-back positions, but with a "skip or take" framing instead of "1 or 2 steps").
