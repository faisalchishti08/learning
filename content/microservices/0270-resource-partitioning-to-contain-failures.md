---
card: microservices
gi: 270
slug: resource-partitioning-to-contain-failures
title: "Resource partitioning to contain failures"
---

## 1. What it is

Resource partitioning to contain failures is the broader principle underlying the [bulkhead pattern](0267-bulkhead-pattern.md): deliberately dividing any shared resource — not just thread pools, but connection pools, memory budgets, rate limit allocations, queue capacity — into separate compartments assigned to specific consumers, so a failure or overload affecting one consumer's compartment cannot spread to consume resources allocated to a different, healthy consumer.

## 2. Why & when

Thread-pool and semaphore bulkheads apply this partitioning specifically to *concurrency* — how many calls can be in flight at once — but the same underlying principle applies to any resource multiple consumers might otherwise compete for unpredictably: a shared connection pool where one misbehaving tenant's queries can exhaust every available connection, a shared message queue where one slow consumer's backlog can delay processing for every other consumer sharing that queue, a shared rate-limit budget where one noisy client can consume the entire allowance meant to serve many clients fairly. Recognizing partitioning as a general principle — not just "the thing bulkheads do for threads" — helps identify other places in a system where an unpartitioned shared resource creates the same kind of hidden coupling risk.

Apply partitioning to any shared resource where multiple distinct, independently-behaving consumers (different tenants, different dependencies, different traffic categories) draw from a common pool that, if exhausted by one consumer, would degrade service for the others — a pattern that recurs across many different resource types beyond just threads.

## 3. Core concept

Partitioning assigns each consumer (or category of consumers) a fixed, bounded share of a resource, so that consumer's maximum possible consumption is capped independently of how the resource as a whole is being used — the resource's total capacity is divided upfront into guaranteed, isolated allocations, rather than being available as one undifferentiated shared pool that any consumer could exhaust.

```java
// UNPARTITIONED -- ONE shared connection pool, ANY tenant could exhaust it ENTIRELY
DataSource sharedPool = createConnectionPool(maxConnections = 50); // ANY tenant's runaway query load starves EVERYONE

// PARTITIONED -- EACH tenant gets its OWN guaranteed, bounded allocation
Map<String, DataSource> perTenantPools = Map.of(
    "tenant-a", createConnectionPool(maxConnections = 15), // tenant A CANNOT consume more than 15, EVER
    "tenant-b", createConnectionPool(maxConnections = 15), // tenant B's OWN separate allocation
    "tenant-c", createConnectionPool(maxConnections = 20)  // sized differently, based on tenant C's KNOWN higher volume
);
// a runaway tenant A exhausts ONLY its OWN 15-connection allocation -- tenant B and C are COMPLETELY unaffected
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unpartitioned shared connection pool lets any one tenant exhaust the entire fifty-connection capacity, starving every other tenant; a partitioned pool divides the same total capacity into fixed, guaranteed allocations per tenant, so one tenant's exhaustion is contained to its own share" >
  <rect x="20" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Unpartitioned: 50 shared</text>
  <text x="155" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">ANY tenant can exhaust ALL 50</text>
  <text x="155" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">starves EVERYONE else</text>

  <rect x="350" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Partitioned: 15+15+20</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">EACH tenant capped INDEPENDENTLY</text>
  <text x="485" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">one exhausting affects ONLY itself</text>
</svg>

The same total capacity, divided upfront into guaranteed shares, contains any single consumer's overconsumption to just its own allocation.

## 5. Runnable example

Scenario: a shared connection pool where one runaway tenant's excessive query load exhausts the entire pool, starving every other tenant, refactored to per-tenant partitioned pools that contain the runaway tenant's impact to its own allocation, and finally demonstrating unequal partition sizing based on each tenant's actual known traffic characteristics rather than uniform division, showing partitioning as a deliberate capacity-planning decision, not just an equal split.

### Level 1 — Basic

```java
// File: UnpartitionedSharedPool.java -- ONE shared pool; a RUNAWAY
// tenant exhausts it ENTIRELY, starving EVERY other tenant.
import java.util.concurrent.*;

public class UnpartitionedSharedPool {
    static Semaphore sharedConnections = new Semaphore(10); // ONE shared allocation for ALL tenants

    static boolean tryAcquireForTenant(String tenantId) { return sharedConnections.tryAcquire(); }

    public static void main(String[] args) {
        // tenant-a has a RUNAWAY query pattern -- acquires 9 of the 10 SHARED connections
        for (int i = 0; i < 9; i++) tryAcquireForTenant("tenant-a");

        boolean tenantBGotConnection = tryAcquireForTenant("tenant-b"); // tenant-b just needs ONE, ordinary connection
        System.out.println("tenant-a consumed 9/10 SHARED connections.");
        System.out.println("tenant-b's request for its OWN, ordinary work: " + (tenantBGotConnection ? "SUCCEEDED" : "STARVED -- only 1 connection left, shared with EVERYONE else"));
    }
}
```

**How to run:** `javac UnpartitionedSharedPool.java && java UnpartitionedSharedPool` (JDK 17+).

### Level 2 — Intermediate

```java
// File: PartitionedPerTenantPools.java -- EACH tenant gets its OWN
// guaranteed allocation -- tenant-a's runaway behavior CANNOT touch
// tenant-b's connections AT ALL.
import java.util.*;
import java.util.concurrent.*;

public class PartitionedPerTenantPools {
    static Map<String, Semaphore> perTenantConnections = Map.of(
        "tenant-a", new Semaphore(5), // tenant-a's OWN allocation
        "tenant-b", new Semaphore(5)  // tenant-b's SEPARATE, isolated allocation
    );

    static boolean tryAcquireForTenant(String tenantId) { return perTenantConnections.get(tenantId).tryAcquire(); }

    public static void main(String[] args) {
        // tenant-a's SAME runaway behavior -- but can ONLY consume from its OWN 5-connection allocation
        int tenantAAcquired = 0;
        for (int i = 0; i < 9; i++) if (tryAcquireForTenant("tenant-a")) tenantAAcquired++;

        boolean tenantBGotConnection = tryAcquireForTenant("tenant-b"); // tenant-b's SEPARATE pool -- UNTOUCHED
        System.out.println("tenant-a acquired " + tenantAAcquired + "/9 attempted connections (capped at its OWN allocation of 5).");
        System.out.println("tenant-b's request: " + (tenantBGotConnection ? "SUCCEEDED -- COMPLETELY unaffected by tenant-a" : "starved"));
    }
}
```

**How to run:** `javac PartitionedPerTenantPools.java && java PartitionedPerTenantPools` (JDK 17+).

Expected output:
```
tenant-a acquired 5/9 attempted connections (capped at its OWN allocation of 5).
tenant-b's request: SUCCEEDED -- COMPLETELY unaffected by tenant-a
```

### Level 3 — Advanced

```java
// File: UnequalPartitionSizingByTrafficProfile.java -- partitions are
// sized UNEQUALLY, based on EACH tenant's ACTUAL known traffic volume --
// a DELIBERATE capacity-planning decision, not a uniform, equal split.
import java.util.*;
import java.util.concurrent.*;

public class UnequalPartitionSizingByTrafficProfile {
    record TenantProfile(String tenantId, int observedAvgConcurrentQueries, int allocatedCapacity) {}

    static List<TenantProfile> planPartitions(Map<String, Integer> observedTrafficByTenant, int totalCapacity) {
        int totalObserved = observedTrafficByTenant.values().stream().mapToInt(Integer::intValue).sum();
        List<TenantProfile> plan = new ArrayList<>();
        for (var entry : observedTrafficByTenant.entrySet()) {
            // allocate PROPORIONALLY to each tenant's OBSERVED share of typical traffic, not an EQUAL split
            int allocated = (int) Math.round((double) entry.getValue() / totalObserved * totalCapacity);
            plan.add(new TenantProfile(entry.getKey(), entry.getValue(), allocated));
        }
        return plan;
    }

    public static void main(String[] args) {
        // REAL observed traffic: tenant-large uses FAR more typical concurrency than tenant-small
        Map<String, Integer> observedTraffic = new LinkedHashMap<>();
        observedTraffic.put("tenant-large", 60);  // observed: routinely runs ~60 concurrent queries
        observedTraffic.put("tenant-medium", 30); // observed: ~30
        observedTraffic.put("tenant-small", 10);  // observed: ~10

        List<TenantProfile> plan = planPartitions(observedTraffic, 100); // total pool capacity: 100 connections

        System.out.println("Partition plan (proportional to OBSERVED traffic, NOT an equal 33/33/33 split):");
        for (TenantProfile p : plan) {
            System.out.println("  " + p.tenantId() + ": observed avg=" + p.observedAvgConcurrentQueries() + " -> allocated capacity=" + p.allocatedCapacity());
        }
        System.out.println("\nAn EQUAL split (33/33/33) would have UNDER-provisioned tenant-large and OVER-provisioned tenant-small --");
        System.out.println("proportional partitioning matches ACTUAL capacity to ACTUAL need, while STILL containing any one tenant's overconsumption.");
    }
}
```

**How to run:** `javac UnequalPartitionSizingByTrafficProfile.java && java UnequalPartitionSizingByTrafficProfile` (JDK 17+).

Expected output:
```
Partition plan (proportional to OBSERVED traffic, NOT an equal 33/33/33 split):
  tenant-large: observed avg=60 -> allocated capacity=60
  tenant-medium: observed avg=30 -> allocated capacity=30
  tenant-small: observed avg=10 -> allocated capacity=10

An EQUAL split (33/33/33) would have UNDER-provisioned tenant-large and OVER-provisioned tenant-small --
proportional partitioning matches ACTUAL capacity to ACTUAL need, while STILL containing any one tenant's overconsumption.
```

## 6. Walkthrough

1. **Level 1, the shared-pool vulnerability** — `sharedConnections`, a single `Semaphore` with 10 permits, is drawn from by every tenant indiscriminately; tenant-a's simulated runaway behavior acquiring 9 of those 10 permits leaves only 1 remaining for tenant-b's completely ordinary, well-behaved request, which either barely succeeds or fails depending on exact timing — a fragile situation entirely caused by tenant-a's misbehavior having unrestricted access to the shared pool.
2. **Level 2, separate allocations per consumer** — `perTenantConnections` maps each tenant to its *own* independent `Semaphore`, each with its own fixed capacity of 5; tenant-a's identical runaway attempt to acquire 9 connections can now succeed at most 5 times, since `tryAcquireForTenant("tenant-a")` only ever draws from `tenant-a`'s own semaphore.
3. **Level 2, the isolation confirmed** — tenant-b's request checks `perTenantConnections.get("tenant-b")`, an entirely separate `Semaphore` object untouched by anything tenant-a did; the request succeeds cleanly and predictably, completely unaffected by tenant-a's misbehavior, which is exactly the containment partitioning is meant to provide.
4. **Level 3, sizing partitions by actual observed need** — `planPartitions` computes each tenant's allocated capacity proportionally to its `observedAvgConcurrentQueries` relative to the total observed traffic across all tenants, rather than dividing the total capacity equally regardless of actual usage patterns.
5. **Level 3, the resulting proportional allocation** — with observed traffic of 60, 30, and 10 for tenant-large, tenant-medium, and tenant-small respectively (totaling 100), and a total pool capacity of 100, each tenant's allocated capacity matches its proportional share exactly: 60, 30, and 10 connections respectively — deliberately mirroring their real, differing needs rather than an arbitrary equal split.
6. **Level 3, why proportional sizing matters alongside containment** — an equal three-way split (roughly 33 each) would have under-provisioned tenant-large (whose genuine, legitimate traffic routinely needs around 60 concurrent connections, more than an equal share would provide) while wastefully over-provisioning tenant-small (whose actual need is only around 10) — this demonstrates that resource partitioning isn't just about equally dividing a resource to prevent one consumer from starving another; it's a deliberate capacity-planning exercise that should match each partition's size to that consumer's actual, real-world resource needs, while still preserving the fundamental containment guarantee that no single consumer, however much traffic it generates, can ever exceed its own allocated share and affect anyone else's.

## 7. Gotchas & takeaways

> **Gotcha:** partitioning a resource based on traffic observed at one point in time can become stale as usage patterns shift — a tenant whose traffic grows well beyond its originally allocated partition will experience artificial throttling even though the resource as a whole (summed across all partitions) may have plenty of spare capacity sitting unused in other tenants' allocations; partition sizes need periodic review and rebalancing against current traffic, not a one-time allocation set once and left unchanged indefinitely.

- Resource partitioning to contain failures is the general principle behind the bulkhead pattern, applicable to any shared resource — connection pools, memory budgets, queue capacity, rate limits — not just thread concurrency.
- An unpartitioned shared resource lets any single consumer's overconsumption (whether from a bug, a runaway process, or simply unexpectedly high legitimate load) potentially exhaust the entire resource, degrading service for every other, unrelated consumer.
- Partitioning divides the resource upfront into fixed, guaranteed allocations per consumer, so one consumer's maximum possible impact is capped independently of how the resource is being used elsewhere.
- Partition sizes should be set deliberately based on each consumer's actual, observed resource needs — proportional to real traffic patterns — rather than an arbitrary equal split that could both under-serve high-volume consumers and waste capacity on low-volume ones.
- Partition sizing needs periodic revisiting as usage patterns evolve; a static allocation set once can become mismatched with reality over time, artificially constraining a growing consumer even while unused capacity sits idle in another consumer's shrinking allocation.
