---
card: microservices
gi: 551
slug: spring-cloud-consul
title: "Spring Cloud Consul"
---

## 1. What it is

**Spring Cloud Consul** is the concrete [`DiscoveryClient`](0539-spring-cloud-commons-shared-abstractions.md) integration for HashiCorp Consul — an alternative to [Eureka](0542-spring-cloud-netflix-eureka.md) that additionally provides distributed key-value configuration storage (an alternative to [Spring Cloud Config](0541-spring-cloud-config-centralized-config.md)) and native health-checking, all through one piece of infrastructure. Where Eureka is a discovery-only registry, Consul is a broader service-mesh-adjacent tool: service discovery, health checking, and a distributed KV store for configuration, unified in a single agent process that runs alongside every service instance.

## 2. Why & when

You reach for Consul specifically when you want discovery, health checking, and configuration storage unified in one piece of infrastructure, rather than operating separate tools for each:

- **Consul's health checks are pluggable and can be far richer than a simple heartbeat** — a Consul health check can be an HTTP endpoint check, a TCP connect check, or a custom script, executed by a local Consul agent running alongside each service instance, giving a more nuanced signal of "is this instance actually healthy" than Eureka's simple heartbeat-based liveness.
- **Consul's KV store lets the same infrastructure serve as a configuration source**, similar in spirit to [Spring Cloud Config](0541-spring-cloud-config-centralized-config.md) but backed by Consul's own distributed store rather than Git — useful if you're already running Consul for discovery and don't want to additionally operate a separate Config Server.
- **Consul supports multi-datacenter topologies natively**, useful for organizations running services across multiple physical or cloud regions that need discovery and configuration to span those boundaries coherently.
- **You choose Consul over Eureka primarily based on infrastructure already in place or richer health-check needs** — if your organization already runs Consul for other purposes (secret management via its cousin tool Vault, or service-mesh features), reusing it for Spring service discovery avoids introducing a separate Eureka deployment; if you have no existing preference, either works well for straightforward VM/container-based discovery.

## 3. Core concept

Think of Consul as a building's integrated security desk that not only maintains a directory of who's currently in the building (discovery), but also actively monitors whether each occupant is actually breathing and responsive via periodic, configurable check-ins (rich health checks) rather than simply noting whether they showed up once — and additionally keeps a shared bulletin board of building-wide announcements (the KV store) that any occupant can consult, all through the same integrated front-desk system rather than needing a separate directory service, a separate wellness-check service, and a separate bulletin board system.

Concretely:

1. **A local Consul agent runs alongside every service instance** (often as a sidecar process or a separate agent), handling that instance's registration and health-check reporting to the broader Consul cluster.
2. **Health checks are configured per service** — an HTTP check (`GET /actuator/health` returning 200), a TCP check, or a custom script — executed by the local agent on a schedule, and reported to the Consul servers, which aggregate health status across the cluster.
3. **Spring Cloud Consul's `DiscoveryClient` implementation queries Consul's catalog for currently-healthy service instances**, exactly matching the same abstraction discussed for [Spring Cloud Commons](0539-spring-cloud-commons-shared-abstractions.md) — application code depending on `DiscoveryClient` needs zero changes moving from Eureka to Consul.
4. **Consul's KV store can back `spring.config.import=consul:` configuration**, letting the same Consul cluster serve both discovery and configuration needs without a separate Config Server.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Consul unifies discovery, rich health checking, and KV-based configuration in one piece of infrastructure, versus operating separate tools for each concern">
  <rect x="230" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Consul cluster</text>

  <rect x="20" y="110" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Discovery (DiscoveryClient)</text>
  <rect x="240" y="110" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Rich health checks</text>
  <rect x="460" y="110" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">KV config store</text>

  <line x1="110" y1="110" x2="300" y2="70" stroke="#8b949e"/>
  <line x1="330" y1="110" x2="330" y2="70" stroke="#8b949e"/>
  <line x1="550" y1="110" x2="360" y2="70" stroke="#8b949e"/>
</svg>

One Consul cluster unifies discovery, richer health checking, and configuration storage that would otherwise require separate tools.

## 5. Runnable example

Scenario: an instance registering with rich health checks. We start with a plain Java model of a heartbeat-only check versus a richer HTTP-based check, extend it to a KV-config lookup model, then show the real Spring Cloud Consul configuration.

### Level 1 — Basic

```java
// File: HeartbeatVsHttpCheck.java -- contrasts a SIMPLE heartbeat check
// (Eureka-style) with a RICHER HTTP-based health check (Consul-style).
import java.util.*;

public class HeartbeatVsHttpCheck {
    // simple heartbeat: only knows "did it check in recently"
    static boolean heartbeatHealthy(long lastHeartbeatAgeMs, long thresholdMs) {
        return lastHeartbeatAgeMs < thresholdMs;
    }

    // richer HTTP check: can reflect ACTUAL application health (DB connectivity, etc.),
    // not just "the process is running and pinging"
    static boolean httpHealthCheck(Map<String, String> healthEndpointResponse) {
        return "UP".equals(healthEndpointResponse.get("status"));
    }

    public static void main(String[] args) {
        System.out.println("Heartbeat-only: " + heartbeatHealthy(20000, 90000) + " (process is alive, but is the APP actually healthy?)");
        Map<String, String> response = Map.of("status", "DOWN", "reason", "database connection pool exhausted");
        System.out.println("HTTP health check: " + httpHealthCheck(response) + " -- correctly reflects a REAL application problem, not just process liveness.");
    }
}
```

How to run: `java HeartbeatVsHttpCheck.java`

`heartbeatHealthy` only knows the process is alive and checking in — it would report this instance healthy even if its database connections were exhausted. `httpHealthCheck`, modeling Consul's HTTP-based check, reflects the actual application-reported health status, correctly detecting the "DOWN" state a plain heartbeat would have missed entirely.

### Level 2 — Intermediate

```java
// File: ConsulKvConfigModel.java -- models CONSUL'S KV STORE serving
// configuration, alongside its discovery role, from the SAME infrastructure.
import java.util.*;

public class ConsulKvConfigModel {
    // ONE store, serving BOTH service registrations AND configuration key-values
    static Map<String, String> serviceRegistry = new HashMap<>(Map.of("order-service", "10.0.5.2:8080"));
    static Map<String, String> kvConfigStore = new HashMap<>(Map.of("order-service/downstream.timeout-ms", "500"));

    public static void main(String[] args) {
        System.out.println("Discovery: order-service is at " + serviceRegistry.get("order-service"));
        System.out.println("Config: order-service's timeout is " + kvConfigStore.get("order-service/downstream.timeout-ms") + "ms");
        System.out.println("Both served from the SAME Consul cluster -- no separate Config Server needed.");
    }
}
```

How to run: `java ConsulKvConfigModel.java`

`serviceRegistry` and `kvConfigStore` model two distinct concerns (discovery, configuration) served from the same underlying Consul infrastructure — a service using Spring Cloud Consul can fetch both its downstream instances and its own configuration values from one cluster, rather than needing separate Eureka and Config Server deployments.

### Level 3 — Advanced

```java
// File: SpringCloudConsulRealShape.java -- the REAL Spring Cloud Consul
// shape: discovery-enabled application with a Consul-backed HTTP health check.
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.web.bind.annotation.*;

public class SpringCloudConsulRealShape {

    @SpringBootApplication
    @EnableDiscoveryClient
    static class OrderServiceApplication {
        public static void main(String[] args) { SpringApplication.run(OrderServiceApplication.class, args); }
        // application.yml:
        //   spring.application.name: order-service
        //   spring.cloud.consul.host: consul-server
        //   spring.cloud.consul.discovery.health-check-path: /actuator/health
        //   spring.cloud.consul.discovery.health-check-interval: 10s
    }

    @RestController
    static class HealthAwareController {
        @GetMapping("/orders/{id}")
        public String getOrder(@PathVariable String id) { return "{\"orderId\":\"" + id + "\"}"; }
    }

    // spring.config.import: consul: -- would let this SAME Consul cluster ALSO serve configuration
    // from its KV store, e.g. reading order-service/downstream.timeout-ms into @Value bindings
}
```

How to run: requires `spring-cloud-starter-consul-discovery` (and optionally `spring-cloud-starter-consul-config`), a running Consul agent/cluster, and `spring.cloud.consul.host` pointed at it; run via `mvn spring-boot:run` and observe the instance registering with Consul, with Consul actively polling `/actuator/health` every 10 seconds (per the configured interval) to determine ongoing health, rather than relying purely on a heartbeat.

`spring.cloud.consul.discovery.health-check-path` and `health-check-interval` configure Consul's local agent to actively poll this application's actual Spring Boot Actuator health endpoint, reflecting real application health (database connectivity, disk space, custom health indicators) rather than mere process liveness — the richer health-check model discussed conceptually in Level 1, here wired into a real Spring Boot application via configuration alone.

## 6. Walkthrough

Trace what happens when `order-service`'s database connection pool becomes exhausted, with Consul configured as in Level 3:

1. **Consul's local agent, per its configured `health-check-interval` of 10 seconds, issues `GET /actuator/health` against the `order-service` instance.**
2. **Spring Boot Actuator's health endpoint aggregates its configured health indicators** — including a database health indicator, which detects the connection pool is exhausted and reports `DOWN` for that specific indicator, causing the overall aggregated status to also report `DOWN`.
3. **Consul's agent receives this `DOWN` status** (rather than a connection failure or timeout, which a heartbeat-only check might also catch, but *only* by the instance failing to respond at all) and marks this instance as unhealthy in the Consul catalog — even though the instance's process is still running and would still be sending heartbeats if that were the only mechanism in place.
4. **Any other service's `DiscoveryClient.getInstances("order-service")` call, resolved through Consul, now excludes this instance from its results** — traffic is routed away from an instance that's technically alive but functionally broken, exactly the scenario a plain heartbeat-based check (as in Eureka's default behavior) would have missed, since the process itself never actually stopped responding to heartbeats.
5. **Once the database connection pool recovers** (say, after a restart or the underlying database issue resolving), the next `/actuator/health` poll reports `UP` again, and Consul restores the instance to the healthy pool — discovery clients querying it resume including this instance in their results automatically.

## 7. Gotchas & takeaways

> **Gotcha:** an HTTP-based health check that itself depends on the same resource being checked (say, the health endpoint's own thread pool being exhausted for the same reason the application is unhealthy) can fail to respond at all, which Consul typically treats the same as an explicit `DOWN` — usually the desired outcome, but worth being aware that a health check's own failure mode (no response versus an explicit "DOWN" body) can matter for how quickly Consul reacts, depending on configured timeout settings.

- Consul unifies service discovery, richer application-level health checking, and KV-based configuration storage in one piece of infrastructure, versus separate tools for each concern.
- Consul's HTTP/TCP/script-based health checks can detect real application-level problems (a specific failing dependency) that a simple heartbeat-based check would miss entirely.
- Application code depending on the `DiscoveryClient` abstraction requires zero changes moving between Eureka and Consul — only the dependency and configuration differ.
- Choose Consul when richer health checking or unified discovery-plus-configuration infrastructure is valuable, or when it's already part of your organization's toolset for other reasons (like paired use with Vault).
