---
card: microservices
gi: 509
slug: leader-election
title: "Leader election"
---

## 1. What it is

**Leader election** is the process by which a group of equivalent service instances agree on exactly one of themselves to act as the "leader" — responsible for some coordinated role (running scheduled tasks, being the single writer to a resource) — while the rest remain **followers**, standing by to detect if the leader disappears and elect a new one. Unlike a [distributed lock](0508-distributed-locks.md), which protects a one-off critical section, leader election establishes an ongoing role that persists until the leader fails or steps down.

## 2. Why & when

You use leader election specifically when a coordinating role needs to be held continuously by exactly one instance, with automatic failover if that instance goes away:

- **Some responsibilities genuinely shouldn't be performed by multiple instances simultaneously, on an ongoing basis** — not a single operation, but a continuous role, like being the one instance that polls an external system and fans out results to the rest of the fleet.
- **A distributed lock re-acquired repeatedly for the same ongoing role is a clunky fit** — leader election is the pattern purpose-built for "who's in charge right now, continuously, with automatic handoff on failure," rather than a series of discrete lock acquisitions.
- **Automatic failover matters** — if the current leader crashes, the system should detect that and promote a new leader without manual intervention, keeping the coordinated role continuously staffed.
- **You reach for this when the coordination is a standing role**, not a one-time operation — for a single scheduled job that just needs to run once, a simpler [distributed lock](0508-distributed-locks.md) acquired at each run is usually a better, simpler fit than full leader election machinery.

## 3. Core concept

Think of a rotating on-call schedule where exactly one person is "on-call" at any given moment, responsible for responding to pages — if that person becomes unreachable (their phone dies), the team needs a mechanism to detect that and hand the on-call role to the next available person automatically, rather than pages going unanswered indefinitely. Leader election is that same continuous "exactly one is responsible right now" role, with automatic reassignment on failure.

Concretely:

1. **Instances periodically attempt to become or remain the leader**, typically by maintaining a lease (much like a distributed lock's TTL) that must be periodically renewed.
2. **The current leader performs the coordinated role** while it holds the lease, and proactively renews that lease before it expires, as long as it's healthy and running.
3. **If the leader fails to renew the lease in time** (because it crashed, became unresponsive, or lost network connectivity), the lease expires, and any follower can then successfully claim leadership.
4. **A new leader is elected**, typically whichever follower's next lease-acquisition attempt succeeds, and it begins performing the coordinated role — the transition should be quick enough that the role's absence is brief.
5. **Followers continuously watch for this transition** — either by periodically attempting to acquire leadership themselves, or by subscribing to a leadership-change notification if the underlying coordination mechanism supports one.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Instance A holds leadership and renews its lease; when it crashes and stops renewing, its lease expires and instance B becomes the new leader">
  <rect x="20" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">instance A: LEADER</text>
  <text x="110" y="62" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">renews lease every interval</text>

  <rect x="230" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">instance B: follower</text>

  <rect x="20" y="120" width="180" height="55" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="110" y="145" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">instance A: CRASHED</text>
  <text x="110" y="162" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">lease expires, unrenewed</text>

  <rect x="230" y="120" width="180" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">instance B: NEW LEADER</text>
  <text x="320" y="162" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">claims the expired lease</text>

  <line x1="110" y1="75" x2="110" y2="120" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="320" y1="75" x2="320" y2="120" stroke="#8b949e" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The leader's crash and unrenewed lease trigger automatic failover to a follower.

## 5. Runnable example

Scenario: three instances electing and maintaining a leader. We start with basic leader election via a leased lock, extend it to periodic lease renewal by the current leader, then handle the hard case: the leader crashing (stops renewing), with a follower correctly detecting this and becoming the new leader.

### Level 1 — Basic

```java
// File: LeaderElectionBasic.java -- models BASIC leader election: an
// instance attempts to claim leadership via a leased lock, exactly like
// acquiring a distributed lock.
import java.util.concurrent.*;

public class LeaderElectionBasic {
    record Lease(String leaderId, long expiresAtMs) {}
    static ConcurrentHashMap<String, Lease> leadershipStore = new ConcurrentHashMap<>();
    static String LEADER_KEY = "cluster-leader";

    static boolean tryBecomeLeader(String instanceId, long leaseMs) {
        long now = System.currentTimeMillis();
        Lease[] result = new Lease[1];
        leadershipStore.compute(LEADER_KEY, (k, existing) -> {
            if (existing == null || now >= existing.expiresAtMs()) {
                result[0] = new Lease(instanceId, now + leaseMs);
                return result[0];
            }
            result[0] = existing;
            return existing;
        });
        return result[0].leaderId().equals(instanceId);
    }

    public static void main(String[] args) {
        boolean becameLeader = tryBecomeLeader("instance-A", 1000);
        System.out.println("[instance-A] became leader: " + becameLeader);
    }
}
```

How to run: `java LeaderElectionBasic.java`

`tryBecomeLeader` uses the same atomic `compute`-based expiry check as a distributed lock's `tryAcquire` — leader election's acquisition mechanics are essentially identical to a distributed lock's, the difference is in how the lease is used afterward (continuously renewed, rather than released after one operation).

### Level 2 — Intermediate

```java
// File: LeaderRenewsLease.java -- the SAME election, now with the LEADER
// PERIODICALLY RENEWING its lease while healthy, keeping leadership
// continuously rather than needing to re-win a fresh race each time.
import java.util.concurrent.*;

public class LeaderRenewsLease {
    record Lease(String leaderId, long expiresAtMs) {}
    static ConcurrentHashMap<String, Lease> leadershipStore = new ConcurrentHashMap<>();
    static String LEADER_KEY = "cluster-leader";

    static boolean tryBecomeOrRenewLeader(String instanceId, long leaseMs) {
        long now = System.currentTimeMillis();
        Lease[] result = new Lease[1];
        leadershipStore.compute(LEADER_KEY, (k, existing) -> {
            boolean expired = existing == null || now >= existing.expiresAtMs();
            boolean isCurrentLeaderRenewing = existing != null && existing.leaderId().equals(instanceId);
            if (expired || isCurrentLeaderRenewing) {
                result[0] = new Lease(instanceId, now + leaseMs);
                return result[0];
            }
            result[0] = existing;
            return existing;
        });
        return result[0].leaderId().equals(instanceId);
    }

    public static void main(String[] args) throws InterruptedException {
        for (int round = 1; round <= 3; round++) {
            boolean isLeader = tryBecomeOrRenewLeader("instance-A", 200);
            System.out.println("round " + round + ": instance-A is leader = " + isLeader + " (renewing its own lease)");
            Thread.sleep(50);
        }
    }
}
```

How to run: `java LeaderRenewsLease.java`

`isCurrentLeaderRenewing` lets the existing leader extend its own lease even before it expires, since `existing.leaderId().equals(instanceId)` is `true` for its own renewal calls — this is what keeps a healthy leader continuously in charge across many rounds, rather than the role having to be freshly re-won from scratch each time.

### Level 3 — Advanced

```java
// File: LeaderCrashFailover.java -- the SAME renewing leader, now
// handling the PRODUCTION-FLAVORED hard case: the LEADER CRASHES (STOPS
// renewing). A FOLLOWER must correctly detect the expired lease and
// become the new leader, with the transition happening automatically.
import java.util.concurrent.*;

public class LeaderCrashFailover {
    record Lease(String leaderId, long expiresAtMs) {}
    static ConcurrentHashMap<String, Lease> leadershipStore = new ConcurrentHashMap<>();
    static String LEADER_KEY = "cluster-leader";

    static boolean tryBecomeOrRenewLeader(String instanceId, long leaseMs) {
        long now = System.currentTimeMillis();
        Lease[] result = new Lease[1];
        leadershipStore.compute(LEADER_KEY, (k, existing) -> {
            boolean expired = existing == null || now >= existing.expiresAtMs();
            boolean isCurrentLeaderRenewing = existing != null && existing.leaderId().equals(instanceId);
            if (expired || isCurrentLeaderRenewing) {
                result[0] = new Lease(instanceId, now + leaseMs);
                return result[0];
            }
            result[0] = existing;
            return existing;
        });
        return result[0].leaderId().equals(instanceId);
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("--- instance-A becomes leader, renews twice while healthy ---");
        for (int round = 1; round <= 2; round++) {
            boolean isLeader = tryBecomeOrRenewLeader("instance-A", 100);
            System.out.println("round " + round + ": instance-A leader=" + isLeader);
            Thread.sleep(30);
        }

        System.out.println();
        System.out.println("[incident] instance-A CRASHES -- stops renewing entirely");

        System.out.println();
        System.out.println("--- instance-B checks IMMEDIATELY, lease not yet expired ---");
        boolean bImmediateAttempt = tryBecomeOrRenewLeader("instance-B", 100);
        System.out.println("instance-B leader=" + bImmediateAttempt + " (correctly still instance-A's lease, not yet expired)");

        System.out.println();
        System.out.println("--- waiting for instance-A's lease to expire ---");
        Thread.sleep(120);

        System.out.println();
        System.out.println("--- instance-B checks AGAIN, lease has now expired ---");
        boolean bAfterExpiry = tryBecomeOrRenewLeader("instance-B", 100);
        System.out.println("instance-B leader=" + bAfterExpiry + " -- FAILOVER complete, new leader elected automatically");
    }
}
```

How to run: `java LeaderCrashFailover.java`

`instance-A` renews twice while "healthy," then the code simply stops calling anything for it, modeling a crash. `instance-B`'s immediate attempt correctly fails, since `instance-A`'s most recent renewal set a fresh, still-valid expiry. Only after sleeping past that lease duration does `instance-B`'s subsequent attempt succeed — `expired` becomes `true` in `tryBecomeOrRenewLeader`'s check, letting `instance-B` claim leadership purely through lease expiry, without any explicit handoff from the crashed `instance-A`.

## 6. Walkthrough

Trace `LeaderCrashFailover.main` in order. **First**, `instance-A` calls `tryBecomeOrRenewLeader` twice in a loop, each time either winning fresh leadership (round 1, since `leadershipStore` starts empty) or renewing its own lease (round 2, via the `isCurrentLeaderRenewing` branch) — both rounds report `instance-A` as leader.

**Next**, the simulated crash means no further calls are ever made on `instance-A`'s behalf — its most recent lease, set during round 2, continues counting down toward its own expiry with nothing renewing it further.

**Then**, `instance-B`'s immediate attempt runs `tryBecomeOrRenewLeader("instance-B", 100)`. Inside the `compute` lambda, `existing` is `instance-A`'s still-valid lease, `expired` is `false` (not enough time has passed), and `isCurrentLeaderRenewing` is `false` (the leader ID doesn't match `instance-B`) — so neither branch condition is met, `existing` is returned unchanged, and `instance-B`'s attempt correctly fails.

**After that**, `Thread.sleep(120)` advances real time past the `100ms` lease duration set during `instance-A`'s last renewal.

**Finally**, `instance-B`'s second attempt runs the identical check, but now `expired` evaluates to `true`, since real elapsed time has exceeded the lease's expiry — the acquisition branch runs, a new `Lease` for `instance-B` replaces the stale one, and `instance-B` becomes the new leader, completing an automatic failover that required no explicit coordination from the crashed `instance-A` at all.

```
--- instance-A becomes leader, renews twice while healthy ---
round 1: instance-A leader=true
round 2: instance-A leader=true

[incident] instance-A CRASHES -- stops renewing entirely

--- instance-B checks IMMEDIATELY, lease not yet expired ---
instance-B leader=false (correctly still instance-A's lease, not yet expired)

--- waiting for instance-A's lease to expire ---

--- instance-B checks AGAIN, lease has now expired ---
instance-B leader=true -- FAILOVER complete, new leader elected automatically
```

## 7. Gotchas & takeaways

> A leader that renews its lease too infrequently relative to the lease duration risks losing leadership to a follower during a brief slowdown, even without actually crashing — tune the renewal interval to be comfortably shorter than the lease TTL (a common rule of thumb is renewing at roughly a third of the TTL), so transient slowness doesn't trigger an unnecessary failover.
- Leader election is the right pattern for an ongoing, continuous role; a [distributed lock](0508-distributed-locks.md) acquired fresh for each individual operation is the right pattern for a one-off critical section — don't reach for the heavier leader-election machinery when a simple lock suffices.
- Followers should be built to correctly handle either role — the code that runs "when I'm the leader" needs to be ready to start at any moment a follower successfully wins a failover election, and equally ready to stop cleanly if it ever loses leadership.
- Real-world leader election is often built on top of a purpose-built coordination service (ZooKeeper, etcd, Kubernetes' own leader-election primitives built on the API server) rather than hand-rolled, since these systems provide the underlying consistency and notification guarantees this pattern depends on.
- A brief period with no leader at all (during the gap between a crash and a new leader's election) is a normal, expected part of this pattern — design the coordinated role to tolerate a short gap in coverage, rather than assuming leadership transitions instantaneously.
