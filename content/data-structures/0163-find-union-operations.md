---
card: data-structures
gi: 163
slug: find-union-operations
title: find & union operations
---

## 1. What it is

**find** and **union** are the two operations that define a [disjoint-set structure](0162-disjoint-set-data-structure.md). `find(x)` answers "which group does `x` belong to?" by returning that group's root. `union(x, y)` merges the groups containing `x` and `y` into a single group.

## 2. Why & when

Every algorithm built on union-find — cycle detection, Kruskal's minimum spanning tree, connected-components counting — is really just a sequence of `find` and `union` calls in a specific order. Understanding exactly what each operation does, step by step, is what lets you implement or debug any of those algorithms confidently.

## 3. Core concept

**How `find` works.** Starting at node `x`, repeatedly move to `parent[x]` until reaching a node whose parent is itself — that node is the root. The root is the group's unique identifier: two nodes are in the same group exactly when `find` returns the same root for both.

**The invariant `find` preserves.** `find` never changes the group structure (in its plain form) — it only reads `parent` pointers and reports the answer. It is a pure query.

**How `union` works.** `union(x, y)` first calls `find(x)` and `find(y)` to get both roots. If the roots are already equal, `x` and `y` are already in the same group, so there is nothing to do. Otherwise, pick one root and make it point to the other — `parent[rootX] = rootY` — which merges the two trees into one, with a single combined root.

**Why the order of operations inside `union` matters.** `union` must call `find` on both `x` and `y` **first**, before attaching anything. Attaching based on `x` and `y` directly (instead of their roots) can create disconnected fragments, because `x` and `y` might already be deep inside larger trees whose roots are what actually need merging.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Step by step trace of union(x,y): find root of x, find root of y, attach one root under the other">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">Before union(4, 6):</text>
    <circle cx="80" cy="50" r="16" fill="#161b22" stroke="#79c0ff"/><text x="80" y="54" text-anchor="middle" font-size="9">1</text>
    <circle cx="80" cy="110" r="16" fill="#0d1117" stroke="#8b949e"/><text x="80" y="114" text-anchor="middle" font-size="9">4</text>
    <line x1="80" y1="68" x2="80" y2="94" stroke="#79c0ff"/>

    <circle cx="220" cy="50" r="16" fill="#f0883e" stroke="#f0883e" fill-opacity="0.2"/><text x="220" y="54" text-anchor="middle" font-size="9">5</text>
    <circle cx="220" cy="110" r="16" fill="#0d1117" stroke="#8b949e"/><text x="220" y="114" text-anchor="middle" font-size="9">6</text>
    <line x1="220" y1="68" x2="220" y2="94" stroke="#f0883e"/>

    <text x="10" y="160" fill="#8b949e">find(4) -&gt; root 1.  find(6) -&gt; root 5.  Roots differ, so attach.</text>

    <text x="400" y="20">After: parent[1] = 5</text>
    <circle cx="480" cy="50" r="16" fill="#f0883e" stroke="#f0883e" fill-opacity="0.2"/><text x="480" y="54" text-anchor="middle" font-size="9">5</text>
    <circle cx="440" cy="110" r="16" fill="#161b22" stroke="#79c0ff"/><text x="440" y="114" text-anchor="middle" font-size="9">1</text>
    <circle cx="520" cy="110" r="16" fill="#0d1117" stroke="#8b949e"/><text x="520" y="114" text-anchor="middle" font-size="9">6</text>
    <circle cx="440" cy="170" r="16" fill="#0d1117" stroke="#8b949e"/><text x="440" y="174" text-anchor="middle" font-size="9">4</text>
    <line x1="480" y1="68" x2="440" y2="94" stroke="#f0883e"/>
    <line x1="480" y1="68" x2="520" y2="94" stroke="#f0883e"/>
    <line x1="440" y1="128" x2="440" y2="154" stroke="#79c0ff"/>
  </g>
</svg>

`union` calls `find` on both arguments first, then attaches roots — never the original nodes directly.

## 5. Runnable example

```java
// FindUnion.java
public class FindUnion {

    static class DSU {
        int[] parent;

        DSU(int n) {
            parent = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }

        int find(int x) {
            while (parent[x] != x) x = parent[x];
            return x;
        }

        void union(int x, int y) {
            int rootX = find(x);
            int rootY = find(y);
            if (rootX != rootY) parent[rootX] = rootY;
        }
    }

    // Basic: trace find() before and after a union, showing the root changes for a merged node.
    static void basicLevel() {
        DSU dsu = new DSU(5);
        System.out.println("basic: find(2) before any union -> " + dsu.find(2));
        dsu.union(2, 3);
        System.out.println("basic: find(2) after union(2,3) -> " + dsu.find(2));
        System.out.println("basic: find(3) after union(2,3) -> " + dsu.find(3));
    }

    // Intermediate: union() on nodes that are already in the same group is a correct no-op.
    static void intermediateLevel() {
        DSU dsu = new DSU(5);
        dsu.union(0, 1);
        dsu.union(1, 2);
        int rootBefore = dsu.find(0);
        dsu.union(0, 2); // 0 and 2 are already connected via 1
        int rootAfter = dsu.find(0);
        System.out.println("intermediate: root unchanged by redundant union -> " + (rootBefore == rootAfter));
    }

    // Advanced: process a stream of union requests and report connectivity queries interleaved with them.
    static void advancedLevel() {
        DSU dsu = new DSU(7);
        int[][] unions = {{0, 1}, {2, 3}, {4, 5}, {1, 2}};
        for (int[] u : unions) dsu.union(u[0], u[1]);

        int[][] queries = {{0, 3}, {0, 4}, {5, 6}};
        for (int[] q : queries) {
            boolean same = dsu.find(q[0]) == dsu.find(q[1]);
            System.out.println("advanced: connected(" + q[0] + "," + q[1] + ") -> " + same);
        }
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java FindUnion.java`

## 6. Walkthrough

Start with 5 singleton groups: `parent = [0,1,2,3,4]`. `find(2)` returns `2` immediately, since it is its own parent.

Call `union(2, 3)`. Inside `union`: `find(2) = 2`, `find(3) = 3`. Roots differ, so attach: `parent[2] = 3`. Now `find(2)` walks `2 -> parent[2]=3 -> parent[3]=3` (self), returning `3`. `find(3)` returns `3` directly. Both `2` and `3` now report the same root, confirming the merge.

Now trace a redundant union: after `union(0,1)` and `union(1,2)`, nodes `0`, `1`, `2` share one root. Calling `union(0, 2)` computes `find(0)` and `find(2)`, both of which already equal the same root — so the `if (rootX != rootY)` check is false, and `union` does nothing. This is correct: `0` and `2` are already in the same group, and no further merging is needed.

**Complexity.** Each `find` costs `O(tree height)`. Each `union` costs two `find` calls plus `O(1)` attach work, so it is also `O(tree height)`. Without [union by rank/size](0164-union-by-rank-size.md) or [path compression](0165-path-compression.md), height can reach `O(n)` in the worst case.

## 7. Gotchas & takeaways

> Attaching by the raw arguments (`parent[x] = y`) instead of their roots (`parent[find(x)] = find(y)`) is a common bug. It can break the "every node's ancestors eventually reach a single root" invariant, silently corrupting future `find` calls for nodes elsewhere in the tree.

- `find` alone never mutates the structure in the plain version above — mutation only happens with [path compression](0165-path-compression.md), which is a valid and important optimization, not a bug.
- Always check `rootX != rootY` before attaching in `union`. Skipping this check on an already-connected pair can create a cycle in the parent pointers (a node pointing to itself through another node), corrupting every future `find`.
- These two operations are the complete public interface of a disjoint-set structure — every optimization (rank, size, path compression) changes *how fast* they run, never *what* they compute.
