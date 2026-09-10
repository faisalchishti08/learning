---
card: system-design
gi: 204
slug: transactional-outbox
title: Transactional outbox
---

## 1. What it is

The **transactional outbox** pattern solves the problem of atomically updating a database *and* publishing an event about that update. Instead of writing to the database and then separately publishing to a message broker (two operations that can fail independently), a service writes the event into an **outbox table**, in the *same* local database transaction as the actual data change. A separate process then reads the outbox table and publishes each event to the broker.

## 2. Why & when

A service that updates its database and then calls `broker.publish(event)` afterward has a real gap: if the process crashes, or the broker is unreachable, right between the database commit and the publish call, the database change succeeds but the event never goes out. Any other service that was supposed to react to that event — inventory reservation, an email, a saga's next step — never runs, and nothing in the system even knows an event was missed.

The transactional outbox closes that gap by writing the event as a row in a table, in the exact same local transaction as the business data change. Because both writes are in one transaction, either both commit or neither does — there is no window where one happened and the other did not. A separate relay process then reads unpublished outbox rows and sends them to the broker, retrying until it succeeds. Use this pattern any time a service must reliably publish an event as a result of updating its own data — which is most services in an [event-driven architecture](0200-event-driven-architecture.md) or a [saga](0203-saga-orchestration-vs-choreography.md).

## 3. Core concept

- **The outbox table.** A normal table in the same database as the business data, typically with columns like `id`, `event_type`, `payload`, `created_at`, `published_at` (null until sent).
- **Single local transaction.** The business data write (e.g. `INSERT INTO orders`) and the outbox row write (`INSERT INTO outbox`) happen in one `BEGIN ... COMMIT` block. The database's own atomicity guarantee — not a distributed transaction — is what makes this safe.
- **The relay (or "message relay") process.** A separate poller, or a database change-data-capture (CDC) tool reading the transaction log, picks up outbox rows where `published_at IS NULL`, sends each to the broker, and marks it published (or deletes it) only after the broker confirms receipt.
- **At-least-once delivery, again.** If the relay crashes after publishing but before marking the row published, it will publish the same row again on restart — this is the same at-least-once guarantee as [event-driven architecture](0200-event-driven-architecture.md), and subscribers must be idempotent for the same reason.
- **No distributed transaction needed.** The pattern's whole value is avoiding a two-phase-commit-style distributed transaction between the database and the broker — the local database transaction is enough, because the event is just data until the relay sends it.

## 4. Diagram

```
  Service                                              Message Broker
     |
     |  BEGIN TRANSACTION
     |    INSERT INTO orders (...)              <- business data change
     |    INSERT INTO outbox (event, payload)   <- event, same transaction
     |  COMMIT                                       (both succeed, or both roll back)
     |
     v
  +----------------------+
  |   orders table        |
  |   outbox table         |
  |   (published_at=NULL)  |
  +-----------+-----------+
              |
              |   Relay process polls:
              |   SELECT * FROM outbox WHERE published_at IS NULL
              v
       +--------------+
       |    Relay      |----- publish event ------------------> Broker
       +--------------+
              |
              v
   UPDATE outbox SET published_at = now()   (only after broker confirms)
```
*Caption: the business write and the outbox write are one atomic unit. The relay's job — reading the outbox and publishing — happens entirely afterward, and can be retried safely if it fails.*

## 5. Runnable example

**Level 1 — Basic.** A single local "transaction" (simulated) that writes both the order and the outbox event atomically.

**Level 2 — Intermediate.** A relay process that polls the outbox table and publishes unpublished rows, marking them published.

**Level 3 — Advanced.** Simulate the relay crashing after publishing but before marking the row published, and show the resulting duplicate delivery, handled by an idempotent subscriber.

```java
// TransactionalOutboxDemo.java
import java.util.*;

public class TransactionalOutboxDemo {

    record Order(String id, String customerId, double amount) {}
    static class OutboxRow {
        String id, eventType, payload;
        boolean published = false;
        OutboxRow(String id, String eventType, String payload) {
            this.id = id; this.eventType = eventType; this.payload = payload;
        }
    }

    // ---------- Level 1: one atomic local transaction covers both writes ----------
    static class Database {
        Map<String, Order> orders = new HashMap<>();
        List<OutboxRow> outbox = new ArrayList<>();

        // Simulates BEGIN ... COMMIT: both writes succeed together, or (if an exception
        // is thrown before this method returns) neither is kept - a real DB enforces this
        // automatically; here we just perform both writes with nothing in between that can fail.
        void placeOrderTransactionally(Order order) {
            orders.put(order.id(), order);
            outbox.add(new OutboxRow("evt-" + order.id(), "OrderPlaced",
                "{orderId=" + order.id() + ", amount=" + order.amount() + "}"));
            System.out.println("  [DB txn] committed order " + order.id() + " AND its outbox row together");
        }
    }

    // ---------- Level 2: relay polls the outbox and publishes ----------
    interface Broker {
        void publish(String eventType, String payload);
    }
    static class LoggingBroker implements Broker {
        Set<String> receivedIds = new HashSet<>(); // subscriber-side idempotency tracking
        public void publish(String eventType, String payload) {
            System.out.println("    [broker] delivered " + eventType + " " + payload);
        }
    }

    static class Relay {
        Database db;
        Broker broker;
        Relay(Database db, Broker broker) { this.db = db; this.broker = broker; }

        void pollAndPublish() {
            for (OutboxRow row : db.outbox) {
                if (row.published) continue;
                broker.publish(row.eventType, row.payload);
                row.published = true; // marked only AFTER the broker call returns successfully
                System.out.println("    [relay] marked " + row.id + " as published");
            }
        }
    }

    // ---------- Level 3: relay crashes AFTER publish, BEFORE marking published ----------
    static class CrashProneRelay {
        Database db;
        Broker broker;
        Set<String> subscriberProcessedIds = new HashSet<>(); // idempotent subscriber, keyed by outbox row id
        CrashProneRelay(Database db, Broker broker) { this.db = db; this.broker = broker; }

        void pollAndPublish(boolean simulateCrashBeforeMarking) {
            for (OutboxRow row : db.outbox) {
                if (row.published) continue;
                broker.publish(row.eventType, row.payload);
                if (simulateCrashBeforeMarking) {
                    System.out.println("    [relay] CRASHED before marking " + row.id + " as published!");
                    return; // row.published stays false - relay will re-send it next run
                }
                row.published = true;
            }
        }

        void subscriberHandle(OutboxRow row) {
            if (subscriberProcessedIds.contains(row.id)) {
                System.out.println("    [subscriber] already processed " + row.id + " - skipping (idempotent)");
                return;
            }
            System.out.println("    [subscriber] processing " + row.id + " for the first time");
            subscriberProcessedIds.add(row.id);
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - atomic write of business data + outbox event:");
        Database db1 = new Database();
        db1.placeOrderTransactionally(new Order("ORD-1", "cust-1", 42.00));

        System.out.println("\nLevel 2 - relay polls outbox and publishes:");
        Broker broker2 = new LoggingBroker();
        Relay relay = new Relay(db1, broker2);
        relay.pollAndPublish();
        relay.pollAndPublish(); // second poll: nothing new, row already marked published

        System.out.println("\nLevel 3 - relay crashes before marking published -> duplicate delivery, handled idempotently:");
        Database db3 = new Database();
        db3.placeOrderTransactionally(new Order("ORD-2", "cust-2", 15.00));
        Broker broker3 = new LoggingBroker();
        CrashProneRelay crashRelay = new CrashProneRelay(db3, broker3);
        crashRelay.pollAndPublish(true);  // publishes, then "crashes" before marking
        System.out.println("  ...relay restarts and polls again...");
        crashRelay.pollAndPublish(false); // same row published AGAIN, since it was never marked
        System.out.println("  now the subscriber, processing both deliveries of the same event:");
        crashRelay.subscriberHandle(db3.outbox.get(0));
        crashRelay.subscriberHandle(db3.outbox.get(0));
    }
}
```

**How to run:** `java TransactionalOutboxDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `placeOrderTransactionally(...)` writes to `orders` and appends to `outbox` with nothing that can fail in between — this stands in for a real `BEGIN...COMMIT` block, where the database guarantees both writes land together or neither does.
2. **Level 2:** `relay.pollAndPublish()` loops over `db1.outbox`, finds the one unpublished row, calls `broker.publish(...)`, and only then sets `row.published = true`. Calling `pollAndPublish()` a second time finds nothing to do — the row is already marked, so the relay does not resend it under normal operation.
3. **Level 3** deliberately breaks the "publish, then mark" ordering. `crashRelay.pollAndPublish(true)` calls `broker.publish(...)` — so the broker genuinely receives the event — but then returns immediately without setting `row.published = true`, simulating a process crash at the worst possible moment.
4. **The relay "restarts"** and polls again with `pollAndPublish(false)`. Because `row.published` is still `false`, the loop finds the same row and publishes it **again** — the broker output line for `evt-ORD-2` appears twice in total, proving the event was delivered twice from one business event.
5. **`subscriberHandle(...)` is called twice** with the same `OutboxRow`. The first call finds `row.id` absent from `subscriberProcessedIds`, processes it, and records the ID. The second call finds the ID already present and skips — this idempotency check on the subscriber side is what makes the relay's at-least-once, occasionally-duplicate delivery safe to build on.

## 7. Gotchas & takeaways

> **Gotcha:** the outbox table itself needs cleanup — published rows accumulate forever if nothing deletes or archives them. A background job that removes rows older than some retention window (after confirming they were published) is a required companion to this pattern, not an afterthought.

- The core guarantee is atomicity between the business write and the outbox write, using the database's own transaction — never try to make the broker publish part of that same transaction (that is a distributed transaction, which this pattern exists to avoid).
- The relay can and will occasionally deliver the same event twice — subscribers must be idempotent, exactly as in plain [event-driven architecture](0200-event-driven-architecture.md).
- A change-data-capture (CDC) tool reading the database's write-ahead log (e.g. Debezium) is a common production alternative to a polling relay — it reacts to new outbox rows without repeatedly querying the table.
- This pattern is what makes each step of a [saga](0203-saga-orchestration-vs-choreography.md) reliably publish its "step completed" event — without it, a crash between the local commit and the publish can silently stall the whole saga.
