---
card: system-design
gi: 108
slug: pacelc-theorem
title: PACELC theorem
---

## 1. What it is

**PACELC** extends the [CAP theorem](0107-cap-theorem.md) to cover normal operation, not just partitions. It reads: **if there is a Partition (P), choose between Availability (A) and Consistency (C); Else (E, i.e. during normal operation with no partition), choose between Latency (L) and Consistency (C).** CAP only tells you what a system does during a network failure; PACELC also tells you what it does the rest of the time, which is most of the time.

## 2. Why & when

CAP alone can make it seem like a system's consistency choice only matters during rare partition events. In reality, many systems trade away some consistency *all the time*, even with a perfectly healthy network, simply to respond faster — because waiting to confirm data is current across multiple nodes takes real time, even when every node is reachable. PACELC makes this second, everyday trade-off explicit. Use it to evaluate a database honestly: ask not just "what does it do during a partition?" (the CAP question) but also "what does it do on a normal Tuesday, with no failures at all?" (the PACELC question) — because the second question is the one that affects your system's behavior nearly all the time.

## 3. Core concept

- **PA/EL systems** (e.g. Cassandra, DynamoDB by default): during a Partition, choose Availability over consistency; Else (normally), choose Latency over consistency — these systems are built for speed and uptime, accepting eventual consistency as their normal-operation default, not just their partition-time fallback.
- **PC/EC systems** (e.g. a traditional relational database configured for synchronous replication, or systems like Spanner): during a Partition, choose Consistency over availability; Else (normally), choose Consistency over latency — these systems always wait for confirmation of correctness, accepting the latency cost as a constant, not an occasional one.
- **Mixed configurations exist:** some systems let you tune the "Else" branch per-operation (e.g. a quorum read/write with adjustable `R`/`W`, as in [quorum reads/writes](0106-quorum-reads-writes-r-w-n.md)), effectively picking EL for some reads and EC for others.
- **The everyday cost of "EC":** choosing consistency over latency during normal operation means every write (or read) pays a coordination cost — a round trip to another node or a quorum check — on every single request, not just during failures.
- **Why this matters for evaluation:** two databases can both be "AP" under CAP, yet behave very differently the other 99.9% of the time (no partition) depending on their Else-branch choice — PACELC is what actually predicts a system's everyday latency profile.

## 4. Diagram

```
                 Is there a network Partition right now?
                    /                          \
                  YES                           NO (Else)
                   |                              |
        Choose: Availability          Choose: Latency
             or Consistency                or Consistency
                   |                              |
         (the CAP question)          (the PACELC-specific question,
                                       applies almost all the time)

  PA/EL example (Cassandra-like): AP during partition, low-latency/
  eventually-consistent normally.

  PC/EC example (Spanner-like): CP during partition, waits for
  cross-node confirmation on every operation even when healthy.
```
*Caption: PACELC adds a second, everyday decision (Latency vs Consistency) to CAP's partition-only decision.*

## 5. Runnable example

**Level 1 — Basic.** Model an EL system: reads return immediately from a local replica, no coordination, even with no partition.

**Level 2 — Model an EC system.** Reads must confirm with another node first, adding latency, even with no partition.

**Level 3 — Compare both under a partition, then during normal operation, to see all four PACELC quadrants.**

```java
// PacelcTheorem.java
import java.util.*;

public class PacelcTheorem {

    static Map<String, Integer> localReplica = new HashMap<>();
    static Map<String, Integer> remoteReplica = new HashMap<>();
    static boolean partitioned = false;

    // EL system: never waits for the remote node, even when healthy. Fast, but can be stale.
    static long elRead(String key) {
        long start = System.nanoTime();
        Integer value = localReplica.get(key); // answered purely locally, no coordination
        long elapsedSimulated = 1; // simulated "cost units": no network round trip needed
        System.out.println("EL read: " + value + " (cost=" + elapsedSimulated + " units, no coordination)");
        return elapsedSimulated;
    }

    // EC system: always confirms with the remote node before answering, even when healthy. Slower, but current.
    static long ecRead(String key) {
        if (partitioned) {
            System.out.println("EC read: cannot reach remote node (partitioned) -> refuses to answer");
            return -1;
        }
        Integer local = localReplica.get(key);
        Integer remote = remoteReplica.get(key); // simulates a round trip to confirm consistency
        long elapsedSimulated = 10; // simulated "cost units": a real network round trip
        System.out.println("EC read: " + Math.max(local, remote) + " (cost=" + elapsedSimulated + " units, confirmed with remote node)");
        return elapsedSimulated;
    }

    public static void main(String[] args) {
        localReplica.put("price", 100);
        remoteReplica.put("price", 100);

        // Level 1 & 2: normal operation (Else branch) - compare EL vs EC cost, both healthy.
        System.out.println("--- normal operation, no partition (the 'Else' branch) ---");
        long elCost = elRead("price");
        long ecCost = ecRead("price");
        System.out.println("EL cost=" + elCost + " vs EC cost=" + ecCost + " -> EL is faster, EC pays a coordination cost even when healthy");

        // Level 3: now simulate a partition and re-run both.
        partitioned = true;
        localReplica.put("price", 120); // a local write the remote side hasn't seen
        System.out.println("--- partition begins (the 'P' branch) ---");
        elRead("price"); // EL: still answers immediately, now visibly stale relative to intent
        ecRead("price"); // EC: refuses, since it cannot confirm with the remote node
        System.out.println("-> EL chose Availability both times (during and outside the partition, consistently PA/EL)");
        System.out.println("-> EC chose Consistency both times (during and outside the partition, consistently PC/EC)");
    }
}
```

**How to run:** save as `PacelcTheorem.java`, then run `java PacelcTheorem.java`.

## 6. Walkthrough

1. With no partition, `elRead` answers purely from `localReplica` at a simulated cost of `1` unit, never contacting `remoteReplica` — this is the "Else: Latency over Consistency" choice, paid on every single read, not only during failures.
2. `ecRead`, still with no partition, reads both `localReplica` and `remoteReplica` and takes their agreement into account, at a simulated cost of `10` units — the "Else: Consistency over Latency" choice, showing a real, constant latency tax for its stronger guarantee.
3. The comparison line makes the everyday difference explicit: even with a perfectly healthy network, the EC system is ten times "slower" in this simulation, purely from its coordination step.
4. Once `partitioned` becomes `true` and a local-only write happens, `elRead` still answers immediately (now with the newer, possibly not-yet-propagated value) — consistent with its PA/EL identity from before.
5. `ecRead` under the partition refuses to answer at all, since it cannot reach `remoteReplica` to confirm — consistent with its PC/EC identity. The same two systems behaved consistently with their PACELC classification in both branches: EL/EC governs the everyday branch, PA/PC governs the partition branch, and a well-designed system's choice tends to be the same "flavor" (favor speed, or favor correctness) in both.

## 7. Gotchas & takeaways

> Gotcha: a system can advertise itself as "highly available" (its CAP answer) while still being noticeably slower than a competitor during completely normal operation, if its PACELC "Else" choice favors consistency over latency. Always ask about both branches — CAP's partition behavior and PACELC's everyday behavior — before choosing a database for a latency-sensitive workload.

- PACELC extends CAP by adding an everyday trade-off: Latency versus Consistency, which applies constantly, not just during a partition.
- PA/EL systems favor speed and availability both during a partition and normally; PC/EC systems favor consistency in both cases, at a constant latency cost.
- Two systems can look identical under CAP alone yet behave very differently on an ordinary day, once their "Else" branch choice is considered.
- Related concepts: [CAP theorem](0107-cap-theorem.md) (the partition-only trade-off PACELC extends), [Quorum reads/writes (R + W > N)](0106-quorum-reads-writes-r-w-n.md) (a tunable mechanism that can shift a system's Else-branch behavior per operation).
