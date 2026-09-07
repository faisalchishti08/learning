---
card: system-design
gi: 100
slug: leaderless-replication-dynamo-style
title: Leaderless replication (Dynamo-style)
---

## 1. What it is

**Leaderless replication** has no designated leader at all — any node can accept a read or a write for any key. The client (or a coordinator on its behalf) sends the write to several nodes directly, and sends reads to several nodes too, comparing their answers to figure out the current value. This style is named after Amazon's Dynamo paper and is used by databases like Cassandra and Riak. It is like asking three different friends for an address instead of relying on one designated record-keeper — if most of them agree, you trust the answer.

## 2. Why & when

Leader-based systems ([leader-follower](0098-leader-follower-primary-replica-replication.md) or [multi-leader](0099-multi-leader-replication.md)) have leaders as availability-critical nodes: if a leader is unreachable, writes for its shard stop until failover completes. Leaderless replication avoids this single point of write failure entirely, since a client can write to whichever nodes are currently reachable, and the write still succeeds as long as enough of them respond. Use it for workloads that must accept writes even during partial node or network failures, at the cost of needing an explicit strategy to keep replicas consistent, since there is no leader whose log defines the "correct" order of writes.

## 3. Core concept

- **N, W, R:** the key parameters. `N` = number of nodes that store a replica of the data. `W` = number of nodes that must acknowledge a write before it is considered successful. `R` = number of nodes a read must contact before returning an answer.
- **Write path:** the client sends the write to all `N` replica nodes, but only waits for `W` of them to acknowledge before declaring success — the rest apply the write when they can.
- **Read path:** the client reads from `R` replica nodes and compares their values, since some may not have the latest write yet.
- **Read repair:** if a read finds that some of the `R` nodes returned a stale value, it writes the latest value back to those stale nodes, quietly fixing them.
- **Quorums:** choosing `W` and `R` so that `W + R > N` guarantees every read overlaps with at least one node that has the latest write — see [Quorum reads/writes](0106-quorum-reads-writes-r-w-n.md) for the full reasoning.

## 4. Diagram

```
N = 3 replica nodes for key "item-42": Node1, Node2, Node3

WRITE (W=2): client sends write to all 3, waits for 2 acks.
  Node1: ACK (fast)     Node2: ACK (fast)     Node3: (slow, not yet)
  -> write succeeds once 2 acks arrive, Node3 catches up later.

READ (R=2): client reads from 2 of the 3 nodes.
  Node1: value=v2 (latest)   Node3: value=v1 (stale, hadn't gotten the write yet)
  -> client sees the disagreement, returns the latest (v2), and read-repairs Node3.
```
*Caption: writes and reads each only need to reach a subset of nodes; reads reconcile any disagreement and repair stale replicas.*

## 5. Runnable example

**Level 1 — Basic.** Model N=3 replica nodes; a write only needs W=2 acknowledgments to succeed.

**Level 2 — Read from R nodes and detect disagreement.** One node is behind; the read compares values from R nodes.

**Level 3 — Read repair.** The read pushes the latest value to the stale node it found.

```java
// LeaderlessReplication.java
import java.util.*;

public class LeaderlessReplication {

    record Versioned(String value, long version) {}

    static Map<String, Versioned> node1 = new HashMap<>();
    static Map<String, Versioned> node2 = new HashMap<>();
    static Map<String, Versioned> node3 = new HashMap<>();
    static List<Map<String, Versioned>> allNodes = List.of(node1, node2, node3);

    static void write(String key, String value, long version, int w) {
        int acks = 0;
        for (Map<String, Versioned> node : allNodes) {
            if (acks < w) { node.put(key, new Versioned(value, version)); acks++; } // only first W nodes ack "in time"
        }
        System.out.println("write '" + value + "' (v" + version + ") acknowledged by " + acks + " of " + allNodes.size() + " nodes (W=" + w + ")");
    }

    static String readWithRepair(String key, int r) {
        List<Map<String, Versioned>> contacted = allNodes.subList(0, r); // read from R nodes
        Versioned latest = null;
        for (var node : contacted) {
            Versioned v = node.get(key);
            if (v != null && (latest == null || v.version() > latest.version())) latest = v;
        }
        for (var node : contacted) { // read repair: push the latest value to any stale node among those contacted
            Versioned v = node.get(key);
            if (v == null || v.version() < latest.version()) node.put(key, latest);
        }
        return latest.value();
    }

    public static void main(String[] args) {
        // Level 1: N=3, W=2 - write succeeds once 2 of 3 nodes ack; node3 is left behind.
        int acksNeeded = 2;
        node1.put("item-42", new Versioned("old-price", 1));
        node2.put("item-42", new Versioned("old-price", 1));
        node3.put("item-42", new Versioned("old-price", 1));
        write("item-42", "new-price", 2, acksNeeded); // only node1, node2 get the new write "in time"

        System.out.println("node1: " + node1.get("item-42"));
        System.out.println("node2: " + node2.get("item-42"));
        System.out.println("node3 (behind): " + node3.get("item-42"));

        // Level 2 & 3: read with R=2, from node1 and node2 - both agree, no repair needed here.
        System.out.println("read (R=2, from node1/node2): " + readWithRepair("item-42", 2));

        // Now read across all 3 nodes (R=3) - node3 is stale, gets detected and repaired.
        String result = readWithRepair("item-42", 3);
        System.out.println("read (R=3, includes stale node3): " + result);
        System.out.println("node3 after read repair: " + node3.get("item-42") + " (now caught up)");
    }
}
```

**How to run:** save as `LeaderlessReplication.java`, then run `java LeaderlessReplication.java`.

## 6. Walkthrough

1. `write` sends the new value to every node in `allNodes`, but only counts an "ack" for the first `w` of them — modeling `node3` being slow or unreachable and not getting the write in time, while the write still succeeds because `W=2` nodes acknowledged.
2. Printing each node's stored value shows `node1` and `node2` at version 2 (`"new-price"`), while `node3` is stuck at version 1 (`"old-price"`) — exactly the divergence leaderless replication must tolerate.
3. `readWithRepair("item-42", 2)` reads only `node1` and `node2`; both agree on version 2, so the read returns `"new-price"` with nothing to repair.
4. `readWithRepair("item-42", 3)` reads all three nodes, including the stale `node3`. It finds `node3`'s version (1) is lower than the latest seen (version 2), so it identifies the disagreement and returns the correct, latest value.
5. The read-repair loop then writes the latest `Versioned` value directly into `node3`, so the final printed line shows `node3` now holding version 2 — the stale replica has quietly caught up as a side effect of being read.

## 7. Gotchas & takeaways

> Gotcha: read repair only fixes a stale replica when it happens to be one of the `R` nodes contacted by a read. A stale replica that is never read (because it wasn't randomly chosen, or because W was low) can drift indefinitely; production systems run a background "anti-entropy" process to compare and repair all replicas periodically, not just the ones a live read happens to touch.

- Leaderless replication removes the single-leader dependency, letting writes and reads succeed against any subset of nodes.
- Choosing `W` and `R` controls the durability-versus-latency and consistency-versus-latency trade-offs; `W + R > N` guarantees a read always sees the latest acknowledged write.
- Read repair opportunistically fixes stale replicas encountered during a read; background anti-entropy fixes the ones that aren't.
- Related concepts: [Quorum reads/writes (R + W > N)](0106-quorum-reads-writes-r-w-n.md) (the formal guarantee behind this scheme), [Eventual consistency](0104-eventual-consistency.md) (the consistency model leaderless systems typically provide).
