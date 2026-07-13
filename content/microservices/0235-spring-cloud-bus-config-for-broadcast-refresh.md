---
card: microservices
gi: 235
slug: spring-cloud-bus-config-for-broadcast-refresh
title: "Spring Cloud Bus + Config for broadcast refresh"
---

## 1. What it is

Spring Cloud Bus links a message broker (Kafka, RabbitMQ) into a group of Spring Boot services so that a single event — like a configuration refresh request — can be broadcast to *every* running instance of *every* affected service simultaneously, instead of requiring `/actuator/refresh` to be called individually, instance by instance, across a fleet that might have dozens of replicas.

## 2. Why & when

[`@RefreshScope`](0234-refreshscope-for-runtime-refresh.md) gives a single application instance the ability to refresh its beans on demand, but calling `/actuator/refresh` on one instance only refreshes *that* instance — a service running twenty replicas behind a load balancer would need that endpoint called twenty separate times, against twenty separate addresses, to bring every replica in sync, and missing even one leaves it running stale configuration. Spring Cloud Bus solves this by having every instance subscribe to a shared broker topic; triggering a refresh on *any one* instance (or via a dedicated endpoint like `/actuator/busrefresh`) publishes an event to that topic, and every subscribed instance across every replica and every affected service receives it and refreshes itself independently.

Adopt Spring Cloud Bus whenever a system runs more than a single instance per service (which is nearly all production deployments) and needs configuration refresh to reach every replica reliably, without a manual per-instance operation or custom broadcast logic. A single-instance deployment gets no benefit from broadcast — `@RefreshScope` alone is sufficient there.

## 3. Core concept

Spring Cloud Bus publishes a `RefreshRemoteApplicationEvent` (or similar) to a shared broker topic when triggered, and every instance connected to that topic — regardless of which physical machine or replica it is — receives the event and triggers its own local `@RefreshScope` refresh in response, achieving fleet-wide consistency through the broker's own fan-out delivery rather than any direct, point-to-point calling between instances.

```java
// triggering a refresh on ANY ONE instance...
// POST http://any-instance:8080/actuator/busrefresh

// ...publishes an event to the SHARED broker topic ("springCloudBus")
// EVERY instance subscribed to that topic -- across ALL replicas of ALL affected services -- receives it:
interface BusEventListener { void onRefreshEvent(); }
class ServiceInstance implements BusEventListener {
    public void onRefreshEvent() { /* triggers this instance's OWN local @RefreshScope refresh */ }
}
// no instance directly calls another -- the BROKER handles fan-out delivery to everyone subscribed
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A refresh trigger publishes one event to a shared message broker topic, and every subscribed service instance -- across multiple replicas -- receives that same event and refreshes itself independently, without any direct instance-to-instance calling" >
  <rect x="20" y="70" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="94" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">/actuator/busrefresh</text>

  <rect x="230" y="55" width="180" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="80" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Message broker</text>
  <text x="320" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">"springCloudBus" topic</text>
  <text x="320" y="112" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fan-out to ALL subscribers</text>

  <rect x="480" y="20" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="42" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Instance A</text>

  <rect x="480" y="65" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="87" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Instance B</text>

  <rect x="480" y="110" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="132" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Instance C</text>

  <line x1="150" y1="90" x2="228" y2="90" stroke="#8b949e" marker-end="url(#arr235)"/>
  <line x1="410" y1="80" x2="478" y2="38" stroke="#8b949e" marker-end="url(#arr235)"/>
  <line x1="410" y1="90" x2="478" y2="83" stroke="#8b949e" marker-end="url(#arr235)"/>
  <line x1="410" y1="100" x2="478" y2="128" stroke="#8b949e" marker-end="url(#arr235)"/>

  <defs>
    <marker id="arr235" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

One trigger, one broker publish, and every subscribed instance — however many replicas exist — refreshes independently.

## 5. Runnable example

Scenario: a fleet-refresh operation that starts requiring each instance to be refreshed individually (manual, error-prone at scale), refactors to a simulated broker-based broadcast where one publish reaches every subscriber, and finally demonstrates the operation succeeding even when new instances join dynamically between publishes — mirroring how a genuinely elastic fleet of replicas stays in sync without a static, hand-maintained list of instances to refresh.

### Level 1 — Basic

```java
// File: ManualPerInstanceRefresh.java -- refreshing a fleet means calling
// EACH instance's endpoint individually -- easy to miss one, and doesn't
// scale as replica count grows.
import java.util.*;

public class ManualPerInstanceRefresh {
    static class ServiceInstance {
        String id; int maxAttempts = 3;
        ServiceInstance(String id) { this.id = id; }
        void refresh(int newValue) { this.maxAttempts = newValue; } // must be called on EACH instance, one by one
    }

    public static void main(String[] args) {
        List<ServiceInstance> fleet = List.of(new ServiceInstance("instance-A"), new ServiceInstance("instance-B"), new ServiceInstance("instance-C"));

        // an operator calls refresh on instance-A and instance-B... but FORGETS instance-C
        fleet.get(0).refresh(7);
        fleet.get(1).refresh(7);
        // fleet.get(2).refresh(7); -- MISSED

        for (ServiceInstance s : fleet) System.out.println(s.id + " maxAttempts = " + s.maxAttempts);
        System.out.println("instance-C is now INCONSISTENT with the rest of the fleet -- easy to miss manually.");
    }
}
```

**How to run:** `javac ManualPerInstanceRefresh.java && java ManualPerInstanceRefresh` (JDK 17+).

### Level 2 — Intermediate

```java
// File: BrokerBroadcastRefresh.java -- ONE publish to a simulated shared
// broker topic reaches EVERY subscribed instance -- no per-instance calls,
// no chance of missing one.
import java.util.*;

public class BrokerBroadcastRefresh {
    interface BusEventListener { void onRefreshEvent(int newValue); }

    static class ServiceInstance implements BusEventListener {
        String id; int maxAttempts = 3;
        ServiceInstance(String id) { this.id = id; }
        public void onRefreshEvent(int newValue) { this.maxAttempts = newValue; } // triggered by the BROKER, not a direct call
    }

    static class MessageBroker {
        List<BusEventListener> subscribers = new ArrayList<>();
        void subscribe(BusEventListener listener) { subscribers.add(listener); }
        void publish(int newValue) { for (BusEventListener s : subscribers) s.onRefreshEvent(newValue); } // fan-out to ALL
    }

    public static void main(String[] args) {
        MessageBroker broker = new MessageBroker();
        List<ServiceInstance> fleet = List.of(new ServiceInstance("instance-A"), new ServiceInstance("instance-B"), new ServiceInstance("instance-C"));
        fleet.forEach(broker::subscribe); // EVERY instance subscribes to the SAME topic

        broker.publish(7); // ONE publish -- mirrors POST /actuator/busrefresh on ANY one instance

        for (ServiceInstance s : fleet) System.out.println(s.id + " maxAttempts = " + s.maxAttempts);
        System.out.println("ALL THREE instances refreshed from ONE publish -- none missed.");
    }
}
```

**How to run:** `javac BrokerBroadcastRefresh.java && java BrokerBroadcastRefresh` (JDK 17+).

Expected output:
```
instance-A maxAttempts = 7
instance-B maxAttempts = 7
instance-C maxAttempts = 7
ALL THREE instances refreshed from ONE publish -- none missed.
```

### Level 3 — Advanced

```java
// File: DynamicFleetMembershipHandledCorrectly.java -- NEW instances
// joining the fleet AFTER a publish naturally start with CURRENT config
// (from their own startup), and only need to subscribe to receive
// FUTURE broadcasts -- no static, hand-maintained instance list required.
import java.util.*;

public class DynamicFleetMembershipHandledCorrectly {
    interface BusEventListener { void onRefreshEvent(int newValue); }

    static class ServiceInstance implements BusEventListener {
        String id; int maxAttempts;
        ServiceInstance(String id, int startupConfigValue) { this.id = id; this.maxAttempts = startupConfigValue; } // reads CURRENT config at startup
        public void onRefreshEvent(int newValue) { this.maxAttempts = newValue; }
    }

    static class MessageBroker {
        List<BusEventListener> subscribers = new ArrayList<>();
        void subscribe(BusEventListener listener) { subscribers.add(listener); }
        void publish(int newValue) { for (BusEventListener s : subscribers) s.onRefreshEvent(newValue); }
    }

    static int currentConfigValue = 3; // the "config source" -- reflects the LATEST published value

    public static void main(String[] args) {
        MessageBroker broker = new MessageBroker();

        ServiceInstance a = new ServiceInstance("instance-A", currentConfigValue);
        ServiceInstance b = new ServiceInstance("instance-B", currentConfigValue);
        broker.subscribe(a); broker.subscribe(b);

        currentConfigValue = 7;
        broker.publish(currentConfigValue); // A and B refresh to 7

        // a THIRD instance joins the fleet AFTER the publish -- e.g. auto-scaling adds a replica
        ServiceInstance c = new ServiceInstance("instance-C", currentConfigValue); // starts UP-TO-DATE already, reading current config directly
        broker.subscribe(c); // subscribes for FUTURE broadcasts -- no need to replay past ones

        for (ServiceInstance s : List.of(a, b, c)) System.out.println(s.id + " maxAttempts = " + s.maxAttempts);

        currentConfigValue = 10;
        broker.publish(currentConfigValue); // a SECOND publish -- reaches ALL THREE, including the newly joined instance-C
        System.out.println("\nAfter a second publish (all three now subscribed):");
        for (ServiceInstance s : List.of(a, b, c)) System.out.println(s.id + " maxAttempts = " + s.maxAttempts);
    }
}
```

**How to run:** `javac DynamicFleetMembershipHandledCorrectly.java && java DynamicFleetMembershipHandledCorrectly` (JDK 17+).

Expected output:
```
instance-A maxAttempts = 7
instance-B maxAttempts = 7
instance-C maxAttempts = 7

After a second publish (all three now subscribed):
instance-A maxAttempts = 10
instance-B maxAttempts = 10
instance-C maxAttempts = 10
```

## 6. Walkthrough

1. **Level 1, the missed-instance risk** — `refresh` is called explicitly on `fleet.get(0)` and `fleet.get(1)` but the call for `fleet.get(2)` is commented out, standing in for an operator's real, easy-to-make mistake of forgetting one instance among many; the printed output confirms `instance-C` remains at its stale value while the other two are updated, an inconsistency invisible until something depending on that stale value misbehaves.
2. **Level 2, the shared topic abstraction** — `MessageBroker.subscribers` holds every instance that has subscribed, and `publish` iterates that entire list, calling `onRefreshEvent` on each one; no code anywhere names a specific instance to refresh — `broker.publish(7)` doesn't know or care how many subscribers exist.
3. **Level 2, the guarantee this provides** — all three instances end up with `maxAttempts = 7` after a single `broker.publish(7)` call, structurally eliminating the "forgot one" failure mode from Level 1, since the broadcast mechanism itself, not an operator's memory, determines which instances get refreshed.
4. **Level 3, a new instance joining mid-fleet-lifecycle** — `instance-C` is constructed *after* the first `broker.publish(7)` call, using `currentConfigValue` (which is `7` by that point) directly as its startup value, mirroring how a real newly started service instance fetches current configuration during its own startup (via [Config Client](0232-spring-cloud-config-client.md)) rather than needing to "catch up" via a replayed bus event.
5. **Level 3, subscribing for future events only** — `broker.subscribe(c)` registers `instance-C` to receive events from this point forward; there's no mechanism (or need) for it to receive the *earlier* `publish(7)` event again, since its own startup already reflected that value.
6. **Level 3, the second publish reaching everyone** — `broker.publish(10)` after `instance-C` has subscribed correctly updates all three instances' `maxAttempts` to `10`, confirming that dynamically joining the fleet and subscribing to the broker's topic is sufficient for a new instance to participate correctly in all *future* broadcasts — exactly the property that makes Spring Cloud Bus work correctly for an elastic, auto-scaling fleet where the exact set of running instances is constantly changing and never needs to be tracked by hand.

## 7. Gotchas & takeaways

> **Gotcha:** Spring Cloud Bus requires a message broker (Kafka or RabbitMQ) as additional infrastructure, and a broker outage means broadcast refresh stops working fleet-wide — even though individual instances can still be refreshed manually via their own local `/actuator/refresh` endpoint as a fallback; broadcast refresh is a convenience and consistency mechanism layered on top of `@RefreshScope`, not a replacement for it, and understanding the manual fallback path matters for operating during a broker outage.

- Spring Cloud Bus broadcasts a refresh event to every subscribed service instance via a shared message broker topic, solving the "refresh every replica" problem that calling `/actuator/refresh` on a single instance doesn't address.
- The broker handles fan-out delivery; no instance directly calls any other instance, and the triggering side doesn't need to know how many instances exist or where they are.
- A newly joined instance (from auto-scaling, a rolling deploy) naturally starts with current configuration from its own startup fetch, and only needs to subscribe to the broker topic to correctly receive all *future* broadcasts.
- This builds directly on [`@RefreshScope`](0234-refreshscope-for-runtime-refresh.md): the broker delivers the trigger, but each instance still performs its own local scoped-bean refresh in response.
- A broker outage disables broadcast refresh fleet-wide, though individual instances remain refreshable manually via their own local endpoint as a fallback — broadcast refresh is a convenience layered on top of, not a replacement for, per-instance refresh capability.
