---
card: leetcode-patterns
gi: 173
slug: count-unreachable-pairs-of-nodes-in-an-undirected-graph
title: Count Unreachable Pairs of Nodes in an Undirected Graph
---

## 1. What it is

Given `n` nodes labeled `0` to `n-1` and a list of undirected `edges`, two nodes are "unreachable" if no path connects them. Return the number of pairs of nodes that are unreachable from each other. Example: `n = 3`, `edges = [[0,1]]` → `2` (pairs `(0,2)` and `(1,2)` are unreachable).

## 2. Why & when

The graph naturally splits into connected components — groups of nodes each fully reachable from one another, with no edges between groups. Any two nodes in DIFFERENT components are unreachable; nodes in the SAME component are always reachable. So the problem reduces to: find component sizes, then count cross-component pairs.

## 3. Core concept

**Key idea:** find every connected component's size using DFS or BFS. For each component, every node in it is reachable from every other node in it, but unreachable from all nodes outside it. Sum, for each component, its size times the count of nodes NOT yet counted in earlier components — a running-total trick avoids double-counting pairs.

**Steps:**
1. Run DFS/BFS from each unvisited node, marking its whole component visited and recording the component's size.
2. Maintain a running total `seenSoFar` of nodes in components already processed.
3. For each new component of size `s`, add `s * seenSoFar` to the answer (every node in this component pairs with every node in a PRIOR component).
4. Add `s` to `seenSoFar`, then move to the next component.
5. Return the accumulated total.

**Why it is correct:** every unreachable pair spans exactly two different components. Processing components one at a time and multiplying the new component's size by the total size of all previously-seen components counts each cross-component pair exactly once, since `(A, B)` from components `X` and `Y` is only counted when the later of `X`/`Y` is processed.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two connected components; nodes across components are unreachable pairs">
  <g font-family="sans-serif" font-size="12">
    <circle cx="70" cy="60" r="14" fill="#161b22" stroke="#3fb950"/><text x="70" y="64" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="140" cy="60" r="14" fill="#161b22" stroke="#3fb950"/><text x="140" y="64" fill="#e6edf3" text-anchor="middle">1</text>
    <line x1="84" y1="60" x2="126" y2="60" stroke="#3fb950"/>
    <circle cx="320" cy="60" r="14" fill="#161b22" stroke="#79c0ff"/><text x="320" y="64" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="10" y="15" fill="#e6edf3">component {0,1} size 2, component {2} size 1 -- unreachable pairs = 2*1 = 2</text>
  </g>
</svg>

Component `{0,1}` (size 2) and component `{2}` (size 1) contribute `2 × 1 = 2` unreachable pairs.

## 5. Runnable example

```java
// CountUnreachablePairsOfNodes.java
import java.util.*;

public class CountUnreachablePairsOfNodes {

    // Level 1 -- Brute force: check every pair (i, j) with a fresh
    // BFS/DFS to test reachability, counting the unreachable ones.
    // Correct, but O(n^2) reachability checks, each themselves O(n +
    // e), is far too slow for large n, and repeats the same component
    // discovery work over and over.

    // KEY INSIGHT: reachability is all-or-nothing WITHIN a connected
    // component -- computing component SIZES once, then combining them
    // with simple arithmetic, replaces n^2 reachability checks with one
    // graph traversal pass.

    // Level 2 -- Optimal: find component sizes, combine with running
    // total.
    static long countPairs(int n, int[][] edges) {
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        for (int[] e : edges) {
            graph.get(e[0]).add(e[1]);
            graph.get(e[1]).add(e[0]);
        }

        boolean[] visited = new boolean[n];
        long unreachablePairs = 0;
        long seenSoFar = 0;

        for (int i = 0; i < n; i++) {
            if (visited[i]) continue;
            int size = bfsComponentSize(graph, visited, i);
            unreachablePairs += (long) size * seenSoFar;
            seenSoFar += size;
        }
        return unreachablePairs;
    }

    static int bfsComponentSize(List<List<Integer>> graph, boolean[] visited, int start) {
        visited[start] = true;
        Queue<Integer> queue = new LinkedList<>();
        queue.add(start);
        int size = 0;
        while (!queue.isEmpty()) {
            int cur = queue.poll();
            size++;
            for (int next : graph.get(cur)) {
                if (!visited[next]) {
                    visited[next] = true;
                    queue.add(next);
                }
            }
        }
        return size;
    }

    // Level 3 -- Hardened: use `long` for the running total and the
    // answer, since n up to 10^5 makes the pair count exceed the range
    // of a 32-bit int.

    public static void main(String[] args) {
        System.out.println(countPairs(3, new int[][]{{0,1}})); // 2
        System.out.println(countPairs(7, new int[][]{{0,2},{0,5},{2,4},{1,6},{5,4}})); // 14
        System.out.println(countPairs(5, new int[][]{})); // 10
    }
}
```

**How to run:** `java CountUnreachablePairsOfNodes.java`

## 6. Walkthrough

Trace `n = 3`, `edges = [[0,1]]`:

| Step | Node | Component found | size | seenSoFar before | pairs added | seenSoFar after |
|---|---|---|---|---|---|---|
| 1 | 0 (unvisited) | `{0,1}` | 2 | 0 | 2×0=0 | 2 |
| 2 | 1 | already visited, skip | — | — | — | — |
| 3 | 2 (unvisited) | `{2}` | 1 | 2 | 1×2=2 | 3 |

Total unreachable pairs = `0 + 2 = 2`. Time complexity is O(n + e), since BFS visits every node and edge exactly once across all components; space is O(n + e) for the adjacency list and visited array.

## 7. Gotchas & takeaways

> Multiplying each component's size by the TOTAL node count `n` (instead of `seenSoFar`, the running total of PRIOR components only) double-counts every cross-component pair twice, once from each side.

- The running-total trick — multiply by nodes seen so far, not all nodes — is the key to counting each pair exactly once without a nested loop over components.
- Use `long` for the answer; component-size products can exceed `Integer.MAX_VALUE` for large `n`.
- Related problems: Number of Provinces (counting components directly), Number of Islands (grid version of component counting).
