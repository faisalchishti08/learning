---
card: leetcode-patterns
gi: 116
slug: populating-next-right-pointers-in-each-node
title: Populating Next Right Pointers in Each Node
---

## 1. What it is

Given a **perfect** binary tree (every level fully filled) where each node has an extra `next` pointer, set every node's `next` to point to the node immediately to its right on the same level, or to `null` if it is the last node of its level. Example: `root = [1,2,3,4,5,6,7]` → level 1 becomes `2 -> 3 -> null`, level 2 becomes `4 -> 5 -> 6 -> 7 -> null`.

## 2. Why & when

This is Tree BFS with the output written back into the tree instead of into a separate list. Because the queue already holds one level's nodes in left-to-right order, connecting each dequeued node to the next one dequeued is exactly the `next` pointer you need. It belongs in this section because `levelSize` marks where one level's chain of `next` pointers must stop (end in `null`) before the next level's chain begins.

## 3. Core concept

**Key idea:** run level-order BFS. While draining a level, keep a reference to the previously dequeued node in that level and set `previous.next = current` for every node after the first in the level. The last node in the level keeps `next = null` (its default).

**Steps:**
1. Push `root` onto the queue.
2. While the queue is not empty:
   - Save `levelSize = queue.size()`.
   - Set `previous = null`.
   - Loop `levelSize` times: dequeue `current`; if `previous != null`, set `previous.next = current`; then set `previous = current`; push `current`'s non-null children.
3. Return the (now-linked) `root`.

**Why it is correct:** `previous` is reset to `null` at the start of every level, so no `next` pointer ever crosses from the last node of one level to the first node of the next; the loop only links nodes dequeued back to back within the same `levelSize` window.

## 4. Diagram

<svg viewBox="0 0 500 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Linking siblings with next pointers, one level at a time">
  <g font-family="sans-serif" font-size="12">
    <circle cx="250" cy="35" r="16" fill="#161b22" stroke="#79c0ff"/><text x="250" y="40" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="180" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="180" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="320" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="320" y="95" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="242" y1="49" x2="188" y2="77" stroke="#8b949e"/>
    <line x1="258" y1="49" x2="312" y2="77" stroke="#8b949e"/>
    <line x1="198" y1="90" x2="302" y2="90" stroke="#3fb950" stroke-dasharray="4,3"/>
    <text x="245" y="82" fill="#3fb950" font-size="10">next</text>
    <text x="330" y="94" fill="#8b949e" font-size="10">-&gt; null</text>
    <text x="10" y="185" fill="#e6edf3">Level 1: 2.next = 3, 3.next = null (chain resets each level)</text>
  </g>
</svg>

Nodes within a level are chained left to right; the chain resets to `null` before the next level starts.

## 5. Runnable example

```java
// PopulatingNextRightPointers.java
import java.util.*;

public class PopulatingNextRightPointers {

    static class Node {
        int val;
        Node left, right, next;
        Node(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: BFS using an ArrayDeque, but store nodes for
    // the whole level in a temporary list first, then link the list.
    // O(n) time, O(w) extra space for the temporary list on top of the queue.
    static Node bruteForce(Node root) {
        if (root == null) return null;
        Queue<Node> queue = new ArrayDeque<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            List<Node> level = new ArrayList<>();
            for (int i = 0; i < levelSize; i++) {
                Node node = queue.poll();
                level.add(node);
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            for (int i = 0; i + 1 < level.size(); i++) level.get(i).next = level.get(i + 1);
        }
        return root;
    }

    // KEY INSIGHT: you do not need to store the whole level to link it --
    // tracking just the single "previous" node while draining the queue is
    // enough, since each node only ever needs to point at the very next one.

    // Level 2 -- Optimal: BFS with levelSize and a running "previous"
    // reference, linking as nodes are dequeued. O(n) time, O(w) space
    // (the queue only; no extra per-level list).
    public static Node connect(Node root) {
        if (root == null) return null;
        Queue<Node> queue = new ArrayDeque<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            Node previous = null;
            for (int i = 0; i < levelSize; i++) {
                Node current = queue.poll();
                if (previous != null) previous.next = current;
                previous = current;
                if (current.left != null) queue.offer(current.left);
                if (current.right != null) queue.offer(current.right);
            }
        }
        return root;
    }

    // Level 3 -- Hardened: a single-node tree must leave next as null,
    // and the last node of every level must never be linked to the next
    // level's first node.
    static Node hardened(Node root) {
        return connect(root);
    }

    public static void main(String[] args) {
        Node root = new Node(1);
        root.left = new Node(2);
        root.right = new Node(3);
        root.left.left = new Node(4);
        root.left.right = new Node(5);
        root.right.left = new Node(6);
        root.right.right = new Node(7);

        connect(root);
        System.out.println(root.left.next.val);       // 3
        System.out.println(root.left.left.next.val);   // 5
        System.out.println(root.right.right.next);     // null
        System.out.println(hardened(new Node(9)).next); // null
    }
}
```

How to run: save as `PopulatingNextRightPointers.java`, then run `java PopulatingNextRightPointers.java`.

## 6. Walkthrough

Dry run of `connect` on the 7-node perfect tree above:

| level | levelSize | dequeue order | previous chain built |
|---|---|---|---|
| 0 | 1 | 1 | previous=1, no link (first node) |
| 1 | 2 | 2, 3 | 2.next = 3 |
| 2 | 4 | 4, 5, 6, 7 | 4.next=5, 5.next=6, 6.next=7 |

Final state: `2.next == 3`, `4.next == 5`, `7.next == null` (never set, its default). Time complexity: O(n), every node dequeued once. Space complexity: O(w), the widest level, for the queue.

## 7. Gotchas & takeaways

> Gotcha: forgetting to reset `previous = null` at the start of each level links the last node of one level to the first node of the next, corrupting the chain.

- This trick only works as written because the tree is **perfect** — every level is fully filled, so `levelSize` always matches the true node count with no gaps to account for.
- Related problems: Binary Tree Level Order Traversal (build a list per level instead of linking in place), Populating Next Right Pointers II (same idea, but the tree may be incomplete).
