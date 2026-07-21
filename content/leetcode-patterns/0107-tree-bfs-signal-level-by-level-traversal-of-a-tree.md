---
card: leetcode-patterns
gi: 107
slug: tree-bfs-signal-level-by-level-traversal-of-a-tree
title: Tree BFS — signal: level-by-level traversal of a tree
---

## 1. What it is

Tree Breadth-First Search (Tree BFS) visits a tree one level at a time, from the root downward, instead of plunging deep down one branch first. It processes every node at depth 0, then every node at depth 1, then depth 2, and so on, using a queue to remember which nodes come next.

## 2. Why & when

Depth-First Search (DFS) explores one branch all the way to a leaf before backtracking, so it does not naturally know which nodes sit at the same depth. Many problems ask directly about levels — the widest level, the value at each depth, the last node visible from the side — and BFS answers these with a single, simple pass because it visits nodes in depth order.

Learn to recognize these signals in a problem statement:

- **"Level order"**, **"level by level"**, or **"by depth"** traversal of a tree.
- **"Minimum depth"** or **"shortest path"** in an unweighted tree — BFS finds the nearest target first, so it stops early instead of exploring every branch.
- **"Right side view"**, **"zigzag"**, or any output organized as one group per depth.
- **"Connect nodes at the same level"** (e.g. populating `next` pointers across a row).

The alternative is DFS with a `depth` parameter, which also visits every node but groups results by depth only after collecting a depth number alongside each node. BFS is more direct here — it visits nodes in depth order for free, so grouping by level needs no extra bookkeeping beyond tracking how many nodes are in the current level.

## 3. Core concept

**Key idea:** put the root in a queue, then repeatedly remove the front node, process it, and push its children onto the back of the queue. Because a queue is first-in-first-out, all nodes at depth `d` are removed (and their children queued) before any node at depth `d + 1` is removed.

**Steps:**
1. Push `root` onto an empty queue (skip if `root` is `null`).
2. While the queue is not empty:
   - Remove the node at the front of the queue.
   - Process it (record its value, compare it, etc.).
   - Push its non-null children onto the back of the queue, left then right.
3. Stop when the queue is empty — every node has been visited exactly once.

**Why it works:** a queue preserves the order nodes were added. Every node at depth `d` gets added to the queue only after every node at depth `d - 1` has already been removed and its children queued. So the queue always finishes draining one full depth before the next depth's nodes start coming out the front — the traversal naturally moves layer by layer.

## 4. Diagram

<svg viewBox="0 0 620 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tree BFS visiting nodes level by level using a queue">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">Tree:</text>
    <circle cx="300" cy="40" r="18" fill="#161b22" stroke="#79c0ff"/><text x="300" y="45" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="220" cy="100" r="18" fill="#161b22" stroke="#79c0ff"/><text x="220" y="105" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="380" cy="100" r="18" fill="#161b22" stroke="#79c0ff"/><text x="380" y="105" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="180" cy="160" r="18" fill="#161b22" stroke="#79c0ff"/><text x="180" y="165" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="260" cy="160" r="18" fill="#161b22" stroke="#79c0ff"/><text x="260" y="165" fill="#e6edf3" text-anchor="middle">5</text>
    <line x1="290" y1="55" x2="230" y2="87" stroke="#8b949e"/>
    <line x1="310" y1="55" x2="370" y2="87" stroke="#8b949e"/>
    <line x1="212" y1="115" x2="188" y2="147" stroke="#8b949e"/>
    <line x1="228" y1="115" x2="252" y2="147" stroke="#8b949e"/>
    <text x="20" y="210" fill="#e6edf3">Queue order: [1] -&gt; [2,3] -&gt; [3,4,5] -&gt; [4,5] -&gt; [5] -&gt; []</text>
    <text x="20" y="230" fill="#8b949e">Visit order: 1 (depth 0), 2, 3 (depth 1), 4, 5 (depth 2)</text>
  </g>
</svg>

The queue holds exactly the nodes of the level currently being drained — nodes from the next level are appended to the back but never processed before the current level empties.

## 5. Runnable example

```java
// TreeBfsSignal.java
import java.util.*;

public class TreeBfsSignal {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    static List<Integer> bfsOrder(TreeNode root) {
        List<Integer> order = new ArrayList<>();
        if (root == null) return order;

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            TreeNode node = queue.poll();
            order.add(node.val);
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
        return order;
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1);
        root.left = new TreeNode(2);
        root.right = new TreeNode(3);
        root.left.left = new TreeNode(4);
        root.left.right = new TreeNode(5);

        System.out.println(bfsOrder(root));
    }
}
```

How to run: save as `TreeBfsSignal.java`, then run `java TreeBfsSignal.java`.

## 6. Walkthrough

1. Queue starts as `[1]`. Remove `1`, record it, push its children: queue becomes `[2, 3]`.
2. Remove `2`, record it, push its children: queue becomes `[3, 4, 5]`.
3. Remove `3`, record it (no children): queue becomes `[4, 5]`.
4. Remove `4`, record it (no children): queue becomes `[5]`.
5. Remove `5`, record it (no children): queue becomes `[]`. Loop ends.
6. Final visit order is `[1, 2, 3, 4, 5]` — depth 0, then depth 1 left-to-right, then depth 2 left-to-right.

## 7. Gotchas & takeaways

> Gotcha: using a stack (`push`/`pop`, last-in-first-out) instead of a queue turns this into DFS, not BFS — the order of visited nodes changes completely, even though the code otherwise looks similar.

- A plain queue traversal visits nodes in level order but does not tell you where one level ends and the next begins — see the next page (§Tree BFS — template) for tracking level boundaries.
- Tree BFS also solves shortest-path-style questions (e.g. minimum depth) efficiently, because it reaches shallow nodes before deep ones and can stop as soon as it finds what it is looking for.
