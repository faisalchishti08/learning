---
card: leetcode-patterns
gi: 217
slug: permutations-ii
title: Permutations II
---

## 1. What it is

Given an array `nums` that MAY contain duplicate values, return all possible UNIQUE permutations, with no duplicate orderings in the output. Example: `nums = [1,1,2]` → `[[1,1,2],[1,2,1],[2,1,1]]`.

## 2. Why & when

This combines Permutations' "choose next from remaining" tree with Subsets II's "skip a duplicate value at the same tree level" trick. Without the skip, swapping which physical `1` (of two identical `1`s) goes first would generate the same-looking permutation twice.

## 3. Core concept

**Key idea:** sort `nums` so duplicate values become adjacent. In the DFS loop over possible next choices, skip index `i` if `nums[i] == nums[i-1]` AND `nums[i-1]` is CURRENTLY UNUSED (meaning this is not the first time a value from this duplicate group is being placed at this position in this branch) — using the later, still-available duplicate would just regenerate a permutation already produced by using the earlier one first.

**Steps:**
1. Sort `nums` in ascending order.
2. Call the DFS helper with an empty partial list and a `used` boolean array.
3. Base case: if the partial list's length equals `nums.length`, save a copy and return.
4. Loop over every index `i`: skip if `used[i]` is `true`. ALSO skip if `i > 0` AND `nums[i] == nums[i-1]` AND `used[i-1]` is `false` (the previous identical value is currently unused, meaning it was skipped over rather than placed, at this exact decision point).
5. Otherwise, mark `used[i] = true`, add `nums[i]`, recurse, then backtrack (remove, reset `used[i] = false`).

**Why it is correct:** requiring the PREVIOUS identical value to be USED (not merely "already tried") before allowing the current one to be placed enforces a strict left-to-right order among physically-identical values — this collapses every permutation that only differs by WHICH occurrence of a repeated value sits in which slot into a single canonical generation path, eliminating duplicates without needing a `Set` to filter them after the fact.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A duplicate value can only be placed after its identical predecessor has already been used">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="30" height="30" fill="#3fb950"/><text x="35" y="50" fill="#0d1117" text-anchor="middle">1a</text>
    <rect x="60" y="30" width="30" height="30" fill="#161b22" stroke="#f85149"/><text x="75" y="50" fill="#e6edf3" text-anchor="middle">1b</text>
    <text x="100" y="50" fill="#f85149">skip: 1a not yet used</text>
    <text x="10" y="15" fill="#e6edf3">the second physical "1" can only be placed once the first physical "1" has already been placed somewhere</text>
  </g>
</svg>

`1b` (the second occurrence) is only a valid next choice once `1a` (the first occurrence) has already been used earlier in this branch.

## 5. Runnable example

```java
// PermutationsII.java
import java.util.*;

public class PermutationsII {

    // Level 1 -- Brute force: generate all permutations as if elements
    // were distinct (using a `used` array only, no duplicate-skip
    // logic), then deduplicate the final list with a
    // Set<List<Integer>>. Correct, but generates and discards many
    // redundant branches instead of preventing them.

    // KEY INSIGHT: sort first, then only allow a duplicate value to be
    // placed once its identical PREDECESSOR is already used -- this
    // enforces a canonical left-to-right order among identical values,
    // preventing duplicate permutations at generation time.

    // Level 2 -- Optimal: sort + skip-duplicate-unless-predecessor-
    // used.
    static List<List<Integer>> permuteUnique(int[] nums) {
        Arrays.sort(nums);
        List<List<Integer>> result = new ArrayList<>();
        dfs(nums, new boolean[nums.length], new ArrayList<>(), result);
        return result;
    }

    static void dfs(int[] nums, boolean[] used, List<Integer> path, List<List<Integer>> result) {
        if (path.size() == nums.length) {
            result.add(new ArrayList<>(path));
            return;
        }
        for (int i = 0; i < nums.length; i++) {
            if (used[i]) continue;
            if (i > 0 && nums[i] == nums[i - 1] && !used[i - 1]) continue;
            used[i] = true;
            path.add(nums[i]);
            dfs(nums, used, path, result);
            path.remove(path.size() - 1);
            used[i] = false;
        }
    }

    // Level 3 -- Hardened: the `!used[i - 1]` condition (checking the
    // predecessor is CURRENTLY unused, not merely "value equal") is
    // what correctly distinguishes "this is a fresh branch skipping
    // ahead" (invalid) from "this is a later step where the
    // predecessor was already legitimately placed earlier" (valid).

    public static void main(String[] args) {
        System.out.println(permuteUnique(new int[]{1,1,2}));
        // [[1,1,2],[1,2,1],[2,1,1]]
    }
}
```

**How to run:** `java PermutationsII.java`

## 6. Walkthrough

Trace the first-level choices for sorted `nums = [1,1,2]` (indices 0,1,2, values 1,1,2):

| i | used[i] | Check | Allowed? |
|---|---|---|---|
| 0 | false | `i==0`, no duplicate check needed | yes, place `1` (index 0) |
| 1 | false | `nums[1]==nums[0]` AND `used[0]==false` (index 0 not yet placed in THIS branch, since we are trying i=1 as an alternative to i=0 at the SAME level) | skip |
| 2 | false | `nums[2] != nums[1]` | yes, place `2` |

At the top level, only index 0 (value `1`) and index 2 (value `2`) are tried as the first element — index 1 (the second `1`) is skipped, since index 0's `1` was not used in that particular branch attempt. Later, DEEPER in the tree, once index 0's `1` IS marked used (because it was placed first), index 1 becomes a valid next choice. Time complexity is O(n · n!) worst case; space is O(n · n!) for the output, plus O(n) for recursion and the `used` array.

## 7. Gotchas & takeaways

> Gotcha: using `used[i-1]` (skip if the predecessor IS used) instead of `!used[i-1]` (skip if the predecessor is NOT used) inverts the logic entirely, causing either massive duplication or missing valid permutations.

- This is the exact same "adjacent duplicate, guarded by a used/unused check" trick as Subsets II and Combination Sum II — the guard condition differs slightly (`!used[i-1]` here, versus `i > start` for the index-based subset/combination templates) because permutations track availability via a `used` array, not a `start` index.
- Sorting first is mandatory, exactly as in Subsets II, so identical values are adjacent and the skip check is meaningful.
- Related problems: Permutations (the no-duplicates base case), Subsets II (same duplicate-skip idea, applied to the subsets tree shape), Combination Sum II (same idea again, applied to a sum-target combinations tree).
