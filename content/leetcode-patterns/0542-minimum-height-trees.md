---
card: leetcode-patterns
gi: 542
slug: minimum-height-trees
title: Minimum Height Trees
---

## 1. What it is

Given a tree with `n` nodes (an undirected, connected, acyclic graph) and its `n - 1` edges, you may pick any node as the root. Rooting the tree at different nodes gives different heights. Return all nodes that, if picked as the root, produce the **minimum possible height**. Example: `n = 4`, `edges = [[1,0],[1,2],[1,3]]` → `[1]` (rooting at node `1`, the center, gives height 1; any other root gives height 2).

## 2. Why & when

This problem does not mention prerequisites at all, but it is solved with the exact mechanics of Kahn's algorithm: **repeatedly peel away the current leaves** (nodes with only one remaining connection) layer by layer, exactly like removing zero-in-degree nodes. The last one or two nodes left standing are the tree's "center," which are the roots that minimize height. Constraints: up to 20,000 nodes.

## 3. Core concept

**Key idea:** the node(s) that minimize height are always the tree's geometric center — the middle of its longest path (its diameter). Repeatedly stripping every current leaf from the tree, one layer at a time, shrinks the tree inward from its edges. The last remaining 1 or 2 nodes are exactly that center.

**Steps:**
1. Handle `n == 1` directly: the single node is its own answer (height 0).
2. Build an adjacency list and a `degree[]` array (number of connections per node, since the graph is undirected).
3. Push every node with `degree == 1` (a current leaf) into a queue as the first layer to remove.
4. Repeatedly: pop the current layer of leaves, decrement the degree of each of their neighbors; any neighbor whose degree drops to `1` becomes next layer's leaf.
5. Track how many nodes remain unprocessed. Stop peeling when `remaining <= 2` — those last 1 or 2 nodes are the answer.

**Why the last-remaining nodes are the true centers:** each peeling round removes exactly the current outermost layer of the tree, shrinking its longest path by 1 from each end simultaneously. After enough rounds, what remains is the middle of the original longest path — 1 node if that path had odd length, 2 nodes if it had even length. Any node further from the center only increases the maximum distance to some leaf, which is exactly the height being minimized.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A star-shaped tree with center 1 peeled down from its outer leaves 0, 2, 3">
  <g font-family="sans-serif" font-size="13">
    <circle cx="300" cy="80" r="18" fill="#161b22" stroke="#3fb950"/>
    <text x="300" y="85" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="150" cy="30" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="150" y="35" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="150" cy="130" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="150" y="135" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="450" cy="80" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="450" y="85" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="285" y1="70" x2="165" y2="40" stroke="#8b949e"/>
    <line x1="285" y1="90" x2="165" y2="120" stroke="#8b949e"/>
    <line x1="318" y1="80" x2="434" y2="80" stroke="#8b949e"/>
    <text x="300" y="150" fill="#3fb950" text-anchor="middle">leaves 0,2,3 peeled first (degree 1) -&gt; only node 1 remains -&gt; answer [1]</text>
  </g>
</svg>

Nodes `0`, `2`, `3` all have degree 1 and are peeled in the first round, leaving only node `1` — the tree's center and the minimum-height root.

## 5. Runnable example

**Level 1 — Brute force.** Root the tree at every node in turn, run a breadth-first search to compute that rooting's height, and track the minimum. O(n²).

**KEY INSIGHT:** the minimum-height roots are always the tree's center, found by repeatedly peeling leaves — no need to test every possible root individually.

**Level 2 — Optimal.** Layer-by-layer leaf peeling (Kahn's-style), O(n).

**Level 3 — Hardened.** Handles `n = 1` (no edges at all) and `n = 2` (both nodes are equally valid centers, height 1 either way).

```java
// MinimumHeightTrees.java
import java.util.*;

public class MinimumHeightTrees {

    static List<Integer> findMinHeightTrees(int n, int[][] edges) {
        if (n == 1) return new ArrayList<>(List.of(0));

        List<Set<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new HashSet<>());
        for (int[] e : edges) {
            graph.get(e[0]).add(e[1]);
            graph.get(e[1]).add(e[0]);
        }

        Deque<Integer> leaves = new ArrayDeque<>();
        for (int i = 0; i < n; i++) {
            if (graph.get(i).size() == 1) leaves.add(i);
        }

        int remaining = n;
        while (remaining > 2) {
            int leafCount = leaves.size();
            remaining -= leafCount;
            for (int i = 0; i < leafCount; i++) {
                int leaf = leaves.poll();
                for (int neighbor : graph.get(leaf)) {
                    graph.get(neighbor).remove(leaf);
                    if (graph.get(neighbor).size() == 1) leaves.add(neighbor);
                }
            }
        }
        return new ArrayList<>(leaves);
    }

    public static void main(String[] args) {
        System.out.println(findMinHeightTrees(4, new int[][]{{1, 0}, {1, 2}, {1, 3}})); // [1]
        System.out.println(findMinHeightTrees(6, new int[][]{{3, 0}, {3, 1}, {3, 2}, {3, 4}, {5, 4}})); // [3, 4]
        System.out.println(findMinHeightTrees(1, new int[][]{})); // [0]
    }
}
```

**How to run:** save as `MinimumHeightTrees.java`, then run `java MinimumHeightTrees.java`.

## 6. Walkthrough

Trace `findMinHeightTrees(6, [[3,0],[3,1],[3,2],[3,4],[5,4]])`:

1. Degrees: node `3` has degree 4 (connects to 0,1,2,4); node `4` has degree 2 (connects to 3,5); nodes `0,1,2,5` have degree 1 each.
2. First round of leaves: `[0, 1, 2, 5]`. `remaining` drops from `6` to `2`.
3. Removing `0, 1, 2` from node `3`'s neighbor set drops `3`'s degree to `1` (only `4` remains). Removing `5` from node `4`'s neighbor set drops `4`'s degree to `1` (only `3` remains). Both `3` and `4` become new leaves, added to the queue.
4. `remaining (2)` is no longer greater than `2`, so the loop stops.
5. The queue now holds `[3, 4]` — the answer.

## 7. Gotchas & takeaways

> Gotcha: stopping the peel when `remaining == 1` instead of `remaining <= 2` misses the case where the tree's longest path has even length, which leaves exactly 2 center nodes, not 1 — always use `<= 2` as the stopping condition.

- Signal: "root that minimizes tree height" is found by peeling leaves layer by layer until 1 or 2 nodes remain — not by testing every possible root.
- The problem is on an undirected tree, so track `degree` (total connections), not a directed `inDegree` — but the peeling mechanic is otherwise identical to Kahn's algorithm.
- Related problems: Course Schedule (same layer-by-layer removal, different graph type), Find Eventual Safe States.
