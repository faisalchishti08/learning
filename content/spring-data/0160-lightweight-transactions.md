---
card: spring-data
gi: 160
slug: lightweight-transactions
title: "Lightweight transactions"
---

## 1. What it is

A **lightweight transaction** (LWT) is Cassandra's mechanism for a conditional, linearizable write — `IF NOT EXISTS` or `IF <column> = <value>` — using the Paxos consensus protocol to guarantee the condition is checked and the write applied as one atomic, strongly-consistent step, even under concurrent attempts. This is Cassandra's answer to the same "detect a lost update" problem the earlier optimistic-locking (`@Version`) card solved for MongoDB, but implemented very differently.

```java
Statement<?> statement = QueryBuilder.insertInto("orders")
    .value("order_id", literal(orderId))
    .value("status", literal("PENDING"))
    .ifNotExists() // LWT: only inserts if no row with this order_id already exists
    .build();

ResultSet result = cqlOperations.execute(statement);
boolean applied = result.wasApplied();
```

## 2. Why & when

Cassandra's normal writes are deliberately "last write wins," with no built-in check against concurrent conflicting writes — this is what makes ordinary writes fast and always available, but it means two concurrent writes to the same row can silently overwrite each other with no error, no warning, and no way to know which one "won" except by timestamp. Lightweight transactions exist specifically for the narrow set of operations that genuinely need a conditional guarantee despite that trade-off — at a real cost: LWTs are meaningfully slower than ordinary writes, because Paxos consensus requires multiple round trips among replicas.

Reach for a lightweight transaction when:

- You need "insert this row only if it doesn't already exist" — a uniqueness constraint Cassandra can't otherwise enforce, since ordinary writes have no concept of "reject if already present."
- You need "update this row only if it currently has this specific value" — the same lost-update-prevention need the `@Version` card addressed for MongoDB, but expressed as a direct conditional check rather than a version counter.
- The operation is genuinely rare relative to your overall write volume — LWTs don't scale the way ordinary Cassandra writes do, so reaching for them on every write in a high-throughput table would undermine the reason to use Cassandra in the first place.

## 3. Core concept

```
 INSERT INTO orders (order_id, status) VALUES ('1', 'PENDING') IF NOT EXISTS;

 Two CONCURRENT attempts to insert order_id='1':
   Attempt A: IF NOT EXISTS -> TRUE (no existing row) -> Paxos coordinates -> A's write APPLIED
   Attempt B: IF NOT EXISTS -> FALSE (A's row now exists) -> B's write REJECTED, [applied]=false

 UPDATE orders SET status = 'SHIPPED' WHERE order_id = '1' IF status = 'PENDING';
   -- only applies if the CURRENT status is exactly 'PENDING' at the moment of the check
```

Paxos consensus among the replicas ensures the condition-check-and-write happens as one atomic step, even when multiple clients attempt it at the exact same moment — exactly the guarantee ordinary Cassandra writes don't provide.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two concurrent IF NOT EXISTS inserts race; Paxos ensures only one succeeds and the other is rejected with applied=false">
  <rect x="20" y="20" width="260" height="45" rx="8" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="150" y="47" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">Attempt A: INSERT ... IF NOT EXISTS</text>

  <rect x="360" y="20" width="260" height="45" rx="8" fill="#f8514922" stroke="#f85149" stroke-width="1.5"/>
  <text x="490" y="47" fill="#f85149" font-size="9.5" text-anchor="middle" font-family="sans-serif">Attempt B: INSERT ... IF NOT EXISTS</text>

  <rect x="150" y="100" width="340" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="122" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Paxos consensus -- only ONE attempt wins</text>

  <line x1="150" y1="65" x2="280" y2="95" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>
  <line x1="490" y1="65" x2="360" y2="95" stroke="#f85149" stroke-width="1.5" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Paxos consensus resolves the race deterministically — exactly one of two simultaneous conditional writes is applied.

## 5. Runnable example

The scenario: reserving unique order ids and safely updating order status, evolving from a basic `IF NOT EXISTS` uniqueness check, to a concurrent-race demonstration showing exactly one of two simultaneous attempts wins, to a conditional `IF status = ...` update preventing a lost update — mirroring the optimistic-locking card's problem, solved Cassandra's way.

### Level 1 — Basic

Model `IF NOT EXISTS`: an insert that only applies if no row with that key already exists.

```java
import java.util.*;

public class LwtLevel1 {
    public static void main(String[] args) {
        CassandraTable table = new CassandraTable();

        boolean firstInsert = table.insertIfNotExists("order-1", "PENDING");
        System.out.println("First insert of order-1: applied=" + firstInsert);

        boolean secondInsert = table.insertIfNotExists("order-1", "CANCELLED"); // same key, already exists
        System.out.println("Second insert of order-1 (already exists): applied=" + secondInsert);

        System.out.println("Final status: " + table.select("order-1")); // still PENDING -- second insert did NOT apply
    }
}

class CassandraTable {
    private final Map<String, String> rows = new HashMap<>();

    // Mirrors: INSERT INTO orders (order_id, status) VALUES (?, ?) IF NOT EXISTS
    boolean insertIfNotExists(String key, String status) {
        if (rows.containsKey(key)) return false; // condition FAILED -- row already exists, write REJECTED
        rows.put(key, status);
        return true;
    }

    String select(String key) { return rows.get(key); }
}
```

How to run: `java LwtLevel1.java`

`insertIfNotExists` mirrors `INSERT ... IF NOT EXISTS`: the first call succeeds because no row exists yet, but the second call — targeting the same key, which now exists — is rejected, returning `false` (`applied=false` in real CQL's response). Critically, order-1's status remains `"PENDING"`, the first write's value, unaffected by the rejected second attempt.

### Level 2 — Intermediate

Simulate two truly concurrent attempts racing for the same key, demonstrating that exactly one wins — the core guarantee Paxos provides.

```java
import java.util.*;
import java.util.concurrent.atomic.*;

public class LwtLevel2 {
    public static void main(String[] args) throws InterruptedException {
        CassandraTable table = new CassandraTable();
        AtomicBoolean resultA = new AtomicBoolean();
        AtomicBoolean resultB = new AtomicBoolean();

        // Two threads racing to insert the SAME key concurrently -- only ONE can win, guaranteed by Paxos in real Cassandra.
        Thread threadA = new Thread(() -> resultA.set(table.insertIfNotExists("order-1", "reserved-by-A")));
        Thread threadB = new Thread(() -> resultB.set(table.insertIfNotExists("order-1", "reserved-by-B")));

        threadA.start(); threadA.join(); // run sequentially in this demo for deterministic, reproducible output --
        threadB.start(); threadB.join(); // real Paxos handles GENUINE concurrency; the OUTCOME shape is what matters here

        System.out.println("Thread A insert applied: " + resultA.get());
        System.out.println("Thread B insert applied: " + resultB.get());
        System.out.println("Exactly one thread won: " + (resultA.get() ^ resultB.get()));
        System.out.println("Final owner: " + table.select("order-1"));
    }
}

class CassandraTable {
    private final Map<String, String> rows = new HashMap<>();
    synchronized boolean insertIfNotExists(String key, String status) { // synchronized -- stands in for Paxos's atomicity
        if (rows.containsKey(key)) return false;
        rows.put(key, status);
        return true;
    }
    String select(String key) { return rows.get(key); }
}
```

How to run: `java LwtLevel2.java`

`insertIfNotExists` is marked `synchronized`, standing in for the atomicity Paxos consensus provides in real Cassandra — no matter how the two threads' timing actually interleaves, exactly one of them observes `rows.containsKey(key)` as `false` and successfully inserts, while the other observes it as `true` (once the first has completed) and is rejected. `resultA.get() ^ resultB.get()` (logical XOR) confirms exactly one — never both, never neither — succeeded.

### Level 3 — Advanced

Model a conditional update, `IF status = 'PENDING'`, preventing a lost update — the same problem the earlier `@Version` optimistic-locking card solved for MongoDB, now solved with Cassandra's native conditional-write mechanism instead of an application-managed version counter.

```java
import java.util.*;

public class LwtLevel3 {
    public static void main(String[] args) {
        CassandraTable table = new CassandraTable();
        table.insertIfNotExists("order-1", "PENDING");

        // Two "processes" both try to transition the SAME order, but only if it's STILL PENDING when they act.
        boolean shipAttempt = table.updateIfStatusEquals("order-1", "PENDING", "SHIPPED");
        System.out.println("Attempt to ship (expecting PENDING): applied=" + shipAttempt + ", status now=" + table.select("order-1"));

        // A SECOND attempt, now that status has already moved to SHIPPED -- its expected precondition no longer holds.
        boolean cancelAttempt = table.updateIfStatusEquals("order-1", "PENDING", "CANCELLED");
        System.out.println("Attempt to cancel (expecting PENDING, but it's now SHIPPED): applied=" + cancelAttempt
            + ", status now=" + table.select("order-1"));
    }
}

class CassandraTable {
    private final Map<String, String> rows = new HashMap<>();
    boolean insertIfNotExists(String key, String status) {
        if (rows.containsKey(key)) return false;
        rows.put(key, status);
        return true;
    }
    String select(String key) { return rows.get(key); }

    // Mirrors: UPDATE orders SET status = ? WHERE order_id = ? IF status = ?
    synchronized boolean updateIfStatusEquals(String key, String expectedCurrentStatus, String newStatus) {
        String currentStatus = rows.get(key);
        if (!expectedCurrentStatus.equals(currentStatus)) return false; // precondition FAILED -- no write happens
        rows.put(key, newStatus);
        return true;
    }
}
```

How to run: `java LwtLevel3.java`

`updateIfStatusEquals` mirrors `UPDATE orders SET status = ? WHERE order_id = ? IF status = ?`: the ship attempt succeeds because the order's status is indeed `"PENDING"` at that moment, transitioning it to `"SHIPPED"`. The subsequent cancel attempt, which also expects `"PENDING"`, fails — the status has already moved to `"SHIPPED"` by the successful ship attempt — exactly preventing the cancel from silently overwriting a shipment that already happened, the same class of lost-update bug the MongoDB `@Version` card addressed, solved here through a direct conditional check rather than a version counter.

## 6. Walkthrough

Execution starts in `main` for Level 3. `table.insertIfNotExists("order-1", "PENDING")` establishes the initial row with status `"PENDING"`.

`table.updateIfStatusEquals("order-1", "PENDING", "SHIPPED")` is called first. Inside, `currentStatus` is read as `"PENDING"`, and `expectedCurrentStatus.equals(currentStatus)` checks `"PENDING".equals("PENDING")` — `true`. The condition holds, so `rows.put("order-1", "SHIPPED")` executes, and the method returns `true`. The order's status is now `"SHIPPED"`.

`table.updateIfStatusEquals("order-1", "PENDING", "CANCELLED")` is called second. This time `currentStatus` is read as `"SHIPPED"` (the value just written), and the check `"PENDING".equals("SHIPPED")` evaluates to `false` — the precondition fails, so the method returns `false` *without* modifying `rows` at all. The order's status remains `"SHIPPED"`, correctly rejecting the stale cancellation attempt.

```
Attempt to ship (expecting PENDING): applied=true, status now=SHIPPED
Attempt to cancel (expecting PENDING, but it's now SHIPPED): applied=false, status now=SHIPPED
```

In real Cassandra, both statements would be sent as CQL with an `IF status = 'PENDING'` clause, and the response includes an `[applied]` column indicating whether the condition held and the write actually happened — application code must always check this `[applied]` value explicitly, since (unlike a normal write) an LWT can silently *not* apply, and treating the call as successful without checking would reintroduce exactly the lost-update bug the LWT was meant to prevent.

## 7. Gotchas & takeaways

> Gotcha: an LWT's response always includes whether it was actually applied (`[applied]` in `cqlsh`, `resultSet.wasApplied()` in the driver) — application code that doesn't check this value and simply assumes the write succeeded reintroduces the exact lost-update problem the LWT exists to prevent. Always check `wasApplied()`.

> Gotcha: lightweight transactions are meaningfully more expensive than ordinary Cassandra writes — Paxos consensus requires multiple round trips among replicas (a "prepare" phase and an "accept" phase, roughly doubling the network round trips of a normal write) — reaching for LWTs on every write in a high-throughput table undermines much of the reason to choose Cassandra for that workload in the first place. Reserve them for genuinely conditional operations, not as a default write pattern.

- Lightweight transactions (`IF NOT EXISTS`, `IF <column> = <value>`) use Paxos consensus to guarantee a conditional check-and-write happens atomically, even under concurrent attempts — the guarantee Cassandra's ordinary "last write wins" writes don't provide.
- This solves the same class of lost-update problem the MongoDB `@Version` optimistic-locking card addressed, but through a direct conditional check rather than an application-managed version field.
- Every LWT response must be checked for whether it was actually applied — an LWT can fail its condition and simply not write, and ignoring that possibility reintroduces the exact bug the LWT is meant to prevent.
- LWTs are significantly more expensive than ordinary writes due to Paxos's extra consensus round trips — reserve them for genuinely conditional operations, not routine high-throughput writes.
