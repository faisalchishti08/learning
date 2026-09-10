---
card: system-design
gi: 221
slug: multi-az-multi-region-deployment
title: Multi-AZ & multi-region deployment
---

## 1. What it is

An **availability zone (AZ)** is one or more physically separate data centers within a cloud region, each with independent power, cooling, and networking, but connected by fast, low-latency links. **Multi-AZ deployment** runs your system's instances across two or more AZs within one region, so the failure of one AZ (a power outage, a network fault) does not take the whole system down. **Multi-region deployment** goes further, running full deployments in geographically distant regions, to survive an outage affecting an entire region, and to serve users with lower latency from a nearby region.

## 2. Why & when

A system running entirely in one data center (or one AZ) has a single point of physical failure — a power outage, a cooling failure, or a fiber cut takes the whole system down, regardless of how well the software itself is architected. Multi-AZ deployment is the first, and usually the highest-value, step to remove this risk: it costs relatively little (AZs within a region have fast, cheap connectivity between them) and protects against the most common class of infrastructure failure.

Multi-region deployment protects against a rarer but more severe failure — an entire region going down, or a region-wide network partition — and also reduces latency for geographically distributed users, since requests can be served from the nearest region instead of always crossing an ocean. The cost and complexity are much higher: data must be replicated across regions (which takes real time and adds real inconsistency risk), and cross-region network calls are slow enough to design around explicitly. Use multi-AZ as close to a default for any production system as multi-region is a deliberate, higher-cost decision for systems with specific global-availability or global-latency requirements.

## 3. Core concept

- **AZs are close, regions are far.** AZs within one region are typically connected by sub-millisecond links, close enough that synchronous replication (write to both before confirming) is practical. Regions are often tens to hundreds of milliseconds apart — far enough that synchronous cross-region writes would make every write painfully slow.
- **Load balancing across AZs.** A load balancer distributes traffic across instances in every AZ; if one AZ's instances become unreachable, the load balancer simply stops sending traffic there and the remaining AZs absorb the load — this requires running enough spare capacity in the healthy AZs to handle it.
- **Data replication strategy differs by distance.** Within a region (multi-AZ), synchronous replication (the write is not confirmed until it exists in a second AZ) is common and keeps data safe with no loss on a single AZ failure. Across regions (multi-region), replication is usually asynchronous — the primary region confirms the write immediately, and the write propagates to other regions shortly after, which means a region failure right after a write can lose that specific write.
- **Active-passive vs. active-active.** Active-passive keeps one region serving all traffic while another stands by, ready to take over (see [disaster recovery](0222-disaster-recovery-rpo-rto.md)). Active-active serves real traffic from multiple regions simultaneously, giving lower latency to users everywhere but requiring a strategy for what happens when the same data is written in two regions at nearly the same time.
- **Failure blast radius shrinks with each layer.** A single server failing affects a fraction of one AZ's capacity. An AZ failing affects a fraction of one region's capacity (assuming multi-AZ). A region failing, without multi-region, affects everything — each additional layer of redundancy shrinks what a single failure can take down.

## 4. Diagram

```
                              Region: us-east
        +------------------------------------------------------+
        |   AZ-1              AZ-2              AZ-3              |
        |  +-------+         +-------+         +-------+           |
        |  | app x3 |         | app x3 |         | app x3 |          |
        |  | db      |<------>| db      |<------>| db      |         |
        |  | replica |  sync  | replica |  sync   | replica |         |
        |  +-------+         +-------+         +-------+           |
        +------------------------------------------------------+
                                   ^
                                   | async replication (higher latency, some lag)
                                   v
                              Region: eu-west
        +------------------------------------------------------+
        |   AZ-1              AZ-2                                |
        |  +-------+         +-------+                            |
        |  | app x3 |         | app x3 |     (standby, or serving   |
        |  | db      |<------>| db      |      local EU traffic in   |
        |  | replica |  sync  | replica |      active-active)         |
        |  +-------+         +-------+                            |
        +------------------------------------------------------+

   AZ-1 failing in us-east: absorbed by AZ-2 and AZ-3, sync replication, no data loss.
   Entire us-east region failing: only survived if eu-west can take over (multi-region).
```
*Caption: replication within a region is synchronous and tight; replication between regions is asynchronous and looser — the physical distance dictates which tradeoff is even possible.*

## 5. Runnable example

**Level 1 — Basic.** A load balancer distributing traffic across instances in multiple AZs, absorbing one AZ's failure.

**Level 2 — Intermediate.** Synchronous replication within a region (multi-AZ) vs. asynchronous replication across regions (multi-region), showing the difference in write latency and data-loss risk.

**Level 3 — Advanced.** A full region failure: traffic fails over to a second region, and the asynchronous replication lag determines how much data (if any) is lost.

```java
// MultiAzRegionDemo.java
import java.util.*;

public class MultiAzRegionDemo {

    // ---------- Level 1: load balancing across AZs, one AZ fails ----------
    static class LoadBalancer {
        Map<String, Boolean> azHealthy = new LinkedHashMap<>();

        String route(String request) {
            List<String> healthyAzs = azHealthy.entrySet().stream()
                .filter(Map.Entry::getValue).map(Map.Entry::getKey).toList();
            if (healthyAzs.isEmpty()) return "ALL AZs DOWN - request failed";
            String chosen = healthyAzs.get(request.hashCode() % healthyAzs.size() >= 0 ?
                request.hashCode() % healthyAzs.size() : 0);
            return chosen + " handled: " + request;
        }
    }

    // ---------- Level 2: sync (in-region) vs async (cross-region) replication ----------
    static class SyncReplicatedStore {
        Map<String, String> azA = new HashMap<>(), azB = new HashMap<>();
        String write(String key, String value) {
            azA.put(key, value);
            azB.put(key, value); // confirmed to caller only after BOTH AZs have it
            return "write confirmed - present in AZ-A AND AZ-B (zero risk of loss if ONE AZ fails)";
        }
    }

    static class AsyncReplicatedStore {
        Map<String, String> primaryRegion = new HashMap<>();
        Map<String, String> secondaryRegion = new HashMap<>();
        List<String> replicationQueue = new ArrayList<>(); // simulates in-flight, not-yet-replicated writes

        String write(String key, String value) {
            primaryRegion.put(key, value); // confirmed IMMEDIATELY, before secondary has it
            replicationQueue.add(key + "=" + value);
            return "write confirmed - present in PRIMARY region only so far; " +
                replicationQueue.size() + " write(s) still propagating to secondary";
        }

        void drainReplicationLag() {
            for (String entry : replicationQueue) {
                String[] parts = entry.split("=", 2);
                secondaryRegion.put(parts[0], parts[1]);
            }
            System.out.println("    (replication catches up - secondary now has " +
                replicationQueue.size() + " pending write(s))");
            replicationQueue.clear();
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - load balancer absorbs one AZ failing:");
        LoadBalancer lb = new LoadBalancer();
        lb.azHealthy.put("AZ-1", true);
        lb.azHealthy.put("AZ-2", true);
        lb.azHealthy.put("AZ-3", true);
        System.out.println("  " + lb.route("req-A"));
        System.out.println("  AZ-2 fails (power outage)...");
        lb.azHealthy.put("AZ-2", false);
        System.out.println("  " + lb.route("req-B") + "  <- rerouted, AZ-2 no longer considered");

        System.out.println("\nLevel 2 - synchronous (multi-AZ) vs asynchronous (multi-region) replication:");
        SyncReplicatedStore syncStore = new SyncReplicatedStore();
        System.out.println("  " + syncStore.write("order-5", "SHIPPED"));

        AsyncReplicatedStore asyncStore = new AsyncReplicatedStore();
        System.out.println("  " + asyncStore.write("order-5", "SHIPPED"));
        System.out.println("  secondary region right now: " + asyncStore.secondaryRegion + "  <- does NOT have it yet");

        System.out.println("\nLevel 3 - primary region fails BEFORE replication catches up:");
        AsyncReplicatedStore store = new AsyncReplicatedStore();
        store.write("order-8", "PLACED");
        store.write("order-9", "PLACED");
        System.out.println("  2 writes confirmed to clients, still only in primary region");
        System.out.println("  primary region fails NOW (before replication caught up)...");
        System.out.println("  failing over to secondary region. secondary has: " + store.secondaryRegion +
            "  <- both writes are LOST from the client's point of view");
        System.out.println("\n  (if replication had caught up first, via drainReplicationLag(), nothing would be lost)");
        store.drainReplicationLag();
        System.out.println("  secondary region after replication catches up: " + store.secondaryRegion);
    }
}
```

**How to run:** `java MultiAzRegionDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `lb.route("req-A")` is called while all three AZs are healthy, and it picks one based on a simple hash of the request. `lb.azHealthy.put("AZ-2", false)` then simulates AZ-2 failing. `lb.route("req-B")` recomputes `healthyAzs` from scratch, filtering out AZ-2 entirely — the load balancer never sends traffic to a known-unhealthy AZ, so the failure is absorbed by the remaining two.
2. **Level 2:** `syncStore.write("order-5", "SHIPPED")` writes to `azA` and `azB` **before** returning — the method only returns after both have the value, which is why the confirmation message can honestly say "zero risk of loss if one AZ fails": both copies already exist by the time the caller knows the write succeeded.
3. `asyncStore.write("order-5", "SHIPPED")` writes only to `primaryRegion` and returns immediately, adding the write to `replicationQueue` to be propagated later. Printing `asyncStore.secondaryRegion` right after confirms it is still empty — the write is confirmed to the client, but the secondary region genuinely does not have it yet.
4. **Level 3:** two writes are confirmed via `store.write(...)`, both landing only in `primaryRegion`, both queued for replication. The scenario then simulates primary region failure *before* `drainReplicationLag()` ever runs — `store.secondaryRegion` at that point is still empty, so failing over to it means both previously-confirmed writes are genuinely gone from the client's perspective, having never made it to the region that is now serving traffic.
5. The final `store.drainReplicationLag()` call shows the alternative outcome: if replication had been given time to catch up before the failure, `secondaryRegion` would contain both writes, and failover would have lost nothing. This exact race — does replication catch up before failure happens — is what [disaster recovery](0222-disaster-recovery-rpo-rto.md)'s **RPO** (recovery point objective) measures and budgets for.

## 7. Gotchas & takeaways

> **Gotcha:** asynchronous cross-region replication means a region failure can lose the most recent writes — even writes the client was told succeeded. If a business process cannot tolerate any data loss (financial transactions are the classic example), that process may need synchronous cross-region writes for just that data, accepting the higher latency cost, rather than relying on async replication's default behavior.

- Multi-AZ is close to a default requirement for any production system — the cost is low relative to the risk it removes (a single data center failure taking down the whole system).
- Multi-region is a deliberate tradeoff between cost/complexity and protection against a rarer, more severe failure (and, separately, a tool for reducing latency to geographically distant users) — evaluate it against your system's actual availability and latency requirements, not as an automatic next step after multi-AZ.
- Understand which replication mode (synchronous vs. asynchronous) applies at each layer of your deployment, and what data loss is possible at the boundary where synchronous stops and asynchronous begins.
- This deployment topology is the physical foundation [disaster recovery](0222-disaster-recovery-rpo-rto.md) plans against — RPO and RTO targets are only achievable if the underlying multi-AZ/multi-region architecture actually supports them.
