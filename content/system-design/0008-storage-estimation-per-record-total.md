---
card: system-design
gi: 8
slug: storage-estimation-per-record-total
title: Storage estimation (per-record & total)
---

## 1. What it is

**Storage estimation** is the calculation of how much disk space a system needs, done by finding the size of one record, then multiplying by how many records the system will hold over a chosen time period — often five years, a common interview horizon. It turns "we store tweets" into a concrete number like "2.5 terabytes over five years", which tells you whether one database server is enough or whether you need to shard.

Think of it like estimating how many boxes you need to move house: measure one typical box's volume, count how many boxes you have, and multiply — rather than guessing "a lot" or "a truck's worth".

## 2. Why & when

Storage estimates decide real architecture choices: whether data fits on a single machine's disk, whether you need to shard across many machines, and roughly what your infrastructure will cost. You compute this right after QPS estimation, using the same daily-active-user and requests-per-day numbers you already derived.

## 3. Core concept

**The estimation method, step by step:**

1. **Estimate the size of one record.** Add up every field: for a tweet, maybe 280 bytes of text (at 1 byte per character, using UTF-8 approximation) plus roughly 100-200 bytes of metadata (user ID, timestamp, tweet ID, like-count). Round to a clean number, e.g. **~500 bytes per record**.
2. **Estimate how many records are created per day.** This reuses the daily-requests number from QPS estimation, or a separate write-rate estimate if only some requests create a record.
3. **Compute daily storage:** `records per day × bytes per record`.
4. **Compute storage over your time horizon** (5 years is a standard interview default): `daily storage × 365 × 5`.
5. **Add a safety margin** for indexes, replication, and metadata overhead — a common rule of thumb is to add 20-30% on top of the raw data size, since databases store more than just your fields (indexes, replica copies).

## 4. Diagram

```
 bytes/record  x  records/day  =  bytes/day
                                       |
                                       v (x 365 x 5 years)
                                       |
                              raw storage over 5 years
                                       |
                                       v (x 1.2-1.3, for indexes/replication)
                                       |
                              TOTAL STORAGE NEEDED
```
*Caption: per-record size times daily record count gives daily storage; scale by time horizon, then add overhead for indexes and replicas.*

## 5. Runnable example

### Artifact: a Java storage calculator with an overhead margin

```java
public class StorageEstimator {

    static long dailyBytes(long recordsPerDay, long bytesPerRecord) {
        return recordsPerDay * bytesPerRecord;
    }

    static long totalBytesOverYears(long dailyBytes, int years) {
        return dailyBytes * 365L * years;
    }

    static long withOverhead(long rawBytes, double overheadFraction) {
        return (long) (rawBytes * (1.0 + overheadFraction));
    }

    public static void main(String[] args) {
        long bytesPerRecord = 500L;          // text + metadata for one tweet
        long recordsPerDay = 100_000_000L;   // 100 million new tweets/day
        int years = 5;
        double overhead = 0.25;              // 25% for indexes and replication

        long daily = dailyBytes(recordsPerDay, bytesPerRecord);
        long rawFiveYear = totalBytesOverYears(daily, years);
        long withMargin = withOverhead(rawFiveYear, overhead);

        System.out.println("Daily storage (bytes): " + daily);
        System.out.printf("Daily storage: %.2f GB%n", daily / 1e9);
        System.out.printf("Raw storage over %d years: %.2f TB%n", years, rawFiveYear / 1e12);
        System.out.printf("With %.0f%% overhead: %.2f TB%n", overhead * 100, withMargin / 1e12);
    }
}
```

**How to run:** save as `StorageEstimator.java`, run `java StorageEstimator.java` (JDK 17+).

## 6. Walkthrough

1. `dailyBytes` multiplies the number of new records created per day by the size of one record, giving total bytes written in a single day.
2. `totalBytesOverYears` scales that daily figure up to a multi-year horizon by multiplying by 365 days and the number of years.
3. `withOverhead` adds a percentage on top of the raw figure, accounting for database indexes and replica copies that store more than just the raw fields.
4. `main` runs the scenario: 500-byte tweets, 100 million new tweets a day, over 5 years, with 25% overhead.
5. Output:
```
Daily storage (bytes): 50000000000
Daily storage: 50.00 GB
Raw storage over 5 years: 91.25 TB
With 25% overhead: 114.06 TB
```
6. Spoken in an interview: "Each tweet is about 500 bytes with metadata. At 100 million tweets a day, that's 50 GB a day. Over five years, roughly 91 terabytes raw. Adding 25% for indexes and replication, call it about 115 terabytes total." That single sentence is the entire estimate, and it directly tells you this will not fit on one machine, so you need to shard the data.

## 7. Gotchas & takeaways

> **Gotcha:** forgetting metadata. Engineers often estimate only the "obvious" field (like tweet text) and forget IDs, timestamps, foreign keys, and indexes, which can easily double or triple the true per-record size.

- Always break a record's size into its actual fields before estimating; do not guess a single number out of thin air.
- Add an overhead margin (20-30% is a reasonable default) for indexes and replication; raw field size understates real storage needs.
- A result in the terabytes or petabytes range is your signal that you need to talk about sharding or partitioning later in the design.
