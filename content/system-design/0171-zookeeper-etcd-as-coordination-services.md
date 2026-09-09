---
card: system-design
gi: 171
slug: zookeeper-etcd-as-coordination-services
title: ZooKeeper / etcd as coordination services
---

## 1. What it is

**ZooKeeper** and **etcd** are purpose-built services that give distributed applications a small, strongly-consistent, highly-available store for coordination data — configuration values, [distributed locks](0167-distributed-locks-redis-redlock-zookeeper.md), [leader election](0169-leader-election.md), and service discovery — all backed internally by a [consensus protocol](0170-consensus-paxos-raft-overview.md) (ZooKeeper uses its own ZAB protocol; etcd uses Raft). Rather than every application team implementing its own consensus logic, these services provide it as a ready-made, reusable building block.

## 2. Why & when

Correctly implementing consensus, leader election, and distributed locking from scratch is genuinely hard to get right — subtle timing bugs can silently break the very guarantees these mechanisms exist to provide. ZooKeeper and etcd exist so that application teams can build coordination features (a leader-only scheduled job, a shared lock, dynamic configuration all instances must agree on) on top of a battle-tested, already-correct implementation, instead of building their own. Use one of these whenever your system needs multiple instances to agree on shared state or elect a leader, and you would rather depend on a well-tested coordination service than reimplement that logic yourself.

## 3. Core concept

- **A small, hierarchical key-value store:** ZooKeeper organizes data as a tree of "znodes" (like a mini file system); etcd is a flatter key-value store — both are meant for small amounts of coordination data, not general application data storage.
- **Ephemeral nodes / leases:** ZooKeeper's ephemeral znodes (and etcd's leases) are automatically deleted when the client's session ends (e.g. the client crashes or its connection drops) — this is what makes locks and leader-election markers self-cleaning, without relying on a fixed TTL guess.
- **Watches:** clients can register a watch on a key or znode and be notified immediately when it changes — this is how followers detect a leader disappearing, or how a service discovers a configuration change, without polling.
- **Sequential znodes / leader election recipes:** ZooKeeper's sequential znodes (each new node gets an auto-incrementing suffix) provide a simple, race-free way to implement leader election: whichever client created the znode with the lowest sequence number is the leader.
- **Strong consistency backed by consensus:** because both services use a real consensus protocol internally, reads and writes across the cluster are strongly consistent — this is precisely why they are trusted for coordination, where an inconsistent view could cause two nodes to both think they are the leader.

## 4. Diagram

```
   3 application instances, all trying to become leader via etcd/ZooKeeper

   instance-A ---- create ephemeral lock node "/leader" ----> etcd/ZooKeeper
   instance-B ---- create ephemeral lock node "/leader" ----> (already exists - FAILS)
   instance-C ---- create ephemeral lock node "/leader" ----> (already exists - FAILS)

   instance-A is now leader; instance-B and instance-C register a WATCH on "/leader"

   instance-A CRASHES -> its session ends -> "/leader" ephemeral node is AUTOMATICALLY deleted
                                    |
                     watch fires on instance-B and instance-C
                                    |
                     both race to create "/leader" again -> instance-B wins this time
```
*Caption: the ephemeral node ties the lock directly to the holder's session, so a crash cleans it up automatically, and watches let the other instances react immediately.*

## 5. Runnable example

This models the ZooKeeper/etcd ephemeral-node + watch mechanism in-process; the "How to run" note shows the real client API calls.

**Level 1 — Basic.** Create a lock node only if it does not already exist, modeling `create` on a ZooKeeper znode.

**Level 2 — Ephemeral cleanup on session end.** The lock node is automatically removed when its owning client's session ends.

**Level 3 — Watches notify the other clients immediately.** Register a watch that fires as soon as the lock node is deleted, without polling.

```java
// CoordinationServiceDemo.java
import java.util.*;
import java.util.function.*;

public class CoordinationServiceDemo {

    // Models a tiny ZooKeeper/etcd-like coordination store.
    static class CoordinationStore {
        String lockOwnerSessionId = null;
        List<Consumer<String>> watchesOnLockNode = new ArrayList<>(); // Level 3: registered callbacks

        // Level 1: create the ephemeral lock node only if it does not already exist.
        boolean tryCreateLock(String sessionId) {
            if (lockOwnerSessionId != null) return false;
            lockOwnerSessionId = sessionId;
            return true;
        }

        // Level 3: register a watch, fired when the lock node is deleted.
        void watchLockNode(Consumer<String> onDeleted) {
            watchesOnLockNode.add(onDeleted);
        }

        // Level 2: a client session ending automatically deletes its ephemeral node, then fires watches.
        void endSession(String sessionId) {
            if (sessionId.equals(lockOwnerSessionId)) {
                System.out.println("session " + sessionId + " ended - its ephemeral lock node is automatically removed.");
                lockOwnerSessionId = null;
                for (Consumer<String> watch : watchesOnLockNode) {
                    watch.accept(sessionId); // notify every watcher immediately, no polling needed
                }
                watchesOnLockNode.clear();
            }
        }
    }

    public static void main(String[] args) {
        CoordinationStore store = new CoordinationStore();

        // Level 1: instance-A wins the race to create the lock node - becomes leader.
        boolean aWon = store.tryCreateLock("session-A");
        boolean bWon = store.tryCreateLock("session-B");
        boolean cWon = store.tryCreateLock("session-C");
        System.out.println("instance-A became leader: " + aWon);
        System.out.println("instance-B became leader: " + bWon + " (lock already held)");
        System.out.println("instance-C became leader: " + cWon + " (lock already held)");

        // Level 3: instance-B and instance-C register watches instead of polling.
        store.watchLockNode(deadSessionId -> System.out.println("  instance-B's watch fired: session " + deadSessionId + " is gone, attempting to become leader..."));
        store.watchLockNode(deadSessionId -> System.out.println("  instance-C's watch fired: session " + deadSessionId + " is gone, attempting to become leader..."));

        // Level 2: instance-A crashes - its session ends.
        System.out.println("instance-A crashes (session-A ends)...");
        store.endSession("session-A");

        // Now instance-B and instance-C race again for the freed lock.
        boolean bWonNow = store.tryCreateLock("session-B");
        System.out.println("instance-B becomes leader now: " + bWonNow);
    }
}
```

**How to run:** save as `CoordinationServiceDemo.java`, then run `java CoordinationServiceDemo.java`. (Real etcd: acquire a lease with `client.lease().grant(ttl)`, then `client.getKVClient().put(key, value, PutOption.newBuilder().withLeaseId(leaseId).build())`; the key is automatically removed when the lease expires or its holder's connection drops, and `client.getWatchClient().watch(key, ...)` delivers change notifications.)

## 6. Walkthrough

1. `store.tryCreateLock("session-A")` finds `lockOwnerSessionId == null`, so it sets it to `"session-A"` and returns `true` — instance-A becomes leader; the subsequent calls for `"session-B"` and `"session-C"` both find `lockOwnerSessionId` already set and return `false`.
2. Both instance-B and instance-C register watch callbacks via `watchLockNode`, storing their `Consumer<String>` lambdas in `watchesOnLockNode` — this models registering an interest in changes to the lock node, instead of repeatedly polling to check if it still exists.
3. `store.endSession("session-A")` checks whether `"session-A"` matches `lockOwnerSessionId`, which it does; this models instance-A's connection or process ending, so its ephemeral lock node is automatically removed by setting `lockOwnerSessionId = null`.
4. Immediately after removing the lock, the method iterates every registered watch and calls it with the dead session's ID — both instance-B's and instance-C's watch callbacks fire right away, printing their "attempting to become leader" messages, with no polling delay at all.
5. `store.tryCreateLock("session-B")` is then called (modeling instance-B's watch callback reacting by immediately trying to become the new leader); since `lockOwnerSessionId` was just cleared, this call succeeds, and instance-B becomes the new leader — completing an automatic, crash-triggered leadership handoff.

## 7. Gotchas & takeaways

> Gotcha: a watch typically fires only once per registration in real ZooKeeper (you must re-register it after it fires to keep watching); forgetting to re-register after handling a watch event means you silently stop receiving future notifications on that node, which can look like the coordination service "stopped working" when really your own client just stopped listening.

- ZooKeeper and etcd give applications ready-made, battle-tested primitives (locks, leader election, watches) built on a real consensus protocol underneath.
- Ephemeral nodes/leases tie coordination state directly to a client's live session, so a crash cleans up automatically — no fixed TTL has to be guessed.
- Watches let other clients react to a change immediately, without the delay and overhead of polling.
- Related concepts: [Distributed locks (Redis Redlock / ZooKeeper)](0167-distributed-locks-redis-redlock-zookeeper.md) (the specific pattern this session-based approach improves on), [Leader election](0169-leader-election.md) (the classic use case these services provide a recipe for), [Consensus (Paxos / Raft) overview](0170-consensus-paxos-raft-overview.md) (the underlying protocol making these services strongly consistent).
