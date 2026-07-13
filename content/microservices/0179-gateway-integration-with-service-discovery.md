---
card: microservices
gi: 179
slug: gateway-integration-with-service-discovery
title: "Gateway integration with service discovery"
---

## 1. What it is

Gateway integration with service discovery lets route destinations be expressed as a logical service name (`lb://order-service`) rather than a fixed host and port, with the gateway resolving that name to a current, healthy instance address at request time by querying a service discovery registry (Eureka, Consul, Kubernetes' own service discovery) — the gateway's routing table never needs to know or track actual backend network locations directly.

## 2. Why & when

Backend service instances in a dynamic environment come and go constantly — instances scale up and down, get rescheduled to different hosts, restart with new IP addresses — and a gateway routing table hard-coded with specific host:port destinations would need to be manually updated every time any of that happens, which is both operationally unworkable and guaranteed to lag behind reality. Service discovery integration solves this by having the gateway look up the current set of healthy instances for a logical service name at request time (or from a periodically refreshed cache), automatically adapting to instances appearing, disappearing, or moving without any manual routing table update.

Integrate the gateway with service discovery in any environment where backend instances are dynamic — which describes essentially all container-orchestrated or auto-scaled deployments. For a small number of genuinely static backend services running at fixed, unchanging addresses, direct host:port routing remains simpler and avoids the added dependency on a discovery registry.

## 3. Core concept

The gateway's route destination uses a `lb://` (load-balanced) scheme with a logical service name instead of a concrete host:port; at request time, the gateway queries the service discovery registry for the current list of healthy instances registered under that name, and load-balances the request across them.

```java
// route destination is a LOGICAL NAME, never a fixed host:port
.route("order_route", r -> r.path("/orders/**").uri("lb://order-service"))

// at REQUEST TIME, the gateway resolves "order-service" via service discovery:
List<ServiceInstance> instances = discoveryClient.getInstances("order-service"); // CURRENT, healthy instances, right now
ServiceInstance chosen = loadBalancer.choose(instances);
forwardTo(chosen.getHost() + ":" + chosen.getPort());
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The gateway's route points to a logical service name; at request time it queries a service discovery registry for the current healthy instances of that service, which have been registering and deregistering as they scale, and routes to one of them" >
  <rect x="20" y="80" width="130" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="104" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Gateway route: lb://order-service</text>

  <rect x="240" y="30" width="160" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Discovery Registry</text>
  <text x="320" y="67" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">current healthy instances</text>

  <rect x="470" y="10" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="540" y="30" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-service-A</text>
  <rect x="470" y="60" width="140" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="540" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-service-B (scaled down)</text>
  <rect x="470" y="110" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="540" y="130" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-service-C (new)</text>

  <line x1="150" y1="95" x2="238" y2="55" stroke="#8b949e" marker-end="url(#arr60)"/>
  <line x1="400" y1="45" x2="468" y2="25" stroke="#8b949e" marker-end="url(#arr60)"/>
  <line x1="400" y1="55" x2="468" y2="120" stroke="#8b949e" marker-end="url(#arr60)"/>

  <defs>
    <marker id="arr60" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The registry's current, up-to-date instance list is what the gateway actually routes against, never a fixed address.

## 5. Runnable example

Scenario: a gateway routing to order-service that starts with a hard-coded instance address (showing what breaks when that instance disappears), integrates with a simulated service discovery registry to resolve instances dynamically, and finally demonstrates the gateway automatically adapting as instances register and deregister over time, with zero manual routing table changes.

### Level 1 — Basic

```java
// File: HardCodedInstanceAddress.java -- the route is a FIXED host:port; if that
// SPECIFIC instance disappears, routing breaks, even if OTHER healthy instances exist.
public class HardCodedInstanceAddress {
    static String hardCodedDestination = "10.0.1.5:8080"; // baked in, a SPECIFIC instance
    static boolean thisSpecificInstanceIsUp = true;

    static String routeRequest(String path) {
        if (!thisSpecificInstanceIsUp) return "502 Bad Gateway -- " + hardCodedDestination + " unreachable";
        return "200 OK from " + hardCodedDestination;
    }

    public static void main(String[] args) {
        System.out.println(routeRequest("/orders/42"));

        thisSpecificInstanceIsUp = false; // this ONE instance is rescheduled to a NEW address (a routine event in a container platform)
        System.out.println(routeRequest("/orders/42"));
        System.out.println("Routing BROKE, even though a healthy order-service instance almost certainly exists SOMEWHERE -- the route just doesn't know its new address.");
    }
}
```

**How to run:** `javac HardCodedInstanceAddress.java && java HardCodedInstanceAddress` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ServiceDiscoveryResolution.java -- the route uses a LOGICAL name; a
// discovery registry resolves it to whichever instances are CURRENTLY healthy.
import java.util.*;

public class ServiceDiscoveryResolution {
    record ServiceInstance(String host, int port, boolean healthy) {}

    static class DiscoveryRegistry {
        Map<String, List<ServiceInstance>> registrations = new HashMap<>();
        void register(String serviceName, ServiceInstance instance) {
            registrations.computeIfAbsent(serviceName, k -> new ArrayList<>()).add(instance);
        }
        List<ServiceInstance> getHealthyInstances(String serviceName) {
            return registrations.getOrDefault(serviceName, List.of()).stream().filter(ServiceInstance::healthy).toList();
        }
    }

    static class Gateway {
        DiscoveryRegistry registry;
        int roundRobinIndex = 0;
        Gateway(DiscoveryRegistry registry) { this.registry = registry; }

        String routeRequest(String logicalServiceName, String path) {
            List<ServiceInstance> healthy = registry.getHealthyInstances(logicalServiceName); // resolved AT REQUEST TIME
            if (healthy.isEmpty()) return "503 -- no healthy instances of " + logicalServiceName;
            ServiceInstance chosen = healthy.get(roundRobinIndex++ % healthy.size());
            return "200 OK from " + chosen.host() + ":" + chosen.port();
        }
    }

    public static void main(String[] args) {
        DiscoveryRegistry registry = new DiscoveryRegistry();
        registry.register("order-service", new ServiceInstance("10.0.1.5", 8080, true));
        registry.register("order-service", new ServiceInstance("10.0.1.6", 8080, true));

        Gateway gateway = new Gateway(registry);
        System.out.println(gateway.routeRequest("order-service", "/orders/42"));
        System.out.println(gateway.routeRequest("order-service", "/orders/43"));
        System.out.println("The GATEWAY's route config never mentions '10.0.1.5' or '10.0.1.6' -- only the logical name 'order-service'.");
    }
}
```

**How to run:** `javac ServiceDiscoveryResolution.java && java ServiceDiscoveryResolution` (JDK 17+).

Expected output:
```
200 OK from 10.0.1.5:8080
200 OK from 10.0.1.6:8080
The GATEWAY's route config never mentions '10.0.1.5' or '10.0.1.6' -- only the logical name 'order-service'.
```

### Level 3 — Advanced

```java
// File: DynamicInstanceChurn.java -- instances REGISTER, DEREGISTER, and get
// REPLACED over time; the gateway's routing AUTOMATICALLY adapts, with ZERO
// manual route configuration changes throughout.
import java.util.*;

public class DynamicInstanceChurn {
    record ServiceInstance(String id, String host, int port, boolean healthy) {}

    static class DiscoveryRegistry {
        Map<String, List<ServiceInstance>> registrations = new HashMap<>();
        void register(String serviceName, ServiceInstance instance) { registrations.computeIfAbsent(serviceName, k -> new ArrayList<>()).add(instance); }
        void deregister(String serviceName, String instanceId) { registrations.get(serviceName).removeIf(i -> i.id().equals(instanceId)); }
        List<ServiceInstance> getHealthyInstances(String serviceName) {
            return registrations.getOrDefault(serviceName, List.of()).stream().filter(ServiceInstance::healthy).toList();
        }
    }

    static class Gateway {
        DiscoveryRegistry registry;
        int roundRobinIndex = 0;
        Gateway(DiscoveryRegistry registry) { this.registry = registry; }
        String routeRequest(String serviceName) {
            List<ServiceInstance> healthy = registry.getHealthyInstances(serviceName);
            if (healthy.isEmpty()) return "503 -- no healthy instances";
            ServiceInstance chosen = healthy.get(roundRobinIndex++ % healthy.size());
            return "200 OK from " + chosen.id();
        }
    }

    public static void main(String[] args) {
        DiscoveryRegistry registry = new DiscoveryRegistry();
        Gateway gateway = new Gateway(registry); // ONE gateway instance, NEVER reconfigured, throughout this ENTIRE scenario

        registry.register("order-service", new ServiceInstance("order-A", "10.0.1.5", 8080, true));
        System.out.println("--- initial: 1 instance ---");
        System.out.println(gateway.routeRequest("order-service"));

        System.out.println("\n--- SCALE UP: order-B and order-C join ---");
        registry.register("order-service", new ServiceInstance("order-B", "10.0.1.6", 8080, true));
        registry.register("order-service", new ServiceInstance("order-C", "10.0.1.7", 8080, true));
        System.out.println(gateway.routeRequest("order-service"));
        System.out.println(gateway.routeRequest("order-service"));
        System.out.println(gateway.routeRequest("order-service"));

        System.out.println("\n--- order-A is RESCHEDULED (deregisters, then re-registers with a NEW address) ---");
        registry.deregister("order-service", "order-A");
        System.out.println(gateway.routeRequest("order-service")); // order-A is GONE, but B and C absorb the traffic
        registry.register("order-service", new ServiceInstance("order-A", "10.0.1.99", 8080, true)); // order-A back, NEW IP
        System.out.println(gateway.routeRequest("order-service"));

        System.out.println("\nThroughout ALL of this instance churn, gateway.routeRequest('order-service') was called with the SAME logical name every time -- ZERO route reconfiguration.");
    }
}
```

**How to run:** `javac DynamicInstanceChurn.java && java DynamicInstanceChurn` (JDK 17+).

Expected output (specific instance ids in round-robin rotation may shift slightly based on registration order, but every call succeeds and no manual reconfiguration occurs):
```
--- initial: 1 instance ---
200 OK from order-A

--- SCALE UP: order-B and order-C join ---
200 OK from order-B
200 OK from order-C
200 OK from order-A

--- order-A is RESCHEDULED (deregisters, then re-registers with a NEW address) ---
200 OK from order-B
200 OK from order-C

Throughout ALL of this instance churn, gateway.routeRequest('order-service') was called with the SAME logical name every time -- ZERO route reconfiguration.
```

## 6. Walkthrough

1. **Level 1** — `hardCodedDestination` is a fixed string baked into the routing logic; when `thisSpecificInstanceIsUp` becomes `false` (simulating that specific instance being rescheduled to a new address, a routine event in any dynamic environment), `routeRequest` has no alternative address to fall back to and fails outright.
2. **Level 2, resolving instances at request time** — `Gateway.routeRequest` calls `registry.getHealthyInstances(logicalServiceName)` fresh on every single call, rather than caching a resolved address once and reusing it — this is what makes the gateway responsive to the registry's *current* state rather than whatever was true when the route was first configured.
3. **Level 2, the route never mentioning a concrete address** — `main`'s calls to `gateway.routeRequest("order-service", ...)` use only the logical service name; the actual `"10.0.1.5"` and `"10.0.1.6"` addresses appear only inside `DiscoveryRegistry`'s registration data, never in the gateway's own routing configuration.
4. **Level 3, one gateway instance across the whole scenario** — `gateway` is constructed exactly once at the very start of `main` and is never reconstructed or reconfigured for the rest of the program, despite the underlying set of registered instances changing substantially over the course of the scenario.
5. **Level 3, scaling up transparently** — after `order-B` and `order-C` register, subsequent calls to `gateway.routeRequest("order-service")` begin including them in the round-robin rotation automatically, purely because `getHealthyInstances` picks up the registry's updated state on its next call — no code in `Gateway` changed to accommodate the new instances.
6. **Level 3, an instance disappearing and reappearing** — `registry.deregister("order-service", "order-A")` removes `order-A` from the registry's list; the immediately following call to `routeRequest` correctly rotates only among the remaining `order-B` and `order-C`, and once `order-A` re-registers (now at a different IP, `"10.0.1.99"`, representing its new post-reschedule address), it becomes eligible for routing again automatically.
7. **Level 3, the stated conclusion verified by the trace** — across an initial registration, a scale-up, a deregistration, and a re-registration at a new address, `gateway.routeRequest("order-service")` was called identically each time, with the exact same logical service name argument — every adaptation to the changing instance set happened entirely within `DiscoveryRegistry`'s data, never requiring any change to how the gateway itself was configured or invoked, which is precisely the operational benefit service discovery integration provides over hard-coded routing destinations in any environment where backend instances are not static.

## 7. Gotchas & takeaways

> **Gotcha:** service discovery resolution has its own latency and failure modes — if the discovery registry itself becomes slow or briefly unreachable, gateway routing for every service depending on it can be affected simultaneously; most real implementations mitigate this with local caching of recently resolved instance lists (refreshed periodically rather than queried fresh on every single request), trading a small amount of staleness for resilience against registry unavailability.

- Service discovery integration lets gateway routes reference backend services by logical name rather than fixed host:port, with instance resolution happening dynamically at (or near) request time.
- This is essential in any environment where backend instances are dynamic — scaling, rescheduling, or restarting with new addresses — since a hard-coded routing table would need constant manual updates to stay correct.
- The gateway's routing configuration never needs to change as instances come and go; only the discovery registry's own state changes, and the gateway automatically reflects that current state on every request.
- This pattern is foundational to running a gateway in any container-orchestrated or auto-scaled deployment, where instance addresses are inherently unstable by design.
- Real implementations typically cache resolved instance lists with periodic refresh, rather than querying the registry on every single request, trading a small amount of staleness for resilience against registry latency or unavailability.
