---
card: system-design
gi: 98
slug: leader-follower-primary-replica-replication
title: Leader-follower (primary-replica) replication
---

## 1. What it is

**Leader-follower replication** (also called primary-replica replication) keeps copies of the same data on multiple database nodes, but only one node — the **leader** — accepts writes. The leader streams every change to the other nodes — the **followers** — which apply the same changes and can serve reads. It is like a teacher (the leader) dictating notes that several students (the followers) copy down identically.

## 2. Why & when

A single database node can only handle so many reads before it becomes the bottleneck. Leader-follower replication lets you add followers purely to serve more read traffic, without touching how writes work, since all writes still go to one place. It also gives you a standby copy of the data: if the leader fails, a follower can be promoted to take over, improving availability. Use it when your workload is read-heavy and you need to scale reads, or when you need a hot standby for failover, and you can tolerate followers being a small amount of time behind the leader.

## 3. Core concept

- **Single writer:** only the leader accepts write requests (`INSERT`, `UPDATE`, `DELETE`). This avoids the coordination problem of two nodes trying to write the same row differently.
- **Change propagation:** the leader records every write in a log (often called a write-ahead log or binlog) and streams that log to each follower.
- **Followers apply the log in order:** each follower replays the log entries in the same order the leader wrote them, so its data eventually matches the leader's.
- **Reads can go anywhere:** an application can send read queries to the leader or to any follower, spreading read load across all of them.
- **Failover:** if the leader crashes, the system (or an operator) promotes one follower to be the new leader, and the other followers start replicating from it instead.

## 4. Diagram

```
              WRITE "set balance = 90"
                        |
                        v
                  +-----------+
                  |  LEADER   |  (only node that accepts writes)
                  +-----------+
                    |       |
          replication log stream
                    |       |
                    v       v
            +-----------+ +-----------+
            | FOLLOWER 1| | FOLLOWER 2|  (apply the same log, serve reads)
            +-----------+ +-----------+

  READ requests can go to LEADER, FOLLOWER 1, or FOLLOWER 2.
```
*Caption: writes flow one-way from the leader; reads can be served by the leader or any follower.*

## 5. Runnable example

**Level 1 — Basic.** Model a leader and one follower; writes go to the leader, then replicate to the follower.

**Level 2 — Multiple followers, reads spread across them.** Add a second follower and route reads round-robin across all followers.

**Level 3 — Leader failover.** Simulate the leader failing and promoting a follower to take its place.

```java
// LeaderFollowerReplication.java
import java.util.*;

public class LeaderFollowerReplication {

    static class Node {
        String name;
        Map<String, Integer> data = new HashMap<>();
        Node(String name) { this.name = name; }
    }

    static Node leader = new Node("leader");
    static List<Node> followers = new ArrayList<>(List.of(new Node("follower1"), new Node("follower2")));

    static void write(String key, int value) {
        leader.data.put(key, value); // only the leader accepts writes
        for (Node f : followers) f.data.put(key, value); // replication log applied to each follower
    }

    static int readRoundRobin(String key, int requestIndex) {
        Node target = followers.get(requestIndex % followers.size()); // spread reads across followers
        return target.data.get(key);
    }

    public static void main(String[] args) {
        // Level 1: a write on the leader propagates to followers.
        write("balance", 100);
        System.out.println("leader balance: " + leader.data.get("balance"));
        System.out.println("follower1 balance: " + followers.get(0).data.get("balance"));

        // Level 2: reads spread across both followers.
        write("balance", 90);
        for (int i = 0; i < 4; i++) {
            int val = readRoundRobin("balance", i);
            System.out.println("read #" + i + " served by " + followers.get(i % followers.size()).name + " -> balance=" + val);
        }

        // Level 3: leader fails - promote follower1 to be the new leader.
        System.out.println("leader has failed! promoting follower1...");
        Node newLeader = followers.remove(0);
        newLeader.name = "leader (promoted)";
        leader = newLeader;
        write("balance", 80); // new leader now accepts writes
        System.out.println("new leader balance: " + leader.data.get("balance"));
        System.out.println("remaining follower balance: " + followers.get(0).data.get("balance"));
    }
}
```

**How to run:** save as `LeaderFollowerReplication.java`, then run `java LeaderFollowerReplication.java`.

## 6. Walkthrough

1. `write("balance", 100)` updates `leader.data` first, then loops over `followers`, applying the same update to each — modeling the leader streaming its log to every follower.
2. The printed leader and follower values match, confirming the replication succeeded.
3. Level 2 writes `balance = 90`, then issues four reads using `readRoundRobin`, which alternates between `follower1` and `follower2` by index — showing read traffic spread across multiple followers instead of hitting one node.
4. Level 3 simulates a leader crash: `followers.remove(0)` takes `follower1` out of the follower list and reassigns it to the `leader` variable, modeling a promotion.
5. The next `write("balance", 80)` now updates this newly promoted leader and the one remaining follower — confirming the system keeps accepting writes after failover, just through a different node.

## 7. Gotchas & takeaways

> Gotcha: because replication takes some time, a follower can briefly serve stale data right after a write — this is [replication lag](0102-replication-lag-read-your-writes.md). A user who writes their own data and immediately reads it from a lagging follower might not see their own change yet, a common and confusing bug if not designed for explicitly.

- Leader-follower replication uses one leader for all writes and any number of followers for reads, scaling read capacity without complicating writes.
- Followers replay the leader's write log in order, and any follower can be promoted to leader if the original leader fails.
- Reads from followers can be stale by a small amount of time, since replication is not instantaneous.
- Related concepts: [Synchronous vs asynchronous replication](0101-synchronous-vs-asynchronous-replication.md) (how strictly the leader waits for followers), [Replication lag & read-your-writes](0102-replication-lag-read-your-writes.md) (the staleness problem this scheme creates).
