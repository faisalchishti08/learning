---
card: leetcode-patterns
gi: 137
slug: path-sum-iii
title: Path Sum III
---

## 1. What it is

Given the `root` of a binary tree and an integer `targetSum`, return the number of paths where the sum of values along the path equals `targetSum`. Unlike Path Sum and Path Sum II, the path does not need to start at the root or end at a leaf — it only needs to travel strictly downward (parent to child, never up or sideways). Example: `root = [10,5,-3,3,2,null,11,3,-2,null,1]`, `targetSum = 8` → `3`.

## 2. Why & when

Because a valid path can start at ANY node, not just the root, the brute-force approach tries every node as a possible start. The efficient approach reuses a classic trick: track the running sum from the root to the current node (a "prefix sum"), and recognize that a path from some ancestor to the current node sums to `targetSum` exactly when an earlier prefix sum equals `currentPrefixSum - targetSum`. This belongs in Tree DFS because the prefix sum is carried down the recursion (pre-order style), and a hash map of "prefix sums seen on the current root-to-here path" must be cleaned up (backtracked) when returning from a subtree.

## 3. Core concept

**Key idea:** as you DFS down from the root, keep a running `prefixSum` (the sum of every node from the root to here) and a map counting how many times each prefix sum has occurred on the current path. For the current node, the number of valid paths ENDING here equals `countOf(prefixSum - targetSum)` in that map — because if some ancestor's prefix sum was `prefixSum - targetSum`, the segment from just after that ancestor down to here sums to exactly `targetSum`.

**Steps:**
1. Initialize a map with `{0: 1}` (representing the "empty prefix", so a path starting exactly at the root is counted correctly).
2. Define `dfs(node, prefixSum)`: base case, if `node == null`, return `0`.
3. Update: `prefixSum += node.val`.
4. Look up: `pathsEndingHere = map.getOrDefault(prefixSum - targetSum, 0)`.
5. Record: increment `map[prefixSum]` by `1` (this node's prefix sum is now visible to its descendants).
6. Recurse: `total = pathsEndingHere + dfs(node.left, prefixSum) + dfs(node.right, prefixSum)`.
7. Backtrack: decrement `map[prefixSum]` by `1` before returning (remove this node's prefix sum so sibling branches don't see it).
8. Return `total`.

**Why it is correct:** the map only ever contains prefix sums from nodes that are actual ancestors of the current node (thanks to the backtrack step removing a node's contribution once its subtree is fully explored), so `map[prefixSum - targetSum]` counts exactly the ancestors from which a downward path to the current node would sum to `targetSum`.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Prefix sum difference reveals a valid downward path between two nodes">
  <g font-family="sans-serif" font-size="12">
    <circle cx="240" cy="30" r="15" fill="#161b22" stroke="#79c0ff"/><text x="240" y="34" fill="#e6edf3" text-anchor="middle">10</text>
    <text x="265" y="25" fill="#8b949e" font-size="10">prefix=10</text>
    <circle cx="180" cy="80" r="15" fill="#161b22" stroke="#3fb950"/><text x="180" y="84" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="120" y="75" fill="#3fb950" font-size="10">prefix=15</text>
    <circle cx="150" cy="130" r="15" fill="#161b22" stroke="#3fb950"/><text x="150" y="134" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="80" y="125" fill="#3fb950" font-size="10">prefix=18, lookup 10, hit</text>
    <line x1="232" y1="43" x2="188" y2="68" stroke="#8b949e"/>
    <line x1="163" y1="93" x2="153" y2="118" stroke="#3fb950" stroke-width="2"/>
    <text x="10" y="15" fill="#e6edf3">Node 3's prefix (18) minus targetSum (8) equals 10 -- node 10's own prefix</text>
    <text x="10" y="175" fill="#e6edf3">So the segment strictly below node 10, ending at node 3 (i.e. 5 -&gt; 3), sums to 8</text>
  </g>
</svg>

Each node's prefix sum (root to that node) is stored in the map while its subtree is explored, then removed once the subtree finishes — this is what lets the map answer "how many ancestors make a valid path end here?" in O(1).

## 5. Runnable example

```java
// PathSumIII.java
import java.util.*;

public class PathSumIII {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: try every node as a path start, and from
    // each start, DFS downward summing until targetSum is matched or
    // exceeded. O(n^2) time worst case (a skewed tree), since each of
    // the n possible starts triggers its own O(n) downward scan.
    static int bruteForce(TreeNode root, int targetSum) {
        if (root == null) return 0;
        return countFrom(root, targetSum) + bruteForce(root.left, targetSum) + bruteForce(root.right, targetSum);
    }

    static int countFrom(TreeNode node, long remaining) {
        if (node == null) return 0;
        remaining -= node.val;
        int count = (remaining == 0) ? 1 : 0;
        return count + countFrom(node.left, remaining) + countFrom(node.right, remaining);
    }

    // KEY INSIGHT: a running prefix sum from the root, combined with a
    // map of "how many ancestors had this prefix sum", finds every
    // valid path ending at the current node in O(1) per node -- no
    // need to re-scan downward from every possible start.

    // Level 2 -- Optimal: prefix sum + hash map with backtracking.
    // O(n) time, O(h) space (the map holds at most h entries at once,
    // one per ancestor on the current root-to-node path).
    public static int pathSum(TreeNode root, int targetSum) {
        Map<Long, Integer> prefixCount = new HashMap<>();
        prefixCount.put(0L, 1);
        return dfs(root, 0L, targetSum, prefixCount);
    }

    static int dfs(TreeNode node, long prefixSum, int targetSum, Map<Long, Integer> prefixCount) {
        if (node == null) return 0;
        prefixSum += node.val;
        int pathsEndingHere = prefixCount.getOrDefault(prefixSum - targetSum, 0);
        prefixCount.merge(prefixSum, 1, Integer::sum);

        int total = pathsEndingHere
            + dfs(node.left, prefixSum, targetSum, prefixCount)
            + dfs(node.right, prefixSum, targetSum, prefixCount);

        prefixCount.merge(prefixSum, -1, Integer::sum); // backtrack
        return total;
    }

    // Level 3 -- Hardened: a tree containing negative values (so a
    // longer path can "come back" to a smaller sum) must still be
    // counted correctly, since the map tracks exact sums, not just
    // monotonically increasing ones.
    static int hardened(TreeNode root, int targetSum) {
        return pathSum(root, targetSum);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(10,
            new TreeNode(5, new TreeNode(3, new TreeNode(3), new TreeNode(-2)), new TreeNode(2, null, new TreeNode(1))),
            new TreeNode(-3, null, new TreeNode(11)));

        System.out.println(bruteForce(root, 8));
        System.out.println(pathSum(root, 8));
        System.out.println(hardened(root, 100));
    }
}
```

How to run: save as `PathSumIII.java`, then run `java PathSumIII.java`.

## 6. Walkthrough

Dry run of `dfs` on the path `10 -> 5 -> 3` (part of the example tree, `targetSum = 8`):

| node | prefixSum | lookup key (prefixSum - 8) | pathsEndingHere | map after recording |
|---|---|---|---|---|
| 10 | 10 | 2 | 0 (no entry for 2) | {0:1, 10:1} |
| 5 | 15 | 7 | 0 (no entry for 7) | {0:1, 10:1, 15:1} |
| 3 | 18 | 10 | 1 (map has one 10, from node "10") | {0:1, 10:1, 15:1, 18:1} |

The match at node `3` (`pathsEndingHere = 1`) corresponds to the path `5 -> 3`, whose sum is `15 - 10 + 3`... more directly: the path from just after node `10` down to node `3` is `5 + 3 = 8`, matching `targetSum`. Across the whole tree, three such paths exist, so `pathSum(root, 8) == 3`. Time complexity: O(n), every node visited once with O(1) map operations. Space complexity: O(h) for the map and the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: forgetting the backtrack step (`prefixCount.merge(prefixSum, -1, ...)`) after exploring a node's subtree leaves that node's prefix sum visible to unrelated branches elsewhere in the tree, over-counting paths that do not actually lie on a single root-to-node line.

- Seeding the map with `{0: 1}` before the recursion starts is what correctly counts paths that begin exactly at the root, treating "no ancestors yet" as a valid empty prefix.
- Related problems: Path Sum (paths must start at the root and end at a leaf), Subarray Sum Equals K (the same prefix-sum-difference trick, applied to a flat array instead of a tree).
