---
card: microservices
gi: 97
slug: client-side-load-balancing-vs-server-side
title: "Client-side load balancing vs server-side"
---

## 1. What it is

When a service calls another service that has multiple running instances, something has to decide which instance handles each call. **Server-side load balancing** puts that decision in a dedicated component the caller talks to — a load balancer or reverse proxy sitting between caller and callees, which the caller doesn't need to know the individual instance addresses of at all. **Client-side load balancing** puts that decision in the caller itself: the caller fetches the current list of available instances (typically from a service registry) and picks one directly, with no intermediary component in the request path at all.

## 2. Why & when

Server-side load balancing keeps callers simple — they call one stable address, and the load balancer handles routing, health checks, and instance changes entirely transparently. But every request now makes an extra network hop through the load balancer, and the load balancer itself becomes a shared piece of infrastructure that needs its own scaling and availability story. Client-side load balancing removes that extra hop — the caller talks directly to the chosen instance — and avoids a single shared load balancer becoming a bottleneck or single point of failure, at the cost of pushing more responsibility (instance list awareness, selection logic, handling instance failures) into every single calling service.

Server-side load balancing is the simpler default and fits most systems well, especially given how thoroughly it fits standard reverse-proxy/load-balancer infrastructure (which most systems need at their edge anyway). Client-side load balancing is worth the added complexity specifically in high-throughput internal service meshes where the extra network hop's latency genuinely matters, or where avoiding a centralized load balancer as a scaling bottleneck is a real, measured concern.

## 3. Core concept

The decision of *which instance* moves from a shared intermediary (server-side) to the caller itself (client-side); both still need an up-to-date list of healthy instances to choose from.

```
SERVER-SIDE:   Client -> Load Balancer -> picks instance -> Instance B
               (client only ever talks to the load balancer's address)

CLIENT-SIDE:   Client -> fetches instance list -> picks instance itself -> Instance B directly
               (client talks DIRECTLY to whichever instance it picked)
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Server-side load balancing routes every client call through a shared load balancer that picks an instance; client-side load balancing has each client fetch the instance list and connect directly to its chosen instance">
  <text x="150" y="18" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Server-side</text>
  <rect x="20" y="30" width="90" height="35" rx="4" fill="#1c2430" stroke="#8b949e"/><text x="65" y="52" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="160" y="30" width="110" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="215" y="52" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Load Balancer</text>
  <rect x="320" y="10" width="90" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="365" y="30" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Instance A</text>
  <rect x="320" y="55" width="90" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="365" y="75" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Instance B</text>
  <line x1="110" y1="48" x2="160" y2="48" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="270" y1="40" x2="320" y2="25" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="270" y1="55" x2="320" y2="70" stroke="#8b949e" stroke-width="1.5"/>

  <text x="490" y="118" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Client-side</text>
  <rect x="420" y="130" width="90" height="35" rx="4" fill="#1c2430" stroke="#8b949e"/><text x="465" y="152" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Client (picks itself)</text>
  <rect x="560" y="110" width="70" height="28" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="595" y="128" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="sans-serif">Instance A</text>
  <rect x="560" y="150" width="70" height="28" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="595" y="168" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="sans-serif">Instance B</text>
  <line x1="510" y1="148" x2="560" y2="164" stroke="#6db33f" stroke-width="1.5"/>
</svg>

Server-side adds a hop through a shared component; client-side connects directly, at the cost of embedding selection logic in every caller.

## 5. Runnable example

Scenario: a client calling `InventoryService`, which has 3 running instances, first modeled with server-side load balancing (all calls go through one shared balancer), then with client-side load balancing (the client fetches the instance list itself and picks directly), then extended to show client-side load balancing reacting to an unhealthy instance without needing the shared balancer to detect and route around it.

### Level 1 — Basic

```java
// File: ServerSideLoadBalancing.java -- the CLIENT only ever talks to
// ONE address (the load balancer); it never sees individual instances.
import java.util.*;

public class ServerSideLoadBalancing {
    static List<String> instances = List.of("instance-A", "instance-B", "instance-C");
    static int roundRobinIndex = 0;

    static class LoadBalancer { // the SHARED component every client call goes through
        String routeToInstance() {
            String chosen = instances.get(roundRobinIndex % instances.size());
            roundRobinIndex++;
            return chosen;
        }
    }

    static class Client {
        LoadBalancer lb; // the client knows ONLY about the load balancer
        Client(LoadBalancer lb) { this.lb = lb; }
        String call() {
            String instance = lb.routeToInstance(); // client never picks directly
            return "called via load balancer -> " + instance;
        }
    }

    public static void main(String[] args) {
        LoadBalancer lb = new LoadBalancer();
        Client client = new Client(lb);
        for (int i = 0; i < 3; i++) System.out.println(client.call());
    }
}
```

**How to run:** `javac ServerSideLoadBalancing.java && java ServerSideLoadBalancing` (JDK 17+).

Expected output:
```
called via load balancer -> instance-A
called via load balancer -> instance-B
called via load balancer -> instance-C
```

### Level 2 — Intermediate

```java
// File: ClientSideLoadBalancing.java -- the CLIENT fetches the instance
// list itself and PICKS directly -- no shared load balancer component.
import java.util.*;

public class ClientSideLoadBalancing {
    static List<String> registryInstances = List.of("instance-A", "instance-B", "instance-C");

    static class ServiceRegistry { // client queries this for the CURRENT instance list
        List<String> getInstances() { return registryInstances; }
    }

    static class Client {
        ServiceRegistry registry;
        int roundRobinIndex = 0; // the SELECTION LOGIC now lives in the client itself
        Client(ServiceRegistry registry) { this.registry = registry; }

        String call() {
            List<String> instances = registry.getInstances(); // fetch current list
            String chosen = instances.get(roundRobinIndex % instances.size()); // client PICKS directly
            roundRobinIndex++;
            return "called DIRECTLY -> " + chosen;
        }
    }

    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();
        Client client = new Client(registry);
        for (int i = 0; i < 3; i++) System.out.println(client.call());
    }
}
```

**How to run:** `javac ClientSideLoadBalancing.java && java ClientSideLoadBalancing` (JDK 17+).

Expected output:
```
called DIRECTLY -> instance-A
called DIRECTLY -> instance-B
called DIRECTLY -> instance-C
```

Note there's no `LoadBalancer` object in this version at all — the client itself holds `roundRobinIndex` and performs the selection, connecting straight to whichever instance it picks.

### Level 3 — Advanced

```java
// File: ClientSideAvoidingUnhealthyInstance.java -- the CLIENT tracks
// instance health itself and routes AROUND a known-bad instance --
// something server-side load balancing would need the SHARED balancer
// to detect via its own health checks, but here the client reacts
// immediately based on its OWN call outcomes.
import java.util.*;

public class ClientSideAvoidingUnhealthyInstance {
    static List<String> registryInstances = List.of("instance-A", "instance-B", "instance-C");

    static class ServiceRegistry {
        List<String> getInstances() { return registryInstances; }
    }

    static class Client {
        ServiceRegistry registry;
        Set<String> knownUnhealthy = new HashSet<>(); // the client's OWN health tracking
        int roundRobinIndex = 0;
        Client(ServiceRegistry registry) { this.registry = registry; }

        boolean simulateCall(String instance) { // "instance-B" is flaky, everything else works
            return !instance.equals("instance-B");
        }

        String call() {
            List<String> healthyInstances = new ArrayList<>();
            for (String instance : registry.getInstances()) {
                if (!knownUnhealthy.contains(instance)) healthyInstances.add(instance);
            }
            String chosen = healthyInstances.get(roundRobinIndex % healthyInstances.size());
            roundRobinIndex++;

            boolean success = simulateCall(chosen);
            if (!success) {
                knownUnhealthy.add(chosen); // client marks it unhealthy IMMEDIATELY, based on its own experience
                return "call to " + chosen + " FAILED -- marked unhealthy, will avoid it going forward";
            }
            return "call to " + chosen + " succeeded";
        }
    }

    public static void main(String[] args) {
        Client client = new Client(new ServiceRegistry());
        for (int i = 0; i < 5; i++) System.out.println(client.call());
    }
}
```

**How to run:** `javac ClientSideAvoidingUnhealthyInstance.java && java ClientSideAvoidingUnhealthyInstance` (JDK 17+).

Expected output:
```
call to instance-A succeeded
call to instance-B FAILED -- marked unhealthy, will avoid it going forward
call to instance-A succeeded
call to instance-C succeeded
call to instance-A succeeded
```

## 6. Walkthrough

1. **Level 1** — `Client` holds a reference only to `LoadBalancer`; every call goes through `lb.routeToInstance()`, which round-robins through `instances` internally. `main` calls `client.call()` three times, and the printed output shows each call routed to a different instance in turn (`A`, `B`, `C`) — but critically, the *client's own code* never touches the `instances` list or the selection logic at all; that responsibility lives entirely inside the shared `LoadBalancer`.
2. **Level 2 — moving selection into the client** — there is no `LoadBalancer` class in this version at all. `Client` itself holds `roundRobinIndex` and directly calls `registry.getInstances()` to get the current list, then performs the same round-robin selection logic that previously lived in the shared `LoadBalancer`. `main`'s output is identical in content to Level 1's — the same three instances, same round-robin order — but structurally, every calling `Client` object now independently carries its own selection state and logic, with no shared intermediary component in the call path.
3. **Level 3 — the client reacting to instance health directly** — `Client` now also tracks `knownUnhealthy`, a set of instances it has personally observed to fail. `call` first filters `registry.getInstances()` down to `healthyInstances` (excluding anything in `knownUnhealthy`), then applies round-robin selection *only* among those. `simulateCall` is hard-coded so `"instance-B"` always fails and everything else succeeds — standing in for a real, flaky downstream instance.
4. **Tracing the five calls** — call 1: `healthyInstances` is all three (`A`, `B`, `C`), `roundRobinIndex % 3 = 0`, chosen is `A`, `simulateCall("A")` succeeds, prints success, `roundRobinIndex` becomes 1. Call 2: still all three healthy, `1 % 3 = 1`, chosen is `B`, `simulateCall("B")` fails, `B` is added to `knownUnhealthy`, prints the failure/marking message, `roundRobinIndex` becomes 2. Call 3: `healthyInstances` is now only `[A, C]` (B excluded, so index 0 is `A` and index 1 is `C`), `roundRobinIndex` is 2, `2 % 2 = 0`, so chosen is `healthyInstances.get(0)`, which is `A` again — `roundRobinIndex` becomes 3. Call 4: `healthyInstances` is still `[A, C]`, `3 % 2 = 1`, chosen is `healthyInstances.get(1)`, which is `C` — `roundRobinIndex` becomes 4. Call 5: `4 % 2 = 0`, chosen is `A` again. B is never selected again for the rest of the client's lifetime, unless health tracking were also given a chance to expire it (not modeled here).
5. **Why this level distinguishes client-side from server-side load balancing** — this instant, call-outcome-driven avoidance of `instance-B` happened entirely within one `Client` object, based purely on that client's own observed call results — no shared load balancer needed to run its own separate health-check probe cycle and propagate that knowledge back out to every caller. In a server-side model, a similarly fast reaction would depend entirely on the shared load balancer's own health-check frequency and propagation delay; in this client-side model, each client's reaction is immediate and call-outcome-driven, though at the cost of every client needing its own health-tracking logic rather than relying on one shared, centrally-maintained view.

## 7. Gotchas & takeaways

> **Gotcha:** client-side health tracking, exactly as modeled in Level 3, is per-client and never expires here — once `instance-B` is marked unhealthy by one client, that client will never route to it again, even if `instance-B` genuinely recovers. Real client-side load-balancing implementations need an expiration or periodic re-check mechanism so a recovered instance eventually re-enters rotation, rather than being permanently blacklisted by any client that happened to see it fail once.

- Server-side load balancing keeps callers simple (one address, no instance-list awareness) at the cost of an extra network hop and a shared component that needs its own scaling/availability story.
- Client-side load balancing removes that extra hop and avoids a centralized bottleneck, at the cost of pushing instance-list awareness and selection logic into every calling service.
- Client-side load balancing can react to a bad instance immediately, based on the calling client's own observed failures, without waiting on a shared load balancer's separate health-check cycle.
- Both approaches still fundamentally depend on an up-to-date, accurate list of healthy instances — that list is populated and maintained by service discovery and registration mechanisms, covered later in this series.
- Client-side health tracking needs an expiration/recovery mechanism — a permanently blacklisted instance that has actually recovered represents wasted capacity that will never be used again by that client.
