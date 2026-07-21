---
card: leetcode-patterns
gi: 148
slug: binary-search-tree-iterator
title: Binary Search Tree Iterator
---

## 1. What it is

Design an iterator over a binary search tree (BST) that returns its values in ascending (in-order) order, one at a time. Implement `next()` (returns the next smallest value) and `hasNext()` (returns whether more values remain), both required to run in average O(1) time. Example: for `root = [7,3,15,null,null,9,20]`, calling `next()` repeatedly returns `3, 7, 9, 15, 20`.

## 2. Why & when

Kth Smallest Element in a BST solved "give me the k-th value" as one batch call; this problem asks for the SAME in-order sequence, but delivered one step at a time, resumable across separate method calls. That resumability is exactly what an explicit stack gives you that plain recursion cannot: recursion's call stack disappears between calls, but a stack you manage yourself persists as an object's field, so `next()` can pick up exactly where the previous call left off.

## 3. Core concept

**Key idea:** maintain a stack that always holds the path of "leftmost still-unvisited" nodes, from the current position down to the deepest pending left child. `next()` pops the top (the smallest pending value), and if that node has a right child, pushes that child and then that child's entire leftmost chain onto the stack (preparing the next batch of "next smallest" candidates).

**Steps (constructor):**
1. Initialize an empty stack.
2. Push `root`, then keep pushing `.left` children until reaching a `null`, so the stack's top is always the current smallest unvisited node.

**Steps (`next()`):**
1. Pop the top node — this is the next smallest value.
2. If the popped node has a right child, push that right child, then push its entire leftmost chain (same logic as the constructor), so the stack's top is again the smallest unvisited node.
3. Return the popped node's value.

**Steps (`hasNext()`):** return `!stack.isEmpty()`.

**Why it is correct:** the stack always represents "ancestors whose right subtree has not been explored yet, plus the current leftmost frontier" — which is precisely the state a recursive in-order traversal would have on its call stack at the same point, just made persistent by managing it explicitly instead of relying on the language's own call stack.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An explicit stack holds the leftmost unvisited chain, mimicking recursion's call stack">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="15" fill="#161b22" stroke="#79c0ff"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">7</text>
    <circle cx="160" cy="85" r="15" fill="#161b22" stroke="#3fb950"/><text x="160" y="89" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="300" cy="85" r="15" fill="#161b22" stroke="#79c0ff"/><text x="300" y="89" fill="#e6edf3" text-anchor="middle">15</text>
    <circle cx="260" cy="140" r="14" fill="#161b22" stroke="#79c0ff"/><text x="260" y="144" fill="#e6edf3" text-anchor="middle" font-size="11">9</text>
    <circle cx="340" cy="140" r="14" fill="#161b22" stroke="#79c0ff"/><text x="340" y="144" fill="#e6edf3" text-anchor="middle" font-size="11">20</text>
    <line x1="222" y1="43" x2="168" y2="72" stroke="#3fb950" stroke-width="2"/>
    <line x1="238" y1="43" x2="292" y2="72" stroke="#8b949e"/>
    <line x1="292" y1="98" x2="266" y2="126" stroke="#8b949e"/>
    <line x1="308" y1="98" x2="334" y2="126" stroke="#8b949e"/>
    <text x="10" y="15" fill="#e6edf3">Initial stack (bottom to top): [7, 3] -- 3's leftmost chain has no children</text>
    <text x="10" y="175" fill="#e6edf3">next() pops 3 (smallest); 3 has no right child, so nothing new is pushed; top is now 7</text>
  </g>
</svg>

The stack's top is always the smallest value not yet returned; popping it and pushing its right subtree's leftmost chain (if any) prepares the next call.

## 5. Runnable example

```java
// BSTIterator.java
import java.util.*;

public class BSTIterator {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: do a full in-order traversal up front,
    // store every value in a list, and use a simple index pointer for
    // next()/hasNext(). O(n) time and O(n) space up front, even if the
    // caller only ever asks for the first few values.
    static class BruteForceIterator {
        List<Integer> values = new ArrayList<>();
        int index = 0;

        BruteForceIterator(TreeNode root) {
            inorder(root);
        }

        void inorder(TreeNode node) {
            if (node == null) return;
            inorder(node.left);
            values.add(node.val);
            inorder(node.right);
        }

        boolean hasNext() { return index < values.size(); }
        int next() { return values.get(index++); }
    }

    // KEY INSIGHT: an explicit stack holding "the leftmost unvisited
    // chain" gives the SAME state a recursive in-order call stack would
    // have at any given pause point -- so next() can resume exactly
    // where it left off, doing only the work needed for one step, in
    // amortized O(1) instead of computing the whole sequence up front.

    // Level 2 -- Optimal: explicit stack, amortized O(1) per next()/hasNext().
    // O(h) space (stack holds at most one path's worth of nodes).
    static class Iterator {
        Deque<TreeNode> stack = new ArrayDeque<>();

        Iterator(TreeNode root) {
            pushLeftmostChain(root);
        }

        void pushLeftmostChain(TreeNode node) {
            while (node != null) {
                stack.push(node);
                node = node.left;
            }
        }

        boolean hasNext() {
            return !stack.isEmpty();
        }

        int next() {
            TreeNode node = stack.pop();
            if (node.right != null) pushLeftmostChain(node.right);
            return node.val;
        }
    }

    // Level 3 -- Hardened: calling next() on a tree with only one node
    // must return that value once, after which hasNext() must report
    // false, never throwing on an empty stack pop.
    static Iterator hardened(TreeNode root) {
        return new Iterator(root);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(7,
            new TreeNode(3),
            new TreeNode(15, new TreeNode(9), new TreeNode(20)));

        BruteForceIterator bf = new BruteForceIterator(root);
        StringBuilder sb1 = new StringBuilder();
        while (bf.hasNext()) sb1.append(bf.next()).append(" ");
        System.out.println(sb1.toString().trim());

        Iterator it = new Iterator(root);
        StringBuilder sb2 = new StringBuilder();
        while (it.hasNext()) sb2.append(it.next()).append(" ");
        System.out.println(sb2.toString().trim());

        Iterator single = hardened(new TreeNode(5));
        System.out.println(single.next() + " " + single.hasNext());
    }
}
```

How to run: save as `BSTIterator.java`, then run `java BSTIterator.java`.

## 6. Walkthrough

Dry run of the optimal `Iterator` on `root = [7,3,15,null,null,9,20]`:

| step | stack before (top last) | action | returns |
|---|---|---|---|
| constructor | [] | push 7, push 3 (3 has no left child, stop) | stack = [7, 3] |
| next() call 1 | [7, 3] | pop 3; 3 has no right child | 3 |
| next() call 2 | [7] | pop 7; 7 has right child 15, push leftmost chain of 15 (15, then 9) | 7 |
| next() call 3 | [15, 9] | pop 9; 9 has no right child | 9 |
| next() call 4 | [15] | pop 15; 15 has right child 20, push leftmost chain of 20 (just 20) | 15 |
| next() call 5 | [20] | pop 20; no right child | 20 |

Final sequence returned: `3, 7, 9, 15, 20` — correct ascending order. Time complexity: O(1) amortized per `next()` call (each node is pushed and popped exactly once across the iterator's whole lifetime, so total work across `n` calls is O(n), giving O(1) average). Space complexity: O(h), the stack holds at most one root-to-node path at a time.

## 7. Gotchas & takeaways

> Gotcha: pushing only the popped node's immediate right CHILD (instead of that child's entire leftmost chain) breaks the invariant that the stack's top is always the smallest unvisited value — you must call `pushLeftmostChain` on the right child, not just push the single node.

- The O(1) "average" (amortized) claim, not a strict O(1) worst case per call, is the correct way to describe this: a single `next()` call right after visiting a node with a deep right subtree does more work, but that work is paid for by many subsequent cheap `next()` calls, so it evens out across the whole traversal.
- Related problems: Kth Smallest Element in a BST (the same in-order sequence, delivered as one batch call instead of a resumable iterator), Flatten Binary Tree to Linked List (also turns a tree into a sequential structure, there by rewiring pointers instead of using an external stack).
