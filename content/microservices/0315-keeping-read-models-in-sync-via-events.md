---
card: microservices
gi: 315
slug: keeping-read-models-in-sync-via-events
title: "Keeping read models in sync via events"
---

## 1. What it is

This is the specific mechanism that keeps a [CQRS read model](0314-cqrs-read-models-materialized-views.md) current after its initial build: the command side publishes an event every time it makes a change, and one or more dedicated event listeners (often called projectors or read-model updaters) subscribe to those events and incrementally apply each one to the read model — updating just the affected portion, not rebuilding the whole thing from scratch. This is the concrete, mechanical bridge that makes CQRS's separation between write and read models actually work over time, not just at the moment the read model is first built.

## 2. Why & when

A read model built once and never updated becomes permanently stale the instant the underlying data changes — useless for anything beyond a one-time snapshot. Rebuilding the entire read model from scratch on every single change is correct but typically far too slow and wasteful for anything beyond small datasets; production systems instead process each event as it arrives and apply just its specific, incremental effect to the read model — an `OrderPlacedEvent` adds one new entry, an `OrderCancelledEvent` updates or removes one existing entry, without touching anything else in the read model.

Use event-driven incremental updates as the standard approach for any read model expected to stay current over an extended period and across many changes. The [transactional outbox pattern](covered elsewhere in this microservices curriculum) is typically used on the publishing side to guarantee an event is reliably published whenever its corresponding write commits, and idempotent, order-aware event handling (processing events in the order they occurred, and handling any given event being delivered more than once safely) is essential on the consuming side, since most messaging systems provide at-least-once delivery rather than exactly-once.

## 3. Core concept

Each event type has a corresponding handler that applies its specific, minimal effect to the read model; handlers must be idempotent, since the same event may be redelivered.

```java
@Component
class OrderHistoryProjector {
    private final OrderHistoryReadModelRepository readModelRepository;

    @EventListener
    void on(OrderPlacedEvent event) {
        // Idempotent: use the event's own ID to detect and skip duplicates.
        if (readModelRepository.existsByEventId(event.eventId())) return; // already applied, SKIP
        readModelRepository.save(new OrderHistoryEntry(event.orderId(), event.customerName(),
                event.summary(), event.eventId()));
    }

    @EventListener
    void on(OrderCancelledEvent event) {
        if (readModelRepository.existsByEventId(event.eventId())) return;
        readModelRepository.updateStatus(event.orderId(), "CANCELLED", event.eventId());
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The command side publishes an event stream as changes happen; a projector consumes each event in order and applies its specific incremental effect to the read model, so the read model stays current through a sequence of small updates rather than being rebuilt from scratch on every change">
  <rect x="20" y="60" width="140" height="35" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="82" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Event 1: OrderPlaced</text>
  <rect x="180" y="60" width="140" height="35" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="250" y="82" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Event 2: OrderCancelled</text>

  <line x1="160" y1="77" x2="180" y2="77" stroke="#8b949e" marker-end="url(#arr315)"/>
  <line x1="320" y1="77" x2="400" y2="77" stroke="#8b949e" marker-end="url(#arr315)"/>

  <rect x="410" y="30" width="200" height="90" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="50" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Projector</text>
  <text x="510" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">applies EACH event's</text>
  <text x="510" y="78" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">specific, minimal effect</text>
  <text x="510" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">to the read model,</text>
  <text x="510" y="106" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">idempotently, IN ORDER</text>

  <defs><marker id="arr315" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each event is applied incrementally, in order, idempotently — the read model evolves through a sequence of small updates.

## 5. Runnable example

Scenario: a projector that naively reprocesses an event it has already seen, corrupting the read model, extended to an idempotent projector that correctly detects and skips duplicate events, and finally a projector that additionally enforces correct event ordering, showing what happens (and how it's handled) when events for the same entity arrive out of order — a realistic concern with distributed, at-least-once message delivery.

### Level 1 — Basic

```java
// File: NonIdempotentProjectorCorrupts.java -- a projector that does NOT
// check for duplicate events; when the SAME event is redelivered
// (a normal occurrence with at-least-once messaging), it double-applies
// the effect, corrupting the read model.
import java.util.*;

public class NonIdempotentProjectorCorrupts {
    record OrderPlacedEvent(String eventId, String orderId, double amount) {}

    static Map<String, Double> revenueReadModel = new HashMap<>();

    // NOT idempotent -- blindly adds the amount EVERY time it's called.
    static void onOrderPlaced(OrderPlacedEvent event) {
        revenueReadModel.merge(event.orderId(), event.amount(), Double::sum);
    }

    public static void main(String[] args) {
        OrderPlacedEvent event = new OrderPlacedEvent("evt-1", "order-1", 49.99);

        onOrderPlaced(event); // first delivery
        onOrderPlaced(event); // REDELIVERY -- messaging systems often deliver AT LEAST ONCE, this WILL happen

        System.out.println("Read model revenue for order-1: $" + revenueReadModel.get("order-1")
                + " -- should be $49.99, but the DUPLICATE delivery double-counted it!");
    }
}
```

How to run: `java NonIdempotentProjectorCorrupts.java`

The same `OrderPlacedEvent` is delivered to `onOrderPlaced` twice, simulating a normal at-least-once redelivery. Because the handler has no way to recognize it has already processed this exact event, it applies the `$49.99` amount a second time, corrupting the read model to show `$99.98` — double the correct revenue for a single order.

### Level 2 — Intermediate

```java
// File: IdempotentProjector.java -- tracks which event IDs have already
// been applied, and SKIPS any event it has already seen, correctly
// tolerating redelivery without corrupting the read model.
import java.util.*;

public class IdempotentProjector {
    record OrderPlacedEvent(String eventId, String orderId, double amount) {}

    static Map<String, Double> revenueReadModel = new HashMap<>();
    static Set<String> processedEventIds = new HashSet<>(); // tracks WHICH events have already been applied

    static void onOrderPlaced(OrderPlacedEvent event) {
        if (processedEventIds.contains(event.eventId())) {
            System.out.println("  Event " + event.eventId() + " already processed -- SKIPPING (idempotent)");
            return; // do NOT re-apply
        }
        revenueReadModel.merge(event.orderId(), event.amount(), Double::sum);
        processedEventIds.add(event.eventId());
    }

    public static void main(String[] args) {
        OrderPlacedEvent event = new OrderPlacedEvent("evt-1", "order-1", 49.99);

        onOrderPlaced(event); // first delivery -- applied
        onOrderPlaced(event); // REDELIVERY -- correctly skipped

        System.out.println("Read model revenue for order-1: $" + revenueReadModel.get("order-1")
                + " -- correct, DESPITE the duplicate delivery.");
    }
}
```

How to run: `java IdempotentProjector.java`

`processedEventIds` tracks every event ID already applied to the read model. The first call to `onOrderPlaced` applies the `$49.99` amount and records `"evt-1"` as processed. The second call (the redelivery) checks `processedEventIds.contains("evt-1")`, finds it already there, and returns immediately without touching `revenueReadModel` again — the final revenue correctly stays at `$49.99` despite the exact same at-least-once redelivery scenario that corrupted Level 1's projector.

### Level 3 — Advanced

```java
// File: OrderAwareIdempotentProjector.java -- handles a HARDER real-world
// case: events for the SAME entity can arrive OUT OF ORDER (e.g., due to
// retries or parallel consumers). Applying an "OrderCancelled" event
// before its corresponding "OrderPlaced" event has been applied would
// corrupt the read model. This projector tracks a per-entity sequence
// number and DEFERS/rejects out-of-order events rather than misapplying them.
import java.util.*;

public class OrderAwareIdempotentProjector {
    sealed interface OrderEvent permits OrderPlacedEvent, OrderCancelledEvent {
        String orderId(); long sequenceNumber();
    }
    record OrderPlacedEvent(String orderId, long sequenceNumber, double amount) implements OrderEvent {}
    record OrderCancelledEvent(String orderId, long sequenceNumber) implements OrderEvent {}

    record ReadModelEntry(double amount, String status, long lastAppliedSequence) {}
    static Map<String, ReadModelEntry> readModel = new HashMap<>();
    static List<OrderEvent> deferredEvents = new ArrayList<>(); // events that arrived TOO EARLY, held for later

    static void apply(OrderEvent event) {
        ReadModelEntry existing = readModel.get(event.orderId());
        long expectedNextSequence = (existing == null) ? 1 : existing.lastAppliedSequence() + 1;

        if (event.sequenceNumber() != expectedNextSequence) {
            System.out.println("  Event for " + event.orderId() + " seq=" + event.sequenceNumber()
                    + " arrived OUT OF ORDER (expected seq=" + expectedNextSequence + ") -- DEFERRING, not misapplying");
            deferredEvents.add(event);
            return;
        }

        if (event instanceof OrderPlacedEvent placed) {
            readModel.put(placed.orderId(), new ReadModelEntry(placed.amount(), "PLACED", placed.sequenceNumber()));
        } else if (event instanceof OrderCancelledEvent cancelled) {
            readModel.put(cancelled.orderId(), new ReadModelEntry(existing.amount(), "CANCELLED", cancelled.sequenceNumber()));
        }
        System.out.println("  Applied " + event.getClass().getSimpleName() + " seq=" + event.sequenceNumber() + " for " + event.orderId());

        retryDeferredEvents(); // now that the sequence advanced, a previously-deferred event might apply now
    }

    static void retryDeferredEvents() {
        List<OrderEvent> toRetry = new ArrayList<>(deferredEvents);
        deferredEvents.clear();
        for (OrderEvent e : toRetry) apply(e); // may defer AGAIN if still not next in sequence
    }

    public static void main(String[] args) {
        // OrderCancelled (seq=2) arrives BEFORE OrderPlaced (seq=1) -- a realistic
        // out-of-order delivery scenario.
        apply(new OrderCancelledEvent("order-1", 2));
        System.out.println("Read model after out-of-order event: " + readModel.get("order-1") + " (correctly NOT yet applied)");

        apply(new OrderPlacedEvent("order-1", 1, 49.99)); // the MISSING seq=1 finally arrives
        System.out.println("Read model after seq=1 arrives: " + readModel.get("order-1")
                + " -- the deferred CANCELLED event was automatically retried and applied correctly, IN ORDER.");
    }
}
```

How to run: `java OrderAwareIdempotentProjector.java`

`OrderCancelledEvent(seq=2)` arrives first. `apply` computes `expectedNextSequence=1` (no existing entry yet), sees the incoming event's `sequenceNumber()` is `2`, not `1`, and defers it instead of misapplying it — the read model correctly stays empty for `"order-1"` rather than showing a cancelled order that was never actually recorded as placed. When `OrderPlacedEvent(seq=1)` subsequently arrives, `apply` finds it matches the expected sequence, applies it (setting status to `"PLACED"`), and then calls `retryDeferredEvents`, which re-attempts the previously deferred cancellation — this time, `expectedNextSequence` is `2` (since seq 1 was just applied), matching the deferred event's `sequenceNumber()` of `2`, so it now applies correctly, updating the status to `"CANCELLED"`. The final read model correctly reflects both events applied in their true logical order, despite having been delivered out of order.

## 6. Walkthrough

Trace `OrderAwareIdempotentProjector.main` in order. **First**, `apply(new OrderCancelledEvent("order-1", 2))` is called. Inside, `readModel.get("order-1")` returns `null` (no entry yet), so `expectedNextSequence` is computed as `1`. The event's own `sequenceNumber()` is `2`, which does not equal `1`, so the out-of-order branch executes: it prints a deferral message and adds the event to `deferredEvents`, then returns immediately — no changes are made to `readModel`.

**`main` prints `readModel.get("order-1")`**, which is still `null` — correctly reflecting that nothing has actually been recorded yet, since the cancellation was correctly withheld rather than misapplied against a nonexistent order.

**`apply(new OrderPlacedEvent("order-1", 1, 49.99))` is called next.** `readModel.get("order-1")` is still `null`, so `expectedNextSequence` is again `1`. This event's `sequenceNumber()` is `1`, which *does* match — so the normal application path executes: since it's an `OrderPlacedEvent`, `readModel.put("order-1", new ReadModelEntry(49.99, "PLACED", 1))` runs, establishing the first real entry.

**Immediately after applying**, `retryDeferredEvents()` is called. It copies `deferredEvents` (containing the one previously-deferred `OrderCancelledEvent`) into `toRetry`, clears `deferredEvents`, and calls `apply` again for that event.

**Inside this nested `apply` call**, `readModel.get("order-1")` now returns the entry just created (`amount=49.99, status="PLACED", lastAppliedSequence=1`), so `expectedNextSequence` is computed as `1 + 1 = 2`. The deferred event's `sequenceNumber()` is `2`, which now matches — the normal application path executes: since it's an `OrderCancelledEvent`, `readModel.put("order-1", new ReadModelEntry(existing.amount(), "CANCELLED", 2))` runs, preserving the `49.99` amount from the existing entry but updating the status to `"CANCELLED"` and the sequence to `2`.

**Back in the outer call**, `main` prints the final `readModel.get("order-1")`, showing `ReadModelEntry(amount=49.99, status="CANCELLED", lastAppliedSequence=2)` — both events have now been correctly applied in their true logical order (placed, then cancelled), even though they were *delivered* in the opposite order.

```
apply(Cancelled, seq=2) -- expected seq=1, got seq=2 -> DEFERRED, read model untouched
apply(Placed, seq=1)    -- expected seq=1, got seq=1 -> APPLIED (status=PLACED)
        |
        v  retryDeferredEvents()
apply(Cancelled, seq=2) [retry] -- expected seq=2, got seq=2 -> APPLIED (status=CANCELLED)
```

## 7. Gotchas & takeaways

> Most real messaging systems (Kafka, RabbitMQ, SQS) guarantee at-least-once delivery, not exactly-once — a projector that assumes every event arrives exactly once, in order, will eventually corrupt its read model in production, even if this never surfaces during testing, since duplicate and out-of-order delivery are relatively rare but inevitable occurrences at scale.

- Every event handler updating a read model must be idempotent — safely re-processable without corrupting state if the same event is delivered more than once, which at-least-once messaging guarantees will eventually happen.
- Events for the same entity can arrive out of order in a distributed system; a projector that cares about ordering (most do) needs an explicit mechanism — a per-entity sequence number, as shown, or partition-ordered consumption guarantees from the messaging system itself — to detect and correctly handle this rather than blindly applying events in whatever order they happen to arrive.
- Deferring an out-of-order event and retrying it once the gap is filled (as in Level 3) is one practical approach; another common approach relies on the messaging system guaranteeing per-key ordering (e.g., Kafka's per-partition ordering, keyed by entity ID), which removes the need for application-level sequence tracking at the cost of requiring that guarantee to actually hold.
- A read model that can always be correctly rebuilt from scratch by replaying its full event history in order is a strong, valuable property — it means bugs in projector logic can be fixed and the read model regenerated correctly, rather than needing to reconcile accumulated corruption.
