---
card: spring-boot
gi: 165
slug: influxdb-legacy
title: InfluxDB (legacy)
---

## 1. What it is

**InfluxDB** is a time-series database optimised for storing and querying metrics, events, and real-time analytics — data that is always associated with a timestamp. Spring Boot 2.x included auto-configuration for InfluxDB via `spring.influx.*` properties (using the InfluxDB Java client v1). This auto-configuration is **not present in Spring Boot 3.x** — the InfluxDB v2 Java client must be configured manually. The "legacy" label in Spring Boot documentation refers to this removed Spring Boot 2.x auto-configuration; the database itself is still actively developed.

## 2. Why & when

Use InfluxDB when:

- **Application metrics** — CPU, memory, request rates, error counts over time.
- **IoT time-series** — temperature, pressure, GPS readings from sensors.
- **Business KPIs over time** — daily active users, revenue per hour, funnel conversion rates.
- **Alerting** — InfluxDB integrates with Grafana and InfluxDB's own Flux alerting engine.

InfluxDB is purpose-built for time-series — inserts are 10–100× faster than a relational database for time-stamped records, and `GROUP BY time()` downsampling queries are first-class citizens.

## 3. Core concept

InfluxDB stores data as **measurements** (analogous to tables) with **tags** (indexed string metadata) and **fields** (numeric or string values). All points have a **timestamp**.

```
measurement: cpu_usage
  tags:       host=server1, region=us-east
  fields:     value=72.5
  timestamp:  2024-01-15T10:30:00Z
```

**Line protocol** (wire format for writes):
```
cpu_usage,host=server1,region=us-east value=72.5 1705315800000000000
```

**Flux query** (InfluxDB v2):
```flux
from(bucket: "metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "cpu_usage")
  |> mean()
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="145" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="92" y="103" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Spring Actuator</text>
  <text x="92" y="120" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Micrometer metrics</text>
  <rect x="240" y="55" width="170" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">InfluxMeterRegistry</text>
  <rect x="240" y="115" width="170" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="325" y="139" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">WriteApi (HTTP)</text>
  <rect x="487" y="80" width="170" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="572" y="110" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">InfluxDB</text>
  <line x1="167" y1="105" x2="236" y2="78" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ix)"/>
  <line x1="325" y1="97" x2="325" y2="113" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ix2)"/>
  <line x1="412" y1="135" x2="483" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ix3)"/>
  <defs>
    <marker id="ix" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ix2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="ix3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Micrometer's `InfluxMeterRegistry` batches metric points and writes them via line protocol to InfluxDB's HTTP API.

## 5. Runnable example

```java
// InfluxApp.java — Spring Boot 3.x, manual InfluxDB v2 client configuration
// pom.xml: spring-boot-starter-actuator, com.influxdb:influxdb-client-java
// application.properties:
//   management.influx.metrics.export.uri=http://localhost:8086
//   management.influx.metrics.export.token=my-token
//   management.influx.metrics.export.org=my-org
//   management.influx.metrics.export.bucket=metrics
//   management.influx.metrics.export.step=10s
// Start InfluxDB: docker run -p 8086:8086 influxdb:2.7

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.InfluxDBClientFactory;
import com.influxdb.client.WriteApiBlocking;
import com.influxdb.client.domain.WritePrecision;
import com.influxdb.client.write.Point;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.List;

@SpringBootApplication
public class InfluxApp {
    public static void main(String[] args) {
        SpringApplication.run(InfluxApp.class, args);
    }
}

@Configuration
class InfluxConfig {
    @Bean
    public InfluxDBClient influxDBClient() {
        return InfluxDBClientFactory.create(
            "http://localhost:8086",
            "my-token".toCharArray(),
            "my-org",
            "metrics"
        );
    }
}

@RestController
@RequestMapping("/metrics")
class MetricsController {

    private final WriteApiBlocking writeApi;

    MetricsController(InfluxDBClient client) {
        this.writeApi = client.getWriteApiBlocking();
    }

    // Write a single metric point
    @PostMapping
    public String write(@RequestParam String measurement,
                        @RequestParam String host,
                        @RequestParam double value) {
        Point point = Point.measurement(measurement)
            .addTag("host", host)
            .addField("value", value)
            .time(Instant.now(), WritePrecision.NS);
        writeApi.writePoint(point);
        return "Written: " + measurement + "{host=" + host + "} = " + value;
    }
}
```

**How to run:**
1. Start InfluxDB: `docker run -p 8086:8086 -e DOCKER_INFLUXDB_INIT_MODE=setup -e DOCKER_INFLUXDB_INIT_USERNAME=admin -e DOCKER_INFLUXDB_INIT_PASSWORD=password -e DOCKER_INFLUXDB_INIT_ORG=my-org -e DOCKER_INFLUXDB_INIT_BUCKET=metrics -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-token influxdb:2.7`
2. Add `influxdb-client-java` to `pom.xml`, start the app.
3. `curl -X POST "http://localhost:8080/metrics?measurement=cpu_usage&host=server1&value=72.5"`
4. Query via InfluxDB UI at `http://localhost:8086`.

## 6. Walkthrough

- **Spring Boot 2.x auto-configuration** (removed in 3.x): `InfluxAutoConfiguration` created an `InfluxDB` v1 client from `spring.influx.url`, `spring.influx.user`, and `spring.influx.password`. This is the "legacy" reference in the docs.
- **Spring Boot 3.x + Micrometer**: The recommended approach for metrics is `management.influx.metrics.export.*` which configures Micrometer's `InfluxMeterRegistry`. This pushes Spring Actuator metrics (JVM heap, HTTP request rates, custom `Counter`/`Gauge` meters) to InfluxDB v2 automatically on the configured `step` interval.
- **Manual InfluxDB v2 client** (shown in example): `InfluxDBClientFactory.create(url, token, org, bucket)` creates a client with the v2 authentication model (token-based, no username/password). `WriteApiBlocking.writePoint(point)` sends a single point synchronously.
- `Point.measurement("cpu_usage").addTag("host", host).addField("value", value).time(Instant.now(), WritePrecision.NS)` constructs a line protocol point: measurement name, tags (indexed, string), fields (values), and nanosecond timestamp.
- Tags are indexed and used in `WHERE` clauses (like `host = "server1"`); fields are the actual measurements and cannot be used as filter criteria without a full scan.

## 7. Gotchas & takeaways

> Spring Boot 3.x removed `spring.influx.*` properties and the `InfluxDB` v1 client auto-configuration entirely. Migrating from Boot 2.x: switch to `management.influx.metrics.export.*` for Micrometer, or configure the v2 client (`com.influxdb:influxdb-client-java`) manually.

> Tags must be **low-cardinality** (e.g., host names, regions, status codes). Using high-cardinality values (user IDs, request IDs) as tags causes the **time-series cardinality explosion** problem — millions of unique tag combinations bloat InfluxDB's index and degrade performance severely.

- InfluxDB v2 uses **token-based authentication**; the v1 username/password model is unavailable in v2 (unless v1 compatibility mode is enabled).
- `management.influx.metrics.export.compressed=true` gzip-compresses writes — reduces bandwidth for high-frequency metric exports.
- InfluxDB's **continuous queries** (v1) / **tasks** (v2) downsample raw data to lower resolution for long-term storage, keeping the database size manageable.
- `WriteApi` (async) vs `WriteApiBlocking` (sync): use async in production for throughput; use blocking in tests for deterministic ordering.
