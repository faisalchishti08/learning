---
card: leetcode-patterns
gi: 524
slug: union-find-template-disjoint-sets-with-union-by-rank-path-co
title: Union-Find — template: disjoint sets with union by rank + path compression
---

## 1. What it is

The union-find template is a small class with a `parent` array, a `rank` (or `size`) array, and three operations: `find`, `union`, and `connected`. Once memorized, applying it to a new problem is mostly about mapping problem items (strings, coordinates, accounts) to integer indices.

## 2. Why & when

Use the plain version (no rank, no path compression) only for tiny inputs, where its simplicity outweighs speed. Use the optimized version — path compression plus union by rank — whenever the input can be large, since it keeps every operation close to O(1) amortized instead of degrading toward O(n) on unlucky union orders.

## 3. Core concept

**Data.** `parent[i]` stores the parent of item `i` (or `i` itself, if `i` is a representative). `rank[i]` stores an upper bound on the height of the tree rooted at `i`, used only to decide which root to attach under which.

**`find(x)` with path compression.** Follow `parent[x]` upward until reaching a node that is its own parent — that is the representative. Then, on the way back, point every visited node directly at that representative. This flattens the tree, so future calls to `find` on those nodes finish in one step.

**`union(x, y)` with union by rank.** Find the representatives of `x` and `y`. If they are equal, the items are already in the same group; do nothing. Otherwise, attach the root with the smaller `rank` under the root with the larger `rank`. If the ranks are equal, attach either one under the other and increment the new root's rank by one.

**Why both optimizations together matter:** path compression alone can still leave the tree tall right before it flattens; union by rank alone still allows chains without compression. Combined, an amortized analysis shows the cost per operation grows slower than any constant number of steps — in practice, treat it as O(1) per operation for problems up to millions of items.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="find(D) walking up a chain, then path compression pointing every node directly at the root">
  <g font-family="sans-serif" font-size="13">
    <text x="150" y="20" fill="#e6edf3" text-anchor="middle">before find(D)</text>
    <circle cx="150" cy="150" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="150" y="155" fill="#e6edf3" text-anchor="middle">A</text>
    <circle cx="150" cy="100" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="150" y="105" fill="#e6edf3" text-anchor="middle">B</text>
    <line x1="150" y1="134" x2="150" y2="116" stroke="#8b949e"/>
    <circle cx="150" cy="50" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="150" y="55" fill="#e6edf3" text-anchor="middle">C</text>
    <line x1="150" y1="84" x2="150" y2="66" stroke="#8b949e"/>
    <circle cx="150" cy="0" r="14" fill="#161b22" stroke="#30363d"/>
    <text x="150" y="4" fill="#e6edf3" text-anchor="middle" font-size="11">D</text>
    <line x1="150" y1="36" x2="150" y2="14" stroke="#8b949e"/>
    <text x="500" y="20" fill="#e6edf3" text-anchor="middle">after find(D): path compressed</text>
    <circle cx="500" cy="150" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="500" y="155" fill="#e6edf3" text-anchor="middle">A</text>
    <circle cx="420" cy="90" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="420" y="95" fill="#e6edf3" text-anchor="middle">B</text>
    <line x1="490" y1="140" x2="430" y2="102" stroke="#8b949e"/>
    <circle cx="500" cy="90" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="500" y="95" fill="#e6edf3" text-anchor="middle">C</text>
    <line x1="500" y1="134" x2="500" y2="106" stroke="#8b949e"/>
    <circle cx="580" cy="90" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="580" y="95" fill="#e6edf3" text-anchor="middle">D</text>
    <line x1="510" y1="140" x2="570" y2="102" stroke="#8b949e"/>
  </g>
</svg>

Before `find(D)`, the chain `A <- B <- C <- D` is four levels deep. After `find(D)`, every visited node points directly at the root `A`, so the next `find` on any of them takes one step.

## 5. Runnable example

The full union-find template with path compression and union by rank.

```java
// UnionFindTemplate.java
public class UnionFindTemplate {

    static class DSU {
        int[] parent;
        int[] rank;
        int groupCount;

        DSU(int n) {
            parent = new int[n];
            rank = new int[n];
            groupCount = n;
            for (int i = 0; i < n; i++) parent[i] = i;
        }

        int find(int x) {
            if (parent[x] != x) {
                parent[x] = find(parent[x]); // path compression
            }
            return parent[x];
        }

        boolean union(int a, int b) {
            int rootA = find(a);
            int rootB = find(b);
            if (rootA == rootB) return false; // already same group

            if (rank[rootA] < rank[rootB]) {
                parent[rootA] = rootB;
            } else if (rank[rootA] > rank[rootB]) {
                parent[rootB] = rootA;
            } else {
                parent[rootB] = rootA;
                rank[rootA]++;
            }
            groupCount--;
            return true;
        }

        boolean connected(int a, int b) {
            return find(a) == find(b);
        }
    }

    public static void main(String[] args) {
        DSU dsu = new DSU(5); // items 0..4, each its own group

        System.out.println("groups before any union: " + dsu.groupCount);
        dsu.union(0, 1);
        dsu.union(1, 2);
        dsu.union(3, 4);
        System.out.println("groups after unions: " + dsu.groupCount);

        System.out.println("0 and 2 connected: " + dsu.connected(0, 2));
        System.out.println("0 and 3 connected: " + dsu.connected(0, 3));

        boolean merged = dsu.union(0, 3); // merges the last two groups
        System.out.println("union(0, 3) merged something new: " + merged);
        System.out.println("groups now: " + dsu.groupCount);
    }
}
```

**How to run:** save as `UnionFindTemplate.java`, then run `java UnionFindTemplate.java`.

## 6. Walkthrough

1. `new DSU(5)` starts with 5 items, each its own representative, so `groupCount` is 5.
2. `union(0, 1)` finds `0` and `1` as their own roots (equal rank, both 0), attaches `1` under `0`, and bumps `0`'s rank to 1. `groupCount` drops to 4.
3. `union(1, 2)` calls `find(1)`, which follows `parent[1] = 0` and returns `0`; it attaches `2` under `0` (lower rank than `0`'s rank of 1). `groupCount` drops to 3.
4. `union(3, 4)` merges the separate pair `{3, 4}`, dropping `groupCount` to 2.
5. `connected(0, 2)` calls `find(0)` (returns `0` directly) and `find(2)` (follows `parent[2] = 0`, returns `0`) — equal, so `true`.
6. `connected(0, 3)` compares roots `0` and `3` — different, so `false`.
7. `union(0, 3)` merges the last two groups into one, dropping `groupCount` to 1, and returns `true` since it merged new groups.

## 7. Gotchas & takeaways

> Gotcha: forgetting path compression's recursive assignment (`parent[x] = find(parent[x])`, not just `return find(parent[x])`) means the tree never flattens — every future `find` on `x` still walks the full original chain.

- `find` almost always needs path compression; `union` almost always needs union by rank (or by size) — skipping either one still works correctly, just slower on adversarial input.
- Track `groupCount`, decrementing it only when `union` actually merges two different roots — this gives you "number of connected components" for free, without a separate pass.
- Map non-integer items (strings, coordinates) to array indices with a `HashMap<Item, Integer>` before applying this exact template.
