---
card: system-design
gi: 69
slug: isolation-levels-read-committed-repeatable-read-serializable
title: "Isolation levels (read-committed, repeatable-read, serializable)"
---

## 1. What it is

An **isolation level** is a setting that controls how much of one transaction's in-progress work another concurrent transaction is allowed to see. **Read-committed** only ever shows other transactions' fully committed data. **Repeatable-read** additionally guarantees that if you read the same row twice within one transaction, you see the same value both times. **Serializable** is the strictest level, guaranteeing that concurrently running transactions behave as if they ran one at a time, in some order.

## 2. Why & when

Perfect isolation (serializable) is the easiest to reason about but the most expensive, because it can force transactions to wait on each other or retry when they conflict. Weaker isolation levels allow more concurrency and higher throughput, but permit specific categories of anomalies that your application must be prepared for. Choose the weakest level that your specific logic can safely tolerate — most applications default to read-committed, and reach for stronger levels only for the specific operations that need it (like the bank transfer example that motivates ACID).

## 3. Core concept

**The anomaly read-committed prevents — dirty reads:** without read-committed, a transaction could read another transaction's uncommitted change, which might later be rolled back — meaning you read data that, in the end, never actually existed. Read-committed guarantees you never see uncommitted writes from other transactions.

**The anomaly read-committed still allows — non-repeatable reads:** under read-committed, if you read a row, then another transaction commits a change to that same row, then you read it again *within your same transaction*, you get a different value the second time — the same query gives two different answers in one transaction.

**The anomaly repeatable-read fixes — but a gap it still allows, phantom reads:** repeatable-read guarantees the exact rows you already read stay the same for the rest of your transaction. But a *new* row matching your filter, inserted by another transaction and committed, can still appear if you re-run the same range query — a "phantom" row that was not there the first time.

**Serializable — the strongest guarantee:** the database ensures the outcome of running transactions concurrently is identical to some possible order of running them one at a time. Achieving this typically means the database detects conflicts and forces one of the conflicting transactions to abort and retry, rather than allowing an anomaly to occur.

## 4. Diagram

```
READ-COMMITTED (allows a non-repeatable read):
  T1: SELECT balance FROM accounts WHERE id=1   -> reads 100
  T2:                                                COMMIT UPDATE balance=90 WHERE id=1
  T1: SELECT balance FROM accounts WHERE id=1   -> reads 90   (DIFFERENT answer, same transaction)

REPEATABLE-READ (fixes that, but allows a phantom row):
  T1: SELECT * FROM orders WHERE total > 100    -> returns 3 rows
  T2:                                                COMMIT INSERT INTO orders (total) VALUES (150)
  T1: SELECT * FROM orders WHERE total > 100    -> returns 4 rows   (a PHANTOM appeared)

SERIALIZABLE:
  T1 and T2 conflict -> database forces one to ABORT and retry,
  so the final result is equivalent to running T1 then T2, or T2 then T1 - never interleaved incorrectly
```
*Caption: each stronger isolation level closes one specific gap the level below it allows, at the cost of more waiting or more forced retries.*

## 5. Runnable example

**Level 1 — Basic.** Simulate a non-repeatable read under read-committed: the same query returns different values within one "transaction."

**Level 2 — Repeatable-read.** The same scenario, but the transaction takes a snapshot at its start and reads consistently from it, avoiding the non-repeatable read.

**Level 3 — Phantom read.** Show that even the snapshot approach cannot prevent a new row (a phantom) from appearing on a range query.

```java
// IsolationLevels.java
import java.util.*;

public class IsolationLevels {

    static final Map<Integer, Integer> accounts = new HashMap<>(); // id -> balance
    static final List<Integer> orderTotals = new ArrayList<>();

    // Level 1: READ-COMMITTED - always reads the current committed state, live.
    static int readCommittedBalance(int id) {
        return accounts.get(id); // always the latest committed value
    }

    // Level 2: REPEATABLE-READ - reads are pinned to a snapshot taken at transaction start.
    static class Snapshot {
        final Map<Integer, Integer> pinnedAccounts;
        final List<Integer> pinnedOrderTotals;
        Snapshot() {
            pinnedAccounts = new HashMap<>(accounts); // copy taken once, at "transaction start"
            pinnedOrderTotals = new ArrayList<>(orderTotals);
        }
        int balance(int id) { return pinnedAccounts.get(id); }
        long countOrdersOver(int threshold) {
            // Level 3: even a snapshot of EXISTING rows cannot see rows inserted after it was taken,
            // but a query re-run against the LIVE table (not the snapshot) still sees the phantom.
            return pinnedOrderTotals.stream().filter(t -> t > threshold).count();
        }
    }

    public static void main(String[] args) {
        accounts.put(1, 100);

        // Level 1: read-committed sees T2's committed change mid-"transaction".
        System.out.println("READ-COMMITTED, first read: " + readCommittedBalance(1));
        accounts.put(1, 90); // another transaction (T2) commits a change
        System.out.println("READ-COMMITTED, second read (same transaction): " + readCommittedBalance(1)
            + "  <- non-repeatable read: different answer, same transaction");

        // Level 2: repeatable-read pins a snapshot at transaction start, avoiding that.
        accounts.put(1, 100); // reset for a clean comparison
        Snapshot t1 = new Snapshot(); // "transaction" T1 starts, takes its snapshot
        System.out.println("REPEATABLE-READ, first read: " + t1.balance(1));
        accounts.put(1, 90); // T2 commits a change to the LIVE table, not the snapshot
        System.out.println("REPEATABLE-READ, second read (same transaction): " + t1.balance(1)
            + "  <- same answer both times: snapshot is pinned");

        // Level 3: phantom read - a NEW row still appears on a range query, even under repeatable-read.
        orderTotals.addAll(List.of(50, 120, 200)); // 2 orders already over 100
        Snapshot t1b = new Snapshot();
        System.out.println("REPEATABLE-READ, orders > 100 (snapshot): " + t1b.countOrdersOver(100));
        orderTotals.add(150); // T2 commits a NEW order, over the threshold
        System.out.println("live table now has a phantom row: orders > 100 (re-querying LIVE table) = "
            + orderTotals.stream().filter(t -> t > 100).count()
            + "  <- a real repeatable-read transaction querying the live table again would see this new row");
    }
}
```

**How to run:** save as `IsolationLevels.java`, then run `java IsolationLevels.java`.

## 6. Walkthrough

1. `readCommittedBalance(1)` is called before and after `accounts.put(1, 90)`; because it always reads the live map directly, the two calls return `100` then `90` — a non-repeatable read, the exact anomaly read-committed allows.
2. `Snapshot t1 = new Snapshot()` copies `accounts` into `pinnedAccounts` once, at creation — modeling the snapshot a repeatable-read transaction takes at its start.
3. `accounts.put(1, 90)` changes the live map, but `t1.balance(1)` reads from `pinnedAccounts`, which was never touched — both calls to `t1.balance(1)` return `100`, demonstrating repeatable-read closes the non-repeatable-read gap.
4. `t1b.countOrdersOver(100)` counts against `pinnedOrderTotals`, a snapshot taken before the new order was added, returning `2`.
5. After `orderTotals.add(150)` commits a new matching row to the live table, re-querying the *live* `orderTotals` list directly (not the snapshot) shows `3` — this models a real repeatable-read transaction re-running the same range query and seeing a phantom row that was not part of its original snapshot, since repeatable-read pins existing rows but does not fully lock out new ones the way serializable does.

## 7. Gotchas & takeaways

> Gotcha: "repeatable-read" sounds like it should mean "nothing can change," but it specifically only guarantees existing rows you already read stay stable — it does not, on its own, prevent new matching rows (phantoms) from appearing on a re-run range query; only serializable closes that gap completely.

- Each isolation level trades concurrency for a specific consistency guarantee: read-committed is fastest but allows the most anomalies; serializable allows none but can force transactions to abort and retry under contention.
- Most applications default to read-committed and only escalate to a stronger level for the specific operations where an anomaly would cause real harm.
- Related concepts: [ACID properties](0068-acid-properties.md) (isolation is one of the four ACID guarantees), [Optimistic vs pessimistic locking](0070-optimistic-vs-pessimistic-locking.md) (practical techniques for handling the conflicts stronger isolation levels detect).
