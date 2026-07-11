---
card: spring-cloud
gi: 91
slug: linking-nodes-via-a-message-broker
title: "Linking nodes via a message broker"
---

## 1. What it is

Spring Cloud Bus links every node in a distributed system to a shared message broker (RabbitMQ or Kafka, via the same binder abstraction Spring Cloud Stream uses) so that one node can broadcast an event and have every other node receive it, without any node needing to know the network address of any other node.

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-bus-amqp</artifactId>
</dependency>
```

```properties
spring.rabbitmq.host=localhost
spring.rabbitmq.port=5672
```

## 2. Why & when

In a single-instance application, one component notifying another is a plain in-process method call or event publish. Once an application is deployed as five, twenty, or two hundred replicas behind a load balancer, that stops working — an event raised inside instance 3 has no way to reach instances 1, 2, 4, and 5 through direct in-process calls, since each instance is a separate JVM, possibly on a separate host, with no shared memory or shared object graph. Spring Cloud Bus solves this by giving every instance a persistent connection to the same message broker: publishing an event to the bus from any one instance results in every other instance connected to that broker receiving it, because the broker itself fans the message out to every subscriber, using the same durable, at-least-once delivery infrastructure already trusted for business messaging.

Reach for the bus when:

- Multiple instances of the same service (or a set of related services) need to react to the same event, without one instance polling another or the caller knowing every instance's address.
- The event is administrative or infrastructural rather than business data — a configuration change, a cache eviction signal, a "shut down gracefully" broadcast — since the bus is designed for this kind of fleet-wide coordination message, not high-volume domain events (that is what plain Spring Cloud Stream bindings, covered earlier, are for).
- The set of receiving instances is dynamic — instances scale up and down constantly, and the bus's broker-mediated fan-out means new instances simply start receiving events the moment they connect, with no registration step against the sender.

## 3. Core concept

```
 without a bus:                          with a bus:

 instance A --?--> instance B             instance A --publish--> [ broker ]
 instance A --?--> instance C                                         |
 instance A --?--> instance D                              fan-out to every subscriber
 (A needs to know B, C, D's addresses)                       |      |      |
                                                          instance B  C     D
                                                    (A never learns B/C/D exist)
```

Every instance opens one connection to the broker on startup and subscribes to a shared topic/exchange dedicated to bus events — publishing to that topic is the entire mechanism; the broker's own fan-out guarantees every subscriber receives a copy.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Instance A publishes one event to a shared message broker which fans the event out to instances B C and D without A knowing their addresses">
  <rect x="270" y="20" width="100" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">broker</text>

  <rect x="20" y="120" width="110" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="144" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">instance A (publisher)</text>

  <rect x="180" y="180" width="90" height="34" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="225" y="201" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance B</text>
  <rect x="290" y="180" width="90" height="34" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="335" y="201" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance C</text>
  <rect x="400" y="180" width="90" height="34" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="445" y="201" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance D</text>

  <defs><marker id="a91" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="130" y1="130" x2="270" y2="55" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a91)"/>
  <line x1="310" y1="70" x2="230" y2="180" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a91)"/>
  <line x1="320" y1="70" x2="335" y2="180" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a91)"/>
  <line x1="335" y1="70" x2="440" y2="180" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a91)"/>
</svg>

One publish from A, one broker-mediated fan-out, three instances receive it — none of them needed A's address, nor did A need theirs.

## 5. Runnable example

The scenario: model a tiny fleet-coordination bus in memory — no real broker, just the fan-out mechanics the bus relies on — where one node publishes an event and every other subscribed node receives it. Start with a single subscriber, then multiple subscribers, then add subscriber churn (nodes joining and leaving) to show the bus keeps working as fleet membership changes.

### Level 1 — Basic

One publisher, one subscriber, connected only through a shared broker object — never directly.

```java
import java.util.*;
import java.util.function.Consumer;

public class MessageBrokerLevel1 {
    // stands in for the real broker (RabbitMQ/Kafka) -- holds subscribers, fans out published events
    static class Broker {
        List<Consumer<String>> subscribers = new ArrayList<>();
        void subscribe(Consumer<String> handler) { subscribers.add(handler); }
        void publish(String event) {
            for (Consumer<String> handler : subscribers) handler.accept(event); // fan-out
        }
    }

    public static void main(String[] args) {
        Broker broker = new Broker();

        // instance B subscribes -- instance A never learns this happened, nor B's identity
        broker.subscribe(event -> System.out.println("instance B received: " + event));

        // instance A publishes -- it has no reference to instance B at all, only to the broker
        broker.publish("config-refresh");
    }
}
```

How to run: `java MessageBrokerLevel1.java`

Instance A calls `broker.publish`, never `handler.accept` directly and never anything resembling instance B's address — the broker is the only thing either side references, exactly like a real message broker mediating between two Spring Boot instances that never open a direct network connection to each other.

### Level 2 — Intermediate

Extend to multiple subscribers, modeling a real fleet where every instance is both a potential publisher and a potential subscriber.

```java
import java.util.*;
import java.util.function.Consumer;

public class MessageBrokerLevel2 {
    static class Broker {
        List<Consumer<String>> subscribers = new ArrayList<>();
        void subscribe(Consumer<String> handler) { subscribers.add(handler); }
        void publish(String event) {
            for (Consumer<String> handler : subscribers) handler.accept(event);
        }
    }

    public static void main(String[] args) {
        Broker broker = new Broker();

        // three fleet instances, each subscribing independently -- none aware of the others
        broker.subscribe(event -> System.out.println("instance B received: " + event));
        broker.subscribe(event -> System.out.println("instance C received: " + event));
        broker.subscribe(event -> System.out.println("instance D received: " + event));

        // instance A publishes ONCE -- the broker fans it out to all three, unmodified
        broker.publish("config-refresh");
    }
}
```

How to run: `java MessageBrokerLevel2.java`

A single `broker.publish` call results in three separate `handler.accept` invocations, one per subscriber, because the broker's `publish` method loops over every registered subscriber — this is the exact fan-out semantic a real broker's exchange/topic delivers, just modeled with a `List` instead of network sockets.

### Level 3 — Advanced

Add subscriber churn: instances join and leave the fleet at runtime (mirroring real autoscaling), and publish still reaches only currently-connected subscribers, with no special handling required for the sender.

```java
import java.util.*;
import java.util.function.Consumer;

public class MessageBrokerLevel3 {
    static class Broker {
        Map<String, Consumer<String>> subscribers = new LinkedHashMap<>();
        void subscribe(String instanceId, Consumer<String> handler) {
            subscribers.put(instanceId, handler);
            System.out.println(instanceId + " joined the bus");
        }
        void unsubscribe(String instanceId) {
            subscribers.remove(instanceId);
            System.out.println(instanceId + " left the bus");
        }
        void publish(String event) {
            for (Map.Entry<String, Consumer<String>> e : subscribers.entrySet()) {
                e.getValue().accept(event); // delivered only to CURRENTLY connected subscribers
            }
        }
    }

    public static void main(String[] args) {
        Broker broker = new Broker();

        broker.subscribe("instance-B", event -> System.out.println("  instance-B received: " + event));
        broker.subscribe("instance-C", event -> System.out.println("  instance-C received: " + event));

        System.out.println("-- publish #1 (B and C connected) --");
        broker.publish("config-refresh v1");

        broker.unsubscribe("instance-C"); // C scales down / disconnects
        broker.subscribe("instance-E", event -> System.out.println("  instance-E received: " + event)); // E scales up

        System.out.println("-- publish #2 (C left, E joined) --");
        broker.publish("config-refresh v2");
    }
}
```

How to run: `java MessageBrokerLevel3.java`

The second `publish` call reaches `instance-B` (still connected) and `instance-E` (newly joined) but not `instance-C` (disconnected) — the sender's `publish("config-refresh v2")` call is byte-for-byte identical in shape to the first, requiring no knowledge of which instances currently exist, exactly mirroring how a real bus publisher never needs to track fleet membership itself.

## 6. Walkthrough

Trace `main` in Level 3 from the first line to the last.

1. `broker.subscribe("instance-B", ...)` runs, adding an entry to the `subscribers` map keyed by `"instance-B"`, and prints `instance-B joined the bus`.
2. `broker.subscribe("instance-C", ...)` runs next, adding a second entry — the map now holds two subscribers.
3. `broker.publish("config-refresh v1")` iterates the map's two entries in insertion order, calling each `Consumer`'s `accept` method with `"config-refresh v1"` — this prints `instance-B received: config-refresh v1` followed by `instance-C received: config-refresh v1`.
4. `broker.unsubscribe("instance-C")` removes that entry from the map and prints `instance-C left the bus` — from this point on, the map holds only `"instance-B"`.
5. `broker.subscribe("instance-E", ...)` adds a new entry — the map now holds `"instance-B"` and `"instance-E"`, in that order.
6. `broker.publish("config-refresh v2")` iterates the (now different) map contents, delivering to `instance-B` and `instance-E` only — `instance-C`, no longer present in the map, receives nothing, and the code never had to explicitly check who was still connected; the map's current contents alone determined delivery.

```
publish #1: subscribers = {B, C}       -> B receives, C receives
   (C unsubscribes, E subscribes)
publish #2: subscribers = {B, E}       -> B receives, E receives, C receives NOTHING
```

## 7. Gotchas & takeaways

> **Gotcha:** a real message broker's fan-out is asynchronous and network-mediated, unlike this in-memory model's synchronous, same-thread `for` loop — a slow or temporarily disconnected subscriber in production doesn't block the publisher, and message delivery order across different subscribers is not guaranteed the way iterating a single in-process `Map` guarantees it. Never assume Spring Cloud Bus events arrive at every instance at exactly the same instant, or in the same relative order the publisher issued them.

- The core value of a bus is decoupling: the publisher references only the broker, never any specific subscriber, so the set of subscribers can grow, shrink, or fully turn over without any change to publishing code.
- This pattern is deliberately reserved for infrastructural, fleet-wide coordination events (as later cards on config refresh and custom bus events will show) rather than high-volume domain data, which belongs on ordinary Spring Cloud Stream bindings instead.
- Broker-mediated fan-out means the publisher pays a fixed cost (one publish call) regardless of how many subscribers currently exist — this is what makes the bus scale cleanly as fleet size changes, unlike a hypothetical design where the publisher had to loop over and call every instance individually.
- Because delivery is broker-mediated rather than direct, a bus event's ordering and timing guarantees are exactly whatever the underlying broker (RabbitMQ or Kafka) provides — understanding those guarantees matters before relying on the bus for anything order-sensitive.
