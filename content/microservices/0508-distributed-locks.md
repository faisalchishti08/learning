---
card: microservices
gi: 508
slug: distributed-locks
title: "Distributed locks"
---

## 1. What it is

A **distributed lock** is a mechanism that lets multiple separate processes — different instances of a service, potentially on different machines — coordinate exclusive access to a shared resource, the way a normal in-process lock (`synchronized`, a `ReentrantLock`) coordinates threads within a single JVM. Because the "threads" here are actually separate processes that could each crash, become slow, or lose network connectivity independently, a distributed lock needs mechanisms an in-process lock never has to worry about — most importantly, a lease with a timeout, so a crashed holder doesn't hold the lock forever.

## 2. Why & when

You reach for a distributed lock specifically when multiple instances of a horizontally-scaled service need to coordinate around a shared resource that must not be touched by more than one instance at a time:

- **A scheduled job that should run exactly once, even with multiple service instances all capable of running it, needs coordination.** Without a lock, every instance's scheduler fires at the same time and the job runs N times instead of once — a distributed lock lets exactly one instance "win" and run it.
- **A resource that isn't safe for concurrent modification by multiple instances** (a specific file, an external system with no transactional guarantees of its own) needs the same mutual-exclusion guarantee a local lock provides, but across process boundaries.
- **The lease/timeout mechanism is what makes this safe in a distributed setting**, where a plain "acquire and never automatically release" lock would leave the resource permanently locked if the holding instance crashed or lost network connectivity before explicitly releasing it.
- **You reach for this specifically when the coordination genuinely needs cross-instance mutual exclusion** — many problems that look like they need a distributed lock are actually better solved with idempotency, a database's own transactional guarantees, or [leader election](0509-leader-election.md) for coordination that's ongoing rather than a one-off critical section.

## 3. Core concept

Think of a single physical key to a shared storage room, but with a twist: if whoever's holding the key doesn't return it within a set time (say, they got locked in an elevator), the key automatically becomes available to the next person after that timeout — rather than the room staying inaccessible forever because one person disappeared mid-task. That timeout is the critical difference from a simple lock: it protects against the holder failing to release the lock, whether due to a crash, a network partition, or simply taking too long.

Concretely:

1. **Acquire**: an instance attempts to acquire the lock, typically by setting a key in a shared store (Redis, a database row) with a value uniquely identifying itself, using an atomic "set if not already present" operation.
2. **Lease/expiry**: the lock is acquired with a timeout (a TTL) — if the holding instance doesn't explicitly release it or extend the lease before the timeout, the lock automatically becomes available again.
3. **Critical section**: while holding the lock, the instance performs the coordinated work — running the scheduled job, modifying the shared resource.
4. **Release**: the instance explicitly releases the lock when done, ideally verifying it's still the actual holder before releasing (to avoid accidentally releasing a lock some *other* instance now holds, if its own lease had already expired).
5. **Extend (optional)**: for work that might take longer than a conservative initial timeout, the holding instance can periodically extend its lease while still actively working, rather than needing to guess a single long timeout upfront.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple instances attempt to acquire a distributed lock; only one succeeds and performs the critical section, releasing the lock afterward or letting it expire" >
  <rect x="20" y="20" width="140" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance A</text>

  <rect x="20" y="80" width="140" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="107" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance B</text>

  <rect x="20" y="140" width="140" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="167" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance C</text>

  <rect x="260" y="80" width="150" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="335" y="107" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">shared lock (TTL)</text>

  <line x1="160" y1="42" x2="260" y2="95" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="160" y1="102" x2="260" y2="102" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="160" y1="162" x2="260" y2="110" stroke="#8b949e" stroke-dasharray="3,2"/>

  <rect x="460" y="80" width="170" height="45" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="545" y="107" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">only B runs the job</text>

  <line x1="410" y1="102" x2="460" y2="102" stroke="#f0883e" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/></marker>
  </defs>
</svg>

Three instances race for the lock; only one acquires it and performs the critical section, while the lease's TTL protects against a crashed holder locking it forever.

## 5. Runnable example

Scenario: multiple instances racing for a distributed lock to run a scheduled job exactly once. We start with a basic single-acquisition lock, extend it to multiple instances racing concurrently for it, then handle the hard case: a lock holder crashing without releasing, which must be recovered via TTL expiry rather than permanently blocking every future acquisition attempt.

### Level 1 — Basic

```java
// File: DistributedLockBasic.java -- models a BASIC distributed lock:
// acquire via an ATOMIC "set if absent" operation, with a TTL, then release.
import java.util.concurrent.*;

public class DistributedLockBasic {
    static ConcurrentHashMap<String, String> sharedLockStore = new ConcurrentHashMap<>(); // simulates Redis/etc.

    static boolean tryAcquire(String lockKey, String holderId) {
        String existing = sharedLockStore.putIfAbsent(lockKey, holderId); // ATOMIC set-if-absent
        boolean acquired = existing == null;
        System.out.println("[" + holderId + "] tryAcquire('" + lockKey + "'): " + (acquired ? "ACQUIRED" : "already held by " + existing));
        return acquired;
    }

    static void release(String lockKey, String holderId) {
        boolean removed = sharedLockStore.remove(lockKey, holderId); // only remove if WE still hold it
        System.out.println("[" + holderId + "] released '" + lockKey + "': " + removed);
    }

    public static void main(String[] args) {
        if (tryAcquire("daily-report-job", "instance-A")) {
            System.out.println("[instance-A] running the scheduled job...");
            release("daily-report-job", "instance-A");
        }
    }
}
```

How to run: `java DistributedLockBasic.java`

`putIfAbsent` is the atomic core of lock acquisition — it either sets the value and returns `null` (meaning this caller just acquired the lock) or returns the existing value (meaning someone else already holds it), with no window between "check" and "set" where a race could occur. `release` uses the two-argument `remove(key, value)` form, which only removes the entry if it still matches the given value — ensuring an instance can only release a lock it actually still holds.

### Level 2 — Intermediate

```java
// File: DistributedLockConcurrentRace.java -- the SAME lock, now with
// MULTIPLE instances genuinely racing to acquire it CONCURRENTLY --
// exactly ONE must win, and the job must run EXACTLY ONCE.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class DistributedLockConcurrentRace {
    static ConcurrentHashMap<String, String> sharedLockStore = new ConcurrentHashMap<>();
    static AtomicInteger jobRunCount = new AtomicInteger(0);

    static boolean tryAcquire(String lockKey, String holderId) {
        return sharedLockStore.putIfAbsent(lockKey, holderId) == null;
    }

    static void release(String lockKey, String holderId) {
        sharedLockStore.remove(lockKey, holderId);
    }

    static void attemptJobRun(String holderId) {
        String lockKey = "daily-report-job";
        if (tryAcquire(lockKey, holderId)) {
            jobRunCount.incrementAndGet();
            System.out.println("[" + holderId + "] WON the race -- running the job now");
            release(lockKey, holderId);
        } else {
            System.out.println("[" + holderId + "] lost the race -- job already claimed by another instance");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        int instanceCount = 5;
        ExecutorService pool = Executors.newFixedThreadPool(instanceCount);
        CountDownLatch latch = new CountDownLatch(instanceCount);

        for (int i = 1; i <= instanceCount; i++) {
            String holderId = "instance-" + i;
            pool.submit(() -> { attemptJobRun(holderId); latch.countDown(); });
        }
        latch.await();
        pool.shutdown();

        System.out.println("[result] " + instanceCount + " instances raced for the lock, job ran " + jobRunCount.get() + " time(s)");
    }
}
```

How to run: `java DistributedLockConcurrentRace.java`

All five instances call `attemptJobRun` at roughly the same time, each racing to `tryAcquire` the same `lockKey`. Because `putIfAbsent` is atomic on the underlying `ConcurrentHashMap`, exactly one instance's call returns `true` regardless of how many threads race simultaneously — `jobRunCount` ends up at exactly `1` no matter which specific instance happens to win.

### Level 3 — Advanced

```java
// File: DistributedLockTtlRecovery.java -- the SAME lock, now handling
// the PRODUCTION-FLAVORED hard case: the lock HOLDER CRASHES without
// releasing (simulating a real process crash mid-critical-section). A
// lock with NO expiry would stay locked FOREVER. This models a TTL-based
// lease: the lock automatically becomes acquirable again once its lease
// expires, WITHOUT the crashed holder ever explicitly releasing it.
import java.util.concurrent.*;

public class DistributedLockTtlRecovery {
    record LockEntry(String holderId, long expiresAtMs) {}
    static ConcurrentHashMap<String, LockEntry> sharedLockStore = new ConcurrentHashMap<>();

    static boolean tryAcquire(String lockKey, String holderId, long leaseMs) {
        long now = System.currentTimeMillis();
        LockEntry newEntry = new LockEntry(holderId, now + leaseMs);

        // Atomic "acquire if absent OR if the existing lease has expired".
        LockEntry[] result = new LockEntry[1];
        sharedLockStore.compute(lockKey, (key, existing) -> {
            if (existing == null || now >= existing.expiresAtMs()) {
                result[0] = newEntry;
                return newEntry;
            }
            result[0] = existing;
            return existing;
        });

        boolean acquired = result[0] == newEntry;
        System.out.println("[" + holderId + "] tryAcquire: " + (acquired ? "ACQUIRED (lease " + leaseMs + "ms)" : "still held by " + result[0].holderId()));
        return acquired;
    }

    public static void main(String[] args) throws InterruptedException {
        String lockKey = "daily-report-job";

        System.out.println("--- instance-A acquires the lock with a short 100ms lease ---");
        tryAcquire(lockKey, "instance-A", 100);

        System.out.println();
        System.out.println("[incident] instance-A CRASHES mid-job -- NEVER calls release()");

        System.out.println();
        System.out.println("--- instance-B tries IMMEDIATELY, lease hasn't expired yet ---");
        boolean immediateAttempt = tryAcquire(lockKey, "instance-B", 100);
        System.out.println("[result] instance-B acquired immediately: " + immediateAttempt + " (correctly blocked, lease still active)");

        System.out.println();
        System.out.println("--- waiting for the crashed lease to expire ---");
        Thread.sleep(150);

        System.out.println();
        System.out.println("--- instance-B tries AGAIN, after the lease has expired ---");
        boolean afterExpiryAttempt = tryAcquire(lockKey, "instance-B", 100);
        System.out.println("[result] instance-B acquired after expiry: " + afterExpiryAttempt + " (recovered WITHOUT instance-A ever releasing)");
    }
}
```

How to run: `java DistributedLockTtlRecovery.java`

`tryAcquire`'s `compute` lambda checks `existing == null || now >= existing.expiresAtMs()` — acquisition succeeds either when no lock exists at all, or when an existing lock's lease has expired, *regardless of whether its holder ever explicitly released it*. `instance-A` "crashes" (the code simply never calls a release method for it, modeling the crash), and `instance-B`'s first attempt correctly fails since the 100ms lease hasn't elapsed yet — but after sleeping past that lease duration, `instance-B`'s second attempt succeeds, because the lease's own expiry, not any explicit release call, is what makes the lock available again.

## 6. Walkthrough

Trace `DistributedLockTtlRecovery.main` in order. **First**, `tryAcquire(lockKey, "instance-A", 100)` runs while `sharedLockStore` has no entry for `lockKey` — inside `compute`, `existing` is `null`, so the acquisition condition is `true`; a new `LockEntry` is stored with `expiresAtMs` set to `100ms` from now, and `instance-A` is reported as having acquired it.

**Next**, the simulated crash happens — no code runs any release logic for `instance-A`'s lock at all, leaving the entry sitting in `sharedLockStore` exactly as it was, with its expiry time fixed at whatever it was calculated to be at acquisition time.

**Then**, `instance-B`'s first attempt calls `tryAcquire` immediately afterward. Inside `compute`, `existing` is `instance-A`'s `LockEntry`, and `now >= existing.expiresAtMs()` is `false`, since only a negligible amount of time has passed — the acquisition condition is `false`, so the existing entry is returned unchanged, and `instance-B`'s attempt correctly fails, reporting the lock as still held by `instance-A`.

**After that**, `Thread.sleep(150)` runs, advancing real elapsed time to `150ms` since `instance-A`'s original acquisition — now past the `100ms` lease duration.

**Finally**, `instance-B`'s second attempt calls `tryAcquire` again. This time, inside `compute`, `now >= existing.expiresAtMs()` is `true`, since real time has now exceeded the lease's expiry — the acquisition condition is `true` despite `existing` being non-null, so a brand-new `LockEntry` for `instance-B` replaces the stale one, and the acquisition succeeds. This recovery happened purely because of the lease's own time-based expiry — `instance-A`, having crashed, never participated in this recovery at all.

```
--- instance-A acquires the lock with a short 100ms lease ---
[instance-A] tryAcquire: ACQUIRED (lease 100ms)

[incident] instance-A CRASHES mid-job -- NEVER calls release()

--- instance-B tries IMMEDIATELY, lease hasn't expired yet ---
[instance-B] tryAcquire: still held by instance-A
[result] instance-B acquired immediately: false (correctly blocked, lease still active)

--- waiting for the crashed lease to expire ---

--- instance-B tries AGAIN, after the lease has expired ---
[instance-B] tryAcquire: ACQUIRED (lease 100ms)
[result] instance-B acquired after expiry: true (recovered WITHOUT instance-A ever releasing)
```

## 7. Gotchas & takeaways

> A distributed lock with no lease/TTL at all — one that only becomes available via an explicit release call — turns any holder crash into a permanent deadlock, since nothing else can ever acquire the lock again. The TTL is not an optional nicety; it's the mechanism that makes a distributed lock survive the reality that distributed processes genuinely do crash.
- Setting the right lease duration is a real tradeoff: too short, and a slow-but-still-working holder might have its lock expire and get "stolen" out from under it mid-operation; too long, and a genuine crash leaves the resource unavailable for that entire duration before recovery.
- For work that might legitimately take longer than a conservative initial lease, extend the lease periodically while still actively working, rather than either guessing an excessively long initial timeout or risking premature expiry.
- Distributed locks solve one-off mutual exclusion for a critical section; for ongoing coordination about which instance should perform a role over an extended period, [leader election](0509-leader-election.md) is usually the better-fitting pattern.
- Before reaching for a distributed lock, consider whether [idempotency keys](0507-idempotency-keys.md) or a database's own transactional guarantees could solve the actual underlying problem more simply — a distributed lock adds real complexity and failure modes of its own, worth reaching for only when genuine cross-instance mutual exclusion is truly required.
