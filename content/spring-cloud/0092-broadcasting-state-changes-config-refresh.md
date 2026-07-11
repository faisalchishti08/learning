---
card: spring-cloud
gi: 92
slug: broadcasting-state-changes-config-refresh
title: "Broadcasting state changes (config refresh)"
---

## 1. What it is

`POST /actuator/busrefresh` on any one instance publishes a `RefreshRemoteApplicationEvent` onto Spring Cloud Bus, which every connected instance receives and reacts to by re-reading its externalized configuration and rebinding any `@ConfigurationProperties` or `@RefreshScope` beans — turning a single HTTP call into a fleet-wide configuration reload.

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-bus-amqp</artifactId>
</dependency>
```

```bash
curl -X POST http://any-instance:8080/actuator/busrefresh
```

## 2. Why & when

Spring Cloud Config's plain `/actuator/refresh` endpoint (covered in an earlier card) reloads configuration for the one instance it's called on — reloading a fleet of fifty instances would mean calling that endpoint fifty separate times, against fifty separate addresses, with no atomicity or coordination between them. `/actuator/busrefresh` solves exactly this: it performs a local refresh on the instance it's called on, then publishes the refresh event onto the bus, and every other instance's own bus listener receives that event and performs the identical local refresh on itself — the operator (or the Config Server's own webhook listener) makes one call, and the whole fleet updates.

Reach for bus refresh when:

- Configuration changes (a feature flag, a rate limit, a `@RefreshScope` bean's properties) need to apply uniformly and promptly across every running instance, without a rolling restart.
- The fleet is too large or too dynamic for calling `/actuator/refresh` on each instance individually to be practical or reliable — bus refresh scales to any fleet size at the same one-call cost.
- The Config Server's Git webhook is configured to trigger automatic broadcast on every commit to the configuration repository, so a config change becomes live fleet-wide the moment it's pushed, with no operator action needed at all.

## 3. Core concept

```
 curl -X POST http://instance-A:8080/actuator/busrefresh
        |
        v
 instance A: performs LOCAL refresh, then publishes
             RefreshRemoteApplicationEvent onto the bus
        |
        v
      [ bus / broker ]
        |         |         |
        v         v         v
   instance B  instance C  instance D
   each RECEIVES the event and performs
   its OWN local refresh independently
```

Every instance's refresh is still the same local mechanism `/actuator/refresh` already performs — the bus is purely the fan-out layer that triggers that local mechanism on every instance from a single origin call.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single busrefresh call on instance A triggers a local refresh there and publishes an event that causes every other instance to perform its own local refresh">
  <rect x="20" y="20" width="150" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">POST /busrefresh</text>

  <rect x="230" y="20" width="140" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="42" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">instance A</text>
  <text x="300" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">local refresh + publish</text>

  <rect x="230" y="100" width="140" height="34" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="300" y="121" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">bus / broker</text>

  <rect x="40" y="170" width="110" height="34" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="95" y="191" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">instance B: refresh</text>
  <rect x="410" y="170" width="110" height="34" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="465" y="191" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">instance C: refresh</text>

  <defs><marker id="a92" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="170" y1="42" x2="230" y2="42" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a92)"/>
  <line x1="300" y1="64" x2="300" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a92)"/>
  <line x1="260" y1="134" x2="110" y2="170" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a92)"/>
  <line x1="340" y1="134" x2="460" y2="170" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a92)"/>
</svg>

One HTTP call at the origin, one broker-mediated broadcast, every instance performs its own local refresh independently.

## 5. Runnable example

The scenario: a `@RefreshScope`-flavored config value shared across a simulated fleet, where refreshing it on one node broadcasts the update to every node. Start with a single instance's local refresh, then extend to fleet-wide broadcast via a shared broker, then add a case where one instance is temporarily disconnected and must catch up.

### Level 1 — Basic

A single instance holds a config value and refreshes it locally — the baseline `/actuator/refresh` behavior, no bus involved yet.

```java
import java.util.function.Supplier;

public class ConfigRefreshLevel1 {
    // stands in for a @RefreshScope bean re-reading its bound property on refresh
    static class ConfigHolder {
        String rateLimit = "100/min";
        void refresh(String newValue) {
            rateLimit = newValue;
            System.out.println("local refresh applied -- rateLimit is now " + rateLimit);
        }
    }

    public static void main(String[] args) {
        ConfigHolder instanceA = new ConfigHolder();
        System.out.println("instanceA starts with rateLimit=" + instanceA.rateLimit);

        instanceA.refresh("50/min"); // equivalent to calling /actuator/refresh on instanceA alone
    }
}
```

How to run: `java ConfigRefreshLevel1.java`

Only `instanceA` changes — this models exactly what `/actuator/refresh` (no bus) does: it reloads the config for the single instance the endpoint was called on, and nothing else.

### Level 2 — Intermediate

Add a shared bus: refreshing one instance now publishes an event that every other instance's own refresh logic reacts to.

```java
import java.util.*;
import java.util.function.Consumer;

public class ConfigRefreshLevel2 {
    static class ConfigHolder {
        String name;
        String rateLimit = "100/min";
        ConfigHolder(String name) { this.name = name; }
        void refresh(String newValue) {
            rateLimit = newValue;
            System.out.println(name + " refreshed locally -- rateLimit is now " + rateLimit);
        }
    }

    static class Bus {
        List<Consumer<String>> subscribers = new ArrayList<>();
        void subscribe(Consumer<String> handler) { subscribers.add(handler); }
        void busRefresh(String newValue) {
            for (Consumer<String> handler : subscribers) handler.accept(newValue); // fan-out to every instance
        }
    }

    public static void main(String[] args) {
        Bus bus = new Bus();
        ConfigHolder instanceA = new ConfigHolder("instanceA");
        ConfigHolder instanceB = new ConfigHolder("instanceB");
        ConfigHolder instanceC = new ConfigHolder("instanceC");

        // every instance's local refresh is registered as a bus subscriber on startup
        bus.subscribe(instanceA::refresh);
        bus.subscribe(instanceB::refresh);
        bus.subscribe(instanceC::refresh);

        System.out.println("-- POST /actuator/busrefresh called against instanceA --");
        bus.busRefresh("50/min"); // ONE call, ALL three instances refresh
    }
}
```

How to run: `java ConfigRefreshLevel2.java`

`bus.busRefresh` is called once, but because all three instances' `refresh` methods were registered as subscribers, all three print a local refresh message — this is the exact behavior difference `/actuator/busrefresh` has over `/actuator/refresh`: the same local mechanism, triggered fleet-wide from one call.

### Level 3 — Advanced

Handle a temporarily disconnected instance: it misses a broadcast while down, then must catch up to the latest value once it reconnects, rather than silently running stale configuration forever.

```java
import java.util.*;
import java.util.function.Consumer;

public class ConfigRefreshLevel3 {
    static class ConfigHolder {
        String name;
        String rateLimit = "100/min";
        ConfigHolder(String name) { this.name = name; }
        void refresh(String newValue) {
            rateLimit = newValue;
            System.out.println(name + " refreshed locally -- rateLimit is now " + rateLimit);
        }
    }

    static class Bus {
        Map<String, Consumer<String>> subscribers = new LinkedHashMap<>();
        String lastBroadcastValue = null; // the bus itself has no memory in real life; this models a Config Server holding latest state
        void subscribe(String id, Consumer<String> handler) { subscribers.put(id, handler); }
        void unsubscribe(String id) { subscribers.remove(id); }
        void busRefresh(String newValue) {
            lastBroadcastValue = newValue;
            for (Consumer<String> handler : subscribers.values()) handler.accept(newValue);
        }
    }

    public static void main(String[] args) {
        Bus bus = new Bus();
        ConfigHolder instanceA = new ConfigHolder("instanceA");
        ConfigHolder instanceB = new ConfigHolder("instanceB");

        bus.subscribe("A", instanceA::refresh);
        bus.subscribe("B", instanceB::refresh);

        System.out.println("-- broadcast #1 (A and B both connected) --");
        bus.busRefresh("50/min");

        bus.unsubscribe("B"); // instance B goes down / disconnects from the broker
        System.out.println("-- broadcast #2 (B is DOWN, misses it) --");
        bus.busRefresh("25/min");
        System.out.println("instanceB is still running stale config: " + instanceB.rateLimit);

        // instance B reconnects -- it must catch up to whatever the LATEST broadcast value was, not just resume listening
        bus.subscribe("B", instanceB::refresh);
        instanceB.refresh(bus.lastBroadcastValue); // catch-up refresh on reconnect
        System.out.println("instanceB after reconnect catch-up: " + instanceB.rateLimit);
    }
}
```

How to run: `java ConfigRefreshLevel3.java`

`instanceB` correctly stays at `"50/min"` through broadcast #2 (it genuinely never received that event while disconnected), then explicitly pulls `bus.lastBroadcastValue` (`"25/min"`) on reconnect rather than assuming it's already current — modeling the real-world need for a reconnecting instance to reconcile against current state rather than trusting a broadcast-only channel it was absent for.

## 6. Walkthrough

Trace Level 3 end to end.

1. `bus.subscribe("A", ...)` and `bus.subscribe("B", ...)` register both instances' `refresh` methods as bus subscribers.
2. `bus.busRefresh("50/min")` sets `lastBroadcastValue` to `"50/min"` and iterates both subscribers, calling `refresh("50/min")` on each — both `instanceA.rateLimit` and `instanceB.rateLimit` become `"50/min"`, and both print a local refresh message.
3. `bus.unsubscribe("B")` removes `instanceB`'s entry from the `subscribers` map, modeling `instanceB` losing its connection to the broker.
4. `bus.busRefresh("25/min")` sets `lastBroadcastValue` to `"25/min"` but iterates a `subscribers` map that now contains only `"A"` — only `instanceA.refresh("25/min")` runs; `instanceB.rateLimit` remains `"50/min"`, unchanged, exactly as it would in production if the instance were genuinely offline when the broadcast fired.
5. The `println` confirming `instanceB` is stale reads `"50/min"`, proving the missed broadcast really did leave it behind.
6. `bus.subscribe("B", ...)` re-registers `instanceB`, modeling reconnection to the broker.
7. `instanceB.refresh(bus.lastBroadcastValue)` is called explicitly and directly (not via `busRefresh`) with the bus's remembered `"25/min"` — this is the catch-up step, bringing `instanceB.rateLimit` in line with what every other instance already has, without needing a fresh broadcast to be re-sent.
8. The final `println` confirms `instanceB.rateLimit` is now `"25/min"`, matching `instanceA`.

```
broadcast #1 (50/min): A refreshes, B refreshes         -> both at 50/min
   (B disconnects)
broadcast #2 (25/min): A refreshes, B MISSES it entirely -> A=25/min, B=50/min (stale)
   (B reconnects, pulls lastBroadcastValue explicitly)
catch-up: B.refresh(25/min)                              -> both at 25/min again
```

## 7. Gotchas & takeaways

> **Gotcha:** the bus itself does not replay missed events to a reconnecting instance — a real message bus is a fire-and-forget fan-out, not a durable log every subscriber can rewind. An instance that was down during a broadcast genuinely misses it and must reconcile some other way on reconnect (re-fetching current config from the Config Server on startup, for instance) rather than assuming the bus will catch it up automatically.

- `/actuator/busrefresh` performs the *same* local refresh mechanism as `/actuator/refresh` — the bus adds fan-out on top, it doesn't replace or change what "refresh" itself does to a `@RefreshScope` bean.
- Because it's one HTTP call producing a fleet-wide effect, bus refresh is naturally the target of Config Server's Git webhook, letting a configuration change become live everywhere the moment it's committed.
- A disconnected or newly-started instance needs its own path to current configuration (typically: fetch fresh from the Config Server on startup) since the bus, being a live broadcast channel, offers no guarantee to instances that weren't listening at broadcast time.
- Treat bus refresh as an operational broadcast mechanism, not a transactional one — there's no built-in confirmation that every instance in the fleet actually completed its local refresh successfully, so monitoring or logging each instance's own refresh outcome remains the operator's responsibility.
