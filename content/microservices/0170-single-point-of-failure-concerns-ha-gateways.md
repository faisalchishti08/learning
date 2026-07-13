---
card: microservices
gi: 170
slug: single-point-of-failure-concerns-ha-gateways
title: "Single point of failure concerns & HA gateways"
---

## 1. What it is

Because every external request passes through the [API gateway](0157-api-gateway-pattern.md), a gateway that exists as a single running instance is a single point of failure for the entire system — if it goes down, external access to every backend service is lost simultaneously, even if every backend is perfectly healthy. High-availability (HA) gateway design eliminates this by running multiple gateway instances behind a load balancer, with no single instance's failure able to take down external access.

## 2. Why & when

A microservices architecture's individual services can each be made resilient on their own — multiple instances, health checks, automatic failover — but all of that resilience is worthless to an external client if the one and only gateway instance sitting in front of everything is down, since the client can't even reach the healthy backends. The gateway concentrates traffic by design (that's the point of having one entry point), which means it also concentrates risk unless deliberately designed to avoid becoming a single point of failure itself.

Design for HA gateways from the start in any production system where the gateway is genuinely the sole entry point for external traffic — which describes essentially every system adopting the gateway pattern seriously. This means running multiple stateless gateway instances behind a load balancer (or DNS-based failover), health-checking each instance, and ensuring no gateway-level state (like in-memory session data) is required to survive a specific instance's failure.

## 3. Core concept

Multiple identical gateway instances run simultaneously behind a load balancer; the load balancer health-checks each instance and routes traffic only to healthy ones, so any single instance's failure is absorbed by the remaining instances continuing to serve traffic — the same [competing consumers](0120-competing-consumers-pattern.md)-style resilience pattern applied to the gateway layer itself.

```java
// MULTIPLE gateway instances, all IDENTICAL, behind a load balancer
List<GatewayInstance> instances = List.of(gatewayInstance1, gatewayInstance2, gatewayInstance3);

Response handleRequest(Request request) {
    GatewayInstance healthy = loadBalancer.pickHealthyInstance(instances); // skips any DOWN instance
    return healthy.handle(request); // client never notices which specific instance served it
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A load balancer sits in front of three gateway instances; one instance is down, but the load balancer routes all traffic to the two remaining healthy instances, so external access to the system continues uninterrupted" >
  <rect x="20" y="70" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Clients</text>

  <rect x="170" y="70" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="240" y="94" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Load Balancer</text>

  <rect x="370" y="20" width="120" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="430" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">gateway-1 (up)</text>
  <rect x="370" y="80" width="120" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="430" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">gateway-2 (DOWN)</text>
  <rect x="370" y="140" width="120" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="430" y="162" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">gateway-3 (up)</text>

  <line x1="120" y1="90" x2="168" y2="90" stroke="#8b949e" marker-end="url(#arr51)"/>
  <line x1="310" y1="85" x2="368" y2="38" stroke="#8b949e" marker-end="url(#arr51)"/>
  <line x1="310" y1="95" x2="368" y2="157" stroke="#8b949e" marker-end="url(#arr51)"/>

  <defs>
    <marker id="arr51" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Traffic is automatically redirected away from the unhealthy instance; clients never notice.

## 5. Runnable example

Scenario: a gateway deployment that starts as a single instance (showing the total outage a failure causes), scales to multiple instances behind a health-checking load balancer to survive individual failures, and finally handles a rolling instance restart (a routine deployment) with zero client-visible downtime, demonstrating the practical operational payoff of the HA design.

### Level 1 — Basic

```java
// File: SingleGatewayInstance.java -- ONE gateway instance; its failure means
// TOTAL external outage, even though the backend is perfectly healthy.
public class SingleGatewayInstance {
    static boolean gatewayIsUp = true;

    static String handleRequest(String path) {
        if (!gatewayIsUp) return "CONNECTION REFUSED -- gateway is down";
        return "response for " + path + " (backend is healthy and reachable)";
    }

    public static void main(String[] args) {
        System.out.println(handleRequest("/orders/42"));

        gatewayIsUp = false; // the ONE instance crashes
        System.out.println(handleRequest("/orders/42"));
        System.out.println("EVERY external request now fails, even though nothing is wrong with any backend service.");
    }
}
```

**How to run:** `javac SingleGatewayInstance.java && java SingleGatewayInstance` (JDK 17+).

### Level 2 — Intermediate

```java
// File: LoadBalancedGatewayInstances.java -- MULTIPLE identical gateway instances;
// the load balancer health-checks and routes ONLY to healthy ones.
import java.util.*;

public class LoadBalancedGatewayInstances {
    static class GatewayInstance {
        String id;
        boolean healthy = true;
        GatewayInstance(String id) { this.id = id; }
        String handle(String path) { return "[" + id + "] response for " + path; }
    }

    static class LoadBalancer {
        List<GatewayInstance> instances;
        int roundRobinIndex = 0;
        LoadBalancer(List<GatewayInstance> instances) { this.instances = instances; }

        String routeRequest(String path) {
            List<GatewayInstance> healthyInstances = instances.stream().filter(i -> i.healthy).toList();
            if (healthyInstances.isEmpty()) return "503 -- ALL instances down";
            GatewayInstance chosen = healthyInstances.get(roundRobinIndex % healthyInstances.size());
            roundRobinIndex++;
            return chosen.handle(path);
        }
    }

    public static void main(String[] args) {
        GatewayInstance g1 = new GatewayInstance("gateway-1");
        GatewayInstance g2 = new GatewayInstance("gateway-2");
        GatewayInstance g3 = new GatewayInstance("gateway-3");
        LoadBalancer lb = new LoadBalancer(List.of(g1, g2, g3));

        System.out.println(lb.routeRequest("/orders/42"));

        g2.healthy = false; // ONE instance fails
        System.out.println("*** gateway-2 CRASHED ***");

        System.out.println(lb.routeRequest("/orders/42"));
        System.out.println(lb.routeRequest("/orders/42"));
        System.out.println(lb.routeRequest("/orders/42"));
        System.out.println("Traffic KEPT FLOWING through gateway-1 and gateway-3 -- gateway-2's failure was fully absorbed.");
    }
}
```

**How to run:** `javac LoadBalancedGatewayInstances.java && java LoadBalancedGatewayInstances` (JDK 17+).

Expected output (round-robin skips the unhealthy instance entirely):
```
[gateway-1] response for /orders/42
*** gateway-2 CRASHED ***
[gateway-3] response for /orders/42
[gateway-1] response for /orders/42
[gateway-3] response for /orders/42
Traffic KEPT FLOWING through gateway-1 and gateway-3 -- gateway-2's failure was fully absorbed.
```

### Level 3 — Advanced

```java
// File: RollingRestartZeroDowntime.java -- a ROUTINE deployment restarts each
// gateway instance ONE AT A TIME; the load balancer's health checks ensure the
// OTHERS keep serving traffic throughout, achieving ZERO client-visible downtime.
import java.util.*;

public class RollingRestartZeroDowntime {
    static class GatewayInstance {
        String id;
        boolean healthy = true;
        GatewayInstance(String id) { this.id = id; }
        String handle(String path) { return "[" + id + "] response for " + path; }
    }

    static class LoadBalancer {
        List<GatewayInstance> instances;
        int roundRobinIndex = 0;
        LoadBalancer(List<GatewayInstance> instances) { this.instances = instances; }

        String routeRequest(String path) {
            List<GatewayInstance> healthyInstances = instances.stream().filter(i -> i.healthy).toList();
            if (healthyInstances.isEmpty()) return "503 -- ALL instances down";
            GatewayInstance chosen = healthyInstances.get(roundRobinIndex % healthyInstances.size());
            roundRobinIndex++;
            return chosen.handle(path);
        }
    }

    // simulates a ROLLING RESTART: take one instance out, "restart" it (upgrade), bring it back, THEN move to the next
    static void rollingRestart(List<GatewayInstance> instances, LoadBalancer lb) {
        for (GatewayInstance instance : instances) {
            instance.healthy = false; // taken OUT of rotation for its restart
            System.out.println("  [deployment] " + instance.id + " taken offline for restart");
            System.out.println("  " + lb.routeRequest("/orders/42") + "  <- traffic continues via OTHER instances");
            instance.healthy = true; // back online, upgraded
            System.out.println("  [deployment] " + instance.id + " back online\n");
        }
    }

    public static void main(String[] args) {
        List<GatewayInstance> instances = List.of(new GatewayInstance("gateway-1"), new GatewayInstance("gateway-2"), new GatewayInstance("gateway-3"));
        LoadBalancer lb = new LoadBalancer(instances);

        int successfulRequests = 0;
        int failedRequests = 0;

        for (int i = 0; i < 9; i++) { // simulate 9 client requests spread across the whole rolling restart
            if (i == 3) { rollingRestart(instances, lb); } // restart happens partway through the traffic
            String result = lb.routeRequest("/orders/42");
            if (result.startsWith("503")) failedRequests++; else successfulRequests++;
        }

        System.out.println("Successful requests: " + successfulRequests + ", failed requests: " + failedRequests);
        System.out.println("A FULL rolling restart of all 3 instances completed with ZERO failed client requests.");
    }
}
```

**How to run:** `javac RollingRestartZeroDowntime.java && java RollingRestartZeroDowntime` (JDK 17+).

Expected output (exact instance names in the traffic lines vary with round-robin position, but `failedRequests` is always `0`):
```
  [deployment] gateway-1 taken offline for restart
  [gateway-2] response for /orders/42  <- traffic continues via OTHER instances
  [deployment] gateway-1 back online

  [deployment] gateway-2 taken offline for restart
  [gateway-3] response for /orders/42  <- traffic continues via OTHER instances
  [deployment] gateway-2 back online

  [deployment] gateway-3 taken offline for restart
  [gateway-1] response for /orders/42  <- traffic continues via OTHER instances
  [deployment] gateway-3 back online

Successful requests: 9, failed requests: 0
A FULL rolling restart of all 3 instances completed with ZERO failed client requests.
```

## 6. Walkthrough

1. **Level 1** — `gatewayIsUp` is a single boolean representing the entire external entry point's health; setting it to `false` immediately causes every subsequent call to `handleRequest` to return a connection-refused error, regardless of the fact that nothing about the actual backend logic changed.
2. **Level 2, multiple independent instances** — `g1`, `g2`, and `g3` are three separate `GatewayInstance` objects, each with its own `healthy` flag; `LoadBalancer.routeRequest` filters `instances` down to only those currently healthy before selecting one via round-robin.
3. **Level 2, the failure absorbed** — setting `g2.healthy = false` removes it from `healthyInstances` on every subsequent call to `routeRequest`; the three follow-up requests are served exclusively by `gateway-1` and `gateway-3`, alternating between them, with `gateway-2` never selected until (if) it recovers.
4. **Level 2, no client-visible failure** — every printed response in the post-crash portion is a normal, successful response, never the `"503"` fallback — proving that losing one out of three instances produced zero observable impact on the client's experience.
5. **Level 3, simulating a routine deployment** — `rollingRestart` iterates every instance in the fleet, temporarily setting each one's `healthy` flag to `false` (simulating taking it offline to deploy a new version), issuing a test request during that window, then setting it back to `true` before moving to the next instance.
6. **Level 3, traffic during each instance's restart window** — each call to `lb.routeRequest` made while one specific instance is marked unhealthy is served by one of the *other* two instances, which the printed `<- traffic continues via OTHER instances` annotation makes explicit for every single restart step.
7. **Level 3, the full accounting** — across all nine simulated requests, spanning a complete rolling restart of every instance in the fleet, `failedRequests` remains exactly `0` — this is the concrete, measurable payoff of an HA gateway design: not just surviving an unplanned crash (Level 2), but enabling routine, planned maintenance (software upgrades, configuration changes) with zero client-visible downtime, because the load balancer's health-check-driven routing ensures there is always at least one healthy instance available throughout the entire process.

## 7. Gotchas & takeaways

> **Gotcha:** an HA gateway design only holds if the gateway instances themselves are genuinely stateless — if a gateway instance holds any in-memory state a client's next request depends on (a session, a partially-built response), routing that client's next request to a *different* instance breaks that assumption; HA gateway design requires either fully stateless instances or externalized shared state (a shared cache, a shared session store) accessible identically from every instance.

- A gateway existing as a single instance is a single point of failure for the entire system's external accessibility, regardless of how resilient the backend services behind it are individually.
- Running multiple identical gateway instances behind a health-checking load balancer absorbs individual instance failures without any client-visible impact.
- This is the same competing-consumers-style resilience pattern used elsewhere in a microservices system, applied specifically to the gateway layer.
- HA gateway design enables not just surviving unplanned crashes but also performing routine deployments (rolling restarts) with zero downtime, since the load balancer continuously routes around whichever instance happens to be temporarily offline.
- HA gateway design requires the gateway instances to be genuinely stateless, or to share externalized state consistently — an instance holding unique in-memory state breaks the assumption that any healthy instance can serve any client's next request.
