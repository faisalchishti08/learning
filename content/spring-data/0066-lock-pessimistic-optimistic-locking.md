---
card: spring-data
gi: 66
slug: lock-pessimistic-optimistic-locking
title: "@Lock (pessimistic/optimistic locking)"
---

## 1. What it is

`@Lock` on a repository method controls what concurrency-control strategy JPA applies when the query loads its rows: **optimistic locking** (via a `@Version` column, checked at commit time) assumes conflicts are rare and detects them after the fact; **pessimistic locking** (`PESSIMISTIC_READ`/`PESSIMISTIC_WRITE`, via a database-level row lock) assumes conflicts are likely and prevents them up front by blocking other transactions from touching the same row.

```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("SELECT o FROM Order o WHERE o.id = :id")
Optional<Order> findByIdForUpdate(@Param("id") Long id);
```

## 2. Why & when

The persistence context card explained that mutating a managed entity gets written automatically at commit — but said nothing about what happens if *two* transactions load and mutate the *same* row concurrently. `@Lock` is how you choose the concurrency strategy for a specific query: let both proceed and detect the conflict later (optimistic), or force one to wait for the other to finish (pessimistic).

Reach for one or the other specifically when:

- Conflicts are rare and you want the highest throughput — use optimistic locking (`@Version` field on the entity; no `@Lock` annotation even required, it's automatic), and handle the occasional `OptimisticLockException` by retrying.
- Conflicts are frequent enough that retry-on-failure would thrash, or the operation is a genuine "read this row, then update it based on what I read" sequence that must not be interleaved (e.g., decrementing inventory) — use `@Lock(PESSIMISTIC_WRITE)` to block concurrent writers on that row until your transaction finishes.
- You need to read a row and guarantee it won't change before you finish reading related data, without necessarily needing to write to it — `PESSIMISTIC_READ` blocks other writers but typically still allows other readers.

## 3. Core concept

```
 OPTIMISTIC (default, via @Version):
   Tx A: SELECT ... (version=1)      Tx B: SELECT ... (version=1)
   Tx A: UPDATE ... version=2 WHERE version=1   -- succeeds, 1 row affected
   Tx B: UPDATE ... version=2 WHERE version=1   -- 0 rows affected!
                                                 -- Spring throws OptimisticLockException

 PESSIMISTIC_WRITE (via @Lock):
   Tx A: SELECT ... FOR UPDATE   -- row LOCKED
   Tx B: SELECT ... FOR UPDATE   -- BLOCKS, waits for Tx A to commit/rollback
   Tx A: commits -> lock released
   Tx B: proceeds now, sees Tx A's committed data
```

Optimistic locking lets both transactions run and only fails the loser at commit time; pessimistic locking makes the second transaction wait its turn.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Optimistic locking detects conflicts at commit; pessimistic locking blocks the second transaction upfront">
  <text x="20" y="20" fill="#e6edf3" font-size="10" font-family="sans-serif">Optimistic</text>
  <rect x="20" y="30" width="140" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="90" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Tx A reads v1</text>
  <rect x="180" y="30" width="140" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="250" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Tx B reads v1</text>
  <rect x="340" y="30" width="140" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="410" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Tx A writes -&gt; v2 OK</text>
  <rect x="500" y="30" width="130" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="565" y="46" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Tx B writes -&gt;</text>
  <text x="565" y="58" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OptimisticLockException</text>

  <text x="20" y="110" fill="#e6edf3" font-size="10" font-family="sans-serif">Pessimistic</text>
  <rect x="20" y="120" width="140" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="90" y="142" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Tx A locks row</text>
  <rect x="180" y="120" width="140" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3" stroke-dasharray="4,3"/>
  <text x="250" y="142" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Tx B BLOCKS...</text>
  <rect x="340" y="120" width="140" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="410" y="142" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Tx A commits, unlocks</text>
  <rect x="500" y="120" width="130" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="565" y="142" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Tx B proceeds</text>
</svg>

Optimistic locking lets both transactions proceed and fails the loser at write time; pessimistic locking makes the second one wait instead.

## 5. Runnable example

The scenario: two concurrent updates to the same order's inventory count, evolving from a version-checked optimistic model that throws on conflict, to a retry loop around it, to a pessimistic-lock model that serializes access instead of failing.

### Level 1 — Basic

Model optimistic locking directly: an `UPDATE` conditioned on the version last read, failing loudly if another transaction already changed it.

```java
import java.util.*;

class OptimisticLockException extends RuntimeException {
    OptimisticLockException(String msg) { super(msg); }
}

class Order {
    long id; int stock; int version;
    Order(long id, int stock, int version) { this.id = id; this.stock = stock; this.version = version; }
}

class OrderRepository {
    private final Map<Long, Order> db;
    OrderRepository(Map<Long, Order> db) { this.db = db; }

    Order findById(long id) {
        Order stored = db.get(id);
        return new Order(stored.id, stored.stock, stored.version); // simulate a separate transaction's read
    }

    // UPDATE orders SET stock = ?, version = version + 1 WHERE id = ? AND version = ?
    void save(Order toSave) {
        Order stored = db.get(toSave.id);
        if (stored.version != toSave.version) {
            throw new OptimisticLockException("Row was modified by another transaction (version mismatch)");
        }
        stored.stock = toSave.stock;
        stored.version = toSave.version + 1; // version bumped on successful write
    }
}

public class LockLevel1 {
    public static void main(String[] args) {
        Map<Long, Order> db = new HashMap<>(Map.of(1L, new Order(1, 10, 0)));
        OrderRepository repo = new OrderRepository(db);

        Order txA = repo.findById(1L); // both "transactions" read version 0
        Order txB = repo.findById(1L);

        txA.stock -= 1; // Tx A decrements stock
        repo.save(txA);  // succeeds: version still 0 in db, matches txA's version 0
        System.out.println("Tx A saved. Stock now: " + db.get(1L).stock + ", version: " + db.get(1L).version);

        txB.stock -= 1; // Tx B ALSO decrements stock, from its own (now stale) read
        try {
            repo.save(txB); // fails: db version is now 1, but txB still thinks it's 0
        } catch (OptimisticLockException e) {
            System.out.println("Tx B failed: " + e.getMessage());
        }
    }
}
```

How to run: `java LockLevel1.java`

Tx A's save succeeds because the `version` it read (`0`) still matches what's in `db`. Tx B's save fails because `db`'s version was already bumped to `1` by Tx A's successful write — this is exactly the `WHERE ... AND version = ?` clause Hibernate generates for a `@Version`-annotated entity, and the zero-rows-affected result is what Spring Data translates into `OptimisticLockException`.

### Level 2 — Intermediate

Wrap the optimistic-locking call in a retry loop — the typical way application code handles the occasional conflict, by re-reading the current state and reapplying the change.

```java
import java.util.*;
import java.util.function.*;

class OptimisticLockException extends RuntimeException {
    OptimisticLockException(String msg) { super(msg); }
}

class Order {
    long id; int stock; int version;
    Order(long id, int stock, int version) { this.id = id; this.stock = stock; this.version = version; }
}

class OrderRepository {
    private final Map<Long, Order> db;
    OrderRepository(Map<Long, Order> db) { this.db = db; }
    Order findById(long id) {
        Order stored = db.get(id);
        return new Order(stored.id, stored.stock, stored.version);
    }
    void save(Order toSave) {
        Order stored = db.get(toSave.id);
        if (stored.version != toSave.version) throw new OptimisticLockException("version mismatch");
        stored.stock = toSave.stock;
        stored.version = toSave.version + 1;
    }
}

public class LockLevel2 {
    // Retries the read-modify-write cycle up to `maxAttempts` times on OptimisticLockException.
    static void decrementStockWithRetry(OrderRepository repo, long orderId, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                Order order = repo.findById(orderId); // fresh read each attempt
                order.stock -= 1;
                repo.save(order);
                System.out.println("Succeeded on attempt " + attempt);
                return;
            } catch (OptimisticLockException e) {
                System.out.println("Attempt " + attempt + " failed (" + e.getMessage() + "), retrying...");
            }
        }
        throw new RuntimeException("Failed after " + maxAttempts + " attempts");
    }

    public static void main(String[] args) {
        Map<Long, Order> db = new HashMap<>(Map.of(1L, new Order(1, 10, 0)));
        OrderRepository repo = new OrderRepository(db);

        // Simulate a "concurrent" write happening between Tx B's read and its save, on attempt 1 only.
        Order staleRead = repo.findById(1L);
        staleRead.stock -= 1;
        repo.save(staleRead); // version becomes 1 -- this represents another transaction winning first

        decrementStockWithRetry(repo, 1L, 3); // attempt 1 uses a fresh read, so it succeeds directly here
        System.out.println("Final stock: " + db.get(1L).stock + ", version: " + db.get(1L).version);
    }
}
```

How to run: `java LockLevel2.java`

`decrementStockWithRetry` re-reads the current version on *every* attempt, so it always saves against the latest state — a conflict only occurs if another write sneaks in *between* its own read and its own save, not against stale data from before the loop started. This is the standard pattern for handling `OptimisticLockException` in application code: retry with a fresh read, not with the original stale object.

### Level 3 — Advanced

Model pessimistic locking as an alternative: instead of retrying after a conflict, a second "transaction" blocks until the first releases the lock, guaranteeing no conflict ever occurs.

```java
import java.util.*;
import java.util.concurrent.locks.*;

class Order {
    long id; int stock;
    Order(long id, int stock) { this.id = id; this.stock = stock; }
}

class OrderRepository {
    private final Map<Long, Order> db;
    private final Map<Long, ReentrantLock> rowLocks = new HashMap<>();
    OrderRepository(Map<Long, Order> db) {
        this.db = db;
        for (Long id : db.keySet()) rowLocks.put(id, new ReentrantLock());
    }

    // @Lock(LockModeType.PESSIMISTIC_WRITE): acquires a real DB row lock (e.g. SELECT ... FOR UPDATE).
    Order findByIdForUpdate(long id) {
        rowLocks.get(id).lock(); // blocks here if another "transaction" holds it
        System.out.println(Thread.currentThread().getName() + ": acquired lock on order " + id);
        return db.get(id);
    }

    void saveAndUnlock(Order order) {
        db.put(order.id, order); // write is safe -- no other transaction could have touched this row
        rowLocks.get(order.id).unlock();
        System.out.println(Thread.currentThread().getName() + ": released lock on order " + order.id);
    }
}

public class LockLevel3 {
    public static void main(String[] args) throws InterruptedException {
        Map<Long, Order> db = new HashMap<>(Map.of(1L, new Order(1, 10)));
        OrderRepository repo = new OrderRepository(db);

        Runnable decrement = () -> {
            Order order = repo.findByIdForUpdate(1L); // blocks if locked by the other thread
            order.stock -= 1;
            try { Thread.sleep(50); } catch (InterruptedException ignored) {} // simulate work while holding the lock
            repo.saveAndUnlock(order);
        };

        Thread txA = new Thread(decrement, "TxA");
        Thread txB = new Thread(decrement, "TxB");
        txA.start();
        txB.start();
        txA.join();
        txB.join();

        System.out.println("Final stock (no conflicts possible): " + db.get(1L).stock);
    }
}
```

How to run: `java LockLevel3.java`

`TxA` and `TxB` both call `findByIdForUpdate(1L)`, but only one acquires `rowLocks.get(1L)` at a time — whichever thread loses the race prints "acquired lock" only after the winner calls `saveAndUnlock`, which releases it. Unlike Level 1/2's optimistic approach, there is no exception and no retry: the second transaction simply waits its turn, and the final stock is always correctly decremented by both, `10 - 1 - 1 = 8`.

## 6. Walkthrough

Execution starts in `main` for Level 3. Two threads, `TxA` and `TxB`, are started nearly simultaneously, each running the same `decrement` logic. Whichever thread's `findByIdForUpdate(1L)` call reaches `rowLocks.get(1L).lock()` first (say `TxA`) acquires the lock immediately and prints "TxA: acquired lock on order 1"; the other thread (`TxB`) blocks inside `.lock()`, unable to proceed.

`TxA` then decrements `order.stock` from 10 to 9, sleeps 50ms (standing in for whatever work a real transaction does while holding the row lock), and calls `saveAndUnlock`, which writes `9` back into `db` and releases the lock, printing "TxA: released lock on order 1".

The instant the lock is released, `TxB`'s blocked `.lock()` call returns, `TxB` prints "TxB: acquired lock on order 1", reads the *already-updated* `db.get(1L)` (stock now 9, since `db` is shared), decrements it to 8, sleeps, and saves — printing "TxB: released lock on order 1". Because `TxB` could only start after `TxA` fully finished, it never operates on stale data — no conflict is possible, and the final `db.get(1L).stock` is deterministically `8`.

```
TxA: lock -> read(10) -> stock=9 -> [sleep] -> save(9), unlock
                                                          |
TxB: [blocked...............................] -> lock -> read(9) -> stock=8 -> save(8), unlock
```

In a real Spring Data JPA repository, `@Lock(LockModeType.PESSIMISTIC_WRITE)` on `findByIdForUpdate` causes Hibernate to issue `SELECT * FROM orders WHERE id = ? FOR UPDATE` — a genuine database-level row lock. A second transaction calling the same method for the same row blocks at the database level until the first transaction commits or rolls back, exactly mirroring the `ReentrantLock` behavior above, except enforced by the database itself rather than in-process Java locking.

## 7. Gotchas & takeaways

> Gotcha: pessimistic locks are held for the *entire* duration of the transaction, not just the query — a long-running transaction that acquires a `PESSIMISTIC_WRITE` lock early and does slow, unrelated work afterward can block every other transaction needing that row for the whole time, risking timeouts or even deadlocks if two transactions try to lock the same rows in different orders.

- Optimistic locking (`@Version`) lets concurrent transactions proceed and only fails the loser at write time with `OptimisticLockException` — cheap, but requires the caller to handle retries.
- Pessimistic locking (`@Lock(PESSIMISTIC_WRITE)`/`PESSIMISTIC_READ`) blocks conflicting transactions up front via a real database row lock — no exception, but reduces concurrency and risks lock contention or deadlocks.
- Choose optimistic locking when conflicts are rare; choose pessimistic locking when conflicts are common or a strict read-then-write sequence must not be interleaved.
- Always retry on a *fresh read*, not on the original stale entity, when handling `OptimisticLockException`.
