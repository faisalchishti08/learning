---
card: microservices
gi: 135
slug: event-ordering-causality
title: "Event ordering & causality"
---

## 1. What it is

Causality is the relationship between two events where one genuinely happened *because of*, or *before and related to*, the other — `PaymentAuthorized` must be caused by (and therefore ordered after) `OrderPlaced` for the same order. Event ordering & causality is the practice of preserving that true cause-and-effect relationship as events flow through a distributed system, which is a stronger and subtler requirement than [message ordering guarantees](0119-message-ordering-guarantees.md)'s per-partition FIFO delivery alone.

## 2. Why & when

Per-partition ordering guarantees that messages sharing a partition key arrive in send order, but causally related events don't always share a single, obvious key, and a system with multiple producers, multiple topics, or multiple services publishing related events can easily end up delivering an *effect* before its *cause* was ever observed — a `PaymentAuthorized` event processed before the `OrderPlaced` event it logically depends on, simply because they traveled through different channels or partitions with different latencies. This produces consumers that briefly (or permanently, if unhandled) operate on an impossible state: authorizing payment for an order that, as far as the payment consumer's local view is concerned, doesn't exist yet.

Design explicitly for causality whenever events span multiple channels, multiple partitions, or multiple producing services and a consumer's correctness depends on seeing them in their true cause-and-effect order — not just in the FIFO order any single channel happens to provide. This is common in choreographed, multi-step business processes; see also [choreography vs orchestration](0132-choreography-vs-orchestration.md) for a related coordination concern.

## 3. Core concept

A causally-aware consumer either enforces same-partition delivery for the entire causal chain (the simplest fix, when possible) or tracks a causal reference — an explicit "this event was caused by event X" pointer — and defers processing an event until its declared cause has already been observed.

```java
record OrderPlaced(String orderId) {}
record PaymentAuthorized(String orderId, String causedByEventId) {} // explicit causal pointer

// a causally-aware consumer defers processing until the cause is confirmed observed
if (!observedEventIds.contains(event.causedByEventId())) {
    pendingUntilCauseArrives.add(event); // hold it, don't process yet -- its cause hasn't been seen
} else {
    process(event);
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OrderPlaced and PaymentAuthorized travel on two different channels with different latencies; PaymentAuthorized, despite being caused by OrderPlaced, can arrive at the consumer FIRST unless causality is explicitly tracked and enforced">
  <text x="160" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Without causal tracking (broken)</text>
  <rect x="20" y="40" width="120" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="80" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">PaymentAuthorized</text>
  <rect x="180" y="40" width="120" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="240" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">OrderPlaced</text>
  <text x="160" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">effect arrives BEFORE cause -- nonsensical state</text>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">With causal tracking (correct)</text>
  <rect x="360" y="40" width="120" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="420" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">OrderPlaced</text>
  <rect x="500" y="40" width="120" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="560" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">PaymentAuthorized</text>
  <text x="480" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">PaymentAuthorized deferred until OrderPlaced confirmed seen</text>
</svg>

Tracking the causal pointer explicitly lets a consumer defer an effect until its cause has genuinely been observed, regardless of channel-level arrival order.

## 5. Runnable example

Scenario: a payment-authorization consumer that starts naively processing events in arrival order (demonstrating the causality violation when channels race), adds explicit causal-pointer tracking to defer out-of-order effects, and finally handles a chain of three causally-linked events arriving in a fully scrambled order, correctly reordering them by their causal dependencies before processing any of them.

### Level 1 — Basic

```java
// File: NaiveArrivalOrder.java -- processes events in WHATEVER order they arrive,
// which can violate true causality when events travel on different channels.
import java.util.*;

public class NaiveArrivalOrder {
    record OrderPlaced(String eventId, String orderId) {}
    record PaymentAuthorized(String eventId, String orderId, String causedByEventId) {}

    public static void main(String[] args) {
        Set<String> knownOrders = new HashSet<>();

        // simulates PaymentAuthorized arriving FIRST -- a real possibility if it
        // traveled a faster channel/partition than OrderPlaced did
        PaymentAuthorized payment = new PaymentAuthorized("evt-2", "order-42", "evt-1");
        OrderPlaced orderPlaced = new OrderPlaced("evt-1", "order-42");

        // naive processing: just handle whatever arrived, in arrival order
        System.out.println("Processing PaymentAuthorized for " + payment.orderId() + "...");
        if (!knownOrders.contains(payment.orderId())) {
            System.out.println("  BUG: authorizing payment for an order that, AS FAR AS THIS CONSUMER KNOWS, doesn't exist yet!");
        }

        knownOrders.add(orderPlaced.orderId());
        System.out.println("Processing OrderPlaced for " + orderPlaced.orderId() + " (arrived SECOND, too late to help)");
    }
}
```

**How to run:** `javac NaiveArrivalOrder.java && java NaiveArrivalOrder` (JDK 17+).

Expected output:
```
Processing PaymentAuthorized for order-42...
  BUG: authorizing payment for an order that, AS FAR AS THIS CONSUMER KNOWS, doesn't exist yet!
Processing OrderPlaced for order-42 (arrived SECOND, too late to help)
```

Nothing enforces that the cause is seen before the effect; the consumer simply reacts to whatever it receives, in receipt order, producing an impossible intermediate state.

### Level 2 — Intermediate

```java
// File: CausalDeferral.java -- an explicit causal pointer lets the consumer DEFER
// processing an effect until its declared cause has genuinely been observed.
import java.util.*;

public class CausalDeferral {
    record OrderPlaced(String eventId, String orderId) {}
    record PaymentAuthorized(String eventId, String orderId, String causedByEventId) {}

    public static void main(String[] args) {
        Set<String> observedEventIds = new HashSet<>();
        List<PaymentAuthorized> pendingUntilCauseArrives = new ArrayList<>();

        PaymentAuthorized payment = new PaymentAuthorized("evt-2", "order-42", "evt-1");
        OrderPlaced orderPlaced = new OrderPlaced("evt-1", "order-42");

        // PaymentAuthorized arrives first, as before
        if (!observedEventIds.contains(payment.causedByEventId())) {
            pendingUntilCauseArrives.add(payment); // defer -- its cause ("evt-1") hasn't been seen yet
            System.out.println("PaymentAuthorized arrived but its cause (evt-1) hasn't been observed -- DEFERRED, not processed.");
        }

        // OrderPlaced arrives second
        observedEventIds.add(orderPlaced.eventId());
        System.out.println("OrderPlaced (evt-1) observed -- checking deferred events for anything now unblocked...");

        pendingUntilCauseArrives.removeIf(deferred -> {
            if (observedEventIds.contains(deferred.causedByEventId())) {
                System.out.println("  now processing deferred PaymentAuthorized for " + deferred.orderId() + " -- its cause has been confirmed.");
                return true; // remove from pending, it's been processed
            }
            return false;
        });
    }
}
```

**How to run:** `javac CausalDeferral.java && java CausalDeferral` (JDK 17+).

Expected output:
```
PaymentAuthorized arrived but its cause (evt-1) hasn't been observed -- DEFERRED, not processed.
OrderPlaced (evt-1) observed -- checking deferred events for anything now unblocked...
  now processing deferred PaymentAuthorized for order-42 -- its cause has been confirmed.
```

The same out-of-order arrival from Level 1 no longer produces an impossible state — `PaymentAuthorized` is correctly held back until `OrderPlaced` is genuinely confirmed observed.

### Level 3 — Advanced

```java
// File: ThreeEventCausalChain.java -- three causally-linked events arrive in a
// FULLY scrambled order; the consumer correctly reorders and processes them by causal dependency.
import java.util.*;

public class ThreeEventCausalChain {
    record CausalEvent(String eventId, String description, String causedByEventId) {} // null cause = root event

    public static void main(String[] args) {
        // the TRUE causal chain: OrderPlaced -> PaymentAuthorized -> ShipmentScheduled
        // but they ARRIVE scrambled: ShipmentScheduled, OrderPlaced, PaymentAuthorized
        List<CausalEvent> arrivalOrder = List.of(
            new CausalEvent("evt-3", "ShipmentScheduled", "evt-2"),
            new CausalEvent("evt-1", "OrderPlaced", null),
            new CausalEvent("evt-2", "PaymentAuthorized", "evt-1")
        );

        Set<String> observedEventIds = new HashSet<>();
        List<CausalEvent> pending = new ArrayList<>();
        List<String> processedInOrder = new ArrayList<>();

        for (CausalEvent event : arrivalOrder) {
            pending.add(event);
            System.out.println("Arrived: " + event.description() + " (id=" + event.eventId() + ", cause=" + event.causedByEventId() + ")");

            // repeatedly sweep pending for anything now unblocked, since resolving ONE
            // event's cause can unblock a CHAIN of subsequent events in the same pass
            boolean progressed = true;
            while (progressed) {
                progressed = false;
                Iterator<CausalEvent> it = pending.iterator();
                while (it.hasNext()) {
                    CausalEvent candidate = it.next();
                    boolean causeSatisfied = candidate.causedByEventId() == null || observedEventIds.contains(candidate.causedByEventId());
                    if (causeSatisfied) {
                        observedEventIds.add(candidate.eventId());
                        processedInOrder.add(candidate.description());
                        System.out.println("  processed: " + candidate.description());
                        it.remove();
                        progressed = true;
                    }
                }
            }
        }

        System.out.println("Final processing order (CAUSALLY correct, despite scrambled arrival): " + processedInOrder);
    }
}
```

**How to run:** `javac ThreeEventCausalChain.java && java ThreeEventCausalChain` (JDK 17+).

Expected output:
```
Arrived: ShipmentScheduled (id=evt-3, cause=evt-2)
Arrived: OrderPlaced (id=evt-1, cause=null)
  processed: OrderPlaced
Arrived: PaymentAuthorized (id=evt-2, cause=evt-1)
  processed: PaymentAuthorized
  processed: ShipmentScheduled
Final processing order (CAUSALLY correct, despite scrambled arrival): [OrderPlaced, PaymentAuthorized, ShipmentScheduled]
```

## 6. Walkthrough

1. **Level 1** — the code processes `payment` before `orderPlaced` purely because that's the order they were handled in `main`, with no check of whether `order-42` is even known yet; the printed "BUG" line is the direct, observable symptom of ignoring causality.
2. **Level 2, deferral instead of immediate processing** — when `payment` arrives, the code checks `observedEventIds.contains(payment.causedByEventId())`; since `"evt-1"` hasn't been added yet, `payment` is placed into `pendingUntilCauseArrives` instead of being acted on.
3. **Level 2, unblocking on the cause's arrival** — once `orderPlaced` is processed and `"evt-1"` is added to `observedEventIds`, the `removeIf` sweep re-checks every deferred event's `causedByEventId` against the now-updated set, finds `payment`'s cause satisfied, and processes it at that point instead.
4. **Level 3, a three-link chain arriving scrambled** — `arrivalOrder` deliberately lists `ShipmentScheduled` (which depends on `PaymentAuthorized`, which depends on `OrderPlaced`) *first*, testing whether the consumer can correctly hold back not just one deferred event but a whole dependent chain.
5. **Level 3, the repeated sweep** — after each new arrival, the `while (progressed)` loop keeps scanning `pending` and processing any event whose `causedByEventId` is now satisfied, and it repeats this scan until a full pass makes no further progress — this is what allows resolving `OrderPlaced` to immediately cascade into also resolving `PaymentAuthorized` and then `ShipmentScheduled` in the same pass, once all three have genuinely arrived.
6. **Level 3, tracing the three arrivals** — `ShipmentScheduled` arrives first but its cause (`evt-2`) is unsatisfied, so it stays in `pending`; `OrderPlaced` arrives second with no cause requirement (`null`), so it's processed immediately; `PaymentAuthorized` arrives third, its cause (`evt-1`) is now satisfied, so it processes immediately, which *in the same sweep* also satisfies `ShipmentScheduled`'s cause (`evt-2`), letting it process right after, all triggered by that single third arrival.
7. **Level 3, the final proof** — `processedInOrder` ends as `[OrderPlaced, PaymentAuthorized, ShipmentScheduled]` — the true causal order — despite `arrivalOrder` having delivered them in the sequence `[ShipmentScheduled, OrderPlaced, PaymentAuthorized]`, demonstrating that causal-order processing was recovered entirely from the explicit `causedByEventId` pointers, independent of actual arrival order.

## 7. Gotchas & takeaways

> **Gotcha:** a causal dependency that never arrives (the "cause" event was lost, or belongs to a producer that crashed before publishing it) leaves the dependent event stuck in the pending set forever — a production implementation of this pattern needs a bounded wait with a fallback (alerting, a [dead letter queue](0123-dead-letter-queue-dlq.md), or a timeout-based escalation), not an indefinitely-growing pending list.

- Causality is a stronger property than per-channel ordering: it's about true cause-and-effect relationships between events, which can be violated even when each individual channel delivers in perfect FIFO order.
- Explicit causal pointers (an event carrying a reference to the event that caused it) let a consumer detect and defer out-of-order effects rather than acting on an impossible intermediate state.
- A repeated sweep over pending events after each arrival correctly cascades the resolution of an entire causal chain, not just a single deferred event.
- This concern is distinct from, and layered on top of, [message ordering guarantees](0119-message-ordering-guarantees.md) — partition-key ordering solves same-channel ordering, causal tracking solves cross-channel, cross-producer ordering.
- A production causal-deferral mechanism needs a bounded wait and fallback path for causes that never arrive, to avoid an unbounded, silently-growing backlog of stuck events.
