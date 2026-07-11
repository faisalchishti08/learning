---
card: spring-cloud
gi: 38
slug: spring-cloud-zookeeper-discovery-config
title: "Spring Cloud Zookeeper (discovery & config)"
---

## 1. What it is

Spring Cloud Zookeeper is a third discovery-and-config option, built on Apache ZooKeeper — a strongly-consistent, hierarchical key-value coordination service originally built for the Hadoop ecosystem. Like Eureka and Consul, it plugs into Spring Cloud Commons' `DiscoveryClient` abstraction; unlike them, its consistency model comes from ZooKeeper's ZAB (ZooKeeper Atomic Broadcast) protocol, giving strict ordering guarantees rather than eventual convergence.

```properties
spring.application.name=orders-service
spring.cloud.zookeeper.connect-string=localhost:2181
spring.cloud.zookeeper.discovery.enabled=true
```

```java
@SpringBootApplication
@EnableDiscoveryClient // same vendor-neutral annotation, works with Eureka, Consul, or Zookeeper
public class OrdersServiceApplication { }
```

## 2. Why & when

The choice between Eureka, Consul, and Zookeeper comes down to what's already in the infrastructure and what consistency guarantees matter. Zookeeper stores service registrations as *ephemeral znodes* — nodes in a hierarchical tree that automatically disappear the moment the client's session disconnects, which is a fundamentally different mechanism from Eureka's heartbeat-timeout eviction or Consul's agent-driven health checks.

Reach for Zookeeper when:

- The organization already runs ZooKeeper for other purposes — it's a long-standing dependency of Kafka (older versions), Hadoop, and various distributed systems, so it may already be operationally familiar and available.
- Strict consistency matters more than availability during a partition — ZooKeeper is CP: a minority partition simply can't serve writes (or, depending on configuration, reads) until it can reach quorum again, rather than serving a possibly-stale view.
- Ephemeral-znode-based membership is a good fit — the moment a client's session to ZooKeeper drops (crash, network cut, GC pause exceeding the session timeout), its registration disappears automatically, with no separate eviction sweep needed.

## 3. Core concept

```
 /services
    /orders-service
        /orders-service-0000000001   (ephemeral znode, holds host:port + metadata)
        /orders-service-0000000002
    /billing-service
        /billing-service-0000000001

 client session drops (crash, GC pause, network cut)
   -> ZooKeeper automatically deletes that client's ephemeral znodes
   -> other clients watching /services/orders-service are notified of the change
```

Registration lives as long as the client's session does — no heartbeat timeout to configure, because the underlying session mechanism handles liveness.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Service instances create ephemeral znodes under a services path in ZooKeeper, and those znodes vanish automatically the moment the owning session disconnects, notifying watchers immediately">
  <rect x="230" y="15" width="180" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="36" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">/services/orders-service</text>

  <rect x="140" y="80" width="160" height="34" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="220" y="101" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ephemeral znode #1</text>

  <rect x="340" y="80" width="160" height="34" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="420" y="101" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ephemeral znode #2</text>

  <line x1="290" y1="49" x2="230" y2="78" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="350" y1="49" x2="410" y2="78" stroke="#8b949e" stroke-width="1.2"/>

  <rect x="60" y="150" width="220" height="40" rx="8" fill="#e6494930" stroke="#e64949" stroke-width="1.5"/>
  <text x="170" y="174" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">session #1 disconnects -&gt; znode #1 auto-deleted</text>

  <line x1="220" y1="114" x2="170" y2="148" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="3,3" marker-end="url(#a38)"/>

  <defs><marker id="a38" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each instance's registration is tied directly to its live session — losing the session removes the registration immediately, with no separate timeout to wait out.

## 5. Runnable example

The scenario: model ZooKeeper's ephemeral-znode registration for `billing-service`, starting from a plain registration, then adding session-tied automatic cleanup, then adding watchers that get notified the instant membership changes.

### Level 1 — Basic

Plain registration under a hierarchical path — no session semantics yet.

```java
import java.util.*;

public class ZookeeperLevel1 {
    static Map<String, List<String>> tree = new HashMap<>(); // path -> child znode names

    static void createEphemeralZnode(String servicePath, String znodeName) {
        tree.computeIfAbsent(servicePath, k -> new ArrayList<>()).add(znodeName);
    }

    public static void main(String[] args) {
        createEphemeralZnode("/services/billing-service", "billing-service-0000000001");
        createEphemeralZnode("/services/billing-service", "billing-service-0000000002");

        System.out.println("znodes under /services/billing-service: "
                + tree.get("/services/billing-service"));
    }
}
```

How to run: `java ZookeeperLevel1.java`

This mirrors the tree structure but has no notion yet of *why* a znode would ever disappear — that's the session mechanism, added next.

### Level 2 — Intermediate

Tie each znode to a session, and remove it automatically the moment that session disconnects.

```java
import java.util.*;

public class ZookeeperLevel2 {
    static class Session {
        String id;
        boolean connected = true;
        Session(String id) { this.id = id; }
    }

    static Map<String, List<String>> tree = new HashMap<>();
    static Map<String, Session> znodeOwner = new HashMap<>(); // znode name -> owning session

    static void createEphemeralZnode(String servicePath, String znodeName, Session session) {
        tree.computeIfAbsent(servicePath, k -> new ArrayList<>()).add(znodeName);
        znodeOwner.put(znodeName, session);
    }

    static void disconnectSession(Session session) {
        session.connected = false;
        // ZooKeeper's server-side cleanup: every ephemeral znode owned by this session is deleted
        for (var entry : tree.entrySet()) {
            entry.getValue().removeIf(znode -> znodeOwner.get(znode) == session);
        }
    }

    public static void main(String[] args) {
        Session s1 = new Session("session-1");
        Session s2 = new Session("session-2");
        createEphemeralZnode("/services/billing-service", "billing-service-0000000001", s1);
        createEphemeralZnode("/services/billing-service", "billing-service-0000000002", s2);

        System.out.println("before disconnect: " + tree.get("/services/billing-service"));

        disconnectSession(s1); // instance 1 crashes, its session times out
        System.out.println("after s1 disconnects: " + tree.get("/services/billing-service"));
    }
}
```

How to run: `java ZookeeperLevel2.java`

`disconnectSession` models what ZooKeeper's server does automatically when a client's session ends (clean close, crash-triggered timeout, or an unrecoverable network partition past the session timeout): every ephemeral znode that session owned is removed, with no separate eviction sweep, heartbeat expiry window, or health check needed — the deletion is a direct, immediate consequence of the session ending.

### Level 3 — Advanced

Add watchers: clients that registered interest in a path get notified the instant its children change, modeling ZooKeeper's watch mechanism that a real `DiscoveryClient` uses to react to membership changes without polling.

```java
import java.util.*;
import java.util.function.Consumer;

public class ZookeeperLevel3 {
    static class Session {
        String id;
        Session(String id) { this.id = id; }
    }

    static Map<String, List<String>> tree = new HashMap<>();
    static Map<String, Session> znodeOwner = new HashMap<>();
    static Map<String, List<Consumer<List<String>>>> watchers = new HashMap<>();

    static void watch(String path, Consumer<List<String>> callback) {
        watchers.computeIfAbsent(path, k -> new ArrayList<>()).add(callback);
    }

    static void notifyWatchers(String path) {
        for (var callback : watchers.getOrDefault(path, List.of())) {
            callback.accept(tree.getOrDefault(path, List.of()));
        }
    }

    static void createEphemeralZnode(String path, String znodeName, Session session) {
        tree.computeIfAbsent(path, k -> new ArrayList<>()).add(znodeName);
        znodeOwner.put(znodeName, session);
        notifyWatchers(path); // membership changed -> fire immediately
    }

    static void disconnectSession(String path, Session session) {
        tree.getOrDefault(path, List.of()).removeIf(znode -> znodeOwner.get(znode) == session);
        notifyWatchers(path); // membership changed again -> fire immediately
    }

    public static void main(String[] args) {
        String path = "/services/billing-service";

        // orders-service's DiscoveryClient watches billing-service's path
        watch(path, znodes -> System.out.println("orders-service sees billing-service instances: " + znodes));

        Session s1 = new Session("session-1");
        Session s2 = new Session("session-2");
        createEphemeralZnode(path, "billing-service-0000000001", s1); // fires watcher: [znode1]
        createEphemeralZnode(path, "billing-service-0000000002", s2); // fires watcher: [znode1, znode2]

        disconnectSession(path, s1); // fires watcher: [znode2]
    }
}
```

How to run: `java ZookeeperLevel3.java`

`watch` models `orders-service`'s `DiscoveryClient` registering a callback on `billing-service`'s path; every time membership changes — a new instance registers, or a session drops and its znode vanishes — `notifyWatchers` fires that callback immediately with the fresh child list. Three lines of output show the watcher firing three separate times, each reflecting the exact current membership at that instant, with zero polling delay.

## 6. Walkthrough

Trace Level 3's sequence in order.

1. `watch(path, ...)` registers a callback before anything else happens — this models `orders-service` starting up and its `DiscoveryClient` placing a watch on `/services/billing-service`, the ZooKeeper equivalent of "notify me the moment this path's children change."
2. `createEphemeralZnode(path, "billing-service-0000000001", s1)` runs — it appends the znode to the tree, records `s1` as its owner, then immediately calls `notifyWatchers(path)`. The registered callback fires and prints `[billing-service-0000000001]` — `orders-service` learns about the new instance the moment it registers, with no polling interval to wait out.
3. `createEphemeralZnode(path, "billing-service-0000000002", s2)` runs the same sequence for a second instance, firing the watcher again with the updated list `[billing-service-0000000001, billing-service-0000000002]`.
4. `disconnectSession(path, s1)` runs — it removes any znode owned by `s1` from the tree (just the first instance) and calls `notifyWatchers(path)` again, firing the callback a third time with `[billing-service-0000000002]`. This models `session-1`'s ZooKeeper session ending (a crash, a network partition exceeding the session timeout, or a clean shutdown), which triggers immediate, automatic cleanup and immediate notification — no separate eviction pass, no lease expiry window.
5. Across the whole run, `orders-service`'s view of `billing-service` stays continuously correct in real time, because every state change is pushed the instant it happens rather than discovered on the next poll.

```
watch(path, callback)                       <- registered once, stays active
createEphemeralZnode(#1) -> notify -> [#1]
createEphemeralZnode(#2) -> notify -> [#1, #2]
disconnectSession(s1)    -> notify -> [#2]
```

## 7. Gotchas & takeaways

> **Gotcha:** ZooKeeper watches are typically one-shot — after a watch fires once, the client must re-register it to keep receiving future notifications on that path. A real `DiscoveryClient` implementation handles this re-registration internally, but hand-rolled ZooKeeper code that forgets to re-watch after each event will silently stop receiving updates after the first change.

- Ephemeral znodes tie registration lifetime directly to session lifetime — there's no separate heartbeat-timeout or agent-health-check concept to configure, unlike Eureka or Consul.
- ZooKeeper's CP consistency model means a client in a minority partition may be unable to write (or even read, depending on configuration) rather than serving a possibly-stale view — the opposite tradeoff from Eureka's AP self-preservation.
- Watches give near-instant membership change notification, in contrast to Eureka's client-side registry cache refreshed on a polling interval — a real latency advantage when membership changes need to propagate fast.
- Reaching for ZooKeeper mainly makes sense when it's already present for another reason (frequently Kafka in older deployments) — introducing it purely for Spring Cloud discovery, when Eureka or Consul would otherwise fit, adds an extra piece of strongly-consistent, quorum-based infrastructure to operate.
