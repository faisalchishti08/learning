---
card: leetcode-patterns
gi: 153
slug: serialize-and-deserialize-binary-tree
title: Serialize and Deserialize Binary Tree
---

## 1. What it is

Design an algorithm to serialize a binary tree into a single string, and deserialize that string back into a tree with the exact same structure and values. Example: `root = [1,2,3,null,null,4,5]` serializes to something like `"1,2,#,#,3,4,#,#,5,#,#"` (using `#` for `null`), and deserializing that string reconstructs the original tree.

## 2. Why & when

Pre-order traversal (root, then left, then right) is the natural choice here because it always writes a subtree's root before its children, which is exactly the order needed to rebuild top-down: read a value, that is the root; recursively read the left subtree next; recursively read the right subtree after that. Explicitly recording `null` markers (instead of omitting missing children) is what makes the string unambiguous to parse back — without them, you cannot tell where one subtree ends and the next begins.

## 3. Core concept

**Key idea:** serialize with pre-order DFS, writing `"#"` for every `null` child so the shape is fully recorded. Deserialize by reading tokens off the front of the same sequence, in the same pre-order: a `"#"` means `null`; a number means a new node, whose left and right children are built by recursively consuming more tokens from the same stream.

**Steps (serialize):**
1. Base case: if `node == null`, append `"#"` to the output and return.
2. Append `node.val`.
3. Recurse: `serialize(node.left)`, then `serialize(node.right)`.
4. Join all appended tokens with a delimiter (e.g. `,`).

**Steps (deserialize):**
1. Split the string into a queue (or list with a shared index) of tokens.
2. Define `build()`: read and remove the next token.
3. If the token is `"#"`, return `null`.
4. Otherwise, create `node = new TreeNode(parseInt(token))`.
5. Recurse: `node.left = build()`, then `node.right = build()`.
6. Return `node`.

**Why it is correct:** because every subtree — including empty ones — leaves exactly one token in the pre-order sequence (either its root value, or a `"#"` marker), the deserializer can always tell, token by token, whether to build a real node or stop at `null`, using a shared read-pointer that advances in perfect lockstep with how `serialize` wrote the tokens.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pre-order with null markers round-trips a tree through a flat string">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="30" r="15" fill="#161b22" stroke="#79c0ff"/><text x="230" y="34" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="170" cy="80" r="15" fill="#161b22" stroke="#79c0ff"/><text x="170" y="84" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="300" cy="80" r="15" fill="#161b22" stroke="#79c0ff"/><text x="300" y="84" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="270" cy="130" r="13" fill="#161b22" stroke="#79c0ff"/><text x="270" y="134" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="330" cy="130" r="13" fill="#161b22" stroke="#79c0ff"/><text x="330" y="134" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <line x1="221" y1="43" x2="179" y2="68" stroke="#8b949e"/>
    <line x1="239" y1="43" x2="291" y2="68" stroke="#8b949e"/>
    <line x1="292" y1="92" x2="277" y2="118" stroke="#8b949e"/>
    <line x1="308" y1="92" x2="323" y2="118" stroke="#8b949e"/>
    <text x="10" y="15" fill="#e6edf3">Serialized (pre-order, # = null): 1,2,#,#,3,4,#,#,5,#,#</text>
    <text x="10" y="175" fill="#e6edf3">Reading left to right rebuilds: 1 -&gt; left=2(leaf) -&gt; right=3 -&gt; left=4(leaf) -&gt; right=5(leaf)</text>
  </g>
</svg>

The `#` markers for node `2`'s missing children tell the deserializer exactly where `2`'s subtree ends and `3`'s subtree begins.

## 5. Runnable example

```java
// SerializeDeserializeBinaryTree.java
import java.util.*;

public class SerializeDeserializeBinaryTree {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
        TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
    }

    // Level 1 -- Brute force: serialize via LEVEL ORDER (BFS) instead
    // of pre-order, recording every node's children explicitly by
    // index. Works, but needs an index-based scheme (like a complete
    // binary tree array) that wastes space on sparse, unbalanced trees
    // -- O(n) in the best case but can blow up to O(2^h) slots for a
    // very lopsided tree, versus pre-order's guaranteed O(n) tokens.
    static String bruteForceSerialize(TreeNode root) {
        List<String> tokens = new ArrayList<>();
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            TreeNode node = queue.poll();
            if (node == null) { tokens.add("#"); continue; }
            tokens.add(String.valueOf(node.val));
            queue.offer(node.left);
            queue.offer(node.right);
        }
        return String.join(",", tokens);
    }

    // KEY INSIGHT: pre-order (root, then left, then right) with # for
    // null is always exactly n tokens for n nodes, and it is naturally
    // resumable -- a single shared read-pointer rebuilds the tree with
    // one pass, no index arithmetic needed.

    // Level 2 -- Optimal: pre-order serialize/deserialize with # markers.
    // O(n) time and space for both directions.
    public static String serialize(TreeNode root) {
        StringBuilder sb = new StringBuilder();
        serializeHelper(root, sb);
        return sb.toString();
    }

    static void serializeHelper(TreeNode node, StringBuilder sb) {
        if (node == null) { sb.append("#,"); return; }
        sb.append(node.val).append(",");
        serializeHelper(node.left, sb);
        serializeHelper(node.right, sb);
    }

    public static TreeNode deserialize(String data) {
        Queue<String> tokens = new LinkedList<>(Arrays.asList(data.split(",")));
        return buildFromTokens(tokens);
    }

    static TreeNode buildFromTokens(Queue<String> tokens) {
        String token = tokens.poll();
        if (token.equals("#")) return null;
        TreeNode node = new TreeNode(Integer.parseInt(token));
        node.left = buildFromTokens(tokens);
        node.right = buildFromTokens(tokens);
        return node;
    }

    // Level 3 -- Hardened: an empty tree (root == null) must serialize
    // to just "#" and deserialize back to null, without throwing on an
    // empty tokens queue.
    static TreeNode hardened(String data) {
        return deserialize(data);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(1,
            new TreeNode(2),
            new TreeNode(3, new TreeNode(4), new TreeNode(5)));

        String bfSerialized = bruteForceSerialize(root);
        System.out.println(bfSerialized);

        String serialized = serialize(root);
        System.out.println(serialized);
        TreeNode rebuilt = deserialize(serialized);
        System.out.println(rebuilt.val + " " + rebuilt.right.left.val + " " + rebuilt.right.right.val);

        System.out.println(hardened("#"));
    }
}
```

How to run: save as `SerializeDeserializeBinaryTree.java`, then run `java SerializeDeserializeBinaryTree.java`.

## 6. Walkthrough

Dry run of `deserialize` on `"1,2,#,#,3,4,#,#,5,#,#"`:

| step | token consumed | action |
|---|---|---|
| 1 | "1" | create node 1; recurse for its left |
| 2 | "2" | create node 2; recurse for ITS left |
| 3 | "#" | node 2's left is null |
| 4 | "#" | node 2's right is null; node 2 fully built, becomes node 1's left |
| 5 | "3" | create node 3, node 1's right; recurse for ITS left |
| 6 | "4" | create node 4; both its children read as "#", "#" (not shown), becomes node 3's left |
| 7 | "5" | create node 5; both its children read as "#", "#", becomes node 3's right |

The rebuilt tree exactly matches the original: `1` with left child `2` (a leaf) and right child `3` (whose children are `4` and `5`). Time complexity: O(n) for both serialize and deserialize. Space complexity: O(n) for the token string/queue, plus O(h) for the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: omitting the `"#"` markers for `null` children (only writing real values) makes the string ambiguous — you cannot tell, just from a flat list of numbers, where one node's subtree ends and its sibling's begins; the explicit `null` markers are what make pre-order alone sufficient to reconstruct the tree unambiguously.

- Using a shared, mutable `Queue<String>` (or an index into an array) for the tokens during deserialization is essential — each recursive call must consume tokens from the SAME position onward, exactly mirroring how `serializeHelper` wrote them in one continuous pass.
- Related problems: Construct Binary Tree from Preorder and Inorder Traversal (also rebuilds a tree from a traversal sequence, but needs a SECOND traversal to disambiguate structure, since it lacks explicit null markers), Flatten Binary Tree to Linked List (also reasons about pre-order structure, there restructuring an existing tree instead of encoding it as text).
