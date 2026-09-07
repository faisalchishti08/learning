---
card: system-design
gi: 122
slug: vertical-vs-horizontal-scaling
title: Vertical vs horizontal scaling
---

## 1. What it is

**Vertical scaling** (scaling up) means making one machine bigger — more CPU cores, more memory, a faster disk — to handle more load. **Horizontal scaling** (scaling out) means adding more machines that each handle a portion of the load, instead of making any single one bigger. It is the difference between hiring one much stronger worker versus hiring more workers.

## 2. Why & when

Vertical scaling is the simplest option: no code changes, just a bigger machine, and it avoids the complexity of distributed coordination. But it hits a hard ceiling — there is a largest machine you can buy — and a single, bigger machine is still a single point of failure. Horizontal scaling has no such ceiling: you can, in principle, keep adding machines indefinitely, and losing one of many machines is far less catastrophic than losing your only one. Use vertical scaling first, for simplicity, while load is moderate and a bigger machine is cheap relative to development time; move to horizontal scaling once you approach the biggest practical machine size, need fault tolerance beyond a single box, or need geographic distribution.

## 3. Core concept

- **Vertical scaling — same architecture, bigger box:** the application code usually needs no changes at all; you simply run it on a machine with more resources.
- **Horizontal scaling — architecture must support it:** distributing load across many machines requires the application to not depend on state living only on one specific machine — see [stateless services & externalized state](0123-stateless-services-externalized-state.md).
- **Load distribution:** horizontal scaling needs a load balancer (or, for data, [sharding](0088-horizontal-vs-vertical-partitioning.md)) to actually route work across the many machines.
- **Cost curve:** vertical scaling's cost per unit of capacity tends to rise steeply at the high end (the biggest machines cost disproportionately more); horizontal scaling's cost per unit of capacity tends to stay closer to linear, using many commodity-sized machines.
- **Fault tolerance:** a vertically scaled single machine is a single point of failure; a horizontally scaled fleet can lose individual machines without the whole system going down, provided the remaining machines can absorb the load.

## 4. Diagram

```
VERTICAL SCALING:                     HORIZONTAL SCALING:

  [ Small server ]                     [Server 1] [Server 2] [Server 3]
        |                                   \         |         /
        v                                    +--- Load Balancer ---+
  [ Bigger server: more CPU, RAM ]                     |
        |                                          incoming requests
        v
  [ Biggest server available ]         Add [Server 4] to handle more load -
        |                              no single machine needs to get bigger.
        v
  CEILING - no bigger machine exists
```
*Caption: vertical scaling grows one machine until it hits a hard ceiling; horizontal scaling adds more machines behind a load balancer with no inherent limit.*

## 5. Runnable example

**Level 1 — Basic.** Model vertical scaling's ceiling: capacity grows until the biggest available machine size.

**Level 2 — Horizontal scaling.** Model capacity growing by adding machines, distributed by a simple load balancer.

**Level 3 — Fault tolerance comparison.** Simulate one machine failing under each strategy and its effect on total capacity.

```java
// ScalingStrategies.java
import java.util.*;

public class ScalingStrategies {

    public static void main(String[] args) {
        // Level 1: vertical scaling - one machine, capacity grows until a hard ceiling.
        int[] verticalUpgrades = {100, 200, 400, 800, 1200}; // capacity after each upgrade
        int verticalCeiling = 1200; // the biggest machine size available
        System.out.println("vertical scaling path: " + Arrays.toString(verticalUpgrades) + " -> hits ceiling at " + verticalCeiling);

        // Level 2: horizontal scaling - add machines, each with fixed capacity, no ceiling.
        int perMachineCapacity = 100;
        List<Integer> machines = new ArrayList<>();
        for (int i = 0; i < 15; i++) machines.add(perMachineCapacity); // 15 machines, well past the vertical ceiling
        int totalHorizontalCapacity = machines.stream().mapToInt(Integer::intValue).sum();
        System.out.println("horizontal scaling: " + machines.size() + " machines x " + perMachineCapacity
            + " each = " + totalHorizontalCapacity + " total capacity (already exceeds the vertical ceiling)");

        // Level 3: fault tolerance - one machine fails under each strategy.
        System.out.println("--- one machine fails ---");
        int verticalCapacityAfterFailure = 0; // the ONE machine failing means total capacity drops to zero
        System.out.println("vertical: single machine fails -> capacity = " + verticalCapacityAfterFailure + " (total outage)");

        int horizontalCapacityAfterFailure = totalHorizontalCapacity - perMachineCapacity; // lose only one of many
        double percentRemaining = 100.0 * horizontalCapacityAfterFailure / totalHorizontalCapacity;
        System.out.printf("horizontal: 1 of %d machines fails -> capacity = %d (%.1f%% remaining, still serving traffic)%n",
            machines.size(), horizontalCapacityAfterFailure, percentRemaining);
    }
}
```

**How to run:** save as `ScalingStrategies.java`, then run `java ScalingStrategies.java`.

## 6. Walkthrough

1. `verticalUpgrades` models a sequence of upgrades to one machine, ending at `verticalCeiling` — the largest machine that exists to buy, illustrating that vertical scaling has a hard, real-world stopping point.
2. `machines`, a list of 15 equally-sized machine capacities, sums to `totalHorizontalCapacity`, a number deliberately larger than the vertical ceiling — demonstrating that horizontal scaling can surpass what any single machine could ever provide, simply by adding more units.
3. The Level 3 vertical case sets `verticalCapacityAfterFailure` to `0`, representing the single machine going down entirely — since there was only ever one machine, its failure is a complete outage.
4. The horizontal case subtracts just one machine's capacity from the 15-machine total, leaving the vast majority of capacity intact.
5. The printed percentage (about 93% remaining) makes the fault-tolerance difference concrete: losing one of many machines barely dents total capacity, while losing the one and only vertically-scaled machine is total failure.

## 7. Gotchas & takeaways

> Gotcha: horizontal scaling's fault tolerance and unlimited growth are not free — they require the application itself to support running many independent instances correctly, meaning no important state can live only in one instance's local memory or disk. Attempting to scale horizontally without first removing that kind of local state (see [stateless services & externalized state](0123-stateless-services-externalized-state.md)) will cause requests to behave inconsistently depending on which instance happens to handle them.

- Vertical scaling is simpler and needs no architecture change, but is capped by the largest available machine and remains a single point of failure.
- Horizontal scaling has no inherent ceiling and tolerates individual machine failures far better, but requires the application to be designed for it.
- A common real-world path is to scale vertically first for simplicity, then move to horizontal scaling once its ceiling or fault-tolerance limits become a real constraint.
- Related concepts: [Stateless services & externalized state](0123-stateless-services-externalized-state.md) (the architectural prerequisite for horizontal scaling), [Horizontal vs vertical partitioning](0088-horizontal-vs-vertical-partitioning.md) (the same "split vs grow" idea applied specifically to data storage).
