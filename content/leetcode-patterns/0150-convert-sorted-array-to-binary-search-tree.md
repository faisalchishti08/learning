---
card: leetcode-patterns
gi: 150
slug: convert-sorted-array-to-binary-search-tree
title: Convert Sorted Array to Binary Search Tree
---

## 1. What it is

Given an integer array `nums` sorted in ascending order, build a height-balanced binary search tree (BST) from it and return its root. Example: `nums = [-10,-3,0,5,9]` → a tree like `[0,-3,9,-10,null,5]` (any height-balanced arrangement matching the sorted order is accepted).

## 2. Why & when

A sorted array is already "in-order" for a BST — the challenge is picking which element becomes each subtree's root so the result stays balanced. Always picking the MIDDLE element of the current range as the root guarantees the left and right halves are as close in size as possible, which is exactly what height-balance requires. This belongs in Tree DFS as another "build a tree by recursing on sub-ranges" problem, alongside Maximum Binary Tree and Construct Binary Tree from Preorder and Inorder Traversal.

## 3. Core concept

**Key idea:** for the current range `[left, right]` of the sorted array, pick the middle index as the current node's value. Recurse on the left half for the left child, and the right half for the right child.

**Steps:**
1. Base case: if `left > right`, return `null`.
2. Compute `mid = left + (right - left) / 2`.
3. Create `node = new TreeNode(nums[mid])`.
4. Recurse: `node.left = build(nums, left, mid - 1)`.
5. Recurse: `node.right = build(nums, mid + 1, right)`.
6. Return `node`.

**Why it is correct:** because the array is already sorted, everything before `mid` is smaller (correctly forming the left subtree) and everything after `mid` is larger (correctly forming the right subtree), satisfying the BST property automatically; picking the true middle at every level keeps the two halves within one element of each other in size at every recursive step, which is what keeps the resulting tree height-balanced.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The middle of each range becomes the root, splitting into two roughly equal halves">
  <g font-family="sans-serif" font-size="12">
    <text x="10" y="20" fill="#e6edf3">nums: [-10, -3, 0, 5, 9]  (indices 0..4, mid = 2)</text>
    <rect x="10" y="30" width="40" height="24" fill="#161b22" stroke="#3fb950"/><text x="30" y="46" fill="#e6edf3" text-anchor="middle" font-size="10">-10</text>
    <rect x="50" y="30" width="40" height="24" fill="#161b22" stroke="#3fb950"/><text x="70" y="46" fill="#e6edf3" text-anchor="middle" font-size="10">-3</text>
    <rect x="90" y="30" width="40" height="24" fill="#161b22" stroke="#f85149"/><text x="110" y="46" fill="#e6edf3" text-anchor="middle" font-size="10">0</text>
    <rect x="130" y="30" width="40" height="24" fill="#161b22" stroke="#79c0ff"/><text x="150" y="46" fill="#e6edf3" text-anchor="middle" font-size="10">5</text>
    <rect x="170" y="30" width="40" height="24" fill="#161b22" stroke="#79c0ff"/><text x="190" y="46" fill="#e6edf3" text-anchor="middle" font-size="10">9</text>
    <text x="10" y="75" fill="#3fb950">left range [-10,-3] (2 elements)</text>
    <text x="10" y="95" fill="#f85149">root = 0 (middle, index 2)</text>
    <text x="10" y="115" fill="#79c0ff">right range [5,9] (2 elements)</text>
    <text x="10" y="150" fill="#e6edf3">Both halves have 2 elements -- perfectly balanced split at every level</text>
  </g>
</svg>

Choosing the middle index (`0`, red) splits the remaining elements into two halves of equal (or near-equal) size.

## 5. Runnable example

```java
// ConvertSortedArrayToBST.java
public class ConvertSortedArrayToBST {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: same midpoint idea, but rebuild a new
    // sub-array (via Arrays.copyOfRange) at every recursive call
    // instead of passing index bounds into the original array.
    // O(n log n) time and O(n log n) extra space overall, since each
    // level copies roughly half the remaining elements.
    static TreeNode bruteForce(int[] nums) {
        if (nums.length == 0) return null;
        int mid = nums.length / 2;
        TreeNode node = new TreeNode(nums[mid]);
        node.left = bruteForce(java.util.Arrays.copyOfRange(nums, 0, mid));
        node.right = bruteForce(java.util.Arrays.copyOfRange(nums, mid + 1, nums.length));
        return node;
    }

    // KEY INSIGHT: passing (left, right) index bounds into the SAME
    // original array, instead of copying sub-arrays, builds the same
    // tree with no extra array allocation at any level.

    // Level 2 -- Optimal: recursive build with index bounds, choosing
    // the midpoint. O(n) time (each element visited once), O(log n)
    // space for the recursion stack on a balanced result.
    public static TreeNode sortedArrayToBST(int[] nums) {
        return build(nums, 0, nums.length - 1);
    }

    static TreeNode build(int[] nums, int left, int right) {
        if (left > right) return null;
        int mid = left + (right - left) / 2;
        TreeNode node = new TreeNode(nums[mid]);
        node.left = build(nums, left, mid - 1);
        node.right = build(nums, mid + 1, right);
        return node;
    }

    // Level 3 -- Hardened: a single-element array must build one node
    // with no children, and an even-length array must still produce a
    // height-balanced tree regardless of which of the two valid
    // "middle" indices is picked.
    static TreeNode hardened(int[] nums) {
        return sortedArrayToBST(nums);
    }

    public static void main(String[] args) {
        int[] nums = {-10, -3, 0, 5, 9};

        TreeNode a = bruteForce(nums);
        System.out.println(a.val + " " + a.left.val + " " + a.right.val);

        TreeNode b = sortedArrayToBST(nums);
        System.out.println(b.val + " " + b.left.right.val + " " + b.right.right.val);

        TreeNode c = hardened(new int[]{7});
        System.out.println(c.val);
    }
}
```

How to run: save as `ConvertSortedArrayToBST.java`, then run `java ConvertSortedArrayToBST.java`.

## 6. Walkthrough

Dry run of `build` on `nums = [-10,-3,0,5,9]`, indices `0..4`:

| call range | mid | rootVal | left recurse | right recurse |
|---|---|---|---|---|
| build(0, 4) | 2 | 0 | build(0, 1) | build(3, 4) |
| build(0, 1) | 0 | -10 | build(0, -1) empty | build(1, 1) |
| build(3, 4) | 3 | 5 | build(3, 2) empty | build(4, 4) |
| build(1, 1) | 1 | -3 | empty | empty |
| build(4, 4) | 4 | 9 | empty | empty |

Final tree: root `0`, left subtree rooted at `-10` (with right child `-3`), right subtree rooted at `5` (with right child `9`) — height-balanced, height `3`. Time complexity: O(n), each array element becomes exactly one node. Space complexity: O(log n) for the recursion stack, since the result is guaranteed balanced (height O(log n)).

## 7. Gotchas & takeaways

> Gotcha: computing `mid = (left + right) / 2` directly can overflow for very large index values in other languages; `mid = left + (right - left) / 2` avoids that overflow risk and is a good habit even where Java's `int` range makes it unlikely to matter for typical array sizes.

- When the current range has an even number of elements, either of the two central indices works as a valid "middle" — both produce a height-balanced tree, just a slightly different (still valid) shape.
- Related problems: Maximum Binary Tree (the same recurse-on-sub-ranges shape, but the split point is the range's maximum instead of its middle), Validate Binary Search Tree (a good check to run on the output, confirming the built tree really does satisfy BST ordering).
