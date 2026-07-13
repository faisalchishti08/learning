---
card: microservices
gi: 335
slug: event-sourcing
title: "Event sourcing"
---

## 1. What it is

**Event sourcing** is a way of persisting a service's data where, instead of storing only the current state of each entity (the usual approach: an `orders` table row that gets overwritten on every update), you store the full, ordered sequence of events that led to that state — `OrderPlaced`, `ItemAdded`, `OrderShipped` — and derive the current state by replaying those events from the beginning. The events are the single source of truth; any "current state" view is just a computed projection of them.

## 2. Why & when

Conventional storage (save only the current row) throws away history: once an order's status changes from `PENDING` to `SHIPPED`, there is no record of what it used to be, when it changed, or why, unless you build separate audit logging for that purpose. Event sourcing makes history the *primary* data, not an afterthought — every state the entity ever passed through is reconstructable exactly, which is valuable for audit trails, debugging ("why does this order look like this?"), and building entirely new projections of old data without having captured them in advance (a new report can replay history from day one, even though nobody thought to build that report until today).

Use event sourcing for entities where history, auditability, or the ability to derive new views from past events after the fact is genuinely valuable — financial ledgers, order lifecycles, anything requiring a strict audit trail. It adds real complexity (a different mental model for reads and writes, and a need for [snapshots](0337-snapshots-in-event-sourcing.md) once histories get long) — don't reach for it as a default for every service; use it where its specific benefits (history, replayability) actually matter to the domain.

## 3. Core concept

Every state change is appended as an immutable event to an **event store** (an append-only log, one stream per entity). Current state is computed by folding (reducing) all of an entity's events in order: `state = events.reduce(initialState, applyEvent)`. Because events are never modified or deleted, the full history is always available, and any new way of interpreting that history (a new projection) can be built by replaying the same events through new logic.

```java
record OrderPlaced(String orderId) {}
record ItemAdded(String orderId, String item) {}
record OrderShipped(String orderId) {}
// Current state = fold every event for this orderId, in order, starting from an empty order.
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An append-only stream of events for order-1: OrderPlaced, ItemAdded, ItemAdded, OrderShipped; current state is computed by folding all four events in order">
  <rect x="20" y="50" width="110" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="75" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">OrderPlaced</text>
  <rect x="150" y="50" width="110" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="205" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">ItemAdded</text>
  <rect x="280" y="50" width="110" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="335" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">ItemAdded</text>
  <rect x="410" y="50" width="110" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">OrderShipped</text>

  <line x1="130" y1="67" x2="145" y2="67" stroke="#8b949e" marker-end="url(#a335)"/>
  <line x1="260" y1="67" x2="275" y2="67" stroke="#8b949e" marker-end="url(#a335)"/>
  <line x1="390" y1="67" x2="405" y2="67" stroke="#8b949e" marker-end="url(#a335)"/>

  <line x1="465" y1="84" x2="465" y2="115" stroke="#79c0ff" marker-end="url(#a335b)"/>
  <text x="465" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">fold ALL 4 events -&gt; current state: SHIPPED, 2 items</text>

  <defs>
    <marker id="a335" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a335b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The event stream is the source of truth; current state is derived by folding every event for the entity, in order.

## 5. Runnable example

Scenario: an order entity, first modeled the conventional way (overwrite current state, history lost), then rebuilt as an event-sourced stream that derives current state by replaying events, and finally extended to answer a "what did this look like at a past point in time" query — something the conventional approach can never do.

### Level 1 — Basic

```java
// File: ConventionalStateOnly.java -- only the CURRENT state is stored;
// every update OVERWRITES the previous state, and history is gone.
import java.util.*;

public class ConventionalStateOnly {
    record OrderState(String status, List<String> items) {}
    static Map<String, OrderState> orders = new HashMap<>();

    static void placeOrder(String id) { orders.put(id, new OrderState("PLACED", new ArrayList<>())); }
    static void addItem(String id, String item) {
        OrderState current = orders.get(id);
        current.items().add(item);
    }
    static void shipOrder(String id) {
        OrderState current = orders.get(id);
        orders.put(id, new OrderState("SHIPPED", current.items())); // OVERWRITES -- "PLACED" is gone forever
    }

    public static void main(String[] args) {
        placeOrder("order-1");
        addItem("order-1", "widget");
        shipOrder("order-1");

        System.out.println("Current state: " + orders.get("order-1"));
        System.out.println("What was the status when the widget was added? -- IMPOSSIBLE TO ANSWER, that history is gone.");
    }
}
```

How to run: `java ConventionalStateOnly.java`

Each call mutates or replaces the stored `OrderState` directly. By the time `main` asks what the order's status was at the moment the widget was added, there is simply no data left to answer that — the conventional model only ever kept the *latest* state, discarding every state that came before it.

### Level 2 — Intermediate

```java
// File: EventSourcedOrder.java -- every change is appended as an EVENT;
// current state is DERIVED by folding all events for the entity, in order.
import java.util.*;

public class EventSourcedOrder {
    sealed interface OrderEvent permits OrderPlaced, ItemAdded, OrderShipped { String orderId(); }
    record OrderPlaced(String orderId) implements OrderEvent {}
    record ItemAdded(String orderId, String item) implements OrderEvent {}
    record OrderShipped(String orderId) implements OrderEvent {}

    record OrderState(String status, List<String> items) {}
    static List<OrderEvent> eventStore = new ArrayList<>(); // the ONLY source of truth -- append-only

    static void append(OrderEvent event) { eventStore.add(event); }

    static OrderState currentState(String orderId) { // DERIVED, never stored directly
        OrderState state = new OrderState("NONE", new ArrayList<>());
        for (OrderEvent event : eventStore) {
            if (!event.orderId().equals(orderId)) continue;
            state = apply(state, event);
        }
        return state;
    }

    static OrderState apply(OrderState state, OrderEvent event) {
        if (event instanceof OrderPlaced) return new OrderState("PLACED", new ArrayList<>());
        if (event instanceof ItemAdded ia) { List<String> items = new ArrayList<>(state.items()); items.add(ia.item()); return new OrderState(state.status(), items); }
        if (event instanceof OrderShipped) return new OrderState("SHIPPED", state.items());
        return state;
    }

    public static void main(String[] args) {
        append(new OrderPlaced("order-1"));
        append(new ItemAdded("order-1", "widget"));
        append(new OrderShipped("order-1"));

        System.out.println("Current state (derived by folding all events): " + currentState("order-1"));
        System.out.println("Full event history is STILL there: " + eventStore.size() + " events, nothing was ever overwritten.");
    }
}
```

How to run: `java EventSourcedOrder.java`

`currentState` computes the order's state fresh each time by folding every recorded event for that order, in order, through `apply` — nothing about the entity's current state is ever stored directly; it's always a derived view. Because `eventStore` is append-only, every event — including the fact that the order was once merely `PLACED` before it was `SHIPPED` — remains permanently available.

### Level 3 — Advanced

```java
// File: PointInTimeQuery.java -- because the FULL event history is
// preserved, we can answer "what did this order look like at an earlier
// point" by folding only the events UP TO that point -- something the
// conventional (state-only) approach can never do.
import java.util.*;

public class PointInTimeQuery {
    sealed interface OrderEvent permits OrderPlaced, ItemAdded, OrderShipped { String orderId(); int sequenceNumber(); }
    record OrderPlaced(String orderId, int sequenceNumber) implements OrderEvent {}
    record ItemAdded(String orderId, int sequenceNumber, String item) implements OrderEvent {}
    record OrderShipped(String orderId, int sequenceNumber) implements OrderEvent {}

    record OrderState(String status, List<String> items) {}
    static List<OrderEvent> eventStore = new ArrayList<>();

    static OrderState stateAsOf(String orderId, int upToSequenceNumber) { // the KEY capability: bound the fold
        OrderState state = new OrderState("NONE", new ArrayList<>());
        for (OrderEvent event : eventStore) {
            if (!event.orderId().equals(orderId) || event.sequenceNumber() > upToSequenceNumber) continue;
            state = apply(state, event);
        }
        return state;
    }

    static OrderState apply(OrderState state, OrderEvent event) {
        if (event instanceof OrderPlaced) return new OrderState("PLACED", new ArrayList<>());
        if (event instanceof ItemAdded ia) { List<String> items = new ArrayList<>(state.items()); items.add(ia.item()); return new OrderState(state.status(), items); }
        if (event instanceof OrderShipped) return new OrderState("SHIPPED", state.items());
        return state;
    }

    public static void main(String[] args) {
        eventStore.add(new OrderPlaced("order-1", 1));
        eventStore.add(new ItemAdded("order-1", 2, "widget"));
        eventStore.add(new OrderShipped("order-1", 3));

        System.out.println("State as of sequence 1 (right after placing): " + stateAsOf("order-1", 1));
        System.out.println("State as of sequence 2 (right after adding the widget, BEFORE shipping): " + stateAsOf("order-1", 2));
        System.out.println("State as of sequence 3 (current, after shipping): " + stateAsOf("order-1", 3));
    }
}
```

How to run: `java PointInTimeQuery.java`

`stateAsOf` folds only the events whose `sequenceNumber()` is at most the requested cutoff, ignoring anything later. Calling it with `upToSequenceNumber=1` reconstructs the state right after `OrderPlaced` alone: `status="PLACED"`, no items yet. Calling it with `2` includes `ItemAdded` too, showing the order as `PLACED` with `["widget"]`. Calling it with `3` includes `OrderShipped`, matching the full current state. This ability to answer "what did it look like back then" precisely and correctly is exactly the benefit that Level 1's conventional, overwrite-only storage could never provide.

## 6. Walkthrough

Trace `PointInTimeQuery.main` in order. **First**, three events are appended to `eventStore`, each tagged with an increasing `sequenceNumber` (`1`, `2`, `3`) for `"order-1"`.

**`stateAsOf("order-1", 1)` runs first.** Its loop walks `eventStore`; the `OrderPlaced` event has `sequenceNumber()=1`, which is not greater than the cutoff `1`, so it's applied via `apply`, setting `state` to `("PLACED", [])`. The `ItemAdded` event has `sequenceNumber()=2`, which *is* greater than the cutoff `1`, so the `continue` skips it, and likewise for `OrderShipped` at `sequenceNumber()=3`. The method returns `("PLACED", [])`.

**`stateAsOf("order-1", 2)` runs next.** This time the cutoff is `2`, so both `OrderPlaced` (`sequenceNumber=1`) and `ItemAdded` (`sequenceNumber=2`) pass the filter and are applied in order — first setting status to `PLACED`, then adding `"widget"` to the items list — while `OrderShipped` (`sequenceNumber=3`) is still skipped. The method returns `("PLACED", ["widget"])`.

**`stateAsOf("order-1", 3)` runs last.** With cutoff `3`, all three events pass the filter and are applied in sequence: `PLACED` with no items, then `"widget"` added, then status flipped to `SHIPPED` — the method returns `("SHIPPED", ["widget"])`, matching the order's true current state.

```
Events (in order): OrderPlaced(seq1) -> ItemAdded(seq2,"widget") -> OrderShipped(seq3)
stateAsOf(cutoff=1) -> fold [seq1]          -> (PLACED, [])
stateAsOf(cutoff=2) -> fold [seq1,seq2]     -> (PLACED, [widget])
stateAsOf(cutoff=3) -> fold [seq1,seq2,seq3]-> (SHIPPED, [widget])
```

## 7. Gotchas & takeaways

> Folding every event from the beginning of time to compute current state gets slower as an entity accumulates history — an order with thousands of events would be expensive to replay on every read. This is exactly the problem [snapshots in event sourcing](0337-snapshots-in-event-sourcing.md) solve: periodically caching a computed state so folding only needs to resume from there.

- Event sourcing stores the full, ordered history of events as the source of truth; current (or any past) state is always a derived, computed view, never stored as the "real" data.
- This unlocks genuine auditability and the ability to answer point-in-time and "what changed and why" questions that conventional overwrite-based storage cannot answer after the fact.
- It adds real complexity — folding logic, and eventually [snapshots](0337-snapshots-in-event-sourcing.md) for performance — so reserve it for entities where history and replayability are genuinely valuable to the domain.
- The append-only event log itself is typically implemented as, or alongside, an [event store](0336-event-store.md), a storage technology purpose-built for this access pattern.
