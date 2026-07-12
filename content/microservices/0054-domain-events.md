---
card: microservices
gi: 54
slug: domain-events
title: Domain events
---

## 1. What it is

A **domain event** is an immutable record of something significant that happened in the domain, expressed in past tense using the domain's own [ubiquitous language](0048-ubiquitous-language.md) — `OrderPlaced`, `PaymentFailed`, `ReservationConfirmed`. Unlike a generic notification or a technical "data changed" signal, a domain event captures a *meaningful business fact*, named the way a domain expert would describe it, carrying exactly the data relevant to that fact. Domain events are the concrete mechanism behind [decentralized data management](0009-decentralized-data-management.md)'s eventual consistency and the [self-contained service pattern](0042-self-contained-service-pattern.md)'s locally-updated copies — a service publishes an event when something meaningful happens inside its own aggregate, and other services react to it independently.

## 2. Why & when

Without domain events, keeping other parts of a system aware of what happened inside one aggregate requires either a synchronous call (with all the coupling and fragility that implies) or, worse, other code reaching directly into an aggregate's internals to notice a change — both violate boundaries this section has built up carefully. Domain events give aggregates a clean way to announce meaningful facts about themselves without knowing or caring who, if anyone, is listening — the aggregate that raises `OrderPlaced` doesn't need to know whether `InventoryService`, `NotificationService`, both, or neither will react to it.

Raise a domain event whenever something happens inside an aggregate that other parts of the system might genuinely need to know about — a state transition, a significant calculation result, a business rule being satisfied or violated. Don't raise an event for every trivial internal change; reserve them for facts a domain expert would consider worth mentioning in a conversation about what happened.

## 3. Core concept

A domain event has three defining properties:

1. **Immutable** — it's a record of something that already happened; it cannot be changed after the fact, only reacted to.
2. **Named in past tense, in the domain's own language** — `OrderPlaced`, not `UpdateOrderStatus`; the name itself communicates a completed fact, not a command to perform an action.
3. **Carries exactly the relevant data** — enough for a listener to react meaningfully, without requiring the listener to call back into the originating aggregate for more context.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An aggregate raises a domain event describing a completed fact; multiple independent listeners react to it without the aggregate knowing who is listening">
  <rect x="30" y="60" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order aggregate</text>

  <rect x="240" y="60" width="150" height="50" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="315" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderPlaced event</text>
  <line x1="170" y1="85" x2="240" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a54)"/>

  <rect x="460" y="20" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">InventoryService</text>
  <rect x="460" y="65" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">NotificationService</text>
  <rect x="460" y="110" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="132" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">AnalyticsService</text>
  <line x1="390" y1="85" x2="460" y2="37" stroke="#8b949e" stroke-width="1"/>
  <line x1="390" y1="85" x2="460" y2="82" stroke="#8b949e" stroke-width="1"/>
  <line x1="390" y1="85" x2="460" y2="127" stroke="#8b949e" stroke-width="1"/>
  <defs><marker id="a54" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The aggregate raises one event; any number of independent listeners can react without the aggregate knowing they exist.

## 5. Runnable example

Scenario: an order aggregate raising a domain event when placed, first with no listeners, then with multiple independent listeners reacting, then extended to a full state-machine of events across an order's lifecycle.

### Level 1 — Basic

```java
// File: BasicDomainEvent.java -- an immutable event, named in past tense,
// carrying exactly the relevant data.
import java.time.Instant;

public class BasicDomainEvent {
    record OrderPlaced(String orderId, double total, Instant occurredAt) { } // IMMUTABLE, past tense, relevant data only

    static class Order {
        String orderId;
        double total;
        Order(String orderId, double total) { this.orderId = orderId; this.total = total; }

        OrderPlaced place() {
            return new OrderPlaced(orderId, total, Instant.EPOCH); // fixed timestamp for reproducible output
        }
    }

    public static void main(String[] args) {
        Order order = new Order("ord-1", 29.98);
        OrderPlaced event = order.place();
        System.out.println("Event raised: " + event.orderId() + " placed, total $" + event.total());
    }
}
```

**How to run:** `javac BasicDomainEvent.java && java BasicDomainEvent` (JDK 17+).

Expected output:
```
Event raised: ord-1 placed, total $29.98
```

`OrderPlaced` is an immutable record capturing exactly what happened — which order, for how much, and when — with no listener yet reacting to it.

### Level 2 — Intermediate

```java
// File: MultipleListeners.java -- SEVERAL independent listeners react
// to the SAME event, none aware of the others.
import java.util.*;
import java.util.function.Consumer;

public class MultipleListeners {
    record OrderPlaced(String orderId, double total) { }

    static class EventBus {
        List<Consumer<OrderPlaced>> listeners = new ArrayList<>();
        void subscribe(Consumer<OrderPlaced> listener) { listeners.add(listener); }
        void publish(OrderPlaced event) { listeners.forEach(l -> l.accept(event)); }
    }

    public static void main(String[] args) {
        EventBus bus = new EventBus();

        bus.subscribe(event -> System.out.println("[Inventory] reserving stock for order " + event.orderId()));
        bus.subscribe(event -> System.out.println("[Notification] sending confirmation for order " + event.orderId()));
        bus.subscribe(event -> System.out.println("[Analytics] recording $" + event.total() + " in sales"));

        bus.publish(new OrderPlaced("ord-1", 29.98)); // the aggregate has NO idea these three listeners exist
    }
}
```

**How to run:** `javac MultipleListeners.java && java MultipleListeners` (JDK 17+).

Expected output:
```
[Inventory] reserving stock for order ord-1
[Notification] sending confirmation for order ord-1
[Analytics] recording $29.98 in sales
```

Three completely independent concerns react to the same `OrderPlaced` event, each doing its own thing — none of them, and critically not the code that published the event either, needed to know about the other two.

### Level 3 — Advanced

```java
// File: OrderLifecycleEvents.java -- a FULL sequence of domain events
// across an order's lifecycle, each triggering its own independent reaction.
import java.util.*;
import java.util.function.Consumer;

public class OrderLifecycleEvents {
    sealed interface OrderEvent permits OrderPlaced, OrderShipped, OrderCancelled { }
    record OrderPlaced(String orderId, double total) implements OrderEvent { }
    record OrderShipped(String orderId, String trackingNumber) implements OrderEvent { }
    record OrderCancelled(String orderId, String reason) implements OrderEvent { }

    static class EventBus {
        List<Consumer<OrderEvent>> listeners = new ArrayList<>();
        void subscribe(Consumer<OrderEvent> listener) { listeners.add(listener); }
        void publish(OrderEvent event) { listeners.forEach(l -> l.accept(event)); }
    }

    static void handleEvent(OrderEvent event) {
        // a listener that reacts DIFFERENTLY depending on which specific event occurred
        String message = switch (event) {
            case OrderPlaced e -> "[Notification] order " + e.orderId() + " placed, $" + e.total();
            case OrderShipped e -> "[Notification] order " + e.orderId() + " shipped, tracking: " + e.trackingNumber();
            case OrderCancelled e -> "[Notification] order " + e.orderId() + " cancelled: " + e.reason();
        };
        System.out.println(message);
    }

    public static void main(String[] args) {
        EventBus bus = new EventBus();
        bus.subscribe(OrderLifecycleEvents::handleEvent);

        bus.publish(new OrderPlaced("ord-1", 29.98));
        bus.publish(new OrderShipped("ord-1", "TRACK123"));
        bus.publish(new OrderCancelled("ord-2", "customer requested"));
    }
}
```

**How to run:** `javac OrderLifecycleEvents.java && java OrderLifecycleEvents` (JDK 17+).

Expected output:
```
[Notification] order ord-1 placed, $29.98
[Notification] order ord-1 shipped, tracking: TRACK123
[Notification] order ord-2 cancelled: customer requested
```

The production-flavored case: three distinct event types, modeled as a `sealed interface` so the compiler enforces that every possible event type is handled in `handleEvent`'s `switch`. Each event carries exactly the data relevant to that specific fact — `OrderShipped` carries a tracking number, `OrderCancelled` carries a reason — and one listener correctly formats a different message for each, all driven purely by which concrete event type it received.

## 6. Walkthrough

1. `bus.publish(new OrderPlaced("ord-1", 29.98))` calls `listeners.forEach(l -> l.accept(event))`, invoking `handleEvent` with an `OrderPlaced` instance. Inside `handleEvent`, the `switch` expression matches `case OrderPlaced e`, formatting and printing the placement message.
2. `bus.publish(new OrderShipped("ord-1", "TRACK123"))` runs next, invoking `handleEvent` again — this time the `switch` matches `case OrderShipped e`, reading `e.trackingNumber()` (a field `OrderPlaced` doesn't even have) and printing the shipping message.
3. `bus.publish(new OrderCancelled("ord-2", "customer requested"))` runs last, matching `case OrderCancelled e`, reading `e.reason()` and printing the cancellation message.
4. Each event carries only the data relevant to its own specific fact — `handleEvent` never needs to call back into any `Order` object to get more context, because the event itself already contains everything needed to react meaningfully.
5. Because `OrderEvent` is a `sealed interface` permitting exactly these three record types, the Java compiler would refuse to compile `handleEvent`'s `switch` if a new event type were added to the `permits` clause without a corresponding `case` being added — a concrete, compiler-enforced guarantee that no domain event type is ever silently left unhandled.

```
publish(OrderPlaced)    -> switch matches OrderPlaced    -> "order placed, $29.98"
publish(OrderShipped)   -> switch matches OrderShipped   -> "order shipped, tracking: TRACK123"
publish(OrderCancelled) -> switch matches OrderCancelled -> "order cancelled: customer requested"
```

## 7. Gotchas & takeaways

> **Gotcha:** domain events should describe *what happened*, not *what to do next* — `OrderPlaced` is a domain event; `SendConfirmationEmail` is a command, a fundamentally different concept (an instruction, not a fact). Naming an event as a command disguises the actual dependency direction: a command implies the sender knows and cares who receives it and what they'll do, while a genuine event leaves that entirely up to independent listeners, exactly the decoupling domain events are meant to provide.

- A domain event is an immutable record of a meaningful business fact, named in past tense using the domain's own ubiquitous language, carrying exactly the data a listener needs to react without calling back for more context.
- Domain events let an aggregate announce what happened without knowing or caring who, if anyone, is listening — the concrete mechanism behind eventual consistency and the self-contained service pattern.
- Model a full set of related events (like an order's lifecycle) as a sealed type hierarchy where practical, so the compiler can enforce that every listener handles every possible event type.
- Reserve domain events for facts genuinely significant to the business — not every trivial internal state change deserves to become an event that other parts of the system must consider reacting to.
