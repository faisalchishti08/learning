---
card: data-structures
gi: 109
slug: serialize-deserialize-a-tree
title: Serialize & deserialize a tree
---

## 1. What it is

**Serialization** turns a tree into a flat string (or array) that you can save to a file or send over a network. **Deserialization** rebuilds the exact same tree — same shape, same values — from that string. The two operations are inverses: `deserialize(serialize(tree))` must produce a tree identical to the original.

## 2. Why & when

Trees live in memory as scattered nodes linked by pointers, but storage and network protocols only understand flat bytes. You need serialization whenever you save a tree to disk, cache it, or send it between processes. It also comes up often as an interview problem, because a correct solution must encode enough structure to recover `null` children — not just the node values.

## 3. Core concept

**Key idea in one sentence.** Walk the tree in a fixed, repeatable order (usually pre-order), writing a marker for every `null` child, so the same walk in reverse can rebuild the exact shape.

**Why `null` markers matter.** If you only write non-null values, the deserializer cannot tell where one subtree ends and the next begins — two different trees can produce the same list of values without markers. Writing an explicit token (e.g. `"#"`) for every `null` child removes that ambiguity.

**Pre-order serialization.** Visit the current node first, then recurse left, then recurse right. Write the node's value, or the `null` marker, at each step. This order is easy to reverse: deserialization also reads one token at a time and reconstructs the same way it was written.

**Pre-order deserialization.** Read tokens one at a time from the front of the list. If the token is the `null` marker, return `null`. Otherwise, create a new node with that value, then recursively read its left child, then its right child — using the same shared cursor so each recursive call consumes exactly the tokens it needs.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A small tree with root 1, left child 2, right child 3, serialized pre order into a token list with hash markers for null children">
  <g font-family="sans-serif" font-size="11">
    <circle cx="150" cy="30" r="18" fill="#0d1117" stroke="#f0883e"/><text x="150" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <circle cx="100" cy="90" r="18" fill="#161b22" stroke="#79c0ff"/><text x="100" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <circle cx="200" cy="90" r="18" fill="#161b22" stroke="#79c0ff"/><text x="200" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <line x1="138" y1="42" x2="112" y2="78" stroke="#8b949e"/>
    <line x1="162" y1="42" x2="188" y2="78" stroke="#8b949e"/>
    <text x="100" y="130" fill="#8b949e" font-size="9">2 is a leaf: left=null, right=null</text>
    <text x="200" y="130" fill="#8b949e" font-size="9">3 is a leaf: left=null, right=null</text>
    <rect x="30" y="160" width="580" height="40" fill="#161b22" stroke="#79c0ff"/>
    <text x="320" y="184" fill="#e6edf3" text-anchor="middle" font-size="10">tokens: 1 , 2 , # , # , 3 , # , #</text>
  </g>
</svg>

The pre-order walk visits `1`, then `2` with its two `null` children (`#`), then `3` with its two `null` children — every `null` is written explicitly so the shape survives.

## 5. Runnable example

```java
// SerializeDeserializeTree.java
import java.util.ArrayDeque;
import java.util.Deque;

public class SerializeDeserializeTree {

    static class TreeNode {
        int value;
        TreeNode left, right;
        TreeNode(int value) { this.value = value; }
        TreeNode(int value, TreeNode left, TreeNode right) { this.value = value; this.left = left; this.right = right; }
    }

    // Basic: pre-order serialize into a comma-separated string, "#" marks a null child.
    static void serializeHelper(TreeNode node, StringBuilder out) {
        if (node == null) { out.append("#,"); return; }
        out.append(node.value).append(",");
        serializeHelper(node.left, out);
        serializeHelper(node.right, out);
    }

    static String serialize(TreeNode root) {
        StringBuilder out = new StringBuilder();
        serializeHelper(root, out);
        return out.toString();
    }

    static void basicLevel() {
        TreeNode root = new TreeNode(1, new TreeNode(2), new TreeNode(3));
        System.out.println("basic: serialize(tree) -> " + serialize(root));
    }

    // Intermediate: deserialize back, using a shared Deque as the cursor so recursive calls consume tokens in order.
    static TreeNode deserializeHelper(Deque<String> tokens) {
        String token = tokens.poll();
        if (token == null || token.equals("#")) return null;
        TreeNode node = new TreeNode(Integer.parseInt(token));
        node.left = deserializeHelper(tokens);  // consumes exactly its own subtree's tokens
        node.right = deserializeHelper(tokens); // resumes right after, since the Deque is shared
        return node;
    }

    static TreeNode deserialize(String data) {
        Deque<String> tokens = new ArrayDeque<>();
        for (String token : data.split(",")) tokens.add(token);
        return deserializeHelper(tokens);
    }

    static void preOrderPrint(TreeNode node, StringBuilder out) {
        if (node == null) { out.append("#,"); return; }
        out.append(node.value).append(",");
        preOrderPrint(node.left, out);
        preOrderPrint(node.right, out);
    }

    static void intermediateLevel() {
        TreeNode root = new TreeNode(1, new TreeNode(2), new TreeNode(3));
        String data = serialize(root);
        TreeNode rebuilt = deserialize(data);

        StringBuilder out = new StringBuilder();
        preOrderPrint(rebuilt, out);
        System.out.println("intermediate: re-serialize(deserialize(data)) -> " + out);
        System.out.println("intermediate: matches original -> " + data.equals(out.toString()));
    }

    // Advanced: a deeper, lopsided tree, confirming null markers correctly preserve an asymmetric shape.
    static void advancedLevel() {
        TreeNode root = new TreeNode(5,
            new TreeNode(3, new TreeNode(1), null),
            new TreeNode(8, null, new TreeNode(9)));

        String data = serialize(root);
        TreeNode rebuilt = deserialize(data);

        StringBuilder out = new StringBuilder();
        preOrderPrint(rebuilt, out);
        System.out.println("advanced: original  -> " + data);
        System.out.println("advanced: roundtrip -> " + out);
        System.out.println("advanced: shape preserved -> " + data.equals(out.toString()));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `SerializeDeserializeTree.java`, then run `java SerializeDeserializeTree.java`.

## 6. Walkthrough

1. `basicLevel()` serializes the tree `1(left: 2, right: 3)`. The pre-order walk visits `1`, then recurses left into `2` (a leaf, so it writes `2,#,#,`), then recurses right into `3` (also a leaf, writing `3,#,#,`). The final string is `1,2,#,#,3,#,#,`.
2. `intermediateLevel()` splits that string on commas into a `Deque`, then calls `deserializeHelper`. The first `poll()` reads `1`, creating the root. The recursive call for `node.left` polls `2`, then its own two recursive calls poll `#` and `#`, returning `null` for both of `2`'s children. Control returns to the root's call, which now polls `3` for `node.right`, repeating the same pattern. Because every recursive call shares the same `Deque`, each call consumes exactly the tokens belonging to its own subtree, never more.
3. `advancedLevel()` uses an asymmetric tree where `3` has only a left child and `8` has only a right child. Serializing then deserializing reproduces the exact same shape, proving the `#` markers correctly disambiguate "no child here" from "the next token belongs to a different branch."

## 7. Gotchas & takeaways

> Gotcha: forgetting to write a marker for `null` children makes the encoding ambiguous — `1,2,3` alone cannot tell you whether `2` and `3` are both children of `1`, or whether `2` is `1`'s only child and `3` is `2`'s child. Always encode structure, not just values.

- Pre-order (node, then left, then right) is the standard choice because deserialization can rebuild top-down using the same order it was written in.
- Use a shared cursor (a `Deque`, or an index into an array) during deserialization — each recursive call must consume only its own subtree's tokens and leave the rest for the caller.
- The same idea works with level-order (BFS) serialization instead of pre-order; the token order just changes to match.
- Related concepts: [In-order / pre-order / post-order traversal](0101-in-order-pre-order-post-order-traversal.md), [Level-order (BFS) traversal](0102-level-order-bfs-traversal.md).
