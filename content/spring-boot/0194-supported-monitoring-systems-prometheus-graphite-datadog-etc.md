---
card: spring-boot
gi: 194
slug: supported-monitoring-systems-prometheus-graphite-datadog-etc
title: Supported monitoring systems (Prometheus, Graphite, Datadog, etc.)
---

## 1. What it is

Micrometer supports **20+ monitoring system back-ends** via separate registry modules. Adding a `micrometer-registry-<name>` dependency wires a registry that translates Micrometer's meter model to the target system's native format. Spring Boot auto-configures the registry from `management.metrics.*` and the system's own `management.<name>.*` properties.

## 2. Why & when

Different organisations use different monitoring stacks. Micrometer lets you write one instrumentation and change the back-end by swapping a dependency — no code changes. Common systems and when to choose them:

| System | When to use |
|---|---|
| **Prometheus** | Self-hosted, k8s-native, pull-based, industry standard |
| **Datadog** | SaaS, rich dashboards, APM integration, enterprise |
| **Graphite** | Legacy systems, simple time-series, push-based |
| **InfluxDB** | High-cardinality time-series, IoT, edge analytics |
| **New Relic** | Full-stack observability SaaS, existing NR users |
| **CloudWatch** | AWS-native services, Lambda, ECS |
| **Dynatrace** | AI-powered observability, enterprise |
| **Wavefront** | VMware/Tanzu observability platform |
| **Elastic** | ELK stack users who want metrics alongside logs/traces |
| **Simple** | Testing — in-memory, no external system |

## 3. Core concept

Pattern: add the registry dependency → configure connection properties → Spring Boot auto-wires everything.

**Prometheus** (pull model — Prometheus scrapes your app):
```
dependency: micrometer-registry-prometheus
endpoint: GET /actuator/prometheus (text/plain, Prometheus format)
config: management.prometheus.metrics.export.enabled=true
```

**Datadog** (push model — your app pushes to Datadog):
```
dependency: micrometer-registry-datadog
config:
  management.datadog.metrics.export.api-key=<your-key>
  management.datadog.metrics.export.step=30s
```

**Graphite** (push via TCP/UDP):
```
dependency: micrometer-registry-graphite
config:
  management.graphite.metrics.export.host=graphite.internal
  management.graphite.metrics.export.port=2004
  management.graphite.metrics.export.step=10s
```

All push-based registries have a `step` (flush interval) and `enabled` property. Prometheus is pull-based and has no step — Prometheus controls the scrape frequency.

Multiple registries can coexist (push to Datadog AND expose Prometheus endpoint): Spring Boot creates a `CompositeMeterRegistry` that fans out to all configured registries.

## 4. Diagram

<svg viewBox="0 0 720 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Micrometer MeterRegistry fans out to multiple monitoring back-ends; Prometheus pulls, others receive push">
  <!-- App -->
  <rect x="10" y="75" width="140" height="56" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="98" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Boot App</text>
  <text x="80" y="114" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CompositeMeterRegistry</text>

  <!-- Arrow to registries -->
  <line x1="153" y1="103" x2="218" y2="103" stroke="#6db33f" stroke-width="2" marker-end="url(#msa)"/>

  <!-- Registry fan-out -->
  <rect x="223" y="45" width="175" height="120" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="66" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Registry Fan-out</text>
  <text x="310" y="84" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">PrometheusMeterRegistry</text>
  <text x="310" y="99" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">DatadogMeterRegistry</text>
  <text x="310" y="114" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">GraphiteMeterRegistry</text>
  <text x="310" y="129" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">CloudWatchMeterRegistry</text>
  <text x="310" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">one dependency = one registry</text>

  <!-- Pull arrow from Prometheus -->
  <line x1="400" y1="84" x2="470" y2="60" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#msb)"/>
  <rect x="474" y="38" width="225" height="38" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="586" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Prometheus Server</text>
  <text x="586" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">scrapes GET /actuator/prometheus</text>

  <!-- Push arrows -->
  <line x1="400" y1="99" x2="470" y2="99" stroke="#6db33f" stroke-width="1.5" marker-end="url(#msa)"/>
  <rect x="474" y="82" width="225" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="586" y="101" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Datadog API (HTTPS push)</text>

  <line x1="400" y1="120" x2="470" y2="135" stroke="#6db33f" stroke-width="1.5" marker-end="url(#msa)"/>
  <rect x="474" y="120" width="225" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="586" y="139" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Graphite TCP (push)</text>

  <line x1="400" y1="140" x2="470" y2="165" stroke="#6db33f" stroke-width="1.5" marker-end="url(#msa)"/>
  <rect x="474" y="158" width="225" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="586" y="177" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">CloudWatch (AWS SDK push)</text>

  <defs>
    <marker id="msa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="msb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Prometheus pulls from the app (scrape model); all other registries push from the app to the target system.

## 5. Runnable example

```java
// MonitoringSystemsDemo.java — compares configuration for major monitoring registries
// How to run: java MonitoringSystemsDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add the matching micrometer-registry-* dependency + properties

import java.util.*;

public class MonitoringSystemsDemo {

    record MonitoringSystem(String name, String dependency, String model,
                            String configPrefix, String[] keyProperties) {}

    public static void main(String[] args) {
        System.out.println("=== Supported Monitoring Systems Demo ===\n");

        List<MonitoringSystem> systems = List.of(
            new MonitoringSystem("Prometheus",
                "micrometer-registry-prometheus",
                "pull (Prometheus scrapes /actuator/prometheus)",
                "management.prometheus.metrics.export",
                new String[]{"enabled=true"}),

            new MonitoringSystem("Datadog",
                "micrometer-registry-datadog",
                "push (HTTPS to api.datadoghq.com)",
                "management.datadog.metrics.export",
                new String[]{"api-key=<secret>", "step=30s", "host-tag=myservice"}),

            new MonitoringSystem("Graphite",
                "micrometer-registry-graphite",
                "push (TCP to Graphite)",
                "management.graphite.metrics.export",
                new String[]{"host=graphite.internal", "port=2004", "step=10s", "protocol=plaintext"}),

            new MonitoringSystem("InfluxDB",
                "micrometer-registry-influx",
                "push (HTTP to InfluxDB API)",
                "management.influx.metrics.export",
                new String[]{"uri=http://influx:8086", "db=myapp", "step=10s"}),

            new MonitoringSystem("New Relic",
                "micrometer-registry-new-relic",
                "push (HTTPS to metrics.newrelic.com)",
                "management.newrelic.metrics.export",
                new String[]{"api-key=<secret>", "account-id=<id>", "step=30s"}),

            new MonitoringSystem("CloudWatch",
                "micrometer-registry-cloudwatch2",
                "push (AWS SDK to CloudWatch)",
                "management.cloudwatch.metrics.export",
                new String[]{"namespace=MyApp", "step=1m"}),

            new MonitoringSystem("Elastic",
                "micrometer-registry-elastic",
                "push (HTTP to Elasticsearch)",
                "management.elastic.metrics.export",
                new String[]{"host=http://elastic:9200", "index=micrometer", "step=30s"}),

            new MonitoringSystem("Simple (testing)",
                "(built-in)",
                "in-memory (no external system)",
                "management.simple.metrics.export",
                new String[]{"enabled=true", "mode=step"})
        );

        System.out.printf("%-14s %-42s %-10s%n", "System", "Dependency", "Model");
        System.out.println("-".repeat(80));
        systems.forEach(s ->
            System.out.printf("%-14s %-42s %s%n", s.name(), s.dependency(), s.model()));

        System.out.println("\n=== Configuration examples ===");
        systems.forEach(s -> {
            System.out.println("\n## " + s.name());
            System.out.println("dependency: " + s.dependency());
            for (String prop : s.keyProperties()) {
                System.out.println(s.configPrefix() + "." + prop);
            }
        });

        System.out.println("\n=== Composite: push to both Datadog AND expose Prometheus ===");
        System.out.println("Add BOTH micrometer-registry-prometheus AND micrometer-registry-datadog");
        System.out.println("Spring Boot creates a CompositeMeterRegistry automatically.");
        System.out.println("All meters flow to both registries simultaneously.");
    }
}
```

**How to run:** `java MonitoringSystemsDemo.java`

## 6. Walkthrough

- **Prometheus** is the only pull-based registry. You expose `/actuator/prometheus`; Prometheus polls it at its configured `scrape_interval`. No outbound network call from your app.
- **Datadog/New Relic** require an API key and push metrics over HTTPS at the configured `step` interval. The key must be stored as a secret (environment variable, Vault) — never in source code.
- **Graphite** pushes over a TCP or UDP socket. The `protocol=plaintext` uses the human-readable line protocol; `protocol=pickled` uses binary for efficiency.
- **CloudWatch** uses the AWS SDK under the hood. The registry automatically uses instance credentials (IAM role) when running on EC2/ECS — no explicit key needed.
- **Composite registry**: Spring Boot creates a `CompositeMeterRegistry` when multiple registry beans are present. All `increment`, `record`, and gauge calls fan out to every registered registry automatically.

## 7. Gotchas & takeaways

> **Push registries** add a background thread that flushes metrics every `step`. If your app is short-lived (Lambda, batch job) and the step is 60 s, the last minute of metrics may never flush before the JVM exits. Force a flush in a shutdown hook or use the `ForceStop` method.

> With **Prometheus** in Kubernetes: configure `scrape_configs` in `prometheus.yml` to target your pod's `/actuator/prometheus` endpoint, or use the Prometheus Operator with PodMonitor CRDs.

- `management.<registry>.metrics.export.enabled=false` disables a specific registry without removing the dependency.
- All registries respect `management.metrics.tags.*` global tags (e.g., `management.metrics.tags.env=prod`).
- Multiple registries: `micrometer-registry-prometheus` + `micrometer-registry-datadog` → both active simultaneously.
- Name convention: Micrometer uses `camelCase` names internally; each registry translates to its native format (Prometheus uses `_`, Graphite uses `.`, Datadog uses `.` with prefix).
- For Prometheus Pushgateway (short-lived jobs): add `micrometer-registry-prometheus` and call `registry.pushAll()` at job completion.
