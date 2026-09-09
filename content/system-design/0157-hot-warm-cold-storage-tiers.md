---
card: system-design
gi: 157
slug: hot-warm-cold-storage-tiers
title: Hot / warm / cold storage tiers
---

## 1. What it is

**Storage tiering** places data on different classes of storage based on how often it is accessed. **Hot** storage is fast and expensive per gigabyte, for data read constantly. **Warm** storage is a middle ground, for data read occasionally. **Cold** (or archive) storage is slow to retrieve but very cheap per gigabyte, for data rarely read at all, such as year-old logs kept only for compliance. Data typically moves from hot to warm to cold automatically as it ages and is accessed less.

## 2. Why & when

Storing every byte you have ever written on the fastest, most expensive storage wastes money on data nobody is actually reading anymore. Storing everything on the cheapest, slowest storage makes frequently-accessed data painfully slow. Tiering solves this by matching each piece of data's storage cost to its actual access pattern, moving data down through tiers automatically as it ages, using a **lifecycle policy** (e.g. "after 30 days with no reads, move to warm; after 90 days, move to cold"). Use tiering for any dataset where most data quickly becomes rarely accessed but must still be kept — logs, backups, historical records, media libraries.

## 3. Core concept

- **Hot tier:** low latency, high cost per gigabyte; used for data accessed frequently, such as this week's application logs or the current month's transaction records.
- **Warm tier:** moderate latency, moderate cost; used for data accessed occasionally, such as last quarter's reports.
- **Cold/archive tier:** high latency (sometimes minutes to hours to retrieve, e.g. tape or archive-class cloud storage), very low cost; used for data almost never read, kept mainly for compliance or disaster recovery.
- **Lifecycle policy:** an automated rule that moves an object from one tier to the next based on its age or time since last access, so nobody has to move data manually.
- **Retrieval cost and latency tradeoff:** moving data to a colder tier saves money on storage but increases the cost and delay of reading it back — this tradeoff must match the data's real likelihood of being read again.

## 4. Diagram

```
   object age / last-access time
   0 days -------- 30 days -------- 90 days -------- 365+ days
      |                |                |                 |
     HOT              WARM            COLD            deleted/
   (fast, $$$)      (medium, $$)   (slow, $)         archived
      |                |                |
      +---- lifecycle policy moves the object down a tier automatically ---->

   read request for an old, cold object:
   client -> storage system -> "restoring from cold tier, ready in ~4 hours"
```
*Caption: a lifecycle policy automatically moves data to cheaper, slower tiers as it ages, trading retrieval speed for storage cost.*

## 5. Runnable example

**Level 1 — Basic.** Assign a tier to each object based on its age.

**Level 2 — Automated lifecycle transitions.** Simulate time passing and move objects between tiers according to a policy.

**Level 3 — Simulate retrieval cost/latency by tier.** Reading a cold object takes far longer (and costs more) than reading a hot one.

```java
// StorageTieringDemo.java
import java.util.*;

public class StorageTieringDemo {

    enum Tier { HOT, WARM, COLD }

    static class TieredObject {
        final String key;
        int ageInDays;
        Tier tier;
        TieredObject(String key, int ageInDays, Tier tier) {
            this.key = key;
            this.ageInDays = ageInDays;
            this.tier = tier;
        }
    }

    // Level 2: the lifecycle policy - moves an object down a tier based on its age.
    static void applyLifecyclePolicy(TieredObject obj) {
        Tier newTier;
        if (obj.ageInDays < 30) newTier = Tier.HOT;
        else if (obj.ageInDays < 90) newTier = Tier.WARM;
        else newTier = Tier.COLD;

        if (newTier != obj.tier) {
            System.out.println("  " + obj.key + " (age " + obj.ageInDays + "d): " + obj.tier + " -> " + newTier);
            obj.tier = newTier;
        }
    }

    // Level 3: retrieval latency and relative cost differ sharply by tier.
    static String readObject(TieredObject obj) {
        switch (obj.tier) {
            case HOT:  return "read from " + obj.key + " in ~5ms (hot tier, cost: $$$)";
            case WARM: return "read from " + obj.key + " in ~200ms (warm tier, cost: $$)";
            case COLD: return "RESTORE REQUESTED for " + obj.key + " - ready in ~4 hours (cold tier, cost: $)";
            default: throw new IllegalStateException();
        }
    }

    public static void main(String[] args) {
        // Level 1: objects starting in the hot tier, at different ages.
        List<TieredObject> objects = new ArrayList<>(List.of(
            new TieredObject("logs/2024-06-01.log", 5, Tier.HOT),
            new TieredObject("logs/2024-04-01.log", 60, Tier.HOT),
            new TieredObject("logs/2023-01-01.log", 400, Tier.HOT)
        ));

        System.out.println("applying lifecycle policy based on object age:");
        for (TieredObject obj : objects) applyLifecyclePolicy(obj);

        System.out.println("reading each object now that tiers have been applied:");
        for (TieredObject obj : objects) {
            System.out.println("  " + readObject(obj));
        }
    }
}
```

**How to run:** save as `StorageTieringDemo.java`, then run `java StorageTieringDemo.java`.

## 6. Walkthrough

1. Three objects start out marked as `HOT`, but with very different `ageInDays` values: 5, 60, and 400 days old.
2. `applyLifecyclePolicy` is run for each; for the 5-day-old log, `ageInDays < 30` is true, so `newTier = HOT` matches its current tier, and nothing is printed since `newTier != obj.tier` is false.
3. For the 60-day-old log, `ageInDays < 30` is false but `ageInDays < 90` is true, so `newTier = WARM`; this differs from its current `HOT` tier, so the transition is printed and `obj.tier` updates to `WARM`.
4. For the 400-day-old log, neither `< 30` nor `< 90` holds, so `newTier = COLD`; again this differs from the stored `HOT` tier, so the transition prints and the object moves straight to `COLD` (this simplified policy does not require passing through `WARM` first).
5. The final read loop calls `readObject` on each; the 5-day-old (still `HOT`) log reads in "~5ms", the 60-day-old (`WARM`) log reads in "~200ms", and the 400-day-old (`COLD`) log prints a "RESTORE REQUESTED... ready in ~4 hours" message instead of an immediate read — showing that reading cold data is not just slower but fundamentally a different, delayed operation, not a simple synchronous read.

## 7. Gotchas & takeaways

> Gotcha: an application that assumes every read is fast and synchronous will break (or hang) when it tries to read an object that has been moved to a cold/archive tier, since cold reads often require an explicit "restore" step and a real delay of hours, not milliseconds — always check an object's tier, or design for an asynchronous restore-then-read flow, before reading data that might be archived.

- Storage tiering matches each object's storage cost to how often it is actually read, moving data to cheaper tiers automatically as it ages.
- A lifecycle policy is what makes this automatic — nobody has to manually decide when to move each object.
- Colder tiers trade retrieval speed for a much lower storage cost, and cold reads can become an asynchronous, hours-long operation rather than an instant one.
- Related concepts: [Object / blob storage (S3-like)](0152-object-blob-storage-s3-like.md) (where tiering is most commonly applied), [Data lake vs data warehouse](0156-data-lake-vs-data-warehouse.md) (a data lake's raw history is a classic candidate for tiering), [Cache-aside (lazy loading)](0045-cache-aside-lazy-loading.md) (the opposite end of the spectrum: keeping the hottest data even faster than the hot storage tier itself).
