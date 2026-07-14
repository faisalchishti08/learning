---
card: microservices
gi: 534
slug: spring-cloud-cluster-zookeeper-redis-locks
title: "Spring Cloud Cluster / ZooKeeper / Redis locks"
---

## 1. What it is

**Spring Cloud Cluster** was an earlier, now-largely-superseded project that provided a common abstraction for distributed locks and leader election across multiple backing stores (ZooKeeper, Redis, Hazelcast) — much of its functionality has since moved into or been mirrored by [Spring Integration's `LockRegistry` and leader-election support](0533-spring-integration-leader-election-locks.md), plus store-specific modules like `spring-integration-zookeeper` and Spring Data Redis's own `RedisLockRegistry`. Regardless of which specific library surface you use, the underlying idea is the same: a **ZooKeeper**-backed lock leans on ZooKeeper's native ephemeral, sequential znodes to implement correct distributed mutual exclusion, while a **Redis**-backed lock builds mutual exclusion out of atomic Redis commands (`SET key value NX PX ttl`) plus a time-to-live safety net.

## 2. Why & when

You choose between ZooKeeper-backed and Redis-backed locks based on what's already in your infrastructure and how strict your correctness requirements are:

- **ZooKeeper is purpose-built for coordination.** Its data model (ephemeral znodes tied to a client session, sequential ordering, watches for change notification) was designed specifically to implement correct distributed locks and leader election, and its consensus protocol (ZAB) gives strong consistency guarantees — if you already run ZooKeeper (common in Kafka-based or Hadoop-ecosystem deployments), it's a natural, battle-tested choice for locking too.
- **Redis is far more commonly already present** in a typical microservices stack (as a cache, if nothing else), so a Redis-backed lock avoids introducing an entirely new piece of infrastructure just for locking — at the cost of Redis's locking guarantees being somewhat weaker in edge cases (particularly around clock drift and failover) than ZooKeeper's, unless you adopt more involved algorithms like Redlock, which itself has documented correctness caveats under network partitions.
- **The core mechanism differs in an important way**: ZooKeeper's ephemeral znodes are tied to the client's *session* — if a client crashes or its network connection to ZooKeeper drops, the session (and its ephemeral znode) is cleaned up automatically and promptly by ZooKeeper itself, releasing the lock. A basic Redis lock instead relies on a **time-to-live (TTL)** on the lock key — if the holder crashes, the lock isn't released until the TTL expires, meaning there's an unavoidable window where the lock appears held even though its holder is gone.
- **Choose ZooKeeper when correctness under failure is paramount** and you can afford to operate it; choose Redis when it's already part of your stack and the TTL-based failure window (typically seconds) is an acceptable trade-off for your use case.

## 3. Core concept

Think of two different ways a shared meeting room might be locked. A ZooKeeper-style lock is like a smart badge reader tied to your live presence — if you leave the building (your connection drops), the system detects your badge going out of range almost immediately and the room is marked free again automatically. A Redis-style lock is more like a physical timer you set on the door when you enter — "reserved for the next 30 minutes" — which correctly keeps others out while you're using the room, but if you leave early or collapse inside, nobody else can use the room until that timer actually runs out, because nothing is actively watching whether you're still really there.

Concretely:

1. **ZooKeeper locks use ephemeral, sequential znodes**: each client wanting the lock creates a sequentially-numbered ephemeral node under a shared path; the client whose node has the lowest sequence number holds the lock, and everyone else watches the node just ahead of them in sequence, waking up only when that specific node is deleted (released or the holder's session expired) — an efficient, event-driven wait rather than polling.
2. **Redis locks use an atomic `SET key uniqueValue NX PX ttl` command**: `NX` means "only set if the key doesn't already exist" (atomic acquire), `PX ttl` sets an expiration so the lock self-releases if never explicitly unlocked, and the unique value (often a UUID) lets the holder safely verify it's still the rightful owner before releasing, rather than accidentally releasing a lock some other client has since acquired after this one's TTL expired.
3. **The TTL is both Redis's safety net and its weakness**: it guarantees a crashed holder's lock eventually releases (unlike a naive lock with no expiration at all, which could be held forever), but it also means there's a real window between a holder crashing and the TTL expiring during which the lock is unavailable to anyone else, even though its original holder is gone.
4. **ZooKeeper's session-based approach avoids that specific window** at the cost of requiring and operating an entire additional coordination service, with its own operational complexity (an odd-numbered ensemble of nodes, careful session timeout tuning) that a Redis-based approach, often reusing infrastructure you already run, avoids.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ZooKeeper lock releases promptly when the holder's session drops; Redis lock waits out its TTL even after the holder crashes, leaving a window where the lock is held by nobody reachable">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">ZooKeeper: session-tied</text>
  <rect x="20" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">holder crashes -&gt; session drops</text>
  <rect x="20" y="75" width="260" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="150" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ZK detects fast, ephemeral node GONE</text>
  <text x="150" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">lock free almost immediately after the crash</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Redis: TTL-based</text>
  <rect x="380" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">holder crashes -&gt; key still set</text>
  <rect x="380" y="75" width="260" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="510" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">lock STAYS held until TTL expires</text>
  <text x="510" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">unavoidable window: nobody can acquire it meanwhile</text>
</svg>

ZooKeeper's session-tied ephemeral nodes release promptly on failure; Redis's TTL-based locks guarantee eventual release but tolerate a real gap after a crash.

## 5. Runnable example

Scenario: two competing instances trying to acquire a lock, one of which then crashes while holding it. We start with a plain Java model of a naive lock with no expiration (showing the "stuck forever" risk), extend it to a TTL-based Redis-style lock, then handle the hard case: safe release using a unique holder token, avoiding one instance accidentally releasing a lock another instance now legitimately holds.

### Level 1 — Basic

```java
// File: NaiveLockNoExpiration.java -- a lock with NO expiration at all:
// if the holder crashes before releasing, the lock is held FOREVER.
import java.util.concurrent.atomic.AtomicBoolean;

public class NaiveLockNoExpiration {
    static AtomicBoolean lockHeld = new AtomicBoolean(false);

    static boolean tryAcquire(String holder) {
        boolean acquired = lockHeld.compareAndSet(false, true);
        System.out.println(holder + " tryAcquire -> " + acquired);
        return acquired;
    }

    public static void main(String[] args) {
        tryAcquire("instance-A"); // acquires successfully
        // instance-A now "crashes" -- simulated by simply never calling release()
        boolean b = tryAcquire("instance-B"); // FOREVER blocked -- no expiration mechanism exists
        System.out.println("instance-B acquired? " + b + " -- STUCK until someone manually intervenes; no TTL, no session detection.");
    }
}
```

How to run: `java NaiveLockNoExpiration.java`

`lockHeld` has no expiration mechanism whatsoever — once set to `true` by `instance-A`, nothing in this code will ever reset it if `instance-A` fails to call a release method (simulated here by simply never calling one). `instance-B`'s subsequent attempt correctly fails, but there's no path back to a working lock without manual intervention — exactly the risk both ZooKeeper's session-based approach and Redis's TTL-based approach are designed to avoid.

### Level 2 — Intermediate

```java
// File: TtlBasedLock.java -- adds a Redis-STYLE time-to-live: the lock
// automatically expires and becomes acquirable again, even if the
// holder never explicitly releases it.
import java.time.*;
import java.util.concurrent.atomic.*;

public class TtlBasedLock {
    static AtomicReference<Instant> lockExpiresAt = new AtomicReference<>(null); // null = not held

    static boolean tryAcquire(String holder, Duration ttl, Instant now) {
        Instant currentExpiry = lockExpiresAt.get();
        boolean expired = currentExpiry != null && now.isAfter(currentExpiry);
        if (currentExpiry == null || expired) {
            lockExpiresAt.set(now.plus(ttl)); // acquire with a hard expiration
            System.out.println(holder + " acquired lock, expires at " + lockExpiresAt.get() + (expired ? " (previous holder's TTL had expired)" : ""));
            return true;
        }
        System.out.println(holder + " tryAcquire FAILED -- still held until " + currentExpiry);
        return false;
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-01-01T00:00:00Z");
        tryAcquire("instance-A", Duration.ofSeconds(30), t0); // acquires with a 30s TTL

        // instance-A "crashes" -- never releases. instance-B tries again 10s later: still held.
        tryAcquire("instance-B", Duration.ofSeconds(30), t0.plusSeconds(10));

        // instance-B tries AGAIN 35s after A's acquisition: A's TTL has now expired
        tryAcquire("instance-B", Duration.ofSeconds(30), t0.plusSeconds(35));
    }
}
```

How to run: `java TtlBasedLock.java`

`lockExpiresAt` models Redis's `PX ttl` behavior: a lock acquired at `t0` with a 30-second TTL is still correctly reported as held 10 seconds later (`instance-B`'s attempt at `t0+10s` fails), but by `t0+35s`, the TTL has passed, so `instance-B`'s attempt succeeds — the lock self-released purely from time passing, with no explicit action from the crashed `instance-A` required. This closes Level 1's "stuck forever" risk, at the cost of a real window (up to 30 seconds here) where the lock was held by a holder that had already crashed.

### Level 3 — Advanced

```java
// File: SafeReleaseWithToken.java -- adds a UNIQUE HOLDER TOKEN so a
// lock can only be released by whoever ACTUALLY currently holds it --
// preventing a stale release from clobbering a NEW legitimate holder.
import java.time.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;

public class SafeReleaseWithToken {
    record LockState(String token, Instant expiresAt) {}
    static AtomicReference<LockState> state = new AtomicReference<>(null);

    static Optional<String> tryAcquire(Duration ttl, Instant now) {
        LockState current = state.get();
        boolean expired = current != null && now.isAfter(current.expiresAt());
        if (current == null || expired) {
            String token = UUID.randomUUID().toString(); // UNIQUE per acquisition -- this is the safety mechanism
            state.set(new LockState(token, now.plus(ttl)));
            return Optional.of(token);
        }
        return Optional.empty();
    }

    // release ONLY succeeds if the caller's token matches the CURRENT holder's token
    static boolean release(String token) {
        LockState current = state.get();
        if (current != null && current.token().equals(token)) {
            state.compareAndSet(current, null);
            return true;
        }
        return false; // this caller is NOT the current legitimate holder -- refuse to release
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-01-01T00:00:00Z");

        String tokenA = tryAcquire(Duration.ofSeconds(10), t0).orElseThrow();
        System.out.println("instance-A acquired with token " + tokenA);

        // instance-A "crashes" here, WITHOUT calling release(tokenA)

        // 15 seconds later: A's TTL has expired, instance-B acquires with a NEW token
        String tokenB = tryAcquire(Duration.ofSeconds(10), t0.plusSeconds(15)).orElseThrow();
        System.out.println("instance-B acquired with DIFFERENT token " + tokenB);

        // instance-A, unaware it's long dead, FINALLY gets around to calling release(tokenA) -- e.g. a delayed retry
        boolean released = release(tokenA);
        System.out.println("instance-A's stale release(tokenA) succeeded? " + released + " -- correctly REFUSED, since tokenA != current token");
        System.out.println("Lock still held by instance-B? " + (state.get() != null));
    }
}
```

How to run: `java SafeReleaseWithToken.java`

Each acquisition gets a fresh, unique `token`; `release(token)` only actually clears the lock if the supplied token matches the *current* holder's token exactly. When `instance-A`'s long-delayed `release(tokenA)` call finally arrives — after its TTL already expired and `instance-B` legitimately acquired the lock with a different token — the release is correctly refused, because `tokenA` no longer matches the current holder's token (`tokenB`). Without this token check, `instance-A`'s stale release call would have incorrectly cleared `instance-B`'s legitimate, currently-active lock.

## 6. Walkthrough

Trace `SafeReleaseWithToken.main` end to end:

1. **`tryAcquire(10s, t0)` is called.** `state.get()` is `null` (unheld), so a new `token = tokenA` (a fresh UUID) is generated, and `state` is set to `LockState(tokenA, t0+10s)`. `instance-A` now holds the lock with expiration `t0+10s`.
2. **`instance-A` "crashes"** — in this simulation, simply by never calling `release(tokenA)` before the next step. This models exactly the failure scenario a TTL exists to protect against.
3. **`tryAcquire(10s, t0+15s)` is called** (representing `instance-B`, 15 seconds later). `state.get()` returns the still-present `LockState(tokenA, t0+10s)`; the code checks `now.isAfter(expiresAt)` — `t0+15s` is after `t0+10s`, so `expired = true`. Since `current != null` but `expired`, the acquisition proceeds: a brand-new `token = tokenB` is generated, and `state` is overwritten with `LockState(tokenB, t0+25s)`.
4. **`release(tokenA)` is called** — representing `instance-A` finally getting around to its (long overdue, and now meaningless) cleanup call. Inside `release`, `current = state.get()` returns `LockState(tokenB, ...)` (from step 3). The check `current.token().equals(token)` compares `tokenB.equals(tokenA)`, which is `false` — so `release` returns `false` without touching `state` at all.
5. **`main` prints that the stale release was correctly refused**, and confirms `state.get() != null` — the lock remains held by `instance-B`'s legitimate `tokenB`, completely unaffected by `instance-A`'s stale, out-of-order release attempt.

This token check is precisely what a correct Redis-based lock implementation does in practice (typically via a small Lua script executed atomically in Redis, checking the token *and* deleting the key in one atomic step) — without it, a delayed or retried release call from a former holder could silently steal the lock out from under whoever legitimately holds it now, a subtle and dangerous class of bug that's easy to miss if you implement TTL-based locking without this safeguard.

## 7. Gotchas & takeaways

> **Gotcha:** the check-token-then-delete-key sequence in `release()` must be a single atomic operation against the real store (a Lua script in Redis, for instance) — checking the token in one round-trip and then deleting the key in a separate round-trip introduces a race window where another instance could acquire the lock *between* those two operations, letting a stale release delete a different, legitimate holder's lock anyway.

- ZooKeeper's ephemeral-znode-per-session model releases a crashed holder's lock promptly, with no configurable TTL trade-off, but requires operating an entire additional coordination service.
- Redis-based locks are simpler to add when Redis is already part of your infrastructure, but every lock needs a TTL for safety, and that TTL creates an unavoidable window between a holder crashing and the lock actually releasing.
- A unique per-acquisition token, checked atomically before release, is essential for Redis-style locks — without it, a delayed or retried release from a former holder can incorrectly release a different, currently-legitimate holder's lock.
- Choose based on what's already operated in your infrastructure and how much risk the TTL window poses for your specific use case — a lock protecting an idempotent, infrequent batch job can tolerate a longer TTL window than one protecting a rapidly-repeating, non-idempotent operation.
