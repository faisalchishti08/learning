---
card: leetcode-patterns
gi: 177
slug: reconstruct-itinerary
title: Reconstruct Itinerary
---

## 1. What it is

Given a list of airline `tickets` as `[from, to]` pairs, all starting from `"JFK"`, reconstruct the itinerary that uses every ticket exactly once, in the lexicographically smallest order when multiple valid itineraries exist. Example: `tickets = [["MUC","LHR"],["JFK","MUC"],["LHR","SFO"],["SFO","SJC"]]` → `["JFK","MUC","LHR","SFO","SJC"]`.

## 2. Why & when

Every ticket is a directed edge; using each ticket exactly once and visiting every edge is an Eulerian path problem. Hierholzer's algorithm — a DFS variant that only adds a node to the result AFTER exhausting all its outgoing edges (post-order) — builds such a path efficiently, and processing neighbors in sorted order naturally yields the lexicographically smallest result.

## 3. Core concept

**Key idea:** build an adjacency list of destinations per airport, sorted lexicographically. DFS from `"JFK"`, always taking the smallest unused destination first; each time a node runs out of outgoing tickets, add it to the front of the result (post-order). Reversing (or prepending) gives the correct itinerary.

**Steps:**
1. Group tickets by origin into a sorted structure (e.g. a `PriorityQueue` or sorted list per origin) so the smallest destination is tried first.
2. DFS from `"JFK"`: pop the smallest available destination for the current airport, recurse into it, and repeat.
3. When an airport has no more outgoing tickets left, that means the DFS has reached a dead end (or exhausted this branch) — add the airport to the front of a result list (this is the post-order step).
4. After DFS from `"JFK"` fully completes, the result list, in the order built, is the final itinerary.

**Why it is correct:** Hierholzer's algorithm guarantees an Eulerian path exists here because the problem guarantees one is always constructible from valid input. Choosing the smallest destination first at every greedy step, combined with post-order insertion (which correctly "backs out" of dead ends by placing them after their unresolved continuations), produces the lexicographically smallest valid path using every ticket exactly once.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DFS follows smallest-destination-first, backtracking builds result in post-order">
  <g font-family="sans-serif" font-size="12">
    <circle cx="60" cy="100" r="22" fill="#161b22" stroke="#3fb950"/><text x="60" y="104" fill="#e6edf3" text-anchor="middle" font-size="11">JFK</text>
    <circle cx="180" cy="100" r="22" fill="#161b22" stroke="#79c0ff"/><text x="180" y="104" fill="#e6edf3" text-anchor="middle" font-size="11">MUC</text>
    <circle cx="300" cy="100" r="22" fill="#161b22" stroke="#79c0ff"/><text x="300" y="104" fill="#e6edf3" text-anchor="middle" font-size="11">LHR</text>
    <circle cx="420" cy="100" r="22" fill="#161b22" stroke="#e3b341"/><text x="420" y="104" fill="#e6edf3" text-anchor="middle" font-size="11">SFO</text>
    <line x1="82" y1="100" x2="158" y2="100" stroke="#8b949e" marker-end="url(#a4)"/>
    <line x1="202" y1="100" x2="278" y2="100" stroke="#8b949e" marker-end="url(#a4)"/>
    <line x1="322" y1="100" x2="398" y2="100" stroke="#8b949e" marker-end="url(#a4)"/>
    <defs><marker id="a4" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="10" y="15" fill="#e6edf3">DFS: JFK-&gt;MUC-&gt;LHR-&gt;SFO, each hop the lexicographically smallest option available</text>
  </g>
</svg>

DFS always follows the alphabetically smallest unused ticket from the current airport, only marking an airport "done" once every outgoing ticket from it has been used.

## 5. Runnable example

```java
// ReconstructItinerary.java
import java.util.*;

public class ReconstructItinerary {

    // Level 1 -- Brute force: generate every permutation of tickets
    // that forms a valid chain starting at JFK, then pick the
    // lexicographically smallest. Correct, but factorial time -- wildly
    // impractical beyond a handful of tickets.

    // KEY INSIGHT: this is an Eulerian path (use every edge exactly
    // once) -- Hierholzer's algorithm builds it in near-linear time by
    // greedily taking the smallest edge and recording nodes in
    // POST-order, which correctly resolves dead ends by placing them
    // after whatever still needs to finish.

    // Level 2 -- Optimal: Hierholzer's algorithm with sorted adjacency.
    static List<String> findItinerary(List<List<String>> tickets) {
        Map<String, PriorityQueue<String>> graph = new HashMap<>();
        for (List<String> ticket : tickets) {
            graph.computeIfAbsent(ticket.get(0), k -> new PriorityQueue<>()).add(ticket.get(1));
        }

        LinkedList<String> result = new LinkedList<>();
        dfs("JFK", graph, result);
        return result;
    }

    static void dfs(String airport, Map<String, PriorityQueue<String>> graph, LinkedList<String> result) {
        PriorityQueue<String> destinations = graph.get(airport);
        while (destinations != null && !destinations.isEmpty()) {
            String next = destinations.poll();
            dfs(next, graph, result);
        }
        result.addFirst(airport);
    }

    // Level 3 -- Hardened: handles airports with no outgoing tickets
    // (graph.get returns null, the while loop's null check skips it)
    // and duplicate tickets between the same pair of airports (the
    // PriorityQueue holds duplicates fine, each used exactly once).

    public static void main(String[] args) {
        System.out.println(findItinerary(Arrays.asList(
            Arrays.asList("MUC","LHR"), Arrays.asList("JFK","MUC"),
            Arrays.asList("LHR","SFO"), Arrays.asList("SFO","SJC")
        ))); // [JFK, MUC, LHR, SFO, SJC]

        System.out.println(findItinerary(Arrays.asList(
            Arrays.asList("JFK","SFO"), Arrays.asList("JFK","ATL"),
            Arrays.asList("SFO","ATL"), Arrays.asList("ATL","JFK"),
            Arrays.asList("ATL","SFO")
        ))); // [JFK, ATL, JFK, SFO, ATL, SFO]
    }
}
```

**How to run:** `java ReconstructItinerary.java`

## 6. Walkthrough

Trace `tickets = [["MUC","LHR"],["JFK","MUC"],["LHR","SFO"],["SFO","SJC"]]`:

| Step | Call | Destinations left | Action |
|---|---|---|---|
| 1 | dfs(JFK) | [MUC] | poll MUC, recurse |
| 2 | dfs(MUC) | [LHR] | poll LHR, recurse |
| 3 | dfs(LHR) | [SFO] | poll SFO, recurse |
| 4 | dfs(SFO) | [SJC] | poll SJC, recurse |
| 5 | dfs(SJC) | none | no destinations, addFirst("SJC") |
| 6 | back in dfs(SFO) | empty | addFirst("SFO") |
| 7 | back in dfs(LHR) | empty | addFirst("LHR") |
| 8 | back in dfs(MUC) | empty | addFirst("MUC") |
| 9 | back in dfs(JFK) | empty | addFirst("JFK") |

Result, built by post-order `addFirst`: `[JFK, MUC, LHR, SFO, SJC]`. Time complexity is O(E log E), where E is the ticket count, for the priority-queue operations across the DFS; space is O(E) for the graph and result list.

## 7. Gotchas & takeaways

> Adding an airport to the result the moment DFS FIRST visits it (pre-order), instead of after exhausting its outgoing edges (post-order), produces an itinerary that skips over a dead-end detour instead of correctly threading through it.

- `addFirst` (post-order / reverse-build) is what makes Hierholzer's algorithm correctly splice in a "dead-end loop" at the right spot in the final path — this is the detail brute-force permutation search does not need to get right, since it just checks validity after the fact.
- A `PriorityQueue<String>` per origin airport keeps destinations in sorted order automatically, giving the lexicographically smallest choice at each greedy step for free.
- Related problems: Course Schedule II (topological sort via a similar post-order DFS), All Paths From Source to Target (DFS enumerating multiple paths rather than one Eulerian path).
