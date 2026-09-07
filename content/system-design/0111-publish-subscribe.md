---
card: system-design
gi: 111
slug: publish-subscribe
title: Publish/subscribe
---

## 1. What it is

**Publish/subscribe** (pub/sub) delivers each message to **every** subscriber listening on a topic, unlike a [point-to-point queue](0110-message-queues-point-to-point.md), which delivers each message to only one consumer. A publisher sends a message to a named topic without knowing who, if anyone, is listening; every current subscriber to that topic receives its own independent copy. It is like a radio broadcast: everyone with a radio tuned to the station hears the same announcement.

## 2. Why & when

Use pub/sub when one event genuinely needs to trigger independent reactions in multiple, unrelated parts of a system — for example, an "OrderPlaced" event that the shipping service, the analytics service, and the email service all need to react to, each in its own way. Pub/sub lets you add a new subscriber later (a new service that also cares about "OrderPlaced") without changing the publisher at all. Avoid it for the strict "exactly one worker handles this job" case, where a point-to-point queue's competing-consumers model fits better.

## 3. Core concept

- **Topic:** a named channel that a publisher sends messages to and subscribers register interest in.
- **Fan-out:** the messaging system delivers a separate copy of each message to every subscriber currently subscribed to that topic — one message in, many messages out.
- **Decoupled publisher:** the publisher does not know how many subscribers exist, or what any of them do with the message; it just publishes to the topic.
- **Independent subscriber state:** each subscriber tracks its own progress through the topic's messages, so a slow or failed subscriber does not affect any other subscriber's delivery.
- **New subscribers, no publisher change:** adding a fourth service that also needs to react to "OrderPlaced" means only adding a new subscription — the publisher's code is untouched.

## 4. Diagram

```
                     Publisher publishes "OrderPlaced" to topic "orders"
                                     |
                     +---------------+---------------+
                     v               v                v
             Shipping Service   Analytics Service   Email Service
             (own copy)          (own copy)          (own copy)
             starts packing      logs the event       sends confirmation

  Each subscriber gets its OWN full copy of the message,
  and processes it independently of the others.
```
*Caption: one published message fans out to every current subscriber, each receiving its own independent copy.*

## 5. Runnable example

**Level 1 — Basic.** A publisher sends one message to a topic with two subscribers; both receive it.

**Level 2 — Independent subscriber state.** Each subscriber tracks its own count of received messages, unaffected by the others.

**Level 3 — Adding a subscriber later.** A third subscriber joins after some messages were published; it only sees messages published after it joined.

```java
// PublishSubscribe.java
import java.util.*;
import java.util.function.*;

public class PublishSubscribe {

    static Map<String, List<Consumer<String>>> subscribersByTopic = new HashMap<>();

    static void subscribe(String topic, Consumer<String> subscriber) {
        subscribersByTopic.computeIfAbsent(topic, t -> new ArrayList<>()).add(subscriber);
    }

    static void publish(String topic, String message) {
        for (Consumer<String> subscriber : subscribersByTopic.getOrDefault(topic, List.of())) {
            subscriber.accept(message); // each subscriber gets its own call, its own copy
        }
    }

    public static void main(String[] args) {
        // Level 1 & 2: two subscribers, each tracking its own received messages independently.
        List<String> shippingReceived = new ArrayList<>();
        List<String> analyticsReceived = new ArrayList<>();

        subscribe("orders", shippingReceived::add);
        subscribe("orders", analyticsReceived::add);

        publish("orders", "OrderPlaced: order-1");
        publish("orders", "OrderPlaced: order-2");

        System.out.println("shipping service received: " + shippingReceived);
        System.out.println("analytics service received: " + analyticsReceived);
        System.out.println("-> both received BOTH messages, independently (unlike point-to-point)");

        // Level 3: a third subscriber joins AFTER order-1 and order-2 were already published.
        List<String> emailReceived = new ArrayList<>();
        subscribe("orders", emailReceived::add);

        publish("orders", "OrderPlaced: order-3");

        System.out.println("email service (joined late) received: " + emailReceived);
        System.out.println("shipping service now has: " + shippingReceived);
        System.out.println("-> email service only sees order-3; it missed order-1 and order-2, published before it subscribed");
    }
}
```

**How to run:** save as `PublishSubscribe.java`, then run `java PublishSubscribe.java`.

## 6. Walkthrough

1. `subscribe` registers a subscriber's callback under a topic name; `publish` loops over every registered subscriber for that topic and calls each one individually with the same message.
2. Level 1 registers `shippingReceived::add` and `analyticsReceived::add` as two subscribers on the `"orders"` topic, then publishes two messages.
3. Both printed lists show both messages — proof that each subscriber received its own full copy, unlike a point-to-point queue, where the two messages would have been split between the consumers.
4. Level 3 adds a third subscriber, `emailReceived::add`, only after the first two messages were already published, then publishes a third message.
5. `emailReceived` ends up with only `"OrderPlaced: order-3"`, while `shippingReceived` (subscribed from the start) has all three — demonstrating that a subscriber only receives messages published after it joined, not a history of everything that happened before.

## 7. Gotchas & takeaways

> Gotcha: a subscriber that is offline when a message is published simply misses it under basic pub/sub, unless the system specifically supports "durable subscriptions" that retain messages for offline subscribers until they reconnect. Confirm whether your messaging system offers this before relying on every subscriber eventually seeing every message.

- Pub/sub fans a single published message out to every current subscriber, each receiving its own independent copy — the opposite delivery model from a point-to-point queue.
- New subscribers can be added without any change to the publisher, making pub/sub a good fit for extending a system with new, independent reactions to the same event.
- A subscriber generally only receives messages published after it subscribes, unless the system provides durable subscriptions or replay.
- Related concepts: [Message queues (point-to-point)](0110-message-queues-point-to-point.md) (the one-consumer-per-message alternative), [Event streaming vs message queues](0112-event-streaming-vs-message-queues.md) (a related model that also supports replaying past messages).
