---
card: system-design
gi: 170
slug: consensus-paxos-raft-overview
title: Consensus (Paxos / Raft) overview
---

## 1. What it is

**Consensus** algorithms let a group of nodes agree on a single value (or a single, ordered sequence of values) even when some nodes fail or messages are delayed, and even when nodes disagree about who the current leader is for a while. **Paxos** is the foundational, famously hard-to-understand algorithm proving this is possible; **Raft** is a later algorithm designed explicitly to be easier to understand and implement while providing the same guarantee, and is what most modern systems (etcd, many replicated databases) actually use.

## 2. Why & when

A system with multiple copies of the same data (for durability) needs every copy to agree on the exact same sequence of changes, in the exact same order, even if some copies are temporarily unreachable or a leader crashes mid-decision. Without a rigorous consensus protocol, ad-hoc coordination easily produces two nodes disagreeing about what happened, or a "split brain" where two nodes both believe they are in charge. Consensus algorithms formally guarantee this cannot happen, at the cost of requiring a majority of nodes to agree before any decision is considered final. Use (or rely on a library implementing) consensus whenever building a system that must keep multiple nodes' state provably consistent despite failures — most people use it indirectly, via etcd, ZooKeeper, or a replicated database's internals, rather than implementing Paxos or Raft from scratch.

## 3. Core concept

- **A single elected leader per term:** Raft simplifies coordination by having one leader per term responsible for proposing the order of all changes; only the leader accepts new writes, and it replicates them to followers.
- **Majority (quorum) commit:** a change is only considered permanently committed once a majority of nodes have durably stored it — this is what lets the system survive a minority of nodes failing without losing any committed data.
- **Log replication:** the leader appends every change to its own log and sends it to followers, who append it to their own logs in the same order; once a majority have acknowledged, the leader tells everyone the entry is committed.
- **Handling leader failure:** if the leader disappears, a new [leader election](0169-leader-election.md) happens, and a critical safety rule ensures the new leader has every entry the previous leader had already committed — it cannot "lose" committed data even across a leadership change.
- **Split-brain prevention:** because both leader election and commits require an actual majority, at most one leader can ever get a majority to agree with it at the same time — this is the core safety property consensus provides.

## 4. Diagram

```
   leader (term 5)
        |
        |-- AppendEntry("x=1") -->  follower-B
        |-- AppendEntry("x=1") -->  follower-C
        |
        |<---------- ACK -----------follower-B
        |<---------- ACK -----------follower-C
        |
   2 of 3 nodes (a majority) acknowledged -> "x=1" is now COMMITTED
        |
        |-- commit notification --> follower-B, follower-C

   if leader crashes AFTER commit: new leader (elected from a majority) still has "x=1" in its log
                                     -> no committed data is lost
```
*Caption: an entry is only committed once a majority of nodes have it in their log, which is exactly what guarantees it survives any future leader change.*

## 5. Runnable example

**Level 1 — Basic.** A leader appends an entry to its own log and replicates it to followers.

**Level 2 — Majority-based commit.** An entry is only marked committed once a majority of nodes have acknowledged it.

**Level 3 — Leader failure and safe re-election.** A new leader is elected from the nodes that already have the committed entry, so nothing committed is ever lost.

```java
// ConsensusDemo.java
import java.util.*;

public class ConsensusDemo {

    static class Node {
        final String id;
        List<String> log = new ArrayList<>();
        boolean alive = true;
        Node(String id) { this.id = id; }
    }

    static int totalNodes;

    // Level 1 & 2: leader appends to its own log, replicates to followers, and commits on majority ack.
    static boolean appendAndCommit(Node leader, List<Node> followers, String entry) {
        leader.log.add(entry); // leader appends to its own log first
        int acks = 1; // leader counts as having it
        for (Node follower : followers) {
            if (follower.alive) {
                follower.log.add(entry); // replicate to this follower
                acks++;
            }
        }
        int majorityNeeded = totalNodes / 2 + 1;
        boolean committed = acks >= majorityNeeded;
        System.out.println("appending \"" + entry + "\": " + acks + "/" + totalNodes + " acks, majority needed=" + majorityNeeded + " -> " + (committed ? "COMMITTED" : "NOT committed"));
        return committed;
    }

    // Level 3: elect a new leader ONLY from nodes that already have every committed entry - safety guarantee.
    static Node electNewLeader(List<Node> nodes, List<String> committedLog) {
        for (Node n : nodes) {
            if (n.alive && n.log.size() >= committedLog.size() && n.log.subList(0, committedLog.size()).equals(committedLog)) {
                return n;
            }
        }
        throw new IllegalStateException("no alive node has the full committed log - should never happen with a correct majority commit");
    }

    public static void main(String[] args) {
        Node leader = new Node("node-A");
        Node followerB = new Node("node-B");
        Node followerC = new Node("node-C");
        List<Node> allNodes = List.of(leader, followerB, followerC);
        totalNodes = allNodes.size();
        List<Node> followers = List.of(followerB, followerC);

        List<String> committedEntries = new ArrayList<>();
        if (appendAndCommit(leader, followers, "x=1")) committedEntries.add("x=1");
        if (appendAndCommit(leader, followers, "y=2")) committedEntries.add("y=2");

        System.out.println("committed log so far: " + committedEntries);

        // Level 3: the leader crashes right after "y=2" was committed.
        leader.alive = false;
        System.out.println("leader (node-A) crashed. electing a new leader...");
        Node newLeader = electNewLeader(allNodes, committedEntries);
        System.out.println("new leader elected: " + newLeader.id + ", with log: " + newLeader.log + " (has every committed entry - none lost)");
    }
}
```

**How to run:** save as `ConsensusDemo.java`, then run `java ConsensusDemo.java`.

## 6. Walkthrough

1. `appendAndCommit(leader, followers, "x=1")` first appends `"x=1"` to `leader.log`, then loops through `followers`, appending it to each alive follower's log and counting acknowledgments — with both `followerB` and `followerC` alive, `acks` reaches 3 (leader plus both followers).
2. `majorityNeeded = totalNodes / 2 + 1 = 3 / 2 + 1 = 2`; since `acks (3) >= majorityNeeded (2)`, the method prints "COMMITTED" and returns `true`, so `"x=1"` is added to `committedEntries`.
3. The same happens for `"y=2"`, so `committedEntries` becomes `["x=1", "y=2"]`, and at this point every one of the three nodes' logs contains both entries, in the same order.
4. `leader.alive = false` simulates the leader crashing right after committing `"y=2"`; `electNewLeader` then scans `allNodes` for one that is alive and whose log's first `committedLog.size()` entries exactly match `committedEntries` — both `followerB` and `followerC` qualify, since they each replicated both entries before the crash.
5. The method returns the first qualifying node, `followerB`, as the new leader; its printed log shows `["x=1", "y=2"]` still fully intact — demonstrating the core safety guarantee: because the earlier commits required a majority (which necessarily includes at least one surviving node after a single-node failure), no committed data was lost when the original leader disappeared.

## 7. Gotchas & takeaways

> Gotcha: this simplified demo elects a new leader from *any* node holding the full committed log, but real Raft's election rule is more precise — it also compares log term numbers and lengths to ensure the new leader has the most up-to-date log among the *voting majority*, not just any node that happens to be alive; a naive "any node with the committed prefix" rule can go wrong once uncommitted, divergent entries are involved, which real Raft's full election and log-matching rules are specifically designed to resolve correctly.

- Consensus guarantees that a majority of nodes agree on both the current leader and the exact, ordered sequence of committed changes, even across failures.
- An entry is only safely committed once a majority of nodes have durably stored it — this majority requirement is the entire basis of the safety guarantee.
- Raft is designed to be more understandable and implementable than Paxos, while providing the same fundamental guarantees, which is why most modern systems build on Raft (or a Raft-like protocol) rather than classic Paxos.
- Related concepts: [Leader election](0169-leader-election.md) (a component consensus protocols formalize and make safe), [ZooKeeper / etcd as coordination services](0171-zookeeper-etcd-as-coordination-services.md) (production systems built on top of a consensus protocol like this), [Distributed transactions (2PC / 3PC) & their cost](0172-distributed-transactions-2pc-3pc-their-cost.md) (a related but distinct coordination problem: atomic multi-node commits, not agreeing on one ordered log).
