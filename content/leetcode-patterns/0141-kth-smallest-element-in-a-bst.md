---
card: leetcode-patterns
gi: 141
slug: kth-smallest-element-in-a-bst
title: Kth Smallest Element in a BST
---

## 1. What it is

Given the `root` of a binary search tree (BST) and an integer `k`, return the `k`th smallest value in the tree (`k` is 1-indexed, so `k = 1` means the smallest value). Example: `root = [5,3,6,2,4,null,null,1]`, `k = 3` → `3`.

## 2. Why & when

A BST's in-order traversal (left, node, right) visits every value in strictly increasing sorted order. That single fact turns this problem into "run in-order DFS, and stop as soon as a counter reaches `k`." It belongs in this section because in-order is one of the three named DFS orders, and this problem is the canonical reason that order exists: it is the only order that walks a BST in sorted order.

## 3. Core concept

**Key idea:** perform an in-order traversal (recurse left, visit node, recurse right). Keep a counter that increments every time a node is "visited" (in the middle step). The `k`th node visited is the answer — stop as soon as the counter reaches `k`, without wasting time visiting the remaining nodes.

**Steps:**
1. Keep a counter starting at `0` and a `result` variable.
2. Define `inorder(node)`: base case, if `node == null` or the answer is already found, return immediately.
3. Recurse left: `inorder(node.left)`.
4. Visit: increment the counter; if the counter now equals `k`, record `result = node.val` and stop further recursion.
5. Recurse right: `inorder(node.right)` (only if the answer has not been found yet).

**Why it is correct:** the BST property guarantees every value in `node.left`'s subtree is smaller than `node.val`, and every value in `node.right`'s subtree is larger, so visiting left-node-right at every level produces the global sorted order; the counter therefore ticks up exactly in ascending rank, and it hits `k` exactly at the `k`th smallest value.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="In-order traversal visits a BST in sorted order">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="15" fill="#161b22" stroke="#79c0ff"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="160" cy="80" r="15" fill="#161b22" stroke="#79c0ff"/><text x="160" y="84" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="300" cy="80" r="15" fill="#161b22" stroke="#79c0ff"/><text x="300" y="84" fill="#e6edf3" text-anchor="middle">6</text>
    <circle cx="120" cy="130" r="15" fill="#161b22" stroke="#3fb950"/><text x="120" y="134" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="200" cy="130" r="15" fill="#161b22" stroke="#79c0ff"/><text x="200" y="134" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="100" cy="175" r="12" fill="#161b22" stroke="#3fb950"/><text x="100" y="179" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <line x1="222" y1="43" x2="168" y2="68" stroke="#8b949e"/>
    <line x1="238" y1="43" x2="292" y2="68" stroke="#8b949e"/>
    <line x1="152" y1="93" x2="128" y2="118" stroke="#8b949e"/>
    <line x1="168" y1="93" x2="192" y2="118" stroke="#8b949e"/>
    <line x1="114" y1="142" x2="103" y2="163" stroke="#8b949e"/>
    <text x="10" y="15" fill="#e6edf3">In-order visit sequence: 1, 2, 3, 4, 5, 6 -- 3rd visited (green so far) is 3</text>
  </g>
</svg>

In-order traversal (`1, 2, 3, 4, 5, 6`) matches the sorted order of all values, so the 3rd value visited is the 3rd smallest, `3`.

## 5. Runnable example

```java
// KthSmallestElementInBST.java
import java.util.*;

public class KthSmallestElementInBST {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: in-order traversal collects every value
    // into a list, then index into it at position k - 1. O(n) time,
    // O(n) EXTRA space for the full list, even though only one value
    // from it is actually needed.
    static int bruteForce(TreeNode root, int k) {
        List<Integer> values = new ArrayList<>();
        inorderCollect(root, values);
        return values.get(k - 1);
    }

    static void inorderCollect(TreeNode node, List<Integer> values) {
        if (node == null) return;
        inorderCollect(node.left, values);
        values.add(node.val);
        inorderCollect(node.right, values);
    }

    // KEY INSIGHT: you do not need the full sorted list -- a counter
    // that increments during in-order traversal reaches k at exactly
    // the k-th smallest node, so the recursion can stop right there.

    // Level 2 -- Optimal: in-order DFS with an early-stopping counter.
    // O(h + k) time (visits at most k nodes plus the left spine down to
    // the first one), O(h) space (recursion stack).
    static int count = 0;
    static int result = -1;

    public static int kthSmallest(TreeNode root, int k) {
        count = 0;
        result = -1;
        inorder(root, k);
        return result;
    }

    static void inorder(TreeNode node, int k) {
        if (node == null || count >= k) return;
        inorder(node.left, k);
        if (count >= k) return;
        count++;
        if (count == k) { result = node.val; return; }
        inorder(node.right, k);
    }

    // Level 3 -- Hardened: k equal to the total number of nodes must
    // return the maximum value in the tree, the last one visited.
    static int hardened(TreeNode root, int k) {
        return kthSmallest(root, k);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(5,
            new TreeNode(3, new TreeNode(2, new TreeNode(1), null), new TreeNode(4)),
            new TreeNode(6));

        System.out.println(bruteForce(root, 3));
        System.out.println(kthSmallest(root, 3));
        System.out.println(hardened(root, 5));
    }
}
```

How to run: save as `KthSmallestElementInBST.java`, then run `java KthSmallestElementInBST.java`.

## 6. Walkthrough

Dry run of `inorder` on `[5,3,6,2,4,null,null,1]` with `k = 3`:

| step | node visited | count after | action |
|---|---|---|---|
| 1 | 1 | 1 | not k yet, continue |
| 2 | 2 | 2 | not k yet, continue |
| 3 | 3 | 3 | count == k -> `result = 3`, stop |

The recursion never visits `4`, `5`, or `6`, since it stops the moment `count == k`. Time complexity: O(h + k) — descend to the leftmost node (O(h)) then visit up to `k` nodes in order. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: forgetting to check `count >= k` before recursing into `node.right` (or at the very top of the function) means the traversal keeps visiting nodes even after the answer is already found, wasting work — though it still produces the correct `result` since it is never overwritten after being set once.

- This early-stopping in-order pattern is only fast (O(h + k)) because of the BST property; running the same traversal on a plain (non-BST) binary tree would visit nodes in an order unrelated to their sorted rank.
- Related problems: Validate Binary Search Tree (relies on the same sorted in-order property, checked via bounds instead of read via traversal), Binary Search Tree Iterator (turns this same in-order walk into a resumable, step-by-step iterator instead of one batch call).
