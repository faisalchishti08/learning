---
card: leetcode-patterns
gi: 165
slug: is-graph-bipartite
title: Is Graph Bipartite?
---

## 1. What it is

Given an undirected graph as an adjacency list `graph`, return `true` if its nodes can be split into two groups such that every edge connects a node from one group to a node from the OTHER group (no edge stays within a single group). Example: `graph = [[1,3],[0,2],[1,3],[0,2]]` → `true` (a 4-cycle, colorable as group A = {0, 2}, group B = {1, 3}).

## 2. Why & when

Checking "can this be 2-colored" is a natural fit for Graph BFS/DFS with an extra piece of state attached to each node: instead of just marking a node visited, ALSO record which of the two colors it was assigned. Every neighbor must get the OPPOSITE color; if a neighbor is already colored and it does NOT have the opposite color, the graph is not bipartite. It belongs in this section as the pattern for "traverse the graph while propagating a constraint, checking for contradictions."

## 3. Core concept

**Key idea:** run BFS or DFS from every unvisited node (the graph may be disconnected), assigning colors as you go: the starting node gets color `0`, and every neighbor gets the opposite color of the current node. If a neighbor is already colored and its color matches the current node's color (a same-color edge), the graph is not bipartite.

**Steps:**
1. Create a `color` array of size `n`, initialized to `-1` (uncolored) for every node.
2. For every node `i` from `0` to `n-1`: if `color[i] == -1` (unvisited, possibly a new connected component), start a BFS/DFS from it with `color[i] = 0`.
3. During the traversal: for each neighbor of the current node, if `color[neighbor] == -1`, assign it `1 - color[current]` and continue the traversal into it. If `color[neighbor] != -1` and `color[neighbor] == color[current]`, immediately return `false` (contradiction found).
4. If every node is colored without a contradiction, return `true`.

**Why it is correct:** assigning the opposite color to every neighbor directly enforces the bipartite requirement (adjacent nodes differ in color); if the graph truly has an odd cycle (which cannot be validly 2-colored), the traversal will eventually try to color some node both ways, triggering the contradiction check — looping over every node (not just node `0`) at the top level ensures disconnected components are all checked too.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A 4-cycle 2-colors cleanly; a 3-cycle forces a same-color contradiction">
  <g font-family="sans-serif" font-size="12">
    <circle cx="80" cy="40" r="15" fill="#161b22" stroke="#3fb950"/><text x="80" y="44" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="150" cy="40" r="15" fill="#161b22" stroke="#79c0ff"/><text x="150" y="44" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="150" cy="100" r="15" fill="#161b22" stroke="#3fb950"/><text x="150" y="104" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="80" cy="100" r="15" fill="#161b22" stroke="#79c0ff"/><text x="80" y="104" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="95" y1="40" x2="135" y2="40" stroke="#8b949e"/>
    <line x1="150" y1="55" x2="150" y2="85" stroke="#8b949e"/>
    <line x1="135" y1="100" x2="95" y2="100" stroke="#8b949e"/>
    <line x1="80" y1="85" x2="80" y2="55" stroke="#8b949e"/>
    <text x="10" y="15" fill="#e6edf3">4-cycle: colors alternate cleanly around the ring (green, blue, green, blue) -- bipartite</text>
    <circle cx="330" cy="50" r="14" fill="#161b22" stroke="#3fb950"/><text x="330" y="54" fill="#e6edf3" text-anchor="middle" font-size="11">A</text>
    <circle cx="390" cy="90" r="14" fill="#161b22" stroke="#79c0ff"/><text x="390" y="94" fill="#e6edf3" text-anchor="middle" font-size="11">B</text>
    <circle cx="330" cy="130" r="14" fill="#161b22" stroke="#f85149"/><text x="330" y="134" fill="#e6edf3" text-anchor="middle" font-size="11">C</text>
    <line x1="336" y1="63" x2="384" y2="80" stroke="#8b949e"/>
    <line x1="384" y1="100" x2="336" y2="120" stroke="#8b949e"/>
    <line x1="330" y1="64" x2="330" y2="116" stroke="#f85149" stroke-width="2"/>
    <text x="280" y="175" fill="#f85149">3-cycle: C forced back to same color as A -- contradiction, not bipartite</text>
  </g>
</svg>

A cycle with an odd number of nodes always forces two adjacent nodes into the same color, revealing a contradiction.

## 5. Runnable example

```java
// IsGraphBipartite.java
import java.util.*;

public class IsGraphBipartite {

    // Level 1 -- Brute force: try EVERY possible 2-coloring assignment
    // via brute-force backtracking (try color 0 or 1 for each node in
    // turn, backtrack on conflict). O(2^n) time worst case, since it
    // does not use the graph's structure to prune efficiently the way a
    // direct BFS/DFS coloring does.
    static boolean bruteForce(int[][] graph) {
        int n = graph.length;
        int[] color = new int[n];
        Arrays.fill(color, -1);
        for (int i = 0; i < n; i++) {
            if (color[i] == -1 && !tryColor(graph, i, 0, color)) return false;
        }
        return true;
    }

    static boolean tryColor(int[][] graph, int node, int c, int[] color) {
        if (color[node] != -1) return color[node] == c;
        color[node] = c;
        for (int neighbor : graph[node]) {
            if (!tryColor(graph, neighbor, 1 - c, color)) return false;
        }
        return true;
    }

    // KEY INSIGHT: a single BFS/DFS pass that assigns the OPPOSITE color
    // to every neighbor as it is discovered directly enforces the
    // bipartite constraint -- no separate backtracking search is needed,
    // since a contradiction is detected the moment it occurs.

    // Level 2 -- Optimal: BFS/DFS coloring, checking for same-color
    // conflicts on already-colored neighbors. O(V + E) time, O(V) space.
    public static boolean isBipartite(int[][] graph) {
        int n = graph.length;
        int[] color = new int[n];
        Arrays.fill(color, -1);

        for (int start = 0; start < n; start++) {
            if (color[start] != -1) continue;
            color[start] = 0;
            Queue<Integer> queue = new LinkedList<>();
            queue.offer(start);

            while (!queue.isEmpty()) {
                int node = queue.poll();
                for (int neighbor : graph[node]) {
                    if (color[neighbor] == -1) {
                        color[neighbor] = 1 - color[node];
                        queue.offer(neighbor);
                    } else if (color[neighbor] == color[node]) {
                        return false;
                    }
                }
            }
        }
        return true;
    }

    // Level 3 -- Hardened: a graph with multiple disconnected
    // components, where one component is bipartite and another contains
    // an odd cycle, must still return false (checking EVERY component,
    // not stopping after the first).
    static boolean hardened(int[][] graph) {
        return isBipartite(graph);
    }

    public static void main(String[] args) {
        int[][] fourCycle = {{1,3},{0,2},{1,3},{0,2}};
        int[][] threeCycle = {{1,2},{0,2},{0,1}};

        System.out.println(bruteForce(fourCycle));
        System.out.println(isBipartite(fourCycle));
        System.out.println(hardened(threeCycle));
    }
}
```

How to run: save as `IsGraphBipartite.java`, then run `java IsGraphBipartite.java`.

## 6. Walkthrough

Dry run of `isBipartite` on the 4-cycle `graph = [[1,3],[0,2],[1,3],[0,2]]`:

| step | node | color assigned | neighbors checked |
|---|---|---|---|
| start=0 | 0 | 0 | 1 (uncolored, gets 1), 3 (uncolored, gets 1) |
| dequeue 1 | 1 | 1 | 0 (colored 0, differs, ok), 2 (uncolored, gets 0) |
| dequeue 3 | 3 | 1 | 0 (colored 0, differs, ok), 2 (already colored 0 from node 1's turn, differs from 3's color 1, ok) |
| dequeue 2 | 2 | 0 | 1 (colored 1, differs, ok), 3 (colored 1, differs, ok) |

No contradiction found; all nodes colored consistently. Result: `true`. On the 3-cycle `[[1,2],[0,2],[0,1]]`: node `0` gets color `0`; node `1` gets color `1`; node `2` gets color `1` (opposite of `0`) via node `0`'s edge, but when node `1` checks its neighbor `2`, `2` is already color `1`, the SAME as node `1`'s own color `1` — contradiction, returns `false`. Time complexity: O(V + E), each node and edge examined once. Space complexity: O(V) for the color array and queue.

## 7. Gotchas & takeaways

> Gotcha: looping over only node `0` as the single starting point misses contradictions (or entire components) in a DISCONNECTED graph — the outer loop must try every node as a potential new starting point, skipping only those already colored, to guarantee every component is checked.

- The `color` array does double duty as both the "visited" tracker (`-1` means unvisited) and the actual bipartition assignment — a single array handles both roles.
- Related problems: Number of Provinces (also loops over every node to handle disconnected components, but counts groups instead of checking a coloring constraint), Find if Path Exists in Graph (a simpler traversal with no coloring, just plain reachability between two specific nodes).
