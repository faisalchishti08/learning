---
card: system-design
gi: 166
slug: optimistic-vs-pessimistic-concurrency
title: Optimistic vs pessimistic concurrency
---

## 1. What it is

**Pessimistic concurrency control** locks a piece of data before touching it, blocking every other thread or process from reading or modifying it until the lock is released — it assumes conflicts are likely, so it prevents them up front. **Optimistic concurrency control** does not lock anything; it lets multiple writers proceed freely, but checks at write time whether the data changed since it was read, and rejects (or retries) the write if it did — it assumes conflicts are rare, so it only handles them when they actually happen.

## 2. Why & when

Locking every read is safe but costs throughput: other threads must wait even when no conflict would actually have occurred. Optimistic concurrency avoids that waiting cost entirely for the common case, at the price of occasionally having to detect and retry a real conflict after the fact. Use pessimistic locking when conflicts are frequent and retries would be expensive or complex (e.g. transferring money between two accounts); use optimistic concurrency when conflicts are rare and most operations would otherwise wait needlessly for a lock they never actually needed (e.g. many users editing different fields of a large, shared record).

## 3. Core concept

- **Pessimistic — acquire a lock before reading/writing:** a `SELECT ... FOR UPDATE` in SQL, or an explicit mutex, blocks other transactions from touching the same row until the lock-holder commits or releases.
- **Optimistic — a version number (or timestamp) per record:** every read captures the current version; the write includes a check, `UPDATE ... WHERE id = ? AND version = ?`, which only succeeds if the version has not changed since the read.
- **Conflict detection, not conflict prevention:** optimistic concurrency lets the conflict happen (two writers both read version 5), then detects it at write time — only one write can match `version = 5` after the first writer's update bumps it to 6.
- **Retry on conflict:** when an optimistic write fails its version check, the usual response is to re-read the current data, reapply the intended change, and try the write again — not to give up outright.
- **Throughput vs. contention tradeoff:** pessimistic locking guarantees no wasted work but costs waiting time even without real contention; optimistic concurrency costs nothing when there is no real contention, but wastes the work of a failed write (and a retry) when contention actually occurs.

## 4. Diagram

```
   PESSIMISTIC:                              OPTIMISTIC:
   writer A: LOCK row -----.                 writer A: read row (version=5)
                            |                 writer B: read row (version=5)
   writer B: BLOCKED,       |                 writer A: write (WHERE version=5) -> OK, version becomes 6
             waiting...     |                 writer B: write (WHERE version=5) -> FAILS (version is now 6)
                            |                              |
   writer A: commit, UNLOCK-+                              v
                            |                 writer B: re-read (version=6), reapply change, retry write
   writer B: now proceeds
```
*Caption: pessimistic locking makes the second writer wait; optimistic concurrency lets both proceed and only makes the loser redo its work after the fact.*

## 5. Runnable example

**Level 1 — Basic.** Pessimistic locking: a mutex blocks a second thread until the first finishes.

**Level 2 — Optimistic concurrency with a version check.** A write only succeeds if the version has not changed since the read.

**Level 3 — Retry loop on optimistic conflict.** A failed write re-reads, reapplies the change, and tries again.

```java
// ConcurrencyControlDemo.java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class ConcurrencyControlDemo {

    // A shared record with an optimistic-concurrency version number.
    static class Record {
        volatile int value;
        volatile int version;
        Record(int value) { this.value = value; this.version = 1; }
    }

    // Level 2: an optimistic write - only succeeds if the version matches what was read.
    static synchronized boolean optimisticWrite(Record record, int expectedVersion, int newValue) {
        if (record.version != expectedVersion) {
            return false; // someone else updated it since we read - conflict detected
        }
        record.value = newValue;
        record.version++;
        return true;
    }

    // Level 3: retry the optimistic write until it succeeds, reapplying the intended change each time.
    static void optimisticIncrementWithRetry(Record record, int amount) {
        while (true) {
            int readVersion = record.version;
            int readValue = record.value;
            boolean ok = optimisticWrite(record, readVersion, readValue + amount);
            if (ok) {
                System.out.println(Thread.currentThread().getName() + ": succeeded, new value=" + record.value + ", new version=" + record.version);
                return;
            }
            System.out.println(Thread.currentThread().getName() + ": conflict detected (version changed), retrying...");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        // Level 1: pessimistic locking - a plain mutex, second thread waits.
        Object lock = new Object();
        AtomicInteger pessimisticCounter = new AtomicInteger(0);
        Runnable pessimisticTask = () -> {
            synchronized (lock) { // blocks any other thread trying to enter this block
                int before = pessimisticCounter.get();
                pessimisticCounter.set(before + 1);
            }
        };
        Thread p1 = new Thread(pessimisticTask, "pess-A");
        Thread p2 = new Thread(pessimisticTask, "pess-B");
        p1.start(); p2.start(); p1.join(); p2.join();
        System.out.println("pessimistic result (no lost updates, thanks to the lock): " + pessimisticCounter.get());

        // Level 2 & 3: optimistic concurrency - two threads increment the SAME record concurrently.
        Record record = new Record(0);
        Thread o1 = new Thread(() -> optimisticIncrementWithRetry(record, 1), "opt-A");
        Thread o2 = new Thread(() -> optimisticIncrementWithRetry(record, 1), "opt-B");
        o1.start(); o2.start(); o1.join(); o2.join();
        System.out.println("optimistic result (no lost updates, thanks to retry-on-conflict): " + record.value);
    }
}
```

**How to run:** save as `ConcurrencyControlDemo.java`, then run `java ConcurrencyControlDemo.java`.

## 6. Walkthrough

1. `p1` and `p2` both run `pessimisticTask`; whichever thread enters the `synchronized (lock)` block first holds it exclusively, and the other blocks at that same line until the first thread's block finishes — so `pessimisticCounter` is always read and updated by exactly one thread at a time, guaranteeing the final value is 2 with no lost update.
2. `optimisticIncrementWithRetry` first reads `record.version` and `record.value` into local variables, *outside* any lock — both `o1` and `o2` can do this concurrently, and may both read the same starting `version`.
3. Each thread then calls `optimisticWrite` with the version it read; this method is `synchronized`, so only one thread's check-and-update runs at a time, but the *read* that happened earlier was not protected — this is the essential difference from pessimistic locking.
4. Whichever thread's `optimisticWrite` call runs first finds `record.version == expectedVersion` still true, so it updates `record.value` and increments `record.version`, returning `true`.
5. The second thread's call to `optimisticWrite` now finds `record.version != expectedVersion` (it changed under it), so it returns `false`; `optimisticIncrementWithRetry`'s `while` loop catches this, prints the conflict message, and loops back to re-read the *current* value and version, then retries the write — this time succeeding, since no one else is changing the record concurrently anymore, giving a final `record.value` of 2, matching the pessimistic result but achieved via detect-and-retry rather than blocking.

## 7. Gotchas & takeaways

> Gotcha: optimistic concurrency's retry loop can spin indefinitely under very high contention (many writers repeatedly colliding on the same record), potentially doing more wasted work than a plain lock would have — if a specific record is a genuine hotspot with frequent conflicts, pessimistic locking (or a queue serializing writes to it) is often the better choice, not optimistic retries.

- Pessimistic locking prevents conflicts by blocking; optimistic concurrency allows them to happen and detects them afterward via a version check.
- The version-check-then-retry pattern is the core mechanism of optimistic concurrency, and it only works correctly if every writer actually checks the version before committing.
- Choose based on contention: frequent conflicts favor locking; rare conflicts favor the lower-overhead optimistic approach.
- Related concepts: [Distributed locks (Redis Redlock / ZooKeeper)](0167-distributed-locks-redis-redlock-zookeeper.md) (pessimistic locking extended across multiple machines), [Idempotency keys for safe retries](0168-idempotency-keys-for-safe-retries.md) (a related but distinct mechanism for safely retrying operations), [Strong consistency](0103-strong-consistency.md) (the guarantee a correctly-implemented version check relies on).
