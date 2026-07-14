---
card: microservices
gi: 526
slug: hardcoded-service-locations
title: "Hardcoded service locations"
---

## 1. What it is

**Hardcoded service locations** is the anti-pattern of baking a downstream service's network address — an IP, a hostname, a port — directly into a caller's code or static configuration, instead of resolving it dynamically through service discovery, DNS, or a load balancer at call time. It works fine as long as that address never changes, but in any environment where instances scale up and down, get replaced after failures, or move between hosts (which describes almost every modern deployment environment), a hardcoded address eventually points at nothing, or at something that no longer serves that role.

## 2. Why & when

You avoid hardcoded locations because the assumption "this address is stable" is almost never true for long in a system designed to scale and heal itself:

- **Instances are ephemeral in any auto-scaled or self-healing environment.** A container orchestrator can kill and reschedule an unhealthy instance onto a different host with a different IP at any moment; an auto-scaler can add or remove instances in response to load. A hardcoded IP baked into a caller assumes none of this ever happens, which is false by design in these environments.
- **Hardcoding location conflates "which service to call" with "where that service currently happens to be running"** — two facts with very different lifetimes. Which service to call is a stable, slow-changing decision made by a developer; where it's currently running is a fast-changing operational fact that should be resolved fresh, close to call time, not baked in ahead of time.
- **It also blocks horizontal scaling from actually working**, since a caller hardcoded to one address can never spread load across multiple instances of the target service — even if five instances are running, a hardcoded caller only ever reaches one of them, defeating the purpose of running five.
- **The fix is indirection**: a service registry, DNS-based discovery, or a load balancer sits between the caller and the actual instances, so the caller resolves "the current healthy address(es) for Service X" at call time (or via a client library that refreshes periodically), rather than assuming a fixed address baked in ahead of time.

## 3. Core concept

Think of memorizing a friend's exact desk location in a large open-plan office instead of just knowing their name and calling the front desk to be connected. The memorized desk location works until the office reorganizes seating (which large offices do often) — at which point everyone who memorized a specific desk shows up at an empty chair, while everyone who just asked the front desk for "Alex" gets connected correctly regardless of where Alex sits today. The front desk is a stable point of indirection between "who you want to reach" (which changes rarely) and "where they currently sit" (which changes often) — exactly the role service discovery plays between a caller and a service's ever-changing set of running instances.

Concretely:

1. **A caller should depend on a stable, logical name for a service** ("inventory-service"), not a specific instance's current network address.
2. **A discovery mechanism resolves that logical name to one or more currently-healthy addresses at, or shortly before, call time** — a DNS lookup, a query to a service registry (Consul, Eureka, Kubernetes' internal DNS), or a client-side load balancer that maintains a refreshed list of healthy instances.
3. **This resolution needs to happen freshly enough to reflect reality** — a discovery result cached forever is just a hardcoded address with extra steps; the cache needs a bounded TTL or an active health-check mechanism that removes dead instances promptly.
4. **The same mechanism that enables resilience (rerouting around a dead instance) also enables horizontal scaling** (spreading calls across multiple healthy instances) — both come from the same underlying fix of resolving location dynamically instead of baking it in.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Hardcoded address points at a specific instance that can disappear; service discovery resolves a stable logical name to currently-healthy instances at call time">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Hardcoded address</text>
  <rect x="20" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Caller: connect to 10.0.4.17:8080</text>
  <line x1="150" y1="65" x2="150" y2="90" stroke="#f0883e" stroke-width="2"/>
  <rect x="20" y="90" width="260" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="150" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">10.0.4.17 -- instance rescheduled, GONE</text>
  <text x="150" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">connection refused / timeout, no fallback</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Service discovery</text>
  <rect x="380" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Caller: resolve "inventory-service"</text>
  <line x1="510" y1="65" x2="510" y2="90" stroke="#6db33f" stroke-width="2"/>
  <rect x="380" y="90" width="260" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">registry: [10.0.5.2, 10.0.5.9] -- healthy</text>
  <text x="510" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">dead instances removed, new ones added automatically</text>
</svg>

A hardcoded address has no recovery path once its instance disappears; discovery resolves fresh, healthy addresses at call time.

## 5. Runnable example

Scenario: a caller reaching an Inventory service. We start with a hardcoded address that breaks when the instance moves, extend it to a simple service registry with dynamic lookup, then handle the hard case: a registry that tracks multiple instances, removes unhealthy ones, and load-balances across the rest.

### Level 1 — Basic

```java
// File: HardcodedLocation.java -- the caller has the Inventory
// service's address BAKED IN as a constant. Fine, until it moves.
import java.util.*;

public class HardcodedLocation {
    static final String INVENTORY_SERVICE_ADDRESS = "10.0.4.17:8080"; // hardcoded, baked into the caller

    static String callInventoryService(Map<String, String> liveTopology) {
        // simulates a network call: succeeds only if the hardcoded address is still actually running the service
        if (liveTopology.containsKey(INVENTORY_SERVICE_ADDRESS)) {
            return "OK: reached " + INVENTORY_SERVICE_ADDRESS + " (" + liveTopology.get(INVENTORY_SERVICE_ADDRESS) + ")";
        }
        return "FAILED: " + INVENTORY_SERVICE_ADDRESS + " unreachable (instance no longer here)";
    }

    public static void main(String[] args) {
        Map<String, String> liveTopology = new HashMap<>();
        liveTopology.put("10.0.4.17:8080", "inventory-service"); // this instance is currently alive
        System.out.println(callInventoryService(liveTopology));

        // the orchestrator reschedules the instance onto a NEW address, as it routinely does
        liveTopology.clear();
        liveTopology.put("10.0.5.2:8080", "inventory-service"); // same service, new address
        System.out.println(callInventoryService(liveTopology));
    }
}
```

How to run: `java HardcodedLocation.java`

`INVENTORY_SERVICE_ADDRESS` is a fixed constant. The first call succeeds because the hardcoded address happens to match the current topology; after the simulated reschedule (the instance now runs at a new address), the exact same caller code fails outright — nothing in the caller has any way to learn about the new address, because it never asked, it just assumed.

### Level 2 — Intermediate

```java
// File: SimpleDiscovery.java -- a minimal SERVICE REGISTRY: the caller
// resolves the CURRENT address for a logical service name AT CALL TIME,
// instead of hardcoding one address ahead of time.
import java.util.*;

public class SimpleDiscovery {
    static class ServiceRegistry {
        Map<String, String> registrations = new HashMap<>(); // logical name -> current address

        void register(String serviceName, String address) { registrations.put(serviceName, address); }
        void deregister(String serviceName) { registrations.remove(serviceName); }
        Optional<String> resolve(String serviceName) { return Optional.ofNullable(registrations.get(serviceName)); }
    }

    static String callService(ServiceRegistry registry, String serviceName) {
        Optional<String> address = registry.resolve(serviceName); // resolved FRESH, every call
        return address.map(a -> "OK: reached " + serviceName + " at " + a)
                       .orElse("FAILED: no healthy instance registered for " + serviceName);
    }

    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();
        registry.register("inventory-service", "10.0.4.17:8080");
        System.out.println(callService(registry, "inventory-service"));

        // instance reschedules: it deregisters its OLD address and registers its NEW one
        registry.deregister("inventory-service");
        registry.register("inventory-service", "10.0.5.2:8080");
        System.out.println(callService(registry, "inventory-service")); // succeeds -- resolved the NEW address automatically
    }
}
```

How to run: `java SimpleDiscovery.java`

The caller never hardcodes an address — it calls `registry.resolve("inventory-service")` every time, getting whatever address is currently registered. When the instance reschedules and re-registers under a new address, the very next call automatically picks up the new location with zero changes to the caller's code — the exact failure from Level 1 simply cannot happen here, because "where is it right now" is answered fresh at call time, not assumed in advance.

### Level 3 — Advanced

```java
// File: MultiInstanceLoadBalanced.java -- extends discovery to track
// MULTIPLE healthy instances per service, remove unhealthy ones via
// health checks, and LOAD-BALANCE calls across whatever remains healthy.
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class MultiInstanceLoadBalanced {
    static class Instance {
        String address; boolean healthy;
        Instance(String address, boolean healthy) { this.address = address; this.healthy = healthy; }
    }

    static class LoadBalancedRegistry {
        Map<String, List<Instance>> registrations = new HashMap<>();
        AtomicInteger roundRobinCounter = new AtomicInteger(0);

        void register(String serviceName, String address) {
            registrations.computeIfAbsent(serviceName, k -> new ArrayList<>()).add(new Instance(address, true));
        }
        void markUnhealthy(String serviceName, String address) {
            for (Instance i : registrations.getOrDefault(serviceName, List.of())) {
                if (i.address.equals(address)) i.healthy = false; // health check detected a failure
            }
        }
        Optional<String> resolve(String serviceName) {
            List<Instance> healthyInstances = registrations.getOrDefault(serviceName, List.of()).stream()
                .filter(i -> i.healthy).toList();
            if (healthyInstances.isEmpty()) return Optional.empty();
            int index = roundRobinCounter.getAndIncrement() % healthyInstances.size(); // spread load across all healthy ones
            return Optional.of(healthyInstances.get(index).address);
        }
    }

    public static void main(String[] args) {
        LoadBalancedRegistry registry = new LoadBalancedRegistry();
        registry.register("inventory-service", "10.0.5.2:8080");
        registry.register("inventory-service", "10.0.5.9:8080");
        registry.register("inventory-service", "10.0.5.14:8080");

        System.out.println("--- normal operation: calls spread across all 3 instances ---");
        for (int i = 0; i < 4; i++) System.out.println("call " + i + " -> " + registry.resolve("inventory-service").get());

        System.out.println("--- health check detects 10.0.5.9 is unhealthy, removes it from rotation ---");
        registry.markUnhealthy("inventory-service", "10.0.5.9:8080");
        for (int i = 0; i < 4; i++) System.out.println("call " + i + " -> " + registry.resolve("inventory-service").get());
    }
}
```

How to run: `java MultiInstanceLoadBalanced.java`

`resolve` round-robins across only the currently-healthy instances, tracked in a list rather than a single value. Before the health check, calls cycle through all three addresses; after `markUnhealthy` flags `10.0.5.9:8080` as unhealthy (simulating a failed health check), that address is filtered out of every subsequent `resolve` call, and traffic continues flowing to only the two remaining healthy instances — automatically, without the caller changing anything or even being aware an instance went unhealthy.

## 6. Walkthrough

Trace `MultiInstanceLoadBalanced.main` end to end:

1. **Three instances register under the same logical name** `"inventory-service"`, each marked healthy by default — the registry now holds a list of three `Instance` objects for that one logical name.
2. **The first loop calls `registry.resolve("inventory-service")` four times.** Each call filters `registrations` down to only healthy instances (all three, initially), then picks one via `roundRobinCounter.getAndIncrement() % 3` — call 0 gets index 0, call 1 gets index 1, call 2 gets index 2, call 3 wraps back to index 0 — spreading the four calls roughly evenly across all three addresses.
3. **`registry.markUnhealthy("inventory-service", "10.0.5.9:8080")` is called**, simulating a health check that detected this instance is no longer responding correctly. This flips that one `Instance`'s `healthy` field to `false`, without removing it from the list entirely (so it could be marked healthy again later if it recovers).
4. **The second loop calls `resolve` four more times.** Each call's internal filter (`i -> i.healthy`) now excludes `10.0.5.9:8080`, leaving only two healthy instances in `healthyInstances`. The round-robin index now cycles `% 2` instead of `% 3` — calls land only on `10.0.5.2:8080` and `10.0.5.14:8080`, alternating between them, with `10.0.5.9:8080` never selected again until it's marked healthy.
5. **No caller code outside the registry needed to change at all** — the caller simply calls `resolve(...)` each time and uses whatever address comes back; the registry's internal health tracking and round-robin logic are the only things that adapted.

This is the same mechanism real infrastructure provides: a Kubernetes Service resolves a stable DNS name to the current set of healthy pod IPs behind it, removing unhealthy pods automatically based on liveness/readiness probes; a client-side load balancer (like those built into many service mesh sidecars) does exactly this round-robin-over-healthy-instances resolution locally, on every call, so the calling code never hardcodes, and never even sees, a specific instance's address.

## 7. Gotchas & takeaways

> **Gotcha:** caching a resolved address for "just a little while, to save the lookup cost" without a bounded refresh or active health-check integration quietly turns discovery back into a hardcoded address with extra steps — if the cache never expires or refreshes, a rescheduled or unhealthy instance is just as invisible as it would have been with a hardcoded constant, only discovered later and more confusingly.

- Never bake a specific instance's IP, hostname, or port into caller code or static config — depend on a stable logical service name and resolve its current address through discovery at (or very close to) call time.
- The same discovery mechanism that provides resilience (routing around a dead instance) also enables horizontal scaling (spreading load across many healthy instances) — they're two benefits of the identical fix.
- Any caching layer in front of discovery needs a bounded TTL or active health-check-driven invalidation — an unbounded cache defeats the purpose just as thoroughly as a hardcoded address would.
- In practice you rarely build a registry from scratch — DNS-based discovery (Kubernetes Services), a dedicated registry (Consul, Eureka), or client-side load-balancing libraries all provide this resolve-at-call-time behavior; the important thing is recognizing when a design has bypassed all of them with a hardcoded shortcut.
