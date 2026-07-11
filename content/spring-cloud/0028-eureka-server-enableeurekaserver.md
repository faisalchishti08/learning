---
card: spring-cloud
gi: 28
slug: eureka-server-enableeurekaserver
title: "Eureka Server (@EnableEurekaServer)"
---

## 1. What it is

Eureka Server is Netflix's service registry: a standalone Spring Boot application, turned into a registry by adding one annotation, `@EnableEurekaServer`, to its main class. Once running, it holds an in-memory directory that maps service names (like `orders-service`) to the list of live network locations (host and port) currently running that service, and it keeps that directory up to date as instances start, stop, and send heartbeats.

```java
@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}
```

## 2. Why & when

In a microservices system, instances come and go: they scale up and down, restart after a deploy, or die and get replaced. Hardcoding "orders-service lives at 10.0.1.5:8080" into every caller's configuration breaks the moment that instance moves. Eureka Server exists to solve exactly that: instances register themselves with it when they start, and callers ask Eureka "who is `orders-service` right now?" instead of hardcoding an address.

Reach for Eureka Server when:

- You are running multiple instances of multiple services and need a single source of truth for "what's alive, and where."
- You want client-side load balancing (a caller picks from a list of live instances itself) rather than routing every call through a central load balancer.
- You are already in the Netflix/Spring Cloud ecosystem, or need a simple, self-hosted, AP-style (favors availability over strict consistency) registry that doesn't require an external coordination service like Zookeeper.

## 3. Core concept

```
                     +-------------------+
   register -------->|                   |
   (on startup)       |   Eureka Server   |<----- heartbeat every 30s
                       |  (in-memory       |       (renew lease)
   query -------------->  registry)       |
   ("who is X?")      |                   |
                       +-------------------+
                              |
                    evicts instance if no
                    heartbeat for ~90s
```

A Eureka Server does three things: accept registrations, accept periodic heartbeats that renew each instance's lease, and answer "give me the instance list for service X" queries — evicting any instance whose lease expires.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three service instances register with and send heartbeats to a central Eureka Server, which answers registry queries from callers">
  <rect x="250" y="20" width="140" height="44" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Eureka Server</text>

  <rect x="40" y="120" width="130" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="105" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">orders-service-1</text>
  <rect x="255" y="120" width="130" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">orders-service-2</text>
  <rect x="470" y="120" width="130" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="535" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">billing-service-1</text>

  <line x1="105" y1="120" x2="290" y2="64" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a28)"/>
  <line x1="320" y1="120" x2="320" y2="64" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a28)"/>
  <line x1="535" y1="120" x2="360" y2="64" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a28)"/>
  <text x="320" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">register + heartbeat every 30s</text>

  <rect x="250" y="180" width="140" height="30" rx="6" fill="#1c2430" stroke="#e6edf3" stroke-width="1"/>
  <text x="320" y="200" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">caller: "who is orders-service?"</text>
  <line x1="320" y1="180" x2="320" y2="64" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="3,3" marker-end="url(#a28)"/>

  <defs><marker id="a28" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Instances register and heartbeat upward; callers query the same registry to resolve a service name to a live address list.

## 5. Runnable example

The scenario: build a tiny in-memory service registry that mirrors what Eureka Server does — register instances, accept heartbeats, evict stale ones — starting from a bare list and growing into a lease-based registry with eviction.

### Level 1 — Basic

A registry that just stores instances by service name.

```java
import java.util.*;

public class EurekaServerLevel1 {
    static Map<String, List<String>> registry = new HashMap<>();

    static void register(String service, String address) {
        registry.computeIfAbsent(service, k -> new ArrayList<>()).add(address);
    }

    public static void main(String[] args) {
        register("orders-service", "10.0.1.5:8080");
        register("orders-service", "10.0.1.6:8080");
        register("billing-service", "10.0.2.1:8080");

        System.out.println("orders-service instances: " + registry.get("orders-service"));
        System.out.println("billing-service instances: " + registry.get("billing-service"));
    }
}
```

How to run: `java EurekaServerLevel1.java`

This is the bare mechanism: a map from service name to a list of addresses, filled by `register` calls. It has no notion of time — once registered, an instance stays forever, even if it has actually crashed.

### Level 2 — Intermediate

Add heartbeats and a lease expiry, so dead instances don't linger forever.

```java
import java.util.*;

public class EurekaServerLevel2 {
    static final long LEASE_DURATION_MS = 90_000;

    static class Lease {
        String address;
        long lastHeartbeat;
        Lease(String address, long now) { this.address = address; this.lastHeartbeat = now; }
        boolean expired(long now) { return now - lastHeartbeat > LEASE_DURATION_MS; }
    }

    static Map<String, List<Lease>> registry = new HashMap<>();

    static void register(String service, String address, long now) {
        registry.computeIfAbsent(service, k -> new ArrayList<>()).add(new Lease(address, now));
    }

    static void heartbeat(String service, String address, long now) {
        for (Lease l : registry.getOrDefault(service, List.of())) {
            if (l.address.equals(address)) l.lastHeartbeat = now;
        }
    }

    static List<String> query(String service, long now) {
        List<String> live = new ArrayList<>();
        for (Lease l : registry.getOrDefault(service, List.of())) {
            if (!l.expired(now)) live.add(l.address);
        }
        return live;
    }

    public static void main(String[] args) {
        long t0 = 0;
        register("orders-service", "10.0.1.5:8080", t0);
        register("orders-service", "10.0.1.6:8080", t0);

        long t1 = 30_000;
        heartbeat("orders-service", "10.0.1.5:8080", t1); // .6 never heartbeats again -- it crashed

        long t2 = 120_000; // 2 minutes later
        System.out.println("live at t2: " + query("orders-service", t2)); // only .5, .6 expired
    }
}
```

How to run: `java EurekaServerLevel2.java`

Each registered instance is now a `Lease` with a `lastHeartbeat` timestamp. `query` filters out any lease whose last heartbeat is older than the 90-second lease duration — exactly what Eureka Server does when an instance stops sending heartbeats without cleanly deregistering.

### Level 3 — Advanced

Add explicit deregistration (graceful shutdown) and a status field, since a real registry must distinguish "clean shutdown" from "silent crash," and callers should only see instances marked `UP`.

```java
import java.util.*;

public class EurekaServerLevel3 {
    static final long LEASE_DURATION_MS = 90_000;
    enum Status { STARTING, UP, DOWN }

    static class Lease {
        String address;
        Status status;
        long lastHeartbeat;
        Lease(String address, long now) { this.address = address; this.status = Status.STARTING; this.lastHeartbeat = now; }
        boolean expired(long now) { return now - lastHeartbeat > LEASE_DURATION_MS; }
    }

    static Map<String, List<Lease>> registry = new HashMap<>();

    static void register(String service, String address, long now) {
        registry.computeIfAbsent(service, k -> new ArrayList<>()).add(new Lease(address, now));
    }

    static void markUp(String service, String address) {
        find(service, address).ifPresent(l -> l.status = Status.UP);
    }

    static void heartbeat(String service, String address, long now) {
        find(service, address).ifPresent(l -> l.lastHeartbeat = now);
    }

    static void deregister(String service, String address) {
        // graceful shutdown: instance tells the registry it's leaving, no need to wait for expiry
        registry.getOrDefault(service, List.of()).removeIf(l -> l.address.equals(address));
    }

    static Optional<Lease> find(String service, String address) {
        return registry.getOrDefault(service, List.of()).stream()
                .filter(l -> l.address.equals(address)).findFirst();
    }

    static List<String> query(String service, long now) {
        List<String> live = new ArrayList<>();
        for (Lease l : registry.getOrDefault(service, List.of())) {
            if (l.status == Status.UP && !l.expired(now)) live.add(l.address);
        }
        return live;
    }

    public static void main(String[] args) {
        long t0 = 0;
        register("orders-service", "10.0.1.5:8080", t0);
        register("orders-service", "10.0.1.6:8080", t0);
        markUp("orders-service", "10.0.1.5:8080");
        markUp("orders-service", "10.0.1.6:8080");

        System.out.println("t0 query (both UP): " + query("orders-service", 5_000));

        deregister("orders-service", "10.0.1.6:8080"); // .6 shuts down cleanly
        heartbeat("orders-service", "10.0.1.5:8080", 30_000);

        System.out.println("after graceful shutdown: " + query("orders-service", 40_000));
    }
}
```

How to run: `java EurekaServerLevel3.java`

Now each lease carries a `Status`: an instance only becomes `UP` after finishing its own startup, and `deregister` removes an instance immediately on clean shutdown instead of forcing callers to wait out the full 90-second lease expiry. This mirrors real Eureka Server behavior: `STARTING` instances are excluded from query results until they self-report ready, and a clean `DELETE` on shutdown avoids the "stale entry for up to 90 seconds" window that a crash produces.

## 6. Walkthrough

Trace Level 3 end to end, since it's closest to real Eureka Server behavior.

1. `register("orders-service", "10.0.1.5:8080", t0)` runs first — a new `Lease` is created with `status = STARTING` and `lastHeartbeat = t0`. This models the real Eureka `POST /eureka/apps/{appName}` registration call an instance makes as it boots.
2. `markUp(...)` runs next for both instances — this models the instance finishing its own application startup and Eureka's health check confirming it, flipping status to `UP`. Only now is the instance eligible to appear in query results.
3. `query("orders-service", 5_000)` runs — it iterates the lease list, keeps only entries with `status == UP` and `!expired`, and returns both addresses. This models a caller's `GET /eureka/apps/orders-service` request; the real response is an XML/JSON payload listing each `<instance>` with its `hostName`, `port`, and `status`.
4. `deregister(...)` runs for instance `.6` — its lease is removed from the list immediately. This models a `DELETE /eureka/apps/{appName}/{instanceId}` call an instance makes as part of a graceful `SIGTERM` shutdown hook.
5. `heartbeat(...)` runs for instance `.5` at `t1 = 30_000` — its `lastHeartbeat` is bumped forward, resetting its 90-second expiry clock. This models the real Eureka Client's background thread sending a `PUT /eureka/apps/{appName}/{instanceId}` renewal every 30 seconds.
6. The final `query("orders-service", 40_000)` runs — `.6` is already gone (deregistered), `.5` is still within its lease window (last heartbeat at `30_000`, now is `40_000`, well under 90 seconds), so the result is just `["10.0.1.5:8080"]`.

```
register(.5) -> STARTING     register(.6) -> STARTING
markUp(.5)   -> UP           markUp(.6)   -> UP
                    |
              query -> [.5, .6]
                    |
        deregister(.6)     heartbeat(.5)
                    |
              query -> [.5]
```

## 7. Gotchas & takeaways

> **Gotcha:** a crashed instance that never calls deregister stays visible to callers for up to 90 seconds (the lease duration) after its last heartbeat — Eureka favors availability (serving a slightly stale list) over instantly-correct membership. Design callers to tolerate calling a dead instance occasionally and retrying.

- `@EnableEurekaServer` turns a plain Spring Boot app into a registry; it needs no database — the registry lives in memory and rebuilds itself from client re-registrations if the server restarts.
- Instances only appear in query results once their status is `UP`, not merely `STARTING` — this prevents callers from routing traffic to an instance that hasn't finished initializing.
- Clean deregistration on shutdown is strictly faster than waiting for lease expiry; production services should hook `SIGTERM` to deregister before the process exits.
- The default lease duration is 90 seconds with a 30-second heartbeat interval — three missed heartbeats before eviction, which is a deliberate buffer against transient network blips.
