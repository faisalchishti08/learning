---
card: system-design
gi: 200
slug: event-driven-architecture
title: Event-driven architecture
---

## 1. What it is

**Event-driven architecture (EDA)** structures a system around **events** — facts that something happened, like `OrderPlaced` or `PaymentFailed` — published to a broker (a message queue or event stream). Services **publish** events when something happens in their domain, and other services **subscribe** to the events they care about, reacting independently and asynchronously.

## 2. Why & when

When one service calls another directly (a synchronous HTTP call), the caller is coupled to the callee's availability — if the payments service is down, the order service's call fails right there. Event-driven architecture removes that coupling: the order service publishes `OrderPlaced` and moves on, without knowing or caring which services will react to it, or whether they are online right now.

This buys **loose coupling** (new subscribers can be added without changing the publisher) and **resilience** (a subscriber being down does not block the publisher), at the cost of **eventual consistency** (subscribers process the event some time after it happened, not instantly) and harder debugging (a single business flow is now scattered across independent reactions instead of one linear call stack). Use EDA when multiple independent parts of the system need to react to the same fact, or when producer and consumer should not be coupled to each other's uptime. Avoid it when a caller genuinely needs an immediate answer before it can proceed — that is a synchronous call, not an event.

## 3. Core concept

- **Event = a fact, already happened, past tense.** `OrderPlaced`, not `PlaceOrder`. The publisher does not ask the subscriber to do anything — it announces what already happened, and subscribers decide what to do about it.
- **Publisher/subscriber decoupling.** The publisher does not know who is subscribed, how many subscribers there are, or whether they succeeded. This is the core difference from a direct service call, where the caller knows exactly who it is calling and waits for a result.
- **The broker.** A message queue or event stream (Kafka, RabbitMQ, SQS/SNS) sits between publishers and subscribers, storing events until subscribers consume them, and often allowing multiple subscribers to each get their own copy of every event.
- **At-least-once delivery.** Most brokers guarantee an event is delivered at least once, but can redeliver the same event after a subscriber failure — so subscribers must be **idempotent** (processing the same event twice must not double the effect).
- **Eventual consistency.** Because subscribers react asynchronously, there is a window after an event is published where not every part of the system has processed it yet. This is an accepted tradeoff for the decoupling, not a bug.

## 4. Diagram

```
   OrderService                    Event Broker                Subscribers
   (publisher)                    (e.g. Kafka topic:
                                    "order-events")
       |                                 |
       |-- publish OrderPlaced --------->|
       |   (fire and forget)             |
       |                                 |----> InventoryService  (reserve stock)
       |                                 |----> EmailService      (send confirmation)
       |                                 |----> AnalyticsService  (record metric)
       |
       v
   returns 201 to the client
   immediately - does NOT wait
   for any subscriber to react
```
*Caption: `OrderService` publishes once and returns immediately. Every subscriber reacts on its own schedule — adding a new subscriber never requires changing `OrderService`.*

## 5. Runnable example

**Level 1 — Basic.** An in-memory event bus: publish an event, deliver it to every subscribed handler.

**Level 2 — Intermediate.** Add multiple independent subscribers reacting to the same event, and show the publisher never waits for them or knows about their existence.

**Level 3 — Advanced.** Model at-least-once delivery with a failing subscriber and a redelivery retry, and make the subscriber idempotent so redelivery does not double-process.

```java
// EventDrivenDemo.java
import java.util.*;
import java.util.function.*;

public class EventDrivenDemo {

    record OrderPlacedEvent(String eventId, String orderId, double amount) {}

    // ---------- Level 1: minimal in-memory event bus ----------
    static class EventBus {
        Map<Class<?>, List<Consumer<Object>>> subscribers = new HashMap<>();

        <T> void subscribe(Class<T> eventType, Consumer<T> handler) {
            subscribers.computeIfAbsent(eventType, k -> new ArrayList<>())
                       .add((Consumer<Object>) handler);
        }

        void publish(Object event) {
            List<Consumer<Object>> handlers = subscribers.getOrDefault(event.getClass(), List.of());
            System.out.println("  [bus] publishing " + event + " to " + handlers.size() + " subscriber(s)");
            for (Consumer<Object> handler : handlers) {
                handler.accept(event); // fire and forget from the publisher's point of view
            }
        }
    }

    // ---------- Level 2: several independent subscribers ----------
    static void inventoryHandler(OrderPlacedEvent e) {
        System.out.println("    [InventoryService] reserved stock for order " + e.orderId());
    }
    static void emailHandler(OrderPlacedEvent e) {
        System.out.println("    [EmailService] sent confirmation for order " + e.orderId());
    }
    static void analyticsHandler(OrderPlacedEvent e) {
        System.out.println("    [AnalyticsService] recorded $" + e.amount() + " for order " + e.orderId());
    }

    // ---------- Level 3: at-least-once delivery + idempotent subscriber ----------
    static class FlakyBrokerWithRetry {
        Random rnd = new Random(3);
        Set<String> processedEventIds = new HashSet<>(); // idempotency tracking on the subscriber side

        void deliverWithRetry(OrderPlacedEvent event, Consumer<OrderPlacedEvent> handler, int maxAttempts) {
            for (int attempt = 1; attempt <= maxAttempts; attempt++) {
                System.out.println("    delivery attempt " + attempt + " for event " + event.eventId());
                boolean deliveryFailed = rnd.nextBoolean() && attempt < maxAttempts; // simulate failure, then eventual success
                if (deliveryFailed) {
                    System.out.println("      delivery failed (broker will redeliver)");
                    continue;
                }
                // Idempotent handler: skip if this event ID was already processed.
                if (processedEventIds.contains(event.eventId())) {
                    System.out.println("      already processed " + event.eventId() + " - skipping (idempotent)");
                    return;
                }
                handler.accept(event);
                processedEventIds.add(event.eventId());
                return;
            }
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - basic publish/subscribe:");
        EventBus bus = new EventBus();
        bus.subscribe(OrderPlacedEvent.class, e -> System.out.println("    handled: " + e));
        bus.publish(new OrderPlacedEvent("evt-1", "ORD-1", 25.00));

        System.out.println("\nLevel 2 - multiple independent subscribers, publisher unaware of them:");
        EventBus bus2 = new EventBus();
        bus2.subscribe(OrderPlacedEvent.class, EventDrivenDemo::inventoryHandler);
        bus2.subscribe(OrderPlacedEvent.class, EventDrivenDemo::emailHandler);
        bus2.subscribe(OrderPlacedEvent.class, EventDrivenDemo::analyticsHandler);
        bus2.publish(new OrderPlacedEvent("evt-2", "ORD-2", 99.50));

        System.out.println("\nLevel 3 - at-least-once delivery with retry + idempotent handler:");
        FlakyBrokerWithRetry broker = new FlakyBrokerWithRetry();
        OrderPlacedEvent event = new OrderPlacedEvent("evt-3", "ORD-3", 15.00);
        Consumer<OrderPlacedEvent> countingHandler = e ->
            System.out.println("      [InventoryService] reserved stock for " + e.orderId() + " (processed once)");
        broker.deliverWithRetry(event, countingHandler, 4);
        System.out.println("  simulating an accidental broker redelivery of the SAME event:");
        broker.deliverWithRetry(event, countingHandler, 1); // redelivery of the same eventId
    }
}
```

**How to run:** `java EventDrivenDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `bus.subscribe(...)` registers one handler for `OrderPlacedEvent`. `bus.publish(...)` looks up all handlers for that event's class and calls each one directly — this is a simplified in-process stand-in for a real broker's delivery.
2. **Level 2:** three independent handlers — `inventoryHandler`, `emailHandler`, `analyticsHandler` — are all subscribed to the same `OrderPlacedEvent` class. A single `bus2.publish(...)` call delivers the event to all three, in the order they were subscribed. Notice `OrderPlacedEvent` itself contains no reference to any of these services — the publisher's code would be unchanged if you added a fourth subscriber tomorrow.
3. **Level 3:** `deliverWithRetry` simulates a broker that sometimes fails to deliver on the first attempt (`rnd.nextBoolean()`) and retries up to `maxAttempts` times — this is what "at-least-once delivery" means in practice: the broker keeps trying until it succeeds or gives up.
4. Once delivery succeeds, the handler checks `processedEventIds.contains(event.eventId())` before doing real work. The **first** call to `deliverWithRetry` for `evt-3` processes normally and adds `"evt-3"` to `processedEventIds`.
5. The **second** call simulates the broker redelivering the exact same event (a common real failure mode: the subscriber processed the event but crashed before acknowledging it, so the broker assumes it failed and resends). Because `processedEventIds` already contains `"evt-3"`, the handler prints `"already processed... skipping"` instead of reserving stock a second time — this idempotency check is what makes at-least-once delivery safe to build on.

## 7. Gotchas & takeaways

> **Gotcha:** "at-least-once" delivery means subscribers WILL occasionally see the same event twice. A subscriber that is not idempotent (e.g. one that just increments a counter on every delivery, with no de-duplication) will silently produce wrong results under normal broker behavior, not just during rare failures.

- Name events in the past tense and keep them free of instructions — `OrderPlaced`, never `PlaceOrder`. An event describes a fact, not a command.
- Design every subscriber to be idempotent by default; assume redelivery will happen eventually, because it will.
- Eventual consistency is a real, visible tradeoff — a user might see their order before `InventoryService` has finished reserving stock. Decide up front which parts of the system can tolerate that delay and which cannot.
- Pair this with the [transactional outbox](0204-transactional-outbox.md) pattern when a service must both update its own database and publish an event, so the two never disagree if one operation succeeds and the other fails.
