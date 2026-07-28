---
card: leetcode-patterns
gi: 534
slug: redundant-connection-ii
title: Redundant Connection II
---

## 1. What it is

Like [Redundant Connection](0526-redundant-connection.md), but the edges are **directed**, and the graph started as a **rooted tree** — one node is the root with no parent, and every other node has exactly one parent. One extra directed edge was added. Return the extra edge; if more than one edge could be removed to restore a valid rooted tree, return the one that appears last in the input. Example: `edges = [[1,2],[1,3],[2,3]]` → `[2,3]` (node 3 would have two parents, 1 and 2; removing `2->3` restores a valid tree).

## 2. Why & when

This variant is harder than the undirected version because the extra edge can cause **two different kinds of problems**, and you must handle both:

1. **A node with two parents** (in-degree 2) — some node is pointed to by two different edges, which cannot happen in a valid rooted tree.
2. **A cycle**, with every node still having at most one parent — the same cycle-detection signal as the undirected version.

A node can also have two parents **and** be part of a cycle at the same time, which is the trickiest case. Constraints: up to 1,000 nodes.

## 3. Core concept

**Key idea:** first scan for a node with two parents. If found, there are exactly two candidate edges (the first and second edge pointing to that node) — try removing the *second* one and check if the rest forms a valid tree using union-find cycle detection (same technique as Redundant Connection). If that works, it is the answer. If not, the *first* edge must be the answer instead (removing the second one left a cycle, so the first one — combined with the two-parents situation — is the true redundant edge).

If no node has two parents, the problem reduces exactly to the undirected version: find the one edge that closes a cycle.

**Steps:**
1. Scan all edges to find `parent[]` for each node. If some node `v` gets a second incoming edge, record both candidate edges: `edge1` (first edge to `v`) and `edge2` (second edge to `v`).
2. Build a union-find over all nodes. Process edges in order, **skipping `edge2`** if it was found (tentatively assume removing it is correct).
3. If any remaining edge closes a cycle (`find(u) == find(v)` before union):
   - If `edge1` exists (a two-parents case was found), the answer is `edge1` — skipping `edge2` was not enough, since a cycle still exists without it, so `edge1` (part of the original two-parents conflict) must be the true problem.
   - If `edge1` does not exist (no two-parents case at all), the answer is this cycle-closing edge directly — same as the undirected version.
4. If no cycle appears while skipping `edge2`, then `edge2` alone was the problem — return `edge2`.

**Why trying to skip `edge2` first is the right order:** when a node has two parents, the true redundant edge is one of those two. Testing "does removing the second one fix everything" first, and falling back to the first one only if that fails, correctly identifies which of the two is truly redundant based on whether a cycle remains.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Node 3 receives edges from both 1 and 2, giving it two parents; skipping the second edge and checking for a remaining cycle decides the answer">
  <g font-family="sans-serif" font-size="13">
    <circle cx="150" cy="40" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="150" y="45" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="300" cy="40" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="300" y="45" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="225" cy="130" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="225" y="135" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="160" y1="52" x2="215" y2="115" stroke="#79c0ff" marker-end="url(#arrow)"/>
    <text x="150" y="90" fill="#79c0ff" font-size="11">edge1: 1-&gt;3</text>
    <line x1="290" y1="52" x2="235" y2="115" stroke="#f0883e" marker-end="url(#arrow)"/>
    <text x="310" y="90" fill="#f0883e" font-size="11">edge2: 2-&gt;3</text>
    <defs>
      <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
        <path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/>
      </marker>
    </defs>
    <text x="225" y="180" fill="#e6edf3" text-anchor="middle">node 3 has two parents (1 and 2) -&gt; try skipping edge2 first</text>
  </g>
</svg>

Node `3` has two incoming edges. The algorithm tentatively skips `edge2` (`2->3`) and checks whether the rest of the graph is now cycle-free; if it is, `edge2` is the answer.

## 5. Runnable example

**Level 1 — Brute force.** Try removing each edge one at a time, and check whether the remaining `n-1` edges form a valid rooted tree (every non-root node has exactly one parent, no cycles, fully connected). O(n²).

**KEY INSIGHT:** the two-parents check and the cycle check are independent signals that must both be handled, and when both apply to the same node, testing "skip the second conflicting edge" first, with a union-find cycle check as the tiebreaker, resolves it in one pass.

**Level 2 — Optimal.** One pass to detect two-parents, one union-find pass (skipping the tentative edge) to detect cycles, O(n · α(n)).

**Level 3 — Hardened.** Handles a pure cycle with no two-parents node, a pure two-parents case with no cycle, and the combined case where both occur on the same node.

```java
// RedundantConnectionII.java
public class RedundantConnectionII {

    static class DSU {
        int[] parent;
        DSU(int n) {
            parent = new int[n + 1];
            for (int i = 0; i <= n; i++) parent[i] = i;
        }
        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }
        boolean union(int a, int b) {
            int rootA = find(a), rootB = find(b);
            if (rootA == rootB) return false;
            parent[rootA] = rootB;
            return true;
        }
    }

    static int[] findRedundantDirectedConnection(int[][] edges) {
        int n = edges.length;
        int[] parentOf = new int[n + 1]; // 0 means no parent seen yet
        int[] edge1 = null, edge2 = null;

        // pass 1: detect a node with two parents
        for (int[] edge : edges) {
            int u = edge[0], v = edge[1];
            if (parentOf[v] != 0) {
                edge1 = new int[]{parentOf[v], v};
                edge2 = edge;
            } else {
                parentOf[v] = u;
            }
        }

        DSU dsu = new DSU(n);
        for (int[] edge : edges) {
            if (edge2 != null && edge[0] == edge2[0] && edge[1] == edge2[1]) {
                continue; // tentatively skip the second candidate edge
            }
            int u = edge[0], v = edge[1];
            if (!dsu.union(u, v)) {
                // cycle found while edge2 was skipped
                if (edge1 == null) {
                    return edge; // pure cycle case, no two-parents node
                }
                return edge1; // two-parents case: edge2 alone was not enough, edge1 is the answer
            }
        }
        return edge2; // no cycle after skipping edge2 -> edge2 was the sole problem
    }

    public static void main(String[] args) {
        // pure cycle, no two-parents node
        System.out.println(java.util.Arrays.toString(
                findRedundantDirectedConnection(new int[][]{{1, 2}, {2, 3}, {3, 1}})));
        // pure two-parents, no cycle
        System.out.println(java.util.Arrays.toString(
                findRedundantDirectedConnection(new int[][]{{1, 2}, {1, 3}, {2, 3}})));
        // combined: node 1 has two parents AND a cycle remains without edge2
        System.out.println(java.util.Arrays.toString(
                findRedundantDirectedConnection(new int[][]{{2, 1}, {3, 1}, {4, 2}, {1, 4}})));
    }
}
```

**How to run:** save as `RedundantConnectionII.java`, then run `java RedundantConnectionII.java`.

## 6. Walkthrough

Trace the combined case `[[2,1],[3,1],[4,2],[1,4]]`:

1. Pass 1: edge `2->1` sets `parentOf[1]=2`. Edge `3->1` finds `parentOf[1]` already set — records `edge1=[2,1]`, `edge2=[3,1]`. Edge `4->2` sets `parentOf[2]=4`. Edge `1->4` sets `parentOf[4]=1`.
2. Union-find pass, skipping `edge2=[3,1]`: process `2->1` (union succeeds), `4->2` (union succeeds), `1->4` — `find(1)` and `find(4)` are now the same representative (since `2->1->4->2` chains them together) — union fails, a cycle exists.
3. Since a cycle was found even while `edge2` was skipped, and `edge1` is not null, the answer is `edge1 = [2, 1]` — the first of the two conflicting edges into node `1`.

## 7. Gotchas & takeaways

> Gotcha: always skipping just `edge1` instead of `edge2` (or picking arbitrarily) gives the wrong answer on the combined case — the algorithm must specifically try removing the *second* edge first, since it is the one that created the two-parents conflict, and only falls back to the first edge if a cycle proves the second removal was not enough.

- Signal: "directed version of redundant connection, rooted tree with one extra edge" needs both an in-degree-2 check and a union-find cycle check, run in that specific order.
- The three distinct cases: pure cycle (no node has two parents) → return the cycle-closing edge; pure two-parents (no cycle) → return the second conflicting edge; combined → return the first conflicting edge.
- Related problems: Redundant Connection (the simpler undirected version), Graph Valid Tree.
