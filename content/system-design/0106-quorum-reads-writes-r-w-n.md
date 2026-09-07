---
card: system-design
gi: 106
slug: quorum-reads-writes-r-w-n
title: Quorum reads/writes (R + W > N)
---

## 1. What it is

A **quorum** is the minimum number of replica nodes that must participate in a read or write for it to count as successful. With `N` replicas total, a write needs `W` acknowledgments and a read needs `R` responses. The key rule, **W + R > N**, guarantees that every read quorum and every write quorum must share at least one common node — so any read is mathematically guaranteed to overlap with the latest successful write.

## 2. Why & when

Waiting for all `N` replicas on every write (as full synchronous replication would) is slow and fragile — one slow or down node blocks everything. Waiting for only 1 replica risks missing the latest write entirely on a later read. Quorums let you tune this trade-off precisely: pick `W` and `R` so their sum exceeds `N`, and you get a mathematical guarantee that reads see the latest write, without needing every single node to participate in every operation. Use quorums in leaderless or multi-node replicated systems (Dynamo-style databases like Cassandra) where you want tunable consistency without a single leader as a bottleneck.

## 3. Core concept

- **The overlap guarantee:** if `W + R > N`, then any set of `W` nodes that acknowledged a write and any set of `R` nodes contacted by a read must share at least one node in common — this is simple pigeonhole reasoning: two subsets of an `N`-sized set whose sizes sum to more than `N` cannot be disjoint.
- **Common configurations:** `N=3, W=2, R=2` (a frequent default: tolerates one node being down for either a read or a write, and `2+2=4 > 3`). `N=3, W=3, R=1` (strong write, fast read). `N=3, W=1, R=3` (fast write, strong read).
- **Tuning the trade-off:** a higher `W` makes writes slower but reads can be faster (and vice versa for a higher `R`); either can be raised to strengthen the guarantee at the cost of that operation's latency and availability.
- **Not a full substitute for strong consistency:** quorums guarantee a read overlaps with the *latest acknowledged* write, but concurrent writes racing each other still need conflict resolution (see [conflict resolution](0109-conflict-resolution-last-write-wins-vector-clocks-crdts.md)), and a read might see multiple different "latest" candidates if writes are still in flight.
- **Sloppy quorums (an availability escape valve):** some systems allow a write to succeed on any `W` reachable nodes, even ones outside the "correct" replica set for that key, to keep writes available during a partition — trading some consistency guarantees for availability.

## 4. Diagram

```
N = 5 replica nodes:  [1] [2] [3] [4] [5]

Write with W=3: write reaches nodes {1, 2, 4}  (any 3 of 5)
Read with R=3:  read contacts nodes {2, 3, 5}  (any 3 of 5)

Overlap check: {1,2,4} ∩ {2,3,5} = {2}  -- node 2 is in BOTH sets.
Since W + R = 6 > N = 5, this overlap is GUARANTEED for any choice
of which 3 nodes each operation happens to use.
```
*Caption: any W-sized write set and any R-sized read set must share a node whenever W + R > N — this is what guarantees the read sees the write.*

## 5. Runnable example

**Level 1 — Basic.** Model N=5 nodes; perform a quorum write to W=3 of them, then a quorum read from R=3, and find the overlapping node.

**Level 2 — Verify the guarantee exhaustively.** Check every possible combination of write-set and read-set for a given N, W, R and confirm they always overlap.

**Level 3 — Show the guarantee breaking when W + R <= N.** Pick a combination that violates the rule and find a write/read pair with no overlap.

```java
// QuorumReplication.java
import java.util.*;

public class QuorumReplication {

    static Set<Integer> overlap(Set<Integer> writeSet, Set<Integer> readSet) {
        Set<Integer> result = new TreeSet<>(writeSet);
        result.retainAll(readSet);
        return result;
    }

    // generate all size-k subsets of {0, 1, ..., n-1}
    static List<Set<Integer>> subsetsOfSize(int n, int k) {
        List<Set<Integer>> result = new ArrayList<>();
        combine(n, k, 0, new TreeSet<>(), result);
        return result;
    }

    static void combine(int n, int k, int start, Set<Integer> current, List<Set<Integer>> result) {
        if (current.size() == k) { result.add(new TreeSet<>(current)); return; }
        for (int i = start; i < n; i++) {
            current.add(i);
            combine(n, k, i + 1, current, result);
            current.remove(i);
        }
    }

    static boolean allCombinationsOverlap(int n, int w, int r) {
        for (Set<Integer> writeSet : subsetsOfSize(n, w)) {
            for (Set<Integer> readSet : subsetsOfSize(n, r)) {
                if (overlap(writeSet, readSet).isEmpty()) return false;
            }
        }
        return true;
    }

    public static void main(String[] args) {
        // Level 1: N=5, W=3, R=3 - a concrete write set and read set, find their overlap.
        Set<Integer> writeSet = Set.of(0, 1, 3); // nodes 1, 2, 4 (0-indexed)
        Set<Integer> readSet = Set.of(1, 2, 4);  // nodes 2, 3, 5 (0-indexed)
        System.out.println("write reached nodes: " + writeSet);
        System.out.println("read contacted nodes: " + readSet);
        System.out.println("overlap: " + overlap(writeSet, readSet) + " -> read is guaranteed to see the write");

        // Level 2: verify N=5, W=3, R=3 overlaps for EVERY possible pair of write/read sets.
        int n = 5, w = 3, r = 3;
        boolean guaranteed = allCombinationsOverlap(n, w, r);
        System.out.println("N=" + n + ", W=" + w + ", R=" + r + " (W+R=" + (w + r) + " > N=" + n + "): "
            + "overlap guaranteed for ALL combinations? " + guaranteed);

        // Level 3: N=5, W=2, R=2 - W+R=4 is NOT > N=5, so the guarantee should fail for some combination.
        int w2 = 2, r2 = 2;
        boolean guaranteed2 = allCombinationsOverlap(n, w2, r2);
        System.out.println("N=" + n + ", W=" + w2 + ", R=" + r2 + " (W+R=" + (w2 + r2) + ", NOT > N=" + n + "): "
            + "overlap guaranteed for ALL combinations? " + guaranteed2);
        if (!guaranteed2) {
            for (Set<Integer> ws : subsetsOfSize(n, w2)) {
                for (Set<Integer> rs : subsetsOfSize(n, r2)) {
                    if (overlap(ws, rs).isEmpty()) {
                        System.out.println("counterexample with no overlap: write=" + ws + ", read=" + rs);
                        return;
                    }
                }
            }
        }
    }
}
```

**How to run:** save as `QuorumReplication.java`, then run `java QuorumReplication.java`.

## 6. Walkthrough

1. Level 1 picks one concrete write set (`{0,1,3}`) and read set (`{1,2,4}`) out of 5 nodes; `overlap` intersects them and finds node `1` in both, confirming the read is guaranteed to see the write for this particular pair.
2. Level 2's `allCombinationsOverlap` exhaustively generates *every* possible 3-node write set and *every* possible 3-node read set out of 5 nodes, and checks that all of them intersect — proving the `W+R>N` guarantee holds not just for one lucky pair, but for every possible pair, which is what makes it a mathematical guarantee rather than a coincidence.
3. The printed result for `N=5, W=3, R=3` (where `W+R=6 > 5`) confirms `guaranteed = true`.
4. Level 3 deliberately picks `W=2, R=2` where `W+R=4` is *not* greater than `N=5`, and the same exhaustive check now returns `false`.
5. The code then searches for and prints a concrete counterexample — a write set and read set that do not overlap at all — demonstrating exactly why the `W+R>N` inequality matters: without it, a read can genuinely miss every node that has the latest write.

## 7. Gotchas & takeaways

> Gotcha: the `W+R>N` guarantee only covers whether a read *can* see the latest acknowledged write — it does not resolve what happens when two writes race each other concurrently. A read that overlaps with two different, concurrent writes still needs a conflict-resolution rule to decide which value to report.

- A quorum requires only `W` (of `N`) nodes to acknowledge a write and `R` (of `N`) nodes to answer a read, avoiding the cost of contacting every node on every operation.
- The rule `W + R > N` guarantees every read quorum overlaps with every write quorum, by simple counting: two subsets of size summing past `N` cannot be disjoint.
- Raising `W` or `R` strengthens that operation's guarantee but costs it latency and availability; the values are tunable per system.
- Related concepts: [Leaderless replication (Dynamo-style)](0100-leaderless-replication-dynamo-style.md) (the system style that popularized this pattern), [Strong consistency](0103-strong-consistency.md) (what a well-chosen quorum can approximate), [CAP theorem](0107-cap-theorem.md) (the broader trade-off quorum tuning navigates).
