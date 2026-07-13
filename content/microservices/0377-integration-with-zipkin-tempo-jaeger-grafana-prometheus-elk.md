---
card: microservices
gi: 377
slug: integration-with-zipkin-tempo-jaeger-grafana-prometheus-elk
title: "Integration with Zipkin / Tempo / Jaeger / Grafana / Prometheus / ELK"
---

## 1. What it is

This topic ties together the concrete observability backend tools a Spring Boot microservices system typically integrates with: **Zipkin**, **Tempo**, and **Jaeger** are trace storage/visualization backends (receiving spans from [Micrometer Tracing](0369-micrometer-tracing-brave-opentelemetry-bridges.md), directly or via OTLP); **Prometheus** is the dominant pull-based metrics backend (receiving data from a [Micrometer Prometheus registry](0367-micrometer-registries-prometheus-datadog-etc.md)); **Grafana** is the visualization layer that queries Prometheus (and often Tempo/Jaeger too) to render [dashboards](0364-dashboards-visualization.md); and the **ELK stack** (Elasticsearch, Logstash, Kibana) is a common choice for [centralized log aggregation](0361-centralized-log-aggregation.md) and search.

## 2. Why & when

Every concept covered earlier in this section — metrics, traces, structured logs, dashboards — needs to actually land somewhere real to be useful, and these are the concrete, widely-deployed tools that fill each role. Knowing which tool handles which pillar (and that Grafana, notably, can visualize data from multiple of these backends at once) helps you understand how a typical production observability stack fits together rather than treating each tool as an isolated black box.

Pick backends matching your organization's existing infrastructure or preferences: Prometheus + Grafana is an extremely common, often default, choice for metrics and dashboards; Tempo (increasingly, as it integrates cleanly with the Grafana ecosystem) or Jaeger or Zipkin for traces, depending on existing investment; ELK or a Loki-based alternative for logs. The specific tools matter less than making sure every pillar has *some* durable, queryable backend, correlated together (often via the correlation/trace ID threading through all of them), rather than any one pillar being left as ephemeral, unaggregated, per-instance data.

## 3. Core concept

Each backend receives data via its own expected protocol: Prometheus scrapes a `/actuator/prometheus`-style endpoint (pull); Zipkin/Jaeger typically receive spans pushed to their own ingestion API, or increasingly via OTLP through a Collector; ELK typically receives logs shipped by an agent (Filebeat/Logstash) reading structured JSON output. Grafana sits above several of these, configured with each as a "data source," letting one dashboard pull panels from Prometheus (metrics) and Tempo (traces) side by side.

```yaml
management:
  metrics:
    export:
      prometheus:
        enabled: true      # Prometheus scrapes /actuator/prometheus
  tracing:
    sampling:
      probability: 0.1
  zipkin:
    tracing:
      endpoint: http://zipkin:9411/api/v2/spans # or use OTLP to a Collector instead
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Spring Boot app sends metrics to Prometheus, traces to Tempo/Jaeger, and logs to ELK; Grafana queries both Prometheus and Tempo as data sources to render unified dashboards">
  <rect x="250" y="10" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="32" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Spring Boot app</text>

  <rect x="30" y="80" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Prometheus</text>
  <rect x="250" y="80" width="140" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Tempo / Jaeger / Zipkin</text>
  <rect x="470" y="80" width="140" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="540" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ELK</text>

  <line x1="280" y1="44" x2="120" y2="80" stroke="#8b949e" marker-end="url(#a377)"/>
  <line x1="320" y1="44" x2="320" y2="80" stroke="#8b949e" marker-end="url(#a377)"/>
  <line x1="360" y1="44" x2="540" y2="80" stroke="#8b949e" marker-end="url(#a377)"/>

  <line x1="100" y1="114" x2="220" y2="160" stroke="#79c0ff" marker-end="url(#a377b)"/>
  <line x1="320" y1="114" x2="260" y2="160" stroke="#79c0ff" marker-end="url(#a377b)"/>
  <rect x="180" y="160" width="160" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="260" y="182" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Grafana (dashboards)</text>

  <defs>
    <marker id="a377" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a377b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Each pillar's data lands in its own specialized backend; Grafana sits above several of them, unifying metrics and trace visualization in one dashboard.

## 5. Runnable example

Scenario: an order-placement operation, first with all three telemetry types produced but going nowhere (no backend integration), then routed to their respective simulated backends (Prometheus-style, Tempo-style, ELK-style), and finally shown as a unified Grafana-style dashboard pulling from both the metrics and tracing backends together.

### Level 1 — Basic

```java
// File: TelemetryProducedNoBackend.java -- metrics, traces, and logs are
// all RECORDED, but nothing ships any of them anywhere -- no backend
// integration at all, so none of it is actually usable operationally.
import java.util.*;

public class TelemetryProducedNoBackend {
    static Map<String, Integer> localMetrics = new HashMap<>();
    static List<String> localSpans = new ArrayList<>();
    static List<String> localLogs = new ArrayList<>();

    static void placeOrder(String orderId) {
        localMetrics.merge("orders.placed", 1, Integer::sum);
        localSpans.add("span: order.place, orderId=" + orderId);
        localLogs.add("{\"level\":\"INFO\",\"message\":\"order placed\",\"orderId\":\"" + orderId + "\"}");
    }

    public static void main(String[] args) {
        placeOrder("order-1");
        System.out.println("Metrics: " + localMetrics + ", Spans: " + localSpans + ", Logs: " + localLogs);
        System.out.println("All THREE pillars recorded -- but NONE of it left this process. No dashboard, no trace viewer, no log search possible.");
    }
}
```

How to run: `java TelemetryProducedNoBackend.java`

All three kinds of telemetry are correctly recorded in local, in-memory structures, but nothing here actually delivers any of it to a real backend — no Prometheus scrape endpoint exposed, no span exporter configured, no log shipping agent — meaning none of this data is actually usable for monitoring, tracing, or debugging outside this single process's own memory.

### Level 2 — Intermediate

```java
// File: RoutedToRespectiveBackends.java -- each telemetry type is now
// routed to ITS OWN appropriate simulated backend, matching real
// Prometheus/Tempo/ELK integration.
import java.util.*;

public class RoutedToRespectiveBackends {
    static Map<String, Integer> prometheusScrapableMetrics = new HashMap<>(); // Prometheus scrapes THIS
    static List<String> tempoReceivedSpans = new ArrayList<>();               // Tempo/Jaeger/Zipkin receives THIS
    static List<String> elkReceivedLogs = new ArrayList<>();                  // ELK receives THIS (via a shipping agent)

    static void recordMetric(String name) { prometheusScrapableMetrics.merge(name, 1, Integer::sum); }
    static void exportSpan(String description) { tempoReceivedSpans.add(description); }
    static void shipLog(String jsonLogLine) { elkReceivedLogs.add(jsonLogLine); }

    static void placeOrder(String orderId) {
        recordMetric("orders.placed"); // -> destined for Prometheus
        exportSpan("span: order.place, orderId=" + orderId); // -> destined for Tempo/Jaeger/Zipkin
        shipLog("{\"level\":\"INFO\",\"message\":\"order placed\",\"orderId\":\"" + orderId + "\"}"); // -> destined for ELK
    }

    public static void main(String[] args) {
        placeOrder("order-1");
        System.out.println("Prometheus would scrape: " + prometheusScrapableMetrics);
        System.out.println("Tempo/Jaeger/Zipkin received: " + tempoReceivedSpans);
        System.out.println("ELK received (via shipping agent): " + elkReceivedLogs);
        System.out.println("Each pillar now lands in its OWN appropriate, queryable backend.");
    }
}
```

How to run: `java RoutedToRespectiveBackends.java`

`recordMetric`, `exportSpan`, and `shipLog` each simulate delivery to the specific backend appropriate for that kind of telemetry — the metric ends up somewhere Prometheus could scrape it from, the span ends up somewhere a trace backend has received it, and the log ends up somewhere ELK has ingested it. Each pillar of observability now has a real, durable, queryable home, rather than staying trapped in local process memory as in Level 1.

### Level 3 — Advanced

```java
// File: GrafanaStyleUnifiedDashboard.java -- simulates GRAFANA querying
// BOTH the metrics backend AND the tracing backend TOGETHER, rendering
// a UNIFIED view that correlates a metric anomaly with the specific
// trace that explains it -- exactly Grafana's real cross-backend role.
import java.util.*;

public class GrafanaStyleUnifiedDashboard {
    record TraceRecord(String traceId, String orderId, long durationMs) {}
    static Map<String, Integer> prometheusMetrics = new HashMap<>();
    static List<TraceRecord> tempoTraces = new ArrayList<>();

    static void recordOrder(String orderId, String traceId, long durationMs) {
        prometheusMetrics.merge("orders.placed", 1, Integer::sum);
        tempoTraces.add(new TraceRecord(traceId, orderId, durationMs));
    }

    // Simulates Grafana querying BOTH backends together to build one unified dashboard view.
    static void renderGrafanaDashboard() {
        int totalOrders = prometheusMetrics.getOrDefault("orders.placed", 0);
        System.out.println("Grafana panel 1 (from Prometheus): total orders placed = " + totalOrders);

        System.out.println("Grafana panel 2 (from Tempo, sorted by duration -- the trace explorer):");
        tempoTraces.stream()
                .sorted(Comparator.comparingLong(TraceRecord::durationMs).reversed())
                .limit(1)
                .forEach(t -> System.out.println("  SLOWEST trace: " + t.traceId() + " (order " + t.orderId()
                        + ") took " + t.durationMs() + "ms -- click through from the metric panel to THIS exact trace."));
    }

    public static void main(String[] args) {
        recordOrder("order-1", "trace-aaa", 80);
        recordOrder("order-2", "trace-bbb", 4200); // the outlier
        recordOrder("order-3", "trace-ccc", 95);

        renderGrafanaDashboard();
        System.out.println("Grafana unified BOTH backends: the metrics panel shows total volume, the tracing panel drills into the SPECIFIC slow request.");
    }
}
```

How to run: `java GrafanaStyleUnifiedDashboard.java`

`recordOrder` populates both `prometheusMetrics` (the aggregate count) and `tempoTraces` (individual trace records with duration), standing in for the two separate backends a real deployment would use. `renderGrafanaDashboard` queries both: the first panel reports the aggregate metric count from the Prometheus-style backend, and the second panel finds and highlights the single slowest trace from the Tempo-style backend — exactly the kind of cross-backend correlation Grafana provides in practice, letting an investigator go from "the metric shows something's off" to "here's the exact trace explaining why" within one unified dashboard.

## 6. Walkthrough

Trace `GrafanaStyleUnifiedDashboard.main` in order. **First**, three `recordOrder` calls populate both backends: `prometheusMetrics` accumulates to `{"orders.placed": 3}`, and `tempoTraces` accumulates three `TraceRecord` entries with durations `80`, `4200`, and `95` milliseconds respectively.

**Next**, `renderGrafanaDashboard()` runs. Its first panel reads `prometheusMetrics.getOrDefault("orders.placed", 0)`, getting `3`, and prints it as the total order count — this is exactly what a real Grafana panel backed by a Prometheus data source would show, querying the aggregate metric.

**Then**, the second panel's stream sorts `tempoTraces` by `durationMs` in descending order (`4200`, `95`, `80`) and takes the first (`limit(1)`) result — the `trace-bbb` entry with `durationMs=4200`. It prints this as the slowest trace, along with its associated order ID, mirroring how a real Grafana panel backed by a Tempo (or Jaeger/Zipkin) data source would let an investigator drill directly into the specific trace responsible for an anomaly the metrics panel merely hinted at.

**Finally**, `main` prints a closing observation summarizing that both backends were queried together to build this one dashboard view — the metrics backend supplying the aggregate "how much" answer, and the tracing backend supplying the specific "which request, and why" answer, correlated within a single pane rather than requiring the investigator to manually cross-reference two entirely separate tools.

```
recordOrder x3 -> prometheusMetrics={orders.placed: 3}, tempoTraces=[trace-aaa/80ms, trace-bbb/4200ms, trace-ccc/95ms]
Grafana panel 1 (Prometheus): total orders placed = 3
Grafana panel 2 (Tempo, sorted desc, top 1): SLOWEST = trace-bbb (order-2), 4200ms
```

## 7. Gotchas & takeaways

> A dashboard that only shows metrics, with no corresponding tracing backend integrated, can tell you *that* latency degraded but leaves you to manually hunt through logs or guess at the cause — integrating a tracing backend alongside metrics (as Grafana's multi-data-source model encourages) is what turns "something is wrong" into "here's exactly which request and step is responsible," dramatically shortening investigation time.

- Prometheus (metrics), Zipkin/Tempo/Jaeger (traces), and ELK (logs) are the concrete, widely-used backends that give each observability pillar a durable, queryable home.
- Grafana's role is distinctively cross-cutting: it can query multiple of these backends as data sources simultaneously, letting one dashboard correlate metrics and traces (and often logs) together.
- Choosing specific tools matters less than ensuring every pillar has some real backend at all — an ungrounded, in-process-only telemetry setup (as in Level 1) provides none of the actual operational value these concepts are meant to deliver.
- This is the natural culmination of the whole Observability section: [structured logging](0360-structured-logging.md) plus [centralized aggregation](0361-centralized-log-aggregation.md) feed ELK; [Micrometer metrics](0366-micrometer-metrics-facade.md) plus a [registry](0367-micrometer-registries-prometheus-datadog-etc.md) feed Prometheus; [Micrometer Tracing](0369-micrometer-tracing-brave-opentelemetry-bridges.md) plus [OTLP export](0371-spring-boot-opentelemetry-otlp-export.md) feed Zipkin/Tempo/Jaeger — all unified for a human via [dashboards](0364-dashboards-visualization.md) like Grafana.
