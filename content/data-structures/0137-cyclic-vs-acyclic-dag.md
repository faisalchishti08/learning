---
card: data-structures
gi: 137
slug: cyclic-vs-acyclic-dag
title: Cyclic vs acyclic (DAG)
---

## 1. What it is

A graph has a **cycle** if you can start at some vertex, follow a sequence of edges, and return to that same vertex without repeating an edge. A graph with no cycles at all is **acyclic**. A **DAG** (Directed Acyclic Graph) is a directed graph with no cycles — a very common and important special case.

## 2. Why & when

Whether a graph is acyclic determines whether certain algorithms even make sense. **Topological sort** — ordering vertices so every edge points from an earlier vertex to a later one — is only possible on a DAG; a cycle makes it logically impossible, since some vertex in the cycle would need to come both before and after another. DAGs naturally model task dependencies (a build system's task graph), version histories (a Git commit graph, ignoring merges' complexity), and course prerequisites — anywhere "X must happen before Y" relationships exist with no circular requirement.

## 3. Core concept

**What a cycle actually is.** A cycle is a path `v1 -> v2 -> ... -> vk -> v1` that returns to its starting vertex, using at least one edge, without immediately reusing the same edge in reverse (a single back-and-forth on one undirected edge does not count as a cycle in an undirected graph, but any directed edge `A -> B` plus `B -> A` does count as a 2-cycle in a directed graph).

**Detecting a cycle in a directed graph.** Run a depth-first search (DFS), tracking each vertex's state as one of: **unvisited**, **in the current recursion stack** (currently being explored), or **fully finished**. If DFS ever encounters an edge pointing to a vertex that is *currently in the recursion stack*, that is a **back edge** — proof of a cycle. An edge to a vertex that is merely *already finished* (but not currently on the stack) is not a cycle — it just means two different paths converge on the same vertex, which is normal in a DAG.

**Why the recursion-stack distinction matters.** Without tracking "currently in the stack" separately from "visited at all," you cannot distinguish a genuine cycle (revisiting an ancestor on the current path) from a harmless reconvergence (two branches both leading to the same downstream vertex, without either being an ancestor of the other).

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A DAG where A points to both B and C, and both B and C point to D, which is a harmless reconvergence, versus a cyclic graph where C points back to A, forming a genuine cycle">
  <g font-family="sans-serif" font-size="11">
    <text x="150" y="16" fill="#79c0ff" text-anchor="middle">DAG: A-&gt;B, A-&gt;C, B-&gt;D, C-&gt;D (no cycle)</text>
    <circle cx="150" cy="50" r="16" fill="#161b22" stroke="#79c0ff"/><text x="150" y="54" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="80" cy="110" r="16" fill="#161b22" stroke="#79c0ff"/><text x="80" y="114" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="220" cy="110" r="16" fill="#161b22" stroke="#79c0ff"/><text x="220" y="114" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <circle cx="150" cy="170" r="16" fill="#161b22" stroke="#79c0ff"/><text x="150" y="174" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <line x1="138" y1="62" x2="92" y2="98" stroke="#79c0ff" stroke-width="2" marker-end="url(#a1)"/>
    <line x1="162" y1="62" x2="208" y2="98" stroke="#79c0ff" stroke-width="2" marker-end="url(#a1)"/>
    <line x1="90" y1="122" x2="138" y2="158" stroke="#79c0ff" stroke-width="2" marker-end="url(#a1)"/>
    <line x1="210" y1="122" x2="162" y2="158" stroke="#79c0ff" stroke-width="2" marker-end="url(#a1)"/>
    <defs><marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

    <text x="480" y="16" fill="#f0883e" text-anchor="middle">cyclic: A-&gt;B, B-&gt;C, C-&gt;A (a genuine cycle)</text>
    <circle cx="480" cy="60" r="16" fill="#161b22" stroke="#f0883e"/><text x="480" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="420" cy="150" r="16" fill="#161b22" stroke="#f0883e"/><text x="420" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="540" cy="150" r="16" fill="#161b22" stroke="#f0883e"/><text x="540" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <line x1="468" y1="72" x2="432" y2="138" stroke="#f0883e" stroke-width="2" marker-end="url(#a2)"/>
    <line x1="436" y1="150" x2="524" y2="150" stroke="#f0883e" stroke-width="2" marker-end="url(#a2)"/>
    <line x1="528" y1="140" x2="492" y2="72" stroke="#f0883e" stroke-width="2" marker-end="url(#a2)"/>
    <defs><marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker></defs>
  </g>
</svg>

`D` being reachable from both `B` and `C` is harmless reconvergence, not a cycle — the DAG remains acyclic. In the cyclic graph, `C -> A` closes a loop back to an ancestor already on the current path, which is a genuine cycle.

## 5. Runnable example

```java
// CycleDetection.java
import java.util.*;

public class CycleDetection {

    // Basic: DFS-based cycle detection using three states -- UNVISITED, IN_STACK, DONE.
    enum State { UNVISITED, IN_STACK, DONE }

    static boolean hasCycle(Map<String, List<String>> graph) {
        Map<String, State> state = new HashMap<>();
        for (String vertex : graph.keySet()) state.put(vertex, State.UNVISITED);

        for (String vertex : graph.keySet()) {
            if (state.get(vertex) == State.UNVISITED) {
                if (dfsHasCycle(graph, vertex, state)) return true;
            }
        }
        return false;
    }

    static boolean dfsHasCycle(Map<String, List<String>> graph, String current, Map<String, State> state) {
        state.put(current, State.IN_STACK);
        for (String neighbor : graph.getOrDefault(current, List.of())) {
            State neighborState = state.getOrDefault(neighbor, State.UNVISITED);
            if (neighborState == State.IN_STACK) return true; // back edge to an ancestor -- genuine cycle
            if (neighborState == State.UNVISITED && dfsHasCycle(graph, neighbor, state)) return true;
            // neighborState == DONE: harmless reconvergence, not a cycle -- skip
        }
        state.put(current, State.DONE);
        return false;
    }

    static void basicLevel() {
        Map<String, List<String>> dag = Map.of(
            "A", List.of("B", "C"),
            "B", List.of("D"),
            "C", List.of("D"),
            "D", List.of());

        System.out.println("basic: DAG (A->B->D, A->C->D) has a cycle? -> " + hasCycle(dag));
    }

    static void intermediateLevel() {
        Map<String, List<String>> cyclicGraph = Map.of(
            "A", List.of("B"),
            "B", List.of("C"),
            "C", List.of("A")); // closes the loop back to A

        System.out.println("intermediate: cyclic graph (A->B->C->A) has a cycle? -> " + hasCycle(cyclicGraph));
    }

    // Advanced: confirm the "reconvergence is not a cycle" distinction directly, on a graph with a diamond shape PLUS an actual cycle elsewhere.
    static void advancedLevel() {
        Map<String, List<String>> mixed = new HashMap<>();
        mixed.put("A", List.of("B", "C")); // diamond: A->B->D and A->C->D, D reached twice, no cycle here
        mixed.put("B", List.of("D"));
        mixed.put("C", List.of("D"));
        mixed.put("D", List.of());
        System.out.println("advanced: diamond shape alone (no back edges) -> has cycle? " + hasCycle(mixed));

        mixed.put("D", List.of("A")); // NOW add a genuine back edge, D -> A, creating a real cycle
        System.out.println("advanced: same graph plus D->A -> has cycle? " + hasCycle(mixed) + " (D->A closes a loop back to an ancestor)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `CycleDetection.java`, then run `java CycleDetection.java`.

## 6. Walkthrough

1. `basicLevel()` checks a DAG shaped like a diamond: `A` points to both `B` and `C`; both `B` and `C` point to `D`. DFS from `A` marks `A` as `IN_STACK`, explores `B` (also `IN_STACK`), reaches `D`, marks it `DONE`, backtracks, marks `B` as `DONE`. It then explores `C`, reaching `D` again — but `D`'s state is now `DONE`, not `IN_STACK`, so this is correctly recognized as harmless reconvergence, not a cycle. Result: `false`.
2. `intermediateLevel()` checks `A -> B -> C -> A`. DFS marks `A`, then `B`, then `C` as `IN_STACK` in turn. From `C`, the edge to `A` finds `A`'s state is still `IN_STACK` (it is an ancestor on the current path, not yet finished) — this is a genuine back edge, so `hasCycle` correctly returns `true`.
3. `advancedLevel()` first confirms the diamond shape alone has no cycle, then adds a single edge `D -> A`, closing a loop back to an ancestor still logically "in progress" on some path. The same detection code now correctly reports a cycle, confirming the `IN_STACK` vs `DONE` distinction is exactly what separates a genuine cycle from safe reconvergence.

## 7. Gotchas & takeaways

> Gotcha: tracking only "visited or not" (two states, not three) cannot distinguish a genuine cycle from harmless reconvergence — both look like "already visited" with just two states. The three-state approach (`UNVISITED`, `IN_STACK`, `DONE`) is what makes directed-cycle detection correct.

- A DAG is a directed graph with no cycles; topological sort is only well-defined on a DAG.
- Cycle detection in a directed graph needs three states per vertex, not two — an edge to a `DONE` vertex is fine, but an edge to an `IN_STACK` vertex is a genuine cycle.
- Undirected-graph cycle detection is simpler (just track visited vertices and the edge you arrived from, to avoid falsely flagging the immediate parent edge as a cycle).
- Related concepts: [Topological sort](0146-topological-sort.md), [Depth-first search (DFS)](0145-depth-first-search-dfs.md), [Connectivity & components](0138-connectivity-components.md).
