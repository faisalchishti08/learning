---
card: spring-data
gi: 127
slug: pub-sub-messaging-messagelistener
title: "Pub/Sub messaging (MessageListener)"
---

## 1. What it is

Redis **publish/subscribe** lets one process broadcast a message on a named channel and any number of other processes, each registered as a `MessageListener`, receive it instantly — Spring Data Redis wires this through `RedisMessageListenerContainer`, which manages subscriptions and dispatches incoming messages to your listener beans.

```java
@Bean
RedisMessageListenerContainer container(RedisConnectionFactory cf, MessageListener listener) {
    RedisMessageListenerContainer container = new RedisMessageListenerContainer();
    container.setConnectionFactory(cf);
    container.addMessageListener(listener, new ChannelTopic("order-events"));
    return container;
}
```

## 2. Why & when

Redis pub/sub is conceptually similar to the reactive change streams covered for MongoDB, but simpler and more general: any process can publish to any named channel, and any process can subscribe, with no requirement that the message relate to a database write at all. It's a lightweight, fire-and-forget broadcast mechanism — useful precisely because it needs no dedicated message broker when you already have Redis in your stack.

Reach for Redis pub/sub when:

- You need lightweight, low-latency broadcast between application instances — invalidating a local cache on every instance when one instance updates shared data, for example.
- The messages are transient by nature — if a subscriber isn't connected when a message is published, it's simply gone; pub/sub delivers to whoever is listening *right now*, with no persistence or replay (unlike Redis Streams, covered in the next card, which does persist).
- You already run Redis and want a simple broadcast channel without introducing a separate message broker (Kafka, RabbitMQ) for a use case that doesn't need their stronger delivery guarantees.

## 3. Core concept

```
 Publisher:  redisTemplate.convertAndSend("order-events", "order:1 SHIPPED")
                                |
                                v
                     Redis PUBLISH order-events "order:1 SHIPPED"
                                |
                 (fanned out to EVERY current subscriber, instantly)
                    /                    |                    \
        Subscriber A               Subscriber B          (no subscribers? message is LOST)
     onMessage(...)              onMessage(...)
```

Publish is fire-and-forget: if zero processes are subscribed to a channel at the moment a message is published, that message is simply gone — nothing stores it for a late subscriber.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A published message fans out instantly to every current subscriber of a channel, with nothing persisted for late subscribers">
  <rect x="20" y="60" width="160" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="87" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">convertAndSend(...)</text>

  <rect x="250" y="60" width="140" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="87" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">channel: order-events</text>

  <line x1="180" y1="82" x2="245" y2="82" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="460" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="535" y="44" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Subscriber A</text>

  <rect x="460" y="110" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="535" y="134" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Subscriber B</text>

  <line x1="390" y1="75" x2="455" y2="40" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>
  <line x1="390" y1="90" x2="455" y2="125" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Every currently-connected subscriber receives the message at the same time; a subscriber that connects a moment later never sees it.

## 5. Runnable example

The scenario: broadcasting order-status changes to interested listeners, evolving from a basic publish/subscribe pair, to multiple listeners on the same channel plus channel-based filtering (only listening to specific channels), to demonstrating pub/sub's core limitation — a message published with no subscribers is simply lost.

### Level 1 — Basic

Model the core publish/subscribe mechanism: a publisher sends a message, a registered listener receives it.

```java
import java.util.*;
import java.util.function.*;

public class PubSubLevel1 {
    public static void main(String[] args) {
        RedisMessageBroker broker = new RedisMessageBroker();

        broker.subscribe("order-events", message -> System.out.println("Listener received: " + message));

        broker.publish("order-events", "order:1 SHIPPED"); // PUBLISH order-events "order:1 SHIPPED"
        broker.publish("order-events", "order:2 DELIVERED");
    }
}

// Stands in for RedisMessageListenerContainer + redisTemplate.convertAndSend(...).
class RedisMessageBroker {
    private final Map<String, List<Consumer<String>>> subscribers = new HashMap<>();

    void subscribe(String channel, Consumer<String> listener) {
        subscribers.computeIfAbsent(channel, k -> new ArrayList<>()).add(listener);
    }

    void publish(String channel, String message) {
        for (Consumer<String> listener : subscribers.getOrDefault(channel, List.of())) {
            listener.accept(message); // delivered SYNCHRONOUSLY here, for demo simplicity
        }
    }
}
```

How to run: `java PubSubLevel1.java`

`subscribe` registers a listener under a channel name, mirroring `container.addMessageListener(listener, new ChannelTopic("order-events"))`. `publish` mirrors `redisTemplate.convertAndSend(channel, message)` — every registered listener for that channel is invoked with the message, in this simplified model, immediately and synchronously.

### Level 2 — Intermediate

Register multiple listeners on the same channel, and a listener scoped to a *different* channel, showing that delivery is per-channel and fans out to every subscriber of that specific channel.

```java
import java.util.*;
import java.util.function.*;

public class PubSubLevel2 {
    public static void main(String[] args) {
        RedisMessageBroker broker = new RedisMessageBroker();

        broker.subscribe("order-events", msg -> System.out.println("Dashboard: " + msg));
        broker.subscribe("order-events", msg -> System.out.println("Audit log: " + msg));
        broker.subscribe("payment-events", msg -> System.out.println("Payment listener: " + msg)); // DIFFERENT channel

        broker.publish("order-events", "order:1 SHIPPED"); // only order-events subscribers fire
        broker.publish("payment-events", "payment:1 CAPTURED"); // only payment-events subscribers fire
    }
}

class RedisMessageBroker {
    private final Map<String, List<Consumer<String>>> subscribers = new HashMap<>();
    void subscribe(String channel, Consumer<String> listener) { subscribers.computeIfAbsent(channel, k -> new ArrayList<>()).add(listener); }
    void publish(String channel, String message) {
        for (Consumer<String> listener : subscribers.getOrDefault(channel, List.of())) listener.accept(message);
    }
}
```

How to run: `java PubSubLevel2.java`

Two listeners ("Dashboard" and "Audit log") both subscribe to `"order-events"`; a third ("Payment listener") subscribes only to `"payment-events"`. Publishing to `"order-events"` fires both order-related listeners but not the payment one; publishing to `"payment-events"` does the reverse — channels fully isolate delivery, matching `ChannelTopic`-scoped subscriptions in real Spring Data Redis.

### Level 3 — Advanced

Demonstrate pub/sub's core limitation directly: a message published while no subscriber is connected is lost forever, with no way for a later subscriber to retrieve it — the exact trade-off that motivates Redis Streams (the next card) for cases that need durability.

```java
import java.util.*;
import java.util.function.*;

public class PubSubLevel3 {
    public static void main(String[] args) {
        RedisMessageBroker broker = new RedisMessageBroker();

        // Publish BEFORE anyone subscribes -- nobody is listening yet.
        broker.publish("order-events", "order:1 CREATED");
        System.out.println("Published 'order:1 CREATED' with zero subscribers -- message is now gone forever.");

        // NOW a subscriber connects -- too late for the message above.
        List<String> received = new ArrayList<>();
        broker.subscribe("order-events", received::add);

        broker.publish("order-events", "order:1 SHIPPED"); // this one WILL be received -- subscriber is connected

        System.out.println("Messages this subscriber actually received: " + received);
        System.out.println("Notice 'order:1 CREATED' is missing -- pub/sub never buffers for late subscribers.");
    }
}

class RedisMessageBroker {
    private final Map<String, List<Consumer<String>>> subscribers = new HashMap<>();
    void subscribe(String channel, Consumer<String> listener) { subscribers.computeIfAbsent(channel, k -> new ArrayList<>()).add(listener); }
    void publish(String channel, String message) {
        // No storage of any kind -- if subscribers.get(channel) is empty or absent, the message is simply discarded.
        for (Consumer<String> listener : subscribers.getOrDefault(channel, List.of())) listener.accept(message);
    }
}
```

How to run: `java PubSubLevel3.java`

The first `publish` call happens before any listener has subscribed — `subscribers.getOrDefault("order-events", List.of())` returns an empty list, so the loop body never runs, and `"order:1 CREATED"` is discarded with no trace. Only after `subscribe` is called does a listener exist to receive `"order:1 SHIPPED"`, which is why `received` contains only the second message.

## 6. Walkthrough

Execution starts in `main` for Level 3. `broker.publish("order-events", "order:1 CREATED")` is called first, before any `subscribe` call has happened. Inside `publish`, `subscribers.getOrDefault("order-events", List.of())` looks up the `"order-events"` channel in a map that has no entries at all yet, so it falls back to the empty list default — the `for` loop iterates zero times, and the message is discarded without being stored anywhere.

`broker.subscribe("order-events", received::add)` then registers a listener that appends every received message to the `received` list. `broker.publish("order-events", "order:1 SHIPPED")` runs next: this time `subscribers.getOrDefault(...)` finds the one listener just registered, and the loop calls it once, appending `"order:1 SHIPPED"` to `received`.

```
Published 'order:1 CREATED' with zero subscribers -- message is now gone forever.
Messages this subscriber actually received: [order:1 SHIPPED]
Notice 'order:1 CREATED' is missing -- pub/sub never buffers for late subscribers.
```

In real Redis, this is exactly how `PUBLISH`/`SUBSCRIBE` behave: `PUBLISH` returns the count of clients the message was delivered to at that instant, and if that count is zero, the message is gone — there's no queue, no log, no persistence backing a pub/sub channel. This is the fundamental trade-off pub/sub makes for its simplicity and low latency, and it's precisely the gap Redis Streams (covered next) fills for use cases where messages need to survive until a consumer is ready to read them.

## 7. Gotchas & takeaways

> Gotcha: a subscriber that briefly disconnects (a network blip, an application restart) loses every message published during that gap — pub/sub has no memory and no replay. If losing messages during downtime is unacceptable, use Redis Streams instead, which persists messages and lets consumers catch up.

> Gotcha: `RedisMessageListenerContainer` runs its own dedicated connection for subscriptions, separate from the connection(s) used for regular commands — a Redis connection that has issued `SUBSCRIBE` can (depending on the client) enter a special mode where it can only issue further pub/sub commands until it unsubscribes.

- Redis pub/sub broadcasts a published message to every subscriber connected to that channel *at the moment of publish*, with zero persistence.
- `RedisMessageListenerContainer` manages the subscription lifecycle and dispatches incoming messages to registered `MessageListener` beans, scoped by `ChannelTopic` (or pattern, for wildcard subscriptions).
- If no subscriber is listening when a message is published, that message is lost — there is no queue or replay behind a pub/sub channel.
- Reach for pub/sub when low-latency, fire-and-forget broadcast is enough; reach for Redis Streams (next card) when messages must survive until a consumer is ready to process them.
