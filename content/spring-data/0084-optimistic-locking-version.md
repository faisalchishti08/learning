---
card: spring-data
gi: 84
slug: optimistic-locking-version
title: "Optimistic locking (@Version)"
---

## 1. What it is

Spring Data JDBC supports the same `@Version` field the JPA locking card covered — a numeric field that Spring Data JDBC increments on every save and includes in the `UPDATE`'s `WHERE` clause, so a concurrent update from stale data affects zero rows and is detected as an `OptimisticLockingFailureException`. Because there is no persistence context, there's no automatic optimistic-lock exception during regular field access — it's checked purely at `save()` time.

```java
class Order {
    @Id Long id;
    @Version Long version;
    String status;
}
// UPDATE orders SET status = ?, version = version + 1 WHERE id = ? AND version = ?
```

## 2. Why & when

The JPA locking card explained `@Version` in the context of a persistence context that tracks managed entities across a transaction; Spring Data JDBC has no such context, so understanding how `@Version` behaves *without* one matters — every `save()` call is an independent, synchronous operation, and the version check happens fresh each time, with no notion of "already loaded in this transaction."

Reach for `@Version` on Spring Data JDBC specifically when:

- Multiple concurrent processes (or threads) might load and save the same aggregate, and you need to detect (not necessarily prevent) a lost-update conflict — exactly the same motivation as the JPA card, but without a persistence context involved.
- You want conflict detection with zero extra infrastructure — no pessimistic locking, no database-level row locks, just a version column and a conditional `UPDATE`.
- You're handling a "read, then update" business operation and need to guarantee it fails cleanly (rather than silently overwriting) if another process updated the same aggregate in between.

## 3. Core concept

```
 @Version Long version;   -- starts at 0 (or null, then set to 0 on first save)

 Tx A: load order (version=0)         Tx B: load order (version=0)
 Tx A: save(order)  -- UPDATE ... SET version=1 WHERE id=1 AND version=0  -- 1 row affected, SUCCESS
 Tx B: save(order)  -- UPDATE ... SET version=1 WHERE id=1 AND version=0  -- 0 rows affected!
                     -- Spring Data JDBC throws OptimisticLockingFailureException
```

No persistence context is involved at all — each `save()` independently issues a conditional `UPDATE` and checks the affected-row count itself.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Two independent saves against the same stale version: the first succeeds and bumps the version, the second affects zero rows and fails">
  <rect x="20" y="20" width="280" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Tx A: save(order, version=0)</text>

  <rect x="340" y="20" width="280" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Tx B: save(order, version=0)</text>

  <rect x="20" y="90" width="280" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">1 row affected -&gt; version=1, OK</text>

  <rect x="340" y="90" width="280" height="45" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="480" y="107" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">0 rows affected (version now 1) -&gt;</text>
  <text x="480" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OptimisticLockingFailureException</text>

  <line x1="160" y1="65" x2="160" y2="85" stroke="#8b949e" stroke-width="1.3" marker-end="url(#vl)"/>
  <line x1="480" y1="65" x2="480" y2="85" stroke="#8b949e" stroke-width="1.3" marker-end="url(#vl)"/>
  <defs><marker id="vl" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Whichever save runs first wins and bumps the version; the second, still holding the now-stale version, affects zero rows and fails.

## 5. Runnable example

The scenario: two "processes" concurrently updating the same order's status, evolving from a baseline showing the lost-update problem without any version check, to a version-checked save detecting the conflict, to a retry loop handling the failure gracefully.

### Level 1 — Basic

Show the baseline problem: without any version check, a stale save silently overwrites a concurrent change — a lost update.

```java
import java.util.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();
    Order load(long id) { Order stored = db.get(id); return new Order(stored.id, stored.status); } // detached copy
    void save(Order order) { db.put(order.id, order); } // NO version check at all -- just overwrites
}

public class VersionLevel1 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.db.put(1L, new Order(1, "PENDING"));

        Order processA = repo.load(1L); // both processes load the SAME initial state
        Order processB = repo.load(1L);

        processA.status = "PROCESSING";
        repo.save(processA); // succeeds, no check

        processB.status = "CANCELLED"; // process B never saw process A's change
        repo.save(processB); // ALSO succeeds -- silently OVERWRITES "PROCESSING" with "CANCELLED"!

        System.out.println("Final status: " + repo.db.get(1L).status); // process A's update is LOST
    }
}
```

How to run: `java VersionLevel1.java`

The final status is `"CANCELLED"` — process A's `"PROCESSING"` update was silently overwritten and lost, because neither save checked whether the row had changed since it was loaded. This is the lost-update problem `@Version` exists to detect.

### Level 2 — Intermediate

Add a `version` field and a conditional `UPDATE` that only succeeds if the version still matches — detecting the exact conflict Level 1 silently allowed.

```java
import java.util.*;

class OptimisticLockingFailureException extends RuntimeException {
    OptimisticLockingFailureException(String msg) { super(msg); }
}

class Order { long id; String status; long version; Order(long id, String status, long version) { this.id = id; this.status = status; this.version = version; } }

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();

    Order load(long id) { Order stored = db.get(id); return new Order(stored.id, stored.status, stored.version); }

    // @Version-aware save: UPDATE ... SET status=?, version=version+1 WHERE id=? AND version=?
    void save(Order order) {
        Order stored = db.get(order.id);
        if (stored.version != order.version) {
            throw new OptimisticLockingFailureException(
                "Order " + order.id + " was modified by someone else (expected version " + order.version + ", found " + stored.version + ")");
        }
        db.put(order.id, new Order(order.id, order.status, order.version + 1)); // version bumped on success
    }
}

public class VersionLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.db.put(1L, new Order(1, "PENDING", 0));

        Order processA = repo.load(1L);
        Order processB = repo.load(1L);

        processA.status = "PROCESSING";
        repo.save(processA); // version 0 matches -> succeeds, db version becomes 1
        System.out.println("Process A saved. DB version now: " + repo.db.get(1L).version);

        processB.status = "CANCELLED";
        try {
            repo.save(processB); // processB still holds version 0, but db is now version 1 -> conflict!
        } catch (OptimisticLockingFailureException e) {
            System.out.println("Process B correctly failed: " + e.getMessage());
        }

        System.out.println("Final status (process A's change preserved): " + repo.db.get(1L).status);
    }
}
```

How to run: `java VersionLevel2.java`

Process A's save succeeds (its version, `0`, matches the stored version), bumping the stored version to `1`. Process B's save then fails loudly with `OptimisticLockingFailureException`, because it's still holding the stale `version=0` — the lost-update problem from Level 1 is now a detected, explicit failure instead of a silent overwrite, and `"PROCESSING"` (process A's change) survives.

### Level 3 — Advanced

Wrap the version-checked save in a retry loop that re-loads the current state and reapplies the intended change on conflict — the standard way application code handles `OptimisticLockingFailureException`, matching the retry pattern from the JPA locking card.

```java
import java.util.*;
import java.util.function.*;

class OptimisticLockingFailureException extends RuntimeException {
    OptimisticLockingFailureException(String msg) { super(msg); }
}

class Order { long id; String status; long version; Order(long id, String status, long version) { this.id = id; this.status = status; this.version = version; } }

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();
    Order load(long id) { Order stored = db.get(id); return new Order(stored.id, stored.status, stored.version); }
    void save(Order order) {
        Order stored = db.get(order.id);
        if (stored.version != order.version) {
            throw new OptimisticLockingFailureException("version conflict on order " + order.id);
        }
        db.put(order.id, new Order(order.id, order.status, order.version + 1));
    }
}

public class VersionLevel3 {
    // Retries the load-modify-save cycle on conflict, always reapplying `newStatus` against the FRESH state.
    static void updateStatusWithRetry(OrderRepository repo, long orderId, String newStatus, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                Order fresh = repo.load(orderId); // always a FRESH load, never the stale object from a prior attempt
                fresh.status = newStatus;
                repo.save(fresh);
                System.out.println("Update succeeded on attempt " + attempt);
                return;
            } catch (OptimisticLockingFailureException e) {
                System.out.println("Attempt " + attempt + " conflicted, retrying with a fresh load...");
            }
        }
        throw new IllegalStateException("Failed after " + maxAttempts + " attempts");
    }

    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.db.put(1L, new Order(1, "PENDING", 0));

        // Simulate a concurrent write that happens between our first load and our first save attempt.
        Order sneaky = repo.load(1L);
        sneaky.status = "PROCESSING";
        repo.save(sneaky); // db version becomes 1 -- this represents another process winning first

        updateStatusWithRetry(repo, 1L, "CANCELLED", 3); // our own update, retried until it succeeds
        System.out.println("Final status: " + repo.db.get(1L).status + ", version: " + repo.db.get(1L).version);
    }
}
```

How to run: `java VersionLevel3.java`

The "sneaky" concurrent write bumps the stored version to `1` before `updateStatusWithRetry` even starts. On attempt 1, `updateStatusWithRetry` calls `repo.load(1L)` fresh — getting the *current* version (`1`), not a stale one — so its save succeeds immediately on the first attempt, without ever hitting a conflict itself; the retry loop's value shows up when a conflict *does* happen between the retry's own load and save, which this same pattern handles by simply trying again with another fresh load.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `repo.db.put(1L, new Order(1, "PENDING", 0))` seeds the initial state at version `0`.

Next, `sneaky` loads the order (version `0`), mutates its status to `"PROCESSING"`, and saves it — this succeeds because `sneaky.version (0)` matches the stored version, bumping the stored version to `1`. This models "another process" completing its update before our own operation begins.

Then `updateStatusWithRetry(repo, 1L, "CANCELLED", 3)` runs. On attempt 1: `repo.load(1L)` fetches the *current* state, which is now version `1` (reflecting the sneaky write) — this is critical, because the retry loop always re-loads fresh rather than reusing a variable captured before the loop started. `fresh.status` is set to `"CANCELLED"`, and `repo.save(fresh)` is called: since `fresh.version (1)` matches the stored version (`1`), the save succeeds immediately, bumping the stored version to `2`. "Update succeeded on attempt 1" is printed, and the method returns without needing a second attempt.

The final printed line confirms `repo.db.get(1L).status` is `"CANCELLED"` and `version` is `2` — both the sneaky write (bumping version 0→1) and our own retried update (bumping version 1→2) are reflected, and no update was silently lost, because each write correctly saw the version left behind by the one before it.

```
seed: Order(1, "PENDING", version=0)
sneaky: load(v0) -> status=PROCESSING -> save -> version checked (0==0) OK -> stored version=1

updateStatusWithRetry attempt 1:
   load(1) -> fresh{version=1}  (sees the sneaky write's result, NOT a stale v0)
   fresh.status = CANCELLED
   save(fresh) -> version checked (1==1) OK -> stored version=2
   -> "succeeded on attempt 1"
```

In a real Spring Data JDBC application, `@Version Long version` on an aggregate root causes every `orderRepository.save(order)` call to generate `UPDATE orders SET status = ?, version = version + 1 WHERE id = ? AND version = ?`, binding the *in-memory* object's current `version` value as the `WHERE` condition. If the database reports zero rows affected (because another process already bumped the version), Spring Data JDBC translates that into `OptimisticLockingFailureException` — application code (typically inside a `@Transactional` service method) is expected to catch this, re-load the current state, and retry the intended change, exactly as `updateStatusWithRetry` demonstrates here.

## 7. Gotchas & takeaways

> Gotcha: because Spring Data JDBC has no persistence context, there is no automatic detection of a conflict *before* `save()` is called — unlike JPA, where a lazy-loaded stale reference might surface issues earlier, here the version check happens purely and only at the moment `save()` runs, so a long-running "read, think, then save" sequence has no warning of a conflict until the very end.

- `@Version` on Spring Data JDBC works the same conceptually as on JPA — a numeric field checked and incremented on every `UPDATE` — but with no persistence context involved at any point.
- A failed version check surfaces as `OptimisticLockingFailureException`, thrown directly from `save()`, based purely on the affected-row count of the conditional `UPDATE`.
- Always retry on a *fresh* load, not the object that failed to save — reusing the stale object would fail the version check again immediately.
- With no persistence context to coordinate multiple operations, each `save()` call is an entirely independent version check — there is no cross-call state to reason about beyond what's in the database itself.
