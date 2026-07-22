---
card: leetcode-patterns
gi: 214
slug: subsets
title: Subsets
---

## 1. What it is

Given an array `nums` of unique integers, return all possible subsets (the power set), with no duplicate subsets. Example: `nums = [1,2,3]` → `[[],[1],[1,2],[1,2,3],[1,3],[2],[2,3],[3]]`.

## 2. Why & when

This is the pattern's namesake problem: the direct application of the DFS backtracking template with no extra twist. It is the perfect baseline before tackling variants that add duplicate-handling or a size/sum constraint.

## 3. Core concept

**Key idea:** DFS from index `0`, adding the CURRENT partial list to the results at every node (not just leaves), then trying each remaining element in turn — include it, recurse, then remove it (backtrack) — before moving to the next element.

**Steps:**
1. Call a recursive helper with an empty partial list and a starting index of `0`.
2. At the start of every call, add a COPY of the current partial list to the results — every partial state, including the empty list, is itself a valid subset.
3. Loop from the starting index to the end of `nums`: add `nums[i]` to the partial list, recurse with `i + 1`, then remove `nums[i]` (backtrack) before trying the next `i`.
4. Return the collected results once the initial call completes.

**Why it is correct:** the `start` index ensures each subset is built by considering elements in a FIXED relative order (only ever moving forward through the array), so the same combination of elements can never be generated twice via a different ordering — this is exactly what distinguishes subsets (order-independent) from permutations.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DFS tree where every node, not just leaves, is a valid subset result">
  <g font-family="sans-serif" font-size="12">
    <circle cx="60" cy="30" r="14" fill="#161b22" stroke="#3fb950"/><text x="60" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">[]</text>
    <circle cx="30" cy="80" r="14" fill="#161b22" stroke="#79c0ff"/><text x="30" y="84" fill="#e6edf3" text-anchor="middle" font-size="9">[1]</text>
    <circle cx="10" cy="130" r="14" fill="#161b22" stroke="#e3b341"/><text x="10" y="134" fill="#e6edf3" text-anchor="middle" font-size="7">[1,2]</text>
    <line x1="60" y1="44" x2="35" y2="66" stroke="#8b949e"/>
    <line x1="30" y1="94" x2="12" y2="116" stroke="#8b949e"/>
    <text x="10" y="15" fill="#e6edf3">every node in the tree (not just leaves) is added to the results as a valid subset</text>
  </g>
</svg>

Unlike a permutations tree (results only at leaves), every single node along the way is itself a complete, valid subset.

## 5. Runnable example

```java
// Subsets.java
import java.util.*;

public class Subsets {

    // Level 1 -- Brute force: use bitmasking -- for each of the 2^n
    // numbers from 0 to 2^n-1, treat each bit as "include this
    // element," building one subset per bitmask. Correct and actually
    // similarly efficient, but less readable and harder to extend to
    // variants with extra constraints (size limits, sum targets) than
    // the DFS backtracking shape.

    // KEY INSIGHT: DFS with a `start` index, adding the current partial
    // list at EVERY node (not just leaves), generates each subset
    // exactly once, in a form that's easy to extend with extra
    // conditions later.

    // Level 2 -- Optimal: DFS backtracking, add at every node.
    static List<List<Integer>> subsets(int[] nums) {
        List<List<Integer>> result = new ArrayList<>();
        dfs(nums, 0, new ArrayList<>(), result);
        return result;
    }

    static void dfs(int[] nums, int start, List<Integer> path, List<List<Integer>> result) {
        result.add(new ArrayList<>(path));
        for (int i = start; i < nums.length; i++) {
            path.add(nums[i]);
            dfs(nums, i + 1, path, result);
            path.remove(path.size() - 1);
        }
    }

    // Level 3 -- Hardened: an empty input array correctly returns
    // `[[]]` (just the empty subset), since the base `result.add` at
    // the top-level call happens before the (empty) loop ever runs.

    public static void main(String[] args) {
        System.out.println(subsets(new int[]{1,2,3}));
        // [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]
    }
}
```

**How to run:** `java Subsets.java`

## 6. Walkthrough

Trace `dfs(nums, 0, [], result)` on `nums = [1,2,3]`:

| Call | path | Added to result | Loop tries |
|---|---|---|---|
| dfs(0) | [] | `[]` | i=0,1,2 |
| dfs(1) via i=0 | [1] | `[1]` | i=1,2 |
| dfs(2) via i=1 | [1,2] | `[1,2]` | i=2 |
| dfs(3) via i=2 | [1,2,3] | `[1,2,3]` | none (i starts at 3, past end) |

After this deepest branch, backtracking unwinds: remove `3` (back to `[1,2]`), no more `i` to try; remove `2` (back to `[1]`), try `i=2`: add `3`, recurse, adds `[1,3]`; then fully backtrack to `[]` and try `i=1`, generating `[2]`, `[2,3]`, then `i=2` generating `[3]`. Time complexity is O(n · 2ⁿ), since there are 2ⁿ subsets, each costing O(n) to copy; space is O(n · 2ⁿ) for the output, plus O(n) for the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: passing `path` directly to `result.add(path)` instead of `result.add(new ArrayList<>(path))` stores a reference to the SAME mutable list — every subsequent backtracking mutation then corrupts every previously "saved" subset to look identical to the final state.

- The `start` parameter, not a `visited` array, is what prevents duplicate/reordered subsets — since subsets only ever move forward through the array, no element can be reconsidered out of order.
- Every recursive call adds exactly one result (unlike permutations, which only add at the leaves) — this is the defining structural feature of the subsets DFS template.
- Related problems: Subsets II (adds duplicate-input handling), Combinations (adds a fixed-size constraint), Combination Sum (adds a sum-target constraint).
