---
card: system-design
gi: 103
slug: strong-consistency
title: Strong consistency
---

## 1. What it is

**Strong consistency** guarantees that every read, from any node, always returns the most recent write — as if there were only one copy of the data, even though it may physically live on several nodes. Once a write is confirmed, no subsequent read can ever return an older value. It is the strictest, simplest-to-reason-about consistency model: there is exactly one true, current answer, and every read gets it.

## 2. Why & when

Strong consistency matters when reading stale or conflicting data would cause a real problem: a bank balance check before approving a withdrawal, an inventory count before confirming the last item is available, or a distributed lock deciding who owns a resource. Use it when correctness depends on every reader agreeing on the current value at all times. The cost is coordination: guaranteeing every node agrees on "the current value" before answering any read requires nodes to talk to each other on the read (or write) path, which adds latency and can reduce availability if some nodes are unreachable.

## 3. Core concept

- **Single source of truth, enforced on every read:** a strongly consistent read cannot be answered by just any node independently; it must confirm (directly or via quorum) that it holds the latest write.
- **How it is achieved:** commonly through a single leader that serves all strongly consistent reads itself (no follower reads), or through a quorum read that contacts enough replicas to guarantee overlap with the latest write (see [quorum reads/writes](0106-quorum-reads-writes-r-w-n.md)).
- **Linearizability:** the formal name for the strongest version of this guarantee — every operation appears to happen instantaneously at some single point in time, and all nodes agree on that order.
- **The CAP trade-off:** strong consistency requires nodes to coordinate, which means during a network partition, a node that cannot confirm it has the latest data must refuse to answer rather than risk returning stale data — trading availability for consistency (see [CAP theorem](0107-cap-theorem.md)).
- **Cost is proportional to coordination:** a strongly consistent read from a distributed system is slower than an eventually consistent one, because it cannot shortcut by reading whichever node is nearest or fastest.

## 4. Diagram

```
STRONG CONSISTENCY (all reads confirm the latest write first):

   Client A writes X=5 -> Leader confirms (X=5 is now "the" value)
   Client B reads X immediately after ->
       read is routed to Leader (or a quorum check happens)
       -> ALWAYS returns X=5, never a stale value

   If the Leader (or enough replicas) is unreachable:
       read REFUSES to answer rather than risk returning stale X.
```
*Caption: a strongly consistent read never returns a stale value — it either gets the true current value or refuses to answer.*

## 5. Runnable example

**Level 1 — Basic.** Model a single-leader system where every read is forced through the leader.

**Level 2 — Quorum-based strong consistency.** Achieve the same guarantee across multiple nodes by requiring read and write quorums to overlap.

**Level 3 — Refusing to answer during a partition.** Show the system rejecting a read rather than risk returning a stale value when it cannot confirm the latest write.

```java
// StrongConsistency.java
import java.util.*;

public class StrongConsistency {

    // Level 1: single-leader strong consistency - every read goes through the leader.
    static Map<String, Integer> leaderStore = new HashMap<>();

    static void write(String key, int value) { leaderStore.put(key, value); }
    static Integer strongRead(String key) { return leaderStore.get(key); } // always the leader, always current

    // Level 2 & 3: quorum-based strong consistency across N=3 nodes.
    record Versioned(int value, long version) {}
    static List<Map<String, Versioned>> nodes = new ArrayList<>(List.of(new HashMap<>(), new HashMap<>(), new HashMap<>()));
    static int N = 3, W = 2, R = 2;

    static void quorumWrite(String key, int value, long version, boolean node3Reachable) {
        nodes.get(0).put(key, new Versioned(value, version));
        nodes.get(1).put(key, new Versioned(value, version));
        if (node3Reachable) nodes.get(2).put(key, new Versioned(value, version));
        System.out.println("quorum write of v" + version + " reached " + (node3Reachable ? 3 : 2) + " nodes (W=" + W + " required, met)");
    }

    static Integer quorumRead(String key, List<Integer> reachableNodeIdxs) {
        if (reachableNodeIdxs.size() < R) {
            System.out.println("cannot reach " + R + " nodes for read quorum -> REFUSING to answer, not risking stale data");
            return null;
        }
        Versioned latest = null;
        for (int idx : reachableNodeIdxs) {
            Versioned v = nodes.get(idx).get(key);
            if (v != null && (latest == null || v.version() > latest.version())) latest = v;
        }
        return latest.value();
    }

    public static void main(String[] args) {
        // Level 1: single leader, always current.
        write("balance", 500);
        System.out.println("strong read after write: " + strongRead("balance"));

        // Level 2: quorum write reaches all 3 nodes; quorum read (R=2, W=2, W+R>N=3) overlaps guaranteed.
        quorumWrite("balance", 700, 1, true);
        Integer result = quorumRead("balance", List.of(0, 2)); // any 2 of 3 nodes
        System.out.println("quorum read result: " + result + " (guaranteed to see the latest write, since W+R > N)");

        // Level 3: a write only reaches 2 of 3 nodes (node index 2 unreachable during the write).
        quorumWrite("balance", 900, 2, false);
        // Now during a read, only node 2 (which missed the write) and no other node are reachable.
        Integer partitionResult = quorumRead("balance", List.of(2)); // only 1 node reachable, below R=2
        System.out.println("partition read result: " + partitionResult + " (refused - could not form a quorum)");
    }
}
```

**How to run:** save as `StrongConsistency.java`, then run `java StrongConsistency.java`.

## 6. Walkthrough

1. Level 1 models the simplest form of strong consistency: `strongRead` always reads `leaderStore` directly, so it is trivially impossible for it to return anything other than the latest write.
2. Level 2 uses quorum parameters `N=3, W=2, R=2`. `quorumWrite` for version 1 reaches all 3 nodes; `quorumRead` then contacts nodes `0` and `2`, finds both hold version 1, and returns it correctly.
3. Because `W + R = 4 > N = 3`, any set of `R` nodes read is mathematically guaranteed to include at least one node that received any given write — this is what makes the quorum read "strongly consistent" without needing every single node.
4. Level 3 simulates a write (`version 2`) that only reaches 2 of 3 nodes because node index `2` was unreachable at write time, then simulates a later read where node `2` is the *only* reachable node.
5. Since only 1 node is reachable and `R=2` is required, `quorumRead` refuses to answer rather than return node `2`'s stale, pre-write value — this refusal is the concrete trade-off strong consistency makes: unavailability instead of a wrong answer.

## 7. Gotchas & takeaways

> Gotcha: "strongly consistent" does not mean "always available" — quite the opposite. The Level 3 refusal is not a bug; it is the entire point. A system that instead let node 2 answer alone would have returned the stale pre-write value, silently breaking the strong-consistency guarantee it promised.

- Strong consistency guarantees every read returns the latest confirmed write, achieved either through a single authoritative node or a quorum that mathematically overlaps every write.
- It requires coordination on the read or write path, which adds latency compared to reading any nearby node blindly.
- Under a network partition, a strongly consistent system must refuse some requests rather than answer with possibly stale data.
- Related concepts: [Quorum reads/writes (R + W > N)](0106-quorum-reads-writes-r-w-n.md) (the mechanism behind quorum-based strong consistency), [CAP theorem](0107-cap-theorem.md) (the formal trade-off strong consistency makes against availability).
