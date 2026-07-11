---
card: spring-data
gi: 117
slug: time-series-collections
title: "Time series collections"
---

## 1. What it is

A **time series collection** is a special MongoDB collection type, purpose-built for storing measurements taken over time — sensor readings, metrics, event logs — where every document shares a timestamp field and, usually, a "what is this a measurement of" metadata field. Spring Data MongoDB creates one either via `@TimeSeries` on a document class or `CollectionOptions.timeSeries(...)`, and MongoDB stores and compresses the underlying data very differently from a regular collection, dramatically speeding up time-range queries.

```java
@TimeSeries(timeField = "recordedAt", metaField = "orderId", granularity = Granularity.MINUTES)
@Document("order_status_events")
class OrderStatusEvent {
    Instant recordedAt;
    String orderId;
    String status;
}
```

## 2. Why & when

A regular collection stores each document independently, with its own indexing and storage overhead — fine for typical CRUD, but wasteful when you have millions of small, timestamped documents that all share the same shape and are almost always queried by time range. Time series collections group documents that are close in time and share the same `metaField` value into internal storage "buckets," which both compresses the data far better and makes range queries over time dramatically faster.

Reach for a time series collection when:

- You're recording a high volume of timestamped events — order status transitions, application metrics, IoT sensor readings — where the dominant query pattern is "show me everything between time A and time B."
- The data is fundamentally append-only: you write new measurements constantly but rarely update or delete old ones.
- You want MongoDB's built-in time-based compression and query optimizations, instead of hand-rolling your own bucketing scheme on top of a regular collection.

It's not the right fit for data that's frequently updated in place, or where most queries look up a single document by ID rather than a time range — a normal collection (with an index on the timestamp field) may serve those patterns just as well with less specialized machinery.

## 3. Core concept

```
 Regular collection: each event is its own independent document
   {recordedAt: 10:00:01, orderId: "A", status: "PENDING"}
   {recordedAt: 10:00:05, orderId: "A", status: "PACKED"}
   {recordedAt: 10:00:09, orderId: "B", status: "PENDING"}
   -- three separate documents, three separate storage entries

 Time series collection: MongoDB internally BUCKETS nearby, same-meta documents together
   bucket[orderId=A, ~10:00]: [{10:00:01, PENDING}, {10:00:05, PACKED}]   <- one compressed storage unit
   bucket[orderId=B, ~10:00]: [{10:00:09, PENDING}]
   -- application code still inserts/queries individual documents; MongoDB handles bucketing internally
```

The application never sees buckets directly — it inserts and queries individual documents exactly like any other collection, but MongoDB stores and compresses them using the bucketed layout underneath.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Individual timestamped events for the same order are grouped into a compressed bucket inside a time series collection">
  <text x="20" y="20" fill="#e6edf3" font-size="10" font-family="sans-serif">Events inserted individually:</text>
  <rect x="20" y="30" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="95" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">10:00:01 A PENDING</text>
  <rect x="180" y="30" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="255" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">10:00:05 A PACKED</text>
  <rect x="340" y="30" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="415" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">10:00:09 B PENDING</text>

  <line x1="95" y1="65" x2="180" y2="120" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <line x1="255" y1="65" x2="180" y2="120" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <line x1="415" y1="65" x2="400" y2="120" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>

  <rect x="40" y="130" width="260" height="45" rx="8" fill="#6db33f22" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="157" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">bucket [orderId=A, ~10:00] (compressed)</text>

  <rect x="330" y="130" width="260" height="45" rx="8" fill="#6db33f22" stroke="#6db33f" stroke-width="1.5"/>
  <text x="460" y="157" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">bucket [orderId=B, ~10:00] (compressed)</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Same-meta, close-in-time documents collapse into shared, compressed storage buckets, invisible to the querying application.

## 5. Runnable example

The scenario: recording order status change events over time, evolving from a plain append-only list standing in for a regular collection, to a bucketed layout matching what a time series collection does internally, to a range query with per-hour downsampling — the kind of aggregation time series collections are built to make fast.

### Level 1 — Basic

Model a regular, non-bucketed collection: every event is its own independent entry.

```java
import java.time.*;
import java.util.*;

public class TimeSeriesLevel1 {
    public static void main(String[] args) {
        RegularCollection events = new RegularCollection();
        Instant base = Instant.parse("2026-07-11T10:00:00Z");

        events.insert(new OrderStatusEvent(base, "A", "PENDING"));
        events.insert(new OrderStatusEvent(base.plusSeconds(4), "A", "PACKED"));
        events.insert(new OrderStatusEvent(base.plusSeconds(8), "B", "PENDING"));

        System.out.println("Stored as " + events.docs.size() + " independent documents:");
        for (OrderStatusEvent e : events.docs) System.out.println("  " + e.recordedAt + " " + e.orderId + " " + e.status);
    }
}

class OrderStatusEvent { Instant recordedAt; String orderId; String status; OrderStatusEvent(Instant recordedAt, String orderId, String status) { this.recordedAt = recordedAt; this.orderId = orderId; this.status = status; } }

// Stands in for a REGULAR MongoDB collection -- one storage entry per document, no bucketing.
class RegularCollection {
    List<OrderStatusEvent> docs = new ArrayList<>();
    void insert(OrderStatusEvent event) { docs.add(event); }
}
```

How to run: `java TimeSeriesLevel1.java`

Every event lands in `docs` as its own independent entry, exactly how a regular MongoDB collection stores documents — no relationship between the three events is captured beyond what's in each document's own fields. This is the baseline a time series collection improves on.

### Level 2 — Intermediate

Model MongoDB's internal bucketing: events sharing a `metaField` (`orderId`) and falling in the same time window are grouped into one bucket — matching `@TimeSeries(timeField = "recordedAt", metaField = "orderId", granularity = Granularity.MINUTES)`.

```java
import java.time.*;
import java.util.*;

public class TimeSeriesLevel2 {
    public static void main(String[] args) {
        TimeSeriesCollection events = new TimeSeriesCollection();
        Instant base = Instant.parse("2026-07-11T10:00:00Z");

        events.insert(new OrderStatusEvent(base, "A", "PENDING"));
        events.insert(new OrderStatusEvent(base.plusSeconds(4), "A", "PACKED"));       // same minute, same order -> same bucket
        events.insert(new OrderStatusEvent(base.plusSeconds(8), "B", "PENDING"));      // different order -> different bucket

        System.out.println("Internally stored as " + events.buckets.size() + " bucket(s):");
        for (var entry : events.buckets.entrySet()) {
            System.out.println("  bucket " + entry.getKey() + " contains " + entry.getValue().size() + " event(s)");
        }
    }
}

class OrderStatusEvent { Instant recordedAt; String orderId; String status; OrderStatusEvent(Instant recordedAt, String orderId, String status) { this.recordedAt = recordedAt; this.orderId = orderId; this.status = status; } }

// Stands in for how MongoDB internally buckets a time series collection: grouped by metaField + time window.
class TimeSeriesCollection {
    // key: "metaField|windowStart" -- one bucket per (orderId, minute) pair
    Map<String, List<OrderStatusEvent>> buckets = new LinkedHashMap<>();

    void insert(OrderStatusEvent event) {
        Instant windowStart = event.recordedAt.truncatedTo(java.time.temporal.ChronoUnit.MINUTES); // MINUTES granularity
        String bucketKey = event.orderId + "|" + windowStart;
        buckets.computeIfAbsent(bucketKey, k -> new ArrayList<>()).add(event);
    }
}
```

How to run: `java TimeSeriesLevel2.java`

The two `orderId=A` events, four seconds apart, fall in the same one-minute window and land in the same bucket; the `orderId=B` event, having a different `metaField` value, gets its own bucket even though it's only eight seconds after the first event. This is the internal storage layout `Granularity.MINUTES` implies — the application still calls `insert` per document, but MongoDB groups the storage for compression and fast time-range scans.

### Level 3 — Advanced

Run a time-range query with hourly downsampling — averaging a numeric measurement per hour, the classic time series aggregation pattern.

```java
import java.time.*;
import java.time.temporal.*;
import java.util.*;
import java.util.stream.*;

public class TimeSeriesLevel3 {
    public static void main(String[] args) {
        TimeSeriesCollection metrics = new TimeSeriesCollection();
        Instant hour10 = Instant.parse("2026-07-11T10:00:00Z");
        Instant hour11 = Instant.parse("2026-07-11T11:00:00Z");
        Instant hour12 = Instant.parse("2026-07-11T12:00:00Z"); // outside the query window below

        metrics.insert(new MetricEvent(hour10.plusSeconds(30), "A", 120));
        metrics.insert(new MetricEvent(hour10.plusSeconds(600), "B", 180));
        metrics.insert(new MetricEvent(hour11.plusSeconds(30), "A", 90));
        metrics.insert(new MetricEvent(hour12.plusSeconds(30), "C", 999)); // outside the range, must be excluded

        List<Map.Entry<Instant, Double>> hourlyAverages = metrics.averageLatencyPerHour(hour10, hour12);

        System.out.println("Average processing latency per hour (10:00 to 12:00, exclusive):");
        for (var entry : hourlyAverages) System.out.println("  " + entry.getKey() + " -> avg " + entry.getValue() + " ms");
    }
}

class MetricEvent { Instant recordedAt; String orderId; double processingLatencyMs; MetricEvent(Instant recordedAt, String orderId, double processingLatencyMs) { this.recordedAt = recordedAt; this.orderId = orderId; this.processingLatencyMs = processingLatencyMs; } }

class TimeSeriesCollection {
    List<MetricEvent> allEvents = new ArrayList<>(); // bucketing detail omitted here -- focus is the query pattern
    void insert(MetricEvent event) { allEvents.add(event); }

    // Mirrors an aggregation pipeline: $match (time range) -> $group (by hour) -> $avg
    List<Map.Entry<Instant, Double>> averageLatencyPerHour(Instant from, Instant to) {
        return allEvents.stream()
            .filter(e -> !e.recordedAt.isBefore(from) && e.recordedAt.isBefore(to)) // $match: time range
            .collect(Collectors.groupingBy(
                e -> e.recordedAt.truncatedTo(ChronoUnit.HOURS),                     // $group by hour bucket
                Collectors.averagingDouble(e -> e.processingLatencyMs)))             // $avg
            .entrySet().stream()
            .sorted(Map.Entry.comparingByKey())
            .collect(Collectors.toList());
    }
}
```

How to run: `java TimeSeriesLevel3.java`

`averageLatencyPerHour` filters to the `[from, to)` window, groups the remaining events by their truncated hour, and averages `processingLatencyMs` within each group — the Java equivalent of a `$match`/`$group`/`$avg` aggregation pipeline run against a time series collection. The `hour12` event is outside the queried range and correctly excluded from the result, even though it was inserted into the same collection.

## 6. Walkthrough

Execution starts in `main` for Level 3. Four `MetricEvent`s are inserted at `10:00:30`, `10:10:00`, `11:00:30`, and `12:00:30`, with latencies `120`, `180`, `90`, and `999` milliseconds respectively.

`metrics.averageLatencyPerHour(hour10, hour12)` is then called with a range from `10:00:00` (inclusive) to `12:00:00` (exclusive). Internally, the `stream().filter(...)` step keeps only events where `recordedAt` is `>= from` and `< to` — this keeps the first three events and drops the `12:00:30` one, since `12:00:30` is not before `12:00:00`.

The surviving events are then grouped by `recordedAt.truncatedTo(HOURS)`: the two events at `10:00:30` and `10:10:00` both truncate to `10:00:00` and land in the same group; the `11:00:30` event truncates to `11:00:00` and forms its own group. `Collectors.averagingDouble` computes the mean latency within each group: the `10:00` group averages `(120 + 180) / 2 = 150.0`, and the `11:00` group has a single value, `90.0`. The results are sorted by hour and printed.

```
Average processing latency per hour (10:00 to 12:00, exclusive):
  2026-07-11T10:00:00Z -> avg 150.0 ms
  2026-07-11T11:00:00Z -> avg 90.0 ms
```

In real Spring Data MongoDB, this same query would be expressed as an `Aggregation` pipeline (`Aggregation.match(Criteria.where("recordedAt").gte(from).lt(to)), Aggregation.group(dateTrunc("recordedAt", "hour")).avg("processingLatencyMs").as("avgLatency")`) run via `mongoTemplate.aggregate(...)` against the time series collection — and because the collection is bucketed by time internally, MongoDB can skip entire buckets that fall outside `[from, to)` without inspecting every document, which is exactly the performance advantage a time series collection has over a regular one for this access pattern.

## 7. Gotchas & takeaways

> Gotcha: time series collections are optimized for **inserting new measurements and querying by time range** — updating or deleting individual historical documents is far more restricted and slower than in a regular collection, because it disturbs the compressed bucket layout. Don't reach for one if your data is frequently mutated in place.

> Gotcha: choosing `Granularity` (`SECONDS`/`MINUTES`/`HOURS`) too coarse or too fine relative to your actual write frequency hurts bucketing efficiency — it should roughly match how close together in time your measurements for the same `metaField` value typically arrive.

- `@TimeSeries(timeField = ..., metaField = ..., granularity = ...)` (or `CollectionOptions.timeSeries(...)`) creates a collection MongoDB stores and compresses using internal time-and-meta buckets.
- Application code inserts and queries individual documents exactly as with any collection — bucketing is invisible except in its effect on performance and storage size.
- The ideal fit is high-volume, append-only, timestamped data queried predominantly by time range — sensor readings, metrics, status-change event logs.
- Range queries and hourly/daily aggregations (`$match` + `$group` by truncated time) are the query shapes a time series collection is specifically optimized to make fast.
