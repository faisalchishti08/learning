---
card: system-design
gi: 169
slug: leader-election
title: Leader election
---

## 1. What it is

**Leader election** is the process by which a group of independent nodes agrees on exactly one of them to act as the "leader," responsible for some task that should only be done by one node at a time — such as coordinating writes, running a scheduled job, or making authoritative decisions. All other nodes act as followers, ready to elect a new leader if the current one fails.

## 2. Why & when

Many distributed systems need a single point of coordination for correctness or simplicity — a replicated database needs one primary to accept writes and propagate them to replicas; a cluster of scheduler instances needs exactly one instance to actually trigger a scheduled job, not all of them simultaneously. Running that role on a fixed, manually-configured node is fragile: if that specific node fails, the role disappears with it. Leader election automates both the initial choice and the recovery: if the current leader fails, the remaining nodes detect this and elect a new one, restoring the role without human intervention. Use it whenever exactly-one-node-does-this coordination is required and the system must survive that node failing.

## 3. Core concept

- **A term or epoch number:** each election produces a new term number, strictly increasing, so nodes can tell an old leader's stale messages apart from the current leader's messages.
- **Heartbeats / liveness detection:** followers expect regular signals (heartbeats) from the leader; the absence of heartbeats for some timeout period is what triggers a new election.
- **Majority (quorum) agreement:** most leader election algorithms (built on [consensus](0170-consensus-paxos-raft-overview.md)) require a majority of nodes to agree on the new leader, preventing two nodes from both believing they are the leader at once (a "split brain").
- **A lease or session-based lock underneath:** practically, leader election is often implemented as every candidate racing to acquire a [distributed lock](0167-distributed-locks-redis-redlock-zookeeper.md) or ephemeral session-tied node (as in ZooKeeper/etcd); whichever candidate acquires it becomes leader until the lock/session expires or is released.
- **Graceful handoff vs. crash-triggered election:** a leader can voluntarily step down (e.g. during a planned restart) and trigger an election immediately, or a crash can be detected only after a heartbeat timeout — the latter is slower but handles the unplanned case.

## 4. Diagram

```
   node-A (leader, term 3)   node-B (follower)   node-C (follower)
        |  heartbeat -------------> |                    |
        |  heartbeat ------------------------------------->|
        |
        X  node-A CRASHES (no more heartbeats)
                                     |                    |
                     (heartbeat timeout elapses)          |
                                     |-- request votes -->|
                                     |<----- vote granted-|
                                     |
                           node-B wins majority -> becomes leader, term 4
                                     |
                                     |-- heartbeat (term 4) ------------->|
```
*Caption: the absence of heartbeats past a timeout triggers an election; the winner starts a new term and begins sending its own heartbeats.*

## 5. Runnable example

**Level 1 — Basic.** A fixed set of nodes, one marked leader, sending heartbeats.

**Level 2 — Heartbeat-timeout-triggered election.** Followers detect a missing leader and hold a vote.

**Level 3 — Majority requirement and a new term number.** The election only succeeds with a majority, and the winner's term strictly increases.

```java
// LeaderElectionDemo.java
import java.util.*;

public class LeaderElectionDemo {

    static class Node {
        final String id;
        boolean isLeader = false;
        boolean alive = true;
        Node(String id) { this.id = id; }
    }

    static int currentTerm = 3;
    static String currentLeaderId = "node-A";

    // Level 2: detect a missing leader (simulated as "not alive" rather than a real timeout).
    static boolean leaderIsMissing(List<Node> nodes) {
        Node leader = nodes.stream().filter(n -> n.id.equals(currentLeaderId)).findFirst().orElse(null);
        return leader == null || !leader.alive;
    }

    // Level 3: hold an election - candidates request votes; the winner needs a MAJORITY of all nodes.
    static void holdElection(List<Node> nodes) {
        List<Node> aliveNodes = nodes.stream().filter(n -> n.alive).toList();
        int majorityNeeded = nodes.size() / 2 + 1;
        System.out.println("election triggered: " + aliveNodes.size() + " alive nodes, need " + majorityNeeded + " votes to win.");

        if (aliveNodes.isEmpty()) {
            System.out.println("no alive nodes - election fails.");
            return;
        }

        // Simplified: the first alive node becomes the candidate; every alive node votes for it.
        Node candidate = aliveNodes.get(0);
        int votes = aliveNodes.size(); // in this simple model, every alive node votes for the one candidate

        if (votes >= majorityNeeded) {
            currentTerm++; // Level 3: term strictly increases with every successful election
            currentLeaderId = candidate.id;
            for (Node n : nodes) n.isLeader = n.id.equals(candidate.id);
            System.out.println("election succeeded: " + candidate.id + " is now leader, term " + currentTerm + " (" + votes + "/" + nodes.size() + " votes)");
        } else {
            System.out.println("election failed: only " + votes + "/" + nodes.size() + " votes, no majority.");
        }
    }

    public static void main(String[] args) {
        Node a = new Node("node-A"); a.isLeader = true;
        Node b = new Node("node-B");
        Node c = new Node("node-C");
        List<Node> nodes = List.of(a, b, c);

        System.out.println("initial state: leader=" + currentLeaderId + ", term=" + currentTerm);

        // Level 2: node-A crashes.
        a.alive = false;
        System.out.println("node-A crashed. checking for a missing leader...");
        if (leaderIsMissing(nodes)) {
            System.out.println("leader is missing (no heartbeats) - holding a new election.");
            holdElection(nodes);
        }

        System.out.println("final state: leader=" + currentLeaderId + ", term=" + currentTerm);
    }
}
```

**How to run:** save as `LeaderElectionDemo.java`, then run `java LeaderElectionDemo.java`.

## 6. Walkthrough

1. The demo starts with `node-A` marked as leader and `currentTerm = 3`; `leaderIsMissing` is not yet called, so nothing has happened.
2. Setting `a.alive = false` models `node-A` crashing; `leaderIsMissing(nodes)` looks up the node matching `currentLeaderId` ("node-A"), finds it, and checks `!leader.alive`, which is now `true` — so the method returns `true`, correctly detecting the missing leader.
3. `holdElection(nodes)` filters to `aliveNodes`, which now contains only `node-B` and `node-C` (2 nodes), and computes `majorityNeeded = 3 / 2 + 1 = 2` — a majority of the *total* cluster size (3), not just the alive nodes, which matters for correctness (a minority partition should never be able to elect a leader on its own).
4. `candidate` is set to the first alive node, `node-B`, and `votes` is set to `aliveNodes.size() = 2`, modeling every alive node voting for the one candidate in this simplified example.
5. Since `votes (2) >= majorityNeeded (2)`, the election succeeds: `currentTerm` increments from 3 to 4, `currentLeaderId` becomes `"node-B"`, and the `isLeader` flag is updated across all nodes — the final printed state confirms `node-B` is the new leader at term 4, having replaced the crashed `node-A` without any manual intervention.

## 7. Gotchas & takeaways

> Gotcha: requiring a majority of the *alive* nodes (rather than the *total* cluster size) instead would let a minority of nodes, cut off from the rest by a network partition, still believe they have "majority" among themselves and elect their own leader — creating two leaders at once (a split brain) while the partition lasts. Always compute the majority threshold against the total configured cluster size, exactly as `nodes.size() / 2 + 1` does here.

- Leader election automates both choosing an initial leader and recovering when it fails, without manual intervention.
- A majority (quorum) requirement, computed against the total cluster size, is what prevents two leaders from existing at once during a network partition.
- A strictly increasing term number lets every node distinguish a current leader's messages from a stale, older leader's messages.
- Related concepts: [Distributed locks (Redis Redlock / ZooKeeper)](0167-distributed-locks-redis-redlock-zookeeper.md) (a common building block leader election is implemented on top of), [Consensus (Paxos / Raft) overview](0170-consensus-paxos-raft-overview.md) (the formal algorithm family that guarantees correct leader election), [Active-active vs active-passive failover](0131-active-active-vs-active-passive-failover.md) (a related failover pattern this election process often drives).
