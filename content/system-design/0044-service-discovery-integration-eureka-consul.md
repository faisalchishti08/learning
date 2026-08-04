---
card: system-design
gi: 44
slug: service-discovery-integration-eureka-consul
title: "Service discovery integration (Eureka / Consul)"
---

## 1. What it is

**Service discovery** is the mechanism that lets services in a distributed system find each other's current network locations automatically, instead of relying on hardcoded, fixed addresses. A **service registry** — commonly **Eureka** (from Netflix, tightly integrated with Spring Cloud) or **Consul** (a more general-purpose tool with additional features like health checking and configuration management) — is the central component services register themselves with, and query, to find each other.

## 2. Why & when

In a microservices architecture, service instances come and go constantly: they scale up and down, restart after deployments, or move to new hosts. Hardcoding IP addresses would break immediately the first time any instance changed location. Service discovery is the piece of infrastructure that makes both client-side load balancing (covered in the previous tutorial) and dynamic scaling possible — every mechanism that needs to know "which instances of this service are currently alive" depends on it. It is a foundational piece of essentially every non-trivial microservices design.

## 3. Core concept

**The two core actions every service registry supports:**

1. **Registration:** when a service instance starts up, it registers itself with the registry, announcing its service name and network address (e.g. "`order-service` is running at `10.0.1.5:8080`").
2. **Discovery (lookup):** when another service wants to call `order-service`, it asks the registry for the current list of healthy instances, rather than using a fixed address.

**Keeping the registry accurate — heartbeats:** a registered instance periodically sends a **heartbeat** to the registry, confirming it is still alive. If the registry stops receiving heartbats from an instance within an expected time window, it removes that instance from the list of available instances — this is essentially a health-check mechanism built into the registry itself.

**Eureka vs Consul, briefly:**

| | Eureka | Consul |
|---|---|---|
| Origin / ecosystem | Netflix; deeply integrated with Spring Cloud | HashiCorp; broader ecosystem, not Spring-specific |
| Consistency model | Favors availability (AP) — may serve slightly stale data during a network partition | Supports strong consistency (via Raft) as well as availability trade-offs |
| Extra features | Focused primarily on service discovery | Also offers key-value configuration storage and more advanced health checking |

**How this connects to everything else in this section:** Spring Cloud LoadBalancer's `discoverInstances`-style lookup (simulated in the previous tutorial) is, in a real system, literally a call to Eureka or Consul. Spring Cloud Gateway's `lb://service-name` URIs resolve through this exact same registry. Service discovery is the shared foundation both of those tutorials' mechanisms are actually built on.

## 4. Diagram

```
 order-service instance starts up
        |
        v
 registers with Service Registry (Eureka/Consul): "order-service @ 10.0.1.5:8080"
        |
        | sends heartbeat every N seconds -------> Registry
        |
 payment-service wants to call order-service:
        |
        v
 asks Registry: "who is order-service right now?"
        |
        v
 Registry returns: [10.0.1.5:8080, 10.0.1.6:8080]  (only instances with recent heartbeats)
```
*Caption: instances register themselves and send heartbeats; other services query the registry for the current, live instance list.*

## 5. Runnable example

### Artifact: a Java simulation of a service registry with registration, heartbeats, and stale-instance eviction

```java
import java.util.*;

public class ServiceRegistrySim {

    record Instance(String address, long lastHeartbeatSecond) {}

    static final Map<String, List<Instance>> registry = new HashMap<>();
    static final long HEARTBEAT_TIMEOUT_SECONDS = 30;

    static void register(String serviceName, String address, long nowSecond) {
        registry.computeIfAbsent(serviceName, s -> new ArrayList<>()).add(new Instance(address, nowSecond));
        System.out.println(address + " registered for " + serviceName + " at t=" + nowSecond);
    }

    static void heartbeat(String serviceName, String address, long nowSecond) {
        List<Instance> instances = registry.get(serviceName);
        for (int i = 0; i < instances.size(); i++) {
            if (instances.get(i).address().equals(address)) {
                instances.set(i, new Instance(address, nowSecond));
            }
        }
    }

    static List<String> discover(String serviceName, long nowSecond) {
        List<Instance> instances = registry.getOrDefault(serviceName, List.of());
        List<String> alive = new ArrayList<>();
        for (Instance inst : instances) {
            if (nowSecond - inst.lastHeartbeatSecond() <= HEARTBEAT_TIMEOUT_SECONDS) {
                alive.add(inst.address());
            }
        }
        return alive;
    }

    public static void main(String[] args) {
        register("order-service", "10.0.1.5:8080", 0);
        register("order-service", "10.0.1.6:8080", 0);

        heartbeat("order-service", "10.0.1.5:8080", 20); // this instance stays healthy
        // 10.0.1.6:8080 sends NO further heartbeat -- it will go stale.

        System.out.println("Discover at t=25: " + discover("order-service", 25));
        System.out.println("Discover at t=40: " + discover("order-service", 40)); // .6 now stale, dropped
    }
}
```

**How to run:** save as `ServiceRegistrySim.java`, run `java ServiceRegistrySim.java` (JDK 17+). A real system uses Eureka or Consul directly, with clients registering and querying via those tools' APIs (often handled automatically by `spring-cloud-starter-netflix-eureka-client` in a Spring Boot app) rather than a hand-rolled registry.

## 6. Walkthrough

1. `registry` maps a service name to its list of known `Instance`s, each tracking its address and the timestamp of its last heartbeat.
2. `register` adds a new instance entry when it first starts up, recording the current time as its initial heartbeat.
3. `heartbeat` updates an existing instance's `lastHeartbeatSecond`, simulating it periodically confirming it is still alive.
4. `discover` filters the registered instances down to only those whose last heartbeat is within `HEARTBEAT_TIMEOUT_SECONDS`, dropping any instance that has gone quiet for too long.
5. `main` registers two instances at t=0, sends a heartbeat for only the first one at t=20, and then queries `discover` at two later times.
6. Output:
```
10.0.1.5:8080 registered for order-service at t=0
10.0.1.6:8080 registered for order-service at t=0
Discover at t=25: [10.0.1.5:8080, 10.0.1.6:8080]
Discover at t=40: [10.0.1.5:8080]
```
7. At t=25, both instances are still within the 30-second timeout window (`.6`'s last heartbeat was at t=0, so 25 seconds have passed — still under 30). At t=40, `.6`'s last heartbeat is now 40 seconds old, past the timeout, so it is correctly dropped from the discoverable list — exactly the self-healing behavior a real service registry provides when an instance silently dies without deregistering.

## 7. Gotchas & takeaways

> **Gotcha:** setting the heartbeat timeout too short. A brief network blip or garbage-collection pause can cause a perfectly healthy instance to miss one heartbeat and be prematurely evicted from the registry, needlessly reducing available capacity — tune the timeout to tolerate normal, brief operational hiccups.

- Service discovery lets instances register themselves and lets other services look up the current, live list, instead of relying on hardcoded addresses.
- Heartbeats are how the registry detects instances that silently died without explicitly deregistering.
- Eureka integrates tightly with Spring Cloud; Consul offers a broader feature set (configuration storage, stronger consistency options) at the cost of being less Spring-specific.
