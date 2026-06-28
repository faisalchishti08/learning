---
card: spring-boot
gi: 52
slug: application-availability-liveness-readiness-state
title: Application availability (Liveness/Readiness state)
---

## 1. What it is

**Application availability** is Spring Boot's built-in model for signalling whether an application is alive and whether it is ready to serve traffic. It maps directly to the two probe types used by Kubernetes:

| State | Probe type | Meaning |
|---|---|---|
| **Liveness** | Liveness probe | Is the app alive? If `BROKEN`, Kubernetes restarts the pod. |
| **Readiness** | Readiness probe | Can the app serve traffic? If `REFUSING_TRAFFIC`, Kubernetes removes the pod from the load balancer. |

Spring Boot exposes these via Spring Boot Actuator:
```
GET /actuator/health/liveness   → {"status": "UP"}
GET /actuator/health/readiness  → {"status": "UP"}
```

And via the `ApplicationAvailability` bean for programmatic access:
```java
@Autowired ApplicationAvailability availability;
availability.getLivenessState();   // LivenessState.CORRECT or BROKEN
availability.getReadinessState();  // ReadinessState.ACCEPTING_TRAFFIC or REFUSING_TRAFFIC
```

## 2. Why & when

Kubernetes needs two separate signals:
- **Liveness**: is the process stuck in a deadlock or unrecoverable state? If yes, kill and restart it.
- **Readiness**: is the process able to accept requests right now? If no, stop routing traffic to it (but don't kill it — it may be warming up).

Before Spring Boot 2.3, both probes were typically mapped to the same `/actuator/health` endpoint, which conflated "alive" with "ready". The availability model separates them so Kubernetes can respond correctly to each scenario.

Know and use this when deploying to Kubernetes or any orchestrator that supports health probes.

## 3. Core concept

Spring Boot publishes events during the `ApplicationStartup` lifecycle that transition liveness and readiness:

- **`ApplicationStartedEvent`** → liveness transitions to `CORRECT` (app started, no deadlock).
- **`ApplicationReadyEvent`** → readiness transitions to `ACCEPTING_TRAFFIC` (app fully ready).
- **`AvailabilityChangeEvent`** → emitted when you manually change either state.

You can manually change state to signal degraded conditions:

```java
// Mark the app as refusing traffic (e.g. dependency down)
AvailabilityChangeEvent.publish(eventPublisher, this, ReadinessState.REFUSING_TRAFFIC);

// Mark the app as broken (triggers a Kubernetes restart)
AvailabilityChangeEvent.publish(eventPublisher, this, LivenessState.BROKEN);
```

Probes are enabled automatically when Spring Boot detects a Kubernetes environment (`KUBERNETES_SERVICE_HOST` set) or when you explicitly enable them:
```properties
management.endpoint.health.probes.enabled=true
```

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Liveness and readiness state transitions during Spring Boot startup and Kubernetes probe responses">
  <!-- Timeline -->
  <line x1="20" y1="200" x2="640" y2="200" stroke="#8b949e" stroke-width="1.5" marker-end="url(#av)"/>

  <!-- Startup phase -->
  <rect x="20" y="140" width="120" height="52" rx="6" fill="#3d2020" stroke="#f85149" stroke-width="1.5"/>
  <text x="80" y="162" fill="#f85149" font-size="10" font-family="monospace" text-anchor="middle">STARTING</text>
  <text x="80" y="180" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">Liveness: CORRECT</text>
  <text x="80" y="192" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">Ready: REFUSING</text>
  <line x1="80" y1="193" x2="80" y2="200" stroke="#f85149" stroke-width="1.5"/>

  <!-- ApplicationStartedEvent -->
  <rect x="160" y="100" width="140" height="92" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="230" y="122" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">ApplicationStarted</text>
  <text x="230" y="138" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">Event</text>
  <text x="230" y="162" fill="#6db33f" font-size="9" font-family="monospace" text-anchor="middle">Liveness: CORRECT ✅</text>
  <text x="230" y="178" fill="#f85149" font-size="9" font-family="monospace" text-anchor="middle">Ready: REFUSING ❌</text>
  <line x1="230" y1="192" x2="230" y2="200" stroke="#79c0ff" stroke-width="1.5"/>

  <!-- ApplicationReadyEvent -->
  <rect x="330" y="60" width="140" height="132" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="400" y="82" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">ApplicationReady</text>
  <text x="400" y="98" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">Event</text>
  <text x="400" y="122" fill="#6db33f" font-size="9" font-family="monospace" text-anchor="middle">Liveness: CORRECT ✅</text>
  <text x="400" y="138" fill="#6db33f" font-size="9" font-family="monospace" text-anchor="middle">Ready: ACCEPTING ✅</text>
  <text x="400" y="158" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">Kubernetes routes</text>
  <text x="400" y="172" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">traffic to pod ✅</text>
  <line x1="400" y1="192" x2="400" y2="200" stroke="#6db33f" stroke-width="2"/>

  <!-- Manual BROKEN -->
  <rect x="510" y="120" width="130" height="72" rx="6" fill="#3d2020" stroke="#f85149" stroke-width="1.5"/>
  <text x="575" y="142" fill="#f85149" font-size="10" font-family="monospace" text-anchor="middle">Manual event:</text>
  <text x="575" y="158" fill="#f85149" font-size="9" font-family="monospace" text-anchor="middle">LivenessState.BROKEN</text>
  <text x="575" y="174" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">→ Kubernetes restarts</text>
  <line x1="575" y1="192" x2="575" y2="200" stroke="#f85149" stroke-width="1.5"/>

  <defs>
    <marker id="av" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Readiness only moves to `ACCEPTING_TRAFFIC` after the `ApplicationReadyEvent`; liveness moves to `CORRECT` earlier at `ApplicationStartedEvent`.

## 5. Runnable example

```java
// AvailabilityDemo.java
// How to run: java AvailabilityDemo.java  (JDK 17+)
// Simulates the Spring Boot availability state machine and probe responses.

import java.util.*;

public class AvailabilityDemo {

    enum LivenessState  { CORRECT, BROKEN }
    enum ReadinessState { ACCEPTING_TRAFFIC, REFUSING_TRAFFIC }

    // ── Simulated availability bean ────────────────────────────────
    static LivenessState  liveness  = LivenessState.CORRECT;    // set at ApplicationStartedEvent
    static ReadinessState readiness = ReadinessState.REFUSING_TRAFFIC; // default until ready

    // ── Probe endpoints ───────────────────────────────────────────
    static String livenessProbe()  {
        return liveness == LivenessState.CORRECT ? "UP" : "DOWN";
    }
    static String readinessProbe() {
        return readiness == ReadinessState.ACCEPTING_TRAFFIC ? "UP" : "OUT_OF_SERVICE";
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Spring Boot Availability State Demo ===\n");

        // Stage 1: starting
        System.out.println("--- Stage: STARTING (context not yet refreshed) ---");
        probe();

        // Stage 2: ApplicationStartedEvent (context refreshed, runners not yet executed)
        System.out.println("--- Stage: ApplicationStartedEvent fired ---");
        liveness = LivenessState.CORRECT;       // Spring Boot sets this automatically
        probe();

        // Stage 3: ApplicationReadyEvent (runners executed, app fully ready)
        System.out.println("--- Stage: ApplicationReadyEvent fired ---");
        readiness = ReadinessState.ACCEPTING_TRAFFIC;  // Spring Boot sets this
        probe();

        // Stage 4: simulate degraded state (dependency down)
        System.out.println("--- Stage: dependency unavailable → REFUSING_TRAFFIC ---");
        readiness = ReadinessState.REFUSING_TRAFFIC;
        probe();
        System.out.println("  (Kubernetes stops routing traffic; pod stays alive)");

        // Stage 5: simulate unrecoverable state (deadlock detected)
        System.out.println("\n--- Stage: deadlock detected → BROKEN ---");
        liveness = LivenessState.BROKEN;
        probe();
        System.out.println("  (Kubernetes kills and restarts the pod)");
    }

    static void probe() {
        System.out.println("  /actuator/health/liveness  → {\"status\": \"" + livenessProbe() + "\"}");
        System.out.println("  /actuator/health/readiness → {\"status\": \"" + readinessProbe() + "\"}");
        System.out.println();
    }
}
```

**How to run:** `java AvailabilityDemo.java`

Expected output:
```
=== Spring Boot Availability State Demo ===

--- Stage: STARTING (context not yet refreshed) ---
  /actuator/health/liveness  → {"status": "UP"}
  /actuator/health/readiness → {"status": "OUT_OF_SERVICE"}

--- Stage: ApplicationStartedEvent fired ---
  /actuator/health/liveness  → {"status": "UP"}
  /actuator/health/readiness → {"status": "OUT_OF_SERVICE"}

--- Stage: ApplicationReadyEvent fired ---
  /actuator/health/liveness  → {"status": "UP"}
  /actuator/health/readiness → {"status": "UP"}

--- Stage: dependency unavailable → REFUSING_TRAFFIC ---
  /actuator/health/liveness  → {"status": "UP"}
  /actuator/health/readiness → {"status": "OUT_OF_SERVICE"}

  (Kubernetes stops routing traffic; pod stays alive)

--- Stage: deadlock detected → BROKEN ---
  /actuator/health/liveness  → {"status": "DOWN"}
  /actuator/health/readiness → {"status": "OUT_OF_SERVICE"}

  (Kubernetes kills and restarts the pod)
```

## 6. Walkthrough

- Stage 1 (STARTING): liveness is `CORRECT` from the start (Spring Boot sets this immediately on startup), but readiness is `REFUSING_TRAFFIC`. Kubernetes routes no traffic yet.
- Stage 2 (ApplicationStartedEvent): liveness stays `CORRECT`; readiness is still `REFUSING_TRAFFIC` — the app started but `CommandLineRunner`s haven't run yet and the app isn't fully ready.
- Stage 3 (ApplicationReadyEvent): readiness flips to `ACCEPTING_TRAFFIC`. Both probes return `UP`. Kubernetes adds the pod to the load balancer.
- Stage 4 (dependency down): we manually set readiness to `REFUSING_TRAFFIC`. Kubernetes removes the pod from the load balancer but does not restart it — the pod is alive and may recover.
- Stage 5 (deadlock): liveness becomes `BROKEN`. Kubernetes detects the `DOWN` liveness probe and restarts the pod.

## 7. Gotchas & takeaways

> Never set `LivenessState.BROKEN` for transient failures (e.g. a downstream service is temporarily unavailable). Use `ReadinessState.REFUSING_TRAFFIC` instead. Setting liveness to `BROKEN` tells Kubernetes the process is permanently corrupted and triggers a restart — which won't fix a temporary network blip.

> The probes are only automatically exposed when `management.endpoint.health.probes.enabled=true` is set, OR when Spring Boot detects a Kubernetes environment (`KUBERNETES_SERVICE_HOST` is non-empty). In local development neither may apply — add the property to verify probe behavior.

- Configure probe path and port in Kubernetes deployment YAML: `livenessProbe.httpGet.path=/actuator/health/liveness`.
- Default timings: 10 seconds initial delay, 10 seconds period. Tune based on your app's startup time.
- Custom `HealthIndicator` beans (e.g. for a specific downstream service) contribute to `/actuator/health` but not automatically to liveness or readiness — you must choose which group they belong to via `management.endpoint.health.group.readiness.include=*,myDb`.
- `AvailabilityChangeEvent.publish(publisher, source, newState)` is the API for manual state transitions from any Spring bean.
