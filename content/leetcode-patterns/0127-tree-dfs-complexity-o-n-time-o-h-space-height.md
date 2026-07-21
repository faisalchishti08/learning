---
card: leetcode-patterns
gi: 127
slug: tree-dfs-complexity-o-n-time-o-h-space-height
title: Tree DFS — complexity: O(n) time, O(h) space (height)
---

## 1. What it is

Every Tree DFS solution built from the template on the previous page costs O(n) time, where `n` is the number of nodes, and O(h) extra space, where `h` is the height of the tree — the length of the longest root-to-leaf path. This page explains exactly where those two costs come from.

## 2. Why & when

Knowing the complexity in advance lets you answer the "why is this efficient?" follow-up in an interview, and lets you predict when a solution might blow the call stack (very deep, unbalanced trees). It also lets you spot the difference between O(h) and O(log n): they are the same only when the tree is balanced; a skewed tree (essentially a linked list) has `h = n`, and the "efficient" DFS solution then uses O(n) space, not O(log n).

## 3. Core concept

**Key idea:** the time cost comes from visiting each node exactly once; the space cost comes from the recursion call stack, whose depth at any moment equals the current path length from the root.

**Why O(n) time:** the recursive function is called exactly once per node — once for the base case and once for every step of the combine. There is no repeated work: no node is revisited, and each call does O(1) work outside of its own two recursive calls. Summing one constant-time visit per node gives O(n) total.

**Why O(h) space:** the call stack holds one frame per node currently "in progress" — that is, every ancestor of whichever node is being visited right now, down to the current node itself. The deepest that stack ever gets is the length of the longest path from the root to the leaf currently being explored, which is exactly the tree's height `h`.

**The balanced vs skewed distinction:**
- A balanced tree has `h = O(log n)` (each level roughly halves the remaining nodes), so DFS space is O(log n).
- A completely skewed tree (every node has only one child) has `h = n`, so DFS space degrades to O(n) — no better than storing every node in a list.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Balanced tree has small height; skewed tree has height equal to n">
  <g font-family="sans-serif" font-size="12">
    <circle cx="110" cy="30" r="14" fill="#161b22" stroke="#79c0ff"/><text x="110" y="34" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="70" cy="70" r="14" fill="#161b22" stroke="#79c0ff"/><text x="70" y="74" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="150" cy="70" r="14" fill="#161b22" stroke="#79c0ff"/><text x="150" y="74" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="50" cy="110" r="14" fill="#161b22" stroke="#79c0ff"/><text x="50" y="114" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="90" cy="110" r="14" fill="#161b22" stroke="#79c0ff"/><text x="90" y="114" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <line x1="103" y1="43" x2="76" y2="58" stroke="#8b949e"/>
    <line x1="117" y1="43" x2="144" y2="58" stroke="#8b949e"/>
    <line x1="63" y1="83" x2="53" y2="98" stroke="#8b949e"/>
    <line x1="77" y1="83" x2="87" y2="98" stroke="#8b949e"/>
    <text x="10" y="150" fill="#e6edf3">Balanced: n=5, h=3 -&gt; O(log n) stack depth</text>
    <circle cx="340" cy="20" r="12" fill="#161b22" stroke="#f85149"/><text x="340" y="24" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <circle cx="340" cy="55" r="12" fill="#161b22" stroke="#f85149"/><text x="340" y="59" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <circle cx="340" cy="90" r="12" fill="#161b22" stroke="#f85149"/><text x="340" y="94" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>
    <circle cx="340" cy="125" r="12" fill="#161b22" stroke="#f85149"/><text x="340" y="129" fill="#e6edf3" text-anchor="middle" font-size="10">4</text>
    <line x1="340" y1="32" x2="340" y2="43" stroke="#8b949e"/>
    <line x1="340" y1="67" x2="340" y2="78" stroke="#8b949e"/>
    <line x1="340" y1="102" x2="340" y2="113" stroke="#8b949e"/>
    <text x="300" y="150" fill="#e6edf3">Skewed: n=4, h=4 -&gt; O(n) stack depth</text>
  </g>
</svg>

Both trees hold roughly the same number of nodes, but the skewed one has a recursion stack four times deeper.

## 5. Runnable example

```java
// TreeDfsComplexity.java
public class TreeDfsComplexity {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Counts recursive calls and reports the deepest stack depth reached,
    // to make the O(n) time / O(h) space claim concrete and measurable.
    static int calls = 0;
    static int maxDepthSeen = 0;

    static int height(TreeNode node, int currentDepth) {
        calls++;
        maxDepthSeen = Math.max(maxDepthSeen, currentDepth);
        if (node == null) return 0;
        int leftHeight = height(node.left, currentDepth + 1);
        int rightHeight = height(node.right, currentDepth + 1);
        return 1 + Math.max(leftHeight, rightHeight);
    }

    public static void main(String[] args) {
        // Balanced tree: 1 -> (2, 3), 2 -> (4, 5). n = 5, h = 3.
        TreeNode balanced = new TreeNode(1);
        balanced.left = new TreeNode(2);
        balanced.right = new TreeNode(3);
        balanced.left.left = new TreeNode(4);
        balanced.left.right = new TreeNode(5);

        calls = 0; maxDepthSeen = 0;
        int h1 = height(balanced, 1);
        System.out.println("balanced height=" + h1 + " calls=" + calls + " maxDepthSeen=" + maxDepthSeen);

        // Skewed tree: 1 -> 2 -> 3 -> 4 (each has only a left child). n = 4, h = 4.
        TreeNode skewed = new TreeNode(1);
        skewed.left = new TreeNode(2);
        skewed.left.left = new TreeNode(3);
        skewed.left.left.left = new TreeNode(4);

        calls = 0; maxDepthSeen = 0;
        int h2 = height(skewed, 1);
        System.out.println("skewed height=" + h2 + " calls=" + calls + " maxDepthSeen=" + maxDepthSeen);
    }
}
```

How to run: save as `TreeDfsComplexity.java`, then run `java TreeDfsComplexity.java`.

## 6. Walkthrough

For the balanced tree (`n = 5` nodes plus null children counted as calls): `calls` ends up at `11` (5 real nodes + 6 null base cases), confirming O(n) total calls; `maxDepthSeen` ends at `4` — one more than `h = 3`, because the deepest calls are the `null` base cases one level below the deepest real leaf.

For the skewed tree (`n = 4` nodes): `calls` ends at `9` (4 real nodes + 5 null base cases along the single chain); `maxDepthSeen` ends at `5`, again one more than `h = 4` for the same reason — the stack goes one frame deeper per node, since there is no branching to keep it shallow.

Both trees do O(n) total work (number of calls scales linearly with node count), but the skewed tree's peak stack depth equals its node count, while the balanced tree's peak stack depth is much smaller.

## 7. Gotchas & takeaways

> Gotcha: assuming DFS space is always O(log n) — that is only true for balanced trees. A problem with adversarial or already-sorted input (common for binary search trees built by inserting a sorted list) produces a skewed tree, where DFS space becomes O(n) and a very deep recursion can even trigger a `StackOverflowError`.

- When asked "what is the space complexity", always answer O(h), then clarify h can range from O(log n) (balanced) to O(n) (skewed) depending on the input.
- This is the standard cost for every problem in this section: Maximum Depth, Same Tree, Symmetric Tree, Path Sum, Invert Binary Tree, Diameter, Balanced Binary Tree, Subtree of Another Tree, Path Sum II.
