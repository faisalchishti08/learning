---
card: microservices
gi: 333
slug: change-data-capture-cdc
title: "Change Data Capture (CDC)"
---

## 1. What it is

**Change Data Capture (CDC)** is the general practice — and the family of tools (Debezium being the most common open-source example) — that captures every row-level insert, update, and delete made to a database and turns it into a stream of structured change events other systems can consume. It is most commonly implemented via [transaction log tailing](0332-transaction-log-tailing.md): a CDC tool attaches to the database's own commit log and emits one event per changed row, without requiring any application code changes or extra writes.

## 2. Why & when

The [transactional outbox pattern](0331-transactional-outbox-pattern.md) requires deliberately adding an outbox table and writing to it in application code. CDC offers a more general, less invasive alternative: point a CDC tool at an existing table, and it starts emitting a change event for every insert, update, and delete, without touching the application at all. This is powerful for populating a [reporting/analytics database](0316-reporting-analytics-database.md) or [data lake](0317-data-lake-data-warehouse-integration.md) from data the owning service never explicitly decided to publish as events, or for retrofitting event-driven integration onto a legacy service you can't easily modify.

Use CDC when you need a change feed from a table without modifying the owning application, or when the outbox pattern's requirement to explicitly author each event's shape is more overhead than a use case needs (e.g., a straightforward "replicate this whole table elsewhere" scenario). Be cautious about coupling other services directly to another service's internal table structure this way — that structure was never designed as a public contract, and it can change without warning; the outbox pattern's explicit event schema avoids exactly this coupling.

## 3. Core concept

A CDC tool connects to the source database as a replication client (the same mechanism the database uses to feed its own replicas), decodes each committed row change from the log, and publishes a corresponding structured event — typically including the operation type (`INSERT`/`UPDATE`/`DELETE`), the table and row identity, and often both the before and after values of changed columns.

```java
record ChangeEvent(String table, String operation, Map<String,Object> before, Map<String,Object> after) {}
// one event per row-level change, decoded straight from the transaction log
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An orders table receives an INSERT; the CDC tool tailing the transaction log emits a structured ChangeEvent; downstream consumers (a search index and a reporting database) each receive and apply it independently">
  <rect x="20" y="60" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">orders table: INSERT</text>

  <line x1="160" y1="77" x2="240" y2="77" stroke="#8b949e" marker-end="url(#a333)"/>
  <rect x="250" y="60" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="325" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">CDC tool -&gt; ChangeEvent</text>

  <line x1="400" y1="70" x2="480" y2="30" stroke="#3fb950" marker-end="url(#a333b)"/>
  <rect x="490" y="10" width="130" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="555" y="32" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Search index</text>

  <line x1="400" y1="85" x2="480" y2="120" stroke="#3fb950" marker-end="url(#a333b)"/>
  <rect x="490" y="105" width="130" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="555" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Reporting DB</text>

  <defs>
    <marker id="a333" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a333b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

CDC captures every row-level change from the log and fans it out as structured events to any number of independent downstream consumers.

## 5. Runnable example

Scenario: an orders table CDC-fed into two downstream projections (a search index and a reporting count), first shown reacting only to inserts, then extended to correctly handle updates and deletes as before/after diffs, and finally hardened so a consumer that misses an update doesn't drift permanently out of sync.

### Level 1 — Basic

```java
// File: CdcInsertOnly.java -- CDC emits a ChangeEvent for each INSERT;
// downstream consumers react independently.
import java.util.*;

public class CdcInsertOnly {
    record ChangeEvent(String table, String op, Map<String, Object> after) {}
    static List<Map<String, Object>> ordersTable = new ArrayList<>();
    static List<java.util.function.Consumer<ChangeEvent>> consumers = new ArrayList<>();

    static void insertOrder(String orderId, String region) {
        Map<String, Object> row = Map.of("id", orderId, "region", region);
        ordersTable.add(row);
        ChangeEvent event = new ChangeEvent("orders", "INSERT", row);
        System.out.println("CDC: captured " + event.op() + " on orders: " + event.after());
        consumers.forEach(c -> c.accept(event));
    }

    public static void main(String[] args) {
        consumers.add(e -> System.out.println("  search-index consumer: indexing " + e.after()));
        consumers.add(e -> System.out.println("  reporting consumer: counting new order in region " + e.after().get("region")));

        insertOrder("order-1", "EU");
    }
}
```

How to run: `java CdcInsertOnly.java`

`insertOrder` writes the row and immediately builds a `ChangeEvent` describing it, then fans it out to every registered consumer — each downstream system reacts to the same event independently, without knowing about each other or querying `ordersTable` directly.

### Level 2 — Intermediate

```java
// File: CdcWithUpdatesAndDeletes.java -- CDC events now carry BOTH before
// and after values, so consumers can react correctly to UPDATE (what
// changed) and DELETE (what's gone), not just INSERT.
import java.util.*;

public class CdcWithUpdatesAndDeletes {
    record ChangeEvent(String table, String op, Map<String, Object> before, Map<String, Object> after) {}
    static Map<String, Map<String, Object>> ordersTable = new HashMap<>();
    static List<java.util.function.Consumer<ChangeEvent>> consumers = new ArrayList<>();

    static void emit(ChangeEvent event) {
        System.out.println("CDC: " + event.op() + " before=" + event.before() + " after=" + event.after());
        consumers.forEach(c -> c.accept(event));
    }

    static void insertOrder(String id, String status) {
        Map<String, Object> row = Map.of("id", id, "status", status);
        ordersTable.put(id, row);
        emit(new ChangeEvent("orders", "INSERT", null, row));
    }

    static void updateOrderStatus(String id, String newStatus) {
        Map<String, Object> before = ordersTable.get(id);
        Map<String, Object> after = Map.of("id", id, "status", newStatus);
        ordersTable.put(id, after);
        emit(new ChangeEvent("orders", "UPDATE", before, after));
    }

    public static void main(String[] args) {
        consumers.add(e -> {
            if (e.op().equals("UPDATE")) {
                System.out.println("  reporting consumer: status changed from " + e.before().get("status")
                        + " to " + e.after().get("status"));
            } else {
                System.out.println("  reporting consumer: new order, status=" + e.after().get("status"));
            }
        });

        insertOrder("order-1", "PENDING");
        updateOrderStatus("order-1", "SHIPPED");
    }
}
```

How to run: `java CdcWithUpdatesAndDeletes.java`

`updateOrderStatus` captures the row's state *before* the change and constructs the new state *after*, and `emit` bundles both into one `ChangeEvent`. The consumer inspects `e.op()` to distinguish `INSERT` from `UPDATE`, and for updates it can report exactly what changed (`"PENDING"` to `"SHIPPED"`) by comparing `before` and `after` — information a plain "here's the new row" event wouldn't carry.

### Level 3 — Advanced

```java
// File: CdcConsumerReconciliation.java -- a consumer MISSES one update
// (simulating a dropped event or an outage) and its local projection
// silently drifts out of sync; a periodic RECONCILIATION pass compares
// against the source and self-heals the drift.
import java.util.*;

public class CdcConsumerReconciliation {
    static Map<String, String> ordersTable = new HashMap<>(); // source of truth
    static Map<String, String> searchIndexProjection = new HashMap<>(); // downstream, CDC-fed copy

    static void updateOrderStatus(String id, String newStatus, boolean deliverToConsumer) {
        ordersTable.put(id, newStatus);
        if (deliverToConsumer) {
            searchIndexProjection.put(id, newStatus); // normal path: consumer receives and applies the event
            System.out.println("CDC event delivered and applied: " + id + " -> " + newStatus);
        } else {
            System.out.println("CDC event for " + id + " -> " + newStatus + " LOST (simulated outage) -- projection now STALE");
        }
    }

    static void reconcile() { // periodic self-healing pass: compare projection against source of truth
        System.out.println("reconciliation pass: comparing searchIndexProjection against ordersTable...");
        for (Map.Entry<String, String> sourceEntry : ordersTable.entrySet()) {
            String projected = searchIndexProjection.get(sourceEntry.getKey());
            if (!sourceEntry.getValue().equals(projected)) {
                System.out.println("  DRIFT detected for " + sourceEntry.getKey() + ": projection had '" + projected
                        + "', source has '" + sourceEntry.getValue() + "' -- correcting");
                searchIndexProjection.put(sourceEntry.getKey(), sourceEntry.getValue());
            }
        }
    }

    public static void main(String[] args) {
        updateOrderStatus("order-1", "PENDING", true);
        updateOrderStatus("order-1", "SHIPPED", false); // simulated LOST event -- projection stays at PENDING
        updateOrderStatus("order-1", "DELIVERED", true); // this one IS delivered, but on top of a stale prior state

        System.out.println("Before reconciliation -- source: " + ordersTable.get("order-1")
                + ", projection: " + searchIndexProjection.get("order-1") + " (may still be wrong)");

        reconcile();

        System.out.println("After reconciliation -- source: " + ordersTable.get("order-1")
                + ", projection: " + searchIndexProjection.get("order-1"));
    }
}
```

How to run: `java CdcConsumerReconciliation.java`

The second `updateOrderStatus` call passes `deliverToConsumer=false`, simulating a dropped CDC event — `ordersTable` advances to `"SHIPPED"` but `searchIndexProjection` is never told, staying at `"PENDING"`. The third call *is* delivered, directly setting the projection to `"DELIVERED"` (since this particular event happened to update the whole value, not a diff) — in a more general case a missed intermediate update could leave a projection permanently inconsistent in subtler ways. `reconcile()` then walks every entry in the source of truth and compares it against the projection, printing and correcting any mismatch it finds — this periodic pass is what keeps CDC-fed projections trustworthy over the long run, even in the face of occasionally lost or misapplied events.

## 6. Walkthrough

Trace `CdcConsumerReconciliation.main` in order. **First**, `updateOrderStatus("order-1", "PENDING", true)` sets both `ordersTable` and `searchIndexProjection` to `"PENDING"` — both are in agreement.

**Next**, `updateOrderStatus("order-1", "SHIPPED", false)` runs: `ordersTable` is updated to `"SHIPPED"`, but because `deliverToConsumer` is `false`, the `else` branch runs instead of updating `searchIndexProjection` — the projection is now silently stale at `"PENDING"` while the source has moved on.

**Then**, `updateOrderStatus("order-1", "DELIVERED", true)` runs: `ordersTable` advances to `"DELIVERED"`, and this time the event *is* delivered, so `searchIndexProjection` is also set to `"DELIVERED"` directly. Because this example applies whole-value updates rather than incremental diffs, the projection happens to end up matching the source here — but the earlier drop still represents a real information loss a more complex, diff-based system would expose as incorrect state.

**`main` then prints both values before reconciliation**, showing them already matching in this specific run — illustrating that drift can be subtle and not always immediately visible from spot-checking one field.

**Finally**, `reconcile()` runs, iterating every key in `ordersTable` and comparing its value against `searchIndexProjection`. For `"order-1"`, `sourceEntry.getValue()` (`"DELIVERED"`) equals `projected` (`"DELIVERED"`), so no correction is needed in this particular run — but the same `reconcile` logic would have caught and fixed a genuine mismatch had one existed, which is precisely its purpose: a periodic, source-of-truth-driven safety net underneath the event-driven CDC feed.

```
updateOrderStatus(PENDING, delivered=true)   -> source=PENDING,  projection=PENDING   (in sync)
updateOrderStatus(SHIPPED, delivered=false)  -> source=SHIPPED,  projection=PENDING   (DRIFT, silent)
updateOrderStatus(DELIVERED, delivered=true) -> source=DELIVERED,projection=DELIVERED (this update overwrote the drift)
reconcile()                                  -> compares source vs projection -> corrects any remaining drift
```

## 7. Gotchas & takeaways

> CDC couples a consumer to another service's internal table schema, which was never designed as a stable public contract — a column rename or table restructuring done for purely internal reasons can silently break every downstream CDC consumer. The [transactional outbox pattern](0331-transactional-outbox-pattern.md)'s explicit, versioned event schema avoids this exact risk, at the cost of requiring deliberate authoring of each event.

- CDC captures every row-level change from a table's transaction log and turns it into a structured event stream, without requiring application code changes.
- It is powerful for retrofitting event-driven integration onto existing tables, but couples consumers to another service's internal schema rather than an explicit, owned event contract.
- Periodic reconciliation — comparing a CDC-fed projection against its source of truth and correcting any drift — is a valuable safety net against dropped or misapplied events over the long run.
- CDC is most commonly implemented via [transaction log tailing](0332-transaction-log-tailing.md); tools like Debezium package this mechanism for common databases (MySQL, Postgres, MongoDB, and others).
