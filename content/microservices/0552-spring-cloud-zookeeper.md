---
card: microservices
gi: 552
slug: spring-cloud-zookeeper
title: "Spring Cloud Zookeeper"
---

## 1. What it is

**Spring Cloud Zookeeper** is the concrete [`DiscoveryClient`](0539-spring-cloud-commons-shared-abstractions.md) integration for Apache ZooKeeper, and also provides ZooKeeper-backed configuration and the [distributed locking/leader election](0533-spring-integration-leader-election-locks.md) primitives discussed earlier, all built on ZooKeeper's ephemeral, sequential znode data model. Where Eureka and Consul are purpose-built service registries, ZooKeeper is a more general-purpose distributed coordination service that Spring Cloud Zookeeper adapts specifically for service discovery, configuration, and locking use cases — a natural choice if ZooKeeper is already part of your infrastructure (commonly true in Kafka-based deployments, since older Kafka versions depended on it directly).

## 2. Why & when

You reach for ZooKeeper-backed discovery specifically when ZooKeeper is already operated in your infrastructure, or when its session-based failure detection is preferable to a heartbeat or polling-based model:

- **ZooKeeper's ephemeral znodes are tied directly to a client's session**, as discussed for [leader election and locks](0534-spring-cloud-cluster-zookeeper-redis-locks.md) — a service instance's registration znode disappears promptly and automatically the moment its session drops (a crash, a network partition), without waiting for a heartbeat timeout or a scheduled health-check poll to notice.
- **If your organization already operates ZooKeeper** (commonly true for older Kafka deployments, or Hadoop-ecosystem tooling), reusing it for Spring service discovery avoids introducing an entirely separate registry technology (Eureka or Consul) purely for this purpose.
- **ZooKeeper's data model (a hierarchical namespace of znodes, similar to a filesystem) naturally supports watches** — a client can subscribe to be notified the instant a specific znode (or its children) changes, giving near-real-time discovery updates rather than relying purely on a polling interval.
- **The trade-off is operational complexity**: ZooKeeper requires a carefully-managed ensemble (an odd number of nodes for quorum) and has its own tuning considerations (session timeouts, watch management) — introducing it purely for Spring service discovery, without other existing uses, is a heavier operational commitment than Eureka for that narrow purpose alone.

## 3. Core concept

Recall the ZooKeeper lock discussion from [Spring Cloud Cluster](0534-spring-cloud-cluster-zookeeper-redis-locks.md): ephemeral znodes tied to a session, released promptly the moment that session drops. Service discovery via ZooKeeper applies the exact same underlying primitive to a different purpose — instead of one znode representing "who holds this lock," many znodes under a shared path represent "which instances of this service are currently alive," each one ephemeral and tied to its owning instance's session, so the registry's contents are always a live, accurate reflection of which sessions are actually still connected, with no separate heartbeat mechanism needed on top.

Concretely:

1. **On startup, a service instance creates an ephemeral znode** under a path like `/services/order-service/instance-1`, containing its address — this znode exists exactly as long as the instance's ZooKeeper session remains active.
2. **If the instance crashes or loses connectivity**, its ZooKeeper session eventually times out (based on the configured session timeout), and ZooKeeper automatically deletes the ephemeral znode — no explicit deregistration call, and no heartbeat-miss threshold to configure separately from the session timeout itself.
3. **A calling service watches the parent path** (`/services/order-service`) for changes to its children — when an instance's znode disappears (or a new one appears), ZooKeeper pushes a notification to watching clients, rather than the client needing to poll on an interval.
4. **Spring Cloud Zookeeper's `DiscoveryClient` implementation wraps this watch-and-query mechanism** behind the same standard interface — application code depending on `DiscoveryClient` needs zero changes moving from Eureka or Consul to ZooKeeper.

## 4. Diagram

<svg viewBox="0 0 660 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Instances register as ephemeral znodes tied to their session; ZooKeeper deletes the znode automatically on session loss and pushes a watch notification to observing clients">
  <rect x="20" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance ephemeral znode</text>

  <rect x="260" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ZooKeeper ensemble</text>

  <rect x="500" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="570" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">watching caller</text>

  <line x1="200" y1="80" x2="260" y2="80" stroke="#8b949e" marker-end="url(#a14)"/>
  <line x1="440" y1="80" x2="500" y2="80" stroke="#8b949e" marker-end="url(#a14)"/>
  <text x="330" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">session drops -&gt; znode auto-deleted -&gt; watch notification pushed instantly</text>
  <defs><marker id="a14" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

Session-tied ephemeral znodes and push-based watches give near-instant registry updates without a separate heartbeat or polling mechanism.

## 5. Runnable example

Scenario: an instance whose session drops, and a watching caller reacting to it. We start with a plain Java model of polling-based discovery, extend it to a watch/notification model, then show the real Spring Cloud Zookeeper configuration.

### Level 1 — Basic

```java
// File: PollingDiscoveryModel.java -- models POLLING-based discovery:
// the caller must ask "what's changed?" on an interval -- there's a
// window between an actual change and the caller noticing it.
import java.util.*;

public class PollingDiscoveryModel {
    static List<String> registeredInstances = new ArrayList<>(List.of("10.0.5.2:8080", "10.0.5.9:8080"));

    static void pollAndCheck(int pollNumber) {
        System.out.println("Poll #" + pollNumber + ": current instances = " + registeredInstances);
    }

    public static void main(String[] args) {
        pollAndCheck(1);
        registeredInstances.remove("10.0.5.9:8080"); // instance crashes RIGHT AFTER poll #1
        // poll #2 doesn't happen until the next scheduled interval -- there's a GAP where the caller doesn't know yet
        System.out.println("... waiting for next poll interval ...");
        pollAndCheck(2); // only NOW does the caller notice
    }
}
```

How to run: `java PollingDiscoveryModel.java`

`pollAndCheck` only reflects reality at the moment it's called — between poll #1 and poll #2, the caller has no idea `10.0.5.9:8080` is already gone, a real (if often small) staleness window inherent in any polling-based discovery approach.

### Level 2 — Intermediate

```java
// File: WatchNotificationModel.java -- models ZooKeeper's PUSH-based
// watch mechanism: the caller is notified IMMEDIATELY when a change
// happens, with no polling interval or staleness window.
import java.util.*;
import java.util.function.Consumer;

public class WatchNotificationModel {
    static List<String> registeredInstances = new ArrayList<>(List.of("10.0.5.2:8080", "10.0.5.9:8080"));
    static List<Consumer<List<String>>> watchers = new ArrayList<>();

    static void watch(Consumer<List<String>> callback) { watchers.add(callback); }

    static void removeInstance(String address) {
        registeredInstances.remove(address);
        System.out.println("Instance " + address + " removed -- PUSHING notification to all watchers immediately");
        watchers.forEach(w -> w.accept(new ArrayList<>(registeredInstances)));
    }

    public static void main(String[] args) {
        watch(current -> System.out.println("[watcher] notified: current instances = " + current));
        removeInstance("10.0.5.9:8080"); // notification fires IMMEDIATELY, no polling delay
    }
}
```

How to run: `java WatchNotificationModel.java`

`removeInstance` immediately invokes every registered watcher's callback the moment a change happens — there's no polling interval or staleness window at all, since the notification is pushed synchronously as part of the change itself, exactly mirroring how ZooKeeper's watch mechanism notifies clients the instant a znode they're watching changes.

### Level 3 — Advanced

```java
// File: SpringCloudZookeeperRealShape.java -- the REAL Spring Cloud
// Zookeeper shape: discovery-enabled application registering via
// ephemeral znodes, using the SAME DiscoveryClient abstraction.
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.web.bind.annotation.*;

public class SpringCloudZookeeperRealShape {

    @SpringBootApplication
    @EnableDiscoveryClient
    static class OrderServiceApplication {
        public static void main(String[] args) { SpringApplication.run(OrderServiceApplication.class, args); }
        // application.yml:
        //   spring.application.name: order-service
        //   spring.cloud.zookeeper.connect-string: zookeeper-1:2181,zookeeper-2:2181,zookeeper-3:2181
    }

    @RestController
    static class DiscoveryDebugController {
        private final DiscoveryClient discoveryClient; // the SAME abstraction, now backed by ZooKeeper
        DiscoveryDebugController(DiscoveryClient discoveryClient) { this.discoveryClient = discoveryClient; }

        @GetMapping("/debug/instances/{serviceName}")
        public Object instances(@PathVariable String serviceName) { return discoveryClient.getInstances(serviceName); }
    }
}
```

How to run: requires `spring-cloud-starter-zookeeper-discovery`, a running ZooKeeper ensemble, and `spring.cloud.zookeeper.connect-string` pointed at it; run via `mvn spring-boot:run` and kill an instance's process abruptly (simulating a crash) to observe `discoveryClient.getInstances(...)` reflecting the instance's removal almost immediately, once its ZooKeeper session times out — typically much faster than Eureka's default 90-second heartbeat-miss eviction window, depending on the configured ZooKeeper session timeout.

`DiscoveryDebugController` is identical in shape to the Eureka and Consul examples shown earlier — it depends purely on `DiscoveryClient`, unaware of ZooKeeper specifically; only the dependency (`spring-cloud-starter-zookeeper-discovery`) and connection configuration differ from an Eureka- or Consul-backed setup.

## 6. Walkthrough

Trace what happens when an `order-service` instance's process crashes abruptly, with ZooKeeper-backed discovery configured:

1. **The instance's ephemeral znode (created at startup under a path like `/services/order-service/instance-1`) remains present in ZooKeeper** as long as its session stays active — a crash doesn't immediately delete anything, since ZooKeeper first needs to detect the session is no longer alive.
2. **ZooKeeper's session-timeout mechanism detects the session has gone silent** (no heartbeat/ping from the crashed instance within the configured session timeout, often a few seconds to tens of seconds depending on configuration) and expires the session.
3. **Upon session expiration, ZooKeeper automatically deletes every ephemeral znode owned by that session** — including this instance's registration znode.
4. **Any client with an active watch on the parent path `/services/order-service` receives a push notification immediately**, since a child of the watched path changed (in this case, was removed).
5. **Spring Cloud Zookeeper's `DiscoveryClient` implementation, having registered such a watch, updates its internal view of `order-service`'s instances** in response to this notification — a subsequent `getInstances("order-service")` call correctly excludes the crashed instance, reflecting the removal essentially as soon as ZooKeeper itself detected the session loss, rather than waiting for a separate polling interval to elapse.

## 7. Gotchas & takeaways

> **Gotcha:** ZooKeeper's session timeout is a single, cluster-wide tuning knob that trades false-positive risk against detection speed — set too short, a brief network blip (not an actual crash) can cause a healthy instance's session to expire and its registration to be wrongly removed; set too long, actual crashes take longer to be reflected in discovery results. Tune this value deliberately rather than leaving it at a default that may not suit your network's actual characteristics.

- ZooKeeper's session-tied ephemeral znodes and push-based watches give near-instant discovery updates on instance failure, without a separate heartbeat mechanism or polling interval.
- Reaching for ZooKeeper-backed discovery makes the most sense when ZooKeeper is already operated in your infrastructure for other reasons — introducing it purely for this purpose is a heavier operational commitment than Eureka.
- Application code depending on `DiscoveryClient` requires zero changes moving between Eureka, Consul, and ZooKeeper — only the dependency and connection configuration differ.
- The session timeout is the key tuning parameter balancing false-positive risk (a network blip causing an unwarranted registration removal) against detection speed for genuine failures.
