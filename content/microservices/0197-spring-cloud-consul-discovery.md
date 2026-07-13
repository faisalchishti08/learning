---
card: microservices
gi: 197
slug: spring-cloud-consul-discovery
title: "Spring Cloud Consul discovery"
---

## 1. What it is

Spring Cloud Consul integrates HashiCorp Consul as the [service registry](0182-service-registry-concept.md) for a Spring application — like [Eureka](0195-spring-cloud-netflix-eureka-server.md), it provides automatic registration and discovery through Spring Cloud's common abstractions, but Consul itself is a broader tool than a pure service registry: it also provides a distributed key-value store for configuration and built-in support for richer, script- or HTTP-based health checks beyond simple heartbeat presence.

## 2. Why & when

Consul's health-checking model is meaningfully more flexible than Eureka's heartbeat-only approach: Consul can run arbitrary health check scripts, TCP checks, or HTTP endpoint checks directly against a registered service, on its own schedule, rather than relying purely on the service itself proactively sending heartbeats — this shifts health verification partly toward third-party-style checking (Consul actively probing the service) rather than relying entirely on the service self-reporting via heartbeats. Consul's additional built-in key-value store also makes it attractive for teams wanting a single piece of infrastructure serving both service discovery and dynamic configuration needs together, rather than running separate tools for each.

Choose Spring Cloud Consul when Consul's richer health-check model (active probing rather than passive heartbeat-only) is valuable, or when a team already uses (or wants to adopt) Consul for its key-value configuration store and prefers consolidating service discovery onto the same infrastructure. Choose Eureka when staying within the classic Netflix-OSS-derived Spring Cloud ecosystem is preferred, or when Consul's additional capabilities aren't needed.

## 3. Core concept

Consul health checks can be defined as scripts, TCP probes, or HTTP endpoint checks that Consul itself executes on a schedule against the registered service, determining registration status based on the check's actual outcome, rather than solely on whether the service proactively sent a heartbeat.

```yaml
# application.yml -- Spring Cloud Consul configuration
spring.cloud.consul.discovery.health-check-path: /actuator/health  # Consul PROBES this endpoint itself
spring.cloud.consul.discovery.health-check-interval: 10s            # on ITS OWN schedule
```
```java
// Consul actively CALLS this endpoint -- the service doesn't need to proactively push anything
@GetMapping("/actuator/health")
HealthStatus health() {
    return databasePool.isHealthy() ? HealthStatus.UP : HealthStatus.DOWN;
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Eureka's model: the service actively pushes heartbeats to the registry on its own schedule. Consul's model: the registry actively pulls health status by probing the service's health endpoint on the registry's own schedule" >
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Eureka: service PUSHES</text>
  <rect x="30" y="45" width="120" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="90" y="67" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Service</text>
  <rect x="200" y="45" width="120" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="260" y="67" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Registry</text>
  <line x1="150" y1="62" x2="198" y2="62" stroke="#8b949e" marker-end="url(#arr78)"/>
  <text x="174" y="50" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">heartbeat</text>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Consul: registry PULLS</text>
  <rect x="360" y="45" width="120" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="420" y="67" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Service</text>
  <rect x="530" y="45" width="120" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="590" y="67" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Consul</text>
  <line x1="528" y1="62" x2="482" y2="62" stroke="#8b949e" marker-end="url(#arr78)"/>
  <text x="505" y="50" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">probe /health</text>

  <defs>
    <marker id="arr78" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The direction of health information flow differs: Eureka's clients push, Consul actively pulls.

## 5. Runnable example

Scenario: a health-checking mechanism that starts with a heartbeat-push model (mirroring Eureka's approach, as a contrast baseline), moves to a probe-pull model mirroring Consul's active health checking, and finally demonstrates the practical advantage of active probing — Consul catching a degraded instance faster than heartbeat-only detection would, since it's independently verifying actual serviceability rather than trusting the instance's own self-reported "I'm alive" signal.

### Level 1 — Basic

```java
// File: HeartbeatPushModel.java -- the SERVICE proactively PUSHES an "I'm alive"
// signal; the registry TRUSTS it without independently verifying anything.
public class HeartbeatPushModel {
    static boolean serviceProcessIsAlive = true; // the process itself hasn't crashed
    static boolean actuallyServingRequestsCorrectly = false; // but a dependency is DOWN

    static void sendHeartbeat() {
        if (serviceProcessIsAlive) {
            System.out.println("[heartbeat] 'I'm alive!' sent to registry -- registry TRUSTS this claim, doesn't verify anything else");
        }
    }

    public static void main(String[] args) {
        sendHeartbeat(); // the process CAN send this heartbeat -- it's still running
        System.out.println("Registry believes this instance is healthy, PURELY because it sent a heartbeat.");
        System.out.println("But actuallyServingRequestsCorrectly = " + actuallyServingRequestsCorrectly + " -- the registry has NO IDEA.");
    }
}
```

**How to run:** `javac HeartbeatPushModel.java && java HeartbeatPushModel` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ActiveProbePullModel.java -- the REGISTRY actively PROBES the service's
// health endpoint ITSELF, independently verifying actual serviceability.
public class ActiveProbePullModel {
    static boolean serviceProcessIsAlive = true;
    static boolean databaseReachable = false; // a REAL dependency, checked by the health endpoint

    // this is the ENDPOINT Consul (or any active health checker) calls DIRECTLY
    static String healthEndpoint() {
        return databaseReachable ? "UP" : "DOWN"; // reflects ACTUAL serviceability
    }

    // simulates Consul PROBING the endpoint on ITS OWN schedule
    static void consulProbesHealth() {
        String result = healthEndpoint(); // Consul CALLS this itself -- doesn't trust a self-reported claim
        System.out.println("[Consul, active probe] called /health -- got: " + result);
        if (result.equals("DOWN")) System.out.println("[Consul] EXCLUDING this instance from service discovery results");
    }

    public static void main(String[] args) {
        consulProbesHealth();
        System.out.println("Consul CAUGHT the degraded state, because it actively CALLED the endpoint rather than trusting a self-reported heartbeat.");
    }
}
```

**How to run:** `javac ActiveProbePullModel.java && java ActiveProbePullModel` (JDK 17+).

Expected output:
```
[Consul, active probe] called /health -- got: DOWN
[Consul] EXCLUDING this instance from service discovery results
Consul CAUGHT the degraded state, because it actively CALLED the endpoint rather than trusting a self-reported heartbeat.
```

### Level 3 — Advanced

```java
// File: PushVsPullDetectionSpeedComparison.java -- SIDE BY SIDE: heartbeat-push
// (mirroring Eureka) can be MISLED by a process that's alive but degraded;
// active-probe-pull (mirroring Consul) catches the SAME degradation immediately.
public class PushVsPullDetectionSpeedComparison {
    static boolean processIsAlive = true;
    static boolean databaseReachable = false;

    // PUSH model: the process decides what to report, based on ITS OWN (possibly incomplete) self-assessment
    static String pushModelSelfReport() {
        // BUG: this self-report ONLY checks process liveness, forgetting to check the database dependency
        return processIsAlive ? "UP" : "DOWN";
    }

    // PULL model: Consul calls a health endpoint that DOES check the real dependency
    static String pullModelHealthEndpoint() {
        return (processIsAlive && databaseReachable) ? "UP" : "DOWN"; // CORRECTLY incorporates the dependency
    }

    public static void main(String[] args) {
        System.out.println("=== Push model (Eureka-style): trusts the SERVICE's own self-report ===");
        String pushResult = pushModelSelfReport();
        System.out.println("Registry receives: " + pushResult + " -- WRONG, this instance is actually degraded, but the self-report has a bug and doesn't catch it");

        System.out.println("\n=== Pull model (Consul-style): actively PROBES and independently evaluates ===");
        String pullResult = pullModelHealthEndpoint();
        System.out.println("Consul's probe returns: " + pullResult + " -- CORRECT, because the CHECK ITSELF (not the service's self-report) incorporates the real dependency");

        System.out.println("\nThe pull model's advantage: health logic lives where it can be INDEPENDENTLY DESIGNED and VERIFIED (the check definition), not solely inside application code that might have a self-reporting bug.");
    }
}
```

**How to run:** `javac PushVsPullDetectionSpeedComparison.java && java PushVsPullDetectionSpeedComparison` (JDK 17+).

Expected output:
```
=== Push model (Eureka-style): trusts the SERVICE's own self-report ===
Registry receives: UP -- WRONG, this instance is actually degraded, but the self-report has a bug and doesn't catch it

=== Pull model (Consul-style): actively PROBES and independently evaluates ===
Consul's probe returns: DOWN -- CORRECT, because the CHECK ITSELF (not the service's self-report) incorporates the real dependency

The pull model's advantage: health logic lives where it can be INDEPENDENTLY DESIGNED and VERIFIED (the check definition), not solely inside application code that might have a self-reporting bug.
```

## 6. Walkthrough

1. **Level 1** — `sendHeartbeat` checks only `serviceProcessIsAlive` and sends its "I'm alive" signal accordingly, entirely ignoring `actuallyServingRequestsCorrectly`; the registry receiving this heartbeat has no way to know the second, more important fact.
2. **Level 2, the endpoint the registry itself calls** — `healthEndpoint()` returns a status derived from `databaseReachable`, a real dependency; `consulProbesHealth` calls this method directly, modeling Consul's own active HTTP probe against a configured health check path.
3. **Level 2, the correct exclusion** — because `consulProbesHealth` genuinely evaluates the endpoint's real return value (`"DOWN"`), it correctly excludes the instance from discovery results, without ever needing the instance itself to proactively recognize or report its own degraded state.
4. **Level 3, a deliberately buggy self-report** — `pushModelSelfReport` only checks `processIsAlive`, representing a realistic mistake: a developer implementing heartbeat logic (or a health self-check meant to gate heartbeat sending) that forgets to incorporate a specific dependency check.
5. **Level 3, the push model's blind spot exposed** — because the *service itself* decides what to report, and that decision has a bug, the registry receives an incorrect `"UP"` status — the push model's correctness is entirely dependent on the service's own self-assessment logic being complete and bug-free.
6. **Level 3, the pull model's independent verification** — `pullModelHealthEndpoint`, representing the actual health check Consul would call, correctly incorporates `databaseReachable` and returns `"DOWN"` — the key structural difference is that this check's logic isn't necessarily written by the same code path (or even the same person) that decided whether to send a heartbeat; it can be defined, reviewed, and tested as its own well-scoped concern.
7. **Level 3, why this matters practically** — the final printed comment names the real advantage precisely: with an active-pull model, the health-determination logic is a distinct, independently designed artifact (a Consul health check definition) rather than being entangled with, and dependent on the correctness of, whatever self-reporting logic a service's own developers happened to write — this doesn't make the pull model immune to bugs (a poorly-written health check endpoint can still be wrong), but it does mean the responsibility for correct health assessment can be more deliberately separated and verified than a purely self-reported heartbeat model allows.

## 7. Gotchas & takeaways

> **Gotcha:** Consul's active-probe model means Consul itself needs network access to reach every registered service's health check endpoint — in network topologies with firewalls or segmented subnets between Consul and certain services, this can require more deliberate network configuration than Eureka's push model, where the service only needs outbound access to reach the registry, not the other way around.

- Spring Cloud Consul integrates HashiCorp Consul as a service registry, distinguished from Eureka primarily by its active, registry-initiated health-checking model rather than Eureka's heartbeat-push model.
- Consul actively probes each registered service's configured health check (script, TCP, or HTTP), independently verifying actual serviceability rather than trusting a self-reported "I'm alive" signal.
- This separates health-determination logic from the service's own self-reporting code, reducing the risk that a bug in self-reporting logic causes a genuinely degraded instance to appear healthy.
- Consul additionally provides a distributed key-value store, making it attractive for teams wanting a single piece of infrastructure covering both service discovery and dynamic configuration needs.
- The active-probe model requires Consul to have network access to reach every registered service's health endpoint, a topology consideration that Eureka's push-based model doesn't require in the same way.
