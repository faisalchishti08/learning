---
card: system-design
gi: 202
slug: event-sourcing
title: Event sourcing
---

## 1. What it is

**Event sourcing** stores every change to an entity as an immutable **event** in an append-only log, instead of storing only the entity's current state. The entity's current state is not stored directly — it is **derived** by replaying every event for that entity, in order, from the beginning.

## 2. Why & when

A normal (state-based) system overwrites a row every time something changes — once you `UPDATE` a row, the previous value is gone, unless you built separate audit logging for it. Event sourcing makes the history the primary source of truth: every `OrderPlaced`, `ItemAdded`, `OrderShipped` event is stored forever, and "current state" is just a value computed by folding all those events together.

This gives you a complete, trustworthy audit trail for free, the ability to answer "what did this look like last Tuesday" by replaying events up to that point, and the ability to fix a bug in how state is derived and recompute all state correctly from the untouched event history. The cost is real: replaying a long event stream to get current state is slower than a plain read (usually solved with periodic **snapshots**), and the query patterns [CQRS](0201-cqrs-command-query-responsibility-segregation.md) needs pair naturally with this approach because a plain "current state" table is not convenient to query on its own. Use event sourcing where the audit trail itself is valuable (finance, inventory, anything regulators care about) or where "what changed and why" is a first-class business question. Avoid it for simple entities where nobody will ever ask about history.

## 3. Core concept

- **Events are the source of truth, not the current state.** The event log is append-only — you never update or delete an event, you only ever append new ones.
- **Current state = fold(events).** To get an order's current state, you start from an empty/initial state and apply every event for that order, in order, one at a time. Each event knows how to transform the state it is applied to.
- **Replay is deterministic.** Applying the same sequence of events always produces the same resulting state — this is what makes "what did it look like at event #40" a well-defined question.
- **Snapshots as an optimization.** Replaying thousands of events on every read is slow, so systems periodically save a snapshot of the derived state (e.g. every 100 events) and only replay events *after* the snapshot to get current state.
- **Pairs with CQRS.** Because folding events is not a convenient way to answer "give me all shipped orders this week," event-sourced systems typically also maintain a separate, queryable read model — this is exactly the [CQRS](0201-cqrs-command-query-responsibility-segregation.md) pattern, kept up to date by a projector consuming the same event stream.

## 4. Diagram

```
  APPEND-ONLY EVENT LOG for order ORD-1  (never modified, only appended to)

  #1 OrderPlaced   {items: []}
  #2 ItemAdded     {item: "mouse"}
  #3 ItemAdded     {item: "keyboard"}
  #4 ItemRemoved   {item: "mouse"}
  #5 OrderShipped  {}
        |
        |  replay events #1..#5, in order, folding each into state
        v
  CURRENT STATE (derived, not stored directly):
    { items: ["keyboard"], status: "SHIPPED" }

  Replaying only #1..#3 instead gives an EARLIER state:
    { items: ["mouse", "keyboard"], status: "PLACED" }
```
*Caption: the log never changes. Every version of the order's state, past or present, is just "replay up to event N" — nothing is ever overwritten.*

## 5. Runnable example

**Level 1 — Basic.** An append-only event log and a fold function that derives current state from it.

**Level 2 — Intermediate.** Replay only up to a given point to reconstruct a past state ("what did this look like at event #3").

**Level 3 — Advanced.** Add a snapshot so replay does not have to start from event #1 every time.

```java
// EventSourcingDemo.java
import java.util.*;

public class EventSourcingDemo {

    // ---------- The events (immutable facts, never changed once appended) ----------
    sealed interface OrderEvent permits OrderPlaced, ItemAdded, ItemRemoved, OrderShipped {}
    record OrderPlaced(String orderId) implements OrderEvent {}
    record ItemAdded(String item) implements OrderEvent {}
    record ItemRemoved(String item) implements OrderEvent {}
    record OrderShipped() implements OrderEvent {}

    // ---------- Derived state - NOT stored directly, computed by folding events ----------
    record OrderState(List<String> items, String status) {
        static OrderState initial() { return new OrderState(new ArrayList<>(), "NEW"); }
    }

    // ---------- Level 1: append-only log + fold ----------
    static class EventStore {
        List<OrderEvent> log = new ArrayList<>();
        void append(OrderEvent event) {
            log.add(event); // NEVER modifies or removes existing entries
            System.out.println("  [log] appended #" + log.size() + ": " + event);
        }
    }

    static OrderState apply(OrderState state, OrderEvent event) {
        List<String> items = new ArrayList<>(state.items());
        String status = state.status();
        switch (event) {
            case OrderPlaced e -> status = "PLACED";
            case ItemAdded e -> items.add(e.item());
            case ItemRemoved e -> items.remove(e.item());
            case OrderShipped e -> status = "SHIPPED";
        }
        return new OrderState(items, status);
    }

    // Fold the whole log (or a prefix of it) into a state.
    static OrderState replay(List<OrderEvent> events, int upToInclusive) {
        OrderState state = OrderState.initial();
        for (int i = 0; i < upToInclusive; i++) {
            state = apply(state, events.get(i));
        }
        return state;
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - append events, then derive current state by replay:");
        EventStore store = new EventStore();
        store.append(new OrderPlaced("ORD-1"));
        store.append(new ItemAdded("mouse"));
        store.append(new ItemAdded("keyboard"));
        store.append(new ItemRemoved("mouse"));
        store.append(new OrderShipped());

        OrderState current = replay(store.log, store.log.size());
        System.out.println("  current state (replay all 5 events): " + current);

        System.out.println("\nLevel 2 - reconstruct a PAST state by replaying only a prefix:");
        OrderState atEventThree = replay(store.log, 3); // only OrderPlaced, ItemAdded(mouse), ItemAdded(keyboard)
        System.out.println("  state as of event #3: " + atEventThree);

        System.out.println("\nLevel 3 - snapshot so replay does not start from event #1 every time:");
        // Take a snapshot after event #3, so future reads only replay events AFTER it.
        OrderState snapshot = replay(store.log, 3);
        int snapshotAtEvent = 3;
        System.out.println("  snapshot taken at event #" + snapshotAtEvent + ": " + snapshot);

        // To get current state now, start from the snapshot and replay only events #4 and #5.
        OrderState fromSnapshot = snapshot;
        for (int i = snapshotAtEvent; i < store.log.size(); i++) {
            fromSnapshot = apply(fromSnapshot, store.log.get(i));
        }
        System.out.println("  current state (snapshot + 2 events, not all 5): " + fromSnapshot);
        System.out.println("  matches full replay? " + fromSnapshot.equals(current));
    }
}
```

**How to run:** `java EventSourcingDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** five events are appended to `store.log`, one at a time — `OrderPlaced`, two `ItemAdded`, one `ItemRemoved`, and `OrderShipped`. None of these calls ever modifies an earlier entry; `log` only ever grows.
2. `replay(store.log, store.log.size())` starts from `OrderState.initial()` (empty items, status `"NEW"`) and calls `apply(...)` once per event, in order. Each `apply` call returns a **new** `OrderState` built from the previous one plus that one event's effect — `ItemAdded("mouse")` adds `"mouse"`, `ItemRemoved("mouse")` removes it again, and so on.
3. After all five events, the folded state is `{items: ["keyboard"], status: "SHIPPED"}` — `"mouse"` was added then removed, so only `"keyboard"` remains, and the final event set the status to shipped.
4. **Level 2:** `replay(store.log, 3)` folds only the first three events (`OrderPlaced`, `ItemAdded(mouse)`, `ItemAdded(keyboard)`), stopping before the removal and the shipment. The result, `{items: ["mouse", "keyboard"], status: "PLACED"}`, is exactly what the order looked like at that earlier point — the log made this "time travel" possible with no extra storage, because every state is just a replay boundary.
5. **Level 3:** rather than take the snapshot idea on faith, the code proves it. `snapshot` is the folded state after event #3. The final loop starts from that snapshot (not from `OrderState.initial()`) and applies only events #4 and #5 — the removal and the shipment. `fromSnapshot.equals(current)` prints `true`, showing the snapshot-plus-remainder approach produces the identical state as replaying all five events from scratch, but does less work.

## 7. Gotchas & takeaways

> **Gotcha:** event sourcing makes changing your mind about the past expensive. If you discover an event's *meaning* was wrong (not just a bug in how you fold it), you cannot simply edit history — the log is append-only. You typically append a correcting event instead, and every piece of code that folds the log must handle it.

- Store events as immutable facts in the past tense (`ItemAdded`, not `AddItem`) — this is the same naming discipline as [event-driven architecture](0200-event-driven-architecture.md), and for good reason: these events are often the same ones published to other services.
- Add snapshotting as soon as replay time becomes noticeable — do not wait until an entity has thousands of events and every read is visibly slow.
- Pair event sourcing with [CQRS](0201-cqrs-command-query-responsibility-segregation.md) for querying — folding events is great for "what is this one entity's state" but bad for "give me all orders shipped today," which needs a separate, queryable projection.
- This pattern is a significant commitment for a whole entity's lifecycle — do not adopt it for one part of a system that does not need history while forcing every read through a fold. Apply it where the audit trail and point-in-time queries are genuinely valuable.
