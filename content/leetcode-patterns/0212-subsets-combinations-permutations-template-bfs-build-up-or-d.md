---
card: leetcode-patterns
gi: 212
slug: subsets-combinations-permutations-template-bfs-build-up-or-d
title: Subsets (Combinations & Permutations) — template: BFS build-up or DFS include/exclude decisions
---

## 1. What it is

Two reusable skeletons cover almost every problem in this family: the **DFS backtracking template** (recursive, make a choice / recurse / undo the choice) and the **BFS build-up template** (iteratively grow a list of partial results by extending each one with every possible next choice). Both produce the same final set of outputs; DFS is more common in practice because it naturally supports pruning (skipping whole invalid branches early).

## 2. Why & when

Memorizing these templates means you spend your problem-solving time on the CONSTRAINT (what makes a candidate valid — a size limit, a sum target, a no-duplicates rule) instead of re-deriving the branching and backtracking mechanics from scratch.

Use DFS backtracking by default — it is the more flexible and more commonly expected template, and supports early pruning (stopping a branch the moment it becomes invalid, e.g. sum exceeds target). Use BFS build-up when the problem naturally describes "start with an empty result and grow it," or when you want all PARTIAL results at each stage explicitly available (rare, but occurs in some subset-generation variants).

## 3. Core concept

**DFS backtracking template (subsets/combinations shape).**
1. A recursive helper takes the current partial answer (a list), a starting index into the input, and the results collector.
2. At entry, add a COPY of the current partial answer to the results (for subsets, every partial state is itself a valid answer; for combinations of exact size, only add when the size matches).
3. Loop from the starting index to the end of the input: add the current element to the partial answer, recurse with `index + 1`, then REMOVE the element (backtrack) before trying the next index.

**DFS backtracking template (permutations shape).**
1. A recursive helper takes the current partial answer, a `used` boolean array, and the results collector.
2. Base case: if the partial answer's length equals the input length, add a copy to the results and return.
3. Loop over EVERY index in the input: skip if already used; otherwise mark it used, add it to the partial answer, recurse, then unmark it and remove it (backtrack).

**BFS build-up template (subsets shape).**
1. Start `results` as a list containing just the empty list.
2. For each element in the input, create new lists by appending that element to EVERY existing list in `results`, and add all those new lists to `results`.
3. After processing every element, `results` contains all 2ⁿ subsets.

The key insight shared by both DFS templates: adding to the partial answer, recursing, then removing it (backtrack) is what lets a single mutable list represent every branch of the tree without allocating a new list per node — the copy only happens at the moment a valid answer is FOUND.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DFS backtracking adds, recurses, then removes; BFS build-up extends every existing partial result with a new element">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3" font-weight="bold">DFS: add -&gt; recurse -&gt; remove (backtrack)</text>
    <rect x="20" y="40" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="50" y="60" fill="#e6edf3" text-anchor="middle">[1]</text>
    <path d="M85,55 L140,55" stroke="#79c0ff" marker-end="url(#a9)"/>
    <defs><marker id="a9" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
    <rect x="145" y="40" width="70" height="30" fill="#161b22" stroke="#79c0ff"/><text x="180" y="60" fill="#e6edf3" text-anchor="middle">[1,2]</text>

    <text x="380" y="24" fill="#e6edf3" font-weight="bold">BFS: extend every existing list with new element</text>
    <rect x="380" y="50" width="50" height="26" fill="#161b22" stroke="#30363d"/><text x="405" y="68" fill="#e6edf3" text-anchor="middle" font-size="10">[]</text>
    <rect x="380" y="90" width="50" height="26" fill="#161b22" stroke="#30363d"/><text x="405" y="108" fill="#e6edf3" text-anchor="middle" font-size="10">[1]</text>
    <rect x="450" y="50" width="60" height="26" fill="#161b22" stroke="#e3b341"/><text x="480" y="68" fill="#e6edf3" text-anchor="middle" font-size="10">[2]</text>
    <rect x="450" y="90" width="60" height="26" fill="#161b22" stroke="#e3b341"/><text x="480" y="108" fill="#e6edf3" text-anchor="middle" font-size="10">[1,2]</text>
  </g>
</svg>

DFS mutates one shared list, undoing each choice after exploring it; BFS creates new lists by extending every existing one with the next element.

## 5. Runnable example

Both templates side by side, generating all subsets of `{1, 2, 3}`.

```java
// SubsetTemplates.java
import java.util.*;

public class SubsetTemplates {

    static List<List<Integer>> subsetsDFS(int[] nums) {
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

    static List<List<Integer>> subsetsBFS(int[] nums) {
        List<List<Integer>> result = new ArrayList<>();
        result.add(new ArrayList<>());
        for (int num : nums) {
            int size = result.size();
            for (int i = 0; i < size; i++) {
                List<Integer> extended = new ArrayList<>(result.get(i));
                extended.add(num);
                result.add(extended);
            }
        }
        return result;
    }

    public static void main(String[] args) {
        int[] nums = {1, 2, 3};
        System.out.println("DFS: " + subsetsDFS(nums));
        System.out.println("BFS: " + subsetsBFS(nums));
    }
}
```

**How to run:** `java SubsetTemplates.java`

## 6. Walkthrough

1. `subsetsDFS` calls `dfs(nums, 0, [], result)`. It immediately adds `[]` to results (every partial state is valid for subsets).
2. Loop `i=0`: add `1` to `path` (now `[1]`), recurse with `start=1`. This adds `[1]` to results, then loops `i=1`: add `2` (now `[1,2]`), recurse, adds `[1,2]`, continues to `[1,2,3]`.
3. After exhausting that branch, backtrack: remove `3`, remove `2`, back to `path=[1]`. Loop continues at `i=2` (from the `start=1` call): add `3` (now `[1,3]`), recurse, adds `[1,3]`.
4. Backtrack fully to `path=[]`. Loop continues at `i=1`: add `2` (now `[2]`), recurse, following the same pattern for `[2]`, `[2,3]`.
5. `subsetsBFS` reaches the identical final set by iteratively doubling: `[[]]` → `[[],[1]]` → `[[],[1],[2],[1,2]]` → `[[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]`.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `start` parameter in the subsets DFS template (always looping from index `0` instead of from the current `start`) generates every PERMUTATION of every subset as a separate duplicate entry, instead of each subset exactly once.

- `result.add(new ArrayList<>(path))` — always copy, never add the mutable `path` reference directly; the shared list keeps changing after being "added."
- The subsets DFS template adds a result at EVERY node (not just leaves); the permutations DFS template adds a result ONLY at leaves (when the partial answer is fully built) — this is the key structural difference between the two shapes.
- This exact DFS template, with `start` for subsets/combinations or `used[]` for permutations, is the direct basis for every named problem in this section — Combination Sum adds a sum check, Permutations II adds duplicate-skipping, and so on.
