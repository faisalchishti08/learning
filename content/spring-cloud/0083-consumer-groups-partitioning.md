---
card: spring-cloud
gi: 83
slug: consumer-groups-partitioning
title: "Consumer groups & partitioning"
---

## 1. What it is

A consumer group is a named set of consumer instances that share the work of consuming a destination — each message is delivered to only *one* instance within a given group (competing consumers, for horizontal scaling), while different groups each independently receive their own full copy of every message (for genuinely different subscribers). Partitioning splits a destination into ordered sub-streams, guaranteeing all messages with the same partition key are always processed by the same consumer instance, preserving relative order for related messages.

```properties
spring.cloud.stream.bindings.handleOrder-in-0.destination=order-placed-events
spring.cloud.stream.bindings.handleOrder-in-0.group=billing-service-group

spring.cloud.stream.bindings.publishOrder-out-0.destination=order-placed-events
spring.cloud.stream.bindings.publishOrder-out-0.producer.partition-key-expression=payload.customerId
spring.cloud.stream.bindings.publishOrder-out-0.producer.partition-count=4
```

## 2. Why & when

Without a consumer group, running three instances of `billing-service` for scalability would mean all three receive every single event — triplicating the work instead of sharing it. `group` fixes that: instances sharing the same group name compete for messages, each message landing on exactly one of them. Partitioning solves a different, related problem: if a customer's events must be processed strictly in order (an `OrderPlaced` followed by an `OrderCancelled` for the *same* customer must never be processed out of order), random load-balancing across instances would risk exactly that — partitioning by customer ID guarantees all of one customer's events always land on the same consumer instance.

Reach for consumer groups and partitioning when:

- Multiple instances of the same service consume the same destination for horizontal scaling — `group` is what turns "triplicated processing" into "shared, load-balanced processing" across those instances.
- Different services need their own independent full copy of every event (billing needs every order; inventory also needs every order, but shouldn't compete with billing for them) — each service uses its *own* group name, distinct from the others.
- Relative ordering matters for a subset of related messages (all events for one customer, one order, one aggregate) — partitioning on that entity's ID guarantees they're always processed by the same instance, in the order they were published.

## 3. Core concept

```
 WITHOUT groups: every instance gets every message (broadcast)
 WITH groups:    instances in the SAME group compete -- each message goes to exactly ONE of them
                 instances in DIFFERENT groups each get their own full copy

 partitioning:   partition-key-expression decides which partition a message goes to
                 (e.g. hash(customerId) % partition-count)
                 messages with the SAME key always land on the SAME partition
                 -> always consumed by the SAME instance within a group -> order preserved for that key
```

Groups control *how many copies* of an event exist across the system; partitioning controls *ordering guarantees* within one destination.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three billing service instances in the same consumer group share incoming messages between them while inventory service in a different group receives its own full independent copy of every message">
  <rect x="230" y="20" width="180" height="34" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="41" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">order-placed-events</text>

  <rect x="30" y="90" width="130" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="95" y="111" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billing-1 (group A)</text>
  <rect x="170" y="90" width="130" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="235" y="111" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billing-2 (group A)</text>
  <text x="165" y="140" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">SAME group -- share/compete for messages</text>

  <rect x="440" y="90" width="150" height="34" rx="6" fill="#1c2430" stroke="#e6edf3" stroke-width="1.2"/>
  <text x="515" y="111" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">inventory-1 (group B)</text>
  <text x="515" y="140" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">DIFFERENT group -- own full copy</text>

  <line x1="280" y1="54" x2="95" y2="88" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a83)"/>
  <line x1="320" y1="54" x2="235" y2="88" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a83)"/>
  <line x1="360" y1="54" x2="515" y2="88" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a83)"/>

  <defs><marker id="a83" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Same-group instances split the workload; different-group instances each get their own independent stream of every message.

## 5. Runnable example

The scenario: distribute `order-placed-events` correctly across scaled billing instances while giving inventory its own full copy, and preserve per-customer ordering. Start with broadcast-only delivery (the scaling problem), then add consumer groups, then add partitioning for ordering guarantees.

### Level 1 — Basic

Broadcast-only delivery — every subscribed instance gets every message, even within the "same" logical service.

```java
import java.util.*;

public class ConsumerGroupsLevel1 {
    static List<Runnable> subscribers = new ArrayList<>();

    static void subscribe(Runnable handler) { subscribers.add(handler); }
    static void publish(String message) {
        for (Runnable subscriber : subscribers) subscriber.run(); // EVERY subscriber gets EVERY message
    }

    public static void main(String[] args) {
        subscribe(() -> System.out.println("billing-1 processed the order"));
        subscribe(() -> System.out.println("billing-2 processed the SAME order")); // triplicated work!

        publish("OrderPlaced(42)");
    }
}
```

How to run: `java ConsumerGroupsLevel1.java`

Both `billing-1` and `billing-2` process the exact same order — if these are two instances of the same service meant to *share* the workload, this is wasted, duplicated processing (and potentially a real bug, like double-charging a customer).

### Level 2 — Intermediate

Add consumer groups: instances in the same group compete for messages instead of both receiving every one.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class ConsumerGroupsLevel2 {
    static Map<String, List<Runnable>> groupSubscribers = new HashMap<>();
    static Map<String, AtomicInteger> groupCounters = new HashMap<>();

    static void subscribe(String group, Runnable handler) {
        groupSubscribers.computeIfAbsent(group, k -> new ArrayList<>()).add(handler);
        groupCounters.putIfAbsent(group, new AtomicInteger(0));
    }

    static void publish(String message) {
        for (String group : groupSubscribers.keySet()) {
            // within EACH group, round-robin to exactly ONE instance -- they compete, not all receive it
            List<Runnable> instances = groupSubscribers.get(group);
            int index = groupCounters.get(group).getAndIncrement() % instances.size();
            instances.get(index).run();
        }
    }

    public static void main(String[] args) {
        subscribe("billing-service-group", () -> System.out.println("billing-1 processed it"));
        subscribe("billing-service-group", () -> System.out.println("billing-2 processed it"));
        subscribe("inventory-service-group", () -> System.out.println("inventory-1 processed it (own group)"));

        publish("OrderPlaced(42)");
        publish("OrderPlaced(43)");
    }
}
```

How to run: `java ConsumerGroupsLevel2.java`

Within `"billing-service-group"`, messages round-robin between `billing-1` and `billing-2` — each message goes to exactly one of them, sharing the workload instead of duplicating it. `"inventory-service-group"`, being a separate group, still receives its own independent copy of every message, since group membership only affects competition *within* the same group.

### Level 3 — Advanced

Add partitioning by customer ID on top of consumer groups, guaranteeing all of one customer's events are always processed by the same instance, preserving their relative order — critical for a customer whose `OrderPlaced` and `OrderCancelled` events must never be processed out of sequence.

```java
import java.util.*;

public class ConsumerGroupsLevel3 {
    record OrderEvent(String customerId, String type, int orderId) {}

    static Map<String, List<java.util.function.Consumer<OrderEvent>>> groupSubscribers = new HashMap<>();

    static void subscribe(String group, java.util.function.Consumer<OrderEvent> handler) {
        groupSubscribers.computeIfAbsent(group, k -> new ArrayList<>()).add(handler);
    }

    static int partitionFor(String customerId, int partitionCount) {
        return Math.floorMod(customerId.hashCode(), partitionCount); // same customerId ALWAYS maps to the same partition
    }

    static void publish(OrderEvent event) {
        for (String group : groupSubscribers.keySet()) {
            List<java.util.function.Consumer<OrderEvent>> instances = groupSubscribers.get(group);
            int partition = partitionFor(event.customerId(), instances.size());
            // the SAME customerId always routes to the SAME instance index -- guaranteed ordering per customer
            instances.get(partition).accept(event);
        }
    }

    public static void main(String[] args) {
        subscribe("billing-service-group", e -> System.out.println("billing-1: " + e));
        subscribe("billing-service-group", e -> System.out.println("billing-2: " + e));

        // two events for the SAME customer -- must be processed in order, by the SAME instance
        publish(new OrderEvent("cust-A", "OrderPlaced", 42));
        publish(new OrderEvent("cust-A", "OrderCancelled", 42));

        // a DIFFERENT customer's event might land on a different instance -- that's fine, no ordering relationship
        publish(new OrderEvent("cust-B", "OrderPlaced", 99));
    }
}
```

How to run: `java ConsumerGroupsLevel3.java`

`partitionFor("cust-A", 2)` computes the exact same partition index every time it's called with `"cust-A"`, regardless of when — so both of `cust-A`'s events (`OrderPlaced` then `OrderCancelled`) are routed to the identical `billing-service-group` instance, in the exact order they were published, guaranteeing correct sequential processing for that customer. `cust-B`'s event, hashing to a potentially different partition, might land on a different instance entirely — which is fine, since there's no ordering relationship between different customers' events to preserve.

## 6. Walkthrough

Trace the three `publish` calls in Level 3.

1. `publish(new OrderEvent("cust-A", "OrderPlaced", 42))` runs — inside the loop over `groupSubscribers.keySet()`, `"billing-service-group"` is found. `partitionFor("cust-A", 2)` computes `Math.floorMod("cust-A".hashCode(), 2)`, some deterministic value, say `1` (the exact number depends on Java's string hashing, but it's consistent). `instances.get(1)` is invoked, printing `billing-2: OrderEvent[customerId=cust-A, type=OrderPlaced, orderId=42]`.
2. `publish(new OrderEvent("cust-A", "OrderCancelled", 42))` runs next — `partitionFor("cust-A", 2)` is called again with the identical `customerId`, so `"cust-A".hashCode()` and the resulting `Math.floorMod` computation produce the *exact same* result as before: `1`. `instances.get(1)` is invoked again — the same `billing-2` instance that handled the `OrderPlaced` event also handles this `OrderCancelled` event, guaranteeing they're processed by the same instance, in the order they were published.
3. `publish(new OrderEvent("cust-B", "OrderPlaced", 99))` runs — `partitionFor("cust-B", 2)` computes a hash for a *different* string, which may (or may not) land on a different partition index than `"cust-A"` did; here it might resolve to `0`, routing to `billing-1` instead. Since there's no ordering requirement between `cust-A`'s and `cust-B`'s events, this is entirely correct behavior — partitioning only guarantees ordering *within* a given key, never *across* different keys.

```
partitionFor("cust-A", 2) -> always the SAME result every call -> both cust-A events -> SAME instance, in order
partitionFor("cust-B", 2) -> a DIFFERENT (possibly different) result -> cust-B's event -> possibly a different instance
                                                                          (no ordering relationship needed between them)
```

## 7. Gotchas & takeaways

> **Gotcha:** `partition-count` must match (or be compatible with, depending on the broker's specific rebalancing rules) the actual number of consumer instances in the group — too few partitions relative to instances means some instances never receive any messages at all; changing `partition-count` after data already exists in the destination can also disrupt existing ordering guarantees, since the same key may now hash to a different partition than it did before the change. Choose and set `partition-count` deliberately, ideally sized for expected future scale, not just current instance count.

- Consumer groups turn "every instance gets every message" (correct for genuinely independent subscribers) into "instances in the group share the workload" (correct for horizontally-scaled instances of the same logical consumer) — group naming is the single configuration deciding which behavior applies.
- Partitioning guarantees ordering only *within* one partition key (all events sharing the same key) — it makes no ordering promise whatsoever *across* different keys, which is usually exactly the right and sufficient guarantee (as with `cust-A` versus `cust-B` here).
- A group name should generally be unique per logical service (not per instance) — every instance of `billing-service` uses the *same* group name, so they compete with each other, while `inventory-service` uses its own distinct group name to get its own independent copy.
- Partitioning and consumer groups compose: partitioning decides which partition a message lands in; the consumer group's instances then divide up which of them handles which partitions — together they deliver both horizontal scalability and per-key ordering guarantees simultaneously.
