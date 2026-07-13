---
card: microservices
gi: 329
slug: pacelc-theorem
title: "PACELC theorem"
---

## 1. What it is

**PACELC** extends the [CAP theorem](0328-cap-theorem.md) by pointing out that CAP only describes the tradeoff during a network **P**artition (choose **A**vailability or **C**onsistency) — but it says nothing about what happens the rest of the time, when there is no partition at all. PACELC adds that second half: **E**lse (when there is no partition), a system must still choose between **L**atency (respond fast) and **C**onsistency (wait to confirm agreement across replicas before responding). Read as a sentence: "if Partitioned, choose Availability or Consistency; Else, choose Latency or Consistency."

## 2. Why & when

CAP theorem is often used to justify a system's design choices, but it technically only applies during the rare moments a partition is actually happening — most of the time, a distributed data system with replicas is running normally, with no partition, and still has to decide: does a write wait for confirmation from every (or a quorum of) replica before returning, or does it return as soon as it's durable on one node, accepting that reads from other replicas might briefly lag behind? PACELC makes this everyday tradeoff explicit, and it's often the more practically relevant half, since a well-run system spends far more time in this "no partition" state than in an active partition.

Use PACELC when evaluating or configuring a replicated data store's normal-operation behavior — its replication factor, write acknowledgment settings (e.g., "wait for all replicas" versus "wait for one"), and read consistency level. This decision shapes every single request's latency and consistency, not just the rare partition-handling path that CAP addresses.

## 3. Core concept

Picture a write to a primary node with two replicas. A **PC/EC** system (consistency in both halves) waits for the write to be confirmed on all (or a quorum of) replicas before acknowledging it, and reads always return the latest value — at the cost of higher latency on every write and read. A **PA/EL** system (availability under partition, latency otherwise) acknowledges the write as soon as it lands on the primary, returning fast, and lets replicas catch up asynchronously — at the cost of a read hitting a lagging replica and seeing a stale value, even with no partition in sight.

```java
enum ElseChoice { LATENCY, CONSISTENCY } // the choice made on EVERY normal-operation write/read, no partition needed
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Decision tree: is there a partition? If yes, choose Availability or Consistency (CAP). If no (Else), choose Latency or Consistency (the L and C of PACELC)">
  <rect x="250" y="10" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="32" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Partition happening?</text>

  <line x1="280" y1="44" x2="130" y2="80" stroke="#8b949e" marker-end="url(#a329)"/>
  <text x="180" y="65" fill="#8b949e" font-size="9" font-family="sans-serif">YES</text>
  <rect x="30" y="80" width="200" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="130" y="104" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">CAP: Availability vs Consistency</text>

  <line x1="360" y1="44" x2="510" y2="80" stroke="#8b949e" marker-end="url(#a329)"/>
  <text x="460" y="65" fill="#8b949e" font-size="9" font-family="sans-serif">ELSE (no)</text>
  <rect x="410" y="80" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="510" y="104" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">PACELC: Latency vs Consistency</text>

  <text x="320" y="160" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">The Else branch applies almost ALL the time -- most systems are NOT partitioned right now.</text>

  <defs><marker id="a329" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

PACELC's "Else" branch — latency versus consistency with no partition — governs day-to-day behavior far more often than CAP's partition branch.

## 5. Runnable example

Scenario: a replicated order-status store, first shown as consistency-favoring (waits for all replicas, every read/write is slow but always correct), then rebuilt to favor latency (acknowledges fast, replicas catch up asynchronously), and finally extended to let the caller choose per-request, since not every request has the same priority.

### Level 1 — Basic

```java
// File: ConsistencyFavoringWrite.java -- every write WAITS for all
// replicas to confirm before returning; slow, but always fully consistent.
import java.util.*;

public class ConsistencyFavoringWrite {
    static Map<String, String> primary = new HashMap<>();
    static List<Map<String, String>> replicas = List.of(new HashMap<>(), new HashMap<>());

    static void write(String key, String value) throws InterruptedException {
        primary.put(key, value);
        for (Map<String, String> replica : replicas) {
            Thread.sleep(50); // simulates real network latency to EACH replica
            replica.put(key, value);
        }
        System.out.println("write acknowledged only AFTER all replicas confirmed (slow, fully consistent)");
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        write("order-1-status", "SHIPPED");
        System.out.println("write took ~" + (System.currentTimeMillis() - start) + "ms -- every replica is GUARANTEED current now.");
    }
}
```

How to run: `java ConsistencyFavoringWrite.java`

`write` deliberately waits (`Thread.sleep(50)`, standing in for real network latency) for each replica in turn before returning, guaranteeing that by the time the caller gets an acknowledgment, every replica genuinely has the new value — favoring consistency (the "C" in PACELC's Else branch) at the direct cost of write latency.

### Level 2 — Intermediate

```java
// File: LatencyFavoringWrite.java -- the write acknowledges as soon as
// the PRIMARY has it; replicas catch up ASYNCHRONOUSLY, so a read hitting
// a replica right after the write can see a stale value -- with NO
// partition involved at all.
import java.util.*;

public class LatencyFavoringWrite {
    static Map<String, String> primary = new HashMap<>();
    static Map<String, String> replica = new HashMap<>();
    static Queue<Runnable> pendingReplication = new LinkedList<>();

    static void write(String key, String value) {
        primary.put(key, value); // acknowledge IMMEDIATELY, don't wait for the replica
        pendingReplication.add(() -> replica.put(key, value));
        System.out.println("write acknowledged INSTANTLY, from the primary only (fast, but replica now lags)");
    }

    static void catchUpReplicas() { // runs later, asynchronously
        Runnable next;
        while ((next = pendingReplication.poll()) != null) next.run();
    }

    public static void main(String[] args) {
        write("order-1-status", "SHIPPED");

        String readFromReplica = replica.getOrDefault("order-1-status", "(not yet replicated)");
        System.out.println("read from replica IMMEDIATELY after write: " + readFromReplica + " -- STALE, no partition needed to cause this!");

        catchUpReplicas();
        System.out.println("read from replica after catch-up: " + replica.get("order-1-status"));
    }
}
```

How to run: `java LatencyFavoringWrite.java`

`write` returns as soon as `primary` is updated, without waiting on `replica` at all — favoring low latency. A read immediately from `replica` correctly shows `"(not yet replicated)"`, illustrating the Else-branch tradeoff: this staleness happened purely because the system chose fast acknowledgment over waiting for replication, with no network partition involved anywhere.

### Level 3 — Advanced

```java
// File: PerRequestPacelcChoice.java -- the SAME store lets each caller
// pick its own point on the latency-vs-consistency spectrum: a payment
// confirmation write WAITS for the replica (favors C), while a low-stakes
// "last seen" timestamp update does NOT (favors L).
import java.util.*;

public class PerRequestPacelcChoice {
    static Map<String, String> primary = new HashMap<>();
    static Map<String, String> replica = new HashMap<>();

    static void writeFavoringConsistency(String key, String value) throws InterruptedException {
        primary.put(key, value);
        Thread.sleep(50); // WAIT for replica -- this caller needs it durable everywhere before proceeding
        replica.put(key, value);
        System.out.println("writeFavoringConsistency(" + key + "): acknowledged only after replica confirmed too");
    }

    static void writeFavoringLatency(String key, String value) {
        primary.put(key, value); // acknowledge immediately; replica updated async, not shown here
        System.out.println("writeFavoringLatency(" + key + "): acknowledged instantly from primary only");
    }

    public static void main(String[] args) throws InterruptedException {
        // Payment confirmation: correctness matters more than speed here.
        long t1 = System.currentTimeMillis();
        writeFavoringConsistency("payment-status", "CONFIRMED");
        System.out.println("  took ~" + (System.currentTimeMillis() - t1) + "ms, replica GUARANTEED current");

        // "Last seen" timestamp: speed matters far more than a few seconds of staleness.
        long t2 = System.currentTimeMillis();
        writeFavoringLatency("last-seen-timestamp", "2026-07-13T10:00:00Z");
        System.out.println("  took ~" + (System.currentTimeMillis() - t2) + "ms, replica may briefly lag -- ACCEPTABLE for this data");
    }
}
```

How to run: `java PerRequestPacelcChoice.java`

`writeFavoringConsistency` is used for the payment status, deliberately paying the latency cost of waiting for the replica to confirm, because a stale payment status could mislead downstream logic. `writeFavoringLatency` is used for the "last seen" timestamp, deliberately skipping that wait, because nothing bad happens if that value briefly lags — the point being that the L-versus-C choice from PACELC's Else branch is made *per operation*, based on what each piece of data actually needs, exactly as [CAP theorem](0328-cap-theorem.md)'s C-versus-A choice was made per operation under partition.

## 6. Walkthrough

Trace `PerRequestPacelcChoice.main` in order. **First**, `writeFavoringConsistency("payment-status", "CONFIRMED")` runs: it updates `primary` immediately, then calls `Thread.sleep(50)` to simulate the real latency of confirming with the replica, then updates `replica`, and only after all of that does it print its acknowledgment message — the caller experiences roughly 50ms of latency in exchange for a guarantee that the replica is current the instant the call returns.

**Next**, `main` prints the elapsed time for that call, which reflects the deliberate wait.

**Then**, `writeFavoringLatency("last-seen-timestamp", "2026-07-13T10:00:00Z")` runs: it updates only `primary` and returns immediately, with no sleep and no wait on `replica` at all — the caller gets an instant acknowledgment, but `replica` has not been told about this write in this code path (a real system would replicate it asynchronously moments later).

**Finally**, `main` prints the elapsed time for the second call, which is effectively zero compared to the first — directly demonstrating the tradeoff: the consistency-favoring write took meaningfully longer in exchange for a stronger guarantee, while the latency-favoring write returned instantly at the cost of the replica temporarily not reflecting the new value.

```
writeFavoringConsistency(payment-status)   -> primary + WAIT + replica  -> ~50ms, replica CURRENT
writeFavoringLatency(last-seen-timestamp)  -> primary only, NO wait     -> ~0ms,  replica LAGS (async)
```

## 7. Gotchas & takeaways

> Teams sometimes cite CAP theorem to justify an eventually-consistent design, when the actual cause of the staleness they're seeing has nothing to do with a network partition — it's the Else branch of PACELC, a deliberate (or accidental) latency-versus-consistency choice made during completely normal operation. Naming the right half of PACELC matters for diagnosing where a staleness issue actually comes from.

- PACELC's "Else" branch — latency versus consistency with no partition — governs the vast majority of a distributed system's actual request-handling behavior.
- A replicated store's write-acknowledgment setting (wait for all replicas vs. wait for one) is exactly this L-versus-C choice, configured explicitly in most production databases.
- Different operations on the same system can and should make different choices, based on how costly staleness would be for that specific piece of data.
- See [CAP theorem](0328-cap-theorem.md) for the partition-specific half of this same overall reasoning.
