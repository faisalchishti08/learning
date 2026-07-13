---
card: microservices
gi: 156
slug: transactional-outbox-via-spring-debezium-cdc
title: "Transactional outbox via Spring + debezium / CDC"
---

## 1. What it is

The transactional outbox pattern writes an event to an "outbox" table in the *same* local database transaction as the business data change it describes, guaranteeing the two either both commit or both roll back together; a separate mechanism — commonly Debezium, a change data capture (CDC) tool reading the database's own transaction log — then reliably publishes each outbox row as a real message to a broker, asynchronously and independently of the original transaction.

## 2. Why & when

Publishing a message to a broker and committing a database change are two genuinely separate operations against two separate systems, and doing them as two independent steps (commit the database change, then separately call the broker) creates an unavoidable gap: a crash between the two leaves either a database change with no corresponding event ever published, or — if the ordering is reversed — a published event whose corresponding database change never actually committed. The transactional outbox closes this gap by making the *only* externally-observable write an ordinary row in an ordinary database table, committed atomically with the business data using the database's own transaction guarantees — no distributed transaction across two different systems is needed, because the "event" is just another local database write.

Reach for this pattern whenever a service needs to reliably publish an event that must never disagree with a local database change it's derived from — order placement triggering an `OrderPlaced` event, payment capture triggering a `PaymentCaptured` event — which is essentially any event-driven microservice with its own database. It is unnecessary for services with no local database of record, or for events that don't need to correspond precisely to a committed local state change.

## 3. Core concept

A single local database transaction writes both the business entity change and a corresponding row in an outbox table; a CDC tool like Debezium tails the database's transaction log (not the application, and not a second network call) and publishes each new outbox row to the broker as it's committed, guaranteeing at-least-once delivery of exactly the events that were genuinely, durably committed.

```java
@Transactional // ONE local transaction covers BOTH writes
void placeOrder(Order order) {
    orderRepository.save(order);                              // business data write
    outboxRepository.save(new OutboxEvent("OrderPlaced", order.toJson())); // event write, SAME transaction
} // if this transaction commits, BOTH rows exist; if it rolls back, NEITHER does -- no gap possible

// separately, entirely outside the application: Debezium tails the DB's transaction log
// and publishes each committed outbox row to Kafka, reliably, asynchronously
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single local transaction writes both the order row and an outbox event row atomically; Debezium, reading the database's transaction log independently, picks up the committed outbox row and publishes it to Kafka -- no distributed transaction between the database and broker is ever needed">
  <rect x="20" y="20" width="260" height="90" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="40" fill="#8b949e" font-size="8" font-family="sans-serif">ONE local transaction</text>
  <rect x="35" y="55" width="100" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="76" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">orders table</text>
  <rect x="150" y="55" width="115" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="207" y="76" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">outbox table</text>

  <rect x="330" y="55" width="140" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="400" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Debezium (tails txn log)</text>

  <rect x="510" y="55" width="110" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="565" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Kafka</text>

  <line x1="280" y1="75" x2="328" y2="75" stroke="#8b949e" marker-end="url(#arr37)"/>
  <line x1="470" y1="75" x2="508" y2="75" stroke="#8b949e" marker-end="url(#arr37)"/>
  <text x="400" y="150" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">the ONLY cross-system write is an ordinary, atomic, local database transaction</text>

  <defs>
    <marker id="arr37" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Both table writes commit or roll back together; CDC bridges the gap to the broker entirely outside the original transaction.

## 5. Runnable example

Scenario: an order-placement flow that starts by publishing to a broker as a separate step after a database commit (demonstrating the exact gap the outbox pattern closes, including a simulated crash), switches to the transactional outbox pattern with both writes in one atomic transaction, and finally adds a simulated CDC poller that reliably publishes committed outbox rows independently of the original request, proving the two concerns are genuinely decoupled.

### Level 1 — Basic

```java
// File: SeparateCommitAndPublish.java -- database commit and broker publish as
// TWO independent steps; a crash between them creates a permanent gap.
import java.util.*;

public class SeparateCommitAndPublish {
    static List<String> ordersTable = new ArrayList<>(); // stands in for the database
    static List<String> publishedToBroker = new ArrayList<>();

    static void placeOrder(String orderData, boolean simulateCrashBeforePublish) {
        ordersTable.add(orderData); // STEP 1: commit to the database -- this succeeds
        System.out.println("Order committed to database: " + orderData);

        if (simulateCrashBeforePublish) {
            System.out.println("*** CRASH before the broker publish call ever happens ***");
            return; // the process dies here -- publishedToBroker.add(...) below NEVER runs
        }
        publishedToBroker.add(orderData); // STEP 2: a SEPARATE network call to the broker
        System.out.println("Event published to broker: " + orderData);
    }

    public static void main(String[] args) {
        placeOrder("OrderPlaced:42", true); // crash simulated
        System.out.println("Orders table: " + ordersTable);
        System.out.println("Broker received: " + publishedToBroker);
        System.out.println("BUG: order 42 is DURABLY committed, but NO downstream service will EVER know it happened.");
    }
}
```

**How to run:** `javac SeparateCommitAndPublish.java && java SeparateCommitAndPublish` (JDK 17+).

Expected output:
```
Order committed to database: OrderPlaced:42
*** CRASH before the broker publish call ever happens ***
Orders table: [OrderPlaced:42]
Broker received: []
BUG: order 42 is DURABLY committed, but NO downstream service will EVER know it happened.
```

### Level 2 — Intermediate

```java
// File: TransactionalOutbox.java -- BOTH the order row and an outbox event row
// written in ONE atomic transaction; the crash point from Level 1 can no longer create a gap.
import java.util.*;

public class TransactionalOutbox {
    static class Database {
        List<String> ordersTable = new ArrayList<>();
        List<String> outboxTable = new ArrayList<>();

        // simulates a SINGLE local transaction covering BOTH writes -- atomic: all or nothing
        void placeOrderTransactionally(String orderData, String outboxEvent, boolean simulateCrashMidTransaction) {
            List<String> pendingOrders = new ArrayList<>(ordersTable);
            List<String> pendingOutbox = new ArrayList<>(outboxTable);
            pendingOrders.add(orderData);
            pendingOutbox.add(outboxEvent);

            if (simulateCrashMidTransaction) {
                System.out.println("*** CRASH mid-transaction -- NEITHER write is committed (atomic rollback) ***");
                return; // neither ordersTable nor outboxTable is updated -- the transaction never committed
            }
            // COMMIT: both changes become visible together
            ordersTable = pendingOrders;
            outboxTable = pendingOutbox;
            System.out.println("Transaction committed: order row AND outbox row, BOTH present together.");
        }
    }

    public static void main(String[] args) {
        Database db = new Database();
        db.placeOrderTransactionally("OrderPlaced:42", "outbox:OrderPlaced:42", false); // succeeds

        System.out.println("Orders table: " + db.ordersTable);
        System.out.println("Outbox table: " + db.outboxTable);
        System.out.println("The outbox row's mere EXISTENCE is now durable proof the order was committed -- no separate broker call was needed to establish that fact.");
    }
}
```

**How to run:** `javac TransactionalOutbox.java && java TransactionalOutbox` (JDK 17+).

Expected output:
```
Transaction committed: order row AND outbox row, BOTH present together.
Orders table: [OrderPlaced:42]
Outbox table: [outbox:OrderPlaced:42]
The outbox row's mere EXISTENCE is now durable proof the order was committed -- no separate broker call was needed to establish that fact.
```

### Level 3 — Advanced

```java
// File: CdcPollerPublishesIndependently.java -- a simulated CDC poller (standing in
// for Debezium) reliably publishes committed outbox rows to a broker, ENTIRELY
// independent of the original request that created them -- proving the decoupling.
import java.util.*;

public class CdcPollerPublishesIndependently {
    static class Database {
        List<String> ordersTable = new ArrayList<>();
        List<String> outboxTable = new ArrayList<>(); // Debezium tails changes to THIS table

        void placeOrderTransactionally(String orderData, String outboxEvent) {
            ordersTable.add(orderData);
            outboxTable.add(outboxEvent); // ONE transaction, both writes -- as in Level 2
            System.out.println("Transaction committed: " + orderData);
        }
    }

    // simulates Debezium: periodically polls for NEW outbox rows and publishes them,
    // COMPLETELY independent of the original HTTP request/transaction that created them
    static class CdcPoller {
        int lastPublishedIndex = 0;
        List<String> publishedToBroker = new ArrayList<>();

        void poll(Database db) {
            while (lastPublishedIndex < db.outboxTable.size()) {
                String event = db.outboxTable.get(lastPublishedIndex);
                publishedToBroker.add(event);
                System.out.println("[CDC poller] published to broker: " + event);
                lastPublishedIndex++;
            }
        }
    }

    public static void main(String[] args) {
        Database db = new Database();
        CdcPoller cdcPoller = new CdcPoller();

        // the ORIGINAL request commits and returns to its caller WITHOUT waiting for any broker publish
        db.placeOrderTransactionally("OrderPlaced:42", "outbox:OrderPlaced:42");
        System.out.println("Original request finished -- caller received a response. Broker has NOT been touched yet.");

        // SEPARATELY, and later, the CDC poller notices the new outbox row and publishes it
        System.out.println("--- some time later, independently ---");
        cdcPoller.poll(db);

        // a SECOND order arrives; the poller picks up ONLY the new row, not a re-publish of the first
        db.placeOrderTransactionally("OrderPlaced:43", "outbox:OrderPlaced:43");
        cdcPoller.poll(db);

        System.out.println("Broker ultimately received: " + cdcPoller.publishedToBroker);
        System.out.println("The original request's latency was NEVER coupled to broker availability or publish latency.");
    }
}
```

**How to run:** `javac CdcPollerPublishesIndependently.java && java CdcPollerPublishesIndependently` (JDK 17+).

Expected output:
```
Transaction committed: OrderPlaced:42
Original request finished -- caller received a response. Broker has NOT been touched yet.
--- some time later, independently ---
[CDC poller] published to broker: outbox:OrderPlaced:42
Transaction committed: OrderPlaced:43
[CDC poller] published to broker: outbox:OrderPlaced:43
Broker ultimately received: [outbox:OrderPlaced:42, outbox:OrderPlaced:43]
```

## 6. Walkthrough

1. **Level 1** — `placeOrder` performs the database write and the broker publish as two sequential, entirely independent operations; the simulated crash between them leaves `ordersTable` containing the order but `publishedToBroker` permanently empty — a real, unrecoverable gap.
2. **Level 2, atomicity via a single local transaction** — `placeOrderTransactionally` builds both `pendingOrders` and `pendingOutbox` before committing either; the simulated mid-transaction crash discards *both* pending lists without ever updating the real `ordersTable` or `outboxTable`, meaning there is no possible crash point that leaves one written without the other.
3. **Level 2, the outbox row as durable proof** — once a transaction *does* commit successfully, `outboxTable` contains a row that, by construction, could only exist if the corresponding order row was also committed in that same transaction — this durable co-existence is what later lets a separate process trust the outbox table completely.
4. **Level 3, the CDC poller as a wholly separate concern** — `CdcPoller.poll` reads from `db.outboxTable` using its own tracked `lastPublishedIndex`, entirely independent of whatever code path originally called `placeOrderTransactionally`; nothing in `placeOrderTransactionally` calls or waits on `CdcPoller` at all.
5. **Level 3, the request completing without waiting on the broker** — the printed line `"Original request finished -- caller received a response. Broker has NOT been touched yet."` appears immediately after the transaction commits and before `cdcPoller.poll` is ever called, directly demonstrating that the original caller's latency was determined solely by the local database transaction, not by any broker round-trip.
6. **Level 3, the poller catching up later, and only on new rows** — the first `cdcPoller.poll(db)` call publishes exactly the one outbox row that existed at that point; after a second order is placed, the second `poll` call publishes only the *new* row (tracked via `lastPublishedIndex`), never re-publishing the first one — mirroring how Debezium tracks its own position in the database's transaction log and only emits genuinely new committed changes.
7. **Level 3, the overall guarantee demonstrated** — by the end, `cdcPoller.publishedToBroker` contains both events, published reliably and in the order they were committed, despite the original requests never having made a single direct call to any broker — the atomicity guarantee from Level 2 plus the independent, reliable CDC publishing from Level 3 together close the exact gap Level 1 exposed, without ever requiring a distributed transaction spanning the database and the broker.

## 7. Gotchas & takeaways

> **Gotcha:** the outbox table needs its own cleanup strategy — rows accumulate forever unless something (a scheduled job, or Debezium's own configuration) deletes or archives already-published rows, and an unbounded outbox table eventually becomes its own storage and query-performance problem, quietly undermining the pattern's operational simplicity if left unmanaged.

- The transactional outbox pattern writes an event to an outbox table in the same local database transaction as the business data change it describes, using the database's own atomicity guarantee instead of a distributed transaction across the database and a broker.
- A CDC tool like Debezium, reading the database's transaction log directly, reliably publishes committed outbox rows to a broker entirely independently of the original request that created them.
- This closes the gap that a naive "commit, then separately call the broker" approach leaves open: a crash between those two steps can no longer create a database change with no corresponding published event.
- The original request's latency is decoupled from broker availability or publish latency, since the request only needs the local database transaction to succeed, not a network round-trip to the broker.
- The outbox table needs a deliberate cleanup or archival strategy; without one, it grows without bound and becomes its own operational liability over time.
