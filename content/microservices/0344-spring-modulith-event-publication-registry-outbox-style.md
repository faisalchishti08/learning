---
card: microservices
gi: 344
slug: spring-modulith-event-publication-registry-outbox-style
title: "Spring Modulith event publication registry (outbox-style)"
---

## 1. What it is

Spring Modulith's **event publication registry** is a built-in mechanism that automatically persists a record of every application event published from within a transaction, alongside the business change, and tracks which event listeners have successfully completed. If a listener fails or the process crashes before all listeners finish, the registry remembers which ones are still incomplete, and a republishing mechanism can retry them later — giving you the core guarantee of the [transactional outbox pattern](0331-transactional-outbox-pattern.md) without hand-building an outbox table and relay yourself.

## 2. Why & when

Building a transactional outbox by hand — an outbox table, code to write to it inside the business transaction, a separate relay process — is valuable but is also boilerplate that's easy to get subtly wrong. Spring Modulith, aimed at building well-structured modular monoliths (and modules that can later become microservices), provides this exact mechanism out of the box: enable it, and every event published via `ApplicationEventPublisher` from within a transaction gets a durable publication record; if a listener throws or the application crashes mid-processing, the incomplete publication is retried automatically (or on demand) once things recover.

Use Spring Modulith's event publication registry when you're already using Spring's own event mechanism (`@EventListener` / `@TransactionalEventListener`) within a Spring Modulith application and want outbox-style reliability without writing and operating a custom outbox table and relay — it's a substantial reduction in code for teams already invested in Spring's event model. For true cross-service messaging (a real broker like Kafka or RabbitMQ), a hand-built outbox or [Debezium-based CDC outbox](0348-debezium-spring-for-cdc-based-outbox.md) may still be more appropriate, but for reliable in-process (or soon-to-be-extracted) event handling, the registry is a strong, low-effort default.

## 3. Core concept

When an event is published from within a transaction, Spring Modulith writes a row to its event publication table recording the event and each interested listener, in the same transaction as the business change. As each listener completes successfully, its row is marked complete; incomplete rows (a listener that hasn't run yet, or one that failed) remain and can be found and retried — either automatically on a schedule or by explicitly invoking the republishing mechanism.

```java
// Application code just does this -- Modulith wires the persistence and retry underneath:
@Transactional
public void placeOrder(Order order) {
    orderRepository.save(order);
    eventPublisher.publishEvent(new OrderPlacedEvent(order.getId())); // Modulith durably tracks this
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An event is published inside a transaction; Modulith writes a publication record in the same transaction; each listener that completes marks its row done; an incomplete row after a crash is found and retried later">
  <rect x="20" y="20" width="260" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">publishEvent() inside transaction</text>
  <text x="150" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">-&gt; publication record written, atomically</text>

  <rect x="360" y="20" width="260" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Listener runs</text>
  <text x="490" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">success -&gt; marked COMPLETE</text>

  <rect x="190" y="110" width="260" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="135" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">incomplete record found later -&gt; RETRIED</text>

  <line x1="490" y1="70" x2="320" y2="110" stroke="#f0883e" marker-end="url(#a344)"/>

  <defs><marker id="a344" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker></defs>
</svg>

Publication and business change commit together; each listener's completion is tracked; incomplete listeners are found and retried later.

## 5. Runnable example

Scenario: an order-placement flow whose listener sometimes fails, first shown with no tracking at all (a failed listener is simply lost), then rebuilt with a simulated Modulith-style publication registry that records completion per listener, and finally extended to show the registry finding and retrying incomplete publications after a simulated restart.

### Level 1 — Basic

```java
// File: NoPublicationTracking.java -- a listener fails; there is NO
// record of this anywhere, so the failure is simply lost.
import java.util.*;

public class NoPublicationTracking {
    static Map<String, String> ordersTable = new HashMap<>();

    static void onOrderPlaced(String orderId, boolean simulateFailure) {
        if (simulateFailure) { System.out.println("listener FAILED for " + orderId + " -- nothing records this happened!"); return; }
        System.out.println("listener: reserved stock for " + orderId);
    }

    static void placeOrder(String orderId, boolean simulateListenerFailure) {
        ordersTable.put(orderId, "PLACED");
        onOrderPlaced(orderId, simulateListenerFailure);
    }

    public static void main(String[] args) {
        placeOrder("order-1", true);
        System.out.println("Order exists: " + ordersTable.containsKey("order-1")
                + ", but its listener's failure left NO trace -- nobody knows stock was never reserved.");
    }
}
```

How to run: `java NoPublicationTracking.java`

The listener fails and prints a message, but that's the entirety of the record — nothing persists the fact that `order-1`'s stock-reservation listener never completed. If this were a real system, stock would never actually be reserved for this order, and no automated process would ever notice or retry.

### Level 2 — Intermediate

```java
// File: PublicationRegistrySimulated.java -- simulates Modulith's
// registry: a publication record is created per (event, listener) pair,
// atomically alongside the business change, and marked COMPLETE only
// when the listener actually succeeds.
import java.util.*;

public class PublicationRegistrySimulated {
    enum Status { INCOMPLETE, COMPLETE }
    record PublicationRecord(String eventId, String listenerName, Status status) {}
    static Map<String, String> ordersTable = new HashMap<>();
    static List<PublicationRecord> publicationRegistry = new ArrayList<>();

    static void placeOrder(String orderId, String eventId, boolean simulateListenerFailure) {
        ordersTable.put(orderId, "PLACED");
        publicationRegistry.add(new PublicationRecord(eventId, "reserveStockListener", Status.INCOMPLETE)); // written WITH the business change
        System.out.println("transaction committed: order " + orderId + " + publication record (INCOMPLETE)");

        runListener(eventId, orderId, simulateListenerFailure);
    }

    static void runListener(String eventId, String orderId, boolean simulateFailure) {
        if (simulateFailure) { System.out.println("listener FAILED for " + orderId + " -- publication record STAYS incomplete"); return; }
        for (int i = 0; i < publicationRegistry.size(); i++) {
            PublicationRecord r = publicationRegistry.get(i);
            if (r.eventId().equals(eventId)) publicationRegistry.set(i, new PublicationRecord(r.eventId(), r.listenerName(), Status.COMPLETE));
        }
        System.out.println("listener: reserved stock for " + orderId + " -- publication record marked COMPLETE");
    }

    public static void main(String[] args) {
        placeOrder("order-1", "evt-1", true); // listener fails -- record stays INCOMPLETE, durably

        System.out.println("Publication registry: " + publicationRegistry);
        System.out.println("Unlike Level 1, the failure is DURABLY recorded and discoverable.");
    }
}
```

How to run: `java PublicationRegistrySimulated.java`

`placeOrder` writes both the order and an `INCOMPLETE` publication record together, standing in for Modulith's atomic write. When the listener fails, `runListener` simply returns without updating the record, leaving it durably `INCOMPLETE` in `publicationRegistry` — unlike Level 1, this failure is now a discoverable fact, not a silently lost event.

### Level 3 — Advanced

```java
// File: RepublishIncompleteAfterRestart.java -- a "restart" happens
// after an incomplete publication; a republishing pass scans the
// registry for INCOMPLETE records and retries their listeners, marking
// them COMPLETE once they succeed.
import java.util.*;

public class RepublishIncompleteAfterRestart {
    enum Status { INCOMPLETE, COMPLETE }
    record PublicationRecord(String eventId, String orderId, String listenerName, Status status) {}
    static Map<String, String> ordersTable = new HashMap<>();
    static List<PublicationRecord> publicationRegistry = new ArrayList<>();
    static int listenerFailuresRemaining = 1; // simulates a transient failure that clears up on retry

    static void placeOrder(String orderId, String eventId) {
        ordersTable.put(orderId, "PLACED");
        publicationRegistry.add(new PublicationRecord(eventId, orderId, "reserveStockListener", Status.INCOMPLETE));
        System.out.println("transaction committed: " + orderId + " + INCOMPLETE publication record");
        runListenerOnce(eventId);
    }

    static boolean runListenerOnce(String eventId) {
        if (listenerFailuresRemaining > 0) { listenerFailuresRemaining--; System.out.println("listener attempt for " + eventId + " FAILED"); return false; }
        for (int i = 0; i < publicationRegistry.size(); i++) {
            PublicationRecord r = publicationRegistry.get(i);
            if (r.eventId().equals(eventId) && r.status() == Status.INCOMPLETE) {
                publicationRegistry.set(i, new PublicationRecord(r.eventId(), r.orderId(), r.listenerName(), Status.COMPLETE));
                System.out.println("listener attempt for " + eventId + " SUCCEEDED -- marked COMPLETE");
            }
        }
        return true;
    }

    static void republishIncomplete() { // Modulith's built-in republishing mechanism, simulated
        System.out.println("republishIncomplete: scanning registry for INCOMPLETE records...");
        for (PublicationRecord r : new ArrayList<>(publicationRegistry)) {
            if (r.status() == Status.INCOMPLETE) {
                System.out.println("  found incomplete: " + r.eventId() + " for " + r.orderId() + " -- retrying");
                runListenerOnce(r.eventId());
            }
        }
    }

    public static void main(String[] args) {
        placeOrder("order-1", "evt-1"); // listener fails on first attempt

        System.out.println("--- application RESTARTS here ---");
        republishIncomplete(); // finds the incomplete record and retries -- this time it succeeds

        System.out.println("Final registry: " + publicationRegistry);
    }
}
```

How to run: `java RepublishIncompleteAfterRestart.java`

`placeOrder` writes the `INCOMPLETE` record and attempts the listener once, which fails (`listenerFailuresRemaining` starts at `1`). After the simulated restart, `republishIncomplete` scans `publicationRegistry`, finds the still-`INCOMPLETE` record for `"evt-1"`, and calls `runListenerOnce` again — this time `listenerFailuresRemaining` is `0`, so the listener succeeds and the record is updated to `COMPLETE`. The final registry state shows the record correctly marked complete, having survived both the original failure and the simulated restart without losing track of the work still owed.

## 6. Walkthrough

Trace `RepublishIncompleteAfterRestart.main` in order. **First**, `placeOrder("order-1", "evt-1")` runs: it adds `"order-1"` to `ordersTable`, appends an `INCOMPLETE` `PublicationRecord` for `"evt-1"` to `publicationRegistry`, and calls `runListenerOnce("evt-1")`. Inside, `listenerFailuresRemaining` is `1`, so the `if` branch decrements it to `0` and returns `false` — the record stays `INCOMPLETE`.

**Next**, the program prints a message marking a simulated restart — nothing about `publicationRegistry` is reset here, representing the fact that this data lives in a durable database in a real Spring Modulith application, not in memory that would be lost on restart.

**Then**, `republishIncomplete()` runs. It iterates a copy of `publicationRegistry`, finds the one record still at `Status.INCOMPLETE`, prints that it was found, and calls `runListenerOnce("evt-1")` again. This time `listenerFailuresRemaining` is `0`, so the `if` branch is skipped; the method's loop finds the matching record (by `eventId` and `INCOMPLETE` status) and replaces it with a `COMPLETE` version, printing a success message.

**Finally**, `main` prints the final `publicationRegistry`, showing the one record now at `Status.COMPLETE` — the listener's work was durably tracked through a failure and a restart, and the republishing pass correctly found and completed the outstanding work without needing anyone to remember it manually.

```
placeOrder(evt-1)        -> registry: [evt-1, INCOMPLETE] ; listener attempt FAILS
[restart]
republishIncomplete()    -> finds [evt-1, INCOMPLETE] -> retries -> SUCCEEDS -> registry: [evt-1, COMPLETE]
```

## 7. Gotchas & takeaways

> The event publication registry tracks *listener completion*, not arbitrary application state — if a listener's logic itself is not idempotent, a retried (previously incomplete) publication can still double-apply a side effect on retry. Listeners registered with Modulith's registry still need the same idempotency discipline as any other message consumer (see [idempotency in saga steps](0330-idempotency-in-saga-steps.md)).

- Spring Modulith's event publication registry gives outbox-style reliability for Spring's own event mechanism, without a hand-built outbox table and relay.
- Publication records are written atomically alongside the business transaction, and updated to complete as each listener finishes successfully.
- A republishing mechanism finds incomplete publications (from a failed listener or a crash) and retries them, so failures are durably tracked rather than silently lost.
- Listeners must still be idempotent, since a republished event can, by design, be delivered to a listener more than once.
