---
card: spring-cloud
gi: 79
slug: event-driven-microservices-concept
title: "Event-driven microservices concept"
---

## 1. What it is

Event-driven microservices communicate by publishing and reacting to *events* — immutable facts about something that already happened ("OrderPlaced", "InvoiceGenerated") — through a shared message broker, instead of one service directly calling another's HTTP API and waiting for a response. Spring Cloud Stream is the abstraction covered through this whole section for building services that speak this way, on top of a real broker like Kafka or RabbitMQ.

```java
@Bean
Function<OrderPlaced, InvoiceRequested> handleOrder() {
    return orderPlaced -> new InvoiceRequested(orderPlaced.orderId(), orderPlaced.amount());
    // consumes an event, publishes a new one -- no direct call to billing-service at all
}
```

## 2. Why & when

Every request-response pattern covered so far in this card (Feign, `@LoadBalanced` clients, Gateway routing) assumes the caller needs an immediate answer and both services must be simultaneously available. Event-driven communication decouples that: a publisher fires an event and moves on without waiting; any number of subscribers react whenever they're ready, entirely independently of the publisher's lifecycle, and independently of each other.

Reach for event-driven communication when:

- The publishing service genuinely doesn't need an immediate response — "an order was placed" is a fact billing, inventory, and notifications all care about, but none of them need to answer synchronously before the order-placing request itself completes.
- New subscribers should be addable later without changing the publisher at all — a new "loyalty-points-service" can start consuming "OrderPlaced" events without `orders-service` ever being modified or even aware it exists.
- Resilience matters more than immediacy — if `billing-service` is briefly down, an `OrderPlaced` event sitting in a queue simply waits for it to come back, rather than the whole order-placement request failing outright (the way a synchronous Feign call to a down `billing-service` would).

## 3. Core concept

```
 request-response (Feign, RestTemplate, Gateway routing -- earlier cards):
   caller ---request---> service ---response---> caller (BLOCKS until it responds)
   caller must know WHO to call; both sides must be up simultaneously

 event-driven (this section):
   publisher ---publishes event---> BROKER ---delivers to---> subscriber A
                                              ---delivers to---> subscriber B
                                              ---delivers to---> subscriber C (added later, publisher unaware)
   publisher doesn't wait, doesn't know who's subscribed, doesn't need them to be up right now
```

Request-response couples caller and callee in time and identity; event-driven communication decouples both.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An orders service publishes an OrderPlaced event to a broker without waiting, and three independent subscribers each react to it whenever they are ready, with none of them known to the publisher">
  <rect x="30" y="80" width="140" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="100" y="105" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">orders-service</text>

  <line x1="170" y1="100" x2="240" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a79)"/>
  <text x="205" y="90" fill="#6db33f" font-size="6.5" text-anchor="middle" font-family="sans-serif">publish, don't wait</text>

  <rect x="245" y="75" width="150" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">broker</text>
  <text x="320" y="113" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">OrderPlaced event</text>

  <rect x="460" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="535" y="41" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billing-service</text>
  <rect x="460" y="83" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="535" y="104" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">inventory-service</text>
  <rect x="460" y="146" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="535" y="167" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">loyalty-service (added later)</text>

  <line x1="395" y1="90" x2="458" y2="40" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a79)"/>
  <line x1="395" y1="100" x2="458" y2="100" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a79)"/>
  <line x1="395" y1="110" x2="458" y2="160" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a79)"/>

  <defs><marker id="a79" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The publisher fires one event into the broker and moves on; every subscriber, present or future, reacts independently.

## 5. Runnable example

The scenario: model `orders-service` publishing an `OrderPlaced` event consumed by multiple independent subscribers. Start with the request-response alternative (tight coupling), then add an event broker decoupling publisher from subscribers, then add a new subscriber without touching the publisher at all.

### Level 1 — Basic

Request-response: the publisher must know and directly call every interested party.

```java
import java.util.*;

public class EventDrivenLevel1 {
    record OrderPlaced(String orderId, double amount) {}

    // orders-service must know about EVERY interested service, and call each one directly
    static void notifyBilling(OrderPlaced event) { System.out.println("billing-service notified directly: " + event); }
    static void notifyInventory(OrderPlaced event) { System.out.println("inventory-service notified directly: " + event); }

    static void placeOrder(String orderId, double amount) {
        OrderPlaced event = new OrderPlaced(orderId, amount);
        notifyBilling(event);   // orders-service is tightly coupled to billing-service's existence
        notifyInventory(event); // AND to inventory-service's existence
        // adding a third interested service means MODIFYING placeOrder itself
    }

    public static void main(String[] args) {
        placeOrder("42", 199.99);
    }
}
```

How to run: `java EventDrivenLevel1.java`

`placeOrder` must explicitly know about and call every interested service — `orders-service`'s code is directly coupled to the existence and availability of both `billing-service` and `inventory-service`, and adding a third consumer requires modifying `placeOrder` itself.

### Level 2 — Intermediate

Add a broker abstraction: the publisher fires an event into a shared channel, and subscribers register independently, with the publisher having no direct knowledge of who's listening.

```java
import java.util.*;
import java.util.function.Consumer;

public class EventDrivenLevel2 {
    record OrderPlaced(String orderId, double amount) {}

    static class Broker {
        Map<String, List<Consumer<OrderPlaced>>> subscribers = new HashMap<>();

        void subscribe(String topic, Consumer<OrderPlaced> subscriber) {
            subscribers.computeIfAbsent(topic, k -> new ArrayList<>()).add(subscriber);
        }

        void publish(String topic, OrderPlaced event) {
            for (Consumer<OrderPlaced> subscriber : subscribers.getOrDefault(topic, List.of())) {
                subscriber.accept(event); // each subscriber reacts independently
            }
        }
    }

    static void placeOrder(Broker broker, String orderId, double amount) {
        OrderPlaced event = new OrderPlaced(orderId, amount);
        broker.publish("order-placed", event); // orders-service knows NOTHING about who's subscribed
    }

    public static void main(String[] args) {
        Broker broker = new Broker();
        broker.subscribe("order-placed", event -> System.out.println("billing-service reacted: " + event));
        broker.subscribe("order-placed", event -> System.out.println("inventory-service reacted: " + event));

        placeOrder(broker, "42", 199.99);
    }
}
```

How to run: `java EventDrivenLevel2.java`

`placeOrder` calls `broker.publish("order-placed", event)` and nothing else — it has no reference to `billing-service` or `inventory-service` at all, only to the abstract concept of an "order-placed" topic. Both subscribers registered themselves independently ahead of time and react automatically when the event arrives, with the publisher completely unaware of how many subscribers exist or what they do.

### Level 3 — Advanced

Add a new subscriber (`loyalty-service`) without touching `placeOrder` at all, demonstrating the real payoff: extensibility without publisher modification, plus a subscriber that fails gracefully without affecting the others.

```java
import java.util.*;
import java.util.function.Consumer;

public class EventDrivenLevel3 {
    record OrderPlaced(String orderId, double amount) {}

    static class Broker {
        Map<String, List<Consumer<OrderPlaced>>> subscribers = new HashMap<>();

        void subscribe(String topic, Consumer<OrderPlaced> subscriber) {
            subscribers.computeIfAbsent(topic, k -> new ArrayList<>()).add(subscriber);
        }

        void publish(String topic, OrderPlaced event) {
            for (Consumer<OrderPlaced> subscriber : subscribers.getOrDefault(topic, List.of())) {
                try {
                    subscriber.accept(event);
                } catch (RuntimeException e) {
                    // one subscriber's failure doesn't stop delivery to the others
                    System.out.println("a subscriber failed (" + e.getMessage() + "), other subscribers still notified");
                }
            }
        }
    }

    // this function is UNCHANGED from Level 2 -- adding a new subscriber never touches it
    static void placeOrder(Broker broker, String orderId, double amount) {
        broker.publish("order-placed", new OrderPlaced(orderId, amount));
    }

    public static void main(String[] args) {
        Broker broker = new Broker();
        broker.subscribe("order-placed", event -> System.out.println("billing-service reacted: " + event));
        broker.subscribe("order-placed", event -> { throw new RuntimeException("inventory-service is temporarily down"); });
        broker.subscribe("order-placed", event -> System.out.println("loyalty-service (added later) reacted: " + event));

        placeOrder(broker, "42", 199.99); // placeOrder itself never changed to accommodate the new subscriber
    }
}
```

How to run: `java EventDrivenLevel3.java`

`placeOrder`'s source code is byte-for-byte identical to Level 2 — `loyalty-service`'s subscription was added purely by calling `broker.subscribe(...)` from outside, with zero modification to the publishing code. The `inventory-service` subscriber deliberately throws, modeling a genuinely down or misbehaving subscriber, and the broker's `try/catch` ensures that failure doesn't prevent `loyalty-service` (registered after it) from still receiving and correctly processing the same event.

## 6. Walkthrough

Trace `placeOrder`'s call in Level 3.

1. `placeOrder(broker, "42", 199.99)` runs — it constructs `OrderPlaced("42", 199.99)` and calls `broker.publish("order-placed", event)`. This is the entire extent of the publisher's involvement; it has no awareness of any subscriber's identity, count, or behavior.
2. Inside `publish`, the loop iterates `subscribers.getOrDefault("order-placed", List.of())`, which contains three registered consumers, in the order they were subscribed: `billing-service`'s handler, `inventory-service`'s (failing) handler, and `loyalty-service`'s handler.
3. The first iteration calls `billing-service`'s consumer, which prints its reaction message successfully and returns normally.
4. The second iteration calls `inventory-service`'s consumer, which throws a `RuntimeException`. The `try/catch` inside `publish` catches it, prints a message noting the failure without crashing the whole publish operation, and the loop continues to the next subscriber rather than aborting.
5. The third iteration calls `loyalty-service`'s consumer, which prints its own reaction message successfully — completely unaffected by `inventory-service`'s failure two steps earlier, since each subscriber's invocation is isolated by the `try/catch` inside the loop.
6. The net effect: two of three subscribers successfully processed the event, one failed gracefully without disrupting the others, and `placeOrder` itself never had to change, be aware of, or handle any of this — exactly the decoupling event-driven communication is designed to provide.

```
publish("order-placed", event)
    subscriber 1 (billing)   -> succeeds
    subscriber 2 (inventory) -> throws -> caught, logged, loop continues
    subscriber 3 (loyalty)   -> succeeds, unaffected by subscriber 2's failure
```

## 7. Gotchas & takeaways

> **Gotcha:** decoupling comes at the cost of losing an immediate, synchronous confirmation that an interested party actually processed the event successfully — in Level 1's request-response model, a failed `notifyBilling` call would be immediately visible to `placeOrder`'s caller; in the event-driven model, `inventory-service`'s failure in Level 3 was silently absorbed and logged, but `placeOrder`'s original caller has no idea it happened at all. Event-driven systems need their own observability (dead-letter queues, monitoring, alerting — covered in a later card) to catch failures that request-response would have surfaced immediately and synchronously.

- Event-driven communication decouples publisher from subscriber in both time (publisher doesn't wait) and identity (publisher doesn't know who's listening), in direct contrast to every request-response pattern covered earlier in this card.
- New subscribers can be added purely by registering themselves with the broker, with zero modification to the publishing code — a real, structural extensibility advantage over request-response's tightly coupled call sites.
- One subscriber's failure shouldn't cascade to prevent other subscribers from receiving the same event — this isolation needs to be deliberately built into the broker/dispatch mechanism, as Resilience4j's various patterns from the previous section are built to provide for other kinds of calls.
- The tradeoff is real: event-driven systems trade immediate, synchronous confirmation for looser coupling and better resilience to individual subscriber outages — appropriate for facts that don't need an immediate reply, not a universal replacement for request-response everywhere.
