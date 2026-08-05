---
card: system-design
gi: 86
slug: spring-data-cassandra
title: Spring Data Cassandra
---

## 1. What it is

**Spring Data Cassandra** brings the same repository pattern to Apache Cassandra, a wide-column store. `@Table` marks a Java class as mapping to a Cassandra table, `@PrimaryKeyColumn` marks which fields form the partition key and clustering columns, and a repository extending `CassandraRepository<T, ID>` provides `save` and derived query methods — but, unlike JPA or MongoDB, only for queries Cassandra can actually execute efficiently, given the table's designed partition key.

## 2. Why & when

Cassandra's core constraint — efficient queries must include the partition key, covered in the wide-column stores tutorial earlier in this section — carries directly into Spring Data Cassandra: it will not silently generate an inefficient full-cluster-scan query the way a relational repository might generate a slow but working query. Use it for Spring applications that need Cassandra's write-throughput and horizontal-scale characteristics, and be prepared to design your `@Table` classes around specific access patterns from the start, exactly as the access-pattern-first modeling tutorial describes.

## 3. Core concept

**`@Table` with an explicit partition key and clustering column:**

```java
@Table("events_by_device")
public class DeviceEvent {
    @PrimaryKeyColumn(name = "device_id", type = PrimaryKeyType.PARTITIONED)
    private String deviceId; // the partition key: determines which node stores this row

    @PrimaryKeyColumn(name = "event_time", type = PrimaryKeyType.CLUSTERED, ordering = Ordering.DESCENDING)
    private Instant eventTime; // the clustering column: sort order WITHIN the partition

    private double value;
}

public interface DeviceEventRepository extends CassandraRepository<DeviceEvent, String> {
    List<DeviceEvent> findByDeviceId(String deviceId); // efficient: uses the partition key directly
}
```

**Why a query on a non-key field is rejected, not just slow:** unlike Spring Data JPA, which will happily generate a `findByValue(double value)` method backed by a full table scan, Spring Data Cassandra requires that query to be supported by the table's actual key structure (or an explicitly created secondary index) — attempting an unsupported derived query typically fails at startup or throws at query time, rather than silently running an expensive scan.

**One table per access pattern, mirrored in the repository layer:** because Cassandra needs a separate, differently-keyed table for each access pattern (as covered earlier), a Spring Data Cassandra application typically has multiple `@Table` classes for what is conceptually the same underlying data — `events_by_device` and, for a different query need, a separately maintained `events_by_time` table — each with its own repository interface.

**Writing to multiple tables explicitly:** because Spring Data Cassandra will not automatically fan a single save out to multiple differently-keyed tables for you, the application's service layer is responsible for writing to every table an access pattern needs, mirroring the fan-out write from the access-pattern-first modeling tutorial.

## 4. Diagram

```
@Table("events_by_device")                       @Table("events_by_time")
  partition key: deviceId                          partition key: (some time bucket)
  clustering:    eventTime DESC                     clustering:    deviceId
        |                                                  |
        v                                                  v
DeviceEventRepository                            EventsByTimeRepository
  findByDeviceId(id)  -- EFFICIENT               findByTimeBucket(bucket) -- EFFICIENT
  (uses the partition key directly)               (uses ITS OWN partition key directly)

  findByValue(v)  -- REJECTED / unsupported: no partition key involved, would need a full scan
```
*Caption: Spring Data Cassandra only generates queries the table's partition key can actually serve efficiently; a different access pattern needs a different table.*

## 5. Runnable example

### Artifact: a minimal Java sketch modeling partition-key-constrained query generation in Spring Data Cassandra

```java
import java.util.*;

public class SpringDataCassandraSim {

    record DeviceEvent(String deviceId, String eventTime, double value) {}

    // Simulates the events_by_device table: partitioned by deviceId, clustered by eventTime.
    static final Map<String, TreeMap<String, Double>> eventsByDevice = new HashMap<>();

    static void insert(String deviceId, String eventTime, double value) {
        eventsByDevice.computeIfAbsent(deviceId, d -> new TreeMap<>(Comparator.reverseOrder())).put(eventTime, value);
    }

    // Efficient: uses the partition key directly - this is what a real derived query method generates.
    static List<DeviceEvent> findByDeviceId(String deviceId) {
        List<DeviceEvent> results = new ArrayList<>();
        for (Map.Entry<String, Double> e : eventsByDevice.getOrDefault(deviceId, new TreeMap<>()).entrySet()) {
            results.add(new DeviceEvent(deviceId, e.getKey(), e.getValue()));
        }
        return results;
    }

    // Modeling what Spring Data Cassandra REJECTS: a query with no partition key, would need a full scan.
    static List<DeviceEvent> findByValueUnsupported(double value) {
        throw new UnsupportedOperationException(
            "Cassandra cannot efficiently query by 'value' - it is not part of the partition key; " +
            "Spring Data Cassandra rejects this derived method rather than silently running a full-cluster scan");
    }

    public static void main(String[] args) {
        insert("device-42", "10:00", 70.8);
        insert("device-42", "10:01", 71.0);
        insert("device-99", "10:01", 68.5);

        System.out.println("findByDeviceId(\"device-42\") - efficient, uses the partition key:");
        for (DeviceEvent e : findByDeviceId("device-42")) {
            System.out.println("  " + e.eventTime() + " -> " + e.value());
        }

        System.out.println("attempting findByValue(70.8) - a query the table's key cannot serve:");
        try {
            findByValueUnsupported(70.8);
        } catch (UnsupportedOperationException e) {
            System.out.println("  REJECTED: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `SpringDataCassandraSim.java`, run `java SpringDataCassandraSim.java` (JDK 17+). A real Spring Boot app needs the `spring-boot-starter-data-cassandra` dependency, a running Cassandra cluster, and `@Table` classes with explicit `@PrimaryKeyColumn` annotations as shown above.

## 6. Walkthrough

1. `insert` writes into `eventsByDevice`, keyed first by `deviceId` (the partition key) and then sorted by `eventTime` within that partition (the clustering column) — mirroring the `@Table` definition's key structure.
2. `findByDeviceId("device-42")` reads only that device's partition, already sorted, mirroring how a real `findByDeviceId` derived query method executes efficiently against Cassandra's partition structure.
3. `findByValueUnsupported` deliberately throws, modeling the real behavior difference from Spring Data JPA: Cassandra's repository layer will not generate a query for a field outside the table's key structure, because doing so would require an inefficient full-cluster scan that Cassandra is not designed to support well.
4. The `try`/`catch` around the call to `findByValueUnsupported` confirms this is treated as a rejected, unsupported operation — not a slow-but-working query the way the equivalent call would behave against a relational database.

## 7. Gotchas & takeaways

> **Gotcha:** a new feature requiring a query on a field outside the existing table's partition key is not a quick fix — it typically means creating a new, differently-keyed `@Table` and a new repository, then writing (and, for a live migration, backfilling) data into it, exactly the "one table per access pattern" cost the wide-column stores and access-pattern-first modeling tutorials describe.

- Spring Data Cassandra deliberately mirrors the JPA and MongoDB repository patterns for consistency, but enforces Cassandra's partition-key constraint at the query-generation level, rejecting unsupported queries rather than running them inefficiently.
- Real Cassandra applications typically maintain several `@Table` classes for the same conceptual data, one per access pattern, each with its own repository.
- Related concepts: [Wide-column stores](0077-wide-column-stores.md) (the underlying store and its partition-key constraints), [Access-pattern-first data modeling](0082-access-pattern-first-data-modeling.md) (the modeling discipline this API's constraints directly enforce).
