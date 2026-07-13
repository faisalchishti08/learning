---
card: microservices
gi: 203
slug: client-side-load-balancing
title: "Client-side load balancing"
---

## 1. What it is

Client-side load balancing is the specific act of a calling service, having already obtained a list of instances (via [client-side discovery](0185-client-side-service-discovery.md) or otherwise), spreading its own outbound traffic across those instances according to a chosen algorithm — the load-balancing *decision* is made inside the caller's own process, on every call, rather than by any separate, shared piece of infrastructure.

## 2. Why & when

Once a caller already has an instance list in hand, someone has to decide, for each individual call, which instance actually receives it — and client-side load balancing means the caller makes that decision itself, in-process, with zero network hop to a separate load-balancing component. This keeps the traffic-distribution logic co-located with the caller, avoiding both the latency of an extra hop and the operational cost of running dedicated load-balancer infrastructure, at the price of every calling service needing its own load-balancing logic (typically via a shared library).

Use client-side load balancing when each caller already performs client-side discovery (making the addition of a balancing step nearly free) and when avoiding an extra network hop through a separate load balancer matters for latency. This is exactly the pattern [Spring Cloud LoadBalancer](0212-spring-cloud-loadbalancer-default-client-side-lb.md) implements for Spring applications, and it is a direct consequence of choosing [client-side service discovery](0185-client-side-service-discovery.md) in the first place.

## 3. Core concept

Given an instance list already available in the caller's process, a load-balancing algorithm picks one instance per call, tracking whatever state that algorithm needs (a rotation counter for round-robin, connection counts for least-connections) locally, inside the calling service itself, with no separate component involved in the decision.

```java
// the instance list is ALREADY in the caller's hands (from discovery)
List<ServiceInstance> instances = discoveryClient.getInstances("order-service");

// the LOAD-BALANCING decision itself happens HERE, in-process, no extra hop
ServiceInstance chosen = clientSideLoadBalancer.choose(instances); // round-robin, random, etc.
httpClient.call(chosen.host(), chosen.port(), "/orders/42");
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The calling service's own process contains both the discovered instance list and the load-balancing algorithm; the decision of which instance to call is made entirely in-process, with the call going directly to the chosen instance, no intermediary hop" >
  <rect x="20" y="30" width="240" height="90" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="50" fill="#8b949e" font-size="8" font-family="sans-serif">Calling service's own process</text>
  <text x="40" y="75" fill="#e6edf3" font-size="7.5" font-family="sans-serif">instance list (from discovery)</text>
  <text x="40" y="100" fill="#e6edf3" font-size="7.5" font-family="sans-serif">load-balancing algorithm</text>

  <rect x="440" y="60" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="515" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Chosen instance</text>

  <line x1="260" y1="77" x2="438" y2="77" stroke="#8b949e" marker-end="url(#arr84)"/>
  <text x="350" y="67" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">direct call, no intermediary</text>

  <defs>
    <marker id="arr84" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Both the instance list and the balancing decision live in the caller's own process, with no separate hop involved.

## 5. Runnable example

Scenario: a shipping-service calling order-service that starts with all calls landing on a single hard-coded instance (no balancing at all), adds in-process round-robin load balancing to spread calls across all known instances, and finally demonstrates the balancer's local state correctly tracking distribution across a realistic volume of calls, confirming even, in-process load spreading with no external component involved.

### Level 1 — Basic

```java
// File: NoBalancingSingleTarget.java -- EVERY call goes to the SAME instance;
// the OTHER known instances sit idle, unused.
import java.util.*;

public class NoBalancingSingleTarget {
    record ServiceInstance(String id) {}
    static List<ServiceInstance> instances = List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b"), new ServiceInstance("order-c"));

    static String callOrderService() {
        ServiceInstance target = instances.get(0); // ALWAYS the first one -- no balancing at all
        return "calling " + target.id();
    }

    public static void main(String[] args) {
        for (int i = 0; i < 6; i++) System.out.println(callOrderService());
        System.out.println("order-b and order-c NEVER received a single call -- all traffic piled onto order-a.");
    }
}
```

**How to run:** `javac NoBalancingSingleTarget.java && java NoBalancingSingleTarget` (JDK 17+).

### Level 2 — Intermediate

```java
// File: InProcessRoundRobin.java -- a load-balancing algorithm running ENTIRELY
// in the CALLER's own process spreads calls across ALL known instances.
import java.util.*;

public class InProcessRoundRobin {
    record ServiceInstance(String id) {}

    static class ClientSideLoadBalancer {
        int index = 0; // STATE lives HERE, in the caller's process -- no external component tracks this
        ServiceInstance choose(List<ServiceInstance> instances) {
            return instances.get(index++ % instances.size());
        }
    }

    public static void main(String[] args) {
        List<ServiceInstance> instances = List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b"), new ServiceInstance("order-c"));
        ClientSideLoadBalancer balancer = new ClientSideLoadBalancer(); // lives WITHIN this calling service

        for (int i = 0; i < 6; i++) {
            ServiceInstance chosen = balancer.choose(instances); // the DECISION happens HERE, in-process
            System.out.println("calling " + chosen.id());
        }
        System.out.println("ALL THREE instances received calls, evenly, with NO external load-balancer component involved.");
    }
}
```

**How to run:** `javac InProcessRoundRobin.java && java InProcessRoundRobin` (JDK 17+).

Expected output:
```
calling order-a
calling order-b
calling order-c
calling order-a
calling order-b
calling order-c
ALL THREE instances received calls, evenly, with NO external load-balancer component involved.
```

### Level 3 — Advanced

```java
// File: DistributionAtRealisticVolume.java -- verifies EVEN distribution
// across a LARGER call volume, confirming the in-process balancer's local
// state correctly tracks and spreads load with no external coordination.
import java.util.*;

public class DistributionAtRealisticVolume {
    record ServiceInstance(String id) {}

    static class ClientSideLoadBalancer {
        int index = 0;
        ServiceInstance choose(List<ServiceInstance> instances) { return instances.get(index++ % instances.size()); }
    }

    public static void main(String[] args) {
        List<ServiceInstance> instances = List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b"), new ServiceInstance("order-c"));
        ClientSideLoadBalancer balancer = new ClientSideLoadBalancer();

        Map<String, Integer> callCounts = new TreeMap<>();
        int totalCalls = 999; // divisible cleanly by 3, for a clean demo
        for (int i = 0; i < totalCalls; i++) {
            ServiceInstance chosen = balancer.choose(instances);
            callCounts.merge(chosen.id(), 1, Integer::sum);
        }

        System.out.println("Distribution across " + totalCalls + " calls: " + callCounts);
        boolean perfectlyEven = callCounts.values().stream().allMatch(count -> count == totalCalls / instances.size());
        System.out.println("Perfectly even distribution: " + perfectlyEven + " -- achieved ENTIRELY with in-process state, zero external load-balancer traffic.");
    }
}
```

**How to run:** `javac DistributionAtRealisticVolume.java && java DistributionAtRealisticVolume` (JDK 17+).

Expected output:
```
Distribution across 999 calls: {order-a=333, order-b=333, order-c=333}
Perfectly even distribution: true -- achieved ENTIRELY with in-process state, zero external load-balancer traffic.
```

## 6. Walkthrough

1. **Level 1** — `callOrderService` always reads `instances.get(0)`, meaning `order-a` is the only instance ever selected across all six calls; `order-b` and `order-c` remain completely unused despite being present in the known `instances` list.
2. **Level 2, the balancer's state living with the caller** — `ClientSideLoadBalancer.index` is a plain field on an object instantiated directly inside what represents the calling service's own code; there is no separate process, network call, or shared component tracking this counter.
3. **Level 2, the decision made entirely in-process** — `balancer.choose(instances)` performs `instances.get(index++ % instances.size())` as a simple, local computation, immediately usable by the calling code to make its next HTTP call — the entire decision, from start to finish, never leaves the calling service's own memory space.
4. **Level 2, the resulting even spread** — six calls rotate cleanly through `order-a`, `order-b`, `order-c`, `order-a`, `order-b`, `order-c`, directly demonstrating that all three instances now receive traffic, unlike Level 1's single-target pileup.
5. **Level 3, scaling up the call volume** — `totalCalls` is set to 999, deliberately chosen to divide evenly by the three-instance list, and the loop calls `balancer.choose` that many times, tallying results in `callCounts`.
6. **Level 3, verifying the exact expected distribution** — `perfectlyEven` checks that every instance's count equals exactly `totalCalls / instances.size()` (333); because `index` increments deterministically and consistently on every single call, the round-robin algorithm guarantees this exact, perfectly even split at this larger scale, not just approximately even.
7. **Level 3, the point about zero external coordination** — the final printed statement emphasizes that this precise, measured, even distribution was achieved purely through a local counter living inside one process — no message was ever sent to any external load-balancing service, no shared state was synchronized across processes, and no network hop beyond the calls to the chosen instances themselves ever occurred, which is the defining structural property of client-side load balancing.

## 7. Gotchas & takeaways

> **Gotcha:** because each calling service instance maintains its own independent load-balancer state (its own `index` counter, or its own connection-count tracking), the *global* distribution of traffic across a fleet of many caller instances depends on each individual caller's own local view being reasonably balanced — with enough concurrent caller instances each doing their own independent round-robin, the aggregate traffic pattern across all callers combined still tends to even out in practice, but no single caller's local state has any awareness of, or coordination with, any other caller's traffic decisions.

- Client-side load balancing performs the instance-selection decision entirely inside the calling service's own process, using an algorithm and state that live locally, with no separate network hop to a dedicated load-balancing component.
- This is a natural extension of client-side service discovery: once the caller already has the instance list in hand, adding a local selection algorithm requires no additional infrastructure.
- The trade-off is that every calling service needs its own load-balancing logic (typically via a shared library), in exchange for avoiding both the latency and operational cost of a separate load-balancer hop.
- Round-robin selection, implemented as a simple local counter, produces precisely even distribution over a large enough number of calls from any single caller.
- Each caller's load-balancing state is entirely independent of every other caller's — there is no cross-caller coordination, only each individual caller balancing its own outbound traffic locally.
