---
card: leetcode-patterns
gi: 525
slug: union-find-complexity-near-o-1-amortized-per-operation
title: Union-Find — complexity: near O(1) amortized per operation
---

## 1. What it is

This page explains why `find` and `union` run in near-constant time once path compression and union by rank are both applied, and lists the named problems that use the pattern.

## 2. Why & when

Interviewers often ask "what is the time complexity of union-find?" as a follow-up. The honest, precise answer is "O(α(n)) amortized per operation," where α is the inverse Ackermann function — but what matters in an interview is explaining *why* it behaves like a constant in practice, not memorizing the Greek letter.

## 3. Core concept

**Without any optimization, a chain can form.** If you always attach the new root under the existing root in the same order, `union(0,1)`, `union(1,2)`, `union(2,3)`, ..., you build a straight-line chain n nodes deep. A `find` on the deepest node then costs O(n) — no better than a linked list.

**Union by rank keeps trees shallow.** By always attaching the smaller (lower-rank) tree under the larger one, no tree's height can more than double from any single union, and it can only double log(n) times. This alone bounds every tree's height at O(log n), so `find` costs O(log n) worst case, even before adding path compression.

**Path compression flattens trees on every read.** Every `find` call, while walking up to the representative, rewires every visited node to point directly at that representative. Later `find` calls on those same nodes then cost O(1).

**Why "amortized" and not just "constant":** the very first `find` on a tall tree still costs O(log n) to walk up and flatten it. But that cost is paid once — every subsequent `find` on any of the nodes it touched is now O(1). Averaged (amortized) across a long sequence of `union`/`find` calls, the formal bound works out to O(α(n)) per operation. The inverse Ackermann function α(n) grows so slowly that it stays below 5 for any n you could actually store in memory — so in practice, treat every operation as O(1).

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cost per find call dropping toward constant time as path compression flattens the tree over repeated calls">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Repeated find() calls on the same growing tree:</text>
    <text x="20" y="50" fill="#f0883e">1st find on a deep node: walks up O(log n) nodes, then compresses them</text>
    <text x="20" y="75" fill="#79c0ff">2nd find on a compressed node: O(1), points straight at the root</text>
    <text x="20" y="100" fill="#79c0ff">3rd find on a compressed node: O(1)</text>
    <text x="20" y="130" fill="#3fb950">amortized over many calls: effectively O(1) each, formally O(inverse-Ackermann(n))</text>
  </g>
</svg>

The first `find` on any node pays the flattening cost; every later `find` on that node (or one that shares its path) is O(1).

## 5. Runnable example

A union-find instance that counts total parent-pointer hops across many `find` calls, showing the average hops per call trending toward a small constant as more calls are made.

```java
// UnionFindComplexity.java
public class UnionFindComplexity {

    static class DSU {
        int[] parent;
        int[] rank;
        long hopCount = 0;

        DSU(int n) {
            parent = new int[n];
            rank = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }

        int find(int x) {
            if (parent[x] != x) {
                hopCount++;
                parent[x] = find(parent[x]); // path compression
            }
            return parent[x];
        }

        void union(int a, int b) {
            int rootA = find(a);
            int rootB = find(b);
            if (rootA == rootB) return;
            if (rank[rootA] < rank[rootB]) {
                parent[rootA] = rootB;
            } else if (rank[rootA] > rank[rootB]) {
                parent[rootB] = rootA;
            } else {
                parent[rootB] = rootA;
                rank[rootA]++;
            }
        }
    }

    public static void main(String[] args) {
        int n = 1000;
        DSU dsu = new DSU(n);

        // build one big chain-prone sequence of unions
        for (int i = 0; i < n - 1; i++) dsu.union(i, i + 1);

        long totalCalls = 0;
        long totalHops = 0;
        for (int round = 0; round < 5; round++) {
            for (int i = 0; i < n; i++) {
                long before = dsu.hopCount;
                dsu.find(i);
                totalHops += dsu.hopCount - before;
                totalCalls++;
            }
            System.out.printf("round %d: avg hops per find so far = %.3f%n",
                    round, (double) totalHops / totalCalls);
        }
    }
}
```

**How to run:** save as `UnionFindComplexity.java`, then run `java UnionFindComplexity.java`.

## 6. Walkthrough

1. Building `n - 1` unions in sequence, `union(0,1)`, `union(1,2)`, ..., creates the exact adversarial pattern that would form a deep chain without union by rank.
2. Round 0 calls `find` on every node from `0` to `n-1`. The first few calls walk up several hops before path compression flattens what they touch; the average hops per call is still noticeably above 0.
3. By round 1, most nodes already point close to the representative from round 0's compressions, so the average hops per call drops sharply.
4. By round 4, nearly every `find` call costs 0 or 1 extra hop, since the tree is almost fully flattened — the running average has converged to a small constant.
5. This demonstrates the amortized bound directly: the expensive early calls are outweighed by the overwhelming majority of near-free later calls.

## 7. Gotchas & takeaways

> Gotcha: quoting "O(1)" for a *single* `find` call on a cold, un-compressed structure overstates it — the true bound is amortized across a sequence of calls; a lone `find` on a deep, never-before-touched chain can still cost O(log n).

- Time: O(α(n)) amortized per `find`/`union` call with both optimizations, which is effectively O(1) for any realistic input size; O(log n) with only union by rank; O(n) worst case with neither.
- Space: O(n) for the `parent` and `rank` arrays.
- Reference problems that use this pattern: Redundant Connection, Number of Connected Components in an Undirected Graph, Accounts Merge, Most Stones Removed with Same Row or Column, Satisfiability of Equality Equations, Graph Valid Tree, Smallest String With Swaps, Evaluate Division, Redundant Connection II.
