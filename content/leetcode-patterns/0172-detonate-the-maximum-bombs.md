---
card: leetcode-patterns
gi: 172
slug: detonate-the-maximum-bombs
title: Detonate the Maximum Bombs
---

## 1. What it is

Given `bombs` as `[x, y, r]` triples (position and blast radius), detonating one bomb triggers any OTHER bomb whose center lies within its radius, which then chains further. Return the maximum number of bombs that can be detonated by choosing the best single bomb to start. Example: `bombs = [[2,1,3],[6,1,4]]` → `2`.

## 2. Why & when

The blast relationship is directed (bomb A's radius reaching bomb B does not mean B's radius reaches A back), so this is a directed graph reachability problem: build an edge `A -> B` whenever A's blast covers B, then find which starting node reaches the most other nodes via DFS or BFS.

## 3. Core concept

**Key idea:** build a directed graph where an edge `i -> j` exists if bomb `i`'s explosion radius reaches bomb `j`'s center. Then, for every bomb as a starting point, count how many nodes are reachable via DFS/BFS, and keep the maximum.

**Steps:**
1. For every pair `(i, j)`, compute the Euclidean distance between their centers. If it is `<= radius[i]`, add edge `i -> j` (bomb i detonates bomb j).
2. For each bomb `i` from `0` to `n-1`, run a DFS/BFS starting at `i` following these directed edges, counting distinct nodes visited (including `i`).
3. Track the maximum count seen across all starting bombs.
4. Return that maximum.

**Why it is correct:** detonating bomb `i` triggers exactly the bombs reachable from `i` by following the "reaches" edges transitively — which is exactly graph reachability from node `i`. Trying every possible starting bomb and taking the best is required, since the graph is directed and reachability is not symmetric.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Directed edge from bomb 0 to bomb 1 because bomb 0's larger radius reaches bomb 1, but not the reverse">
  <g font-family="sans-serif" font-size="12">
    <circle cx="100" cy="100" r="40" fill="none" stroke="#3fb950" stroke-dasharray="4,3"/>
    <circle cx="100" cy="100" r="6" fill="#3fb950"/><text x="100" y="125" fill="#e6edf3" text-anchor="middle">bomb 0 (r=3)</text>
    <circle cx="220" cy="100" r="6" fill="#79c0ff"/><text x="220" y="125" fill="#e6edf3" text-anchor="middle">bomb 1</text>
    <line x1="140" y1="100" x2="212" y2="100" stroke="#8b949e" marker-end="url(#a2)"/>
    <defs><marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="10" y="15" fill="#e6edf3">bomb 0's radius circle covers bomb 1's center -- edge 0-&gt;1 only, not 1-&gt;0</text>
  </g>
</svg>

Bomb `0`'s radius reaches bomb `1`, so the edge is directed `0 -> 1`; starting from `0` detonates both, starting from `1` alone detonates only `1`.

## 5. Runnable example

```java
// DetonateTheMaximumBombs.java
import java.util.*;

public class DetonateTheMaximumBombs {

    // Level 1 -- Brute force: simulate the chain reaction with a queue
    // for every possible starting bomb, recomputing all pairwise
    // distances fresh each time. Correct, but O(n^3) since the O(n^2)
    // edge computation is redone n times.

    // KEY INSIGHT: build the directed reachability graph ONCE (O(n^2)),
    // then reuse it for n separate reachability searches, one per
    // starting bomb -- separating "build the graph" from "search it"
    // avoids repeating the expensive geometry.

    // Level 2 -- Optimal: build adjacency list once, BFS per start.
    static int maximumDetonation(int[][] bombs) {
        int n = bombs.length;
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());

        for (int i = 0; i < n; i++) {
            long xi = bombs[i][0], yi = bombs[i][1], ri = bombs[i][2];
            for (int j = 0; j < n; j++) {
                if (i == j) continue;
                long dx = xi - bombs[j][0], dy = yi - bombs[j][1];
                if (dx * dx + dy * dy <= ri * ri) graph.get(i).add(j);
            }
        }

        int best = 0;
        for (int start = 0; start < n; start++) {
            best = Math.max(best, bfsCount(graph, start, n));
        }
        return best;
    }

    static int bfsCount(List<List<Integer>> graph, int start, int n) {
        boolean[] visited = new boolean[n];
        visited[start] = true;
        Queue<Integer> queue = new LinkedList<>();
        queue.add(start);
        int count = 1;
        while (!queue.isEmpty()) {
            int cur = queue.poll();
            for (int next : graph.get(cur)) {
                if (!visited[next]) {
                    visited[next] = true;
                    count++;
                    queue.add(next);
                }
            }
        }
        return count;
    }

    // Level 3 -- Hardened: use `long` for the squared-distance
    // comparison to avoid integer overflow, since coordinates and radii
    // can be up to 10^5, making dx*dx up to 10^10 (overflows a 32-bit
    // int).

    public static void main(String[] args) {
        System.out.println(maximumDetonation(new int[][]{{2,1,3},{6,1,4}})); // 2
        System.out.println(maximumDetonation(new int[][]{{1,1,5},{10,10,5}})); // 1
        System.out.println(maximumDetonation(new int[][]{{1,2,3},{2,3,1},{3,4,2},{4,5,3},{5,6,4}})); // 5
    }
}
```

**How to run:** `java DetonateTheMaximumBombs.java`

## 6. Walkthrough

Trace `bombs = [[2,1,3],[6,1,4]]`:

| Step | Pair checked | Distance² | radius₀² | Edge added? |
|---|---|---|---|---|
| 1 | 0→1 | (2-6)²+(1-1)²=16 | 3²=9 | no (16 > 9) |
| 2 | 1→0 | 16 | 4²=16 | yes (16 ≤ 16), edge 1→0 |
| 3 | BFS from 0 | — | — | count = 1 (no outgoing edges) |
| 4 | BFS from 1 | — | — | reaches 0 → count = 2 |

Maximum over both starts is `2`. Time complexity is O(n³) — O(n²) to build the graph plus O(n) starts each doing an O(n²) worst-case BFS; space is O(n²) for the adjacency list.

## 7. Gotchas & takeaways

> Using `int` instead of `long` for `dx * dx + dy * dy` silently overflows when coordinates are large, producing wrong (often negative) comparisons that misclassify which bombs reach which.

- The graph is directed: a large-radius bomb reaching a small one does not imply the reverse — always check both `bfsCount` starting points separately, never assume symmetry.
- Comparing squared distances avoids a `sqrt` call and its floating-point rounding risk.
- Related problems: All Paths From Source to Target (DFS over a directed graph), Course Schedule (directed graph reachability/cycle detection).
