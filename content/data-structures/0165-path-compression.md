---
card: data-structures
gi: 165
slug: path-compression
title: Path compression
---

## 1. What it is

**Path compression** is an optimization applied during `find`: after walking up from a node to its root, re-point every node on that path directly to the root. The next time any of those nodes calls `find`, it reaches the root in one step instead of retracing the whole path.

## 2. Why & when

Even with [union by rank/size](0164-union-by-rank-size.md) bounding tree height to `O(log n)`, repeated `find` calls on deep nodes still cost `O(log n)` each time. Path compression flattens the tree as a side effect of every `find` call, so trees that start with some height quickly become almost flat after a few queries. Combined with union by rank/size, this gives amortized **near-constant** time per operation — the best known bound for this problem.

## 3. Core concept

**The shape.** The same `parent[]` array as plain union-find. Path compression changes nothing structurally; it only rewrites pointers that were already logically implied (every node on a find-path was always in the same group as the root).

**The invariant.** After `find(x)` runs, every node visited on the path from `x` to the root now points **directly** to the root. The group membership does not change — only how quickly future lookups discover it.

**The two common implementations.**
- **Recursive (path compression proper):** `find(x)` recurses to the root first, then, as the recursion unwinds, sets `parent[x] = root` for every node visited. This achieves full flattening in one pass.
- **Iterative (path halving/splitting):** a loop-based version that repoints each node to its grandparent as it walks up, avoiding recursion depth issues on very large chains, at the cost of slightly less aggressive flattening per call.

**Why it helps future calls, not just the current one.** The first `find` on a deep node still walks the full original path — compression cannot make that first call faster than the tree's current height. Its benefit shows up on **every subsequent** `find` for any node that was on that path: those nodes now resolve in `O(1)`.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Path compression flattening a chain: before find(4), a tall chain; after find(4), every visited node points directly to the root">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">Before find(4):</text>
    <circle cx="60" cy="40" r="14" fill="#161b22" stroke="#79c0ff"/><text x="60" y="44" text-anchor="middle" font-size="9">1</text>
    <circle cx="60" cy="90" r="14" fill="#0d1117" stroke="#8b949e"/><text x="60" y="94" text-anchor="middle" font-size="9">2</text>
    <circle cx="60" cy="140" r="14" fill="#0d1117" stroke="#8b949e"/><text x="60" y="144" text-anchor="middle" font-size="9">3</text>
    <circle cx="60" cy="190" r="14" fill="#0d1117" stroke="#8b949e"/><text x="60" y="194" text-anchor="middle" font-size="9">4</text>
    <line x1="60" y1="54" x2="60" y2="76" stroke="#79c0ff"/>
    <line x1="60" y1="104" x2="60" y2="126" stroke="#79c0ff"/>
    <line x1="60" y1="154" x2="60" y2="176" stroke="#79c0ff"/>

    <text x="330" y="20">After find(4): all point to root 1</text>
    <circle cx="330" cy="40" r="14" fill="#161b22" stroke="#3fb950"/><text x="330" y="44" text-anchor="middle" font-size="9">1</text>
    <circle cx="260" cy="110" r="14" fill="#0d1117" stroke="#8b949e"/><text x="260" y="114" text-anchor="middle" font-size="9">2</text>
    <circle cx="330" cy="110" r="14" fill="#0d1117" stroke="#8b949e"/><text x="330" y="114" text-anchor="middle" font-size="9">3</text>
    <circle cx="400" cy="110" r="14" fill="#0d1117" stroke="#8b949e"/><text x="400" y="114" text-anchor="middle" font-size="9">4</text>
    <line x1="330" y1="54" x2="260" y2="96" stroke="#3fb950"/>
    <line x1="330" y1="54" x2="330" y2="96" stroke="#3fb950"/>
    <line x1="330" y1="54" x2="400" y2="96" stroke="#3fb950"/>
    <text x="330" y="200" text-anchor="middle" font-size="9" fill="#3fb950">next find(2), find(3), find(4) are all O(1)</text>
  </g>
</svg>

One `find(4)` call rewires every node it visits to point straight at the root.

## 5. Runnable example

```java
// PathCompression.java
public class PathCompression {

    // Basic: recursive path compression during find.
    static class RecursiveDSU {
        int[] parent;

        RecursiveDSU(int n) {
            parent = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }

        int find(int x) {
            if (parent[x] != x) {
                parent[x] = find(parent[x]); // recurse to root, then repoint x directly to it
            }
            return parent[x];
        }

        void union(int x, int y) {
            int rootX = find(x), rootY = find(y);
            if (rootX != rootY) parent[rootX] = rootY;
        }
    }

    static void basicLevel() {
        RecursiveDSU dsu = new RecursiveDSU(5);
        // Manually build a chain: 0 -> 1 -> 2 -> 3 -> 4 (worst case shape)
        dsu.parent = new int[]{1, 2, 3, 4, 4};

        System.out.println("basic: parent before find(0) -> " + java.util.Arrays.toString(dsu.parent));
        dsu.find(0);
        System.out.println("basic: parent after find(0)  -> " + java.util.Arrays.toString(dsu.parent));
    }

    // Intermediate: iterative path halving, an alternative that avoids recursion.
    static class IterativeDSU {
        int[] parent;

        IterativeDSU(int n) {
            parent = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }

        int find(int x) {
            while (parent[x] != x) {
                parent[x] = parent[parent[x]]; // point to grandparent, halving path length each step
                x = parent[x];
            }
            return x;
        }
    }

    static void intermediateLevel() {
        IterativeDSU dsu = new IterativeDSU(5);
        dsu.parent = new int[]{1, 2, 3, 4, 4};

        System.out.println("intermediate: parent before find(0) -> " + java.util.Arrays.toString(dsu.parent));
        dsu.find(0);
        System.out.println("intermediate: parent after find(0)  -> " + java.util.Arrays.toString(dsu.parent));
    }

    // Advanced: combine path compression with union by rank, the standard production-grade disjoint-set.
    static class OptimizedDSU {
        int[] parent, rank;

        OptimizedDSU(int n) {
            parent = new int[n];
            rank = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }

        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }

        void union(int x, int y) {
            int rootX = find(x), rootY = find(y);
            if (rootX == rootY) return;
            if (rank[rootX] < rank[rootY]) parent[rootX] = rootY;
            else if (rank[rootX] > rank[rootY]) parent[rootY] = rootX;
            else { parent[rootY] = rootX; rank[rootX]++; }
        }
    }

    static void advancedLevel() {
        OptimizedDSU dsu = new OptimizedDSU(8);
        for (int i = 1; i < 8; i++) dsu.union(i - 1, i); // union in a line, but rank keeps it shallow

        int rootBefore = dsu.parent[7];
        dsu.find(7);
        System.out.println("advanced: parent[7] before extra find (already flat from union-by-rank) -> " + rootBefore);
        System.out.println("advanced: find(0) == find(7) -> " + (dsu.find(0) == dsu.find(7)));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java PathCompression.java`

## 6. Walkthrough

Build a deliberately tall chain: `parent = [1, 2, 3, 4, 4]`, meaning `0 -> 1 -> 2 -> 3 -> 4` (self-root). Call `find(0)` using the recursive version. It recurses: `find(0)` calls `find(1)`, which calls `find(2)`, which calls `find(3)`, which calls `find(4)` — and `4` is its own parent, so the recursion bottoms out and returns `4`.

As the recursion **unwinds**, each frame sets its own node's parent directly to the returned root: `parent[3] = 4`, then `parent[2] = 4`, then `parent[1] = 4`, then `parent[0] = 4`. After this single `find(0)` call, `parent = [4, 4, 4, 4, 4]` — every node points straight at the root.

The next call, `find(2)`, now costs exactly one step: `parent[2]` is already `4`, so it returns immediately, no chain to walk. The `O(log n)` (or worse) cost of the very first `find` amortizes across every future `find` on the same nodes.

**Complexity.** A single `find` with path compression still costs `O(tree height)` in the worst case (the compression happens *during* the walk, not before it). But combined with [union by rank/size](0164-union-by-rank-size.md), the amortized cost over a sequence of `m` operations drops to `O(α(n))` per operation — see [near-constant amortized complexity](0166-near-constant-amortized-complexity-inverse-ackermann.md) for what `α` means.

## 7. Gotchas & takeaways

> Path compression alone (without union by rank/size) still gives a good amortized bound, but combining both gives the best known bound. Do not skip union by rank/size just because path compression is in place — they solve complementary problems (tree height growth vs. flattening after the fact).

- The recursive version (`parent[x] = find(parent[x])`) is the cleanest to read but can hit Java's stack limit on extremely long chains (millions of nodes in a pathological worst case); the iterative path-halving version avoids this.
- Path compression only triggers on `find`. If your code only ever calls `union` and never queries connectivity with `find`, the trees never flatten.
- This optimization does not change what any operation *returns* — only how fast future calls run. It is always safe to add to an existing correct union-find implementation.
