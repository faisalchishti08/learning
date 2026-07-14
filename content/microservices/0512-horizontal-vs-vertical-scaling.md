---
card: microservices
gi: 512
slug: horizontal-vs-vertical-scaling
title: "Horizontal vs vertical scaling"
---

## 1. What it is

**Vertical scaling** (scaling up) means giving a single instance more resources — more CPU, more memory — to handle more load. **Horizontal scaling** (scaling out) means running more instances of the same service, each handling a share of the total load, coordinated by a load balancer. Microservices architectures are built around horizontal scaling as the primary strategy, which is precisely why [statelessness](0513-stateless-services-for-scaling.md) matters so much: only a stateless service can be scaled horizontally by simply adding more identical, interchangeable copies.

## 2. Why & when

You lean toward horizontal scaling as the default for microservices specifically because of properties vertical scaling can't provide:

- **Vertical scaling has a hard ceiling.** There's a maximum amount of CPU and memory a single machine can have, and beyond that ceiling, vertical scaling simply isn't an option anymore, regardless of budget — horizontal scaling has no such intrinsic limit, since you can keep adding more instances.
- **Vertical scaling means a single point of failure remains a single point of failure, just a bigger one.** One larger instance is still one instance — if it crashes, the service is completely down; horizontal scaling means the loss of any single instance leaves the others still serving traffic.
- **Horizontal scaling matches how [rolling deployments](0450-rolling-deployment.md) and elastic autoscaling actually work.** Kubernetes and similar orchestrators are built around adding and removing instances dynamically in response to load — a capability that only makes sense for a horizontally-scalable service in the first place.
- **You reach for vertical scaling for the specific pieces of a system that genuinely can't be horizontally scaled** — a single-writer database primary, for instance — and horizontal scaling for everything else, which in a well-designed microservices system is most of the application tier.

## 3. Core concept

Think of a restaurant needing to serve more customers: vertical scaling is hiring one incredibly fast, superhuman chef who can somehow cook faster and faster as demand grows — until you hit the physical limit of how fast one person can possibly cook, and if that one chef gets sick, the kitchen stops entirely. Horizontal scaling is instead hiring more ordinary chefs, each capable of independently preparing any dish — demand grows, you add more chefs; one chef calls in sick, the others keep the kitchen running.

Concretely:

1. **Vertical scaling** increases a single instance's `cpu`/`memory` allocation (in Kubernetes terms, its resource requests/limits, or literally provisioning a larger machine) — the number of running instances stays the same, but each one can do more.
2. **Horizontal scaling** increases the *number* of instances (`replicas` in a Kubernetes Deployment) — each individual instance's resource allocation stays the same, but there are more of them collectively sharing the total load.
3. **A load balancer distributes traffic across horizontally-scaled instances**, which is what makes horizontal scaling actually usable — without something routing traffic across the fleet, adding more instances wouldn't help handle more requests.
4. **Statelessness is the prerequisite that makes horizontal scaling correct**, not just possible — a request routed to any instance must be able to be handled correctly by that instance, which only works if instances don't hold request-specific state that only exists on one specific instance.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Vertical scaling makes one instance bigger with a hard ceiling; horizontal scaling adds more identical instances behind a load balancer with no intrinsic limit" >
  <rect x="20" y="20" width="270" height="150" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="155" y="42" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">VERTICAL: bigger instance</text>
  <rect x="90" y="80" width="130" height="60" rx="6" fill="#141a22" stroke="#f0883e"/>
  <text x="155" y="115" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">1 large instance</text>
  <text x="155" y="155" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">hard ceiling; single point of failure</text>

  <rect x="350" y="20" width="290" height="150" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">HORIZONTAL: more instances</text>
  <rect x="365" y="70" width="60" height="40" rx="4" fill="#141a22" stroke="#6db33f"/>
  <rect x="435" y="70" width="60" height="40" rx="4" fill="#141a22" stroke="#6db33f"/>
  <rect x="505" y="70" width="60" height="40" rx="4" fill="#141a22" stroke="#6db33f"/>
  <rect x="575" y="70" width="55" height="40" rx="4" fill="#141a22" stroke="#6db33f"/>
  <text x="495" y="155" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no intrinsic limit; one loss survives</text>
</svg>

Vertical scaling grows one instance to a ceiling; horizontal scaling adds more instances with no such limit.

## 5. Runnable example

Scenario: a load simulator comparing vertical and horizontal scaling under growing demand. We start with basic vertical scaling hitting its ceiling, extend it to horizontal scaling adding instances to absorb the same growth, then handle the hard case: one instance failing under horizontal scaling, showing the fleet continues serving traffic, versus the same failure under vertical scaling taking the whole service down.

### Level 1 — Basic

```java
// File: VerticalScalingCeiling.java -- models VERTICAL scaling: ONE
// instance's capacity grows with each upgrade, but hits a HARD CEILING.
public class VerticalScalingCeiling {
    static int instanceCapacity = 100; // requests/sec this one instance can handle
    static int maxPossibleCapacity = 500; // the largest machine size actually available

    static void scaleVertically(int addedCapacity) {
        int newCapacity = instanceCapacity + addedCapacity;
        if (newCapacity > maxPossibleCapacity) {
            System.out.println("[vertical] CANNOT scale to " + newCapacity + " -- exceeds max possible capacity of " + maxPossibleCapacity);
            instanceCapacity = maxPossibleCapacity;
        } else {
            instanceCapacity = newCapacity;
            System.out.println("[vertical] scaled up to " + instanceCapacity + " req/sec (1 instance)");
        }
    }

    public static void main(String[] args) {
        scaleVertically(100);
        scaleVertically(150);
        scaleVertically(200); // this pushes past the ceiling
        System.out.println("[final] capacity capped at " + instanceCapacity + " req/sec -- cannot grow further, regardless of budget");
    }
}
```

How to run: `java VerticalScalingCeiling.java`

`scaleVertically` checks each requested increase against `maxPossibleCapacity` — the third call attempts to push `instanceCapacity` from `350` to `550`, exceeding the `500` ceiling, so the code caps it at the maximum rather than allowing an impossible value, concretely demonstrating vertical scaling's hard, physical limit.

### Level 2 — Intermediate

```java
// File: HorizontalScalingNoLimit.java -- the SAME growing demand, now
// met via HORIZONTAL scaling: adding MORE instances, each with FIXED,
// modest capacity, with NO intrinsic ceiling on how many can be added.
import java.util.*;

public class HorizontalScalingNoLimit {
    static int perInstanceCapacity = 100; // fixed, modest capacity per instance
    static List<String> instances = new ArrayList<>();

    static void scaleHorizontally(int additionalInstances) {
        for (int i = 0; i < additionalInstances; i++) {
            instances.add("instance-" + (instances.size() + 1));
        }
        int totalCapacity = instances.size() * perInstanceCapacity;
        System.out.println("[horizontal] now running " + instances.size() + " instances, total capacity " + totalCapacity + " req/sec");
    }

    public static void main(String[] args) {
        scaleHorizontally(1);
        scaleHorizontally(2);
        scaleHorizontally(5); // far beyond what a SINGLE vertical instance could ever reach
        System.out.println("[final] " + instances.size() + " instances, " + (instances.size() * perInstanceCapacity)
                + " req/sec total -- no intrinsic ceiling, just add more instances");
    }
}
```

How to run: `java HorizontalScalingNoLimit.java`

`scaleHorizontally` simply grows the `instances` list — there's no check against any maximum anywhere in this code, because horizontal scaling genuinely has no intrinsic ceiling analogous to `maxPossibleCapacity` in the vertical case; total capacity is just `instances.size() * perInstanceCapacity`, a value that can keep growing as long as you're willing to add more instances.

### Level 3 — Advanced

```java
// File: HorizontalScalingSurvivesFailure.java -- the SAME two scaling
// approaches, now handling the PRODUCTION-FLAVORED hard case: an
// INSTANCE FAILURE. Under VERTICAL scaling, the ONE instance failing
// means TOTAL OUTAGE. Under HORIZONTAL scaling, ONE instance failing
// still leaves the REST serving traffic -- the fleet SURVIVES.
import java.util.*;

public class HorizontalScalingSurvivesFailure {
    static int verticalInstanceCapacity = 500; // one large, maximally-scaled instance
    static boolean verticalInstanceHealthy = true;

    static List<String> horizontalInstances = new ArrayList<>(List.of(
        "instance-1", "instance-2", "instance-3", "instance-4", "instance-5"
    ));
    static int perInstanceCapacity = 100;

    static void simulateInstanceFailure_Vertical() {
        System.out.println("[incident] the ONE vertically-scaled instance crashes");
        verticalInstanceHealthy = false;
    }

    static void simulateInstanceFailure_Horizontal(String failedInstance) {
        System.out.println("[incident] " + failedInstance + " crashes (one of " + horizontalInstances.size() + " instances)");
        horizontalInstances.remove(failedInstance);
    }

    public static void main(String[] args) {
        System.out.println("--- BEFORE any failure ---");
        System.out.println("[vertical] capacity: " + (verticalInstanceHealthy ? verticalInstanceCapacity : 0) + " req/sec");
        System.out.println("[horizontal] capacity: " + (horizontalInstances.size() * perInstanceCapacity) + " req/sec ("
                + horizontalInstances.size() + " instances)");

        System.out.println();
        System.out.println("--- AFTER one instance fails in each scenario ---");
        simulateInstanceFailure_Vertical();
        simulateInstanceFailure_Horizontal("instance-3");

        System.out.println();
        int verticalRemainingCapacity = verticalInstanceHealthy ? verticalInstanceCapacity : 0;
        int horizontalRemainingCapacity = horizontalInstances.size() * perInstanceCapacity;
        System.out.println("[vertical] remaining capacity: " + verticalRemainingCapacity + " req/sec -- TOTAL OUTAGE, the only instance is down");
        System.out.println("[horizontal] remaining capacity: " + horizontalRemainingCapacity + " req/sec -- DEGRADED but STILL SERVING traffic ("
                + horizontalInstances.size() + " instances remain)");
    }
}
```

How to run: `java HorizontalScalingSurvivesFailure.java`

`simulateInstanceFailure_Vertical` sets `verticalInstanceHealthy = false`, and since there's only ever one vertical instance, this single flag flipping means `verticalRemainingCapacity` computes to `0` — a complete outage. `simulateInstanceFailure_Horizontal` removes just one entry from the five-element `horizontalInstances` list, and `horizontalRemainingCapacity` still computes to `4 * 100 = 400` — reduced, but very much non-zero, demonstrating that horizontal scaling's redundancy is what actually provides fault tolerance, not just raw capacity.

## 6. Walkthrough

Trace `HorizontalScalingSurvivesFailure.main` in order. **First**, the "before" section prints both scenarios' healthy-state capacity: `vertical` reports `500` (since `verticalInstanceHealthy` is still `true`), and `horizontal` reports `500` too (`5 instances * 100` each) — both scenarios start with identical total capacity, making the comparison fair.

**Next**, `simulateInstanceFailure_Vertical()` runs, setting `verticalInstanceHealthy` to `false` — this single boolean flip represents the entirety of the vertical scenario's failure, since there's nothing else to fail or remain standing.

**Then**, `simulateInstanceFailure_Horizontal("instance-3")` runs, calling `horizontalInstances.remove("instance-3")` — this removes exactly one entry from the five-element list, leaving four instances (`instance-1`, `instance-2`, `instance-4`, `instance-5`) still present and, implicitly, still healthy.

**After that**, `verticalRemainingCapacity` is computed via the ternary `verticalInstanceHealthy ? verticalInstanceCapacity : 0` — since `verticalInstanceHealthy` is now `false`, this evaluates to `0` regardless of how large `verticalInstanceCapacity` was.

**Finally**, `horizontalRemainingCapacity` is computed as `horizontalInstances.size() * perInstanceCapacity`, which is `4 * 100 = 400` — `main` prints both final numbers side by side, making the contrast unmistakable: the exact same "one instance fails" event produces a complete `0` req/sec outage in the vertical scenario, and a reduced-but-functional `400` req/sec in the horizontal scenario, purely because of how many independent instances existed to begin with.

```
--- BEFORE any failure ---
[vertical] capacity: 500 req/sec
[horizontal] capacity: 500 req/sec (5 instances)

--- AFTER one instance fails in each scenario ---
[incident] the ONE vertically-scaled instance crashes
[incident] instance-3 crashes (one of 5 instances)

[vertical] remaining capacity: 0 req/sec -- TOTAL OUTAGE, the only instance is down
[horizontal] remaining capacity: 400 req/sec -- DEGRADED but STILL SERVING traffic (4 instances remain)
```

## 7. Gotchas & takeaways

> Vertical scaling isn't just a capacity strategy with a ceiling — it's also a fault-tolerance liability, since "one big instance" means "one point of total failure," regardless of how much capacity that instance has. Horizontal scaling delivers both greater achievable capacity *and* fault tolerance, which is why it's the default strategy for microservices, not merely a scaling preference.
- Horizontal scaling fundamentally depends on [statelessness](0513-stateless-services-for-scaling.md) — a stateful service can't correctly be scaled horizontally, since a request routed to a different instance than the one holding its relevant state would behave incorrectly.
- Vertical scaling still has a legitimate, important role for genuinely single-instance components — a database's primary writer, for example, where horizontal write scaling requires much more sophisticated (and often more complex) approaches like sharding.
- Combine both in practice: horizontally scale the stateless application tier for capacity and fault tolerance, and appropriately vertically scale the specific stateful components (databases, caches) that can't be horizontally scaled as straightforwardly.
- A load balancer is a required piece of infrastructure for horizontal scaling to actually work — capacity spread across many instances is only usable if something correctly routes traffic across all of them, ideally accounting for each instance's current health and load.
