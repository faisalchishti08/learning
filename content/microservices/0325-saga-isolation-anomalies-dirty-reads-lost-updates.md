---
card: microservices
gi: 325
slug: saga-isolation-anomalies-dirty-reads-lost-updates
title: "Saga isolation anomalies (dirty reads, lost updates)"
---

## 1. What it is

**Saga isolation anomalies** are the specific ways a [saga's](0320-saga-pattern.md) lack of cross-service isolation can produce incorrect results when other operations read or write the same data while the saga is still in flight. The two classic ones, borrowed from database transaction theory, are a **dirty read** (something reads data that a saga's forward step wrote but that might still be undone by a later compensation) and a **lost update** (two operations, one from inside a saga and one from outside it, both write to the same data, and one silently overwrites the other's effect without either knowing).

## 2. Why & when

ACID transactions guarantee **isolation** — a transaction's uncommitted changes are invisible to everyone else until it commits. A saga has no such guarantee: each step commits locally and immediately, becoming visible to the rest of the system well before the whole saga finishes (or before anyone knows if it will finish successfully at all). This is an unavoidable consequence of rejecting cross-service locks (see [why 2PC/XA is avoided in microservices](0318-why-2pc-xa-is-avoided-in-microservices.md)), and it means every saga needs to be designed with the awareness that its intermediate states are real, visible, and actionable by other code — not hidden the way an uncommitted database transaction would be.

You need to actively think about isolation anomalies for any saga whose intermediate data is read by something else — a report, a different saga, a user-facing screen — before the saga fully completes or compensates. [Semantic locks](0324-semantic-locks-countermeasures.md) are the primary tool for preventing these anomalies; this topic is about recognizing which anomaly you're at risk of so you know a semantic lock (or another countermeasure) is needed at all.

## 3. Core concept

A **dirty read** happens when a reader sees a saga's in-progress write and acts on it as if final, and the saga later compensates that write away — the reader acted on data that turned out to be temporary. A **lost update** happens when a saga step and a concurrent, unrelated write both target the same record; whichever writes last wins, silently discarding the other's change, with neither operation aware a conflict occurred.

```java
// Dirty read risk: a report queries "pending" orders mid-saga and counts one
// that will be cancelled moments later by the saga's own compensation.
// Lost update risk: the saga's own step and an unrelated customer edit both
// write the same order row; the LAST write wins, silently dropping the other.
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Timeline showing a saga placing an order, a report reading it as final (dirty read), then the saga compensating and cancelling the order, leaving the report's earlier count wrong">
  <line x1="40" y1="100" x2="600" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <circle cx="100" cy="100" r="5" fill="#3fb950"/>
  <text x="100" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">saga: order PLACED</text>

  <circle cx="280" cy="100" r="5" fill="#f0883e"/>
  <text x="280" y="120" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">report reads order as final (DIRTY READ)</text>

  <circle cx="460" cy="100" r="5" fill="#f85149"/>
  <text x="460" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">saga compensates: order CANCELLED</text>

  <text x="330" y="170" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Report already counted the order -- now WRONG, and nothing tells it to recheck.</text>

  <defs><marker id="a325" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A reader that observes a saga's intermediate state as final can be left holding a stale conclusion once the saga later compensates.

## 5. Runnable example

Scenario: a revenue report that dirty-reads an order mid-saga and later a customer address update that's silently lost to a concurrent saga step — first shown as bugs, then fixed with a semantic-lock-aware report, then fixed with an optimistic-concurrency check that detects the lost update instead of silently losing it.

### Level 1 — Basic

```java
// File: DirtyReadBug.java -- a revenue report counts an order mid-saga,
// which the saga's own compensation later cancels -- the report is now wrong.
import java.util.*;

public class DirtyReadBug {
    enum Status { PENDING, CONFIRMED, CANCELLED }
    record Order(String id, double amount, Status status) {}
    static Map<String, Order> orders = new HashMap<>();

    static double totalConfirmedRevenue() { // BUG: counts PENDING orders too, not just CONFIRMED
        double total = 0;
        for (Order o : orders.values()) if (o.status() != Status.CANCELLED) total += o.amount();
        return total;
    }

    public static void main(String[] args) {
        orders.put("order-1", new Order("order-1", 100.0, Status.PENDING)); // saga step 1: order placed, payment NOT yet confirmed

        double reportedRevenue = totalConfirmedRevenue(); // DIRTY READ: counts the still-pending order
        System.out.println("Report (mid-saga): total revenue = $" + reportedRevenue + " -- includes an UNCONFIRMED order!");

        orders.put("order-1", new Order("order-1", 100.0, Status.CANCELLED)); // saga's payment step fails -> compensates
        System.out.println("Saga later cancels order-1 -- but the report was ALREADY generated and is now WRONG.");
    }
}
```

How to run: `java DirtyReadBug.java`

`totalConfirmedRevenue` treats any non-`CANCELLED` order as revenue, which incorrectly includes `PENDING` orders — those still mid-saga, with payment not yet confirmed. The report runs and includes `order-1`'s `$100.0` while it is still `PENDING`; moments later the saga's compensation cancels the order, but the already-generated report has no way to know its number is now stale.

### Level 2 — Intermediate

```java
// File: SemanticLockAwareReport.java -- the report is fixed to check the
// semantic lock itself: it only counts orders that have reached a FINAL,
// non-PENDING state, avoiding the dirty read.
import java.util.*;

public class SemanticLockAwareReport {
    enum Status { PENDING, CONFIRMED, CANCELLED }
    record Order(String id, double amount, Status status) {}
    static Map<String, Order> orders = new HashMap<>();

    static double totalConfirmedRevenue() { // FIXED: only CONFIRMED counts -- PENDING is explicitly excluded
        double total = 0;
        for (Order o : orders.values()) if (o.status() == Status.CONFIRMED) total += o.amount();
        return total;
    }

    public static void main(String[] args) {
        orders.put("order-1", new Order("order-1", 100.0, Status.PENDING)); // still mid-saga

        double reportedRevenue = totalConfirmedRevenue();
        System.out.println("Report (mid-saga): total revenue = $" + reportedRevenue + " -- correctly excludes the PENDING order.");

        orders.put("order-1", new Order("order-1", 100.0, Status.CONFIRMED)); // saga completes successfully
        System.out.println("Report (after saga completes): total revenue = $" + totalConfirmedRevenue()
                + " -- now correctly includes it.");
    }
}
```

How to run: `java SemanticLockAwareReport.java`

By explicitly requiring `status() == Status.CONFIRMED` rather than merely "not cancelled," the report now respects the semantic lock: a `PENDING` order is neither wrongly included nor wrongly excluded forever — it is correctly excluded *while* pending and correctly included once the saga confirms it. Re-running the report after the status flips to `CONFIRMED` shows the correct, updated total.

### Level 3 — Advanced

```java
// File: OptimisticConcurrencyDetectsLostUpdate.java -- a saga step and an
// UNRELATED concurrent customer edit both try to write the same order row;
// a version number DETECTS the conflict instead of silently losing one
// write, so the losing side can retry against the current data.
import java.util.*;

public class OptimisticConcurrencyDetectsLostUpdate {
    record Order(String id, String shippingAddress, Status status, int version) {}
    enum Status { PENDING, CONFIRMED }
    static Map<String, Order> orders = new HashMap<>();

    static boolean write(String id, Order updated, int expectedVersion) {
        Order current = orders.get(id);
        if (current.version() != expectedVersion) { // someone else already wrote a newer version -- CONFLICT
            System.out.println("  CONFLICT: " + id + " is at version " + current.version()
                    + ", expected " + expectedVersion + " -- write REJECTED, not silently overwritten");
            return false;
        }
        orders.put(id, updated);
        return true;
    }

    public static void main(String[] args) {
        orders.put("order-1", new Order("order-1", "123 Main St", Status.PENDING, 1));

        // Both reads happen against version 1, BEFORE either write lands.
        Order sagaView = orders.get("order-1");      // saga's payment-confirmation step read this
        Order customerView = orders.get("order-1");  // customer's address-edit request read this too

        System.out.println("saga: confirming order (based on version " + sagaView.version() + ")");
        boolean sagaWriteOk = write("order-1", new Order("order-1", sagaView.shippingAddress(), Status.CONFIRMED, 2), sagaView.version());
        System.out.println("saga write succeeded? " + sagaWriteOk + " -- new version: " + orders.get("order-1").version());

        System.out.println("customer: updating shipping address (based on STALE version " + customerView.version() + ")");
        boolean customerWriteOk = write("order-1", new Order("order-1", "456 Oak Ave", customerView.status(), 2), customerView.version());
        System.out.println("customer write succeeded? " + customerWriteOk + " -- customer must RETRY against the current version, not silently lose the edit");

        System.out.println("Final order: " + orders.get("order-1"));
    }
}
```

How to run: `java OptimisticConcurrencyDetectsLostUpdate.java`

Both the saga's confirmation step and the customer's address edit read `order-1` at `version=1`. The saga writes first, passing `expectedVersion=1`, which matches the stored version, so the write succeeds and the stored version advances to `2`. When the customer's write then runs, it also passes `expectedVersion=1` (based on its now-stale read) — but the stored order is now at version `2`, so `write` detects the mismatch and rejects it, printing a conflict message instead of silently overwriting the saga's confirmation with a write based on old data. The customer's request fails loudly and must retry against the current data, rather than the classic lost-update bug where the last writer wins silently and one side's change vanishes without anyone noticing.

## 6. Walkthrough

Trace `OptimisticConcurrencyDetectsLostUpdate.main` in order. **First**, `order-1` is stored at `version=1`. **Both** `sagaView` and `customerView` are read immediately after, so both capture `version=1` — this is the setup for the conflict, representing two independent operations that both started from the same, now-about-to-be-stale, snapshot.

**Next**, the saga's write runs: `write("order-1", ..., expectedVersion=1)`. Inside `write`, `current.version()` is `1`, matching `expectedVersion`, so the condition is false, the write proceeds, `orders.put` stores the new order at `version=2`, and `write` returns `true`.

**Then**, the customer's write runs: `write("order-1", ..., expectedVersion=1)` — still using the stale version captured before the saga's write happened. Inside `write` this time, `current.version()` is now `2` (from the saga's write), which does not equal the customer's `expectedVersion` of `1` — the conflict branch fires, prints the mismatch, and returns `false` without modifying `orders`.

**Finally**, `main` prints the final stored order, which reflects the saga's confirmation (`status=CONFIRMED`, `version=2`) with the *original* shipping address — the customer's address change was correctly rejected rather than silently lost, and the customer's request handler (not shown, but implied) would now retry by rereading the current version and reapplying the address change on top of it.

```
order-1 @ v1
   |-- sagaView reads v1        |-- customerView reads v1  (both stale relative to each other)
saga write(expectedVersion=1)      -> MATCHES v1 -> SUCCEEDS, order now @ v2
customer write(expectedVersion=1)  -> v2 != 1     -> REJECTED (conflict detected, not silently lost)
```

## 7. Gotchas & takeaways

> A classic lost update looks like this, without optimistic concurrency: the saga writes `CONFIRMED`, then the customer's stale write overwrites the whole row with `PENDING` data from before the saga ran — the confirmation silently vanishes, and nobody is ever told a conflict happened. Optimistic concurrency (a version number checked on write) turns a silent, invisible bug into a visible, retryable conflict.

- A dirty read happens when something treats a saga's in-flight intermediate state as final; guard against it by checking status (a [semantic lock](0324-semantic-locks-countermeasures.md)) before trusting data that could still be compensated away.
- A lost update happens when two writers, one of them a saga step, both write the same record based on a stale read; a version number (optimistic concurrency control) turns this into a detectable, retryable conflict instead of silent data loss.
- These anomalies exist specifically because sagas trade cross-service isolation for availability — see [why 2PC/XA is avoided in microservices](0318-why-2pc-xa-is-avoided-in-microservices.md).
- Both anomalies are addressed with the same family of tools: explicit status fields, version numbers, and countermeasures designed alongside the saga itself, not bolted on after a bug is found in production.
