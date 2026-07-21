---
card: leetcode-patterns
gi: 125
slug: tree-dfs-signal-root-to-leaf-paths-or-recursive-subtree-comp
title: Tree DFS — signal: root-to-leaf paths or recursive subtree computation
---

## 1. What it is

Tree Depth-First Search (DFS) is the pattern of solving a tree problem by recursing into a node's children first, then combining their results with the current node's own value. The "signal" is the wording in a problem that tells you DFS, not BFS, is the right tool.

## 2. Why & when

Recognise this pattern from phrases like: "root-to-leaf path", "maximum depth", "is this tree balanced/symmetric/the same as another", "sum along a path", or "compute something about a subtree, then combine it with the parent". These all describe a value that depends on an entire subtree, which only exists once you have finished exploring that subtree — exactly what recursion (going deep before coming back) gives you for free.

Use DFS instead of BFS whenever the answer for a node depends on results computed from its children, rather than on which "row" a node sits in. If the problem instead says "level", "row", or "layer", that is the signal for Tree BFS, not this pattern.

The alternative — an explicit stack instead of recursion — works too, and is sometimes required to avoid stack overflow on very deep trees, but recursion is simpler to write and read for most interview-sized trees.

## 3. Core concept

**Key idea:** define a recursive function that takes a node and returns whatever partial answer that node's subtree contributes; call it on the left child, call it on the right child, then combine both results with the current node's own value before returning.

**General steps:**
1. **Base case:** if the node is `null`, return the "empty subtree" answer (often `0`, `true`, or an empty list — whatever makes the combination step correct).
2. **Recurse left:** call the function on `node.left`.
3. **Recurse right:** call the function on `node.right`.
4. **Combine:** merge the left result, right result, and `node.val` into this node's answer, and return it.

**Why it works:** the recursion only returns from a node after both its children have already returned, so by the time you combine results at a node, you are guaranteed to have the fully-computed answer for its entire left and right subtrees — never a partial one.

## 4. Diagram

<svg viewBox="0 0 480 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DFS returns from children before combining at the parent">
  <g font-family="sans-serif" font-size="12">
    <circle cx="240" cy="35" r="16" fill="#161b22" stroke="#3fb950"/><text x="240" y="40" fill="#e6edf3" text-anchor="middle">?</text>
    <circle cx="170" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="170" y="95" fill="#e6edf3" text-anchor="middle">L</text>
    <circle cx="310" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="310" y="95" fill="#e6edf3" text-anchor="middle">R</text>
    <circle cx="140" cy="145" r="14" fill="#161b22" stroke="#8b949e"/><text x="140" y="149" fill="#e6edf3" text-anchor="middle" font-size="11">a</text>
    <circle cx="200" cy="145" r="14" fill="#161b22" stroke="#8b949e"/><text x="200" y="149" fill="#e6edf3" text-anchor="middle" font-size="11">b</text>
    <line x1="232" y1="49" x2="178" y2="77" stroke="#8b949e"/>
    <line x1="248" y1="49" x2="302" y2="77" stroke="#8b949e"/>
    <line x1="163" y1="103" x2="145" y2="132" stroke="#8b949e"/>
    <line x1="177" y1="103" x2="197" y2="132" stroke="#8b949e"/>
    <text x="10" y="175" fill="#e6edf3">1. recurse to a, b (leaves) 2. combine at L 3. recurse to R</text>
    <text x="10" y="192" fill="#e6edf3">4. combine L-result, R-result, and root's own value at "?"</text>
  </g>
</svg>

The parent node's answer is only computed once both children have already returned their own combined answers.

## 5. Runnable example

```java
// TreeDfsTemplate.java
public class TreeDfsTemplate {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // The reusable template: recurse into both children, then combine
    // their results with this node's own value. Here the combination
    // computes the sum of all node values in the subtree.
    static int subtreeSum(TreeNode node) {
        if (node == null) return 0; // base case: empty subtree contributes 0
        int leftSum = subtreeSum(node.left);
        int rightSum = subtreeSum(node.right);
        return node.val + leftSum + rightSum; // combine
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1,
            new TreeNode(2, new TreeNode(4), new TreeNode(5)),
            new TreeNode(3));

        System.out.println(subtreeSum(root));
    }
}
```

How to run: save as `TreeDfsTemplate.java`, then run `java TreeDfsTemplate.java`.

## 6. Walkthrough

Trace of `subtreeSum(root)` on `root = [1,2,3,4,5]`:

1. `subtreeSum(1)` calls `subtreeSum(2)` first.
2. `subtreeSum(2)` calls `subtreeSum(4)`: `4` has no children, so `leftSum = 0`, `rightSum = 0`, returns `4 + 0 + 0 = 4`.
3. `subtreeSum(2)` calls `subtreeSum(5)`: same as above, returns `5`.
4. `subtreeSum(2)` combines: `2 + 4 + 5 = 11`. Returns `11`.
5. `subtreeSum(1)` calls `subtreeSum(3)`: `3` has no children, returns `3`.
6. `subtreeSum(1)` combines: `1 + 11 + 3 = 15`. Returns `15`.

Final answer: `15`, the sum of every node in the tree.

## 7. Gotchas & takeaways

> Gotcha: picking the wrong base-case value breaks the combination — for a sum the empty subtree must contribute `0`, but for a depth problem it must contribute `0` as well (not `-1`), while for a "same tree" comparison the base case must handle two `null` nodes as equal, and one `null` versus one non-null as unequal.

- The whole pattern is really one question, asked recursively: "what does an empty subtree contribute, and how do I combine two child answers with this node's value?" Answer that once and the recursion writes itself.
- Complexity is O(n) time (every node visited once) and O(h) space for the recursion stack, where `h` is the tree's height — covered in detail on the next page.
