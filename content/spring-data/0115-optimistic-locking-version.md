---
card: spring-data
gi: 115
slug: optimistic-locking-version
title: "Optimistic locking (@Version)"
---

## 1. What it is

`@Version` on a MongoDB document field makes Spring Data MongoDB detect **lost updates**: whenever a document is saved, it checks that the version stored in the database still matches the version the caller last read, and increments it on success. If a concurrent save has already bumped the version in between, the save fails with `OptimisticLockingFailureException` instead of silently overwriting someone else's change.

```java
@Document("orders")
class Order {
    @Id String id;
    String status;
    @Version Long version; // managed automatically by Spring Data MongoDB
}
```

## 2. Why & when

MongoDB has no built-in row-level locking the way some relational databases do for `SELECT ... FOR UPDATE`. Two application instances can both load the same document, both modify their in-memory copy, and both call `save()` — without `@Version`, the second save simply overwrites the first one's changes with no error and no warning: a **lost update**. `@Version` turns that silent data loss into a detectable, recoverable failure.

Reach for `@Version` when:

- Multiple requests (or multiple application instances behind a load balancer) can read-modify-write the same document concurrently, and losing one of those updates would be a real bug — inventory counts, account balances, order status transitions.
- You want to avoid the cost and complexity of a multi-document transaction (the previous card) for the common case of protecting a **single** document from concurrent overwrite — optimistic locking on one document is far cheaper than a transaction.
- You want the failure to surface explicitly (as an exception the caller can catch and retry) rather than have it happen invisibly.

## 3. Core concept

```
 Thread 1: read order (version=1, status=PENDING)
 Thread 2: read order (version=1, status=PENDING)      <- both read the SAME version

 Thread 1: status=SHIPPED, save()  -> DB checks version==1: MATCH -> write succeeds, version becomes 2
 Thread 2: status=CANCELLED, save() -> DB checks version==1: MISMATCH (DB now has 2) -> OptimisticLockingFailureException
```

The version field is the arbiter: a save only succeeds if the version it's writing against still matches what's actually in the database — proof that nobody else changed the document in between.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads read the same version; the first save succeeds and bumps the version, the second save fails because its version is stale">
  <rect x="20" y="20" width="600" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Both threads read: version = 1</text>

  <rect x="40" y="80" width="260" height="45" rx="8" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="170" y="102" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">Thread 1 saves (version 1 -&gt; 2)</text>
  <text x="170" y="117" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SUCCEEDS</text>

  <rect x="340" y="80" width="260" height="45" rx="8" fill="#f8514922" stroke="#f85149" stroke-width="1.5"/>
  <text x="470" y="102" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Thread 2 saves (expects version 1)</text>
  <text x="470" y="117" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">FAILS -- DB already at version 2</text>

  <rect x="150" y="150" width="340" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="173" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">OptimisticLockingFailureException</text>
</svg>

The database is the single source of truth for the version; whichever save arrives second, against a now-stale version, is the one that fails.

## 5. Runnable example

The scenario: two concurrent updates to the same order document, evolving from a basic version check that detects the conflict, to a repository that throws a proper exception on mismatch, to a retry loop that re-reads and reapplies the intended change after a conflict — the standard way applications recover from optimistic locking failures.

### Level 1 — Basic

Model the version check directly: a save only applies if the version being written matches what's currently stored.

```java
import java.util.*;

public class OptimisticLockingLevel1 {
    public static void main(String[] args) {
        OrdersCollection orders = new OrdersCollection();
        orders.insert(new Order("1", "PENDING", 0));

        Order copyForThread1 = new Order("1", "SHIPPED", 0);   // both threads read version=0
        Order copyForThread2 = new Order("1", "CANCELLED", 0);

        boolean thread1Result = orders.save(copyForThread1);
        boolean thread2Result = orders.save(copyForThread2); // its version (0) is now stale -- DB is at version 1

        System.out.println("Thread 1 save succeeded: " + thread1Result);
        System.out.println("Thread 2 save succeeded: " + thread2Result);
        System.out.println("Final status: " + orders.docs.get("1").status + ", version: " + orders.docs.get("1").version);
    }
}

class Order { String id; String status; long version; Order(String id, String status, long version) { this.id = id; this.status = status; this.version = version; } }

// Stands in for MongoTemplate's @Version-aware save logic.
class OrdersCollection {
    Map<String, Order> docs = new HashMap<>();

    void insert(Order order) { docs.put(order.id, order); } // version starts at whatever the caller set, e.g. 0

    boolean save(Order candidate) {
        Order current = docs.get(candidate.id);
        if (current.version != candidate.version) return false; // STALE -- someone else already saved a newer version
        candidate.version = current.version + 1; // version bump happens ONLY on a successful save
        docs.put(candidate.id, candidate);
        return true;
    }
}
```

How to run: `java OptimisticLockingLevel1.java`

Both "threads" load the document at `version=0`. Thread 1's save matches the stored version, so it succeeds and bumps the stored version to `1`. Thread 2's save is checked against the *current* stored version (now `1`), not the version it read (`0`) — they no longer match, so the save is rejected. `CANCELLED` never overwrites `SHIPPED`.

### Level 2 — Intermediate

Make the failure explicit with a real exception, matching what a Spring Data MongoDB repository actually throws, and show it being caught.

```java
import java.util.*;

public class OptimisticLockingLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.insert(new Order("1", "PENDING", 0));

        Order copyForThread1 = new Order("1", "SHIPPED", 0);
        Order copyForThread2 = new Order("1", "CANCELLED", 0);

        repo.save(copyForThread1); // succeeds
        try {
            repo.save(copyForThread2); // fails -- version is stale
        } catch (OptimisticLockingFailureException e) {
            System.out.println("Caught: " + e.getMessage());
        }

        System.out.println("Final status: " + repo.docs.get("1").status);
    }
}

class Order { String id; String status; long version; Order(String id, String status, long version) { this.id = id; this.status = status; this.version = version; } }

// Stands in for org.springframework.dao.OptimisticLockingFailureException.
class OptimisticLockingFailureException extends RuntimeException {
    OptimisticLockingFailureException(String msg) { super(msg); }
}

class OrderRepository {
    Map<String, Order> docs = new HashMap<>();
    void insert(Order order) { docs.put(order.id, order); }

    void save(Order candidate) { // matches repository.save(order) throwing on conflict
        Order current = docs.get(candidate.id);
        if (current.version != candidate.version) {
            throw new OptimisticLockingFailureException(
                "Order " + candidate.id + " was modified concurrently (expected version "
                + candidate.version + ", found " + current.version + ")");
        }
        candidate.version = current.version + 1;
        docs.put(candidate.id, candidate);
    }
}
```

How to run: `java OptimisticLockingLevel2.java`

`save` now throws `OptimisticLockingFailureException` with a clear message instead of returning a boolean, matching the real exception type Spring Data MongoDB throws from a `@Version`-annotated document's save. The caller catches it explicitly — the shape a real service method would use to decide whether to retry, surface an error to the user, or log and move on.

### Level 3 — Advanced

Recover from the conflict automatically: on `OptimisticLockingFailureException`, re-read the current document, reapply the intended change on top of the fresh version, and retry — the standard optimistic-locking recovery pattern.

```java
import java.util.*;
import java.util.function.*;

public class OptimisticLockingLevel3 {
    // Retries the WHOLE read-modify-write cycle, not just the write -- the modification must apply to the FRESH document.
    static void updateStatusWithRetry(OrderRepository repo, String id, String newStatus, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            Order fresh = repo.findById(id); // re-read on EVERY attempt, including the first
            fresh.status = newStatus;
            try {
                repo.save(fresh);
                System.out.println("Saved on attempt " + attempt + " (new version " + fresh.version + ")");
                return;
            } catch (OptimisticLockingFailureException e) {
                System.out.println("Attempt " + attempt + " conflicted (" + e.getMessage() + "), re-reading and retrying...");
            }
        }
        throw new IllegalStateException("gave up after " + maxAttempts + " attempts");
    }

    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.insert(new Order("1", "PENDING", 0));

        // Simulate a concurrent writer racing ahead and bumping the version TWICE before our retry loop wins.
        Order sneaky = repo.findById("1"); sneaky.status = "PACKED"; repo.save(sneaky);   // version 0 -> 1
        Order sneaky2 = repo.findById("1"); sneaky2.status = "LABELED"; repo.save(sneaky2); // version 1 -> 2

        updateStatusWithRetry(repo, "1", "SHIPPED", 5);

        System.out.println("Final status: " + repo.docs.get("1").status + ", version: " + repo.docs.get("1").version);
    }
}

class Order { String id; String status; long version; Order(String id, String status, long version) { this.id = id; this.status = status; this.version = version; } }

class OptimisticLockingFailureException extends RuntimeException {
    OptimisticLockingFailureException(String msg) { super(msg); }
}

class OrderRepository {
    Map<String, Order> docs = new HashMap<>();
    void insert(Order order) { docs.put(order.id, order); }
    Order findById(String id) { Order o = docs.get(id); return new Order(o.id, o.status, o.version); } // fresh copy

    void save(Order candidate) {
        Order current = docs.get(candidate.id);
        if (current.version != candidate.version) {
            throw new OptimisticLockingFailureException("stale version " + candidate.version + ", current is " + current.version);
        }
        candidate.version = current.version + 1;
        docs.put(candidate.id, candidate);
    }
}
```

How to run: `java OptimisticLockingLevel3.java`

Before the retry loop even starts, two "sneaky" concurrent saves bump the document's version from `0` to `2` and change its status twice. `updateStatusWithRetry` re-reads the document fresh on every attempt (not just the first), reapplies `"SHIPPED"` on top of whatever the current state is, and calls `save`. Because it reads the *current* version each time rather than reusing a stale one, it succeeds on its very first attempt, correctly landing on top of the latest state instead of conflicting with it.

## 6. Walkthrough

Execution starts in `main` for Level 3. `repo.insert` creates the order at `version=0`. Two "sneaky" writes then run sequentially, outside the retry loop: the first reads the document (`version=0`), sets `status="PACKED"`, and saves — this succeeds and bumps the stored version to `1`. The second reads again (now `version=1`), sets `status="LABELED"`, and saves — succeeds, bumping the version to `2`. This simulates two other requests having already modified the document by the time our update wants to run.

`updateStatusWithRetry(repo, "1", "SHIPPED", 5)` then begins attempt `1`: it calls `repo.findById("1")`, which returns a *fresh* copy at the current state — `status="LABELED", version=2`. It sets `status="SHIPPED"` on that fresh copy and calls `repo.save(fresh)`. Because `fresh.version` (`2`) matches the currently stored version (`2`), the save succeeds immediately: the stored version becomes `3`, and the method returns without needing a second attempt.

```
Saved on attempt 1 (new version 3)
Final status: SHIPPED, version: 3
```

If a real conflict had occurred — for example, if another write had happened *between* `findById` and `save` inside the retry loop itself — `repo.save` would throw `OptimisticLockingFailureException`, the `catch` block would print a retry message, and the loop would go around again, calling `findById` a second time to get an even fresher copy before reapplying `"SHIPPED"`. This is exactly the pattern a real Spring Data MongoDB service method uses around a `@Version`-protected `save()` call: catch the exception, re-read, reapply the *intent* of the change (not the stale object), and retry — never simply retry the same stale `save()` call, since it would fail identically every time.

## 7. Gotchas & takeaways

> Gotcha: retrying a failed optimistic-lock save by resubmitting the *same* stale object will fail again in exactly the same way — the retry must re-read the current document first and reapply the intended change on top of it, not just call `save()` again on the old copy.

> Gotcha: `@Version` only protects the single document it's declared on — it does nothing for consistency across multiple documents. If an operation needs "these several documents must change together, safely," that's what multi-document transactions (the previous card) are for.

- `@Version` adds an automatic, monotonically increasing counter that Spring Data MongoDB checks on every save, rejecting the save with `OptimisticLockingFailureException` if the stored version has moved on since the document was read.
- This detects lost updates cheaply, without locking anything — far lighter-weight than a multi-document transaction for protecting a single document.
- The standard recovery pattern on conflict is: catch the exception, re-read the document fresh, reapply the intended change, and retry — bounded by a maximum attempt count.
- `@Version` guards one document at a time; it is not a substitute for a transaction when multiple documents must stay consistent together.
