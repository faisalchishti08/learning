---
card: spring-integration
gi: 72
slug: zookeeper-support
title: "Zookeeper support"
---

## 1. What it is

Zookeeper support (`ZookeeperLockRegistry`, `ZookeeperMetadataStore`, and leader-election components built on Curator) integrates a flow with Apache Zookeeper — a coordination service designed for distributed systems that need shared, consistent state: locks, leader election, and small pieces of shared configuration. It plugs into the same abstractions used elsewhere in Spring Integration — the `LockRegistry` interface from distributed locks (card 0048) and the `MetadataStore` interface from the metadata store (card 0046) — backed by Zookeeper instead of a database or Redis.

## 2. Why & when

You reach for Zookeeper support specifically when multiple instances of an application need to coordinate, and Zookeeper is already the coordination service in use:

- **Only one instance among several should perform a task at a time** — leader election via Zookeeper ensures exactly one node in a cluster acts as the active leader for a duty like running a scheduled job, with automatic failover to another node if the leader goes down.
- **Distributed locking across instances is needed and Zookeeper is the established coordination service** — `ZookeeperLockRegistry` provides the same distributed-lock guarantee as the JDBC- or Redis-backed lock registry (card 0048), but built on Zookeeper's stronger consistency guarantees, useful when the deployment already runs Zookeeper for other coordination needs (many Kafka deployments historically included it).
- **A small amount of shared, strongly-consistent configuration needs to be visible to every instance** — `ZookeeperMetadataStore` persists key/value pairs (like the last-processed offset in card 0046) in Zookeeper's tree, visible consistently across every node reading it.

## 3. Core concept

Think of Zookeeper as a tiny, extremely reliable filing cabinet shared by a whole team, with a strict rule: only one person can hold the key to a given drawer at a time, and everyone always sees the same, current contents of every drawer — no stale copies. Leader election works like a numbered ticket system for "who's in charge right now": every instance takes a ticket, and whoever holds the lowest number becomes leader; if that instance disappears, the next-lowest ticket holder is promoted automatically, without anyone needing to notice and intervene manually.

```java
@Bean
public LeaderInitiator leaderInitiator(CuratorFramework client) {
    LeaderInitiator initiator = new LeaderInitiator(client, new DefaultCandidate("node-1", "scheduledJobRole"));
    initiator.setLeaderEventPublisher(new DefaultLeaderEventPublisher());
    return initiator;
}

@EventListener
public void onGranted(OnGrantedEvent event) {
    scheduledJobRunner.start(); // only the elected leader runs this
}
```

Every instance registers a candidate; Zookeeper (through Curator) ensures exactly one is ever the granted leader at a time, and publishes an event locally when leadership is granted or revoked.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple application instances register as leader-election candidates with Zookeeper; exactly one is granted leadership at a time, with automatic failover to the next candidate if the leader disappears" >
  <rect x="20" y="20" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">node-1</text>
  <text x="95" y="58" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">LEADER</text>

  <rect x="190" y="20" width="150" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="265" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">node-2</text>
  <text x="265" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">standby</text>

  <rect x="360" y="20" width="150" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="435" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">node-3</text>
  <text x="435" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">standby</text>

  <rect x="190" y="100" width="150" height="50" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="265" y="122" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Zookeeper</text>
  <text x="265" y="138" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">tracks candidates &amp; grants</text>

  <line x1="95" y1="70" x2="240" y2="100" stroke="#6db33f" stroke-width="1.2"/>
  <line x1="265" y1="70" x2="265" y2="100" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="435" y1="70" x2="290" y2="100" stroke="#8b949e" stroke-width="1.2"/>
</svg>

If `node-1` disappears, Zookeeper promotes the next-lowest candidate automatically — no manual intervention needed.

## 5. Runnable example

The scenario: electing a leader among several instances to run a scheduled job, simulated with a plain in-memory candidate registry standing in for Curator's leader-election recipe (no real Zookeeper ensemble needed to demonstrate the election and failover logic), starting with a basic election, then adding leadership-change event handling, then adding automatic re-election on leader failure.

### Level 1 — Basic

```java
// LeaderElectionDemo.java
import java.util.*;

public class LeaderElectionDemo {
    // Stand-in for Curator's LeaderSelector: candidates registered in join order, lowest index leads.
    static class LeaderRegistry {
        private final List<String> candidates = new ArrayList<>();
        void join(String nodeId) { candidates.add(nodeId); }
        String currentLeader() { return candidates.isEmpty() ? null : candidates.get(0); }
    }

    public static void main(String[] args) {
        LeaderRegistry registry = new LeaderRegistry();
        registry.join("node-1");
        registry.join("node-2");
        registry.join("node-3");

        System.out.println("Current leader: " + registry.currentLeader());
    }
}
```

How to run: `java LeaderElectionDemo.java`. Expected output: `Current leader: node-1` — the first candidate to register becomes leader, the simplest form of the election.

### Level 2 — Intermediate

```java
// LeaderElectionDemo.java
import java.util.*;

public class LeaderElectionDemo {
    static class LeaderRegistry {
        private final List<String> candidates = new ArrayList<>();
        private String notifiedLeader = null;

        void join(String nodeId) { candidates.add(nodeId); reconcile(); }

        // Real-world concern: the flow reacts to leadership CHANGES via events (OnGrantedEvent /
        // OnRevokedEvent), not by polling "who's leader" -- only start/stop the job on a transition.
        private void reconcile() {
            String current = candidates.isEmpty() ? null : candidates.get(0);
            if (!Objects.equals(current, notifiedLeader)) {
                if (notifiedLeader != null) System.out.println(notifiedLeader + ": leadership REVOKED");
                if (current != null) System.out.println(current + ": leadership GRANTED, starting scheduled job");
                notifiedLeader = current;
            }
        }
    }

    public static void main(String[] args) {
        LeaderRegistry registry = new LeaderRegistry();
        registry.join("node-1");
        registry.join("node-2"); // joining doesn't change the leader, so no event fires again
    }
}
```

How to run: `java LeaderElectionDemo.java`. Expected output: only `node-1: leadership GRANTED, starting scheduled job` prints — `node-2` joining as a standby candidate produces no event, since leadership didn't actually change hands, matching how a real `LeaderEventPublisher` only fires on genuine transitions.

### Level 3 — Advanced

```java
// LeaderElectionDemo.java
import java.util.*;

public class LeaderElectionDemo {
    static class LeaderRegistry {
        private final List<String> candidates = new ArrayList<>();
        private String notifiedLeader = null;

        void join(String nodeId) { candidates.add(nodeId); reconcile(); }

        // Production concern: the current leader can disappear at any time (crash, network
        // partition) -- Zookeeper's ephemeral nodes detect this and the next candidate must be
        // promoted automatically, with the job stopped on the old leader's side and started fresh
        // on the new one.
        void leave(String nodeId) { candidates.remove(nodeId); reconcile(); }

        private void reconcile() {
            String current = candidates.isEmpty() ? null : candidates.get(0);
            if (!Objects.equals(current, notifiedLeader)) {
                if (notifiedLeader != null) System.out.println(notifiedLeader + ": leadership REVOKED, stopping scheduled job");
                if (current != null) System.out.println(current + ": leadership GRANTED, starting scheduled job");
                notifiedLeader = current;
            }
        }
    }

    public static void main(String[] args) {
        LeaderRegistry registry = new LeaderRegistry();
        registry.join("node-1");
        registry.join("node-2");
        registry.join("node-3");

        System.out.println("-- node-1 crashes (Zookeeper session expires, ephemeral node removed) --");
        registry.leave("node-1");

        System.out.println("-- node-2 also crashes --");
        registry.leave("node-2");
    }
}
```

How to run: `java LeaderElectionDemo.java`. Expected output: `node-1` is granted leadership initially; after it leaves, `node-1: leadership REVOKED, stopping scheduled job` and `node-2: leadership GRANTED, starting scheduled job` print in sequence; after `node-2` also leaves, leadership transitions to `node-3` the same way — demonstrating automatic failover without any node needing to notice and manually reassign the job.

## 6. Walkthrough

Trace a leadership transition end to end.

1. **Startup**: each application instance connects to the Zookeeper ensemble via Curator and registers itself as a leader-election candidate for a named role (e.g., `"scheduledJobRole"`), creating an ephemeral sequential node in Zookeeper's tree.
2. **Election**: Zookeeper's ordering of ephemeral sequential nodes determines the leader — the candidate holding the lowest-numbered node is granted leadership; every other candidate watches the node just ahead of it in the sequence.
3. **Grant event**: the elected instance's `LeaderInitiator` fires an `OnGrantedEvent`, which the application's `@EventListener` reacts to — in the example, starting the scheduled job.
4. **Normal operation**: only the leader runs the job; standby instances remain idle but continue watching Zookeeper for a change in leadership.
5. **Leader failure**: if the leader crashes or its network connection to Zookeeper drops, its session expires and Zookeeper automatically removes its ephemeral node (this is the core guarantee ephemeral nodes provide — they vanish when the session that created them ends).
6. **Automatic failover**: the removal of that node triggers the next-lowest candidate's watch, promoting it to leader; its `OnGrantedEvent` fires, starting the job on the new leader, while any prior leader (if it recovers) receives an `OnRevokedEvent` and stops running the job — ensuring exactly one instance is ever active at a time even through failures.

```
node-1 registers (ephemeral seq node #1) -> granted leader -> job starts
node-2 registers (ephemeral seq node #2) -> standby, watches node #1
node-3 registers (ephemeral seq node #3) -> standby, watches node #2

node-1 session expires (crash/network partition)
  -> Zookeeper removes node #1
    -> node-2's watch fires -> node-2 granted leader -> job starts on node-2
```

## 7. Gotchas & takeaways

> **Gotcha:** leadership can briefly appear to have "two leaders" during a network partition if the failure detection (session timeout) hasn't yet expired the old leader's ephemeral node — a job that must never run twice concurrently needs its own idempotency or fencing token in addition to leader election, since election alone guarantees eventual consistency, not an instantaneous, glitch-free handoff.

- Zookeeper's guarantees come from a quorum-based consensus protocol; running it as a single node defeats its purpose entirely — production deployments need an odd number of nodes (typically 3 or 5) to tolerate failures while still reaching quorum.
- Ephemeral nodes are the mechanism that makes failover automatic: they exist only as long as the client session that created them is alive, so a crashed instance is detected and its leadership released without any manual cleanup.
- Reserve Zookeeper-backed coordination for cases where the deployment already runs Zookeeper for another purpose (historically, older Kafka clusters); if nothing else in the stack needs it, a JDBC- or Redis-backed lock registry (card 0048) avoids operating an entirely separate coordination service.
- Distinguish leader election (deciding who runs a duty) from the lock registry (mutual exclusion for a specific critical section) — they solve related but different problems, and Zookeeper support in Spring Integration offers both, backed by the same underlying ensemble.
