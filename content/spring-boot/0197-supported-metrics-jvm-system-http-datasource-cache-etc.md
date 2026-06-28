---
card: spring-boot
gi: 197
slug: supported-metrics-jvm-system-http-datasource-cache-etc
title: Supported metrics (JVM, system, HTTP, DataSource, cache, etc.)
---

## 1. What it is

Spring Boot auto-configures Micrometer `MeterBinder` beans that instrument common infrastructure components — no application code required. The moment a dependency is on the classpath and configured, its metrics appear in `/actuator/metrics`. These built-in metrics cover JVM internals, system resources, HTTP servers and clients, JDBC connection pools, caches, Kafka consumers, RabbitMQ, and more.

## 2. Why & when

Built-in metrics answer the most important operational questions before you write a single line of custom instrumentation:
- Is the JVM running out of memory? (`jvm.memory.used`, `jvm.gc.pause`)
- Are threads piling up? (`jvm.threads.live`, `jvm.threads.daemon`)
- Is the app overloaded? (`http.server.requests` rate and latency)
- Is the DB connection pool exhausted? (`hikaricp.connections.active`)
- Is the cache effective? (`cache.gets{outcome=hit}` vs `cache.gets{outcome=miss}`)

Add `starter-actuator` and the appropriate starters; monitoring starts automatically.

## 3. Core concept

Auto-instrumented metric families:

| Family | Metric names (sample) | Triggered by |
|---|---|---|
| **JVM memory** | `jvm.memory.used`, `jvm.memory.max`, `jvm.memory.committed` | Always (JVM) |
| **JVM GC** | `jvm.gc.pause`, `jvm.gc.memory.allocated`, `jvm.gc.live.data.size` | Always (JVM) |
| **JVM threads** | `jvm.threads.live`, `jvm.threads.daemon`, `jvm.threads.peak` | Always |
| **JVM classes** | `jvm.classes.loaded`, `jvm.classes.unloaded` | Always |
| **Process** | `process.cpu.usage`, `process.uptime`, `process.files.open` | Always |
| **System** | `system.cpu.usage`, `system.cpu.count`, `system.load.average.1m` | Always |
| **HTTP server** | `http.server.requests` | spring-boot-starter-web/webflux |
| **HTTP client** | `http.client.requests` | RestTemplate/WebClient/RestClient |
| **DataSource/HikariCP** | `hikaricp.connections.*` | spring-boot-starter-data-jpa/jdbc |
| **Cache** | `cache.gets`, `cache.puts`, `cache.evictions`, `cache.size` | spring-boot-starter-cache |
| **Kafka** | `kafka.consumer.records.consumed.rate`, `kafka.consumer.lag` | spring-boot-starter-kafka |
| **RabbitMQ** | `rabbitmq.published`, `rabbitmq.acknowledged` | spring-boot-starter-amqp |
| **Executor** | `executor.completed`, `executor.queue.size`, `executor.active` | spring-boot-starter-web (async) |
| **Logback** | `logback.events{level=error/warn/info}` | spring-boot + Logback |

All are enabled by default; disable with `management.metrics.enable.<family>=false`.

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot auto-configures MeterBinders for JVM, HTTP, DataSource, cache, messaging; all export to MeterRegistry">
  <!-- JVM/System -->
  <rect x="10" y="20" width="155" height="88" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="87" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">JVM + System</text>
  <text x="87" y="56" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">jvm.memory.used[area=heap]</text>
  <text x="87" y="70" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">jvm.gc.pause[action=...]</text>
  <text x="87" y="84" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">jvm.threads.live</text>
  <text x="87" y="98" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">process.cpu.usage</text>

  <!-- HTTP -->
  <rect x="10" y="118" width="155" height="72" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="87" y="137" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">HTTP</text>
  <text x="87" y="153" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">http.server.requests[method,uri,status]</text>
  <text x="87" y="167" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">http.client.requests</text>
  <text x="87" y="181" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">executor.active  logback.events</text>

  <!-- All feed into registry -->
  <line x1="168" y1="65" x2="270" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sma)"/>
  <line x1="168" y1="160" x2="270" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sma)"/>

  <!-- DataSource/Cache -->
  <rect x="280" y="20" width="155" height="88" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="357" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">DataSource + Cache</text>
  <text x="357" y="56" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">hikaricp.connections.active</text>
  <text x="357" y="70" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">hikaricp.connections.pending</text>
  <text x="357" y="84" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">cache.gets[outcome=hit/miss]</text>
  <text x="357" y="98" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">cache.size  cache.evictions</text>

  <!-- Messaging -->
  <rect x="280" y="118" width="155" height="72" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="357" y="137" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Messaging</text>
  <text x="357" y="153" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">kafka.consumer.records.lag</text>
  <text x="357" y="167" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">rabbitmq.published</text>
  <text x="357" y="181" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">spring.kafka.listener.seconds</text>

  <line x1="357" y1="112" x2="440" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#smb)"/>
  <line x1="357" y1="190" x2="440" y2="112" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#smb)"/>

  <!-- MeterRegistry -->
  <rect x="445" y="80" width="145" height="55" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="517" y="102" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">MeterRegistry</text>
  <text x="517" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">all auto-meters</text>

  <!-- Export -->
  <line x1="592" y1="107" x2="650" y2="107" stroke="#6db33f" stroke-width="2" marker-end="url(#sma)"/>
  <rect x="655" y="85" width="55" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="682" y="109" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Prom</text>

  <defs>
    <marker id="sma" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="smb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Auto-instrumented metric families feed into the registry with zero application code.

## 5. Runnable example

```java
// SupportedMetricsDemo.java — catalogues key auto-instrumented metrics and their usage
// How to run: java SupportedMetricsDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add starter-actuator; metrics appear in /actuator/metrics automatically

import java.util.*;

public class SupportedMetricsDemo {

    record MetricInfo(String name, String unit, String tags, String query, String diagnostic) {}

    public static void main(String[] args) {
        System.out.println("=== Spring Boot Auto-instrumented Metrics ===\n");

        List<MetricInfo> metrics = List.of(
            // JVM Memory
            new MetricInfo("jvm.memory.used",        "bytes",
                "area={heap|nonheap}, id={G1 Heap|Metaspace|...}",
                "?tag=area:heap", "Is heap growing towards max? OOM risk?"),
            new MetricInfo("jvm.memory.max",         "bytes",
                "area, id",
                "?tag=area:heap", "Configured heap size (-Xmx)"),
            new MetricInfo("jvm.gc.pause",           "seconds",
                "action={end of major|end of minor GC}, cause",
                "", "GC stop-the-world duration — watch for spikes"),
            new MetricInfo("jvm.gc.memory.allocated","bytes", "",
                "", "Allocation rate — high rate = GC pressure"),

            // JVM Threads
            new MetricInfo("jvm.threads.live",       "threads", "state={runnable|blocked|waiting}",
                "", "Runnable threads growing? Thread pool exhausted?"),
            new MetricInfo("jvm.threads.peak",       "threads", "",
                "", "Max concurrent threads ever seen"),

            // System
            new MetricInfo("process.cpu.usage",      "1 (ratio)", "",
                "", "0=idle, 1=100% CPU — alert if sustained > 0.8"),
            new MetricInfo("system.load.average.1m", "load", "",
                "", "Linux load average — compare to CPU count"),

            // HTTP server
            new MetricInfo("http.server.requests",   "seconds",
                "method, uri, status, outcome",
                "?tag=status:500", "Request rate, latency, error rate per endpoint"),

            // HTTP client
            new MetricInfo("http.client.requests",   "seconds",
                "method, uri, status, clientName",
                "?tag=outcome:SERVER_ERROR", "Downstream call latency and error rate"),

            // HikariCP
            new MetricInfo("hikaricp.connections.active",  "connections", "pool",
                "", "Active > max? Thread waiting for connection"),
            new MetricInfo("hikaricp.connections.pending", "connections", "pool",
                "", "Threads waiting for a connection — should be 0"),
            new MetricInfo("hikaricp.connections.timeout", "total", "pool",
                "", "Connection timeout count — critical alert threshold"),

            // Cache
            new MetricInfo("cache.gets",             "1", "name, outcome={hit|miss}, cacheManager",
                "?tag=outcome:miss", "Hit ratio: hit/(hit+miss) — low ratio = ineffective cache"),

            // Kafka
            new MetricInfo("kafka.consumer.records-consumed-rate", "records/sec", "client.id, topic",
                "", "Consumer throughput per topic"),
            new MetricInfo("kafka.consumer.fetch-latency-avg", "ms", "client.id",
                "", "Kafka fetch latency"),

            // Logback
            new MetricInfo("logback.events",         "1", "level={error|warn|info|debug}",
                "?tag=level:error", "ERROR spike = something is broken")
        );

        System.out.printf("%-44s %-10s %s%n", "Metric Name", "Unit", "What it tells you");
        System.out.println("-".repeat(100));
        metrics.forEach(m ->
            System.out.printf("%-44s %-10s %s%n",
                    m.name() + (m.tags().isEmpty() ? "" : "[...]"), m.unit(), m.diagnostic()));

        System.out.println("\n--- Disable specific metric families ---");
        System.out.println("management.metrics.enable.jvm=false        # all jvm.* metrics off");
        System.out.println("management.metrics.enable.process=false    # process.* off");
        System.out.println("management.metrics.enable.http.server=false # http.server.* off");

        System.out.println("\n--- Add global tag to all metrics ---");
        System.out.println("management.metrics.tags.application=order-service");
        System.out.println("management.metrics.tags.env=production");
        System.out.println("=> tag 'application=order-service' appears on every meter");
    }
}
```

**How to run:** `java SupportedMetricsDemo.java`

## 6. Walkthrough

- **`jvm.memory.used[area=heap]`**: the most-watched JVM metric. Alert when `used / max > 0.85` for sustained periods — approaching OOM. Each memory pool (G1 Heap, Metaspace, Code Cache) is a separate tag value.
- **`jvm.gc.pause`**: records the time the JVM paused all threads for GC. A p99 above 500 ms affects user-visible latency. G1GC and ZGC reduce pause times; enable if pauses are high.
- **`http.server.requests`**: the core HTTP SLO metric. Filter by `tag=status:5xx` to get error rates; `tag=uri:/api/orders` to get per-endpoint latency. Always has `count`, `totalTime`, and `max` measurements.
- **`hikaricp.connections.pending`**: the key DB pool saturation signal. Any value > 0 for more than a few seconds means threads are waiting for DB connections — scale the pool or reduce query time.
- **`cache.gets[outcome=hit/miss]`**: hit ratio = `hit / (hit + miss)`. Below 80% usually means the cache key strategy or TTL is wrong.

## 7. Gotchas & takeaways

> `http.server.requests` tags include `uri` which by default uses the **template path** (`/api/orders/{id}`) not the actual path — preventing high-cardinality metric explosion. If you use non-template URLs, Spring uses `"UNKNOWN"` as the URI tag.

> `hikaricp.*` metrics require **HikariCP** as the connection pool (the default in Spring Boot). If you've replaced HikariCP with another pool, these metrics won't appear.

- `GET /actuator/metrics` lists all metric names. Use `?tag=level:error` filters to narrow: `GET /actuator/metrics/logback.events?tag=level:error`.
- Add `management.metrics.distribution.percentiles.http.server.requests=0.5,0.95,0.99` to publish percentile measurements for HTTP requests.
- `management.metrics.distribution.slo.http.server.requests=50ms,200ms,1000ms` adds SLO histogram buckets for Prometheus SLA tracking.
- `Executor` metrics (`executor.*`) appear automatically for any `ThreadPoolExecutor` registered as a Spring bean.
- Kafka consumer lag (`kafka.consumer.records-lag`) is the key streaming health metric: sustained lag → consumers are not keeping up with producers.
