---
card: data-structures
gi: 103
slug: bst-insert-search-delete
title: BST insert / search / delete
---

## 1. What it is

These are the three core mutating and querying operations on a binary search tree (BST): **insert** a new value while keeping the BST invariant intact, **search** for a value, and **delete** a value while keeping the invariant intact afterward. Insert and search are straightforward; delete is the operation with real subtlety, because removing a node can leave a gap that must be filled correctly.

## 2. Why & when

These three operations are what make a BST useful in the first place — everything else (successor/predecessor, validation, LCA) builds on understanding how the tree's shape changes correctly under insert and delete. Delete specifically is one of the most commonly asked "explain the cases" interview questions, because it has three genuinely different cases to handle.

## 3. Core concept

**How the operation transforms the structure — search.** Compare the target against the current node; if smaller, recurse left; if larger, recurse right; if equal, found. This only works because of the BST invariant — at each step, an entire subtree is safely ruled out.

**How the operation transforms the structure — insert.** Same downward walk as search, but when a `null` is reached (the correct empty spot, following the same smaller-left/larger-right rule the whole way down), a new node is created there. The rest of the tree is untouched — insert only ever adds one new leaf.

**How the operation transforms the structure — delete, the three cases.**
1. **Node has no children (a leaf):** simply remove it — replace the reference to it with `null`.
2. **Node has exactly one child:** replace the node with its one child directly — the child (and its whole subtree) takes the deleted node's place.
3. **Node has two children:** this is the subtle case. You cannot just remove it — you need a replacement value that keeps the BST invariant intact. The standard fix: find the node's **in-order successor** (the smallest value in its right subtree — see [BST successor & predecessor](0104-bst-successor-predecessor.md)), copy that value into the node being "deleted," then delete the successor node instead (which is guaranteed to have at most one child, reducing to case 1 or 2).

**Why the invariant survives case 3.** The in-order successor is the smallest value greater than the node being deleted — copying it up preserves "everything in the right subtree is still greater," and removing it from its original position (where it has at most a right child, by definition of being the leftmost node) is a simple case-1-or-2 delete.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Deleting node 8 which has two children, by finding its in-order successor 9 in the right subtree, copying 9 up into 8's position, then removing the original node 9">
  <g font-family="sans-serif" font-size="11">
    <circle cx="200" cy="30" r="18" fill="#0d1117" stroke="#f0883e"/><text x="200" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <text x="150" y="20" fill="#f0883e" font-size="9">delete this</text>
    <circle cx="140" cy="90" r="18" fill="#161b22" stroke="#8b949e"/><text x="140" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <circle cx="280" cy="90" r="18" fill="#161b22" stroke="#8b949e"/><text x="280" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">12</text>
    <circle cx="240" cy="150" r="18" fill="#0d1117" stroke="#79c0ff"/><text x="240" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">9</text>
    <text x="240" y="180" fill="#79c0ff" text-anchor="middle" font-size="9">successor: smallest in right subtree</text>
    <line x1="188" y1="42" x2="152" y2="78" stroke="#8b949e"/>
    <line x1="212" y1="42" x2="268" y2="78" stroke="#8b949e"/>
    <line x1="268" y1="102" x2="248" y2="138" stroke="#8b949e"/>
    <text x="440" y="90" fill="#a5d6ff" font-size="10">result: copy 9 into the root's</text>
    <text x="440" y="105" fill="#a5d6ff" font-size="10">position, then remove the</text>
    <text x="440" y="120" fill="#a5d6ff" font-size="10">original node 9 (a simple</text>
    <text x="440" y="135" fill="#a5d6ff" font-size="10">leaf-or-one-child delete)</text>
  </g>
</svg>

`8` has two children, so its in-order successor `9` (the leftmost node in `8`'s right subtree) is copied into `8`'s position, and the original `9` node is removed via the simpler one-child-or-leaf case.

## 5. Runnable example

```java
// BstInsertSearchDelete.java
public class BstInsertSearchDelete {

    static class TreeNode {
        int value;
        TreeNode left, right;
        TreeNode(int value) { this.value = value; }
    }

    // Basic: insert and search.
    static TreeNode insert(TreeNode node, int value) {
        if (node == null) return new TreeNode(value);
        if (value < node.value) node.left = insert(node.left, value);
        else if (value > node.value) node.right = insert(node.right, value);
        return node;
    }

    static boolean search(TreeNode node, int target) {
        if (node == null) return false;
        if (target == node.value) return true;
        return target < node.value ? search(node.left, target) : search(node.right, target);
    }

    static void basicLevel() {
        TreeNode root = null;
        for (int v : new int[]{8, 5, 12, 3, 9}) root = insert(root, v);
        System.out.println("basic: search(9) -> " + search(root, 9));
        System.out.println("basic: search(7) -> " + search(root, 7));
    }

    // Intermediate: delete a leaf and a one-child node -- the simpler two cases.
    static TreeNode delete(TreeNode node, int target) {
        if (node == null) return null;
        if (target < node.value) { node.left = delete(node.left, target); return node; }
        if (target > node.value) { node.right = delete(node.right, target); return node; }

        // target == node.value: this IS the node to delete.
        if (node.left == null && node.right == null) return null;         // case 1: leaf
        if (node.left == null) return node.right;                          // case 2: only a right child
        if (node.right == null) return node.left;                         // case 2: only a left child

        // case 3: two children -- find in-order successor (smallest in right subtree), copy it up, delete it from the right subtree.
        TreeNode successor = node.right;
        while (successor.left != null) successor = successor.left;
        node.value = successor.value;                                     // copy successor's value up
        node.right = delete(node.right, successor.value);                 // remove the original successor node
        return node;
    }

    static void intermediateLevel() {
        TreeNode root = null;
        for (int v : new int[]{8, 5, 12, 3, 9}) root = insert(root, v);

        root = delete(root, 3); // leaf delete
        System.out.println("intermediate: after deleting leaf 3, search(3) -> " + search(root, 3));

        root = delete(root, 5); // 5 is now a leaf, since its only child (3) was just removed above
        System.out.println("intermediate: after deleting 5, search(5) -> " + search(root, 5));
    }

    // Advanced: delete a two-children node, confirm the in-order traversal stays sorted afterward.
    static void inOrder(TreeNode node, StringBuilder out) {
        if (node == null) return;
        inOrder(node.left, out);
        out.append(node.value).append(" ");
        inOrder(node.right, out);
    }

    static void advancedLevel() {
        TreeNode root = null;
        for (int v : new int[]{8, 5, 12, 3, 9, 10, 15}) root = insert(root, v);

        StringBuilder before = new StringBuilder();
        inOrder(root, before);
        System.out.println("advanced: in-order before delete -> " + before.toString().trim());

        root = delete(root, 12); // 12 has two children: 9 (with its own right child 10) and 15
        StringBuilder after = new StringBuilder();
        inOrder(root, after);
        System.out.println("advanced: in-order after deleting 12 (two children) -> " + after.toString().trim() + " (still sorted)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `BstInsertSearchDelete.java`, then run `java BstInsertSearchDelete.java`.

## 6. Walkthrough

Trace `delete(root, 12)` in `advancedLevel()`, where the tree is `8(5(3,-), 12(9(-,10), 15))`:

| Step | Action |
|---|---|
| 1 | Recurse down: `12 > 8`, go right; arrive at node `12` — this is the target |
| 2 | `12` has two children (`9` and `15`) — case 3 |
| 3 | Find in-order successor: start at `node.right` (`15`), walk `.left` while possible — `15.left` is `null`, so successor is `15` itself |
| 4 | Copy `15` into node `12`'s value — the node formerly holding `12` now holds `15` |
| 5 | Recursively delete `15` from the right subtree — `15` is a leaf, so it is simply removed |

Result: the node that was `12` now holds `15`, and the original `15` leaf is gone. The in-order traversal (`3, 5, 8, 9, 10, 15`) stays fully sorted, confirming the BST invariant survived the two-children delete correctly.

## 7. Gotchas & takeaways

> Gotcha: a common bug in case 3 is deleting the *original* node object and trying to re-link its parent to the successor node directly, instead of the simpler and more robust approach shown here — copying the successor's *value* into the existing node, then deleting the successor from its original position. The value-copy approach avoids having to rewire the deleted node's own child pointers onto a different node.

- Search and insert both walk down comparing against each node, using the BST invariant to discard half the remaining tree each step.
- Delete has three cases: no children (remove directly), one child (replace with that child), two children (copy the in-order successor's value up, then delete the successor from its simpler position).
- The in-order successor of a two-children node is always the leftmost node of its right subtree, and it always has at most one child (a right child), making its own removal simple.
- Related concepts: [BST successor & predecessor](0104-bst-successor-predecessor.md), [Binary tree & binary search tree (BST)](0098-binary-tree-binary-search-tree-bst.md).
