---
card: system-design
gi: 131
slug: active-active-vs-active-passive-failover
title: Active-active vs active-passive failover
---

## 1. What it is

**Active-passive failover** keeps a standby copy of a system (or a whole data center) idle, ready to take over only if the primary fails. **Active-active** runs multiple copies simultaneously, all actively serving real traffic at the same time, with none of them sitting idle as a pure backup. Both are redundancy strategies, but they differ in whether the backup capacity is used during normal operation or held in reserve.

## 2. Why & when

Active-passive is simpler: the passive side does not need to handle real traffic or worry about being kept perfectly in sync in real time, only well enough to take over during a failure. But its standby capacity sits unused most of the time, and the failover process (detecting the failure and promoting the standby) takes some time, during which the system is degraded or down. Active-active uses all capacity all the time — no resource sits idle — and failing over is instant, since the other side is already actively serving traffic. Use active-passive when simplicity matters more than failover speed, or when running a full duplicate active system is not cost-justified. Use active-active when you need the fastest possible failover (effectively zero downtime) and can handle the added complexity of keeping multiple active sides consistent.

## 3. Core concept

- **Active-passive:** one primary handles all traffic; a standby replica stays synchronized (usually via [asynchronous replication](0101-synchronous-vs-asynchronous-replication.md)) but serves nothing until a failover promotes it.
- **Failover time (active-passive):** detecting the primary's failure, then promoting the standby, takes real time — often seconds to minutes — during which the system may be unavailable or serving stale data.
- **Active-active:** multiple nodes (or data centers) all serve live traffic simultaneously; if one fails, the others are already handling requests, so users see no interruption at all for that failure.
- **Active-active's consistency cost:** since multiple active sides can accept writes independently, active-active for data typically needs [multi-leader](0099-multi-leader-replication.md) or [leaderless replication](0100-leaderless-replication-dynamo-style.md), with the conflict-resolution complexity that comes with them.
- **Choosing between them:** active-passive trades failover speed and resource utilization for operational simplicity; active-active trades operational complexity (conflict resolution, keeping multiple actives truly consistent) for near-zero failover time and full resource utilization.

## 4. Diagram

```
ACTIVE-PASSIVE:                       ACTIVE-ACTIVE:

  [Primary] <- ALL traffic             [Node A] <- some traffic
     |                                 [Node B] <- some traffic    (both serving
  replicates to                        [Node C] <- some traffic     live traffic
     v                                                               simultaneously)
  [Standby] (idle, not serving)
                                       Node B fails:
  Primary fails:                      [Node A] <- traffic shifts
  [Standby] promoted ->               [Node C] <- traffic shifts    (instant,
  takes over (failover delay)                                        no promotion
                                                                       needed)
```
*Caption: active-passive's standby sits idle until promoted, with a delay; active-active's surviving nodes are already serving traffic the instant one fails.*

## 5. Runnable example

**Level 1 — Basic.** Model active-passive: the standby is idle, and a failover has a measurable delay.

**Level 2 — Active-active.** All nodes serve live traffic; one failing simply redistributes load among survivors, with no promotion delay.

**Level 3 — Compare downtime.** Measure the effective downtime window for both strategies under the same failure.

```java
// FailoverStrategies.java
import java.util.*;

public class FailoverStrategies {

    public static void main(String[] args) {
        // Level 1: active-passive - standby is idle until promoted.
        String primary = "primary-server";
        String standby = "standby-server (idle)";
        System.out.println("normal operation: ALL traffic -> " + primary + ", " + standby + " serving nothing");

        boolean primaryFailed = true;
        int failoverDetectionMs = 3000; // time to detect the failure
        int failoverPromotionMs = 2000; // time to promote the standby
        int totalFailoverDelayMs = failoverDetectionMs + failoverPromotionMs;
        System.out.println("primary fails! detecting failure: " + failoverDetectionMs + "ms, promoting standby: " + failoverPromotionMs + "ms");
        System.out.println("total downtime during active-passive failover: " + totalFailoverDelayMs + "ms");
        System.out.println("after failover: ALL traffic -> " + standby + " (now promoted to primary)");

        // Level 2: active-active - all nodes already serving traffic; one fails, load redistributes instantly.
        List<String> activeNodes = new ArrayList<>(List.of("node-A", "node-B", "node-C"));
        Map<String, Integer> trafficShare = new LinkedHashMap<>();
        for (String node : activeNodes) trafficShare.put(node, 100 / activeNodes.size()); // ~33% each
        System.out.println("--- active-active, normal operation ---");
        System.out.println("traffic distribution: " + trafficShare);

        activeNodes.remove("node-B"); // node-B fails
        trafficShare.clear();
        for (String node : activeNodes) trafficShare.put(node, 100 / activeNodes.size()); // instantly recalculated
        System.out.println("node-B fails -> traffic redistributes IMMEDIATELY: " + trafficShare);
        System.out.println("downtime during active-active failover: 0ms (survivors were already serving live traffic)");

        // Level 3: direct downtime comparison for the same failure event.
        System.out.println("--- summary ---");
        System.out.println("active-passive downtime for this failure: " + totalFailoverDelayMs + "ms");
        System.out.println("active-active downtime for this failure: 0ms");
    }
}
```

**How to run:** save as `FailoverStrategies.java`, then run `java FailoverStrategies.java`.

## 6. Walkthrough

1. Level 1 models `standby` as explicitly idle during normal operation; when `primaryFailed` becomes `true`, the code sums `failoverDetectionMs` and `failoverPromotionMs` into a `totalFailoverDelayMs` — this delay is real, measurable downtime that occurs before traffic can move to the now-promoted standby.
2. Level 2 starts with 3 active nodes each already receiving roughly a third of traffic; when `node-B` is removed from `activeNodes` (modeling its failure), the traffic distribution is recalculated across the remaining two nodes.
3. Because `node-A` and `node-C` were already serving live traffic before the failure, there is no "promotion" step needed at all — the recalculation of `trafficShare` happens immediately, in the same statement, with no artificial delay modeled, unlike the active-passive case's explicit `totalFailoverDelayMs`.
4. The Level 3 summary directly contrasts the two numbers: the active-passive scenario's `totalFailoverDelayMs` (5000ms in this example) against active-active's `0ms` — quantifying the core trade-off these two strategies make.
5. This comparison is the central lesson: active-active is not simply "more redundant" than active-passive, it specifically eliminates the failover *delay*, at the cost of needing every active side to already be correctly serving traffic and staying consistent with the others.

## 7. Gotchas & takeaways

> Gotcha: active-passive's standby is often the most under-tested part of the whole system, precisely because it never serves real traffic during normal operation — a subtle bug or misconfiguration in the standby can go completely unnoticed until the moment a real failover is needed, when it is too late to catch. Regularly test failover to the standby (a "game day" drill) rather than assuming it works.

- Active-passive keeps a standby idle until a failure triggers a promotion, which takes real, measurable time; active-active keeps every node serving live traffic, so a failure causes no promotion delay at all.
- Active-active fully utilizes its capacity during normal operation, unlike active-passive's idle standby.
- The trade-off is complexity: active-active generally needs multi-leader or leaderless replication and conflict resolution, while active-passive can use simpler single-leader replication.
- Related concepts: [Redundancy & replication](0130-redundancy-replication.md) (the general principle both strategies implement), [Multi-leader replication](0099-multi-leader-replication.md) (commonly needed to support an active-active data layer).
