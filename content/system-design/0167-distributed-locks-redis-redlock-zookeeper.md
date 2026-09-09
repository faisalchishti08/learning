---
card: system-design
gi: 167
slug: distributed-locks-redis-redlock-zookeeper
title: Distributed locks (Redis Redlock / ZooKeeper)
---

## 1. What it is

A **distributed lock** lets multiple separate processes, running on different machines, coordinate so that only one of them at a time can perform some action — the same idea as an in-process mutex, but working across a network instead of inside one process's memory. **Redlock** is an algorithm for implementing this using Redis; **ZooKeeper** (and similarly, etcd) provides distributed locks as a built-in feature of a purpose-built coordination service.

## 2. Why & when

When several application instances could otherwise all try to do the same exclusive job at once — running a scheduled cleanup task, processing the same queue item, or updating a shared resource — an in-process lock does nothing, since each instance has its own separate memory. A distributed lock, held in a shared external system, is what actually enforces "only one instance does this right now," across the whole fleet. Use it whenever exactly-one-at-a-time execution matters across multiple servers, such as a leader-only scheduled job, or protecting a critical section of a shared external resource that itself provides no locking of its own.

## 3. Core concept

- **Acquire with a unique token and an expiry (TTL):** a client sets a lock key in Redis (e.g. `SET lock:job1 clientId NX EX 30`) only if it does not already exist, with a time-to-live so the lock is automatically released if the holder crashes without releasing it.
- **Release by checking ownership first:** releasing the lock must verify the caller still owns it (matching its unique token) before deleting the key — otherwise a client could accidentally release a lock another client now holds, after its own lock expired.
- **TTL is a safety net, not a substitute for finishing work in time:** if the work takes longer than the TTL, the lock can expire while the original holder is still working, letting a second client acquire it — a real risk that must be accounted for (e.g. by extending the TTL while still working, or by making the protected work itself idempotent).
- **Redlock's added robustness:** Redlock acquires the lock across multiple independent Redis instances, requiring a majority to succeed, so a single Redis instance failing does not silently break the locking guarantee.
- **ZooKeeper/etcd's approach:** these are purpose-built coordination services using ephemeral nodes tied to a client's active session — if the client's session dies (e.g. it crashes), the coordination service itself detects this and removes the lock automatically, without relying on a fixed TTL guess.

## 4. Diagram

```
   client A                    client B                 Redis (or ZooKeeper/etcd)
      |                            |                            |
      |-- SET lock:job1 A NX EX 30 ---------------------------->|
      |<----------------------------------------- OK (acquired) |
      | (doing exclusive work)     |                            |
      |                            |-- SET lock:job1 B NX EX 30->|
      |                            |<---------- FAIL (exists) ---|
      |                            |  (client B waits / retries) |
      |-- DEL lock:job1 (if owner==A) ------------------------->|
      |<---------------------------------------------- released |
      |                            |-- SET lock:job1 B NX EX 30->|
      |                            |<--------------- OK (acquired)|
```
*Caption: only one client's `SET ... NX` succeeds at a time; the loser must wait until the lock is released (or its TTL expires) before it can acquire it.*

## 5. Runnable example

This models the Redis-based lock in-process; the "How to run" note shows the real Redis commands.

**Level 1 — Basic.** Acquire a lock only if it is not already held, modeling `SET ... NX`.

**Level 2 — TTL-based automatic expiry.** A lock releases itself automatically if its holder never releases it in time.

**Level 3 — Safe release, checking ownership first.** Prevent a client from releasing a lock it no longer actually owns.

```java
// DistributedLockDemo.java
import java.util.*;
import java.util.concurrent.*;

public class DistributedLockDemo {

    // Models the Redis key used as the lock: holder's token + an expiry time.
    static class FakeRedisLock {
        String currentHolderToken = null;
        long expiresAtMillis = 0;

        // Level 1 & 2: acquire only if unheld OR the previous holder's TTL has expired.
        synchronized boolean tryAcquire(String token, long ttlMillis, long nowMillis) {
            if (currentHolderToken == null || nowMillis >= expiresAtMillis) {
                currentHolderToken = token;
                expiresAtMillis = nowMillis + ttlMillis;
                return true;
            }
            return false;
        }

        // Level 3: release ONLY if the caller still owns the lock (matching token) - never blindly delete.
        synchronized boolean release(String token) {
            if (token.equals(currentHolderToken)) {
                currentHolderToken = null;
                return true;
            }
            return false; // this caller's lock already expired and someone else may hold it now
        }
    }

    public static void main(String[] args) throws InterruptedException {
        FakeRedisLock lock = new FakeRedisLock();
        long ttl = 30_000; // 30 second TTL

        // Level 1: client A acquires the lock first.
        boolean aAcquired = lock.tryAcquire("client-A", ttl, 0);
        System.out.println("client-A tryAcquire: " + aAcquired);

        // client B tries immediately after - fails, since A still holds it and its TTL has not expired.
        boolean bAcquired = lock.tryAcquire("client-B", ttl, 1000);
        System.out.println("client-B tryAcquire (1s later): " + bAcquired);

        // Level 2: client B tries again after A's TTL has expired (simulate A crashing without releasing).
        boolean bAcquiredAfterExpiry = lock.tryAcquire("client-B", ttl, 31_000);
        System.out.println("client-B tryAcquire (31s later, A's TTL expired): " + bAcquiredAfterExpiry);

        // Level 3: client A (which crashed and never actually finished) now tries to release its OLD lock.
        boolean aReleaseAttempt = lock.release("client-A");
        System.out.println("client-A release attempt (lock now held by B): " + aReleaseAttempt + " (correctly refused - A no longer owns it)");

        // client B correctly releases its own, still-valid lock.
        boolean bRelease = lock.release("client-B");
        System.out.println("client-B release: " + bRelease);
    }
}
```

**How to run:** save as `DistributedLockDemo.java`, then run `java DistributedLockDemo.java`. (Real Redis: `SET lock:job1 <uniqueToken> NX EX 30` to acquire; release with a Lua script that checks `GET lock:job1 == <uniqueToken>` before `DEL`, so the check-and-delete is atomic.)

## 6. Walkthrough

1. `lock.tryAcquire("client-A", ttl, 0)` finds `currentHolderToken == null`, so it succeeds, setting the holder to `"client-A"` and `expiresAtMillis = 0 + 30000 = 30000`.
2. `lock.tryAcquire("client-B", ttl, 1000)` finds `currentHolderToken` is not `null` and `nowMillis (1000) < expiresAtMillis (30000)`, so the condition fails and the method returns `false` — client B correctly cannot acquire a lock client A still legitimately holds.
3. `lock.tryAcquire("client-B", ttl, 31_000)` now finds `nowMillis (31000) >= expiresAtMillis (30000)` is true, meaning client A's TTL has expired (modeling client A having crashed without ever releasing it); the lock is granted to `"client-B"`, and a new `expiresAtMillis` is set from this later time.
4. `lock.release("client-A")` checks whether `"client-A".equals(currentHolderToken)`, but `currentHolderToken` is now `"client-B"`, so the check fails and `release` correctly returns `false` — if this check were skipped, client A would have deleted client B's active, legitimate lock, letting a third client acquire it too, with two clients now believing they exclusively hold it.
5. `lock.release("client-B")` checks the same condition, finds it matches, sets `currentHolderToken = null`, and returns `true` — the lock is now genuinely free for the next acquirer.

## 7. Gotchas & takeaways

> Gotcha: this demo's `release` check-then-delete is only safe because it runs inside one `synchronized` method (atomic by construction); implementing the same check and delete as two separate Redis calls (`GET` then `DEL`) reintroduces a race condition where another client could acquire the lock in between — always use a single atomic operation (a Lua script in real Redis) for check-then-release, exactly as for [centralized Redis counters](0147-centralized-counter-redis-rate-limiting.md).

- A distributed lock coordinates exclusive access across separate machines, which no in-process lock can do.
- A TTL prevents a crashed holder from locking a resource forever, but introduces its own risk if the protected work outlives the TTL.
- Releasing a lock must verify current ownership first — an unconditional delete can release someone else's now-valid lock.
- Related concepts: [ZooKeeper / etcd as coordination services](0171-zookeeper-etcd-as-coordination-services.md) (a session-based alternative avoiding the fixed-TTL guess entirely), [Leader election](0169-leader-election.md) (a common use case built directly on top of distributed locking), [Optimistic vs pessimistic concurrency](0166-optimistic-vs-pessimistic-concurrency.md) (a distributed lock is the multi-machine form of pessimistic locking).
