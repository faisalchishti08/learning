---
card: leetcode-patterns
gi: 352
slug: climbing-stairs
title: Climbing Stairs
---

## 1. What it is

Given an integer `n` representing the total number of stairs, return the number of DISTINCT ways to climb to the top, where each step you take is either 1 or 2 stairs. Example: `n = 3` → `3` (`1+1+1`, `1+2`, `2+1`).

## 2. Why & when

This is the canonical Fibonacci/Linear DP problem: the number of ways to reach stair `i` is the sum of the ways to reach stair `i-1` (then take one more step of size 1) and stair `i-2` (then take one more step of size 2). Use this shape whenever a problem counts paths through a sequence where each move advances by a small, fixed set of step sizes.

## 3. Core concept

**Key idea:** build `dp[i]` = number of ways to reach stair `i`, for every `i` from `0` to `n`, using the two immediately preceding values.

**Steps:**
1. Base cases: `dp[0] = 1` (one way to be at the ground: take no steps), `dp[1] = 1` (one way to reach stair 1: a single 1-step).
2. For `i` from `2` to `n`: `dp[i] = dp[i-1] + dp[i-2]`.
3. Return `dp[n]`.

**Why it is correct:** the LAST step taken to reach stair `i` is either a 1-step (coming from stair `i-1`) or a 2-step (coming from stair `i-2`) — there is no other option. Every way to reach `i` falls into exactly one of these two cases, so summing the ways to reach `i-1` and `i-2` counts every path to `i` exactly once.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array for n=3 built from dp of 1 and dp of 2 summing to dp of 3">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">dp[0]=1, dp[1]=1</text>
    <text x="10" y="45">dp[2] = dp[1]+dp[0] = 1+1 = 2</text>
    <text x="10" y="65">dp[3] = dp[2]+dp[1] = 2+1 = 3</text>
    <rect x="10" y="85" width="200" height="24" fill="#3fb950"/><text x="110" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[3] = 3 ways</text>
  </g>
</svg>

Every stair's count is the sum of the two stairs directly behind it.

## 5. Runnable example

```java
// ClimbingStairs.java
public class ClimbingStairs {

    // KEY INSIGHT: the last step to reach stair i is either a 1-step
    // (from i-1) or a 2-step (from i-2) -- sum the ways from both.

    static int climbStairs(int n) {
        if (n <= 2) return n;
        int prev2 = 1, prev1 = 2;
        for (int i = 3; i <= n; i++) {
            int curr = prev1 + prev2;
            prev2 = prev1;
            prev1 = curr;
        }
        return prev1;
    }

    public static void main(String[] args) {
        System.out.println(climbStairs(3));
        // 3
        System.out.println(climbStairs(5));
        // 8
    }
}
```

**How to run:** `java ClimbingStairs.java`

## 6. Walkthrough

Trace `climbStairs(5)`:

| i | prev2 | prev1 | curr |
|---|---|---|---|
| start | 1 | 2 | - |
| 3 | 2 | 3 | 3 |
| 4 | 3 | 5 | 5 |
| 5 | 5 | 8 | 8 |

Final `prev1 = 8`, matching the expected `8` ways for `n=5`. Time complexity is O(n). Space is O(1) with rolling variables.

## 7. Gotchas & takeaways

> Gotcha: the answer for `climbStairs(n)` is literally the `(n+1)`-th Fibonacci number, but treating it as a MATH TRIVIA fact instead of deriving it from the "last step is 1 or 2" reasoning makes it easy to get the base cases or offset wrong — always derive the recurrence from the problem's own rule.

- `dp[i] = dp[i-1] + dp[i-2]`, with base cases `dp[0]=1, dp[1]=1`: the exact Fibonacci/Linear template, applied to counting paths.
- Rolling variables reduce this from O(n) space to O(1), since only the last two counts ever matter.
- Related problems: Fibonacci Number (the same recurrence shape, applied directly instead of derived from a step-counting story), Min Cost Climbing Stairs (adds a cost to minimize, turning the `+` combine into a `min` combine).
