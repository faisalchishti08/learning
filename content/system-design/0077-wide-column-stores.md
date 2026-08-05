---
card: system-design
gi: 77
slug: wide-column-stores
title: Wide-column stores
---

## 1. What it is

A **wide-column store** organizes data into rows identified by a key, where each row can have a different, dynamic set of columns, grouped into **column families**. Physically, data is stored and read column-by-column within a row, rather than row-by-row like a relational table. Apache Cassandra and HBase are the leading examples.

## 2. Why & when

Wide-column stores are built specifically for very high write throughput and horizontal scale across many nodes, at the cost of the rich querying and strict consistency a relational database offers. Use one when you need to ingest massive, continuous write volume (sensor data, event logs, time-series metrics, activity feeds) distributed across a cluster, and your reads are known in advance to follow a small number of specific access patterns rather than ad-hoc queries.

## 3. Core concept

**Rows with dynamic columns, not a fixed schema:** unlike a relational table where every row has the exact same columns, one row in a wide-column store might have columns `name`, `email`; another row in the same table might have `name`, `email`, `lastLoginAt` — the set of columns is per-row, not fixed for the whole table.

**Partition key and clustering columns:** a wide-column store's primary key typically has two parts: a **partition key**, which determines which node in the cluster stores the row (via hashing, similar to consistent hashing), and one or more **clustering columns**, which determine the sort order of rows *within* that partition. Designing the right partition key is the single most important decision in a wide-column schema, because all efficient queries must include it.

**Query-first schema design:** because a wide-column store has no general-purpose join and limited ad-hoc filtering, tables are typically designed around one specific query each — it is common to store the same underlying data in multiple differently-keyed tables, one per access pattern, rather than normalizing it once as you would relationally.

**Why this scales writes so well:** because rows are distributed by partition key hash across many nodes, and each node only needs to append to its own local storage for the writes it owns, write throughput scales roughly linearly by adding more nodes — very different from a single relational primary that must coordinate all writes centrally.

## 4. Diagram

```
Table: events, partition key = deviceId, clustering column = timestamp (sorted DESC)

  partition "device-42" (all rows for this device live on ONE node):
     timestamp=2026-08-05T10:02  temp=71.2
     timestamp=2026-08-05T10:01  temp=71.0     <- sorted by clustering column
     timestamp=2026-08-05T10:00  temp=70.8

  partition "device-99" (a DIFFERENT node, hashed independently):
     timestamp=2026-08-05T10:01  temp=68.5

  QUERY: "latest readings for device-42" -> hits ONE partition, ONE node, reads sorted rows directly
  QUERY: "all devices with temp > 70 right now" -> NOT a supported query shape; needs a different table
```
*Caption: the partition key routes a row to one node; the clustering column keeps that partition's rows pre-sorted for the one query pattern the table was designed for.*

## 5. Runnable example

**Level 1 — Basic.** Model rows partitioned by a key, with clustering-column sort order within each partition.

**Level 2 — Dynamic columns.** Show two rows in the same "table" with different column sets.

**Level 3 — Query-first design.** Store the same event data in two differently-keyed tables, one per access pattern, and show each is efficient for its own query only.

```java
// WideColumnStores.java
import java.util.*;

public class WideColumnStores {

    record Reading(String timestamp, double temp) {}

    // Level 1: partitioned by deviceId (the partition key); each partition's rows sorted by timestamp.
    static final Map<String, TreeMap<String, Double>> byDevice = new HashMap<>(); // deviceId -> {timestamp -> temp}

    static void insertReading(String deviceId, String timestamp, double temp) {
        byDevice.computeIfAbsent(deviceId, d -> new TreeMap<>(Comparator.reverseOrder())).put(timestamp, temp);
    }

    // Level 3: a SECOND table, keyed differently, for a different query pattern ("readings above a threshold, by time").
    static final TreeMap<String, List<String>> byTimestamp = new TreeMap<>(); // timestamp -> [deviceId, ...]

    static void insertIntoTimeIndex(String deviceId, String timestamp) {
        byTimestamp.computeIfAbsent(timestamp, t -> new ArrayList<>()).add(deviceId);
    }

    public static void main(String[] args) {
        insertReading("device-42", "10:00", 70.8);
        insertReading("device-42", "10:01", 71.0);
        insertReading("device-42", "10:02", 71.2);
        insertReading("device-99", "10:01", 68.5);

        insertIntoTimeIndex("device-42", "10:00");
        insertIntoTimeIndex("device-42", "10:01");
        insertIntoTimeIndex("device-42", "10:02");
        insertIntoTimeIndex("device-99", "10:01");

        // Level 1: efficient query - "latest readings for device-42" - hits ONE partition, already sorted.
        System.out.println("latest readings for device-42 (one partition, pre-sorted):");
        for (Map.Entry<String, Double> e : byDevice.get("device-42").entrySet()) {
            System.out.println("  " + e.getKey() + " -> " + e.getValue());
        }

        // Level 2: dynamic columns - device-99's row set differs from device-42's (fewer readings so far).
        System.out.println("device-42 has " + byDevice.get("device-42").size() + " columns (readings)");
        System.out.println("device-99 has " + byDevice.get("device-99").size() + " columns (readings) - a different shape, same table");

        // Level 3: efficient query on the SECOND, differently-keyed table - "all devices reporting at 10:01".
        System.out.println("all devices reporting at 10:01 (uses the byTimestamp table, not byDevice):");
        System.out.println("  " + byTimestamp.get("10:01"));
    }
}
```

**How to run:** save as `WideColumnStores.java`, then run `java WideColumnStores.java`.

## 6. Walkthrough

1. `insertReading` puts each reading into a `TreeMap` keyed by `deviceId` at the top level (the partition key) and sorted by `timestamp` within that partition (the clustering column, sorted descending for "latest first").
2. `byDevice.get("device-42")` returns only that device's rows, already sorted newest-first — mirroring how a real wide-column store answers "give me this partition's rows in clustering order" with no scan of other partitions at all.
3. `device-42` ends up with 3 readings (columns) and `device-99` with only 1 — different column counts for different rows in the same conceptual table, mirroring wide-column's per-row dynamic column sets.
4. `byTimestamp`, a completely separate structure keyed by `timestamp` instead of `deviceId`, is populated alongside `byDevice` — mirroring the query-first pattern of maintaining a second table specifically for a second query shape ("who reported at a given time"), rather than trying to force one table to answer both efficiently.
5. `byTimestamp.get("10:01")` directly returns `[device-42, device-99]` — a query that would require scanning every partition in `byDevice` is instead answered efficiently by the differently-keyed second table.

## 7. Gotchas & takeaways

> Gotcha: querying by anything *other* than a table's designed partition key (for example, trying to find "all readings above 71 degrees, across every device" against the `byDevice` table) requires scanning every partition on every node — exactly the kind of full-cluster scan wide-column stores are built to avoid, which is why query-first schema design, duplicating data into multiple tables, is the normal and expected practice, not a workaround.

- Wide-column stores trade relational flexibility for horizontal write scale and fast, predictable reads — but strictly only for the access patterns their partition keys were designed around.
- Designing the partition key correctly is the single most important schema decision; getting it wrong means either hot partitions (too coarse) or inefficient queries (too fine, or wrong for the actual query pattern).
- Related concepts: [Access-pattern-first data modeling](0082-access-pattern-first-data-modeling.md) (the general discipline this store type demands more strictly than any other), [Hot keys & key distribution](0052-hot-keys-key-distribution.md) (a poorly chosen partition key directly causes this problem).
