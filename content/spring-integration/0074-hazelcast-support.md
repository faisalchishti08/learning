---
card: spring-integration
gi: 74
slug: hazelcast-support
title: "Hazelcast support"
---

## 1. What it is

Hazelcast support (`HazelcastLockRegistry`, `HazelcastMetadataStore`, and Hazelcast-backed distributed collections used as channels or stores) integrates a flow with Hazelcast — an in-memory data grid that replicates data across cluster members. Like the Zookeeper support (card 0072), it plugs into the same `LockRegistry` and `MetadataStore` interfaces used elsewhere in Spring Integration, but backed by Hazelcast's in-memory, replicated data structures instead of a coordination-focused service.

## 2. Why & when

You reach for Hazelcast support when the deployment already runs Hazelcast as its in-memory data grid and wants coordination or shared state to use that same infrastructure:

- **The application already caches data in Hazelcast** — if Hazelcast maps are already how the application shares session data or cached lookups across cluster members, reusing it for a `MetadataStore` (idempotency tracking, last-processed markers) avoids introducing a second, separate coordination technology just for the integration layer.
- **Distributed locking across cluster members is needed, and low latency matters more than Zookeeper's stronger consistency guarantees** — `HazelcastLockRegistry` provides mutual exclusion backed by an in-memory, replicated lock, typically faster to acquire and release than a Zookeeper- or database-backed lock, at the cost of Hazelcast's slightly different failure and consistency characteristics under a network partition.
- **The team's operational expertise and existing infrastructure investment is in Hazelcast** rather than Zookeeper or Redis — using whichever coordination technology is already deployed and well-understood avoids the operational cost of running and monitoring a second one.

## 3. Core concept

Think of Hazelcast as a shared whiteboard that every member of a distributed team can see and write to at once, with the whiteboard's contents automatically kept in sync (replicated) across every copy in the room, rather than living on one person's desk. A distributed lock in Hazelcast is like a physical marker on that whiteboard: whoever picks it up gets to write in a specific section undisturbed, and everyone else waits their turn — the same mutual-exclusion idea as any other lock registry (card 0048), just backed by in-memory replication rather than a database row or a Zookeeper ephemeral node.

```java
@Bean
public LockRegistry lockRegistry(HazelcastInstance hazelcastInstance) {
    return new HazelcastLockRegistry(hazelcastInstance);
}

@ServiceActivator(inputChannel = "batchJobTrigger")
public void runBatchJobExclusively(Message<?> message) {
    Lock lock = lockRegistry.obtain("nightly-batch-job");
    if (lock.tryLock()) {
        try { batchJobRunner.run(); } finally { lock.unlock(); }
    }
}
```

Any cluster member calling `obtain("nightly-batch-job")` competes for the same in-memory-replicated lock, so only one member's `tryLock()` ever succeeds at a time.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Hazelcast replicates lock and metadata state across every cluster member in memory; a lock acquired by one member is immediately visible to all others as held" >
  <rect x="20" y="20" width="150" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">member-1</text>
  <text x="95" y="58" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">holds lock</text>

  <rect x="190" y="20" width="150" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="265" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">member-2</text>
  <text x="265" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">tryLock() fails</text>

  <rect x="360" y="20" width="150" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="435" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">member-3</text>
  <text x="435" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">tryLock() fails</text>

  <rect x="150" y="105" width="300" height="40" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="130" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Hazelcast in-memory replicated lock state</text>

  <line x1="95" y1="75" x2="230" y2="105" stroke="#6db33f" stroke-width="1.2"/>
  <line x1="265" y1="75" x2="290" y2="105" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="435" y1="75" x2="350" y2="105" stroke="#8b949e" stroke-width="1.2"/>
</svg>

Lock state lives in Hazelcast's in-memory grid, visible to every member the instant it changes.

## 5. Runnable example

The scenario: making sure only one cluster member runs a nightly batch job, simulated with a plain shared object standing in for `HazelcastLockRegistry` (no real Hazelcast cluster needed to demonstrate the mutual-exclusion and contention-handling logic), starting with a basic try-lock, then adding lock-holder tracking across attempts, then adding a lease timeout so a crashed lock holder doesn't block the job forever.

### Level 1 — Basic

```java
// HazelcastLockDemo.java
import java.util.concurrent.locks.*;
import java.util.concurrent.*;

public class HazelcastLockDemo {
    // Stand-in for HazelcastLockRegistry.obtain(key): a shared, cluster-wide lock.
    static final Lock sharedLock = new ReentrantLock();

    static void runIfLockAcquired(String memberName) {
        if (sharedLock.tryLock()) {
            try {
                System.out.println(memberName + " acquired the lock, running batch job");
            } finally {
                sharedLock.unlock();
            }
        } else {
            System.out.println(memberName + " could not acquire the lock, skipping");
        }
    }

    public static void main(String[] args) {
        runIfLockAcquired("member-1");
    }
}
```

How to run: `java HazelcastLockDemo.java`. Expected output: `member-1 acquired the lock, running batch job` — a single member with no contention.

### Level 2 — Intermediate

```java
// HazelcastLockDemo.java
import java.util.concurrent.locks.*;

public class HazelcastLockDemo {
    static final Lock sharedLock = new ReentrantLock();

    // Real-world concern: multiple cluster members may attempt the same job at once (e.g. a
    // scheduled trigger firing on every node) -- only one must actually run it.
    static void runIfLockAcquired(String memberName) {
        if (sharedLock.tryLock()) {
            try {
                System.out.println(memberName + " acquired the lock, running batch job");
            } finally {
                sharedLock.unlock();
            }
        } else {
            System.out.println(memberName + " could not acquire the lock, skipping");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        // Simulate member-1 holding the lock while member-2 and member-3 also attempt it.
        sharedLock.lock();
        try {
            Thread contender2 = new Thread(() -> runIfLockAcquired("member-2"));
            Thread contender3 = new Thread(() -> runIfLockAcquired("member-3"));
            contender2.start(); contender2.join();
            contender3.start(); contender3.join();
        } finally {
            sharedLock.unlock();
        }
        runIfLockAcquired("member-1"); // now lock is free
    }
}
```

How to run: `java HazelcastLockDemo.java`. Expected output: while `member-1` holds the lock, both `member-2` and `member-3` print "could not acquire the lock, skipping"; once released, `member-1`'s own subsequent attempt succeeds — exactly one member ever runs the job per acquisition window.

### Level 3 — Advanced

```java
// HazelcastLockDemo.java
import java.util.concurrent.*;
import java.util.concurrent.locks.*;

public class HazelcastLockDemo {
    // A lock with a lease: if the holder crashes without unlocking, the lease timeout expires
    // it automatically, the way HazelcastLockRegistry's lease-time semantics prevent a crashed
    // node from holding a distributed lock forever.
    static class LeasedLock {
        private volatile String heldBy = null;
        private volatile long expiresAtMillis = 0;

        synchronized boolean tryLock(String memberName, long leaseMillis, long nowMillis) {
            if (heldBy == null || nowMillis > expiresAtMillis) {
                heldBy = memberName;
                expiresAtMillis = nowMillis + leaseMillis;
                return true;
            }
            return false;
        }

        synchronized void unlock(String memberName) {
            if (memberName.equals(heldBy)) heldBy = null;
        }
    }

    public static void main(String[] args) {
        LeasedLock lock = new LeasedLock();
        long now = 0;

        System.out.println(lock.tryLock("member-1", 5000, now) + " -- member-1 acquires (lease 5000ms)");
        System.out.println(lock.tryLock("member-2", 5000, now + 1000) + " -- member-2 tries too soon, lease still active");

        // member-1 crashes without calling unlock(); simulate time passing beyond the lease.
        long muchLater = now + 6000;
        System.out.println(lock.tryLock("member-2", 5000, muchLater) + " -- member-2 retries after lease expired");
    }
}
```

How to run: `java HazelcastLockDemo.java`. Expected output: `true -- member-1 acquires`, then `false -- member-2 tries too soon`, then `true -- member-2 retries after lease expired` — the lease timeout reclaiming the lock automatically once enough time has passed, exactly the protection needed against a crashed lock-holder blocking the job forever.

## 6. Walkthrough

Trace a batch job's single-member execution through cluster contention and a simulated crash recovery.

1. **Trigger fires on every node**: a scheduled trigger configured identically on every application instance fires at the same time, since the schedule itself doesn't know about cluster membership.
2. **Lock acquisition attempt**: each instance calls `lockRegistry.obtain("nightly-batch-job").tryLock()`, which checks (and, if free, claims) the shared lock state replicated across the Hazelcast cluster.
3. **Winner proceeds**: exactly one instance's `tryLock()` succeeds; it runs the batch job inside a `try/finally` that releases the lock afterward, ensuring the lock is freed even if the job throws.
4. **Losers skip**: every other instance's `tryLock()` returns `false` immediately (non-blocking), and those instances simply skip this run — no job duplication, no waiting.
5. **Crash resilience**: if the winning instance crashes mid-job without reaching the `finally` block (a JVM kill, not a caught exception), a lock with a lease time — rather than an indefinite hold — automatically expires after its configured lease, so a later attempt (the next scheduled run, or an immediate retry) can reclaim the lock rather than the job being permanently blocked by a dead holder.
6. **Steady state**: over many scheduled firings, exactly one instance runs the job each time, with cluster membership free to change (nodes joining or leaving) without needing any code change, since the lock coordination lives in Hazelcast's replicated state rather than any single node's local memory.

```
scheduled trigger fires identically on member-1, member-2, member-3
  -> each calls lockRegistry.obtain("nightly-batch-job").tryLock()
       member-1: true  -> runs job -> unlock() in finally
       member-2: false -> skip
       member-3: false -> skip

(if member-1 crashes before unlock)
  -> lease timeout expires the lock automatically
    -> next attempt can reclaim it
```

## 7. Gotchas & takeaways

> **Gotcha:** a `tryLock()` that never reaches its `finally`/`unlock()` block (because the holding instance crashed, not merely because an exception was thrown and caught) leaves the lock held until its lease expires — always configure an explicit, reasonably short lease time on any Hazelcast-backed lock used for a recurring job, rather than relying on the holder to always clean up gracefully.

- Hazelcast's replication model favors low-latency access within the cluster over the stronger consistency guarantees a Zookeeper ensemble (card 0072) provides during network partitions — pick Hazelcast when speed and "already using it" matter more, Zookeeper when partition-tolerant consistency is the priority.
- Because Hazelcast state is in-memory, a full cluster restart (all members down at once) loses all lock and metadata state unless it's also configured with a persistence layer — plan for that if the coordinated state must survive a total outage.
- `tryLock()` (non-blocking, immediate return) is usually the right choice for "only one instance should run this job" scenarios; a blocking `lock()` call is more appropriate when a caller genuinely needs to wait its turn rather than skip the work entirely.
- Reuse whichever data grid or coordination service is already operationally established in the deployment — introducing Hazelcast solely for Spring Integration's lock registry when Zookeeper or a database is already running and well-understood adds operational surface area without a clear benefit.
