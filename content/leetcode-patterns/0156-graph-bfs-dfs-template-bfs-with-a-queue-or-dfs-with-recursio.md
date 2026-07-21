---
card: leetcode-patterns
gi: 156
slug: graph-bfs-dfs-template-bfs-with-a-queue-or-dfs-with-recursio
title: Graph BFS/DFS — template: BFS with a queue or DFS with recursion/stack + visited set
---

## 1. What it is

This is the reusable template for exploring a general graph: BFS uses a queue to process nodes level by level; DFS uses recursion (or an explicit stack) to go as deep as possible before backtracking. Both need a `visited` set to handle cycles and shared neighbors, and both visit every reachable node exactly once.

## 2. Why & when

Choose BFS when a problem needs the SHORTEST number of steps/edges to reach something (minimum mutations, shortest path in an unweighted grid, "rounds" of spreading like rotting oranges) — BFS explores in strict distance order, so the first time it reaches a target, that is guaranteed to be via the shortest path. Choose DFS when the problem only needs to know "is this reachable" or "explore this whole connected piece" (counting islands, cloning a graph, checking if any path exists), where the specific order of exploration does not matter, only which nodes are reachable.

The two are otherwise interchangeable for pure reachability questions; DFS is often shorter to write (plain recursion, no explicit queue), while BFS is required whenever "shortest" or "fewest steps" is part of the question.

## 3. Core concept

**Key idea (BFS):** a queue naturally processes nodes in the order they were discovered, which is also increasing distance-from-start order in an unweighted graph — so the first time a node is dequeued, the number of steps taken to reach it is guaranteed minimal.

**Steps (BFS):**
1. Mark the start node visited, and enqueue it (optionally paired with a distance of `0`).
2. While the queue is not empty: dequeue a node, process it, then for each unvisited neighbor, mark it visited and enqueue it (with distance + 1, if tracking distance).
3. Stop early if searching for a specific target and it is dequeued.

**Key idea (DFS):** recursion naturally explores one branch completely (as deep as possible) before backtracking to try the next branch — perfect for "have I explored every reachable node" questions.

**Steps (DFS):**
1. Mark the current node visited.
2. Process it (whatever the problem needs).
3. For each neighbor: if not visited, recurse into it.
4. (An explicit stack works the same way if recursion depth is a concern: push instead of recurse, pop instead of return.)

**Why they work:** both approaches only ever enqueue/recurse into a node once, because of the `visited` check — this guarantees termination on any graph, including ones with cycles, and guarantees every reachable node is processed exactly once.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BFS explores by distance rings; DFS explores by going deep first">
  <g font-family="sans-serif" font-size="12">
    <circle cx="80" cy="90" r="15" fill="#161b22" stroke="#3fb950"/><text x="80" y="94" fill="#e6edf3" text-anchor="middle">S</text>
    <circle cx="150" cy="50" r="13" fill="#161b22" stroke="#79c0ff"/><text x="150" y="54" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="150" cy="130" r="13" fill="#161b22" stroke="#79c0ff"/><text x="150" y="134" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="220" cy="50" r="12" fill="#161b22" stroke="#f85149"/><text x="220" y="54" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <circle cx="220" cy="130" r="12" fill="#161b22" stroke="#f85149"/><text x="220" y="134" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <line x1="93" y1="83" x2="137" y2="57" stroke="#8b949e"/>
    <line x1="93" y1="97" x2="137" y2="123" stroke="#8b949e"/>
    <line x1="163" y1="50" x2="207" y2="50" stroke="#8b949e"/>
    <line x1="163" y1="130" x2="207" y2="130" stroke="#8b949e"/>
    <text x="10" y="20" fill="#e6edf3">BFS ring order: S (dist 0), then both "1" nodes (dist 1), then both "2" nodes (dist 2)</text>
    <text x="10" y="175" fill="#e6edf3">DFS instead plunges S -&gt; top-1 -&gt; top-2 fully before ever visiting bottom-1</text>
  </g>
</svg>

BFS visits nodes in strict "distance rings"; DFS commits to one full branch before backtracking to the other.

## 5. Runnable example

```java
// GraphBfsDfsTemplates.java
import java.util.*;

public class GraphBfsDfsTemplates {

    // BFS template with distance tracking -- returns shortest distance
    // from start to every reachable node.
    static Map<Integer, Integer> bfsDistances(Map<Integer, List<Integer>> graph, int start) {
        Map<Integer, Integer> distance = new HashMap<>();
        Queue<Integer> queue = new LinkedList<>();
        distance.put(start, 0);
        queue.offer(start);

        while (!queue.isEmpty()) {
            int node = queue.poll();
            for (int neighbor : graph.getOrDefault(node, List.of())) {
                if (!distance.containsKey(neighbor)) {
                    distance.put(neighbor, distance.get(node) + 1);
                    queue.offer(neighbor);
                }
            }
        }
        return distance;
    }

    // DFS template using an explicit stack (iterative, avoids recursion
    // depth limits on very large graphs).
    static Set<Integer> dfsIterative(Map<Integer, List<Integer>> graph, int start) {
        Set<Integer> visited = new HashSet<>();
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(start);
        visited.add(start);

        while (!stack.isEmpty()) {
            int node = stack.pop();
            for (int neighbor : graph.getOrDefault(node, List.of())) {
                if (!visited.contains(neighbor)) {
                    visited.add(neighbor);
                    stack.push(neighbor);
                }
            }
        }
        return visited;
    }

    public static void main(String[] args) {
        Map<Integer, List<Integer>> graph = new HashMap<>();
        graph.put(0, List.of(1, 2));
        graph.put(1, List.of(3));
        graph.put(2, List.of(3));
        graph.put(3, List.of());

        System.out.println(bfsDistances(graph, 0));
        System.out.println(dfsIterative(graph, 0));
    }
}
```

How to run: save as `GraphBfsDfsTemplates.java`, then run `java GraphBfsDfsTemplates.java`.

## 6. Walkthrough

Trace of `bfsDistances(graph, 0)` on `0 -> {1, 2}`, `1 -> {3}`, `2 -> {3}`:

1. `distance = {0: 0}`, `queue = [0]`.
2. Dequeue `0`. Neighbors `1`, `2` are unvisited: `distance = {0:0, 1:1, 2:1}`, `queue = [1, 2]`.
3. Dequeue `1`. Neighbor `3` is unvisited: `distance = {..., 3:2}`, `queue = [2, 3]`.
4. Dequeue `2`. Neighbor `3` is ALREADY in `distance` (visited via `1`) — skip. `queue = [3]`.
5. Dequeue `3`. No neighbors. `queue = []`.

Final distances: `{0:0, 1:1, 2:1, 3:2}` — node `3` correctly gets distance `2`, the shortest of its two possible paths (`0->1->3` or `0->2->3`), because BFS reaches it for the first time via whichever path is shorter (here, both are length 2, and the second arrival via `2` is correctly ignored since `3` is already recorded).

## 7. Gotchas & takeaways

> Gotcha: for DFS, checking `visited` BEFORE pushing/recursing (not after popping) avoids pushing the same node onto the stack multiple times from different neighbors — the iterative stack version above marks a node visited at push time, exactly mirroring how the recursive version marks it visited at the top of the function call.

- BFS's `distance` map doubles as its `visited` set here — checking `!distance.containsKey(neighbor)` serves both purposes at once (has it been seen, and if not, what is its distance).
- The next page covers the shared time and space complexity, O(V + E), for both BFS and DFS — and why that bound holds regardless of which one you pick.
