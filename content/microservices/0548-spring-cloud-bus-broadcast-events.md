---
card: microservices
gi: 548
slug: spring-cloud-bus-broadcast-events
title: "Spring Cloud Bus (broadcast events)"
---

## 1. What it is

Positioned within the broader Spring Cloud ecosystem, **Spring Cloud Bus** is the thin, general-purpose broadcast layer that several other Spring Cloud modules build on: it links every service instance to a lightweight message topic (via the same Kafka or RabbitMQ binder infrastructure [Spring Cloud Stream](0547-spring-cloud-stream-event-driven.md) uses), and lets any instance publish an event that every other connected instance receives. [Configuration refresh](0537-spring-cloud-bus-for-cross-instance-coordination.md) is its most common built-in use, but the underlying mechanism is general — any `RemoteApplicationEvent` subclass can be broadcast, making the Bus a small, reusable building block for fleet-wide notification, not a single-purpose config-refresh tool.

## 2. Why & when

Understanding where Bus sits in the ecosystem clarifies when to reach for it versus its neighboring modules:

- **Bus solves one specific shape of problem — "notify every instance" — that no other single Spring Cloud module targets directly.** [Spring Cloud Stream](0547-spring-cloud-stream-event-driven.md) is built for general message-driven communication between different *services* (an order service publishing to a shipping service); Bus is specifically for broadcasting *within* a fleet of instances of the same (or related) service, or across the whole system for operational events.
- **It reuses the same underlying transport infrastructure as Stream** (Kafka or RabbitMQ, via the same binder concept), so if your system already has one of those brokers deployed for Stream-based messaging, adding Bus doesn't necessarily mean standing up new infrastructure — just adding the `spring-cloud-starter-bus-amqp`/`-kafka` dependency and letting instances subscribe to the Bus's own topic.
- **Beyond configuration refresh, Bus is a natural fit for any operational signal that every instance should react to**: a cache-invalidation broadcast telling every instance to drop a specific cached value, a maintenance-mode toggle telling every instance to start returning a "temporarily unavailable" response, or a custom domain event meant for fleet-wide awareness rather than point-to-point delivery.
- **You reach for Bus specifically when the coordination shape is "broadcast to all," not "deliver to one" (ordinary point-to-point messaging) or "process each message exactly once across a consumer group" (typical Stream/Kafka consumer group semantics)** — mixing up these shapes (using Stream's typical consumer-group model when you actually wanted every instance to react, or using Bus when you actually wanted load-shared processing) produces subtly wrong behavior that's easy to miss until multiple instances start behaving inconsistently.

## 3. Core concept

Think of Spring Cloud Bus as the building-wide intercom system in an office building that already has a phone network (the broker infrastructure Stream also uses) — the intercom doesn't replace individual desk-to-desk phone calls (Stream's point-to-point or consumer-group messaging), it serves a different, complementary purpose: one announcement, heard by every desk in the building simultaneously, for things that genuinely need everyone's attention at once (a fire drill, an all-hands notice) rather than a specific conversation between two people.

Concretely:

1. **Any `RemoteApplicationEvent` subclass can be published onto the Bus** — `RefreshRemoteApplicationEvent` (used for config refresh) is Spring Cloud's own built-in example, but application code can define and publish custom event subclasses for its own broadcast needs.
2. **Every instance connected to the same Bus topic receives every published event**, regardless of how many instances exist — the publisher never enumerates or addresses specific instances.
3. **Bus reuses the same broker (Kafka/RabbitMQ) infrastructure Spring Cloud Stream uses**, but with a distinct topic/exchange dedicated to Bus's own broadcast traffic, separate from any application-level Stream bindings — the two coexist without interfering with each other.
4. **Bus is the right tool specifically for "every instance should react," as distinct from Stream's more typical "exactly one consumer in a group processes this message" model** — picking the wrong one for a given coordination need produces either duplicated processing (if you wanted one) or missed instances (if you wanted all).

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Cloud Bus sits alongside Stream in the ecosystem, reusing the same broker transport, but serving broadcast-to-all needs rather than typical point-to-point or consumer-group message processing">
  <rect x="20" y="20" width="620" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Shared broker infrastructure (Kafka / RabbitMQ)</text>

  <rect x="40" y="90" width="260" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="170" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Cloud Stream</text>
  <text x="170" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">point-to-point / consumer-group processing</text>

  <rect x="360" y="90" width="260" height="60" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="490" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Cloud Bus</text>
  <text x="490" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">broadcast to EVERY connected instance</text>
</svg>

Bus and Stream share the same underlying transport but serve distinct coordination shapes — broadcast-to-all versus typical message processing.

## 5. Runnable example

Scenario: broadcasting a cache-invalidation signal across a fleet, distinct from the earlier config-refresh example. We start with a plain Java model contrasting "deliver to one" versus "broadcast to all," extend it to a custom broadcast event type, then show the real Spring Cloud Bus custom-event shape.

### Level 1 — Basic

```java
// File: DeliveryShapeContrast.java -- contrasts DELIVER-TO-ONE (typical
// queue/consumer-group processing) with BROADCAST-TO-ALL (Bus's shape).
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class DeliveryShapeContrast {
    static List<String> consumerGroupMembers = List.of("instance-A", "instance-B", "instance-C");
    static AtomicInteger roundRobinIndex = new AtomicInteger(0);

    // DELIVER-TO-ONE: exactly one member processes each message (typical Stream consumer group)
    static void deliverToOne(String message) {
        String chosen = consumerGroupMembers.get(roundRobinIndex.getAndIncrement() % consumerGroupMembers.size());
        System.out.println("[deliver-to-one] '" + message + "' processed by ONLY: " + chosen);
    }

    // BROADCAST-TO-ALL: every member processes the SAME message (Bus's shape)
    static void broadcastToAll(String message) {
        for (String member : consumerGroupMembers) {
            System.out.println("[broadcast-to-all] '" + message + "' processed by: " + member);
        }
    }

    public static void main(String[] args) {
        deliverToOne("process-order-42");   // ONE instance handles it
        broadcastToAll("invalidate-cache-key:order-42"); // ALL instances handle it
    }
}
```

How to run: `java DeliveryShapeContrast.java`

`deliverToOne` picks exactly one member to process a given message — the right shape for work that should happen once, like processing an order. `broadcastToAll` has every member process the same message — the right shape for a cache-invalidation signal, where every instance's own local cache needs to drop the same stale entry, not just one instance's.

### Level 2 — Intermediate

```java
// File: CustomBroadcastEvent.java -- models a CUSTOM broadcast event
// type (not just configuration refresh), showing Bus's general-purpose
// nature: any event type can ride the same broadcast mechanism.
import java.util.*;
import java.util.function.Consumer;

public class CustomBroadcastEvent {
    interface BusEvent {}
    record CacheInvalidateEvent(String cacheKey) implements BusEvent {}
    record MaintenanceModeEvent(boolean enabled) implements BusEvent {}

    static List<Consumer<BusEvent>> subscribers = new ArrayList<>();
    static void subscribe(String instanceName, Consumer<BusEvent> handler) { subscribers.add(handler); }
    static void publish(BusEvent event) {
        System.out.println("Publishing " + event.getClass().getSimpleName() + " to the bus...");
        subscribers.forEach(s -> s.accept(event));
    }

    public static void main(String[] args) {
        subscribe("instance-A", event -> {
            if (event instanceof CacheInvalidateEvent e) System.out.println("[instance-A] dropping cache key: " + e.cacheKey());
            if (event instanceof MaintenanceModeEvent e) System.out.println("[instance-A] maintenance mode now: " + e.enabled());
        });
        subscribe("instance-B", event -> {
            if (event instanceof CacheInvalidateEvent e) System.out.println("[instance-B] dropping cache key: " + e.cacheKey());
            if (event instanceof MaintenanceModeEvent e) System.out.println("[instance-B] maintenance mode now: " + e.enabled());
        });

        publish(new CacheInvalidateEvent("order-42"));   // a CUSTOM event type, not config refresh
        publish(new MaintenanceModeEvent(true));          // ANOTHER custom event type, same broadcast mechanism
    }
}
```

How to run: `java CustomBroadcastEvent.java`

`CacheInvalidateEvent` and `MaintenanceModeEvent` are both custom event types, unrelated to configuration refresh, riding the exact same `publish`-to-all-`subscribers` mechanism — demonstrating that Bus's underlying broadcast idea generalizes to any operational signal a fleet needs to share, not just the built-in `RefreshRemoteApplicationEvent`.

### Level 3 — Advanced

```java
// File: SpringCloudBusCustomEventRealShape.java -- the REAL Spring
// Cloud Bus shape for a CUSTOM event type: extending RemoteApplicationEvent
// and listening for it, distinct from the built-in refresh event.
import org.springframework.cloud.bus.event.RemoteApplicationEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;
import org.springframework.cloud.bus.BusEnvironment;

public class SpringCloudBusCustomEventRealShape {

    // a CUSTOM broadcast event, extending Bus's own base class
    static class CacheInvalidateRemoteEvent extends RemoteApplicationEvent {
        private String cacheKey;
        public CacheInvalidateRemoteEvent() {} // required no-arg constructor for deserialization
        public CacheInvalidateRemoteEvent(Object source, String originService, String cacheKey) {
            super(source, originService);
            this.cacheKey = cacheKey;
        }
        public String getCacheKey() { return cacheKey; }
    }

    @Component
    static class CacheInvalidationListener {
        // fires on EVERY instance connected to the bus, whenever ANY instance publishes this event type
        @EventListener
        public void onCacheInvalidate(CacheInvalidateRemoteEvent event) {
            System.out.println("Received broadcast: dropping local cache entry for key " + event.getCacheKey());
            // real implementation: localCache.evict(event.getCacheKey());
        }
    }

    // Publishing side (on whichever instance detects the underlying data changed):
    // applicationEventPublisher.publishEvent(
    //     new CacheInvalidateRemoteEvent(this, busProperties.getId(), "order-42"));
    // -- this ONE publish call reaches every OTHER instance connected to the same bus topic.
}
```

How to run: requires `spring-cloud-starter-bus-amqp` (or `-kafka`) on every instance, all connected to the same broker; publishing a `CacheInvalidateRemoteEvent` via `ApplicationEventPublisher.publishEvent(...)` on any one instance triggers `CacheInvalidationListener.onCacheInvalidate` to fire on every connected instance, observable by running multiple instances and watching each one log the "dropping local cache entry" message after just one publish call anywhere in the fleet.

`CacheInvalidateRemoteEvent extends RemoteApplicationEvent` is what marks this as a Bus-broadcast event rather than an ordinary, local-only Spring `ApplicationEvent` — Bus automatically serializes and republishes any `RemoteApplicationEvent` subclass onto the shared broker topic, and every instance's own local event system re-fires it locally upon receipt, which is why a plain `@EventListener` method (no Bus-specific subscription code) is enough to react to it on every instance.

## 6. Walkthrough

Trace what happens when Instance A detects that order `42`'s underlying data changed and needs its cache entry invalidated fleet-wide, across a three-instance fleet (A, B, C) all connected to the same Bus topic:

1. **Instance A calls `applicationEventPublisher.publishEvent(new CacheInvalidateRemoteEvent(this, "instance-A", "order-42"))`** through Spring's ordinary, local `ApplicationEventPublisher` — the same mechanism used for any local Spring event.
2. **Because `CacheInvalidateRemoteEvent` extends `RemoteApplicationEvent`, Spring Cloud Bus's own listener (registered automatically once the Bus starter is on the classpath) intercepts this local publish**, serializes the event, and republishes it onto the shared broker topic every Bus-connected instance subscribes to.
3. **The broker delivers this serialized event to every subscriber on that topic** — including Instance A itself (Bus is typically configured to let an instance ignore its own re-delivered events to avoid double-processing), Instance B, and Instance C.
4. **Each receiving instance's own Bus integration deserializes the event back into a `CacheInvalidateRemoteEvent` object** and re-fires it through that instance's *local* Spring event system — at this point, it behaves exactly like any ordinary local event on each receiving instance.
5. **Each instance's `CacheInvalidationListener.onCacheInvalidate` method (a plain `@EventListener`, with no Bus-specific code in it at all) fires in response**, printing its own "dropping local cache entry for key order-42" message and, in a real implementation, actually evicting that key from its own local cache.

The key point: `CacheInvalidationListener` is written as an entirely ordinary Spring event listener — it has no awareness that the event it's handling originated on a *different* instance, arrived via a message broker, and was serialized/deserialized along the way. That transparency, letting ordinary local event-listener code react correctly to fleet-wide broadcasts, is the specific value Spring Cloud Bus adds on top of the raw messaging infrastructure it shares with Spring Cloud Stream.

## 7. Gotchas & takeaways

> **Gotcha:** a custom `RemoteApplicationEvent` subclass, like any object destined to be serialized and sent over a broker, must have a no-argument constructor available for deserialization (as shown in `CacheInvalidateRemoteEvent`'s `public CacheInvalidateRemoteEvent() {}`) — omitting it causes deserialization failures on receiving instances that can be confusing to diagnose, since the failure surfaces on the *receiving* side, potentially far from wherever the event was originally published.

- Spring Cloud Bus fills a distinct ecosystem niche — broadcast-to-every-instance — separate from Spring Cloud Stream's more typical point-to-point or consumer-group message processing, even though both reuse the same underlying broker infrastructure.
- Configuration refresh is Bus's most common built-in use, but the mechanism generalizes to any custom `RemoteApplicationEvent` subclass — cache invalidation and maintenance-mode toggles are two other natural fits.
- A custom broadcast event, once defined by extending `RemoteApplicationEvent`, can be handled with entirely ordinary `@EventListener` methods on every receiving instance — no Bus-specific subscription code is needed on the consuming side.
- Choose deliberately between Bus's broadcast-to-all shape and Stream's typical deliver-to-one/consumer-group shape based on whether the coordination need is genuinely "every instance must react" or "exactly one instance should process this" — conflating the two produces either duplicated work or silently-missed instances.
