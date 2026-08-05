---
card: system-design
gi: 80
slug: base-vs-acid
title: BASE vs ACID
---

## 1. What it is

**ACID** (Atomicity, Consistency, Isolation, Durability) is the strong-consistency guarantee traditional relational databases offer, covered earlier in this section. **BASE** — **Basically Available, Soft state, Eventually consistent** — describes the looser guarantee many NoSQL databases offer instead: the system stays available even during a failure, its state may be temporarily inconsistent, but it converges to a consistent state eventually, given enough time with no new writes.

## 2. Why & when

ACID and BASE represent two different answers to a hard constraint: in a distributed system, during a network partition, you generally cannot have both perfect consistency and full availability at the same time (this is the essence of the CAP theorem). ACID systems tend to favor consistency, sometimes rejecting a write or a read rather than risk showing inconsistent data. BASE systems favor availability, accepting writes and serving reads even when nodes cannot fully coordinate, and reconciling the differences afterward. Choose based on what a wrong or delayed answer actually costs you: a bank balance usually needs ACID; a social media "like count" usually tolerates BASE.

## 3. Core concept

**Basically available:** the system prioritizes responding to every request, even if some nodes cannot currently communicate with each other — a request is served by whichever nodes are reachable, rather than failing outright because full consistency cannot currently be guaranteed.

**Soft state:** the system's state can change over time even without new input, as replicas reconcile differences with each other in the background — unlike ACID's strict guarantee that a committed value stays exactly as committed until explicitly changed again.

**Eventually consistent:** if no new writes happen, all replicas will converge to the same value — eventually. During the window before that convergence, different replicas (or different reads) can return different, temporarily conflicting answers for the same key.

**A concrete example — a "like" counter:** two replicas of a like counter both accept a concurrent increment while briefly unable to communicate. Each replica's local count is briefly inconsistent with the other. Once they can communicate again, they reconcile (often by simply merging both increments), and the count is eventually correct — a brief window of undercounting is a completely acceptable cost for a like counter, and BASE's higher availability during the partition is a clear win.

## 4. Diagram

```
ACID (favors consistency; may sacrifice availability during a partition):
  Node A <--partitioned, cannot reach--> Node B
  Write request arrives at Node A -> Node A cannot confirm consistency with B -> REJECTS the write

BASE (favors availability; accepts a temporary inconsistency window):
  Node A <--partitioned, cannot reach--> Node B
  Write request arrives at Node A -> Node A ACCEPTS it locally (basically available, soft state)
  Write request arrives at Node B -> Node B ALSO accepts its own version locally
  ... partition heals ...
  Node A and Node B reconcile their differences -> EVENTUALLY consistent
```
*Caption: during a network partition, ACID-leaning systems can refuse a request to stay consistent; BASE-leaning systems accept the request and reconcile differences once communication is restored.*

## 5. Runnable example

**Level 1 — Basic.** An ACID-style store that rejects a write when it cannot confirm consistency with a "replica."

**Level 2 — BASE-style store.** The same scenario, but the store accepts the write locally regardless, marking it for later reconciliation.

**Level 3 — Eventual consistency.** Simulate the partition healing and the two replicas reconciling to the same final value.

```java
// BaseVsAcid.java
import java.util.*;

public class BaseVsAcid {

    // Level 1: ACID-style - refuses to accept a write if it cannot confirm the other replica agrees.
    static Integer acidCounter = 0;
    static boolean acidWrite(int delta, boolean replicaReachable) {
        if (!replicaReachable) {
            System.out.println("  ACID: replica unreachable, cannot guarantee consistency -> REJECTING write");
            return false;
        }
        acidCounter += delta;
        return true;
    }

    // Level 2 & 3: BASE-style - two replicas, each accepts writes locally even when partitioned.
    static int replicaA = 0;
    static int replicaB = 0;
    static final List<Integer> pendingReconciliation = new ArrayList<>();

    static void baseWriteToA(int delta, boolean partitioned) {
        replicaA += delta; // basically available: accepted locally regardless
        if (partitioned) {
            pendingReconciliation.add(delta); // soft state: this write has not yet reached B
            System.out.println("  BASE: replica A accepted +" + delta + " locally while partitioned (A=" + replicaA + ", B=" + replicaB + ")");
        } else {
            replicaB += delta; // not partitioned: propagates immediately
        }
    }

    static void reconcile() {
        System.out.println("  partition healed - reconciling " + pendingReconciliation.size() + " pending write(s) to replica B");
        for (int delta : pendingReconciliation) {
            replicaB += delta; // eventually consistent: B catches up
        }
        pendingReconciliation.clear();
    }

    public static void main(String[] args) {
        System.out.println("ACID counter, replica unreachable:");
        acidWrite(1, false); // rejected: availability sacrificed for consistency
        System.out.println("acidCounter after rejected write: " + acidCounter);

        System.out.println("ACID counter, replica reachable:");
        acidWrite(1, true); // accepted, both sides guaranteed in sync
        System.out.println("acidCounter after accepted write: " + acidCounter);

        System.out.println();
        System.out.println("BASE counters, partition in effect:");
        baseWriteToA(1, true);
        baseWriteToA(1, true);
        System.out.println("  DURING partition: replicaA=" + replicaA + ", replicaB=" + replicaB + "  <- temporarily inconsistent");

        reconcile();
        System.out.println("  AFTER reconciliation: replicaA=" + replicaA + ", replicaB=" + replicaB + "  <- eventually consistent");
    }
}
```

**How to run:** save as `BaseVsAcid.java`, then run `java BaseVsAcid.java`.

## 6. Walkthrough

1. `acidWrite(1, false)` sees `replicaReachable = false` and refuses the write entirely, printing a rejection — modeling an ACID-leaning system choosing consistency over availability during a partition; `acidCounter` stays at `0`.
2. `acidWrite(1, true)` succeeds because the replica is reachable, so consistency can be guaranteed; `acidCounter` becomes `1`.
3. `baseWriteToA(1, true)` (called twice) accepts both writes into `replicaA` immediately regardless of the partition, but because `partitioned = true`, they are queued in `pendingReconciliation` rather than reaching `replicaB` right away.
4. Printing both replicas mid-partition shows `replicaA=2, replicaB=0` — a real, visible inconsistency between the two replicas, which BASE explicitly accepts as the cost of staying available.
5. `reconcile()` applies the queued deltas to `replicaB`, bringing it to `2` as well — both replicas now agree, demonstrating the "eventually consistent" guarantee: no new writes happened, and given enough time (here, until reconciliation runs), the replicas converged to the same value.

## 7. Gotchas & takeaways

> Gotcha: "eventually" in eventual consistency has no fixed bound — under sustained partitioning or heavy load, "eventually" could be much longer than expected; applications relying on BASE guarantees must be explicitly designed to tolerate reading a stale or temporarily conflicting value, not just assume convergence happens fast.

- ACID and BASE are opposite answers to the same unavoidable trade-off during a network partition: reject the request to stay consistent, or accept it and reconcile later to stay available.
- Choose based on the real cost of temporary inconsistency for that specific data — not as a blanket choice for an entire system; many real systems use ACID for some data and BASE for other data (polyglot persistence, covered later in this section).
- Related concepts: [Isolation levels (read-committed, repeatable-read, serializable)](0069-isolation-levels-read-committed-repeatable-read-serializable.md) (ACID's consistency spectrum, in more depth), [Polyglot persistence in one system](0084-polyglot-persistence-in-one-system.md) (deliberately combining ACID and BASE stores for different data in the same system).
