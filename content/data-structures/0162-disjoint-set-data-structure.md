---
card: data-structures
gi: 162
slug: disjoint-set-data-structure
title: Disjoint-set data structure
---

## 1. What it is

A **disjoint-set** structure (also called **union-find**) tracks a collection of items split into non-overlapping groups. It answers two questions fast: "are these two items in the same group?" and "merge these two groups into one." Think of it as a forest of trees, where each tree is one group and the tree's root is that group's representative label.

## 2. Why & when

Use a disjoint-set structure whenever you need to track connectivity or grouping as merges happen over time — detecting a cycle while building a graph, finding connected components in an image, or grouping accounts that share an email. Recomputing groups from scratch after each merge, by re-running a graph traversal, costs `O(n)` or worse per merge. A disjoint-set structure does each merge and each "same group?" check in very close to `O(1)`.

## 3. Core concept

**The shape.** An array `parent[]`, where `parent[i]` points to `i`'s parent in its group's tree. A root points to itself (`parent[i] == i`). There is no explicit tree object — the array of parent pointers **is** the forest.

**The invariant.** Every item belongs to exactly one tree. Two items are in the same group if and only if following their `parent` pointers up to the root lands on the same root. This single invariant is what both core operations rely on.

**Two operations, one structure.**
- **find(x):** follow `parent` pointers from `x` until reaching a node that is its own parent — that node is the group's root, and it identifies the group.
- **union(x, y):** find the root of `x` and the root of `y`; if they differ, attach one root under the other, merging the two trees into one.

**Why naive find/union can be slow.** Without any care, repeatedly unioning items in a line (`union(1,2)`, `union(2,3)`, `union(3,4)`, ...) can build a tall, thin chain, making `find` cost `O(n)` in the worst case. Fixing this needs two techniques: [union by rank/size](0164-union-by-rank-size.md) to keep trees shallow, and [path compression](0165-path-compression.md) to flatten them further during `find`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A disjoint-set forest with two trees, each rooted at its group's representative">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <circle cx="120" cy="30" r="18" fill="#161b22" stroke="#79c0ff"/><text x="120" y="34" text-anchor="middle">1</text>
    <circle cx="70" cy="100" r="18" fill="#0d1117" stroke="#8b949e"/><text x="70" y="104" text-anchor="middle">2</text>
    <circle cx="170" cy="100" r="18" fill="#0d1117" stroke="#8b949e"/><text x="170" y="104" text-anchor="middle">3</text>
    <circle cx="120" cy="170" r="18" fill="#0d1117" stroke="#8b949e"/><text x="120" y="174" text-anchor="middle">4</text>

    <line x1="120" y1="48" x2="70" y2="82" stroke="#79c0ff"/>
    <line x1="120" y1="48" x2="170" y2="82" stroke="#79c0ff"/>
    <line x1="170" y1="118" x2="120" y2="152" stroke="#79c0ff"/>

    <text x="120" y="15" text-anchor="middle" font-size="9" fill="#79c0ff">root: group A = {1,2,3,4}</text>

    <circle cx="450" cy="60" r="18" fill="#161b22" stroke="#f0883e"/><text x="450" y="64" text-anchor="middle">5</text>
    <circle cx="500" cy="130" r="18" fill="#0d1117" stroke="#8b949e"/><text x="500" y="134" text-anchor="middle">6</text>
    <line x1="450" y1="78" x2="500" y2="112" stroke="#f0883e"/>
    <text x="450" y="45" text-anchor="middle" font-size="9" fill="#f0883e">root: group B = {5,6}</text>

    <text x="320" y="195" text-anchor="middle" font-size="9" fill="#8b949e">find(4) walks 4-&gt;3-&gt;1, reaching root 1 -- same group as find(2)</text>
  </g>
</svg>

Two trees, two groups. `find` on any node in a tree returns that tree's root.

## 5. Runnable example

```java
// DisjointSet.java
public class DisjointSet {

    // Basic: naive disjoint-set with plain find and union, no optimizations.
    static class NaiveDSU {
        int[] parent;

        NaiveDSU(int n) {
            parent = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i; // each item starts as its own root
        }

        int find(int x) {
            while (parent[x] != x) x = parent[x];
            return x;
        }

        void union(int x, int y) {
            int rootX = find(x), rootY = find(y);
            if (rootX != rootY) parent[rootX] = rootY;
        }

        boolean connected(int x, int y) { return find(x) == find(y); }
    }

    static void basicLevel() {
        NaiveDSU dsu = new NaiveDSU(6);
        dsu.union(0, 1);
        dsu.union(1, 2);
        dsu.union(3, 4);

        System.out.println("basic: connected(0,2) -> " + dsu.connected(0, 2));
        System.out.println("basic: connected(0,3) -> " + dsu.connected(0, 3));
    }

    // Intermediate: track group sizes so you can answer "how big is x's group?" in O(1) after find.
    static class SizedDSU extends NaiveDSU {
        int[] size;

        SizedDSU(int n) {
            super(n);
            size = new int[n];
            java.util.Arrays.fill(size, 1);
        }

        void union(int x, int y) {
            int rootX = find(x), rootY = find(y);
            if (rootX == rootY) return;
            parent[rootX] = rootY;
            size[rootY] += size[rootX];
        }

        int groupSize(int x) { return size[find(x)]; }
    }

    static void intermediateLevel() {
        SizedDSU dsu = new SizedDSU(6);
        dsu.union(0, 1);
        dsu.union(1, 2);
        dsu.union(3, 4);

        System.out.println("intermediate: groupSize(0) -> " + dsu.groupSize(0));
        System.out.println("intermediate: groupSize(5) -> " + dsu.groupSize(5));
    }

    // Advanced: count the number of distinct groups remaining after a sequence of unions.
    static class CountingDSU extends NaiveDSU {
        int groupCount;

        CountingDSU(int n) { super(n); groupCount = n; }

        void union(int x, int y) {
            int rootX = find(x), rootY = find(y);
            if (rootX == rootY) return;
            parent[rootX] = rootY;
            groupCount--;
        }
    }

    static void advancedLevel() {
        CountingDSU dsu = new CountingDSU(6);
        System.out.println("advanced: initial groups -> " + dsu.groupCount);
        dsu.union(0, 1);
        dsu.union(1, 2);
        dsu.union(3, 4);
        System.out.println("advanced: groups after 3 unions -> " + dsu.groupCount);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java DisjointSet.java`

## 6. Walkthrough

Start with 6 items, each its own root: `parent = [0,1,2,3,4,5]`. Call `union(0,1)`: `find(0) = 0`, `find(1) = 1`; attach `parent[0] = 1`. Now `parent = [1,1,2,3,4,5]`. Call `union(1,2)`: `find(1) = 1`, `find(2) = 2`; attach `parent[1] = 2`. Now `parent = [1,2,2,3,4,5]`.

Check `connected(0, 2)`. `find(0)`: `0 -> parent[0]=1 -> parent[1]=2 -> parent[2]=2` (self), so root is `2`. `find(2)`: already root `2`. Both roots are `2`, so `connected` returns `true`.

Check `connected(0, 3)`. `find(0) = 2` (as above). `find(3) = 3` (still its own root, untouched). Roots differ, so `connected` returns `false`.

**Complexity.** With this naive version: `find` is `O(tree height)`, which can degrade to `O(n)` for a poorly-built chain. `union` is one `find` plus `O(1)` attach work. Space: `O(n)`. The next two pages — [union by rank/size](0164-union-by-rank-size.md) and [path compression](0165-path-compression.md) — fix the worst-case height problem.

## 7. Gotchas & takeaways

> Naive union-find (as shown here) can silently degrade to `O(n)` per `find` if you always attach the same side's root under the other — for example, always doing `parent[rootX] = rootY` regardless of which tree is taller. This is exactly why real implementations never skip union by rank/size in practice.

- `find` and `connected` never modify the group structure by themselves; only `union` changes it.
- A disjoint-set structure only answers "same group?" and "merge groups." It cannot list every member of a group in less than `O(n)` without extra bookkeeping (like the `size` array shown above, or a separate adjacency list per root).
- Prefer union-find over a full graph traversal (BFS/DFS) when you need to check connectivity **repeatedly** as edges are added incrementally, not just once on a fixed graph.
