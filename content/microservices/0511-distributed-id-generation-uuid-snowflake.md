---
card: microservices
gi: 511
slug: distributed-id-generation-uuid-snowflake
title: "Distributed ID generation (UUID, Snowflake)"
---

## 1. What it is

**Distributed ID generation** is how services generate unique identifiers without a single, centralized counter that would become a bottleneck and a single point of failure across many instances. **UUIDs** (typically version 4, randomly generated) give statistically-unique IDs with zero coordination between generators, at the cost of being large, non-sequential, and poor for database index locality. **Snowflake-style IDs** (popularized by Twitter) encode a timestamp, a machine/worker identifier, and a sequence number into a single 64-bit integer, giving roughly time-sortable, compact IDs while still requiring no central coordination between generators.

## 2. Why & when

You need a distributed ID generation strategy the moment more than one instance needs to generate IDs independently, because a single auto-incrementing counter doesn't scale across independent processes:

- **A database's own auto-increment column is a natural single point of coordination**, which is exactly the kind of centralized bottleneck and single point of failure that horizontally-scaled, independently-deployable services try to avoid — every instance would need to coordinate through that one database sequence.
- **UUIDs need zero coordination and are extremely simple to generate anywhere**, at the cost of being 128 bits (versus a 64-bit Snowflake ID or a much smaller integer), being non-sequential (which can hurt database index performance, since new rows insert at random positions rather than appending), and revealing nothing about creation order from the ID alone.
- **Snowflake-style IDs are compact and roughly sortable by creation time**, which is genuinely useful for many real systems (e.g., naturally ordering records by ID without a separate timestamp column, better database index locality for sequential inserts), at the cost of needing each generator to have a unique machine/worker ID assigned to it and needing careful handling of clock behavior.
- **You choose UUIDs for simplicity when ID size and sort order don't matter**, and Snowflake-style IDs when compactness and rough time-ordering are genuinely valuable — many systems use UUIDs by default and only reach for Snowflake-style IDs when a specific, measured need justifies the added complexity of assigning and managing worker IDs.

## 3. Core concept

Think of UUIDs like everyone in a huge crowd independently rolling an enormous number of dice and writing down the result — the chance of two people getting the exact same combination is astronomically small, and nobody needs to coordinate with anyone else to do this. Snowflake-style IDs are more like each person having their own pre-assigned, unique badge number (the worker ID) and simply appending the current time and a running count to it — still requiring zero live coordination between people, but producing a more structured, compact, and naturally time-ordered result, precisely because each person's slice of the ID space is disjoint from everyone else's by construction.

Concretely:

1. **UUID v4**: 128 bits, the vast majority randomly generated — the probability of two independently-generated UUIDs colliding is so low it's treated as effectively zero for practical purposes, requiring no coordination or configuration between generators at all.
2. **Snowflake structure**: typically 41 bits for a millisecond timestamp (relative to a custom epoch), 10 bits for a machine/worker ID (supporting up to 1024 distinct generators), and 12 bits for a per-millisecond sequence number (supporting up to 4096 IDs per generator per millisecond) — all packed into a single 64-bit long.
3. **Uniqueness in Snowflake comes from the combination**: two different generators (different worker IDs) can never collide, since that portion of the ID differs; the same generator, within the same millisecond, uses its sequence counter to stay unique.
4. **Clock behavior matters for Snowflake IDs** — if a generator's system clock moves backward (an NTP correction), naively continuing to generate IDs could produce a timestamp portion that's not properly increasing, requiring explicit handling (waiting, or erroring) to avoid violating the ID's ordering guarantee.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Snowflake ID packs a timestamp, a worker ID, and a sequence number into 64 bits; different worker IDs make collisions across generators impossible by construction">
  <rect x="20" y="60" width="300" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="170" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">41 bits: timestamp (ms)</text>
  <text x="170" y="105" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">roughly time-sortable</text>

  <rect x="330" y="60" width="150" height="60" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="405" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">10 bits: worker ID</text>
  <text x="405" y="105" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">unique per generator</text>

  <rect x="490" y="60" width="150" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="565" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">12 bits: sequence</text>
  <text x="565" y="105" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">per-ms counter</text>
</svg>

Three fields packed into 64 bits, each contributing to uniqueness without any live coordination between generators.

## 5. Runnable example

Scenario: generating IDs across multiple simulated worker instances. We start with a basic UUID generation baseline, extend it to a Snowflake-style ID generator combining timestamp, worker ID, and sequence, then handle the hard case: many rapid IDs generated within the same millisecond by the same worker, which must stay unique via the sequence counter, including correctly rolling over into the next millisecond if the sequence space is exhausted.

### Level 1 — Basic

```java
// File: UuidGenerationBasic.java -- models the SIMPLEST distributed ID
// strategy: UUIDs, generated with ZERO coordination between callers.
import java.util.*;

public class UuidGenerationBasic {
    static String generateId() {
        return UUID.randomUUID().toString();
    }

    public static void main(String[] args) {
        Set<String> generated = new HashSet<>();
        for (int i = 0; i < 5; i++) {
            String id = generateId();
            generated.add(id);
            System.out.println("[generated] " + id);
        }
        System.out.println("[result] " + generated.size() + " unique IDs out of 5 generated, zero coordination needed");
    }
}
```

How to run: `java UuidGenerationBasic.java`

`UUID.randomUUID()` needs no configuration, no assigned identifier, and no coordination with any other generator anywhere — every call independently produces a statistically-unique 128-bit value, which is UUID generation's core simplicity advantage.

### Level 2 — Intermediate

```java
// File: SnowflakeIdBasic.java -- the SAME uniqueness goal, now via a
// SNOWFLAKE-style generator: packing a TIMESTAMP, a WORKER ID, and a
// SEQUENCE number into one compact, roughly TIME-SORTABLE 64-bit long.
public class SnowflakeIdBasic {
    static final long CUSTOM_EPOCH = 1704067200000L; // 2024-01-01, an arbitrary reference point
    static final int WORKER_ID_BITS = 10;
    static final int SEQUENCE_BITS = 12;

    static class SnowflakeGenerator {
        long workerId;
        long lastTimestamp = -1;
        long sequence = 0;

        SnowflakeGenerator(long workerId) { this.workerId = workerId; }

        synchronized long nextId() {
            long timestamp = System.currentTimeMillis();
            if (timestamp == lastTimestamp) {
                sequence = (sequence + 1) & ((1 << SEQUENCE_BITS) - 1); // wraps at 4096
            } else {
                sequence = 0;
            }
            lastTimestamp = timestamp;

            long timestampPart = (timestamp - CUSTOM_EPOCH) << (WORKER_ID_BITS + SEQUENCE_BITS);
            long workerPart = workerId << SEQUENCE_BITS;
            return timestampPart | workerPart | sequence;
        }
    }

    public static void main(String[] args) {
        SnowflakeGenerator worker1 = new SnowflakeGenerator(1);
        SnowflakeGenerator worker7 = new SnowflakeGenerator(7);

        System.out.println("[worker-1] id: " + worker1.nextId());
        System.out.println("[worker-7] id: " + worker7.nextId());
        System.out.println("[worker-1] id: " + worker1.nextId() + " (later, larger -- roughly time-sortable)");
    }
}
```

How to run: `java SnowflakeIdBasic.java`

`nextId` combines the current timestamp (shifted left to make room for the lower bits), the generator's own `workerId` (shifted left past the sequence bits), and a per-millisecond `sequence` counter into one `long` via bitwise OR — two generators with different `workerId` values (`1` and `7`) can never produce a colliding ID, since that bit range differs between them by construction, with no live coordination required between the two generators at all.

### Level 3 — Advanced

```java
// File: SnowflakeSequenceRollover.java -- the SAME generator, now
// handling the PRODUCTION-FLAVORED hard case: MANY IDs requested RAPIDLY
// within the SAME millisecond by the SAME worker, exhausting the
// 12-bit sequence space (4096 values). The generator must correctly
// detect this and ROLL OVER to the next millisecond, rather than wrapping
// the sequence back to zero and silently producing a DUPLICATE ID.
public class SnowflakeSequenceRollover {
    static final long CUSTOM_EPOCH = 1704067200000L;
    static final int WORKER_ID_BITS = 10;
    static final int SEQUENCE_BITS = 12;
    static final long MAX_SEQUENCE = (1L << SEQUENCE_BITS) - 1; // 4095

    static class SnowflakeGenerator {
        long workerId;
        long lastTimestamp = -1;
        long sequence = 0;

        SnowflakeGenerator(long workerId) { this.workerId = workerId; }

        synchronized long nextId() {
            long timestamp = System.currentTimeMillis();

            if (timestamp == lastTimestamp) {
                sequence = (sequence + 1) & MAX_SEQUENCE;
                if (sequence == 0) {
                    // Sequence space EXHAUSTED for this millisecond -- must wait for the NEXT one,
                    // rather than silently wrapping and risking a duplicate ID.
                    System.out.println("[generator] sequence space exhausted for timestamp " + timestamp + " -- WAITING for next millisecond");
                    while (timestamp <= lastTimestamp) {
                        timestamp = System.currentTimeMillis();
                    }
                    System.out.println("[generator] advanced to new timestamp " + timestamp);
                }
            } else {
                sequence = 0;
            }
            lastTimestamp = timestamp;

            long timestampPart = (timestamp - CUSTOM_EPOCH) << (WORKER_ID_BITS + SEQUENCE_BITS);
            long workerPart = workerId << SEQUENCE_BITS;
            return timestampPart | workerPart | sequence;
        }
    }

    public static void main(String[] args) {
        SnowflakeGenerator generator = new SnowflakeGenerator(3);
        java.util.Set<Long> generatedIds = new java.util.HashSet<>();

        // Simulate generating more IDs than the sequence space allows within one millisecond
        // by forcibly setting lastTimestamp and driving sequence near its max.
        long now = System.currentTimeMillis();
        generator.lastTimestamp = now;
        generator.sequence = MAX_SEQUENCE - 2; // start just 2 below the limit

        System.out.println("--- generating IDs right at the edge of the sequence limit ---");
        for (int i = 0; i < 5; i++) {
            long id = generator.nextId();
            boolean isNewId = generatedIds.add(id);
            System.out.println("generated id=" + id + ", unique=" + isNewId);
        }

        System.out.println();
        System.out.println("[result] " + generatedIds.size() + "/5 IDs were unique -- rollover correctly PREVENTED any duplicate");
    }
}
```

How to run: `java SnowflakeSequenceRollover.java`

`generator.sequence` is deliberately set to `MAX_SEQUENCE - 2`, just below its limit, and `lastTimestamp` is pinned to the current millisecond — the next few `nextId()` calls will drive `sequence` to wrap past `MAX_SEQUENCE` back to `0` via the `& MAX_SEQUENCE` mask. When that wraparound to `0` is detected (`if (sequence == 0)`), the generator explicitly busy-waits in a `while` loop until `System.currentTimeMillis()` genuinely advances past `lastTimestamp`, rather than proceeding with a sequence value of `0` at the *same* millisecond it already used `0` for — which would produce an exact duplicate of an earlier ID from this same millisecond.

## 6. Walkthrough

Trace `SnowflakeSequenceRollover.main` in order. **First**, `generator.lastTimestamp` and `generator.sequence` are forcibly set to simulate a generator that's already issued `MAX_SEQUENCE - 2` IDs within the current millisecond, priming the scenario for the sequence space to run out within just a few more calls.

**Next**, the loop's first two `nextId()` calls run normally: `timestamp == lastTimestamp` is `true` (still the same millisecond), so `sequence` increments via the mask, reaching `MAX_SEQUENCE - 1` then `MAX_SEQUENCE` — neither hits the `sequence == 0` rollover condition yet, so both return distinct, valid IDs.

**Then**, the third call runs: `sequence = (sequence + 1) & MAX_SEQUENCE` computes `(MAX_SEQUENCE + 1) & MAX_SEQUENCE`, which wraps around to exactly `0` — the sequence space for this millisecond has been fully exhausted. The `if (sequence == 0)` check is now `true`, so the generator prints its exhaustion message and enters the `while (timestamp <= lastTimestamp)` busy-wait loop, repeatedly calling `System.currentTimeMillis()` until it returns a genuinely later value.

**After that**, once real time advances to a new millisecond, the `while` loop exits, the generator prints confirmation of the new timestamp, `lastTimestamp` is updated to this new value, and the ID is constructed using `sequence = 0` — but this time, `0` at a *new*, later timestamp, which is a completely different bit pattern than `0` at the *original* timestamp, so no duplicate results.

**Finally**, the loop's remaining calls continue from this new millisecond, and `main`'s final check confirms all five generated IDs landed in `generatedIds` as genuinely distinct values — `generatedIds.add(id)` returning `true` for every single one — demonstrating that the explicit rollover-and-wait logic correctly prevented what would otherwise have been a real, silent ID collision the moment the sequence counter wrapped back to zero within the same millisecond.

```
--- generating IDs right at the edge of the sequence limit ---
generated id=..., unique=true
generated id=..., unique=true
[generator] sequence space exhausted for timestamp ... -- WAITING for next millisecond
[generator] advanced to new timestamp ...
generated id=..., unique=true
generated id=..., unique=true
generated id=..., unique=true

[result] 5/5 IDs were unique -- rollover correctly PREVENTED any duplicate
```

(Exact numeric ID values vary by run since they're timestamp-dependent, but the count of unique IDs and the rollover message are deterministic given this exact scenario.)

## 7. Gotchas & takeaways

> A Snowflake-style generator that lets its sequence counter silently wrap back to zero *without* also advancing to a new timestamp produces a genuine, silent duplicate ID — indistinguishable from a real collision, and far more insidious than an obvious crash, since it can go unnoticed until two records with the "same" unique ID cause a subtle downstream bug. The explicit wait-for-next-millisecond logic is not optional correctness detail; it's what actually delivers the uniqueness guarantee under sustained high throughput.
- Assign worker IDs carefully and durably in any real deployment — two Snowflake generators accidentally sharing the same worker ID (a configuration mistake, or a naive "derive from hostname" approach that collides) reintroduces exactly the collision risk the worker-ID bits exist to prevent.
- Clock behavior matters for Snowflake-style generators — a system clock that jumps backward (an NTP correction) can violate the timestamp-ordering assumption; production-grade implementations typically detect and explicitly handle (wait out, or refuse to generate IDs during) backward clock jumps.
- UUIDs remain the simpler, lower-risk default for most systems — reach for Snowflake-style IDs specifically when compactness (64 bits versus 128) or rough time-ordering (better database index locality for sequential inserts) is a measured, real need, not a default assumption.
- Both strategies share the same underlying principle as [distributed locks](0508-distributed-locks.md) and [leader election](0509-leader-election.md): achieving a correctness guarantee across independent, uncoordinated processes by construction (disjoint ID spaces, atomic compare-and-set) rather than through live, synchronous coordination between them.
