---
card: microservices
gi: 155
slug: spring-cloud-bus-for-broadcasting-events-across-instances
title: "Spring Cloud Bus for broadcasting events across instances"
---

## 1. What it is

Spring Cloud Bus links every instance of a service (or multiple different services) to a shared message broker and gives them a simple way to broadcast lightweight application events to every other connected instance simultaneously — most commonly used to propagate a "configuration changed, please refresh" signal to an entire fleet of running instances at once, without needing to know or track how many instances exist or where they are.

## 2. Why & when

Without a bus, notifying every running instance of a service about a fleet-wide event — a configuration change, a cache-invalidation signal, a feature flag flip — means either polling (each instance repeatedly checking "has anything changed?", wasteful and laggy) or an operator manually hitting each instance's individual management endpoint one at a time, which doesn't scale past a handful of instances and is easy to miss one. Spring Cloud Bus solves this by giving every instance a shared broadcast channel: publishing one event reaches every currently-connected instance, regardless of how many there are or how they're deployed, with no per-instance addressing needed.

Reach for Spring Cloud Bus specifically for fleet-wide broadcast signals meant for *every* instance simultaneously — the classic case is Spring Cloud Config's `/actuator/busrefresh` endpoint, which uses the bus to tell every instance of every subscribed service to reload its configuration after a central config change. It is not a general-purpose replacement for [point-to-point](0113-point-to-point-queue-messaging.md) work queues or [pub/sub](0114-publish-subscribe-topic-messaging.md) business event streams — those remain the right tool for routing individual units of work or domain events between different services.

## 3. Core concept

Every instance subscribes to a shared bus topic on startup; publishing an event to the bus (typically triggered via a management endpoint call to any single instance) causes that event to be broadcast to every subscribed instance, each of which reacts independently, with no instance needing to know how many peers exist.

```java
// triggering a bus event (conceptually -- normally done via POST /actuator/busrefresh)
applicationEventPublisher.publishEvent(new RefreshRemoteApplicationEvent(this, "config-service", "*"));

// EVERY instance subscribed to the bus receives this, independently, and reacts:
@EventListener
public void onRefresh(RefreshRemoteApplicationEvent event) {
    contextRefresher.refresh(); // reloads this instance's configuration
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One instance's refresh event is published to the shared Spring Cloud Bus topic; every subscribed instance across the fleet, regardless of count, receives and reacts to that same event independently" >
  <rect x="20" y="80" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="104" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">instance-1 (trigger)</text>

  <rect x="220" y="70" width="200" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Cloud Bus</text>
  <text x="320" y="112" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">shared broadcast topic</text>

  <rect x="490" y="20" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance-2</text>
  <rect x="490" y="75" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance-3</text>
  <rect x="490" y="130" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="152" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance-N</text>

  <line x1="150" y1="100" x2="218" y2="100" stroke="#8b949e" marker-end="url(#arr36)"/>
  <line x1="420" y1="90" x2="488" y2="38" stroke="#8b949e" marker-end="url(#arr36)"/>
  <line x1="420" y1="100" x2="488" y2="92" stroke="#8b949e" marker-end="url(#arr36)"/>
  <line x1="420" y1="110" x2="488" y2="147" stroke="#8b949e" marker-end="url(#arr36)"/>

  <defs>
    <marker id="arr36" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

One event, broadcast to every instance simultaneously, regardless of how many instances are running.

## 5. Runnable example

Scenario: a fleet configuration-refresh scenario that starts with manual, per-instance notification (showing why it doesn't scale), moves to a simulated shared bus broadcasting one event to every subscribed instance, and finally demonstrates the bus correctly handling instances joining and leaving dynamically — a new instance automatically receives future broadcasts without any manual registration step by an operator.

### Level 1 — Basic

```java
// File: ManualPerInstanceNotification.java -- an operator (or script) must notify
// EACH instance individually; easy to miss one, doesn't scale past a few instances.
import java.util.*;

public class ManualPerInstanceNotification {
    static class ServiceInstance {
        String id;
        boolean configRefreshed = false;
        ServiceInstance(String id) { this.id = id; }
        void refreshConfig() { configRefreshed = true; System.out.println("[" + id + "] config refreshed"); }
    }

    public static void main(String[] args) {
        List<ServiceInstance> fleet = List.of(new ServiceInstance("instance-1"), new ServiceInstance("instance-2"), new ServiceInstance("instance-3"));

        // an operator must call refreshConfig() on EACH instance BY NAME, one at a time
        fleet.get(0).refreshConfig();
        fleet.get(1).refreshConfig();
        // ...and accidentally forgets instance-3!

        for (ServiceInstance instance : fleet) {
            System.out.println(instance.id + " refreshed: " + instance.configRefreshed);
        }
        System.out.println("instance-3 was MISSED -- now running with STALE configuration, silently.");
    }
}
```

**How to run:** `javac ManualPerInstanceNotification.java && java ManualPerInstanceNotification` (JDK 17+).

Expected output:
```
[instance-1] config refreshed
[instance-2] config refreshed
instance-1 refreshed: true
instance-2 refreshed: true
instance-3 refreshed: false
instance-3 was MISSED -- now running with STALE configuration, silently.
```

### Level 2 — Intermediate

```java
// File: SharedBusBroadcast.java -- ONE publish reaches EVERY subscribed instance,
// with no per-instance addressing or risk of accidentally missing one.
import java.util.*;
import java.util.function.*;

public class SharedBusBroadcast {
    static class ServiceInstance {
        String id;
        boolean configRefreshed = false;
        ServiceInstance(String id) { this.id = id; }
        void onBusEvent(String eventType) {
            if (eventType.equals("refresh")) {
                configRefreshed = true;
                System.out.println("[" + id + "] received bus event, config refreshed");
            }
        }
    }

    static class SpringCloudBus {
        List<ServiceInstance> subscribedInstances = new ArrayList<>();
        void subscribe(ServiceInstance instance) { subscribedInstances.add(instance); }
        void publish(String eventType) {
            System.out.println("[bus] broadcasting '" + eventType + "' to " + subscribedInstances.size() + " subscribed instance(s)");
            subscribedInstances.forEach(instance -> instance.onBusEvent(eventType)); // ALL instances, automatically, no addressing needed
        }
    }

    public static void main(String[] args) {
        SpringCloudBus bus = new SpringCloudBus();
        bus.subscribe(new ServiceInstance("instance-1"));
        bus.subscribe(new ServiceInstance("instance-2"));
        bus.subscribe(new ServiceInstance("instance-3"));

        bus.publish("refresh"); // ONE call -- no way to accidentally miss an instance

        System.out.println("All " + bus.subscribedInstances.size() + " instances refreshed: " +
            bus.subscribedInstances.stream().allMatch(i -> i.configRefreshed));
    }
}
```

**How to run:** `javac SharedBusBroadcast.java && java SharedBusBroadcast` (JDK 17+).

Expected output:
```
[bus] broadcasting 'refresh' to 3 subscribed instance(s)
[instance-1] received bus event, config refreshed
[instance-2] received bus event, config refreshed
[instance-3] received bus event, config refreshed
All 3 instances refreshed: true
```

### Level 3 — Advanced

```java
// File: DynamicInstanceMembership.java -- an instance joins the fleet AFTER an
// earlier broadcast; it automatically receives FUTURE broadcasts, and an instance
// that leaves stops receiving them, with NO manual registration bookkeeping needed.
import java.util.*;

public class DynamicInstanceMembership {
    static class ServiceInstance {
        String id;
        List<String> receivedEvents = new ArrayList<>();
        ServiceInstance(String id) { this.id = id; }
        void onBusEvent(String eventType) { receivedEvents.add(eventType); System.out.println("[" + id + "] received: " + eventType); }
    }

    static class SpringCloudBus {
        List<ServiceInstance> subscribedInstances = new ArrayList<>();
        void subscribe(ServiceInstance instance) {
            subscribedInstances.add(instance);
            System.out.println("[bus] " + instance.id + " subscribed -- will receive ALL FUTURE broadcasts automatically");
        }
        void unsubscribe(ServiceInstance instance) {
            subscribedInstances.remove(instance);
            System.out.println("[bus] " + instance.id + " unsubscribed (e.g. scaled down / shut down)");
        }
        void publish(String eventType) {
            System.out.println("[bus] broadcasting '" + eventType + "' to " + subscribedInstances.size() + " CURRENTLY subscribed instance(s)");
            subscribedInstances.forEach(instance -> instance.onBusEvent(eventType));
        }
    }

    public static void main(String[] args) {
        SpringCloudBus bus = new SpringCloudBus();
        ServiceInstance instance1 = new ServiceInstance("instance-1");
        ServiceInstance instance2 = new ServiceInstance("instance-2");
        bus.subscribe(instance1);
        bus.subscribe(instance2);

        bus.publish("refresh"); // both instance-1 and instance-2 receive this

        // FLEET SCALES UP: instance-3 joins AFTER the first broadcast, with NO manual registration effort
        ServiceInstance instance3 = new ServiceInstance("instance-3");
        bus.subscribe(instance3);

        // FLEET SCALES DOWN: instance-1 leaves
        bus.unsubscribe(instance1);

        bus.publish("refresh"); // now reaches instance-2 and instance-3 -- NOT instance-1

        System.out.println("instance-1 events: " + instance1.receivedEvents + " (only the FIRST broadcast -- missed the second, correctly, since it left)");
        System.out.println("instance-2 events: " + instance2.receivedEvents + " (BOTH broadcasts)");
        System.out.println("instance-3 events: " + instance3.receivedEvents + " (only the SECOND -- correctly missed the first, which happened before it joined)");
    }
}
```

**How to run:** `javac DynamicInstanceMembership.java && java DynamicInstanceMembership` (JDK 17+).

Expected output:
```
[bus] instance-1 subscribed -- will receive ALL FUTURE broadcasts automatically
[bus] instance-2 subscribed -- will receive ALL FUTURE broadcasts automatically
[bus] broadcasting 'refresh' to 2 CURRENTLY subscribed instance(s)
[instance-1] received: refresh
[instance-2] received: refresh
[bus] instance-3 subscribed -- will receive ALL FUTURE broadcasts automatically
[bus] instance-1 unsubscribed (e.g. scaled down / shut down)
[bus] broadcasting 'refresh' to 2 CURRENTLY subscribed instance(s)
[instance-2] received: refresh
[instance-3] received: refresh
instance-1 events: [refresh] (only the FIRST broadcast -- missed the second, correctly, since it left)
instance-2 events: [refresh, refresh] (BOTH broadcasts)
instance-3 events: [refresh] (only the SECOND -- correctly missed the first, which happened before it joined)
```

## 6. Walkthrough

1. **Level 1** — `fleet.get(0).refreshConfig()` and `fleet.get(1).refreshConfig()` are called explicitly, by name, while `fleet.get(2)` is simply never called at all — this is a realistic operator mistake, not a contrived edge case, and it leaves `instance-3` silently running stale configuration.
2. **Level 2, subscription as the only setup step** — each `ServiceInstance` calls `bus.subscribe(instance)` once, at startup (mirroring how a real Spring Cloud Bus-connected application automatically joins the shared topic on boot); after that, no per-instance addressing is ever needed again.
3. **Level 2, the broadcast mechanism** — `SpringCloudBus.publish` iterates `subscribedInstances` and calls `onBusEvent` on every single one, with no possibility of skipping an entry the way Level 1's manual, name-by-name calls could.
4. **Level 2, the guarantee made verifiable** — `bus.subscribedInstances.stream().allMatch(i -> i.configRefreshed)` checks and confirms every subscribed instance was reached by the single `publish` call, directly contrasting with Level 1's `instance-3 refreshed: false`.
5. **Level 3, joining after an earlier broadcast** — `instance3` is created and subscribed *after* the first `bus.publish("refresh")` call has already completed; because it wasn't in `subscribedInstances` at that time, it correctly has no record of that first event.
6. **Level 3, leaving before a later broadcast** — `bus.unsubscribe(instance1)` removes `instance1` from `subscribedInstances` before the second `publish` call; that second call's loop, iterating the now-updated list, simply never reaches `instance1` at all.
7. **Level 3, the three instances' differing histories explained** — `instance1.receivedEvents` contains exactly one entry (present for the first broadcast, gone before the second); `instance2.receivedEvents` contains two entries (present for both, having never unsubscribed); `instance3.receivedEvents` contains exactly one entry (absent for the first, present for the second) — each instance's event history is a direct, correct consequence of exactly when it was subscribed and unsubscribed, with the bus itself requiring no special-casing to handle this dynamic membership correctly.

## 7. Gotchas & takeaways

> **Gotcha:** Spring Cloud Bus events are fire-and-forget broadcasts with no delivery guarantee to instances that are temporarily disconnected at broadcast time — an instance that's mid-restart or briefly network-partitioned when a refresh event fires will simply miss it and continue running with stale state until the next broadcast or its own next restart; this is a meaningfully weaker guarantee than a durable, [replayable](0136-replayability-of-event-streams.md) event log would provide, and is an accepted trade-off for the bus's simplicity.

- Spring Cloud Bus links every instance of a service to a shared broadcast topic, letting one published event reach every currently-connected instance without per-instance addressing.
- The classic use case is fleet-wide configuration refresh, most commonly triggered via Spring Cloud Config's `/actuator/busrefresh` endpoint reaching every subscribed instance across a fleet.
- Instances joining after a broadcast correctly miss it; instances unsubscribing before a broadcast correctly stop receiving future ones — dynamic fleet membership is handled naturally by simple subscribe/unsubscribe, with no manual bookkeeping.
- This is not a general-purpose replacement for point-to-point work queues or pub/sub business event streams — it's specifically suited to lightweight, fleet-wide broadcast signals.
- Bus events are fire-and-forget with no durability guarantee for temporarily disconnected instances, a real trade-off accepted for the mechanism's simplicity.
