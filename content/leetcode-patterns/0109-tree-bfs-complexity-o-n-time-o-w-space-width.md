---
card: leetcode-patterns
gi: 109
slug: tree-bfs-complexity-o-n-time-o-w-space-width
title: Tree BFS — complexity: O(n) time, O(w) space (width)
---

## 1. What it is

Tree BFS visits every node exactly once, so its time cost is O(n), where n is the number of nodes. Its space cost is O(w), where w is the maximum number of nodes present in the queue at any one time — the width of the tree's widest level.

## 2. Why & when

Knowing the exact complexity lets you defend a BFS solution in an interview and compare it honestly against DFS alternatives. Time is easy — every node is queued once and dequeued once, so the work is linear in the node count regardless of the tree's shape.

Space is the subtler part, because it does not depend on the tree's height (like DFS's recursion stack does) but on its **width** — how many nodes can exist at the same depth. Understanding this distinction matters when a problem states memory constraints, or when a tree is unbalanced in a way that makes one metric much larger than the other.

## 3. Core concept

**Key idea:** the queue only ever holds nodes from at most two adjacent levels — the tail end of the level being drained and the children of those nodes being appended for the next level. Its size peaks at the width of the tree's single widest level.

**Time — O(n):**
- Every node is pushed onto the queue exactly once (when its parent processes it, or as the root at the start).
- Every node is popped exactly once.
- Each push and pop is O(1), so total time is O(n) — n pushes and n pops, each constant work.

**Space — O(w):**
- At any instant, the queue contains a suffix of the current level plus a prefix of the next level being built.
- The largest this ever gets is bounded by the size of the widest level in the tree, called `w`.
- For a **balanced** binary tree, the widest level is the last one, with roughly `n / 2` nodes, so `w = O(n)` in the worst case.
- For a **skewed** tree (e.g. every node has only one child, like a linked list), every level has exactly 1 node, so `w = O(1)`.

So Tree BFS space usage ranges from O(1) (a completely skewed tree) up to O(n) (a wide, balanced tree) — always bounded by the widest level, never by the height.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparing queue width across a balanced tree and a skewed tree">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">Balanced tree: widest level has 4 nodes -&gt; queue peaks at w = 4</text>
    <circle cx="300" cy="40" r="14" fill="#161b22" stroke="#79c0ff"/>
    <circle cx="240" cy="80" r="14" fill="#161b22" stroke="#79c0ff"/>
    <circle cx="360" cy="80" r="14" fill="#161b22" stroke="#79c0ff"/>
    <circle cx="210" cy="120" r="14" fill="#161b22" stroke="#3fb950"/>
    <circle cx="270" cy="120" r="14" fill="#161b22" stroke="#3fb950"/>
    <circle cx="330" cy="120" r="14" fill="#161b22" stroke="#3fb950"/>
    <circle cx="390" cy="120" r="14" fill="#161b22" stroke="#3fb950"/>
    <text x="20" y="170" fill="#e6edf3">Skewed tree (each node has 1 child): every level has 1 node -&gt; queue peaks at w = 1</text>
    <circle cx="60" cy="190" r="10" fill="#161b22" stroke="#f0883e"/>
    <circle cx="100" cy="190" r="10" fill="#161b22" stroke="#f0883e"/>
    <circle cx="140" cy="190" r="10" fill="#161b22" stroke="#f0883e"/>
    <circle cx="180" cy="190" r="10" fill="#161b22" stroke="#f0883e"/>
    <line x1="70" y1="190" x2="90" y2="190" stroke="#8b949e"/>
    <line x1="110" y1="190" x2="130" y2="190" stroke="#8b949e"/>
    <line x1="150" y1="190" x2="170" y2="190" stroke="#8b949e"/>
  </g>
</svg>

The queue's peak size tracks the widest level, not the tree's height or total node count — the two example trees above have the same node count but very different peak queue sizes.

## 5. Runnable example

```java
// TreeBfsComplexity.java
import java.util.*;

public class TreeBfsComplexity {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Runs standard level-order BFS while tracking the largest queue size seen -- that peak is O(w).
    static int widestLevelSize(TreeNode root) {
        if (root == null) return 0;

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        int maxQueueSize = 0;

        while (!queue.isEmpty()) {
            maxQueueSize = Math.max(maxQueueSize, queue.size());
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
        }
        return maxQueueSize;
    }

    public static void main(String[] args) {
        // Balanced tree: 1 -> (2,3) -> (4,5,6,7). Widest level has 4 nodes.
        TreeNode balanced = new TreeNode(1);
        balanced.left = new TreeNode(2);
        balanced.right = new TreeNode(3);
        balanced.left.left = new TreeNode(4);
        balanced.left.right = new TreeNode(5);
        balanced.right.left = new TreeNode(6);
        balanced.right.right = new TreeNode(7);
        System.out.println("balanced tree width: " + widestLevelSize(balanced));

        // Skewed tree: 1 -> 2 -> 3 -> 4, each with only a left child. Widest level has 1 node.
        TreeNode skewed = new TreeNode(1);
        skewed.left = new TreeNode(2);
        skewed.left.left = new TreeNode(3);
        skewed.left.left.left = new TreeNode(4);
        System.out.println("skewed tree width: " + widestLevelSize(skewed));
    }
}
```

How to run: save as `TreeBfsComplexity.java`, then run `java TreeBfsComplexity.java`.

## 6. Walkthrough

For the balanced tree (7 nodes: `1`, then `2, 3`, then `4, 5, 6, 7`):

1. Level 0: queue size before draining is `1` (`[1]`). `maxQueueSize = 1`.
2. Level 1: queue size before draining is `2` (`[2, 3]`). `maxQueueSize = 2`.
3. Level 2: queue size before draining is `4` (`[4, 5, 6, 7]`). `maxQueueSize = 4`.
4. Loop ends. Output: `4` — matching the widest level.

For the skewed tree (4 nodes, each with one child):

1. Every level has exactly 1 node, so the queue size never exceeds `1`.
2. Output: `1`, even though the tree still has 4 nodes total.

Both trees do O(n) total work (7 and 4 pushes/pops respectively), but their peak space differs sharply — O(n) for the balanced tree versus O(1) for the skewed one.

## 7. Gotchas & takeaways

> Gotcha: assuming Tree BFS space is always O(n) — it is O(w), which only equals O(n) in the worst case (a wide, balanced tree). A skewed tree needs only O(1) queue space, even with the same node count.

- Time is always O(n) — every node is pushed and popped exactly once.
- Space is O(w), the width of the widest level — this can range from O(1) to O(n) depending on the tree's shape, unlike DFS whose space is O(h), the tree's height.
- For a **complete** binary tree specifically, the widest level is the last one and has close to `n / 2` nodes, so BFS space is O(n) there even though DFS space would only be O(log n).
