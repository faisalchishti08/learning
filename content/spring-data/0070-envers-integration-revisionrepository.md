---
card: spring-data
gi: 70
slug: envers-integration-revisionrepository
title: "Envers integration (RevisionRepository)"
---

## 1. What it is

Hibernate Envers keeps a full history of every change made to an audited entity, storing each version as a numbered "revision" in a shadow `_AUD` table. Spring Data JPA's `RevisionRepository<T, ID, N>` interface exposes that history through ordinary repository methods — `findRevisions(id)`, `findLastChangeRevision(id)` — so retrieving an entity's past states doesn't require hand-written Envers `AuditReader` queries.

```java
interface OrderRepository extends JpaRepository<Order, Long>, RevisionRepository<Order, Long, Integer> { }

Revisions<Integer, Order> history = orderRepository.findRevisions(1L);
```

## 2. Why & when

The previous card's `@EnableJpaAuditing` only tracks *when* and *by whom* an entity was last changed — it overwrites `updatedAt` every time, keeping no record of what the entity looked like before. Envers goes further: it keeps every past version as its own row, so you can answer "what did this order look like on revision 3" or "list every change ever made to this row," not just "when was it last touched."

Reach for Envers/`RevisionRepository` specifically when:

- Full change history matters for compliance, debugging, or "undo" functionality — auditing timestamps alone (`@CreatedDate`/`@LastModifiedDate`) can't answer "what was the value before the last three changes."
- You need to reconstruct an entity's exact state as of a specific point in time or a specific revision number, not just its current state.
- The overhead of a shadow history table per audited entity (more storage, extra writes on every change) is acceptable in exchange for that capability — this is a heavier feature than basic auditing.

## 3. Core concept

```
 @Audited                            orders_AUD (shadow table, one row per change):
 @Entity                              id | REV | REVTYPE | status   | total
 class Order { ... }                   1 |   1 |   ADD   | PENDING  | 100
                                        1 |   2 |   MOD   | SHIPPED  | 100
                                        1 |   3 |   MOD   | SHIPPED  | 120

 orderRepository.findRevisions(1L)
   -> Revisions<Integer, Order> {
        revision 1: Order{status=PENDING, total=100}
        revision 2: Order{status=SHIPPED, total=100}
        revision 3: Order{status=SHIPPED, total=120}
      }
```

Every insert or update to an `@Audited` entity appends a new row to its shadow table; `RevisionRepository` reads that history back as a sequence of full entity snapshots.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Each change to an audited entity appends a full snapshot to a shadow revision table">
  <rect x="20" y="20" width="180" height="130" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">orders (live row)</text>
  <text x="110" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">id=1</text>
  <text x="110" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">status=SHIPPED</text>
  <text x="110" y="106" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">total=120</text>

  <rect x="260" y="10" width="360" height="150" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="30" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">orders_AUD (shadow history)</text>
  <text x="280" y="55" fill="#8b949e" font-size="8.5" font-family="monospace">REV=1  ADD  status=PENDING total=100</text>
  <text x="280" y="80" fill="#8b949e" font-size="8.5" font-family="monospace">REV=2  MOD  status=SHIPPED total=100</text>
  <text x="280" y="105" fill="#8b949e" font-size="8.5" font-family="monospace">REV=3  MOD  status=SHIPPED total=120</text>
  <text x="280" y="135" fill="#79c0ff" font-size="8.5" font-family="sans-serif">findRevisions(1L) -&gt; all 3 rows above</text>

  <line x1="200" y1="85" x2="255" y2="85" stroke="#8b949e" stroke-width="1.3" marker-end="url(#en)"/>
  <defs><marker id="en" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The live table always shows the current state; the shadow table accumulates one full snapshot per change, retrievable as a revision history.

## 5. Runnable example

The scenario: tracking an order's full change history, evolving from a plain mutable model with no history, to a simulated Envers shadow table recording every change, to a `RevisionRepository`-shaped API for querying that history including "as of revision N."

### Level 1 — Basic

Show the baseline: a plain entity that only ever holds its current state — no history is kept anywhere.

```java
class Order {
    long id; String status; double total;
    Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; }
}

public class EnversLevel1 {
    public static void main(String[] args) {
        Order order = new Order(1, "PENDING", 100);
        System.out.println("Created: status=" + order.status + ", total=" + order.total);

        order.status = "SHIPPED"; // previous state ("PENDING") is now GONE, nowhere to recover it
        System.out.println("Updated: status=" + order.status + ", total=" + order.total);

        order.total = 120;
        System.out.println("Updated again: status=" + order.status + ", total=" + order.total);
        // No way to answer "what was this order's status right after it was created?"
    }
}
```

How to run: `java EnversLevel1.java`

Each mutation simply overwrites the field — by the end, there is no way to recover that the order was ever `"PENDING"` or that its total was ever `100`. This is the gap Envers closes: a plain `@Entity` (even with `@CreatedDate`/`@LastModifiedDate` auditing) only ever shows its current state.

### Level 2 — Intermediate

Introduce a simulated shadow "revision table" that records a full snapshot on every change, standing in for what Hibernate Envers does automatically for any `@Audited` entity.

```java
import java.util.*;

class Order {
    long id; String status; double total;
    Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; }
    Order copy() { return new Order(id, status, total); }
}

record Revision(int number, Order snapshot) {}

// Stands in for Hibernate Envers' shadow "orders_AUD" table.
class EnversShadowTable {
    private final List<Revision> revisions = new ArrayList<>();
    private int nextRevision = 1;

    void recordChange(Order current) {
        revisions.add(new Revision(nextRevision++, current.copy())); // full snapshot, not a diff
    }

    List<Revision> allRevisions() { return revisions; }
}

public class EnversLevel2 {
    public static void main(String[] args) {
        EnversShadowTable history = new EnversShadowTable();

        Order order = new Order(1, "PENDING", 100);
        history.recordChange(order); // revision 1: the initial insert

        order.status = "SHIPPED";
        history.recordChange(order); // revision 2

        order.total = 120;
        history.recordChange(order); // revision 3

        for (Revision r : history.allRevisions()) {
            System.out.println("Revision " + r.number() + ": status=" + r.snapshot().status + ", total=" + r.snapshot().total);
        }
    }
}
```

How to run: `java EnversLevel2.java`

Every call to `history.recordChange(order)` stores an independent full snapshot (`order.copy()`), so mutating `order` afterward never affects revisions already recorded — exactly like Envers' `orders_AUD` table, where each row is a complete point-in-time copy of the entity, not a live reference to it.

### Level 3 — Advanced

Wrap the shadow table behind a `RevisionRepository`-shaped API, supporting `findRevisions(id)` (the full history) and `findRevision(id, revisionNumber)` (a single point-in-time lookup), matching Spring Data's real `RevisionRepository` contract.

```java
import java.util.*;

class Order {
    long id; String status; double total;
    Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; }
    Order copy() { return new Order(id, status, total); }
    public String toString() { return "Order{status=" + status + ", total=" + total + "}"; }
}

record Revision(int number, Order snapshot) {}

// Stands in for: interface OrderRepository extends JpaRepository<Order, Long>,
//                                                    RevisionRepository<Order, Long, Integer> { }
class OrderRepository {
    private final Map<Long, List<Revision>> revisionsByOrderId = new HashMap<>();
    private int nextRevision = 1;

    void save(Order order) {
        revisionsByOrderId
            .computeIfAbsent(order.id, k -> new ArrayList<>())
            .add(new Revision(nextRevision++, order.copy()));
    }

    // RevisionRepository.findRevisions(ID id)
    List<Revision> findRevisions(long orderId) {
        return revisionsByOrderId.getOrDefault(orderId, List.of());
    }

    // RevisionRepository.findLastChangeRevision(ID id)
    Optional<Revision> findLastChangeRevision(long orderId) {
        List<Revision> revs = findRevisions(orderId);
        return revs.isEmpty() ? Optional.empty() : Optional.of(revs.get(revs.size() - 1));
    }

    // A specific point-in-time lookup, by revision number.
    Optional<Order> findRevision(long orderId, int revisionNumber) {
        return findRevisions(orderId).stream()
            .filter(r -> r.number() == revisionNumber)
            .map(Revision::snapshot)
            .findFirst();
    }
}

public class EnversLevel3 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();

        Order order = new Order(1, "PENDING", 100);
        repo.save(order); // revision 1

        order.status = "SHIPPED";
        repo.save(order); // revision 2

        order.total = 120;
        repo.save(order); // revision 3

        System.out.println("Full history:");
        for (Revision r : repo.findRevisions(1L)) {
            System.out.println("  rev " + r.number() + ": " + r.snapshot());
        }

        System.out.println("As of revision 1 (right after creation): " + repo.findRevision(1L, 1).orElseThrow());
        System.out.println("Last change: " + repo.findLastChangeRevision(1L).orElseThrow());
    }
}
```

How to run: `java EnversLevel3.java`

`repo.findRevision(1L, 1)` reconstructs exactly what the order looked like immediately after creation (`status=PENDING, total=100`), even though the live `order` object has long since moved on to `status=SHIPPED, total=120` — this is the core capability `RevisionRepository` provides that plain auditing (from the previous card) cannot.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `order` is created with `status="PENDING", total=100`, and `repo.save(order)` runs, appending `Revision(1, snapshot{PENDING,100})` to `revisionsByOrderId.get(1L)` — the snapshot is an independent copy, not a reference to `order`.

Next, `order.status` is mutated to `"SHIPPED"` and `repo.save(order)` runs again, appending `Revision(2, snapshot{SHIPPED,100})`. Then `order.total` is mutated to `120` and `repo.save(order)` runs a third time, appending `Revision(3, snapshot{SHIPPED,120})`. Throughout, each prior `Revision`'s stored snapshot is untouched by these later mutations, because each was copied at the moment it was recorded.

The loop over `repo.findRevisions(1L)` then prints all three revisions in order, showing the order's state evolving: `PENDING/100` → `SHIPPED/100` → `SHIPPED/120`. Next, `repo.findRevision(1L, 1)` filters that same list down to the entry where `number == 1`, returning the very first snapshot — `PENDING/100` — regardless of what the live `order` variable currently holds. Finally, `repo.findLastChangeRevision(1L)` returns the last element of the list, `SHIPPED/120`, matching the order's current state.

```
save() #1: order{PENDING,100}  -> revisions=[rev1{PENDING,100}]
save() #2: order{SHIPPED,100}  -> revisions=[rev1{PENDING,100}, rev2{SHIPPED,100}]
save() #3: order{SHIPPED,120}  -> revisions=[rev1{PENDING,100}, rev2{SHIPPED,100}, rev3{SHIPPED,120}]

findRevision(1L, 1)          -> rev1{PENDING,100}   (reconstructed past state)
findLastChangeRevision(1L)   -> rev3{SHIPPED,120}   (matches current state)
```

In a real Spring Data JPA application, marking `Order` `@Audited` (Hibernate Envers' annotation) causes every insert or update to also write a row into an automatically-generated `orders_AUD` shadow table, tagged with an incrementing revision number and a `REVTYPE` (`ADD`/`MOD`/`DEL`). `orderRepository.findRevisions(1L)` (from `RevisionRepository<Order, Long, Integer>`) queries that shadow table and returns a `Revisions<Integer, Order>` object — an iterable sequence of fully-reconstructed `Order` snapshots, one per historical revision, letting application code answer "what did this order look like at any point in its history" without ever writing raw SQL against `orders_AUD` directly.

## 7. Gotchas & takeaways

> Gotcha: Envers auditing must be enabled per-entity via `@Audited` — an unmarked entity has no shadow table at all, and calling `RevisionRepository` methods against it fails, since there is no history to query in the first place.

- Basic JPA auditing (the previous card) only tracks the *current* entity's created/modified metadata; Envers keeps a full, independent snapshot for *every* change.
- Each change appends a new revision row to a shadow table — snapshots are independent copies, immune to later mutation of the live entity.
- `RevisionRepository<T, ID, N>` exposes that history through ordinary repository methods: `findRevisions(id)` for the full history, `findLastChangeRevision(id)` for the most recent one.
- This is a heavier feature than plain auditing — every write to an `@Audited` entity also writes to its shadow table, at additional storage and I/O cost.
