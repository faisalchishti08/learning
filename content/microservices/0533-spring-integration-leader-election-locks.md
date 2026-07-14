---
card: microservices
gi: 533
slug: spring-integration-leader-election-locks
title: "Spring Integration leader election & locks"
---

## 1. What it is

**Spring Integration** provides a `LockRegistry` abstraction for [distributed locks](0508-distributed-locks.md) and a `LeaderInitiator`/`Candidate` mechanism for [leader election](0509-leader-election.md), both backed by pluggable stores (JDBC, Redis, ZooKeeper) so that multiple instances of a horizontally-scaled service can coordinate — ensuring only one instance holds a given lock at a time, or that exactly one instance is recognized as "the leader" for a particular role, without each instance having to hand-roll its own coordination protocol against the underlying store.

## 2. Why & when

You reach for Spring Integration's locking and leader election support whenever multiple instances of a service need to coordinate around a shared resource or a singleton responsibility:

- **Some work must only happen on one instance at a time, even though the service is horizontally scaled.** A scheduled job that reconciles inventory counts, for instance, would corrupt data or waste resources if every instance in a five-instance fleet ran it simultaneously — exactly one instance should run it per scheduled interval.
- **`LockRegistry` provides a distributed mutual-exclusion primitive**: `lockRegistry.obtain("reconciliation-job")` returns a `Lock` object whose `tryLock()`/`lock()`/`unlock()` behave like `java.util.concurrent.locks.Lock`, but the mutual exclusion is enforced across the whole fleet via the shared backing store, not just within one JVM.
- **Leader election is the right tool when a *role*, not just a one-off task, needs exactly one holder at a time** — one instance recognized as "the leader" for as long as it stays healthy, with automatic failover electing a new leader if the current one crashes or becomes unreachable, rather than repeatedly acquiring and releasing a lock for each individual unit of work.
- **Both mechanisms exist specifically because "just run it on one hardcoded instance" doesn't survive that instance failing**, and "let every instance race to do it" risks duplicate work or corrupted shared state — coordinated, store-backed election or locking gives you exactly-one-at-a-time behavior that automatically adapts as instances come and go.

## 3. Core concept

Think of a team of firefighters where, when the alarm sounds, all five available firefighters shouldn't all pile into the same emergency (redundant, chaotic, and potentially damaging if they interfere with each other) — but exactly one should respond, decided fairly and quickly at the moment the alarm sounds, with a clear rule for what happens if that firefighter becomes unavailable mid-response (someone else takes over). A distributed lock is like grabbing the one truck key hanging on a shared hook — whoever grabs it first drives, everyone else waits their turn for the next alarm. Leader election is more like appointing one firefighter as "shift captain" for the whole shift — they hold that role continuously until they're unavailable, at which point the team automatically recognizes a new captain, rather than re-deciding captaincy for every single call.

Concretely:

1. **`LockRegistry.obtain(lockKey)` returns a distributed `Lock`** — calling `tryLock()` attempts to acquire mutual exclusion across every instance connected to the same backing store; only one instance's `tryLock()` succeeds at a time for a given `lockKey`, and others either block (`lock()`) or fail fast (`tryLock()` returning `false`).
2. **A `LeaderInitiator`, backed by a `Candidate` implementation, participates in a fleet-wide election** — the backing store (ZooKeeper is a common choice, given its built-in support for ephemeral, session-tied nodes) determines exactly one participant is granted leadership at a time.
3. **Leadership is tied to the leader's liveness**, typically via a session or heartbeat mechanism in the backing store — if the leader instance crashes, hangs, or loses connectivity, the backing store detects this (often via a session timeout) and triggers a new election among the remaining candidates automatically.
4. **Application code reacts to leadership events** (`onGranted`, `onRevoked` callbacks on the `Candidate`) rather than polling "am I the leader right now" — an instance that's granted leadership starts doing the leader-only work; an instance that has leadership revoked (or never granted) stays idle for that responsibility until it might be granted leadership later.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A distributed lock grants exclusive, one-at-a-time access to a resource across instances; leader election grants exactly one instance a continuous leader role that fails over automatically if that instance becomes unavailable">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Distributed lock</text>
  <rect x="20" y="35" width="80" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="60" y="56" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance A: HOLDS lock</text>
  <rect x="110" y="35" width="80" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="56" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance B: waits</text>
  <rect x="200" y="35" width="80" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="240" y="56" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance C: waits</text>
  <text x="150" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">A releases -&gt; one of B/C acquires it next, per task</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Leader election</text>
  <rect x="420" y="35" width="80" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="460" y="56" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance A: LEADER</text>
  <rect x="510" y="35" width="60" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="56" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">B: standby</text>
  <rect x="580" y="35" width="60" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="610" y="56" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">C: standby</text>
  <text x="530" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">A crashes -&gt; automatic re-election, B or C becomes leader</text>
</svg>

A lock grants exclusive access per task; leader election grants a continuous role with automatic failover if the leader disappears.

## 5. Runnable example

Scenario: a scheduled reconciliation job that must run on exactly one instance. We start with a plain Java model of the race condition without coordination, extend it to a simple lock-based fix, then handle the real Spring Integration `LockRegistry`/leader-election shape for both a one-off task and a continuous leader role.

### Level 1 — Basic

```java
// File: UncoordinatedRace.java -- WITHOUT coordination, every instance
// runs the "scheduled job" independently -- duplicated, wasted, and
// potentially conflicting work.
public class UncoordinatedRace {
    static void runReconciliationJob(String instanceName) {
        System.out.println("[" + instanceName + "] running reconciliation job (nobody coordinated this!)");
    }

    public static void main(String[] args) {
        // three instances, all triggered by the SAME scheduled interval, with no coordination
        runReconciliationJob("instance-A");
        runReconciliationJob("instance-B");
        runReconciliationJob("instance-C");
        System.out.println("Problem: reconciliation ran 3 TIMES for what should have been ONE run per interval.");
    }
}
```

How to run: `java UncoordinatedRace.java`

Each "instance" independently runs the reconciliation job with no awareness of the others — in a real fleet, this means the same reconciliation logic executes redundantly on every instance, at best wasting resources and at worst corrupting shared state if the job isn't safely idempotent when run concurrently by multiple instances at once.

### Level 2 — Intermediate

```java
// File: SimpleLockCoordination.java -- a MINIMAL lock-based fix: only
// the instance that successfully acquires the shared lock runs the job;
// the others correctly back off.
import java.util.concurrent.atomic.AtomicBoolean;

public class SimpleLockCoordination {
    // simulates a DISTRIBUTED lock shared across instances (a real one would be backed by Redis/JDBC/ZooKeeper)
    static AtomicBoolean sharedLockHeld = new AtomicBoolean(false);

    static boolean tryRunJob(String instanceName) {
        if (sharedLockHeld.compareAndSet(false, true)) { // atomic acquire: only ONE instance can win this race
            try {
                System.out.println("[" + instanceName + "] acquired lock -- running reconciliation job");
                return true;
            } finally {
                sharedLockHeld.set(false); // release for the NEXT scheduled interval
            }
        } else {
            System.out.println("[" + instanceName + "] lock already held -- backing off, not running job");
            return false;
        }
    }

    public static void main(String[] args) {
        tryRunJob("instance-A"); // wins the race, runs, releases
        // simulate B and C attempting AFTER A already released -- in reality this race happens concurrently
        sharedLockHeld.set(true); // simulate A currently holding the lock mid-job
        tryRunJob("instance-B"); // correctly backs off
        tryRunJob("instance-C"); // correctly backs off
    }
}
```

How to run: `java SimpleLockCoordination.java`

`compareAndSet(false, true)` models the atomic, all-or-nothing acquisition a distributed lock provides — only one caller can flip the flag from `false` to `true` at a time. In the simulated concurrent scenario, `instance-B` and `instance-C` both correctly see the lock already held and back off, rather than duplicating the work `instance-A` is already doing.

### Level 3 — Advanced

```java
// File: SpringIntegrationRealShape.java -- the REAL Spring Integration
// shapes: LockRegistry for a one-off scheduled task, and a leader-election
// Candidate for a CONTINUOUS leader role with automatic failover.
import org.springframework.integration.support.locks.LockRegistry;
import org.springframework.integration.leader.Candidate;
import org.springframework.integration.leader.Context;
import org.springframework.integration.leader.event.OnGrantedEvent;
import org.springframework.integration.leader.event.OnRevokedEvent;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.concurrent.locks.Lock;

public class SpringIntegrationRealShape {

    // ONE-OFF TASK, coordinated per scheduled run via a distributed lock
    @Component
    static class ReconciliationJob {
        private final LockRegistry lockRegistry; // backed by JDBC, Redis, or ZooKeeper depending on configuration
        ReconciliationJob(LockRegistry lockRegistry) { this.lockRegistry = lockRegistry; }

        @Scheduled(fixedRate = 60000) // every instance's scheduler fires this, but only one should actually run the job
        public void reconcile() {
            Lock lock = lockRegistry.obtain("reconciliation-job");
            if (lock.tryLock()) {
                try {
                    System.out.println("Acquired lock -- running reconciliation for this interval");
                } finally {
                    lock.unlock(); // release immediately after this run so the NEXT interval can be acquired by anyone
                }
            } else {
                System.out.println("Another instance holds the lock this interval -- skipping");
            }
        }
    }

    // CONTINUOUS ROLE, coordinated via leader election with automatic failover
    @Component
    static class PollerLeaderCandidate implements Candidate {
        private volatile boolean isLeader = false;

        @Override
        public void onGranted(Context context) {
            isLeader = true;
            System.out.println("Granted leadership -- this instance now runs the continuous polling loop");
        }

        @Override
        public void onRevoked(Context context) {
            isLeader = false;
            System.out.println("Leadership revoked -- this instance stops the polling loop (a new leader will be elected)");
        }

        @Override
        public String getRole() { return "message-poller"; }

        public boolean isLeader() { return isLeader; }
    }
}
```

How to run: requires `spring-integration-core` (for `LockRegistry`) plus a store-specific module such as `spring-integration-jdbc` or `spring-integration-redis` for the lock backend, and `spring-integration-zookeeper` for leader election, configured against a real backing store; run multiple instances of the same Spring Boot application pointed at the same store to observe only one instance's `reconcile()` logging "Acquired lock" per interval, and only one `PollerLeaderCandidate` logging "Granted leadership" at a time.

`ReconciliationJob.reconcile()` runs on *every* instance's own scheduler (that part is not coordinated — each JVM has its own `@Scheduled` trigger), but `lockRegistry.obtain("reconciliation-job").tryLock()` ensures only the instance that wins the shared-store-backed race actually executes the reconciliation body; every other instance's `tryLock()` returns `false` and skips. `PollerLeaderCandidate` is different in kind: `onGranted`/`onRevoked` are called by Spring Integration's leader-election machinery in response to the backing store's election outcome, not per scheduled interval — this instance stays the leader continuously until leadership is explicitly revoked (typically because it crashed, hung, or lost connectivity to the store), at which point the store automatically elects a new leader among the remaining candidates.

## 6. Walkthrough

Trace what happens across a three-instance fleet (A, B, C) running `ReconciliationJob`, all sharing the same `LockRegistry` backing store, when their `@Scheduled` triggers fire at approximately the same moment:

1. **All three instances' schedulers fire `reconcile()` at roughly the same time**, since each instance runs its own independent `@Scheduled(fixedRate = 60000)` timer with no coordination between the timers themselves.
2. **Each instance calls `lockRegistry.obtain("reconciliation-job").tryLock()`** — this call reaches out to the shared backing store (say, a database row or a ZooKeeper znode representing the lock `"reconciliation-job"`). Only one of these three concurrent attempts can atomically win the underlying store's compare-and-set (or equivalent) operation.
3. **Say Instance A's `tryLock()` succeeds first.** It proceeds into the `try` block, prints "Acquired lock -- running reconciliation," and performs the reconciliation work.
4. **Instances B and C's `tryLock()` calls both return `false`**, since the store correctly reports the lock is already held by A. Both print "Another instance holds the lock this interval -- skipping" and return immediately, without running any reconciliation logic.
5. **Instance A finishes its reconciliation work and calls `lock.unlock()`** in the `finally` block, releasing the lock back to the shared store.
6. **On the *next* scheduled interval (60 seconds later), the race repeats** — this time, any of A, B, or C could win, since the lock was fully released; there's no guarantee the same instance wins every interval, only that exactly one instance wins each interval.

Now contrast with `PollerLeaderCandidate`: leadership, once granted (say, to Instance A), is *not* re-contested every 60 seconds — A remains the leader continuously, running its polling loop indefinitely, until something changes its liveness status in the backing store (a crash, a network partition, a graceful shutdown). Only at that point does the store detect A's absence (typically via an expired session or lost ephemeral connection) and trigger a new election, at which point one of B or C receives `onGranted` and takes over the role — a fundamentally different coordination shape from the per-interval lock race above, suited to "who is the leader right now" rather than "who gets to run this one task this time."

## 7. Gotchas & takeaways

> **Gotcha:** a `tryLock()` that succeeds but whose holder then crashes *before* calling `unlock()` can leave the lock stuck held forever, unless the backing store supports lock expiration or lease timeouts — always verify the chosen `LockRegistry` backend (JDBC-based locks in particular) has some mechanism to release an abandoned lock, or a single crashed instance can permanently block every future scheduled run.

- Use a distributed lock (`LockRegistry`) for coordinating one-off or per-interval tasks that must run on exactly one instance at a time, re-contested fresh each time.
- Use leader election (`Candidate`/`LeaderInitiator`) for a continuous role that one instance holds until it becomes unavailable, with automatic failover to a healthy remaining instance — not for tasks that should be re-decided on every run.
- Both mechanisms depend entirely on the backing store's ability to detect a holder's failure (via lease expiration, session timeout, or heartbeat) — the coordination is only as reliable as that failure-detection mechanism.
- Application code reacts to leadership events (`onGranted`/`onRevoked`) rather than polling "am I the leader" in a loop — structuring leader-dependent logic around these callbacks keeps the transition (both gaining and losing leadership) explicit and correctly scoped.
