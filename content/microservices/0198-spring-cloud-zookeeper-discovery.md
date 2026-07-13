---
card: microservices
gi: 198
slug: spring-cloud-zookeeper-discovery
title: "Spring Cloud Zookeeper discovery"
---

## 1. What it is

Spring Cloud Zookeeper integrates Apache ZooKeeper, a distributed coordination service, as a [service registry](0182-service-registry-concept.md) backend — service instances register themselves as ephemeral nodes in ZooKeeper's hierarchical namespace, and ZooKeeper's own session mechanism automatically removes an instance's node the moment its client session disconnects (a crash, a network partition, a clean shutdown), providing registration-and-liveness-tracking as a natural side effect of ZooKeeper's general-purpose coordination primitives rather than a purpose-built registry feature.

## 2. Why & when

ZooKeeper wasn't originally designed as a service registry specifically — it's a general-purpose distributed coordination primitive (used for leader election, distributed locks, configuration management, and more) that happens to provide exactly the properties a service registry needs: a hierarchical, replicated, consistent data store with a session-based ephemeral-node mechanism that automatically cleans up entries when a client disconnects. Teams already running ZooKeeper for other coordination needs (as is common in Hadoop, Kafka's older versions, and other distributed systems ecosystems) can reuse that same infrastructure for service discovery rather than standing up a separate, dedicated registry.

Choose Spring Cloud Zookeeper when ZooKeeper is already part of a system's infrastructure for other coordination needs, making its reuse for service discovery an efficient consolidation rather than a from-scratch adoption decision. For a system with no existing ZooKeeper dependency, [Eureka](0195-spring-cloud-netflix-eureka-server.md) or [Consul](0197-spring-cloud-consul-discovery.md) are more commonly the default choices, since they were purpose-built as registries and typically involve a simpler operational model for that specific use case alone.

## 3. Core concept

An instance registers by creating an ephemeral znode (ZooKeeper's node type) under a path representing its service name; ZooKeeper's session mechanism ties that znode's existence directly to the client's active session, so a session ending for any reason (graceful close, timeout, crash) automatically and immediately removes the znode, with no separate heartbeat-and-timeout logic needed — this behavior comes from ZooKeeper's core session model itself.

```java
// registration: create an EPHEMERAL znode -- tied DIRECTLY to this client's session
zooKeeper.create("/services/order-service/order-a", instanceData, CreateMode.EPHEMERAL);

// if the session ends (crash, disconnect, clean close) -- ZooKeeper ITSELF removes the znode
// NO separate heartbeat-timeout logic is needed; this is a property of the SESSION mechanism itself

// discovery: list children under the service's path
List<String> instances = zooKeeper.getChildren("/services/order-service", false);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An instance creates an ephemeral znode under /services/order-service tied to its ZooKeeper session; when that session ends for any reason, ZooKeeper automatically removes the znode as a direct consequence of its session mechanism, with no separate heartbeat logic involved" >
  <rect x="20" y="70" width="140" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Instance session</text>

  <rect x="230" y="30" width="200" height="110" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="50" fill="#8b949e" font-size="8" font-family="sans-serif">/services/order-service/</text>
  <rect x="250" y="65" width="160" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-a (ephemeral)</text>
  <text x="330" y="115" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">exists ONLY while session is alive</text>

  <line x1="160" y1="92" x2="248" y2="80" stroke="#8b949e" marker-end="url(#arr79)"/>

  <defs>
    <marker id="arr79" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The ephemeral znode's lifetime is directly tied to the session; no separate expiration logic is layered on top.

## 5. Runnable example

Scenario: an order-service registration modeled first with separately-tracked, manually-managed registration state (contrasting with ZooKeeper's built-in behavior), models ZooKeeper's ephemeral znode mechanism where registration is automatically tied to session lifetime, and finally demonstrates the automatic cleanup on both a clean session close and an abrupt session timeout, both handled uniformly by the same underlying mechanism with no separate code paths.

### Level 1 — Basic

```java
// File: ManuallyTrackedRegistration.java -- registration state tracked SEPARATELY
// from any session concept -- requires EXPLICIT cleanup logic for every disconnect scenario.
import java.util.*;

public class ManuallyTrackedRegistration {
    static Set<String> registeredPaths = new HashSet<>();

    static void register(String path) { registeredPaths.add(path); System.out.println("registered: " + path); }
    static void handleCleanDisconnect(String path) { registeredPaths.remove(path); System.out.println("MANUALLY cleaned up on clean disconnect: " + path); }
    static void handleCrashDetection(String path) { registeredPaths.remove(path); System.out.println("MANUALLY cleaned up after crash-detection logic: " + path); }
    // EACH disconnect scenario needs its OWN explicit cleanup call -- easy to miss one

    public static void main(String[] args) {
        register("/services/order-service/order-a");
        handleCleanDisconnect("/services/order-service/order-a");
        System.out.println("This required TWO separate concepts: registration state, AND separate cleanup logic per disconnect scenario.");
    }
}
```

**How to run:** `javac ManuallyTrackedRegistration.java && java ManuallyTrackedRegistration` (JDK 17+).

### Level 2 — Intermediate

```java
// File: EphemeralNodeTiedToSession.java -- registration is TIED DIRECTLY to a
// SESSION object's lifetime -- ONE mechanism handles EVERY disconnect scenario uniformly.
import java.util.*;

public class EphemeralNodeTiedToSession {
    static class ZkSession {
        String sessionId;
        boolean alive = true;
        List<String> ephemeralNodes = new ArrayList<>(); // nodes THIS session created
        ZkSession(String sessionId) { this.sessionId = sessionId; }

        void createEphemeral(String path) {
            ephemeralNodes.add(path);
            System.out.println("[session " + sessionId + "] created ephemeral znode: " + path);
        }

        // ONE method handles EVERY way a session can end -- clean close, timeout, crash detection, ALL THE SAME
        void endSession(String reason) {
            alive = false;
            System.out.println("[session " + sessionId + "] ended (" + reason + ") -- ZooKeeper AUTOMATICALLY removes ALL ephemeral nodes: " + ephemeralNodes);
            ephemeralNodes.clear(); // automatic, NOT a separate, hand-written cleanup call
        }
    }

    public static void main(String[] args) {
        ZkSession session = new ZkSession("sess-001");
        session.createEphemeral("/services/order-service/order-a");

        session.endSession("client closed connection cleanly");
        System.out.println("registeredNodes remaining for this session: " + session.ephemeralNodes);
        System.out.println("ONE unified mechanism (session end) handled cleanup -- no separate 'clean disconnect' vs 'crash' code paths needed.");
    }
}
```

**How to run:** `javac EphemeralNodeTiedToSession.java && java EphemeralNodeTiedToSession` (JDK 17+).

Expected output:
```
[session sess-001] created ephemeral znode: /services/order-service/order-a
[session sess-001] ended (client closed connection cleanly) -- ZooKeeper AUTOMATICALLY removes ALL ephemeral nodes: [/services/order-service/order-a]
registeredNodes remaining for this session: []
ONE unified mechanism (session end) handled cleanup -- no separate 'clean disconnect' vs 'crash' code paths needed.
```

### Level 3 — Advanced

```java
// File: UniformHandlingAcrossDisconnectTypes.java -- BOTH a graceful shutdown
// AND an abrupt crash-and-timeout result in IDENTICAL cleanup behavior, since
// BOTH simply end the session -- ZooKeeper doesn't distinguish the REASON.
import java.util.*;

public class UniformHandlingAcrossDisconnectTypes {
    static class ZkSession {
        String sessionId;
        List<String> ephemeralNodes = new ArrayList<>();
        long sessionTimeoutMillis;
        long lastActivityMillis;
        ZkSession(String sessionId, long sessionTimeoutMillis, long nowMillis) {
            this.sessionId = sessionId; this.sessionTimeoutMillis = sessionTimeoutMillis; this.lastActivityMillis = nowMillis;
        }
        void createEphemeral(String path) { ephemeralNodes.add(path); }
        void heartbeatOrActivity(long nowMillis) { lastActivityMillis = nowMillis; } // ANY client activity resets the session timeout

        // simulates ZooKeeper's OWN internal session-expiry check -- NOT application-written cleanup logic
        boolean checkAndExpireIfTimedOut(long nowMillis) {
            if (nowMillis - lastActivityMillis > sessionTimeoutMillis) {
                System.out.println("[ZooKeeper internal] session " + sessionId + " TIMED OUT (no activity) -- auto-removing: " + ephemeralNodes);
                ephemeralNodes.clear();
                return true;
            }
            return false;
        }
        void gracefulClose() { // explicit disconnect -- SAME cleanup outcome as a timeout
            System.out.println("[ZooKeeper internal] session " + sessionId + " CLOSED gracefully -- auto-removing: " + ephemeralNodes);
            ephemeralNodes.clear();
        }
    }

    public static void main(String[] args) {
        // SCENARIO 1: graceful shutdown
        ZkSession gracefulSession = new ZkSession("sess-graceful", 5000, 0);
        gracefulSession.createEphemeral("/services/order-service/order-a");
        gracefulSession.gracefulClose();
        System.out.println("After graceful close: " + gracefulSession.ephemeralNodes.size() + " nodes remain\n");

        // SCENARIO 2: abrupt crash -- NO graceful close call, session just goes silent, and TIMES OUT
        ZkSession crashedSession = new ZkSession("sess-crashed", 5000, 0);
        crashedSession.createEphemeral("/services/order-service/order-b");
        // no heartbeatOrActivity() calls happen after this -- the process CRASHED
        crashedSession.checkAndExpireIfTimedOut(3000); // too soon -- session hasn't timed out yet
        System.out.println("At t=3000 (before timeout): " + crashedSession.ephemeralNodes.size() + " nodes remain");
        crashedSession.checkAndExpireIfTimedOut(6000); // NOW past the 5000ms timeout
        System.out.println("At t=6000 (after timeout): " + crashedSession.ephemeralNodes.size() + " nodes remain");

        System.out.println("\nBOTH scenarios reached the IDENTICAL outcome (0 nodes remaining) through the SAME underlying session-ending mechanism -- no separate code paths were needed for 'graceful' vs 'crash'.");
    }
}
```

**How to run:** `javac UniformHandlingAcrossDisconnectTypes.java && java UniformHandlingAcrossDisconnectTypes` (JDK 17+).

Expected output:
```
[ZooKeeper internal] session sess-graceful CLOSED gracefully -- auto-removing: [/services/order-service/order-a]
After graceful close: 0 nodes remain

At t=3000 (before timeout): 1 nodes remain
[ZooKeeper internal] session sess-crashed TIMED OUT (no activity) -- auto-removing: [/services/order-service/order-b]
At t=6000 (after timeout): 0 nodes remain

BOTH scenarios reached the IDENTICAL outcome (0 nodes remaining) through the SAME underlying session-ending mechanism -- no separate code paths were needed for 'graceful' vs 'crash'.
```

## 6. Walkthrough

1. **Level 1** — `handleCleanDisconnect` and `handleCrashDetection` are two entirely separate methods, each explicitly manipulating `registeredPaths`; supporting a third kind of disconnect scenario would require writing yet another, similarly-shaped cleanup method.
2. **Level 2, ephemeral nodes owned by a session object** — `ZkSession.ephemeralNodes` is a list local to a specific session instance, and `createEphemeral` simply appends to it, modeling how a real ZooKeeper client's ephemeral znode creation is inherently associated with that client's current session.
3. **Level 2, one method for every ending reason** — `endSession(String reason)` takes a free-text description of *why* the session ended, but its actual cleanup logic (`ephemeralNodes.clear()`) is identical regardless of that reason — this is the key structural point: the mechanism doesn't branch on disconnect type at all.
4. **Level 2, the demonstrated simplicity** — calling `endSession("client closed connection cleanly")` produces the identical cleanup behavior that a crash or timeout reason string would produce, since the reason is purely informational logging, not a branch in the cleanup logic itself.
5. **Level 3, timeout as the crash-detection mechanism** — `checkAndExpireIfTimedOut` compares elapsed time since `lastActivityMillis` against `sessionTimeoutMillis`, mirroring ZooKeeper's own internal session-timeout mechanism that detects an unresponsive client (a crash, a severed network connection) without requiring any explicit "I crashed" signal — the absence of expected activity is itself sufficient.
6. **Level 3, the two scenarios converging on identical cleanup** — `gracefulSession.gracefulClose()` and `crashedSession.checkAndExpireIfTimedOut(6000)` (which returns `true` and clears nodes) both end with `ephemeralNodes` empty; despite representing genuinely different real-world situations (a deliberate, orderly shutdown versus an unplanned failure), both paths call the identical `ephemeralNodes.clear()` operation.
7. **Level 3, why this uniformity matters** — the final printed statement makes the key architectural point explicit: because ZooKeeper's ephemeral-node cleanup is a direct, built-in consequence of its general session-management mechanism rather than something layered on top as separate registry-specific logic, there is structurally no way to correctly handle one disconnect scenario while forgetting another — unlike Level 1's hand-written approach, where a developer could easily implement cleanup for graceful disconnects but forget or mishandle the crash-detection case, ZooKeeper's session model makes that class of bug impossible by construction.

## 7. Gotchas & takeaways

> **Gotcha:** ZooKeeper's session timeout, by default, can be on the order of tens of seconds — meaning a crashed instance's ephemeral node (and therefore its registry entry) may persist for a noticeably longer window than a well-tuned Eureka [lease duration](0189-heartbeats-lease-renewal.md) would allow, since ZooKeeper's timeout is a general-purpose session parameter, not one specifically tuned for fast service-discovery failure detection; this session timeout often needs deliberate tuning if fast discovery-failure detection is a priority.

- Spring Cloud Zookeeper uses ZooKeeper's ephemeral znode mechanism as a service registry, where registration lifetime is directly tied to the underlying client session rather than managed through separate, purpose-built registry logic.
- ZooKeeper's session-ending behavior (graceful close, timeout, or crash detection) uniformly triggers automatic removal of that session's ephemeral nodes, with no separate cleanup code paths needed for different disconnect scenarios.
- This is attractive specifically for teams already running ZooKeeper for other distributed coordination needs, letting service discovery reuse existing infrastructure rather than requiring a separate, dedicated registry.
- The uniform session model structurally eliminates the class of bug where cleanup logic is correctly implemented for one disconnect scenario but forgotten for another.
- ZooKeeper's session timeout is a general-purpose parameter not specifically tuned for service-discovery failure-detection speed, and often needs deliberate adjustment to achieve responsiveness comparable to a purpose-built registry's lease duration.
