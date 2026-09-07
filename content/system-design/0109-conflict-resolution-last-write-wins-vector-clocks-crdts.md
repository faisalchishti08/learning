---
card: system-design
gi: 109
slug: conflict-resolution-last-write-wins-vector-clocks-crdts
title: Conflict resolution (last-write-wins, vector clocks, CRDTs)
---

## 1. What it is

**Conflict resolution** is how a replicated system decides what to do when two writes to the same key happen concurrently, on different nodes, without either node knowing about the other's write at the time. Three common strategies are: **last-write-wins (LWW)**, which keeps whichever write has the later timestamp and discards the other; **vector clocks**, which detect and preserve the fact that two writes were concurrent instead of guessing an order; and **CRDTs** (Conflict-free Replicated Data Types), which are data structures specifically designed so concurrent updates can always be merged automatically, without losing information.

## 2. Why & when

Any system with more than one node that can accept writes independently — [multi-leader replication](0099-multi-leader-replication.md) or [leaderless replication](0100-leaderless-replication-dynamo-style.md) — will eventually have two nodes accept different writes to the same key before either has heard from the other. Something must decide the final value once both writes are known to all replicas. Use last-write-wins when losing one of the two writes is an acceptable trade-off for simplicity (a "last seen at" timestamp, a cache entry). Use vector clocks when you need to *detect* a genuine conflict and hand it to the application or the user to resolve (a shopping cart, a document edit). Use a CRDT when the data type allows a merge that keeps information from both writes automatically (a counter, a set, a collaboratively edited list).

## 3. Core concept

- **Last-write-wins (LWW):** attach a timestamp to every write; when two versions of a key are found, keep the one with the higher timestamp, discard the other. Simple, but silently loses data — the discarded write is gone with no trace.
- **Vector clocks:** each node keeps a counter per node (e.g. `{nodeA: 2, nodeB: 1}`). A write increments the writing node's own counter. Comparing two vector clocks tells you if one clock is *strictly greater* than the other in every position (meaning one write causally followed the other, so no conflict), or if neither dominates the other (meaning the writes were truly concurrent — a real conflict to surface).
- **Surfacing conflicts:** once a vector clock detects a real conflict, the system keeps *both* versions and returns both to the application (or the user) to resolve — for example, a shopping cart showing "you had item A on one device and item B on another; here's the merge".
- **CRDTs:** data types with a merge operation that is mathematically guaranteed to produce the same result no matter what order updates are applied in. A grow-only counter CRDT, for example, tracks each node's own increments separately and sums them — merging two nodes' counters can never lose an increment, unlike a plain integer with last-write-wins.
- **Choosing between them:** LWW is easiest but loses data silently; vector clocks preserve information about the conflict but push the resolution work onto the application; CRDTs need a data-type-specific design but resolve automatically with no data loss and no manual step.

## 4. Diagram

```
LAST-WRITE-WINS:                    VECTOR CLOCKS:
  Write A: value=5, t=100              Write A: {nodeA:1} on nodeA
  Write B: value=9, t=101              Write B: {nodeB:1} on nodeB
  -> keep B (9), DISCARD A silently    -> neither dominates -> CONFLICT detected,
                                           both versions kept, given to app to merge

CRDT (grow-only counter):
  nodeA increments its own slot: {nodeA:3, nodeB:0}
  nodeB increments its own slot: {nodeA:0, nodeB:2}
  MERGE (take max per slot): {nodeA:3, nodeB:2} -> total = 5
  -> both increments preserved, no data lost, no manual step needed
```
*Caption: LWW discards one write; vector clocks detect and preserve the conflict for manual resolution; CRDTs merge automatically with no loss.*

## 5. Runnable example

**Level 1 — Basic.** Last-write-wins: compare two timestamped writes and keep the later one.

**Level 2 — Vector clocks.** Detect whether two writes are causally ordered or truly concurrent.

**Level 3 — CRDT counter.** Merge two nodes' independent increments into a correct total with no data loss.

```java
// ConflictResolution.java
import java.util.*;

public class ConflictResolution {

    // Level 1: last-write-wins.
    record TimestampedWrite(int value, long timestamp) {}

    static TimestampedWrite lastWriteWins(TimestampedWrite a, TimestampedWrite b) {
        return a.timestamp() >= b.timestamp() ? a : b; // the other write is silently discarded
    }

    // Level 2: vector clocks - compare {nodeId -> counter} maps.
    enum Order { A_BEFORE_B, B_BEFORE_A, CONCURRENT }

    static Order compareVectorClocks(Map<String, Integer> a, Map<String, Integer> b) {
        boolean aLessOrEqual = true, bLessOrEqual = true;
        Set<String> allNodes = new TreeSet<>();
        allNodes.addAll(a.keySet()); allNodes.addAll(b.keySet());
        for (String node : allNodes) {
            int av = a.getOrDefault(node, 0), bv = b.getOrDefault(node, 0);
            if (av > bv) bLessOrEqual = false;
            if (bv > av) aLessOrEqual = false;
        }
        if (aLessOrEqual && !bLessOrEqual) return Order.A_BEFORE_B;
        if (bLessOrEqual && !aLessOrEqual) return Order.B_BEFORE_A;
        return Order.CONCURRENT; // neither dominates - a genuine conflict
    }

    public static void main(String[] args) {
        // Level 1: LWW keeps the later write, silently drops the other.
        TimestampedWrite writeA = new TimestampedWrite(5, 100);
        TimestampedWrite writeB = new TimestampedWrite(9, 101);
        TimestampedWrite winner = lastWriteWins(writeA, writeB);
        System.out.println("LWW result: " + winner.value() + " (write with value=5 was silently discarded)");

        // Level 2: vector clocks detect a genuine conflict between two independent writes.
        Map<String, Integer> clockA = Map.of("nodeA", 1); // write happened only on nodeA, its first write
        Map<String, Integer> clockB = Map.of("nodeB", 1); // write happened only on nodeB, its first write
        Order order = compareVectorClocks(clockA, clockB);
        System.out.println("comparing " + clockA + " vs " + clockB + " -> " + order);
        if (order == Order.CONCURRENT) {
            System.out.println("-> a real conflict: BOTH versions are kept and handed to the application to merge");
        }

        // A causally-ordered pair, for contrast: B's clock strictly dominates A's.
        Map<String, Integer> clockC = Map.of("nodeA", 1);
        Map<String, Integer> clockD = Map.of("nodeA", 1, "nodeB", 1); // saw A's write, then added its own
        System.out.println("comparing " + clockC + " vs " + clockD + " -> " + compareVectorClocks(clockC, clockD));

        // Level 3: CRDT grow-only counter - merge two nodes' independent increments, losing nothing.
        Map<String, Integer> counterOnNodeA = Map.of("nodeA", 3, "nodeB", 0); // nodeA incremented 3 times locally
        Map<String, Integer> counterOnNodeB = Map.of("nodeA", 0, "nodeB", 2); // nodeB incremented 2 times locally
        Map<String, Integer> merged = new TreeMap<>();
        for (String node : Set.of("nodeA", "nodeB")) {
            merged.put(node, Math.max(counterOnNodeA.getOrDefault(node, 0), counterOnNodeB.getOrDefault(node, 0)));
        }
        int total = merged.values().stream().mapToInt(Integer::intValue).sum();
        System.out.println("CRDT merge of per-node slots: " + merged + " -> total = " + total + " (both nodes' increments preserved)");
    }
}
```

**How to run:** save as `ConflictResolution.java`, then run `java ConflictResolution.java`.

## 6. Walkthrough

1. `lastWriteWins` compares `writeA` (timestamp 100) and `writeB` (timestamp 101) and returns `writeB`; the printed line notes that `writeA`'s value (`5`) is now gone entirely — LWW's defining trade-off.
2. `compareVectorClocks(clockA, clockB)` checks each node's counter across both clocks: `nodeA`'s counter is higher in `clockA`, but `nodeB`'s counter is higher in `clockB`, so neither clock dominates the other — the function returns `CONCURRENT`, correctly identifying a genuine, unresolved conflict.
3. The contrasting pair, `clockC` versus `clockD`, has `clockD` matching `clockC`'s `nodeA` count *and* adding its own `nodeB` increment — `clockC` is less-than-or-equal to `clockD` in every position, so the function returns `A_BEFORE_B`, correctly identifying that `clockD`'s write causally followed `clockC`'s, not a conflict at all.
4. Level 3 models a CRDT counter as a map of per-node increment counts; `counterOnNodeA` recorded 3 increments from `nodeA` (and knows nothing yet about `nodeB`'s), while `counterOnNodeB` recorded 2 increments from `nodeB`.
5. The merge takes the maximum of each node's slot across both copies (`{nodeA: 3, nodeB: 2}`), then sums them to `5` — both nodes' independent increments survive the merge intact, unlike LWW, which would have kept only one node's count and lost the other's entirely.

## 7. Gotchas & takeaways

> Gotcha: vector clocks tell you *that* two writes conflicted, but they do not tell you *how* to merge them — that decision is pushed to the application (or the user), and if the application does not handle the `CONCURRENT` case explicitly, it is easy to accidentally fall back to picking one arbitrarily, silently reintroducing LWW's data-loss problem anyway.

- Last-write-wins is the simplest strategy but silently discards one of two conflicting writes.
- Vector clocks correctly distinguish real concurrency from causal ordering, but only detect conflicts — they do not resolve them.
- CRDTs bake a safe, automatic merge directly into the data type, so no information is lost and no manual resolution step is needed, at the cost of only working for data types that have a valid CRDT design.
- Related concepts: [Multi-leader replication](0099-multi-leader-replication.md) and [Leaderless replication (Dynamo-style)](0100-leaderless-replication-dynamo-style.md) (the replication styles that create these conflicts), [Causal & monotonic consistency](0105-causal-monotonic-consistency.md) (built on the same causal-ordering idea vector clocks use).
