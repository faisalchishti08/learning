---
card: leetcode-patterns
gi: 169
slug: all-paths-from-source-to-target
title: All Paths From Source to Target
---

## 1. What it is

Given a directed acyclic graph (DAG) of `n` nodes labeled `0` to `n-1`, given as an adjacency list `graph`, return every possible path from node `0` to node `n-1`. Example: `graph = [[1,2],[3],[3],[]]` → `[[0,1,3],[0,2,3]]`.

## 2. Why & when

Unlike "does a path exist" (BFS/DFS to a boolean), this problem asks for EVERY path. That means you cannot stop at the first hit — you must explore all branches and record each complete path, which is a job for DFS with backtracking, not BFS.

## 3. Core concept

**Key idea:** DFS from node `0`, keeping a running path list. Every time the DFS adds `n-1` to the path, save a copy of the path. Because the graph is a DAG (no cycles), no visited-set is even needed — DFS naturally terminates.

**Steps:**
1. Start DFS at node `0` with a path list containing just `0`.
2. At each node, if it equals `n-1` (the target), save a COPY of the current path list to the results.
3. Otherwise, for each neighbor, add it to the path, recurse, then remove it (backtrack) before trying the next neighbor.
4. Return the collected results after DFS finishes exploring from `0`.

**Why it is correct:** DFS with backtracking explores every possible sequence of edges from `0`. Because the graph is acyclic, every branch terminates, and copying the path at each node `n-1` reached captures every distinct route.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DFS backtracking exploring two branches, each ending at target node 3">
  <g font-family="sans-serif" font-size="12">
    <circle cx="60" cy="100" r="18" fill="#161b22" stroke="#3fb950"/><text x="60" y="104" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="180" cy="50" r="18" fill="#161b22" stroke="#79c0ff"/><text x="180" y="54" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="180" cy="150" r="18" fill="#161b22" stroke="#79c0ff"/><text x="180" y="154" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="320" cy="100" r="18" fill="#161b22" stroke="#e3b341"/><text x="320" y="104" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="76" y1="90" x2="164" y2="58" stroke="#8b949e"/>
    <line x1="76" y1="110" x2="164" y2="142" stroke="#8b949e"/>
    <line x1="196" y1="58" x2="304" y2="98" stroke="#8b949e"/>
    <line x1="196" y1="142" x2="304" y2="102" stroke="#8b949e"/>
    <text x="10" y="15" fill="#e6edf3">two DFS branches, each reaching target 3: paths [0,1,3] and [0,2,3]</text>
  </g>
</svg>

DFS follows each branch to completion, records the path on reaching node `3`, then backtracks to try the next branch.

## 5. Runnable example

```java
// AllPathsFromSourceToTarget.java
import java.util.*;

public class AllPathsFromSourceToTarget {

    // Level 1 -- Brute force: BFS tracking full paths in the queue
    // instead of just nodes, enqueuing a growing path at every step.
    // Correct, but keeping full path copies in a queue burns much more
    // memory than DFS's single mutable path plus backtracking, and
    // gives up DFS's simpler natural recursion for this kind of
    // exhaustive enumeration.

    // KEY INSIGHT: DFS with a SINGLE shared path list, adding a node
    // before recursing and removing it after (backtracking), explores
    // every route using only one path buffer instead of copying a new
    // one per queue entry.

    // Level 2 -- Optimal: DFS + backtracking.
    static List<List<Integer>> allPathsSourceTarget(int[][] graph) {
        List<List<Integer>> result = new ArrayList<>();
        List<Integer> path = new ArrayList<>();
        path.add(0);
        dfs(graph, 0, path, result);
        return result;
    }

    static void dfs(int[][] graph, int node, List<Integer> path, List<List<Integer>> result) {
        int target = graph.length - 1;
        if (node == target) {
            result.add(new ArrayList<>(path));
            return;
        }
        for (int next : graph[node]) {
            path.add(next);
            dfs(graph, next, path, result);
            path.remove(path.size() - 1);
        }
    }

    // Level 3 -- Hardened: works even if node 0 has no outgoing edges
    // (result stays empty) and if node 0 IS the target for n == 1,
    // since the base case check happens before the neighbor loop.

    public static void main(String[] args) {
        System.out.println(allPathsSourceTarget(new int[][]{{1,2},{3},{3},{}})); // [[0,1,3],[0,2,3]]
        System.out.println(allPathsSourceTarget(new int[][]{{4,3,1},{3,2,4},{3},{4},{}}));
        // [[0,4],[0,3,4],[0,1,3,4],[0,1,2,3,4],[0,1,4]]
    }
}
```

**How to run:** `java AllPathsFromSourceToTarget.java`

## 6. Walkthrough

Trace `graph = [[1,2],[3],[3],[]]`:

| Step | Call | path | Action |
|---|---|---|---|
| 1 | dfs(0) | [0] | not target, try neighbor 1 |
| 2 | dfs(1) | [0,1] | not target, try neighbor 3 |
| 3 | dfs(3) | [0,1,3] | target! save `[0,1,3]`, return |
| 4 | back in dfs(1) | [0,1] | remove 3, no more neighbors, return |
| 5 | back in dfs(0) | [0] | remove 1, try neighbor 2 |
| 6 | dfs(2) | [0,2] | not target, try neighbor 3 |
| 7 | dfs(3) | [0,2,3] | target! save `[0,2,3]`, return |

Time complexity is O(2^n · n) in the worst case (every subset of intermediate nodes can form a path, each copied in O(n)); space is O(n) for the recursion stack plus the output.

## 7. Gotchas & takeaways

> Adding `path` itself (not `new ArrayList<>(path)`) to the results list stores a reference, not a snapshot — later backtracking mutates that same list, corrupting every saved "path" to look identical.

- Always copy the path when saving it; the shared mutable list is only valid at the exact moment you save it.
- Because the graph is guaranteed acyclic, no visited-set is needed — a cyclic graph would need one to avoid infinite recursion.
- Related problems: Word Ladder II (DFS backtracking to enumerate ALL shortest paths, after a BFS layering pass), Reconstruct Itinerary (DFS with a different termination rule).
