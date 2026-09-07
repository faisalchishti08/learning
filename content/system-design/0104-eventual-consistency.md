---
card: system-design
gi: 104
slug: eventual-consistency
title: Eventual consistency
---

## 1. What it is

**Eventual consistency** guarantees that if no new writes happen to a piece of data, every replica of it will *eventually* converge to the same value — but it makes no promise about how long that convergence takes, or what a read will see in the meantime. Unlike [strong consistency](0103-strong-consistency.md), a read immediately after a write may return an old value; eventual consistency only promises the staleness is temporary.

## 2. Why & when

Guaranteeing every read sees the latest write ([strong consistency](0103-strong-consistency.md)) requires coordination, which costs latency and can force a system to refuse requests during a network problem. Eventual consistency drops that guarantee in exchange for every node being able to answer reads and writes independently, immediately, without checking with anyone else. Use it for data where a brief window of staleness is harmless — a social media "like" count, a product view counter, a DNS record, a cache — and where you need high availability and low latency more than an always-current answer.

## 3. Core concept

- **No coordination on the read or write path:** any replica can answer a read with whatever value it currently has, and any replica can accept a write and propagate it in the background.
- **Convergence, not correctness-at-every-instant:** the guarantee is only that replicas *will* agree once writes stop and propagation finishes — not that they agree right now.
- **Propagation mechanisms:** asynchronous replication (see [synchronous vs asynchronous replication](0101-synchronous-vs-asynchronous-replication.md)), gossip protocols, or background anti-entropy processes all move writes from where they landed to every other replica over time.
- **Conflicting concurrent writes still need resolution:** if two replicas each accept a different write to the same key before either has heard from the other, eventual consistency alone does not say which one wins — a resolution rule like last-write-wins or a CRDT is still needed (see [conflict resolution](0109-conflict-resolution-last-write-wins-vector-clocks-crdts.md)).
- **Bounded staleness (a stronger variant):** some systems promise a maximum lag, e.g. "no replica is more than 5 seconds behind", giving a predictable upper bound instead of an unspecified "eventually".

## 4. Diagram

```
t=0: write "likes = 100" lands on Node A only.

t=0 (immediately after): read from Node B -> "likes = 99" (stale, but valid answer)
t=0 (immediately after): read from Node C -> "likes = 99" (stale, but valid answer)

t=1: background replication propagates the write to Node B.
t=2: background replication propagates the write to Node C.

t=2 (no new writes since t=0): read from ANY node -> "likes = 100"
   -> all nodes have now CONVERGED to the same value.
```
*Caption: reads may briefly disagree right after a write, but once propagation finishes, every node converges to the same answer.*

## 5. Runnable example

**Level 1 — Basic.** Three nodes; a write lands on one node and reads from the others are briefly stale.

**Level 2 — Convergence over time.** Simulate propagation delay, then confirm all nodes agree once it completes.

**Level 3 — Concurrent writes needing resolution.** Two nodes each accept a different write before hearing from each other; resolve so both converge.

```java
// EventualConsistency.java
import java.util.*;

public class EventualConsistency {

    static Map<String, Integer> nodeA = new HashMap<>();
    static Map<String, Integer> nodeB = new HashMap<>();
    static Map<String, Integer> nodeC = new HashMap<>();
    static List<Map<String, Integer>> allNodes = List.of(nodeA, nodeB, nodeC);

    public static void main(String[] args) {
        // Level 1: write lands on nodeA only; nodeB and nodeC still have the old value.
        nodeA.put("likes", 99);
        nodeB.put("likes", 99);
        nodeC.put("likes", 99);
        nodeA.put("likes", 100); // new write, only applied to nodeA so far

        System.out.println("immediately after write -> nodeA: " + nodeA.get("likes")
            + ", nodeB: " + nodeB.get("likes") + ", nodeC: " + nodeC.get("likes"));
        System.out.println("-> nodeB and nodeC are stale, but this is expected and temporary");

        // Level 2: background propagation runs, one node at a time, simulating a delay.
        System.out.println("propagating to nodeB...");
        nodeB.put("likes", nodeA.get("likes"));
        System.out.println("propagating to nodeC...");
        nodeC.put("likes", nodeA.get("likes"));

        boolean converged = allNodes.stream().allMatch(n -> n.get("likes").equals(nodeA.get("likes")));
        System.out.println("all nodes now: " + nodeA.get("likes") + ", " + nodeB.get("likes") + ", " + nodeC.get("likes"));
        System.out.println("converged: " + converged);

        // Level 3: concurrent writes on 2 nodes before either hears from the other.
        record Versioned(int value, long timestamp) {}
        Map<String, Versioned> nodeX = new HashMap<>();
        Map<String, Versioned> nodeY = new HashMap<>();
        nodeX.put("counter", new Versioned(41, 1000)); // nodeX accepts a write at t=1000
        nodeY.put("counter", new Versioned(42, 1001)); // nodeY accepts a DIFFERENT write, slightly later

        System.out.println("before resolution -> nodeX: " + nodeX.get("counter").value() + ", nodeY: " + nodeY.get("counter").value());

        // resolution rule: last-write-wins by timestamp, applied once each node hears the other's write.
        Versioned xVal = nodeX.get("counter"), yVal = nodeY.get("counter");
        Versioned resolved = xVal.timestamp() >= yVal.timestamp() ? xVal : yVal;
        nodeX.put("counter", resolved);
        nodeY.put("counter", resolved);

        System.out.println("after resolution -> nodeX: " + nodeX.get("counter").value() + ", nodeY: " + nodeY.get("counter").value());
        System.out.println("-> both converged on the value with the later timestamp");
    }
}
```

**How to run:** save as `EventualConsistency.java`, then run `java EventualConsistency.java`.

## 6. Walkthrough

1. The write `nodeA.put("likes", 100)` only updates `nodeA`; `nodeB` and `nodeC` still hold `99` because no propagation has happened yet — the first print line shows this three-way disagreement directly.
2. The propagation lines copy `nodeA`'s current value into `nodeB`, then into `nodeC`, one at a time, modeling the delay real asynchronous replication or a gossip protocol would take.
3. After both propagation steps run, the `converged` check confirms all three nodes now hold the identical value `100` — the eventual-consistency guarantee has been fulfilled, since no further writes happened during propagation.
4. Level 3 sets up a harder case: `nodeX` and `nodeY` each independently accept a *different* write to the same key, at close but different timestamps, before either has heard from the other — a genuine conflict, not just staleness.
5. The resolution step picks whichever `Versioned` value has the higher timestamp (`42` at `1001`) and applies it to both nodes; the final print confirms both `nodeX` and `nodeY` now agree, showing that eventual consistency's convergence promise still needs an explicit conflict-resolution rule when writes genuinely raced.

## 7. Gotchas & takeaways

> Gotcha: eventual consistency promises convergence only once writes stop. Under continuous, ongoing writes (a busy counter, a hot key), replicas may never actually catch up to each other in practice, even though the formal guarantee is technically not violated. Do not treat "eventually" as a bounded or short time window unless your specific system also documents a concrete staleness bound.

- Eventual consistency lets every replica answer reads and writes immediately and independently, at the cost of temporary disagreement between replicas.
- The only formal guarantee is convergence after writes stop; it says nothing about how long convergence takes.
- Concurrent conflicting writes still need an explicit resolution rule (like last-write-wins) for replicas to actually converge to the same value.
- Related concepts: [Strong consistency](0103-strong-consistency.md) (the opposite trade-off), [Conflict resolution](0109-conflict-resolution-last-write-wins-vector-clocks-crdts.md) (how concurrent writes are reconciled), [CAP theorem](0107-cap-theorem.md) (the formal framing of this trade-off).
