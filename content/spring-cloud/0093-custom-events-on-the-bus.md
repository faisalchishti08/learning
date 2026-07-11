---
card: spring-cloud
gi: 93
slug: custom-events-on-the-bus
title: "Custom events on the bus"
---

## 1. What it is

Beyond the built-in `RefreshRemoteApplicationEvent`, Spring Cloud Bus lets an application define and publish its own `RemoteApplicationEvent` subclass, so any application-specific broadcast — "cache X is stale," "feature flag Y flipped," "drain traffic before shutdown" — travels over the same bus infrastructure as config refresh, reaching every instance without custom broker plumbing.

```java
public class CacheEvictEvent extends RemoteApplicationEvent {
    private String cacheName;
    public CacheEvictEvent() {} // required for deserialization
    public CacheEvictEvent(Object source, String originService, String cacheName) {
        super(source, originService);
        this.cacheName = cacheName;
    }
    public String getCacheName() { return cacheName; }
}
```

```java
@Autowired ApplicationEventPublisher publisher;

publisher.publishEvent(new CacheEvictEvent(this, busProperties.getId(), "productCache"));
```

## 2. Why & when

`/actuator/busrefresh` covers exactly one use case: reload configuration. A fleet frequently needs to broadcast other kinds of fleet-wide signals too — evict a specific cache everywhere, notify every instance a feature flag changed, tell every instance to start draining connections before a coordinated shutdown — and building a second broker connection and wire format from scratch for each of these would duplicate everything the bus already provides. Because `RefreshRemoteApplicationEvent` is just one subclass of the more general `RemoteApplicationEvent`, an application can define its own subclass, publish it through the normal Spring `ApplicationEventPublisher`, and have Spring Cloud Bus automatically serialize it, put it on the broker, and deserialize + re-publish it as a local Spring event on every other instance — with an `@EventListener` method reacting to it exactly like any other Spring application event.

Reach for custom bus events when:

- A fleet-wide broadcast is needed for something other than configuration reload — cache invalidation, feature-flag propagation, coordinated maintenance signals.
- The event should reach every instance uniformly, using infrastructure (serialization, broker connection, origin tracking) that's already proven and already running for bus refresh, rather than standing up a second broadcast mechanism.
- Instances should be able to both publish and consume the same custom event type, so any instance can trigger the broadcast and every instance (including, optionally, the originator) reacts identically.

## 3. Core concept

```
 instance A:
   publisher.publishEvent(new CacheEvictEvent(...))
        |
        v
   Spring Cloud Bus intercepts (because it extends RemoteApplicationEvent),
   serializes it, publishes to the broker
        |
        v
      [ bus / broker ]
        |          |
        v          v
   instance B    instance C
   bus deserializes it, re-publishes as a LOCAL Spring event
        |          |
        v          v
   @EventListener(CacheEvictEvent.class) methods fire locally on each
```

Any class extending `RemoteApplicationEvent` automatically gets this treatment — the only requirement is that the class is on the classpath of every instance so it can be deserialized.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A custom RemoteApplicationEvent published on one instance travels over the bus and is re published as a local Spring event on every other instance where an EventListener reacts to it">
  <rect x="20" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">instance A</text>
  <text x="105" y="56" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">publishEvent(CacheEvictEvent)</text>

  <rect x="250" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="50" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">bus / broker</text>

  <rect x="450" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="535" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">instance B</text>
  <text x="535" y="56" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">@EventListener fires locally</text>

  <defs><marker id="a93" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="190" y1="45" x2="250" y2="45" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a93)"/>
  <line x1="390" y1="45" x2="450" y2="45" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a93)"/>
</svg>

The same publish/subscribe pipeline bus refresh uses, generalized to any event type extending `RemoteApplicationEvent`.

## 5. Runnable example

The scenario: broadcast a cache-eviction signal across a fleet. Start with a plain local event listener (no bus), then route the event through a shared bus so every instance reacts, then add an event payload carrying which specific cache to evict, letting listeners react selectively.

### Level 1 — Basic

A plain local event and listener — no bus yet, the baseline Spring event mechanism a custom bus event builds on.

```java
import java.util.function.Consumer;
import java.util.*;

public class CustomBusEventLevel1 {
    record CacheEvictEvent(String cacheName) {}

    static class LocalEventBus {
        List<Consumer<CacheEvictEvent>> listeners = new ArrayList<>();
        void addListener(Consumer<CacheEvictEvent> l) { listeners.add(l); }
        void publishEvent(CacheEvictEvent e) {
            for (Consumer<CacheEvictEvent> l : listeners) l.accept(e); // local dispatch only
        }
    }

    public static void main(String[] args) {
        LocalEventBus events = new LocalEventBus();
        events.addListener(e -> System.out.println("evicting cache: " + e.cacheName()));

        events.publishEvent(new CacheEvictEvent("productCache"));
    }
}
```

How to run: `java CustomBusEventLevel1.java`

This is ordinary same-JVM `ApplicationEventPublisher`/`@EventListener` behavior — the event never leaves the process, which is exactly the gap a *remote* application event (the next level) closes.

### Level 2 — Intermediate

Route the event through a shared bus so it reaches multiple simulated instances, not just local listeners in the same process.

```java
import java.util.*;
import java.util.function.Consumer;

public class CustomBusEventLevel2 {
    record CacheEvictEvent(String originService, String cacheName) {}

    static class Bus {
        List<Consumer<CacheEvictEvent>> subscribers = new ArrayList<>();
        void subscribe(Consumer<CacheEvictEvent> handler) { subscribers.add(handler); }
        void publishEvent(CacheEvictEvent e) {
            for (Consumer<CacheEvictEvent> handler : subscribers) handler.accept(e); // fan-out to EVERY instance
        }
    }

    public static void main(String[] args) {
        Bus bus = new Bus();

        // instance B and instance C each register a listener for this custom event type
        bus.subscribe(e -> System.out.println("instanceB: evicting " + e.cacheName() + " (origin: " + e.originService() + ")"));
        bus.subscribe(e -> System.out.println("instanceC: evicting " + e.cacheName() + " (origin: " + e.originService() + ")"));

        // instanceA publishes -- reaches EVERY subscribed instance, same mechanism bus refresh uses
        bus.publishEvent(new CacheEvictEvent("instanceA", "productCache"));
    }
}
```

How to run: `java CustomBusEventLevel2.java`

`originService` (mirroring the real `RemoteApplicationEvent`'s built-in origin field) lets every receiving instance see which node triggered the broadcast — useful for logging and for avoiding a receiving instance mistakenly reacting to its own echoed event.

### Level 3 — Advanced

Add selective reaction: listeners only act on events for caches they actually own, and the origin instance skips reacting to its own broadcast (mirroring how a real bus setup often filters self-originated events).

```java
import java.util.*;
import java.util.function.Consumer;

public class CustomBusEventLevel3 {
    record CacheEvictEvent(String originService, String cacheName) {}

    static class Instance {
        String id;
        Set<String> ownedCaches;
        Instance(String id, Set<String> ownedCaches) { this.id = id; this.ownedCaches = ownedCaches; }

        void onCacheEvict(CacheEvictEvent e) {
            if (e.originService().equals(id)) {
                System.out.println(id + ": skipping own broadcast (already evicted locally before publish)");
                return;
            }
            if (!ownedCaches.contains(e.cacheName())) {
                System.out.println(id + ": ignoring -- does not own cache '" + e.cacheName() + "'");
                return;
            }
            System.out.println(id + ": evicting owned cache '" + e.cacheName() + "'");
        }
    }

    static class Bus {
        List<Instance> instances = new ArrayList<>();
        void register(Instance i) { instances.add(i); }
        void publishEvent(CacheEvictEvent e) {
            for (Instance i : instances) i.onCacheEvict(e);
        }
    }

    public static void main(String[] args) {
        Bus bus = new Bus();
        Instance a = new Instance("instanceA", Set.of("productCache", "userCache"));
        Instance b = new Instance("instanceB", Set.of("productCache"));
        Instance c = new Instance("instanceC", Set.of("orderCache")); // does NOT own productCache

        bus.register(a); bus.register(b); bus.register(c);

        // instanceA already evicted productCache locally, THEN published -- it should skip reacting to its own echo
        bus.publishEvent(new CacheEvictEvent("instanceA", "productCache"));
    }
}
```

How to run: `java CustomBusEventLevel3.java`

`instanceA` recognizes `e.originService().equals(id)` and skips redundant local work, `instanceB` owns `productCache` and evicts it, and `instanceC` receives the same event but ignores it because `orderCache`, not `productCache`, is what it owns — three instances, one broadcast, three different (and correct) reactions, each driven purely by local state each instance already had.

## 6. Walkthrough

Trace `bus.publishEvent` in Level 3.

1. `bus.publishEvent(new CacheEvictEvent("instanceA", "productCache"))` iterates the registered `instances` list in order: `a`, then `b`, then `c`.
2. For `a`, `onCacheEvict` runs: `e.originService().equals(id)` compares `"instanceA".equals("instanceA")`, which is `true`, so the method prints the skip message and returns immediately — `a` never even checks `ownedCaches` because the origin check short-circuits first.
3. For `b`, `e.originService().equals(id)` compares `"instanceA".equals("instanceB")`, `false`, so the method proceeds to check `ownedCaches.contains("productCache")` — `b`'s `ownedCaches` is `Set.of("productCache")`, so this is `true`, and `b` prints the eviction message.
4. For `c`, the origin check is again `false` (`c`'s id doesn't match), so it proceeds to the ownership check: `ownedCaches.contains("productCache")` against `c`'s `Set.of("orderCache")` is `false`, so `c` prints the ignore message and does no eviction work.
5. All three reactions happen from one `publishEvent` call, each instance deciding its own outcome purely from comparing the event's fields (`originService`, `cacheName`) against its own local state (`id`, `ownedCaches`) — no central coordinator decided who should react how.

```
publishEvent(origin=instanceA, cache=productCache)
   instanceA: origin matches self       -> SKIP (already handled locally)
   instanceB: owns productCache         -> EVICT
   instanceC: does not own productCache -> IGNORE
```

## 7. Gotchas & takeaways

> **Gotcha:** a custom `RemoteApplicationEvent` subclass must exist on the classpath of *every* instance expected to receive it, with a no-arg constructor available for deserialization — an instance running an older version of the application that lacks the event class (or has an incompatible field set) will fail to deserialize the broadcast, which can silently break fleet-wide coordination during a rolling deployment where old and new versions briefly coexist.

- Custom bus events reuse the exact publish/serialize/broker/deserialize/local-republish pipeline `RefreshRemoteApplicationEvent` already relies on — defining a new event type is a matter of extending `RemoteApplicationEvent` and publishing through the standard `ApplicationEventPublisher`, not building new broker plumbing.
- Carrying an origin field (built into `RemoteApplicationEvent`) lets every receiving instance distinguish "an event from elsewhere" from "an echo of my own broadcast," which matters whenever the originating instance already did the local work before publishing.
- Because every instance receives every event of a subscribed type, per-instance selectivity (as Level 3's `ownedCaches` check shows) belongs in the listener logic itself — the bus fans events out uniformly, filtering to "does this actually apply to me" is the receiving application's job.
- Reserve custom bus events for genuinely fleet-wide administrative signals; using them for high-volume business data duplicates what ordinary Spring Cloud Stream bindings (covered earlier) already do, without any of the throughput or partitioning controls those bindings offer.
