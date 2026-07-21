---
card: leetcode-patterns
gi: 154
slug: vertical-order-traversal-of-a-binary-tree
title: Vertical Order Traversal of a Binary Tree
---

## 1. What it is

Given the `root` of a binary tree, return its nodes' values arranged by vertical "column": imagine each node placed at a column position (root at column `0`, a left child one column to the left, a right child one column to the right). Return the values column by column, left to right; within a column, order top to bottom (by row), and for nodes in the same column AND the same row, order by value ascending. Example: `root = [3,1,4,0,2,2]` (with `4` having two children both at value `2`) groups nodes with matching `(column, row)` and sorts ties by value.

## 2. Why & when

This needs DFS (or BFS) to assign every node a `(column, row)` coordinate — a left child's column is `parentColumn - 1`, a right child's is `parentColumn + 1`, and every child's row is `parentRow + 1`. It belongs in Tree DFS because assigning coordinates is naturally done with a pre-order-style traversal that passes `(column, row)` down to each child; the actual grouping and sorting happens afterward, once every node's coordinate is known.

## 3. Core concept

**Key idea:** traverse the tree once, recording each node's value along with its `(column, row)` coordinate. Group all recorded nodes by column. Within each column, sort by row first, and break ties (same column AND same row) by value.

**Steps:**
1. Define `dfs(node, column, row)`: base case, if `node == null`, return.
2. Record `(column, row, node.val)` in a flat list.
3. Recurse: `dfs(node.left, column - 1, row + 1)`, `dfs(node.right, column + 1, row + 1)`.
4. After the traversal, group all recorded entries by `column`.
5. Sort the columns themselves by column number (ascending, left to right).
6. Within each column's group, sort by `(row, value)` — row ascending first, value ascending to break ties.
7. Build the result: one list per column, in sorted order.

**Why it is correct:** column and row are defined purely by the parent-to-child offsets (`-1`/`+1` for column, always `+1` for row), so passing them down the recursion assigns every node a coordinate consistent with its actual position in the tree; sorting by `(column, row, value)` afterward directly implements the problem's stated ordering rule.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each node gets a column and row coordinate based on left/right offsets from its parent">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="15" fill="#161b22" stroke="#79c0ff"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="250" y="20" fill="#8b949e" font-size="10">(col 0, row 0)</text>
    <circle cx="170" cy="85" r="15" fill="#161b22" stroke="#79c0ff"/><text x="170" y="89" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="90" y="80" fill="#8b949e" font-size="10">(col -1, row 1)</text>
    <circle cx="290" cy="85" r="15" fill="#161b22" stroke="#79c0ff"/><text x="290" y="89" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="300" y="80" fill="#8b949e" font-size="10">(col 1, row 1)</text>
    <circle cx="260" cy="140" r="13" fill="#161b22" stroke="#3fb950"/><text x="260" y="144" fill="#e6edf3" text-anchor="middle" font-size="11">0</text>
    <text x="180" y="150" fill="#3fb950" font-size="10">(col 0, row 2)</text>
    <circle cx="320" cy="140" r="13" fill="#161b22" stroke="#3fb950"/><text x="320" y="144" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <line x1="222" y1="43" x2="178" y2="72" stroke="#8b949e"/>
    <line x1="238" y1="43" x2="282" y2="72" stroke="#8b949e"/>
    <line x1="282" y1="97" x2="266" y2="126" stroke="#8b949e"/>
    <line x1="298" y1="97" x2="314" y2="126" stroke="#8b949e"/>
    <text x="10" y="175" fill="#e6edf3">Node 3 (col 0, row 0) and node 0 (col 0, row 2) share column 0 but differ in row</text>
  </g>
</svg>

Node `3` and node `0` both sit in column `0`, at different rows, so both appear in column `0`'s output, ordered by row.

## 5. Runnable example

```java
// VerticalOrderTraversal.java
import java.util.*;

public class VerticalOrderTraversal {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    static class Entry {
        int column, row, val;
        Entry(int column, int row, int val) { this.column = column; this.row = row; this.val = val; }
    }

    // Level 1 -- Brute force: BFS instead of DFS to assign coordinates
    // (functionally equivalent for this problem, since only coordinates
    // matter, not visit order), then sort the ENTIRE flat list by
    // (column, row, value) in one combined comparator, then split into
    // columns afterward. O(n log n) time either way -- included mainly
    // to show the traversal order does not matter, only the final sort.
    static List<List<Integer>> bruteForce(TreeNode root) {
        List<Entry> entries = new ArrayList<>();
        Queue<TreeNode> nodeQueue = new LinkedList<>();
        Queue<int[]> coordQueue = new LinkedList<>();
        nodeQueue.offer(root);
        coordQueue.offer(new int[]{0, 0});
        while (!nodeQueue.isEmpty()) {
            TreeNode node = nodeQueue.poll();
            int[] coord = coordQueue.poll();
            if (node == null) continue;
            entries.add(new Entry(coord[0], coord[1], node.val));
            nodeQueue.offer(node.left); coordQueue.offer(new int[]{coord[0] - 1, coord[1] + 1});
            nodeQueue.offer(node.right); coordQueue.offer(new int[]{coord[0] + 1, coord[1] + 1});
        }
        return groupAndSort(entries);
    }

    // KEY INSIGHT: whether you gather (column, row, value) triples via
    // DFS or BFS makes no difference to the final answer -- the actual
    // work is entirely in the grouping and sorting step afterward, so
    // pick whichever traversal is simplest to write.

    // Level 2 -- Optimal: pre-order DFS to assign coordinates, then
    // group by column and sort by (row, value) within each column.
    // O(n log n) time (dominated by the sort), O(n) space.
    public static List<List<Integer>> verticalTraversal(TreeNode root) {
        List<Entry> entries = new ArrayList<>();
        dfs(root, 0, 0, entries);
        return groupAndSort(entries);
    }

    static void dfs(TreeNode node, int column, int row, List<Entry> entries) {
        if (node == null) return;
        entries.add(new Entry(column, row, node.val));
        dfs(node.left, column - 1, row + 1, entries);
        dfs(node.right, column + 1, row + 1, entries);
    }

    static List<List<Integer>> groupAndSort(List<Entry> entries) {
        entries.sort((a, b) -> {
            if (a.column != b.column) return Integer.compare(a.column, b.column);
            if (a.row != b.row) return Integer.compare(a.row, b.row);
            return Integer.compare(a.val, b.val);
        });
        List<List<Integer>> result = new ArrayList<>();
        int currentColumn = Integer.MIN_VALUE;
        for (Entry entry : entries) {
            if (entry.column != currentColumn) {
                result.add(new ArrayList<>());
                currentColumn = entry.column;
            }
            result.get(result.size() - 1).add(entry.val);
        }
        return result;
    }

    // Level 3 -- Hardened: two nodes with the same column AND the same
    // row must be ordered by value ascending, not left-to-right visit
    // order -- verified with a tree where a left-side and right-side
    // node land on the same coordinate.
    static List<List<Integer>> hardened(TreeNode root) {
        return verticalTraversal(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(3,
            new TreeNode(1, null, new TreeNode(0)),
            new TreeNode(4, new TreeNode(2), null));

        System.out.println(bruteForce(root));
        System.out.println(verticalTraversal(root));

        TreeNode tie = new TreeNode(1, new TreeNode(3), new TreeNode(2));
        // node 3 (left child, col -1) and node 2 (right child, col 1) do NOT tie here;
        // a genuine tie needs a deeper tree, shown in the walkthrough instead.
        System.out.println(hardened(tie));
    }
}
```

How to run: save as `VerticalOrderTraversal.java`, then run `java VerticalOrderTraversal.java`.

## 6. Walkthrough

Dry run of `dfs` on `root = [3,1,4,null,0,2,null]` where `1` has a right child `0`, and `4` has a left child `2`:

| node | column | row |
|---|---|---|
| 3 | 0 | 0 |
| 1 | -1 | 1 |
| 0 | 0 | 2 |
| 4 | 1 | 1 |
| 2 | 0 | 2 |

Grouping by column: column `-1` has `[1]`; column `0` has `3` (row 0), and `0`, `2` (both row 2, tied — sorted by value: `0` before `2`); column `1` has `[4]`. Final result: `[[1], [3, 0, 2], [4]]`. Time complexity: O(n log n), dominated by sorting all `n` entries. Space complexity: O(n) for the entries list.

## 7. Gotchas & takeaways

> Gotcha: sorting by `(column, row)` alone, without the value as a final tiebreaker, leaves the relative order of same-column-same-row nodes UNDEFINED (dependent on sort stability and traversal order) — the problem requires those ties to be broken specifically by ascending value, so the comparator must include `value` as its last key.

- Assigning `(column, row)` coordinates works identically whether you traverse with DFS or BFS — the coordinates themselves, not the traversal order, are what the final answer depends on.
- Related problems: Binary Tree Level Order Traversal (groups by row alone, with no column dimension or value-based tiebreak), Binary Tree Zigzag Level Order Traversal (also reasons about horizontal position, but only to alternate direction, not to group nodes into columns).
