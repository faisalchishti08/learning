---
card: system-design
gi: 156
slug: data-lake-vs-data-warehouse
title: Data lake vs data warehouse
---

## 1. What it is

A **data lake** stores raw data in its original format — JSON, CSV, log files, images — without requiring a predefined structure before you write it in, typically on cheap [object storage](0152-object-blob-storage-s3-like.md). A **data warehouse** stores data in a strict, predefined schema of tables and columns, already cleaned and transformed, optimized for fast analytical queries (aggregations, joins, reports). The core difference is *when* you impose structure: a data lake is "schema-on-read" (you decide the structure when you query it), and a data warehouse is "schema-on-write" (the structure is fixed before the data goes in).

## 2. Why & when

Teams need both, for different reasons. A data lake is cheap and flexible — you can dump any raw data into it immediately, without deciding up front exactly how you will use it later, which suits exploratory analysis, machine learning training data, and archiving everything "just in case." A data warehouse is fast and reliable for a known, repeated set of business questions — dashboards, monthly reports — because its data is already cleaned, structured, and indexed for that purpose. Use a data lake to capture raw data broadly and cheaply; use a data warehouse (often fed *from* the lake, after a transformation step) for the specific, well-understood analytical queries the business runs every day.

## 3. Core concept

- **Schema-on-read (data lake):** raw files are stored as-is; the structure (which fields exist, their types) is only decided and applied when a query tool reads the data — this is flexible, but a bad or inconsistent input format is only discovered at query time.
- **Schema-on-write (data warehouse):** an ETL (Extract, Transform, Load) or ELT pipeline cleans and reshapes raw data into a fixed table structure *before* it is loaded — invalid data is caught and handled during this load step, not at query time.
- **Storage cost and format:** data lakes use cheap object storage and flexible formats (JSON, Parquet, CSV); data warehouses use structured, often columnar storage engineered for fast aggregation over specific columns.
- **Query pattern:** data lakes are queried with tools that can interpret varied raw formats (e.g. Spark, Presto); data warehouses are queried with SQL against well-known tables, usually much faster for a known reporting question.
- **The common pipeline:** many architectures load raw data into the lake first (cheap, fast, lossless), then run a transformation job that cleans and loads a curated subset into the warehouse for the queries that matter most.

## 4. Diagram

```
   raw sources (app logs, clickstream, JSON events, CSVs)
              |
              v
   +-------------------------+          transform (ETL/ELT):
   |  DATA LAKE               |   ---->  clean, validate,
   |  object storage          |          reshape into tables
   |  raw, schema-on-read     |              |
   +-------------------------+               v
                                   +-------------------------+
                                   |  DATA WAREHOUSE          |
                                   |  fixed schema, tables    |
                                   |  schema-on-write         |
                                   +-------------------------+
                                              |
                                    fast SQL dashboards & reports
```
*Caption: raw data lands in the lake first, cheaply and without structure; only the data a known report actually needs is transformed and loaded into the warehouse.*

## 5. Runnable example

**Level 1 — Basic.** A data lake: store raw, inconsistently-shaped records as-is.

**Level 2 — Schema-on-read.** Apply structure only at query time, handling records that do not match the expected shape.

**Level 3 — ETL into a data warehouse.** Transform the valid subset of raw records into a strict, fixed-schema table, and run a fast aggregation query against it.

```java
// DataLakeVsWarehouseDemo.java
import java.util.*;

public class DataLakeVsWarehouseDemo {

    // Level 1: the data lake - raw, untyped, possibly inconsistent records, stored as-is.
    static List<Map<String, String>> dataLake = new ArrayList<>();

    // Level 3: the data warehouse - a strict, fixed-schema table.
    static class OrderRow {
        final String orderId;
        final double amount;
        OrderRow(String orderId, double amount) { this.orderId = orderId; this.amount = amount; }
    }
    static List<OrderRow> ordersWarehouseTable = new ArrayList<>();

    public static void main(String[] args) {
        // Level 1: raw records land in the lake exactly as they arrived - note the inconsistent shapes.
        dataLake.add(Map.of("orderId", "o1", "amount", "49.99", "currency", "USD"));
        dataLake.add(Map.of("orderId", "o2", "amount", "not-a-number", "currency", "USD")); // malformed
        dataLake.add(Map.of("orderId", "o3", "amount", "120.00")); // missing "currency" field entirely
        dataLake.add(Map.of("eventType", "click", "page", "/home")); // a totally different record shape

        System.out.println("data lake holds " + dataLake.size() + " raw records of varying shapes, stored without complaint.");

        // Level 2: schema-on-read - a query decides, right now, what shape it expects, and skips what doesn't fit.
        System.out.println("querying the lake AS IF it were order data:");
        for (Map<String, String> record : dataLake) {
            if (!record.containsKey("orderId") || !record.containsKey("amount")) {
                System.out.println("  skipped record (does not look like order data): " + record);
                continue;
            }
            try {
                double amount = Double.parseDouble(record.get("amount"));
                System.out.println("  valid order record: " + record.get("orderId") + " = " + amount);
            } catch (NumberFormatException e) {
                System.out.println("  skipped malformed record: " + record);
            }
        }

        // Level 3: ETL - transform ONLY the valid order records into the warehouse's strict schema.
        for (Map<String, String> record : dataLake) {
            if (!record.containsKey("orderId") || !record.containsKey("amount")) continue;
            try {
                double amount = Double.parseDouble(record.get("amount"));
                ordersWarehouseTable.add(new OrderRow(record.get("orderId"), amount));
            } catch (NumberFormatException e) { /* dropped during ETL, not at query time */ }
        }

        // A fast, reliable aggregation query against the CLEAN warehouse table.
        double total = ordersWarehouseTable.stream().mapToDouble(r -> r.amount).sum();
        System.out.println("warehouse table has " + ordersWarehouseTable.size() + " clean rows; total revenue = " + total);
    }
}
```

**How to run:** save as `DataLakeVsWarehouseDemo.java`, then run `java DataLakeVsWarehouseDemo.java`.

## 6. Walkthrough

1. Four raw records are added to `dataLake`, each with a different shape: a valid order, an order with a non-numeric `amount`, an order missing its `currency` field, and an unrelated click event — the lake accepts all four without any validation, exactly modeling schema-on-read.
2. The "query the lake" loop applies structure *now*, at read time: it checks `containsKey("orderId")` and `containsKey("amount")` first, immediately skipping the click-event record since it has neither field.
3. For the remaining candidates, `Double.parseDouble(record.get("amount"))` succeeds for `o1` and `o3`, but throws a `NumberFormatException` for `o2`'s `"not-a-number"` value, which is caught and printed as a skipped, malformed record — this discovery of bad data happens only now, at query time, which is the defining risk of schema-on-read.
4. The ETL loop repeats a similar filter, but this time writes the successfully-parsed records (`o1` and `o3`) into `ordersWarehouseTable` as strongly-typed `OrderRow` objects, permanently leaving the malformed `o2` record out of the warehouse entirely.
5. The final aggregation, `ordersWarehouseTable.stream().mapToDouble(r -> r.amount).sum()`, runs against the clean, strictly-typed table and needs no error handling at all — it correctly sums to `49.99 + 120.00 = 169.99`, showing the warehouse's fast, reliable querying comes from the validation work having already happened during the earlier ETL step, not during this query.

## 7. Gotchas & takeaways

> Gotcha: relying on a data lake alone for frequent, business-critical reporting means every single query has to re-discover and re-handle the same malformed or inconsistent records — as this demo's query loop had to skip `o2` and the click event every time it ran. A data warehouse pays that validation cost once, during ETL, so every subsequent query is fast and does not need its own error-handling logic.

- A data lake stores raw data cheaply and flexibly, deferring structure to query time; a data warehouse enforces structure up front, at load time.
- Schema-on-read gives flexibility but risks discovering bad data late, and repeatedly, at every query; schema-on-write catches it once, during ETL.
- A common architecture uses both: raw data lands in the lake first, and only the cleaned, business-relevant subset is transformed into the warehouse.
- Related concepts: [Object / blob storage (S3-like)](0152-object-blob-storage-s3-like.md) (the typical underlying storage for a data lake), [Hot / warm / cold storage tiers](0157-hot-warm-cold-storage-tiers.md) (how lake data is often tiered by access frequency), [Denormalization & data duplication](0081-denormalization-data-duplication.md) (a schema design tradeoff a warehouse's fixed tables often make).
