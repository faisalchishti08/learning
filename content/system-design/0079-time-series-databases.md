---
card: system-design
gi: 79
slug: time-series-databases
title: Time-series databases
---

## 1. What it is

A **time-series database** is optimized specifically for data points indexed by time — metrics, sensor readings, application logs — where writes arrive continuously and roughly in time order, and reads typically ask for a range of time (the last hour, the last week) rather than a single point. InfluxDB, TimescaleDB, and Prometheus are common examples.

## 2. Why & when

Time-series data has a distinctive shape: an extremely high volume of writes, almost always for the current moment, and reads that overwhelmingly ask for a contiguous time range, often aggregated (the average CPU usage per minute over the last day). General-purpose databases can store this data, but a time-series database is built around this exact shape — optimized storage layout, purpose-built compression, and built-in **downsampling** and retention policies. Use one for metrics, monitoring, IoT sensor data, or any dataset that is fundamentally "a value, at a timestamp," queried mostly by time range.

## 3. Core concept

**Storage laid out by time, not by row order:** a time-series database typically groups data into time-based chunks (an hour's or a day's worth of points together), so a query for "the last 24 hours" reads a small, contiguous region instead of scanning the entire dataset — the time-range equivalent of a wide-column store's partition-key locality.

**Compression exploiting time-series structure:** consecutive readings from the same sensor tend to be close in value and evenly spaced in time, which compresses extremely well with delta encoding (storing the *difference* from the previous point, rather than the full value each time) — often reducing storage by an order of magnitude compared to storing raw values.

**Downsampling and retention:** raw, per-second data is rarely useful forever — a time-series database can automatically **downsample** old data (replace a day of per-second readings with one row per minute, keeping only aggregates like min/max/average) and enforce a **retention policy** (automatically delete data older than a configured age), keeping storage bounded even under continuous high-volume ingestion.

**Time-bucketed aggregation as a first-class query:** `SELECT avg(cpu) FROM metrics WHERE time > now() - 1h GROUP BY time_bucket('1m')` — grouping and aggregating by time buckets is a core, optimized operation, not something bolted onto a general-purpose query language.

## 4. Diagram

```
Raw ingestion (continuous, mostly appends at "now"):
  10:00:01 cpu=42  10:00:02 cpu=43  10:00:03 cpu=41  ... (thousands of points per second)

Stored in TIME-ORDERED chunks:
  [chunk: 10:00-10:05] [chunk: 10:05-10:10] [chunk: 10:10-10:15] ...
  query "last 5 minutes" -> reads ONE chunk, not the whole dataset

Downsampling (older data compacted automatically):
  raw per-second data, age < 1 day  -> kept as-is
  per-second data, age > 1 day      -> compacted to per-minute avg/min/max, raw points discarded
  data, age > 90 days               -> deleted entirely (retention policy)
```
*Caption: time-ordered storage makes range queries fast; downsampling and retention keep storage bounded despite continuous high-volume writes.*

## 5. Runnable example

**Level 1 — Basic.** Ingest time-stamped points and query a time range directly (a sorted structure, mirroring time-ordered chunks).

**Level 2 — Time-bucketed aggregation.** Group points into fixed-size time buckets and compute an average per bucket.

**Level 3 — Downsampling.** Replace old raw points with one aggregated summary per bucket, shrinking storage while preserving the trend.

```java
// TimeSeriesDatabases.java
import java.util.*;

public class TimeSeriesDatabases {

    record Point(int timestamp, double value) {} // timestamp in seconds, for simplicity

    // Level 1: time-ordered storage - TreeMap keeps points sorted by time, enabling fast range queries.
    static final TreeMap<Integer, Double> series = new TreeMap<>();

    static void ingest(int timestamp, double value) { series.put(timestamp, value); }

    static SortedMap<Integer, Double> queryRange(int fromTs, int toTs) {
        return series.subMap(fromTs, true, toTs, true); // reads only this contiguous range
    }

    // Level 2: time-bucketed aggregation, grouping by a fixed bucket size.
    static Map<Integer, Double> aggregateByBucket(int bucketSizeSeconds) {
        Map<Integer, List<Double>> grouped = new TreeMap<>();
        for (Map.Entry<Integer, Double> e : series.entrySet()) {
            int bucket = (e.getKey() / bucketSizeSeconds) * bucketSizeSeconds;
            grouped.computeIfAbsent(bucket, b -> new ArrayList<>()).add(e.getValue());
        }
        Map<Integer, Double> averages = new TreeMap<>();
        for (Map.Entry<Integer, List<Double>> e : grouped.entrySet()) {
            averages.put(e.getKey(), e.getValue().stream().mapToDouble(Double::doubleValue).average().orElse(0));
        }
        return averages;
    }

    public static void main(String[] args) {
        // Simulate CPU readings arriving roughly every second, from t=0 to t=9.
        double[] rawValues = {40, 42, 41, 43, 44, 60, 62, 61, 59, 58};
        for (int t = 0; t < rawValues.length; t++) ingest(t, rawValues[t]);

        // Level 1: range query - only the last 5 seconds.
        System.out.println("last 5 seconds (t=5..9), read as a contiguous range: " + queryRange(5, 9));

        // Level 2: time-bucketed aggregation, bucket size = 5 seconds.
        Map<Integer, Double> bucketAverages = aggregateByBucket(5);
        System.out.println("5-second bucket averages: " + bucketAverages);

        // Level 3: downsampling - replace 10 raw points with 2 aggregated bucket summaries.
        System.out.println("raw point count: " + series.size());
        System.out.println("downsampled point count (one per bucket): " + bucketAverages.size());
        System.out.println("downsampled series still shows the trend (40s rising to 60s): " + bucketAverages);
    }
}
```

**How to run:** save as `TimeSeriesDatabases.java`, then run `java TimeSeriesDatabases.java`.

## 6. Walkthrough

1. `series` is a `TreeMap<Integer, Double>` keeping every point sorted by timestamp, mirroring time-ordered on-disk chunking.
2. `queryRange(5, 9)` uses `subMap`, which reads only the contiguous portion of the structure between those two timestamps — mirroring a time-series database reading only the relevant chunk(s) instead of the whole dataset.
3. `aggregateByBucket(5)` groups all ten points into two 5-second buckets (`t=0-4` and `t=5-9`), then averages each bucket's values, producing `{0=42.0, 5=60.0}` — mirroring `GROUP BY time_bucket('5s')`.
4. The averages clearly preserve the underlying trend (a low-40s plateau followed by a jump to the low-60s), even though each bucket collapses 5 raw points into 1 aggregated value.
5. Comparing `series.size()` (`10` raw points) to `bucketAverages.size()` (`2` downsampled points) shows the storage reduction downsampling provides, while the two remaining values still communicate the same overall shape the raw data showed — exactly the trade a real downsampling retention policy makes for old data.

## 7. Gotchas & takeaways

> Gotcha: once data is downsampled (raw points replaced with per-bucket aggregates), any query needing the original raw values — an exact reading at a specific second, rather than a bucket average — can no longer be answered; downsampling and retention policies must be configured deliberately, based on how far back fine-grained detail is actually needed.

- Time-series databases specialize in exactly one shape of data: continuous, mostly-append writes, queried by time range and often aggregated — general-purpose databases can store this data but rarely optimize for it as deeply.
- Downsampling and retention are what keep storage bounded despite unbounded, continuous ingestion — without them, a busy metrics pipeline would grow storage forever.
- Related concepts: [Wide-column stores](0077-wide-column-stores.md) (a related, partition-and-cluster-key-based approach some time-series databases are built on), [Client / CDN / application / database cache layers](0055-client-cdn-application-database-cache-layers.md) (recent time-series data is often additionally cached, since dashboards repeatedly query the same recent window).
