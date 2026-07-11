---
card: spring-cloud
gi: 34
slug: region-zone-awareness
title: "Region & zone awareness"
---

## 1. What it is

Eureka can group instances by availability zone (and region, one level up), and a zone-aware client prefers discovering and calling instances in its *own* zone before falling back to instances in other zones. This keeps traffic local when possible — lower latency, no cross-zone network cost — while still functioning if the local zone runs out of healthy instances.

```properties
eureka.instance.metadata-map.zone=us-east-1a
eureka.client.region=us-east-1
eureka.client.availability-zones.us-east-1=us-east-1a,us-east-1b,us-east-1c
eureka.client.prefer-same-zone-eureka=true
```

## 2. Why & when

Calling an instance in the same availability zone is faster and usually cheaper than calling one in a different zone — cross-zone traffic typically has higher latency and, on most cloud providers, an explicit data-transfer cost. Left to plain round-robin discovery (from the earlier client card), a caller in `us-east-1a` would just as happily call an instance in `us-east-1c` as one three racks away, wasting both latency and money for no benefit.

Reach for region/zone awareness when:

- Services are deployed across multiple availability zones for resilience, and you want normal traffic to stay zone-local for performance, while still surviving a whole-zone outage by falling back to other zones.
- Cross-zone data transfer cost is a real budget line item — keeping the bulk of internal service-to-service traffic zone-local measurably reduces it.
- You're operating at a scale where "closest instance" genuinely matters — for a two-instance dev setup running in one zone, this feature has nothing to do.

## 3. Core concept

```
 caller in zone A
    |
    |-- 1st preference: instances of target service also in zone A
    |-- fallback: instances in other known zones (B, C, ...), if zone A has none healthy
```

Zone-aware discovery is round-robin *within* the preferred zone first, only reaching into other zones when the local zone can't fully serve the request.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A caller in zone A prefers billing-service instances also in zone A, only reaching into zone B when zone A has no healthy instances left">
  <rect x="20" y="20" width="280" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="38" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">zone A</text>
  <rect x="35" y="50" width="110" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90" y="69" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">caller</text>
  <rect x="165" y="50" width="120" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="225" y="69" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billing-1 (zone A)</text>

  <line x1="145" y1="65" x2="163" y2="65" stroke="#6db33f" stroke-width="1.6" marker-end="url(#a34)"/>
  <text x="155" y="95" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">preferred</text>

  <rect x="340" y="20" width="280" height="80" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="480" y="38" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">zone B</text>
  <rect x="465" y="50" width="120" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="525" y="69" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billing-2 (zone B)</text>

  <line x1="145" y1="80" x2="500" y2="140" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="3,3" marker-end="url(#a34)"/>
  <text x="320" y="160" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fallback only if zone A has no healthy instance</text>

  <defs><marker id="a34" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Zone-local instances are tried first; cross-zone instances are a fallback, not an equal peer in the rotation.

## 5. Runnable example

The scenario: `orders-service` in zone A calling `billing-service` instances spread across zones A and B. Start with zone-blind round-robin, then add zone preference, then add automatic fallback when the local zone's instances are all unhealthy.

### Level 1 — Basic

Zone-blind round-robin — the previous card's discovery behavior, with no notion of locality.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class RegionZoneLevel1 {
    record Instance(String address, String zone) {}

    static List<Instance> billingInstances = List.of(
            new Instance("10.0.1.1:8080", "us-east-1a"),
            new Instance("10.0.1.2:8080", "us-east-1a"),
            new Instance("10.0.2.1:8080", "us-east-1b")
    );
    static AtomicInteger counter = new AtomicInteger(0);

    static Instance discover() {
        return billingInstances.get(counter.getAndIncrement() % billingInstances.size());
    }

    public static void main(String[] args) {
        // caller runs in us-east-1a, but discover() doesn't know or care
        for (int i = 0; i < 3; i++) {
            Instance inst = discover();
            System.out.println("call " + i + " -> " + inst.address() + " (" + inst.zone() + ")");
        }
    }
}
```

How to run: `java RegionZoneLevel1.java`

One out of every three calls lands on the cross-zone instance in `us-east-1b`, purely by round-robin luck — even though two perfectly good same-zone instances exist. That's wasted cross-zone latency and cost with no benefit.

### Level 2 — Intermediate

Add zone preference: partition instances into "same zone as caller" and "other zones," and only reach into "other zones" if the local list is empty.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

public class RegionZoneLevel2 {
    record Instance(String address, String zone) {}

    static List<Instance> billingInstances = List.of(
            new Instance("10.0.1.1:8080", "us-east-1a"),
            new Instance("10.0.1.2:8080", "us-east-1a"),
            new Instance("10.0.2.1:8080", "us-east-1b")
    );
    static AtomicInteger counter = new AtomicInteger(0);
    static String callerZone = "us-east-1a";

    static Instance discover() {
        List<Instance> sameZone = billingInstances.stream()
                .filter(i -> i.zone().equals(callerZone)).collect(Collectors.toList());
        List<Instance> pool = sameZone.isEmpty() ? billingInstances : sameZone;
        return pool.get(counter.getAndIncrement() % pool.size());
    }

    public static void main(String[] args) {
        for (int i = 0; i < 4; i++) {
            Instance inst = discover();
            System.out.println("call " + i + " -> " + inst.address() + " (" + inst.zone() + ")");
        }
    }
}
```

How to run: `java RegionZoneLevel2.java`

`discover()` now filters to `sameZone` first; since `us-east-1a` has two healthy instances, `pool` is that filtered list, and every one of the four calls lands on `10.0.1.1` or `10.0.1.2` — the cross-zone `us-east-1b` instance is never touched while zone-local instances are available.

### Level 3 — Advanced

Add automatic fallback: mark the zone-A instances unhealthy (simulating a zone outage or a bad deploy) and confirm discovery correctly falls back to the remaining zone instead of returning nothing.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

public class RegionZoneLevel3 {
    static class Instance {
        String address, zone;
        boolean healthy = true;
        Instance(String address, String zone) { this.address = address; this.zone = zone; }
    }

    static List<Instance> billingInstances = List.of(
            new Instance("10.0.1.1:8080", "us-east-1a"),
            new Instance("10.0.1.2:8080", "us-east-1a"),
            new Instance("10.0.2.1:8080", "us-east-1b")
    );
    static AtomicInteger counter = new AtomicInteger(0);
    static String callerZone = "us-east-1a";

    static Instance discover() {
        List<Instance> healthy = billingInstances.stream().filter(i -> i.healthy).collect(Collectors.toList());
        List<Instance> sameZoneHealthy = healthy.stream().filter(i -> i.zone.equals(callerZone)).collect(Collectors.toList());
        List<Instance> pool = sameZoneHealthy.isEmpty() ? healthy : sameZoneHealthy;
        if (pool.isEmpty()) throw new IllegalStateException("no healthy billing-service instances anywhere");
        return pool.get(counter.getAndIncrement() % pool.size());
    }

    public static void main(String[] args) {
        System.out.println("-- zone A healthy --");
        for (int i = 0; i < 2; i++) System.out.println("call " + i + " -> " + describe(discover()));

        // zone A outage: both us-east-1a instances go unhealthy
        billingInstances.stream().filter(i -> i.zone.equals("us-east-1a")).forEach(i -> i.healthy = false);

        System.out.println("-- zone A down, falling back to zone B --");
        for (int i = 0; i < 2; i++) System.out.println("call " + i + " -> " + describe(discover()));
    }

    static String describe(Instance i) { return i.address + " (" + i.zone + ")"; }
}
```

How to run: `java RegionZoneLevel3.java`

Before the simulated outage, every call stays in `us-east-1a` exactly as in Level 2. After both zone-A instances are marked unhealthy, `sameZoneHealthy` becomes empty, so `pool` falls back to `healthy` (all healthy instances regardless of zone) — which is now just the single `us-east-1b` instance. Discovery correctly keeps working during a full local-zone outage instead of throwing, because the fallback path was built in from the start.

## 6. Walkthrough

Trace Level 3's full run.

1. The first loop calls `discover()` twice while all three instances are healthy. Each call computes `healthy` (all three), then `sameZoneHealthy` (the two `us-east-1a` instances), and since that list is non-empty, `pool` is set to it — both calls round-robin between `10.0.1.1` and `10.0.1.2`, never touching the zone-B instance, matching Level 2's behavior.
2. The zone-A outage is simulated by flipping `healthy = false` on both `us-east-1a` instances — this models something like a bad deploy or an actual availability-zone-level network event that Eureka's health-check propagation (the previous card) would detect and report.
3. The second loop calls `discover()` twice more. Now `healthy` contains only the `us-east-1b` instance; `sameZoneHealthy` filters that down further to instances matching `callerZone="us-east-1a"`, which is empty, so `pool` falls back to the full `healthy` list — just the one zone-B instance.
4. Both fallback calls correctly return `10.0.2.1:8080 (us-east-1b)` — the caller keeps functioning, at the cost of now paying cross-zone latency for every call, exactly the tradeoff zone awareness is designed to make only when necessary.

```
discover():
  healthy          = filter(all instances, i.healthy)
  sameZoneHealthy  = filter(healthy, i.zone == callerZone)
  pool             = sameZoneHealthy.isEmpty() ? healthy : sameZoneHealthy
  return round_robin(pool)
```

## 7. Gotchas & takeaways

> **Gotcha:** `prefer-same-zone-eureka` affects which Eureka *server* a client talks to, and zone-aware load balancing affects which *service instance* a client calls — they're related but separate settings, both needed together for full zone-local behavior end to end (talk to a local registry, and get routed to local instances).

- Zone awareness only pays off once you actually run instances in more than one zone — for a single-zone deployment it's a no-op with the fallback path never exercised.
- The fallback to other zones is what keeps a service reachable during a zone-local outage — without it, zone preference would turn a partial outage into a full one for zone-A callers.
- `eureka.instance.metadata-map.zone` must be set correctly and consistently across every instance, or zone-matching silently fails and every call falls back to the "reach into all zones" path.
- Region is one level above zone (a region typically contains multiple zones) — most zone-awareness configuration only needs the zone list; region grouping matters more for genuinely multi-region deployments.
