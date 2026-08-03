---
card: data-structures
gi: 164
slug: union-by-rank-size
title: Union by rank / size
---

## 1. What it is

**Union by rank** (or **union by size**) is a rule for deciding *which* root to attach under the other during `union`. Instead of arbitrarily picking one, it always attaches the **shorter** (or **smaller**) tree under the **taller** (or **larger**) one. This single rule keeps every tree in a disjoint-set structure short.

## 2. Why & when

Plain [union](0163-find-union-operations.md), without this rule, can build a tall chain if you always attach the same side — for example, always `union(0,1)`, then `union(1,2)`, then `union(2,3)`, always folding the newer node's root under the growing chain's root, produces a tree of height `n`. `find` on the deepest node then costs `O(n)`. Union by rank guarantees the tree height never exceeds `O(log n)`, which alone brings every `find` and `union` down to `O(log n)`.

## 3. Core concept

**The shape.** Alongside `parent[]`, keep a `rank[]` array (an upper bound on each root's tree height) or a `size[]` array (the number of nodes in each root's tree). Either works; size is more intuitive, rank is the classic textbook choice.

**The rule.** When `union(x, y)` finds two different roots `rootX` and `rootY`, compare their rank (or size). Attach the smaller-rank root under the larger-rank root: `parent[smaller] = larger`. If the ranks are equal, attach either way and increment the surviving root's rank by one.

**Why this bounds the height.** A tree can only grow taller when it merges with a tree of **equal or greater** height, and even then the new height only grows by `1`. Doubling a tree's size (the size-based version) at minimum every time its height increases means a tree of height `h` must contain at least `2^h` nodes — so for `n` total nodes, height can never exceed `log2(n)`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Union by rank attaching the shorter tree under the taller tree, versus naive union creating a tall chain">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20" fill="#f44336">Naive (bad): always chain</text>
    <circle cx="60" cy="40" r="12" fill="#0d1117" stroke="#8b949e"/><text x="60" y="43" text-anchor="middle" font-size="8">1</text>
    <circle cx="60" cy="80" r="12" fill="#0d1117" stroke="#8b949e"/><text x="60" y="83" text-anchor="middle" font-size="8">2</text>
    <circle cx="60" cy="120" r="12" fill="#0d1117" stroke="#8b949e"/><text x="60" y="123" text-anchor="middle" font-size="8">3</text>
    <circle cx="60" cy="160" r="12" fill="#0d1117" stroke="#8b949e"/><text x="60" y="163" text-anchor="middle" font-size="8">4</text>
    <line x1="60" y1="52" x2="60" y2="68" stroke="#f44336"/>
    <line x1="60" y1="92" x2="60" y2="108" stroke="#f44336"/>
    <line x1="60" y1="132" x2="60" y2="148" stroke="#f44336"/>
    <text x="60" y="190" text-anchor="middle" font-size="8" fill="#f44336">height 4, find(4) = 4 hops</text>

    <text x="400" y="20" fill="#3fb950">Union by rank (good): balanced</text>
    <circle cx="400" cy="50" r="14" fill="#161b22" stroke="#3fb950"/><text x="400" y="53" text-anchor="middle" font-size="8">1</text>
    <circle cx="350" cy="110" r="12" fill="#0d1117" stroke="#8b949e"/><text x="350" y="113" text-anchor="middle" font-size="8">2</text>
    <circle cx="450" cy="110" r="12" fill="#0d1117" stroke="#8b949e"/><text x="450" y="113" text-anchor="middle" font-size="8">3</text>
    <circle cx="325" cy="160" r="12" fill="#0d1117" stroke="#8b949e"/><text x="325" y="163" text-anchor="middle" font-size="8">4</text>
    <line x1="400" y1="63" x2="350" y2="98" stroke="#3fb950"/>
    <line x1="400" y1="63" x2="450" y2="98" stroke="#3fb950"/>
    <line x1="350" y1="122" x2="325" y2="148" stroke="#3fb950"/>
    <text x="400" y="190" text-anchor="middle" font-size="8" fill="#3fb950">height 3 for same 4 nodes, stays O(log n)</text>
  </g>
</svg>

Attaching the smaller tree under the larger one keeps height logarithmic instead of linear.

## 5. Runnable example

```java
// UnionByRank.java
public class UnionByRank {

    // Basic: union by rank, attaching the shorter tree under the taller one.
    static class RankDSU {
        int[] parent, rank;

        RankDSU(int n) {
            parent = new int[n];
            rank = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }

        int find(int x) {
            while (parent[x] != x) x = parent[x];
            return x;
        }

        void union(int x, int y) {
            int rootX = find(x), rootY = find(y);
            if (rootX == rootY) return;
            if (rank[rootX] < rank[rootY]) {
                parent[rootX] = rootY;
            } else if (rank[rootX] > rank[rootY]) {
                parent[rootY] = rootX;
            } else {
                parent[rootY] = rootX;
                rank[rootX]++;
            }
        }
    }

    static void basicLevel() {
        RankDSU dsu = new RankDSU(5);
        dsu.union(0, 1);
        dsu.union(2, 3);
        dsu.union(0, 2); // merges two rank-1 trees -> root's rank becomes 2
        System.out.println("basic: rank of root after merging two height-1 trees -> " + dsu.rank[dsu.find(0)]);
    }

    // Intermediate: union by size, attaching the smaller tree under the larger one, tracking group sizes.
    static class SizeDSU {
        int[] parent, size;

        SizeDSU(int n) {
            parent = new int[n];
            size = new int[n];
            for (int i = 0; i < n; i++) { parent[i] = i; size[i] = 1; }
        }

        int find(int x) {
            while (parent[x] != x) x = parent[x];
            return x;
        }

        void union(int x, int y) {
            int rootX = find(x), rootY = find(y);
            if (rootX == rootY) return;
            if (size[rootX] < size[rootY]) {
                parent[rootX] = rootY;
                size[rootY] += size[rootX];
            } else {
                parent[rootY] = rootX;
                size[rootX] += size[rootY];
            }
        }
    }

    static void intermediateLevel() {
        SizeDSU dsu = new SizeDSU(6);
        dsu.union(0, 1);
        dsu.union(1, 2); // group {0,1,2} now size 3
        dsu.union(3, 4); // group {3,4} size 2
        dsu.union(2, 3); // smaller group {3,4} attaches under larger {0,1,2}

        System.out.println("intermediate: final root of 4 -> " + dsu.find(4));
        System.out.println("intermediate: final group size at root -> " + dsu.size[dsu.find(0)]);
    }

    // Advanced: measure the height difference naive union vs union-by-size produces on a worst-case chain input.
    static int treeHeight(int[] parent, int node) {
        int height = 0;
        while (parent[node] != node) { node = parent[node]; height++; }
        return height;
    }

    static void advancedLevel() {
        int n = 16;
        int[] naiveParent = new int[n];
        for (int i = 0; i < n; i++) naiveParent[i] = i;
        for (int i = 1; i < n; i++) naiveParent[i - 1] = i; // worst case: always attach old root under new node

        SizeDSU sized = new SizeDSU(n);
        for (int i = 1; i < n; i++) sized.union(i - 1, i);

        System.out.println("advanced: naive chain height for node 0 -> " + treeHeight(naiveParent, 0));
        System.out.println("advanced: union-by-size height for node 0 -> " + treeHeight(sized.parent, 0));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java UnionByRank.java`

## 6. Walkthrough

Start with 5 singletons, all `rank = 0`. `union(0,1)`: both roots have rank `0` (a tie), so attach `parent[1] = 0` and bump `rank[0]` to `1`. `union(2,3)`: same tie-breaking, `parent[3] = 2`, `rank[2] = 1`.

Now `union(0, 2)`: `find(0) = 0` with `rank[0] = 1`; `find(2) = 2` with `rank[2] = 1`. Ranks tie again, so attach `parent[2] = 0` and bump `rank[0]` to `2`. The combined tree now has 4 nodes at height `2` — much shorter than the height-`3` chain a naive always-attach-right approach would have produced for the same sequence.

Trace the "advanced" worst-case scenario: build a naive chain by always doing `parent[i-1] = i` (attach the old root under each new node), which produces height `n-1` for a line of `n` nodes. Compare against union by size on the same merge sequence: because size-based union always attaches the smaller side under the larger, the resulting tree height grows only logarithmically, staying near `log2(n)` instead of `n-1`.

**Complexity.** With union by rank/size alone (no path compression): both `find` and `union` are `O(log n)`, because tree height is bounded by `log2(n)`. Combined with [path compression](0165-path-compression.md), this drops further to [near-constant amortized time](0166-near-constant-amortized-complexity-inverse-ackermann.md).

## 7. Gotchas & takeaways

> Union by size and union by rank are both correct and both give `O(log n)` height bounds — do not mix them carelessly in one implementation. If you track `size`, keep incrementing it correctly on every merge (`size[newRoot] += size[oldRoot]`); a stale `size` value silently breaks the comparison's usefulness without breaking correctness of `find`/`union` themselves.

- `rank` is only an upper bound on height, not an exact height, once path compression starts flattening trees — this is expected and does not break the algorithm.
- Union by rank/size alone already fixes the worst-case `O(n)` height problem. Path compression is a separate, complementary optimization, not a requirement for correctness.
- Always attach based on the **roots'** rank/size (found via `find`), never the original arguments' — the same rule that matters for [find & union](0163-find-union-operations.md) in general.
