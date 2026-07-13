---
card: microservices
gi: 196
slug: spring-cloud-netflix-eureka-client
title: "Spring Cloud Netflix Eureka client"
---

## 1. What it is

Spring Cloud Netflix Eureka Client is the counterpart to [Eureka Server](0195-spring-cloud-netflix-eureka-server.md) — adding `spring-cloud-starter-netflix-eureka-client` to a Spring Boot application automatically handles [self-registration](0183-service-registration-self-vs-third-party.md), periodic heartbeat sending, and local caching of the registry's data for fast lookups, all through configuration alone, with no manual registry API calls written by the application.

## 2. Why & when

Manually implementing registration, heartbeat scheduling, and registry-query caching in every service that needs to participate in discovery would be exactly the kind of repetitive, error-prone boilerplate that a client library exists to eliminate — get the heartbeat interval wrong, forget to handle registration failure on startup, or skip caching entirely (hammering the registry with a network call on every single lookup) are all easy mistakes when done by hand, repeatedly, across many services. The Eureka Client handles all of this automatically once configured, using sensible defaults tuned by the same team that built the server, and exposes the resolved registry data through Spring's standard `DiscoveryClient` interface for application code to query when needed.

Add the Eureka Client to any Spring Boot service that needs to register itself with a Eureka Server and/or discover other services registered there. This is typically paired with `@EnableDiscoveryClient` (or its Spring Boot auto-configuration equivalent) and works seamlessly alongside `spring-cloud-starter-loadbalancer` for [client-side discovery](0185-client-side-service-discovery.md) with load balancing.

## 3. Core concept

On application startup, the client automatically registers the instance with the configured Eureka Server(s), begins sending heartbeats on a schedule to renew its lease, and periodically fetches and locally caches the registry's current state so that discovery queries made by application code are served from a fast local cache rather than a network call every time.

```java
@SpringBootApplication
@EnableDiscoveryClient // activates AUTOMATIC registration, heartbeats, and registry caching
public class OrderServiceApplication {
    public static void main(String[] args) { SpringApplication.run(OrderServiceApplication.class, args); }
}
```
```yaml
eureka.client.service-url.defaultZone: http://eureka-server:8761/eureka/
eureka.instance.lease-renewal-interval-in-seconds: 30 # heartbeat frequency -- CLIENT handles the scheduling automatically
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Spring Boot application annotated with @EnableDiscoveryClient automatically registers with Eureka Server on startup, sends periodic heartbeats, and refreshes a local cache of the registry's data, all without application code making any manual API calls" >
  <rect x="20" y="70" width="180" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="92" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">order-service</text>
  <text x="110" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">@EnableDiscoveryClient</text>

  <rect x="440" y="70" width="180" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="95" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Eureka Server</text>

  <line x1="200" y1="80" x2="438" y2="80" stroke="#8b949e" marker-end="url(#arr77)"/>
  <text x="320" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">register + heartbeat</text>

  <line x1="438" y1="105" x2="200" y2="105" stroke="#8b949e" marker-end="url(#arr77)"/>
  <text x="320" y="120" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">periodic registry fetch -&gt; local cache</text>

  <defs>
    <marker id="arr77" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

All three responsibilities — registration, heartbeats, and cache refresh — run automatically once the client is configured.

## 5. Runnable example

Scenario: an order-service startup that starts with manually written registration and heartbeat-scheduling code (showing the boilerplate the client eliminates), models the equivalent automatic behavior the Eureka Client provides once configured, and finally demonstrates the local registry cache in action, showing lookups served fast from cache with periodic background refresh rather than a network call per lookup.

### Level 1 — Basic

```java
// File: ManualRegistrationAndHeartbeat.java -- HAND-WRITTEN registration and
// heartbeat scheduling -- exactly the boilerplate a Eureka Client eliminates.
import java.util.concurrent.*;

public class ManualRegistrationAndHeartbeat {
    static void registerWithEureka() { System.out.println("[manual] POST /eureka/apps/ORDER-SERVICE ..."); }
    static void sendHeartbeat() { System.out.println("[manual] PUT /eureka/apps/ORDER-SERVICE/order-a ..."); }

    public static void main(String[] args) throws InterruptedException {
        registerWithEureka(); // the APPLICATION must remember to call this on startup

        ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
        scheduler.scheduleAtFixedRate(ManualRegistrationAndHeartbeat::sendHeartbeat, 0, 30, TimeUnit.SECONDS); // MUST be hand-scheduled correctly

        Thread.sleep(100); // just enough for ONE heartbeat to fire in this demo
        scheduler.shutdown();
        System.out.println("Every service needing this had to write and correctly schedule ALL of this itself.");
    }
}
```

**How to run:** `javac ManualRegistrationAndHeartbeat.java && java ManualRegistrationAndHeartbeat` (JDK 17+).

### Level 2 — Intermediate

```java
// File: AutomaticClientBehavior.java -- models what @EnableDiscoveryClient
// does AUTOMATICALLY: registration and heartbeat scheduling handled by the
// FRAMEWORK, activated purely through configuration.
import java.util.concurrent.*;

public class AutomaticClientBehavior {
    // simulates the Eureka Client's internal machinery -- code the FRAMEWORK provides
    static class EurekaClientCore {
        String appName;
        long heartbeatIntervalSeconds;
        EurekaClientCore(String appName, long heartbeatIntervalSeconds) { this.appName = appName; this.heartbeatIntervalSeconds = heartbeatIntervalSeconds; }

        void onApplicationStartup() { // called AUTOMATICALLY by Spring's lifecycle, not by application code
            System.out.println("[EurekaClient] auto-registering " + appName + " on startup");
            scheduleHeartbeats();
        }
        void scheduleHeartbeats() {
            System.out.println("[EurekaClient] auto-scheduled heartbeats every " + heartbeatIntervalSeconds + "s, using CONFIGURED interval");
        }
    }

    public static void main(String[] args) {
        // the APPLICATION'S code: just configuration values, NO manual scheduling logic anywhere
        EurekaClientCore client = new EurekaClientCore("ORDER-SERVICE", 30);
        client.onApplicationStartup(); // this is what "@EnableDiscoveryClient" triggers automatically at real startup

        System.out.println("Application code contains ZERO registration or heartbeat-scheduling logic -- ONLY configuration values.");
    }
}
```

**How to run:** `javac AutomaticClientBehavior.java && java AutomaticClientBehavior` (JDK 17+).

Expected output:
```
[EurekaClient] auto-registering ORDER-SERVICE on startup
[EurekaClient] auto-scheduled heartbeats every 30s, using CONFIGURED interval
Application code contains ZERO registration or heartbeat-scheduling logic -- ONLY configuration values.
```

### Level 3 — Advanced

```java
// File: LocalCacheWithBackgroundRefresh.java -- discovery LOOKUPS are served
// from a FAST local cache, refreshed periodically in the BACKGROUND -- NOT a
// network call to the registry on every single lookup.
import java.util.*;
import java.util.concurrent.*;

public class LocalCacheWithBackgroundRefresh {
    record ServiceInstance(String id, String host) {}

    static class RemoteEurekaServer { // simulates the ACTUAL remote registry, a real network call away
        List<ServiceInstance> currentInstances = new ArrayList<>(List.of(new ServiceInstance("customer-a", "10.0.2.5")));
        int fetchCount = 0;
        List<ServiceInstance> fetchAll() { fetchCount++; System.out.println("  [NETWORK CALL to Eureka Server] fetch #" + fetchCount); return new ArrayList<>(currentInstances); }
    }

    static class EurekaClientWithCache {
        RemoteEurekaServer server;
        List<ServiceInstance> localCache = new ArrayList<>();
        EurekaClientWithCache(RemoteEurekaServer server) { this.server = server; refreshCache(); }

        void refreshCache() { localCache = server.fetchAll(); } // the ONLY place a network call happens

        // application code calls THIS -- served from the LOCAL cache, NO network call per lookup
        List<ServiceInstance> discover(String serviceName) {
            return localCache; // FAST, local, in-memory read
        }
    }

    public static void main(String[] args) {
        RemoteEurekaServer server = new RemoteEurekaServer();
        EurekaClientWithCache client = new EurekaClientWithCache(server); // ONE fetch, at startup

        // application code makes MANY lookups -- NONE of them hit the network
        System.out.println("Lookup 1: " + client.discover("customer-service"));
        System.out.println("Lookup 2: " + client.discover("customer-service"));
        System.out.println("Lookup 3: " + client.discover("customer-service"));
        System.out.println("3 lookups, but only " + server.fetchCount + " actual network call to the registry -- served from CACHE.");

        // a NEW instance registers on the server -- the client's cache is STALE until its next scheduled refresh
        server.currentInstances.add(new ServiceInstance("customer-b", "10.0.2.6"));
        System.out.println("\nA new instance registered server-side, but client cache is STILL stale: " + client.discover("customer-service"));

        client.refreshCache(); // the PERIODIC background refresh a real Eureka Client performs automatically
        System.out.println("After the periodic background refresh: " + client.discover("customer-service"));
    }
}
```

**How to run:** `javac LocalCacheWithBackgroundRefresh.java && java LocalCacheWithBackgroundRefresh` (JDK 17+).

Expected output:
```
  [NETWORK CALL to Eureka Server] fetch #1
Lookup 1: [ServiceInstance[id=customer-a, host=10.0.2.5]]
Lookup 2: [ServiceInstance[id=customer-a, host=10.0.2.5]]
Lookup 3: [ServiceInstance[id=customer-a, host=10.0.2.5]]
3 lookups, but only 1 actual network call to the registry -- served from CACHE.

A new instance registered server-side, but client cache is STILL stale: [ServiceInstance[id=customer-a, host=10.0.2.5]]
  [NETWORK CALL to Eureka Server] fetch #2
After the periodic background refresh: [ServiceInstance[id=customer-a, host=10.0.2.5], ServiceInstance[id=customer-b, host=10.0.2.6]]
```

## 6. Walkthrough

1. **Level 1** — `registerWithEureka()` and the `scheduler.scheduleAtFixedRate` call must both be written and correctly invoked from `main` itself; any service adopting this pattern would need to replicate this exact scheduling setup, with real risk of misconfiguring the interval or forgetting the registration call on some startup path.
2. **Level 2, the lifecycle hook standing in for automatic activation** — `EurekaClientCore.onApplicationStartup` represents what Spring's own application lifecycle calls automatically once `@EnableDiscoveryClient` is present and the Eureka Client dependency is on the classpath; `main` calls it directly here only to make the *timing* of this automatic behavior visible in the demo.
3. **Level 2, configuration instead of code** — `new EurekaClientCore("ORDER-SERVICE", 30)` takes only data (an application name and an interval), mirroring how a real application's involvement with Eureka Client is limited to `application.yml` configuration values, not imperative scheduling code.
4. **Level 2, the observable simplicity** — the final printed statement is directly verifiable from the code: nowhere in `main` or in what represents "application code" does any scheduling or registration logic appear, only configuration values passed to the framework-provided `EurekaClientCore`.
5. **Level 3, distinguishing the network call from the cached read** — `RemoteEurekaServer.fetchAll` is the only method that increments `fetchCount` and prints a "NETWORK CALL" log line; `EurekaClientWithCache.discover` simply returns `localCache`, a plain in-memory field read with no network interaction at all.
6. **Level 3, three lookups, one network call** — `main` calls `client.discover(...)` three times, but `server.fetchCount` remains at `1` (from the initial cache population in the constructor), directly demonstrating that repeated discovery lookups are served entirely from the local cache rather than triggering a fresh registry query each time.
7. **Level 3, the staleness window and its resolution** — after `server.currentInstances.add(...)` registers a new instance directly on the simulated remote server, `client.discover(...)` still returns only the original single instance, since the local cache hasn't been told anything changed; only after `client.refreshCache()` is explicitly called (representing the periodic background refresh a real Eureka Client performs automatically on its own configured schedule) does the discovery result include the newly registered instance — this trace makes concrete both the performance benefit of caching (most lookups are free) and its accepted cost (a bounded staleness window between refreshes), exactly the trade-off [service registry as source of truth](0187-service-registry-as-source-of-truth.md) describes for any correctly-implemented discovery cache.

## 7. Gotchas & takeaways

> **Gotcha:** the Eureka Client's default cache refresh interval (30 seconds by default) means a newly registered or newly deregistered instance can take up to that long to become visible to (or invisible to) other services' cached views — for use cases needing faster propagation of registration changes (rapid autoscaling events, fast-failing deployments), this interval may need to be tuned shorter, trading more frequent network traffic to the registry for fresher discovery data.

- Spring Cloud Netflix Eureka Client automatically handles self-registration, scheduled heartbeat sending, and local caching of registry data, activated through configuration and `@EnableDiscoveryClient` rather than manual application code.
- This eliminates the repetitive, error-prone boilerplate every service would otherwise need to implement itself for registration and heartbeat scheduling.
- Discovery lookups made by application code are served from a locally cached copy of the registry's data, avoiding a network round-trip to the registry server on every single lookup.
- The local cache is refreshed periodically in the background, introducing a bounded staleness window between when a registration change happens on the server and when it becomes visible in a given client's cached view.
- The cache refresh interval is a tunable trade-off between network overhead (more frequent refreshes cost more registry traffic) and freshness (faster propagation of registration changes) — worth adjusting deliberately for use cases sensitive to discovery latency.
