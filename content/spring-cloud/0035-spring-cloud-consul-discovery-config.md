---
card: spring-cloud
gi: 35
slug: spring-cloud-consul-discovery-config
title: "Spring Cloud Consul (discovery & config)"
---

## 1. What it is

Spring Cloud Consul is an alternative to Eureka: instead of Netflix's registry, it integrates with HashiCorp Consul, which provides both service discovery *and* a key-value configuration store in one system, with health checking built directly into its agent architecture rather than bolted on via heartbeats.

```properties
spring.application.name=orders-service
spring.cloud.consul.host=localhost
spring.cloud.consul.port=8500
spring.cloud.consul.discovery.enabled=true
```

```java
@SpringBootApplication
@EnableDiscoveryClient // same annotation as Eureka -- Spring Cloud Commons abstracts the difference
public class OrdersServiceApplication { }
```

## 2. Why & when

Eureka and Consul solve the same core problem (service discovery) with different architectures: Eureka is a purpose-built registry with client-driven heartbeats; Consul is a general-purpose service mesh building block with a local agent on every host, gossip-based cluster membership, and native support for configuration alongside discovery. Because Spring Cloud Commons defines discovery through the vendor-neutral `DiscoveryClient` interface (covered in the Overview section), switching between them is mostly a dependency and configuration change, not an application code rewrite.

Reach for Consul over Eureka when:

- The organization already runs Consul for other purposes (e.g. HashiCorp Vault integration, existing non-Spring services using Consul, network infrastructure like Consul Connect) — reusing it avoids running two separate discovery systems.
- You want service discovery and configuration management from a single system, rather than pairing Eureka with a separate Config Server.
- You need Consul's stronger consistency model (it uses the Raft protocol for its catalog, CP rather than Eureka's AP) — Consul favors returning a correct answer over always answering, the reverse of Eureka's self-preservation tradeoff.

## 3. Core concept

```
   Consul Agent (runs on every host, alongside the app)
        |
        |-- registers services running on this host
        |-- performs health checks locally (script, HTTP, TCP, TTL)
        |-- gossips membership + health with other agents in the cluster
        |
   Consul Server cluster (Raft-consistent catalog)
        |
        |-- authoritative source of truth for the whole datacenter
        |-- also serves as a key-value store for configuration
```

A local agent per host does health checking and registration; a small server cluster holds the consistent, authoritative catalog that all agents and clients ultimately query.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each host runs a local Consul agent that registers services and runs health checks, gossiping with other agents and syncing to a small consistent Consul server cluster">
  <rect x="30" y="20" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">host 1</text>
  <text x="110" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">orders-service +</text>
  <text x="110" y="70" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Consul agent</text>

  <rect x="240" y="20" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">host 2</text>
  <text x="320" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">billing-service +</text>
  <text x="320" y="70" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Consul agent</text>

  <line x1="190" y1="50" x2="238" y2="50" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="3,3"/>
  <text x="215" y="42" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">gossip</text>

  <rect x="230" y="130" width="180" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="150" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Consul Server cluster</text>
  <text x="320" y="166" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">catalog + KV store (Raft)</text>

  <line x1="110" y1="80" x2="300" y2="128" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a35)"/>
  <line x1="320" y1="80" x2="320" y2="128" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a35)"/>

  <defs><marker id="a35" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Local agents handle registration and health checks per host and sync to a small, strongly-consistent server cluster that holds the authoritative catalog.

## 5. Runnable example

The scenario: mirror the Eureka Client example from earlier (`orders-service` calling `billing-service`) but through a Consul-shaped model — an agent-based registry with agent-local health checking, built up from single-agent registration to multi-agent gossip-based membership to combined discovery-plus-config.

### Level 1 — Basic

A single Consul agent registering one service, health-checked locally rather than via remote heartbeat.

```java
import java.util.*;

public class ConsulLevel1 {
    static class Agent {
        String host;
        Map<String, String> services = new HashMap<>(); // serviceName -> address
        Map<String, Boolean> localHealthChecks = new HashMap<>();

        Agent(String host) { this.host = host; }

        void register(String service, String address) {
            services.put(service, address);
            localHealthChecks.put(service, true); // agent runs its own check, e.g. a TCP probe
        }
    }

    public static void main(String[] args) {
        Agent agentOnHost1 = new Agent("host-1");
        agentOnHost1.register("billing-service", "10.0.2.1:8080");

        System.out.println("agent on " + agentOnHost1.host + " tracks: " + agentOnHost1.services);
        System.out.println("locally health-checked: " + agentOnHost1.localHealthChecks);
    }
}
```

How to run: `java ConsulLevel1.java`

Unlike Eureka's remote heartbeat model, the Consul agent runs *locally* on the same host as the service and checks its health directly — via a script, HTTP probe, or TCP connect — rather than waiting for the service to phone home.

### Level 2 — Intermediate

Add a second agent on a different host and a shared catalog they both sync to, modeling gossip-based membership converging into one authoritative view.

```java
import java.util.*;

public class ConsulLevel2 {
    static class Agent {
        String host;
        Map<String, String> localServices = new HashMap<>();
        Map<String, Boolean> localHealth = new HashMap<>();
        Catalog catalog;

        Agent(String host, Catalog catalog) { this.host = host; this.catalog = catalog; }

        void register(String service, String address) {
            localServices.put(service, address);
            localHealth.put(service, true);
            catalog.sync(service, address, true); // agent pushes its local state to the shared catalog
        }
    }

    static class Catalog {
        Map<String, List<String>> healthyInstances = new HashMap<>();
        void sync(String service, String address, boolean healthy) {
            if (healthy) healthyInstances.computeIfAbsent(service, k -> new ArrayList<>()).add(address);
        }
    }

    public static void main(String[] args) {
        Catalog catalog = new Catalog();
        Agent agent1 = new Agent("host-1", catalog);
        Agent agent2 = new Agent("host-2", catalog);

        agent1.register("billing-service", "10.0.2.1:8080");
        agent2.register("billing-service", "10.0.2.2:8080");

        System.out.println("catalog view of billing-service: " + catalog.healthyInstances.get("billing-service"));
    }
}
```

How to run: `java ConsulLevel2.java`

Each `Agent.register` call performs its own local health check and pushes the result to the shared `Catalog` — mirroring how Consul agents gossip locally-observed state to the server cluster. Because both agents converge into one `Catalog`, `billing-service` correctly shows both instances even though they were registered independently by two different agents.

### Level 3 — Advanced

Add key-value configuration alongside discovery — the same Consul cluster serving both roles — and a failing health check that removes an instance from the catalog automatically.

```java
import java.util.*;

public class ConsulLevel3 {
    static class Agent {
        String host;
        Map<String, String> localServices = new HashMap<>();
        Catalog catalog;

        Agent(String host, Catalog catalog) { this.host = host; this.catalog = catalog; }

        void register(String service, String address) {
            localServices.put(service, address);
            catalog.setHealth(service, address, true);
        }

        void reportHealthCheckResult(String service, boolean healthy) {
            // agent runs its configured check (HTTP/TCP/script) on an interval and reports the result
            catalog.setHealth(service, localServices.get(service), healthy);
        }
    }

    static class Catalog {
        Map<String, Map<String, Boolean>> health = new HashMap<>(); // service -> address -> healthy
        Map<String, String> kv = new HashMap<>(); // shared key-value config store

        void setHealth(String service, String address, boolean healthy) {
            health.computeIfAbsent(service, k -> new HashMap<>()).put(address, healthy);
        }

        List<String> healthyInstancesOf(String service) {
            List<String> result = new ArrayList<>();
            for (var e : health.getOrDefault(service, Map.of()).entrySet()) {
                if (e.getValue()) result.add(e.getKey());
            }
            return result;
        }

        void putConfig(String key, String value) { kv.put(key, value); }
        String getConfig(String key) { return kv.get(key); }
    }

    public static void main(String[] args) {
        Catalog catalog = new Catalog();
        Agent agent1 = new Agent("host-1", catalog);
        Agent agent2 = new Agent("host-2", catalog);

        agent1.register("billing-service", "10.0.2.1:8080");
        agent2.register("billing-service", "10.0.2.2:8080");
        catalog.putConfig("billing-service/tax-rate", "0.0825"); // shared config, same cluster as discovery

        System.out.println("healthy before failure: " + catalog.healthyInstancesOf("billing-service"));
        System.out.println("tax-rate config: " + catalog.getConfig("billing-service/tax-rate"));

        agent1.reportHealthCheckResult("billing-service", false); // host-1's local check starts failing
        System.out.println("healthy after failure: " + catalog.healthyInstancesOf("billing-service"));
    }
}
```

How to run: `java ConsulLevel3.java`

`catalog.putConfig` and `catalog.getConfig` model Consul's KV store living in the *same* cluster as service discovery — no separate Config Server is needed, unlike the Eureka-plus-Config-Server combination covered earlier. When `agent1`'s local health check fails, `reportHealthCheckResult` pushes `healthy=false` for that specific address, and `healthyInstancesOf` immediately excludes it — the catalog reacts to the agent's own local observation, not a missed remote heartbeat.

## 6. Walkthrough

Trace Level 3 end to end.

1. Both agents register their local `billing-service` instance — each call updates `localServices` on the agent and pushes an initial `healthy=true` entry into the shared `Catalog` via `setHealth`. This models each Consul agent's `PUT /v1/agent/service/register` call.
2. `catalog.putConfig("billing-service/tax-rate", "0.0825")` runs — this models a `PUT` to Consul's KV HTTP API (`/v1/kv/billing-service/tax-rate`), storing configuration in the exact same cluster that just received the service registrations.
3. The first two `println` calls confirm both capabilities work side by side: `healthyInstancesOf` returns both addresses, and `getConfig` returns the stored tax rate — proving discovery and configuration share one system rather than needing separate infrastructure.
4. `agent1.reportHealthCheckResult("billing-service", false)` runs — this models `host-1`'s local Consul agent running its configured health check (an HTTP probe against `orders-service`'s own `/health` endpoint, say) on a periodic interval, and that check starting to fail — perhaps the process is still running but a dependency died.
5. The final `println` calls `healthyInstancesOf` again — because the agent already reported the failure directly into the catalog's health map for that specific address, `10.0.2.1:8080` is filtered out immediately, leaving only `10.0.2.2:8080`. There's no heartbeat-expiry delay to wait out, because the check result was pushed the moment it changed, not inferred from silence.

```
register(host-1, billing-service) -> catalog.setHealth(healthy=true)
register(host-2, billing-service) -> catalog.setHealth(healthy=true)
putConfig(tax-rate)               -> same catalog, KV side

healthyInstancesOf() -> [host-1, host-2]

agent1 health check fails -> setHealth(host-1, healthy=false)

healthyInstancesOf() -> [host-2]   (immediate, not lease-expiry-based)
```

## 7. Gotchas & takeaways

> **Gotcha:** Consul's health checks are defined and run by the *local agent*, not the application itself pushing status — if the agent process on a host dies while the application keeps running, Consul has no way to know the application is still healthy, and typically marks it critical/unreachable. This is a different failure mode than Eureka's client-pushes-heartbeats model, worth understanding before choosing between them.

- Consul combines service discovery and key-value configuration in one system — a real operational simplification if you'd otherwise run Eureka plus a separate Config Server.
- Consul's catalog is Raft-consistent (CP) rather than Eureka's AP self-preservation model — during a partition, Consul may refuse to answer rather than serve a possibly-stale view; pick based on which tradeoff fits the workload.
- Health checks live in the local agent, not in remote heartbeats — this generally detects failure faster (a check can fail within seconds) but ties health accuracy to the agent's own uptime on that host.
- Spring Cloud Commons' `@EnableDiscoveryClient` and `DiscoveryClient` abstraction mean application code calling other services by name doesn't need to change when swapping Eureka for Consul — only the starter dependency and `spring.cloud.consul.*` configuration change.
