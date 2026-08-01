---
card: data-structures
gi: 108
slug: path-sum-root-to-leaf-problems
title: Path-sum & root-to-leaf problems
---

## 1. What it is

**Path-sum** problems ask whether some path in a tree — most commonly a root-to-leaf path — adds up to a target value, or ask you to collect all such paths. "Root-to-leaf" means the path must start at the root and end at a node with no children; it is not any arbitrary path between two nodes (that would be a different, harder problem, related to [Tree height, depth & diameter](0107-tree-height-depth-diameter.md)'s diameter).

## 2. Why & when

This pattern tests whether you can carry running state *down* through a recursion (the accumulated sum so far) and correctly decide when a path is "complete" (only at a true leaf, not at any node with a missing child). It generalizes directly to any "find/collect paths meeting a condition" tree problem — a very common interview shape.

## 3. Core concept

**Key idea in one sentence.** Recurse downward, subtracting (or adding) each node's value from a running target as you go; only check for a match at an actual leaf, since a root-to-leaf path is not complete anywhere else.

**Level 1 — Basic: does a root-to-leaf path summing to the target exist?** At each node, subtract its value from the remaining target. If the node is a leaf, check whether the remaining target has reached exactly `0`. Otherwise, recurse into whichever children exist, and return `true` if *either* recursive call succeeds (using boolean OR, not AND — only one matching path is needed).

**Why checking only at leaves matters.** A path that "happens" to sum to the target partway down, at a non-leaf node, does not count — the problem specifically wants a *complete* root-to-leaf path. Checking at every node instead of just leaves would produce false positives for any node with children that has, coincidentally, absorbed exactly the remaining target so far.

**Level 2 — collect all matching paths, not just check existence.** Same downward recursion, but also maintain a list of "the path so far" (the actual sequence of values, not just the running sum). When a leaf matches, copy the current path into the results list. Critically, after returning from a recursive call, the current node's value must be removed from the "path so far" list (**backtracking**) — otherwise the list would incorrectly retain values from an already-explored branch when exploring a sibling branch.

**Level 3 — count paths that don't have to start at the root.** A harder variant: count *any* downward path (not necessarily starting at the root, but always going strictly downward) that sums to the target. The standard trick uses a running prefix-sum and a frequency map (see [Frequency maps & grouping](0096-frequency-maps-grouping-computeifabsent-merge.md)) to count, at each node, how many earlier prefix sums on the current path would make a valid target-sum sub-path ending here.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A tree with root 5, showing the running remaining target decrease at each step down one path, reaching exactly zero at a leaf, confirming a matching root to leaf path">
  <g font-family="sans-serif" font-size="11">
    <circle cx="300" cy="30" r="18" fill="#0d1117" stroke="#f0883e"/><text x="300" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <text x="380" y="20" fill="#8b949e" font-size="9">target = 8</text>
    <circle cx="240" cy="90" r="18" fill="#161b22" stroke="#79c0ff"/><text x="240" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">4</text>
    <circle cx="200" cy="150" r="18" fill="#0d1117" stroke="#79c0ff"/><text x="200" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">-1</text>
    <text x="120" y="150" fill="#79c0ff" font-size="9">leaf</text>
    <line x1="288" y1="42" x2="252" y2="78" stroke="#8b949e"/>
    <line x1="228" y1="102" x2="212" y2="138" stroke="#8b949e"/>
    <text x="450" y="60" fill="#8b949e" font-size="9">remaining after 5: 8-5=3</text>
    <text x="450" y="90" fill="#8b949e" font-size="9">remaining after 4: 3-4=-1</text>
    <text x="450" y="120" fill="#79c0ff" font-size="9">remaining after -1: -1-(-1)=0</text>
    <text x="450" y="140" fill="#79c0ff" font-size="9">leaf AND remaining==0 -&gt; MATCH</text>
  </g>
</svg>

Along the path `5 -> 4 -> -1`, the remaining target decreases by each node's value; reaching exactly `0` at a leaf confirms a matching root-to-leaf path.

## 5. Runnable example

```java
// PathSumRootToLeaf.java
import java.util.ArrayList;
import java.util.List;

public class PathSumRootToLeaf {

    static class TreeNode {
        int value;
        TreeNode left, right;
        TreeNode(int value) { this.value = value; }
        TreeNode(int value, TreeNode left, TreeNode right) { this.value = value; this.left = left; this.right = right; }
    }

    // Level 1: does ANY root-to-leaf path sum to the target?
    static boolean hasPathSum(TreeNode node, int remaining) {
        if (node == null) return false;
        remaining -= node.value;
        if (node.left == null && node.right == null) return remaining == 0; // only a TRUE leaf can complete a match
        return hasPathSum(node.left, remaining) || hasPathSum(node.right, remaining); // either side succeeding is enough
    }

    static void basicLevel() {
        TreeNode root = new TreeNode(5, new TreeNode(4, new TreeNode(-1), null), new TreeNode(8, new TreeNode(2), null));
        System.out.println("basic: hasPathSum(target=8) -> " + hasPathSum(root, 8));
        System.out.println("basic: hasPathSum(target=100) -> " + hasPathSum(root, 100));
    }

    // Level 2: collect ALL matching root-to-leaf paths, using backtracking to reuse one shared path list.
    static List<List<Integer>> allPathSums(TreeNode root, int target) {
        List<List<Integer>> results = new ArrayList<>();
        collectPaths(root, target, new ArrayList<>(), results);
        return results;
    }

    static void collectPaths(TreeNode node, int remaining, List<Integer> currentPath, List<List<Integer>> results) {
        if (node == null) return;
        currentPath.add(node.value); // step INTO this node: add it to the path
        remaining -= node.value;

        if (node.left == null && node.right == null && remaining == 0) {
            results.add(new ArrayList<>(currentPath)); // COPY the path -- currentPath will keep mutating after this
        } else {
            collectPaths(node.left, remaining, currentPath, results);
            collectPaths(node.right, remaining, currentPath, results);
        }

        currentPath.remove(currentPath.size() - 1); // step OUT of this node: backtrack before returning to the caller
    }

    static void intermediateLevel() {
        TreeNode root = new TreeNode(5, new TreeNode(4, new TreeNode(-1), null), new TreeNode(8, new TreeNode(2), null));
        System.out.println("intermediate: all paths summing to 8 -> " + allPathSums(root, 8));
    }

    // Level 3: count ANY downward path (not necessarily from the root) summing to the target, via prefix sums.
    static int pathSumAnyStart(TreeNode root, int target) {
        java.util.Map<Long, Integer> prefixCounts = new java.util.HashMap<>();
        prefixCounts.put(0L, 1); // an empty prefix (sum 0) occurs once, by convention -- handles a path starting at the root
        return countPaths(root, 0L, target, prefixCounts);
    }

    static int countPaths(TreeNode node, long currentSum, int target, java.util.Map<Long, Integer> prefixCounts) {
        if (node == null) return 0;
        currentSum += node.value;

        int count = prefixCounts.getOrDefault(currentSum - target, 0); // how many earlier prefixes make a valid sub-path ending HERE
        prefixCounts.merge(currentSum, 1, Integer::sum);

        count += countPaths(node.left, currentSum, target, prefixCounts);
        count += countPaths(node.right, currentSum, target, prefixCounts);

        prefixCounts.merge(currentSum, -1, Integer::sum); // backtrack: this prefix sum no longer applies once we leave this branch
        return count;
    }

    static void advancedLevel() {
        TreeNode root = new TreeNode(1, new TreeNode(2, new TreeNode(3), null), new TreeNode(-1, new TreeNode(1), null));
        System.out.println("advanced: count of any downward paths summing to 3 -> " + pathSumAnyStart(root, 3));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `PathSumRootToLeaf.java`, then run `java PathSumRootToLeaf.java`.

## 6. Walkthrough

1. `basicLevel()` checks `target = 8` against the tree `5(left: 4(left: -1), right: 8(left: 2))`. Path `5 -> 4 -> -1` gives `5 + 4 + (-1) = 8` — a match, since `-1` is a true leaf. `target = 100` finds no matching path in any branch, so `hasPathSum` returns `false`.
2. `intermediateLevel()` walks the same tree, building `currentPath` incrementally. At the leaf `-1`, `currentPath` is `[5, 4, -1]` and `remaining` is `0` — a match, so a *copy* of `[5, 4, -1]` is saved. After returning from that leaf, `-1` is removed from `currentPath` (backtracking), then `4` is removed too, before the recursion moves on to explore the `8` branch — without backtracking, `currentPath` would incorrectly carry `[5, 4]` into the unrelated `8` subtree.
3. `advancedLevel()`'s prefix-sum approach tracks, at every node, the running sum from the root down to that node. `currentSum - target` looks up how many *earlier* points on the current path had exactly the sum that would make the sub-path from just after that point to here equal `target` — this correctly counts paths that start anywhere, not just the root, because it is really asking "prefix(here) - prefix(some ancestor) == target," rearranged to a map lookup. The final `prefixCounts.merge(currentSum, -1, ...)` removes the current node's contribution once its subtree is fully explored, so a value from one branch never leaks into an unrelated sibling branch's count.

## 7. Gotchas & takeaways

> Gotcha: forgetting the backtracking step (removing the current node from `currentPath`, or decrementing its prefix-sum count) after exploring a subtree is one of the most common bugs in this pattern — without it, state from an already-explored branch silently contaminates the results for every subsequent sibling branch explored afterward.

- Only check for a match at a true leaf (both children `null`) — a root-to-leaf path is not complete anywhere else.
- Collecting all matching paths (not just checking existence) requires backtracking: undo the current node's contribution to shared state before returning to the caller.
- Counting any-start downward paths uses a prefix-sum-and-frequency-map trick, also requiring backtracking on the map count.
- Related concepts: [In-order / pre-order / post-order traversal](0101-in-order-pre-order-post-order-traversal.md), [Frequency maps & grouping (computeIfAbsent / merge)](0096-frequency-maps-grouping-computeifabsent-merge.md).
