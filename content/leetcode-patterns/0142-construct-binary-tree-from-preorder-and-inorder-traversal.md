---
card: leetcode-patterns
gi: 142
slug: construct-binary-tree-from-preorder-and-inorder-traversal
title: Construct Binary Tree from Preorder and Inorder Traversal
---

## 1. What it is

Given two integer arrays `preorder` and `inorder` representing the pre-order and in-order traversal of the same binary tree (with unique values), rebuild and return the tree. Example: `preorder = [3,9,20,15,7]`, `inorder = [9,3,15,20,7]` → `[3,9,20,null,null,15,7]`.

## 2. Why & when

Pre-order always lists the root of a (sub)tree first; in-order always splits into "everything left of the root" and "everything right of the root". Combining those two facts lets you reconstruct the tree top-down: read the next unused pre-order value as the current subtree's root, then use its position in the in-order array to split the remaining work into a left recursive call and a right recursive call. This belongs in Tree DFS because building the tree IS a pre-order recursion — root first, then recursively build left, then right.

## 3. Core concept

**Key idea:** the first element of `preorder` (within the current range) is always the root of the current subtree. Find that value's index in `inorder`; everything to its left in `inorder` belongs to the left subtree, everything to its right belongs to the right subtree. Recurse on those two splits, advancing through `preorder` in the same fixed order every time (root, then all of the left subtree, then all of the right subtree).

**Steps:**
1. Build a hash map from value to index in `inorder`, for O(1) lookups.
2. Keep a single pointer `preorderIndex` into `preorder`, starting at `0`.
3. Define `build(inorderLeft, inorderRight)`: base case, if `inorderLeft > inorderRight`, return `null`.
4. Take the next root: `rootVal = preorder[preorderIndex]`, then increment `preorderIndex`.
5. Find `mid = inorderMap[rootVal]` (this root's position within the current in-order slice).
6. Build left first: `node.left = build(inorderLeft, mid - 1)`.
7. Build right second: `node.right = build(mid + 1, inorderRight)`.
8. Return the new `node`.

**Why it is correct:** pre-order always visits a subtree's root before any of its descendants, so reading `preorder[preorderIndex]` and incrementing the pointer once per call always yields the correct root for whichever subtree is currently being built; building the left subtree completely before touching the right subtree matches the exact order pre-order values were laid down, so the shared pointer never gets misaligned.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Root from preorder splits the inorder array into left and right subtree ranges">
  <g font-family="sans-serif" font-size="12">
    <text x="10" y="20" fill="#e6edf3">preorder: [3, 9, 20, 15, 7]  (root is always next unused element)</text>
    <text x="10" y="45" fill="#e6edf3">inorder:  [9, 3, 15, 20, 7]</text>
    <rect x="10" y="55" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="25" y="71" fill="#e6edf3" text-anchor="middle">9</text>
    <rect x="45" y="55" width="30" height="24" fill="#161b22" stroke="#79c0ff"/><text x="60" y="71" fill="#e6edf3" text-anchor="middle">3</text>
    <rect x="80" y="55" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="95" y="71" fill="#e6edf3" text-anchor="middle">15</text>
    <rect x="115" y="55" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="130" y="71" fill="#e6edf3" text-anchor="middle">20</text>
    <rect x="150" y="55" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="165" y="71" fill="#e6edf3" text-anchor="middle">7</text>
    <text x="10" y="100" fill="#3fb950">left of 3 (green): [9] -&gt; left subtree</text>
    <text x="10" y="120" fill="#f85149">right of 3 (red): [15,20,7] -&gt; right subtree</text>
    <text x="10" y="150" fill="#e6edf3">Root = preorder[0] = 3. In inorder, 3 splits [9] | [15,20,7].</text>
    <text x="10" y="170" fill="#e6edf3">Next preorder value (9) becomes the left subtree's root; recursion continues.</text>
  </g>
</svg>

The root's position in `inorder` is the pivot that separates the left subtree's values from the right subtree's values.

## 5. Runnable example

```java
// ConstructBinaryTree.java
import java.util.*;

public class ConstructBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: same recursive idea, but re-scan the
    // inorder array with a linear search every time to find the root's
    // index, instead of a hash map. O(n^2) time worst case (n linear
    // scans, each up to O(n)), O(n) extra space for the recursion.
    static TreeNode bruteForce(int[] preorder, int[] inorder) {
        return buildSlow(preorder, new int[]{0}, inorder, 0, inorder.length - 1);
    }

    static TreeNode buildSlow(int[] preorder, int[] preorderIndex, int[] inorder, int left, int right) {
        if (left > right) return null;
        int rootVal = preorder[preorderIndex[0]++];
        TreeNode node = new TreeNode(rootVal);
        int mid = left;
        while (inorder[mid] != rootVal) mid++;
        node.left = buildSlow(preorder, preorderIndex, inorder, left, mid - 1);
        node.right = buildSlow(preorder, preorderIndex, inorder, mid + 1, right);
        return node;
    }

    // KEY INSIGHT: pre-building a value-to-index map for inorder turns
    // the "find the root's split point" step from an O(n) scan into an
    // O(1) lookup, without changing the recursive structure at all.

    // Level 2 -- Optimal: hash map for O(1) inorder index lookup.
    // O(n) time, O(n) space (the map plus the recursion stack).
    static int preorderIndex;
    static Map<Integer, Integer> inorderIndexOf;

    public static TreeNode buildTree(int[] preorder, int[] inorder) {
        preorderIndex = 0;
        inorderIndexOf = new HashMap<>();
        for (int i = 0; i < inorder.length; i++) inorderIndexOf.put(inorder[i], i);
        return build(preorder, 0, inorder.length - 1);
    }

    static TreeNode build(int[] preorder, int inorderLeft, int inorderRight) {
        if (inorderLeft > inorderRight) return null;
        int rootVal = preorder[preorderIndex++];
        TreeNode node = new TreeNode(rootVal);
        int mid = inorderIndexOf.get(rootVal);
        node.left = build(preorder, inorderLeft, mid - 1);
        node.right = build(preorder, mid + 1, inorderRight);
        return node;
    }

    // Level 3 -- Hardened: a single-node tree (`preorder = [1]`,
    // `inorder = [1]`) must build correctly, with both recursive calls
    // immediately hitting the `inorderLeft > inorderRight` base case.
    static TreeNode hardened(int[] preorder, int[] inorder) {
        return buildTree(preorder, inorder);
    }

    public static void main(String[] args) {
        int[] preorder = {3, 9, 20, 15, 7};
        int[] inorder = {9, 3, 15, 20, 7};

        TreeNode a = bruteForce(preorder, inorder);
        System.out.println(a.val + " " + a.left.val + " " + a.right.val);

        TreeNode b = buildTree(preorder, inorder);
        System.out.println(b.val + " " + b.right.left.val + " " + b.right.right.val);

        TreeNode c = hardened(new int[]{1}, new int[]{1});
        System.out.println(c.val);
    }
}
```

How to run: save as `ConstructBinaryTree.java`, then run `java ConstructBinaryTree.java`.

## 6. Walkthrough

Dry run of `build` on `preorder = [3,9,20,15,7]`, `inorder = [9,3,15,20,7]`:

| call | preorderIndex before | rootVal | mid in inorder | left range | right range |
|---|---|---|---|---|---|
| build(0, 4) | 0 | 3 | 1 | (0, 0) | (2, 4) |
| build(0, 0) | 1 | 9 | 0 | (0, -1) empty | (1, 0) empty |
| build(2, 4) | 2 | 20 | 3 | (2, 2) | (4, 4) |
| build(2, 2) | 3 | 15 | 2 | empty | empty |
| build(4, 4) | 4 | 7 | 4 | empty | empty |

Final tree: root `3`, left child `9`, right child `20` (whose children are `15` and `7`) — matching `[3,9,20,null,null,15,7]`. Time complexity: O(n), each node built once with an O(1) map lookup. Space complexity: O(n) for the map plus O(h) for the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: incrementing `preorderIndex` in the wrong place (for example, incrementing it separately for the left and right calls instead of exactly once per node, right when the root is read) desynchronizes the pointer from the actual pre-order sequence, since the shared index must advance by exactly one per node, in the exact order pre-order lists them.

- Building the left subtree completely before starting the right subtree is mandatory — it is precisely what keeps the single shared `preorderIndex` pointer aligned with the pre-order array's root-left-right order.
- Related problems: Maximum Binary Tree (also builds a tree recursively from an array, but the "root" is found by scanning for the maximum instead of reading it directly), Flatten Binary Tree to Linked List (restructures an existing tree into pre-order, the reverse direction of the idea used here).
