---
card: spring-cloud
gi: 119
slug: leader-election
title: "Leader election"
---

## 1. What it is

Spring Cloud Kubernetes provides leader election built on Kubernetes' own native `Lease` (or `ConfigMap`-based, in older versions) coordination primitive — among several replicas of the same application, exactly one is elected "leader" at any given time, and application code can register a callback that runs only on whichever instance currently holds leadership, letting a task that must run exactly once across the whole fleet (a scheduled cleanup job, a cache-warming routine) be safely enabled on every replica's code path while actually executing on only one.

```java
@Bean
CuratorLeaderInitiator leaderInitiator(...) { ... } // conceptual -- exact API varies by Spring Cloud Kubernetes version

@EventListener
void onGrantedLeadership(OnGrantedEvent event) {
    System.out.println("this instance is now the LEADER");
    scheduledCleanupJob.enable();
}

@EventListener
void onRevokedLeadership(OnRevokedEvent event) {
    scheduledCleanupJob.disable(); // this instance is no longer leader -- stop doing leader-only work
}
```

## 2. Why & when

Running several replicas of a service for availability and throughput is standard practice, but some tasks are fundamentally single-writer in nature — a scheduled job that must run exactly once (not once per replica, which would mean N duplicate executions for N replicas), a background process managing a shared external resource that would conflict if multiple instances touched it simultaneously. Leader election solves this by having the replicas themselves coordinate (via Kubernetes' Lease object, which supports atomic, contended acquisition) to agree on exactly one current leader, with the platform's own atomicity guarantees ensuring no two replicas ever simultaneously believe they hold leadership, and automatic re-election if the current leader crashes or becomes unreachable, so leader-only work resumes on a different replica without manual intervention.

Reach for leader election when:

- A scheduled task must run exactly once across a fleet of replicas, not once per replica — enabling a `@Scheduled` job unconditionally on every replica would produce N duplicate runs; gating it behind "am I currently the leader" produces exactly one.
- Managing a resource that genuinely requires single-writer access at the application level — even briefly having two replicas both believe they're responsible for the same external coordination task risks conflicting writes or duplicated side effects.
- High availability for the leader role itself matters — if the current leader crashes, leader election automatically promotes a different healthy replica, so the leader-only work resumes without requiring an operator to intervene.

## 3. Core concept

```
 N replicas of the SAME application, all running the SAME code:

   replica-1: attempts to acquire the Lease -- SUCCEEDS -> becomes LEADER
   replica-2: attempts to acquire the Lease -- FAILS (already held) -> remains a FOLLOWER
   replica-3: attempts to acquire the Lease -- FAILS (already held) -> remains a FOLLOWER

 ONLY replica-1 runs leader-only work (e.g. the scheduled cleanup job)

 IF replica-1 crashes or its Lease renewal lapses:
   Kubernetes releases the Lease -- another replica's NEXT acquisition attempt SUCCEEDS
   -> that replica becomes the NEW leader, leader-only work resumes THERE
```

Every replica runs identical code and identically attempts leadership — which one actually succeeds is decided by the Kubernetes Lease object's own atomic acquisition semantics, not by any application-level coordination the replicas perform among themselves directly.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three identical replicas all attempt to acquire a shared Kubernetes Lease object with only replica one succeeding and becoming leader while replicas two and three remain followers running no leader only work">
  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Kubernetes Lease object</text>

  <rect x="20" y="110" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="130" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">replica-1: LEADER</text>
  <text x="95" y="144" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">runs leader-only work</text>

  <rect x="230" y="110" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="305" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">replica-2: follower</text>

  <rect x="440" y="110" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="515" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">replica-3: follower</text>

  <defs><marker id="a119" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="95" y1="110" x2="290" y2="66" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a119)"/>
  <line x1="305" y1="110" x2="310" y2="66" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3" marker-end="url(#a119)"/>
  <line x1="515" y1="110" x2="330" y2="66" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3" marker-end="url(#a119)"/>
</svg>

Solid line: the successful acquisition. Dashed lines: failed attempts — those replicas simply remain followers, running no leader-only logic.

## 5. Runnable example

The scenario: model several identical replicas competing for one shared Lease, with only the successful acquirer running leader-only work, and automatic re-election when the current leader "crashes." Start with a single acquisition attempt, then add multiple competing replicas with only one succeeding, then add leader failure and automatic promotion of a new leader.

### Level 1 — Basic

One replica attempting to acquire a shared lease and, on success, running leader-only work.

```java
public class LeaderElectionLevel1 {
    static class SharedLease {
        String currentHolder = null;
        synchronized boolean tryAcquire(String replicaId) {
            if (currentHolder == null) {
                currentHolder = replicaId;
                return true;
            }
            return false; // already held by someone else
        }
    }

    static void runLeaderOnlyWork(String replicaId) {
        System.out.println(replicaId + ": running leader-only work (e.g. scheduled cleanup)");
    }

    public static void main(String[] args) {
        SharedLease lease = new SharedLease();

        boolean acquired = lease.tryAcquire("replica-1");
        if (acquired) runLeaderOnlyWork("replica-1");
    }
}
```

How to run: `java LeaderElectionLevel1.java`

`tryAcquire` succeeds because `currentHolder` starts `null` — this is the simplest case, a single replica with no competition, always becoming leader.

### Level 2 — Intermediate

Add multiple competing replicas attempting acquisition — only the first succeeds, and the rest correctly remain followers running no leader-only work.

```java
public class LeaderElectionLevel2 {
    static class SharedLease {
        String currentHolder = null;
        synchronized boolean tryAcquire(String replicaId) {
            if (currentHolder == null) {
                currentHolder = replicaId;
                return true;
            }
            return false;
        }
    }

    static void runLeaderOnlyWork(String replicaId) {
        System.out.println(replicaId + ": ELECTED LEADER, running leader-only work");
    }

    static void runAsFollower(String replicaId) {
        System.out.println(replicaId + ": remains a FOLLOWER, no leader-only work");
    }

    public static void main(String[] args) {
        SharedLease lease = new SharedLease();

        // three IDENTICAL replicas, all running the SAME code, all attempting acquisition
        for (String replicaId : new String[]{"replica-1", "replica-2", "replica-3"}) {
            if (lease.tryAcquire(replicaId)) {
                runLeaderOnlyWork(replicaId);
            } else {
                runAsFollower(replicaId);
            }
        }
    }
}
```

How to run: `java LeaderElectionLevel2.java`

Only `replica-1` (the first to call `tryAcquire`) succeeds and runs leader-only work; `replica-2` and `replica-3` both find `currentHolder` already set to `"replica-1"` and correctly fall back to follower behavior — every replica ran the exact same `if (lease.tryAcquire(...))` code, with the outcome determined entirely by the shared `lease`'s state, not by any special-casing in any individual replica's own logic.

### Level 3 — Advanced

Add leader failure and re-election: the current leader crashes (releases the lease), and a follower's next acquisition attempt succeeds, promoting it to leader and resuming leader-only work there.

```java
public class LeaderElectionLevel3 {
    static class SharedLease {
        String currentHolder = null;
        synchronized boolean tryAcquire(String replicaId) {
            if (currentHolder == null) {
                currentHolder = replicaId;
                return true;
            }
            return false;
        }
        synchronized void release(String replicaId) {
            if (replicaId.equals(currentHolder)) {
                currentHolder = null; // models the Lease expiring/being released when the leader crashes or steps down
                System.out.println(replicaId + " released the lease (crashed or shut down)");
            }
        }
    }

    static void runLeaderOnlyWork(String replicaId) {
        System.out.println(replicaId + ": ELECTED LEADER, running leader-only work");
    }

    static void runAsFollower(String replicaId) {
        System.out.println(replicaId + ": remains a FOLLOWER");
    }

    public static void main(String[] args) {
        SharedLease lease = new SharedLease();
        String[] replicas = {"replica-1", "replica-2", "replica-3"};

        System.out.println("-- initial election --");
        for (String r : replicas) {
            if (lease.tryAcquire(r)) runLeaderOnlyWork(r); else runAsFollower(r);
        }

        System.out.println("-- replica-1 (the current leader) crashes --");
        lease.release("replica-1");

        System.out.println("-- re-election among remaining candidates --");
        // remaining replicas (2 and 3) attempt acquisition again -- one of them will now succeed
        for (String r : new String[]{"replica-2", "replica-3"}) {
            if (lease.tryAcquire(r)) runLeaderOnlyWork(r); else runAsFollower(r);
        }
    }
}
```

How to run: `java LeaderElectionLevel3.java`

After `lease.release("replica-1")` sets `currentHolder` back to `null`, the re-election loop's first attempt (`"replica-2"`) succeeds this time, becoming the new leader — `"replica-3"` still finds the lease held (now by `replica-2`) and remains a follower; leader-only work correctly resumes, now on `replica-2`, with no code anywhere needing to specifically detect "the old leader crashed" beyond the lease's own state naturally reflecting that its previous holder released it.

## 6. Walkthrough

Trace the crash-and-re-election sequence in Level 3.

1. In the initial election loop, `"replica-1"` calls `tryAcquire`, finds `currentHolder == null`, sets `currentHolder = "replica-1"`, and returns `true` — `runLeaderOnlyWork("replica-1")` runs.
2. `"replica-2"` and `"replica-3"` each call `tryAcquire` next, both finding `currentHolder` already `"replica-1"`, so both return `false` and run `runAsFollower` instead.
3. `lease.release("replica-1")` is called — inside, `replicaId.equals(currentHolder)` checks `"replica-1".equals("replica-1")`, which is `true`, so `currentHolder` is reset to `null`, and a message is printed confirming the release; this models a real Kubernetes Lease's holder failing to renew it in time (a crash, a network partition), causing the platform to eventually consider the lease available again.
4. The re-election loop's first iteration calls `lease.tryAcquire("replica-2")` — because `currentHolder` is now `null` again, this succeeds, setting `currentHolder = "replica-2"` and returning `true`, so `runLeaderOnlyWork("replica-2")` runs — leadership has genuinely transferred.
5. The loop's second iteration calls `lease.tryAcquire("replica-3")` — `currentHolder` is now `"replica-2"`, not `null`, so this returns `false`, and `"replica-3"` runs `runAsFollower` — it remains a follower under the new leader, exactly as it was under the old one.

```
initial:  replica-1 acquires -> LEADER;  replica-2, replica-3 -> followers
replica-1 crashes -> lease.release("replica-1") -> currentHolder reset to null
re-election:
  replica-2 attempts -> currentHolder was null -> SUCCEEDS -> replica-2 is the NEW leader
  replica-3 attempts -> currentHolder is now "replica-2" -> FAILS -> remains follower
```

## 7. Gotchas & takeaways

> **Gotcha:** leadership acquisition and renewal in a real Kubernetes Lease-based system happens over a network, with inherent timing uncertainty — a leader that becomes slow or partially unresponsive (rather than cleanly crashing) can, in rare edge cases around lease expiry timing, briefly overlap with a newly-elected leader before the old one's own code notices it lost leadership and stops its leader-only work. Leader-only work that has real side effects (writes to an external system) should ideally also be designed to tolerate this brief overlap gracefully (idempotent writes, for instance), rather than assuming leader election alone provides an absolute, zero-overlap single-writer guarantee.

- Leader election lets identical replica code safely run leader-only logic without manual configuration distinguishing "this is the special instance" — every replica runs the same code, and Kubernetes' own Lease acquisition semantics determine which one actually executes the leader-only path.
- Automatic re-election on leader failure is the key operational benefit over a manually-designated "this one instance runs the cron job" approach — leadership, and the work tied to it, transfers automatically to a healthy replica without requiring an operator to notice the failure and intervene.
- Leader election is appropriate specifically for genuinely single-writer concerns — tasks that must run exactly once across a fleet, not tasks that are naturally safe (or even beneficial) to run redundantly across every replica.
- Because leadership can, in rare timing edge cases, briefly overlap during a transition, leader-only work with real external side effects benefits from being designed idempotently wherever practical, rather than relying purely on leader election's guarantees as an absolute correctness mechanism.
