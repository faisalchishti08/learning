---
card: leetcode-patterns
gi: 146
slug: sum-root-to-leaf-numbers
title: Sum Root to Leaf Numbers
---

## 1. What it is

Given the `root` of a binary tree where each node holds a single digit (`0`-`9`), each root-to-leaf path represents a number formed by concatenating its digits in order. Return the sum of all these numbers across every root-to-leaf path. Example: `root = [1,2,3]` → `25` (path `1->2` forms `12`, path `1->3` forms `13`; `12 + 13 = 25`).

## 2. Why & when

This is the numeric twin of Binary Tree Paths: instead of building a string down the recursion, you build a running integer using the standard "shift left, add next digit" trick (`number * 10 + digit`). It belongs in this section because the accumulated value is only a valid, complete number once a leaf is reached — exactly the pre-order "carry state down, finalize at a leaf" shape.

## 3. Core concept

**Key idea:** carry a `numberSoFar` value down the recursion, updating it at each node as `numberSoFar * 10 + node.val`. When a leaf is reached, `numberSoFar` is a complete root-to-leaf number — add it to a running total.

**Steps:**
1. Base case: if `node == null`, return `0` (contributes nothing to the sum).
2. Update: `numberSoFar = numberSoFar * 10 + node.val`.
3. Base case: if `node` is a leaf, return `numberSoFar` (this path's complete number).
4. Recurse: return `dfs(node.left, numberSoFar) + dfs(node.right, numberSoFar)` (each branch's leaf contributions sum together).

**Why it is correct:** multiplying by `10` before adding the next digit is exactly how positional numbers are built left to right (the same trick used to parse a string of digits into an integer), so `numberSoFar` at any node always equals the number formed by every digit from the root down to that node, in order.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="numberSoFar shifts left and adds the next digit at each step">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="15" fill="#161b22" stroke="#3fb950"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="250" y="20" fill="#3fb950" font-size="10">num=1</text>
    <circle cx="170" cy="85" r="15" fill="#161b22" stroke="#3fb950"/><text x="170" y="89" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="90" y="80" fill="#3fb950" font-size="10">num=1*10+2=12</text>
    <circle cx="290" cy="85" r="15" fill="#161b22" stroke="#79c0ff"/><text x="290" y="89" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="300" y="105" fill="#8b949e" font-size="10">num=1*10+3=13</text>
    <line x1="221" y1="43" x2="179" y2="72" stroke="#3fb950" stroke-width="2"/>
    <line x1="239" y1="43" x2="281" y2="72" stroke="#8b949e"/>
    <text x="10" y="175" fill="#e6edf3">Leaf 2 contributes 12; leaf 3 contributes 13; total sum = 12 + 13 = 25</text>
  </g>
</svg>

Each digit shifts the running number left by one place (multiply by 10) before the next digit is added.

## 5. Runnable example

```java
// SumRootToLeafNumbers.java
public class SumRootToLeafNumbers {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: build each root-to-leaf path as a STRING
    // of digits first, then parse it into an integer and add it to the
    // sum. O(n) time but pays for string building and parsing overhead
    // that the direct arithmetic trick avoids entirely.
    static int bruteForce(TreeNode root) {
        return sumFromStrings(root, "");
    }

    static int sumFromStrings(TreeNode node, String digitsSoFar) {
        if (node == null) return 0;
        String newDigits = digitsSoFar + node.val;
        if (node.left == null && node.right == null) return Integer.parseInt(newDigits);
        return sumFromStrings(node.left, newDigits) + sumFromStrings(node.right, newDigits);
    }

    // KEY INSIGHT: "multiply by 10, then add the next digit" builds the
    // same number as string concatenation would, directly as an
    // integer -- no string allocation or parsing needed at any step.

    // Level 2 -- Optimal: pre-order DFS with numberSoFar = numberSoFar * 10 + digit.
    // O(n) time, O(h) space (recursion stack).
    public static int sumNumbers(TreeNode root) {
        return dfs(root, 0);
    }

    static int dfs(TreeNode node, int numberSoFar) {
        if (node == null) return 0;
        numberSoFar = numberSoFar * 10 + node.val;
        if (node.left == null && node.right == null) return numberSoFar;
        return dfs(node.left, numberSoFar) + dfs(node.right, numberSoFar);
    }

    // Level 3 -- Hardened: a single-node tree must return that node's
    // own digit value as the complete number, with no multiplication
    // needed beyond the base 0 * 10 + digit = digit.
    static int hardened(TreeNode root) {
        return sumNumbers(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1, new TreeNode(2), new TreeNode(3));

        System.out.println(bruteForce(root));
        System.out.println(sumNumbers(root));
        System.out.println(hardened(new TreeNode(7)));
    }
}
```

How to run: save as `SumRootToLeafNumbers.java`, then run `java SumRootToLeafNumbers.java`.

## 6. Walkthrough

Dry run of `dfs` on `[1,2,3]`:

| call | numberSoFar in | numberSoFar after update | is leaf? | returns |
|---|---|---|---|---|
| dfs(1, 0) | 0 | `0*10+1=1` | no | recurse left and right |
| dfs(2, 1) | 1 | `1*10+2=12` | yes | 12 |
| dfs(3, 1) | 1 | `1*10+3=13` | yes | 13 |

`dfs(1, 0)` returns `12 + 13 = 25`. Time complexity: O(n) total, one visit per node with O(1) arithmetic each. Space complexity: O(h), the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: for very deep trees (many more than the 10 digits an `int` can safely hold), `numberSoFar * 10 + node.val` can overflow a 32-bit `int` — the actual LeetCode constraints cap tree depth to keep numbers within `int` range, but a general-purpose version of this function should use `long` for safety.

- This exact `value * 10 + digit` accumulation pattern also appears outside trees, anywhere a sequence of digits needs to become a number incrementally (parsing a string, reading digits from a stream) — recognizing it saves reinventing string-to-int conversion by hand.
- Related problems: Binary Tree Paths (the same accumulate-down-the-recursion shape, producing a formatted string instead of a numeric total), Path Sum (accumulates a REMAINING target instead of a growing number, subtracting rather than shifting-and-adding).
