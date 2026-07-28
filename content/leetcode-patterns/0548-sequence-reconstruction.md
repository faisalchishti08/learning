---
card: leetcode-patterns
gi: 548
slug: sequence-reconstruction
title: Sequence Reconstruction
---

## 1. What it is

Given an array `nums` (a permutation of `1` to `n`) and a list of sequences, determine whether `nums` is the **unique** shortest common supersequence implied by all the pairwise orderings inside `sequences`. In plain terms: do the sequences' adjacent-pair constraints force exactly one possible ordering, and is that ordering `nums`? Example: `nums = [1,2,3]`, `sequences = [[1,2],[1,3],[2,3]]` → `true`.

## 2. Why & when

Every sequence's adjacent pairs are ordering constraints, exactly like [Alien Dictionary](0545-alien-dictionary.md)'s adjacent-word comparisons — this is a [topological sort](0537-topological-sort-signal-ordering-with-dependency-prerequisit.md) with an extra uniqueness requirement. A topological order is unique exactly when, at every step of Kahn's algorithm, there is only ever **one** node available to pick next (the queue never holds more than one node at a time). Constraints: up to 10,000 numbers and sequences.

## 3. Core concept

**Key idea:** build a graph where each sequence's adjacent pair `a, b` becomes an edge `a -> b`. Run Kahn's algorithm. If at any point the queue holds more than one available node simultaneously, there is a choice — meaning more than one valid order exists, so the reconstruction is not unique. Compare the single valid order Kahn's algorithm produces (when it is unique) against `nums`.

**Steps:**
1. Build a graph over values `1..n` and an `inDegree[]` array, adding an edge for every adjacent pair within every sequence.
2. Push every value with `inDegree == 0` into a queue.
3. Repeatedly: **if the queue's size is ever greater than 1, return `false` immediately** — more than one node is available, so the order is not forced to be unique. Otherwise, pop the single node, append it to the built order, and decrement its neighbors' in-degrees, pushing any that reach zero.
4. After the loop, return `true` only if the built order has length `n` (no cycle) AND matches `nums` exactly.

**Why checking the queue size at every step (not just once) is essential:** uniqueness must hold at *every* step of the process, not just the beginning — even if the first few picks are forced, a later step might present two equally valid next choices, which still breaks uniqueness. Checking `queue.size() > 1` right before each pop catches this at every layer.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="At each step of Kahn's algorithm, only one node is ever available, forcing a unique order 1, 2, 3">
  <g font-family="sans-serif" font-size="13">
    <circle cx="100" cy="70" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="100" y="75" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="300" cy="70" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="300" y="75" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="500" cy="70" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="500" y="75" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="118" y1="70" x2="282" y2="70" stroke="#8b949e" marker-end="url(#a8)"/>
    <line x1="318" y1="70" x2="482" y2="70" stroke="#8b949e" marker-end="url(#a8)"/>
    <defs><marker id="a8" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0L6,3L0,6Z" fill="#8b949e"/></marker></defs>
    <text x="300" y="120" fill="#3fb950" text-anchor="middle">queue always holds exactly 1 node at each step -&gt; unique order</text>
  </g>
</svg>

At every step, only one node has all its prerequisites satisfied — the queue never has a real choice, so the order is forced and unique.

## 5. Runnable example

**Level 1 — Brute force.** Generate the topological order using standard Kahn's algorithm, then separately check every possible alternate order by trying to swap adjacent independent elements. Complex and slow.

**KEY INSIGHT:** watching the queue's size at every single step of Kahn's algorithm is a direct, cheap way to detect whether more than one valid choice ever existed — no separate alternate-order search needed.

**Level 2 — Optimal.** Kahn's algorithm with a queue-size check at each step, O(n + total sequence length).

**Level 3 — Hardened.** Handles a cycle (built order shorter than `n`, return `false`) and sequences that reference values not forming a full chain of `1..n`.

```java
// SequenceReconstruction.java
import java.util.*;

public class SequenceReconstruction {

    static boolean sequenceReconstruction(int[] nums, List<List<Integer>> sequences) {
        int n = nums.length;
        List<Set<Integer>> graph = new ArrayList<>();
        for (int i = 0; i <= n; i++) graph.add(new HashSet<>());
        int[] inDegree = new int[n + 1];

        for (List<Integer> seq : sequences) {
            for (int i = 0; i < seq.size() - 1; i++) {
                int a = seq.get(i), b = seq.get(i + 1);
                if (graph.get(a).add(b)) {
                    inDegree[b]++;
                }
            }
        }

        Deque<Integer> queue = new ArrayDeque<>();
        for (int i = 1; i <= n; i++) {
            if (inDegree[i] == 0) queue.add(i);
        }

        List<Integer> order = new ArrayList<>();
        while (!queue.isEmpty()) {
            if (queue.size() > 1) return false; // more than one choice available: not unique
            int u = queue.poll();
            order.add(u);
            for (int v : graph.get(u)) {
                if (--inDegree[v] == 0) queue.add(v);
            }
        }

        if (order.size() != n) return false; // cycle, no full order at all

        for (int i = 0; i < n; i++) {
            if (!order.get(i).equals(nums[i])) return false;
        }
        return true;
    }

    public static void main(String[] args) {
        int[] nums = {1, 2, 3};
        List<List<Integer>> sequences = Arrays.asList(
                Arrays.asList(1, 2), Arrays.asList(1, 3), Arrays.asList(2, 3));
        System.out.println(sequenceReconstruction(nums, sequences)); // true

        List<List<Integer>> ambiguous = Arrays.asList(
                Arrays.asList(1, 2), Arrays.asList(1, 3));
        System.out.println(sequenceReconstruction(nums, ambiguous)); // false, 2 and 3 both available after 1
    }
}
```

**How to run:** save as `SequenceReconstruction.java`, then run `java SequenceReconstruction.java`.

## 6. Walkthrough

Trace `sequenceReconstruction([1,2,3], [[1,2],[1,3],[2,3]])`:

| step | inDegree | queue | order |
|---|---|---|---|
| build | `1`→0, `2`→1, `3`→2 | `[1]` | `[]` |
| pop 1 | `2`→0, `3`→2 | `[2]` (queue size 1, OK) | `[1]` |
| pop 2 | `3`→1 | `[]` initially, then `3`→0, `[3]` | `[1,2]` |
| pop 3 | unchanged | `[]` | `[1,2,3]` |

At every step, the queue held exactly one node, so the order is unique. `order = [1,2,3]` matches `nums` exactly — return `true`.

Now trace the ambiguous case `[[1,2],[1,3]]`: after popping `1`, both `2` and `3` reach in-degree `0` simultaneously, so the queue holds `[2, 3]` — size `2` — the function returns `false` immediately, without needing to check anything further.

## 7. Gotchas & takeaways

> Gotcha: checking `queue.size() > 1` only once, before the loop starts, misses cases where the ambiguity appears at a *later* step — the check must run at the top of every loop iteration, right before each pop.

- Signal: "is this the unique topological order implied by these constraints" is answered by checking the queue never exceeds size 1 during Kahn's algorithm, at every step.
- Deduplicate edges when building the graph (`Set.add` returning `false` for a repeat) so a repeated pair across multiple sequences does not double-count `inDegree`.
- Related problems: Alien Dictionary (also derives edges from adjacent pairs), Course Schedule II.
