---
card: leetcode-patterns
gi: 330
slug: last-stone-weight-ii
title: Last Stone Weight II
---

## 1. What it is

Given an array `stones` of stone weights, repeatedly choose any two stones and smash them together: if their weights are equal, both are destroyed; otherwise, the lighter is destroyed and the heavier becomes `heavy - light`. Return the SMALLEST possible weight of the last remaining stone (or `0` if none remain). Example: `stones = [2,7,4,1,8,1]` → `1`.

## 2. Why & when

The smashing process is equivalent to splitting `stones` into two groups and computing the ABSOLUTE DIFFERENCE of their sums: whatever order you smash in, the final remaining weight always equals `|sum(groupA) - sum(groupB)|` for SOME partition into two groups. Minimizing this difference is a 0/1 knapsack problem: find the subset whose sum is as CLOSE AS POSSIBLE to `total / 2`. Use this shape whenever a problem's real question, after some reasoning, becomes "minimize the difference between two subset sums."

## 3. Core concept

**Key idea:** find the largest achievable subset sum that does not exceed `total / 2`. That subset (call its sum `s1`) pairs with the rest (summing to `total - s1`), and the final answer is `total - 2 * s1` — the smaller this gap, the closer the two groups are to equal.

**Steps:**
1. Compute `total = sum(stones)`, `half = total / 2` (integer division).
2. Create `dp[half + 1]`, a boolean array, `dp[0] = true`.
3. For each stone weight `w` in `stones`, loop `cap` from `half` DOWN TO `w`: `dp[cap] = dp[cap] || dp[cap - w]` (standard 0/1 knapsack reachability).
4. Find the LARGEST `cap` such that `dp[cap]` is `true` — call it `s1`.
5. Return `total - 2 * s1`.

**Why it is correct:** any sequence of smashes is equivalent to partitioning the stones into two groups (the ones that end up "canceling out" versus the ones that survive as the final weight), and the final remaining weight is always `|sum(A) - sum(B)|` for that partition — a well-known invariant of this smashing process. Since `sum(A) + sum(B) = total`, minimizing `|sum(A) - sum(B)| = |total - 2*sum(A)|` is minimized by making `sum(A)` as close as possible to `total/2`, which is exactly what scanning for the LARGEST reachable subset sum not exceeding `total/2` finds.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Finding the largest reachable subset sum not exceeding half the total, for stones 2 7 4 1 8 1, and computing the final difference">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">stones = [2,7,4,1,8,1], total = 23, half = 11</text>
    <text x="10" y="45">many subset sums up to 11 are reachable, including 11 itself</text>
    <text x="10" y="65">largest reachable s1 &lt;= 11 is 11 (e.g. 7+4=11, or 2+1+8=11)</text>
    <rect x="10" y="80" width="220" height="24" fill="#3fb950"/><text x="120" y="97" fill="#0d1117" text-anchor="middle" font-size="10">answer = 23 - 2*11 = 1</text>
  </g>
</svg>

The two groups end up as close to equal as possible, minimizing the final leftover weight.

## 5. Runnable example

```java
// LastStoneWeightII.java
public class LastStoneWeightII {

    // KEY INSIGHT: the smashing process always reduces to "partition
    // into two groups, final weight = |sum(A) - sum(B)|" -- minimize
    // this by finding the largest reachable subset sum up to
    // total/2, a 0/1 knapsack reachability problem.

    static int lastStoneWeightII(int[] stones) {
        int total = 0;
        for (int stone : stones) total += stone;

        int half = total / 2;
        boolean[] dp = new boolean[half + 1];
        dp[0] = true;

        for (int stone : stones) {
            for (int cap = half; cap >= stone; cap--) {
                dp[cap] = dp[cap] || dp[cap - stone];
            }
        }

        int s1 = half;
        while (!dp[s1]) s1--;

        return total - 2 * s1;
    }

    public static void main(String[] args) {
        System.out.println(lastStoneWeightII(new int[]{2, 7, 4, 1, 8, 1}));
        // 1
        System.out.println(lastStoneWeightII(new int[]{31, 26, 33, 21, 40}));
        // 5
    }
}
```

**How to run:** `java LastStoneWeightII.java`

## 6. Walkthrough

Trace `lastStoneWeightII([2,7,4,1,8,1])`: `total = 23`, `half = 11`.

| step | value |
|---|---|
| dp array after all stones processed | true at reachable sums including 0,1,2,3,4,5,6,7,8,9,10,11 (many combinations) |
| largest s1 with dp[s1]=true, s1&lt;=11 | 11 (e.g. stones 7+4=11, or 2+1+8=11) |
| answer | 23 - 2*11 = 1 |

Final result: `1`, matching the expected smallest possible final stone weight. Time complexity is O(n · total), where `total` is the sum of all stone weights. Space is O(total), for the 1D boolean array.

## 7. Gotchas & takeaways

> Gotcha: the loop that finds `s1` (`while (!dp[s1]) s1--`) assumes `dp[0]` is always `true`, which guarantees the loop terminates — without this base case, searching downward from `half` could run past index `0` if no other sum were reachable, though `dp[0] = true` always holds by definition (the empty subset).

- This problem's real insight is entirely in the REFRAMING (smashing → partition into two closest-sum groups) — once you see it, the DP itself is identical to Partition Equal Subset Sum's reachability array.
- `total - 2 * s1` is the general formula for "minimize `|total - 2*subsetSum|`" whenever `s1` is the largest reachable subset sum not exceeding `total/2`.
- Related problems: Partition Equal Subset Sum (checks if the difference can be EXACTLY 0), Tallest Billboard (a related but harder difference-minimization problem, needing a 2D state to track the running difference itself).
