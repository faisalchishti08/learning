---
card: leetcode-patterns
gi: 556
slug: bus-routes
title: Bus Routes
---

## 1. What it is

`routes[i]` is the list of bus stops that bus route `i` visits, in a loop. Starting at stop `source`, find the **minimum number of buses** you must take to reach stop `target`. Return `-1` if it is impossible. Example: `routes = [[1,2,7],[3,6,7]]`, `source=1`, `target=6` → `2` (bus 0 goes `1->7`, bus 1 goes `7->6`).

## 2. Why & when

The obvious graph (stops as nodes, direct stop-to-stop travel as edges) hides the real cost structure: moving between two stops on the *same* bus is free once you are already riding it, but switching to a *different* bus is what actually costs you (one more bus ride). This is an unweighted shortest-path problem — plain breadth-first search — but only once you build the graph over the right unit: **routes**, not stops. Constraints: up to 500 routes, up to 100,000 total stops across all routes.

## 3. Core concept

**Key idea:** build a graph where the nodes are **bus routes** (not stops), and two routes are connected if they share at least one stop (meaning you can transfer between them at that stop). Then run breadth-first search over this route graph, starting from every route that visits `source`, and stop as soon as you reach any route that visits `target`. The number of breadth-first search layers traversed is the number of buses taken.

**Steps:**
1. Build a `Map<Integer, List<Integer>> stopToRoutes`: for every stop, which routes visit it.
2. Build a route-to-route adjacency: two routes are connected if `stopToRoutes` shows they share a stop (or just derive this on the fly while doing breadth-first search, via the shared stop map, to avoid an expensive all-pairs comparison).
3. Breadth-first search starting from every route that contains `source` (all at "1 bus" distance), marking visited routes.
4. At each layer, for every route popped, check if it visits `target` — if so, return the current bus count. Otherwise, add every *not-yet-visited* route reachable through any stop on this route.
5. If the queue empties without finding `target`, return `-1`.

**Why breadth-first search over routes (not stops) gives the minimum bus count directly:** each "hop" in this route graph represents exactly one additional bus boarded, since traveling along a single route (however many stops) costs zero extra buses. Breadth-first search naturally finds the fewest hops needed, which corresponds exactly to the fewest buses.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Route 0 and route 1 sharing stop 7, connecting them in the route graph">
  <g font-family="sans-serif" font-size="13">
    <rect x="30" y="30" width="220" height="50" rx="6" fill="#161b22" stroke="#3fb950"/>
    <text x="140" y="55" fill="#e6edf3" text-anchor="middle">route 0: stops 1,2,7</text>
    <rect x="380" y="30" width="220" height="50" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="490" y="55" fill="#e6edf3" text-anchor="middle">route 1: stops 3,6,7</text>
    <line x1="252" y1="55" x2="378" y2="55" stroke="#79c0ff" stroke-width="2"/>
    <text x="315" y="45" fill="#79c0ff" font-size="11" text-anchor="middle">shared stop 7</text>
    <text x="315" y="110" fill="#e6edf3" text-anchor="middle">source=1 (on route 0) -&gt; transfer at 7 -&gt; target=6 (on route 1): 2 buses</text>
  </g>
</svg>

Routes `0` and `1` share stop `7`, connecting them directly in the route graph — one transfer, two buses total.

## 5. Runnable example

**Level 1 — Brute force.** Breadth-first search directly over stops, treating every pair of stops on the same route as connected by a "free" edge and every actual different route as a weighted step. Correctly modeling "free within a route" this way is awkward and easy to get wrong.

**KEY INSIGHT:** re-framing the graph so that routes (not stops) are the nodes turns "minimum buses" into a plain unweighted breadth-first search — the natural unit of cost.

**Level 2 — Optimal.** Breadth-first search over the route graph, using a stop-to-routes map to find neighbors on the fly, O(total stops across all routes).

**Level 3 — Hardened.** Handles `source == target` (`0` buses needed), and `source` or `target` not present on any route (`-1`).

```java
// BusRoutes.java
import java.util.*;

public class BusRoutes {

    static int numBusesToDestination(int[][] routes, int source, int target) {
        if (source == target) return 0;

        Map<Integer, List<Integer>> stopToRoutes = new HashMap<>();
        for (int r = 0; r < routes.length; r++) {
            for (int stop : routes[r]) {
                stopToRoutes.computeIfAbsent(stop, k -> new ArrayList<>()).add(r);
            }
        }

        boolean[] visitedRoute = new boolean[routes.length];
        Deque<Integer> queue = new ArrayDeque<>();
        for (int route : stopToRoutes.getOrDefault(source, Collections.emptyList())) {
            if (!visitedRoute[route]) {
                visitedRoute[route] = true;
                queue.add(route);
            }
        }

        int buses = 1;
        while (!queue.isEmpty()) {
            int size = queue.size();
            for (int i = 0; i < size; i++) {
                int route = queue.poll();
                for (int stop : routes[route]) {
                    if (stop == target) return buses;
                    for (int nextRoute : stopToRoutes.getOrDefault(stop, Collections.emptyList())) {
                        if (!visitedRoute[nextRoute]) {
                            visitedRoute[nextRoute] = true;
                            queue.add(nextRoute);
                        }
                    }
                }
            }
            buses++;
        }
        return -1;
    }

    public static void main(String[] args) {
        int[][] routes1 = {{1, 2, 7}, {3, 6, 7}};
        System.out.println(numBusesToDestination(routes1, 1, 6)); // 2

        int[][] routes2 = {{7, 12}, {4, 5, 15}, {6}, {15, 19}, {9, 12, 13}};
        System.out.println(numBusesToDestination(routes2, 15, 12)); // -1
    }
}
```

**How to run:** save as `BusRoutes.java`, then run `java BusRoutes.java`.

## 6. Walkthrough

Trace `numBusesToDestination([[1,2,7],[3,6,7]], 1, 6)`:

1. `source (1) != target (6)`. `stopToRoutes = {1:[0], 2:[0], 7:[0,1], 3:[1], 6:[1]}`.
2. Start: `source=1` is on route `0` only. Queue: `[0]`, `visitedRoute=[true,false]`, `buses=1`.
3. Layer 1: pop route `0`. Check its stops `1,2,7` for `target=6` — none match. For each stop, look up other routes sharing it: stop `7` also belongs to route `1` (unvisited) — mark visited, add to queue.
4. `buses` becomes `2`. Queue: `[1]`.
5. Layer 2: pop route `1`. Check its stops `3,6,7` for `target=6` — found! Return `buses = 2`.

## 7. Gotchas & takeaways

> Gotcha: building the graph over stops directly (treating every stop reachable via any route as a single unweighted hop) miscounts buses — moving between two stops on the *same* route costs zero extra buses, which a stop-level graph cannot represent without extra bookkeeping. Route-level breadth-first search sidesteps this entirely.

- Signal: "minimum number of vehicles/legs/transfers," where each vehicle can visit many stops "for free," is breadth-first search over the *vehicles/routes*, not the individual stops.
- Mark routes (not stops) as visited, to avoid ever re-expanding the same route and to guarantee breadth-first search's minimum-hop-count property holds.
- Related problems: Network Delay Time (weighted analogue), Cheapest Flights Within K Stops (bounded-hop analogue).
