---
card: microservices
gi: 537
slug: spring-cloud-bus-for-cross-instance-coordination
title: "Spring Cloud Bus for cross-instance coordination"
---

## 1. What it is

**Spring Cloud Bus** links every instance of a service (and, potentially, every service in a whole system) to a shared lightweight message broker (typically RabbitMQ or Kafka), so a single event broadcast from one instance is automatically delivered to every other connected instance — most commonly used to broadcast configuration-refresh events (`/actuator/busrefresh`) so that a config change made once is picked up by every instance in a fleet, without having to call each instance's own `/actuator/refresh` endpoint individually.

## 2. Why & when

You reach for Spring Cloud Bus whenever an operational event needs to reach every instance of a horizontally-scaled service, rather than just one:

- **A single instance's `/actuator/refresh` endpoint only refreshes that one instance's configuration**, re-reading from Spring Cloud Config for that instance alone. In a fleet of ten instances, refreshing configuration correctly would otherwise require calling `/actuator/refresh` on all ten individually — tedious, error-prone if one is missed, and requiring you to know every instance's individual address (itself the [hardcoded service location](0526-hardcoded-service-locations.md) problem, applied to an operational task).
- **Spring Cloud Bus broadcasts one event to a shared topic on a message broker, and every subscribed instance receives it** — calling `/actuator/busrefresh` on *any single instance* triggers a refresh across the *entire* fleet, since that one instance publishes a `RefreshRemoteApplicationEvent` onto the bus, and every other instance's Bus listener picks it up and refreshes locally in response.
- **The same mechanism generalizes beyond configuration refresh** — any custom event can be broadcast across the fleet via the bus (a cache-invalidation signal, a feature-flag toggle notification), letting you build fleet-wide coordination on the same publish-once-deliver-to-all pattern, rather than hand-rolling a broadcast mechanism per use case.
- **You reach for it specifically when the coordination need is "notify everyone" rather than "coordinate exactly one"** — contrast with [leader election](0533-spring-integration-leader-election-locks.md) (exactly one instance takes a role) or [distributed locks](0533-spring-integration-leader-election-locks.md) (exactly one instance proceeds at a time); Spring Cloud Bus is for the opposite shape, where you want *every* instance to react to the same event.

## 3. Core concept

Think of a company-wide fire alarm system versus calling every employee's desk phone individually to tell them to evacuate. Calling desk phones one at a time means someone eventually gets missed, it takes a while to get through everyone, and the caller needs to know every extension. Pulling one fire alarm lever broadcasts to every connected alarm bell in the building simultaneously — anyone who installed a bell (subscribed to the alarm system) hears it, regardless of how many bells exist or where they're physically located, and the person pulling the lever doesn't need to know anything about who's currently in the building. Spring Cloud Bus is that shared alarm system: one event, published once, reaches every instance wired into the same broker topic.

Concretely:

1. **Every instance connects to a shared message broker topic at startup** (RabbitMQ or Kafka, configured via `spring-cloud-starter-bus-amqp` or `spring-cloud-starter-bus-kafka`), each instance both publishing to and listening on that same topic.
2. **Calling `/actuator/busrefresh` on any one instance publishes a `RefreshRemoteApplicationEvent`** onto the shared bus topic — this is a fire-and-forget broadcast, not a targeted call to a specific instance.
3. **Every instance's Bus listener receives that same event** (since they're all subscribed to the same topic) and reacts to it locally — for a refresh event, each instance independently re-fetches its configuration from Spring Cloud Config and applies any `@RefreshScope`-annotated beans' updated values.
4. **The originating instance doesn't need to know how many other instances exist, or their addresses** — the broker handles fan-out delivery to every subscriber; this is the same [service-discovery-style indirection](0526-hardcoded-service-locations.md) idea applied to broadcast messaging rather than point-to-point calls.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calling busrefresh on one instance publishes an event to a shared broker topic, which fans it out to every other subscribed instance automatically, refreshing configuration fleet-wide from one call">
  <rect x="20" y="80" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance A: /busrefresh</text>

  <rect x="260" y="30" width="140" height="140" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="330" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">shared broker topic</text>
  <line x1="160" y1="100" x2="260" y2="100" stroke="#8b949e" marker-end="url(#a5)"/>

  <rect x="470" y="30" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance B: refreshed</text>
  <rect x="470" y="83" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance C: refreshed</text>
  <rect x="470" y="136" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="158" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance D: refreshed</text>
  <line x1="400" y1="70" x2="470" y2="47" stroke="#8b949e" marker-end="url(#a5)"/>
  <line x1="400" y1="100" x2="470" y2="100" stroke="#8b949e" marker-end="url(#a5)"/>
  <line x1="400" y1="130" x2="470" y2="153" stroke="#8b949e" marker-end="url(#a5)"/>
  <defs><marker id="a5" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

One call to any single instance publishes to the shared bus, which fans the event out to every subscribed instance automatically.

## 5. Runnable example

Scenario: broadcasting a configuration-refresh event across a fleet. We start with a plain Java model of one-at-a-time point-to-point calls (the problem), extend it to a simple publish-subscribe broadcast model, then handle the real Spring Cloud Bus shape using `/actuator/busrefresh` and `@RefreshScope`.

### Level 1 — Basic

```java
// File: PointToPointRefresh.java -- the PROBLEM: refreshing configuration
// requires calling EVERY instance INDIVIDUALLY, by address, one at a time.
import java.util.*;

public class PointToPointRefresh {
    static void callRefreshEndpoint(String instanceAddress) {
        System.out.println("Calling POST " + instanceAddress + "/actuator/refresh ...");
    }

    public static void main(String[] args) {
        List<String> instanceAddresses = List.of(
            "http://10.0.5.2:8080", "http://10.0.5.9:8080", "http://10.0.5.14:8080"
        ); // must be known and enumerated INDIVIDUALLY, by whoever is triggering the refresh

        for (String address : instanceAddresses) {
            callRefreshEndpoint(address); // one call PER instance
        }
        System.out.println("Problem: if a 4th instance existed but wasn't in this list, it's silently NEVER refreshed.");
    }
}
```

How to run: `java PointToPointRefresh.java`

The caller must know every instance's address ahead of time and call each one individually — this is both operationally tedious and fragile: any instance not included in `instanceAddresses` (perhaps one that scaled up after this list was last updated) silently never receives the refresh, running with stale configuration indefinitely.

### Level 2 — Intermediate

```java
// File: BroadcastModel.java -- models the BUS idea: publish ONE event to
// a SHARED topic, and every subscribed instance receives it automatically
// -- the publisher doesn't need to know how many subscribers exist.
import java.util.*;
import java.util.function.Consumer;

public class BroadcastModel {
    static List<Consumer<String>> subscribers = new ArrayList<>(); // instances subscribe themselves

    static void subscribe(String instanceName) {
        subscribers.add(event -> System.out.println("[" + instanceName + "] received event: " + event + " -- refreshing locally"));
    }

    // publishing doesn't need to know WHO is subscribed, or how many -- just publish ONCE
    static void publish(String event) {
        System.out.println("Publishing '" + event + "' to the shared topic...");
        for (Consumer<String> subscriber : subscribers) subscriber.accept(event);
    }

    public static void main(String[] args) {
        subscribe("instance-A");
        subscribe("instance-B");
        subscribe("instance-C");

        publish("RefreshRemoteApplicationEvent"); // ONE call, reaches all THREE subscribers automatically

        // a 4th instance joins LATER, subscribing itself -- future publishes reach it too, with no change to publish()
        subscribe("instance-D");
        publish("RefreshRemoteApplicationEvent");
    }
}
```

How to run: `java BroadcastModel.java`

`publish` has no knowledge of how many subscribers exist or their identities — it simply broadcasts to whoever is currently subscribed. The first `publish` call reaches all three initially-subscribed instances; after `instance-D` subscribes itself, the second `publish` call automatically reaches it too, with zero change to `publish`'s own code — modeling exactly how a new fleet instance, once connected to the shared broker topic, automatically starts receiving bus events without any change to how those events are published.

### Level 3 — Advanced

```java
// File: SpringCloudBusRealShape.java -- the REAL Spring Cloud Bus shape:
// a @RefreshScope bean whose value updates FLEET-WIDE after ONE call to
// /actuator/busrefresh on any single instance.
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.*;

public class SpringCloudBusRealShape {

    // @RefreshScope beans are RE-CREATED (picking up fresh @Value bindings)
    // whenever a refresh event -- LOCAL or, via the Bus, FLEET-WIDE -- is received
    @RefreshScope
    @Component
    static class FeatureFlagHolder {
        @Value("${feature.new-checkout-flow.enabled:false}")
        private boolean newCheckoutFlowEnabled;

        public boolean isNewCheckoutFlowEnabled() { return newCheckoutFlowEnabled; }
    }

    @RestController
    static class CheckoutController {
        private final FeatureFlagHolder featureFlagHolder;
        CheckoutController(FeatureFlagHolder featureFlagHolder) { this.featureFlagHolder = featureFlagHolder; }

        @GetMapping("/checkout-flow")
        public String getCheckoutFlow() {
            return featureFlagHolder.isNewCheckoutFlowEnabled() ? "new-flow" : "legacy-flow";
        }
    }

    // Operational sequence, illustrating the fleet-wide effect (as it would really run):
    // 1. feature.new-checkout-flow.enabled=false in Config Server, all instances serving "legacy-flow"
    // 2. Config Server value updated to true
    // 3. ONE call: POST http://instance-A:8080/actuator/busrefresh
    // 4. instance-A publishes a RefreshRemoteApplicationEvent onto the shared bus topic
    // 5. EVERY instance (A, B, C, ...) receives the event, re-reads config, recreates FeatureFlagHolder
    // 6. GET /checkout-flow on ANY instance now returns "new-flow" -- fleet-wide, from ONE call
}
```

How to run: requires `spring-cloud-starter-bus-amqp` (or `-kafka`) plus `spring-cloud-config-client` on every instance, all connected to the same broker and Config Server; after updating the config value in Config Server, calling `POST /actuator/busrefresh` on any single running instance triggers every connected instance to refresh, observable by calling `GET /checkout-flow` on each and seeing all of them return `"new-flow"`.

`@RefreshScope` on `FeatureFlagHolder` means this bean isn't a normal singleton created once at startup — it's a special proxy that can be torn down and recreated on demand, re-evaluating its `@Value` bindings against the latest configuration each time. A bus refresh event, received identically by every instance connected to the shared topic, triggers exactly this recreation on each of them independently, which is why one `/actuator/busrefresh` call updates the *entire* fleet's behavior rather than just the one instance it was called against.

## 6. Walkthrough

Trace the operational sequence from Level 3 end to end, across a three-instance fleet (A, B, C):

1. **The `feature.new-checkout-flow.enabled` property is updated to `true` in the Config Server** — at this point, nothing in the running fleet has changed yet; every instance's `FeatureFlagHolder` still holds the old, cached value (`false`) from when it was last created or refreshed.
2. **An operator calls `POST http://instance-A:8080/actuator/busrefresh`** — this hits instance A specifically, but note the endpoint name: `busrefresh`, not `refresh`. This is the Bus-aware variant.
3. **Instance A's Bus integration constructs a `RefreshRemoteApplicationEvent`** and publishes it onto the shared broker topic every instance in the fleet is connected to. Instance A does not need to know instance B's or C's addresses, or even that they exist — it publishes once, to the topic, and is done.
4. **The broker delivers this event to every subscriber on that topic** — which includes instance A itself, instance B, and instance C, since all three connected to the same topic at startup.
5. **Each instance's own Bus listener receives the event and triggers a *local* refresh**, exactly as if `/actuator/refresh` (the non-Bus, single-instance endpoint) had been called directly on that instance. Each instance independently re-fetches the latest configuration from Config Server and recreates its `@RefreshScope` beans — including `FeatureFlagHolder` — with the new `true` value bound.
6. **A subsequent `GET /checkout-flow` request, whether it lands on instance A, B, or C**, now reads `featureFlagHolder.isNewCheckoutFlowEnabled()` as `true` and returns `"new-flow"` — all three instances behave consistently, having each independently refreshed in response to the one broadcast event, without the operator needing to call any endpoint more than once, or know how many instances currently exist in the fleet.

The key structural point: step 2's single HTTP call became step 5's *N* independent local refreshes (one per fleet instance), entirely through the shared broker's fan-out delivery — the operator's mental model stays "I called refresh once," even though the actual effect correctly reached every instance currently running, including ones that might have been added to the fleet after the operator last checked how many there were.

## 7. Gotchas & takeaways

> **Gotcha:** Spring Cloud Bus requires every instance to actually be connected to the same broker topic at the moment the event is published — an instance that's still starting up, or briefly disconnected from the broker, will not receive that specific refresh event and will keep running with stale configuration until its *next* successful refresh (or its own restart, which re-reads configuration fresh); the bus doesn't retroactively deliver a missed broadcast to a late-joining or reconnecting instance.

- Reach for Spring Cloud Bus when the coordination need is "notify every instance," the opposite shape from leader election or locks (which coordinate toward exactly one instance acting).
- `/actuator/busrefresh` (called on any one instance) broadcasts to the whole fleet; `/actuator/refresh` (called per instance) only affects that single instance — using the wrong one is an easy, quiet mistake that leaves most of the fleet on stale configuration.
- `@RefreshScope` is what makes a bean's values actually update in response to a refresh event, whether triggered locally or via the bus — a plain singleton bean's `@Value` fields are bound once at startup and won't pick up a refresh at all.
- The publisher of a bus event never needs to know how many instances exist or their addresses — the broker's topic-based fan-out handles delivery to whichever instances happen to be currently connected, which is what makes this approach resilient to a fleet's size changing over time.
