---
card: leetcode-patterns
gi: 121
slug: add-one-row-to-tree
title: Add One Row to Tree
---

## 1. What it is

Given the `root` of a binary tree, an integer `val`, and an integer `depth`, insert a new row of nodes with value `val` at the given `depth`. Every original node at `depth - 1` gets two new children holding `val`; the original left subtree hangs off the new left child, and the original right subtree hangs off the new right child. If `depth == 1`, the new row becomes the new root, with the whole original tree as its left child. Example: `root = [4,2,6,3,1,5]`, `val = 1`, `depth = 2` → `[4,1,1,2,null,null,6,3,1,5]`.

## 2. Why & when

This needs Tree BFS because the row to insert before is identified by depth, and BFS naturally stops you at any depth by counting levels as it goes. It belongs in this section because `levelSize` and a running depth counter are exactly what let you stop one level short of the target and splice in the new row there.

## 3. Core concept

**Key idea:** run level-order BFS while counting the current depth. When the depth counter reaches `targetDepth - 1`, every node in that level gets two new children carrying `val`; the node's old left child becomes the new left child's left child, and the old right child becomes the new right child's right child.

**Steps:**
1. If `depth == 1`, create a new node with `val` whose left child is the old `root`; return the new node.
2. Push `root` onto the queue with `currentDepth = 1`.
3. While the queue is not empty and `currentDepth < depth - 1`: drain the level normally (using `levelSize`), pushing children as usual; increment `currentDepth`.
4. Once `currentDepth == depth - 1`, for every node in the current level: save `oldLeft` and `oldRight`; set `node.left = new TreeNode(val, oldLeft, null)`; set `node.right = new TreeNode(val, null, oldRight)`.
5. Return `root`.

**Why it is correct:** the depth counter increments exactly once per fully-drained level, so stopping at `depth - 1` guarantees you are looking at the direct parents of where the new row belongs, before any of their existing children are touched.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Splicing a new row of nodes above the target depth">
  <g font-family="sans-serif" font-size="12">
    <circle cx="240" cy="35" r="16" fill="#161b22" stroke="#79c0ff"/><text x="240" y="40" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="170" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="170" y="95" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="310" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="310" y="95" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="150" cy="145" r="16" fill="#161b22" stroke="#79c0ff"/><text x="150" y="150" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="330" cy="145" r="16" fill="#161b22" stroke="#79c0ff"/><text x="330" y="150" fill="#e6edf3" text-anchor="middle">6</text>
    <line x1="232" y1="49" x2="178" y2="77" stroke="#8b949e"/>
    <line x1="248" y1="49" x2="302" y2="77" stroke="#8b949e"/>
    <line x1="163" y1="104" x2="152" y2="132" stroke="#3fb950" stroke-width="2"/>
    <line x1="317" y1="104" x2="328" y2="132" stroke="#3fb950" stroke-width="2"/>
    <text x="10" y="185" fill="#e6edf3">New row (green) at depth 2: old subtrees reattach as left.left and right.right</text>
  </g>
</svg>

Each new node keeps exactly one side (left child hangs left, right child hangs right) so the original subtree structure is preserved below the inserted row.

## 5. Runnable example

```java
// AddOneRowToTree.java
public class AddOneRowToTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: DFS with a depth argument, checking
    // depth == targetDepth - 1 on every recursive call. O(n) time,
    // correct but re-derives "how deep am I" via recursion instead of
    // the natural level counter a queue already gives you.
    static TreeNode bruteForce(TreeNode root, int val, int depth) {
        if (depth == 1) return new TreeNode(val, root, null);
        dfsInsert(root, val, depth, 1);
        return root;
    }

    static void dfsInsert(TreeNode node, int val, int targetDepth, int currentDepth) {
        if (node == null) return;
        if (currentDepth == targetDepth - 1) {
            node.left = new TreeNode(val, node.left, null);
            node.right = new TreeNode(val, null, node.right);
            return;
        }
        dfsInsert(node.left, val, targetDepth, currentDepth + 1);
        dfsInsert(node.right, val, targetDepth, currentDepth + 1);
    }

    // KEY INSIGHT: BFS already advances one full level per iteration, so
    // stopping the queue drain once currentDepth == targetDepth - 1 finds
    // the exact parent row without any recursive depth argument.

    // Level 2 -- Optimal: BFS with levelSize, stopping the loop one level
    // short of the target and splicing in the new row there. O(n) time,
    // O(w) space (widest level).
    public static TreeNode addOneRow(TreeNode root, int val, int depth) {
        if (depth == 1) return new TreeNode(val, root, null);

        java.util.Queue<TreeNode> queue = new java.util.LinkedList<>();
        queue.offer(root);
        int currentDepth = 1;
        while (!queue.isEmpty()) {
            if (currentDepth == depth - 1) {
                for (TreeNode node : queue) {
                    node.left = new TreeNode(val, node.left, null);
                    node.right = new TreeNode(val, null, node.right);
                }
                break;
            }
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            currentDepth++;
        }
        return root;
    }

    // Level 3 -- Hardened: depth == 1 must wrap the whole tree in a new
    // root with an empty right side, without running the BFS loop at all.
    static TreeNode hardened(TreeNode root, int val, int depth) {
        return addOneRow(root, val, depth);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(4);
        root.left = new TreeNode(2);
        root.right = new TreeNode(6);
        root.left.left = new TreeNode(3);
        root.left.right = new TreeNode(1);
        root.right.left = new TreeNode(5);

        TreeNode a = bruteForce(root, 1, 2);
        System.out.println(a.val + " " + a.left.val + " " + a.right.val);

        TreeNode root2 = new TreeNode(4);
        root2.left = new TreeNode(2);
        root2.right = new TreeNode(6);
        TreeNode b = addOneRow(root2, 1, 2);
        System.out.println(b.val + " " + b.left.val + " " + b.right.val);

        TreeNode single = new TreeNode(9);
        TreeNode c = hardened(single, 5, 1);
        System.out.println(c.val + " " + c.left.val + " " + c.right);
    }
}
```

How to run: save as `AddOneRowToTree.java`, then run `java AddOneRowToTree.java`.

## 6. Walkthrough

Dry run of `addOneRow(root, val=1, depth=2)` on `[4,2,6,3,1,5]`:

| step | currentDepth | queue | action |
|---|---|---|---|
| start | 1 | [4] | `currentDepth == depth - 1` (1 == 1), splice now |
| splice | 1 | [4] | `4.left = new(1, old 2, null)`; `4.right = new(1, null, old 6)` |

Final tree root is still `4`, with new children valued `1` on both sides, and the old subtrees rooted at `2` and `6` now one level deeper. Time complexity: O(n) in the worst case (every node visited once before the target depth is reached). Space complexity: O(w), the widest level, for the queue.

## 7. Gotchas & takeaways

> Gotcha: attaching the old left subtree to the new node's `right` side (or vice versa) silently swaps left and right children — the old left child must become the new left node's left child, and the old right child must become the new right node's right child.

- The `depth == 1` case is special: there is no "level above" the root to iterate, so it is handled separately by wrapping the whole tree in a new root.
- Related problems: Binary Tree Level Order Traversal (the same level-draining loop, without any mutation), Populating Next Right Pointers in Each Node (also mutates nodes level by level, but links instead of inserting).
