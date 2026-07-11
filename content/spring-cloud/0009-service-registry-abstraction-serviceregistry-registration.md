---
card: spring-cloud
gi: 9
slug: service-registry-abstraction-serviceregistry-registration
title: "Service Registry abstraction (ServiceRegistry/Registration)"
---

## 1. What it is

`ServiceRegistry<R extends Registration>` is the Commons interface for the *write* side of service discovery — registering an application instance with a registry, updating its status, and deregistering it — mirroring `DiscoveryClient`'s role on the *read* side. `Registration` is the accompanying interface describing what's being registered: a service id, host, port, and metadata.

```java
@Autowired ServiceRegistry<Registration> serviceRegistry;
@Autowired Registration registration;

serviceRegistry.register(registration);   // announce this instance to the registry
serviceRegistry.setStatus(registration, "OUT_OF_SERVICE"); // temporarily mark unavailable
serviceRegistry.deregister(registration); // remove this instance from the registry
```

## 2. Why & when

The earlier Commons card covered `DiscoveryClient` — how a service *finds* other services. `ServiceRegistry` is the other half: how a service *announces itself* so others can find it. Every running instance of a Spring Cloud application is both a potential caller (using `DiscoveryClient`) and a potential callee (using `ServiceRegistry` to make itself discoverable) — most applications use this indirectly, through `@EnableDiscoveryClient` (a later card) auto-registering on startup, but understanding the underlying interface clarifies what's actually happening.

Reach for direct `ServiceRegistry` usage when:

- You need fine-grained control over registration timing — deliberately delaying registration until some internal warm-up or readiness check passes.
- Temporarily marking an instance as unavailable (`setStatus`) for a maintenance window, without fully deregistering and losing its registered metadata.
- Implementing custom lifecycle logic around graceful shutdown — deregistering cleanly before the process actually stops accepting connections.

## 3. Core concept

```
 interface Registration {
     String getServiceId();   -- e.g. "payment-service"
     String getHost();
     int getPort();
 }

 interface ServiceRegistry<R extends Registration> {
     void register(R registration);
     void deregister(R registration);
     void setStatus(R registration, String status);
     <T> T getStatus(R registration);
 }

 On startup:  serviceRegistry.register(thisInstance)   -- announce "I exist, here's how to reach me"
 On shutdown: serviceRegistry.deregister(thisInstance)  -- announce "I'm going away, stop routing to me"
```

`Registration` describes an instance's identity and location; `ServiceRegistry` is the operations that act on that description against the backing registry (Eureka, Consul, etc.).

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An application instance registers itself at startup and deregisters at shutdown, with a status update possible in between">
  <rect x="20" y="20" width="180" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">startup: register()</text>

  <line x1="200" y1="40" x2="260" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a29)"/>

  <rect x="270" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">running: setStatus()</text>

  <line x1="450" y1="40" x2="510" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a29)"/>

  <rect x="520" y="20" width="100" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">shutdown</text>

  <rect x="130" y="90" width="380" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">deregister() -- announces removal before the instance stops</text>
</svg>

An instance's lifecycle: register at startup, optionally change status while running, deregister before shutdown.

## 5. Runnable example

The scenario: a payment-service instance managing its own registry presence, evolving from a naive registry that has no concept of instance status, to a registry supporting register/deregister and status transitions, to a full graceful-shutdown sequence that deregisters *before* stopping actual traffic handling — the production-realistic ordering that avoids routing requests to an instance that's already going away.

### Level 1 — Basic

Model a bare registry supporting only registration, no status or deregistration — the limited baseline.

```java
import java.util.*;

public class ServiceRegistryLevel1 {
    public static void main(String[] args) {
        Registry registry = new Registry();
        Registration paymentInstance = new Registration("payment-service", "10.0.1.5", 8081);

        registry.register(paymentInstance);
        System.out.println("Registered instances: " + registry.instancesOf("payment-service"));
        // No way to mark this instance unavailable, or cleanly remove it -- it's registered forever.
    }
}

class Registration {
    String serviceId, host; int port;
    Registration(String serviceId, String host, int port) { this.serviceId = serviceId; this.host = host; this.port = port; }
    public String toString() { return host + ":" + port; }
}

class Registry {
    private final Map<String, List<Registration>> registrations = new HashMap<>();
    void register(Registration r) { registrations.computeIfAbsent(r.serviceId, k -> new ArrayList<>()).add(r); }
    List<Registration> instancesOf(String serviceId) { return registrations.getOrDefault(serviceId, List.of()); }
}
```

How to run: `java ServiceRegistryLevel1.java`

`Registry` only supports adding an instance — there's no way to remove it or mark it temporarily unavailable, which is exactly the gap `ServiceRegistry`'s `deregister`/`setStatus` operations fill.

### Level 2 — Intermediate

Add `deregister` and `setStatus`, modeling the full `ServiceRegistry` interface's operations.

```java
import java.util.*;

public class ServiceRegistryLevel2 {
    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();
        Registration paymentInstance = new Registration("payment-service", "10.0.1.5", 8081);

        registry.register(paymentInstance);
        System.out.println("After register: " + registry.instancesOf("payment-service"));

        registry.setStatus(paymentInstance, "OUT_OF_SERVICE"); // temporarily unavailable, still registered
        System.out.println("Status: " + registry.getStatus(paymentInstance));
        System.out.println("Still listed (but callers should check status): " + registry.instancesOf("payment-service"));

        registry.deregister(paymentInstance); // fully removed
        System.out.println("After deregister: " + registry.instancesOf("payment-service"));
    }
}

class Registration {
    String serviceId, host; int port;
    Registration(String serviceId, String host, int port) { this.serviceId = serviceId; this.host = host; this.port = port; }
    public String toString() { return host + ":" + port; }
}

// Stands in for org.springframework.cloud.client.serviceregistry.ServiceRegistry.
class ServiceRegistry {
    private final Map<String, List<Registration>> registrations = new HashMap<>();
    private final Map<Registration, String> statuses = new HashMap<>();

    void register(Registration r) {
        registrations.computeIfAbsent(r.serviceId, k -> new ArrayList<>()).add(r);
        statuses.put(r, "UP");
    }
    void deregister(Registration r) {
        registrations.getOrDefault(r.serviceId, List.of()).remove(r);
        statuses.remove(r);
    }
    void setStatus(Registration r, String status) { statuses.put(r, status); }
    String getStatus(Registration r) { return statuses.get(r); }
    List<Registration> instancesOf(String serviceId) { return registrations.getOrDefault(serviceId, List.of()); }
}
```

How to run: `java ServiceRegistryLevel2.java`

`setStatus` changes an instance's status without removing it from the registry entirely — a well-behaved caller (typically the load balancer, covered in a later card) checks status and skips `OUT_OF_SERVICE` instances, while `deregister` fully removes the registration once the instance is genuinely gone.

### Level 3 — Advanced

Model a graceful shutdown sequence: deregister from the registry *before* stopping the instance's actual request handling, so no new traffic is routed to an instance that's already winding down — the production-correct ordering.

```java
import java.util.*;

public class ServiceRegistryLevel3 {
    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();
        PaymentServiceInstance instance = new PaymentServiceInstance(registry, "10.0.1.5", 8081);

        instance.startup();
        System.out.println("Registered and serving: " + registry.instancesOf("payment-service"));
        System.out.println("Handling a request: " + instance.handleRequest());

        instance.gracefulShutdown(); // deregisters FIRST, THEN stops handling requests
        System.out.println("After graceful shutdown, registry shows: " + registry.instancesOf("payment-service"));
    }
}

class Registration {
    String serviceId, host; int port;
    Registration(String serviceId, String host, int port) { this.serviceId = serviceId; this.host = host; this.port = port; }
    public String toString() { return host + ":" + port; }
}

class ServiceRegistry {
    private final Map<String, List<Registration>> registrations = new HashMap<>();
    void register(Registration r) { registrations.computeIfAbsent(r.serviceId, k -> new ArrayList<>()).add(r); }
    void deregister(Registration r) { registrations.getOrDefault(r.serviceId, List.of()).remove(r); }
    List<Registration> instancesOf(String serviceId) { return registrations.getOrDefault(serviceId, List.of()); }
}

class PaymentServiceInstance {
    private final ServiceRegistry registry;
    private final Registration registration;
    private boolean acceptingRequests = false;

    PaymentServiceInstance(ServiceRegistry registry, String host, int port) {
        this.registry = registry;
        this.registration = new Registration("payment-service", host, port);
    }

    void startup() {
        acceptingRequests = true; // start serving FIRST
        registry.register(registration); // THEN announce -- avoid being discoverable before ready to serve
    }

    String handleRequest() {
        return acceptingRequests ? "processed" : "rejected -- not accepting requests";
    }

    void gracefulShutdown() {
        registry.deregister(registration); // deregister FIRST -- stop NEW traffic from being routed here
        // In a real deployment: wait for IN-FLIGHT requests to drain here, THEN:
        acceptingRequests = false; // stop accepting entirely, only after deregistration has had time to propagate
    }
}
```

How to run: `java ServiceRegistryLevel3.java`

`gracefulShutdown` deliberately calls `registry.deregister` *before* flipping `acceptingRequests` to `false` — in a real deployment, callers using stale discovery data (cached briefly before the deregistration propagates) might still send a request or two during this window, so `acceptingRequests` is only flipped off after giving the deregistration time to take effect elsewhere, avoiding a hard cutoff that would reject requests still in flight from callers who hadn't yet learned this instance is going away.

## 6. Walkthrough

Execution starts in `main` for Level 3. `instance.startup()` sets `acceptingRequests = true` first, then registers — this ordering matters in a real deployment too: an instance shouldn't be discoverable before it's actually ready to serve requests (usually gated by a readiness check, not just this simple flag).

`instance.handleRequest()` returns `"processed"` since `acceptingRequests` is `true`:

```
Registered and serving: [10.0.1.5:8081]
Handling a request: processed
```

`instance.gracefulShutdown()` calls `registry.deregister` first — removing the instance from `registrations` immediately — and only afterward sets `acceptingRequests = false`. The final registry check confirms the instance no longer appears:

```
After graceful shutdown, registry shows: []
```

In a real Spring Cloud application, this deregister-before-stop-serving ordering is precisely what avoids a race condition during rolling deployments: if an instance stopped accepting requests *before* deregistering, any caller that had already cached its address (from a `DiscoveryClient` lookup moments earlier) could still route a request to it and get a connection refused — deregistering first, then giving the change time to propagate before actually stopping, minimizes that window.

## 7. Gotchas & takeaways

> Gotcha: registry deregistration on shutdown isn't instantaneous from other services' point of view — most discovery clients cache the instance list locally and refresh it periodically, meaning even a clean deregistration can leave a brief window where other services still route traffic to an instance that's already stopped serving; graceful shutdown logic needs to account for this propagation delay, not assume deregistration is immediately visible everywhere.

> Gotcha: most applications never call `ServiceRegistry` methods directly — `@EnableDiscoveryClient` (a later card) wires up automatic registration on startup and deregistration on shutdown via Spring's lifecycle hooks; reaching for the raw `ServiceRegistry` API directly is usually only needed for custom lifecycle logic (delayed registration, temporary status changes) beyond what the automatic wiring provides.

- `ServiceRegistry`/`Registration` are the Commons interfaces for the write side of service discovery — announcing, updating the status of, and removing an instance from the registry.
- `setStatus` allows temporarily marking an instance unavailable without fully deregistering it, useful for maintenance windows.
- Deregistering before stopping request handling (rather than the reverse) minimizes the window where other services route traffic to an instance that's already going away.
- Most applications rely on `@EnableDiscoveryClient`'s automatic registration/deregistration rather than calling `ServiceRegistry` directly — direct usage is for custom lifecycle needs beyond the default behavior.
