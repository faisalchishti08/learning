---
card: spring-data
gi: 110
slug: index-management
title: "Index management"
---

## 1. What it is

Beyond the single-field `@Indexed` annotation from the document-mapping card, Spring Data MongoDB supports `@CompoundIndex` (an index spanning multiple fields together), unique indexes (`@Indexed(unique = true)`), TTL indexes (`@Indexed(expireAfterSeconds = ...)`, automatically deleting documents after a time period), and programmatic index creation/inspection via `IndexOperations` for cases annotations can't express or when indexes need to be managed dynamically rather than declared on the entity.

```java
@Document("orders")
@CompoundIndex(name = "status_total_idx", def = "{'status': 1, 'total': -1}")
class Order {
    @Indexed(unique = true) String orderNumber; // enforces uniqueness at the database level
    @Indexed(expireAfterSeconds = 86400) Instant createdAt; // TTL: auto-deleted after 24 hours
}
```

## 2. Why & when

The document-mapping card's `@Indexed` covers the simplest case: one field, one index. Real applications routinely need more: a query filtering on *two* fields together benefits from one compound index rather than two separate single-field indexes; a business rule requiring no duplicate values needs the database itself to enforce it, not just application code; temporary data (session tokens, cache entries) benefits from automatic expiration rather than manual cleanup jobs.

Reach for these more advanced index types specifically when:

- A query regularly filters (or sorts) on a combination of fields together — a compound index covering that exact combination serves it far better than two separate single-field indexes.
- A field must be unique across the collection (an email address, an order number) — a unique index enforces this at the database level, rejecting the write outright rather than relying on application code to check first (which has the same race-condition risk covered in earlier optimistic-locking cards).
- Documents naturally expire after a fixed time (session data, temporary tokens, log entries) — a TTL index has MongoDB delete them automatically, with no scheduled cleanup job required.

## 3. Core concept

```
 @CompoundIndex(def = "{'status': 1, 'total': -1}")
   -- ONE index serving queries that filter/sort on BOTH status AND total together
   -- far more effective than separate single-field indexes for a combined condition

 @Indexed(unique = true) String orderNumber
   -- database REJECTS any insert/update that would create a duplicate value
   -- (not just application-level validation, which has a race-condition gap)

 @Indexed(expireAfterSeconds = 86400) Instant createdAt
   -- MongoDB's background process deletes documents once (createdAt + 86400s) has passed
   -- NO application code, scheduled job, or manual cleanup needed
```

Each advanced index type solves a distinct problem: multi-field query performance, database-enforced uniqueness, or automatic expiration.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Three index types each address a different concern: compound indexes for combined query performance, unique indexes for enforced uniqueness, TTL indexes for automatic expiration">
  <rect x="20" y="20" width="180" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">@CompoundIndex</text>
  <text x="110" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">{status, total} together</text>
  <text x="110" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; fast combined-field queries</text>

  <rect x="230" y="20" width="180" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">@Indexed(unique)</text>
  <text x="320" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">rejects duplicate values</text>
  <text x="320" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; DB-enforced uniqueness</text>

  <rect x="440" y="20" width="180" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="530" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">@Indexed(expireAfter)</text>
  <text x="530" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">deletes old documents</text>
  <text x="530" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; automatic expiration (TTL)</text>
</svg>

Each index type addresses a distinct, independent concern — combined-field query speed, enforced uniqueness, or automatic time-based expiration.

## 5. Runnable example

The scenario: managing orders, evolving from a compound-index-style query performance comparison, to a unique-index-style constraint enforcement, to a TTL-index-style automatic expiration check.

### Level 1 — Basic

Model a compound index's benefit: a query on two fields together resolves faster with one combined structure than by intersecting two separate single-field lookups.

```java
import java.util.*;
import java.util.stream.*;

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

public class IndexMgmtLevel1 {
    // Simulates a compound index: a single sorted structure keyed on (status, total) TOGETHER.
    static Map<String, List<Order>> buildCompoundIndex(List<Order> orders) {
        // Real MongoDB stores this as one B-tree over the combined key; simplified here as a grouped map.
        return orders.stream().collect(Collectors.groupingBy(o -> o.status));
    }

    // @CompoundIndex(def = "{'status': 1, 'total': -1}") lookup: filter status directly via the index, THEN
    // the index's own internal ordering already has entries sorted by total within each status group.
    static List<Order> findByStatusSortedByTotal(Map<String, List<Order>> compoundIndex, String status) {
        List<Order> matching = new ArrayList<>(compoundIndex.getOrDefault(status, List.of()));
        matching.sort(Comparator.comparingDouble((Order o) -> o.total).reversed()); // index ALREADY has this order
        return matching;
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", 50), new Order("2", "SHIPPED", 300), new Order("3", "PENDING", 100)
        );
        Map<String, List<Order>> compoundIndex = buildCompoundIndex(orders);

        List<Order> result = findByStatusSortedByTotal(compoundIndex, "SHIPPED");
        System.out.println("Shipped orders, by total descending: " + result.stream().map(o -> o.id).toList());
    }
}
```

How to run: `java IndexMgmtLevel1.java`

The compound index groups by `status` first, and within each group the entries are effectively already ordered by `total` (a real compound index physically stores entries sorted by both keys together) — a query filtering on `status` and sorting by `total` can use this single structure directly, rather than needing to filter with one index and then sort the results separately.

### Level 2 — Intermediate

Model a unique index's enforcement: rejecting a duplicate value at the point of insertion, rather than relying on application code to check first.

```java
import java.util.*;

class DuplicateKeyException extends RuntimeException { DuplicateKeyException(String msg) { super(msg); } }

// Stands in for a collection with @Indexed(unique = true) String orderNumber.
class UniqueIndexedCollection {
    private final Set<String> seenOrderNumbers = new HashSet<>();
    private final Map<String, String> collection = new HashMap<>(); // orderNumber -> status, simplified

    void insert(String orderNumber, String status) {
        if (!seenOrderNumbers.add(orderNumber)) { // Set.add returns false if the value was ALREADY present
            throw new DuplicateKeyException("E11000 duplicate key error: orderNumber '" + orderNumber + "' already exists");
        }
        collection.put(orderNumber, status);
    }
}

public class IndexMgmtLevel2 {
    public static void main(String[] args) {
        UniqueIndexedCollection orders = new UniqueIndexedCollection();

        orders.insert("ORD-1001", "PENDING"); // succeeds -- first time seeing this order number
        System.out.println("First insert succeeded.");

        try {
            orders.insert("ORD-1001", "SHIPPED"); // FAILS -- duplicate orderNumber, rejected by the unique index
        } catch (DuplicateKeyException e) {
            System.out.println("Second insert correctly rejected: " + e.getMessage());
        }
    }
}
```

How to run: `java IndexMgmtLevel2.java`

The second insert, reusing `"ORD-1001"`, is rejected outright — this mirrors exactly how a real `@Indexed(unique = true)` field causes MongoDB to reject the write server-side with a duplicate-key error, providing a guarantee application-level uniqueness checking alone cannot: no race condition where two concurrent inserts both pass a "does this already exist" check before either one commits.

### Level 3 — Advanced

Model a TTL index's automatic expiration: documents older than a configured threshold are treated as expired and excluded from results, matching how MongoDB's background TTL monitor periodically deletes expired documents.

```java
import java.time.*;
import java.util.*;
import java.util.stream.*;

class SessionToken { String token; Instant createdAt; SessionToken(String token, Instant createdAt) { this.token = token; this.createdAt = createdAt; } }

public class IndexMgmtLevel3 {
    // Simulates @Indexed(expireAfterSeconds = 3600) Instant createdAt -- 1 hour TTL.
    static final long TTL_SECONDS = 3600;

    static boolean isExpired(SessionToken token, Instant now) {
        return Duration.between(token.createdAt, now).getSeconds() > TTL_SECONDS;
    }

    // Simulates the effect of MongoDB's TTL background monitor: expired documents are treated as gone.
    static List<SessionToken> findActiveTokens(List<SessionToken> allTokens, Instant now) {
        return allTokens.stream().filter(t -> !isExpired(t, now)).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        Instant now = Instant.now();
        List<SessionToken> tokens = List.of(
            new SessionToken("fresh-token", now.minusSeconds(60)),          // 1 minute old -- still valid
            new SessionToken("old-token", now.minusSeconds(7200)),           // 2 hours old -- expired
            new SessionToken("borderline-token", now.minusSeconds(3599))     // just under the threshold -- still valid
        );

        List<SessionToken> active = findActiveTokens(tokens, now);
        System.out.println("Active tokens: " + active.stream().map(t -> t.token).toList());
        System.out.println("(old-token would have been AUTOMATICALLY deleted by MongoDB's TTL monitor by now)");
    }
}
```

How to run: `java IndexMgmtLevel3.java`

`isExpired` checks each token's age against the `3600`-second TTL threshold: `fresh-token` (60 seconds old) and `borderline-token` (3599 seconds old, just under the threshold) both remain active, while `old-token` (7200 seconds old) is correctly identified as expired and excluded — mirroring how a real `@Indexed(expireAfterSeconds = 3600)` field causes MongoDB's background TTL monitor to periodically scan for and delete documents whose `createdAt` timestamp has aged past the threshold, with no application code involved in the cleanup at all.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `now` captures the current instant, and three `SessionToken` objects are built with `createdAt` timestamps set relative to it: `fresh-token` at 60 seconds ago, `old-token` at 7200 seconds (2 hours) ago, and `borderline-token` at 3599 seconds ago — deliberately just 1 second under the 3600-second TTL threshold.

`findActiveTokens(tokens, now)` runs, calling `isExpired` on each token in turn. For `fresh-token`, `Duration.between(createdAt, now).getSeconds()` computes `60`, which is not greater than `3600`, so `isExpired` returns `false` — the token is kept. For `old-token`, the computed duration is `7200`, which *is* greater than `3600`, so `isExpired` returns `true` — the token is filtered out. For `borderline-token`, the computed duration is `3599`, which is not greater than `3600` (just barely), so `isExpired` returns `false` — the token is kept, right at the edge of the threshold.

The resulting `active` list contains `fresh-token` and `borderline-token`, but not `old-token` — printed as "Active tokens: [fresh-token, borderline-token]", followed by a note that a real TTL index would have already physically deleted `old-token` from the database by this point, rather than merely excluding it from one particular query's results.

```
now - 60s   (fresh-token):        60 > 3600? NO  -> active
now - 7200s (old-token):          7200 > 3600? YES -> EXPIRED, excluded
now - 3599s (borderline-token):  3599 > 3600? NO  -> active (just under threshold)

result: [fresh-token, borderline-token]
```

In a real Spring Data MongoDB application, `@Indexed(expireAfterSeconds = 3600)` on a `SessionToken.createdAt` field causes MongoDB's background TTL monitor (a process that runs periodically, typically every 60 seconds, independent of any application query) to physically delete documents whose `createdAt` has aged past the threshold — unlike this example's `findActiveTokens`, which only *filters* expired tokens out of one query's results, the real TTL index actually removes the data from the collection entirely, freeing storage automatically with zero application code needed to manage the cleanup.

## 7. Gotchas & takeaways

> Gotcha: MongoDB's TTL monitor runs on a periodic background cycle (not instantaneously the moment a document expires), so there's a real window — typically up to 60 seconds, sometimes longer under load — between when a document technically expires and when it's actually deleted; application code that needs an exact "is this expired right now" answer should still check the timestamp explicitly (as `isExpired` does here), rather than assuming an expired document is already gone.

- `@CompoundIndex` builds one index spanning multiple fields together, serving combined-field query-and-sort conditions far more efficiently than separate single-field indexes.
- `@Indexed(unique = true)` enforces uniqueness at the database level, rejecting duplicate writes outright — a stronger guarantee than an application-level check, which has the same race-condition gap covered in earlier optimistic-locking cards.
- `@Indexed(expireAfterSeconds = ...)` (a TTL index) has MongoDB automatically delete documents once they age past the threshold, with no scheduled cleanup job needed.
- TTL deletion happens on a periodic background cycle, not instantly at the exact expiration moment — account for that lag in any logic that depends on precise expiration timing.
