---
card: microservices
gi: 316
slug: reporting-analytics-database
title: "Reporting / analytics database"
---

## 1. What it is

A **reporting/analytics database** is a separate data store, distinct from any service's operational (OLTP) database, built specifically to answer heavy aggregation and cross-entity questions — "total revenue by region last quarter," "top 10 customers by order count" — questions that touch huge numbers of rows and don't need to be instantaneous. It is populated asynchronously from the operational services (via events, change-data-capture, or scheduled ETL jobs) rather than being written to directly by user-facing requests.

## 2. Why & when

Operational databases are tuned for fast, small, transactional reads and writes — "fetch this one order," "update this one row" — because that is what live user traffic needs. A reporting query that scans and joins millions of rows is the opposite workload: it is fine with being a few minutes stale, but it wants wide table scans and heavy aggregation to run fast, and it must never compete with live traffic for locks or CPU. Running BI-style queries directly against a production OLTP database risks locking rows that live customers are trying to read or write, and it forces one schema to serve two incompatible access patterns at once.

Use a dedicated reporting/analytics database whenever there is a genuine need to aggregate data across services or across a large historical window for dashboards, BI tools, or ad hoc analysis — and whenever those queries are heavy enough that running them live would degrade the operational systems that serve real users.

## 3. Core concept

The split is OLTP (operational, transactional, one-row-at-a-time) versus OLAP (analytical, aggregate, whole-table). Data flows one way, asynchronously: services publish events (or expose a change stream) as their data changes; a separate ingestion process consumes those events and writes them into the reporting database, usually in a schema shaped for aggregation (e.g., a star schema: one central "facts" table of numeric measures, surrounded by "dimension" tables like customer, product, and date) rather than a normalized OLTP schema.

```java
// A reporting row is shaped for aggregation, not for single-record lookup.
record OrderFact(String orderId, String customerId, String region,
                  double amount, java.time.LocalDate orderDate) {}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Order service and customer service each publish events; an ingestion process consumes them and writes into a separate reporting database; a BI tool queries only the reporting database, never the operational databases">
  <rect x="20" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="44" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Order Service</text>
  <rect x="20" y="90" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="114" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Customer Service</text>

  <line x1="160" y1="40" x2="270" y2="90" stroke="#8b949e" marker-end="url(#a316)"/>
  <line x1="160" y1="110" x2="270" y2="95" stroke="#8b949e" marker-end="url(#a316)"/>
  <text x="200" y="70" fill="#8b949e" font-size="9" font-family="sans-serif">events</text>

  <rect x="280" y="75" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="340" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Ingestion</text>

  <line x1="400" y1="95" x2="470" y2="95" stroke="#79c0ff" marker-end="url(#a316b)"/>

  <rect x="480" y="75" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Reporting DB</text>

  <line x1="550" y1="115" x2="550" y2="160" stroke="#3fb950" marker-end="url(#a316c)"/>
  <text x="550" y="180" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">BI tool queries only this</text>

  <defs>
    <marker id="a316" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a316b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="a316c" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Operational services publish events; an ingestion step feeds a separate reporting database; only that database absorbs heavy analytical queries.

## 5. Runnable example

Scenario: an in-memory order store that starts out serving both live lookups and heavy reporting queries from the same map, then splits reporting into its own async-fed store, then adds a staleness timestamp so consumers know how fresh the analytics are.

### Level 1 — Basic

```java
// File: SharedStoreContention.java -- reporting queries run directly
// against the SAME map that live order lookups use.
import java.util.*;

public class SharedStoreContention {
    record Order(String id, String region, double amount) {}
    static final Map<String, Order> liveOrders = new HashMap<>();

    static double totalRevenueByRegion(String region) { // the HEAVY reporting query
        double total = 0;
        for (Order o : liveOrders.values()) if (o.region().equals(region)) total += o.amount();
        return total;
    }

    public static void main(String[] args) {
        liveOrders.put("o1", new Order("o1", "EU", 100.0));
        liveOrders.put("o2", new Order("o2", "EU", 250.0));
        System.out.println("Live lookup: " + liveOrders.get("o1"));
        System.out.println("Reporting query (scans EVERY order, same store): EU revenue = "
                + totalRevenueByRegion("EU"));
    }
}
```

How to run: `java SharedStoreContention.java`

The single `liveOrders` map serves both a fast single-key lookup and a full-table scan for the reporting query. In a real system with millions of rows and concurrent writers, that scan would hold locks or consume resources that live traffic needs — this Level exists to show why that coupling is a problem, even though the code above happens to work in-memory.

### Level 2 — Intermediate

```java
// File: SeparateReportingStore.java -- order events are published and a
// SEPARATE reporting store is updated asynchronously; heavy queries never
// touch the live order store.
import java.util.*;

public class SeparateReportingStore {
    record OrderPlacedEvent(String orderId, String region, double amount) {}
    record OrderFact(String orderId, String region, double amount) {}

    static final Map<String, OrderPlacedEvent> liveOrders = new HashMap<>(); // operational store
    static final List<OrderFact> reportingStore = new ArrayList<>();          // separate analytics store

    static void onOrderPlaced(OrderPlacedEvent event) { // ingestion: feeds the reporting store
        reportingStore.add(new OrderFact(event.orderId(), event.region(), event.amount()));
    }

    static double totalRevenueByRegion(String region) { // reads ONLY the reporting store
        double total = 0;
        for (OrderFact f : reportingStore) if (f.region().equals(region)) total += f.amount();
        return total;
    }

    public static void main(String[] args) {
        OrderPlacedEvent e1 = new OrderPlacedEvent("o1", "EU", 100.0);
        OrderPlacedEvent e2 = new OrderPlacedEvent("o2", "EU", 250.0);

        liveOrders.put(e1.orderId(), e1); onOrderPlaced(e1); // write path: live store + event to reporting
        liveOrders.put(e2.orderId(), e2); onOrderPlaced(e2);

        System.out.println("Live lookup (operational store): " + liveOrders.get("o1"));
        System.out.println("Reporting query (separate store): EU revenue = " + totalRevenueByRegion("EU"));
    }
}
```

How to run: `java SeparateReportingStore.java`

Placing an order now does two things: it updates `liveOrders` (the fast operational store real requests read) and calls `onOrderPlaced`, which appends a fact row to `reportingStore`. `totalRevenueByRegion` now scans only `reportingStore` — a separate structure that could, in a real system, be a completely different database on different hardware, so the heavy scan never competes with a live order lookup for the same resource.

### Level 3 — Advanced

```java
// File: ReportingWithStaleness.java -- the reporting store is fed
// asynchronously (simulated with a delay) and every query result carries
// a staleness timestamp so consumers KNOW how fresh the numbers are.
import java.util.*;
import java.time.Instant;

public class ReportingWithStaleness {
    record OrderPlacedEvent(String orderId, String region, double amount, Instant occurredAt) {}
    record OrderFact(String orderId, String region, double amount) {}
    record ReportResult(double total, Instant asOf) {}

    static final Queue<OrderPlacedEvent> eventQueue = new LinkedList<>(); // events waiting to be ingested
    static final List<OrderFact> reportingStore = new ArrayList<>();
    static Instant lastIngestedAt = Instant.EPOCH;

    static void publish(OrderPlacedEvent event) { eventQueue.add(event); } // write path only enqueues

    static void runIngestionBatch() { // simulates a periodic ETL/ingestion job, NOT real-time
        OrderPlacedEvent event;
        while ((event = eventQueue.poll()) != null) {
            reportingStore.add(new OrderFact(event.orderId(), event.region(), event.amount()));
            lastIngestedAt = event.occurredAt();
        }
    }

    static ReportResult totalRevenueByRegion(String region) {
        double total = 0;
        for (OrderFact f : reportingStore) if (f.region().equals(region)) total += f.amount();
        return new ReportResult(total, lastIngestedAt); // caller sees BOTH the number and how fresh it is
    }

    public static void main(String[] args) {
        publish(new OrderPlacedEvent("o1", "EU", 100.0, Instant.parse("2026-07-01T10:00:00Z")));
        publish(new OrderPlacedEvent("o2", "EU", 250.0, Instant.parse("2026-07-01T10:05:00Z")));

        ReportResult beforeIngestion = totalRevenueByRegion("EU");
        System.out.println("Before ingestion runs: total=" + beforeIngestion.total()
                + " asOf=" + beforeIngestion.asOf() + " (queue not processed yet)");

        runIngestionBatch();

        ReportResult afterIngestion = totalRevenueByRegion("EU");
        System.out.println("After ingestion runs: total=" + afterIngestion.total()
                + " asOf=" + afterIngestion.asOf() + " (consumer can see exactly how stale this is)");
    }
}
```

How to run: `java ReportingWithStaleness.java`

Publishing an order now only enqueues an event — it does not immediately update `reportingStore`. Before `runIngestionBatch` runs, the reporting query correctly reports `total=0` with `asOf=1970-01-01T00:00:00Z` (the epoch default), honestly reflecting that no data has landed yet. After `runIngestionBatch` drains the queue and applies both facts, the same query returns the correct `total=350.0` with `asOf` set to the timestamp of the last event actually ingested — giving the caller a concrete answer to "how stale is this number," rather than a silent, unstated lag.

## 6. Walkthrough

Trace `ReportingWithStaleness.main` in order. **First**, two `publish` calls run, each simply adding an `OrderPlacedEvent` to `eventQueue` — at this point `reportingStore` is still empty and `lastIngestedAt` is still `Instant.EPOCH`.

**Next**, `totalRevenueByRegion("EU")` is called before any ingestion has happened. It scans the (still empty) `reportingStore`, finds nothing, and returns `ReportResult(0, Instant.EPOCH)` — this is printed as the "before ingestion" line, honestly showing zero and an epoch timestamp rather than pretending to have current data.

**Then**, `runIngestionBatch()` runs: it polls `eventQueue` until empty, and for each event appends a corresponding `OrderFact` to `reportingStore` and advances `lastIngestedAt` to that event's `occurredAt`. After this call, `reportingStore` holds two facts and `lastIngestedAt` is `2026-07-01T10:05:00Z` (the later of the two events).

**Finally**, `totalRevenueByRegion("EU")` is called again. It now scans a populated `reportingStore`, sums both `100.0` and `250.0` to get `350.0`, and returns that total paired with the current `lastIngestedAt` — printed as the "after ingestion" line.

```
publish(o1) publish(o2)  -> eventQueue=[o1,o2], reportingStore=[]
totalRevenueByRegion      -> total=0, asOf=EPOCH        (queue not drained yet)
runIngestionBatch()       -> reportingStore=[o1,o2], lastIngestedAt=10:05
totalRevenueByRegion      -> total=350.0, asOf=10:05     (now current as of ingestion)
```

## 7. Gotchas & takeaways

> A reporting database is, by design, **not** real-time. If a dashboard needs numbers that reflect the last few seconds of activity, a batch-fed reporting store is the wrong tool — that calls for a real-time stream-processing pipeline instead, which is a different (and more expensive) architecture.

- Never run heavy aggregation queries directly against a service's operational (OLTP) database — it competes with live traffic for locks and resources.
- The reporting database is fed asynchronously (events, CDC, or scheduled ETL), so it always lags the operational data by some amount; surface that lag (a staleness timestamp) rather than hiding it.
- Reporting schemas are usually denormalized (star schema: facts + dimensions) because they are optimized for aggregation, not for single-row transactional updates.
- This is a specific application of [CQRS](0313-command-query-responsibility-segregation-cqrs.md) at the analytics scale: reads (reporting) and writes (operational) are fully separated into different stores.
