---
card: microservices
gi: 150
slug: spring-kafka-streams-support
title: "Spring Kafka Streams support"
---

## 1. What it is

Spring's Kafka Streams support wires the Kafka Streams library — a stream processing library built directly on Kafka, expressing computations as a topology of transformations over `KStream`s (event streams) and `KTable`s (the [table view of a stream](0142-stream-table-duality.md)) — into Spring Boot's dependency injection and configuration, letting a `@Bean` define a Kafka Streams topology using ordinary Spring configuration instead of raw `Properties` and manual `KafkaStreams` lifecycle management.

## 2. Why & when

Plain Kafka Streams applications configure and manage a `KafkaStreams` instance's lifecycle (start, close, error handling, state store recovery) manually, and building the actual processing topology involves a fair amount of boilerplate around properties and serializers even before any real business logic appears. Spring's support auto-configures the streams properties from `application.yml`, manages the `KafkaStreams` lifecycle alongside the application's own, and lets the topology itself be defined as a `@Bean` returning a `KStream` pipeline built with the Streams DSL — keeping the actual computation (`filter`, `map`, `groupByKey`, `aggregate`) as the focus, with the surrounding plumbing handled by Spring.

Reach for this when a service needs genuine [stream processing](0138-stream-processing-concepts.md) capabilities — [windowed aggregations](0143-windowing-aggregation.md), stream-table joins, stateful transformations — directly against Kafka, and is already a Spring Boot application benefiting from Spring's configuration and lifecycle management elsewhere. For simple produce/consume without stateful aggregation, plain [`KafkaTemplate`/`@KafkaListener`](0149-spring-for-apache-kafka-kafkatemplate-kafkalistener.md) or [Spring Cloud Stream](0146-spring-cloud-stream-functional-programming-model-supplier-fu.md) are simpler, more appropriate tools.

## 3. Core concept

A `@Bean` method returns a `Function<KStream<K, V>, KStream<K, R>>` (or builds a topology directly against a `StreamsBuilder`), and Spring's auto-configuration handles constructing the underlying `KafkaStreams` instance, wiring it to the configured input/output topics, and managing its start/stop lifecycle alongside the application context.

```java
@Bean
public Function<KStream<String, OrderPlaced>, KStream<String, Long>> orderCountByRegion() {
    return stream -> stream
        .groupBy((key, order) -> order.region())      // re-key by region
        .count(Materialized.as("order-counts-store"))  // stateful aggregation, backed by a state store
        .toStream(); // back to a KStream for the framework to publish downstream
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Spring-managed Kafka Streams topology reads a KStream of order events, groups and counts them by region using a stateful aggregation backed by a local state store, and emits the running counts as an output KStream" >
  <rect x="20" y="60" width="140" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="87" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">KStream: order-events</text>

  <rect x="220" y="55" width="200" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="78" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">groupBy(region).count()</text>
  <text x="320" y="94" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">state store: order-counts-store</text>

  <rect x="480" y="60" width="140" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="87" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">KStream: counts out</text>

  <line x1="160" y1="82" x2="218" y2="82" stroke="#8b949e" marker-end="url(#arr31)"/>
  <line x1="420" y1="82" x2="478" y2="82" stroke="#8b949e" marker-end="url(#arr31)"/>

  <defs>
    <marker id="arr31" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The topology's stateful aggregation is backed by a local state store, managed automatically alongside the stream itself.

## 5. Runnable example

Scenario: a per-region order counting job that starts as a naive, non-incremental recomputation over a growing list (highlighting why a real streams engine avoids this), becomes an incrementally-updated stateful aggregation mirroring `groupBy().count()`'s actual behavior, and finally adds a second, chained aggregation stage to show a multi-step topology composing cleanly.

### Level 1 — Basic

```java
// File: NaiveRecomputation.java -- recomputes the ENTIRE count from scratch on
// every new event, the inefficient approach a real streams engine avoids.
import java.util.*;

public class NaiveRecomputation {
    record OrderPlaced(int orderId, String region) {}

    public static void main(String[] args) {
        List<OrderPlaced> allEventsEverSeen = new ArrayList<>();
        String[] incoming = {"US", "EU", "US", "APAC", "US"};

        for (int i = 0; i < incoming.length; i++) {
            allEventsEverSeen.add(new OrderPlaced(i, incoming[i]));

            // NAIVE: recompute the FULL count from the entire history, every single time
            Map<String, Long> counts = new TreeMap<>();
            for (OrderPlaced e : allEventsEverSeen) counts.merge(e.region(), 1L, Long::sum);
            System.out.println("After event " + i + ": " + counts + " (recomputed from ALL " + allEventsEverSeen.size() + " events)");
        }
        System.out.println("This gets slower and slower as history grows -- O(n) work per event, O(n^2) total.");
    }
}
```

**How to run:** `javac NaiveRecomputation.java && java NaiveRecomputation` (JDK 17+).

Every new event triggers a full re-scan of all events ever seen — correct, but the per-event cost grows linearly with total history, which does not scale.

### Level 2 — Intermediate

```java
// File: IncrementalAggregation.java -- mirrors groupBy().count()'s ACTUAL behavior:
// state is updated incrementally, O(1) work per event, backed by a state store.
import java.util.*;

public class IncrementalAggregation {
    record OrderPlaced(int orderId, String region) {}

    // simulates a Kafka Streams state store: a persistent, incrementally-updated key-value store
    static class StateStore {
        Map<String, Long> counts = new TreeMap<>();
        void increment(String key) { counts.merge(key, 1L, Long::sum); } // O(1), NOT a full rescan
    }

    public static void main(String[] args) {
        StateStore orderCountsStore = new StateStore(); // mirrors Materialized.as("order-counts-store")
        String[] incoming = {"US", "EU", "US", "APAC", "US"};

        for (int i = 0; i < incoming.length; i++) {
            orderCountsStore.increment(incoming[i]); // INCREMENTAL update, no rescan of history
            System.out.println("After event " + i + " (region=" + incoming[i] + "): " + orderCountsStore.counts);
        }
        System.out.println("Each event does CONSTANT work, regardless of how much history has accumulated -- this is how groupBy().count() actually behaves.");
    }
}
```

**How to run:** `javac IncrementalAggregation.java && java IncrementalAggregation` (JDK 17+).

Expected output:
```
After event 0 (region=US): {US=1}
After event 1 (region=EU): {EU=1, US=1}
After event 2 (region=US): {EU=1, US=2}
After event 3 (region=APAC): {APAC=1, EU=1, US=2}
After event 4 (region=US): {APAC=1, EU=1, US=3}
Each event does CONSTANT work, regardless of how much history has accumulated -- this is how groupBy().count() actually behaves.
```

Unlike Level 1, `increment` touches only the single relevant counter, not the entire history — exactly mirroring how a real Kafka Streams state store handles a `groupBy().count()` topology.

### Level 3 — Advanced

```java
// File: ChainedTopologyStages.java -- a SECOND aggregation stage chained onto the
// first, mirroring how Kafka Streams topologies compose multiple processing steps.
import java.util.*;

public class ChainedTopologyStages {
    record OrderPlaced(int orderId, String region, double amount) {}

    static class StateStore<V> {
        Map<String, V> data = new TreeMap<>();
    }

    public static void main(String[] args) {
        // STAGE 1: count orders per region (as in Level 2)
        StateStore<Long> orderCountsStore = new StateStore<>();
        // STAGE 2: a SEPARATE, chained aggregation -- total revenue per region, from the SAME input stream
        StateStore<Double> revenueStore = new StateStore<>();
        // STAGE 3: derived from stage 1 AND 2 together -- average order value per region
        StateStore<Double> avgOrderValueStore = new StateStore<>();

        OrderPlaced[] incoming = {
            new OrderPlaced(1, "US", 100.0), new OrderPlaced(2, "EU", 50.0),
            new OrderPlaced(3, "US", 200.0), new OrderPlaced(4, "US", 150.0)
        };

        for (OrderPlaced order : incoming) {
            // stage 1: incremental count, exactly as Level 2
            orderCountsStore.data.merge(order.region(), 1L, Long::sum);
            // stage 2: incremental sum, a SEPARATE aggregation over the SAME input stream
            revenueStore.data.merge(order.region(), order.amount(), Double::sum);
            // stage 3: derived from BOTH prior stages, recomputed each time from their current state
            long count = orderCountsStore.data.get(order.region());
            double revenue = revenueStore.data.get(order.region());
            avgOrderValueStore.data.put(order.region(), revenue / count);

            System.out.println("Region " + order.region() + ": count=" + count + " revenue=" + revenue + " avg=" + String.format("%.2f", revenue / count));
        }

        System.out.println("Final counts:  " + orderCountsStore.data);
        System.out.println("Final revenue: " + revenueStore.data);
        System.out.println("Final avg:     " + avgOrderValueStore.data);
    }
}
```

**How to run:** `javac ChainedTopologyStages.java && java ChainedTopologyStages` (JDK 17+).

Expected output:
```
Region US: count=1 revenue=100.0 avg=100.00
Region EU: count=1 revenue=50.0 avg=50.00
Region US: count=2 revenue=300.0 avg=150.00
Region US: count=3 revenue=450.0 avg=150.00
Final counts:  {EU=1, US=3}
Final revenue: {EU=50.0, US=300.0}
Final avg:     {EU=50.0, US=150.0}
```

## 6. Walkthrough

1. **Level 1** — the inner `for` loop inside the outer loop iterates `allEventsEverSeen` from scratch every single time a new event arrives, meaning the tenth event triggers a scan of all ten events, the hundredth would scan all hundred, and so on — clearly correct but structurally the opposite of how a production streams engine operates.
2. **Level 2, the state store abstraction** — `StateStore.increment` performs a single `Map.merge` call touching only the specific region key relevant to the current event, doing a fixed, constant amount of work regardless of how many prior events have been processed.
3. **Level 2, matching real behavior** — this is precisely what `KStream.groupBy(...).count()` does internally in real Kafka Streams: maintain a persistent, incrementally-updated state store (backed by RocksDB and a Kafka changelog topic for fault tolerance) rather than replaying the full input stream on every new event.
4. **Level 3, three coordinated state stores** — `orderCountsStore`, `revenueStore`, and `avgOrderValueStore` each maintain their own independent, incrementally-updated map, modeling a topology with multiple aggregation stages processing the same input stream.
5. **Level 3, stages 1 and 2 as independent, parallel aggregations** — for each incoming `order`, both `orderCountsStore.data.merge(...)` and `revenueStore.data.merge(...)` are updated from the same single event, representing two separate `groupBy().count()`- and `groupBy().reduce()`-style aggregations both consuming the identical input `KStream`.
6. **Level 3, stage 3 derived from the other two** — `avgOrderValueStore.data.put(order.region(), revenue / count)` reads the *current* values from both `orderCountsStore` and `revenueStore` (not the full event history) to compute a derived metric, mirroring how a Kafka Streams topology can chain a `KTable`-to-`KTable` join or transformation on top of two upstream aggregations.
7. **Level 3, tracing the US region across three events** — after the first US order (amount 100.0), avg is 100.00; after the second US order (amount 200.0), count becomes 2 and revenue becomes 300.0, giving avg 150.00; after the third US order (amount 150.0), count becomes 3 and revenue becomes 450.0, giving avg 150.00 again (coincidentally unchanged, since the third order's amount matched the prior average) — each step reflects only the current accumulated state, never a full replay of prior individual order amounts.

## 7. Gotchas & takeaways

> **Gotcha:** local state stores back their state with an embedded store (RocksDB by default) *and* a Kafka changelog topic for fault tolerance — losing or corrupting the local state directory forces Kafka Streams to rebuild it from the changelog topic on restart, which can take real time proportional to how much state has accumulated; this recovery behavior is a genuine operational consideration, not just an implementation detail.

- Spring's Kafka Streams support wires the Kafka Streams library's topology and lifecycle into Spring Boot's configuration and dependency injection, reducing the manual `Properties` and lifecycle-management boilerplate of using the library directly.
- Stateful aggregations (`groupBy().count()`, `.reduce()`, `.aggregate()`) update a persistent state store incrementally, doing constant work per event rather than recomputing from full history.
- Multiple aggregation stages can be chained or run in parallel over the same input stream, with later stages reading from earlier stages' current state rather than replaying raw events.
- This tool fits genuine stateful stream processing needs; simple produce/consume without aggregation is better served by simpler tools like [`KafkaTemplate`/`@KafkaListener`](0149-spring-for-apache-kafka-kafkatemplate-kafkalistener.md).
- State stores are backed by both a local embedded store and a Kafka changelog topic for fault tolerance, and rebuilding lost local state from that changelog on restart is a real, time-proportional operational cost worth planning for.
