---
card: microservices
gi: 114
slug: publish-subscribe-topic-messaging
title: "Publish/subscribe (topic) messaging"
---

## 1. What it is

Publish/subscribe (pub/sub) messaging is a delivery model where a producer publishes a message to a topic, and *every* subscriber currently listening to that topic receives its own independent copy — unlike [point-to-point queue messaging](0113-point-to-point-queue-messaging.md), where only one consumer gets each message.

## 2. Why & when

Many real events matter to more than one part of a system for different reasons: an `OrderPlaced` event might need to trigger an email confirmation, update a sales dashboard, and adjust inventory, all independently and without any of those three services knowing about the others. Pub/sub is built for exactly this — the producer publishes one event to one topic, entirely unaware of who (if anyone) is subscribed, and each interested service subscribes on its own to get its own copy.

Use pub/sub when an occurrence is broadcast-worthy — multiple independent, decoupled consumers each need to react to the *same* event in their *own* way. Use point-to-point instead when a single unit of work should be done exactly once by whichever available worker picks it up.

## 3. Core concept

A topic is a named broadcast channel. Publishing to it does not target any specific consumer; instead, the broker fans the message out to every current subscription, and each subscriber processes the message independently of what any other subscriber does with its own copy.

```java
topic.publish("order-events", orderPlacedJson);

// three independent subscribers, each gets its OWN copy of the SAME message
emailSubscription.onMessage(msg -> sendConfirmation(msg));
analyticsSubscription.onMessage(msg -> recordSale(msg));
inventorySubscription.onMessage(msg -> decrementStock(msg));
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A producer publishes one message to a topic; three independent subscribers each receive their own copy of that same message">
  <rect x="20" y="90" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="115" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order Service</text>

  <rect x="230" y="80" width="140" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Topic:</text>
  <text x="300" y="128" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-events</text>

  <rect x="480" y="20" width="140" height="36" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="43" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Email Subscriber</text>
  <rect x="480" y="92" width="140" height="36" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="115" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Analytics Subscriber</text>
  <rect x="480" y="164" width="140" height="36" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="187" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Inventory Subscriber</text>

  <line x1="150" y1="110" x2="228" y2="110" stroke="#8b949e" marker-end="url(#arr4)"/>
  <line x1="370" y1="95" x2="478" y2="40" stroke="#8b949e" marker-end="url(#arr4)"/>
  <line x1="370" y1="110" x2="478" y2="110" stroke="#8b949e" marker-end="url(#arr4)"/>
  <line x1="370" y1="125" x2="478" y2="180" stroke="#8b949e" marker-end="url(#arr4)"/>

  <defs>
    <marker id="arr4" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

One publish fans out to every subscriber; each gets a full, independent copy of the message, not a share of it.

## 5. Runnable example

Scenario: an `OrderPlaced` event broadcast that starts with a single subscriber (indistinguishable from point-to-point), grows to three independent subscribers each doing something different with the same event, and finally adds a late-joining subscriber to show that pub/sub delivery is normally tied to being subscribed *at publish time*, not retroactive.

### Level 1 — Basic

```java
// File: SingleSubscriberTopic.java -- one subscriber; looks like point-to-point so far.
import java.util.*;
import java.util.function.*;

public class SingleSubscriberTopic {
    static class Topic {
        private final List<Consumer<String>> subscribers = new ArrayList<>();
        void subscribe(Consumer<String> handler) { subscribers.add(handler); }
        void publish(String message) { subscribers.forEach(s -> s.accept(message)); } // fan-out, even with 1 subscriber
    }

    public static void main(String[] args) {
        Topic orderEvents = new Topic();
        orderEvents.subscribe(msg -> System.out.println("[email] confirming: " + msg));
        orderEvents.publish("OrderPlaced:42");
    }
}
```

**How to run:** `javac SingleSubscriberTopic.java && java SingleSubscriberTopic` (JDK 17+).

With one subscriber the fan-out mechanism is present but not yet visibly different from a plain queue delivering to a single consumer.

### Level 2 — Intermediate

```java
// File: MultiSubscriberTopic.java -- three independent subscribers, each getting the SAME event.
import java.util.*;
import java.util.function.*;

public class MultiSubscriberTopic {
    static class Topic {
        private final List<Consumer<String>> subscribers = new ArrayList<>();
        void subscribe(Consumer<String> handler) { subscribers.add(handler); }
        void publish(String message) {
            System.out.println("Publishing to " + subscribers.size() + " subscriber(s): " + message);
            for (Consumer<String> s : subscribers) s.accept(message); // EVERY subscriber gets its OWN call
        }
    }

    public static void main(String[] args) {
        Topic orderEvents = new Topic();
        orderEvents.subscribe(msg -> System.out.println("  [email] sending confirmation for " + msg));
        orderEvents.subscribe(msg -> System.out.println("  [analytics] recording sale for " + msg));
        orderEvents.subscribe(msg -> System.out.println("  [inventory] decrementing stock for " + msg));

        orderEvents.publish("OrderPlaced:42"); // ONE publish call...
    }
}
```

**How to run:** `javac MultiSubscriberTopic.java && java MultiSubscriberTopic` (JDK 17+).

Expected output:
```
Publishing to 3 subscriber(s): OrderPlaced:42
  [email] sending confirmation for OrderPlaced:42
  [analytics] recording sale for OrderPlaced:42
  [inventory] decrementing stock for OrderPlaced:42
```

...produces three independent reactions, each subscriber fully unaware of the other two.

### Level 3 — Advanced

```java
// File: LateSubscriberTopic.java -- shows that a subscriber joining AFTER a publish
// misses that message, the key contrast with a durable point-to-point queue.
import java.util.*;
import java.util.function.*;

public class LateSubscriberTopic {
    static class Topic {
        private final List<Consumer<String>> subscribers = new ArrayList<>();
        private int messagesPublished = 0;
        void subscribe(String name, Consumer<String> handler) {
            subscribers.add(handler);
            System.out.println(name + " subscribed after " + messagesPublished + " message(s) already published");
        }
        void publish(String message) {
            messagesPublished++;
            for (Consumer<String> s : subscribers) s.accept(message);
        }
    }

    public static void main(String[] args) {
        Topic orderEvents = new Topic();
        orderEvents.subscribe("email-service", msg -> System.out.println("  [email] confirming " + msg));
        orderEvents.subscribe("analytics-service", msg -> System.out.println("  [analytics] recording " + msg));

        orderEvents.publish("OrderPlaced:42"); // both current subscribers get this

        // a NEW service joins the system after the fact -- e.g. a fraud-detection service added later
        orderEvents.subscribe("fraud-service", msg -> System.out.println("  [fraud] screening " + msg));

        orderEvents.publish("OrderPlaced:43"); // now ALL THREE get this one, including the late joiner

        System.out.println("Note: fraud-service never saw OrderPlaced:42 -- it wasn't subscribed yet.");
    }
}
```

**How to run:** `javac LateSubscriberTopic.java && java LateSubscriberTopic` (JDK 17+).

Expected output:
```
email-service subscribed after 0 message(s) already published
analytics-service subscribed after 0 message(s) already published
  [email] confirming OrderPlaced:42
  [analytics] recording OrderPlaced:42
fraud-service subscribed after 1 message(s) already published
  [email] confirming OrderPlaced:43
  [analytics] recording OrderPlaced:43
  [fraud] screening OrderPlaced:43
Note: fraud-service never saw OrderPlaced:42 -- it wasn't subscribed yet.
```

## 6. Walkthrough

1. **Level 1** — `Topic.publish` loops over `subscribers` and calls each handler; with one subscriber registered, this behaves like a simple direct call, but the fan-out loop is already the mechanism that will matter once more subscribers exist.
2. **Level 2, three independent registrations** — `main` calls `subscribe` three times with three unrelated lambda handlers, each representing a different downstream service reacting to the same kind of event for its own purpose.
3. **Level 2, the single publish** — `orderEvents.publish("OrderPlaced:42")` is called exactly once, but because `publish` iterates every entry in `subscribers`, all three handlers run, each receiving the identical message string, each completely unaware the other two ran.
4. **Level 3, subscribing before the first publish** — `email-service` and `analytics-service` subscribe while `messagesPublished` is still 0, so both are present in the `subscribers` list before the first `publish("OrderPlaced:42")` call, and both receive it.
5. **Level 3, subscribing after a publish** — `fraud-service` calls `subscribe` only *after* the first `publish` has already run; because the `Topic` implementation here (like most pub/sub systems by default) does not retroactively deliver past messages to new subscribers, `fraud-service` is added to the list too late to have received `OrderPlaced:42`.
6. **Level 3, the second publish** — `publish("OrderPlaced:43")` now iterates a `subscribers` list containing all three handlers, so this time every one of them, including the late joiner, receives the message.
7. **What the final printed note demonstrates** — pub/sub delivery is tied to subscription state *at the moment of publish*; a subscriber that joins late genuinely misses earlier messages unless the broker specifically offers a durable/replayable subscription mechanism (as Kafka does with consumer offsets, and as durable topic subscriptions do in JMS-style brokers) — that replay capability is a broker feature layered on top of the basic pub/sub model, not something the basic model guarantees for free.

## 7. Gotchas & takeaways

> **Gotcha:** "every subscriber gets every message" is only true for subscribers that exist *at publish time* with a non-durable subscription — a service that is down when a message is published, or that subscribes after the fact, will simply miss it unless the broker specifically supports durable subscriptions or message replay (e.g., Kafka consumer groups reading from a stored offset).

- Publish/subscribe delivers an independent copy of each message to every current subscriber of a topic, in contrast to [point-to-point](0113-point-to-point-queue-messaging.md)'s exactly-one-consumer delivery.
- It is the right model when multiple decoupled services each need to react to the same occurrence in their own, independent way.
- The producer publishing to a topic has no knowledge of, or dependency on, how many subscribers exist or what they do with the message.
- Whether a late-joining subscriber can retroactively receive earlier messages depends entirely on the specific broker's replay/durability features, not on the pub/sub model itself.
- Choosing pub/sub vs. point-to-point is a question of "should this event be seen by many independent consumers, or claimed by exactly one worker" — get that choice wrong and you either duplicate work or silently drop interested consumers.
