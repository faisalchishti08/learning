---
card: system-design
gi: 133
slug: single-points-of-failure-elimination
title: Single points of failure elimination
---

## 1. What it is

A **single point of failure (SPOF)** is any single component whose failure alone can bring down the whole system, or a critical part of it. **SPOF elimination** is the systematic process of finding every such component in a system's design and adding redundancy specifically to remove it as a single point of failure. It is not one technique, but a review discipline: trace every path a request takes, and ask of each component on that path, "if only this one thing failed, would the system still work?"

## 2. Why & when

A system can have redundant application servers and still have a SPOF hiding in the load balancer in front of them, the single database behind them, or the one DNS record pointing at all of it — redundancy applied inconsistently gives a false sense of resilience. Do a SPOF elimination pass on any system where availability actually matters, tracing the *entire* request path end to end, not just the part that was easiest to make redundant. This is a deliberate, systematic exercise, not something that happens automatically just because some components are redundant.

## 3. Core concept

- **Trace the full request path:** DNS, load balancer, application servers, cache, database, any external service called along the way — every single one of these is a candidate SPOF until proven otherwise.
- **Common overlooked SPOFs:** a single load balancer in front of many redundant servers; a single database with no replica; a single region or data center hosting an otherwise redundant fleet; a single third-party API with no fallback; a single person who is the only one who knows how to operate a critical system.
- **Redundancy must match the failure domain:** running multiple servers in the same rack, on the same power circuit, is not real redundancy against a power failure — the redundant copies must be independent across whatever failure domain you are protecting against (a server, a rack, a data center, a region).
- **The review is iterative:** removing one SPOF (adding a second database replica) can reveal the next one (both replicas are in the same data center) — this process is not a single pass, but a repeated tightening.
- **Not every SPOF is worth eliminating:** eliminating a SPOF has a real cost (more infrastructure, more complexity); the decision should weigh the cost of elimination against the actual business impact and likelihood of that specific component failing.

## 4. Diagram

```
Request path with SPOFs highlighted:

  DNS (single record)          <- SPOF? usually mitigated by DNS's own redundancy
       |
  Load Balancer (ONE instance) <- SPOF! if it dies, no traffic reaches ANY server
       |
  +----+----+----+
  v    v    v    v
Server Server Server (redundant - good)
  |    |    |
  +----+----+
       |
  Database (ONE instance, no replica) <- SPOF! if it dies, every server fails

FIX: add a second, redundant load balancer, AND a database replica.
```
*Caption: redundancy at the server layer alone is not enough; every single-instance component on the path is still a SPOF until it, too, has redundancy.*

## 5. Runnable example

**Level 1 — Basic.** Model a request path as a list of components, and flag every one that has no redundancy.

**Level 2 — Fix the flagged SPOFs.** Add redundancy to the flagged components and re-run the check.

**Level 3 — Failure-domain check.** Confirm redundant copies are actually in different failure domains, not just duplicated in the same one.

```java
// SpofElimination.java
import java.util.*;

public class SpofElimination {

    record Component(String name, int instanceCount, List<String> failureDomains) {}

    static List<String> findSpofs(List<Component> path) {
        List<String> spofs = new ArrayList<>();
        for (Component c : path) {
            if (c.instanceCount() <= 1) spofs.add(c.name());
        }
        return spofs;
    }

    public static void main(String[] args) {
        // Level 1: trace the request path, flag single-instance components.
        List<Component> requestPath = new ArrayList<>(List.of(
            new Component("DNS", 2, List.of("provider-A", "provider-B")),
            new Component("LoadBalancer", 1, List.of("zone-1")),      // SPOF
            new Component("AppServers", 3, List.of("zone-1", "zone-1", "zone-1")),
            new Component("Database", 1, List.of("zone-1"))           // SPOF
        ));
        List<String> spofs = findSpofs(requestPath);
        System.out.println("SPOFs found in request path: " + spofs);

        // Level 2: fix the flagged SPOFs by adding redundant instances.
        requestPath.set(1, new Component("LoadBalancer", 2, List.of("zone-1", "zone-1")));
        requestPath.set(3, new Component("Database", 2, List.of("zone-1", "zone-1"))); // replica added, same zone for now
        List<String> spofsAfterFix = findSpofs(requestPath);
        System.out.println("SPOFs after adding redundant instances: " + spofsAfterFix + " (none - but check failure domains next)");

        // Level 3: failure-domain check - are the redundant instances actually independent?
        for (Component c : requestPath) {
            Set<String> distinctDomains = new HashSet<>(c.failureDomains());
            boolean sameSingleDomain = c.instanceCount() > 1 && distinctDomains.size() == 1;
            if (sameSingleDomain) {
                System.out.println(c.name() + ": " + c.instanceCount() + " instances, but ALL in domain '"
                    + distinctDomains.iterator().next() + "' -> NOT real redundancy against a zone failure");
            } else {
                System.out.println(c.name() + ": instances spread across domains " + distinctDomains + " -> genuinely redundant");
            }
        }
    }
}
```

**How to run:** save as `SpofElimination.java`, then run `java SpofElimination.java`.

## 6. Walkthrough

1. `findSpofs` flags any `Component` with `instanceCount() <= 1`; running it against the initial `requestPath` correctly identifies `LoadBalancer` and `Database` as SPOFs, since `DNS` and `AppServers` already have more than one instance.
2. Level 2 replaces the `LoadBalancer` and `Database` entries with versions having `instanceCount = 2`, modeling the fix of adding redundant instances to each.
3. Running `findSpofs` again on the updated `requestPath` returns an empty list — by the simple "more than one instance" measure, no more SPOFs remain.
4. Level 3 goes further, checking each component's `failureDomains` list for distinct values; `AppServers` and the newly-fixed `LoadBalancer` and `Database` are all found to have every instance listed under the single domain `"zone-1"`.
5. The printed output flags all three as "NOT real redundancy against a zone failure", since all their instances share the same failure domain — demonstrating that simply having multiple instances is not sufficient; the SPOF elimination process must also verify those instances fail independently of each other, which the `instanceCount` check alone cannot catch.

## 7. Gotchas & takeaways

> Gotcha: it is common to declare a review "done" once every component shows more than one instance, without checking whether those instances share an underlying failure domain (the same rack, the same availability zone, the same cloud region) — this gives a false sense of resilience against exactly the kind of larger-scale failure (a zone outage) that redundancy was meant to protect against.

- A single point of failure is any one component whose failure alone can take down the system; elimination requires tracing the entire request path, not just the parts already made redundant.
- Common overlooked SPOFs include the load balancer itself, the database, DNS, and even a single person as the only operator of a critical system.
- Redundant instances must sit in genuinely independent failure domains (different racks, zones, or regions) to provide real protection, not just duplication within the same domain.
- Related concepts: [Redundancy & replication](0130-redundancy-replication.md) (the fix this process identifies the need for), [Active-active vs active-passive failover](0131-active-active-vs-active-passive-failover.md) (a strategy for the redundancy this process reveals is needed).
