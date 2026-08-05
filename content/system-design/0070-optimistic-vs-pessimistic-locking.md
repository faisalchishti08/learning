---
card: system-design
gi: 70
slug: optimistic-vs-pessimistic-locking
title: Optimistic vs pessimistic locking
---

## 1. What it is

**Pessimistic locking** prevents a conflict before it can happen, by having a transaction acquire an exclusive lock on a row before modifying it, forcing any other transaction that wants the same row to wait. **Optimistic locking** allows conflicts to happen and instead detects them at commit time, using a version number (or timestamp) on the row: if the version has changed since you read it, your update is rejected and you must retry.

## 2. Why & when

The two approaches make opposite bets about how often conflicts actually happen. Pessimistic locking pays an upfront cost (every writer waits for a lock) on every single update, whether or not a real conflict would have occurred — worthwhile when conflicts are frequent, because it avoids wasted retry work. Optimistic locking pays no upfront cost at all and only pays a retry cost on the rare occasion a real conflict happens — worthwhile when conflicts are rare, which is the common case for most web applications (two users editing the exact same row at the exact same instant is unusual).

## 3. Core concept

**Pessimistic locking, step by step:** a transaction reads a row `SELECT ... FOR UPDATE`, which acquires a lock on it immediately. Any other transaction trying to read (with `FOR UPDATE`) or write that same row must wait until the first transaction commits or rolls back and releases the lock. This guarantees no other transaction can interleave a conflicting change, at the cost of that other transaction simply waiting.

**Optimistic locking, step by step:** a row carries a `version` column. A transaction reads the row (including its current version), makes changes, and on write issues an update like `UPDATE ... SET version = version + 1 WHERE id = ? AND version = ?` (the *old* version it read). If another transaction already updated the row and bumped its version, this `WHERE` clause matches zero rows, the update silently fails to apply, and the application must detect this (checking the affected row count) and retry — typically by re-reading the row and reapplying its intended change.

**Why optimistic locking needs an explicit retry loop:** unlike pessimistic locking, where the database itself handles waiting, an optimistic-locking failure is just a normal update affecting zero rows — the application must check for that and decide what to do, usually re-fetch and retry.

## 4. Diagram

```
PESSIMISTIC (row locked immediately, second transaction WAITS):
  T1: SELECT ... FOR UPDATE (acquires lock)
  T2: SELECT ... FOR UPDATE                 <- BLOCKS, waits for T1
  T1: UPDATE ..., COMMIT (releases lock)
  T2: (now proceeds, lock acquired, sees T1's committed change)

OPTIMISTIC (no lock; conflict detected at write time via version number):
  T1: reads row, version=1
  T2: reads row, version=1                  <- both read the SAME version, no waiting
  T1: UPDATE ... WHERE version=1 -> succeeds, row is now version=2
  T2: UPDATE ... WHERE version=1 -> matches ZERO rows (version is now 2) -> T2 must RETRY
```
*Caption: pessimistic locking makes the second writer wait; optimistic locking lets both proceed, then rejects and retries whichever one loses the race.*

## 5. Runnable example

**Level 1 — Basic.** Pessimistic locking: a simple mutex simulates `SELECT ... FOR UPDATE`, forcing a second thread to wait.

**Level 2 — Optimistic locking.** A version-checked update that fails when the version has moved, requiring a retry.

**Level 3 — Retry loop.** A full optimistic-locking retry loop that keeps re-reading and reapplying an update until it succeeds.

```java
// OptimisticVsPessimisticLocking.java
import java.util.concurrent.locks.ReentrantLock;

public class OptimisticVsPessimisticLocking {

    // Level 1: pessimistic locking - an explicit lock, mirroring SELECT ... FOR UPDATE.
    static final ReentrantLock rowLock = new ReentrantLock();
    static int pessimisticBalance = 100;

    static void pessimisticWithdraw(int amount) {
        rowLock.lock(); // other callers BLOCK here until this one finishes
        try {
            pessimisticBalance -= amount;
        } finally {
            rowLock.unlock();
        }
    }

    // Level 2 & 3: optimistic locking - a version column, checked on every update.
    static class VersionedRow {
        int balance;
        int version;
        VersionedRow(int balance, int version) { this.balance = balance; this.version = version; }
    }
    static VersionedRow row = new VersionedRow(100, 1);

    // Models: UPDATE accounts SET balance=?, version=version+1 WHERE id=? AND version=?
    static boolean tryUpdate(int expectedVersion, int newBalance) {
        if (row.version != expectedVersion) {
            return false; // WHERE clause matched zero rows: someone else updated it first
        }
        row.balance = newBalance;
        row.version++;
        return true;
    }

    static void optimisticWithdrawWithRetry(int amount) {
        while (true) {
            int readVersion = row.version;
            int readBalance = row.balance;
            int newBalance = readBalance - amount;

            boolean applied = tryUpdate(readVersion, newBalance);
            if (applied) {
                System.out.println("  optimistic withdraw of " + amount + " succeeded on attempt with version " + readVersion);
                return;
            }
            System.out.println("  optimistic withdraw of " + amount + " CONFLICTED at version " + readVersion + " - retrying");
            // loop again: re-read the (now newer) version and balance, and retry
        }
    }

    public static void main(String[] args) {
        System.out.println("pessimistic: starting balance = " + pessimisticBalance);
        pessimisticWithdraw(30);
        System.out.println("pessimistic: after one withdraw = " + pessimisticBalance);

        System.out.println("optimistic: starting balance = " + row.balance + ", version = " + row.version);

        // Simulate a conflict: another transaction updates the row BETWEEN our read and our write.
        int ourReadVersion = row.version; // we "read" the row here
        row.balance -= 10; // another transaction commits first
        row.version++;
        System.out.println("(another transaction committed first: balance=" + row.balance + ", version=" + row.version + ")");

        boolean firstAttempt = tryUpdate(ourReadVersion, row.balance - 20); // uses our STALE version
        System.out.println("our update using stale version " + ourReadVersion + " succeeded? " + firstAttempt);

        optimisticWithdrawWithRetry(20); // the correct way: retries automatically on conflict
        System.out.println("optimistic: final balance = " + row.balance + ", version = " + row.version);
    }
}
```

**How to run:** save as `OptimisticVsPessimisticLocking.java`, then run `java OptimisticVsPessimisticLocking.java`.

## 6. Walkthrough

1. `pessimisticWithdraw(30)` acquires `rowLock` before touching `pessimisticBalance`; any concurrent caller would block on `rowLock.lock()` until this one calls `unlock()` — mirroring `SELECT ... FOR UPDATE` forcing a second transaction to wait.
2. `ourReadVersion` captures `row.version` (`1`) as if a transaction had just read the row.
3. `row.balance -= 10; row.version++` simulates a *different* transaction committing a change first, moving the row to `version=2`.
4. `tryUpdate(ourReadVersion, ...)` uses the now-stale `ourReadVersion=1`, but `row.version` is now `2` — the check `row.version != expectedVersion` is true, so the update is rejected and `firstAttempt` is `false`, exactly like an `UPDATE ... WHERE version=1` matching zero rows in the database.
5. `optimisticWithdrawWithRetry(20)` shows the correct pattern: it re-reads the current version and balance on every loop iteration, so its first attempt uses the *current* version (`2`), succeeds immediately, and prints the success message without ever hitting a conflict itself — because the retry loop always reads fresh state.

## 7. Gotchas & takeaways

> Gotcha: optimistic locking without a retry loop is a bug waiting to happen — the failed update quietly does nothing (zero rows affected) unless the application explicitly checks the affected-row count and retries; forgetting that check means a user's change can silently vanish.

- Pessimistic locking guarantees no wasted work but makes every writer to a contended row wait, even when most attempts would not have actually conflicted.
- Optimistic locking does no waiting at all and scales better under low contention, but requires the application to detect and retry conflicts explicitly.
- Related concepts: [Isolation levels (read-committed, repeatable-read, serializable)](0069-isolation-levels-read-committed-repeatable-read-serializable.md) (the underlying guarantees these locking strategies build on), [ACID properties](0068-acid-properties.md) (the transactional foundation both strategies operate within).
