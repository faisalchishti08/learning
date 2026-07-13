---
card: microservices
gi: 182
slug: service-registry-concept
title: "Service registry concept"
---

## 1. What it is

A service registry is a database of currently-available service instances and their network locations — each service instance registers itself (or is registered) when it starts up, and any other component that needs to call that service queries the registry to find out where a healthy instance currently lives, rather than relying on a fixed, hard-coded address. This is the foundational piece of infrastructure behind [gateway integration with service discovery](0179-gateway-integration-with-service-discovery.md) and behind service-to-service calls generally in a dynamic environment.

## 2. Why & when

Service instances in a modern deployment don't sit at fixed, permanent addresses — they scale up and down, get rescheduled across hosts, restart with new IP addresses — and any component hard-coding a specific address for a service it depends on will break the moment that address changes. A service registry solves this by being the single, continuously-updated source of truth for "what instances of this service currently exist and are healthy," letting every caller resolve a logical service name to a real, current address at the moment it actually needs to make a call, rather than trusting a stale, previously-known address.

Introduce a service registry as soon as backend service instances are dynamic — which describes virtually all containerized or auto-scaled deployments — and more than a trivial number of services need to locate each other. For a system with a small, fixed number of statically-addressed services, a registry adds operational complexity without a corresponding benefit; static configuration remains simpler in that specific case.

## 3. Core concept

Every service instance registers its network location (and often health status, metadata) with the registry on startup, and periodically confirms it's still alive; any component needing to call that service queries the registry by logical service name and receives back the current list of healthy, registered instances, choosing (or having chosen for it) which specific instance to actually call.

```java
// on startup: an instance REGISTERS itself with the registry
registry.register("order-service", new ServiceInstance("order-service-a1b2", "10.0.1.5", 8080));

// a caller QUERIES the registry by logical name, gets back CURRENT instances
List<ServiceInstance> instances = registry.getInstances("order-service");
// instances reflects whatever is TRUE right now, not whatever was true when the caller was written
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three order-service instances each register themselves with the service registry on startup; a caller queries the registry by the logical name 'order-service' and receives the current list of registered, healthy instance addresses" >
  <rect x="20" y="20" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="90" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-service-1</text>
  <rect x="20" y="80" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="90" y="100" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-service-2</text>
  <rect x="20" y="140" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="90" y="160" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-service-3</text>

  <rect x="250" y="65" width="150" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service Registry</text>
  <text x="325" y="106" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">3 instances registered</text>

  <rect x="480" y="80" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Caller (queries)</text>

  <line x1="160" y1="35" x2="248" y2="80" stroke="#8b949e" marker-end="url(#arr63)"/>
  <line x1="160" y1="95" x2="248" y2="95" stroke="#8b949e" marker-end="url(#arr63)"/>
  <line x1="160" y1="155" x2="248" y2="110" stroke="#8b949e" marker-end="url(#arr63)"/>
  <line x1="478" y1="95" x2="402" y2="95" stroke="#8b949e" marker-end="url(#arr63)"/>

  <defs>
    <marker id="arr63" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Every instance registers itself; every caller queries the same central registry to find current, real addresses.

## 5. Runnable example

Scenario: a caller trying to reach order-service instances that starts with a hard-coded address list (showing the staleness problem), introduces a service registry that instances register with and callers query dynamically, and finally demonstrates the registry staying accurate as instances start up and shut down over time, with callers always seeing a correct, current view.

### Level 1 — Basic

```java
// File: HardCodedAddressList.java -- a FIXED list of addresses; goes stale the
// instant any instance's address actually changes.
import java.util.*;

public class HardCodedAddressList {
    static List<String> knownAddresses = List.of("10.0.1.5:8080", "10.0.1.6:8080"); // baked in, NEVER updates

    public static void main(String[] args) {
        System.out.println("Caller believes order-service instances are: " + knownAddresses);
        System.out.println("If 10.0.1.6 was rescheduled to a NEW address an hour ago, this list has been WRONG for an hour, silently.");
    }
}
```

**How to run:** `javac HardCodedAddressList.java && java HardCodedAddressList` (JDK 17+).

### Level 2 — Intermediate

```java
// File: DynamicServiceRegistry.java -- instances REGISTER themselves; callers
// QUERY the registry, always getting the CURRENT, real state.
import java.util.*;

public class DynamicServiceRegistry {
    record ServiceInstance(String id, String host, int port) {}

    static class ServiceRegistry {
        Map<String, List<ServiceInstance>> registrations = new HashMap<>();
        void register(String serviceName, ServiceInstance instance) {
            registrations.computeIfAbsent(serviceName, k -> new ArrayList<>()).add(instance);
            System.out.println("[registry] " + instance.id() + " registered at " + instance.host() + ":" + instance.port());
        }
        List<ServiceInstance> getInstances(String serviceName) {
            return registrations.getOrDefault(serviceName, List.of());
        }
    }

    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();

        registry.register("order-service", new ServiceInstance("order-a", "10.0.1.5", 8080));
        registry.register("order-service", new ServiceInstance("order-b", "10.0.1.6", 8080));

        List<ServiceInstance> current = registry.getInstances("order-service"); // QUERIED, not hard-coded
        System.out.println("Caller queried the registry and got: " + current);
        System.out.println("This list came from the registry ITSELF, reflecting whatever is CURRENTLY registered.");
    }
}
```

**How to run:** `javac DynamicServiceRegistry.java && java DynamicServiceRegistry` (JDK 17+).

Expected output:
```
[registry] order-a registered at 10.0.1.5:8080
[registry] order-b registered at 10.0.1.6:8080
Caller queried the registry and got: [ServiceInstance[id=order-a, host=10.0.1.5, port=8080], ServiceInstance[id=order-b, host=10.0.1.6, port=8080]]
This list came from the registry ITSELF, reflecting whatever is CURRENTLY registered.
```

### Level 3 — Advanced

```java
// File: RegistryStaysAccurateOverTime.java -- instances START UP, SHUT DOWN,
// and RESTART at NEW addresses; the registry (and every fresh query against it)
// stays accurate throughout, with NO caller-side changes needed.
import java.util.*;

public class RegistryStaysAccurateOverTime {
    record ServiceInstance(String id, String host, int port) {}

    static class ServiceRegistry {
        Map<String, List<ServiceInstance>> registrations = new HashMap<>();
        void register(String serviceName, ServiceInstance instance) {
            registrations.computeIfAbsent(serviceName, k -> new ArrayList<>()).add(instance);
        }
        void deregister(String serviceName, String instanceId) {
            registrations.get(serviceName).removeIf(i -> i.id().equals(instanceId));
        }
        List<ServiceInstance> getInstances(String serviceName) { return registrations.getOrDefault(serviceName, List.of()); }
    }

    static void printCurrentState(ServiceRegistry registry, String label) {
        System.out.println(label + ": " + registry.getInstances("order-service").stream().map(ServiceInstance::id).toList());
    }

    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();

        registry.register("order-service", new ServiceInstance("order-a", "10.0.1.5", 8080));
        printCurrentState(registry, "t=0, after order-a starts");

        registry.register("order-service", new ServiceInstance("order-b", "10.0.1.6", 8080));
        printCurrentState(registry, "t=1, after order-b starts (scale-up)");

        registry.deregister("order-service", "order-a");
        printCurrentState(registry, "t=2, after order-a shuts down");

        registry.register("order-service", new ServiceInstance("order-a", "10.0.1.99", 8080)); // order-a restarts at a NEW address
        printCurrentState(registry, "t=3, after order-a restarts at a NEW address");

        System.out.println("\nEvery printCurrentState() call QUERIED the registry FRESH -- no caller ever had a stale, cached address list.");
    }
}
```

**How to run:** `javac RegistryStaysAccurateOverTime.java && java RegistryStaysAccurateOverTime` (JDK 17+).

Expected output:
```
t=0, after order-a starts: [order-a]
t=1, after order-b starts (scale-up): [order-a, order-b]
t=2, after order-a shuts down: [order-b]
t=3, after order-a restarts at a NEW address: [order-b, order-a]

Every printCurrentState() call QUERIED the registry FRESH -- no caller ever had a stale, cached address list.
```

## 6. Walkthrough

1. **Level 1** — `knownAddresses` is a fixed `List.of(...)` constructed once and never revisited; the printed comment makes explicit that if the real-world state behind these addresses has since changed, this list has silently become wrong with no mechanism to notice or correct it.
2. **Level 2, registration as an explicit action** — `registry.register(serviceName, instance)` is called once per instance at what represents that instance's own startup, adding it to `registrations`' list for that service name.
3. **Level 2, querying instead of hard-coding** — `registry.getInstances("order-service")` is called by what represents the caller, retrieving whatever is currently present in `registrations` for that key — the caller's code contains no addresses of its own at all.
4. **Level 2, the result reflecting live registry state** — the printed `current` list contains exactly the two instances that were registered moments earlier, demonstrating that the caller's view is derived entirely from the registry's own state, not from any value baked into the caller.
5. **Level 3, four snapshots across a changing timeline** — `printCurrentState` is called after each of four state-changing events (a startup, a scale-up, a shutdown, and a restart-at-a-new-address), and each call independently queries `registry.getInstances(...)` fresh, rather than reusing any previously retrieved list.
6. **Level 3, tracing the sequence** — at `t=0`, only `order-a` is registered; at `t=1`, `order-b` joins, and both appear; at `t=2`, `order-a` is deregistered (simulating a shutdown), leaving only `order-b`; at `t=3`, `order-a` re-registers under the same `id` but a different `host` (`"10.0.1.99"`, simulating a restart at a new address after rescheduling), and it reappears in the query result.
7. **Level 3, the concluding point verified by the trace** — every one of the four `printCurrentState` calls used the identical query pattern (`registry.getInstances("order-service")`), yet each returned a different, correct answer reflecting the registry's state *at that exact moment* — this is the concrete mechanism by which a service registry keeps every caller's view of "where are the current instances of this service" accurate over time, without any caller needing to be aware of, or react specifically to, any individual registration or deregistration event.

## 7. Gotchas & takeaways

> **Gotcha:** a service registry itself becomes critical shared infrastructure that every service-to-service call in the system ultimately depends on — if the registry is unavailable or returns stale data, service discovery for the *entire* system can be affected simultaneously; registries are typically designed and deployed with their own [high availability and replication](0193-service-registry-high-availability-replication.md) strategy specifically because of this outsized blast radius.

- A service registry is the continuously-updated source of truth for which instances of a given service currently exist and are healthy, replacing hard-coded, static addresses.
- Instances register themselves (or are registered) on startup; callers query the registry by logical service name to get the current set of healthy instances, resolved at the moment of need rather than baked in ahead of time.
- This is essential in any environment with dynamic service instances — scaling, rescheduling, restarting at new addresses — since static configuration would need constant manual updates to remain correct.
- The registry stays accurate over time purely because every query reflects the registry's current state; no caller needs to be individually notified of specific registration or deregistration events to benefit from this accuracy.
- Because the registry becomes critical, load-bearing shared infrastructure for the entire system's service-to-service communication, it requires its own dedicated high-availability design, not just ordinary service-level reliability.
