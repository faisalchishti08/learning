---
card: system-design
gi: 99
slug: multi-leader-replication
title: Multi-leader replication
---

## 1. What it is

**Multi-leader replication** allows more than one node to accept writes at the same time, with each leader replicating its changes to every other leader. This differs from [leader-follower replication](0098-leader-follower-primary-replica-replication.md), where only one node can accept writes. Each leader is like a co-editor of the same shared document, who can type changes locally and then sends those changes to every other co-editor.

## 2. Why & when

A single leader forces every write, from anywhere in the world, to travel to one node — slow for users far from it, and a single point of failure for all writes. Multi-leader replication lets each region (or each data center) have its own local leader, so users write to a nearby node with low latency, and each leader propagates its writes to the others in the background. Use it for multi-datacenter deployments where write latency matters, or for offline-capable applications (like a calendar app that syncs after reconnecting) where each device is effectively its own leader while offline.

## 3. Core concept

- **Multiple write-accepting nodes:** each leader accepts writes independently, without asking any other leader first.
- **Asynchronous cross-leader replication:** each leader sends its writes to the other leaders, usually asynchronously, since waiting for every other leader on every write would defeat the low-latency purpose of having multiple leaders.
- **The conflict problem:** since two leaders can accept a write to the *same* key at nearly the same time, without coordinating, their values can conflict once replicated to each other. This did not exist with a single leader, where all writes to a key are naturally ordered.
- **Conflict detection:** each leader must recognize when an incoming replicated write conflicts with a local write to the same key.
- **Conflict resolution:** a strategy decides the outcome — last-write-wins (pick the write with the later timestamp), a custom merge function, or deferring to the application to resolve it. See [conflict resolution](0109-conflict-resolution-last-write-wins-vector-clocks-crdts.md) for the details.

## 4. Diagram

```
   Leader A (Region: US)              Leader B (Region: EU)
   local write: set("cart.item", "book")   local write: set("cart.item", "pen")
   at time T=100                            at time T=101 (slightly later)
          |                                          |
          +------- both replicate to each other -----+
          |                                          |
          v                                          v
   Leader A receives B's write             Leader B receives A's write
   "book" (T=100) vs "pen" (T=101)         "book" (T=100) vs "pen" (T=101)
   CONFLICT -> resolve (e.g. last-write-wins: T=101 "pen" wins on both)
```
*Caption: two leaders can accept conflicting writes to the same key at nearly the same time; both must resolve to the same final answer.*

## 5. Runnable example

**Level 1 — Basic.** Two leaders each accept a local write, then replicate it to the other.

**Level 2 — Conflict detection.** Both leaders write the same key at nearly the same time, creating a conflict once replicated.

**Level 3 — Last-write-wins resolution.** Resolve the conflict using timestamps, and confirm both leaders converge to the same value.

```java
// MultiLeaderReplication.java
import java.util.*;

public class MultiLeaderReplication {

    record Write(String key, String value, long timestamp) {}

    static class Leader {
        String name;
        Map<String, Write> data = new HashMap<>();
        Leader(String name) { this.name = name; }

        void localWrite(String key, String value, long ts) {
            data.put(key, new Write(key, value, ts));
        }

        // apply an incoming replicated write, resolving any conflict by last-write-wins.
        void receiveReplicated(Write incoming) {
            Write existing = data.get(incoming.key());
            if (existing == null || incoming.timestamp() > existing.timestamp()) {
                data.put(incoming.key(), incoming); // incoming write is newer, or there was nothing local
            } // else: local write is newer, keep it, discard the incoming one
        }
    }

    public static void main(String[] args) {
        Leader leaderA = new Leader("A (US)");
        Leader leaderB = new Leader("B (EU)");

        // Level 1: each leader accepts an independent local write for a DIFFERENT key.
        leaderA.localWrite("cart.shipping", "express", 100);
        leaderB.localWrite("cart.giftwrap", "yes", 101);
        leaderA.receiveReplicated(leaderB.data.get("cart.giftwrap"));
        leaderB.receiveReplicated(leaderA.data.get("cart.shipping"));
        System.out.println("leaderA now has: " + leaderA.data.keySet());
        System.out.println("leaderB now has: " + leaderB.data.keySet());

        // Level 2: both leaders write the SAME key at nearly the same time - a conflict.
        leaderA.localWrite("cart.item", "book", 200);
        leaderB.localWrite("cart.item", "pen", 201); // slightly later timestamp

        System.out.println("before replication -> leaderA cart.item: " + leaderA.data.get("cart.item").value());
        System.out.println("before replication -> leaderB cart.item: " + leaderB.data.get("cart.item").value());

        // Level 3: replicate each write to the other leader; last-write-wins resolves the conflict.
        Write aWrite = leaderA.data.get("cart.item");
        Write bWrite = leaderB.data.get("cart.item");
        leaderA.receiveReplicated(bWrite);
        leaderB.receiveReplicated(aWrite);

        System.out.println("after replication -> leaderA cart.item: " + leaderA.data.get("cart.item").value());
        System.out.println("after replication -> leaderB cart.item: " + leaderB.data.get("cart.item").value());
        System.out.println("-> both leaders converged on \"pen\" (timestamp 201 was later)");
    }
}
```

**How to run:** save as `MultiLeaderReplication.java`, then run `java MultiLeaderReplication.java`.

## 6. Walkthrough

1. Level 1 has each leader write a different key locally, then replicate it to the other; since the keys differ, `receiveReplicated` finds no existing entry and simply adds the new one — no conflict.
2. Level 2 has both leaders write the *same* key, `cart.item`, at nearly the same time but with different values (`"book"` at timestamp 200, `"pen"` at 201). Before replication, each leader only knows its own local value.
3. Level 3 replicates each leader's write to the other. `leaderA.receiveReplicated(bWrite)` compares `bWrite`'s timestamp (201) to the existing local write's timestamp (200); since 201 is greater, it overwrites with `"pen"`.
4. `leaderB.receiveReplicated(aWrite)` compares `aWrite`'s timestamp (200) to its own existing local write (201); since 200 is not greater, it keeps `"pen"` and discards the incoming `"book"`.
5. Both leaders end up holding `"pen"` — proof that last-write-wins conflict resolution makes independent leaders converge to the same final value, even though they accepted different writes to the same key initially.

## 7. Gotchas & takeaways

> Gotcha: last-write-wins silently discards one of the two conflicting writes — in this example, the customer's original "book" selection is simply gone, with no record that it ever conflicted. For data where silently losing a write is unacceptable, use a smarter [conflict resolution](0109-conflict-resolution-last-write-wins-vector-clocks-crdts.md) strategy, such as a merge function or surfacing the conflict to the user.

- Multi-leader replication lets several nodes accept writes independently, cutting write latency for geographically distributed users.
- The cost is write conflicts: two leaders can accept different writes to the same key before either knows about the other's write.
- A resolution strategy (like last-write-wins) is required so all leaders eventually converge to the same value for every key.
- Related concepts: [Leader-follower replication](0098-leader-follower-primary-replica-replication.md) (the single-writer alternative that avoids this conflict problem), [Conflict resolution](0109-conflict-resolution-last-write-wins-vector-clocks-crdts.md) (deeper strategies beyond last-write-wins).
