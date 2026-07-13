---
card: microservices
gi: 195
slug: spring-cloud-netflix-eureka-server
title: "Spring Cloud Netflix Eureka server"
---

## 1. What it is

Spring Cloud Netflix Eureka Server is a ready-made [service registry](0182-service-registry-concept.md) implementation for the Spring ecosystem — adding the `spring-cloud-starter-netflix-eureka-server` dependency and a single `@EnableEurekaServer` annotation turns an ordinary Spring Boot application into a fully functional registry, complete with heartbeat-based [lease renewal](0189-heartbeats-lease-renewal.md), [self-preservation handling](0194-stale-instance-self-preservation-handling.md), and a web dashboard for inspecting current registrations.

## 2. Why & when

Building a service registry from scratch, as this course's earlier examples have modeled conceptually, means implementing lease management, expiration sweeping, self-preservation logic, and a client-facing API correctly and reliably — genuinely non-trivial infrastructure. Eureka Server packages a battle-tested implementation of exactly this, originally built and proven at Netflix's own scale, exposed through Spring Boot's familiar configuration and annotation model, so a team can stand up a working registry in minutes rather than building and hardening one themselves.

Reach for Eureka Server when building a Spring-based microservices system needing a dedicated service registry outside of a platform (like Kubernetes) that already provides discovery natively. It remains a common, well-supported choice within the Spring Cloud ecosystem specifically, though newer systems increasingly rely on platform-native discovery (Kubernetes) or other registries (Consul) depending on their broader infrastructure choices.

## 3. Core concept

`@EnableEurekaServer` on a Spring Boot application's main class activates the embedded registry server; the application, once started, exposes a REST API that client applications' Eureka clients use to register, send heartbeats, and query for other services' instances, plus a browser-accessible dashboard showing the current registration state.

```java
@SpringBootApplication
@EnableEurekaServer // turns this ORDINARY Spring Boot app into a full service registry
public class EurekaServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}
```
```yaml
# application.yml -- this instance is the registry ITSELF, so it shouldn't register with or fetch from another
eureka.client.register-with-eureka: false
eureka.client.fetch-registry: false
server.port: 8761
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Spring Boot application annotated with @EnableEurekaServer exposes a REST API for registration, heartbeats, and lookup, plus a browser-accessible dashboard, all provided by the Eureka Server starter with no custom registry code written" >
  <rect x="220" y="20" width="200" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@EnableEurekaServer</text>
  <text x="320" y="62" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Spring Boot application</text>

  <rect x="30" y="120" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="105" y="142" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">register/heartbeat REST API</text>
  <rect x="245" y="120" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="320" y="142" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">lookup REST API</text>
  <rect x="460" y="120" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="535" y="142" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">web dashboard</text>

  <line x1="150" y1="80" x2="105" y2="118" stroke="#8b949e" marker-end="url(#arr76)"/>
  <line x1="320" y1="80" x2="320" y2="118" stroke="#8b949e" marker-end="url(#arr76)"/>
  <line x1="410" y1="80" x2="535" y2="118" stroke="#8b949e" marker-end="url(#arr76)"/>

  <defs>
    <marker id="arr76" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

One annotation activates a complete registry server with its full API surface and dashboard, no custom code required.

## 5. Runnable example

Scenario: a registry that starts modeled as a hand-built implementation requiring custom lease and expiration logic (contrasting with what Eureka Server provides out of the box), models the equivalent behavior activated purely through Eureka Server's configuration-driven approach, and finally demonstrates the dashboard-equivalent introspection capability Eureka Server provides for free, letting an operator see registration state without writing any custom tooling.

### Level 1 — Basic

```java
// File: HandBuiltRegistryRequiresCustomCode.java -- building the SAME
// capabilities Eureka Server provides would require substantial custom
// implementation work.
import java.util.*;

public class HandBuiltRegistryRequiresCustomCode {
    static class CustomRegistry {
        Map<String, Long> leaseExpirations = new HashMap<>();
        // would ALSO need: self-preservation logic, an HTTP API, a dashboard, replication...
        // ALL of this is CUSTOM code someone has to write, test, and maintain

        void register(String id, long expiresAt) { leaseExpirations.put(id, expiresAt); }
    }

    public static void main(String[] args) {
        CustomRegistry registry = new CustomRegistry();
        registry.register("order-a", System.currentTimeMillis() + 30000);
        System.out.println("Built a MINIMAL registry -- but self-preservation, a REST API, a dashboard, and replication are ALL still unwritten.");
    }
}
```

**How to run:** `javac HandBuiltRegistryRequiresCustomCode.java && java HandBuiltRegistryRequiresCustomCode` (JDK 17+).

### Level 2 — Intermediate

```java
// File: EurekaServerEquivalentBehavior.java -- models what Eureka Server
// provides OUT OF THE BOX, activated purely through configuration -- lease
// tracking, self-preservation, AND an API surface, all pre-built.
import java.util.*;

public class EurekaServerEquivalentBehavior {
    // simulates the Eureka Server implementation ITSELF -- code the FRAMEWORK provides,
    // not code the application team writes
    static class EurekaServerCore {
        Map<String, Long> leaseExpirations = new HashMap<>();
        double selfPreservationThreshold = 0.85;
        boolean selfPreservationActive = false;

        // this is EXACTLY the registration API real Eureka clients call automatically
        String handlePost_register(String instanceId, long leaseDurationMillis, long nowMillis) {
            leaseExpirations.put(instanceId, nowMillis + leaseDurationMillis);
            return "204 No Content"; // Eureka's ACTUAL registration response code
        }
        // this is EXACTLY the heartbeat API real Eureka clients call periodically
        String handlePut_heartbeat(String instanceId, long leaseDurationMillis, long nowMillis) {
            if (!leaseExpirations.containsKey(instanceId)) return "404 Not Found";
            leaseExpirations.put(instanceId, nowMillis + leaseDurationMillis);
            return "200 OK";
        }
        // this is EXACTLY the lookup API real Eureka clients call to discover other services
        List<String> handleGet_apps(String appName) {
            return leaseExpirations.keySet().stream().filter(id -> id.startsWith(appName)).toList();
        }
    }

    public static void main(String[] args) {
        EurekaServerCore eureka = new EurekaServerCore(); // this WHOLE object is "one annotation" in real Spring Cloud

        System.out.println("POST /eureka/apps/ORDER-SERVICE : " + eureka.handlePost_register("order-service-a1b2", 30000, 0));
        System.out.println("PUT /eureka/apps/ORDER-SERVICE/order-service-a1b2 : " + eureka.handlePut_heartbeat("order-service-a1b2", 30000, 15000));
        System.out.println("GET /eureka/apps/ORDER-SERVICE : " + eureka.handleGet_apps("order-service"));
        System.out.println("ALL of this -- lease tracking, a REST API mirroring Eureka's real endpoints -- comes from ONE @EnableEurekaServer annotation in a real Spring app.");
    }
}
```

**How to run:** `javac EurekaServerEquivalentBehavior.java && java EurekaServerEquivalentBehavior` (JDK 17+).

Expected output:
```
POST /eureka/apps/ORDER-SERVICE : 204 No Content
PUT /eureka/apps/ORDER-SERVICE/order-service-a1b2 : 200 OK
GET /eureka/apps/ORDER-SERVICE : [order-service-a1b2]
ALL of this -- lease tracking, a REST API mirroring Eureka's real endpoints -- comes from ONE @EnableEurekaServer annotation in a real Spring app.
```

### Level 3 — Advanced

```java
// File: DashboardEquivalentIntrospection.java -- models Eureka's WEB DASHBOARD:
// a human-readable view of registration state, provided FOR FREE, with NO custom
// tooling written by the application team.
import java.util.*;

public class DashboardEquivalentIntrospection {
    record RegisteredInstance(String appName, String instanceId, String status, long leaseExpiresAt) {}

    static class EurekaServerCore {
        List<RegisteredInstance> instances = new ArrayList<>();
        void register(String appName, String instanceId, long leaseExpiresAt) {
            instances.add(new RegisteredInstance(appName, instanceId, "UP", leaseExpiresAt));
        }

        // mirrors the Eureka DASHBOARD's summary view -- grouped by application, with instance counts and status
        void renderDashboard() {
            Map<String, List<RegisteredInstance>> byApp = new TreeMap<>();
            for (RegisteredInstance inst : instances) byApp.computeIfAbsent(inst.appName(), k -> new ArrayList<>()).add(inst);

            System.out.println("=== Eureka Dashboard (simulated) ===");
            System.out.println("Application            AMIs    Availability Zones    Status");
            for (var entry : byApp.entrySet()) {
                System.out.printf("%-22s  n/a     n/a                    %d instance(s) UP%n", entry.getKey(), entry.getValue().size());
            }
        }
    }

    public static void main(String[] args) {
        EurekaServerCore eureka = new EurekaServerCore();
        eureka.register("ORDER-SERVICE", "order-a", 30000);
        eureka.register("ORDER-SERVICE", "order-b", 30000);
        eureka.register("CUSTOMER-SERVICE", "customer-a", 30000);

        eureka.renderDashboard();
        System.out.println("\nAn operator can see this in a REAL Eureka Server simply by opening http://localhost:8761 in a browser -- ZERO custom monitoring code written.");
    }
}
```

**How to run:** `javac DashboardEquivalentIntrospection.java && java DashboardEquivalentIntrospection` (JDK 17+).

Expected output:
```
=== Eureka Dashboard (simulated) ===
Application            AMIs    Availability Zones    Status
CUSTOMER-SERVICE       n/a     n/a                    1 instance(s) UP
ORDER-SERVICE          n/a     n/a                    2 instance(s) UP

An operator can see this in a REAL Eureka Server simply by opening http://localhost:8761 in a browser -- ZERO custom monitoring code written.
```

## 6. Walkthrough

1. **Level 1** — `CustomRegistry` implements only the most basic lease-tracking capability, and the code comments explicitly enumerate what's still missing: self-preservation, an HTTP API, a dashboard, replication — all substantial pieces of infrastructure that would need to be designed, implemented, and hardened from scratch.
2. **Level 2, mirroring Eureka's actual API shape** — `EurekaServerCore.handlePost_register`, `handlePut_heartbeat`, and `handleGet_apps` are modeled directly after Eureka's real REST endpoints (`POST /eureka/apps/{appName}`, `PUT /eureka/apps/{appName}/{instanceId}`, `GET /eureka/apps/{appName}`), including matching HTTP status codes (`204` for registration, `200` for heartbeat).
3. **Level 2, the three calls tracing a client's lifecycle** — `handlePost_register` establishes the initial lease; `handlePut_heartbeat` (called with `nowMillis=15000`, simulating time passing) renews it; `handleGet_apps` demonstrates a lookup call finding the registered instance — this three-call sequence mirrors exactly what a real Eureka client does automatically, without the application developer writing any of this logic themselves.
4. **Level 2, the framework-versus-application-code distinction** — the final printed comment makes explicit that in a real Spring Cloud application, this entire `EurekaServerCore` equivalent is provided by the `spring-cloud-starter-netflix-eureka-server` dependency and activated by one annotation — none of `EurekaServerCore`'s logic would need to be written by the team using it.
5. **Level 3, structured registration data for display** — `RegisteredInstance` carries `appName`, `instanceId`, `status`, and lease information, giving `renderDashboard` enough structured data to produce a human-readable summary, mirroring the kind of information Eureka's actual web dashboard displays.
6. **Level 3, grouping by application for the summary view** — `renderDashboard` groups `instances` by `appName` using a `TreeMap` (for consistent, alphabetical ordering) and prints a per-application row showing the instance count, mirroring Eureka's dashboard's own per-application summary table.
7. **Level 3, the operational payoff stated directly** — the final printed line makes the practical point concrete: a real Eureka Server automatically exposes this exact kind of information through a browser-accessible dashboard at its configured port, meaning an operator investigating "which services are currently registered and how many instances does each have" needs no custom monitoring tool at all — this introspection capability comes bundled with the registry server itself, for free, the moment `@EnableEurekaServer` is added.

## 7. Gotchas & takeaways

> **Gotcha:** a Eureka Server instance, by default, tries to register itself with, and fetch its registry from, *another* Eureka server (since Eureka clients and servers share configuration conventions) — a standalone Eureka Server needs `eureka.client.register-with-eureka: false` and `eureka.client.fetch-registry: false` explicitly set, or it will generate confusing startup errors trying to connect to a peer that doesn't exist; this is one of the most common initial configuration mistakes when standing up a first Eureka Server instance.

- Spring Cloud Netflix Eureka Server turns an ordinary Spring Boot application into a fully functional service registry via a single `@EnableEurekaServer` annotation, providing lease management, self-preservation, an HTTP API, and a web dashboard out of the box.
- This avoids the substantial implementation and hardening effort a hand-built registry would require, packaging a battle-tested implementation exposed through familiar Spring Boot configuration.
- Eureka's REST API (registration, heartbeat, and lookup endpoints) is what Eureka client libraries call automatically on the application's behalf, requiring no manual HTTP calls from application code.
- The bundled web dashboard provides free operational visibility into current registration state, without any custom monitoring tooling needing to be built.
- A standalone Eureka Server instance needs explicit configuration (`register-with-eureka: false`, `fetch-registry: false`) to avoid attempting to connect to a peer server that doesn't exist — a common first-setup mistake.
