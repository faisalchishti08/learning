---
card: spring-cloud
gi: 27
slug: spring-cloud-bus-for-broadcast-refresh
title: "Spring Cloud Bus for broadcast refresh"
---

## 1. What it is

Spring Cloud Bus connects every instance of every service to a shared message broker (RabbitMQ or Kafka), letting one triggered event — most commonly `POST /actuator/busrefresh` on any single instance, or a Config Server webhook — broadcast to every connected instance across the entire fleet, rather than requiring `/actuator/refresh` to be called individually on each one.

```
POST /actuator/busrefresh   (called on ANY ONE instance, or triggered by a Config Server webhook)
  -> publishes a RefreshRemoteApplicationEvent onto the shared message bus
  -> EVERY instance subscribed to the bus receives it
  -> EVERY instance independently performs its own local refresh, simultaneously
```

## 2. Why & when

The previous card ended on exactly this gap: refresh is per-instance, and with dozens or hundreds of running instances across a fleet, manually calling `/actuator/refresh` on each one individually doesn't scale, and risks leaving some instances out of sync with the rest for an extended, unpredictable window. Spring Cloud Bus closes that gap by turning "refresh this one instance" into "refresh every instance in the fleet," using a message broker every instance is already connected to as the broadcast mechanism.

Reach for Spring Cloud Bus when:

- A fleet has more than a handful of instances of the same service (or even multiple different services) that all need to refresh together, consistently, in response to one configuration change.
- You want a Config Server webhook (triggered automatically by a Git push, say) to propagate a change to every running instance without a separate script individually calling `/actuator/refresh` on each one.
- Consistency across the fleet matters — every instance genuinely should be running with the same effective configuration at (approximately) the same time, not drifting apart based on which ones happened to be manually refreshed.

## 3. Core concept

```
 Without Spring Cloud Bus:
   operator calls /actuator/refresh on instance-1, then instance-2, then instance-3, ... (N calls, N chances to miss one)

 With Spring Cloud Bus:
   operator (or a webhook) calls /actuator/busrefresh on ANY ONE instance
     -> event published to the shared message bus (RabbitMQ/Kafka)
     -> instance-1, instance-2, instance-3, ... ALL receive it via their bus subscription
     -> ALL refresh independently, at roughly the same time, with ONE triggering call
```

One call triggers a fan-out broadcast across every connected instance, instead of requiring one call per instance.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single busrefresh call publishes an event to a shared message bus which every connected instance receives and acts on independently">
  <rect x="250" y="20" width="140" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">/actuator/busrefresh</text>

  <line x1="320" y1="60" x2="320" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a47)"/>

  <rect x="220" y="95" width="200" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="120" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">message bus (RabbitMQ/Kafka)</text>

  <line x1="270" y1="135" x2="130" y2="165" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a47)"/>
  <line x1="320" y1="135" x2="320" y2="165" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a47)"/>
  <line x1="370" y1="135" x2="510" y2="165" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a47)"/>

  <rect x="60" y="170" width="140" height="20" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="130" y="184" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">instance-1</text>
  <rect x="250" y="170" width="140" height="20" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="184" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">instance-2</text>
  <rect x="440" y="170" width="140" height="20" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="510" y="184" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">instance-3</text>

  <defs><marker id="a47" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A single triggering call fans out through the message bus to every connected instance simultaneously.

## 5. Runnable example

The scenario: refreshing a three-instance fleet, evolving from the manual per-instance approach that risks missing an instance, to a bus-style broadcast mechanism refreshing every subscribed instance from one trigger, to a scoped broadcast targeting only instances of one specific service — since a real fleet often runs multiple different services sharing the same bus.

### Level 1 — Basic

Show the manual, per-instance approach and its risk: a forgotten instance.

```java
import java.util.*;

public class SpringCloudBusLevel1 {
    public static void main(String[] args) {
        List<ServiceInstance> fleet = List.of(
            new ServiceInstance("instance-1", "50"),
            new ServiceInstance("instance-2", "50"),
            new ServiceInstance("instance-3", "50")
        );

        // Operator manually refreshes each instance -- but FORGETS instance-3.
        fleet.get(0).refresh("100");
        fleet.get(1).refresh("100");
        // fleet.get(2) never refreshed -- an easy mistake at scale

        for (ServiceInstance instance : fleet) {
            System.out.println(instance.name + ": db.pool.size=" + instance.currentPoolSize);
        }
    }
}

class ServiceInstance {
    String name; String currentPoolSize;
    ServiceInstance(String name, String currentPoolSize) { this.name = name; this.currentPoolSize = currentPoolSize; }
    void refresh(String newValue) { this.currentPoolSize = newValue; }
}
```

How to run: `java SpringCloudBusLevel1.java`

`instance-3` is silently missed — with three instances this typo-of-omission is obvious in the code, but at real fleet scale (tens or hundreds of instances), manually tracking which ones have actually been refreshed becomes genuinely error-prone.

### Level 2 — Intermediate

Add a `MessageBus` that broadcasts one refresh event to every subscribed instance, removing the per-instance manual step entirely.

```java
import java.util.*;

public class SpringCloudBusLevel2 {
    public static void main(String[] args) {
        MessageBus bus = new MessageBus();
        List<ServiceInstance> fleet = List.of(
            new ServiceInstance("instance-1", "50", bus),
            new ServiceInstance("instance-2", "50", bus),
            new ServiceInstance("instance-3", "50", bus)
        );

        // ONE call, on ANY instance -- or triggered externally -- reaches EVERY subscribed instance.
        bus.publish("db.pool.size", "100");

        for (ServiceInstance instance : fleet) {
            System.out.println(instance.name + ": db.pool.size=" + instance.currentPoolSize);
        }
    }
}

// Stands in for the shared RabbitMQ/Kafka-backed bus Spring Cloud Bus uses.
class MessageBus {
    private final List<ServiceInstance> subscribers = new ArrayList<>();
    void subscribe(ServiceInstance instance) { subscribers.add(instance); }
    void publish(String key, String value) {
        for (ServiceInstance instance : subscribers) instance.onBusEvent(key, value); // fan-out to ALL subscribers
    }
}

class ServiceInstance {
    String name; String currentPoolSize;
    ServiceInstance(String name, String currentPoolSize, MessageBus bus) {
        this.name = name; this.currentPoolSize = currentPoolSize;
        bus.subscribe(this); // every instance subscribes to the SAME shared bus on startup
    }
    void onBusEvent(String key, String value) {
        if (key.equals("db.pool.size")) this.currentPoolSize = value; // each instance refreshes ITSELF independently
    }
}
```

How to run: `java SpringCloudBusLevel2.java`

`bus.publish(...)` is called exactly once, and every `ServiceInstance` that subscribed to `bus` at construction time receives `onBusEvent` and updates itself — no per-instance manual step, and no possibility of forgetting one, since subscription (not a manually-tracked list of refresh calls) determines who receives the event.

### Level 3 — Advanced

Add service-scoped broadcasting: multiple *different* services sharing the same bus, with a refresh event scoped to only one service's instances — since a real message bus in production typically carries traffic for an entire organization's services, not just one.

```java
import java.util.*;

public class SpringCloudBusLevel3 {
    public static void main(String[] args) {
        MessageBus bus = new MessageBus();
        List<ServiceInstance> paymentInstances = List.of(
            new ServiceInstance("payment-service", "instance-1", "50", bus),
            new ServiceInstance("payment-service", "instance-2", "50", bus)
        );
        List<ServiceInstance> inventoryInstances = List.of(
            new ServiceInstance("inventory-service", "instance-1", "20", bus)
        );

        // Refresh ONLY payment-service instances -- inventory-service is untouched.
        bus.publish("payment-service", "db.pool.size", "100");

        System.out.println("--- payment-service (should be refreshed) ---");
        for (ServiceInstance i : paymentInstances) System.out.println(i.instanceId + ": db.pool.size=" + i.currentPoolSize);

        System.out.println("--- inventory-service (should be UNCHANGED) ---");
        for (ServiceInstance i : inventoryInstances) System.out.println(i.instanceId + ": db.pool.size=" + i.currentPoolSize);
    }
}

class MessageBus {
    private final List<ServiceInstance> subscribers = new ArrayList<>();
    void subscribe(ServiceInstance instance) { subscribers.add(instance); }
    // Scoped broadcast: only subscribers matching the target service receive the event.
    void publish(String targetService, String key, String value) {
        for (ServiceInstance instance : subscribers) {
            if (instance.serviceId.equals(targetService)) instance.onBusEvent(key, value);
        }
    }
}

class ServiceInstance {
    String serviceId, instanceId, currentPoolSize;
    ServiceInstance(String serviceId, String instanceId, String currentPoolSize, MessageBus bus) {
        this.serviceId = serviceId; this.instanceId = instanceId; this.currentPoolSize = currentPoolSize;
        bus.subscribe(this);
    }
    void onBusEvent(String key, String value) {
        if (key.equals("db.pool.size")) this.currentPoolSize = value;
    }
}
```

How to run: `java SpringCloudBusLevel3.java`

`bus.publish("payment-service", "db.pool.size", "100")` iterates every subscriber but only calls `onBusEvent` for those whose `serviceId` matches `"payment-service"` — both `payment-service` instances update, while the `inventory-service` instance, sharing the same bus but a different service identity, is correctly left untouched, mirroring how Spring Cloud Bus's `busrefresh` supports a `destination` parameter to scope a broadcast to a specific service (and optionally, specific instances of it) rather than always refreshing the entire connected fleet.

## 6. Walkthrough

Execution starts in `main` for Level 3. Two `payment-service` instances and one `inventory-service` instance are constructed, each subscribing itself to the shared `bus` at construction time. `bus.publish("payment-service", "db.pool.size", "100")` is called once.

Inside `publish`, the loop checks every subscriber's `serviceId` — for the two `payment-service` instances, `instance.serviceId.equals("payment-service")` is `true`, so `onBusEvent` runs and updates `currentPoolSize`; for the `inventory-service` instance, the check is `false`, so `onBusEvent` is never called for it at all:

```
--- payment-service (should be refreshed) ---
instance-1: db.pool.size=100
instance-2: db.pool.size=100
--- inventory-service (should be UNCHANGED) ---
instance-1: db.pool.size=20
```

In a real deployment, this is exactly the payoff of pairing Spring Cloud Config with Spring Cloud Bus and a Config Server Git webhook: a developer merges a configuration change, the webhook fires `POST /actuator/busrefresh` (optionally scoped via a `destination` parameter to just the affected service) against any single reachable instance, that event propagates through RabbitMQ or Kafka to every instance of that service across the entire fleet, and each one independently performs its own local `@RefreshScope` recreation — the entire fleet converges on the new configuration within moments, from one webhook call, with no operator manually touching individual instances at all.

## 7. Gotchas & takeaways

> Gotcha: Spring Cloud Bus requires every participating instance to be connected to the same message broker and correctly configured to listen for bus events — an instance that's disconnected from the broker (a network partition, a misconfiguration) silently misses the broadcast entirely, with no error surfaced to the operator who triggered the refresh, unlike the very visible, per-call failure of manually calling `/actuator/refresh` against an unreachable instance directly.

> Gotcha: broadcasting a refresh event doesn't guarantee all instances apply it at exactly the same instant — message delivery, however fast, still has some latency and ordering variance, so there's a real (typically brief) window where different instances of the same service are running with different effective configuration during the propagation, which matters for anything requiring strict consistency across the fleet at every single moment.

- Spring Cloud Bus broadcasts a refresh event across an entire fleet of instances via a shared message broker (RabbitMQ/Kafka), replacing the need to manually call `/actuator/refresh` on every instance individually.
- One triggering call — often from a Config Server Git webhook — fans out to every connected instance, closing the "refresh is per-instance and doesn't scale" gap from the previous card.
- Broadcasts can be scoped to a specific service (or specific instances) using a destination parameter, since a real production bus typically carries traffic for many different services simultaneously.
- Broadcast delivery isn't instantaneous or guaranteed against every possible connectivity failure — there's a real propagation window, and a disconnected instance can silently miss an event with no visible error to the operator.
