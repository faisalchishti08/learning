---
card: leetcode-patterns
gi: 145
slug: binary-tree-paths
title: Binary Tree Paths
---

## 1. What it is

Given the `root` of a binary tree, return all root-to-leaf paths, each formatted as a string with node values joined by `"->"`. Example: `root = [1,2,3,null,5]` → `["1->2->5","1->3"]`.

## 2. Why & when

This is the pre-order "carry state down" style of Tree DFS: the path string is built up incrementally as the recursion descends, and it is only finalized (added to the result) once a leaf is reached. It belongs in this section as a direct sibling of Path Sum II — same shape, but the accumulated state is a formatted string instead of a running numeric sum, and the "list of results" holds strings instead of lists of integers.

## 3. Core concept

**Key idea:** carry a `currentPath` string down the recursion, appending `"->" + node.val` (or just `node.val` for the root) at each step. When a leaf is reached, the accumulated string is a complete answer — add it to the result list.

**Steps:**
1. Base case: if `node == null`, return (nothing to add).
2. Build: `newPath = currentPath.isEmpty() ? String.valueOf(node.val) : currentPath + "->" + node.val`.
3. Base case: if `node` is a leaf (`left == null && right == null`), add `newPath` to the result list, and stop (no further recursion needed from a leaf).
4. Recurse: call on `node.left` and `node.right`, passing `newPath` to both.

**Why it is correct:** because `newPath` is built as a new string at every call (not mutated in place), each recursive branch automatically gets its own independent copy of the path so far — there is no need for an explicit backtrack step like Path Sum II needed for its shared, mutable list.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Path string grows independently down each branch">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="15" fill="#161b22" stroke="#79c0ff"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="170" cy="85" r="15" fill="#161b22" stroke="#3fb950"/><text x="170" y="89" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="290" cy="85" r="15" fill="#161b22" stroke="#f85149"/><text x="290" y="89" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="210" cy="140" r="13" fill="#161b22" stroke="#3fb950"/><text x="210" y="144" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <line x1="221" y1="43" x2="179" y2="72" stroke="#3fb950" stroke-width="2"/>
    <line x1="239" y1="43" x2="281" y2="72" stroke="#f85149" stroke-width="2"/>
    <line x1="180" y1="98" x2="202" y2="128" stroke="#3fb950" stroke-width="2"/>
    <text x="10" y="175" fill="#e6edf3">Green branch builds "1-&gt;2-&gt;5"; red branch independently builds "1-&gt;3"</text>
  </g>
</svg>

Each branch builds its own path string from scratch off the parent's string — no shared mutable state means no backtracking is needed.

## 5. Runnable example

```java
// BinaryTreePaths.java
import java.util.*;

public class BinaryTreePaths {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: collect every root-to-leaf path as a LIST
    // of integers first (copying the list at every call, like Path Sum
    // II's brute force), then join each list into a string afterward.
    // O(n^2) time worst case due to repeated list copying, plus a
    // separate formatting pass.
    static List<String> bruteForce(TreeNode root) {
        List<List<Integer>> rawPaths = new ArrayList<>();
        collectPaths(root, new ArrayList<>(), rawPaths);
        List<String> result = new ArrayList<>();
        for (List<Integer> path : rawPaths) {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < path.size(); i++) {
                if (i > 0) sb.append("->");
                sb.append(path.get(i));
            }
            result.add(sb.toString());
        }
        return result;
    }

    static void collectPaths(TreeNode node, List<Integer> pathSoFar, List<List<Integer>> result) {
        if (node == null) return;
        List<Integer> newPath = new ArrayList<>(pathSoFar);
        newPath.add(node.val);
        if (node.left == null && node.right == null) { result.add(newPath); return; }
        collectPaths(node.left, newPath, result);
        collectPaths(node.right, newPath, result);
    }

    // KEY INSIGHT: building the FORMATTED string directly (instead of a
    // list of integers to be joined later) means each recursive call
    // hands its child a ready-to-use string -- no separate formatting
    // pass, and no shared mutable buffer requiring backtracking.

    // Level 2 -- Optimal: pre-order DFS building the path string
    // directly. O(n) time overall (n leaves times average path length,
    // bounded by total tree size), O(h) space for the recursion stack.
    public static List<String> binaryTreePaths(TreeNode root) {
        List<String> result = new ArrayList<>();
        dfs(root, "", result);
        return result;
    }

    static void dfs(TreeNode node, String currentPath, List<String> result) {
        if (node == null) return;
        String newPath = currentPath.isEmpty() ? String.valueOf(node.val) : currentPath + "->" + node.val;
        if (node.left == null && node.right == null) { result.add(newPath); return; }
        dfs(node.left, newPath, result);
        dfs(node.right, newPath, result);
    }

    // Level 3 -- Hardened: a single-node tree must return a list
    // containing exactly one string: that node's value with no arrow.
    static List<String> hardened(TreeNode root) {
        return binaryTreePaths(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1,
            new TreeNode(2, null, new TreeNode(5)),
            new TreeNode(3));

        System.out.println(bruteForce(root));
        System.out.println(binaryTreePaths(root));
        System.out.println(hardened(new TreeNode(9)));
    }
}
```

How to run: save as `BinaryTreePaths.java`, then run `java BinaryTreePaths.java`.

## 6. Walkthrough

Dry run of `dfs` on `[1,2,3,null,5]`:

| call | currentPath in | newPath | is leaf? | action |
|---|---|---|---|---|
| dfs(1, "") | "" | "1" | no | recurse left (2), then right (3) |
| dfs(2, "1") | "1" | "1->2" | no | recurse right (5) only (no left child) |
| dfs(5, "1->2") | "1->2" | "1->2->5" | yes | add "1->2->5" |
| dfs(3, "1") | "1" | "1->3" | yes | add "1->3" |

Final result: `["1->2->5", "1->3"]`. Time complexity: O(n) total, since each node contributes to at most one path string being built. Space complexity: O(h), the recursion stack (each level's string is independent, not shared).

## 7. Gotchas & takeaways

> Gotcha: building `newPath` with string concatenation (`currentPath + "->" + node.val`) creates a NEW string object every call rather than mutating a shared buffer — this is why no backtracking step is needed here, unlike Path Sum II's shared `List`, but it does mean repeated concatenation could be slower than a `StringBuilder` for very deep, narrow trees (still O(n) total in the worst realistic cases for typical problem sizes).

- Checking `currentPath.isEmpty()` to decide whether to prepend `"->"` is what correctly avoids a leading arrow before the root's own value.
- Related problems: Path Sum II (the same accumulate-down-the-recursion shape, using a shared mutable list with backtracking instead of immutable string concatenation), Sum Root to Leaf Numbers (accumulates a numeric value built digit by digit instead of a formatted string).
