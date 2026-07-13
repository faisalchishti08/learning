---
card: microservices
gi: 326
slug: eventual-consistency
title: "Eventual consistency"
---

## 1. What it is

**Eventual consistency** is a guarantee weaker than the immediate consistency of a single ACID transaction: if no new updates are made to a piece of data, every part of the system that has a copy of it will *eventually* converge to the same, correct value — but there is no guarantee about exactly when. In between an update and that convergence, different parts of the system can legitimately observe different, stale values for the same logical data.

## 2. Why & when

Once a system is split into independently deployed services, each with its own database, and cross-service consistency is achieved through asynchronous mechanisms — events, [sagas](0320-saga-pattern.md), [read models kept in sync via events](0315-keeping-read-models-in-sync-via-events.md) — there is inherently a window of time between a change happening in one place and every other place that cares about it finding out. Trying to eliminate that window entirely means falling back to synchronous cross-service coordination like [2PC](0319-two-phase-commit-2pc-overview-drawbacks.md), which sacrifices availability. Eventual consistency is the deliberate acceptance of that propagation delay in exchange for services that stay independently available even when others are slow or down.

Accept eventual consistency for any data that is replicated or derived across service boundaries — a [reporting database](0316-reporting-analytics-database.md), a [CQRS read model](0314-cqrs-read-models-materialized-views.md), a cached copy of another service's data. It is not appropriate for the single, authoritative "system of record" write inside one service's own database, which should stay strongly consistent locally — eventual consistency is specifically about consistency *between* services, not within one.

## 3. Core concept

A write updates the source of truth immediately and strongly; every other copy learns about that write asynchronously, usually via an event, and updates itself some time later. The gap between "source updated" and "every replica updated" is the **replication lag**, and a correct system either tolerates reading a stale replica during that window or explicitly surfaces the lag so callers can decide whether staleness is acceptable for their use case.

```java
record ReplicaState<T> (T value, java.time.Instant asOf) {} // "asOf" tells the caller HOW stale this copy might be
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Source of truth updates instantly at t=0; three replicas update at t=50ms, t=120ms, and t=300ms respectively -- during that window, different readers see different values for the same data">
  <rect x="20" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="95" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Source of truth: t=0</text>

  <rect x="230" y="70" width="130" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="295" y="90" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Replica A: t=50ms</text>
  <rect x="380" y="70" width="130" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="445" y="90" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Replica B: t=120ms</text>
  <rect x="530" y="70" width="100" height="30" rx="5" fill="#1c2430" stroke="#f0883e"/>
  <text x="580" y="90" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Replica C: t=300ms</text>

  <line x1="95" y1="54" x2="295" y2="70" stroke="#8b949e" marker-end="url(#a326)"/>
  <line x1="95" y1="54" x2="445" y2="70" stroke="#8b949e" marker-end="url(#a326)"/>
  <line x1="95" y1="54" x2="580" y2="70" stroke="#8b949e" marker-end="url(#a326)"/>

  <text x="330" y="140" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">Between t=0 and t=300ms, a reader hitting Replica C sees stale data -- this is the eventual-consistency window.</text>

  <defs><marker id="a326" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every replica converges to the same value eventually, but each does so on its own schedule — the gap in between is real and observable.

## 5. Runnable example

Scenario: a customer's email address, updated at the source and replicated to a read-side cache, first shown with a naive reader that treats the cache as always current, then fixed to expose the staleness window explicitly, and finally extended to let a caller opt into "read-your-own-write" consistency for the one case that actually needs it.

### Level 1 — Basic

```java
// File: NaiveEventualConsistency.java -- source of truth updates
// instantly; the replica updates on a DELAY, but the reader has no idea
// it might be looking at stale data.
import java.util.*;

public class NaiveEventualConsistency {
    static Map<String, String> sourceOfTruth = new HashMap<>();
    static Map<String, String> replica = new HashMap<>(); // updated asynchronously, with lag

    static void updateEmail(String customerId, String newEmail) {
        sourceOfTruth.put(customerId, newEmail); // instant, authoritative
        System.out.println("source: email updated to " + newEmail);
        // replica update happens LATER, asynchronously -- not shown here yet
    }

    public static void main(String[] args) {
        replica.put("cust-1", "old@example.com");
        updateEmail("cust-1", "new@example.com");

        String readFromReplica = replica.get("cust-1"); // reader has NO IDEA this might be stale
        System.out.println("reader sees (from replica): " + readFromReplica + " -- STALE, but presented as if current!");
    }
}
```

How to run: `java NaiveEventualConsistency.java`

`updateEmail` updates `sourceOfTruth` immediately but the code never updates `replica` in this run — standing in for the real propagation delay before an event reaches the replica. A reader querying `replica` gets `"old@example.com"` with no indication it might be out of date, which is the core risk of eventual consistency handled naively: staleness is real but invisible.

### Level 2 — Intermediate

```java
// File: ExplicitStalenessWindow.java -- the replica update is modeled as
// happening asynchronously, and every read from the replica returns a
// timestamp so the caller can SEE how stale the value might be.
import java.util.*;
import java.time.Instant;

public class ExplicitStalenessWindow {
    record TimestampedValue(String value, Instant asOf) {}
    static Map<String, String> sourceOfTruth = new HashMap<>();
    static Map<String, TimestampedValue> replica = new HashMap<>();
    static Queue<Runnable> pendingReplication = new LinkedList<>(); // simulates the async event still in flight

    static void updateEmail(String customerId, String newEmail, Instant now) {
        sourceOfTruth.put(customerId, newEmail);
        System.out.println("source: email updated to " + newEmail + " at " + now);
        pendingReplication.add(() -> replica.put(customerId, new TimestampedValue(newEmail, now)));
    }

    static void runReplicationLag() { // simulates the event actually being delivered and applied, LATER
        Runnable next;
        while ((next = pendingReplication.poll()) != null) next.run();
    }

    public static void main(String[] args) {
        replica.put("cust-1", new TimestampedValue("old@example.com", Instant.parse("2026-07-01T09:00:00Z")));

        updateEmail("cust-1", "new@example.com", Instant.parse("2026-07-01T10:00:00Z"));

        TimestampedValue beforeReplication = replica.get("cust-1");
        System.out.println("reader sees: " + beforeReplication.value() + " (as of " + beforeReplication.asOf()
                + ") -- CLEARLY stale, caller can compare against 'now' and decide if that's acceptable.");

        runReplicationLag();

        TimestampedValue afterReplication = replica.get("cust-1");
        System.out.println("reader sees (after replication lag passes): " + afterReplication.value()
                + " (as of " + afterReplication.asOf() + ") -- now current.");
    }
}
```

How to run: `java ExplicitStalenessWindow.java`

`updateEmail` no longer updates `replica` directly — it enqueues the update into `pendingReplication`, simulating an event still in transit. A read from `replica` immediately after the source update correctly returns the *old* email, but now paired with an `asOf` timestamp the caller can compare against the current time to judge staleness explicitly. Once `runReplicationLag()` drains the queue (simulating the event finally being delivered), the same read returns the new email with an updated timestamp.

### Level 3 — Advanced

```java
// File: ReadYourOwnWrites.java -- one specific caller (the customer who
// JUST changed their own email) needs to see their own change immediately,
// even though the replica generally lags; this is done by routing THAT
// read to the source of truth instead of the replica, without abandoning
// eventual consistency for everyone else.
import java.util.*;
import java.time.Instant;

public class ReadYourOwnWrites {
    record TimestampedValue(String value, Instant asOf) {}
    static Map<String, String> sourceOfTruth = new HashMap<>();
    static Map<String, TimestampedValue> replica = new HashMap<>();
    static Map<String, Instant> lastWrittenBySelf = new HashMap<>(); // tracks recent writes per customer

    static void updateEmail(String customerId, String newEmail, Instant now) {
        sourceOfTruth.put(customerId, newEmail);
        lastWrittenBySelf.put(customerId, now); // remember: THIS customer just wrote, recently
        System.out.println("source: " + customerId + "'s email updated to " + newEmail);
        // replica intentionally NOT updated yet -- still lagging, exactly like a real system
    }

    static String readEmail(String customerId, boolean isTheCustomerWhoJustWrote, Instant now) {
        boolean recentSelfWrite = lastWrittenBySelf.containsKey(customerId)
                && lastWrittenBySelf.get(customerId).isAfter(now.minusSeconds(30)); // "recent" = last 30s

        if (isTheCustomerWhoJustWrote && recentSelfWrite) {
            System.out.println("  routing " + customerId + "'s own read to the SOURCE OF TRUTH (read-your-own-writes)");
            return sourceOfTruth.get(customerId); // bypass the lagging replica for THIS specific case
        }
        System.out.println("  routing read to the (possibly stale) REPLICA -- fine for everyone else");
        return replica.getOrDefault(customerId, new TimestampedValue("(no replica yet)", Instant.EPOCH)).value();
    }

    public static void main(String[] args) {
        replica.put("cust-1", new TimestampedValue("old@example.com", Instant.parse("2026-07-01T09:00:00Z")));
        Instant writeTime = Instant.parse("2026-07-01T10:00:00Z");

        updateEmail("cust-1", "new@example.com", writeTime);

        String customerOwnRead = readEmail("cust-1", true, writeTime.plusSeconds(2)); // the SAME customer, reading right after their own write
        System.out.println("cust-1 (own read, right after writing): sees " + customerOwnRead + " -- CORRECT, sees their own change instantly.");

        String supportAgentRead = readEmail("cust-1", false, writeTime.plusSeconds(2)); // a DIFFERENT actor (e.g. a support agent) looking at the same customer
        System.out.println("support agent (different reader, same instant): sees " + supportAgentRead
                + " -- still stale, and that's ACCEPTABLE for this use case.");
    }
}
```

How to run: `java ReadYourOwnWrites.java`

`readEmail` checks two things: is this read coming from the same customer who just wrote, and did that write happen recently? When both are true, the read is routed to `sourceOfTruth`, guaranteeing the customer sees their own change immediately. When a different actor (like a support agent) reads the same data moments later, the read is routed to the (still-lagging) `replica`, correctly returning the stale value — which is acceptable, since that reader has no expectation of seeing a change that just happened elsewhere.

## 6. Walkthrough

Trace `ReadYourOwnWrites.main` in order. **First**, `replica` starts with `cust-1` at the old email, and `updateEmail("cust-1", "new@example.com", writeTime)` runs: it updates `sourceOfTruth` to the new email and records `lastWrittenBySelf.put("cust-1", writeTime)` — `replica` is deliberately left untouched, standing in for a real propagation delay.

**Next**, `readEmail("cust-1", true, writeTime.plusSeconds(2))` is called, representing the same customer reading two seconds after their own write. Inside, `recentSelfWrite` evaluates to `true` (the write was 2 seconds ago, well within the 30-second window), and `isTheCustomerWhoJustWrote` is `true`, so the `if` branch fires: the method returns `sourceOfTruth.get("cust-1")`, which is the new email — the customer correctly sees their own change.

**Then**, `readEmail("cust-1", false, writeTime.plusSeconds(2))` is called for the same customer's data but from a different actor's perspective (`isTheCustomerWhoJustWrote=false`). Even though `recentSelfWrite` is still `true`, the `if` condition requires *both* flags, so it evaluates to `false` overall — the method falls through to the replica branch and returns `replica.get("cust-1")`'s value, which is still the old email, since the replication lag hasn't been simulated as resolved in this run.

**Finally**, `main` prints both results, showing the customer's own read as correct and current, and the support agent's read as stale but acceptable — the same underlying data, read two different ways, with the routing decision made explicitly based on who is asking and why.

```
updateEmail(cust-1, new-email) -> sourceOfTruth updated; replica NOT updated (lag)
readEmail(cust-1, isSelf=true)  -> recent self-write -> read from SOURCE  -> sees NEW email
readEmail(cust-1, isSelf=false) -> not the writer     -> read from REPLICA -> sees OLD (stale) email
```

## 7. Gotchas & takeaways

> "Eventually" has no upper bound unless you build one. A system that claims eventual consistency but never measures or bounds its replication lag can silently degrade to minutes or hours of staleness under load, with nobody noticing until a user complains that their own change "isn't showing up."

- Eventual consistency means every replica converges to the same value given no further writes, with no fixed deadline for when that happens — always consider and, where possible, measure the replication lag.
- Apply it between services (replicated or derived data); keep strong, immediate consistency for the single authoritative write inside one service's own database.
- "Read-your-own-writes" is a common, targeted fix for the one case that feels most broken to users — seeing their own change lag behind — without abandoning eventual consistency for every other reader.
- This is precisely the consistency model traded for availability whenever a system chooses [BASE over ACID](0327-base-vs-acid.md).
