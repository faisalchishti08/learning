---
card: microservices
gi: 14
slug: independent-scalability
title: Independent scalability
---

## 1. What it is

**Independent scalability** is the ability to add or remove running instances of one specific service in response to its own load, without needing to scale every other service by the same amount. In a monolith, scaling means running more copies of the *entire* application, even if only one feature inside it (say, image processing) is actually under heavy load — every other feature scales along for the ride, wasting resources. In microservices, each service can be scaled to match its own, independent traffic pattern.

## 2. Why & when

Different capabilities in a real system rarely have matching load profiles. A checkout flow might see steady, moderate traffic, while a search or recommendation feature spikes wildly during a sale. In a monolith, handling that search spike means scaling the whole application — checkout, inventory, everything — to match the busiest feature's needs, which is expensive and unnecessary for the parts that aren't actually under pressure.

Reach for independent scalability once your services genuinely have different, measurable load profiles — it's the concrete payoff of having already split a system along business capabilities. If every service in your system tends to scale in lockstep anyway (because load always arrives proportionally across all of them), independent scalability offers little real benefit over just scaling a monolith as one unit.

## 3. Core concept

The mechanism is straightforward once services are separate processes: a load balancer (or, in this simplified example, a simple round-robin dispatcher) routes requests across however many instances of a given service are currently running. Scaling a service up means starting another instance and adding it to that pool; scaling down means removing one. Crucially, this operation touches only the pool for *that* service — every other service's instance count is untouched.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OrdersService runs one instance while InventoryService, under heavier load, runs three instances behind a load balancer">
  <rect x="20" y="70" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="97" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrdersService x1</text>

  <text x="420" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">InventoryService (scaled to x3)</text>
  <rect x="330" y="35" width="90" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="375" y="57" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance 1</text>
  <rect x="430" y="35" width="90" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="57" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance 2</text>
  <rect x="530" y="35" width="90" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="575" y="57" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance 3</text>
  <rect x="420" y="90" width="120" height="30" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="480" y="110" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">load balancer</text>
</svg>

Only the service under heavy load gets more instances; the rest scale independently, matched to their own traffic.

## 5. Runnable example

Scenario: `OrdersService` and `InventoryService` under different load levels, first both fixed at one instance, then `InventoryService` scaled up independently, then a round-robin dispatcher distributing load across its added instances.

### Level 1 — Basic

```java
// File: OneInstanceEach.java -- both services fixed at ONE instance, no scaling at all
public class OneInstanceEach {
    static int ordersHandled = 0;
    static int inventoryHandled = 0;

    static void handleOrdersRequest() { ordersHandled++; }
    static void handleInventoryRequest() { inventoryHandled++; }

    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) handleOrdersRequest();
        for (int i = 0; i < 20; i++) handleInventoryRequest(); // 4x the load, but still only ONE instance

        System.out.println("orders handled by 1 instance: " + ordersHandled);
        System.out.println("inventory handled by 1 instance: " + inventoryHandled + " (overloaded)");
    }
}
```

**How to run:** `javac OneInstanceEach.java && java OneInstanceEach` (JDK 17+).

Expected output:
```
orders handled by 1 instance: 5
inventory handled by 1 instance: 20 (overloaded)
```

`InventoryService`'s single instance absorbs four times the requests `OrdersService` does — with no way to add capacity specifically for it, that one instance becomes the bottleneck for the whole system, even though `OrdersService` is fine.

### Level 2 — Intermediate

```java
// File: ScaleInventoryOnly.java -- add MORE instances of InventoryService,
// leaving OrdersService's instance count completely untouched.
import java.util.*;

public class ScaleInventoryOnly {
    static class InstancePool {
        String serviceName;
        List<Integer> instanceLoad = new ArrayList<>(); // one entry per instance, tracks requests handled
        InstancePool(String name, int startingInstances) {
            this.serviceName = name;
            for (int i = 0; i < startingInstances; i++) instanceLoad.add(0);
        }
        void scaleTo(int instanceCount) {
            while (instanceLoad.size() < instanceCount) instanceLoad.add(0);
            while (instanceLoad.size() > instanceCount) instanceLoad.remove(instanceLoad.size() - 1);
        }
    }

    public static void main(String[] args) {
        InstancePool orders = new InstancePool("OrdersService", 1);
        InstancePool inventory = new InstancePool("InventoryService", 1);

        System.out.println("before scaling -- orders instances: " + orders.instanceLoad.size() + ", inventory instances: " + inventory.instanceLoad.size());

        inventory.scaleTo(4); // scale ONLY inventory, in response to ITS OWN load

        System.out.println("after scaling  -- orders instances: " + orders.instanceLoad.size() + ", inventory instances: " + inventory.instanceLoad.size());
    }
}
```

**How to run:** `javac ScaleInventoryOnly.java && java ScaleInventoryOnly` (JDK 17+).

Expected output:
```
before scaling -- orders instances: 1, inventory instances: 1
after scaling  -- orders instances: 1, inventory instances: 4
```

`orders.instanceLoad.size()` never changes across the whole run — `orders.scaleTo(...)` is never even called. Only `InventoryService`'s pool grows, matched to its own load, with zero effect on `OrdersService`'s resource footprint.

### Level 3 — Advanced

```java
// File: RoundRobinAcrossScaledInstances.java -- distribute real traffic
// across InventoryService's 4 scaled instances via round-robin dispatch.
import java.util.*;

public class RoundRobinAcrossScaledInstances {
    static class InstancePool {
        String serviceName;
        List<Integer> instanceLoad = new ArrayList<>();
        int nextInstance = 0;

        InstancePool(String name, int startingInstances) {
            this.serviceName = name;
            for (int i = 0; i < startingInstances; i++) instanceLoad.add(0);
        }

        void scaleTo(int instanceCount) {
            while (instanceLoad.size() < instanceCount) instanceLoad.add(0);
            while (instanceLoad.size() > instanceCount) instanceLoad.remove(instanceLoad.size() - 1);
        }

        void dispatch() { // round-robin: send this request to the NEXT instance in rotation
            instanceLoad.set(nextInstance, instanceLoad.get(nextInstance) + 1);
            nextInstance = (nextInstance + 1) % instanceLoad.size();
        }
    }

    public static void main(String[] args) {
        InstancePool orders = new InstancePool("OrdersService", 1);
        InstancePool inventory = new InstancePool("InventoryService", 1);
        inventory.scaleTo(4);

        for (int i = 0; i < 5; i++) orders.dispatch();       // 5 requests, 1 instance
        for (int i = 0; i < 20; i++) inventory.dispatch();   // 20 requests, spread across 4 instances

        System.out.println("orders per-instance load: " + orders.instanceLoad);
        System.out.println("inventory per-instance load: " + inventory.instanceLoad + " (evenly spread, 5 each)");
    }
}
```

**How to run:** `javac RoundRobinAcrossScaledInstances.java && java RoundRobinAcrossScaledInstances` (JDK 17+).

Expected output:
```
orders per-instance load: [5]
inventory per-instance load: [5, 5, 5, 5]
```

The production-flavored payoff: `InventoryService`'s 20 requests, the same total load as before scaling, are now spread across 4 instances at 5 requests each — matching `OrdersService`'s single instance's per-instance load of 5. Scaling `InventoryService` independently turned an overloaded single instance into four instances each carrying a manageable, matched share of the work.

## 6. Walkthrough

1. `inventory.scaleTo(4)` grows `inventory.instanceLoad` from `[0]` to `[0, 0, 0, 0]` — four instance slots, each starting at zero load. `orders.instanceLoad` remains `[0]`, since `orders.scaleTo` is never called.
2. The first loop calls `orders.dispatch()` five times. Each call increments `instanceLoad.get(0)` (the only instance) and advances `nextInstance` modulo `1`, which always stays `0` — all five requests land on the single `OrdersService` instance.
3. The second loop calls `inventory.dispatch()` twenty times. Each call increments whichever instance `nextInstance` currently points to, then advances `nextInstance` by one, wrapping around modulo `4`.
4. Because 20 is an exact multiple of 4, the round-robin distributes exactly 5 requests to each of the four instances: request 1 to instance 0, request 2 to instance 1, request 3 to instance 2, request 4 to instance 3, request 5 back to instance 0, and so on.
5. The final printout shows `orders.instanceLoad` as `[5]` (one instance, all the load) and `inventory.instanceLoad` as `[5, 5, 5, 5]` (four instances, evenly sharing the load) — the same total inventory traffic as Level 1's overloaded single instance, now spread thin enough that no single instance is a bottleneck.

```
dispatch() calls:  1    2    3    4    5    6    7    8  ...  20
instance index:    0    1    2    3    0    1    2    3  ...   3   (wraps every 4)
final load:      [5,   5,   5,   5]
```

## 7. Gotchas & takeaways

> **Gotcha:** independent scalability only helps if the service being scaled is actually **stateless**, or its state is stored somewhere shared and consistent (like a database) rather than in each instance's own memory. Scaling a service that keeps important state only in local memory can produce inconsistent results depending on which instance a given request happens to land on.

- Independent scalability lets one service's instance count grow or shrink to match its own traffic, without forcing every other service to scale along with it.
- The mechanism is a pool of instances per service plus a dispatch strategy (round-robin here; real systems often use more adaptive load balancing) routing requests across whichever instances currently exist for that service.
- This characteristic pays off specifically when services have genuinely different load profiles — matching load evenly across all services makes independent scaling far less valuable than scaling everything together.
- Scaling stateful services safely requires the state itself to live somewhere shared (a database, a cache) rather than purely in each instance's local memory, or different instances can give inconsistent answers.
