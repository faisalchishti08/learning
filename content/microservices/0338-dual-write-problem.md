---
card: microservices
gi: 338
slug: dual-write-problem
title: "Dual-write problem"
---

## 1. What it is

The **dual-write problem** is the general failure mode that arises whenever a single logical operation must write to two separate systems — most commonly a database and a message broker — with no shared transaction covering both. Because the two writes are independent, one can succeed while the other fails, leaving the two systems permanently disagreeing about what happened: the database says an order was placed, but no event was ever published, or an event was published for a database write that then failed to commit.

## 2. Why & when

This problem shows up constantly in microservices because publishing an event after a database change is one of the most common things a service does — it's how [sagas](0320-saga-pattern.md) coordinate, how [read models stay in sync](0315-keeping-read-models-in-sync-via-events.md), how a [reporting database](0316-reporting-analytics-database.md) learns about new data. Any code that does `db.save(...)` followed by `broker.publish(...)` as two separate calls has this problem lurking, whether or not it's ever been triggered in practice — a network blip, a process crash between the two calls, or a broker outage at exactly the wrong moment will eventually expose it.

Recognize the dual-write problem any time you see a database write followed by a separate call to an external system (a message broker, another service's API, a cache) that isn't wrapped in the same transaction as the database write. It needs a real architectural fix — not a `try/catch` around the second call, which can only paper over the symptom (a caught exception still leaves the database and the broker disagreeing; it just makes the failure quieter).

## 3. Core concept

The problem exists because a service's local database transaction and a call to an external system are two different failure domains with no shared atomicity — there is no way to make "commit the database write" and "successfully call the broker" a single all-or-nothing operation without one of them going through an intermediary that participates in the local transaction, which is exactly what the [transactional outbox pattern](0331-transactional-outbox-pattern.md) provides.

```java
// The problem, structurally:
db.save(order);          // succeeds
broker.publish(event);   // FAILS -- now db and broker permanently disagree, and nothing detects this
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A database write succeeds, then a separate broker publish call fails; the database and the broker are now permanently out of sync, with no shared transaction to prevent this">
  <rect x="30" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="120" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">db.save() -- SUCCEEDS</text>

  <rect x="430" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="520" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">broker.publish() -- FAILS</text>

  <line x1="210" y1="50" x2="425" y2="50" stroke="#8b949e" stroke-dasharray="4,4"/>
  <text x="320" y="40" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">NO shared transaction</text>

  <text x="320" y="120" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Order exists in the database. No event was ever published.</text>
  <text x="320" y="140" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Every downstream consumer of that event never learns this order exists.</text>
</svg>

Two independent writes with no shared transaction can diverge — one commits, the other fails, and nothing automatically detects or corrects it.

## 5. Runnable example

Scenario: an order-placement flow that first demonstrates the dual-write problem directly, then a naive attempted fix (retry the publish in a catch block, which is still not fully safe), and finally the real fix using a transactional outbox to make both writes atomic.

### Level 1 — Basic

```java
// File: DualWriteFailsSilently.java -- database write succeeds, broker
// publish fails; the two systems now disagree, and NOTHING notices.
import java.util.*;

public class DualWriteFailsSilently {
    static Map<String, String> ordersDb = new HashMap<>();
    static List<String> publishedEvents = new ArrayList<>();

    static void placeOrder(String orderId, boolean brokerIsDown) {
        ordersDb.put(orderId, "PLACED"); // write 1: SUCCEEDS
        System.out.println("db: order " + orderId + " saved");

        if (brokerIsDown) {
            System.out.println("broker: publish call FAILED -- caller sees an exception, but the DB write ALREADY committed");
            return; // db.save() cannot be undone from here -- it already committed
        }
        publishedEvents.add("OrderPlaced:" + orderId); // write 2: only reached if the broker is up
    }

    public static void main(String[] args) {
        placeOrder("order-1", true);
        System.out.println("Order in DB: " + ordersDb.containsKey("order-1") + ", event published: "
                + publishedEvents.contains("OrderPlaced:order-1") + " -- these two facts now PERMANENTLY disagree.");
    }
}
```

How to run: `java DualWriteFailsSilently.java`

The database write and the broker publish are separate, sequential operations. The database write commits unconditionally; the broker call, simulated as failing, leaves `publishedEvents` untouched. The order genuinely exists, but no other service will ever learn that via the expected event — this is the dual-write problem in its purest form.

### Level 2 — Intermediate

```java
// File: RetryInCatchIsNotEnough.java -- a naive attempted fix: retry the
// publish call if it fails. This HELPS but is still not fully safe,
// because the retry itself can ALSO fail, or the process can crash
// between the db write and the retry ever running.
import java.util.*;

public class RetryInCatchIsNotEnough {
    static Map<String, String> ordersDb = new HashMap<>();
    static List<String> publishedEvents = new ArrayList<>();
    static int brokerFailuresRemaining = 2; // simulates the broker being down for TWO attempts

    static boolean tryPublish(String orderId) {
        if (brokerFailuresRemaining > 0) { brokerFailuresRemaining--; return false; }
        publishedEvents.add("OrderPlaced:" + orderId);
        return true;
    }

    static void placeOrderWithRetry(String orderId, int maxRetries) {
        ordersDb.put(orderId, "PLACED");
        System.out.println("db: order " + orderId + " saved");

        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            if (tryPublish(orderId)) { System.out.println("broker: publish succeeded on attempt " + attempt); return; }
            System.out.println("broker: publish attempt " + attempt + " FAILED, retrying...");
            // if the PROCESS CRASHES here, between attempts, the retry loop never resumes -- still unsafe!
        }
        System.out.println("broker: publish FAILED after " + maxRetries + " attempts -- gave up, event STILL lost.");
    }

    public static void main(String[] args) {
        placeOrderWithRetry("order-1", 3); // succeeds on the 3rd attempt, but ONLY because we happened to retry enough times

        brokerFailuresRemaining = 5; // now simulate a broker outage that outlasts our retry budget
        placeOrderWithRetry("order-2", 3); // gives up after 3 attempts -- STILL lost, just less often
    }
}
```

How to run: `java RetryInCatchIsNotEnough.java`

`order-1` succeeds because the retry loop happens to outlast the simulated 2 failures. `order-2` simulates a longer outage (5 failures) that exceeds `maxRetries=3`, so the loop gives up and the event is still lost — retrying reduces how *often* the problem occurs but does not structurally fix it, and a process crash mid-retry (not even modeled here) would lose the event just as surely as no retry at all, since the retry state itself only lives in memory, not durably tied to the database write.

### Level 3 — Advanced

```java
// File: FixedWithTransactionalOutbox.java -- the REAL fix: the order
// write and the outbox event write happen in ONE local transaction, so
// they are atomic; a SEPARATE relay reliably drains the outbox whenever
// the broker is available, with no dependency on the original request's
// lifetime.
import java.util.*;

public class FixedWithTransactionalOutbox {
    static Map<String, String> ordersDb = new HashMap<>();
    static List<String> outboxTable = new ArrayList<>(); // written atomically WITH ordersDb
    static List<String> publishedEvents = new ArrayList<>();

    static void placeOrder(String orderId) { // ONE simulated local transaction -- both writes, or neither
        ordersDb.put(orderId, "PLACED");
        outboxTable.add("OrderPlaced:" + orderId);
        System.out.println("transaction committed: order " + orderId + " AND its outbox event, atomically");
    }

    static void relayOutbox() { // runs independently, whenever the broker is reachable -- no time pressure from the original request
        for (String event : new ArrayList<>(outboxTable)) {
            publishedEvents.add(event);
            outboxTable.remove(event);
            System.out.println("relay: published " + event + " (from the durable outbox, not from the original request)");
        }
    }

    public static void main(String[] args) {
        placeOrder("order-1"); // even if the broker is down RIGHT NOW, this cannot lose the event

        System.out.println("--- broker was down at request time; the relay simply hasn't run yet ---");
        System.out.println("db: " + ordersDb.containsKey("order-1") + ", outbox pending: " + outboxTable.size());

        relayOutbox(); // runs later, whenever the broker becomes reachable -- no deadline tied to the original request
        System.out.println("Final -- db: " + ordersDb.containsKey("order-1")
                + ", published: " + publishedEvents.contains("OrderPlaced:order-1") + " -- CONSISTENT, guaranteed.");
    }
}
```

How to run: `java FixedWithTransactionalOutbox.java`

`placeOrder` writes to `ordersDb` and `outboxTable` together, standing in for one atomic local transaction — there is no possible outcome where the order exists but the outbox event doesn't, or vice versa. `relayOutbox` runs completely independently of `placeOrder`'s original request, with no retry-count deadline — it will eventually run again (on its next scheduled pass, or after a crash and restart) and will still find the event durably waiting in `outboxTable`, guaranteeing it eventually gets published regardless of how long the broker outage lasts.

## 6. Walkthrough

Trace `FixedWithTransactionalOutbox.main` in order. **First**, `placeOrder("order-1")` runs: it adds `"order-1" -> "PLACED"` to `ordersDb` and appends `"OrderPlaced:order-1"` to `outboxTable` — both writes are modeled as happening within the same atomic transaction, so there is no window where one exists without the other.

**Next**, `main` prints the current state, confirming the order exists in `ordersDb` and one event is pending in `outboxTable` — this represents the moment right after the original request completed, even though the broker was unavailable at that time.

**Then**, `relayOutbox()` runs, entirely decoupled from the original request's timing. It iterates `outboxTable`, and for the one pending event, adds it to `publishedEvents` and removes it from `outboxTable`, printing a confirmation.

**Finally**, `main` prints the final state: the order still exists in `ordersDb`, and the event is now present in `publishedEvents` — both facts agree, and critically, this agreement was guaranteed the moment `placeOrder`'s transaction committed; `relayOutbox` merely had to run *at some point* afterward, with no deadline, unlike the retry-loop approach in Level 2 which needed to succeed within a fixed number of attempts during the original request's lifetime.

```
placeOrder(order-1)  -> ONE transaction: ordersDb + outboxTable, atomically
[broker down at request time -- doesn't matter]
relayOutbox()  -> runs LATER, whenever broker is reachable -> publishes from the durable outbox
Final: ordersDb has order-1 AND publishedEvents has its event -- guaranteed consistent
```

## 7. Gotchas & takeaways

> A `try { db.save(); broker.publish(); } catch { retry publish; }` pattern only reduces the *frequency* of the dual-write problem, not its existence — a crash between the database commit and the retry logic, or a retry budget that's exhausted during a longer outage, still loses the event. The only structural fix is making both writes atomic, via the [transactional outbox pattern](0331-transactional-outbox-pattern.md).

- The dual-write problem occurs whenever a database write and a separate external call (broker publish, another service's API) aren't covered by a shared transaction.
- Retrying the second call reduces how often the problem surfaces but does not eliminate it — a crash or a sufficiently long outage still causes permanent loss.
- The structural fix is the [transactional outbox pattern](0331-transactional-outbox-pattern.md): write the event to a table in the same local transaction as the business change, and let a separate, time-unlimited relay process handle actually publishing it.
- On the consuming side, the corresponding safeguard against redelivered or duplicate events is the [inbox pattern](0339-inbox-pattern-for-idempotent-consumption.md).
