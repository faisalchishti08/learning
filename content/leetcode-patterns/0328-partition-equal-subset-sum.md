---
card: leetcode-patterns
gi: 328
slug: partition-equal-subset-sum
title: Partition Equal Subset Sum
---

## 1. What it is

Given an integer array `nums`, return `true` if it can be split into two subsets with EQUAL sums, using every element exactly once. Example: `nums = [1,5,11,5]` → `true` (`[1,5,5]` and `[11]`, both summing to `11`).

## 2. Why & when

This is 0/1 knapsack in disguise: if the total sum is `S`, each subset must sum to `S/2`, so the question becomes "can some subset of `nums` sum to EXACTLY `S/2`?" — a REACHABILITY variant of knapsack, where each number's "weight" and "value" are the same, and capacity is the target `S/2`. Use this shape whenever a problem asks whether a target sum is reachable using a subset of given numbers, each usable once.

## 3. Core concept

**Key idea:** compute `total = sum(nums)`. If `total` is odd, no equal partition is possible — return `false` immediately. Otherwise, the question reduces to: "is `target = total / 2` reachable as the sum of some subset of `nums`?"

**Steps:**
1. If `total % 2 != 0`, return `false` (prune before any DP work).
2. Compute `target = total / 2`. Create `dp[target + 1]`, a boolean array, with `dp[0] = true` (a sum of `0` is always reachable, by taking no elements).
3. For each number `num` in `nums`, loop `w` from `target` DOWN TO `num`: `dp[w] = dp[w] || dp[w - num]` (this number either contributes to reaching `w`, or it does not — `dp[w]` stays true if it was already reachable, or becomes true if `w - num` was reachable before this number was considered).
4. Return `dp[target]`.

**Why it is correct:** this is exactly the 0/1 knapsack reachability template — each number is used at most once (enforced by the descending loop), and `dp[w]` becomes `true` the moment ANY combination of already-considered numbers sums to exactly `w`. If `dp[target]` ends up `true`, that subset (summing to `target = total/2`) and its complement (summing to `total - target = total/2` too) form a valid equal-sum partition.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reachability array showing which sums become true as each number from 1,5,11,5 is processed, targeting sum 11">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [1,5,11,5], total=22, target=11</text>
    <text x="10" y="45">after processing 1: dp[0]=T, dp[1]=T</text>
    <text x="10" y="65">after processing 5: dp[5]=T, dp[6]=T (1+5)</text>
    <text x="10" y="85">after processing 11: dp[11]=T (11 alone)</text>
    <rect x="10" y="100" width="150" height="24" fill="#3fb950"/><text x="85" y="117" fill="#0d1117" text-anchor="middle" font-size="10">dp[11] = true -&gt; true</text>
  </g>
</svg>

Each number either extends the set of reachable sums or leaves it unchanged; the search stops early conceptually once the target becomes reachable.

## 5. Runnable example

```java
// PartitionEqualSubsetSum.java
public class PartitionEqualSubsetSum {

    // KEY INSIGHT: "split into two equal-sum subsets" reduces to "is
    // total/2 reachable as a subset sum" -- a 0/1 knapsack
    // reachability problem, where weight and value are the same
    // number.

    static boolean canPartition(int[] nums) {
        int total = 0;
        for (int num : nums) total += num;
        if (total % 2 != 0) return false;

        int target = total / 2;
        boolean[] dp = new boolean[target + 1];
        dp[0] = true;

        for (int num : nums) {
            for (int w = target; w >= num; w--) {
                dp[w] = dp[w] || dp[w - num];
            }
        }
        return dp[target];
    }

    public static void main(String[] args) {
        System.out.println(canPartition(new int[]{1, 5, 11, 5}));
        // true
        System.out.println(canPartition(new int[]{1, 2, 3, 5}));
        // false
    }
}
```

**How to run:** `java PartitionEqualSubsetSum.java`

## 6. Walkthrough

Trace `canPartition([1,5,11,5])`, `total = 22`, `target = 11`:

| number | dp values that become true (descending update) |
|---|---|
| 1 | dp[1] = dp[0] = true |
| 5 | dp[6] = dp[1] = true; dp[5] = dp[0] = true |
| 11 | dp[11] = dp[0] = true |
| 5 (second) | dp[11] already true; other slots may also update, but target is already reached |

`dp[11] = true` after processing the number `11`. Time complexity is O(n · target), where `target = total/2`. Space is O(target), for the 1D boolean array.

## 7. Gotchas & takeaways

> Gotcha: checking `total % 2 != 0` BEFORE running the DP is not just an optimization — it is a correctness requirement, since an odd total can never be split into two EQUAL integer sums, and skipping this check would waste time running a DP that could never succeed.

- "Value equals weight" is the specific twist that turns generic 0/1 knapsack into a SUBSET-SUM reachability problem — recognize this pattern whenever a problem's only quantity is a sum, with no separate value to maximize.
- The descending loop order is exactly the 0/1 knapsack discipline from the template page, ensuring each number is used at most once.
- Related problems: Target Sum (a related subset-sum problem, but counting the number of ways rather than checking reachability), Last Stone Weight II (uses the SAME "reach total/2" idea, but to MINIMIZE a final difference rather than to check exact reachability).
