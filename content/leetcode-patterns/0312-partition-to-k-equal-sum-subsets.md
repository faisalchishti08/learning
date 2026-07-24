---
card: leetcode-patterns
gi: 312
slug: partition-to-k-equal-sum-subsets
title: Partition to K Equal Sum Subsets
---

## 1. What it is

Given an integer array `nums` and an integer `k`, return `true` if `nums` can be split into `k` non-empty subsets, each with an EQUAL sum, using every element exactly once. Example: `nums = [4,3,2,3,5,2,1]`, `k = 4` → `true` (subsets `[5]`, `[1,4]`, `[2,3]`, `[2,3]`, each summing to `5`).

## 2. Why & when

This is Matchsticks to Square generalized: instead of exactly 4 equal-sum groups, there are `k` of them. It uses the identical backtracking structure — assign each number to a group, prune on overflow, skip redundant empty-group attempts — with `k` groups instead of a fixed 4. Use this shape whenever a problem partitions a set into a VARIABLE number of equal-sum (or otherwise equal-constrained) groups.

## 3. Core concept

**Key idea:** the target sum per group is `sum(nums) / k` (must divide evenly). Sort `nums` descending, then try placing each number into one of `k` running group totals, backtracking on overflow.

**Steps:**
1. Compute `total = sum(nums)`. If `total % k != 0`, return `false` immediately.
2. Compute `target = total / k`. If any single number in `nums` exceeds `target`, return `false` (it could never fit any group).
3. Sort `nums` descending (fail bad branches faster).
4. Track `groups[k]`, all starting at `0`. Define `backtrack(index)`. **Base case:** if `index == nums.length`, every element was placed — return `true` (every group is guaranteed to equal `target`, since the total divides evenly and no group ever exceeded it).
5. **Loop:** for each of the `k` groups: if `groups[i] + nums[index] > target`, skip (prune). Otherwise, add `nums[index]` to `groups[i]` (choose), recurse to `index + 1`, then subtract it back out (un-choose). If `groups[i]` was `0` before this attempt and it failed, `break` out of the loop (skip other equally-empty groups).

**Why it is correct:** the same reasoning as Matchsticks to Square applies, generalized to `k` groups: any partial state where a group exceeds `target` can never be completed correctly, so pruning it is safe; and once every element is placed without any group exceeding `target`, the fixed total and equal division GUARANTEE every group hit exactly `target`. Rejecting any single number larger than `target` upfront is an additional prune unique to this general `k` version, since Matchsticks to Square implicitly handles it the same way but the check is worth stating explicitly for clarity.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Assigning numbers 5,4,3,3,2,2,1 sorted descending to 4 groups each targeting sum 5">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums=[4,3,2,3,5,2,1], k=4, sum=20, target=5</text>
    <text x="10" y="45">sorted desc: [5,4,3,3,2,2,1]</text>
    <text x="10" y="65">place 5 -&gt; group0=5 (done)</text>
    <text x="10" y="85">place 4 -&gt; group1=4; place 3 -&gt; group1 overflow(7&gt;5), try group2=3</text>
    <text x="10" y="105">continue placing 3,2,2,1 into groups 2,3,1 -&gt; final groups = [5,5,5,5]</text>
    <rect x="10" y="120" width="150" height="24" fill="#3fb950"/><text x="85" y="137" fill="#0d1117" text-anchor="middle" font-size="10">result: true</text>
  </g>
</svg>

Each number is tried against the `k` running group totals, backtracking whenever a placement would overflow the shared target.

## 5. Runnable example

```java
// PartitionToKEqualSumSubsets.java
import java.util.*;

public class PartitionToKEqualSumSubsets {

    // KEY INSIGHT: this is Matchsticks to Square generalized from a
    // fixed 4 groups to k groups -- same overflow-prune and
    // skip-duplicate-empty-groups logic, just a variable group count.

    static boolean canPartitionKSubsets(int[] nums, int k) {
        int total = 0;
        for (int num : nums) total += num;
        if (total % k != 0) return false;

        int target = total / k;
        Integer[] sorted = new Integer[nums.length];
        for (int i = 0; i < nums.length; i++) sorted[i] = nums[i];
        Arrays.sort(sorted, Collections.reverseOrder());

        if (sorted[0] > target) return false; // largest element cannot fit any group

        int[] groups = new int[k];
        return backtrack(sorted, 0, groups, target);
    }

    static boolean backtrack(Integer[] nums, int index, int[] groups, int target) {
        if (index == nums.length) return true; // every element placed without overflow

        for (int i = 0; i < groups.length; i++) {
            if (groups[i] + nums[index] > target) continue; // prune: would overflow

            groups[i] += nums[index];                 // choose
            if (backtrack(nums, index + 1, groups, target)) return true; // recurse
            groups[i] -= nums[index];                 // un-choose

            if (groups[i] == 0) break; // prune: skip other equally-empty groups
        }
        return false;
    }

    public static void main(String[] args) {
        System.out.println(canPartitionKSubsets(new int[]{4, 3, 2, 3, 5, 2, 1}, 4));
        // true
        System.out.println(canPartitionKSubsets(new int[]{1, 2, 3, 4}, 3));
        // false
    }
}
```

**How to run:** `java PartitionToKEqualSumSubsets.java`

## 6. Walkthrough

Trace the start of `canPartitionKSubsets([4,3,2,3,5,2,1], 4)`, sorted descending to `[5,4,3,3,2,2,1]`, `target = 5`:

| index | num | tried group | groups before | fits? | groups after |
|---|---|---|---|---|---|
| 0 | 5 | group 0 | [0,0,0,0] | yes | [5,0,0,0] |
| 1 | 4 | group 0 fails (5+4&gt;5), try group 1 | [5,0,0,0] | yes | [5,4,0,0] |
| 2 | 3 | group 1 fails (4+3&gt;5), try group 2 | [5,4,0,0] | yes | [5,4,3,0] |
| 3 | 3 | group 2 fails (3+3&gt;5), try group 3 | [5,4,3,0] | yes | [5,4,3,3] |
| 4 | 2 | group 1 (4+2&gt;5 fails), group 2 (3+2=5 fits) | [5,4,3,3] | yes | [5,4,5,3] |
| 5 | 2 | group 3 (3+2=5 fits) | [5,4,5,3] | yes | [5,4,5,5] |
| 6 | 1 | group 1 (4+1=5 fits) | [5,4,5,5] | yes | [5,5,5,5] |
| 7 (index==length) | — | — | — | all groups = target | return true |

Final result: `true`. Time complexity is O(k^n) in the worst case, but the prunes (overflow check, skip-duplicate-empty-groups, largest-element check) make it fast in practice for typical inputs. Space is O(n), for the recursion depth and the `groups` array.

## 7. Gotchas & takeaways

> Gotcha: skipping the upfront check `sorted[0] > target` still gives a correct answer eventually (the backtracking search would fail every branch involving that oversized element), but wastes significant time before discovering the impossibility — always add cheap, obvious prune checks before starting an expensive search.

- This problem is the direct generalization of Matchsticks to Square: same technique, `k` groups instead of a fixed `4`.
- The "skip other empty groups" prune matters even more here than in the 4-group case, since larger `k` means more interchangeable empty groups to (wastefully) try without it.
- Related problems: Matchsticks to Square (the `k=4` special case), Fair Distribution of Cookies (a related bin-packing-style backtracking problem, minimizing the maximum group sum instead of requiring equality).
