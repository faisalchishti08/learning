---
card: spring-boot
gi: 162
slug: cassandra
title: Cassandra
---

## 1. What it is

**Apache Cassandra** is a distributed wide-column NoSQL database designed for linear scalability and high availability with no single point of failure. Spring Boot auto-configures it via `spring-boot-starter-data-cassandra`, providing a `CqlSession`, `CassandraTemplate`, and Spring Data Cassandra repositories. Connection is configured with `spring.cassandra.contact-points`, `spring.cassandra.keyspace-name`, and related properties.

## 2. Why & when

Use Cassandra when:

- **Write-heavy, massive scale** — millions of writes per second across geographically distributed datacentres.
- **Time-series data** — IoT sensor readings, event logs, metrics — insert-only, query by time window.
- **High availability requirements** — no master node; any node can serve reads and writes.
- **Multi-region replication** — data replicated across data centres for disaster recovery.

Avoid Cassandra for ad-hoc queries, joins, or transactional workloads. Data model must be designed around query patterns (denormalisation is expected).

## 3. Core concept

Cassandra uses **tables** but unlike SQL they are designed around access patterns. The **partition key** determines which node holds the data; **clustering columns** determine sort order within a partition.

```java
@Table("sensor_readings")
class SensorReading {
    @PrimaryKeyColumn(name = "sensor_id", type = PrimaryKeyType.PARTITIONED)
    String sensorId;
    @PrimaryKeyColumn(name = "timestamp", type = PrimaryKeyType.CLUSTERED,
                      ordering = Ordering.DESCENDING)
    Instant timestamp;
    double value;
}
```

CQL: `SELECT * FROM sensor_readings WHERE sensor_id = ? ORDER BY timestamp DESC LIMIT 100`

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">CassandraRepository</text>
  <rect x="240" y="55" width="170" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">CassandraTemplate</text>
  <rect x="240" y="115" width="170" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="325" y="139" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">CqlSession</text>
  <rect x="488" y="65" width="170" height="75" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="573" y="90" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Cassandra</text>
  <text x="573" y="107" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Node A / Node B</text>
  <text x="573" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">replication factor 3</text>
  <line x1="172" y1="105" x2="236" y2="78" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ca)"/>
  <line x1="325" y1="97" x2="325" y2="113" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ca2)"/>
  <line x1="412" y1="135" x2="484" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ca3)"/>
  <defs>
    <marker id="ca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ca2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="ca3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`CqlSession` distributes requests across Cassandra nodes; replication factor 3 means each partition is on three nodes — any node failure is transparent.

## 5. Runnable example

```java
// CassandraApp.java — Spring Boot project with spring-boot-starter-data-cassandra
// application.properties:
//   spring.cassandra.contact-points=localhost
//   spring.cassandra.port=9042
//   spring.cassandra.keyspace-name=demo
//   spring.cassandra.local-datacenter=datacenter1
//   spring.cassandra.schema-action=CREATE_IF_NOT_EXISTS
// Start Cassandra: docker run -p 9042:9042 cassandra:4

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.cassandra.core.cql.PrimaryKeyType;
import org.springframework.data.cassandra.core.mapping.*;
import org.springframework.data.cassandra.repository.CassandraRepository;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@SpringBootApplication
public class CassandraApp {
    public static void main(String[] args) {
        SpringApplication.run(CassandraApp.class, args);
    }
}

@Table("events")
class Event {
    @PrimaryKeyColumn(name = "category", type = PrimaryKeyType.PARTITIONED)
    String category;
    @PrimaryKeyColumn(name = "id", type = PrimaryKeyType.CLUSTERED)
    UUID id = UUID.randomUUID();
    String description;
    Event() {}
    Event(String category, String description) {
        this.category = category;
        this.description = description;
    }
    public String getCategory() { return category; }
    public UUID getId() { return id; }
    public String getDescription() { return description; }
}

interface EventRepo extends CassandraRepository<Event, UUID> {
    List<Event> findByCategory(String category);
}

@RestController
@RequestMapping("/events")
class EventController {

    private final EventRepo repo;

    EventController(EventRepo repo) { this.repo = repo; }

    @PostMapping
    public Event create(@RequestBody Event e) { return repo.save(e); }

    @GetMapping("/{category}")
    public List<Event> byCategory(@PathVariable String category) {
        return repo.findByCategory(category);
    }
}
```

**How to run:**
1. Start Cassandra: `docker run -p 9042:9042 cassandra:4`
2. Wait ~30 s for startup; `spring.cassandra.schema-action=CREATE_IF_NOT_EXISTS` auto-creates the keyspace and table.
3. Add `spring-boot-starter-data-cassandra` to `pom.xml`, start the app.
4. `curl -X POST http://localhost:8080/events -H 'Content-Type: application/json' -d '{"category":"login","description":"User alice logged in"}'`
5. `curl http://localhost:8080/events/login` → all login events.

## 6. Walkthrough

- `CassandraAutoConfiguration` creates a `CqlSession` from `spring.cassandra.contact-points` and `spring.cassandra.keyspace-name`. `CassandraDataAutoConfiguration` registers `CassandraTemplate` and enables repository scanning.
- `spring.cassandra.schema-action=CREATE_IF_NOT_EXISTS` tells Spring Data Cassandra to auto-create the keyspace (specified separately) and all `@Table`-annotated tables if absent — useful for dev; use `NONE` in production with explicit CQL schema scripts.
- `@PrimaryKeyColumn(type = PrimaryKeyType.PARTITIONED)` marks `category` as the partition key — all events in the same category live on the same set of replica nodes, making `WHERE category = ?` queries efficient.
- `@PrimaryKeyColumn(type = PrimaryKeyType.CLUSTERED)` marks `id` as a clustering column — events within a category are sorted by `id` (UUID time-ordered if using `UUID.randomUUID()`; use `UUIDs.timeBased()` for true time ordering).
- `findByCategory(category)` generates `SELECT * FROM events WHERE category = ?` — a single-partition scan, the most efficient Cassandra query pattern.

## 7. Gotchas & takeaways

> Cassandra queries **must** include the full partition key. A `SELECT * FROM events` full-table scan is allowed only with `ALLOW FILTERING` — never use it in production; it scans every node.

> Cassandra provides **eventual consistency** by default. Use `ConsistencyLevel.QUORUM` for read-your-writes guarantees at the cost of latency; `LOCAL_QUORUM` for multi-DC deployments.

- `spring.cassandra.request.consistency=local-quorum` sets the default consistency level for all operations.
- Updates in Cassandra are upserts — there is no difference between `INSERT` and `UPDATE` at the storage level.
- Cassandra has no joins — denormalise data and write to multiple tables to support different query patterns.
- For reactive Cassandra (WebFlux), use `spring-boot-starter-data-cassandra-reactive` and `ReactiveCassandraRepository`.
- `spring.cassandra.local-datacenter` must match the data centre name reported by `DESCRIBE DATACENTER` in `cqlsh`.
