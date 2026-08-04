---
card: system-design
gi: 32
slug: why-load-balance-scale-availability
title: "Why load balance (scale & availability)"
---

## 1. What it is

A **load balancer** is a component that sits in front of multiple servers and distributes incoming requests across them, instead of every client talking to one single server. Clients connect to the load balancer's address, not directly to any individual backend server, and the load balancer decides, per request, which backend server actually handles it.

## 2. Why & when

A single server has a hard ceiling on how much traffic it can handle, and if it goes down, every user is affected. Load balancing solves two separate problems at once: **scale** (spreading requests across many servers means the system can handle far more total traffic than any one server could alone) and **availability** (if one server crashes, the load balancer simply stops sending it traffic and routes around it, so the overall system keeps working). You introduce a load balancer as soon as your capacity estimate shows peak QPS exceeding what a single server can realistically handle, or as soon as an availability requirement (like 99.9%+) demands surviving the loss of any one server.

## 3. Core concept

**The scale argument:** if one server can handle roughly 1,000 QPS, and your peak QPS estimate is 35,000 (from the earlier estimation tutorials in this card), you need enough servers behind a load balancer to cover that peak — roughly 35 servers, plus some headroom for safety margin and uneven distribution.

**The availability argument:** with only one server, that server is a **single point of failure (SPOF)** — if it crashes, is being deployed to, or is overloaded, every user is affected with no fallback. With multiple servers behind a load balancer, the load balancer detects an unhealthy server (via health checks, covered later in this section) and stops routing traffic to it, so the system as a whole keeps serving requests using the remaining healthy servers.

**Where a load balancer typically sits:** at the very edge of your system, in front of your application servers, so clients never connect directly to a specific backend instance. This also means backend servers can be added, removed, restarted, or replaced without clients ever needing to know — the load balancer's address is the only stable, public-facing endpoint.

**The tradeoff this introduces:** a load balancer is itself a new component that must be reliable — if it goes down, nothing behind it is reachable. In practice this is solved by making the load balancer itself redundant (multiple load balancer instances, often behind a DNS-based or hardware failover mechanism), which is a topic this card returns to at scale.

## 4. Diagram

```
              WITHOUT a load balancer          WITH a load balancer
 Clients -------> [ONE SERVER]                Clients --> [Load Balancer]
                    (SPOF: if it dies,                        |
                     everyone is affected;      +-------------+-------------+
                     capped at ~1000 QPS)        v             v             v
                                              [Server1]    [Server2]    [Server3]
                                              (each ~1000 QPS; if one dies,
                                               LB routes around it)
```
*Caption: a load balancer removes the single point of failure and lets total capacity scale by adding more backend servers.*

## 5. Runnable example

### Artifact: a Java simulation showing total capacity and survivability with vs. without a load balancer

```java
import java.util.*;

public class LoadBalanceRationale {

    record Server(String name, int capacityQps, boolean healthy) {}

    static int totalCapacity(List<Server> servers) {
        return servers.stream()
            .filter(Server::healthy)
            .mapToInt(Server::capacityQps)
            .sum();
    }

    public static void main(String[] args) {
        int peakQpsRequired = 2500;

        // Single-server scenario.
        List<Server> singleServer = List.of(new Server("server1", 1000, true));
        System.out.println("Single server capacity: " + totalCapacity(singleServer) + " QPS (need " + peakQpsRequired + ")");
        System.out.println("  Can meet peak demand? " + (totalCapacity(singleServer) >= peakQpsRequired));

        // Multi-server scenario, one of them currently unhealthy.
        List<Server> pool = List.of(
            new Server("server1", 1000, true),
            new Server("server2", 1000, false), // simulating a crashed instance
            new Server("server3", 1000, true)
        );
        System.out.println("Pool capacity (server2 down): " + totalCapacity(pool) + " QPS (need " + peakQpsRequired + ")");
        System.out.println("  Can meet peak demand? " + (totalCapacity(pool) >= peakQpsRequired));
    }
}
```

**How to run:** save as `LoadBalanceRationale.java`, run `java LoadBalanceRationale.java` (JDK 17+).

## 6. Walkthrough

1. `Server` models one backend instance with a rough capacity in QPS and a `healthy` flag, standing in for whether it currently passes health checks.
2. `totalCapacity` sums the capacity of only the *healthy* servers, mirroring how a real load balancer excludes unhealthy servers from routing.
3. The single-server scenario has exactly one server, so its total capacity is capped at 1,000 QPS — well under the 2,500 QPS peak requirement.
4. The pool scenario has three servers, but one (`server2`) is simulated as unhealthy (crashed); the total capacity still comes from the two remaining healthy servers.
5. Output:
```
Single server capacity: 1000 QPS (need 2500)
  Can meet peak demand? false
Pool capacity (server2 down): 2000 QPS (need 2500)
  Can meet peak demand? true
Can meet peak demand? true
```
6. Notice the pool still cannot fully cover 2,500 QPS with one server down (2,000 < 2,500) in this specific numeric example — a realistic and important detail: capacity planning behind a load balancer must include enough spare servers to absorb the loss of at least one, not just enough for exact peak demand with everything healthy.

## 7. Gotchas & takeaways

> **Gotcha:** sizing your server pool for exactly your peak QPS with zero spare capacity. The moment any single server becomes unhealthy (a crash, a deployment, routine maintenance), the remaining servers cannot cover peak demand, and users experience degraded performance right when you can least afford it.

- A load balancer solves two distinct problems: horizontal scale (more total capacity) and availability (no single point of failure).
- Introduce one whenever peak QPS exceeds a single server's capacity, or whenever your availability requirement demands surviving the loss of one server.
- Always provision some spare capacity beyond exact peak demand, so the pool still meets demand even with one or more servers temporarily unhealthy.
