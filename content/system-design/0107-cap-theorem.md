---
card: system-design
gi: 107
slug: cap-theorem
title: CAP theorem
---

## 1. What it is

The **CAP theorem** states that a distributed data system can provide at most two of three properties at the same time: **Consistency** (every read sees the latest write), **Availability** (every request gets a response, even if it might not be the latest data), and **Partition tolerance** (the system keeps working even when network failures split it into groups of nodes that cannot talk to each other). Since real networks do fail, partition tolerance is not really optional — so the theorem, in practice, is a choice between Consistency and Availability *during a partition*.

## 2. Why & when

You need the CAP theorem to make an honest decision about what your system does when — not if — a network partition happens: two data centers lose their link, or a node loses contact with the rest of the cluster. During that partition, each isolated group must choose: keep answering requests with whatever data it has (favoring **A**vailability, risking stale or conflicting answers), or refuse to answer unless it can confirm it has the latest data (favoring **C**onsistency, risking some requests failing). This decision only matters *during* a partition — once the network heals, both choices can converge again. Every distributed database makes this choice somewhere, so understanding it tells you what to expect from a specific technology under failure.

## 3. Core concept

- **Consistency (C):** every node that answers a read returns the most recent write — this is the same guarantee as [strong consistency](0103-strong-consistency.md).
- **Availability (A):** every request that reaches a non-failed node receives *some* response, even if that response might not reflect the very latest write.
- **Partition tolerance (P):** the system continues to operate despite network messages between some nodes being dropped or delayed.
- **The actual choice — CP vs AP, during a partition:** a **CP** system refuses to answer a request on the isolated side of a partition if it cannot guarantee the answer is current — sacrificing availability. An **AP** system answers anyway, using whatever data it has locally — sacrificing consistency, at least temporarily.
- **"CA" is not a real option at scale:** a system that promises both consistency and availability with zero partition tolerance can only work if there is never a partition — for any real distributed system with more than one node over a real network, partitions eventually happen, so this combination is not a meaningful design goal.
- **This is strictly about behavior during a partition:** it says nothing about a system's normal-operation trade-offs (e.g. read/write latency when everything is healthy) — that is a separate set of decisions, like the ones in [quorum reads/writes](0106-quorum-reads-writes-r-w-n.md).

## 4. Diagram

```
Network partition splits the cluster into two isolated groups:

   Group 1 (has the leader)          Group 2 (isolated, cannot reach Group 1)
   +------------------+              +------------------+
   | Node A (leader)  |   X-----X    | Node B (follower) |
   +------------------+  (partition) +------------------+

CP CHOICE: Node B refuses reads/writes it cannot confirm are current.
           -> Group 2's users get errors. Consistency preserved.

AP CHOICE: Node B keeps answering reads/writes with its local data.
           -> Group 2's users get answers, possibly stale/conflicting
              with what Group 1 is doing. Availability preserved.
```
*Caption: during a partition, the isolated side must choose between refusing requests (CP) or answering with possibly stale data (AP).*

## 5. Runnable example

**Level 1 — Basic.** Model two node groups and simulate a partition between them.

**Level 2 — CP behavior.** The isolated group refuses to serve requests it cannot verify are current.

**Level 3 — AP behavior.** The isolated group serves requests anyway, and the two groups reconcile once the partition heals.

```java
// CapTheorem.java
import java.util.*;

public class CapTheorem {

    static Map<String, Integer> groupOneData = new HashMap<>();
    static Map<String, Integer> groupTwoData = new HashMap<>();
    static boolean partitioned = false;

    static void write(String key, int value, boolean toGroupOne) {
        if (toGroupOne) groupOneData.put(key, value);
        else groupTwoData.put(key, value);
        if (!partitioned) { groupOneData.put(key, value); groupTwoData.put(key, value); } // replicates when healthy
    }

    // CP behavior: refuse if this group cannot confirm it is in sync (i.e. it's on the isolated side).
    static Integer cpRead(String key, boolean isIsolatedSide) {
        if (partitioned && isIsolatedSide) {
            System.out.println("CP system: refusing read on isolated side - cannot guarantee latest data");
            return null;
        }
        return groupOneData.get(key);
    }

    // AP behavior: always answer, using whatever local data this group has.
    static Integer apRead(String key, Map<String, Integer> localGroupData) {
        return localGroupData.get(key); // answers even if potentially stale
    }

    public static void main(String[] args) {
        // Level 1: healthy state - both groups agree.
        write("stock_price", 100, true);
        System.out.println("before partition -> group1: " + groupOneData.get("stock_price") + ", group2: " + groupTwoData.get("stock_price"));

        partitioned = true;
        System.out.println("--- network partition begins: group2 is now isolated ---");

        write("stock_price", 150, true); // only group1 (has the "leader") receives this write

        // Level 2: CP - group2 (isolated) refuses to answer rather than risk staleness.
        Integer cpResult = cpRead("stock_price", true);
        System.out.println("CP read from isolated group2: " + cpResult + " (request failed, consistency preserved)");

        // Level 3: AP - group2 answers anyway, using its last known (now stale) value.
        Integer apResult = apRead("stock_price", groupTwoData);
        System.out.println("AP read from isolated group2: " + apResult + " (stale, but the request succeeded)");

        // Partition heals - reconcile.
        partitioned = false;
        groupTwoData.put("stock_price", groupOneData.get("stock_price"));
        System.out.println("--- partition heals, group2 catches up to: " + groupTwoData.get("stock_price") + " ---");
    }
}
```

**How to run:** save as `CapTheorem.java`, then run `java CapTheorem.java`.

## 6. Walkthrough

1. Before the partition, `write("stock_price", 100, true)` updates both `groupOneData` and `groupTwoData`, since `partitioned` is still `false` — both groups agree, as shown by the first print.
2. `partitioned` flips to `true`, then `write("stock_price", 150, true)` only updates `groupOneData`, because the replication step inside `write` is skipped while partitioned — modeling `group2` becoming isolated and missing this update.
3. `cpRead("stock_price", true)` checks `partitioned && isIsolatedSide` and returns `null` immediately, printing that it refuses to answer — this is the CP choice: no answer rather than a possibly-wrong one.
4. `apRead("stock_price", groupTwoData)` simply returns whatever `groupTwoData` currently holds — `100`, the last value it knew before the partition — printing that stale value as a successful response. This is the AP choice: an answer, but not necessarily the latest one.
5. Once `partitioned` is set back to `false`, `groupTwoData` is explicitly caught up to `groupOneData`'s current value (`150`), modeling reconciliation after the network heals — both groups agree again, closing the loop.

## 7. Gotchas & takeaways

> Gotcha: CAP is often mis-stated as "pick any two of three, all the time" — but partition tolerance cannot really be opted out of for any system spanning more than one node over a real network. The only meaningful, ongoing choice is CP versus AP, and only during an actual partition; outside of a partition, a well-built system can offer both consistency and availability simultaneously.

- CAP forces a choice between consistency and availability specifically during a network partition; partition tolerance itself is not optional for a real distributed system.
- A CP system refuses requests it cannot verify are current; an AP system answers with whatever local data it has, possibly stale.
- The choice only applies during the partition itself — once the network heals, the system reconciles and can resume offering both properties.
- Related concepts: [Strong consistency](0103-strong-consistency.md) (the "C" side of the trade-off), [Eventual consistency](0104-eventual-consistency.md) (a common consequence of choosing "A"), [PACELC theorem](0108-pacelc-theorem.md) (extends this trade-off to normal, non-partitioned operation).
