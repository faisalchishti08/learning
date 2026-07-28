---
card: leetcode-patterns
gi: 553
slug: cheapest-flights-within-k-stops
title: Cheapest Flights Within K Stops
---

## 1. What it is

Given `n` cities connected by directed flights `flights[i] = [from, to, price]`, find the cheapest price from `src` to `dst` using **at most `k` stops** (meaning at most `k+1` flights, since `k` stops means `k` intermediate cities). Return `-1` if no such route exists. Example: `flights = [[0,1,100],[1,2,100],[0,2,500]]`, `src=0`, `dst=2`, `k=1` → `200` (via `0->1->2`, using exactly 1 stop, cheaper than the direct `500` flight).

## 2. Why & when

Plain Dijkstra's algorithm optimizes for cost alone and can "finalize" a node too early, using a path that happens to have too many stops — it has no way to track "stops used" as part of what makes one path better than another. This is a shortest-path variant with an **added constraint** on path length, best solved with a **bounded Bellman-Ford**: relax edges for exactly `k+1` rounds, using distances frozen from the *previous* round only. Constraints: up to 100 cities, 10,000 flights, `k` up to `n-1`.

## 3. Core concept

**Key idea:** run Bellman-Ford, but limit it to exactly `k + 1` rounds of relaxation (since a path with at most `k` stops has at most `k + 1` edges). Critically, each round must relax edges using the distance array **as it stood at the start of that round** — not distances already updated within the same round — otherwise a single round could "chain" multiple hops together and silently violate the stop limit.

**Steps:**
1. Initialize `dist[src] = 0`, everything else infinity.
2. Repeat `k + 1` times: make a **copy** of the current `dist[]` array (call it `prevDist`). For every flight `(u, v, price)`, if `prevDist[u] + price < dist[v]`, update `dist[v] = prevDist[u] + price`.
3. After all rounds, return `dist[dst]` if it is finite, else `-1`.

**Why copying `dist[]` before each round is essential:** without the copy, an update to `dist[u]` made earlier *in the same round* could immediately be used to relax `dist[v]` in that same round — effectively using two edges within what should count as one round, letting a path sneak in more hops than the stop limit allows.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Round-by-round relaxation using a frozen previous-round distance array, capped at k+1 rounds">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">round 1 (1 edge used): dist[1] = 100 (via 0-&gt;1)</text>
    <text x="20" y="50" fill="#79c0ff">round 2 (2 edges used): dist[2] = min(500, prevDist[1]+100=200) = 200</text>
    <text x="20" y="80" fill="#3fb950">k=1 stop allowed -&gt; 2 rounds total (k+1 edges) -&gt; stop after round 2</text>
    <text x="20" y="115" fill="#f0883e">using dist[1] updated THIS round instead of prevDist would let a 3rd hop sneak in</text>
  </g>
</svg>

Each round adds exactly one more edge to every reachable path; freezing the previous round's distances prevents a single round from silently using two edges at once.

## 5. Runnable example

**Level 1 — Brute force.** Depth-first search every path from `src` to `dst`, tracking stops used and cost, pruning paths that exceed `k` stops. Exponential in the worst case, though pruning helps.

**KEY INSIGHT:** bounding Bellman-Ford to exactly `k+1` relaxation rounds, using a frozen snapshot of the previous round's distances, directly enforces the stop limit without needing to enumerate paths.

**Level 2 — Optimal.** Bounded Bellman-Ford, O(k · E).

**Level 3 — Hardened.** Handles `k = 0` (direct flights only), a `dst` unreachable within the stop limit (`-1`), and multiple flights between the same pair of cities with different prices.

```java
// CheapestFlightsWithinKStops.java
import java.util.*;

public class CheapestFlightsWithinKStops {

    static int findCheapestPrice(int n, int[][] flights, int src, int dst, int k) {
        int[] dist = new int[n];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[src] = 0;

        for (int round = 0; round <= k; round++) {
            int[] prevDist = dist.clone(); // freeze this round's starting distances
            for (int[] flight : flights) {
                int u = flight[0], v = flight[1], price = flight[2];
                if (prevDist[u] != Integer.MAX_VALUE && prevDist[u] + price < dist[v]) {
                    dist[v] = prevDist[u] + price;
                }
            }
        }
        return dist[dst] == Integer.MAX_VALUE ? -1 : dist[dst];
    }

    public static void main(String[] args) {
        int[][] flights1 = {{0, 1, 100}, {1, 2, 100}, {0, 2, 500}};
        System.out.println(findCheapestPrice(3, flights1, 0, 2, 1)); // 200

        int[][] flights2 = {{0, 1, 100}, {1, 2, 100}, {0, 2, 500}};
        System.out.println(findCheapestPrice(3, flights2, 0, 2, 0)); // 500, direct only
        System.out.println(findCheapestPrice(3, flights2, 0, 2, 5)); // 200, extra stops allowed but unused
    }
}
```

**How to run:** save as `CheapestFlightsWithinKStops.java`, then run `java CheapestFlightsWithinKStops.java`.

## 6. Walkthrough

Trace `findCheapestPrice(3, [[0,1,100],[1,2,100],[0,2,500]], 0, 2, 1)`, so `k+1 = 2` rounds:

| round | prevDist | updates | dist after |
|---|---|---|---|
| 0 | [0, inf, inf] | flight 0->1: `prevDist[0]+100=100 < inf` → dist[1]=100. flight 0->2: `prevDist[0]+500=500 < inf` → dist[2]=500. flight 1->2: `prevDist[1]=inf`, skip. | [0, 100, 500] |
| 1 | [0, 100, 500] | flight 0->1: `100 < 100`? no. flight 0->2: `500 < 500`? no. flight 1->2: `prevDist[1]+100=200 < 500` → dist[2]=200. | [0, 100, 200] |

After 2 rounds, `dist[2] = 200` — the answer.

## 7. Gotchas & takeaways

> Gotcha: reusing the same `dist[]` array for both reading and writing within one round (skipping the `prevDist` snapshot) can let a path use 2 edges within a single round if the edges happen to be processed in a favorable order — silently allowing more stops than `k` permits, and giving a wrong (too-low) answer.

- Signal: "shortest/cheapest path with a bound on the number of edges/stops used" needs bounded Bellman-Ford, not plain Dijkstra, since Dijkstra has no way to track "edges used so far" as part of its greedy choice.
- Run exactly `k + 1` rounds, since `k` stops means `k + 1` edges on the path.
- Related problems: Network Delay Time, Path with Maximum Probability, Find the City With the Smallest Number of Neighbors at a Threshold Distance.
