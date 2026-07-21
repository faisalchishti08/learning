---
card: leetcode-patterns
gi: 147
slug: maximum-binary-tree
title: Maximum Binary Tree
---

## 1. What it is

Given an integer array `nums` with no duplicates, build a "maximum binary tree" recursively: the root is the maximum value in `nums`; its left subtree is built (the same way) from the elements to the left of that maximum; its right subtree is built from the elements to its right. Return the root. Example: `nums = [3,2,1,6,0,5]` → `[6,3,5,null,2,0,null,null,1]` (root is `6`, the array's maximum).

## 2. Why & when

This is a pre-order Tree DFS in reverse: instead of walking an existing tree, you are BUILDING one, and the shape naturally comes out pre-order (root decided first, then the left range is fully built, then the right range). It belongs in this section alongside Construct Binary Tree from Preorder and Inorder Traversal, since both problems build a tree top-down from array information, recursing on sub-ranges.

## 3. Core concept

**Key idea:** for the current range `[left, right]` of `nums`, find the index of its maximum value — that becomes the current node. Recurse on the sub-range strictly to the left of that index for the left child, and the sub-range strictly to the right for the right child.

**Steps:**
1. Base case: if `left > right`, return `null` (an empty range has no tree).
2. Find `maxIndex`, the index of the largest value in `nums[left..right]`.
3. Create `node = new TreeNode(nums[maxIndex])`.
4. Recurse: `node.left = build(nums, left, maxIndex - 1)`.
5. Recurse: `node.right = build(nums, maxIndex + 1, right)`.
6. Return `node`.

**Why it is correct:** the problem's definition of "maximum binary tree" is exactly this recursive rule — the maximum of a range is always the root of that range's subtree, and everything left of it (in array order) forms the left subtree, everything right of it forms the right subtree — so directly implementing the definition produces the correct tree.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The maximum of the current range becomes the root; it splits the range into two sub-ranges">
  <g font-family="sans-serif" font-size="12">
    <text x="10" y="20" fill="#e6edf3">nums: [3, 2, 1, 6, 0, 5]  (indices 0..5)</text>
    <rect x="10" y="30" width="26" height="24" fill="#161b22" stroke="#3fb950"/><text x="23" y="46" fill="#e6edf3" text-anchor="middle">3</text>
    <rect x="40" y="30" width="26" height="24" fill="#161b22" stroke="#3fb950"/><text x="53" y="46" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="70" y="30" width="26" height="24" fill="#161b22" stroke="#3fb950"/><text x="83" y="46" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="100" y="30" width="26" height="24" fill="#161b22" stroke="#f85149"/><text x="113" y="46" fill="#e6edf3" text-anchor="middle">6</text>
    <rect x="130" y="30" width="26" height="24" fill="#161b22" stroke="#79c0ff"/><text x="143" y="46" fill="#e6edf3" text-anchor="middle">0</text>
    <rect x="160" y="30" width="26" height="24" fill="#161b22" stroke="#79c0ff"/><text x="173" y="46" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="10" y="75" fill="#3fb950">left range [3,2,1] -&gt; recurse, max is 3</text>
    <text x="10" y="95" fill="#f85149">root = 6 (max of whole array, index 3)</text>
    <text x="10" y="115" fill="#79c0ff">right range [0,5] -&gt; recurse, max is 5</text>
    <text x="10" y="150" fill="#e6edf3">Result: root 6, left child 3 (from [3,2,1]), right child 5 (from [0,5])</text>
  </g>
</svg>

The maximum (`6`, red) splits the array into a left range and a right range, each recursively built the same way.

## 5. Runnable example

```java
// MaximumBinaryTree.java
public class MaximumBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: same recursive shape, but rebuild a new
    // sub-array (via Arrays.copyOfRange) for every recursive call
    // instead of passing index bounds into the original array.
    // O(n^2) time and space worst case (a sorted array causes maximum
    // recursion depth, and each level copies an almost-full array).
    static TreeNode bruteForce(int[] nums) {
        if (nums.length == 0) return null;
        int maxIndex = 0;
        for (int i = 1; i < nums.length; i++) if (nums[i] > nums[maxIndex]) maxIndex = i;
        TreeNode node = new TreeNode(nums[maxIndex]);
        node.left = bruteForce(java.util.Arrays.copyOfRange(nums, 0, maxIndex));
        node.right = bruteForce(java.util.Arrays.copyOfRange(nums, maxIndex + 1, nums.length));
        return node;
    }

    // KEY INSIGHT: passing (left, right) index bounds into the SAME
    // original array avoids copying any sub-array at all -- the
    // recursion just narrows which indices it looks at.

    // Level 2 -- Optimal: recursive build with index bounds, no copying.
    // O(n^2) time worst case (finding the max in a range still costs
    // O(range length), and a sorted input gives n nested ranges), O(n)
    // space for the recursion stack in the worst case.
    public static TreeNode constructMaximumBinaryTree(int[] nums) {
        return build(nums, 0, nums.length - 1);
    }

    static TreeNode build(int[] nums, int left, int right) {
        if (left > right) return null;
        int maxIndex = left;
        for (int i = left + 1; i <= right; i++) if (nums[i] > nums[maxIndex]) maxIndex = i;
        TreeNode node = new TreeNode(nums[maxIndex]);
        node.left = build(nums, left, maxIndex - 1);
        node.right = build(nums, maxIndex + 1, right);
        return node;
    }

    // Level 3 -- Hardened: a single-element array must build a single
    // node with no children, and the global maximum (wherever it sits)
    // must always end up as the root of the whole tree.
    static TreeNode hardened(int[] nums) {
        return constructMaximumBinaryTree(nums);
    }

    public static void main(String[] args) {
        int[] nums = {3, 2, 1, 6, 0, 5};

        TreeNode a = bruteForce(nums);
        System.out.println(a.val + " " + a.left.val + " " + a.right.val);

        TreeNode b = constructMaximumBinaryTree(nums);
        System.out.println(b.val + " " + b.left.val + " " + b.right.val);

        TreeNode c = hardened(new int[]{5});
        System.out.println(c.val);
    }
}
```

How to run: save as `MaximumBinaryTree.java`, then run `java MaximumBinaryTree.java`.

## 6. Walkthrough

Dry run of `build` on `nums = [3,2,1,6,0,5]`, indices `0..5`:

| call range | maxIndex | rootVal | left recurse | right recurse |
|---|---|---|---|---|
| build(0, 5) | 3 | 6 | build(0, 2) | build(4, 5) |
| build(0, 2) | 0 | 3 | build(0, -1) empty | build(1, 2) |
| build(4, 5) | 5 | 5 | build(4, 3) empty | build(6, 5) empty |
| build(1, 2) | 1 | 2 | build(1, 0) empty | build(2, 2) |
| build(2, 2) | 2 | 1 | empty | empty |

Final tree root is `6`, left child `3` (whose own right child is `2`, whose own right child is `1`), right child `5`. Time complexity: O(n^2) worst case — each call scans its range for the max, and a sorted array produces `n` nested calls each scanning O(n). Space complexity: O(n) worst case for the recursion stack on a sorted (fully skewed) input.

## 7. Gotchas & takeaways

> Gotcha: assuming this runs in O(n) time is a common mistake — finding the maximum in a range costs O(range length), and for an already-sorted (or reverse-sorted) input array, every recursive call's range only shrinks by one element, giving O(n^2) total work in the worst case. A monotonic-stack approach can achieve true O(n), but the direct recursive version shown here is what most interviews expect first.

- Passing index bounds `(left, right)` into the original array (instead of allocating a new sub-array per call) is a general technique that turns an O(n) copy per level into O(1) extra bookkeeping per level.
- Related problems: Construct Binary Tree from Preorder and Inorder Traversal (a different rule for finding the root, but the same recurse-on-sub-ranges shape), Maximum Depth of Binary Tree (a good sanity check to run on the built tree, since a skewed input produces a skewed, deep tree).
