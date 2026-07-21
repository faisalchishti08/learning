---
card: leetcode-patterns
gi: 144
slug: house-robber-iii
title: House Robber III
---

## 1. What it is

The houses in a neighborhood form a binary tree; robbing a node steals its value but forbids robbing its direct parent or its direct children on the same night. Given the `root` of this tree, return the maximum total amount you can rob without robbing two directly connected nodes. Example: `root = [3,4,5,1,3,null,1]` → `9` (skip the root, rob its two children `4` and `5` instead — they are not directly connected to each other, and `4 + 5 = 9` beats any combination that includes the root).

## 2. Why & when

The naive recursion ("rob this node or don't") recomputes the same subtree's answer multiple times, since "don't rob this node" needs to know the best answer for skipping it, and "rob this node" needs the best answer assuming its children are also skipped. The efficient version has each node return BOTH numbers at once — the best result if it is robbed, and the best result if it is not — so a parent can combine them without recomputation. This is a post-order Tree DFS: a node cannot compute its own pair of answers until both children have already returned their pairs.

## 3. Core concept

**Key idea:** each recursive call returns a pair `(robbedHere, notRobbedHere)`. `robbedHere` = this node's value plus BOTH children's `notRobbedHere` (since robbing this node forbids robbing either child). `notRobbedHere` = the sum of, for each child independently, whichever of that child's two values is larger (since skipping this node frees each child to be robbed or not, whichever is better).

**Steps:**
1. Base case: if `node == null`, return `(0, 0)`.
2. Recurse: `left = robHelper(node.left)`, `right = robHelper(node.right)`.
3. Combine "robbed": `robbedHere = node.val + left.notRobbed + right.notRobbed`.
4. Combine "not robbed": `notRobbedHere = max(left.robbed, left.notRobbed) + max(right.robbed, right.notRobbed)`.
5. Return `(robbedHere, notRobbedHere)`.
6. The final answer is `max(robHelper(root).robbed, robHelper(root).notRobbed)`.

**Why it is correct:** the pair captures every choice a parent might need — "assume I forced you to be skipped" (`notRobbed`) and "here's your best regardless" implicitly available as `max(robbed, notRobbed)` — so no case is ever left uncomputed, and no subtree's answer is ever recomputed from scratch.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each node returns a pair: best if robbed, best if not robbed">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="16" fill="#161b22" stroke="#79c0ff"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="160" cy="85" r="16" fill="#161b22" stroke="#3fb950"/><text x="160" y="89" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="60" y="95" fill="#3fb950" font-size="10">leaf: (robbed=4, notRobbed=0)</text>
    <circle cx="300" cy="85" r="16" fill="#161b22" stroke="#79c0ff"/><text x="300" y="89" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="290" y="105" fill="#8b949e" font-size="10">leaf: (robbed=5, notRobbed=0)</text>
    <line x1="221" y1="44" x2="169" y2="72" stroke="#8b949e"/>
    <line x1="239" y1="44" x2="291" y2="72" stroke="#8b949e"/>
    <text x="10" y="175" fill="#e6edf3">Root robbed = 3 + 0 + 0 = 3. Root not robbed = max(4,0) + max(5,0) = 4 + 5 = 9. Best is 9.</text>
  </g>
</svg>

Each node's pair lets its parent pick whichever option (robbed or not) is larger, independently per child.

## 5. Runnable example

```java
// HouseRobberIII.java
public class HouseRobberIII {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: at every node, try both "rob it" (skip
    // both children entirely) and "don't rob it" (recurse normally into
    // both children), recomputing subtree results repeatedly.
    // O(2^n) time worst case, since the same subtree's best value can
    // be recomputed many times across different call paths.
    static int bruteForce(TreeNode node) {
        if (node == null) return 0;
        int robThis = node.val;
        if (node.left != null) robThis += bruteForce(node.left.left) + bruteForce(node.left.right);
        if (node.right != null) robThis += bruteForce(node.right.left) + bruteForce(node.right.right);
        int skipThis = bruteForce(node.left) + bruteForce(node.right);
        return Math.max(robThis, skipThis);
    }

    // KEY INSIGHT: returning BOTH "robbed" and "not robbed" totals from
    // every call, in one pass, gives the parent everything it needs
    // without ever recomputing the same subtree's answer twice.

    // Level 2 -- Optimal: post-order DFS returning a (robbed, notRobbed)
    // pair. O(n) time, O(h) space (recursion stack).
    static class Result {
        int robbed, notRobbed;
        Result(int robbed, int notRobbed) { this.robbed = robbed; this.notRobbed = notRobbed; }
    }

    public static int rob(TreeNode root) {
        Result result = robHelper(root);
        return Math.max(result.robbed, result.notRobbed);
    }

    static Result robHelper(TreeNode node) {
        if (node == null) return new Result(0, 0);
        Result left = robHelper(node.left);
        Result right = robHelper(node.right);
        int robbedHere = node.val + left.notRobbed + right.notRobbed;
        int notRobbedHere = Math.max(left.robbed, left.notRobbed) + Math.max(right.robbed, right.notRobbed);
        return new Result(robbedHere, notRobbedHere);
    }

    // Level 3 -- Hardened: a single-node tree must return that node's
    // own value (robbing the only house), and a tree with two levels
    // must correctly prefer robbing the grandchildren over the middle
    // level when that yields more.
    static int hardened(TreeNode root) {
        return rob(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(3,
            new TreeNode(2, null, new TreeNode(3)),
            new TreeNode(3, null, new TreeNode(1)));

        System.out.println(bruteForce(root));
        System.out.println(rob(root));
        System.out.println(hardened(new TreeNode(5)));
    }
}
```

How to run: save as `HouseRobberIII.java`, then run `java HouseRobberIII.java`.

## 6. Walkthrough

Dry run of `robHelper` on `root = [3,2,3,null,3,null,1]` (`3` has children `2` and `3`; `2` has right child `3`; the other `3` has right child `1`):

| call | robbedHere | notRobbedHere |
|---|---|---|
| robHelper(3, deep leaf under left `2`) | 3 | 0 |
| robHelper(2) | `2 + 0 + 0 = 2` | `max(0,0) + max(3,0) = 3` |
| robHelper(1, deep leaf under right `3`) | 1 | 0 |
| robHelper(3, right branch) | `3 + 0 + 0 = 3` | `max(0,0) + max(1,0) = 1` |
| robHelper(root=3) | `3 + 3 + 1 = 7` | `max(2,3) + max(3,1) = 3 + 3 = 6` |

Final answer: `max(7, 6) = 7` — robbing the root plus its two deep grandchildren (`3` and `1`) beats every other combination. Time complexity: O(n), every node visited once. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: computing `notRobbedHere` as `left.notRobbed + right.notRobbed` (forcing both children to also be skipped) is wrong — skipping the current node only means it CANNOT be robbed, not that its children must also be skipped; each child should independently pick its own better option via `max(child.robbed, child.notRobbed)`.

- This pair-returning technique — computing two mutually exclusive outcomes at every node instead of one — is the tree-shaped version of the classic House Robber array DP, adapted from a linear "previous two" state to a "per-child pair" state.
- Related problems: Diameter of Binary Tree (a different two-value combine: a node's own best depth versus the best diameter seen anywhere below it), Balanced Binary Tree (also returns extra information beyond a single number to avoid recomputation).
