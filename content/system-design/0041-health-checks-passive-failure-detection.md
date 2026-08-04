---
card: system-design
gi: 41
slug: health-checks-passive-failure-detection
title: Health checks & passive failure detection
---

## 1. What it is

A **health check** is a periodic probe a load balancer sends to each backend server to verify it is still working correctly, so unhealthy servers can be automatically removed from routing before they cause failed requests for real clients. **Active health checks** are the load balancer proactively pinging each server on a schedule. **Passive failure detection** instead watches *real* client traffic for signs of trouble — like a server returning errors or timing out — without sending any separate probe requests at all.

## 2. Why & when

Without health checks, a load balancer keeps routing traffic to a crashed or malfunctioning server, sending real client requests to a dead end. This directly undermines the entire point of having multiple servers behind a load balancer for availability, covered earlier in this section. You always include health checks in a load-balanced design; the discussion is really about which kind, and how quickly they should react.

## 3. Core concept

**Active health checks:** the load balancer sends a request — often a lightweight, dedicated endpoint like `GET /health` — to every server on a fixed interval (e.g. every 5 seconds). If a server fails a certain number of consecutive checks (a threshold, to avoid reacting to one transient blip), it is marked unhealthy and removed from routing. It continues to be checked while unhealthy, and is added back once it passes checks again.

**Key active health check settings:**
- **Interval:** how often to check (e.g. every 5s). Shorter intervals detect failure faster, but add more overhead.
- **Timeout:** how long to wait for a response before counting it as a failure.
- **Unhealthy threshold:** how many consecutive failures before marking a server down (avoids reacting to one flaky response).
- **Healthy threshold:** how many consecutive successes before marking a recovered server healthy again.

**Passive failure detection:** instead of (or in addition to) separate probe requests, the load balancer watches real request outcomes — a spike in error responses or timeouts from a specific server — and reacts by temporarily removing that server from rotation. This has the advantage of reacting to real, actual failures affecting real users without any extra probe traffic, but it means at least a few real requests must fail before the problem is noticed — active checks can catch failures proactively, before any real user is affected.

**Why both approaches together are common:** active checks catch a server that has gone completely unresponsive, even during a quiet period with little real traffic. Passive detection catches subtler problems — like a server that responds to a simple health check endpoint but is actually failing on real, more complex requests — that a shallow active check might miss.

## 4. Diagram

```
 ACTIVE HEALTH CHECK (LB proactively probes)      PASSIVE DETECTION (LB watches real traffic)
 LB --GET /health---> Server1   (every 5s)         Client req -> Server2 -> 500 error
 LB <--200 OK---------|                             Client req -> Server2 -> 500 error
                                                     Client req -> Server2 -> timeout
 3 consecutive failures -> Server1 marked unhealthy   3 failures in a row -> Server2 marked
 and removed from routing                             unhealthy, removed from routing
```
*Caption: active checks probe proactively on a schedule; passive detection reacts to failures observed in real request traffic.*

## 5. Runnable example

### Artifact: a Java simulation of both active health checking and passive failure detection, each removing an unhealthy server from routing

```java
import java.util.*;

public class HealthCheckSim {

    static final int UNHEALTHY_THRESHOLD = 3;
    static final Map<String, Integer> consecutiveFailures = new HashMap<>();
    static final Set<String> unhealthyServers = new HashSet<>();

    static void recordCheckResult(String server, boolean success) {
        if (success) {
            consecutiveFailures.put(server, 0);
            if (unhealthyServers.remove(server)) {
                System.out.println("  " + server + " recovered, added back to routing");
            }
        } else {
            int failures = consecutiveFailures.merge(server, 1, Integer::sum);
            if (failures >= UNHEALTHY_THRESHOLD && unhealthyServers.add(server)) {
                System.out.println("  " + server + " marked UNHEALTHY after " + failures + " consecutive failures, removed from routing");
            }
        }
    }

    public static void main(String[] args) {
        System.out.println("Active health checks on serverA (every interval):");
        recordCheckResult("serverA", true);
        recordCheckResult("serverA", false);
        recordCheckResult("serverA", false);
        recordCheckResult("serverA", false); // 3rd consecutive failure

        System.out.println("Passive detection watching real traffic to serverB:");
        recordCheckResult("serverB", false); // real request failed
        recordCheckResult("serverB", false); // another real request failed
        recordCheckResult("serverB", false); // 3rd real failure

        System.out.println("serverA recovers on next active check:");
        recordCheckResult("serverA", true);

        System.out.println("Currently unhealthy (excluded from routing): " + unhealthyServers);
    }
}
```

**How to run:** save as `HealthCheckSim.java`, run `java HealthCheckSim.java` (JDK 17+).

## 6. Walkthrough

1. `consecutiveFailures` tracks how many checks (active or passive) in a row have failed for each server, resetting to zero on any success — this is what makes the threshold require *consecutive* failures, not just any failures ever.
2. `recordCheckResult` is called for both active probe results and passive real-traffic observations — the underlying logic is identical either way; only the *source* of the success/failure signal differs.
3. `main` first simulates 3 consecutive active health-check failures for `serverA`, crossing the threshold. It then simulates 3 consecutive *real request* failures for `serverB`, representing passive detection reaching the same threshold through actual client traffic instead of a dedicated probe.
4. It then simulates `serverA` passing a check again, showing recovery.
5. Output:
```
Active health checks on serverA (every interval):
  serverA marked UNHEALTHY after 3 consecutive failures, removed from routing
Passive detection watching real traffic to serverB:
  serverB marked UNHEALTHY after 3 consecutive failures, removed from routing
serverA recovers on next active check:
  serverA recovered, added back to routing
Currently unhealthy (excluded from routing): [serverB]
```
6. Note both `serverA` and `serverB` reach "unhealthy" through the exact same threshold logic — the only difference was whether the failing signal came from a dedicated health-check probe or from real client requests failing.

## 7. Gotchas & takeaways

> **Gotcha:** setting the unhealthy threshold to 1 (marking a server down after a single failed check). A single transient network blip or garbage-collection pause can then remove a perfectly healthy server from rotation, needlessly reducing capacity — a threshold of several consecutive failures avoids overreacting to one-off noise.

- Active health checks proactively probe every server on a schedule; passive detection reacts to failures seen in real traffic.
- Require multiple consecutive failures before marking a server unhealthy, to avoid overreacting to transient blips.
- Use both together in production: active checks catch total unresponsiveness even during quiet periods; passive detection catches subtler problems a shallow probe might miss.
