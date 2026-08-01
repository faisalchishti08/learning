---
card: data-structures
gi: 100
slug: n-ary-general-trees
title: N-ary & general trees
---

## 1. What it is

An **N-ary tree** (or general tree) is a tree where each node can have any number of children — not limited to two, like a binary tree. Instead of fixed `left`/`right` fields, each node typically holds a `List` (or array) of child references, one per child, however many there are.

## 2. Why & when

Use an N-ary tree whenever the real-world structure naturally has more than two branches per node: a file system (a folder can hold any number of files or subfolders), an HTML/XML document (an element can have any number of child elements), an organization chart (a manager can have any number of direct reports), or a trie (each node can branch on any number of characters). Forcing such data into a binary tree would be an artificial, awkward fit.

## 3. Core concept

**The structure's shape.** Each node holds a value and a collection of children — commonly `List<Node>`. There is no upper bound on a node's number of children (hence "N-ary," for an arbitrary N), unlike a binary tree's fixed two-slot `left`/`right`.

**How it sits in memory.** Same idea as a binary tree — nodes connected by references — but each node's "next" pointers are now a variable-length list instead of two fixed fields. Memory layout is otherwise identical: scattered node objects, each holding a reference to its own children collection.

**Traversal still works the same way, generalized.** Pre-order (visit node, then each child's subtree in order) and post-order (visit each child's subtree, then the node) still make sense for an N-ary tree — you just loop over all children instead of hardcoding "left, then right." Level-order (BFS) works identically too, enqueueing all of a node's children instead of just two. In-order specifically does *not* generalize cleanly, since it relies on exactly two children (visit left, then self, then right) — there is no single natural "in-order" position among N children.

**Binary tree as a special case.** A binary tree is simply an N-ary tree where N happens to always be at most 2 — every binary-tree algorithm's core idea (recurse into children, combine results) carries over directly; only the exact code shape (a loop over children, instead of two hardcoded recursive calls) changes.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A file system tree where the root folder has three children, one of which itself has two children, illustrating a variable number of children per node">
  <g font-family="sans-serif" font-size="11">
    <rect x="280" y="20" width="80" height="26" fill="#0d1117" stroke="#f0883e" rx="4"/><text x="320" y="37" fill="#e6edf3" text-anchor="middle" font-size="8">/root</text>
    <rect x="150" y="90" width="80" height="26" fill="#161b22" stroke="#8b949e" rx="4"/><text x="190" y="107" fill="#e6edf3" text-anchor="middle" font-size="8">docs/</text>
    <rect x="280" y="90" width="80" height="26" fill="#161b22" stroke="#8b949e" rx="4"/><text x="320" y="107" fill="#e6edf3" text-anchor="middle" font-size="8">a.txt</text>
    <rect x="410" y="90" width="80" height="26" fill="#161b22" stroke="#8b949e" rx="4"/><text x="450" y="107" fill="#e6edf3" text-anchor="middle" font-size="8">src/</text>
    <rect x="380" y="150" width="80" height="26" fill="#161b22" stroke="#8b949e" rx="4"/><text x="420" y="167" fill="#e6edf3" text-anchor="middle" font-size="8">main.java</text>
    <rect x="470" y="150" width="80" height="26" fill="#161b22" stroke="#8b949e" rx="4"/><text x="510" y="167" fill="#e6edf3" text-anchor="middle" font-size="8">util.java</text>
    <line x1="300" y1="46" x2="200" y2="82" stroke="#8b949e"/>
    <line x1="320" y1="46" x2="320" y2="82" stroke="#8b949e"/>
    <line x1="340" y1="46" x2="450" y2="82" stroke="#8b949e"/>
    <line x1="440" y1="116" x2="425" y2="142" stroke="#8b949e"/>
    <line x1="460" y1="116" x2="510" y2="142" stroke="#8b949e"/>
    <text x="320" y="65" fill="#79c0ff" text-anchor="middle" font-size="8">/root has 3 children -- not limited to 2</text>
  </g>
</svg>

`/root` has three children (`docs/`, `a.txt`, `src/`); `src/` has two of its own — each node's child count is whatever the data actually needs, not a fixed maximum.

## 5. Runnable example

```java
// NAryTreeDemo.java
import java.util.ArrayList;
import java.util.List;

public class NAryTreeDemo {

    static class Node {
        String name;
        List<Node> children = new ArrayList<>();
        Node(String name) { this.name = name; }
        Node addChild(Node child) { children.add(child); return this; }
    }

    // Basic: build a small file-system-like tree with a variable number of children per node.
    static void basicLevel() {
        Node root = new Node("/root");
        Node docs = new Node("docs");
        Node src = new Node("src");
        root.addChild(docs).addChild(new Node("a.txt")).addChild(src);
        src.addChild(new Node("main.java")).addChild(new Node("util.java"));

        System.out.println("basic: root has " + root.children.size() + " children");
        System.out.println("basic: src has " + src.children.size() + " children");
    }

    // Intermediate: pre-order traversal, generalized to loop over ALL children instead of hardcoding left/right.
    static void preOrder(Node node, StringBuilder out) {
        if (node == null) return;
        out.append(node.name).append(" ");
        for (Node child : node.children) preOrder(child, out); // loop, not two fixed calls
    }

    static void intermediateLevel() {
        Node root = new Node("/root");
        Node docs = new Node("docs");
        Node src = new Node("src");
        root.addChild(docs).addChild(new Node("a.txt")).addChild(src);
        src.addChild(new Node("main.java")).addChild(new Node("util.java"));

        StringBuilder out = new StringBuilder();
        preOrder(root, out);
        System.out.println("intermediate: pre-order visit -> " + out.toString().trim());
    }

    // Advanced: level-order (BFS) traversal, and computing max depth -- both generalize the same way as binary trees.
    static int maxDepth(Node node) {
        if (node == null) return 0;
        int deepest = 0;
        for (Node child : node.children) deepest = Math.max(deepest, maxDepth(child));
        return 1 + deepest;
    }

    static void advancedLevel() {
        Node root = new Node("/root");
        Node docs = new Node("docs");
        Node src = new Node("src");
        root.addChild(docs).addChild(new Node("a.txt")).addChild(src);
        src.addChild(new Node("main.java")).addChild(new Node("util.java"));

        java.util.Queue<Node> queue = new java.util.ArrayDeque<>();
        queue.offer(root);
        StringBuilder levelOrder = new StringBuilder();
        while (!queue.isEmpty()) {
            Node node = queue.poll();
            levelOrder.append(node.name).append(" ");
            for (Node child : node.children) queue.offer(child); // enqueue ALL children, however many there are
        }

        System.out.println("advanced: level-order visit -> " + levelOrder.toString().trim());
        System.out.println("advanced: max depth -> " + maxDepth(root));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `NAryTreeDemo.java`, then run `java NAryTreeDemo.java`.

## 6. Walkthrough

1. `basicLevel()` builds `/root` with three children (`docs`, `a.txt`, `src`), and `src` with two of its own — confirming each node's `children.size()` reflects however many were actually added, with no fixed cap.
2. `intermediateLevel()`'s `preOrder` visits a node, then loops over `node.children` calling itself recursively on each — the exact same "visit self, then recurse" idea as a binary tree's pre-order, just generalized from two hardcoded calls (`left`, `right`) to a loop over however many children exist. Output: `/root docs a.txt src main.java util.java`.
3. `advancedLevel()`'s BFS enqueues every child of the current node (not just up to two), giving the same level-order guarantee as [BFS level-order using a queue](0080-bfs-level-order-using-a-queue.md), generalized. `maxDepth` recurses into every child and takes the maximum depth found, plus one for the current node — for this tree, the deepest path is `/root -> src -> main.java` (or `util.java`), depth `3`.

## 7. Gotchas & takeaways

> Gotcha: in-order traversal does not generalize to N-ary trees in any single, agreed-upon way — since there is no natural "middle" position among an arbitrary number of children, code that assumes an in-order-style traversal exists for a general tree is applying a binary-tree-specific concept where it does not apply.

- An N-ary tree node holds a variable-length collection of children, instead of fixed `left`/`right` fields.
- Pre-order, post-order, and level-order all generalize directly: loop over all children instead of hardcoding two.
- In-order does not generalize cleanly, since it depends on there being exactly two children.
- A binary tree is simply the special case where every node has at most 2 children.
- Related concepts: [In-order / pre-order / post-order traversal](0101-in-order-pre-order-post-order-traversal.md), [BFS level-order using a queue](0080-bfs-level-order-using-a-queue.md).
