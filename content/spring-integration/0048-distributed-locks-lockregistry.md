---
card: spring-integration
gi: 48
slug: distributed-locks-lockregistry
title: "Distributed locks (LockRegistry)"
---

## 1. What it is

`LockRegistry` is Spring Integration's abstraction for obtaining named, mutual-exclusion locks that work correctly *across multiple application instances*, not just within one JVM's threads. A plain Java `ReentrantLock` only coordinates threads within a single process; `LockRegistry` implementations (`JdbcLockRegistry`, `RedisLockRegistry`, `ZookeeperLockRegistry`) coordinate across every instance of a clustered application talking to the same shared backend, so that "only one instance at a time is doing X" can actually be guaranteed cluster-wide, not just process-wide.

## 2. Why & when

You reach for `LockRegistry` specifically when correctness depends on true mutual exclusion across a clustered, multi-instance application:

- **Multiple application instances could otherwise race on the same resource** — a poller-driven endpoint (card 0035) polling a shared external resource, where two instances polling simultaneously would both grab and process the same item, causing duplicate work — a distributed lock ensures only one instance's poll actually proceeds at a time for a given resource key.
- **An `Aggregator` (card 0025) or `Delayer` (card 0028) release decision needs to happen exactly once**, even though multiple clustered instances share the same persistent `MessageStore` (card 0046) and could all simultaneously notice a group is ready to release — a lock around the release decision ensures only one instance actually performs it.
- **You want the same mutual-exclusion guarantee `synchronized`/`ReentrantLock` gives within one process, but need it to hold across process boundaries** — `LockRegistry` is deliberately API-compatible with `java.util.concurrent.locks.Lock`, so code already familiar with single-JVM locking patterns translates directly.

## 3. Core concept

Think of `LockRegistry` like a physical key to a shared warehouse that multiple branch offices (application instances) all need access to, versus each branch office having its own separate, disconnected lock on its own local supply closet (`ReentrantLock`, per-JVM). A local lock only prevents two people *within the same branch* from entering its closet simultaneously; it does nothing to stop a completely different branch office from walking into the *same shared warehouse* at the same moment. A single, shared physical key — one that only one branch can be holding at any given time, enforced by something external to any individual branch — is what a `LockRegistry` provides.

```java
@Bean
public LockRegistry lockRegistry(DataSource dataSource) {
    return new JdbcLockRegistry(new DefaultLockRepository(dataSource));
}

public void processSharedResource(String resourceId) {
    Lock lock = lockRegistry.obtain("resource-" + resourceId);
    if (lock.tryLock()) {
        try {
            // only ONE instance across the entire cluster is inside this block for this resourceId
            doWork(resourceId);
        } finally {
            lock.unlock();
        }
    } else {
        System.out.println("Another instance already holds the lock for " + resourceId);
    }
}
```

The `Lock` interface itself is the exact same `java.util.concurrent.locks.Lock` type used for local, single-JVM locking — `LockRegistry` is what makes `tryLock()`/`unlock()` on that interface actually coordinate across a shared backend, rather than a plain in-JVM `ReentrantLock`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple application instances each obtain a lock by the same key from a shared LockRegistry backend; only one instance's tryLock succeeds at a time, coordinated across process boundaries" >
  <rect x="20" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance A</text>

  <rect x="20" y="130" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="154" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance B</text>

  <line x1="160" y1="40" x2="240" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#lr1)"/>
  <line x1="160" y1="150" x2="240" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#lr1)"/>

  <rect x="250" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="325" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">shared backend</text>
  <text x="325" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(DB / Redis / ZK)</text>

  <text x="500" y="60" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">A: tryLock() SUCCEEDS</text>
  <text x="500" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">B: tryLock() FAILS (A holds it)</text>

  <defs>
    <marker id="lr1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The shared backend, not either instance's own memory, is what enforces that only one instance can hold a given lock key at a time.

## 5. Runnable example

The scenario: a shared resource that multiple clustered instances might otherwise process concurrently, starting with demonstrating the race condition a purely local lock fails to prevent across instances, then a shared-backend simulation actually preventing it, and finally lock contention with a timeout.

### Level 1 — Basic

```java
// LocalLockFailsAcrossInstancesDemo.java
import java.util.concurrent.locks.ReentrantLock;
import java.util.concurrent.*;

public class LocalLockFailsAcrossInstancesDemo {
    public static void main(String[] args) throws InterruptedException {
        // TWO SEPARATE ReentrantLock instances, standing in for two SEPARATE application instances —
        // each JVM/process would have its OWN local lock, with no coordination between them at all
        ReentrantLock instanceALock = new ReentrantLock();
        ReentrantLock instanceBLock = new ReentrantLock();

        ExecutorService pool = Executors.newFixedThreadPool(2);
        CountDownLatch bothStarted = new CountDownLatch(2);

        Runnable instanceAWork = () -> {
            instanceALock.lock(); // only prevents OTHER THREADS WITHIN instance A — does NOT see instance B at all
            try {
                bothStarted.countDown();
                System.out.println("[Instance A] entered critical section (its OWN local lock says it's safe)");
                Thread.sleep(200);
            } catch (InterruptedException ignored) {} finally { instanceALock.unlock(); }
        };
        Runnable instanceBWork = () -> {
            instanceBLock.lock(); // a COMPLETELY DIFFERENT lock object — no relationship to instanceALock whatsoever
            try {
                bothStarted.countDown();
                System.out.println("[Instance B] ALSO entered critical section (its OWN, DIFFERENT local lock)");
                Thread.sleep(200);
            } catch (InterruptedException ignored) {} finally { instanceBLock.unlock(); }
        };

        pool.submit(instanceAWork);
        pool.submit(instanceBWork);
        bothStarted.await();
        System.out.println("BOTH instances were inside the 'critical section' SIMULTANEOUSLY — local locks provided NO cross-instance protection");
        pool.shutdown();
    }
}
```

How to run: `java LocalLockFailsAcrossInstancesDemo.java`. Expected output: both `[Instance A]` and `[Instance B]` "entered critical section" lines print essentially together, followed by `BOTH instances were inside the 'critical section' SIMULTANEOUSLY...` — exactly the race condition a plain per-process `ReentrantLock` cannot prevent, since each instance's lock has no idea the other instance (or its lock) even exists.

### Level 2 — Intermediate

A shared backend (simulated here with a `ConcurrentHashMap` standing in for a database row or Redis key that both "instances" actually contend on) correctly prevents the same race — only one instance's `tryLock()` succeeds at a time for a given key, exactly as `LockRegistry` provides in a real clustered application.

```java
// SharedBackendLockDemo.java
import java.util.concurrent.*;

public class SharedBackendLockDemo {
    // stands in for a LockRegistry's shared backend (a DB table, a Redis key) — genuinely SHARED, not per-instance
    static ConcurrentHashMap<String, String> sharedLockBackend = new ConcurrentHashMap<>();

    static boolean tryLock(String key, String holderId) {
        return sharedLockBackend.putIfAbsent(key, holderId) == null; // atomic: succeeds only if unheld
    }

    static void unlock(String key, String holderId) {
        sharedLockBackend.remove(key, holderId);
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(2);
        CountDownLatch done = new CountDownLatch(2);
        String lockKey = "resource-42";

        Runnable instanceAWork = () -> {
            if (tryLock(lockKey, "instance-A")) {
                try {
                    System.out.println("[Instance A] acquired the SHARED lock, processing resource-42");
                    Thread.sleep(300);
                } catch (InterruptedException ignored) {} finally { unlock(lockKey, "instance-A"); done.countDown(); }
            } else {
                System.out.println("[Instance A] could NOT acquire lock — another instance holds it");
                done.countDown();
            }
        };
        Runnable instanceBWork = () -> {
            try { Thread.sleep(50); } catch (InterruptedException ignored) {} // slight delay so A gets there first
            if (tryLock(lockKey, "instance-B")) {
                System.out.println("[Instance B] acquired the SHARED lock, processing resource-42");
            } else {
                System.out.println("[Instance B] could NOT acquire lock — Instance A already holds it");
            }
            done.countDown();
        };

        pool.submit(instanceAWork);
        pool.submit(instanceBWork);
        done.await();
        pool.shutdown();
    }
}
```

How to run: `java SharedBackendLockDemo.java`. Expected output: `[Instance A] acquired the SHARED lock, processing resource-42` then `[Instance B] could NOT acquire lock — Instance A already holds it` — because both "instances" contend on the *same* shared backend entry (rather than each having its own separate lock, as in Level 1), true mutual exclusion is achieved: only one instance is ever actually processing `resource-42` at a time.

### Level 3 — Advanced

A `tryLock` with a timeout, waiting a bounded amount of time for a currently-held lock to become available rather than failing immediately — mirroring `Lock.tryLock(timeout, unit)`'s real behavior, useful when a brief wait is acceptable but indefinite blocking isn't.

```java
// TimedLockContentionDemo.java
import java.util.concurrent.*;
import java.util.concurrent.locks.*;

public class TimedLockContentionDemo {
    // a ReentrantLock here stands in for the Lock instance LockRegistry.obtain(key) would return,
    // since the real cross-process coordination requires an actual shared backend to demonstrate live
    static ReentrantLock sharedResourceLock = new ReentrantLock();

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(2);
        CountDownLatch done = new CountDownLatch(2);

        pool.submit(() -> {
            sharedResourceLock.lock();
            try {
                System.out.println("[Instance A] holding lock for 500ms");
                Thread.sleep(500);
            } catch (InterruptedException ignored) {} finally {
                sharedResourceLock.unlock();
                System.out.println("[Instance A] released lock");
                done.countDown();
            }
        });

        pool.submit(() -> {
            try { Thread.sleep(50); } catch (InterruptedException ignored) {} // let A grab it first
            System.out.println("[Instance B] attempting tryLock with 1000ms timeout...");
            try {
                boolean acquired = sharedResourceLock.tryLock(1000, TimeUnit.MILLISECONDS);
                if (acquired) {
                    System.out.println("[Instance B] acquired lock AFTER waiting for A to release it");
                    sharedResourceLock.unlock();
                } else {
                    System.out.println("[Instance B] gave up after 1000ms timeout");
                }
            } catch (InterruptedException ignored) {} finally { done.countDown(); }
        });

        done.await();
        pool.shutdown();
    }
}
```

How to run: `java TimedLockContentionDemo.java`. Expected output: `[Instance A] holding lock for 500ms`, `[Instance B] attempting tryLock with 1000ms timeout...`, then (after ~450ms of actual waiting) `[Instance A] released lock` followed immediately by `[Instance B] acquired lock AFTER waiting for A to release it` — Instance B's bounded wait (1000ms) was long enough to actually receive the lock once Instance A released it (after ~500ms total), rather than either failing immediately or blocking forever.

## 6. Walkthrough

Tracing `TimedLockContentionDemo` in execution order:

1. The first pooled task immediately calls `sharedResourceLock.lock()`, acquiring it (nothing else holds it yet), prints confirmation, and sleeps 500ms to simulate doing real work while holding the lock.
2. The second pooled task sleeps 50ms first (ensuring the first task gets there first for a deterministic demonstration), then calls `sharedResourceLock.tryLock(1000, TimeUnit.MILLISECONDS)` — this is a *bounded* wait, unlike a plain `lock()` call, which would block indefinitely.
3. Because the first task is still holding the lock at this point (it's only about 50ms into its 500ms hold), `tryLock` cannot acquire immediately — it begins waiting, up to its 1000ms budget, for the lock to become available.
4. At roughly the 500ms mark, the first task's `finally` block runs, calling `sharedResourceLock.unlock()` and printing its release confirmation — this is the moment the lock actually becomes available for another holder.
5. The second task's still-waiting `tryLock` call — which had been blocked since roughly the 50ms mark, well within its 1000ms budget — immediately notices the lock is now free and acquires it, returning `true`.
6. Because the second task's timeout (1000ms) comfortably exceeded the actual wait required (roughly 450ms, from when it started waiting to when the first task released the lock), it successfully acquired the lock rather than timing out — had the first task instead held the lock for, say, 1200ms, the second task's `tryLock` would have returned `false` after its own 1000ms budget elapsed, exactly the bounded-wait behavior a distributed lock's `tryLock(timeout, unit)` provides for coordinating clustered instances without any risk of indefinite blocking.

```
t=0ms:    Instance A: lock() SUCCEEDS, holds for 500ms
t=50ms:   Instance B: tryLock(1000ms) called -> lock is HELD -> B starts WAITING
t=500ms:  Instance A: unlock() -> lock becomes available
t=500ms:  Instance B: tryLock() SUCCEEDS (had waited ~450ms, well within its 1000ms budget)
```

## 7. Gotchas & takeaways

> A held distributed lock whose owning instance crashes (or is killed) before calling `unlock()` can leave the lock permanently held, blocking every other instance from ever acquiring it again — unless the specific `LockRegistry` implementation supports lock expiration/leasing (many do, via a TTL on the underlying backend entry). Always verify whether the chosen `LockRegistry` implementation handles this "lock holder died without releasing" scenario, and prefer implementations (or explicit lease configuration) that do, especially for any lock guarding a resource that must never become permanently stuck.

- `LockRegistry` provides named, mutual-exclusion locks that coordinate correctly across multiple application instances via a shared external backend (JDBC, Redis, Zookeeper), unlike a plain per-process `ReentrantLock`, which only coordinates threads within one JVM.
- Use it whenever correctness depends on true cluster-wide mutual exclusion — a shared external resource, a coordinated release decision on a shared `MessageStore` (card 0046), or any "only one instance should do this at a time" requirement.
- `LockRegistry`'s obtained `Lock` objects implement the standard `java.util.concurrent.locks.Lock` interface, so `tryLock()`, `tryLock(timeout, unit)`, and `unlock()` behave familiarly, just coordinated across process boundaries via the shared backend.
- A bounded `tryLock(timeout, unit)` call is generally preferable to an unbounded `lock()` call in distributed settings, since it avoids indefinite blocking if the lock is held longer than expected or never released at all.
- Verify the chosen `LockRegistry` implementation's behavior when a lock holder crashes without releasing — implementations with lock expiration/leasing avoid a crashed instance permanently blocking every other instance from ever acquiring that lock again.
