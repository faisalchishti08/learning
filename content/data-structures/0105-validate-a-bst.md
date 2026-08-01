---
card: data-structures
gi: 105
slug: validate-a-bst
title: Validate a BST
---

## 1. What it is

**Validating a BST** means checking whether a given binary tree actually satisfies the BST invariant everywhere — every node's entire left subtree smaller, entire right subtree larger — not just checking a node against its immediate children. It is a named, frequently asked problem, precisely because the naive "obvious" solution is subtly wrong.

## 2. Why & when

This tests whether you truly understand the BST invariant (see [Binary tree & binary search tree (BST)](0098-binary-tree-binary-search-tree-bst.md)) applies to entire subtrees, not just parent-child pairs. It comes up directly as an interview problem, and the underlying technique — passing a valid range down through recursion — is a reusable pattern for any "constraint must hold transitively down the tree" problem.

## 3. Core concept

**Key idea in one sentence.** Each recursive call must know the valid `(min, max)` range its current node is allowed to fall in, established by *all* of its ancestors so far — not just its immediate parent.

**Level 1 — the tempting but wrong approach: check only the immediate parent.** `isValid(node)` that only checks `node.left.value < node.value < node.right.value` locally, recursing without passing any range down, will incorrectly accept invalid trees — for example, a right child's *left* grandchild that is smaller than the original root, but happens to be larger than its own immediate parent, would pass this local check while violating the actual BST invariant.

**KEY INSIGHT.** The valid range for a node must be threaded down through the recursion from the root — going left tightens the *upper* bound (everything below must stay less than the parent), going right tightens the *lower* bound (everything below must stay greater than the parent). A single node passing its own local check is not enough; it must also satisfy every bound accumulated from every ancestor above it.

**Level 2 — the optimal, correct approach: pass a range.** `isValid(node, min, max)` — check `min < node.value < max`; recurse left with `isValid(node.left, min, node.value)` (tightening the upper bound to the current node's value); recurse right with `isValid(node.right, node.value, max)` (tightening the lower bound). Start the top call with `(-infinity, +infinity)`.

**Level 3 — hardened.** Handle duplicate values correctly (decide up front whether `==` is allowed on one side — this implementation treats the range as exclusive on both ends, rejecting duplicates entirely, which matches the standard "strict BST" definition used in most problem statements), and confirm an empty tree (`null`) is trivially valid.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A tree where root is 10, right child is 15, and 15's left child is 6, which violates the BST invariant against the root even though it satisfies the local check against its immediate parent 15">
  <g font-family="sans-serif" font-size="11">
    <circle cx="250" cy="30" r="18" fill="#161b22" stroke="#8b949e"/><text x="250" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <circle cx="350" cy="90" r="18" fill="#161b22" stroke="#8b949e"/><text x="350" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">15</text>
    <circle cx="300" cy="150" r="18" fill="#0d1117" stroke="#f0883e"/><text x="300" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">6</text>
    <line x1="262" y1="42" x2="338" y2="78" stroke="#8b949e"/>
    <line x1="338" y1="102" x2="312" y2="138" stroke="#8b949e"/>
    <text x="440" y="90" fill="#79c0ff" font-size="10">local check: 6 &lt; 15 (parent) -&gt; PASSES</text>
    <text x="440" y="110" fill="#f0883e" font-size="10">real check: 6 must be &gt; 10 (root),</text>
    <text x="440" y="125" fill="#f0883e" font-size="10">since it is in root's RIGHT subtree</text>
    <text x="440" y="140" fill="#f0883e" font-size="10">-&gt; 6 &gt; 10 is FALSE -&gt; invalid BST</text>
  </g>
</svg>

Node `6` satisfies a local check against its immediate parent `15`, but violates the accumulated range from the root: everything in `10`'s right subtree must be `> 10`, and `6` is not.

## 5. Runnable example

```java
// ValidateBst.java
public class ValidateBst {

    static class TreeNode {
        int value;
        TreeNode left, right;
        TreeNode(int value) { this.value = value; }
        TreeNode(int value, TreeNode left, TreeNode right) { this.value = value; this.left = left; this.right = right; }
    }

    // Level 1: the WRONG approach -- only checks the immediate parent, misses violations further down.
    static boolean isValidLocalOnly(TreeNode node) {
        if (node == null) return true;
        if (node.left != null && node.left.value >= node.value) return false;
        if (node.right != null && node.right.value <= node.value) return false;
        return isValidLocalOnly(node.left) && isValidLocalOnly(node.right);
    }

    static void basicLevel() {
        // 10 -> right child 15 -> left child 6 (violates the root's constraint, but not its immediate parent's)
        TreeNode invalidTree = new TreeNode(10, null, new TreeNode(15, new TreeNode(6), null));
        System.out.println("basic: local-only check on the flawed tree (INCORRECTLY passes) -> " + isValidLocalOnly(invalidTree));
    }

    // Level 2: optimal -- pass a valid (min, max) range down through the recursion.
    static boolean isValidBst(TreeNode node) {
        return isValidBst(node, Long.MIN_VALUE, Long.MAX_VALUE);
    }

    static boolean isValidBst(TreeNode node, long min, long max) {
        if (node == null) return true;
        if (node.value <= min || node.value >= max) return false; // must respect EVERY ancestor's bound, not just the parent
        return isValidBst(node.left, min, node.value)    // tighten the UPPER bound going left
            && isValidBst(node.right, node.value, max);   // tighten the LOWER bound going right
    }

    static void intermediateLevel() {
        TreeNode invalidTree = new TreeNode(10, null, new TreeNode(15, new TreeNode(6), null));
        System.out.println("intermediate: range-based check on the flawed tree (correctly fails) -> " + isValidBst(invalidTree));

        TreeNode validTree = new TreeNode(10, new TreeNode(5), new TreeNode(15, new TreeNode(12), new TreeNode(20)));
        System.out.println("intermediate: range-based check on a genuinely valid BST -> " + isValidBst(validTree));
    }

    // Level 3: hardened -- empty tree, and a tree with a duplicate value (rejected under a strict BST definition).
    static void advancedLevel() {
        System.out.println("advanced: isValidBst(null) -> " + isValidBst(null));

        TreeNode duplicateTree = new TreeNode(10, new TreeNode(10), null); // left child EQUAL to parent -- violates strict "<"
        System.out.println("advanced: isValidBst with a duplicate value -> " + isValidBst(duplicateTree));

        TreeNode edgeCase = new TreeNode(Integer.MIN_VALUE); // confirm no overflow issues with the Long-based bounds
        System.out.println("advanced: isValidBst with Integer.MIN_VALUE as the only node -> " + isValidBst(edgeCase));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ValidateBst.java`, then run `java ValidateBst.java`.

## 6. Walkthrough

Trace `isValidBst` on the flawed tree `10(right: 15(left: 6))`:

| Call | min | max | node.value | check | recurse |
|---|---|---|---|---|---|
| `isValidBst(10, ...)` | -inf | +inf | 10 | `10 > -inf && 10 < +inf` -> pass | left: `(null, -inf, 10)`; right: `(15, 10, +inf)` |
| `isValidBst(15, 10, +inf)` | 10 | +inf | 15 | `15 > 10 && 15 < +inf` -> pass | left: `(6, 10, 15)`; right: `(null, 15, +inf)` |
| `isValidBst(6, 10, 15)` | 10 | 15 | 6 | `6 > 10` -> **false** | stop |

The range `(10, 15)` passed into the check on node `6` correctly carries the constraint from the root (`> 10`), which `6` fails — exactly the violation the local-only check in `basicLevel()` missed, since it only ever compared `6` against its immediate parent `15` (`6 < 15`, which looks fine in isolation).

## 7. Gotchas & takeaways

> Gotcha: using `int` for `min`/`max` bounds (instead of `long`, or `Integer`/boxed with explicit `null` handling) breaks on a tree containing `Integer.MIN_VALUE` or `Integer.MAX_VALUE`, since the initial sentinel bounds would need to be *outside* the full `int` range — using `long` for the bounds sidesteps this overflow trap entirely.

- The naive "check only the immediate parent" approach is wrong — it misses violations from a non-immediate ancestor further up the tree.
- The correct approach threads a valid `(min, max)` range down through the recursion, tightened by every ancestor along the way.
- Use `long` bounds (or boxed `Integer` with careful `null` handling) to avoid overflow at the tree's extreme values.
- Related concepts: [Binary tree & binary search tree (BST)](0098-binary-tree-binary-search-tree-bst.md), [In-order / pre-order / post-order traversal](0101-in-order-pre-order-post-order-traversal.md) (an in-order traversal producing sorted output is an alternative validation technique).
