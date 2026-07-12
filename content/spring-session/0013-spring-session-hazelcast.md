---
card: spring-session
gi: 13
slug: spring-session-hazelcast
title: "Spring Session Hazelcast"
---

## 1. What it is

`spring-session-hazelcast` is the Hazelcast-backed implementation of Spring Session, wired via `@EnableHazelcastHttpSession`. It stores session data in a Hazelcast distributed `IMap`, relying on Hazelcast's own clustering and native entry-TTL support for replication and expiration, similar in spirit to the Redis integration (card 0009) but built on Hazelcast's embedded, JVM-native clustering model instead of a separate server process.

## 2. Why & when

Hazelcast is fundamentally different from Redis in deployment shape: rather than being a standalone server processes connect to over the network, Hazelcast is typically embedded directly inside the application's own JVM, with instances discovering and clustering with each other automatically. For teams already using Hazelcast as their distributed cache or compute grid, backing Spring Session with the same technology avoids introducing an entirely separate piece of infrastructure (Redis) purely for sessions — one clustering technology serves both needs.

Reach for Spring Session Hazelcast when:

- Hazelcast is already part of the application's stack (as a distributed cache, a compute grid, or for other clustered data needs) — reusing it for sessions avoids operating two different clustering technologies side by side.
- Preferring an embedded, JVM-native clustering model over a separate server process — Hazelcast nodes typically run inside the application instances themselves, with no separate server to deploy and monitor.
- Deciding between Hazelcast, Redis (card 0009), and JDBC (card 0012) — Hazelcast is the right choice specifically when the team's existing infrastructure and operational familiarity already center on it; it's not generally a reason to introduce Hazelcast fresh purely for session storage if Redis or JDBC are already comfortable choices.

## 3. Core concept

Think of Redis as a shared central warehouse — every application instance drives to the same external building to store and retrieve items. Hazelcast is more like each application instance carrying its own storage locker that automatically syncs its contents with every other instance's locker in real time — there's no separate central building; the "warehouse" is actually distributed across and embedded within the application instances themselves, coordinating directly with each other over the network to stay consistent.

```java
@Configuration
@EnableHazelcastHttpSession
public class HazelcastSessionConfig {

    @Bean
    public HazelcastInstance hazelcastInstance() {
        Config config = new Config();
        config.getMapConfig("spring:session:sessions")
                .setTimeToLiveSeconds(1800); // matches maxInactiveInterval
        return Hazelcast.newHazelcastInstance(config);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each application instance embeds a Hazelcast node; nodes cluster together and replicate session data among themselves directly">
  <rect x="30" y="30" width="160" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">App Instance A</text>
  <text x="110" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(embedded Hazelcast)</text>

  <rect x="250" y="30" width="160" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">App Instance B</text>
  <text x="330" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(embedded Hazelcast)</text>

  <rect x="470" y="30" width="160" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">App Instance C</text>
  <text x="550" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(embedded Hazelcast)</text>

  <line x1="190" y1="65" x2="245" y2="65" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="410" y1="65" x2="465" y2="65" stroke="#3fb950" stroke-width="1.5"/>
  <text x="330" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">nodes discover each other and form a cluster directly — no separate server</text>
</svg>

Contrast this with Redis (card 0009), where instances connect out to one external, standalone server instead of clustering with each other directly.

## 5. Runnable example

The scenario: enabling Hazelcast-backed sessions for a single-instance setup first, growing to run two clustered instances and prove session data replicates between them, and finally to configure Hazelcast's map eviction and backup settings for production resilience.

### Level 1 — Basic

```java
// HazelcastSessionConfig.java
import com.hazelcast.config.Config;
import com.hazelcast.core.Hazelcast;
import com.hazelcast.core.HazelcastInstance;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.session.hazelcast.config.annotation.web.http.EnableHazelcastHttpSession;

@Configuration
@EnableHazelcastHttpSession
public class HazelcastSessionConfig {

    @Bean
    public HazelcastInstance hazelcastInstance() {
        Config config = new Config();
        config.setInstanceName("spring-session-hazelcast");
        return Hazelcast.newHazelcastInstance(config);
    }
}
```

**How to run:** with `spring-session-hazelcast` and `hazelcast` on the classpath, start the app and make a request touching the session. Expected behavior: the session works exactly like any other Spring Session-backed setup (card 0006's transparency) — attribute reads and writes behave identically to Redis or JDBC-backed sessions from the application's point of view.

### Level 2 — Intermediate

Running two application instances with Hazelcast's default multicast discovery lets them automatically find and cluster with each other — proving session data genuinely replicates without any explicit connection configuration, the way Redis's single shared server made trivially obvious but which needs demonstrating here since there's no single central store to inspect.

```java
import jakarta.servlet.http.HttpSession;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ClusterProofController {

    @GetMapping("/cluster-check")
    public String checkSession(HttpSession session) {
        Integer visits = (Integer) session.getAttribute("visits");
        visits = (visits == null ? 0 : visits) + 1;
        session.setAttribute("visits", visits);
        return "Visit #" + visits + " served by this JVM instance";
    }
}
```

**How to run:** run two instances of the same jar on different ports (`-Dserver.port=8081` and `-Dserver.port=8082`) on the same local network, allowing Hazelcast's default multicast discovery to find both. `curl -c c.txt http://localhost:8081/cluster-check` then `curl -b c.txt http://localhost:8082/cluster-check`. Expected output: `Visit #2` from instance B, proving it read and incremented the session instance A created — direct evidence the two embedded Hazelcast nodes formed a cluster and replicated the session data between themselves.

What changed: this proves the peer-to-peer clustering model actually works as advertised — no central server was involved, yet both instances see and correctly update the same shared session state.

### Level 3 — Advanced

Production Hazelcast configuration needs explicit backup counts (so a single node crashing doesn't lose session data that was only ever stored on that one node) and often TCP/IP-based discovery instead of multicast, since multicast is frequently blocked or unreliable in real cloud network environments.

```java
import com.hazelcast.config.Config;
import com.hazelcast.config.JoinConfig;
import com.hazelcast.config.MapConfig;
import com.hazelcast.core.Hazelcast;
import com.hazelcast.core.HazelcastInstance;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ProductionHazelcastConfig {

    @Bean
    public HazelcastInstance hazelcastInstance() {
        Config config = new Config();

        // Explicit backups: session data survives one node dying, since a copy
        // lives on at least one other node too, not just the node that created it.
        MapConfig sessionMapConfig = config.getMapConfig("spring:session:sessions");
        sessionMapConfig.setBackupCount(1);
        sessionMapConfig.setTimeToLiveSeconds(1800);

        // TCP/IP discovery: explicit member list, more reliable than multicast
        // in most real cloud network environments where multicast is often blocked.
        JoinConfig join = config.getNetworkConfig().getJoin();
        join.getMulticastConfig().setEnabled(false);
        join.getTcpIpConfig().setEnabled(true).addMember("10.0.1.10").addMember("10.0.1.11");

        return Hazelcast.newHazelcastInstance(config);
    }
}
```

**How to run:** deploy this configuration across instances with known static or service-discovered IPs (adjusting the member list per environment), then kill one instance mid-session and verify via a surviving instance that the session data is still present (thanks to `backupCount(1)` having replicated it elsewhere before the crash). Expected behavior: the session survives the killed node's disappearance, since a backup copy already existed on a different node — losing the node that originally created the session doesn't lose the session itself.

What changed and why it's production-flavored: this closes the real gap between "clustering works when nothing fails" and "clustering survives an actual node failure" — without an explicit backup count, a session that only ever lived on one node's local Hazelcast partition is lost entirely the instant that specific node crashes, defeating much of the resilience clustering was meant to provide in the first place.

## 6. Walkthrough

Tracing a session read/write across two clustered Hazelcast nodes, in execution order:

1. Instance A and instance B start up; each embeds its own Hazelcast node, and via TCP/IP discovery (Level 3) they locate each other and form a single logical cluster.
2. Hazelcast internally partitions the distributed `IMap` used for session storage across the cluster's members — a given session's data lives primarily on one partition (owned by one node) with backup copies on others, per `backupCount`.
3. A request lands on instance A; `SessionRepositoryFilter` (card 0004) creates a new session, and Hazelcast's `IMap.put(...)` stores it — Hazelcast automatically determines which partition (and therefore which node) owns this specific session ID, and replicates a backup copy to at least one other node per the configured `backupCount`.
4. A subsequent request from the same client, carrying the same session cookie, happens to land on instance B (a different node, via the load balancer).
5. Instance B's `SessionRepositoryFilter` calls `findById(...)`, which Hazelcast resolves by locating the owning partition for that session ID — regardless of which physical node currently owns it, Hazelcast's internal routing finds and returns the correct, up-to-date session data, exactly as instance A last wrote it.
6. If the node that originally owned this session's partition crashes at any point, Hazelcast automatically promotes the backup copy on another node to become the new primary — the session survives, and subsequent lookups continue to succeed transparently, application code and Spring Session's own logic completely unaware any failover occurred.

```
Instance A: session created -> Hazelcast IMap.put(id, data)
                                       |
                        Hazelcast partitions + replicates (backupCount=1)
                                       |
Instance B: findById(id) -> Hazelcast resolves owning partition -> returns data
   |
(node holding primary copy crashes)
   |
Hazelcast promotes backup copy on surviving node -> session data preserved
```

## 7. Gotchas & takeaways

> Multicast-based discovery (Hazelcast's simplest default) frequently doesn't work in cloud environments (AWS, GCP, Kubernetes) where multicast traffic is commonly blocked by network policy — a setup that clusters perfectly on a local development machine can silently fail to cluster at all once deployed, with each instance ending up isolated and unaware of the others. Always use TCP/IP or a cloud-specific discovery mechanism (Level 3) for real deployments, never rely on multicast working in production.

- `backupCount` is not optional for genuine resilience — a `backupCount` of `0` means a session's data exists on exactly one node, and that node crashing loses every session it was hosting; `backupCount(1)` (one backup copy) is a reasonable production minimum.
- Because Hazelcast nodes are typically embedded directly in the application JVM, session storage and application logic share the same process's memory and CPU — under heavy load, session storage overhead genuinely competes with application workload for resources, unlike Redis where session storage load is isolated in a separate process entirely.
- Session `timeToLiveSeconds` on the Hazelcast map configuration should be kept in sync with Spring Session's own `maxInactiveInterval` configuration — a mismatch between the two leads to confusing behavior where Hazelcast evicts entries at a different cadence than the application believes sessions should expire.
- Rolling deployments need care with Hazelcast clustering — a node leaving the cluster (during a deploy) triggers partition rebalancing and, depending on timing and backup configuration, could briefly affect session availability for sessions whose only backup happened to also be on a node currently restarting; stagger rolling restarts appropriately.
- Choosing Hazelcast purely for Spring Session, without any other existing use for Hazelcast in the stack, adds a genuinely different operational model (embedded clustering, partition/backup tuning, discovery configuration) compared to the more common Redis or JDBC choices — this is a reasonable choice when Hazelcast is already present for other reasons, but a heavier one to introduce from scratch than either alternative.
