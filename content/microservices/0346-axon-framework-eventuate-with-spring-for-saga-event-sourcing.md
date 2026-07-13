---
card: microservices
gi: 346
slug: axon-framework-eventuate-with-spring-for-saga-event-sourcing
title: "Axon Framework / Eventuate with Spring for saga & event sourcing"
---

## 1. What it is

**Axon Framework** and **Eventuate** are two Java frameworks, each integrating with Spring, that provide ready-made infrastructure for [event sourcing](0335-event-sourcing.md) and [sagas](0320-saga-pattern.md) — an [event store](0336-event-store.md) implementation, aggregate modeling (entities whose state is built from events), saga orchestration support, and often a built-in [transactional outbox](0331-transactional-outbox-pattern.md)-equivalent for publishing events reliably. Instead of hand-building the event store, the fold/replay logic, and the saga coordination discussed in earlier topics, these frameworks provide annotations and base classes that implement the same concepts for you.

## 2. Why & when

Building event sourcing and sagas from scratch — as the earlier topics in this section did with plain Java, for teaching purposes — is real, non-trivial infrastructure: an append-only store with optimistic concurrency, snapshotting, saga state persistence and resumption, idempotent event handling. Axon and Eventuate exist because most teams building several event-sourced services don't want to re-solve these problems independently in each one. They provide, respectively, `@Aggregate` and `@Saga` (Axon) or its own comparable annotations (Eventuate) that map directly onto the concepts already covered: an aggregate's event-sourced state, a saga's steps and compensations, and the underlying event store and outbox machinery, all wired into Spring's dependency injection.

Adopt one of these frameworks once you have multiple genuinely event-sourced entities or non-trivial sagas across a system, and the cost of hand-rolling and maintaining that infrastructure yourself outweighs learning a framework's conventions. For a single simple saga or one event-sourced entity, the hand-built approach from earlier topics may still be simpler and more transparent; these frameworks pay off at scale, across many entities and sagas, where consistent infrastructure matters more than initial simplicity.

## 3. Core concept

An Axon `@Aggregate` class holds command handlers (`@CommandHandler`) that validate a command and, if valid, apply an event (`AggregateLifecycle.apply(...)`); event sourcing handlers (`@EventSourcingHandler`) update the aggregate's in-memory state from each applied event — Axon's infrastructure handles persisting events to its event store and rebuilding aggregate state by replaying them, exactly the fold-based reconstruction discussed in [event sourcing](0335-event-sourcing.md), but implemented for you.

```java
@Aggregate
class OrderAggregate {
    @AggregateIdentifier String orderId;
    @CommandHandler
    public OrderAggregate(PlaceOrderCommand cmd) { apply(new OrderPlacedEvent(cmd.orderId())); }
    @EventSourcingHandler
    public void on(OrderPlacedEvent event) { this.orderId = event.orderId(); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A command is sent to an Axon aggregate; the command handler validates and applies an event; the event is persisted to Axon's event store and used to update the aggregate's in-memory state via the event sourcing handler">
  <rect x="20" y="60" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">PlaceOrderCommand</text>

  <line x1="160" y1="77" x2="230" y2="77" stroke="#8b949e" marker-end="url(#a346)"/>
  <rect x="240" y="60" width="160" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">@CommandHandler applies event</text>

  <line x1="400" y1="77" x2="470" y2="77" stroke="#8b949e" marker-end="url(#a346)"/>
  <rect x="480" y="60" width="140" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="550" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Axon event store</text>

  <line x1="550" y1="94" x2="320" y2="120" stroke="#3fb950" marker-end="url(#a346b)"/>
  <text x="430" y="130" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">@EventSourcingHandler updates state</text>

  <defs>
    <marker id="a346" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a346b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

A command handler applies an event, which is persisted to the event store and folded back into the aggregate's own in-memory state.

## 5. Runnable example

Scenario: an order aggregate, first modeled with hand-written command handling and manual event application (the pattern from earlier topics), then rebuilt to mirror Axon's `@CommandHandler`/`@EventSourcingHandler` split more explicitly, and finally extended to show how a framework-provided saga would react to the same event, coordinating a next step automatically.

### Level 1 — Basic

```java
// File: HandRolledAggregate.java -- the pattern from earlier topics:
// manually applying and folding events, with NO framework support.
import java.util.*;

public class HandRolledAggregate {
    record OrderPlacedEvent(String orderId) {}
    static List<OrderPlacedEvent> eventStore = new ArrayList<>();
    static String currentOrderId; // manually maintained "aggregate state"

    static void handlePlaceOrderCommand(String orderId) {
        OrderPlacedEvent event = new OrderPlacedEvent(orderId);
        eventStore.add(event);       // manual: persist
        currentOrderId = event.orderId(); // manual: fold into state
        System.out.println("hand-rolled: command handled, event applied and folded manually");
    }

    public static void main(String[] args) {
        handlePlaceOrderCommand("order-1");
        System.out.println("Aggregate state: orderId=" + currentOrderId + ", event store size=" + eventStore.size());
    }
}
```

How to run: `java HandRolledAggregate.java`

`handlePlaceOrderCommand` does everything manually: build the event, append it to a list standing in for an event store, and update `currentOrderId` to reflect it — every step written and maintained by hand, exactly the discipline required without a dedicated framework.

### Level 2 — Intermediate

```java
// File: AxonStyleAggregate.java -- mirrors Axon's separation between
// COMMAND HANDLING (decide what event to apply) and EVENT SOURCING
// HANDLING (fold an applied event into state) as two distinct methods,
// the way @CommandHandler and @EventSourcingHandler split responsibilities.
import java.util.*;

public class AxonStyleAggregate {
    record OrderPlacedEvent(String orderId) {}
    record ItemAddedEvent(String orderId, String item) {}

    static class OrderAggregate { // mirrors an Axon @Aggregate class's shape
        String orderId;
        List<String> items = new ArrayList<>();

        // Mirrors @CommandHandler: validates and decides WHAT event to apply.
        void handlePlaceOrderCommand(String orderId) {
            System.out.println("@CommandHandler-style: validating PlaceOrderCommand...");
            apply(new OrderPlacedEvent(orderId));
        }
        void handleAddItemCommand(String item) {
            System.out.println("@CommandHandler-style: validating AddItemCommand...");
            apply(new ItemAddedEvent(this.orderId, item));
        }

        // Mirrors the framework's internal "apply" -- persists AND immediately folds.
        void apply(Object event) {
            eventStore.add(event);
            on(event); // the framework calls the matching @EventSourcingHandler automatically; here, done explicitly
        }

        // Mirrors @EventSourcingHandler: ONLY folds state, no business logic/validation here.
        void on(Object event) {
            if (event instanceof OrderPlacedEvent e) this.orderId = e.orderId();
            if (event instanceof ItemAddedEvent e) this.items.add(e.item());
        }
    }

    static List<Object> eventStore = new ArrayList<>();

    public static void main(String[] args) {
        OrderAggregate aggregate = new OrderAggregate();
        aggregate.handlePlaceOrderCommand("order-1");
        aggregate.handleAddItemCommand("widget");

        System.out.println("Aggregate state: orderId=" + aggregate.orderId + ", items=" + aggregate.items);
        System.out.println("Event store: " + eventStore.size() + " events -- this SAME split (command handler decides, event handler folds) is exactly Axon's model.");
    }
}
```

How to run: `java AxonStyleAggregate.java`

`handlePlaceOrderCommand` and `handleAddItemCommand` mirror `@CommandHandler` methods: they contain business validation and decide which event to apply, but never mutate state directly. `apply` mirrors the framework's internal machinery: it persists the event and calls `on`, which mirrors `@EventSourcingHandler` — purely folding logic, with no validation. This separation (validate-and-decide versus fold-only) is exactly how Axon structures aggregates, just implemented explicitly here instead of via annotations and a framework runtime.

### Level 3 — Advanced

```java
// File: SagaReactsToAggregateEvent.java -- extends the aggregate with a
// SAGA-style reaction: when OrderPlacedEvent is applied, a saga handler
// automatically issues the NEXT command (ReserveStock) -- mirroring how
// Axon's @SagaEventHandler / @StartSaga would react to an aggregate's event.
import java.util.*;

public class SagaReactsToAggregateEvent {
    record OrderPlacedEvent(String orderId) {}
    record ReserveStockCommand(String orderId) {}
    record StockReservedEvent(String orderId) {}

    static List<Object> eventStore = new ArrayList<>();
    static List<Object> issuedCommands = new ArrayList<>(); // commands the saga issues in reaction to events

    static class OrderAggregate {
        String orderId;
        void handlePlaceOrderCommand(String orderId) { apply(new OrderPlacedEvent(orderId)); }
        void apply(Object event) { eventStore.add(event); on(event); dispatchToSaga(event); }
        void on(Object event) { if (event instanceof OrderPlacedEvent e) this.orderId = e.orderId(); }
    }

    // Mirrors a @Saga class's @SagaEventHandler methods -- reacts to events, issues new commands.
    static void dispatchToSaga(Object event) {
        if (event instanceof OrderPlacedEvent e) {
            System.out.println("saga: OrderPlacedEvent received -- issuing ReserveStockCommand for " + e.orderId());
            issuedCommands.add(new ReserveStockCommand(e.orderId()));
            handleReserveStockCommand(e.orderId()); // in real Axon, this would route to the inventory aggregate/service
        }
    }

    static void handleReserveStockCommand(String orderId) {
        System.out.println("inventory: handling ReserveStockCommand for " + orderId);
        Object event = new StockReservedEvent(orderId);
        eventStore.add(event);
        System.out.println("saga: StockReservedEvent received -- saga step complete for " + orderId);
    }

    public static void main(String[] args) {
        OrderAggregate aggregate = new OrderAggregate();
        aggregate.handlePlaceOrderCommand("order-1");

        System.out.println("Event store (full history): " + eventStore);
        System.out.println("Commands the saga issued along the way: " + issuedCommands);
    }
}
```

How to run: `java SagaReactsToAggregateEvent.java`

`OrderAggregate.apply` now calls `dispatchToSaga` after folding state, mirroring how a real Axon `@Saga` class's `@SagaEventHandler` methods are automatically invoked whenever a matching event is published. `dispatchToSaga` reacts to `OrderPlacedEvent` by constructing and "issuing" a `ReserveStockCommand`, then (standing in for the framework routing that command to the appropriate handler) directly calls `handleReserveStockCommand`, which produces a `StockReservedEvent`. The whole chain — order placed, saga reacts, stock reserved — happens automatically from a single initial command, exactly the kind of coordination a real saga framework provides without the application code needing to manually wire each step's trigger.

## 6. Walkthrough

Trace `SagaReactsToAggregateEvent.main` in order. **First**, `aggregate.handlePlaceOrderCommand("order-1")` runs, which calls `apply(new OrderPlacedEvent("order-1"))`.

**Inside `apply`**, three things happen in sequence: the event is appended to `eventStore`; `on(event)` runs, setting `aggregate.orderId` to `"order-1"`; and `dispatchToSaga(event)` runs.

**Inside `dispatchToSaga`**, the event matches `OrderPlacedEvent`, so the saga branch executes: it prints that it's reacting, constructs a `ReserveStockCommand`, appends it to `issuedCommands`, and calls `handleReserveStockCommand("order-1")` — modeling the framework automatically routing the saga-issued command to its handler.

**Inside `handleReserveStockCommand`**, a `StockReservedEvent` is constructed and appended to `eventStore`, and a message confirms the saga step completed — note that in this simplified example, `StockReservedEvent` isn't itself folded into any aggregate's state or dispatched further, but in a real framework it could trigger yet another saga step or aggregate update the same way `OrderPlacedEvent` did.

**Finally**, `main` prints `eventStore` (containing both `OrderPlacedEvent` and `StockReservedEvent`, in the order they occurred) and `issuedCommands` (containing the one `ReserveStockCommand` the saga issued along the way) — demonstrating that a single initial `handlePlaceOrderCommand` call triggered an entire chain of reactions automatically, driven purely by events flowing through the aggregate and saga dispatch logic.

```
handlePlaceOrderCommand(order-1)
  -> apply(OrderPlacedEvent) -> eventStore+=[OrderPlaced] -> fold state -> dispatchToSaga
       -> saga reacts: issue ReserveStockCommand -> handleReserveStockCommand
            -> eventStore+=[StockReserved]
Final eventStore: [OrderPlaced, StockReserved]     issuedCommands: [ReserveStockCommand]
```

## 7. Gotchas & takeaways

> Adopting Axon or Eventuate is a significant architectural commitment — your aggregates' persistence model, and often your messaging infrastructure, become tied to the framework's own event store and command/event bus. Evaluate this tradeoff deliberately against hand-rolling the specific pieces (event store, saga coordination) you actually need; a framework earns its cost at a scale where consistent infrastructure across many aggregates and sagas outweighs the flexibility of a custom-built, more transparent solution.

- Axon and Eventuate provide ready-made event store, aggregate, and saga infrastructure for Spring applications, implementing the same event sourcing and saga concepts covered in earlier topics, without hand-building them.
- Axon's `@CommandHandler` (validate and decide what event to apply) and `@EventSourcingHandler` (fold an event into state) mirror the same separation of concerns a hand-rolled aggregate should already maintain.
- A framework's saga support (`@Saga`, `@SagaEventHandler`) automates the event-to-next-command wiring that a hand-built [orchestration-based saga](0322-orchestration-based-saga.md) or [choreography-based saga](0321-choreography-based-saga.md) would otherwise require you to wire manually.
- Reach for one of these frameworks once the number and complexity of event-sourced entities and sagas in your system makes hand-rolled infrastructure a genuine maintenance burden, not as a default starting point for a single simple case.
