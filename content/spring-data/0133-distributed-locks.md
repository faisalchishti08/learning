---
card: spring-data
gi: 133
slug: distributed-locks
title: "Distributed locks"
---

## 1. What it is

A **distributed lock** uses Redis as a shared coordination point so that multiple application instances — running on different machines, unable to use an in-process `synchronized` block — can agree that only one of them is allowed to perform some action at a time. The standard building block is `SET key value NX EX ttl`: set a key only if it doesn't already exist (`NX`), with an automatic expiration (`EX`), all as one atomic operation.

```java
Boolean acquired = redisTemplate.opsForValue()
    .setIfAbsent("lock:order:1", "instance-A", Duration.ofSeconds(10)); // SET lock:order:1 instance-A NX EX 10

if (Boolean.TRUE.equals(acquired)) {
    try { /* critical section: only ONE instance runs this at a time */ }
    finally { redisTemplate.delete("lock:order:1"); }
}
```

## 2. Why & when

A `synchronized` block or a `java.util.concurrent.Lock` only coordinates threads *within one JVM* — it does nothing to stop a second application instance, running on a different machine, from doing the same work at the same time. When several instances of a horizontally-scaled application need to agree "only one of us processes this job / sends this email / runs this scheduled task right now," they need a lock that all of them can see — Redis, being centrally reachable and offering atomic operations, is a natural fit.

Reach for a Redis-based distributed lock when:

- Multiple application instances poll the same queue or table and must not process the same item twice — acquiring a per-item lock before processing prevents duplicate work.
- A scheduled task (`@Scheduled`) runs identically on every instance in a cluster, but the work itself should only actually happen once per interval, not once per instance.
- You need mutual exclusion across process/machine boundaries for a short-lived critical section, and a full distributed consensus system (like ZooKeeper) would be overkill for the actual reliability requirements.

## 3. Core concept

```
 Instance A:  SET lock:order:1 "A" NX EX 10   -> OK (key didn't exist)  -- A now holds the lock
 Instance B:  SET lock:order:1 "B" NX EX 10   -> (nil), key already exists -- B does NOT get the lock

 Instance A finishes its work:  DEL lock:order:1   -- lock released

 Instance B (or a NEW attempt):  SET lock:order:1 "B" NX EX 10   -> OK now -- B gets the lock
```

`NX` ("set if not exists") plus `EX` (an expiration) combined into one atomic command is what makes this safe: there's no gap between "check if the lock is free" and "take it" for two clients to race into simultaneously.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two instances race to SET NX the same lock key; only one succeeds and proceeds, the other is rejected">
  <rect x="20" y="20" width="220" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Instance A: SET lock NX EX 10</text>

  <rect x="20" y="90" width="220" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="117" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Instance B: SET lock NX EX 10</text>

  <rect x="400" y="20" width="200" height="40" rx="6" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="500" y="44" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">OK -- A holds the lock</text>
  <line x1="240" y1="42" x2="395" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="400" y="100" width="200" height="40" rx="6" fill="#f8514922" stroke="#f85149" stroke-width="1.5"/>
  <text x="500" y="124" fill="#f85149" font-size="9.5" text-anchor="middle" font-family="sans-serif">(nil) -- B rejected</text>
  <line x1="240" y1="112" x2="395" y2="112" stroke="#f85149" stroke-width="2" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`SET ... NX` is atomic on the Redis server, so exactly one of two simultaneous requests wins the lock — there's no race window between the two.

## 5. Runnable example

The scenario: multiple application instances competing to process the same order, evolving from a basic `SET NX` lock, to correctly handling lock expiration for a crashed holder, to a safe-release pattern that only lets the lock's actual owner release it — avoiding one instance accidentally releasing a lock it no longer holds.

### Level 1 — Basic

Model `SET key value NX EX ttl`: atomically acquire a lock only if it's currently free.

```java
import java.util.*;

public class DistributedLockLevel1 {
    public static void main(String[] args) {
        RedisLockServer redis = new RedisLockServer();

        boolean instanceAAcquired = redis.setIfAbsent("lock:order:1", "instance-A", 10, 0);
        System.out.println("Instance A acquired lock: " + instanceAAcquired);

        boolean instanceBAcquired = redis.setIfAbsent("lock:order:1", "instance-B", 10, 0); // same key, still held
        System.out.println("Instance B acquired lock: " + instanceBAcquired);

        redis.delete("lock:order:1"); // instance A releases it
        boolean instanceBRetry = redis.setIfAbsent("lock:order:1", "instance-B", 10, 0);
        System.out.println("Instance B acquired lock after release: " + instanceBRetry);
    }
}

class LockEntry { String owner; long expiresAt; LockEntry(String owner, long expiresAt) { this.owner = owner; this.expiresAt = expiresAt; } }

// Stands in for redisTemplate.opsForValue().setIfAbsent(key, value, Duration) -- mirrors SET key value NX EX ttl.
class RedisLockServer {
    private final Map<String, LockEntry> locks = new HashMap<>();

    boolean setIfAbsent(String key, String owner, long ttlSeconds, long nowSeconds) {
        LockEntry existing = locks.get(key);
        if (existing != null && nowSeconds < existing.expiresAt) return false; // NX -- key already exists and is live
        locks.put(key, new LockEntry(owner, nowSeconds + ttlSeconds)); // atomically claims the lock
        return true;
    }
    void delete(String key) { locks.remove(key); }
}
```

How to run: `java DistributedLockLevel1.java`

`setIfAbsent` mirrors `SET lock:order:1 instance-A NX EX 10` as one atomic check-and-set: instance A's first call succeeds because the key is free; instance B's call, while the key is still held, fails and returns `false`. Only after instance A explicitly `delete`s the key does instance B's retry succeed — matching the real mutual-exclusion guarantee `SET NX` provides.

### Level 2 — Intermediate

Show why the `EX` (expiration) part matters: a lock holder that crashes without releasing the lock would otherwise block every other instance forever — the TTL is what guarantees eventual recovery.

```java
import java.util.*;

public class DistributedLockLevel2 {
    public static void main(String[] args) {
        RedisLockServer redis = new RedisLockServer();

        // Instance A acquires the lock at t=0 with a 10s TTL, then CRASHES without releasing it.
        boolean acquired = redis.setIfAbsent("lock:order:1", "instance-A", 10, 0);
        System.out.println("Instance A acquired lock at t=0: " + acquired);
        System.out.println("(instance A crashes here -- never calls delete)");

        boolean retryAt5 = redis.setIfAbsent("lock:order:1", "instance-B", 10, 5);
        System.out.println("Instance B retries at t=5 (lock TTL not yet elapsed): " + retryAt5);

        boolean retryAt11 = redis.setIfAbsent("lock:order:1", "instance-B", 10, 11);
        System.out.println("Instance B retries at t=11 (lock TTL of 10s HAS elapsed): " + retryAt11);
    }
}

class LockEntry { String owner; long expiresAt; LockEntry(String owner, long expiresAt) { this.owner = owner; this.expiresAt = expiresAt; } }

class RedisLockServer {
    private final Map<String, LockEntry> locks = new HashMap<>();
    boolean setIfAbsent(String key, String owner, long ttlSeconds, long nowSeconds) {
        LockEntry existing = locks.get(key);
        if (existing != null && nowSeconds < existing.expiresAt) return false;
        locks.put(key, new LockEntry(owner, nowSeconds + ttlSeconds));
        return true;
    }
}
```

How to run: `java DistributedLockLevel2.java`

Instance A acquires the lock at `t=0` with a 10-second TTL and then never releases it (simulating a crash). Instance B's retry at `t=5` fails, since `5 < expiresAt (10)` — the lock is still considered held. Instance B's retry at `t=11` succeeds, since `11 < 10` is `false` — the TTL has elapsed, so Redis (via this simulated check) treats the key as available again, and instance B claims it. Without the `EX` component, a crashed holder would leave the lock held forever, with no other instance ever able to proceed.

### Level 3 — Advanced

Add safe release: only the instance that actually holds the lock should be able to release it, using a unique per-holder token — otherwise instance A could accidentally release a lock that instance B has since (validly) acquired after A's own lock expired.

```java
import java.util.*;

public class DistributedLockLevel3 {
    public static void main(String[] args) {
        RedisLockServer redis = new RedisLockServer();

        String instanceAToken = UUID.randomUUID().toString();
        redis.setIfAbsent("lock:order:1", instanceAToken, 10, 0); // A acquires with ITS OWN unique token

        // Simulate: A's TTL expires (t=11) BEFORE it gets around to releasing -- B acquires the lock legitimately.
        String instanceBToken = UUID.randomUUID().toString();
        boolean bAcquired = redis.setIfAbsent("lock:order:1", instanceBToken, 10, 11);
        System.out.println("Instance B acquired the (now expired) lock: " + bAcquired);

        // A FINALLY gets around to releasing -- but must check its OWN token matches before deleting.
        boolean aReleaseSafe = redis.releaseIfOwner("lock:order:1", instanceAToken);
        System.out.println("Instance A's release attempt (wrong owner by now): succeeded=" + aReleaseSafe);
        System.out.println("Lock still held by B afterward: " + (redis.currentOwner("lock:order:1") != null));

        boolean bReleaseSafe = redis.releaseIfOwner("lock:order:1", instanceBToken);
        System.out.println("Instance B's own release attempt: succeeded=" + bReleaseSafe);
    }
}

class LockEntry { String owner; long expiresAt; LockEntry(String owner, long expiresAt) { this.owner = owner; this.expiresAt = expiresAt; } }

class RedisLockServer {
    private final Map<String, LockEntry> locks = new HashMap<>();

    boolean setIfAbsent(String key, String owner, long ttlSeconds, long nowSeconds) {
        LockEntry existing = locks.get(key);
        if (existing != null && nowSeconds < existing.expiresAt) return false;
        locks.put(key, new LockEntry(owner, nowSeconds + ttlSeconds));
        return true;
    }

    // Mirrors a Lua script comparing GET key == expectedOwner before DEL key, atomically -- prevents releasing SOMEONE ELSE's lock.
    boolean releaseIfOwner(String key, String expectedOwner) {
        LockEntry current = locks.get(key);
        if (current == null || !current.owner.equals(expectedOwner)) return false; // NOT our lock anymore -- do nothing
        locks.remove(key);
        return true;
    }

    String currentOwner(String key) { LockEntry e = locks.get(key); return e == null ? null : e.owner; }
}
```

How to run: `java DistributedLockLevel3.java`

Instance A acquires the lock with its own unique `instanceAToken`. By `t=11`, A's TTL has expired, so instance B legitimately acquires the same key with its own `instanceBToken`. When A *finally* attempts to release (perhaps after a slow garbage-collection pause), `releaseIfOwner` compares the *current* lock's owner against `instanceAToken` — they no longer match, since B now holds it — so the release is correctly refused, leaving B's legitimate lock intact. Only B's own release, using `instanceBToken`, actually succeeds.

## 6. Walkthrough

Execution starts in `main` for Level 3. `instanceAToken` is generated as a random UUID, and `redis.setIfAbsent("lock:order:1", instanceAToken, 10, 0)` stores a `LockEntry` with `owner = instanceAToken` and `expiresAt = 10`.

`instanceBToken` is generated, and `redis.setIfAbsent("lock:order:1", instanceBToken, 10, 11)` is called at simulated `t=11`. Inside `setIfAbsent`, `existing` is the entry owned by A, and the check `11 < existing.expiresAt (10)` evaluates to `false` — meaning A's lock is treated as expired — so the method proceeds to overwrite `locks.get("lock:order:1")` with a *new* `LockEntry` owned by `instanceBToken`, expiring at `11 + 10 = 21`. `bAcquired` is `true`.

`redis.releaseIfOwner("lock:order:1", instanceAToken)` is then called, simulating instance A finally attempting to clean up after its (now-irrelevant) critical section. Inside, `current` is the entry just written for B; `current.owner.equals(instanceAToken)` compares B's token against A's token — they differ, so the method returns `false` immediately without touching `locks` at all. The lock, still owned by B, is untouched: `currentOwner("lock:order:1")` remains non-`null`.

`redis.releaseIfOwner("lock:order:1", instanceBToken)` is called last. This time `current.owner.equals(instanceBToken)` is `true`, since B is indeed the current holder, so `locks.remove(key)` runs and the method returns `true`.

```
Instance B acquired the (now expired) lock: true
Instance A's release attempt (wrong owner by now): succeeded=false
Lock still held by B afterward: true
Instance B's own release attempt: succeeded=true
```

In real Redis, this ownership check must be **atomic** with the delete — a plain `GET key` followed by a separate `DEL key` has a race window where the lock could expire and be reacquired by someone else *between* those two commands, defeating the whole safety check. The standard fix, exactly matching `RedisLockServer.releaseIfOwner`'s single-method atomicity here, is a Lua script (covered in the next card) executed via `EVAL` — `if redis.call("GET", KEYS[1]) == ARGV[1] then return redis.call("DEL", KEYS[1]) else return 0 end` — which Redis guarantees runs as one indivisible unit on the server.

## 7. Gotchas & takeaways

> Gotcha: a plain `GET` then `DEL` for "safe release" is *not* actually safe — there's a gap between the two commands where the lock could expire and be legitimately reacquired by another instance, and your `DEL` would then delete *their* lock instead of a no-op. The check-and-delete must be one atomic operation (a Lua script via `EVAL`), not two separate round trips.

> Gotcha: choosing a TTL is a real trade-off — too short, and a slow-but-still-alive lock holder can have its lock expire and be stolen mid-work (causing two instances to run the critical section concurrently after all); too long, and a genuinely crashed holder blocks everyone else for that entire duration. Production implementations often extend ("renew") the TTL periodically while the holder is confirmed still working, rather than relying on one fixed TTL for the whole operation.

- `SET key value NX EX ttl` atomically acquires a lock only if it's currently free, with an automatic expiration — the foundational primitive for a Redis distributed lock.
- The TTL is what guarantees a crashed lock holder doesn't block every other instance forever, at the cost of a lock potentially expiring while its real holder is still legitimately working.
- Releasing a lock must verify the caller still owns it (via a unique per-holder token) and do so atomically, to avoid one instance releasing a lock that's since been legitimately reacquired by someone else.
- Redis-based locks are appropriate for short-lived, best-effort mutual exclusion; a use case that needs stronger correctness guarantees under network partitions typically needs a purpose-built consensus system instead.
