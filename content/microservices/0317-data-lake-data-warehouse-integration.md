---
card: microservices
gi: 317
slug: data-lake-data-warehouse-integration
title: "Data lake / data warehouse integration"
---

## 1. What it is

A **data lake** is a store that ingests raw data from every service in whatever shape it arrives — JSON events, CSV exports, logs — cheaply and without requiring a fixed schema upfront. A **data warehouse** is a store that holds cleaned, structured, schema-enforced data, organized for fast analytical queries and joins across the whole business. In a microservices architecture, both are typically fed the same way: each service publishes events (or exposes a change stream) once, and separate pipelines land that data into the lake (as-is, for archival and flexible exploration) and, after transforming and validating it, into the warehouse (as structured tables, for reliable BI and reporting).

## 2. Why & when

A microservices system spreads data across dozens of independently owned databases, each shaped for its own service's needs. Nobody can run a single SQL join across "order service's Postgres" and "customer service's MongoDB" — they are different engines with no shared schema. A data lake and warehouse solve this by centralizing copies of the data outside any one service's database, in one place built for cross-service analysis instead of transactional serving.

Use a data lake when you need to retain raw, unstructured, or semi-structured data cheaply and flexibly — including data whose exact future use isn't known yet (machine learning training sets, ad hoc investigation). Use a data warehouse (often built by transforming lake data, an "ELT" pipeline: extract, load, then transform) when you need reliable, structured, schema-enforced tables that BI tools and analysts can query with confidence, joining across many services' data at once.

## 3. Core concept

Data flows one direction, out of the operational services and into analytical stores, never back: `services -> events/CDC -> data lake (raw) -> transform -> data warehouse (structured)`. The lake keeps everything, in original form, cheaply; the warehouse keeps a curated, validated, query-optimized subset.

```java
record RawEvent(String source, String type, String rawJsonPayload, long ingestedAtEpochMs) {} // lake row: as-is
record WarehouseOrderFact(String orderId, String region, double amount, java.time.LocalDate date) {} // warehouse row: validated, typed
```

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple services publish events which land raw in a data lake; a transform step validates and structures the data into a data warehouse for BI queries">
  <rect x="20" y="70" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="75" y="94" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Services</text>
  <line x1="130" y1="90" x2="200" y2="90" stroke="#8b949e" marker-end="url(#a317)"/>
  <rect x="210" y="70" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="265" y="90" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Data Lake</text>
  <text x="265" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(raw, as-is)</text>
  <line x1="320" y1="90" x2="390" y2="90" stroke="#79c0ff" marker-end="url(#a317b)"/>
  <text x="355" y="80" fill="#8b949e" font-size="8" font-family="sans-serif">transform</text>
  <rect x="400" y="70" width="130" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="465" y="90" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Data Warehouse</text>
  <text x="465" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(structured)</text>
  <line x1="465" y1="110" x2="465" y2="150" stroke="#3fb950" marker-end="url(#a317c)"/>
  <text x="465" y="168" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">BI queries</text>
  <defs>
    <marker id="a317" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a317b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="a317c" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Raw events land in the lake unchanged; a transform step validates and structures them into the warehouse for reliable BI queries.

## 5. Runnable example

Scenario: raw order events are dumped into a data lake with no validation, then a transform step promotes valid rows into a structured warehouse, then the pipeline is extended to quarantine invalid rows instead of silently dropping or crashing on them.

### Level 1 — Basic

```java
// File: RawLakeIngest.java -- events are landed in the lake EXACTLY as
// received, with no validation or structure.
import java.util.*;

public class RawLakeIngest {
    record RawEvent(String source, String rawJsonPayload) {}
    static final List<RawEvent> dataLake = new ArrayList<>();

    static void ingest(RawEvent event) { dataLake.add(event); } // no validation -- lake accepts anything

    public static void main(String[] args) {
        ingest(new RawEvent("order-service", "{\"orderId\":\"o1\",\"region\":\"EU\",\"amount\":100.0}"));
        ingest(new RawEvent("order-service", "{\"orderId\":\"o2\",\"amount\":\"not-a-number\"}")); // malformed, but lake still takes it
        System.out.println("Data lake now holds " + dataLake.size() + " raw rows, unvalidated:");
        dataLake.forEach(e -> System.out.println("  " + e));
    }
}
```

How to run: `java RawLakeIngest.java`

The lake's job is to keep everything, so it happily stores both the well-formed order and the malformed one (`amount` is the string `"not-a-number"`) side by side — no validation happens at this stage, which is intentional: the lake is cheap, flexible storage, not a data-quality gate.

### Level 2 — Intermediate

```java
// File: TransformToWarehouse.java -- a transform step reads the lake and
// promotes VALID rows into a structured warehouse table.
import java.util.*;

public class TransformToWarehouse {
    record RawEvent(String source, String rawJsonPayload) {}
    record WarehouseOrderFact(String orderId, String region, double amount) {}

    static final List<RawEvent> dataLake = new ArrayList<>();
    static final List<WarehouseOrderFact> warehouse = new ArrayList<>();

    static void ingest(RawEvent event) { dataLake.add(event); }

    // very small hand-rolled parser standing in for a real JSON library
    static WarehouseOrderFact tryParse(RawEvent event) {
        String json = event.rawJsonPayload();
        String orderId = extract(json, "orderId");
        String region = extract(json, "region");
        String amountStr = extract(json, "amount");
        if (orderId == null || region == null || amountStr == null) return null; // missing field
        try {
            return new WarehouseOrderFact(orderId, region, Double.parseDouble(amountStr));
        } catch (NumberFormatException e) {
            return null; // "not-a-number" fails HERE
        }
    }

    static String extract(String json, String key) {
        String marker = "\"" + key + "\":";
        int i = json.indexOf(marker);
        if (i < 0) return null;
        int start = i + marker.length();
        boolean quoted = json.charAt(start) == '"';
        if (quoted) start++;
        int end = quoted ? json.indexOf('"', start) : Math.min(
                json.indexOf(',', start) < 0 ? json.length() - 1 : json.indexOf(',', start),
                json.indexOf('}', start));
        return json.substring(start, end);
    }

    static void runTransform() {
        for (RawEvent event : dataLake) {
            WarehouseOrderFact fact = tryParse(event);
            if (fact != null) warehouse.add(fact); // invalid rows are simply SKIPPED here (improved in Level 3)
        }
    }

    public static void main(String[] args) {
        ingest(new RawEvent("order-service", "{\"orderId\":\"o1\",\"region\":\"EU\",\"amount\":100.0}"));
        ingest(new RawEvent("order-service", "{\"orderId\":\"o2\",\"region\":\"EU\",\"amount\":\"not-a-number\"}"));

        runTransform();

        System.out.println("Warehouse holds " + warehouse.size() + " valid fact(s): " + warehouse);
        System.out.println("(o2 was silently dropped -- Level 3 fixes this)");
    }
}
```

How to run: `java TransformToWarehouse.java`

`runTransform` walks every raw lake row and calls `tryParse`, which extracts fields with a small hand-rolled parser and attempts `Double.parseDouble` on the amount. For `o1` this succeeds, producing a `WarehouseOrderFact` added to `warehouse`. For `o2`, `Double.parseDouble("not-a-number")` throws `NumberFormatException`, `tryParse` catches it and returns `null`, and the row is skipped — the warehouse ends up with only one fact, and the malformed row simply vanishes without a trace.

### Level 3 — Advanced

```java
// File: TransformWithQuarantine.java -- invalid rows are QUARANTINED
// (kept, with a reason) instead of silently dropped, so data-quality
// issues are visible and fixable rather than invisible data loss.
import java.util.*;

public class TransformWithQuarantine {
    record RawEvent(String source, String rawJsonPayload) {}
    record WarehouseOrderFact(String orderId, String region, double amount) {}
    record QuarantinedRow(RawEvent original, String reason) {}

    static final List<RawEvent> dataLake = new ArrayList<>();
    static final List<WarehouseOrderFact> warehouse = new ArrayList<>();
    static final List<QuarantinedRow> quarantine = new ArrayList<>(); // rejected rows, WITH a reason

    static void ingest(RawEvent event) { dataLake.add(event); }

    static String extract(String json, String key) {
        String marker = "\"" + key + "\":";
        int i = json.indexOf(marker);
        if (i < 0) return null;
        int start = i + marker.length();
        boolean quoted = json.charAt(start) == '"';
        if (quoted) start++;
        int end = quoted ? json.indexOf('"', start) : Math.min(
                json.indexOf(',', start) < 0 ? json.length() - 1 : json.indexOf(',', start),
                json.indexOf('}', start));
        return json.substring(start, end);
    }

    static void runTransform() {
        for (RawEvent event : dataLake) {
            String orderId = extract(event.rawJsonPayload(), "orderId");
            String region = extract(event.rawJsonPayload(), "region");
            String amountStr = extract(event.rawJsonPayload(), "amount");

            if (orderId == null || region == null || amountStr == null) {
                quarantine.add(new QuarantinedRow(event, "missing required field"));
                continue;
            }
            try {
                warehouse.add(new WarehouseOrderFact(orderId, region, Double.parseDouble(amountStr)));
            } catch (NumberFormatException e) {
                quarantine.add(new QuarantinedRow(event, "amount not numeric: '" + amountStr + "'"));
            }
        }
    }

    public static void main(String[] args) {
        ingest(new RawEvent("order-service", "{\"orderId\":\"o1\",\"region\":\"EU\",\"amount\":100.0}"));
        ingest(new RawEvent("order-service", "{\"orderId\":\"o2\",\"region\":\"EU\",\"amount\":\"not-a-number\"}"));
        ingest(new RawEvent("order-service", "{\"region\":\"EU\",\"amount\":50.0}")); // missing orderId

        runTransform();

        System.out.println("Warehouse: " + warehouse.size() + " valid fact(s): " + warehouse);
        System.out.println("Quarantine: " + quarantine.size() + " rejected row(s), WITH reasons:");
        quarantine.forEach(q -> System.out.println("  " + q.reason() + " -- " + q.original().rawJsonPayload()));
    }
}
```

How to run: `java TransformWithQuarantine.java`

Now every raw row is guaranteed to end up somewhere visible: `o1` parses cleanly and lands in `warehouse`; the malformed-amount row lands in `quarantine` with the reason `"amount not numeric: 'not-a-number'"`; the row missing `orderId` lands in `quarantine` with the reason `"missing required field"`. Nothing is silently lost — an operator or data engineer can inspect `quarantine`, understand exactly why each row failed, and fix the upstream producer or the transform logic.

## 6. Walkthrough

Trace `TransformWithQuarantine.main` in order. **First**, three `ingest` calls run, appending three `RawEvent`s to `dataLake` exactly as given — no validation happens here, matching the lake's job of accepting data as-is.

**Next**, `runTransform()` iterates `dataLake` one event at a time. **For the first event** (`o1`, valid), `extract` successfully pulls `orderId="o1"`, `region="EU"`, `amountStr="100.0"`; none are `null`, so the code proceeds to `Double.parseDouble("100.0")`, which succeeds, and a `WarehouseOrderFact` is added to `warehouse`.

**For the second event** (`o2`, malformed amount), the three `extract` calls all succeed (all fields are present), so the `null`-check passes and the code reaches `Double.parseDouble("not-a-number")`, which throws `NumberFormatException`. The `catch` block adds a `QuarantinedRow` with reason `"amount not numeric: 'not-a-number'"`.

**For the third event** (missing `orderId`), `extract(json, "orderId")` returns `null` because the marker `"orderId":` isn't found in that JSON string. The `null`-check catches this immediately and adds a `QuarantinedRow` with reason `"missing required field"`, without ever attempting to parse the amount.

**Finally**, `main` prints both `warehouse` (containing exactly the one valid fact) and `quarantine` (containing both rejected rows, each annotated with why it failed) — giving a complete, auditable picture of what happened to every row that entered the pipeline.

```
ingest(o1 valid) ingest(o2 bad-amount) ingest(o3 missing-orderId)
      |
      v runTransform()
  o1 -> parses OK          -> warehouse
  o2 -> amount parse fails -> quarantine("amount not numeric")
  o3 -> orderId missing    -> quarantine("missing required field")
```

## 7. Gotchas & takeaways

> Silently dropping rows that fail validation (as in Level 2) is a common and dangerous mistake in ETL pipelines — the warehouse quietly under-reports, dashboards look plausible but are wrong, and nobody notices until a reconciliation audit turns up a discrepancy months later. Quarantining, not dropping, makes data loss visible and debuggable.

- The data lake accepts data as-is and cheaply, with no schema enforcement — that's its purpose, not a flaw.
- The data warehouse enforces structure and validity; the transform step between lake and warehouse (ELT: extract, load, then transform) is where data quality is actually enforced.
- Always quarantine or flag rows that fail transformation, with a reason, rather than silently dropping them — invisible data loss is far worse than a visibly incomplete warehouse.
- This pipeline pairs naturally with a [reporting/analytics database](0316-reporting-analytics-database.md): the warehouse often *is* that reporting store, or feeds it.
