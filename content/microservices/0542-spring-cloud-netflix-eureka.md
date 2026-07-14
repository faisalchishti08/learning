---
card: microservices
gi: 542
slug: spring-cloud-netflix-eureka
title: "Spring Cloud Netflix (Eureka)"
---

## 1. What it is

**Eureka** is Netflix's service registry, integrated into Spring Cloud as **Spring Cloud Netflix Eureka** — a concrete implementation of the [`DiscoveryClient`/`ServiceInstance` abstractions](0539-spring-cloud-commons-shared-abstractions.md) that solves [hardcoded service locations](0526-hardcoded-service-locations.md) via a central registry server every service instance registers itself with on startup and periodically renews a heartbeat against, while every service instance that needs to *call* another service queries the same registry to discover currently-healthy instances. It was, for years, the default and most widely-used discovery mechanism in the Spring Cloud ecosystem, though newer projects today often reach for Kubernetes-native discovery when running on Kubernetes, since it provides equivalent functionality without an extra piece of infrastructure to operate.

## 2. Why & when

You reach for Eureka specifically when running outside Kubernetes (or another environment with its own native service discovery) and need a battle-tested, standalone service registry:

- **Eureka provides both halves of service discovery**: the **Eureka Server** (a standalone registry application) and the **Eureka Client** (embedded in every service instance) — instances register themselves on startup (`POST /eureka/apps/{appName}`), send periodic heartbeats to prove they're still alive, and are automatically removed from the registry if their heartbeats stop (signaling they've crashed or become unreachable).
- **It solves exactly the [hardcoded address problem](0526-hardcoded-service-locations.md)**: callers never hardcode a downstream instance's address; they query Eureka for "order-service"'s currently-registered, healthy instances and get back a fresh list reflecting the fleet's actual current state.
- **It was historically the default choice for Spring Cloud microservices running on traditional VMs or bare containers** (not Kubernetes), where no other discovery mechanism was already provided by the underlying infrastructure — if you're deploying onto Kubernetes, its own built-in Service/Endpoints-based discovery typically replaces Eureka's role without needing separate infrastructure.
- **It provides a self-preservation mode**: if Eureka Server detects an unusually large fraction of instances suddenly stopped sending heartbeats (often signaling a network partition between the server and clients, rather than instances actually being down), it stops aggressively evicting registrations, protecting against a network blip causing mass, likely-incorrect deregistration.

## 3. Core concept

Think of Eureka as a hotel's front desk that every guest checks in with upon arrival, and that periodically confirms with each guest's room ("still there?") to keep its own registry of who's actually currently staying accurate. Anyone (another guest, a delivery person) asking the front desk "which room is guest X in right now" gets an answer reflecting who's actually currently checked in, not a stale list from last week — and if a guest checks out (or stops responding to the front desk's periodic check-ins, suggesting they've left without formally checking out), the front desk removes them from the active registry so future inquiries don't get sent to an empty room.

Concretely:

1. **On startup, a service instance registers with Eureka Server**, providing its host, port, and application name — Eureka now knows this instance exists and is (presumably) healthy.
2. **The instance sends a heartbeat to Eureka Server at a regular interval** (default 30 seconds) to renew its registration — Eureka Server tracks the last heartbeat time per instance.
3. **If an instance's heartbeat lapses beyond a configured threshold** (default 90 seconds, three missed heartbeats), Eureka Server evicts that instance from its registry — subsequent discovery queries for that service no longer return it.
4. **A calling service's `DiscoveryClient` (backed by the Eureka client library) queries Eureka Server for the current list of healthy instances of a target service**, typically caching this list locally for a short interval to avoid querying the server on every single call, and refreshing it periodically.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Instances register with Eureka Server and send periodic heartbeats; a caller queries Eureka Server for the current healthy instance list before making a call">
  <rect x="270" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="360" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Eureka Server (registry)</text>

  <rect x="20" y="100" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-service instance</text>
  <line x1="95" y1="100" x2="300" y2="60" stroke="#8b949e" marker-end="url(#a7)"/>
  <text x="130" y="80" fill="#8b949e" font-size="8">register + heartbeat</text>

  <rect x="480" y="100" width="150" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="555" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">caller service</text>
  <line x1="555" y1="100" x2="400" y2="60" stroke="#8b949e" marker-end="url(#a7)"/>
  <text x="500" y="80" fill="#8b949e" font-size="8">query: who's healthy?</text>

  <text x="330" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">missed heartbeats -&gt; instance evicted -&gt; no longer returned to callers</text>
  <defs><marker id="a7" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

Instances register and heartbeat with Eureka Server; callers query it for the current, healthy instance list rather than hardcoding an address.

## 5. Runnable example

Scenario: instances registering and a caller discovering them. We start with a plain Java model of the register/heartbeat/discover cycle, extend it to include eviction on missed heartbeats, then show the real Spring Cloud Netflix Eureka client/server configuration.

### Level 1 — Basic

```java
// File: SimpleRegistryModel.java -- models the CORE Eureka idea:
// instances REGISTER; callers QUERY the registry for current instances.
import java.util.*;

public class SimpleRegistryModel {
    static Map<String, List<String>> registry = new HashMap<>(); // serviceName -> list of addresses

    static void register(String serviceName, String address) {
        registry.computeIfAbsent(serviceName, k -> new ArrayList<>()).add(address);
        System.out.println("Registered " + address + " under " + serviceName);
    }
    static List<String> discover(String serviceName) {
        return registry.getOrDefault(serviceName, List.of());
    }

    public static void main(String[] args) {
        register("order-service", "10.0.5.2:8080");
        register("order-service", "10.0.5.9:8080");
        System.out.println("Discovered order-service instances: " + discover("order-service"));
    }
}
```

How to run: `java SimpleRegistryModel.java`

`register` and `discover` model Eureka Server's two core operations — instances register themselves under a logical service name, and callers query that same name to get back the current list of registered addresses, rather than hardcoding a specific one.

### Level 2 — Intermediate

```java
// File: HeartbeatEviction.java -- adds HEARTBEATS and EVICTION: an
// instance that stops heartbeating is automatically removed from the
// registry after a threshold, so callers stop being sent to it.
import java.time.*;
import java.util.*;

public class HeartbeatEviction {
    record Registration(String address, Instant lastHeartbeat) {}
    static Map<String, List<Registration>> registry = new HashMap<>();
    static final Duration EVICTION_THRESHOLD = Duration.ofSeconds(90);

    static void heartbeat(String serviceName, String address, Instant now) {
        List<Registration> regs = registry.computeIfAbsent(serviceName, k -> new ArrayList<>());
        regs.removeIf(r -> r.address().equals(address));
        regs.add(new Registration(address, now));
    }

    static List<String> discover(String serviceName, Instant now) {
        List<Registration> regs = registry.getOrDefault(serviceName, List.of());
        // EVICT any registration whose heartbeat is too old before returning results
        return regs.stream()
            .filter(r -> Duration.between(r.lastHeartbeat(), now).compareTo(EVICTION_THRESHOLD) < 0)
            .map(Registration::address)
            .toList();
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-01-01T00:00:00Z");
        heartbeat("order-service", "10.0.5.2:8080", t0);
        heartbeat("order-service", "10.0.5.9:8080", t0);

        System.out.println("At t0: " + discover("order-service", t0));

        // 10.0.5.9 stops heartbeating (crashed); 10.0.5.2 keeps heartbeating normally
        heartbeat("order-service", "10.0.5.2:8080", t0.plusSeconds(60));
        System.out.println("At t0+60s: " + discover("order-service", t0.plusSeconds(60)) + " (both still within threshold)");

        System.out.println("At t0+120s: " + discover("order-service", t0.plusSeconds(120)) + " -- 10.0.5.9 EVICTED, missed heartbeats past threshold");
    }
}
```

How to run: `java HeartbeatEviction.java`

`discover` filters out any registration whose `lastHeartbeat` is older than `EVICTION_THRESHOLD` (90 seconds) relative to `now` — `10.0.5.9:8080` heartbeats once at `t0` and then stops (simulating a crash), so by `t0+120s`, `Duration.between(t0, t0+120s)` exceeds the threshold and it's correctly excluded from the discovery result, while `10.0.5.2:8080` (which kept heartbeating at `t0+60s`) remains present.

### Level 3 — Advanced

```java
// File: EurekaRealShape.java -- the REAL Spring Cloud Netflix Eureka
// shape: @EnableEurekaServer for the registry, @EnableDiscoveryClient
// for a service that registers itself and discovers others.
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.netflix.eureka.server.EnableEurekaServer;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.web.bind.annotation.*;

public class EurekaRealShape {

    // --- the Eureka SERVER: a standalone registry application ---
    @SpringBootApplication
    @EnableEurekaServer
    static class EurekaServerApplication {
        public static void main(String[] args) { SpringApplication.run(EurekaServerApplication.class, args); }
        // application.yml: eureka.client.register-with-eureka=false, fetch-registry=false
        // (the server itself doesn't need to register with or query itself)
    }

    // --- a Eureka CLIENT service, e.g. an api-gateway calling order-service ---
    @SpringBootApplication
    @EnableDiscoveryClient
    static class GatewayApplication {
        public static void main(String[] args) { SpringApplication.run(GatewayApplication.class, args); }
        // application.yml: spring.application.name=api-gateway
        //                  eureka.client.service-url.defaultZone=http://eureka-server:8761/eureka
    }

    @RestController
    static class DiscoveryDebugController {
        private final DiscoveryClient discoveryClient;
        DiscoveryDebugController(DiscoveryClient discoveryClient) { this.discoveryClient = discoveryClient; }

        @GetMapping("/debug/instances/{serviceName}")
        public Object instances(@PathVariable String serviceName) {
            return discoveryClient.getInstances(serviceName); // resolved via Eureka underneath, using the shared abstraction
        }
    }
}
```

How to run: requires `spring-cloud-starter-netflix-eureka-server` for the server application, `spring-cloud-starter-netflix-eureka-client` for every registering/discovering client application, and each client's `spring.application.name` plus `eureka.client.service-url.defaultZone` pointed at the running Eureka Server; run the server first, then any client applications, and hit `/debug/instances/order-service` on the gateway to see the currently-registered `order-service` instances Eureka reports.

`@EnableEurekaServer` turns a plain Spring Boot application into the registry itself; `@EnableDiscoveryClient` (alongside the Eureka client dependency) makes any other Spring Boot application both register itself with that server on startup and be able to query it via the standard `DiscoveryClient` interface — the exact same abstraction discussed in [Spring Cloud Commons](0539-spring-cloud-commons-shared-abstractions.md), here concretely backed by Eureka.

## 6. Walkthrough

Trace what happens across the fleet from `GatewayApplication` starting up through calling `/debug/instances/order-service`, assuming two `order-service` instances are already registered and healthy:

1. **`GatewayApplication` starts**, and because of `@EnableDiscoveryClient` plus the Eureka client dependency, it registers itself with the Eureka Server at `http://eureka-server:8761/eureka` under the application name `api-gateway` — the gateway is now itself discoverable too, though this example doesn't rely on that.
2. **The Eureka client embedded in the gateway begins periodically fetching the full registry** from Eureka Server in the background (a local cache refreshed on an interval, typically 30 seconds by default), rather than querying the server fresh on every single discovery call — this cache is what `DiscoveryClient.getInstances(...)` actually reads from most of the time.
3. **A request arrives at `GET /debug/instances/order-service`.** `DiscoveryDebugController` calls `discoveryClient.getInstances("order-service")`.
4. **The Eureka-backed `DiscoveryClient` implementation reads from its locally-cached registry snapshot** (populated in step 2), finds the two `order-service` instances currently marked healthy, and returns them as `ServiceInstance` objects.
5. **The response includes both instances' host/port information**, reflecting whatever Eureka Server's registry showed as of the client's last cache refresh — if one of those two instances crashed moments ago and hasn't yet missed enough heartbeats to be evicted server-side, or if the gateway's local cache simply hasn't refreshed since the eviction happened, the response could very briefly still include it; this is the expected, bounded staleness window inherent in any cached discovery approach, not a bug.

If, instead, one `order-service` instance had already missed enough heartbeats (past the 90-second default threshold) *and* the gateway's local cache had already refreshed since that eviction, step 4's result would correctly exclude that instance — reflecting the same core `discover` filtering logic modeled in Level 2's `HeartbeatEviction` example, just running for real against Eureka Server's actual registry.

## 7. Gotchas & takeaways

> **Gotcha:** Eureka's default self-preservation mode can cause discovery to keep returning instances that have actually stopped heartbeating, if Eureka Server detects an unusually large fraction of instances losing their heartbeats simultaneously (its heuristic for "this is probably a network partition between the server and clients, not mass instance failure") — this protects against a false mass-eviction during a transient network issue, but means a real, widespread outage can also briefly leave stale registrations visible; understand this trade-off rather than being surprised by it during an actual incident.

- Eureka provides a battle-tested, standalone service registry for environments without their own native discovery mechanism — on Kubernetes, its own built-in Service/Endpoints discovery often fills this role instead, without needing separate infrastructure.
- Registration and heartbeats are how Eureka Server tracks which instances are currently believed healthy; missed heartbeats past a threshold trigger automatic eviction from the registry.
- Discovery clients typically cache the registry locally and refresh on an interval, trading a small bounded staleness window for far fewer queries against Eureka Server itself.
- Self-preservation mode exists to avoid over-reacting to what might just be a network blip, at the cost of potentially masking a genuine large-scale outage briefly — know this behavior exists before relying on Eureka's eviction as an instant failure-detection signal.
