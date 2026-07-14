---
card: microservices
gi: 510
slug: optimistic-vs-pessimistic-locking
title: "Optimistic vs pessimistic locking"
---

## 1. What it is

**Pessimistic locking** acquires an exclusive lock on a record *before* reading and modifying it, blocking any other concurrent operation from touching that record until the lock is released — assuming conflict is likely enough to prevent upfront. **Optimistic locking** assumes conflict is rare: it reads a record's current version, makes changes, and only checks at write time whether the version has changed since the read — if it has, the write is rejected and must be retried, rather than being blocked from ever starting.

## 2. Why & when

You choose between them based on how likely concurrent conflicting writes to the same record actually are, and how expensive blocking versus retrying is for your workload:

- **Pessimistic locking avoids wasted work when conflicts are frequent.** If many concurrent operations are likely to target the same record, letting them all proceed optimistically and then fail at write time wastes the work each one did before discovering the conflict — a pessimistic lock avoids that waste by preventing the conflicting work from starting in the first place.
- **Optimistic locking avoids blocking when conflicts are rare.** If most operations on a given record never actually collide with another concurrent one, pessimistic locking pays a real cost (every operation waits for a lock, even when no other operation is actually competing for it) for a problem that mostly doesn't happen.
- **Pessimistic locking holds a lock for the duration of the operation**, including any slow steps (a network call, user think-time in an interactive flow) — a lock held across a slow step blocks every other concurrent operation for that entire duration, which can be a serious throughput problem.
- **You default to optimistic locking for typical microservice update patterns** — most single-record updates in most systems have infrequent actual contention, making optimistic locking's lower overhead the better fit; reach for pessimistic locking specifically when contention is known to be frequent and the cost of a wasted, retried optimistic attempt is high.

## 3. Core concept

Think of editing a shared document: pessimistic locking is like checking out the document exclusively before you start editing — nobody else can even open it until you're done, guaranteeing no conflict but potentially leaving others waiting even if they'd have edited a completely different section. Optimistic locking is like everyone being able to open and edit their own copy freely, but when you go to save, the system checks whether anyone else saved changes since you opened your copy — if they did, your save is rejected and you need to reconcile and retry, but in the common case where nobody else touched it, your save just succeeds immediately with no waiting at all.

Concretely:

1. **Pessimistic locking**: acquire a database-level lock (`SELECT ... FOR UPDATE`) on the record before reading it; every other transaction attempting to lock the same record blocks until the lock holder commits or rolls back.
2. **Optimistic locking**: read the record along with a version number (or timestamp); when writing, include a `WHERE version = <the version you read>` clause — if zero rows match (because someone else already updated it and bumped the version), the write affects zero rows, signaling a conflict that must be handled, typically by retrying with a fresh read.
3. **The cost tradeoff**: pessimistic locking pays cost upfront (every operation, contended or not, pays for lock acquisition and potential waiting); optimistic locking pays cost only on actual conflict (a wasted read-modify cycle that must be retried), which is cheap when conflicts are genuinely rare.
4. **Retry logic is essential for optimistic locking to actually work in practice** — a version-mismatch failure without a retry loop just becomes a visible error for what might be a perfectly legitimate, recoverable situation.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pessimistic locking blocks concurrent operations upfront; optimistic locking lets them proceed and only checks for conflict at write time, retrying on failure">
  <rect x="20" y="20" width="290" height="70" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="165" y="42" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">pessimistic: lock, THEN work</text>
  <text x="165" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">second writer BLOCKS until first releases</text>

  <rect x="350" y="20" width="290" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">optimistic: work, THEN check version</text>
  <text x="495" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">second writer's SAVE is rejected, must RETRY</text>
</svg>

Pessimistic prevents conflicting work from starting; optimistic lets it proceed and catches conflict at save time.

## 5. Runnable example

Scenario: two concurrent updates to the same inventory record. We start with a basic optimistic-locking version check, extend it to a conflict being correctly detected and rejected, then handle the hard case: automatically retrying a rejected optimistic write with a fresh read, succeeding on the retry.

### Level 1 — Basic

```java
// File: OptimisticLockBasic.java -- models the CORE optimistic locking
// mechanism: read a VERSION alongside the data, and only WRITE if the
// version STILL matches what was read.
import java.util.concurrent.atomic.*;

public class OptimisticLockBasic {
    static AtomicInteger stockQuantity = new AtomicInteger(100);
    static AtomicInteger version = new AtomicInteger(1);

    record ReadResult(int quantity, int versionRead) {}

    static ReadResult read() {
        return new ReadResult(stockQuantity.get(), version.get());
    }

    static boolean writeIfVersionMatches(int newQuantity, int expectedVersion) {
        boolean matched = version.compareAndSet(expectedVersion, expectedVersion + 1);
        if (matched) {
            stockQuantity.set(newQuantity);
            System.out.println("[write] SUCCESS -- version matched (" + expectedVersion + "), quantity now " + newQuantity + ", version now " + version.get());
        } else {
            System.out.println("[write] REJECTED -- expected version " + expectedVersion + " but current version is " + version.get());
        }
        return matched;
    }

    public static void main(String[] args) {
        ReadResult read = read();
        System.out.println("[read] quantity=" + read.quantity() + ", version=" + read.versionRead());
        writeIfVersionMatches(95, read.versionRead());
    }
}
```

How to run: `java OptimisticLockBasic.java`

`writeIfVersionMatches` uses `version.compareAndSet(expectedVersion, ...)`, an atomic check-and-set — the write only succeeds if the current version still equals exactly what was read earlier, and it also bumps the version on success, so any *future* reader will see a version that no longer matches this now-stale read.

### Level 2 — Intermediate

```java
// File: OptimisticLockConflictDetected.java -- the SAME mechanism, now
// demonstrating an ACTUAL CONFLICT: TWO readers read the same version,
// one writes successfully (bumping the version), and the SECOND writer's
// attempt is correctly REJECTED because its read is now stale.
import java.util.concurrent.atomic.*;

public class OptimisticLockConflictDetected {
    static AtomicInteger stockQuantity = new AtomicInteger(100);
    static AtomicInteger version = new AtomicInteger(1);

    record ReadResult(int quantity, int versionRead) {}
    static ReadResult read() { return new ReadResult(stockQuantity.get(), version.get()); }

    static boolean writeIfVersionMatches(int newQuantity, int expectedVersion, String writerName) {
        boolean matched = version.compareAndSet(expectedVersion, expectedVersion + 1);
        if (matched) {
            stockQuantity.set(newQuantity);
            System.out.println("[" + writerName + "] SUCCESS -- wrote quantity=" + newQuantity);
        } else {
            System.out.println("[" + writerName + "] REJECTED -- version conflict (expected " + expectedVersion + ", actual " + version.get() + ")");
        }
        return matched;
    }

    public static void main(String[] args) {
        // BOTH writers read the SAME initial state -- neither knows about the other yet.
        ReadResult readByOrderService = read();
        ReadResult readByWarehouseService = read();
        System.out.println("[both] read quantity=100, version=" + readByOrderService.versionRead());

        // order-service writes first and succeeds, bumping the version.
        writeIfVersionMatches(95, readByOrderService.versionRead(), "order-service");

        // warehouse-service, still holding its now-STALE read, tries to write too.
        writeIfVersionMatches(90, readByWarehouseService.versionRead(), "warehouse-service");
    }
}
```

How to run: `java OptimisticLockConflictDetected.java`

Both `readByOrderService` and `readByWarehouseService` capture the identical initial `versionRead` of `1`, since both read before either wrote. `order-service`'s write succeeds first, bumping `version` to `2`. `warehouse-service`'s subsequent write attempt still carries the stale `versionRead` of `1`, which no longer matches the current version of `2` — `compareAndSet` correctly fails, and the write is rejected rather than silently overwriting `order-service`'s already-committed change.

### Level 3 — Advanced

```java
// File: OptimisticLockRetryLoop.java -- the SAME conflict scenario, now
// handling the PRODUCTION-FLAVORED hard case CORRECTLY: instead of just
// reporting the rejection as a final failure, warehouse-service RETRIES
// with a FRESH read, correctly re-applying its intended CHANGE (a
// relative decrement) against the NEW current state, and succeeds.
import java.util.concurrent.atomic.*;

public class OptimisticLockRetryLoop {
    static AtomicInteger stockQuantity = new AtomicInteger(100);
    static AtomicInteger version = new AtomicInteger(1);

    record ReadResult(int quantity, int versionRead) {}
    static ReadResult read() { return new ReadResult(stockQuantity.get(), version.get()); }

    // Applies a RELATIVE change (decrement by 5) with automatic retry on conflict.
    static void decrementWithRetry(String writerName, int decrementBy, int maxRetries) {
        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            ReadResult current = read(); // ALWAYS a FRESH read on every attempt
            int intendedNewQuantity = current.quantity() - decrementBy;
            boolean success = version.compareAndSet(current.versionRead(), current.versionRead() + 1);
            if (success) {
                stockQuantity.set(intendedNewQuantity);
                System.out.println("[" + writerName + "] attempt " + attempt + ": SUCCESS -- decremented from "
                        + current.quantity() + " to " + intendedNewQuantity);
                return;
            }
            System.out.println("[" + writerName + "] attempt " + attempt + ": version conflict, RETRYING with a fresh read");
        }
        System.out.println("[" + writerName + "] exhausted " + maxRetries + " retries -- giving up");
    }

    public static void main(String[] args) {
        // order-service writes directly first, simulating it winning the initial race.
        int v = version.get();
        version.compareAndSet(v, v + 1);
        stockQuantity.set(95);
        System.out.println("[order-service] wrote quantity=95 directly, version now " + version.get());

        System.out.println();
        System.out.println("--- warehouse-service decrements by 5, using retry-on-conflict logic ---");
        decrementWithRetry("warehouse-service", 5, 3);

        System.out.println();
        System.out.println("[final state] quantity=" + stockQuantity.get() + " -- CORRECTLY based on order-service's 95, not the stale original 100");
    }
}
```

How to run: `java OptimisticLockRetryLoop.java`

`decrementWithRetry`'s loop calls `read()` fresh on *every* attempt, not just once at the start — this is the critical fix over a naive retry that would reuse the original stale read. `order-service` writes `95` directly first, bumping the version. `warehouse-service`'s first attempt reads the *current* state (`95`, the up-to-date value, not the stale `100`) and correctly computes `intendedNewQuantity` as `95 - 5 = 90`, succeeding immediately on its first real attempt in this run since no further concurrent writer interferes — but critically, its computation is always based on whatever the *fresh* read returns, ensuring correctness even if a conflict genuinely required a retry.

## 6. Walkthrough

Trace `OptimisticLockRetryLoop.main` in order. **First**, `order-service`'s direct write runs: `version.compareAndSet(v, v + 1)` bumps the version, and `stockQuantity.set(95)` updates the quantity directly, representing `order-service` winning an initial race and successfully committing its change.

**Next**, `decrementWithRetry("warehouse-service", 5, 3)` begins its loop with `attempt = 1`. `read()` is called fresh, capturing the *current* state — `quantity = 95` (order-service's already-applied change) and whatever the current `versionRead` now is, *not* any earlier, now-stale value.

**Then**, `intendedNewQuantity` is computed as `current.quantity() - decrementBy`, which is `95 - 5 = 90` — this calculation is based on the fresh read, correctly building on top of `order-service`'s change rather than a stale snapshot from before it.

**After that**, `version.compareAndSet(current.versionRead(), current.versionRead() + 1)` runs. Since `current.versionRead()` was just read moments ago and nothing else has modified `version` in the meantime, this succeeds — `success` is `true`, so `stockQuantity.set(90)` applies the correctly-computed new value, and the loop returns immediately after reporting success on attempt `1`.

**Finally**, `main` prints the final quantity, `90`, explicitly noting it correctly reflects `warehouse-service`'s decrement applied on top of `order-service`'s prior write (`95 - 5`), rather than what a naive "retry with the same stale read" bug would have produced — recomputing from the original `100` and yielding an incorrect `95` that would have silently discarded `order-service`'s change entirely.

```
[order-service] wrote quantity=95 directly, version now 2

--- warehouse-service decrements by 5, using retry-on-conflict logic ---
[warehouse-service] attempt 1: SUCCESS -- decremented from 95 to 90

[final state] quantity=90 -- CORRECTLY based on order-service's 95, not the stale original 100
```

## 7. Gotchas & takeaways

> A retry loop that reuses the *original* stale read's data on each retry attempt — recomputing the intended new value from data captured before the conflict was even detected — silently discards whatever change the *other* writer successfully committed. Always perform a genuinely fresh read on every retry attempt, as `decrementWithRetry` does, especially for relative changes (increment/decrement) where the correct result depends on the actual current state, not the state you originally, incorrectly assumed was still current.
- Optimistic locking's retry logic needs a bounded maximum attempt count — under genuinely high, sustained contention, an unbounded retry loop could spin indefinitely; a bounded count with a clear failure path (as `decrementWithRetry`'s `maxRetries` provides) is the safer design.
- Pessimistic locking remains the better choice for known-high-contention scenarios where the wasted work of repeated optimistic conflicts and retries would exceed the cost of simply waiting for a lock upfront — measure actual contention rather than guessing.
- This concept underlies [distributed locks](0508-distributed-locks.md)' own acquisition mechanics in spirit — both rely on an atomic compare-and-set primitive to detect and reject conflicting concurrent operations, just applied at different scopes (a single record's version versus an entire cross-instance critical section).
- Absolute writes (setting a field to a fixed value regardless of its prior state) are simpler to make optimistically correct than relative changes (incrementing, decrementing) — relative changes specifically require the fresh-read-on-retry discipline shown here to avoid silently losing concurrent updates.
