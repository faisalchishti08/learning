---
card: leetcode-patterns
gi: 216
slug: permutations
title: Permutations
---

## 1. What it is

Given an array `nums` of unique integers, return all possible permutations (every distinct ordering) of the elements. Example: `nums = [1,2,3]` → `[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]`.

## 2. Why & when

This is the pattern's namesake permutations problem: the direct application of the "choose next from remaining" DFS template with no extra twist. Unlike subsets, ORDER matters here, so every element must be tried at every position, tracked via a `used` array instead of a `start` index.

## 3. Core concept

**Key idea:** DFS builds a partial ordering one position at a time. At each position, try EVERY unused element as the next one placed — not just elements after some index, since any order is valid. A result is added only at LEAVES, when the partial ordering's length equals the input length.

**Steps:**
1. Call a recursive helper with an empty partial list and a `used` boolean array (all `false` initially).
2. Base case: if the partial list's length equals `nums.length`, add a copy to the results and return.
3. Loop over every index `i` from `0` to `nums.length - 1`: skip if `used[i]` is `true`.
4. Otherwise, mark `used[i] = true`, add `nums[i]` to the partial list, recurse, then remove `nums[i]` and reset `used[i] = false` (backtrack) before trying the next `i`.

**Why it is correct:** trying every unused element at every position (rather than only elements after a fixed index) is exactly what generates every possible ORDERING — since any element could legally come next, regardless of which elements came before it. The `used` array correctly ensures each element appears exactly once per permutation, and the leaf-only result collection ensures only COMPLETE orderings are recorded.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="At each position, every unused element is tried; results collected only at leaves">
  <g font-family="sans-serif" font-size="12">
    <circle cx="100" cy="30" r="4" fill="#e6edf3"/>
    <line x1="100" y1="30" x2="60" y2="70" stroke="#3fb950"/><text x="40" y="85" fill="#3fb950" font-size="10">pick 1</text>
    <line x1="100" y1="30" x2="100" y2="70" stroke="#79c0ff"/><text x="100" y="85" fill="#79c0ff" font-size="10">pick 2</text>
    <line x1="100" y1="30" x2="140" y2="70" stroke="#e3b341"/><text x="150" y="85" fill="#e3b341" font-size="10">pick 3</text>
    <circle cx="60" cy="70" r="4" fill="#e6edf3"/><circle cx="100" cy="70" r="4" fill="#e6edf3"/><circle cx="140" cy="70" r="4" fill="#e6edf3"/>
    <text x="10" y="15" fill="#e6edf3">every element is a valid "next choice" at every position -- unlike subsets, no start index restricts options</text>
  </g>
</svg>

Every unused element is a valid next choice at any position, since order matters and any element could legally come next.

## 5. Runnable example

```java
// Permutations.java
import java.util.*;

public class Permutations {

    // Level 1 -- Brute force: generate all n^n sequences by choosing
    // freely at each position WITHOUT tracking usage, then filter out
    // any sequence that repeats an element. Correct, but wastes huge
    // amounts of work generating and discarding invalid sequences
    // instead of only ever generating valid ones.

    // KEY INSIGHT: a `used` boolean array lets DFS only ever consider
    // VALID next choices (unused elements), generating exactly the n!
    // valid permutations with no wasted work on invalid sequences.

    // Level 2 -- Optimal: DFS with a `used` array, add results at
    // leaves.
    static List<List<Integer>> permute(int[] nums) {
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
            used[i] = true;
            path.add(nums[i]);
            dfs(nums, used, path, result);
            path.remove(path.size() - 1);
            used[i] = false;
        }
    }

    // Level 3 -- Hardened: resetting `used[i] = false` AFTER
    // backtracking (removing the element from `path`) is essential --
    // otherwise later sibling branches would incorrectly believe this
    // element is still in use.

    public static void main(String[] args) {
        System.out.println(permute(new int[]{1,2,3}));
        // [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
    }
}
```

**How to run:** `java Permutations.java`

## 6. Walkthrough

Trace `dfs(nums, used, [], result)` on `nums = [1,2,3]`, following the `i=0` branch first:

| Call | path | used | Action |
|---|---|---|---|
| dfs, path=[] | [] | [F,F,F] | i=0 unused, mark used[0], add 1 |
| dfs, path=[1] | [1] | [T,F,F] | i=1 unused, mark used[1], add 2 |
| dfs, path=[1,2] | [1,2] | [T,T,F] | i=2 unused, mark used[2], add 3 |
| dfs, path=[1,2,3] | [1,2,3] | [T,T,T] | length==3, save `[1,2,3]`, return |

Backtracking: remove `3`, reset `used[2]=false`; back at `path=[1,2]`, no more unused elements at this level, backtrack further; remove `2`, reset `used[1]=false`; back at `path=[1]`, try `i=2`: add `3`, then only `i=1` remains unused, producing `[1,3,2]`. This continues until all 6 permutations are found. Time complexity is O(n · n!), since there are n! permutations, each costing O(n) to copy; space is O(n · n!) for the output, plus O(n) for the recursion stack and `used` array.

## 7. Gotchas & takeaways

> Gotcha: forgetting to reset `used[i] = false` after backtracking (or resetting it BEFORE removing the element from `path`, in the wrong order relative to the recursive call) leaves stale state that either blocks valid future branches or allows an element to be used twice in the same permutation.

- Permutations use a `used` array; subsets/combinations use a `start` index — mixing these up is the most common bug when adapting one template to the other's problem shape.
- Results are collected only at LEAVES here (full-length paths), unlike subsets, which collect at every node — get this backwards and you either get zero results or far too many.
- Related problems: Permutations II (adds duplicate-input handling via sorting plus a same-level skip), Combinations (uses a `start` index instead, since order does not matter there).
