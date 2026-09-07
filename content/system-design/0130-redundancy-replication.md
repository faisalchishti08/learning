---
card: system-design
gi: 130
slug: redundancy-replication
title: Redundancy & replication
---

## 1. What it is

**Redundancy** means having more than one of a critical component, so that if one fails, another can take over its job. **Replication** is the specific form of redundancy applied to data: keeping copies of the same data on multiple nodes, so losing one node does not lose the data. Redundancy is the general principle (extra servers, extra network paths, extra power supplies); replication is redundancy applied specifically to state.

## 2. Why & when

Any single component — a server, a disk, a network link, a data center — can fail. If a system has exactly one of something critical, that thing failing takes the whole system down: a **single point of failure**. Redundancy removes this by ensuring no single failure can take the whole system down, because something else can continue doing that component's job. Apply redundancy to anything whose failure would be unacceptable: application servers (run more than one instance), databases (replicate the data, as in [leader-follower replication](0098-leader-follower-primary-replica-replication.md)), and even network paths and power in a physical data center.

## 3. Core concept

- **Redundant compute:** run multiple instances of a service behind a load balancer; if one instance crashes, the others keep serving traffic.
- **Redundant data (replication):** keep the same data on multiple nodes, so a node failure does not mean data loss — the mechanics of this are covered in depth in [replication & consistency](0098-leader-follower-primary-replica-replication.md).
- **Redundant infrastructure:** redundant power supplies, network switches, and even entire data centers or availability zones, so a failure at any one physical layer does not take the whole system down.
- **N+1 redundancy:** run one more instance/component than the minimum needed to handle expected load, so a single failure still leaves enough capacity to serve normal traffic without degradation.
- **Redundancy is not free:** more instances and more data copies cost more money to run, and replicated data needs a consistency strategy (see [CAP theorem](0107-cap-theorem.md)) — redundancy is a deliberate trade-off, sized to the failure risk you actually need to tolerate.

## 4. Diagram

```
NO REDUNDANCY (single point of failure):     WITH REDUNDANCY:

  [ Single Server ] <- all traffic             [Server A] [Server B] [Server C]
         |                                          \         |         /
    Server crashes -> TOTAL OUTAGE              +--- Load Balancer ---+
                                                          |
                                                Server B crashes -> A and C
                                                keep serving, users unaffected
```
*Caption: with no redundancy, one failure is a total outage; with redundant instances, the same failure is absorbed without visible impact.*

## 5. Runnable example

**Level 1 — Basic.** Model a single server and show that its failure causes a total outage.

**Level 2 — Redundant servers.** The same failure, with multiple instances behind a load balancer, causes no visible outage.

**Level 3 — N+1 sizing.** Calculate how much spare capacity N+1 redundancy provides against expected load.

```java
// RedundancyReplication.java
import java.util.*;

public class RedundancyReplication {

    record Server(String name, boolean healthy) {}

    public static void main(String[] args) {
        // Level 1: no redundancy - one server, and it fails.
        Server soleServer = new Server("server-1", false); // it has crashed
        boolean systemAvailable = soleServer.healthy();
        System.out.println("single server, crashed -> system available? " + systemAvailable + " (TOTAL OUTAGE)");

        // Level 2: redundancy - 3 servers behind a load balancer; one crashes.
        List<Server> servers = new ArrayList<>(List.of(
            new Server("server-A", true),
            new Server("server-B", false), // this one crashed
            new Server("server-C", true)
        ));
        List<Server> healthyServers = servers.stream().filter(Server::healthy).toList();
        boolean redundantSystemAvailable = !healthyServers.isEmpty();
        System.out.println("3 servers, 1 crashed -> healthy servers: " + healthyServers.stream().map(Server::name).toList());
        System.out.println("system available? " + redundantSystemAvailable + " (users routed only to healthy servers, no visible outage)");

        // Level 3: N+1 sizing - how much spare capacity does redundancy actually provide?
        int expectedPeakLoad = 1000; // requests/sec the system must handle
        int perServerCapacity = 400;
        int minimumServersNeeded = (int) Math.ceil((double) expectedPeakLoad / perServerCapacity); // bare minimum, no redundancy
        int nPlusOneServers = minimumServersNeeded + 1; // one extra, for redundancy

        int capacityWithMinimum = minimumServersNeeded * perServerCapacity;
        int capacityWithNPlusOne = nPlusOneServers * perServerCapacity;
        int capacityIfOneFailsWithMinimum = (minimumServersNeeded - 1) * perServerCapacity;
        int capacityIfOneFailsWithNPlusOne = (nPlusOneServers - 1) * perServerCapacity;

        System.out.println("expected peak load: " + expectedPeakLoad + " req/sec");
        System.out.println("minimum servers (" + minimumServersNeeded + "): capacity=" + capacityWithMinimum
            + ", if one fails: " + capacityIfOneFailsWithMinimum + " (" + (capacityIfOneFailsWithMinimum < expectedPeakLoad ? "BELOW peak load!" : "OK") + ")");
        System.out.println("N+1 servers (" + nPlusOneServers + "): capacity=" + capacityWithNPlusOne
            + ", if one fails: " + capacityIfOneFailsWithNPlusOne + " (" + (capacityIfOneFailsWithNPlusOne < expectedPeakLoad ? "BELOW peak load!" : "still meets peak load") + ")");
    }
}
```

**How to run:** save as `RedundancyReplication.java`, then run `java RedundancyReplication.java`.

## 6. Walkthrough

1. Level 1 models the simplest possible failure case: one `Server` marked unhealthy, and the system's availability is directly tied to that one server's health — it is `false`, so the system is completely down.
2. Level 2 introduces 3 servers, one of which (`server-B`) is unhealthy; filtering for `Server::healthy` leaves `server-A` and `server-C`, and the system is still considered available because at least one healthy server remains to serve traffic.
3. This demonstrates the core redundancy payoff directly: the identical single-component failure that caused a total outage in Level 1 causes zero visible impact in Level 2, because the load balancer can route around the unhealthy instance.
4. Level 3 computes the bare-minimum server count needed to meet `expectedPeakLoad` exactly, then compares it against one extra server (N+1). It checks each configuration's remaining capacity *if one server fails*.
5. The output shows the minimum-sized fleet dropping below peak load capacity the moment any one server fails, while the N+1-sized fleet still meets peak load even with one failure — quantifying exactly why N+1 sizing, not just "more than one server", is the standard target for genuinely fault-tolerant capacity planning.

## 7. Gotchas & takeaways

> Gotcha: redundant servers behind a load balancer only help if the load balancer itself, and anything else all instances share (a single database, a single network path), is not itself a single point of failure. Redundancy applied to only part of a system's dependency chain leaves the unaddressed part as the system's true bottleneck for reliability.

- Redundancy provides extra instances of a critical component so a single failure does not take the whole system down; replication is redundancy applied specifically to data.
- N+1 sizing (one more instance than the bare minimum needed) ensures the system still meets its load requirements even after losing one instance to failure.
- Redundancy must be applied consistently across a system's whole dependency chain — a redundant fleet behind a non-redundant load balancer or shared database still has a single point of failure.
- Related concepts: [Single points of failure elimination](0133-single-points-of-failure-elimination.md) (the systematic process this principle drives), [Leader-follower (primary-replica) replication](0098-leader-follower-primary-replica-replication.md) (redundancy applied specifically to data).
