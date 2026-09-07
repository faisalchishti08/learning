---
card: system-design
gi: 132
slug: health-checks-heartbeats
title: Health checks & heartbeats
---

## 1. What it is

A **health check** is a request sent to a service specifically to ask "are you working correctly right now?" — typically a lightweight HTTP endpoint (like `/health`) that returns a simple healthy/unhealthy status. A **heartbeat** is the same idea from the opposite direction: instead of being asked, a node periodically announces "I am still alive" on its own, and the absence of an expected heartbeat is treated as a failure signal.

## 2. Why & when

Redundancy (running multiple instances) only helps if the system actually knows *which* instances are currently healthy — otherwise a load balancer keeps sending traffic to a crashed or hung instance, and a failover system never knows a primary has died. Health checks and heartbeats are how a system detects failure in the first place, which is the necessary first step before any redundancy, failover, or [circuit breaker](0136-circuit-breaker.md) mechanism can react to it. Use health checks for anything a load balancer or orchestrator (Kubernetes, a cloud load balancer) routes traffic to. Use heartbeats for components that need to actively signal liveness to a monitor, such as nodes in a cluster that need to detect a peer's failure.

## 3. Core concept

- **Liveness check:** "is the process even running?" — a minimal check, often just "did the process respond at all."
- **Readiness check:** "is this instance ready to serve real traffic right now?" — a deeper check that might verify the instance's own dependencies (its database connection, a warmed-up cache) are actually working, since a running process is not necessarily a *useful* one.
- **Active health checks:** the load balancer or orchestrator periodically polls each instance's health endpoint itself.
- **Heartbeats (passive-style):** each node periodically sends a signal to a central monitor (or to its peers); if a heartbeat is missed for longer than a threshold, the node is presumed failed.
- **Failure detection timing trade-off:** checking too frequently adds overhead and network traffic; checking too infrequently means a failure takes longer to detect, during which traffic keeps flowing to a dead instance. The check interval and failure threshold (e.g. "3 consecutive failed checks") must be tuned to this trade-off.
- **Avoiding false positives:** a single missed check due to a transient network blip should not immediately declare an instance dead — most systems require multiple consecutive failures before acting, to avoid unnecessarily failing over a healthy instance.

## 4. Diagram

```
ACTIVE HEALTH CHECK:                   HEARTBEAT:

  Load Balancer                        Node A --"I'm alive"--> Monitor (every 5s)
    | GET /health (every 5s)           Node A --"I'm alive"--> Monitor
    v                                  Node A --"I'm alive"--> Monitor
  Instance 1: 200 OK (healthy)         Node A: [CRASHES]
  Instance 2: 200 OK (healthy)         Monitor waits... no heartbeat for 15s
  Instance 3: TIMEOUT (unhealthy)          -> Node A presumed FAILED
       |
  removed from rotation
```
*Caption: an active health check polls outward to ask if a node is healthy; a heartbeat has the node itself announce liveness, with silence treated as failure.*

## 5. Runnable example

**Level 1 — Basic.** Poll each instance's health check and route traffic only to healthy ones.

**Level 2 — Heartbeat-based failure detection.** A monitor tracks the last heartbeat time per node and flags any node overdue past a threshold.

**Level 3 — Avoiding false positives.** Require multiple consecutive failures before marking an instance unhealthy, tolerating one transient blip.

```java
// HealthChecksHeartbeats.java
import java.util.*;

public class HealthChecksHeartbeats {

    record Instance(String name, boolean respondsHealthy) {}

    static List<String> activeHealthCheck(List<Instance> instances) {
        List<String> healthy = new ArrayList<>();
        for (Instance i : instances) {
            System.out.println("polling " + i.name() + " -> " + (i.respondsHealthy() ? "200 OK" : "TIMEOUT/error"));
            if (i.respondsHealthy()) healthy.add(i.name());
        }
        return healthy;
    }

    public static void main(String[] args) {
        // Level 1: active health checks - poll each instance, route traffic only to healthy ones.
        List<Instance> instances = List.of(
            new Instance("instance-1", true),
            new Instance("instance-2", true),
            new Instance("instance-3", false) // this one is unhealthy
        );
        List<String> healthyInstances = activeHealthCheck(instances);
        System.out.println("load balancer routes traffic only to: " + healthyInstances);

        // Level 2: heartbeat-based detection - a monitor tracks last-seen time, flags overdue nodes.
        Map<String, Long> lastHeartbeat = new HashMap<>();
        long now = 100_000L; // simulated current time in ms
        lastHeartbeat.put("node-A", now - 5_000);  // heartbeat 5s ago - fine
        lastHeartbeat.put("node-B", now - 20_000); // heartbeat 20s ago - overdue

        long heartbeatTimeoutMs = 15_000;
        for (var entry : lastHeartbeat.entrySet()) {
            long sinceLastHeartbeat = now - entry.getValue();
            boolean presumedFailed = sinceLastHeartbeat > heartbeatTimeoutMs;
            System.out.println(entry.getKey() + ": last heartbeat " + sinceLastHeartbeat + "ms ago -> "
                + (presumedFailed ? "PRESUMED FAILED" : "alive"));
        }

        // Level 3: avoid false positives - require multiple consecutive failures before acting.
        List<Boolean> recentChecks = List.of(true, true, false, true, true); // one transient blip in the middle
        int consecutiveFailureThreshold = 3;
        int currentConsecutiveFailures = 0;
        int maxConsecutiveFailuresSeen = 0;
        for (boolean checkPassed : recentChecks) {
            currentConsecutiveFailures = checkPassed ? 0 : currentConsecutiveFailures + 1;
            maxConsecutiveFailuresSeen = Math.max(maxConsecutiveFailuresSeen, currentConsecutiveFailures);
        }
        boolean shouldMarkUnhealthy = maxConsecutiveFailuresSeen >= consecutiveFailureThreshold;
        System.out.println("check history: " + recentChecks + ", max consecutive failures: " + maxConsecutiveFailuresSeen);
        System.out.println("mark unhealthy? " + shouldMarkUnhealthy + " (single transient blip did not trigger a false failover)");
    }
}
```

**How to run:** save as `HealthChecksHeartbeats.java`, then run `java HealthChecksHeartbeats.java`.

## 6. Walkthrough

1. `activeHealthCheck` iterates every instance, prints the simulated poll result, and collects only the ones reporting healthy; `instance-3`'s `respondsHealthy() == false` excludes it from `healthyInstances`.
2. The final print of `healthyInstances` shows only `instance-1` and `instance-2` — exactly the set a real load balancer would keep routing traffic to, having removed the unhealthy `instance-3` from rotation.
3. Level 2 checks each node's `sinceLastHeartbeat` against `heartbeatTimeoutMs`; `node-A`'s 5-second gap is well under the 15-second threshold, so it is reported alive, while `node-B`'s 20-second gap exceeds it and is reported as presumed failed.
4. Level 3 processes a sequence of 5 recent check results with one isolated `false` in the middle; `currentConsecutiveFailures` resets to `0` on every `true` and only increments on consecutive `false` results, so `maxConsecutiveFailuresSeen` ends up at `1`, not enough to reach `consecutiveFailureThreshold = 3`.
5. `shouldMarkUnhealthy` comes out `false`, confirming that a single transient blip surrounded by successful checks does not trigger a false failover — this is the direct mechanism that protects a genuinely healthy instance from being wrongly pulled out of rotation due to one flaky check.

## 7. Gotchas & takeaways

> Gotcha: a readiness check that only verifies "the process responds to a request" (a liveness check) can report healthy even when the instance's actual dependencies (its database connection, a required downstream service) are broken — traffic gets routed to an instance that will fail every real request. Use a genuine readiness check that verifies the instance's actual ability to do its job, not just that the process is running.

- Health checks let external systems (load balancers, orchestrators) actively verify an instance's status; heartbeats let a node proactively announce its own liveness, with silence treated as failure.
- Liveness checks confirm a process is running; readiness checks confirm it can actually serve real requests correctly — the two are not the same, and both matter.
- Requiring multiple consecutive failures before acting avoids a single transient blip triggering an unnecessary, disruptive failover.
- Related concepts: [Redundancy & replication](0130-redundancy-replication.md) (what health checks decide how to route around), [Active-active vs active-passive failover](0131-active-active-vs-active-passive-failover.md) (the failover process health checks and heartbeats trigger).
