---
card: microservices
gi: 331
slug: transactional-outbox-pattern
title: "Transactional outbox pattern"
---

## 1. What it is

The **transactional outbox pattern** solves the [dual-write problem](0338-dual-write-problem.md) — reliably updating a database *and* publishing a message about that update — by writing the event to an **outbox table** in the *same local database transaction* as the business change, instead of publishing to a message broker directly. A separate process then reads the outbox table and reliably publishes each event to the broker, deleting or marking it once confirmed sent. Because the business write and the outbox write share one atomic local transaction, either both happen or neither does — there is no window where one succeeds and the other silently doesn't.

## 2. Why & when

If a service updates its own database and then makes a separate call to a message broker to publish an event, those are two independent operations with no shared atomicity: the database commit could succeed while the broker call fails (the event is lost, and nobody downstream ever learns the change happened), or the broker call could succeed while the database commit fails (a "phantom" event is published for a change that never actually took effect). Either failure silently breaks the guarantee that a [saga](0320-saga-pattern.md) or [read model](0315-keeping-read-models-in-sync-via-events.md) depends on.

Use the outbox pattern whenever a service's local database write must be reliably accompanied by an event, which is essentially every case where one service's change needs to trigger something in another service. It's the standard, low-risk way to guarantee "the event was published if and only if the database change committed," using only the atomicity a service's own local database already provides.

## 3. Core concept

Within one local transaction: write the business change to its normal table, and write a corresponding row (event type, payload, a "sent" flag or timestamp) to an `outbox` table in the same database. Commit once — both rows land together or neither does. A separate relay process (often via [transaction log tailing / CDC](0332-transaction-log-tailing.md), or a simpler polling loop) reads unsent outbox rows, publishes each to the broker, and marks it sent, retrying safely since publishing an already-sent-but-not-yet-marked event twice is a duplicate the consumer's idempotency handles.

```java
@Transactional // ONE local transaction covers BOTH writes
void placeOrder(Order order) {
    orderRepository.save(order);
    outboxRepository.save(new OutboxEvent("OrderPlaced", toJson(order)));
} // commits together, or neither commits
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One local transaction writes both the orders table and the outbox table together; a separate relay process later reads the outbox table and publishes each event to the message broker, marking it sent">
  <rect x="30" y="20" width="280" height="70" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="170" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ONE local transaction</text>
  <text x="170" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">orders table + outbox table</text>
  <text x="170" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">commit together, or neither</text>

  <line x1="170" y1="90" x2="170" y2="120" stroke="#8b949e" marker-end="url(#a331)"/>
  <rect x="30" y="120" width="280" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="170" y="145" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Relay process reads outbox, publishes, marks sent</text>

  <line x1="310" y1="140" x2="420" y2="140" stroke="#79c0ff" marker-end="url(#a331b)"/>
  <rect x="430" y="120" width="180" height="40" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="520" y="145" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Message broker</text>

  <defs>
    <marker id="a331" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a331b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The business write and the outbox write share one local transaction; a separate relay reliably publishes from the outbox afterward.

## 5. Runnable example

Scenario: an order-placement flow that first shows the dual-write problem directly (database commits, broker publish fails silently), then fixed with a transactional outbox written in the same commit, then extended with a relay loop that reliably drains the outbox and marks entries sent, tolerating its own crashes.

### Level 1 — Basic

```java
// File: DualWriteProblem.java -- database write and "broker publish" are
// TWO separate operations; the second one FAILS, and the event is LOST,
// even though the database change succeeded.
import java.util.*;

public class DualWriteProblem {
    static Map<String, String> ordersTable = new HashMap<>();
    static List<String> publishedEvents = new ArrayList<>();

    static void placeOrder(String orderId, boolean simulateBrokerFailure) {
        ordersTable.put(orderId, "PLACED"); // database write SUCCEEDS
        System.out.println("database: order " + orderId + " saved");

        if (simulateBrokerFailure) {
            System.out.println("broker: publish FAILED (e.g. network blip) -- event LOST, nobody told!");
            return; // the database commit already happened -- there's no going back now
        }
        publishedEvents.add("OrderPlaced:" + orderId);
    }

    public static void main(String[] args) {
        placeOrder("order-1", true);
        System.out.println("Order exists in DB: " + ordersTable.containsKey("order-1")
                + ", but published events: " + publishedEvents + " -- inventory service will NEVER hear about this order!");
    }
}
```

How to run: `java DualWriteProblem.java`

The database write and the broker publish are independent steps with no shared atomicity. The database commit succeeds, but the simulated broker failure means `publishedEvents` stays empty — any other service relying on an `OrderPlaced` event (to reserve stock, say) will never react, even though the order genuinely exists.

### Level 2 — Intermediate

```java
// File: TransactionalOutbox.java -- the order AND its outbox event are
// written together in ONE simulated local transaction; the broker publish
// is a SEPARATE, later step that reads from the outbox.
import java.util.*;

public class TransactionalOutbox {
    static Map<String, String> ordersTable = new HashMap<>();
    static List<String> outboxTable = new ArrayList<>(); // written in the SAME transaction as ordersTable

    static void placeOrder(String orderId) { // simulates ONE local transaction covering both writes
        ordersTable.put(orderId, "PLACED");
        outboxTable.add("OrderPlaced:" + orderId); // same transaction -- commits together with the order write
        System.out.println("transaction committed: order " + orderId + " saved AND outbox event recorded, atomically");
    }

    static void relayOutboxToBroker() { // a SEPARATE process/step, run afterward
        for (String event : outboxTable) System.out.println("relay: publishing " + event + " to broker");
    }

    public static void main(String[] args) {
        placeOrder("order-1"); // even if the broker is down right now, the event is SAFELY recorded
        System.out.println("--- broker was down at the moment of placeOrder, but nothing was lost ---");
        relayOutboxToBroker(); // runs later, once the broker (or the relay's retry loop) is ready
    }
}
```

How to run: `java TransactionalOutbox.java`

`placeOrder` writes both `ordersTable` and `outboxTable` together, standing in for one local database transaction — there is no possibility of the order existing without its corresponding outbox event, or vice versa. `relayOutboxToBroker` is a distinct step that can run at any later time (immediately, after a delay, after a crash and restart) and will still find the event durably recorded, ready to publish — the broker's availability at the exact moment of `placeOrder` no longer matters.

### Level 3 — Advanced

```java
// File: OutboxRelayWithRetryAndMarking.java -- the relay marks each event
// SENT only after a successful publish, retries unsent events on its next
// pass (surviving its own crash), and skips events already marked sent so
// a restart doesn't republish everything from scratch.
import java.util.*;

public class OutboxRelayWithRetryAndMarking {
    record OutboxEvent(String id, String payload, boolean sent) {}
    static List<OutboxEvent> outboxTable = new ArrayList<>();
    static List<String> publishedToBroker = new ArrayList<>();
    static int brokerFailuresRemaining = 1; // simulates the broker being briefly unavailable on the first attempt

    static void placeOrder(String orderId) {
        outboxTable.add(new OutboxEvent("evt-" + orderId, "OrderPlaced:" + orderId, false));
        System.out.println("transaction committed: order " + orderId + " + outbox event evt-" + orderId + " (unsent)");
    }

    static boolean publishToBroker(String payload) {
        if (brokerFailuresRemaining > 0) { brokerFailuresRemaining--; return false; } // simulated transient failure
        publishedToBroker.add(payload);
        return true;
    }

    static void relayPass() { // one pass of the relay's loop -- safe to call repeatedly, even after a crash
        for (int i = 0; i < outboxTable.size(); i++) {
            OutboxEvent event = outboxTable.get(i);
            if (event.sent()) continue; // already sent -- skip, don't republish on restart
            System.out.println("relay: attempting to publish " + event.id() + "...");
            if (publishToBroker(event.payload())) {
                outboxTable.set(i, new OutboxEvent(event.id(), event.payload(), true)); // mark sent ONLY after success
                System.out.println("relay: " + event.id() + " published and marked SENT");
            } else {
                System.out.println("relay: " + event.id() + " publish FAILED -- remains unsent, will retry NEXT pass");
            }
        }
    }

    public static void main(String[] args) {
        placeOrder("order-1");

        relayPass(); // FIRST pass: broker fails, event stays unsent
        relayPass(); // SECOND pass (e.g. after the relay restarts, or on its next scheduled run): succeeds

        System.out.println("Published to broker: " + publishedToBroker);
        System.out.println("Outbox event sent flag: " + outboxTable.get(0).sent());
    }
}
```

How to run: `java OutboxRelayWithRetryAndMarking.java`

`placeOrder` records one unsent outbox event. The first `relayPass()` attempts to publish it, but `publishToBroker` simulates a transient failure (`brokerFailuresRemaining` starts at `1`), so the event stays unmarked and unsent. The second `relayPass()` runs the same loop again — because the event's `sent` flag is still `false`, it is retried, and this time `publishToBroker` succeeds (the failure counter is now exhausted), so it is added to `publishedToBroker` and its outbox row is updated to `sent=true`. A third call to `relayPass()` (not shown, but implied by "safe to call repeatedly") would find `sent=true` and skip it, which is exactly what makes this relay safe to restart after its own crash: it never loses track of what still needs sending, and never re-sends what's already confirmed.

## 6. Walkthrough

Trace `OutboxRelayWithRetryAndMarking.main` in order. **First**, `placeOrder("order-1")` appends one `OutboxEvent` with `sent=false` to `outboxTable` — this stands in for the atomic local transaction that would, in a real system, write the order row and this outbox row together.

**Next**, the first `relayPass()` call runs its loop. For the one event in `outboxTable`, `event.sent()` is `false`, so it does not skip. It calls `publishToBroker(event.payload())`; inside, `brokerFailuresRemaining` is `1`, so the `if` branch decrements it to `0` and returns `false`. Back in `relayPass`, the `else` branch runs, printing that the publish failed and the event remains unsent — critically, `outboxTable` is left unchanged, still holding `sent=false`.

**Then**, the second `relayPass()` call runs the same loop again. The event still has `sent=false`, so it is retried: `publishToBroker` is called again, and this time `brokerFailuresRemaining` is `0`, so the `if` branch is skipped, the payload is added to `publishedToBroker`, and `true` is returned. Back in `relayPass`, the success branch runs: `outboxTable.set(i, ...)` replaces the event with an identical one except `sent=true`, and a confirmation is printed.

**Finally**, `main` prints `publishedToBroker` (containing the one event, published on the retry) and the outbox entry's `sent` flag, which is now `true` — demonstrating that a transient broker failure did not lose the event, and a naive re-run of the relay would not double-publish it either, since the `if (event.sent()) continue;` check at the top of the loop protects against that.

```
placeOrder(order-1)  -> outboxTable=[{evt-order-1, sent=false}]
relayPass() #1       -> publish FAILS -> stays {sent=false}
relayPass() #2       -> publish SUCCEEDS -> marked {sent=true}, added to publishedToBroker
(any future relayPass()) -> sent=true -> SKIPPED, never republished
```

## 7. Gotchas & takeaways

> Marking an outbox event "sent" *before* confirming the publish actually succeeded reintroduces the dual-write problem in miniature — a crash between marking-sent and the publish actually landing loses the event just as surely as the original naive approach. Always mark sent only *after* a confirmed successful publish, as shown in Level 3.

- The core guarantee is atomicity between the business write and the outbox write, achieved for free by using the service's own local database transaction — no distributed transaction is needed.
- A separate relay process reads unsent outbox rows and publishes them, retrying safely on failure and marking rows sent only after a confirmed publish.
- The relay itself can be built via polling (see [polling publisher pattern](0334-polling-publisher-pattern.md)) or via reading the database's own transaction log (see [transaction log tailing](0332-transaction-log-tailing.md) and [CDC](0333-change-data-capture-cdc.md)).
- Consumers of the published events must still be idempotent (see [idempotency in saga steps](0330-idempotency-in-saga-steps.md)), since the relay's own retries can cause the same event to be delivered more than once.
